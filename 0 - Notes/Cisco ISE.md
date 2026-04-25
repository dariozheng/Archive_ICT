---
categories:
  - "[[Networking]]"
  - "[[Security]]"
topic@networking:
  - "[[Networking General]]"
topic@security:
  - "[[Security General]]"
tags:
  - project
  - nac
  - cisco
  - scor/sise
  - ccnp
  - tech_doc
icon: SiCisco
iconColor: "#1BA0D7"
aliases:
  - Identity Service Engine
  - Cisco Identity Service Engine
  - ISE
cssclasses:
  - img-grid
---
Cisco <strong>Identity Service Engine</strong> (ISE) is a <strong>Network Access Control</strong> solution that manages access to network ensuring only authenticated, authorized, and compliant users and devices can connect. 

An ISE-based network access control solution has four components: <mark style="background: #FFB86CA6;"><strong>endpoints</strong></mark>, <mark style="background: #FFB8EBA6;"><strong>network access devices (NAD)</strong></mark>, <mark style="background: #ABF7F7A6;"><strong>Cisco ISE</strong></mark>, and <mark style="background: #FFF3A3A6;"><strong>external services</strong></mark>.
<strong>Endpoints</strong> need <mark style="background: #BBFABBA6;">network access</mark> and the <strong>network access devices (NAD)</strong> provide network access to endpoints, based on instructions from <strong>ISE</strong>. 
ISE can leverage <strong>external services</strong> to understand more about the corresponding endpoints for policy decisions.

<mark style="background: #FFB8EBA6;">The server ISE acts as the core, it's where the policies are defined</mark>. <mark style="background: #FF5582A6;">The network devices acts as the authenticator</mark> and <strong>enforce</strong> the policies from the server ISE. <mark style="background: #FFF3A3A6;">The endpoint receives the response</mark> <mark style="background: #FFB86CA6;">given by the server ISE</mark> <mark style="background: #BBFABBA6;">from the network access device</mark>. Most of the high level host endpoint have <mark style="background: #ABF7F7A6;">supplicants that allow them to communicate with the authenticator or NAD</mark>.  <mark style="background: #D2B3FFA6;">The server ISE can use external services</mark>, such as the <strong>Microsoft Active Directory</strong>, <mark style="background: #D2B3FFA6;">to get knowledge about the users</mark>. 
# ISE Server
Cisco Identity Services Engine (ISE) is an <strong>identity-based network access control</strong> and <strong>policy enforcement system</strong>. It functions as a common policy engine that enables <mark style="background: #FFF3A3A6;">endpoint access control </mark>and <mark style="background: #BBFABBA6;">network device administration</mark> for enterprises.











# External Services
ISE can leverage existing infrastructures to manage user network access. 
## Microsoft Servers
In most cases the external services used are Microsoft Servers, with Active Directory as identity store, Certificate Authority for the certificates to use together with the user and/or host on the Active Directory and Group Policy Management to rollout the configuration to clients.  
### Active Directory
![[Pasted image 20260421124607.png]]
Cisco ISE can join Microsoft Active Directory as an External Identity Source under the item Active Directory. 

The AD is used to identify the users when they do an authentication. They can be checked with their domain password or with the domain certificates they provide ISE.

For the server ISE to be able to join the domain, it has to have a machine account in the domain and a DNS entry, while the AD User Name must have the permissions to join ISE to AD. 
![[Pasted image 20260421152119.png]]

On this section it is also possible to retrieve groups from the AD to create policies around the user group identity. 
![[Pasted image 20260421125524.png]]
### Certificate Authority #certificates
The Certificate Authority service is used to provide certificates to both ISE server itself and clients that will use it to do network access authentication. 
#### Server Certificates
There are many portals hosted in ISE. All the ISE portals require encryption by default. In other words, all portals in ISE use HTTPS, and a certificate on ISE is used to secure the communication.
Certificates are also used to secure EAP communications, to form a Transport Layer Security (TLS) tunnel between an endpoint and a RADIUS server, or to identify the RADIUS server (ISE) to the client (supplicant):
- <strong>Admin</strong>: for <mark style="background: #FF5582A6;">ISE Admin Portal</mark>. If this is chosen the ISE node needs to restart all services to use the newly applied certificate.
- <strong>EAP Authentication</strong>: ISE will use this certificate for <mark style="background: #FFB86CA6;">EAP protocols that use SSL/TLS tunneling</mark>.
- <strong>RADIUS DTLS</strong>: RADIUS over Datagram Transport Layer Security encrypt the full packet. The certificate can be used to establish and secure the communication between the <mark style="background: #FFB8EBA6;">ISE server and the NAD</mark>.
- <strong>Portal</strong>: Certificates used for ISE <mark style="background: #BBFABBA6;">user portals</mark>. Which can be Guest Portal, Client Provisioning Portal, MDM Portal, BYOD Portal, Sponsor Portal, or My Devices Portal. The Guest Portal usually should have a public certificate as it should be used to external devices. 
- <strong>pxGrid</strong>: This certificate will be used to establish trust and build a <mark style="background: #ABF7F7A6;">secure connection between ISE and third-party pxGrid clients</mark> to share contextual information. 
![[Pasted image 20260421153234.png]]

To add a certificate
##### Trusted Certificates

###### CRL Revocation List
##### Certificate Authentication Profile
![[Pasted image 20260424144802.png]]
<strong>Certificate Authentication Profile</strong>(CAP) section is used to decide which <mark style="background: #FF5582A6;">attribute of the certificate</mark> the server ISE will use to check identity of the client. 

Here it is set to Subject Alternate Name (SAN) as the CAP will be used for both Machine and User EAP authentication protocols. The Users in the SAN will use the UPN while the Machines will use the DNS Name.

| User Certificate                     | Machine Certificate                  |
| ------------------------------------ | ------------------------------------ |
| ![[Pasted image 20260424145144.png]] | ![[Pasted image 20260424145227.png]] |
The selection <strong>Match Client Certificate Against Certificate In Identity Store</strong>:
- <strong>Only to resolve identity ambiguity</strong>: This is the standard setting. It tells ISE to use the certificate information to identify the user in AD, but it doesn't require a byte-for-byte match of the certificate itself against an AD attribute.
- <strong>Always perform binary comparison</strong>: <mark style="background: #FF5582A6;">Use this only if you have physically uploaded or published the user/machine certificates into the <strong>userCertificate</strong> attribute in Active Directory</mark>. <mark style="background: #FFB86CA6;">ISE will then perform a byte-for-byte comparison between the certificate the client presents and the one stored in AD</mark>. If they don't match exactly, authentication will fail.
   [[#Domain Users Certificate| Link to configuration of a domain user certificate and the img of userCertificate attribute]]
   [[#Script To Remove Expired userCertificate| Link to the managing of expired userCertificate attribute]]
- **Never:** Choose this if you are not using an identity store at all for this profile. This would be common for Guest or BYOD setups where you just want to verify that the certificate is valid and signed by a trusted CA without checking it against an AD account.
#### Client Certificates 
Client Certificates are used by users, machine or both to authenticate to ISE. 
In the server SubordinateCA, on the Certificate Authority service create the Certificate Templates that will be used by Domain Users, Domain Machines, and non Domain Users. 
##### Domain Users Certificate
For Users Certificates, duplicate from the default <strong>User</strong> certificate template:
- On the <u>General tab</u> create a logical template name. The <strong>Publish certificate in Active Directory</strong> is used to publish the certificate into the user <strong>userCertificate</strong> attribute in Active Directory. ![[Pasted image 20260424150748.png|200]]
- On the <u>Request Handling tab</u>, uncheck the <strong>Allow private key to be exported</strong> box. 
- On the <u>Extensions tab</u>, highlight the <strong>Application Policies</strong> and click <strong>Edit</strong>. The <strong>Edit Application Policies Extension</strong> window will pop up. Click the <strong>Add</strong> button. Then, add the <strong>Server Authentication</strong> policy to the <strong>Application Policies</strong>. Then click <strong>OK</strong> to close the <strong>Edit Application Policies Extension</strong> window.
- On the <u>Security tab</u>, highlight <strong>Domain Users</strong> and check the <strong>Allow</strong> boxes for <strong>Read</strong>, <strong>Enroll</strong>, and <strong>Autoenroll</strong> under the Permissions pane. <mark style="background: #FF5582A6;">This will be important when configuring our Group Policy to <strong>auto-enroll</strong> users with a user certificate</mark> for EAP authentication when they log into their computers. 
- On the <u>Subject Name tab</u>. If this is a lab environment, <mark style="background: #ADCCFFA6;">you may want to exclude email addresses from the Certificate template</mark> as your environment may not have an Exchange server or SMTP server integrated with Active Directory to pre-populate that information in the AD. <mark style="background: #ADCCFFA6;">If that information is not in the Active Directory record and this box is checked in the template, your certificate will not be issued to the user</mark>. <mark style="background: #FFB8EBA6;">The UPN in Alternate Subject Name (SAN) is what the ISE Server will use to check the identity of the machine in the Active Directory</mark>, if the Certificate Authentication Profile is configured with the SAN.

| General tab               | Request Handling tab               | Extensions tab               | Security tab               | Subject Name tab               |
| ------------------------- | ---------------------------------- | ---------------------------- | -------------------------- | ------------------------------ |
| ![[General tab.png\|200]] | ![[Request Handling tab.png\|200]] | ![[Extensions tab.png\|200]] | ![[Security tab.png\|200]] | ![[Subject Name tab.png\|200]] |
Once the Domain Users Certificate Template is created, <mark style="background: #FF5582A6;">issue the template only on one of the SubordinateCA server</mark> <mark style="background: #FFB86CA6;">if the design is to separate User Certificates</mark> from <mark style="background: #BBFABBA6;">Machine Certificates</mark>. 
In this case the <strong>User Certificate</strong> is issued on the <strong>SubordinateCA01</strong>.
![[Pasted image 20260424135651.png]]
##### Domain Admin Certificate
For the <strong>Domain Admin Certificate</strong> template copy the <strong>Domain User Certificate</strong> template and <mark style="background: #FFF3A3A6;">change Security tab <strong>Group or user names</strong> section</mark>, <mark style="background: #FFB86CA6;">remove Domain Users</mark> and in <mark style="background: #ABF7F7A6;">Domain Admin permissions, allow Read, Write, and Enroll</mark>. The Write permission is used to modify the certificate template. 

As the Domain Admin Certificate is made for admins that have a domain user account but not a domain computer, the enrollment is done manually. 
###### Enrollment - Windows Manual
![[Manual Enrollment of Admin Certificate.mp4]]
###### Enrollment - Windows Script
```powershell
param(
    [ValidateSet("All", "Step1", "Step2")]
    [string]$Step = "All",
    [string]$CertPath = "$env:USERPROFILE\Downloads\certnew.cer"
)
# Paths
$infPath = Join-Path $env:TEMP "cert_request.inf"
$csrPath = Join-Path $env:USERPROFILE "Desktop\request.csr"
$subcaUrl = "https://subordinateca01.publiacqua.it/certsrv/certrqxt.asp"

$infContent = @"
[NewRequest]
Subject = "CN=$env:USERNAME"
KeyLength = 2048
Exportable = TRUE
MachineKeySet = FALSE
RequestType = PKCS10
ProviderName = "Microsoft Software Key Storage Provider"
[EnhancedKeyUsageExtension]
OID = 1.3.6.1.5.5.7.3.2 ; Client Authentication
"@

function Move-UsedFilesToRecycleBin {
    $filesToMove = @($infPath, $csrPath, $CertPath)
    foreach ($file in $filesToMove) {
        if (Test-Path $file) {
            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                $file,
                [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin
            )
        }
    }
}

function Invoke-Step1 {
    Set-Content -Path $infPath -Value $infContent
    certreq -new $infPath $csrPath

    if (Test-Path $csrPath) {
        $csrText = Get-Content $csrPath -Raw
        $csrText | Set-Clipboard
        Write-Host "`n CSR saved and copied to clipboard." -ForegroundColor Green
        Write-Host "`n Use Publiacqua domain credentials." -ForegroundColor Green
        Write-Host "`n Paste the CSR to $subcaUrl" -ForegroundColor Green
        Write-Host "`n Certificate Template must be EAP-Admin-User." -ForegroundColor Green
        Write-Host "`n Download the Base64 certificate as certnew.cer in the Download folder." -ForegroundColor Green
        Start-Process $subcaUrl
    }
    else {
        Write-Error "Failed to generate CSR."
        return $false
    }
    return $true
}

function Invoke-Step2 {
    if (-not (Test-Path $CertPath)) {
        Write-Error "`n Certificate file not found: $CertPath"
        Write-Host "`n If needed, specify it explicitly:" -ForegroundColor Yellow
        Write-Host "`n .\EAP-Admin-User_Cert_Enroll.ps1 -Step Step2 -CertPath 'C:\path\certnew.cer'" -ForegroundColor Yellow
        return $false
    }
    if (Import-Certificate -FilePath $CertPath -CertStoreLocation "Cert:\CurrentUser\My") {
        Write-Host "`n certnew.cer installed to CurrentUser\Personal store." -ForegroundColor Green
        Add-Type -AssemblyName Microsoft.VisualBasic
        Move-UsedFilesToRecycleBin
        Write-Host "`n Used files sent to user Recycle Bin." -ForegroundColor Green
        return $true
    }
    else {
        Write-Error "`n Certificate import failed."
        return $false
    }
}

if ($Step -eq "Step1") {
    [void](Invoke-Step1)
}
elseif ($Step -eq "Step2") {
    if (-not (Invoke-Step2)) {
        exit 1
    }
}
elseif ($Step -eq "All") {
    $okStep1 = Invoke-Step1
    if (-not $okStep1) {
        exit 1
    }
    Write-Host "`n Once the certnew.cer is downloaded, press ENTER to continue " -ForegroundColor Yellow
    $userInput = Read-Host "`n Press ENTER to continue or Q to quit"
    if ($userInput -match '^[Qq]$') {
        Write-Host "`n Stopped after Step 1. You can later run: .\EAP-Admin-User_Cert_Enroll.ps1 -Step Step2" -ForegroundColor Yellow
        exit 0
    }
    if (-not (Invoke-Step2)) {
        exit 1
    }
}
```

###### Enrollment - Apple Script
```applescript
-- Define paths
set userName to short user name of (system info)
set desktopPath to (path to desktop)
set downloadsPath to (path to downloads folder)
set csrPath to (desktopPath as string) & "request.csr"
set keyPath to (desktopPath as string) & "private.key"
set p12Path to (desktopPath as string) & "identity.p12"
set certName to "certnew.cer"
set subCaUrl to "https://subordinateca01.publiacqua.it/certsrv/certrqxt.asp"
set tempPass to "1234"

set certInDownloads to (downloadsPath as string) & certName

-- Files to move to Trash at the end
set filesToTrash to {csrPath, keyPath, p12Path, certInDownloads}
set caughtError to ""

try
	-- 1. Generate Private Key and CSR
	do shell script "openssl req -new -newkey rsa:2048 -nodes -keyout " & quoted form of POSIX path of keyPath & " -out " & quoted form of POSIX path of csrPath & " -subj '/CN=" & userName & "'"
	
	-- 2. Copy CSR and open portal
	set csrText to do shell script "cat " & quoted form of POSIX path of csrPath
	set the clipboard to csrText
	open location subCaUrl
	
	-- 3. Wait for user
	display dialog "CSR COPIED! 

1. Paste into portal and select Template: EAP-Admin-User.
2. Download the 'Base 64 encoded' certificate.
3. Click 'Finalize' to link the key, install into Keychain, and clean up temporary files" with icon note buttons {"Finalize"} default button 1
	
	-- 4. Ensure downloaded certificate exists in Downloads
	set certDownloadsPosix to quoted form of POSIX path of certInDownloads
	do shell script "test -f " & certDownloadsPosix
	
	-- 5. Create PKCS#12 bundle from key + cert
	do shell script "openssl pkcs12 -export -out " & quoted form of POSIX path of p12Path & " -inkey " & quoted form of POSIX path of keyPath & " -in " & quoted form of POSIX path of certInDownloads & " -passout pass:" & quoted form of tempPass
	
	-- Import into the login keychain
	-- -P provides the password for the P12; -T allows the codesign tool access
	do shell script "security import " & quoted form of POSIX path of p12Path & " -k ~/Library/Keychains/login.keychain-db -P " & quoted form of tempPass & " -T /usr/bin/codesign"
	
	display notification "Certificate and key installed in Keychain!" with title "Success"
	
on error anyError
	set caughtError to anyError
end try

my moveToTrash(filesToTrash)
if caughtError is not "" and caughtError does not contain "User canceled" then
	display dialog "Error: " & caughtError buttons {"OK"} default button 1
end if

-- TRASH HANDLER
on moveToTrash(fileList)
	tell application "Finder"
		repeat with filePath in fileList
			if exists file filePath then
				delete file filePath
			end if
		end repeat
	end tell
end moveToTrash
```

##### Domain Computer Certificate
For Computer Certificates, duplicate from the default <strong>Workstation Authentication</strong> certificate template:
- On the <u>General tab</u> create a logical template name, the <strong>Publish certificate in Active Directory</strong> is used to publish the certificate into the computer <strong>userCertificate</strong> attribute in Active Directory. ![[Pasted image 20260424150609.png|200]]
- On the <u>Extensions tab</u>, highlight the <strong>Application Policies</strong> and click <strong>Edit</strong>. The <strong>Edit Application Policies Extension</strong> window will pop up. Click the <strong>Add</strong> button. Then, add the <strong>Server Authentication</strong> policy to the <strong>Application Policies</strong>. Then click <strong>OK</strong> to close the <strong>Edit Application Policies Extension</strong> window.
- On the <u>Security tab</u>, highlight <strong>Domain Computers</strong> and check the <strong>Allow</strong> boxes for <strong>Read</strong>, <strong>Enroll</strong>, and <strong>Autoenroll</strong> under the Permissions pane. <mark style="background: #FF5582A6;">This will be important when configuring our Group Policy to <strong>auto-enroll</strong> computers with a machine certificate</mark> for EAP authentication when they log into their computers. 
- On the <u>Subject Name tab</u> under Subject Name Format, change it to <strong>Fully distinguished name</strong>, and leave the DNS Name checked. <mark style="background: #FFB8EBA6;">The DNS name in Alternate Subject Name (SAN) is what the ISE Server will use to check the identity of the machine in the Active Directory</mark>, if the Certificate Authentication Profile is configured with the SAN.

| General tab                          | Extensions tab                       | Security tab                         | Subject Name tab                     |
| ------------------------------------ | ------------------------------------ | ------------------------------------ | ------------------------------------ |
| ![[Pasted image 20260424150448.png]] | ![[Pasted image 20260424141629.png]] | ![[Pasted image 20260424141754.png]] | ![[Pasted image 20260424141809.png]] |
Like the User certificate templates <mark style="background: #FF5582A6;">issue the template only on one of the SubordinateCA server</mark> <mark style="background: #FFB86CA6;">if the design is to separate User Certificates</mark> from <mark style="background: #BBFABBA6;">Machine Certificates</mark>. 
In this case the <strong>Machine Certificate</strong> is issued on the <strong>SubordinateCA02</strong>.
![[Pasted image 20260424141851.png]]
##### Script To Remove Expired userCertificate
The expired certificates in the userCertificate attribute cannot be removed automatically, we should remove them manually or with the help of a script.


```powershell
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
```
### Group Policy Management
The Group Policy Management service is used to deploy the configuration of Windows native supplicant and the rollout of the Client Certificates. 

# Network Devices
# Tutorial
# Reference 
| Voce                  | Topic        | Link                                                                                                      |
| --------------------- | ------------ | --------------------------------------------------------------------------------------------------------- |
| Certificate Templates | Certificates | https://sendthepayload.com/configuring-certificate-templates-with-active-directory-certificate-services/# |
| Windows Certificates  | Certificates | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/certreq_1                |
|                       |              |                                                                                                           |
