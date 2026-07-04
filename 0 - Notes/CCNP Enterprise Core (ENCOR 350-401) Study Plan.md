

_An 18-to-20-week, phase-ordered plan for the ENCOR 350-401 v1.2 exam, with topic lists, labs, books, courses, white papers, design guides, and RFCs per phase._

> [!important] This plan targets exam blueprint v1.2, which went live on 2026-03-19. The headline change: all wireless content was removed from ENCOR and moved to a new CCNP Wireless track with its own core exam (350-101 WLCOR). Domain 6 was renamed to "Automation and Artificial Intelligence", and Cisco product names were updated throughout (DNA Center is now Catalyst Center, vManage is now SD-WAN Manager, SD-WAN is now Catalyst SD-WAN). Most study material published before 2026 still assumes v1.1 and includes wireless chapters you can skip. Always cross-check against the official exam topics: https://learningnetwork.cisco.com/s/encor-exam-topics

Quick navigation: [[#Exam facts (v1.2)|exam facts]] | [[#How to use this plan|method]] | [[#Phase 0 - Baseline and lab setup|setup]] | [[#The study sequence at a glance|sequence]] | [[#Master resource list|resources]] | [[#White papers and design guides|white papers]] | [[#Week-by-week schedule|schedule]] | [[#Exam logistics and final tips|logistics]]

## Exam facts (v1.2)

_What the exam is, what it earns, and how it is weighted._

|Attribute|Value|
|---|---|
|Exam|350-401 ENCOR, Implementing Cisco Enterprise Network Core Technologies, v1.2 (effective 2026-03-19)|
|Duration|120 minutes|
|Questions|Not officially published; commonly reported around 90-110 (multiple choice, multi-select, drag-and-drop, sims)|
|Cost|400 USD (or Cisco Learning Credits), via Pearson VUE test center or OnVUE online proctoring|
|Languages|English, Japanese|
|Passing score|Variable scaled cut, unofficially reported around 825/1000|
|Earns|Cisco Certified Specialist - Enterprise Core|
|Counts toward|Core exam for CCNP Enterprise; qualifying exam for the CCIE Enterprise Infrastructure lab|
|Full CCNP Enterprise|ENCOR plus one concentration exam (ENARSI 300-410 is the most common pairing)|
|Validity|3 years; renew by re-exam or Continuing Education credits|

Domain weights in v1.2:

|#|Domain|Weight|
|---|---|---|
|1|Architecture|15%|
|2|Virtualization|10%|
|3|Infrastructure|30%|
|4|Network Assurance|10%|
|5|Security|20%|
|6|Automation and Artificial Intelligence|15%|

> [!note] Domain percentages are unchanged from v1.1, but with wireless gone the question density on the remaining topics rises: L3 routing, multicast, Catalyst SD-WAN, security, and automation are all reported to carry more weight in practice. Multicast coverage was reportedly strengthened, SD-WAN policy depth increased, and zero-trust concepts entered the security domain. The "Artificial Intelligence" part of domain 6 is currently thin: the concrete blueprint change is that Catalyst Center is tested with both traditional and AI-powered workflows under assurance topic 4.5, plus general awareness of AI-assisted network operations.

Product rename table (old names still appear everywhere in books and older courses; the exam uses the new names):

|Old name|Current name|
|---|---|
|Cisco DNA Center|Cisco Catalyst Center|
|Cisco SD-WAN (Viptela)|Cisco Catalyst SD-WAN|
|vManage|SD-WAN Manager|
|vSmart|SD-WAN Controller|
|vBond|SD-WAN Validator|
|vEdge / cEdge|WAN Edge|

## How to use this plan

_A repeatable loop applied to eleven phases over roughly 18 weeks._

The plan assumes 10-12 hours per week for about 180-200 total hours. At 15+ hours per week you can compress to 12-14 weeks; part-time at 6-8 hours stretches to about 26 weeks. Each phase runs the same loop:

1. Read the mapped Official Cert Guide chapters first, doing the "Do I Know This Already" quiz before and the chapter review after.
2. Watch the matching video course module for a second explanation of anything that did not land.
3. Lab it the same week. Configuration knowledge decays in days if it never touches a CLI.
4. Write the note. Distill each topic into your vault in your own words, with verification command output pasted into bash fences. If you cannot write the note without the book open, you are not done with the topic.
5. Drill. Add flashcards (Anki or the OCG memory tables) for timers, defaults, code points, and attribute orders, and answer the chapter question bank.
6. Read one white paper or design guide per phase to see the technology as Cisco deploys it, not just as the exam tests it.

> [!info] The Official Cert Guide 2nd edition (2023) is written against blueprint v1.1. It remains the backbone text for v1.2: skip the wireless part (chapters 17-21), and pull the publisher's digital update content for blueprint changes from https://www.ciscopress.com/newcerts before you start. If a 3rd edition aligned to v1.2 has shipped by the time you buy, take that instead.

## Phase 0 - Baseline and lab setup

_One week to close CCNA gaps, download the blueprint, and stand up a lab you will use in every later phase._

Blueprint first:

- Download the official v1.2 exam topics PDF from https://learningnetwork.cisco.com/s/encor-exam-topics and keep it next to this plan. Every line item becomes a checklist entry; the goal of the next 17 weeks is to be able to rate yourself 4/5 or better on each line.
- Bookmark the exam page for logistics: https://www.cisco.com/site/us/en/learn/training-certifications/exams/encor.html

CCNA-level knowledge assumed by everything below. Refresh anything shaky now:

- IPv4 subnetting fluency and IPv6 addressing (types, SLAAC, link-local behavior)
- VLANs, trunking, and inter-VLAN routing basics
- Static routing, administrative distance, and the idea of a routing protocol
- Standard and extended ACL syntax
- Device management: SSH, local users, basic IOS navigation
- Reading simple Python and JSON (you do not need to write much, but you must read it)

Lab environment. Pick one primary and one supplementary:

- Cisco Modeling Labs (CML), https://developer.cisco.com/modeling-labs/ : the free tier (small node count) covers early phases; the paid personal tier is the most comfortable option for the full plan since it ships legal IOS XE, IOSv/IOSvL2, and Catalyst 9000v images.
- EVE-NG (https://www.eve-ng.net) or GNS3 (https://www.gns3.com) with Catalyst 8000v/CSR 1000v and IOSvL2 images if you already run a virtualization host; note that image licensing is on you.
- Cisco DevNet Sandboxes, https://developer.cisco.com/site/sandbox/ : free, reservable, and the only practical way to touch Catalyst Center and Catalyst SD-WAN Manager. Mandatory for phases 7, 9, and 10.
- Cisco dCloud, https://dcloud.cisco.com : scripted full-stack demos of SD-Access and Catalyst SD-WAN with real controllers, free with a cisco.com login.
- Packet Tracer is below ENCOR level for most topics; keep it only as a quick STP/FHRP scratchpad.

Suggested core topology, reused all plan long (grow it, never rebuild it):

```
            AS 65001                        AS 65002
   +------ R1 ---------- R2 ------+   +------ R4
   |        |  OSPF area 0 |      |   |  eBGP
   |        |              |      +---+
   |       R3 (area 1 ABR) |
   |        |              |
  SW1 ==== SW2   (== EtherChannel, HSRP/VRRP toward hosts)
   |         |
  PC1       PC2
```

Baseline tooling:

- Obsidian vault section for ENCOR notes (see [[#Folding this into the vault|vault layout]])
- Anki (or the OCG's own flashcard app) for spaced repetition
- A lab journal note: every lab gets date, topology delta, and the two or three show commands that proved it worked

## The study sequence at a glance

_Ordered so that every phase only depends on phases before it._

The blueprint lists Architecture first, but studying in blueprint order forces you to absorb SD-Access before you know LISP and VXLAN, and SD-WAN before you know BGP-like control planes. This sequence builds bottom-up instead:

1. Phase 1, weeks 1-2: switching and forwarding internals (CEF, TCAM, VLANs, STP/RSTP/MST, EtherChannel)
2. Phase 2, weeks 3-4: IGP routing (routing essentials, OSPF v2/v3 in depth, EIGRP for comparison)
3. Phase 3, week 5: BGP (peering, path attributes, best-path selection)
4. Phase 4, week 6: multicast and QoS
5. Phase 5, week 7: IP services (NTP, NAT/PAT, HSRP/VRRP/GLBP)
6. Phase 6, weeks 8-9: virtualization and overlays (hypervisors, VRF-lite, GRE, IPsec, LISP, VXLAN)
7. Phase 7, weeks 10-11: architecture (campus design, high availability, SD-Access, Catalyst SD-WAN, cloud)
8. Phase 8, weeks 12-13: security (AAA, ACL/CoPP, TrustSec, MACsec, threat-defense portfolio, zero trust)
9. Phase 9, week 14: network assurance (syslog, SNMP, NetFlow, SPAN/ERSPAN, IP SLA, Catalyst Center, NETCONF/RESTCONF)
10. Phase 10, weeks 15-16: automation and AI (Python/JSON, YANG, REST APIs, Catalyst Center and SD-WAN Manager APIs, EEM, orchestration)
11. Phase 11, weeks 17-18 (+2 buffer): consolidation, full practice exams, weak-area loops, exam booking

## Phase 1 - Switching and forwarding internals

_How a Catalyst actually moves a frame, then the L2 control plane on top of it._

What to master:

- Forwarding architecture: process switching vs CEF, RIB vs FIB, adjacency table, centralized vs distributed forwarding, software vs hardware CEF, CAM vs TCAM lookups, SDM templates
- VLANs, access vs trunk ports, 802.1Q tagging, native VLAN behavior and its security implications
- Spanning tree: 802.1D fundamentals, root election and port roles, RSTP (802.1w) states, proposal/agreement convergence, MST (802.1s) regions and instance mapping
- STP tuning and protection: PortFast, root guard, BPDU guard, BPDU filter, loop guard, UDLD
- EtherChannel: static vs PAgP vs LACP, negotiation rules, load-balancing hash options, common bring-up failures

Primary sources:

- OCG 2nd ed. chapters 1-5 (Packet Forwarding; Spanning Tree Protocol; Advanced STP Tuning; Multiple Spanning Tree Protocol; VLAN Trunks and EtherChannel Bundles): https://www.ciscopress.com/store/ccnp-and-ccie-enterprise-core-encor-350-401-official-9780138216764
- NetworkLessons.com switching section for alternate explanations of RSTP sync and MST region logic: https://networklessons.com

Lab work (SW1/SW2 pair plus a third switch if node budget allows):

- Force root bridge moves and watch RSTP reconverge; time it against classic 802.1D behavior
- Build a two-region MST setup, then deliberately mismatch the config name and observe the boundary
- Trigger BPDU guard and root guard, and document recovery (errdisable)
- Break LACP with mismatched modes and read the negotiation state

```bash
show spanning-tree detail
show spanning-tree mst configuration
show etherchannel summary
show mac address-table dynamic
show platform tcam utilization   # platform dependent
```

White papers and deep dives:

- Understanding Rapid Spanning Tree Protocol (802.1w), Cisco TAC document 24062: https://www.cisco.com/c/en/us/support/docs/lan-switching/spanning-tree-protocol/24062-146.html
- Understanding Multiple Spanning Tree Protocol (802.1s), Cisco TAC document 24248: https://www.cisco.com/c/en/us/support/docs/lan-switching/spanning-tree-protocol/24248-147.html
- Cisco Catalyst 9000 architecture white papers (TCAM, ASIC pipeline, UADP; one per series, the 9300 paper is the best single read): https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9300-series-switches/nb-06-cat9300-architecture-cte-en.html - the full per-series set is on the white-paper listing page: https://www.cisco.com/c/en/us/products/switches/catalyst-9300-series-switches/white-paper-listing.html
- Cisco Catalyst 9000 Platform StackWise Virtual white paper: https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9000/nb-06-cat-9k-stack-wp-cte-en.html
- IEEE standards to know by name: 802.1D, 802.1w, 802.1s, 802.1Q, 802.3ad/802.1AX (texts on IEEE Xplore, https://ieeexplore.ieee.org - the 802 series is free there through the IEEE GET Program)

## Phase 2 - IGP routing: OSPF and EIGRP

_The heaviest-tested routing block: OSPF in real depth, EIGRP mostly for contrast._

What to master:

- Routing essentials: administrative distance, metric comparison, longest-prefix match, recursive lookup, RIB installation logic, static and floating static routes
- EIGRP at compare-and-contrast depth: DUAL, feasibility condition, successor vs feasible successor, metric components, advanced distance vector vs link state framing
- OSPFv2 in configuration depth: neighbor state machine, hello/dead and other adjacency parameters, DR/BDR election, network types (broadcast vs point-to-point and their mismatches), areas and ABR/ASBR roles, LSA types 1, 2, 3, 4, 5, 7, stub/totally-stubby/NSSA behavior, cost manipulation, interarea summarization, filtering, default-information originate
- OSPFv3: address families, differences from v2, dual-stack operation

Primary sources:

- OCG chapters 6-10 (IP Routing Essentials; EIGRP; OSPF; Advanced OSPF; OSPFv3)
- OSPF Design Guide, Cisco TAC document 7039 (old, still the single best free OSPF design text): https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/7039-1.html
- Routing TCP/IP, Volume I, 2nd ed. (Doyle and Carroll) for the theory behind LSDB synchronization; read the OSPF chapters, skim the rest: https://www.ciscopress.com/store/routing-tcp-ip-volume-1-9781587052026

Lab work (R1-R3 multi-area):

- Multi-area OSPF with one NSSA; trace a type 7 to type 5 translation at the ABR
- Break an adjacency four ways (MTU, timer, area type, network type) and diagnose each from show/debug output only
- Summarize between areas and watch the LSDB shrink; compare cost math on mixed link speeds with auto-cost reference-bandwidth changes
- OSPFv3 AF config over the same topology, dual stack

White papers and deep dives:

- RFC 2328 (OSPFv2), https://www.rfc-editor.org/rfc/rfc2328 and RFC 5340 (OSPF for IPv6), https://www.rfc-editor.org/rfc/rfc5340 : read the concepts sections, not every packet field
- Cisco Live On-Demand: search the library for OSPF deployment and troubleshooting breakouts: https://www.ciscolive.com

## Phase 3 - BGP

_Enough BGP to configure eBGP/iBGP cleanly and predict best-path selection cold._

What to master:

- When BGP instead of an IGP; path-vector logic; eBGP vs iBGP rules (TTL, next-hop behavior, loop prevention via AS_PATH and split horizon)
- Peering mechanics: neighbor states, update-source and loopback peering, ebgp-multihop, authentication
- Address families and NLRI exchange; network statements vs redistribution into BGP
- Path attributes and the best-path algorithm in order (weight, local preference, locally originated, AS path length, origin, MED, eBGP over iBGP, IGP metric to next hop, and the tiebreakers)
- Basic policy: prefix filtering, AS-path prepending, communities at awareness level

Primary sources:

- OCG chapters 11-12 (BGP; Advanced BGP)
- BGP Case Studies, Cisco TAC document 26634: https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/26634-bgp-toc.html
- BGP Best Path Selection Algorithm, Cisco TAC document 13753: https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html
- Deep-dive shelf: Internet Routing Architectures, 2nd ed. (Halabi), https://www.ciscopress.com/store/internet-routing-architectures-9781578702336 and Troubleshooting BGP (Jain and Edgeworth), https://www.ciscopress.com/store/troubleshooting-bgp-a-practical-guide-to-understanding-9781587144646

Lab work (add R4 in AS 65002):

- eBGP between AS 65001 and 65002, iBGP full mesh inside 65001 with next-hop-self
- Manipulate best path with weight, then local preference, then prepending; predict the winner before each show ip bgp
- Break peering with a wrong update-source and diagnose from the neighbor state alone

White papers and deep dives:

- RFC 4271 (BGP-4), the FSM and decision process sections: https://www.rfc-editor.org/rfc/rfc4271

## Phase 4 - Multicast and QoS

_Two blueprint areas people skimp on; v1.2 reportedly increased multicast density._

What to master:

- Multicast addressing (224/4 ranges, well-known groups, MAC mapping and its 32:1 overlap)
- IGMPv2 vs IGMPv3 (source-specific joins), IGMP snooping
- PIM sparse mode end to end: shared tree and RPT, rendezvous point role, register process, SPT switchover, RPF checks; RP assignment options (static, Auto-RP, BSR) at concept level
- QoS models: best effort, IntServ, DiffServ; classification and marking (DSCP, PHBs: EF, AF classes, CS), trust boundaries
- Policing vs shaping, single-rate and dual-rate concepts, congestion management (CBWFQ, LLQ), congestion avoidance (WRED)

Primary sources:

- OCG chapters 13-14 (Multicast; Quality of Service)
- IP Multicast Technology Overview, Cisco white paper: https://www.cisco.com/c/en/us/td/docs/ios/solutions_docs/ip_multicast/White_papers/mcst_ovr.html
- Enterprise QoS Solution Reference Network Design Guide (SRND): the classic Cisco design document for end-to-end QoS; read the framework chapters. Cisco no longer hosts it at a stable product URL, but the full v3.3 book survives as a PDF on the Cisco community legacy file store: https://community.cisco.com/legacyfs/online/legacy/3/2/6/64623-qossrnd.pdf
- Deep-dive shelf: End-to-End QoS Network Design, 2nd ed. (Szigeti et al.), https://www.ciscopress.com/store/end-to-end-qos-network-design-quality-of-service-for-9781587143694 and IP Multicast, Volume I (Loveless, Blair, Durai), https://www.ciscopress.com/store/ip-multicast-volume-i-cisco-ip-multicast-networking-9781587144592

Lab work:

- PIM-SM with a static RP; join a group from a host, capture the (*,G) then (S,G) entries, watch SPT switchover
- Deliberately fail RPF (wrong unicast path) and read the mroute flags
- MQC policy on a router: classify by ACL and DSCP, LLQ for a voice class, police a scavenger class and observe markdown

```bash
show ip mroute
show ip pim rp mapping
show ip igmp groups
show policy-map interface g0/1
```

White papers and deep dives:

- RFC 4594 (DiffServ service class guidelines), https://www.rfc-editor.org/rfc/rfc4594 ; RFC 3376 (IGMPv3), https://www.rfc-editor.org/rfc/rfc3376 ; RFC 7761 (PIM-SM), https://www.rfc-editor.org/rfc/rfc7761

## Phase 5 - IP services

_The short but dense services chapter: time, translation, and first-hop redundancy._

What to master:

- NTP: client/server and peer modes, stratum, authentication, and design hygiene (source interface, limiting who can sync)
- NAT: inside/outside local/global terminology cold, static NAT, dynamic pools, PAT/overload, common troubleshooting order
- First-hop redundancy: HSRP v1 vs v2 (groups, virtual MAC, priority, preemption, interface and object tracking), VRRP v2/v3 differences from HSRP, GLBP AVG/AVF load sharing
- Where DHCP relay and stateless services fit (light coverage)

Primary sources:

- OCG chapter 15 (IP Services)
- Network Time Protocol: Best Practices White Paper, Cisco TAC document 19643: https://www.cisco.com/c/en/us/support/docs/availability/high-availability/19643-ntpm.html

Lab work:

- HSRP pair on SW1/SW2 with object tracking against an upstream interface; measure failover with a continuous ping
- Convert the same setup to VRRP, note default timer and preemption differences
- PAT overload on R1 for the PC subnet, verify translations under load

White papers and deep dives:

- RFC 5905 (NTPv4), https://www.rfc-editor.org/rfc/rfc5905 ; RFC 5798 (VRRPv3), https://www.rfc-editor.org/rfc/rfc5798

## Phase 6 - Virtualization and overlay tunnels

_The 10% virtualization domain plus the tunnel tech that SD-Access is built from._

What to master:

- Device virtualization: type 1 vs type 2 hypervisors, VMs vs containers, virtual switching concepts, SR-IOV awareness
- Path virtualization: VRF-lite (VRF definition, interface assignment, per-VRF routing and verification)
- GRE: encapsulation, tunnel interfaces, recursive-routing pitfalls
- IPsec: IKEv2 at concept level, ESP, tunnel vs transport mode, GRE over IPsec and VTI as the practical patterns
- LISP: the map-and-encap model, EID vs RLOC, ITR/ETR, map server and map resolver roles
- VXLAN: why 24-bit VNIs, VTEPs, header structure, how it carries L2 over L3, flood-and-learn vs EVPN control plane at awareness level

Primary sources:

- OCG chapters 16 and 27 (Overlay Tunnels; Virtualization)
- VXLAN Overview: Cisco Nexus 9000 Series Switches, Cisco white paper (Nexus framing, but the cleanest VXLAN explainer Cisco publishes): https://www.cisco.com/c/en/us/products/collateral/switches/nexus-9000-series-switches/white-paper-c11-729383.html
- Cisco LISP technology overview and collateral, from the LISP landing page: https://www.cisco.com/c/en/us/products/ios-nx-os-software/locator-id-separation-protocol-lisp/index.html

Lab work:

- Two VRFs with overlapping address space on one router; prove isolation with per-VRF pings and routing tables
- GRE tunnel between R1 and R4 across the BGP core, then wrap it in IPsec; capture before/after headers
- If images allow, a minimal LISP site pair with a shared map server/resolver

White papers and deep dives:

- RFC 2784 (GRE), https://www.rfc-editor.org/rfc/rfc2784 ; RFC 7348 (VXLAN), https://www.rfc-editor.org/rfc/rfc7348 ; RFC 9300 and 9301 (LISP architecture and control plane), https://www.rfc-editor.org/rfc/rfc9300 and https://www.rfc-editor.org/rfc/rfc9301

## Phase 7 - Architecture: campus design, SD-Access, Catalyst SD-WAN

_The design domain, done after the building blocks so the fabrics are demystified rather than memorized._

What to master:

- Campus design: 2-tier vs 3-tier, access/distribution/core roles, L2 vs routed access tradeoffs, oversubscription thinking
- High availability: redundancy design, SSO, NSF/graceful restart, StackWise and StackWise Virtual placement, FHRP recap in a design frame
- On-prem vs cloud: IaaS/PaaS/SaaS distinctions, connectivity models, what changes operationally
- SD-Access: underlay vs overlay, fabric roles (control plane node running LISP map server/resolver, border node, edge node, intermediate), virtual networks as VRFs, SGT-based policy plane, Catalyst Center as the automation and assurance layer, interoperability with traditional campus
- Catalyst SD-WAN: orchestration/management/control/data plane split, SD-WAN Manager, SD-WAN Controller, SD-WAN Validator, WAN Edge roles, OMP route exchange, TLOCs, VPN segmentation (VPN 0, 512, service VPNs), control vs data policy and application-aware routing (v1.2 gives this more depth than older material does)
- Hardware vs software switching recap from phase 1, now framed as a design consideration

Primary sources:

- OCG chapters 22-23 (Enterprise Network Architecture; Fabric Technologies)
- Cisco Software-Defined Access Solution Design Guide (Cisco Validated Design): https://www.cisco.com/c/en/us/td/docs/solutions/CVD/Campus/cisco-sda-design-guide.html
- Cisco Catalyst SD-WAN Design Guide (Cisco Validated Design): https://www.cisco.com/c/en/us/td/docs/solutions/CVD/SDWAN/cisco-sdwan-design-guide.html
- Campus LAN and Wireless LAN Solution Design Guide (Cisco Validated Design), https://www.cisco.com/c/en/us/td/docs/solutions/CVD/Campus/cisco-campus-lan-wlan-design-guide.html and Campus Network for High Availability Design Guide, https://www.cisco.com/c/en/us/td/docs/solutions/Enterprise/Campus/HA_campus_DG/hacampusdg.html
- Deep-dive shelf: Cisco Software-Defined Wide Area Networks (Gooley, Yanch, Schuemann, Curran; Cisco Press), https://www.ciscopress.com/store/cisco-software-defined-wide-area-networks-designing-9780136533177 and Cisco Software-Defined Access (Vemula, Gooley, Hasan; Cisco Press), https://www.ciscopress.com/store/cisco-software-defined-access-9780136448389

Lab work:

- DevNet sandbox: reserve the Catalyst Center sandbox, walk discovery, inventory, topology, and an assurance dashboard end to end
- DevNet sandbox or dCloud: Catalyst SD-WAN instance; identify every controller by role, read an OMP route, follow one app-aware routing policy from definition to effect
- On CML, build a routed-access underlay (point-to-point L3 links, an IGP, loopbacks) to internalize what Catalyst Center automates in LAN automation

White papers and deep dives:

- The four CVDs above are now linked directly; the Design Zone index remains the fallback if Cisco moves them: https://www.cisco.com/go/cvd
- Cisco Live On-Demand: SD-Access deep dive and Catalyst SD-WAN design breakout sessions: https://www.ciscolive.com

## Phase 8 - Security

_A fifth of the exam: device hardening, network policy, and the Cisco security portfolio by name and function._

What to master:

- Device access control: line vs local authentication, privilege levels, AAA login authentication and authorization, TACACS+ vs RADIUS compared properly (transport, encryption scope, command authorization)
- Infrastructure security: standard vs extended ACL behavior and placement, wildcard fluency, control plane policing (CoPP) policy construction and verification
- REST API security: TLS, token-based auth, keys and secrets handling, rate limiting concepts
- Threat-defense portfolio by function and current name: Cisco Secure Firewall (NGFW/NGIPS), Secure Email (ESA), Secure Web Appliance (WSA), Umbrella, Secure Endpoint (AMP), Secure Network Analytics (Stealthwatch), Talos as the intel backbone
- Segmentation: TrustSec SGT classification, propagation inline vs SXP, SGACL enforcement; MACsec (802.1AE) with MKA for link encryption, switch-to-switch and host-to-switch
- Zero trust and SASE concepts: multiple v1.2 change summaries report these entering the blueprint; learn the architecture vocabulary

> [!warning] v1.2 removed the wireless security line items (PSK, EAP, WebAuth for WLANs), and some change summaries report the wired NAC line (802.1X, MAB, WebAuth) was trimmed as well. Verify both against the official topics PDF before deciding how deep to go; as a working sysadmin you probably want 802.1X knowledge regardless of what the exam does with it.

Primary sources:

- OCG chapters 25-26 (Secure Network Access Control; Network Device Access Control and Infrastructure Security)
- Cisco Guide to Harden Cisco IOS Devices, Cisco TAC document 13608 (its control-plane section doubles as the CoPP best-practices reference): https://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html
- Cisco TrustSec technology page (white papers, configuration guides, at-a-glance docs): https://www.cisco.com/c/en/us/solutions/enterprise-networks/trustsec/index.html
- WAN MACsec white paper (Innovations in Ethernet Encryption 802.1AE for Securing High Speed 1-100GE WAN Deployments): https://www.cisco.com/c/dam/en/us/td/docs/solutions/Enterprise/Security/MACsec/WP-High-Speed-WAN-Encrypt-MACsec.pdf
- Cisco SAFE Secure Campus Architecture Guide, https://www.cisco.com/c/en/us/solutions/collateral/enterprise/design-zone-security/safe-secure-campus-architecture-guide.html (start with the SAFE Overview Guide if the model is new: https://www.cisco.com/c/en/us/solutions/collateral/enterprise/design-zone-security/safe-overview-guide.html)
- Cisco zero trust architecture white papers: Zero Trust at Scale (how Cisco IT deployed it), https://www.cisco.com/c/dam/en/us/products/collateral/security/zero-trust-at-scale.pdf and the Zero Trust Architectural Framework whitepaper, document 218443: https://www.cisco.com/c/en/us/support/docs/security-vpn/security-vpn/218443-verify-zero-trust-security-whitepaper.html

Lab work:

- AAA with TACACS+ configured and local fallback proven by breaking the server path
- CoPP policy that rate-limits ICMP to the control plane; verify with show policy-map control-plane while pinging the box
- ACL placement experiments: same policy as ingress-near-source vs egress-near-destination, compare
- If Catalyst 9000v images are available: SXP peering between two switches and an SGACL

## Phase 9 - Network assurance

_Seeing the network: classic telemetry, flow data, and Catalyst Center assurance including the new AI-workflow angle._

What to master:

- Diagnostics discipline: ping and extended ping, traceroute, debug and conditional debug, terminal monitor, when debugs are safe
- Syslog: severity levels cold (0-7), logging destinations, timestamps and buffered logging hygiene
- SNMP: v2c vs v3 (noAuthNoPriv, authNoPriv, authPriv), traps vs informs
- NetFlow and Flexible NetFlow: records, monitors, exporters, samplers, and reading a flow cache
- SPAN, RSPAN, ERSPAN: what each can cross and their config shapes
- IP SLA: probes (icmp-echo, udp-jitter), responders, and binding results to object tracking
- Catalyst Center assurance: health scores, device and client 360 views, workflows for configuration, monitoring, and management using both traditional and AI-powered workflows (blueprint topic 4.5 in v1.2)
- NETCONF and RESTCONF: enabling and verifying both on IOS XE (tested here as operational protocols, then used hands-on in phase 10)

Primary sources:

- OCG chapter 24 (Network Assurance), plus the NETCONF/RESTCONF portions of chapter 28
- Cisco IOS XE Model-Driven Telemetry white paper: https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9300-series-switches/model-driven-telemetry-wp.html
- Catalyst Center data sheet (the assurance feature tables and scale numbers), https://www.cisco.com/c/en/us/products/collateral/cloud-systems-management/dna-center/nb-06-dna-center-data-sheet-cte-en.html and the Cisco Catalyst Assurance User Guide: https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center-assurance/2-3-7/b_cisco_catalyst_assurance_2_3_7_ug.html

Lab work:

- Flexible NetFlow: custom record, monitor on an interface, read the cache during an iperf or repeated ping run
- ERSPAN session between two CML routers, capture at the destination
- IP SLA udp-jitter probe tied to a track object that demotes HSRP priority; fail the path and watch the FHRP react
- Enable netconf-yang and restconf, verify both respond

```bash
show flow monitor FLOWMON cache
show monitor session all
show ip sla statistics
show netconf-yang sessions
show platform software yang-management process
```

## Phase 10 - Automation and AI

_Domain 6: read code and models, drive real APIs, and automate the box itself._

What to master:

- Python literacy: data types, lists/dicts, conditionals, loops, functions, the requests library pattern; interpret scripts, not author frameworks
- JSON: construct and parse valid JSON by hand; know YAML and XML by sight
- YANG: what a data model is, structure (containers, lists, leaves), native vs open models (IETF, OpenConfig)
- NETCONF operations (get, get-config, edit-config, datastores) vs RESTCONF (URI structure, HTTP methods, Accept/Content-Type headers)
- REST fundamentals: verbs, response code classes (2xx/3xx/4xx/5xx and the specific ones: 200, 201, 204, 400, 401, 403, 404, 500), interpreting payloads specifically with Catalyst Center and RESTCONF (v1.2 topic 6.5)
- Catalyst Center Intent APIs and SD-WAN Manager REST API: authentication flow, token usage, common endpoints at recognition level
- EEM: construct an applet (event triggers: syslog, CLI, timer; actions; variables) for configuration, troubleshooting, or data collection (v1.2 topic 6.6)
- Orchestration: agent vs agentless models conceptually (v1.2 dropped the vendor-name list, but Ansible remains the obvious agentless example to lab); infrastructure-as-code awareness
- AI in network operations at awareness level: AIOps concepts, where Catalyst Center applies ML/AI (baselining, anomaly detection, AI-assisted workflows)

Primary sources:

- OCG chapters 28-29 (Foundational Network Programmability; Introduction to Automation Tools)
- Cisco DevNet learning labs (free): IOS XE programmability, Catalyst Center API, Catalyst SD-WAN API tracks at https://developer.cisco.com ; the IOS XE hub collects the programmability material in one place: https://developer.cisco.com/iosxe/
- IOS XE Programmability Configuration Guide, https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1718/b-1718-programmability-cg.html and the Catalyst Programmability and Automation white paper: https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9300-series-switches/catalyst-programmability-automation-wp.html
- Deep-dive shelf: Network Programmability and Automation, 2nd ed. (O'Reilly): https://www.oreilly.com/library/view/network-programmability-and/9781098110826/

Lab work:

- RESTCONF against a CML router: GET an interface config with curl or Postman, then PATCH a description; confirm on the CLI
- NETCONF with Python ncclient: get-config, then edit-config the same change
- Catalyst Center sandbox: authenticate for a token, pull the device inventory via the Intent API, walk the JSON
- EEM applet: on a syslog pattern (interface down), collect show tech to flash and log a message; trigger it by flapping the interface
- Optional stretch: a three-task Ansible playbook (ios_config) against two CML routers

White papers and deep dives:

- RFC 6241 (NETCONF), https://www.rfc-editor.org/rfc/rfc6241 ; RFC 8040 (RESTCONF), https://www.rfc-editor.org/rfc/rfc8040 ; RFC 7950 (YANG 1.1), https://www.rfc-editor.org/rfc/rfc7950

## Phase 11 - Consolidation and practice exams

_Two weeks (plus buffer) of deliberate review, timed exams, and weak-area loops._

Process:

1. Blueprint self-audit: score every line of the v1.2 topics PDF 1-5. Anything under 4 goes on the drill list.
2. OCG review pass: key topics tables, memory tables, and every end-of-chapter question you previously missed.
3. Pacing text: 31 Days Before Your CCNP and CCIE Enterprise Core Exam (Gargano, Cisco Press) structures exactly this window; skip its wireless days: https://www.ciscopress.com/store/31-days-before-your-ccnp-and-ccie-enterprise-core-exam-9780136965220
4. Practice exams in escalating realism: OCG Pearson Test Prep by domain first, then Boson ExSim-Max for 350-401 as full 120-minute timed sims, then the official Cisco U. practice exam (https://u.cisco.com/exams/4527) as the final calibration.
5. After every timed exam: review by domain, not by question. Re-lab anything you got wrong for a configuration reason.
6. Lab speed runs from a blank topology: bring up multi-area OSPF, an eBGP session with a best-path change, an HSRP pair with tracking, a Flexible NetFlow monitor, and one RESTCONF call. Each should be quick and error-free by now.

Readiness gate: book the exam when you are scoring 85%+ consistently on fresh (unseen) Boson forms and can pass your blueprint self-audit at 4+ everywhere.

> [!warning] Confirm any practice exam you buy is updated for v1.2 (no wireless questions, current product names) before paying. And avoid braindump sites entirely: they violate the Cisco exam NDA (a caught violation voids certifications and bans you) and their answer keys are routinely wrong, which is worse than no practice at all.

## Master resource list

_Everything referenced above plus the supporting cast, grouped by type._

### Official Cisco sources

- ENCOR v1.2 exam topics (the blueprint): https://learningnetwork.cisco.com/s/encor-exam-topics
- Exam page (logistics, scheduling entry point): https://www.cisco.com/site/us/en/learn/training-certifications/exams/encor.html
- Cisco U. ENCOR learning path (official course content, labs, assessments): https://u.cisco.com/paths/implementing-operating-cisco-enterprise-network-core-technologies-170
- Cisco U. official ENCOR practice exam: https://u.cisco.com/exams/4527
- Cisco Learning Network Enterprise certifications community (study groups, exam-change announcements): https://learningnetwork.cisco.com/s/topic/0TO3i0000008jYIGAY/enterprise-certifications-community
- Cisco DevNet (learning labs, sandboxes, API docs): https://developer.cisco.com
- Cisco Design Zone, home of the Cisco Validated Designs: https://www.cisco.com/go/cvd
- Cisco Live On-Demand Library (free recorded breakout sessions; search per phase): https://www.ciscolive.com
- Cisco Press blueprint-update content for the OCG: https://www.ciscopress.com/newcerts

### Core books

- CCNP and CCIE Enterprise Core ENCOR 350-401 Official Cert Guide, 2nd ed., Edgeworth, Garza Rios, Gooley, Hucaby (Cisco Press, 2023). The backbone. Written for v1.1: skip chapters 17-21 (wireless) and pull the digital blueprint updates. The Premium Edition adds four Pearson Test Prep practice exams: https://www.ciscopress.com/store/ccnp-and-ccie-enterprise-core-encor-350-401-official-9780138216764
- CCNP and CCIE Enterprise Core and CCNP Enterprise Advanced Routing Portable Command Guide, Empson and Gargano (Cisco Press). Command syntax quick reference for lab sessions: https://www.ciscopress.com/store/ccnp-and-ccie-enterprise-core-ccnp-enterprise-advanced-9780135768167
- 31 Days Before Your CCNP and CCIE Enterprise Core Exam, Gargano (Cisco Press). Structured final-month review; use in phase 11: https://www.ciscopress.com/store/31-days-before-your-ccnp-and-ccie-enterprise-core-exam-9780136965220

### Deep-dive shelf

_Optional per-topic depth; each maps to one phase and pays off well beyond the exam._

- Routing TCP/IP, Volume I, 2nd ed., Doyle and Carroll (Cisco Press) - phase 2: https://www.ciscopress.com/store/routing-tcp-ip-volume-1-9781587052026
- Internet Routing Architectures, 2nd ed., Halabi (Cisco Press) - phase 3: https://www.ciscopress.com/store/internet-routing-architectures-9781578702336
- Troubleshooting BGP, Jain and Edgeworth (Cisco Press) - phase 3: https://www.ciscopress.com/store/troubleshooting-bgp-a-practical-guide-to-understanding-9781587144646
- IP Routing on Cisco IOS, IOS XE, and IOS XR, Edgeworth, Foss, Garza Rios (Cisco Press) - phases 2-3: https://www.ciscopress.com/store/ip-routing-on-cisco-ios-ios-xe-and-ios-xr-an-essential-9781587144233
- End-to-End QoS Network Design, 2nd ed., Szigeti, Hattingh, Barton, Briley (Cisco Press) - phase 4: https://www.ciscopress.com/store/end-to-end-qos-network-design-quality-of-service-for-9781587143694
- IP Multicast, Volume I, Loveless, Blair, Durai (Cisco Press) - phase 4: https://www.ciscopress.com/store/ip-multicast-volume-i-cisco-ip-multicast-networking-9781587144592
- Cisco Software-Defined Wide Area Networks, Gooley, Yanch, Schuemann, Curran (Cisco Press) - phase 7: https://www.ciscopress.com/store/cisco-software-defined-wide-area-networks-designing-9780136533177
- Cisco Software-Defined Access, Vemula, Gooley, Hasan (Cisco Press) - phase 7: https://www.ciscopress.com/store/cisco-software-defined-access-9780136448389
- Network Programmability and Automation, 2nd ed., Edelman, Lowe, Oswalt, Adell (O'Reilly) - phase 10: https://www.oreilly.com/library/view/network-programmability-and/9781098110826/

### Video courses

- Cisco U. ENCOR learning path (official; updated for v1.2 after 2026-03-19): https://u.cisco.com/paths/implementing-operating-cisco-enterprise-network-core-technologies-170
- CBT Nuggets, Cisco CCNP Enterprise ENCOR 350-401 course: https://www.cbtnuggets.com
- INE, CCNP Enterprise learning path (strong on routing depth and labs): https://ine.com
- Pluralsight, ENCOR 350-401 learning path: https://www.pluralsight.com
- Kevin Wallace Training ENCOR course (also on Udemy): https://kwtrain.com
- Pearson/Cisco Press, CCNP and CCIE Enterprise Core ENCOR 350-401 Complete Video Course (search the title on https://www.ciscopress.com or in the O'Reilly library)
- Free full-length ENCOR playlists exist on YouTube (search ENCOR 350-401 on https://www.youtube.com); fine as a supplement, but verify any course you lean on has been updated for v1.2 (no wireless modules, current product names)

### Written lesson sites and blogs

- NetworkLessons.com: subscription; short, lab-backed articles mapped to the ENCOR blueprint; excellent second explanation source: https://networklessons.com
- PacketLife cheat sheets (free PDFs for OSPF, BGP, STP, QoS, IPsec and more): https://packetlife.net/library/cheat-sheets/
- Lost in Transit (Daniel Dib) for routing and design depth: https://lostintransit.se
- ipSpace.net (Ivan Pepelnjak) for a skeptical, design-level view of overlays and SDN claims: https://blog.ipspace.net
- Cisco support tech notes and configuration examples (the TAC documents now linked per phase live in this tree): https://www.cisco.com/c/en/us/support/index.html

### Lab platforms

- Cisco Modeling Labs: free tier for small topologies; paid personal tier with official IOS XE/IOSv/Catalyst 9000v images for the full plan: https://developer.cisco.com/modeling-labs/
- EVE-NG, https://www.eve-ng.net or GNS3, https://www.gns3.com as self-hosted alternatives (bring your own images)
- Cisco DevNet Sandboxes: free reservable Catalyst Center, Catalyst SD-WAN, and IOS XE programmability environments: https://developer.cisco.com/site/sandbox/
- Cisco dCloud full-stack SD-Access and SD-WAN demos: https://dcloud.cisco.com
- Cisco Packet Tracer: quick L2/FHRP scratchpad only: https://www.netacad.com

### Practice exams

- Boson ExSim-Max for 350-401: the strongest third-party sims with real explanations; confirm v1.2 alignment before purchase: https://www.boson.com
- Pearson Test Prep question banks bundled with the OCG (four full exams in the Premium Edition); redeem the book's access code at https://www.pearsontestprep.com
- Cisco U. official practice exam: https://u.cisco.com/exams/4527

### White papers and design guides

_The primary-source layer: read one or two per phase; together they cover most of the blueprint from the design side._

Design guides and CVDs (linked directly; the Design Zone index at https://www.cisco.com/go/cvd is the fallback if Cisco moves them):

1. Cisco Software-Defined Access Solution Design Guide (CVD) - phase 7: https://www.cisco.com/c/en/us/td/docs/solutions/CVD/Campus/cisco-sda-design-guide.html
2. Cisco Catalyst SD-WAN Design Guide (CVD) - phase 7: https://www.cisco.com/c/en/us/td/docs/solutions/CVD/SDWAN/cisco-sdwan-design-guide.html
3. Campus LAN and Wireless LAN Solution Design Guide (CVD) - phases 1, 7: https://www.cisco.com/c/en/us/td/docs/solutions/CVD/Campus/cisco-campus-lan-wlan-design-guide.html
4. Campus Network for High Availability Design Guide - phases 1, 7: https://www.cisco.com/c/en/us/td/docs/solutions/Enterprise/Campus/HA_campus_DG/hacampusdg.html
5. Enterprise QoS Solution Reference Network Design Guide (SRND) - phase 4 (classic v3.3 book, preserved as a PDF on the Cisco community legacy file store): https://community.cisco.com/legacyfs/online/legacy/3/2/6/64623-qossrnd.pdf
6. Cisco SAFE Secure Campus Architecture Guide - phase 8: https://www.cisco.com/c/en/us/solutions/collateral/enterprise/design-zone-security/safe-secure-campus-architecture-guide.html

Technology white papers (deep Cisco collateral URLs move more often than the design-guide tree; if one 404s, search the exact title on cisco.com):

7. Cisco Catalyst 9000 architecture white papers (per series; 9300 linked) - phase 1: https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9300-series-switches/nb-06-cat9300-architecture-cte-en.html (per-series listing: https://www.cisco.com/c/en/us/products/switches/catalyst-9300-series-switches/white-paper-listing.html)
8. Cisco Catalyst 9000 Platform StackWise Virtual white paper - phases 1, 7: https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9000/nb-06-cat-9k-stack-wp-cte-en.html
9. IP Multicast Technology Overview - phase 4: https://www.cisco.com/c/en/us/td/docs/ios/solutions_docs/ip_multicast/White_papers/mcst_ovr.html (more in the IP multicast white-paper index: https://www.cisco.com/c/en/us/tech/ip/ip-multicast/tech-white-papers-list.html)
10. VXLAN Overview: Cisco Nexus 9000 Series Switches - phase 6: https://www.cisco.com/c/en/us/products/collateral/switches/nexus-9000-series-switches/white-paper-c11-729383.html
11. Cisco LISP technology overview and white papers - phase 6: https://www.cisco.com/c/en/us/products/ios-nx-os-software/locator-id-separation-protocol-lisp/index.html
12. Cisco TrustSec white papers and guides - phase 8: https://www.cisco.com/c/en/us/solutions/enterprise-networks/trustsec/index.html
13. WAN MACsec white paper (Innovations in Ethernet Encryption 802.1AE for 1-100GE WAN) - phase 8: https://www.cisco.com/c/dam/en/us/td/docs/solutions/Enterprise/Security/MACsec/WP-High-Speed-WAN-Encrypt-MACsec.pdf
14. Cisco zero trust architecture white papers - phase 8: Zero Trust at Scale, https://www.cisco.com/c/dam/en/us/products/collateral/security/zero-trust-at-scale.pdf and the Zero Trust Architectural Framework whitepaper (document 218443), https://www.cisco.com/c/en/us/support/docs/security-vpn/security-vpn/218443-verify-zero-trust-security-whitepaper.html
15. Cisco IOS XE Model-Driven Telemetry white paper - phase 9: https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9300-series-switches/model-driven-telemetry-wp.html
16. Catalyst Programmability and Automation white paper (IOS XE) - phase 10: https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9300-series-switches/catalyst-programmability-automation-wp.html
17. Catalyst Center data sheet and Cisco Catalyst Assurance User Guide - phase 9: https://www.cisco.com/c/en/us/products/collateral/cloud-systems-management/dna-center/nb-06-dna-center-data-sheet-cte-en.html and https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center-assurance/2-3-7/b_cisco_catalyst_assurance_2_3_7_ug.html

Classic Cisco TAC technical documents (linked directly; document IDs are stable search terms if a path changes):

18. OSPF Design Guide, document 7039 - phase 2: https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/7039-1.html
19. BGP Case Studies, document 26634 - phase 3: https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/26634-bgp-toc.html
20. BGP Best Path Selection Algorithm, document 13753 - phase 3: https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html
21. Understanding Rapid Spanning Tree Protocol (802.1w), document 24062 - phase 1: https://www.cisco.com/c/en/us/support/docs/lan-switching/spanning-tree-protocol/24062-146.html
22. Understanding Multiple Spanning Tree Protocol (802.1s), document 24248 - phase 1: https://www.cisco.com/c/en/us/support/docs/lan-switching/spanning-tree-protocol/24248-147.html
23. Network Time Protocol: Best Practices White Paper, document 19643 - phase 5: https://www.cisco.com/c/en/us/support/docs/availability/high-availability/19643-ntpm.html
24. Cisco Guide to Harden Cisco IOS Devices (includes CoPP best practices), document 13608 - phase 8: https://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html

### RFCs and IEEE standards

_Primary standards worth at least a concepts-level read; each RFC is linked directly below via the RFC Editor._

- RFC 2328, OSPF Version 2 - phase 2: https://www.rfc-editor.org/rfc/rfc2328
- RFC 5340, OSPF for IPv6 - phase 2: https://www.rfc-editor.org/rfc/rfc5340
- RFC 4271, BGP-4 - phase 3: https://www.rfc-editor.org/rfc/rfc4271
- RFC 3376, IGMPv3 - phase 4: https://www.rfc-editor.org/rfc/rfc3376
- RFC 7761, PIM Sparse Mode - phase 4: https://www.rfc-editor.org/rfc/rfc7761
- RFC 4594, DiffServ service class guidelines - phase 4: https://www.rfc-editor.org/rfc/rfc4594
- RFC 5905, NTPv4 - phase 5: https://www.rfc-editor.org/rfc/rfc5905
- RFC 5798, VRRPv3 - phase 5: https://www.rfc-editor.org/rfc/rfc5798
- RFC 2784, GRE - phase 6: https://www.rfc-editor.org/rfc/rfc2784
- RFC 7348, VXLAN - phase 6: https://www.rfc-editor.org/rfc/rfc7348
- RFC 9300 and 9301, LISP architecture and control plane - phase 6: https://www.rfc-editor.org/rfc/rfc9300 and https://www.rfc-editor.org/rfc/rfc9301
- RFC 6241, NETCONF - phases 9-10: https://www.rfc-editor.org/rfc/rfc6241
- RFC 8040, RESTCONF - phases 9-10: https://www.rfc-editor.org/rfc/rfc8040
- RFC 7950, YANG 1.1 - phase 10: https://www.rfc-editor.org/rfc/rfc7950
- IEEE 802.1D, 802.1w, 802.1s, 802.1Q, 802.3ad/802.1AX - phase 1: on IEEE Xplore, https://ieeexplore.ieee.org (802 series free via the IEEE GET Program)
- IEEE 802.1AE, MACsec - phase 8: on IEEE Xplore, https://ieeexplore.ieee.org

### Communities and podcasts

- Cisco Learning Network Enterprise certifications community: active study groups and the first place exam changes get discussed: https://learningnetwork.cisco.com/s/topic/0TO3i0000008jYIGAY/enterprise-certifications-community
- r/ccnp: candid pass/fail write-ups and resource reviews: https://www.reddit.com/r/ccnp/
- Packet Pushers, Heavy Networking: design-level discussion that makes the architecture domain concrete: https://packetpushers.net
- The Art of Network Engineering: career and certification interviews, good motivation fuel: https://artofnetworkengineering.com

## Week-by-week schedule

_The default 18-week track at 10-12 hours per week; weeks 19-20 are buffer._

| Week | Focus                                                           | Milestone at week end                                    |
| ---- | --------------------------------------------------------------- | -------------------------------------------------------- |
| 0    | Phase 0: blueprint, gap check, lab build                        | Topology boots; blueprint checklist created              |
| 1    | Forwarding internals, VLANs, STP fundamentals                   | Can explain CEF vs process switching unprompted          |
| 2    | RSTP, MST, STP guards, EtherChannel                             | All STP failure labs documented                          |
| 3    | Routing essentials, EIGRP concepts, OSPF core                   | Multi-area OSPF up with clean adjacencies                |
| 4    | Advanced OSPF, OSPFv3                                           | Four adjacency-failure modes diagnosed cold              |
| 5    | BGP and best-path selection                                     | Best-path order recited and proven in lab                |
| 6    | Multicast, QoS                                                  | PIM-SM lab documented; MQC policy verified               |
| 7    | NTP, NAT, FHRPs                                                 | HSRP tracking failover measured                          |
| 8    | Device virtualization, VRF-lite, GRE, IPsec                     | GRE-over-IPsec captured and annotated                    |
| 9    | LISP, VXLAN                                                     | Map-and-encap explained in own words in vault            |
| 10   | Campus design, HA, cloud, SD-Access                             | SDA fabric roles mapped to LISP/VXLAN/SGT knowledge      |
| 11   | Catalyst SD-WAN                                                 | Every controller role identified live in sandbox         |
| 12   | AAA, ACLs, CoPP, REST API security                              | CoPP policy built and verified                           |
| 13   | TrustSec, MACsec, security portfolio, zero trust                | Portfolio table (product, function, old name) done       |
| 14   | Assurance: syslog, SNMP, NetFlow, SPAN, IP SLA, Catalyst Center | FNF and IP-SLA-to-FHRP labs done                         |
| 15   | Python/JSON, YANG, NETCONF/RESTCONF hands-on                    | First successful RESTCONF PATCH                          |
| 16   | Catalyst Center and SD-WAN Manager APIs, EEM, orchestration     | Token auth plus inventory pull via API; EEM applet fires |
| 17   | Review: blueprint audit, OCG key topics, domain quizzes         | Drill list built from every sub-4 blueprint line         |
| 18   | Full timed practice exams and weak-area loops                   | Two fresh Boson forms at 85%+; book the exam             |

## Readiness gates

_Do not book until all four hold._

1. Blueprint self-audit: every v1.2 line item rated 4/5 or better.
2. Two consecutive unseen full-length practice exams at 85% or higher under real timing.
3. Lab speed runs (OSPF multi-area, eBGP with policy change, HSRP with tracking, Flexible NetFlow, one RESTCONF call) completed from scratch without references.
4. You can write a one-paragraph vault summary of every domain from memory, including the SD-Access and SD-WAN component roles and the BGP best-path order.

## Exam logistics and final tips

_Mechanics that catch people off guard._

- Register through the Cisco certification portal, which hands off to Pearson VUE; choose a test center or OnVUE online proctoring. If testing online, run the system check days ahead and clear your desk completely.
- Cisco exams do not allow going back to previous questions. Answer, commit, move on; never leave a question blank.
- Budget roughly 70-75 seconds per question against the reported 90-110 questions in 120 minutes, and bank time early on the fast multiple-choice items so sims and drag-and-drops can run long.
- Expect the new naming everywhere: Catalyst Center, Catalyst SD-WAN, SD-WAN Manager. If a practice source still says DNA Center and vManage on every question, it has not been updated for v1.2.
- Score reports break results down by domain; if a retake is ever needed, that breakdown is your new drill list. Retakes carry the full fee and short waiting periods apply.
- Passing ENCOR alone already grants the Specialist certification and starts your 3-year CCIE-qualification clock; plan the concentration exam (ENARSI for most people) within a few months while the core knowledge is fresh.

## Folding this into the vault

_Keeping the notes consistent with the rest of the reference vault._

A split that has worked well for this material is one note per phase pillar rather than one monolith: encor-switching, encor-ospf, encor-bgp, encor-multicast-qos, encor-ip-services, encor-overlays, encor-sda-sdwan, encor-security, encor-assurance, encor-automation, plus this plan as the index note linking to all of them. Verification output and configs go in bash fences, topologies in plain code fences, and the usual link validation pass after each editing session keeps the cross-note links honest as the set grows. The blueprint self-audit table can live at the top of the index note and double as the progress tracker.

> [!note] Every link above was individually verified via web search on 2026-07-03. Two caveats going forward: Cisco revises blueprints and renames products on its own schedule (the exam topics page and the Cisco Learning Network community post announcements first, so recheck both before buying anything and once more in the final month), and deep Cisco collateral URLs occasionally move. If a white-paper link 404s, search the exact title or TAC document ID on cisco.com; for the CVDs, fall back to the Design Zone index at https://www.cisco.com/go/cvd