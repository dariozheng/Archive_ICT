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

 By default this script is in read only mode, read the description for the how to use.
```powershell
<#
.SYNOPSIS
    Cleans up expired/corrupt certificates from the AD `userCertificate`
    attribute on user and/or computer objects. Designed to be run alongside
    Cisco ISE deployments that use Certificate Binary Comparison as part of
    EAP-TLS authorization. 
    
    The script should be run in UTF-8 BOM mode.

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
    - Streaming CSV audit log with normalized Action/Type columns plus
      issuer, NotBefore/NotAfter, and per-object active-cert counts.
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
        Issuer           : Issuer DN
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

.PARAMETER RemoveCorruptBlobs
    When $true, unreadable/corrupt certificate blobs are removed in addition
    to expired certificates. Default $false.

.PARAMETER AllowFullRemoval
    When $false (default), the script refuses to leave the userCertificate
    attribute empty.

.PARAMETER Server
    Optional DC for reads/writes. Pin to the DC ISE's Join Point queries, can be checked in ISE
    server admin portal, in External Identity Sources, Active Directory, Connection, Domain Controller.

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

.EXAMPLE
    # Default: dry-run on users in the current domain
    .\Invoke-ExpiredCertCleanup.ps1

.EXAMPLE
    # ISE-scoped dry-run on computers, exact issuer match
    .\Invoke-ExpiredCertCleanup.ps1 `
        -Target Computer `
        -RequiredIssuer 'CN=Publiacqua Issuing CA, DC=publiacqua, DC=local' `
        -IssuerMatchMode Exact `
        -Server dc01.publiacqua.it

.EXAMPLE
    # Commit removals on computers, exact issuer match, prompt per object
    .\Invoke-ExpiredCertCleanup.ps1 `
        -Target Computer `
        -RequiredIssuer 'CN=Publiacqua Issuing CA, DC=publiacqua, DC=local' `
        -IssuerMatchMode Exact `
        -DryRun:$false -Confirm `
        -Server dc01.publiacqua.it

.NOTES
    Requires the ActiveDirectory module and write permissions for live runs.
    Uses Get-ADObject / Set-ADObject so user and computer classes share one
    code path.

    NOTE on large environments: Get-ADObject materializes the full result
    set before iteration begins, so the kill-switch is a *post-fetch* guard,
    not a query-time abort. For very large domains, scope tightly with
    -SearchBase. The userCertificate=* filter is matched against an
    unindexed attribute in many schemas, so OU scoping is doubly important.
#>

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

    [bool]$IncludeActiveCerts = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

#region ── Helpers ────────────────────────────────────────────────────────────

function Write-Section {
    param([string]$Message, [ConsoleColor]$Color = "Cyan")
    Write-Host ""
    Write-Host ("─" * 72) -ForegroundColor DarkGray
    Write-Host "  $Message" -ForegroundColor $Color
    Write-Host ("─" * 72) -ForegroundColor DarkGray
}

function New-ResultRecord {
    <#
        Audit-record factory. Action/Type are normalized for aggregation;
        Detail is free text. ValidInScope and RemainingAfter give per-record
        context for the parent object so the CSV can be filtered by ISE
        impact (e.g., rows where ValidInScope=0 are objects that will fail
        binary comparison until autoenrollment runs).

        IssuerCN is derived from $Issuer via Get-DnCN — callers do NOT
        pass it explicitly.
    #>
    param(
        [string]$ObjectClass,
        [string]$ObjectName,
        [string]$ObjectDN,
        [string]$Thumbprint   = "N/A",
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
        Timestamp      = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        ObjectClass    = $ObjectClass
        Name           = $ObjectName
        ObjectDN       = $ObjectDN
        Thumbprint     = $Thumbprint
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
                # Wrap each blob in a single-element array so PowerShell does
                # not unroll byte[] into individual integers when building the
                # hashtable passed to -Remove.
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
    param(
        [System.Collections.Generic.List[PSObject]]$Buffer,
        [string]$LogPath,
        [string]$LogFile,
        [hashtable]$ActionCounts,
        [hashtable]$TypeCounts,
        [ref]$CsvInitialized
    )

    if ($Buffer.Count -eq 0) { return }

    foreach ($r in $Buffer) {
        Update-RecordCounters -Record $r -ActionCounts $ActionCounts -TypeCounts $TypeCounts
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

function Get-DnCN {
    <#
        Extract the CN= component from an X.500 distinguished name.

        Splits on unescaped commas (commas not preceded by '\') so DNs like
        "CN=Smith\, John,DC=example,DC=com" parse correctly. Returns the
        first CN found, with escaped commas un-escaped. Falls back to the
        full DN if no CN is present, and to "N/A" for placeholder values.

        Used to populate the IssuerCN column from the Issuer DN — gives
        a short, filterable value in Excel (e.g. "Publiacqua Issuing CA")
        without needing to parse the full DN every time.
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

#endregion

#region ── Initialisation ─────────────────────────────────────────────────────

$Now     = Get-Date
$LogFile = Join-Path $LogPath "ExpiredCertCleanup_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
$Results = [System.Collections.Generic.List[PSObject]]::new()
$ActionCounts    = @{}
$TypeCounts      = @{}
$CsvInitialized  = $false
$IsStreamingMode = $false

# ── Domain-wide cert population counters ───────────────────────────────────
# Cheap integer accumulators incremented per object after classification.
# Only counts blobs from objects that passed the per-object kill-switch
# (i.e., the population the script actually inspected).
$TotalCertsSeen     = 0   # every userCertificate value classified
$TotalValidInScope  = 0   # parseable, in-scope per -RequiredIssuer, not expired
$TotalOutOfScope    = 0   # parseable but issuer didn't match policy
$TotalExpiredSeen   = 0   # parseable, in-scope, NotAfter < now
$TotalCorruptSeen   = 0   # blob failed X509 parse

Write-Section "Expired Certificate Cleanup  |  Target=$Target  |  DryRun=$DryRun"
if ($DryRun) {
    Write-Host "  !! DRY-RUN — no changes will be written to AD. !!" -ForegroundColor Yellow
}
if ($RequiredIssuer) {
    Write-Host "  Issuer scope ($IssuerMatchMode): '$RequiredIssuer'" -ForegroundColor Cyan
} else {
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
    ResultSetSize  = $null
    ResultPageSize = 1000
}
if ($SearchBase) { $GetADObjectParams.SearchBase = $SearchBase }
if ($Server)     { $GetADObjectParams.Server     = $Server     }
if ($Credential) { $GetADObjectParams.Credential = $Credential }

try {
    $ObjectStream = Get-ADObject @GetADObjectParams
    Write-Host "  LDAP filter: $LdapFilter" -ForegroundColor DarkGray
    Write-Host "  Streaming objects with at least one userCertificate value..." -ForegroundColor Cyan
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

foreach ($AdObject in $ObjectStream) {
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
                        Issuer     = $Cert.Issuer
                        NotBefore  = $Cert.NotBefore.ToString("yyyy-MM-dd HH:mm:ss")
                        NotAfter   = $Cert.NotAfter.ToString("yyyy-MM-dd HH:mm:ss")
                        InScope    = $true
                    })
                }
            }
        } catch {
            $CorruptBlobs.Add($CertData)
            $BlobSha256 = [System.Security.Cryptography.SHA256]::Create()
            try {
                $HashHex = [System.BitConverter]::ToString($BlobSha256.ComputeHash($CertData))
            } finally {
                $BlobSha256.Dispose()
            }
            $CorruptRecords.Add([PSCustomObject]@{
                Thumbprint = "N/A (corrupt)"
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
    $TotalCertsSeen    += $AdObject.userCertificate.Count
    $TotalValidInScope += $ValidCount
    $TotalOutOfScope   += $OutOfScopeCount
    $TotalExpiredSeen  += $ExpiredBlobs.Count
    $TotalCorruptSeen  += $CorruptBlobs.Count

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
                -Thumbprint $Record.Thumbprint -Issuer $Record.Issuer `
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
                -Thumbprint $Record.Thumbprint -Issuer $Record.Issuer `
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
        $verb = if ($DryRun) { "would fail" } else { "will fail" }
        if ($RequiredIssuer) {
            Write-Warning "  [$FriendlyName] After cleanup, no certs from issuer matching '$RequiredIssuer' remain. ISE binary comparison $verb for this object until autoenrollment runs."
        } else {
            Write-Warning "  [$FriendlyName] Cleanup $verb leave no non-expired certificates."
        }
    }

    # ── Console log of what's being acted on ──────────────────────────────
    foreach ($Record in $ExpiredRecords) {
        Write-Host ("  [{0}] ({1}) Expired: {2}  issuer={3}  notAfter={4}" -f `
            $FriendlyName, $ObjClass, $Record.Thumbprint, $Record.Issuer, $Record.NotAfter) `
            -ForegroundColor Yellow
    }
    if ($OutOfScopeCount -gt 0 -and $RequiredIssuer) {
        Write-Host ("  [{0}] ({1}) {2} out-of-scope cert(s) ignored." -f `
            $FriendlyName, $ObjClass, $OutOfScopeCount) -ForegroundColor DarkGray
    }

    # ── Commit or simulate ────────────────────────────────────────────────
    if ($BlobsToRemove.Count -gt 0) {
        $ObjectsModified++

        $SetADObjectParams = @{ Identity = $AdObject.DistinguishedName }
        if ($Server)     { $SetADObjectParams.Server     = $Server     }
        if ($Credential) { $SetADObjectParams.Credential = $Credential }

        $RemovalApplied         = $false
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
                $SkippedByShouldProcess = $true
                Write-Host ("  [WhatIf/Confirm] Skipped {0}." -f $FriendlyName) -ForegroundColor DarkYellow
            }

            $ResultAction = if ($DryRun) {
                "Identified"
            } elseif ($SkippedByShouldProcess -or $WhatIfPreference) {
                "Skipped"
            } elseif ($RemovalApplied) {
                "Removed"
            } else {
                "Skipped"
            }
            $WhatIfDetail = if ($SkippedByShouldProcess -or $WhatIfPreference) { " (WhatIf/Confirm)" } else { "" }

            foreach ($Record in $ExpiredRecords) {
                $Results.Add((New-ResultRecord `
                    -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                    -Thumbprint $Record.Thumbprint -Issuer $Record.Issuer `
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
                        -Thumbprint $Record.Thumbprint -Issuer $Record.Issuer `
                        -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                        -Action $ResultAction -Type "Corrupt" `
                        -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                        -Detail "Unreadable/corrupt blob$WhatIfDetail; BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
                    ))
                } else {
                    $Results.Add((New-ResultRecord `
                        -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                        -Thumbprint $Record.Thumbprint -Issuer $Record.Issuer `
                        -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                        -Action "Skipped" -Type "Corrupt" `
                        -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                        -Detail "Unreadable/corrupt blob (RemoveCorruptBlobs=$RemoveCorruptBlobs); BlobHash=$($Record.BlobHash); BlobLength=$($Record.BlobLength)"
                    ))
                }
            }

        } catch {
            Write-Warning "  Failed to update [$FriendlyName]: $($_.Exception.Message)"

            foreach ($Record in $ExpiredRecords) {
                $Results.Add((New-ResultRecord `
                    -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                    -Thumbprint $Record.Thumbprint -Issuer $Record.Issuer `
                    -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                    -Action "Failed" -Type "Expired" `
                    -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                    -Detail $_.Exception.Message
                ))
            }
            foreach ($Record in $CorruptRecords) {
                $Results.Add((New-ResultRecord `
                    -ObjectClass $ObjClass -ObjectName $FriendlyName -ObjectDN $AdObject.DistinguishedName `
                    -Thumbprint $Record.Thumbprint -Issuer $Record.Issuer `
                    -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                    -Action $(if ($RemoveCorruptBlobs) { "Failed" } else { "Skipped" }) -Type "Corrupt" `
                    -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                    -Detail $(if ($RemoveCorruptBlobs) {
                        $_.Exception.Message
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
                -Thumbprint $Record.Thumbprint -Issuer $Record.Issuer `
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
                -Thumbprint $Record.Thumbprint -Issuer $Record.Issuer `
                -NotBefore $Record.NotBefore -NotAfter $Record.NotAfter `
                -Action "Skipped" -Type "Active" `
                -ValidInScope $ValidInScopeStr -RemainingAfter $RemainingStr `
                -Detail $ActiveDetail
            ))
        }
    }

    # ── Streaming flush every 1000 result rows ────────────────────────────
    if ($Results.Count -ge 1000) {
        Flush-ResultsBuffer `
            -Buffer          $Results `
            -LogPath         $LogPath `
            -LogFile         $LogFile `
            -ActionCounts    $ActionCounts `
            -TypeCounts      $TypeCounts `
            -CsvInitialized  ([ref]$CsvInitialized)
        $IsStreamingMode = $true
    }
}

#endregion

#region ── Summary & Export ───────────────────────────────────────────────────

if ($IsStreamingMode -and $Results.Count -gt 0) {
    Flush-ResultsBuffer `
        -Buffer          $Results `
        -LogPath         $LogPath `
        -LogFile         $LogFile `
        -ActionCounts    $ActionCounts `
        -TypeCounts      $TypeCounts `
        -CsvInitialized  ([ref]$CsvInitialized)
} elseif (-not $IsStreamingMode -and $Results.Count -gt 0) {
    foreach ($r in $Results) {
        Update-RecordCounters -Record $r -ActionCounts $ActionCounts -TypeCounts $TypeCounts
    }
}

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
$_PopulationSum = $TotalValidInScope + $TotalOutOfScope + $TotalExpiredSeen + $TotalCorruptSeen
if ($_PopulationSum -ne $TotalCertsSeen) {
    Write-Warning ("  Population invariant mismatch: $TotalValidInScope + $TotalOutOfScope + $TotalExpiredSeen + $TotalCorruptSeen = $_PopulationSum, expected $TotalCertsSeen. " +
                   "Difference is likely from kill-switched objects whose blobs weren't classified.")
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

# CSV export
if ($CsvInitialized) {
    Write-Host ""
    Write-Host "  Audit log: $LogFile" -ForegroundColor Cyan
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
} else {
    Write-Host ""
    Write-Host "  No expired or corrupt certificates found in scope." -ForegroundColor Gray
}

# Replication reminder for live runs
if (-not $DryRun -and $ARemoved -gt 0) {
    Write-Host ""
    Write-Host "  Reminder: AD changes must replicate before ISE sees them." -ForegroundColor Cyan
    Write-Host "  - If ISE's Join Point points to a specific DC, prefer that DC for -Server." -ForegroundColor Cyan
    Write-Host "  - Otherwise allow your normal intra-site replication interval before retesting." -ForegroundColor Cyan
}

# Out-GridView (interactive sessions only, non-streaming)
if ($CsvInitialized) {
    if ($IsStreamingMode) {
        Write-Host "  (Out-GridView skipped: streamed to CSV in batches.)" -ForegroundColor DarkGray
    } elseif (Get-Command Out-GridView -ErrorAction SilentlyContinue) {
        $Results | Out-GridView -Title "Cert Audit  |  Target=$Target  |  DryRun=$DryRun  |  Issuer=$RequiredIssuer ($IssuerMatchMode)"
    } else {
        Write-Host "  (Out-GridView unavailable — review the CSV above.)" -ForegroundColor DarkGray
    }
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
