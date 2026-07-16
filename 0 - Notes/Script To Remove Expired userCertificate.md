---
categories:
  - "[[Microsoft]]"
topic@microsoft:
  - "[[Windows Server]]"
tags:
  - active_directory
  - nac
  - script
  - powershell
  - PBA
  - category/microsoft/windows_server
icon: SiWindows
iconColor: "#0078D4"
---
```powershell
<#
.SYNOPSIS
    Cleans up expired/corrupt certificates from the AD `userCertificate`
    attribute on user and/or computer objects. Designed to be run alongside
    Cisco ISE deployments that use Certificate Binary Comparison as part of
    EAP-TLS authorization.

.DESCRIPTION
    Why this exists
    ---------------
    When ISE is configured to perform Certificate Binary Comparison, every
    EAP-TLS authentication causes ISE to fetch the userCertificate values
    from the matching AD object (via the configured Join Point) and compare
    them, byte-for-byte, against the certificate the supplicant just
    presented. Any value in the attribute is a candidate match.

    Over time userCertificate accumulates stale blobs:
      - Old certs from auto-enrollment renewals (publish, never prune).
      - Replaced devices/users that re-enrolled.
      - Truly corrupt entries (truncated writes, schema mishaps, third-party
        injectors).

    Stale blobs do NOT cause ISE binary comparison to fail (the supplicant
    can only present its current cert), but they:
      * Inflate every ISE LDAP fetch.
      * Make troubleshooting harder.
      * Risk an accidental match if a cert is reissued for a different entity
        with a colliding identity (rare, but a real audit finding).

    What this script does
    ---------------------
    - Pre-filters AD via LDAP to only fetch objects that actually carry certs.
    - Supports user objects, computer objects, or both via -Target.
    - Optional -RequiredIssuer scoping (regex or exact) so the script only
      ever touches certs from the CA that issues your ISE EAP-TLS certs.
      Out-of-scope certs are counted but never removed.
    - Per-cert classification: Valid / Expired / Corrupt / OutOfScope.
    - Atomic per-value -Remove against userCertificate (no read-modify-write
      race; AD matches blobs by exact byte value).
    - Deduplicates blobs queued for removal.
    - Refuses to empty the attribute unless -AllowFullRemoval:$true (clearing
      it kills ISE binary comparison for that object until the next
      autoenrollment cycle + AD replication).
    - Dry-run by default; supports -WhatIf / -Confirm via ShouldProcess.
    - Streaming CSV audit log with normalized Action/Type columns and
      per-cert detail (Thumbprint, Subject, SubjectCN, Issuer, IssuerCN,
      NotBefore/NotAfter) plus per-object active-cert counts.
    - Optional -EagerFlush mode flushes the audit CSV after every successful
      AD write, trading throughput for a complete audit trail if the script
      crashes mid-run.
    - Safety kill-switches for runaway queries or absurd per-object cert counts.
    - Domain-wide cert population totals in the summary (total blobs seen,
      valid in-scope, out-of-scope, expired, corrupt).
    - Optional -IncludeActiveCerts mode emits one audit row per healthy
      (parseable, non-expired) certificate, both in-scope and out-of-scope.
      Type='Active' on every row; the Issuer column tells you which CA
      each cert came from. Gives a full inventory of every live cert in
      userCertificate across the scanned objects.

    Safety guarantee for active certificates
    ----------------------------------------
    Active certificates (parseable + NotAfter >= now) are NEVER removed
    by this script, under any parameter combination. They are:
      - Counted (always, for the summary).
      - Listed in the audit CSV ONLY when -IncludeActiveCerts is set
        explicitly. The default is $false — no listing without opt-in.
    The removal pipeline only ever consumes expired in-scope blobs
    (always eligible) and corrupt blobs (eligible only when
    -RemoveCorruptBlobs is set). There is no code path in which an
    active cert reaches the AD write call. -IncludeActiveCerts is a
    read-only inventory switch; it adds rows to the CSV and nothing
    else.

    What this script does NOT do
    ----------------------------
    - It does not validate the cert chain, revocation, or NTAuth membership.
    - It does not know which cert ISE last matched — it only knows expiry.
    - It does not wait for AD replication. Plan a quiet window or pin both
      writes (-Server) and the ISE Join Point to the same DC for predictable
      behaviour.

    Audit CSV schema
    ----------------
        Timestamp        : when the row was written
        ObjectClass      : 'user' or 'computer'
        Name             : SamAccountName (users) or Name (computers)
        ObjectDN         : full DN
        Thumbprint       : cert thumbprint (or 'N/A' for corrupt/object-level)
        Subject          : cert Subject DN (who the cert was issued TO).
                           'N/A (corrupt)' for unparseable blobs, 'N/A' for
                           object-level rows (KillSwitch, OutOfScopeOnly).
        SubjectCN        : just the CN= component of Subject, for quick
                           filtering by hostname/username in Excel.
                           Derived from Subject; falls back to the full DN
                           if no CN is found, and to "N/A" for placeholders
                           ("N/A", "N/A (corrupt)", etc.).
        Issuer           : cert Issuer DN (which CA signed it). Same N/A
                           rules as Subject.
        IssuerCN         : just the CN= component of Issuer, for quick
                           filtering in Excel (e.g. "Publiacqua Issuing CA").
                           Derived from Issuer; falls back to the full DN
                           if no CN is found, and to "N/A" for placeholders.
        NotBefore        : cert validity start
        NotAfter         : cert validity end
        Action           : Removed | Identified | Skipped | Failed
        Type             : Expired | Corrupt | OutOfScopeOnly | Protection |
                           KillSwitch | Active
        ValidInScope     : count of in-scope, non-expired certs the object
                           has (== "active certificates for ISE binary
                           comparison"). 'N/A' when unclassified.
        RemainingAfter   : total userCertificate values the object will
                           hold after the run. 'N/A' when unclassified.
        Detail           : free-form context (reason, error message, etc.)

.PARAMETER Target
    Which AD object class to scan. User | Computer | Both. Default: User.

.PARAMETER DryRun
    When $true (default), no AD writes are attempted.

    Interaction with -WhatIf and -Confirm:
    -DryRun is checked BEFORE PSCmdlet.ShouldProcess(), so when DryRun is
    on the standard PowerShell -WhatIf flag is effectively redundant —
    you'll get DryRun output regardless. Pass -DryRun:$false to enable
    real-write semantics, then -WhatIf or -Confirm will behave normally.

.PARAMETER SearchBase
    Optional OU distinguished name to limit query scope.

.PARAMETER RequiredIssuer
    Optional pattern matched against the certificate Issuer DN.
    When set, only certs whose Issuer matches are eligible for removal.
    Certs that do not match are tracked as 'OutOfScope' and left alone.
    Strongly recommended for ISE deployments.

.PARAMETER IssuerMatchMode
    How -RequiredIssuer is interpreted.
      Regex  : .NET regex (default, preserves prior behaviour). Note that
               DNs commonly contain regex metacharacters: '(', ')', '+',
               '.'. Escape them, or use Exact mode.
      Exact  : case-insensitive full-DN string equality against $Cert.Issuer.

    NOTE: When -RequiredIssuer starts with 'CN=' and -IssuerMatchMode is
    Regex (the default), the script emits a warning suggesting Exact mode.
    Most users paste a DN and don't think about regex escaping; the warning
    is there to catch that case before it produces silently-wrong matches.

    PERFORMANCE: Test-IssuerInScope runs once per cert blob (not per
    object). With expensive regex patterns — anything with backtracking,
    alternation, or unanchored wildcards — this becomes the per-blob hot
    path. For domain-wide runs with -IncludeActiveCerts producing tens of
    thousands of evaluations, prefer Exact mode (which is a string
    comparison and orders of magnitude faster). The default Regex mode is
    fine for normal DN patterns; this only matters if you've crafted a
    deliberately complex pattern.

.PARAMETER RemoveCorruptBlobs
    When $true, unreadable/corrupt certificate blobs are removed in addition
    to expired certificates. Default $false.

.PARAMETER AllowFullRemoval
    When $false (default), the script refuses to leave the userCertificate
    attribute empty.

.PARAMETER Server
    Optional Domain Controller for AD reads and writes (i.e. the value
    passed to Get-ADObject -Server / Set-ADObject -Server).

    What it is:
      - A Domain Controller (DC) hostname or domain name.
      - Accepted formats: FQDN ('dc01.publiacqua.local'), NetBIOS short
        name ('dc01'), or a domain DNS name ('publiacqua.local'). With
        a domain name, the AD module performs DC locator and binds to
        whichever DC the directory returns — usually fine for reads,
        but may not be the DC ISE uses, see below.

    What it is NOT:
      - It is NOT the issuing CA hostname. The script never connects
        to a CA. The CA is referenced only by the *Issuer DN string*
        you pass to -RequiredIssuer (e.g. 'CN=Publiacqua Issuing CA,
        DC=publiacqua, DC=local'), which is a string match against
        each cert's Issuer field, not a DNS hostname.
      - It is NOT a Global Catalog port. Use a regular LDAP/LDAPS DC
        binding; userCertificate is replicated to every DC, no GC
        needed.

    Why it matters for ISE:
      - Cisco ISE's AD Join Point binds each PSN to a specific DC
        (visible in Administration -> Identity Management -> External
        Identity Sources -> Active Directory -> [Join Point] ->
        Connection tab). When you remove blobs from a different DC,
        ISE won't see the change until intra-site replication catches
        up — typically 15s to a few minutes within a site, longer
        across sites. Pinning -Server to ISE's DC makes post-cleanup
        verification deterministic.

    When -Server is omitted:
      - The AD module calls DC locator for each cmdlet invocation.
        Reads and writes can land on different DCs, which is fine for
        correctness but harder to reason about during testing.
      - The script emits a warning at startup encouraging you to set
        this for ISE deployments.

    Recommended for live runs in ISE environments:
      -Server <fqdn-of-the-DC-bound-to-your-EAP-TLS-PSN>

.PARAMETER Credential
    Optional PSCredential.

.PARAMETER LogPath
    Directory where the CSV audit log will be written.

.PARAMETER ShowProgress
    Show progress while scanning (every 500 objects).

.PARAMETER MaxObjectsKillSwitch
    Abort if more than this many AD objects are returned. Default 50000.
    Compared against scanned-object count (broad guard, not just cert-bearing).

.PARAMETER MaxCertsPerObjectKillSwitch
    Abort processing a single object if its userCertificate has more values
    than this. Default 500.

.PARAMETER IncludeActiveCerts
    READ-ONLY inventory switch. Default $false.

    When $true, emits one CSV row per active certificate (parseable,
    NotAfter >= now) found on the scanned objects: in-scope and out-of-
    scope alike. Rows have Action='Skipped' and Type='Active'. The
    Issuer column distinguishes in-scope from out-of-scope, and Detail
    labels each row accordingly.

    SAFETY: this parameter NEVER causes an active certificate to be
    removed or modified. It only adds rows to the audit CSV. There is
    no combination of parameters that can cause active certs to be
    deleted by this script — the removal pipeline does not consume
    active certs at all.

    OPT-IN: active certificates are not listed unless this parameter
    is explicitly set to $true. The default is $false (no inventory).

    In large environments this can significantly increase audit-log
    size — every healthy cert produces a row.

.PARAMETER EagerFlush
    When $true, flushes the audit-log buffer to disk after every successful
    AD write in committed (non-DryRun) runs, instead of every 1000 rows.
    Default $false.

    Tradeoff:
      - Default ($false): flushes in batches of 1000 rows. Faster — fewer
        Export-Csv invocations, fewer file-handle open/close cycles. If the
        script crashes mid-run you lose up to 1000 audit rows that describe
        AD changes that DID complete. Acceptable for dry-runs and most
        committed runs in healthy environments.
      - Enabled ($true): flushes after every successful Set-ADObject. Slower
        on large runs (each flush re-opens the CSV), but the on-disk audit
        log always reflects every committed change up to the crash point.
        Recommended for unattended/scheduled runs, large blast-radius
        operations, or any run where you'd rather have a slow but complete
        audit trail than a fast but incomplete one.

    Has no effect in DryRun mode (no writes, nothing to crash mid-write).

    Scope of guarantee: EagerFlush flushes after objects that received an
    AD write. Audit rows for objects that DIDN'T receive a write — Active-
    inventory rows from -IncludeActiveCerts on objects with no removals,
    Skipped/OutOfScopeOnly rows, KillSwitch rows — are still buffered and
    follow the standard 1000-row size cap. On a crash, you may lose up to
    1000 of these "no-AD-change" rows. The rows that describe completed
    AD changes are always durable.

.EXAMPLE
    # Default: dry-run on users in the current domain
    .\Invoke-ExpiredCertCleanup.ps1

.EXAMPLE
    # ISE-scoped dry-run on computers, exact issuer match
    .\Invoke-ExpiredCertCleanup.ps1 `
        -Target Computer `
        -RequiredIssuer 'CN=Publiacqua Issuing CA, DC=publiacqua, DC=local' `
        -IssuerMatchMode Exact `
        -Server dc01.publiacqua.local

.EXAMPLE
    # Commit removals on computers, exact issuer match, prompt per object.
    # ConfirmImpact='High' on the script means PowerShell will prompt
    # before each modification unless you pass -Confirm:$false.
    .\Invoke-ExpiredCertCleanup.ps1 `
        -Target Computer `
        -RequiredIssuer 'CN=Publiacqua Issuing CA, DC=publiacqua, DC=local' `
        -IssuerMatchMode Exact `
        -DryRun:$false -Confirm `
        -Server dc01.publiacqua.local

.EXAMPLE
    # Same as above but suppresses per-object prompts. Use ONLY after a
    # dry-run has shown you exactly what will be removed. Combine with
    # -IncludeActiveCerts on a prior dry-run to verify every object
    # retains at least one active cert.
    .\Invoke-ExpiredCertCleanup.ps1 `
        -Target Computer `
        -RequiredIssuer 'CN=Publiacqua Issuing CA, DC=publiacqua, DC=local' `
        -IssuerMatchMode Exact `
        -DryRun:$false -Confirm:$false `
        -Server dc01.publiacqua.local

.EXAMPLE
    # Unattended live run with eager flushing — every committed change is
    # on disk before the next AD write starts. Safe to run from Task
    # Scheduler / Jenkins where you can't watch console output and need
    # the CSV to survive an unexpected termination.
    .\Invoke-ExpiredCertCleanup.ps1 `
        -Target Computer `
        -RequiredIssuer 'CN=Publiacqua Issuing CA, DC=publiacqua, DC=local' `
        -IssuerMatchMode Exact `
        -DryRun:$false -Confirm:$false `
        -EagerFlush:$true `
        -Server dc01.publiacqua.local

.EXAMPLE
    # Dry-run inventory pass: list every active cert on every computer
    # without changing anything. Useful before a live cleanup.
    .\Invoke-ExpiredCertCleanup.ps1 `
        -Target Computer `
        -RequiredIssuer 'CN=Publiacqua Issuing CA, DC=publiacqua, DC=local' `
        -IssuerMatchMode Exact `
        -IncludeActiveCerts:$true `
        -Server dc01.publiacqua.local

.NOTES
    Requires the ActiveDirectory module and write permissions for live runs.
    Uses Get-ADObject / Set-ADObject so user and computer classes share one
    code path.

    NOTE on large environments: Get-ADObject materializes the full result
    set before iteration begins, so the kill-switch is a *post-fetch* guard,
    not a query-time abort. For very large domains, scope tightly with
    -SearchBase. The userCertificate=* filter is matched against an
    unindexed attribute in many schemas, so OU scoping is doubly important.

    NOTE on concurrent invocations: do NOT run multiple instances of this
    script simultaneously against the same scope. Both runners would see
    the same expired blobs, and the second runner's Set-ADObject -Remove
    will fail with "value not present in attribute" because the first
    already removed it. The retry loop will exhaust and the audit log
    will show spurious 'Failed' rows for blobs that are in fact gone.
    The script does not lock or coordinate across invocations — operator
    discipline is required. Stagger by SearchBase if parallelism is
    needed.

    NOTE on disk-write failure: Flush-ResultsBuffer uses Export-Csv with
    -ErrorAction Stop. If the audit-log disk fills up or permissions
    break mid-run, the throw bubbles out of the script and the in-memory
    $Results buffer is lost (no fallback save). For unattended -EagerFlush
    runs, this means a disk hiccup terminates the script with a partial
    CSV. There is no automatic retry on disk write — recovery is not
    meaningful (the operator wanted durable logs, the disk said no, the
    only honest response is to fail loudly). Plan unattended runs against
    a disk with headroom; on-disk audit log up to the failure point is
    preserved.
#>

#Requires -Version 5.1
#Requires -Modules ActiveDirectory

[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param (
    [ValidateSet('User','Computer','Both')]
    [string]$Target = 'User',

    [bool]$DryRun = $true,

    [string]$SearchBase = "",

    [string]$RequiredIssuer = "",

    [ValidateSet('Regex','Exact')]
    [string]$IssuerMatchMode = 'Regex',

    [bool]$RemoveCorruptBlobs = $false,

    [bool]$AllowFullRemoval = $false,

    [string]$Server = "",

    [System.Management.Automation.PSCredential]$Credential = $null,

    [string]$LogPath = "$env:USERPROFILE\Documents",

    [bool]$ShowProgress = $false,

    [int]$MaxObjectsKillSwitch = 50000,

    [int]$MaxCertsPerObjectKillSwitch = 500,

    [bool]$IncludeActiveCerts = $false,

    [bool]$EagerFlush = $false
)

# Pinned at 3.0 deliberately. 'Latest' floats with the host PS version, which
# means a future PS major release could introduce a stricter rule that breaks
# this script silently in CI long after the original author has moved on.
# 3.0 covers the cases we actually care about (uninitialized vars, missing
# properties, unbounded function arg references).
Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

#region ── Helpers ────────────────────────────────────────────────────────────

function Write-Section {
    param([string]$Message, [ConsoleColor]$Color = "Cyan")
    Write-Host ""
    Write-Host ("─" * 72) -ForegroundColor DarkGray
    Write-Host "  $Message" -ForegroundColor $Color
    Write-Host ("─" * 72) -ForegroundColor DarkGray
}

function Get-DnCN {
    <#
        Extract the CN= component from an X.500 distinguished name.

        Splits on unescaped commas (commas not preceded by '\') so DNs like
        "CN=Smith\, John,DC=example,DC=com" parse correctly. Returns the
        first CN found, with escaped commas un-escaped. Falls back to the
        full DN if no CN is present, and to "N/A" for placeholder values.

        NOTE on placeholders: any input matching "N/A" or "N/A*" collapses
        to "N/A". This means "N/A (corrupt)" becomes "N/A" in the SubjectCN
        / IssuerCN columns, losing the "corrupt" annotation. The full
        Subject/Issuer columns retain "N/A (corrupt)" for filtering.

        Used by New-ResultRecord to populate the IssuerCN / SubjectCN
        columns — gives a short, filterable value in Excel (e.g.
        "Publiacqua Issuing CA") without needing to parse the full DN
        every time.

        Defined before New-ResultRecord because that function calls it.
    #>
    param([string]$Dn)
    if (-not $Dn -or $Dn -eq "N/A" -or $Dn -like "N/A*") { return "N/A" }

    # (?<!\\), = comma not preceded by backslash. Splits on unescaped commas.
    $parts = $Dn -split '(?<!\\),'
    foreach ($part in $parts) {
        $trimmed = $part.Trim()
        if ($trimmed -match '^(?i)CN=(.+)$') {
            return $matches[1].Trim() -replace '\\,', ','
        }
    }
    return $Dn   # No CN found — fall back to full DN rather than losing data
}

function New-ResultRecord {
    <#
        Audit-record factory. Action/Type are normalized for aggregation;
        Detail is free text. ValidInScope and RemainingAfter give per-record
        context for the parent object so the CSV can be filtered by ISE
        impact (e.g., rows where ValidInScope=0 are objects that will fail
        binary comparison until autoenrollment runs).

        IssuerCN is derived from $Issuer via Get-DnCN — callers do NOT
        pass it explicitly. Subject must be supplied by the caller from
        the parsed cert (it is a separate X509 property, not derivable
        from anything else in this record).
    #>
    param(
        [string]$ObjectClass,
        [string]$ObjectName,
        [string]$ObjectDN,
        [string]$Thumbprint   = "N/A",
        [string]$Subject      = "N/A",
        [string]$Issuer       = "N/A",
        [string]$NotBefore    = "N/A",
        [string]$NotAfter     = "N/A",
        [ValidateSet('Removed','Identified','Skipped','Failed')]
        [string]$Action,
        [ValidateSet('Expired','Corrupt','OutOfScopeOnly','Protection','KillSwitch','Active')]
        [string]$Type,
        [string]$ValidInScope   = "N/A",
        [string]$RemainingAfter = "N/A",
        [string]$Detail         = ""
    )
    [PSCustomObject]@{
        # [datetime]::Now.ToString(...) is ~10x faster than `Get-Date -Format ...`
        # because it skips the cmdlet pipeline. The format string here is the
        # same. Matters at scale: a 100k-row -IncludeActiveCerts run saves
        # roughly a second of wallclock for free. NOTE: column order below is
        # contractual — downstream filters and Detail-field references rely
        # on it. Append new columns; do not reorder.
        Timestamp      = [datetime]::Now.ToString("yyyy-MM-dd HH:mm:ss")
        ObjectClass    = $ObjectClass
        Name           = $ObjectName
        ObjectDN       = $ObjectDN
        Thumbprint     = $Thumbprint
        Subject        = $Subject
        SubjectCN      = (Get-DnCN -Dn $Subject)
        Issuer         = $Issuer
        IssuerCN       = (Get-DnCN -Dn $Issuer)
        NotBefore      = $NotBefore
        NotAfter       = $NotAfter
        Action         = $Action
        Type           = $Type
        ValidInScope   = $ValidInScope
        RemainingAfter = $RemainingAfter
        Detail         = $Detail
    }
}

function Invoke-SetADObjectWithRetry {
    <#
        Wraps Set-ADObject with exponential-backoff retry.
          -RemoveBlobs : atomic per-value -Remove (preferred, race-safe)
          -ClearAttr   : full attribute clear via -Clear userCertificate

        On the byte[][] -> -Remove handoff: $RemoveBlobs is byte[][]. We
        wrap each element in a single-element array (',$_') and rebuild
        with @(...) before stuffing it into the hashtable. This looks like
        a no-op (and in current AD module versions, passing the raw
        byte[][] works too) but it defends against PS parameter-binding
        edge cases where the inner byte[] arrays could be unrolled into
        their constituent integers during binding to -Remove. The wrap
        forces each blob to remain a discrete array reference. If a
        future test shows the simple form is reliable across all AD
        module versions you support, this can be simplified — but the
        cost of the verbose form is negligible and the failure mode of
        the simple form is silent data corruption (Set-ADObject would
        try to remove integer values from a byte[] attribute).
    #>
    param(
        [hashtable]$SetADObjectParams,
        [byte[][]]$RemoveBlobs = $null,
        [switch]$ClearAttr,
        [int]$MaxRetries = 3
    )

    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            if ($ClearAttr) {
                Set-ADObject @SetADObjectParams -Clear userCertificate
            } elseif ($null -ne $RemoveBlobs -and $RemoveBlobs.Count -gt 0) {
                # See function-header note for why we wrap each blob.
                $RemoveHash = @{ userCertificate = @($RemoveBlobs | ForEach-Object { ,$_ }) }
                Set-ADObject @SetADObjectParams -Remove $RemoveHash
            } else {
                Set-ADObject @SetADObjectParams
            }
            return
        } catch {
            if ($attempt -eq $MaxRetries) {
                throw "Set-ADObject failed after $MaxRetries attempts: $($_.Exception.Message)"
            }
            Write-Warning ("  Set-ADObject attempt {0}/{1} failed: {2}. Retrying in {3}s..." -f `
                $attempt, $MaxRetries, $_.Exception.Message, (2 * $attempt))
            Start-Sleep -Seconds (2 * $attempt)
        }
    }
}

function Update-RecordCounters {
    <#
        Increments two parallel hashtables: one keyed by Action, one by Type.
        Called during streaming flush and at end-of-run aggregation.
    #>
    param(
        [PSObject]$Record,
        [hashtable]$ActionCounts,
        [hashtable]$TypeCounts
    )
    if ($Record.Action) {
        if ($ActionCounts.ContainsKey($Record.Action)) {
            $ActionCounts[$Record.Action]++
        } else {
            $ActionCounts[$Record.Action] = 1
        }
    }
    if ($Record.Type) {
        if ($TypeCounts.ContainsKey($Record.Type)) {
            $TypeCounts[$Record.Type]++
        } else {
            $TypeCounts[$Record.Type] = 1
        }
    }
}

function Flush-ResultsBuffer {
    <#
        Drains $Buffer to the audit CSV and updates the in-memory counters.
        No-op when the buffer is empty.

        $CsvInitialized is passed by [ref] so the caller's value is updated
        on first write (controls Export-Csv -Append vs. fresh-file mode on
        subsequent calls).

        Caller is responsible for ensuring the parent directory of $LogFile
        exists. The script-init block creates it once at startup.
    #>
    param(
        [System.Collections.Generic.List[PSObject]]$Buffer,
        [string]$LogFile,
        [hashtable]$ActionCounts,
        [hashtable]$TypeCounts,
        [ref]$CsvInitialized
    )

    if ($Buffer.Count -eq 0) { return }

    foreach ($r in $Buffer) {
        Update-RecordCounters -Record $r -ActionCounts $ActionCounts -TypeCounts $TypeCounts
    }

    if ($CsvInitialized.Value) {
        $Buffer | Export-Csv -Path $LogFile -Append -NoTypeInformation -ErrorAction Stop
    } else {
        $Buffer | Export-Csv -Path $LogFile -NoTypeInformation -ErrorAction Stop
        $CsvInitialized.Value = $true
    }

    $Buffer.Clear()
}

function Get-FriendlyName {
    <#
        Returns a short display name. Computers prefer Name (no trailing $);
        users prefer SamAccountName but fall back to Name if missing.
    #>
    param($AdObject)
    if ($AdObject.objectClass -contains 'computer') {
        return $AdObject.Name
    }
    if ($AdObject.SamAccountName) {
        return $AdObject.SamAccountName
    }
    return $AdObject.Name
}

function Get-DedupedBlobList {
    <#
        Deduplicates a list of byte[] blobs by exact byte-value.

        We can't use Sort-Object -Unique here: PowerShell compares byte[]
        values by reference, so two distinct array instances holding the
        same bytes always sort as unique. We key on Base64 of the bytes
        instead, using a HashSet for O(1) lookup.
    #>
    param([System.Collections.Generic.List[byte[]]]$Blobs)

    $seen   = [System.Collections.Generic.HashSet[string]]::new()
    $result = [System.Collections.Generic.List[byte[]]]::new()
    foreach ($b in $Blobs) {
        $key = [Convert]::ToBase64String($b)
        if ($seen.Add($key)) {
            $result.Add($b)
        }
    }
    return ,$result   # comma-prefix prevents PS from unrolling the List
}

function Test-IssuerInScope {
    <#
        Applies -RequiredIssuer / -IssuerMatchMode policy.
        Empty $RequiredIssuer means "no scope filter" -> always in-scope.
    #>
    param(
        [string]$IssuerDn,
        [string]$RequiredIssuer,
        [string]$IssuerMatchMode
    )
    if (-not $RequiredIssuer) { return $true }

    if ($IssuerMatchMode -eq 'Exact') {
        return [string]::Equals($IssuerDn, $RequiredIssuer, [StringComparison]::OrdinalIgnoreCase)
    }
    # Regex (default) — case-insensitive by default in PowerShell, matching
    # DN comparison semantics (RFC 4514). Use [regex]::Escape() in your
    # input if you want literal matching of '(', ')', '+', '.' etc.
    return $IssuerDn -match $RequiredIssuer
}

#endregion

#region ── Initialisation ─────────────────────────────────────────────────────

# Snapshot the expiry clock once at script start. All NotAfter comparisons
# throughout the run use this single timestamp, so a cert that's classified
# as Valid early in the run and one that's classified late are evaluated
# against the same instant. Expiry classification is therefore consistent
# across the whole pass.
#
# What this is NOT: an "AD-as-of-T0" snapshot. Get-ADObject pages results
# over the wire as the foreach iterates, so each AD object reflects directory
# state at the moment IT was streamed, not at $Now. If a cert is added to
# an object 20 minutes into a 30-minute run, the script will see it; if one
# is deleted on a different DC during the run, you may or may not see it
# depending on replication timing. The expiry clock is atomic; the directory
# view is not.
$Now     = Get-Date
$LogFile = Join-Path $LogPath "ExpiredCertCleanup_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"

# Create the log directory once at script start, before any potential flush.
# Flush-ResultsBuffer used to do this on every call, but that's wasteful
# under -EagerFlush (one Test-Path per AD write). Doing it here means the
# directory is guaranteed to exist before the first flush attempts to write.
if (!(Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force -ErrorAction Stop | Out-Null
}

$Results = [System.Collections.Generic.List[PSObject]]::new()
$ActionCounts    = @{}
$TypeCounts      = @{}

# CsvInitialized tracks whether the audit CSV has been opened yet. Scoped
# at script: so [ref]-passing to Flush-ResultsBuffer binds unambiguously.
# Either form (local or $script:) works in current code; using $script:
# makes the binding explicit at every call site.
$script:CsvInitialized = $false

# ── Domain-wide cert population counters ───────────────────────────────────
# Cheap integer accumulators incremented per object after classification.
# Only counts blobs from objects that passed the per-object kill-switch
# (i.e., the population the script actually inspected).
$TotalCertsSeen     = 0   # every userCertificate value classified
$TotalValidInScope  = 0   # parseable, in-scope per -RequiredIssuer, not expired
$TotalOutOfScope    = 0   # parseable but issuer didn't match policy
$TotalExpiredSeen   = 0   # parseable, in-scope, NotAfter < now
$TotalCorruptSeen   = 0   # blob failed X509 parse

# Per-class population counters (populated regardless of -Target, used
# for the breakdown row in the summary). Indexed by 'user'/'computer'.
$ClassTotals = @{
    user     = @{ Seen = 0; Valid = 0; OOS = 0; Expired = 0; Corrupt = 0 }
    computer = @{ Seen = 0; Valid = 0; OOS = 0; Expired = 0; Corrupt = 0 }
}

# Single SHA-256 instance reused for every corrupt-blob hash. The .NET
# SHA256 type's ComputeHash(byte[]) is one-shot and resets state per
# call, so reusing the instance is safe and avoids creating one per
# corrupt blob. Disposed at the end of the script.
$BlobHasher = [System.Security.Cryptography.SHA256]::Create()

Write-Section "Expired Certificate Cleanup  |  Target=$Target  |  DryRun=$DryRun"
if ($DryRun) {
    Write-Host "  !! DRY-RUN — no changes will be written to AD. !!" -ForegroundColor Yellow
}
if ($RequiredIssuer) {
    Write-Host "  Issuer scope ($IssuerMatchMode): '$RequiredIssuer'" -ForegroundColor Cyan

    # Footgun warning: a DN passed to Regex mode rarely does what users want.
    # DNs contain '.', '+', '(', ')' and similar metacharacters. If the user
    # pasted a DN ('CN=...') and didn't pick Exact, they almost certainly
    # want Exact.
    if ($IssuerMatchMode -eq 'Regex' -and $RequiredIssuer -match '^(?i)CN=') {
        Write-Warning "RequiredIssuer looks like a DN ('CN=...') but IssuerMatchMode is Regex. DNs contain regex metacharacters (., +, (, ), etc.) that may not match literally. Consider -IssuerMatchMode Exact, or wrap your input in [regex]::Escape()."
    }
}
else {
    Write-Warning "No -RequiredIssuer supplied. The script will treat certs from any CA as in-scope. For ISE deployments you almost always want to restrict this."
}
if (-not $Server) {
    Write-Warning "No -Server specified. ISE binary comparison reads from the DC pinned in the AD Join Point — replication delay between the DC you write to and the DC ISE reads from can cause transient mismatches. Pin -Server to ISE's chosen DC if possible."
}
if ($IncludeActiveCerts) {
    Write-Host "  -IncludeActiveCerts: active certs will be LISTED in the CSV (read-only)." -ForegroundColor Cyan
    Write-Host "                       No active cert is ever removed by this script." -ForegroundColor Cyan
} else {
    Write-Host "  -IncludeActiveCerts: OFF (default). Active certs will not appear in the CSV." -ForegroundColor DarkGray
}
if ($EagerFlush -and -not $DryRun) {
    Write-Host "  -EagerFlush: ON. Audit log will be flushed to disk after every successful AD write." -ForegroundColor Cyan
} elseif ($EagerFlush -and $DryRun) {
    Write-Host "  -EagerFlush: requested but ignored in DryRun (no AD writes occur)." -ForegroundColor DarkGray
}

#endregion

#region ── AD Query ───────────────────────────────────────────────────────────

Write-Section "Querying Active Directory"

$ClassFilter = switch ($Target) {
    'User'     { "(&(objectCategory=person)(objectClass=user))" }
    'Computer' { "(objectCategory=computer)" }
    'Both'     { "(|(objectCategory=computer)(&(objectCategory=person)(objectClass=user)))" }
}
$LdapFilter = "(&$ClassFilter(userCertificate=*))"

$GetADObjectParams = @{
    LDAPFilter     = $LdapFilter
    Properties     = @("userCertificate","DistinguishedName","SamAccountName","Name","objectClass")
    # ResultSetSize=$null means UNLIMITED (return everything). The AD module
    # default is 1000, which is very much not what we want for this kind of
    # tenant-wide sweep. Readers will assume $null means "default" — it
    # doesn't, hence this comment.
    ResultSetSize  = $null
    ResultPageSize = 1000
}
if ($SearchBase) { $GetADObjectParams.SearchBase = $SearchBase }
if ($Server)     { $GetADObjectParams.Server     = $Server     }
if ($Credential) { $GetADObjectParams.Credential = $Credential }

# Naming note: $AdObjects, not $ObjectStream. Get-ADObject materializes
# the entire result set before returning, despite appearances — a name
# like "Stream" would imply lazy iteration that isn't happening.
try {
    $AdObjects = Get-ADObject @GetADObjectParams
    Write-Host "  LDAP filter: $LdapFilter" -ForegroundColor DarkGray
    Write-Host "  Iterating objects with at least one userCertificate value..." -ForegroundColor Cyan
} catch {
    throw "AD query failed: $($_.Exception.Message)"
}

#endregion

#region ── Certificate Processing ─────────────────────────────────────────────

Write-Section "Processing Certificates"

# Object-level counters (independent of per-record action/type aggregation)
$ObjectsScanned         = 0
$ObjectsWithCerts       = 0
$ObjectsModified        = 0  # writes attempted (incl. dry-run "would write")
$ObjectsBroken          = 0  # ValidInScope == 0 after run (ISE binary comp will fail)
$ObjectsProtected       = 0  # empty-attr protection tripped (object-level)
$ObjectsKillSwitched    = 0  # per-object too-many-certs guard tripped
$ObjectsOutOfScopeOnly  = 0  # no in-scope certs, nothing to do (but logged)

foreach ($AdObject in $AdObjects) {
    $ObjectsScanned++

    # Broad query-size guard. Compared against scanned (not just cert-bearing)
    # so a misconfigured filter that returns far too much data trips early.
    if ($ObjectsScanned -gt $MaxObjectsKillSwitch) {
        throw ("Safety kill-switch: more than $MaxObjectsKillSwitch objects " +
               "scanned. Verify SearchBase/filter or raise -MaxObjectsKillSwitch.")
    }

    if ($ShowProgress -and $ObjectsScanned % 500 -eq 0) {
        Write-Host "  Processed $ObjectsScanned objects..." -ForegroundColor DarkGray
        Write-Progress -Activity "Processing AD objects" -Status "$ObjectsScanned objects processed" -PercentComplete -1
    }

    if (-not $AdObject.userCertificate) { continue }
    $ObjectsWithCerts++

    $FriendlyName = Get-FriendlyName -AdObject $AdObject
    $ObjClass     = if ($AdObject.objectClass -contains 'computer') { 'computer' } else { 'user' }

    # Per-object kill-switch (bloated userCertificate)
    if ($AdObject.userCertificate.Count -gt $MaxCertsPerObjectKillSwitch) {
        Write-Warning ("  [$FriendlyName] Skipped: $($AdObject.userCertificate.Count) cert blobs " +
                       "exceeds per-object safety limit ($MaxCertsPerObjectKillSwitch).")
        $ObjectsKillSwitched++
        $Results.Add((New-ResultRecord `
            -ObjectClass $ObjClass `
            -ObjectName  $FriendlyName `
            -ObjectDN    $AdObject.DistinguishedName `
            -Action      "Skipped" `
            -Type        "KillSwitch" `
            -Detail      "Cert count $($AdObject.userCertificate.Count) exceeds MaxCertsPerObjectKillSwitch=$MaxCertsPerObjectKillSwitch"
        ))
        continue
    }

    # ── Classify each blob ────────────────────────────────────────────────
    $ExpiredBlobs    = [System.Collections.Generic.List[byte[]]]::new()
    $CorruptBlobs    = [System.Collections.Generic.List[byte[]]]::new()
    $ExpiredRecords  = [System.Collections.Generic.List[PSObject]]::new()
    $CorruptRecords  = [System.Collections.Generic.List[PSObject]]::new()
    $ActiveRecords   = [System.Collections.Generic.List[PSObject]]::new()  # READ-ONLY inventory; only populated when -IncludeActiveCerts. Never feeds removal.
    $ValidCount      = 0   # in-scope, parseable, not expired
    $OutOfScopeCount = 0   # parseable but issuer didn't match policy

    foreach ($CertData in $AdObject.userCertificate) {
        $Cert = $null
        try {
            $Cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($CertData)

            $InScope = Test-IssuerInScope `
                -IssuerDn        $Cert.Issuer `
                -RequiredIssuer  $RequiredIssuer `
                -IssuerMatchMode $IssuerMatchMode

            if (-not $InScope) {
                $OutOfScopeCount++
                # Out-of-scope active certs (parseable + not expired) are
                # also part of the live inventory; capture them when the
                # caller asked for the active-cert listing.
                if ($IncludeActiveCerts -and $Cert.NotAfter -ge $Now) {
                    $ActiveRecords.Add([PSCustomObject]@{
                        Thumbprint = $Cert.Thumbprint
                        Subject    = $Cert.Subject
                        Issuer     = $Cert.Issuer
                        NotBefore  = $Cert.NotBefore.ToString("yyyy-MM-dd HH:mm:ss")
                        NotAfter   = $Cert.NotAfter.ToString("yyyy-MM-dd HH:mm:ss")
                        InScope    = $false
                    })
                }
            }
            elseif ($Cert.NotAfter -lt $Now) {
                $ExpiredBlobs.Add($CertData)
                $ExpiredRecords.Add([PSCustomObject]@{
                    Thumbprint = $Cert.Thumbprint
                    Subject    = $Cert.Subject
                    Issuer     = $Cert.Issuer
                    NotBefore  = $Cert.NotBefore.ToString("yyyy-MM-dd HH:mm:ss")
                    NotAfter   = $Cert.NotAfter.ToString("yyyy-MM-dd HH:mm:ss")
                })
            }
            else {
                $ValidCount++
                if ($IncludeActiveCerts) {
                    $ActiveRecords.Add([PSCustomObject]@{
                        Thumbprint = $Cert.Thumbprint
                        Subject    = $Cert.Subject
                        Issuer     = $Cert.Issuer
                        NotBefore  = $Cert.NotBefore.ToString("yyyy-MM-dd HH:mm:ss")
                        NotAfter   = $Cert.NotAfter.ToString("yyyy-MM-dd HH:mm:ss")
                        InScope    = $true
                    })
                }
            }
        } catch {
            $CorruptBlobs.Add($CertData)
            # Reuse the hoisted $BlobHasher instance — ComputeHash is
            # one-shot and resets internal state, so this is safe.
            $HashHex = [System.BitConverter]::ToString($BlobHasher.ComputeHash($CertData))
            $CorruptRecords.Add([PSCustomObject]@{
                Thumbprint = "N/A (corrupt)"
                Subject    = "N/A (corrupt)"
                Issuer     = "N/A (corrupt)"
                NotBefore  = "N/A"
                NotAfter   = "N/A"
                BlobHash   = $HashHex
                BlobLength = $CertData.Length
            })
            Write-Warning "  [$FriendlyName] Unreadable cert blob (length=$($CertData.Length))."
        } finally {
            if ($null -ne $Cert) { $Cert.Dispose() }
        }
    }

    # ── Domain-wide totals (post-classification, pre-action) ─────────────
    # Five integer adds; no allocations. Invariant:
    #   TotalCertsSeen == TotalValidInScope + TotalOutOfScope
    #                   + TotalExpiredSeen + TotalCorruptSeen
    # Counts are taken *before* any removal so they reflect the population
    # found in AD at scan time, not the post-cleanup state.
    #
    # NOTE on duplicates: $TotalExpiredSeen and $ExpiredRecords reflect the
    # raw count of blobs in userCertificate (with any duplicates). The
    # removal pipeline deduplicates ($BlobsToRemove < $ExpiredBlobs in that
    # case) so the 'Removed' row count for one object can be smaller than
    # its 'Expired' row count. This is intentional: totals describe the
    # population found in AD; action counts describe what was done to it.
    $TotalCertsSeen    += $AdObject.userCertificate.Count
    $TotalValidInScope += $ValidCount
    $TotalOutOfScope   += $OutOfScopeCount
    $TotalExpiredSeen  += $ExpiredBlobs.Count
    $TotalCorruptSeen  += $CorruptBlobs.Count

    # Per-class breakdown (always populated; printed in summary).
    $ClassTotals[$ObjClass]['Seen']    += $AdObject.userCertificate.Count
    $ClassTotals[$ObjClass]['Valid']   += $ValidCount
    $ClassTotals[$ObjClass]['OOS']     += $OutOfScopeCount
    $ClassTotals[$ObjClass]['Expired'] += $ExpiredBlobs.Count
    $ClassTotals[$ObjClass]['Corrupt'] += $CorruptBlobs.Count

    # ── Build (and dedupe) the removal list ──────────────────────────────
    # SAFETY: the removal list is built ONLY from $ExpiredBlobs (in-scope,
    # parseable, NotAfter < $Now) and optionally $CorruptBlobs. Active
    # certs (live in $ActiveRecords) are never sourced here — there is
    # no code path by which an active cert can reach the AD write call.
    $BlobsToRemoveRaw = [System.Collections.Generic.List[byte[]]]::new()
    foreach ($b in $ExpiredBlobs)  { $BlobsToRemoveRaw.Add($b) }
    if ($RemoveCorruptBlobs) {
        foreach ($b in $CorruptBlobs) { $BlobsToRemoveRaw.Add($b) }
    }
    $BlobsToRemove = Get-DedupedBlobList -Blobs $BlobsToRemoveRaw

    # OutOfScope-only objects (RequiredIssuer set, nothing in scope at all):
    # log a single audit row so the auditor can see the script saw this object.
    if ($RequiredIssuer -and `
        $ExpiredBlobs.Count -eq 0 -and `
        $ValidCount -eq 0 -and `
        $CorruptRecords.Count -eq 0 -and `
        $OutOfScopeCount -gt 0) {

        $ObjectsOutOfScopeOnly++

        # When -IncludeActiveCerts is on, also emit one row per active OOS
        # cert. ValidCount==0 here by construction, so all ActiveRecords
        # entries on this object are InScope=false (no need to branch on it).
        if ($IncludeActiveCerts -and $ActiveRecords.Count -gt 0) {
            foreach ($Record in $ActiveRecords) {
                $Results.Add((New-ResultRecord `
                    -ObjectClass     $ObjClass `
                    -ObjectName      $FriendlyName `
                    -ObjectDN        $AdObject.DistinguishedName `
                    -Thumbprint      $Record.Thumbprint `
                    -Subject         $Record.Subject `
                    -Issuer          $Record.Issuer `
                    -NotBefore       $Record.NotBefore `
                    -NotAfter        $Record.NotAfter `
                    -Action          "Skipped" `
                    -Type            "Active" `
                    -ValidInScope    "0" `
                    -RemainingAfter  "$OutOfScopeCount" `
                    -Detail          "Active out-of-scope certificate (issuer outside RequiredIssuer policy; no action)"
                ))
            }
        }

        $Results.Add((New-ResultRecord `
            -ObjectClass     $ObjClass `
            -ObjectName      $FriendlyName `
            -ObjectDN        $AdObject.DistinguishedName `
            -Action          "Skipped" `
            -Type            "OutOfScopeOnly" `
            -ValidInScope    "0" `
            -RemainingAfter  "$OutOfScopeCount" `
            -Detail          "Only out-of-scope certs present ($OutOfScopeCount). Issuer policy: $IssuerMatchMode='$RequiredIssuer'."
        ))
        continue
    }

    # ── How many cert values will remain after the operation? ─────────────
    # OutOfScope blobs are NEVER removed, so they survive.
    # Corrupt blobs survive when -RemoveCorruptBlobs is $false.
    $CorruptSurvivors = if ($RemoveCorruptBlobs) { 0 } else { $CorruptRecords.Count }
    $RemainingAfter   = $ValidCount + $OutOfScopeCount + $CorruptSurvivors
    $ValidInScopeStr  = "$ValidCount"
    $RemainingStr     = "$RemainingAfter"

    # ── Empty-attribute protection ────────────────────────────────────────
    # Refuses to leave userCertificate empty unless explicitly authorized.
    if ($BlobsToRemove.Count -gt 0 -and $RemainingAfter -eq 0 -and -not $AllowFullRemoval) {
        $ObjectsProtected++
        Write-Warning "  [$FriendlyName] Skipping: would empty userCertificate (would break ISE binary comparison until next enrollment + replication)."
        foreach ($Record in $ExpiredRecords) {
            $Results.Add((New-ResultRecord `
                -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                -Thumbprint $Record.Thumbprint -Subject $Record.Subject -Issuer $Record.Issuer `
                -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                -Action "Skipped" -Type "Protection" `
                -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                -Detail "Empty-attr protection. AllowFullRemoval=$AllowFullRemoval. Would break ISE binary comparison."
            ))
        }
        # Corrupt rows: keep Type=Corrupt so corrupt-blob tallies stay accurate
        foreach ($Record in $CorruptRecords) {
            $Results.Add((New-ResultRecord `
                -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                -Thumbprint $Record.Thumbprint -Subject $Record.Subject -Issuer $Record.Issuer `
                -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                -Action "Skipped" -Type "Corrupt" `
                -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                -Detail "Empty-attr protection (RemoveCorruptBlobs=$RemoveCorruptBlobs); BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
            ))
        }
        continue
    }

    # ── ISE-impact: no in-scope, non-expired cert remains ─────────────────
    # Tracked separately because the object isn't *protected* (e.g., it has
    # surviving out-of-scope certs), but ISE — restricted to the issuing CA
    # — won't have a usable match after the run.
    if ($BlobsToRemove.Count -gt 0 -and $ValidCount -eq 0) {
        $ObjectsBroken++
        $verbPhrase = if ($DryRun) { "would fail" } else { "will fail" }
        if ($RequiredIssuer) {
            Write-Warning "  [$FriendlyName] After cleanup, no certs from issuer matching '$RequiredIssuer' remain. ISE binary comparison $verbPhrase for this object until autoenrollment runs."
        } else {
            Write-Warning "  [$FriendlyName] Cleanup $verbPhrase leave no non-expired certificates."
        }
    }

    # ── Console log of what's being acted on ──────────────────────────────
    foreach ($Record in $ExpiredRecords) {
        Write-Host ("  [{0}] ({1}) Expired: {2}  subject={3}  issuer={4}  notAfter={5}" -f `
            $FriendlyName, $ObjClass, $Record.Thumbprint, $Record.Subject, $Record.Issuer, $Record.NotAfter) `
            -ForegroundColor Yellow
    }
    if ($OutOfScopeCount -gt 0 -and $RequiredIssuer) {
        Write-Host ("  [{0}] ({1}) {2} out-of-scope cert(s) ignored." -f `
            $FriendlyName, $ObjClass, $OutOfScopeCount) -ForegroundColor DarkGray
    }

    # ── Commit or simulate ────────────────────────────────────────────────
    # $RemovalApplied is hoisted above the if so the post-loop EagerFlush
    # block can read it unconditionally even when no removal was attempted
    # (in which case it stays $false and EagerFlush is a no-op).
    $RemovalApplied = $false

    if ($BlobsToRemove.Count -gt 0) {
        $ObjectsModified++

        $SetADObjectParams = @{ Identity = $AdObject.DistinguishedName }
        if ($Server)     { $SetADObjectParams.Server     = $Server     }
        if ($Credential) { $SetADObjectParams.Credential = $Credential }

        $SkippedByShouldProcess = $false

        try {
            if ($DryRun) {
                Write-Host ("  [DryRun] Would remove {0} blob(s) from {1} ({2}). Active in-scope after: {3} (oos={4}, corrupt-kept={5})" -f `
                    $BlobsToRemove.Count, $FriendlyName, $ObjClass, $ValidCount, $OutOfScopeCount, $CorruptSurvivors) `
                    -ForegroundColor DarkYellow
            } elseif ($PSCmdlet.ShouldProcess(
                $AdObject.DistinguishedName,
                "Remove $($BlobsToRemove.Count) certificate blob(s) from userCertificate")) {

                # Atomic per-value removal. -Clear is only used when nothing
                # would remain (which already passed the AllowFullRemoval gate).
                if ($RemainingAfter -gt 0) {
                    Invoke-SetADObjectWithRetry `
                        -SetADObjectParams $SetADObjectParams `
                        -RemoveBlobs $BlobsToRemove.ToArray()
                } else {
                    Invoke-SetADObjectWithRetry `
                        -SetADObjectParams $SetADObjectParams `
                        -ClearAttr
                }

                $RemovalApplied = $true
                Write-Host ("  [REMOVED] {0} blob(s) from {1} ({2}). Active in-scope: {3}" -f `
                    $BlobsToRemove.Count, $FriendlyName, $ObjClass, $ValidCount) -ForegroundColor Green
            } else {
                # ShouldProcess returned $false: -WhatIf was set, or -Confirm
                # prompted and the user declined. We don't separately check
                # $WhatIfPreference here — ShouldProcess already subsumes it
                # (ShouldProcess returns $false when -WhatIf is in effect).
                $SkippedByShouldProcess = $true
                Write-Host ("  [WhatIf/Confirm] Skipped {0}." -f $FriendlyName) -ForegroundColor DarkYellow
            }

            $ResultAction = if ($DryRun) {
                "Identified"
            } elseif ($SkippedByShouldProcess) {
                "Skipped"
            } elseif ($RemovalApplied) {
                "Removed"
            } else {
                "Skipped"
            }
            $WhatIfDetail = if ($SkippedByShouldProcess) { " (WhatIf/Confirm)" } else { "" }

            foreach ($Record in $ExpiredRecords) {
                $Results.Add((New-ResultRecord `
                    -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                    -Thumbprint $Record.Thumbprint -Subject $Record.Subject -Issuer $Record.Issuer `
                    -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                    -Action $ResultAction -Type "Expired" `
                    -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                    -Detail "Certificate expired$WhatIfDetail"
                ))
            }
            foreach ($Record in $CorruptRecords) {
                if ($RemoveCorruptBlobs) {
                    $Results.Add((New-ResultRecord `
                        -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                        -Thumbprint $Record.Thumbprint -Subject $Record.Subject -Issuer $Record.Issuer `
                        -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                        -Action $ResultAction -Type "Corrupt" `
                        -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                        -Detail "Unreadable/corrupt blob$WhatIfDetail; BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
                    ))
                } else {
                    $Results.Add((New-ResultRecord `
                        -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                        -Thumbprint $Record.Thumbprint -Subject $Record.Subject -Issuer $Record.Issuer `
                        -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                        -Action "Skipped" -Type "Corrupt" `
                        -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                        -Detail "Unreadable/corrupt blob (RemoveCorruptBlobs=$RemoveCorruptBlobs); BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
                    ))
                }
            }

        } catch {
            # Capture the exception at catch entry. We use $caughtException
            # explicitly inside the foreach loops below as a defensive habit:
            # `foreach ($x in $col)` (statement form) does NOT rebind $_, so
            # $_ inside it would still refer to the catch's exception. But a
            # future refactor that switches to `| ForEach-Object {…}` would
            # silently shadow $_ with the pipeline item and corrupt the
            # error-message field. Explicit capture defuses that footgun.
            $caughtException = $_
            Write-Warning "  Failed to update [$FriendlyName]: $($caughtException.Exception.Message)"

            foreach ($Record in $ExpiredRecords) {
                $Results.Add((New-ResultRecord `
                    -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                    -Thumbprint $Record.Thumbprint -Subject $Record.Subject -Issuer $Record.Issuer `
                    -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                    -Action "Failed" -Type "Expired" `
                    -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                    -Detail $caughtException.Exception.Message
                ))
            }
            foreach ($Record in $CorruptRecords) {
                $Results.Add((New-ResultRecord `
                    -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                    -Thumbprint $Record.Thumbprint -Subject $Record.Subject -Issuer $Record.Issuer `
                    -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                    -Action $(if ($RemoveCorruptBlobs) { "Failed" } else { "Skipped" }) -Type "Corrupt" `
                    -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                    -Detail $(if ($RemoveCorruptBlobs) {
                        $caughtException.Exception.Message
                    } else {
                        "Unreadable/corrupt blob (RemoveCorruptBlobs=$RemoveCorruptBlobs); BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
                    })
                ))
            }
        }

    } elseif ($CorruptRecords.Count -gt 0) {
        # No expired blobs, only corrupt ones, RemoveCorruptBlobs=$false
        foreach ($Record in $CorruptRecords) {
            $Results.Add((New-ResultRecord `
                -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                -Thumbprint $Record.Thumbprint -Subject $Record.Subject -Issuer $Record.Issuer `
                -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                -Action "Skipped" -Type "Corrupt" `
                -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                -Detail "Unreadable/corrupt blob (RemoveCorruptBlobs=$RemoveCorruptBlobs); BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
            ))
        }
    }

    # ── Emit Active rows (inventory mode) ─────────────────────────────────
    # Healthy certs that survived the run, regardless of issuer scope.
    # Logged with Action='Skipped' (no AD write was made for them) and
    # Type='Active'. Detail differentiates in-scope (matches RequiredIssuer)
    # from out-of-scope. Reachable on the normal commit/dry-run path, the
    # corrupt-only path, and the all-active path. The OutOfScopeOnly
    # 'continue' has its own active emission (those objects can only have
    # InScope=false records, never InScope=true).
    if ($IncludeActiveCerts -and $ActiveRecords.Count -gt 0) {
        foreach ($Record in $ActiveRecords) {
            $ActiveDetail = if ($Record.InScope) {
                "Active in-scope certificate (no action required)"
            } else {
                "Active out-of-scope certificate (issuer outside RequiredIssuer policy; no action)"
            }
            $Results.Add((New-ResultRecord `
                -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                -Thumbprint $Record.Thumbprint -Subject $Record.Subject -Issuer $Record.Issuer `
                -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                -Action "Skipped" -Type "Active" `
                -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                -Detail $ActiveDetail
            ))
        }
    }

    # ── End-of-object flush ───────────────────────────────────────────────
    # Single conditional with two mutually-exclusive triggers. Either:
    #   1. -EagerFlush + a successful committed AD write — drain so the on-
    #      disk audit log reflects every committed change up to a crash. We
    #      drain HERE (after Active rows are emitted) rather than inside the
    #      commit block so a single flush per object covers all rows about
    #      that object: Expired/Corrupt removal records AND the surviving
    #      Active inventory rows.
    #   2. Size-based buffer cap (>=1000 rows) — bounds memory growth in
    #      ALL modes, including DryRun + EagerFlush (where trigger #1 never
    #      fires because there are no AD writes). Without this, a long
    #      DryRun with -IncludeActiveCerts could buffer the entire run.
    #
    # Why elseif (not two separate ifs): right after an EagerFlush the
    # buffer is empty, so the size-cap branch would always be a no-op
    # anyway. The elseif makes that explicit and prevents a future edit
    # from accidentally introducing a double-flush by adding code that
    # appends to $Results between the two branches.
    if ($EagerFlush -and -not $DryRun -and $RemovalApplied) {
        Flush-ResultsBuffer `
            -Buffer          $Results `
            -LogFile         $LogFile `
            -ActionCounts    $ActionCounts `
            -TypeCounts      $TypeCounts `
            -CsvInitialized  ([ref]$script:CsvInitialized)
    }
    elseif ($Results.Count -ge 1000) {
        Flush-ResultsBuffer `
            -Buffer          $Results `
            -LogFile         $LogFile `
            -ActionCounts    $ActionCounts `
            -TypeCounts      $TypeCounts `
            -CsvInitialized  ([ref]$script:CsvInitialized)
    }
}

#endregion

#region ── Summary & Export ───────────────────────────────────────────────────

# Single end-of-run flush: handles both the residual buffer in streaming
# mode (after mid-loop flushes drained most of $Results) and the entire
# buffer in non-streaming mode (where no mid-loop flush ever ran). The
# Flush function performs counter aggregation AND CSV write atomically
# and is a no-op when the buffer is empty, so this works for runs that
# produced no audit rows at all.
Flush-ResultsBuffer `
    -Buffer          $Results `
    -LogFile         $LogFile `
    -ActionCounts    $ActionCounts `
    -TypeCounts      $TypeCounts `
    -CsvInitialized  ([ref]$script:CsvInitialized)

# Release the SHA-256 native handle now that the corrupt-blob processing
# is over. (.NET would clean this up via finalizer eventually; explicit
# Dispose is just good hygiene.)
if ($null -ne $BlobHasher) { $BlobHasher.Dispose() }

if ($ShowProgress) { Write-Progress -Activity "Processing AD objects" -Completed }

Write-Section "Summary" -Color Green

$GetCount = {
    param([hashtable]$Table, [string]$Key)
    if ($Table.ContainsKey($Key)) { return $Table[$Key] }
    return 0
}

$ARemoved    = & $GetCount $ActionCounts "Removed"
$AIdentified = & $GetCount $ActionCounts "Identified"
$ASkipped    = & $GetCount $ActionCounts "Skipped"
$AFailed     = & $GetCount $ActionCounts "Failed"

$TExpired    = & $GetCount $TypeCounts "Expired"
$TCorrupt    = & $GetCount $TypeCounts "Corrupt"
$TOos        = & $GetCount $TypeCounts "OutOfScopeOnly"
$TProtection = & $GetCount $TypeCounts "Protection"
$TKill       = & $GetCount $TypeCounts "KillSwitch"
$TActive     = & $GetCount $TypeCounts "Active"

Write-Host "  Target                       : $Target"
Write-Host "  Issuer scope                 : $(if ($RequiredIssuer) { "$IssuerMatchMode '$RequiredIssuer'" } else { '<none>' })"
Write-Host ""
Write-Host "  -- Object-level counters --"
Write-Host "  Objects scanned              : $ObjectsScanned"
Write-Host "  Objects with certs           : $ObjectsWithCerts"
Write-Host "  Objects modified*            : $ObjectsModified"            -ForegroundColor $(if ($ObjectsModified)      { "Green"   } else { "Gray" })
Write-Host "  Objects ISE-broken**         : $ObjectsBroken"              -ForegroundColor $(if ($ObjectsBroken)        { "Yellow"  } else { "Gray" })
Write-Host "  Objects empty-attr protected : $ObjectsProtected"           -ForegroundColor $(if ($ObjectsProtected)     { "DarkCyan"} else { "Gray" })
Write-Host "  Objects out-of-scope only    : $ObjectsOutOfScopeOnly"      -ForegroundColor $(if ($ObjectsOutOfScopeOnly){ "DarkGray"} else { "Gray" })
Write-Host "  Objects kill-switched        : $ObjectsKillSwitched"        -ForegroundColor $(if ($ObjectsKillSwitched)  { "Red"     } else { "Gray" })
Write-Host ""
Write-Host "  -- Domain cert population (in query scope) --"
Write-Host "  Total cert blobs seen        : $TotalCertsSeen"             -ForegroundColor Cyan
Write-Host "  Valid in-scope               : $TotalValidInScope"          -ForegroundColor $(if ($TotalValidInScope) { "Green" } else { "Gray" })
Write-Host "  Out-of-scope                 : $TotalOutOfScope"            -ForegroundColor $(if ($TotalOutOfScope)   { "DarkGray" } else { "Gray" })
Write-Host "  Expired                      : $TotalExpiredSeen"           -ForegroundColor $(if ($TotalExpiredSeen)  { "Yellow" } else { "Gray" })
Write-Host "  Corrupt                      : $TotalCorruptSeen"           -ForegroundColor $(if ($TotalCorruptSeen)  { "Magenta" } else { "Gray" })

# Per-class breakdown — always printed for consistency. For User/Computer
# runs the unused class shows zeros, which is harmless and makes the
# section's structure stable across invocations.
Write-Host ""
Write-Host "  -- Per-class breakdown --"
Write-Host ("  {0,-13} Seen={1,-7} Valid={2,-7} OOS={3,-7} Expired={4,-7} Corrupt={5}" -f `
    "users:",     $ClassTotals.user.Seen,     $ClassTotals.user.Valid,     $ClassTotals.user.OOS,     $ClassTotals.user.Expired,     $ClassTotals.user.Corrupt)
Write-Host ("  {0,-13} Seen={1,-7} Valid={2,-7} OOS={3,-7} Expired={4,-7} Corrupt={5}" -f `
    "computers:", $ClassTotals.computer.Seen, $ClassTotals.computer.Valid, $ClassTotals.computer.OOS, $ClassTotals.computer.Expired, $ClassTotals.computer.Corrupt)

$populationSum = $TotalValidInScope + $TotalOutOfScope + $TotalExpiredSeen + $TotalCorruptSeen
if ($populationSum -ne $TotalCertsSeen) {
    # This invariant is supposed to hold tautologically: every cert blob
    # the script classifies bumps exactly one of the four sub-counters
    # AND the global $TotalCertsSeen. Kill-switched objects don't
    # contribute to either side (they 'continue' before classification
    # and before the totals increment). If this fires, something
    # genuinely unexpected happened — re-examine the classify/totals
    # block before trusting the run.
    Write-Warning ("  Population invariant mismatch: $TotalValidInScope + $TotalOutOfScope + $TotalExpiredSeen + $TotalCorruptSeen = $populationSum, expected $TotalCertsSeen. " +
                   "This should not happen — please re-run and report if reproducible.")
}
Write-Host ""
Write-Host "  -- Record-level (per blob)  --"
Write-Host "  Action: Removed              : $ARemoved"                   -ForegroundColor $(if ($ARemoved)             { "Green"   } else { "Gray" })
Write-Host "  Action: Identified (DryRun)  : $AIdentified"                -ForegroundColor DarkYellow
Write-Host "  Action: Skipped              : $ASkipped"
Write-Host "  Action: Failed               : $AFailed"                    -ForegroundColor $(if ($AFailed)              { "Red"     } else { "Gray" })
Write-Host "  Type:   Expired              : $TExpired"
Write-Host "  Type:   Corrupt              : $TCorrupt"                   -ForegroundColor $(if ($TCorrupt)             { "Magenta" } else { "Gray" })
Write-Host "  Type:   OutOfScopeOnly       : $TOos"
Write-Host "  Type:   Protection           : $TProtection"
Write-Host "  Type:   KillSwitch           : $TKill"                      -ForegroundColor $(if ($TKill)                { "Red"     } else { "Gray" })
Write-Host "  Type:   Active (inventory)   : $TActive"                    -ForegroundColor $(if ($TActive)              { "Green"   } else { "Gray" })

Write-Host ""
Write-Host "  *  modified = write attempted (committed run) or planned (DryRun)."
Write-Host "  ** ISE-broken = no in-scope, non-expired cert remains for the object" -ForegroundColor $(if ($ObjectsBroken) { "Yellow" } else { "Gray" })
Write-Host "     after this run. These objects fail ISE binary comparison until"   -ForegroundColor $(if ($ObjectsBroken) { "Yellow" } else { "Gray" })
Write-Host "     autoenrollment publishes a new cert AND replication reaches the"  -ForegroundColor $(if ($ObjectsBroken) { "Yellow" } else { "Gray" })
Write-Host "     DC the ISE Join Point reads from."                                 -ForegroundColor $(if ($ObjectsBroken) { "Yellow" } else { "Gray" })

# CSV export status
# After the unified Flush above, the audit log either exists (and rows
# were written) or it doesn't (no audit-worthy events in scope). The
# old fallback Export-Csv block here is gone — Flush handles both paths.
if ($script:CsvInitialized) {
    Write-Host ""
    Write-Host "  Audit log: $LogFile" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "  No audit-worthy events found in scope (no CSV written)." -ForegroundColor Gray
}

# Replication reminder for live runs
if (-not $DryRun -and $ARemoved -gt 0) {
    Write-Host ""
    Write-Host "  Reminder: AD changes must replicate before ISE sees them." -ForegroundColor Cyan
    Write-Host "  - If ISE's Join Point points to a specific DC, prefer that DC for -Server." -ForegroundColor Cyan
    Write-Host "  - Otherwise allow your normal intra-site replication interval before retesting." -ForegroundColor Cyan
}

# Out-GridView (interactive sessions only)
# Reads the CSV back from disk rather than from $Results — the unified
# Flush has cleared the in-memory buffer by this point, so we'd otherwise
# show an empty grid. Re-reading is fine: it only happens in interactive
# sessions where Out-GridView is available, and the CSV is bounded in
# size by streaming-flush semantics.
if ($script:CsvInitialized) {
    if (Get-Command Out-GridView -ErrorAction SilentlyContinue) {
        Import-Csv -Path $LogFile |
            Out-GridView -Title "Cert Audit  |  Target=$Target  |  DryRun=$DryRun  |  Issuer=$RequiredIssuer ($IssuerMatchMode)"
    } else {
        Write-Host "  (Out-GridView unavailable — review the CSV above.)" -ForegroundColor DarkGray
    }
}

Write-Host ""

#endregion
```