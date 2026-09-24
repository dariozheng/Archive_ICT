---
title: Primer - VRF, RD, RT, BGP, route-maps and tags
tags:
  - network/cisco
  - primer
  - vrf
  - bgp
up: "[[00 - MOC - VM90-IP-CORE1 Routing]]"
---

# Primer - everything you need before reading the rest

This note assumes you know what an IP address and a routing table are, and nothing else.

---

## 1. A routing table

A router keeps a list: *"to reach network X, send the packet to next-hop Y via interface Z"*. That list is the **routing table** (or RIB). A normal router has exactly one.

```
VM90-IP-CORE1# show ip route
```

---

## 2. A VRF is a second routing table

**VRF** = Virtual Routing and Forwarding. It is a completely separate routing table living inside the same physical router.

> [!tip] Analogy
> One office building (the router), but each department gets its own locked filing cabinet (the VRF). A letter filed in the HR cabinet cannot be found by someone searching the Finance cabinet - even though both cabinets are in the same room.

Two consequences that surprise beginners:

1. **The same IP subnet can exist twice**, once in each VRF, with no conflict.
2. **By default, VRFs cannot reach each other at all.** Not "it is discouraged" - there is simply no lookup path. Leaking routes between them is an explicit, deliberate act.

On this box:

```cisco
vrf definition IT-VRF-CAMPUS          ! create the cabinet
 rd 65001:20                          ! see section 4
 ...
interface Port-channel10.3634
 vrf forwarding IT-VRF-CAMPUS         ! put this interface in that cabinet
 ip address 10.142.24.110 255.255.255.252
```

To look inside one cabinet instead of the default one, every command grows a `vrf` keyword:

```cisco
show ip route vrf IT-VRF-CAMPUS
ping vrf IT-VRF-CAMPUS 10.128.1.1
```

### The "global" table

The original, unnamed routing table still exists. It is called the **global table** (or "global VRF", though it is not really a VRF). Interfaces with no `vrf forwarding` line live there - for example `Port-channel10.3674` and `Port-channel10.3701` on this router. Most of the WAN and static routes live in global.

---

## 3. Why so many VRFs here

Each VRF is a **security zone**:

| VRF | Zone |
|---|---|
| `IT-VRF-CAMPUS` | office user network |
| `IT-VRF-DC` | data centre servers |
| `IT-VRF-VDI` | virtual desktops |
| `IT-VRF-MGMNT` | device management |
| `IT-VRF-ACCESS-CONTROL` | badge readers / physical access |
| `IT-VRF-WIFIGUEST` | guest wifi |
| `IT-VRF-TCI`, `IT-VRF-APPALTI`, `IT-MON-VRF` | other isolated services |

The VRF is the *enforcement* of the zone model. If a route never gets copied into the CAMPUS table, a campus PC physically cannot route to it, regardless of ACLs.

---

## 4. Route Distinguisher (RD) - just a serial number

```cisco
vrf definition IT-VRF-CAMPUS
 rd 65001:20
```

The RD is an 8-byte value prepended to a prefix so that `10.1.1.0/24` in CAMPUS and `10.1.1.0/24` in DC are two distinguishable objects inside BGP's shared table. Format here is `ASN:number` - AS 65001 is Publiacqua's private AS number.

> [!warning] The RD does **not** control leaking
> This is the #1 beginner mistake. The RD only makes prefixes unique. It decides nothing about who sees what. If a VRF has **no** `rd` line, it simply cannot participate in BGP at all - which is why `IT-VRF-APPALTI` (no RD) is an OSPF-only island. See [[02 - VRF Inventory]].

---

## 5. Route Target (RT) - the coloured sticker

The RT is what actually controls leaking.

```cisco
vrf definition IT-VRF-DC-BACKBONE
 rd 65001:69
 route-target export 65001:69     ! sticker I put ON my routes
 route-target import 65001:69     ! sticker I am willing to PICK UP
 address-family ipv4
  route-target import 65001:64    ! ...and this one
  route-target import 65001:62    ! ...and this one
```

> [!tip] Analogy
> There is one big shared parcel bin in the middle of the room (BGP's VPNv4 table). When a VRF puts a route in the bin, it sticks a coloured label on it (**export RT**). Every VRF also has a list of labels it is allowed to take out of the bin (**import RT**). No label match, no copy.

Two rules worth memorising:

- **Import is not transitive.** If A exports to B, and B exports to C, C does *not* automatically get A's routes. Importing a route does not re-stamp it with your own export RT.
- **`route-target both X` is shorthand** for `export X` + `import X`. Importing your own export RT is normal and is how a VRF keeps its own routes visible in BGP.

> [!note] Why some route-targets appear twice in this config
> In the `show run` you will see route-targets both directly under `vrf definition` and again under `address-family ipv4`. Read them **together** - the effective import list for the IPv4 address family is the union of both places. Example, `IT-VRF-CAMPUS-BACKBONE` imports `65001:64, 66, 68, 62, 69`.

---

## 6. BGP with no neighbours

```cisco
router bgp 65001
 bgp router-id 10.100.100.100
 bgp log-neighbor-changes
 bgp graceful-restart
 !
 address-family ipv4               ! <-- the GLOBAL table's BGP view
  redistribute connected
  redistribute static
  redistribute ospf 1 match internal external 1 external 2
 exit-address-family
 !
 address-family ipv4 vrf IT-VRF-CAMPUS   ! <-- one BGP view per VRF
  redistribute connected
  redistribute static
  redistribute ospf 4 match internal external 1 external 2 route-map NO-RED-TAG-TO-GLOBAL
 exit-address-family
```

Scroll the whole config: there is **not a single `neighbor` statement**. BGP here is not a routing protocol between routers. It is:

> a local table with import/export rules attached, that all the VRFs can drop routes into and pick routes out of.

That is entirely legal and quite common in enterprise designs. It is sometimes called "BGP as a route-leaking engine" or "VRF-lite with BGP leaking".

**What each `address-family` block means:**

| Block | Meaning |
|---|---|
| `address-family ipv4` | the BGP view of the **global** table |
| `address-family ipv4 vrf X` | the BGP view of VRF **X** |

**What `redistribute` means:** *copy routes from one table into another*. `redistribute ospf 4` under `address-family ipv4 vrf IT-VRF-CAMPUS` means "take what OSPF process 4 learned and put copies into CAMPUS's BGP view, where the RT/export rules can act on them".

Without a `redistribute`, a VRF's BGP view stays empty and nothing can ever leak out of it. This is exactly why `IT-VRF-TCI` leaks nothing despite having route-targets configured.

---

## 7. Route-maps - the if/then filters

A route-map is a numbered list of rules. Each rule is `permit` or `deny`, optionally has `match` conditions, and optionally `set`s something.

```cisco
route-map IMPORT-CAMPUS-FROM-GLOBAL deny 5
 match community FROM-GLOBAL-TO-CAMPUS
!
route-map IMPORT-CAMPUS-FROM-GLOBAL permit 200
 set community 58983300
```

How it is evaluated, for each route, in sequence-number order:

1. Try seq 5. Does the route carry one of those communities? If **yes** → the rule is `deny` → **route is dropped**, stop.
2. Try seq 200. No `match` clause at all → matches everything → rule is `permit` → route is accepted, and its community is overwritten with `58983300`.

> [!danger] The implicit deny at the end
> Every route-map ends with an **invisible `deny` that matches everything**. A route-map that contains only `permit 10 / match X` will **silently discard every route that does not match X**. This is used deliberately several times in this config - see `SET-TAG-TO-GLOBAL-COMMUNITY` in [[05 - Tags 80 and 800]]. If you ever add a `match` line to an existing route-map, ask yourself what now falls off the end.

`set` without `additive` **replaces**. `set community 58983300` wipes any community the route was already carrying. That matters in [[04 - Global Leaking and Communities]].

---

## 8. Prefix-lists - the lists of networks

```cisco
ip prefix-list CAMPUS-SUBNETS seq 5 permit 10.128.1.0/24
ip prefix-list CAMPUS-SUBNETS seq 10 permit 10.128.2.0/23
```

Matches those exact prefixes only. The modifiers change that:

| Written | Means |
|---|---|
| `permit 10.128.1.0/24` | exactly `10.128.1.0/24` |
| `permit 172.28.0.0/16 le 32` | `172.28.0.0/16` **and any more specific prefix inside it**, up to a /32 |
| `permit 0.0.0.0/0 le 32` | **literally every possible prefix** - a wildcard "permit all" |
| `permit 0.0.0.0/0 ge 16` | any prefix with a mask of /16 or longer |
| `permit 0.0.0.0/0` | **only the default route**, nothing else |

> [!note] Read these carefully in this config
> `ip prefix-list LEAKED-VRF-CAMPUS seq 200 permit 0.0.0.0/0 le 32` is a **permit-everything** list - it is a placeholder, not a filter. By contrast `LEAKED-VRF-WIFI-GUEST` lists six individual /32s and is a very tight filter. Same naming pattern, completely different effect.

---

## 9. BGP communities - "where did this route come from?"

A **community** is a 32-bit number you can staple onto a BGP route. It carries no meaning to the router; it means whatever your design says it means. Here it answers one question: *which VRF did this route originate in?*

```cisco
route-map EXPORT-CAMPUS-TO-GLOBAL permit 10
 match ip address prefix-list CAMPUS-SUBNETS
 set community 4259905600                     ! = "I came from CAMPUS"
```

### Decoding the community numbers

The config shows communities as raw 32-bit decimals. The usual readable form is `AS:value`, where:

```
decimal = (AS x 65536) + value
65001 x 65536 = 4,259,905,536
```

So subtract `4259905536` from any `42599055xx` number to get the low half:

| Decimal in config | Readable | Meaning in this design |
|---|---|---|
| `4259905598` | `65001:62` | route originated in **VDI** |
| `4259905600` | `65001:64` | route originated in **CAMPUS** |
| `4259905601` | `65001:65` | (WIFIGUEST - only in unused route-map `CHECK-TAG`) |
| `4259905602` | `65001:66` | route originated in **ACCESS-CONTROL** |
| `4259905604` | `65001:68` | route originated in **MGMNT** |
| `4259905605` | `65001:69` | route originated in **DC** |
| `4259905629` | `65001:93` | route originated in **VRF-TEST-A** |
| `4259905630` | `65001:94` | route originated in **VRF-TEST-B** |
| `58983300` | `900:900` | **route came from the GLOBAL table** |
| `4249905602` | `64848:27074` | ⚠️ **typo** - see [[08 - Findings and Cleanup]] |

Notice the numbering convention: the community value for "came from CAMPUS" is `64`, which is the route-target number of `IT-VRF-CAMPUS-BACKBONE`. That is just a mnemonic the designers chose; communities and route-targets are different attribute types and never collide.

### Standard vs expanded community-lists

```cisco
ip community-list expanded FROM-GLOBAL-TO-CAMPUS permit 4259905602
```

`expanded` means the value is treated as a **regular expression matched against the text form of the route's communities**, not as a number. `standard` would treat it as an exact numeric value. Expanded lists are slower and can match substrings by accident. See the warning in [[08 - Findings and Cleanup]].

---

## 10. Route tags - breadcrumbs that survive redistribution

Any route in IOS can carry a 32-bit **tag**. OSPF external LSAs carry it natively, BGP can set it, and it survives being redistributed from one protocol into another. It is a note-to-self written on the route.

```cisco
route-map SET-TAG-TO-GLOBAL-COMMUNITY permit 10
 match community GLOBAL-COMMUNITY
 set tag 800                      ! "remember: this one was born in Global"
```

...and later:

```cisco
route-map NO-RED-TAG-TO-GLOBAL deny 5
 match tag 800 80                 ! "don't let tagged routes back in"
```

This is the entire anti-loop system, and it gets its own note: [[05 - Tags 80 and 800]].

---

## 11. Redistribution loops - the problem the tags solve

When two protocols redistribute into *each other*, routes can bounce back and forth forever:

```
OSPF --redistribute--> BGP --redistribute--> OSPF --redistribute--> BGP ...
```

Each round trip strips the original metric and re-originates the route, which can cause churn, wrong path selection, or a route that never dies even after the real network is gone. The industry-standard fix is exactly what is used here: **tag routes on the way in, refuse tagged routes on the way out.**

---

## 12. `capability vrf-lite` - the one command you must not remove

```cisco
router ospf 4 vrf IT-VRF-CAMPUS
 capability vrf-lite
```

When a router redistributes BGP into an OSPF process inside a VRF, IOS assumes it is a service-provider PE router and sets the **DN (down) bit** in the generated LSA. Any VRF-aware OSPF router that sees the DN bit **ignores the LSA**, to stop a PE re-learning routes it originated. On a VRF-lite enterprise design that check is wrong and it silently blackholes everything.

`capability vrf-lite` disables the DN-bit behaviour. On this box it is present on every OSPF process that does `redistribute bgp` - and absent only on processes 3 (APPALTI), 7 (TCI) and 10 (MON), which do no BGP redistribution at all, so no harm. That consistency is a good sign the design was done deliberately.

---

## 13. Administrative distance cheat sheet

When the same prefix is learned twice, the lowest AD wins:

| Source | AD |
|---|---|
| Connected | 0 |
| Static | 1 |
| eBGP | 20 |
| OSPF (any type) | 110 |
| iBGP / locally-originated BGP | 200 |

Useful here: an OSPF external route at 110 beats the same prefix from BGP at 200. That is why the BGP-to-OSPF leak actually installs in the RIB, and it is also why the missing loop guard in the global table (see [[08 - Findings and Cleanup]]) is untidy rather than immediately fatal.

---

## Next

→ [[02 - VRF Inventory]] to meet the actual VRFs on this box.
