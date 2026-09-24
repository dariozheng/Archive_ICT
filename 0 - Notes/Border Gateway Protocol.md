---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - category/networking/networking_general
  - encor/routing
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-08-26
aliases:
  - BGP
  - Border Gateway Protocol
  - MBGP
  - MP-BGP
---
<strong>Border Gateway Protocol (BGP)</strong> is the core [[Routing|routing]] protocol that manages how data packets are directed across the internet by exchanging routing and reachability information between different networks or [[Autonomous System]].

# Path Attributes
<strong>BGP</strong> uses <strong>path attributes (PAs)</strong> associated with each network path. 
<strong>BGP routers</strong> evaluate these attributes in a sequential order to prevent routing loops, classify prefixes, and determine the single best path to a network destination.

Every path attribute falls into one of four standard categories based on whether all routers must recognize it and whether it must be passed across different networks.
## Well-known mandatory
Every <strong>BGP-compliant router</strong> <mark style="background: #FFB8EBA6;">must recognize these attributes</mark>, and they <strong>must be included</strong> in every BGP route update message.
### AS_Path
<strong>AS_Path</strong> is a <strong>well-known mandatory attribute</strong> and <mark style="background: #FFB86CA6;">includes a complete list of all the ASNs</mark> that <mark style="background: #BBFABBA6;">the prefix advertisement has traversed</mark> from its <strong>source AS</strong>. 
<strong>AS_Path</strong> is used as a <mark style="background: #ADCCFFA6;">loop-prevention mechanism in BGP</mark>. 
If a <mark style="background: #ABF7F7A6;">BGP router receives a prefix advertisement with its AS listed in the AS_Path attribute</mark>, <mark style="background: #ADCCFFA6;">it discards the prefix because the router thinks the advertisement forms a loop</mark>.

![[Pasted image 20260901124137.png]]

The Path column has <strong>i</strong>, e, <strong>?</strong>, <strong>AS number</strong>, the AS_Path attribute is the AS number which identify the neighbor BGP routers. 
### ORIGIN
A well-known mandatory BGP path attribute used in the BGP best-path algorithm. 

The origin codes indicates how the network first entered the BGP, <strong>i</strong> for IGP (Interior Gateway Protocol), <strong>e</strong> for EGP (Exterior Gateway Protocol) and <strong>?</strong> for incomplete origin (redistributed routes). 
### NEXT_HOP
The specific IP address of the next router used to reach the destination.
Every single BGP route must have a valid, reachable next-hop IP address. 
If the router's routing table cannot find a valid path to reach this `NEXT_HOP` IP, the BGP route is completely ignored.

The column <strong>Next Hop</strong>.

![[Pasted image 20260901124137.png]]

## Well-known discretionary 
Every BGP router <strong>must recognize</strong> these attributes, but they are <strong>optional</strong> to include in a route update
### LOCAL_PREF
Instructs routers within the local network which path to prefer when exiting the system.
This is the primary tool for engineering <strong>outbound traffic</strong>. If your company has two internet providers, you give a higher <strong>Local Preference</strong> to your primary provider so all internal routers choose it first.
### ATOMIC_AGGREGATE
Warns downstream routers that specific routing data was lost due to route summarization.

![[Pasted image 20260901130128.png]]

## Optional transitive
Routers do not have to recognize these attributes. If a router does not recognize it, it will still <strong>keep the attribute intact and pass it along</strong> to neighboring routers.
### COMMUNITY
A tagging mechanism used to group destinations and apply routing policies dynamically.

While not part of the standard step-by-step decision tree, <strong>BGP Communities</strong> are <mark style="background: #FFB8EBA6;">strings of numbers</mark> used to <mark style="background: #FF5582A6;">group routes</mark>. It is heavily used by Internet Service Providers (ISPs) to let customers dynamically trigger `LOCAL_PREF` or `AS_PATH` changes on the provider's side.
### AGGREGATOR
Specifies the AS number and IP address of the router that performed route summarization.

![[Pasted image 20260902090457.png]]

## Optional non-transitive
Routers do not have to recognize these attributes. If a router does not recognize it, or if the route crosses into a different network, the attribute is <strong>quietly deleted and not passed forward</strong>.
### MED (Multi-Exit Discriminator)
Suggests to external neighbors which path they should prefer when entering your network if there are more path to the same network.

This is used to influence <strong>inbound traffic</strong> from a directly connected BGP neighbor. 
If you have two physical connections to the same provider, you send a lower MED value on the link you want them to use.
The <strong>Metric</strong> column:

![[Pasted image 20260902092819.png]]

### ORIGINATOR_ID
A tie-breaker ID (BGP router-IP) used to prevent routing loops in networks utilizing Route Reflectors.

![[Pasted image 20260903100646.png]]

- `10.23.1.1` (Next Hop): The IP where traffic is forwarded.
- `from 10.23.1.1` (BGP Peer IP): The actual IP address used to establish the TCP neighbor session.
- `(10.12.1.2)` (Remote BGP Router ID): This is the BGP Router ID of that peer. The neighbor router manually configured or automatically chose 10.12.1.2 as its Router ID, even though it is peering with you using its 10.23.1.1 interface.

# Address Families
An <strong>address family</strong> correlates to a specific network protocol, such as IPv4 or [[IPv6]], it uses an extension called <strong>address family identifier</strong> <strong>(AFI)</strong> and additional granularity is provided through a <strong>subsequent address-family identifier</strong> <strong>(SAFI)</strong> such as <strong>unicast</strong> or <strong>multicast</strong>.

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

![[Pasted image 20260827100535.png]]

In figure, R1 is able to establish a direct BGP session with R2. 
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

Injecting external BGP routes into an Interior Gateway Protocol (IGP)—like [[OSPF]] or EIGRP—to fix this issue is not viable for three reasons:

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
p
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

# Route Advertisement
<strong>BGP network statements</strong> do not enable


BGP for a specific interface; they <strong>identify specific network prefixes</strong> <mark style="background: #FFB86CA6;">to be installed into the BGP table</mark>, known as the <strong>Loc-RIB</strong> (The main BGP table that contains all the active BGP prefixes and path attributes that is used to select the best path and install routes into the RIB). 

After configuring a <strong>BGP network statement</strong>, the BGP process <strong>searches</strong> the <mark style="background: #FFB8EBA6;">RIB routes for an exact network prefix match</mark>. The route can be from a connected network, a secondary connected network, or any route from a routing protocol. <mark style="background: #BBFABBA6;">After verifying that the <strong>network statement</strong> matches a route in the RIB</mark>, <mark style="background: #ABF7F7A6;">the following <strong>BGP PAs</strong> are set</mark>, depending on the route type:
- <strong>Connected network</strong>: The next-hop BGP attribute is set to 0.0.0.0, the BGP origin attribute is set to <strong>i (IGP)</strong>, and the BGP weight is set to 32,768.
- <strong>Static route</strong> or <strong>routing protocol</strong>: The next-hop BGP attribute is set to the next-hop IP address in the RIB, the BGP origin attribute is set to <strong>i (IGP)</strong>, the BGP weight is set to 32,768, and the <strong>MED</strong> is set to the IGP metric.

After the <strong>BGP PAs</strong> are set, <mark style="background: #FFF3A3A6;">the route is installed into the <strong>Loc-RIB</strong></mark> (the BGP table). Not every route in the Loc-RIB is advertised to a BGP peer. <mark style="background: #FFB86CA6;">All routes in the Loc-RIB use the following process for advertisement to BGP peers</mark>:
1. Pass a validity check. Verify that the <strong>NLRI</strong> is valid and that the next-hop address is resolvable in the RIB. If the NLRI fails, the NLRI remains but does not process further.
2. Process outbound neighbor route policies. After processing, if a route was not denied by the outbound policies, the route is maintained in the <strong>Adj-RIB-Out</strong> for later reference.
3. Advertise the routes to BGP peers. If the <strong>next-hop BGP PA</strong> is <strong>0.0.0.0 </strong>for the prefixes in the NLRI PA, then the <strong>next-hop address</strong> is changed to the IP address of the BGP session (the IP of the BGP peer).

![[Pasted image 20260827144307.png]]

The <strong>network statement</strong> resides under the appropriate address family within the BGP router configuration. 

The command <strong>network</strong> _network_ <strong>mask</strong> _subnet-mask_ <strong>route-map</strong> _route- map-name_ is used for advertising IPv4 networks. 

The optional <strong>route-map</strong> provides a method of setting specific <strong>BGP PAs</strong> when the route installs into the Loc-RIB.

The figure illustrates R1 and R2 connected through the 10.12.1.0/24 network. The example demonstrates the configuration where both routers will advertise the Loopback 0 interfaces (192.168.1.1/32 and 192.168.2.2/32, respectively) and the 10.12.1.0/24 network into BGP. Notice that R1 uses the default IPv4 address family, and R2 explicitly specifies the IPv4 address family.

![[Pasted image 20260827145155.png]]

![[Pasted image 20260827145205.png]]

# Receiving Routes 
BGP uses three tables for maintaining the network prefix and path attributes (PAs) for a route:
- **Adj-RIB-In:** Contains the routes in original form (that is, from before inbound route policies are processed). To save memory, the table is purged after all route policies are processed.
- **Loc-RIB:** Contains all the routes that originated locally or were received from other BGP peers. After the routes pass the validity and next-hop reachability check, the BGP best-path algorithm selects the best route for a specific prefix. The Loc-RIB, also known as the BGP table, is used for presenting routes to the IP routing table (RIB).
- **Adj-RIB-Out:** Contains the routes after outbound route policies have been processed.

Not every route in the Loc-RIB is advertised to a BGP peer or installed into the RIB when received from a BGP peer. BGP performs the following route processing steps:

1. Store the route in the <strong>Adj-RIB-In</strong> in the original state and apply the inbound route policy based on the neighbor on which the route was received.
2. Update the <strong>Loc-RIB</strong> with the latest entry. The <strong>Adj-RIB-In</strong> is cleared to save memory.
3. Pass a validity check to <mark style="background: #FFF3A3A6;">verify that the route is valid</mark> and <mark style="background: #BBFABBA6;">that the next-hop address is resolvable in the RIB</mark>. If the route fails, the route remains in the Loc-RIB but is not processed further.
4. <mark style="background: #ADCCFFA6;">Identify the BGP best path</mark> and <mark style="background: #D2B3FFA6;">pass only the best path and its path attributes to step 5</mark>.
5. <mark style="background: #FFB8EBA6;">Install the best-path route into the RIB</mark>, process the outbound route policy, store the non-discarded routes in the <strong>Adj-RIB-Out</strong>, and advertise to BGP peers.

![[Pasted image 20260827150713.png]]

# Showing Routes

## show bgp afi safi

The command **show bgp** _afi safi_ displays the contents of the BGP table (Loc-RIB) on the router. Every entry in the Loc-RIB contains at least one path but could contain multiple paths for the same network prefix.
The example displays the BGP table on R1, which contains received routes and locally generated routes.

![[Pasted image 20260827153105.png]]

| Field           | Description                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Network         | A list of the prefixes installed in BGP. If multiple paths exist for the same prefix, only the first prefix is listed, and other paths leave an empty space in the output.<br>Valid paths are indicated by the * . <br>The path selected as the best path is indicated by an angle bracket (>).                                                                                                                                                     |
| Next Hop        | A <strong>well-known mandatory BGP path attribute</strong> that defines the IP address for the next hop for that specific path.                                                                                                                                                                                                                                                                                                                     |
| Metric          | <strong>Multiple-exit discrimator (MED)</strong>: An optional non-transitive BGP path attribute used in BGP for the specific path.                                                                                                                                                                                                                                                                                                                  |
| LocPrf          | <strong>Local Preference</strong>: A well-known discretionary BGP path attribute used in the BGP best-path algorithm for the specific path.                                                                                                                                                                                                                                                                                                         |
| Weight          | A locally significant Cisco-defined attribute used in the BGP best-path algorithm for the specific path.                                                                                                                                                                                                                                                                                                                                            |
| Path and Origin | <strong>AS_Path</strong>: A <strong>well-known mandatory BGP path attribute</strong> used for loop prevention and in the BGP best-path algorithm for the specific path.<br><br><strong>Origin</strong>: A well-known mandatory BGP path attribute used in the BGP best-path algorithm. A value of <strong>i</strong> represents an IGP, <strong>e</strong> indicates EGP, and <strong>?</strong> indicates a route that was redistributed into BGP. |

The command **show bgp** _afi safi network_ displays all the paths for a specific prefix and the BGP path attributes for that prefix. The example show the paths for the 10.12.1.0/24 prefix. The output includes the number of paths and which path is the best path.
The command **show bgp** _afi safi_ **detail** displays the entire BGP table with all the path attributes.

![[Pasted image 20260827154056.png]]

## show bgp afi safi neighbor ip-address advertised routes

The <strong>Adj-RIB-Out</strong> is a unique table maintained for <strong>each</strong> <mark style="background: #FFB8EBA6;">BGP peer</mark>. 
It enables a network engineer to view routes advertised to a specific router. 

The command **show bgp** _afi safi_ **neighbor** _ip-address_ **advertised routes** displays the contents of the Adj-RIB-Out for a specific neighbor.

The example shows the Adj-RIB-Out entries specific to each neighbor. Notice that the next-hop address reflects the local router and will be changed as the route advertises to the peer.

![[Pasted image 20260827163547.png]]

## show bgp ipv4 unicast summary

The **show bgp ipv4 unicast summary** command can also be used to verify the exchange of routes between nodes.

![[Pasted image 20260827163622.png]]
## show ip route bgp

The BGP routes in the global IP routing table (RIB) are displayed with the command **show ip route bgp**.

The example shows these commands in the sample topology. The prefixes are from an eBGP session and have an AD of 20, and no metric is present.

![[Pasted image 20260827163718.png]]
# BGP Route Advertisements from Indirect Sources
BGP session and route advertisement are two separate components. 
The figure shows a topology where R1 installs multiple routes learned from static routes, EIGRP, and OSPF. R1 can advertise these routes to R2.

![[Pasted image 20260831105421.png]]

The routing table for R1. Notice that R3’s loopback is learned via EIGRP, R4’s loopback is reached using a static route, and R5’s loopback is learned from OSPF.

![[Pasted image 20260831105729.png]]

The installation of R3’s and R4’s loopback use a <strong>network</strong> statement. R5’s loopback is learned by redistributing OSPF straight into BGP.

![[Pasted image 20260831105749.png]]

<mark style="background: #FFB8EBA6;">Redistributing routes learned from an IGP into BGP is completely safe</mark>; however, <mark style="background: #FF5582A6;">BGP learned routes should be redistributed into an IGP with caution</mark>. <mark style="background: #FFB86CA6;">BGP is designed for large scale and can handle a routing table the size of the Internet</mark> (940,000+ prefixes), <mark style="background: #FFF3A3A6;">whereas IGPs could have stability problems with fewer than 20,000 routes</mark>.

The image show the BGP routing tables on <strong>R1</strong> and <strong>R2</strong>.  
Notice that on <strong>R1</strong>, <mark style="background: #BBFABBA6;">the next hop matches the next hop learned from the RIB</mark>, the <strong>AS_Path</strong> is blank, and the origin code is _IGP_ (<mark style="background: #FFB8EBA6;">for routes learned from network statement</mark>) or _incomplete_ (<mark style="background: #FF5582A6;">redistributed</mark>). 
The metric is carried over from R3’s and R5’s IGP routing protocols and is reflected as the <strong>MED</strong>. 
R2 learns the routes strictly from eBGP and sees only the MED and the origin codes.

![[Pasted image 20260831110117.png]]

# IPv4 Route Summarization
<strong>Route summarization</strong>, also referred to as <strong>route aggregation</strong>, conserves router resources and accelerates best-path calculation by reducing the size of the table. 

<strong>Summarization</strong> also provides the benefit of stability by hiding route flaps from downstream routers, thereby reducing routing churn. 

While most service providers do not accept prefixes larger than /24 for IPv4 (/25 through /32), the Internet, at the time of this writing, still has more than 940,000 routes and continues to grow. 
Route summarization is required to reduce the size of the BGP table for Internet routers.

In the figure, R3 summarizes all the eBGP routes received from AS 65100 and AS 65200 to reduce route computation on R4 during link flaps. 

In the event of a link flap on the 10.13.1.0/24 network, R3 removes all the AS 65100 routes learned directly from R1 and identifies the same network prefixes via R2 with different path attributes (a longer AS_Path). 

R3 has to advertise new routes to R4 because of these flaps, which is a waste of CPU cycles because R4 receives connectivity only from R3. <mark style="background: #ABF7F7A6;">If R3 summarized the network prefix range, R4 would execute the best-path algorithm once and not need to run during link flaps of the 10.13.1.0/24 link</mark>.

![[Pasted image 20260831110747.png]]

There are two techniques for BGP summarization, in both methods of route aggregation, a new network prefix with a shorter prefix length is advertised into BGP. Because the aggregated prefix is a new route, the summarizing router is the originator for the new aggregate route: 
#### Static 
Create a static route to <strong>Null0</strong> for the summary network prefix and then advertise the prefix with a **network** statement. The downfall of this technique is that the summary route is always advertised, even if the networks are not available.

#### Dynamic 
Configure an aggregation network prefix. When viable component routes that match the aggregate network prefix enter the BGP table, then the aggregate prefix is created. The originating router sets the next hop to <strong>Null0</strong> as a discard route for the aggregated prefix for loop prevention.

## Aggregate Address
Dynamic route summarization is accomplished with the BGP address family configuration command **aggregate-address** _network subnet-mask_ <strong>summary-only</strong> <strong>as-set</strong>.

The figure removes the flapping serial link between R1 and R3 to demonstrate BGP route summarization and the effect of the <strong>aggregate-address</strong> command. 

![[Pasted image 20260831144427.png]]
This example shows the BGP tables for R1, R2, and R3 before route summarization is performed. R1’s stub networks (172.16.1.0/24, 172.16.2.0/24, and 172.16.3.0/24) are advertised through all the autonomous systems, along with the loopback addresses of R1, R2, and R3 (192.168.1.1/32, 192.168.2.2/32, and 192.168.3.3/32) and the peering links (10.12.1.0/24 and 10.23.1.0/24).

![[Pasted image 20260831145119.png]]
R1 aggregates all the stub networks (172.16.1.0/24, 172.16.2.0/24, and 172.16.3.0/24) into a 172.16.0.0/20 summary route. R2 summarizes all of the router’s loopback addresses into a 192.168.0.0/16 summary route. The example shows the configuration for R1 using the default IPv4 address family and R2 with the default IPv4 address family disabled.

![[Pasted image 20260831160345.png]]

Example shows the BGP tables for R1, R2, and R3 after summarization is configured on R1 and R2.

![[Pasted image 20260831160618.png]]

Notice that the 172.16.0.0/20 and 192.168.0.0/16 summary routes are visible, but the smaller component routes still exist on all the routers. The **aggregate-address** command advertises the summary route in addition to the original component routes. Using the optional **summary-only** keyword suppresses the component routes, and only the summary route is advertised. Example 11-17 shows the configuration with the **summary-only** keyword.

![[Pasted image 20260831160734.png]]

Example 11-18 shows the BGP table for R3 after the **summary-only** keyword is added to the **aggregate-address** command on R1 and R2. Notice that the 172.16.0.0/20 and 192.168.0.0/16 summary routes are visible, but the smaller component routes are no longer present.

![[Pasted image 20260831160802.png]]
Example 11-19 shows the BGP table and RIB for R2. Notice that the component loopback networks have been suppressed by BGP and are not advertised by R2. In addition, a summary discard route has been installed to Null0 as a loop-prevention mechanism.

![[Pasted image 20260831160842.png]]

Example 11-20 shows that R1’s stub networks have been suppressed, and the summary discard route for the 172.16.0.0/20 network has been installed in the RIB as well.

![[Pasted image 20260831160900.png]]

### Atomic Aggregate 
Summarized routes act like new BGP routes with a shorter prefix length. 

When a BGP router summarizes a route, it does not advertise the <strong>AS_Path</strong> information from before the route was summarized. 
BGP path attributes like AS_Path, <strong>MED</strong>, and <strong>BGP communities</strong> are not included in the new BGP advertisement. 

The **atomic aggregate** attribute indicates that a loss of path information has occurred.

![[Pasted image 20260901130128.png]]

## Route Aggregation with AS_SET
To keep the BGP path information history, the optional **as-set** keyword may be used with the **aggregate-address** command. As the router generates the summary route, BGP path information from the component routes is copied over to it. The AS_Path settings from the original component routes are stored in the AS_SET portion of the AS_Path. The AS_SET, which is displayed within brackets, counts as only one hop, even if multiple ASs are listed.

![[Pasted image 20260910111646.png]]

Example shows the 172.16.0.0/20 summary route again, including the BGP path information copied into it. Notice that the AS_Path information now contains AS 65100.

![[Pasted image 20260910111723.png]]

# BGP Multihoming 
BGP multihoming is a method of providing redundancy and optimal routing that involves adding multiple links to external AS.

Multihomed environments should be configured so that branch routers cannot act as transit routers. In most designs, transit routing of traffic from another branch is undesirable, because WAN bandwidth may not be sized accordingly. Transit routing can be avoided by configuring outbound route filtering at each branch site.

In essence, the branch sites do not advertise what they learn from the WAN but advertise only networks that face the LAN.

If transit behavior is required, it is restricted to the data centers or specific locations as follows:
- Proper routing design can accommodate outages.
- Bandwidth can be sized accordingly.
- The routing pattern is bidirectional and predictable.

# Conditional Matching 

