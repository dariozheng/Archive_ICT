---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags: [project, nac, cisco]
icon: SiCisco
iconColor: "#1BA0D7"
---
# 1. Scopo del documento
Il presente documento costituisce il Manuale Operativo del sistema di Network Access Control (NAC) e ha lo scopo di fornire una guida sull'utilizzo dei vari strumenti che compongono il sistema. L'obiettivo principale del NAC è aumentare la sicurezza dell'infrastruttura di rete di Publiacqua, introducendo un controllo degli accessi a livello degli switch di accesso.
# 2. Sistema NAC
Il sistema NAC è costituito da tre componenti:
- il **server ISE**, che gestisce e valuta le policy di sicurezza e funge da server RADIUS;
- i **dispositivi di rete di livello access** (switch), che inoltrano le richieste di autenticazione a ISE e applicano l'esito (VLAN, dACL) sulla porta del client;
- i **client**, che possono disporre di un software supplicant (ad esempio il Windows Native Supplicant) per autenticarsi presso ISE.

Il flusso di autenticazione è il seguente: il client avvia una sessione 802.1X verso lo switch; lo switch inoltra la richiesta al server ISE tramite RADIUS; ISE valuta la richiesta sulla base delle policy configurate e restituisce allo switch l'esito (Permit/Deny) insieme all'Authorization Profile da applicare, lo switch infine applicherà questa decisione chiudendo o aprendo la porta.
### 2.1 Protocolli di autenticazione
ISE e i supplicant utilizzano i protocolli di autenticazione per stabilire se concedere o meno l'accesso al client. La configurazione del protocollo lato endpoint avviene tramite Group Policy (GPO).

I protocolli utilizzati in questo deployment sono riepilogati nella tabella seguente:

| Protocollo    | Scenario d'uso                                          | Credenziali utilizzate        | GPO di riferimento |
| ------------- | ------------------------------------------------------- | ----------------------------- | ------------------ |
| TEAP          | Utenti di dominio (default)                             | Cert. macchina + cert. utente | `C_PC-NAC-TEAP`    |
| PEAP-MSCHAPv2 | Utenti di dominio, consulenti esterni con account admin | Credenziali di dominio        | `C_PC-NAC-PEAP`    |
| PEAP-EAP-TLS  | Consulenti esterni con computer non in dominio          | Certificato utente            | Non neccessario    |
| EAP-TLS       | Permettere l'accesso in RDP                             | Certificato macchina          | `C_PC_NAC-EAP-TLS` |

Le sezioni seguenti descrivono nel dettaglio ciascun protocollo.
#### 2.1.1 TEAP
TEAP è il protocollo di default per gli utenti Publiacqua in dominio. Utilizza sia il certificato macchina sia il certificato utente; entrambi sono distribuiti automaticamente tramite Group Policy.
Con TEAP sono previsti due scenari di autenticazione, a cui corrispondono due distinti Authorization Profile su ISE:
- **Solo certificato macchina valido (Pre-Auth)** — tipico della fase pre-logon, quando l'utente non ha ancora effettuato il logon e il certificato utente non è quindi disponibile, oppure del primo accesso di un nuovo utente su un computer di dominio, quando il certificato utente non è ancora presente in profilo. 
  In questi casi viene concesso un accesso Pre-Auth limitato, che consente la comunicazione con Domain Controller e Certification Authority per permettere il logon di dominio e l'enrollment del certificato utente.
- **Certificato macchina e certificato utente entrambi validi** — l'utente ottiene l'accesso alla rete con il livello di autorizzazione associato al proprio profilo.
#### 2.1.2 PEAP-MSCHAPv2
PEAP-MSCHAPv2 utilizza le credenziali di dominio (username e password) per l'autenticazione alla rete Publiacqua.
Viene impiegato nei seguenti casi:
- utenti di dominio che, per un qualsiasi motivo, non possono utilizzare TEAP;
- utenti non di dominio, ad esempio consulenti esterni con privilegi amministrativi.
#### 2.1.3 PEAP-EAP-TLS 
Il protocollo è utilizzato per l'autenticazione di consulenti esterni con computer non appartenenti al dominio Publiacqua, mediante certificato utente rilasciato ad hoc dalla SubCA di Publiacqua.
#### 2.1.4 EAP-TLS
In questo deployment EAP-TLS utilizza il certificato macchina per autenticare l'endpoint. È impiegato sui computer connessi alla porta switch configurata sulla VLAN 802, per abilitare l'accesso RDP.