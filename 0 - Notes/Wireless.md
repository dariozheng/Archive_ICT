---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - category/networking/networking_general
icon: FasNetworkWired
iconColor:
last_update:
---
Enterprise wireless networking replaces the standalone access point with a controller-based design, where a central Wireless LAN Controller (WLC) manages a fleet of lightweight access points (APs) as a single system. Rather than configuring each AP by hand, an administrator defines wireless policy once on the controller and pushes it to every AP that matches. This note covers the Cisco enterprise model built around the Catalyst 9800 controller: how the AP and controller divide responsibility, how they communicate over CAPWAP, how APs forward client traffic, and how the controller manages radio frequency, roaming, and security across the whole deployment.

## Split-MAC Architecture

_The division of 802.11 MAC-layer work between the access point and the controller._

A standalone (autonomous) AP handles everything itself: radio transmission, encryption, client association, authentication, and management. The controller-based model divides these responsibilities between the AP and the WLC — hence split-MAC. Work that must happen in real time, within microseconds of a frame arriving, stays on the AP. Work that tolerates a few milliseconds of latency and benefits from central coordination moves to the controller.

### Real-Time vs Management Functions

The AP keeps the time-critical MAC functions:

- Beacon and probe-response transmission
- Frame acknowledgement and retransmission
- Encryption and decryption of 802.11 frames
- Buffering for power-save clients
- Data-rate negotiation with the client

The WLC takes the management MAC functions:

- Association and re-association state
- Client authentication and key management
- RF management (channel and power)
- Roaming coordination between APs
- Security policy and QoS enforcement

```
      Client
        │  802.11
        ▼
  ┌──────────┐   CAPWAP tunnel   ┌───────────────┐
  │    AP    │──────────────────►│      WLC      │
  │ real-time│                   │  management   │
  │   MAC    │◄──────────────────│     MAC       │
  └──────────┘                   └───────────────┘
  ACK · encrypt                  associate · auth
  beacon · retransmit            RF · roam · policy
```

> [!note] Why split the MAC Acknowledging a frame cannot wait for a round trip to the controller, so it stays on the AP. Choosing a channel benefits from a controller that can see every AP at once, so it moves to the WLC. Split-MAC simply puts each job where it belongs.

## CAPWAP

_Control And Provisioning of Wireless Access Points — the tunnel protocol that binds an AP to its controller._

CAPWAP (RFC 5415) is what carries the [[#Split-MAC Architecture|split-MAC]] relationship over the wire. Every lightweight AP builds a CAPWAP tunnel to the WLC, and from that point on all control communication — and, in the default mode, all client data — passes through it. CAPWAP runs over UDP and is the successor to the older LWAPP.

### Control and Data Tunnels

A single CAPWAP association carries two logical channels:

|Channel|UDP port|Purpose|Encryption|
|---|---|---|---|
|Control|5246|Configuration, management, keepalives between AP and WLC|DTLS, always on|
|Data|5247|Encapsulated client traffic|DTLS, optional and off by default|

```
                CAPWAP
   ┌──────┐  control (UDP 5246, DTLS)  ┌──────┐
   │  AP  │═══════════════════════════►│ WLC  │
   │      │  data    (UDP 5247)        │      │
   └──────┘═══════════════════════════►└──────┘
```

> [!info] Where DTLS applies The control channel is always protected with DTLS so configuration and keys cannot be intercepted or altered. Data-channel DTLS can be turned on where client traffic must be encrypted between AP and controller, at the cost of extra CPU on both ends.

### AP Discovery and Join

Before an AP can be managed it must find a controller. It works through a discovery sequence until one answers:

1. Layer 2 broadcast on the local subnet
2. Controllers it has already learned and stored (priming)
3. DHCP option 43, which returns one or more controller management IPs
4. DNS resolution of `CISCO-CAPWAP-CONTROLLER.localdomain`

Once a controller responds, the AP selects one, sets up DTLS, downloads its configuration and — if versions differ — matching firmware, then reaches the [[#AP Join States|Run state]] where it begins serving clients.

### AP Join States

The AP advances through a fixed sequence: Discover, then DTLS setup, then Join, then Image download (only if its firmware does not match the controller), then Config, then Run.

> [!tip] First join after an upgrade is slow An AP whose firmware differs from the controller downloads the correct image during join and reboots. The first join after a controller upgrade therefore takes noticeably longer than a normal one.

## Catalyst 9800 Wireless LAN Controller

_The controller platform, built on IOS-XE, that terminates CAPWAP and applies wireless policy to the AP fleet._

The Catalyst 9800 is Cisco's current-generation controller. It runs the same IOS-XE software as Catalyst switches and routers, replacing the older AireOS controllers. It terminates the CAPWAP tunnels, holds the management MAC functions, runs Radio Resource Management, and enforces security and QoS.

### Form Factors

|Form factor|Role|
|---|---|
|9800-80 / 9800-40|Hardware appliances for large and mid-size campuses|
|9800-L|Smaller hardware appliance for mid-size sites|
|9800-CL|Virtual controller for public cloud or on-prem hypervisors|
|Embedded Wireless Controller (EWC)|Controller function running on a Catalyst 9000 switch or on an AP, for small sites without dedicated hardware|

### The Tag-Based Configuration Model

_The 9800 organizes wireless configuration into reusable profiles grouped by tags, rather than per-AP settings._

This is the defining concept of the 9800. Instead of configuring each AP directly, you define reusable profiles, group them into tags, and assign exactly three tags to every AP. An AP's entire behaviour is the sum of its three tags.

Profiles describe the "what":

|Profile|Defines|
|---|---|
|WLAN Profile|The SSID and its Layer 2 security (WPA, 802.1X, PSK)|
|Policy Profile|Layer 3 handling for that WLAN: VLAN/interface, central or local switching, QoS, ACLs, mobility|
|AP Join Profile|CAPWAP settings, AP credentials, and timers for the AP itself|
|Flex Profile|[[#FlexConnect|
|RF Profile|Per-band RF parameters: data rates, power, channels|

Tags describe the "who and where"; each AP receives one of each:

|Tag|Binds|
|---|---|
|Policy Tag|WLAN Profiles to Policy Profiles — which SSIDs the AP broadcasts and how each is handled|
|Site Tag|The AP Join Profile and Flex Profile — and whether the site is central or FlexConnect|
|RF Tag|The 2.4, 5, and 6 GHz RF Profiles|

```
 WLAN Profile ──┐
                ├──► Policy Tag ──┐
 Policy Profile ┘                 │
                                  │
 AP Join Profile ──┐              ├──► AP
 Flex Profile ─────┴──► Site Tag ─┤
                                  │
 RF Profile 2.4 ──┐               │
 RF Profile 5     ├──► RF Tag ────┘
 RF Profile 6 ────┘
```

A minimal assignment ties the tags to a single AP by its Ethernet MAC:

```cisco
wireless tag policy PT-CAMPUS
 wlan CORP-WLAN policy PP-CENTRAL
!
ap 00aa.00bb.00cc
 policy-tag PT-CAMPUS
 site-tag  ST-CAMPUS
 rf-tag    RT-DEFAULT
```

> [!note] Defaults cover small sites An AP that joins without explicit assignment receives the default Policy, Site, and RF tags, so a small deployment can run entirely on defaults. The model scales up by defining custom tags for different buildings, floors, or AP roles.

> [!info] From AireOS to IOS-XE Older controllers such as the 5520 and 3504 used WLANs, AP groups, RF profiles, and FlexConnect groups. The 9800's profiles and tags cover the same ground with a more modular structure and share IOS-XE with the wired network.

## Access Point Modes

_The operational role an AP plays, which also determines where client traffic is switched._

An AP's mode sets what the AP does and, importantly, whether client data is tunnelled back to the controller or dropped straight onto the local wired network at the AP.

### Local Mode

The default mode. Client traffic is tunnelled through CAPWAP to the controller and switched there — central switching. All policy, VLANs, and security are applied at the controller. This suits campus deployments where APs and controller share a low-latency LAN.

### FlexConnect

Designed for branch sites where the controller sits across a WAN. The AP can switch client traffic locally onto branch VLANs instead of tunnelling every frame back to a distant controller — local switching. It can also authenticate clients locally if the WAN link to the controller (and therefore to the RADIUS server) goes down.

| Aspect | [[#Local Mode|Local mode]] | FlexConnect | |---|---|---| | Data path | Central (CAPWAP to WLC) | Local (branch switch) | | Controller location | Same LAN | Across a WAN | | If the WAN link fails | AP stops serving clients | Continues serving known clients | | Client-handling config | Policy Profile | Flex Profile |

```
LOCAL MODE  (central switching)
  Client ── AP ══ CAPWAP data ══► WLC ──► Campus VLANs

FLEXCONNECT (local switching)
  Client ── AP ──► Branch switch ──► Branch VLANs
                └─ CAPWAP control ─► WLC  (policy only)
```

### Other Modes

|Mode|Purpose|
|---|---|
|Monitor|No client service; dedicated to scanning for rogues, interference, and location|
|Sniffer|Captures 802.11 frames and forwards them to a packet analyzer|
|Bridge / Flex+Bridge|Mesh backhaul between APs where cabling is impractical|
|Sensor|Runs synthetic tests for Catalyst Center assurance|

> [!note] Central versus local switching is the real choice Local mode keeps all traffic and policy in one place, which simplifies enforcement. FlexConnect trades some central control for WAN efficiency and branch survivability. Everything else about a mode follows from where its traffic is switched.

## RF Fundamentals

_The radio-frequency basics the controller must manage: bands, channels, and reuse._

Wireless is a shared medium — every AP and client within range competes for the same air. Sound RF design is what separates a fast wireless network from a slow one, and on the 9800 the controller automates most of it.

### Bands and Channels

|Band|Character|
|---|---|
|2.4 GHz|Long range and good wall penetration, but crowded, and only three non-overlapping 20 MHz channels (1, 6, 11). Kept mainly for legacy clients.|
|5 GHz|Many more non-overlapping channels and less interference, at shorter range. The workhorse band for capacity.|
|6 GHz|Large amount of new spectrum for Wi-Fi 6E and Wi-Fi 7, wide channels, little legacy interference; requires WPA3 and newer clients.|

### Channel Width and Reuse

Wider channels (40, 80, or 160 MHz) raise throughput but consume more spectrum and increase the chance of overlap. In dense deployments, narrower channels allow more non-overlapping cells, which is what channel reuse depends on. Neighbouring APs must sit on different channels to avoid co-channel interference, where two cells on the same channel are forced to take turns transmitting.

> [!warning] 2.4 GHz fills up fast With only three non-overlapping channels, any dense 2.4 GHz deployment suffers co-channel interference. Many designs disable the 2.4 GHz radio on a share of APs and rely on 5 and 6 GHz for capacity.

## Radio Resource Management

_The controller's automatic tuning of channel, power, and coverage across the whole AP fleet._

Radio Resource Management (RRM) is the set of algorithms the WLC runs to keep the RF environment healthy without manual channel planning. APs continuously measure the air and report to the controller, which then adjusts settings across the deployment.

### RF Groups

_A set of controllers that pool RRM information and tune as one RF domain._

Controllers covering the same physical space join an RF group so their APs are managed as a single RF domain. One controller is elected RF group leader and runs the RRM calculations for the entire group, so that channel and power decisions account for every AP that can hear every other AP — even across controllers.

### Dynamic Channel Assignment

DCA chooses the channel for each radio, steering neighbouring APs onto different channels to minimize interference. It reacts to new interference sources and to APs joining or leaving the [[#RF Groups|RF group]].

### Transmit Power Control

TPC sets each radio's transmit power. Where APs are dense it lowers power so cells do not bleed into one another; where coverage is sparse it raises power. The aim is cells that just touch rather than heavily overlap.

### Coverage Hole Detection

By watching the signal quality that clients report, the controller detects areas where coverage has become too weak — a coverage hole — and can raise nearby AP power to fill the gap.

### Flexible Radio Assignment

On dual-band radios, FRA lets the controller decide whether a flexible radio serves 2.4 GHz, adds a second 5 GHz radio for capacity, or monitors the air, automatically balancing coverage against capacity.

> [!tip] Let RRM see the whole picture RRM assumes it can observe every AP in the domain. Pinning a few APs to fixed channels or power, or leaving isolated APs out of the RF group, undermines the algorithm for their neighbours too.

## Client Roaming and Mobility

_How a client moves between APs while keeping its session, and how controllers coordinate the handoff._

Roaming is always initiated by the client — it decides when a neighbouring AP looks better and re-associates to it. The infrastructure's job is to make that handoff fast and to preserve the client's IP address and authentication state across it. On the 9800, controllers coordinate this through [[#Mobility Groups and Domains|mobility groups]].

### Mobility Groups and Domains

_Controllers that share client and roaming context so a session survives a move between them._

Controllers configured with each other's addresses and a shared group name form a mobility group. Within it, they exchange client state, so a client roaming from an AP on one controller to an AP on another is recognized as an existing session rather than treated as brand new. A mobility domain can span several mobility groups for larger designs.

### Intra-Controller Roaming

When a client moves between two APs joined to the same controller, that controller already holds its full context. The handoff is trivial: the client keeps its IP address and keys with no inter-controller signalling at all.

### Inter-Controller Roaming

When the two APs belong to different controllers in the same mobility group, the original controller and the new one coordinate the move. If both place the client in the same VLAN and subnet, this is a Layer 2 roam, and the new controller simply takes over serving the client.

### Layer 3 Roaming

If the two controllers place the client in different subnets, changing its IP would break the session. Instead they build an anchor-and-foreign tunnel: the client stays anchored to its original controller for IP purposes while the foreign controller handles the radio. Traffic tunnels back to the anchor, so the client keeps its original address.

```
Client roams:   AP1 (WLC-A)  ─────►  AP2 (WLC-B)

 Layer 2 roam  same subnet      → WLC-B serves the client directly
 Layer 3 roam  different subnet →
     client keeps its IP from WLC-A          (anchor)
     WLC-B ══ mobility tunnel ══► WLC-A ──► original subnet
     (foreign)
```

### Fast and Assisted Roaming

Re-authenticating from scratch at every roam adds delay that hurts voice and video. Several 802.11 amendments cut it down:

|Amendment|What it does|
|---|---|
|802.11r (Fast Transition)|Pre-establishes keys so the client skips most of the 802.1X exchange when it roams|
|802.11k (Neighbor Reports)|The AP hands the client a list of nearby APs and channels, so it need not scan blindly|
|802.11v (BSS Transition Management)|Lets the infrastructure suggest a better AP to the client|
|OKC / CCKM|Earlier opportunistic and Cisco key-caching schemes with a goal similar to 11r|

> [!important] Roaming is hardest for voice Wireless voice, and increasingly video, is the demanding case. Without fast roaming (11r) and assisted roaming (11k and 11v), a call can drop or stutter each time the user walks between cells, because a full re-authentication takes too long to complete mid-call.

## Guest Access

_Isolating visitor traffic and steering it to a controlled entry point, usually in a DMZ._

Guest wireless carries untrusted users and must be kept away from internal resources. The common enterprise pattern combines auto-anchor mobility with web authentication.

### Auto-Anchor Guest Tunneling

All guest traffic from the campus controllers is tunnelled to a dedicated [[#Layer 3 Roaming|anchor]] controller in the DMZ, regardless of which AP the guest joined. Guests never touch internal VLANs; their traffic surfaces only at the DMZ, where a firewall enforces internet-only access.

### Web Authentication

Guests land behind a captive portal — a web page that requires accepting terms, entering a sponsor-provided credential, or self-registering. Until a guest passes web authentication their access is restricted. The portal can be hosted on the controller itself or on an external server.

## Wireless Security

_How wireless clients are authenticated and how their traffic is encrypted over the air._

Because the medium is open air, wireless security has to do two jobs: authenticate who may join, and encrypt what they send. Modern enterprise wireless builds both on the WPA2 and WPA3 framework.

### WPA2 and WPA3

|Standard|Properties|
|---|---|
|WPA2|Long-standing standard using AES-CCMP encryption; still widespread|
|WPA3|Current standard: stronger encryption, mandatory protected management frames (PMF), and SAE replacing the PSK handshake to resist offline password guessing|
|Enhanced Open (OWE)|Encrypts traffic on otherwise open networks, such as guest SSIDs, without a password|

### Personal vs Enterprise

|Model|How clients authenticate|
|---|---|
|Personal (PSK / SAE)|A single pre-shared key or passphrase for the SSID; simple, and suited to small or IoT networks|
|[[#802.1X and the WLC as Authenticator|Enterprise]] (802.1X/EAP)|

### 802.1X and the WLC as Authenticator

On an enterprise SSID the WLC plays the authenticator role in 802.1X: it relays EAP between the wireless client (the supplicant) and a RADIUS server such as Cisco ISE, then enforces the VLAN, ACL, or security-group tag that the server returns. In this role the controller is itself a [[PBA - NAC - Network Access Devices|network access device]] on the wired NAC side — the same policy engine that governs switch ports governs wireless clients.

```
 Wireless client ── EAP over 802.11 ──► WLC ── RADIUS ──► ISE
   (supplicant)                    (authenticator)     (server)
                                         │
                          enforces VLAN · ACL · SGT result
```

> [!note] One identity model, wired and wireless Because the WLC forwards to the same RADIUS infrastructure as the switches, an organization can run one identity and policy model across wired and wireless access instead of maintaining two.

## High Availability

_Keeping the controller — a single point of failure for every AP it serves — continuously available._

Every AP depends on its controller, so controller redundancy is essential in production. The 9800 offers two complementary approaches.

### SSO and HA Pairs

Two 9800 controllers can run as a Stateful Switchover (SSO) pair: one active and one hot standby, sharing AP and client state over a redundancy link. If the active fails, the standby takes over with APs and clients staying up — sub-second failover and no re-join.

### N+1 Redundancy

Alternatively, each AP is configured with a primary, secondary, and tertiary controller. If the primary fails, the AP re-joins a backup controller. This is cheaper and more flexible across sites than an SSO pair, but it involves a brief AP re-join rather than seamless failover.

> [!tip] Combine both approaches Large designs often pair SSO within a site, for seamless local failover, with N+1 across sites, for disaster fallback — so that neither a single controller failure nor a whole-site outage takes wireless down.