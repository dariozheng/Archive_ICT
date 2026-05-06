---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags: [project, nac, cisco]
icon: SiCisco
iconColor: "#1BA0D7"
---
#  Scopo del documento
Il presente documento costituisce il Manuale Operativo del sistema di Network Access Control (NAC) e ha lo scopo di fornire una guida sull'utilizzo dei vari strumenti che compongono il sistema. L'obiettivo principale del NAC è aumentare la sicurezza dell'infrastruttura di rete di Publiacqua, introducendo un controllo degli accessi a livello degli switch di accesso.
#  Sistema NAC
Il sistema NAC è costituito da tre componenti:
- il **server ISE**, che gestisce e valuta le policy di sicurezza e funge da server RADIUS;
- i **dispositivi di rete di livello access** (switch), che inoltrano le richieste di autenticazione a ISE e applicano l'esito (VLAN, dACL) sulla porta del client;
- i **client**, che possono disporre di un software supplicant (ad esempio il Windows Native Supplicant) per autenticarsi presso ISE.

Il flusso di autenticazione è il seguente: il client avvia una sessione 802.1X verso lo switch; lo switch inoltra la richiesta al server ISE tramite RADIUS; ISE valuta la richiesta sulla base delle policy configurate e restituisce allo switch l'esito (Permit/Deny) insieme all'Authorization Profile da applicare, lo switch infine applicherà questa decisione chiudendo o aprendo la porta.
###  Protocolli di autenticazione
ISE e i supplicant utilizzano i protocolli di autenticazione per stabilire se concedere o meno l'accesso al client. La configurazione del protocollo lato endpoint avviene tramite Group Policy (GPO).

![[Pasted image 20260506082019.png| 200]]

I protocolli utilizzati in questo deployment sono riepilogati nella tabella seguente:

| Protocollo    | Scenario d'uso                                          | Credenziali utilizzate        | GPO di riferimento |
| ------------- | ------------------------------------------------------- | ----------------------------- | ------------------ |
| TEAP          | Utenti di dominio (default)                             | Cert. macchina + cert. utente | `C_PC-NAC-TEAP`    |
| PEAP-MSCHAPv2 | Utenti di dominio, consulenti esterni con account admin | Credenziali di dominio        | `C_PC-NAC-PEAP`    |
| PEAP-EAP-TLS  | Consulenti esterni con computer non in dominio          | Certificato utente            | Non neccessario    |
| EAP-TLS       | Permettere l'accesso in RDP                             | Certificato macchina          | `C_PC_NAC-EAP-TLS` |

Le sezioni seguenti descrivono nel dettaglio ciascun protocollo.
####  TEAP
TEAP è il protocollo di default per gli utenti Publiacqua in dominio. Utilizza sia il certificato macchina sia il certificato utente; entrambi sono distribuiti automaticamente tramite Group Policy.
Con TEAP sono previsti due scenari di autenticazione, a cui corrispondono due distinti Authorization Profile su ISE:
- **Solo certificato macchina valido (Pre-Auth)** — tipico della fase pre-logon, quando l'utente non ha ancora effettuato il logon e il certificato utente non è quindi disponibile, oppure del primo accesso di un nuovo utente su un computer di dominio, quando il certificato utente non è ancora presente in profilo. 
  In questi casi viene concesso un accesso Pre-Auth limitato, che consente la comunicazione con Domain Controller e Certification Authority per permettere il logon di dominio e l'enrollment del certificato utente.
- **Certificato macchina e certificato utente entrambi validi** — l'utente ottiene l'accesso alla rete con il livello di autorizzazione associato al proprio profilo.
####  PEAP-MSCHAPv2
PEAP-MSCHAPv2 utilizza le credenziali di dominio (username e password) per l'autenticazione alla rete Publiacqua.
Viene impiegato nei seguenti casi:
- utenti di dominio che, per un qualsiasi motivo, non possono utilizzare TEAP;
- utenti non di dominio, ad esempio consulenti esterni con privilegi amministrativi.
#### PEAP-EAP-TLS 
Il protocollo è utilizzato per l'autenticazione di consulenti esterni con computer non appartenenti al dominio Publiacqua, mediante certificato utente rilasciato ad hoc dalla SubCA di Publiacqua.
#### EAP-TLS
In questo deployment EAP-TLS utilizza il certificato macchina per autenticare l'endpoint. È impiegato sui computer connessi alla porta switch configurata sulla VLAN 802, per abilitare l'accesso RDP.

# Accesso al portale GUI ISE

Nodo Primario = [https://cisco-ise1.publiacqua.it](https://cisco-ise1.publiacqua.it)
Nodo Secondario = [https://pba-ise02.publiacqua.it](https://pba-ise02.publiacqua.it)

L’accesso alla GUI ISE avviene con credenziali nominali integrate con Active Directory Publiacqua. Le attività di operation sono lettura Live Logs e Live Sessions, esecuzione CoA (Session Reauthentication e Port Bounce), gestione di Endpoint Identity Group per mettere computer in Blacklist/Whitelist. 

Il nodo secondario viene solitamente tenuto spento, viene acceso quando il nodo primario è down.
# Operazioni
Le operazioni a primo livello che possono essere eseguiti sono: 
- Mettere un computer in Blacklist
- Attivare l'accesso MAB (Accesso per indirizzo MAC)
- Sbloccare un utente che è stato rifiutato troppe volte
- Live Logs e Live Sessions
- Fare fare la re-autenticazione all'utente
- Onboarding di nuovi PC e Utenze 
- Guest Portal 
## Utente in Blacklist
Per inserire un computer in blacklist, andare nella sezione illustrata nell'immagine ed inserire l'indirizzo MAC da bloccare. 
Il gruppo blacklist si chiama appunto <strong>Blacklist</strong>. 

![[Pasted image 20260506142431.png]]

![[Pasted image 20260506142459.png]]
# Accesso MAB
Per fornire un'autorizzazioni speciali, ed utilizzare l'accesso per indirizzi MAC, bisogna inserire il PC dell'utente sul gruppo whitelist designato: MAB_Whitelist.

Ogni volta che viene aggiunto un computer sulla whitelist, va segnato sul file <mark style="background: #FF5582A6;">Excel</mark>.

![[Pasted image 20260506142539.png]]
# Live Logs

![[Pasted image 20260506152434.png]]

In questa lista è possibile trovare vari filtri da usare per facilitare l'operazione di monitoring: 
- Authentication Policy (Wired o Wireless)
- AD username 
- Mac Address 
- Location 
- Authorization Profile 
- IP address
## Detailed Report
Cliccando sull’icona della lente in una riga di Live Logs si apre il Detailed Report. 

![[Screenshot 2026-05-06 at 15.39.20.png]]
## Esempi Visivi 
## TEAP User and machine both succeeded - Authorization Result Correct
In questo esempio vediamo che l'autenticazione è andato a buon fine la Authorization Result è la VLAN corretta. 
Sono presenti entrambi account, account utente e account computer, con i loro certificati, tutto verificato. 
L'Authorization Result viene data dal gruppo AD che appartiene l'utente. In questo caso <strong>InfrastructureAdmin</strong> prevale sul gruppo AD <strong>Utenti_Publiacqua</strong>, che è il gruppo di default.
Essendo un autenticazione con i certificati, ci sono i dettagli sui due certificati che ha fornito i due client. 

Ed infine ci sono i vari attributi come Location, Device type, Device Profile ecc.

![[Pasted image 20260506155921.png]]

## TEAP User and machine both succeeded - Authorization Result Redirect_Guest_Wired
![[Screenshot 2026-05-06 at 15-54-15 Cisco Identity Services Engine.png]]
Questo è un Report quasi completamente simile al report precedente, solo che l'Authorization Result è Redirect_Guest_Wired. Questo Result viene fornita a tutti client che non sono stati autorizzati dal server ISE. 
In questo caso l'utente non è stato autorizzato per che il certificato computer è presente sul computer locale e sulla SubCA02 ma non è presente sulla AD. 

![[Pasted image 20260506161129.png]]
# Tabella Step ID sugli errori negli report di ISE

| Step ID | Description                                                                                                                                                     | Errore |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 24363   | Client certificate does not match AD account certificate Il certificato è presente sul PC locale dell'utente e sulla SubCA, ma non è presente sull'account AD o |        |
|         |                                                                                                                                                                 |        |
