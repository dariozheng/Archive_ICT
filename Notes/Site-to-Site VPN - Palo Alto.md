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
IPsec is a suite of protocols for <mark style="background: #FFF3A3A6;">authenticating and encrypting the traffic</mark> between two peers.

IPsec <strong>authenticates</strong> or <strong>encrypts</strong> packets or <strong>both</strong>:
- Internet Key Exchange (IKE)
- Encapsulating Security Payload (ESP): provides both data integrity and encryption
- Authentication Header (AH): only provides data integrity, no encryption

<mark style="background: #BBFABBA6;">The <strong>IP Security (IPsec)</strong> set of protocols</mark> sets up <mark style="background: #ABF7F7A6;">a secure tunnel for VPN traffic</mark>. 

<mark style="background: #ADCCFFA6;">If the tunnel type</mark> is <strong>Encapsulating Security Payload (ESP)</strong>, <mark style="background: #ADCCFFA6;">the information in the TCP/IP packet is secured and encrypted</mark>. <mark style="background: #D2B3FFA6;">The IP packet (header and payload) is embedded in another IP payload</mark>, <mark style="background: #CACFD9A6;">and a new header is applied and then sent through the IPsec tunnel</mark>. <mark style="background: #BBFABBA6;">The <strong>source IP address</strong> in the new header is that of the <mark style="background: #FF5582A6;">local VPN peer</mark></mark> and <mark style="background: #BBFABBA6;">the <strong>destination IP address</strong> is that of the <mark style="background: #FF5582A6;">VPN peer at the far end of the tunnel</mark></mark>. <mark style="background: #ABF7F7A6;">When the packet reaches the remote VPN peer (the firewall at the far end of the tunnel), <mark style="background: #FF5582A6;">the outer header is removed</mark> and the original packet is sent to its destination</mark>.