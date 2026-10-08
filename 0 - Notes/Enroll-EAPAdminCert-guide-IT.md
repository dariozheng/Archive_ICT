Questo script PowerShell registra il [[#Domain Admin Certificate|certificato Domain Admin]] (template <strong>EAP-Admin-User</strong>) su un computer Windows <u>non aggiunto al dominio</u>, per un amministratore che ha un account in Active Directory. Fa lo stesso lavoro della [[#Enrollment - Windows Manual|registrazione manuale]]: lo script crea la richiesta, installa la catena della CA e installa il certificato, quindi l'unica parte manuale è l'invio della richiesta nel browser.

###### Cosa fa lo script

Lo script lavora in due passi e tra l'uno e l'altro aspetta te. <mark style="background: #ADCCFFA6;">Tutti i messaggi dello script sono in italiano</mark>, comprese le istruzioni per avviarlo (nel commento all'inizio del file) e i passaggi da fare nel browser, quindi chi ha solo il file dello script può seguirlo anche senza questa guida.

1. <strong>Passo 1 - Richiesta</strong> (<strong>Passo 1 di 2</strong> nella finestra): crea con `certreq` una chiave privata <strong>non esportabile</strong> e una richiesta di certificato (CSR). Mostra la richiesta nella finestra, la copia negli appunti e la salva come <strong>request.csr</strong> sul Desktop, elenca i passaggi da fare nel browser e, quando premi <strong>INVIO</strong>, apre la pagina di registrazione web di <strong>SubordinateCA01</strong>.
2. <strong>Tu, nel browser</strong>: invii la richiesta con il template <strong>EAP-Admin-User</strong> e scarichi il certificato emesso con la catena della CA (<strong>certnew.p7b</strong>) nella cartella <strong>Download</strong>.
3. <strong>Passo 2 - Installazione</strong> (<strong>Passo 2 di 2</strong>): trova il file <strong>.p7b</strong> più recente nella cartella Download e lo controlla (un solo certificato personale più la catena della CA fino alla CA radice, utilizzo <strong>Client Authentication</strong>, valido oggi). Installa i certificati della CA negli archivi del computer <strong>Autorità di certificazione radice attendibili</strong> e <strong>Autorità di certificazione intermedie</strong>, collega il tuo certificato alla sua chiave privata con `certreq -accept`, verifica che sia nell'archivio <strong>Personale</strong> con la chiave privata, registra l'operazione nel registro eventi Applicazione e sposta nel Cestino i file usati.

###### Prima di iniziare

- Il computer è collegato alla rete aziendale e riesce ad aprire `https://subordinateca01.publiacqua.it/certsrv`.
- Il tuo account AD può registrare il template <strong>EAP-Admin-User</strong>, come impostato nella [[#Domain Admin Certificate|scheda Sicurezza del template]].
- L'account Windows con cui hai effettuato l'accesso è <strong>amministratore locale</strong> del computer. <mark style="background: #FF5582A6;">Il certificato viene installato per l'account Windows che esegue lo script</mark>: se il Controllo dell'account utente (UAC) chiede nome utente e password di un altro account, fermati, perché il certificato finirebbe in quell'account. Anche lo script lo controlla e in quel caso si ferma.

###### 1. Salva lo script

Se hai già il file <strong>Enroll-EAPAdminCert.ps1</strong>, copialo in `C:\Scripts` e passa a [[#2. Apri PowerShell come amministratore]]. Altrimenti:

1. Copia tutto il [[#Codice dello script|codice dello script]] qui sotto.
2. Apri <strong>Blocco note</strong> e incollalo.
3. Fai clic su <strong>File → Salva con nome</strong> e imposta:
    - Cartella: `C:\Scripts` (creala se non esiste)
    - Nome file: `Enroll-EAPAdminCert.ps1`
    - Salva come: <strong>Tutti i file (\*.\*)</strong>, altrimenti Blocco note aggiunge `.txt`
    - Codifica: <strong>UTF-8 con BOM</strong>, così le lettere accentate dei messaggi si vedono correttamente
4. Fai clic su <strong>Salva</strong>.

###### 2. Apri PowerShell come amministratore

1. Apri il menu <strong>Start</strong> e digita `PowerShell`.
2. Fai clic con il tasto destro su <strong>Windows PowerShell</strong> e seleziona <strong>Esegui come amministratore</strong>.
3. Nella finestra del Controllo dell'account utente fai clic su <strong>Sì</strong>. Il titolo della finestra ora inizia con <strong>Amministratore:</strong>.

###### 3. Avvia lo script

Digita questi comandi, premendo <strong>INVIO</strong> dopo ciascuno:

```powershell
cd C:\Scripts
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\Enroll-EAPAdminCert.ps1
```

La riga `Set-ExecutionPolicy` permette di eseguire script solo in questa finestra: non cambia l'impostazione del computer e smette di valere quando chiudi la finestra.

Inizia il passo 1: lo script crea la richiesta, la mostra nella finestra, la copia negli appunti ed elenca i passaggi da fare nel browser (gli stessi di [[#4. Richiedi il certificato nel browser]]). Quando premi <strong>INVIO</strong> a <strong>Premi INVIO per aprire la pagina nel browser</strong>, apre la pagina della CA e resta in attesa con <strong>Quando certnew.p7b è nella cartella Download, premi INVIO per avviare il passo 2 (per interrompere scrivi Q e premi INVIO)</strong>.

<mark style="background: #FFB86CA6;">Lascia aperta la finestra di PowerShell</mark> e passa al browser. Se devi interrompere, scrivi <strong>Q</strong> e premi <strong>INVIO</strong>, poi completa più tardi come in [[#Eseguire un passo alla volta]].

###### 4. Richiedi il certificato nel browser

Lo script mostra gli stessi passaggi. Le etichette della pagina sono in inglese perché la pagina della CA è in inglese.

1. Se il browser lo chiede, accedi con nome utente e password del <strong>dominio Publiacqua</strong>.
2. Nella pagina <strong>Submit a Certificate Request or Renewal Request</strong> fai clic nella casella <strong>Saved Request</strong> e premi <strong>Ctrl+V</strong>. Il testo incollato inizia con `-----BEGIN NEW CERTIFICATE REQUEST-----`. Se la casella resta vuota, apri <strong>request.csr</strong> sul Desktop con Blocco note, copia tutto il testo e incollalo. Lo stesso testo è mostrato anche nella finestra di PowerShell.
3. In <strong>Certificate Template</strong> scegli <strong>EAP-Admin-User</strong>.
4. Lascia vuoto <strong>Additional Attributes</strong> e fai clic su <strong>Submit</strong>.
5. Nella pagina <strong>Certificate Issued</strong> seleziona <strong>Base 64 encoded</strong> e fai clic su <strong>Download certificate chain</strong>. Viene salvato <strong>certnew.p7b</strong>, che contiene il tuo certificato e la catena della CA. Non usare <strong>Download certificate</strong>: salva <strong>certnew.cer</strong>, che non contiene la catena della CA, e lo script non lo trova.
6. Salva il file nella cartella <strong>Download</strong>, quella predefinita del browser. Se il browser chiede conferma, scegli di mantenere il file. Non aprirlo: lo installa lo script.
7. Torna nella finestra di PowerShell e premi <strong>INVIO</strong> per avviare il passo 2 (se hai avviato lo script con `-Step Step1`, esegui invece `.\Enroll-EAPAdminCert.ps1 -Step Step2`).

###### 5. Completa l'installazione

Nel passo 2 non devi fare nulla: lo script spiega cosa sta per fare, poi trova il file nella cartella Download, lo controlla, installa i certificati della CA e infine il tuo certificato.

La registrazione è completata quando lo script mostra <strong>Certificato installato nell'archivio Personale dell'utente</strong> e poi <strong>Registrazione completata</strong>. Puoi chiudere la finestra.

###### 6. Verifica il certificato

1. Premi <strong>Win+R</strong>, digita `certmgr.msc` e premi <strong>INVIO</strong>.
2. Apri <strong>Personale → Certificati</strong>. Il tuo certificato è nell'elenco, emesso dalla CA subordinata, e la sua icona mostra una piccola chiave: la chiave privata è presente.
3. Fai doppio clic sul certificato:
    - La scheda <strong>Generale</strong> indica che hai una chiave privata corrispondente al certificato.
    - Nella scheda <strong>Dettagli</strong>, il campo <strong>Utilizzo chiavi avanzato</strong> contiene <strong>Autenticazione client</strong>.
    - La scheda <strong>Percorso certificazione</strong> mostra tutta la catena fino alla CA radice e indica che il certificato è valido.

L'operazione è registrata anche in <strong>Visualizzatore eventi → Registri di Windows → Applicazione</strong>, origine <strong>EAPEnroll</strong>, ID evento <strong>1000</strong>, con utente, computer, impronta digitale del certificato, file usato e certificati della CA aggiunti agli archivi del computer.

###### Eseguire un passo alla volta

| Comando | Quando usarlo |
|---|---|
| `.\Enroll-EAPAdminCert.ps1` | Uso normale: esegue entrambi i passi e aspetta mentre usi il browser |
| `.\Enroll-EAPAdminCert.ps1 -Step Step1` | Solo per creare la richiesta e aprire la pagina della CA |
| `.\Enroll-EAPAdminCert.ps1 -Step Step2` | Per completare più tardi, dopo `-Step Step1` o dopo aver scritto <strong>Q</strong>: installa il .p7b più recente nella cartella Download |
| `.\Enroll-EAPAdminCert.ps1 -Step Step2 -CertPath "C:\percorso\certnew.p7b"` | Il file non è nella cartella Download, oppure il .p7b più recente che contiene non è quello giusto |

Per eseguire il passo 2 in una nuova finestra, apri PowerShell come in [[#2. Apri PowerShell come amministratore]] e ripeti prima i comandi `cd` e `Set-ExecutionPolicy`.

<mark style="background: #FF5582A6;">Esegui il passo 2 sullo stesso computer e con lo stesso account Windows del passo 1</mark>: la chiave privata creata nel passo 1 è salvata solo lì, e senza di essa il certificato non si può installare. Quando il passo 2 parte nella stessa finestra del passo 1, prende solo un .p7b salvato dopo l'inizio del passo 1; quando parte da solo, prende il .p7b più recente nella cartella Download, qualunque sia la sua data.

###### Risoluzione dei problemi

| Messaggio o problema | Causa | Soluzione |
|---|---|---|
| <strong>L'esecuzione di script è disabilitata nel sistema in uso</strong> (su Windows in inglese: <strong>running scripts is disabled on this system</strong>) | I criteri di esecuzione bloccano gli script | Esegui la riga `Set-ExecutionPolicy` di [[#3. Avvia lo script\|3. Avvia lo script]], poi di nuovo lo script |
| <strong>Lo script va avviato da PowerShell come amministratore</strong> | PowerShell non è in esecuzione come amministratore | Apri PowerShell come in [[#2. Apri PowerShell come amministratore\|2. Apri PowerShell come amministratore]] |
| <strong>PowerShell è stato avviato come amministratore con un altro account</strong> | UAC ha chiesto nome utente e password di un altro account, perché l'account Windows con cui hai effettuato l'accesso non è amministratore locale | Chiedi al reparto IT di rendere il tuo account Windows amministratore locale del computer, poi ricomincia da [[#2. Apri PowerShell come amministratore\|2. Apri PowerShell come amministratore]] |
| Avviso <strong>Non è stato possibile verificare con quale account è stato avviato PowerShell</strong> | Lo script non è riuscito a controllare con quale account è in esecuzione PowerShell | Continua solo se UAC non ha chiesto nome utente e password di un altro account; altrimenti chiudi la finestra e vedi la riga precedente |
| Le lettere accentate appaiono come <strong>Ã¨</strong>, <strong>Ã¹</strong> | Lo script è stato salvato senza BOM | Salvalo di nuovo con codifica <strong>UTF-8 con BOM</strong>, come in [[#1. Salva lo script\|1. Salva lo script]] |
| <strong>Non è stato possibile creare la richiesta</strong> | `certreq` non è riuscito a creare la chiave o la richiesta | Esegui di nuovo lo script; se l'errore si ripete, contatta il reparto IT indicando il messaggio mostrato |
| <strong>EAP-Admin-User</strong> non è nell'elenco <strong>Certificate Template</strong> | L'account AD con cui hai effettuato l'accesso non può registrare il template, oppure il template non è pubblicato su SubordinateCA01 | Accedi con il tuo account amministratore; controlla la [[#Domain Admin Certificate\|scheda Sicurezza]] del template e che il template sia pubblicato su SubordinateCA01 |
| <strong>non c'è un nuovo file certnew.p7b</strong> | Il file non è ancora stato scaricato, è stato scaricato con <strong>Download certificate</strong> (<strong>certnew.cer</strong>), oppure è stato salvato fuori dalla cartella Download | Se la pagina Certificate Issued è ancora aperta, fai clic su <strong>Download certificate chain</strong> ed esegui `-Step Step2`; altrimenti esegui di nuovo lo script dall'inizio. Se il .p7b è in un'altra cartella, esegui `-Step Step2 -CertPath` con il percorso completo del file |
| <strong>Il file ... non esiste</strong> | Il percorso indicato con `-CertPath` è sbagliato | In Esplora file fai clic con il tasto destro sul file e seleziona <strong>Copia come percorso</strong> (su Windows 10 tieni premuto <strong>Maiusc</strong> mentre fai clic con il tasto destro), poi esegui `-Step Step2 -CertPath` e incolla il percorso |
| <strong>non la catena della CA</strong>, <strong>dovrebbe contenere 1 certificato personale</strong>, <strong>non contiene il certificato della CA radice</strong> oppure <strong>non contiene certificati leggibili</strong> | Il file non è quello salvato con <strong>Download certificate chain</strong> (per esempio un .cer indicato con `-CertPath`), oppure il download non è stato completato | Se la pagina Certificate Issued è ancora aperta, fai clic su <strong>Download certificate chain</strong> ed esegui `-Step Step2`; altrimenti esegui di nuovo lo script dall'inizio |
| <strong>manca l'utilizzo Client Authentication</strong> | È stato scelto il template sbagliato | Esegui di nuovo lo script dall'inizio e scegli <strong>EAP-Admin-User</strong> |
| <strong>Il certificato è valido dal ... ma la data di questo PC è ...</strong> | L'orologio del computer è sbagliato | <strong>Impostazioni → Ora e lingua → Data e ora → Sincronizza ora</strong> (su Windows 10: <strong>Data/ora e lingua</strong>), poi esegui `-Step Step2` |
| <strong>certreq -accept, codice</strong> oppure <strong>installato senza la sua chiave privata</strong> | Il certificato non corrisponde a una richiesta fatta su questo computer con questo account Windows | Esegui di nuovo lo script dall'inizio, con lo stesso account, e scarica il nuovo certificato |

> [!warning] Archivio delle CA radice attendibili
> Il passo 2 aggiunge i certificati della CA che trova nel .p7b agli archivi del computer <strong>Autorità di certificazione radice attendibili</strong> e <strong>Autorità di certificazione intermedie</strong>, senza controllare a quale CA appartengono. Usa solo un file scaricato dalla pagina di SubordinateCA01 aperta dallo script. I certificati aggiunti sono elencati nell'evento del registro, quindi si possono ritrovare e rimuovere se serve.

###### Codice dello script

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
