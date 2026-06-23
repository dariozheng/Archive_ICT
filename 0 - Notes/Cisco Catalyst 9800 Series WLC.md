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

### 2. Network Architecture & Topology

- **Logical diagram** showing the WLC position (DMZ, core, distribution)
- **Physical interfaces used** (management, redundancy, service ports) with IP addresses, VLANs, and uplink switch ports
- **HA/SSO configuration** — which unit is active/standby, RP keepalive/redundancy port IPs
- **AP join mode** — FlexConnect, Local mode, or SD-Access fabric mode
- **CAPWAP/DTLS settings** — any non-default ports or DTLS encryption status
- **Mobility domain** — if multiple WLCs exist, which is the anchor and which is the foreign

---

### 3. Access & Credentials

- **GUI access** URL and port (default `https://<mgmt-ip>`, port 443)
- **CLI access** — SSH address, username/privilege level structure (level 15 vs. read-only accounts)
- **TACACS+/RADIUS** for AAA — server IPs, which server group is used for device management
- **Out-of-band access** — console server port, IP, or management network details
- **Credential rotation policy** — how often passwords change and where they are stored (e.g. vault, password manager)
- **Certificate** in use for the GUI — self-signed or CA-signed, expiry date

---

### 4. RF & Wireless Design Decisions

- **Radio Resource Management (RRM)** — is it enabled globally, per band, or overridden per AP?
- **Channel plan** — DCA or static? Allowed channel list, channel width
- **Tx power** — TPC enabled or fixed?
- **CleanAir / EDRRM** — enabled or not, and sensitivity settings
- **Band steering and load balancing** settings
- **Why** specific design choices were made (document the rationale, not just the config)

---

### 5. WLAN / SSID Configuration

For **each SSID**, document:

| Parameter                         | Value            |
| --------------------------------- | ---------------- |
| SSID name                         | e.g. `Corp-WiFi` |
| Security (WPA3/WPA2, 802.1X, PSK) |                  |
| RADIUS server(s) for auth         |                  |
| Policy profile assigned           |                  |
| VLAN / mapped interface           |                  |
| QoS policy                        |                  |
| Client exclusion timers           |                  |
| Band restrictions                 |                  |
| Any SSID-level ACLs               |                  |

---

### 6. Policy Tags, Site Tags & RF Tags (the "Tag" Architecture)

The 9800 uses a tag-based model that differs from older WLC platforms — this is often the most confusing part for newcomers. Include:

- Explanation of the **Policy Tag → WLAN Profile + Policy Profile** relationship
- **Site Tag** — local switching vs. central switching, flex profile name
- **RF Tag** — which RF profile is applied per site/AP group
- A table mapping which tags are applied to which APs or AP groups

---

### 7. AP Inventory

A table or exported CSV with:

- AP name, model, MAC (base radio MAC), serial number
- Location (building, floor, room)
- AP join mode (local/flex/fabric)
- Site tag assigned
- Switch port and PoE budget
- Any APs with special config (mesh, outdoor, monitor mode)

---

### 8. Routine Operations (Day-2 Tasks)

Step-by-step procedures for the most common tasks:

- **Adding a new AP** — pre-provisioning via AP name, applying correct tag
- **Creating or modifying an SSID**
- **Deauthenticating/excluding a client**
- **Checking client connectivity** (GUI path: Monitoring → Clients)
- **Running a packet capture** on the WLC or an AP
- **Checking AP radio statistics** and channel utilization
- **Viewing and clearing rogue APs**
- **Exporting client or AP reports**

---

### 9. Backup & Restore

- **Configuration backup** procedure — `copy running-config` to TFTP/SCP/USB, or via NETCONF
- **Backup schedule** and retention policy
- **Restore procedure** — including what happens during an HA failover vs. a full restore
- Location where backups are stored (server IP, path, credentials)
- **Software image backup** — where the golden image is stored

---

### 10. Software Upgrade Procedure

- Recommended upgrade path (IOS-XE trains to follow)
- **ISSU (In-Service Software Upgrade)** availability for the specific hardware
- Step-by-step procedure:
    1. Download image
    2. Install mode vs. bundle mode
    3. Pre-check commands (`show version`, `show redundancy`)
    4. The install command sequence
    5. Post-upgrade verification checklist
- Rollback procedure if upgrade fails

---

### 11. Monitoring & Alerting

- **SNMP** — version (v2c/v3), community strings or credentials, which NMS is polling the WLC
- **Syslog** — server IP, facility, severity level configured
- **Netflow/Flexible Netflow** — if enabled, collector address
- **DNA Center / Catalyst Center** — if the WLC is managed by CatC, note which features are pushed from CatC vs. managed locally
- **Cisco PI (Prime Infrastructure)** — if in use
- Key OIDs or alerts already configured for threshold breaches

---

### 12. Troubleshooting Procedures

Include a structured runbook for the most common issues:

**Client can't connect**

- Check client exclusion list
- Verify RADIUS reachability (`test aaa group …`)
- Check DHCP pool / scope on upstream device
- Debug commands: `debug client <mac>`, `show wireless client detail mac <mac>`

**AP not joining**

- Check CAPWAP reachability (VLAN/IP/routing)
- Check certificate trust (`show wireless management trustpoint`)
- Check DHCP option 43 if applicable
- `debug capwap events enable` on the WLC

**HA / SSO failover happened unexpectedly**

- Check `show redundancy` for reason
- Check `show log` around the failover time
- Verify standby is in hot standby state after recovery

**High interference / low throughput**

- `show ap auto-rf dot11 5ghz <ap-name>`
- CleanAir interference type report
- Force RRM recalculation: `ap dot11 5ghz rrm channel global once`

---

### 13. Security & Compliance Notes

- **Management ACL** — which source IPs are allowed to reach the management interface
- **HTTPS/SSH hardening** settings (TLS version, cipher suites, SSHv2 only)
- **Rogue policy** — what the policy does (alert only, auto-contain, manual contain)
- **Any local firewall rules** on the WLC itself
- **Audit log** retention
- **Compliance requirements** specific to the organization (PCI, ISO 27001, etc.)

---

### 14. Known Issues & Caveats

- Any bugs encountered during deployment and the workarounds applied
- Cisco TAC case numbers if relevant
- Links to applicable Cisco Field Notices or Bug IDs

---

### 15. Useful References & Contacts

- **Cisco 9800 Config Guide** for the specific IOS-XE version (always pin to the exact release)
- **Cisco Bug Search Tool** URL
- **TAC contact** and support contract number (SmartNet / SNTC)
- **Vendor/integrator contact** who performed the deployment
- **Internal escalation path** (L1 → L2 → network team lead)

---

### Quick-Reference Cheat Sheet (Appendix)

Include a one-pager with the most-used CLI commands:

```
show version
show wireless summary
show ap summary
show wireless client summary
show wireless exclusionlist
show redundancy
show run | sec wlan
debug wireless mac <client-mac> {monitor-time 60}
clear wireless client <mac> delete
request platform software trace rotate al
```