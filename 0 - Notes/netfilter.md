---
categories:
  - "[[Linux]]"
topic@linux:
tags:
icon: SiLinux
iconColor: "#000000"
---
Netfilter is a framework inside the Linux kernel that lets kernel code register callback functions at fixed points of the network stack, so packets can be inspected, modified, dropped, queued, or rerouted as they pass through. nftables is the userspace tool and ruleset language (`nft`) that programs this framework; everything you write with `nft` ends up controlling Netfilter at one of those points.

> [!info] The ecosystem
> 
> - Netfilter — the kernel framework: the [[#Hooks|hooks]] plus the subsystems ([[#Connection Tracking|conntrack]], [[#NAT|NAT]], [[#Logging|logging]]).
> - nf_tables — the kernel module that evaluates your ruleset (a small bytecode machine).
> - nftables / `nft` — the project and the userspace command that compiles rules into nf_tables.
> - iptables-nft — a compatibility layer that accepts iptables syntax but writes nf_tables rules underneath.

nftables replaces the older iptables, ip6tables, arptables and ebtables tools, unifying them under one syntax and one in-kernel engine while reusing the same Netfilter [[#Hooks|hooks]] and subsystems.

---

# The Netfilter Framework

_The kernel-level machinery: where packets are intercepted and in what order._

## Hooks

_The fixed points in the kernel where Netfilter hands each packet to your rules._

For the IP layer (IPv4 and IPv6) there are five hooks, named `NF_INET_*` in the kernel. Every [[#Base Chains|base chain]] you create attaches to exactly one of them, and the [[#Address Families|family]] you choose decides which hooks are available.

|Hook|Kernel constant|Triggered for|
|---|---|---|
|Prerouting|`NF_INET_PREROUTING`|every incoming packet, before the routing decision|
|Input|`NF_INET_LOCAL_IN`|packets destined to the local host|
|Forward|`NF_INET_FORWARD`|packets being routed through the host|
|Output|`NF_INET_LOCAL_OUT`|packets generated locally, leaving the host|
|Postrouting|`NF_INET_POSTROUTING`|every outgoing packet, after the routing decision|

### Prerouting

The first hook every incoming packet hits, right after basic sanity checks but before the kernel decides where the packet should go. Because it runs before routing, it is the only place you can change a packet's destination and still have it routed accordingly, which is why [[#DNAT|DNAT]] lives here.

### Input

Reached only after the routing decision concludes the packet is addressed to this machine. This is where you filter traffic that terminates on the host itself (SSH to the box, a local web server).

### Forward

Reached when routing determines the packet must be passed on to another host, i.e. the box is acting as a router. Filtering for traffic passing through belongs here.

> [!warning] IP forwarding must be enabled The Forward hook is only meaningfully traversed when the kernel is allowed to route between interfaces: `net.ipv4.ip_forward = 1` and `net.ipv6.conf.all.forwarding = 1`.

### Output

The first hook for packets created by local processes (a reply from your web server, a DNS query from the host). It runs after an initial routing lookup the kernel needs in order to fill in source address and outgoing interface.

### Postrouting

The last hook before a packet leaves the machine, after routing is finalized. Since the destination is already chosen, this is where [[#SNAT|SNAT]] and [[#Masquerade|masquerade]] are applied.

## Hook Priorities

_How the kernel orders multiple chains that sit on the same hook._

Several functions can register on the same [[#Hooks|hook]]. Their order is decided by an integer priority: lower numbers run first, and values can be negative. This is how the kernel guarantees defragmentation and [[#Connection Tracking|connection tracking]] run before your filtering, and source [[#NAT|NAT]] runs after it.

nftables exposes the common values as named keywords so you rarely write the numbers (`ip` / `ip6` / `inet` families):

|Keyword|Value|Purpose|
|---|---|---|
|`raw`|-300|runs before conntrack (used for `notrack`)|
|`mangle`|-150|early packet mangling|
|`dstnat`|-100|destination NAT (prerouting)|
|`filter`|0|normal filtering — the default|
|`security`|50|SECMARK / MAC labelling|
|`srcnat`|100|source NAT (postrouting)|

> [!note] Built-in stages run around your rules Connection tracking registers at -200 and defragmentation at -400, so both always run before anything you write at `filter` priority.

![[netfilter-hook-priority.png]]

These keyword-to-number mappings are defined per [[#Address Families|family]]. The `bridge` family uses a different scale (see [[#bridge|the bridge family]]), so `priority filter` means 0 in an `inet` chain but -200 in a `bridge` chain.

## Packet Traversal

_How a packet threads through the [[#Hooks|hooks]], with the routing decision splitting the path._

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

---

# The nftables Object Model

_How rules are organized: a family holds tables, a table holds chains, a chain holds rules, and sets and maps keep those rules compact._

## Address Families

_Which protocol's packets a [[#Tables|table]] sees, and which [[#Hooks|hooks]] are available to it._

Every nftables table belongs to an address family. The family is the first thing you pick, because it determines what layer of the stack your rules can see (IP, ARP, raw Ethernet) and which hooks exist there.

|Family|Layer / scope|Hooks available|
|---|---|---|
|`ip`|IPv4 only|all five IP hooks|
|`ip6`|IPv6 only|all five IP hooks|
|`inet`|IPv4 and IPv6 together|all five IP hooks|
|`arp`|ARP packets|input, output|
|`bridge`|bridged Ethernet frames (L2)|prerouting, input, forward, output, postrouting|
|`netdev`|raw packets on one interface|ingress (and egress)|

### inet (dual-stack)

A virtual family that attaches to the IP [[#Hooks|hooks]] for both IPv4 and IPv6 at once, so a single ruleset covers both protocols. This is the recommended default for host and router firewalls — it removes the need to maintain parallel `ip` and `ip6` rulesets.

Inside an `inet` chain you can still narrow to one protocol when needed:

- `meta nfproto ipv4` or `meta nfproto ipv6` selects by IP version.
- shared matches like `tcp dport`, `ct state` or `meta l4proto` apply to both versions at once.
- a protocol-specific header match (`ip saddr`, `ip6 daddr`) implicitly restricts that rule to the matching version.

### ip and ip6

Single-protocol families that see only IPv4 (`ip`) or only IPv6 (`ip6`) traffic, each with all five IP hooks. Reach for them only when a rule genuinely applies to one protocol alone; otherwise prefer [[#inet (dual-stack)|inet]].

### arp

The `arp` family filters ARP packets — the protocol that maps IPv4 addresses to MAC addresses on a local segment. It supports only the input and output hooks and replaces the old arptables tool. Typical uses are blocking or rate-limiting ARP to mitigate spoofing, or enforcing expected MAC/IP pairings.

### bridge

The `bridge` family operates at Layer 2, on Ethernet frames passing through a Linux software bridge — a virtual switch (for example `br0`) that joins several interfaces into one segment, the kind hypervisors and container runtimes create to connect VMs and containers. It replaces the old ebtables tool.

Because bridging happens below IP, a bridge chain can match on MAC addresses, VLAN tags and EtherType, and can filter traffic flowing between bridge ports that may never reach the IP layer at all. It exposes the same five hook names as IP, but they fire on the bridge's L2 path — the `forward` hook, for instance, sees a frame moving from one bridge port to another.

The bridge family defines its own [[#Hook Priorities|priority]] scale, so the standard keywords map to different numbers than in `ip` / `ip6` / `inet`:

|Keyword|Value|Hook|
|---|---|---|
|`dstnat`|-300|prerouting|
|`filter`|-200|all|
|`out`|100|output|
|`srcnat`|300|postrouting|

This is the reason `priority filter` resolves to a different number depending on family: each family numbers its standard stages independently, and the keyword is just a friendly name for the family-specific value.

### netdev (per-interface)

A `netdev` chain is bound to one specific interface and runs at the `ingress` hook — the earliest point in the stack, before [[#Prerouting|prerouting]] and before [[#Connection Tracking|conntrack]], roughly where tc ingress sits. Kernels 5.16 and later also offer an `egress` hook.

Because packets dropped here never enter the rest of the stack, netdev is the place for high-volume early filtering: anti-spoofing, basic DDoS scrubbing, and dropping obvious garbage before it costs the kernel anything. A netdev base chain must name its device:

```bash
nft add chain netdev filter ingress-eth0 \
    { type filter hook ingress device eth0 \; }
```

## Tables

_Top-level containers; in nftables they carry no behaviour of their own._

A table holds [[#Chains|chains]], [[#Sets|sets]], [[#Maps|maps]] and other objects, and is identified by its [[#Address Families|family]] plus a name you choose.

```bash
nft add table inet filter      # create a dual-stack table
nft list ruleset               # show everything currently loaded
```

> [!important] Different from iptables In iptables the tables were fixed and predefined (`filter`, `nat`, `mangle`, `raw`). In nftables you create tables yourself, the names are arbitrary, and a table has no built-in meaning. What a chain does is decided by its [[#Chain Types|type]] and [[#Hooks|hook]], not by the table's name. An empty table simply does nothing.

## Chains

_Ordered lists of rules. Whether a chain is reached automatically depends on its kind._

A chain lives inside a [[#Tables|table]] and holds the rules that are evaluated in order. There are two kinds — [[#Base Chains|base]] and [[#Regular Chains|regular]] — and the difference is whether the kernel enters the chain on its own or only when another chain sends control to it.

### Base Chains

A base chain is wired into the Netfilter packet flow. It declares four things — a [[#Chain Types|type]], a [[#Hooks|hook]], a [[#Hook Priorities|priority]] and a [[#Policy|policy]] — and packets reach it automatically because it is registered at one of the hooks.

```bash
nft add chain inet filter input \
    { type filter hook input priority 0 \; policy drop \; }
```

### Regular Chains

A regular chain has no hook and is never entered on its own. It runs only when another chain [[#Verdict Statements|jumps or goes]] to it, which makes it useful for grouping rules into reusable blocks (for example a `tcp-services` chain called from `input`).

```bash
nft add chain inet filter tcp-services          # regular chain, no hook
nft add rule inet filter input ip protocol tcp jump tcp-services
```

A regular chain has no [[#Policy|policy]]. When it ends without a verdict, control simply returns to the caller as if `return` had been issued.

### Chain Types

The type of a [[#Base Chains|base chain]] selects which Netfilter semantics apply.

|Type|Purpose|Valid hooks|
|---|---|---|
|`filter`|ordinary packet filtering|all hooks|
|`nat`|network address translation (conntrack-based)|prerouting, input, output, postrouting|
|`route`|trigger a fresh route lookup if routing-relevant fields changed|output only|

A `nat` chain only inspects the first packet of a connection; [[#Connection Tracking|conntrack]] replays the same translation on every later packet, which is why NAT chains should not carry general filtering rules.

The `route` type is a specialised output-only type. After the [[#Output|output]] chain runs, if the packet's routing-relevant fields changed — destination address, source address, TOS/DSCP, or the firewall mark (`meta mark`) — the kernel performs a fresh routing lookup so the change actually takes effect. Use it when locally generated traffic must be policy-routed based on a mark set in the output path; it corresponds to the old iptables mangle OUTPUT behaviour.

### Hook and Priority

A base chain must declare its [[#Hooks|hook]] (which of the five, or netdev/arp), its [[#Hook Priorities|priority]] (usually a keyword from that section), and its [[#Policy|policy]].

```bash
nft add chain inet nat postrouting \
    { type nat hook postrouting priority srcnat \; policy accept \; }
```

nftables allows more than one base chain on the same hook; they run in ascending priority order, and a packet dropped by an earlier chain never reaches a later one. This is how a `filter` chain at priority 0 coexists on the same hook with a `nat` chain at `dstnat` (-100) or `srcnat` (100).

### Policy

The policy is the [[#Verdict Statements|verdict]] applied to a packet that reaches the end of a base chain without hitting a terminating rule. It can only be `accept` or `drop`. A base chain created without an explicit policy defaults to `accept`.

> [!warning] Default-drop and lockout A `policy drop` on the input chain is the secure default, but loading it with no allow rules can lock you out. Always permit loopback and established traffic first.

```bash
nft add rule inet filter input iif lo accept
nft add rule inet filter input ct state established,related accept
```

### Chain Evaluation Order

Within a chain, rules are tried from top to bottom. For each rule, all of its [[#Match Statements|match]] conditions must pass; if they do, the rule's statements run, and the first terminal [[#Verdict Statements|verdict]] (accept, drop, reject, queue) ends evaluation immediately. A rule that does not match, or that only performs a non-terminal action (counter, log, mark), falls through to the next rule.

If the end of a [[#Base Chains|base chain]] is reached with no terminal verdict, the chain [[#Policy|policy]] is applied. A [[#Regular Chains|regular chain]] instead returns control to whatever chain called it.

![[nftables-chain-evaluation.png]]

## Rules, Statements and Verdicts

_A rule is statements evaluated left to right; the [[#Verdict Statements|verdict]] decides the packet's fate._

### Match Statements

Match statements (expressions) test packet fields. If any test fails, the rest of the rule is skipped and evaluation moves to the next rule.

|Selector|Matches|
|---|---|
|`ip saddr` / `ip daddr`|IPv4 source / destination address|
|`ip6 saddr` / `ip6 daddr`|IPv6 source / destination address|
|`tcp dport` / `udp dport`|transport destination port|
|`tcp flags`|TCP flags (e.g. `syn`, `rst`)|
|`ct state`|[[#Connection Tracking|
|`iif` / `oif`|input / output interface by index (fast)|
|`iifname` / `oifname`|input / output interface by name (supports wildcards like `eth*`)|
|`meta nfproto`|IP version (`ipv4` / `ipv6`), useful in [[#inet (dual-stack)|
|`meta l4proto`|layer-4 protocol, IP-version-agnostic|
|`meta mark` / `ct mark`|packet mark / connection mark|
|`ether saddr`|source MAC address ([[#bridge|

### Verdict Statements

Verdict statements decide what happens to the packet.

|Verdict|Terminal?|Effect|
|---|---|---|
|`accept`|yes (this chain)|let the packet pass this hook|
|`drop`|yes|discard silently, no reply|
|`reject`|yes|discard and send an error (ICMP / TCP RST)|
|`queue`|yes|hand the packet to userspace via [[#NFQUEUE|
|`continue`|no|keep evaluating the next rule|
|`return`|no|leave the current chain (a [[#Base Chains|
|`jump <chain>`|no|enter a chain; `return` comes back here|
|`goto <chain>`|no|enter a chain; does not return — the caller's context is replaced|

> [!note] reject is technically separate The strict verdict statements are `accept`, `drop`, `queue`, `continue`, `return`, `jump` and `goto`. `reject` is a separate terminating statement that drops the packet and additionally sends an error reply, so it behaves like a verdict in practice.

`accept` is only final for the current base chain. A packet accepted in a [[#Prerouting|prerouting]] chain still continues to the next hook; it is not a global pass.

The difference between `jump` and `goto` is the return path. After a `jump`, a `return` (or the chain ending) brings you back to the statement after the jump. After a `goto`, a `return` does not come back; it behaves as if you had been in the target chain all along.

![[nftables-jump-vs-goto.png]]

A rule may also carry non-verdict actions that change state without ending evaluation, such as `counter`, `log`, `meta mark set` or `ct mark set`, followed by a verdict.

```bash
nft add rule inet filter input tcp dport 22 ct state new \
    log prefix "SSH-NEW: " counter accept
```

## Sets, Maps and Dictionaries

_Native data structures that keep rulesets short and lookups fast._

### Sets

A set holds many values of one type (addresses, ports, interfaces) and is matched in a single [[#Match Statements|rule]].

```bash
nft add set inet filter blocklist { type ipv4_addr \; flags interval \; }
nft add element inet filter blocklist { 10.0.0.0/8, 192.0.2.55 }
nft add rule inet filter input ip saddr @blocklist drop
```

An anonymous set is written inline (`tcp dport { 22, 80, 443 } accept`) and dies with its rule. A named set exists independently and can be changed live without reloading the ruleset, which is what makes it suitable for dynamic blocklists. The `flags interval` option lets a set store ranges and CIDR prefixes rather than single values.

### Maps

A map associates a key with a value. A verdict map (`vmap`) maps keys directly to [[#Verdict Statements|verdicts]], collapsing many rules into one lookup.

```bash
nft add rule inet filter input tcp dport vmap { 22 : accept, 25 : drop, 80 : accept }
```

### Dynamic Sets and Rate Limiting

A set can be populated by the ruleset itself and combined with rate limits to track per-source behaviour, which is the basis for connection-rate limiting.

```bash
nft add rule inet filter input ct state new \
    meter ssh-flood { ip saddr limit rate 10/minute } accept
```

> [!note] `meter` is the legacy form Current nftables expresses the same idea with a named dynamic set updated from the rule, e.g. `update @set { ip saddr limit rate 10/minute }`.

---

# Stateful Processing and Subsystems

_Subsystems layered on top of the [[#The nftables Object Model|object model]]: connection tracking, address translation, logging and offload._

## Connection Tracking

_The subsystem that records connection state and turns the filter from stateless into stateful._

Conntrack runs early ([[#Hook Priorities|priority]] -200, before your [[#Chain Types|filter]] chains) and is the foundation for [[#NAT|NAT]]. Without it you would have to manually allow the return traffic of every connection.

Each packet is classified into a state, matchable with `ct state`:

|State|Meaning|
|---|---|
|`new`|first packet of a connection conntrack has not seen before|
|`established`|belongs to a connection already seen in both directions|
|`related`|a new connection logically tied to an existing one (FTP data channel, ICMP errors)|
|`invalid`|cannot be associated with any known connection, or is malformed — usually dropped|
|`untracked`|deliberately excluded from tracking by a `notrack` rule at `raw` (-300) priority|

```bash
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input ct state invalid drop
```

![[netfilter-conntrack-states.png]]

> [!note] Helpers for dynamic-port protocols Protocols like FTP, SIP and TFTP open secondary connections on dynamic ports. Conntrack helpers parse the control channel and create an expectation so the data connection matches `ct state related`. On modern kernels automatic helper assignment is disabled for security; you attach a helper explicitly with a `ct helper` object and a rule that assigns it to the control traffic.

Beyond state, the `ct` expression also exposes the connection mark (`ct mark`, persistent for the life of the flow, unlike the per-packet `meta mark`) and a live connection counter (`ct count`) you can use to cap concurrent connections per source.

## NAT

_Rewriting source or destination addresses, built on top of [[#Connection Tracking|conntrack]]._

NAT depends entirely on connection tracking: the translation is decided on the first packet of a flow and replayed for the rest, which is why a [[#Chain Types|nat-type]] chain only sees that first packet.

### DNAT

Destination NAT changes the destination, so it must run in [[#Prerouting|prerouting]] (or [[#Output|output]] for locally generated traffic) where the new destination still affects routing. Used for port forwarding and publishing internal servers.

```bash
nft add rule inet nat prerouting tcp dport 80 dnat to 192.168.1.10:8080
```

### SNAT

Source NAT changes the source, so it must run in [[#Postrouting|postrouting]], after routing has chosen the outgoing interface.

```bash
nft add rule inet nat postrouting oif eth0 snat to 203.0.113.5
```

### Masquerade

A dynamic form of [[#SNAT|SNAT]] that uses the outgoing interface's current IP automatically, ideal when the WAN address is assigned by DHCP or PPP. Slightly more costly than static SNAT because the address is resolved per connection.

```bash
nft add rule inet nat postrouting oif eth0 masquerade
```

### Redirect

A special [[#DNAT|DNAT]] that sends the packet to the local machine itself (the incoming interface's address), commonly used for transparent proxies.

```bash
nft add rule inet nat prerouting tcp dport 80 redirect to :3128
```

> [!note] NAT chain placement Keep one [[#Chain Types|nat-type]] base chain per relevant hook — a [[#Prerouting|prerouting]] chain at `dstnat` priority for DNAT and a [[#Postrouting|postrouting]] chain at `srcnat` priority for SNAT — and leave general filtering in separate [[#Chain Types|filter]] chains.

## Logging, Accounting and Offload

_Side-channel and performance subsystems that ride on the same [[#Hooks|hooks]]._

### Logging

The `log` statement sends packet metadata to the kernel log, or to userspace via nfnetlink_log. It is non-terminal, so pair it with a [[#Verdict Statements|verdict]].

```bash
nft add rule inet filter input ct state invalid log prefix "INVALID: " drop
```

### NFQUEUE

The `queue` [[#Verdict Statements|verdict]] hands packets to a userspace program (via libnetfilter_queue) which then returns its own verdict. This is how IDS/IPS and deep-inspection tools plug in.

### Counters and Quotas

`counter` objects tally packets and bytes per rule; `quota` objects can trip once a byte threshold is crossed, enabling usage-based rules.

### Flowtables

A flowtable offloads already-[[#Connection Tracking|established]] connections to a software (or hardware) fast path. Once a [[#Forward|forwarded]] flow is added to a flowtable, its later packets bypass the normal [[#Chains|chain]] traversal entirely, which sharply increases router throughput. Only suitable for forwarded, established traffic; the first packets still pass through the regular path so policy is applied.

```bash
table inet filter {
    flowtable f { hook ingress priority 0; devices = { eth0, eth1 }; }
    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state established flow add @f
        ct state established,related accept
    }
}
```

---

# Operating nftables

_Loading, inspecting and persisting rules in day-to-day use._

## Managing the Ruleset

_Everything goes through the single `nft` command; changes are applied atomically._

### Atomic Loading

Loading a file with `nft -f` is atomic: the whole file is parsed and committed in one transaction, so the kernel never runs a half-applied ruleset. A syntax error anywhere aborts the load and leaves the running ruleset untouched.

```bash
nft -f /etc/nftables.conf      # load (replace) atomically
nft -c -f /etc/nftables.conf   # check syntax only, change nothing
```

### Inspecting

```bash
nft list ruleset               # everything currently loaded
nft list tables                # just the table names
nft list table inet filter     # one table with its chains and rules
nft -a list ruleset            # show rule handles (needed for deletion)
```

### Modifying Live

Objects can be added or removed without reloading the whole ruleset. Deleting a specific rule needs its handle, obtained with `-a`.

```bash
nft add rule inet filter input tcp dport 8080 accept
nft -a list chain inet filter input            # find the handle
nft delete rule inet filter input handle 12    # delete that rule by handle
```

### Flushing and Deleting

```bash
nft flush ruleset                   # wipe everything
nft flush chain inet filter input   # empty one chain but keep it registered
nft delete chain inet filter input  # remove the chain
nft delete table inet filter        # remove the table and all it contains
```

### Persistence

The running ruleset lives only in kernel memory and is lost on reboot. Snapshot it to the distribution's config file and enable the service so it is restored at boot.

```bash
nft list ruleset > /etc/nftables.conf   # snapshot current state
systemctl enable --now nftables         # restore /etc/nftables.conf at boot
```

## Practical Skeleton

_A minimal stateful host firewall that ties the concepts together._

```bash
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;

        iif lo accept                                  # loopback
        ct state established,related accept            # stateful return traffic
        ct state invalid drop                          # bad packets
        ip protocol icmp accept                        # IPv4 ping
        ip6 nexthdr icmpv6 accept                      # ICMPv6 (required for IPv6)
        tcp dport { 22, 80, 443 } ct state new accept  # allowed services
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
    }

    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

> [!info] Reading order recap A packet hits a [[#Hooks|hook]], the [[#Base Chains|base chains]] on that hook run in [[#Hook Priorities|priority]] order, rules are evaluated top to bottom, and the first terminal [[#Verdict Statements|verdict]] wins. If no rule terminates, the chain [[#Policy|policy]] applies. If the packet is accepted, it continues to the next hook along the [[#Packet Traversal|traversal path]].