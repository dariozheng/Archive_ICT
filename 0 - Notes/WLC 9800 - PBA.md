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

## Server Groups e Method Lists

I Server Group crea gruppi di servers che vengono usati nelle Method List che verranno usati dalle WLANs e policy profiles. 










## Profiles

_Containers for the actual settings. Each profile type is related to on field of the network._

| Profile         | Field                                                                                          | Configured in                                    |
| --------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| WLAN profile    | SSID e L2 security                                                                             | [[#WLAN Profiles]]                               |
| Policy profile  | What VLAN, QoS, ACLs and switching a client gets after it joins                                | [[#Policy Profiles]]                             |
| AP join profile | How the AP itself behaves — CAPWAP timers, management, SSH, syslog                             | [[#AP Join Profile]]                             |
| Flex profile    | VLAN mapping and local-switching behavior for [[#FlexConnect (Local Switching)\| FlexConnect]] | [[#FlexConnect (Local Switching)\| FlexConnect]] |
| RF profile      | Data rates, channels and power per band                                                        | [[#RF Management]]                               |
