---
title: Worked examples
tags:
  - network/cisco
  - examples
  - study
up: "[[00 - MOC - VM90-IP-CORE1 Routing]]"
---

# Worked examples

Five traces through the config. Follow each one with the `show run` open beside you.

---

## Example 1 - A WAN route reaches a campus PC

**Question:** a campus PC needs to reach `10.122.35.7`, a remote site behind the Fastweb MPLS cloud. How does the route get there?

**Route:** `10.122.32.0/19`

### Control plane, step by step

**① The route exists in global as a tracked static**

```cisco
ip route 10.122.32.0 255.255.224.0 10.142.96.85 track 4
!
track 4 ip sla 4 reachability
ip sla 4
 icmp-echo 10.142.96.85 source-ip 10.142.96.82
 frequency 30
```

The `track 4` keyword means the static is only installed while the IP SLA ping to `10.142.96.85` succeeds. If the WAN dies, the static disappears and so does every downstream copy of it. Elegant - but see the warning about SLA 4 in [[08 - Findings and Cleanup]].

**② Global BGP picks it up**

```cisco
router bgp 65001
 address-family ipv4
  redistribute static
```

Now `10.122.32.0/19` is in the global BGP table. No community attached.

**③ CAMPUS imports it**

```cisco
vrf definition IT-VRF-CAMPUS
 address-family ipv4
  import ipv4 unicast map IMPORT-CAMPUS-FROM-GLOBAL
```

The route-map runs:
- seq 5 `deny` - does it carry `65001:62/64/66/68/69`? No, it carries nothing. **Not matched.**
- seq 200 `permit` - no match clause, so yes. Accepted, and `set community 58983300` (`900:900`) is applied.

The route is now in the CAMPUS BGP table, marked "came from Global".

**④ CAMPUS OSPF picks it up and tags it**

```cisco
router ospf 4 vrf IT-VRF-CAMPUS
 capability vrf-lite
 redistribute bgp 65001 route-map SET-TAG-TO-GLOBAL-COMMUNITY
```

```cisco
route-map SET-TAG-TO-GLOBAL-COMMUNITY permit 10
 match community GLOBAL-COMMUNITY      ! = 58983300
 set tag 800
```

It matches. The route becomes an **OSPF external type-2 LSA with tag 800** inside OSPF process 4.

**⑤ The aggregation switches learn it**

`VM90-IP-AGGR1` and `AGGR2` are OSPF neighbours on `Po10.3634` and `Po10.3636`. They now have `10.122.32.0/19` as O E2. The PC's default gateway on the access switch follows.

**⑥ The loop is closed off**

```cisco
address-family ipv4 vrf IT-VRF-CAMPUS
 redistribute ospf 4 match internal external 1 external 2 route-map NO-RED-TAG-TO-GLOBAL
```
`NO-RED-TAG-TO-GLOBAL deny 5 / match tag 800 80` → the route is **not** put back into BGP. Done.

### Data plane

PC → access switch → `VM90-IP-AGGR1` → `Po10.3634` → VM90-IP-CORE1 in the CAMPUS VRF → the route says next-hop `10.142.96.85`, which lives in **global** → the packet leaves via the WAN path in the global table.

> [!question] How does a VRF route recurse to a global next-hop?
> `10.142.96.85` is not inside `IT-VRF-CAMPUS`. It resolves because the global connected/transit prefixes are themselves imported into CAMPUS by the same `IMPORT-CAMPUS-FROM-GLOBAL` map (global `redistribute connected` puts them in global BGP first). Confirm on the box with `show ip route vrf IT-VRF-CAMPUS 10.142.96.85` - if that lookup fails, the static's recursion fails too.

---

## Example 2 - Campus PC → DC server (through the firewall)

**Question:** `10.128.2.50` (campus) wants `10.140.4.20` (a DC server). Why does the traffic pass the firewall and not shortcut inside the router?

### Why there is no shortcut

- `IT-VRF-CAMPUS` imports only `65001:20`. `IT-VRF-DC` exports `65001:23`. No match → no leak.
- Could it leak via global? DC exports `10.140.4.0/23` to global with community `65001:69` (it is in `DC-SUBNETS` seq 10). CAMPUS's import map has `deny 5 match community FROM-GLOBAL-TO-CAMPUS`, and that list contains `4259905605` = `65001:69`. **Blocked.**

So the only path is the hairpin.

### How campus learns the route

**① The firewall advertises DC subnets into the CAMPUS backbone**

The FTD has an OSPF adjacency with `IT-VRF-CAMPUS-BACKBONE` on `Po11.3243` (`10.142.2.37/30`, OSPF 64). Where did the firewall learn the DC subnets? From `IT-VRF-DC` on `Po11.3291` and/or from `IT-VRF-DC-BACKBONE` on `Po11.3293`.

**② Backbone-to-backbone leak**

```cisco
address-family ipv4 vrf IT-VRF-DC-BACKBONE
 redistribute ospf 69 match internal external 1 external 2 route-map NO-RED-TAG-TO-LEAK
```
→ into BGP with export RT `65001:69`.

```cisco
vrf definition IT-VRF-CAMPUS-BACKBONE
 address-family ipv4
  route-target import 65001:69          ! ✅ CAMPUS-BB accepts DC-BB
```
→ the route lands in CAMPUS-BB's BGP table.

**③ CAMPUS-BB advertises it to the firewall**

```cisco
router ospf 64 vrf IT-VRF-CAMPUS-BACKBONE
 redistribute bgp 65001 route-map TAG-LEAKED-SUBNETS-CAMPUS   ! set tag 80
 passive-interface default
 no passive-interface Port-channel11.3243
```

The firewall now knows: *"to reach `10.140.4.0/23`, use the campus-backbone interface."*

### Data plane

```
PC 10.128.2.50
  → AGGR switch
  → CORE1, VRF IT-VRF-CAMPUS
  → default route / specific route points at the FTD
  → Po11.3241 (VLAN 3241)  ────► FTD4125
                                   │  policy inspection here
  ◄──── Po11.3293 (VLAN 3293) ─────┘
  → CORE1, VRF IT-VRF-DC-BACKBONE
  → ... to IT-VRF-DC → Po10 → server 10.140.4.20
```

Return traffic takes the mirror path. The firewall sees both directions, which is what makes stateful inspection work.

> [!note] The relevant default routes
> ```cisco
> ip route vrf IT-VRF-CAMPUS 0.0.0.0 0.0.0.0 10.142.128.102 200
> ip route vrf IT-VRF-DC     0.0.0.0 0.0.0.0 10.142.25.18
> ```
> plus `default-information originate` in OSPF 4/8/9/2/6 so the aggregation layer also gets a default. The `200` on the CAMPUS one is an administrative distance, making it a **floating** static - it only installs if nothing better exists.

---

## Example 3 - Guest wifi can reach exactly six servers

This is the tightest policy on the box and the clearest example of the design working.

**① The guest service VRF has no BGP at all**

`IT-VRF-WIFIGUEST` has interfaces (`Po10.3639/3641/3642/3645`, `Po11.3251`), an OSPF process 5, route-targets `65001:21`... and **no `address-family ipv4 vrf IT-VRF-WIFIGUEST` in BGP**. Nothing is ever exported, nothing is ever imported. Its route-targets are decorative.

**② The guest backbone VRF imports DC and nothing else**

```cisco
vrf definition IT-VRF-WIFIGUEST-BACKBONE
 rd 65001:65
 route-target export 65001:65
 route-target import 65001:65
 address-family ipv4
  route-target import 65001:69       ! DC-BACKBONE. That is the entire list.
```

**③ And even DC's routes are then filtered down to six hosts**

```cisco
router ospf 65 vrf IT-VRF-WIFIGUEST-BACKBONE
 redistribute bgp 65001 route-map TAG-LEAKED-SUBNETS-WIFI-GUEST
!
route-map TAG-LEAKED-SUBNETS-WIFI-GUEST permit 10
 match ip address prefix-list LEAKED-VRF-WIFI-GUEST
 set tag 80
```

`LEAKED-VRF-WIFI-GUEST` permits only `10.140.2.8`, `.31`, `.32`, `.37`, `10.140.10.102`, `10.140.10.103` - all /32. Everything else hits the implicit deny.

**Result:** on the guest side of the firewall, the only non-default routes in existence are six host routes - almost certainly DNS, DHCP, the captive portal and the wireless controllers. A guest laptop has no route to any campus, VDI, management or access-control subnet, at the routing layer, before any firewall rule is even consulted.

> [!tip] Defence in depth done properly
> Three independent mechanisms all have to fail before a guest can reach the campus: (1) no BGP AF on the service VRF, (2) no route-target for CAMPUS-BB, (3) a six-entry prefix-list. Plus the firewall policy itself.

---

## Example 4 - "Can CAMPUS reach TCI?" ⭐

**Short answer: no, and it cannot be made to work by adding route-targets alone.**

### Why not

```cisco
vrf definition IT-VRF-TCI
 rd 65001:25
 route-target export 65001:25
 route-target import 65001:25
 address-family ipv4
 exit-address-family
!
router ospf 7 vrf IT-VRF-TCI
 area 0.0.0.0 authentication
 area 0.0.0.101 authentication
 area 0.0.0.101 nssa no-redistribution no-summary
 area 0.0.0.101 nssa translate type7 always suppress-fa
 bfd all-interfaces
```

Three separate blockers:

1. **No BGP address-family.** Search the config: there is no `address-family ipv4 vrf IT-VRF-TCI`. TCI's routes never enter BGP, so `route-target export 65001:25` never gets applied to anything. The export RT is configured and completely inert.
2. **No `capability vrf-lite`** and no `redistribute bgp` in OSPF 7 - so even if routes arrived in BGP, they would not be pushed into TCI's OSPF.
3. **No firewall interface.** TCI has no `Port-channel11` subinterface and no `-BACKBONE` twin. The sanctioned inter-zone path does not physically exist for it.

TCI's interfaces are `Po10.3606` (area `0.0.0.101`, to `VM39-CORE-SW`), `Po10.3659`, `Po10.3661`, `Po10.3662` (area 0). It is a self-contained OSPF domain. Same story for `IT-VRF-APPALTI` and `IT-MON-VRF`.

### Option A - the sanctioned way (via the firewall)

Mirror what every other zone does. This is more work but keeps the security model intact.

```cisco
! 1. Create the backbone twin
vrf definition IT-VRF-TCI-BACKBONE
 rd 65001:67
 route-target export 65001:67
 route-target import 65001:67
 address-family ipv4
  route-target import 65001:64          ! accept CAMPUS-BACKBONE
 exit-address-family
!
! 2. Let CAMPUS-BACKBONE accept TCI in return - MUST be symmetric
vrf definition IT-VRF-CAMPUS-BACKBONE
 address-family ipv4
  route-target import 65001:67
 exit-address-family
!
! 3. Two firewall subinterfaces (VLANs/IPs to be allocated properly)
interface Port-channel11.32xx
 description OSPF-TCI-FTD4125-BACK
 encapsulation dot1Q 32xx
 vrf forwarding IT-VRF-TCI
 ip address 10.142.2.xxx 255.255.255.252
 no ip redirects
 no ip proxy-arp
 ip ospf authentication-key 7 <key>
 ip ospf network point-to-point
 ip ospf bfd
 ip ospf 7 area 0.0.0.0
!
interface Port-channel11.32yy
 encapsulation dot1Q 32yy
 vrf forwarding IT-VRF-TCI-BACKBONE
 ip address 10.142.2.yyy 255.255.255.252
 ip ospf network point-to-point
 ip ospf bfd
 ip ospf 67 area 0.0.0.0
!
! 4. The backbone OSPF process
router ospf 67 vrf IT-VRF-TCI-BACKBONE
 capability vrf-lite
 area 0.0.0.0 authentication
 redistribute bgp 65001 route-map TAG-LEAKED-SUBNETS-TCI
 passive-interface default
 no passive-interface Port-channel11.32yy
 bfd all-interfaces
!
! 5. The BGP address-family
router bgp 65001
 address-family ipv4 vrf IT-VRF-TCI-BACKBONE
  redistribute ospf 67 match internal external 1 external 2 route-map NO-RED-TAG-TO-LEAK
 exit-address-family
!
! 6. The tagging route-map + its prefix-list
ip prefix-list LEAKED-VRF-TCI seq 10 permit 10.x.x.0/24     ! be specific, not 0.0.0.0/0 le 32
!
route-map TAG-LEAKED-SUBNETS-TCI permit 10
 match ip address prefix-list LEAKED-VRF-TCI
 set tag 80
```

Plus VLANs on `VM90-DC-L2-AGGR1/2`, interfaces and a policy on the FTD.

> [!warning] Do not forget `capability vrf-lite`
> Adding `redistribute bgp` to an OSPF VRF process **without** `capability vrf-lite` sets the DN bit on the generated LSAs. Downstream VRF-aware routers silently ignore them and you get a blackhole that looks like "OSPF is up but no routes". See [[01 - Primer - VRF RD RT and BGP#12 capability vrf-lite - the one command you must not remove]].

### Option B - the quick way (direct RT leak, no firewall)

Only if the security model explicitly allows this flow to be uninspected.

```cisco
! TCI needs a BGP address-family first - without it nothing happens
router bgp 65001
 address-family ipv4 vrf IT-VRF-TCI
  redistribute connected
  redistribute ospf 7 match internal external 1 external 2 route-map NO-RED-TAG-TO-GLOBAL
 exit-address-family
!
router ospf 7 vrf IT-VRF-TCI
 capability vrf-lite
 redistribute bgp 65001 route-map SET-TAG-TO-GLOBAL-COMMUNITY   ! see caveat below
!
! Then the symmetric route-target pair
vrf definition IT-VRF-CAMPUS
 address-family ipv4
  route-target import 65001:25
!
vrf definition IT-VRF-TCI
 address-family ipv4
  route-target import 65001:20
```

> [!danger] Caveat on Option B
> `SET-TAG-TO-GLOBAL-COMMUNITY` only matches routes carrying community `900:900`. Routes arriving in TCI via route-target `65001:20` do **not** carry it, so they would be silently dropped at the OSPF redistribution step. You would need a purpose-built route-map, e.g.:
> ```cisco
> route-map TAG-LEAKED-SUBNETS-TCI-DIRECT permit 10
>  match ip address prefix-list CAMPUS-SUBNETS
>  set tag 80
> ```
> This is exactly the kind of subtlety that makes Option A - copying an existing, proven pattern - the safer choice. It also breaks the "all inter-zone traffic is inspected" property, which is probably why nobody has done it.

---

## Example 5 - The TEST-A / TEST-B lab pair (study this one first)

`VRF-TEST-A` and `VRF-TEST-B` are a miniature, complete copy of the whole design. Two zones, two backbones, nothing else attached. Perfect for learning.

| Piece | TEST-A | TEST-B |
|---|---|---|
| Service VRF | `VRF-TEST-A` (`65001:91`) | `VRF-TEST-B` (`65001:92`) |
| Backbone VRF | `VRF-TEST-A-BACKBONE` (`65001:93`) | `VRF-TEST-B-BACKBONE` (`65001:94`) |
| OSPF service | 91 | 92 |
| OSPF backbone | 93 | 94 |
| Link to aggregation | `Po10.3901` | `Po10.3902` |
| Link to firewall (service) | `Po11.3900` | `Po11.3903` |
| Link to firewall (backbone) | `Po11.3950` | `Po11.3953` |
| Export to global | `TEST-A-TO-GLOBAL-BGP` → `65001:93` | `TEST-B-TO-GLOBAL-BGP` → `65001:94` |
| Import from global | `TEST-A-IMPORT-GLOBAL` (blocks `:93`, `:94`) | `TEST-B-IMPORT-GLOBAL` (blocks `:94`, `:93`) |
| Backbone RT import | `65001:94` | `65001:93` |
| Tag guard (service) | `NO-RED-TAG-80` | `NO-RED-TAG-80` |
| Tag guard (backbone) | `NO-RED-TAG-800` | `NO-RED-TAG-800` |

Every mechanism in this vault appears exactly once here:

- **VRF ↔ VRF** through the firewall: `:93` ↔ `:94` mutual import between the backbones.
- **VRF ↔ Global**: export with a unique community, import with a deny-list of the other VRFs' communities.
- **Loop prevention**: `TAG-LEAKED-SUBNETS-A-B` sets tag 80, `NO-RED-TAG-80` / `NO-RED-TAG-800` block the return.
- **Isolation**: TEST-A and TEST-B service VRFs import only their own RT, so no shortcut.

There are also lab leftovers to ignore: `ip route vrf VRF-TEST-A 1.1.1.1/32 10.142.28.18`, `ip route vrf VRF-TEST-A-BACKBONE 100.100.100.100/32 Null0`, `ip route vrf IT-VRF-ACCESS-CONTROL-BACKBONE 2.2.2.2/32 Null0`, `ip route 2.3.4.5/32 Null0`, `route-map test_lorenzo`, `route-map red-ospf-tag`, `route-map RF-TEST-A-BGP`. None of them are referenced by anything live.

> [!tip] Practice exercise
> Using only the config, work out what would happen if you added `route-target import 65001:92` to `VRF-TEST-A`. Answer: TEST-A's BGP table would receive TEST-B's routes directly, but they would **not** appear in TEST-A's routing table as far as OSPF 91 is concerned, because `SET-TAG-TO-GLOBAL-COMMUNITY` only redistributes routes carrying `900:900`. They *would* still be installed in the VRF RIB from BGP itself. Verify with `show ip route vrf VRF-TEST-A` vs `show bgp vpnv4 unicast vrf VRF-TEST-A`.

---

## Next

→ [[07 - Command Reference]] for line-by-line syntax, or [[08 - Findings and Cleanup]] for the problems.
