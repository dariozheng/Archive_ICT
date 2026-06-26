---
categories:
  - "[[Linux]]"
topic@linux: "[[Linux General]]"
tags:
  - networking
  - documentation
  - firewall
  - framework
icon: SiLinux
iconColor: "#000000"
---
Netfilter is the <mark style="background: #FFB8EBA6;">packet-processing framework</mark> <mark style="background: #FF5582A6;">built into the Linux kernel</mark>. It exposes a set of fixed points — hooks — in the network stack where kernel code can register callbacks to inspect, modify, drop, queue or reroute packets. 
The subsystems most administrators care about ([[#Connection Tracking|connection tracking]], [[#Network Address Translation|NAT]], [[#Logging, Queueing and Accounting|logging and queueing]]) are all built on these hooks. You rarely program <strong>Netfilter</strong> directly; you drive it through a frontend, and the modern one is [[nftables]].

> [!info] Netfilter is the engine, not the tool 
> Netfilter lives in the kernel and defines the hooks and subsystems. 
> 
> [[nftables]] — the `nft` command plus the `nf_tables` kernel module — is the userspace tool that tells Netfilter what to do. Older tools (iptables, ip6tables, arptables, ebtables) are alternative frontends to the same framework; see [[#Frontends and Related Tools]].

# The Netfilter Framework

_What the kernel provides and how it fits into packet processing._

## What Netfilter Is

Netfilter is a <strong>framework</strong>, not a program. The kernel calls every <mark style="background: #FFB86CA6;">registered hook function</mark> as a packet <mark style="background: #FFF3A3A6;">reaches the corresponding point in the stack</mark>, passing <mark style="background: #FFB86CA6;">it</mark> the packet and expecting a [[#Kernel Verdicts|verdict]] back. 
Modules build features on top: `nf_conntrack` implements [[#Connection Tracking|connection tracking]], `nf_nat` implements [[#Network Address Translation|NAT]], `nf_tables` implements the [[nftables]] rule engine. 
Because they all attach at the same [[#Hooks and Packet Flow|hooks]], the features compose — conntrack runs, then your filtering, then NAT, all on the same packet.

> [!note] The subsystems are kernel modules 
> Netfilter's pieces load on demand: `nf_tables` for the [[nftables]] engine, `nf_conntrack` for [[#Connection Tracking|conntrack]], `nf_nat` for [[#Network Address Translation|NAT]], plus per-protocol helpers. They autoload the first time a rule needs them, so `lsmod | grep -E 'nf_|nft'` is a quick way to see what is currently active.

## Where Netfilter Sits in the Stack

A packet passes through several stages before and after the Netfilter hooks. Knowing the order explains why some tools see a packet before others.

![[netfilter-packet-flow.png]]

On receive:

- the NIC hands the frame to its driver;
- an XDP program, if attached, runs first — in the driver, before the kernel even allocates a socket buffer — making it the earliest and cheapest drop point;
- the frame becomes an `skb` and reaches `tc` ingress (the `clsact` / ingress qdisc), where shaping and eBPF classifiers run;
- Netfilter's [[#Layer 2, ARP and Per-Device Hooks|netdev ingress]] hook fires at this same early stage, before the protocol handler;
- the IP layer takes over and the first IP hook, [[#Prerouting|prerouting]], fires;
- the [[#Packet Traversal|routing decision]] then sends the packet to [[#Input|input]] (local) or [[#Forward|forward]] (transit).

On transmit the order reverses: [[#Output|output]] or [[#Forward|forward]] → [[#Postrouting|postrouting]] → tc egress → netdev egress → driver → wire.

> [!note] Netfilter is not the only hook layer 
> XDP and tc sit below Netfilter and are used mainly for very high-rate drop or for traffic shaping. Netfilter is where stateful filtering and NAT live. See [[#tc and XDP]].

## Kernel Verdicts

At the lowest level a hook function returns one of a small set of verdicts. Frontends like [[nftables]] expose friendlier names, but these are what the kernel acts on.

|Kernel verdict|Meaning|
|---|---|
|`NF_ACCEPT`|let the packet continue to the next stage|
|`NF_DROP`|discard the packet immediately|
|`NF_STOLEN`|a module has taken ownership; stop processing (for example, a fragment held for reassembly)|
|`NF_QUEUE`|hand the packet to userspace (see [[#NFQUEUE]])|
|`NF_REPEAT`|call this hook again|

In [[nftables]] terms, `accept` maps to `NF_ACCEPT`, `drop` to `NF_DROP`, and `queue` to `NF_QUEUE`. The control-flow verdicts `continue`, `return`, `jump` and `goto` are handled inside the rule engine and do not correspond to distinct kernel verdicts; see [[nftables#Verdict Statements]].

---

# Hooks and Packet Flow

_The fixed points where Netfilter intercepts packets, and the order in which they fire._

## IP Hooks

_The five hooks on the IPv4 and IPv6 path, where most firewalling happens._

For IPv4 and IPv6 there are five hooks, named `NF_INET_*`. Every [[nftables#Base Chains|base chain]] attaches to exactly one of them, and the [[nftables#Address Families|family]] you pick decides which hooks are available.

| Hook        | Kernel constant       | Triggered for                                      |
| ----------- | --------------------- | -------------------------------------------------- |
| Prerouting  | `NF_INET_PREROUTING`  | every incoming packet, before the routing decision |
| Input       | `NF_INET_LOCAL_IN`    | packets destined to the local host                 |
| Forward     | `NF_INET_FORWARD`     | packets being routed through the host              |
| Output      | `NF_INET_LOCAL_OUT`   | packets generated locally, leaving the host        |
| Postrouting | `NF_INET_POSTROUTING` | every outgoing packet, after the routing decision  |

![[netfilter-packet-flow-1.png]]
### Prerouting

<mark style="background: #ABF7F7A6;">The first hook every incoming packet hits</mark>, right after basic sanity checks but before the kernel decides where the packet should go. Because it runs before routing, it is the only place you can change a packet's destination and still have it routed accordingly, <mark style="background: #ADCCFFA6;">which is why</mark> [[#DNAT|DNAT]] <mark style="background: #ADCCFFA6;">lives here</mark>.

### Input

Reached only after the routing decision concludes the packet is addressed to this machine. <mark style="background: #D2B3FFA6;">This is where you filter traffic that terminates on the host itself</mark> (SSH to the box, a local web server).

### Forward

Reached when <mark style="background: #CACFD9A6;">routing determines the packet must be passed on to another host</mark>, i.e. <mark style="background: #FFB8EBA6;">the box is acting as a router</mark>. Filtering for traffic passing through belongs here.

> [!warning] IP forwarding must be enabled 
> The Forward hook is only meaningfully traversed when the kernel is allowed to route between interfaces: `net.ipv4.ip_forward = 1` and `net.ipv6.conf.all.forwarding = 1`.

### Output

<mark style="background: #FFB86CA6;">The first hook for packets created by <strong>local processes</strong></mark> (a reply from your web server, a DNS query from the host). <mark style="background: #FFF3A3A6;">It runs</mark> <strong>after</strong> <mark style="background: #BBFABBA6;">an initial routing lookup the kernel needs in order to fill in source address and outgoing interface</mark>.

### Postrouting

<mark style="background: #ABF7F7A6;">The last hook before a packet leaves the machine</mark>, <mark style="background: #ADCCFFA6;">after routing is finalized</mark>. Since the <mark style="background: #D2B3FFA6;">destination is already chosen</mark>, this is where [[#SNAT|SNAT]] and [[#Masquerade|masquerade]] are applied.

## Layer 2, ARP and Per-Device Hooks

_Hooks outside the IP path: bridging, ARP and per-interface._

![[netfilter-packet-flow.png]]

Beyond the IP hooks, <mark style="background: #CACFD9A6;">Netfilter registers hooks at other points</mark>, <mark style="background: #FFB8EBA6;">each surfaced by the matching</mark> [[nftables#Address Families|address family]]:

- <strong>Bridge hooks</strong> (`NF_BR_*`) — the same five names (prerouting, input, forward, output, postrouting) <mark style="background: #FF5582A6;">but on Ethernet frames traversing a software bridge</mark>. Used by the [[nftables#bridge|bridge family]], and historically by <strong>ebtables</strong>.
- <mark style="background: #FFB86CA6;">ARP hooks</mark> (`NF_ARP_*`) — input and output, for ARP packets. Used by the [[nftables#arp|arp family]], historically by arptables.
- <strong>Netdev hooks</strong> (`NF_NETDEV_*`) — <mark style="background: #FFF3A3A6;">bound to a single interface</mark> and<mark style="background: #BBFABBA6;"> firing earlier than the IP hooks</mark>. Ingress has existed since kernel 4.2, egress since 5.16. Used by the [[nftables#netdev (per-interface)|netdev family]].

## Bridged Traffic and br_netfilter

_Making bridged IP packets traverse the IP hooks._

By default <mark style="background: #ABF7F7A6;">a <strong>frame</strong> bridged between ports</mark> is handled only at Layer 2 — <mark style="background: #ADCCFFA6;">it never reaches the</mark> [[#IP Hooks|IP hooks]], so your `ip` / `inet` rules never see it. 

The optional `br_netfilter` module changes that: <mark style="background: #ADCCFFA6;">when loaded, the IP packets carried inside bridged frames are injected into the IP</mark> `PREROUTING`, `FORWARD`, and `POSTROUTING` <mark style="background: #ADCCFFA6;">hooks</mark>, so the same ruleset can filter both <mark style="background: #FF5582A6;">routed</mark> and <mark style="background: #FFB8EBA6;">bridged</mark> traffic. Three <strong>sysctls</strong> gate the behaviour, one per protocol — and they only exist once the module is loaded:

```bash
modprobe br_netfilter
sysctl net.bridge.bridge-nf-call-iptables=1   # bridged IPv4 -> ip/inet hooks
sysctl net.bridge.bridge-nf-call-ip6tables=1  # bridged IPv6 -> ip6/inet hooks
sysctl net.bridge.bridge-nf-call-arptables=1  # bridged ARP  -> arp hooks
```

In practice this means <mark style="background: #D2B3FFA6;">that traffic crossing the bridge is no longer invisible to the firewall</mark>: <mark style="background: #CACFD9A6;">the module unwraps each Ethernet frame</mark> <mark style="background: #FFB8EBA6;">and injects the IP packet inside it</mark> <mark style="background: #FF5582A6;">into the normal IP hook path</mark>, <mark style="background: #FFB86CA6;">where your firewall rules can inspect and act on it just as they would for any routed packet</mark>.

The module works in both directions: it not only pushes bridged IP packets up into the IP hook path, it also lets `ebtables` act on L3 content from the bridge layer, giving you visibility across both L2 and L3 in the same flow.

> [!important] Containers depend on this 
> iptables-based Kubernetes setups require `bridge-nf-call-iptables=1` so that kube-proxy's Service and NAT rules apply to pod traffic crossing the node's [[nftables#bridge|bridge]]. It is a frequent cause of "the rules look right but traffic still isn't filtered or redirected" in bridged and [[#Containers and Namespaces|containerised]] setups. 
> 
> That said, this is not a universal requirement. <strong>eBPF-based CNI plugins</strong> — such as Cilium in full kube-proxy replacement mode — attach directly to the kernel's eBPF hooks and do not rely on iptables at all, so `bridge-nf-call-iptables=1` is unnecessary and can safely remain off.
> 
> Pushing bridged traffic through the full IP stack adds processing overhead on every bridged packet. Enable it where you need unified filtering or container networking demands it; leave it off where you are genuinely only bridging and the extra cost buys you nothing.

## Hook Priorities

_How the kernel orders multiple functions that sit on the same hook._

<mark style="background: #FFF3A3A6;">When several functions register on the same hook they run in ascending integer priority</mark> — <mark style="background: #FFF3A3A6;">lower numbers first, negatives allowed</mark>. <mark style="background: #BBFABBA6;">The kernel relies on this to guarantee ordering</mark>: defragmentation and [[#Connection Tracking|connection tracking]] run before filtering, and source [[#Network Address Translation|NAT]] runs after it.

Some priorities are occupied by built-in stages regardless of what you write:

|Stage|Priority|Runs|
|---|---|---|
|defragmentation|-400|reassembles fragments before anything inspects them|
|connection tracking|-200|classifies the packet's [[#Connection States|
|destination NAT|-100|DNAT, in prerouting / output|
|source NAT|100|SNAT, in postrouting / input|

[[nftables]] gives the common values keyword names (`raw`, `mangle`, `dstnat`, `filter`, `security`, `srcnat`); see [[nftables#Hook and Priority]]. The numbers are defined per family, so the [[nftables#bridge|bridge family]] uses a different scale.

![[netfilter-hook-priority.png]]

## Packet Traversal

_How a packet threads through the hooks, with the routing decision splitting the path._

The single most important fact: the routing decision sends a packet down one of two paths. It is either delivered locally ([[#Input|Input]]) or forwarded ([[#Forward|Forward]]), never both.

![[netfilter-packet-flow-1.png]]

The same three journeys as quick text reference:

```
Forwarded (transit) traffic:
   wire ──▶ PREROUTING ──▶ [route] ──▶ FORWARD ──▶ POSTROUTING ──▶ wire

Inbound to this host:
   wire ──▶ PREROUTING ──▶ [route] ──▶ INPUT ──▶ local socket

Outbound from this host:
   local socket ──▶ [route] ──▶ OUTPUT ──▶ POSTROUTING ──▶ wire
```

NAT positioning falls out of this naturally: change the destination before routing ([[#DNAT|DNAT]] in [[#Prerouting|prerouting]]) and the source after routing ([[#SNAT|SNAT]] in [[#Postrouting|postrouting]]).

# Connection Tracking

_The subsystem that remembers connections, making stateful filtering and NAT possible._

Connection tracking — <strong>conntrack</strong>, the `nf_conntrack` module — <mark style="background: #ABF7F7A6;">records each connection passing through the host</mark> <mark style="background: #ADCCFFA6;">so that later packets can be associated with earlier ones</mark>. <mark style="background: #D2B3FFA6;">It runs early</mark> ([[#Hook Priorities|priority]] -200, before filtering) <mark style="background: #CACFD9A6;">and is the prerequisite for</mark> [[#Network Address Translation|NAT]]. Without it you would have to allow the return traffic of every connection by hand. From [[nftables]] it is read and set through the `ct` expression; see [[nftables#Other Statements]].

## The Conntrack Table

<mark style="background: #CACFD9A6;">A connection is identified by a <strong>tuple</strong></mark> — a fixed set of fields the kernel uses as a unique key to recognize which connection a packet belongs to:

- source and destination IP address
- layer-4 protocol (TCP, UDP, ICMP, …)
- for TCP/UDP: source and destination ports
- for ICMP: type, code, and ID — which take the place of ports

![[netfilter-conntrack-tuple.png]]

<mark style="background: #FFB8EBA6;">For every connection the kernel records <strong>two copies</strong> of this tuple</mark>. 
The <strong>original direction</strong> <mark style="background: #FF5582A6;">is the tuple as the first packet arrived</mark> — the client's address, the server's address, and the ports exactly as seen. 
The <strong>expected reply</strong> <mark style="background: #FFB86CA6;">is the same connection viewed from the other side</mark>: addresses and ports reversed, <mark style="background: #FFF3A3A6;">representing the traffic the server will send back</mark>. 
<mark style="background: #BBFABBA6;">Where NAT is involved, the reply tuple carries the translated addresses</mark> rather than the original ones — <mark style="background: #ABF7F7A6;">that is how the kernel knows how to rewrite return traffic back to the correct sender without you writing an explicit rule for it</mark>. 

These entries are stored in an in-kernel hash table. <mark style="background: #ADCCFFA6;">The size of that table is controlled by two</mark> <strong>tunables</strong> — <mark style="background: #ADCCFFA6;">kernel parameters you can read and write at runtime via</mark> `sysctl` <mark style="background: #ADCCFFA6;">to adjust behavior without recompiling or rebooting</mark>:

- `net.netfilter.nf_conntrack_max` — <mark style="background: #D2B3FFA6;">the maximum number of connections the table can hold at any one time</mark>.
- `net.netfilter.nf_conntrack_buckets` — <mark style="background: #CACFD9A6;">the number of slots in the hash table</mark>; <mark style="background: #FFB8EBA6;">each slot holds a chained list of entries that happen to hash to the same slot</mark>.

The two must be tuned together. The default ratio is one bucket per four entries, so raising `nf_conntrack_max` without also raising `nf_conntrack_buckets` makes the chains longer and slows down lookups under load.

When the table is full the kernel first tries to evict timed-out entries; only if that fails does it drop the incoming packet and log `nf_conntrack: table full, dropping packet`. 
Raising `nf_conntrack_max` on a busy forwarder is a routine fix — but each entry costs roughly 300–400 bytes of kernel memory, so raising it aggressively on a memory-constrained machine can create pressure elsewhere.

## Connection States

Conntrack classifies each packet into a state, matched in [[nftables]] with `ct state`:

|State|Meaning|
|---|---|
|`new`|first packet of a connection that conntrack has not seen before|
|`established`|belongs to a connection already seen in both directions|
|`related`|a new connection logically tied to an existing one (FTP data channel, ICMP errors)|
|`invalid`|cannot be associated with any known connection, or is malformed — usually dropped|
|`untracked`|deliberately excluded from tracking by a `notrack` rule at `raw` (-300) priority|

![[netfilter-conntrack-states.png]]

> [!note] State versus status 
> `ct state` is the value above and is what firewall rules test. Separately, each entry carries internal status flags (`ct status`) such as `confirmed`, `assured`, `snat` and `dnat`, which record how the entry has been processed rather than the packet's filtering state.

## Timeouts and Limits

Every tracked connection has a timeout after which its entry is discarded. The timeouts are per protocol and per state, tunable under `/proc/sys/net/netfilter/`:

- `nf_conntrack_tcp_timeout_established` defaults to 432000 seconds (five days), which is why long-lived idle TCP sessions stay tracked.
- `nf_conntrack_udp_timeout` is short (tens of seconds), since UDP is connectionless.

Shortening the established-TCP timeout is a common way to relieve pressure on a near-full table. For high-rate traffic that needs no stateful handling — authoritative DNS, for instance — exempting it with a `notrack` rule at `raw` priority avoids creating entries at all, sidestepping the pressure rather than tuning around it.

## Helpers and Expectations

Protocols like FTP, SIP and TFTP negotiate a second connection on a dynamically chosen port. A conntrack helper parses the control channel and registers an expectation, so the data connection is recognised as `related` rather than `new`.

> [!warning] Helpers are not automatic on modern kernels 
> Automatic helper assignment was disabled for security (`nf_conntrack_helper = 0`), because blindly parsing payloads is risky. Assign a helper explicitly with a `ct helper` object plus a rule that attaches it to the control traffic; see [[nftables#Connection-Tracking Objects]].

## Conntrack Zones

A conntrack zone partitions the conntrack table within a single host, so that identical tuples in different zones are tracked as distinct flows. This is the tool to reach for when two interfaces carry overlapping address ranges but you do not want the full isolation of a separate [[#Network Namespaces|namespace]]. Zones are set from [[nftables]] with `ct zone set`, early (at `raw` priority) before the entry is confirmed.

## Accounting and Events

- Accounting — enabling `nf_conntrack_acct` attaches per-flow packet and byte counters to every entry, visible in the conntrack listing.
- Events — conntrack emits creation, update and destruction events over nfnetlink. The `conntrackd` daemon consumes these to replicate state between firewalls, allowing stateful failover in an active-standby pair.

## Flow Offload

Once a forwarded connection is [[#Connection States|established]], its packets are predictable, so the kernel can shortcut them. A flow added to a flowtable takes a fast path that bypasses the normal hook traversal, sharply increasing routing and NAT throughput; with capable hardware the flow can be offloaded to the NIC entirely. Only forwarded, established traffic qualifies — the first packets still take the slow path so that policy is applied. The flowtable itself is defined in [[nftables]]; see [[nftables#Flowtables]].

## Inspecting Conntrack

The conntrack-tools package (see [[#conntrack-tools]]) provides the `conntrack` command, and the table is also exposed at `/proc/net/nf_conntrack`.

```bash
conntrack -L                 # list all tracked connections
conntrack -L -p tcp --dport 443   # filter the listing
conntrack -E                 # watch creation/destruction events live
conntrack -C                 # count current entries
conntrack -D -s 10.0.0.5     # delete entries from a source
conntrack -F                 # flush the whole table
```

# Network Address Translation

_Rewriting source or destination addresses and ports, layered on conntrack._

## How NAT Uses Conntrack

NAT is not a separate packet-mangling pass on every packet. The translation is decided once, on the first packet of a flow, and recorded in that flow's [[#Connection Tracking|conntrack]] entry; the kernel then applies it to every subsequent packet in both directions automatically. This is why a [[nftables#Chain Types|nat-type]] chain only ever sees the first packet of a connection, and why NAT requires conntrack to be active. IPv6, by contrast, is normally routed end to end without NAT at all; see [[#No NAT by Default]].

![[netfilter-conntrack-nat.png]]

## DNAT

Destination NAT is the mechanism behind <strong>port forwarding</strong> and publishing an internal server: it rewrites the destination address, and optionally the port, to a target you name explicitly in the rule (`dnat to 192.168.1.10:443`) — the kernel does not infer the real server, you specify it. 

The rule runs at [[#Prerouting|prerouting]] (or [[#Output|output]] for locally generated traffic) at `dstnat` priority, before the [[#Packet Traversal|routing decision]], and that ordering is the whole point: with the destination already changed, the routing lookup sees the internal address and forwards the packet to the real server instead of delivering it locally to the gateway. 

The first packet also creates the [[#Connection Tracking|conntrack]] entry, whose reply tuple takes the new destination as its source; from then on the stored entry does the translating, not the rule.

The reply is un-translated automatically: a returning packet matches that reply tuple, so the kernel rewrites its source back to the address the client first contacted, with no second rule. This holds only if replies come back through the same box — if the internal server has its own route to the client and answers directly, the reply never meets the conntrack entry and the client discards it, the classic reason a port forward appears to "half work".

## SNAT

Source NAT rewrites the source address, so it must run in [[#Postrouting|postrouting]], after routing has chosen the outgoing interface. It is how many private hosts share one public address.

## Masquerade

Masquerade is a dynamic form of [[#SNAT|SNAT]]: instead of a fixed source written into the rule, it rewrites the source to the address currently configured on the outgoing interface, looked up when the flow's first packet is translated. 

That makes it the right choice for an uplink whose address comes from DHCP or PPP and is not known when the ruleset is written — `oifname "eth0" masquerade` keeps working across address changes, where a static `snat to` would have to be rewritten each time.

The convenience has two costs. It does the interface-address lookup per new connection rather than using a constant, so it is marginally more work than static [[#SNAT|SNAT]]. More importantly, it hooks interface state: when the outgoing interface goes down, the kernel flushes the [[#Connection Tracking|conntrack]] entries that were masqueraded through it, so flows over a link that drops are cleared instead of lingering against an address that may have changed on the way back up. On a stable uplink with a known fixed address, plain SNAT is slightly cheaper and equally correct.

## Redirect

Redirect is a special [[#DNAT|DNAT]] that sends the packet to the local machine itself (the address of the interface it arrived on). It is the usual way to transparently divert traffic into a local proxy. When the proxy needs to see the original destination rather than the rewritten local one, use [[#Transparent Proxying (TPROXY)|TPROXY]] instead, which delivers to a local socket without translating the address.

## Hairpin NAT

When a host on the inside reaches another inside host through the firewall's public address, the packet needs both [[#DNAT|DNAT]] (to reach the real server) and [[#SNAT|SNAT]] (so the server replies back through the firewall rather than directly). This combination is called hairpin NAT or NAT reflection, and forgetting the SNAT half is a classic cause of "works from outside, fails from inside".

The [[nftables]] statements that perform these operations (`dnat`, `snat`, `masquerade`, `redirect`) are covered in [[nftables#Other Statements]].

# Packet Mangling and Marking

_Rewriting and tagging packets in flight, and steering routing with the result._

Beyond filtering and NAT, Netfilter can modify packets and attach metadata to them as they pass a hook, most of it around the `mangle` [[#Hook Priorities|priority]] (-150). The changes fall into two groups: marks, which are invisible tags read by other kernel subsystems, and field rewrites, which alter the packet itself.

## Packet and Connection Marks

Two distinct marks exist:

- The packet mark (also called <strong>fwmark</strong> or <strong>nfmark</strong>) is a 32-bit value attached to a packet for the duration of its trip through the kernel. It is never transmitted; it lives only in memory and is read by routing and <strong>tc</strong>.
- The connection mark (<strong>ctmark</strong>) is stored on the [[#Connection Tracking|conntrack]] entry, so it persists for the whole connection, across every packet in both directions.

Both are set from [[nftables]] with `meta mark set` and `ct mark set` (see [[nftables#Other Statements]]). The usual idiom is to decide once and remember it: on the first packet, compute a packet mark and copy it to the connection mark; on every later packet, copy the connection mark back to the packet mark so the whole flow is treated consistently.

```bash
ct mark set 0x1            # first packet of a flow: tag the connection
meta mark set ct mark      # every packet: restore the packet mark from the connection
```

## Marks and Policy Routing

The packet mark is the bridge between the firewall and policy routing. The routing subsystem can choose a routing table based on the mark, which is how multi-WAN, <strong>VPN split-tunnelling</strong> and source-based routing are built: nftables sets the mark, `ip rule` matches it.

```bash
ip rule add fwmark 0x1 table 100        # marked packets consult table 100
ip route add default via 203.0.113.1 table 100
```

The same mark can drive <strong>tc</strong>, which classifies packets into shaping queues by <strong>fwmark</strong> — so a single mark set in the firewall can steer both which link a packet leaves by and how it is queued.

## Transparent Proxying (TPROXY)

_Diverting traffic to a local proxy without rewriting its destination._

<mark style="background: #FFB8EBA6;">A transparent proxy</mark> — or a service-mesh sidecar such as Envoy — <mark style="background: #FFB8EBA6;">must receive connections</mark> <mark style="background: #FF5582A6;">that were aimed at some other host</mark> <mark style="background: #FFB8EBA6;">while still seeing the original destination</mark>, <mark style="background: #FFB86CA6;">so it can relay them upstream</mark>. A plain [[#Redirect|redirect]] cannot do this: being a DNAT, it overwrites the destination with the local address, and the proxy can only partially recover it (IPv4 TCP only, via `SO_ORIGINAL_DST`).

<strong>TPROXY</strong> instead <mark style="background: #FFF3A3A6;">delivers the packet to a local socket</mark> <mark style="background: #BBFABBA6;">while leaving its destination address untouched</mark>, and it works for TCP and UDP over both IPv4 and IPv6. <mark style="background: #ADCCFFA6;">It runs in a</mark> [[#Prerouting|prerouting]] <mark style="background: #ADCCFFA6;">chain</mark> and <mark style="background: #D2B3FFA6;">is built directly on the</mark> [[#Packet and Connection Marks|marks]] and [[#Marks and Policy Routing|policy routing]] <mark style="background: #D2B3FFA6;">above</mark> — three pieces have to line up:

1. The proxy opens its listening socket with the `IP_TRANSPARENT` option, so it may bind foreign addresses and accept redirected traffic.
2. A prerouting rule matches the traffic, marks it, and hands it to the proxy's port with `tproxy`.
3. A policy-routing rule sends marked packets to the loopback, so the local transparent socket receives them.

```bash
table ip mangle {
    chain prerouting {
        type filter hook prerouting priority mangle; policy accept;
        # keep packets of already-established proxied flows going to the socket
        meta l4proto tcp socket transparent 1 meta mark set 1 accept
        # divert new web traffic to the proxy on port 50080, marking it
        tcp dport { 80, 443 } tproxy to :50080 meta mark set 1
    }
}
```

```bash
# route marked packets to the local transparent socket via loopback
ip rule add fwmark 1 lookup 100
ip route add local 0.0.0.0/0 dev lo table 100
# the IPv6 equivalents, since TPROXY handles both families
ip -6 rule add fwmark 1 lookup 100
ip -6 route add local ::/0 dev lo table 100
```

Because it only attaches at prerouting, TPROXY acts on traffic the host forwards or terminates locally; it is the mechanism behind transparent proxies such as Squid, and one of the interception modes a [[#Containers and Namespaces|service-mesh]] sidecar can use in place of redirect-based capture.

## Rewriting Header Fields

Netfilter can also overwrite selected header fields in flight: normalizing the DSCP / TOS bits for QoS, or adjusting the IPv4 TTL and IPv6 hop limit. These are ordinary statements applied at a hook, and the rewritten value (DSCP, for example) survives onto the wire to be honored by downstream routers.

## MSS Clamping

On links with a reduced MTU — PPPoE, GRE, IPsec and other tunnels — large TCP segments carrying the <strong>Don't-Fragment</strong> bit can be silently dropped when Path MTU Discovery is broken, giving the classic "small requests work, large transfers hang" symptom. MSS clamping fixes this by rewriting the TCP maximum-segment-size option on SYN packets as they are forwarded, so both endpoints agree on a segment size that fits. It is applied to SYNs in the [[#Forward|forward]] path:

```bash
# clamp the MSS of forwarded SYNs down to the path MTU
nft add rule inet filter forward tcp flags syn tcp option maxseg size set rt mtu
```

# IPv6 and Netfilter

_The things that differ enough to break an IPv4 ruleset ported as-is._

IPv6 uses the very same [[#Hooks and Packet Flow|hooks]], families (`ip6`, or `inet` for dual-stack) and [[#Connection Tracking|conntrack]] as IPv4, so stateful filtering works identically. What trips people up is what is different: ICMPv6 cannot be filtered away, there is normally no [[#Network Address Translation|NAT]], and anti-spoofing is done differently.

## ICMPv6 Is Mandatory

Where ICMPv4 can be blocked with little consequence, large parts of IPv6 ride on ICMPv6 and stop working if it is dropped:

- Neighbor Discovery (NDP) replaces ARP. Neighbor Solicitation and Advertisement resolve link-layer addresses, while Router Solicitation and Advertisement drive prefix discovery and SLAAC. These use link-local (`fe80::/10`) addresses; block them and the host cannot resolve neighbors or autoconfigure.
- Path MTU Discovery depends on the ICMPv6 "packet too big" message. IPv6 routers never fragment, so a source learns the path limit only from these — drop them and large transfers black-hole exactly as with broken [[#MSS Clamping|MSS clamping]].

An input chain must therefore accept the essential ICMPv6 types:

```bash
nft add rule inet filter input icmpv6 type { \
    destination-unreachable, packet-too-big, time-exceeded, parameter-problem, \
    echo-request, nd-neighbor-solicit, nd-neighbor-advert, nd-router-advert } accept
```

> [!note] Harden Neighbor Discovery with the hop limit Genuine ND messages always arrive with a hop limit of 255 — routers decrement it, so a value of 255 proves the packet was not forwarded. Matching `ip6 hoplimit 255` on the ND types rejects spoofed Neighbor Discovery injected from off-link.

## No NAT by Default

IPv6 hands every host a globally routable address and routes traffic end to end; NAT66 and NPTv6 exist but are discouraged and rarely needed. This flips the security model. With IPv4 behind [[#Masquerade|masquerade]], unsolicited inbound traffic is blocked almost by accident, because no NAT mapping exists for it. IPv6 has no such accident, so every host is potentially reachable from the internet and inbound protection becomes entirely the job of the [[#Forward|forward]] chain. A default-drop forward policy that accepts only `established,related` plus the services you intend to expose is essential here, not optional.

## Anti-Spoofing with fib

The [[#Reverse Path Filtering|rp_filter]] sysctl is IPv4-only, so it does nothing for IPv6. The portable replacement — and the only reverse-path option for IPv6 — is the [[nftables#Match Statements|fib expression]], which asks the routing table whether a packet's source is reachable back through the interface it arrived on:

```bash
nft add rule inet filter prerouting fib saddr . iif oif missing drop
```

Because `fib` works for any family, it is worth using in place of `rp_filter` even on dual-stack hosts, so both protocols are covered by a single rule.

## Extension Headers and Fragments

IPv6 replaces the IPv4 options field with a chain of extension headers (Hop-by-Hop, Routing, Fragment, Destination). The real upper-layer protocol sits after them, so match it with `meta l4proto`, which walks the chain, rather than assuming a fixed offset. Fragmentation is carried in a Fragment extension header and is reassembled by [[#Connection Tracking|conntrack]] before inspection, just as in IPv4. Some extension headers are abused — the Type 0 Routing Header (RH0) enabled traffic amplification and is dropped by modern kernels — so dropping unwanted extension headers explicitly is a reasonable hardening step.

# Network Namespaces

_Every Netfilter ruleset, set of hooks and conntrack table exists once per network namespace._

A <strong>network namespace</strong> <mark style="background: #FFB8EBA6;">partitions</mark> <mark style="background: #FF5582A6;">the entire network stack</mark> — <mark style="background: #FFB86CA6;">interfaces, routing tables, the ARP and [[#Connection Tracking|conntrack]] tables, and the full [[nftables]] ruleset are all private to it</mark>. <mark style="background: #FFF3A3A6;">The machine boots with one initial namespace (the host)</mark>, and <mark style="background: #BBFABBA6;">further namespaces can be created on demand; each container normally gets its own</mark>. <mark style="background: #ABF7F7A6;">Nothing in Netfilter is global</mark>: the [[#Hooks and Packet Flow|hooks]], their [[#Hook Priorities|priorities]], and the conntrack state table <mark style="background: #ADCCFFA6;">all exist once per namespace, fully independent of every other namespace's copy</mark>.

The practical consequences:

- <mark style="background: #D2B3FFA6;">Rules are not shared</mark>. A ruleset loaded in the host has no effect inside a container, and the reverse is equally true.
- <mark style="background: #D2B3FFA6;">A flow is tracked separately in each namespace it passes through</mark>, so the same connection can be `established` on one side of a link and `new` on the other.
- A [[nftables#netdev (per-interface)|netdev]] chain follows its device: an interface lives in exactly one namespace at a time, so the chain only sees traffic while that interface sits in the same namespace.

<mark style="background: #CACFD9A6;">Namespaces do not share a packet path</mark>. Traffic crosses between them only over a link that spans the boundary — typically a <strong>veth pair</strong> with one end in each namespace, or a physical interface moved across — and each side runs its own hooks and rules on the packet independently as it arrives. If you only need conntrack separation without full isolation, a [[#Conntrack Zones|conntrack zone]] is the lighter option.

## Working Across Namespaces

A namespace is created by `clone(CLONE_NEWNET)`; in practice you make one with `ip netns` or `unshare`, and any `nft`, `conntrack` or `ip` command then acts on the namespace of the process that runs it.

```bash
ip netns list                                   # namespaces created with `ip netns`
lsns -t net                                      # every net namespace, including containers'
ip netns add testns                             # create a named namespace
unshare --net bash                              # spawn a shell in a fresh namespace
ip netns exec testns nft list ruleset           # run nft inside a named namespace
nsenter -t <pid> -n nft list ruleset            # enter the namespace of a running process
```

> [!note] `ip netns` only sees named namespaces 
> `ip netns list` shows namespaces registered under `/run/netns` — those created with `ip netns add`. Container runtimes usually create anonymous namespaces that are not registered there, so they will not appear. Use `lsns -t net` to enumerate every network namespace on the host, and reach a container's namespace through a process inside it with `nsenter -t <pid> -n …`.

## Containers and Namespaces

<mark style="background: #FFB8EBA6;">A container runtime</mark> — Docker, Podman, Kubernetes — <mark style="background: #FFB8EBA6;">gives each container its own namespace and links it to the host with a <strong>veth pair</strong></mark>, <mark style="background: #FF5582A6;">usually attached to a [[nftables#bridge|bridge]] such as `docker0` that lives in the host namespace</mark>. <mark style="background: #FFB86CA6;">The rules that publish ports and masquerade outbound traffic</mark> ([[#DNAT|DNAT]] and [[#Masquerade|masquerade]]) <mark style="background: #FFB86CA6;">are written into the host namespace by the runtime</mark>, <mark style="background: #FFF3A3A6;">while the container's own namespace typically starts almost empty</mark>.

When container connectivity misbehaves, check both sides: the host ruleset for the runtime's [[#Network Address Translation|NAT]] and forward rules, and the container's namespace (reached with `nsenter`) for anything the workload loaded itself. <mark style="background: #BBFABBA6;">Rules you load inside a container's namespace also vanish when the container is recreated</mark>, unless the image or an init step reloads them. <mark style="background: #ABF7F7A6;">And because containers are usually attached through a bridge, bridged IP traffic only reaches your `ip` / `inet` rules when [[#Bridged Traffic and br_netfilter|br_netfilter]] is enabled</mark>.

# Logging, Queueing and Accounting

_Side-channel subsystems for observing, diverting and metering packets._

## Kernel Logging

Netfilter can log packet metadata in two ways:

- Kernel log — the classic path, writing a line per packet to the kernel ring buffer (`dmesg`, then syslog/journald). Simple, but high volume floods the log.
- NFLOG (`nfnetlink_log`) — packets are sent to a numbered netlink group and read by a userspace daemon, typically `ulogd2`, which can write structured logs, pcap files or database records. This is the right path for sustained or detailed logging.

From [[nftables]] the `log` statement selects between them (a plain `log`, or `log group N` for NFLOG); see [[nftables#Other Statements]].

> [!warning] Rate-limit logging 
> A `log` rule on a busy path can flood the kernel log and crowd out everything else. Pair it with a rate limit (a `limit` statement in [[nftables]]) so only a sample of matching packets is recorded.

## NFQUEUE

NFQUEUE hands a packet to a userspace program over `libnetfilter_queue`; the program inspects it and returns a verdict, so the packet's fate is decided outside the kernel. This is how inline intrusion-prevention systems such as Suricata operate. In [[nftables]] it is the `queue` [[nftables#Verdict Statements|verdict]], which corresponds to the kernel's `NF_QUEUE`.

## Counters and Quotas

Netfilter can attach counters (packets and bytes) and quotas (a one-shot byte threshold) to rules, providing per-rule accounting and usage caps. In [[nftables]] these are the `counter` and `quota` objects and statements; see [[nftables#Counters and Quotas]].

# Troubleshooting and Observability

_A practical path for working out why a packet is, or isn't, getting through._

## Tracing a Dropped Packet

When traffic is being dropped and the cause is not obvious, work through the layers rather than guessing:

- Confirm the rule is even consulted — attach a [[#Counters and Quotas|counter]] to the suspect rule and watch whether it increments.
- See the drop happen — add a temporary `log` rule just before the drop so the packet appears in the kernel log (`dmesg -w`), then remove it. In [[nftables]] you can instead tag packets with `meta nftrace set 1` and watch `nft monitor trace`.
- Check connection state — `conntrack -E` (see [[#Inspecting Conntrack]]) shows flows being created and torn down live; an unexpected `invalid` or a missing reply points at asymmetric routing or NAT.
- Check the right namespace — a ruleset only governs the [[#Network Namespaces|namespace]] it was loaded in; for a container, inspect both the host and the container's namespace.
- For bridged or container traffic — verify [[#Bridged Traffic and br_netfilter|br_netfilter]] is on if IP rules seem to be ignored.
- For stalled large transfers over a tunnel — suspect MTU and check [[#MSS Clamping|MSS clamping]].
- For a busy forwarder dropping connections — check whether the [[#The Conntrack Table|conntrack table]] is full (`dmesg` will say so) and raise `nf_conntrack_max`.

## Reverse Path Filtering

Reverse path filtering is a kernel anti-spoofing check that lives in the IP input path, not in a Netfilter hook, but it is a frequent culprit when packets vanish before any rule sees them. It drops an incoming packet if the route back to its source does not point out the interface the packet arrived on. It is set per interface, and the effective value is the larger of the per-interface setting and `net.ipv4.conf.all.rp_filter`:

- `1` — strict mode: the reply route must use the same interface.
- `2` — loose mode: the source need only be routable out of some interface.
- `0` — off.

On hosts with asymmetric or multi-homed routing, strict mode silently drops legitimate traffic; loose mode, or turning it off, is the usual fix. Note that `rp_filter` is IPv4-only; for IPv6, and portably for both families, use the `fib` expression instead — see [[#Anti-Spoofing with fib]].

## Mitigating Floods

For internet-facing services, two Netfilter features blunt common floods. A [[#Connection Tracking|conntrack]]-based limit (`ct count` in [[nftables]]) caps concurrent connections per source. For SYN floods specifically, synproxy answers the handshake with SYN cookies and only creates a conntrack entry once a connection is proven real, keeping spoofed SYNs out of the state table entirely.

# Frontends and Related Tools

_The userspace tools that program Netfilter, and the neighbouring subsystems._

## nftables

The modern, recommended frontend: one tool (`nft`) and one in-kernel engine (`nf_tables`) covering IPv4, IPv6, ARP and bridging. It replaces the entire iptables family. The companion note [[nftables]] documents its object model, syntax and operation in full.

## iptables and Its Variants

The original frontend, still widespread. Two implementations coexist behind the same command name:

- `iptables-legacy` drives the old `x_tables` kernel API directly.
- `iptables-nft` accepts iptables syntax but writes [[nftables]] rules underneath, so legacy scripts run on the modern engine. Most current distributions ship this as the default `iptables`.

Mixing legacy `iptables` and `nft` rules on the same host is error-prone because they can attach at the same hooks without being aware of each other; prefer one engine. Migration is covered in [[nftables#Migrating from iptables]].

## ebtables, arptables and ipset

- ebtables filtered bridged Ethernet frames; its job is now the [[nftables#bridge|bridge family]].
- arptables filtered ARP; its job is now the [[nftables#arp|arp family]].
- ipset stored large IP/port sets for fast matching from iptables. [[nftables]] has native [[nftables#Sets|sets]], so ipset is largely unnecessary in a pure-nftables setup.

## conntrack-tools

The userspace counterpart to [[#Connection Tracking|conntrack]]: the `conntrack` command inspects, edits and flushes the table (see [[#Inspecting Conntrack]]), and `conntrackd` replicates conntrack state between hosts for stateful firewall failover.

## tc and XDP

Adjacent kernel facilities that sit below Netfilter on the packet path (see [[#Where Netfilter Sits in the Stack]]):

- tc (traffic control) handles queueing, shaping and policing, and can run eBPF classifiers at the `clsact` ingress/egress hooks. It is about bandwidth and latency, not stateful filtering.
- XDP runs an eBPF program in the driver before an `skb` exists, giving the fastest possible drop or redirect — used for DDoS mitigation and load balancing, but with no access to conntrack or the rest of the Netfilter machinery.