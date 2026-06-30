---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[WLAN]]"
tags:
icon:
iconColor:
---
L'accesso al portale WLC è eseguito con le credenziali RADIUS tramite il portale
[https://pba-wlc01.publiacqua.it/webui/](https://pba-wlc01.publiacqua.it/webui/). 

Il WLC ha l'indirizzo 10.140.1.10 

Il WLC 9800 è un wireless controller che termina i tunnel CAPWAP degli AP e centralizza le loro configurazioni.

Il WLC non configura direttamente gli AP ma costruisce degli profili re-usabili, raggruppa questi profili in tags ed assegna un tag per tipo (Policy tag, Site tag, RF tag) ad ogni AP. Le configurazioni sono date da queste tag o profili. 

![[wlc9800-tag-architecture.png]]

## Profiles

_Containers for the actual settings. Each profile type answers one question about the network._

| Profile         | Answers                                                                         | Configured in                                    |
| --------------- | ------------------------------------------------------------------------------- | ------------------------------------------------ |
| WLAN profile    | What SSID is broadcast and how clients authenticate (L2 security)               | [[#WLAN Profiles]]                               |
| Policy profile  | What VLAN, QoS, ACLs and switching a client gets after it joins                 | [[#Policy Profiles]]                             |
| AP join profile | How the AP itself behaves — CAPWAP timers, management, SSH, syslog              | [[#AP Join Profile]]                             |
| Flex profile    | VLAN mapping and local-switching behaviour for [[#FlexConnect (Local Switching) | [[#FlexConnect (Local Switching)\| FlexConnect]] |
| RF profile      | Data rates, channels and power per band                                         | [[#RF Management]]                               |

A WLAN profile and a policy profile are always used as a pair: the WLAN says how to authenticate, the policy says what access results. The pairing is made inside the [[#Policy Tag|policy tag]].