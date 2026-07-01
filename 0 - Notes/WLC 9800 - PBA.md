---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[WLAN]]"
tags:
icon: SiCisco
iconColor:
---


- Policy Tag
- Site Tag
- RF Tag
- HA
# Accesso 
L'accesso al portale GUI di WLC è eseguito con le credenziali RADIUS tramite il portale
[https://pba-wlc01.publiacqua.it/webui/](https://pba-wlc01.publiacqua.it/webui/). 

Il WLC ha l'indirizzo 10.140.1.10 

![[Pasted image 20260630121117.png]]

Anche l'accesso SSH è eseguito con le credenziali RADIUS. 
# Configurazione Iniziale
Le configurazioni che devono essere fatte prima di creare WLANs e prima di joinare gli AP sono le configurazioni base come hostname, VLAN, SSH, NTP, DNS, Country Code e la Wireless Management Interface. 
## Wireless Management Interface

![[Pasted image 20260630145410.png]]

Il Wireless Management Interface è l'interfaccia che termina CAPWAP ed è il source interface per il RADIUS oltre ad essere l'indirizzo di management for la macchina stessa.

## Country Code
Le radio non sono attive finché non è configurato il corretto country code.

```cisco
ap country IT
```

# RADIUS e AAA
## RADIUS Servers
Command per definire i server radius con SSH 

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

### CoA
Change of Authorization permette a un server NAC di cambiare il tipo di autorizzazione ad un client. Con CoA è possibile disconnettere una sessione, applicare nuovi attributi(ACL, VLAN), cambiare banda. 

```cisco
aaa server radius dynamic-author
 client 10.140.2.27 server-key 0CiScOsSSo0
 client 10.140.2.31 server-key Plutarco46Dc!
```

## Server Groups

![[Pasted image 20260630153701.png]]

I Radius Server Group crea dei gruppi server che può essere usato per i Method List. 

## Method List

![[Pasted image 20260630154036.png]]

I method list corrispondono ai commandi
```
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

# Configurazione 

Il WLC non configura direttamente gli AP ma costruisce degli profili re-usabili, raggruppa questi profili in tags ed assegna un tag per tipo (Policy tag, Site tag, RF tag) ad ogni AP. Le configurazioni sono date da queste tag o profili. 


![[wlc9800-tag-architecture.png]]
## Profiles

_Containers for the actual settings. Each profile type is related to on field of the network._

| Profile         | Field                                                                         | Configured in                                    |
| --------------- | ----------------------------------------------------------------------------- | ------------------------------------------------ |
| WLAN profile    | SSID e L2 security                                                            | [[#WLAN Profiles]]                               |
| Policy profile  | What VLAN, QoS, ACLs and switching a client gets after it joins               | [[#Policy Profiles]]                             |
| AP join profile | How the AP itself behaves — CAPWAP timers, management, SSH, syslog            | [[#AP Join Profile]]                             |
| Flex profile    | VLAN mapping and local-switching behavior for [[#Flex Profile\| FlexConnect]] | [[#FlexConnect (Local Switching)\| FlexConnect]] |
| RF profile      | Data rates, channels and power per band                                       | [[#RF Management]]                               |
## AP Join Process

In questo deployment gli AP usano <strong>DHCP option 43</strong> per ottenere il [[#Wireless Management Interface]] per joinare il WLC.

Reference:
https://www.cisco.com/c/en/us/support/docs/wireless-mobility/wireless-lan-wlan/97066-dhcp-option-43-00.html

![[Pasted image 20260701111850.png]]

Il DHCP option 43 ha tre formatti, f1, f2 e f3. Noi usiamo <strong>f1</strong> 

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

<strong>0x</strong> significa che la stringa è in <strong>esadecimale</strong> ed non in <strong>decimale</strong>.

<strong>04</strong> o <strong>08</strong> sono le lunghezza del l'indirizzo, 04 significa 4 bytes cioè un IP address, 08 sono 8 bytes ed quindi due IP address.

<strong>0A8C010A</strong> indirizzo IP in esadecimale, se sono presenti due indirizzi, inserire il secondo indirizzo subito dopo il primo indirizzo. 

## Tags
### Site Tag

Il Site Tag decide in che <strong>switching mode</strong> configurare gli AP:
- Local Mode (Central Switching): gli AP invia il traffico dati verso il WLC tramite il CAPWAP tunnel, il quale trasferisce il traffico L2 verso la VLAN contenuto nella policy profile. In questo mode tutti i siti remoti devono riuscire a raggiungere la WLC che si trova in VM90. 
- FlexConnect (Local Switching): gli AP porta il traffico direttamente sulla VLAN locale e la WLC viene usato solo per il control-plane. La VLAN viene fornito dalla Flex Profile che viene chiamato dalla site tag. 

Nello deployment attuale lo switching mode è in FlexConnect (Local Switching). La FlexConnect disattiva la selezione <strong>Enable Local Site</strong> e aggiunge la <strong>Flex Profile</strong> tra le selezioni.

![[Pasted image 20260701120051.png]]

#### AP Join Profile 
AP join profile configura il <strong>country code</strong> delle AP, <strong>NTP server</strong>, <strong>WLC secondario</strong>, le credenziali admin locali, se <strong>SSH verso l'AP</strong> è permesso, dove invia i syslog, CAPWAP timers, e la crittografia DTLS del CAPWAP data path e altro. 

![[Pasted image 20260701114537.png]]

![[Pasted image 20260701114557.png]]

![[Pasted image 20260701114902.png]]

#### Flex Profile
L'opzione di Flex Profile viene mostrato solo se <strong>Enable Local Site</strong> è disattivo. 
Su Flex Profile è possible configurare le VLAN, Native VLAN, autenticazione locale e le policy ACL.

![[Pasted image 20260701115751.png]]

![[Pasted image 20260701122312.png]]

![[Pasted image 20260701122343.png]]

In policy ACL viene configurato il GUEST_REDIRECT access list che gestisce il dirottamento delle rotte per la Guest Wifi. 
Attivando il <strong>Central Web Auth</strong>, il traffico che attiva questo ACL non viene gestita localmente ma reindirizzata verso il WLC in modo da attivare il portale guest.

![[Pasted image 20260701123009.png]]

### Policy Tag
