---
categories:
  - "[[Security]]"
topic@security:
  - "[[Network-Based Attacks]]"
tags:
  - security/attack
created: 2026-01-01T21:58:51+01:00
modified: 2026-01-02T08:05:42+01:00
---
A <strong>denial-of-service (DoS)</strong> attack <mark style="background: #ABF7F7A6;">targets a system to prevent network communication</mark> or <mark style="background: #FFF3A3A6;">it targets an entire organization to prevent or shut down outgoing or incoming traffic to a machine or to certain network services</mark>, such as an organization’s website access or email services.

DoS attacks accomplish their goals by flooding the target with traffic or by sending it a type of information that triggers a crash. 

In both instances, the DoS attack deprives legitimate users (such as employees, members, or account holders) of the service or resource they expected. 
This type of attack easily can obstruct business-related functions and cause them to stop functioning.

## Two Forms of DoS Attacks

### Flood Attacks

Flood attacks occur when the system receives too much traffic for the server to buffer, thus causing it to slow down and eventually stop. 
Popular flood attacks include:
##### Internet Control Message Protocol (ICMP) Flood
Leverages misconfigured network devices by <mark style="background: #FF5582A6;">sending spoofed packets that <strong>ping</strong> every computer on the targeted network</mark>, instead of just one specific machine. The network is then triggered to amplify the traffic. This attack also is known as the smurf attack or ping of death.
##### Synchronize (SYN) Flood
<mark style="background: #BBFABBA6;">Sends a request to connect to a server, but never completes the handshake. It continues until all open ports are saturated with requests and none are available for legitimate users to connect to</mark>.

### Resource Exhaustion

A Buffer Overflow Attack can exploit vulnerabilities in a system. A Buffer Overflow Attack can also cause resource depletion, leading to a DoS Attack on the system.