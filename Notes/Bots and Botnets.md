---
categories:
  - "[[Security]]"
topic@security:
  - "[[Network-Based Attacks]]"
tags:
  - security/c2
created: 2026-01-01T21:57:14+01:00
modified: 2026-01-02T08:05:21+01:00
---
<mark style="background: #FFB8EBA6;">Bots (or zombies) are individual endpoints infected with advanced malware</mark> <mark style="background: #FF5582A6;">that enables an attacker <strong>to control compromised endpoints</strong></mark>. 

<mark style="background: #FFF3A3A6;">A botnet is a network of bots</mark> (often tens of thousands or more) <mark style="background: #FFF3A3A6;">working together under the control of attackers and using numerous servers</mark>.

Bots and botnets are notably difficult for organizations to detect and defend against using traditional anti-malware solutions. 
The botnet can evolve to pursue new goals or adapt when different security countermeasures are deployed. 
Communication between the individual bots and the larger botnet through C2 servers provides resiliency in the botnet.

Because botnets are flexible and can evade defenses, they are a significant threat to organizations. 
The scope of an attacker's ultimate impact can extend from sending spam one day to stealing credit card data the next day to avoiding detection for months or even years.

## Botnet Takedowns

#### Neutralizing Though Isolation 

<mark style="background: #FFB8EBA6;">A botnet can be dismantled or neutralized by isolating the bots</mark> (<mark style="background: #FF5582A6;">zombies or infected endpoints</mark>) <mark style="background: #FFB8EBA6;">from their command centers</mark> (<mark style="background: #FF5582A6;">command-and-control servers</mark>). 
If the bots are unable to communicate with their servers, they cannot receive new instructions, transmit stolen data, or carry out any actions that make botnets uniquely dangerous.

#### Disamblement of C2 Servers

<mark style="background: #BBFABBA6;">Disablement of C2 servers often requires physically seizing the servers and taking ownership of the domain and IP address range associated with the servers</mark>. 
Very close coordination between technical teams, legal teams, and law enforcement is essential to disabling the C2 infrastructure of a botnet. 
Many botnets have C2 servers worldwide and will function, especially in countries with little or no law enforcement for internet crimes.

#### Disabling C2 Infrastructure Simultaneously

Most botnet systems are designed to withstand a C2 server's loss, which means that the entire botnet C2 infrastructure must be disabled almost simultaneously. 
<mark style="background: #FFB86CA6;">If any C2 server is accessible or any of the fallback options survive, the bots will get updates and rapidly populate an entirely new set of C2 servers</mark>. The botnet will quickly recover to function.