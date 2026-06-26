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

![[nf-hooks.png]]

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

The optional `br_netfilter` module changes that: <mark style="background: #ADCCFFA6;">when loaded, the IP packets carried inside bridged frames are injected into the IP</mark> `PREROUTING`, `FORWARD`, and `POSTROUTING` <mark style="background: #ADCCFFA6;">hooks</mark>, so the same ruleset can filter both <mark style="background: #FF5582A6;">routed</mark> and <mark style="background: #FFB8EBA6;">bridged</mark> traffic. Three <strong>sysctls</strong> gate the behavior, one per protocol — and they only exist once the module is loaded:

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

![[nf-hooks.png]]

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

### Forwarded Packet Path

Complete traversal of an <strong>incoming forwarded IPv4 packet</strong> through all tables and subsystems:

```
NIC receives packet
        │
        ▼
NF_INET_PRE_ROUTING
  ├── raw::PREROUTING       (−300)   NOTRACK / CT helper assignment
  ├── nf_conntrack          (−200)   tuple lookup / new entry creation
  ├── mangle::PREROUTING    (−150)   TOS, TTL, MARK modification
  └── nat::PREROUTING       (−100)   DNAT / port forwarding
        │
   Routing decision
        │
        ▼ (forward)
NF_INET_FORWARD
  ├── mangle::FORWARD       (−150)
  ├── filter::FORWARD       (   0)   ← main forwarding filter
  └── security::FORWARD     (  50)
        │
        ▼
NF_INET_POST_ROUTING
  ├── mangle::POSTROUTING   (−150)
  ├── nat::POSTROUTING      ( 100)   SNAT / Masquerade
  └── conntrack confirm     (INT_MAX) insert entry into hash table
        │
        ▼
     NIC transmit
```

### Locally Generated Packet Path

```
Socket write()
        │
        ▼
NF_INET_LOCAL_OUT
  ├── raw::OUTPUT           (−300)
  ├── nf_conntrack          (−200)
  ├── mangle::OUTPUT        (−150)
  ├── nat::OUTPUT           (−100)   DNAT for locally-generated traffic
  └── filter::OUTPUT        (   0)
        │
   Routing decision
        │
        ▼
NF_INET_POST_ROUTING
  ├── mangle::POSTROUTING   (−150)
  ├── nat::POSTROUTING      ( 100)   SNAT
  └── conntrack confirm     (INT_MAX)
        │
        ▼
     NIC transmit
```

### Incoming-to-Local Packet Path

```
NF_INET_PRE_ROUTING        (same pipeline as forwarded path)
        │
   Routing decision → local process
        │
        ▼
NF_INET_LOCAL_IN
  ├── mangle::INPUT         (−150)
  ├── filter::INPUT         (   0)   ← main input filter
  ├── security::INPUT       (  50)
  └── conntrack confirm     (INT_MAX)
        │
        ▼
   Local socket
```

### Bridge Packet Traversal

Without [[#Bridged Traffic and br_netfilter|br_netfilter,]] bridged frames stay entirely within ebtables hooks and never reach iptables or conntrack. With `br_netfilter` loaded, bridged IP frames additionally traverse the INET hooks:

```
Frame arrives on bridge port
        │
        ▼
NF_BR_PRE_ROUTING                ← ebtables PREROUTING (L2 filtering)
        │
   Forwarding decision (MAC table)
        │
        ├─── destined for bridge IP ──────────────┐
        │                                          │
        ▼ (forward to another port)                ▼
  [br_netfilter injects into INET hooks:]   NF_BR_LOCAL_IN
  NF_INET_PRE_ROUTING  ← conntrack, DNAT          │
  NF_INET_FORWARD      ← iptables/nftables         ▼
  NF_INET_POST_ROUTING ← SNAT                Bridge IP stack
        │
        ▼
NF_BR_POST_ROUTING               ← ebtables POSTROUTING
        │
        ▼
Frame exits bridge port
```

> [!warning] Double-processing 
> With `br_netfilter`, the same IP packet passes through both `ebtables` (L2) and `iptables`/`nftables` (L3) hooks. Traffic that crosses a bridge and is then routed (common on Docker hosts) can trigger conntrack twice, causing INVALID states or double-NAT. Use conntrack zones to isolate bridge and routing domains. 

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

NAT is not a separate packet-mangling pass on every packet. <mark style="background: #FFB8EBA6;">The translation is decided once</mark>, <mark style="background: #FF5582A6;">on the first packet of a flow</mark>, <mark style="background: #FFB86CA6;">and recorded in that flow's [[#Connection Tracking|conntrack]] entry</mark>; <mark style="background: #FFF3A3A6;">the kernel then applies it to every subsequent packet in both directions automatically</mark>. This is why a [[nftables#Chain Types|nat-type]] chain only ever sees the first packet of a connection, and why NAT requires conntrack to be active. IPv6, by contrast, is normally routed end to end without NAT at all; see [[#No NAT by Default]].

![[netfilter-conntrack-nat.png]]

## DNAT

Destination NAT is the mechanism behind <strong>port forwarding</strong> and publishing an internal server: <mark style="background: #FFB8EBA6;">it rewrites the destination address</mark>, and optionally the port, <mark style="background: #FF5582A6;">to a target you name explicitly in the rule</mark> (`dnat to 192.168.1.10:443`) — the kernel does not infer the real server, you specify it. 

<mark style="background: #FFB86CA6;">The rule runs at [[#Prerouting|prerouting]] (or [[#Output|output]] for locally generated traffic) at `dstnat` priority</mark>, before the [[#Packet Traversal|routing decision]], and that ordering is the whole point: with the destination already changed, the routing lookup sees the internal address and forwards the packet to the real server instead of delivering it locally to the gateway. 

<mark style="background: #FFF3A3A6;">The first packet also creates the [[#Connection Tracking|conntrack]] entry</mark>, whose <strong>reply tuple</strong> takes the <mark style="background: #BBFABBA6;">new destination</mark> as its source; <mark style="background: #ABF7F7A6;">from then on <strong>the stored entry</strong> does the translating</mark>, not the rule.

<mark style="background: #ADCCFFA6;">The <strong>reply</strong> is un-translated automatically</mark>: <mark style="background: #D2B3FFA6;">a returning packet matches that <strong>reply tuple</strong></mark>, so <mark style="background: #CACFD9A6;">the kernel rewrites its source back to the address the client first contacted</mark>, with no second rule. This holds only <mark style="background: #FFB8EBA6;">if replies come back through the same box</mark> — if the internal server has its own route to the client and answers directly, the reply never meets the conntrack entry and the client discards it, the classic reason a port forward appears to "half work".

### Port Forwarding

To publish an internal web server at `192.168.1.10:443` on the firewall's public `203.0.113.7:443`:

1. Enable forwarding, since the firewall must route the packet onward rather than deliver it locally: `net.ipv4.ip_forward = 1` (and `net.ipv6.conf.all.forwarding = 1` for IPv6).
2. Add the DNAT rule in a [[nftables#Chain Types|nat-type]] chain on [[#Prerouting|prerouting]], so it runs before routing: `iifname "eth0" tcp dport 443 dnat to 192.168.1.10:443`. This is the only rule that names the target; the public address is just the one clients reach the firewall on.
3. On the first packet the destination becomes `192.168.1.10:443`, so the [[#Packet Traversal|routing decision]] forwards it toward the LAN instead of delivering it to the firewall, and [[#Connection Tracking|conntrack]] records the flow with the reply tuple's source set to `192.168.1.10:443`.
4. Permit the forwarded traffic in the filter `forward` chain when its policy is drop, matching the post-DNAT destination: `ip daddr 192.168.1.10 tcp dport 443 ct state new accept`. Return traffic is already handled by the usual `ct state established,related accept`.
5. The server replies from `192.168.1.10:443`; that reply matches the stored reply tuple, so the kernel restores the source to `203.0.113.7:443` on its own — no return rule — and the client sees the answer from the address it contacted.
6. If inside hosts must also reach the service through the public address, add the [[#Hairpin NAT|hairpin]] SNAT. Confirm the live mapping at any time with `conntrack -L`.

The complete, copy-ready ruleset is the [[nftables#Port Forwarding|port-forwarding recipe]] in the nftables note.

## SNAT

Source NAT rewrites the source address, so it must run in [[#Postrouting|postrouting]], after routing has chosen the outgoing interface. It is how many private hosts share one public address.

## Masquerade

<mark style="background: #FFB8EBA6;">Masquerade is a dynamic form of [[#SNAT|SNAT]]</mark>. Rather than <strong>a fixed source</strong> <mark style="background: #FFF3A3A6;">written into the rule</mark>, <mark style="background: #FF5582A6;">it rewrites the source to whatever address is</mark> <mark style="background: #FFB86CA6;">on the outgoing interface</mark> when the flow's first packet is translated — so `oifname "eth0" masquerade` is the natural choice for an uplink addressed by DHCP or PPP, following the interface across address changes where a static `snat to` would be wrong until rewritten.

![[netfilter-masquerade.png]]

That dynamism carries two consequences. <mark style="background: #FFF3A3A6;">It costs a per-connection lookup of the interface address instead of reusing a constant</mark>, so it is marginally heavier than static [[#SNAT|SNAT]]. And it is tied to interface state: <mark style="background: #BBFABBA6;">when the outgoing interface goes down</mark>, <mark style="background: #ABF7F7A6;">the kernel flushes the [[#Connection Tracking|conntrack]] entries masqueraded through it</mark>, <mark style="background: #ADCCFFA6;">clearing flows over a dropped link</mark> rather than leaving them stranded against an address that may differ when the link returns. On a stable uplink with a fixed address, plain SNAT is slightly cheaper and just as correct.

## Redirect

Redirect is [[#DNAT|DNAT]] <mark style="background: #FFB8EBA6;">aimed at the local host</mark>: <mark style="background: #FF5582A6;">it rewrites the destination</mark> <mark style="background: #FFB86CA6;">to the primary address of the interface the packet arrived on</mark>, <mark style="background: #FFF3A3A6;">keeping the original port or taking one you give it</mark> (`redirect to :3128`). 

Running at [[#Prerouting|prerouting]] like any DNAT, it is the standard way <mark style="background: #BBFABBA6;">to pull traffic into a local proxy</mark> — for instance sending outbound port 80 to a Squid listening on 3128 — and the reply is un-translated automatically.

Its limitation is that the proxy now sees a connection addressed to the local machine, so the original destination is gone from the packet; the proxy has to recover it from conntrack via the `SO_ORIGINAL_DST` socket option. 

When the original destination must stay on the packet, or the host needs to intercept traffic that is merely passing through rather than addressed to it, use [[#Transparent Proxying (TPROXY)|TPROXY]] instead, which delivers to a local socket without translating the address.

## Hairpin NAT

<mark style="background: #FFB8EBA6;">When an inside host reaches another inside host through the firewall's public address</mark>, the traffic "hairpins" — in and back out the same interface — <mark style="background: #FF5582A6;">and needs two translations, not one</mark>. [[#DNAT|DNAT]] <mark style="background: #FFB86CA6;">sends the request on to the real server as usual</mark>, <mark style="background: #FFF3A3A6;">but on its own</mark> <mark style="background: #BBFABBA6;">it leaves the server seeing the original inside client as the source</mark>. <mark style="background: #ABF7F7A6;">Because the two share a subnet, the server then replies straight to the client</mark>; <mark style="background: #ADCCFFA6;">the client, which addressed its request to the public IP</mark>, <mark style="background: #D2B3FFA6;">gets a reply from an unexpected private address and discards it</mark>.

<mark style="background: #CACFD9A6;">Adding [[#SNAT|SNAT]] (or [[#Masquerade|masquerade]]) on that path fixes it by rewriting the source to the firewall's inside address</mark>, <mark style="background: #FFB8EBA6;">so the server replies to the firewall, which reverses both translations and returns the packet from the public address the client expects</mark>. This combination is hairpin NAT, or NAT reflection; forgetting the SNAT half is the classic cause of "works from outside, fails from inside".

The [[nftables]] statements that perform these operations (`dnat`, `snat`, `masquerade`, `redirect`) are covered in [[nftables#Other Statements]].

# Packet Mangling and Marking

_Rewriting and tagging packets in flight, and steering routing with the result._

Beyond filtering and NAT, Netfilter can modify packets and attach metadata to them as they pass a hook, most of it around the `mangle` [[#Hook Priorities|priority]] (-150). The changes fall into two groups: marks, which are invisible tags read by other kernel subsystems, and field rewrites, which alter the packet itself.

## Packet and Connection Marks

A <strong>mark</strong> is a <mark style="background: #FFB8EBA6;">32-bit integer</mark> <mark style="background: #FF5582A6;">the kernel attaches to a packet</mark> or <mark style="background: #FF5582A6;">a connection</mark> and <mark style="background: #FFB86CA6;">reads internally to make decisions</mark>; <mark style="background: #FFF3A3A6;">it is never written into a header or sent on the wire</mark>. <mark style="background: #BBFABBA6;">Two separate marks exist, and what distinguishes them is how long they live</mark>.

The <strong>packet mark</strong> <mark style="background: #ABF7F7A6;">is a field on the in-kernel packet buffer</mark> (`skb->mark`), and <mark style="background: #ADCCFFA6;">it exists only for that single packet's journey through the stack</mark> — <mark style="background: #D2B3FFA6;">once the packet is transmitted or dropped the value is gone</mark>, and the matching reply arrives carrying its own mark of zero. The names <strong>fwmark</strong> and <strong>nfmark</strong> <mark style="background: #CACFD9A6;">are two labels for this same field</mark>, inherited from two different worlds: <strong>nfmark</strong> is netfilter's name for it (`meta mark` in nftables, the `MARK` target in iptables), while <strong>fwmark</strong> — "firewall mark" — is what the routing and traffic-control tools call it (`ip rule … fwmark`, tc's `fw` classifier). <mark style="background: #FFB8EBA6;">Setting `meta mark` and matching on `fwmark` therefore act on exactly the same value</mark>. <mark style="background: #FFB86CA6;">It is read by [[#Marks and Policy Routing|policy routing]] to <strong>pick a routing table</strong></mark> and <mark style="background: #FFF3A3A6;">by <strong>tc</strong> to pick a shaping queue</mark>, it can be matched by other netfilter rules, and a local process can stamp it on its own outgoing packets through the `SO_MARK` socket option.

<mark style="background: #FFB8EBA6;">The <strong>connection mark</strong> (<strong>ctmark</strong>) is stored on the [[#Connection Tracking|conntrack]] entry</mark> instead of the packet, <mark style="background: #FF5582A6;">so it persists for the entire connection</mark> — every packet, both directions, for as long as the flow lives in the table. It is the durable counterpart to the ephemeral packet mark.

<mark style="background: #FFB86CA6;">The two are normally used together, because the packet mark forgets and the connection mark remembers</mark>. The decision you want to act on <mark style="background: #FFF3A3A6;">can usually only be made <strong>on the first packet</strong> of a flow</mark> — which interface it entered on, which socket or user it came from — and <mark style="background: #BBFABBA6;">the reply, handled later and separately, no longer has that context</mark>. So the idiom is to decide once, save the result on the connection, then restore it onto every subsequent packet, using the `ct mark set` and `meta mark set` statements from [[nftables#Other Statements]]:

```bash
ct mark set 0x1            # first packet: record the decision on the connection
meta mark set ct mark      # every packet: copy it back onto the packet for routing and tc
```

<mark style="background: #ABF7F7A6;">The restore has to run before the [[#Packet Traversal|routing decision]] consults `skb->mark`</mark>, <mark style="background: #ADCCFFA6;">so it belongs in a prerouting or output chain</mark>. Both marks are 32 bits wide and are often handled with bitmasks, letting independent subsystems each own a slice of the bits without clobbering one another (`meta mark set mark and 0xffff0000 or 0x1`).

## Marks and Policy Routing

The <strong>packet mark</strong> <mark style="background: #FFB8EBA6;">is the bridge between the firewall and policy routing</mark>. <mark style="background: #FF5582A6;">The routing subsystem can choose a routing table based on the mark</mark>, which is how multi-WAN, VPN split-tunnelling and source-based routing are built: nftables sets the mark, `ip rule` matches it.

```bash
ip rule add fwmark 0x1 table 100        # marked packets consult table 100
ip route add default via 203.0.113.1 table 100
```

The same mark can drive <strong>tc</strong>, which classifies packets into shaping queues by fwmark — so a single mark set in the firewall can steer both which link a packet leaves by and how it is queued.

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

> [!note] Harden Neighbor 
> Discovery with the hop limit Genuine ND messages always arrive with a hop limit of 255 — routers decrement it, so a value of 255 proves the packet was not forwarded. Matching `ip6 hoplimit 255` on the ND types rejects spoofed Neighbor Discovery injected from off-link.

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

```
Kernel                           Userspace
  │                                  │
  │  rule: -j NFQUEUE --queue-num 0  │
  ├─── NF_QUEUE verdict ────────────►│  libnetfilter_queue
  │                                  │  inspects / optionally modifies
  │◄── verdict (ACCEPT or DROP) ─────│
  └─ packet continues or is freed
```

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