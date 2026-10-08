This PowerShell script enrolls the [[#Domain Admin Certificate]] (template <strong>EAP-Admin-User</strong>) on a Windows computer that is <u>not joined to the domain</u>, for an admin who has an account in Active Directory. It does the same job as [[#Enrollment - Windows Manual|the manual enrollment]]: the script creates the request, installs the CA chain and installs the certificate, so the only manual part is submitting the request in the browser.

###### What the script does

The script runs in two parts and waits for you in between. <mark style="background: #ADCCFFA6;">Everything the script shows is in Italian</mark>, including how to start it (in the comment at the top of the file) and the browser steps, so a user who has only the script file can follow it without this guide.

1. <strong>Part 1 - Request</strong> (<strong>Passo 1 di 2</strong> in the window): creates a <strong>non-exportable</strong> private key and a certificate request (CSR) with `certreq`. It shows the request in the window, copies it to the clipboard and saves it as <strong>request.csr</strong> on the Desktop, lists the browser steps, and opens the web enrollment page of <strong>SubordinateCA01</strong> when you press <strong>ENTER</strong>.
2. <strong>You, in the browser</strong>: submit the request with the <strong>EAP-Admin-User</strong> template and download the issued certificate with its CA chain (<strong>certnew.p7b</strong>) to the <strong>Downloads</strong> folder.
3. <strong>Part 2 - Installation</strong> (<strong>Passo 2 di 2</strong>): finds the newest <strong>.p7b</strong> in Downloads and checks it (one user certificate plus the CA chain up to the Root CA, <strong>Client Authentication</strong> EKU, valid today). It installs the CA certificates in the computer's <strong>Trusted Root Certification Authorities</strong> and <strong>Intermediate Certification Authorities</strong> stores, links your certificate to its private key with `certreq -accept`, confirms it is in your <strong>Personal</strong> store with its private key, logs the enrollment in the Application event log, and moves the files it used to the Recycle Bin.

###### Before you start

- The computer is on the company network and can open `https://subordinateca01.publiacqua.it/certsrv`.
- Your AD account can enroll the <strong>EAP-Admin-User</strong> template, as set on the [[#Domain Admin Certificate|template Security tab]].
- The Windows account you are logged in with is a <strong>local administrator</strong> of the computer. <mark style="background: #FF5582A6;">The certificate is installed for the Windows account that runs the script</mark>: if UAC asks for the username and password of another account, stop, because the certificate would end up in that account. The script also checks this and stops.

###### 1. Save the script

If you already have the file <strong>Enroll-EAPAdminCert.ps1</strong>, copy it to `C:\Scripts` and go to [[#2. Open PowerShell as administrator]]. Otherwise:

1. Copy the whole [[#Script code|script]] below.
2. Open <strong>Notepad</strong> and paste it.
3. Click <strong>File → Save as</strong> and set:
    - Folder: `C:\Scripts` (create it if it does not exist)
    - File name: `Enroll-EAPAdminCert.ps1`
    - Save as type: <strong>All files (\*.\*)</strong>, otherwise Notepad adds `.txt`
    - Encoding: <strong>UTF-8 with BOM</strong>, so the accented letters in the Italian messages display correctly
4. Click <strong>Save</strong>.

###### 2. Open PowerShell as administrator

1. Open the <strong>Start</strong> menu and type `PowerShell`.
2. Right-click <strong>Windows PowerShell</strong> and select <strong>Run as administrator</strong>.
3. Click <strong>Yes</strong> on the UAC prompt. The window title now starts with <strong>Administrator:</strong>.

###### 3. Run the script

Type these commands, pressing <strong>ENTER</strong> after each one:

```powershell
cd C:\Scripts
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\Enroll-EAPAdminCert.ps1
```

The `Set-ExecutionPolicy` line lets scripts run in this window only: it does not change the computer's policy and ends when the window is closed.

Part 1 starts: the script creates the request, shows it in the window, copies it to the clipboard and lists the browser steps (the same as [[#4. Request the certificate in the browser]]). When you press <strong>ENTER</strong> at <strong>Premi INVIO per aprire la pagina nel browser</strong>, it opens the CA page and waits with <strong>Quando certnew.p7b è nella cartella Download, premi INVIO per avviare il passo 2 (per interrompere scrivi Q e premi INVIO)</strong>.

<mark style="background: #FFB86CA6;">Leave the PowerShell window open</mark> and go to the browser. If you need to stop here, type <strong>Q</strong> and press <strong>ENTER</strong>, then finish later as in [[#Run one part at a time]].

###### 4. Request the certificate in the browser

The script shows these same steps in Italian. The page labels are in English because they appear that way on the CA page.

1. If the browser asks, sign in with your <strong>Publiacqua domain</strong> username and password.
2. On <strong>Submit a Certificate Request or Renewal Request</strong>, click in the <strong>Saved Request</strong> box and press <strong>Ctrl+V</strong>. The pasted text starts with `-----BEGIN NEW CERTIFICATE REQUEST-----`. If the box stays empty, open <strong>request.csr</strong> on the Desktop with Notepad, copy all of it and paste it. The same text is also shown in the PowerShell window.
3. In <strong>Certificate Template</strong> select <strong>EAP-Admin-User</strong>.
4. Leave <strong>Additional Attributes</strong> empty and click <strong>Submit</strong>.
5. On <strong>Certificate Issued</strong> select <strong>Base 64 encoded</strong> and click <strong>Download certificate chain</strong>. This saves <strong>certnew.p7b</strong>, which holds your certificate and the CA chain. Do not use <strong>Download certificate</strong>: it saves <strong>certnew.cer</strong>, which has no CA chain, and the script does not find it.
6. Save the file in the <strong>Downloads</strong> folder, the browser default. If the browser asks, keep the file. Do not open it: the script installs it.
7. Go back to the PowerShell window and press <strong>ENTER</strong> to start part 2 (if you started the script with `-Step Step1`, run `.\Enroll-EAPAdminCert.ps1 -Step Step2` instead).

###### 5. Finish the installation

Part 2 needs no action from you: the script explains in Italian what it is about to do, then finds the file in Downloads, checks it, installs the CA certificates and then your certificate.

The enrollment is complete when the script shows <strong>Certificato installato nell'archivio Personale dell'utente</strong> and then <strong>Registrazione completata</strong>. You can close the window.

###### 6. Check the certificate

1. Press <strong>Win+R</strong>, type `certmgr.msc` and press <strong>ENTER</strong>.
2. Open <strong>Personal → Certificates</strong>. Your certificate is listed, issued by the Subordinate CA, and its icon shows a small key: the private key is present.
3. Double-click it:
    - <strong>General</strong> says <strong>You have a private key that corresponds to this certificate</strong>.
    - <strong>Details → Enhanced Key Usage</strong> includes <strong>Client Authentication</strong>.
    - <strong>Certification Path</strong> shows the whole chain up to the Root CA with <strong>This certificate is OK</strong>.

The enrollment is also logged in <strong>Event Viewer → Windows Logs → Application</strong>, source <strong>EAPEnroll</strong>, Event ID <strong>1000</strong>, with the user, computer, certificate thumbprint, the file used, and the CA certificates added to the computer's stores.

###### Run one part at a time

| Command | When to use it |
|---|---|
| `.\Enroll-EAPAdminCert.ps1` | Normal use: runs both parts and waits while you use the browser |
| `.\Enroll-EAPAdminCert.ps1 -Step Step1` | Only create the request and open the CA page |
| `.\Enroll-EAPAdminCert.ps1 -Step Step2` | Finish later, after `-Step Step1` or after typing <strong>Q</strong>: installs the newest .p7b in Downloads |
| `.\Enroll-EAPAdminCert.ps1 -Step Step2 -CertPath "C:\path\certnew.p7b"` | The file is not in Downloads, or the newest .p7b there is not the right one |

To run part 2 in a new window, open PowerShell as in [[#2. Open PowerShell as administrator]] and repeat the `cd` and `Set-ExecutionPolicy` commands first.

<mark style="background: #FF5582A6;">Run part 2 on the same computer and with the same Windows account as part 1</mark>: the private key created in part 1 is stored only there, and without it the certificate cannot be installed. When part 2 runs in the same window as part 1, it only takes a .p7b saved after part 1 started; when it runs on its own, it takes the newest .p7b in Downloads, whatever its age.

###### Troubleshooting

| Message or problem | Cause | Fix |
|---|---|---|
| <strong>running scripts is disabled on this system</strong> (on Italian Windows: <strong>L'esecuzione di script è disabilitata nel sistema in uso</strong>) | The execution policy blocks scripts | Run the `Set-ExecutionPolicy` line from [[#3. Run the script\|3. Run the script]], then the script again |
| <strong>Lo script va avviato da PowerShell come amministratore</strong> | PowerShell is not running as administrator | Open PowerShell as in [[#2. Open PowerShell as administrator\|2. Open PowerShell as administrator]] |
| <strong>PowerShell è stato avviato come amministratore con un altro account</strong> | UAC asked for another account's username and password, because the Windows account you are logged in with is not a local administrator | Have IT make your Windows account a local administrator of the computer, then start again from [[#2. Open PowerShell as administrator\|2. Open PowerShell as administrator]] |
| Warning <strong>Non è stato possibile verificare con quale account è stato avviato PowerShell</strong> | The script could not check which account PowerShell is running as | Continue only if UAC did not ask for another account's username and password; otherwise close the window and see the row above |
| Accented letters show as <strong>Ã¨</strong>, <strong>Ã¹</strong> | The script was saved without the BOM | Save it again with encoding <strong>UTF-8 with BOM</strong>, as in [[#1. Save the script\|1. Save the script]] |
| <strong>Non è stato possibile creare la richiesta</strong> | `certreq` could not create the key or the request | Run the script again; if the error repeats, contact IT with the message shown |
| <strong>EAP-Admin-User</strong> is not in the <strong>Certificate Template</strong> list | The signed-in AD account cannot enroll the template, or the template is not issued on SubordinateCA01 | Sign in with your admin account; check the template [[#Domain Admin Certificate\|Security tab]] and that the template is issued on SubordinateCA01 |
| <strong>non c'è un nuovo file certnew.p7b</strong> | The file was not downloaded yet, was downloaded with <strong>Download certificate</strong> (<strong>certnew.cer</strong>), or was saved outside Downloads | If the Certificate Issued page is still open, click <strong>Download certificate chain</strong> and run `-Step Step2`; otherwise run the script again from the start. If the .p7b is in another folder, run `-Step Step2 -CertPath` with the full path of the file |
| <strong>Il file ... non esiste</strong> | The path given with `-CertPath` is wrong | In File Explorer right-click the file and select <strong>Copy as path</strong> (on Windows 10 hold <strong>Shift</strong> while right-clicking), then run `-Step Step2 -CertPath` and paste the path |
| <strong>non la catena della CA</strong>, <strong>dovrebbe contenere 1 certificato personale</strong>, <strong>non contiene il certificato della CA radice</strong>, or <strong>non contiene certificati leggibili</strong> | The file is not the one saved with <strong>Download certificate chain</strong> (for example a .cer passed with `-CertPath`), or the download did not complete | If the Certificate Issued page is still open, click <strong>Download certificate chain</strong> and run `-Step Step2`; otherwise run the script again from the start |
| <strong>manca l'utilizzo Client Authentication</strong> | The wrong template was selected | Run the script again from the start and select <strong>EAP-Admin-User</strong> |
| <strong>Il certificato è valido dal ... ma la data di questo PC è ...</strong> | The computer clock is wrong | <strong>Settings → Time & language → Date & time → Sync now</strong>, then run `-Step Step2` |
| <strong>certreq -accept, codice</strong> or <strong>installato senza la sua chiave privata</strong> | The certificate does not match a request made on this computer by this Windows account | Run the script again from the start, with the same account, and download the new certificate |

> [!warning] Trusted Root store
> Part 2 adds the CA certificates it finds in the .p7b to the computer's <strong>Trusted Root Certification Authorities</strong> and <strong>Intermediate Certification Authorities</strong> stores, without checking which CA they belong to. Use only a file downloaded from the SubordinateCA01 page the script opens. The certificates added are listed in the event log entry, so they can be found and removed if needed.

###### Script code

```powershell
# Certificato NAC per PC Windows non in dominio (template EAP-Admin-User).
# Richiede e installa il certificato con cui ti autentichi alla rete aziendale da questo PC,
# usando il tuo account del dominio Publiacqua.
#
# Come avviarlo:
#   1. Apri il menu Start e digita PowerShell
#   2. Clic destro su Windows PowerShell > Esegui come amministratore, poi Sì.
#      Se Windows chiede nome utente e password di un altro account, fermati:
#      il certificato verrebbe installato per quell'account e non per il tuo.
#   3. Nella finestra di PowerShell esegui questi comandi, premendo INVIO dopo ciascuno
#      (il secondo permette di eseguire script solo in questa finestra):
#        cd "<cartella in cui hai salvato lo script>"
#        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
#        .\Enroll-EAPAdminCert.ps1
#   4. Segui le istruzioni che compaiono nella finestra.
#
# Se hai chiuso la finestra dopo il passo 1, ripeti i punti 1-3 usando come ultimo comando
#   .\Enroll-EAPAdminCert.ps1 -Step Step2
# e aggiungi -CertPath "<percorso di certnew.p7b>" se il file non è nella cartella Download.
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
$infPath      = Join-Path $env:TEMP 'cert_request.inf'
$csrPath      = Join-Path ([Environment]::GetFolderPath('Desktop')) 'request.csr'
$scriptName   = $MyInvocation.MyCommand.Name
$step2Command = ".\$scriptName -Step Step2"
$step1Start   = $null

# Resolved through the shell, so a Downloads folder moved elsewhere is still found
$downloadsDir = try { (New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path } catch { $null }
if (-not $downloadsDir) { $downloadsDir = Join-Path $env:USERPROFILE 'Downloads' }

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

function Test-IsSelfSigned($Cert) {
    $Cert.Subject -eq $Cert.Issuer
}

function Assert-DesktopUser {
    # Elevating with another account's credentials would install the certificate for that account
    $sessionId = (Get-Process -Id $PID).SessionId
    $shell = Get-CimInstance Win32_Process -Filter "Name='explorer.exe' AND SessionId=$sessionId" | Select-Object -First 1
    if (-not $shell) {
        Write-Warning "Non è stato possibile verificare con quale account è stato avviato PowerShell. Se hai inserito nome utente e password di un altro account, chiudi la finestra: il certificato verrebbe installato per quell'account."
        return
    }
    $shellSid = (Invoke-CimMethod -InputObject $shell -MethodName GetOwnerSid).Sid
    if ($shellSid -ne [Security.Principal.WindowsIdentity]::GetCurrent().User.Value) {
        throw "PowerShell è stato avviato come amministratore con un altro account, quindi il certificato verrebbe installato per quell'account e non per il tuo. Il tuo account Windows deve essere amministratore di questo PC: contatta il reparto IT."
    }
}

function Get-IssuedCertificate([string]$Path) {
    # Returns the user certificate and its CA chain from the .p7b, or throws with the reason
    $downloadAgain = "Nella pagina 'Certificate Issued' fai clic su 'Download certificate chain', poi esegui $step2Command. Se hai già chiuso la pagina, esegui di nuovo lo script dall'inizio."

    $all = New-Object Security.Cryptography.X509Certificates.X509Certificate2Collection
    try { $all.Import($Path) }
    catch {
        throw "Il file $Path non contiene certificati leggibili: forse il download non è andato a buon fine. $downloadAgain (Dettaglio tecnico: $($_.Exception.Message))"
    }
    $caCerts = @($all | Where-Object { Test-IsCA $_ })
    $leaf    = @($all | Where-Object { -not (Test-IsCA $_) })

    if ($leaf.Count -ne 1) {
        throw "Il file $Path non è quello giusto: dovrebbe contenere 1 certificato personale, ne contiene $($leaf.Count). $downloadAgain"
    }
    if ($caCerts.Count -eq 0) {
        throw "Il file $Path contiene il tuo certificato ma non la catena della CA, perché è stato scaricato con 'Download certificate'. $downloadAgain"
    }

    # 'Download certificate chain' always includes the root CA, which certreq -accept needs to trust the chain
    if (-not ($caCerts | Where-Object { Test-IsSelfSigned $_ })) {
        throw "Il file $Path non contiene il certificato della CA radice Publiacqua. $downloadAgain"
    }

    $ekus = @($leaf[0].Extensions |
        Where-Object { $_ -is [Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension] } |
        ForEach-Object { $_.EnhancedKeyUsages.Value })
    if ('1.3.6.1.5.5.7.3.2' -notin $ekus) {
        throw "Il certificato non vale per l'accesso alla rete (manca l'utilizzo Client Authentication): probabilmente è stato scelto un template diverso da $template. Esegui di nuovo lo script dall'inizio e scegli $template."
    }

    $now = Get-Date
    if ($now -lt $leaf[0].NotBefore -or $now -gt $leaf[0].NotAfter) {
        throw "Il certificato è valido dal $($leaf[0].NotBefore) al $($leaf[0].NotAfter), ma la data di questo PC è $now. Correggi data e ora del PC, poi esegui $step2Command."
    }

    [pscustomobject]@{ Leaf = $leaf[0]; CACerts = $caCerts }
}

function Invoke-Step1 {
    Write-Host @"

 ==== Certificato NAC - Passo 1 di 2: richiesta del certificato ====

 Lo script crea una richiesta di certificato e una chiave privata, che resta su questo PC
 e non può essere esportata. Poi apre la pagina della CA Publiacqua, dove invii la
 richiesta e scarichi il certificato.

"@ -ForegroundColor Cyan
    $script:step1Start = Get-Date
    # Unicode keeps accented characters in the user name intact
    Set-Content -Path $infPath -Value $infContent -Encoding Unicode
    if (Test-Path $csrPath) { Remove-Item $csrPath }

    certreq -new $infPath $csrPath
    if ($LASTEXITCODE -ne 0) {
        throw "Non è stato possibile creare la richiesta (certreq -new, codice $LASTEXITCODE). Esegui di nuovo lo script; se l'errore si ripete, contatta il reparto IT."
    }

    $csr = Get-Content $csrPath -Raw
    Write-Host "`n Richiesta di certificato (salvata anche in $csrPath):`n" -ForegroundColor Cyan
    Write-Host $csr
    try {
        Set-Clipboard -Value $csr
        Write-Host " La richiesta è stata copiata negli appunti." -ForegroundColor Green
    }
    catch {
        Write-Host "`n Appunti non disponibili: apri $csrPath con Blocco note, copia tutto il testo e incollalo al punto 2." -ForegroundColor Yellow
    }

    # With -Step Step1 the script ends here, so Step2 is started by running the script again
    $startStep2 = if ($Step -eq 'All') { 'e premi INVIO per avviare il passo 2' } else { "ed esegui $step2Command" }
    Write-Host @"

 Dopo aver premuto INVIO si apre la pagina della CA nel browser. Nella pagina:
   1. Se il browser lo chiede, accedi con nome utente e password del dominio Publiacqua
   2. Fai clic nella casella 'Saved Request' e premi Ctrl+V per incollare la richiesta
      (il testo inizia con -----BEGIN NEW CERTIFICATE REQUEST-----)
   3. In 'Certificate Template' scegli $template
   4. Lascia vuoto 'Additional Attributes' e fai clic su 'Submit'
   5. Nella pagina 'Certificate Issued' seleziona 'Base 64 encoded', poi fai clic su
      'Download certificate chain' (NON su 'Download certificate')
   6. Salva il file certnew.p7b nella cartella Download ($downloadsDir).
      Se il browser chiede conferma, scegli di mantenere il file
   7. Torna in questa finestra $startStep2
"@ -ForegroundColor Green
    [void](Read-Host "`n Premi INVIO per aprire la pagina nel browser")
    # Opened through explorer so the browser runs without administrator rights
    Start-Process explorer.exe $caUrl
}

function Invoke-Step2 {
    Write-Host @"

 ==== Certificato NAC - Passo 2 di 2: installazione del certificato ====

 Non devi fare nulla: lo script controlla il file scaricato, installa su questo PC i
 certificati della CA Publiacqua e poi il tuo certificato, collegandolo alla chiave
 privata creata nel passo 1. Infine sposta nel Cestino i file che non servono più.
 Attendi il messaggio "Registrazione completata".
"@ -ForegroundColor Cyan
    if ($CertPath) {
        if (-not (Test-Path -LiteralPath $CertPath -PathType Leaf)) {
            throw "Il file $CertPath non esiste. Controlla il percorso, poi esegui $step2Command -CertPath `"<percorso completo del file>`"."
        }
        # .NET resolves relative paths against the process folder, not the PowerShell location
        $path = (Resolve-Path -LiteralPath $CertPath).ProviderPath
    }
    else {
        # Newest .p7b in Downloads, saved after Step1 when Step1 ran in this session
        $path = Get-ChildItem $downloadsDir -Filter *.p7b -File -ErrorAction SilentlyContinue |
            Where-Object { -not $script:step1Start -or $_.LastWriteTime -ge $script:step1Start } |
            Sort-Object LastWriteTime | Select-Object -Last 1 -ExpandProperty FullName
        if (-not $path) {
            throw "Nella cartella $downloadsDir non c'è un nuovo file certnew.p7b. Se non l'hai ancora scaricato, segui i punti 5 e 6 del passo 1, poi esegui $step2Command. Se l'hai salvato in un'altra cartella, esegui $step2Command -CertPath `"<percorso completo del file>`"."
        }
    }
    Write-Host "`n File del certificato: $path" -ForegroundColor Cyan
    $issued = Get-IssuedCertificate $path

    # The CA chain must be trusted first, or certreq -accept fails with UNTRUSTEDROOT
    foreach ($ca in $issued.CACerts) {
        $storeName = if (Test-IsSelfSigned $ca) { 'Root' } else { 'CA' }
        $store = New-Object Security.Cryptography.X509Certificates.X509Store($storeName, 'LocalMachine')
        try {
            $store.Open('ReadWrite')
            $store.Add($ca)
        }
        finally { $store.Close() }
        Write-Host "  Certificato della CA installato: $($ca.Subject)" -ForegroundColor DarkGreen
    }

    # Binds the issued certificate to the private key created in Step1
    certreq -accept -user $path
    if ($LASTEXITCODE -ne 0) {
        throw "Non è stato possibile installare il certificato (certreq -accept, codice $LASTEXITCODE). Il certificato va richiesto e installato su questo PC con lo stesso account Windows: esegui di nuovo lo script dall'inizio."
    }

    $thumb = $issued.Leaf.Thumbprint
    if (-not (Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Thumbprint -eq $thumb -and $_.HasPrivateKey })) {
        throw "Il certificato è stato installato senza la sua chiave privata, quindi non funzionerebbe per l'accesso alla rete. Esegui di nuovo lo script dall'inizio."
    }
    Write-Host "`n Certificato installato nell'archivio Personale dell'utente (impronta digitale $thumb)." -ForegroundColor Green

    # CA thumbprints are logged so the machine-wide changes can be reviewed or reverted
    $caList = ($issued.CACerts | ForEach-Object { "$($_.Subject) [$($_.Thumbprint)]" }) -join '; '
    try {
        if (-not [Diagnostics.EventLog]::SourceExists($eventSource)) { New-EventLog -LogName Application -Source $eventSource }
        Write-EventLog -LogName Application -Source $eventSource -EventId 1000 -EntryType Information `
            -Message "EAP cert enrolled for $env:USERNAME on $env:COMPUTERNAME, thumbprint $thumb, source file $path. CA certificates added to LocalMachine stores: $caList"
    }
    catch { Write-Warning "Non è stato possibile scrivere l'operazione nel registro eventi (il certificato non ne risente): $_" }

    # Recycle Bin rather than delete, so the files can be restored
    try {
        Add-Type -AssemblyName Microsoft.VisualBasic
        foreach ($file in $infPath, $csrPath, $path) {
            if (Test-Path -LiteralPath $file) {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($file, 'OnlyErrorDialogs', 'SendToRecycleBin')
            }
        }
        Write-Host " File usati spostati nel Cestino." -ForegroundColor Green
    }
    catch { Write-Warning "Non è stato possibile spostare nel Cestino i file usati (il certificato non ne risente): $_" }

    Write-Host @"

 Registrazione completata: il tuo certificato è installato.
 Per verificarlo premi Win+R, digita certmgr.msc e premi INVIO, poi apri
 Personale > Certificati: il tuo certificato ha un'icona con una piccola chiave.
 Puoi chiudere questa finestra.
"@ -ForegroundColor Green
}

try {
    $identity = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not $identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Lo script va avviato da PowerShell come amministratore: menu Start > digita PowerShell > clic destro su Windows PowerShell > Esegui come amministratore. Nella nuova finestra esegui di nuovo i comandi cd, Set-ExecutionPolicy e .\$scriptName."
    }
    Assert-DesktopUser

    if ($Step -ne 'Step2') { Invoke-Step1 }
    if ($Step -eq 'All') {
        $answer = Read-Host "`n Quando certnew.p7b è nella cartella Download, premi INVIO per avviare il passo 2 (per interrompere scrivi Q e premi INVIO)"
        if ($answer -match '^[Qq]$') {
            Write-Host " Interrotto dopo il passo 1. Per completare più tardi esegui $step2Command (in una nuova finestra di PowerShell ripeti prima i comandi cd e Set-ExecutionPolicy)." -ForegroundColor Yellow
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
