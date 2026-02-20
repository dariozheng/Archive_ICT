---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-20T12:47:26+01:00
modified: 2026-02-20T14:08:16+01:00
---
<mark style="background: #FFB8EBA6;"><strong>Data redistribution</strong> allows <strong>IP-to-user mappings</strong> from one firewall to be shared with another firewall</mark>. 

<mark style="background: #FF5582A6;">Every firewall that enforces <strong>user-based policies</strong> requires <strong>group-to-user mapping</strong> information</mark>. 

<mark style="background: #FFB86CA6;">In a large-scale network, each firewall would have to directly query each of the mapping sources (e.g. Domain Controllers) to map IP addresses to usernames</mark>. 

<mark style="background: #BBFABBA6;">With <strong>data redistribution</strong>, you can reduce resource usage by configuring one or more firewalls <strong>to collect</strong> multiple <strong>mapping sources</strong></mark> and <mark style="background: #ABF7F7A6;"><strong>share</strong> that information across firewalls</mark>. 

<mark style="background: #ADCCFFA6;"><strong>Redistribution</strong> enables you to enforce user-based policies when users rely on local sources for authentication</mark>, <mark style="background: #FFF3A3A6;">such as a regional directory service</mark>, <mark style="background: #CACFD9A6;">but need access to remote services and applications</mark>, <mark style="background: #FFF3A3A6;">such as a data center application without the need for re-authentication</mark>.

In simple terms, the idea is <mark style="background: #FFB8EBA6;">to set up an identity data redistribution point</mark> using <strong>NGFW</strong>, <strong>VM-Series</strong>, or <strong>Panorama</strong> <mark style="background: #FF5582A6;">to collect identity context from various sources</mark> and <mark style="background: #FFB86CA6;"><strong>redistribute</strong> that information to all firewalls</mark> <mark style="background: #FFF3A3A6;">to enforce <strong>consistent policies</strong> independent of the location</mark>.

<mark style="background: #BBFABBA6;">For a firewall, context could be something like <strong>IP-to-user mapping</strong> or <strong>host information profile</strong> (HIP), which gives information about device posture</mark>. 

<mark style="background: #ABF7F7A6;">Now irrespective of whether users are working from an office or home or a coffee shop</mark>, <mark style="background: #ADCCFFA6;"><u>the information is fed to all the firewalls that are enforcing identity-based policies</u></mark>.
### Configure the Firewall to Connect to the Redistribution Point #configuration 
With data redistribution, <mark style="background: #FFB8EBA6;">you configure the <strong>source</strong> or <strong>redistribution point</strong> the firewall will connect to</mark> and <mark style="background: #ADCCFFA6;">then select the type of information you want it to redistribute</mark>.

<mark style="background: #ABF7F7A6;">You can connect to the source device by using either the serial number or the host and port numbers</mark>. 
<mark style="background: #D2B3FFA6;">The type of information you select can include IP address-to-username mappings, IP address-to-tag mappings, username-to-tag mappings, Host Information Profile HIP data, or quarantined devices</mark>.
![[Redistribution Point.png]]

On the Clients tab, you can look at all the other firewalls, in real time, that are receiving data from this firewall.

Optionally, <mark style="background: #FFB8EBA6;">you can configure which networks you want the agent or agents to include in the data redistribution</mark> and <mark style="background: #FFF3A3A6;">which networks you want to exclude from data redistribution</mark>.
![[Redistribution Point 2.png]]