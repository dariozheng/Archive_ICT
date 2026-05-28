---
categories:
  - "[[Security]]"
topic@security:
  - VPN
tags:
icon: SiWireguard
iconColor: "#87151F"
---
WireGuard securely encapsulates IP packets over UDP. 
You add a WireGuard interface, configure it with your private key and your peers' public keys, and then you send packets across it. 

All issues of key distribution and pushed configurations are _out of scope_ of WireGuard; these are issues much better left for other layers, lest we end up with the bloat of IKE or OpenVPN. In contrast, it more mimics the model of SSH and Mosh; both parties have each other's public keys, and then they're simply able to begin exchanging packets through the interface.
# Simple Network Interface
WireGuard works by adding a network interface (or multiple), like `eth0` or `wlan0`, called `wg0` (or `wg1`, `wg2`, `wg3`, etc). 

This network interface can then be configured normally using `ifconfig(8)` or `ip-address(8)`, with routes for it added and removed using `route(8)` or `ip-route(8)`, and so on with all the ordinary networking utilities. 

The specific WireGuard aspects of the interface are configured using the [`wg(8)`](https://git.zx2c4.com/wireguard-tools/about/src/man/wg.8) tool. 

This interface acts as a tunnel interface.

WireGuard associates tunnel IP addresses with public keys and remote endpoints. When the interface sends a packet to a peer, it does the following:

1. This packet is meant for 192.168.30.8. Which peer is that? Let me look... Okay, it's for peer `ABCDEFGH`. (Or if it's not for any configured peer, drop the packet.)
2. Encrypt entire IP packet using peer `ABCDEFGH`'s public key.
3. What is the remote endpoint of peer `ABCDEFGH`? Let me look... Okay, the endpoint is UDP port 53133 on host 216.58.211.110.
4. Send encrypted bytes from step 2 over the Internet to 216.58.211.110:53133 using UDP.

When the interface receives a packet, this happens:

1. I just got a packet from UDP port 7361 on host 98.139.183.24. Let's decrypt it!
2. It decrypted and authenticated properly for peer `LMNOPQRS`. Okay, let's remember that peer `LMNOPQRS`'s most recent Internet endpoint is 98.139.183.24:7361 using UDP.
3. Once decrypted, the plain-text packet is from 192.168.43.89. Is peer `LMNOPQRS` allowed to be sending us packets as 192.168.43.89?
4. If so, accept the packet on the interface. If not, drop it.

Behind the scenes there is much happening to provide proper privacy, authenticity, and perfect forward secrecy, using state-of-the-art cryptography.
# Cryptokey Routing
At the heart of WireGuard is a concept called _Cryptokey Routing_, <mark style="background: #ADCCFFA6;">which works by associating public keys with a list of <strong>tunnel IP addresses</strong> that are allowed inside the tunnel</mark>. <mark style="background: #ABF7F7A6;">Each network interface has a private key and a list of peers</mark>. <mark style="background: #D2B3FFA6;">Each peer has a public key</mark>. <mark style="background: #CACFD9A6;">Public keys are short and simple, and are used by peers to authenticate each other</mark>. <mark style="background: #FFB86CA6;">They can be passed around for use in configuration files by any out-of-band method</mark>, similar to how one might send their SSH public key to a friend for access to a shell server.

For example, a server computer might have this configuration:

`[Interface] PrivateKey = yAnz5TF+lXXJte14tji3zlMNq+hd2rYUIgJBgB3fBmk= ListenPort = 51820  [Peer] PublicKey = xTIBA5rboUvnH4htodjb6e697QjLERt1NAB4mZqp8Dg= AllowedIPs = 10.192.122.3/32, 10.192.124.1/24  [Peer] PublicKey = TrMvSoP4jYQlY6RIzBgbssQqY3vxI2Pi+y71lOWWXX0= AllowedIPs = 10.192.122.4/32, 192.168.0.0/16  [Peer] PublicKey = gN65BkIKy1eCE9pP1wdc8ROUtkHLF2PfAqYdyYBz6EA= AllowedIPs = 10.10.10.230/32`

And a client computer might have this simpler configuration:

`[Interface] PrivateKey = gI6EdUSYvn8ugXOt8QQD6Yc+JyiZxIhp3GInSWRfWGE= ListenPort = 21841  [Peer] PublicKey = HIgo9xNzJMWLKASShiTqIybxZ0U3wGLiUeJ1PKf8ykw= Endpoint = 192.95.5.69:51820 AllowedIPs = 0.0.0.0/0`

<mark style="background: #FFB8EBA6;">In the server configuration</mark>, <mark style="background: #FF5582A6;">each peer (a client) will be able to send packets to the network interface with a source IP matching his corresponding list of allowed IPs</mark>. For example, when a packet is received by the server from peer `gN65BkIK...`, after being decrypted and authenticated, if its source IP is 10.10.10.230, then it's allowed onto the interface; otherwise it's dropped.

<mark style="background: #FFB8EBA6;">In the server configuration</mark>, <mark style="background: #FFB86CA6;">when the network interface wants to send a packet to a peer (a client)</mark>, <mark style="background: #FFF3A3A6;">it looks at that packet's destination IP and compares it to each peer's list of allowed IPs to see which peer to send it to</mark>. For example, if the network interface is asked to send a packet with a destination IP of 10.10.10.230, it will encrypt it using the public key of peer `gN65BkIK...`, and then send it to that peer's most recent Internet endpoint.

<mark style="background: #FFB8EBA6;">In the client configuration</mark>, <mark style="background: #ABF7F7A6;">its single peer (the <strong>server</strong>) will be able to send packets to the network interface with <strong>any</strong> source IP (since 0.0.0.0/0 is a wildcard)</mark>. For example, when a packet is received from peer `HIgo9xNz...`, if it decrypts and authenticates correctly, with any source IP, then it's allowed onto the interface; otherwise it's dropped.

<mark style="background: #FFB8EBA6;">In the client configuration</mark>, <mark style="background: #BBFABBA6;">when the network interface wants to send a packet to its single peer (the <strong>server</strong>), it will encrypt packets for the single peer with <strong>any</strong> destination IP address (since 0.0.0.0/0 is a wildcard)</mark>. For example, if the network interface is asked to send a packet with any destination IP, it will encrypt it using the public key of the single peer `HIgo9xNz...`, and then send it to the single peer's most recent Internet endpoint.

In other words, when sending packets, the list of allowed IPs behaves as a sort of routing table, and when receiving packets, the list of allowed IPs behaves as a sort of access control list.

<mark style="background: #FF5582A6;">This is what we call a <strong>Cryptokey Routing Table</strong>: the simple association of public keys and allowed IPs</mark>.

Any combination of IPv4 and IPv6 can be used, for any of the fields. WireGuard is fully capable of encapsulating one inside the other if necessary.

Because all packets sent on the WireGuard interface are encrypted and authenticated, and because there is such a tight coupling between the identity of a peer and the allowed IP address of a peer, system administrators do not need complicated firewall extensions, such as in the case of IPsec, but rather they can simply match on "is it from this IP? on this interface?", and be assured that it is a secure and authentic packet. 
This greatly simplifies network management and access control, and provides a great deal more assurance that your iptables rules are actually doing what you intended for them to do.
# Built-in Roaming
The client configuration contains an _initial_ endpoint of its single peer (the server), so that it knows where to send encrypted data before it has received encrypted data. 

The server configuration doesn't have any initial endpoints of its peers (the clients). 

This is because the server discovers the endpoint of its peers by examining from where correctly authenticated data originates. If the server itself changes its own endpoint, and sends data to the clients, the clients will discover the new server endpoint and update the configuration just the same. Both client and server send encrypted data to the most recent IP endpoint for which they authentically decrypted data. Thus, there is full IP roaming on both ends.