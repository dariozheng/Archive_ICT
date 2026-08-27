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
- <mark style="background: #FFB8EBA6;">The <strong>advertising router</strong> modifies the <strong>BGP next-hop address</strong> to the <strong>IP address sourcing the BGP connection</strong></mark>.
- The <strong>advertising router</strong> <mark style="background: #FF5582A6;">prepends</mark> its <strong>ASN</strong> to the existing <strong>AS_Path</strong> attribute.
- <mark style="background: #ABF7F7A6;">The receiving router verifies that the <strong>AS_Path</strong> attribute does not contain an <strong>ASN</strong> that matches the local ASN (his own)</mark>. BGP discards the route if it fails the <strong>AS_Path</strong> loop prevention check.
The configurations for eBGP and iBGP sessions are fundamentally the same except that the ASN in the <strong>remote-as</strong> statement is different from the ASN defined in the BGP process.

The figure shows the <strong>eBGP</strong> and <strong>iBGP</strong> sessions that would be needed between the routers to allow reachability between AS 65100 and AS 65300. Notice that all routers in AS 65200 establish iBGP sessions in a full mesh to allow for proper forwarding between AS 65100 and AS 65300.
![[Pasted image 20260827112403.png]]
# BGP Messages

| Type | Name         | Functional Overview                            |
| ---- | ------------ | ---------------------------------------------- |
| 1    | OPEN         | Sets up and establishes BGP adjacency          |
| 2    | UPDATE       | Advertises, updates, or withdraws routes       |
| 3    | NOTIFICATION | Indicates an error condition to a BGP neighbor |
| 4    | KEEPALIVE    | Ensures that BGP neighbors are still alive     |
## OPEN
An OPEN message is used to establish a BGP adjacency. 

Both sides negotiate session capabilities before BGP peering is established. 

The OPEN message contains the BGP version number, the <strong>ASN of the originating router</strong>, the <strong>hold time</strong>, the <strong>BGP identifier</strong>, and other optional parameters that establish the session capabilities.
### Hold time 
The hold time field in the OPEN message sets the proposed value for the hold timer in seconds, for each BGP neighbor. 

The hold timer in conjunction with keepalive messages is a heartbeat mechanism for BGP neighbors to ensure that a neighbor is healthy and alive.
When establishing a BGP session, the routers use the smaller hold time value contained in the two routers’ OPEN messages. 
The hold time value must be at least 3 seconds, or set to 0 to disable keepalive messages. For Cisco routers, the default hold timer is 180 seconds.
### BGP identifier
The <strong>BGP router ID (RID)</strong> is a 32-bit unique number that identifies the BGP router in the advertised prefixes. 
The RID can be used as a loop-prevention mechanism for routers advertised within an AS. 
The RID can be set manually or dynamically for BGP. A nonzero value must be set in order for routers to become neighbors.
## KEEPALIVE
BGP does not rely on the TCP connection state to ensure that the neighbors are still alive. 
<strong>KEEPALIVE</strong> messages are exchanged every one-third of the hold timer agreed upon between the two BGP routers. 
Cisco devices have a default hold time of 180 seconds, so the default keepalive interval is 60 seconds. If the hold time is set to 0, then no keepalive messages are sent between the BGP neighbors.
## UPDATE
An <strong>UPDATE</strong> message advertises any feasible routes, withdraws previously advertised routes, or can do both. 

An UPDATE message includes the advertised prefixes in the <strong>Network Layer Reachability Information (NLRI) PA</strong>, as well as other associated <strong>BGP PAs</strong>. 

<mark style="background: #FFB8EBA6;">Prefixes that need to be withdrawn</mark> are <mark style="background: #FF5582A6;">advertised in the</mark> <strong>WITHDRAWN ROUTES</strong> <mark style="background: #FF5582A6;">field of the UPDATE message</mark>. 

An <strong>UPDATE</strong> message can act as a keepalive to reduce unnecessary traffic. <mark style="background: #FFB86CA6;">Upon receipt of an UPDATE, the hold timer resets to the initial value</mark>. <mark style="background: #BBFABBA6;">If the hold timer reaches zero</mark>, <mark style="background: #ABF7F7A6;">the BGP session is torn down</mark>, <mark style="background: #ADCCFFA6;">routes from that neighbor are removed</mark>, <mark style="background: #D2B3FFA6;">and an UPDATE message is sent to other BGP neighbors to withdraw the affected prefixes</mark>.

## NOTIFICATION
A <strong>NOTIFICATION</strong> message is sent when an error is detected with the BGP session, such as a hold timer expiring, neighbor capabilities changing, or a BGP session reset being requested. This causes the BGP connection to close.
# BGP Neighbor States
BGP forms a TCP session with neighbor routers called _peers_. BGP uses the <strong>finite-state machine (FSM)</strong> to maintain a table of all BGP peers and their operational status. The BGP session may report the following states:
- Idle
- Connect
- Active
- OpenSent
- OpenConfirm
- Established
![[Pasted image 20260827114532.png]]
## Idle 
Idle is the fist stage of the <strong>BGP FSM</strong>.  <mark style="background: #FFB8EBA6;">BGP detects a start event</mark> and <mark style="background: #FF5582A6;">tries to initiate a TCP connection to the BGP peer</mark> and <mark style="background: #FFB86CA6;">also listens for a new connection from a peer router</mark>.

If an error causes BGP to go back to the Idle state for a second time, the ConnectRetryTimer is set to 60 seconds and must decrement to zero before the connection can be initiated again. Further failures to leave the Idle state result in the ConnectRetryTimer doubling in length from the previous time.
## Connect 
In the <strong>Connect</strong> state, BGP initiates the TCP connection. If the three-way TCP handshake is completed, the established BGP session process resets the <strong>ConnectRetryTimer</strong> and sends an <strong>Open</strong> message to the neighbor; it then changes to the <strong>OpenSent</strong> state.

If the <strong>ConnectRetryTimer</strong> depletes before this stage is complete, a new TCP connection is attempted, the <strong>ConnectRetryTimer</strong> is reset, and the state stays in <strong>Connect</strong>. 
If the TCP connection fails, the state changes to <strong>Active</strong>. For any other events, the state is changed to <strong>Idle</strong>.

BGP routers use TCP port 179 to listen for incoming connections and as the destination port to connect to BGP peers. The router initiating the outgoing TCP connection uses a random source port and the destination port 179.

![[Pasted image 20260827115619.png]]
## Active
In the <strong>Active</strong> state, BGP starts a new three-way TCP handshake. 

If a connection is established, an <strong>Open</strong> message is sent, the hold timer is set to 4 minutes, and the state moves to <strong>OpenSent</strong>. 

If this attempt for TCP connection fails, the state moves back to the <strong>Connect</strong> state, and the <strong>ConnectRetryTimer</strong> is reset.

## OpenSent
In the OpenSent state, an Open message has been sent from the originating router and is awaiting an Open message from the other router. Once the originating router receives the OPEN message from the other router, both OPEN messages are checked for errors. The following items are examined:

- BGP versions must match.
- The source IP address of the OPEN message must match the IP address that is configured for the neighbor.
- The AS number in the OPEN message must match what is configured for the neighbor.
- BGP identifiers (RIDs) must be unique. If an RID does not exist, this condition is not met.
- Security parameters (such as password and TTL) must be set appropriately.

If the OPEN messages do not have any errors, the hold time is negotiated (using the lower value), and a <strong>KEEPALIVE</strong> message is sent (assuming that the value is not set to 0). The connection state is then moved to <strong>OpenConfirm</strong>. If an error is found in the <strong>OPEN</strong> message, a <strong>NOTIFICATION</strong> message is sent, and the state is moved back to Idle.

If TCP receives a disconnect message, BGP closes the connection, resets the <strong>ConnectRetryTimer</strong>, and sets the state to <strong>Active</strong>. Any other events in this process result in the state moving to <strong>Idle</strong>.

## OpenConfirm
In the OpenConfirm state, BGP waits for a <strong>KEEPALIVE</strong> or <strong>NOTIFICATION</strong> message. 

Upon receipt of a neighbor’s <strong>KEEPALIVE</strong> message, the state is moved to <strong>Established</strong>. If the hold timer expires, a stop event occurs, or if a <strong>NOTIFICATION</strong> message is received, the state is moved to <strong>Idle</strong>.

## Established
In the Established state, the <strong>BGP</strong> session is established. <strong>BGP</strong> neighbors exchange routes using <strong>UPDATE</strong> messages. As <strong>UPDATE</strong> and <strong>KEEPALIVE</strong> messages are received, the hold timer is reset. If the hold timer expires, an error is detected, and BGP moves the neighbor back to the Idle state.

# BGP Configuration
BGP router configuration requires the following components:
- <strong>BGP session parameters</strong>: BGP session parameters provide settings that involve establishing communication to the remote BGP neighbor. Session settings include the <mark style="background: #FF5582A6;">ASN of the BGP peer</mark>, <mark style="background: #FFB86CA6;">authentication</mark>, and <mark style="background: #FFF3A3A6;">keepalive timers</mark>.
- <strong>Address family initialization</strong>: The address family is initialized under the BGP router configuration mode. <strong>Network advertisement</strong> and <strong>summarization</strong> occur within the address family.
- <strong>Activate the address family on the BGP peer</strong>: For a session to initiate, <mark style="background: #BBFABBA6;">one address family for a neighbor must be activated</mark>. <mark style="background: #ABF7F7A6;">The router’s IP address is added to the neighbor table</mark>, and <mark style="background: #ADCCFFA6;">BGP attempts to establish a BGP session</mark> or <mark style="background: #CACFD9A6;">accepts a BGP session initiated from the peer router</mark>.

The following steps show how to configure BGP:

- Step 1. Initialize the BGP routing process with the global command **router bgp** _as-number_.

- Step 2.(Optional) Statically define the BGP router ID (RID). The dynamic RID allocation logic uses the highest IP address of any _up_ loopback interfaces. If there is not an _up_ loopback interface, then the highest IP address of any active _up_ interfaces becomes the RID when the BGP process initializes.
  
  To ensure that the RID does not change, a static RID is assigned (typically representing an IPv4 address that resides on the router, such as a loopback address). Any IPv4 address can be used, including IP addresses not configured on the router. Statically configuring the BGP RID is a best practice and involves using the command **bgp router-id** _router-id_.
  
  When the router ID changes, all BGP sessions reset and need to be reestablished.

- Step 3. Identify the BGP neighbor’s IP address and autonomous system number with the BGP router configuration command **neighbor** _ip-address_ **remote-as** _as-number_. 
  
  It is important to understand the traffic flow of BGP packets between peers. The source IP address of the BGP packets still reflects the IP address of the outbound interface. 
  
  When a BGP packet is received, the router correlates the source IP address of the packet to the IP address configured for that neighbor. If the BGP packet source does not match an entry in the neighbor table, the packet cannot be associated to a neighbor and is discarded.
  
- Step 4. Initialize the address family with the BGP router configuration command **address-family** _afi safi_. Examples of _afi_ values are IPv4 and IPv6, and examples of _safi_ values are unicast and multicast.
  
- Step 5. Activate the address family for the BGP neighbor with the BGP address family configuration command **neighbor** _ip-address_ **activate**.

![[Pasted image 20260827121711.png]]
# BGP Session Verification
The BGP session is verified with the command **show bgp** _afi safi_ **summary**. 

The example shows the IPv4 BGP unicast summary. Notice that the BGP RID and table version are the first components shown. The Up/Down column indicates that the BGP session is up for over 5 minutes.

![[Pasted image 20260827122551.png]]

| Field        | Description                                                                                                       |
| ------------ | ----------------------------------------------------------------------------------------------------------------- |
| Neighbor     | IP address of the BGP peer                                                                                        |
| V            | BGP version spoken by the BGP peer                                                                                |
| AS           | Autonomous system number of the BGP peer                                                                          |
| MsgRcvd      | Count of messages received from the BGP peer                                                                      |
| MsgSent      | Count of messages sent to the BGP peer                                                                            |
| TblVer       | Last version of the BGP database sent to the peer                                                                 |
| InQ          | Number of messages received from the peer and queued to be processed                                              |
| OutQ         | Number of messages queued to be sent to the peer                                                                  |
| Up/Down      | Length of time the BGP session is established or the current status if the session is not in an established state |
| State/PfxRcd | Current BGP peer state or the number of prefixes received from the peer                                           |
BGP neighbor session state, timers, and other essential peering information is available with the command **show bgp** _afi safi_ **neighbors** _ip-address_, as shown in the example.

---
R2# <strong>show bgp ipv4 unicast neighbors 10.12.1.1</strong>

<mark style="background: #ABF7F7A6;">The first section provides the neighbor's IP address, remote-as, indicates if the neighbor is 'internal' or 'external', the neighbor's BGP version, RID, session state, and timers</mark>.

BGP neighbor is <strong>10.12.1.1</strong>, <strong>remote AS65100</strong>, <strong>external link</strong>
  BGP <strong>version 4</strong>, remote router <strong>ID 192.168.1.1</strong>
  BGP state = Established, up for 00:01:04
  Last read 00:00:10, last write 00:00:09, <strong>hold is 180</strong>, <strong>keepalive is 60</strong> seconds
  Neighbor sessions:
    1 active, is not multisession capable (disabled)

<mark style="background: #BBFABBA6;">This second section indicates the capabilities of the BGP neighbor and address-families configured on the neighbor</mark>.                                           
  Neighbor capabilities:
    Route refresh: advertised and received(new)
    Four-octets ASN Capability: advertised and received
    Address family IPv4 Unicast: advertised and received
    Enhanced Refresh Capability: advertised
    Multisession Capability:
    Stateful switchover support enabled: NO for session 1
  Message statistics:
    InQ depth is 0
    OutQ depth is 0

<mark style="background: #ABF7F7A6;">This section provides a list of the BGP packet types that have been received or sent to the neighbor router</mark>.                                                         
                   Sent        Rcvd
    Opens:                    1           1
    Notifications:         0           0
    Updates:                0           0
    Keepalives:            2           2
    Route Refresh:      0           0
    Total:                      3           3
  Default minimum time between advertisement runs is 0 seconds

<mark style="background: #ADCCFFA6;">This section provides the BGP table version of the IPv4 Unicast address-family</mark>. <mark style="background: #CACFD9A6;">The table version is not a 1-to-1 correlation with routes as multiple route change can occur during a revision change</mark>. <mark style="background: #FFB8EBA6;">Notice the Prefix Activity columns in this section</mark>.                                                                
For address family: IPv4 Unicast
  Session: 10.12.1.1
  BGP table version 1, neighbor version 1/0
  Output queue size : 0
  Index 1, Advertise bit 0
                        Sent       Rcvd
  Prefix activity:                    ----       ----
    Prefixes Current:             0          0
    Prefixes Total:                  0          0
    Implicit Withdraw:           0          0
    Explicit Withdraw:           0          0
    Used as bestpath:         n/a          0
    Used as multipath:        n/a          0

							Outbound    Inbound
  Local Policy Denied Prefixes:    --------    -------
    Total:                                                  0          0

 Number of NLRIs in the update sent: max 0, min 0

<mark style="background: #FFB86CA6;">This section indicates that a valid route exists in the RIB to the BGP peer IP address</mark>, <mark style="background: #FFF3A3A6;">provides the number of times that the connection has established and time dropped, since the last reset</mark>, <mark style="background: #BBFABBA6;">the reason for the reset</mark>, if <strong>path-mtu-discovery</strong> is enabled, and ports used for the BGP session. 
   
 Address tracking is enabled, the RIB does have a route to 10.12.1.1
  Connections <strong>established 2</strong>; <strong>dropped 1</strong>
  <strong>Last reset 00:01:40</strong>, due to <strong>Peer closed the session</strong>
  Transport(tcp) <strong>path-mtu-discovery is enabled</strong>
Connection state is ESTAB, I/O status: 1, unread input bytes: 0
Minimum incoming TTL 0, Outgoing TTL 255
Local host: 10.12.1.2, Local port: <strong>179</strong>
Foreign host: 10.12.1.1, Foreign port: <strong>56824</strong>

---

# Route Advertisement
