---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - ccnp
  - claude
  - encor/routing
  - networking
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-07-15
---
_A router must determine, for each packet, the appropriate egress path. The routing table records that determination. This note addresses the three mechanisms that populate it: routes entered manually, a trust ranking that resolves conflicts between sources, and protocols that maintain the table automatically._

A switch forwards inside a broadcast domain. A router forwards between them, and to do that it needs a table mapping destination prefixes to next hops. Three questions define everything that follows:

- The origin of routes. Some are derived automatically from the router's own interfaces, some are entered by an administrator — see [[#Static Routing|static routing]] — and some are learned from other routers.
- The resolution of conflict. Where two sources advertise the same destination, one must be selected. This is governed by [[#Administrative Distance|administrative distance]].
- The maintenance of correctness under change. This is the function of [[#The Idea of a Routing Protocol|a routing protocol]].

Underlying all three is [[#The Routing Table|the routing table]] itself, together with one ordering that should be established before anything else, since most confusion about routing reduces to confusion over which of the following three quantities applies at which stage:

- A metric ranks paths within a single protocol.
- An administrative distance ranks sources against one another, for the same prefix.
- A longest prefix match selects the route used for a given packet, and consults neither of the other two.

> [!important] Routing is one-directional 
> A router determines only the next hop for a packet. It exercises no control over the return path, which is decided independently by the routers along that path, using their own tables. A route that exists in one direction but not the other produces a connection that fails without an evident cause: packets are transmitted, and nothing returns. Where a path is expected to operate but does not, the return route should be verified first.

---

## The Routing Table

_The data structure that every other section of this note either populates or consults. An understanding of what a single entry contains, and how one is selected, constitutes the greater part of routing._

### What a Route Entry Contains

A single entry answers "for this range of destinations, send the packet here". In practice it carries:

- The destination prefix — a network address plus a prefix length, such as `10.20.30.0/24`. The prefix length is what makes the entry more or less specific.
- The next hop — the IP address of the neighbouring router to hand the packet to, or the interface to send it out of, or both.
- The route source — connected, static, OSPF, BGP, and so on. This is what determines the entry's administrative distance.
- The administrative distance and the metric, conventionally shown together as `[AD/metric]`.

On a Cisco router the entry reads left to right in exactly that order:

```cisco
O    10.20.30.0/24 [110/20] via 10.255.0.2, 00:04:11, GigabitEthernet0/1
```

`O` is the source (OSPF), `110` its administrative distance, `20` the OSPF metric, and `10.255.0.2` the next hop.

### Route Sources

Every route in the table arrived by one of three routes of its own:

- Connected. The router has an interface configured in that subnet and the interface is up. It knows the subnet exists because it is physically in it. No configuration beyond the IP address is needed.
- Static. An administrator typed it in. See [[#Static Routing|static routing]].
- Dynamic. Another router advertised it, over a routing protocol. See [[#The Idea of a Routing Protocol|the idea of a routing protocol]].

This taxonomy is exhaustive. Everything else — floating statics, redistribution, summarisation — is a variation upon one of these three.

### Connected and Local Routes

The moment an interface is given an address and comes up, the router installs two entries for it:

```cisco
C    10.20.30.0/24 is directly connected, GigabitEthernet0/1
L    10.20.30.1/32 is directly connected, GigabitEthernet0/1
```

The `C` route is the subnet the interface sits in — this is the route that lets the router forward toward hosts on that segment. The `L` route is a host route for the interface's own address, which is how the router recognises traffic addressed to itself. Connected routes carry administrative distance 0: nothing is more trustworthy than "I am physically attached to this".

On a Layer-3 switch the interfaces producing these routes are not physical router ports but SVIs and routed ports — the switch's own gateway addresses, covered in the VLAN note under [[VLANs#Inter-VLAN Routing|inter-VLAN routing]]. A [[VLANs#Routed Ports|routed port]] in particular is how a switch presents a point-to-point link to another Layer-3 device, and it is those links that the point-to-point prefixes discussed below run over.

The dependency is unidirectional and consequential: a connected route exists only while the interface is up. Because static and dynamic routes are ultimately resolved against connected routes, an interface transitioning to down silently removes considerably more than its own subnet.

A host performs a reduced form of the same decision for every packet it transmits, determining whether the destination lies within its own subnet or must be forwarded to its gateway. This is covered in the subnetting note under [[Subnetting#The Host Forwarding Decision|the host forwarding decision]].

### Longest Prefix Match

_The rule that selects the route applied to a given packet. It takes precedence over every other mechanism described in this note._

When a packet arrives, its destination address may fall within several installed prefixes simultaneously. The router selects the most specific of them, namely the entry with the longest prefix length — not the entry with the best administrative distance, and not the entry with the best metric.

This is what renders hierarchical addressing workable. A `/16` may cover an entire site while individual `/24`s within it are steered separately, and packets resolve automatically to the most specific entry that covers them. The addressing arithmetic underlying the match is covered in [[Subnetting#Longest Prefix Match|the subnetting note]]; what is material here is its position in the decision order, which is first.

The corollary is the most useful diagnostic practice in routing: to determine what a router will do with a given packet, do not read the table and reason from it. Query the router for the specific destination.

### The Default Route

The prefix `0.0.0.0/0` has a prefix length of zero, so it matches every possible address — and, being the shortest possible prefix, it always loses the longest-prefix match to any other entry that covers the destination. This is precisely what makes it useful: it is the entry that receives every destination no other entry covers. Cisco terms it the gateway of last resort.

A default route is the reason a small site requires almost no routing configuration. It need not know the structure of the internet; it need only know its egress.

### The RIB and the FIB

Two tables, readily conflated, whose distinction accounts for the tooling:

- The <strong>RIB</strong> (<strong>Routing Information Base</strong>) is the <mark style="background: #FF5582A6;">control plane's table</mark>. It is what the routing protocols, static configuration, and connected interfaces all compete to install into. `show ip route` displays the RIB.
- The <strong>FIB</strong> (<strong>Forwarding Information Base</strong>) is the <mark style="background: #FFB8EBA6;">data plane's table</mark>. It is derived from the RIB, optimized for lookup, and pushed into hardware. `show ip cef` displays the FIB. On Linux, the kernel's forwarding trie plays this role.

Administrative distance operates on entry to the RIB. Longest prefix match operates on exit from the FIB. The two never interact, which is precisely why they are so frequently conflated. The following diagram represents the structure of the entire note:

```
CONTROL PLANE — how a route enters the table
───────────────────────────────────────────

  connected   static     OSPF     EIGRP     RIP     BGP
      │          │         │        │        │       │
      │          │         └────────┴───┬────┴───────┘
      │          │                      ▼
      │          │        within one protocol the best
      │          │        path to a prefix is chosen
      │          │        by its own METRIC
      │          │                      │
      └──────────┴────────────┬─────────┘
                              ▼
        ┌─────────────────────┬─────────────────────┐
        │ Same prefix from two sources?             │
        │ The lower ADMINISTRATIVE DISTANCE is      │
        │ installed; the unsuccessful route is      │
        │ retained as a registered backup.          │
        │                                           │
        │ Different prefix lengths are distinct     │
        │ destinations — both are installed.        │
        └─────────────────────┬─────────────────────┘
                      ┌───────┴───────┐
                      │      RIB      │
                      └───────┬───────┘
                      ┌───────┴───────┐
                      │      FIB      │
                      └───────┬───────┘
                              │

DATA PLANE — how a packet uses the table
───────────────────────────────────────
                              ▼
        a packet for 10.20.30.200 arrives
                              │
                              ▼
     LONGEST PREFIX MATCH across every installed
     prefix. Administrative distance is not
     consulted here.
                              │
                              ▼
           next hop / exit interface
```

---

## Static Routing

_Routes entered manually. Entirely deterministic, imposing no protocol overhead, and incapable of reacting to any change._

A static route is an assertion by an administrator: to reach this prefix, use this path. The router does not verify the assertion beyond confirming that the next hop is reachable. No aspect of a static route adapts: if the path it names fails, the route continues to reference the failure until it is changed manually or withdrawn by another mechanism.

### Anatomy of a Static Route

```cisco
ip route  10.20.30.0   255.255.255.0  10.255.0.2
!        └─ prefix ─┘ └─── mask ───┘ └ next hop ┘
```

An optional trailing number sets the administrative distance, which is the mechanism behind [[#Floating Static Routes|floating static routes]]:

```cisco
ip route 10.20.30.0 255.255.255.0 10.255.0.2 200
```

### Next-Hop, Exit Interface, and Fully Specified

There are three means of specifying the destination of the packet, and the choice carries material consequences:

|Form|Example|Behaviour|
|---|---|---|
|Next-hop only|`ip route 10.20.30.0 255.255.255.0 10.255.0.2`|The router must resolve `10.255.0.2` against the routing table to find an egress interface. See [[#Recursive Lookup\|recursive lookup]].|
|Exit interface only|`ip route 10.20.30.0 255.255.255.0 Serial0/0/0`|No recursion. Safe on a point-to-point link, where there is only one possible neighbour. Problematic on Ethernet.|
|Fully specified|`ip route 10.20.30.0 255.255.255.0 GigabitEthernet0/1 10.255.0.2`|Both. No recursion, and an unambiguous neighbour. The right choice on a multi-access link.|

The exit-interface-only form is hazardous on a broadcast segment. The router treats every destination within the prefix as though it were directly attached to that segment, and issues an ARP request for each one individually. It functions only if the actual next-hop router responds with proxy ARP, and it inflates the ARP table with an entry per remote destination. On Ethernet, the fully specified form should be used.

> [!warning] A static route pointing at an interface still has administrative distance 1 
> A persistent claim holds that a static route configured with an exit interface carries administrative distance 0, as a connected route does. It does not: it carries AD 1, as any other static route does. The confusion originates in the display, where such a route is rendered as "is directly connected", resembling a connected route. Older revisions of Cisco's administrative-distance document carried a footnote asserting AD 0; the current revision has removed it, and the table now lists static routes at 1 without qualification. Where doubt arises, the bracketed `[AD/metric]` field in `show ip route` is authoritative.

#### Recursive Lookup

A static route that specifies only a next-hop IP address has not identified an egress interface. The router therefore performs a second lookup, resolving the next hop against its own routing table to determine how to reach it, and inherits that route's egress interface. This is recursion, and it has two consequences:

- It constitutes a rudimentary health check. If the next hop cannot be resolved in the routing table, the static route is not installed. Loss of the connected route in which the next hop resides removes the static route along with it.
- It may resolve incorrectly. If the next hop is reachable only via a [[#The Default Route|default route]], the static route will still be installed and will still appear correct, while directing traffic to an unintended destination. A recursive route that resolves via a default route is almost always an error.

The health check is weaker than it appears. Reachability of the next hop by ARP does not establish that the path beyond it is functional. A common failure is a link that remains physically up through an intermediate switch while the router at the far end has failed. The static route remains installed, traffic continues to be forwarded to an unreachable destination, and no failover occurs. Object tracking (IP SLA) or BFD closes this gap.

### The Default Static Route

The single most common static route in existence:

```cisco
ip route 0.0.0.0 0.0.0.0 10.255.0.1
```

All traffic for which no more specific route exists is forwarded to `10.255.0.1`. On a stub site with a single uplink, this one line constitutes the entire routing configuration, and it is the correct one: operating a routing protocol to learn a single egress would confer no benefit.

### Floating Static Routes

_A static route deliberately assigned an unfavourable administrative distance, so that it remains out of the table until a preferred route is withdrawn._

This is the first point at which [[#Administrative Distance|administrative distance]] functions as an instrument rather than a constraint. A static route assigned a distance worse than that of the protocol whose route it backs up will lose the comparison and remain out of the RIB. If the protocol's route is subsequently withdrawn, no competing route remains, and the static route is installed.

```cisco
! primary path is learned via OSPF (AD 110)
! this backup stays dormant until the OSPF route disappears
ip route 10.20.0.0 255.255.0.0 10.255.9.1 130
```

The value must be selected with reference to the protocol: 130 exceeds OSPF's 110, so the OSPF route prevails while it exists. A value of 100 would cause the backup to prevail immediately and permanently conceal the OSPF route, which is the characteristic failure of this construction. The rule is straightforward: the floating route's distance must be strictly worse than that of every route to which it is intended to defer.

The corresponding failure mode warrants explicit statement, as it presents no obvious symptom: a floating static assumes the path only when the primary route is withdrawn. If the primary is never withdrawn, because the interface remained up despite the failure of the path, the backup is never activated, and the outage persists while the routing table appears entirely correct.

### Blackhole and Null Routes

Pointing a route at the null interface discards matching traffic:

```cisco
ip route 192.0.2.0 255.255.255.0 Null0
```

There are three distinct reasons to do this, of which only the first is self-evident:

- Discarding unwanted traffic. Dropping at the routing table is computationally inexpensive.
- Anchoring a summary. To advertise an aggregate that the router does not itself have a complete route for, the aggregate must exist in the RIB. A Null0 route creates it.
- Preventing summarization loops. If a router advertises a summary upstream but does not hold every sub-prefix within it, packets addressed to the missing sub-prefixes arrive, match no specific entry, match the router's own default route, and are returned upstream, forming a loop. A Null0 route covering the summary intercepts precisely those packets and discards them. This is why a summary and a corresponding discard route are normally configured together; the addressing aspect is covered in [[Subnetting#Route Summarization|the subnetting note]].

Linux provides the same facility, with greater precision as to how the discard is reported:

```bash
ip route add blackhole 192.0.2.0/24     # drop silently
ip route add unreachable 192.0.2.0/24   # drop, send ICMP host unreachable
ip route add prohibit 192.0.2.0/24      # drop, send ICMP administratively prohibited
```

### Where Static Routing Fits

Static routing is appropriate more often than its reputation suggests. It is correct where:

- The site has a single egress. A default route is sufficient, and a protocol would add nothing.
- The path must be deterministic and must not be renegotiated by anything.
- The peer will not run a routing protocol, as with most ISP handoffs that do not use BGP.
- The topology is sufficiently small and stable to be maintained reliably by hand.
- It is acting as a backup, as a floating static.

It is inappropriate where the network has redundant paths that must fail over autonomously, where the topology changes, or where the product of the router count and the prefix count exceeds what can be reliably maintained by hand. These are the conditions a routing protocol exists to address.

---

## Administrative Distance

_A ranking of the trust the router places in each source of routing information. It exists because the values produced by different protocols are not comparable._

### The Problem It Solves

Consider a router that learns a route to `10.50.0.0/16` from both OSPF and RIP. OSPF reports a cost of 20; RIP reports a hop count of 3. Which of the two paths is superior?

The question admits no answer. An OSPF cost is derived from cumulative link bandwidth; a RIP hop count is the number of intervening routers. The two measure different quantities, on different scales, in different units. No conversion exists between them, and there is no principled basis on which to assert that 20 of the one is better or worse than 3 of the other.

Administrative distance does not attempt to resolve this problem; it circumvents it. Rather than comparing the values the protocols produced, it ranks the protocols that produced them. The router does not evaluate which path is superior, but which source is the more trustworthy — a question that does admit an answer, because it concerns the protocols themselves rather than any particular network.

Lower values denote greater trustworthiness. The route from the most trusted source is installed; the remainder are not.

> [!note] Administrative distance is local and is never advertised 
> A router's administrative distances constitute its own assessment. They are not carried in any routing update, and no neighbour learns them. Changing the AD of a protocol on one router affects only that router's table. This is why AD changes applied inconsistently tend to produce asymmetric routing: each router forms its judgement independently.

### The Default Values

The values Cisco assigns by default:

|Route source|Default administrative distance|
|---|---|
|Connected interface|0|
|Static route|1|
|EIGRP summary route|5|
|External BGP (eBGP)|20|
|Internal EIGRP|90|
|IGRP (obsolete)|100|
|OSPF|110|
|IS-IS|115|
|RIP|120|
|EGP (obsolete)|140|
|On-Demand Routing (ODR)|160|
|External EIGRP|170|
|Internal BGP (iBGP)|200|
|Unknown / untrusted|255|

Two entries deserve comment.

`255` does not denote merely the least preferred case. A route with distance 255 is not installed at all: the router declines to accept the source. <mark style="background: #FFB8EBA6;">Setting a route's AD to 255 is a means of disabling it without deleting it</mark>.

The eBGP/iBGP split — 20 against 200 — appears arbitrary but is not. External BGP routes describe destinations outside the autonomous system, of which no interior protocol has any knowledge, so eBGP is trusted above every IGP at 20. Internal BGP routes are copies of information relayed within the AS, where an interior protocol is authoritative; iBGP is therefore placed at 200, worse than every IGP, so that the IGP always prevails for internal prefixes. The values encode a design intent regarding which source is authoritative for which class of destination.

These are not Cisco-specific conventions. The same values appear independently in FRRouting's `zebra` daemon — static 1, eBGP 20, EIGRP 90, OSPF 110, IS-IS 115, RIP 120, iBGP 200, connected 0, and 255 as the maximum — which provides useful corroboration that the ranking reflects a genuine property of the protocols rather than the preference of a single vendor.

### Administrative Distance Is Not a Metric

The two are frequently confused; the distinction is exact:

||Administrative distance|Metric|
|---|---|---|
|Compares|Different sources, same prefix|Different paths, same prefix, same protocol|
|Set by|The router's local policy|The routing protocol's own algorithm|
|Meaning|The degree of trust in the source|The quality of the path|
|Units|None — it is a rank|Protocol-specific: hops, cost, composite|
|Advertised|No|Yes, within the protocol|
|Applies when|Installing a route into the RIB|Choosing the best path inside one protocol|

The sequence is therefore as follows: each protocol independently applies its own [[#Metrics|metric]] to select its single best path to a prefix; those selections are then compared against one another by administrative distance; and the surviving route is installed. A metric comparison never crosses protocol boundaries, and an administrative distance comparison never occurs within a single protocol.

### Longest Prefix Match Beats Administrative Distance

_The most consequential misunderstanding in this domain, and the one warranting the closest attention._

Administrative distance compares only routes for an identical prefix. Routes with different prefix lengths constitute different destinations; the router does not regard them as being in competition, and installs all of them.

Consider a router that has learned three overlapping routes from three sources:

|Source|Prefix|AD|Next hop|Covers|
|---|---|---|---|---|
|Static|`10.20.0.0/16`|1|`10.255.0.1`|10.20.0.0 – 10.20.255.255|
|OSPF|`10.20.30.0/24`|110|`10.255.0.2`|10.20.30.0 – 10.20.30.255|
|RIP|`10.20.30.128/25`|120|`10.255.0.3`|10.20.30.128 – 10.20.30.255|

All three are installed. They have different prefix lengths and are therefore not in competition. Consider the forwarding of three packets:

- To `10.20.30.200` — inside all three ranges. The longest match is the `/25`. The packet goes via `10.255.0.3`, the RIP route, which has the worst administrative distance in the table.
- To `10.20.30.50` — inside the `/16` and the `/24`, but below `.128` so outside the `/25`. The longest match is the `/24`, via the OSPF route.
- To `10.20.99.1` — inside the `/16` only. It goes via the static route.

The static route, holding the best possible administrative distance, receives only the traffic that no more specific entry claimed. The RIP route, holding the worst, prevails outright for its `/25`. Administrative distance did not enter the forwarding decision at any point, because no contest for an identical prefix arose to be arbitrated.

Cisco's documentation draws precisely this distinction: prefix length determines which of the installed routes a packet uses, whereas administrative distance determines which routes are installed in the first place. Two distinct contests, occurring at two distinct stages.

### Adjusting Administrative Distance

For a whole protocol, inside the routing process:

```cisco
router rip
 distance 90
```

For a single static route, as a trailing argument, which is the floating static mechanism:

```cisco
ip route 10.20.0.0 255.255.0.0 10.255.9.1 130
```

There is no command to change the distance of all static routes at once; each one carries its own.

> [!warning] Administrative distance changes carry substantial risk 
> AD changes are local, so an inconsistent change across routers produces routers that disagree as to the best path, resulting in a routing loop or a blackhole according to the topology. Cisco's documentation warns explicitly of this. AD should be adjusted only for a specific reason, such as a floating static or a protocol migration; the change should be planned across every affected device, and its effect on traffic determined before commitment.

### What Happens to the Losing Route

A route that loses the administrative-distance comparison is not discarded. Protocols that maintain their own database — OSPF, IS-IS, EIGRP, BGP, RIP — retain the route and register it with the routing table as a backup. If the installed route is subsequently withdrawn, the routing table requests that the registered protocols reinstall, and the best remaining candidate by AD is installed. This is what makes administrative distance a functioning failover mechanism rather than merely a tiebreak: the unsuccessful route remains available.

This is also why the OSPF database may contain a route that never appears in `show ip route`. The route is known; it was not selected. Examining only the routing table during troubleshooting therefore conceals half of the available information, since the unsuccessful candidates reside in the protocol's own database.

### Administrative Distance on Linux

There is no administrative distance in the Linux kernel. The kernel's own header states this directly: route protocol values above `RTPROT_STATIC` are, in the wording of the source, not interpreted by the kernel and are passed from user space and back unchanged.

In concrete terms: the `proto` field on a Linux route (`proto kernel`, `proto static`, `proto dhcp`, `proto bgp`, `proto ospf`) is a label recording which component installed the route. It is informational. The kernel does not rank sources by it, and will not prefer an OSPF route over a RIP route on its account.

What the kernel has instead is a per-route metric:

```bash
ip route add 10.20.0.0/16 via 10.255.0.2 metric 100
ip route add 10.20.0.0/16 via 10.255.9.1 metric 200
```

Both routes exist simultaneously; the lower metric is used. The iproute2 documentation states explicitly that this value is an arbitrary 32-bit number in which lower values are preferred. It is a priority, not a path cost and not a trust ranking. Employed in this manner it is the closest Linux analogue to a floating static, although the quantity it expresses is nearer to a metric than to an administrative distance.

Administrative distance does exist on Linux, but not in the kernel. It is implemented in userspace, within a routing suite. FRRouting's `zebra` daemon acts as the arbiter: each protocol daemon (`ospfd`, `bgpd`, `ripd`, `staticd`) offers its routes to `zebra`, which compares them by distance exactly as a Cisco router would, and installs only the successful route into the kernel. Its defaults are drawn directly from the table given in [[#The Default Values|the default values]] above. The kernel observes only the outcome.

The practical consequence for a Linux host running FRR is that `ip route show` reports the outcome, whereas `vtysh -c "show ip route"` reports the comparison that produced it.

---

## The Idea of a Routing Protocol

_The automation of what static routing performs manually: discovering what exists, establishing agreement on how to reach it, and repeating the process correctly whenever the network changes._

### What a Routing Protocol Must Do

Setting aside the differences between protocols, the same six functions remain:

- <strong>Discover neighbours</strong>. Identify the other routers willing to exchange routes, generally by transmitting periodic hello messages and forming an adjacency with those that respond.
- <strong>Exchange reachability</strong>. Advertise to neighbours the destinations this router can reach, and receive theirs.
- Compute a best path, free of loops. This is the point at which the protocols differ, and it is what defines the families described below.
- <strong>Install the result</strong> — subject to administrative distance, since the protocol only proposes.
- <strong>Detect change</strong>. Identify the loss of a neighbour or the failure of a link.
- Reconverge. Recompute, redistribute, reinstall, and restore a network in which every router again agrees.

### Metrics

A metric is a <strong>protocol</strong>'s <mark style="background: #FFB8EBA6;">internal measure of path quality</mark>, used to select among several paths to the same prefix. <mark style="background: #FF5582A6;">Lower values are always preferred</mark>. The parameter is determined by the protocol's designers and constitutes the protocol's entire definition of path quality:

|Protocol|Metric|Quantity measured|
|---|---|---|
|RIP|Hop count|Number of routers traversed. Maximum 15; a metric of 16 means unreachable.|
|OSPF|Cost|Sum of per-link costs, each derived from interface bandwidth.|
|IS-IS|Cost|Sum of per-link costs, administratively assigned.|
|EIGRP|Composite|Bandwidth and delay by default.|
|BGP|None|No single metric — a long ordered list of tiebreaks, most of them policy.|

RIP's metric is the clearest illustration that a metric embodies a judgement rather than a fact. Hop count treats a 10 Gbps link and a dial-up modem as equivalent, and will route across the modem if doing so saves one hop. The metric is not incorrect; it measures precisely what it was designed to measure, and that quantity ceased to be a sound proxy for path quality decades ago.

RIP's treatment of 16 as unreachable is likewise not incidental. It is a deliberate ceiling, and it limits the usable diameter of a RIP network to 15 hops — the cost of the loop mitigation described below.

### Protocol Families

The families are defined by what a router knows and how it computes. That single distinction determines everything else about them: convergence speed, resource cost, and failure mode.

```
DISTANCE VECTOR             │ LINK STATE
routing by rumour           │ every router holds the same map
────────────────────────────┼────────────────────────────────
                            │
R2 advertises to R1:        │ Every router floods a list of
  "I reach 10.0.0.0/8       │ its OWN links:
   at a cost of 3."         │   R1: "links to R2, R3"
                            │   R2: "links to R1, R4"
R1 derives:                 │   R3: "links to R1, R4"
  "My cost is therefore 4,  │   R4: "links to R2, R3"
   by way of R2."           │
                            │ Every router then holds an
R1 never observes the       │ identical link-state database
topology. It accepts R2's   │ and runs Dijkstra over it to
summary and adds its own    │ construct its own
link cost.                  │ shortest-path tree.
                            │
Low cost. Slow convergence. │ High cost. Fast convergence.
Vulnerable to false         │ Loop-free by construction
information.                │ within an area.
```

#### Distance Vector

<mark style="background: #BBFABBA6;">Each router advertises to its neighbors</mark>, <mark style="background: #ABF7F7A6;">for every destination it knows</mark>, <mark style="background: #BBFABBA6;">the distance to that destination</mark>. It does not communicate the path by which it reaches the destination, nor the shape of the topology — only the distance. A router receiving that advertisement adds the cost of the link on which it arrived and treats the result as its own distance.

The consequence is that a distance-vector router never observes the network. It observes its neighbors' summaries and accepts them. This is why the family is conventionally described as routing by rumor; the description is accurate rather than pejorative, since it states precisely what the algorithm does. RIP is the canonical example; the underlying algorithm is Bellman-Ford.

This reliance on second-hand information has a specific failure mode. When a destination becomes unreachable, a router may receive an advertisement for a path to it from a neighbor that is in fact routing through the first router — stale information reflected back. Each accepts the other's advertisement, each increments the metric, and the metric climbs toward infinity one iteration at a time while a loop persists. This is count-to-infinity, and it is the reason RIP defines infinity as 16 rather than a larger value: a small infinity is reached quickly, and the loop terminates.

##### Split Horizon, Poisoning, and Hold-down

The mitigations all attack the reflection of stale information:

- Split horizon. A route is never advertised back out of the interface on which it was learned. A neighbor that advertised a destination is not sent an advertisement for that destination in return.
- Route poisoning and poison reverse. Rather than ceasing to advertise a failed route, the route is advertised explicitly with an infinite metric. Silence is ambiguous; an explicitly poisoned advertisement is not.
- Hold-down timers. Once a route is known to have failed, more favorable advertisements for it are rejected for a defined period, allowing the withdrawal to propagate fully before any router acts on stale information.
- Triggered updates. An update is transmitted the moment a change occurs, rather than at the next periodic broadcast.

These are mitigations of a structural weakness. Collectively they render distance vector workable; they do not render it fast.

#### Link State

<mark style="background: #FFB8EBA6;">Every router describes its own directly attached links</mark> and <mark style="background: #FFB86CA6;">floods that description to every other router in the area</mark>. It does not describe routes; it describes links. <mark style="background: #FFF3A3A6;">Each router assembles the descriptions of every other router into an identical link-state database</mark>, and then <mark style="background: #BBFABBA6;">independently runs Dijkstra's shortest-path algorithm over that database to construct a shortest-path tree rooted at itself</mark>.

The properties follow from that design. Because every router computes from the same map, the routers cannot disagree, and the result is loop-free by construction within an area. Because the map is complete, convergence is rapid: a change is flooded and every router recomputes. Because the map is complete, it is also costly: flooding consumes bandwidth, the database consumes memory, and SPF consumes CPU, each growing with the size of the area. Bounding that cost is the purpose of areas: partitioning the network limits the extent of flooding and the size of any single SPF computation. OSPF and IS-IS are the two link-state protocols in current use.

##### The Reference Bandwidth Trap

OSPF derives a link's cost from its bandwidth, as a reference bandwidth divided by the interface bandwidth, with a floor of 1. The default reference bandwidth is 100 Mbps.

This arithmetic no longer reflects contemporary link speeds. Every interface at or above 100 Mbps divides to 1 or less and is floored at 1. A gigabit link, a ten-gigabit link, and a hundred-gigabit link therefore all carry cost 1, and OSPF cannot distinguish between them; it will load-share across them as equals or select arbitrarily. On any modern network the reference bandwidth must be raised.

```cisco
router ospf 1
 auto-cost reference-bandwidth 100000
```

Consistency is essential: the reference bandwidth must be set identically on every router in the area. If it is changed on some routers and not others, those routers compute costs on different scales, producing precisely the asymmetric, difficult-to-diagnose suboptimal routing that link state was intended to eliminate.

#### Path Vector

<mark style="background: #FFB8EBA6;">BGP advertises,</mark> with <mark style="background: #FF5582A6;">each prefix</mark>, <mark style="background: #FFB8EBA6;">the complete list of autonomous systems through which the advertisement</mark> has passed — <mark style="background: #FFB8EBA6;">the AS path</mark>. Loop detection is consequently exact and requires no algorithm: a router that observes its own AS number in the path discards the route, since accepting it would constitute routing in a cycle.

The essential characteristic of BGP is that it is not a shortest-path protocol but a policy protocol. Its best-path selection is a long, strictly ordered sequence of tiebreaks — weight, local preference, locally originated, AS path length, origin, MED, eBGP over iBGP, IGP metric to the next hop, and others — in which AS path length, the only criterion resembling "shortest", occupies a position several steps down, beneath parameters whose explicit purpose is to permit an operator to override it.

This is by design, and it is why the paths taken across the internet are frequently not the shortest available. They are those selected by the operators' commercial relationships and traffic-engineering preferences. BGP is the protocol by which competing organisations exchange reachability without mutual trust; policy, rather than optimality, is its purpose.

#### Advanced Distance Vector

EIGRP is distance-vector in its foundations, learning distances from neighbours rather than constructing a map, but it incorporates sufficient additional machinery that its behaviour bears little resemblance to RIP.

It maintains a topology table of all known paths rather than only the best one, and runs DUAL (the Diffusing Update Algorithm) over it. The central construct of DUAL is the feasible successor: a backup next hop that is provably loop-free, because the neighbour offering it reports a distance to the destination strictly less than the router's own current best distance, which establishes that the neighbour cannot be routing back through this router. Where the primary path fails and a feasible successor exists, the router transitions to it immediately, without recomputation and without querying any neighbour; failover is effectively instantaneous. Only where no feasible successor exists must the router enter the active state and query its neighbours, which is the slow path.

Its metric is composite, derived from bandwidth and delay by default. EIGRP was Cisco-proprietary for most of its life and is now published as an informational RFC.

### Interior and Exterior Gateway Protocols

The most fundamental division in the taxonomy is not the algorithm but the scope:

- An interior gateway protocol runs inside a single autonomous system — one organisation's network, under one routing policy. Its goal is to find the best path. RIP, OSPF, IS-IS, and EIGRP are IGPs.
- An exterior gateway protocol runs between autonomous systems. Its goal is reachability under policy, not optimality. BGP is the only one in use.

An autonomous system is a network operating under a single, coherent routing policy, identified by an AS number. The distinction is material because the two problems are fundamentally different. Within a single administrative domain the topology is known, every router is trusted, and the objective is the shortest path. Between domains the interior of the peer network is unknown, the peer is not fully trusted, and the objective is control over which of several available relationships carries the traffic.

### Convergence

<strong>Convergence</strong> <mark style="background: #FFB8EBA6;">is the interval</mark> <mark style="background: #FFB86CA6;">between a topology change</mark> and <mark style="background: #BBFABBA6;">the restoration of a consistent, correct, loop-free view across every router</mark>. It is the measure by which routing protocols are most usefully compared, because during convergence the network is in an incorrect state: transient loops and blackholes are expected rather than exceptional.

Four phases, whose durations differ by orders of magnitude:

- <strong>Detect</strong>. Identify that a failure has occurred. Ordinarily the dominant term.
- <strong>Propagate</strong>. Distribute the change to every router.
- <strong>Compute</strong>. Run the algorithm.
- <strong>Install</strong>. Push the result into the RIB, and from there to the FIB and the hardware.

Detection dominates because the elementary mechanism is a hello timer, which requires several successive hellos to be missed before a neighbor is declared unreachable, and that interval is measured in seconds. <strong>BFD</strong> (Bidirectional Forwarding Detection) exists specifically to reduce this term: it is a lightweight protocol whose sole function is to detect the failure of a path to a neighbor within milliseconds and to notify the routing protocol so that it may act immediately. Every modern routing protocol can be driven by BFD, and on any network where rapid failover is required, it should be.

### Shared Vocabulary

Terms recurring across all of them:

- <strong>Adjacency</strong>. An established relationship with a neighbour across which routes are exchanged. Two routers may be physically adjacent and never form an adjacency, which is a common and frequently misdiagnosed failure.
- <strong>Hello and dead intervals</strong>. The frequency at which liveness is asserted, and the duration for which silence is tolerated. These must match between neighbours, or the adjacency will not form.
- <strong>Passive interface</strong>. An interface whose prefix continues to be advertised into the protocol, but on which no protocol packets are transmitted, so that no adjacency can form. This is the correct setting for every user-facing access interface: the subnet belongs in the routing table, but an end host should not be offered a routing adjacency. It is a security control as much as an organisational one.
- <strong>Summarisation</strong>. The advertisement of a single aggregate in place of many specific prefixes. It reduces table size and, more significantly, suppresses churn: a flapping link within the summary does not cause recomputation beyond it.
- <strong>Equal-cost multipath</strong>. Where a protocol identifies several paths with identical metrics, it may install all of them and load-share across them.
- <strong>Route filtering</strong>. Control over which prefixes are advertised or accepted, by means of prefix lists and route maps. Essential wherever two routing domains meet.

---

## Static and Dynamic Together

_The two are not alternatives but distinct instruments, and almost every production network employs both._

### Choosing Between Them

The common and correct pattern in a small-to-medium network is a hybrid: a default static route directed at the ISP, because there is a single egress and nothing to compute, together with an interior gateway protocol within the network, because the interior does possess redundancy and does change.

The decision for any individual route reduces to two considerations: whether anything must react automatically should the path fail, and whether the route can be reliably maintained by hand. Where automatic reaction is not required and reliable maintenance is assured, a static route is not a compromise but the superior engineering choice, and it will continue to operate, unchanged and predictable, indefinitely.

### Redistribution

<strong>Redistribution</strong> takes routes learned by one protocol and injects them into another. It is necessary during migrations, at the boundary between merged networks, and wherever a static or connected route must be advertised into a protocol. It is also the most reliable means of constructing a routing loop that resists diagnosis.

Three hazards, each a consequence of principles established earlier in this note:

- Metrics do not translate. A RIP hop count is meaningless to OSPF. The redistributing router must supply a seed metric, assigned by the administrator, because no conversion exists. Cisco's OSPF applies a default of 20 to redistributed routes where none is given.
- Administrative distance changes beneath the route. A route redistributed into a protocol assumes that protocol's administrative distance, not the one it previously held. A route may therefore become more or less trusted purely by virtue of being redistributed, and may come to prevail over the original from which it was copied.
- Mutual redistribution creates feedback. Where A is redistributed into B and B into A at two different routers, a route may travel out of A, through B, and back into A, arriving as a fresh advertisement that appears legitimate. The network then routes toward a reflection of its own advertisement. Route tags, filtering, and controlled AD manipulation prevent this; all three are required rather than optional.

Redistribution is the point at which every concept in this note interacts simultaneously, which is precisely why it fails so readily. It should be treated as a boundary to be controlled rather than a feature to be enabled.

---

## Verification and Tooling

_The commands that establish the router's current view of the network and the forwarding decision it will make._

### On a Cisco Router

```cisco
show ip route
show ip route 10.20.30.200
show ip route 10.20.30.0 255.255.255.0 longer-prefixes
show ip protocols
show ip cef 10.20.30.200
```

What each is for:

- `show ip route` — the RIB. The whole table, with `[AD/metric]` on every entry.
- `show ip route <address>` — the most valuable single routing command. It reports the entry that would be used for that destination, resolving the longest-prefix match directly. Reading the full table and reasoning about which entry prevails is the principal source of incorrect conclusions; querying the router eliminates the reasoning step entirely.
- `show ip protocols` — the routing protocols in operation, together with their timers, networks, administrative distances, and neighbours. The primary reference where a protocol is not behaving as expected.
- `show ip cef <address>` — the FIB entry, which is what the hardware will use. On the rare occasion that the RIB and FIB disagree, this command reveals it.

### On a Linux Host

```bash
# the routing table
ip route show
ip -4 route show table all

# what the kernel would ACTUALLY do with a packet to this address
ip route get 10.20.30.200

# with FRR: the full contest, including routes that lost
vtysh -c "show ip route"
```

`ip route get` is the Linux counterpart of `show ip route <address>` and merits the same priority. It instructs the kernel to perform an actual lookup and report the result, including the selected source address and the egress interface. It resolves policy rules, longest-prefix match, and metrics in a single step, and it is definitive in a way that reading `ip route show` is not.

In FRR's output, the leading flags are significant: `>` denotes the selected route and `*` denotes the route installed into the kernel FIB. A route present in FRR's RIB without these marks is one that was not selected.

> [!warning] `ip route add` does not survive a reboot 
> A route added with `ip route add` resides in the kernel's memory and nowhere else. It is lost on reboot, and frequently on an interface flap. Persistence is the responsibility of whichever component manages the interface — systemd-networkd, NetworkManager, netplan, or the distribution's interfaces file. A route that operates correctly until the next maintenance window and then disappears is almost invariably attributable to this.

#### Policy Routing Changes the Lookup

Linux does not maintain a single routing table; it maintains several, together with a set of rules determining which is consulted. `ip rule show` lists them in priority order. The kernel evaluates the rules from the lowest priority number upward and uses the first table that yields a match. The built-in tables are `local` (255), `main` (254), and `default` (253).

```bash
ip rule show
ip route show table main
```

This accounts for a specific and frequently misdiagnosed symptom: a route visibly present in `ip route show` that is nonetheless not used. If a rule of higher priority directed the lookup to a different table, the route in `main` was never consulted. `ip route get` accounts for the rules and reports the actual outcome; `ip route show` does not.

---

## Common Pitfalls

_The recurring failures, each traced to the mechanism that accounts for it._

| Symptom                                                                | Root cause                                                    | Where it is explained                                                                  |
| ---------------------------------------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Traffic leaves but nothing comes back                                  | No return route — routing is decided per direction            | [[#Overview\|routing is one-directional]]                                              |
| Static route never appears in the table                                | Its next hop cannot be resolved                               | [[#Recursive Lookup\|recursive lookup]]                                                |
| Route is in the table but packets go elsewhere                         | A longer prefix from another source is winning                | [[#Longest Prefix Match Beats Administrative Distance\|longest prefix match beats AD]] |
| Floating static takes over immediately and hides the real route        | Its AD was set lower than the protocol's, not higher          | [[#Floating Static Routes\|floating static routes]]                                    |
| Floating static never takes over during an outage                      | The primary route never withdrew — the link stayed up         | [[#Convergence\|convergence]]                                                          |
| Static route via an Ethernet exit interface ARPs for every destination | Exit-interface form used on a multi-access link               | [[#Next-Hop, Exit Interface, and Fully Specified\|next-hop and exit interface]]        |
| Every OSPF link reports cost 1                                         | Reference bandwidth left at the 100 Mbps default              | [[#The Reference Bandwidth Trap\|the reference bandwidth trap]]                        |
| A protocol knows a route that never reaches the routing table          | It lost the AD comparison and is being held as a backup       | [[#What Happens to the Losing Route\|what happens to the losing route]]                |
| Redistribution causes loops or persistent flapping                     | Mutual redistribution without tags or filtering               | [[#Redistribution\|redistribution]]                                                    |
| Linux: the route is in `ip route show` but is not used                 | A lower-metric route, or an `ip rule` selecting another table | [[#Policy Routing Changes the Lookup\|policy routing]]                                 |
| Linux: the route disappears after a reboot                             | `ip route add` is not persistent                              | [[#On a Linux Host\|on a Linux host]]                                                  |