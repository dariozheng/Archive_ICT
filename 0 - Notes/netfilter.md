---
categories:
  - "[[Linux]]"
topic@linux:
tags:
icon: SiLinux
iconColor: "#000000"
---
<strong>Netfilter</strong> is a framework inside the <strong>Linux kernel</strong> that lets kernel code <mark style="background: #FFB8EBA6;">register callback functions at fixed points of the network stack</mark>, so packets can be inspected, modified, dropped, queued, or rerouted as they pass through. <strong>nftables</strong> is the userspace tool and ruleset language (`nft`) that programs this framework; everything you write with `nft` ends up controlling Netfilter at one of those points.

> [!info] The ecosystem
> 
> - Netfilter — the kernel framework: the hooks plus the subsystems (conntrack, NAT, logging).
> - nf_tables — the kernel module that evaluates your ruleset (a small bytecode machine).
> - nftables / `nft` — the project and the userspace command that compiles rules into nf_tables.
> - iptables-nft — a compatibility layer that accepts iptables syntax but writes nf_tables rules underneath.

nftables replaces the older iptables, ip6tables, arptables and ebtables tools, unifying them under one syntax and one in-kernel engine while reusing the same Netfilter hooks and subsystems.

# Hooks

_The fixed points in the kernel where Netfilter hands each packet to your rules._

<mark style="background: #FFB8EBA6;">For the IP layer (IPv4 and IPv6) there are five hooks</mark>, named `NF_INET_*` <mark style="background: #FFB8EBA6;">in the kernel</mark>. Every [[#Base Chains|base chain]] you create attaches to exactly one of them.

| Hook        | Kernel constant       | Triggered for                                      |
| ----------- | --------------------- | -------------------------------------------------- |
| Prerouting  | `NF_INET_PREROUTING`  | every incoming packet, before the routing decision |
| Input       | `NF_INET_LOCAL_IN`    | packets destined to the local host                 |
| Forward     | `NF_INET_FORWARD`     | packets being routed through the host              |
| Output      | `NF_INET_LOCAL_OUT`   | packets generated locally, leaving the host        |
| Postrouting | `NF_INET_POSTROUTING` | every outgoing packet, after the routing decision  |

## Prerouting

The first hook every incoming packet hits, right after basic sanity checks but before the kernel decides where the packet should go. Because it runs before routing, <mark style="background: #FFB8EBA6;">it is the only place you can change a packet's destination</mark> and still have it routed accordingly, which is why <mark style="background: #FF5582A6;">DNAT lives here</mark>.

## Input

Reached only after the routing decision concludes the <mark style="background: #FFB86CA6;">packet is addressed to this machine</mark>. This is where you filter traffic that terminates on the host itself (SSH to the box, a local web server).

## Forward

Reached when routing determines the <mark style="background: #FFB8EBA6;">packet must be passed on to another host</mark>, <mark style="background: #FF5582A6;">i.e. the box is acting as a router</mark>. Filtering for traffic passing through belongs here.

> [!warning] IP forwarding must be enabled 
> The Forward hook is only meaningfully traversed when the kernel is allowed to route between interfaces: `net.ipv4.ip_forward = 1` and `net.ipv6.conf.all.forwarding = 1`.

## Output

The first hook for <mark style="background: #FFB86CA6;">packets created by local processes</mark> (a reply from your web server, a DNS query from the host). It runs after an initial routing lookup the kernel needs in order to fill in source address and outgoing interface.

## Postrouting

<mark style="background: #FFF3A3A6;">The last hook before a packet leaves the machine, after routing is finalized</mark>. Since the destination is already chosen, <mark style="background: #BBFABBA6;">this is where SNAT and masquerade are applied</mark>.

# Hook Priorities

_How the kernel orders multiple chains that sit on the same hook._

<mark style="background: #FF5582A6;">Several functions</mark> <mark style="background: #FFB8EBA6;">can register on the same hook</mark>. <mark style="background: #BBFABBA6;">Their order is decided by an integer priority: lower numbers run first, and values can be negative</mark>. This is how the kernel guarantees defragmentation and connection tracking run before your filtering, and source NAT runs after it.

nftables exposes the common values as named <strong>keywords</strong> so you rarely write the numbers (ip / ip6 / inet families):

|Keyword|Value|Purpose|
|---|---|---|
|`raw`|-300|runs before conntrack (used for `notrack`)|
|`mangle`|-150|early packet mangling|
|`dstnat`|-100|destination NAT (prerouting)|
|`filter`|0|normal filtering — the default|
|`security`|50|SECMARK / MAC labelling|
|`srcnat`|100|source NAT (postrouting)|

> [!note] 
> Built-in stages run around your rules, Connection tracking registers at -200 and defragmentation at -400, so both always run before anything you write at `filter` priority.

The bridge family uses a different default scale (`dstnat` -300, `filter` -200, `srcnat` 300), so the same keyword maps to a different number depending on family.

![[netfilter-hook-priority.png]]

# Packet Traversal

_How a packet threads through the hooks, with the routing decision splitting the path._

The single most important fact: the routing decision sends a packet down one of two paths. It is either delivered locally (Input) or forwarded (Forward), never both.

```
Forwarded (transit) traffic:
   wire ──▶ PREROUTING ──▶ [route] ──▶ FORWARD ──▶ POSTROUTING ──▶ wire

Inbound to this host:
   wire ──▶ PREROUTING ──▶ [route] ──▶ INPUT ──▶ local socket

Outbound from this host:
   local socket ──▶ [route] ──▶ OUTPUT ──▶ POSTROUTING ──▶ wire
```

NAT positioning falls out of this naturally: change the destination before routing (DNAT in prerouting) and the source after routing (SNAT in postrouting).

![[netfilter-packet-flow 1.png]]

# Address Families

_Which protocol's packets a table sees, and which hooks are available to it._

Every nftables table belongs to an address family.

|Family|Scope|Notes|
|---|---|---|
|`ip`|IPv4 only|classic IPv4 filtering / NAT|
|`ip6`|IPv6 only|IPv6 equivalent|
|`inet`|IPv4 and IPv6|recommended default — one ruleset for both|
|`arp`|ARP packets|only `input` and `output` hooks|
|`bridge`|bridged L2 frames|replaces ebtables; for software bridges|
|`netdev`|per-interface raw packets|`ingress` (and `egress` on newer kernels), runs earliest|

The inet family is preferred for host and router firewalls because one rule can cover both IP versions, while protocol-specific matches (`ip saddr` vs `ip6 saddr`) still work inside it.

> [!note] netdev / ingress 
> The netdev family attaches a chain to a specific interface and runs at the `ingress` hook, before the normal prerouting path and before conntrack. It suits very high-performance early drops (anti-spoofing, DDoS scrubbing) because rejected packets never enter the rest of the stack.

# Tables

_Top-level containers; in nftables they carry no behavior of their own._

A table holds chains, sets, maps and other objects, and is identified by its family plus a name you choose.

```bash
nft add table inet filter      # create a dual-stack table
nft list ruleset               # show everything currently loaded
```

> [!important] Different from iptables
> In iptables the tables were fixed and predefined (`filter`, `nat`, `mangle`, `raw`). In nftables you create tables yourself, the names are arbitrary, and a table has no built-in meaning. What a chain does is decided by its type and hook, not by the table's name. An empty table simply does nothing.

# Chains

_Ordered lists of rules. Whether a chain is reached automatically depends on its kind._

## Base Chains

A base chain is wired into the Netfilter packet flow. It declares a type, a hook, a priority and a policy, and packets reach it automatically because it is registered at one of the hooks.

```bash
nft add chain inet filter input \
    { type filter hook input priority 0 \; policy drop \; }
```

## Regular Chains

A regular chain has no hook and is never entered on its own. It runs only when another chain jumps or goes to it, which makes it useful for grouping rules into reusable blocks.

```bash
nft add chain inet filter tcp-services          # regular chain, no hook
nft add rule inet filter input ip protocol tcp jump tcp-services
```

## Chain Types

The type of a base chain selects which Netfilter semantics apply.

|Type|Purpose|Valid hooks|
|---|---|---|
|`filter`|ordinary packet filtering|all hooks|
|`nat`|network address translation (conntrack-based)|prerouting, input, output, postrouting|
|`route`|trigger a fresh route lookup if routing-relevant fields (e.g. mark) changed|output only|

A `nat` chain only inspects the first packet of a connection; conntrack replays the same translation on every later packet, which is why NAT chains should not carry general filtering rules.

## Hook and Priority

A base chain must declare its hook (which of the five, or netdev/arp), its priority (usually a keyword from the table above), and its policy.

```bash
nft add chain inet nat postrouting \
    { type nat hook postrouting priority srcnat \; policy accept \; }
```

## Policy

The policy is the verdict applied to a packet that reaches the end of a base chain without hitting a terminating rule. It can only be `accept` or `drop`.

> [!warning] Default-drop and lockout 
> A `policy drop` on the input chain is the secure default, but loading it with no allow rules can lock you out. Always permit loopback and established traffic first.

```bash
nft add rule inet filter input iif lo accept
nft add rule inet filter input ct state established,related accept
```

A regular chain has no policy. When it ends without a verdict, control simply returns to the caller as if `return` had been issued.

---

# Rules, Statements and Verdicts

_A rule is statements evaluated left to right; the verdict decides the packet's fate._

## Match Statements

Match statements (expressions) test packet fields. If any test fails, the rest of the rule is skipped and evaluation moves to the next rule.

|Selector|Matches|
|---|---|
|`ip saddr` / `ip daddr`|IPv4 source / destination address|
|`ip6 saddr` / `ip6 daddr`|IPv6 source / destination address|
|`tcp dport` / `udp dport`|transport destination port|
|`tcp flags`|TCP flags (e.g. `syn`, `rst`)|
|`ct state`|connection-tracking state|
|`iif` / `oif`|input / output interface by index (fast)|
|`iifname` / `oifname`|input / output interface by name (supports wildcards like `eth*`)|
|`meta l4proto`|layer-4 protocol, IP-version-agnostic|
|`meta mark` / `ct mark`|packet mark / connection mark|
|`ether saddr`|source MAC address (bridge / netdev)|

## Verdict Statements

Verdict statements decide what happens to the packet.

| Verdict        | Terminal?        | Effect                                                            |
| -------------- | ---------------- | ----------------------------------------------------------------- |
| `accept`       | yes (this chain) | let the packet pass this hook                                     |
| `drop`         | yes              | discard silently, no reply                                        |
| `reject`       | yes              | discard and send an error (ICMP / TCP RST)                        |
| `queue`        | yes              | hand the packet to userspace via NFQUEUE                          |
| `continue`     | no               | keep evaluating the next rule                                     |
| `return`       | no               | leave the current chain (base chain then applies its policy)      |
| `jump <chain>` | no               | enter a chain; `return` comes back here                           |
| `goto <chain>` | no               | enter a chain; does not return — the caller's context is replaced |
|                |                  |                                                                   |

> [!note] reject is technically separate 
> The strict verdict statements are `accept`, `drop`, `queue`, `continue`, `return`, `jump` and `goto`. `reject` is a separate terminating statement that drops the packet and additionally sends an error reply, so it behaves like a verdict in practice.

`accept` is only final for the current base chain. A packet accepted in a prerouting chain still continues to the next hook; it is not a global pass.

The difference between `jump` and `goto` is the return path. After a `jump`, a `return` (or the chain ending) brings you back to the statement after the jump. After a `goto`, a `return` does not come back; it behaves as if you had been in the target chain all along.

A rule may also carry non-verdict actions that change state without ending evaluation, such as `counter`, `log`, `meta mark set` or `ct mark set`, followed by a verdict.

```bash
nft add rule inet filter input tcp dport 22 ct state new \
    log prefix "SSH-NEW: " counter accept
```

---

# Connection Tracking

_The subsystem that records connection state and turns the filter from stateless into stateful._

Conntrack runs early (priority -200, before your filter chains) and is the foundation for NAT. Without it you would have to manually allow the return traffic of every connection.

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

> [!note] Helpers for dynamic-port protocols 
> Protocols like FTP, SIP and TFTP open secondary connections on dynamic ports. Conntrack helpers parse the control channel and create an expectation so the data connection matches `ct state related`. On modern kernels automatic helper assignment is disabled for security; you attach a helper explicitly with a `ct helper` object and a rule that assigns it to the control traffic.

---

# NAT

_Rewriting source or destination addresses, built on top of conntrack._

The translation is decided on the first packet of a flow and replayed for the rest.

## DNAT — Destination NAT

Changes the destination, so it must run in prerouting (or output for locally generated traffic) where the new destination still affects routing. Used for port forwarding and publishing internal servers.

```bash
nft add rule inet nat prerouting tcp dport 80 dnat to 192.168.1.10:8080
```

## SNAT — Source NAT

Changes the source, so it must run in postrouting, after routing has chosen the outgoing interface.

```bash
nft add rule inet nat postrouting oif eth0 snat to 203.0.113.5
```

## Masquerade

A dynamic form of SNAT that uses the outgoing interface's current IP automatically, ideal when the WAN address is assigned by DHCP or PPP. Slightly more costly than static SNAT because the address is resolved per connection.

```bash
nft add rule inet nat postrouting oif eth0 masquerade
```

## Redirect

A special DNAT that sends the packet to the local machine itself (the incoming interface's address), commonly used for transparent proxies.

```bash
nft add rule inet nat prerouting tcp dport 80 redirect to :3128
```

> [!note] NAT chain placement 
> Because NAT is conntrack-driven, keep one nat-type base chain per relevant hook — a prerouting chain at `dstnat` priority for DNAT and a postrouting chain at `srcnat` priority for SNAT — and leave general filtering in separate filter chains.

---

# Sets, Maps and Dictionaries

_Native data structures that keep rulesets short and lookups fast._

## Sets

A set holds many values of one type (addresses, ports, interfaces) and is matched in a single rule.

```bash
nft add set inet filter blocklist { type ipv4_addr \; flags interval \; }
nft add element inet filter blocklist { 10.0.0.0/8, 192.0.2.55 }
nft add rule inet filter input ip saddr @blocklist drop
```

An anonymous set is written inline (`tcp dport { 22, 80, 443 } accept`) and dies with its rule. A named set exists independently and can be changed live without reloading the ruleset, which is what makes it suitable for dynamic blocklists.

## Maps

A map associates a key with a value. A verdict map (`vmap`) maps keys directly to verdicts, collapsing many rules into one lookup.

```bash
nft add rule inet filter input tcp dport vmap { 22 : accept, 25 : drop, 80 : accept }
```

## Dynamic Sets and Rate Limiting

A set can be populated by the ruleset itself and combined with rate limits to track per-source behaviour, which is the basis for connection-rate limiting.

```bash
nft add rule inet filter input ct state new \
    meter ssh-flood { ip saddr limit rate 10/minute } accept
```

> [!note] `meter` is the legacy form 
> Current nftables expresses the same idea with a named dynamic set updated from the rule, e.g. `update @set { ip saddr limit rate 10/minute }`.

---

# Other Subsystems

_Logging, userspace handoff, and accounting that ride on the same hooks._

## Logging

The `log` statement sends packet metadata to the kernel log, or to userspace via nfnetlink_log. It is non-terminal, so pair it with a verdict.

```bash
nft add rule inet filter input ct state invalid log prefix "INVALID: " drop
```

## NFQUEUE

The `queue` verdict hands packets to a userspace program (via libnetfilter_queue) which then returns its own verdict. This is how IDS/IPS and deep-inspection tools plug in.

## Counters and Quotas

`counter` objects tally packets and bytes per rule; `quota` objects can trip once a byte threshold is crossed, enabling usage-based rules.

---

# Managing the Ruleset

_Day-to-day operation of nftables through the single `nft` command._

## Atomic Loading

Loading a file with `nft -f` is atomic: the whole file is parsed and committed in one transaction, so the kernel never runs a half-applied ruleset. A syntax error anywhere aborts the load and leaves the running ruleset untouched.

```bash
nft -f /etc/nftables.conf      # load (replace) atomically
nft -c -f /etc/nftables.conf   # check syntax only, change nothing
```

## Inspecting

```bash
nft list ruleset               # everything currently loaded
nft list tables                # just the table names
nft list table inet filter     # one table with its chains and rules
nft -a list ruleset            # show rule handles (needed for deletion)
```

## Modifying Live

Objects can be added or removed without reloading the whole ruleset. Deleting a specific rule needs its handle, obtained with `-a`.

```bash
nft add rule inet filter input tcp dport 8080 accept
nft -a list chain inet filter input            # find the handle
nft delete rule inet filter input handle 12    # delete that rule by handle
```

## Flushing and Deleting

```bash
nft flush ruleset                   # wipe everything
nft flush chain inet filter input   # empty one chain but keep it registered
nft delete chain inet filter input  # remove the chain
nft delete table inet filter        # remove the table and all it contains
```

## Persistence

The running ruleset lives only in kernel memory and is lost on reboot. Snapshot it to the distribution's config file and enable the service so it is restored at boot.

```bash
nft list ruleset > /etc/nftables.conf   # snapshot current state
systemctl enable --now nftables         # restore /etc/nftables.conf at boot
```

---

# Practical Skeleton

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

> [!info] Reading order recap 
> A packet hits a hook, the base chains on that hook run in priority order, rules are evaluated top to bottom, and the first terminal verdict wins. If no rule terminates, the chain policy applies. If the packet is accepted, it continues to the next hook along the traversal path.