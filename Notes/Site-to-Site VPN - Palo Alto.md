---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
---
<strong>Virtual private networks</strong> (VPNs) <mark style="background: #FFB8EBA6;">create <strong>tunnels</strong> that enable users and systems to connect securely over a <strong>public network</strong></mark>.

<mark style="background: #FF5582A6;">A <strong>VPN connection</strong> that enables you to connect two LANs is called a "<strong>site-to-site VPN</strong>"</mark>. <mark style="background: #FFB86CA6;">You can configure route-based VPNs to connect Palo Alto Networks firewalls that are at two sites</mark> or to connect a Palo Alto Networks firewall to a third-party security device at another location.

The Palo Alto Networks firewall sets up a <strong>route-based VPN</strong>. <mark style="background: #FFF3A3A6;">The firewall makes a <strong>routing decision</strong> for the VPN</mark> based on the destination IP address. 

<mark style="background: #CACFD9A6;">Before a VPN tunnel can be set up</mark>, <mark style="background: #BBFABBA6;">peers need to be <strong>authenticated</strong></mark>. 
After successful authentication, the <mark style="background: #ABF7F7A6;">peers negotiate the <strong>encryption</strong> mechanism and algorithms to secure the communication</mark>. 

<mark style="background: #ADCCFFA6;">The <strong>Internet Key Exchange</strong> (<strong>IKE</strong>) process <strong>authenticates</strong> the VPN peers</mark>, and <mark style="background: #D2B3FFA6;"><strong>IPsec Security Associations</strong> (<strong>SAs</strong>) are defined at <strong>each end</strong> of the tunnel to <strong>secure</strong> the VPN communication</mark>. 

<mark style="background: #CACFD9A6;"><strong>IKE</strong> uses <mark style="background: #FF5582A6;">digital certificates</mark> or <mark style="background: #FFB86CA6;">preshared keys</mark> and <mark style="background: #FFF3A3A6;">the <strong>Diffie-Hellman</strong> (<strong>DH</strong>) <strong>keys</strong></mark> to set up the <strong>SAs</strong> for the <strong>IPsec tunnel</strong></mark>. 

<mark style="background: #BBFABBA6;">The <strong>SAs</strong> specify all of the parameters that are required for secure transmission, <mark style="background: #ABF7F7A6;">including the <strong>security parameter index (SPI)</strong></mark>, <strong>security protocol</strong>, <mark style="background: #ADCCFFA6;">cryptographic keys</mark>, <mark style="background: #D2B3FFA6;">destination IP address</mark>, <mark style="background: #CACFD9A6;">encryption</mark>, <mark style="background: #FFB8EBA6;">data authentication</mark>, <mark style="background: #FF5582A6;">data integrity</mark>, and <mark style="background: #FFB86CA6;">endpoint authentication</mark></mark>.

# IPsec
<mark style="background: #FFB8EBA6;"><strong>IPsec</strong> is a suite of protocols</mark> for <mark style="background: #FFF3A3A6;"><strong>authenticating</strong> and <strong>encrypting</strong> the traffic</mark> between two peers.

The three most used protocols in the IPsec suite are <strong>IKE</strong>, <strong>ESP</strong>, and <strong>AH</strong>.

<strong>Internet Key Exchange (IKE)</strong> is used to negotiate the <mark style="background: #FFB8EBA6;">AH and ESP password algorithm</mark> and put the necessary key of the algorithm to the right place.

<strong>Encapsulating Security Payload</strong>
<mark style="background: #BBFABBA6;">The <strong>IP Security (IPsec)</strong> set of protocols</mark> sets up <mark style="background: #ABF7F7A6;">a secure tunnel for VPN traffic</mark>. 
<mark style="background: #ADCCFFA6;">If the tunnel type</mark> is <strong>Encapsulating Security Payload (ESP)</strong>, <mark style="background: #ADCCFFA6;">the information in the TCP/IP packet is secured and encrypted</mark>. <mark style="background: #D2B3FFA6;">The IP packet (header and payload) is embedded in another IP payload</mark>, <mark style="background: #CACFD9A6;">and a new header is applied and then sent through the IPsec tunnel</mark>. <mark style="background: #BBFABBA6;">The <strong>source IP address</strong> in the new header is that of the <mark style="background: #FF5582A6;">local VPN peer</mark></mark> and <mark style="background: #BBFABBA6;">the <strong>destination IP address</strong> is that of the <mark style="background: #FF5582A6;">VPN peer at the far end of the tunnel</mark></mark>. <mark style="background: #ABF7F7A6;">When the packet reaches the remote VPN peer (the firewall at the far end of the tunnel), <mark style="background: #FF5582A6;">the outer header is removed</mark> and the original packet is sent to its destination</mark>.

<strong>Authentication Header (AH)</strong> is a security protocol for <mark style="background: #FFB86CA6;">authenticating the source of an IP packet</mark> and <mark style="background: #FFF3A3A6;">verifying the integrity of the IP packet content</mark>. The <strong>AH protocol</strong> <mark style="background: #ABF7F7A6;">verifies the authenticity and integrity of the content and the origin of a packet</mark>.

## Internet Key Exchange (IKE)
An IPsec tunnel is created in two phases.
### IKE Phase 1
With IKE Phase 1,<mark style="background: #FFF3A3A6;"> <u>each device is identified to the other by a <strong>peer ID</strong></u></mark>. In most cases, <mark style="background: #BBFABBA6;">this ID is just the <strong>public IP address</strong> of the device</mark>. <mark style="background: #ABF7F7A6;">In situations where the public ID is not static, this value can be replaced with a <strong>domain name</strong> or other text value</mark>. 

<mark style="background: #ADCCFFA6;">IKE Phase 1 provides <strong>authentication</strong> of the endpoints of the tunnel</mark> and <mark style="background: #D2B3FFA6;">creates a <strong>secure channel</strong> for the next phase of the VPN</mark>. <mark style="background: #FFB86CA6;">The IKE protocol uses the <strong>IKE-Crypto profile</strong> for negotiation</mark>.

During IKE Phase 1, five pieces of information are passed between peers:
![[IKE Phase 1.png]]
### IKE Phase 2
IKE Phase 2 creates the tunnel that will encapsulate data traffic.

IKE Phase 1 is concerned with authenticating the endpoints. <mark style="background: #FFF3A3A6;">IKE Phase 2 is concerned with data traffic that crosses the tunnel</mark>. <mark style="background: #BBFABBA6;">Each side of the tunnel has a <strong>proxy ID</strong> to identify the traffic that it will send</mark> <mark style="background: #ABF7F7A6;">and what it expects to receive</mark>. <mark style="background: #ADCCFFA6;">The IDs either can be a specific network range</mark> or <mark style="background: #D2B3FFA6;">a generic network of <strong>0.0.0.0/0</strong></mark>. <mark style="background: #CACFD9A6;">In either case, both sides need to know what the other side will send for the tunnel to work</mark>.

During IKE Phase 2, five pieces of information are passed between peers:
![[IKE Phase 2.png]]
# Route-Based Site-to-Site VPN
![[Route-Based Site-to-Site VPN.png]]
When a client that is secured by <strong>VPN Peer A</strong> needs content from a server at the other site, <mark style="background: #FFB8EBA6;"><strong>VPN Peer A</strong> initiates a connection request to <strong>VPN Peer B</strong></mark>. <mark style="background: #FFF3A3A6;">If the security policy permits the connection</mark>, <mark style="background: #BBFABBA6;"><strong>VPN Peer A</strong> uses the <strong>IKE Crypto profile parameters (IKE Phase 1)</strong> to <u>establish a secure connection</u></mark> and <mark style="background: #ABF7F7A6;"><u>authenticate</u> <strong>VPN Peer B</strong></mark>. Then, <mark style="background: #ADCCFFA6;"><strong>VPN Peer A</strong> uses the <strong>IPsec Crypto profile</strong> to <u>establish the <strong>VPN tunnel</strong></u></mark>, <mark style="background: #D2B3FFA6;">which defines the IKE phase 2 parameters to allow the secure transfer of data between the two sites</mark>.

## VPN Tunnel
Before you can set up VPNs, you must understand your network topology and be able to determine the required number of tunnels:
- One VPN tunnel might be enough to connect a single central site and a remote site.
- To connect a central site to multiple remote sites, you must create a VPN tunnel for each central site and remote site pair.

<mark style="background: #FFB8EBA6;">Each <strong>tunnel</strong> is bound to a <strong>tunnel interface</strong></mark>. <mark style="background: #FF5582A6;">The <strong>tunnel</strong> moves <strong>VPN traffic</strong> across the <strong>tunnel interface</strong></mark> <mark style="background: #FFB86CA6;">to the same <strong>virtual router</strong> as the incoming (cleartext) traffic</mark>. When a packet comes to the firewall, the route lookup function can identify the appropriate tunnel to use.

<mark style="background: #BBFABBA6;">The <strong>tunnel interface</strong> <u>appears to the system as a normal interface</u></mark>. <mark style="background: #ABF7F7A6;">The existing routing infrastructure can be applied</mark>.

<mark style="background: #ADCCFFA6;">Each <strong>tunnel interface</strong> can have a maximum of 10 <strong>IPsec tunnels</strong></mark>. <mark style="background: #D2B3FFA6;">Those <strong>IPsec tunnels</strong> can be used for <mark style="background: #FFF3A3A6;">multiple networks</mark> that are all associated with the <mark style="background: #FFF3A3A6;">same tunnel interface</mark> on the firewall</mark>.

To configure an IPsec VPN tunnel, you must create various components.

Create the tunnel interface or <mark style="background: #FF5582A6;">Phase 1 objects</mark>:
- To configure the interface in the web interface, navigate to **Network > Interfaces > Tunnel**. 
- The new <mark style="background: #FFB86CA6;">logical interface</mark> must be <mark style="background: #FFF3A3A6;">added to a Layer 3 zone</mark> <mark style="background: #BBFABBA6;">and to a virtual router</mark>, just as any other logical Layer 3 interface is handled.

Configure the IPsec tunnel or <mark style="background: #FF5582A6;">Phase 2 objects</mark>:
- You can use <mark style="background: #ABF7F7A6;">the basic interface when you create a tunnel between PAN-OS devices with known IP addresses</mark>. 
- The only values that are required are the <mark style="background: #ADCCFFA6;">tunnel interface to use</mark>, <mark style="background: #D2B3FFA6;">the local peer ID</mark>, <mark style="background: #CACFD9A6;">the remote peer ID</mark>, and <mark style="background: #FFB8EBA6;">the pre-shared key (PSK)</mark>.
- <mark style="background: #FFF3A3A6;">If the configuration is site-to-site with another Palo Alto Networks firewall, use the default Crypto profiles</mark>.
- <mark style="background: #BBFABBA6;">If the configuration is site-to-site with a different vendor’s firewall, configure the advanced settings in the Crypto profiles to match</mark>.

<mark style="background: #ABF7F7A6;">Add a static route to the virtual router or enable a dynamic routing protocol such as BGP, OSPF, or RIP</mark>. 

Then create a <mark style="background: #FF5582A6;">Security policy rule</mark> to allow the tunnel traffic:
- <mark style="background: #FFB86CA6;">Add a route table entry</mark> <mark style="background: #BBFABBA6;">for the remote network that points to the tunnel interface</mark> that is used in step 1 and step 2. 
- <mark style="background: #ADCCFFA6;">Create a route for the remote network that uses the tunnel interface</mark>.
- No next-hop IP address is required when tunnel interfaces are used.
- You must create a Security policy rule to allow tunneled traffic.