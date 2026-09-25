---
categories:
  - "[[Networking]]"
  - "[[Security]]"
  - "[[Microsoft]]"
topic@networking:
  - "[[2 - Categories/Topics/Networking/Cisco ISE|Cisco ISE]]"
topic@security:
  - "[[NAC]]"
topic@microsoft:
  - "[[Windows Server]]"
tags:
  - project
  - nac
  - cisco
  - scor/sise
  - ccnp
  - tech_doc
  - PBA
  - category/networking/cisco_ise
  - category/security/nac
  - category/microsoft/windows_server
icon: SiWindows
iconColor: "#0078D4"
last_update: 2026-09-25
---


In most cases the external services used are Microsoft Servers: [[#Active Directory]] as the identity store, the [[#Certificate Authority]] providing the certificates that users and/or hosts present for authentication, and [[#Group Policy Management]] rolling out the configuration to clients.

## Active Directory

![[Pasted image 20260421124607.png]]

Cisco ISE can join Microsoft Active Directory as an External Identity Source under the item Active Directory.

The AD is used to identify the users when they do an authentication. They can be checked with their domain password or with the domain certificates they provide ISE.

For the ISE server to be able to join the domain, it has to have a machine account in the domain and a DNS entry, while the AD user account used for the join must have the permissions to join ISE to AD.

![[Pasted image 20260421152119.png]]

In this section it is also possible to retrieve groups from the AD to create policies around the user group identity.

![[Pasted image 20260421125524.png]]

## Certificate Authority

The Certificate Authority service is used to provide certificates to both ISE server itself and clients that will use it to do network access authentication.

### Server Certificates

The ISE server has two types of certificates: [[#System Certificates|system certificates]] that are used to identify itself, and [[#Trusted Certificates|trusted certificates]] that are used to validate clients.

#### System Certificates

There are many portals hosted in ISE. All the ISE portals require encryption by default. In other words, all portals in ISE use HTTPS, and a certificate on ISE is used to secure the communication. Certificates are also used to secure EAP communications, to form a Transport Layer Security (TLS) tunnel between an endpoint and a RADIUS server, or to identify the RADIUS server (ISE) to the client (supplicant).

![[Pasted image 20260421153234.png]]

##### Admin Certificate

For the <mark style="background: #FF5582A6;">ISE Admin Portal</mark>. If this is chosen the ISE node needs to restart all services to use the newly applied certificate.

##### EAP Authentication Certificate

ISE will use this certificate for <mark style="background: #FFB86CA6;">[[PBA - NAC - ISE Server#Extensible Authentication Protocols|EAP protocols that use SSL/TLS tunneling]]</mark>. <mark style="background: #FFF3A3A6;">This is the certificate the ISE will present to the client to prove itself as a trusted server</mark>.

##### RADIUS DTLS Certificate

RADIUS over Datagram Transport Layer Security encrypts the full RADIUS packet. The certificate can be used to establish and secure the communication between the <mark style="background: #FFB8EBA6;">ISE server and the NAD</mark>.

##### Portal Certificate

Certificates used for ISE <mark style="background: #BBFABBA6;">user portals</mark>, which can be the Guest Portal, Client Provisioning Portal, MDM Portal, BYOD Portal, Sponsor Portal, or My Devices Portal. The Guest Portal usually should have a public certificate as it will be used by external devices.

##### pxGrid Certificate

This certificate will be used to establish trust and build a <mark style="background: #ABF7F7A6;">secure connection between ISE and third-party pxGrid clients</mark> to share contextual information.

##### Certificate Signing Request

To create a certificate signed by an external Certificate Authority like Microsoft [[Active Directory Certificate Services|AD CS]], create <strong>a Certificate Signing Request (CSR)</strong> in <strong>Administration > System > Certificates > Certificate Signing Request</strong>.

![[Pasted image 20260427150149.png]]

- <strong>Common Name (CN)</strong> : The CN should be a <mark style="background: #FF5582A6;">FQDN that will resolve via DNS to the IP address of the ISE node</mark>.
- <strong>Organization (O)</strong>: The organization the certificate is meant to represent — the org implementing ISE
- <strong>Organizational Unit (OU)</strong>: This is the division of the organization that is controlling the device for which the certificate is being used
- <strong>Locality (L)</strong>: The city where the entity resides
- <strong>State (ST)</strong>: The state or the province the entity resides in
- <strong>Country (C)</strong>: This is the country that the entity resides in

The ISE GUI also allows the customization of the Subject Alternative Name (SAN) field, which is meant to carry a number of different attributes, each designed to aid in the identification of the certificate:

- <strong>DNS Name</strong>: This is the FQDN of the ISE node. If the certificate will be a wildcard certificate, be sure to specify the wildcard notation <strong>*</strong>, like <strong>*.publiacqua.it</strong>.
- <strong>IP Address</strong>: This is the IP address of the ISE node associated with the certificate
- <strong>Uniform Resource Name</strong>: This is the URI associated with the certificate.
- <strong>Directory Name</strong>: This is a string representation of the distinguished name (DN). DNs are defined in RFC 2253.

A client that is presented with a certificate compares <mark style="background: #ABF7F7A6;">the name of the host</mark> with <mark style="background: #ADCCFFA6;">the CN field of the certificate subject</mark>. If the hostname or FQDN used to reach the host doesn’t match what is in the CN field, a certificate mismatch occurs. Modern clients check the SAN DNS entries first — many ignore the CN entirely — so the FQDN should always be present in the SAN as well.

The newly created CSR is saved in the <strong>Certificate Signing Requests</strong> section and it can be exported, it is a <strong>Base64-encoded plaintext file</strong> known as a <strong>PEM</strong> file. Open the CSR with a text editor, copy its content and paste it into the certificate authority web enrollment page, following a procedure similar to [[#Enrollment - Windows Manual|the manual enrollment]] except that the CSR is already present.

Once the <strong>certnew.cer</strong> is downloaded, go back to the <strong>Certificate Signing Requests</strong> section and bind the certificate to the CSR that generated it (the <strong>Bind Certificate</strong> action).

The new cert should appear in the System Certificates list.

#### Trusted Certificates

Trusted certificates are used for validation. <mark style="background: #FFF3A3A6;">They are the certificates</mark> (usually Root or Intermediate CA certificates) <mark style="background: #FFF3A3A6;">that ISE uses to verify the identity of someone else</mark>.

In <strong>Administration > System > Certificates > Trusted Certificates</strong> a copy of the <mark style="background: #FF5582A6;">signing certificate authority’s public key must be stored</mark>, and that certificate must be trusted for purpose of authentication.

![[Pasted image 20260427145832.png]]

When a client presents a certificate for an EAP authentication protocol, the ISE server will check if the issuer of the client certificate is present on the list of Trusted Certificates.

![[Pasted image 20260427162757.png | 200]]

![[Pasted image 20260427165456.png]]

If the issuing certificate authority is not present among the <strong>Trusted Certificates</strong>, the authentication fails.

##### CRL Revocation List

The Trusted Certificates section is also where CRL validation is set for the selected certificate. The Certificate Revocation List is a list of the revoked certificates; it is used to check for certificates that have not yet reached their expiration date but have been <strong>revoked</strong> before expiration.

![[Pasted image 20260504121014.png]]

The Retrieve CRL timers should be set according to the CA CRL timers.

![[Pasted image 20260504122151.png | 200]]

- <strong>Effective date</strong> is the date the CRL will start to be valid.
- <strong>Next update</strong> is the time the CRL will expire.
- <strong>Next CRL Publish</strong> is when the new CRL will be published, while the old one is still active. The Retrieve CRL timer set to 8 hours before expiration falls 8 hours before the <strong>Next update</strong>, so it will retrieve the <strong>Next CRL Publish</strong> CRL. The old CRL and the new CRL have an 8 hour overlap in which both CRLs are active, so the timer set to Automatically 8 hours before expiration, with 10 minutes of wait before retry, is correct and leaves no blackout periods.

The CRL Distribution URL can be retrieved from the Certificate Authority server.

![[Pasted image 20260427170031.png]]

When a certificate is revoked outside of the automated cycle, you must trigger a manual CRL publication to synchronize the revocation status across all validating clients:

![[Pasted image 20260427170213.png]]

![[Pasted image 20260427170229.png]]

When doing a manual CRL publication do a manual download of the CRL in ISE server too, by setting the Retrieve CRL download to every 1 minute and then changing it back.

#### Certificate Authentication Profile

![[Pasted image 20260424144802.png]]

The <strong>Certificate Authentication Profile</strong> (CAP) section is used to decide which <mark style="background: #FF5582A6;">attribute of the certificate</mark> the ISE server will use to check the identity of the client.

Here it is set to Subject Alternative Name (SAN) as the CAP will be used for both Machine and User EAP authentication protocols. The Users in the SAN will use the UPN while the Machines will use the DNS Name. See the ISE-side counterpart in [[PBA - NAC - ISE Server#External Identity Sources - Certificate Authentication Profile|the ISE note]], where the CAP sits in the certificate-validation flow.

|User Certificate|Machine Certificate|
|---|---|
|![[Pasted image 20260424145144.png]]|![[Pasted image 20260424145227.png]]|

The selection <strong>Match Client Certificate Against Certificate In Identity Store</strong>:

- <strong>Only to resolve identity ambiguity</strong>: This is the standard setting. It tells ISE to use the certificate information to identify the user in AD, but it doesn't require a byte-for-byte match of the certificate itself against an AD attribute.
- <strong>Always perform binary comparison</strong>: <mark style="background: #FF5582A6;">Use this only if you have physically uploaded or published the user/machine certificates into the <strong>userCertificate</strong> attribute in Active Directory</mark>. <mark style="background: #FFB86CA6;">ISE will then perform a byte-for-byte comparison between the certificate the client presents and the one stored in AD</mark>. If they don't match exactly, authentication will fail. See [[#Domain Users Certificate|the domain user certificate configuration]] for populating the userCertificate attribute, and [[#Script To Remove Expired userCertificate|the removal script]] for clearing expired entries from it.
- <strong>Never:</strong> Choose this if you are not using an identity store at all for this profile. This would be common for Guest or BYOD setups where you just want to verify that the certificate is valid and signed by a trusted CA without checking it against an AD account.

### Client Certificates

Client Certificates are used by users, machines, or both to authenticate to ISE; the identity is read from the certificate field configured in the [[#Certificate Authentication Profile]]. On the server SubordinateCA, in the Certificate Authority service, create the Certificate Templates that will be used by Domain Users, Domain Machines, and non-Domain Users. When a client can present only the machine certificate and not the user one, ISE grants the limited [[PBA - NAC - ISE Server#Machine Access|Machine Access]] authorization.

#### Domain Users Certificate

For Users Certificates, duplicate from the default <strong>User</strong> certificate template:

- On the <u>General tab</u> create a logical template name. The <strong>Publish certificate in Active Directory</strong> is used to publish the certificate into the user <strong>userCertificate</strong> attribute in Active Directory. ![[Pasted image 20260424150748.png|200]]
- On the <u>Request Handling tab</u>, uncheck the <strong>Allow private key to be exported</strong> box.
- On the <u>Extensions tab</u>, highlight the <strong>Application Policies</strong> and click <strong>Edit</strong> to verify that <strong>Client Authentication</strong> (OID 1.3.6.1.5.5.7.3.2) is listed — the duplicated <strong>User</strong> template already includes it. This is the EKU a supplicant certificate presents for EAP-TLS, the same one the [[#Enrollment - Windows Script|enrollment script]] INF requests. Do not add <strong>Server Authentication</strong>: that EKU belongs on the ISE [[#EAP Authentication Certificate|EAP Authentication Certificate]], not on client certificates.
- On the <u>Security tab</u>, highlight <strong>Domain Users</strong> and check the <strong>Allow</strong> boxes for <strong>Read</strong>, <strong>Enroll</strong>, and <strong>Autoenroll</strong> under the Permissions pane. <mark style="background: #FF5582A6;">This will be important when configuring our Group Policy to <strong>auto-enroll</strong> users with a user certificate</mark> for EAP authentication when they log into their computers.
- On the <u>Subject Name tab</u>. If this is a lab environment, <mark style="background: #ADCCFFA6;">you may want to exclude email addresses from the Certificate template</mark> as your environment may not have an Exchange server or SMTP server integrated with Active Directory to pre-populate that information in the AD. <mark style="background: #ADCCFFA6;">If that information is not in the Active Directory record and this box is checked in the template, your certificate will not be issued to the user</mark>. <mark style="background: #FFB8EBA6;">The UPN in the Alternate Subject Name (SAN) is what the ISE Server will use to check the identity of the user in the Active Directory</mark>, if the Certificate Authentication Profile is configured with the SAN.

|General tab|Request Handling tab|Extensions tab|Security tab|Subject Name tab|
|---|---|---|---|---|
|![[General tab.png\|200]]|![[Request Handling tab.png\|200]]|![[Extensions tab.png\|200]]|![[Security tab.png\|200]]|![[Subject Name tab.png\|200]]|

Once the Domain Users Certificate Template is created, <mark style="background: #FF5582A6;">issue the template only on one of the SubordinateCA servers</mark> <mark style="background: #FFB86CA6;">if the design is to separate User Certificates</mark> from <mark style="background: #BBFABBA6;">Machine Certificates</mark>. In this case the <strong>User Certificate</strong> is issued on the <strong>SubordinateCA01</strong>.

![[Pasted image 20260424135651.png]]

#### Domain Admin Certificate

For the <strong>Domain Admin Certificate</strong> template copy the <strong>Domain User Certificate</strong> template and <mark style="background: #FFF3A3A6;">change Security tab <strong>Group or user names</strong> section</mark>, <mark style="background: #FFB86CA6;">remove Domain Users</mark> and in <mark style="background: #ABF7F7A6;">Domain Admin permissions, allow Read, Write, and Enroll</mark>. The Write permission is used to modify the certificate template.

As the Domain Admin Certificate is made for admins that have a domain user account but not a domain computer, the enrollment is done manually.

##### Enrollment - Windows Manual

![[Manual Enrollment of Admin Certificate.mp4]]

##### Enrollment - Windows Script

This PowerShell script enrolls the [[#Domain Admin Certificate]] (template <strong>EAP-Admin-User</strong>) on a Windows computer that is <u>not joined to the domain</u>, for an admin who has an account in Active Directory. It does the same job as [[#Enrollment - Windows Manual|the manual enrollment]], but the script creates the request, installs the CA chain, and installs the certificate: the only manual part is submitting the request in the browser.

###### What the script does

It runs in two steps and waits for you in between. <mark style="background: #ADCCFFA6;">Everything the script shows is in Italian</mark>, including how to start it (in the comment at the top) and the browser steps, so a user who has only the script file can follow it without this note.

1. <strong>Step1 - Create the request</strong>: creates a <strong>non-exportable</strong> private key and a certificate request (CSR) with `certreq`, copies the CSR to the clipboard (it is also saved as <strong>request.csr</strong> on the Desktop), shows the browser steps, and opens the web enrollment page of <strong>SubordinateCA01</strong> when you press <strong>ENTER</strong>.
2. <strong>You, in the browser</strong>: submit the CSR with the <strong>EAP-Admin-User</strong> template and download the issued certificate with its CA chain (<strong>certnew.p7b</strong>) to the <strong>Downloads</strong> folder.
3. <strong>Step2 - Install the certificate</strong>: finds the newest <strong>.p7b</strong> in Downloads and checks it (one user certificate plus the CA chain, <strong>Client Authentication</strong> EKU, valid today), installs the CA chain in the computer's <strong>Trusted Root</strong> and <strong>Intermediate</strong> stores, links the certificate to its private key with `certreq -accept`, confirms it is in your <strong>Personal</strong> store, logs the enrollment in the Application event log, and moves the files it used to the Recycle Bin.

###### Before you start

- The computer can open `https://subordinateca01.publiacqua.it/certsrv`.
- Your AD account can enroll the <strong>EAP-Admin-User</strong> template, as set on the [[#Domain Admin Certificate|template Security tab]].
- The Windows account you are logged in with is a <strong>local administrator</strong> of the computer. <mark style="background: #FF5582A6;">The certificate is installed for the Windows account that runs the script</mark>: if UAC asks for the username and password of another account, stop, because the certificate would end up in that account.

###### Step 1 - Save the script

1. Copy the whole [[#Script code|script]] below.
2. Open <strong>Notepad</strong> and paste it.
3. Click <strong>File → Save as</strong> and set:
    - Folder: `C:\Scripts` (create it if it does not exist)
    - File name: `Enroll-EAPAdminCert.ps1`
    - Save as type: <strong>All files (\*.\*)</strong>, otherwise Notepad adds `.txt`
    - Encoding: <strong>UTF-8 with BOM</strong>, so the accented letters in the Italian messages display correctly
4. Click <strong>Save</strong>.

###### Step 2 - Open PowerShell as administrator

1. Open the <strong>Start</strong> menu and type `PowerShell`.
2. Right-click <strong>Windows PowerShell</strong> and select <strong>Run as administrator</strong>.
3. Click <strong>Yes</strong> on the UAC prompt. The window title now starts with <strong>Administrator:</strong>.

###### Step 3 - Run the script

Type these commands, pressing <strong>ENTER</strong> after each one:

```powershell
cd C:\Scripts
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\Enroll-EAPAdminCert.ps1
```

The `Set-ExecutionPolicy` line lets scripts run in this window only: it does not change the computer's policy and ends when the window is closed.

The script creates the request, lists the browser steps (the same as [[#Step 4 - Request the certificate in the browser|Step 4]]), and opens the page when you press <strong>ENTER</strong> at <strong>Premi INVIO per aprire la pagina nel browser</strong>. It then waits with <strong>Quando certnew.p7b è nella cartella Download, premi INVIO per avviare il passo 2 (Q per uscire)</strong>: Step2 starts only when you press <strong>ENTER</strong>. <mark style="background: #FFB86CA6;">Leave the PowerShell window open.</mark>

###### Step 4 - Request the certificate in the browser

The script shows these steps in Italian; the page labels are in English because they appear that way on the CA page.

1. Sign in with your <strong>Publiacqua domain</strong> username and password.
2. On <strong>Submit a Certificate Request or Renewal Request</strong>, click in the <strong>Saved Request</strong> box and press <strong>Ctrl+V</strong>. The pasted text starts with `-----BEGIN NEW CERTIFICATE REQUEST-----`. If the box stays empty, open <strong>request.csr</strong> on the Desktop with Notepad, copy all of it, and paste it.
3. In <strong>Certificate Template</strong> select <strong>EAP-Admin-User</strong>.
4. Leave <strong>Additional Attributes</strong> empty and click <strong>Submit</strong>.
5. On <strong>Certificate Issued</strong> select <strong>Base 64 encoded</strong> and click <strong>Download certificate chain</strong>. This saves <strong>certnew.p7b</strong>, which holds your certificate and the CA chain. Do not use <strong>Download certificate</strong>: that <strong>.cer</strong> file has no CA chain and the script rejects it.
6. Save the file in the <strong>Downloads</strong> folder, the browser default; if the browser asks, keep the file. Do not open it or double-click it.
7. Go back to the PowerShell window and press <strong>ENTER</strong> to start Step2 (if you started with `-Step Step1`, run `-Step Step2` instead).

###### Step 5 - Finish the installation

1. Go back to the PowerShell window and press <strong>ENTER</strong>.
2. The script explains in Italian what it is about to do, then finds the file in Downloads, checks it, installs the CA chain, and then the certificate. No other action is needed.
3. The enrollment is complete when the script shows <strong>Certificato installato nell'archivio Personale dell'utente</strong> and then <strong>Registrazione completata</strong>, with how to check the certificate as in [[#Step 6 - Check the certificate|Step 6]].

###### Step 6 - Check the certificate

1. Press <strong>Win+R</strong>, type `certmgr.msc`, and press <strong>ENTER</strong>.
2. Open <strong>Personal → Certificates</strong>. Your certificate is listed, issued by the Subordinate CA, and its icon shows a small key: the private key is present.
3. Double-click it:
    - <strong>General</strong> says <strong>You have a private key that corresponds to this certificate</strong>.
    - <strong>Details → Enhanced Key Usage</strong> includes <strong>Client Authentication</strong>.
    - <strong>Certification Path</strong> shows the whole chain up to the Root CA with <strong>This certificate is OK</strong>.

The enrollment is also logged in <strong>Event Viewer → Windows Logs → Application</strong>, source <strong>EAPEnroll</strong>, Event ID <strong>1000</strong>, with the user, computer, and certificate thumbprint.

###### Run one step at a time

| Command | When to use it |
|---|---|
| `.\Enroll-EAPAdminCert.ps1` | Normal use: runs both steps and waits while you use the browser |
| `.\Enroll-EAPAdminCert.ps1 -Step Step1` | Only create the request and open the page |
| `.\Enroll-EAPAdminCert.ps1 -Step Step2` | Finish later, or after pressing <strong>Q</strong> at the prompt: installs the newest .p7b in Downloads |
| `.\Enroll-EAPAdminCert.ps1 -Step Step2 -CertPath 'C:\path\certnew.p7b'` | The file is not in Downloads, or the newest file there is not the right one |

<mark style="background: #FF5582A6;">Run Step2 on the same computer and with the same Windows account as Step1</mark>: the private key created in Step1 is stored only there, and without it the certificate cannot be installed. When Step2 runs on its own it takes the newest .p7b in Downloads, whatever its age.

###### Troubleshooting

| Message or problem | Cause | Fix |
|---|---|---|
| <strong>cannot be loaded because running scripts is disabled on this system</strong> | The execution policy blocks scripts | Run the `Set-ExecutionPolicy` line from [[#Step 3 - Run the script\|Step 3]], then the script again |
| <strong>Esegui lo script da Windows PowerShell aperto come amministratore</strong> | PowerShell is not elevated | Open PowerShell as in [[#Step 2 - Open PowerShell as administrator\|Step 2]] |
| Accented letters show as <strong>Ã¨</strong>, <strong>Ã¹</strong> | The script was saved without the BOM | Save it again with encoding <strong>UTF-8 with BOM</strong>, as in [[#Step 1 - Save the script\|Step 1]] |
| <strong>EAP-Admin-User</strong> is not in the Certificate Template list | The signed-in AD account cannot enroll the template, or the template is not issued on SubordinateCA01 | Sign in with your admin account; check the template [[#Domain Admin Certificate\|Security tab]] and that the template is issued on SubordinateCA01 |
| <strong>Nessun nuovo file .p7b in ...\Downloads</strong> | The file was saved outside Downloads | Run `-Step Step2 -CertPath` with the full path of the file |
| <strong>non contiene la catena CA</strong> or <strong>dovrebbe contenere 1 certificato utente</strong> | The wrong file was downloaded: <strong>Download certificate</strong> (.cer) or a CA-only chain | If the Certificate Issued page is still open, click <strong>Download certificate chain</strong> and run `-Step Step2`; otherwise run the script again from the start |
| <strong>Il certificato non ha l'utilizzo Client Authentication</strong> | The wrong template was selected | Run the script again from the start and select <strong>EAP-Admin-User</strong> |
| <strong>Il certificato è valido dal ... non adesso</strong> | The computer clock is wrong | <strong>Settings → Time & language → Date & time → Sync now</strong>, then run `-Step Step2` |
| <strong>certreq -accept non riuscito</strong> or <strong>non è nell'archivio Personale con la sua chiave privata</strong> | The certificate does not match a request made on this computer by this Windows account | Run the script again from the start, with the same account, and download the new certificate |

> [!warning] Trusted Root store
> The script adds the CA certificates it finds in the .p7b to the computer's <strong>Trusted Root</strong> and <strong>Intermediate</strong> stores. Use only a file downloaded from the SubordinateCA01 page the script opens.

###### Script code

```powershell
# Registrazione del certificato NAC (template EAP-Admin-User) su un PC Windows non in dominio.
# Come avviarlo:
#   1. Menu Start > digita PowerShell > clic destro su Windows PowerShell > Esegui come amministratore
#   2. Nella finestra esegui questi comandi (il secondo vale solo per questa finestra):
#        cd <cartella in cui si trova lo script>
#        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
#        .\Enroll-EAPAdminCert.ps1
#   Per completare in un secondo momento: .\Enroll-EAPAdminCert.ps1 -Step Step2 [-CertPath <certnew.p7b>]
param(
    [ValidateSet('All', 'Step1', 'Step2')]
    [string]$Step = 'All',
    [string]$CertPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Settings
$caUrl        = 'https://subordinateca01.publiacqua.it/certsrv/certrqxt.asp'
$template     = 'EAP-Admin-User'
$eventSource  = 'EAPEnroll'
$downloadsDir = Join-Path $env:USERPROFILE 'Downloads'
$infPath      = Join-Path $env:TEMP 'cert_request.inf'
$csrPath      = Join-Path ([Environment]::GetFolderPath('Desktop')) 'request.csr'
$scriptName   = $MyInvocation.MyCommand.Name
$step1Start   = $null

# User-context request with a non-exportable key and the Client Authentication EKU
$infContent = @"
[NewRequest]
Subject = "CN=$env:USERNAME"
KeyLength = 2048
Exportable = FALSE
MachineKeySet = FALSE
RequestType = PKCS10
ProviderName = "Microsoft Software Key Storage Provider"

[EnhancedKeyUsageExtension]
OID = 1.3.6.1.5.5.7.3.2 ; Client Authentication
"@

function Test-IsCA($Cert) {
    [bool]($Cert.Extensions | Where-Object {
        $_ -is [Security.Cryptography.X509Certificates.X509BasicConstraintsExtension] -and $_.CertificateAuthority })
}

function Get-IssuedCertificate([string]$Path) {
    # Returns the user certificate and its CA chain from the .p7b, or throws with the reason
    $all = New-Object Security.Cryptography.X509Certificates.X509Certificate2Collection
    $all.Import($Path)
    $caCerts = @($all | Where-Object { Test-IsCA $_ })
    $leaf    = @($all | Where-Object { -not (Test-IsCA $_) })

    if ($leaf.Count -ne 1) {
        throw "$Path dovrebbe contenere 1 certificato utente, ne contiene $($leaf.Count). Nella pagina 'Certificate Issued' fai clic su 'Download certificate chain'."
    }
    if ($caCerts.Count -eq 0) {
        throw "$Path non contiene la catena CA. Nella pagina 'Certificate Issued' fai clic su 'Download certificate chain', non su 'Download certificate'."
    }

    $ekus = @($leaf[0].Extensions |
        Where-Object { $_ -is [Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension] } |
        ForEach-Object { $_.EnhancedKeyUsages.Value })
    if ('1.3.6.1.5.5.7.3.2' -notin $ekus) {
        throw "Il certificato non ha l'utilizzo Client Authentication. Rifai la richiesta scegliendo il template $template."
    }

    $now = Get-Date
    if ($now -lt $leaf[0].NotBefore -or $now -gt $leaf[0].NotAfter) {
        throw "Il certificato è valido dal $($leaf[0].NotBefore) al $($leaf[0].NotAfter), non adesso. Controlla data e ora di questo computer."
    }

    [pscustomobject]@{ Leaf = $leaf[0]; CACerts = $caCerts }
}

function Invoke-Step1 {
    Write-Host "`n ==== Certificato NAC - Passo 1 di 2: richiesta ====" -ForegroundColor Cyan
    $script:step1Start = Get-Date
    Set-Content -Path $infPath -Value $infContent -Encoding ASCII
    if (Test-Path $csrPath) { Remove-Item $csrPath }

    certreq -new $infPath $csrPath
    if ($LASTEXITCODE -ne 0) { throw "certreq -new non riuscito (codice $LASTEXITCODE). La richiesta non è stata creata." }

    try {
        Get-Content $csrPath -Raw | Set-Clipboard
        Write-Host "`n La richiesta è stata copiata negli appunti (ed è salvata in $csrPath)." -ForegroundColor Green
    }
    catch {
        Write-Host "`n Appunti non disponibili: apri $csrPath con Blocco note e copia tutto il testo." -ForegroundColor Yellow
    }

    # With -Step Step1 the script ends here, so Step2 is started by running the script again
    $startStep2 = if ($Step -eq 'All') { 'e premi INVIO per avviare il passo 2' } else { "ed esegui .\$scriptName -Step Step2" }
    Write-Host @"

 Nella pagina che si apre nel browser:
   1. Accedi con nome utente e password del dominio Publiacqua
   2. Fai clic nella casella 'Saved Request' e premi Ctrl+V per incollare la richiesta
   3. In 'Certificate Template' seleziona $template
   4. Lascia vuoto 'Additional Attributes' e fai clic su 'Submit'
   5. Nella pagina 'Certificate Issued' seleziona 'Base 64 encoded' e fai clic su
      'Download certificate chain' (NON su 'Download certificate')
   6. Salva il file certnew.p7b nella cartella Download ($downloadsDir).
      Se il browser chiede conferma, scegli di mantenere il file
   7. Torna in questa finestra $startStep2
"@ -ForegroundColor Green
    [void](Read-Host "`n Premi INVIO per aprire la pagina nel browser")
    Start-Process $caUrl
}

function Invoke-Step2 {
    Write-Host "`n ==== Certificato NAC - Passo 2 di 2: installazione ====" -ForegroundColor Cyan
    Write-Host @"

 Ora lo script, senza altre azioni da parte tua:
   1. cerca certnew.p7b nella cartella Download e lo controlla
   2. installa su questo computer i certificati della CA Publiacqua
   3. installa il tuo certificato e lo collega alla chiave privata creata nel passo 1
   4. sposta nel Cestino i file usati
 Attendi il messaggio 'Registrazione completata'.
"@ -ForegroundColor Green
    $path = $CertPath
    if (-not $path) {
        # Newest .p7b in Downloads, saved after Step1 when Step1 ran in this session
        $path = Get-ChildItem $downloadsDir -Filter *.p7b -File -ErrorAction SilentlyContinue |
            Where-Object { -not $script:step1Start -or $_.LastWriteTime -ge $script:step1Start } |
            Sort-Object LastWriteTime | Select-Object -Last 1 -ExpandProperty FullName
        if (-not $path) {
            throw "Nessun nuovo file .p7b in $downloadsDir. Se l'hai salvato altrove esegui: .\$scriptName -Step Step2 -CertPath 'C:\percorso\certnew.p7b'"
        }
    }
    Write-Host "`n File: $path" -ForegroundColor Cyan
    $issued = Get-IssuedCertificate $path

    # The CA chain must be trusted first, or certreq -accept fails with UNTRUSTEDROOT
    foreach ($ca in $issued.CACerts) {
        $storeName = if ($ca.Subject -eq $ca.Issuer) { 'Root' } else { 'CA' }
        $store = New-Object Security.Cryptography.X509Certificates.X509Store($storeName, 'LocalMachine')
        $store.Open('ReadWrite')
        $store.Add($ca)
        $store.Close()
        Write-Host "  Certificato CA installato: $($ca.Subject)" -ForegroundColor DarkGreen
    }

    # Binds the issued certificate to the private key created in Step1
    certreq -accept $path
    if ($LASTEXITCODE -ne 0) {
        throw "certreq -accept non riuscito (codice $LASTEXITCODE). Il passo 1 e il passo 2 vanno eseguiti su questo computer con lo stesso account Windows."
    }

    $thumb = $issued.Leaf.Thumbprint
    if (-not (Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Thumbprint -eq $thumb -and $_.HasPrivateKey })) {
        throw "Il certificato è stato accettato ma non è nell'archivio Personale con la sua chiave privata, quindi l'autenticazione EAP-TLS non funzionerebbe. Riesegui lo script dall'inizio."
    }
    Write-Host "`n Certificato installato nell'archivio Personale dell'utente (impronta digitale $thumb)." -ForegroundColor Green

    try {
        if (-not [Diagnostics.EventLog]::SourceExists($eventSource)) { New-EventLog -LogName Application -Source $eventSource }
        Write-EventLog -LogName Application -Source $eventSource -EventId 1000 -EntryType Information `
            -Message "EAP cert enrolled for $env:USERNAME on $env:COMPUTERNAME, thumbprint $thumb, source file $path"
    }
    catch { Write-Warning "Voce nel registro eventi non scritta: $_" }

    # Recycle Bin rather than delete, so the files can be restored
    try {
        Add-Type -AssemblyName Microsoft.VisualBasic
        foreach ($file in $infPath, $csrPath, $path) {
            if (Test-Path $file) {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($file, 'OnlyErrorDialogs', 'SendToRecycleBin')
            }
        }
        Write-Host " File usati spostati nel Cestino." -ForegroundColor Green
    }
    catch { Write-Warning "File usati non spostati nel Cestino: $_" }

    Write-Host @"

 Registrazione completata. Per verificare il certificato:
   Win+R > digita certmgr.msc > INVIO > Personale > Certificati
   (l'icona del tuo certificato mostra una piccola chiave)
 Puoi chiudere questa finestra.
"@ -ForegroundColor Green
}

try {
    $identity = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not $identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Esegui lo script da Windows PowerShell aperto come amministratore: menu Start > digita PowerShell > clic destro su Windows PowerShell > Esegui come amministratore."
    }

    if ($Step -ne 'Step2') { Invoke-Step1 }
    if ($Step -eq 'All') {
        $answer = Read-Host "`n Quando certnew.p7b è nella cartella Download, premi INVIO per avviare il passo 2 (Q per uscire)"
        if ($answer -match '^[Qq]$') {
            Write-Host " Interrotto dopo il passo 1. Per completare più tardi esegui: .\$scriptName -Step Step2" -ForegroundColor Yellow
            exit 0
        }
    }
    if ($Step -ne 'Step1') { Invoke-Step2 }
}
catch {
    Write-Host "`n ERRORE: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
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

- On the <u>General tab</u> create a logical template name. The <strong>Publish certificate in Active Directory</strong> is used to publish the certificate into the computer <strong>userCertificate</strong> attribute in Active Directory. ![[Pasted image 20260424150609.png|200]]
- On the <u>Extensions tab</u>, highlight the <strong>Application Policies</strong> and click <strong>Edit</strong> to verify that <strong>Client Authentication</strong> (OID 1.3.6.1.5.5.7.3.2) is listed — it is the only application policy the default <strong>Workstation Authentication</strong> template carries, and the only EKU the machine needs to authenticate as an EAP-TLS client.
- On the <u>Security tab</u>, highlight <strong>Domain Computers</strong> and check the <strong>Allow</strong> boxes for <strong>Read</strong>, <strong>Enroll</strong>, and <strong>Autoenroll</strong> under the Permissions pane. <mark style="background: #FF5582A6;">This will be important when configuring our Group Policy to <strong>auto-enroll</strong> computers with a machine certificate</mark> for EAP authentication when they log into their computers.
- On the <u>Subject Name tab</u> under Subject Name Format, change it to <strong>Fully distinguished name</strong>, and leave the DNS Name checked. <mark style="background: #FFB8EBA6;">The DNS name in the Alternate Subject Name (SAN) is what the ISE Server will use to check the identity of the machine in the Active Directory</mark>, if the Certificate Authentication Profile is configured with the SAN.

| General tab                          | Extensions tab                       | Security tab                         | Subject Name tab                     |
| ------------------------------------ | ------------------------------------ | ------------------------------------ | ------------------------------------ |
| ![[Pasted image 20260424150448.png]] | ![[Pasted image 20260424141629.png]] | ![[Pasted image 20260424141754.png]] | ![[Pasted image 20260424141809.png]] |

Like the [[#Domain Users Certificate|User certificate template]], <mark style="background: #FF5582A6;">issue the template only on one of the SubordinateCA servers</mark> <mark style="background: #FFB86CA6;">if the design is to separate User Certificates</mark> from <mark style="background: #BBFABBA6;">Machine Certificates</mark>. In this case the <strong>Machine Certificate</strong> is issued on the <strong>SubordinateCA02</strong>.

![[Pasted image 20260424141851.png]]

#### Script To Remove Expired userCertificate

The expired certificates in the userCertificate attribute cannot be removed automatically; we should remove them manually or with the help of a script. By default this script is in read-only mode; read the description for how to use it.

[[Script To Remove Expired userCertificate]]

## Group Policy Management

The Group Policy Management service is used to deploy the configuration of the [[PBA - NAC - ISE Server#Dot1X (802.1X)|Windows native supplicant]], roll out the [[#Client Certificates]], and manage other user and computer configuration settings.

Make sure the GPO with the desired configuration is winning against other GPOs and its policies are enforced, and the <strong>Security Filtering</strong> is applied correctly. This can be checked with the <strong>Group Policy Results Wizard</strong> in <strong>Group Policy Management</strong>.

### Computer GPO

This GPO will be used to <mark style="background: #FFF3A3A6;">enroll Domain Computers</mark> with the [[#Domain Computer Certificate]] and enable <mark style="background: #FFB86CA6;">Wired AutoConfig</mark> on computers.

All computer GPOs must be created under the <strong>Group Policy Management → Forest: publiacqua.it → Domains → publiacqua.it → ComputerXp</strong> OU, which is where the Domain Computer accounts are stored. <mark style="background: #FFB8EBA6;"><u>After each change of computer GPO, there must be a <strong>gpupdate /force</strong> CMD command and a reboot of the client computer to apply the GPO configuration</u></mark>.

<strong>Wired AutoConfig</strong> (<strong>DOT3SVC</strong>) is a Windows service that manages <mark style="background: #FF5582A6;">IEEE 802.1X authentication on Ethernet connections</mark>. It enables computers to authenticate themselves on secure networks, often used in corporate environments to enforce network access control. The service is enabled at <strong>Computer Configuration → Policies → Windows Settings → Security Settings → System Services → Wired AutoConfig</strong>, setting the startup mode to Automatic.

![[Pasted Graphic 2.png]]

The [[#Domain Computer Certificate]] has Auto-Enrollment configured on its certificate template, so to enroll the computers we just need to enable the Auto-Enrollment.

To activate Auto-Enrollment go to <strong>Computer Configuration → Policies → Windows Settings → Security Settings → Public Key Policies → Certificate Services Client - Auto-Enrollment</strong>. Set the Configuration Model to Enabled and tick both checkboxes: renew expired, update pending, and remove revoked certificates; and update certificates that use certificate templates.

![[Pasted Graphic.png]]

<mark style="background: #ABF7F7A6;">Core 802.1X configuration is the <strong>Wired Network (IEEE 802.3) Policies</strong></mark> in <strong>Computer Configuration → Policies → Windows Settings → Security Settings → Wired Network (IEEE 802.3) Policies</strong>; in the current deployment there are <strong>[[#PEAP MSCHAPv2|PEAP]]</strong>, <strong>[[#TEAP]]</strong> and <strong>[[#EAP-TLS]]</strong>.

GPO hierarchy: <strong>EAP-TLS → PEAP-MSCHAPv2 → TEAP</strong>, from highest to lowest link precedence.

- <strong>TEAP</strong> GPO — scoped to <strong>Domain Computers</strong>. This makes TEAP the default authentication method for the entire fleet.
- <strong>PEAP MSCHAPv2</strong> GPO — scoped to a custom security group (e.g., <strong>GPO_C_PC_Enable_PEAP</strong>) for machines that require PEAP.
- <strong>EAP-TLS</strong> GPO — scoped to a custom security group (e.g., <strong>GPO_C_PC_Enable_EAP-TLS</strong>) for machines that require EAP-TLS.

Because the EAP-TLS and PEAP GPOs are linked at higher precedence than TEAP, <mark style="background: #FFB86CA6;">any computer added to one of the custom groups will have that GPO's wired profile applied last and override the default TEAP profile</mark>. <mark style="background: #BBFABBA6;">To switch a machine's authentication method, just add its computer object to the appropriate group</mark> — no per-machine configuration needed.

#### PEAP MSCHAPv2

PEAP is used for Domain Users that cannot or do not want to use a certificate to authenticate to ISE.

- <strong>General tab</strong>: enable <strong>Use Windows Wired Auto Config service for clients</strong>
- <strong>Security tab</strong>:
    - Enable <strong>Use IEEE 802.1X authentication for network access</strong>
    - Network authentication method: <strong>Microsoft: Protected EAP (PEAP)</strong>, go to <strong>Properties...</strong>
        - Tick <strong>Verify server's identity by validating certificate</strong>
        - <strong>Connect to these servers</strong>: Cisco ISE server FQDN
        - In Trusted Root Certification Authorities select the Root CA that signed the ISE [[#EAP Authentication Certificate]], and tick <strong>Don't ask user to authorize new servers or trusted CAs</strong>.
        - Authentication Method: <strong>Secured password (EAP-MSCHAP v2)</strong>
        - Tick <strong>Enable Fast Reconnect</strong>
    - Authentication Mode: <strong>User authentication</strong>
    - Max authentication failures: 1–3
    - <strong>Cache user information for subsequent connections</strong>: optional, decide whether to tick it.

Under <strong>Scope → Security Filtering</strong> of the GPO add the Group for which this GPO will be applied. In <strong>Delegation → Advanced</strong> ensure this Group has <strong>Apply group policy</strong> and <strong>Read</strong> in <strong>Allow</strong>.

#### EAP-TLS

This is a GPO with the authentication protocol set to EAP-TLS, made specifically for the RDP connections — see [[PBA - NAC - ISE Server#RDP Access|the policy rule]] made for this.

- <strong>General tab</strong>: enable <strong>Use Windows Wired Auto Config service for clients</strong>
- <strong>Security tab</strong>:
    - Enable <strong>Use IEEE 802.1X authentication for network access</strong>
    - Network authentication method: <strong>Microsoft: Smart Card or other certificate</strong>
        - Tick <strong>Use a certificate on this computer</strong>
        - Tick <strong>Use simple certificate selection</strong>
        - Tick <strong>Verify server's identity by validating certificate</strong>
        - Tick <strong>Connect to these servers</strong>: Cisco ISE servers FQDN
        - In <strong>Trusted Root Certification Authorities</strong> select the Root CA (only the Root CA) that signed the ISE [[#EAP Authentication Certificate]]
        - Tick <strong>Don't prompt user to authorize new servers or trusted certification authorities</strong>.
    - Authentication Mode: <strong>Computer only</strong>
    - Max authentication failures: 1–3

Under <strong>Scope → Security Filtering</strong> of the GPO add the Group for which this GPO will be applied. In <strong>Delegation → Advanced</strong> ensure this Group has <strong>Apply group policy</strong> and <strong>Read</strong> in <strong>Allow</strong>.

#### TEAP

The TEAP authentication protocol — described in [[PBA - NAC - ISE Server#Extensible Authentication Protocols|the ISE note]] — is the default protocol used by Domain Users and Domain Computers.

In the Group Policy Management editor the TEAP authentication method is not available; to roll out this authentication method we need to import an XML configuration from a working Win10/11 client.

##### TEAP profile

First we need to create a TEAP profile to export as XML.

On a domain-joined client that has both the machine and user certs already enrolled, configure the wired NIC manually so you can export it.

Open the NIC <strong>properties</strong> → <strong>Authentication</strong> tab:

1. Tick <strong>Enable IEEE 802.1X authentication</strong>.
2. Network authentication method → <strong>Microsoft: Tunnel EAP (TEAP)</strong>.
3. Click <strong>Settings</strong>:
    - <strong>Identity privacy</strong> → anonymous.
    - <strong>Connect to these servers</strong>: Cisco ISE servers FQDN.
    - <strong>Trusted Root Certification Authorities</strong> → tick the root that signed the ISE [[#EAP Authentication Certificate]]. (If you have a 2-tier PKI, <mark style="background: #FF5582A6;">only tick the <strong>offline root</strong></mark>, not the issuing CA).
    - Tick <strong>Don't prompt user if unable to authorize server</strong>
    - <strong>Client authentication</strong>:
        - <strong>Primary EAP method </strong>→ <mark style="background: #FFF3A3A6;">Microsoft: Smart Card or other certificate (EAP-TLS)</mark> → this is the computer authentication.
            - Tick <strong>Use a certificate on this computer</strong>
            - Tick <strong>Use simple certificate selection</strong>
            - Tick <strong>Verify server's identity by validating certificate</strong>
            - Tick <strong>Connect to these servers</strong>: Cisco ISE servers FQDN
            - In <strong>Trusted Root Certification Authorities</strong> select the Root CA (only the Root CA) that signed the ISE [[#EAP Authentication Certificate]]
            - Tick <strong>Don't prompt user to authorize new servers or trusted certification authorities</strong>.
        - <strong>Secondary EAP method</strong> → <mark style="background: #FFF3A3A6;">Microsoft: Smart Card or other certificate (EAP-TLS)</mark> → this becomes the user auth.
            - Tick <strong>Use a certificate on this computer</strong>
            - Tick <strong>Use simple certificate selection</strong>
            - Tick <strong>Verify server's identity by validating certificate</strong>
            - Tick <strong>Connect to these servers</strong>: Cisco ISE servers FQDN
            - In <strong>Trusted Root Certification Authorities</strong> select the Root CA (only the Root CA) that signed the ISE [[#EAP Authentication Certificate]]
            - Tick <strong>Don't prompt user to authorize new servers or trusted certification authorities</strong>.
4. Back on the <strong>Authentication</strong> tab → <strong>Additional settings</strong>
    - Tick <strong>Specify authentication mode</strong> → <strong>User or computer authentication</strong>.
    - Tick <strong>Enable Single Sign On for this network</strong>
        - Tick <strong>Perform immediately before user logon</strong>
        - Tick <strong>This network uses different VLAN for authentication with machine and user credentials</strong>. The <strong>Fallback to unauthorized network access</strong> option must remain <strong>ticked</strong>; without it, a user connecting to a switch port with no authenticator would get no network access.

##### Export the profile to XML

From an elevated cmd on the same client:

```powershell
netsh lan show profiles
netsh lan export profile folder=C:\Temp interface="Ethernet"
```

The `interface=""` value depends on the output of `netsh lan show profiles`.

Note that <strong>netsh</strong> can have a bug where the TrustedRootCAHash block has a malformed hash like `fc 5 c2 6 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e`, where bytes `0x05` and `0x06` came out as single hex digits. Change it to `fc 05 c2 06 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e`.

When there is more than one FQDN in the ServerNames block, separate the FQDNs with a semicolon <strong>;</strong> with no trailing spaces.

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

On the DC open Group Policy Management and create a new GPO linked to the OU that contains your domain computers. Edit it. <strong>Computer Configuration → Policies → Windows Settings → Security Settings → Wired Network (IEEE 802.3) Policies → right-click → Create A New Wired Network Policy for Windows Vista and Later Releases</strong>.

1. Make a dummy authentication profile that will be rewritten by the XML config file.
    - <strong>General tab</strong>: Choose a <strong>Policy Name</strong>, enable <strong>Use Windows Wired Auto Config service for clients</strong>
    - <strong>Security tab</strong>:
        - Enable <strong>Use IEEE 802.1X authentication for network access</strong>
        - Network authentication method: Pick <strong>Microsoft: Protected EAP (PEAP)</strong> as a placeholder; it will be overwritten.
    - <strong>Security → Advanced</strong>:
        - Tick <strong>Enforce advanced 802.1X settings</strong>
            - <strong>Max Eapol-Start Msgs</strong>: 2
            - <strong>Held Period</strong>: 60
            - <strong>Start Period</strong>: 3
            - <strong>Auth Period</strong>: 30
        - Tick <strong>Enable Single Sign On for this network</strong> → <strong>Perform immediately before user logon</strong>.
        - Tick <strong>This network uses different VLAN for authentication with machine and user credentials</strong>.
2. Save the policy, go to <strong>Group Policy Management → Forest: publiacqua.it → Domains → publiacqua.it → Group Policy Objects</strong>, find the saved policy.
3. Back Up... → Choose the Location (C:\Users\Username\Desktop).
4. Open the folder and open <strong>Backup.xml</strong> file with a text editor.
5. Find the block <strong>OneX xmlns="http://www.microsoft.com/networking/OneX/v1"</strong>
6. Replace the whole block with the customized one, save and close.
7. Return to <strong>Group Policy Objects</strong>, click <strong>Restore from Backup...</strong>
8. Select the Backup folder; if the GUID folder was inside <strong>C:\Users\username\Desktop</strong> just select <strong>C:\Users\username\Desktop</strong> and not the GUID folder.
9. Finish the restore of the backup.
10. Check that it works.

Under <strong>Scope → Security Filtering</strong> of the GPO add <strong>Domain Computers</strong>, which is the group this GPO will be applied to. In <strong>Delegation → Advanced</strong> ensure this Group has <strong>Apply group policy</strong> and <strong>Read</strong> in <strong>Allow</strong>.

### User GPO

This GPO will be used to <mark style="background: #FFF3A3A6;">enroll Domain Users</mark> with the [[#Domain Users Certificate]].

All user GPOs must be created under the <strong>Group Policy Management → Forest: publiacqua.it → Domains → publiacqua.it → Publiacqua</strong> OU, which is where the Domain User accounts are stored. <mark style="background: #CACFD9A6;">At each change of user GPO, there must be a <strong>gpupdate /force</strong> CMD command to apply the GPO configuration</mark>.

To activate Auto-Enrollment go to <strong>User Configuration → Policies → Windows Settings → Security Settings → Public Key Policies → Certificate Services Client - Auto-Enrollment</strong>

![[Pasted Graphic 3.png]]

The GPO should be in <strong>Enforced</strong> mode to ensure that it will be applied. As with the computer GPOs, check under Scope → Security Filtering that the GPO applies to the intended user group.