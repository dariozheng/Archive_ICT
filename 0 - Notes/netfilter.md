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

# Netfilter Conntrack — Connection Tracking

> [!abstract] Summary 
> **Conntrack** (connection tracking) is a subsystem of the Linux kernel's **Netfilter** framework. It keeps a stateful record of every active network flow passing through the system, enabling firewalls, NAT, and other network services to make decisions based on the full context of a connection — not just individual packets.

---

## Table of Contents

- [[#1. Architecture Overview]]
- [[#2. How Connection Tracking Works]]
- [[#3. Connection States]]
- [[#4. The Conntrack Entry (ct object)]]
- [[#5. Netfilter Hooks]]
- [[#6. NAT Integration]]
- [[#7. Connection Tracking Helpers (ALGs)]]
- [[#8. Conntrack Zones]]
- [[#9. Conntrack Tools and Commands]]
- [[#10. /proc and /sys Interfaces]]
- [[#11. Kernel Parameters and Tuning]]
- [[#12. Events and Logging (NFLOG / conntrack-tools)]]
- [[#13. Conntrack in iptables and nftables]]
- [[#14. Common Issues and Troubleshooting]]

---

## 1. Architecture Overview

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

| Module                 | Purpose                               |
| ---------------------- | ------------------------------------- |
| `nf_conntrack`         | Core connection tracking engine       |
| `nf_conntrack_ipv4`    | IPv4 conntrack support                |
| `nf_conntrack_ipv6`    | IPv6 conntrack support                |
| `nf_conntrack_ftp`     | FTP ALG helper                        |
| `nf_conntrack_sip`     | SIP/VoIP ALG helper                   |
| `nf_conntrack_h323`    | H.323 ALG helper                      |
| `nf_conntrack_tftp`    | TFTP ALG helper                       |
| `nf_conntrack_irc`     | IRC DCC ALG helper                    |
| `nf_conntrack_netlink` | Userspace communication via nfnetlink |
| `nf_nat`               | NAT core (depends on conntrack)       |

---

## 2. How Connection Tracking Works

### 2.1 Packet Flow and Tuple Matching

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

### 2.2 Bidirectional Tracking

Each conntrack entry tracks **both directions** of a flow:

```
ORIGINAL direction:   client → server   (e.g., 10.0.0.1:54321 → 1.2.3.4:80)
REPLY direction:      server → client   (e.g., 1.2.3.4:80 → 10.0.0.1:54321)
```

Both tuples (original + reply) are stored in the same entry. This is how NAT information is preserved: the reply tuple is rewritten if NAT is applied.

### 2.3 Timeout and Eviction

Each entry has a **timeout** specific to its protocol and state. When the timer expires and no packets have refreshed it, the entry is removed.

| Protocol / State | Typical Default Timeout |
| ---------------- | ----------------------- |
| TCP ESTABLISHED  | 5 days (432000 s)       |
| TCP TIME_WAIT    | 120 s                   |
| TCP CLOSE        | 10 s                    |
| TCP SYN_SENT     | 120 s                   |
| TCP FIN_WAIT     | 120 s                   |
| UDP stream       | 180 s                   |
| UDP unreplied    | 30 s                    |
| ICMP             | 30 s                    |
| Generic          | 600 s                   |

> [!note] Timeouts can be customized per-protocol and are accessible via `/proc/sys/net/netfilter/` or `sysctl`.

---

## 3. Connection States

These are the states a conntrack entry can be in. These states are **independent from TCP states** — they are Netfilter's own abstraction applied across all protocols.

### States Table

| State         | Description                                                                                                           |
| ------------- | --------------------------------------------------------------------------------------------------------------------- |
| `NEW`         | First packet of a flow; no reply seen yet.                                                                            |
| `ESTABLISHED` | Bidirectional traffic observed; the reply packet has been seen.                                                       |
| `RELATED`     | A new connection related to an existing `ESTABLISHED` one (e.g., FTP data channel, ICMP error). Requires a CT helper. |
| `INVALID`     | Packet does not match any known connection and cannot be identified as starting a new one. Usually dropped.           |
| `UNTRACKED`   | The packet has explicitly been marked to bypass conntrack (via `NOTRACK`/`CT --notrack`).                             |
| `SNAT`        | Virtual state used in iptables rules: entry has SNAT applied.                                                         |
| `DNAT`        | Virtual state used in iptables rules: entry has DNAT applied.                                                         |

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

> [!warning] 
> INVALID packets Packets hitting the `INVALID` state should almost always be **dropped** explicitly with a firewall rule. Passing them through can cause security issues and confuse the state machine.

---

## 4. The Conntrack Entry (ct object)

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

| Flag             | Meaning                                                 |
| ---------------- | ------------------------------------------------------- |
| `IPS_EXPECTED`   | Entry was expected (by a CT helper)                     |
| `IPS_SEEN_REPLY` | A reply packet has been received                        |
| `IPS_ASSURED`    | Entry is safe to keep (won't be evicted under pressure) |
| `IPS_CONFIRMED`  | Entry has been inserted into the hash table             |
| `IPS_SRC_NAT`    | Source NAT applied                                      |
| `IPS_DST_NAT`    | Destination NAT applied                                 |
| `IPS_SEQ_ADJUST` | Sequence number adjustment active (for NAT on TCP)      |
| `IPS_DYING`      | Entry is being removed                                  |
| `IPS_OFFLOAD`    | Flow offloaded to hardware (flowtable)                  |

---

## 5. Netfilter Hooks

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

| Hook                   | Priority            | Action                                    |
| ---------------------- | ------------------- | ----------------------------------------- |
| `NF_INET_PRE_ROUTING`  | `-200` (very early) | Lookup + create unconfirmed entry         |
| `NF_INET_LOCAL_OUT`    | `-200`              | Lookup + create unconfirmed entry         |
| `NF_INET_POST_ROUTING` | `MAX` (very late)   | **Confirm** the entry (insert into table) |
| `NF_INET_LOCAL_IN`     | `MAX`               | **Confirm** the entry                     |

> [!important] Confirmation Entries are created **unconfirmed** at PRE_ROUTING/LOCAL_OUT and only become visible in the hash table after **confirmation** at POST_ROUTING/LOCAL_IN. This avoids inserting entries for packets that are later dropped by firewall rules.

---

## 6. NAT Integration

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

## 7. Connection Tracking Helpers (ALGs)

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

## 8. Conntrack Zones

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

## 9. Conntrack Tools and Commands

The `conntrack` userspace tool (from the `conntrack-tools` package) lets you inspect and manipulate the kernel's conntrack table.

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

## 10. /proc and /sys Interfaces

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
|`nf_conntrack_buckets`|Number of hash table buckets (read-only, set at module load)|
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

## 11. Kernel Parameters and Tuning

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

## 12. Events and Logging (conntrackd)

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

## 13. Conntrack in iptables and nftables

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

## 14. Common Issues and Troubleshooting

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

**Solution:** Enable flowtable offloading (see [[#11. Kernel Parameters and Tuning]]):

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