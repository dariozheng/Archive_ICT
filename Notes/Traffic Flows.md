---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
created: 2026-01-01T21:53:41+01:00
modified: 2026-01-02T08:07:04+01:00
---
# Network Perimeters
The network perimeter is the <strong>bolder</strong> between an org’s <strong>secured internal network</strong> and <strong>unsecured external network</strong>.

<mark style="background: #FFF3A3A6;">Within the perimeter, the organization has administrative control over devices</mark>, while outside, it does not.

# Traffic Flow Directions
The two primary traffic flow directions in a data center are <strong>North-South</strong> and <strong>East-West</strong>.

## North-South Traffic
Refers to data <strong>entering</strong> or <strong>leaving</strong> the network perimeter.

<strong>Exiting the data center</strong> is <strong>Northbound</strong>, while <strong>traffic entering</strong> is <strong>Southbound</strong>.

Examples include browsing websites, sending emails, and API commands.

## East-West Traffic
Occurs <strong>within</strong> the network perimeter, between different data center components.

Like communication between endpoints and servers or between endpoints in the same subnet.

# Traffic Flow Directions in virtual data centers
![[East-West Versus North-South Protection.png]]
### North-South Protection
North-south refers to data packets that move in and out of the virtualized environment from the host network or a corresponding traditional data center. 
<mark style="background: #FFF3A3A6;"><strong>North-south traffic</strong> is secured by one or more physical form factor perimeter edge firewalls. </mark>
<mark style="background: #FF5582A6;">The edge firewall usually is a high-throughput appliance working in high availability active/passive (or active/active) mode to increase resiliency</mark>. 
<mark style="background: #FFB8EBA6;">It controls all the traffic reaching into the data center and authorizes only allowed and “clean” packets to flow into the virtualized environment</mark>. 

### East-West Protection
East-west refers to data packets moving between virtual workloads entirely within the private cloud. 
<mark style="background: #BBFABBA6;">East-west traffic is protected by a local, virtualized firewall instantiated on each hypervisor</mark>. 
East-west firewalls are inserted transparently into the application infrastructure and do not necessitate a redesign of the logical topology.
East-west protection provides the following benefits:
- <strong>Application Authorization</strong>: Authorizes only allowed applications to flow inside the data center, between VMs
- <strong>Lateral Reduction</strong>: Reduces lateral threat movement when a front-end workload has been compromised (the attacker breaches the front-end server by using a misconfigured application or unpatched exploit)
- <strong>Threat Prevention</strong>: Stops known and unknown threats that are sourced internally within the data center
- <strong>Data Protection</strong>: Protects against data theft by leveraging data and file filtering capability and blocking anti-spyware communications to the external world
- <strong>Visibility Optimization:</strong> An added benefit of using virtual firewalls for east-west protection is <mark style="background: #FFB86CA6;">the unprecedented traffic and threat visibility that the virtualized security device can now provide</mark>. <mark style="background: #ABF7F7A6;">After traffic logs and threat logs are turned on, VM-to-VM communications and malicious attacks become visible</mark>. <mark style="background: #D2B3FFA6;">This virtual data center awareness allows security teams to optimize policies and enforce cyberthreat protection</mark> (for example, IPS, anti-malware, file blocking, data filtering, and DoS protection) <mark style="background: #D2B3FFA6;">where needed</mark>.