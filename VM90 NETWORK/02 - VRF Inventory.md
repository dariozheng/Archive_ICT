---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
title: VRF Inventory
tags:
  - network/cisco
  - vrf
  - reference
  - category/networking/networking_general
up: "[[00 - MOC - VM90-IP-CORE1 Routing]]"
icon: FasNetworkWired
iconColor:
last_update: 2026-09-21
---

# VRF Inventory

Every VRF defined on VM90-IP-CORE1, what it is for, and whether it is actually doing anything.

---

## Master table

| VRF | RD | Export RT | Import RTs | OSPF proc | BGP AF? | Leaks to global? | Status |
|---|---|---|---|---|---|---|---|
| `IT-VRF-CAMPUS` | 65001:20 | 65001:20 | 65001:20 | 4 | ✅ | ✅ import + export map | **Live - service** |
| `IT-VRF-WIFIGUEST` | 65001:21 | 65001:21 | 65001:21 | 5 | ❌ | ❌ | Live interfaces, **no leaking** |
| `IT-VRF-ACCESS-CONTROL` | 65001:22 | 65001:22 | 65001:22 | 6 | ✅ | ✅ import + export map | **Live - service** |
| `IT-VRF-DC` | 65001:23 | 65001:23 | 65001:23 | 9 | ✅ | ✅ import + export map | **Live - service** |
| `IT-VRF-VDI` | 65001:24 | 65001:24 | 65001:24 | 2 | ✅ | ✅ import + export map | **Live - service** |
| `IT-VRF-TCI` | 65001:25 | 65001:25 | 65001:25 | 7 | ❌ | ❌ | Live interfaces, **island** |
| `IT-VRF-BACKBONE` | 65001:26 | 65001:26 | 65001:26, :24 | – | ✅ (connected only) | ✅ maps named `*_VDI_*` | **No interfaces - dead** |
| `IT-VRF-MGMNT` | 65001:29 | 65001:29 | 65001:29 | 8 | ✅ | ✅ import + export map | **Live - service** |
| `IT-MON-VRF` | 65001:32 | – | – | 10 | ❌ | ❌ | Live interfaces, **island** |
| `TEMP` | 65001:33 | – | 65001:20 + import map | – | ❌ | ❌ | No interfaces - **dead** |
| `IT-VRF-VDI-BACKBONE` | 65001:62 | 65001:62 | :62, :66, :68, :64, :69 | 62 | ✅ | ❌ | **Live - backbone** |
| `IT-VRF-CAMPUS-BACKBONE` | 65001:64 | 65001:64 | :64, :66, :68, :62, :69 | 64 | ✅ | ❌ | **Live - backbone** |
| `IT-VRF-WIFIGUEST-BACKBONE` | 65001:65 | 65001:65 | :65, :69 | 65 | ✅ | ❌ | **Live - backbone** |
| `IT-VRF-ACCESS-CONTROL-BACKBONE` | 65001:66 | 65001:66 | :66, :64, :62, :69 | 66 | ✅ | ❌ | **Live - backbone** |
| `IT-VRF-MGMNT-BACKBONE` | 65001:68 | 65001:68 | :68, :64, :62, :69 | 68 | ✅ | ❌ | **Live - backbone** |
| `IT-VRF-DC-BACKBONE` | 65001:69 | 65001:69 | :69, :66, :65, :68, :64, :62 | 69 | ✅ | ❌ | **Live - backbone** |
| `VRF-TEST-A` | 65001:91 | 65001:91 | 65001:91 | 91 | ✅ | ✅ import + export map | **Lab** |
| `VRF-TEST-B` | 65001:92 | 65001:92 | 65001:92 | 92 | ✅ | ✅ import + export map | **Lab** |
| `VRF-TEST-A-BACKBONE` | 65001:93 | 65001:93 | :93, :94 | 93 | ✅ | ❌ | **Lab backbone** |
| `VRF-TEST-B-BACKBONE` | 65001:94 | 65001:94 | :94, :93 | 94 | ✅ | ❌ | **Lab backbone** |
| `IT-VRF-APPALTI` | **none** | – | – | 3 | ❌ | ❌ | Live interfaces, **island, cannot ever leak** |
| `IT-VRF-FIWIFI` | none | – | – | – | ❌ | ❌ | **Empty shell** |
| `MON-VRF` | none | – | – | – | ❌ | ❌ | **Empty shell** |
| `OT-VRF` | none | – | – | – | ❌ | ❌ | **Empty shell** |
| `OT-VRF-DC` | none | – | – | – | ❌ | ❌ | **Empty shell** |
| `OT-VRF-FIELD` | none | – | – | – | ❌ | ❌ | **Empty shell** |
| `Mgmt-intf` | none | – | – | – | ❌ | ❌ | Out-of-band `Gi0` only |

---

## Route-target number → VRF quick lookup

Keep this next to you when reading `show vrf detail` or `show bgp vpnv4 unicast all`.

| RT | VRF | Layer |
|---|---|---|
| `65001:20` | IT-VRF-CAMPUS | service |
| `65001:21` | IT-VRF-WIFIGUEST | service |
| `65001:22` | IT-VRF-ACCESS-CONTROL | service |
| `65001:23` | IT-VRF-DC | service |
| `65001:24` | IT-VRF-VDI | service |
| `65001:25` | IT-VRF-TCI | service |
| `65001:26` | IT-VRF-BACKBONE | dead |
| `65001:29` | IT-VRF-MGMNT | service |
| `65001:62` | IT-VRF-VDI-BACKBONE | backbone |
| `65001:64` | IT-VRF-CAMPUS-BACKBONE | backbone |
| `65001:65` | IT-VRF-WIFIGUEST-BACKBONE | backbone |
| `65001:66` | IT-VRF-ACCESS-CONTROL-BACKBONE | backbone |
| `65001:68` | IT-VRF-MGMNT-BACKBONE | backbone |
| `65001:69` | IT-VRF-DC-BACKBONE | backbone |
| `65001:91` / `:92` | VRF-TEST-A / B | lab service |
| `65001:93` / `:94` | VRF-TEST-A / B -BACKBONE | lab backbone |

> [!tip] Mnemonic
> Service VRFs live in the **20s**. Their backbone twins live in the **60s**. Lab VRFs live in the **90s**. The service RT and its backbone RT are unrelated numbers (CAMPUS is `:20`, CAMPUS-BACKBONE is `:64`) - do not expect a pattern there.

---

## The four families

### A. Service VRFs with full leaking

`IT-VRF-CAMPUS`, `IT-VRF-DC`, `IT-VRF-VDI`, `IT-VRF-MGMNT`, `IT-VRF-ACCESS-CONTROL`

These have the complete kit:
- Their own OSPF process down to the aggregation switches (`VM90-IP-AGGR1/2`).
- A BGP address-family redistributing connected, static and their OSPF.
- An `import ipv4 unicast map` + `export ipv4 unicast map` pair for talking to the global table.
- A subinterface on `Port-channel11` toward the FTD4125 firewall.
- A `*-BACKBONE` twin.

They import **only their own route-target**, so they never receive routes from a sibling VRF directly. That is intentional - see [[03 - Service and Backbone VRFs]].

### B. Backbone VRFs

`IT-VRF-*-BACKBONE`, `VRF-TEST-*-BACKBONE`

These exist only to sit on the far side of the firewall. They have:
- One interface only: a `Port-channel11.xxxx` subinterface to the FTD.
- An OSPF process with `passive-interface default` and one explicit `no passive-interface` - so they speak OSPF to the firewall and to nothing else.
- A BGP address-family that redistributes **only** their OSPF process (no `redistribute connected`, no `redistribute static`).
- A rich `route-target import` list - this is the actual zone-to-zone policy.
- **No** global-table leaking.

### C. Islands

`IT-VRF-TCI`, `IT-VRF-APPALTI`, `IT-MON-VRF`, and (for leaking purposes) `IT-VRF-WIFIGUEST`

These have live interfaces and a working OSPF process, but **no BGP address-family**. No BGP address-family means:
- nothing is ever put into the shared BGP table,
- so their export route-target never gets applied to anything,
- so no other VRF can import them,
- and they can never receive a route from the global table.

They are fully isolated routing domains. `IT-VRF-TCI` even has `route-target export 65001:25` configured, which does precisely nothing today.

> [!info] `IT-VRF-APPALTI` is doubly isolated
> It has **no `rd` at all**. A VRF without an RD cannot be given a BGP address-family, full stop. Adding one requires adding `rd 65001:xx` first - and adding an RD to a live VRF is disruptive to any existing BGP state, so plan it.

`IT-VRF-WIFIGUEST` is a special case: the *service* VRF is an island, but its *backbone* twin `IT-VRF-WIFIGUEST-BACKBONE` does participate. See the guest-wifi example in [[06 - Worked Examples]].

### D. Empty shells and leftovers

`IT-VRF-FIWIFI`, `MON-VRF`, `OT-VRF`, `OT-VRF-DC`, `OT-VRF-FIELD`, `TEMP`, `IT-VRF-BACKBONE`

Declared, never used. `IT-VRF-BACKBONE` is the most confusing one because it *looks* alive - it has an RD, route-targets, a BGP address-family with `redistribute connected`, and import/export maps called `VRF_GLOBAL_TO_VDI` / `VRF_VDI_TO_GLOBAL`. But no interface is assigned to it, so `redistribute connected` finds nothing and the whole block is inert. Its name also does not match the `*-BACKBONE` convention used everywhere else. Listed in [[08 - Findings and Cleanup]].

---

## OSPF process ↔ VRF map

You will need this constantly, because the config refers to processes by number.

| Proc | VRF | Notes |
|---|---|---|
| `1` | global | WAN / external, `redistribute bgp` and `redistribute static` |
| `2` | IT-VRF-VDI | has a stale `network 10.146.26.24 0.0.0.3` statement |
| `3` | IT-VRF-APPALTI | no redistribution, no `capability vrf-lite` |
| `4` | IT-VRF-CAMPUS | also `redistribute static` |
| `5` | IT-VRF-WIFIGUEST | no `redistribute bgp` |
| `6` | IT-VRF-ACCESS-CONTROL | |
| `7` | IT-VRF-TCI | has NSSA area `0.0.0.101` toward VM39 |
| `8` | IT-VRF-MGMNT | |
| `9` | IT-VRF-DC | |
| `10` | IT-MON-VRF | monitoring / PRTG path |
| `62` | IT-VRF-VDI-BACKBONE | |
| `64` | IT-VRF-CAMPUS-BACKBONE | |
| `65` | IT-VRF-WIFIGUEST-BACKBONE | |
| `66` | IT-VRF-ACCESS-CONTROL-BACKBONE | |
| `68` | IT-VRF-MGMNT-BACKBONE | |
| `69` | IT-VRF-DC-BACKBONE | |
| `91` / `92` | VRF-TEST-A / B | lab |
| `93` / `94` | VRF-TEST-A / B -BACKBONE | lab |

> [!note] Backbone processes use the same number as their route-target
> OSPF 64 ↔ RT `65001:64` ↔ `IT-VRF-CAMPUS-BACKBONE`. Handy. The service VRFs do not follow this pattern.

---

## Where the VRFs physically live

| Port-channel | Peer | Purpose |
|---|---|---|
| `Po10` (8 × 10G) | `VM90-DC-L2-AGGR1/2` | Subinterfaces down to the aggregation/core switches and the WAN routers. This is where the **service VRFs** face the network. |
| `Po11` (4 × 10G) | `VM90-DC-L2-AGGR1/2` → `FTD4125-BACK` | Subinterfaces to the firewall. Each zone appears **twice**: once as the service VRF, once as the backbone VRF. |
| `Gi0` | OOB switch | `Mgmt-intf` VRF, `10.140.0.113/24`, used for SSH/RADIUS/syslog/SNMP/TFTP source |
| `Lo100` | – | `10.100.100.100/32`, BGP router-id and NetFlow exporter source |

---

## Next

→ [[03 - Service and Backbone VRFs]] for why every zone appears twice.
