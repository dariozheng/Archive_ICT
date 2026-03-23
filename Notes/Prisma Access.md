---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/sase
---
Palo Alto Networks <strong>Prisma Access</strong> is a leading cloud-delivered <mark style="background: #FF5582A6;">Security Service Edge (SSE) solution</mark> that provides comprehensive <mark style="background: #FFB86CA6;">Zero Trust network access (ZTNA)</mark>, <mark style="background: #FFF3A3A6;">web security</mark>, and <mark style="background: #BBFABBA6;">data protection</mark> for remote users, branches, and applications. Powered by AI-driven security, it secures traffic via the GlobalProtect VPN agent and offers integrated digital experience management (ADEM). 
# Licensing
# Service Connection 
<strong>Prisma Access</strong> leverages a combination of <mark style="background: #FFB8EBA6;"><strong>service connections</strong> (<strong>SCs</strong>)</mark> and <mark style="background: #FF5582A6;">Corporate Access Nodes (SC-CANs)</mark> <mark style="background: #FFF3A3A6;">to connect mobile users, and users at remote locations</mark>, <mark style="background: #FFB86CA6;">with headquarters (HQ) and data centers (DC)</mark>. 
<mark style="background: #BBFABBA6;">The service connection does not provide any security enforcement</mark> and <mark style="background: #ABF7F7A6;">does not support internet use from the data center location</mark>.

A <strong>service connection</strong> (<strong>SC</strong>) is an <mark style="background: #ADCCFFA6;"><strong>IPSec</strong> virtual private network (VPN)</mark> <mark style="background: #D2B3FFA6;">that connects a data center or headquarters site</mark> to <mark style="background: #CACFD9A6;">the Prisma Access infrastructure subnet</mark>.  
The component within the Prisma Access infrastructure that a service connection connects to is called a Corporate Access Node and referred to as the SC-CAN.

A service connection allows <mark style="background: #FFB8EBA6;">mobile users and users at remote locations</mark> t<mark style="background: #FFB86CA6;">o securely access private applications</mark> <mark style="background: #FFF3A3A6;">hosted in the data center</mark> and <mark style="background: #BBFABBA6;">enables connectivity from data centers</mark> <mark style="background: #ABF7F7A6;">to mobile users and remote networks</mark>.

In addition to providing access to resources at the data centers or headquarters locations, <mark style="background: #FFF3A3A6;">service connections can also be leveraged to facilitate communication amongst mobile users and users or resources on remote networks</mark>.  
This requires at least a minimally-configured service connection along with the appropriate licensing (Prisma Access Enterprise Edition and the Net Interconnect add-on).

<mark style="background: #FFB86CA6;">The number of service connections available to you depends on your license</mark>. <mark style="background: #BBFABBA6;">The following HQ, or data center, information needs to be gathered in order to set up service connections</mark>:
##### IPSec network information
Obtain the <mark style="background: #FFB8EBA6;">IPSec network information</mark> needed to set up the service connections:
- Configuration of <mark style="background: #FFF3A3A6;">IP addresses</mark> for the IPSec-capable firewall, router, or SD-WAN device <mark style="background: #FFF3A3A6;">connection</mark> at the corporate site
- <mark style="background: #FFB86CA6;">IPSec settings for terminating the primary VPN tunnel</mark> from Prisma Access to the IPSec-capable device on the corporate network
- <mark style="background: #FFF3A3A6;">IPSec settings for terminating the secondary VPN tunnel</mark> from Prisma Access to the IPSec-capable device on the corporate network
##### IP address information
Obtain the <mark style="background: #FFB8EBA6;">IP address information</mark> needed to set up the service connections:
- <mark style="background: #ABF7F7A6;">List of IP subnetworks at the site</mark>. The infrastructure subnet must not overlap with any existing subnet on the corporate network.
- <mark style="background: #BBFABBA6;">List of internal domains that Prisma Access must be able to resolve</mark>
- <mark style="background: #FFF3A3A6;">The IP address of a device that is highly available on the corporate network to which Prisma Access can send Internet Control Message Protocol (ICMP) ping requests for IPSec tunnel monitoring</mark>. Make sure that this address is reachable by ICMP from the entire Prisma Access infrastructure subnet.
- <mark style="background: #ADCCFFA6;">Network reachability settings for the service infrastructure subnet</mark>. Make the entire service infrastructure subnet reachable from the HQ or data center. Prisma Access uses IP addresses for all control-plan traffic from the subnet.
## IPsec Tunnels
IPSec is a secure <mark style="background: #BBFABBA6;">network protocol suite</mark> that <strong>authenticates</strong> and <strong>encrypts</strong> <mark style="background: #D2B3FFA6;">the packets of data that are sent over an IP network</mark>. IPSec is used by VPNs.
IPSec VPN tunnels are built between <mark style="background: #FF5582A6;">Prisma Access</mark> and <mark style="background: #ABF7F7A6;">locations</mark>, such as <mark style="background: #ABF7F7A6;">data centers</mark> and <mark style="background: #ABF7F7A6;">remote sites</mark>.
Prisma Access uses a <mark style="background: #FFB8EBA6;">route-based VPN</mark> to <mark style="background: #FF5582A6;">direct traffic to the appropriate network</mark>.

<mark style="background: #FFB86CA6;">Before a new service connection can be onboarded for Prisma Access</mark>, <mark style="background: #FFB8EBA6;">IPSec tunnels must be configured</mark>. 

All traffic flowing in and out of the <mark style="background: #BBFABBA6;">service connection</mark> <mark style="background: #BBFABBA6;">will traverse the IPSec tunnel</mark>. The remote networks will require an IPSec VPN tunnel, which will need to be configured prior to onboarding the remote network.
![[IPsec Tunnels Service Connection.png]]

A VPN connection that enables you to <mark style="background: #FFB8EBA6;">connect two local area networks (LANs)</mark> is called a [[Site-to-Site VPN - Palo Alto|site-to-site VPN]]. 

You can configure <strong>Prisma Access</strong> to connect the IPSec VPN tunnel to a <mark style="background: #FF5582A6;">Palo Alto Networks firewall</mark>, or to a <mark style="background: #FFB86CA6;">third-party security device</mark>, that is located at the remote site. <mark style="background: #FFF3A3A6;">Prisma Access implements a route-based VPN</mark>, but it also can interoperate with third-party, policy-based VPN devices.
### IKE Phases
The creation of the IPSec tunnel has two phases. 

In the first phase, the <strong>Internet Key Exchange</strong> (IKE) protocol <mark style="background: #FFB8EBA6;">authenticates the firewalls to each other and sets up a secure control channel</mark>. The first phase uses the <mark style="background: #FF5582A6;">IKE Crypto Profile</mark> for IKE negotiation. 

IKE phase 2 creates the tunnel that will encapsulate data traffic.
#### IKE Phase 1
![[IKE Phase 1 rewiew.png]]
In IKE phase 1, <mark style="background: #FFB86CA6;">each device is identified to the other by a peer ID</mark>. 

<mark style="background: #FFF3A3A6;">The ID usually is just the public IP address of the device</mark>. In situations where the public ID is not static, <mark style="background: #FFB86CA6;">this value can be replaced with a domain name or other text value</mark>. 

IKE phase 1 provides <strong>authentication</strong> <mark style="background: #FF5582A6;">of the endpoints of the tunnel</mark> and <mark style="background: #BBFABBA6;">creates a secure channel for the next phase of the VPN</mark>.

<mark style="background: #ABF7F7A6;">The five pieces of information passed during <strong>IKE phase 1</strong> are</mark> <mark style="background: #ADCCFFA6;">authentication method</mark>, <mark style="background: #D2B3FFA6;">Diffie-Hellman key</mark>, <mark style="background: #CACFD9A6;">symmetric key algorithm – bulk data encryption</mark>, <mark style="background: #FFB8EBA6;">hashing algorithm</mark>, and <mark style="background: #FF5582A6;">key lifetime</mark>.
#### IKE Phase 2
![[IKE Phase 2 rewiew.png]]
<strong>IKE phase 2</strong> concerns <mark style="background: #FFB8EBA6;">data traversing the tunnel</mark>. <mark style="background: #FF5582A6;">Each side of the tunnel</mark> <mark style="background: #FFB86CA6;">has a proxy ID</mark> <mark style="background: #BBFABBA6;">to identify the traffic that it sends</mark> and <mark style="background: #FFF3A3A6;">what it expects to receive</mark>. <mark style="background: #ABF7F7A6;">These IDs either can be a specific network range or a generic network of <strong>0.0.0.0/0</strong></mark>. In either case, <mark style="background: #ADCCFFA6;">for the tunnel to work, both sides need to know what the other side will be sending</mark>.

<mark style="background: #D2B3FFA6;">The five pieces of information passed during IKE phase 2 are</mark> <mark style="background: #CACFD9A6;">IPsec type or mode</mark>, <mark style="background: #FFB8EBA6;">Diffie-Hellman: PFS</mark>, <mark style="background: #FFB86CA6;">symmetric key algorithm – bulk data encryption</mark>, <mark style="background: #FFF3A3A6;">hashing algorithm</mark>, and <mark style="background: #CACFD9A6;">lifetime (before rekey)</mark>.
###  IPSec Templates
<strong>Prisma Access</strong> includes predefined <strong>IPSec templates</strong> for <mark style="background: #BBFABBA6;">common third-party IPSec</mark> and <mark style="background: #ADCCFFA6;">SD-WAN devices</mark>. These templates simplify the onboarding of service connections and remote network connections.

Templates for the following vendors are available: <mark style="background: #FFB8EBA6;">Cisco Integrated Services Routers (ISRs)</mark>, <mark style="background: #FF5582A6;">Cisco Adaptive Security Appliances (ASAs)</mark>, <mark style="background: #FFB86CA6;">Citrix</mark>, <mark style="background: #FFF3A3A6;">Prisma SD-WAN</mark>, <mark style="background: #BBFABBA6;">Riverbed</mark>, and <mark style="background: #ADCCFFA6;">Silver Peak</mark>. Modify predefined template settings to match your security requirements.
![[IPSec Templates palo alto.png]]
### Predefined IPSec and IKE Crypto Profiles
To help simplify the onboarding of IPSec tunnels, common third-party crypto profiles are provided. 

The configurations in these profiles are common settings. You must replace some of the placeholder values with the settings to match your security requirements. Remove any unneeded configurations and add settings to match the on-premises crypto settings.
![[Predefined IPSec and IKE Crypto Profiles.png]]
### IKE Gateway Configuration
