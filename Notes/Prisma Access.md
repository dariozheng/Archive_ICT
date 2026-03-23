---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/sase
---

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
