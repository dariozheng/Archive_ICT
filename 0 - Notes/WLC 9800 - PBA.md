---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[WLAN]]"
tags:
icon: SiCisco
iconColor:
---
Il Wireless LAN Controller (WLC) è il punto di controllo centrale della rete wireless: gli AP si registrano al controller tramite CAPWAP e ne ricevono la configurazione.

## Accesso

L'accesso al portale GUI del WLC è eseguito con le credenziali RADIUS tramite il portale [https://pba-wlc01.publiacqua.it/webui/](https://pba-wlc01.publiacqua.it/webui/).

Il WLC ha l'indirizzo 10.140.1.10.

![[Pasted image 20260630121117.png]]

![[Pasted image 20260630121117.png]]

Anche l'accesso SSH è eseguito con le credenziali RADIUS. L'autenticazione degli accessi admin è definita dalle [[#Method List|method list]] di login; l'eventuale utente locale di fallback per quando i server RADIUS non sono raggiungibili si trova su password manager.

## Configurazione Iniziale

Le configurazioni che devono essere fatte prima di creare le WLAN e prima di joinare gli AP sono le configurazioni base come hostname, VLAN, SSH, NTP, DNS, country code e la Wireless Management Interface. 

```cisco
hostname pba-wlc01
ip domain name publiacqua.it
!
vlan <wmi-vlan-id>
 name <wmi-vlan-name>
!
interface TenGigabitEthernet0/0/<n>
 description Uplink
 switchport mode trunk
 switchport trunk allowed vlan <wmi-vlan-id>
!
interface Vlan<wmi-vlan-id>
 description Wireless Management Interface
 ip address 10.140.1.10 <netmask>
!
wireless management interface Vlan<wmi-vlan-id>
!
ip name-server <dns-1> <dns-2>
ntp server <ntp-1>
!
ip ssh version 2
line vty 0 15
 transport input ssh
```

### Wireless Management Interface

![[Pasted image 20260630145410.png]]

La Wireless Management Interface (WMI) è l'interfaccia che termina i tunnel CAPWAP degli AP ed è la source interface per il RADIUS, oltre a essere l'indirizzo di management della macchina stessa (10.140.1.10).

### Country Code

Le radio non sono attive finché non è configurato il corretto country code. Il comando definisce la lista globale dei country code ammessi sul WLC:

```cisco
ap country IT
```

Il country code viene poi assegnato agli AP tramite l'[[#AP Join Profile]]: il paese selezionato nel profilo deve essere presente anche in questa lista globale, altrimenti viene ignorato. 

## RADIUS e AAA

### RADIUS Servers

Comandi CLI per definire i server RADIUS:

```cisco
radius server RADIUS_SERVER_DAY0_1
 address ipv4 10.140.2.27 auth-port 1812 acct-port 1813
 timeout 5
 retransmit 3
 automate-tester username probe-user ignore-acct-port probe-on
 key <radius-key>
!
radius server PBA-ISE-01
 address ipv4 10.140.2.31 auth-port 1812 acct-port 1813
 timeout 5
 retransmit 3
 automate-tester username probe-user ignore-acct-port probe-on
 key <radius-key>
!
radius-server dead-criteria time 5 tries 3
radius-server deadtime 15
```

Configurazione GUI

![[Pasted image 20260630121733.png]]

#### CoA

Change of Authorization permette a un server NAC di cambiare l'autorizzazione di una sessione già attiva: con una CoA è possibile disconnettere la sessione, forzare una riautenticazione o applicare nuovi attributi (VLAN, ACL, redirect URL). È il meccanismo che chiude il flusso guest di [[#PBA-Guest]]: dopo il login sul portale, ISE invia al WLC una CoA di riautenticazione.

```cisco
aaa server radius dynamic-author
 client 10.140.2.27 server-key <coa-key-day0>
 client 10.140.2.31 server-key <coa-key-ise>
```

Solo gli IP elencati come client possono inviare CoA al WLC, e la server-key deve combaciare con quella configurata lato server.

### Server Groups

![[Pasted image 20260630153701.png]]

I RADIUS Server Group raggruppano i server definiti sopra e vengono poi richiamati dalle method list. I gruppi sono due: ISE (contiene PBA-ISE-01) e RADIUS_SERVER_GROUP_DAY0 (contiene RADIUS_SERVER_DAY0_1).

### Method List

![[Pasted image 20260630154036.png]]

Le method list corrispondono ai comandi:

```cisco
aaa authentication login default group RADIUS_SERVER_GROUP_DAY0 group ISE

aaa authentication login authentication_login_day0 group RADIUS_SERVER_GROUP_DAY0 local

aaa authentication login ISE group ISE

aaa authentication dot1x authentication_dot1x_day0 group RADIUS_SERVER_GROUP_DAY0

aaa authentication dot1x ML-ISE group ISE

aaa authorization exec default group ISE group RADIUS_SERVER_GROUP_DAY0

aaa authorization network default local

aaa authorization network mac_filtering group ISE

aaa authorization credential-download wcm_loc_serv_cert local

aaa accounting identity default start-stop group ISE
```

Le liste più rilevanti:

| Method list                       | Tipo                  | Uso                                                                                                           |
| --------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------- |
| default                           | authentication login  | Autentica gli accessi admin GUI/SSH descritti in [[#Accesso]]: prima il gruppo day0, poi ISE.                 |
| authentication_login_day0         | authentication login  | Come la default ma con fallback sulle credenziali locali; su quali linee sia applicata non è documentato qui. |
| ML-ISE, authentication_dot1x_day0 | authentication dot1x  | Authentication List per le WLAN 802.1X come [[#PBA-Client]].                                                  |
| mac_filtering                     | authorization network | Authorization List del MAC filtering della WLAN guest.                                                        |
| default                           | authorization exec    | Livello di privilegio della shell per gli admin: prima ISE, poi il gruppo day0.                               |
| default                           | accounting identity   | Invia a ISE gli accounting start/stop delle sessioni client, necessari a ISE per tracciare le sessioni.       |

#### Anatomia e ordine dei metodi

_Il fallback tra metodi scatta solo se i server sono irraggiungibili, mai su un Access-Reject._

La sintassi generale è `aaa <funzione> <sottotipo> {default|nome} metodo1 [metodo2 ...]`: le funzioni sono authentication, authorization e accounting, il sottotipo indica il contesto (login, dot1x, exec, network, identity) e i metodi sono server group, `local` o `none`. La lista `default` si applica automaticamente ovunque non venga richiamata una lista con nome.

I metodi vengono percorsi in ordine, ma il passaggio al successivo avviene solo se il metodo corrente non risponde — cioè se tutti i server del gruppo sono marcati dead o irraggiungibili. Un Access-Reject è una risposta valida: la lista si ferma lì e l'accesso viene negato, senza provare i metodi dopo. Quindi il `local` in coda a authentication_login_day0 non è una password alternativa da usare quando quella RADIUS viene rifiutata: entra in gioco esclusivamente quando i server RADIUS sono giù.

Quando un server è considerato dead lo decidono i comandi già visti in [[#RADIUS Servers]]: con dead-criteria un server che non risponde a 3 tentativi entro 5 secondi viene marcato dead, con deadtime resta fuori rotazione per 15 minuti, e l'automate-tester lo sonda con autenticazioni fittizie (probe-user) così lo stato torna alive appena il server risponde, anche in assenza di traffico reale.

> [!warning] La lista default di authentication login non ha `local` in coda: se tutti i server RADIUS di entrambi i gruppi risultano dead, GUI e SSH restano chiusi fuori. Il fallback locale esiste solo in authentication_login_day0, quindi va verificato su quale linea è applicata (tipicamente la console) e che l'utente locale esista davvero.

#### Dove vengono richiamate

_Una method list non fa nulla finché un profilo, una linea o un processo non la richiama._

I punti di aggancio sul 9800 sono quattro: le WLAN (tab Security dei [[#WLAN Profiles]]), i policy profile (tab Advanced), le linee e i processi di management, e i processi interni che usano le liste default in modo implicito.

```
WLAN Profile > Security
├─ AAA > Authentication List ──── ML-ISE ─────────── (dot1x)
│                                  └─ PBA-Client: EAP 802.1X
└─ Layer2 > Authorization List ── mac_filtering ──── (network)
                                   └─ PBA-Guest: MAB

Policy Profile > Advanced
└─ Accounting List ────────────── default ────────── (identity)

Management
├─ GUI/SSH login ──────────────── default ────────── (login)
├─ privilegio shell ───────────── default ────────── (exec)
└─ console (da verificare) ────── authentication_login_day0
```

|Method list|Dove viene richiamata|Cosa fa|
|---|---|---|
|ML-ISE|[[#PBA-Client]] > Security > AAA > Authentication List|Autentica l'EAP 802.1X dei client Wi-Fi: il WLC fa da authenticator e inoltra le richieste a ISE.|
|authentication_dot1x_day0|Da verificare se qualche WLAN la richiami|Gemella day-0 di ML-ISE, ma verso il gruppo RADIUS_SERVER_GROUP_DAY0.|
|mac_filtering|[[#PBA-Guest]] > Security > Layer2 > Authorization List|La MAB della guest: sul 9800 il MAC filtering è una transazione di authorization network, per questo la lista è di tipo network e in GUI si chiama Authorization List.|
|default (login)|Implicita su VTY e HTTP|Gli accessi admin GUI/SSH di [[#Accesso]].|
|authentication_login_day0|Da verificare (tipicamente line console)|Login admin con fallback sulle credenziali locali.|
|default (exec)|Implicita dopo il login admin|Chiede a ISE il privilege level della shell; ISE risponde con il cisco-av-pair shell:priv-lvl=15.|
|default (identity)|[[#Policy Profiles]] > Advanced > Accounting List|Start, interim e stop delle sessioni client verso ISE.|
|default (network, local)|Processi interni|Autorizzazioni network senza RADIUS; creata dal wizard day-0.|
|wcm_loc_serv_cert|Processi interni (credential-download)|Lista generata in day-0 per il download locale di credenziali e certificati (Local EAP, LWA); estranea al flusso ISE.|

> [!note] Le WLAN 802.1X richiedono anche il toggle globale `dot1x system-auth-control`, assente dagli estratti sopra: verificare che sia presente nella running-config.

#### Verifica

```cisco
show aaa method-lists all
show aaa servers
show run | section ^aaa|^radius|^line
```

## AP Join Process

In questo deployment gli AP usano la <strong>DHCP option 43</strong> per ottenere l'indirizzo della [[#Wireless Management Interface]] per joinare il WLC.

Reference: https://www.cisco.com/c/en/us/support/docs/wireless-mobility/wireless-lan-wlan/97066-dhcp-option-43-00.html

![[Pasted image 20260701111850.png]]

La DHCP option 43 ha tre formati: f1 è il classico discovery del WLC, f2 serve a convertire gli AP da EWC a modalità CAPWAP, f3 (fast offline migration) commuta gli AP Wi-Fi 7 tra modalità Catalyst e Meraki aggiungendo un byte di mode dopo gli IP. Noi usiamo <strong>f1</strong>.

```
One IP (10.140.1.10):
  f1  04  0A 8C 01 0A
 type  len  10.140.1.10
= 0xf1040A8C010A

CONVERSIONE BYTE: 0A=10, 8C=140, 01=1, 0A=10

Two IPs (10.128.10.8 and .9) — just append each IP's 4 bytes:
  f1 08  0a 80 0a 08  0a 80 0a 09
= 0xf1080a800a080a800a09
```

<strong>0x</strong> significa che la stringa è in <strong>esadecimale</strong> e non in <strong>decimale</strong>.

<strong>04</strong> o <strong>08</strong> indicano la lunghezza (Length) del campo value: 04 vale 4 byte cioè un indirizzo IP, 08 vale 8 byte cioè due indirizzi IP.

<strong>0A8C010A</strong> è l'indirizzo IP in esadecimale; se sono presenti due indirizzi, il secondo va accodato subito dopo il primo.

## Tags e Profiles

Il WLC non configura direttamente gli AP: costruisce dei profili riutilizzabili, raggruppa questi profili in tag e assegna un tag per tipo (Policy tag, Site tag, RF tag) a ogni AP. Le configurazioni sono date da questi tag e profili.

![[wlc9800-tag-architecture.png]]

### Profiles

_Containers for the actual settings. Each profile type is related to one field of the network._

|Profile|Field|Configured in|
|---|---|---|
|WLAN profile|SSID e L2 security|[[#WLAN Profiles]]|
|Policy profile|What VLAN, QoS, ACLs and switching a client gets after it joins|[[#Policy Profiles]]|
|AP join profile|How the AP itself behaves — CAPWAP timers, management, SSH, syslog|[[#AP Join Profile]]|
|Flex profile|VLAN mapping and local-switching behavior for FlexConnect|[[#Flex Profile]]|
|RF profile|Data rates, channels and power per band|[[#RF Profiles]]|

### Tags

#### Site Tag

Il Site Tag associa a ogni AP il suo AP Join Profile e decide in che <strong>switching mode</strong> configurare gli AP:

- Local Mode (Central Switching): gli AP inviano il traffico dati verso il WLC tramite il tunnel CAPWAP, e il WLC lo riversa in L2 sulla VLAN contenuta nel [[#Policy Profiles|policy profile]]. In questo mode tutti i siti remoti devono riuscire a raggiungere il WLC, che si trova in VM90.
- FlexConnect (Local Switching): gli AP portano il traffico direttamente sulla VLAN locale e il WLC viene usato solo per il control plane. La VLAN viene fornita dal [[#Flex Profile]] richiamato dal site tag.

Nel deployment attuale lo switching mode è FlexConnect (Local Switching): deselezionando <strong>Enable Local Site</strong> il site tag passa in FlexConnect e compare la selezione della <strong>Flex Profile</strong>.

![[Pasted image 20260701120051.png]]

##### AP Join Profile

L'AP join profile configura il <strong>country code</strong> degli AP, il <strong>NTP server</strong>, il <strong>WLC secondario</strong>, le credenziali admin locali, se <strong>SSH verso l'AP</strong> è permesso, dove inviare i syslog, i CAPWAP timers, la crittografia DTLS del CAPWAP data path e altro.

![[Pasted image 20260701114537.png]]

![[Pasted image 20260701114557.png]]

![[Pasted image 20260701114902.png]]

##### Flex Profile

L'opzione Flex Profile viene mostrata solo se <strong>Enable Local Site</strong> è disattivo. Nel Flex Profile è possibile configurare le VLAN (mapping nome/ID), la Native VLAN, l'autenticazione locale e le Policy ACL.

![[Pasted image 20260701115751.png]]

![[Pasted image 20260701122312.png]]

![[Pasted image 20260701122343.png]]

In Policy ACL viene configurata l'access list GUEST_REDIRECT, la redirect ACL della Guest Wifi: definisce quale traffico del client viene intercettato e reindirizzato verso il portale (permit su HTTP/HTTPS) e quale invece deve passare liberamente (deny su DHCP, DNS e traffico verso i nodi ISE). È la stessa logica dell'ACL lato switch [[PBA - NAC - Network Access Devices#Redirect ACL — `ACL_GUEST_REDIRECT`|ACL_GUEST_REDIRECT]]; il contenuto esatto dell'ACL definita sul WLC non è ancora documentato qui.

Il che significa che, a differenza del central switching dove gli AP usano le ACL dentro il WLC, in local switching le ACL sono presenti localmente, inserite nell'AP al momento del join a seconda della configurazione di Policy ACL.

La selezione <strong>Central Web Auth</strong> marca l'ACL come redirect ACL per la CWA e viene usata per attivare la HTTP/HTTPS interception engine sull'AP.

![[Pasted image 20260701123009.png]]

Il comportamento della redirect ACL sul 9800: le entry permit indicano il traffico da intercettare e redirigere, le entry deny il traffico che attraversa senza redirect, e tutto ciò che non matcha nulla resta bloccato dallo stato WEBAUTH_REQD della sessione finché la CWA non si conclude. Questa è la struttura canonica, da confrontare con quella reale (`show ip access-lists GUEST_REDIRECT`):

```cisco
ip access-list extended GUEST_REDIRECT
 deny   udp any any eq bootps
 deny   udp any any eq bootpc
 deny   udp any any eq domain
 deny   ip any host 10.140.2.31
 deny   ip host 10.140.2.31 any
 permit tcp any any eq www
 permit tcp any any eq 443
```

#### Policy Tag

![[Pasted image 20260701154141.png]]

Il Policy Tag mappa ogni WLAN Profile con il suo Policy Profile: la coppia stabilisce quali SSID trasmette l'AP e che trattamento ricevono i client di ciascuna.

##### WLAN Profiles

I WLAN Profile configurano l'SSID e la sicurezza L2; ogni profilo ha un nome, un SSID e una WLAN ID.

###### PBA-Client

![[Pasted image 20260701155819.png]]

Nella sezione Security, in Layer2 è configurato che come protocolli di sicurezza si usano WPA2 e WPA3 con la crittografia AES.

Per l'autenticazione viene usato 802.1X o 802.1X-SHA256, il che significa che l'utente non ha una password condivisa ma si autentica verso il server AAA configurato nella Authentication List — il server ISE in questo caso, tramite una delle method list dot1x definite in [[#Method List]].

![[Pasted image 20260701160528.png]]

![[Pasted image 20260701162426.png]]

Le impostazioni PMF (richieste da WPA3) e l'eventuale Fast Transition 802.11r non sono ancora documentate qui.

Il vincolo tecnico da tenere presente quando verranno documentate: WPA3 richiede le Protected Management Frames (802.11w), quindi su un SSID misto WPA2+WPA3 l'impostazione coerente è PMF Optional — i client WPA3 le negoziano sempre, quelli WPA2 privi di supporto si associano comunque. PMF Required è praticabile solo rinunciando ai client WPA2 senza 802.11w. L'AKM 802.1X-SHA256 visto sopra è proprio la variante usata dai client che negoziano PMF.

Per il Fast Transition le opzioni del 9800 sono Disabled, Enabled e Adaptive: con FT attivo il roaming tra AP riusa le chiavi già derivate ed evita la full authentication EAP a ogni passaggio, cosa che pesa soprattutto su voce e client in movimento; Adaptive è la variante Cisco che non annuncia l'11r come obbligatorio nei beacon e lo concede solo ai client che lo negoziano esplicitamente.

###### PBA-Guest

Per la WLAN guest invece non c'è nessun controllo Layer2 tranne il MAC filtering: il MAC address del client viene inviato come richiesta MAB al server indicato nella Authorization List, cioè la method list mac_filtering che punta a ISE.

Il MAC non è censito tra gli endpoint autorizzati, quindi la MAB "fallisce", ma ISE è configurato per proseguire comunque: la authorization policy risponde con un Access-Accept che contiene la redirect URL verso il guest portal e il nome della redirect ACL da applicare (non un DenyAccess: con un reject il client non otterrebbe rete e non vedrebbe mai il portale). L'AP intercetta l'HTTP/HTTPS del client con la Policy ACL del Flex Profile e lo dirotta sul portale; dopo il login ISE invia una [[#CoA]] di riautenticazione e alla seconda MAB il client, ormai in Guest Flow, riceve l'accesso pieno.

Il profilo di authorization equivalente lato wired è [[PBA - NAC - ISE Server#Redirect_Guest_Wired|Redirect_Guest_Wired]]; il profilo usato per il wireless non è ancora documentato, e il nome dell'ACL che ISE invia in url-redirect-acl deve combaciare esattamente con quello dell'ACL definita sul WLC (GUEST_REDIRECT).

![[Pasted image 20260701162626.png]]

Web Policy serve per attivare la Local Web Authentication: dato che usiamo la CWA è disattivata e le configurazioni non sono attive.

Il tab AAA non viene usato per le guest WLAN: l'Authorization List del MAC filtering si imposta nel tab Layer2.

![[Pasted image 20260701164609.png]]

##### Policy Profiles

Il Policy Profile definisce cosa succede al client dopo l'associazione: la VLAN di destinazione, QoS, ACL, i timeout di sessione e il tipo di switching e autenticazione (central o local) per quella WLAN. Per il funzionamento con ISE sono importanti tre impostazioni:

- AAA Override: permette al WLC di applicare gli attributi restituiti da ISE (VLAN, ACL, redirect URL); senza, gli attributi dell'Access-Accept vengono ignorati.
- NAC State (RADIUS NAC): abilita la CWA e le CoA sulla WLAN; indispensabile per il flusso di PBA-Guest.
- Accounting List: invia gli accounting a ISE.

I policy profile effettivi di PBA-Client e PBA-Guest (nomi, VLAN assegnate, flag attivi) non sono ancora documentati qui — da integrare con gli screenshot.

###### General

Oltre a nome e stato del profilo, il tab General contiene le quattro spunte che definiscono il modello di traffico della WLAN, cioè cosa resta centrale sul WLC e cosa scende sull'AP:

|Impostazione|Cosa controlla|Valore atteso qui|
|---|---|---|
|Central Switching|Se il traffico dati viaggia nel CAPWAP fino al WLC o esce in locale dall'AP|Disattivo|
|Central Authentication|Se 802.1X e MAB sono gestiti dal WLC (RADIUS client verso ISE) o dall'AP|Attivo|
|Central DHCP|Se il DHCP dei client transita dal WLC|Disattivo|
|Central Association|Se l'associazione dei client è gestita centralmente|Disattivo|

La combinazione in tabella è quella canonica del FlexConnect local switching con CWA: l'autenticazione resta centrale perché è il WLC a parlare con ISE e a ricevere le [[#CoA]], mentre dati, DHCP e associazione restano sull'AP. Se Central Authentication fosse disattivo, 802.1X e MAB passerebbero alla local authentication del [[#Flex Profile]] e il flusso guest descritto in [[#PBA-Guest]] non funzionerebbe così com'è. I valori reali sono da confermare con gli screenshot.

###### Access Policies

Qui si assegna la VLAN di destinazione dei client (per nome o ID) ed eventuali ACL statiche della WLAN. In local switching il valore deve corrispondere a una VLAN presente nel mapping del [[#Flex Profile]], perché è l'AP a taggare il traffico: se il nome non combacia con il mapping il client finisce su una VLAN diversa da quella attesa o resta senza rete. Lo stesso vincolo vale per la VLAN restituita da ISE con l'AAA Override: l'override può assegnare solo VLAN già mappate nel flex profile, il WLC non può crearle sull'AP al volo.

Le ACL impostate qui (WLAN ACL) non vanno confuse con la redirect ACL della CWA: quella arriva da ISE come nome dentro url-redirect-acl e vive nella Policy ACL del [[#Flex Profile]].

###### Advanced

Il tab Advanced concentra le impostazioni che legano la WLAN a ISE; conviene guardarle una per una.

AAA Override autorizza il WLC ad applicare gli attributi dell'Access-Accept al posto della configurazione statica del profilo. Gli attributi rilevanti per questo deployment:

|Attributo|Effetto|
|---|---|
|Tunnel-Private-Group-ID (con Tunnel-Type e Tunnel-Medium-Type)|VLAN override: sposta il client su una VLAN diversa da quella del tab Access Policies.|
|cisco-av-pair url-redirect|URL del guest portal verso cui dirottare il client.|
|cisco-av-pair url-redirect-acl|Nome della redirect ACL da attivare (GUEST_REDIRECT).|
|Airespace-ACL-Name|ACL con nome da applicare alla sessione come filtro.|
|Session-Timeout|Durata della sessione decisa da ISE al posto del valore del profilo.|

Senza AAA Override tutti questi attributi vengono ignorati: niente redirect, niente VLAN dinamiche.

NAC State (con NAC Type su ISE NAC) abilita il RADIUS NAC sulla WLAN: permette al WLC di gestire lo stato intermedio della CWA — client autorizzato ma in redirect — e di accettare le [[#CoA]] per le sessioni di quella WLAN. Senza, la CoA di riautenticazione che ISE invia dopo il login sul portale viene ignorata e il guest resta intrappolato nel redirect.

Accounting List richiama la lista default di accounting identity descritta in [[#Method List]]. Non è cosmetica: con gli start, gli interim e gli stop ISE popola e chiude le Live Sessions e impara l'indirizzo IP del client, che serve al portale per agganciare la sessione giusta; e una CoA può essere indirizzata solo a una sessione che ISE conosce.

Session Timeout e Idle Timeout definiscono la durata massima della sessione e l'inattività tollerata prima della disconnessione; con AAA Override attivo il session timeout può essere sovrascritto da ISE, ed è il meccanismo tipico con cui si limita la durata dell'accesso guest.

> [!note] Le altre voci del tab vanno toccate con cautela in local switching: IPv4 DHCP Required, per esempio, scarta i client con indirizzo statico e va valutata solo con i profili reali davanti.

#### RF Tag

Il RF Tag associa a ogni AP i RF Profile da usare per banda (2.4 GHz, 5 GHz ed eventualmente 6 GHz).

##### RF Profiles

Nei RF Profile si configurano i data rate, i canali (DCA), le potenze (TPC) e le altre impostazioni radio per banda. Quali RF tag e RF profile siano in uso nel deployment, o se si usi il default-rf-tag, non è ancora documentato qui.

In generale è qui che si interviene per banda su tre leve: i data rate (disattivare i rate legacy del 2.4 GHz come 1–11 Mb/s e alzare il primo rate mandatory riduce l'airtime sprecato), il DCA (limitare i canali utilizzabili e, sul 5 GHz, la larghezza di canale) e il TPC (fissare potenza minima e massima per contenere celle troppo grandi o troppo deboli). Finché non viene creato e assegnato un RF tag dedicato, gli AP restano sul default-rf-tag con i default-rf-profile per banda.

### Assegnazione dei Tag agli AP

I tag possono essere assegnati agli AP in tre modi: staticamente per singolo AP, tramite filtri con regex sul nome dell'AP, oppure lasciando i default tag (default-policy-tag, default-site-tag, default-rf-tag). Il metodo usato in questo deployment e la naming convention degli AP non sono ancora documentati qui.

I tre meccanismi in dettaglio, in ordine di precedenza:

- Assegnazione statica per singolo AP, da GUI o da exec:

```cisco
ap name <nome-ap> policy-tag <tag>
ap name <nome-ap> site-tag <tag>
ap name <nome-ap> rf-tag <tag>
```

- Filtri con regex sul nome dell'AP, utili quando la naming convention codifica sito o piano:

```cisco
ap filter name <nome-filtro>
 ap name-regex ^PBA-<sito>-.*
 tag policy <policy-tag>
 tag site <site-tag>
 tag rf <rf-tag>
!
ap filter priority <0-1023> filter-name <nome-filtro>
```

- In assenza di assegnazione statica e di filtri che matchano, l'AP riceve i tre default tag.

Lo stato corrente si legge con `show ap tag summary`, che mostra per ogni AP i tre tag assegnati e la sorgente (Static, Filter, Default).

> [!warning] Cambiare i tag di un AP non è un'operazione trasparente: alla riassegnazione (in particolare del site tag) l'AP riavvia il CAPWAP e i client vengono disconnessi per qualche istante. Con `ap tag persistency enable` i tag vengono salvati sull'AP e sopravvivono ai rejoin.

## Da recuperare dal sistema live

_La coda delle verifiche: tutto ciò che nelle sezioni sopra è marcato come non ancora documentato._

- Modello esatto e versione IOS-XE (`show version`).
- Utente locale di fallback e linee su cui è applicata authentication_login_day0 (`show run | section ^line`) — [[#Accesso]], [[#Method List]].
- Blocco reale della configurazione base: VLAN della WMI, uplink, NTP, DNS, SSH — [[#Configurazione Iniziale]].
- Presenza di `dot1x system-auth-control` nella running-config — [[#Method List]].
- Contenuto reale della redirect ACL (`show ip access-lists GUEST_REDIRECT`) — [[#Flex Profile]].
- Impostazioni PMF e Fast Transition della WLAN client — [[#PBA-Client]].
- Nomi, VLAN e flag dei policy profile, con screenshot (`show wireless profile policy detailed <nome>`) — [[#Policy Profiles]].
- Nome del profilo di authorization ISE usato per il guest wireless, l'equivalente di [[PBA - NAC - ISE Server#Redirect_Guest_Wired|Redirect_Guest_Wired]] — [[#PBA-Guest]].
- RF tag e RF profile in uso (`show wireless tag rf summary`) — [[#RF Profiles]].
- Metodo di assegnazione dei tag e naming convention degli AP (`show ap tag summary`) — [[#Assegnazione dei Tag agli AP]].