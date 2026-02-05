---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
created: 2026-02-04T22:34:35+01:00
modified: 2026-02-05T10:33:04+01:00
aliases:
  - SNI
---
<mark style="background: #FFB86CA6;"><strong>Server Name Indication</strong> (<strong>SNI</strong>) is an extension</mark> to the <strong>Transport Layer Security</strong> (<strong>TLS</strong>) computer networking protocol <mark style="background: #FFB86CA6;">by which a</mark> <mark style="background: #FF5582A6;">client</mark> <mark style="background: #ADCCFFA6;">indicates</mark> <mark style="background: #D2B3FFA6;">which hostname</mark> <mark style="background: #FF5582A6;">it</mark> <mark style="background: #ADCCFFA6;">is attempting to connect to</mark> <mark style="background: #CACFD9A6;">at the start of the handshaking process</mark>.

<mark style="background: #BBFABBA6;">The extension allows a server to present</mark> <mark style="background: #FFB8EBA6;">one of multiple possible certificates</mark> <mark style="background: #ABF7F7A6;">on the same IP address and TCP port number</mark> and <mark style="background: #FF5582A6;">hence allows multiple secure (<strong>HTTPS</strong>) websites (or any other service over TLS) to be served by the same IP address without requiring all those sites to use the same certificate</mark>. 

<mark style="background: #BBFABBA6;">This also allows a proxy to forward client traffic to the right server during a TLS handshake</mark>. 

The desired hostname is not encrypted in the original SNI extension, so an eavesdropper can see which site is being requested. 

The SNI extension was specified in 2003 in RFC 3546

<mark style="background: #FFB86CA6;">SNI make the client send the name of the virtual domain as part of the TLS negotiation's ClientHello message</mark>.

<mark style="background: #FFB8EBA6;">This enables the server to select the correct virtual domain early and present the browser with the certificate containing the correct name</mark>. 

Therefore, <mark style="background: #ADCCFFA6;">with clients and servers that implement SNI</mark>, <mark style="background: #FF5582A6;">a server with a single IP address can serve a group of domain names</mark> <mark style="background: #FFF3A3A6;">for which it is impractical to get a common certificate</mark>.