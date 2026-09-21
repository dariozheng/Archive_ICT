---
title: Findings, risks and cleanup
tags:
  - network/cisco
  - findings
  - review
up: "[[00 - MOC - VM90-IP-CORE1 Routing]]"
---

# Findings, risks and cleanup

Everything below was found by reading the `show run` of 2026-07-29. **None of it has been verified against the live device.** Each item lists how to confirm it before acting.

Ordered roughly by impact.

---

## 🔴 P1 - Segmentation holes

### F1 - Community typo breaks two deny filters

```cisco
ip community-list expanded FROM-GLOBAL-TO-ACCESS-CONTROL permit 4249905602
ip community-list expanded FROM-GLOBAL-TO-VDI            permit 4249905602
```

`4249905602` should be `4259905602`. One digit (`424` vs `425`). The correct value appears written properly in `FROM-GLOBAL-TO-CAMPUS` and `FROM-GLOBAL-TO-DC`, so this is a transcription slip.

| | Intended | Actual |
|---|---|---|
| `4259905602` | `65001:66` = "came from ACCESS-CONTROL" | – |
| `4249905602` | – | `64848:27074`, set by nothing |

**Effect**
- `IT-VRF-VDI` does not block access-control routes arriving from global → **VDI can route to access-control subnets without the firewall**.
- `IT-VRF-ACCESS-CONTROL` does not block its own community → it re-imports its own exported routes from global (an echo, potentially installing a worse path over the real one).

**Verify**
```
show ip route vrf IT-VRF-VDI | include 10.  (look for access-control subnets)
show bgp vpnv4 unicast vrf IT-VRF-VDI <an-AC-prefix>
show ip community-list FROM-GLOBAL-TO-VDI
```

**Fix**
```cisco
no ip community-list expanded FROM-GLOBAL-TO-ACCESS-CONTROL permit 4249905602
ip community-list expanded FROM-GLOBAL-TO-ACCESS-CONTROL permit 4259905602
no ip community-list expanded FROM-GLOBAL-TO-VDI permit 4249905602
ip community-list expanded FROM-GLOBAL-TO-VDI permit 4259905602
```
Then `clear ip bgp * soft` (or `clear bgp vpnv4 unicast * soft`) and re-check. Expect routes to **disappear** from VDI - confirm nothing depends on them first.

---

### F2 - ACCESS-CONTROL ↔ MGMNT leak through the global table

`FROM-GLOBAL-TO-ACCESS-CONTROL` has no entry for `4259905604` (MGMNT) and `FROM-GLOBAL-TO-MGMNT` has no entry for `4259905602` (AC). Both directions are open.

This **contradicts the backbone layer**, where `IT-VRF-ACCESS-CONTROL-BACKBONE` deliberately omits `route-target import 65001:68` and `IT-VRF-MGMNT-BACKBONE` deliberately omits `65001:66`. Someone decided those zones should not exchange routes; the global filters were not updated to match.

**Decide first:** should management reach access control? If yes, do it properly at the backbone layer so the firewall sees it. If no, close the hole.

**Fix (close the hole)**
```cisco
ip community-list expanded FROM-GLOBAL-TO-ACCESS-CONTROL permit 4259905604
ip community-list expanded FROM-GLOBAL-TO-MGMNT permit 4259905602
```

---

### F3 - Two export maps have no prefix filter

```cisco
route-map EXPORT-VDI-TO-GLOBAL permit 10
 set community 4259905598
!
route-map EXPORT-ACCESS-CONTROL-TO-GLOBAL permit 10
 set community 4259905602
```

No `match` clause → **the entire VRF BGP table is exported to global**, including transit /30s and anything those VRFs learned from elsewhere. CAMPUS, DC and MGMNT all use a curated prefix-list; these two do not.

Combined with F1 and F2, the leaks above are not limited to a handful of server subnets.

**Fix** - build explicit lists and use them, mirroring the CAMPUS pattern:
```cisco
ip prefix-list VDI-EXPORT-SUBNETS seq 5 permit 10.140.128.0/20
!
route-map EXPORT-VDI-TO-GLOBAL permit 10
 match ip address prefix-list VDI-EXPORT-SUBNETS
 set community 4259905598
```
Note `VDI-SUBNETS` already exists (`10.140.128.0/20`) but is only referenced by the dead `VRF_GLOBAL_TO_VDI` map - reuse or rename it rather than creating a third list.

---

## 🟠 P2 - Availability risks

### F4 - IP SLA 4 source address is not local

```cisco
ip sla 4
 icmp-echo 10.142.96.85 source-ip 10.142.96.82
```

No interface on this router carries `10.142.96.82`. An IP SLA source must be a local address. If the probe cannot start, `track 4` is down, and **all 32 static routes with `track 4` are not installed**:

`10.20.208.0/22`, `10.20.220.0/24`, `10.55.33/34/36/65/77.0/24`, `10.57.37.0/24`, `10.70.16.0/20`, `10.115.56.0/24`, `10.122.32.0/19`, `10.240.0.192/29`, `10.243.0.0/16`, `172.16.*`, `172.21.*`, `172.30.10.0/24`.

Because global statics feed BGP (`redistribute static`) which feeds every service VRF's import map, **losing track 4 removes those destinations from CAMPUS, DC, VDI, MGMNT and ACCESS-CONTROL simultaneously.**

**Verify**
```
show track 4
show ip sla statistics 4
show ip route 10.122.32.0
```

If `show track 4` reports Up, the address exists somewhere this config does not show (e.g. an interface added after the snapshot, or the SLA is sourcing from a secondary address) - in which case this finding is void. Check before touching anything.

**Related:** `ip sla 6` (sourcing from `10.142.25.138`, valid) has **no tracked object** referencing it. It runs and nothing consumes the result. Either wire it to a track or remove it.

---

### F5 - Mutual redistribution in the global table with no guard

```cisco
router ospf 1
 redistribute bgp 65001                                      ! no route-map
!
router bgp 65001
 address-family ipv4
  redistribute ospf 1 match internal external 1 external 2   ! no route-map
```

Every other VRF on this box has a tag guard on exactly this pair of commands. Global does not.

**Effect**
- Everything exported from any VRF (`EXPORT-*-TO-GLOBAL`) is flooded into the OSPF 1 domain as E2 and then read back into BGP.
- OSPF's AD (110) beats locally-originated BGP (200), so the RIB usually settles rather than looping - but the database churns on every VRF subnet change, and there is no brake on an accidental export propagating out to the WAN routers.

**Fix** - apply the same pattern already used everywhere else:
```cisco
route-map GLOBAL-FROM-BGP permit 10
 set tag 700
!
route-map GLOBAL-TO-BGP deny 5
 match tag 700
!
route-map GLOBAL-TO-BGP permit 200
!
router ospf 1
 redistribute bgp 65001 route-map GLOBAL-FROM-BGP
!
router bgp 65001
 address-family ipv4
  redistribute ospf 1 match internal external 1 external 2 route-map GLOBAL-TO-BGP
```
Use a **new** tag value (700 here) rather than reusing 80/800 so the two domains stay independently debuggable. Do this in a maintenance window - it changes what the WAN routers see.

---

### F6 - Expanded community-lists are fragile

Every community-list in the config is `expanded`, which means the value is a **regular expression matched against the text form** of the route's communities.

Two risks:

1. **Unanchored regex.** `permit 4259905600` would also match a longer community string containing those digits. No collision exists today, but adding a value could silently create one.
2. **Format dependency.** These lists only work while IOS renders communities as raw decimals. If `ip bgp-community new-format` is ever enabled, communities render as `65001:64` and **every decimal expanded list stops matching** - which means every `IMPORT-*-FROM-GLOBAL` deny filter fails open and the VRFs start importing each other's routes.

**Verify**
```
show run | include bgp-community
show ip community-list
show bgp vpnv4 unicast vrf IT-VRF-CAMPUS <prefix>    (look at how communities are printed)
```

**Fix** - convert to `standard` lists with explicit values:
```cisco
ip community-list standard FROM-GLOBAL-TO-CAMPUS permit 4259905602
```
Same values, exact match, format-independent. Test on one list first.

---

## 🟡 P3 - Hardening

### F7 - OSPF uses simple-password authentication

```cisco
area 0.0.0.0 authentication
ip ospf authentication-key 7 <hidden>
```

`area X authentication` (without `message-digest`) is **type 1** - the password travels in the clear in every OSPF packet. Type 7 encoding in the config is obfuscation, reversible in seconds.

Better: `area 0.0.0.0 authentication message-digest` + `ip ospf message-digest-key 1 md5 <key>`, or on 17.6, OSPF key chains with SHA. This is a coordinated change across every OSPF speaker in the VRF - plan per-VRF, not all at once.

Also note several keys are **reused across different VRFs** (the same type-7 string appears on CAMPUS, DC and TEST-A interfaces). One compromised key affects several zones.

### F8 - SNMP and management

```cisco
snmp-server community publiacqua RO
snmp-server host 10.139.108.10 vrf Mgmt-intf version 2c publiacqua
```

SNMPv2c with a community string equal to the company name. Outside the scope of the routing design, but worth logging: consider SNMPv3 with auth+priv.

Positives worth keeping: `aaa new-model` with RADIUS + local fallback, `transport input ssh` only, `ip ssh version 2`, all management sourced from `Gi0` in `Mgmt-intf`, `no ip http server`.

---

## 🔵 P4 - Dead configuration

None of this is dangerous. It is noise that makes the config harder to read and audit, and it creates traps for the next engineer ("is `RMP-IT-VRF-CAMPUS-BGP` used? better not touch it").

### Route-maps referenced by nothing

`RMP-IT-VRF-WIFIGUEST-BGP`, `RMP-IT-VRF-MGMNT-BGP`, `RMP-IT-VRF-VDI-BGP`, `RMP-IT-VRF-ACCESS-CONTROL-BGP`, `RMP-IT-VRF-DC-BGP`, `RMP-IT-VRF-CAMPUS-BGP`, `VRF-TEST-A-BGP`, `VRF-TEST-B-BGP`, `red-ospf-tag`, `CHECK-TAG`, `RF-TEST-A-BGP`, `test_lorenzo`, `WIFI-GUEST`, `IMPORT-WIFI-GUEST`, `TEST-A-TO-GLOBAL`, `SET-TAG-TO-TEST-A`, `IMPORT-GLOBAL-TO-A`, `LEAK-IT-VRF-MGMNT-TO-GLOBAL`, `LEAK-GLOBAL-TO-IT-VRF-MGMNT`, `LEAK-IT-VRF-DC-TO-GLOBAL`, `LEAK-GLOBAL-TO-IT-VRF-DC`, `LEAK-IT-VRF-CAMPUS-TO-GLOBAL`, `LEAK-GLOBAL-TO-IT-VRF-CAMPUS`, `LEAK-ACCESS-CONTROL-TO-GLOBAL`, `LEAK-GLOBAL-TO-ACCESS-CONTROL`.

The `LEAK-*` family looks like an earlier design iteration that was replaced by the `IMPORT-*-FROM-GLOBAL` / `EXPORT-*-TO-GLOBAL` family.

> [!danger] Do not enable `SET-TAG-TO-TEST-A`
> It has a catch-all `permit 20` with no match. If it were ever applied to a `redistribute bgp` under an OSPF VRF process, it would create the exact feedback loop that `SET-TAG-TO-GLOBAL-COMMUNITY`'s implicit deny prevents. See [[05 - Tags 80 and 800]].

### VRFs with no interfaces

`IT-VRF-FIWIFI`, `MON-VRF`, `OT-VRF`, `OT-VRF-DC`, `OT-VRF-FIELD`, `TEMP`, `IT-VRF-BACKBONE`.

`IT-VRF-BACKBONE` is the misleading one - it has an RD, route-targets, a BGP address-family and import/export maps, but no interfaces, so `redistribute connected` finds nothing. Its maps are named `VRF_GLOBAL_TO_VDI` / `VRF_VDI_TO_GLOBAL`, which suggests it was a VDI experiment. Its name also breaks the `*-BACKBONE` convention.

`MON-VRF` vs `IT-MON-VRF` is a genuine trap - one is live, one is empty, and they differ by three characters.

### Lab leftover routes

```cisco
ip route 2.3.4.5 255.255.255.255 Null0
ip route vrf IT-VRF-ACCESS-CONTROL-BACKBONE 2.2.2.2 255.255.255.255 Null0
ip route vrf VRF-TEST-A 1.1.1.1 255.255.255.255 10.142.28.18
ip route vrf VRF-TEST-A-BACKBONE 100.100.100.100 255.255.255.255 Null0
```

⚠️ `2.3.4.5/32` is in the **global** table and therefore gets redistributed into global BGP, imported into every service VRF, tagged 800, and flooded into five OSPF domains. A junk /32 with real reach.

⚠️ `100.100.100.100/32` is one digit away from `10.100.100.100` (the router-id / Loopback100). Confusing at 3 a.m.

### Other odds and ends

| Item | Note |
|---|---|
| `router ospf 2` `network 10.146.26.24 0.0.0.3 area 0.0.0.0` | No interface matches `10.146.x`. Stale |
| `router ospf 4` `network 10.142.24.108 0.0.0.3 area 0.0.0.0` | Matches `Po10.3634` (`.110/30`), but the interface already has `ip ospf 4 area 0`. Redundant, harmless |
| `IT-VRF-TCI` route-targets `65001:25` | Configured, inert - no BGP address-family exists for TCI |
| `IT-VRF-WIFIGUEST` route-targets `65001:21` | Same. Also duplicated inside and outside the address-family |
| `IT-VRF-APPALTI` | No `rd` - cannot ever have a BGP address-family until one is added |
| `ip prefix-list BGP seq 5 permit 10.20.30.40/32`, `ip prefix-list GLOBAL`, `ip access-list standard VRF-TO-GLB`, `ip extcommunity-list EXT-CML-LORENZO` | Test artefacts |
| `ip prefix-list IMPORT-CAMPUS` and `ip access-list standard IMPORT-CAMPUS` | Same name, two different object types. `route-map IMPORT-CAMPUS-TO-TEMP` uses the **prefix-list**. Rename one |
| `class-map CM_POLICE-BE-LEOPARDI` / `policy-map CM_POLICE-BE-RABATTA` | Defined, applied to no interface. Also `class-map` and `policy-map` names do not match each other |
| `vrf definition IT-VRF-WIFIGUEST` | `route-target export/import 65001:21` appears twice, once at VRF level and once under the address-family |

### Four identical guard route-maps

`NO-RED-TAG-TO-GLOBAL`, `NO-RED-TAG-TO-LEAK`, `NO-RED-TAG-80`, `NO-RED-TAG-800` all mean "deny tag 80 or 800, permit everything else". Consolidating to one (e.g. `NO-RED-TAGGED-ROUTES`) removes three places to forget when the tag scheme changes. Low priority, zero functional risk, but do it in a window - it touches 15 `redistribute` statements.

---

## Suggested order of work

| Step | Item | Risk | Window needed |
|---|---|---|---|
| 1 | Verify F4 (`show track 4`) | none - read only | no |
| 2 | Verify F6 (community format) | none - read only | no |
| 3 | Decide the AC ↔ MGMNT policy question (F2) | none - a decision | no |
| 4 | Fix F1 typo | **removes routes** | yes |
| 5 | Close F2 | **removes routes** | yes |
| 6 | Tighten F3 exports | **removes routes** | yes |
| 7 | Add the global guard (F5) | changes WAN view | yes |
| 8 | Convert community-lists to `standard` (F6) | low if tested | yes |
| 9 | Remove dead config (P4) | low, but large diff | yes |
| 10 | OSPF MD5 migration (F7) | per-VRF project | multiple |

> [!caution] Make every change reversible
> ```
> copy running-config bootflash:pre-change-YYYYMMDD.cfg
> configure terminal
>  ...changes...
> ! if anything goes wrong:
> configure replace bootflash:pre-change-YYYYMMDD.cfg
> ```
> Or set a safety net before you start: `reload in 15`, then `reload cancel` once you are happy.

---

## Next

→ [[09 - Verification Playbook]] for the exact commands to confirm each finding.
