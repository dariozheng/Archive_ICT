---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - ccnp
  - category/networking/networking_general
icon: FasNetworkWired
iconColor:
last_update: 2026-07-06
---
**Exam:** Implementing Cisco Enterprise Advanced [[Routing]] and Services (ENARSI 300-410 v1.1) **Duration:** 90 minutes | **Format:** Multiple choice, drag-and-drop, simlets/labs **Role in certification:** Concentration exam for CCNP Enterprise (paired with ENCOR 350-401) **Plan length:** ~16 weeks at 10–14 hours/week (adjust to your pace)

---

## Blueprint Weighting (study time should roughly mirror this)

|Domain|Weight|
|---|---|
|1.0 Layer 3 Technologies|35%|
|2.0 VPN Technologies|20%|
|3.0 Infrastructure Security|20%|
|4.0 Infrastructure Services|25%|

---

# PHASE 0 — Setup & Prerequisites (Week 0)

Before touching ENARSI content:

1. **Download the official exam topics PDF** from the Cisco Learning Network — https://learningnetwork.cisco.com/s/enarsi-exam-topics. Print it. Check off every line item as you master it. This is your master checklist.
2. **Verify your ENCOR/CCNA routing foundations.** ENARSI assumes you already know basic [[OSPF]], EIGRP, [[Border Gateway Protocol|BGP]], and [[IPv6]] configuration. If EIGRP metrics or OSPF LSA types are fuzzy, do a 1-week ENCOR routing refresher first.
3. **Build your lab environment** (pick one):
    - **Cisco Modeling Labs (CML) Personal** — best fidelity, official IOS-XE images (~$199/yr) — https://developer.cisco.com/modeling-labs/
    - **EVE-NG Community + IOSv/CSR1000v images** — free platform, very popular for ENARSI — https://www.eve-ng.net
    - **GNS3** — free, works well with IOSv/IOL images — https://www.gns3.com
    - **Boson NetSim for ENARSI** — simulator with guided labs if you don't want to build topologies yourself — https://www.boson.com/netsim-cisco-network-simulator
    - Note: Packet Tracer is NOT sufficient for ENARSI (no MPLS, DMVPN, VRF-Lite depth).
4. **Buy/gather your core materials** (see Resources section at the end).
5. **Create a study log** (spreadsheet or Notion): date, topic, hours, confidence 1–5, weak points.

---

# PHASE 1 — Layer 3 Technologies Part I: IGPs (Weeks 1–4)

_This is the heart of the exam (35%). Do not rush it._

## Week 1 — Routing Fundamentals & Route Manipulation

Study order:

1. Administrative distance (all routing protocols) — default values, floating static routes, AD manipulation, troubleshooting AD conflicts
2. Routing table decision process (longest match → AD → metric)
3. Prefix lists vs. standard/extended ACLs for route filtering
4. Route maps: match/set clauses, sequence logic, implicit deny, continue statements
5. Route tagging and filtering with route maps
6. Policy-Based Routing (PBR): configure and verify, local PBR, `set ip next-hop`, verify with `debug ip policy`
7. Loop prevention mechanisms: split horizon, route poisoning, filtering, tagging
8. Manual and auto-summarization behavior per protocol
9. Bidirectional Forwarding Detection (BFD): modes, timers, protocol registration

Labs: static routing with AD manipulation, PBR steering traffic to two ISPs, route-map filtering lab.

Sources:

- OCG (Official Cert Guide) Ch. on IPv4/IPv6 static routing, PBR — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- Cisco white paper: _"Route Selection in Cisco Routers"_ (Doc ID 8651) — https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/8651-21.html
- Cisco doc: _"Bidirectional Forwarding Detection"_ — IOS-XE IP Routing BFD Configuration Guide — https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html (search "BFD configuration guide")
- RFC 5880 (BFD) — skim sections 1–4 — https://www.rfc-editor.org/rfc/rfc5880

## Week 2 — EIGRP (classic + named mode)

Study order:

1. EIGRP fundamentals review: DUAL, feasibility condition, FD/RD, successors/feasible successors
2. Classic vs. **named mode** configuration (address-family, af-interface, topology base) — named mode is heavily tested
3. Neighbor relationships: K-values, [[Autonomous System|AS]] mismatch, authentication (MD5 + SHA in named mode), passive interfaces, mismatched subnets, timers
4. EIGRP stub routing: all stub types, why remote sites use it, stuck-in-active (SIA) and how stubs prevent it
5. EIGRP load balancing: equal and unequal cost (variance)
6. EIGRP summarization (interface-level), leak maps
7. EIGRP over IPv6 and **EIGRP inside a [[VRF]]** (blueprint tests EIGRP in "VRF and global" contexts — lab `address-family ipv4 vrf X autonomous-system Y`)
8. Troubleshooting methodology: `show ip eigrp neighbors/topology/interfaces`, event logs, debugs

Labs: build classic AND named-mode topologies; break authentication, K-values, and stub configs on purpose; convert classic → named.

Sources:

- OCG EIGRP chapters (3 chapters: fundamentals, troubleshooting v4, troubleshooting v6) — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- Cisco white paper: _"Enhanced Interior Gateway Routing Protocol"_ (Doc ID 16406) — the classic EIGRP white paper — https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/16406-eigrp-toc.html
- Cisco doc: _"EIGRP Stub Routing"_ configuration guide — https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html (search "EIGRP stub routing")
- RFC 7868 (Cisco's EIGRP informational RFC) — skim — https://www.rfc-editor.org/rfc/rfc7868
- INE / CBT Nuggets EIGRP troubleshooting modules — https://ine.com | https://www.cbtnuggets.com/it-training/cisco/enarsi

## Week 3 — OSPF (v2 and v3)

Study order:

1. OSPF neighbor states (Down → Full) and exactly what breaks at each state — memorize this cold
2. Adjacency requirements: area ID, timers, MTU, authentication, network type, stub flags, subnet match
3. Network types: broadcast, non-broadcast, point-to-point, point-to-multipoint — DR/BDR election, mismatch symptoms
4. LSA types 1–7 in depth, OSPF database interpretation (`show ip ospf database`)
5. Area types: stub, totally stubby, NSSA, totally NSSA — which LSAs are blocked in each, the forward address, LSA type 7→5 translation
6. Router types: internal, backbone, ABR, ASBR — how to identify each in `show ip ospf` and the database
7. Path preference: intra-area > inter-area > E1 > E2 (and N1/N2), cost manipulation, reference bandwidth
8. Summarization: `area range` (ABR) vs. `summary-address` (ASBR)
9. Virtual links and GRE alternatives
10. Authentication: plaintext, MD5, SHA (key chains), OSPFv3 IPsec authentication
11. OSPFv3: differences from v2, address families, LSA changes
12. Troubleshooting flows: adjacency, missing routes, suboptimal routing

Labs: multi-area topology with every area type; break MTU, timers, network types; OSPFv3 AF lab dual-stack.

Sources:

- OCG OSPF chapters (4 chapters: fundamentals, adjacency troubleshooting, route troubleshooting, OSPFv3) — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- **Cisco white paper: "OSPF Design Guide" (Doc ID 7039)** — one of the best OSPF documents ever written; read it fully — https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/7039-1.html
- Cisco white paper: _"What Are OSPF Areas and Virtual Links?"_ (Doc ID 13703) — https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13703-8.html
- Cisco doc: _"OSPF Neighbor States"_ (Doc ID 13685) — https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13685-13.html
- RFC 2328 (OSPFv2) — reference — https://www.rfc-editor.org/rfc/rfc2328 ; RFC 5340 (OSPFv3) — skim differences section — https://www.rfc-editor.org/rfc/rfc5340
- Optional deep dive: _"OSPF and IS-IS: Choosing an IGP for Large-Scale Networks"_ concepts — https://www.amazon.com/s?k=OSPF+and+IS-IS+Choosing+an+IGP

## Week 4 — Redistribution & Route Control (the exam's favorite trap area)

Study order:

1. Redistribution rules per protocol: seed metrics, subnets keyword, metric-type
2. What gets redistributed (connected interfaces running the protocol, routes in RIB from that protocol)
3. Multipoint redistribution problems: routing loops, suboptimal routing, feedback
4. Loop prevention in redistribution: route tags, AD manipulation, distribute lists, prefix lists, route maps
5. Redistribution into/out of OSPF (E1 vs E2, NSSA behavior), EIGRP (external AD 170), BGP
6. VRF-Lite: configure and verify, route leaking basics, `ip vrf forwarding` vs. new `vrf definition` syntax
7. Full review week: rebuild one big lab combining EIGRP + OSPF + redistribution + filtering

Labs: two-point redistribution with loop creation then fix via tagging; VRF-Lite with overlapping address space.

Sources:

- OCG redistribution chapters (2 chapters + troubleshooting) — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- **Cisco white paper: "Redistributing Routing Protocols" (Doc ID 8606)** — mandatory reading — https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/8606-redist.html
- Cisco doc: _"VRF-Lite"_ configuration guide — https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html (search "VRF-Lite configuration")
- Blog: networklessons.com redistribution series (excellent visuals) — https://networklessons.com/tag/redistribution

**Checkpoint 1 (end of Week 4):** Take a domain quiz (OCG chapter review questions for all Layer 3 IGP chapters). Score < 80%? Repeat weak areas before moving on.

---

# PHASE 2 — Layer 3 Technologies Part II: BGP (Weeks 5–6)

## Week 5 — BGP Fundamentals & Neighbor Relationships

Study order:

1. iBGP vs. eBGP rules: TTL, next-hop behavior, AD (20/200), split horizon rule for iBGP
2. Neighbor states (Idle → Established) and troubleshooting each transition
3. Peering problems: TTL/ebgp-multihop, update-source, authentication (MD5), timers, ACLs blocking TCP 179
4. Blueprint-specific neighbor details: **4-byte AS numbers** (asplain/asdot), **private AS ranges and `remove-private-as`**, **route refresh capability**, **synchronization** (legacy rule — know what it was and why it's disabled by default)
5. Route reflectors: cluster-id, originator-id, client vs non-client rules (blueprint explicitly EXCLUDES multiple RRs, confederations, and dynamic peers — don't over-invest there)
6. Next-hop-self, peer groups, dynamic neighbors
7. BGP inside VRF-Lite (per-VRF address families) and IPv6 BGP (address families, activating neighbors)

## Week 6 — BGP Path Selection & Policies

Study order:

1. **BGP best-path algorithm — memorize the full order** (Weight → LocPref → locally originated → AS-path → Origin → MED → eBGP>iBGP → IGP metric to next hop → ...). Use a mnemonic ("We Love Oranges AS Oranges Mean Pure Refreshment").
2. Path manipulation: weight, local preference, AS-path prepending, MED — where each is applied (inbound vs outbound influence)
3. Inbound/outbound filtering: prefix lists, filter lists (AS-path ACLs), route maps, distribute lists
4. Regular expressions for AS-path filtering
5. Communities (standard, no-export, no-advertise, local-AS)
6. BGP aggregation: `aggregate-address`, summary-only, suppress-map, unsuppress-map, AS-SET
7. Troubleshooting missing/suboptimal BGP routes, `show ip bgp` output mastery

Labs: 4-AS topology; manipulate path with each attribute; RR cluster; regex filtering; break MD5/multihop.

Sources:

- OCG BGP chapters (3 chapters) — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- **Cisco white paper: "BGP Best Path Selection Algorithm" (Doc ID 13753)** — mandatory — https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html
- Cisco white paper: _"BGP Case Studies"_ (Doc ID 26634) — a legendary 5-part document, read all parts — https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/26634-bgp-toc.html
- Cisco doc: _"Troubleshooting BGP"_ (Doc ID 22166) — https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/22166-bgp-trouble-main.html
- RFC 4271 (BGP-4) — reference — https://www.rfc-editor.org/rfc/rfc4271 ; RFC 4456 (Route Reflection) — skim — https://www.rfc-editor.org/rfc/rfc4456
- Book (optional, career-grade): _Internet Routing Architectures_ by Sam Halabi — https://www.amazon.com/s?k=Internet+Routing+Architectures+Halabi
- Video: INE or CBT Nuggets BGP path-selection deep dives — https://ine.com | https://www.cbtnuggets.com/it-training/cisco/enarsi

**Checkpoint 2:** Full Layer 3 domain practice test (Boson ExSim domain mode or Pearson Test Prep by chapter).

---

# PHASE 3 — VPN Technologies (Weeks 7–9) — 20%

## Week 7 — MPLS & MPLS L3VPN (describe-level, but know it well)

Study order:

1. MPLS operations: LSR roles (ingress/egress/transit), label switching, LSP, PHP (penultimate hop popping)
2. LDP: neighbor discovery, label distribution, LIB vs LFIB vs FIB
3. MPLS Layer 3 VPN components: PE/CE/P routers, RD (route distinguisher) vs RT (route target) — know the difference cold
4. MP-BGP and VPNv4 address family basics
5. How a packet flows through an MPLS VPN end to end (two-label stack)

Sources:

- OCG MPLS chapters (2 chapters) — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- **Cisco white paper: MPLS technology & VPN overview pages** — https://www.cisco.com/c/en/us/products/ios-nx-os-software/multiprotocol-label-switching-mpls/index.html
- Cisco Press (optional deep): _MPLS Fundamentals_ by Luc De Ghein — Ch. 1–3, 7 — https://www.ciscopress.com (search "MPLS Fundamentals")
- RFC 3031 (MPLS architecture) — skim — https://www.rfc-editor.org/rfc/rfc3031 ; RFC 4364 (BGP/MPLS IP VPNs) — skim sections 1–4 — https://www.rfc-editor.org/rfc/rfc4364
- Cisco Live session: _"Introduction to MPLS"_ (BRKMPL-1100, free on-demand) — https://www.ciscolive.com/on-demand.html (search "BRKMPL-1100")

## Weeks 8–9 — DMVPN (configure & verify — heavily tested)

Study order:

1. GRE fundamentals and mGRE
2. NHRP: registration, resolution, redirect/shortcut (Phase 3 mechanics)
3. DMVPN Phase 1 vs Phase 2 vs Phase 3 — differences in routing design and spoke-to-spoke traffic
4. Routing protocols over DMVPN: EIGRP (split horizon, next-hop-self issues), OSPF network-type issues over mGRE
5. IPsec protection of DMVPN: crypto profiles, IKEv2 basics, tunnel protection
6. Troubleshooting: `show dmvpn`, `show ip nhrp`, NHRP registration failures, hub/spoke reachability
7. Awareness-level: FlexVPN, GETVPN (how they differ from DMVPN)

Labs: full hub-and-2-spokes DMVPN in all three phases; run EIGRP then OSPF over it; add IPsec; break NHRP.

Sources:

- OCG DMVPN chapters (2 chapters: DMVPN + troubleshooting) — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- **Cisco white paper: "Dynamic Multipoint VPN (DMVPN) Design Guide"** (Cisco Validated Design) — https://www.cisco.com/c/en/us/td/docs/solutions/Enterprise/WAN_and_MAN/DMVPDG.html
- **Cisco doc: "Shortcut Switching Enhancements for NHRP in DMVPN Networks" (Phase 3)** — https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html (search "Shortcut Switching Enhancements NHRP")
- Cisco doc: _"Most Common DMVPN Troubleshooting Solutions"_ (Doc ID 111976) — https://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/111976-dmvpn-troubleshoot-00.html
- Cisco Live: _"DMVPN Deployment and Troubleshooting"_ sessions — https://www.ciscolive.com/on-demand.html (search "DMVPN")
- RFC 2332 (NHRP) — skim concepts only — https://www.rfc-editor.org/rfc/rfc2332

**Checkpoint 3:** VPN domain quiz + rebuild DMVPN Phase 3 from a blank config without notes.

---

# PHASE 4 — Infrastructure Security (Weeks 10–11) — 20%

## Week 10 — Device Security

Study order:

1. AAA: authentication, authorization, accounting; TACACS+ vs RADIUS (port numbers, encryption scope, use cases)
2. Method lists, local fallback, `aaa new-model` gotchas (locking yourself out)
3. Device access control: line configuration (VTY/console), privilege levels, transport input
4. Control Plane Policing (CoPP): class maps, policy maps, service-policy on control plane, what traffic hits the control plane
5. uRPF (Unicast Reverse Path Forwarding): strict vs loose mode, where each applies, verification

Sources:

- OCG security chapters (2 chapters) — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- **Cisco white paper: "Control Plane Policing Implementation Best Practices"** — https://sec.cloudapps.cisco.com/security/center/resources/copp_best_practices
- **Cisco white paper: "Understanding Unicast Reverse Path Forwarding"** — https://sec.cloudapps.cisco.com/security/center/resources/unicast_reverse_path_forwarding
- Cisco doc: _"TACACS+ and RADIUS Comparison"_ (Doc ID 13838) — https://www.cisco.com/c/en/us/support/docs/security-vpn/remote-authentication-dial-user-service-radius/13838-10.html
- RFC 3704 (uRPF / ingress filtering BCP 84) — skim — https://www.rfc-editor.org/rfc/rfc3704

## Week 11 — Router Security Features & IPv6 Security

Study order:

1. IPv4 ACL review (as applied to security/troubleshooting scenarios), time-based ACLs
2. IPv6 traffic filters (IPv6 ACLs and their implicit ND permits)
3. **IPv6 First Hop Security** (describe level, all of them):
    - RA Guard
    - DHCPv6 Guard
    - Binding table
    - ND inspection/snooping
    - IPv6 Source Guard
4. Why each exists: rogue RA attacks, DHCPv6 spoofing, ND spoofing

Labs: AAA with local fallback; CoPP policy rate-limiting ICMP; strict uRPF blocking spoofed source; RA Guard on a switchport.

Sources:

- OCG IPv6 First Hop Security chapter — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- **Cisco doc: "IPv6 First-Hop Security" configuration guide** — https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html (search "IPv6 First-Hop Security configuration guide")
- Cisco Press (optional): _IPv6 Security_ by Scott Hogg & Eric Vyncke — Ch. on FHS — https://www.ciscopress.com (search "IPv6 Security")
- Cisco Live: _"IPv6 Security Threats and Mitigations"_ — https://www.ciscolive.com/on-demand.html (search "IPv6 security")
- RFC 6105 (RA Guard) — skim — https://www.rfc-editor.org/rfc/rfc6105

---

# PHASE 5 — Infrastructure Services (Weeks 12–13) — 25%

## Week 12 — Management, Logging, SNMP, DHCP

Study order:

1. Device management troubleshooting: console/VTY, Telnet vs SSH (crypto key gen, version 2), HTTP/HTTPS server, SCP, TFTP/FTP
2. Syslog: severity levels 0–7 (memorize), local buffer vs remote, timestamps (`service timestamps`), conditional debugs, debug best practices
3. SNMP: v2c vs v3 (auth/priv, security levels noAuthNoPriv/authNoPriv/authPriv), traps vs informs, views/groups/users
4. DHCP IPv4: server, relay (`ip helper-address`), client; common failures; DHCP options
5. DHCPv6: stateful vs stateless, SLAAC + DHCPv6 combinations, relay, prefix delegation (awareness)

Sources:

- OCG device management + DHCP chapters — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- Cisco doc: _"Configuring SNMP Support"_ (IOS-XE Network Management Configuration Guide) — https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html (search "SNMP configuration guide")
- Cisco doc: _"IP Addressing: DHCP Configuration Guide"_ (includes relay agent concepts) — https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html (search "DHCP configuration guide")
- Cisco doc: _"Conditionally Triggered Debugs / Troubleshooting and Fault Management"_ — https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html (search "troubleshooting and fault management")

## Week 13 — IP SLA, Object Tracking, NetFlow, DNA Center

Study order:

1. IP SLA: ICMP echo, UDP jitter (one-way delay, jitter, packet loss), HTTP; responders; scheduling
2. Object tracking: track SLA reachability/state, tie to static routes and HSRP, delay up/down
3. Using IP SLA + PBR/static routes for failover designs
4. NetFlow v5 vs v9, Flexible NetFlow (flow records, monitors, exporters, samplers), verification commands
5. Cisco DNA Center (Catalyst Center) Assurance: network/device/client health, issues & insights, path trace — describe-level troubleshooting workflows

Labs: IP SLA tracking a default route with failover to backup ISP; Flexible NetFlow exporting to a collector.

Sources:

- OCG chapters on IP services + DNA Center Assurance — https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide")
- **Cisco white paper: "Cisco IOS NetFlow Overview"** — https://www.cisco.com/c/en/us/products/collateral/ios-nx-os-software/ios-netflow/prod_white_paper0900aecd80406232.html
- Cisco: Flexible NetFlow technology page — https://www.cisco.com/c/en/us/products/ios-nx-os-software/flexible-netflow/index.html
- Cisco doc: _"IP SLAs Configuration Guide"_ (IOS-XE) — https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html (search "IP SLAs configuration guide")
- Cisco DNA Center Assurance User Guide (free) — https://www.cisco.com/c/en/us/support/cloud-systems-management/dna-center/products-user-guide-list.html
- Cisco Live: _"DNA Center Assurance Deep Dive"_ sessions — https://www.ciscolive.com/on-demand.html (search "DNA Center Assurance")

**Checkpoint 4:** Services + Security domain quizzes; overall practice score target ≥ 80%.

---

# PHASE 6 — Review, Practice Exams, Final Prep (Weeks 14–16)

## Week 14 — Full Blueprint Review

1. Go line-by-line through the official exam topics PDF; anything not checked = immediate review
2. Rebuild your three "mega labs" from scratch, no notes:
    - Mega lab 1: EIGRP + OSPF + redistribution + PBR + VRF-Lite
    - Mega lab 2: BGP multi-AS with path manipulation + filtering
    - Mega lab 3: DMVPN Phase 3 + IPsec + EIGRP + IP SLA failover
3. Create/review flashcards (Anki) for: AD values, BGP best path order, OSPF LSA types, area type LSA filtering, syslog levels, SNMPv3 security levels, DMVPN phases, TACACS+/RADIUS differences, NetFlow versions

## Week 15 — Practice Exams

1. **Boson ExSim-Max for 300-410** — the gold-standard practice exam; take Exam A in simulation mode — https://www.boson.com/practice-exam/300-410-cisco-exsim-max-practice-exam
2. Review EVERY question (right and wrong); read all explanations
3. Take Exam B mid-week; target ≥ 85%
4. Pearson Test Prep exams (bundled with the OCG) as supplementary — https://www.pearsontestprep.com
5. Drill weak domains in Boson's custom/domain mode

## Week 16 — Final Week

1. Take Boson Exam C under strict exam conditions
2. Light review only; re-read the OSPF Design Guide and BGP Best Path white papers one final time
3. Redo flashcards daily
4. Day before exam: stop studying by afternoon, sleep well
5. Exam day: budget ~1 min/question, flag and move on (note: Cisco exams do NOT allow going back — answer everything before advancing), expect simlets on OSPF/EIGRP/BGP/DMVPN troubleshooting

---

# MASTER RESOURCE LIST

> **Note on links:** Cisco doc-ID links (the `support/docs/...` URLs) have been stable for 20+ years, but Cisco occasionally reorganizes pages. If any link 404s, search Google for `Cisco Doc ID <number>` or the document title — it always resurfaces.

## Primary Books

1. **CCNP Enterprise Advanced Routing ENARSI 300-410 Official Cert Guide, 2nd Edition** — Raymond Lacoste & Brad Edgeworth (Cisco Press). Your backbone text; matches v1.1 blueprint. → https://www.ciscopress.com (search "ENARSI 300-410 Official Cert Guide") | https://www.amazon.com/s?k=ENARSI+300-410+Official+Cert+Guide
2. _CCNP Enterprise ENARSI 300-410 Portable Command Guide_ (Cisco Press) — quick command reference for lab days. → https://www.amazon.com/s?k=CCNP+ENARSI+Portable+Command+Guide
3. Optional deep-dives:
    - _Internet Routing Architectures_ (Halabi) → https://www.amazon.com/s?k=Internet+Routing+Architectures+Halabi
    - _MPLS Fundamentals_ (De Ghein) → https://www.ciscopress.com (search "MPLS Fundamentals")
    - _IPv6 Security_ (Hogg/Vyncke) → https://www.ciscopress.com (search "IPv6 Security")
    - _Routing TCP/IP Vol. I_ (Doyle) → https://www.amazon.com/s?k=Routing+TCP%2FIP+Volume+1+Doyle

## Video Courses (pick 1–2)

4. **CBT Nuggets — Cisco CCNP ENARSI (300-410)** — engaging, lab-driven → https://www.cbtnuggets.com/it-training/cisco/enarsi
5. **INE — CCNP Enterprise ENARSI course** — deepest technical treatment → https://ine.com (Networking → CCNP Enterprise learning path)
6. **Cisco U. — ENARSI learning path** (official Cisco training, includes labs; free tier available) → https://u.cisco.com (search "ENARSI")
7. Pluralsight ENARSI path → https://www.pluralsight.com/search?q=ENARSI
8. Kevin Wallace / KWTrain ENARSI course (Udemy, budget-friendly) → https://www.udemy.com/courses/search/?q=ENARSI+Kevin+Wallace | https://kwtrain.com
9. Free YouTube supplements:
    - Jeremy's IT Lab → https://www.youtube.com/@JeremysITLab
    - Keith Barker → https://www.youtube.com/@KeithBarker
    - NetworkChuck → https://www.youtube.com/@NetworkChuck
    - Art of Network Engineering (podcast) → https://artofnetworkengineering.com

## Labs & Practice

10. Lab platforms (hands-on labs are non-negotiable for ENARSI):
    - **Cisco Modeling Labs (CML) Personal** → https://developer.cisco.com/modeling-labs/
    - **EVE-NG** → https://www.eve-ng.net
    - **GNS3** → https://www.gns3.com
11. **Boson NetSim for ENARSI** (guided labs) → https://www.boson.com/netsim-cisco-network-simulator
12. **Boson ExSim-Max 300-410** (best practice exams on the market) → https://www.boson.com/practice-exam/300-410-cisco-exsim-max-practice-exam
13. Pearson Test Prep (included with OCG) → https://www.pearsontestprep.com
14. Cisco Learning Network — official ENARSI exam topics + study community → https://learningnetwork.cisco.com/s/enarsi-exam-topics

## Cisco White Papers & Technical Documents (all free on cisco.com)

15. **OSPF Design Guide** (Doc ID 7039) — mandatory → https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/7039-1.html
16. **BGP Best Path Selection Algorithm** (Doc ID 13753) — mandatory → https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html
17. **BGP Case Studies** (Doc ID 26634) — mandatory → https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/26634-bgp-toc.html
18. **Redistributing Routing Protocols** (Doc ID 8606) — mandatory → https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/8606-redist.html
19. Enhanced Interior Gateway Routing Protocol white paper (Doc ID 16406) → https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/16406-eigrp-toc.html
20. Route Selection in Cisco Routers (Doc ID 8651) → https://www.cisco.com/c/en/us/support/docs/ip/enhanced-interior-gateway-routing-protocol-eigrp/8651-21.html
21. What Are OSPF Areas and Virtual Links? (Doc ID 13703) → https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13703-8.html
22. OSPF Neighbor States explained (Doc ID 13685) → https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13685-13.html
23. Troubleshooting BGP (Doc ID 22166) → https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/22166-bgp-trouble-main.html
24. Dynamic Multipoint VPN (DMVPN) Design Guide (Cisco Validated Design) → https://www.cisco.com/c/en/us/td/docs/solutions/Enterprise/WAN_and_MAN/DMVPDG.html
25. Most Common DMVPN Troubleshooting Solutions (Doc ID 111976) → https://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/111976-dmvpn-troubleshoot-00.html
26. MPLS technology & VPN white papers (landing page) → https://www.cisco.com/c/en/us/products/ios-nx-os-software/multiprotocol-label-switching-mpls/index.html
27. Control Plane Policing Implementation Best Practices (Cisco Security Center) → https://sec.cloudapps.cisco.com/security/center/resources/copp_best_practices
28. Understanding Unicast Reverse Path Forwarding (Cisco Security Center) → https://sec.cloudapps.cisco.com/security/center/resources/unicast_reverse_path_forwarding
29. TACACS+ and RADIUS Comparison (Doc ID 13838) → https://www.cisco.com/c/en/us/support/docs/security-vpn/remote-authentication-dial-user-service-radius/13838-10.html
30. IPv6 First-Hop Security configuration guide (search "IPv6 First-Hop Security" for your IOS-XE version) → https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html
31. Cisco IOS NetFlow Overview white paper + Flexible NetFlow → https://www.cisco.com/c/en/us/products/collateral/ios-nx-os-software/ios-netflow/prod_white_paper0900aecd80406232.html → https://www.cisco.com/c/en/us/products/ios-nx-os-software/flexible-netflow/index.html
32. IP SLAs Configuration Guide (IOS-XE) — search "IP SLAs Configuration Guide" at: → https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/series.html
33. Cisco DNA Center (Catalyst Center) Assurance User Guide → https://www.cisco.com/c/en/us/support/cloud-systems-management/dna-center/products-user-guide-list.html

## RFCs (skim-level, for depth and tie-breaker questions)

34. RFC 2328 — OSPFv2 → https://www.rfc-editor.org/rfc/rfc2328
35. RFC 5340 — OSPFv3 → https://www.rfc-editor.org/rfc/rfc5340
36. RFC 4271 — BGP-4 → https://www.rfc-editor.org/rfc/rfc4271
37. RFC 4456 — BGP Route Reflection → https://www.rfc-editor.org/rfc/rfc4456
38. RFC 7868 — EIGRP → https://www.rfc-editor.org/rfc/rfc7868
39. RFC 5880 — BFD → https://www.rfc-editor.org/rfc/rfc5880
40. RFC 3031 — MPLS Architecture → https://www.rfc-editor.org/rfc/rfc3031
41. RFC 4364 — BGP/MPLS IP VPNs → https://www.rfc-editor.org/rfc/rfc4364
42. RFC 2332 — NHRP → https://www.rfc-editor.org/rfc/rfc2332
43. RFC 3704 — Ingress Filtering (uRPF, BCP 84) → https://www.rfc-editor.org/rfc/rfc3704
44. RFC 6105 — IPv6 RA Guard → https://www.rfc-editor.org/rfc/rfc6105
45. RFC 4861 — IPv6 Neighbor Discovery → https://www.rfc-editor.org/rfc/rfc4861

## Free Cisco Live On-Demand Sessions (free account required)

46. Cisco Live On-Demand Library → https://www.ciscolive.com/on-demand.html
    - Search "BRKMPL-1100" (Introduction to MPLS)
    - Search "DMVPN" (deployment & troubleshooting sessions)
    - Search "BRKRST OSPF" / "BRKRST BGP" (deployment & troubleshooting deep dives)
    - Search "IPv6 security" (BRKSEC-2003 and successors)

## Communities

47. Cisco Learning Network (official forums & study groups) → https://learningnetwork.cisco.com
48. r/ccnp on Reddit → https://www.reddit.com/r/ccnp/
49. networklessons.com — outstanding written lessons with diagrams (subscription, covers nearly every ENARSI topic) → https://networklessons.com
50. Discord study servers — search Disboard for "network engineering" → https://disboard.org/search?keyword=networking

---

# QUICK MEMORIZATION HIT-LIST (make flashcards Day 1)

- Administrative distances: connected 0, static 1, eBGP 20, EIGRP 90, OSPF 110, IS-IS 115, RIP 120, EIGRP external 170, iBGP 200
- BGP best-path order (all 11+ steps)
- OSPF LSA types 1–7 and which area types block which
- OSPF neighbor states in order; EIGRP packet types; BGP neighbor states in order
- Syslog severity 0–7 (Every Awesome Cisco Engineer Will Need Ice-cream Daily)
- SNMPv3 security levels per mode
- DMVPN Phase 1/2/3 differences
- TACACS+ (TCP 49, full encryption, command authorization) vs RADIUS (UDP 1812/1813, password-only encryption)
- NetFlow v5 (fixed, IPv4 only) vs v9 (template-based) vs Flexible NetFlow
- IPv6 FHS features and the attack each one stops

---

## Weekly Rhythm That Works

- **2–3 sessions of theory** (book/video), 60–90 min each
- **2 lab sessions**, 90–120 min each — configure it, then BREAK it, then fix it (ENARSI is a troubleshooting exam)
- **1 review session**: flashcards + previous weeks' checkpoint questions
- Every topic: read → watch → lab → break/fix → explain it out loud (Feynman technique)

Good luck — ENARSI is widely considered the hardest CCNP Enterprise concentration, but it's also the one that makes you a genuinely strong routing engineer.