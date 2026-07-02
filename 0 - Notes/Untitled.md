Il Wireless LAN Controller (WLC) è il punto di controllo centrale della rete wireless: gli AP si registrano al controller tramite CAPWAP e ne ricevono la configurazione, mentre il WLC agisce da RADIUS client verso ISE per l'autenticazione dei client Wi-Fi (802.1X e MAB). Nel deployment il WLC è pba-wlc01 (10.140.1.10), un Catalyst 9800 — modello esatto e versione IOS-XE da confermare sul sistema live — e i siti remoti lavorano in FlexConnect local switching. Il lato server è documentato in [[PBA - NAC - ISE Server]], il lato switch in [[PBA - NAC - Network Access Devices]].

## Accesso

L'accesso al portale GUI del WLC è eseguito con le credenziali RADIUS tramite il portale [https://pba-wlc01.publiacqua.it/webui/](https://pba-wlc01.publiacqua.it/webui/).

Il WLC ha l'indirizzo 10.140.1.10.

![[Pasted image 20260630121117.png]]

Anche l'accesso SSH è eseguito con le credenziali RADIUS. L'autenticazione degli accessi admin è definita dalle [[#Method List|method list]] di login; l'eventuale utente locale di fallback per quando i server RADIUS non sono raggiungibili non è ancora documentato qui.

## Configurazione Iniziale

Le configurazioni che devono essere fatte prima di creare le WLAN e prima di joinare gli AP sono le configurazioni base come hostname, VLAN, SSH, NTP, DNS, country code e la Wireless Management Interface. Hostname, VLAN e interfacce di uplink, SSH, NTP e DNS non sono ancora documentati qui — da integrare, idealmente con il blocco di configurazione come fatto per gli switch in [[PBA - NAC - Network Access Devices#Initial Configuration|Initial Configuration]].

### Wireless Management Interface

![[Pasted image 20260630145410.png]]

La Wireless Management Interface (WMI) è l'interfaccia che termina i tunnel CAPWAP degli AP ed è la source interface per il RADIUS, oltre a essere l'indirizzo di management della macchina stessa (10.140.1.10).

### Country Code

Le radio non sono attive finché non è configurato il corretto country code. Il comando definisce la lista globale dei country code ammessi sul WLC:

```cisco
ap country IT
```

Il country code viene poi assegnato agli AP tramite l'[[#AP Join Profile]]: il paese selezionato nel profilo deve essere presente anche in questa lista globale, altrimenti viene ignorato. È particolarmente importante per gli AP con dominio regolatorio -ROW, che senza country code assegnato restano in compatibility mode con la radio 5 GHz spenta.

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

RADIUS_SERVER_DAY0_1 è radius-mgmnt-auth01 (10.140.2.27), il RADIUS di management usato per il login admin di ISE, NAD e DNAC ([[PBA - NAC - ISE Server#Deployment Architecture|Deployment Architecture]]). PBA-ISE-01 (10.140.2.31) è il Policy Service Node ISE01; il secondo nodo ISE02 (10.140.2.32) non è definito sul WLC — da valutare se aggiungerlo al gruppo ISE e tra i client CoA per avere il failover, come già fanno gli switch con il gruppo ISESERV.

`automate-tester` invia periodicamente una probe con l'utente probe-user per verificare che il server risponda; `dead-criteria` e `deadtime` definiscono quando un server viene marcato dead (nessuna risposta entro 5 secondi per 3 tentativi) e per quanti minuti resta escluso, permettendo il failover sull'altro server del gruppo.

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

_Method lists tell the WLC who to ask and what to do with the answer._

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

|Method list|Tipo|Uso|
|---|---|---|
|default|authentication login|Autentica gli accessi admin GUI/SSH descritti in [[#Accesso]]: prima il gruppo day0, poi ISE.|
|authentication_login_day0|authentication login|Come la default ma con fallback sulle credenziali locali; su quali linee sia applicata non è documentato qui.|
|ML-ISE, authentication_dot1x_day0|authentication dot1x|Authentication List per le WLAN 802.1X come [[#PBA-Client]].|
|mac_filtering|authorization network|Authorization List del MAC filtering della WLAN guest.|
|default|authorization exec|Livello di privilegio della shell per gli admin: prima ISE, poi il gruppo day0.|
|default|accounting identity|Invia a ISE gli accounting start/stop delle sessioni client, necessari a ISE per tracciare le sessioni.|

wcm_loc_serv_cert è una voce di default del 9800 (download locale delle credenziali per i servizi interni) e non fa parte del design.

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

#### RF Tag

Il RF Tag associa a ogni AP i RF Profile da usare per banda (2.4 GHz, 5 GHz ed eventualmente 6 GHz).

##### RF Profiles

Nei RF Profile si configurano i data rate, i canali (DCA), le potenze (TPC) e le altre impostazioni radio per banda. Quali RF tag e RF profile siano in uso nel deployment, o se si usi il default-rf-tag, non è ancora documentato qui.

### Assegnazione dei Tag agli AP

I tag possono essere assegnati agli AP in tre modi: staticamente per singolo AP, tramite filtri con regex sul nome dell'AP, oppure lasciando i default tag (default-policy-tag, default-site-tag, default-rf-tag). Il metodo usato in questo deployment e la naming convention degli AP non sono ancora documentati qui.