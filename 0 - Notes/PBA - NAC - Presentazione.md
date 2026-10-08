---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Cisco ISE]]"
tags:
  - category/networking/cisco_ise
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-10-08
status: draft
---
# Presentazione NAC
Il NAC ISE (Network Access Control) è un sistema che gestisce e monitora gli accessi alla rete aziendale.

Offre un controllo degli accessi si basa su diversi attributi, tra cui **identità dell'utente, tipologia di dispositivo, posizione e contesto della connessione**. In base alle informazioni raccolte e alle regole configurate, Cisco ISE determina il livello di accesso da concedere alla rete aziendale.

Le informazioni relative alle autenticazioni e alle autorizzazioni vengono registrate nei log di Cisco ISE. La durata della conservazione dipende dalla configurazione e dalle risorse disponibili; per estendere la retention oltre quella consentita localmente, è possibile inoltrare i log a un server esterno

Con la corretta implementazione del NAC gli utenti normali di Publiacqua non noteranno quasi nessuna differenza quando accederanno alla rete cablata, mentre i dispositivi non riconosciuti o non correttamente registrati e autorizzati si ritroveranno nella rete Guest, senza accesso a internet se non hanno l'autorizzazione da un utente di Publiacqua. 

Tutte le policy sono gestite in una piattaforma centralizzata dove verrà impostata quali profili di autorizzazione ogni utente riceverà. 
I profili di autorizzazione possono essere semplicemente fornire l'accesso alla VLAN di ADMIN, CLIENT, GUEST o impostare anche Access List per limitare a quali indirizzi IP l'utente può raggiungere. 

Questi profili di autorizzazione e le policy che permettono questi profili possono essere personalizzati a seconda di esigenze in ogni momento.

