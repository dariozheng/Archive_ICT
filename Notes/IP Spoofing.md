---
categories:
  - "[[Security]]"
topic@security:
  - "[[Network-Based Attacks]]"
tags:
  - security/exploit
created: 2026-01-01T21:59:06+01:00
modified: 2026-01-02T08:05:57+01:00
---
IP Spoofing is an attack vector, a technique employed in various network-based attacks.

<mark style="background: #FFF3A3A6;">Adversaries use this technique in computer networks to mimic another computer’s IP address or hide their source IP address.</mark>

IP spoofing is usually used in conjunction with denial-of-service attacks by writing the target IP address as the source IP address of the packets.

The IP protocol doesn’t authenticate the source IP address by design.

<mark style="background: #ABF7F7A6;">Therefore, an adversary could send an IP packet with a fake, different, or unreal source IP address and thus remain <strong>anonymous</strong></mark>.

<mark style="background: #FFF3A3A6;">It then can initiate another attack and <strong>bypass some security restrictions that rely on verifying the source IP address</strong>.</mark>
