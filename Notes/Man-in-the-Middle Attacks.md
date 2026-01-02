---
categories:
  - "[[Security]]"
topic@security:
  - "[[Network-Based Attacks]]"
tags:
  - security/attack
created: 2026-01-01T21:59:30+01:00
modified: 2026-01-02T08:06:02+01:00
---
This attack's main purpose is to allow an attacker to intercept communications so that the attacker can actually see the traffic and steal or manipulate it.

A man-in-the-middle attack happens when <mark style="background: #FFB8EBA6;">an attacker places themselves in-line <strong>between two devices that are communicating</strong></mark>. 
The attacker's intent is to perform reconnaissance or manipulate the data that is being transferred as it moves between those entities. This attack can happen at Layer 2 (Data Link) or Layer 3 (Network).

### Layer 2

In a Layer 2 man-in-the-middle attack, the <mark style="background: #ADCCFFA6;">attacker</mark> <mark style="background: #FFF3A3A6;">spoofs its Layer 2 hardware address</mark> <mark style="background: #ABF7F7A6;">to make the <strong>devices on the local area network</strong></mark> believe <mark style="background: #BBFABBA6;">th<strong></strong>at the Layer 2 address of the attacker</mark> is <mark style="background: #FFB86CA6;">the Layer 2 address of its <strong>default gateway</strong></mark>. 
However, the target still <mark style="background: #FFB8EBA6;">has an ARP</mark> (Address Resolution Protocol) table (a table associating a hardware address with an IP address) <mark style="background: #FFB8EBA6;">pointing to the default gateway</mark>. 
The target must use the attacker’s hardware address to complete the man-in-the-middle attack.

How is this accomplished? The technique is called an <strong>ARP poisoning attack</strong>. 
In this attack, <mark style="background: #FF5582A6;">the attacker sends falsified ARP packets to the target</mark>. 

<mark style="background: #FFB86CA6;">These packets associate the attacker’s hardware address with the router's IP address</mark>. 
<mark style="background: #BBFABBA6;">Packets that are supposed to go through the default gateway</mark> <mark style="background: #ABF7F7A6;">are forwarded to the attacker's hardware address (Layer 2) on the same network</mark>. 
<mark style="background: #D2B3FFA6;">The attacker can forward the packets to the correct destination so that the client will have the necessary connectivity</mark>, <mark style="background: #CACFD9A6;">and the attacker now sees all the data between the two devices</mark>.

### Layer 3

A man-in-the-middle attack can also occur at Layer 3. 
<mark style="background: #FFF3A3A6;">The attack can be done by a rogue router being placed on the network</mark>, <mark style="background: #BBFABBA6;">which then tricks the other routers into believing the new router has a better path in the network</mark>. 
This action could cause network traffic to slow through the rogue router and allow the attacker to steal network data.

### Compromised System

There are other man-in-the-middle attacks that can occur at layer 3. 

<mark style="background: #FFF3A3A6;">The attacker can install malware that can intercept the victim's packets and send them directly to the attacker</mark>. 

<mark style="background: #BBFABBA6;"><strong>This type of malware can capture a packet before it is encrypted</strong></mark>. 
If the victim is using TLS, SSL, HTTPS, or any other mechanisms, then packets can be stolen and sent to the attacker before they are encrypted.