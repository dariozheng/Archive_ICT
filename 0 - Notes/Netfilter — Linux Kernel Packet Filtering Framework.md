---
categories:
  - "[[Linux]]"
topic@linux:
tags:
icon: SiLinux
iconColor: "#000000"
---
**Netfilter** is the packet filtering and manipulation framework built into the Linux kernel. It defines a series of **hooks** at strategic points in the network stack where modules can register callbacks to inspect, modify, or drop packets. Every stateful firewall, NAT engine, connection tracker, and packet logger in Linux is built as a Netfilter subsystem. Userspace tools — `iptables`, `nftables`, `ipset`, `conntrack` — interact with these subsystems through well-defined kernel interfaces.

---

## Table of Contents

**Framework Architecture**

- [[#Architecture Overview]]
- [[#Protocol Families and Hook Namespaces]]
- [[#Subsystems Built on Netfilter]]
- [[#Key Kernel Modules]]

**Hook System**

- [[#Hook Points]]
    - [[#IPv4 and IPv6 Hook Points]]
    - [[#ARP Hook Points]]
    - [[#Bridge Hook Points]]
    - [[#netdev Ingress and Egress Hooks]]
- [[#Hook Priorities]]
- [[#Hook Registration (Kernel API)]]
- [[#Netfilter Verdicts]]

**Packet Processing Paths**

- [[#Forwarded Packet Path]]
- [[#Locally Generated Packet Path]]
- [[#Incoming-to-Local Packet Path]]
- [[#Bridge Packet Traversal]]

**Userspace Interfaces**

- [[#Netlink and nfnetlink]]
- [[#NFQUEUE — Userspace Packet Processing]]
- [[#NFLOG — Packet Logging to Userspace]]
- [[#libnetfilter Libraries]]

**Core Subsystems**

- [[#iptables]]
    - [[#iptables Tables and Chains]]
    - [[#iptables Rule Structure]]
    - [[#iptables Built-in Targets]]
    - [[#iptables Match Extensions]]
    - [[#ip6tables and arptables]]
- [[#nftables]]
    - [[#nftables Data Model]]
    - [[#nftables Expressions and Statements]]
    - [[#nftables Sets and Maps]]
    - [[#nftables Flowtables]]
    - [[#Migrating from iptables to nftables]]
- [[#ipset]]
- [[#Connection Tracking]]
- [[#NAT]]
    - [[#SNAT and Masquerade]]
    - [[#DNAT and Port Forwarding]]
    - [[#NAT Hairpinning]]

**Topology and Protocol Scenarios**

- [[#Network Namespaces]]
- [[#IPv6-Specific Considerations]]
    - [[#ICMPv6 Requirements]]
    - [[#IPv6 Extension Header Matching]]
    - [[#IPv6 Address Types and Bogon Rules]]
- [[#ebtables — Layer 2 Filtering]]
    - [[#ebtables Tables and Chains]]
    - [[#ebtables Match Extensions and Targets]]
    - [[#br_netfilter Integration]]
- [[#VLANs, Tunnels, and Encapsulation]]
    - [[#VLAN (802.1Q) and Netfilter]]
    - [[#VXLAN and Overlay Networks]]
    - [[#GRE and IPIP Tunnels]]
    - [[#MTU, Fragmentation, and MSS Clamping]]
- [[#WireGuard and Netfilter]]
- [[#IPsec and xfrm Integration]]
    - [[#xfrm Hooks in the Packet Path]]
    - [[#Matching IPsec Policy in Firewall Rules]]

**Container Networking**

- [[#Docker Networking Chains]]
    - [[#Docker Chain Architecture]]
    - [[#DOCKER-USER — Safe Customisation Point]]
    - [[#Docker IPv6 and conntrack]]
- [[#Podman and Rootless Containers]]

**Advanced Targets**

- [[#SYNPROXY — SYN Flood Protection]]
- [[#TPROXY — Transparent Proxying]]
- [[#REJECT — Generating Error Responses]]

**Marks and Policy Routing**

- [[#Packet Mark vs Conntrack Mark]]
- [[#Policy Routing with the RPDB]]
- [[#CONNMARK and Multi-ISP Routing]]

**Security and Rate Limiting**

- [[#Connection Limiting (connlimit)]]
- [[#Per-Source Rate Limiting (hashlimit)]]
- [[#Dynamic Blocking with nftables Sets]]
- [[#The recent Module]]
- [[#Port Knocking]]
- [[#GeoIP and Country-Based Filtering]]
- [[#String and Payload Matching]]
- [[#OSF — Passive OS Fingerprinting]]
- [[#The security Table — SELinux and AppArmor]]

**Logging and Accounting**

- [[#nfacct — Kernel Accounting Objects]]
- [[#Fail2ban Integration]]

**Traffic Shaping and QoS**

- [[#DSCP Marking]]
- [[#Integration with tc (Traffic Control)]]

**Performance and Optimization**

- [[#Hook Overhead and Optimization]]
- [[#eBPF and XDP Integration]]

**Kernel Internals**

- [[#nf_tables Bytecode Virtual Machine]]
- [[#x_tables Infrastructure (Legacy)]]

**Module Reference**

- [[#Netfilter Module Reference]]

**Debugging and Testing**

- [[#Debugging Netfilter]]
    - [[#TRACE Target (iptables)]]
    - [[#nftables Tracing]]
    - [[#Counting Drops by Chain]]
    - [[#Checking What Rules Are Active]]
- [[#Testing and Validating Firewall Rules]]
- [[#Common Issues]]

**Firewall Baselines**

- [[#Comprehensive nftables Firewall Baseline]]
- [[#Comprehensive iptables Firewall Baseline]]

---

## Architecture Overview

Netfilter is not a monolithic firewall — it is a **hook framework** embedded in the kernel's network processing path. Higher-level features (stateful firewalling, NAT, packet queuing) are layered on top as loadable kernel modules.

```
User Space
  ├── iptables(8) / ip6tables(8)   → setsockopt() (legacy) or Netlink (iptables-nft)
  ├── nft(8)                        → Netlink (NFNL_SUBSYS_NFTABLES)
  ├── ipset(8)                      → Netlink (NFNL_SUBSYS_IPSET)
  ├── conntrack(8)                  → Netlink (NFNL_SUBSYS_CTNETLINK)
  └── libnetfilter_queue/log        → Netlink (NFNL_SUBSYS_QUEUE / ULOG)

Kernel Space
  └── Netfilter Core (net/netfilter/)
        ├── Hook dispatcher
        │     ├── NFPROTO_IPV4   hooks
        │     ├── NFPROTO_IPV6   hooks
        │     ├── NFPROTO_ARP    hooks
        │     ├── NFPROTO_BRIDGE hooks
        │     └── NFPROTO_NETDEV hooks (per-device ingress/egress)
        ├── iptables subsystem (raw · mangle · nat · filter · security)
        ├── nftables subsystem (tables · chains · rules · sets · flowtables)
        ├── Conntrack  → [[Netfilter Conntrack — Connection Tracking]]
        ├── NAT (depends on conntrack)
        ├── NFQUEUE
        ├── NFLOG
        └── ipset
```

Netfilter was introduced in Linux **2.4** (2000), replacing `ipchains` (2.2) and `ipfwadm` (2.0). The hook-plus-module design has remained stable; the userspace interface evolved from `iptables` to `nftables`.

---

## Protocol Families and Hook Namespaces

Each hook is registered for a specific **protocol family**. A hook registered for `NFPROTO_IPV4` only fires on IPv4 packets.

|Constant|Value|Scope|
|---|---|---|
|`NFPROTO_UNSPEC`|0|Global / unspecified|
|`NFPROTO_INET`|1|IPv4 + IPv6 (nftables `inet` family only — not a real kernel hook family)|
|`NFPROTO_IPV4`|2|IPv4|
|`NFPROTO_ARP`|3|ARP|
|`NFPROTO_NETDEV`|5|Per network device (ingress / egress)|
|`NFPROTO_BRIDGE`|7|Ethernet bridge (Layer 2 frames)|
|`NFPROTO_IPV6`|10|IPv6|

> [!note] NFPROTO_INET The `inet` family is a **nftables-only abstraction**: the kernel creates two independent hooks (one IPv4, one IPv6) for each `inet` base chain. It does not exist in the kernel C hook API.

---

## Subsystems Built on Netfilter

|Subsystem|Module|Depends on|Purpose|
|---|---|---|---|
|Conntrack|`nf_conntrack`|Netfilter core|Stateful connection tracking|
|NAT|`nf_nat`|`nf_conntrack`|Address / port translation|
|iptables filter|`ip_tables`|Netfilter core|IPv4 packet filtering|
|iptables NAT|`iptable_nat`|`nf_nat`, `ip_tables`|IPv4 NAT rules|
|iptables mangle|`iptable_mangle`|`ip_tables`|Packet modification|
|nftables|`nf_tables`|Netfilter core|Next-generation rule framework|
|NFQUEUE|`nfnetlink_queue`|`nfnetlink`|Userspace packet processing|
|NFLOG|`nfnetlink_log`|`nfnetlink`|Userspace packet logging|
|ipset|`ip_set`|Netfilter core|Hash / bitmap set matching|
|Flowtable|`nf_flow_table`|`nf_conntrack`|Fast-path bypass for ESTABLISHED flows|

---

## Key Kernel Modules

|Module|Purpose|
|---|---|
|`x_tables`|Shared infrastructure for iptables / ip6tables / arptables / ebtables|
|`ip_tables`|iptables core (IPv4)|
|`ip6_tables`|ip6tables core (IPv6)|
|`iptable_filter`|`filter` table|
|`iptable_nat`|`nat` table|
|`iptable_mangle`|`mangle` table|
|`iptable_raw`|`raw` table|
|`nf_tables`|nftables core|
|`nft_compat`|Use iptables match/target extensions from nftables|
|`nf_conntrack`|Connection tracking core → [[Netfilter Conntrack — Connection Tracking]]|
|`nf_nat`|NAT core (IPv4 + IPv6 since kernel 5.1)|
|`nfnetlink`|Netlink transport for all Netfilter subsystems|
|`nfnetlink_queue`|NFQUEUE|
|`nfnetlink_log`|NFLOG|
|`ip_set`|ipset core|
|`br_netfilter`|Make bridged IPv4/IPv6 traffic traverse Netfilter IP hooks|
|`nf_flow_table`|Software flowtable fast path|
|`nf_flow_table_hw`|Hardware offload extension for flowtables|
|`xt_osf`|Passive OS fingerprinting match|
|`nf_conntrack_ftp`|FTP ALG helper|
|`nf_conntrack_sip`|SIP/VoIP ALG helper|
|`nf_conntrack_proto_gre`|GRE conntrack support|

---

## Hook Points

### IPv4 and IPv6 Hook Points

Both IPv4 (`NFPROTO_IPV4`) and IPv6 (`NFPROTO_IPV6`) share five hook constants:

|Hook|Value|Position in the network stack|
|---|---|---|
|`NF_INET_PRE_ROUTING`|0|After NIC reception, before routing decision|
|`NF_INET_LOCAL_IN`|1|After routing: packet destined for a local socket|
|`NF_INET_FORWARD`|2|After routing: packet to be forwarded|
|`NF_INET_LOCAL_OUT`|3|Packet generated by a local socket, before routing|
|`NF_INET_POST_ROUTING`|4|After routing decision, before NIC transmission|

```
Incoming packet
        │
        ▼
[NF_INET_PRE_ROUTING]    ← raw · conntrack · DNAT
        │
   Routing decision
        │
        ├─── local? ──────────────────────────────┐
        │                                          │
        ▼ (forward)                                ▼ (deliver locally)
[NF_INET_FORWARD]                         [NF_INET_LOCAL_IN]
        │                                          │
        ▼                                          ▼
[NF_INET_POST_ROUTING]                     Local socket
  ← SNAT · conntrack confirm
        │
        ▼
    NIC transmit

Locally generated packet
        │
        ▼
[NF_INET_LOCAL_OUT]      ← raw · conntrack · DNAT for local
        │
   Routing decision
        │
        ▼
[NF_INET_POST_ROUTING]   ← SNAT · conntrack confirm
        │
        ▼
    NIC transmit
```

### ARP Hook Points

|Hook|Constant|Description|
|---|---|---|
|`NF_ARP_IN`|0|Incoming ARP packet|
|`NF_ARP_OUT`|1|Outgoing ARP packet|
|`NF_ARP_FORWARD`|2|ARP forwarded by a bridge proxy|

`arptables` registers at these hook points under `NFPROTO_ARP`.

### Bridge Hook Points

Bridge hooks fire on Ethernet frames traversing a Linux bridge (`NFPROTO_BRIDGE`). `ebtables` and the nftables `bridge` family operate here.

|Hook|Constant|Description|
|---|---|---|
|`NF_BR_PRE_ROUTING`|0|Frame received on bridge port, before forwarding decision|
|`NF_BR_LOCAL_IN`|1|Frame destined for the bridge device itself|
|`NF_BR_FORWARD`|2|Frame being forwarded through the bridge|
|`NF_BR_LOCAL_OUT`|3|Frame generated by the bridge (STP, etc.)|
|`NF_BR_POST_ROUTING`|4|Frame leaving a bridge port|
|`NF_BR_BROUTING`|5|Decision: bridge this frame or route it to the IP stack?|

> [!note] With `br_netfilter` loaded, bridged IP traffic additionally traverses the standard `NFPROTO_IPV4/IPV6` hooks — see [[#br_netfilter Integration]].

### netdev Ingress and Egress Hooks

The `NFPROTO_NETDEV` family binds chains to a specific interface. The ingress hook (since Linux 4.2) fires **before** `NF_INET_PRE_ROUTING`; the egress hook (since Linux 5.16) fires **after** `NF_INET_POST_ROUTING`.

```nftables
table netdev filter {
    chain ingress {
        type filter hook ingress device eth0 priority -500;
        # Before conntrack, before routing — ideal for DDoS drops
        ip saddr @blocklist drop
    }
    chain egress {
        type filter hook egress device eth0 priority 0;
        # After POST_ROUTING, before driver transmission
    }
}
```

Use cases: line-rate DDoS drops without conntrack overhead; per-interface early filtering.

---

## Hook Priorities

Each callback is registered with a signed **priority** integer. Lower numbers run **first**. Multiple callbacks at the same hook point fire in ascending priority order.

### Standard Priority Constants

|Constant|Value|Used by|
|---|---|---|
|`NF_IP_PRI_RAW_BEFORE_DEFRAG`|`-450`|nftables raw (before fragment reassembly)|
|`NF_IP_PRI_CONNTRACK_DEFRAG`|`-400`|`nf_defrag_ipv4` / `nf_defrag_ipv6`|
|`NF_IP_PRI_RAW`|`-300`|iptables `raw` table; nftables `raw` priority|
|`NF_IP_PRI_SELINUX_FIRST`|`-225`|SELinux early|
|`NF_IP_PRI_CONNTRACK`|`-200`|Conntrack lookup and new-entry creation|
|`NF_IP_PRI_MANGLE`|`-150`|iptables `mangle` table|
|`NF_IP_PRI_NAT_DST`|`-100`|DNAT|
|`NF_IP_PRI_FILTER`|`0`|iptables `filter` table; nftables `filter` default|
|`NF_IP_PRI_SECURITY`|`50`|AppArmor / SELinux late|
|`NF_IP_PRI_NAT_SRC`|`100`|SNAT / Masquerade|
|`NF_IP_PRI_CONNTRACK_CONFIRM`|`INT_MAX`|Conntrack confirmation (insert into hash table)|

### Effective Firing Order at PRE_ROUTING

```
NF_INET_PRE_ROUTING
  ├── −450   nftables raw (before defrag)
  ├── −400   nf_defrag_ipv4 — fragment reassembly
  ├── −300   iptables raw table  /  nftables priority raw
  ├── −200   nf_conntrack — lookup or create entry
  ├── −150   iptables mangle table
  ├── −100   iptables nat::PREROUTING (DNAT rules)
  └──    0   iptables filter table
```

### nftables Named Priorities

|Name|Integer|Equivalent iptables table|
|---|---|---|
|`raw`|`-300`|`raw`|
|`mangle`|`-150`|`mangle`|
|`dstnat`|`-100`|`nat` PREROUTING|
|`filter`|`0`|`filter`|
|`security`|`50`|—|
|`srcnat`|`100`|`nat` POSTROUTING|

> [!warning] Priority conflicts Multiple callbacks at the same priority have **undefined relative ordering** (depends on registration order). Use distinct values when execution order between two hooks matters.

---

## Hook Registration (Kernel API)

This section is for kernel module developers; administrators use iptables/nftables instead.

### Registering a Hook

```c
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>

static unsigned int my_hook_fn(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state)
{
    /* inspect or modify skb */
    return NF_ACCEPT;
}

static struct nf_hook_ops my_ops = {
    .hook     = my_hook_fn,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FILTER,
};

/* module_init */  nf_register_net_hook(net, &my_ops);
/* module_exit */  nf_unregister_net_hook(net, &my_ops);
```

### The sk_buff (Socket Buffer)

Every packet traversing Netfilter is a `struct sk_buff` (skb):

|Field|Type|Description|
|---|---|---|
|`data`|`unsigned char *`|Current packet data start|
|`head` / `end`|`unsigned char *`|Buffer boundaries|
|`len`|`unsigned int`|Total packet length|
|`protocol`|`__be16`|L3 protocol (`ETH_P_IP`, `ETH_P_IPV6`, …)|
|`dev`|`struct net_device *`|Incoming or outgoing device|
|`sk`|`struct sock *`|Associated socket (may be NULL)|
|`_nfct`|`unsigned long`|Packed conntrack entry pointer + ctinfo|
|`mark`|`__u32`|Packet mark, read by `ip rule fwmark` and `tc fw`|

### The nf_hook_state

```c
struct nf_hook_state {
    unsigned int       hook;  /* which hook point */
    u8                 pf;    /* protocol family  */
    struct net_device *in;    /* incoming device  */
    struct net_device *out;   /* outgoing device  */
    struct sock       *sk;
    struct net        *net;   /* network namespace */
};
```

---

## Netfilter Verdicts

Every hook callback returns a **verdict**:

|Verdict|Value|Meaning|
|---|---|---|
|`NF_ACCEPT`|0|Packet continues through the stack|
|`NF_DROP`|1|Packet silently discarded; skb freed immediately|
|`NF_STOLEN`|2|Hook takes ownership of the skb; kernel does nothing further|
|`NF_QUEUE`|3|Deliver packet to userspace via NFQUEUE|
|`NF_REPEAT`|4|Re-invoke this hook on the same packet|
|`NF_STOP`|5|**Deprecated** — treated as `NF_ACCEPT` in modern kernels|

**Key semantics:**

- `NF_DROP` does not generate an ICMP error. Use `REJECT` or nftables `reject` for that.
- `NF_STOLEN` is used by implementations that re-inject the skb later via `nf_reinject()`.
- `NF_QUEUE` drops the packet if no process is listening on that queue number.

### iptables Targets → Netfilter Verdicts

|iptables target|Verdict|Notes|
|---|---|---|
|`ACCEPT`|`NF_ACCEPT`|Terminates rule evaluation in the current chain|
|`DROP`|`NF_DROP`|Silent discard|
|`REJECT`|`NF_DROP` + ICMP/RST|Sends an error response before dropping|
|`NFQUEUE --queue-num N`|`NF_QUEUE`|Delivers to specific queue number|
|`RETURN`|internal|Returns from user chain to calling chain|
|`GOTO chain`|internal|Jumps to chain without returning|
|`LOG`|`NF_ACCEPT` (continues)|Non-terminating — logs then falls through|

---

## Forwarded Packet Path

Complete traversal of an **incoming forwarded IPv4 packet** through all tables and subsystems:

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

---

## Locally Generated Packet Path

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

---

## Incoming-to-Local Packet Path

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

---

## Bridge Packet Traversal

Without `br_netfilter`, bridged frames stay entirely within ebtables hooks and never reach iptables or conntrack. With `br_netfilter` loaded, bridged IP frames additionally traverse the INET hooks:

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

> [!warning] Double-processing With `br_netfilter`, the same IP packet passes through both `ebtables` (L2) and `iptables`/`nftables` (L3) hooks. Traffic that crosses a bridge and is then routed (common on Docker hosts) can trigger conntrack twice, causing INVALID states or double-NAT. Use conntrack zones to isolate bridge and routing domains. See [[Netfilter Conntrack — Connection Tracking#Bridge Networking and nf_conntrack_bridge]].

---

## Netlink and nfnetlink

Netlink is the **socket-based IPC mechanism** for kernel↔userspace communication. Netfilter uses its own Netlink family: **nfnetlink** (`NETLINK_NETFILTER`, protocol 12).

|Subsystem constant|Value|Used by|
|---|---|---|
|`NFNL_SUBSYS_CTNETLINK`|1|`conntrack` tool — read/write conntrack table|
|`NFNL_SUBSYS_CTNETLINK_EXP`|2|Conntrack expectations|
|`NFNL_SUBSYS_QUEUE`|3|NFQUEUE packet deliver / verdict|
|`NFNL_SUBSYS_ULOG`|4|NFLOG packet logging|
|`NFNL_SUBSYS_IPSET`|6|`ipset` management|
|`NFNL_SUBSYS_ACCT`|7|Netfilter accounting objects|
|`NFNL_SUBSYS_CTNETLINK_TIMEOUT`|8|Per-flow CT timeout policies|
|`NFNL_SUBSYS_CTHELPER`|9|Userspace CT helper protocol|
|`NFNL_SUBSYS_NFTABLES`|12|`nft` — nftables rule management|
|`NFNL_SUBSYS_NFT_COMPAT`|13|iptables compatibility via nftables|

> [!note] Legacy iptables uses setsockopt, not Netlink **Legacy** `iptables` communicates via `setsockopt`/`getsockopt` on a raw socket. The modern `iptables-nft` wrapper (the default on most distributions since ~2019) translates iptables commands into nftables Netlink messages. This is why `nft list ruleset` shows rules added by `iptables-nft`, but rules added by `iptables-legacy` remain invisible to `nft`.

---

## NFQUEUE — Userspace Packet Processing

NFQUEUE allows a **userspace process** to receive packets, inspect or modify them, and issue a verdict. Use cases: IDS/IPS (Suricata, Snort), deep protocol inspection, custom packet transformation.

```
Kernel                           Userspace
  │                                  │
  │  rule: -j NFQUEUE --queue-num 0  │
  ├─── NF_QUEUE verdict ────────────►│  libnetfilter_queue
  │                                  │  inspects / optionally modifies
  │◄── verdict (ACCEPT or DROP) ─────│
  └─ packet continues or is freed
```

### NFQUEUE Setup

```bash
# iptables
iptables -A INPUT -p tcp --dport 80 -j NFQUEUE --queue-num 0
iptables -A INPUT -p tcp --dport 80 -j NFQUEUE --queue-num 0 --queue-bypass  # ACCEPT if no listener
iptables -A INPUT -p tcp --dport 80 -j NFQUEUE --queue-balance 0:3            # fan-out 0–3
```

```nftables
# nftables
table inet filter {
    chain input {
        type filter hook input priority filter;
        tcp dport 80 queue num 0
        tcp dport 80 queue num 0-3 bypass
    }
}
```

### NFQUEUE Copy Modes

|Mode|API constant|What is delivered|
|---|---|---|
|None|`NFQNL_COPY_NONE`|Metadata only|
|Meta|`NFQNL_COPY_META`|Metadata + zero payload bytes|
|Packet|`NFQNL_COPY_PACKET`|Full packet up to `copy_range` bytes|

```c
nfq_set_mode(qh, NFQNL_COPY_PACKET, 0xffff);  /* copy up to 65535 bytes */
```

### Verdict with Packet Modification

```c
nfq_set_verdict2(qh, id, NF_ACCEPT, mark, data_len, modified_data);
```

> [!note] Limitations NFQUEUE adds a kernel→userspace→kernel round trip per packet (~50–200 µs). If the queue fills because the userspace process is slow, packets are dropped. `--queue-bypass` mitigates this by falling back to ACCEPT when no process is listening.

---

## NFLOG — Packet Logging to Userspace

NFLOG delivers **copies** of packets to userspace for logging. Unlike NFQUEUE, the kernel does not wait for a verdict — the original packet continues immediately.

```bash
# iptables: log INVALID packets to group 1, then drop
iptables -A INPUT -m conntrack --ctstate INVALID \
    -j NFLOG --nflog-group 1 --nflog-prefix "INVALID: "
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
```

```nftables
# nftables: combined log + action
table inet filter {
    chain input {
        ct state invalid log group 1 prefix "INVALID: " drop
        tcp dport 22 ct state new log group 2 prefix "SSH-NEW: "
    }
}
```

### ulogd2 Configuration

`ulogd2` receives NFLOG packets via Netlink and routes them to output plugins (files, pcap, databases):

```ini
# /etc/ulogd.conf (minimal)
[global]
logfile = "/var/log/ulogd.log"
loglevel = 5
stack = log1:NFLOG,base1:BASE,ifi1:IFINDEX,ip2str1:IP2STR,print1:PRINTPKT,emu1:LOGEMU

[log1]
group = 1       # must match --nflog-group / log group N in rules

[emu1]
file  = "/var/log/netfilter.log"
sync  = 1
```

### NFLOG vs LOG Target

|Feature|`LOG` target|`NFLOG` target|
|---|---|---|
|Destination|Kernel log (dmesg / printk)|Userspace via Netlink|
|Performance|High overhead (synchronous printk)|Batched Netlink delivery|
|Structured output|No — free text|Yes — ulogd2 plugins|
|pcap / database|No|Yes (ulogd2 plugins)|
|Production use|Debugging only|Recommended|

---

## libnetfilter Libraries

|Library|Purpose|
|---|---|
|`libmnl`|Low-level Netlink message building and parsing|
|`libnftnl`|nftables object serialization (used by `nft`)|
|`libnetfilter_conntrack`|Read / write the conntrack table|
|`libnetfilter_queue`|NFQUEUE packet receive / verdict API|
|`libnetfilter_log`|NFLOG packet receive API|
|`libnetfilter_acct`|Netfilter accounting object management|
|`libnetfilter_cthelper`|Userspace CT helper framework|
|`libnetfilter_cttimeout`|Per-flow CT timeout policy management|
|`libipset`|ipset management|
|`libnftables`|High-level nftables library (JSON / scripting)|

---

## iptables

### iptables Tables and Chains

`iptables` organises rules into **tables**, each attached to specific hook points. Each table contains **chains** — ordered sequences of rules evaluated top-to-bottom.

```
Table      Hook Points                      Built-in Chains
─────────  ──────────────────────────────   ──────────────────────────────────────────
raw        PRE_ROUTING · LOCAL_OUT          PREROUTING · OUTPUT
mangle     all five                         PREROUTING · INPUT · FORWARD · OUTPUT · POSTROUTING
nat        PRE_ROUTING · LOCAL_IN           PREROUTING · INPUT · OUTPUT · POSTROUTING
           LOCAL_OUT · POST_ROUTING         (INPUT available since kernel 3.7)
filter     LOCAL_IN · FORWARD · LOCAL_OUT   INPUT · FORWARD · OUTPUT
security   LOCAL_IN · FORWARD · LOCAL_OUT   INPUT · FORWARD · OUTPUT
```

### Packet Flow Through iptables Tables

**Forwarded packet** (numbered evaluation order):

```
1.  raw::PREROUTING
2.  [conntrack lookup / create]
3.  mangle::PREROUTING
4.  nat::PREROUTING            ← DNAT
5.  [routing decision]
6.  mangle::FORWARD
7.  filter::FORWARD            ← main forwarding filter
8.  security::FORWARD
9.  mangle::POSTROUTING
10. nat::POSTROUTING           ← SNAT / Masquerade
```

### iptables Rule Structure

```
iptables [-t table] COMMAND chain [match...] [-j target]
```

|Component|Description|
|---|---|
|`-t table`|`raw`, `mangle`, `nat`, `filter`, `security` (default: `filter`)|
|`COMMAND`|`-A` append · `-I [N]` insert · `-D` delete · `-R` replace · `-L` list · `-F` flush|
|`chain`|`INPUT`, `FORWARD`, `OUTPUT`, `PREROUTING`, `POSTROUTING`, or a user chain|
|match|`-p tcp`, `-s 10.0.0.0/8`, `-m conntrack --ctstate NEW`, …|
|`-j target`|`ACCEPT`, `DROP`, `REJECT`, `LOG`, `DNAT`, user chain, …|

### iptables Built-in Targets

#### Terminating Targets

|Target|Effect|
|---|---|
|`ACCEPT`|Accept; skip remaining rules in this chain|
|`DROP`|Silently discard|
|`REJECT [--reject-with TYPE]`|Discard and send ICMP error or TCP RST|
|`RETURN`|Return from user chain to calling chain|
|`QUEUE`|Deliver to NFQUEUE 0 (legacy; use `NFQUEUE` instead)|

#### REJECT `--reject-with` Types

|Type|Response sent|
|---|---|
|`icmp-net-unreachable`|ICMP type 3 code 0|
|`icmp-host-unreachable`|ICMP type 3 code 1|
|`icmp-port-unreachable`|ICMP type 3 code 3 **(default for TCP/UDP)**|
|`icmp-proto-unreachable`|ICMP type 3 code 2|
|`icmp-net-prohibited`|ICMP type 3 code 9|
|`icmp-host-prohibited`|ICMP type 3 code 10|
|`icmp-admin-prohibited`|ICMP type 3 code 13|
|`tcp-reset`|TCP RST (TCP only)|
|`icmp6-no-route`|ICMPv6 type 1 code 0 (ip6tables)|
|`icmp6-adm-prohibited`|ICMPv6 type 1 code 1 (ip6tables)|
|`icmp6-port-unreachable`|ICMPv6 type 1 code 4 **(ip6tables default)**|

#### Non-Terminating Targets

|Target|Effect|
|---|---|
|`LOG`|Log to kernel log and continue|
|`NFLOG`|Log via Netlink to userspace and continue|
|`MARK --set-mark VALUE`|Set `skb->mark` and continue|
|`CONNMARK`|Save / restore conntrack mark and continue|
|`DSCP --set-dscp VALUE`|Set DSCP bits in IP ToS and continue|
|`TOS --set-tos VALUE`|Set IP ToS byte and continue|
|`TTL --ttl-set VALUE`|Modify IP TTL and continue|
|`TRACE`|Enable per-rule packet tracing and continue|
|`TCPMSS --clamp-mss-to-pmtu`|Clamp TCP MSS to PMTU and continue|

#### NAT Targets (nat table only)

|Target|Usage|
|---|---|
|`DNAT --to-destination IP[:port[-port]]`|Rewrite destination address/port|
|`SNAT --to-source IP[:port[-port]]`|Rewrite source address/port|
|`MASQUERADE`|SNAT using the outgoing interface's current IP|
|`REDIRECT --to-ports PORT`|Redirect to local port (DNAT to 127.0.0.1)|
|`NETMAP --to IP/MASK`|1:1 network address block mapping|
|`TPROXY --tproxy-mark M --on-port P`|Transparent proxy redirect|
|`SYNPROXY`|Intercept and validate TCP handshake before forwarding|

### iptables Match Extensions

Loaded with `-m module_name`:

|Module|Key options|Description|
|---|---|---|
|`conntrack`|`--ctstate`, `--ctproto`, `--ctmark`|Match conntrack state / attributes|
|`state`|`--state`|Legacy alias for `conntrack` — avoid in new rules|
|`multiport`|`--dports`, `--sports`|Match multiple ports in one rule|
|`limit`|`--limit N/s --limit-burst B`|Token-bucket rate limiting (global, not per-source)|
|`hashlimit`|`--hashlimit-above`, `--hashlimit-mode`|Per-source/dest rate limiting|
|`connlimit`|`--connlimit-above N`|Limit concurrent connections per key|
|`iprange`|`--src-range`, `--dst-range`|Match IP address ranges|
|`set`|`--match-set NAME src\|dst`|Match against an ipset|
|`recent`|`--rcheck`, `--update`, `--set`, `--remove`|Per-source access history|
|`string`|`--string STR --algo bm\|kmp`|Payload string matching|
|`u32`|`--u32 EXPR`|Raw packet byte matching|
|`length`|`--length MIN:MAX`|Packet length matching|
|`ttl`|`--ttl-eq`, `--ttl-lt`, `--ttl-gt`|IP TTL matching|
|`owner`|`--uid-owner`, `--gid-owner`|Socket owner (OUTPUT chain only)|
|`physdev`|`--physdev-in`, `--physdev-out`|Bridge physical device matching|
|`addrtype`|`--src-type`, `--dst-type`|Address type (LOCAL, BROADCAST, …)|
|`mark`|`--mark VALUE[/MASK]`|Packet mark matching|
|`osf`|`--genre OS --ttl MODE`|Passive OS fingerprinting|
|`nfacct`|`--nfacct-name NAME`|Increment a named kernel counter|
|`comment`|`--comment "text"`|Annotate a rule; no effect on matching|
|`time`|`--timestart`, `--timestop`, `--weekdays`|Time-based matching|
|`policy`|`--pol ipsec\|none`, `--dir in\|out`|IPsec policy matching|

### ip6tables and arptables

`ip6tables` is the IPv6 equivalent of `iptables` with the same table/chain structure:

- IPv6 NAT is supported: `ip6tables -t nat`.
- ICMPv6 uses `-p ipv6-icmp`. **Never blanket-drop ICMPv6** — it is required for NDP, PMTUD, and SLAAC.
- `--reject-with` uses `icmp6-*` codes.

`arptables` operates on `NF_ARP_*` hooks:

```bash
# Drop ARP replies impersonating 192.168.1.1
arptables -A INPUT --opcode reply --arp-ip-src 192.168.1.1 -j DROP
```

---

## nftables

### nftables Data Model

nftables replaces `iptables`, `ip6tables`, `arptables`, and `ebtables` with one framework:

```
Table  (named; belongs to a family)
  └── Chain  (base chain attached to a hook, or a regular chain called by jump/goto)
        └── Rule  (ordered list of match expressions + one verdict statement)
```

Key differences from iptables:

- **No built-in tables or chains** — you create everything explicitly.
- **Single `nft` binary** for all protocol families.
- **Atomic transactions** — rule sets applied or rolled back as a unit via Netlink.
- **Native sets and maps** — O(1) lookup without a separate `ipset` tool.
- **Counters, limits, quotas** built in as rule statements.

### Table Families

|Family|Covers|
|---|---|
|`ip`|IPv4 only|
|`ip6`|IPv6 only|
|`inet`|IPv4 + IPv6 (single rule set for both)|
|`arp`|ARP|
|`bridge`|Bridge / Ethernet frames|
|`netdev`|Per-device ingress / egress|

### Chain Types

|Type|Valid hooks|Purpose|
|---|---|---|
|`filter`|All|Packet filtering|
|`nat`|`prerouting`, `input`, `output`, `postrouting`|Address translation|
|`route`|`output` only|Re-route packet after mark change|

```nftables
table inet firewall {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
        ct state invalid drop
        iif "lo" accept
        tcp dport { 22, 80, 443 } ct state new accept
        reject with icmpx type port-unreachable
    }

    # Regular chain: no hook — called via jump/goto
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

# Transport
tcp dport 80
tcp dport 1024-65535
udp sport { 53, 5353 }
tcp flags syn / syn,rst,ack      # SYN only (not SYN-ACK)
tcp flags syn,ack / syn,ack      # SYN+ACK

# Conntrack
ct state new,established,related,invalid,untracked
ct mark 0x10
ct zone 1

# Meta / interface
iif "eth0"                       # by index (faster)
iifname "eth*"                   # by name with wildcard (slower)
meta l4proto tcp
meta mark 0x100
skuid 1000                       # socket owner UID (output chain only)
```

#### Verdict Statements

```nftables
accept
drop
return                    # return from regular chain to caller
jump other_chain          # jump; return to caller when done
goto other_chain          # jump; do NOT return (tail-call)
queue num 0
queue num 0-3             # fan-out
queue num 0 bypass        # ACCEPT if no listener
reject                    # ICMP port-unreachable (type auto-selected by L4)
reject with tcp reset     # TCP RST
reject with icmpx type admin-prohibited
```

#### Action Statements (non-terminating)

```nftables
counter                   # increment rule counter
log prefix "X: " level warn
log group 1 prefix "NFLOG: "

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

#### Anonymous Sets (inline, immutable)

```nftables
tcp dport { 80, 443, 8080 } accept
ip saddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } drop
```

#### Named Sets (persistent, runtime-updatable without touching rules)

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
# Add / remove at runtime
nft add element inet filter blocked_ips { 203.0.113.5 }
nft delete element inet filter blocked_ips { 203.0.113.5 }
```

#### Maps

```nftables
table inet filter {
    # Verdict map: per-source-IP verdict — O(1) lookup
    map ip_verdicts {
        type ipv4_addr : verdict
        elements = { 10.0.0.1 : accept, 10.0.0.2 : drop }
    }
    chain input {
        ip saddr vmap @ip_verdicts
    }

    # Data map: destination port → backend IP (DNAT)
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
|`constant`|Set is immutable after creation|
|`interval`|Elements can be CIDR prefixes or ranges|
|`timeout`|Elements auto-expire; set per-element or per-set timeout|
|`dynamic`|Elements can be inserted from the packet path via `add` / `update`|

### nftables Flowtables

A **flowtable** provides a fast path for established TCP/UDP flows, bypassing the full Netfilter hook chain. Once a flow is offloaded, subsequent packets are forwarded at the ingress hook (before PRE_ROUTING), skipping filter, mangle, and nat tables entirely.

```nftables
table inet router {
    flowtable ft {
        hook ingress priority -1;
        devices = { eth0, eth1 };
        # flags offload;   # enable NIC hardware offload (requires driver support)
    }

    chain forward {
        type filter hook forward priority filter; policy drop;

        # Offload established TCP/UDP flows to the fast path
        ip protocol { tcp, udp } ct state established flow add @ft

        ct state related,established accept
        ct state invalid drop
        oifname "eth0" ct state new accept
    }
}
```

Key constraints: only IPv4/IPv6 TCP and UDP; NAT is supported since Linux 5.3; offloaded entries have their conntrack timeout frozen. For hardware offload and full documentation see [[Netfilter Conntrack — Connection Tracking#Flowtable and Hardware Offload]].

### Migrating from iptables to nftables

```bash
# Translate a single rule
iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT
# → nft add rule ip filter INPUT tcp dport 22 counter accept

# Translate an entire saved ruleset
iptables-save | iptables-restore-translate -f /etc/nftables/converted.nft
```

> [!note] iptables-nft On modern distributions, `iptables` is `iptables-nft` — a thin wrapper that translates iptables commands into nftables Netlink messages. `nft list ruleset` shows all rules including those added via `iptables-nft`. The `iptables-legacy` binary (setsockopt path) maintains a completely separate ruleset visible only via `iptables-legacy -L`.

---

## ipset

`ipset` provides **hash and bitmap data structures** in the kernel for fast set-membership matching. A single iptables rule with an ipset replaces thousands of individual address rules with an O(1) hash lookup.

### ipset Types

|Set type|Key fields|Use case|
|---|---|---|
|`hash:ip`|Single IP address|Blocklists, allowlists|
|`hash:net`|CIDR prefix|Network-level lists|
|`hash:ip,port`|IP + L4 port|Per-service per-host rules|
|`hash:net,port`|Network + port|Per-service per-network|
|`hash:ip,port,ip`|Src IP + port + Dst IP|Full 5-tuple matching|
|`hash:mac`|MAC address|L2 filtering (via ebtables)|
|`bitmap:ip`|Dense IP range (up to /16, max 65536 addresses)|Fast lookup for a compact subnet|
|`bitmap:port`|Dense port range|Bulk port range matching|
|`list:set`|List of set names|Chained set lookup|

> [!note] bitmap:ip size limit `bitmap:ip` stores a contiguous range of IPv4 addresses as a bitmap. The maximum is **65536 entries**, corresponding to a /16 subnet. You cannot use a /8 (16 million addresses); use `hash:net` for large or sparse address spaces.

### ipset Commands

```bash
# Create
ipset create BLOCKED_NETS hash:net

# Add / remove entries
ipset add BLOCKED_NETS 203.0.113.0/24
ipset del BLOCKED_NETS 203.0.113.0/24

# Test membership (exits 0 on match)
ipset test BLOCKED_NETS 203.0.113.5

# List, flush, destroy
ipset list BLOCKED_NETS
ipset flush BLOCKED_NETS       # clear entries, keep set
ipset destroy BLOCKED_NETS     # remove set entirely

# Persistence
ipset save   > /etc/ipset.conf
ipset restore < /etc/ipset.conf
```

#### Using ipset in iptables

```bash
ipset create BLOCKED_IPS hash:ip
ipset add BLOCKED_IPS 192.0.2.1
iptables -I INPUT -m set --match-set BLOCKED_IPS src -j DROP

ipset create ALLOWED_MGMT hash:net
ipset add ALLOWED_MGMT 10.0.0.0/8
iptables -A INPUT -p tcp --dport 22 -m set --match-set ALLOWED_MGMT src -j ACCEPT
```

### ipset Timeout (Auto-expiry)

```bash
ipset create TEMP_BLOCK hash:ip timeout 300   # default 5 minutes
ipset add TEMP_BLOCK 192.0.2.1 timeout 60    # override per element
ipset add TEMP_BLOCK 192.0.2.2               # uses set default (300 s)
```

### ipset vs nftables Sets

|Feature|ipset|nftables native sets|
|---|---|---|
|Requires iptables|Yes (or `nft_compat`)|No|
|Runtime update without rule reload|Yes|Yes|
|Auto-expiry|Yes (`timeout`)|Yes (`timeout` flag)|
|Dynamic insertion from packet path|No|Yes (`dynamic` flag)|
|Verdict maps|No|Yes|

> [!tip] Prefer **nftables native sets** for new deployments. Use `ipset` when integrating with tools that manage it directly (fail2ban, blocklist automation scripts, etc.).

---

## Connection Tracking

Netfilter's stateful layer is the `nf_conntrack` subsystem, fully documented in [[Netfilter Conntrack — Connection Tracking]].

Integration with other Netfilter components:

- Conntrack registers at `PRE_ROUTING` / `LOCAL_OUT` (priority `−200`) to look up or create entries.
- **Confirmation** — inserting the entry into the hash table — happens at `POST_ROUTING` / `LOCAL_IN` (priority `INT_MAX`), **after** all firewall rules. Packets dropped by a filter rule never produce a conntrack entry.
- `ct state` / `--ctstate` match keywords query the conntrack entry attached to the skb.
- **Conntrack is a hard prerequisite for NAT** — NAT rules cannot function without it.

---

## NAT

NAT is implemented in `nf_nat`, which depends on `nf_conntrack`. The critical property: **NAT rules evaluate only once per flow** — on the first packet. The translation mapping is stored in the conntrack reply tuple. All subsequent packets are translated by entry lookup, with no rule re-evaluation.

For the full mechanism see [[Netfilter Conntrack — Connection Tracking#NAT Integration]].

### SNAT and Masquerade

```bash
# iptables: Masquerade — outbound NAT for a dynamic public IP
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# iptables: SNAT to a fixed IP
iptables -t nat -A POSTROUTING -o eth0 -j SNAT --to-source 203.0.113.1
```

```nftables
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat;
        oifname "eth0" masquerade
    }
}
```

### DNAT and Port Forwarding

```bash
# Forward external port 8080 → internal 192.168.1.100:80
iptables -t nat -A PREROUTING -p tcp --dport 8080 \
    -j DNAT --to-destination 192.168.1.100:80
# Also allow the forwarded traffic through FORWARD
iptables -A FORWARD -d 192.168.1.100 -p tcp --dport 80 \
    -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT
```

```nftables
table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat;
        tcp dport 8080 dnat to 192.168.1.100:80
    }
}
```

### NAT Hairpinning

When an internal host reaches an internal server via its **external IP**, the reply goes directly back (not through the NAT gateway), breaking NAT state. Fix with an additional POSTROUTING SNAT:

```bash
iptables -t nat -A POSTROUTING \
    -s 192.168.1.0/24 -d 192.168.1.100 -p tcp --dport 80 \
    -j MASQUERADE
```

---

## Network Namespaces

Every Linux **network namespace** contains a completely independent Netfilter state: independent hook registrations, rule sets, conntrack tables, timeouts, and sysctl values. This isolates container firewalling from host firewalling.

```bash
# Create and operate in a namespace
ip netns add myns
ip netns exec myns iptables -A INPUT -j DROP
ip netns exec myns nft list ruleset
ip netns exec myns conntrack -L

# Access without networking tools inside
nsenter --net=/var/run/netns/myns -- nft list ruleset
```

```
Host netns
  ├── Netfilter hooks:  host iptables/nftables rules
  ├── Conntrack table:  host-level sessions, Docker NAT
  └── sysctls:          net.netfilter.nf_conntrack_max = <host value>

Container netns (e.g., a Docker container)
  ├── Netfilter hooks:  typically empty
  ├── Conntrack table:  separate, isolated — always empty at container start
  └── sysctls:          inherits host values at creation time
```

> [!note] Docker's MASQUERADE / NAT rules operate in the **host netns** on the `docker0` interface — not inside the container's netns. Containers themselves have no iptables rules by default.

---

## IPv6-Specific Considerations

### ICMPv6 Requirements

IPv6 delegates to ICMPv6 functions that IPv4 handled via ARP and other protocols. **Never blanket-drop ICMPv6.**

|Type|Name|Function|Status|
|---|---|---|---|
|1|Destination Unreachable|Error reporting|Required|
|2|Packet Too Big|**PMTUD** — IPv6 routers never fragment|**Critical**|
|3|Time Exceeded|Traceroute, loop detection|Required|
|4|Parameter Problem|Error reporting|Required|
|128|Echo Request|ping6|Recommended|
|129|Echo Reply|ping6|Recommended|
|133|Router Solicitation|SLAAC|Required|
|134|Router Advertisement|SLAAC / gateway discovery|Required|
|135|Neighbor Solicitation|NDP — ARP equivalent|**Critical**|
|136|Neighbor Advertisement|NDP — ARP equivalent|**Critical**|
|143|MLDv2 Report|Multicast group membership|Required|

```nftables
# nftables: accept all required ICMPv6 types
ip6 nexthdr ipv6-icmp icmpv6 type {
    destination-unreachable, packet-too-big, time-exceeded, parameter-problem,
    echo-request, echo-reply, nd-router-solicit, nd-router-advert,
    nd-neighbor-solicit, nd-neighbor-advert, mld2-listener-report
} accept
```

> [!warning] PMTUD and Packet Too Big Dropping ICMPv6 type 2 breaks Path MTU Discovery. IPv6 routers never fragment — the source must reduce its MSS based on this feedback. Blocked type 2 causes connections across smaller-MTU links to stall silently after the handshake.

### IPv6 Extension Header Matching

```bash
# iptables: drop routing header type 0 (deprecated; used in amplification attacks)
ip6tables -A INPUT -m rt --rt-type 0 -j DROP
```

```nftables
# nftables
ip6 nexthdr ipv6-route rt type 0 drop
```

#### Extension Header Match Modules (iptables)

|Module|Matches|
|---|---|
|`-m rt`|Routing header (`--rt-type`, `--rt-segsleft`)|
|`-m frag`|Fragment header (`--fragfirst`, `--fraglast`, `--fragmore`, `--fragid`)|
|`-m hbh`|Hop-by-hop options header|
|`-m dst`|Destination options header|
|`-m ah`|Authentication header (IPsec AH)|
|`-m ipv6header`|Presence of any specific header type|

### IPv6 Address Types and Bogon Rules

|Range|Type|Firewall consideration|
|---|---|---|
|`::1/128`|Loopback|Allow only on `lo`; drop if arriving externally|
|`fe80::/10`|Link-local|Required for NDP; never route globally|
|`fc00::/7`|Unique local (ULA)|Treat like RFC1918 — block inbound from WAN|
|`ff00::/8`|Multicast|Allow MLDv2 (type 143); others optional|
|`2000::/3`|Global unicast|Public addresses|
|`2002::/16`|6to4|Block if 6to4 is not in use|

```nftables
# Drop bogon source addresses from WAN
table inet bogons6 {
    chain prerouting {
        type filter hook prerouting priority raw;
        iifname "eth0" ip6 saddr ::1/128     drop
        iifname "eth0" ip6 saddr fe80::/10   drop
        iifname "eth0" ip6 saddr fc00::/7    drop
        iifname "eth0" ip6 saddr 2002::/16   drop
    }
}
```

---

## ebtables — Layer 2 Filtering

`ebtables` filters **Ethernet frames** at Layer 2 using `NFPROTO_BRIDGE` hooks. It is the bridge equivalent of iptables.

### ebtables Tables and Chains

|Table|Chains|Purpose|
|---|---|---|
|`filter`|`FORWARD` · `INPUT` · `OUTPUT`|Frame filtering (primary use case)|
|`nat`|`PREROUTING` · `OUTPUT` · `POSTROUTING`|Frame address rewriting|
|`broute`|`BROUTING`|Bridge vs. route decision per frame|

The `BROUTING` chain fires before the forwarding decision. Returning `BROUTING` forces the frame to be routed (sent to the L3 IP stack) rather than bridged — useful for selectively routing some traffic through iptables/conntrack.

### ebtables Match Extensions and Targets

**Common match options:**

|Option|Description|
|---|---|
|`-p PROTO`|EtherType: `IPv4`, `IPv6`, `ARP`, `802_1Q`, or hex (e.g. `0x8100`)|
|`--src MAC` / `--dst MAC`|MAC address (with optional mask)|
|`-i IFACE` / `-o IFACE`|Bridge port (physical interface name)|
|`--vlan-id ID`|802.1Q VLAN ID (requires `-p 802_1Q`)|
|`--vlan-prio PRIO`|802.1Q priority bits|
|`--ip-src IP` / `--ip-dst IP`|IP header inside an IPv4 frame|
|`--ip-proto PROTO`|L4 protocol inside IPv4|
|`--arp-ip-src IP` / `--arp-ip-dst IP`|IP in ARP packet|
|`--arp-mac-src MAC` / `--arp-mac-dst MAC`|MAC in ARP packet|
|`--limit RATE`|Token-bucket rate limiting|

**Targets:**

|Target|Effect|
|---|---|
|`ACCEPT`|Allow frame; bridge normally|
|`DROP`|Drop frame|
|`RETURN`|Return from user chain|
|`REDIRECT`|Change destination MAC to bridge MAC (nat table)|
|`LOG`|Log to kernel log and continue|
|`MARK --set-mark VALUE`|Set frame mark|
|`BROUTING`|Force frame to be routed (broute table only)|

```bash
# Allow only ARP and IPv4 through the bridge; drop everything else
ebtables -A FORWARD -p ARP  -j ACCEPT
ebtables -A FORWARD -p IPv4 -j ACCEPT
ebtables -A FORWARD         -j DROP

# Drop frames from a specific MAC
ebtables -A FORWARD --src de:ad:be:ef:00:01 -j DROP

# Filter by VLAN ID
ebtables -A FORWARD -p 802_1Q --vlan-id 100 -j ACCEPT
ebtables -A FORWARD -p 802_1Q               -j DROP

# Persist
ebtables-save    > /etc/ebtables.conf
ebtables-restore < /etc/ebtables.conf
```

**nftables bridge family** replaces ebtables:

```nftables
table bridge filter {
    chain forward {
        type filter hook forward priority 0; policy accept;
        meta protocol != { ip, arp } drop
        ether saddr de:ad:be:ef:00:01 drop
        vlan id != { 10, 20 } drop
    }
}
```

### br_netfilter Integration

Loading `br_netfilter` makes bridged IP frames traverse the standard IPv4/IPv6 hooks, enabling iptables/nftables/conntrack to filter them.

```bash
modprobe br_netfilter
sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1

# Persist
cat >> /etc/sysctl.d/99-bridge-nf.conf << 'EOF'
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF
echo "br_netfilter" >> /etc/modules-load.d/netfilter.conf
```

> [!warning] Double-tracking With `br_netfilter`, traffic that crosses a bridge and is then routed (common on Docker hosts) can be processed by conntrack twice. This produces duplicate NAT application or INVALID states. Use conntrack zones to isolate bridge and routing domains.

---

## VLANs, Tunnels, and Encapsulation

### VLAN (802.1Q) and Netfilter

The kernel strips 802.1Q tags before Netfilter sees the packet. Rules operate on sub-interface names, not VLAN IDs.

```bash
iptables -A FORWARD -i eth0.100 -o eth0.200 -j ACCEPT

# To match on the VLAN ID before stripping, use ebtables:
ebtables -A FORWARD -p 802_1Q --vlan-id 100 -j ACCEPT
```

### VXLAN and Overlay Networks

VXLAN (UDP/4789) and Geneve (UDP/6081) encapsulate Ethernet frames in UDP. Netfilter on `eth0` sees the outer UDP packet; Netfilter on `vxlan0` sees the decapsulated inner packet.

```bash
iptables -A INPUT -p udp --dport 4789 -j ACCEPT   # VXLAN
iptables -A INPUT -p udp --dport 6081 -j ACCEPT   # Geneve
iptables -A FORWARD -i vxlan0 -p tcp --dport 22 -j ACCEPT
```

### GRE and IPIP Tunnels

GRE (protocol 47) and IPIP (protocol 4) are IP-in-IP tunnels. Rules on the physical interface match the outer header; rules on the tunnel interface match the inner packet.

```bash
iptables -A INPUT -p 47 -j ACCEPT   # GRE
iptables -A INPUT -p 4  -j ACCEPT   # IPIP
iptables -A FORWARD -i gre0 -j ACCEPT
modprobe nf_conntrack_proto_gre     # conntrack for GRE
```

### MTU, Fragmentation, and MSS Clamping

All encapsulation reduces the inner MTU:

|Encapsulation|Overhead|Inner MTU (from 1500-byte outer)|
|---|---|---|
|VXLAN (IPv4 outer)|50 bytes|1450|
|GRE (no options)|24 bytes|1476|
|GRE (with checksum)|28 bytes|1472|
|IPIP|20 bytes|1480|
|WireGuard|60 bytes|1440|
|IPsec (ESP, transport mode)|~50–73 bytes|~1427–1450|

Clamp TCP MSS to prevent fragmentation:

```bash
# iptables
iptables -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
    -j TCPMSS --clamp-mss-to-pmtu
```

```nftables
# nftables
table inet mtu_fix {
    chain forward {
        type filter hook forward priority mangle;
        tcp flags syn / syn,rst tcp option maxseg size set rt mtu
    }
}
```

---

## WireGuard and Netfilter

WireGuard presents as a standard virtual NIC (`wg0`). Netfilter sees two separate packet paths:

```
Encrypted UDP/51820 arrives on eth0
        │
NF_INET_PRE_ROUTING (eth0)   ← firewall sees encrypted outer UDP

WireGuard module decrypts

Decrypted inner packet injected on wg0
        │
NF_INET_PRE_ROUTING (wg0)    ← firewall sees inner plaintext
        │
NF_INET_FORWARD              ← normal forward rules apply
```

### Firewall Rules for WireGuard

```nftables
table inet wg_fw {
    chain input {
        type filter hook input priority filter; policy drop;
        iif "lo" accept
        ct state established,related accept
        udp dport 51820 accept      # WireGuard handshake / keepalive
        iif "wg0"       accept      # all traffic from tunnel
        reject with icmpx type port-unreachable
    }
    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state established,related accept
        iif "wg0" oif "eth0" ct state new accept
    }
}

table ip wg_nat {
    chain postrouting {
        type nat hook postrouting priority srcnat;
        iif "wg0" oif "eth0" masquerade
    }
}
```

> [!note] Conntrack and keepalives WireGuard sends keepalives every 25 seconds (`PersistentKeepalive = 25`). The default `nf_conntrack_udp_timeout_stream` is 180 s — sufficient. If you reduce UDP stream timeout below 25 s, the conntrack entry for the outer session expires and the next packet appears as `NEW`, requiring re-evaluation by your rules.

---

## IPsec and xfrm Integration

Linux IPsec is implemented in the **xfrm** (transform) framework. xfrm and Netfilter share the packet path but at different positions.

### xfrm Hooks in the Packet Path

```
Incoming encrypted packet
        │
NF_INET_PRE_ROUTING       ← Netfilter sees encrypted outer packet
        │
xfrm inbound policy check and decryption (AH / ESP)
        │
NF_INET_LOCAL_IN or FORWARD   ← Netfilter sees DECRYPTED inner packet

Outgoing packet
        │
NF_INET_LOCAL_OUT or FORWARD  ← Netfilter sees plaintext
        │
xfrm outbound policy check and encryption
        │
NF_INET_POST_ROUTING          ← Netfilter sees ENCRYPTED outer packet
```

> [!important] Write firewall rules for the **inner** (decrypted) packet when filtering IPsec content. `FORWARD` / `INPUT` rules see plaintext. `PREROUTING` / `POSTROUTING` rules see the encrypted outer packet.

### Matching IPsec Policy in Firewall Rules

```bash
# iptables: accept inbound ESP-decrypted traffic
iptables -A INPUT -m policy --pol ipsec --dir in --proto esp -j ACCEPT

# Accept outbound traffic that will be encrypted
iptables -A OUTPUT -m policy --pol ipsec --dir out --proto esp -j ACCEPT

# Drop unencrypted traffic on an IPsec-only interface
iptables -A INPUT -i eth1 -m policy --pol none --dir in -j DROP
```

|`-m policy` option|Description|
|---|---|
|`--pol ipsec\|none`|Match IPsec-processed vs unprocessed packets|
|`--dir in\|out`|Policy direction|
|`--proto esp\|ah`|IPsec protocol|
|`--spi VALUE`|Security Parameter Index|
|`--tunnel-src IP` / `--tunnel-dst IP`|Outer tunnel endpoint addresses|

```nftables
# nftables
table inet ipsec_fw {
    chain input {
        type filter hook input priority filter;
        ipsec in ip saddr 203.0.113.1 accept
    }
    chain output {
        type filter hook output priority filter;
        ipsec out accept
    }
}
```

---

## Docker Networking Chains

### Docker Chain Architecture

Docker injects chains into the **host netns** iptables rule set at daemon startup, rebuilding them whenever containers start or stop:

```
filter::FORWARD
  ├── -j DOCKER-USER               ← user rules — evaluated FIRST
  ├── -j DOCKER-ISOLATION-STAGE-1
  │       └── -j DOCKER-ISOLATION-STAGE-2  ← prevents cross-network traffic
  └── -j DOCKER                    ← per-container allow rules

nat::PREROUTING
  └── -j DOCKER                    ← port-mapping DNAT rules

nat::POSTROUTING
  └── MASQUERADE rules              ← outbound SNAT per Docker network
```

**DOCKER-ISOLATION** prevents containers on different Docker networks from communicating at L3:

```
DOCKER-ISOLATION-STAGE-1:  -i docker0 ! -o docker0 → STAGE-2 ; RETURN
DOCKER-ISOLATION-STAGE-2:  -o docker0 → DROP ; RETURN
```

Docker also inserts per-container rules in the `DOCKER` chain for each `-p HOST:CONTAINER` port mapping:

```bash
# Example: container mapped with -p 8080:80
# Docker inserts in nat::PREROUTING:
#   ! -i docker0 -p tcp --dport 8080 -j DNAT --to-destination 172.17.0.2:80
# And in filter::DOCKER:
#   -d 172.17.0.2/32 ! -i docker0 -o docker0 -p tcp --dport 80 -j ACCEPT

# Inspect Docker's injected rules
iptables -t nat -L DOCKER -n -v
iptables -L DOCKER -n -v
```

### DOCKER-USER — Safe Customisation Point

`DOCKER-USER` is the **only correct chain for adding your own rules** that interact with Docker traffic. Rules added directly to `FORWARD`, or to `DOCKER` / `DOCKER-ISOLATION` chains, may be overwritten on Docker daemon restart.

```bash
# Restrict access to mapped ports to specific source IPs
iptables -I DOCKER-USER \
    -i eth0 ! -s 203.0.113.0/24 \
    -j DROP

# Rate-limit new connections to Docker containers
iptables -I DOCKER-USER -i eth0 -p tcp \
    -m hashlimit \
    --hashlimit-name docker_new \
    --hashlimit-above 50/second \
    --hashlimit-burst 100 \
    --hashlimit-mode srcip \
    -j DROP

# ALWAYS end DOCKER-USER with RETURN.
# Packets that don't match any of your rules must reach the end of DOCKER-USER
# and return to the FORWARD chain, where Docker's own -j DOCKER jump fires.
# Without RETURN, unmatched packets fall off the end of DOCKER-USER into the
# FORWARD chain's default policy — which is DROP — silently breaking all
# container port mappings.
iptables -A DOCKER-USER -j RETURN
```

### Docker IPv6 and conntrack

Enable IPv6 in `/etc/docker/daemon.json`:

```json
{
    "ipv6": true,
    "fixed-cidr-v6": "fd00:dead:beef::/48",
    "ip6tables": true
}
```

Docker then creates equivalent `ip6tables` chains. Inspect with:

```bash
ip6tables -L DOCKER-USER -n -v
ip6tables -t nat -L DOCKER -n -v
```

---

## Podman and Rootless Containers

|Mode|Networking mechanism|Host Netfilter modified?|
|---|---|---|
|**Rootful Podman**|`netavark` + firewalld / nftables|Yes — via `PODMAN` chains (mirrors Docker's pattern)|
|**Rootless Podman**|`slirp4netns` or `pasta` — userspace NAT inside container netns|**No** — host Netfilter never sees container traffic|

For rootless Podman, `conntrack -L` on the host shows nothing from containers. Filtering requires rules inside the container's network namespace.

---

## SYNPROXY — SYN Flood Protection

Under a SYN flood, conntrack creates a `SYN_SENT` entry for every forged SYN before the handshake completes, eventually filling the conntrack table. SYNPROXY intercepts SYNs and **completes the three-way handshake on the kernel's behalf**. Only clients that send a valid ACK produce a conntrack entry.

```
Without SYNPROXY:  SYN → conntrack SYN_SENT entry created → table may fill
With SYNPROXY:     SYN → kernel sends SYN+ACK
                   ACK → kernel validates → creates ESTABLISHED entry → forwards to server
                   (forged SYNs never return ACK → no entry created)
```

### iptables Setup

```bash
# Step 1 (raw PREROUTING): exempt SYNs from conntrack — no premature entry
iptables -t raw -A PREROUTING -p tcp --dport 80 --syn -j CT --notrack

# Step 2 (filter INPUT or FORWARD): hand UNTRACKED + INVALID packets to SYNPROXY
iptables -A INPUT -p tcp --dport 80 \
    -m conntrack --ctstate INVALID,UNTRACKED \
    -j SYNPROXY --sack-perm --timestamp --wscale 7 --mss 1460

# Step 3: drop everything SYNPROXY rejects (failed handshakes become INVALID)
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
```

### nftables Setup

```nftables
table inet synproxy_demo {
    chain prerouting {
        type filter hook prerouting priority raw;
        tcp dport 80 tcp flags syn notrack
    }
    chain input {
        type filter hook input priority filter;
        tcp dport 80 ct state { invalid, untracked } \
            synproxy mss 1460 wscale 7 timestamp sack-perm
        ct state invalid drop
    }
}
```

### SYNPROXY Options

|Option|Description|
|---|---|
|`--mss VALUE`|MSS to advertise in the synthetic SYN+ACK|
|`--wscale VALUE`|TCP window scaling factor (0–14)|
|`--sack-perm`|Advertise Selective ACK support|
|`--timestamp`|Advertise TCP timestamps (required for `--wscale` to work)|
|`--ecn`|Advertise Explicit Congestion Notification|

> [!important] Advertised values must match what the backend server actually supports. Profile the server's TCP options with `ss -itun` or `tcpdump` before deploying.

---

## TPROXY — Transparent Proxying

TPROXY redirects packets to a **local socket** without altering the destination IP/port. The proxy reads the original destination via `SO_ORIGINAL_DST`, enabling SNI-based routing, TLS inspection, and protocol-aware load balancing.

Unlike `REDIRECT` (which rewrites the destination to 127.0.0.1), TPROXY leaves the IP header intact.

### Required Setup

Three cooperating components are needed:

#### 1 — Netfilter rule (mangle table)

```bash
iptables -t mangle -A PREROUTING \
    -p tcp --dport 80 \
    -j TPROXY --tproxy-mark 0x1/0x1 --on-port 8080 --on-ip 127.0.0.1
```

```nftables
table ip tproxy_demo {
    chain prerouting {
        type filter hook prerouting priority mangle;
        tcp dport 80 tproxy to :8080 meta mark set 0x1
    }
}
```

#### 2 — Policy routing (deliver marked packets to local stack)

```bash
ip rule  add fwmark 0x1 lookup 100
ip route add local default dev lo table 100
```

Without this, the kernel forwards the packet rather than delivering it to the local socket.

#### 3 — Proxy socket with IP_TRANSPARENT

```python
import socket, struct

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_IP, socket.IP_TRANSPARENT, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('127.0.0.1', 8080))
sock.listen(128)

conn, addr = sock.accept()
# SO_ORIGINAL_DST = 80 (from <linux/netfilter_ipv4.h>)
raw = conn.getsockopt(socket.SOL_IP, 80, 16)
family, port = struct.unpack_from('!HH', raw, 0)
ip = socket.inet_ntoa(raw[4:8])
print(f"Original destination: {ip}:{port}")
```

Use cases: Squid transparent proxy, HAProxy `bind ... transparent`, mitmproxy TLS interception, Kubernetes kube-proxy TPROXY mode.

---

## REJECT — Generating Error Responses

The `REJECT` target drops a packet and **sends an ICMP (or TCP RST) error** back to the sender. This is the correct choice for services that should be cleanly unavailable — `DROP` causes the sender to hang until timeout; `REJECT` gives an immediate error.

```bash
# iptables: default — ICMP port-unreachable
iptables -A INPUT -p tcp --dport 23 -j REJECT

# Reject with TCP RST (cleaner for TCP; no ICMP needed)
iptables -A INPUT -p tcp --dport 23 -j REJECT --reject-with tcp-reset

# Reject with admin-prohibited ICMP
iptables -A INPUT -j REJECT --reject-with icmp-admin-prohibited
```

```nftables
# nftables
reject                             # port-unreachable (type auto-selected by IP version)
reject with tcp reset              # TCP RST
reject with icmp type port-unreachable
reject with icmpv6 type port-unreachable
reject with icmpx type admin-prohibited   # icmpx = correct type for IPv4 or IPv6
```

> [!tip] DROP vs REJECT Use `REJECT` for ports that should be cleanly unavailable (SSH from untrusted sources, Telnet). Use `DROP` for stealth filtering (SYN flood mitigation, DDoS) or when you do not want to reveal the host exists. Never `DROP` ICMPv6 types that are required for IPv6 operation.

---

## Packet Mark vs Conntrack Mark

Linux maintains two distinct metadata values per packet / per flow:

||Packet mark (`skb->mark`)|Conntrack mark (`nf_conn.mark`)|
|---|---|---|
|Location|In the skb (in-flight memory)|In the conntrack entry|
|Scope|Per-packet; lost when packet leaves the system|Per-flow; survives across all packets in the flow|
|Size|32 bits|32 bits|
|Set by|`MARK` / `meta mark set`|`CONNMARK --set-mark` / `ct mark set`|
|Read by|`ip rule fwmark`, `tc fw filter`, `-m mark`|`-m connmark`, `ct mark`|

The **packet mark** is what `ip rule fwmark` and `tc fw` read for policy routing and traffic shaping. The **conntrack mark** is the persistence layer — it survives between packets of the same flow.

---

## Policy Routing with the RPDB

The Linux **Routing Policy Database** evaluates `ip rule` entries in priority order and selects the routing table for each packet. The most common use is routing by packet mark:

```bash
# Route packets marked 0x1 via ISP-A (table 10)
ip rule add fwmark 0x1 lookup 10
ip route add default via 203.0.113.1 table 10

# Route packets marked 0x2 via ISP-B (table 20)
ip rule add fwmark 0x2 lookup 20
ip route add default via 198.51.100.1 table 20
```

```bash
# Mark traffic by source subnet in mangle PREROUTING
iptables -t mangle -A PREROUTING -s 192.168.1.0/24 -j MARK --set-mark 0x1
iptables -t mangle -A PREROUTING -s 192.168.2.0/24 -j MARK --set-mark 0x2
```

---

## CONNMARK and Multi-ISP Routing

Simple mark-based routing breaks for **reply packets**: the reply arrives on ISP-A, but without saving the routing decision it may be independently evaluated and sent out ISP-B, causing asymmetric routing.

`CONNMARK` saves the packet mark into the conntrack entry on the first packet and restores it for every subsequent packet — making routing **sticky for the entire connection**.

```bash
# Step 1 (mangle PREROUTING): restore saved connmark → packet mark for existing flows
iptables -t mangle -A PREROUTING -j CONNMARK --restore-mark

# Step 2: for new flows (mark still 0), assign based on source
iptables -t mangle -A PREROUTING -m mark --mark 0 \
    -s 192.168.1.0/24 -j MARK --set-mark 0x1
iptables -t mangle -A PREROUTING -m mark --mark 0 \
    -s 192.168.2.0/24 -j MARK --set-mark 0x2

# Step 3 (mangle POSTROUTING): save packet mark → connmark
iptables -t mangle -A POSTROUTING \
    -m mark ! --mark 0 -j CONNMARK --save-mark
```

```nftables
# nftables equivalent
table ip pbr {
    chain prerouting {
        type filter hook prerouting priority mangle;
        ct mark != 0  meta mark set ct mark        # restore saved mark
        meta mark 0  ip saddr 192.168.1.0/24  meta mark set 0x1
        meta mark 0  ip saddr 192.168.2.0/24  meta mark set 0x2
    }
    chain postrouting {
        type filter hook postrouting priority mangle;
        meta mark != 0  ct mark set meta mark      # save mark to conntrack
    }
}
```

---

## Connection Limiting (connlimit)

`connlimit` counts **active conntrack entries** matching a given key and limits how many simultaneous connections a single host (or subnet) can hold open.

```bash
# At most 20 concurrent HTTP connections per source IP
iptables -A INPUT -p tcp --dport 80 \
    -m connlimit --connlimit-above 20 --connlimit-mask 32 \
    -j REJECT --reject-with tcp-reset

# At most 5 concurrent SSH connections per /24 subnet
iptables -A INPUT -p tcp --dport 22 \
    -m connlimit --connlimit-above 5 --connlimit-mask 24 \
    -j DROP

# Total concurrency cap across all sources (mask 0 = all IPs combined)
iptables -A INPUT -p tcp --dport 3306 \
    -m connlimit --connlimit-above 200 --connlimit-mask 0 \
    -j DROP
```

```nftables
table inet climit {
    chain input {
        type filter hook input priority filter;
        tcp dport 80 ct state new \
            meter http_conns { ip saddr ct count over 20 } \
            reject with tcp reset
    }
}
```

|Option|Description|
|---|---|
|`--connlimit-above N`|Match if concurrent count **exceeds** N|
|`--connlimit-upto N`|Match if concurrent count is **at or below** N|
|`--connlimit-mask BITS`|Group IPs: `32`/`128` = per-host; `24` = per /24; `0` = all IPs combined|
|`--connlimit-saddr`|Count by source address (default)|
|`--connlimit-daddr`|Count by destination address|

> [!note] `connlimit` queries the conntrack table. If `CT --notrack` is applied to the traffic, connlimit sees zero entries and never triggers.

---

## Per-Source Rate Limiting (hashlimit)

`hashlimit` maintains a **separate token bucket per key** (source IP, destination IP, port, or combinations) rather than a single global bucket like `limit`.

```bash
# Allow at most 10 new SSH connections per source IP per minute
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m hashlimit \
    --hashlimit-name ssh_rate \
    --hashlimit-above 10/minute \
    --hashlimit-burst 5 \
    --hashlimit-mode srcip \
    -j DROP
```

|Parameter|Description|
|---|---|
|`--hashlimit-above RATE`|Drop if rate **exceeds** this value|
|`--hashlimit-upto RATE`|Accept if rate is **at or below** this value|
|`--hashlimit-burst N`|Initial token bucket depth (burst allowance)|
|`--hashlimit-mode MODES`|`srcip`, `dstip`, `srcport`, `dstport`, or combinations|
|`--hashlimit-name NAME`|Name for the internal hash table (required)|
|`--hashlimit-htable-expire MS`|Idle entry expiry in milliseconds|

---

## Dynamic Blocking with nftables Sets

nftables `dynamic` sets allow the **packet path itself** to add entries, enabling automatic blocking without daemons or log parsing.

```nftables
table inet auto_block {

    # Blocked IPs auto-expire after 5 minutes
    set abusers {
        type ipv4_addr
        flags dynamic, timeout
        timeout 5m
    }

    chain input {
        type filter hook input priority filter; policy accept;

        # Step 1: drop IPs already in the abuser set
        ip saddr @abusers drop

        # Step 2: if an IP exceeds 100 SYNs/second, add it and drop
        tcp flags syn ct state new \
            add @abusers { ip saddr limit rate over 100/second } \
            drop
    }
}
```

> [!note] Rule ordering The check against `@abusers` (step 1) must come **before** the `add` statement (step 2). Once an IP is in the set, its subsequent SYN packets hit step 1 and are dropped without reaching the rate limiter.

---

## The recent Module

`recent` maintains a **kernel-side list of recently seen IP addresses** with timestamps. It is the building block for connection rate limiting and port knocking.

```bash
# Rate-limit SSH: drop source IPs seen >= 4 times in 60 s
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --name SSH --rcheck --seconds 60 --hitcount 4 -j DROP
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --name SSH --set -j ACCEPT
```

|Option|Description|
|---|---|
|`--set`|Add source IP to the named list (sets / updates timestamp)|
|`--rcheck`|Test if IP is in the list; do **not** update timestamp|
|`--update`|Test if IP is in the list; **update** timestamp if found|
|`--remove`|Remove source IP from the list|
|`--seconds N`|Only match entries seen within the last N seconds|
|`--hitcount N`|Only match if the IP has been seen N or more times|
|`--name NAME`|Named list identifier|

Lists are accessible at `/proc/net/xt_recent/`:

```bash
echo +192.0.2.1 > /proc/net/xt_recent/SSH   # manually add
echo -192.0.2.1 > /proc/net/xt_recent/SSH   # manually remove
```

---

## Port Knocking

Port knocking keeps a service completely firewalled until a client sends a **secret sequence of connection attempts** on specific ports in the correct order within a time window.

### Three-Port Knock with `recent`

```bash
# Stage 1: anyone hitting port 1234 is added to the KNOCK1 list → drop
iptables -A INPUT -p tcp --dport 1234 \
    -m recent --name KNOCK1 --set -j DROP

# Stage 2: hitting port 5678 within 5 s of stage 1 advances to KNOCK2 → drop
# (--rcheck tests KNOCK1 without updating its timestamp; --set adds to KNOCK2)
iptables -A INPUT -p tcp --dport 5678 \
    -m recent --name KNOCK1 --rcheck --seconds 5 \
    -m recent --name KNOCK2 --set \
    -j DROP

# Stage 3: hitting port 9012 within 5 s of stage 2 advances to KNOCK3 → drop
iptables -A INPUT -p tcp --dport 9012 \
    -m recent --name KNOCK2 --rcheck --seconds 5 \
    -m recent --name KNOCK3 --set \
    -j DROP

# SSH: open for 30 s after completing the full sequence
iptables -A INPUT -p tcp --dport 22 \
    -m recent --name KNOCK3 --rcheck --seconds 30 \
    -j ACCEPT
```

```bash
# Client sends the sequence (connection attempts, not full connections)
nmap -Pn --host-timeout 201ms --max-retries 0 -p 1234 TARGET
nmap -Pn --host-timeout 201ms --max-retries 0 -p 5678 TARGET
nmap -Pn --host-timeout 201ms --max-retries 0 -p 9012 TARGET
ssh user@TARGET
```

> [!warning] Port knocking provides security through obscurity. The sequence can be captured by a network observer. For production environments, use **Single Packet Authorization (SPA)** — e.g., `fwknop` — which uses a cryptographically authenticated single packet rather than an observable sequence.

---

## GeoIP and Country-Based Filtering

Country-based filtering loads **pre-built IP prefix lists** into kernel data structures for raw-address matching. No DNS lookups; no per-packet overhead beyond the set lookup.

### With ipset (iptables)

```bash
# Download country zone file (ipdeny.com aggregated lists)
curl -o /tmp/cn.zone https://www.ipdeny.com/ipblocks/data/aggregated/cn-aggregated.zone

# Load into ipset
ipset create GEOBLOCK_CN hash:net maxelem 65536
while IFS= read -r net; do
    ipset add GEOBLOCK_CN "$net" 2>/dev/null
done < /tmp/cn.zone

# Apply rules
iptables -I INPUT   -m set --match-set GEOBLOCK_CN src -j DROP
iptables -I FORWARD -m set --match-set GEOBLOCK_CN src -j DROP

# Persist
ipset save > /etc/ipset-geoblock.conf
# Restore on boot: ipset restore < /etc/ipset-geoblock.conf
```

### With nftables Native Sets

Generate `/etc/nftables/cn_v4.nft`:

```bash
{
  echo "set CN_v4 { type ipv4_addr; flags interval; elements = {"
  awk '{printf "  %s,\n", $1}' /tmp/cn.zone
  echo "} }"
} > /etc/nftables/cn_v4.nft
```

```nftables
# /etc/nftables.conf
include "/etc/nftables/cn_v4.nft"

table inet geoblock {
    chain prerouting {
        type filter hook prerouting priority raw;
        ip saddr @CN_v4 drop
    }
}
```

> [!warning] GeoIP accuracy IP geolocation is approximately 95–99% accurate at the country level. Mobile carriers, VPNs, CDNs, and cloud providers frequently use IPs attributed to unexpected countries. Refresh databases weekly and never rely on GeoIP as a sole security control.

---

## String and Payload Matching

### xt_string Match

`xt_string` scans the **L4 payload** for a literal string or hex sequence. Useful for known-bad payload signatures, specific User-Agent strings, or protocol identifiers.

```bash
# Block HTTP requests from a specific bad bot
iptables -A FORWARD -p tcp --dport 80 \
    -m string --string "BadBot/1.0" --algo bm \
    -j DROP

# Block DNS queries for a specific domain
iptables -A INPUT -p udp --dport 53 \
    -m string --string "malware.example.com" --algo kmp \
    -j DROP

# Match binary content (two consecutive CRLF = end of HTTP headers)
iptables -A FORWARD \
    -m string --hex-string "|0d0a0d0a|" --algo bm \
    -j LOG --log-prefix "HTTP_HDR_END: "
```

|Option|Description|
|---|---|
|`--string STRING`|Literal string to match|
|`--hex-string HEX`|Binary string in hex notation (e.g. `\|deadbeef\|`)|
|`--algo bm\|kmp`|Boyer-Moore (faster for long patterns) or Knuth-Morris-Pratt|
|`--from OFFSET`|Start scanning at this byte offset from L4 header start|
|`--to OFFSET`|Stop scanning at this byte offset|
|`--icase`|Case-insensitive matching|

> [!warning] Limitations
> 
> - Only effective on **unencrypted** traffic. TLS, QUIC, SSH, and WireGuard payloads are opaque.
> - Carries significant CPU overhead on high-throughput links — combine with narrow port/protocol matches.
> - For encrypted traffic inspection, use NFQUEUE + userspace with TLS decryption.

### u32 Match — Raw Packet Inspection

`u32` provides arbitrary 32-bit-aligned raw packet byte extraction and comparison:

```bash
# Match IPv4 packets with the Don't Fragment bit set (bit 14 at byte offset 6)
iptables -A INPUT -m u32 --u32 "6 & 0x4000 = 0x4000" \
    -j LOG --log-prefix "DF_SET: "
```

`u32` is powerful but error-prone. In nftables, use the `@base,offset,length` raw payload syntax instead:

```nftables
# Match DF bit (bit offset 48 from IP header start, length 1 bit)
@ih,48,1 == 1 log prefix "DF_SET: "
```

---

## OSF — Passive OS Fingerprinting

The `xt_osf` module identifies a remote host's OS by inspecting TCP SYN header fields: window size, TTL, MSS, window scaling, SACK, and timestamp options. Entirely passive — no probes are sent.

```bash
# Load module and fingerprint database
modprobe xt_osf
# Install fingerprint database (xtables-addons package provides pf.os)
nfnl_osf -f /usr/share/xtables-addons/pf.os

# Log detected OS for incoming SYN packets
iptables -A INPUT -p tcp --syn \
    -m osf --genre Linux --ttl 0 \
    -j LOG --log-prefix "OS_LINUX: "

# Drop traffic claiming to be from Windows on a Linux-only API port
iptables -A INPUT -p tcp --dport 8443 \
    -m osf --genre "Windows" --ttl 0 \
    -j DROP
```

|`--ttl` mode|Behavior|
|---|---|
|`0`|Do not check TTL (recommended for NAT environments)|
|`1`|Allow TTL to be within ±5 of the expected value|
|`2`|TTL must match exactly|

> [!warning] OSF accuracy is 70–85% in production. NAT, VPNs, and proxies alter TTLs; OS fingerprints evolve faster than databases are updated. Use for logging and soft classification, not hard security enforcement.

---

## The security Table — SELinux and AppArmor

The `security` table (priority `50`, after `filter`) is reserved for Mandatory Access Control frameworks. It provides hooks where SELinux and AppArmor can label packets with security contexts and enforce policy at the socket layer.

### SECMARK Target

`SECMARK` sets a security context label on a packet (`skb->secmark`):

```bash
iptables -t security -A INPUT -p tcp --dport 22 \
    -j SECMARK --selctx "system_u:object_r:ssh_packet_t:s0"
```

### CONNSECMARK Target

`CONNSECMARK` saves the packet's security label into the conntrack entry and restores it on subsequent packets, avoiding re-labelling on every packet of an established flow:

```bash
# On NEW connections: set label and save to conntrack entry
iptables -t security -A INPUT -m conntrack --ctstate NEW \
    -j SECMARK --selctx "system_u:object_r:http_packet_t:s0"
iptables -t security -A INPUT -m conntrack --ctstate NEW \
    -j CONNSECMARK --save

# On ESTABLISHED/RELATED: restore saved label
iptables -t security -A INPUT \
    -m conntrack --ctstate ESTABLISHED,RELATED \
    -j CONNSECMARK --restore
```

When `skb->secmark` is set, SELinux checks whether the receiving/sending process has `recv_msg` / `send_msg` permission for the packet's security type. Denials appear in the audit log:

```bash
ausearch -m avc -ts recent | grep packet
# avc: denied { recv_msg } for scontext=... tclass=packet
```

---

## nfacct — Kernel Accounting Objects

`nfacct` provides **named, kernel-resident byte/packet counters** independent of any specific firewall rule. Multiple rules across different tables, chains, or namespaces can increment the same counter — useful for billing, quota monitoring, and traffic analytics.

```bash
# Create counters
nfacct add http_traffic
nfacct add dns_traffic

# List / read / reset
nfacct list
nfacct get   http_traffic    # { pkts = 142034, bytes = 98304512 }
nfacct flush http_traffic    # read and atomically reset

# Delete
nfacct del http_traffic
```

### Using nfacct in iptables

The `nfacct` match is **non-terminating** — it increments the counter and rule evaluation continues:

```bash
# Count all HTTP traffic in both directions
iptables -A FORWARD -p tcp --dport 80 -m nfacct --nfacct-name http_traffic
iptables -A FORWARD -p tcp --sport 80 -m nfacct --nfacct-name http_traffic
iptables -A FORWARD -p udp --dport 53 -m nfacct --nfacct-name dns_traffic
```

### Using nfacct in nftables

```nftables
table inet accounting {
    counter http_traffic { }
    counter dns_traffic  { }

    chain forward {
        type filter hook forward priority filter;
        tcp dport { 80, 443 } counter name "http_traffic"
        tcp sport { 80, 443 } counter name "http_traffic"
        udp dport 53          counter name "dns_traffic"
    }
}
```

> [!note] nftables has built-in `counter` objects simpler than nfacct for most cases. Use `nfacct` when you need counters shared between iptables and nftables rules, or when you need the atomic read-and-reset of `nfacct flush`.

---

## Fail2ban Integration

Fail2ban parses **log files** for abuse patterns and dynamically inserts firewall rules to block offending IPs.

### How Fail2ban Uses Netfilter

For each enabled jail, fail2ban creates a dedicated iptables chain and inserts a jump into INPUT:

```
filter::INPUT
  └── -j f2b-sshd

f2b-sshd chain:
  -s 1.2.3.4 -j REJECT    ← inserted per banned IP
  -s 5.6.7.8 -j REJECT
  ...
  -j RETURN                ← unmatched traffic continues through INPUT
```

```bash
fail2ban-client status sshd          # view active bans
iptables -L f2b-sshd -n -v           # view the iptables chain
fail2ban-client set sshd unbanip 1.2.3.4
```

### Fail2ban with nftables

Configure via `/etc/fail2ban/jail.local` (fail2ban ≥ 0.11):

```ini
[DEFAULT]
banaction          = nftables-multiport
banaction_allports = nftables-allports

[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 5
bantime  = 3600
findtime = 600
```

With the nftables backend, fail2ban uses a named set with per-element timeouts:

```bash
nft list set inet f2b-table f2b-set-sshd
nft add element inet f2b-table f2b-set-sshd { 1.2.3.4 timeout 1h }
```

> [!tip] Fail2ban vs kernel-native rate limiting Fail2ban reacts in **seconds** (log write → inotify → parse → ban). nftables dynamic sets react in **microseconds** (packet path → kernel set insert). Prefer dynamic sets for connection-rate-based blocking. Use fail2ban for **application-layer** patterns that appear only in log files (wrong passwords, 404 storms, etc.).

---

## DSCP Marking

DSCP (Differentiated Services Code Point) is a 6-bit field in the IP ToS byte. It is preserved end-to-end across DiffServ-capable routers, enabling network-wide QoS without per-flow state.

```bash
# iptables: mark VoIP RTP as Expedited Forwarding (EF)
iptables -t mangle -A POSTROUTING \
    -p udp --dport 16384:32767 -j DSCP --set-dscp-class EF

# Mark SSH as CS2
iptables -t mangle -A POSTROUTING \
    -p tcp --dport 22 -j DSCP --set-dscp-class CS2
```

```nftables
table ip qos {
    chain postrouting {
        type filter hook postrouting priority mangle;
        udp dport 16384-32767  ip dscp set ef
        tcp dport 22           ip dscp set cs2
        tcp dport { 8000, 9418 } ip dscp set cs0
    }
}
```

|Class|DSCP hex|Use case|
|---|---|---|
|`EF`|`0x2e`|VoIP, real-time interactive|
|`AF41`|`0x22`|Video conferencing|
|`AF31`|`0x1a`|Streaming media|
|`AF21`|`0x12`|Transactional data|
|`CS2`|`0x10`|Network operations (SSH, SNMP)|
|`CS0` / `BE`|`0x00`|Best effort (default)|

---

## Integration with tc (Traffic Control)

The most common pattern: **Netfilter marks packets** in `mangle POSTROUTING`; **tc** classifies them by reading the mark via the `fw` filter.

```bash
# Mark traffic categories
iptables -t mangle -A POSTROUTING -p udp --dport 16384:32767 -j MARK --set-mark 0x10
iptables -t mangle -A POSTROUTING -p tcp --dport 22000       -j MARK --set-mark 0x20

# Attach HTB qdisc to eth0 (100 Mbps ceiling)
tc qdisc add dev eth0 root handle 1: htb default 30
tc class add dev eth0 parent 1:  classid 1:1  htb rate 100mbit

# Class 1:10 — VoIP: 20 Mbps guaranteed, burst to 100 Mbps
tc class add dev eth0 parent 1:1 classid 1:10 htb rate 20mbit ceil 100mbit prio 1

# Class 1:20 — Bulk: 5 Mbps guaranteed
tc class add dev eth0 parent 1:1 classid 1:20 htb rate 5mbit  ceil 50mbit  prio 3

# Class 1:30 — Default / best effort
tc class add dev eth0 parent 1:1 classid 1:30 htb rate 5mbit  ceil 100mbit prio 5

# Steer marked packets into HTB classes via fw filter
tc filter add dev eth0 parent 1: protocol ip handle 0x10 fw classid 1:10
tc filter add dev eth0 parent 1: protocol ip handle 0x20 fw classid 1:20
```

> [!note] `tc fw` reads `skb->mark` — the same value Netfilter's `MARK` target writes. For DSCP-based tc classification, use `tc filter ... u32 match ip dscp VALUE 0xfc` instead of `fw`.

---

## Hook Overhead and Optimization

### Traversal Cost

- A hook with zero registered callbacks incurs only a small dispatch check.
- Each registered callback adds function-call overhead plus whatever the callback computes.
- A linear chain of 1000 iptables rules = up to 1000 comparisons per packet.

### Optimization Techniques

**1. Use sets for large address lists** — O(1) vs O(n):

```bash
# Slow: 10,000 individual rules
for ip in $(cat blocklist.txt); do iptables -A INPUT -s "$ip" -j DROP; done

# Fast: one rule + hash set
ipset create BLOCKLIST hash:ip
while IFS= read -r ip; do ipset add BLOCKLIST "$ip"; done < blocklist.txt
iptables -A INPUT -m set --match-set BLOCKLIST src -j DROP
```

**2. Place high-frequency matches first** — ESTABLISHED covers the vast majority of packets:

```bash
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT  # first
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```

**3. NOTRACK for high-rate stateless traffic** — bypass conntrack for DNS, syslog, metrics. See [[Netfilter Conntrack — Connection Tracking#NOTRACK and CT Bypass]].

**4. Enable flowtable offloading** — see [[#nftables Flowtables]] and [[Netfilter Conntrack — Connection Tracking#Flowtable and Hardware Offload]].

**5. Prefer nftables for large rule sets** — the bytecode VM and native sets avoid iptables' O(n) linear scan and per-table write-lock contention.

**6. Use netdev ingress for very early drops** — fires before conntrack, before routing:

```nftables
table netdev early_drop {
    chain ingress {
        type filter hook ingress device eth0 priority -500;
        ip saddr @ddos_sources counter drop
    }
}
```

---

## eBPF and XDP Integration

eBPF and Netfilter coexist at different kernel layers:

||XDP (eBPF)|TC eBPF|Netfilter|
|---|---|---|---|
|Fires|Before `sk_buff` allocation|After skb alloc, before Netfilter|After skb alloc|
|Performance|Extreme (NIC driver level)|Very high|Good|
|Stateful tracking|Custom via eBPF maps|Custom via eBPF maps|Built-in conntrack|
|NAT|Custom only|Custom only|Built-in|

```
NIC RX interrupt
  │
  ▼  XDP hook (eBPF) — XDP_DROP for line-rate DDoS mitigation
  │
  ▼  sk_buff allocated
  │
  ▼  TC ingress (cls_bpf / cls_flower)
  │
  ▼  NF_INET_PRE_ROUTING  ← Netfilter begins here
```

**XDP verdicts:**

|Verdict|Effect|
|---|---|
|`XDP_DROP`|Drop before skb allocation — lowest CPU cost|
|`XDP_PASS`|Continue to normal network stack|
|`XDP_TX`|Retransmit on same NIC (hairpin)|
|`XDP_REDIRECT`|Redirect to another NIC or CPU queue|

**TC ↔ Netfilter via packet marks:**

```bash
# TC marks a packet
tc filter add dev eth0 ingress ... action skbedit mark 0x100
# Netfilter matches it
iptables -A INPUT -m mark --mark 0x100 -j ACCEPT
```

Cilium (eBPF-based CNI) implements its own conntrack in eBPF, bypassing Netfilter for Pod-to-Pod traffic. `conntrack -L` on a Cilium node will not show eBPF-tracked flows.

---

## nf_tables Bytecode Virtual Machine

The nftables kernel engine compiles rules to **bytecode** at configuration time and evaluates it in a tight loop at packet time — no textual parsing, no per-rule function dispatch.

### VM Registers

- **16 × 32-bit data registers** (`NFT_REG32_00` … `NFT_REG32_15`) — hold intermediate values (IPs, ports, computed results). Consecutive registers hold wider values (IPv6 addresses, 128-bit labels).
- **1 verdict register** — holds the current verdict (`NF_ACCEPT`, `NF_DROP`, jump target, …).

### Expression Types (VM Opcodes)

|Expression|Operation|
|---|---|
|`payload`|Read packet bytes into a register (IP src addr, TCP dport, …)|
|`cmp`|Compare register to a constant; update verdict on mismatch|
|`lookup`|Check register against a set; hit/miss updates verdict|
|`immediate`|Load a constant into a register or set the verdict|
|`bitwise`|AND / OR / XOR / shift on a register|
|`byteorder`|Convert byte order (network ↔ host)|
|`meta`|Read packet metadata (iif, oif, mark, l4proto, …)|
|`ct`|Read conntrack fields|
|`counter`|Increment a named counter|
|`log`|Emit a log message|
|`nat`|Apply address translation|
|`limit`|Token-bucket rate check|
|`dynset`|Add / update / delete a dynamic set element|

### Example: `tcp dport 80 accept` Compilation

```
1. meta l4proto → reg[0]         # load L4 protocol number
2. cmp reg[0] == 6               # is it TCP? else: next rule
3. payload (TCP, dport) → reg[0] # load destination port
4. cmp reg[0] == 80              # is it port 80? else: next rule
5. immediate → verdict = NF_ACCEPT
```

### Performance

- Bytecode evaluates in a cache-friendly tight loop (`nft_do_chain`).
- Set lookups are **O(1)** for hash types; O(log n) for interval/rbtree types.
- JIT compilation (`CONFIG_NF_TABLES_JIT`, x86-64) compiles bytecode to native machine code for an additional ~20–40% speedup.

```bash
sysctl net.core.bpf_jit_enable   # 1 = enabled (shared with eBPF JIT)
```

---

## x_tables Infrastructure (Legacy)

`x_tables` is the shared kernel infrastructure underlying all legacy tools: `iptables`, `ip6tables`, `arptables`, and `ebtables`. It provides match extension modules (`xt_conntrack.ko`, `xt_multiport.ko`, …) and target extension modules (`xt_MARK.ko`, `xt_LOG.ko`, …).

### Rule Evaluation Model

Legacy iptables stores rules in a flat in-kernel blob and evaluates them linearly:

```
[ rule 1: match list + target ]
[ rule 2: match list + target ]
...
[ policy (default verdict)    ]
```

For each packet: walk the array; if all matches pass → invoke target; if terminating → stop; otherwise continue. User chain jumps are recursive; non-terminating targets continue after return.

### Why nftables Supersedes x_tables

|Dimension|x_tables (iptables)|nf_tables (nftables)|
|---|---|---|
|Rule evaluation|Linear scan — O(n)|Bytecode VM — O(1) for set lookups|
|Multiple protocols|4 separate binaries|Single `nft` for all families|
|Atomic updates|Full blob replace with lock|Netlink transactions|
|Large address lists|External `ipset` required|Native sets, built-in|
|Runtime update|Full rule reload|`nft add/delete element`|
|Kernel interface|`setsockopt` (opaque blob)|Structured Netlink messages|

> [!note] Coexistence `iptables-nft` translates iptables syntax into nftables bytecode. Both `nft` and `iptables-nft` rules appear together in `nft list ruleset`. `iptables-legacy` keeps a completely separate ruleset visible only via `iptables-legacy -L`.

---

## Netfilter Module Reference

### Loading and Inspection

```bash
modprobe nf_conntrack
modprobe nf_nat
modprobe nf_tables

lsmod | grep -E 'nf_|iptable|ip_tables|nft|x_tables|br_netfilter'
modinfo nf_nat | grep depends
```

### Module Auto-loading

|Action|Modules auto-loaded|
|---|---|
|`iptables -A INPUT ...`|`ip_tables`, `iptable_filter`|
|`iptables -t nat ...`|`iptable_nat`, `nf_nat`, `nf_conntrack`|
|`nft add table ...`|`nf_tables`|
|First conntrack rule|`nf_conntrack`, `nf_defrag_ipv4`, `nf_defrag_ipv6`|
|`br_netfilter`|**Manual only** — never auto-loaded|

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
|`nft_compat`|`iptables-nft`|iptables-over-nftables compatibility|
|`ip_tables`|`iptables`|Legacy iptables core (IPv4)|
|`ip6_tables`|`ip6tables`|Legacy ip6tables core (IPv6)|
|`iptable_filter`|`iptables`|`filter` table|
|`iptable_nat`|`iptables -t nat`|`nat` table|
|`iptable_mangle`|`iptables -t mangle`|`mangle` table|
|`iptable_raw`|`iptables -t raw`|`raw` table|
|`nf_conntrack`|First stateful rule|Connection tracking core|
|`nf_conntrack_ipv4`|`nf_conntrack`|IPv4 L4 protocol trackers|
|`nf_conntrack_ipv6`|`nf_conntrack`|IPv6 L4 protocol trackers|
|`nf_nat`|First NAT rule|NAT core — IPv4 + IPv6 since kernel 5.1|
|`nf_defrag_ipv4`|`nf_conntrack`|IPv4 fragment reassembly|
|`nf_defrag_ipv6`|`nf_conntrack`|IPv6 fragment reassembly|
|`nfnetlink`|`nf_tables`, queue, log|Netlink transport for Netfilter|
|`nfnetlink_queue`|NFQUEUE rules|NFQUEUE subsystem|
|`nfnetlink_log`|NFLOG rules|NFLOG subsystem|
|`ip_set`|`ipset` commands|ipset core|
|`ip_set_hash_ip`|`ipset create ... hash:ip`|hash:ip type|
|`ip_set_hash_net`|`ipset create ... hash:net`|hash:net type|
|`br_netfilter`|Manual only|Bridge + Netfilter IPv4/IPv6 integration|
|`nf_flow_table`|nftables flowtable rules|Software flowtable fast path|
|`nf_flow_table_hw`|`flags offload` in flowtable|NIC hardware offload extension|
|`xt_osf`|`-m osf`|Passive OS fingerprinting|
|`nf_conntrack_ftp`|Manual|FTP ALG helper|
|`nf_conntrack_sip`|Manual|SIP/VoIP ALG helper|
|`nf_conntrack_proto_gre`|Manual|GRE conntrack support|
|`nf_conntrack_proto_sctp`|Manual|SCTP conntrack support|

---

## Debugging Netfilter

### TRACE Target (iptables)

`TRACE` logs a packet as it hits each table / chain / rule:

```bash
# Trace only new TCP SYN packets to port 22 to limit volume
iptables -t raw -A PREROUTING -p tcp --dport 22 --syn -j TRACE

dmesg | grep TRACE
# TRACE: raw:PREROUTING:policy:1 IN=eth0 SRC=1.2.3.4 DST=10.0.0.1 SYN
# TRACE: mangle:PREROUTING:policy:1
# TRACE: nat:PREROUTING:rule:1
# TRACE: filter:INPUT:rule:2

# Remove when done
iptables -t raw -D PREROUTING -p tcp --dport 22 --syn -j TRACE
```

> [!warning] `TRACE` produces extremely high log volume on any moderately busy system. Always use very specific match criteria and remove the rule immediately after debugging.

### nftables Tracing

```nftables
# Enable tracing for matching packets
table inet debug {
    chain prerouting {
        type filter hook prerouting priority raw;
        tcp dport 22 meta nftrace set 1
    }
}
```

```bash
# Monitor trace events in real time
nft monitor trace
# trace id a1b2c3d4 inet filter input packet: iif "eth0" ip saddr 1.2.3.4 ...
# trace id a1b2c3d4 inet filter input rule tcp dport 22 accept (verdict accept)

# Disable: set nftrace to 0 in the rule, or delete the rule
```

### Counting Drops by Chain

```bash
# List all rules with packet / byte counters
iptables -L -v -n

# Watch counters update in real time
watch -n1 'iptables -L -v -n'

# Zero all counters
iptables -Z

# nftables: rules with counter statements show counts inline
nft list ruleset | grep -E 'packets|bytes'
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

# Complete nftables ruleset (includes iptables-nft rules)
nft list ruleset

# Determine which iptables backend is in use
iptables --version
# "iptables v1.8.x (nf_tables)"  → iptables-nft
# "iptables v1.8.x (legacy)"     → iptables-legacy
```

---

## Testing and Validating Firewall Rules

### hping3 — Crafted Packet Testing

```bash
# Test TCP port 22 (SYN → expects SYN+ACK if open)
hping3 -S -p 22 -c 3 TARGET

# Test a filtered port (expects no response / timeout)
hping3 -S -p 23 -c 3 TARGET

# UDP test
hping3 -2 -p 53 -c 3 TARGET

# Send fragmented packets (test fragment handling rules)
hping3 -S -p 80 --mtu 64 TARGET

# Verify SYN flood / rate limiting rules (lab only)
hping3 -S -p 80 --flood TARGET
```

### nmap — Port and State Scanning

```bash
# SYN scan (half-open; requires root)
nmap -sS -p 22,80,443 TARGET

# Connect scan (no root needed; full handshake)
nmap -sT -p 1-65535 TARGET

# UDP scan
nmap -sU -p 53,123,161 TARGET

# OS detection + version + all ports
nmap -sS -sV -O -p- TARGET
```

### Scapy — Scriptable Packet Crafting

```python
from scapy.all import *

# Christmas tree packet (FIN+PSH+URG) — should be INVALID in conntrack
ans = sr1(IP(dst="TARGET") / TCP(dport=22, flags="FPU"), timeout=2)
print(ans.summary() if ans else "No response (INVALID drop)")

# Verify INVALID drop: ACK with no prior connection
ans = sr1(IP(dst="TARGET") / TCP(dport=22, flags="A", seq=99999, ack=99999), timeout=2)
print(ans.summary() if ans else "Dropped — correct INVALID behavior")

# Fragmented packet
send(fragment(IP(dst="TARGET") / TCP(dport=80) / ("X" * 1000)))
```

### Validating nftables Configuration Files

```bash
# Syntax check without applying
nft --check --file /etc/nftables.conf

# Safe atomic replacement with automatic rollback
# On the server: apply new rules, schedule revert in 60 s
nft --file /etc/nftables.new
sleep 60 && nft --file /etc/nftables.conf &
ROLLBACK_PID=$!

# From another terminal: verify connectivity
ssh user@server "echo still connected"

# If everything works, cancel the rollback
kill $ROLLBACK_PID && echo "Rules confirmed"
```

### Capturing Netfilter-Dropped Packets

```bash
# Method 1: LOG target before the DROP rule
iptables -I INPUT -j LOG --log-prefix "PRECHECK: " --log-level 6
iptables -A INPUT -j DROP
dmesg | grep PRECHECK

# Method 2: nftables log + journal
# In rules: log prefix "DROP: " level debug drop
journalctl -k -f | grep "DROP:"

# Method 3: tc mirror — copy all traffic to loopback before Netfilter
tc qdisc add dev eth0 ingress
tc filter add dev eth0 ingress protocol all u32 match u32 0 0 \
    action mirred egress mirror dev lo
tcpdump -i lo -w /tmp/mirrored.pcap

# Method 4: xdpdump — capture at XDP layer, before Netfilter
xdpdump -i eth0 --rx-capture entry -w /tmp/xdp.pcap
```

---

## Common Issues

### Rules Not Matching — Wrong iptables Backend

**Symptom:** `iptables -L` shows a rule but traffic passes anyway.

**Cause:** System uses `iptables-nft` while the rule was added with `iptables-legacy` (or vice versa). Each backend has an independent ruleset.

```bash
iptables-legacy -L    # rules via setsockopt
iptables-nft    -L    # rules via nftables kernel subsystem
nft list ruleset      # all nftables rules including iptables-nft
```

**Solution:** Choose one backend and migrate all rules to it.

---

### Bridged Traffic Not Filtered

**Symptom:** iptables/nftables rules have no effect on traffic between two VMs on the same bridge.

**Cause:** Bridged L2 traffic bypasses IPv4/IPv6 hooks without `br_netfilter`.

```bash
modprobe br_netfilter
sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1
```

---

### NFQUEUE Drops When No Listener

**Symptom:** Traffic matched by `-j NFQUEUE` disappears when no userspace process is attached.

**Fix:** Add `--queue-bypass` to fall back to ACCEPT:

```bash
iptables -A INPUT -p tcp -j NFQUEUE --queue-num 0 --queue-bypass
```

---

### iptables Rules Lost After Reboot

```bash
# Debian / Ubuntu
apt install iptables-persistent
netfilter-persistent save
systemctl enable netfilter-persistent

# RHEL / CentOS / Fedora
dnf install iptables-services
service iptables save
systemctl enable iptables

# nftables: loaded from /etc/nftables.conf on boot
systemctl enable nftables
```

---

### NAT Not Working for Forwarded Traffic

```bash
sysctl net.ipv4.ip_forward          # must be 1
sysctl -w net.ipv4.ip_forward=1

iptables -A FORWARD -d 192.168.1.100 -p tcp --dport 80 \
    -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT

lsmod | grep nf_conntrack
iptables -t nat -L PREROUTING -n -v   # confirm DNAT rule is present
```

---

### nftables and iptables-nft Conflicts

**Symptom:** Unexpected filtering when both `nft` and `iptables-nft` are managing rules simultaneously.

```bash
nft list ruleset   # shows ALL active nftables rules — both nft and iptables-nft
```

**Solution:** Choose one tool and flush the other's rules:

```bash
iptables-nft -F; iptables-nft -X
iptables-nft -t nat    -F; iptables-nft -t nat    -X
iptables-nft -t mangle -F; iptables-nft -t mangle -X
iptables-nft -t raw    -F; iptables-nft -t raw    -X
```

---

## Comprehensive nftables Firewall Baseline

Production-ready stateful firewall for a **server** (IPv4 + IPv6, default-deny input):

```nftables
#!/usr/sbin/nft -f
# /etc/nftables.conf

flush ruleset

table inet filter {

    # -----------------------------------------------------------------------
    # Named sets — update at runtime without touching rules
    # -----------------------------------------------------------------------
    set trusted_mgmt {
        type ipv4_addr
        flags interval
        elements = { 10.0.0.0/8, 192.168.0.0/16 }
    }

    set blocked_sources {
        type ipv4_addr
        flags dynamic, timeout
        timeout 1h
    }

    # -----------------------------------------------------------------------
    # Raw: NOTRACK loopback — no conntrack overhead for local traffic
    # -----------------------------------------------------------------------
    chain raw_prerouting {
        type filter hook prerouting priority raw; policy accept;
        iif "lo" notrack
    }

    # -----------------------------------------------------------------------
    # Input
    # -----------------------------------------------------------------------
    chain input {
        type filter hook input priority filter; policy drop;

        iif "lo" accept

        # ESTABLISHED / RELATED first — covers the vast majority of packets
        ct state established,related accept

        # Drop INVALID before specific rules
        ct state invalid log prefix "NF_INVALID: " level warn counter drop

        # Dynamic block list (populated by the SYN-flood rule below)
        ip saddr @blocked_sources drop

        # ICMPv4 — allow essential types
        ip protocol icmp icmp type {
            echo-request, destination-unreachable,
            time-exceeded, parameter-problem
        } accept

        # ICMPv6 — required for NDP and PMTUD; never drop blanket
        ip6 nexthdr ipv6-icmp icmpv6 type {
            destination-unreachable, packet-too-big, time-exceeded,
            parameter-problem, echo-request, echo-reply,
            nd-router-solicit, nd-router-advert,
            nd-neighbor-solicit, nd-neighbor-advert,
            mld2-listener-report
        } accept

        # SYN flood protection: auto-block offenders for 1 h
        tcp flags syn ct state new \
            add @blocked_sources { ip saddr limit rate over 200/second } \
            log prefix "NF_SYNFLOOD: " level warn counter drop

        # SSH: restricted to trusted management sources
        tcp dport 22 ip saddr @trusted_mgmt ct state new accept

        # Public services
        tcp dport { 80, 443 } ct state new accept

        log prefix "NF_INPUT_DROP: " level info
        drop
    }

    # -----------------------------------------------------------------------
    # Forward (for gateway / container host role)
    # -----------------------------------------------------------------------
    chain forward {
        type filter hook forward priority filter; policy drop;

        ct state established,related accept
        ct state invalid drop
        iifname "eth1" oifname "eth0" ct state new accept

        log prefix "NF_FORWARD_DROP: " level info
        drop
    }

    # -----------------------------------------------------------------------
    # Output (permissive for servers)
    # -----------------------------------------------------------------------
    chain output {
        type filter hook output priority filter; policy accept;
        ct state invalid drop
    }
}

# -----------------------------------------------------------------------
# NAT (gateway role only)
# -----------------------------------------------------------------------
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat;
        oifname "eth0" masquerade
    }
}
```

---

## Comprehensive iptables Firewall Baseline

```bash
#!/bin/bash
# /etc/iptables/setup.sh

IPT="iptables"
IP6T="ip6tables"

# --- Flush and reset policies ---
for t in filter nat mangle raw; do
    $IPT  -t "$t" -F; $IPT  -t "$t" -X; $IPT  -t "$t" -Z
    $IP6T -t "$t" -F; $IP6T -t "$t" -X; $IP6T -t "$t" -Z 2>/dev/null
done

$IPT  -P INPUT DROP;    $IPT  -P FORWARD DROP;   $IPT  -P OUTPUT ACCEPT
$IP6T -P INPUT DROP;    $IP6T -P FORWARD DROP;   $IP6T -P OUTPUT ACCEPT

# --- Loopback ---
$IPT  -A INPUT -i lo -j ACCEPT
$IP6T -A INPUT -i lo -j ACCEPT

# --- ESTABLISHED / RELATED ---
$IPT  -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
$IP6T -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# --- INVALID ---
$IPT  -A INPUT -m conntrack --ctstate INVALID \
      -j LOG --log-prefix "NF_INVALID: " --log-level 4
$IPT  -A INPUT -m conntrack --ctstate INVALID -j DROP
$IP6T -A INPUT -m conntrack --ctstate INVALID -j DROP

# --- ICMPv4 ---
for type in echo-request destination-unreachable time-exceeded parameter-problem; do
    $IPT -A INPUT -p icmp --icmp-type "$type" -j ACCEPT
done

# --- ICMPv6 (required for NDP and PMTUD) ---
$IP6T -A INPUT -p ipv6-icmp -j ACCEPT

# --- SYN flood protection ---
$IPT -A INPUT -p tcp --syn -m conntrack --ctstate NEW \
     -m hashlimit \
     --hashlimit-name synflood \
     --hashlimit-above 200/second \
     --hashlimit-burst 500 \
     --hashlimit-mode srcip \
     -j LOG --log-prefix "NF_SYNFLOOD: " --log-level 4
$IPT -A INPUT -p tcp --syn -m conntrack --ctstate NEW \
     -m hashlimit \
     --hashlimit-name synflood \
     --hashlimit-above 200/second \
     --hashlimit-burst 500 \
     --hashlimit-mode srcip \
     -j DROP

# --- Public services ---
$IPT  -A INPUT -p tcp -m multiport --dports 80,443 \
      -m conntrack --ctstate NEW -j ACCEPT
$IP6T -A INPUT -p tcp -m multiport --dports 80,443 \
      -m conntrack --ctstate NEW -j ACCEPT

# --- SSH (trusted management subnets only) ---
$IPT  -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 \
      -m conntrack --ctstate NEW -j ACCEPT
$IPT  -A INPUT -p tcp --dport 22 -s 192.168.0.0/16 \
      -m conntrack --ctstate NEW -j ACCEPT
$IP6T -A INPUT -p tcp --dport 22 -s fe80::/10 \
      -m conntrack --ctstate NEW -j ACCEPT

# --- Log remaining INPUT ---
$IPT  -A INPUT -j LOG --log-prefix "NF_INPUT_DROP: "  --log-level 6
$IP6T -A INPUT -j LOG --log-prefix "NF_INPUT_DROP: "  --log-level 6

# --- FORWARD (gateway role) ---
$IPT  -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
$IPT  -A FORWARD -m conntrack --ctstate INVALID -j DROP
$IPT  -A FORWARD -i eth1 -o eth0 -m conntrack --ctstate NEW -j ACCEPT

# --- NAT (gateway role) ---
$IPT  -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

---

## Related Notes

- [[Netfilter Conntrack — Connection Tracking]]
- [[iptables Reference]]
- [[nftables Reference]]
- [[ebtables Reference]]
- [[Linux NAT Configuration]]
- [[Linux Network Performance Tuning]]
- [[Kubernetes Network Internals]]
- [[Linux Network Namespaces]]
- [[eBPF and Cilium Networking]]
- [[Linux TC and Traffic Control]]

---

_Sources: Linux kernel source (`net/netfilter/`, `include/linux/netfilter.h`), `man 8 iptables`, `man 8 iptables-extensions`, `man 8 nft`, `man 8 ipset`, `man 8 ebtables`, nftables wiki, kernel documentation (`Documentation/networking/netfilter.rst`), netfilter.org._