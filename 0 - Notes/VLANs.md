---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - ccnp
  - claude
  - encor/switching
  - category/networking/networking_general
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-07-15
aliases:
  - VLAN
---
_A VLAN turns one physical switch into several isolated broadcast domains. Trunking carries many of those domains over one link. Inter-VLAN [[Routing|routing]] is the only sanctioned way back across the boundaries a VLAN creates._

A switch, left alone, is one flat <strong>broadcast domain</strong>: every port can reach every other port, and a broadcast from any host is flooded to all of them. 

A <strong>VLAN</strong> (Virtual LAN) <strong>partitions that single switch into several independent Layer-2 domains</strong>, each with its own broadcast scope, as if the ports had been split across separate physical switches that share no wire.

Three mechanisms make this work, and they map onto the three parts of this note:

- Ports are assigned to a VLAN. Traffic in one VLAN never reaches another at Layer 2 — see [[#Access Ports|access ports]].
- A single link can carry many VLANs between switches, by tagging each frame with its VLAN number — see [[#Trunk Ports|trunk ports]] and the [[#The 802.1Q Tag|802.1Q tag]].
- Because VLANs are separate Layer-2 domains, moving a packet from one to another is a routing operation, not a switching one — see [[#Inter-VLAN Routing|inter-VLAN routing]].

Everything else is detail on top of those three ideas: how the tag is built, how switches decide whether to trunk, how the boundary is crossed efficiently, and where the whole scheme can be attacked.

> [!info] Layer 2 versus Layer 3, kept straight 
> A VLAN is a Layer-2 construct — it defines a broadcast domain. A subnet is a Layer-3 construct — it defines an IP address range. They are different things, but in almost every real design they are mapped one-to-one: one VLAN carries exactly one subnet. The mapping is a convention, not a requirement, and keeping the two ideas distinct is what makes inter-VLAN routing comprehensible.

---

## What a VLAN Is

_A VLAN is a broadcast domain defined in switch software rather than by physical cabling. Its identity is a number from 1 to 4094 carried in the frame, not in the wire._

### The Broadcast Domain

The defining property of a VLAN is broadcast containment. A broadcast, an unknown-unicast flood, or a multicast sent by a host in VLAN 10 is delivered only to other ports in VLAN 10. Ports in VLAN 20 never see it. This is the same isolation that separate physical switches would give, achieved by tagging and filtering inside one switch.

Two consequences follow immediately, and they are the reason VLANs exist:

- Smaller broadcast domains. Broadcast traffic scales with domain size; splitting a large flat network into VLANs caps how far any broadcast storm can spread.
- Segmentation independent of location. Hosts on the same VLAN can be plugged into different switches in different rooms and still share one broadcast domain, while two hosts in the same rack can be kept in different VLANs.

### VLAN Membership

Membership — which VLAN a given frame belongs to — is decided when the frame enters the switch, by one of two methods:

- <strong>Port-based</strong> (∫). The port is configured to belong to a VLAN, and every untagged frame arriving on it is assigned to that VLAN. This is the overwhelmingly common case and is what an [[#Access Ports|access port]] does.
- <strong>Dynamic</strong>. The VLAN is chosen per-endpoint at authentication time, by a policy server, and pushed to the port. This is how [[#Dynamic VLAN Assignment|802.1X/RADIUS assignment]] works, and it is what a NAC deployment relies on.

MAC-based and protocol-based membership also exist historically, but on modern enterprise gear dynamic assignment is done through authentication rather than static MAC-to-VLAN tables.

### The VLAN Database

On a Cisco switch, VLANs must exist in the switch's VLAN database before a port can be assigned to them. A VLAN is created and named:

```cisco
vlan 10
 name USERS
vlan 20
 name VOICE
```

A port referencing a VLAN that does not exist in the database will not pass that VLAN's traffic. This is a common and silent cause of an apparently inert port. The database is also what an [[#SVI (Switch Virtual Interface) Model|SVI]] checks when deciding whether to come up.

---

## The 802.1Q Tag

_The 4-byte field that carries VLAN identity inside an Ethernet frame. Every trunking decision, the native VLAN, the MTU cost, and the double-tagging attack all follow from its structure._

A standard Ethernet frame has no field for a VLAN number. IEEE 802.1Q defines one by inserting four bytes into the frame, immediately after the source MAC address and before the EtherType. This is the mechanism that makes a [[#Trunk Ports|trunk]] possible: it is what lets a single link carry frames from many VLANs and still have the far end sort them correctly.

### Tag Structure

The inserted tag is 4 bytes, split into two 2-byte halves — the TPID and the TCI:

```
┌───────────────────────────────────────────────────────────────────┐
│                        802.1Q tag: 4 bytes                        │
├──────────────────────────┬────────────────────────────────────────┤
│     TPID  (16 bits)      │             TCI  (16 bits)             │
│          0x8100          │  ┌────────┬─────┬───────────────────┐  │
│                          │  │  PCP   │ DEI │        VID        │  │
│                          │  │ 3 bits │ 1 b │      12 bits      │  │
│                          │  └────────┴─────┴───────────────────┘  │
└──────────────────────────┴────────────────────────────────────────┘
```

Its position in the frame:

```
untagged:   [ dst MAC ][ src MAC ][ EtherType ][ payload … ]
                                   ▲
                                   │ 802.1Q inserts 4 bytes here
                                   ▼
tagged:     [ dst MAC ][ src MAC ][ 0x8100 ][ TCI ][ EtherType ][ payload … ]
```

Because the TPID sits exactly where the EtherType would be in an untagged frame, a receiver that reads `0x8100` there knows the next two bytes are tag control information rather than the start of the payload, and that the real EtherType follows the tag.

#### TPID — Tag Protocol Identifier

The first 2 bytes. For standard 802.1Q it is always `0x8100`. Its only job is to flag the frame as tagged. Provider-bridging (QinQ, 802.1ad) uses `0x88A8` in the outer tag while the inner tag stays `0x8100`; that is out of scope here but explains why the value is worth recognising.

#### TCI — Tag Control Information

The second 2 bytes, subdivided into three fields:

|Field|Bits|Purpose|
|---|---|---|
|PCP — Priority Code Point|3|Layer-2 class of service (802.1p). Eight priority levels, 0–7. Higher is preferred under congestion; voice is typically marked 5.|
|DEI — Drop Eligible Indicator|1|Marks the frame as preferentially droppable when a queue is congested. Formerly the CFI bit in older revisions.|
|VID — VLAN Identifier|12|The VLAN number the frame belongs to. This is the field that matters for segmentation.|

The 3-bit PCP field is the reason a trunk can carry QoS markings between switches. The [[#The Voice VLAN|voice VLAN]] relies on it directly.

### Why VLAN Numbers Stop at 4094

The VID is 12 bits, so it can express 2¹² = 4096 values. Two are reserved by the standard:

- `0` — means "no VLAN, priority-tagged only." A frame with VID 0 carries a PCP value but no VLAN membership.
- `4095` — reserved for implementation use.

That leaves 1–4094 as assignable VLAN IDs — 4094 usable values. This ceiling is a hard property of the 12-bit field, and it is one of the motivations for [[VXLAN]] in large multi-tenant fabrics, where a 24-bit identifier replaces the 12-bit VID.

### The MTU Cost

Inserting 4 bytes into every tagged frame raises the frame size. The classic Ethernet payload of 1500 bytes plus a 14-byte header plus the 4-byte tag gives a tagged frame of 1518 bytes excluding the frame check sequence — the exact constants the Linux kernel encodes as `VLAN_HLEN` (4), `VLAN_ETH_HLEN` (18) and `VLAN_ETH_FRAME_LEN` (1518).

The operational consequence: a device that must carry tagged frames at full 1500-byte payload needs to accept a slightly larger frame on the wire. Switch trunk ports do this transparently, but any host or router terminating a tag — and especially any tunnel stacked on top — must have its MTU accounted for, or large frames are dropped or fragmented. This is the same MTU bookkeeping that a [[#Linux VLANs|Linux VLAN sub-interface]] enforces in software.

---

## Access Ports

_A port that belongs to exactly one VLAN and speaks to ordinary untagged hosts. It removes all knowledge of VLANs from the endpoint._

An access port carries the traffic of a single VLAN and connects to an end device — a workstation, a printer, a server — that has no concept of VLAN tagging. The port hides tagging entirely:

- On ingress, an untagged frame from the host is internally associated with the port's access VLAN.
- On egress toward the host, any internal VLAN association is removed, so the host always receives a plain untagged frame.

Configuration is a single VLAN assignment:

```cisco
interface GigabitEthernet1/0/5
 switchport mode access
 switchport access vlan 10
```

Beyond assigning the VLAN, the `switchport mode access` line has a second and frequently overlooked effect: it disables [[#Dynamic Trunking Protocol (DTP)|DTP]] on the port, so that the port cannot negotiate itself into a trunk. This is a security property rather than a matter of convention: a statically configured access port cannot be converted into a trunk by a neighbouring device.

### The Voice VLAN

A special case: a port can carry one data VLAN untagged for a PC and one voice VLAN tagged for an IP phone daisy-chained through it. The phone tags its own traffic; the PC behind the phone stays untagged.

```cisco
interface GigabitEthernet1/0/5
 switchport mode access
 switchport access vlan 10
 switchport voice vlan 20
```

This is not a trunk — it is an access port with a specific two-VLAN exception for the phone, and the PCP markings the phone sets are honoured for voice priority.

---

## Trunk Ports

_A port that carries many VLANs over one link by tagging each frame. Trunks connect switches to switches, switches to routers, and switches to hypervisors._

Where an access port serves one VLAN toward one host, a trunk carries the traffic of many VLANs over a single physical link between infrastructure devices. It does this by applying the [[#The 802.1Q Tag|802.1Q tag]] to every frame as it leaves — so the far end can read the VID and place the frame back into the correct VLAN — with the single exception of the [[#The Native VLAN|native VLAN]].

```cisco
interface GigabitEthernet1/0/1
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30
```

### Tagging on a Trunk

The treatment a trunk applies to a frame is defined precisely as follows:

- Egress, VLAN is not the native VLAN → the frame is tagged with its VID.
- Egress, VLAN is the native VLAN → the frame is sent untagged.
- Ingress, frame is tagged → it is placed in the VLAN named by the tag.
- Ingress, frame is untagged → it is placed in the native VLAN.

The final pair constitutes the entire basis of both the native VLAN's utility and its risk.

### The Allowed VLAN List

By default a trunk will carry every VLAN that exists on the switch. Restricting it is both a scaling and a security measure — it limits how far broadcast domains extend and shrinks the attack surface:

```cisco
interface GigabitEthernet1/0/1
 switchport trunk allowed vlan 10,20,30
 switchport trunk allowed vlan add 40
```

Only the VLANs listed traverse the trunk. A VLAN that is not in the allowed list is pruned from that link entirely, and — relevant to routing — its SVI will not count that trunk toward staying up.

### The Native VLAN

_The one VLAN on a trunk whose frames cross untagged. Convenient for legacy interoperability, and the pivot of the double-tagging attack._

Every 802.1Q trunk has exactly one native VLAN. Frames belonging to it are sent across the trunk without a tag, and any untagged frame received on the trunk is assumed to belong to it. The default native VLAN is VLAN 1.

```cisco
interface GigabitEthernet1/0/1
 switchport trunk native vlan 999
```

The native VLAN exists so that a trunk can interoperate with a device that transmits untagged frames. It presents two failure modes that must be designed against:

- Native VLAN mismatch. If the two ends of a trunk disagree on the native VLAN, untagged frames are silently placed into different VLANs on each side, merging two broadcast domains. CDP will usually log the mismatch, but traffic leaks regardless.
- It is the entry point for [[#Double-Tagging|double-tagging]]. Because native-VLAN frames are untagged on the trunk, an attacker in the native VLAN can hide a second tag inside the frame that the first switch never inspects.

The standard hardening is to set the native VLAN to an unused, dedicated VLAN that carries no hosts, and — on newer platforms — to tag it explicitly with `vlan dot1q tag native`, which removes the untagged behaviour that the attack depends on.

---

## Dynamic Trunking Protocol (DTP)

_Cisco's proprietary mechanism for negotiating whether a link becomes a trunk. Convenient, non-standard, and a security liability where left enabled._

DTP is a Cisco protocol that lets two switch ports negotiate, automatically, whether the link between them becomes a trunk. Each port advertises a mode, and the combination of the two modes decides the outcome. It removes manual configuration, at the cost of letting the network form trunks on its own.

### Switchport Modes

The `switchport mode` command sets the administrative mode that drives negotiation:

|Mode|Behaviour|
|---|---|
|`access`|Never trunks. Actively disables DTP on the port.|
|`trunk`|Forces trunking. Still sends DTP frames as a courtesy unless silenced.|
|`dynamic auto`|Will trunk only if the other side asks. Passive.|
|`dynamic desirable`|Actively tries to form a trunk.|

The default administrative mode on most modern Catalyst platforms is `dynamic auto`, though some older platforms defaulted to `dynamic desirable`. The exact default varies by model, so it should be checked rather than assumed.

### The Negotiation Matrix

The combinations that result in a trunk:

||access|dynamic auto|dynamic desirable|trunk|
|---|---|---|---|---|
|access|no|no|no|no|
|dynamic auto|no|no|trunk|trunk|
|dynamic desirable|no|trunk|trunk|trunk|
|trunk|no|trunk|trunk|trunk|

Two entries in this table account for most operational failures:

- auto + auto = no trunk. Two ports each waiting to be solicited never form a trunk. Connecting two default-configured switches therefore yields an access link on VLAN 1 rather than the expected trunk.
- A dynamic mode facing an attacker. A port left in a dynamic mode will form a trunk with any device that solicits one, including a host running DTP. This is [[#Switch Spoofing|switch spoofing]].

### Disabling DTP

On a production network, DTP should be off. There are two ways, and one subtlety:

```cisco
interface GigabitEthernet1/0/1
 switchport mode trunk
 switchport nonegotiate
```

- `switchport nonegotiate` stops the port sending or responding to DTP frames. It is only accepted on a port that is statically `access` or `trunk`; a dynamic port rejects it, because a dynamic port must run DTP to decide its mode.
- `switchport mode access` also disables DTP, as noted for access ports.

The recommended posture for a switch-to-switch link is to configure `switchport mode trunk` explicitly and add `switchport nonegotiate` — the trunk is forced, and no negotiation can change it. This is exactly the intent of the [[PBA - NAC - Network Access Devices#Trunk / Uplink Policy — `Disable_DT_Trunk`|trunk-uplink policy]] used on the NAC access switches.

---

## VLAN Numbering

_The number space is divided into a normal range and an extended range, with a small set of reserved values. Design conventions are of greater practical consequence than the raw limits._

### Normal and Extended Ranges

|Range|IDs|Notes|
|---|---|---|
|Reserved (low)|0|Priority-tagging only, never a real VLAN.|
|Normal|1 – 1005|1002–1005 are reserved for legacy Token Ring and FDDI. VLAN 1 is the default.|
|Extended|1006 – 4094|Fully usable on modern switches.|
|Reserved (high)|4095|Implementation-reserved.|

The normal/extended split is historical — extended VLANs once required a different storage mode (transparent VTP) — but on current platforms both ranges are freely usable.

### VLAN 1 Is Special and Should Be Empty

VLAN 1 is the default for everything: the default access VLAN, the default native VLAN, and the VLAN that control-plane protocols (CDP, DTP, VTP, PAgP) use. It cannot be deleted. Precisely because everything lands there by default, no user traffic should. The hardening conventions are:

- Move the native VLAN off VLAN 1.
- Assign every access port to a real, purpose-built VLAN, never leaving it on 1.
- Prune VLAN 1 from trunks where it is not needed.

### Designing the Numbering Plan

VLAN numbers are plentiful and are read by operators, so meaning should be encoded within them. A workable convention aligns the VLAN number with the third octet of its subnet, so that `VLAN 20 → 10.0.20.0/24` is immediately legible. The addressing side of this is covered in the subnetting note under [[Subnetting#Encode Meaning in the Address|encoding meaning in the address]]; the one-VLAN-one-subnet mapping is what lets the two numbering schemes reinforce each other.

---

## Inter-VLAN Routing

_VLANs are isolated Layer-2 domains by definition, so any traffic between them must be routed. Three models do this, trading cost against performance._

A VLAN is a broadcast domain; a host in VLAN 10 cannot reach a host in VLAN 20 at Layer 2, by design. The moment two VLANs must communicate, a Layer-3 device has to route between them — receive the frame from the source VLAN, make a routing decision, and forward it into the destination VLAN. There are three ways to provide that device, and they are listed in the order the industry adopted and then largely abandoned the first.

### Router-on-a-Stick

_One router, one trunk, one sub-interface per VLAN. Simple and inexpensive, but constrained by the throughput of the single link._

The oldest model uses an external router connected to the switch by a single trunk. The router's physical interface is divided into logical sub-interfaces, one per VLAN, each tagged with that VLAN's ID and each holding the IP address that will serve as that VLAN's default gateway.

```cisco
interface GigabitEthernet0/0.10
 encapsulation dot1Q 10
 ip address 10.0.10.1 255.255.255.0
interface GigabitEthernet0/0.20
 encapsulation dot1Q 20
 ip address 10.0.20.1 255.255.255.0
```

A frame from VLAN 10 to VLAN 20 travels up the trunk tagged for VLAN 10, arrives at sub-interface `.10`, is routed to sub-interface `.20`, and returns down the same trunk tagged for VLAN 20.

- Strength: requires only one router interface and one switch port. Inexpensive and readily understood.
- Weakness: every inter-VLAN packet crosses the single trunk twice — in on one tag, out on another — so the one link is a hard bandwidth ceiling and a single point of failure. This is why the model is now confined to small sites and lab work.

> [!note] The `encapsulation dot1Q` line is doing the tagging 
> On a router sub-interface, `encapsulation dot1Q 10` is what ties that sub-interface to VLAN 10's tag. Frequently, the native VLAN's sub-interface is written `encapsulation dot1Q 1 native` so the router expects it untagged, mirroring the switch's native VLAN behaviour.

### SVI (Switch Virtual Interface) Model

_The Layer-3 switch routes internally between virtual VLAN interfaces at hardware speed. The standard enterprise design._

A multilayer (Layer-3) switch can route between VLANs itself, with no external router and no trunk bottleneck, because the routing happens in the switch's own forwarding hardware. Each VLAN is given a Switch Virtual Interface — a virtual routed interface named for the VLAN — that holds the gateway IP for that VLAN.

```cisco
ip routing
!
interface Vlan10
 ip address 10.0.10.1 255.255.255.0
interface Vlan20
 ip address 10.0.20.1 255.255.255.0
```

The global `ip routing` line is mandatory — without it the switch has SVIs but will not route between them.

- Strength: routing is done in ASICs at line rate, with no trunk to saturate. Scales to as many VLANs as the platform supports.
- Weakness: requires Layer-3-capable (and more expensive) switch hardware.

This is the model a NAC access layer assumes: authenticated endpoints land in a data VLAN whose SVI is the gateway, and the same switch routes them onward.

#### SVI Up/Down Behaviour

An SVI is not necessarily up merely because it is configured. It is subject to autostate: the SVI's line protocol comes up only when the conditions for the VLAN to be genuinely active are satisfied. Three requirements must hold simultaneously:

- The VLAN exists and is active in the [[#The VLAN Database|VLAN database]].
- At least one physical port is in that VLAN (an access port in it, or a trunk that allows it).
- That port is in the spanning-tree forwarding state for the VLAN.

The practical consequence is significant: an SVI may remain `up/down` despite a correct IP address, solely because no access port or allowed trunk is carrying its VLAN in a forwarding state. The routed interface then never appears in the routing table, and the fault presents as an unroutable subnet with no apparent misconfiguration. The override, `switchport autostate exclude`, removes a port from the calculation; it is used, for example, to prevent a monitoring port from holding an SVI up on its own.

### Routed Ports

_A physical switch port taken out of Layer 2 entirely and given an IP address, for point-to-point links between Layer-3 devices._

The third model is not about routing between local VLANs at all, but about the links that carry already-routed traffic onward. A physical port on a Layer-3 switch can be removed from switching entirely and made a routed interface with its own IP address, exactly like a router's interface.

```cisco
interface GigabitEthernet1/0/24
 no switchport
 ip address 10.255.0.1 255.255.255.252
```

The `no switchport` line converts the port from Layer 2 to Layer 3. It belongs to no VLAN, participates in no spanning tree, and typically carries a /30 or /31 point-to-point link to another router or Layer-3 switch — the uplinks in the [[Subnetting#Allocate Hierarchically|hierarchical addressing plan]]. A routed port is the counterpart to an SVI: the SVI routes for a VLAN full of hosts, the routed port routes across a link between infrastructure devices.

---

## Linux VLANs

_The same 802.1Q tagging, expressed as kernel sub-interfaces and bridge VLAN filtering. The concepts map directly onto the switch model; only the syntax changes._

A Linux host is a fully capable 802.1Q participant. It can terminate tagged traffic on VLAN sub-interfaces, and it can act as a VLAN-aware switch through the bridge's VLAN filtering — the same two roles as a router sub-interface and a switch, respectively. This is directly relevant wherever a Linux box sits on a trunk, as a router, firewall, or [[Hypervisors|hypervisor]].

### VLAN Sub-Interfaces

The direct analogue of a [[#Router-on-a-Stick|router-on-a-stick]] sub-interface. A VLAN sub-interface is stacked on a physical NIC and handles one VLAN's tagged traffic:

```bash
# create eth0.10 carrying VLAN 10
ip link add link eth0 name eth0.10 type vlan id 10
ip addr add 10.0.10.1/24 dev eth0.10
ip link set eth0.10 up
```

The parent `eth0` carries the trunk; `eth0.10` sees only VLAN 10, already de-tagged. This is how a Linux router routes between VLANs, and how a hypervisor host presents a specific VLAN to a virtual machine.

> [!warning] The sub-interface MTU is capped by the parent 
> The kernel will not let a VLAN sub-interface have an MTU larger than its parent minus the tag overhead where the driver cannot absorb it — the `netif_reduces_vlan_mtu` check subtracts `VLAN_HLEN` (4 bytes). If tagged traffic at full 1500-byte payload must pass, the parent interface's MTU has to be raised to accommodate the tag, or large frames are silently dropped. This is the software face of the [[#The MTU Cost|MTU cost]] described above.

### Bridge VLAN Filtering

The analogue of the switch itself. A Linux bridge with `vlan_filtering` enabled becomes a VLAN-aware switch: ports carry PVIDs and tagged/untagged egress rules exactly like switch access and trunk ports.

```bash
ip link add br0 type bridge vlan_filtering 1
ip link set eth1 master br0
# eth1 as an access port in VLAN 10 (PVID + untagged egress)
bridge vlan add dev eth1 vid 10 pvid untagged
# eth2 as a trunk carrying VLANs 10 and 20
bridge vlan add dev eth2 vid 10
bridge vlan add dev eth2 vid 20
```

The vocabulary lines up one-to-one with the switch model:

- `pvid` on a port is the native VLAN equivalent — untagged ingress is assigned to it. The kernel's default bridge PVID is 1, mirroring the default VLAN 1.
- `untagged` on egress makes the port behave as an access port for that VLAN — the tag is stripped on the way out.
- A port with several tagged VIDs and no untagged flag is a trunk.

---

## VLAN Security

_VLANs isolate by policy rather than by physical separation. Two well-known attacks defeat inadequately hardened configurations, and both are closed by the same small set of settings._

VLAN separation is enforced by switch software, so a misconfiguration — or a protocol left in its permissive default — can let traffic cross a boundary that the design assumed was solid. Two attacks are the canonical demonstrations, and understanding them justifies the hardening conventions cited throughout this note.

### Switch Spoofing

The attacker's port faces a switch port left in a dynamic DTP mode. The attacker runs DTP and negotiates a trunk with the switch. Once the link becomes a trunk, every VLAN carried on it is exposed to the attacker, and the isolation is defeated in its entirety.

The fix is entirely on the switch: never leave a port in `dynamic auto` or `dynamic desirable` facing anything untrusted. Configure end-host ports as `switchport mode access`, which disables DTP, and force infrastructure trunks with `switchport nonegotiate`.

### Double-Tagging

A subtler, one-way attack that exploits the native VLAN's untagged behaviour. It works only when the attacker sits in the same VLAN as the trunk's native VLAN.

```
                 attacker in native VLAN 1, target in VLAN 20

  attacker  ─── crafts frame with TWO tags: outer=1 (native), inner=20
     │
     ▼
  switch 1  ─── strips the OUTER tag (it matches native VLAN 1),
                forwards the frame onto the trunk UNTAGGED-except-for-inner
     │
     ▼ trunk
  switch 2  ─── sees only the INNER tag (20), delivers into VLAN 20
     │
     ▼
   target   ─── receives a frame that "jumped" from VLAN 1 to VLAN 20
```

The mechanism, step by step:

- The attacker builds a frame with two stacked tags: an outer tag for the native VLAN and an inner tag for the target VLAN.
- The first switch removes exactly one tag — the outer one — because a switch strips only a single tag, and because that tag matches the native VLAN it forwards the frame onto the trunk without re-tagging.
- The inner tag was never inspected by the first switch. The second switch reads it as an ordinary single tag and delivers the frame into the target VLAN.

The attack is unidirectional — replies come back tagged for the target VLAN and never reach the attacker in the native VLAN — but it is enough to inject traffic across a boundary.

The defences all attack the native VLAN's untagged property:

- Set the native VLAN to a dedicated, unused VLAN that no host sits in, so no attacker can be in it.
- Tag the native VLAN explicitly (`vlan dot1q tag native`), which eliminates the untagged behaviour the attack depends on.
- Restrict every trunk's [[#The Allowed VLAN List|allowed VLAN list]] to only the VLANs it must carry.

### Baseline Hardening

The settings that, taken together, close both attacks and the common misconfigurations:

- Access ports explicitly `switchport mode access` — single VLAN, DTP off.
- Trunks explicitly `switchport mode trunk` plus `switchport nonegotiate` — no negotiation.
- Native VLAN moved off VLAN 1 to an unused VLAN, and tagged where supported.
- Allowed VLAN list pruned on every trunk.
- Unused ports shut down and parked in an unused VLAN.
- VLAN 1 kept empty of user traffic.

### Dynamic VLAN Assignment

Rather than statically pinning a port to a VLAN, a NAC deployment assigns the VLAN per-endpoint at authentication. After 802.1X or MAB succeeds, the RADIUS server returns the VLAN in the Access-Accept using the three RFC 3580 tunnel attributes:

|RADIUS attribute|Value|Meaning|
|---|---|---|
|Tunnel-Type (64)|13 (VLAN)|The tunnel is a VLAN assignment.|
|Tunnel-Medium-Type (65)|6 (802)|The medium is IEEE 802.|
|Tunnel-Private-Group-ID (81)|VLAN ID or name|The VLAN to place the port in.|

All three must be sent, with a matching tag value grouping them, or the switch ignores the assignment. This is the mechanism behind the [[PBA - NAC - Network Access Devices#RADIUS Attribute|RADIUS attributes]] the access switches are configured to send, and it is how an endpoint that fails authentication is dropped into the [[PBA - NAC - Network Access Devices#Guest VLAN — `vlan 805`|guest VLAN]] instead of the production one. The security case for it is decisive: a statically assigned switchport can be inherited by anyone who unplugs the authorised host and plugs in their own, whereas a dynamically assigned port follows the identity, not the cable.

---

## Verification and Tooling

_The commands that establish which VLAN a port carries, whether a link is a trunk, and why a configuration is not operating as intended._

### On a Cisco Switch

```cisco
show vlan brief
show interfaces trunk
show interfaces GigabitEthernet1/0/1 switchport
show ip interface brief | include Vlan
```

What each answers:

- `show vlan brief` — the VLAN database and which access ports are in each VLAN.
- `show interfaces trunk` — every trunk, its native VLAN, and the VLANs allowed and forwarding on it. This is the primary reference for diagnosing a native-VLAN mismatch or a pruned VLAN.
- `show interfaces … switchport` — a single port's administrative and operational mode. This confirms that DTP is disabled ("Negotiation of Trunking: Off") and that the port holds its intended access or trunk role, rather than one it negotiated into.
- `show ip interface brief | include Vlan` — every SVI and its up/down state, used when diagnosing autostate behaviour.

### On a Linux Host

```bash
# show VLAN sub-interfaces and their parents
ip -d link show type vlan

# show the bridge's per-port VLAN membership (PVID + tagged/untagged)
bridge vlan show

# watch a live capture to confirm what tag is actually on the wire
tcpdump -e -i eth0 vlan
```

The `-e` flag on tcpdump prints the link-layer header, so the 802.1Q tag and its VID are visible directly — the definitive way to confirm whether a frame is arriving tagged, untagged, or on the wrong VLAN. `ip -d link show type vlan` exposes the VID and parent of each [[#VLAN Sub-Interfaces|sub-interface]]; `bridge vlan show` is the Linux equivalent of `show interfaces trunk` for a [[#Bridge VLAN Filtering|VLAN-aware bridge]].

---

## Common Pitfalls

_The recurring failures, each traced to the mechanism earlier in this note that explains it._

| Symptom                                               | Root cause                                  | Where it is explained                                 |
| ----------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------- |
| Two switches do not trunk under default configuration | Both ports `dynamic auto` → no trunk        | [[#The Negotiation Matrix\|negotiation matrix]]       |
| A port unexpectedly carries many VLANs                | Port left dynamic, negotiated a trunk       | [[#Switch Spoofing\|switch spoofing]]                 |
| Untagged traffic leaks between VLANs across a trunk   | Native VLAN mismatch on the two ends        | [[#The Native VLAN\|native VLAN]]                     |
| SVI remains `up/down`, subnet does not route          | No forwarding port in the VLAN              | [[#SVI Up/Down Behaviour\|SVI up/down behaviour]]     |
| Port assigned to a VLAN passes no traffic             | VLAN missing from the database              | [[#The VLAN Database\|VLAN database]]                 |
| Large frames dropped over a Linux trunk               | Parent MTU too small for the tag            | [[#The MTU Cost\|MTU cost]]                           |
| Endpoint lands in the wrong VLAN after auth           | RFC 3580 attributes incomplete or mistagged | [[#Dynamic VLAN Assignment\|dynamic VLAN assignment]] |