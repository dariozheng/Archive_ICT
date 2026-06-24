---
categories:
  - "[[Linux]]"
topic@linux:
tags:
  - tobecompleted
icon: SiLinux
iconColor: "#000000"
---

![[netfilter-packet-flow.png]]

The <strong>netfilter</strong> project is a community-driven collaborative FOSS project that provides <strong>packet filtering software</strong> for the Linux 2.4.x and later kernel series. The netfilter project is commonly associated with [[iptables]] and its successor [[nftables]].

The netfilter project provides a framework that enables packet filtering, network address and port translation (NAT), packet logging, connection tracking, userspace packet queueing and other [[security glossary#packet mangling|packet mangling]].

The netfilter framework provides a powerful mechanism for intercepting and manipulating network packets in the Linux kernel. This framework has 2 components to it – <strong>Netfilter hooks</strong> and <strong>conntrack</strong>.

The [[#netfilter hooks]] are a framework inside the Linux kernel that allows kernel modules to register callback functions at different locations of the Linux network stack. 
The registered callback function is then called back for every packet that traverses the respective hook within the Linux network stack.

[[iptables]] is a generic firewalling software that allows you to define rulesets. Each rule within an IP table consists of a number of classifiers (iptables matches) and one connected action (iptables target).

[[nftables]] is the successor of iptables, it allows for much more flexible, scalable and performance packet classification. This is where all the fancy new features are developed. 

## Main Features
- stateless packet filtering (IPv4 and IPv6)
- stateful packet filtering (IPv4 and IPv6)
- all kinds of network address and port translation, e.g. NAT/NAPT (IPv4 and IPv6)
- flexible and extensible infrastructure
- multiple layers of API's for 3rd party extensions
## What can I do with netfilter?
- build internet firewalls based on stateless and stateful packet filtering
- deploy highly available stateless and stateful firewall clusters
- use NAT and masquerading for sharing internet access if you don't have enough public IP addresses
- use NAT to implement transparent proxies
- aid the <strong>tc</strong> and <strong>iproute2</strong> systems used to build sophisticated QoS and policy routers
- do further packet manipulation (mangling) like altering the TOS/DSCP/ECN bits of the IP header
## What value does nftables provide?
- a single tool with consistent syntax as opposed to the fragmented {ip,ip6,eb,arp}tables and ipset
- faster kernel-side transactional ruleset updates, no need for user-space locking
- sets are more flexible and powerful than ipset, maps push the concept even further
- full ruleset flexibility:
    
    - no pre-defined tables and chains
    - arbitrary number of user-defined tables to separate the ruleset into "namespaces"
    - base chain's hook and priority are configurable
    
- more flexible rules: No mandatory parts (like counters), multiple actions allowed (e.g. log and drop)
- ingress hook attaching a chain to an interface for early filtering right after TC
- egress hook attaching a chain to an interface for transmit path filtering right before TC
- flowtables provide a software fast path and hardware acceleration
- some limited scripting ability embedded in the syntax (define variables, include other files), support for extensive scripting via JSON input and output
# Netfilter Hooks
There are five `netfilter` hooks that programs can register with. 

<mark style="background: #BBFABBA6;">As packets progress through the stack, they will trigger the kernel modules that have registered with these hooks</mark>. 

The hooks that a packet will trigger depends on whether the packet is incoming or outgoing, the packet’s destination, and whether the packet was dropped or rejected at a previous point.

<strong>Netfilter hooks</strong> allow the kernel modules to implement custom firewall rules, network address translation, packet filtering, logging, and more. 
Pre-defined functions that are performing tasks such as filtering and logging can be hot-plugged into the kernel, which makes them easier to use.

There are five predefined netfilter hook points:

## `NF_IP_PRE_ROUTING`
This hook will be triggered by <mark style="background: #FF5582A6;">any incoming traffic</mark> very soon after entering the network stack. This hook is processed before any routing decisions have been made regarding where to send the packet i.e. <mark style="background: #FFB8EBA6;">to check if this packet is destined for another interface</mark>, or <mark style="background: #FFB86CA6;">a local process</mark>. The routing code may drop packets that are unrouteable.

Port Address Translation (NAPT) and Redirections, that is, Destination Network Translation (DNAT), are implemented in this hook.

## `NF_IP_LOCAL_IN`
This hook is triggered <mark style="background: #FFB86CA6;">after an incoming packet has been routed</mark> <mark style="background: #FFF3A3A6;">if the packet is destined for the local system</mark>. This is the last hook in the incoming path for the local machine traffic.

## `NF_IP_FORWARD`
This hook is triggered <mark style="background: #BBFABBA6;">after an incoming packet has been routed</mark> <mark style="background: #ABF7F7A6;">if the packet is to be forwarded to another host</mark> (e.g., packets going through the firewall).

## `NF_IP_LOCAL_OUT`
This hook is triggered by <mark style="background: #ADCCFFA6;">any locally created outbound traffic</mark> <mark style="background: #FFB86CA6;">as soon as it hits the network stack</mark>.  This is the first hook in the outgoing packet path. Packets leaving the local machine always hit this hook.

## `NF_IP_POST_ROUTING`
This hook is triggered by <mark style="background: #FFB8EBA6;">any outgoing or forwarded traffic</mark> <mark style="background: #FF5582A6;">after routing has taken place and just before being sent out on the wire</mark>.
Source Network Address Translation (SNAT) is registered to this hook. 
All the packets that leave the local machine reach this hook.
#
Each hook point corresponds to a different stage of packet processing, as shown in the diagram below:

![[Pasted image 20260623101434.png]]

![[linux_netfilter_packet_flow.png]]

Therefore we can model three kind of traffic flows, depending on the destination:
- Traffic going through the firewall, in other words, traffic not going to the local machine. Such traffic follows the path: <mark style="background: #BBFABBA6;">PREROUTING</mark> <mark style="background: #ADCCFFA6;">FORWARD</mark> <mark style="background: #BBFABBA6;">POSTROUTING</mark>.
- Incoming traffic to the firewall, for example, traffic for the local machine. Such traffic follows the path: <mark style="background: #BBFABBA6;">PREROUTING</mark> <mark style="background: #D2B3FFA6;">INPUT</mark>.
- Outgoing traffic from the firewall: <mark style="background: #D2B3FFA6;">OUTPUT</mark> <mark style="background: #BBFABBA6;">POSTROUTING</mark>

When a packet arrives at or leaves a network interface, it passes through each of these hook points in order. 

<mark style="background: #D2B3FFA6;">At each hook point</mark>, the kernel calls <mark style="background: #ABF7F7A6;">all the registered netfilter hook functions</mark> for that hook point. <mark style="background: #FFB86CA6;">Each netfilter hook function</mark> <mark style="background: #BBFABBA6;">can inspect the packet</mark> and<mark style="background: #ADCCFFA6;"> decide what to do with it</mark>. The possible actions are:

- <strong>Accept</strong>: The packet is allowed to continue to the next hook point or the destination.
- <strong>Drop</strong>: The packet is silently discarded and no further processing is done.
- <strong>Queue</strong>: The packet is queued for userspace processing by a daemon such as iptables or nftables.
- <strong>Repeat</strong>: The packet is re-injected at the same hook point for another round of processing.
- <strong>Stolen</strong>:  Silently holds the packet until something happens, so that it temporarily does not continue to travel through the stack. This is usually used to collect defragmented IP packets.

Netfilter [[linux glossary#kernel modules|kernel modules]] <mark style="background: #ABF7F7A6;">that need to register at these hooks</mark> must also provide a <strong>priority number</strong> <mark style="background: #BBFABBA6;">to help determine the order in which the <strong>kernel modules</strong> will be called when the hook is triggered</mark>. 
<mark style="background: #ADCCFFA6;">This provides the means for multiple modules</mark> (or multiple instances of the same module) <mark style="background: #D2B3FFA6;">to be connected to each of the hooks (multiple modules can be connected to a single host) with deterministic ordering</mark>. 

<mark style="background: #ABF7F7A6;">Each module will be called in turn</mark> and <mark style="background: #ADCCFFA6;">will return a decision to the</mark> `netfilter` <strong>framework</strong> after <strong>a processing</strong> <mark style="background: #CACFD9A6;">that indicates what should be done with the packet</mark>.

# Netfilter APIs

The prototype of the callback function is defined in the structure <strong>nf_hook_ops</strong> in <strong>netfilter.h</strong>. This structure contains the information about the hook to which the callback will be registered, together with the priority. 

One needs to call <strong>nf_register_net_hook()</strong> with a pointer to a net structure (usually _&init_net_) and a pointer to the <strong>nf_hook_ops</strong> structure. This will register the netfilter hook function with the kernel and make it active.

To unregister a netfilter hook function, one needs to call <strong>nf_unregister_net_hook()</strong> with the same parameters.

One can attach multiple callback functions to the same hooks and perform different operations based on the requirement. 

Let’s try to visualize what this looks like.

![[Pasted image 20260622123957.png]]

---

tags:

- linux
- networking
- kernel
- firewall
- netfilter created: 2026-06-23

---

# Netfilter Conntrack — Connection Tracking

> [!abstract] Summary **Conntrack** (connection tracking) is a subsystem of the Linux kernel's **Netfilter** framework. It keeps a stateful record of every active network flow passing through the system, enabling firewalls, NAT, and other network services to make decisions based on the full context of a connection — not just individual packets.

---

## Table of Contents

**Core Concepts**

- [[#Architecture Overview]]
- [[#How Connection Tracking Works]]
- [[#Connection States]]
- [[#The Conntrack Entry]]
- [[#Full TCP Internal State Machine]]

**Protocol Support**

- [[#Netfilter Hooks]]
- [[#IP Fragment Handling and Defragmentation]]
- [[#SCTP and DCCP Protocol Tracking]]
- [[#GRE and PPTP Tracking]]
- [[#Bridge Networking and nf_conntrack_bridge]]

**Features**

- [[#NAT Integration]]
- [[#Connection Tracking Helpers]]
- [[#Conntrack Zones]]
- [[#Conntrack Labels]]
- [[#Conntrack Accounting and Timestamps]]

**Firewall Integration**

- [[#Conntrack in iptables and nftables]]

**Configuration and Performance**

- [[#/proc and /sys Interfaces]]
- [[#Kernel Parameters and Tuning]]
- [[#NOTRACK and CT Bypass]]
- [[#Flowtable and Hardware Offload]]

**Operations and Tooling**

- [[#Conntrack Tools and Commands]]
- [[#Events, Logging and conntrackd]]
- [[#conntrackd Internals]]

**Deployment and Security**

- [[#Conntrack in Containers and Kubernetes]]
- [[#Security Considerations and Hardening]]

**Troubleshooting**

- [[#Common Issues and Troubleshooting]]

---

## Architecture Overview

Netfilter is the packet filtering framework embedded in the Linux kernel. It provides a series of **hooks** inside the kernel networking stack where kernel modules can register callback functions to inspect or modify packets.

Conntrack is built on top of Netfilter and provides the foundational **stateful** layer that all other stateful components (NAT, stateful firewalling) depend on.

```
User Space
  └── conntrack(8), nftables(8), iptables(8)
        │
Kernel Space
  └── Netfilter Core
        ├── Conntrack Subsystem  ←── you are here
        │     ├── Hash Table (conntrack entries)
        │     ├── Protocol Trackers (TCP, UDP, ICMP, DCCP, SCTP…)
        │     ├── CT Helpers (FTP, SIP, H.323, TFTP…)
        │     └── CT Events (nfnetlink)
        ├── NAT Subsystem (depends on conntrack)
        └── Packet Filter (iptables / nftables)
```

### Key Kernel Modules

|Module|Purpose|
|---|---|
|`nf_conntrack`|Core connection tracking engine|
|`nf_conntrack_ipv4`|IPv4 conntrack support|
|`nf_conntrack_ipv6`|IPv6 conntrack support|
|`nf_conntrack_ftp`|FTP ALG helper|
|`nf_conntrack_sip`|SIP/VoIP ALG helper|
|`nf_conntrack_h323`|H.323 ALG helper|
|`nf_conntrack_tftp`|TFTP ALG helper|
|`nf_conntrack_irc`|IRC DCC ALG helper|
|`nf_conntrack_netlink`|Userspace communication via nfnetlink|
|`nf_nat`|NAT core (depends on conntrack)|
|`nf_conntrack_bridge`|Conntrack support for bridged traffic (see [[#Bridge Networking and nf_conntrack_bridge]])|
|`br_netfilter`|Enables Netfilter hooks on Linux bridge devices; prerequisite for `nf_conntrack_bridge`|
|`nf_defrag_ipv4`|IPv4 fragment reassembly; auto-loaded by `nf_conntrack` (see [[#IP Fragment Handling and Defragmentation]])|
|`nf_defrag_ipv6`|IPv6 fragment reassembly; auto-loaded by `nf_conntrack` (see [[#IP Fragment Handling and Defragmentation]])|

---

## How Connection Tracking Works

### Packet Flow and Tuple Matching

Every packet that enters the conntrack subsystem is described by a **tuple** — a unique identifier for a flow:

```
IPv4 tuple = (src_ip, dst_ip, src_port, dst_port, protocol, zone)
IPv6 tuple = (src_ip6, dst_ip6, src_port, dst_port, protocol, zone)
```

The conntrack engine maintains a **hash table** of all known connections. For each incoming packet, it:

1. Computes the tuple from the packet headers.
2. Looks up the tuple in the hash table.
3. If found → updates the existing entry (refreshes timeout, advances TCP state machine).
4. If not found → creates a **new** entry in state `NEW`.

### Bidirectional Tracking

Each conntrack entry tracks **both directions** of a flow:

```
ORIGINAL direction:   client → server   (e.g., 10.0.0.1:54321 → 1.2.3.4:80)
REPLY direction:      server → client   (e.g., 1.2.3.4:80 → 10.0.0.1:54321)
```

Both tuples (original + reply) are stored in the same entry. This is how NAT information is preserved: the reply tuple is rewritten if NAT is applied.

### Timeout and Eviction

Each entry has a **timeout** specific to its protocol and state. When the timer expires and no packets have refreshed it, the entry is removed.

|Protocol / State|Typical Default Timeout|
|---|---|
|TCP ESTABLISHED|5 days (432000 s)|
|TCP TIME_WAIT|120 s|
|TCP CLOSE|10 s|
|TCP SYN_SENT|120 s|
|TCP FIN_WAIT|120 s|
|UDP stream|180 s|
|UDP unreplied|30 s|
|ICMP|30 s|
|Generic|600 s|

> [!note] Timeouts can be customized per-protocol and are accessible via `/proc/sys/net/netfilter/` or `sysctl`.

---

## Connection States

These are the states a conntrack entry can be in. These states are **independent from TCP states** — they are Netfilter's own abstraction applied across all protocols.

### States Table

|State|Description|
|---|---|
|`NEW`|First packet of a flow; no reply seen yet.|
|`ESTABLISHED`|Bidirectional traffic observed; the reply packet has been seen.|
|`RELATED`|A new connection related to an existing `ESTABLISHED` one (e.g., FTP data channel, ICMP error). Requires a CT helper.|
|`INVALID`|Packet does not match any known connection and cannot be identified as starting a new one. Usually dropped.|
|`UNTRACKED`|The packet has explicitly been marked to bypass conntrack (via `NOTRACK`/`CT --notrack`).|
|`SNAT`|Virtual state exposed only by the legacy `-m state` module: entry has SNAT applied. **Not** matchable with `-m conntrack --ctstate`; use `--ctstatus snat` instead.|
|`DNAT`|Virtual state exposed only by the legacy `-m state` module: entry has DNAT applied. **Not** matchable with `-m conntrack --ctstate`; use `--ctstatus dnat` instead.|

### State Transition Diagram (TCP)

```
                     SYN
[NEW] ─────────────────────────────► [SYN_SENT]
                                           │ SYN+ACK
                                           ▼
                                    [SYN_RECV]
                                           │ ACK
                                           ▼
                                    [ESTABLISHED] ◄──── data packets
                                           │
                                    FIN / RST
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                         [FIN_WAIT]  [CLOSE_WAIT]  [CLOSE]
                              │
                         TIME_WAIT
                              │
                           (evicted)
```

> [!warning] INVALID packets Packets hitting the `INVALID` state should almost always be **dropped** explicitly with a firewall rule. Passing them through can cause security issues and confuse the state machine.

---

## The Conntrack Entry

Each entry in the conntrack table stores:

```
struct nf_conn {
    /* Tuples */
    struct nf_conntrack_tuple_hash tuplehash[IP_CT_DIR_MAX];

    /* State flags */
    unsigned long status;          // IPS_* flags (see below)

    /* Timeout */
    u32 timeout;

    /* Protocol-specific state */
    union nf_conntrack_proto proto;  // e.g., TCP state machine data

    /* NAT info (if nf_nat loaded) */
    struct nf_conn_nat *nat;

    /* Helper (ALG) */
    struct nf_conntrack_helper *helper;

    /* Extension area (CT labels, marks, zones…) */
    struct nf_ct_ext *ext;

    /* Reference count */
    struct nf_conntrack ct_general;

    /* Mark (set via iptables CONNMARK or nftables ct mark) */
    u32 mark;

    /* Zone */
    struct nf_conntrack_zone zone;
};
```

### IPS_* Status Flags

These flags are stored in the `status` field:

|Flag|Meaning|
|---|---|
|`IPS_EXPECTED`|Entry was expected (by a CT helper)|
|`IPS_SEEN_REPLY`|A reply packet has been received|
|`IPS_ASSURED`|Entry is safe to keep (won't be evicted under pressure)|
|`IPS_CONFIRMED`|Entry has been inserted into the hash table|
|`IPS_SRC_NAT`|Source NAT applied|
|`IPS_DST_NAT`|Destination NAT applied|
|`IPS_SEQ_ADJUST`|Sequence number adjustment active (for NAT on TCP)|
|`IPS_DYING`|Entry is being removed|
|`IPS_OFFLOAD`|Flow offloaded to hardware (flowtable)|

---

## Netfilter Hooks

Conntrack registers callbacks at multiple points in the packet path:

```
                       ┌─────────────────────────────────────────────┐
                       │              Linux Kernel Network Stack      │
                       └─────────────────────────────────────────────┘

Incoming packet
       │
       ▼
[NF_INET_PRE_ROUTING]   ← conntrack: lookup / create entry
       │
       ├──(local process?)──► [NF_INET_LOCAL_IN]   ← conntrack confirm
       │
       └──(forwarded)──────► [NF_INET_FORWARD]
                                     │
                                     ▼
                             [NF_INET_POST_ROUTING]  ← NAT / confirm

Outgoing (local) packet
       │
       ▼
[NF_INET_LOCAL_OUT]      ← conntrack: lookup / create entry
       │
       ▼
[NF_INET_POST_ROUTING]   ← conntrack confirm / NAT
```

### Hook Priority Values (conntrack registers at these priorities)

|Hook|Priority|Action|
|---|---|---|
|`NF_INET_PRE_ROUTING`|`-200` (very early)|Lookup + create unconfirmed entry|
|`NF_INET_LOCAL_OUT`|`-200`|Lookup + create unconfirmed entry|
|`NF_INET_POST_ROUTING`|`MAX` (very late)|**Confirm** the entry (insert into table)|
|`NF_INET_LOCAL_IN`|`MAX`|**Confirm** the entry|

> [!important] Confirmation Entries are created **unconfirmed** at PRE_ROUTING/LOCAL_OUT and only become visible in the hash table after **confirmation** at POST_ROUTING/LOCAL_IN. This avoids inserting entries for packets that are later dropped by firewall rules.

---

## NAT Integration

NAT (Network Address Translation) is implemented as an extension to conntrack. It does **not** perform per-packet address rewriting independently — it relies on the conntrack entry to store the NAT mapping and applies it consistently to all packets in a flow.

### How it Works

1. **First packet** of a flow hits `NF_INET_PRE_ROUTING`.
2. Conntrack creates a new entry with original and reply tuples.
3. NAT rule fires: the **reply tuple** is rewritten (e.g., DNAT rewrites the reply tuple's destination back to the internal IP).
4. On the **REPLY** direction, conntrack automatically applies the inverse mapping.
5. All subsequent packets in the flow are translated using the stored entry — no rule re-evaluation needed.

### SNAT vs DNAT

|Type|What changes|Applied at|
|---|---|---|
|SNAT (Masquerade)|Source IP/port of outgoing packet|`POSTROUTING`|
|DNAT (Port Forward)|Dest IP/port of incoming packet|`PREROUTING`|

---

## Connection Tracking Helpers

Some protocols embed IP addresses or port numbers **inside the payload** (FTP, SIP, H.323). Conntrack helpers (Application Layer Gateways) parse these payloads and create **expected connections** — entries pre-registered in the "expectation" table.

### How Expectations Work

1. Helper inspects payload of an `ESTABLISHED` control connection.
2. Extracts the data channel IP:port from the payload.
3. Creates an **expectation** entry (a pending conntrack entry).
4. When the data connection arrives, it matches the expectation and is marked `RELATED`.

### Example: FTP Passive Mode

```
Client ──[TCP:21 CONTROL]──► Server       ← ESTABLISHED, helper parses PORT/PASV
Client ──[TCP:XXXX DATA]───► Server       ← RELATED (matched expectation)
```

### Available Helpers

|Helper|Protocol|Ports|
|---|---|---|
|`nf_conntrack_ftp`|FTP (active + passive)|21|
|`nf_conntrack_sip`|SIP/VoIP|5060, 5061|
|`nf_conntrack_h323`|H.323 video|1720|
|`nf_conntrack_tftp`|TFTP|69|
|`nf_conntrack_irc`|IRC DCC|6667|
|`nf_conntrack_pptp`|PPTP VPN|1723|
|`nf_conntrack_amanda`|Amanda backup|10080|

> [!warning] Automatic helper assignment Since Linux 4.7, helpers are **no longer automatically assigned** by port number. You must explicitly assign helpers using `iptables -j CT --helper ftp` or nftables `ct helper` objects. This improves security but may break existing setups.

---

## Conntrack Zones

Zones allow you to run **multiple independent conntrack instances** on the same system. This is useful when routing between overlapping IP address spaces (e.g., multiple VRFs with the same RFC1918 ranges).

### Zone Types

|Zone type|Scope|
|---|---|
|**Default zone (0)**|All interfaces; global tracking|
|**Per-interface zone**|Assigned via `nf_tables` or iptables, scoped to an interface|
|**Per-packet zone**|Assigned dynamically via iptables mark + zone rules|

### Setting a Zone (iptables)

```bash
# Assign incoming traffic on eth1 to zone 1
iptables -t raw -A PREROUTING -i eth1 -j CT --zone 1

# Assign reply direction for zone 1
iptables -t raw -A OUTPUT -o eth1 -j CT --zone 1 --zone-dir reply
```

Entries in different zones are completely isolated — two connections with identical tuples can coexist if they are in different zones.

---

## Conntrack Tools and Commands

The `conntrack` userspace tool (from the `conntrack-tools` package) lets you inspect and manipulate the kernel's conntrack table.

> [!important] Required capability: `CAP_NET_ADMIN` All `conntrack` operations require the `CAP_NET_ADMIN` Linux capability. Without it commands fail silently or with `Operation not permitted`. This matters in:
> 
> - **Containers**: Docker/Podman drop `CAP_NET_ADMIN` by default — add it with `--cap-add NET_ADMIN`.
> - **Rootless environments**: Unprivileged users cannot read or modify the conntrack table.
> - **Kubernetes pods**: Requires `securityContext.capabilities.add: ["NET_ADMIN"]` and typically also `hostNetwork: true` to see host-namespace entries.

### Installation

```bash
# Debian/Ubuntu
apt install conntrack

# RHEL/CentOS/Fedora
dnf install conntrack-tools
```

### Listing Entries

```bash
# List all entries (like /proc/net/nf_conntrack but human-readable)
conntrack -L

# List only TCP ESTABLISHED connections
conntrack -L -p tcp --state ESTABLISHED

# List connections to a specific IP
conntrack -L -d 192.168.1.100

# JSON output
conntrack -L -o json
```

**Example output:**

```
tcp      6 86393 ESTABLISHED src=192.168.1.5 dst=93.184.216.34 sport=54321 dport=443 \
         src=93.184.216.34 dst=192.168.1.5 sport=443 dport=54321 [ASSURED] mark=0 use=1
```

Fields: `proto`, `proto_number`, `timeout`, `state`, `src`, `dst`, `sport`, `dport` (original dir), then `src`, `dst`, `sport`, `dport` (reply dir), `[flags]`, `mark`, `zone`.

### Deleting Entries

```bash
# Delete a specific flow
conntrack -D -p tcp -s 10.0.0.1 --sport 12345 -d 1.2.3.4 --dport 80

# Delete all UDP entries
conntrack -D -p udp

# Delete all entries for a source IP
conntrack -D -s 192.168.1.50

# Flush the entire table (use with extreme caution!)
conntrack -F
```

> [!danger] Flushing conntrack `conntrack -F` deletes all entries, including those tracking active NAT sessions. All active connections will be **reset** and must be re-established.

### Monitoring Events

```bash
# Watch real-time events (new, update, destroy)
conntrack -E

# Watch only new connections
conntrack -E -e NEW

# Watch destroy events for TCP
conntrack -E -e DESTROY -p tcp
```

### Counting Entries

```bash
# Show current entry count
conntrack -C

# Show statistics per CPU
conntrack -S
```

### Creating Entries Manually

```bash
# Manually insert a conntrack entry
conntrack -I -p tcp \
  --src 10.0.0.1 --sport 1234 --dst 10.0.0.2 --dport 80 \
  --reply-src 10.0.0.2 --reply-sport 80 --reply-dst 10.0.0.1 --reply-dport 1234 \
  --state ESTABLISHED --timeout 300
```

---

## /proc and /sys Interfaces

### /proc/net/nf_conntrack

The raw conntrack table, one entry per line:

```bash
cat /proc/net/nf_conntrack
```

Each line format:

```
ipversion  proto_num  proto_name  timeout  state  \
  src=X dst=Y sport=Z dport=W  src=X2 dst=Y2 sport=Z2 dport=W2  [flags]
```

### /proc/net/nf_conntrack_expect

Lists pending **expectations** (from CT helpers):

```bash
cat /proc/net/nf_conntrack_expect
```

### /proc/sys/net/netfilter/ — Runtime Parameters

|Path|Description|
|---|---|
|`nf_conntrack_max`|Maximum number of entries in the table|
|`nf_conntrack_count`|Current number of entries (read-only)|
|`nf_conntrack_buckets`|Hash table bucket count. Read-only via `/proc`; on kernels **≥ 5.x** writable at runtime via `/sys/module/nf_conntrack/parameters/hashsize`. On older kernels set only at module load.|
|`nf_conntrack_tcp_timeout_established`|TCP ESTABLISHED timeout (seconds)|
|`nf_conntrack_tcp_timeout_time_wait`|TCP TIME_WAIT timeout|
|`nf_conntrack_tcp_timeout_close`|TCP CLOSE timeout|
|`nf_conntrack_tcp_timeout_syn_sent`|TCP SYN_SENT timeout|
|`nf_conntrack_udp_timeout`|UDP unreplied timeout|
|`nf_conntrack_udp_timeout_stream`|UDP stream (replied) timeout|
|`nf_conntrack_icmp_timeout`|ICMP timeout|
|`nf_conntrack_generic_timeout`|Generic (unknown protocol) timeout|
|`nf_conntrack_tcp_loose`|Allow mid-flow TCP pickup (bool, default 1)|
|`nf_conntrack_tcp_be_liberal`|Be liberal with TCP window tracking (bool)|
|`nf_conntrack_log_invalid`|Log invalid packets (0=off, proto number)|
|`nf_conntrack_expect_max`|Max number of pending expectations|
|`nf_conntrack_checksum`|Verify checksums of packets (bool, default 1)|

---

## Kernel Parameters and Tuning

### Common Tuning for High-Traffic Systems

```bash
# Increase max table size (default usually 65536 or 131072)
sysctl -w net.netfilter.nf_conntrack_max=524288

# Increase bucket count (must be set before module load, or at module load)
# Rule of thumb: buckets = nf_conntrack_max / 4
# At module load time:
modprobe nf_conntrack hashsize=131072

# Or set via sysfs (if supported):
echo 131072 > /sys/module/nf_conntrack/parameters/hashsize

# Reduce TCP established timeout for idle connections (e.g., NAT gateway)
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600

# Reduce UDP stream timeout
sysctl -w net.netfilter.nf_conntrack_udp_timeout_stream=60

# Reduce generic timeout
sysctl -w net.netfilter.nf_conntrack_generic_timeout=60
```

### Making Settings Persistent

Add to `/etc/sysctl.conf` or `/etc/sysctl.d/99-conntrack.conf`:

```ini
net.netfilter.nf_conntrack_max = 524288
net.netfilter.nf_conntrack_tcp_timeout_established = 600
net.netfilter.nf_conntrack_udp_timeout_stream = 60
net.netfilter.nf_conntrack_generic_timeout = 60
```

Then apply:

```bash
sysctl --system
```

For `hashsize`, create `/etc/modprobe.d/nf_conntrack.conf`:

```
options nf_conntrack hashsize=131072
```

### Memory Estimation

Each conntrack entry uses approximately **300–400 bytes** of kernel memory.

```
Memory (bytes) ≈ nf_conntrack_max × 350
```

For 524288 entries: `524288 × 350 ≈ 175 MB`

> [!note] Additional overhead with optional features If `nf_conntrack_acct` or `nf_conntrack_timestamp` are enabled, add up to **+48 bytes per entry** (see [[#Conntrack Accounting and Timestamps]] for the per-feature breakdown). For 524288 entries that adds another ~25 MB.

### Monitoring Table Usage

```bash
# Current count vs max
echo "Count: $(sysctl -n net.netfilter.nf_conntrack_count) / $(sysctl -n net.netfilter.nf_conntrack_max)"

# Per-CPU statistics
conntrack -S
# Fields: found, invalid, ignore, insert, insert_failed, drop, early_drop,
#         error, search_restart
```

> [!warning] Table full condition When `nf_conntrack_count` approaches `nf_conntrack_max`, new connections are **dropped** and the kernel logs `nf_conntrack: table full, dropping packet`. Monitor this value closely on busy systems.

### Flow Table Offloading (Flowtable)

Since Linux 4.16, nftables supports **flowtables**: a fast-path that bypasses the full Netfilter hook chain for ESTABLISHED flows, dramatically reducing CPU overhead on routers.

```
nftables config:
  table ip filter {
      flowtable ft {
          hook ingress priority 0;
          devices = { eth0, eth1 };
      }
      chain forward {
          type filter hook forward priority 0;
          ip protocol { tcp, udp } flow add @ft
      }
  }
```

---

## Events, Logging and conntrackd

### Conntrack Events via nfnetlink

Conntrack publishes events over a **Netlink** socket (`NFNLGRP_CONNTRACK_NEW`, `NFNLGRP_CONNTRACK_UPDATE`, `NFNLGRP_CONNTRACK_DESTROY`) that userspace tools can subscribe to.

Event types:

|Event|When fired|
|---|---|
|`NFCT_T_NEW`|New conntrack entry confirmed|
|`NFCT_T_UPDATE`|Entry updated (state change, timeout refresh)|
|`NFCT_T_DESTROY`|Entry destroyed (timeout or explicit delete)|
|`NFCT_T_NEW` (expect)|New expectation created|
|`NFCT_T_DESTROY` (expect)|Expectation destroyed|

### nf_conntrack_events — Controlling Event Generation

By default the kernel emits an event to userspace for every conntrack state change. On high-traffic systems this Netlink overhead is measurable and can be safely reduced or disabled when `conntrackd` is not in use.

|Sysctl|Values|Description|
|---|---|---|
|`net.netfilter.nf_conntrack_events`|`0` / `1` / `2`|`0` = disabled, `1` = enabled, `2` = dynamic (auto-disable when no listener)|
|`net.netfilter.nf_conntrack_events_retry_timeout`|seconds|How long to retry delivering events before giving up|

```bash
# Disable events entirely (saves CPU on busy routers with no conntrackd)
sysctl -w net.netfilter.nf_conntrack_events=0

# Dynamic mode — kernel auto-enables when a listener subscribes
sysctl -w net.netfilter.nf_conntrack_events=2
```

> [!tip] Performance Disabling conntrack events (`=0`) on a NAT router that does not run `conntrackd` can reduce CPU usage by 5–15% under high connection-rate load, because the kernel no longer serialises and sends Netlink messages for every state change.

### conntrackd — High Availability Sync

`conntrackd` is a daemon that:

- Replicates conntrack state between **cluster nodes** (active-passive or active-active HA).
- Uses UDP multicast or unicast to synchronize entries.
- Integrates with Keepalived and Corosync for failover.

```bash
# Install
apt install conntrackd

# Minimal /etc/conntrackd/conntrackd.conf (unicast sync)
Sync {
    Mode FTFW {
        ResendQueueSize 131072
        CommitTimeout 1800
        PurgeTimeout 60
    }
    UDP {
        IPv4_address 192.168.0.1
        IPv4_Destination_Address 192.168.0.2
        Port 3780
        Interface eth1
        Checksum on
    }
}
General {
    HashSize 32768
    HashLimit 131072
    LogFile /var/log/conntrackd.log
    Syslog on
    LockFile /var/lock/conntrack.lock
    UNIX {
        Path /var/run/conntrackd.ctl
    }
    NetlinkBufferSize 262142
    Filter From Kernelspace {
        Protocol Accept {
            TCP
            UDP
            ICMP
        }
        Address Ignore {
            IPv4_address 127.0.0.1
        }
    }
}
```

---

## Conntrack in iptables and nftables

### iptables — `-m conntrack` and `-m state`

```bash
# Allow ESTABLISHED and RELATED (stateful firewall core rule)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Drop INVALID packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Allow NEW connections on port 80
iptables -A INPUT -m conntrack --ctstate NEW -p tcp --dport 80 -j ACCEPT

# Match original direction source IP
iptables -A FORWARD -m conntrack --ctorigdst 10.0.0.5 -j ACCEPT

# Match by conntrack mark
iptables -A FORWARD -m conntrack --ctmark 42 -j ACCEPT
```

**Conntrack match options:**

|Option|Description|
|---|---|
|`--ctstate STATE[,STATE...]`|Match connection state|
|`--ctproto PROTO`|Match IP protocol|
|`--ctorigsrc IP[/MASK]`|Match original source IP|
|`--ctorigdst IP[/MASK]`|Match original destination IP|
|`--ctreplsrc IP[/MASK]`|Match reply source IP|
|`--ctrepldst IP[/MASK]`|Match reply destination IP|
|`--ctorigsrcport PORT`|Match original source port|
|`--ctorigdstport PORT`|Match original destination port|
|`--ctdir DIR`|Match `ORIGINAL` or `REPLY` direction|
|`--ctstatus FLAGS`|Match IPS_* status flags|
|`--ctexpire TIME[:TIME]`|Match remaining timeout (seconds)|
|`--ctmark MARK[/MASK]`|Match conntrack mark|

### CONNMARK Target (Saving Marks)

```bash
# Save packet mark into conntrack entry
iptables -t mangle -A PREROUTING -j CONNMARK --save-mark

# Restore conntrack mark to packet mark (for routing, tc, etc.)
iptables -t mangle -A PREROUTING -j CONNMARK --restore-mark

# Set a specific conntrack mark
iptables -t mangle -A PREROUTING -j CONNMARK --set-mark 0x10/0x10
```

### CT Target (Raw Table — Control conntrack behavior)

```bash
# Exempt traffic from tracking (NOTRACK)
iptables -t raw -A PREROUTING -p udp --dport 53 -j CT --notrack

# Assign a CT helper explicitly
iptables -t raw -A PREROUTING -p tcp --dport 21 -j CT --helper ftp

# Assign a zone
iptables -t raw -A PREROUTING -i eth1 -j CT --zone 1
```

---

### nftables — ct expressions

```nftables
# Stateful firewall core rules
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        ct state established,related accept
        ct state invalid drop

        tcp dport 22 ct state new accept
        tcp dport { 80, 443 } ct state new accept
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
        ct state established,related accept
        ct state invalid drop
    }
}
```

**nftables ct expressions:**

|Expression|Description|
|---|---|
|`ct state new\|established\|related\|invalid\|untracked`|Connection state|
|`ct status expected\|seen-reply\|assured\|confirmed\|snat\|dnat`|IPS flags|
|`ct mark`|Conntrack mark (read/write)|
|`ct label`|Conntrack label bits|
|`ct direction original\|reply`|Packet direction within flow|
|`ct expiration`|Remaining timeout|
|`ct proto-src`|Original protocol source port|
|`ct proto-dst`|Original protocol destination port|
|`ct original { ip saddr, ip daddr, ... }`|Fields in original direction|
|`ct reply { ip saddr, ip daddr, ... }`|Fields in reply direction|
|`ct zone`|Zone identifier|
|`ct helper`|Assigned helper name|

**Assigning helpers in nftables:**

```nftables
table ip mynat {
    ct helper ftp-standard {
        type "ftp" protocol tcp;
        l3proto ip;
    }
    chain prerouting {
        type filter hook prerouting priority raw;
        tcp dport 21 ct helper set "ftp-standard"
    }
}
```

---

## Common Issues and Troubleshooting

### Issue: Table Full — Dropping Packets

**Symptom:** `dmesg | grep conntrack` shows `nf_conntrack: table full, dropping packet`

**Solution:**

```bash
# Check current usage
sysctl net.netfilter.nf_conntrack_count
sysctl net.netfilter.nf_conntrack_max

# Increase the limit
sysctl -w net.netfilter.nf_conntrack_max=524288

# Also reduce timeouts for protocols you don't need long tracking on
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600
sysctl -w net.netfilter.nf_conntrack_udp_timeout_stream=30
```

---

### Issue: FTP / SIP Not Working Through NAT

**Symptom:** FTP passive mode or SIP calls fail when going through a NAT gateway.

**Cause:** CT helper not loaded or not assigned.

**Solution:**

```bash
# Load the helper module
modprobe nf_conntrack_ftp
modprobe nf_conntrack_sip

# Assign it explicitly (modern kernels)
iptables -t raw -A PREROUTING -p tcp --dport 21 -j CT --helper ftp
```

---

### Issue: Asymmetric Routing Drops Packets (INVALID state)

**Symptom:** Return traffic is marked `INVALID` and dropped by stateful rules.

**Cause:** Packets follow different paths in each direction; conntrack only sees one direction.

**Solution options:**

1. Fix routing to be symmetric.
2. Use conntrack zones to separate the routing domains.
3. Disable conntrack for that specific traffic class with `CT --notrack` in the raw table.
4. Set `nf_conntrack_tcp_loose=1` to allow mid-flow TCP pickup.

---

### Issue: High CPU on Busy Routers

**Cause:** Every packet goes through the full Netfilter hook chain.

**Solution:** Enable flowtable offloading (see [[#Kernel Parameters and Tuning]]):

```nftables
flowtable ft {
    hook ingress priority 0;
    devices = { eth0, eth1 };
}
# In forward chain:
ip protocol { tcp, udp } flow add @ft
```

---

### Issue: Conntrack Not Tracking Expected Protocol

**Cause:** Protocol not supported, or `CT --notrack` applied.

**Diagnostic:**

```bash
# Check if packets are entering conntrack at all
conntrack -E -e NEW 2>/dev/null &
# Then generate traffic and see if NEW events appear

# Check for NOTRACK rules
iptables -t raw -L -nv
```

---

### Useful Diagnostic Commands

```bash
# Watch conntrack table in real-time
watch -n1 'conntrack -L 2>/dev/null | wc -l; echo "/" ; sysctl -n net.netfilter.nf_conntrack_max'

# Find top talkers in conntrack table
conntrack -L 2>/dev/null | awk '{print $7}' | sort | uniq -c | sort -rn | head

# Show per-CPU drop stats
conntrack -S

# Dump raw table
cat /proc/net/nf_conntrack | less

# Show expectations (CT helpers)
conntrack -L expect

# Check loaded conntrack modules
lsmod | grep conntrack
```

---

## Conntrack Accounting and Timestamps

### Per-Flow Byte and Packet Counters

Conntrack can store per-entry **byte and packet counters** for both directions of a flow. This is disabled by default because it increases memory consumption per entry.

```bash
# Enable accounting (survives until module reload)
sysctl -w net.netfilter.nf_conntrack_acct=1

# Persist in /etc/sysctl.d/99-conntrack.conf
net.netfilter.nf_conntrack_acct = 1

# Or load the module with accounting on
modprobe nf_conntrack nf_conntrack_acct=1
```

Once enabled, `conntrack -L` shows byte/packet counts per direction:

```
tcp 6 86390 ESTABLISHED src=10.0.0.1 dst=1.2.3.4 sport=54321 dport=443 \
    packets=142 bytes=18432 \
    src=1.2.3.4 dst=10.0.0.1 sport=443 dport=54321 \
    packets=98 bytes=104857 [ASSURED] mark=0 use=1
```

### Per-Flow Timestamps

Conntrack can also record the **start time** (and implicitly the end time via the destroy event) of every flow. Useful for audit logging, billing, and anomaly detection.

```bash
# Enable timestamps
sysctl -w net.netfilter.nf_conntrack_timestamp=1

# Or at module load
modprobe nf_conntrack nf_conntrack_timestamp=1
```

With timestamps enabled, each entry carries:

- `delta-time` — seconds since the connection was first seen (shown in `conntrack -L` output)
- `start` — absolute Unix timestamp (visible in event output)

```bash
# See timestamps in event stream
conntrack -E -o timestamp
```

### Memory Impact

|Feature|Overhead per entry|
|---|---|
|Accounting|+32 bytes (2× `{ packets, bytes }` u64 pairs)|
|Timestamps|+16 bytes (2× u64: start, stop)|
|Both|+48 bytes|

For 524 288 entries with both features: ≈ 25 MB additional RAM.

---

## IP Fragment Handling and Defragmentation

### Why Conntrack Needs Reassembly

Conntrack must inspect L4 headers (TCP/UDP ports, ICMP type/code) to build a flow tuple. IP fragments after the first one carry **no L4 header**, only raw payload. Without reassembly, conntrack cannot classify them.

To solve this, loading `nf_conntrack` automatically pulls in:

```
nf_conntrack
  └── nf_defrag_ipv4   (registers NF_INET_PRE_ROUTING hook at priority -400)
  └── nf_defrag_ipv6
```

These modules **reassemble fragments in kernel memory** before conntrack sees the packet. After conntrack processes the reassembled packet, the kernel re-fragments it (if needed) for transmission.

### Performance and Memory Implications

Fragment reassembly requires buffering incomplete fragment chains in kernel memory. Under a fragmentation flood this can exhaust kernel memory rapidly.

Key parameters:

|Sysctl|Default|Description|
|---|---|---|
|`net.ipv4.ipfrag_high_thresh`|4 MB|Max memory for fragment queues; new frags dropped above this|
|`net.ipv4.ipfrag_low_thresh`|3 MB|Threshold to start evicting old queues|
|`net.ipv4.ipfrag_time`|30 s|Timeout for incomplete fragment chains|
|`net.ipv6.ip6frag_high_thresh`|4 MB|Same for IPv6|
|`net.ipv6.ip6frag_time`|60 s|IPv6 fragment timeout|

### Tunnels and Fragmentation (GRE, VXLAN, IPsec)

Encapsulation protocols reduce the effective MTU for the inner packet. A common failure mode:

```
Physical MTU = 1500
VXLAN overhead = 50 bytes → inner MTU = 1450
Inner packet = 1500 bytes → must be fragmented
```

If the inner packet is fragmented **after** encapsulation, conntrack on the outer tunnel interface sees only the outer headers and classifies the inner fragments as generic/unknown. Consider:

- Setting `ip link set dev vxlan0 mtu 1450` on the inner interface.
- Using `nf_conntrack_proto_gre` for GRE tunnels.
- Enabling PMTUD (Path MTU Discovery) across the tunnel.

> [!warning] Fragmentation + NAT Fragmented packets with NAT applied require conntrack to track sequence number adjustments. If a fragment arrives out-of-order after NAT is applied, the rewrite may be incorrect. Always avoid fragmentation on NAT paths.

---

## Conntrack Labels

### Labels vs Marks

Conntrack supports two distinct per-entry metadata mechanisms:

|Feature|Size|Primary use|
|---|---|---|
|**Mark** (`ct mark`)|32 bits (u32)|Routing policy, QoS, general tagging|
|**Label** (`ct label`)|128 bits (bitfield)|Fine-grained policy (Kubernetes, Calico)|

Labels are a bitmask: each bit is independently set or cleared. This allows multiple independent subsystems to use different bits without interfering with each other.

### Enabling Label Support

Labels require the `nf_conntrack_labels` module and must be enabled with a sysctl:

```bash
modprobe nf_conntrack_labels

# Set the label length in bits (must be a multiple of 32, max 128)
sysctl -w net.netfilter.nf_conntrack_labels_bit_size=128
```

### Using Labels in iptables

```bash
# Set bit 0 of the conntrack label
iptables -t mangle -A PREROUTING -j CONNLABEL --label 0 --set

# Match on bit 0
iptables -A FORWARD -m connlabel --label 0 -j ACCEPT

# Clear bit 0
iptables -t mangle -A POSTROUTING -j CONNLABEL --label 0
```

### Using Labels in nftables

```nftables
# Set label bits 0 and 1
table ip filter {
    chain forward {
        ct label set 0x3      # set bits 0 and 1
    }
}

# Match label bit 0
ct label & 0x1 == 0x1 accept
```

### Kubernetes / Calico Usage

Calico uses conntrack labels to track **policy verdict** for a flow, so that the full policy evaluation only happens on the first packet:

- Bit 0: Policy has been evaluated
- Bit 1: Flow was allowed

This is why `nf_conntrack_labels_bit_size` must be at least 64 on Kubernetes nodes running Calico.

---

## Full TCP Internal State Machine

Conntrack maintains its own TCP state machine **independently from the kernel's socket state machine**. It tracks states at the packet level, without needing the socket to exist.

### Complete State Table

|Conntrack TCP State|Trigger|Timeout (default)|
|---|---|---|
|`NONE`|No packet yet|—|
|`SYN_SENT`|SYN seen in original direction|120 s|
|`SYN_RECV`|SYN+ACK seen in reply direction|60 s|
|`ESTABLISHED`|ACK completing the handshake|432000 s (5 days)|
|`FIN_WAIT`|FIN seen in either direction|120 s|
|`CLOSE_WAIT`|FIN seen, waiting for the other side|60 s|
|`LAST_ACK`|Second FIN seen|30 s|
|`TIME_WAIT`|Final ACK seen|120 s|
|`CLOSE`|RST seen, or simultaneous close|10 s|
|`SYN_SENT2`|SYN seen in both directions (simultaneous open)|120 s|
|`IGNORE`|Packet deliberately not tracked|—|

### Simultaneous Open (SYN_SENT2)

When two hosts both initiate a TCP connection to each other at the same time (rare but valid per RFC 793), conntrack sees SYN in **both** the original and reply directions before any SYN+ACK. It advances to `SYN_SENT2` rather than `SYN_RECV`.

```
Host A ──SYN──► Host B
Host A ◄──SYN── Host B    ← both in SYN_SENT2
Host A ──SYN+ACK──► Host B
Host A ◄──SYN+ACK── Host B
                           → ESTABLISHED
```

### TCP Window Tracking

By default, conntrack validates that each TCP segment's sequence number falls within the expected window. This prevents sequence-number-based attacks but can cause legitimate mid-flow pickup (e.g., after a reboot) to be marked `INVALID`.

Relevant sysctls:

|Sysctl|Default|Effect|
|---|---|---|
|`nf_conntrack_tcp_loose`|`1`|Accept mid-flow packets that don't match any entry (creates ESTABLISHED entry on first packet seen)|
|`nf_conntrack_tcp_be_liberal`|`0`|If `1`, only out-of-window RST packets are marked INVALID; everything else passes|
|`nf_conntrack_tcp_max_retrans`|`3`|Max retransmissions before considering the connection dead|
|`nf_conntrack_tcp_ignore_invalid_rst`|`0`|Ignore RSTs with unexpected sequence numbers. **Not present on all kernels** — introduced as a distro backport (RHEL/CentOS); absent on many vanilla upstream kernels. Check with `sysctl net.netfilter.nf_conntrack_tcp_ignore_invalid_rst` before relying on it.|

> [!warning] tcp_loose and security Setting `tcp_loose=1` (the default) means conntrack will create an ESTABLISHED entry for the first packet it sees, even if it is a mid-session data packet with no prior handshake visible. This is necessary for asymmetric routing but allows traffic to bypass `NEW`-state firewall rules.

---

## SCTP and DCCP Protocol Tracking

### SCTP (Stream Control Transmission Protocol)

SCTP is a multi-homed, multi-stream transport protocol. Its conntrack support is in `nf_conntrack_proto_sctp`.

#### SCTP Conntrack States

|State|Description|
|---|---|
|`NONE`|No chunk seen|
|`COOKIE_WAIT`|INIT chunk seen|
|`COOKIE_ECHOED`|INIT-ACK seen|
|`ESTABLISHED`|COOKIE-ACK seen; association up|
|`SHUTDOWN_SENT`|SHUTDOWN sent|
|`SHUTDOWN_RECD`|SHUTDOWN received|
|`SHUTDOWN_ACK_SENT`|SHUTDOWN-ACK sent|
|`CLOSED`|Association terminated|

#### Multi-homing

SCTP associations can use multiple IP addresses per endpoint. Conntrack tracks only the **primary path** tuple. Secondary paths (failover paths) may appear as new connections unless handled explicitly.

```bash
modprobe nf_conntrack_proto_sctp

# Allow SCTP in iptables
iptables -A INPUT -p sctp -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
```

### DCCP (Datagram Congestion Control Protocol)

DCCP is a connection-oriented protocol with congestion control but no reliability. Conntrack support is in `nf_conntrack_proto_dccp`.

#### DCCP Conntrack States

|State|Description|
|---|---|
|`NONE`|No packet seen|
|`REQUEST`|DCCP-Request seen|
|`RESPOND`|DCCP-Response seen|
|`PARTOPEN`|DCCP-Ack seen (partial open)|
|`OPEN`|DCCP-DataAck seen; connection active|
|`CLOSEREQ`|DCCP-CloseReq seen|
|`CLOSING`|DCCP-Close seen|
|`TIMEWAIT`|DCCP-Reset seen|
|`IGNORE`|Packet deliberately not tracked|

```bash
modprobe nf_conntrack_proto_dccp
```

#### DCCP Timeouts

|State|Default Timeout|
|---|---|
|`REQUEST`|2 s|
|`RESPOND`|10 s|
|`PARTOPEN`|14 s|
|`OPEN`|43200 s (12 h)|
|`CLOSEREQ`|64 s|
|`CLOSING`|64 s|
|`TIMEWAIT`|240 s|

---

## GRE and PPTP Tracking

### GRE (Generic Routing Encapsulation)

GRE is a tunnelling protocol with no port concept. Its tuple uses the **GRE key** field instead of port numbers. Conntrack support is provided by `nf_conntrack_proto_gre`.

```bash
modprobe nf_conntrack_proto_gre
```

GRE tuple structure:

```
(src_ip, dst_ip, gre_key, protocol=GRE)
```

For GRE flows without a key (key field = 0), all GRE packets between the same pair of IPs share a single conntrack entry.

### PPTP

PPTP (Point-to-Point Tunnelling Protocol) uses TCP port 1723 for the **control channel** and GRE for the **data channel**. The `nf_conntrack_pptp` helper parses the PPTP control connection and creates expectations for the associated GRE data flows.

```bash
modprobe nf_conntrack_pptp   # automatically loads nf_conntrack_proto_gre
```

Flow:

```
Client ──TCP:1723──► Server   ← ESTABLISHED, pptp helper active
Client ──GRE──────► Server   ← RELATED (expected by pptp helper)
```

Timeouts for GRE:

|Sysctl|Default|
|---|---|
|`nf_conntrack_gre_timeout`|30 s (unreplied)|
|`nf_conntrack_gre_timeout_stream`|180 s (replied)|

> [!note] PPTP/GRE conntrack does **not** inspect or modify the PPP payload inside GRE. If you need to do NAT on PPTP itself (not just the control channel), you also need `nf_nat_pptp`.

---

## Bridge Networking and nf_conntrack_bridge

### The Problem: Bridged Traffic Bypasses Conntrack by Default

A Linux bridge (e.g., `docker0`, `virbr0`, `br0`) forwards frames at Layer 2. Without explicit configuration, bridged packets do **not** traverse the Netfilter IPv4/IPv6 hook points — they go through the bridge's own `BROUTING`/`FORWARD` hooks instead. This means conntrack, NAT rules, and iptables FORWARD rules are all silently bypassed for bridged traffic.

This is a common and confusing failure mode in:

- **Docker** (default `bridge` networking uses `docker0`)
- **KVM / libvirt** (VMs on `virbr0`)
- **LXC containers** on a Linux bridge
- **Software-defined networking** with Linux bridges as vSwitches

### The Solution: br_netfilter + nf_conntrack_bridge

Loading `br_netfilter` makes the bridge call the standard Netfilter IPv4/IPv6 hooks for routed traffic crossing the bridge. `nf_conntrack_bridge` adds full conntrack support for bridged (non-routed) traffic.

```bash
# Load both modules
modprobe br_netfilter
modprobe nf_conntrack_bridge   # kernel >= 5.3

# Make persistent
echo "br_netfilter" >> /etc/modules-load.d/conntrack.conf
echo "nf_conntrack_bridge" >> /etc/modules-load.d/conntrack.conf
```

After loading `br_netfilter`, enable the required sysctls:

```bash
# Make bridged IPv4/IPv6 traffic traverse iptables rules
sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1
sysctl -w net.bridge.bridge-nf-call-arptables=0   # usually not needed

# Persist
cat >> /etc/sysctl.d/99-bridge-conntrack.conf <<'EOF'
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF
```

### Packet Path with br_netfilter

```
Without br_netfilter:
  VM1 → [bridge L2 forward] → VM2       (iptables/conntrack NOT called)

With br_netfilter:
  VM1 → NF_INET_PRE_ROUTING → conntrack → NF_INET_FORWARD → NF_INET_POST_ROUTING → VM2
```

### nf_conntrack_bridge vs br_netfilter

|Module|What it enables|Kernel|
|---|---|---|
|`br_netfilter`|Bridged IPv4/IPv6 traffic passes through Netfilter IPv4/IPv6 hooks|All modern kernels|
|`nf_conntrack_bridge`|Full conntrack for purely bridged (non-IP-routed) frames|≥ 5.3|

> [!warning] Double-tracking risk With `br_netfilter` loaded, traffic that crosses a bridge **and** is then routed (common in Docker where the container sends via `docker0` and the host routes it out `eth0`) can be processed by conntrack **twice** — once at the bridge hook and once at the routing hook. This can cause duplicate NAT application or unexpected INVALID states. Use conntrack zones to isolate bridge and routing domains if this occurs.

### Kubernetes Requirement

Kubernetes mandates `br_netfilter` on every node because kube-proxy's iptables rules (for Service DNAT) must fire for Pod-to-Pod traffic crossing the `cbr0`/`cni0` bridge. Without it, Service routing silently breaks.

```bash
# Standard Kubernetes pre-flight check
cat /proc/sys/net/bridge/bridge-nf-call-iptables   # must be 1
lsmod | grep br_netfilter                          # must be loaded
```

---

## NOTRACK and CT Bypass

### What NOTRACK Does

`CT --notrack` (iptables raw table) / `notrack` (nftables raw chain) tells the kernel to **skip conntrack entirely** for matching packets. They are marked `UNTRACKED` and bypass:

- Hash table lookup
- State machine updates
- Timeout refreshes
- Event generation
- NAT application

> [!important] Traffic exempted from conntrack **cannot** use stateful firewall rules (`-m conntrack --ctstate`) or NAT. Ensure your firewall rules account for UNTRACKED traffic explicitly.

### When to Use NOTRACK

#### 1. High-Throughput UDP (DNS, Syslog, Metrics)

DNS servers handling hundreds of thousands of queries per second will create and immediately destroy conntrack entries at the same rate. This is pure overhead.

```bash
# iptables: exempt DNS from conntrack on a nameserver
iptables -t raw -A PREROUTING -p udp --dport 53 -j CT --notrack
iptables -t raw -A OUTPUT     -p udp --sport 53 -j CT --notrack

# nftables equivalent
table inet raw {
    chain prerouting {
        type filter hook prerouting priority raw;
        udp dport 53 notrack
    }
    chain output {
        type filter hook output priority raw;
        udp sport 53 notrack
    }
}
```

#### 2. Loopback Traffic

Loopback traffic is always local and trusted; tracking it wastes table space.

```bash
iptables -t raw -A PREROUTING -i lo -j CT --notrack
iptables -t raw -A OUTPUT     -o lo -j CT --notrack
```

#### 3. Intra-Cluster / Overlay Network Traffic (Kubernetes)

Pod-to-pod traffic within a node or across a VXLAN overlay often does not need per-flow state tracking. Calico, Cilium, and other CNI plugins implement their own flow accounting and may explicitly notrack internal traffic.

#### 4. Syslog, SNMP, IPFIX / NetFlow Collectors

High-volume UDP monitoring traffic follows the same pattern as DNS — short-lived unidirectional flows that generate table churn.

#### 5. Bulk UDP Streaming (Media, Gaming)

```bash
# Exempt RTP media streams (ports 16384-32767) on a media server
iptables -t raw -A PREROUTING -p udp --dport 16384:32767 -j CT --notrack
iptables -t raw -A OUTPUT     -p udp --sport 16384:32767 -j CT --notrack
```

### Accepting UNTRACKED Traffic in Firewall Rules

With NOTRACK applied, a packet in the INPUT chain will have state `UNTRACKED`. You must explicitly allow it:

```bash
# iptables
iptables -A INPUT -m conntrack --ctstate UNTRACKED -p udp --dport 53 -j ACCEPT

# nftables
ct state untracked udp dport 53 accept
```

### Performance Impact

Benchmarks on a DNS resolver handling 500k queries/second show:

- **With conntrack**: 35–40% CPU in softirq (conntrack hash table operations)
- **With NOTRACK**: 8–12% CPU in softirq

This makes NOTRACK the single highest-impact conntrack optimization for UDP-heavy workloads.

---

## Security Considerations and Hardening

### SYN Flood Interaction

Conntrack creates an entry in `SYN_SENT` state upon seeing the **very first SYN**, before the handshake is complete. Under a SYN flood, the conntrack table fills with half-open entries, eventually dropping legitimate traffic with `table full` errors.

**Mitigation strategies:**

```bash
# 1. Reduce SYN_SENT timeout aggressively
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_syn_sent=10

# 2. Enable SYN cookies at the TCP layer (prevents socket queue exhaustion
#    but does not directly limit conntrack table growth)
sysctl -w net.ipv4.tcp_syncookies=1

# 3. Use hashlimit to rate-limit NEW connections before conntrack
iptables -A INPUT -p tcp --syn -m hashlimit \
    --hashlimit-name synflood \
    --hashlimit-above 200/second \
    --hashlimit-burst 1000 \
    --hashlimit-mode srcip \
    -j DROP

# 4. For nftables: rate-limit SYN in the raw chain (before conntrack)
table inet raw {
    chain prerouting {
        type filter hook prerouting priority raw;
        tcp flags syn limit rate over 200/second burst 1000 packets drop
    }
}
```

### Mandatory INVALID Drop

Every stateful firewall **must** explicitly drop INVALID packets:

```bash
# iptables
iptables -A INPUT   -m conntrack --ctstate INVALID -j DROP
iptables -A FORWARD -m conntrack --ctstate INVALID -j DROP
iptables -A OUTPUT  -m conntrack --ctstate INVALID -j DROP

# nftables
ct state invalid drop
```

Failing to do so allows:

- TCP RST injection attacks (attacker sends RST with wrong sequence → `INVALID` → passes through → tears down legitimate connections)
- Fragment-based evasion (out-of-order fragments may be `INVALID`)
- Port-scan fingerprinting (unexpected packets probe firewall behaviour)

### tcp_loose Security Implications

`nf_conntrack_tcp_loose=1` (default):

- Allows picking up mid-flow TCP connections.
- An attacker who can send a data packet that matches an unused tuple can create an ESTABLISHED conntrack entry, bypassing `NEW`-only firewall rules.

If your topology has no asymmetric routing, **set it to 0**:

```bash
sysctl -w net.netfilter.nf_conntrack_tcp_loose=0
```

### tcp_be_liberal Security Implications

`nf_conntrack_tcp_be_liberal=0` (default):

- Out-of-window packets are marked `INVALID`.

Setting it to `1` disables window tracking entirely, which:

- Hides RST injection attacks from conntrack.
- Allows spoofed segments to pass through.

Only set `tcp_be_liberal=1` if you have a specific interoperability problem that requires it.

### Expectation Table Exhaustion

CT helpers insert **expectations** into a separate table. This table has its own limit:

```bash
sysctl net.netfilter.nf_conntrack_expect_max   # default: 256
```

An attacker who can send many valid control-channel messages (e.g., many SIP INVITE packets to port 5060) can exhaust the expectation table, preventing legitimate RELATED connections from being established.

```bash
# Rate-limit new connections to SIP port before the helper sees them
iptables -A INPUT -p udp --dport 5060 -m hashlimit \
    --hashlimit-name sip --hashlimit-above 50/second --hashlimit-mode srcip -j DROP
```

### Logging Invalid and Suspicious Packets

```bash
# Log INVALID packets before dropping (iptables)
iptables -A INPUT -m conntrack --ctstate INVALID \
    -j LOG --log-prefix "CT_INVALID: " --log-level 4
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Enable kernel-level invalid packet logging (logs to dmesg)
sysctl -w net.netfilter.nf_conntrack_log_invalid=6  # 6 = TCP
# Values: 0=off, 1=generic, 6=TCP, 17=UDP, 58=ICMPv6, 255=all
```

### Recommended Hardening Sysctl Set

```ini
# /etc/sysctl.d/99-conntrack-hardening.conf

# Drop invalid packets (enforce in fw rules too)
net.netfilter.nf_conntrack_log_invalid = 255

# No mid-flow pickup on dedicated firewalls
net.netfilter.nf_conntrack_tcp_loose = 0

# Keep window tracking enabled
net.netfilter.nf_conntrack_tcp_be_liberal = 0

# Reduce SYN timeout to limit half-open entry accumulation
net.netfilter.nf_conntrack_tcp_timeout_syn_sent = 10
net.netfilter.nf_conntrack_tcp_timeout_syn_recv = 15

# Disable events if conntrackd not used (reduce attack surface on netlink)
net.netfilter.nf_conntrack_events = 0
```

---

## Conntrack in Containers and Kubernetes

### Network Namespace Isolation

Each Linux **network namespace** (`netns`) has its own independent conntrack table, hash table, and sysctl namespace. This means:

- Docker containers using their own `netns` each have isolated conntrack state.
- `nf_conntrack_max` set in the host `netns` does **not** automatically propagate to container namespaces (since kernel ~4.x with per-netns sysctls).
- Pod-to-pod traffic inside Kubernetes may pass through 2–3 different network namespaces (pod netns → veth → host netns), each potentially running conntrack.

```bash
# Check conntrack table inside a container's namespace
nsenter --net=/var/run/docker/netns/<id> conntrack -L
nsenter --net=/var/run/docker/netns/<id> sysctl net.netfilter.nf_conntrack_max

# Set nf_conntrack_max inside a container netns
nsenter --net=/var/run/docker/netns/<id> \
    sysctl -w net.netfilter.nf_conntrack_max=131072
```

### Docker and conntrack

Docker's `iptables`-based networking relies heavily on conntrack:

- **MASQUERADE** (SNAT) for outbound container traffic uses conntrack to track NAT sessions.
- **DNAT** port forwarding (`-p 8080:80`) uses conntrack for the mapping.
- The `DOCKER` chain in `iptables` populates per-container forwarding rules.

Conntrack entries are created in the **host network namespace**, not the container's namespace, because the NAT/forwarding happens at the host level.

### Kubernetes and kube-proxy

`kube-proxy` (iptables mode) inserts DNAT rules for every `ClusterIP` service. These rules redirect traffic from the ClusterIP to a backing Pod IP. Conntrack tracks each individual session's DNAT mapping.

#### Known Kubernetes Conntrack Issues

**1. UDP DNS conntrack race condition (pre-5.x kernels)**

When a Pod sends multiple DNS queries simultaneously, kube-proxy's DNAT rules can cause conntrack to create conflicting entries (two packets racing to insert entries with the same 5-tuple). This can result in DNS responses being delivered to the wrong socket. Fixed with `net.netfilter.nf_conntrack_tcp_loose` and kernel-level DNAT fixes in 5.x.

Mitigation:

```bash
sysctl -w net.netfilter.nf_conntrack_udp_timeout=10
sysctl -w net.netfilter.nf_conntrack_udp_timeout_stream=10
```

**2. Conntrack table exhaustion in large clusters**

A 1000-node cluster with heavy inter-pod traffic can easily hit the default `nf_conntrack_max`. Each node should have:

```bash
# Recommended for Kubernetes nodes
sysctl -w net.netfilter.nf_conntrack_max=1048576
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=300
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_close_wait=15
sysctl -w net.netfilter.nf_conntrack_udp_timeout=10
sysctl -w net.netfilter.nf_conntrack_udp_timeout_stream=30
```

**3. TIME_WAIT accumulation**

With many short-lived connections (HTTP/1.1 keep-alive disabled, batch jobs), TIME_WAIT entries accumulate rapidly. Reduce the timeout:

```bash
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=15
```

**4. Cilium and conntrack bypass**

Cilium (eBPF-based CNI) implements its own connection tracking in eBPF, **bypassing** Netfilter conntrack for Pod-to-Pod traffic. This requires:

- `kube-proxy` to be disabled (or replaced by Cilium).
- `nf_conntrack` still active for host-level traffic.
- Awareness that `conntrack -L` will not show eBPF-tracked flows.

### Recommended Kubernetes Node Sysctl Baseline

```ini
# /etc/sysctl.d/99-k8s-conntrack.conf
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 300
net.netfilter.nf_conntrack_tcp_timeout_syn_sent = 20
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 15
net.netfilter.nf_conntrack_tcp_timeout_close_wait = 15
net.netfilter.nf_conntrack_tcp_timeout_fin_wait = 30
net.netfilter.nf_conntrack_udp_timeout = 10
net.netfilter.nf_conntrack_udp_timeout_stream = 30
net.netfilter.nf_conntrack_generic_timeout = 60
net.netfilter.nf_conntrack_events = 0
```

---

## Flowtable and Hardware Offload

### Software Flowtable (Fast Path)

A **flowtable** (introduced in Linux 4.16, nftables only) is a hash table in the kernel that provides a **fast path** for already-ESTABLISHED flows, bypassing the full Netfilter hook chain.

```
Normal path (every packet):
  NF_PRE_ROUTING → NF_FORWARD → NF_POST_ROUTING   [all hooks fire]

Flowtable fast path (ESTABLISHED flow):
  NF_INGRESS → flowtable lookup → direct forwarding  [hooks skipped]
```

The fast path fires at the **ingress** hook (priority -300) — earlier than PRE_ROUTING — and forwards the packet directly without passing through the filter, mangle, or nat tables.

#### How a Flow is Offloaded

1. First packets of a flow go through the normal path (NAT, firewall rules).
2. Once the flow is `ESTABLISHED` and `ASSURED`, a rule explicitly adds it to the flowtable: `flow add @ft`.
3. Subsequent packets hit the ingress hook, are matched in the flowtable, and are forwarded in O(1) — no iptables/nftables rule traversal.
4. If the conntrack entry expires or is deleted, the flow is evicted from the flowtable and returns to the normal path.

#### Complete Flowtable Configuration

```nftables
table inet router {

    # Define the flowtable — list the forwarding interfaces
    flowtable ft {
        hook ingress priority -1;
        devices = { eth0, eth1, eth2 };
        # Optional: specify offload type
        # flags offload;   # enable hardware offload (see below)
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        # Offload established TCP/UDP flows
        ip protocol { tcp, udp }  ct state established flow add @ft

        # Normal stateful rules for new connections
        ct state related,established accept
        ct state invalid drop

        # Allow new outbound
        oifname "eth0" ct state new accept
    }
}
```

#### Flowtable Limitations

- Only **IPv4/IPv6 TCP and UDP** flows can be offloaded (no SCTP, ICMP, GRE).
- **NAT** is supported inside flowtables since Linux 5.3.
- Conntrack entries for offloaded flows are **frozen** (timeout does not advance) until the flow is evicted — this prevents premature timeout of active flows.
- PPPoE and VLAN tagged traffic require the relevant interface to be listed in `devices`.

---

### Hardware Offload (NIC-level)

Since Linux 5.3, flowtables support full **hardware offload**: the kernel programs flow tables directly into NIC hardware (ASICs, SmartNICs), bypassing the CPU entirely for packet forwarding.

#### Supported Hardware

|Vendor / Driver|Notes|
|---|---|
|Mellanox / `mlx5`|Full flowtable offload, widely deployed|
|Netronome / `nfp`|SmartNIC with full offload|
|Marvell / `prestera`|Switch-chip offload|
|Broadcom / `bnxt_en`|Partial support|
|TC flower (`cls_flower`)|Generic TC-based offload path|

#### Enabling Hardware Offload

```nftables
flowtable ft {
    hook ingress priority -1;
    devices = { eth0, eth1 };
    flags offload;    # <-- enable HW offload
}
```

```bash
# Verify offload is active (shows IPS_OFFLOAD flag)
conntrack -L | grep OFFLOAD

# Check NIC capabilities
ethtool -k eth0 | grep -E 'tc-skbedit|flow-classification'
```

#### tc flower + conntrack (Alternate HW Offload Path)

For drivers that support `tc flower` but not the nftables flowtable offload API, you can use `tc` with conntrack marks:

```bash
# Mark established flows with a conntrack mark
nftables: ct mark set 0x1 (when ct state established)

# Offload matching flows to hardware via tc flower
tc qdisc add dev eth0 ingress
tc filter add dev eth0 ingress \
    protocol ip flower \
    ct_state +est+trk \
    action mirred egress redirect dev eth1
```

#### Software vs Hardware Flowtable — Performance

|Mode|CPU per Gbps (approx.)|Max throughput|
|---|---|---|
|Full Netfilter (no flowtable)|~1 core / 10 Gbps|CPU-bound|
|Software flowtable|~1 core / 40–80 Gbps|Memory bandwidth|
|Hardware offload (Mellanox)|~0 (CPU-free)|Line rate (100+ Gbps)|

---

## conntrackd Internals

### Overview

`conntrackd` keeps conntrack tables synchronised between two or more nodes in an HA cluster, so that when a failover occurs, active sessions continue without resetting.

```
┌─────────────────┐         UDP sync         ┌─────────────────┐
│   Primary node  │ ──────────────────────► │  Backup node    │
│  (ACTIVE)       │ ◄──────────────────────  │  (STANDBY)      │
│  conntrackd     │                          │  conntrackd     │
└─────────────────┘                          └─────────────────┘
        │                                            │
  VIP: 10.0.0.1                             (no traffic normally)
```

### Sync Modes

#### FTFW (Fault Tolerant Flow Watching) — Recommended

FTFW uses an **event-driven, acknowledged** protocol:

- The primary sends conntrack events (NEW, UPDATE, DESTROY) over UDP.
- The backup acknowledges received messages.
- Unacknowledged messages are **retransmitted** (up to `ResendQueueSize` entries).
- On primary failure, the backup applies its buffered events and takes over with minimal state loss.

```
Sync {
    Mode FTFW {
        ResendQueueSize 131072    # max unacked messages in queue
        PurgeTimeout    180       # evict unsynced entries after N seconds
        CommitTimeout   180       # how long to wait before committing on startup
        DisableExternalCache off  # cache sync events in RAM (recommended on)
    }
}
```

#### ALARM Mode — Simple, No Acknowledgement

ALARM sends **periodic full dumps** of the conntrack table rather than incremental events. Simpler but higher bandwidth and less consistent:

- Sends full table every `RefreshTime` seconds.
- No acknowledgement; backup replaces its table with each dump.
- On failover, state is accurate to within `RefreshTime` seconds.

```
Sync {
    Mode ALARM {
        RefreshTime 15       # resend all entries every 15 s
        CacheTimeout 180     # entries expire in backup if not refreshed
    }
}
```

#### notrack Mode

For testing or scenarios where only cache inspection is needed, `notrack` mode subscribes to events and builds a local cache without sending to any peer.

### Transport Options

```
# Unicast (recommended for 2-node clusters)
UDP {
    IPv4_address 192.168.100.1
    IPv4_Destination_Address 192.168.100.2
    Port 3780
    Interface eth1
    Checksum on
    SndSocketBuffer 1249280
    RcvSocketBuffer 1249280
}

# Multicast (for N-node clusters)
Multicast {
    IPv4_address 225.0.0.50
    Group 3780
    TTL 1
    Interface eth1
    Checksum on
}
```

### Failover Integration with Keepalived

```bash
# /etc/keepalived/keepalived.conf (primary)
vrrp_sync_group G1 {
    group { VI_1 }
    notify_master "/usr/sbin/conntrackd -C /etc/conntrackd/conntrackd.conf -B"
    notify_backup "/usr/sbin/conntrackd -C /etc/conntrackd/conntrackd.conf -B"
    notify_fault  "/usr/sbin/conntrackd -C /etc/conntrackd/conntrackd.conf -B"
}
```

The `-B` flag tells `conntrackd` to send a **bulk update** (full table dump) to the peer — triggered on every VRRP state transition.

### Failover Sequence (FTFW mode)

```
T=0   Primary running, backup synced via FTFW events
T=1   Primary fails (link down / kernel panic)
T=2   Keepalived detects failure (dead interval ~3 s)
T=3   Backup promotes to MASTER, takes VIP
T=4   conntrackd on backup enters COMMIT phase:
        - Replays buffered events from ResendQueue
        - Injects entries into local kernel conntrack table
T=5   New packets arrive at backup, matched in conntrack → sessions survive
```

### State Consistency Guarantees

|Event|FTFW|ALARM|
|---|---|---|
|Entry created before failure|Synced within 1 RTT|Synced within `RefreshTime`|
|Entry updated (timeout refresh)|Synced (UPDATE event)|Re-synced on next dump|
|Entry destroyed before failover|Synced (DESTROY event)|May linger until CacheTimeout|
|Entries during failover window|May be lost (queue depth)|Lost since last dump|

### conntrackd Operational Commands

```bash
# Show daemon statistics
conntrackd -s

# Show the internal cache (what conntrackd knows)
conntrackd -i   # internal (kernel) cache
conntrackd -e   # external (peer) cache

# Force a bulk commit to the kernel (restore after maintenance)
conntrackd -R

# Send a bulk update to all peers
conntrackd -B

# Flush the external cache
conntrackd -F ext

# Check configuration file
conntrackd -C /etc/conntrackd/conntrackd.conf -d
```

---

_Sources: Linux kernel documentation (`Documentation/networking/nf_conntrack-sysctl.rst`), `man 8 conntrack`, `man 8 iptables-extensions`, nftables wiki, Kubernetes networking docs, Calico documentation._