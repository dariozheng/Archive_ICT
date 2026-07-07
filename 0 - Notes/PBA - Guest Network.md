---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - PBA
icon: FasNetworkWired
iconColor: "#003791"
---
In questa documentazione ci sono varie configurazioni per la rete Guest di PBA. 
# DNS-GUEST
La configurazione della dns-guest server e come vengono impostati i forwarders.

![[Pasted image 20260706114203.png]]

 ![[Pasted image 20260706114254.png]]
# Firewall Firepower
Firepower policy dagli dns-guest verso i suoi forwarders. Regola per permettere DNS-GUEST di raggiungere il firewall Palo-Alto.

![[Pasted image 20260706105737.png]]

Firepower policy dagli dns-guest verso i siti remoti.

![[Pasted image 20260706105752.png]]

# Firewall Panorama
Panorama rule per gli guests.

![[Pasted image 20260706110217.png]]

La rule permette la navigazione solo alle Applications nella lista NAVIGAZIONE_INTERNET_GUESTS.

![[Pasted image 20260707114519.png]]

Panorama rule per gli dns-guest verso i suoi forwarders.

![[Pasted image 20260706110301.png]]

Aggiungere le rotte statiche all'interfaccia ae1.3555 su Virtual Router - vrINTERNET.

![[Pasted image 20260706114448.png]]

![[Pasted image 20260706114505.png]]

L'interfaccia ae1.3555 si trova in zona VRF_GW_IN.

![[Pasted image 20260707121651.png]]

In NAT Rules viene usata la regola seguente.

![[Pasted image 20260707121148.png]]