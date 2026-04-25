<#
.SYNOPSIS
    Scans Active Directory for users with expired or corrupt certificates
    in the userCertificate attribute and optionally removes them.

.DESCRIPTION
    - Queries only users who actually carry certificates (LDAP pre-filter).
    - Distinguishes expired certs, corrupt/unreadable blobs, and valid certs.
    - Corrupt blobs are tracked separately and can be optionally removed.
    - Dry-run mode ($DryRun) is the default; no changes are written unless
      explicitly set to $false.
    - Supports WhatIf/Confirm via ShouldProcess for native PowerShell safety.
    - Uses retry logic for Set-ADUser updates to tolerate transient AD errors.
    - Streams CSV output in batches for large environments to reduce memory use.
    - Produces a timestamped CSV audit log and a console summary.
    - Out-GridView is used only when available and when not in streaming mode.

.PARAMETER DryRun
    When $true (default), AD writes are not attempted and removals are reported.

.PARAMETER SearchBase
    Optional OU distinguished name to limit the query scope.

.PARAMETER RemoveCorruptBlobs
    When $true, unreadable/corrupt certificate blobs are removed in addition
    to expired certificates.

.PARAMETER ProtectLastValidCert
    Legacy safety switch retained for compatibility. Full-removal control is
    primarily enforced by AllowFullRemoval.

.PARAMETER AllowFullRemoval
    When $false (default), users are skipped if cleanup would remove all certs.
    Set to $true only when full removal is explicitly intended.

.PARAMETER Server
    Optional domain controller to use for reads/writes.
    Specifying one DC helps reduce multi-DC consistency surprises.

.PARAMETER Credential
    Optional PSCredential for cross-domain or service-account execution.

.PARAMETER LogPath
    Directory where the CSV audit log will be written.

.PARAMETER ShowProgress
    When $true, shows a progress bar while scanning AD users.

.EXAMPLE
    # Default safety run (dry-run) across the current domain
    .\user.ps1

.EXAMPLE
    # Commit removals in a specific OU and prompt for confirmation
    .\user.ps1 -DryRun:$false -SearchBase "OU=Users,DC=corp,DC=local" -Confirm

.EXAMPLE
    # Include corrupt blob removal and allow full removal if needed
    .\user.ps1 -DryRun:$false -RemoveCorruptBlobs:$true -AllowFullRemoval:$true

.EXAMPLE
    # Target a specific DC with progress output
    .\user.ps1 -Server "dc01.corp.local" -ShowProgress:$true

.NOTES
    Requires: ActiveDirectory module, appropriate AD write permissions.
#>

[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param (
    # Set to $false to commit changes. Defaults to dry-run.
    [bool]$DryRun = $true,

    # Limit scope to a specific OU. Leave empty to scan the whole directory.
    [string]$SearchBase = "",

    # Remove corrupt/unreadable blobs in addition to expired certs.
    [bool]$RemoveCorruptBlobs = $false,

    # Prevent cleanup from removing all certificates for a user.
    [bool]$ProtectLastValidCert = $true,

    # Allow removing all certificates from a user when no valid cert would remain.
    [bool]$AllowFullRemoval = $false,

    # Target DC. Leave empty to use the default logon DC.
    [string]$Server = "",

    # Optional credential for cross-domain or service-account execution.
    [System.Management.Automation.PSCredential]$Credential = $null,

    # Directory where the CSV audit log will be written.
    [string]$LogPath = "C:\Temp",

    # Show progress bar while scanning users.
    [bool]$ShowProgress = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

#region ── Helpers ────────────────────────────────────────────────────────────

function Write-Section {
    param([string]$Message, [ConsoleColor]$Color = "Cyan")
    Write-Host ""
    Write-Host ("─" * 60) -ForegroundColor DarkGray
    Write-Host "  $Message" -ForegroundColor $Color
    Write-Host ("─" * 60) -ForegroundColor DarkGray
}

function New-ResultRecord {
    param(
        [string]$SamAccountName,
        [string]$UserDN,
        [string]$Thumbprint,
        [string]$ExpiryDate,
        [string]$Status,
        [string]$Details
    )
    [PSCustomObject]@{
        Timestamp  = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        User       = $SamAccountName
        UserDN     = $UserDN
        Thumbprint = $Thumbprint
        ExpiryDate = $ExpiryDate
        Status     = $Status
        Details    = $Details
    }
}

function Get-BlobHash {
    param([byte[]]$Blob)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $sha256.ComputeHash($Blob)
        return [System.BitConverter]::ToString($hashBytes)
    } finally {
        $sha256.Dispose()
    }
}

function Get-BlobHashCached {
    param(
        [byte[]]$Blob,
        [hashtable]$HashCache
    )

    $cacheKey = [Convert]::ToBase64String($Blob)
    if ($HashCache.ContainsKey($cacheKey)) {
        return $HashCache[$cacheKey]
    }

    $hash = Get-BlobHash -Blob $Blob
    $HashCache[$cacheKey] = $hash
    return $hash
}

function Invoke-SetADUserWithRetry {
    param(
        [hashtable]$SetADUserParams,
        [switch]$ClearUserCertificate,
        [int]$MaxRetries = 3
    )

    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            if ($ClearUserCertificate) {
                Set-ADUser @SetADUserParams -Clear userCertificate
            } else {
                Set-ADUser @SetADUserParams
            }
            return
        } catch {
            if ($attempt -eq $MaxRetries) {
                throw "Set-ADUser failed after $MaxRetries attempts: $($_.Exception.Message)"
            }
            Start-Sleep -Seconds (2 * $attempt)
        }
    }
}

function Flush-ResultsBuffer {
    param(
        [System.Collections.Generic.List[PSObject]]$Buffer,
        [string]$LogPath,
        [string]$LogFile,
        [hashtable]$AggregatedStatusCounts,
        [ref]$CsvInitialized
    )

    if ($Buffer.Count -eq 0) { return }

    foreach ($r in $Buffer) {
        if ($AggregatedStatusCounts.ContainsKey($r.Status)) {
            $AggregatedStatusCounts[$r.Status]++
        } else {
            $AggregatedStatusCounts[$r.Status] = 1
        }
    }

    if (!(Test-Path $LogPath)) {
        New-Item -ItemType Directory -Path $LogPath -Force -ErrorAction Stop | Out-Null
    }

    if ($CsvInitialized.Value) {
        $Buffer | Export-Csv -Path $LogFile -Append -NoTypeInformation -ErrorAction Stop
    } else {
        $Buffer | Export-Csv -Path $LogFile -NoTypeInformation -ErrorAction Stop
        $CsvInitialized.Value = $true
    }

    $Buffer.Clear()
}

#endregion

#region ── Initialisation ─────────────────────────────────────────────────────

$Now     = Get-Date
$LogFile = Join-Path $LogPath "ExpiredCertCleanup_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
$Results = [System.Collections.Generic.List[PSObject]]::new()
$AggregatedStatusCounts = @{}
$CsvInitialized = $false
$IsStreamingMode = $false

Write-Section "Expired Certificate Cleanup  |  DryRun = $DryRun"
if ($DryRun) {
    Write-Host "  !! Running in DRY-RUN mode. No changes will be written to AD. !!" `
        -ForegroundColor Yellow
}
if (-not $Server) {
    Write-Warning "No DC specified. Results may be inconsistent in multi-DC environments."
}

#endregion

#region ── AD Query ───────────────────────────────────────────────────────────

Write-Section "Querying Active Directory"

$GetADUserParams = @{
    LDAPFilter  = "(userCertificate=*)"
    Properties  = "userCertificate", "DistinguishedName", "SamAccountName"
    ResultSetSize = $null
}
if ($SearchBase) { $GetADUserParams.SearchBase = $SearchBase }
if ($Server)     { $GetADUserParams.Server     = $Server     }
if ($Credential) { $GetADUserParams.Credential = $Credential }

try {
    $UserStream = Get-ADUser @GetADUserParams
    Write-Host "  Streaming users that match the certificate filter..." -ForegroundColor Cyan
} catch {
    throw "AD query failed: $($_.Exception.Message)"
}

#endregion

#region ── Certificate Processing ────────────────────────────────────────────

Write-Section "Processing Certificates"

$UsersScanned = 0
$UsersWithCerts = 0

foreach ($User in $UserStream) {
    $UsersScanned++
    if ($UsersScanned % 100 -eq 0) {
        Write-Host "  Processed $UsersScanned users..." -ForegroundColor DarkGray
    }
    if ($ShowProgress) {
        Write-Progress -Activity "Processing AD users" -Status "$UsersScanned users processed" -PercentComplete -1
    }
    if (-not $User.userCertificate) { continue }
    $UsersWithCerts++

    $ExpiredBlobs     = [System.Collections.Generic.List[byte[]]]::new()
    $CorruptBlobs     = [System.Collections.Generic.List[byte[]]]::new()
    $ExpiredRecords   = [System.Collections.Generic.List[PSObject]]::new()
    $CorruptRecords   = [System.Collections.Generic.List[PSObject]]::new()
    $ValidCount       = 0
    $HashCache        = @{}

    foreach ($CertData in $User.userCertificate) {
        $Cert = $null
        try {
            $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
            $Cert.Import($CertData)

            if ($Cert.NotAfter -le $Now) {
                $ExpiredBlobs.Add($CertData)
                $ExpiredRecords.Add([PSCustomObject]@{
                    Thumbprint = $Cert.Thumbprint
                    ExpiryDate = $Cert.NotAfter.ToString("yyyy-MM-dd HH:mm:ss")
                })
            } else {
                $ValidCount++
            }
        } catch {
            # Blob cannot be parsed as a valid X.509 certificate
            $CorruptBlobs.Add($CertData)
            $CorruptHash = Get-BlobHashCached -Blob $CertData -HashCache $HashCache
            $CorruptRecords.Add([PSCustomObject]@{
                Thumbprint = "N/A (corrupt)"
                ExpiryDate = "N/A"
                BlobHash   = $CorruptHash
                BlobLength = $CertData.Length
            })
            Write-Warning "  [$($User.SamAccountName)] Unreadable cert blob detected."
        } finally {
            if ($null -ne $Cert) { $Cert.Dispose() }
        }
    }

    # ── Build the final removal list ──────────────────────────────────────
    $BlobsToRemove = [System.Collections.Generic.List[byte[]]]::new()
    foreach ($b in $ExpiredBlobs) { $BlobsToRemove.Add($b) }
    if ($RemoveCorruptBlobs) {
        foreach ($b in $CorruptBlobs) { $BlobsToRemove.Add($b) }
    }
    if ($BlobsToRemove.Count -gt 0 -and $ValidCount -eq 0 -and -not $AllowFullRemoval) {
        Write-Warning "  [$($User.SamAccountName)] Skipping cleanup because no valid certificates would remain."
        foreach ($Record in $ExpiredRecords) {
            $Results.Add((New-ResultRecord `
                -SamAccountName $User.SamAccountName `
                -UserDN         $User.DistinguishedName `
                -Thumbprint     $Record.Thumbprint `
                -ExpiryDate     $Record.ExpiryDate `
                -Status         "Skipped - Last Valid Cert Protection" `
                -Details        "AllowFullRemoval=$AllowFullRemoval"
            ))
        }
        foreach ($Record in $CorruptRecords) {
            $Results.Add((New-ResultRecord `
                -SamAccountName $User.SamAccountName `
                -UserDN         $User.DistinguishedName `
                -Thumbprint     $Record.Thumbprint `
                -ExpiryDate     $Record.ExpiryDate `
                -Status         $(if ($RemoveCorruptBlobs) { "Skipped - Last Valid Cert Protection" } else { "Skipped - Corrupt" }) `
                -Details        $(if ($RemoveCorruptBlobs) {
                    "AllowFullRemoval=$AllowFullRemoval"
                } else {
                    "Unreadable/corrupt blob. RemoveCorruptBlobs=$RemoveCorruptBlobs; BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
                })
            ))
        }
        continue
    } elseif ($BlobsToRemove.Count -gt 0 -and $ValidCount -eq 0) {
        Write-Warning "  [$($User.SamAccountName)] Cleanup leaves no valid certificates."
    }

    # ── Log expired certs ─────────────────────────────────────────────────
    foreach ($Record in $ExpiredRecords) {
        Write-Host ("  [{0}] Expired cert: {1}  (expired {2})" -f `
            $User.SamAccountName, $Record.Thumbprint, $Record.ExpiryDate) `
            -ForegroundColor Yellow
    }

    # ── Commit or simulate removal ────────────────────────────────────────
    if ($BlobsToRemove.Count -gt 0) {

        $SetADUserParams = @{
            Identity = $User.DistinguishedName
        }
        if ($Server)     { $SetADUserParams.Server     = $Server     }
        if ($Credential) { $SetADUserParams.Credential = $Credential }
        $RemovalApplied = $false
        $SkippedByShouldProcess = $false

        try {
            if ($DryRun) {
                # Simulate without touching AD
                Write-Host ("  [DryRun] Would remove {0} blob(s) for {1}." -f `
                    $BlobsToRemove.Count, $User.SamAccountName) -ForegroundColor DarkYellow
            } elseif ($PSCmdlet.ShouldProcess($User.DistinguishedName, "Remove $($BlobsToRemove.Count) certificate blob(s) from userCertificate")) {
                # Build the remaining blob set and write it back explicitly.
                # This is more reliable than -Remove for multi-value byte[] attributes.
                # Use hashes to avoid nested byte-by-byte comparisons at scale.
                $BlobHashesToRemove = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
                foreach ($RemoveBlob in $BlobsToRemove) {
                    [void]$BlobHashesToRemove.Add((Get-BlobHashCached -Blob $RemoveBlob -HashCache $HashCache))
                }

                $RemainingBlobs = [System.Collections.Generic.List[byte[]]]::new()
                foreach ($ExistingBlob in $User.userCertificate) {
                    $ExistingBlobHash = Get-BlobHashCached -Blob $ExistingBlob -HashCache $HashCache
                    if (-not $BlobHashesToRemove.Contains($ExistingBlobHash)) {
                        $RemainingBlobs.Add($ExistingBlob)
                    }
                }

                if ($RemainingBlobs.Count -gt 0) {
                    $SetADUserParams.Replace = @{ userCertificate = $RemainingBlobs.ToArray() }
                    Invoke-SetADUserWithRetry -SetADUserParams $SetADUserParams
                } else {
                    Invoke-SetADUserWithRetry -SetADUserParams $SetADUserParams -ClearUserCertificate
                }
                $RemovalApplied = $true
                Write-Host ("  [REMOVED] {0} blob(s) removed for {1}." -f `
                    $BlobsToRemove.Count, $User.SamAccountName) -ForegroundColor Green
            } else {
                $SkippedByShouldProcess = $true
                Write-Host ("  [WhatIf/Confirm] Skipped removal for {0}." -f `
                    $User.SamAccountName) -ForegroundColor DarkYellow
            }

            foreach ($Record in $ExpiredRecords) {
                $Results.Add((New-ResultRecord `
                    -SamAccountName $User.SamAccountName `
                    -UserDN         $User.DistinguishedName `
                    -Thumbprint     $Record.Thumbprint `
                    -ExpiryDate     $Record.ExpiryDate `
                    -Status         $(if ($DryRun) {
                        "Identified (DryRun)"
                    } elseif ($SkippedByShouldProcess) {
                        "Skipped (WhatIf/Confirm)"
                    } elseif ($WhatIfPreference) {
                        "Identified (WhatIf)"
                    } elseif ($RemovalApplied) {
                        "Removed"
                    } else {
                        "Skipped (WhatIf/Confirm)"
                    }) `
                    -Details        "Certificate expired"
                ))
            }

            foreach ($Record in $CorruptRecords) {
                $Results.Add((New-ResultRecord `
                    -SamAccountName $User.SamAccountName `
                    -UserDN         $User.DistinguishedName `
                    -Thumbprint     $Record.Thumbprint `
                    -ExpiryDate     $Record.ExpiryDate `
                    -Status         $(if ($RemoveCorruptBlobs) {
                        if ($DryRun) {
                            "Identified Corrupt (DryRun)"
                        } elseif ($SkippedByShouldProcess) {
                            "Skipped Corrupt (WhatIf/Confirm)"
                        } elseif ($WhatIfPreference) {
                            "Identified Corrupt (WhatIf)"
                        } elseif ($RemovalApplied) {
                            "Removed Corrupt"
                        } else {
                            "Skipped Corrupt (WhatIf/Confirm)"
                        }
                    } else { "Skipped - Corrupt" }) `
                    -Details        "Unreadable/corrupt blob. RemoveCorruptBlobs=$RemoveCorruptBlobs; BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
                ))
            }

        } catch {
            Write-Warning "  Failed to update [$($User.SamAccountName)]: $($_.Exception.Message)"

            foreach ($Record in $ExpiredRecords) {
                $Results.Add((New-ResultRecord `
                    -SamAccountName $User.SamAccountName `
                    -UserDN         $User.DistinguishedName `
                    -Thumbprint     $Record.Thumbprint `
                    -ExpiryDate     $Record.ExpiryDate `
                    -Status         "Update Failed" `
                    -Details        $_.Exception.Message
                ))
            }

            foreach ($Record in $CorruptRecords) {
                $Results.Add((New-ResultRecord `
                    -SamAccountName $User.SamAccountName `
                    -UserDN         $User.DistinguishedName `
                    -Thumbprint     $Record.Thumbprint `
                    -ExpiryDate     $Record.ExpiryDate `
                    -Status         $(if ($RemoveCorruptBlobs) { "Corrupt Update Failed" } else { "Skipped - Corrupt" }) `
                    -Details        $(if ($RemoveCorruptBlobs) {
                        $_.Exception.Message
                    } else {
                        "Unreadable/corrupt blob. RemoveCorruptBlobs=$RemoveCorruptBlobs; BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
                    })
                ))
            }
        }
    } elseif ($CorruptRecords.Count -gt 0) {
        foreach ($Record in $CorruptRecords) {
            $Results.Add((New-ResultRecord `
                -SamAccountName $User.SamAccountName `
                -UserDN         $User.DistinguishedName `
                -Thumbprint     $Record.Thumbprint `
                -ExpiryDate     $Record.ExpiryDate `
                -Status         "Skipped - Corrupt" `
                -Details        "Unreadable/corrupt blob. RemoveCorruptBlobs=$RemoveCorruptBlobs; BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
            ))
        }
    }

    if ($Results.Count -ge 1000) {
        Flush-ResultsBuffer `
            -Buffer $Results `
            -LogPath $LogPath `
            -LogFile $LogFile `
            -AggregatedStatusCounts $AggregatedStatusCounts `
            -CsvInitialized ([ref]$CsvInitialized)
        $IsStreamingMode = $true
    }
}

#endregion

#region ── Summary & Export ───────────────────────────────────────────────────

if ($IsStreamingMode -and $Results.Count -gt 0) {
    Flush-ResultsBuffer `
        -Buffer $Results `
        -LogPath $LogPath `
        -LogFile $LogFile `
        -AggregatedStatusCounts $AggregatedStatusCounts `
        -CsvInitialized ([ref]$CsvInitialized)
} elseif (-not $IsStreamingMode -and $Results.Count -gt 0) {
    foreach ($r in $Results) {
        if ($AggregatedStatusCounts.ContainsKey($r.Status)) {
            $AggregatedStatusCounts[$r.Status]++
        } else {
            $AggregatedStatusCounts[$r.Status] = 1
        }
    }
}

if ($ShowProgress) {
    Write-Progress -Activity "Processing AD users" -Completed
}

Write-Section "Summary" -Color Green

$GetStatusCount = {
    param([string]$Status)
    if ($AggregatedStatusCounts.ContainsKey($Status)) { return $AggregatedStatusCounts[$Status] }
    return 0
}

$CountRemoved  = & $GetStatusCount "Removed"
$CountDryRun   = (& $GetStatusCount "Identified (DryRun)") + (& $GetStatusCount "Identified (WhatIf)")
$CountFailed   = & $GetStatusCount "Update Failed"
$CountCorrupt  = (
    (& $GetStatusCount "Skipped - Corrupt") +
    (& $GetStatusCount "Identified Corrupt (DryRun)") +
    (& $GetStatusCount "Identified Corrupt (WhatIf)") +
    (& $GetStatusCount "Skipped Corrupt (WhatIf/Confirm)") +
    (& $GetStatusCount "Removed Corrupt") +
    (& $GetStatusCount "Corrupt Update Failed") +
    (& $GetStatusCount "Skipped - Last Valid Cert Protection")
)

Write-Host "  Removed            : $CountRemoved"
Write-Host "  Identified (DryRun): $CountDryRun"   -ForegroundColor DarkYellow
Write-Host "  Update Failed      : $CountFailed"   -ForegroundColor $(if ($CountFailed) {"Red"} else {"Gray"})
Write-Host "  Corrupt Blobs      : $CountCorrupt"  -ForegroundColor $(if ($CountCorrupt) {"Magenta"} else {"Gray"})
Write-Host "  Users scanned      : $UsersScanned"
Write-Host "  Users with certs   : $UsersWithCerts"

# Export CSV
if ($CsvInitialized) {
    try {
        Write-Host ""
        Write-Host "  Audit log: $LogFile" -ForegroundColor Cyan
    } catch {
        Write-Warning "Could not write audit log to ${LogFile}: $($_.Exception.Message)"
    }

    # Out-GridView only when the environment supports it
    if ($IsStreamingMode) {
        Write-Host "  (Out-GridView skipped because results were streamed to CSV in batches.)" `
            -ForegroundColor DarkGray
    } elseif (Get-Command Out-GridView -ErrorAction SilentlyContinue) {
        $Results | Out-GridView -Title "Certificate Audit  |  DryRun=$DryRun"
    } else {
        Write-Host "  (Out-GridView unavailable — review the CSV above.)" `
            -ForegroundColor DarkGray
    }
} elseif ($Results.Count -gt 0) {
    try {
        if (!(Test-Path $LogPath)) {
            New-Item -ItemType Directory -Path $LogPath -Force -ErrorAction Stop | Out-Null
        }
        $Results | Export-Csv -Path $LogFile -NoTypeInformation -ErrorAction Stop
        $CsvInitialized = $true
        Write-Host ""
        Write-Host "  Audit log: $LogFile" -ForegroundColor Cyan
    } catch {
        Write-Warning "Could not write audit log to ${LogFile}: $($_.Exception.Message)"
    }

    if (Get-Command Out-GridView -ErrorAction SilentlyContinue) {
        $Results | Out-GridView -Title "Certificate Audit  |  DryRun=$DryRun"
    } else {
        Write-Host "  (Out-GridView unavailable — review the CSV above.)" `
            -ForegroundColor DarkGray
    }
} else {
    Write-Host ""
    Write-Host "  No expired or corrupt certificates found." -ForegroundColor Gray
}

Write-Host ""

#endregion