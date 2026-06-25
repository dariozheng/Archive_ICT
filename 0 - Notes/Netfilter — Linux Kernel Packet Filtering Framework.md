---
categories:
  - "[[Linux]]"
topic@linux:
tags:
icon: SiLinux
iconColor: "#000000"
---
# Netfilter — Linux Kernel Packet Filtering Framework

> [!abstract] Summary 
> **Netfilter** is the packet filtering and manipulation framework built into the Linux kernel. It provides a series of **hooks** embedded at strategic points in the kernel's network stack where kernel modules can register callback functions to inspect, modify, or drop packets. All of Linux's stateful firewalling, NAT, connection tracking, and packet logging are built as Netfilter subsystems. Userspace tools such as `iptables`, `nftables`, `ipset`, and `nfqueue` interact with Netfilter through well-defined kernel interfaces.

---

## Table of Contents

**Framework Architecture**

- [[#Architecture Overview]]
- [[#Protocol Families and Hook Namespaces]]
- [[#Subsystems Built on Netfilter]]
- [[#Key Kernel Modules]]

**Hook System**

- [[#Hook Points and Packet Paths]]
    - [[#IPv4 Hook Points]]
    - [[#IPv6 Hook Points]]
    - [[#ARP Hook Points]]
    - [[#Bridge Hook Points]]
    - [[#Ingress and Egress Hooks (TC / netdev)]]
- [[#Hook Priorities]]
- [[#Hook Registration (Kernel API)]]
- [[#Netfilter Verdicts]]

**Packet Processing Paths**

- [[#IPv4 Packet Traversal]]
- [[#IPv6 Packet Traversal]]
- [[#Bridge Packet Traversal]]
- [[#Locally Generated Packets]]

**Userspace Interfaces**

- [[#Netlink and nfnetlink]]
- [[#NFQUEUE — Userspace Packet Processing]]
    - [[#NFQUEUE Setup]]
    - [[#NFQUEUE Copy Modes]]
    - [[#NFQUEUE Verdict with Modification]]
    - [[#NFQUEUE Limitations]]
- [[#NFLOG — Packet Logging to Userspace]]
- [[#libnetfilter Libraries]]

**Subsystems**

- [[#iptables]]
    - [[#iptables Tables and Chains]]
    - [[#iptables Rule Structure]]
    - [[#iptables Built-in Targets]]
    - [[#iptables Rule Matching Extensions]]
    - [[#ip6tables and arptables]]
- [[#nftables]]
    - [[#nftables Data Model]]
    - [[#nftables Expressions and Statements]]
    - [[#nftables Sets and Maps]]
    - [[#nftables Flowtables]]
    - [[#Migrating from iptables to nftables]]
- [[#ipset]]
    - [[#ipset Types]]
    - [[#ipset Commands]]
    - [[#ipset Timeout (Auto-expiry)]]
    - [[#ipset vs nftables Sets]]
- [[#Connection Tracking]]
- [[#NAT]]
    - [[#SNAT and Masquerade]]
    - [[#DNAT and Port Forwarding]]
    - [[#NAT Hairpinning]]

**Network Namespaces**

- [[#Netfilter and Network Namespaces]]

**Performance and Scaling**

- [[#Hook Overhead and Optimization]]
- [[#eBPF and XDP Integration]]

**Kernel Module Reference**

- [[#Netfilter Module Reference]]

**Debugging and Troubleshooting**

- [[#Debugging Netfilter]]
    - [[#TRACE Target (iptables)]]
    - [[#nftables Tracing]]
    - [[#Counting Drops by Chain]]
    - [[#Checking What Rules Are Active]]
- [[#Common Issues]]

**Advanced Targets**

- [[#SYNPROXY — SYN Flood Protection]]
- [[#TPROXY — Transparent Proxying]]

**Policy-Based Routing Integration**

- [[#Packet Marks and Policy Routing]]
- [[#CONNMARK and Multi-ISP Routing]]

**ebtables — Layer 2 Filtering**

- [[#ebtables Architecture]]
- [[#ebtables Tables and Chains]]
- [[#ebtables Match Extensions and Targets]]
- [[#ebtables and br_netfilter Interaction]]

**IPsec and xfrm Integration**

- [[#IPsec and Netfilter (xfrm)]]
    - [[#xfrm Hooks in the Packet Path]]
    - [[#Matching IPsec Policy in Firewall Rules]]

**Netfilter Accounting**

- [[#nfacct — Kernel Accounting Objects]]

**Security Table and MAC Integration**

- [[#The security Table and SELinux / AppArmor]]
    - [[#SECMARK Target]]
    - [[#CONNSECMARK Target]]

**Firewall Baselines and Rate Limiting**

- [[#Comprehensive nftables Firewall Baseline]]
- [[#Comprehensive iptables Firewall Baseline]]
- [[#Rate Limiting Patterns]]
    - [[#Per-Source Rate Limiting with hashlimit]]
    - [[#Dynamic Blocking with nftables Sets]]
    - [[#The recent Module]]

**Netfilter Internals**

- [[#nf_tables Bytecode Virtual Machine]]
- [[#x_tables Infrastructure (Legacy)]]

**Connection Limiting**

- [[#Connection Limiting (connlimit)]]

**Traffic Shaping and QoS**

- [[#Traffic Shaping and QoS Marks]]
    - [[#DSCP Marking]]
    - [[#Integration with tc (Traffic Control)]]

**IPv6-Specific Considerations**

- [[#IPv6-Specific Rules and Considerations]]
    - [[#ICMPv6 Requirements]]
    - [[#IPv6 Extension Header Matching]]
    - [[#IPv6 Address Types and Unique Concerns]]

**Docker and Container Networking**

- [[#Docker Networking Chains]]
    - [[#Docker Chain Architecture]]
    - [[#DOCKER-USER — Safe Customisation Point]]
    - [[#Docker IPv6 and conntrack]]
    - [[#Podman and Rootless Containers]]

**GeoIP and Country-Based Filtering**

- [[#GeoIP and Country-Based Filtering]]

**String and Payload Matching**

- [[#String and Payload Matching]]
    - [[#xt_string Match]]
    - [[#u32 Match — Raw Packet Inspection]]

**WireGuard and Netfilter**

- [[#WireGuard and Netfilter]]

**Fail2ban Integration**

- [[#Fail2ban Integration]]
    - [[#How Fail2ban Uses Netfilter]]
    - [[#Fail2ban with nftables]]

**Port Knocking**

- [[#Port Knocking with the recent Module]]

**OSF — Passive OS Fingerprinting**

- [[#OSF — Passive OS Fingerprinting]]

**VLANs, Tunnels, and Encapsulation**

- [[#VLANs, Tunnels, and Encapsulation]]
    - [[#VLAN (802.1Q) and Netfilter]]
    - [[#VXLAN and Overlay Networks]]
    - [[#GRE and IPIP Tunnels]]
    - [[#Bonding and Teams]]

**Testing and Validation**

- [[#Testing and Validating Firewall Rules]]
    - [[#hping3 — Crafted Packet Testing]]
    - [[#nmap — Port and State Scanning]]
    - [[#Scapy — Scriptable Packet Crafting]]
    - [[#Validating nftables Configuration Files]]
    - [[#Capturing Netfilter-Dropped Packets]]

---

## Architecture Overview

Netfilter is not a single monolithic firewall — it is a **framework of hooks** embedded in the Linux kernel's network processing path. Higher-level features (stateful firewalling, NAT, packet queuing to userspace) are **layered on top** as loadable kernel modules.

```
User Space
  ├── iptables(8) / ip6tables(8) / arptables(8)   → interact via setsockopt()
  ├── nft(8)                                        → interact via Netlink
  ├── ipset(8)                                      → interact via Netlink
  ├── conntrack(8)                                  → interact via nfnetlink
  └── libnetfilter_queue / libnetfilter_log         → NFQUEUE / NFLOG via Netlink

Kernel Space
  └── Netfilter Core (net/netfilter/)
        ├── Hook dispatcher
        │     ├── NFPROTO_IPV4 hooks
        │     ├── NFPROTO_IPV6 hooks
        │     ├── NFPROTO_ARP hooks
        │     ├── NFPROTO_BRIDGE hooks
        │     └── NFPROTO_NETDEV hooks (ingress/egress per device)
        ├── iptables subsystem
        │     ├── raw table
        │     ├── mangle table
        │     ├── nat table
        │     └── filter table
        ├── nftables subsystem
        │     ├── tables, chains, rules
        │     └── sets, maps, meters, flowtables
        ├── Conntrack subsystem  → [[Netfilter Conntrack — Connection Tracking]]
        ├── NAT subsystem (depends on conntrack)
        ├── NFQUEUE (packet hand-off to userspace)
        ├── NFLOG (packet logging to userspace)
        └── ipset (hash/bitmap set data structures)
```

Netfilter was introduced in Linux **2.4** (year 2000) as the replacement for `ipchains` (2.2) and `ipfwadm` (2.0). The core design — hooks + modules — has remained stable, while the userspace interface evolved from `iptables` to `nftables`.

---

## Protocol Families and Hook Namespaces

Netfilter defines separate **protocol family** hook namespaces. A hook registered for one family only fires on packets of that family.

|Family constant|Value|Covers|
|---|---|---|
|`NFPROTO_UNSPEC`|0|Unspecified / global|
|`NFPROTO_INET`|1|IPv4 + IPv6 combined (nftables `inet` family only)|
|`NFPROTO_IPV4`|2|IPv4|
|`NFPROTO_ARP`|3|ARP|
|`NFPROTO_NETDEV`|5|Per-device ingress/egress hooks|
|`NFPROTO_BRIDGE`|7|Bridge (Layer 2 frames)|
|`NFPROTO_IPV6`|10|IPv6|

> [!note] NFPROTO_INET The `inet` family is a **nftables-only abstraction** that multiplexes a single rule set over both IPv4 and IPv6. Internally, nftables creates two hooks (one per IP family) for each `inet` chain. It does not exist as a hook family in the kernel C API.

---

## Subsystems Built on Netfilter

|Subsystem|Module|Depends on|Purpose|
|---|---|---|---|
|Conntrack|`nf_conntrack`|Netfilter core|Stateful connection tracking|
|NAT|`nf_nat`|`nf_conntrack`|Address/port translation|
|iptables filter|`ip_tables`|Netfilter core|IPv4 packet filtering|
|iptables NAT|`iptable_nat`|`nf_nat`, `ip_tables`|IPv4 NAT rules|
|iptables mangle|`iptable_mangle`|`ip_tables`|Packet modification|
|nftables|`nf_tables`|Netfilter core|Next-gen rule framework|
|NFQUEUE|`nfnetlink_queue`|`nfnetlink`|Userspace packet processing|
|NFLOG|`nfnetlink_log`|`nfnetlink`|Userspace packet logging|
|ipset|`ip_set`|Netfilter core|Set-based matching|
|Flowtable|`nf_flow_table`|`nf_conntrack`|Fast-path bypass for ESTABLISHED flows|

---

## Key Kernel Modules

|Module|Purpose|
|---|---|
|`x_tables`|Shared infrastructure for iptables / ip6tables / arptables / ebtables|
|`ip_tables`|iptables core (IPv4)|
|`ip6_tables`|ip6tables core (IPv6)|
|`iptable_filter`|`filter` table for iptables|
|`iptable_nat`|`nat` table for iptables|
|`iptable_mangle`|`mangle` table for iptables|
|`iptable_raw`|`raw` table for iptables|
|`nf_tables`|nftables core|
|`nft_compat`|Compatibility layer to use iptables match/target extensions from nftables|
|`nf_conntrack`|Connection tracking core → [[Netfilter Conntrack — Connection Tracking]]|
|`nf_nat`|NAT core|
|`nfnetlink`|Netlink family for Netfilter (transport for conntrack, NFQUEUE, NFLOG)|
|`nfnetlink_queue`|NFQUEUE — queue packets to userspace|
|`nfnetlink_log`|NFLOG — log packets to userspace|
|`ip_set`|ipset core|
|`ip_set_hash_ip`|ipset `hash:ip` type|
|`ip_set_hash_net`|ipset `hash:net` type|
|`ip_set_hash_ipport`|ipset `hash:ip,port` type|
|`ip_set_bitmap_ip`|ipset `bitmap:ip` type|
|`ip_set_list_set`|ipset `list:set` type|
|`br_netfilter`|Enable Netfilter IPv4/IPv6 hooks on bridge devices|
|`nf_flow_table`|Software flowtable fast path|
|`nf_flow_table_hw`|Hardware offload extension for flowtables|

---

## Hook Points and Packet Paths

### IPv4 Hook Points

The five standard Netfilter hook points for IPv4 (and IPv6, using the same constants):

|Hook|Value|Position in the network stack|
|---|---|---|
|`NF_INET_PRE_ROUTING`|0|Immediately after NIC reception, before routing decision|
|`NF_INET_LOCAL_IN`|1|After routing: packet destined for a local socket|
|`NF_INET_FORWARD`|2|After routing: packet to be forwarded to another interface|
|`NF_INET_LOCAL_OUT`|3|Packet generated by a local socket, before routing|
|`NF_INET_POST_ROUTING`|4|After routing, immediately before NIC transmission|

```
Incoming packet (from NIC)
        │
        ▼
[NF_INET_PRE_ROUTING]        ← raw table · conntrack lookup · DNAT
        │
        ├──── Routing decision ──────────────────────────────────────────┐
        │                                                                  │
        │  (destined for local process)          (to be forwarded)        │
        ▼                                                ▼                │
[NF_INET_LOCAL_IN]                          [NF_INET_FORWARD]            │
        │                                                │                │
        ▼                                                ▼                │
  Local sockets                               [NF_INET_POST_ROUTING]     │
                                                         │                │
                                                         ▼                │
                                                    Outgoing NIC          │
                                                                          │
Locally generated packet                                                  │
        │                                                                  │
        ▼                                                                  │
[NF_INET_LOCAL_OUT]          ← raw table · conntrack · DNAT for local    │
        │                                                                  │
        └──────────────── Routing decision ──────────────────────────────►│
                                                                          ▼
                                                          [NF_INET_POST_ROUTING]
                                                                  ← SNAT / Masquerade
                                                                  ← conntrack confirm
                                                                          │
                                                                          ▼
                                                                     Outgoing NIC
```

### IPv6 Hook Points

IPv6 uses the same five `NF_INET_*` constants, registered under `NFPROTO_IPV6`. The packet traversal path is structurally identical to IPv4. `ip6tables` operates here. Fragmentation uses `nf_defrag_ipv6` instead of `nf_defrag_ipv4`.

### ARP Hook Points

|Hook|Constant|Description|
|---|---|---|
|`NF_ARP_IN`|0|Incoming ARP packet|
|`NF_ARP_OUT`|1|Outgoing ARP packet|
|`NF_ARP_FORWARD`|2|ARP being forwarded (bridge proxy ARP)|

`arptables` registers at these hook points under `NFPROTO_ARP`.

### Bridge Hook Points

Bridge hooks fire on Ethernet frames traversing a Linux bridge device (`NFPROTO_BRIDGE`). `ebtables` uses these.

|Hook|Constant|Description|
|---|---|---|
|`NF_BR_PRE_ROUTING`|0|Frame received on bridge port, before forwarding decision|
|`NF_BR_LOCAL_IN`|1|Frame destined for the bridge device itself|
|`NF_BR_FORWARD`|2|Frame being forwarded through the bridge|
|`NF_BR_LOCAL_OUT`|3|Frame generated by the bridge (e.g., STP BPDUs)|
|`NF_BR_POST_ROUTING`|4|Frame leaving a bridge port|
|`NF_BR_BROUTING`|5|Decision: bridge or route? (ebtables BROUTE chain)|

> [!note] With `br_netfilter` loaded, bridged IP traffic additionally passes through the standard `NFPROTO_IPV4/IPV6` hooks, making iptables/nftables/conntrack visible to it. See [[Netfilter Conntrack — Connection Tracking#Bridge Networking and nf_conntrack_bridge]].

### Ingress and Egress Hooks (TC / netdev)

Since Linux 4.2, nftables can attach chains to the **TC ingress** hook — earlier than `NF_INET_PRE_ROUTING`. Since Linux 5.16, a symmetric **egress** hook was added. These belong to `NFPROTO_NETDEV` and are bound to a specific network device.

```nftables
table netdev filter {
    chain ingress {
        type filter hook ingress device eth0 priority -500;
        # Fires before NF_INET_PRE_ROUTING — before conntrack, before routing
        ip saddr @ddos_sources drop
    }
    chain egress {
        type filter hook egress device eth0 priority 0;
        # Fires after NF_INET_POST_ROUTING, before driver transmission
    }
}
```

The `netdev` hooks are ideal for:

- Very early DDoS packet drops (no conntrack overhead for known-bad sources)
- Interface-specific filtering without traversing the full stack
- Rate limiting at line rate

---

## Hook Priorities

Each hook callback is registered with a **priority** (signed integer). Lower values run **first**. Multiple callbacks at the same hook point fire in priority order.

### Standard Priority Constants

|Constant|Value|Used by|
|---|---|---|
|`NF_IP_PRI_RAW_BEFORE_DEFRAG`|`-450`|nftables raw (before defragmentation)|
|`NF_IP_PRI_CONNTRACK_DEFRAG`|`-400`|`nf_defrag_ipv4` / `nf_defrag_ipv6`|
|`NF_IP_PRI_RAW`|`-300`|iptables `raw` table; nftables `raw` priority|
|`NF_IP_PRI_SELINUX_FIRST`|`-225`|SELinux early|
|`NF_IP_PRI_CONNTRACK`|`-200`|Conntrack lookup and entry creation|
|`NF_IP_PRI_MANGLE`|`-150`|iptables `mangle` table|
|`NF_IP_PRI_NAT_DST`|`-100`|Destination NAT (DNAT)|
|`NF_IP_PRI_FILTER`|`0`|iptables `filter` table; nftables `filter` default|
|`NF_IP_PRI_SECURITY`|`50`|AppArmor / SELinux late|
|`NF_IP_PRI_NAT_SRC`|`100`|Source NAT (SNAT / Masquerade)|
|`NF_IP_PRI_CONNTRACK_CONFIRM`|`INT_MAX`|Conntrack confirmation (insert into hash table)|

### Effective Firing Order at PRE_ROUTING

```
NF_INET_PRE_ROUTING
  ├── priority -450   nftables raw (before defrag)
  ├── priority -400   nf_defrag_ipv4 (fragment reassembly)
  ├── priority -300   iptables raw table / nftables raw
  ├── priority -200   nf_conntrack (lookup / create entry)
  ├── priority -150   iptables mangle table
  ├── priority -100   iptables nat table (DNAT rules)
  └── priority    0   iptables filter table
```

### nftables Named Priorities

In nftables, priorities can be specified as integers or named constants:

|Named priority|Integer|Equivalent iptables table|
|---|---|---|
|`raw`|`-300`|`raw`|
|`mangle`|`-150`|`mangle`|
|`dstnat`|`-100`|`nat` PREROUTING|
|`filter`|`0`|`filter`|
|`security`|`50`|—|
|`srcnat`|`100`|`nat` POSTROUTING|

> [!warning] Priority conflicts Multiple callbacks at exactly the same priority have **undefined ordering** relative to each other (depends on registration order). Use distinct priorities when ordering between hooks matters.

---

## Hook Registration (Kernel API)

This section is relevant for kernel module developers.

### Registering a Hook

```c
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>

static unsigned int my_hook_fn(
    void *priv,
    struct sk_buff *skb,
    const struct nf_hook_state *state)
{
    /* Inspect or modify the packet */
    return NF_ACCEPT;
}

static struct nf_hook_ops my_hook_ops = {
    .hook     = my_hook_fn,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FILTER,
};

/* Register at module init */
nf_register_net_hook(net, &my_hook_ops);

/* Unregister at module exit */
nf_unregister_net_hook(net, &my_hook_ops);
```

### The sk_buff (Socket Buffer)

`struct sk_buff` (skb) is the universal packet representation in the Linux kernel. Every packet is an skb as it traverses Netfilter hooks.

|Field|Type|Description|
|---|---|---|
|`data`|`unsigned char *`|Pointer to current packet data start|
|`head` / `end`|`unsigned char *`|Buffer boundaries|
|`len`|`unsigned int`|Total packet length|
|`protocol`|`__be16`|L3 protocol (`ETH_P_IP`, `ETH_P_IPV6`, …)|
|`dev`|`struct net_device *`|Incoming or outgoing device|
|`sk`|`struct sock *`|Associated socket (may be NULL)|
|`nfct`|`struct nf_conntrack *`|Conntrack entry (if tracked)|
|`mark`|`__u32`|Packet mark (set by `MARK` target / `meta mark set`)|

### The nf_hook_state

```c
struct nf_hook_state {
    unsigned int      hook;   // which hook point fired
    u_int8_t          pf;     // protocol family
    struct net_device *in;    // incoming device (NULL if not applicable)
    struct net_device *out;   // outgoing device (NULL if not applicable)
    struct sock       *sk;    // socket (may be NULL)
    struct net        *net;   // network namespace
    netfilter_fn       okfn;  // function to call on NF_ACCEPT
};
```

---

## Netfilter Verdicts

Every hook callback must return a **verdict** telling the kernel what to do next with the packet:

|Verdict|Value|Meaning|
|---|---|---|
|`NF_ACCEPT`|0|Packet continues through the stack normally|
|`NF_DROP`|1|Packet is silently discarded; skb memory freed|
|`NF_STOLEN`|2|Hook takes ownership of the skb; kernel takes no further action|
|`NF_QUEUE`|3|Packet is handed to a userspace queue (NFQUEUE)|
|`NF_REPEAT`|4|Re-invoke the hook on this packet (use carefully — can loop)|
|`NF_STOP`|5|**Deprecated.** Treated as `NF_ACCEPT` in modern kernels|

### Verdict Semantics

- **`NF_DROP`** frees the skb immediately. No ICMP error is generated automatically — use the `REJECT` target or `reject` statement for that.
- **`NF_STOLEN`** transfers ownership to the hook function. Used by packet-queuing code that will re-inject the skb later. The kernel will not double-free.
- **`NF_QUEUE`** hands the packet to the NFQUEUE subsystem. If no userspace process is listening on that queue number, the packet is dropped.

### iptables Targets vs Netfilter Verdicts

|iptables target|Netfilter verdict|Notes|
|---|---|---|
|`ACCEPT`|`NF_ACCEPT`||
|`DROP`|`NF_DROP`||
|`REJECT`|`NF_DROP` + ICMP/RST|Generates error response before dropping|
|`QUEUE`|`NF_QUEUE`|Legacy; uses queue number 0|
|`NFQUEUE --queue-num N`|`NF_QUEUE`|Specific queue number|
|`RETURN`|Internal|Returns from current chain to calling chain|
|`GOTO chain`|Internal|Jumps to chain (no return)|
|`LOG`|`NF_ACCEPT` (continues)|Non-terminating: logs and passes through|

---

## IPv4 Packet Traversal

Complete path of an **incoming forwarded IPv4 packet** through all Netfilter tables and chains:

```
NIC receives packet
        │
        ▼
NF_INET_PRE_ROUTING
  ├── raw::PREROUTING          (−300: NOTRACK, CT helper assignment)
  ├── nf_conntrack             (−200: tuple lookup / new entry creation)
  ├── mangle::PREROUTING       (−150: TOS, TTL, MARK modification)
  └── nat::PREROUTING          (−100: DNAT / port forwarding)
        │
        ▼
   Routing decision
        │
        ├─── destined for local process ────────────────────────────────┐
        │                                                                 │
        ▼ (forward)                                                       ▼ (local)
NF_INET_FORWARD                                                 NF_INET_LOCAL_IN
  ├── mangle::FORWARD  (−150)                                    ├── mangle::INPUT   (−150)
  ├── filter::FORWARD  (0)    ← main forwarding filter           ├── filter::INPUT   (0)
  └── security::FORWARD (50)                                     └── security::INPUT (50)
        │                                                                  │
        ▼                                                                  ▼
NF_INET_POST_ROUTING                                               Local sockets
  ├── mangle::POSTROUTING (−150)
  ├── nat::POSTROUTING    (100)  ← SNAT / Masquerade
  └── conntrack confirm   (INT_MAX)
        │
        ▼
     NIC transmit
```

### Locally Generated Packets

```
Socket write()
        │
        ▼
NF_INET_LOCAL_OUT
  ├── raw::OUTPUT             (−300)
  ├── nf_conntrack            (−200)
  ├── mangle::OUTPUT          (−150)
  ├── nat::OUTPUT             (−100: DNAT for locally-generated traffic)
  └── filter::OUTPUT          (0)
        │
        ▼
   Routing decision
        │
        ▼
NF_INET_POST_ROUTING
  ├── mangle::POSTROUTING     (−150)
  ├── nat::POSTROUTING        (100: SNAT)
  └── conntrack confirm       (INT_MAX)
        │
        ▼
     NIC transmit
```

---

## IPv6 Packet Traversal

The IPv6 packet path mirrors IPv4 exactly, using `NFPROTO_IPV6` hooks. Key differences:

- Fragmentation uses extension headers; `nf_defrag_ipv6` handles reassembly.
- ICMPv6 is tracked by conntrack separately from ICMPv4.
- NAT for IPv6 requires `nf_nat` with IPv6 support (merged into `nf_nat` on kernels ≥ 5.x; `nf_nat_ipv6` on older kernels).
- `ip6tables` operates here; syntax is nearly identical to `iptables` except ICMPv6 uses `-p ipv6-icmp`.

```bash
# Stateful ip6tables rules
ip6tables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
ip6tables -A INPUT -m conntrack --ctstate INVALID -j DROP
ip6tables -A INPUT -p ipv6-icmp -j ACCEPT    # ICMPv6 is required for NDP
```

---

## Bridge Packet Traversal

Bridged traffic passes through `NFPROTO_BRIDGE` hooks (`ebtables`). With `br_netfilter` loaded, it additionally passes through the `NFPROTO_IPV4/IPV6` hooks.

```
Frame arrives on bridge port (e.g., eth1 in bridge br0)
        │
        ▼
NF_BR_PRE_ROUTING           ← ebtables PREROUTING
        │
  Forwarding decision (MAC learning table)
        │
        ├── destined for bridge IP stack ────────────────┐
        │                                                  │
        ▼ (forward to another port)                        ▼
  [with br_netfilter:]                             NF_BR_LOCAL_IN
NF_INET_PRE_ROUTING  ← iptables/nftables/conntrack         │
NF_INET_FORWARD      ← iptables/nftables                   ▼
NF_INET_POST_ROUTING ← iptables/nftables             Bridge IP stack
        │
        ▼
NF_BR_POST_ROUTING          ← ebtables POSTROUTING
        │
        ▼
Frame transmitted on bridge port
```

> [!warning] Double-processing risk Without `br_netfilter`, bridged traffic silently bypasses iptables/nftables/conntrack. With it, the same IP packet may be processed by both `ebtables` (bridge-level) and `iptables` (IP-level) hooks. Use conntrack zones to isolate the two domains if double-tracking occurs. See [[Netfilter Conntrack — Connection Tracking#Bridge Networking and nf_conntrack_bridge]].

---

## Netlink and nfnetlink

### Overview

Netlink is a **socket-based IPC mechanism** for kernel↔userspace communication. Netfilter uses a specialized Netlink family: **nfnetlink** (`NETLINK_NETFILTER`, protocol 12).

All modern Netfilter tools communicate via Netlink:

- `nft` → `NFNL_SUBSYS_NFTABLES`
- `conntrack` → `NFNL_SUBSYS_CTNETLINK`
- `ipset` → `NFNL_SUBSYS_IPSET`
- NFQUEUE libraries → `NFNL_SUBSYS_QUEUE`
- NFLOG libraries → `NFNL_SUBSYS_ULOG`

> [!note] Legacy iptables The **legacy** `iptables` tool uses `setsockopt`/`getsockopt` on a raw socket, **not** Netlink. The newer `iptables-nft` wrapper (iptables-over-nftables) does use Netlink. This is why running `nft list ruleset` shows rules added by `iptables-nft` but not by `iptables-legacy`.

### nfnetlink Subsystems

|Subsystem constant|Value|Purpose|
|---|---|---|
|`NFNL_SUBSYS_CTNETLINK`|1|Conntrack table access|
|`NFNL_SUBSYS_CTNETLINK_EXP`|2|Conntrack expectations|
|`NFNL_SUBSYS_QUEUE`|3|NFQUEUE packet deliver / verdict|
|`NFNL_SUBSYS_ULOG`|4|NFLOG packet logging|
|`NFNL_SUBSYS_IPSET`|6|ipset management|
|`NFNL_SUBSYS_ACCT`|7|Netfilter accounting objects|
|`NFNL_SUBSYS_CTNETLINK_TIMEOUT`|8|Per-flow CT timeout policies|
|`NFNL_SUBSYS_CTHELPER`|9|Userspace CT helpers|
|`NFNL_SUBSYS_NFTABLES`|12|nftables rule management|
|`NFNL_SUBSYS_NFT_COMPAT`|13|iptables compatibility via nftables|

---

## NFQUEUE — Userspace Packet Processing

### What NFQUEUE Does

NFQUEUE allows a **userspace process** to receive packets from the kernel, inspect or modify them, and return a verdict (`ACCEPT` or `DROP`). Use cases include userspace firewalls, IDS/IPS (Suricata, Snort), and custom protocol-aware transformation that is too complex for in-kernel rules.

```
Kernel                              Userspace
  │                                    │
  │  Rule: -j NFQUEUE --queue-num 0   │
  │                                    │
  ├── NF_QUEUE verdict ───────────────►│  libnetfilter_queue
  │                                    │  Receives packet via Netlink
  │                                    │  Inspects / optionally modifies
  │◄── Verdict (ACCEPT / DROP) ────────│  Sends verdict back
  │
  └── NF_ACCEPT or NF_DROP
```

### NFQUEUE Setup

#### iptables

```bash
# Send all incoming TCP to queue 0
iptables -A INPUT -p tcp -j NFQUEUE --queue-num 0

# Bypass (ACCEPT) if no userspace listener is running
iptables -A INPUT -p tcp -j NFQUEUE --queue-num 0 --queue-bypass

# Fan out to multiple queues for parallel processing
iptables -A INPUT -p tcp -j NFQUEUE --queue-balance 0:3
```

#### nftables

```nftables
table inet filter {
    chain input {
        type filter hook input priority 0;
        tcp dport 80 queue num 0
        tcp dport 80 queue num 0-3       # fan-out across queues 0–3
        tcp dport 80 queue num 0 bypass  # bypass if no listener
    }
}
```

### NFQUEUE Copy Modes

When delivering packets to userspace, the kernel can send:

|Mode|Flag|Description|
|---|---|---|
|None|`NFQNL_COPY_NONE`|Metadata only; no packet data|
|Meta|`NFQNL_COPY_META`|Metadata + zero bytes of payload|
|Packet|`NFQNL_COPY_PACKET`|Full packet up to `copy_range` bytes|

```c
// Copy up to 65535 bytes of packet data to userspace
nfq_set_mode(qh, NFQNL_COPY_PACKET, 0xffff);
```

### NFQUEUE Verdict with Modification

Userspace can **modify the packet** before issuing a verdict:

```c
nfq_set_verdict2(
    qh,
    id,             // packet id received from kernel
    NF_ACCEPT,      // verdict
    mark,           // new packet mark (0 = leave unchanged)
    data_len,       // length of modified packet data
    modified_data   // pointer to modified packet bytes
);
```

### NFQUEUE Limitations

- Adds per-packet latency (kernel→userspace→kernel round trip; typically 50–200 µs).
- Not suitable for line-rate forwarding without batching and multi-queue tuning.
- If the userspace process crashes or stalls, the queue fills and packets are dropped.
- `--queue-bypass` mitigates the crash case by falling back to `ACCEPT`.

---

## NFLOG — Packet Logging to Userspace

### What NFLOG Does

NFLOG delivers **copies** of packets (or metadata) to userspace for logging. Unlike NFQUEUE, the kernel does **not** wait for a verdict — the original packet continues immediately. NFLOG is the production replacement for the `LOG` target.

### NFLOG Setup

#### iptables

```bash
# Log INVALID packets to NFLOG group 1, then drop them
iptables -A INPUT -m conntrack --ctstate INVALID \
    -j NFLOG --nflog-group 1 --nflog-prefix "INVALID: " --nflog-threshold 10
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
```

#### nftables

```nftables
table inet filter {
    chain input {
        ct state invalid log group 1 prefix "INVALID: " drop
        tcp dport 22 ct state new log group 2 prefix "SSH-NEW: "
    }
}
```

### ulogd2 — Userspace Logging Daemon

`ulogd2` receives NFLOG packets via Netlink and routes them to output plugins (flat files, pcap, MySQL, PostgreSQL, JSON):

```ini
# /etc/ulogd.conf (minimal)
[global]
logfile="/var/log/ulogd.log"
loglevel=5
stack=log1:NFLOG,base1:BASE,ifi1:IFINDEX,ip2str1:IP2STR,print1:PRINTPKT,emu1:LOGEMU

[log1]
group=1          # must match --nflog-group in iptables

[emu1]
file="/var/log/netfilter.log"
sync=1
```

### NFLOG vs LOG Target

|Feature|`LOG` target|`NFLOG` target|
|---|---|---|
|Destination|Kernel log (`dmesg` / syslog via `printk`)|Userspace via Netlink|
|Output filtering|None|Per-group, configurable copy range|
|Performance|High overhead (synchronous printk)|Batched Netlink delivery|
|Structured output|No — plain text|Yes — via ulogd2 plugins|
|pcap capture|No|Yes (ulogd2 PCAP output plugin)|
|Database logging|No|Yes (ulogd2 MySQL / PostgreSQL plugins)|
|Recommended for production?|No — debugging only|Yes|

---

## libnetfilter Libraries

These userspace C libraries wrap the Netlink interaction for each Netfilter subsystem:

|Library|Purpose|
|---|---|
|`libmnl`|Low-level Netlink message parsing and building|
|`libnftnl`|nftables object serialization/deserialization (used by `nft`)|
|`libnetfilter_conntrack`|Read/write the conntrack table|
|`libnetfilter_queue`|NFQUEUE packet receive / verdict API|
|`libnetfilter_log`|NFLOG packet receive API|
|`libnetfilter_acct`|Netfilter accounting objects|
|`libnetfilter_cthelper`|Userspace CT helper framework|
|`libnetfilter_cttimeout`|Per-flow CT timeout policy management|
|`libipset`|ipset management|
|`libnftables`|High-level nftables library (JSON/scripting interface)|

---

## iptables

### iptables Tables and Chains

`iptables` organises rules into **tables**, each attached to specific Netfilter hook points. Each table contains **chains** — ordered sequences of rules.

```
Table       Hook Points                        Built-in Chains
─────────   ──────────────────────────────     ──────────────────────────────────────────
raw         PRE_ROUTING · LOCAL_OUT            PREROUTING · OUTPUT
mangle      all five hooks                     PREROUTING · INPUT · FORWARD · OUTPUT · POSTROUTING
nat         PRE_ROUTING · LOCAL_OUT            PREROUTING · OUTPUT · POSTROUTING
            LOCAL_IN · POST_ROUTING            (+ INPUT since kernel 3.7 for local NAT)
filter      LOCAL_IN · FORWARD · LOCAL_OUT     INPUT · FORWARD · OUTPUT
security    LOCAL_IN · FORWARD · LOCAL_OUT     INPUT · FORWARD · OUTPUT
```

### Packet Flow Through iptables Tables

For a **forwarded packet**:

```
1.  raw::PREROUTING
2.  [conntrack lookup]
3.  mangle::PREROUTING
4.  nat::PREROUTING          ← DNAT
5.  [routing decision]
6.  mangle::FORWARD
7.  filter::FORWARD          ← main forwarding filter
8.  security::FORWARD
9.  mangle::POSTROUTING
10. nat::POSTROUTING         ← SNAT / Masquerade
```

For an **incoming packet to a local process**:

```
1. raw::PREROUTING
2. [conntrack]
3. mangle::PREROUTING
4. nat::PREROUTING
5. [routing]
6. mangle::INPUT
7. filter::INPUT             ← main input filter
8. security::INPUT
```

### iptables Rule Structure

```bash
iptables [-t table] COMMAND chain [match...] [-j target]
```

|Component|Description|
|---|---|
|`-t table`|Table name (default: `filter`)|
|`COMMAND`|`-A` append · `-I` insert · `-D` delete · `-R` replace · `-L` list · `-F` flush|
|`chain`|`INPUT`, `FORWARD`, `OUTPUT`, `PREROUTING`, `POSTROUTING`, or user chain|
|`match`|`-p tcp`, `-s 10.0.0.0/8`, `-m conntrack --ctstate NEW`, …|
|`-j target`|`ACCEPT`, `DROP`, `REJECT`, `LOG`, `DNAT`, `SNAT`, user chain, …|

### iptables Built-in Targets

#### Terminating Targets

|Target|Effect|
|---|---|
|`ACCEPT`|Accept packet; skip remaining rules in current chain|
|`DROP`|Silently discard packet|
|`REJECT [--reject-with type]`|Discard packet and send ICMP error or TCP RST|
|`QUEUE`|Send to NFQUEUE number 0 (legacy; use `NFQUEUE` instead)|
|`RETURN`|Return from user chain to calling chain|

#### Non-Terminating Targets

|Target|Effect|
|---|---|
|`LOG`|Log to kernel log and continue to next rule|
|`NFLOG`|Log via Netlink to userspace and continue|
|`MARK --set-mark VALUE`|Set packet mark (`skb->mark`) and continue|
|`CONNMARK`|Save / restore conntrack mark and continue|
|`DSCP --set-dscp VALUE`|Set DSCP bits in IP ToS field and continue|
|`TOS --set-tos VALUE`|Set IP ToS byte and continue|
|`TTL --ttl-set VALUE`|Modify IP TTL and continue|
|`TRACE`|Enable per-rule packet tracing (see [[#Debugging Netfilter]])|

#### NAT Targets (nat table only)

|Target|Usage|
|---|---|
|`DNAT --to-destination IP[:port[-port]]`|Rewrite destination address/port|
|`SNAT --to-source IP[:port[-port]]`|Rewrite source address/port|
|`MASQUERADE`|SNAT using the outgoing interface's current IP (for dynamic IPs)|
|`REDIRECT --to-ports PORT`|Redirect to a local port (DNAT to 127.0.0.1)|
|`NETMAP --to IP/MASK`|1:1 network address mapping|

### iptables Rule Matching Extensions

Loaded with `-m module_name`:

|Module|Key options|Description|
|---|---|---|
|`conntrack`|`--ctstate`, `--ctproto`, `--ctmark`|Match conntrack state / attributes|
|`state`|`--state`|Legacy conntrack state match (use `conntrack` instead)|
|`multiport`|`--dports`, `--sports`|Match multiple ports in one rule|
|`limit`|`--limit N/s --limit-burst B`|Token-bucket rate limiting|
|`hashlimit`|`--hashlimit-above`, `--hashlimit-mode`|Per-source / per-dest rate limiting|
|`iprange`|`--src-range`, `--dst-range`|Match IP address ranges|
|`set`|`--match-set setname src\|dst`|Match against an ipset|
|`recent`|`--rcheck`, `--update`, `--set`|Per-source IP recent connection tracking|
|`string`|`--string`, `--algo`|Payload string matching|
|`length`|`--length`|Packet length matching|
|`ttl`|`--ttl-eq`, `--ttl-lt`|IP TTL matching|
|`owner`|`--uid-owner`, `--gid-owner`|Socket owner matching (OUTPUT chain only)|
|`physdev`|`--physdev-in`, `--physdev-out`|Bridge physical device matching|
|`addrtype`|`--src-type`, `--dst-type`|IP address type (LOCAL, BROADCAST, …)|
|`mark`|`--mark VALUE[/MASK]`|Packet mark matching|
|`comment`|`--comment "text"`|Annotate a rule (no matching effect)|
|`time`|`--timestart`, `--timestop`, `--weekdays`|Time-based matching|

### ip6tables and arptables

`ip6tables` is the IPv6 equivalent of `iptables` with an identical table/chain structure. Key differences:

- Masquerade / NAT is rare for IPv6 but supported via `ip6tables -t nat`.
- ICMPv6 uses `-p ipv6-icmp` (not `icmp`).
- `--reject-with` uses `icmp6-*` codes.
- ICMPv6 must never be blanket-dropped — it is required for Neighbor Discovery Protocol (NDP).

`arptables` operates on `NF_ARP_*` hooks with a simpler rule structure:

```bash
# Drop ARP replies impersonating a specific IP
arptables -A INPUT --opcode reply --arp-ip-src 192.168.1.1 -j DROP
```

---

## nftables

### nftables Data Model

`nftables` replaces `iptables / ip6tables / arptables / ebtables` with a **single unified framework**.

```
nftables
  └── Table  (named; belongs to a protocol family)
        └── Chain  (hook-attached base chain, or a regular chain called by jump/goto)
              └── Rule  (ordered list of match expressions + a verdict statement)
```

Key differences from iptables:

- **No built-in tables or chains** — everything is created explicitly.
- **Single binary** (`nft`) for all protocol families.
- **Atomic rule sets** — entire sets applied or rolled back as one transaction.
- **Sets and maps** are first-class objects (no separate `ipset` needed).
- **Counters, quotas, rate meters** built in as statements.

### Table Families

|Family|Covers|
|---|---|
|`ip`|IPv4 only|
|`ip6`|IPv6 only|
|`inet`|IPv4 + IPv6 combined|
|`arp`|ARP|
|`bridge`|Bridge / Ethernet frames|
|`netdev`|Per-device ingress / egress|

### Chain Types

|Type|Usable at hooks|Purpose|
|---|---|---|
|`filter`|All hooks|Packet filtering|
|`nat`|`prerouting` · `postrouting` · `input` · `output`|Address translation|
|`route`|`output` only|Re-route after mark change|

```nftables
table inet firewall {
    # Base chain (attached to a hook)
    chain input {
        type filter hook input priority filter; policy drop;

        ct state established,related accept
        ct state invalid drop
        iif "lo" accept
        tcp dport { 22, 80, 443 } ct state new accept
    }

    # Regular chain (no hook — called via jump/goto from a base chain)
    chain log_and_drop {
        log prefix "DROPPED: " level warn
        drop
    }
}
```

### nftables Expressions and Statements

#### Match Expressions

```nftables
# IP header
ip saddr 10.0.0.0/8
ip daddr { 192.168.1.1, 192.168.1.2 }
ip protocol tcp
ip ttl <= 64

# IPv6
ip6 saddr fe80::/10
ip6 nexthdr tcp

# Transport layer
tcp dport 80
tcp dport 1024-65535
udp sport { 53, 5353 }
tcp flags syn,ack / syn,ack     # match SYN+ACK

# Connection tracking
ct state new,established,related,invalid,untracked
ct mark 0x10
ct zone 1

# Meta / interface
iif "eth0"
oifname "eth*"       # wildcard match
meta l4proto tcp
meta mark 0x100
skuid 1000            # socket UID (local output only)
```

#### Verdict Statements

```nftables
accept               # NF_ACCEPT
drop                 # NF_DROP
return               # return from chain
jump other_chain     # jump to chain (returns when done)
goto other_chain     # jump to chain (no return)
queue num 0          # NF_QUEUE
queue num 0-3        # fan-out
```

#### Non-Verdict Statements

```nftables
# Logging
log prefix "DROP: " level warn
log group 1 prefix "NFLOG: "

# Counters
counter packets 0 bytes 0

# NAT
dnat to 192.168.1.100:8080
snat to 203.0.113.1
masquerade
redirect to :8080

# Packet modification
meta mark set 0x10
ct mark set meta mark
ip ttl set 64
ip dscp set ef

# Rate limiting
limit rate 100/minute burst 150 packets
```

### nftables Sets and Maps

Sets and maps are **first-class data structures** for efficient multi-value matching.

#### Anonymous Sets (inline, immutable)

```nftables
tcp dport { 80, 443, 8080 } accept
ip saddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } drop
```

#### Named Sets (persistent, updatable at runtime without reloading rules)

```nftables
table inet filter {
    set blocked_ips {
        type ipv4_addr
        flags interval          # allows CIDR ranges
        elements = { 192.0.2.1, 198.51.100.0/24 }
    }

    chain input {
        ip saddr @blocked_ips drop
    }
}
```

```bash
# Add / remove elements at runtime — rules re-evaluated instantly
nft add element inet filter blocked_ips { 203.0.113.5 }
nft delete element inet filter blocked_ips { 203.0.113.5 }
```

#### Maps (data maps and verdict maps)

```nftables
table inet filter {
    # Verdict map: source IP → verdict
    map ip_verdict {
        type ipv4_addr : verdict
        elements = { 10.0.0.1 : accept, 10.0.0.2 : drop }
    }

    chain input {
        ip saddr vmap @ip_verdict
    }

    # Data map: dst port → backend IP (for DNAT)
    map port_to_backend {
        type inet_service : ipv4_addr
        elements = { 80 : 192.168.1.10, 443 : 192.168.1.11 }
    }

    chain prerouting {
        type nat hook prerouting priority dstnat;
        dnat to tcp dport map @port_to_backend
    }
}
```

#### Set Flags

|Flag|Meaning|
|---|---|
|`constant`|Set cannot be modified at runtime|
|`interval`|Elements can be IP ranges / CIDR prefixes|
|`timeout`|Elements auto-expire after a configurable TTL|
|`dynamic`|Elements can be added from the packet path via `update` statement|

```nftables
# Auto-block IPs that send more than 10 SYNs/second
set syn_flood {
    type ipv4_addr
    flags dynamic, timeout
    timeout 60s
}

chain input {
    tcp flags syn \
        add @syn_flood { ip saddr limit rate over 10/second } \
        drop
    ip saddr @syn_flood drop
}
```

### nftables Flowtables

Flowtables provide a **fast path** for established TCP/UDP flows, bypassing the full Netfilter hook chain. See [[Netfilter Conntrack — Connection Tracking#Flowtable and Hardware Offload]] for full documentation.

### Migrating from iptables to nftables

`iptables-translate` converts individual rules; `iptables-restore-translate` converts an entire saved ruleset:

```bash
iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT
# nft add rule ip filter INPUT tcp dport 22 counter accept

iptables-save | iptables-restore-translate -f /etc/nftables/converted.nft
```

> [!note] iptables-nft On most modern distributions, `iptables` is actually a wrapper over nftables (`iptables-nft`). `iptables -L` queries the nftables kernel subsystem, and `nft list ruleset` shows both `iptables-nft` and `nft` rules together. `iptables-legacy` (via `setsockopt`) maintains a separate, independent ruleset.

---

## ipset

`ipset` provides **hash and bitmap data structures** in the kernel that can be used as matching criteria in iptables rules. A single iptables rule with an ipset replaces thousands of individual rules and uses O(1) hash lookups.

### ipset Types

|Set type|Key fields|Use case|
|---|---|---|
|`hash:ip`|Single IP address|Blocklists, allowlists|
|`hash:net`|CIDR prefix|Network-level allowlists|
|`hash:ip,port`|IP + port|Per-service per-host rules|
|`hash:net,port`|Network + port|Per-service per-network|
|`hash:ip,port,ip`|Src IP + port + Dst IP|Full 5-tuple matching|
|`hash:mac`|MAC address|L2 filtering (via ebtables)|
|`bitmap:ip`|Dense IP range (single /8–/24)|Fast lookup for a compact range|
|`bitmap:port`|Port range|Bulk port range matching|
|`list:set`|List of set names|Chained set lookup|

### ipset Commands

```bash
# Create
ipset create BLOCKED_NETS hash:net

# Add entries
ipset add BLOCKED_NETS 203.0.113.0/24
ipset add BLOCKED_NETS 198.51.100.0/24

# Test membership
ipset test BLOCKED_NETS 203.0.113.5    # exits 0 on match

# List contents
ipset list BLOCKED_NETS

# Delete entry
ipset del BLOCKED_NETS 203.0.113.0/24

# Flush all entries from a set (keep the set)
ipset flush BLOCKED_NETS

# Destroy set (including entries)
ipset destroy BLOCKED_NETS

# Persistence
ipset save  > /etc/ipset.conf
ipset restore < /etc/ipset.conf
```

#### Using ipset in iptables

```bash
# Allowlist
ipset create ALLOWED_IPS hash:ip
ipset add ALLOWED_IPS 192.168.1.1
iptables -A INPUT -m set --match-set ALLOWED_IPS src -j ACCEPT

# Blocklist (insert as first rule for performance)
ipset create BLOCKED_IPS hash:ip
iptables -I INPUT -m set --match-set BLOCKED_IPS src -j DROP
```

### ipset Timeout (Auto-expiry)

```bash
# Set with a default element timeout
ipset create TEMP_BLOCK hash:ip timeout 300

# Override per element
ipset add TEMP_BLOCK 192.0.2.1 timeout 60    # expires in 60 s
ipset add TEMP_BLOCK 192.0.2.2               # uses set default (300 s)
```

### ipset vs nftables Sets

|Feature|ipset|nftables sets|
|---|---|---|
|Requires iptables|Yes (or `nft_compat`)|No|
|Runtime update|Yes (`ipset add/del`)|Yes (`nft add/delete element`)|
|Auto-expiry|Yes (`timeout`)|Yes (`timeout` flag)|
|Dynamic from packet path|No|Yes (`dynamic` flag)|
|Verdict maps|No|Yes|
|Lookup performance|Excellent (O(1))|Excellent (O(1))|

> [!tip] Prefer **nftables native sets** for new setups. `ipset` remains valuable for compatibility with tools that manage it directly (fail2ban, blocklist managers, etc.).

---

## Connection Tracking

Netfilter's stateful tracking is provided by the `nf_conntrack` subsystem, fully documented in [[Netfilter Conntrack — Connection Tracking]].

Key integration points:

- Conntrack registers at `PRE_ROUTING` / `LOCAL_OUT` (priority `−200`) for lookup and entry creation.
- Confirmation (insertion into the hash table) happens at `POST_ROUTING` / `LOCAL_IN` (priority `INT_MAX`), after firewall rules — entries are never inserted for packets that are dropped.
- The `ct state`, `--ctstate` match keywords query the conntrack entry attached to the skb.
- **Conntrack is a prerequisite for NAT** — NAT cannot function without it.

---

## NAT

### How NAT Works in Netfilter

NAT is implemented in `nf_nat` (which depends on `nf_conntrack`). The key insight: **NAT rules evaluate only once per flow** — on the first packet. The translation mapping is stored in the conntrack entry, and all subsequent packets are translated by looking up that entry, with no rule re-evaluation.

For the full mechanism see [[Netfilter Conntrack — Connection Tracking#NAT Integration]].

### SNAT and Masquerade

```bash
# iptables: Masquerade (dynamic SNAT) — for outbound with a dynamic public IP
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# iptables: SNAT to a fixed IP
iptables -t nat -A POSTROUTING -o eth0 -j SNAT --to-source 203.0.113.1

# nftables equivalent
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat;
        oifname "eth0" masquerade
    }
}
```

### DNAT and Port Forwarding

```bash
# iptables: forward external port 8080 to internal 192.168.1.100:80
iptables -t nat -A PREROUTING -p tcp --dport 8080 \
    -j DNAT --to-destination 192.168.1.100:80

# Also allow the forwarded traffic through the FORWARD chain
iptables -A FORWARD -d 192.168.1.100 -p tcp --dport 80 \
    -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT

# nftables equivalent
table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat;
        tcp dport 8080 dnat to 192.168.1.100:80
    }
}
```

### NAT Hairpinning

When an internal host reaches an internal server via the server's **external IP**, the reply travels directly back (not via the NAT gateway), breaking the NAT state. Fix with an additional SNAT rule:

```bash
# iptables: hairpin NAT (loopback NAT)
iptables -t nat -A POSTROUTING \
    -s 192.168.1.0/24 -d 192.168.1.100 -p tcp --dport 80 \
    -j MASQUERADE
```

---

## Netfilter and Network Namespaces

Every Linux **network namespace** (`netns`) contains a completely independent Netfilter state:

- Independent hook registrations per namespace
- Independent iptables / nftables rule sets
- Independent conntrack tables and timeouts
- Independent sysctl values for all netfilter parameters

This is foundational to container networking — each container in its own netns has its own isolated firewall, conntrack table, and NAT rules.

```bash
# Create a network namespace
ip netns add myns

# Run iptables inside it
ip netns exec myns iptables -A INPUT -j DROP

# Run nft inside it
ip netns exec myns nft list ruleset

# Inspect conntrack inside it
ip netns exec myns conntrack -L

# Access via nsenter
nsenter --net=/var/run/netns/myns -- nft list ruleset
```

### Namespace Isolation Model

```
Host netns
  ├── Netfilter hooks:    iptables/nftables rules for host traffic
  ├── Conntrack table:    host-level sessions (Docker NAT, host services)
  └── sysctl values:      e.g., net.netfilter.nf_conntrack_max = 524288

Container netns (e.g., a Docker container)
  ├── Netfilter hooks:    typically empty — container has no own rules
  ├── Conntrack table:    separate, isolated table
  └── sysctl values:      inherits host defaults at creation; can be set independently
```

> [!note] Docker NAT location Docker's default `bridge` networking performs Masquerade/conntrack in the **host netns** on the `docker0` interface, not in the container's netns. Containers themselves typically have no iptables rules.

---

## Hook Overhead and Optimization

### Traversal Cost

Each Netfilter hook call carries measurable CPU overhead:

- A hook with zero registered callbacks still incurs a small dispatch check.
- Each registered callback adds function call overhead plus whatever the callback does.
- A linear chain of 1,000 iptables rules evaluates up to 1,000 comparisons per packet.

### Optimization Techniques

#### 1. Use sets for large address lists — O(1) vs O(n)

```bash
# Slow: 10,000 rules, linear O(n) evaluation
for ip in $(cat blocklist.txt); do
    iptables -A INPUT -s "$ip" -j DROP
done

# Fast: one rule + hash set, O(1) lookup
ipset create BLOCKLIST hash:ip
while read ip; do ipset add BLOCKLIST "$ip"; done < blocklist.txt
iptables -A INPUT -m set --match-set BLOCKLIST src -j DROP
```

#### 2. Place high-frequency matches first in chains

```bash
# Good: ESTABLISHED first (the vast majority of packets)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Bad: specific port rules before the common case
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

#### 3. NOTRACK for high-rate stateless traffic

Use `CT --notrack` (iptables raw table) or `notrack` (nftables raw chain) to bypass conntrack entirely for traffic that does not need state tracking (DNS, syslog, metrics). See [[Netfilter Conntrack — Connection Tracking#NOTRACK and CT Bypass]].

#### 4. Enable flowtable offloading for established TCP/UDP flows

See [[Netfilter Conntrack — Connection Tracking#Flowtable and Hardware Offload]].

#### 5. Prefer nftables over iptables for large rule sets

nftables executes rules via a **bytecode VM**, which is more cache-friendly and avoids the per-table write lock contention present in legacy iptables. For large rule sets, nftables native sets replace thousands of rules with a single O(1) hash lookup.

#### 6. Use the netdev ingress hook for very early drops

```nftables
table netdev filter {
    chain ingress {
        type filter hook ingress device eth0 priority -500;
        # Drops before conntrack, before routing, before any sk_buff processing
        ip saddr @ddos_sources counter drop
    }
}
```

---

## eBPF and XDP Integration

### Positioning Relative to Netfilter

eBPF and Netfilter coexist but occupy different layers:

||XDP (eBPF)|TC eBPF (`cls_bpf`)|Netfilter|
|---|---|---|---|
|Hook location|Before `sk_buff` allocation|After `sk_buff` alloc, before Netfilter|After `sk_buff` alloc|
|Performance|Extreme (NIC driver level)|Very high|Good|
|Stateful features|Custom via eBPF maps|Custom via eBPF maps|Built-in conntrack / NAT|
|NAT|Custom only|Custom only|Built-in|

```
NIC RX interrupt
  │
  ▼  XDP hook (eBPF)         ← XDP_DROP for line-rate DDoS mitigation
  │
  ▼  sk_buff allocated
  │
  ▼  TC ingress (cls_bpf / cls_flower)
  │
  ▼  NF_INET_PRE_ROUTING     ← Netfilter begins here
  │
  └── ... normal network stack
```

### XDP (eXpress Data Path)

XDP runs eBPF programs at the **NIC driver level**, before skb allocation, enabling line-rate packet dropping with near-zero CPU overhead:

|XDP verdict|Effect|
|---|---|
|`XDP_DROP`|Drop packet before skb allocation (fastest possible drop)|
|`XDP_PASS`|Pass packet to normal network stack|
|`XDP_TX`|Retransmit on same NIC (hairpin)|
|`XDP_REDIRECT`|Redirect to another NIC or CPU queue|

### TC and Netfilter Cooperation

TC rules and Netfilter can cooperate via packet marks:

```bash
# TC rule marks a packet
tc filter add dev eth0 ingress ... action skbedit mark 0x100

# Netfilter rule matches the mark
iptables -A INPUT -m mark --mark 0x100 -j ACCEPT
```

Cilium (eBPF-based CNI) implements its own connection tracking in eBPF, bypassing Netfilter conntrack for Pod-to-Pod traffic. Host-level traffic still goes through Netfilter. The implication: `conntrack -L` will not show eBPF-tracked flows.

---

## Netfilter Module Reference

### Loading Modules

```bash
# Load manually
modprobe nf_conntrack
modprobe nf_nat
modprobe iptable_filter
modprobe nf_tables

# List loaded Netfilter-related modules
lsmod | grep -E 'nf_|iptable|ip_tables|nft|x_tables'

# Check dependencies
modinfo nf_nat | grep depends
```

### Module Auto-loading

Most Netfilter modules are auto-loaded on demand:

- `iptables -A INPUT ...` → loads `ip_tables`, `iptable_filter`
- `iptables -t nat ...` → loads `iptable_nat`, `nf_nat`, `nf_conntrack`
- `nft add table ...` → loads `nf_tables`
- First packet touching a conntrack rule → loads `nf_conntrack`

### Persistent Module Loading

```bash
# /etc/modules-load.d/netfilter.conf
nf_conntrack
nf_nat
br_netfilter
```

### Full Module Reference

|Module|Auto-loaded by|Notes|
|---|---|---|
|`nf_tables`|`nft` commands|Core nftables engine|
|`nft_compat`|`iptables-nft`|iptables-over-nftables compat layer|
|`ip_tables`|`iptables`|Legacy iptables core (IPv4)|
|`ip6_tables`|`ip6tables`|Legacy ip6tables core (IPv6)|
|`iptable_filter`|`iptables`|`filter` table|
|`iptable_nat`|`iptables -t nat`|`nat` table|
|`iptable_mangle`|`iptables -t mangle`|`mangle` table|
|`iptable_raw`|`iptables -t raw`|`raw` table|
|`nf_conntrack`|First stateful rule|Connection tracking core|
|`nf_conntrack_ipv4`|`nf_conntrack`|IPv4 protocol tracker|
|`nf_conntrack_ipv6`|`nf_conntrack`|IPv6 protocol tracker|
|`nf_nat`|First NAT rule|NAT core|
|`nf_defrag_ipv4`|`nf_conntrack`|IPv4 fragment reassembly|
|`nf_defrag_ipv6`|`nf_conntrack`|IPv6 fragment reassembly|
|`nfnetlink`|`nf_tables`, `nfnetlink_queue`|Netlink transport for Netfilter|
|`nfnetlink_queue`|NFQUEUE rules|NFQUEUE subsystem|
|`nfnetlink_log`|NFLOG rules|NFLOG subsystem|
|`ip_set`|`ipset` commands|ipset core|
|`ip_set_hash_ip`|`ipset create ... hash:ip`|ipset hash:ip type|
|`ip_set_hash_net`|`ipset create ... hash:net`|ipset hash:net type|
|`br_netfilter`|Manual load required|Bridge + Netfilter IPv4/IPv6 integration|
|`nf_flow_table`|Flowtable nftables rules|Software flowtable fast path|
|`nf_flow_table_hw`|`flags offload` in flowtable|Hardware offload extension|

---

## Debugging Netfilter

### TRACE Target (iptables)

The `TRACE` target logs each packet as it passes through every table / chain / rule:

```bash
# Enable tracing for all incoming SYN packets
iptables -t raw -A PREROUTING -p tcp --syn -j TRACE
iptables -t raw -A OUTPUT     -p tcp --syn -j TRACE

# View trace output
dmesg | grep TRACE
# Example output:
# TRACE: raw:PREROUTING:policy:1 IN=eth0 OUT= SRC=1.2.3.4 DST=10.0.0.1 ... SYN
# TRACE: mangle:PREROUTING:policy:1
# TRACE: nat:PREROUTING:rule:1
# TRACE: filter:INPUT:rule:2
```

> [!warning] `TRACE` generates extremely high volumes of output on any moderately busy system. Always use very narrow match criteria and remove the TRACE rules immediately after debugging.

### nftables Tracing

nftables has a built-in tracing mechanism:

```nftables
table inet filter {
    chain input {
        meta nftrace set 1    # enable tracing for packets matching this rule
        tcp dport 22 accept
    }
}
```

```bash
# Monitor trace events in real time
nft monitor trace
# Example output:
# trace id a1b2c3d4 inet filter input packet: ... tcp dport 22
# trace id a1b2c3d4 inet filter input rule tcp dport 22 accept (verdict accept)
```

### Counting Drops by Chain

```bash
# iptables: all rules with packet/byte counters
iptables -L -v -n

# Watch counters update in real time
watch -n1 'iptables -L -v -n'

# nftables: counters appear inline if rules include the counter statement
nft list ruleset

# Zero all iptables counters
iptables -Z
```

### Checking What Rules Are Active

```bash
# All iptables tables
for t in raw mangle nat filter security; do
    echo "=== iptables -t $t ===" && iptables -t "$t" -L -n -v
done

# ip6tables
for t in raw mangle nat filter; do
    echo "=== ip6tables -t $t ===" && ip6tables -t "$t" -L -n -v
done

# Complete nftables ruleset
nft list ruleset

# Which iptables backend is in use?
iptables --version
# "iptables v1.8.x (nf_tables)"  → iptables-nft (using nftables kernel backend)
# "iptables v1.8.x (legacy)"     → iptables-legacy (using setsockopt path)
```

---

## Common Issues

### Issue: Rules Not Matching — Wrong Backend

**Symptom:** `iptables -L` shows a rule but traffic is unaffected.

**Cause:** The system is using `iptables-nft` while rules were added with `iptables-legacy` (or vice versa). The two backends maintain separate, independent rule sets.

**Diagnosis:**

```bash
iptables-legacy -L    # rules via setsockopt (legacy path)
iptables-nft    -L    # rules via nftables kernel subsystem
nft list ruleset      # all active nftables rules (includes iptables-nft rules)
```

**Solution:** Pick one backend and migrate all rules to it.

---

### Issue: Bridged Traffic Not Filtered

**Symptom:** iptables / nftables rules have no effect on traffic between two VMs on the same bridge.

**Cause:** Bridged L2 traffic does not traverse `NFPROTO_IPV4` hooks by default.

**Solution:**

```bash
modprobe br_netfilter
sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1
```

See [[Netfilter Conntrack — Connection Tracking#Bridge Networking and nf_conntrack_bridge]].

---

### Issue: NFQUEUE Packets Dropped When No Listener

**Symptom:** Packets matched by `-j NFQUEUE` disappear when no userspace process is attached.

**Cause:** `NF_QUEUE` with no registered listener causes the kernel to drop the packet.

**Solution:** Use `--queue-bypass` to fall back to `ACCEPT` when no process is listening:

```bash
iptables -A INPUT -p tcp -j NFQUEUE --queue-num 0 --queue-bypass
```

---

### Issue: iptables Rules Lost After Reboot

**Cause:** `iptables` rules are in-memory only and not persistent by default.

**Solution:**

```bash
# Debian / Ubuntu
apt install iptables-persistent
netfilter-persistent save
systemctl enable netfilter-persistent

# RHEL / CentOS / Fedora
dnf install iptables-services
service iptables save
systemctl enable iptables

# nftables (recommended: loads /etc/nftables.conf on boot via systemd)
systemctl enable nftables
```

---

### Issue: NAT Not Working for Forwarded Traffic

**Symptom:** DNAT rule exists but packets never reach the target host.

**Checklist:**

```bash
# 1. IP forwarding must be enabled
sysctl net.ipv4.ip_forward          # must be 1
sysctl -w net.ipv4.ip_forward=1

# 2. FORWARD chain must accept the traffic
iptables -A FORWARD -d 192.168.1.100 -p tcp --dport 80 \
    -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT

# 3. conntrack must be loaded
lsmod | grep nf_conntrack

# 4. Verify DNAT rule is present in PREROUTING
iptables -t nat -L PREROUTING -n -v
```

---

### Issue: nftables and iptables-nft Conflicts

**Symptom:** Unexpected filtering or NAT behavior when both `nft` and `iptables-nft` are actively managing rules.

**Cause:** Both tools write to the same nftables kernel subsystem; their rules coexist and both are evaluated.

**Diagnosis:**

```bash
nft list ruleset    # shows ALL active rules, including those from iptables-nft
```

**Solution:** Choose one tool and flush the other's rules:

```bash
# Remove all iptables-nft rules
iptables-nft -F
iptables-nft -t nat    -F
iptables-nft -t mangle -F
iptables-nft -t raw    -F
```

---

## SYNPROXY — SYN Flood Protection

### The Problem with Naive SYN Handling

Under a SYN flood, conntrack creates a `SYN_SENT` entry for every forged SYN packet before the three-way handshake completes. The conntrack table fills with half-open entries, eventually causing legitimate traffic to be dropped with `table full` errors.

See [[Netfilter Conntrack — Connection Tracking#SYN Flood Interaction]] for conntrack-level mitigations. SYNPROXY addresses the root cause at the Netfilter level.

### What SYNPROXY Does

`SYNPROXY` intercepts incoming SYN packets and **completes the three-way handshake on behalf of the server** before the connection is forwarded. The kernel absorbs the cost of the handshake; only validated connections ever reach conntrack or the backend.

```
Without SYNPROXY:
  Attacker ──SYN──► conntrack creates SYN_SENT entry ──► server (or table full)

With SYNPROXY:
  Attacker ──SYN──────────────────────────────► SYNPROXY
  Attacker ◄──SYN+ACK (from kernel)──────────── SYNPROXY
  Attacker ──ACK──────────────────────────────► SYNPROXY validates
                                                 (forged SYNs never send ACK → no entry created)
  SYNPROXY ──new SYN──────────────────────────► server
  Server   ◄──SYN+ACK────────────────────────── server
  SYNPROXY ──ACK──────────────────────────────► server
                                                 connection ESTABLISHED in conntrack
```

### SYNPROXY Setup (iptables)

SYNPROXY must be applied in the `raw` table (before conntrack) and also allowed through in the `filter` table:

```bash
# 1. In raw PREROUTING: intercept SYN packets before conntrack sees them
#    and mark them NOTRACK so conntrack does not create a premature entry
iptables -t raw -A PREROUTING -p tcp --dport 80 --syn -j CT --notrack

# 2. In filter INPUT (or FORWARD): hand untracked SYN packets to SYNPROXY
iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate INVALID,UNTRACKED \
    -j SYNPROXY --sack-perm --timestamp --wscale 7 --mss 1460

# 3. Drop any remaining INVALID packets (failed handshakes)
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
```

### SYNPROXY Setup (nftables)

```nftables
table inet synproxy_demo {

    chain prerouting {
        type filter hook prerouting priority raw;
        # Exempt SYN packets from conntrack tracking
        tcp dport 80 tcp flags syn notrack
    }

    chain input {
        type filter hook input priority filter;

        # Hand untracked SYN and INVALID packets to SYNPROXY
        tcp dport 80 ct state { invalid, untracked } \
            synproxy mss 1460 wscale 7 timestamp sack-perm

        # Drop what SYNPROXY rejects
        ct state invalid drop
    }
}
```

### SYNPROXY Options

|Option|Description|
|---|---|
|`--mss VALUE`|Maximum Segment Size to advertise in SYN+ACK|
|`--wscale VALUE`|Window scale factor (0–14)|
|`--sack-perm`|Advertise Selective ACK support|
|`--timestamp`|Advertise TCP timestamp support (required for wscale)|
|`--ecn`|Advertise Explicit Congestion Notification support|

> [!important] Values advertised by SYNPROXY must match what the backend server actually supports. Mismatches cause performance degradation or connection failures. Profile your server's TCP options with `ss -i` or `tcpdump` first.

### sysctl: Enabling SYN Cookies

SYNPROXY works best alongside kernel SYN cookies as a secondary layer:

```bash
sysctl -w net.ipv4.tcp_syncookies=1
sysctl -w net.ipv4.tcp_timestamps=1    # required for SYN cookies with options
```

---

## TPROXY — Transparent Proxying

### What TPROXY Does

`TPROXY` redirects packets destined for a remote address to a **local socket** without altering the packet's destination IP/port. The proxy process can call `getsockname()` / `SO_ORIGINAL_DST` to learn the original destination and make protocol-aware decisions.

Unlike `REDIRECT` (which rewrites the destination to `127.0.0.1`), TPROXY leaves the IP header untouched. The proxy sees the original destination address — essential for SNI-based TLS inspection, HTTP `CONNECT`, or any protocol where the proxy must know the intended target.

### TPROXY Packet Flow

```
Client 10.0.0.5:54321 ─── SYN to 93.184.216.34:443 ──► router
                                                            │
                                         TPROXY rule fires  │
                                                            │
                                    ┌───────────────────────┘
                                    │  mark packet + redirect to
                                    │  local socket on :443
                                    ▼
                           Proxy process on router
                           sees: src=10.0.0.5:54321
                                 dst=93.184.216.34:443  ← original, unmodified
```

### Required Setup

TPROXY requires three cooperating pieces: a Netfilter rule, a policy routing rule, and a proxy socket bound with `IP_TRANSPARENT`.

#### Step 1 — iptables / nftables Rule

```bash
# iptables: mark and TPROXY incoming HTTP to local port 8080
iptables -t mangle -A PREROUTING \
    -p tcp --dport 80 \
    -j TPROXY --tproxy-mark 0x1/0x1 --on-port 8080 --on-ip 127.0.0.1

# nftables equivalent
table ip tproxy_demo {
    chain prerouting {
        type filter hook prerouting priority mangle;
        tcp dport 80 tproxy to :8080 meta mark set 0x1
    }
}
```

#### Step 2 — Policy Routing (redirect marked packets to local stack)

```bash
# Packets marked 0x1 are routed locally (not forwarded)
ip rule  add fwmark 0x1 lookup 100
ip route add local default dev lo table 100
```

#### Step 3 — Proxy Socket with IP_TRANSPARENT

The proxy must bind with `IP_TRANSPARENT` so the kernel allows it to bind to non-local addresses:

```python
import socket, struct

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_IP, socket.IP_TRANSPARENT, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('127.0.0.1', 8080))
sock.listen(128)

conn, addr = sock.accept()
# Retrieve original destination
orig_dst = conn.getsockopt(socket.SOL_IP, 80, 16)  # SO_ORIGINAL_DST = 80
port, host = struct.unpack('!2xH4s8x', orig_dst)
```

### Use Cases

- **Squid** transparent HTTP/S proxy (`tproxy` mode)
- **HAProxy** with `bind ... transparent`
- **Mitmproxy** for TLS interception
- **Kubernetes** `kube-proxy` TPROXY mode (alternative to DNAT for Services)
- Custom L7 load balancers

---

## Packet Marks and Policy Routing

### Two Independent Mark Spaces

Linux maintains two distinct per-packet/per-flow mark values:

|Mark|Location|Size|Scope|
|---|---|---|---|
|**Packet mark** (`skb->mark`)|In the `sk_buff`|32 bits|Per-packet; lost when packet leaves the system|
|**Conntrack mark** (`nf_conn.mark`)|In the conntrack entry|32 bits|Per-flow; persists across all packets of the flow|

The `MARK` / `meta mark set` target sets the packet mark. The `CONNMARK` / `ct mark set` target saves and restores between the two. Packet marks are what the kernel's routing policy database (`ip rule`) actually reads.

### Policy Routing with Marks (RPDB)

The Linux **Routing Policy Database** evaluates `ip rule` entries in order and routes packets using the matching routing table:

```bash
# Route packets marked 0x1 via routing table 10  (ISP-A)
ip rule add fwmark 0x1 lookup 10
ip route add default via 192.168.1.1 table 10

# Route packets marked 0x2 via routing table 20  (ISP-B)
ip rule add fwmark 0x2 lookup 20
ip route add default via 10.0.0.1 table 20
```

```bash
# Set mark based on source IP (sends all traffic from 192.168.2.0/24 via ISP-B)
iptables -t mangle -A PREROUTING \
    -s 192.168.2.0/24 -j MARK --set-mark 0x2

# nftables
table ip mangle_demo {
    chain prerouting {
        type filter hook prerouting priority mangle;
        ip saddr 192.168.2.0/24 meta mark set 0x2
    }
}
```

### Matching on Marks in Rules

```bash
# iptables: match packet mark (with optional mask)
iptables -A FORWARD -m mark --mark 0x10/0x10 -j ACCEPT

# nftables
meta mark 0x10 accept
meta mark & 0x10 == 0x10 accept    # with bitmask
```

---

## CONNMARK and Multi-ISP Routing

### The Problem: Per-Flow Routing Consistency

Simple mark-based routing breaks for **reply packets**. When an outbound packet is marked and sent via ISP-A, the reply arrives on ISP-A's interface. But without saving the routing decision, the reply is evaluated independently and might be sent back via ISP-B — causing an asymmetric path that ISP-A's router drops as a spoofed source.

### The CONNMARK Save/Restore Pattern

`CONNMARK` saves the packet mark into the conntrack entry on the first packet, then restores it on every subsequent packet in the flow. This makes the routing decision **sticky for the entire connection**:

```bash
# iptables CONNMARK approach
# 1. In mangle PREROUTING: restore saved connmark → packet mark
iptables -t mangle -A PREROUTING -j CONNMARK --restore-mark

# 2. If no connmark is saved yet (new flow), apply routing policy
iptables -t mangle -A PREROUTING \
    -m mark --mark 0x0 \
    -s 192.168.1.0/24 -j MARK --set-mark 0x1    # LAN-A → ISP-A

iptables -t mangle -A PREROUTING \
    -m mark --mark 0x0 \
    -s 192.168.2.0/24 -j MARK --set-mark 0x2    # LAN-B → ISP-B

# 3. In mangle POSTROUTING: save packet mark → connmark for future packets
iptables -t mangle -A POSTROUTING -j CONNMARK --save-mark
```

```nftables
# nftables equivalent
table ip mangle_demo {
    chain prerouting {
        type filter hook prerouting priority mangle;
        # Restore conntrack mark to packet mark for established flows
        ct mark != 0 meta mark set ct mark
        # New flows: assign mark by source subnet
        meta mark 0 ip saddr 192.168.1.0/24 meta mark set 0x1
        meta mark 0 ip saddr 192.168.2.0/24 meta mark set 0x2
    }
    chain postrouting {
        type filter hook postrouting priority mangle;
        # Save packet mark into conntrack entry
        meta mark != 0 ct mark set meta mark
    }
}
```

### Full Multi-ISP Routing Example

```bash
# Two uplinks: eth0 (ISP-A, GW 203.0.113.1), eth1 (ISP-B, GW 198.51.100.1)
# Internal LANs: 192.168.1.0/24 → ISP-A, 192.168.2.0/24 → ISP-B

# Routing tables
ip route add default via 203.0.113.1  dev eth0 table 10
ip route add default via 198.51.100.1 dev eth1 table 20

# Policy rules
ip rule add fwmark 0x1 lookup 10
ip rule add fwmark 0x2 lookup 20

# NAT for each ISP (using the correct source IP)
iptables -t nat -A POSTROUTING -o eth0 -j SNAT --to-source 203.0.113.5
iptables -t nat -A POSTROUTING -o eth1 -j SNAT --to-source 198.51.100.7

# Mark + save (mangle rules as above)
```

> [!note] For inbound connections (servers behind the router), the mark must be set based on the **incoming interface** (`-i eth0 → mark 0x1`) rather than the source address. Combine with CONNMARK so replies go back out the same interface.

---

## ebtables — Layer 2 Filtering

### ebtables Architecture

`ebtables` is the Ethernet bridge firewalling tool. It operates on **Ethernet frames** at Layer 2, via the `NFPROTO_BRIDGE` hook family. It is the bridge equivalent of iptables and is typically used to:

- Filter by MAC address (source or destination)
- Filter by EtherType (IPv4, IPv6, ARP, VLAN, …)
- Filter by VLAN ID (802.1Q)
- Implement bridge-level NAT (rare)
- Force Layer 2 traffic to be routed instead of bridged (`BROUTING` chain)

### ebtables Tables and Chains

ebtables has three tables:

```
Table     Chains                        Purpose
────────  ───────────────────────────   ──────────────────────────────────────────────
filter    FORWARD · INPUT · OUTPUT      Frame filtering (the primary use case)
nat       PREROUTING · OUTPUT           Frame address rewriting
          POSTROUTING
broute    BROUTING                      Bridge vs. route decision (L2/L3 demux)
```

#### filter table

```
NF_BR_PRE_ROUTING
      │
      ├── FORWARD chain    ← frames forwarded between bridge ports
      ├── INPUT chain      ← frames destined for the bridge device itself
      └── OUTPUT chain     ← frames generated by the bridge host
```

#### broute table / BROUTING chain

The `BROUTING` chain fires before the bridge makes its forwarding decision. Returning `BROUTING` (via `-j BROUTING` / `-j DROP` combined with `--redirect-target ACCEPT`) forces the frame to be **routed** (handed to the L3 stack) rather than bridged. This is used for:

- Selectively routing some traffic through the IP stack (for NAT or conntrack) while bridging everything else
- Protocol-based L2/L3 demux on the same interface

### ebtables Syntax and Common Rules

```bash
# List all rules
ebtables -L --Lx     # -Lx: machine-readable format

# Drop all frames from a specific MAC address
ebtables -A FORWARD --src 00:11:22:33:44:55 -j DROP

# Allow only ARP and IPv4 frames through the bridge
ebtables -A FORWARD -p IPv4  -j ACCEPT
ebtables -A FORWARD -p ARP   -j ACCEPT
ebtables -A FORWARD          -j DROP     # default deny

# Filter by VLAN ID (requires 802.1Q frame)
ebtables -A FORWARD -p 802_1Q --vlan-id 100 -j ACCEPT
ebtables -A FORWARD -p 802_1Q              -j DROP

# Drop IPv6 frames (e.g., to enforce IPv4-only on a bridge)
ebtables -A FORWARD -p IPv6 -j DROP

# Log frames
ebtables -A FORWARD --src 00:11:22:33:44:55 -j LOG --log-prefix "MAC_BLOCK: "

# Persist rules
ebtables-save  > /etc/ebtables.conf
ebtables-restore < /etc/ebtables.conf
```

### ebtables Match Extensions and Targets

#### Common Match Options

|Option|Description|
|---|---|
|`-p PROTO` / `--proto`|EtherType: `IPv4`, `IPv6`, `ARP`, `802_1Q`, hex value (e.g. `0x8100`)|
|`--src MAC` / `--dst MAC`|Source / destination MAC address (with optional mask: `00:11:22:33:44:55/ff:ff:ff:00:00:00`)|
|`-i IFACE` / `-o IFACE`|Incoming / outgoing bridge port|
|`--vlan-id ID`|802.1Q VLAN ID (requires `-p 802_1Q`)|
|`--vlan-prio PRIO`|802.1Q priority bits|
|`--ip-src IP`|Source IP inside an IPv4 frame (requires `-p IPv4`)|
|`--ip-dst IP`|Destination IP inside an IPv4 frame|
|`--ip-proto PROTO`|L4 protocol inside an IPv4 frame|
|`--ip-dport PORT`|Destination port inside an IPv4 TCP/UDP frame|
|`--arp-ip-src IP`|Source IP in an ARP packet|
|`--arp-ip-dst IP`|Destination IP in an ARP packet|
|`--arp-mac-src MAC`|Source MAC in an ARP packet|
|`--limit RATE`|Rate limiting (token bucket)|

#### Targets

|Target|Effect|
|---|---|
|`ACCEPT`|Accept the frame; bridge normally|
|`DROP`|Drop the frame|
|`RETURN`|Return from user chain|
|`REDIRECT`|Redirect frame to the bridge itself (nat table, changes dst MAC)|
|`LOG`|Log to kernel log and continue|
|`MARK --set-mark VALUE`|Set frame mark|
|`BROUTING`|Force frame to be routed (broute table only)|

### ebtables and br_netfilter Interaction

When `br_netfilter` is loaded, bridged IP frames additionally traverse `iptables` / `nftables` hooks. This creates a multi-level filtering architecture:

```
Frame arrives on bridge port
        │
        ▼
ebtables: filter::FORWARD       ← L2 decision (MAC, EtherType, VLAN)
        │
        ▼  (if br_netfilter loaded and frame is IPv4/IPv6)
iptables: filter::FORWARD       ← L3/L4 decision (IP, TCP ports, conntrack)
        │
        ▼
ebtables: filter::FORWARD (post-IP) ← rarely used
        │
        ▼
Frame forwarded to destination bridge port
```

> [!warning] Rule ordering With both `ebtables` and `iptables` active on a bridge, the same frame is evaluated by both. A frame ACCEPT'd by ebtables still goes through iptables. A DROP in either stops the frame. Design rules with this dual-evaluation in mind.

### nftables bridge family

nftables can replace `ebtables` using the `bridge` family:

```nftables
table bridge filter {
    chain forward {
        type filter hook forward priority 0; policy accept;

        # Drop all non-IPv4, non-ARP frames
        meta protocol != { ip, arp } drop

        # Drop frames from a specific MAC
        ether saddr 00:11:22:33:44:55 drop

        # VLAN filtering
        vlan id != { 10, 20, 30 } drop
    }
}
```

---

## IPsec and Netfilter (xfrm)

### Overview

Linux IPsec is implemented in the **xfrm** (transform) framework, which coexists with Netfilter. xfrm handles encryption/decryption and authentication of IP packets according to Security Policies (SP) and Security Associations (SA). Netfilter and xfrm share the packet path but operate at different layers.

### xfrm Hooks in the Packet Path

xfrm inserts itself at specific points relative to Netfilter hooks:

```
Incoming encrypted packet
        │
        ▼
NF_INET_PRE_ROUTING        ← Netfilter (raw, conntrack, DNAT)
        │
        ▼
xfrm policy check (inbound)
        │
        ▼
xfrm decrypt / authenticate  ← IPsec processing (AH/ESP)
        │
        ▼
NF_INET_LOCAL_IN / FORWARD   ← Netfilter sees the DECRYPTED packet here

Outgoing plaintext packet
        │
        ▼
NF_INET_LOCAL_OUT / FORWARD  ← Netfilter sees plaintext
        │
        ▼
xfrm policy check (outbound)
        │
        ▼
xfrm encrypt / sign          ← IPsec processing
        │
        ▼
NF_INET_POST_ROUTING         ← Netfilter sees the ENCRYPTED packet
```

> [!important] Netfilter rules in `FORWARD` and `INPUT` operate on the **decrypted** inner packet. Netfilter rules in `POSTROUTING` and `PREROUTING` operate on the **encrypted** outer packet. Write rules for the inner packet (post-decryption) when you want to filter IPsec traffic content.

### Matching IPsec Policy in Firewall Rules

#### iptables — `-m policy`

The `policy` match module lets you match packets based on their IPsec processing state:

```bash
# Accept packets that arrived via an IPsec tunnel (decrypted inbound)
iptables -A INPUT \
    -m policy --pol ipsec --dir in --proto esp \
    -j ACCEPT

# Accept packets that will be sent via an IPsec tunnel (outbound)
iptables -A OUTPUT \
    -m policy --pol ipsec --dir out --proto esp \
    -j ACCEPT

# Match by specific tunnel parameters
iptables -A FORWARD \
    -m policy --pol ipsec --dir in \
    --tunnel-src 203.0.113.1 --tunnel-dst 198.51.100.1 \
    -j ACCEPT

# Drop non-IPsec traffic on an interface that should only carry IPsec
iptables -A INPUT -i eth0 \
    -m policy --pol none --dir in \
    -j DROP
```

#### iptables `-m policy` Options

|Option|Description|
|---|---|
|`--pol ipsec\|none`|Match packets that are / are not IPsec-processed|
|`--dir in\|out`|Direction of the IPsec policy|
|`--proto esp\|ah`|IPsec protocol|
|`--spi VALUE`|Match on Security Parameter Index|
|`--tunnel-src IP`|IPsec tunnel outer source address|
|`--tunnel-dst IP`|IPsec tunnel outer destination address|
|`--strict`|Match all `--next` parameters strictly|

#### nftables — `ipsec` expression

```nftables
table inet ipsec_filter {
    chain input {
        type filter hook input priority filter;

        # Accept inbound ESP-decrypted packets from a known peer
        ipsec in ip saddr 203.0.113.1 accept

        # Drop traffic on a dedicated IPsec interface that bypassed processing
        ipsec in ip protocol != esp drop
    }

    chain output {
        type filter hook output priority filter;
        ipsec out accept
    }
}
```

### xfrm and Conntrack

By default, conntrack tracks the **outer** encrypted ESP/AH packets (identified by SPI rather than ports). The inner plaintext traffic is tracked separately once decrypted. The `nf_conntrack_proto_generic` module handles ESP; more precise per-flow tracking is possible with custom xfrm policies.

```bash
# View ESP flows in conntrack
conntrack -L -p esp
# esp 50 timeout=...  src=203.0.113.1 dst=198.51.100.1 spi=0x12345678 ...
```

---

## nfacct — Kernel Accounting Objects

### What nfacct Does

`nfacct` (Netfilter accounting) provides **named, kernel-resident byte/packet counters** that are independent of any specific firewall rule. Multiple rules across different tables, chains, and even namespaces can increment the same counter. This is useful for:

- Billing (per-customer traffic accounting)
- Quota enforcement
- Traffic monitoring without restructuring existing rules

### Installation

```bash
# Debian/Ubuntu
apt install nfacct

# RHEL/Fedora
dnf install libnetfilter_acct
```

### Managing Accounting Objects

```bash
# Create a named counter
nfacct add http_traffic
nfacct add dns_traffic

# List all counters
nfacct list

# Read a specific counter (outputs packets + bytes)
nfacct get http_traffic
# {pkts = 142034, bytes = 98304512}

# Reset a counter (read and zero atomically)
nfacct flush http_traffic

# Delete a counter
nfacct del http_traffic
```

### Using nfacct in iptables

```bash
# Count all HTTP and HTTPS traffic
iptables -A FORWARD -p tcp --dport 80  -m nfacct --nfacct-name http_traffic
iptables -A FORWARD -p tcp --dport 443 -m nfacct --nfacct-name http_traffic
iptables -A FORWARD -p udp --dport 53  -m nfacct --nfacct-name dns_traffic

# Count return traffic too
iptables -A FORWARD -p tcp --sport 80  -m nfacct --nfacct-name http_traffic
iptables -A FORWARD -p tcp --sport 443 -m nfacct --nfacct-name http_traffic
```

> [!note] The `nfacct` match is **non-terminating** — it increments the counter and rule evaluation continues. Combine it with any other match expression.

### Using nfacct in nftables

```nftables
table inet accounting {
    counter http_traffic { }
    counter dns_traffic  { }

    chain forward {
        type filter hook forward priority filter;
        tcp dport { 80, 443 } add @http_traffic { ip saddr . ip daddr counter }
        udp dport 53          counter name "dns_traffic"
    }
}
```

### Quota Enforcement

`nfacct` objects can also act as **quotas**: once the byte limit is reached, the kernel sets a flag that can be matched to drop further traffic:

```bash
# Create a quota: 1 GiB per month
nfacct add monthly_quota --quota --bytes 1073741824

# Match traffic after quota is exceeded
iptables -A FORWARD -m nfacct --nfacct-name monthly_quota \
    -m nfacct --nfacct-name monthly_quota --nfacct-quota-flag \
    -j DROP
```

---

## The security Table and SELinux / AppArmor

### Purpose

The `security` table (priority `50` in the hook stack — after `filter`) is reserved for **Mandatory Access Control** (MAC) systems such as SELinux and AppArmor. It provides hooks where security modules can apply labels to packets and enforce policy on them.

### SECMARK Target

`SECMARK` sets a **security context label** on a packet (`skb->secmark`). The label is a 32-bit value mapped to a SELinux / AppArmor context string:

```bash
# iptables: label incoming SSH packets with the SELinux context "system_u:object_r:ssh_packet_t:s0"
iptables -t security -A INPUT -p tcp --dport 22 \
    -j SECMARK --selctx "system_u:object_r:ssh_packet_t:s0"

# Label outgoing web traffic
iptables -t security -A OUTPUT -p tcp --dport 80 \
    -j SECMARK --selctx "system_u:object_r:http_packet_t:s0"
```

### CONNSECMARK Target

`CONNSECMARK` saves the packet's security label into the conntrack entry (and restores it on subsequent packets), avoiding re-labelling on every packet of an established flow:

```bash
# Save the security mark from the first packet into the conntrack entry
iptables -t security -A INPUT -m conntrack --ctstate NEW \
    -j SECMARK --selctx "system_u:object_r:http_packet_t:s0"

# Restore the saved label to subsequent packets
iptables -t security -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED \
    -j CONNSECMARK --restore
```

### How SELinux Uses SECMARK

When a packet's `skb->secmark` is set, the SELinux network enforcement code compares it against the policy for the receiving or sending process. If the process's type does not have `recv_msg` or `send_msg` permission for the packet's security context, the packet is denied at the socket layer.

```bash
# Check SELinux packet labelling
ausearch -m avc -ts recent | grep packet
# type=AVC msg=audit(...): avc: denied { recv_msg } ...
#     tclass=packet permissive=0

# View current SECMARK rules
iptables -t security -L -nv
```

### nftables Security Integration

```nftables
table inet security {
    chain input {
        type filter hook input priority security;
        tcp dport 22 meta secmark set "system_u:object_r:ssh_packet_t:s0"
        ct state established ct secmark != 0 meta secmark set ct secmark
    }
}
```

---

## Comprehensive nftables Firewall Baseline

A production-ready stateful firewall for a **server** with IPv4 + IPv6, default-deny input, stateful forward, and logging:

```nftables
#!/usr/sbin/nft -f
# /etc/nftables.conf

flush ruleset

table inet filter {

    # ---------------------------------------------------------------------------
    # Sets (populated at runtime or from provisioning)
    # ---------------------------------------------------------------------------
    set trusted_mgmt {
        type ipv4_addr
        flags interval
        elements = { 10.0.0.0/8, 192.168.0.0/16 }
    }

    set blocked_sources {
        type ipv4_addr
        flags interval, timeout
        timeout 1h
    }

    # ---------------------------------------------------------------------------
    # Counters
    # ---------------------------------------------------------------------------
    counter blocked_invalid  { }
    counter blocked_syn_flood { }
    counter accepted_new     { }

    # ---------------------------------------------------------------------------
    # Raw — before conntrack (NOTRACK for stateless high-rate traffic)
    # ---------------------------------------------------------------------------
    chain raw_prerouting {
        type filter hook prerouting priority raw; policy accept;

        # Loopback never needs tracking
        iif "lo" notrack

        # DNS server: exempt DNS from conntrack
        # udp dport 53 notrack
    }

    # ---------------------------------------------------------------------------
    # Input chain
    # ---------------------------------------------------------------------------
    chain input {
        type filter hook input priority filter; policy drop;

        # Loopback
        iif "lo" accept

        # Established / related (fast path — must be first)
        ct state established,related accept

        # Invalid — log and drop
        ct state invalid counter name "blocked_invalid" \
            log prefix "NF_INVALID: " level warn drop

        # ICMPv4 — allow essential types only
        ip protocol icmp icmp type {
            echo-request,           # ping
            destination-unreachable,
            time-exceeded,
            parameter-problem
        } accept

        # ICMPv6 — required for NDP; allow essential types only
        ip6 nexthdr ipv6-icmp icmpv6 type {
            echo-request,
            destination-unreachable,
            packet-too-big,
            time-exceeded,
            parameter-problem,
            nd-router-advert,
            nd-neighbor-solicit,
            nd-neighbor-advert,
            nd-router-solicit
        } accept

        # Management access: SSH restricted to trusted subnets
        tcp dport 22 ip saddr @trusted_mgmt \
            ct state new counter name "accepted_new" accept

        # Public services
        tcp dport { 80, 443 } ct state new \
            counter name "accepted_new" accept

        # Dynamic block list
        ip saddr @blocked_sources drop

        # SYN flood protection: rate-limit new TCP connections
        tcp flags syn ct state new \
            limit rate over 200/second burst 500 packets \
            counter name "blocked_syn_flood" \
            log prefix "NF_SYNFLOOD: " level warn drop

        # Log and drop everything else
        log prefix "NF_INPUT_DROP: " level info
        drop
    }

    # ---------------------------------------------------------------------------
    # Forward chain (for a router / gateway / container host)
    # ---------------------------------------------------------------------------
    chain forward {
        type filter hook forward priority filter; policy drop;

        ct state established,related accept
        ct state invalid drop

        # Allow LAN → WAN
        iifname "eth1" oifname "eth0" ct state new accept

        # Default deny with logging
        log prefix "NF_FORWARD_DROP: " level info
        drop
    }

    # ---------------------------------------------------------------------------
    # Output chain (optional; default accept is common for servers)
    # ---------------------------------------------------------------------------
    chain output {
        type filter hook output priority filter; policy accept;

        ct state invalid drop
    }
}

# ---------------------------------------------------------------------------
# NAT table (for gateway / router role)
# ---------------------------------------------------------------------------
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat;
        oifname "eth0" masquerade
    }
}
```

---

## Comprehensive iptables Firewall Baseline

The equivalent server baseline for legacy `iptables`/`ip6tables`:

```bash
#!/bin/bash
# /etc/iptables/rules.sh

IPT="iptables"
IP6T="ip6tables"

# --- Flush and set policies ---
$IPT  -F; $IPT  -X; $IPT  -Z
$IP6T -F; $IP6T -X; $IP6T -Z

$IPT  -P INPUT DROP;   $IPT  -P FORWARD DROP; $IPT  -P OUTPUT ACCEPT
$IP6T -P INPUT DROP;   $IP6T -P FORWARD DROP; $IP6T -P OUTPUT ACCEPT

# --- Loopback ---
$IPT  -A INPUT -i lo -j ACCEPT
$IP6T -A INPUT -i lo -j ACCEPT

# --- Established / Related ---
$IPT  -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
$IP6T -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# --- Invalid ---
$IPT  -A INPUT   -m conntrack --ctstate INVALID -j LOG --log-prefix "NF_INVALID: "
$IPT  -A INPUT   -m conntrack --ctstate INVALID -j DROP
$IP6T -A INPUT   -m conntrack --ctstate INVALID -j DROP

# --- ICMPv4 ---
$IPT -A INPUT -p icmp --icmp-type echo-request          -j ACCEPT
$IPT -A INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
$IPT -A INPUT -p icmp --icmp-type time-exceeded          -j ACCEPT
$IPT -A INPUT -p icmp --icmp-type parameter-problem      -j ACCEPT

# --- ICMPv6 (required for NDP) ---
$IP6T -A INPUT -p ipv6-icmp -j ACCEPT

# --- SYN flood protection ---
$IPT  -A INPUT -p tcp --syn -m hashlimit \
    --hashlimit-name synflood \
    --hashlimit-above 200/second \
    --hashlimit-burst 500 \
    --hashlimit-mode srcip \
    -j LOG --log-prefix "NF_SYNFLOOD: "
$IPT  -A INPUT -p tcp --syn -m hashlimit \
    --hashlimit-name synflood \
    --hashlimit-above 200/second \
    --hashlimit-burst 500 \
    --hashlimit-mode srcip \
    -j DROP

# --- Public services ---
$IPT  -A INPUT -p tcp -m multiport --dports 80,443 -m conntrack --ctstate NEW -j ACCEPT
$IP6T -A INPUT -p tcp -m multiport --dports 80,443 -m conntrack --ctstate NEW -j ACCEPT

# --- SSH (restrict to management subnet) ---
$IPT  -A INPUT -p tcp --dport 22 -s 10.0.0.0/8       -m conntrack --ctstate NEW -j ACCEPT
$IPT  -A INPUT -p tcp --dport 22 -s 192.168.0.0/16   -m conntrack --ctstate NEW -j ACCEPT
$IP6T -A INPUT -p tcp --dport 22 -s fe80::/10         -m conntrack --ctstate NEW -j ACCEPT

# --- Log remaining INPUT ---
$IPT  -A INPUT -j LOG --log-prefix "NF_INPUT_DROP: " --log-level 6
$IP6T -A INPUT -j LOG --log-prefix "NF_INPUT_DROP: " --log-level 6

# --- FORWARD (gateway role) ---
$IPT  -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
$IPT  -A FORWARD -m conntrack --ctstate INVALID -j DROP
$IPT  -A FORWARD -i eth1 -o eth0 -m conntrack --ctstate NEW -j ACCEPT

# --- NAT (gateway role) ---
$IPT  -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

---

## Rate Limiting Patterns

### Per-Source Rate Limiting with hashlimit

`hashlimit` maintains a **separate token bucket per tracked key** (source IP, destination IP, source port, or combinations). This makes it far more useful than `limit` for anti-abuse rules.

```bash
# iptables: allow at most 10 new SSH connections per source IP per minute
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m hashlimit \
    --hashlimit-name ssh_conn \
    --hashlimit-above 10/minute \
    --hashlimit-burst 5 \
    --hashlimit-mode srcip \
    -j DROP

# nftables: equivalent with limit per source
table inet ratelimit {
    chain input {
        type filter hook input priority filter;
        tcp dport 22 ct state new \
            add @ssh_sources { ip saddr limit rate over 10/minute burst 5 packets } \
            drop
    }
}
```

#### hashlimit Modes

|Mode (`--hashlimit-mode`)|Tracks per …|
|---|---|
|`srcip`|Source IP address|
|`dstip`|Destination IP address|
|`srcport`|Source port|
|`dstport`|Destination port|
|`srcip,dstip`|Source + destination IP pair|
|`srcip,dstport`|Source IP + destination port|

#### hashlimit Parameters

|Parameter|Description|
|---|---|
|`--hashlimit-above RATE`|Drop if rate **exceeds** this value|
|`--hashlimit-upto RATE`|Accept if rate is **at or below** this value|
|`--hashlimit-burst N`|Initial token bucket depth (burst allowance)|
|`--hashlimit-mode MODES`|What to track (see above)|
|`--hashlimit-name NAME`|Name for the internal hash table (required)|
|`--hashlimit-htable-size N`|Hash table bucket count (default: 512)|
|`--hashlimit-htable-expire MS`|How long to keep idle entries (milliseconds)|

### Dynamic Blocking with nftables Sets

nftables `dynamic` sets allow the **packet path itself** to add entries, enabling automatic blocking without external daemons:

```nftables
table inet dynamic_block {

    # Set of source IPs that have exceeded the rate limit; auto-expire after 5 minutes
    set abusers {
        type ipv4_addr
        flags dynamic, timeout
        timeout 5m
    }

    chain input {
        type filter hook input priority filter; policy accept;

        # Drop IPs already in the abuser set
        ip saddr @abusers drop

        # If an IP sends more than 100 SYNs/second, add to abuser set and drop
        tcp flags syn ct state new \
            add @abusers { ip saddr limit rate over 100/second } drop
    }
}
```

This pattern replaces the common `fail2ban` use case for network-level blocking without the overhead of a userspace daemon parsing log files.

### The recent Module (iptables)

The `recent` module maintains a **kernel-side list** of recently seen IP addresses and lets you match based on access history:

```bash
# Rate-limit SSH to 4 attempts per 60 seconds per source IP
# Step 1: if the IP has been seen 4+ times in 60 s, drop
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --name SSH --rcheck --seconds 60 --hitcount 4 -j DROP

# Step 2: record the connection attempt
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --name SSH --set -j ACCEPT

# The same effect as fail2ban but entirely in-kernel; no log parsing required
```

#### recent Module Options

|Option|Description|
|---|---|
|`--set`|Add source IP to the named list|
|`--rcheck`|Check if the IP is in the list; do not update timestamp|
|`--update`|Check if the IP is in the list; update timestamp if found|
|`--remove`|Remove source IP from the list|
|`--seconds N`|Only match entries added within the last N seconds|
|`--hitcount N`|Only match if the IP has been seen N or more times|
|`--name NAME`|Named list (default: `DEFAULT`)|
|`--rsource` / `--rdest`|Track by source IP (default) or destination IP|

> [!note] /proc interface The `recent` module exposes its lists at `/proc/net/xt_recent/`. You can manually add or remove IPs by writing to these files:
> 
> ```bash
> echo +192.0.2.1 > /proc/net/xt_recent/SSH   # add
> echo -192.0.2.1 > /proc/net/xt_recent/SSH   # remove
> ```

---

## nf_tables Bytecode Virtual Machine

### Architecture

The nftables kernel engine (`nf_tables`) uses a **register-based bytecode virtual machine** to execute rules. When you run `nft add rule`, the kernel compiles the rule into a sequence of bytecode instructions. At packet time, the VM evaluates the bytecode directly — no textual rule parsing, no per-rule function dispatch table like legacy iptables.

### VM Registers

The nf_tables VM has:

- **16 data registers** of 4 bytes each (`NFT_REG32_00` … `NFT_REG32_15`) — used to hold intermediate values (IP addresses, ports, computed results)
- **1 verdict register** — holds the current verdict (`NF_ACCEPT`, `NF_DROP`, jump target, etc.)

Larger values (IPv6 addresses, 128-bit labels) use multiple consecutive 32-bit registers.

### Expression Types (VM Opcodes)

Each nftables "expression" is one VM instruction:

|Expression|Operation|
|---|---|
|`payload`|Read packet bytes into a register (e.g., IP src addr, TCP dst port)|
|`cmp`|Compare register value to a constant; update verdict on mismatch|
|`lookup`|Check register value against a set; set verdict on hit/miss|
|`immediate`|Load a constant into a register or set the verdict register|
|`bitwise`|Bitwise AND/OR/XOR/shift on a register|
|`byteorder`|Convert byte order (network ↔ host) in a register|
|`meta`|Read packet metadata (iif, oif, mark, l4proto, …) into a register|
|`ct`|Read conntrack fields into a register|
|`counter`|Increment a named counter|
|`log`|Emit a log message and continue|
|`nat`|Perform SNAT/DNAT address rewriting|
|`queue`|Emit NF_QUEUE verdict|
|`limit`|Token-bucket rate check|
|`dynset`|Add/update/delete an element in a dynamic set|

### Example: How `tcp dport 80 accept` Compiles

```
Rule text:  tcp dport 80 accept

Bytecode:
  1. meta l4proto → reg[0]          # load L4 protocol
  2. cmp reg[0] == 0x06             # is it TCP? (0x06)
     └─ if no: continue to next rule (no verdict change)
  3. payload (transport, dport) → reg[0]   # load destination port
  4. cmp reg[0] == 0x0050           # is it 80 (0x0050 big-endian)?
     └─ if no: continue to next rule
  5. immediate → verdict = NF_ACCEPT      # set verdict register
```

The verdict register is checked after all expressions in a rule run. If it was set to a terminating value, rule evaluation stops.

### Performance Implications

- **No per-rule function pointer dispatch**: the bytecode is a flat array evaluated by a tight loop (`nft_do_chain`), which is CPU cache-friendly.
- **Set lookups are O(1)**: the `lookup` expression uses the set's hash or rbtree structure — regardless of set size, lookup cost is bounded.
- **JIT compilation**: on x86-64, the kernel optionally JIT-compiles nftables bytecode to native machine code via the `CONFIG_NF_TABLES_JIT` option, giving another 20–40% speedup over the interpreter.

```bash
# Check if JIT is enabled
sysctl net.core.bpf_jit_enable   # 1 = enabled (shared with eBPF JIT)
```

---

## x_tables Infrastructure (Legacy)

### What x_tables Is

`x_tables` (`xt_*`) is the **shared kernel infrastructure** underlying all legacy iptables tools:

- `iptables` (IPv4 filtering) → `x_tables` + `ip_tables`
- `ip6tables` (IPv6 filtering) → `x_tables` + `ip6_tables`
- `arptables` (ARP filtering) → `x_tables` + `arp_tables`
- `ebtables` (bridge filtering) → `x_tables` + `ebt_*`

It provides the common framework for match extensions (`xt_conntrack.ko`, `xt_multiport.ko`, …) and target extensions (`xt_MARK.ko`, `xt_LOG.ko`, …).

### Rule Evaluation Model

Legacy iptables uses a **linear array** of rules stored in a kernel blob:

```
iptables internal representation:
  [ rule 1: match_list + target ]
  [ rule 2: match_list + target ]
  ...
  [ rule N: match_list + target ]
  [ policy (default verdict)    ]
```

For each packet, the kernel walks the array from index 0. For each rule:

1. Evaluates all match extensions in sequence (short-circuits on first miss).
2. If all matches pass → invokes the target.
3. If the target is terminating (`ACCEPT`, `DROP`, `REJECT`) → stops.
4. If the target is non-terminating (`LOG`, `MARK`, `CONNMARK`) → continues to next rule.
5. If the target is a **user chain jump** → recursively evaluates that chain, then returns.

### The xt_table Lock

iptables rule updates require replacing the entire rule blob atomically. In older kernels this used a **per-table spinlock** (`xt_table.lock`), which caused lock contention under high connection rates on multi-core systems. Newer kernels (since ~4.x) use per-CPU rule blobs to reduce contention, but the fundamental linear-scan model remains.

### Why nftables Supersedes x_tables

|Dimension|x_tables (iptables)|nf_tables (nftables)|
|---|---|---|
|Rule evaluation|Linear scan, O(n)|Bytecode VM, O(1) for set lookups|
|Multi-protocol|Separate binaries (`iptables`, `ip6tables`, `arptables`, `ebtables`)|Single `nft` binary, all families|
|Atomic updates|Full table replace (locks)|Transactional batch via Netlink|
|Large address lists|Requires ipset (external)|Native sets, built-in|
|Dynamic modification|Requires full rule reload|`nft add element` at runtime|
|Kernel interface|`setsockopt` (old, opaque binary blob)|Netlink (structured messages)|

> [!note] Coexistence and migration `iptables-nft` (the default `iptables` on modern distros) translates iptables syntax into nftables bytecode under the hood, letting you migrate incrementally. The `iptables-translate` command converts individual rules. Both can coexist as long as you are aware they share the same nftables kernel state (visible with `nft list ruleset`).

---

## Connection Limiting (connlimit)

### What connlimit Does

The `connlimit` match counts the number of **active conntrack entries** that share a given key (source IP, destination IP, or a subnet prefix) and lets you limit how many simultaneous connections a single host can maintain. Unlike `hashlimit`, which limits connection rate, `connlimit` limits **concurrent count**.

### iptables connlimit

```bash
# Allow at most 20 simultaneous HTTP connections per source IP
iptables -A INPUT -p tcp --dport 80 \
    -m connlimit --connlimit-above 20 --connlimit-mask 32 \
    -j REJECT --reject-with tcp-reset

# Allow at most 5 simultaneous SSH connections per /24 subnet
iptables -A INPUT -p tcp --dport 22 \
    -m connlimit --connlimit-above 5 --connlimit-mask 24 \
    -j DROP

# Limit total concurrent connections to a service (all sources combined)
iptables -A INPUT -p tcp --dport 3306 \
    -m connlimit --connlimit-above 100 --connlimit-mask 0 \
    -j DROP
```

#### connlimit Options

|Option|Description|
|---|---|
|`--connlimit-above N`|Match if the connection count **exceeds** N|
|`--connlimit-upto N`|Match if the connection count is **at or below** N|
|`--connlimit-mask BITS`|Group IPs into subnets of this prefix length. `32` (IPv4) or `128` (IPv6) = per-host. `0` = count all IPs together|
|`--connlimit-saddr`|Count by source address (default)|
|`--connlimit-daddr`|Count by destination address|

### nftables connlimit

```nftables
table inet climit {
    chain input {
        type filter hook input priority filter;

        # Allow at most 20 concurrent connections per source IP on port 80
        tcp dport 80 ct state new \
            meter http_limit { ip saddr ct count over 20 } \
            reject with tcp reset

        # Allow at most 5 concurrent SSH connections per /24
        tcp dport 22 ct state new \
            meter ssh_limit { ip saddr and 255.255.255.0 ct count over 5 } \
            drop
    }
}
```

### connlimit vs hashlimit

|Criterion|`connlimit`|`hashlimit`|
|---|---|---|
|What it limits|Simultaneous connections (current count)|Connection rate (new connections per time)|
|Use case|"No single IP may hold > N open connections"|"No single IP may open > N new connections/second"|
|State required|Yes — queries conntrack table|No — maintains its own hash table|

> [!note] `connlimit` relies on the conntrack table being accurate. If conntrack is disabled (via `CT --notrack`) for the relevant traffic, `connlimit` will see a count of zero and never trigger.

---

## Traffic Shaping and QoS Marks

### Overview

Netfilter's packet mark (`skb->mark`) and DSCP bits are the two main mechanisms for integrating Netfilter rules with Linux's traffic shaping system. The general pattern is:

1. Netfilter **marks** packets in the `mangle` table based on whatever criteria (protocol, source, destination, conntrack state).
2. `tc` (Traffic Control) **classifies** packets by reading the mark or DSCP and places them into the appropriate queue discipline.

### DSCP Marking

DSCP (Differentiated Services Code Point) is a 6-bit field in the IP header ToS byte. It is preserved hop-to-hop across routers that support DiffServ, making it suitable for end-to-end QoS.

#### iptables DSCP

```bash
# Mark VoIP RTP traffic (ports 16384–32767) as Expedited Forwarding (EF = 0x2e)
iptables -t mangle -A POSTROUTING \
    -p udp --dport 16384:32767 \
    -j DSCP --set-dscp-class EF

# Mark interactive SSH as CS2 (assured forwarding)
iptables -t mangle -A POSTROUTING \
    -p tcp --dport 22 \
    -j DSCP --set-dscp-class CS2

# Mark bulk backup traffic as Best Effort (0x00)
iptables -t mangle -A POSTROUTING \
    -p tcp --dport 22000 \
    -j DSCP --set-dscp 0x00
```

#### nftables DSCP

```nftables
table ip qos {
    chain postrouting {
        type filter hook postrouting priority mangle;

        # VoIP: Expedited Forwarding
        udp dport 16384-32767 ip dscp set ef

        # Interactive: CS2
        tcp dport 22 ip dscp set cs2

        # Bulk transfers: Best Effort
        tcp dport { 8000, 22000, 9418 } ip dscp set cs0
    }
}
```

#### DSCP Classes Quick Reference

|Class|DSCP value|Use case|
|---|---|---|
|`EF`|`0x2e` (46)|VoIP, real-time interactive|
|`AF41`|`0x22` (34)|Video conferencing|
|`AF31`|`0x1a` (26)|Streaming media|
|`AF21`|`0x12` (18)|Transactional data|
|`AF11`|`0x0a` (10)|High-throughput data|
|`CS2`|`0x10` (16)|Network operations (SSH, SNMP)|
|`CS0` / `BE`|`0x00` (0)|Best effort (default)|

### Integration with tc (Traffic Control)

The most common pattern is marking in `mangle POSTROUTING` and then classifying in `tc`:

```bash
# Mark high-priority traffic (VoIP) with mark 0x10
iptables -t mangle -A POSTROUTING \
    -p udp --dport 16384:32767 -j MARK --set-mark 0x10

# Mark bulk traffic with mark 0x20
iptables -t mangle -A POSTROUTING \
    -p tcp --dport 22000 -j MARK --set-mark 0x20

# TC: attach HTB (Hierarchical Token Bucket) to eth0
tc qdisc add dev eth0 root handle 1: htb default 30

# Root class (100 Mbps ceiling)
tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit

# Class 10: VoIP — guaranteed 20 Mbps, burst to 100 Mbps
tc class add dev eth0 parent 1:1 classid 1:10 htb rate 20mbit ceil 100mbit

# Class 20: Bulk — guaranteed 10 Mbps
tc class add dev eth0 parent 1:1 classid 1:20 htb rate 10mbit ceil 50mbit

# Class 30: Default — best effort
tc class add dev eth0 parent 1:1 classid 1:30 htb rate 5mbit ceil 100mbit

# TC filters: steer marked packets into HTB classes
tc filter add dev eth0 parent 1: protocol ip handle 0x10 fw classid 1:10
tc filter add dev eth0 parent 1: protocol ip handle 0x20 fw classid 1:20
```

```
Packet arrives at mangle POSTROUTING
    │
    ├── VoIP (udp 16384-32767)  → MARK 0x10 → tc classid 1:10 (20 Mbps guaranteed)
    ├── Bulk (tcp 22000)        → MARK 0x20 → tc classid 1:20 (10 Mbps)
    └── Everything else         → no mark  → tc classid 1:30 (best effort)
```

> [!note] `tc` reads the mark from `skb->mark`, so the MARK target in Netfilter and tc's `fw` filter speak the same language. For DSCP-based classification in tc, use `tc filter ... protocol ip u32 match ip dscp ...` instead.

---

## IPv6-Specific Rules and Considerations

### ICMPv6 Requirements

IPv6 relies heavily on ICMPv6 for core functionality that IPv4 delegated to ARP and separate protocols. **ICMPv6 must never be globally dropped.** The following ICMPv6 types are required for a functional IPv6 network:

|ICMPv6 type|Code|Function|Required?|
|---|---|---|---|
|1|—|Destination Unreachable|Yes (PMTUD)|
|2|—|Packet Too Big|**Critical** (PMTUD)|
|3|—|Time Exceeded|Yes (traceroute)|
|4|—|Parameter Problem|Yes|
|128|—|Echo Request (ping6)|Recommended|
|129|—|Echo Reply|Recommended|
|133|—|Router Solicitation|Yes (SLAAC)|
|134|—|Router Advertisement|Yes (SLAAC)|
|135|—|Neighbor Solicitation|**Critical** (NDP/ARP equiv)|
|136|—|Neighbor Advertisement|**Critical** (NDP/ARP equiv)|
|143|—|MLD v2 Report|Yes (multicast)|

```nftables
# nftables: accept all required ICMPv6
ip6 nexthdr ipv6-icmp icmpv6 type {
    destination-unreachable,
    packet-too-big,
    time-exceeded,
    parameter-problem,
    echo-request,
    echo-reply,
    nd-router-solicit,
    nd-router-advert,
    nd-neighbor-solicit,
    nd-neighbor-advert,
    mld2-listener-report
} accept
```

> [!warning] Dropping `packet-too-big` (type 2) breaks **Path MTU Discovery** for IPv6. Unlike IPv4, IPv6 routers do not fragment packets — the source host must reduce its MSS. Without PMTUD feedback, connections to hosts beyond a smaller-MTU link silently stall after the initial handshake.

### IPv6 Extension Header Matching

IPv6 uses chained **extension headers** instead of IPv4's option fields. Netfilter can match on the presence or content of extension headers:

```bash
# iptables: match packets with a routing extension header (type 0 — deprecated, dangerous)
ip6tables -A INPUT \
    -m rt --rt-type 0 \
    -j DROP

# Match packets with a fragment extension header
ip6tables -A INPUT \
    -m frag --fragfirst \
    -j DROP     # drop first fragment of a fragmented packet (e.g., for DoS mitigation)

# Match packets with hop-by-hop options header
ip6tables -A INPUT \
    -m hbh \
    -j LOG --log-prefix "HBH_HEADER: "
```

```nftables
# nftables: drop routing header type 0 (deprecated; used in amplification attacks)
ip6 nexthdr ipv6-route rt type 0 drop

# Drop packets containing a fragment header aimed at local delivery
ip6 nexthdr frag frag frag-off 0 drop
```

#### IPv6 Extension Header Modules (iptables)

|Module|Matches|
|---|---|
|`-m rt`|Routing header (`--rt-type`, `--rt-segsleft`)|
|`-m frag`|Fragment header (`--fragfirst`, `--fraglast`, `--fragmore`, `--fragid`)|
|`-m hbh`|Hop-by-hop options header|
|`-m dst`|Destination options header|
|`-m ah`|Authentication header (IPsec AH)|
|`-m eui64`|EUI-64 address check (SLAAC-generated addr validation)|
|`-m ipv6header`|Presence of any specific header type|

### IPv6 Address Types and Unique Concerns

|Address range|Type|Consideration|
|---|---|---|
|`::1/128`|Loopback|Always allow on `lo`|
|`fe80::/10`|Link-local|Required for NDP; never route globally|
|`fc00::/7`|Unique local (ULA)|Private; treat like RFC1918|
|`ff00::/8`|Multicast|Allow MLDv2 (143); others optional|
|`2000::/3`|Global unicast|Public addresses|
|`::ffff:0:0/96`|IPv4-mapped|Treat with IPv4 rules|
|`2002::/16`|6to4|Tunnel addresses; block if not used|

```nftables
# Block IPv6 source routing (type 0 routing header — CVE-2007-2242)
ip6 nexthdr ipv6-route rt type 0 drop

# Never accept packets claiming to come from loopback externally
ip6 saddr ::1 iif != "lo" drop
ip6 daddr ::1 oif != "lo" drop

# Block obvious spoofed source addresses inbound from WAN
ip6 saddr fe80::/10   iif "eth0" drop   # link-local from WAN is bogus
ip6 saddr ::1/128     iif "eth0" drop
ip6 saddr fc00::/7    iif "eth0" drop   # ULA from WAN
```

---

## Docker Networking Chains

### Docker Chain Architecture

When Docker is installed and running with the default `iptables` integration enabled, it injects several chains into the host's iptables rule set. These are created at Docker daemon startup and rebuilt whenever containers start or stop.

```
Table: filter

INPUT chain
  └── (Docker does not normally touch INPUT)

FORWARD chain
  ├── DOCKER-USER          ← user-defined rules go HERE (evaluated first)
  ├── DOCKER-ISOLATION-STAGE-1
  │     └── DOCKER-ISOLATION-STAGE-2   ← prevents inter-network bridging
  └── DOCKER               ← per-container DNAT allow rules

Table: nat

PREROUTING chain
  └── DOCKER               ← port-mapping DNAT rules

OUTPUT chain
  └── DOCKER               ← local DNAT for port mappings to 127.0.0.1

POSTROUTING chain
  └── MASQUERADE rules      ← outbound SNAT per docker network
```

### Docker Chain Details

#### DOCKER chain (nat::PREROUTING)

Docker inserts a DNAT rule here for every `-p HOST:CONTAINER` port mapping:

```bash
# Example: container mapped with -p 8080:80
# Docker inserts:
iptables -t nat -A DOCKER \
    ! -i docker0 -p tcp --dport 8080 \
    -j DNAT --to-destination 172.17.0.2:80

# Inspect what Docker has inserted
iptables -t nat -L DOCKER -n -v
```

#### DOCKER chain (filter::FORWARD)

Docker inserts a rule here to allow forwarded traffic to reach containers that have port mappings:

```bash
# Docker inserts for each mapped port:
iptables -A DOCKER \
    -d 172.17.0.2/32 ! -i docker0 -o docker0 \
    -p tcp --dport 80 -j ACCEPT
```

#### DOCKER-ISOLATION-STAGE-1 and STAGE-2

These chains prevent traffic from crossing between different Docker networks (e.g., between `docker0` and `br-abc123`). Each Docker network gets its own bridge, and Docker ensures they are isolated at L3:

```
DOCKER-ISOLATION-STAGE-1:
  -i docker0 ! -o docker0 → DOCKER-ISOLATION-STAGE-2
  RETURN

DOCKER-ISOLATION-STAGE-2:
  -o docker0 → DROP
  RETURN
```

### DOCKER-USER — Safe Customisation Point

`DOCKER-USER` is **the correct place to add your own rules** that interact with Docker traffic. Rules in `FORWARD` before the `DOCKER-USER` jump, or rules added directly to the `DOCKER` or `DOCKER-ISOLATION` chains, may be overwritten by Docker daemon restarts.

```bash
# Allow only specific source IPs to reach any mapped port
iptables -I DOCKER-USER -i eth0 \
    ! -s 203.0.113.0/24 \
    -j DROP

# Block a specific container from being reached externally
iptables -I DOCKER-USER \
    -d 172.17.0.5/32 \
    ! -i docker0 \
    -j DROP

# Rate-limit connections to Docker containers from outside
iptables -I DOCKER-USER -i eth0 -p tcp \
    -m hashlimit \
    --hashlimit-name docker_conn \
    --hashlimit-above 50/second \
    --hashlimit-burst 100 \
    --hashlimit-mode srcip \
    -j DROP

# ALWAYS return at end of DOCKER-USER so Docker's own rules still run
iptables -A DOCKER-USER -j RETURN
```

> [!important] Always end `DOCKER-USER` with `-j RETURN`. If packets are `DROP`ped or `ACCEPT`ed by a rule that falls through without `RETURN`, Docker's own `DOCKER` and `DOCKER-ISOLATION` chains are bypassed — potentially allowing inter-network traffic or blocking legitimate port mappings.

### Docker IPv6 and conntrack

Docker's IPv6 support is opt-in. When enabled, Docker adds equivalent `ip6tables` rules. Key settings in `/etc/docker/daemon.json`:

```json
{
    "ipv6": true,
    "fixed-cidr-v6": "fd00:dead:beef::/48",
    "ip6tables": true
}
```

```bash
# Docker adds to ip6tables similarly:
ip6tables -t nat -L DOCKER -n -v
ip6tables -L DOCKER-USER -n -v
```

### Podman and Rootless Containers

Podman (rootless mode) uses `nftables` rather than `iptables` and operates entirely within a **user network namespace** (via `slirp4netns` or `pasta`). Key differences:

- **No host iptables rules** are modified for rootless Podman containers.
- Rootless networking uses userspace NAT at the slirp4netns level — Netfilter on the host does not see container traffic.
- Rootful Podman mirrors Docker's iptables integration (uses the same `DOCKER`-style chain pattern, but named `PODMAN`).

```bash
# Inspect Podman's iptables chains (rootful only)
iptables -L PODMAN -n -v
iptables -t nat -L PODMAN -n -v
```

---

## GeoIP and Country-Based Filtering

### Overview

Country-based filtering uses **GeoIP databases** to map IP address ranges to countries, then loads those ranges into kernel data structures (ipset or nftables sets) for efficient matching. The kernel never makes DNS queries — it matches raw IP addresses from the pre-loaded table.

### Approach 1: ipset + iptables with MaxMind GeoLite2

```bash
# Install geoip tools
apt install geoip-bin ipset

# Or use the MaxMind mmdbinspect / geoipupdate workflow
apt install mmdb-bin

# 1. Download GeoLite2 Country database (requires free MaxMind account)
geoipupdate    # uses /etc/GeoIP.conf

# 2. Extract all CIDR ranges for a country (e.g., CN)
#    Using mmdbinspect + jq:
mmdbinspect -db /usr/share/GeoIP/GeoLite2-Country.mmdb \
    "1.0.0.0/8" 2>/dev/null | \
    jq -r '.[] | select(.Record.country.iso_code=="CN") | .Network' \
    > /tmp/cn_ranges.txt

# Or use the ipdeny.com aggregated zone files (simpler, less precise)
curl -o /tmp/cn.zone https://www.ipdeny.com/ipblocks/data/aggregated/cn-aggregated.zone

# 3. Load into ipset
ipset create GEOBLOCK_CN hash:net maxelem 65536
while read net; do
    ipset add GEOBLOCK_CN "$net" 2>/dev/null
done < /tmp/cn.zone

# 4. Block in iptables
iptables -I INPUT -m set --match-set GEOBLOCK_CN src -j DROP
iptables -I FORWARD -m set --match-set GEOBLOCK_CN src -j DROP

# 5. Save ipset for persistence
ipset save > /etc/ipset-geoblock.conf

# On boot (add to rc.local or a systemd unit):
ipset restore < /etc/ipset-geoblock.conf
```

### Approach 2: nftables Native Sets

```bash
# Generate nftables set format from zone file
echo "table inet geoblock {" > /etc/nftables-geoblock.conf
echo "    set CN_v4 {" >> /etc/nftables-geoblock.conf
echo "        type ipv4_addr" >> /etc/nftables-geoblock.conf
echo "        flags interval" >> /etc/nftables-geoblock.conf
echo "        elements = {" >> /etc/nftables-geoblock.conf
awk '{printf "            %s,\n", $1}' /tmp/cn.zone >> /etc/nftables-geoblock.conf
echo "        }" >> /etc/nftables-geoblock.conf
echo "    }" >> /etc/nftables-geoblock.conf
echo "}" >> /etc/nftables-geoblock.conf
```

```nftables
# /etc/nftables-geoblock.conf (generated above, then included)
table inet geoblock {
    set CN_v4 {
        type ipv4_addr
        flags interval
        elements = {
            1.0.0.0/8,
            1.24.0.0/13,
            # ... thousands of entries ...
        }
    }

    chain input {
        type filter hook input priority filter - 10;
        ip saddr @CN_v4 drop
    }
}
```

### Performance Considerations

- ipset `hash:net` and nftables `interval` sets both use **radix trees** internally — lookup is O(log n) in the worst case but very cache-friendly in practice.
- A full country block list (e.g., China: ~8,000 prefixes) has negligible per-packet overhead.
- Reload the database **weekly** — GeoIP allocations change frequently.
- For IPv6 country filtering, generate and load a separate IPv6 set. MaxMind GeoLite2 includes IPv6 data.

> [!warning] GeoIP accuracy is approximately **95–99%** at the country level. IP geolocation databases have known errors, especially for mobile carriers, VPNs, CDNs, and cloud providers with globally distributed IPs. Never rely on GeoIP as a sole security control.

---

## String and Payload Matching

### xt_string Match

The `xt_string` module scans packet payloads for a literal string or a regular expression. It operates on raw bytes starting from a configurable offset and is useful for blocking specific payloads, User-Agent strings, DNS names, or protocol signatures.

```bash
# Block HTTP requests containing a specific User-Agent
iptables -A FORWARD -p tcp --dport 80 \
    -m string --string "BadBot/1.0" --algo bm \
    -j DROP

# Block DNS queries for a specific domain (matches in UDP payload)
iptables -A INPUT -p udp --dport 53 \
    -m string --string "malware.example.com" --algo kmp \
    -j DROP

# Block connections containing "cmd.exe" (worm payload signature)
iptables -A FORWARD \
    -m string --string "cmd.exe" --algo bm --from 0 --to 2000 \
    -j DROP
```

#### xt_string Options

|Option|Description|
|---|---|
|`--string STRING`|Literal string to search for|
|`--hex-string HEXSTRING`|Hex-encoded binary string (e.g., `--hex-string "|
|`--algo {bm,kmp}`|Search algorithm: Boyer-Moore (`bm`) or Knuth-Morris-Pratt (`kmp`)|
|`--from OFFSET`|Start searching at this byte offset from the start of the L4 payload|
|`--to OFFSET`|Stop searching at this byte offset|
|`--icase`|Case-insensitive matching|

```nftables
# nftables: payload string matching (limited native support — use xt_string via nft_compat)
table inet dpi {
    chain forward {
        type filter hook forward priority filter;
        # Via xt_compat:
        # tcp dport 80 xt target "NFQUEUE" ...
        # (true DPI in nftables requires NFQUEUE + userspace)
    }
}
```

> [!warning] Performance String matching scans packet payloads byte-by-byte. On high-throughput links this adds significant CPU overhead, especially with long patterns or large `--to` offsets. Prefer narrow match criteria (specific port, protocol, connection state) to minimise the number of packets that reach the string match.

> [!warning] Encrypted traffic `xt_string` operates on unencrypted payload. It has no effect on TLS/HTTPS, QUIC, SSH, or any encrypted protocol. For encrypted traffic, use NFQUEUE with a userspace process that can perform TLS inspection (e.g., mitmproxy with CA certificate injection).

### u32 Match — Raw Packet Inspection

The `u32` module provides **arbitrary raw packet byte extraction and comparison**. It is extremely flexible but requires deep knowledge of packet structure. It is rarely needed since `xt_string`, conntrack, and protocol-specific matches cover most use cases.

```bash
# Match IPv4 packets with the "Don't Fragment" bit set
iptables -A INPUT \
    -m u32 --u32 "6 & 0x4000 = 0x4000" \
    -j LOG --log-prefix "DF_SET: "

# Match DNS queries (UDP/53, 3rd byte of DNS header = QR bit = 0 = query)
iptables -A INPUT -p udp --dport 53 \
    -m u32 --u32 "22 & 0x8000 = 0" \
    -j ACCEPT

# The u32 expression syntax:
# "OFFSET [& MASK] [>> SHIFT] OPERATOR VALUE [&& ...]"
# OFFSET: byte offset from the start of the IP header
# Values are always 32-bit (4-byte) aligned reads
```

The `u32` syntax is complex and error-prone. For new deployments, prefer nftables `payload` expressions which offer the same capability with clearer syntax:

```nftables
# nftables: match DF bit in IPv4 header (byte offset 6, bit 14)
@ih,48,1 1 drop   # raw payload: offset 48 bits, length 1 bit, value 1 → DF set
```

---

## WireGuard and Netfilter

### How WireGuard Appears to Netfilter

WireGuard is a modern VPN implemented as a kernel module (`wireguard.ko`). It presents as a **virtual network interface** (`wg0`, `wg1`, …). From Netfilter's perspective:

- **Outer UDP packets** (the encrypted WireGuard datagrams, default port 51820) pass through the standard IPv4/IPv6 hook chain like any UDP traffic.
- **Inner decrypted packets** appear on the WireGuard interface (`wg0`) as if they arrived on a regular NIC — they traverse the full `NF_INET_PRE_ROUTING` hook chain again on the `wg0` interface.

```
External UDP/51820 packet arrives on eth0
        │
        ▼
NF_INET_PRE_ROUTING (eth0)    ← firewall sees outer encrypted UDP
        │
        ▼
WireGuard kernel module decrypts
        │
        ▼
Decrypted inner packet injected on wg0
        │
        ▼
NF_INET_PRE_ROUTING (wg0)     ← firewall sees inner plaintext packet
        │
        ▼
NF_INET_FORWARD                ← normal routing/forwarding rules apply
```

### Typical WireGuard Firewall Rules

```bash
# 1. Allow incoming WireGuard UDP on the listening port
iptables -A INPUT -p udp --dport 51820 -j ACCEPT

# 2. Allow forwarding between WireGuard tunnel and LAN
iptables -A FORWARD -i wg0 -j ACCEPT
iptables -A FORWARD -o wg0 -j ACCEPT

# 3. NAT for WireGuard clients accessing the internet via the gateway
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
```

```nftables
table inet wireguard {
    chain input {
        type filter hook input priority filter;
        iif "lo"   accept
        ct state established,related accept

        # WireGuard handshake / data
        udp dport 51820 accept

        # Allow any traffic from the WireGuard tunnel itself
        iif "wg0" accept

        drop
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state established,related accept

        # Tunnel → internet
        iif "wg0" oif "eth0" accept

        # Internet → tunnel (ESTABLISHED already covered above)
    }
}

table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat;
        iif "wg0" oif "eth0" masquerade
    }
}
```

### Conntrack and WireGuard

WireGuard's outer UDP session is tracked as a `udp stream` conntrack entry. The inner packets are tracked independently. Because WireGuard initiates connections from both sides (handshake is symmetric), the first packet in each direction may appear as `NEW` to conntrack. Ensure your rules accept `NEW` on the WireGuard interface:

```bash
# Allow new connections from WireGuard clients
iptables -A FORWARD -i wg0 -m conntrack --ctstate NEW -j ACCEPT
```

> [!note] conntrack timeout WireGuard keeps-alive are sent every 25 seconds by default (`PersistentKeepalive = 25`). The `udp_timeout_stream` (default 180 s) is long enough for this. If you reduce `nf_conntrack_udp_timeout_stream` below 25 s, WireGuard sessions will be evicted from conntrack and the first data packet after eviction will require a new handshake.

---

## Fail2ban Integration

### How Fail2ban Uses Netfilter

Fail2ban is a **log-parsing intrusion prevention daemon**. It monitors log files (SSH auth logs, web server logs, etc.) for brute-force or abuse patterns, then dynamically inserts iptables or nftables rules to block offending source IPs.

```
Log file (e.g., /var/log/auth.log)
        │
        ▼ inotify watch
fail2ban daemon
        │  parses log lines against regex filters
        ├── pattern match: "Failed password for root from 1.2.3.4"
        │
        ▼
Insert block rule:
  iptables -I f2b-sshd 1 -s 1.2.3.4 -j REJECT
  (or nft add element ...)
        │
        ▼
After bantime expires:
  iptables -D f2b-sshd -s 1.2.3.4 -j REJECT
```

### Fail2ban iptables Chain Structure

For each jail (e.g., `sshd`), fail2ban creates:

```
INPUT chain
  └── -j f2b-sshd       ← fail2ban inserts this jump

f2b-sshd chain:
  -s 1.2.3.4 -j REJECT  ← dynamically inserted per banned IP
  -s 5.6.7.8 -j REJECT
  ...
  -j RETURN              ← fall through to normal rules
```

```bash
# View active fail2ban bans
fail2ban-client status sshd
# Banned IP list: 1.2.3.4, 5.6.7.8 ...

# View the iptables chain
iptables -L f2b-sshd -n -v

# Manually unban an IP
fail2ban-client set sshd unbanip 1.2.3.4
```

### Fail2ban with nftables

Since fail2ban ≥ 0.11, it supports nftables natively via the `nftables` action backend. Configuration in `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
banaction = nftables-multiport
banaction_allports = nftables-allports

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
findtime = 600
```

With the nftables backend, fail2ban uses a **named set** for banned IPs:

```nftables
# fail2ban creates and manages this automatically
table inet f2b-table {
    set f2b-set-sshd {
        type ipv4_addr
        flags timeout
    }
    chain f2b-chain {
        type filter hook input priority filter - 1;
        ip saddr @f2b-set-sshd reject
    }
}
```

```bash
# Manually inspect the nftables set
nft list set inet f2b-table f2b-set-sshd

# Manually add a ban (for testing)
nft add element inet f2b-table f2b-set-sshd { 1.2.3.4 timeout 1h }
```

> [!tip] Fail2ban vs kernel-native rate limiting For pure connection-rate limiting, prefer nftables dynamic sets (see [[#Dynamic Blocking with nftables Sets]]) — they react in **microseconds** at the packet level without any log parsing. Fail2ban is better suited for **application-layer** brute force detection where the abuse pattern is in log messages (wrong password, 404 errors, etc.) rather than connection rate.

---

## Port Knocking with the recent Module

### Concept

Port knocking is a technique where a host remains completely firewalled until it receives a **secret sequence of connection attempts** on specific ports. Only after the correct sequence is received is the protected service (typically SSH) temporarily opened for the source IP.

```
Client sends SYN to port 1234 → recorded
Client sends SYN to port 5678 → recorded
Client sends SYN to port 9012 → sequence complete → SSH port opened for client IP
```

### Three-Port Knock Example (iptables)

```bash
# Create named lists for each stage of the sequence
# Stage 1: hit port 1234
iptables -A INPUT -m recent --name KNOCK1 --remove -p tcp --dport 1234 -j DROP

# Stage 2: if you hit port 1234 first, hitting 5678 advances to stage 2
iptables -A INPUT -p tcp --dport 5678 \
    -m recent --name KNOCK1 --rcheck --seconds 5 \
    -m recent --name KNOCK2 --set \
    -j DROP

# Stage 3: if you completed stages 1+2, hitting 9012 advances to stage 3
iptables -A INPUT -p tcp --dport 9012 \
    -m recent --name KNOCK2 --rcheck --seconds 5 \
    -m recent --name KNOCK3 --set \
    -j DROP

# Open SSH for 30 seconds after completing the sequence
iptables -A INPUT -p tcp --dport 22 \
    -m recent --name KNOCK3 --rcheck --seconds 30 \
    -j ACCEPT

# Add this first so it's evaluated before the DROP rules:
iptables -I INPUT -p tcp --dport 1234 \
    -m recent --name KNOCK1 --set \
    -j DROP
```

```bash
# Knock sequence from client:
nmap -Pn --host-timeout 201ms --max-retries 0 -p 1234 TARGET
nmap -Pn --host-timeout 201ms --max-retries 0 -p 5678 TARGET
nmap -Pn --host-timeout 201ms --max-retries 0 -p 9012 TARGET
ssh TARGET
```

> [!warning] Port knocking limitations
> 
> - Provides **security through obscurity**, not cryptographic authentication.
> - Sequence can be sniffed from an already-compromised network.
> - `knockd` (a dedicated daemon) or a cryptographic variant (Single Packet Authorization — SPA) is more robust for production use.
> - Timing between knocks must be under `--seconds` threshold (default 5 s above).

### knockd Daemon (Alternative)

`knockd` listens on a raw socket and is more reliable than iptables-only port knocking:

```ini
# /etc/knockd.conf
[openSSH]
    sequence    = 7000,8000,9000
    seq_timeout = 5
    command     = /sbin/iptables -I INPUT -s %IP% -p tcp --dport 22 -j ACCEPT
    tcpflags    = syn

[closeSSH]
    sequence    = 9000,8000,7000
    seq_timeout = 5
    command     = /sbin/iptables -D INPUT -s %IP% -p tcp --dport 22 -j ACCEPT
    tcpflags    = syn
```

---

## OSF — Passive OS Fingerprinting

### What OSF Does

The `osf` (OS Fingerprinting) module identifies the **operating system** of a remote host by analysing the TCP SYN packet's header fields (Window size, TTL, MSS, window scaling, SACK, timestamp options). This is passive — no probes are sent.

```bash
# Load the module and fingerprint database
modprobe nf_osf

# Install fingerprint database
# The nmap project's nmap-os-db is commonly used; convert it for OSF:
# (Tool: p0f or xtables-addons provides /usr/share/xtables-addons/pf.os)

# Log the OS guess for all incoming TCP SYN packets
iptables -A INPUT -p tcp --syn \
    -m osf --genre Linux --ttl 0 \
    -j LOG --log-prefix "OS_LINUX: "

# Drop Windows hosts on a Linux-only API port
iptables -A INPUT -p tcp --dport 8443 \
    -m osf --genre "Windows" \
    -j DROP
```

#### OSF Match Options

|Option|Description|
|---|---|
|`--genre GENRE`|OS genre string (e.g., `Linux`, `Windows`, `FreeBSD`, `Cisco`)|
|`--ttl MODE`|TTL check: `0` = skip, `1` = check ±5, `2` = check exactly|
|`--log LEVEL`|Log level for OS detections (0–3)|

> [!note] OSF accuracy is approximately 70–85% in real-world conditions. TTL is often modified by intermediate hops (NAT, proxies), and many OS fingerprints have evolved since fingerprint databases were last updated. Use for logging and analytics rather than hard security decisions.

---

## VLANs, Tunnels, and Encapsulation

### VLAN (802.1Q) and Netfilter

When a Linux host has VLAN sub-interfaces (e.g., `eth0.100`), Netfilter hooks see the **decapsulated** IP packet on the sub-interface. The 802.1Q VLAN tag has already been stripped by the kernel's VLAN layer before Netfilter sees the packet.

```bash
# Rules on VLAN sub-interfaces work by matching the interface name
iptables -A FORWARD -i eth0.100 -o eth0.200 -j ACCEPT

# Or match the VLAN interface prefix with nftables wildcard
nftables: iifname "eth0.*" accept

# If you need to match the VLAN ID itself (before tag stripping), use ebtables:
ebtables -A FORWARD -p 802_1Q --vlan-id 100 -j ACCEPT
```

```
802.1Q tagged frame → [kernel VLAN layer strips tag] → plain Ethernet frame
                                                            │
                                                            ▼ appears on eth0.100
                                                        NF_INET_PRE_ROUTING
                                                        iif = "eth0.100"
```

### VXLAN and Overlay Networks

VXLAN (UDP port 4789) and Geneve (UDP port 6081) encapsulate Ethernet frames inside UDP for overlay networking (Kubernetes, OpenStack, Open vSwitch).

```
Inner packet (VM/container traffic)
Encapsulated → outer UDP/4789 packet on eth0

Netfilter on eth0 sees:
  - outer IPv4 header + UDP port 4789
  - inner Ethernet frame as opaque payload

Netfilter on the VXLAN interface (vxlan0) sees:
  - inner IP packet (after decapsulation)
```

Key implication: **rules on `eth0` cannot match inner packet fields** (inner IP src/dst, inner TCP ports). Rules on `vxlan0` can.

```bash
# Allow VXLAN encapsulation traffic (outer)
iptables -A INPUT -p udp --dport 4789 -j ACCEPT
iptables -A INPUT -p udp --dport 6081 -j ACCEPT   # Geneve

# Filter inner traffic on the VXLAN interface
iptables -A FORWARD -i vxlan0 -p tcp --dport 22 -j ACCEPT
iptables -A FORWARD -i vxlan0 -j DROP
```

### GRE and IPIP Tunnels

GRE (protocol 47) and IPIP (protocol 4) encapsulate IP-in-IP. Rules on the physical interface match the outer header; rules on the tunnel interface (`gre0`, `tun0`, `ipip0`) match the inner packet.

```bash
# Allow GRE protocol on the external interface
iptables -A INPUT -p 47 -j ACCEPT     # GRE
iptables -A INPUT -p 4  -j ACCEPT     # IPIP

# Filter traffic on the GRE tunnel interface
iptables -A FORWARD -i gre0 -s 10.0.0.0/8 -j ACCEPT
iptables -A FORWARD -i gre0 -j DROP

# Conntrack for GRE (required for stateful rules on gre0)
modprobe nf_conntrack_proto_gre
```

### Bonding and Teams

Bonding (`bond0`) and teaming (`team0`) present as **single logical interfaces** to Netfilter. Rules match the bond interface name, not the underlying physical members:

```bash
# Rules on the bond interface apply to all member traffic
iptables -A INPUT -i bond0 -p tcp --dport 443 -j ACCEPT

# You cannot match individual bond members (eth0, eth1) independently
# from the bonding driver — all traffic appears on bond0
```

> [!note] `PREROUTING` hook for bonded traffic fires on `bond0`, not on `eth0` or `eth1`. If you need to filter by physical interface, consider using `tc` on the physical interfaces before bonding aggregation, or use the `physdev` match module (only meaningful for bridged interfaces, not bonds).

### MTU and Fragmentation Across Tunnels

All encapsulation protocols reduce the effective MTU for inner packets:

|Encapsulation|Overhead|Inner MTU (from 1500 byte outer)|
|---|---|---|
|VXLAN (IPv4)|50 bytes|1450|
|GRE (no checksum)|24 bytes|1476|
|GRE (with checksum)|28 bytes|1472|
|IPIP|20 bytes|1480|
|WireGuard|60 bytes|1440|
|IPsec (ESP, transport)|~50–73 bytes|~1427–1450|

Always set the inner interface MTU or use PMTUD clamping:

```bash
# Clamp TCP MSS to avoid fragmentation through a VXLAN tunnel
iptables -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
    -j TCPMSS --clamp-mss-to-pmtu

# Or set a fixed MSS
iptables -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
    -j TCPMSS --set-mss 1400

# nftables
table inet mtu {
    chain forward {
        type filter hook forward priority mangle;
        tcp flags syn / syn,rst tcp option maxseg size set rt mtu
    }
}
```

---

## Testing and Validating Firewall Rules

### hping3 — Crafted Packet Testing

`hping3` sends custom TCP/UDP/ICMP packets and reports on responses. It is the standard tool for verifying that firewall rules have the expected effect.

```bash
# Test if TCP port 22 accepts a SYN (expects SYN+ACK back)
hping3 -S -p 22 -c 3 TARGET

# Test if port 23 is correctly dropped (expects no response / timeout)
hping3 -S -p 23 -c 3 TARGET

# Test UDP port
hping3 -2 -p 53 -c 3 TARGET

# Send fragmented packet (test fragment handling)
hping3 -S -p 80 --mtu 64 TARGET

# Test ICMP
hping3 --icmp TARGET

# SYN flood simulation (test rate limiting rules)
hping3 -S -p 80 --flood TARGET

# Spoof source IP (test anti-spoofing rules; requires root)
hping3 -S -p 80 --spoof 192.0.2.1 TARGET
```

### nmap — Port and State Scanning

`nmap` provides a high-level view of what the firewall exposes:

```bash
# TCP connect scan (most reliable; uses full 3-way handshake)
nmap -sT -p 1-65535 TARGET

# SYN scan (half-open; faster; requires root)
nmap -sS -p 22,80,443 TARGET

# UDP scan (slow; requires root)
nmap -sU -p 53,123,161 TARGET

# Firewall evasion: test fragmented packets
nmap -sS -f TARGET

# Test with decoy IPs (check if anti-spoofing is consistent)
nmap -D 10.0.0.1,10.0.0.2 TARGET

# OS detection
nmap -O TARGET

# Full audit: all ports, version detection, OS
nmap -sS -sV -O -p- TARGET

# From inside the firewall (verify OUTPUT rules)
nmap -sT scanme.nmap.org
```

### Scapy — Scriptable Packet Crafting

Scapy is a Python library for constructing and sending arbitrary packets. It is ideal for testing specific edge cases in firewall rules:

```python
from scapy.all import *

# Test a specific TCP flag combination (URG+FIN — often used in scans)
pkt = IP(dst="TARGET") / TCP(dport=22, flags="UF")
ans = sr1(pkt, timeout=2)
print(ans.summary() if ans else "No response (DROP)")

# Test a Christmas tree packet (FIN+PSH+URG — should be INVALID in conntrack)
pkt = IP(dst="TARGET") / TCP(dport=22, flags="FPU")
ans = sr1(pkt, timeout=2)

# Test ICMP type not in allowlist
pkt = IP(dst="TARGET") / ICMP(type=15)  # type 15 = Information Request (obsolete)
ans = sr1(pkt, timeout=2)

# Send fragmented packet
send(fragment(IP(dst="TARGET")/TCP(dport=80)/("X"*1000)))

# Test conntrack INVALID: send ACK with no prior connection
pkt = IP(dst="TARGET") / TCP(dport=22, flags="A", seq=12345, ack=67890)
ans = sr1(pkt, timeout=2)
```

### Validating nftables Configuration Files

```bash
# Dry-run: validate syntax without applying
nft --check --file /etc/nftables.conf

# Atomic replace: apply entire new ruleset or roll back on error
nft --file /etc/nftables.conf

# Show what would change (compare current vs new)
nft list ruleset > /tmp/current.nft
nft --check --file /etc/nftables.new && echo "Syntax OK"

# Preview with diff
diff /tmp/current.nft /etc/nftables.new
```

#### Testing Rule Changes Safely (Auto-Rollback)

```bash
# Apply new rules; automatically revert after 60 seconds if not confirmed
#
# In terminal 1 (on the server):
nft --file /etc/nftables.new

# Start a countdown: if you don't cancel it, rules revert
sleep 60 && nft --file /etc/nftables.conf &
ROLLBACK_PID=$!

# In terminal 2 (from your workstation — verify access still works):
ssh user@server "echo still connected"

# If everything works, cancel the rollback:
kill $ROLLBACK_PID
echo "Rules confirmed — rollback cancelled"
```

### Capturing Netfilter-Dropped Packets

Dropped packets leave no trace by default. Use these techniques to capture them:

```bash
# 1. LOG target: adds a line to dmesg/syslog for each dropped packet
iptables -I INPUT -j LOG --log-prefix "PRECHECK: " --log-level 6
iptables -A INPUT -j DROP
# Then:
dmesg | grep PRECHECK

# 2. NFLOG: capture dropped packets to a pcap file via ulogd2

# 3. nftables log + tcpdump on a mirror:
# In nftables: log prefix "DROP: " level debug
# Then:
journalctl -k -f | grep "DROP:"

# 4. Use tc mirror to capture traffic before it hits Netfilter
tc qdisc add dev eth0 ingress
tc filter add dev eth0 ingress \
    protocol all u32 match u32 0 0 \
    action mirred egress mirror dev lo

# Capture on the mirror interface
tcpdump -i lo -w /tmp/mirrored.pcap

# 5. XDP-based capture (zero-overhead; captures before Netfilter)
# Use xdpdump from iproute2:
xdpdump -i eth0 --rx-capture entry -w /tmp/xdp.pcap
```

---

## Related Notes

---

_Sources: Linux kernel source (`net/netfilter/`, `include/linux/netfilter.h`), `man 8 iptables`, `man 8 nft`, `man 8 ipset`, nftables wiki, kernel documentation (`Documentation/networking/netfilter.rst`), netfilter.org._