---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - glossaries
  - networking
created: 2026-01-05T16:52:58+01:00
modified: 2026-01-27T17:31:39+01:00
---
#### software-defined network
<strong>Software-Defined Network (SDN)</strong> infrastructure <mark style="background: #FFB8EBA6;">centralizes network control in software</mark>, separating it from hardware (routers/switches), <mark style="background: #FFF3A3A6;">creating a virtualized, programmable network</mark> <mark style="background: #ABF7F7A6;">managed via a central controller and APIs for agility, automation, and easier management</mark>, allowing dynamic traffic steering and policy enforcement across physical and virtual environments. 
#### SD-WAN
SD-WAN (Software-Defined Wide Area Network) is a networking approach that uses <mark style="background: #FFF3A3A6;">software</mark> to <mark style="background: #FFB8EBA6;">manage and optimize connectivity across different locations</mark> (like <strong>branches</strong>, <strong>data centers</strong>, <strong>cloud</strong>) <mark style="background: #BBFABBA6;">over various transport links (<strong>MPLS</strong>, <strong>broadband</strong>, <strong>LTE</strong>)</mark>, <mark style="background: #FFB86CA6;">simplifying management, improving performance, and reducing costs compared to traditional hardware-centric WANs</mark>. <mark style="background: #CACFD9A6;">It centralizes control</mark>, creating a virtual network overlay for dynamic, policy-based traffic steering to ensure the best path for applications. 
#### backhaul 
Backhauling is routing all data from each location back to a central location, even if the ultimate destination for some traffic is another office or the internet.  This allows security policy to be enforced and traffic inspected consistently from central hubs. However, the practice is inefficient compared to current options. Performance can be difficult to maintain, and expense is added when private circuits must be upgraded.
#### service-level assurance
Service-level assurance involves guaranteeing specific <strong>performance standard</strong> such as <strong>uptime</strong>, <strong>response times</strong>, and <strong>resolution speed</strong> between a <strong>service provider</strong> and a <strong>client</strong>, often formalized in a Service Level Agreement (SLA).
#### latency
Latency refers to the time it takes for data packets to travel from a source to a destination. (measured in ms).
#### jitter
Jitter refers to the inconsistency of data packet arrival intervals or the variation in latency over time.
#### loss
Packet Loss is when data packets fail to reach their destination.
#### ethernet handoff
An Ethernet handoff is the physical interface (typically RJ-45 for copper or SFP for fiber) where an Internet Service Provider (ISP) delivers connectivity to a customer's router or firewall. 
It acts as the final termination point, allowing direct connection to a standard 10/100/1000 Mbps port without needing intermediate conversion devices
#### tenant
A tenant is a <strong>logical container</strong>, <strong>user group</strong>, or <strong>organization</strong> <mark style="background: #FFB86CA6;">that shares common access, policies, and resources within a shared infrastructure</mark> (like cloud, SD-WAN, or data centers) <mark style="background: #FFF3A3A6;">while remaining isolated from other tenants</mark>. It defines a security boundary or "perimeter" for managing network traffic, security rules, and user identities. 
#### inbound service 
Inbound customer service refers to <mark style="background: #ABF7F7A6;">the process of handling incoming requests, inquiries, or issues from customers</mark>. This can include answering phone calls, responding to emails, messages, or social media comments, and providing assistance or solutions to customers' concerns.
#### network telemetry
Network telemetry <mark style="background: #FFF3A3A6;">is the automated, real-time collection and analysis</mark> <mark style="background: #FFB86CA6;">of data from network devices (switches, routers, firewalls)</mark> <mark style="background: #BBFABBA6;">to monitor performance, security, and traffic patterns</mark>. It enables proactive management by pushing data—such as packet-level statistics or device health—to a central collector for rapid insights