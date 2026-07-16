---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - ccnp
  - claude
  - encor/routing
  - category/networking/networking_general
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-07-15
---
Routing is the process of moving a packet toward a destination that is not on the local network. A host can deliver a frame directly only inside its own subnet; anything else has to be handed to a router, which repeats the same decision — where does this go next? — until the packet reaches the network that owns the destination address.

The subject splits into two questions that are easy to conflate:

- Where can I reach, and over which path? — learning routes and choosing between them.
- Where does this specific packet go, right now? — looking the destination up and forwarding it.

Everything else in this note — static routes, OSPF areas, BGP attributes, redistribution, VRFs — is machinery built in service of those two questions.

---

## Routing Fundamentals

### Routing and Switching

Layer 2 switching and Layer 3 routing solve different halves of the delivery problem, and the difference decides which table a device consults.

|Aspect|Layer 2 switching|Layer 3 routing|
|---|---|---|
|Address used|MAC address|IP address|
|Table consulted|MAC address table|routing table|
|Scope|one broadcast domain (VLAN / subnet)|between broadcast domains|
|Address structure|flat|hierarchical|
|Unknown destination|flood out every port in the VLAN|drop and return ICMP unreachable|
|Header changes|none|TTL decremented, checksum recomputed, L2 header rewritten|
|Learning|passive, from the source MAC of received frames|explicit, from configuration or a routing protocol|

A switch never really has to choose: a MAC address is either in the table or it is not, and because the address is flat there is nothing to compare. Routing needs [[#Route Selection|selection logic]] precisely because IP addresses are hierarchical — a single destination can be covered by several prefixes at once, learned from several sources, over several paths.

### Router

A router is any device with interfaces in two or more IP networks that forwards packets between them based on the destination address in the IP header. Its defining properties:

- It terminates the broadcast domain. Broadcasts and unknown-unicast floods do not cross it.
- It owns a subnet on each interface, and every host in that subnet uses the router's address as its [[#Default Gateway|default gateway]].
- It maintains a [[#The Routing Table|routing table]] describing every destination it believes is reachable.
- It rewrites the Layer 2 header on every packet it forwards, because the next hop is a different neighbor on a different medium.

#### Layer 3 Switch

A Layer 3 switch (multilayer switch) applies the same routing logic, but in ASIC hardware rather than software, and it combines routing with switching in one chassis. It routes between VLANs it already carries, using [[#Switched Virtual Interface|SVIs]] or [[#Routed Port|routed ports]] instead of physical WAN interfaces. On Cisco IOS the routing function is off until `ip routing` is configured.

The functional difference is not the algorithm — it is scale, interface types, and feature depth. A router terminates diverse WAN media and carries the heavy feature set (deep NAT, tunnels, extensive QoS); a Layer 3 switch pushes very high Ethernet port density at line rate.

### Hop-by-Hop Forwarding

No router knows the end-to-end path. Each router makes an independent, local decision using only its own table and only the destination address, then hands the packet on. The full path is an emergent property of many independent decisions.

Three consequences follow, and they explain most routing surprises:

- A router only needs to be right about the next hop, not about the whole path.
- The return path is chosen by different routers using their own tables, so it need not match the forward path. This is asymmetric routing, and it is normal — but it breaks stateful devices (firewalls, [[#Unicast RPF|strict uRPF]]) that expect to see both directions.
- If any router along the way disagrees with its neighbor about the direction of a prefix, the packet loops. The whole [[#Loop Prevention and Stability|loop prevention]] apparatus exists to keep independent decisions consistent.

### Control Plane

The control plane learns what exists. It runs the routing protocols, processes configuration, exchanges updates with neighbors, runs the protocol algorithms, and decides which route to install for each prefix. It is implemented in software on the CPU and it is comparatively slow — it operates on the timescale of events (a link failing, a neighbor announcing a prefix), not packets.

Its output is the [[#Routing Information Base|RIB]].

### Data Plane

The data plane moves packets. For each packet it does a destination lookup, decrements the TTL, rewrites the Layer 2 header, and transmits. It is implemented in ASIC or optimized software, and it operates at line rate on every packet.

Its input is the [[#Forwarding Information Base|FIB]].

```
   Configuration ─┐
   Static routes  ├──→ CONTROL PLANE ──→ RIB ──┐
   Routing protos ┘     (learn, select)        │
                                               ▼
                        DATA PLANE  ←────────  FIB
                        (lookup, rewrite, send)
```

The separation matters operationally: a prefix can be correct in the RIB and wrong or absent in the FIB, and packets follow the FIB. On any forwarding problem, check both.

### Forwarding Tables

#### Routing Information Base

The RIB is the routing table proper — the control plane's chosen best route for each prefix, drawn from every source that offered one. It stores routes the way protocols describe them, which means a next hop may still be an IP address that itself requires another lookup ([[#Recursive Lookup|recursion]]).

#### Forwarding Information Base

The FIB is derived from the RIB and optimized purely for lookup speed. The critical difference is that recursion is already resolved: every FIB entry points at a real exit interface and a real next hop, so the data plane never walks the table twice. It is organized for fast longest-prefix search and is programmed into hardware.

#### Adjacency Table

The adjacency table holds the Layer 2 rewrite information for each next hop — the destination MAC, the source MAC, and the frame type — populated from ARP, IPv6 Neighbor Discovery, and static mappings. The FIB says which next hop; the adjacency table says how to address the frame to it.

Splitting them is what makes forwarding cheap: when a neighbor's MAC changes, only one adjacency entry updates, not the thousands of FIB entries pointing through it.

### Switching Methods

Historically, three approaches to the forwarding decision, in increasing efficiency. Only the last is current, but the vocabulary persists in troubleshooting output.

#### Process Switching

Every packet is handed to the CPU, which does a full routing table lookup for each one. Correct, universal, and far too slow for production traffic. On a modern platform, sustained process switching means something has gone wrong — the packet is taking the [[#Punt to the CPU|punt path]].

#### Fast Switching

The first packet to a destination is process switched, and the result is cached. Subsequent packets to the same destination hit the cache. Traffic-driven — the cache is built by demand — which makes it unpredictable: the first packet of every flow is slow, and cache invalidation on topology change causes bursts of CPU load.

#### Cisco Express Forwarding

CEF is topology-driven rather than traffic-driven. It builds the [[#Forwarding Information Base|FIB]] and [[#Adjacency Table|adjacency table]] ahead of time, directly from the RIB and ARP table, so there is no first-packet penalty and no cache to invalidate. Every packet, including the first, is forwarded in hardware.

CEF is the default on all modern platforms and is a prerequisite for most features that touch the data plane — NetFlow, most QoS, [[#Unicast RPF|uRPF]], per-flow load sharing.

> [!note] Why CEF changes troubleshooting Because CEF pre-resolves everything, `show ip route` tells you what the control plane decided and `show ip cef` tells you what the data plane will actually do. When they disagree, believe CEF — the packets do.

---

## Addressing Foundations

Routing is entirely a consequence of how IP addresses are structured. These concepts are prerequisites rather than parts of routing, but every routing decision rests on them.

### IP Prefix

An IP address splits into a network portion and a host portion, and the boundary is set by the mask. The network portion — written as a prefix such as `10.1.4.0/24` — is the only part routing cares about. Routers forward toward prefixes; only the last router, the one that owns the subnet, cares about the host bits.

This is what makes routing scale. A router can describe a million hosts with one table entry, because it only needs to know the direction of their shared prefix.

### Classful Addressing

The original scheme fixed the network/host boundary by the leading bits of the address: Class A `/8`, Class B `/16`, Class C `/24`. The mask was implied by the address itself and therefore never carried in routing updates.

It failed on both ends — Class B networks were far too large for most organizations and Class C far too small — and it wasted enormous address space. It is dead, but its ghost lingers in protocol behavior ([[#RIP|RIPv1]] auto-summarizing at classful boundaries), in defaults, and in terminology.

### CIDR

Classless Inter-Domain Routing removed the fixed boundary. The mask became an explicit, arbitrary value carried alongside the address in every routing update, so a prefix can be any length.

Two things follow, and they are the foundation of the modern Internet:

- Allocation can match actual need, at any size.
- Prefixes can be aggregated. A block of contiguous smaller prefixes is advertised as one shorter prefix, which is what keeps the global [[#Border Gateway Protocol|BGP]] table finite. See [[#Summarization|summarization]].

### VLSM

Variable Length Subnet Masking is CIDR applied inside an organization: different subnets of the same major network can use different mask lengths. A point-to-point link gets a `/30` or `/31`, a user VLAN gets a `/24`, a loopback gets a `/32`.

VLSM requires that the routing protocol carry the mask in its updates. Every current protocol does; only RIPv1 and IGRP did not.

### Default Gateway

A host compares a destination against its own address and mask. If the destination is inside its subnet, it ARPs for the destination directly. If it is outside, the host cannot route — it simply hands the packet to its configured default gateway, addressing the frame to the gateway's MAC while leaving the destination IP untouched.

This is the boundary between hosts and routing. The host makes exactly one binary decision — local or not — and delegates everything else. It also makes the gateway a single point of failure, which is why [[#First Hop Redundancy|FHRPs]] exist.

> [!info] Frame versus packet The destination IP never changes as a packet crosses the network (barring NAT); the destination MAC changes at every hop. A host sending to the Internet writes the gateway's MAC and the server's IP into the same message. Confusing these two is the most common conceptual error in early routing work.

---

## The Routing Table

The routing table is the router's complete statement of belief about what is reachable and in which direction. It is a list of prefixes, each with the information needed to forward toward it.

### Route Entry Anatomy

Every entry carries the same fields, regardless of where the route came from.

|Field|Meaning|
|---|---|
|Destination prefix|The network and mask this entry describes. The only thing matched against a packet.|
|Route source|Which mechanism produced the route — connected, static, or a specific protocol. Shown as a one-letter code.|
|Administrative distance|How much the router trusts the source. Used to choose between sources offering the same prefix. See [[#Administrative Distance]].|
|Metric|The source protocol's own cost for this path. Used to choose between paths offered by the same source. See [[#Metric]].|
|Next hop|The neighbor's IP address to send toward. May need [[#Recursive Lookup|
|Exit interface|The local interface to transmit out of.|
|Route age|How long since the route was learned or last changed. A rapidly resetting age indicates [[#Route Flapping and Dampening|

The AD and metric are shown together in brackets, in that order: `[110/65]` is an OSPF route with a cost of 65.

### Connected and Local Routes

Two routes appear automatically for every interface that has an address and is up in both directions:

- The connected route (`C`) — the subnet itself, e.g. `10.1.4.0/24`. This is the router announcing that it owns this segment and can reach every host on it directly via ARP.
- The local route (`L`) — a host route for the router's own interface address, e.g. `10.1.4.1/32`. It tells the data plane that packets to this exact address are for the router itself and must be handed up the stack rather than forwarded.

Both have an [[#Administrative Distance|administrative distance]] of 0 — nothing outranks first-hand knowledge — and both disappear the instant the interface goes down. That disappearance is the trigger for everything else: withdrawing the prefix from routing protocols, activating [[#Floating Static Route|floating statics]], and running [[#SPF Algorithm|SPF]].

> [!important] Connected routes are the root of all routing Every dynamic route in the network is ultimately somebody's connected route, propagated. If an interface is not up/up with an address, no protocol can advertise its subnet, no matter how the protocol is configured.

### Gateway of Last Resort

The gateway of last resort is where packets go when nothing else matches — the next hop of the installed [[#Default Route|default route]]. A router without one drops any packet whose destination is not explicitly in the table and returns ICMP destination unreachable.

Whether a router should have one is a design decision. Edge and access routers almost always do. Core and Internet-facing routers carrying a full BGP table often deliberately do not, so that unroutable traffic is dropped immediately rather than being carried across the network first.

### Reading the Table

```cisco
Router# show ip route

Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2
       i - IS-IS, L1 - IS-IS level-1, L2 - IS-IS level-2, * - candidate default

Gateway of last resort is 203.0.113.1 to network 0.0.0.0

S*    0.0.0.0/0 [1/0] via 203.0.113.1
      10.0.0.0/8 is variably subnetted, 5 subnets, 3 masks
C        10.1.4.0/24 is directly connected, GigabitEthernet0/1
L        10.1.4.1/32 is directly connected, GigabitEthernet0/1
O        10.1.5.0/24 [110/65] via 10.1.4.2, 00:14:22, GigabitEthernet0/1
D        10.2.0.0/16 [90/30720] via 10.1.4.2, 01:02:11, GigabitEthernet0/1
O IA     10.9.9.9/32 [110/2] via 10.1.4.2, 00:14:22, GigabitEthernet0/1
B     192.0.2.0/24 [20/0] via 203.0.113.1, 00:44:03
```

Reading one line — `O 10.1.5.0/24 [110/65] via 10.1.4.2, 00:14:22, GigabitEthernet0/1` — the router learned `10.1.5.0/24` from OSPF (`O`), trusts OSPF at distance 110, computed a cost of 65, will send toward `10.1.4.2` out `Gi0/1`, and has held this route unchanged for 14 minutes.

The `is variably subnetted, 5 subnets, 3 masks` header is a [[#VLSM|VLSM]] artifact: it reports how many pieces of `10.0.0.0/8` are known and how many distinct mask lengths appear among them.

---

## Route Selection

A router is routinely offered the same destination by several sources over several paths. Three rules resolve this, and they are applied strictly in order. Nearly every "why is traffic going that way" question is answered by walking these three in sequence.

### Longest Prefix Match

The most specific prefix that covers the destination wins. Always. This rule is absolute and is evaluated before any consideration of source or cost.

For a packet to `10.1.4.7` against this table:

|Route|Covers the destination?|Prefix length|
|---|---|---|
|`0.0.0.0/0`|yes|0|
|`10.0.0.0/8`|yes|8|
|`10.1.4.0/24`|yes|24|
|`10.1.4.7/32`|yes|32|
|`10.1.5.0/24`|no|—|

The `/32` is used. The others are ignored entirely — not compared, not scored.

> [!warning] The rule that overrides every other rule A `/32` static route learned from a typo beats a `/24` from OSPF with a perfect cost, because the comparison never happens. AD and metric only ever compare routes for the _identical_ prefix. A router with a "wrong" path is far more often the victim of an unnoticed more-specific route than of a bad metric.

The rule exists to make hierarchy work. It is what allows a [[#Summarization|summary]] to be advertised broadly while a specific exception is advertised narrowly, and what lets the [[#Default Route|default route]] act as a catch-all without shadowing anything.

### Administrative Distance

When two different sources offer the _same_ prefix, the router cannot compare their metrics — an OSPF cost of 65 and an EIGRP metric of 30720 measure different things on different scales. Instead it compares how much it trusts each source. That trust value is the administrative distance: a 0–255 integer where lower is more trusted.

AD is purely local to the router. It is never advertised, never carried in an update, and two routers can disagree about it without any protocol noticing — which is exactly why AD manipulation is a powerful and dangerous tool.

#### Default Administrative Distances

|Route source|AD|
|---|---|
|Connected interface|0|
|Static route|1|
|EIGRP summary route|5|
|External BGP|20|
|Internal EIGRP|90|
|IGRP|100|
|OSPF|110|
|IS-IS|115|
|RIP|120|
|On-Demand Routing|160|
|External EIGRP|170|
|Internal BGP|200|
|Unknown / unusable|255|

The ordering encodes a rough judgement about reliability. First-hand knowledge (connected) outranks a human's assertion (static), which outranks a protocol's computation. Among protocols, EIGRP's [[#DUAL|DUAL]] is trusted over OSPF's [[#SPF Algorithm|SPF]], both over RIP's hop count. External routes are trusted less than internal ones of the same protocol, because they came from outside the protocol's own view. eBGP at 20 is trusted above every IGP, on the reasoning that a route from another autonomous system is authoritative about that AS; iBGP at 200 is trusted below every IGP, because that information is second-hand within your own AS.

> [!note] AD 255 means never A route at distance 255 is considered unusable and is never installed. Setting AD to 255 is a way of suppressing a route source entirely without removing the configuration.

### Metric

The metric is the cost of a path as measured by the protocol that learned it, and it is only ever compared against other routes to the same prefix from the same protocol. Each protocol measures something different, and the choice of measurement is the protocol's defining characteristic.

|Protocol|Metric|What it actually measures|
|---|---|---|
|RIP|hop count|number of routers crossed — ignores speed entirely|
|OSPF|cost|inverse of interface bandwidth, summed along the path|
|IS-IS|cost|an administratively assigned per-link value, summed|
|EIGRP|composite|slowest bandwidth on the path plus cumulative delay|
|BGP|no metric|replaced by a [[#Best Path Selection|

BGP is the outlier, and deliberately so. Inter-domain routing is about business relationships, not about which path is shortest, so BGP substitutes a tie-breaker list of attributes for a numeric cost.

### Selection Order

```
Packet arrives
   │
   ▼
1. Find every route covering the destination
   │
   ▼
2. Keep only the LONGEST prefix          ← absolute, ends the comparison
   │
   ▼
3. Among those, keep the LOWEST AD       ← chooses the source
   │
   ▼
4. Among those, keep the LOWEST metric   ← chooses the path
   │
   ▼
5. Still tied? Install all of them       → Equal-Cost Multipath
```

Steps 3 and 4 happen at installation time, not at forwarding time: the RIB already holds only the winner, so the data plane only ever performs step 2.

### Equal-Cost Multipath

When several paths survive with identical metrics, the router installs all of them and shares traffic across them. The number installed is capped by `maximum-paths` — commonly 4 by default, configurable higher.

With [[#Cisco Express Forwarding|CEF]], the sharing is per-destination by default: a hash over the source and destination address selects the path, so every packet of a given flow takes the same path.

|Mode|Behavior|Trade-off|
|---|---|---|
|Per-destination|hash of source/destination picks one path per flow|no reordering; can distribute unevenly with few flows|
|Per-packet|round-robin each packet across paths|perfectly even; reorders packets and hurts TCP badly|

Per-destination is effectively always correct. Per-packet exists for pathological cases and should be treated as a last resort.

> [!tip] ECMP looks broken with few flows Two 1 Gb links with ECMP will not carry 2 Gb of a single TCP flow — the hash pins that flow to one link. ECMP distributes conversations, not bits. Uneven utilization with a handful of large flows is expected behavior, not a fault.

### Unequal-Cost Load Balancing

Only EIGRP does this natively, via [[#EIGRP Variance|variance]]: paths with a metric up to _variance_ times the best metric are also installed, and traffic is shared in inverse proportion to their cost. No other IGP supports it; BGP approximates it with `dmzlink-bw`.

The safety condition is that only a [[#Successor and Feasible Successor|feasible successor]] is eligible — a path already proven loop-free — so the router never sends traffic down a worse path that turns out to point back at itself.

---

## The Forwarding Process

What a router actually does to a single packet, in order.

### Destination Lookup

The router reads the destination address from the IP header and performs a [[#Longest Prefix Match|longest prefix match]] against the [[#Forwarding Information Base|FIB]]. Three outcomes: a match, no match at all, or a match on the [[#Default Route|default route]]. No match means drop plus ICMP destination unreachable.

Note what is _not_ consulted. Not the source address, not the ports, not the application — plain IP forwarding is destination-only. Anything that considers other fields ([[#Policy-Based Routing|PBR]], NAT, ACLs) is an extra mechanism layered on top.

### Recursive Lookup

If a route names only a next-hop IP address and no exit interface, the router does not know which interface to use. It must look the _next hop_ up as a destination in its own table, find whatever route covers it, and inherit that route's exit interface.

```
S    192.0.2.0/24  via 10.1.4.2            ← next hop, no interface
                     │
                     ▼  look up 10.1.4.2
C    10.1.4.0/24   directly connected, Gi0/1
                     │
                     ▼
Resolved: 192.0.2.0/24 → out Gi0/1, next hop 10.1.4.2
```

Recursion must terminate on a route with a real exit interface, or the route is unusable and will not be installed. [[#Cisco Express Forwarding|CEF]] resolves the whole chain once at installation time and stores the flattened result, so the data plane pays no cost for it.

The danger is a recursive route resolving through the [[#Default Route|default route]], which is very nearly always a loop — the router sends the packet out the default to reach a next hop that only exists via the default. IOS deliberately refuses to resolve static routes this way.

### Frame Rewrite

The packet is re-encapsulated for the outbound medium: the old Layer 2 header is discarded entirely, and a new one is built from the [[#Adjacency Table|adjacency table]] — source MAC of the exit interface, destination MAC of the next hop, correct frame type for the medium.

This is why routing works across dissimilar media. The Layer 3 packet is medium-independent; only the wrapper changes.

### TTL Decrement

Every router decrements the IPv4 TTL (IPv6 Hop Limit) by one. At zero the packet is discarded and an ICMP Time Exceeded is returned to the source.

TTL is not an optimization — it is the last-resort guarantee that a [[#How Routing Loops Form|routing loop]] consumes bandwidth for a bounded time rather than forever. It also makes `traceroute` possible: sending probes with TTL 1, 2, 3… elicits one Time Exceeded per hop.

Because the TTL changes, the IPv4 header checksum must be recomputed at every hop. IPv6 removed the header checksum precisely to avoid this per-hop work.

### MTU and Fragmentation

If the packet is larger than the outbound interface's MTU, the router must do something:

- IPv4, DF bit clear — the router fragments the packet, and the destination reassembles.
- IPv4, DF bit set — the router drops it and returns ICMP Fragmentation Needed, carrying the MTU it could not meet.
- IPv6 — routers never fragment. The router drops it and returns ICMPv6 Packet Too Big.

Both signalling messages are ICMP, which is why blanket ICMP filtering breaks Path MTU Discovery and produces the classic symptom of small packets working while large transfers hang. Tunnels ([[#GRE|GRE]], [[#IPsec|IPsec]]) make this common by adding overhead to an already full-size packet.

### Punt to the CPU

Some packets cannot be handled by the data plane and are punted to the control plane CPU: packets addressed to the router itself (matching a local route), packets needing ICMP generation, packets with IP options, ARP resolution for an unresolved adjacency, and routing protocol traffic.

Punting is expensive and finite. An attack or a misconfiguration that punts high-rate traffic starves the control plane, and neighbor adjacencies drop — which is what [[#Control Plane Policing|CoPP]] defends against.

---

## Static Routing

A static route is a manually configured entry: an administrator asserting that a prefix is reachable in a given direction. The router does not verify the assertion beyond checking that the next hop resolves and the interface is up.

Static routes have an [[#Administrative Distance|AD]] of 1, so they beat every routing protocol for the same prefix.

### Next-Hop Static Route

```cisco
ip route 192.0.2.0 255.255.255.0 10.1.4.2
```

Names only the next hop, which forces a [[#Recursive Lookup|recursive lookup]] to find the exit interface. This is the right form on multi-access media such as Ethernet, because the router must ARP for a specific neighbor and this tells it which one.

### Directly Attached Static Route

```cisco
ip route 192.0.2.0 255.255.255.0 Serial0/0/0
```

Names only the exit interface, with no recursion. Valid only on point-to-point media, where there is exactly one possible neighbor and therefore nothing to resolve.

On Ethernet this form is a trap. The router treats the whole remote prefix as directly connected and ARPs for every individual destination address inside it. It appears to work if a neighbor runs proxy ARP, then fails mysteriously when proxy ARP is disabled, and meanwhile bloats the ARP table with one entry per remote host.

### Fully Specified Static Route

```cisco
ip route 192.0.2.0 255.255.255.0 GigabitEthernet0/1 10.1.4.2
```

Names both. No recursion is needed, and the route is withdrawn the moment the named interface goes down — the failure detection of the interface form, with the correctness of the next-hop form on Ethernet.

This is mandatory for [[#Link-Local Next Hop|IPv6 static routes over link-local next hops]], since a link-local address is only meaningful in the context of a specific interface.

### Default Route

```cisco
ip route 0.0.0.0 0.0.0.0 203.0.113.1
```

A route to `0.0.0.0/0` — a prefix of length zero, which by definition covers every possible destination. Because [[#Longest Prefix Match|longest prefix match]] rejects it whenever anything else matches, it never shadows a real route; it only catches what is left over. It becomes the [[#Gateway of Last Resort|gateway of last resort]].

The default route is the single most important scaling tool in routing. A branch router needs one entry to reach the entire Internet, because it has exactly one exit and no decision to make.

### Host Route

A `/32` (IPv4) or `/128` (IPv6) route to a single address. Automatically generated as the [[#Connected and Local Routes|local route]] of each interface, and configured explicitly to pull one specific host onto a particular path — for management access, for a service address, or to divert traffic to an inspection device.

Because a `/32` is the longest possible match, a host route overrides everything for that address. This makes it both the sharpest available tool and a common cause of "it works for everyone except that one server".

### Floating Static Route

```cisco
ip route 192.0.2.0 255.255.255.0 10.1.4.2
ip route 192.0.2.0 255.255.255.0 10.9.9.2 200
```

The trailing value overrides the default AD of 1. At AD 200 the second route is worse than any protocol-learned route, so it stays out of the table entirely while the primary path lives, and installs automatically only when the primary is withdrawn.

The AD must be chosen relative to what it is backing up: higher than the protocol it floats behind, and lower than 255. Backing up an OSPF route (110) means picking something above 110; backing up an iBGP route (200) means picking something above 200.

This is the standard idiom for backup WAN links — the dial/LTE/broadband path that carries nothing until the MPLS circuit fails.

### Null Route

```cisco
ip route 198.51.100.0 255.255.255.0 Null0
```

`Null0` is a virtual interface that discards everything sent to it, in hardware, at zero cost. Three uses:

- Blackholing. Traffic to a prefix is dropped at line rate — the basis of [[#Remotely Triggered Black Hole|RTBH]].
- Summarization anchor. A router advertising a [[#Summarization|summary]] installs a matching route to `Null0`, so traffic to a covered-but-nonexistent subnet is dropped locally instead of being forwarded back to the router that sent it. EIGRP, OSPF and BGP create this automatically when configured to summarize; with manual summaries it must be added by hand or the summary becomes a loop.
- Anchoring a BGP `network` statement so a prefix can be originated regardless of the state of any individual internal link.

### Static Route Tracking

A plain static route is only withdrawn if the next hop becomes unresolvable or the named interface goes down. Neither necessarily happens when the path is actually broken: if the failure is beyond the directly connected switch, the interface stays up and the router keeps forwarding into a black hole.

Object tracking fixes this by binding the route to a probe:

```cisco
ip sla 1
 icmp-echo 203.0.113.1 source-interface GigabitEthernet0/0
 frequency 5
ip sla schedule 1 life forever start-time now
!
track 1 ip sla 1 reachability
!
ip route 0.0.0.0 0.0.0.0 203.0.113.1 track 1
```

The route is installed only while the tracked object is up. This turns a static route into something with the one property it otherwise lacks — actual reachability verification — and is what makes [[#Floating Static Route|floating statics]] work reliably on Ethernet handoffs.

> [!warning] Track the far end, not the near end Probing the directly connected next hop only proves the local link works. Probe something on the far side of the provider — an address that is only reachable if the path genuinely works end to end.

### When Static Routing Fits

|Static routing|Dynamic routing|
|---|---|
|Predictable; the path is exactly what was typed|Adaptive; the path is recomputed on change|
|No CPU, memory, or bandwidth overhead|Consumes all three, continuously|
|No neighbor relationship to fail or be attacked|Neighbors must be formed, maintained, secured|
|Does not react to failure without [[#Static Route Tracking|tracking]]|
|Effort grows with the square of the network|Effort is roughly constant regardless of size|
|Silent failure modes; nothing tells you it is wrong|Failures are visible in protocol state|

Static routing is right for stub sites with one exit, for the default route at the edge, for blackholes, and for overriding a protocol deliberately. It is wrong anywhere there is a real choice of paths to make or more than a handful of routers, because the configuration burden and the silence of its failure modes both scale badly.

Real networks use both: a protocol for the interior, a default static at the edge, floating statics for backup.

---

## Dynamic Routing

A dynamic routing protocol lets routers discover each other, exchange reachability information, compute paths, and recompute them automatically when the topology changes. The trade is overhead and complexity for adaptability and scale.

### Protocol Classification

#### Interior and Exterior Gateway Protocols

|Class|Scope|Optimizes for|Protocols|
|---|---|---|---|
|IGP|inside one administrative domain|the technically best path — fast convergence, low cost|RIP, EIGRP, OSPF, IS-IS|
|EGP|between administrative domains|policy — business relationships, control over what is advertised|BGP|

The split reflects a difference in goal, not in scale. Inside your own network there is one authority and one definition of "best", so an IGP is free to just compute it. Between networks there is no shared authority, every party has commercial reasons to prefer paths that are not shortest, and nobody trusts anyone else's metrics — so BGP does not compute a best path at all. It applies [[#Best Path Selection|policy]].

#### Distance Vector

Each router advertises its _routing table_ to its directly connected neighbors — "here are the prefixes I can reach and how far away they are". A receiving router has no idea what the topology looks like. It knows only what its neighbors claim and how far they claim it is. It trusts them, adds its own cost, and re-advertises.

This is routing by rumour. It is simple and cheap, and it is why classic distance vector protocols converge slowly and are vulnerable to [[#How Routing Loops Form|loops]] — a router cannot tell whether a neighbor's advertisement is based on information the router itself supplied a moment ago. Everything in [[#Distance Vector Protections|split horizon, poisoning, and hold-down]] exists to patch this blindness.

RIP is the pure example. EIGRP is called advanced distance vector because [[#DUAL|DUAL]] adds enough topology awareness to escape most of the consequences.

#### Link State

Each router describes only its _own directly attached links_ and floods that description, unchanged, to every router in the area. Every router therefore ends up holding an identical database describing the whole topology — not routes, but the map itself — and independently runs a shortest-path algorithm over it.

Because each router computes from a complete map rather than a neighbor's summary, link-state protocols converge fast and are structurally loop-free within an area. The costs are memory and CPU to hold and process the database, and the fact that the flooding domain has to be bounded — which is exactly why [[#OSPF Areas|areas]] exist.

OSPF and IS-IS are the link-state protocols.

|Aspect|Distance vector|Link state|
|---|---|---|
|What is advertised|the sender's routing table|the sender's own links|
|What each router knows|neighbors' claims|the complete topology map|
|Sent to|directly connected neighbors only|flooded to the whole area|
|Computation|add own cost, compare|run SPF over the database|
|Convergence|slow, sequential router by router|fast, all routers compute in parallel|
|Loop risk|high; needs explicit protections|structurally low within an area|
|Resource use|low CPU and memory|significant CPU and memory|

#### Path Vector

A distance vector variant that advertises the complete list of autonomous systems a route has traversed instead of a numeric distance. That list — the AS_PATH — serves three purposes at once: loop detection (a router rejects any path already containing its own AS), a crude length metric, and a handle for policy.

BGP is the only path vector protocol in use.

#### Classful and Classless Protocols

A classful protocol does not carry the subnet mask in its updates; the receiver infers it from the address class. This makes [[#VLSM|VLSM]] impossible and forces automatic summarization at classful boundaries, which breaks discontiguous networks outright.

Classless protocols carry the mask explicitly. Every protocol still in use is classless — RIPv2, EIGRP, OSPF, IS-IS, BGP. The distinction survives only as history and as the reason `no auto-summary` exists.

### Protocol Mechanics

Below the differences, every dynamic protocol solves the same sequence of problems in the same order.

```
Discover neighbors  →  Form adjacency  →  Exchange information
                                                │
                                                ▼
                                       Compute best path
                                                │
                                                ▼
                                       Install into the RIB
                                                │
                                                ▼
                                   Maintain: hellos, updates, withdrawals
```

#### Neighbor Discovery

Before exchanging anything, routers must find each other and agree to talk. Most protocols multicast periodic hello packets; BGP is the exception and requires each peer to be configured explicitly.

|Protocol|Transport|Discovery|
|---|---|---|
|RIPv2|UDP 520|multicast 224.0.0.9|
|EIGRP|IP protocol 88|multicast 224.0.0.10|
|OSPF|IP protocol 89|multicast 224.0.0.5|
|IS-IS|directly over Layer 2|L1/L2 multicast MAC|
|BGP|TCP 179|none — peers are configured manually|

Adjacency requires agreement on a set of parameters, and a mismatch in any of them silently prevents the neighborship. The typical culprits are mismatched timers, mismatched [[#Protocol Authentication|authentication]], different subnets or masks on the same link, mismatched area or AS numbers, and an ACL blocking the protocol.

#### Route Advertisement

Once adjacent, routers exchange reachability, and the notable design choice is what happens afterwards. RIP re-sends its entire table every 30 seconds, whether or not anything changed. EIGRP, OSPF, IS-IS and BGP send a full exchange once, then send only incremental changes for the life of the adjacency, relying on hellos to confirm the neighbor is still there.

Incremental updating is what makes a protocol usable on a large or slow network. Periodic full updates waste bandwidth in proportion to table size and delay convergence to the update interval.

#### Convergence

Convergence is the interval during which routers disagree — the time from a topology change until every router again holds a consistent, correct, loop-free view. Traffic can be black-holed or looped for the whole of it, so convergence time is the single most important operational property of a protocol.

It decomposes into four stages, and each is attacked with different tools:

|Stage|What happens|Improved by|
|---|---|---|
|Detect|notice the failure|carrier loss, [[#Bidirectional Forwarding Detection|
|Propagate|tell the other routers|triggered updates, flooding|
|Compute|recalculate paths|efficient algorithms, [[#OSPF Areas|
|Install|program the RIB and FIB|hardware programming speed, [[#Fast Reroute|

Detection dominates. A protocol that recomputes in 50 ms but takes 40 seconds to notice the link is down converges in 40 seconds.

#### Timers

|Timer|Purpose|
|---|---|
|Hello|how often a keepalive is sent — proves the neighbor is alive|
|Hold / dead|how long without a hello before the neighbor is declared down. Conventionally 3× or 4× the hello|
|Update|how often routing information is sent (periodic protocols only)|
|Invalid / flush / hold-down|distance vector loop-suppression timers — see [[#Hold-Down Timer]]|

Hello and hold-down must match between neighbors in OSPF (a mismatch prevents adjacency) but need not match in EIGRP (each router advertises its own hold time). Lowering hellos speeds detection but increases CPU load and risks false failures under transient load — which is why [[#Bidirectional Forwarding Detection|BFD]] exists to do the job properly.

#### Router ID

A 32-bit value that uniquely identifies a router within a protocol domain. It is written like an IPv4 address but is not one — it is never routed to and need not be reachable. Used to identify database entries (OSPF LSAs, IS-IS system IDs), to break ties in elections and [[#Best Path Selection|best-path selection]], and to detect duplicates.

Selection order is: explicitly configured value, else the highest active loopback address, else the highest active physical interface address. It is chosen once at protocol start and does not change afterwards, even if that interface goes down.

Always configure it explicitly. Letting it be inferred means a routine interface change can silently reassign it on the next reload, which resets every adjacency and, in OSPF, invalidates the router's LSAs across the area.

#### Passive Interface

A passive interface still has its subnet advertised into the protocol, but the protocol sends no hellos and forms no adjacencies on it.

```cisco
router ospf 1
 passive-interface default
 no passive-interface GigabitEthernet0/1
```

The correct default posture is `passive-interface default` with explicit exceptions for the links that genuinely carry neighbors. This is both a security control — a routing protocol should never be offered to an access VLAN full of hosts, where anyone could form an adjacency and inject routes — and a hygiene one, since it stops needless multicast on every user segment.

#### Network Statement and Interface Selection

The `network` statement in the IGPs does not advertise a network. It selects _interfaces_: any interface whose address falls inside the specified range is enabled for the protocol, which then advertises that interface's real connected subnet — with its real mask — and starts sending hellos on it unless the interface is [[#Passive Interface|passive]].

```cisco
router ospf 1
 network 10.1.4.0 0.0.0.255 area 0
```

Two consequences that catch people out: the wildcard mask in the statement has nothing to do with the mask advertised (the interface's own mask is used), and a statement matching an interface you did not intend silently starts forming adjacencies out of it.

Modern configuration prefers enabling the protocol directly on the interface, which removes the indirection entirely:

```cisco
interface GigabitEthernet0/1
 ip ospf 1 area 0
```

---

## Interior Gateway Protocols

### RIP

The oldest IP routing protocol still in the standards. Obsolete in practice, but worth understanding because it is [[#Distance Vector|distance vector]] in its purest form and every one of its problems motivated a feature in the protocols that replaced it.

#### RIP Operation

Every 30 seconds each router broadcasts or multicasts its entire routing table to its neighbors. A receiving router adds 1 to the metric of each advertised route, and installs it if it is better than what it has, or if it came from the same neighbor that supplied the current route.

There is no neighbor relationship, no acknowledgement, and no concept of topology. A router that stops hearing about a route simply ages it out.

#### RIP Metric and Timers

The metric is hop count, and nothing else. A 64 kbps serial link one hop away beats a 100 Gbps path two hops away — RIP has no way to express the difference. Maximum usable metric is 15; 16 means unreachable and is used as the [[#Route Poisoning|poison]] value.

|Timer|Default|Purpose|
|---|---|---|
|Update|30 s|send the full table|
|Invalid|180 s|no update heard → mark the route unreachable|
|Hold-down|180 s|ignore worse information about the route while it settles|
|Flush|240 s|remove the route from the table entirely|

Those timers set the floor on convergence. Even in the best case a failure takes three minutes to clear, and [[#Counting to Infinity|counting to infinity]] can make it far worse.

#### RIPv2

Adds the pieces RIPv1 lacked: the subnet mask in updates (enabling [[#VLSM|VLSM]] and [[#CIDR|CIDR]]), multicast to 224.0.0.9 instead of broadcast, [[#Protocol Authentication|authentication]], and route tags. It retains automatic classful summarization for backward compatibility, which must be disabled with `no auto-summary` on any network with discontiguous subnets.

#### RIPng

RIP for IPv6. UDP port 521, multicast FF02::9, next hops expressed as link-local addresses. Structurally identical, and equally obsolete.

#### RIP Limitations

- Hop count ignores bandwidth entirely, so it routinely picks the worst path.
- Diameter of 15 hops caps network size.
- Timer-driven convergence measured in minutes.
- Full-table updates every 30 seconds regardless of change.
- No topology awareness, so loops must be patched with [[#Distance Vector Protections|split horizon and hold-down]].

Use it only where nothing else is supported. It survives mainly on small appliances and in labs.

### EIGRP

Cisco's advanced distance vector protocol, opened as an informational RFC in 2016. It keeps the distance vector model — routers advertise distances, not topology — but adds [[#DUAL|DUAL]], which stores enough information about alternatives to converge in sub-second time without ever risking a loop.

#### EIGRP Tables

|Table|Contents|
|---|---|
|Neighbor table|every adjacent EIGRP router, per interface, with hold time and queue state|
|Topology table|every route learned from every neighbor, with that neighbor's distance and the local distance through it|
|Routing table|only the [[#Successor and Feasible Successor|

The topology table is the key structure and the reason EIGRP is fast: alternatives are already known and pre-validated, so a failure is a table lookup rather than a recalculation.

#### EIGRP Packet Types

|Packet|Purpose|Reliable|
|---|---|---|
|Hello|discover and maintain neighbors|no|
|Update|advertise routes|yes|
|Query|ask neighbors about a route that has gone [[#Active and Passive States|active]]|
|Reply|answer a query|yes|
|ACK|acknowledge a reliable packet (a hello with a non-zero ack number)|no|
|SIA-Query / SIA-Reply|check whether a slow neighbor is still processing a query|yes|

Reliable delivery is provided by RTP (Reliable Transport Protocol), EIGRP's own acknowledgement mechanism — needed because EIGRP runs directly over IP with no TCP beneath it.

Hellos are sent every 5 seconds with a 15-second hold on high-speed links, and every 60 seconds with a 180-second hold on low-speed NBMA interfaces (T1 and below).

#### DUAL

The Diffusing Update Algorithm is what separates EIGRP from RIP. Rather than recomputing on failure, DUAL pre-computes which alternative paths are guaranteed loop-free and keeps them ready.

##### Feasible Distance and Reported Distance

|Term|Meaning|
|---|---|
|Reported distance (RD)|the metric the neighbor advertises — the neighbor's own cost to the destination. Also called advertised distance|
|Feasible distance (FD)|the local best metric to the destination — the neighbor's RD plus the cost of the link to that neighbor|

The distinction is the whole trick. RD is what the neighbor claims about _itself_; FD is what that means for _me_.

##### Successor and Feasible Successor

- Successor — the neighbor offering the lowest FD. Its path is installed in the routing table.
- Feasible successor — a backup neighbor whose path satisfies the [[#Feasibility Condition|feasibility condition]]. Held in the topology table, ready to be promoted instantly with no computation and no queries.

##### Feasibility Condition

> A neighbor is a feasible successor if its reported distance is strictly less than the current feasible distance.

`RD < FD`

The logic: if the neighbor's own cost to the destination is already lower than my best cost, then the neighbor cannot be reaching the destination through me — a path through me would have to cost at least as much as my own best path. So its path cannot loop back.

```
                    ┌──── B ────┐  RD(B)=10
   A ───────────────┤           ├──── DEST
     FD via B = 20  └──── C ────┘  RD(C)=25

   FD = 20  (best, via B — B is the successor)

   Is C feasible?   RD(C) = 25  <  FD = 20 ?   No.
                    → C is NOT a feasible successor, even though it works.
```

The condition is deliberately conservative. It rejects some perfectly good paths — C above may well be loop-free — because it is a purely local test with no topology knowledge, and a conservative local test is the price of guaranteed loop-freedom without a map.

##### Active and Passive States

- Passive — a successor exists and the route is stable. The normal state.
- Active — the successor was lost and no feasible successor existed, so the router is querying its neighbors for an alternative.

Passive is good. Active means the router is asking around, and the route is unusable until every query is answered. Losing a successor when a feasible successor exists never goes active at all — promotion is instant and no query is sent. That is the whole point of the [[#Feasibility Condition|feasibility condition]], and it is why EIGRP design work is really about maximizing the proportion of routes that have a feasible successor.

##### Stuck in Active

A query must be answered by every neighbor before the route can leave the active state, and each neighbor without an answer queries _its_ neighbors in turn. On a large, flat EIGRP network the query diffuses outward until it hits a boundary. If any router in that scope is slow or unreachable, the originator waits — and after the active timer (3 minutes by default) it declares the route Stuck In Active and resets the adjacency with the unresponsive neighbor.

SIA is the dominant EIGRP scaling failure. It is controlled by bounding query scope, which is what [[#EIGRP Summarization|summarization]] and [[#EIGRP Stub Routing|stub routing]] are for.

#### EIGRP Metric

The classic composite metric, with default K values (K1 = K3 = 1, K2 = K4 = K5 = 0), reduces to:

```
metric = 256 × ( 10^7 / minimum-bandwidth-kbps  +  cumulative-delay / 10 )
```

- Minimum bandwidth — the slowest link along the entire path, not the sum. A single slow hop dominates.
- Cumulative delay — the sum of every interface's configured delay, in tens of microseconds.

Load and reliability are available as inputs (K2, K4, K5) but are disabled by default, and should stay that way — they vary with traffic, so enabling them makes the metric change under load and the network oscillate.

Because bandwidth is a minimum and delay is a sum, delay is the correct knob for tuning EIGRP path preference: changing it affects only this protocol's view, whereas changing `bandwidth` also affects QoS calculations and interface statistics.

The K values must match between neighbors or the adjacency will not form.

> [!note] Wide metrics The classic metric saturates above about 10 Gbps — every faster interface computes to the same bandwidth term. EIGRP named mode introduces 64-bit wide metrics with a K6 term and a scaling constant, which restores discrimination on modern interface speeds. Classic and wide metrics interoperate through automatic scaling.

#### EIGRP Summarization

```cisco
interface GigabitEthernet0/1
 ip summary-address eigrp 100 10.1.0.0 255.255.0.0
```

Configured per interface, in any direction, at any router — not just at area boundaries, because EIGRP has no areas. This flexibility is EIGRP's main design advantage and its main design trap, since arbitrary summarization is easy to get wrong.

A summary creates a matching route to [[#Null Route|Null0]] locally at AD 5, so that traffic for a covered-but-nonexistent subnet is discarded rather than looped back.

Critically, a summary boundary is also a query boundary: a router that has summarized answers a query for a covered prefix itself, rather than propagating it. This is the primary defence against [[#Stuck in Active|SIA]].

#### EIGRP Stub Routing

```cisco
router eigrp 100
 eigrp stub connected summary
```

A stub router tells its neighbors that it is not a transit path. Neighbors then never send it queries, which removes it from the query diffusion entirely, and it advertises only the configured categories (connected, summary, static, redistributed).

Every spoke in a hub-and-spoke topology should be a stub. It costs nothing, prevents the spoke from ever being used as transit between two hubs, and is one of the two tools that keep EIGRP query scope bounded.

#### EIGRP Variance

```cisco
router eigrp 100
 variance 2
 traffic-share balanced
```

Enables [[#Unequal-Cost Load Balancing|unequal-cost load balancing]]. Any path whose metric is within _variance_ × FD is installed alongside the successor, and traffic is shared in inverse proportion to metric.

Only [[#Successor and Feasible Successor|feasible successors]] are eligible, so a variance path is always loop-free by construction. This is unique to EIGRP.

### OSPF

The dominant enterprise [[#Link State|link-state]] IGP. Open standard (RFC 2328), fast, and structurally loop-free within an area — at the cost of a rigid hierarchy that must be designed up front.

#### OSPF Areas

An area is a flooding domain. Every router inside one holds an identical [[#Link-State Database|LSDB]] and runs [[#SPF Algorithm|SPF]] over it; topology changes are flooded to every router in the area, and every one of them recomputes.

That is exactly why areas must be bounded. Without them, a single flapping link in a distant corner forces every router in the network to re-run SPF. Areas contain the flooding, contain the SPF computation, and provide the boundary at which [[#OSPF Summarization|summarization]] becomes possible.

##### Backbone Area

Area 0 is the backbone. Every other area must connect to it directly, and all inter-area traffic transits it. This is a hard requirement of the protocol, not a design guideline.

The reason is loop prevention. OSPF is only structurally loop-free _inside_ an area — between areas it degenerates to [[#Distance Vector|distance vector]] behaviour, since an [[#Router Roles|ABR]] advertises a distance to a prefix rather than the topology behind it. Forcing everything through a single hub area means the inter-area graph is a star, and a star cannot contain a loop.

A [[#Virtual Link|virtual link]] can patch an area that has become disconnected from area 0, but it is a repair, not a design.

##### Stub Area Types

External routes ([[#LSA Types|Type 5 LSAs]]) are flooded across the entire OSPF domain, which can dwarf the internal topology — a full Internet table redistributed into OSPF would destroy it. Stub area types trade external detail for a default route.

|Area type|Type 3 (inter-area)|Type 5 (external)|Type 7 (NSSA external)|Default injected by ABR|
|---|---|---|---|---|
|Standard|yes|yes|no|no|
|Stub|yes|blocked|no|yes|
|Totally stubby|blocked|blocked|no|yes|
|NSSA|yes|blocked|yes|optional|
|Totally NSSA|blocked|blocked|yes|yes|

- Stub — no externals. Every router in the area follows a default to the ABR to leave the OSPF domain.
- Totally stubby — no externals and no inter-area detail either. Routers hold only their own area plus one default. Cisco-specific, and the most aggressive reduction available.
- NSSA — a stub area that nevertheless contains an [[#Router Roles|ASBR]]. Its externals cannot be Type 5 (stub areas forbid those), so they are carried as Type 7 within the area and translated to Type 5 by the ABR on the way out.

Every router in an area must agree on its type, or adjacencies will not form — the flag is carried in the hello.

##### Virtual Link

A logical link that tunnels area 0 across a transit area, reconnecting a stranded area to the backbone. Legitimate as a temporary repair after a merger or a failure. As a permanent design element it signals that the area layout is wrong: it adds a dependency on the transit area, complicates troubleshooting, and cannot cross a stub area.

#### Router Roles

|Role|Definition|
|---|---|
|Internal router|all interfaces in one area|
|Backbone router|at least one interface in area 0|
|Area Border Router (ABR)|interfaces in two or more areas, one of which must be area 0. Generates [[#LSA Types|
|Autonomous System Boundary Router (ASBR)|injects external routes into OSPF via [[#Redistribution|

A router can hold several roles at once. The roles are consequences of where a router sits, not configuration.

#### Link-State Database

The LSDB is the map: a collection of LSAs, each describing one piece of the topology, flooded reliably and unchanged across the area. Its defining property is that every router in an area holds a byte-identical copy — if two routers disagree, one of them will compute a different tree and a loop becomes possible.

LSAs age. Each is refreshed by its originator every 30 minutes and expires at MaxAge (60 minutes) if the refresh stops.

##### LSA Types

|Type|Name|Originated by|Flooding scope|Describes|
|---|---|---|---|---|
|1|Router LSA|every router|its own area|the router's own links, costs, and neighbors|
|2|Network LSA|the [[#DR and BDR|DR]]|its own area|
|3|Summary LSA|ABR|other areas|a prefix in another area, and its cost|
|4|ASBR Summary LSA|ABR|other areas|how to reach an ASBR in another area|
|5|AS External LSA|ASBR|the whole domain except stub areas|a route redistributed from outside OSPF|
|7|NSSA External LSA|ASBR in an NSSA|its NSSA only|an external route, for translation to Type 5 by the ABR|
|9, 10, 11|Opaque LSA|any router|link, area, or AS|arbitrary extensions — used by MPLS-TE and [[#Segment Routing|

Types 1 and 2 are the actual topology; they never leave their area. Everything else is a description of something happening elsewhere.

The Type 4 exists to solve a subtle problem: a Type 5 names the ASBR as the origin, but a router in another area has no topology information about that ASBR and cannot compute a path to it. The Type 4 supplies exactly that.

##### OSPFv3 LSA Additions

|Type|Name|Purpose|
|---|---|---|
|8|Link LSA|link-local addresses and prefixes, per link|
|9|Intra-Area-Prefix LSA|carries prefixes, separated out of the Type 1/2|

The separation of prefixes from topology is the central OSPFv3 change — it lets the topology converge without re-running SPF for an address change.

#### SPF Algorithm

Each router runs Dijkstra's shortest-path-first algorithm over the [[#Link-State Database|LSDB]], with itself as the root, producing a tree of shortest paths to every destination in the area. Because every router computes over an identical database, all the trees are consistent — which is the structural reason OSPF cannot loop inside an area.

SPF is CPU-intensive and runs on any topology change within the area. Modern implementations throttle it (`timers throttle spf`) with an exponential backoff: fast for the first event, progressively slower under a storm of them.

Two important refinements: a change to a Type 3 or 5 LSA — a prefix elsewhere, not local topology — triggers only a partial SPF, which is much cheaper; and incremental SPF recomputes only the affected branch of the tree.

#### OSPF Cost

```
cost = reference-bandwidth / interface-bandwidth
```

Default reference bandwidth is 100 Mbps, so a 100 Mbps interface has cost 1. Everything faster also has cost 1, because the result is rounded up to a minimum of 1 — meaning that by default OSPF cannot distinguish FastEthernet from 100 Gigabit Ethernet.

```cisco
router ospf 1
 auto-cost reference-bandwidth 100000     ! 100 Gbps, in Mbps
```

This must be set identically on every router in the domain. An inconsistent reference bandwidth produces asymmetric costs and persistently suboptimal paths, and nothing warns you about it.

Cost is applied on the _outbound_ interface and summed along the path. `ip ospf cost` on an interface overrides the calculation entirely and is the cleanest way to tune a specific link.

#### Neighbor Adjacency

Routers must agree on all of the following before an adjacency forms. Any mismatch fails silently or leaves the neighbor stuck part-way:

- Area ID, and area type flags (stub / NSSA)
- Hello and dead intervals
- Subnet and mask on the link
- [[#Protocol Authentication|Authentication]] type and key
- MTU (checked during the database exchange)
- Unique router IDs

##### Neighbor States

|State|Meaning|
|---|---|
|Down|no hello heard|
|Attempt|NBMA only — actively trying a manually configured neighbor|
|Init|a hello was received, but it did not list us|
|2-Way|a hello was received listing us — bidirectional communication confirmed. [[#DR and BDR|
|ExStart|negotiating master/slave and sequence numbers|
|Exchange|trading database descriptors|
|Loading|requesting the LSAs found to be missing|
|Full|databases synchronized|

Two states are diagnostic rather than transient:

- Stuck in 2-Way — normal between two DROTHERs on a broadcast segment, which by design never go Full with each other. Only a problem if it happens between a DROTHER and the DR.
- Stuck in ExStart/Exchange — almost always an MTU mismatch. OSPF checks MTU in the database descriptor and refuses to proceed if it differs.

#### DR and BDR

On a multi-access segment with _n_ routers, full-mesh adjacency would require n(n−1)/2 relationships and n copies of every LSA. Instead the routers elect a Designated Router and a Backup DR, and everyone else (a DROTHER) adjacencies only with those two. Flooding goes to the DR (224.0.0.6), which redistributes it to everyone (224.0.0.5).

The DR also originates the [[#LSA Types|Type 2 Network LSA]] representing the segment itself as a pseudonode, which is what keeps the LSDB describing a star instead of a mesh.

Election rules:

- Highest interface priority wins; tie broken by highest [[#Router ID|router ID]].
- Priority 0 means never eligible.
- The election is non-preemptive. A new router with a better priority does not take over from a working DR — it waits for the DR to fail. Consequently, the DR is usually whichever router booted first, not whichever router you intended.

There is no DR on point-to-point links — there are only two routers, so there is nothing to optimize.

#### Network Types

|Network type|DR/BDR|Hello / Dead|Neighbors|
|---|---|---|---|
|Broadcast|yes|10 / 40|discovered by multicast|
|Non-broadcast (NBMA)|yes|30 / 120|configured manually|
|Point-to-point|no|10 / 40|discovered by multicast|
|Point-to-multipoint|no|30 / 120|discovered; treated as a set of p2p links|
|Point-to-multipoint non-broadcast|no|30 / 120|configured manually|
|Loopback|n/a|n/a|advertised as a `/32` host route regardless of the configured mask|

The network type is what determines whether there is a DR and which timers apply, and it must match between neighbors. Setting a point-to-point Ethernet link to `ip ospf network point-to-point` is standard practice — it removes a pointless DR election and speeds convergence.

#### OSPF Summarization

Unlike [[#EIGRP Summarization|EIGRP]], OSPF can only summarize at boundaries, because the LSDB inside an area must remain complete and identical everywhere. Two commands, two places:

|Command|Where|Summarizes|
|---|---|---|
|`area X range`|on an [[#Router Roles|ABR]]|
|`summary-address`|on an ASBR|external routes, into Type 5|

Both create a [[#Null Route|Null0]] discard route locally. This constraint is precisely why OSPF area design has to be done before addressing is assigned: if the prefixes inside an area are not contiguous, no summary is possible and the hierarchy achieves nothing.

#### OSPFv3

OSPF for IPv6 (RFC 5340), and a genuine redesign rather than a port:

- Runs per link, not per subnet. Multiple IPv6 subnets on one link share one adjacency.
- Neighbors are identified by [[#Router ID|router ID]] only, and next hops are [[#Link-Local Next Hop|link-local addresses]].
- Prefixes are removed from the Type 1 and Type 2 LSAs and carried in the new [[#OSPFv3 LSA Additions|Type 9]] instead, decoupling addressing from topology.
- Authentication is delegated to IPsec rather than built in.
- Adjacencies form over link-local addresses, so a link needs no global IPv6 address at all.
- Address families allow one OSPFv3 process to carry both IPv4 and IPv6.

The router ID is still a 32-bit value and must still be configured manually — with no IPv4 addresses on the box, there is nothing for it to infer one from, and the process will not start.

### IS-IS

The other [[#Link State|link-state]] protocol. Functionally very close to OSPF, but it originates from OSI rather than IP, and that origin gives it the properties that make it dominant in service provider cores.

#### IS-IS Addressing

IS-IS runs directly over Layer 2 — it is not carried in IP at all. Routers are identified by an NSAP-derived NET address:

```
49.0001.0000.0000.0001.00
│  │    │              └── NSEL, always 00 for a router
│  │    └── System ID, 6 bytes, must be unique
│  └── Area ID
└── AFI (49 = private)
```

Not being carried in IP is the protocol's defining structural advantage. IS-IS cannot be attacked over IP, does not depend on IP addressing to form adjacencies, and — crucially — was extended to carry IPv6 and MPLS labels by simply defining new TLVs, with no new protocol version and no separate process. That extensibility is why Segment Routing arrived on IS-IS first.

#### IS-IS Levels

|Level|Scope|Analogous to|
|---|---|---|
|Level 1|intra-area; knows only its own area, follows the nearest L1/L2 router out|OSPF non-backbone area|
|Level 2|inter-area backbone; carries routes between areas|OSPF area 0|
|Level 1/2|both, maintaining a separate database for each|OSPF ABR|

The hierarchy differs from OSPF in a way that matters for design. In OSPF the area boundary runs _through_ a router (an ABR has interfaces in two areas). In IS-IS the boundary runs _between_ routers — a router belongs entirely to one area, and the L1/L2 routers form the backbone by adjacency.

The L2 backbone must be contiguous, but it need not be a single area, and it can be extended anywhere. There is no equivalent of a virtual link and no requirement to renumber areas to grow the backbone — which is precisely why providers prefer it.

L1 routers have no view outside their area and reach everything else by following the nearest L1/L2 router, flagged by the ATT bit. This is convenient but produces suboptimal exits, since "nearest" is measured to the router, not to the destination.

#### IS-IS PDUs

|PDU|Purpose|
|---|---|
|IIH (Hello)|discover and maintain neighbors. Separate L1 and L2 variants on LAN media|
|LSP|the link-state advertisement — one per router per level, carrying all its information as TLVs|
|CSNP|a complete list of LSPs in the database, sent periodically by the DIS to synchronize the LAN|
|PSNP|requests a missing LSP, or acknowledges one on point-to-point links|

On LANs, IS-IS elects a DIS instead of a DR. Three differences from OSPF: there is no backup (a failed DIS is simply re-elected, which is fast), the election _is_ preemptive, and a tie on priority is broken by the highest MAC address rather than a router ID.

#### IS-IS Metric

Every interface has a default metric of 10, regardless of speed — IS-IS has no bandwidth-derived cost, so metrics are always assigned deliberately.

|Metric style|Per-link range|Total path range|
|---|---|---|
|Narrow (original)|1–63|1–1023|
|Wide (RFC 5305)|1–16777215|32-bit|

Wide metrics are mandatory in practice: the narrow range cannot express modern link speeds, and every extension (traffic engineering, Segment Routing) requires the wide TLVs. `metric-style wide` should be set everywhere.

#### IS-IS Compared to OSPF

|Aspect|OSPF|IS-IS|
|---|---|---|
|Encapsulation|IP protocol 89|directly over Layer 2|
|Area boundary|inside a router (ABR)|between routers|
|Backbone|area 0, must be contiguous|Level 2, must be contiguous|
|Adding a new area|constrained by area 0 adjacency|any L1/L2 router extends the backbone|
|Extensibility|new LSA types, new protocol version for IPv6|new TLVs, same protocol|
|IPv6|separate protocol (OSPFv3)|a TLV in the same process|
|Default metric|derived from bandwidth|10 everywhere|
|LAN election|DR + BDR, non-preemptive|DIS, no backup, preemptive|
|Typical deployment|enterprise|service provider core|

Neither is technically superior for a normal enterprise. The real decision drivers are operational: staff familiarity, vendor support, and — at provider scale — IS-IS's flatter hierarchy and cleaner extensibility.

---

## Border Gateway Protocol

BGP is the routing protocol of the Internet and the only [[#Path Vector|path vector]] protocol in use. It is fundamentally different in purpose from every [[#Interior Gateway Protocols|IGP]]: an IGP finds the technically best path within one administration, whereas BGP decides which paths a network is willing to use and willing to tell others about. It is a policy engine that happens to distribute prefixes.

Three properties follow from that purpose:

- It does not optimize. There is no metric, and the "best" path is frequently the slower one, because it is cheaper or contractually required.
- It prioritizes stability over speed. Convergence is measured in tens of seconds by design — the global table cannot afford to react to every flap.
- It scales to the entire Internet — over a million prefixes — which no IGP could survive.

### Autonomous System

An AS is a collection of prefixes under a single routing policy, identified by a globally unique number. It is the unit BGP reasons about: the atom of the [[#Well-Known Mandatory|AS_PATH]], the boundary between eBGP and iBGP, and the granularity of loop detection.

|Range|Use|
|---|---|
|1 – 64495|public, 16-bit|
|64512 – 65534|private, 16-bit|
|65536 – 4199999999|public, 32-bit (RFC 6793)|
|4200000000 – 4294967294|private, 32-bit|

32-bit ASNs are written either as a plain integer or in asdot notation (`65536` = `1.0`).

### eBGP and iBGP

The same protocol, but the behaviour differs sharply depending on whether the peer is in another AS or your own.

|Aspect|eBGP|iBGP|
|---|---|---|
|Peer AS|different|same|
|[[#Administrative Distance|AD]]|20|
|Default TTL on the session|1 — peers must be directly connected|255|
|AS_PATH|local AS prepended on advertisement|unchanged|
|NEXT_HOP|set to self on advertisement|preserved unchanged|
|LOCAL_PREF|not sent|sent, and is the main internal policy lever|
|Re-advertisement|to everyone|see [[#iBGP Split Horizon|

The eBGP TTL of 1 is a deliberate security property — it means an eBGP session cannot be established from more than one hop away, which blocks a whole class of remote attack. Multihop peering (needed for loopback peering or through a firewall) requires `ebgp-multihop` and should be scoped tightly.

The NEXT_HOP rule is the classic iBGP trap. An eBGP peer sets the next hop to itself, but when that route is passed to iBGP peers the next hop is preserved — so an internal router receives a route whose next hop is an address in _another_ AS, on a link it has no route to. The route is then never installed. The fix is `next-hop-self` on the border router's iBGP sessions, or carrying the external link in the IGP (which is worse).

#### iBGP Split Horizon

> A route learned from an iBGP peer is never advertised to another iBGP peer.

This is not a tunable — it is the only loop prevention iBGP has. [[#Well-Known Mandatory|AS_PATH]] cannot help inside an AS, because every internal router shares the same AS number and the path would never change, so the rule must be absolute.

The cost is that every iBGP speaker must peer with every other one: a full mesh of n(n−1)/2 sessions. At 10 routers that is 45 sessions; at 100 it is 4,950, which is unmanageable. Two mechanisms relax it.

#### Route Reflector

An RR is permitted to break the split-horizon rule and reflect routes between its clients, so clients need only peer with the RR. The mesh collapses from n(n−1)/2 to n.

Reflection rules:

|Route learned from|Reflected to|
|---|---|
|a client|all clients and all non-clients|
|a non-client|clients only|
|an eBGP peer|all clients and all non-clients|

Because reflecting reintroduces the possibility of an iBGP loop, two attributes are added to detect it: ORIGINATOR_ID records the router ID of the original iBGP advertiser, and CLUSTER_LIST records each cluster the route has passed through. A router discards a route carrying its own ORIGINATOR_ID; an RR discards one carrying its own cluster ID.

Deploy RRs in redundant pairs. Placing them out of the forwarding path is normal and preferred — an RR is a control-plane function and need not carry traffic.

> [!warning] Route reflectors hide paths An RR reflects only its own best path, not every path it knows. Clients therefore see fewer options than a full mesh would give them, which can cause suboptimal routing and, in some topologies, persistent path oscillation. `additional-paths` or a diverse-path RR restores visibility where it matters.

#### Confederation

Splits one AS into sub-autonomous systems that use eBGP between them and iBGP within them. The sub-AS numbers are stripped at the confederation boundary, so the outside world sees one AS.

More flexible than reflection and better at scoping policy, but considerably more complex and much rarer. Route reflection won.

### Session Establishment

BGP runs over TCP port 179. Everything TCP provides — reliable delivery, ordering, flow control, retransmission — BGP therefore does not implement, which is why its own protocol machinery is comparatively thin.

Peers are always configured explicitly. There is no discovery, by design: you do not want to accidentally peer with a stranger and inherit their routing policy.

#### BGP Messages

|Message|Purpose|
|---|---|
|OPEN|initiate the session — carries AS number, router ID, hold time, and capabilities|
|UPDATE|advertise new prefixes with their attributes, and withdraw prefixes. The only message that carries routing information|
|KEEPALIVE|prove liveness. Default 60 s, with a 180 s hold time|
|NOTIFICATION|report an error and tear the session down. BGP has no recoverable errors — any problem kills the session|
|ROUTE-REFRESH|ask a peer to resend its full table, so that a changed inbound policy can be re-applied without a reset|

ROUTE-REFRESH matters operationally: without it, changing an inbound route-map required a hard reset of the session, dropping every prefix. It is negotiated as a capability at OPEN time and is universally supported.

#### BGP Finite State Machine

|State|Meaning|
|---|---|
|Idle|not attempting. Either administratively down, or backing off after a failure|
|Connect|waiting for the TCP handshake to complete|
|Active|the TCP handshake failed; retrying|
|OpenSent|TCP is up, OPEN sent, awaiting the peer's OPEN|
|OpenConfirm|OPENs exchanged and accepted, awaiting the first KEEPALIVE|
|Established|the session is up and UPDATEs may flow|

The two diagnostic states:

- Idle — usually a missing route to the peer, or a peer that has been shut down. Idle (Admin) means exactly that.
- Active — misleadingly named. It means TCP is failing, not that anything is working. An Idle/Active flap is the signature of a one-way reachability problem, a filtered port 179, or an AS number mismatch.

### BGP Tables

|Table|Contents|
|---|---|
|Adj-RIB-In|everything received from each peer, before inbound policy|
|Loc-RIB|what survived inbound policy, with the [[#Best Path Selection|
|Adj-RIB-Out|what will be advertised to each peer, after outbound policy|

The separation is what makes BGP a policy engine. Each peer gets its own inbound and outbound view, so a router can accept a route and not use it, use a route and not advertise it, or advertise a prefix differently to two peers.

Only the best path from Loc-RIB is offered to the RIB, and only the best path is advertised to peers — a decision with real consequences, since it means BGP propagates only one path per prefix per router unless [[#BGP Multipath|multipath]] or add-path is enabled.

### Path Attributes

Every BGP route carries attributes. The classification determines what a router must do with one it does not understand.

|Class|Must be recognized?|Must be present?|Propagated if unknown?|
|---|---|---|---|
|Well-known mandatory|yes|yes, in every UPDATE|n/a|
|Well-known discretionary|yes|optional|n/a|
|Optional transitive|no|optional|yes, marked partial|
|Optional non-transitive|no|optional|no, silently dropped|

The transitive/non-transitive split is what allowed BGP to be extended for 25 years without flag days. An unknown transitive attribute is passed through untouched, so a new attribute can be deployed at the edges and simply survive its transit across older routers in the middle.

#### Well-Known Mandatory

|Attribute|Meaning|
|---|---|
|ORIGIN|how the prefix entered BGP: IGP (`i`, a `network` statement), EGP (`e`, historical), or Incomplete (`?`, [[#Redistribution|
|AS_PATH|the ordered list of ASes traversed. Loop detection, length metric, and a policy handle all at once|
|NEXT_HOP|where to send traffic for this prefix|

AS_PATH is the heart of the protocol. Loop prevention is trivially simple — a router rejects any path containing its own AS number — and unlike TTL or split horizon it is exact, requires no timers, and works at global scale.

It is also the standard tool for traffic engineering _inbound_, via AS_PATH prepending: adding copies of your own AS number to a path makes it look longer and therefore less attractive. Blunt, universally supported, and the only lever you have over what other people's routers do, since the alternatives ([[#Optional Non-Transitive|MED]], communities) require the other side to cooperate.

#### Well-Known Discretionary

|Attribute|Meaning|
|---|---|
|LOCAL_PREF|how much _this AS_ wants to use the path. Higher wins. Sent to iBGP peers only, never to eBGP|
|ATOMIC_AGGREGATE|a flag warning that this route is an aggregate that has lost AS_PATH detail|

LOCAL_PREF is the primary internal policy lever. Because it is exchanged among all iBGP speakers and evaluated near the top of [[#Best Path Selection|best-path selection]], setting it on an inbound route-map at one border router steers the exit choice of the whole AS consistently. It is how "prefer the transit provider over the peering link" is actually implemented.

#### Optional Transitive

|Attribute|Meaning|
|---|---|
|COMMUNITY|a 32-bit tag with no intrinsic meaning, used to group prefixes for policy|
|AGGREGATOR|the AS and router ID that performed an aggregation|

Communities are BGP's signalling mechanism. A provider publishes a list of communities its customers can set, and each one triggers an agreed action inside the provider's network — set a local preference, prepend n times toward a given peer, do not export to a region, blackhole the prefix. The customer thus influences the provider's policy without either party editing configuration.

Well-known values with universal meaning:

|Community|Effect|
|---|---|
|NO_EXPORT|do not advertise outside the AS (or confederation)|
|NO_ADVERTISE|do not advertise to any peer at all|
|NO_EXPORT_SUBCONFED|do not advertise outside the sub-AS|
|INTERNET|advertise normally|

Extended communities (64-bit) carry structured values and are what [[#Route Distinguisher and Route Target|route targets]] are built from; large communities (96-bit) exist because a 32-bit community cannot hold a 32-bit ASN plus a value.

#### Optional Non-Transitive

|Attribute|Meaning|
|---|---|
|MED|a hint to a neighboring AS about which of several entry points into this AS to prefer. Lower wins|
|ORIGINATOR_ID|the router ID of the iBGP router that originated the route — [[#Route Reflector|
|CLUSTER_LIST|the clusters a reflected route has passed through — RR loop prevention|

MED is the mirror image of AS_PATH prepending: it influences inbound traffic, but only from a directly adjacent AS, and only if that AS chooses to honour it. Many providers ignore it entirely. By default it is compared only between paths from the _same_ neighboring AS, since MED values from different ASes are not on a common scale; `bgp always-compare-med` removes that guard and should be used with care.

### Best Path Selection

With no metric, BGP walks an ordered list of tie-breakers, taking the first that discriminates. The Cisco order:

|#|Rule|Notes|
|---|---|---|
|0|The NEXT_HOP must be reachable|If not, the path is not considered at all. The most common cause of "the route is there but not used"|
|1|Highest WEIGHT|Cisco-proprietary, local to one router, never advertised. Default 0, or 32768 for locally originated|
|2|Highest LOCAL_PREF|Consistent across the whole AS. The main policy lever|
|3|Locally originated|`network`, `aggregate-address`, or redistributed on this router|
|4|Shortest AS_PATH|The closest thing to a metric. Prepending attacks this|
|5|Lowest ORIGIN|IGP (i) < EGP (e) < Incomplete (?)|
|6|Lowest MED|Only between paths from the same neighboring AS by default|
|7|eBGP over iBGP|An external path beats an internal one|
|8|Lowest IGP metric to the NEXT_HOP|"Hot potato" — hand the traffic off at the nearest exit|
|9|Oldest eBGP path|A stability tie-break: prefer the path that has been up longest, since changing costs a reconvergence|
|10|Lowest neighbor router ID|Deterministic|
|11|Lowest neighbor IP address|Final tie-break; only reached with two sessions to the same router|

The ordering is a statement of priorities, and reading it top-down explains BGP's philosophy: local override first, then AS-wide policy, then path length, then a series of arbitrary but deterministic tie-breaks. Attributes you control locally beat information other people gave you. Nothing about speed appears anywhere.

Steps 8 and 9 are the interesting ones. "Lowest IGP metric to the next hop" is hot-potato routing — get the traffic out of your network as cheaply as possible and let the next AS carry it. "Oldest path" exists purely to prevent churn: given two equal paths, the one already in use wins, because switching has a cost and no benefit.

> [!tip] Weight versus local preference Both are "prefer this path", and both are commonly misapplied. WEIGHT is local to one router and affects only that router's decision — useful for a quick override on a single box. LOCAL_PREF is flooded to every iBGP speaker and steers the entire AS consistently. If two border routers are configured with WEIGHT instead of LOCAL_PREF, they will happily disagree with each other.

### Advertising Prefixes

```cisco
router bgp 65001
 network 192.0.2.0 mask 255.255.255.0
```

The `network` statement in BGP means something completely different from the [[#Network Statement and Interface Selection|IGP `network` statement]]. It does not select interfaces and it starts no adjacencies. It says: if this exact prefix, with this exact mask, is present in the routing table, originate it into BGP with ORIGIN `i`.

The exact-match requirement is the trap. `network 192.0.2.0 mask 255.255.255.0` does nothing at all if the RIB holds only `192.0.2.0/25` and `192.0.2.128/25`. The standard idiom is to anchor the aggregate with a [[#Null Route|Null0]] static so it is always present regardless of the state of any component link.

Aggregation is the other origination method:

```cisco
 aggregate-address 192.0.2.0 255.255.254.0 summary-only
```

`aggregate-address` emits a summary as long as at least one component prefix is in the BGP table; `summary-only` also suppresses those components. Without `summary-only` both the aggregate and the specifics are advertised, which achieves nothing — [[#Longest Prefix Match|longest prefix match]] means the specifics will be used anyway, and the table has grown rather than shrunk.

### BGP Policy

Policy is applied per neighbor, per direction, and is the actual work of running BGP.

|Tool|Matches on|
|---|---|
|Prefix list|the prefix and its length, with `ge`/`le` range matching|
|AS-path access list|the AS_PATH, as a regular expression|
|Community list|community values|
|[[#Route Map|Route map]]|

The route map is the engine; the lists are what it matches. A typical inbound policy from a transit provider filters bogons and over-long prefixes, sets a LOCAL_PREF, and tags with a community for later reference. A typical outbound policy to a peer permits only your own prefixes and your customers' — nothing else, ever.

> [!important] Advertise only what you should The default in older implementations was to advertise everything you know to everyone you peer with. A network that accepts a full table from a transit provider and re-advertises it to another transit provider has announced itself as a transit path for the entire Internet — and will immediately receive traffic it cannot carry. This is the mechanism behind most large-scale route leaks. Explicit outbound filtering on every eBGP session is not optional.

### BGP Multipath

BGP installs one path per prefix by default, even where several are identical. `maximum-paths` enables [[#Equal-Cost Multipath|ECMP]], but only among paths that are equal in every attribute up to the IGP metric step — including the same neighboring AS.

`bgp bestpath as-path multipath-relax` relaxes that last condition, allowing multipath across different ASes as long as the AS_PATH lengths match. It is essential for multihoming to two providers, and is off by default because sharing traffic across two commercially different paths is a policy decision, not a technical one.

---

## Route Manipulation

Everything above describes what protocols do on their own. This section is about overriding them.

### Summarization

Advertising one shorter prefix in place of a set of longer ones that it covers. `10.1.0.0/16` replaces `10.1.0.0/24` through `10.1.255.0/24` — 256 entries become 1.

The benefit is not only table size. It is boundary:

|Effect|Why it matters|
|---|---|
|Smaller tables|less memory, faster lookup, faster convergence|
|Hides instability|a flap inside the block does not change the summary, so nothing outside recomputes at all|
|Bounds query scope|an [[#EIGRP Summarization|
|Bounds SPF|an [[#OSPF Summarization|

Hiding instability is the real prize. An unsummarized network propagates every flap to every router; a summarized one contains it.

The costs are real and must be accepted deliberately:

- Suboptimal routing. The summary is advertised at one cost, so a distant router cannot tell that one component is nearer than another.
- Black holes. If a component subnet disappears but the summary is still advertised, traffic is drawn in and dropped. The [[#Null Route|Null0]] discard route ensures it is dropped locally rather than looped.
- It requires contiguous addressing. Summarization is impossible if the prefixes in a block are scattered across the topology, which is why addressing must be designed alongside the hierarchy rather than after it.

### Filtering

Controlling which routes are accepted or advertised.

#### Prefix List

```cisco
ip prefix-list ALLOW seq 5 permit 10.1.0.0/16 le 24
```

Matches the prefix _and_ its length. `le 24` permits `10.1.0.0/16` and anything more specific down to `/24`; `ge`/`le` together specify a range. This is why prefix lists replaced ACLs for route filtering — an ACL matches an address and cannot distinguish `10.1.0.0/16` from `10.1.0.0/24`, which is exactly the distinction that matters. There is an implicit deny at the end.

#### Distribute List

Applies an ACL or prefix list to a protocol's updates in a given direction:

```cisco
router ospf 1
 distribute-list prefix ALLOW in
```

The direction has a subtlety that catches people out. Applied `in` to a [[#Link State|link-state]] protocol, a distribute list filters what goes from the protocol into the RIB — it does not and cannot filter the [[#Link-State Database|LSDB]], because the database must remain identical across the area. The router will still hold the LSA, still flood it, and still compute over it; it simply will not install the resulting route. Filtering `out` in OSPF is only possible at an [[#Router Roles|ASBR]], on redistributed routes.

Distance vector protocols have no such constraint, which is one of the few things they do more simply than link-state ones.

#### Route Map

The general-purpose policy tool: an ordered list of clauses, each with match conditions and set actions, evaluated top-down until a match. Used for [[#Redistribution|redistribution]] control, [[#BGP Policy|BGP policy]], and [[#Policy-Based Routing|PBR]].

```cisco
route-map REDIST-TO-OSPF permit 10
 match ip address prefix-list ALLOW
 set metric 100
 set metric-type type-1
 set tag 65001
!
route-map REDIST-TO-OSPF deny 20
```

Semantics worth being precise about, because they are the source of most route-map bugs:

- Clauses are evaluated in sequence number order; the first match wins and evaluation stops.
- `permit` with matches → the route passes, and the `set` actions apply.
- `deny` → the route is dropped, and `set` actions are ignored.
- A clause with no `match` matches everything — which makes an empty `permit` clause a catch-all.
- There is an implicit `deny any` at the end. A route map that permits nothing explicitly denies everything.

### Redistribution

Taking routes from one routing source and injecting them into another. Necessary during migrations, at the boundary between merged networks, and wherever an IGP meets BGP or a set of statics.

It is also the single most dangerous thing in routing, because the two protocols involved have no common language. Metrics do not translate. Loop prevention does not carry across. Each protocol's mechanisms protect it only from itself.

```cisco
router ospf 1
 redistribute eigrp 100 subnets route-map REDIST-TO-OSPF
```

Redistribution takes routes from the _RIB_, not from the source protocol's own database — so only routes actually installed and active are candidates, and a route losing on [[#Administrative Distance|AD]] to another source is silently invisible to redistribution.

#### Seed Metric

The metric assigned to a route as it enters the target protocol. There is nothing to derive it from — an EIGRP composite of 30720 has no meaning as an OSPF cost — so each protocol has a default.

|Redistributed into|Default seed metric|
|---|---|
|RIP|infinity — the route is discarded|
|EIGRP|infinity — the route is discarded|
|OSPF|20, external type 2 (1 when the source is BGP)|
|IS-IS|0|
|BGP|the IGP metric of the source route|

RIP and EIGRP treat a missing seed metric as unreachable and silently drop the route. This is the most common redistribution failure by a wide margin: the configuration is present, the command is accepted, no error appears, and nothing is redistributed.

```cisco
router eigrp 100
 default-metric 100000 100 255 1 1500
```

> [!note] The EIGRP exception Connected routes redistributed into EIGRP on the same router are the exception — they take their metric from the interface's own bandwidth and delay, so they work without `default-metric`. This inconsistency makes the failure harder to spot, since redistributing connected appears to work while redistributing OSPF silently does not.

#### External Route Types

OSPF marks redistributed routes as external and offers two costing models:

|Type|Cost seen by a remote router|Use|
|---|---|---|
|E2 (default)|the seed metric only — constant everywhere in the domain|when the exit choice does not matter, or all ASBRs are equivalent|
|E1|the seed metric plus the internal cost to reach the ASBR|when the nearest ASBR should be preferred|

E2 is the default and is frequently the wrong choice with multiple ASBRs: every router sees the same cost regardless of distance, so the tie falls through to the lowest [[#Router ID|router ID]] and traffic can cross the network to reach a distant ASBR when a local one exists. E1 makes distance count.

NSSA externals use N1 and N2 with the same semantics.

EIGRP marks redistributed routes as external and trusts them less — AD 170 rather than 90 — which is a form of the same protection.

#### Redistribution Loops

Consider two routers redistributing between OSPF and EIGRP in both directions. A prefix native to OSPF is redistributed into EIGRP by router A, carried across EIGRP to router B, and redistributed by B back into OSPF — where it now appears as an OSPF external. Neither protocol can detect this: OSPF's [[#SPF Algorithm|SPF]] guarantees are about the LSDB and say nothing about a route that arrived from outside, and EIGRP's [[#Feasibility Condition|feasibility condition]] compares distances within EIGRP only.

The route is now circulating. Worse, [[#Administrative Distance|AD]] can make the reinjected copy win: a route natively OSPF (110) that returns as internal EIGRP (90) will be preferred over the original, and the router will forward toward the copy of its own advertisement.

The failure is quiet — routes resolve, pings work, and the loop only appears under a specific failure. Three defences, used together:

- Redistribute in one direction only wherever possible. Mutual redistribution should be avoided rather than mitigated.
- Filter explicitly on every redistribution point, with a [[#Route Map|route map]] permitting only what should cross.
- [[#Route Tag|Tag]] on the way out and deny the tag on the way back in.

#### Route Tag

A 32-bit value attached to a route, carried by every modern protocol, with no meaning to the protocol itself. It is a marker for administrative use.

```cisco
route-map OSPF-TO-EIGRP permit 10
 set tag 110
!
route-map EIGRP-TO-OSPF deny 10
 match tag 110
route-map EIGRP-TO-OSPF permit 20
```

Routes leaving OSPF are stamped with tag 110; routes returning are dropped if they carry it. This is the standard mutual-redistribution safeguard, and unlike prefix filtering it does not need to be updated when subnets are added — it is topological rather than enumerated, so it keeps working as the network changes.

### Administrative Distance Manipulation

```cisco
router ospf 1
 distance 171 10.1.4.2 0.0.0.0
```

Changes how much this router trusts a route source. Legitimate uses are narrow: making a redistributed route lose to the native protocol during a migration, or backing up one protocol with another.

The danger is that [[#Administrative Distance|AD]] is local and unadvertised. Changing it on one router and not its neighbor produces two routers with different opinions and no protocol able to notice — which is a routing loop assembled by hand. If AD is changed at all, it must be changed consistently and documented, and a [[#Route Tag|tag]] is almost always the better tool.

### Policy-Based Routing

Normal forwarding considers only the destination. PBR overrides it, forwarding on source address, protocol, port, packet size, or anything else a [[#Route Map|route map]] can match.

```cisco
route-map PBR-GUEST permit 10
 match ip address GUEST-SOURCES
 set ip next-hop 203.0.113.9
!
route-map PBR-GUEST permit 20
!
interface GigabitEthernet0/1
 ip policy route-map PBR-GUEST
```

Applied inbound on an interface, and evaluated _before_ the routing table lookup. `ip local policy route-map` applies it to traffic the router itself generates.

|Set action|Behavior|
|---|---|
|`set ip next-hop`|overrides the routing table, provided the next hop is reachable|
|`set ip default next-hop`|used only if the routing table has no match — a policy default|
|`set interface`|forces an exit interface|
|`set ip precedence` / `set ip dscp`|marks rather than redirects|

The trailing empty `permit` clause is mandatory in practice: without it, the implicit deny at the end of the route map means unmatched traffic is not policy-routed — which is the desired outcome, but only because the implicit deny in PBR means "route normally" rather than "drop". Being explicit about it avoids relying on that asymmetry.

PBR is powerful and should be used sparingly. It creates forwarding behaviour that is invisible in `show ip route`, it does not react to failure unless combined with [[#Static Route Tracking|tracking]], and it is punted to the CPU on some platforms. A packet taking a path that the routing table says is impossible is almost always PBR.

---

## Loop Prevention and Stability

### How Routing Loops Form

Every router forwards independently on local information. A loop is what happens when two routers' local information disagrees about direction: A believes the prefix is toward B, B believes it is toward A, and the packet shuttles between them until its [[#TTL Decrement|TTL]] expires.

The disagreement is almost always transient — a moment during [[#Convergence|convergence]] when one router has learned about a failure and the other has not. Loop prevention is therefore mostly about making that window short, or about making decisions that remain safe throughout it.

Loops are not merely a wasted packet. Each looping packet consumes the link's bandwidth once per traversal, so a modest flow saturates the link and starves the routing protocol hellos that would otherwise fix the problem. Loops are self-sustaining.

### Distance Vector Protections

[[#Distance Vector|Distance vector]] protocols are blind — a router cannot tell whether a neighbor's advertisement is based on information the router itself supplied. Each mechanism below patches one aspect of that blindness.

#### Split Horizon

> Never advertise a route back out the interface it was learned on.

If B learned about a prefix from A, then B telling A about it is at best noise and at worst the seed of a loop. The rule is simple, cheap, and stops the two-router case completely.

It has a well-known failure: on a hub-and-spoke NBMA topology, all spokes are reached through one physical interface, so split horizon prevents the hub from relaying one spoke's routes to another. The fix is `no ip split-horizon` on the hub, or subinterfaces so each spoke is logically separate. [[#iBGP Split Horizon|iBGP]] uses the same principle for the same reason and solves the same problem with [[#Route Reflector|route reflectors]].

#### Route Poisoning

Rather than silently removing a failed route, advertise it with an infinite metric — 16 in [[#RIP|RIP]]. Explicit bad news travels immediately; a silent removal must be inferred from a timer expiring.

Poison reverse is the deliberate exception to split horizon: on learning a route from a neighbor, send it back to that neighbor poisoned. This trades bandwidth for certainty — instead of relying on the neighbor to infer that you are not a path, you tell it outright.

#### Hold-Down Timer

After hearing that a route is unreachable, ignore any _worse_ information about it for the hold-down period (180 s in RIP). The purpose is to let the bad news propagate fully before believing anyone's claim to have an alternative — the alternative is very often just a stale echo of the original route coming back around.

It works, and it is why RIP convergence is measured in minutes. The protocol trades speed for safety because it has no better option.

#### Triggered Update

Send an update immediately on a change instead of waiting for the next periodic timer. Obvious, and it is the single largest improvement available to a periodic protocol — it shrinks the propagation window from 30 seconds to milliseconds. Every modern protocol is triggered-only.

#### Maximum Metric

Cap the metric at a value that means unreachable — 16 hops in RIP, `4294967295` in EIGRP. This bounds [[#Counting to Infinity|counting to infinity]] rather than preventing it, and the cost is a hard limit on network diameter.

#### Counting to Infinity

The pathology all of the above exist to contain. A prefix fails; the router owning it removes it. Before the news propagates, some other router advertises the prefix back at its own metric — a route that is stale, and ultimately derived from the originator itself, but nothing in the advertisement says so. It is accepted, incremented by 1, and re-advertised. The metric climbs by one on every exchange while the packets loop, until it reaches the [[#Maximum Metric|maximum]] and everyone finally gives up.

[[#Split Horizon|Split horizon]] kills this outright between two routers — B never tells A about a route it learned from A. The pathology therefore needs a loop of three or more, where the stale information arrives from a router that was never told:

```
   A ── B ── C ── A          X is owned by A

   X fails at A.  A removes it.
   But C learned X from B, and A never told C anything,
   so split horizon does not stop C advertising X back to A.

   C → A: "X, metric 3"      ← stale, and A cannot tell
   A: X via C, metric 4   →  B: X via A, metric 5
   B → C: "X, metric 5"   →  C: X via B, metric 6
   ...                       until metric = 16 = unreachable
```

The loop persists for as long as it takes the metric to climb to infinity — which is why "infinity" is set as low as 16 in RIP, and why [[#Hold-Down Timer|hold-down]] is needed on top to stop the stale route being believed at all.

This is the direct consequence of routing by rumour, and it is why [[#Link State|link-state]] protocols — which never re-advertise anyone else's information — were designed.

### Link-State Protections

[[#Link State|Link-state]] protocols do not need any of the above inside an area, because the structure removes the cause. A router describes only its own links and never repeats a neighbor's claim, so there is no rumour to circulate; every router computes over an identical [[#Link-State Database|database]], so all the resulting trees are consistent; and LSAs carry a sequence number and age, so a stale advertisement is recognised as stale rather than believed.

The guarantee is bounded, and the boundary matters:

- Inside an area — structurally loop-free, provided databases are synchronized.
- Between areas — [[#Distance Vector|distance vector]] behaviour, since an [[#Router Roles|ABR]] advertises a cost rather than the topology. Loop-free only because the [[#Backbone Area|area 0]] rule forces a star.
- External routes — no protection whatsoever. A [[#LSA Types|Type 5]] LSA is an assertion by an ASBR, and OSPF has no way to validate it. This is why [[#Redistribution Loops|redistribution loops]] are possible in a protocol that is otherwise loop-free.

### Path Vector Protections

[[#Path Vector|Path vector]] carries the full [[#Well-Known Mandatory|AS_PATH]], so a router rejects any route already containing its own AS. This is exact rather than heuristic: no timers, no counting, no window of uncertainty. It works at global scale and it is the only reason inter-domain routing is tractable.

Its limitation is granularity. It detects loops at AS level only, which is why iBGP needs [[#iBGP Split Horizon|its own absolute rule]] and route reflection needs [[#Route Reflector|ORIGINATOR_ID and CLUSTER_LIST]] on top.

### TTL as a Backstop

Every mechanism above is protocol-level and can be defeated — by [[#Redistribution Loops|redistribution]], by [[#Administrative Distance Manipulation|AD manipulation]], by a mis-scoped [[#Policy-Based Routing|PBR]] policy, or simply by a transient during convergence. [[#TTL Decrement|TTL]] is the layer below all of it: it does not prevent loops, but it guarantees that any loop is finite and self-limiting.

It is the reason a routing loop degrades a network rather than destroying it.

### Route Flapping and Dampening

A flapping route is one repeatedly withdrawn and re-advertised — a marginal link, a failing optic, an overloaded neighbor. Each transition costs a recomputation, and the cost is paid by every router that hears about it, so one bad optic can hold an entire domain in continuous SPF.

Defences, in order of preference:

- [[#Summarization|Summarization]]. The flap does not change the summary, so nothing outside the boundary hears about it at all. This is the correct answer wherever it applies.
- Throttling. SPF and LSA throttle timers back off exponentially under repeated events, so a flapping link degrades responsiveness rather than the CPU.
- Dampening in BGP. Each flap adds a penalty (1000); the penalty decays exponentially with a half-life (15 minutes). Above the suppress limit (2000) the route is suppressed and not advertised; it returns below the reuse limit (750), up to a maximum suppression time (60 minutes).

Dampening is now used sparingly. The default parameters are aggressive enough to suppress a prefix for tens of minutes over a couple of transient flaps, and because penalties accumulate along a path, a well-behaved prefix can be dampened for someone else's instability several ASes away. RFC 7196 recommends much higher thresholds if it is used at all.

### Fast Convergence

#### Failure Detection

The dominant term in [[#Convergence|convergence]]. The options, from best to worst:

|Mechanism|Detection time|Limitation|
|---|---|---|
|Physical carrier loss|milliseconds|only detects a local link failure — useless if the break is beyond a media converter, switch, or provider handoff|
|[[#Bidirectional Forwarding Detection|BFD]]|tens of milliseconds|
|Aggressive protocol hellos|hundreds of ms to seconds|CPU cost scales with neighbor count; risks false failures under load|
|Default protocol timers|10–180 s|far too slow for anything real-time|

Carrier loss is instant but frequently lies. Any Ethernet handoff, media converter, or provider circuit means the local interface stays up while the path beyond it is broken — the router is watching the wrong thing. This is exactly the gap BFD fills.

#### Bidirectional Forwarding Detection

A minimal protocol whose only job is to detect that a path between two systems has failed, as fast as possible. It exchanges tiny hellos at sub-second intervals, and because it is deliberately simple it can run in hardware or on a line card rather than the main CPU.

```cisco
interface GigabitEthernet0/1
 bfd interval 50 min_rx 50 multiplier 3
!
router ospf 1
 bfd all-interfaces
```

The design insight is decoupling. Routing protocols register as BFD clients, so one session serves OSPF, BGP, EIGRP and static route tracking at once. Rather than every protocol implementing its own aggressive timers — multiplying CPU cost by the number of protocols and producing inconsistent results — detection is solved once, properly, and the protocols simply subscribe.

Echo mode loops the packet back through the neighbor's data plane rather than its control plane, which tests forwarding rather than just liveness and removes the neighbor's CPU from the equation.

#### Fast Reroute

Even with instant detection, recomputation and FIB reprogramming take time. Fast reroute removes that too, by computing the backup _before_ the failure and pre-installing it, so the failover is a data-plane pointer swap measured in tens of milliseconds.

|Mechanism|Coverage|
|---|---|
|LFA (Loop-Free Alternate)|a neighbor that already has a loop-free path to the destination. Simple, but coverage is topology-dependent and often incomplete|
|Remote LFA|extends coverage by tunnelling to a distant node that qualifies|
|TI-LFA|uses [[#Segment Routing|
|[[#Successor and Feasible Successor|EIGRP feasible successor]]|

EIGRP's feasible successor is the clearest illustration of the principle: the reason EIGRP converges in milliseconds is not that DUAL is fast, but that when a feasible successor exists there is nothing to compute at all.

---

## Routing in the Campus

### Inter-VLAN Routing

A VLAN is a broadcast domain and normally maps one-to-one to an IP subnet. Hosts in different VLANs cannot reach each other at Layer 2 by definition — that is the entire point of a VLAN — so something must route between them. Three ways to provide it.

#### Router on a Stick

One physical link to an external router, carrying every VLAN as an 802.1Q trunk, with a subinterface per VLAN acting as that subnet's [[#Default Gateway|default gateway]].

```cisco
interface GigabitEthernet0/0.802
 encapsulation dot1Q 802
 ip address 10.140.2.1 255.255.255.0
!
interface GigabitEthernet0/0.805
 encapsulation dot1Q 805
 ip address 10.140.5.1 255.255.255.0
```

The native VLAN needs `encapsulation dot1Q <vlan> native`, since its frames arrive untagged.

Every inter-VLAN packet crosses the trunk twice — in on one subinterface, out on another — so the single link is a hard bandwidth ceiling and a single point of failure. Legacy: acceptable only for very small sites or where no Layer 3 switch exists.

#### Switched Virtual Interface

A virtual Layer 3 interface on the switch itself, one per VLAN, routed in ASIC hardware at line rate.

```cisco
ip routing
!
interface Vlan802
 description LAN-CLIENT
 ip address 10.140.2.1 255.255.255.0
 no shutdown
```

This is the normal answer. Traffic never leaves the switch, there is no trunk bottleneck, and the routing is done at switching speed.

An SVI comes up only when the VLAN exists in the VLAN database and at least one port in that VLAN is up — an access port, or a trunk that allows it. An SVI stuck down with a perfectly correct configuration is nearly always a VLAN that exists nowhere on the switch, or one pruned off every trunk.

#### Routed Port

A physical switch port taken out of Layer 2 entirely with `no switchport` and given an address directly. It belongs to no VLAN, participates in no spanning tree, and behaves exactly like a router interface.

```cisco
interface GigabitEthernet1/0/24
 no switchport
 ip address 10.255.1.1 255.255.255.252
```

Used for uplinks between Layer 3 switches, for point-to-point links to routers, and for anything that should be a routed hop rather than a bridged one.

### First Hop Redundancy

A host has one [[#Default Gateway|default gateway]] and no way to detect that it has failed. Redundant routers do not help — the host will not use the second one, because it does not know it exists. FHRPs solve this by presenting a virtual IP and virtual MAC that are shared between routers, so the host talks to an address rather than a device.

The host is never involved and never reconfigured. Failover consists of a different physical router taking ownership of the same virtual MAC.

|Aspect|HSRP|VRRP|GLBP|
|---|---|---|---|
|Standard|Cisco|RFC 5798|Cisco|
|Roles|Active / Standby|Master / Backup|AVG / AVF|
|Virtual MAC|`0000.0C07.ACxx` (v1), `0000.0C9F.Fxxx` (v2)|`0000.5E00.01xx`|`0007.B400.xxxx`|
|Transport|UDP 1985, 224.0.0.2 (v1) / 224.0.0.102 (v2)|IP protocol 112, 224.0.0.18|UDP 3222, 224.0.0.102|
|Default priority|100|100|100|
|Preempt by default|no|yes|no|
|Load balancing|per VLAN, by alternating the active router|per VLAN|native, across up to 4 forwarders|
|Virtual IP can be a real interface IP|no|yes (that router becomes owner, priority 255)|no|

#### HSRP

```cisco
interface Vlan802
 ip address 10.140.2.2 255.255.255.0
 standby version 2
 standby 802 ip 10.140.2.1
 standby 802 priority 110
 standby 802 preempt
 standby 802 track GigabitEthernet1/0/24 20
```

Cisco's, and the most common in Cisco environments. The virtual IP is separate from both routers' real addresses.

Two configuration points that are almost always wrong when they are omitted:

- Preempt is off by default. Without it, a recovered primary stays standby and the priority you configured never takes effect — the active router is simply whichever booted first.
- Tracking. Without it, HSRP monitors only its own local interface. A router whose _uplink_ has failed remains happily active and black-holes everything the hosts send it. Tracking decrements the priority when the tracked object fails, which triggers a preemptive failover to the router that still has a path.

#### VRRP

The open standard, and functionally near-identical. Two differences matter in practice: preemption is on by default (which is the more sensible default), and the virtual IP may be one of the physical routers' real addresses, in which case that router is the owner and runs at priority 255 permanently.

Use it in multi-vendor environments.

#### GLBP

Cisco's, and the only one that load-balances natively. One router is elected Active Virtual Gateway and answers all ARP requests for the virtual IP, handing out a _different_ virtual MAC to each host, round-robin or weighted. Each Active Virtual Forwarder then handles the traffic for its own MAC — so up to four routers forward simultaneously for one VLAN, without any per-VLAN priority engineering.

Elegant, but it depends on the ARP-time distribution being even, and its niche has largely been taken by [[#Routed Access Design|routed access]] and by MLAG designs where both uplinks are active anyway.

### Routed Access Design

Pushing the Layer 3 boundary down to the access switch, so that access-to-distribution links are [[#Routed Port|routed ports]] and no VLAN spans more than one switch.

|Property|Layer 2 access|Routed access|
|---|---|---|
|Access–distribution links|trunks|routed|
|Loop prevention|spanning tree|routing protocol|
|Convergence|seconds (STP)|sub-second (IGP + [[#Bidirectional Forwarding Detection|
|Both uplinks active|only with MLAG or [[#GLBP|GLBP]]|
|Gateway redundancy|needs an [[#First Hop Redundancy|FHRP]]|
|VLAN spanning switches|possible|impossible by design|
|Failure domain|the whole L2 domain|one switch|

The trade is that a VLAN cannot span access switches, which breaks anything requiring Layer 2 adjacency across the campus. That constraint was a genuine obstacle for years, and is precisely what [[#VXLAN and EVPN|VXLAN/EVPN]] overlays now remove — providing Layer 2 adjacency over a routed underlay, and giving both properties at once.

---

## Routing Virtualization and Overlays

### VRF

Virtual Routing and Forwarding runs multiple independent routing tables on one device. Each VRF has its own [[#Routing Information Base|RIB]], its own [[#Forwarding Information Base|FIB]], its own protocol instances, and its own interfaces. They are isolated by default: two VRFs can use overlapping address space with no conflict, because a lookup happens only within the VRF the packet arrived on.

```cisco
vrf definition GUEST
 rd 65001:805
 address-family ipv4
 exit-address-family
!
interface Vlan805
 vrf forwarding GUEST
 ip address 10.140.5.1 255.255.255.0
```

Assigning an interface to a VRF wipes its IP configuration — the address must be reapplied afterwards. This surprises people once.

The default VRF (also called the global routing table) is where everything lives until placed elsewhere. `Mgmt-vrf` is a common special case: putting management interfaces in their own VRF means management reachability does not depend on, and cannot be broken by, the production routing table.

#### VRF-Lite

VRFs without MPLS: pure local separation, extended between devices by giving each VRF its own subinterface or VLAN on the link and its own protocol instance.

Simple and effective for a handful of VRFs, and it is how guest, IoT, or partner traffic is typically isolated in an enterprise. It does not scale — every VRF needs its own subinterface, its own adjacency, and its own protocol process on every hop — which is the problem [[#MPLS L3VPN|MPLS L3VPN]] and [[#VXLAN and EVPN|EVPN]] exist to solve.

#### Route Distinguisher and Route Target

Two 8-byte values that are constantly confused, and they do unrelated jobs.

|Value|Job|When it matters|
|---|---|---|
|Route Distinguisher|makes a prefix globally unique by prepending to it, turning `10.1.1.0/24` into `65001:100:10.1.1.0/24`|carrying overlapping prefixes from different VRFs across one MP-BGP session|
|Route Target|an extended community controlling which VRFs a route is exported to and imported into|deciding VPN membership and topology|

The RD is about uniqueness. Without it, two customers both using `10.1.1.0/24` would collide in a shared BGP table, and BGP would treat them as one prefix and pick a best path between them.

The RT is about policy, and it is the RT alone that builds the VPN topology. Every site exporting and importing the same RT gives a full mesh; a hub exporting one RT and importing another gives hub-and-spoke; importing an extra RT gives a shared-services VRF reachable from everywhere.

#### Route Leaking

Deliberately moving routes between VRFs, because complete isolation is rarely what is actually wanted — a guest VRF still needs DNS, and every VRF needs monitoring.

Done cleanly with import/export [[#Route Distinguisher and Route Target|route targets]] where MP-BGP is present, or with static routes across VRFs (`ip route vrf ... global`) in VRF-Lite. Leaking bidirectionally between two VRFs that both use overlapping space cannot work — the reason to leak is precisely the reason the address plan must not overlap.

### MPLS

#### Label Switching

MPLS pushes a short fixed-length label onto the packet at the network edge, and every router in the core forwards on that label alone — a single exact-match lookup, no [[#Longest Prefix Match|longest prefix match]], no IP header inspected.

```
    Ingress LER          LSR          LSR       Egress LER
   push label 100 → swap 100→200 → swap 200→pop → plain IP
   [ 100 | IP pkt ]  [ 200 | IP ]   [ IP ]        [ IP ]
```

The original motivation — that label lookup was faster than IP lookup — evaporated once hardware could do longest-prefix match at line rate. What kept MPLS is everything else: core routers do not need to know the destination prefix at all (only the label), which means they need not carry a full BGP table; and the label stack allows arbitrary services to be layered on top.

Labels are distributed by LDP (TCP/UDP 646) for plain IP forwarding, by MP-BGP for [[#MPLS L3VPN|VPNs]], and by RSVP-TE or [[#Segment Routing|SR]] for traffic engineering. Penultimate hop popping has the second-to-last router remove the label so the egress does one lookup instead of two.

#### MPLS L3VPN

The dominant enterprise WAN service, and the reason MPLS is ubiquitous.

Customer routes are placed in a per-customer [[#VRF|VRF]] at the provider edge, made unique with a [[#Route Distinguisher and Route Target|route distinguisher]], and carried across the provider core in MP-BGP as VPNv4 routes. A two-label stack is used: the outer label routes the packet to the correct egress PE, and the inner label — known only to that PE — identifies the VRF to deliver it into.

The consequence is that the provider core carries no customer routes at all. P routers see only labels and the provider's own loopbacks. Adding a customer touches the two PEs and nothing else, which is what makes the service scale to thousands of customers.

### Tunnels

#### GRE

A generic encapsulation that wraps any protocol in an IP packet, creating a virtual point-to-point link between two endpoints across any intervening network.

```cisco
interface Tunnel0
 ip address 10.255.255.1 255.255.255.252
 tunnel source GigabitEthernet0/0
 tunnel destination 203.0.113.9
```

GRE's value is that the tunnel looks like an ordinary interface: routing protocols run over it, multicast crosses it, and non-IP protocols traverse an IP network. That is why GRE is almost always paired with [[#IPsec|IPsec]] — IPsec alone carries neither multicast nor routing protocols, so `GRE over IPsec` is the standard combination.

Two hazards, and they cause most tunnel problems:

- Recursive routing. If the route to the tunnel destination is learned _through the tunnel_, the tunnel tries to carry itself and flaps permanently. Keep the tunnel destination in the underlay, never in the overlay, and never redistribute the underlay into the overlay.
- MTU. The GRE header (24 bytes) is added to an already full-size packet, so the result exceeds the path MTU. `ip mtu 1400` and `ip tcp adjust-mss 1360` on the tunnel are the standard workarounds, needed because [[#MTU and Fragmentation|PMTUD]] frequently fails through the filtering in between.

#### IPsec

Provides confidentiality, integrity, and authentication for IP traffic. Tunnel mode encapsulates the entire original packet in a new one; transport mode protects only the payload.

Relevant to routing because of what it does _not_ do: plain IPsec carries only unicast IP, so no routing protocol and no multicast can cross it. This is why it is combined with GRE, or replaced by VTI (`tunnel mode ipsec ipv4`), which presents a routable interface and is the cleaner modern approach. DMVPN builds the same idea into a dynamic hub-and-spoke overlay with on-demand spoke-to-spoke tunnels via NHRP.

### VXLAN and EVPN

VXLAN encapsulates an Ethernet frame in UDP (port 4789) and carries it across a routed network. The endpoints — VTEPs — are the boundary between the bridged overlay and the routed underlay. The 24-bit VNI replaces the 12-bit VLAN ID, raising the segment limit from 4,094 to roughly 16 million.

Alone, VXLAN has no control plane and floods to learn, exactly like a switch. EVPN supplies one: MP-BGP with the L2VPN EVPN address family distributes MAC and IP reachability explicitly, so the fabric learns by advertisement rather than by flooding.

|EVPN route type|Carries|
|---|---|
|Type 2|MAC / IP advertisement — a host's location in the fabric|
|Type 3|multicast — how to reach a VTEP for BUM traffic|
|Type 5|IP prefix — routed reachability, no MAC involved|

The result resolves the tension in [[#Routed Access Design|routed access]]: a fully routed underlay with ECMP and sub-second convergence, and Layer 2 adjacency anywhere it is needed on top of it. It is the basis of modern data centre fabrics and of Cisco SD-Access.

### Segment Routing

Source routing done properly. The ingress router encodes the path as an ordered list of segments in the packet header, and the routers along the way simply execute it. No per-flow state is held anywhere in the core, and no label distribution protocol is needed — segment identifiers are advertised as extensions to [[#IS-IS|IS-IS]] or [[#OSPF|OSPF]].

|Segment type|Meaning|
|---|---|
|Prefix-SID|go to this node, by the shortest path|
|Adjacency-SID|traverse this specific link|
|Anycast-SID|go to the nearest member of a set|

Removing LDP and RSVP-TE removes the two hardest protocols to operate in an MPLS core, and replaces per-tunnel state in every router with a stack in the packet. It also enables [[#Fast Reroute|TI-LFA]], which is the only fast-reroute mechanism with complete topology coverage. SR-MPLS reuses the MPLS data plane; SRv6 encodes segments as IPv6 addresses and needs no MPLS at all.

### LISP

Separates identity from location. The EID identifies the endpoint and never changes; the RLOC identifies where in the network it currently is. A mapping system (map server / map resolver) resolves one to the other on demand, so routers cache mappings rather than holding a full table.

Its value is mobility: an endpoint keeps its address when it moves, and only its mapping updates. It is the control plane underneath Cisco SD-Access.

### SD-WAN

Applies the overlay idea to the WAN: a centralized controller distributes policy and builds an encrypted [[#Tunnels|tunnel]] mesh across whatever transports exist — MPLS, broadband, LTE — and forwarding decisions are made per application against measured path characteristics rather than per destination prefix.

From a routing perspective the notable inversion is that the transport becomes interchangeable. The controller holds the policy; the routers hold tunnels; the underlying circuits are a commodity. Path selection stops being "which prefix" and becomes "which of my available paths currently meets this application's SLA" — the point where routing, [[#Policy-Based Routing|policy routing]], and QoS merge into one system.

---

## IPv6 Routing

### Differences from IPv4

The forwarding model is identical: [[#Longest Prefix Match|longest prefix match]], [[#Administrative Distance|AD]], [[#Metric|metric]], hop-by-hop. What changed is the environment around it.

|Aspect|IPv4|IPv6|
|---|---|---|
|Enabling routing|on by default on routers|`ipv6 unicast-routing` required|
|L2 address resolution|ARP|Neighbor Discovery (ICMPv6)|
|Broadcast|yes|none — multicast only|
|Router fragmentation|permitted when DF is clear|never; ICMPv6 Packet Too Big instead|
|Header checksum|present, recomputed each hop|removed|
|Addresses per interface|normally one|always several — link-local plus global|
|Default gateway|configured or DHCP|learned from Router Advertisements|
|Protocol next hop|global address|[[#Link-Local Next Hop|

ICMPv6 is not optional. Neighbor Discovery, Router Advertisement, and Path MTU Discovery are all ICMPv6, so filtering it the way ICMP is often filtered in IPv4 breaks the network outright rather than degrading it.

### Link-Local Next Hop

Every IPv6-enabled interface automatically has an `FE80::/10` link-local address, and this is what routing protocols use — for adjacencies and as the next hop they advertise.

The consequence is that a link needs no global addressing at all for routing to work over it, which is why unnumbered infrastructure links are practical in IPv6 and awkward in IPv4.

It also forces a syntax change. A link-local address is only unique within a link, so a static route through one must name the interface too:

```cisco
ipv6 route 2001:db8:1::/48 GigabitEthernet0/1 FE80::1
```

`ipv6 route 2001:db8:1::/48 FE80::1` is rejected — `FE80::1` exists on every link, so the router has no way to know which one is meant.

### IPv6 Routing Protocols

|Protocol|Transport|Multicast|Notes|
|---|---|---|---|
|RIPng|UDP 521|FF02::9|obsolete, like its predecessor|
|[[#OSPFv3|OSPFv3]]|IP protocol 89|FF02::5, FF02::6|
|EIGRP for IPv6|IP protocol 88|FF02::A|same [[#DUAL|
|[[#IS-IS|IS-IS]]|Layer 2|—|
|MP-BGP|TCP 179|—|the IPv6 unicast address family on the existing session|

IS-IS is the standout: because it never ran over IP, adding IPv6 meant defining a TLV, and one process with one set of adjacencies carries both families. OSPF needed an entirely new protocol version. This is the clearest practical dividend of the design choice, and a large part of why providers chose IS-IS.

### Dual Stack

Running both protocols in parallel on the same infrastructure, each with its own routing table and its own protocol instances, with hosts preferring IPv6 where both are available.

The operational point that matters: the two stacks are independent, so they fail independently. A host with a working IPv6 default route to a broken path will use it and time out, rather than falling back to a perfectly good IPv4 path — Happy Eyeballs at the application layer exists to paper over exactly this. IPv6 must be monitored as a first-class path, not assumed to be a mirror of IPv4.

---

## Multicast Routing

Unicast routing moves a packet toward one destination. Multicast moves one packet toward a _group_, replicating it only where the paths to members diverge, so a stream traverses each link once regardless of how many receivers are behind it.

It reverses the basic question. Unicast asks "where is this destination?"; multicast asks "where are the receivers, and where must I replicate?" — which is why it needs its own protocols, its own tree-building, and its own loop prevention.

### Reverse Path Forwarding

The RPF check is multicast's loop prevention, and it is the core mechanism.

> A multicast packet is accepted only if it arrived on the interface the router would use to send _unicast_ traffic back toward its source. Otherwise it is dropped.

The reasoning: if the packet came from the direction of the source, it is on the shortest path and is the first copy to arrive. If it came from anywhere else, it is a duplicate that has looped or been flooded, and dropping it costs nothing.

RPF is why multicast depends entirely on the unicast routing table. It also means asymmetric unicast routing breaks multicast — the check consults the unicast RIB, so if the reverse path differs from the forward path, valid traffic is rejected. A separate multicast RIB (via MP-BGP or static mroutes) exists to decouple them where necessary.

### PIM

Protocol Independent Multicast builds the distribution trees. It is "independent" because it has no topology database of its own — it simply uses whatever the unicast table says, via [[#Reverse Path Forwarding|RPF]].

|Mode|Behavior|Use|
|---|---|---|
|Dense|flood everywhere, then prune back where unwanted|only where receivers are nearly everywhere. Effectively obsolete|
|Sparse|build a shared tree rooted at a Rendezvous Point; join explicitly|the default choice|
|SSM|build a source-specific tree directly, no RP at all|the modern default where receivers know the source|
|Bidir|shared tree in both directions, no source registration|many-to-many, e.g. trading floors|

PIM-SM's shared tree `(*,G)` is rooted at the Rendezvous Point, which every source registers with and every receiver joins toward. Once traffic flows, the last-hop router usually switches to the shortest-path tree `(S,G)` directly toward the source and prunes off the shared tree. The RP is thus a rendezvous mechanism, not a permanent forwarder — but it is still a dependency, which is why RP redundancy (Anycast RP with MSDP) matters.

PIM-SSM removes the RP entirely by requiring the receiver to name the source. Simpler, more secure, and the right default for the one-to-many streaming that is most multicast traffic.

### IGMP

How a host tells its local router that it wants a group. IGMPv2 signals interest in a group; IGMPv3 adds source filtering, which is what makes [[#PIM|PIM-SSM]] possible.

IGMP snooping is the Layer 2 companion: without it, a switch treats multicast as unknown-unicast and floods it to every port in the VLAN, so a single video stream saturates every access port. Snooping has the switch listen to IGMP and forward each group only to the ports that asked.

---

## Routing Security

Routing protocols were designed among people who trusted each other. Every protocol in this note will, by default, believe what it is told — and a router that believes a lie forwards traffic wherever the liar chooses. The threat model is not just disruption; it is silent interception.

### Protocol Authentication

Cryptographically verifying that an update came from a legitimate neighbor. Without it, anyone who can put a packet on the segment can form an adjacency and inject routes.

|Protocol|Mechanism|
|---|---|
|RIPv2|plain text or MD5|
|EIGRP|MD5, or SHA-256 in named mode via a key chain|
|OSPFv2|plain text, MD5, or SHA (RFC 5709)|
|OSPFv3|IPsec AH/ESP, or built-in authentication (RFC 7166)|
|IS-IS|plain text or HMAC-MD5|
|BGP|TCP-MD5 (RFC 2385), or the modern TCP-AO|

```cisco
key chain OSPF-KEYS
 key 1
  key-string <secret>
  cryptographic-algorithm hmac-sha-256
!
interface GigabitEthernet0/1
 ip ospf authentication key-chain OSPF-KEYS
```

Authentication proves identity, not honesty. It stops an outsider injecting routes; it does nothing about a legitimate but compromised or misconfigured neighbor advertising something it should not. That requires [[#Prefix Filtering|filtering]].

Pair it with [[#Passive Interface|`passive-interface default`]]. Authentication protects the links that carry neighbors; passive-by-default ensures no other link is even offering the protocol.

### Prefix Filtering

Deciding what to believe, independently of who said it. The complement to authentication, and the more important of the two.

At an eBGP edge the minimum is:

- Inbound — reject bogons and RFC 1918 space, reject your own prefixes coming back, reject prefixes longer than `/24` (IPv4) or `/48` (IPv6), and cap the session with `maximum-prefix`.
- Outbound — permit your own prefixes and your customers'. Nothing else, ever. See [[#BGP Policy|BGP policy]].

`neighbor X maximum-prefix 500 90 restart 15` tears the session down if a peer suddenly announces far more than it should. It is crude, but it is the difference between one broken session and a router out of memory with every prefix invalid — and it catches the common case where a customer accidentally leaks a full table.

### Unicast RPF

Validates _source_ addresses. Every check so far in this note has examined the destination; uRPF asks whether the source address is plausible given the interface the packet arrived on.

|Mode|Check|
|---|---|
|Strict|the source must be reachable via the _same_ interface the packet came in on|
|Loose|the source must simply exist somewhere in the [[#The Routing Table|

```cisco
interface GigabitEthernet0/1
 ip verify unicast source reachable-via rx      ! strict
 ip verify unicast source reachable-via any     ! loose
```

Strict mode is the effective one and drops spoofed traffic outright, but it breaks under [[#Hop-by-Hop Forwarding|asymmetric routing]] — perfectly valid traffic arrives on the "wrong" interface and is discarded. It belongs at the access edge, where a single-homed customer or a user VLAN has exactly one legitimate direction.

Loose mode survives asymmetry and therefore fits multihomed and core links, but it only catches source addresses that are entirely unrouted. It is nearly useless as anti-spoofing and is deployed mainly as the enforcement half of [[#Remotely Triggered Black Hole|source-based RTBH]].

### Control Plane Policing

Rate-limits traffic [[#Punt to the CPU|punted]] to the CPU, classified by type, so that a flood cannot starve the control plane.

```cisco
control-plane
 service-policy input COPP-POLICY
```

The failure it prevents is the ugly one: a router under a control-plane flood drops its routing adjacencies, which withdraws its routes, which reroutes traffic onto other routers, which then receive the same flood. The attack propagates through the network by way of the routing protocol itself. CoPP is what keeps a local overload local.

Deploy it in monitoring mode first. A too-aggressive CoPP policy drops the very protocol traffic it exists to protect, and does it silently.

### BGP Hijacking and RPKI

BGP has no way to verify that an AS is entitled to originate a prefix. Announce someone else's prefix with a shorter [[#Well-Known Mandatory|AS_PATH]] or a more specific mask, and by the ordinary rules of [[#Best Path Selection|best-path selection]] and [[#Longest Prefix Match|longest prefix match]], the world routes to you. This is not an exploit — it is the protocol working exactly as designed, on a false input.

Hijacks are usually accidents (a typo, a leaked internal aggregate) and occasionally deliberate interception. Either way, the traffic goes where the announcement points.

|Defence|What it validates|Status|
|---|---|---|
|IRR filtering|a registry entry claiming who may originate a prefix|widely used; registries are frequently stale|
|RPKI / ROA|a cryptographically signed statement of which AS may originate a prefix, and at what maximum length|deployed and growing; the current practical answer|
|BGPsec|the entire AS_PATH, signed hop by hop|standardized, essentially undeployed — the overhead is prohibitive|

RPKI is origin validation only: it proves that the _first_ AS in the path is entitled to announce the prefix. It says nothing about whether the rest of the path is real, so a hijacker who forges a plausible origin AS in the path still succeeds. It closes the common case, not the determined one — which is why it must be paired with [[#Prefix Filtering|prefix filtering]] and with route leak defences such as RFC 9234 peering roles.

### Remotely Triggered Black Hole

Turning [[#Null Route|Null0]] into a network-wide, instantly deployable drop, triggered from one place — the standard way to absorb a volumetric DDoS at the edge rather than at the target.

Destination-based RTBH:

1. Every edge router carries a static route for an unused address — e.g. `192.0.2.1` — to `Null0`.
2. A trigger router originates the victim's prefix into iBGP with the next hop set to `192.0.2.1` and the NO_EXPORT [[#Optional Transitive|community]].
3. Every edge router resolves that next hop to `Null0` and drops the traffic, at line rate, in hardware.

One BGP announcement blackholes the prefix at every edge simultaneously. The cost is honest and must be understood: the victim's address becomes unreachable. RTBH completes the attack on that host in order to save the rest of the network — it is damage control, not mitigation.

Source-based RTBH inverts it, blackholing traffic _from_ an attacking source by combining the same trigger with [[#Unicast RPF|loose uRPF]]: if the source resolves to `Null0`, the uRPF check fails and the packet is dropped. It preserves the victim, but it only works while the source addresses are few and not spoofed.

---

## Verification and Troubleshooting

### Routing Table Inspection

```cisco
show ip route
show ip route 10.1.4.7                 ! which entry actually matches this address
show ip route 10.1.4.0 255.255.255.0   ! this exact prefix only
show ip route summary                  ! entry counts by source — table size and growth
show ip cef 10.1.4.7                   ! what the data plane will really do
show ip cef exact-route 10.1.1.1 10.1.4.7   ! which ECMP path this flow takes
show ip protocols                      ! what is running, what it advertises, what it filters
```

`show ip route <address>` is the fastest answer to "why is traffic going there" — it performs the [[#Longest Prefix Match|longest prefix match]] for you and shows the winning entry, which is frequently a more specific route nobody remembered.

Compare `show ip route` against `show ip cef` whenever behaviour and configuration disagree. The RIB is what the [[#Control Plane|control plane]] decided; CEF is what the [[#Data Plane|data plane]] will do. Packets follow CEF.

### Protocol State

```cisco
show ip ospf neighbor                  ! stuck in ExStart = MTU; stuck in Init = one-way hellos
show ip ospf interface brief           ! area, cost, timers, network type, neighbor count
show ip ospf database
!
show ip eigrp neighbors
show ip eigrp topology                 ! successors, feasible successors, FD/RD
show ip eigrp topology active          ! anything stuck in active
!
show isis neighbors
show isis database
!
show bgp ipv4 unicast summary          ! state per peer; Active/Idle = TCP is failing
show bgp ipv4 unicast 192.0.2.0/24     ! every path, and why the best one won
show bgp ipv4 unicast neighbors X advertised-routes
show bgp ipv4 unicast neighbors X received-routes    ! needs soft-reconfiguration inbound
```

`show bgp <prefix>` states the winning reason explicitly, which turns [[#Best Path Selection|best-path selection]] from a list to be memorized into something the router simply tells you.

### Path Testing

```cisco
ping 10.1.5.7 source Loopback0         ! test the path the application will actually use
ping 10.1.5.7 size 1500 df-bit         ! find MTU black holes
traceroute 10.1.5.7 source Loopback0
!
show ip arp
show ipv6 neighbors
show ip route repair-paths             ! precomputed backups, if LFA is enabled
debug ip routing                       ! RIB changes only — safe, and reveals flapping
```

Always specify a source. An unsourced ping uses the exit interface's address, which may take a different path, be filtered differently, or be the one address that happens to work — testing the wrong thing convincingly is worse than not testing.

`traceroute` relies on [[#TTL Decrement|TTL]] expiry and ICMP being permitted; missing hops usually mean filtering rather than a break. It shows the forward path only — asymmetry means the return path is invisible, and diagnosing it requires a traceroute from the other end.

### Common Failure Patterns

|Symptom|Usual cause|
|---|---|
|Route in the table, traffic goes elsewhere|a more specific [[#Longest Prefix Match|
|Route absent despite correct configuration|it lost on [[#Administrative Distance|
|Neighbor never forms|mismatched timers, area, AS, [[#Protocol Authentication|
|OSPF stuck in ExStart/Exchange|MTU mismatch|
|Route redistributed but never appears|missing [[#Seed Metric|
|Traffic black-holed after a [[#Summarization|summary]]|
|Works small, fails large|MTU — [[#MTU and Fragmentation|
|Intermittent, path-dependent failure|[[#Hop-by-Hop Forwarding|
|BGP peer flaps Idle/Active|TCP failing — no route to the peer, port 179 filtered, or an AS mismatch|
|EIGRP routes drop periodically|[[#Stuck in Active|
|Everything reconverges constantly|a [[#Route Flapping and Dampening|
|Loop only during failover|[[#Redistribution Loops|

The pattern behind most of these: routing problems are rarely a wrong route. They are an unnoticed _better_ route, a route silently rejected, or two routers holding different opinions that no protocol is able to reconcile.