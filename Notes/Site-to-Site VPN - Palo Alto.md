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

Before a VPN tunnel can be set up, <mark style="background: #BBFABBA6;">peers need to be authenticated</mark>. 
After successful authentication, the <mark style="background: #ABF7F7A6;">peers negotiate the encryption mechanism and algorithms to secure the communication</mark>. 

<mark style="background: #ADCCFFA6;">The <strong>Internet Key Exchange</strong> (<strong>IKE</strong>) process authenticates the VPN peers</mark>, and <mark style="background: #D2B3FFA6;"><strong>IPsec Security Associations</strong> (<strong>SAs</strong>) are defined at <strong>each end</strong> of the tunnel</mark> to secure the VPN communication. 

<mark style="background: #CACFD9A6;"><strong>IKE</strong> uses</mark> <mark style="background: #FF5582A6;">digital certificates</mark> or <mark style="background: #FFB86CA6;">preshared keys</mark> and <mark style="background: #FFF3A3A6;">the <strong>Diffie-Hellman</strong> (<strong>DH</strong>) <strong>keys</strong></mark> <mark style="background: #CACFD9A6;">to set up the <strong>SAs</strong> for the <strong>IPsec tunnel</strong></mark>. 
<mark style="background: #BBFABBA6;">The <strong>SAs</strong> specify all of the parameters that are required for secure transmission</mark>, <mark style="background: #ABF7F7A6;">including the <strong>security parameter index (SPI)</strong></mark>, <strong>security protocol</strong>, <mark style="background: #ADCCFFA6;">cryptographic keys</mark>, <mark style="background: #D2B3FFA6;">destination IP address</mark>, <mark style="background: #CACFD9A6;">encryption</mark>, <mark style="background: #FFB8EBA6;">data authentication</mark>, <mark style="background: #FF5582A6;">data integrity</mark>, and <mark style="background: #FFB86CA6;">endpoint authentication</mark>.

