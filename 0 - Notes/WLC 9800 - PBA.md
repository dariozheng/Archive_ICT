---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[WLAN]]"
tags:
icon: SiCisco
iconColor:
---
# Table of Contents 
- Overview 
- Accessi 
- Configurazione iniziale
- RADIUS
- Modello Configurazione 
- AP Join
- Policy Tag
- Site Tag
- RF Tag
- HA

Il Cisco Catalyst 9800 WLC è un IOS-XE controller che termina i tunnel CAPWAP degli AP e centralizza le loro configurazioni.

Il WLC non configura direttamente gli AP ma costruisce degli profili re-usabili, raggruppa questi profili in tags ed assegna un tag per tipo (Policy tag, Site tag, RF tag) ad ogni AP. Le configurazioni sono date da queste tag o profili. 


![[wlc9800-tag-architecture.png]]

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


## Profiles

_Containers for the actual settings. Each profile type is related to on field of the network._

| Profile         | Field                                                                                          | Configured in                                    |
| --------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| WLAN profile    | SSID e L2 security                                                                             | [[#WLAN Profiles]]                               |
| Policy profile  | What VLAN, QoS, ACLs and switching a client gets after it joins                                | [[#Policy Profiles]]                             |
| AP join profile | How the AP itself behaves — CAPWAP timers, management, SSH, syslog                             | [[#AP Join Profile]]                             |
| Flex profile    | VLAN mapping and local-switching behavior for [[#FlexConnect (Local Switching)\| FlexConnect]] | [[#FlexConnect (Local Switching)\| FlexConnect]] |
| RF profile      | Data rates, channels and power per band                                                        | [[#RF Management]]                               |
