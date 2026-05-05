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
---
Cisco <strong>Identity Service Engine</strong> (ISE) is a <strong>Network Access Control</strong> solution that manages access to network ensuring only authenticated, authorized, and compliant users and devices can connect. 

An ISE-based network access control solution has four components: <mark style="background: #FFB86CA6;"><strong>endpoints</strong></mark>, <mark style="background: #FFB8EBA6;"><strong>network access devices (NAD)</strong></mark>, <mark style="background: #ABF7F7A6;"><strong>Cisco ISE</strong></mark>, and <mark style="background: #FFF3A3A6;"><strong>external services</strong></mark>.
<strong>Endpoints</strong> need <mark style="background: #BBFABBA6;">network access</mark> and the <strong>network access devices (NAD)</strong> provide network access to endpoints, based on instructions from <strong>ISE</strong>. 
ISE can leverage <strong>external services</strong> to understand more about the corresponding endpoints for policy decisions.

<mark style="background: #FFB8EBA6;">The server ISE acts as the core, it's where the policies are defined</mark>. <mark style="background: #FF5582A6;">The network devices acts as the authenticator</mark> and <strong>enforce</strong> the policies from the server ISE. <mark style="background: #FFF3A3A6;">The endpoint receives the response</mark> <mark style="background: #FFB86CA6;">given by the server ISE</mark> <mark style="background: #BBFABBA6;">from the network access device</mark>. Most of the high level host endpoint have <mark style="background: #ABF7F7A6;">supplicants that allow them to communicate with the authenticator or NAD</mark>.  <mark style="background: #D2B3FFA6;">The server ISE can use external services</mark>, such as the <strong>Microsoft Active Directory</strong>, <mark style="background: #D2B3FFA6;">to get knowledge about the users</mark>. 
# ISE Server
Cisco Identity Services Engine (ISE) is an <strong>identity-based network access control</strong> and <strong>policy enforcement system</strong>. It functions as a common policy engine that enables <mark style="background: #FFF3A3A6;">endpoint access control </mark>and <mark style="background: #BBFABBA6;">network device administration</mark> for enterprises.
## Network Resources
In <strong>Network Resources</strong> are managed <strong>Network Access Devices</strong> (<strong>NAD</strong>), they are the enforcement point of policies set by the server ISE.
### Network Devices Profiles
ISE supports third-party NADs through the use of network device profiles. The NAD profiles are configured to define the capabilities and attributes of these third-party devices.

![[Pasted image 20260505104543.png]]

![[Pasted image 20260505104601.png]]

In a Cisco dominant environment the default network device profile for Cisco is enough.
#### Authentication/Authorization

![[Pasted image 20260505110156.png]]

![[Pasted image 20260505110209.png]]

##### Flow Type Conditions
Enter the attributes and values that your device uses for the various flows like <strong>Wired MAB</strong>, <strong>802.1X</strong>, in the <strong>Flow Type Conditions</strong> section. This is necessary for ISE to detect the right flow type for your device according to the attributes it uses.
<strong>Radius:Service-Type</strong> indicate if the packet is a Ethernet or a Wireless packet.
<strong>Radius:NAS-Port-Type</strong> determine if the authorization protocol is a <strong>Call Check</strong> (Use MAB) <strong>Framed</strong> (Use 802.1X) or <strong>Login</strong> (Web Portal).
##### Attribute Aliasing
<mark style="background: #FF5582A6;"><strong>Attribute Aliasing</strong> allows a <strong>NAD Profile</strong> to map vendor-specific attributes to a common attribute so that policy rules can use the friendly name</mark>. 
It simplifies attribute selection, reduces the number of authentication/authorization policy rules required for different vendor devices, and is potentially less error prone. 
<mark style="background: #ADCCFFA6;">For example, the Wireless SSID involved in a flow could be included in the <strong>Airespace-Wlan-ID</strong>, <strong>Aruba-ESSID-Name</strong>, or <strong>Called-Station-ID</strong> depending on the type of NAD involved</mark>. They can all be aliased to <strong>SSID</strong>.
##### Host Lookup
<strong>Host Lookup</strong> allows you to define which attributes and protocols your device uses for MAB.
Different (non-Cisco) vendors populate the RADIUS Calling-Station-ID and password attributes differently while doing a MAB authentication. For Cisco NADs doing MAB, enabling the Process Host Lookup option is sufficient.
#### Permissions

![[Pasted image 20260505111657.png]]

This section defines which attributes your device uses for setting a VLAN or ACL. 
They may be IETF standard attributes or vendor specific. These are usually published in your device’s Admin Guide.

For the VLAN permission, you can specify a single RADIUS attribute (e.g. Aruba-User-VLAN).

For the ACL permission, you can specify a single RADIUS attribute, to be used for setting a named ACL on NADs relevant to the current NAD profile.
## Policy Sets






# Microsoft Servers
In most cases the external services used are Microsoft Servers, with Active Directory as identity store, Certificate Authority for the certificates to use together with the user and/or host on the Active Directory and Group Policy Management to rollout the configuration to clients.  
## Active Directory

![[Pasted image 20260421124607.png]]

Cisco ISE can join Microsoft Active Directory as an External Identity Source under the item Active Directory. 

The AD is used to identify the users when they do an authentication. They can be checked with their domain password or with the domain certificates they provide ISE.

For the server ISE to be able to join the domain, it has to have a machine account in the domain and a DNS entry, while the AD User Name must have the permissions to join ISE to AD. 

![[Pasted image 20260421152119.png]]

On this section it is also possible to retrieve groups from the AD to create policies around the user group identity. 

![[Pasted image 20260421125524.png]]

## Certificate Authority #certificates
The Certificate Authority service is used to provide certificates to both ISE server itself and clients that will use it to do network access authentication. 
### Server Certificates
The ISE server has two types of certificates, system certificates that are used to identify itself, and trusted certificates that are used to validate clients.
#### System Certificates
There are many portals hosted in ISE. All the ISE portals require encryption by default. In other words, all portals in ISE use HTTPS, and a certificate on ISE is used to secure the communication.
Certificates are also used to secure EAP communications, to form a Transport Layer Security (TLS) tunnel between an endpoint and a RADIUS server, or to identify the RADIUS server (ISE) to the client (supplicant)

![[Pasted image 20260421153234.png]]

##### Admin Certificate
For <mark style="background: #FF5582A6;">ISE Admin Portal</mark>. If this is chosen the ISE node needs to restart all services to use the newly applied certificate.
##### EAP Authentication Certificate
ISE will use this certificate for <mark style="background: #FFB86CA6;">EAP protocols that use SSL/TLS tunneling</mark>. <mark style="background: #FFF3A3A6;">This is the certificate the ISE will present to the client to prove itself as trusted server</mark>.
##### RADIUS DTLS Certificate
RADIUS over Datagram Transport Layer Security encrypt the full packet. The certificate can be used to establish and secure the communication between the <mark style="background: #FFB8EBA6;">ISE server and the NAD</mark>.
##### Portal Certificate
Certificates used for ISE <mark style="background: #BBFABBA6;">user portals</mark>. Which can be Guest Portal, Client Provisioning Portal, MDM Portal, BYOD Portal, Sponsor Portal, or My Devices Portal. The Guest Portal usually should have a public certificate as it should be used to external devices. 
##### pxGrid Certificate
This certificate will be used to establish trust and build a <mark style="background: #ABF7F7A6;">secure connection between ISE and third-party pxGrid clients</mark> to share contextual information. 
#### Certificate Signing Request
To create a certificate signed the a external Certificate Authority like Microsoft AD CS, create <strong>a Certificate Signing Request (CSR)</strong> in <strong>Administration > System > Certificates > Certificate Signing Request</strong> 

![[Pasted image 20260427150149.png]]
- <strong>Common Name (CN)</strong> : The CN should be a <mark style="background: #FF5582A6;">FQDN that will resolve via DNS to the IP address of ISE node</mark>.
- <strong>Organization(O)</strong>: The organization the certificate is meant ot represent, the org implementing ISE
- <strong>Organizational Unit(OU)</strong>: This is the division of the organization that is controlling the device for which the certificate is being used
- <strong>Locality(L)</strong>: The city where the entity resides
- <strong>State(ST)</strong>: The state or the province the entity resides in
- <strong>Country(C)</strong>: This is the country that the entity resides in

The ISE GUI also allows the customization of the Subject Alternative Name (SAN) field, which is meant to carry a number of different attributes, each designed to aid in the identification of the certificate:

- <strong>DNS Name</strong>: This is the FQDN of the ISE node. If the certificate will be a wildcard certificate, be sure to specify the wildcard notation <strong>*</strong>, like <strong>*.publiacqua.it</strong>.
- <strong>IP Address</strong>: This is the IP address of the ISE node associated with the certificate
- <strong>Uniform Resource Name</strong>: This is the URI associated with the certificate.
- <strong>Directory Name</strong>: This is a string representation of the distinguished name (DN). DNs are defined in RFC 2253.

A client that is presented with a certificate compare <mark style="background: #ABF7F7A6;">the name of the host</mark> with <mark style="background: #ADCCFFA6;">the CN field of the certificate subject</mark>. If the hostname or FQDN used to reach the host doesn’t match what is in the CN field, a certificate mismatch occurs.

The newly created CSR is saved in the <strong>Certificate Signing Requests</strong> section and it can be exported, it is a <strong>Base64-encoded plaintext file</strong> known as a <strong>PEM</strong> file.
Open the CSR with a text editor, copy its content and paste it on the certificate authority web server similar to the procedure in [[#Enrollment - Windows Manual | this link]] except that the CSR is already present.

Once the <strong>certnew.cer</strong> is downloaded, go back to the <strong>Certificate Signing Requests</strong> section and link to the certificate to the CSR used to make this cert. 

The new cert should show on System Certificates list.
#### Trusted Certificates
Trusted certificates are used for validation. <mark style="background: #FFF3A3A6;">They are the certificates</mark> (usually Root or Intermediate CA certificates) <mark style="background: #FFF3A3A6;">that ISE uses to verify the identity of someone else</mark>. 

In <strong>Administration > System > Certificates > Trusted Certificates</strong> a copy of the <mark style="background: #FF5582A6;">signing certificate authority’s public key must be stored</mark>, and that certificate must be trusted for purpose of authentication.

![[Pasted image 20260427145832.png]]

When a client presents a certificate for EAP authentication protocol, the ISE server will check if the issuer of the client certificate is present on the list of Trusted Certificates. 

![[Pasted image 20260427162757.png | 200]]

![[Pasted image 20260427165456.png]]

If the issuing certificate authority is not present among the Trusted Certificate the authentication fails. 
##### CRL Revocation List
In the Trusted Certificates is also set the CRL validation for the selected certificate. 
The Certificate Revocation List is a list of the revoked certificates, it is used to check for certificates that are not expired but are not usable because they are expired. 

![[Pasted image 20260504121014.png]]

The Retrieve CRL timers should be set accordingly to the CA CRL timers.

![[Pasted image 20260504122151.png | 200]]

- <strong>Effective date</strong> is the date the CRL will start to be valid. 
- <strong>Next update</strong> is the time the CRL will expire.
- <strong>Next CRL Publish</strong> is when the new CRL will be published but is still not active
The Retrieve CRL set to 8 hours before expiration is set 8 hours before the <strong>Next update</strong> so it will retrive the <strong>Next CRL Publish</strong> CRL.
The old CRL and the new CRL have 8 hours overlap in which both CRL are active, so the timer set to Automatically 8 hour before expire with 10 minutes of wait before retry, is correct and leave no black periods. 

The CRL Distribution URL can be retrieved from the Certificate Authority server

![[Pasted image 20260427170031.png]]

When a certificate is revoked outside of the automated cycle, you must trigger a manual CRL publication to synchronize the revocation status across all validating clients:

![[Pasted image 20260427170213.png]]

![[Pasted image 20260427170229.png]]

When doing a manual CRL publication do a manual download of the CRL in ISE server too, by setting the Retrieve CRL download to every 1 minute and then change back. 
#### Certificate Authentication Profile

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
### Client Certificates 
Client Certificates are used by users, machine or both to authenticate to ISE. 
In the server SubordinateCA, on the Certificate Authority service create the Certificate Templates that will be used by Domain Users, Domain Machines, and non Domain Users. 
#### Domain Users Certificate
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

#### Domain Admin Certificate
For the <strong>Domain Admin Certificate</strong> template copy the <strong>Domain User Certificate</strong> template and <mark style="background: #FFF3A3A6;">change Security tab <strong>Group or user names</strong> section</mark>, <mark style="background: #FFB86CA6;">remove Domain Users</mark> and in <mark style="background: #ABF7F7A6;">Domain Admin permissions, allow Read, Write, and Enroll</mark>. The Write permission is used to modify the certificate template. 

As the Domain Admin Certificate is made for admins that have a domain user account but not a domain computer, the enrollment is done manually. 
##### Enrollment - Windows Manual
![[Manual Enrollment of Admin Certificate.mp4]]
##### Enrollment - Windows Script
This is a script that enroll a non domain computer with a domain certificate if the user is an admin with a account in the Active Directory. 

To correctly activate this script, it must be saved with <strong>.ps1</strong> extension in the format <strong>UTF-8 with BOM</strong>.

It's advised to install the 64-base <strong>certnew.p7b</strong> certificate chain, for easiest install, but the <strong>certnew.cer</strong> certificate works too.

```powershell
param(
    [ValidateSet("All", "Step1", "Step2")]
    [string]$Step = "All",
    [string]$CertPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Require elevation — CA chain import writes to LocalMachine stores
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "This script must be run as Administrator (right-click → Run as administrator)."
}

# Verify certreq is available before doing anything else
if (-not (Get-Command certreq.exe -ErrorAction SilentlyContinue)) {
    throw "certreq.exe not found on this system. This script requires the Windows certificate request utility."
}

# Load VB assembly once at script scope (used by Move-UsedFilesToRecycleBin)
Add-Type -AssemblyName Microsoft.VisualBasic

# Paths
$desktop      = [Environment]::GetFolderPath('Desktop')
$downloadsDir = Join-Path $env:USERPROFILE 'Downloads'
$infPath      = Join-Path $env:TEMP "cert_request.inf"
$csrPath      = Join-Path $desktop  "request.csr"
$subcaBase    = "https://subordinateca01.publiacqua.it/certsrv"
$subcaUrl     = "$subcaBase/certrqxt.asp"
$caChainPage  = "$subcaBase/certcarc.asp"
$scriptName   = $MyInvocation.MyCommand.Name
$eventSource  = "EAPEnroll"

# Expected template name (for display only)
$expectedTemplate = "EAP-Admin-User"

$script:Step1StartTime = $null
$IsCertPathExplicit    = $PSBoundParameters.ContainsKey('CertPath')

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

function Write-EnrollmentEvent {
    param(
        [string]$Message,
        [ValidateSet('Information','Warning','Error')]
        [string]$EntryType = 'Information'
    )
    try {
        if (-not [System.Diagnostics.EventLog]::SourceExists($eventSource)) {
            try { New-EventLog -LogName Application -Source $eventSource -ErrorAction Stop } catch { return }
        }
        Write-EventLog -LogName Application -Source $eventSource -EventId 1000 `
            -EntryType $EntryType -Message $Message -ErrorAction Stop
    }
    catch {
        # Best-effort.
    }
}

function Find-NewestCertificate {
    param([datetime]$SinceTime)

    if (-not (Test-Path $downloadsDir)) { return $null }

    $candidates = Get-ChildItem -Path $downloadsDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.cer','.p7b' }

    if ($SinceTime) {
        $candidates = $candidates | Where-Object { $_.LastWriteTime -ge $SinceTime }
    }

    $newest = $candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($newest) { return $newest.FullName }
    return $null
}

function Test-IsCACertificate {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)

    $bcExt = $Certificate.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.19' } | Select-Object -First 1
    if (-not $bcExt) { return $false }
    return ([System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension]$bcExt).CertificateAuthority
}

function Test-DownloadedCertificate {
    <#
    Accepts either a single-cert (.cer) or PKCS#7 chain (.p7b).
    For a chain, finds the leaf (non-CA) certificate and validates it.
    #>
    param([string]$Path)

    $result = [ordered]@{
        Valid       = $false
        Reason      = $null
        Certificate = $null
        CACerts     = @()
    }

    $collection = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2Collection
    try {
        $collection.Import($Path)
    }
    catch {
        $result.Reason = "File could not be parsed as a certificate or PKCS#7 chain: $_"
        return $result
    }

    if ($collection.Count -eq 0) {
        $result.Reason = "File contains no certificates."
        return $result
    }

    $leafCandidates = @()
    $caCerts        = @()
    foreach ($c in $collection) {
        if (Test-IsCACertificate -Certificate $c) { $caCerts += $c }
        else { $leafCandidates += $c }
    }

    if ($leafCandidates.Count -eq 0) {
        $result.Reason = "File contains only CA certificates — no user/leaf certificate found. Did you download the CA chain instead of your issued certificate?"
        return $result
    }
    if ($leafCandidates.Count -gt 1) {
        $result.Reason = "File contains multiple non-CA certificates ($($leafCandidates.Count)). Cannot determine which is yours."
        return $result
    }

    $cert = $leafCandidates[0]
    $result.Certificate = $cert
    $result.CACerts     = $caCerts

    $clientAuthOid = '1.3.6.1.5.5.7.3.2'
    $ekuExts = $cert.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.37' }
    if (-not $ekuExts) {
        $result.Reason = "Certificate has no Enhanced Key Usage extension. Wrong template?"
        return $result
    }

    $ekuOids = foreach ($ext in $ekuExts) {
        ([System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]$ext).EnhancedKeyUsages |
            ForEach-Object { $_.Value }
    }

    if ($clientAuthOid -notin $ekuOids) {
        $result.Reason = "Certificate is missing Client Authentication EKU. Found EKUs: $($ekuOids -join ', ')"
        return $result
    }

    $now = Get-Date
    if ($cert.NotAfter -lt $now) {
        $result.Reason = "Certificate is already expired (NotAfter: $($cert.NotAfter))."
        return $result
    }
    if ($cert.NotBefore -gt $now) {
        $result.Reason = "Certificate is not yet valid (NotBefore: $($cert.NotBefore)) — possible clock skew."
        return $result
    }

    $result.Valid = $true
    return $result
}

function Install-CAChainFromCerts {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2[]]$CACerts)

    if (-not $CACerts -or $CACerts.Count -eq 0) { return $false }

    $rootStore = $null
    $caStore   = $null
    try {
        $rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store('Root','LocalMachine')
        $caStore   = New-Object System.Security.Cryptography.X509Certificates.X509Store('CA','LocalMachine')
        $rootStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
        $caStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)

        foreach ($c in $CACerts) {
            $isSelfSigned = ($c.Subject -eq $c.Issuer)
            if ($isSelfSigned) {
                $rootStore.Add($c)
                Write-Host "  Installed root: $($c.Subject)" -ForegroundColor DarkGreen
            } else {
                $caStore.Add($c)
                Write-Host "  Installed intermediate: $($c.Subject)" -ForegroundColor DarkGreen
            }
        }
        return $true
    }
    catch {
        Write-Warning " CA chain import failed: $_"
        return $false
    }
    finally {
        if ($rootStore) { $rootStore.Close() }
        if ($caStore)   { $caStore.Close() }
    }
}

function Install-CAChainViaBrowser {
    <#
    Asks the user to download the CA certificate chain .p7b through their browser
    (auth is handled by the browser), then finds it in Downloads, validates that
    it contains only CA certs, and installs it.

    Returns the path to the installed .p7b on success, or $null on failure.
    #>

    Write-Host ""
    Write-Host " The downloaded certificate does not include the CA chain." -ForegroundColor Yellow
    Write-Host " The CA chain must be installed before the certificate can be bound to its private key." -ForegroundColor Yellow
    Write-Host ""
    Write-Host " Opening the CA certificate download page:" -ForegroundColor Cyan
    Write-Host "   $caChainPage" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " On that page:" -ForegroundColor Cyan
    Write-Host "   1. Select 'Base 64'" -ForegroundColor Cyan
    Write-Host "   2. Click 'Download CA certificate chain'" -ForegroundColor Cyan
    Write-Host "   3. Save the .p7b file to your Downloads folder" -ForegroundColor Cyan

    $promptTime = Get-Date
    Start-Process $caChainPage

    [void](Read-Host "`n Press ENTER once the .p7b is downloaded")

    Write-Host " Looking for newly downloaded .p7b in $downloadsDir..." -ForegroundColor Cyan
    $p7bPath = $null
    for ($i = 0; $i -lt 10; $i++) {
        $candidate = Get-ChildItem -Path $downloadsDir -Filter '*.p7b' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $promptTime } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($candidate) { $p7bPath = $candidate.FullName; break }
        Start-Sleep -Milliseconds 500
    }

    if (-not $p7bPath) {
        Write-Error " No .p7b file found in $downloadsDir newer than $($promptTime.ToString('HH:mm:ss'))."
        return $null
    }
    Write-Host " Found chain file: $p7bPath" -ForegroundColor Cyan

    try {
        $coll = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2Collection
        $coll.Import($p7bPath)
    }
    catch {
        Write-Error " Could not parse $p7bPath as PKCS#7: $_"
        return $null
    }

    if ($coll.Count -eq 0) {
        Write-Error " The downloaded file contains no certificates."
        return $null
    }

    # Refuse anything that isn't a CA cert — we're installing into trusted stores
    $caOnly = @($coll | Where-Object { Test-IsCACertificate -Certificate $_ })
    if ($caOnly.Count -ne $coll.Count) {
        Write-Error " The downloaded chain file contains non-CA certificates. Aborting for safety — you may have downloaded the wrong file."
        return $null
    }

    Write-Host " Installing $($caOnly.Count) CA cert(s) from the chain..." -ForegroundColor Cyan
    if (-not (Install-CAChainFromCerts -CACerts $caOnly)) {
        return $null
    }

    return $p7bPath
}

function Move-UsedFilesToRecycleBin {
    param(
        [string]$ResolvedCertPath,
        [string]$CAChainPath
    )

    $filesToMove = @($infPath, $csrPath, $ResolvedCertPath, $CAChainPath)
    foreach ($file in $filesToMove) {
        if ($file -and (Test-Path $file)) {
            try {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                    $file,
                    [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                    [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin
                )
            }
            catch {
                Write-Warning "Could not move '$file' to Recycle Bin: $_"
            }
        }
    }
}

function Invoke-Step1 {
    if (Test-Path $csrPath) { Remove-Item $csrPath -Force }
    if (Test-Path $infPath) { Remove-Item $infPath -Force }

    $script:Step1StartTime = Get-Date

    Set-Content -Path $infPath -Value $infContent -Encoding ASCII

    certreq -new $infPath $csrPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $csrPath)) {
        Write-Error "certreq -new failed (exit code $LASTEXITCODE). CSR was not generated."
        return $false
    }

    $csrText = Get-Content $csrPath -Raw

    $clipboardOk = $false
    try {
        $csrText | Set-Clipboard
        $clipboardOk = $true
    }
    catch {
        Write-Warning "Clipboard unavailable: $_"
    }

    if ($clipboardOk) {
        Write-Host "`n CSR saved and copied to clipboard (your previous clipboard contents have been replaced)." -ForegroundColor Green
    }
    else {
        Write-Host "`n CSR saved to: $csrPath" -ForegroundColor Yellow
        Write-Host " Clipboard was unavailable — open the file and copy its contents manually." -ForegroundColor Yellow
    }

    Write-Host "`n Use Publiacqua domain credentials." -ForegroundColor Green
    Write-Host "`n Paste the CSR to $subcaUrl" -ForegroundColor Green
    Write-Host "`n Certificate Template must be $expectedTemplate." -ForegroundColor Green
    Write-Host "`n Download the Base64 certificate (.cer) OR full chain (.p7b) to the Downloads folder." -ForegroundColor Green

    Start-Process $subcaUrl
    return $true
}

function Invoke-Step2 {
    $resolvedPath = $null

    if ($IsCertPathExplicit) {
        $resolvedPath = $CertPath
    }
    else {
        Write-Host "`n Looking for newly downloaded .cer or .p7b in $downloadsDir..." -ForegroundColor Cyan
        for ($i = 0; $i -lt 10; $i++) {
            $resolvedPath = Find-NewestCertificate -SinceTime $script:Step1StartTime
            if ($resolvedPath) { break }
            Start-Sleep -Milliseconds 500
        }

        if (-not $resolvedPath) {
            Write-Error "`n No .cer or .p7b file found in $downloadsDir$(if ($script:Step1StartTime) { " newer than $($script:Step1StartTime.ToString('HH:mm:ss'))" })."
            Write-Host " If needed, specify it explicitly:" -ForegroundColor Yellow
            Write-Host "   .\$scriptName -Step Step2 -CertPath 'C:\path\certnew.cer'" -ForegroundColor Yellow
            return $false
        }
        Write-Host " Auto-detected: $resolvedPath" -ForegroundColor Cyan
    }

    if (-not (Test-Path $resolvedPath)) {
        Write-Error "`n Certificate file not found: $resolvedPath"
        return $false
    }

    $validation = Test-DownloadedCertificate -Path $resolvedPath
    if (-not $validation.Valid) {
        Write-Error "`n Certificate validation failed: $($validation.Reason)"
        Write-Host "   File: $resolvedPath" -ForegroundColor Yellow
        Write-Host "   Re-download from $subcaUrl using template '$expectedTemplate'." -ForegroundColor Yellow
        return $false
    }

    Write-Host " Certificate validated (Subject: $($validation.Certificate.Subject), Issuer: $($validation.Certificate.Issuer))." -ForegroundColor Green
    if ($validation.CACerts.Count -gt 0) {
        Write-Host " Found $($validation.CACerts.Count) CA cert(s) bundled in the file." -ForegroundColor Green
    }

    # Install CA chain — either from the downloaded .p7b, or by asking the user to download one
    $chainP7bPath = $null
    if ($validation.CACerts.Count -gt 0) {
        Write-Host "`n Installing CA chain from the downloaded file..." -ForegroundColor Cyan
        if (-not (Install-CAChainFromCerts -CACerts $validation.CACerts)) {
            Write-Error " CA chain installation failed."
            return $false
        }
        Write-Host " CA chain installed." -ForegroundColor Green
    } else {
        $chainP7bPath = Install-CAChainViaBrowser
        if (-not $chainP7bPath) {
            Write-Error " CA chain not installed. certreq -accept would fail with UNTRUSTEDROOT."
            return $false
        }
        Write-Host " CA chain installed." -ForegroundColor Green
    }

    # certreq -accept handles both .cer and .p7b; binds the issued cert to the private key in the CSP
    certreq -accept $resolvedPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "`n certreq -accept failed (exit code $LASTEXITCODE). The issued certificate could not be bound to its private key."
        return $false
    }

    $imported = Get-ChildItem Cert:\CurrentUser\My |
        Where-Object {
            $_.Thumbprint -eq $validation.Certificate.Thumbprint -and $_.HasPrivateKey
        } |
        Select-Object -First 1

    if (-not $imported) {
        Write-Warning "Certificate accepted, but no matching cert with a private key was found in CurrentUser\My. EAP authentication may fail."
    }
    else {
        Write-Host "`n Certificate installed to CurrentUser\Personal store (thumbprint $($imported.Thumbprint))." -ForegroundColor Green
        Write-EnrollmentEvent -Message "EAP cert enrolled for $env:USERNAME on $env:COMPUTERNAME, thumbprint $($imported.Thumbprint), source file $resolvedPath"
    }

    Move-UsedFilesToRecycleBin -ResolvedCertPath $resolvedPath -CAChainPath $chainP7bPath
    Write-Host "`n Used files sent to user Recycle Bin." -ForegroundColor Green
    return $true
}

switch ($Step) {
    'Step1' {
        if (-not (Invoke-Step1)) { exit 1 }
    }
    'Step2' {
        if (-not (Invoke-Step2)) { exit 1 }
    }
    'All' {
        if (-not (Invoke-Step1)) { exit 1 }

        $userInput = Read-Host "`n Once the certificate is downloaded, press ENTER to continue or Q to quit"
        if ($userInput -match '^[Qq]$') {
            Write-Host "`n Stopped after Step 1. You can later run: .\$scriptName -Step Step2" -ForegroundColor Yellow
            exit 0
        }

        if (-not (Invoke-Step2)) { exit 1 }
    }
}
```

##### Enrollment - Apple Script

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

#### Domain Computer Certificate
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

#### Script To Remove Expired userCertificate
The expired certificates in the userCertificate attribute cannot be removed automatically, we should remove them manually or with the help of a script. 
By default this script is in read only mode, read the description for the how to use.

[[Script To Remove Expired userCertificate]]
## Group Policy Management
The Group Policy Management service is used to deploy the configuration of Windows native supplicant and the rollout of the Client Certificates and other setting to manage the user and computer configuration. 

Make sure the GPO with the desired configuration is winning against other GPOs and its policies are enforced, and the <strong>Security Filtering</strong> is applied correctly. This is possible to check on <strong>Group Policy Results Wizard</strong> on <strong>Group Policy Management</strong>.
### Computer GPO
This GPO will be used to <mark style="background: #FFF3A3A6;">enroll Domain Computers</mark> with the [[#Domain Computer Certificate]] and enable <mark style="background: #FFB86CA6;">Wired AutoConfig</mark> on computers. 

All computer GPO must be create in the <strong>Group Policy Management → Forest: publiacqua.it → Domains → publiacqua.it → ComputerXp</strong> which is where the Domain Computer accounts are stored.
<mark style="background: #FFB8EBA6;"><u>At each change of computer GPO, there must be a <strong>gpupdate /force</strong> CMD command and a reboot of the client computer to apply the GPO configuration</u></mark>.

<strong>Wired AutoConfig</strong> (<strong>DOT3SVC</strong>) is a Windows service that manages <mark style="background: #FF5582A6;">IEEE 802.1X authentication on Ethernet connections</mark>. It enables computers to authenticate themselves on secure networks, often used in corporate environments to enforce network access control. 
<strong>Computer Configuration → Policies → Windows Settings → Security Settings → System Services → Wired AutoConfig</strong>

![[Pasted Graphic 2.png]]

The [[#Domain Computer Certificate]] has Auto-Enrollment configured on its certificate template, so to enroll the computers we just need to enable the Auto-Enrollment.

To activate Auto-Enrollment go to <strong>Computer Configuration → Policies → Windows Settings → Security Settings → Public Key Policies → Certificate Services Client - Auto-Enrollment</strong> 

![[Pasted Graphic.png]]

<mark style="background: #ABF7F7A6;">Core 802.1X configuration is the <strong>Wired Network (IEEE 802.3) Policies</strong></mark> in <strong>Computer Configuration → Policies → Windows Settings → Security Settings → Wired Network (IEEE 802.3) Policies</strong>, in the current deployment there are <strong>PEAP</strong>, <strong>TEAP</strong> and <strong>EAP-TLS</strong>.

GPO hierarchy: <strong>EAP-TLS → PEAP-MSCHAPv2 → TEAP</strong>
- <strong>TEAP</strong> GPO — scoped to <strong>Domain Computers</strong>. This makes TEAP the default authentication method for the entire fleet.
- <strong>PEAP MSCHAPv2</strong> GPO — scoped to a custom security group (e.g., <strong>GPO_C_PC_Enable_PEAP</strong>) for machines that require PEAP.
- <strong>EAP-TLS</strong> GPO — scoped to a custom security group (e.g., <strong>GPO_C_PC_Enable_EAP-TLS</strong>) for machines that require EAP-TLS.

Because the EAP-TLS and PEAP GPOs are linked at higher precedence than TEAP, <mark style="background: #FFB86CA6;">any computer added to one of the custom groups will have that GPO's wired profile applied last and override the default TEAP profile</mark>. <mark style="background: #BBFABBA6;">To switch a machine's authentication method, just add its computer object to the appropriate group</mark> — no per-machine configuration needed.

The default is TEAP and when some computers need EAP-TLS or PEAP they just need to be dropped in to the custom groups, they will automatically pick the correct authentication method at new reboot. 
#### PEAP MSCHAPv2
PEAP is used for Domain Users that cannot or do not want to use the certification to authenticate to ISE.

- <strong>General tab</strong>: enable <strong>Use Windows Wired Auto Config service for clients</strong>
- <strong>Security tab</strong>:
    - Enable <strong>Use IEEE 802.1X authentication for network access</strong>
	- Network authentication method: <strong>Microsoft: Protected EAP (PEAP)</strong>, go to <strong>Properties...</strong>
		- Tick <strong>Verify server's identity by validating certificate</strong>
		- <strong>Connect to these servers</strong>: Cisco ISE server FQDN
		- In Trusted Root Certification Authorities select the Root CA that signed the ISE [[#EAP Authentication Certificate]], <strong>Don't ask user to authorize new servers or trusted CAs</strong>.
		- Authentication Method: <strong>Secured password (EAP-MSCHAP v2)</strong>
		- Tick <strong>Enable Fast Reconnect</strong>
	- Authentication Mode: <strong>User authentication</strong>
	- Max authentication failures: 1–3
	- Tick <strong>Cache user information for subsequent connections</strong>, to decide if to tick or not. 

Under <strong>Scope → Security Filtering</strong> of the GPO add the Group for which this GPO will be applied. In <strong>Delegation → Advanced</strong> ensure this Group has <strong>Apply group policy</strong> and <strong>Read</strong> in <strong>Allow</strong>.
#### EAP-TLS
This is a GPO with authentication protocol set in EAP-TLS, made specifically for RDP connection, see the policy rule made for this. 

- **General tab**: enable <strong>Use Windows Wired Auto Config service for clients</strong>
- **Security tab**:
    - Enable <strong>Use IEEE 802.1X authentication for network access</strong>
	- Network authentication method: <strong>Microsoft: Smart Card or other certificate</strong>
		- Tick <strong>Use a certificate on this computer</strong>
		- Tick <strong>Use simple certificate selection</strong> 
		- Tick <strong>Verify server's identity by validating certificate</strong> 
		- Tick <strong>Connect to these servers</strong>: Cisco ISE servers FQDN 
		- In <strong>Trusted Root Certificate Authorities</strong> select the Root CA (only the Root CA) that signed the ISE [[#EAP Authentication Certificate]] 
		- Tick <strong>don't prompt user to authorize new servers or trusted certification authorities</strong>.
	- Authentication Mode: <strong>Computer only</strong>
	- Max authentication failures: 1–3

Under <strong>Scope → Security Filtering</strong> of the GPO add the Group for which this GPO will be applied. In <strong>Delegation → Advanced</strong> ensure this Group has <strong>Apply group policy</strong> and <strong>Read</strong> in <strong>Allow</strong>.
#### TEAP
TEAP authentication protocol is the default protocol used by Domain Users and Domain Computers. 

On Group Policy Management editor, the TEAP authentication method is broken, to rollout this type of authentication method we need to import a XML configuration from a working Win10/11 client. 
##### TEAP profile 
First we need to create a TEAP profile to export as XML. 

On a domain-joined client that has both the machine and user certs already enrolled, configure the wired NIC manually so you can export it.

Open the NIC <strong>properties</strong> → <strong>Authentication</strong> tab:
1. Tick <strong>Enable IEEE 802.1X authentication</strong>.
2. Network authentication method → <strong>Microsoft: Tunnel EAP (TEAP)</strong>.
3. Click <strong>Settings</strong>:
    - <strong>Identity privacy</strong> → anonymous.
	    - <strong>Connect to these servers</strong>: Cisco ISE servers FQDN.
	    - <strong>Trusted Root Certification Authorities</strong> → tick the root that signed the ISE [[#EAP Authentication Certificate]]. (If you have a 2-tier PKI, <mark style="background: #FF5582A6;">only tick the <strong>offline root</strong></mark>, not the issuing CA)
	    - Tick <strong>Don't prompt user if unable to authorize server</strong>
    - <strong>Client authentication</strong>:
        - <strong>Primary EAP method </strong>→ <mark style="background: #FFF3A3A6;">Microsoft: Smart Card or other certificate (EAP-TLS)</mark> → this is the computer authentication.
	        -  Tick <strong>Use a certificate on this computer</strong>
			- Tick <strong>Use simple certificate selection</strong> 
			- Tick <strong>Verify server's identity by validating certificate</strong> 
			- Tick <strong>Connect to these servers</strong>: Cisco ISE servers FQDN 
			- In <strong>Trusted Root Certificate Authorities</strong> select the Root CA (only the Root CA) that signed the ISE [[#EAP Authentication Certificate]] 
			- Tick <strong>don't prompt user to authorize new servers or trusted certification authorities</strong>.
        - <strong>Secondary EAP method</strong> → <mark style="background: #FFF3A3A6;">Microsoft: Smart Card or other certificate (EAP-TLS)</mark> → this becomes the user auth.
	        - Tick <strong>Use a certificate on this computer</strong>
			- Tick <strong>Use simple certificate selection</strong> 
			- Tick <strong>Verify server's identity by validating certificate</strong> 
			- Tick <strong>Connect to these servers</strong>: Cisco ISE servers FQDN 
			- In <strong>Trusted Root Certificate Authorities</strong> select the Root CA (only the Root CA) that signed the ISE [[#EAP Authentication Certificate]] 
			- Tick <strong>don't prompt user to authorize new servers or trusted certification authorities</strong>.
4. Back on the <strong>Authentication</strong> tab → <strong>Additional settings</strong> 
	- Tick <strong>Specify authentication mode</strong> → <strong>User or computer authentication</strong>.
	- Tick <strong>Enable Single Sign On for this network</strong> 
		- Tick <strong>Perform immediately before user logon</strong>
		- Tick <strong>This network uses different VLAN for authentication with machine and user credentials</strong> 
The <strong>Fallback to unauthorized network access</strong> must remain <strong>ticked</strong>, as without this option enabled if the user connect to a switch with no authenticator it will not get network access.
##### Export the profile to XML
From an elevated cmd on the same client:
```powershell
netsh lan show profiles
netsh lan export profile folder=C:\Temp interface="Ethernet"
```
The interface="" depends on the show lan profiles.

Note that the <strong>netsh</strong> can have a bug where the TrustedRootCAHash block have malformed hash like `fc 5 c2 6 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e
where bytes `0x05` and `0x06` came out as single hex digits. Change it like `fc 05 c2 06 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e`.

When there are more than one FQDN in the ServerNames block, separate the FQDNs with a semicolon <strong>;</strong> with no trailing spaces.

Open the resulting XML and copy everything inside the OneX block. 
```xml
<OneX xmlns="http://www.microsoft.com/networking/OneX/v1">
				<cacheUserData>false</cacheUserData>
				<heldPeriod>20</heldPeriod>
				<authPeriod>18</authPeriod>
				<startPeriod>3</startPeriod>
				<maxStart>2</maxStart>
				<maxAuthFailures>1</maxAuthFailures>
				<authMode>machineOrUser</authMode>
				<singleSignOn>
					<type>preLogon</type>
					<maxDelay>10</maxDelay>
					<allowAdditionalDialogs>false</allowAdditionalDialogs>
					<userBasedVirtualLan>true</userBasedVirtualLan>
				</singleSignOn>
				<EAPConfig><EapHostConfig xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><EapMethod><Type xmlns="http://www.microsoft.com/provisioning/EapCommon">55</Type><VendorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorId><VendorType xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorType><AuthorId xmlns="http://www.microsoft.com/provisioning/EapCommon">311</AuthorId></EapMethod><Config xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><EapTeap xmlns="http://www.microsoft.com/provisioning/EapTeapConnectionPropertiesV1"><ServerValidation><ServerNames>cisco-ise1.publiacqua.it;pba-ise02.publiacqua.it</ServerNames><TrustedRootCAHash>fc 05 c2 06 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e</TrustedRootCAHash><DisablePrompt>true</DisablePrompt><DownloadTrustedServerRoot>false</DownloadTrustedServerRoot></ServerValidation><Phase2Authentication><InnerMethodConfig><EapHostConfig xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><EapMethod><Type xmlns="http://www.microsoft.com/provisioning/EapCommon">13</Type><VendorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorId><VendorType xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorType><AuthorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</AuthorId></EapMethod><Config xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><Eap xmlns="http://www.microsoft.com/provisioning/BaseEapConnectionPropertiesV1"><Type>13</Type><EapType xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV1"><CredentialsSource><CertificateStore><SimpleCertSelection>true</SimpleCertSelection></CertificateStore></CredentialsSource><ServerValidation><DisableUserPromptForServerValidation>true</DisableUserPromptForServerValidation><ServerNames>cisco-ise1.publiacqua.it;pba-ise02.publiacqua.it</ServerNames><TrustedRootCA>fc 05 c2 06 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e</TrustedRootCA></ServerValidation><DifferentUsername>false</DifferentUsername><PerformServerValidation xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">true</PerformServerValidation><AcceptServerName xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">true</AcceptServerName></EapType></Eap></Config></EapHostConfig></InnerMethodConfig><InnerMethodConfig><EapHostConfig xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><EapMethod><Type xmlns="http://www.microsoft.com/provisioning/EapCommon">13</Type><VendorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorId><VendorType xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorType><AuthorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</AuthorId></EapMethod><Config xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><Eap xmlns="http://www.microsoft.com/provisioning/BaseEapConnectionPropertiesV1"><Type>13</Type><EapType xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV1"><CredentialsSource><CertificateStore><SimpleCertSelection>true</SimpleCertSelection></CertificateStore></CredentialsSource><ServerValidation><DisableUserPromptForServerValidation>true</DisableUserPromptForServerValidation><ServerNames>cisco-ise1.publiacqua.it;pba-ise02.publiacqua.it</ServerNames><TrustedRootCA>fc 05 c2 06 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e</TrustedRootCA></ServerValidation><DifferentUsername>false</DifferentUsername><PerformServerValidation xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">true</PerformServerValidation><AcceptServerName xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">true</AcceptServerName></EapType></Eap></Config></EapHostConfig></InnerMethodConfig></Phase2Authentication><Phase1Identity><IdentityPrivacy>true</IdentityPrivacy><AnonymousIdentity>anonymous</AnonymousIdentity></Phase1Identity></EapTeap></Config></EapHostConfig></EAPConfig>
			</OneX>
```
##### Create the GPO
On the DC open Group Policy Management and create a new GPO linked to the OU that contains your domain computers. Edit it. 
<strong>Computer Configuration → Policies → Windows Settings → Security Settings → Wired Network (IEEE 802.3) Policies → right-click → Create A New Wired Network Policy for Windows Vista and Later Releases</strong>.

1. Make a dummy authentication profile that will be rewritten by the XML config file. 
	- <strong>General tab</strong>: Choose a <strong>Policy Name</strong>, enable <strong>Use Windows Wired Auto Config service for clients</strong>
	- **Security tab**:
	    - Enable <strong>Use IEEE 802.1X authentication for network access</strong>
		- Network authentication method: Pick <strong>Microsoft: Protected EAP (PEAP)</strong> for placeholder, it will be overwritten. 
	- **Security → Advanced**:
	    - Tick <strong>Enforce advanced 802.1X settings</strong>
		    - <strong>Max Eapol-Start Msgs</strong>: 2
		    - <strong>Held Period</strong>: 20
		    - <strong>Start Period</strong>: 3
		    - <strong>Auth Period</strong>: 10
	    - Tick <strong>Enable Single Sign On for this network</strong> → <strong>Perform immediately before user logon</strong>.
	    - Tick <strong>This network uses different VLAN for authentication with machine and user credentials</strong>.
2. Save the policy, go to <strong>Group Policy Management → Forest: publiacqua.it → Domains → publiacqua.it → Group Policy Objects</strong>, find the saved policy.
3. Back Up... → Choose the Location (C:\Users\Username\Desktop).
4. Open the folder and open <strong>Backup.xml</strong> file with a text editor.
5. Find the block <strong>OneX xmlns="http://www.microsoft.com/networking/OneX/v1"</strong> 
6. Replace the whole block with the customized one, save and close. 
7. Return to <strong>Group Policy Objects</strong>, click <strong>Restore from Backup...</strong> 
8. Select Backup folder, if the the GUID folder was inside <strong>C:\Users\username\Desktop</strong> just select <strong>C:\Users\username\Desktop</strong> and not the GUID folder.
9. And finish the restore of the backup.
10. Check that it works.

Under <strong>Scope → Security Filtering</strong> of the GPO add <strong>Domain Computers</strong> which is the group this GPO will be applied to. In <strong>Delegation → Advanced</strong> ensure this Group has <strong>Apply group policy</strong> and <strong>Read</strong> in <strong>Allow</strong>.
### User GPO
This GPO will be used to <mark style="background: #FFF3A3A6;">enroll Domain Users</mark> with the [[#Domain Users Certificate]].

All computer GPO must be create in the <strong>Group Policy Management → Forest: publiacqua.it → Domains → publiacqua.it → Publiacqua</strong> which is where the Domain User accounts are stored.
<mark style="background: #CACFD9A6;">At each change of computer GPO, there must be a <strong>gpupdate /force</strong> CMD command to apply the GPO configuration</mark>.

To activate Auto-Enrollment go to <strong>User Configuration → Policies → Windows Settings → Security Settings → Public Key Policies → Certificate Services Client - Auto-Enrollment</strong> 

![[Pasted Graphic 3.png]]

The GPO should be in <strong>Enforced</strong> mode to ensure that it will be applied.
# Network Devices

# Packet Flow with Cisco ISE
Certificate authentication: 
CLIENT send certificate, ISE CHECK if issuer is in trusted, the expiry date, CRL, proof of possession (server privat key + client public key (the certificate sent for authentication) + random data) the client need to decrypt the data with client private key and server public key. 


# Reference 


| Voce                  | Topic        | Link                                                                                                      |
| --------------------- | ------------ | --------------------------------------------------------------------------------------------------------- |
| Certificate Templates | Certificates | https://sendthepayload.com/configuring-certificate-templates-with-active-directory-certificate-services/# |
| Windows Certificates  | Certificates | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/certreq_1                |
|                       |              |                                                                                                           |
