---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/sase
---
Palo Alto Networks <strong>Prisma Access</strong> is a leading cloud-delivered <strong><mark style="background: #FF5582A6;">Security Service Edge (SSE) solution</mark></strong> that provides comprehensive <mark style="background: #FFB86CA6;">Zero Trust Network Access (ZTNA)</mark>, <mark style="background: #FFF3A3A6;">SWG</mark>, <strong>CASB</strong>, and <mark style="background: #BBFABBA6;">DLP</mark> for <mark style="background: #ABF7F7A6;">remote users, branches, and applications</mark>. Powered by AI-driven security, it secures traffic via the GlobalProtect VPN agent and offers integrated digital experience management (ADEM). 

Core Topology Components:
- <mark style="background: #FFB86CA6;">Mobile Users</mark> (<strong>MU-SPN</strong>): <mark style="background: #FFB8EBA6;">Individual users connecting via the GlobalProtect app</mark> to nearby <mark style="background: #FFF3A3A6;">cloud gateways</mark>. <mark style="background: #ABF7F7A6;">These gateways act as the security enforcement point for remote employees</mark>.
- <mark style="background: #FFB8EBA6;">Remote Networks</mark> (<strong>RN-SPN</strong>): <mark style="background: #FFF3A3A6;">Branch offices</mark> or <mark style="background: #FFF3A3A6;">retail sites</mark> <mark style="background: #BBFABBA6;">that connect to Prisma Access via IPsec VPN tunnels</mark> <mark style="background: #ADCCFFA6;">from local routers or SD-WAN devices</mark>. <mark style="background: #ABF7F7A6;">Prisma Access provides the security stack for these sites</mark>.
- <mark style="background: #FF5582A6;">Service Connections</mark> (<strong>SC-CAN</strong>): <mark style="background: #D2B3FFA6;">Dedicated tunnels that link Prisma Access to your Private Data Centers or HQ where internal apps are hosted</mark>. Unlike other nodes, SC-CANs typically do not enforce security, assuming the data center already has its own firewall. 

The topology is designed so that all traffic—whether destined for the internet, a SaaS app, or another internal site—passes through the <strong>Prisma Access</strong> cloud for inspection. 

<mark style="background: #BBFABBA6;">Prisma Access can be managed with <strong>Strata Cloud Manager</strong> or <strong>Panorama</strong></mark>.
# Licensing
# Service Connection 
<strong>Prisma Access</strong> leverages a combination of <mark style="background: #FFB8EBA6;"><strong>service connections</strong> (<strong>SCs</strong>)</mark> and <mark style="background: #FF5582A6;">Corporate Access Nodes (SC-CANs)</mark> <strong><mark style="background: #FFF3A3A6;">to connect mobile users, and users at remote locations</mark>, <mark style="background: #FFB86CA6;">with headquarters (HQ) and data centers (DC)</mark></strong>. 

<mark style="background: #BBFABBA6;">The service connection does not provide any security enforcement</mark> and <mark style="background: #ABF7F7A6;">does not support internet use from the data center location</mark>.
![[Configured Service Connection Topology.png]]

A <strong>service connection</strong> (<strong>SC</strong>) is an <mark style="background: #ADCCFFA6;"><strong>IPSec</strong> virtual private network (VPN)</mark> <mark style="background: #D2B3FFA6;">that connects a data center or headquarters site</mark> to <mark style="background: #CACFD9A6;">the Prisma Access infrastructure subnet</mark>.  
The component within the Prisma Access infrastructure that a service connection connects to is called a Corporate Access Node and referred to as the SC-CAN.

A service connection allows <mark style="background: #FFB8EBA6;">mobile users and users at remote locations</mark> <mark style="background: #FFB86CA6;">to securely access private applications</mark> <mark style="background: #FFF3A3A6;">hosted in the data center</mark> and <mark style="background: #BBFABBA6;">enables connectivity from data centers</mark> <mark style="background: #ABF7F7A6;">to mobile users and remote networks</mark>.

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
### IKE Gateway
Prisma Access uses <strong>IKE gateways</strong> <mark style="background: #FFB8EBA6;">to connect to an on-premises device</mark> <mark style="background: #FF5582A6;">that initiates and terminates VPN connections</mark>. <mark style="background: #FFF3A3A6;">The IKE gateways negotiate the phase 1 portion of the IKE and IPSec VPN</mark>.
#### IKE Gateway Configuration #configuration 
Panorama provides several <mark style="background: #BBFABBA6;">IKE gateways templates</mark> for common third-party vendors, as well as a generic gateway to help simplify gateway configuration.

Predefined gateway templates provide a generic configuration for each vendor. To avoid potential connectivity issues, you must replace placeholder values in the preconfigured gateway templates with values that match your security requirements.
![[Configuration Using Predefined Templates.png]]

Before you can set up the VPN tunnel and send traffic between the IKE gateways, <mark style="background: #FFB8EBA6;">each peer must have a static or dynamic IP address or fully qualified domain name (FQDN)</mark>. <mark style="background: #FF5582A6;">The VPN peers use pre-shared keys or certificates to mutually authenticate each other</mark>.
![[Modify the IKE Gateway Predefined Template.png]]
The configuration shown above is for the <mark style="background: #FFB86CA6;">Prisma Access side of the IPSec VPN tunnel</mark>. A dynamic peer IP address type has been selected. <mark style="background: #FFF3A3A6;">When using dynamic IP addresses, you must configure the Peer Identification using a hostname, IP address, KEYID, or a user FQDN</mark>. 
<mark style="background: #BBFABBA6;">To complete the service connection configuration, you must also configure the other side of the IPSec VPN tunnel on the on-premises VPN device</mark>.

![[IKE Gateway Advanced Options.png]]
Enabling passive mode <mark style="background: #ABF7F7A6;">prevents the IPSec tunnel from initiating the connection request</mark>. Palo Alto Networks recommends that you <mark style="background: #ADCCFFA6;">let the <strong>on-premises VPN device</strong> initiate the connection</mark>.

The peers also must negotiate <mark style="background: #D2B3FFA6;">the mode for setting up the VPN tunnel</mark> and <mark style="background: #FF5582A6;">the SA lifetime</mark> in IKE phase 1. 
<mark style="background: #FFB86CA6;">Main mode protects the identity of the peers</mark> and <mark style="background: #FFF3A3A6;">is more secure because more packets are exchanged when the tunnel is set up</mark>. <mark style="background: #BBFABBA6;">Main mode is the recommended mode for IKE negotiation if both peers support it</mark>. <mark style="background: #ABF7F7A6;">Aggressive mode uses fewer packets to set up the VPN tunnel, so it is a faster but a less secure option</mark>.
### IPSec Tunnel #configuration 
In addition to configuring a gateway, you must configure an <strong>IPSec tunnel</strong>. <mark style="background: #FFF3A3A6;">IPSec tunnels establish and manage IPSec VPN tunnels</mark> between Prisma Access and the on-premises VPN device. <mark style="background: #BBFABBA6;">This is the phase 2 portion of the IKE/IPSec VPN setup</mark>.

Panorama provides several IPSec tunnel templates for common third-party vendors to help simplify IPSec tunnel configuration.
![[Configure Using Predefined Templates.png]]

The IPSec tunnel configuration allows you to <strong>authenticate</strong> and/or <strong>encrypt</strong> <mark style="background: #ABF7F7A6;">the data (IP packet) as it traverses the tunnel</mark>.
![[Modify the IPSec Tunnel Predefined Template.png]]
##### 1. Name
Provide a name for the IPSec tunnel.
##### 2. IKE Gateway
From drop-down list, select the **IKE Gateway** that you previously configured.
##### 3. IPSec Crypto Profile
Choose either a default [[Prisma Access#Predefined IPSec and IKE Crypto Profiles|IPSec crypto profile]] or a customized one that you have created.
##### 4. Enable Replay Protection
This option is enabled by default. To provide protection against replay attacks, leave the <strong>Enable Replay Protection</strong> checkbox selected.
##### 5. Add GRE Encapsulation
If you require <strong>type-of-service headers</strong> or <mark style="background: #FF5582A6;">GRE header encapsulation</mark>, select the <strong>Add GRE Encapsulation</strong> checkbox.
##### 6. Tunnel Monitor
Enable <strong>Tunnel Monitor</strong> to alert the administrator about tunnel failures and to provide automatic failover.

If you are setting up Prisma Access <mark style="background: #FFB8EBA6;">to work with a peer that supports <strong>policy-based VPN</strong></mark>, you must define <strong>proxy IDs</strong>. 
Devices that support policy-based VPN <mark style="background: #FFB86CA6;">use specific security rules and policies or access lists for permitting interesting traffic through an IPSec tunnel</mark>. <mark style="background: #FFF3A3A6;">These rules are referenced during quick mode negotiation</mark> and <mark style="background: #BBFABBA6;">are exchanged as proxy IDs in the first or the second message of the process</mark>.
###  IPSec Templates
<strong>Prisma Access</strong> includes predefined <strong>IPSec templates</strong> for <mark style="background: #BBFABBA6;">common third-party IPSec</mark> and <mark style="background: #ADCCFFA6;">SD-WAN devices</mark>. These templates simplify the onboarding of service connections and remote network connections.

Templates for the following vendors are available: <mark style="background: #FFB8EBA6;">Cisco Integrated Services Routers (ISRs)</mark>, <mark style="background: #FF5582A6;">Cisco Adaptive Security Appliances (ASAs)</mark>, <mark style="background: #FFB86CA6;">Citrix</mark>, <mark style="background: #FFF3A3A6;">Prisma SD-WAN</mark>, <mark style="background: #BBFABBA6;">Riverbed</mark>, and <mark style="background: #ADCCFFA6;">Silver Peak</mark>. Modify predefined template settings to match your security requirements.
![[IPSec Templates palo alto.png]]
### Predefined IPSec and IKE Crypto Profiles
To help simplify the onboarding of IPSec tunnels, common third-party crypto profiles are provided. 

The configurations in these profiles are common settings. You must replace some of the placeholder values with the settings to match your security requirements. Remove any unneeded configurations and add settings to match the on-premises crypto settings.
![[Predefined IPSec and IKE Crypto Profiles.png]]
## Service Connection #Configuration
To begin the process of creating a new service connection, navigate to <strong>Panorama > Cloud Services > Configuration > Service Connection</strong>.
### Private App NAT Support
Starting in Prisma Access Innovation v3.2, <mark style="background: #FFB8EBA6;">a subnet can be specified at one or more service connections that are used to perform network address translation (NAT)</mark> on traffic between Prisma Access, GlobalProtect mobile users, and private applications/resources at a data center. Options for this feature include the following:
##### Enable Data Traffic Source NAT
<mark style="background: #FFB86CA6;">Performs NAT on Mobile User IP Address pool addresses</mark> so t<mark style="background: #FFF3A3A6;">hat they are not advertised to the data center</mark>, and <mark style="background: #BBFABBA6;">only the subnets you specify at the service connections are advertised and routed in the data cente</mark>r.
##### Enable Infrastructure Traffic Source NAT
<mark style="background: #ABF7F7A6;">Performs NAT on addresses from the Infrastructure Subnet</mark> so that they are not advertised to the data center, and only those subnets you specify at the service connections are advertised and routed in the data center.
##### IP Pool 
<mark style="background: #ADCCFFA6;">Specify the IP address pool used to perform NAT on the mobile user IP address pool, Infrastructure Subnet, or both</mark>. Use a private IP (RFC 1918) subnet or a suitable subnet that is routable in your routing domain and does not overlap with the Mobile Users GlobalProtect IP address pool or the Infrastructure Subnet.
Enter a subnet between /25 and /32.
## Routing and QoS
In order for Prisma Access <mark style="background: #FFB8EBA6;">to route traffic to the HQ and data centers</mark>, <mark style="background: #FF5582A6;"><strong>routing information</strong> for the subnetworks that you want users to access must be provided</mark>. This can be done in three ways: <mark style="background: #FFB86CA6;">configuring static routing</mark>, <mark style="background: #FFF3A3A6;">creating a QoS Profile to prioritize business-critical traffic</mark>, or <mark style="background: #BBFABBA6;">configuring dynamic routing and Border Gateway Protocol (BGP)</mark>.
### Configuring Static Routing #configuration 
The first method is <mark style="background: #ABF7F7A6;">using static routing</mark> <mark style="background: #ADCCFFA6;">to identify the subnetworks, or individual IP addresses, at the data center or HQ</mark> <mark style="background: #FFF3A3A6;">that you want mobile users or remote sites to access</mark>.

The subnetworks at HQ, data centers, and remote network sites <mark style="background: #BBFABBA6;">must not overlap with each other</mark>, <mark style="background: #ADCCFFA6;">with the IP pools that you designated for Prisma Access for users</mark>, or <mark style="background: #D2B3FFA6;">with the infrastructure subnet</mark>. <mark style="background: #CACFD9A6;">If you are using static routes to route traffic to and from your HQ/DC</mark>, <mark style="background: #FFB8EBA6;">add the IP subnets or IP addresses that you want to secure at the branch</mark>. 

Note: If you make any changes to the IP subnets on your HQ/DC network, you must manually update the static routes. Additionally, if you configure both static routes and BGP routing, the static routes take precedence.

To configure static routing, navigate to <strong>Panorama > Cloud Services > Configuration > Service Connection > Onboarding > Add</strong>. On the <strong>Static Routes</strong> tab, click <strong>Add</strong>.![[Configuring Static Routing.png]]
### Creating a QoS Profile to Prioritize Business Critical Traffic #configuration 
The second approach to controlling throughput for service connections involves enabling QoS and creating a QoS Profile.

To configure Quality of Service (QoS) for the service connection, you will need to enable QoS  and then specify a QoS Profile. To enable QoS, navigate to **Panorama > Cloud Services > Configuration > Service Connection** and on the **QoS** tab, select **Enable** .
![[Creating a QoS Profile to Prioritize Business Critical Traffic.png]]

If you plan to configure Prisma Access security policy rules <mark style="background: #FFB8EBA6;">to apply QoS markings to ingress traffic</mark>, or <mark style="background: #FFB86CA6;">you have a device at the HQ/DC that marks ingress traffic</mark>, <mark style="background: #BBFABBA6;">you can shape the traffic egressing the site by defining a QoS Profile</mark>:
##### Add QoS Profile
Set bandwidth limits for the profile. Set the maximum throughput (in Mbps) for traffic leaving the HQ/DC service connection as the egress max. You can specify a value up to the maximum licensed bandwidth of your HQ/DC service connection. Set the guaranteed bandwidth as the Egress Guaranteed (in Mbps). Any traffic that exceeds the egress guaranteed value is the best effort but not guaranteed.
##### Define the QoS Classes for the Profile
There are up to eight definable QoS classes in a single QoS profile. Unless otherwise configured, traffic that does not match a QoS class is assigned a class of four. A QoS class determines the priority and bandwidth for traffic matching a QoS policy rule. You can use a profile to define each QoS class and then attach this profile to a policy rule.
##### Define Egress Max Value
The egress max value for a QoS class, or the combined egress max values for multiple QoS classes, must not exceed the egress max value for the QoS profile.
##### Define Egress Guaranteed Value
The guaranteed bandwidth assigned to the QoS class is not reserved for that class; unused bandwidth remains available to all traffic. Any class traffic that exceeds the egress guaranteed value is the best effort but not guaranteed.
### Configure the Dynamic Routing and BGP
The third method is using Border Gateway Protocol (BGP). 

If you want to enable BGP to dynamically route traffic to and from your HQ and data centers, you will need to provide the following BGP information for the eBGP router at the HQ/DC:
##### Branch Router AS Number
The autonomous system (AS) to which the eBGP router at the HQ/DC belongs. This is called the Peer AS.
##### Router ID
The IP address is assigned as the Router ID of the eBGP router on the HQ/DC network. This is called the Peer Address.
#### Dynamic Routing Configuration Settings
To use Dynamic Routing to advertise HQ/DC subnets, navigate to **Panorama > Cloud Services > Configuration > Service Connection**. In the Onboarding section, click **Add** and select the **BGP** tab. Click **Enable** and configure the following settings:
- **Add no-export community:** To add a no-export community for SC-CANs to the outbound prefixes from the eBGP peers at the customer premises equipment (CPE), set Add no-export community to Enabled Out. This capability is Disabled by default. 
- **Don’t Advertise Prisma Access Routes**: Select this option to prevent the Prisma Access BGP peer from forwarding routes into your organization’s network. 
- **Peer AS:** Enter the Peer AS, which is the autonomous system (AS) for your network.
- **Peer Address:** Enter the IP address assigned as the Router ID of the eBGP router on the data center/HQ network for which you're configuring this service connection. 
- **Local IP Address:** Enter the IP address that Prisma Access uses as its Local IP Address for BGP.
- **Secret and Confirm Secret:** Enter a secret password to authenticate BGP peer communications and enter it again to confirm. 
![[Dynamic Routing Configuration Settings.png]]
# Remote Networks
<strong>Remote networks</strong> are designed <mark style="background: #FFB8EBA6;">to secure users and devices</mark> <mark style="background: #FFB86CA6;">in remote network locations, such as branch offices or remote sites</mark>. 
To establish a secure connection to Prisma Access, the remote site requires either <mark style="background: #FFF3A3A6;">a <strong>Palo Alto Networks Next-Generation Firewall</strong> or a <strong>third-party IPSec-compliant device</strong></mark>, <mark style="background: #FFF3A3A6;">such as a software-defined wide area network (SD-WAN), that is capable of creating an IPSec tunnel</mark>.

<mark style="background: #BBFABBA6;">Remote networks are <strong>metered</strong>, which means that a specific amount of bandwidth is allocated to the compute locations</mark>, and there is a cost associated with this allocated bandwidth.

<strong>Remote networks</strong> connect <mark style="background: #ABF7F7A6;"><strong>offices</strong> that require connections to and from the <strong>Internet</strong> and <strong>Prisma Access</strong></mark>. They create a <strong>remote network security processing node</strong> (<strong>RN-SPN</strong>), <mark style="background: #FF5582A6;">which provides functionality similar to a Palo Alto Networks Next-Generation Platform</mark>.

When planning to connect remote networks to Prisma Access, you will need to <strong>know</strong> <mark style="background: #FFB86CA6;">how many sites will be onboarded</mark> and <mark style="background: #FFF3A3A6;">the bandwidth requirements for each of those sites</mark>.
This information will help you determine connectivity requirements, such as <mark style="background: #BBFABBA6;">how to route traffic through Prisma Access</mark>. 
You should also consider <mark style="background: #ABF7F7A6;">what type of applications that will pass through Prisma Access</mark> to help you determine <mark style="background: #ADCCFFA6;">what Security policy rules will be needed</mark>. When <strong>determining Security policy rules</strong>, consider your <mark style="background: #D2B3FFA6;">threat profile configuration</mark> and <mark style="background: #CACFD9A6;">plan to apply the same threat, URL, and WildFire scanning to all rules for a consistent threat-mitigation strategy across all traffic</mark>.
![[Planning Considerations for Remote Networks.png]]
##### deployment planning phase
During this deployment planning phase, consider the following and gather as much information as you can to prepare for onboarding
###### Establish Service Connections to Corporate Resource
If your remote network <mark style="background: #FFB8EBA6;">requires access to infrastructure or resources in your headquarters (HQ) or a data center</mark>, <mark style="background: #FFB86CA6;">create a Prisma Access service connection to the corporate site</mark>. If the remote network location is autonomous and doesn’t need to access the infrastructure at other locations, you don’t need to do this.
###### Choose the Right Prisma Access Locations
When users at your branch office connect to Prisma Access, the Prisma Access location you choose determines the language in which content from the internet is served. To ensure the optimal experience for your users, <mark style="background: #FFF3A3A6;">select the region (country and, if applicable, state) and location as your branch office</mark>. If a location is not available in the same region as your branch office, choose a location that uses the same language as the majority of the users at the site.
###### Identify Subnets to Secure
For Prisma Access to route traffic to your remote networks, you’ll need to <mark style="background: #BBFABBA6;">provide routing information for the subnetworks</mark> that you want Prisma Access to secure.
###### Allocate Bandwidth for Remote Networks
To form a compute location, you would need at least two (often more) geographically near Prisma Access locations. <mark style="background: #ABF7F7A6;">This is the level at which you allocate bandwidth instead of allocating bandwidth for individual Prisma Access locations or specific remote network sites</mark>.
###### Define IPSec Termination Nodes for Compute Location
IPSec termination nodes allow you to associate remote networks with compute locations. When you onboard a remote network, <mark style="background: #ADCCFFA6;">select an IPSec termination node for the remote network that correlates to the compute location</mark>.
###### Avoid Overlapping Subnets
As a general rule, <mark style="background: #D2B3FFA6;">you cannot have any overlapping subnets within a Prisma Access instance</mark>. This means that the subnets for all remote network locations, service connections, and Prisma Access for mobile users' IP address pools must be unique and non-overlapping.
## Remote Network #configuration 
Once you have planned for your remote networks, you can begin the configuration process. This involves <mark style="background: #FFB8EBA6;">onboarding the remote network</mark>, <mark style="background: #FF5582A6;">connecting the remote network site to Prisma Access</mark>, and <mark style="background: #FFB86CA6;">enabling routing and quality of service (QoS)</mark> for the remote network.

To onboard a remote network, navigate to <strong>Panorama > Cloud Services > Configuration > Remote Networks</strong> and edit the settings by clicking the gear icon in the <strong>Settings</strong> area.  In the <strong>Templates</strong> section, add any templates that contain configuration you want to push to Prisma Access for networks and select the <strong>Device Group</strong> to which you wish to apply the configurations. 
![[Configuring the Remote Networks.png]]
##### Enable ECMP Load Balancing for BGP
If you plan to use Border Gateway Protocol (<strong>BGP</strong>) for dynamic routing, enable <strong>ECMP Load Balancing</strong> so that <mark style="background: #FF5582A6;">the remote network site can use up to four IPSec tunnels to connect to the compute location</mark>.

<mark style="background: #ADCCFFA6;">BGP is required for ECMP load balancing</mark>; additionally, <mark style="background: #FFB86CA6;">QoS and static routes are not supported</mark>. 

With <strong>remote networks</strong>, each <strong>compute location</strong> must <mark style="background: #BBFABBA6;">have a minimum bandwidth of 50Mbps</mark>. <mark style="background: #ABF7F7A6;">Therefore, when using ECMP load balancing, specify a minimum bandwidth of 50 Mbps</mark>. <mark style="background: #ADCCFFA6;">Prisma Access divides the bandwidth you select by the number of tunnels</mark>; for example, <mark style="background: #D2B3FFA6;">if you specify 300 Mbps and add four tunnels, each tunnel carries 75 Mbps</mark>. If one of the tunnels goes down, your network connection will now carry 225 Mbps instead of 300 Mbps. 
### Primary Tunnel
<mark style="background: #CACFD9A6;">The first tunnel you create is the <strong>primary tunnel</strong> for the remote network site</mark>. 

You can then repeat this workflow to optionally set up a secondary tunnel. When both tunnels are up, the primary tunnel takes priority over the secondary tunnel. If the primary tunnel for a remote network site goes down, the remote network falls back to the secondary tunnel until the primary tunnel comes back up. 

To establish secure connections between your remote network sites and Prisma Access, <mark style="background: #FFB8EBA6;">you must create an IPSec tunnel from your branch IPSec device to Prisma Access</mark>.
#### Add a Primary IPSec Virtual Private Network (VPN) Tunnel
IPSec tunnels establish and manage IPSec VPN tunnels between Prisma Access and your on-premises VPN device. Panorama provides several preconfigured third-party IPSec tunnels to simplify configuration, or you can click **Add** to begin adding a new one.
![[Add a Primary IPSec Virtual Private Network (VPN) Tunnel.png]]
### Remote Network Onboarding 
To add a new remote network site to Prisma Access, start by specifying the location and defining the amount of bandwidth to allocate to the connection.

Navigate to **Panorama > Cloud Services > Configuration > Remote Networks > Onboarding** to onboard a remote network.
![[Remote Network Onboarding.png]]
### Secure Inbound Access 
If your organization hosts <mark style="background: #FF5582A6;">internet-accessible applications</mark> at a remote network site, <mark style="background: #FFF3A3A6;">providing access to those applications exposes your network to all the threats the open internet poses</mark>. Use Secure Inbound Access to secure the network. 

Secure inbound access features:
- You <strong>cannot</strong> modify an existing remote network to provide secure inbound access. 
- The inbound access feature <mark style="background: #FFB86CA6;">is not available on remote networks that use ECMP load balancing</mark>. 
- <mark style="background: #BBFABBA6;">Application port translation is not supported</mark>. 
- <mark style="background: #ADCCFFA6;">Do not use remote network inbound access with traffic forwarding rules that have service connections</mark>. 
- <mark style="background: #D2B3FFA6;">User-ID and application authentication are not supported</mark>.

Remote networks that are configured for <strong>secure inbound access</strong> <mark style="background: #FF5582A6;">can only be used for that purpose</mark>. <mark style="background: #BBFABBA6;">For <strong>inbound</strong> and <strong>outbound</strong> access at a remote network site, create two <strong>remote network</strong> sites in the same location</mark>—<mark style="background: #ADCCFFA6;">one for inbound access</mark> and <mark style="background: #ABF7F7A6;">one for outbound access</mark>. Customer routing at the branch needs <mark style="background: #D2B3FFA6;">to ensure symmetrical flows if both inbound and outbound access is required</mark>. 

<mark style="background: #FFB8EBA6;">In this example, User 1 uses Remote Network 1 for inbound access to www.example.com, while User 2 uses Remote Network 2 for outbound internet access from the remote network location</mark>. 
![[Guidelines for Secure Inbound Access.png]]

