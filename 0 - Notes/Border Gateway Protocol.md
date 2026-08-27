---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - category/networking/networking_general
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-08-26
aliases:
  - BGP
  - Border Gateway Protocol
  - MBGP
  - MP-BGP
---
<strong>Border Gateway Protocol (BGP)</strong> is the core routing protocol that manages how data packets are directed across the internet by exchanging routing and reachability information between different networks or [[Autonomous System]].

# Path Attributes
<strong>BGP</strong> uses <strong>path attributes (PAs)</strong> associated with each network path. 
<strong>BGP routers</strong> evaluate these attributes in a strict, sequential order to prevent routing loops, classify prefixes, and determine the single best path to a network destination.

Every path attribute falls into one of four standard categories based on whether all routers must recognize it and whether it must be passed across different networks.

Per RFC 4271, <strong>well-known attributes</strong> must be recognized by all BGP implementations. <strong>Well-known mandatory attributes</strong> must be included with every prefix advertisement; <strong>well-known discretionary attributes</strong> may or may not be included with a prefix advertisement.

<strong>Optional attributes</strong> do not have to be recognized by all BGP implementations. Optional attributes can be set so that they are <strong>transitive</strong> and stay with the route advertisement from AS to AS. Other PAs are <strong>non-transitive</strong> and cannot be shared from AS to AS.
## Well-known mandatory
Every <strong>BGP-compliant router</strong> <mark style="background: #FFB8EBA6;">must recognize these attributes</mark>, and they <strong>must be included</strong> in every BGP route update message.
### AS_PATH
<strong>AS_PATH</strong> is a <strong>well-known mandatory attribute</strong> and <mark style="background: #FFB86CA6;">includes a complete list of all the ASNs</mark> that <mark style="background: #BBFABBA6;">the prefix advertisement has traversed</mark> from its <strong>source AS</strong>. 
<strong>AS_Path</strong> is used as a <mark style="background: #ADCCFFA6;">loop-prevention mechanism in BGP</mark>. 
If a <mark style="background: #ABF7F7A6;">BGP router receives a prefix advertisement with its AS listed in the AS_Path attribute</mark>, <mark style="background: #ADCCFFA6;">it discards the prefix because the router thinks the advertisement forms a loop</mark>.
### NEXT_HOP
The specific IP address of the next router used to reach the destination.
Every single BGP route must have a valid, reachable next-hop IP address. If the router's routing table cannot find a valid path to reach this `NEXT_HOP` IP, the BGP route is completely ignored.
### ORIGIN
Identifies how the route was first injected into BGP (e.g., via Interior Gateway Protocol, Exterior Gateway Protocol, or an incomplete/unknown source).
## Well-known discretionary 
Every BGP router <strong>must recognize</strong> these attributes, but they are <strong>optional</strong> to include in a route update
### LOCAL_PREF
Instructs routers within the local network which path to prefer when exiting the system.
This is the primary tool for engineering <strong>outbound traffic</strong>. If your company has two internet providers, you give a higher <strong>Local Preference</strong> to your primary provider so all internal routers choose it first.
### ATOMIC_AGGREGATE
Warns downstream routers that specific routing data was lost due to route summarization
## Optional transitive
Routers do not have to recognize these attributes. If a router does not recognize it, it will still <strong>keep the attribute intact and pass it along</strong> to neighboring routers.
### COMMUNITY
A tagging mechanism used to group destinations and apply routing policies dynamically.

While not part of the standard step-by-step decision tree, <strong>BGP Communities</strong> are <mark style="background: #FFB8EBA6;">strings of numbers</mark> used to <mark style="background: #FF5582A6;">group routes</mark>. It is heavily used by Internet Service Providers (ISPs) to let customers dynamically trigger `LOCAL_PREF` or `AS_PATH` changes on the provider's side.
### AGGREGATOR
Specifies the AS number and IP address of the router that performed route summarization.
## Optional non-transitive
Routers do not have to recognize these attributes. If a router does not recognize it, or if the route crosses into a different network, the attribute is <strong>quietly deleted and not passed forward</strong>.
### MED (Multi-Exit Discriminator)
Suggests to external neighbors which path they should prefer when entering your network.
This is used to influence <strong>inbound traffic</strong> from a directly connected neighbor. If you have two physical connections to the same provider, you send a lower MED value on the link you want them to use.
### ORIGINATOR_ID
A tie-breaker ID used to prevent routing loops in networks utilizing Route Reflectors.
# Address Families
An <strong>address family</strong> correlates to a specific network protocol, such as IPv4 or IPv6, it uses an extension called <strong>address family identifier</strong> <strong>(AFI)</strong> and additional granularity is provided through a <strong>subsequent address-family identifier</strong> <strong>(SAFI)</strong> such as <strong>unicast</strong> or <strong>multicast</strong>.

In BGP, the <strong>Network Layer Reachability Information</strong> (<strong>NLRI</strong>) is the prefix length and the prefix. 

Every address family <mark style="background: #FFB8EBA6;">maintains a separate database and configuration</mark> for each protocol (address family + sub-address family) in BGP. 

This allows for a routing policy in one address family to be different from a routing policy in a different address family, even though the router uses the same BGP session with the other router. 
<mark style="background: #FFB86CA6;">BGP includes an <strong>AFI</strong> and <strong>SAFI</strong> with every route advertisement</mark> to <mark style="background: #ADCCFFA6;">differentiate between the AFI and SAFI databases</mark>.

# Inter-Router Communication
BGP is designed as an inter-autonomous routing protocol, the neighbor adjacencies should not change frequently and are coordinated. 

BGP neighbor are defined by IP address. 

BGP uses TCP port 179 to communicate with other routers. 
TCP allows for handling of fragmentation, sequencing, and reliability (acknowledgment and retransmission) of communication packets. 
Most recent implementations of BGP set the do-not-fragment (DF) bit to prevent fragmentation and rely on path MTU discovery.

BGP by using TCP, <mark style="background: #BBFABBA6;">is capable of crossing network boundaries</mark> (that is, multi-hop capable) so while <mark style="background: #ABF7F7A6;">BGP can form neighbor adjacencies that are directly connected</mark>, <mark style="background: #ADCCFFA6;">it can also form adjacencies that are multiple hops away</mark>.

A <strong>BGP session</strong> refers to the <strong>established adjacency between two BGP routers</strong>. 
<strong>Multi-hop sessions</strong> require that the <mark style="background: #CACFD9A6;">router use an underlying route installed in the RIB</mark> (static or from any routing protocol) <mark style="background: #ABF7F7A6;">to establish the TCP session with the remote endpoint</mark>.

![[Pasted image 20260827100535.png]]In figure, R1 is able to establish a direct BGP session with R2. 
In addition, R2 is able to establish a BGP session with R4, even though it passes through R3. 
R1 and R2 use a directly connected route to locate each other. 
R2 uses a static route to reach the 10.34.1.0/24 network, and R4 has a static route to reach the 10.23.1.0/24 network. 
R3 is unaware that R2 and R4 have established a BGP session even though the packets flow through R3.

> [!NOTE]
> BGP neighbors connected to the same network use the ARP table to locate the IP address of the peer. 
> 
> Multi-hop BGP sessions require routing table information for finding the IP address of the peer. It is common to have a static route or an IGP running between iBGP neighbors for providing the topology path information to establish the BGP TCP session. A default route is not sufficient to establish a multi-hop BGP session.

# BGP Session Types
BGP session are categorized into two types: 
- <strong>Internal BGP (iBGP)</strong>: Sessions established with an <strong>iBGP</strong> router that are in the same AS or that participate in the same BGP confederation. 
  <strong>iBGP</strong> prefixes are assigned an administrative distance (AD) of 200 upon installation in the router's RIB. 
- <strong>External BGP (eBGP)</strong>: Sessions established with a BGP router that are in a different AS. 
  <strong>eBGP</strong> prefixes are assigned an AD of 20 upon installation in the router's RIB.
## iBGP
Internal BGP (iBGP) is required within an Autonomous System (AS) when running multiple routing policies or providing transit connectivity between external networks.

It is primarily used inside large enterprise networks or Service Provider (ISP) cores <strong>to distribute</strong> <mark style="background: #FFB86CA6;">external routing internet paths</mark> <strong>transitively</strong> <mark style="background: #BBFABBA6;">across the internal network</mark>.

For example, in the figure, **AS 65200** acts as a transit provider, connecting **AS 65100** (at router R2) to **AS 65300** (at router R4).
![[Pasted image 20260827104340.png]]

If R2 and R4 establish an iBGP session directly, the intermediate core router (R3) remains unaware of the external routes. As shown in figure, when transit traffic from either AS reaches R3, the router drops the packets because its routing table lacks the necessary forwarding information.
![[Pasted image 20260827104517.png]]
Injecting external BGP routes into an Interior Gateway Protocol (IGP)—like OSPF or EIGRP—to fix this issue is not viable for three reasons:

- **Scalability:** The global Internet routing table contains over 940,000 IPv4 prefixes. IGPs are not engineered to handle this volume of routes.
- **Routing Policy:** IGPs rely strictly on metrics (like bandwidth or delay) for path selection. BGP uses a multi-step decision process and path attributes, allowing it to intentionally choose longer or seemingly suboptimal paths to satisfy corporate routing policies.
- **Attribute Preservation:** IGPs cannot carry or preserve BGP-specific path attributes as a prefix travels across the internal network.

<mark style="background: #FF5582A6;">To ensure successful traffic forwarding</mark> through AS 65200, an <mark style="background: #ADCCFFA6;">iBGP session must be established between all internal routers (<strong>R2</strong>, <strong>R3</strong>, and <strong>R4</strong>) in a <strong>full-mesh topology</strong></mark>.

> [!NOTE]
> Transit connectivity is strictly a service provider function. Enterprise organizations are consumers and should never provide transit connectivity between autonomous systems over the Internet.

## eBGP
eBGP involves the exchange of network prefixes between AS. eBGP peerings are the core component of BGP on the Internet. eBGP involves the exchange of network prefixes between autonomous systems. The following behaviors are different on **eBGP sessions** than on **iBGP sessions**:
- <strong>Time-to-live (TTL)</strong> on <strong>eBGP</strong> packets is set to <strong>1</strong> by default. <mark style="background: #BBFABBA6;">eBGP packets drop in transit if a multi-hop BGP session is attempted</mark>. (TTL on iBGP packets is set to 255, which allows for multi-hop sessions.)
- The <strong>advertising router</strong> modifies the <strong>BGP next-hop address</strong> to the <strong>IP address sourcing the BGP connection</strong>.
- The <strong>advertising router</strong> prepends its <strong>ASN</strong> to the existing <strong>AS_Path</strong> attribute.
- The receiving router verifies that the <strong>AS_Path</strong> attribute does not contain an <strong>ASN</strong> that matches the local ASN. BGP discards the route if it fails the <strong>AS_Path</strong> loop prevention check.
