---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-06T12:24:24+01:00
modified: 2026-02-19T15:21:40+01:00
---
![[Phishing Protection.png]]
1) Attacker sends phishing email that contains a link to the compromised web server.
2) Bob clicks the link and enter his corporate credentials.
3) The firewall notices <mark style="background: #FFB8EBA6;">credential information in the web traffic</mark> and uses <mark style="background: #FF5582A6;">User-ID to detect whether they are valid corporate credentials</mark>. You can configure User-ID to use one of three different methods to detect corporate credentials in web traffic.
4) If User-ID detects valid corporate credentials, then the <mark style="background: #FFB86CA6;">firewall consults its URL filtering configuration</mark> <mark style="background: #FFF3A3A6;">to determine the URL categories for which users should be prevented from entering their corporate credentials</mark>.
5) In this case, Bob is attempting to enter his corporate credentials to a blocked website and the firewall blocks his credentials from being submitted.


