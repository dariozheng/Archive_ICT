---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
title: Command reference - every line decoded
tags:
  - network/cisco
  - reference
  - ios-xe
  - category/networking/networking_general
up: "[[00 - MOC - VM90-IP-CORE1 Routing]]"
icon: FasNetworkWired
iconColor:
last_update: 2026-09-21
---

# Command reference

Every command that participates in the VRF/BGP/OSPF routing design, what it does, and where it appears in this config. Use as a dictionary.

---

## VRF definition

```cisco
vrf definition IT-VRF-CAMPUS
 rd 65001:20
 route-target export 65001:20
 route-target import 65001:20
 !
 address-family ipv4
  import ipv4 unicast map IMPORT-CAMPUS-FROM-GLOBAL
  export ipv4 unicast map EXPORT-CAMPUS-TO-GLOBAL
 exit-address-family
```

| Command | Meaning |
|---|---|
| `vrf definition NAME` | Create a VRF. The modern, multi-address-family form. (The old `ip vrf NAME` form is not used here.) |
| `rd ASN:nn` | Route distinguisher. Makes prefixes unique inside BGP. **Does not control leaking.** Without it a VRF cannot have a BGP address-family. Changing it on a live VRF tears down all BGP state for that VRF. |
| `route-target export X` | Stamp X on every route this VRF puts into the shared BGP table |
| `route-target import X` | Accept routes stamped X from the shared BGP table |
| `route-target both X` | Shorthand for export + import (not used here, written out longhand) |
| `address-family ipv4` | Per-address-family settings. Route-targets can be configured here **or** at the VRF level; read both together |
| `import ipv4 unicast map RM` | Copy routes from the **global** IPv4 table into this VRF, filtered by route-map RM. Default prefix limit 1000 |
| `export ipv4 unicast map RM` | Copy routes from this VRF into the **global** table, filtered by route-map RM |

Also seen: `import map RM` (without `ipv4 unicast`) in `vrf definition TEMP` - that is the older **VPN import** filter, applied to route-target imports, not to global leaking. Different feature, similar-looking command. Worth knowing so you do not confuse the two.

---

## Interface commands

```cisco
interface Port-channel11.3241
 description OSPF-CAMPUS-FTD4125-BACK:L3_Peering:Po4.3241
 encapsulation dot1Q 3241
 vrf forwarding IT-VRF-CAMPUS
 ip address 10.142.2.33 255.255.255.252
 no ip redirects
 no ip proxy-arp
 ip ospf authentication-key 7 <hidden>
 ip ospf network point-to-point
 ip ospf bfd
 ip ospf 4 area 0.0.0.0
 ip ospf cost 120
```

| Command | Meaning |
|---|---|
| `encapsulation dot1Q N` | This subinterface handles VLAN tag N on the trunk |
| `vrf forwarding NAME` | Put the interface in that VRF. ⚠️ **This wipes the IP address** - always re-apply `ip address` after |
| `no ip redirects` | Do not send ICMP redirects. Standard hardening on L3 point-to-point links |
| `no ip proxy-arp` | Do not answer ARP on behalf of other hosts. Standard hardening |
| `ip ospf N area A` | Interface-level way to join OSPF process N in area A. **This config uses this style**, not `network` statements under the router - which is clearer and less error-prone |
| `ip ospf network point-to-point` | Skip DR/BDR election. Correct on a /30. Speeds up convergence and avoids a pointless election |
| `ip ospf bfd` | Enable Bidirectional Forwarding Detection on this interface - sub-second failure detection instead of waiting for OSPF dead timers |
| `ip ospf cost 120` | Raise the cost to make this link the backup. Used on every `AGGR2` link so `AGGR1` is primary |
| `ip ospf authentication-key 7 X` | Simple (type 1) OSPF password. Type 7 is **obfuscation, not encryption** - trivially reversible |
| `ip flow monitor X input/output` | NetFlow/IPFIX export, on `Po10.3500` only |
| `standby N ip / priority / preempt / track` | HSRP - this router is one of a pair, active for VLANs 3302 and 3500 |

### The naming convention in descriptions

`OSPF-CAMPUS-FTD4125-BACK:L3_Peering:Po4.3241` reads as:

`<protocol>-<VRF/zone>-<remote device>:<link type>:<remote interface>`

It is consistent across the whole config and is genuinely useful - `show interface description` (alias `sid`) gives you the topology at a glance.

---

## OSPF per VRF

```cisco
router ospf 64 vrf IT-VRF-CAMPUS-BACKBONE
 capability vrf-lite
 area 0.0.0.0 authentication
 redistribute bgp 65001 route-map TAG-LEAKED-SUBNETS-CAMPUS
 passive-interface default
 no passive-interface Port-channel11.3243
 default-information originate
 bfd all-interfaces
```

| Command | Meaning |
|---|---|
| `router ospf N vrf X` | An OSPF process that runs entirely inside VRF X. Each VRF needs its own process number |
| `capability vrf-lite` | Disable the DN-bit / domain-tag PE check. **Required** whenever the process does `redistribute bgp`. See [[01 - Primer - VRF RD RT and BGP]] |
| `area A authentication` | Enable **simple password** authentication in area A. (`area A authentication message-digest` would be MD5 - stronger, not used here) |
| `redistribute bgp 65001 route-map RM` | Pull routes out of this VRF's BGP table into OSPF, filtered/tagged by RM |
| `redistribute static` | Pull VRF static routes into OSPF (used in ospf 4 and ospf 93) |
| `match internal external 1 external 2` | On the BGP side: which OSPF route types to take. Internal = O/IA, external 1/2 = E1/E2. Omitting this defaults to internal only, which would silently drop all the E2 leaked routes |
| `passive-interface default` | Do not form adjacencies on any interface |
| `no passive-interface X` | ...except X. Used in all backbone VRFs so they can only ever peer with the firewall |
| `default-information originate` | Advertise a default route into OSPF. Used in service VRFs to give the aggregation layer a way out |
| `bfd all-interfaces` | Turn on BFD for every interface in the process |
| `network A.B.C.D wildcard area A` | Classic way to add interfaces. Only two survive here (ospf 2 and ospf 4); the ospf 2 one matches no interface |

### The NSSA block in OSPF 7 (TCI)

```cisco
router ospf 7 vrf IT-VRF-TCI
 area 0.0.0.101 nssa no-redistribution no-summary
 area 0.0.0.101 nssa translate type7 always suppress-fa
```

| Keyword | Meaning |
|---|---|
| `nssa` | Not-So-Stubby Area - blocks type-5 externals but allows type-7 locally |
| `no-redistribution` | This ABR does not inject its own redistributed routes into the NSSA |
| `no-summary` | Also block type-3 summaries - a "totally NSSA". The area only gets a default route |
| `translate type7 always` | Always convert type-7 LSAs to type-5 at the ABR, even when not elected translator |
| `suppress-fa` | Suppress the forwarding address in the translated LSA - forces traffic through this ABR. Common workaround for non-Cisco or asymmetric NSSA peers |

This is a self-contained piece of the config, unrelated to the VRF leaking design.

---

## BGP

```cisco
router bgp 65001
 bgp router-id 10.100.100.100
 bgp log-neighbor-changes
 bgp graceful-restart
 !
 address-family ipv4
  redistribute connected
  redistribute static
  redistribute ospf 1 match internal external 1 external 2
 exit-address-family
 !
 address-family ipv4 vrf IT-VRF-CAMPUS
  redistribute connected
  redistribute static
  redistribute ospf 4 match internal external 1 external 2 route-map NO-RED-TAG-TO-GLOBAL
  default-information originate
 exit-address-family
```

| Command | Meaning |
|---|---|
| `router bgp 65001` | BGP in private AS 65001. **No neighbours anywhere** - purely a local leaking engine |
| `bgp router-id 10.100.100.100` | Pinned to `Loopback100`. Good practice - stops the ID changing when an interface flaps |
| `bgp log-neighbor-changes` | Log adjacency changes (nothing to log here, but harmless) |
| `bgp graceful-restart` | Preserve forwarding during a control-plane restart |
| `address-family ipv4` | The **global** table's BGP view |
| `address-family ipv4 vrf X` | VRF X's BGP view |
| `redistribute connected` | Put the VRF's directly-connected subnets into BGP so they can be exported |
| `redistribute static` | Same for static routes |
| `redistribute ospf N ... route-map RM` | Same for OSPF, with the tag guard applied |
| `default-information originate` | Advertise a default into this BGP address-family (CAMPUS, MGMNT, VDI only) |

> [!note] Service VRFs vs backbone VRFs
> Service VRF blocks have `redistribute connected` + `static` + `ospf`. Backbone VRF blocks have **only** `redistribute ospf`. That difference is intentional - backbone VRFs own nothing, they only relay what the firewall tells them.

---

## Route-maps

```cisco
route-map NAME permit|deny SEQ
 match <condition>
 set <attribute>
```

| Rule | Detail |
|---|---|
| Evaluation order | Ascending sequence number, first match wins, then stop |
| `permit` + match | Route passes, `set` clauses applied |
| `deny` + match | Route is dropped |
| No `match` clause | Matches **everything** |
| End of route-map | **Invisible `deny` that matches everything** - the single biggest source of surprises |
| Multiple `match` of different types | Logical **AND** |
| Multiple values on one `match` line | Logical **OR** (`match tag 800 80` = tag is 800 *or* 80) |

Match/set types used here:

| Clause | Meaning |
|---|---|
| `match ip address prefix-list X` | Prefix is in list X |
| `match community X` | Route carries a community in community-list X |
| `match extcommunity X` | Route carries an extended community (route-target) in list X - only in the unused `test_lorenzo` |
| `match tag N [N2 ...]` | Route carries one of these tags |
| `set community N` | **Replace** communities with N (add `additive` to append instead) |
| `set tag N` | Write tag N onto the route |
| `set ip next-hop A.B.C.D` | Override next-hop - only in the unused `RF-TEST-A-BGP` |
| `description TEXT` | Free text. Only `SET-TAG-TO-GLOBAL-COMMUNITY` has one. Worth adding to the rest |

---

## Community lists

```cisco
ip community-list standard NAME permit 65001:64
ip community-list expanded NAME permit 4259905600
```

| Form | Behaviour |
|---|---|
| `standard` | Exact numeric match on the community value. Fast, unambiguous. **Not used in this config** |
| `expanded` | The value is a **regular expression** matched against the *text* of the route's community string. Slower, and unanchored - it can match a substring of a different community |

Multiple `permit` lines in one list = logical OR.

> [!warning] Fragility
> Every community-list here is `expanded` with a decimal value. Two consequences:
> 1. The regex is unanchored. Today no value is a substring of another, so it works, but adding a community could silently create a false match. `standard` lists would be safer.
> 2. The values only match while the router displays communities as decimals. If someone enables `ip bgp-community new-format`, communities render as `65001:64` and every expanded list containing `4259905600` **stops matching**, which would break the segmentation deny-lists. Verify with `show ip community-list` and a live route.

---

## Prefix lists

```cisco
ip prefix-list NAME seq N permit A.B.C.D/len [ge X] [le Y]
```

| Written | Matches |
|---|---|
| `permit 10.128.1.0/24` | exactly that prefix |
| `permit 172.28.0.0/16 le 32` | that prefix and everything more specific inside it |
| `permit 0.0.0.0/0 le 32` | **everything** (a permit-all placeholder) |
| `permit 0.0.0.0/0 ge 16` | any prefix /16 or longer |
| `permit 0.0.0.0/0` | **only** the default route |

Implicit `deny` at the end, same as route-maps.

Prefix-lists in this config and their job:

| Prefix-list | Used by | Effect |
|---|---|---|
| `CAMPUS-SUBNETS` | `EXPORT-CAMPUS-TO-GLOBAL`, `LEAK-GLOBAL-TO-IT-VRF-CAMPUS` | 11 real campus subnets |
| `DC-SUBNETS` | `EXPORT-DC-TO-GLOBAL` | ~60 DC subnets |
| `MGMT-SUBNETS` | `EXPORT-MGMNT-TO-GLOBAL`, `LEAK-GLOBAL-TO-IT-VRF-MGMNT` | 3 subnets |
| `VDI-SUBNETS` | `VRF_GLOBAL_TO_VDI` (dead VRF) | `10.140.128.0/20` |
| `LEAKED-VRF-*` | `TAG-LEAKED-SUBNETS-*` | permit-all, except WIFI-GUEST |
| `LEAKED-VRF-WIFI-GUEST` | `TAG-LEAKED-SUBNETS-WIFI-GUEST` | 6 host routes - a real filter |
| `ALL-NETWORKS` | `VRFGLOBAL-REDISTRIBUTE-STATIC-TO-OSPF` | permit-all |
| `IT-VRF-*-SUBNETS` | the unused `RMP-*-BGP` route-maps | permit-all, dead |
| `VRF-TEST-A/B-SUBNETS`, `TEST-B`, `BGP`, `GLOBAL`, `IMPORT-CAMPUS`, `WIFI_GUEST` | mostly unused | see [[08 - Findings and Cleanup]] |

---

## Static routes and tracking

```cisco
ip route 10.122.32.0 255.255.224.0 10.142.96.85 track 4
ip route vrf IT-VRF-DC 0.0.0.0 0.0.0.0 10.142.25.18
ip route vrf IT-VRF-CAMPUS 0.0.0.0 0.0.0.0 10.142.128.102 200
```

| Element | Meaning |
|---|---|
| `ip route A.B.C.D mask next-hop` | Static route in the **global** table |
| `ip route vrf X ...` | Static route inside VRF X |
| trailing number (`200`) | Administrative distance. 200 > OSPF's 110, so it is a **floating** static - a last resort |
| `track N` | Only install the route while tracked object N is up |

```cisco
track 4 ip sla 4 reachability
!
ip sla 4
 icmp-echo 10.142.96.85 source-ip 10.142.96.82
  threshold 1500
  timeout 2000
  frequency 30
ip sla schedule 4 life forever start-time now
```

| Element | Meaning |
|---|---|
| `ip sla N` / `icmp-echo dst source-ip src` | Ping `dst` from `src` every `frequency` seconds |
| `timeout 2000` | Declare a probe failed after 2000 ms |
| `threshold 1500` | Threshold for "over threshold" reaction, not used for reachability here |
| `track N ip sla N reachability` | Tracked object that is **up** while the SLA succeeds |
| `ip sla schedule N life forever start-time now` | Run it permanently. **Without this line the SLA never starts** |

> [!danger] Check SLA 4
> `source-ip 10.142.96.82` does not correspond to any interface address in this config. An IP SLA source address must be a local address. If it is not local, the probe never succeeds, `track 4` stays down, and roughly 32 static routes are never installed - which would also remove them from every VRF that imports from global. Verify with `show ip sla statistics 4` and `show track 4`. See [[08 - Findings and Cleanup]].
>
> By contrast `ip sla 5` sources from `10.142.100.21` (= `Po10.3500`, valid) and `ip sla 6` from `10.142.25.138` (= `Po10.3699`, valid). `ip sla 6` has no tracked object referencing it - it runs and is used by nothing.

---

## Extended community lists

```cisco
ip extcommunity-list expanded EXT-CML-LORENZO permit rt 65001:94
```

Matches route-targets rather than standard communities. Referenced only by `route-map test_lorenzo`, which is itself referenced by nothing. Dead.

---

## Useful aliases already configured on the box

```cisco
alias exec s    show ip int brie
alias exec sps  show etherchannel summary
alias exec sis  show interface status
alias exec scn  show cdp neighbors
alias exec sid  show interface description
alias exec siv  show ip route vrf
alias exec sion show ip ospf neig
alias exec sri  show run int
alias exec sr   show runn
```

`siv IT-VRF-CAMPUS` and `sion` will save you a lot of typing.

---

## Next

→ [[08 - Findings and Cleanup]] for what is wrong, or [[09 - Verification Playbook]] for what to type.
