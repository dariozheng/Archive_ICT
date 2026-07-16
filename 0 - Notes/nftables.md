---
categories:
  - "[[Linux]]"
  - "[[Security]]"
topic@linux: "[[Linux General]]"
tags:
  - firewall
  - claude
  - kernel
  - Networking
  - Security
  - Linux
icon: SiLinux
iconColor: "#000000"
last_update: 2026-07-09
---
nftables is the modern packet-filtering framework for Linux: a single command, `nft`, and one in-kernel engine, `nf_tables`, that together replace iptables, ip6tables, arptables and ebtables. It does not process packets itself —<mark style="background: #FFB8EBA6;"> it compiles your ruleset into the kernel</mark> and <mark style="background: #FFB86CA6;">programs [[Netfilter]], the framework that provides the hooks and subsystems the rules actually act on</mark>.

> [!info] nftables drives 
> 
> Netfilter `nft` (userspace) writes rules into `nf_tables` (kernel), which registers them at [[Netfilter#Hooks and Packet Flow|Netfilter hooks]]. The hooks, [[Netfilter#Hook Priorities|priorities]], [[Netfilter#Connection Tracking|conntrack]] and [[Netfilter#Network Address Translation|NAT]] are defined by Netfilter and documented in [[Netfilter]]; this note covers how to express and operate the rules that use them.

---

# The nftables Object Model

_How rules are organized: a family holds tables, a table holds chains, a chain holds rules, and sets and maps keep those rules compact._

![[nftables-object-model.png]]

Two relationships hold the whole model together, and every object in this note is some mix of the two.

The first is _containment_ — a family holds tables, a table holds chains and data structures, a chain holds rules, a rule holds statements — which gives the ruleset its tree shape.

The second is _reference_ — a rule names a set, a map, a stateful object or another chain that lives beside it in the same table, rather than containing it. Containment decides where an object is defined; references decide how those objects cooperate once packets start flowing.

The containment spine runs from the outside in:

```text
family                which protocol layer, and which hooks exist   (a property, not a container you create)
└── table             names a family; groups objects; no behaviour of its own
    ├── chain         an ordered list of rules
    │   └── rule      an ordered list of statements — matches gate it, a verdict ends it
    ├── set / map     values the rules look up in a single shot (@name, vmap)
    └── object        state that outlives any one rule: counter, quota, ct helper/timeout, flowtable
```

The same tree written as a ruleset, with one object of each kind in place:

```bash
table inet filter {                                     # container, in the inet family
    set blocklist   { type ipv4_addr; flags interval; } # data structure, referenced by @name
    counter dropped { }                                 # stateful object, outlives every rule

    chain input {                                       # base chain: entered at a hook
        type filter hook input priority filter; policy drop;
        ip saddr @blocklist counter name "dropped" drop # rule: matches, action, verdict
        tcp dport 22 jump ssh-rules                     # rule: reference to a regular chain
    }

    chain ssh-rules {                                   # regular chain: entered only by jump/goto
        ct state new limit rate 10/minute accept
    }
}
```

<mark style="background: #FF5582A6;">A [[#Address Families|family]]</mark> is the outermost choice, but it is not something you create and pour objects into — it is a property every [[#Tables|table]] carries that <mark style="background: #FF5582A6;">fixes which layer of the stack</mark> the table's chains <mark style="background: #FF5582A6;">can see</mark> and <mark style="background: #FF5582A6;">which [[Netfilter#Hooks and Packet Flow|Netfilter hooks]] are open to them</mark>.

<mark style="background: #FFB86CA6;">The [[#Tables|table]] beneath it is a pure container</mark>: <mark style="background: #FFB86CA6;">it gathers chains, sets, maps and objects under one family and name and does nothing by itself</mark>.

<mark style="background: #FFF3A3A6;">A [[#Chains|chain]] holds the rules</mark>, and <mark style="background: #CACFD9A6;">whether packets ever reach those rules depends on the chain's kind</mark> — <mark style="background: #FFB8EBA6;">a [[#Base Chains|base chain]] is registered at a hook and entered automatically</mark>, <mark style="background: #BBFABBA6;">a [[#Regular Chains|regular chain]] runs only when another chain jumps to it</mark>.

<mark style="background: #ABF7F7A6;">A [[#Anatomy of a Rule|rule]]</mark> is the bottom of the tree: <mark style="background: #ABF7F7A6;">a line of statements where</mark> <mark style="background: #D2B3FFA6;">[[#Match Statements|matches]] gate the rule</mark> and <mark style="background: #CACFD9A6;">a [[#Verdict Statements|verdict]] settles the packet</mark>.

<strong>References</strong> are what keep that tree short and stateful. Rather than one rule per value, a rule tests membership in a [[#Sets|set]] (`ip saddr @blocklist`) or dispatches through a verdict [[#Maps|map]] in one lookup; rather than losing state when the rule ends, a rule attaches a named [[#Stateful Objects|object]] — a [[#Counters and Quotas|counter]] that accumulates across every rule that names it, a [[#Connection-Tracking Objects|ct helper]], a [[#Flowtables|flowtable]] — that persists independently of any rule.

`jump` and `goto` are references as well: they pass control to a [[#Regular Chains|regular chain]] so a block of rules can be shared.

What each layer _does to_ the others falls out of this. The family constrains everything under it: pick `arp` and there is no IP match or NAT hook to be had; pick `netdev` and only `ingress`/`egress` exist. Inside a table it is the chain's [[#Chain Types|type]] and [[#Hook and Priority|hook]] — never the table's name — that decide what the chain does and where in the packet's path it runs.

And the [[#Base Chains|base chain]] is the single seam to the kernel: registering at a hook is what pulls packets into the ruleset in the first place, so every regular chain, set, map and object is inert until a rule in some base chain reaches it.

That seam is also the line between the two subjects. The objects here are nftables' way of _expressing_ a policy; the [[Netfilter#Hooks and Packet Flow|hooks]] they hang on, the [[Netfilter#Hook Priorities|priorities]] that order them, and the [[Netfilter#Connection Tracking|conntrack]] and [[Netfilter#Network Address Translation|NAT]] they drive all belong to [[Netfilter]] and are documented there. The sections below walk the tree from the outside in, starting with the family.

## Address Families

_Which protocol's packets a [[#Tables|table]] sees, and which [[Netfilter#Hooks and Packet Flow|hooks]] are available to it._

<mark style="background: #FFF3A3A6;">Every table belongs to an address family</mark>. The family is the first thing you pick, because <mark style="background: #BBFABBA6;">it determines what layer of the stack the rules can see (IP, ARP, raw Ethernet)</mark> and which <mark style="background: #ABF7F7A6;">Netfilter hooks exist there</mark>.

|Family|Layer / scope|Hooks available|
|---|---|---|
|`ip`|IPv4 only|all five IP hooks|
|`ip6`|IPv6 only|all five IP hooks|
|`inet`|IPv4 and IPv6 together|all five IP hooks, plus ingress (kernel ≥ 5.10)|
|`arp`|ARP packets|input, output|
|`bridge`|bridged Ethernet frames (L2)|prerouting, input, forward, output, postrouting|
|`netdev`|raw packets on one interface|ingress (and egress)|

The family is named where the table is created, and never again:

```bash
nft add table ip     filter      # IPv4 only
nft add table ip6    filter      # IPv6 only
nft add table inet   filter      # both at once — the usual choice
nft add table arp    filter      # ARP packets
nft add table bridge filter      # Ethernet frames crossing a software bridge
nft add table netdev filter      # raw packets on one named interface
```

The names are unrelated: `ip filter` and `inet filter` are two distinct tables that happen to share a name, and either could just as well be called `myrules`.

![[netfilter-packet-flow.png]]

### inet (dual-stack)

<mark style="background: #FFB8EBA6;">A virtual family that attaches to the IP hooks for both IPv4 and IPv6 at once</mark>, so a single ruleset covers both protocols. This is the <mark style="background: #FF5582A6;">recommended default for host and router firewalls</mark> — it removes the need to maintain parallel `ip` and `ip6` rulesets.

Inside an `inet` chain you can still narrow to one protocol when needed:

- `meta nfproto ipv4` or `meta nfproto ipv6` selects by IP version.
- shared matches like `tcp dport`, `ct state` or `meta l4proto` apply to both versions at once.
- a protocol-specific header match (`ip saddr`, `ip6 daddr`) implicitly restricts that rule to the matching version.

```bash
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;

        ct state established,related accept          # version-agnostic
        tcp dport 22 ct state new accept             # matches v4 and v6 alike

        meta nfproto ipv4 icmp   type echo-request accept    # explicit: IPv4 only
        meta nfproto ipv6 icmpv6 type echo-request accept    # explicit: IPv6 only

        ip  saddr 192.0.2.0/24 accept               # implicitly IPv4 only
        ip6 saddr 2001:db8::/32 accept              # implicitly IPv6 only
    }
}
```

A dual-stack ruleset still has to honor a few IPv6-specific requirements — permitting ICMPv6, the no-NAT model, and `fib`-based anti-spoofing; these are covered in [[Netfilter#IPv6 and Netfilter]].

### ip and ip6

<mark style="background: #FFB86CA6;">Single-protocol families</mark> <mark style="background: #BBFABBA6;">that see only IPv4</mark> (`ip`) <mark style="background: #BBFABBA6;">or only IPv6</mark> (`ip6`) <mark style="background: #BBFABBA6;">traffic</mark>, each with all five IP hooks. Reach for them only when a rule genuinely applies to one protocol alone; otherwise prefer [[#inet (dual-stack)|inet]].

```bash
# IPv4 only: masquerading has no place in an IPv6 ruleset
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        oifname "eth0" masquerade
    }
}

# IPv6 only: neighbour discovery has no IPv4 counterpart
table ip6 filter {
    chain input {
        type filter hook input priority filter; policy drop;
        icmpv6 type { nd-neighbor-solicit, nd-neighbor-advert, nd-router-advert } \
            ip6 hoplimit 255 accept
    }
}
```

Because a NAT chain in `inet` needs kernel 5.2 or later, a separate `ip nat` table is also the compatible way to masquerade on older systems — see [[#Chain Types|chain types]].

### arp

The `arp` family <mark style="background: #ABF7F7A6;">filters ARP packets</mark> — the protocol that maps IPv4 addresses to MAC addresses on a local segment. <mark style="background: #ADCCFFA6;">It supports only the input and output hooks</mark> and replaces the old <strong>arptables</strong> tool. Typical uses are blocking or rate-limiting ARP to mitigate spoofing, or enforcing expected MAC/IP pairings.

```bash
table arp filter {
    chain input {
        type filter hook input priority filter; policy accept;

        # only the real gateway may answer for 192.0.2.1
        arp operation reply arp daddr ip 192.0.2.1 \
            arp saddr ether != 00:11:22:33:44:55 drop

        arp operation request limit rate over 20/second drop   # ARP storm brake
    }
}
```

### bridge

The `bridge` family <mark style="background: #D2B3FFA6;">operates at Layer 2</mark>, <mark style="background: #D2B3FFA6;">on Ethernet frames passing through a Linux software bridge</mark> — <mark style="background: #CACFD9A6;">a virtual switch</mark> (for example `br0`) <mark style="background: #CACFD9A6;">that joins several interfaces into one segment</mark>, the <mark style="background: #FFB8EBA6;">kind</mark> <mark style="background: #FF5582A6;">hypervisors and container runtimes</mark> <mark style="background: #FFB8EBA6;">create</mark> <mark style="background: #FFB86CA6;">to connect VMs and containers</mark>. <strong>It replaces the old ebtables tool</strong>. <mark style="background: #FFF3A3A6;">The bridge normally lives in the host's initial [[Netfilter#Network Namespaces|namespace]]</mark>, <mark style="background: #BBFABBA6;">so its bridge-family rules are evaluated there</mark> rather than inside each container.

<mark style="background: #ABF7F7A6;">Because bridging happens below IP</mark>, <mark style="background: #ADCCFFA6;">a bridge chain can match on MAC addresses, VLAN tags and EtherType</mark>, and <mark style="background: #D2B3FFA6;">can filter traffic flowing between bridge ports that may never reach the IP layer at all</mark>. It exposes the same five hook names as IP, but they fire on the bridge's L2 path — the `forward` hook, for instance, sees a frame moving from one bridge port to another.

```bash
table bridge filter {
    chain forward {
        type filter hook forward priority filter; policy accept;

        ether type arp accept                     # let address resolution through
        vlan id != 100 drop                       # only VLAN 100 crosses this bridge
        iifname "vnet0" ether saddr != 52:54:00:12:34:56 drop   # pin a guest's MAC
        ether type { ipv4, ipv6 } accept
        drop                                      # everything else, including non-IP chatter
    }
}
```

> [!note] br_netfilter is a separate, legacy mechanism 
> 
> The old `br_netfilter` module makes bridged IP traffic additionally traverse the `ip`/`ip6`/`inet` hooks (the `bridge-nf-call-iptables` sysctls). It is unrelated to the bridge family and a frequent source of "why is my bridge traffic being filtered" surprises — some container runtimes load it. Bridge-family rules do not need it.

The bridge family defines its own [[Netfilter#Hook Priorities|priority]] scale, so the standard keywords map to different numbers than in `ip` / `ip6` / `inet`:

|Keyword|Value|Hook|
|---|---|---|
|`dstnat`|-300|prerouting|
|`filter`|-200|all|
|`out`|100|output|
|`srcnat`|300|postrouting|

This is why `priority filter` resolves to a different number depending on family: each family numbers its standard stages independently, and the keyword is just a friendly name for the family-specific value.

### netdev (per-interface)

<mark style="background: #FFB8EBA6;">A `netdev` chain is bound to one specific interface</mark> and <mark style="background: #FF5582A6;">runs at the `ingress` hook</mark> — <mark style="background: #FF5582A6;">the earliest Netfilter point in the stack</mark>, <mark style="background: #FFB86CA6;">before [[Netfilter#Prerouting|prerouting]] and before [[Netfilter#Connection Tracking|conntrack]]</mark>. On the receive path only XDP and <strong>tc</strong> ingress run earlier: the order is XDP → tc ingress → netfilter ingress. Kernels 5.16 and later also offer an `egress` hook.

Because packets dropped here never enter the rest of the stack, <mark style="background: #FFF3A3A6;"><strong>netdev</strong> is the place for high-volume early filtering</mark>: <strong>anti-spoofing</strong>, <strong>basic DDoS scrubbing</strong>, and <strong>dropping obvious garbage</strong> before it costs the kernel anything. A <strong>netdev</strong> base chain must name its device (and, like any base chain, declare a priority):

```bash
nft add chain netdev filter ingress-eth0 \
    { type filter hook ingress device eth0 priority 0 \; }
```

The same chain in file form, doing the scrubbing it exists for:

```bash
table netdev filter {
    chain ingress-eth0 {
        type filter hook ingress device eth0 priority 0; policy accept;

        ip saddr { 127.0.0.0/8, 10.0.0.0/8, 192.168.0.0/16 } drop  # martians on the WAN
        ip frag-off & 0x1fff != 0 drop                             # fragment floods
        tcp flags & (fin|syn|rst|ack) == 0 drop                    # null scan
        meta pkttype broadcast drop
    }
}
```

## Tables

_Top-level containers; in nftables they carry no behavior of their own._

A table holds [[#Chains|chains]], [[#Sets|sets]], [[#Maps|maps]] and other objects, and is identified by its [[#Address Families|family]] plus a name you choose.

```bash
nft add table inet filter      # create a dual-stack table
nft list ruleset               # show everything currently loaded
```

In file form the table is simply the brace that everything else lives inside:

```bash
table inet filter {
    set   blocklist { type ipv4_addr; flags interval; }
    map   dispatch  { type inet_service : verdict; }
    counter dropped { }

    chain input { type filter hook input priority filter; policy drop; }
    chain audit { }                       # regular chain: no hook, no policy
}
```

Deleting the table removes every object above it in one step, which makes a table a convenient unit of ownership — one table per subsystem or per role, so each can be reloaded or torn down on its own:

```bash
nft list table inet filter     # one table with everything it contains
nft delete table inet filter   # and everything it contains goes with it
```

> [!important] Different from iptables 
> 
> In iptables the tables were fixed and predefined (`filter`, `nat`, `mangle`, `raw`). In nftables you create tables yourself, the names are arbitrary, and a table has no built-in meaning. What a chain does is decided by its [[#Chain Types|type]] and [[Netfilter#Hooks and Packet Flow|hook]], not by the table's name. An empty table simply does nothing.

## Chains

_Ordered lists of rules. Whether a chain is reached automatically depends on its kind._

A chain lives inside a [[#Tables|table]] and holds the rules that are evaluated in order. There are two kinds — [[#Base Chains|base]] and [[#Regular Chains|regular]] — and the difference is whether the kernel enters the chain on its own or only when another chain sends control to it.

### Base Chains

A base chain is wired into the [[Netfilter#Hooks and Packet Flow|Netfilter packet flow]]. It declares four things — a [[#Chain Types|type]], a hook, a [[Netfilter#Hook Priorities|priority]] and a [[#Policy|policy]] — and packets reach it automatically because it is registered at one of the hooks.

```bash
nft add chain inet filter input \
    { type filter hook input priority 0 \; policy drop \; }
```

Written as a file, with all four declarations visible on the first line and one base chain per hook:

```bash
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
    }
    chain forward {
        type filter hook forward priority filter; policy drop;
    }
    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

A base chain in the `netdev` family additionally names its `device`; one in a `nat` chain type is restricted to the NAT-capable hooks. Everything else — matching, verdicts, references — works the same as in a regular chain.

### Regular Chains

A regular chain has no hook and is never entered on its own. It runs only when another chain [[#Verdict Statements|jumps or goes]] to it, which makes it useful for grouping rules into reusable blocks (for example a `tcp-services` chain called from `input`).

```bash
nft add chain inet filter tcp-services          # regular chain, no hook
nft add rule inet filter input ip protocol tcp jump tcp-services
```

A fuller example: one shared block of rules, reached from two different base chains.

```bash
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ip protocol tcp jump tcp-services
    }
    chain forward {
        type filter hook forward priority filter; policy drop;
        ip protocol tcp jump tcp-services
    }

    chain tcp-services {                    # no type, no hook, no policy
        tcp dport 22 ct state new accept
        tcp dport { 80, 443 } accept
        return                              # explicit; falling off the end does the same
    }
}
```

A regular chain has no [[#Policy|policy]]. When it ends without a verdict, control simply returns to the caller as if `return` had been issued.

### Chain Types

The type of a [[#Base Chains|base chain]] selects which Netfilter semantics apply.

|Type|Purpose|Valid hooks|
|---|---|---|
|`filter`|ordinary packet filtering|all hooks|
|`nat`|network address translation (conntrack-based)|prerouting, input, output, postrouting|
|`route`|trigger a fresh route lookup if routing-relevant fields changed|output only|

```bash
table inet example {
    # filter: ordinary matching, valid on any hook
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
    }

    # nat: sees only the first packet of each connection
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        oifname "eth0" masquerade
    }

    # route: re-runs the routing lookup because the mark changed
    chain out-mark {
        type route hook output priority mangle; policy accept;
        ip daddr 203.0.113.0/24 meta mark set 0x1
    }
}
```

A `nat` chain only inspects the first packet of a connection; [[Netfilter#How NAT Uses Conntrack|conntrack]] replays the same translation on every later packet, which is why NAT chains should not carry general filtering rules. (NAT in the `inet` family needs kernel 5.2 or later; on older kernels use separate `ip` / `ip6` NAT tables.)

The `route` type is a specialised output-only type. After the [[Netfilter#Output|output]] chain runs, if the packet's routing-relevant fields changed — destination address, source address, TOS/DSCP, or the firewall mark (`meta mark`) — the kernel performs a fresh routing lookup so the change takes effect. Use it when locally generated traffic must be policy-routed based on a mark set in the output path; it corresponds to the old iptables mangle OUTPUT behaviour.

### Hook and Priority

A base chain must declare its hook (which of the five, or netdev/arp) and its [[Netfilter#Hook Priorities|priority]]. nftables names the common priorities so you rarely write the raw numbers:

|Keyword|Value (ip/ip6/inet)|Purpose|
|---|---|---|
|`raw`|-300|before conntrack (used for `notrack`)|
|`mangle`|-150|early packet mangling|
|`dstnat`|-100|destination NAT, prerouting|
|`filter`|0|normal filtering — the default|
|`security`|50|SECMARK / MAC labelling|
|`srcnat`|100|source NAT, postrouting|

```bash
nft add chain inet nat postrouting \
    { type nat hook postrouting priority srcnat \; policy accept \; }
```

More than one base chain may sit on the same hook; they run in ascending priority order, and a packet dropped by an earlier chain never reaches a later one. An `accept`, by contrast, only concludes the chain that issued it — the remaining chains on the same hook still see the packet. This is how a `filter` chain at priority 0 coexists on the same hook with a `nat` chain at `dstnat` (-100) or `srcnat` (100).

Three chains sharing the prerouting hook, running in the order their priorities give them:

```bash
table inet stack {
    chain pre-raw {
        type filter hook prerouting priority raw; policy accept;    # -300, before conntrack
        udp dport 123 notrack
    }
    chain pre-dnat {
        type nat hook prerouting priority dstnat; policy accept;    # -100
        tcp dport 443 dnat ip to 192.168.1.10
    }
    chain pre-filter {
        type filter hook prerouting priority filter; policy accept; #    0
        fib saddr . iif oif missing drop
    }
}
```

Priorities also accept arithmetic on the keyword — `priority filter - 10` slips a chain in just ahead of the normal filtering stage without hard-coding `-10`.

### Policy

The policy is the [[#Verdict Statements|verdict]] applied to a packet that reaches the end of a base chain without hitting a terminating rule. It can only be `accept` or `drop`. A base chain created without an explicit policy defaults to `accept`.

```bash
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;    # deny anything not matched
        iif lo accept
        ct state established,related accept
    }
    chain output {
        type filter hook output priority filter; policy accept; # permit anything not matched
    }
    chain forward {
        type filter hook forward priority filter;               # no policy given -> accept
    }
}
```

The policy of a live chain can be changed without touching its rules, which is the safe way to test a default-drop chain: build the rules with `policy accept`, confirm nothing legitimate is unmatched, then tighten.

```bash
nft chain inet filter input '{ policy accept; }'   # relax
nft chain inet filter input '{ policy drop; }'     # tighten once the allow rules are proven
```

A [[#Regular Chains|regular chain]] cannot carry a policy at all; reaching its end returns control to the caller.

> [!warning] Default-drop and lockout 
> 
> A `policy drop` on the input chain is the secure default, but loading it with no allow rules can lock you out. Always permit loopback and established traffic first.

```bash
nft add rule inet filter input iif lo accept
nft add rule inet filter input ct state established,related accept
```

### Chain Evaluation Order

Within a chain, rules are tried from top to bottom. For each rule, all of its [[#Match Statements|match]] conditions must pass; if they do, the rule's statements run, and the first terminal [[#Verdict Statements|verdict]] (accept, drop, reject, queue) ends evaluation immediately. A rule that does not match, or that only performs a non-terminal action (counter, log, mark), falls through to the next rule.

```bash
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;

        ct state invalid drop            # 1  terminal — evaluation of the chain stops here
        tcp dport 22 counter             # 2  non-terminal — counts, then falls through
        tcp dport 22 ip saddr 10.0.0.0/8 accept   # 3  reached only because 2 did not terminate
        tcp dport 80 jump web            # 4  web runs; if it returns, evaluation resumes at 5
        udp dport 53 accept              # 5
                                         #    end of chain, nothing matched -> policy drop
    }

    chain web {
        ct state new limit rate 50/second accept  # under the rate: accept, chain over
        drop                                      # over it: drop, chain over
    }
}
```

Rule 2 shows why a bare `counter` is not a verdict, and rule 4 shows the one case where control leaves the chain and comes back. If `web` had ended without a verdict, evaluation would have resumed at rule 5 exactly as a `return` would have done.

If the end of a [[#Base Chains|base chain]] is reached with no terminal verdict, the chain [[#Policy|policy]] is applied. A [[#Regular Chains|regular chain]] instead returns control to whatever chain called it.

![[nftables-chain-evaluation.png]]

---

# Rules, Statements and Verdicts

_A rule is a list of statements evaluated left to right; matches gate the rule, and a verdict decides the packet's fate._

## Anatomy of a Rule

A rule is a sequence of statements inside a [[#Chains|chain]]. Statements are read left to right and fall into two kinds: [[#Match Statements|match]] statements that test the packet, and action statements that do something (a [[#Verdict Statements|verdict]], or a non-terminal action like `counter` — see [[#Other Statements]]). Evaluation of a rule stops at the first match that fails; if every match passes, all the actions run.

```bash
nft add rule inet filter input tcp dport 22 ct state new counter accept
#                              └── matches ──┘ └ action ┘ └verdict┘
```

The kernel assigns every rule a numeric handle, which you need in order to delete or insert relative to it.

```bash
nft -a list chain inet filter input            # show rules with handles
nft delete rule inet filter input handle 12    # delete by handle
nft insert rule inet filter input position 12 ip saddr 10.0.0.1 drop
```

A trailing `comment "…"` annotates a rule and survives in the listing.

```bash
nft add rule inet filter input tcp dport 5432 accept comment "postgres, ticket #412"
```

## Match Statements

Match statements test packet fields. They come from three main sources: `meta` (packet metadata), header expressions (the protocol fields themselves), and `ct` (connection state).

Metadata (`meta`, the keyword is often optional):

|Selector|Matches|
|---|---|
|`iif` / `oif`|input / output interface by index (fast, but the interface must exist when the rule loads — for interfaces that come and go, like `ppp0` or `wg0`, use the name form)|
|`iifname` / `oifname`|interface by name, with wildcards like `eth*`|
|`meta nfproto`|IP version (`ipv4` / `ipv6`), useful in [[#inet (dual-stack)\|inet]]|
|`meta l4proto`|layer-4 protocol, IP-version-agnostic|
|`meta mark`|the packet's firewall mark|
|`meta length`|total packet size in bytes|
|`meta pkttype`|link-layer class: `host`, `broadcast`, `multicast` — useful for dropping broadcast/multicast noise|
|`meta hour` / `meta day`|wall-clock time of day and day of week, for time-windowed rules|
|`meta skuid` / `meta skgid`|owning socket's user / group (output only)|

```bash
nft add rule inet filter input iifname "eth*" meta pkttype broadcast drop
nft add rule inet filter input meta length > 1500 counter drop
nft add rule inet filter input meta hour "09:00"-"17:00" tcp dport 3306 accept
nft add rule inet filter output meta skuid "backup" oifname "eth0" accept
```

Header fields:

|Selector|Matches|
|---|---|
|`ip saddr` / `ip daddr`|IPv4 source / destination address|
|`ip6 saddr` / `ip6 daddr`|IPv6 source / destination address|
|`ip protocol` / `ip6 nexthdr`|upper-layer protocol (`ip6 nexthdr` only reads the first next-header field, so it misses transports behind IPv6 extension headers — prefer `meta l4proto`)|
|`ip dscp` / `ip6 dscp`|DSCP / traffic-class field (QoS)|
|`ip ttl` / `ip6 hoplimit`|IPv4 TTL / IPv6 hop limit|
|`ip frag-off` / `frag`|IPv4 fragment offset / IPv6 fragment header|
|`tcp dport` / `udp dport`|transport destination port|
|`tcp flags`|TCP flags (e.g. `syn`, `rst`)|
|`icmp type` / `icmpv6 type`|ICMP message type|
|`ether saddr` / `ether type`|source MAC / EtherType ([[#bridge]])|
|`vlan id`|802.1Q VLAN tag|

```bash
nft add rule inet filter input ip saddr != 10.0.0.0/8 ip daddr 10.0.0.1 drop
nft add rule inet filter input tcp flags & (fin|syn|rst|ack) == syn ct state new accept
nft add rule inet filter input tcp flags & (fin|syn) == (fin|syn) drop      # scan pattern
nft add rule inet filter input icmpv6 type { echo-request, nd-neighbor-solicit } accept
nft add rule inet filter forward ip dscp set cs1                            # also a match target
```

Connection tracking (see [[Netfilter#Connection Tracking|conntrack]]):

|Selector|Matches|
|---|---|
|`ct state`|new / established / related / invalid / untracked|
|`ct status`|internal flags such as `dnat`, `snat`|
|`ct mark`|the connection mark (persists for the flow)|
|`ct count`|number of concurrent connections (with a limit)|
|`ct original` / `ct reply`|a per-direction tuple field, e.g. `ct original daddr` is the pre-DNAT destination|

```bash
nft add rule inet filter input ct state invalid drop
nft add rule inet filter input tcp dport 22 ct state new ct count over 10 drop
nft add rule inet filter forward ct status dnat accept        # only translated flows
nft add rule inet filter forward ct mark 0x1 accept
nft add rule inet filter forward ct original daddr 203.0.113.7 counter   # pre-DNAT address
```

Two further expressions query kernel state rather than fields in the packet:

|Expression|Matches|
|---|---|
|`fib <keys> <result>`|the result of a routing-table lookup, used for reverse-path / anti-spoofing checks (see [[Netfilter#Anti-Spoofing with fib]])|
|`socket`|properties of the local socket a packet belongs to, e.g. `socket transparent 1` for [[Netfilter#Transparent Proxying (TPROXY)]]|

Strict reverse-path filtering, working for IPv4 and IPv6 alike, is a single `fib` rule:

```bash
nft add rule inet filter prerouting fib saddr . iif oif missing drop
```

## Verdict Statements

Verdict statements decide what happens to the packet. The terminal ones map to [[Netfilter#Kernel Verdicts|kernel verdicts]]; the rest steer evaluation.

|Verdict|Terminal?|Effect|
|---|---|---|
|`accept`|yes (this chain)|let the packet pass this chain (other chains on the hook still run)|
|`drop`|yes|discard silently, no reply|
|`reject`|yes|discard and send an error (ICMP / TCP RST)|
|`queue`|yes|hand the packet to userspace via [[Netfilter#NFQUEUE]]|
|`continue`|no|keep evaluating the next rule|
|`return`|no|leave the current chain — back to the caller from a [[#Regular Chains\|regular chain]]|
|`jump <chain>`|no|enter a chain; `return` comes back here|
|`goto <chain>`|no|enter a chain; does not return — the caller's context is replaced|

```bash
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;

        tcp dport 443 accept                          # pass this chain
        tcp dport 23 drop                             # silent discard
        tcp dport 25 reject with tcp reset            # RST back to the sender
        udp dport 137 reject with icmpx type port-unreachable
        meta mark 0x10 queue num 0-3 flags fanout,bypass   # to userspace

        ip protocol tcp jump  tcp-services            # comes back here afterwards
        ip protocol udp goto  udp-services            # never comes back
        counter                                       # reached only after a jump returns
    }

    chain tcp-services {
        tcp dport 22 accept
        return                                        # back to input, after the jump
    }

    chain udp-services {
        udp dport 53 accept
        # ending here does not resume input: policy drop applies, as if we were still there
    }
}
```

> [!note] reject is technically separate 
> 
> The strict verdict statements are `accept`, `drop`, `queue`, `continue`, `return`, `jump` and `goto`. `reject` is a separate terminating statement that drops the packet and additionally sends an error reply, so it behaves like a verdict in practice. It is only valid in the input, forward and output hooks (where a reply can sensibly be generated). The reply type is selectable with `reject with` — `reject with tcp reset` sends a TCP RST, and `reject with icmpx type admin-prohibited` sends a family-independent ICMP/ICMPv6 error.

The `queue` verdict can target a specific queue or a range — `queue num 0-3` spreads packets across several userspace readers (add `flags fanout` to keep each flow on one queue), and `queue flags bypass` lets a packet be accepted instead of dropped when no program is listening.

`accept` is only final for the current base chain. A packet accepted in a [[Netfilter#Prerouting|prerouting]] chain still continues to the next hook — and to any other base chains registered on the same hook at a later priority; it is not a global pass. Only `drop` ends a packet's journey everywhere.

The difference between `jump` and `goto` is the return path. After a `jump`, a `return` (or the chain ending) brings you back to the statement after the jump. After a `goto`, a `return` does not come back; it behaves as if you had been in the target chain all along.

![[nftables-jump-vs-goto.png]]

## Other Statements

Besides verdicts, a rule can carry non-terminal action statements that change state or hand the packet elsewhere, then continue. Most are thin wrappers over a [[Netfilter]] subsystem.

|Statement|Does|Subsystem|
|---|---|---|
|`counter`|count packets and bytes|[[Netfilter#Counters and Quotas]]|
|`log`|log to kernel ring buffer, or `log group N` to NFLOG|[[Netfilter#Kernel Logging]]|
|`limit rate …`|match only while under a rate (rate limiting)|—|
|`dnat to` / `snat to`|rewrite destination / source|[[Netfilter#Network Address Translation]]|
|`masquerade` / `redirect`|dynamic SNAT / DNAT-to-local|[[Netfilter#Masquerade]]|
|`tproxy to`|deliver to a local socket without rewriting the destination|[[Netfilter#Transparent Proxying (TPROXY)]]|
|`meta mark set` / `ct mark set`|tag the packet / the connection|[[Netfilter#Packet and Connection Marks]]|
|`ip dscp set` / `ip ttl set` / `ip6 hoplimit set`|rewrite header fields in place (QoS class, TTL / hop limit)|[[Netfilter#Rewriting Header Fields\|mangling]]|
|`tcp option maxseg size set`|clamp the TCP MSS (e.g. `… set rt mtu`)|[[Netfilter#MSS Clamping\|MSS clamping]]|
|`notrack`|skip [[Netfilter#Connection Tracking\|conntrack]] for this packet (use at `raw`)|conntrack|
|`flow add @ft`|offload an established flow to a [[#Flowtables]]|[[#Flowtables]]|
|`dup to`|send a copy of the packet elsewhere|—|
|`fwd to`|forward the frame to another interface (netdev only)|—|
|`synproxy`|answer TCP handshakes with SYN cookies to absorb SYN floods|[[Netfilter#Mitigating Floods]]|

```bash
# log new SSH connections, count them, then accept
nft add rule inet filter input tcp dport 22 ct state new \
    log prefix "SSH-NEW: " counter accept

# rate-limit new connections, dropping the excess
nft add rule inet filter input ct state new limit rate 20/second accept
nft add rule inet filter input ct state new drop

# port-forward and masquerade (NAT)
nft add rule ip nat prerouting tcp dport 80 dnat to 192.168.1.10:8080
nft add rule ip nat postrouting oif "eth0" masquerade
```

More of them in context — marking, mangling, mirroring and skipping conntrack:

```bash
# tag a connection once, then match the cheap packet mark on every later packet
nft add rule inet filter forward tcp dport 443 ct mark set 0x1
nft add rule inet mangle output ct mark 0x1 meta mark set ct mark

# rewrite header fields in place
nft add rule inet mangle forward ip dscp set af41            # QoS class for video
nft add rule inet mangle output  ip ttl set 64               # normalise the TTL

# skip conntrack entirely for high-volume unlogged traffic (raw priority)
nft add rule inet raw prerouting udp dport 123 notrack

# copy matching packets to a monitoring host, and keep evaluating
nft add rule inet filter input tcp dport 80 dup to 192.0.2.99 device "eth1"

# absorb a SYN flood with kernel-side SYN cookies
nft add rule inet filter input tcp flags syn tcp dport 80 synproxy mss 1460 wscale 7
```

A `limit` can also permit short bursts above the average rate — `limit rate 20/second burst 50 packets` — so brief legitimate spikes are not dropped.

The NAT statements above only take effect in a [[#Chain Types|nat-type]] chain at the right hook; the mechanics are described in [[Netfilter#Network Address Translation]]. In an [[#inet (dual-stack)|inet]] table the NAT statement must additionally name its family — `dnat ip to …` / `dnat ip6 to …` — because a dual-stack chain cannot infer which protocol the translation address belongs to. The `tproxy` statement additionally needs a policy-routing rule that delivers marked packets to the loopback — the full recipe is in [[Netfilter#Transparent Proxying (TPROXY)]].

---

# Sets, Maps and Dictionaries

_Native data structures that keep rulesets short and lookups fast._

> [!note] Prefer sets and maps to long rule lists 
> 
> A chain of rules is evaluated one after another, while a set or map is a single hash lookup. Matching many addresses or ports against a [[#Sets|set]], or dispatching with a verdict [[#Maps|map]], is both faster and shorter than writing a rule per value — reach for them whenever a list starts to grow.

## Sets

A set holds many values of one type and is matched in a single rule. An anonymous set is written inline (`tcp dport { 22, 80, 443 }`) and dies with its rule; a named set exists independently and can be changed live without reloading.

```bash
nft add set inet filter blocklist { type ipv4_addr \; flags interval \; }
nft add element inet filter blocklist { 10.0.0.0/8, 192.0.2.55 }
nft add rule inet filter input ip saddr @blocklist drop
```

Set behaviour is controlled by flags and options:

- `flags interval` lets the set store ranges and CIDR prefixes, not just single values.
- `flags timeout` (with `timeout 1h`) expires elements automatically.
- `flags dynamic` allows the ruleset itself to add elements (see [[#Dynamic Sets and Rate Limiting]]).
- a concatenated type (`type ipv4_addr . inet_service`) keys on a tuple, e.g. address-and-port together.
- `size N` caps the number of elements, worth setting on a [[#Dynamic Sets and Rate Limiting|dynamic set]] so it cannot grow without bound.
- `elements = { … }` inside the definition pre-populates the set when the ruleset loads.
- `auto-merge` (on interval sets) merges adjacent or overlapping elements on insertion instead of rejecting them.

Each of those options in a single table:

```bash
table inet filter {
    set admins {                                # plain set, pre-populated at load
        type ipv4_addr
        elements = { 10.0.0.5, 10.0.0.6 }
    }

    set blocklist {                             # ranges and prefixes, merged on insert
        type ipv4_addr
        flags interval
        auto-merge
        elements = { 192.0.2.0/24, 198.51.100.10-198.51.100.20 }
    }

    set tarpit {                                # elements expire on their own
        type ipv6_addr
        flags timeout
        timeout 1h
        size 4096
    }

    set services {                              # concatenated key: address and port together
        type ipv4_addr . inet_service
        elements = { 10.0.0.5 . 22, 10.0.0.6 . 3306 }
    }

    chain input {
        type filter hook input priority filter; policy drop;
        ip  saddr @blocklist drop
        ip6 saddr @tarpit    drop
        ip  saddr . tcp dport @services accept
        ip  saddr @admins tcp dport 22 accept
        tcp dport { 80, 443 } accept            # anonymous set: lives and dies with this rule
    }
}
```

Named sets can be edited while the ruleset runs, which is what makes them the right home for a blocklist that a script or daemon maintains:

```bash
nft add    element inet filter blocklist { 203.0.113.9 }
nft delete element inet filter blocklist { 203.0.113.9 }
nft list   set     inet filter blocklist
nft flush  set     inet filter blocklist
```

## Maps

A map associates a key with a value. A verdict map (`vmap`) maps keys directly to [[#Verdict Statements|verdicts]], collapsing many rules into one lookup; other maps can return data such as a NAT target.

```bash
# dispatch by destination port to a verdict
nft add rule inet filter input tcp dport vmap { 22 : accept, 25 : drop, 80 : accept }

# map an external port to an internal host:port for DNAT
nft add rule ip nat prerouting dnat to tcp dport map { 80 : 192.168.1.10, 443 : 192.168.1.11 }
```

Like sets, maps can be named and edited live, and their values can be verdicts, addresses, marks or `jump` targets:

```bash
table inet filter {
    map port_verdict {                       # verdict map, keyed on port
        type inet_service : verdict
        elements = { 22 : jump ssh-rules, 25 : drop, 80 : accept, 443 : accept }
    }

    map iface_mark {                         # data map: interface name to a mark value
        type ifname : mark
        elements = { "eth0" : 0x1, "wg0" : 0x2 }
    }

    chain input {
        type filter hook input priority filter; policy drop;
        meta mark set iifname map @iface_mark      # look up a value and use it
        tcp dport vmap @port_verdict               # look up a verdict and obey it
    }

    chain ssh-rules {
        ct state new limit rate 10/minute accept
    }
}
```

```bash
nft add element inet filter port_verdict { 8080 : accept }   # extend the dispatch live
```

A vmap that finds no matching key simply falls through to the next rule, so a `vmap` is not itself a terminal statement — the verdict it returns is.

## Dynamic Sets and Rate Limiting

A dynamic set is populated by the ruleset as packets arrive, which makes per-source tracking possible — the basis of connection-rate limiting and automated blocklists. The set must be declared with `flags dynamic` before a rule can add to it (a `timeout` and `size` keep it from growing stale or unbounded):

```bash
nft add set inet filter flooders \
    { type ipv4_addr \; flags dynamic \; timeout 10m \; size 65536 \; }

# drop sources opening more than 10 new connections a minute
nft add rule inet filter input ct state new \
    add @flooders { ip saddr limit rate over 10/minute } drop
```

The same idea in file form, and the two-stage variant that turns a rate breach into a lasting block:

```bash
table inet filter {
    set flooders {
        type ipv4_addr
        flags dynamic
        timeout 10m
        size 65536
    }

    set banned {                     # plain timeout set, filled by the rule below
        type ipv4_addr
        flags timeout
        timeout 24h
        size 65536
    }

    chain input {
        type filter hook input priority filter; policy drop;

        ip saddr @banned drop                                   # cheap check, first
        iif lo accept
        ct state established,related accept

        ct state new add @flooders { ip saddr limit rate over 10/minute } \
            add @banned { ip saddr } log prefix "BANNED: " drop
        ct state new accept
    }
}
```

```bash
nft list set inet filter banned      # inspect current members and their remaining timeouts
```

> [!note] `meter` is the legacy spelling 
> 
> Older rulesets used a `meter { … }` wrapper; current nftables expresses the same idea by updating a named dynamic set from the rule, as above.

---

# Stateful Objects

_Named objects that hold state independently of any single rule, referenced by name._

## Counters and Quotas

A named `counter` accumulates across every rule that references it; a `quota` trips once a byte total is crossed, enabling usage-based rules.

```bash
table inet filter {
    counter http-bytes { }
    quota monthly { over 100 gbytes }

    chain input {
        type filter hook input priority filter; policy drop;
        tcp dport 80 counter name "http-bytes" accept
        oif "eth0" quota name "monthly" drop
    }
}
```

Because the object lives beside the rules rather than inside one, several rules can feed the same counter, and its value survives rule edits:

```bash
table inet filter {
    counter web-total { }

    chain input {
        type filter hook input priority filter; policy drop;
        tcp dport 80  counter name "web-total" accept    # both rules
        tcp dport 443 counter name "web-total" accept    # feed one counter
    }
}
```

```bash
nft list counters                       # current packet/byte totals
nft reset counter inet filter web-total # read and zero in one step
nft list quotas                         # how much of each quota is consumed
```

A quota is one-directional: once `over 100 gbytes` is reached it matches from then on, so the rule above starts dropping. Add `used 0 bytes` to a redefinition, or reload the object, to reset it.

## Connection-Tracking Objects

These objects configure [[Netfilter#Connection Tracking|conntrack]] behaviour and are then attached to traffic by a rule.

- `ct helper` — enables a protocol [[Netfilter#Helpers and Expectations|helper]] for matched control traffic (helpers are off by default on modern kernels, so this is how you turn one on).
- `ct timeout` — applies custom per-state timeouts to selected flows.
- `ct expectation` — pre-declares an expected related connection.

```bash
table inet filter {
    ct helper ftp-standard {
        type "ftp" protocol tcp
    }
    chain prerouting {
        type filter hook prerouting priority filter; policy accept;
        tcp dport 21 ct helper set "ftp-standard"
    }
}
```

The corresponding kernel module still has to be present — `nf_conntrack_ftp` here, plus `nf_nat_ftp` if the helped traffic is NATed; the object only assigns the helper to flows.

A `ct timeout` object overrides the global conntrack timeouts for the flows a rule attaches it to — useful for long-lived database or SSH sessions that would otherwise be evicted from the table while idle:

```bash
table inet filter {
    ct timeout long-lived {
        protocol tcp
        l3proto ip
        policy = { established: 24h, close_wait: 12s, close: 4s }
    }
    chain output {
        type filter hook output priority filter; policy accept;
        tcp dport 3306 ct timeout set "long-lived"
    }
}
```

A `ct expectation` pre-declares a related connection instead of relying on a helper to parse it out of the control stream — the same effect a helper achieves, but stated by the administrator:

```bash
table inet filter {
    ct expectation ftp-data {
        protocol tcp
        dport 20
        timeout 1h
        size 2
        l3proto ip
    }
    chain prerouting {
        type filter hook prerouting priority filter; policy accept;
        tcp dport 21 ct expectation set "ftp-data"
    }
}
```

Traffic matched by an expectation arrives as `ct state related`, so a chain that already accepts `established,related` needs no further rule for it.

## Flowtables

A flowtable defines the [[Netfilter#Flow Offload|fast path]] for established forwarded connections. After the first packets establish the flow, a `flow add @name` statement moves it onto the flowtable, and its later packets bypass normal chain traversal — which also means they skip any counters or log rules in the forward chain.

```bash
table inet filter {
    flowtable f {
        hook ingress priority 0
        devices = { eth0, eth1 }
        # flags offload      # add for hardware offload on capable NICs
    }
    chain forward {
        type filter hook forward priority filter; policy drop;
        meta l4proto { tcp, udp } ct state established flow add @f
        ct state established,related accept
    }
}
```

Offloading selectively is the usual pattern: send only the bulk flows down the fast path and keep everything else visible to the forward chain.

```bash
table inet filter {
    flowtable fastpath {
        hook ingress priority filter
        devices = { eth0, eth1 }
    }
    chain forward {
        type filter hook forward priority filter; policy drop;
        iifname "eth1" oifname "eth0" tcp dport { 80, 443 } \
            ct state established flow add @fastpath      # bulk web traffic, offloaded
        ct state established,related counter accept      # everything else, still counted
        ct state new accept
    }
}
```

```bash
nft list flowtables      # which devices each flowtable is attached to
```

---

# Scripting and Syntax

_Writing rulesets as maintainable files rather than long command sequences._

## Variables and Includes

A ruleset file can define variables and pull in other files, which keeps large configurations readable.

```bash
#!/usr/sbin/nft -f

define wan = "eth0"
define admins = { 10.0.0.5, 10.0.0.6 }

include "/etc/nftables.d/*.nft"

table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        iifname $wan tcp dport 22 ip saddr $admins accept
    }
}
```

The leading shebang lets the file be executed directly; `nft` reads the whole file as one [[#Atomic Loading|atomic]] transaction.

## Data Types and Intervals

Values can be written in natural forms: addresses and CIDR prefixes (`192.0.2.0/24`), ranges (`1024-2048`, `192.0.2.10-192.0.2.20`), named services (`ssh`), time units (`30s`, `1h`), and data sizes (`10 mbytes`). Negation with `!=` and set membership with `{ … }` work across these types.

```bash
nft add rule inet filter input tcp dport 1024-2048 accept              # port range
nft add rule inet filter input tcp dport ssh accept                    # named service
nft add rule inet filter input ip saddr 192.0.2.10-192.0.2.20 accept   # address range
nft add rule inet filter input ip saddr != 192.0.2.0/24 drop           # negation
nft add rule inet filter input ip saddr { 10.0.0.0/8, 192.0.2.55 } \
    tcp dport { ssh, http, https } accept                              # membership

nft add set   inet filter recent { type ipv4_addr \; flags dynamic \; timeout 30s \; }
nft add quota inet filter cap    { over 10 mbytes }
```

## JSON and Monitoring

`nft` speaks JSON for automation, and can stream live events.

```bash
nft -j list ruleset            # machine-readable JSON dump
nft monitor                    # watch ruleset changes as they happen
```

---

# Operating nftables

_Loading, inspecting, persisting and debugging rules in day-to-day use._

## Managing the Ruleset

_Everything goes through the single `nft` command; file loads are applied atomically._

### Atomic Loading

Loading a file with `nft -f` is atomic: the whole file is parsed and committed in one transaction, so the kernel never runs a half-applied ruleset. A syntax error anywhere aborts the load and leaves the running ruleset untouched.

```bash
nft -f /etc/nftables.conf      # apply the whole file as one transaction
nft -c -f /etc/nftables.conf   # check syntax only, change nothing
```

> [!important] `nft -f` is additive, not a reset 
> 
> A file is layered on top of whatever is already loaded; it does not clear the existing ruleset first. To make a file fully replace the running configuration — the usual intent for `/etc/nftables.conf` — begin it with `flush ruleset`, which is why the complete configs in this note open with that line. Note that `flush ruleset` also discards state: counters reset and dynamic-set contents are lost on every reload.

### Inspecting

```bash
nft list ruleset               # everything currently loaded
nft -s list ruleset            # stateless dump (no counters); ideal for diffs and version control
nft list tables                # just the table names
nft list table inet filter     # one table with its chains and rules
nft -a list ruleset            # show rule handles (needed for deletion)
nft reset counters             # zero every counter (likewise: nft reset quotas)
```

### Modifying Live

Objects can be added or removed without reloading the whole ruleset. Deleting a specific rule needs its handle, obtained with `-a` (see [[#Anatomy of a Rule]]).

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
nft destroy table inet filter       # like delete, but no error if it is already gone
```

`destroy` (nftables 1.0.7 with kernel 6.3 or later) is the script-friendly counterpart to `delete`: it succeeds whether or not the object exists, so a teardown script need not guard against a missing table.

### Persistence

The running ruleset lives only in kernel memory and is lost on reboot. Snapshot it to the distribution's config file and enable the service so it is restored at boot.

```bash
nft list ruleset > /etc/nftables.conf   # snapshot current state
systemctl enable --now nftables         # restore /etc/nftables.conf at boot
```

Two caveats. First, `nft list ruleset` prints only the ruleset — the snapshot contains neither the shebang nor a leading `flush ruleset`, so re-add `flush ruleset` at the top or the next load will be [[#Atomic Loading|additive]] instead of a replacement. Second, the file path is distribution policy: Debian and Arch use `/etc/nftables.conf`, while RHEL-family systems read `/etc/sysconfig/nftables.conf` (which by default includes files from `/etc/nftables/`).

The `nftables` service restores rules into the host (initial) [[Netfilter#Network Namespaces|namespace]] only. Rulesets for other namespaces need their own loading step, run after each namespace is created — for a container, that is normally the runtime's or the workload's responsibility, not the host service.

## Debugging and Tracing

To see exactly which rules a packet hits, tag it for tracing and watch the trace stream. The trace shows the packet entering each chain and the verdict at each step. Set the flag as early as possible (a chain at `raw` priority or earlier) if you want the trace to cover every chain the packet crosses.

```bash
# mark matching packets for tracing, then watch
nft add rule inet filter input ip saddr 10.0.0.5 meta nftrace set 1
nft monitor trace
```

Combine this with `nft -a list ruleset` to correlate trace output against rule handles. Tracing is one tool in the wider workflow for chasing down dropped packets; see [[Netfilter#Troubleshooting and Observability]].

---

# Migrating from iptables

_Moving an existing iptables setup onto the nftables engine._

Two implementations share the `iptables` command name: `iptables-legacy` drives the old kernel API directly, while `iptables-nft` accepts iptables syntax but writes [[Netfilter]] rules through `nf_tables`. Most current distributions default to `iptables-nft`, so legacy scripts already run on the modern engine; `iptables -V` shows which variant is active. The remaining work is converting the rules to native nftables syntax. The framework-side view of these variants is in [[Netfilter#iptables and Its Variants]].

The translation tools convert rules mechanically:

```bash
# translate a single rule
iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT
# -> nft add rule ip filter INPUT tcp dport 22 counter accept

# translate an entire saved ruleset
iptables-save | iptables-restore-translate -f /dev/stdin
```

> [!warning] Do not mix engines on one host 
> 
> Legacy `iptables` and `nft` rules can attach at the same [[Netfilter#Hooks and Packet Flow|hooks]] without being aware of each other, producing confusing results. Pick one engine and stay on it.

The biggest conceptual change is that iptables' fixed tables (`filter`, `nat`, `mangle`, `raw`) become ordinary [[#Tables|tables]] and [[#Chains|chains]] that you create yourself, with the old table semantics expressed through [[#Chain Types|chain types]] and [[#Hook and Priority|priorities]].

---

# Common Configurations

_Complete, adaptable rulesets for the scenarios a sysadmin meets most. Each is a starting point to tighten, not a drop-in._

## Stateful Host Firewall

_Deny inbound by default; allow loopback, return traffic and a few services._

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
        meta l4proto ipv6-icmp accept                  # ICMPv6 (required for IPv6)
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

> [!note] Match ICMPv6 with `meta l4proto`, not `ip6 nexthdr` 
> 
> `ip6 nexthdr icmpv6` reads only the first next-header field, so an ICMPv6 packet carrying any extension header slips past the rule — and with a drop policy, silently breaks neighbor discovery. `meta l4proto ipv6-icmp` matches the actual transport protocol regardless of extension headers.

## NAT Gateway

_A router that lets a private LAN reach the internet behind one public address._

Enable forwarding first (`net.ipv4.ip_forward = 1`, plus `net.ipv6.conf.all.forwarding = 1` for IPv6), then:

```bash
#!/usr/sbin/nft -f

flush ruleset

define wan = "eth0"
define lan = "eth1"

table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        iif lo accept
        ct state established,related accept
        iifname $lan accept                  # trust the LAN side (tighten as needed)
        ip protocol icmp accept
        meta l4proto ipv6-icmp accept
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
        tcp flags syn tcp option maxseg size set rt mtu   # clamp MSS to the path
        ct state established,related accept
        iifname $lan oifname $wan accept                  # LAN out to the internet
    }
}

table inet nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        oifname $wan masquerade
    }
}
```

The MSS-clamp line matters on PPPoE or tunnelled uplinks; the reasoning is in [[Netfilter#MSS Clamping]].

## Port Forwarding

_Publishing an internal service on the gateway's public address._

```bash
define pubip = 203.0.113.7

table inet nat {
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;
        ip daddr $pubip tcp dport 443 dnat ip to 192.168.1.10:443
    }
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        # hairpin: internal clients reaching the public address still get a working reply
        ip saddr 192.168.1.0/24 ip daddr 192.168.1.10 tcp dport 443 masquerade
    }
}

table inet filter {
    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state established,related accept
        ip daddr 192.168.1.10 tcp dport 443 ct state new accept   # permit the forwarded service
    }
}
```

Two details are easy to get wrong here. The DNAT rule matches on the public destination address rather than `iifname $wan`, so it also catches LAN clients connecting to the public address — a rule restricted to the WAN interface would never translate their packets, and hairpinning would silently fail. And because this is an [[#inet (dual-stack)|inet]] table, the statement is `dnat ip to`, naming the address family explicitly.

Because [[Netfilter#DNAT|DNAT]] runs before the forward chain, the forward rule matches the internal address. The postrouting line is [[Netfilter#Hairpin NAT|hairpin NAT]]: it rewrites the source of hairpinned connections to the gateway, so the server's reply returns via the gateway (which can un-DNAT it) instead of going directly to the LAN client, where the untranslated source address would be rejected.

## WireGuard Gateway

_The firewall rules for a WireGuard server. WireGuard's own configuration — keys, peers, `AllowedIPs`, `wg-quick` — is a separate topic and is not shown here; these are only the nftables rules that turn a WireGuard host into a working gateway._

```bash
#!/usr/sbin/nft -f

flush ruleset

define wan     = "eth0"
define wg      = "wg0"
define wg_port = 51820

table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        iif lo accept
        ct state established,related accept
        udp dport $wg_port accept           # WireGuard listen port
        iifname $wg accept                  # services offered to VPN peers
        tcp dport 22 ct state new accept
        ip protocol icmp accept
        meta l4proto ipv6-icmp accept
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
        tcp flags syn tcp option maxseg size set rt mtu   # clamp for the tunnel MTU
        ct state established,related accept
        iifname $wg oifname $wan accept     # peers out to the internet
        iifname $wg oifname $wg accept      # peer-to-peer within the VPN (optional)
    }
}

table inet nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        iifname $wg oifname $wan masquerade
    }
}
```

These let peers connect on the UDP listen port, route their traffic out (forward plus masquerade), and clamp the tunnel MSS. They can live in `nftables.conf`, or in `wg-quick`'s `PostUp` / `PostDown` if you prefer to tie them to the interface lifecycle. The rules deliberately match `wg0` by name (`iifname`), not by index (`iif`), because the interface only exists while the tunnel is up. Forwarding must be enabled, as for the [[#NAT Gateway|NAT gateway]].

## Brute-Force Throttling

_Rate-limiting new SSH connections per source with a [[#Dynamic Sets and Rate Limiting|dynamic set]]._

```bash
table inet filter {
    set ssh_throttle {
        type ipv4_addr
        flags dynamic
        timeout 1h
    }

    chain input {
        type filter hook input priority filter; policy drop;
        iif lo accept
        ct state established,related accept
        # more than 10 new SSH connections a minute from one source -> drop it
        tcp dport 22 ct state new \
            add @ssh_throttle { ip saddr limit rate over 10/minute } drop
        tcp dport 22 ct state new accept
    }
}
```

This throttles rather than bans: connection attempts above the rate are dropped, but as soon as a source falls back under 10 per minute its new connections pass again (the `timeout` only expires idle entries, it is not a ban duration). To turn offenders into a hard block, have the over-rate rule add the source to a second blocklist set with its own timeout and drop members of that set early in the chain. Note also that an `ipv4_addr` set tracks IPv4 sources only — SSH over IPv6 needs a parallel `ipv6_addr` set and rule.

> [!info] Reading order recap 
> 
> A packet hits a [[Netfilter#Hooks and Packet Flow|hook]], the [[#Base Chains|base chains]] on that hook run in [[Netfilter#Hook Priorities|priority]] order, rules are evaluated top to bottom, and the first terminal [[#Verdict Statements|verdict]] wins. If no rule terminates, the chain [[#Policy|policy]] applies. If the packet is accepted, it continues to the next hook along the [[Netfilter#Packet Traversal|traversal path]].