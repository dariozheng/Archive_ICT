---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
created: 2026-02-04T22:34:35+01:00
modified: 2026-02-05T08:44:17+01:00
aliases:
  - SNI
---
<mark style="background: #FFB86CA6;"><strong>Server Name Indication</strong> (<strong>SNI</strong>) is an extension</mark> to the <strong>Transport Layer Security</strong> (<strong>TLS</strong>) computer networking protocol by which <mark style="background: #BBFABBA6;">a client indicates which hostname it is attempting to connect to at the start of the handshaking process</mark>.

The extension allows a server to present one of multiple possible certificates on the same IP address and TCP port number and hence allows multiple secure (HTTPS) websites (or any other service over TLS) to be served by the same IP address without requiring all those sites to use the same certificate. It is the conceptual equivalent to HTTP/1.1 name-based virtual hosting, but for HTTPS. This also allows a proxy to forward client traffic to the right server during a TLS handshake. The desired hostname is not encrypted in the original SNI extension, so an eavesdropper can see which site is being requested. The SNI extension was specified in 2003 in RFC 3546