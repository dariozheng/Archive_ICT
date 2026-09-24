---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - category/networking/networking_general
icon: FasNetworkWired
iconColor:
last_update: 2026-08-26
---
# VM90-IP-CORE1

`VM90-IP-CORE1` is the IP core router of the Villamagna 90 datacenter. It performs no Layer-2 switching and terminates no endpoints: every link is a Layer-3 peering carried as a tagged VLAN over two port-channels, and every routing decision it makes is made inside a VRF.

Its job is threefold — carry each security zone in its own routing table, force traffic between zones through the firewall, and hand the zones a controlled view of the global routing table so they can reach the WAN without seeing each other.

This note documents the routing and segmentation design of the device as configured: platform, attachment, VRF model, OSPF and BGP roles, route leaking, static routing, redundancy, telemetry, and the management plane.

---

## Platform

### Hardware and Software

```cisco
version 17.6
boot system bootflash:c8000aep-universalk9.17.06.03a.SPA.bin
license udi pid C8500-12X sn TTM253802UH
license boot level network-advantage
redundancy
 mode none
```

A Catalyst 8500-12X running IOS-XE 17.06.03a on the Aggregation Edge Platform image, with twelve 10-Gigabit ports and a single route processor (`mode none` — there is no supervisor redundancy to fail over to, so device-level resilience comes entirely from the second core router and from [[#First-Hop Redundancy|HSRP]]).

The `network-advantage` boot level is what licenses the features this configuration depends on — VRFs, BGP, and Flexible NetFlow.

### Router Identity

```cisco
interface Loopback100
 ip address 10.100.100.100 255.255.255.255
!
router bgp 65001
 bgp router-id 10.100.100.100
```

`Loopback100` is the router's stable identity. It supplies the BGP router-ID and is the source address for [[#Flow Exporter|flow export]]. It lives in the global table, is picked up by `redistribute connected` in the [[#Global Address Family|global BGP address family]], and therefore reaches any VRF that imports from global.

### Out-of-Band Management

```cisco
vrf definition Mgmt-intf
!
interface GigabitEthernet0
 vrf forwarding Mgmt-intf
 ip address 10.140.0.113 255.255.255.0
 negotiation auto
!
ip route vrf Mgmt-intf 0.0.0.0 0.0.0.0 10.140.0.1
```

`GigabitEthernet0` is the dedicated management port, isolated in `Mgmt-intf` with its own default route. Every management protocol is pinned to it:

|Function|Binding|
|---|---|
|SSH|`ip ssh source-interface GigabitEthernet0`|
|RADIUS|`ip radius source-interface GigabitEthernet0` inside `Mgmt-intf`|
|Syslog|`logging source-interface GigabitEthernet0 vrf Mgmt-intf`|
|SNMP traps and informs|`snmp-server trap-source GigabitEthernet0`|
|TFTP|`ip tftp source-interface GigabitEthernet0`|
|HTTP client|`ip http client source-interface GigabitEthernet0`|
|PKI enrolment (`DNAC-CA`)|`source interface GigabitEthernet0`|

There is also an in-band path to the same management network, via `Port-channel10.3699` and two static routes — see [[#Untracked Static Routes|the untracked statics]]. The out-of-band port and the in-band path both reach `10.140.0.0/24`, which is intentional: it keeps the box reachable when one of the two fails.

### Platform Defaults

```cisco
platform qfp utilization monitor load 80
platform punt-keepalive disable-kernel-core
memory free low-watermark processor 682859
subscriber templating
multilink bundle-name authenticated
spanning-tree extend system-id
diagnostic bootup level minimal
```

Boilerplate and thresholds rather than design. `platform qfp utilization monitor load 80` raises a notification when the forwarding processor passes 80% load, and the memory low-watermark triggers a syslog message when free processor memory drops below roughly 683 MB. `spanning-tree extend system-id` is vestigial on a router with no switched ports.

---

## Physical and Logical Attachment

Both port-channels land on the same pair of Layer-2 aggregation switches, `VM90-DC-L2-AGGR1` and `VM90-DC-L2-AGGR2`. Those switches carry no Layer-3 state for this design — they are pure VLAN transport, which is why the core can build one port-channel across both chassis and reach every peer through it.

```
                      VM90-IP-CORE1
                    ┌────────┬────────┐
                    │  Po10  │  Po11  │
                    └───┬────┴────┬───┘
              8 x 10G   │         │  4 x 10G
                    ┌───┴─────────┴───┐
                    │ VM90-DC-L2-AGGR │   (AGGR1 + AGGR2, L2 only)
                    └───┬─────────┬───┘
          Po2 VLANs ────┘         └──── Po4 VLANs
                    │                    │
   IP-AGGR1/2, SW-VM90-CORE,        FTD4125-BACK
   SW-VM90-EXT, WANMS-RTR1/2,       (zone + backbone
   CLDXT-RTR1/2, MPLS handoff        interface pairs)
```

### Port-channel10 — Peering Trunk

```cisco
interface Port-channel10
 description VM90-DC-L2-AGGR:PO2:L3_Peering-2-IP-Aggr
 no ip address
```

#### Member Links

Eight 10-Gigabit members, four to each aggregation switch, all in LACP active mode:

|Ports|Peer|
|---|---|
|`Te0/0/0` – `Te0/0/3`|`VM90-DC-L2-AGGR1` Po2, `Eth1/1/1-4`|
|`Te0/0/4` – `Te0/0/7`|`VM90-DC-L2-AGGR2` Po2, `Eth1/1/1-4`|

#### Sub-interface Inventory

The parent interface holds no address. Everything rides on `dot1Q` sub-interfaces:

|Sub-interface|VRF|Peer|Address|OSPF|
|---|---|---|---|---|
|`.3300`|`IT-MON-VRF`|`SW-VM90-CORE`|`10.142.132.2/30`|10 / area 0|
|`.3302`|global|`ADM-LESOLUZIONI-EMPOLI` (CallManager flows)|`10.142.132.5/29`|— (HSRP 5)|
|`.3500`|global|MPLS handoff, `FASTWEB`|`10.142.100.21/29`|— (HSRP 4)|
|`.3606`|`IT-VRF-TCI`|`VM39-CORE-SW`|`10.142.107.57/30`|7 / area 0.0.0.101|
|`.3610`|`IT-VRF-VDI`|`VM90-IP-AGGR1`|`10.142.24.26/30`|2 / area 0|
|`.3611`|`IT-VRF-VDI`|`VM90-IP-AGGR2`|`10.142.24.30/30`|2 / area 0, cost 120|
|`.3621`|`IT-VRF-APPALTI`|`VM90-IP-AGGR1`|`10.142.24.70/30`|3 / area 0|
|`.3625`|`IT-VRF-APPALTI`|`VM90-IP-AGGR2`|`10.142.24.86/30`|3 / area 0, cost 120|
|`.3627`|`IT-VRF-APPALTI`|`SW-VM90-EXT`|`10.142.24.89/30`|3 / area 0|
|`.3634`|`IT-VRF-CAMPUS`|`VM90-IP-AGGR1`|`10.142.24.110/30`|4 / area 0|
|`.3636`|`IT-VRF-CAMPUS`|`VM90-IP-AGGR2`|`10.142.24.118/30`|4 / area 0|
|`.3639`|`IT-VRF-WIFIGUEST`|`SW-VM90-CORE`|`10.142.24.129/30`|5 / area 0|
|`.3641`|`IT-VRF-WIFIGUEST`|`WANMS-VM90-RTR1`|`10.142.24.137/30`|5 / area 0|
|`.3642`|`IT-VRF-WIFIGUEST`|`WANMS-VM90-RTR2`|`10.142.24.141/30`|5 / area 0, cost 120|
|`.3645`|`IT-VRF-WIFIGUEST`|`SW-VM90-EXT`|`10.142.24.153/30`|5 / area 0|
|`.3650`|`IT-VRF-ACCESS-CONTROL`|`VM90-IP-AGGR1`|`10.142.24.174/30`|6 / area 0|
|`.3652`|`IT-VRF-ACCESS-CONTROL`|`VM90-IP-AGGR2`|`10.142.24.182/30`|6 / area 0, cost 120|
|`.3659`|`IT-VRF-TCI`|`SW-VM90-EXT`|`10.142.24.209/30`|7 / area 0|
|`.3661`|`IT-VRF-TCI`|`VM90-IP-AGGR1`|`10.142.24.218/30`|7 / area 0|
|`.3662`|`IT-VRF-TCI`|`VM90-IP-AGGR2`|`10.142.24.222/30`|7 / area 0, cost 120|
|`.3670`|`IT-VRF-MGMNT`|`VM90-IP-AGGR1`|`10.142.24.254/30`|8 / area 0|
|`.3672`|`IT-VRF-MGMNT`|`VM90-IP-AGGR2`|`10.142.25.10/30`|8 / area 0, cost 120|
|`.3674`|global|`SW-VM90-EXT`|`10.142.25.17/30`|1 / area 0|
|`.3681`|`IT-VRF-DC`|`VM90-IP-AGGR1`|`10.142.25.46/30`|9 / area 0|
|`.3683`|`IT-VRF-DC`|`VM90-IP-AGGR2`|`10.142.25.54/30`|9 / area 0|
|`.3693`|`IT-MON-VRF`|`VM90-IP-AGGR1`|`10.142.25.114/30`|10 / area 0|
|`.3695`|`IT-MON-VRF`|`VM90-IP-AGGR2`|`10.142.25.122/30`|10 / area 0, cost 120|
|`.3699`|global|`VM90-IP-AGGR1` (OOB)|`10.142.25.138/30`|none|
|`.3701`|global|`WANMS-VM90-RTR1`|`10.142.128.22/30`|1 / area 0|
|`.3703`|global|`WANMS-VM90-RTR2`|`10.142.128.30/30`|1 / area 0|
|`.3742`|global|`CLDXT-VM90-RTR1`|`10.142.128.68/31`|1 / area 0|
|`.3743`|global|`CLDXT-VM90-RTR2`|`10.142.128.70/31`|1 / area 0|
|`.3901`|`VRF-TEST-A`|`VM90-IP-AGGR1`|`10.142.26.6/30`|91 / area 0|
|`.3902`|`VRF-TEST-B`|`VM90-IP-AGGR1`|`10.142.26.14/30`|92 / area 0|

### Port-channel11 — Firewall Trunk

```cisco
interface Port-channel11
 description VM90-DC-L2-AGGR:PO4:L3_Peering-2-FTD-BACK
 no ip address
```

#### Member Links

Four 10-Gigabit members, two to each aggregation switch, carrying only peerings with the `FTD4125` firewall:

|Ports|Peer|
|---|---|
|`Te0/0/8` – `Te0/0/9`|`VM90-DC-L2-AGGR1` Po4, `Eth1/3/1-2`|
|`Te0/0/10` – `Te0/0/11`|`VM90-DC-L2-AGGR2` Po4, `Eth1/3/1-2`|

#### Sub-interface Inventory

Every zone appears here twice — once in its own VRF and once in its backbone VRF. That pairing is the mechanism described in [[#The Firewall Stitch|the firewall stitch]]:

|Sub-interface|VRF|Address|OSPF|
|---|---|---|---|
|`.3221`|`IT-VRF-VDI`|`10.142.2.129/30`|2|
|`.3223`|`IT-VRF-VDI-BACKBONE`|`10.142.2.133/30`|62|
|`.3241`|`IT-VRF-CAMPUS`|`10.142.2.33/30`|4|
|`.3243`|`IT-VRF-CAMPUS-BACKBONE`|`10.142.2.37/30`|64|
|`.3251`|`IT-VRF-WIFIGUEST`|`10.142.2.161/30`|5|
|`.3253`|`IT-VRF-WIFIGUEST-BACKBONE`|`10.142.2.165/30`|65|
|`.3261`|`IT-VRF-ACCESS-CONTROL`|`10.142.2.1/30`|6|
|`.3263`|`IT-VRF-ACCESS-CONTROL-BACKBONE`|`10.142.2.5/30`|66|
|`.3281`|`IT-VRF-MGMNT`|`10.142.2.97/30`|8|
|`.3283`|`IT-VRF-MGMNT-BACKBONE`|`10.142.2.101/30`|68|
|`.3291`|`IT-VRF-DC`|`10.142.2.65/30`|9|
|`.3293`|`IT-VRF-DC-BACKBONE`|`10.142.2.69/30`|69|
|`.3900`|`VRF-TEST-A`|`10.142.26.17/30`|91|
|`.3950`|`VRF-TEST-A-BACKBONE`|`10.142.26.21/30`|93|
|`.3903`|`VRF-TEST-B`|`10.142.26.25/30`|92|
|`.3953`|`VRF-TEST-B-BACKBONE`|`10.142.26.29/30`|94|

Note the absence of `IT-VRF-APPALTI`, `IT-VRF-TCI` and `IT-MON-VRF` — those are [[#Isolated VRFs|isolated VRFs]] with no firewall attachment and no route leaking.

### Naming and Numbering Conventions

The configuration is machine-consistent, and the conventions are worth knowing because they let you read a line and infer its role without looking anything up.

|Convention|Example|Meaning|
|---|---|---|
|Physical description|`PO10:VM90-DC-L2-AGGR1-PO2:Eth1/1/1`|Local bundle, remote device, remote bundle, remote port|
|Sub-interface description|`OSPF-CAMPUS-VM90-IP-AGGR1:L3_Peering:Po1.3634`|Protocol, zone, peer, link type, remote sub-interface|
|Host prefix|`VM90-`, `VM39-`|Site — `VM90` is Villamagna 90, per the SNMP location string|
|Firewall VLAN|`32x1` / `32x3`|Zone-side / backbone-side of the same zone|
|Backbone OSPF process|`62`, `64`, `65`, `66`, `68`, `69`|Equals the VRF's route-target value and its leak community|
|Sub-interface number|`3610`, `3634`, `3650`|Equals the `dot1Q` tag; VLAN ranges are grouped per zone|

The `ip ospf <pid> area <area>` form is used on every interface, so process membership is readable from the interface block itself rather than from `network` statements under the process.

### Neighbouring Devices

|Device|Role|Reached in|
|---|---|---|
|`VM90-DC-L2-AGGR1/2`|Layer-2 aggregation, VLAN transport for both bundles|—|
|`VM90-IP-AGGR1/2`|Layer-3 aggregation toward the access layer, per zone|VDI, APPALTI, CAMPUS, ACCESS-CONTROL, TCI, MGMNT, DC, MON, TEST|
|`FTD4125-BACK`|Firepower 4125, inter-zone enforcement|All zone and backbone VRFs|
|`SW-VM90-CORE`|Site core switch|MON, WIFIGUEST|
|`SW-VM90-EXT`|External / perimeter switch|global, APPALTI, WIFIGUEST, TCI|
|`WANMS-VM90-RTR1/2`|Managed WAN routers|global, WIFIGUEST|
|`CLDXT-VM90-RTR1/2`|Cloud exchange routers|global|
|`VM39-CORE-SW`|Remote site core switch|TCI (NSSA area)|
|`MPLS_FASTWEB`|Carrier MPLS handoff|global|
|`VM90-IP-CORE2`|Peer core router|Implied by the two HSRP groups|

---

## Segmentation Model

This is the centre of the design. Every functional area of the network is a zone, and every zone exists twice in the routing configuration: once as a zone VRF holding its real subnets, and once as a backbone VRF used only for transit between zones. The firewall is the only device that joins the two halves.

The consequence is that a zone's routing table physically cannot contain another zone's subnets. Reachability between zones is not a policy decision made in an ACL — it is a property of which route-targets a backbone VRF imports.

### Zone VRFs

Each zone VRF faces the access layer and holds the zone's live subnets, learned by [[#Zone-Side Processes|its OSPF process]] from the IP aggregation routers, the core switch, or the external switch.

|VRF|RD / RT|Leaks to global|Zone OSPF|
|---|---|---|---|
|`IT-VRF-CAMPUS`|`65001:20`|yes|4|
|`IT-VRF-WIFIGUEST`|`65001:21`|no|5|
|`IT-VRF-ACCESS-CONTROL`|`65001:22`|yes|6|
|`IT-VRF-DC`|`65001:23`|yes|9|
|`IT-VRF-VDI`|`65001:24`|yes|2|
|`IT-VRF-MGMNT`|`65001:29`|yes|8|
|`VRF-TEST-A`|`65001:91`|yes|91|
|`VRF-TEST-B`|`65001:92`|yes|92|

`IT-VRF-WIFIGUEST` is the exception: it has a route-target but no import/export map and no BGP address-family, so it never participates in [[#Route Leaking|route leaking]] at all. Guest traffic reaches internal services only through the firewall, and only for the handful of hosts named in [[#Guest Zone Restriction|the guest restriction]].

### Backbone VRFs

Each backbone VRF holds only two things: the `/30` toward the firewall, and routes imported from other backbone VRFs. It has no access-layer interfaces and no subnets of its own.

|VRF|RD / RT|Imports RTs|Backbone OSPF|
|---|---|---|---|
|`IT-VRF-VDI-BACKBONE`|`65001:62`|66, 68, 64, 69|62|
|`IT-VRF-CAMPUS-BACKBONE`|`65001:64`|66, 68, 62, 69|64|
|`IT-VRF-WIFIGUEST-BACKBONE`|`65001:65`|69|65|
|`IT-VRF-ACCESS-CONTROL-BACKBONE`|`65001:66`|64, 62, 69|66|
|`IT-VRF-MGMNT-BACKBONE`|`65001:68`|64, 62, 69|68|
|`IT-VRF-DC-BACKBONE`|`65001:69`|66, 65, 68, 64, 62|69|
|`VRF-TEST-A-BACKBONE`|`65001:93`|94|93|
|`VRF-TEST-B-BACKBONE`|`65001:94`|93|94|

### The Firewall Stitch

The zone VRF and its backbone VRF are never joined inside the router. They are joined only by the `FTD4125`, which holds an interface in each:

```
   access layer                                            other zones
        │                                                       ▲
        │  OSPF 4                                               │ RT import
        ▼                                                       │  64 ↔ 62/66/68/69
 ┌────────────────┐   Po11.3241    ┌──────────┐   Po11.3243   ┌─────────────────────┐
 │ IT-VRF-CAMPUS  │───────────────►│ FTD4125  │──────────────►│ CAMPUS-BACKBONE     │
 │ (zone subnets) │◄───────────────│          │◄──────────────│ (transit only)      │
 └────────────────┘    OSPF 4      └──────────┘    OSPF 64    └─────────────────────┘
```

Nothing in the core's routing tables can move a packet from `IT-VRF-CAMPUS` to `IT-VRF-CAMPUS-BACKBONE`. The only path between them leaves the router, is inspected, and comes back — which is what makes the firewall unavoidable rather than merely recommended.

#### Inter-Zone Reachability Matrix

The route-targets imported by each backbone VRF define, exactly, which zones can exchange routes. The matrix is symmetric, so every permitted pair is permitted in both directions:

|Zone|AC|Campus|VDI|MGMNT|DC|Guest|
|---|---|---|---|---|---|---|
|Access Control|—|yes|yes|no|yes|no|
|Campus|yes|—|yes|yes|yes|no|
|VDI|yes|yes|—|yes|yes|no|
|Management|no|yes|yes|—|yes|no|
|Datacenter|yes|yes|yes|yes|—|yes|
|WiFi Guest|no|no|no|no|yes|—|

Two patterns stand out. The datacenter zone is the hub — every other zone imports it and it imports every other zone. The guest zone is a leaf with a single adjacency, to the datacenter, and even that is filtered down to six host routes.

The Access Control ↔ Management pair is deliberately absent from the route-target matrix. That intent is not fully carried through into the community filters — see [[#Malformed Community Value|the community observation]].

#### Traffic Path Between Zones

Following a packet from a campus client to a datacenter server:

```
 1. client ──► IT-VRF-CAMPUS            route learned from FTD by OSPF 4
 2.        ──► Po11.3241 ──► FTD        inspected leaving the campus zone
 3.        ──► Po11.3243 ──► CAMPUS-BACKBONE
 4.            lookup hits a route imported from DC-BACKBONE (RT 65001:69)
 5.        ──► Po11.3293 ──► FTD        inspected entering the datacenter zone
 6.        ──► Po11.3291 ──► IT-VRF-DC
 7.        ──► VM90-IP-AGGR ──► server
```

Two consequences follow, and both are worth confirming against the firewall configuration, which is out of scope for this note:

- Zone-to-zone traffic crosses the firewall twice, once on the source zone's boundary and once on the destination zone's boundary. Whether that is one or two inspection passes depends on how the `FTD4125` groups those interface pairs into its own VRFs.
- Traffic to the WAN or the internet does not cross the firewall at all. Zones learn external destinations directly from [[#Global to VRF — Import Maps|the global-table leak]], so the firewall is an inter-zone enforcement point, not the perimeter. The `-BACK` suffix in the peer name implies there is a front side elsewhere handling that role.

### Isolated VRFs

Three VRFs run OSPF but take no part in leaking or firewalling. They have no backbone counterpart, no firewall sub-interface, and — with one partial exception — no route-targets that anything imports.

#### IT-VRF-TCI

```cisco
router ospf 7 vrf IT-VRF-TCI
 area 0.0.0.0 authentication
 area 0.0.0.101 authentication
 area 0.0.0.101 nssa no-redistribution no-summary
 area 0.0.0.101 nssa translate type7 always suppress-fa
 bfd all-interfaces
```

The only VRF with a multi-area OSPF design. Area 0 faces `SW-VM90-EXT` and the IP aggregation pair locally; area `0.0.0.101` faces `VM39-CORE-SW` at the remote site over `Po10.3606`. See [[#Area Design and the VM39 NSSA|the NSSA discussion]] for what the area keywords do.

`IT-VRF-TCI` carries an RD and route-target `65001:25`, but no other VRF imports it and it has no BGP address-family, so the route-target is inert.

#### IT-VRF-APPALTI

```cisco
vrf definition IT-VRF-APPALTI
 !
 address-family ipv4
 exit-address-family
```

No route distinguisher at all, which means it cannot participate in BGP or in any form of leaking — an RD is the prerequisite. It runs OSPF 3 across three links (both aggregation routers and the external switch) and is reachable only from within itself.

#### IT-MON-VRF

Monitoring transport, RD `65001:32`, no route-targets, no BGP address-family. OSPF 10 peers with `SW-VM90-CORE` on `Po10.3300` and with both aggregation routers on `.3693` and `.3695`. Fully self-contained.

### Placeholder and Leftover VRFs

|VRF|State|
|---|---|
|`IT-VRF-FIWIFI`, `MON-VRF`, `OT-VRF`, `OT-VRF-DC`, `OT-VRF-FIELD`|Name-only shells. No RD, no interfaces, no protocol. The `OT-` set looks like reserved space for operational-technology segmentation.|
|`IT-VRF-BACKBONE`|RD `65001:26`, imports RT `65001:24` (VDI) and carries the `VRF_GLOBAL_TO_VDI` / `VRF_VDI_TO_GLOBAL` maps. Has a BGP address-family with `redistribute connected`, but no interfaces to connect. An earlier VDI leak design, superseded.|
|`TEMP`|RD `65001:33`, `import map IMPORT-CAMPUS-TO-TEMP`, RT import `65001:20`. Note this is the older `import map` form, which filters route-target imports — not the `import ipv4 unicast map` form used for global leaking. With no BGP address-family for `TEMP`, nothing is imported in practice.|
|`VRF-TEST-A/B` and their backbones|A working copy of the production pattern for lab use, complete with firewall sub-interfaces, backbone VRFs, tag filters, and `Null0` test routes.|

### Route Distinguishers and Route Targets

Because there is no MPLS and no VPN peer, the RD/RT values here are purely local bookkeeping. The RD makes a VRF's routes distinguishable inside the BGP VPNv4 table; the RT decides which other local VRFs import them. Nothing is advertised off-box.

The numbering is deliberate and readable:

|Range|Use|
|---|---|
|`65001:20` – `65001:33`|Zone VRFs and utility VRFs|
|`65001:62` – `65001:69`|Backbone VRFs, matching their [[#Process Map|
|`65001:91` – `65001:94`|Test VRFs and their backbones|

The backbone values do double duty: `65001:64` is Campus-Backbone's route-target, the OSPF process ID for that VRF, and the BGP community stamped on campus routes exported to global. One number, three roles — which makes the [[#Community Numbering|community table]] easy to read once you know the trick.

---

## OSPF

OSPF does all the dynamic routing here. There are twenty processes: one per zone VRF, one per backbone VRF, and one for the global table.

### Process Map

|Process|VRF|Neighbours|Notes|
|---|---|---|---|
|1|global|`SW-VM90-EXT`, `WANMS-RTR1/2`, `CLDXT-RTR1/2`|Redistributes statics and BGP|
|2|`IT-VRF-VDI`|IP-AGGR1/2, FTD|`capability vrf-lite`|
|3|`IT-VRF-APPALTI`|IP-AGGR1/2, `SW-VM90-EXT`|Isolated, no leaking|
|4|`IT-VRF-CAMPUS`|IP-AGGR1/2, FTD|`redistribute static`|
|5|`IT-VRF-WIFIGUEST`|`SW-VM90-CORE`, `SW-VM90-EXT`, WANMS-RTR1/2, FTD|No default origination|
|6|`IT-VRF-ACCESS-CONTROL`|IP-AGGR1/2, FTD||
|7|`IT-VRF-TCI`|`SW-VM90-EXT`, IP-AGGR1/2, `VM39-CORE-SW`|Two areas, NSSA|
|8|`IT-VRF-MGMNT`|IP-AGGR1/2, FTD||
|9|`IT-VRF-DC`|IP-AGGR1/2, FTD||
|10|`IT-MON-VRF`|`SW-VM90-CORE`, IP-AGGR1/2|Isolated, no leaking|
|62, 64, 65, 66, 68, 69|Backbone VRFs|FTD only|`passive-interface default`|
|91, 92|`VRF-TEST-A/B`|IP-AGGR1, FTD|`passive-interface default`|
|93, 94|Test backbones|FTD only|`passive-interface default`|

### Zone-Side Processes

```cisco
router ospf 4 vrf IT-VRF-CAMPUS
 capability vrf-lite
 area 0.0.0.0 authentication
 redistribute static
 redistribute bgp 65001 route-map SET-TAG-TO-GLOBAL-COMMUNITY
 network 10.142.24.108 0.0.0.3 area 0.0.0.0
 default-information originate
 bfd all-interfaces
```

A zone-side process learns the zone's subnets from the access layer and gives back two things: a default route, and the external destinations leaked from the global table.

The `redistribute bgp` route-map is the important line. `SET-TAG-TO-GLOBAL-COMMUNITY` permits only routes carrying community `900:900` — the marker applied by the import maps — and stamps them with [[#Tag 800|OSPF tag 800]]. Because the route-map has no catch-all permit clause, nothing else in the VRF's BGP table reaches OSPF. Routes leaked in from other zones stay out of the zone-side OSPF domain entirely, which is exactly right: they must be reached through the firewall, not advertised to the access layer.

### Backbone-Side Processes

```cisco
router ospf 64 vrf IT-VRF-CAMPUS-BACKBONE
 capability vrf-lite
 area 0.0.0.0 authentication
 redistribute bgp 65001 route-map TAG-LEAKED-SUBNETS-CAMPUS
 passive-interface default
 no passive-interface Port-channel11.3243
 bfd all-interfaces
```

Backbone processes talk to nothing but the firewall. `passive-interface default` with a single exception makes that explicit and protects against a stray adjacency if a backbone VLAN is ever extended somewhere it shouldn't be.

Their one job is to advertise the other zones' leaked routes to the firewall, tagged with [[#Tag 80|tag 80]], so the firewall knows what is reachable through this zone's backbone and can build its own return path. There is no `default-information originate` here — a backbone VRF should never be a last resort for anything.

### Global Process

```cisco
router ospf 1
 area 0.0.0.0 authentication
 redistribute static route-map VRFGLOBAL-REDISTRIBUTE-STATIC-TO-OSPF
 redistribute bgp 65001
 bfd all-interfaces
```

Process 1 covers the WAN-facing and perimeter peerings: `SW-VM90-EXT`, both managed WAN routers, and both cloud exchange routers. `VRFGLOBAL-REDISTRIBUTE-STATIC-TO-OSPF` matches prefix-list `ALL-NETWORKS` (`0.0.0.0/0 le 32`), so it permits everything — the route-map is a hook for future filtering rather than a filter today.

Note that process 1 redistributes BGP while the [[#Global Address Family|global BGP address family]] redistributes process 1. See [[#Mutual Redistribution Between OSPF 1 and BGP|the observation on mutual redistribution]].

### `capability vrf-lite`

Present on every VRF process that participates in leaking, absent on the isolated ones. Without it, an OSPF process running inside a VRF behaves like a PE: it sets the DN bit on LSAs generated from BGP-redistributed routes, and it ignores received LSAs that already have the DN bit set. That loop-prevention behaviour is correct for MPLS VPN and wrong here, where BGP is only a local leaking mechanism and both ends of the link are ordinary routers. `capability vrf-lite` disables the DN-bit and domain-tag checks so the redistributed routes actually propagate.

It is missing on processes 3, 7 and 10 — which is harmless, because those processes redistribute nothing from BGP.

### Area Design and the VM39 NSSA

Every process uses a single area 0 except process 7, which extends `IT-VRF-TCI` to the remote `VM39` site through area `0.0.0.101`:

|Keyword|Effect|
|---|---|
|`nssa no-summary`|Suppresses Type-3 summaries into the area. Combined with NSSA this makes it a totally NSSA area — `VM39` receives only a default route plus its own intra-area routes.|
|`nssa no-redistribution`|Stops this router, as an ABR, from injecting its own redistributed routes into the area as Type-7.|
|`translate type7 always`|Forces this ABR to translate Type-7 into Type-5 regardless of the usual translator election, so translation does not move if the peer ABR's router-ID changes.|
|`suppress-fa`|Zeroes the forwarding address in the translated Type-5 LSAs, so backbone routers route to this ABR instead of to a forwarding address they may not be able to reach.|

`translate type7 always` on more than one ABR in the same area produces duplicate Type-5 LSAs, so if `VM39` is dual-homed, verify the setting on the other ABR.

### Authentication

Every area carries `area 0.0.0.0 authentication` and every OSPF-enabled interface carries an `ip ospf authentication-key 7 …`. That is OSPF Type-1 authentication — a plaintext password obfuscated on-box by `service password-encryption`, sent in the clear on the wire. It defends against accidental adjacencies, not against an attacker with access to the VLAN. Type-2 (`ip ospf message-digest-key`) or the SHA variants would be the upgrade path.

Keys differ per zone and, in a few cases, per link within a zone — for example `Po10.3625` and `Po10.3662` use one value while their zone partners use another. Mismatched keys prevent an adjacency from forming, so treat any key change as per-link work coordinated with the peer.

### BFD

```cisco
router ospf 4 vrf IT-VRF-CAMPUS
 bfd all-interfaces
!
interface Port-channel10.3634
 ip ospf bfd
```

Every process asks OSPF to use BFD, and most sub-interfaces enable it explicitly. This matters more than usual here: with sub-second failure detection, OSPF converges on the alternate aggregation router long before the dead-interval would expire, and the port-channel spanning two chassis means a peer can be lost while the bundle stays up.

However, no interface carries `bfd interval … min_rx … multiplier …` and there is no BFD template — see [[#BFD Without Timers|the observation]].

### Path Preference

Redundancy inside the VRFs is metric-based rather than protocol-based. For most zones the link to `VM90-IP-AGGR2` carries `ip ospf cost 120` while the link to `AGGR1` keeps its default cost, so this router prefers `AGGR1` and uses `AGGR2` only on failure:

|Zone|AGGR1 link|AGGR2 link|Preference|
|---|---|---|---|
|VDI|`.3610`|`.3611` cost 120|AGGR1|
|APPALTI|`.3621`|`.3625` cost 120|AGGR1|
|CAMPUS|`.3634`|`.3636`|equal cost|
|ACCESS-CONTROL|`.3650`|`.3652` cost 120|AGGR1|
|TCI|`.3661`|`.3662` cost 120|AGGR1|
|MGMNT|`.3670`|`.3672` cost 120|AGGR1|
|DC|`.3681`|`.3683`|equal cost|
|MON|`.3693`|`.3695` cost 120|AGGR1|
|WIFIGUEST (WANMS)|`.3641`|`.3642` cost 120|RTR1|

Campus and DC load-share where the others fail over — see [[#Asymmetric Path Costs|the observation]].

---

## BGP 65001 as a Route-Leaking Engine

### No Neighbours

```cisco
router bgp 65001
 bgp router-id 10.100.100.100
 bgp log-neighbor-changes
 bgp graceful-restart
```

There is not a single `neighbor` statement. BGP exchanges nothing with anyone; it exists because it is the only mechanism IOS-XE offers for moving routes between routing tables on the same box. Every VRF-to-VRF and global-to-VRF leak in this configuration is a BGP import.

`bgp graceful-restart` is configured but, with no peers, has nothing to preserve.

### Global Address Family

```cisco
 address-family ipv4
  redistribute connected
  redistribute static
  redistribute ospf 1 match internal external 1 external 2
 exit-address-family
```

This populates the BGP global IPv4 table with everything the global routing table knows: connected interfaces (including `Loopback100`), the tracked and untracked statics, and all of OSPF 1 including externals. That table is the source for every zone's [[#Global to VRF — Import Maps|global import]].

### Per-VRF Address Families

Zone VRFs redistribute their OSPF process into BGP, filtered against re-leaking:

```cisco
 address-family ipv4 vrf IT-VRF-CAMPUS
  redistribute connected
  redistribute static
  redistribute ospf 4 match internal external 1 external 2 route-map NO-RED-TAG-TO-GLOBAL
  default-information originate
 exit-address-family
```

Backbone VRFs redistribute only their OSPF process, with the equivalent guard:

```cisco
 address-family ipv4 vrf IT-VRF-CAMPUS-BACKBONE
  redistribute ospf 64 match internal external 1 external 2 route-map NO-RED-TAG-TO-LEAK
 exit-address-family
```

Address families exist for the six zone VRFs, the six backbone VRFs, the four test VRFs, and `IT-VRF-BACKBONE`. There is deliberately none for `IT-VRF-WIFIGUEST`, `IT-VRF-APPALTI`, `IT-VRF-TCI`, `IT-MON-VRF` or `TEMP` — without an address-family, a VRF is invisible to the leaking machinery no matter what route-targets it carries.

---

## Route Leaking

Three distinct flows of routes, each with its own mechanism:

```
                    ┌──────────────────┐
                    │   global table   │  WAN, MPLS, cloud exchange
                    └────┬────────▲────┘
      import ipv4 unicast│        │export ipv4 unicast
      map (community     │        │map (set community
      deny + set 900:900)│        │= backbone RT)
                    ┌────▼────────┴────┐
                    │    zone VRF      │  real subnets, access layer
                    └──────────────────┘
                             ▲
                             │ firewall only — no leak
                             ▼
                    ┌──────────────────┐
                    │  backbone VRF    │◄──── route-target import ────► other
                    └──────────────────┘                              backbones
```

### Community Numbering

Every community in the configuration is a 32-bit decimal. Decoded, the scheme is systematic — the value a zone stamps on its exported routes equals its own backbone route-target:

|Decimal|Community|Meaning|
|---|---|---|
|`58983300`|`900:900`|Set by every import map. Marks "this route came from the global table".|
|`4259905598`|`65001:62`|VDI origin|
|`4259905600`|`65001:64`|Campus origin|
|`4259905602`|`65001:66`|Access Control origin|
|`4259905604`|`65001:68`|Management origin|
|`4259905605`|`65001:69`|Datacenter origin|
|`4259905629`|`65001:93`|Test-A origin|
|`4259905630`|`65001:94`|Test-B origin|
|`4249905602`|`64848:27074`|Not a valid `65001:` value — see [[#Malformed Community Value|

### VRF to Global — Export Maps

```cisco
vrf definition IT-VRF-CAMPUS
 address-family ipv4
  export ipv4 unicast map EXPORT-CAMPUS-TO-GLOBAL
!
route-map EXPORT-CAMPUS-TO-GLOBAL permit 10
 match ip address prefix-list CAMPUS-SUBNETS
 set community 4259905600
```

Each zone pushes a defined set of its own prefixes into the BGP global table, stamped with its origin community. The stamp is what makes the [[#Global to VRF — Import Maps|import filters]] possible: without it, a route arriving from global would be indistinguishable from a route that started in a peer zone.

|Zone|Export map|Prefix filter|Community set|
|---|---|---|---|
|Campus|`EXPORT-CAMPUS-TO-GLOBAL`|`CAMPUS-SUBNETS`|`65001:64`|
|Datacenter|`EXPORT-DC-TO-GLOBAL`|`DC-SUBNETS`|`65001:69`|
|Management|`EXPORT-MGMNT-TO-GLOBAL`|`MGMT-SUBNETS`|`65001:68`|
|VDI|`EXPORT-VDI-TO-GLOBAL`|none|`65001:62`|
|Access Control|`EXPORT-ACCESS-CONTROL-TO-GLOBAL`|none|`65001:66`|
|Test-A / Test-B|`TEST-A-TO-GLOBAL-BGP` / `TEST-B-TO-GLOBAL-BGP`|none|`65001:93` / `65001:94`|

VDI and Access Control have no prefix filter, so every route in those VRFs is exported to global. Campus, DC and Management publish only an explicit list. That asymmetry is worth a decision: either the filtered zones' lists need maintaining as subnets are added, or the unfiltered zones are publishing more than intended.

### Global to VRF — Import Maps

```cisco
vrf definition IT-VRF-CAMPUS
 address-family ipv4
  import ipv4 unicast map IMPORT-CAMPUS-FROM-GLOBAL
!
ip community-list expanded FROM-GLOBAL-TO-CAMPUS permit 4259905602
ip community-list expanded FROM-GLOBAL-TO-CAMPUS permit 4259905600
ip community-list expanded FROM-GLOBAL-TO-CAMPUS permit 4259905604
ip community-list expanded FROM-GLOBAL-TO-CAMPUS permit 4259905598
ip community-list expanded FROM-GLOBAL-TO-CAMPUS permit 4259905605
!
route-map IMPORT-CAMPUS-FROM-GLOBAL deny 5
 match community FROM-GLOBAL-TO-CAMPUS
!
route-map IMPORT-CAMPUS-FROM-GLOBAL permit 200
 set community 58983300
```

This is the load-bearing piece of the whole design, and it reads backwards until you see the point. The community-list gathers the origin communities of every zone, including Campus itself. The route-map denies all of them and permits everything else.

So a zone imports from the global table everything except routes that started life in a zone. WAN prefixes, MPLS prefixes, cloud-exchange prefixes and loopbacks come through; another zone's subnets do not, even though they are sitting right there in the BGP global table. Denying its own community as well stops a zone from re-importing what it just exported.

Whatever survives is stamped `900:900`, which is the signal that lets [[#Zone-Side Processes|the zone's OSPF process]] pick exactly those routes up for the access layer.

|Zone|Community-list|Communities denied|
|---|---|---|
|Campus|`FROM-GLOBAL-TO-CAMPUS`|AC, Campus, MGMNT, VDI, DC|
|Datacenter|`FROM-GLOBAL-TO-DC`|DC, AC, MGMNT, Campus, VDI|
|Management|`FROM-GLOBAL-TO-MGMNT`|MGMNT, Campus, VDI, DC|
|VDI|`FROM-GLOBAL-TO-VDI`|VDI, Campus, MGMNT, DC, plus one malformed value|
|Access Control|`FROM-GLOBAL-TO-ACCESS-CONTROL`|Campus, VDI, DC, plus one malformed value|
|Test-A / Test-B|`FROM-GLOBAL-TO-A` / `FROM-GLOBAL-TO-B`|Test-A, Test-B|

### Zone to Zone — Route Targets

Between backbone VRFs there is no import map and no community filtering — plain route-target import, per [[#Inter-Zone Reachability Matrix|the matrix]]. Because both VRFs are local, an imported route keeps the source VRF's next hop and outgoing interface, so a lookup in `CAMPUS-BACKBONE` can forward straight out `Po11.3293` in the DC backbone's subnet.

What the firewall gets to see of those imported routes is decided by the `TAG-LEAKED-SUBNETS-*` maps on redistribution into the backbone OSPF process:

|Map|Prefix filter|Effect|
|---|---|---|
|`TAG-LEAKED-SUBNETS-VDI`|`LEAKED-VRF-VDI` (`0.0.0.0/0 le 32`)|Everything, tagged 80|
|`TAG-LEAKED-SUBNETS-CAMPUS`|`LEAKED-VRF-CAMPUS` (permit all)|Everything, tagged 80|
|`TAG-LEAKED-SUBNETS-DC`|`LEAKED-VRF-DC` (permit all)|Everything, tagged 80|
|`TAG-LEAKED-SUBNETS-MGMNT`|`LEAKED-VRF-MGMNT` (permit all)|Everything, tagged 80|
|`TAG-LEAKED-SUBNETS-ACCESS-CONTROL`|`LEAKED-VRF-ACCESS-CONTROL` (permit all)|Everything, tagged 80|
|`TAG-LEAKED-SUBNETS-WIFI-GUEST`|`LEAKED-VRF-WIFI-GUEST` (six `/32`s)|Six host routes only|
|`TAG-LEAKED-SUBNETS-A-B`|none|Everything, tagged 80|

### Loop Prevention with Route Tags

Two OSPF tags carry the entire loop-prevention scheme. Both mean "this route was leaked in from somewhere else, do not send it back".

#### Tag 800

```cisco
route-map SET-TAG-TO-GLOBAL-COMMUNITY permit 10
 description Tag 800 per tutte le subnet importate da Global
 match community GLOBAL-COMMUNITY
 set tag 800
```

Applied when a zone's OSPF process picks up global-leaked routes. `GLOBAL-COMMUNITY` is `900:900`, so tag 800 means "learned from the global table".

#### Tag 80

Applied by the `TAG-LEAKED-SUBNETS-*` maps when a backbone process advertises another zone's routes to the firewall. Tag 80 means "leaked from another zone".

#### NO-RED-TAG Maps

```cisco
route-map NO-RED-TAG-TO-GLOBAL deny 5
 match tag 800 80
!
route-map NO-RED-TAG-TO-GLOBAL permit 200
```

On the way back into BGP, both tags are dropped. Without this, a route leaked into a zone would be redistributed into that zone's OSPF, learned back from a neighbour, redistributed into BGP, and re-exported to global — a loop across two protocols and three route tables that would be tedious to unpick from a `show ip route` output.

The four variants are identical in behaviour and differ only in where they are applied:

|Map|Applied to|
|---|---|
|`NO-RED-TAG-TO-GLOBAL`|`redistribute ospf` in zone VRF address-families|
|`NO-RED-TAG-TO-LEAK`|`redistribute ospf` in backbone VRF address-families|
|`NO-RED-TAG-80`|`redistribute ospf` in `VRF-TEST-A/B`|
|`NO-RED-TAG-800`|`redistribute ospf` in the test backbones|

### Guest Zone Restriction

The guest zone deserves separate mention because it is the strictest thing in the configuration and it is enforced in three independent places.

```cisco
ip prefix-list LEAKED-VRF-WIFI-GUEST seq 10 permit 10.140.2.8/32
ip prefix-list LEAKED-VRF-WIFI-GUEST seq 20 permit 10.140.2.31/32
ip prefix-list LEAKED-VRF-WIFI-GUEST seq 30 permit 10.140.2.32/32
ip prefix-list LEAKED-VRF-WIFI-GUEST seq 45 permit 10.140.2.37/32
ip prefix-list LEAKED-VRF-WIFI-GUEST seq 50 permit 10.140.10.102/32
ip prefix-list LEAKED-VRF-WIFI-GUEST seq 60 permit 10.140.10.103/32
```

1. `IT-VRF-WIFIGUEST` has no BGP address-family and no import or export map, so guest subnets never enter the global table and global routes never enter the guest VRF.
2. `IT-VRF-WIFIGUEST-BACKBONE` imports one route-target only, `65001:69`, so the datacenter is the sole reachable zone.
3. Of the datacenter routes imported, only the six `/32`s above are advertised to the firewall.

`10.140.2.31` and `10.140.2.32` are the ISE Policy Service Nodes documented in [[PBA - NAC - Network Access Devices#RADIUS Server Definition|the NAD note]] — the guest portal, and the source of the CoA that moves a guest session out of the redirect state. The remaining hosts are the supporting infrastructure a captive portal needs.

Guest internet access does not come through the firewall: `Po10.3641` and `.3642` put the two managed WAN routers directly into the guest VRF, and OSPF 5 has no `default-information originate`, so the default for guests is expected to come from those routers.

### Prefix-List Inventory

|Prefix-list|Used by|Content|
|---|---|---|
|`ALL-NETWORKS`|`VRFGLOBAL-REDISTRIBUTE-STATIC-TO-OSPF`|Permit all|
|`CAMPUS-SUBNETS`|`EXPORT-CAMPUS-TO-GLOBAL`|11 campus prefixes in `10.128/16`, `10.10/16`, `172.20/16`, `172.22/16`|
|`DC-SUBNETS`|`EXPORT-DC-TO-GLOBAL`|~70 datacenter prefixes, mostly `10.140/16`, `10.129/16`, `172.28/16`|
|`MGMT-SUBNETS`|`EXPORT-MGMNT-TO-GLOBAL`|`10.140.1.0/24`, `172.20.130.0/24`, `10.128.0.0/24`|
|`LEAKED-VRF-*`|`TAG-LEAKED-SUBNETS-*`|Permit all, except the guest list|
|`IMPORT-CAMPUS`|`IMPORT-CAMPUS-TO-TEMP`|`0.0.0.0/0 ge 16`|
|`VDI-SUBNETS`|`VRF_GLOBAL_TO_VDI` (on `IT-VRF-BACKBONE`)|`10.140.128.0/20`|
|`VRF-TEST-A/B-SUBNETS`, `TEST-B`|Test maps|Lab prefixes|
|`IT-VRF-*-SUBNETS`|`RMP-IT-VRF-*-BGP` — unreferenced|Permit all|
|`WIFI_GUEST`|`WIFI-GUEST` — unreferenced|Guest service hosts|
|`GLOBAL`, `BGP`|nothing|`10.100.100.100/32`, `10.20.30.40/32`|

Two same-named objects are easy to confuse: `IMPORT-CAMPUS` exists both as a standard access-list (`10.128.1.0/24`) and as a prefix-list (`0.0.0.0/0 ge 16`). The route-map matches `prefix-list IMPORT-CAMPUS`, so the access-list is unused.

---

## Static Routing and Defaults

### Global Static Routes

#### Tracked Static Routes

Two large groups of statics are conditional on IP SLA probes, so they withdraw automatically when the next hop stops answering.

```cisco
track 4 ip sla 4 reachability
track 5 ip sla 5 reachability
!
ip sla 4
 icmp-echo 10.142.96.85 source-ip 10.142.96.82
  threshold 1500
  timeout 2000
  frequency 30
ip sla schedule 4 life forever start-time now
!
ip sla 5
 icmp-echo 10.142.100.18 source-ip 10.142.100.21
  threshold 1500
  timeout 2000
  frequency 30
ip sla schedule 5 life forever start-time now
```

|Group|Next hop|Probe|Destinations|
|---|---|---|---|
|`track 4`|`10.142.96.85`|SLA 4|~30 legacy and partner ranges: `10.20.208.0/22`, `10.55.x`, `10.70.16.0/20`, `10.122.32.0/19`, `10.243.0.0/16`, `172.16.x`, `172.21.x`, `172.30.10.0/24`|
|`track 5`|`10.142.100.18`|SLA 5|MPLS WAN: `10.10.0.0/19`, `10.10.64.0/20`, `10.128.0.0/15`, `10.128.178.0/24`, `172.20.0.0/19`, `172.20.64.0/20`, `10.142.100.0/29`|

Each probe sends an ICMP echo every 30 seconds, gives up after 2000 ms, and marks the connection degraded past 1500 ms — though with `reachability` tracking only, the threshold affects statistics rather than the track state.

`track 5` does double duty: as well as gating the WAN statics, it is watched by [[#HSRP Group 4 — MPLS Handoff|HSRP group 4]] on the same interface, so losing the carrier next hop also moves the gateway to the peer core router.

`track 4`'s probe is sourced from `10.142.96.82`, which is not configured on any interface of this router — see [[#Unreachable IP SLA Source|the observation]].

#### IP SLA 6 — Unreferenced Probe

```cisco
ip sla 6
 icmp-echo 10.140.0.1 source-ip 10.142.25.138
  threshold 1500
  timeout 2000
  frequency 30
ip sla schedule 6 life forever start-time now
```

Probes the management gateway from the in-band OOB link. No track object references it, so it feeds statistics and SNMP `ipsla` traps only.

#### Untracked Static Routes

|Route|Next hop|Purpose|
|---|---|---|
|`10.140.0.0/24`|`10.142.25.137`|In-band path to the management LAN via `Po10.3699`|
|`10.140.220.0/24`|`10.142.25.137`|Same, second management range|
|`172.20.253.0/24`|`10.142.100.18`|MPLS destination, deliberately not tracked|
|`2.3.4.5/32`|`Null0`|Test artifact|

### Per-VRF Defaults

```cisco
ip route vrf Mgmt-intf 0.0.0.0 0.0.0.0 10.140.0.1
ip route vrf IT-VRF-ACCESS-CONTROL 0.0.0.0 0.0.0.0 10.142.24.42
ip route vrf IT-VRF-CAMPUS 0.0.0.0 0.0.0.0 10.142.128.102 200
ip route vrf IT-VRF-DC 0.0.0.0 0.0.0.0 10.142.25.18
ip route vrf IT-VRF-MGMNT 0.0.0.0 0.0.0.0 10.142.25.18
ip route vrf IT-VRF-VDI 0.0.0.0 0.0.0.0 10.142.25.18
ip route vrf VRF-TEST-A 0.0.0.0 0.0.0.0 10.142.25.18
ip route vrf VRF-TEST-B 0.0.0.0 0.0.0.0 10.142.25.18
```

`10.142.25.18` is `SW-VM90-EXT` on the global-table sub-interface `Po10.3674`. The next hop is not directly connected in any of these VRFs — it resolves because `10.142.25.16/30` is a connected route in the global table, redistributed into BGP and leaked back into each VRF by [[#Global to VRF — Import Maps|the import map]]. The leaked route keeps the global interface, so default-routed traffic from a zone leaves through the global-table peering with the external switch and never touches the firewall.

Two defaults break the pattern. Access Control points at `10.142.24.42`, an address inside its own OSPF domain rather than the global table. Campus points at `10.142.128.102` with administrative distance 200, making it a floating static that yields to any OSPF-learned default.

There are also three `Null0` and lab statics — `2.2.2.2/32` in `IT-VRF-ACCESS-CONTROL-BACKBONE`, `100.100.100.100/32` in `VRF-TEST-A-BACKBONE`, and `1.1.1.1/32` via `10.142.28.18` in `VRF-TEST-A`. The second is redistributed to the firewall by `router ospf 93`'s `redistribute static`.

### Default Origination into the Zones

The per-VRF statics are not there to route traffic — they are there to be originated. `default-information originate` without `always` requires an existing default in the table, so each static is the seed that lets the zone's OSPF process advertise `0.0.0.0/0` to the access layer:

|Zone|Static seed|OSPF originates|BGP originates|
|---|---|---|---|
|VDI|yes|yes (2)|yes|
|Campus|yes, distance 200|yes (4)|yes|
|Access Control|yes|yes (6)|no|
|Management|yes|yes (8)|yes|
|Datacenter|yes|yes (9)|no|
|Test-A / Test-B|yes|yes (91 / 92)|no|
|WiFi Guest|no|no|no|

Campus is the one to watch: its seed sits at distance 200, so if that zone ever learns a default from OSPF, the static goes inactive and origination then depends on which route is actually in the table.

Remove one of those statics and the corresponding zone silently loses its default route — a dependency worth a comment in the configuration.

---

## First-Hop Redundancy

The two HSRP groups are the only places where this router shares a subnet with `VM90-IP-CORE2`. Both sit on global-table sub-interfaces, and this router is configured to be active in both.

### HSRP Group 4 — MPLS Handoff

```cisco
interface Port-channel10.3500
 description OSPF-GLB-MPLS_FASTWEB:L3_Peering
 ip flow monitor FLOWMON-L4-NBAR input
 ip flow monitor FLOWMON-L4-NBAR output
 ip address 10.142.100.21 255.255.255.248
 standby 4 ip 10.142.100.17
 standby 4 priority 120
 standby 4 preempt
 standby 4 authentication ph2ompls
 standby 4 track 5 decrement 10
```

|Element|Effect|
|---|---|
|`ip 10.142.100.17`|Virtual IP presented to the carrier segment|
|`priority 120` + `preempt`|This router is active and reclaims the role after recovery|
|`authentication ph2ompls`|Plaintext HSRP authentication — prevents accidental group joins, not attacks|
|`track 5 decrement 10`|Drops priority to 110 when the carrier next hop stops answering|

The tracking is what makes the group useful. Without it, this router would stay active while holding no usable path to the carrier, black-holing traffic that the peer could have forwarded. With it, losing `10.142.100.18` costs 10 points and the peer — if configured above 110 — takes the VIP.

This is also the only interface with [[#Application Points|flow monitoring]] applied.

### HSRP Group 5 — Partner Segment

```cisco
interface Port-channel10.3302
 description ADM-LESOLUZIONI-EMPOLI_FLUSSI-CALLMANAGER
 ip address 10.142.132.5 255.255.255.248
 standby 5 ip 10.142.132.1
 standby 5 priority 110
 standby 5 preempt
```

A shared segment with an external party carrying CallManager traffic. No authentication and no tracking — a failure beyond this interface will not move the gateway.

---

## External Connectivity

All external connectivity lives in the global table, which is why the zones need [[#Global to VRF — Import Maps|the global leak]] to reach any of it.

### MPLS WAN

`Po10.3500` to the `FASTWEB` MPLS handoff, protected by [[#HSRP Group 4 — MPLS Handoff|HSRP group 4]] and gated by `track 5`. Destinations reached through it are the `track 5` static group — the `10.10/16`, `10.128/15` and `172.20/16` ranges that make up the branch network.

### WAN Managed Service Routers

`WANMS-VM90-RTR1` and `RTR2` appear twice each: on `Po10.3701` and `.3703` in the global table with OSPF 1, and on `Po10.3641` and `.3642` in `IT-VRF-WIFIGUEST` with OSPF 5. The second pair is the guest breakout described in [[#Guest Zone Restriction|the guest restriction]].

### Cloud Exchange

`Po10.3742` and `.3743` to `CLDXT-VM90-RTR1/2`, the only links using `/31` addressing — appropriate for point-to-point and a sign these were built later than the rest.

### External Switch

`SW-VM90-EXT` is the most widely connected peer: global on `Po10.3674`, plus `IT-VRF-APPALTI`, `IT-VRF-WIFIGUEST` and `IT-VRF-TCI`. It is also the next hop for most [[#Per-VRF Defaults|per-VRF defaults]].

### Remote Site VM39

`Po10.3606` carries `IT-VRF-TCI` to `VM39-CORE-SW` inside NSSA area `0.0.0.101`. Because `IT-VRF-TCI` is [[#Isolated VRFs|isolated]], that site is reachable only from within the TCI VRF.

---

## Traffic Visibility

### Flow Record

```cisco
flow record FLOWREC-L4-NBAR
 match ipv4 source address
 match ipv4 destination address
 match ipv4 protocol
 match transport destination-port
 match transport source-port
 match timestamp absolute monitoring-interval start
 match routing vrf input
 collect counter bytes long
 collect counter packets long
 collect timestamp absolute last
 collect flow direction
 collect interface input
 collect interface output
```

A classic five-tuple key, with two additions that matter. `match routing vrf input` puts the ingress VRF in the key, so flows from different zones are never merged — essential on a router where the same address could in principle appear in more than one table. `match timestamp absolute monitoring-interval start` keys each flow to its interval, which is what makes the synchronized cache below work.

Despite the name, there is no `match application name`, so no NBAR classification is performed — see [[#Dead Route-Maps and Prefix-Lists|the observations]].

### Flow Exporter

```cisco
flow exporter FLOWEXP-PRTG
 destination 10.140.2.96
 source Loopback100
 ttl 16
 transport udp 9991
 export-protocol ipfix
 option interface-table
 option vrf-table
 option application-table
```

IPFIX to a PRTG collector on UDP 9991, sourced from `Loopback100` so the collector sees a stable identity regardless of egress path. The three option templates let the collector resolve numeric values into names — `ifIndex` to interface, VRF ID to VRF name, application ID to application. The last has nothing to resolve given the record above.

### Flow Monitor

```cisco
flow monitor FLOWMON-L4-NBAR
 exporter FLOWEXP-PRTG
 cache timeout synchronized 60
 cache type synchronized
 record FLOWREC-L4-NBAR
```

A synchronized cache exports every flow on a fixed 60-second boundary rather than when individual timers expire. The collector therefore receives complete, aligned intervals and can plot rates without interpolating — the reason the record carries `match timestamp absolute monitoring-interval start`.

### Application Points

The monitor is applied on exactly one interface, `Po10.3500`, in both directions. Only MPLS WAN traffic is measured; everything crossing the firewall, the zones and the cloud exchange is invisible to the collector.

---

## Quality of Service

```cisco
class-map match-all CM_POLICE-BE-LEOPARDI
 match access-group name AL_POLICE-BESTEFFORT-TRAFFIC-LEOPARDI
!
policy-map CM_POLICE-BE-RABATTA
 class CM_POLICE-BE-LEOPARDI
  police cir 2000000 conform-action transmit exceed-action drop
!
ip access-list extended AL_POLICE-BESTEFFORT-TRAFFIC-LEOPARDI
 10 permit ip host 172.20.140.62 172.20.5.0 0.0.0.255
```

A 2 Mbit/s policer for traffic from one datacenter host to one branch subnet, presumably a site-specific bandwidth cap. Note the naming: the class-map prefix `CM_` is reused for the policy-map, and the class and policy names refer to different sites.

No `service-policy` statement exists anywhere in the configuration, so none of this is enforced — see [[#Unapplied Policy Map|the observation]].

---

## Management Plane

### AAA and RADIUS

```cisco
aaa new-model
!
radius server radius-mgmnt-auth01
 address ipv4 10.140.2.27 auth-port 1812 acct-port 1813
 timeout 3
 retransmit 3
 key 7 06562C287F4D260A36241D5B
!
aaa group server radius RADSERV
 server name radius-mgmnt-auth01
 ip vrf forwarding Mgmt-intf
 ip radius source-interface GigabitEthernet0
 retransmit 3
 timeout 3
```

`10.140.2.27` is the same management RADIUS server used by the access switches, documented in [[PBA - NAC - Network Access Devices#RADIUS Server Configuration|the NAD note]]. `ip vrf forwarding Mgmt-intf` inside the group is required here: without it, RADIUS packets would be sourced into the global table and never reach the server through the out-of-band port.

Worst-case failover is `(retransmit + 1) × timeout` = 12 seconds, after which the method lists fall through to their local option. There is only one server, so there is no second node to try — the local fallback is the only resilience.

```cisco
aaa authentication login default group RADSERV local-case
aaa authentication login console local-case
aaa authentication login HTTPSRV group RADSERV local-case
aaa authentication enable default enable
aaa authorization exec default group RADSERV if-authenticated
aaa authorization exec HTTPSRV group RADSERV if-authenticated
aaa accounting exec default start-stop group RADSERV
aaa session-id common
```

|Method list|Purpose|Applied|
|---|---|---|
|`default` (login)|RADSERV, then case-sensitive local|Implicitly, to all lines|
|`console`|Local only|Nowhere — see [[#Console Method List Not Applied|
|`HTTPSRV`|RADSERV, then local|Nowhere, since the HTTP server is disabled|
|`enable default`|Local enable secret|Privilege escalation|
|`exec default`|Authorization, or pass if authenticated|Shell authorization|

`local-case` makes the local fallback username case-sensitive. `aaa session-id common` keeps one session ID across authentication, authorization and accounting, so the records correlate — the same reasoning as on [[PBA - NAC - Network Access Devices#Shared Session ID — `aaa session-id common`|the NADs]].

Local credentials: `enable secret 9` (scrypt) and `username admin secret 8` (PBKDF2). Both are current-generation hashes; everything else on the box is reversible type 7 under `service password-encryption`.

### Device Access

```cisco
ip ssh source-interface GigabitEthernet0
ip ssh version 2
ip scp server enable
no ip http server
no ip http secure-server
!
line con 0
 stopbits 1
line aux 0
line vty 0 4
 transport input ssh
```

SSHv2 only, SCP enabled for configuration and image transfer, both HTTP servers disabled. `login on-success log` records successful logins to syslog.

The VTY configuration is thin compared with the access-switch template: no `exec-timeout`, no `session-timeout`, no `logging synchronous`, and only `vty 0 4` defined, so lines 5–15 keep platform defaults. Aligning it with the standard in [[PBA - NAC - Network Access Devices#General Configuration|the NAD note]] would be a small, low-risk change.

### Name Resolution

```cisco
ip name-server 10.140.4.252 10.140.4.250
ip domain name publiacqua.it
```

Two resolvers in the datacenter range, and the domain name that completes unqualified hostnames and forms the FQDN used in certificate subject names. The access-switch template also lists `172.20.129.250` and `172.20.129.252` as third and fourth resolvers; this router does not have them, so a failure of both `10.140.4.x` servers leaves it without name resolution.

### Logging

```cisco
logging buffered 16384 informational
logging facility local3
logging source-interface GigabitEthernet0 vrf Mgmt-intf
logging host 10.140.2.24 vrf Mgmt-intf
logging host 10.140.2.181 vrf Mgmt-intf
logging host 10.139.108.10 vrf Mgmt-intf
!
service timestamps debug datetime msec
service timestamps log datetime localtime
```

Three collectors, all reached through the management VRF — the same three used by the access switches, so core and edge events land together. Facility `local3` distinguishes this device class from the switches' `local6`.

The two `service timestamps` lines are inconsistent: debug output carries milliseconds but UTC, while log output carries local time but whole seconds. Correlating a debug trace against a syslog entry means doing both a timezone and a precision conversion by hand.

### SNMP

```cisco
snmp-server community publiacqua RO
snmp-server host 10.139.108.10 vrf Mgmt-intf version 2c publiacqua
snmp-server trap-source GigabitEthernet0
snmp-server source-interface informs GigabitEthernet0
snmp-server location Via Villamagna 90/C - PUBLIACQUA S.p.A - DataCenter
snmp-server contact NOC Publiacqua S.p.A - networkadmin@publiacqua.it
```

Read-only v2c to a single trap host. Unlike the access switches there is no read-write community, which is the right call on a core device.

The trap list is close to exhaustive — effectively every notification the platform can raise. The ones that matter for this design are `ospf state-change`, `ospf lsa`, `bgp`, `bfd`, `hsrp`, `ipsla`, `vrfmib vrf-up vrf-down`, `flowmon`, `entity-sensor`, `cpu threshold` and `entity-qfp`. The rest cover features not configured here (`isdn`, `frame-relay`, `atm`, `sbc`, `gdoi`, `sonet`) and generate nothing.

SNMPv2c sends the community string in clear text. It is confined to the out-of-band VRF, which limits the exposure, but v3 with authPriv would remove it.

### Time

```cisco
clock timezone CET 1 0
clock summer-time ROME recurring last Sun Mar 2:00 last Sun Oct 2:00
```

The timezone and DST rules are set, but there is no `ntp server` statement — see [[#No NTP Source|the observation]].

### PKI

```cisco
crypto pki trustpoint TP-self-signed-366934226
crypto pki trustpoint SLA-TrustPoint
crypto pki trustpoint DNAC-CA
 enrollment mode ra
 enrollment terminal
 usage ssl-client
 revocation-check crl none
 source interface GigabitEthernet0
```

|Trustpoint|Role|
|---|---|
|`TP-self-signed-366934226`|Auto-generated certificate for the HTTPS server. Inert, since `no ip http secure-server` is configured.|
|`SLA-TrustPoint`|Cisco Licensing Root CA, installed with the image for smart licensing.|
|`DNAC-CA`|Holds `PubliacquaRootCA`, valid from 2024, used as an SSL client. This is the organisation's internal root — the same authority that issues the certificates described in [[PBA - NAC - Microsoft Servers]] — and its presence indicates the device is managed by, or was onboarded through, Cisco Catalyst Center.|

`crypto pki certificate pool` additionally loads the bundle shipped in `nvram:ios_core.p7b`, which is what validates Cisco-signed endpoints such as Smart Licensing and Call Home.

`revocation-check crl none` tries CRL first and accepts the certificate if no CRL is reachable. That is the pragmatic setting for a device that may have no path to the CRL distribution point, and it does weaken revocation.

### Licensing and Call Home

```cisco
license boot level network-advantage
license smart transport off
!
call-home
 contact-email-addr sch-smart-licensing@cisco.com
 profile "CiscoTAC-1"
  active
  destination transport-method http
```

The boot level licenses the features in use, but `license smart transport off` means the device never reports usage to a Smart Software Manager or satellite. Call Home is active to Cisco TAC over HTTP, which is a separate channel from licensing.

### Discovery Protocols

`cdp run` and `lldp run` are both enabled. CDP feeds the aggregation switches' neighbour tables and Catalyst Center's topology view; LLDP covers any non-Cisco peer. On a core router with only known infrastructure neighbours the exposure is minimal, and the operational value of accurate neighbour data is high.

### Operator Aliases

```cisco
alias exec s show ip int brie
alias exec sps show etherchannel summary
alias exec sis show interface status
alias exec scn show cdp neighbors
alias exec sid show interface description
alias exec siv show ip route vrf
alias exec sion show ip ospf neig
alias exec sri show run int
alias exec sr show runn
```

Local shortcuts. `siv` and `sion` are the two worth remembering — `siv <vrf>` and `sion` cover most day-to-day work on this device. Note they are configuration, so they exist only here and not on the switches.

---

## Verification

### Segmentation and Leaking

```cisco
show vrf detail
show vrf detail IT-VRF-CAMPUS | include Import|Export|Route-target
show ip route vrf IT-VRF-CAMPUS
show ip route vrf IT-VRF-CAMPUS-BACKBONE
show bgp vpnv4 unicast all summary
show bgp vpnv4 unicast vrf IT-VRF-CAMPUS
show bgp ipv4 unicast
show bgp vpnv4 unicast all community 4259905600
show ip route vrf IT-VRF-CAMPUS 0.0.0.0
```

The first check for any leaking problem is whether the route reached BGP at all, then whether the import map permitted it, then whether the tag let it into OSPF.

### OSPF and BFD

```cisco
show ip ospf neighbor
show ip ospf 4 neighbor
show ip ospf interface brief
show ip ospf database nssa-external
show ip ospf 7 border-routers
show bfd neighbors
show bfd summary
```

`show ip ospf interface brief` is the fastest way to confirm which process and area an interface landed in, and `show bfd neighbors` is the check for [[#BFD Without Timers|the BFD question]].

### Forwarding and Redundancy

```cisco
show standby brief
show track brief
show ip sla statistics
show ip sla configuration 4
show etherchannel summary
show interface description
show ip route 0.0.0.0
```

`show track brief` and `show ip sla statistics` together answer whether the tracked statics are installed and why.

### Flow and Management Plane

```cisco
show flow monitor FLOWMON-L4-NBAR cache
show flow exporter FLOWEXP-PRTG statistics
show flow interface Port-channel10.3500
show aaa servers
show radius statistics
show logging | include %OSPF|%BGP|%HSRP
show crypto pki certificates
show license summary
show platform hardware qfp active datapath utilization
```

---

## Observations

Items found while reading the configuration. None is an outage in progress; each is either a latent inconsistency, a piece of dead configuration, or something whose runtime state should be confirmed before it is trusted.

### Malformed Community Value

```cisco
ip community-list expanded FROM-GLOBAL-TO-ACCESS-CONTROL permit 4249905602
ip community-list expanded FROM-GLOBAL-TO-VDI permit 4249905602
```

`4249905602` decodes to `64848:27074`. Every other value in the scheme sits in `65001:`, and the intended value is almost certainly `4259905602` (`65001:66`, Access Control) — one digit transposed.

Two consequences, both real:

- `FROM-GLOBAL-TO-ACCESS-CONTROL` no longer contains Access Control's own community, so routes that zone exported to global can be imported straight back into it.
- `FROM-GLOBAL-TO-VDI` no longer denies Access Control's routes, so Access Control subnets leak into VDI through the global table. VDI and Access Control are permitted to communicate by [[#Inter-Zone Reachability Matrix|the matrix]] — but through the firewall, and this path bypasses it.

Separately, `FROM-GLOBAL-TO-ACCESS-CONTROL` omits Management's community and `FROM-GLOBAL-TO-MGMNT` omits Access Control's. Because the omission is symmetric it may be deliberate, but it contradicts the route-target matrix, where those two zones are the only pair with no adjacency. Worth confirming against the intended policy.

### BFD Without Timers

Every OSPF process carries `bfd all-interfaces` and most sub-interfaces carry `ip ospf bfd`, but no interface has `bfd interval … min_rx … multiplier …` and no `bfd template` is defined. Without timers, IOS-XE has no parameters with which to bring a session up, so the sub-second detection this design implies may not exist. Check `show bfd neighbors` — if it is empty, OSPF is falling back to the default 40-second dead interval on every link.

### Unreachable IP SLA Source

```cisco
ip sla 4
 icmp-echo 10.142.96.85 source-ip 10.142.96.82
```

No interface on this router carries `10.142.96.82`, and `10.142.96.85` is not in any connected subnet either — the next hop resolves recursively. The `10.142.96.104/29` entry in `DC-SUBNETS` shows the range exists elsewhere in the network, which suggests this block was carried over from the device this router replaced.

If `track 4` is down, roughly thirty static routes to legacy and partner ranges are not installed. Confirm with `show track 4` and `show ip sla statistics 4` before assuming those destinations are reachable.

### OSPF `network` Statement Typo

```cisco
router ospf 2 vrf IT-VRF-VDI
 network 10.146.26.24 0.0.0.3 area 0.0.0.0
```

`10.146.26.24/30` matches nothing on this router. The VDI interface it was presumably meant to match is `Po10.3610`, in `10.142.24.24/30` — `142` typed as `146`. Harmless in practice, because the interface already carries `ip ospf 2 area 0.0.0.0`, which is how every other interface joins its process. The equivalent statement under `router ospf 4` (`10.142.24.108 0.0.0.3`) is correct, and equally redundant.

### Asymmetric Path Costs

Campus (`.3634` / `.3636`) and Datacenter (`.3681` / `.3683`) have no `ip ospf cost 120` on the second aggregation link, so those two zones load-share across both aggregation routers while every other zone fails over. Either behaviour is defensible; having both in the same device is likely an oversight. Load-sharing also makes troubleshooting harder, since a flow's path depends on its hash.

The same applies to `no ip redirects` and `no ip proxy-arp`, present on most sub-interfaces but missing on a few — `Po10.3300`, `.3610`, `.3634` and `.3639` among them.

### Unapplied Policy Map

`CM_POLICE-BE-RABATTA` exists with its class-map and ACL, but no interface has a `service-policy`. The 2 Mbit/s cap is not being enforced. Either it was removed during troubleshooting and not reinstated, or the requirement lapsed and the configuration was left behind.

### Dead Route-Maps and Prefix-Lists

Roughly twenty route-maps are defined and never referenced. They fall into three groups:

|Group|Members|
|---|---|
|Earlier leak design|`RMP-IT-VRF-*-BGP` (six), `LEAK-*-TO-GLOBAL` and `LEAK-GLOBAL-TO-*` (eight)|
|Test and scratch|`red-ospf-tag`, `CHECK-TAG`, `RF-TEST-A-BGP`, `test_lorenzo`, `SET-TAG-TO-TEST-A`, `IMPORT-GLOBAL-TO-A`, `TEST-A-TO-GLOBAL`, `VRF-TEST-A-BGP`, `VRF-TEST-B-BGP`|
|Guest, superseded|`WIFI-GUEST`, `IMPORT-WIFI-GUEST` and prefix-list `WIFI_GUEST`|

Also unreferenced: `ip extcommunity-list expanded EXT-CML-LORENZO`, standard ACLs `IMPORT-CAMPUS` and `VRF-TO-GLB`, and prefix-lists `GLOBAL`, `BGP` and the `IT-VRF-*-SUBNETS` set.

The `flow record` name `FLOWREC-L4-NBAR` belongs in the same category — it promises NBAR classification the record does not perform, and `option application-table` on the exporter exists to support it.

None of this affects forwarding. It does affect the next person reading the configuration, who has to establish for each object whether it is load-bearing before touching anything.

### Mutual Redistribution Between OSPF 1 and BGP

`router ospf 1` redistributes BGP with no filter, and the global BGP address-family redistributes OSPF 1 with no filter. Mutual redistribution without tags or prefix filtering is the classic setup for route feedback: a static becomes an OSPF external, gets picked up by BGP, and can be reoriginated. The VRF paths are protected by [[#NO-RED-TAG Maps|the tag filters]], but the global path has no equivalent.

It is likely stable today because the routes involved originate locally. Adding a tag-and-deny pair on the global side, matching the pattern already used in the VRFs, would make it safe by construction rather than by circumstance.

### No NTP Source

`clock timezone` and `clock summer-time` are configured; `ntp server` is not. The clock is whatever it was set to, drifting. Log correlation across the three syslog collectors, certificate validity checks in the [[#PKI|PKI]] trustpoints, and the timestamps in [[#Flow Record|exported flow records]] all depend on it. The access-switch template configures `172.20.129.64` and `172.20.129.65` — the same servers, reachable through the management VRF, would fix this in two lines.

### Console Method List Not Applied

`aaa authentication login console local-case` defines a console-only local method list, but `line con 0` contains only `stopbits 1` — there is no `login authentication console`. The console therefore uses the `default` list, which tries RADIUS first. The local fallback still works, so this is not a lockout risk; the intended behaviour of a console that never depends on the network is simply not in effect. One line under `line con 0` realises it.

### Test Artifacts in a Production Table

`VRF-TEST-A` and `VRF-TEST-B` are fully built out — VRFs, backbone VRFs, RDs, route-targets, import and export maps, firewall sub-interfaces, four OSPF processes, tag filters and static routes. Together with `ip route 2.3.4.5/32 Null0`, `1.1.1.1/32`, `100.100.100.100/32`, `2.2.2.2/32`, prefix-list `BGP` (`10.20.30.40/32`) and `route-map test_lorenzo`, they represent a meaningful amount of live configuration serving no production purpose.

They are also the best documentation of the intended pattern in the file: `VRF-TEST-A` plus `VRF-TEST-A-BACKBONE` is the production zone model in miniature, which makes them useful for validating a change before it touches a real zone. Worth keeping deliberately, with a comment saying so, or removing deliberately — the current ambiguity is the problem.