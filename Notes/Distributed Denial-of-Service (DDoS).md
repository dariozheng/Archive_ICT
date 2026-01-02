---
categories:
  - "[[Security]]"
topic@security:
  - "[[Network-Based Attacks]]"
tags:
  - security/attack
created: 2026-01-01T21:58:59+01:00
modified: 2026-01-02T08:05:46+01:00
---
Another type of DoS attack is the distributed denial-of-service (DDoS) attack that employs large numbers of attacking computers to overwhelm the target with bogus traffic.

<mark style="background: #FF5582A6;">DDoS attacks often are performed by botnets, and millions of infected machines can unconsciously participate in the attack, even though they are not the target of the attack itself</mark>.

<mark style="background: #FFF3A3A6;">The attacker leverages the massive number of infected machines to flood the remote target with traffic and cause a DoS</mark>.

DDoS Attack Advantages:
- <strong>Higher Volume of Machine</strong>: It can leverage the higher volume of machines to execute a seriously disruptive scale due to the large network of infected computers under its command.
- <strong>Undetectable Location</strong>: The attack is often spread worldwide, and the location is difficult to detect due to the random distribution of attacking systems.
- <strong>Difficult to Shut Down</strong>: It is more difficult to shut down than other DoS attacks due to the number of machines involved.
- <strong>Difficult to Identify the Attackers</strong>: The attacking party's exact source is highly challenging to identify, because it is disguised behind many (mostly compromised) systems.

### DDoS Mitigation Techniques
#### Implement DDoS Detection Tools
Network security infrastructure should include DDoS detection tools that can identify and block both exploits and tools that attackers use to launch an attack.
#### Create DDoS Protection Profiles
Network administrators also can create profiles to observe and control specific floods of traffic (i.e., SYN floods, UDP, and ICMP floods).
#### Set Thresholds
After all traffic is examined in aggregate, thresholds can be set to monitor and cut behaviors that indicate a possible DDoS attack
