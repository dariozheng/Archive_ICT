---
title: Verification playbook
tags:
  - network/cisco
  - troubleshooting
  - playbook
up: "[[00 - MOC - VM90-IP-CORE1 Routing]]"
---

# Verification playbook

What to type on the box to prove anything in this vault. Organised by the question you are trying to answer.

---

## Q1 - "Is the route actually in the VRF?"

```
show ip route vrf IT-VRF-CAMPUS
show ip route vrf IT-VRF-CAMPUS 10.122.32.0
siv IT-VRF-CAMPUS 10.122.32.0          # alias, same thing
```

Read the code letters:

| Code | Means | In this design |
|---|---|---|
| `C` / `L` | connected / local | a real interface in the VRF |
| `S` | static | from `ip route vrf X ...` |
| `O` | OSPF intra-area | learned from a neighbour |
| `O IA` | OSPF inter-area | |
| `O E2` | OSPF external type 2 | **the leaked routes** - this is what you expect for anything from global or another VRF |
| `B` | BGP | a route imported by route-target that OSPF did not re-originate |

The detailed output shows the **tag**:

```
VM90-IP-CORE1# show ip route vrf IT-VRF-CAMPUS 10.122.32.0
Routing entry for 10.122.32.0/19
  Known via "ospf 4", distance 110, metric 20, type extern 2
  Tag 800                       <--- confirms it came from Global
```

`Tag 800` → from the global table. `Tag 800` → see [[05 - Tags 80 and 800]].
`Tag 80` → leaked in from another backbone VRF.
No tag → native to this VRF.

---

## Q2 - "Where did this route come from?"

```
show bgp vpnv4 unicast vrf IT-VRF-CAMPUS 10.122.32.0/19
show bgp vpnv4 unicast all 10.122.32.0/19
```

Look for:

- **Extended Community: RT:65001:xx** → which VRF exported it. Cross-reference the RT table in [[02 - VRF Inventory]].
- **Community:** → the source stamp. Decode with the table in [[01 - Primer - VRF RD RT and BGP#Decoding the community numbers]]. `58983300` / `900:900` means it came from the global table.
- **Route Distinguisher:** at the top → which VRF's view you are looking at.

To find every copy of a prefix across all VRFs at once:

```
show bgp vpnv4 unicast all | include 10.122.32.0
```

---

## Q3 - "What is this VRF importing and exporting?"

```
show vrf detail IT-VRF-CAMPUS
show vrf detail IT-VRF-CAMPUS-BACKBONE
show vrf brief
```

Gives you, in one place:
- the RD,
- the **effective** import and export route-target lists (already merged across VRF level and address-family level - useful because the `show run` splits them),
- the import/export route-maps for global leaking,
- the interfaces in the VRF,
- the import prefix limit actually in force.

```
show vrf detail | include Import|Export|VRF
```

---

## Q4 - "Did my route-map do anything?"

```
show route-map IMPORT-CAMPUS-FROM-GLOBAL
show route-map NO-RED-TAG-TO-GLOBAL
show route-map                              # all of them
```

Each sequence shows a **policy routing matches** / hit counter. A `deny` sequence with a rising counter is actively dropping routes. A route-map with all counters at zero is doing nothing - either it is not applied, or nothing matches.

This is the fastest way to confirm the findings in [[08 - Findings and Cleanup]]: if `IMPORT-CAMPUS-FROM-GLOBAL` seq 5 has hits, the segmentation deny is working; if it has zero, investigate.

```
show ip community-list
show ip community-list FROM-GLOBAL-TO-VDI
show ip prefix-list LEAKED-VRF-WIFI-GUEST
show ip prefix-list detail                  # includes hit counts
```

---

## Q5 - "Is redistribution actually configured and running?"

```
show ip protocols vrf IT-VRF-CAMPUS
show ip protocols
```

Shows, per VRF: which protocols are running, what they redistribute, which route-maps are applied, and which interfaces are passive. If a redistribution you expect is missing here, it is not configured - do not go hunting in the BGP table.

---

## Q6 - "Are the OSPF adjacencies up?"

```
show ip ospf neighbor
sion                                        # alias
show ip ospf 64 neighbor                    # one process
show ip ospf interface brief
show ip ospf interface brief vrf all
show bfd neighbors
```

Expected neighbour counts on this box:

| Process | Expected neighbours |
|---|---|
| 1 (global) | WAN routers ×2, cloud-exit routers ×2, external switch |
| 4, 2, 6, 8, 9 (service) | AGGR1, AGGR2, FTD |
| 64, 62, 66, 68, 69, 65 (backbone) | **exactly 1** - the FTD |
| 7 (TCI) | VM39 core switch + external switch + AGGR1/2 |

A backbone process with more than one neighbour means `passive-interface default` has been broken.

---

## Q7 - "Why does BGP show no neighbours?"

```
show bgp vpnv4 unicast all summary
show ip bgp summary
```

**Empty is correct.** There are no BGP peers on this router by design - see [[01 - Primer - VRF RD RT and BGP#6 BGP with no neighbours]]. To confirm BGP is doing its job anyway:

```
show bgp vpnv4 unicast all | count
show bgp vpnv4 unicast vrf IT-VRF-DC-BACKBONE
show bgp vpnv4 unicast rd 65001:64
```

If those tables have entries, the leaking engine is working.

---

## Q8 - "Are the tracked statics installed?"

```
show track
show track 4
show track 5
show ip sla statistics
show ip sla statistics 4
show ip sla configuration 4
show ip route static | count
```

`show track 4` should say **Up** with a recent change timestamp. If it says Down, every `track 4` static is missing from the RIB, and therefore from global BGP, and therefore from every VRF. See F4 in [[08 - Findings and Cleanup]].

Cross-check that the SLA source address exists:

```
show ip interface brief | include 10.142.96
show ip interface brief | include 10.142.100.21
```

---

## Q9 - "Which VRF is this interface in?"

```
show ip interface brief vrf all
show interface description | include 3241
sri Port-channel11.3241                     # alias for show run int
show vrf interfaces
```

---

## Q10 - "Prove the segmentation actually holds"

The routing-table test - a prefix that should be invisible must be absent:

```
show ip route vrf IT-VRF-WIFIGUEST 10.128.2.0
! expected: % Network not in table

show ip route vrf IT-VRF-CAMPUS 10.140.4.0
! expected: reachable only as O E2 tag 80 (via firewall), not as a direct leak
```

The forwarding test:

```
ping vrf IT-VRF-WIFIGUEST 10.128.2.50
traceroute vrf IT-VRF-CAMPUS 10.140.4.20
```

A `traceroute` from CAMPUS to a DC address **should show the firewall as a hop**. If it does not, the hairpin has been bypassed somewhere - go straight to [[08 - Findings and Cleanup]].

---

## Q11 - "Confirm the specific findings"

| Finding | Command |
|---|---|
| F1 typo | `show ip community-list FROM-GLOBAL-TO-VDI` then `show ip route vrf IT-VRF-VDI` for access-control subnets |
| F2 AC↔MGMNT | `show ip route vrf IT-VRF-MGMNT` looking for access-control subnets, and vice versa |
| F3 unfiltered export | `show bgp vpnv4 unicast all \| include 65001:62` - count how many VDI prefixes are in global |
| F4 SLA source | `show ip sla statistics 4` and `show ip interface brief \| include 10.142.96.82` |
| F5 global loop | `show ip route \| include ^O E2` - count how many VRF-origin prefixes are in the global OSPF domain |
| F6 community format | `show run \| include bgp-community` and inspect how `show bgp` prints a community |
| Dead route-maps | `show route-map \| include ^route-map` then grep the running config for each name |

Quick way to find unreferenced objects:

```
show run | include route-map
show run | section route-map
```
The first lists both definitions and references; anything that appears only once is defined but never used.

---

## Safe change procedure

```
! 1. Snapshot
copy running-config bootflash:pre-change-20260913.cfg
show run | redirect bootflash:pre-change-20260913.txt

! 2. Safety net (auto-reload if you lose the session)
reload in 15

! 3. Make the change
configure terminal
 ...
end

! 4. Verify
show ip route vrf <affected>
show route-map <changed>
show ip ospf neighbor

! 5a. Happy
reload cancel
copy running-config startup-config

! 5b. Not happy
configure replace bootflash:pre-change-20260913.cfg
```

> [!warning] Two commands that bite
> - `vrf forwarding X` on an interface **removes the IP address**. Always paste `ip address` immediately after.
> - Changing `rd` on a live VRF tears down all its BGP state. Treat as a reload-level change.
>
> And after any route-target or community-list edit, routes do not move until you refresh:
> ```
> clear bgp vpnv4 unicast * soft
> ```
> `soft` is safe here because there are no peers to reset.

---

## One-shot health check

Paste this block to get a full picture:

```
term len 0
show clock
show version | include uptime|Version
show vrf brief
show ip interface brief vrf all
show ip ospf neighbor
show bfd neighbors
show ip protocols
show track
show ip sla statistics
show bgp vpnv4 unicast all summary
show vrf detail | include VRF|Import|Export
show route-map
show ip route summary
show ip route vrf * summary
```

---

← Back to [[00 - MOC - VM90-IP-CORE1 Routing]]
