---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
created: 2026-01-28T16:02:30+01:00
modified: 2026-01-29T16:38:51+01:00
aliases:
  - Software-Defined WAN
  - Software Defined Wan
  - SDWAN
---
<strong>SD-WAN</strong> (<strong>software-defined wide area network</strong>) is a type of networking technology that uses <strong>software-defined networking</strong> (<strong>SDN</strong>) principles to manage and optimize wide area network (WAN) performance.

SD-WAN also simplifies WAN management by <mark style="background: #FFF3A3A6;">providing centralized control and visibility over the entire network</mark>.

<mark style="background: #FF5582A6;">SD-WAN is a virtualized approach to managing wide area networks</mark>.
<mark style="background: #FF5582A6;">It connects</mark> <mark style="background: #BBFABBA6;">users and branch sites</mark> to <mark style="background: #ABF7F7A6;">enterprise applications</mark> across <mark style="background: #FFB86CA6;">multiple transport types</mark>. <mark style="background: #FFB86CA6;">Like MPLS, broadband, wireless links, VPNs, and public internet</mark>.

<mark style="background: #ADCCFFA6;">Each SD-WAN appliance connects to a <strong>centralized controller</strong></mark>. <mark style="background: #FFB8EBA6;">The controller monitors network conditions—latency, jitter, packet loss—and decides how traffic should flow</mark>. <mark style="background: #FFF3A3A6;">If a link degrades, SD-WAN automatically reroutes traffic to a better-performing path</mark>.
![[Dynamic path selection in SDWAN.png]]

<mark style="background: #D2B3FFA6;">Policies are created centrally and pushed to all sites without manual configuration</mark>. 
Which means changes can be rolled out quickly and consistently.

<mark style="background: #ABF7F7A6;">Routing decisions aren't made locally. They follow global policies set by the control plane</mark>. That's what allows for dynamic, policy-based traffic management.

Basically, SD-WAN continuously adapts based on real-time performance. It supports application-aware routing, steers traffic across the best available link, and helps maintain uptime.

## SD-WAN architecture

SD-WAN architecture refers to the conceptual structure and logical design of a software-defined wide area network.
It defines how the system is built, how components interact, and how traffic is routed and managed. Understanding the architecture helps clarify what SD-WAN does. And how it works behind the scenes.

SD-WAN is made up of several core components that work together to provide centralized control, efficient traffic routing, and flexible deployment across locations.
![[SD-WAN components.png]]
- <strong>SD-WAN edge</strong>: The edge is the enforcement point where SD-WAN connects to the physical network, typically at branches or cloud sites. <mark style="background: #FFB86CA6;">It forwards traffic and <strong>applies local policies</strong> based on controller instructions</mark>.
- <strong>SD-WAN orchestrator</strong>: The orchestrator is a centralized software management that provides centralized management, pushing configurations and updates across all sites. It reduces manual work by letting admins control the network through a single interface. <mark style="background: #FFB8EBA6;">It's web portal</mark> or web page. 
- <strong>SD-WAN controller</strong>: The controller makes centralized policy decisions and monitors network conditions. It directs how traffic should flow and communicates those decisions to edge devices.
- <strong>Virtual or physical nodes</strong>: These optional nodes help expand SD-WAN coverage or capacity at key points in the network. They can improve traffic routing and scalability across distributed environments.