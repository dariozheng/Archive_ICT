---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/sase
  - tobecompleted
icon: SiPaloaltonetworks
iconColor: "#F04E23"
---
Palo Alto Networks <strong>Prisma Access</strong> is a leading cloud-delivered <strong><mark style="background: #FF5582A6;">Security Service Edge (SSE) solution</mark></strong> that provides comprehensive <mark style="background: #FFB86CA6;">Zero Trust Network Access (ZTNA)</mark>, <mark style="background: #FFF3A3A6;">SWG</mark>, <strong>CASB</strong>, and <mark style="background: #BBFABBA6;">DLP</mark> for <mark style="background: #ABF7F7A6;">remote users, branches, and applications</mark>. Powered by AI-driven security, it secures traffic via the GlobalProtect VPN agent and offers integrated digital experience management (ADEM). 

Core Topology Components:
- <mark style="background: #FFB86CA6;">Mobile Users</mark> Security Processing Node (<strong>MU-SPN</strong>): <mark style="background: #FFB8EBA6;">Individual users connecting via the <strong>GlobalProtect</strong> app</mark> to nearby <mark style="background: #FFF3A3A6;">cloud gateways</mark>. <mark style="background: #ABF7F7A6;">These gateways act as the security enforcement point for remote employees</mark>.
- <mark style="background: #FFB8EBA6;">Remote Networks</mark> Security Processing Node (<strong>RN-SPN</strong>): <mark style="background: #FFF3A3A6;">Branch offices</mark> or <mark style="background: #FFF3A3A6;">retail sites</mark> <mark style="background: #BBFABBA6;">that connect to Prisma Access via IPsec VPN tunnels</mark> <mark style="background: #ADCCFFA6;">from local routers or SD-WAN devices</mark>. <mark style="background: #ABF7F7A6;">Prisma Access provides the security stack for these sites</mark>.
- <mark style="background: #FF5582A6;">Service Connections</mark> Corporate Access Node (<strong>SC-CAN</strong>): <mark style="background: #D2B3FFA6;">Dedicated tunnels that link Prisma Access to your Private Data Centers or HQ where internal apps are hosted</mark>. Unlike other nodes, SC-CANs typically do not enforce security, assuming the data center already has its own firewall. 

The topology is designed so that all traffic—whether destined for the internet, a SaaS app, or another internal site—passes through the <strong>Prisma Access</strong> cloud for inspection. 

<mark style="background: #BBFABBA6;">Prisma Access can be managed with <strong>Strata Cloud Manager</strong> or <strong>Panorama</strong></mark>.
# Licensing
# Service Connection 
<strong>Prisma Access</strong> leverages a combination of <mark style="background: #FFB8EBA6;"><strong>service connections</strong> (<strong>SCs</strong>)</mark> and <mark style="background: #FF5582A6;"><strong>Corporate Access Nodes (SC-CANs)</strong></mark> <strong><mark style="background: #FFF3A3A6;">to connect mobile users, and users at remote locations</mark>, <mark style="background: #FFB86CA6;">with headquarters (HQ) and data centers (DC)</mark></strong>. 

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
From drop-down list, select the <strong>IKE Gateway</strong> that you previously configured.
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

To configure Quality of Service (QoS) for the service connection, you will need to enable QoS  and then specify a QoS Profile. To enable QoS, navigate to <strong>Panorama > Cloud Services > Configuration > Service Connection</strong> and on the <strong>QoS</strong> tab, select <strong>Enable</strong> .

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
To use Dynamic Routing to advertise HQ/DC subnets, navigate to <strong>Panorama > Cloud Services > Configuration > Service Connection</strong>. In the Onboarding section, click <strong>Add</strong> and select the <strong>BGP</strong> tab. Click <strong>Enable</strong> and configure the following settings:
- <strong>Add no-export community:</strong> To add a no-export community for SC-CANs to the outbound prefixes from the eBGP peers at the customer premises equipment (CPE), set Add no-export community to Enabled Out. This capability is Disabled by default. 
- <strong>Don’t Advertise Prisma Access Routes</strong>: Select this option to prevent the Prisma Access BGP peer from forwarding routes into your organization’s network. 
- <strong>Peer AS:</strong> Enter the Peer AS, which is the autonomous system (AS) for your network.
- <strong>Peer Address:</strong> Enter the IP address assigned as the Router ID of the eBGP router on the data center/HQ network for which you're configuring this service connection. 
- <strong>Local IP Address:</strong> Enter the IP address that Prisma Access uses as its Local IP Address for BGP.
- <strong>Secret and Confirm Secret:</strong> Enter a secret password to authenticate BGP peer communications and enter it again to confirm. 

![[Dynamic Routing Configuration Settings.png]]

# Remote Networks
<strong>Remote networks</strong> are designed <mark style="background: #FFB8EBA6;">to secure users and devices</mark> <mark style="background: #FFB86CA6;">in remote network locations, such as branch offices or remote sites</mark>. 
To establish a secure connection to Prisma Access, the remote site requires either <mark style="background: #FFF3A3A6;">a <strong>Palo Alto Networks Next-Generation Firewall</strong> or a <strong>third-party IPSec-compliant device</strong></mark>, <mark style="background: #FFF3A3A6;">such as a software-defined wide area network (SD-WAN), that is capable of creating an IPSec tunnel</mark>.

<mark style="background: #BBFABBA6;">Remote networks are <strong>metered</strong>, which means that a specific amount of bandwidth is allocated to the compute locations</mark>, and there is a cost associated with this allocated bandwidth.

<strong>Remote networks</strong> connect <mark style="background: #ABF7F7A6;"><strong>offices</strong> that require connections to and from the <strong>Internet</strong> and <strong>Prisma Access</strong></mark>. 
<mark style="background: #FFB8EBA6;">They create a <strong>Remote Network Security Processing Node</strong> (<strong>RN-SPN</strong>)</mark>, <mark style="background: #FF5582A6;">which provides functionality similar to a Palo Alto Networks Next-Generation Platform</mark>.

When planning to connect remote networks to Prisma Access, you will need to <strong>know</strong> <mark style="background: #FFB86CA6;">how many sites will be onboarded</mark> and <mark style="background: #FFF3A3A6;">the bandwidth requirements for each of those sites</mark>.
This information will help you determine connectivity requirements, such as <mark style="background: #BBFABBA6;">how to route traffic through Prisma Access</mark>. 
You should also consider <mark style="background: #ABF7F7A6;">what type of applications that will pass through Prisma Access</mark> to help you determine <mark style="background: #ADCCFFA6;">what Security policy rules will be needed</mark>. When <strong>determining Security policy rules</strong>, consider your <mark style="background: #D2B3FFA6;">threat profile configuration</mark> and <mark style="background: #CACFD9A6;">plan to apply the same threat, URL, and WildFire scanning to all rules for a consistent threat-mitigation strategy across all traffic</mark>.

![[Planning Considerations for Remote Networks.png]]

##### Deployment Planning Phase
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
IPSec tunnels establish and manage IPSec VPN tunnels between Prisma Access and your on-premises VPN device. Panorama provides several preconfigured third-party IPSec tunnels to simplify configuration, or you can click <strong>Add</strong> to begin adding a new one.

![[Add a Primary IPSec Virtual Private Network (VPN) Tunnel.png]]

### Remote Network Onboarding 
<mark style="background: #D2B3FFA6;">To add a new remote network site to Prisma Access</mark>, start by specifying the location and defining the amount of bandwidth to allocate to the connection.

Navigate to <strong>Panorama > Cloud Services > Configuration > Remote Networks > Onboarding</strong> to onboard a remote network.

![[Remote Network Onboarding.png]]

### Secure Inbound Access 
If your organization hosts <mark style="background: #FF5582A6;">internet-accessible applications</mark> at a remote network site, <mark style="background: #FFF3A3A6;">providing access to those applications exposes your network to all the threats the open internet poses</mark>. 

<strong>Secure Inbound Access</strong> is a specific feature within Prisma Access designed <mark style="background: #FFB86CA6;">to protect traffic initiated from the internet or external sources</mark> <mark style="background: #BBFABBA6;">to applications hosted at a branch or remote site</mark>.

Secure inbound access features:
- You <strong>cannot</strong> modify an existing remote network to provide secure inbound access. 
- The inbound access feature <mark style="background: #FFB86CA6;">is not available on remote networks that use ECMP load balancing</mark>. 
- <mark style="background: #BBFABBA6;">Application port translation is not supported</mark>. 
- <mark style="background: #ADCCFFA6;">Do not use remote network inbound access with traffic forwarding rules that have service connections</mark>. 
- <mark style="background: #D2B3FFA6;">User-ID and application authentication are not supported</mark>.

Remote networks that are configured for <strong>secure inbound access</strong> <mark style="background: #FF5582A6;">can only be used for that purpose</mark>. <mark style="background: #BBFABBA6;">For <strong>inbound</strong> and <strong>outbound</strong> access at a remote network site, create two <strong>remote network</strong> sites in the same location</mark>—<mark style="background: #ADCCFFA6;">one for inbound access</mark> and <mark style="background: #ABF7F7A6;">one for outbound access</mark>. Customer routing at the branch needs <mark style="background: #D2B3FFA6;">to ensure symmetrical flows if both inbound and outbound access is required</mark>. 

<mark style="background: #FFB8EBA6;">In this example, User 1 uses Remote Network 1 for inbound access to www.example.com, while User 2 uses Remote Network 2 for outbound internet access from the remote network location</mark>. 

![[Guidelines for Secure Inbound Access.png]]

<strong>Prisma Access</strong> for remote networks allows <strong>outbound access</strong> to <mark style="background: #ABF7F7A6;">internet-connected applications</mark>. In some cases, your organization might need to provide <mark style="background: #BBFABBA6;">inbound access</mark> <mark style="background: #FFB86CA6;">to an application or website at a remote site</mark> and <mark style="background: #ADCCFFA6;"><strong>secure access</strong> to that application for any internet-connected user</mark>—not just users who are protected by Prisma Access.
#### Secure Inbound Access #configuration 
Follow these steps to make an application accessible from a remote network site to all internet-connected users.

Go to <strong>Panorama > Cloud Services > Configuration > Remote Networks</strong>, and select <strong>Inbound Access Remote Networks</strong>. Then, click <strong>Add</strong>.

![[Secure Inbound Access.png]]

Specify the following settings for the inbound access remote network connection:
- Provide a <strong>Name</strong> for your inbound access
- Specify the <strong>Location</strong> for your Prisma Access
- Set a <strong>Bandwidth</strong>
- Select the <strong>Number of Public IPs</strong> you want to use for the applications, either five or ten
- Select the <strong>IPSec Tunnel</strong> to use with the inbound access connection.

![[Secure Inbound Access2.png]]

Select the <strong>Inbound Access</strong> tab and click <strong>Add</strong> to add the inbound access applications for which you want to secure access. This option displays additional fields in a table.

![[Secure Inbound Access3.png]]

In the table, provide a suitable name for your inbound access application. Enter the <strong>Private IP</strong> address where your Prisma Access environment is running. Set the <strong>Protocol</strong> to <strong>TCP</strong> and provide a <strong>Port</strong>. 
Click <strong>OK</strong> to save your changes.![[Secure Inbound Access4.png]]

#### Secure Inbound Access Deployments
Here are inbound access examples, along with the IP addresses that Prisma Access assigns in various deployments.

In this configuration example, you <mark style="background: #FFF3A3A6;">enable inbound access for an application (www.example.com) at a remote network site</mark>. <mark style="background: #FFF3A3A6;">Then assign an IP address of 10.10.10.2, a port of 443, and a protocol of TCP to the application</mark>. <mark style="background: #FFB86CA6;">You then enter these values in Prisma Access when you configure inbound access</mark>. After you save and commit your changes, <mark style="background: #FFF3A3A6;">Prisma Access assigns a public IP address to the application you defined—in this case, 52.1.1.1</mark>.
##### Source Network Address Translation (NAT) Enabled
The following figure shows the traffic flow from users to applications. <mark style="background: #BBFABBA6;">Since source NAT is enabled, the source IP address in the routing table changes from the IP of the user’s device (34.1.1.1) to the remote network’s EBGP routing address. (172.1.1.1)</mark>.

![[Secure Inbound Access Deployments 1.png]]

##### Source NAT Enabled: Return Traffic
With source NAT enabled, you can clearly see the return path of the traffic.

![[Secure Inbound Access Deployments 2.png]]

##### Source NAT Disabled
If you disable source NAT, Prisma Access still performs destination NAT, but the source IP address of the request is unchanged.

![[Secure Inbound Access Deployments 3.png]]

##### Source NAT Disabled: Return Traffic
In this example, you can clearly see that the return address and the destination address for all of the routing tables is the user's IP address (34.1.1.1).

![[Secure Inbound Access Deployments 4.png]]

### Connect a Remote Network to Prisma Access #configuration 
Each remote network connection requires an IPSec VPN tunnel to Prisma Access. You must select an IPSec VPN tunnel when you onboard a remote network, so configure the tunnel before you configure the remote network.

A <mark style="background: #FF5582A6;">remote network security processing node</mark> (<strong>RN-SPN</strong>) <mark style="background: #FFB86CA6;">can accommodate up to 1,000 Mbps aggregated bandwidth before spawning an additional RN-SPN in a single compute location</mark>. <mark style="background: #ABF7F7A6;">More than one remote network going to the same location may share the same RN-SPN, but their total aggregated bandwidth is limited to 1,000 Mbps on the shared RN-SPN</mark>.
#### IKE Options
Based on the <mark style="background: #FF5582A6;">IPSec device type</mark> you selected, Prisma Access provides a recommended set of ciphers and a key lifetime for the IKE Phase 1 key exchange process.

You can use the recommended settings or customize the settings as needed for your environment. The following are recommended settings:
- Select an IKE Protocol Version for your branch device to use for IKE negotiation.
- Add an IKEv1 Crypto Profile to customize the IKE crypto settings.
- Enable IKE Passive Mode.
- IKE NAT Traversal is turned on by default.
##### IKE Crypto Settings
###### Encryption
Specify the encryption algorithm used in the IKE security association (SA) negotiation. Prisma Access supports the following encryption algorithms:
- 3des (168 bits)
- aes-128-cbc (128 bits)
- aes-192-cbc (192 bits)
- aes-256-cbc (256 bits)
- des (56 bits)
You can also select null (no encryption).
###### Authentication
Specify the authentication algorithm used in the IKE SA negotiation. Prisma Access supports the following authentication algorithms:
- sha1 (160 bits)
- sha256 (256 bits) 
- sha384 (384 bits) 
- sha512 (512 bits)
- md5 (128 bits)x
You can also select null (no authentication).
###### DH Group
Specify the Diffie-Hellman (DH) groups used to generate symmetrical keys for IKE in the IKE SA negotiation. The Diffie-Hellman algorithm uses the private key of one party and the public key of the other to create a shared secret, which is an encrypted key that both VPN tunnel peers share. Prisma Access supports the following DH groups:
- Group 1 (768 bits)
- Group 2 (1024 bits-default)
- Group 5 (1536 bits)
- Group 14 (2048 bits)
- Group 19 (256-bit elliptic curve group)
- Group 20 (384-bit elliptic curve group)
For the strongest security, select the group with the highest number.
###### Lifetime 
<mark style="background: #FFF3A3A6;">Specify the unit and amount of time for which the IKE Phase 1 key is valid</mark> (default is 8 hours). For IKEv1, the security association (SA) is not actively re-keyed before the key lifetime expires. 

<mark style="background: #BBFABBA6;">The IKEv1 Phase 1 re-key triggers only when the SA expires</mark>. <mark style="background: #ADCCFFA6;">For IKEv2, the SA must be re-keyed before the key lifetime expires</mark>. If the SA is not re-keyed upon expiration, the SA must begin a new Phase 1 key.
###### IKEv2 Authentication Multiple
Define the multiplier value (range: 0 to 50; default: 0) for the key lifetime to calculate the authentication count. The authentication count represents the number of times the security processing node can execute the IKEv2 IKE SA re-key before needing to initiate IKEv2 re-authentication. By default, the re-authentication feature is disabled with a value of 0.
#### IPSec Options 
Based on the IPSec device type you selected, Prisma Access provides a recommended set of IPSec protocol and key lifetime settings. You can customize the IPsec Crypto Profile to define how data is secured within the tunnel.

Secure the data that traverses the VPN tunnel. The Encapsulating Security Payload (ESP) protocol encrypts the data, authenticates the source, and verifies the data integrity. The Authentication Header (AH) protocol authenticates the source and verifies the data integrity.
#### Verify the Status of Remote Networks
After you have configured the IPSec VPN device on the remote network, verify the tunnel status.

To check the status of the remote networks, navigate to <strong>Panorama > Cloud Services > Status > Status</strong> to verify that the remote network connections have been successfully deployed. The <strong>Deployment Status</strong> allows you to view the progress of onboarding and deployment jobs before they complete, as well as see more information about the status of completed jobs.

If there are errors or warnings, review the system log and local logs on the remote network device. Resolve issues before proceeding with the configuration and then continue adding remote networks as needed.

![[Verify the Status of Remote Networks.png]]

# Mobile Users and GlobalProtect
<strong>GlobalProtect</strong> <mark style="background: #FFB8EBA6;">provides an infrastructure to secure</mark> <strong>mobile workforce networking</strong>. 
GlobalProtect enables secure access for all users, regardless of what endpoints they are using or where they are located.

GlobalProtect builds on familiar mobile security technology: <mark style="background: #CACFD9A6;">the remote-access virtual private network (VPN)</mark>. <mark style="background: #FF5582A6;">You can use <strong>GlobalProtect</strong> as a replacement for a traditional VPN gateway</mark>. This eliminates the complexity and headaches of administering a standalone, third-party VPN gateway.
## GlobalProtect Components
A GlobalProtect deployment consists of three major components: 
##### GlobalProtect Portal
The portal provides <mark style="background: #FFF3A3A6;">management functions for your GlobalProtect infrastructure</mark>. 

Every endpoint that participates in the GlobalProtect network <mark style="background: #BBFABBA6;">receives configuration information from the portal</mark>, <mark style="background: #ABF7F7A6;">including information about available gateways</mark> as well as <mark style="background: #ADCCFFA6;">any client certificates that may be required to connect to the GlobalProtect gateway(s)</mark>. 

In addition, <mark style="background: #D2B3FFA6;">the portal controls the behavior and distribution of the GlobalProtect app software to both macOS and Windows endpoints</mark>. (On mobile endpoints, the GlobalProtect app is distributed through the Apple App Store for iOS endpoints, Google Play for Android endpoints and Chromebooks, and the Microsoft Store for Windows 10 UWP endpoints.)
<mark style="background: #CACFD9A6;">If you are using the <strong>Host Information Profile (HIP)</strong> feature</mark>, <mark style="background: #FFB8EBA6;">the portal also defines what information to collect from the host</mark>, including any custom information you require. <mark style="background: #FF5582A6;">You can set up access to the <strong>GlobalProtect Portal</strong> on an interface on any Palo Alto Networks next-generation firewall</mark>.

Although <mark style="background: #FFB86CA6;">there can be only one portal</mark>, <mark style="background: #FFF3A3A6;">the portal is not a single point of failure</mark>: <mark style="background: #FF5582A6;">even if the portal is not reachable, clients will use their cached configuration to connect to the gateways</mark>. <mark style="background: #D2B3FFA6;">When the portal is unreachable, you cannot install a new client or distribute configuration changes to existing clients</mark>. To resolve this issue, <mark style="background: #ADCCFFA6;">re-establish the connection to the portal or redirect clients to a standby portal</mark>. <mark style="background: #CACFD9A6;">This redirection can be executed by changing the portal's DNS record</mark>.
##### GlobalProtect Gateway
The <strong>gateway</strong> provides <mark style="background: #FFB86CA6;">security enforcement </mark>for <mark style="background: #FFF3A3A6;">traffic from GlobalProtect apps</mark>. 

Additionally, if the <strong>HIP</strong> feature is enabled, <mark style="background: #BBFABBA6;">the gateway generates a HIP report from the raw host data the apps submit</mark>, and this information can be used in policy enforcement. 

<mark style="background: #ABF7F7A6;">You can configure different types of gateways</mark> to provide <mark style="background: #ADCCFFA6;">secure access for your remote users</mark>, as well <mark style="background: #D2B3FFA6;">as apply Security policy enforcement for access to internal resources</mark>.
<mark style="background: #CACFD9A6;">You can configure a <strong>GlobalProtect gateway</strong> on an interface on any Palo Alto Networks Next-Generation Firewall</mark>. <mark style="background: #FFB8EBA6;">You can run both a gateway and a portal on the same firewall</mark>, or you can have multiple distributed gateways throughout your enterprise.
##### GlobalProtect App
The <strong>GlobalProtect app software</strong> <mark style="background: #FF5582A6;">runs on endpoints</mark> and <mark style="background: #FFB86CA6;">enables access to your network resources through the GlobalProtect portals and gateways that you have deployed</mark>.

The GlobalProtect app for Windows and macOS endpoints is deployed from the GlobalProtect portal.

The GlobalProtect app for mobile endpoints (iOS, Android, and Windows UWP) is available through the official store for the endpoint—the Apple App Store for iOS, Google Play for Android, and the Microsoft Store for Windows UWP.
## GlobalProtect VPNs
The GlobalProtect app provides a simple way to extend enterprise Security policies to mobile endpoints. As with other remote endpoints running the GlobalProtect app,<mark style="background: #FFB8EBA6;"> the mobile app provides secure access to your corporate network over an IPSec or SSL tunnel</mark>.
### Types of VPN Configuration
The app connects <mark style="background: #FFB86CA6;">to the gateway that is closest to the end user’s current location</mark>. In addition, <mark style="background: #BBFABBA6;">traffic to and from the mobile endpoint is automatically subject to the same Security-policy enforcement as other endpoints in your corporate network</mark>. The app also collects information about the host configuration and can use this information for enhanced HIP-based Security-policy enforcement. 

There are two types of VPN configurations: <strong>on-demand</strong> and <strong>always-on</strong>.

In a <mark style="background: #FF5582A6;">remote access (On-Demand) VPN configuration</mark>, <mark style="background: #FFF3A3A6;">users must manually launch the GlobalProtect app to establish a secure GlobalProtect connection</mark>. The GlobalProtect app connects to the GlobalProtect portal (upon user login) to submit user and host information and retrieve the agent configuration. After the app receives the agent configuration from the portal, it connects and establishes a VPN tunnel to the GlobalProtect gateway that was specified in the agent configuration.

In an <mark style="background: #FF5582A6;">Always-On VPN configuration</mark>, <mark style="background: #FFB8EBA6;">the secure GlobalProtect connection is always on</mark>. The GlobalProtect app connects to the GlobalProtect portal (upon user login) to submit user and host information and retrieve the agent configuration. After the app receives the agent configuration from the portal, it automatically connects and establishes a VPN tunnel to the GlobalProtect gateway that was specified in the agent configuration.
### GlobalProtect User Connection Sequence
First, the <mark style="background: #BBFABBA6;"><strong>GlobalProtect client</strong> on the local system connects to the GlobalProtect portal for authentication</mark>. After authorization is confirmed, <mark style="background: #ABF7F7A6;">the portal sends the client configuration and a list of GlobalProtect gateways</mark>. Lastly, <mark style="background: #ADCCFFA6;">the client connects to the best gateway (based on SSL response time and local priority) to respond to its connection request</mark>. 

<mark style="background: #D2B3FFA6;">The client communicates with portals and gateways</mark>. <mark style="background: #FFB86CA6;">There is no direct communication among gateways or between gateways and portals</mark>. <mark style="background: #ADCCFFA6;">After the client is installed and enabled, the client contacts the portal when setting up a connection</mark>. Any time the client contacts the portal, the portal authenticates the connections. 

![[GlobalProtect User Connection Sequence.png]]

## GlobalProtect Topology
For larger environments, GlobalProtect can be configured with multiple gateways.

<mark style="background: #FFF3A3A6;">Additional gateways can be used to provide access to multiple protected networks</mark>. <mark style="background: #FFB86CA6;">They can also be used to improve user redundancy and performance</mark>. <mark style="background: #BBFABBA6;">GlobalProtect clients connect directly to a gateway from a list provided by the portal</mark>. By default, <mark style="background: #ABF7F7A6;">the chosen gateway is the one that responds fastest to the connection request</mark>. To ensure consistent access, <strong>multiple gateways often require the networks to be connected to each other by VPN</strong> <mark style="background: #D2B3FFA6;">so that the user has access to the same data, regardless of which gateway they connect to</mark>.

![[GlobalProtect Topology.png]]

## GlobalProtect Gateway
An <strong>internal gateway</strong> <mark style="background: #FFB8EBA6;">is an interface on the internal network that is configured as a GlobalProtect gateway</mark>. When used in conjunction with <strong>User-ID</strong> and <strong>HIP checks</strong>, <mark style="background: #FFB86CA6;">an internal gateway can be used to provide a secure, accurate method of identifying and controlling traffic based on user or device state</mark>. Internal gateways are useful in sensitive environments where authenticated access to critical resources is required.
![[GlobalProtect Gateway.gif]]
In the example shown, <strong>internal gateways</strong> are used to enforce <mark style="background: #FF5582A6;">group-based policies</mark> that allow users <mark style="background: #FFB86CA6;">in the Engineering group</mark> <mark style="background: #FFF3A3A6;">access to internal source control</mark> and <mark style="background: #FFF3A3A6;">bug-tracking databases</mark> and allow users <mark style="background: #FFB86CA6;">in the Finance group</mark> <mark style="background: #FFF3A3A6;">to access the customer relationship management (CRM) applications</mark>. <mark style="background: #FFB8EBA6;">All authenticated users have access to internal web resources</mark>. <mark style="background: #BBFABBA6;">HIP profiles configured on the gateway also check each host to ensure compliance with internal maintenance requirements</mark>, such as whether the latest security patches and antivirus definitions are installed, whether disk encryption is enabled, or whether the required software is installed.

The <strong>GlobalProtect portal</strong> can <mark style="background: #FF5582A6;">provide an IP address and DNS hostname as part of the information passed to the client</mark>, which <mark style="background: #FFB8EBA6;">the client can use to determine whether it is <strong>inside</strong> or <strong>outside</strong> the corporate network</mark>. The DNS hostname and IP address must correspond to a <mark style="background: #FFB86CA6;">device whose name can be resolved only by an internal name server</mark>.
- <strong>Internal Network</strong>: <mark style="background: #FFB8EBA6;">The agent performs a <strong>reverse lookup</strong> on the IP address</mark>. <mark style="background: #FFF3A3A6;">If it receives the expected hostname as a response</mark>, <mark style="background: #BBFABBA6;">the agent assumes it is on an internal network and connects to the <strong>gateways in the internal list</strong></mark>.
- <strong>External Network</strong>: <mark style="background: #FFB86CA6;">If no response is received for the lookup</mark>, <mark style="background: #ABF7F7A6;">the client connects to the <strong>gateways in the external</strong> list</mark>. If an internal host detection hostname and address pair are not provided, <mark style="background: #ADCCFFA6;">the client connection attempts to connect to the internal gateways first, then to the external gateways</mark>.

![[Internal and External Gateways.png]]

### Internal Gateway
<strong>Prisma Access cloud-native internal gateway solution</strong> reduces the need to implement GlobalProtect in conjunction with an on-premises internal gateway <mark style="background: #FFF3A3A6;">to learn User-ID for users on an internal network</mark>. <mark style="background: #BBFABBA6;">Prisma Access deployments can enable a native-internal gateway natively</mark> within the Prisma Access architecture.

Prior to Prisma Access 5.1, an on-premises NGFW had to be deployed as an internal gateway to generate IP user mappings and HIP for hosts running the GlobalProtect client software in Prisma Access remote networks. 
With Prisma Access cloud-native internal gateway, you can avoid using on-premises internal gateways; <mark style="background: #FFB86CA6;">the Prisma Access internal gateway generates the IP user mappings and HIPs locally in remote networks</mark>. <mark style="background: #FF5582A6;">Remote networks consume IP user mappings and HIPs from the local database</mark> for posture checks, instead of learning them from other firewalls.

![[nternal Gateway GlobalProtect.png]]

To enable the Prisma Access internal gateway, navigate to <strong>Workflows > Prisma Access Setup > Remote Networks > Advanced Settings</strong>. Select the <strong>Enable Internal Gateway</strong> checkbox, and then click <strong>Save</strong>. 
If you do not want to use your own DNS server, you can select the <strong>Enable Internal Host Detection</strong> checkbox for IPv4. 

When you enable the internal gateway, <mark style="background: #D2B3FFA6;">the remote network instances act as internal gateways</mark>. When you enable the internal host detection, <mark style="background: #CACFD9A6;">Prisma Access creates PTR records on the remote network DNS proxy servers for the internal host detection process</mark>. If you enable Internal Host Detection, <mark style="background: #FFF3A3A6;">verify that the DNS resolution is working, perform a reverse DNS lookup from your internal network to the DNS proxy server IP, and ensure it returns an FQDN starting with <strong>any-igw</strong></mark>.
## GlobalProtect #configuration 
Before doing the initial GlobalProtect (GP) configuration, there are several considerations and decisions to be made, such as <mark style="background: #BBFABBA6;">egress addresses</mark> and <mark style="background: #ADCCFFA6;">pre-allocated addresses</mark> for mobile users.
- <strong>Egress IP Addresses</strong>
<strong>Prisma Access</strong> uses <strong>GP gateway</strong> and <strong>GP portal</strong> IP addresses in mobile user deployments. <mark style="background: #FFB8EBA6;">These IP addresses are known collectively as egress IP addresses</mark>. <mark style="background: #FFB86CA6;">If you require these egress IP addresses before onboarding the location</mark>, <mark style="background: #BBFABBA6;">you can run an application programming interface (API) script to have Prisma Access pre-allocate these IP addresses for a location in advance</mark>. <mark style="background: #ABF7F7A6;">You can then add the location's egress IP addresses to your organization's allow lists before onboarding the location</mark>.
- <strong>Static IP Address Allocation</strong>
The <strong>Static IP Address Allocation</strong> feature allows <mark style="background: #ADCCFFA6;">you to assign a fixed IP address to Prisma Access mobile users</mark>. This is useful if your legacy network deployments utilize IP addresses to restrict user access to corporate resources as part of your network and application design. <mark style="background: #D2B3FFA6;">Prisma Access enables you to allocate a static IP address to the mobile user</mark>, <mark style="background: #CACFD9A6;">which can then be used to configure access to private applications or data center resources</mark>.

To enable secure access for your mobile workforce no matter where they are located, you can strategically <mark style="background: #FFB8EBA6;">deploy additional Palo Alto Networks Next-Generation Firewalls (NGFWs)</mark> and <mark style="background: #FF5582A6;">configure them as GlobalProtect gateways</mark>.

To configure GlobalProtect on Prisma Access, navigate to <strong>Workflow > Prisma Access Setup > GlobalProtect</strong>.
#### Steps for Configuring GlobalProtect
Follow these steps to configure GlobalProtect in Prisma Access:
##### Step 1: Determine the Connection Methods
Determine how mobile users in the location you’re setting up should connect to Prisma Access. You can divide your mobile user license <mark style="background: #FFB86CA6;">between GlobalProtect</mark> and <mark style="background: #FFF3A3A6;">Explicit Proxy Connections</mark>; <mark style="background: #ABF7F7A6;">some users can connect through GlobalProtect and others through Explicit Proxy</mark>. The GlobalProtect app installed on mobile user devices sends traffic to Prisma Access.![[Determine the Connection Methods.png]]

##### Step 2: Set Up the Infrastructure
Set up basic infrastructure settings and then configure the infrastructure settings that are specific to your connection type (GlobalProtect or Explicit Proxy). 

A proxy auto-config (PAC) file on mobile user devices redirects browser traffic to Prisma Access. 

Out-of-the-box settings include the Infrastructure Subnet. You can customize infrastructure settings as needed, such as adding a portal hostname, Prisma Access locations, and setting up user authentication.![[Set Up the Infrastructure.png]]

##### Step 3: Choose the Prisma Access Locations
The map displays the global regions where you can deploy Prisma Access for Users: North America, South America, Europe, Africa, Middle East, Asia, Japan, and ANZ (Australia and New Zealand). In addition, Prisma Access provides multiple locations within each region to ensure that your users can connect to a location that provides a user experience tailored to the users’ locale. For the best performance, Select All. 

Alternatively, select the specific locations within each selected region where your users will need access. By limiting your deployment to a single region, you can have more granular control over your deployed regions and exclude regions required by your policy or industry regulations.
##### Step 4: Set Up User Authentication
Set up User Authentication so that only legitimate users have access to your services and applications. To test your setup, you can add users that Prisma Access authenticates locally, or you can go straight to setting up enterprise-level authentication.

![[Set Up User Authentication.png]]

##### Step 5: Push the Settings to Prisma Access
Once the user authentication is completed, the settings need to be pushed to Prisma Access to complete the GlobalProtect configuration.

![[Push the Settings to Prisma Access.png]]

#### Enable Portal Only for Proxy Mode on GP Agent
When GlobalProtect is set to proxy mode, <mark style="background: #FFB8EBA6;">GlobalProtect portals can be onboarded without gateways when the Agent Proxy feature is enabled</mark>. Complete the following steps to enable explicit proxy and the <strong>Enable Portal Only for Proxy Mode</strong> on <strong>GP Agent</strong> feature for GlobalProtect.
##### Step 1: Enable Explicit Proxy and Agent-Based Proxy 
Navigate to <strong>Workflows > Prisma Access Setup > Mobile Users > Explicit Proxy</strong> and click <strong>Enable</strong>. Once enabled, click <strong>Explicit Proxy Setup</strong>. Under <strong>Explicit Proxy Setup > Infrastructure Settings</strong>, click <strong>Set Up Proxy Settings</strong>. Under Proxy URL Settings, provide an <strong>Explicit Proxy URL</strong> and a local proxy port that mobile users will use to connect to Prisma Access. Select <strong>Enable Agent Proxy</strong> and click <strong>Save</strong>.![[Enable Explicit Proxy and Agent-Based Proxy.png]]

##### Step 2: Configure GlobalProtect 
After enabling explicit proxy, navigate to <strong>Workflows > Prisma Access Setup > GlobalProtect</strong>. Under <strong>Infrastructure Settings</strong>, click the <strong>Enable Portal only for Proxy Mode on GP Agent</strong> checkbox.

![[Configure GlobalProtect.png]]

##### Step 3: Review Prisma Access Locations
Once the <strong>Enable Portal only for Proxy Mode on GP Agent</strong> feature has been enabled, you will not have the option to add Prisma Access locations.

![[Review Prisma Access Locations.png]]

#### Mobile Users 
Before configuring mobile users, <mark style="background: #FFB8EBA6;">ensure that you have the required licenses</mark> (<mark style="background: #FF5582A6;">a Prisma Access license for mobile users</mark> and <mark style="background: #FFB86CA6;">a Strata Logging Service license with proper PAN-OS storage space</mark>). If mobile users will be connecting to other connected networks, you will need either the <mark style="background: #FFF3A3A6;">Zero Trust Network Access (ZTNA)</mark> or <mark style="background: #FFF3A3A6;">Enterprise Edition Prisma Access license</mark> that will provide the <strong>corporate access node</strong> (CAN) necessary to connect.
##### Step 1: Choose GlobalProtect Connection  
Determine how mobile users in the location you’re setting up should connect to Prisma Access. You can divide your mobile user license between GlobalProtect and explicit proxy connections; some users can connect through GlobalProtect and others through explicit proxy.

These steps are for GlobalProtect. From the GlobalProtect Connection panel, click <strong>Enable > GlobalProtect Setup > Setup Infrastructure Settings.</strong>

![[Choose GlobalProtect Connection.png]]

##### Step 2: Portal Hostname  
Add a fully qualified domain name as the Portal Hostname, and add a DNS region. In the image, Worldwide has been selected as the DNS region. Then, click <strong>Save</strong>.![[Portal Hostname.png]]

##### Step 3: Choose Prisma Access Locations  
Once you have configured the Portal Hostname and DNS Region, you can select a location. Click <strong>Add Locations</strong> and the location map will appear. The map displays the global regions where you can deploy Prisma Access for users: North America, South America, Europe, Africa, Middle East, Asia, Japan, and ANZ (Australia and New Zealand). In addition, Prisma Access provides multiple locations within each region to ensure that your users can connect to a location that provides a user experience tailored to the users’ locale. For the best performance, select <strong>All</strong>. 

Choose regions and locations, and then click <strong>Save</strong>.

![[Choose Prisma Access Locations.png]]

##### Step 4: Authenticate Mobile Users  
Set up User Authentication so that only legitimate users have access to your services and applications. To test your setup, you can add users that Prisma Access authenticates locally, or you can go straight to setting up enterprise-level authentication.

![[Authenticate Mobile Users.png]]

#### Customize the Portal Address
You can configure your company domain in the portal address that your mobile users connect to for secure access to the internet, data centers, and headquarters. By default, Prisma Access uses the gpcloudservice.com domain.
##### Step 1
Navigate to <strong>Workflows > Prisma Access Setup > GlobalProtect</strong> and click the gear icon to edit the <strong>Infrastructure Settings.</strong> First, select <strong>Custom Domain</strong> on Portal Name Type, and enter the <strong>Portal Hostname</strong> you want to use. Next, add the <strong>Portal DNS CNAME</strong> to which to map your DNS server entries. Lastly, click <strong>Import</strong> to import the certificate you provisioned for your custom domain portal address.![[Customize the Portal Address.png]]

##### Step 2
On the Import Certificate panel, enter a name for the certificate and click <strong>Choose File</strong> to upload the certificate file. Next, select a certificate format for the certificate you are importing from the <strong>Format</strong> drop-down menu. You have two options, select either:
- <strong>Encrypted Private Key and Certificate (PKCS12):</strong> The key and certificate are in a single container (Certificate File).
- <strong>Base64 Encoded Certificate (PEM):</strong> If you select this option, click <strong>Choose File</strong> to upload the Key File separately from the certificate.
Lastly, enter a passphrase to encrypt the key into the <strong>Passphrase</strong> and <strong>Confirm Passphrase</strong> fields, then click <strong>Save.</strong>![[Customize the Portal Address2.png]]

##### Step 3
If you have not already done so, configure your DNS servers to point to the Prisma Access DNS CNAME you defined. Click <strong>Save</strong> and <strong>Push Config</strong> to Prisma Access.![[Customize the Portal Address3.png]]

#### Customize App Settings
Customize how your end users interact with the GlobalProtect app. You can explore all GlobalProtect settings on the GlobalProtect App page. The following are some of the options available to you.
##### Authentication Override
Enable Prisma Access to generate and accept secure, encrypted cookies for user authentication. Turning this feature on allows the user to provide login credentials only once during the specified period of time.
- Generate cookie for authentication override: Enables the Prisma Access to generate encrypted, endpoint-specific cookies and issue authentication cookies to the endpoint.
- Accept cookie for authentication override: Enables Prisma Access to authenticate users with a valid, encrypted cookie.
- Cookie Lifetime: Specifies the hours, days, or weeks for which the cookie is valid (default is 24 hours). The range for hours is 1 to 72; for weeks is 1 to 52; and for days is 1 to 365.
- Certificate to Encrypt/Decrypt Cookie: Selects the RSA certificate used to encrypt and decrypt the cookie.

![[Customize App Settings.png]]

##### Connect
Specify the method that the GlobalProtect app uses to connect to Prisma Access:
- User-Logon (Always On): The GlobalProtect app automatically connects to Prisma Access as soon as the user logs in.
- Pre-Logon (Always On): The GlobalProtect app authenticates the user and establishes a VPN tunnel to Prisma Access before the user logs in.
- On-Demand: Users must manually launch the app to connect to GlobalProtect.
- Pre-Logon Then On-Demand: Enables the GlobalProtect app to authenticate the user and establish a VPN tunnel to Prisma Access before the user logs in to the endpoint.

![[Customize App Settings2.png]]

##### GlobalProtect  
Decide what GlobalProtect app settings the user can adjust:  
- <strong>Disable GlobalProtect:</strong> Decide whether or not users can disable the GlobalProtect app.
- <strong>Uninstall GlobalProtect:</strong> Allow users to uninstall the GlobalProtect app, prevent them from uninstalling the GlobalProtect app, or allow them to uninstall if they enter a password you create.
- <strong>Upgrade GlobalProtect:</strong> Specify how app upgrades should work, including whether users can initiate updates.
- <strong>Allow User to Change Portal:</strong> Let users change the portal the GlobalProtect app uses to connect to Prisma Access.

![[Customize App Settings3.png]]

##### Internal Host Detection  
If you do not require your mobile users to connect to Prisma Access when they are on the internal network, enable internal host detection to enable the GlobalProtect app to determine whether the network is internal or external.
##### Gateways  
By default, all the gateways in your Prisma Access locations are available to users. If you have additional GlobalProtect gateways that you’d like your users to be able to connect to, you can add those gateways here.![[Customize App Settings4.png]]

##### HIP Data Collection  
Define custom host information profile (HIP) data that you want the app to collect or exclude from collection. When this option is enabled, the app collects data from devices running Windows, macOS, or Linux operating systems. Go to <strong>Objects > HIP Objects / HIP Profiles</strong>. It is important to remember that adding and requiring a sync with too many items can restrict a user from logging on and can cause a denial.

![[Customize App Settings5.png]]

#### Setting Up Mobile User Authentication
You can authenticate mobile users to Prisma Access using any of the supported authentication types.
##### Step 1
Go to <strong>Workflows > Prisma Access Setup > GlobalProtect > Infrastructure > User Authentication</strong> and click the <strong>Add Authentication</strong>.
##### Step 2
Select the <strong>Authentication Method</strong> from the supported authentication types.
##### Step 3
Specify the <strong>Certificate Authentication</strong> settings.
#### Steps to Enable Mobile Users to Access Corporate Resources
To allow mobile users to access resources on your HQ, data center networks, or other branch locations, you must configure the Prisma Access Infrastructure Settings to enable the network backbone after you complete the steps below. To complete the necessary configurations, go to <strong>Workflows</strong> <strong>> Prisma Access Setup > Service Connections > Service Connections Setup</strong>.
##### Step 1
Navigate to <strong>Workflows > Prisma Access Setup > GlobalProtect > Infrastructure</strong> tab and click <strong>Set Up Infrastructure Settings</strong>.  
Under Client IP Pool, click <strong>Add IP Pool</strong> and then define the IP address pools Prisma Access uses to assign IP addresses to your mobile users.
##### Step 2
In the Create new IP Pool screen, select your region and add the IP address range for that pool.
Review or adjust the client IP Pool that Prisma Access uses to assign IP addresses to mobile users. You can customize per region to set up IP pools dedicated to regions or locations. For regions or locations for which you do not specify an IP pool, Prisma Access uses the Worldwide IP pool.
<strong>Note:</strong> Make sure to Push Config to Prisma Access to save the new mobile user settings.
## Split Tunneling
<strong>Split Tunneling</strong> allows you to <mark style="background: #FFB8EBA6;">customize traffic routing</mark> through <mark style="background: #FF5582A6;">the VPN tunnel to Prisma Access</mark> <mark style="background: #FFB86CA6;">via the GlobalProtect app</mark>. This functionality not only <mark style="background: #FFF3A3A6;">conserves bandwidth by excluding non-business-critical or non-productive traffic</mark> but also <mark style="background: #BBFABBA6;">provides flexibility in defining which users, devices, or systems should receive specific tunnel settings</mark>.

By configuring Split Tunneling Settings, <mark style="background: #ADCCFFA6;">you can determine what traffic is sent to Prisma Access and what <mark style="background: #BBFABBA6;">can be routed locally instead</mark></mark>. There are three options for the Split Tunnel Settings:
##### Local Network Access
Allows Windows and macOS users <mark style="background: #FFB8EBA6;">access to local resources</mark> <mark style="background: #FF5582A6;">without requiring them to first connect to Prisma Access</mark>.
##### Exclude Traffic
<mark style="background: #FFF3A3A6;">Specify traffic to exclude from Prisma Access policy inspection and enforcement</mark> <mark style="background: #FFB86CA6;">based on application, domain, and route (like an IP address)</mark>.
##### Include Traffic
By default, <mark style="background: #BBFABBA6;">the <strong>GlobalProtect</strong> app routes all traffic to Prisma Access except for the traffic specified on the exclusions list</mark>. <mark style="background: #D2B3FFA6;">Specify traffic that the GlobalProtect app should always route to Prisma Access, even when it meets exclude list criteria</mark>.

![[Split Tunneling.png]]

## Clientless VPN
The <strong>Clientless VPN</strong> <mark style="background: #FF5582A6;">allows users without the GlobalProtect app</mark> (for example, partners or contractors) <mark style="background: #FFB86CA6;">to securely access enterprise applications by enabling them to authenticate to GlobalProtect in a browser</mark>.
### Clientless VPN #configuration 
#### Step 1
Navigate to <strong>Workflows > Prisma Access Setup > GlobalProtect</strong> and click the <strong>Clientless VPN</strong> tab. Then, click <strong>Add Applications</strong>.![[Clientless VPN.png]]

#### Step 2
Toggle the <strong>Enable Clientless VPN</strong> option and click <strong>Add Rule</strong> to specify the users and applications that can use Clientless VPN.![[Clientless VPN1.png]]

#### Step 3
Configure the Timeout Settings and the advanced settings (if required). Then, click <strong>Save</strong>.![[Clientless VPN3.png]]

## Certificate Authentication
For enhanced security, use a <strong>certificate</strong> (in addition to your authentication service) <mark style="background: #FFB8EBA6;">to obtain usernames and authenticate users to Prisma Access</mark>. 

To authenticate users based on a client certificate, <mark style="background: #FFB86CA6;">one of the certificate fields, such as the Subject Name field, must identify the username</mark>. 

Mobile users who successfully authenticate through client certificate authentication <mark style="background: #FF5582A6;">do not have the option to sign out of the GlobalProtect app</mark>. 

With Prisma Access, you can choose to require mobile users to pass both certificate authentication and authentication based on the authentication type or to grant access to mobile users as long as they have successfully passed only one of those checks.
## Certificate Profile
The <strong>Certificate Profile</strong> <mark style="background: #FFB8EBA6;">specifies the contents of the username and user domain fields</mark>, <mark style="background: #FF5582A6;">lists CA certificates</mark>, <mark style="background: #FFB86CA6;">sets criteria for blocking a session</mark>, and <mark style="background: #FFF3A3A6;">offers ways to determine the revocation status of CA certificates</mark>. <mark style="background: #BBFABBA6;">Because the certificate is part of the authentication for the mobile user, you must predeploy certificates used in Certificate Profiles to your users before their initial login</mark>. <mark style="background: #ADCCFFA6;">The Certificate Profile specifies which certificate field contains the username (Subject or Subject Alt)</mark>.
# Security Policy and Security Profiles
### Policy Types
Prisma Access supports the following policy types:
#### Security 
Security policy rules determine whether <mark style="background: #FFB8EBA6;">to block or allow sessions</mark> <mark style="background: #FF5582A6;">based on traffic attributes</mark> such as <mark style="background: #FFF3A3A6;">source and destination zones</mark>, <mark style="background: #FFB86CA6;">source and destination IP addresses, applications, or users</mark>.
#### Decryption
Decryption policy rules <mark style="background: #BBFABBA6;">allow you to define the traffic to decrypt</mark> and <mark style="background: #ABF7F7A6;">the type of decryption you wish to perform on the specified traffic</mark>. To start decrypting traffic, simply set up the certificates required by Prisma Access to act as a trusted third party in a session.
#### Application Override
You can create an application override policy rule when <mark style="background: #D2B3FFA6;">you do not want traffic inspection for custom applications between known IP addresses</mark>.
#### QoS
QoS rules allow you to dependably <mark style="background: #CACFD9A6;">run high-priority applications and traffic under limited network capacity</mark>. You can use Quality of Service (QoS) policy rules <mark style="background: #FFB8EBA6;">to identify traffic that requires preferential treatment or bandwidth limiting</mark>.
##### QoS Codepoints
###### Expedited Forwarding (EF)
Used to request low loss, low latency, and guaranteed bandwidth for traffic. Packets with EF codepoint values are typically guaranteed the highest priority delivery.
###### Assured Forwarding (AF)
Used to provide reliable delivery for applications. Packets with AF codepoints indicate a request for traffic to receive higher priority treatment than best-effort service provides. Packet with EF codepoint take precedence over packets with AF codepoint.
###### Class Selector (CS)
Used to provide backward compatibility with network IP addresses that use the IP precedence field to mark priority traffic.
###### IP Precedence (Type of Service or ToS)
Used by legacy network IP addresses to mark priority traffic. The IP ToS specifies the type of service the packet is supposed to receive. It may also be known as the ToS byte, which is related to the Differentiated Service Codepoint (DSCP).
###### IP Precedence (Type of Service or ToS)
Used by legacy network IP addresses to mark priority traffic. The IP ToS specifies the type of service the packet is supposed to receive. It may also be known as the ToS byte, which is related to the Differentiated Service Codepoint (DSCP).
### Policy Action
For traffic that matches the attributes defined in a Security policy, you can apply the following actions.

| Action          | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Allow (default) | Allows all traffic                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Deny            | Blocks traffic and applies the default Deny Action defined for the application that is being denied. To view the deny action defined by default for an application, view the application details in Objects > Applications or check the application details in Applipedia.                                                                                                                                                                                                           |
| Drop            | Silently drops the traffic; for an application, it overrides the default deny action. A TCP reset is not sent to the host/application. For Layer 3 interfaces, to optionally send an ICMP unreachable response to the client, set Action: Drop and enable the Send ICMP Unreachable check box. When enabled, the Security Processing Node sends the ICMP code for communication with the destination is administratively prohibited-ICMPv4: Type 3, Code 13; ICMPV6: Type 1, Code 1. |
| Reset Client    | Sends a TCP reset to the client-side device                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Reset Server    | Sends a TCP reset to the server-side device                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Reset Both      | Sends a TCP request to both the client-side and server-side devices                                                                                                                                                                                                                                                                                                                                                                                                                  |
<mark style="background: #BBFABBA6;">A reset is sent only after a session is formed</mark>. <mark style="background: #ABF7F7A6;">If the session is blocked before a three-way handshake is completed</mark>, the security processing node (SPN) <mark style="background: #ADCCFFA6;">will not send the reset</mark>.
For a TCP session with a reset action, the SPN does not send an Internet Control Message Protocol (ICMP) Unreachable response.
For a UDP session with a drop or reset action, if the ICMP Unreachable checkbox is selected, the SPN sends an ICMP message to the client.
### Policy Objects
A <strong>policy object</strong> is a <mark style="background: #FFB8EBA6;">single object or a collective unit</mark> <mark style="background: #FFB86CA6;">that groups discrete identities such as IP addresses, URLs, applications, or users</mark>. With policy objects that are a collective unit, you can reference the object in a security policy instead of manually selecting multiple objects one at a time.
#### Address-Related Objects
The following are address-related objects available within Prisma Access.
##### Addresses, Address Groups, and Regions
Allows you to <strong>group</strong> <mark style="background: #ADCCFFA6;">specific source</mark> or <mark style="background: #BBFABBA6;">destination addresses</mark> that require the same policy enforcement. <mark style="background: #FFB8EBA6;">Address objects can include IPv4 and IPv6 addresses</mark> (single IP, range, or subnet) or <mark style="background: #FFB8EBA6;">FQDN</mark>. Alternatively, you may define a <mark style="background: #FFB86CA6;">region by the latitude and longitude coordinates</mark>, or <mark style="background: #FFF3A3A6;">you can <mark style="background: #ADCCFFA6;">select a country</mark> and <mark style="background: #D2B3FFA6;">define an IP address or range</mark></mark>. You can then group a collection of address objects to create an address group object.
##### Dynamic User Groups (DUGs) 
<strong>Dynamic user groups</strong> are groups <mark style="background: #FFB8EBA6;">where membership is based on tags</mark>. 

The group membership <mark style="background: #FF5582A6;">is based on an attribute or activity that the tag identifies</mark>, and <mark style="background: #FFB86CA6;">members are included in the group only when they meet that criterion</mark>. 

A dynamic user group that is based on an auto-tag includes <mark style="background: #ADCCFFA6;">users or IP addresses that are associated with a certain type of log activity</mark>. You do not need to manually update policy or groups to respond to a threat.
##### Tags
<mark style="background: #FFF3A3A6;">Tag policies and objects to group related items and add colors to visually distinguish them from other configured policies for easy review</mark>. You can tag all <mark style="background: #FF5582A6;">Prisma Access policies</mark>, as well as <mark style="background: #FF5582A6;">addresses</mark>, <mark style="background: #FF5582A6;">objects</mark>, <mark style="background: #FF5582A6;">address groups</mark>, <mark style="background: #FF5582A6;">service objects</mark>, and <mark style="background: #FF5582A6;">service groups</mark>. You can apply one or more tags to any policy rule or object, up to a maximum of 64 tags. Prisma Access supports up to 10,000 tags.
##### Auto Tags
Prisma Access can <mark style="background: #ABF7F7A6;">automatically tag the users or IP addresses associated with a log entry</mark>. <mark style="background: #BBFABBA6;">When you use auto-tags to build policy, you can automatically enforce users and IP addresses</mark> <mark style="background: #ADCCFFA6;">based on behavior and activity</mark>. You do not need to manually and retroactively adjust policy or groups. 

To get started, set up an auto-tag and then use it to populate a dynamic address group or a dynamic user group. Then, add the dynamic address or user group to a policy rule.
##### External Dynamic Lists (EDLs)
Allows you to <mark style="background: #D2B3FFA6;">define an imported list of IP addresses, URLs, or domain names</mark> that you can use in policy rules to block or allow traffic.
#### Policy and Enforcement-Related Objects
##### Profile Groups
<strong>Security profiles</strong> scan traffic for threats, and a <strong>profile group</strong> <mark style="background: #FFB8EBA6;">is a collection of each type of profile</mark>. To enable <mark style="background: #FFB86CA6;">Security profile scanning</mark>, <mark style="background: #BBFABBA6;">you must build a profile group and attach the group to a Security rule</mark>. Prisma Access provides predefined Security profiles that you can use to build a profile group.
##### Service and Service Groups
<mark style="background: #FF5582A6;">Allows you to specify the</mark> <mark style="background: #ADCCFFA6;">source and destination ports</mark> and <mark style="background: #ADCCFFA6;">protocols</mark> that <mark style="background: #FF5582A6;">a service can use</mark>. You also create a <mark style="background: #FFB86CA6;">custom service on any TCP/UDP port of your choice to restrict application usage to specific ports on your network</mark>. 

<mark style="background: #FFF3A3A6;">After you have created your service objects, you can then group a collection of services that require the same policy enforcement to create a service group</mark>.
##### HIP Objects and HIP Profiles
Allows you to define objects for the <strong>Host Information Profile (HIP)</strong> <mark style="background: #FFB86CA6;">to provide matching criteria</mark> <mark style="background: #BBFABBA6;">for filtering the raw data</mark>. 
<mark style="background: #FFF3A3A6;">Doing this gives information about how the device is maintained</mark>, such as whether data is encrypted, whether antivirus signatures are up to date, whether the device is jailbroken, and more. 

<mark style="background: #BBFABBA6;">You can use the device state information to enforce the policy</mark>. After you have created your HIP objects, <mark style="background: #FFF3A3A6;">you can then group a collection of <strong>HIP objects</strong> to create a <strong>HIP Profile</strong> to be evaluated together for monitoring or policy enforcement</mark>.
##### Schedules
By default, <mark style="background: #FFB8EBA6;">Security policy rules are always in effect (on all dates and times)</mark>. <mark style="background: #FFB86CA6;">To limit a Security policy rule to specific times</mark>, <mark style="background: #ABF7F7A6;">you can define schedules and then apply them to the appropriate rules</mark>. For each schedule, <mark style="background: #D2B3FFA6;">you can specify a fixed date and time range or a recurring daily or weekly schedule</mark>. Add or edit a Security policy rule to get started.
##### Quarantine Device Lists
Prisma Access allows you to identify and quarantine compromised devices with the GlobalProtect app. <mark style="background: #CACFD9A6;">You can either manually or automatically (based on auto-tags) add devices to a quarantine list</mark>. <mark style="background: #FFF3A3A6;">You can block quarantined devices from accessing the network or restrict the device traffic based on a security rule</mark>. To get started, go to <strong>Configuration</strong> > <strong>Objects</strong> and set up a Quarantined Device List. Then, use the list as part of identity redistribution.
##### Certificates
<mark style="background: #FFB8EBA6;">Centrally manage the certificates you use to secure communication across your network</mark>. In one place, <mark style="background: #FF5582A6;">set up your certificates</mark>, <mark style="background: #FFB86CA6;">add a certificate</mark>, <mark style="background: #FFF3A3A6;">add OCSP responders</mark>, and <mark style="background: #BBFABBA6;">deﬁne certificate checks you want to require</mark>. The certificates and settings you set up here can be used throughout your Prisma Access deployment to secure features like decryption, your authentication portal, and the GlobalProtect app.
##### URL Category
Allows you to create<mark style="background: #ABF7F7A6;"> a custom URL category object to use in a URL Filtering profile</mark> <mark style="background: #FFB86CA6;">to specify exceptions to URL category enforcement</mark>. It also allows you to create a custom URL category based on multiple URL categories.
### Security Profiles
<strong>Security profiles</strong> <mark style="background: #FF5582A6;">are fundamental components for enabling security services</mark> such as Threat Prevention, WildFire, and URL Filtering on your network traffic. <mark style="background: #FFF3A3A6;">These profiles perform <mark style="background: #FF5582A6;">advanced inspection</mark> on traffic that a Security rule allows</mark>; <mark style="background: #FFB86CA6;">they scan for and prevent threats, attacks, misuse, and abuse</mark>.

For customization, management, and visibility into each Security profile type, you can access the Security profiles via <strong>Manage > Configuration > NGFW and Prisma Access > Security Services</strong>. 

<strong>Security profiles</strong> <mark style="background: #BBFABBA6;">consolidate profile configuration</mark>, <mark style="background: #FFB86CA6;">centralizing everything you need to set up and manage profiles is in one place</mark>. The interfaces also give you access to all the features a profile offers and resources you can use to update profiles, such as content release updates, the Threat Vault, and PAN-DB site classifications.

When working with Security profiles, it's especially important to know about profile groups. <mark style="background: #FFB8EBA6;">Security rules reference profile groups</mark>, not individual profiles. <mark style="background: #FF5582A6;">Therefore, for a profile to be active</mark>, <mark style="background: #FFB8EBA6;">it must be part of a profile group that a Security rule is using</mark>.![[Security Profiles and Profile Groups.png]]

You can create, manage, and enable your Security Services profiles via <strong>Manage > Configuration > NGFW and Prisma Access > Security Services</strong> and select the available profile types. The profile dashboards allow you to review the best practice profiles, add a new profile, update existing profiles, and create and manage overrides.

In <strong>Strata Cloud Manager</strong>, a Security profile is only active when the following two conditions are met:
##### 1. The Security Profile Is in a Profile Group
You can add a Security profile to a Profile Group by navigating to <strong>Manage ></strong> <strong>Configuration > NGFW and Prisma Access > Security Services > Profile Groups</strong>. 

A <strong>profile group</strong> <mark style="background: #FFB8EBA6;">is a collection of profiles</mark>, and <mark style="background: #FF5582A6;">it can include <strong>one</strong> profile from each type</mark>.
For each profile, <mark style="background: #FFF3A3A6;">best-practice settings are built in and enabled by default</mark>. You can use these out-of-the-box profiles as a starting point to customize and build upon the predefined settings.

![[The Security Profile Is in a Profile Group.png]]

##### 2. A Security Rule Is Referencing a Profile Group
A <strong>Security profile</strong> <mark style="background: #FFB8EBA6;">is active only when it is in a profile group that is attached to a Security rule</mark>. When a Security rule is referencing a profile group, <mark style="background: #FFB86CA6;">you can make updates to the individual profiles</mark> and <mark style="background: #FFF3A3A6;">add the group without editing the Security rule</mark>. The Security rule automatically enforces your changes, without requiring you to make a policy commit.

![[A Security Rule Is Referencing a Profile Group.png]]

#### Best Practices Settings
For each profile, <mark style="background: #D2B3FFA6;">best-practice settings are built in and enabled by default</mark>. You can use these out-of-the-box profiles as a starting point to customize and build upon the predefined settings.

Best-practice profiles use the strictest security settings recommended by Palo Alto Networks.
##### Anti-Spyware
This type of protection zeros in on <strong>threats</strong> <mark style="background: #FFB8EBA6;">that affect users' outbound activity</mark>, <mark style="background: #FF5582A6;">especially command-and-control (C2) activity</mark>, where an infected client is being leveraged as part of a remotely conducted cyberattack. It is a part of the Threat Prevention subscription.

![[Anti-Spyware.png]]

<mark style="background: #FFB86CA6;">Anti-spyware detects <strong>command-and-control (C2)</strong> activity</mark>, where spyware on an infected client is <mark style="background: #FFF3A3A6;">collecting data without the user's consent</mark> and/or <mark style="background: #ABF7F7A6;">communicating with a remote attacker</mark>. Prisma Access enforces a strict best-practice Anti-Spyware profile by default, but it also provides an alternate best-practice profile. The best-practice profiles enforce one of two actions on matching traffic:
- <strong>Default</strong> - The default action Palo Alto Networks sets for a specific signature. Typically, the default action is an alert or a reset-both.
- <strong>Reset Both</strong> - For TCP, resets the connection on both client and server ends. For UDP, drops the connection.
##### Vulnerability Protection
Vulnerability Protection <mark style="background: #FFB86CA6;">stops the attacker’s attempts to exploit the system flaws</mark> and gain unauthorized access to your network. It is one part of the Threat Prevention subscription. This type of protection zeros in on <mark style="background: #FF5582A6;">inbound threats</mark>, <mark style="background: #BBFABBA6;">where an attacker is attempting to exploit a system flaw to breach your network</mark>.

![[Vulnerability Protection.png]]

Vulnerability Protection detects system flaws that an attacker might otherwise attempt to exploit. Whereas Anti-Spyware identifies infected hosts as traffic leaves the network, Vulnerability Protection <mark style="background: #D2B3FFA6;">protects against threats entering the network</mark>.
- <strong>Default</strong> - The default action Palo Alto Networks specifies for a specific signature. Typically, the default action is an alert or a reset-both.
- <strong>Reset Both</strong> - For TCP, resets the connection on both client and server ends. For UDP, drops the connection.
##### WildFire and Antivirus

![[WildFire and Antivirus.png]]

Antivirus detects <mark style="background: #ADCCFFA6;">viruses and malware found in executables and file types</mark>. These profiles scan inside compressed files and data-encoding schemes, and if you have enabled decryption, they also scan decrypted content. 

The best-practice Antivirus profile takes one of the following two actions on traffic:
- <strong>Alert</strong> - Generates an alert for each application traffic flow. The alert is saved in the threat log.
- <strong>Reset Both</strong> - For TCP, resets the connection on both client and server ends. For UDP, drops the connection.
##### DNS Security
By leveraging <mark style="background: #FFB8EBA6;">advanced machine learning and predictive analytics</mark>, the <mark style="background: #FFB86CA6;">service provides real-time DNS request analysis</mark> and <mark style="background: #FFF3A3A6;">rapidly produces and distributes DNS signatures that are specifically designed to defend against malware using DNS for C2 and data theft</mark>. Combined with an extensible cloud architecture, it provides access to a scalable threat intelligence system to keep your network protections up to date. Threat protection service is designed to protect and defend your networks from advanced threats.

![[DNS Security.png]]

##### URL Access Control
PAN-DB—the URL Filtering cloud—<mark style="background: #FFF3A3A6;">classifies sites based on content, features, and safety</mark>, and you can enforce your Security policy based on these URL categories. 

You can also prevent credential phishing by tightly controlling the types of sites to which users can enter their corporate credentials. It gives you control of web access and how users interact with online content.

![[URL Access Control.png]]

URL Filtering enables you to control how users interact with web content. The URL Filtering best-practice profile gives you visibility into your users’ web usage and blocks access to URL categories that identify malicious and exploitive web content.
- The best-practice URL Filtering profile includes credential threat prevention checks. Credential threat prevention works by scanning username and password submissions to websites and comparing those submissions against valid corporate credentials.
##### File Blocking
<mark style="background: #ADCCFFA6;">File blocking allows you to identify specific file types that you want to block or monitor</mark>. For most traffic (including traffic on your internal network), block files that are known to carry threats or that have no real use case for upload/download.

![[File Blocking.png]]

File blocking gives you a way to monitor file types in use and limit or stop access to risky file types. The strict best-practice File Blocking profile blocks risky file types and logs the rest (there are over 150 file types that File Blocking detects):
- <strong>Alert</strong> - When the specified file type is detected, a log is generated in the Data Filtering log.
- <strong>Block</strong> - When the risky file type is detected, the file is blocked and a customizable block page is presented to the user. A log is also generated in the Data Filtering log.
- <strong>Continue</strong> - When the specified file type is detected, a response page is displayed to the user. The user can click through the page to download the file, and Data Filtering logs record this event.
##### HTTP Header Insertion
There are predefined settings built in that you can use to manage access to popular SaaS applications, such as Google and YouTube, and create a custom rule to do HTTP header insertion for any other applications.

![[HTTP Header Insertion.png]]

##### Data Loss Prevention
Data Loss Prevention (DLP) on Prisma Access enables you to enforce your organization’s data security standards and prevent the loss of sensitive data across mobile users and remote networks. DLP protects sensitive information against unauthorized access, misuse, extraction, and sharing.

![[Data Loss Prevention.png]]

# 