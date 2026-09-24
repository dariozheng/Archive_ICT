---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - category/networking/networking_general
  - encor/routing
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-08-26
aliases:
  - AS
---
<strong>Autonomous System (AS)</strong> is a massive network or a collection of networks under a single administrative control that shares a unified routing policy, and an <strong>Autonomous System Number (ASN)</strong> is a globally unique identifier assigned to that system. 

An <strong>AS</strong> is essentially a major building block of the internet infrastructure. Large organizations—such as Internet Service Providers (ISPs), tech giants like Google and Amazon, universities, and government agencies—operate their own AS networks.

Every <strong>AS</strong> manages and controls a specific group of IP addresses called IP prefixes. 

The <strong>ASN</strong> is assigned to an <strong>AS</strong> by the <strong>IANA</strong> via Regional Internet Registries like <strong>ARIN</strong> or <strong>RIPE</strong>. 

The <strong>ASN</strong> are a 4 bytes (32-bit range) numbers. This allows for  <strong>4,294,967,295</strong> unique <strong>ASNs</strong>.

Two blocks of private <strong>ASNs</strong> are available for any organization to use, as long as they are never exchanged publicly on the Internet. 
<strong>ASNs 64,512–65,534</strong> are private ASNs in the <strong>16-bit ASN range</strong>, and <strong>4,200,000,000–4,294,967,294</strong> are private ASNs within the extended <strong>32-bit range</strong>.

It is imperative to use only the <strong>ASN</strong> assigned by IANA, the ASN assigned by your service provider, or a private ASN. Using another organization's ASN without permission could result in traffic loss and cause havoc on the Internet.