---
categories:
  - "[[Security]]"
topic@security:
  - "[[Network-Based Attacks]]"
tags:
  - security/attack
created: 2026-01-01T21:58:31+01:00
modified: 2026-01-02T08:05:26+01:00
---
The goal of an attacker when using a <strong>buffer overflow attack</strong> is <mark style="background: #ABF7F7A6;">to find a <strong>system memory-related flaw</strong> on a server and exploit it</mark>. <mark style="background: #FF5582A6;">Exploiting the buffer memory by overwhelming it with unexpected values usually renders the system inoperable</mark>, creating a <strong>denial-of-service (DoS)</strong> attack.

Let's say that an adversary <mark style="background: #CACFD9A6;">enters input that is larger than expected by the application running on a server</mark>. 
<mark style="background: #ADCCFFA6;">The application accepts the large amount of input and stores it in memory</mark>. 
<mark style="background: #FFB8EBA6;">The result is that the application may consume the associated memory buffer and potentially overwrite adjacent memory, eventually corrupting the system and causing it to crash</mark>.

An early example of using malformed packets is the Ping of Death. In this legacy attack, the threat actor would send a ping of death, which was an echo request in an IP packet larger than the maximum packet size of 65,535 bytes. The receiving host would not be able to handle a packet of that size, and it would crash.