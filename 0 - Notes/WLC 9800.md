---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[WLAN]]"
tags:
  - cisco
  - tech_doc
  - networking
  - PBA
icon: SiCisco
iconColor: "#1BA0D7"
---
- Hardware
- Product ID 
- Serial Number
- Licenses

![[Screenshot 2026-06-23 at 16.14.37.png]]

### Access & Credentials

GUI Portal 
- https://10.140.1.10/webui/#/acl
- https://pba-wlc01.publiacqua.it/webui/
SSH
- Host: 10.140.1.10 / Port: 22
- Host: pba-wlc01 / Port: 22

Credentials
- RADIUS credentials
# Cisco WLC 9800

The Catalyst 9800 Wireless LAN Controller runs IOS-XE and introduces a fundamentally different configuration model compared to older AireOS platforms. The controller does not bind SSIDs directly to access points. Instead, independent profiles for radio settings, AP behavior, client policy, and WLAN definitions are assembled into tags, and those tags are assigned to APs.

Every piece of wireless configuration flows through this tag and profile hierarchy. Understanding it completely before touching anything else is what separates a working deployment from one that takes hours to debug.

---

# Architecture

## Tag and Profile Model

The 9800 configuration is built in two layers. The first layer is profiles, which are self-contained units of configuration for a specific concern. The second layer is tags, which are lightweight containers that reference profiles and are assigned to APs.

When an AP joins the controller and receives its three tags, it reads all the profiles referenced by those tags and derives its full operating configuration from them.

## Tag Types

There are three tag types and every AP must have all three assigned.

The Policy Tag maps WLAN definitions to Policy Profiles. It controls what SSIDs the AP broadcasts and how client traffic for each SSID is handled.

The Site Tag references an AP Join Profile and a Flex Profile. It governs how the AP joins the controller, its operational mode (local vs FlexConnect), and site-specific parameters.

The RF Tag references up to three RF Profiles, one per band (2.4 GHz, 5 GHz, 6 GHz). It controls channel, power, and radio resource management behavior.

## Profile Types

|Profile|Tag it belongs to|What it controls|
|---|---|---|
|AP Join Profile|Site Tag|CAPWAP behavior, AP credentials, syslog, NTP|
|Flex Profile|Site Tag|FlexConnect VLAN mapping, local switching|
|RF Profile|RF Tag|Channel, TX power, data rates, RRM|
|WLAN|Policy Tag|SSID name, L2 security (WPA2/WPA3, PSK, 802.1X)|
|Policy Profile|Policy Tag|VLAN, QoS, session timeout, ACLs, accounting|

## Default Tag Behavior

Any AP that joins without an explicit tag assignment receives the three built-in default tags. The default configuration uses local mode with no VLAN mapping. It works for lab testing but should be replaced in production deployments where explicit control over tagging is required.

---

# Initial Setup

## Accessing the Controller

### Web UI

After initial IP assignment, the management interface is reachable on HTTPS port 443. The Day 0 wizard launches automatically on first boot.

### CLI

```
ssh admin@<management-ip>
```

The console port is available on hardware appliances. Serial settings are 9600 baud, 8 data bits, no parity, 1 stop bit.

## Day 0 Wizard

The wizard covers hostname, management IP, default gateway, NTP, admin password, country code, and wireless regulatory domain. Running the wizard is the fastest path to a functional baseline. The wizard can be bypassed and all the same settings applied manually from CLI.

## Base System Configuration

### Hostname

```
hostname WLC-9800
```

### Domain and DNS

```
ip domain name example.local
ip name-server 192.168.1.53
```

### NTP

At least two NTP servers should be configured. Certificate validation, logging timestamps, and some RADIUS functions depend on accurate time.

```
ntp server 192.168.1.1
ntp server 192.168.1.2
```

### Timezone

```
clock timezone CET 1 0
clock summer-time CEST recurring last Sun Mar 2:00 last Sun Oct 3:00
```

### SSH Hardening

```
ip ssh version 2
ip ssh authentication-retries 3
ip ssh time-out 60
crypto key generate rsa modulus 4096
```

---

# Network Connectivity

## Management Interface

The management IP is the address the controller uses for administration traffic, CAPWAP AP tunnels, and outbound RADIUS communication. On hardware appliances it is typically assigned to GigabitEthernet0.

```
interface GigabitEthernet0
 ip address 192.168.1.10 255.255.255.0
 no shutdown

ip route 0.0.0.0 0.0.0.0 192.168.1.1
```

## Trunk Uplink

In local (centralized) mode the controller bridges all client traffic to its uplink. The uplink must be a trunk carrying every VLAN referenced by any Policy Profile.

```
interface GigabitEthernet1
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30,100
 switchport trunk native vlan 1
 no shutdown
```

## SVIs for Local Switching

When the controller itself does the inter-VLAN routing or hosts DHCP, SVIs are needed.

```
interface Vlan10
 ip address 10.10.10.1 255.255.255.0
 ip helper-address 192.168.1.70
 no shutdown

interface Vlan20
 ip address 10.10.20.1 255.255.255.0
 ip helper-address 192.168.1.70
 no shutdown
```

---

# Licensing

## Smart Licensing

The 9800 uses Cisco Smart Licensing with Usage Reporting (SLUR). The controller must register with Cisco Smart Software Manager (CSSM) or a local on-premises CSSM satellite. Without registration it enters a 90-day evaluation period, after which unlicensed features may be restricted.

```
license smart transport callhome

service call-home
call-home
 contact-email-addr admin@example.local
 profile CiscoTAC-1
  active
  destination transport-method http
```

## AP License Tiers

Each AP consumes one license. The tier level determines available features.

Essentials covers basic CAPWAP, WPA2/WPA3, and standard RRM.

Advantage adds FlexConnect enhancements, Cisco CleanAir, Application Visibility and Control (AVC), and mDNS gateway.

Premier adds Hyperlocation, advanced analytics, and Cisco DNA Spaces integration.

The license tier applied to the controller determines which features are available globally. Per-WLAN or per-policy-profile overrides for AVC, QoS, and analytics require the appropriate tier.

---

# Certificates

Managing certificates early avoids AP join failures and browser warnings throughout the rest of the deployment.

## Self-Signed Certificate

The controller generates a self-signed certificate on first boot. Browsers will warn on the management interface and APs with strict certificate validation may refuse to join using Locally Significant Certificates (LSC) enrollment.

## Generating a CSR and Installing a CA Certificate

Create a trustpoint and generate the keypair:

```
crypto key generate rsa label WLC-KEY modulus 2048

crypto pki trustpoint WLC-CERT
 enrollment terminal
 subject-name CN=wlc.example.local,OU=IT,O=Example,C=IT
 subject-alt-name wlc.example.local
 revocation-check none
 rsakeypair WLC-KEY
```

Generate and copy the CSR:

```
crypto pki enroll WLC-CERT
```

After the CA returns the signed certificate, import it:

```
crypto pki import WLC-CERT certificate
```

Assign the certificate to the HTTPS management server:

```
ip http secure-trustpoint WLC-CERT
```

## LSC (Locally Significant Certificates) for APs

LSC allows APs to use a CA-signed certificate instead of the factory MIC. Configure the CA details in the AP Join Profile:

```
ap profile CORP-AP-PROFILE
 lsc-only-auth
 certificate-authority trustpoint WLC-CERT
```

Provision LSC to the APs before enabling LSC-only mode. APs without a valid LSC will fail to join after that change.

---

# RF Profiles

RF Profiles define per-radio behavior for groups of APs. A separate profile is created for each band.

## Creating an RF Profile for 5 GHz

```
ap dot11 5ghz rf-profile CORP-5GHz
 description "Corporate 5GHz Profile"
 channel width 80
 coverage data fail-percentage 20
 coverage data rssi-threshold -80
 coverage exception global 25
 coverage min-client-level 3
 load-balancing window 5
 no shutdown
```

## Creating an RF Profile for 2.4 GHz

```
ap dot11 24ghz rf-profile CORP-2.4GHz
 description "Corporate 2.4GHz Profile"
 channel width 20
 coverage data fail-percentage 20
 coverage data rssi-threshold -80
 no shutdown
```

## Data Rate Optimization

Disabling low data rates reduces airtime waste from legacy frames and management overhead. Clients on older 802.11b/g rates are steered toward faster rates or disassociated.

```
ap dot11 5ghz rf-profile CORP-5GHz
 rate RATE_6M disable
 rate RATE_9M disable
 rate RATE_12M mandatory
 rate RATE_18M supported
 rate RATE_24M supported
 rate RATE_36M supported
 rate RATE_48M supported
 rate RATE_54M supported
```

For 2.4 GHz, disabling 802.11b rates (1, 2, 5.5, 11 Mbps) prevents legacy clients from associating:

```
ap dot11 24ghz rf-profile CORP-2.4GHz
 rate RATE_1M disable
 rate RATE_2M disable
 rate RATE_5_5M disable
 rate RATE_11M disable
 rate RATE_12M mandatory
```

## Band Steering

Band steering nudges dual-band clients toward 5 GHz by delaying probe responses on the 2.4 GHz radio.

```
ap dot11 5ghz rf-profile CORP-5GHz
 band-select probe-response
 band-select cycle-count 2
 band-select cycle-threshold 200
 band-select expire suppression 20
```

---

# AP Join Profiles

The AP Join Profile defines operational parameters for APs after they join the controller.

## Creating an AP Join Profile

```
ap profile CORP-AP-PROFILE
 description "Corporate AP Join Profile"
 capwap retransmit count 3
 capwap retransmit interval 3
 mgmtuser username apmanager password 0 <password> secret 0 <secret>
 ntp ip 192.168.1.1
 syslog host 192.168.1.100
 statistics ap-system-logging enable
 no shutdown
```

## Per-AP Profile Parameters

The AP join profile also controls the following behaviors on a per-AP basis:

- LLDP and CDP advertisement on the AP wired port
- LED state (normal, off, always-on)
- AP crash file upload destination
- Hyperlocation BLE beacon interval
- AP console access credentials separate from the management user

---

# Flex Profiles

Flex Profiles are used exclusively with APs in FlexConnect mode. They define VLAN mappings so the AP can switch client traffic locally to the correct VLAN without tunneling back to the controller.

## Creating a Flex Profile

```
wireless profile flex BRANCH-FLEX-PROFILE
 description "Branch FlexConnect Profile"
 native-vlan 10
 vlan 20
 vlan 30
```

## WLAN to VLAN Mapping in FlexConnect

In FlexConnect the local VLAN assignment for a WLAN can be overridden in the Flex Profile on a per-SSID basis. This allows the same policy profile VLAN to be mapped to different local VLANs at different branch sites.

```
wireless profile flex BRANCH-FLEX-PROFILE
 wlan CORP-WLAN vlan 20
 wlan GUEST-WLAN vlan 30
```

---

# Site Tags

The Site Tag binds an AP Join Profile and optionally a Flex Profile. It also sets whether APs operate in local (centralized) mode or FlexConnect mode.

## Local Mode Site Tag

In local mode all client traffic is tunneled to the controller via CAPWAP. The Site Tag references only the AP Join Profile.

```
wireless tag site CORP-SITE-TAG
 description "Corporate Local Mode"
 ap-profile CORP-AP-PROFILE
 local-site
```

## FlexConnect Mode Site Tag

Removing `local-site` switches the AP to FlexConnect mode. A Flex Profile must be referenced.

```
wireless tag site BRANCH-SITE-TAG
 description "Branch FlexConnect"
 ap-profile CORP-AP-PROFILE
 flex-profile BRANCH-FLEX-PROFILE
 no local-site
```

---

# RF Tags

The RF Tag references up to three RF Profiles and is the only way to assign band-specific radio behavior to a group of APs.

## Creating an RF Tag

```
wireless tag rf CORP-RF-TAG
 description "Corporate RF Tag"
 24ghz-rf-policy CORP-2.4GHz
 5ghz-rf-policy CORP-5GHz
```

For controllers and APs supporting 6 GHz (Wi-Fi 6E):

```
wireless tag rf CORP-RF-TAG
 6ghz-rf-policy CORP-6GHz
```

---

# WLANs

A WLAN defines an SSID and its Layer 2 security parameters. VLAN assignment and client policy are handled separately in the Policy Profile. A WLAN does nothing until it is referenced inside a Policy Tag.

## Creating a WLAN

```
wlan CORP-WLAN 1 CORP-SSID
 description "Corporate Internal SSID"
 no shutdown
```

The first argument is the WLAN name used in the controller configuration. The integer (1) is the WLAN ID, a local identifier. The last argument is the actual SSID string broadcast to clients.

## Security Modes

### WPA2 Personal (PSK)

```
wlan PSK-WLAN 2 PSK-SSID
 security wpa wpa2
 security wpa wpa2 ciphers aes
 security wpa akm psk
 security wpa akm psk set-key ascii 0 YourPreSharedKey
 no security wpa akm dot1x
 no shutdown
```

### WPA2 Enterprise (802.1X)

```
wlan DOT1X-WLAN 3 CORP-DOT1X
 security wpa wpa2
 security wpa wpa2 ciphers aes
 security wpa akm dot1x
 no security wpa akm psk
 no shutdown
```

### WPA3 Personal (SAE)

SAE replaces PSK and prevents offline dictionary attacks.

```
wlan WPA3-WLAN 4 SECURE-SSID
 security wpa wpa3
 security wpa akm sae
 security wpa akm sae pwe h2e
 no security wpa akm psk
 no shutdown
```

### WPA3 Enterprise (192-bit mode)

```
wlan WPA3-ENT-WLAN 5 SECURE-ENT
 security wpa wpa3
 security wpa akm dot1x-sha256
 no security wpa akm dot1x
 no shutdown
```

### OWE (Opportunistic Wireless Encryption)

OWE provides encryption on open networks without a passphrase. Suitable for guest SSIDs where a shared PSK is not desired.

```
wlan OWE-WLAN 6 OPEN-ENCRYPTED
 security wpa wpa3
 security wpa akm owe
 no security wpa akm psk
 no shutdown
```

### Open (Captive Portal / Guest)

An entirely open WLAN for captive portal redirect workflows. Authentication is handled in the Policy Profile via web redirect.

```
wlan GUEST-WLAN 7 GUEST-SSID
 no security wpa
 no security wpa wpa2
 no security wpa akm dot1x
 no security wpa akm psk
 no shutdown
```

## WLAN Advanced Settings

### Band Restriction

Restricting a WLAN to 5 GHz only prevents dual-band association at the 2.4 GHz radio. This reduces co-channel interference and steers capable clients to the better band.

```
wlan CORP-WLAN 1 CORP-SSID
 radio policy dot11 5ghz
```

### 802.11r Fast Transition (FT)

Fast BSS Transition accelerates roaming by reducing the number of round trips required for re-authentication.

```
wlan CORP-WLAN 1 CORP-SSID
 security ft
 security ft over-the-ds
 security ft reassociation-timeout 20
```

### 802.11k and 802.11v

These protocols allow APs and clients to exchange neighbor and load information for assisted roaming.

```
wlan CORP-WLAN 1 CORP-SSID
 bss-transition
 dot11k enable
```

### WMM and DTIM

WMM (Wi-Fi Multimedia) is required for QoS. DTIM (Delivery Traffic Indication Message) interval affects power save behavior.

```
wlan CORP-WLAN 1 CORP-SSID
 wmm require
 dtim dot11 5ghz 1
 dtim dot11 24ghz 2
```

---

# Policy Profiles

The Policy Profile defines what happens to client traffic after authentication. This is where VLAN assignment, QoS, timeouts, and accounting are configured.

## Creating a Policy Profile

```
wireless profile policy CORP-POLICY-PROFILE
 description "Corporate Client Policy"
 vlan 10
 session-timeout 28800
 idle-timeout 300
 accounting-list RADIUS-ACCT
 no shutdown
```

## Switching Mode

### Central (Local) Switching

In central mode the controller handles all client frame switching. The traffic is tunneled from the AP to the controller via CAPWAP and then forwarded to the VLAN.

```
wireless profile policy CORP-POLICY-PROFILE
 central association
 central dhcp
 central switching
```

### FlexConnect Local Switching

In FlexConnect mode the AP switches traffic locally. The CAPWAP control tunnel remains up but data is forwarded at the AP site.

```
wireless profile policy BRANCH-POLICY-PROFILE
 no central association
 no central dhcp
 no central switching
 vlan 20
```

## QoS

The four available QoS profiles map to 802.11e access categories:

- platinum maps to voice (AC_VO)
- gold maps to video (AC_VI)
- silver maps to best effort (AC_BE)
- bronze maps to background (AC_BK)

```
wireless profile policy VOIP-POLICY-PROFILE
 upstream qos-profile platinum
 downstream qos-profile platinum
```

## Client Exclusion

```
wireless profile policy CORP-POLICY-PROFILE
 exclusionlist
 exclusionlist timeout 60
```

After the configured number of consecutive authentication failures, the client MAC is excluded for the timeout period. This protects against brute force attempts.

## IPv6 Support

```
wireless profile policy CORP-POLICY-PROFILE
 ipv6 nd proxy disable
```

## mDNS Policy

For service discovery (Apple Bonjour, AirPlay, Chromecast) the controller can proxy mDNS between VLANs.

```
wireless profile policy CORP-POLICY-PROFILE
 mdns-sd
```

---

# Policy Tags

The Policy Tag is the container that links WLAN definitions to Policy Profiles. It is the key binding point of the entire wireless service configuration.

## Creating a Policy Tag

```
wireless tag policy CORP-POLICY-TAG
 description "Corporate Policy Tag"
 wlan CORP-WLAN policy CORP-POLICY-PROFILE
 wlan GUEST-WLAN policy GUEST-POLICY-PROFILE
 wlan VOIP-WLAN policy VOIP-POLICY-PROFILE
```

A single Policy Tag can hold up to 16 WLAN-to-Policy mappings. Every WLAN referenced in the Policy Tag will be broadcast by every AP assigned to that tag.

---

# Assigning Tags to Access Points

## Manual Assignment via CLI

```
ap 1c2b.3d4e.5f6a
 policy-tag CORP-POLICY-TAG
 site-tag CORP-SITE-TAG
 rf-tag CORP-RF-TAG
```

The AP reinitializes its radio after receiving a new tag assignment. Schedule tag changes during a maintenance window in production environments.

## Manual Assignment via Web UI

Navigate to Configuration > Wireless > Access Points, select the AP, expand the Tags section, and assign all three tags. Click Update and Apply to AP.

## Bulk Assignment with AP Filters

AP filters apply tags automatically based on AP name patterns. This is useful for large deployments where APs follow a naming convention.

```
ap filter name CORP-FILTER
 priority 10
 ap-name-regex CORP-AP-.*
 tag policy CORP-POLICY-TAG
 tag site CORP-SITE-TAG
 tag rf CORP-RF-TAG
```

Filters are evaluated in priority order (lower number = higher priority). The first matching filter wins.

---

# AAA and RADIUS

## Configuring RADIUS Servers

```
radius server RADIUS-PRIMARY
 address ipv4 192.168.1.200 auth-port 1812 acct-port 1813
 timeout 5
 retransmit 3
 key 0 RadiusSharedSecret

radius server RADIUS-SECONDARY
 address ipv4 192.168.1.201 auth-port 1812 acct-port 1813
 timeout 5
 retransmit 3
 key 0 RadiusSharedSecret
```

## RADIUS Server Groups

```
aaa group server radius RADIUS-GROUP
 server name RADIUS-PRIMARY
 server name RADIUS-SECONDARY
 deadtime 5
 load-balance method least-outstanding
```

## AAA Method Lists

```
aaa new-model

aaa authentication dot1x DOT1X-AUTH-LIST group RADIUS-GROUP
aaa authorization network DOT1X-AUTHZ-LIST group RADIUS-GROUP
aaa accounting dot1x DOT1X-ACCT-LIST start-stop group RADIUS-GROUP
aaa accounting network RADIUS-ACCT start-stop group RADIUS-GROUP
```

## Linking AAA to a WLAN

The authentication and authorization method lists are bound to the WLAN, not the Policy Profile.

```
wlan CORP-WLAN 1 CORP-SSID
 security dot1x authentication-list DOT1X-AUTH-LIST
 security dot1x authorization-list DOT1X-AUTHZ-LIST
```

## RADIUS CoA (Change of Authorization)

CoA allows the RADIUS server (typically ISE) to dynamically change a client's authorization state after they have already associated. This is required for CWA guest workflows and posture-based policy.

```
aaa server radius dynamic-author
 client 192.168.1.200 server-key RadiusSharedSecret
 client 192.168.1.201 server-key RadiusSharedSecret
 auth-type any
```

---

# Web Authentication

## Local Web Authentication (LWA)

In LWA the controller serves the portal page itself. No external redirect is needed.

```
parameter-map type webauth LOCAL-WEBAUTH
 type webauth
 virtual-ip ipv4 192.0.2.1
 banner text "Welcome to Guest Wi-Fi"
 max-http-conns 100
 timeout init-state sec 120

ip http server
ip http secure-server
```

Bind the parameter map to the Policy Profile:

```
wireless profile policy GUEST-POLICY-PROFILE
 vlan 100
 webauth-parameter LOCAL-WEBAUTH
```

## Central Web Authentication (CWA)

CWA redirects the client browser to an external portal, typically ISE. The client initially receives a restricted ACL and is redirected on first HTTP/HTTPS request.

The workflow is:

1. Client associates to the open WLAN
2. Controller applies the redirect ACL and redirect URL from the initial RADIUS Access-Accept
3. Client opens a browser and is redirected to the ISE guest portal
4. Client authenticates on the portal
5. ISE sends a CoA to the controller granting full access

The WLAN uses MAC filtering as the initial authentication trigger (ISE returns an Access-Accept with redirect attributes):

```
wlan GUEST-WLAN 7 GUEST-SSID
 mac-filtering GUEST-MAC-LIST
 no security wpa
 no shutdown
```

The redirect ACL is configured on the controller and referenced in the RADIUS attributes returned by ISE.

---

# RRM (Radio Resource Management)

RRM runs on the controller and automatically adjusts channel assignment and TX power across all managed APs. It runs on a configurable interval and also responds to event-driven triggers such as radar detection or new AP addition.

## Enabling RRM

RRM is enabled by default. Explicit configuration is usually only needed to restrict the channel list or tune thresholds.

```
ap dot11 5ghz rrm channel
ap dot11 5ghz rrm channel automatic
ap dot11 5ghz rrm txpower automatic
ap dot11 24ghz rrm channel automatic
ap dot11 24ghz rrm txpower automatic
```

## DCA Channel List for 5 GHz

Restricting to non-DFS channels avoids radar-triggered channel changes in environments with frequent radar events:

```
ap dot11 5ghz rrm channel dca chan-width 80
ap dot11 5ghz channel add 36
ap dot11 5ghz channel add 40
ap dot11 5ghz channel add 44
ap dot11 5ghz channel add 48
ap dot11 5ghz channel add 149
ap dot11 5ghz channel add 153
ap dot11 5ghz channel add 157
ap dot11 5ghz channel add 161
```

## DCA Channel List for 2.4 GHz

In 2.4 GHz only channels 1, 6, and 11 are non-overlapping. Restricting to these prevents RRM from selecting partially overlapping channels.

```
ap dot11 24ghz channel add 1
ap dot11 24ghz channel add 6
ap dot11 24ghz channel add 11
```

## Coverage Hole Detection

```
ap dot11 5ghz rrm coverage
ap dot11 5ghz rrm coverage data fail-percentage 20
ap dot11 5ghz rrm coverage data packet-count 50
ap dot11 5ghz rrm coverage data rssi-threshold -80
ap dot11 5ghz rrm coverage exception global 25
ap dot11 5ghz rrm coverage min-client-level 3
```

When the threshold of clients below the RSSI level exceeds the exception percentage, the controller flags a coverage hole. This does not automatically increase TX power; it logs the event and can be used to trigger alerts.

## RRM Interval

```
ap dot11 5ghz rrm channel dca interval 1
ap dot11 5ghz rrm channel dca anchor-time 3
```

The interval is in hours. The anchor-time sets the hour of day when DCA runs. Setting interval to 1 with anchor-time 3 runs DCA once per day at 3:00 AM.

---

# High Availability

## SSO (Stateful Switchover)

The 9800 supports an active/standby HA pair using a dedicated HA link. Client sessions, AP associations, and CAPWAP tunnels are maintained across a failover with no re-authentication required from wireless clients.

### HA Link Configuration

On the active controller:

```
chassis ha-interface GigabitEthernet2
 ip address 10.255.255.1 255.255.255.252
```

On the standby controller:

```
chassis ha-interface GigabitEthernet2
 ip address 10.255.255.2 255.255.255.252
```

### Pairing

From the active controller:

```
chassis ha-pair ip 10.255.255.2 secret PairingSecret123
```

The standby controller reboots, synchronizes configuration, and enters hot standby mode. After synchronization all subsequent configuration changes are automatically replicated.

### Verifying HA State

```
show chassis
show redundancy
show wireless redundancy summary
```

## N+1 and N+N HA

For deployments without a dedicated standby, APs can be configured to fall back to a secondary controller. The priority of each controller is set in the AP Join Profile:

```
ap profile CORP-AP-PROFILE
 primary-base WLC-PRIMARY 192.168.1.10
 secondary-base WLC-SECONDARY 192.168.1.11
```

---

# Mobility

Mobility allows APs managed by multiple controllers to support seamless client roaming across controller boundaries. A mobility group is a set of controllers that trust each other for fast roaming handoffs.

## Configuring a Mobility Group

Each controller must know the mobility MAC and IP of every peer:

```
wireless mobility group name CORP-MOBILITY-GROUP

wireless mobility controller peer-group CORP-PEERS
 member ip 192.168.1.10 public-ip 192.168.1.10 group CORP-PEERS
 member ip 192.168.1.11 public-ip 192.168.1.11 group CORP-PEERS
```

Set the DTLS key for encrypted mobility tunnels:

```
wireless mobility group keepalive interval 10
wireless mobility group keepalive count 3
```

## Verifying Mobility

```
show wireless mobility summary
show wireless mobility peer ip 192.168.1.11
```

---

# Management and Monitoring

## Role-Based Access Control

```
aaa new-model
aaa authentication login VTY-AUTH local
aaa authorization exec VTY-AUTHZ local

username netadmin privilege 15 secret 0 SecurePassword123
username helpdesk privilege 5 secret 0 HelpdeskPass123
```

## SNMP

```
snmp-server community ReadCommunity ro
snmp-server location "Building A - Server Room"
snmp-server contact admin@example.local
snmp-server host 192.168.1.100 version 2c ReadCommunity
snmp-server enable traps wireless
snmp-server enable traps wlan
```

For SNMPv3:

```
snmp-server group SNMP-GROUP v3 priv
snmp-server user snmpuser SNMP-GROUP v3 auth sha AuthPassword priv aes 128 PrivPassword
```

## Syslog

```
logging host 192.168.1.100
logging trap informational
logging origin-id ip
logging facility local6
```

## NETCONF and RESTCONF

The 9800 exposes full programmatic configuration via NETCONF on port 830 and RESTCONF on port 443.

```
netconf-yang
restconf
```

Both use the same local or RADIUS credentials. RESTCONF supports HTTP Basic Auth and token-based authentication. YANG models covering the entire controller configuration are available from Cisco's YANG GitHub repository.

---

# Useful Verification Commands

## System and Licensing

```
show version
show inventory
show license summary
show license udi
show ntp associations
show clock
```

## AP Status and Tags

```
show ap summary
show ap status
show ap tag summary
show ap join stats summary all
show ap config general <ap-name>
show ap tag <ap-name>
```

## WLAN and Policy

```
show wlan summary
show wlan all
show wireless profile policy summary
show wireless tag policy summary
```

## Client Status

```
show wireless client summary
show wireless client detail mac-address <mac-address>
show wireless stats client delete reason
```

## RF and Radio

```
show ap dot11 5ghz summary
show ap dot11 24ghz summary
show rrm summary
show wireless rrm 5ghz status
show wireless rrm 24ghz status
```

## AAA and RADIUS

```
show aaa servers
show aaa method-lists authentication
show radius statistics
show wireless client statistics
```

## High Availability and Mobility

```
show chassis
show redundancy
show wireless redundancy summary
show wireless mobility summary
show wireless mobility peer ip <peer-ip>
```

---

# Troubleshooting

## AP Not Joining

The most common causes for AP join failure are:

- CAPWAP discovery is failing because the AP cannot reach the controller IP. Verify IP reachability, routing, and that no firewall is blocking UDP 5246 and 5247.
- DHCP Option 43 is misconfigured or not present. Without Option 43 the AP falls back to DNS-based discovery using CISCO-CAPWAP-CONTROLLER.<domain>.
- MTU on the network path is below 1500 bytes. CAPWAP frames can be large and fragmentation often causes silent failures.
- The AP is running an incompatible software version. Check the AP image requirement for the controller version in use.

Collect debug output on the controller while the AP attempts to join:

```
debug capwap events enable
debug capwap errors enable
```

## Client Not Receiving an IP Address

- In central switching mode, verify that the SVI for the client VLAN has an `ip helper-address` pointing to the DHCP server, and that the VLAN is allowed on the trunk uplink.
- In FlexConnect mode, verify the Flex Profile VLAN mapping is correct and that the AP has local switching enabled for that WLAN.
- Check the Policy Profile to confirm the correct VLAN is assigned.
- Use `show wireless client detail mac-address <mac>` to see which VLAN the controller assigned the client to.

## Authentication Failures (802.1X)

Check the RADIUS server logs first, as they provide the most detail on why an authentication failed. On the controller:

```
debug aaa authentication
debug dot1x events
debug dot1x errors
```

Confirm the RADIUS server reachability:

```
test aaa group RADIUS-GROUP <username> <password> new-code
```

Verify the shared secret is identical on the controller and the RADIUS server. Shared secret mismatches typically show up as invalid authenticator errors in the server logs.

## RRM Not Adjusting Channels

If APs are not moving off interfering channels, verify:

- All APs have an RF Tag assigned referencing an RF Profile with RRM enabled
- The DCA channel list has at least two non-overlapping entries per AP
- APs are not statically assigned to channels (static channel assignment overrides RRM)

```
show wireless rrm 5ghz status
show ap auto-rf dot11 5ghz <ap-name>
```

## Roaming Issues

Clients that disconnect and reconnect instead of roaming are usually missing 802.11r, 802.11k, or 802.11v. Verify these are enabled on the WLAN. Also confirm that all APs handling the roaming path are in the same mobility group and that their controllers are mobility peers.

```
show wireless client detail mac-address <mac>
show wireless mobility peer ip <peer-ip>
```