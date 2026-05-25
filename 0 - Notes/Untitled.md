## NAD Configuration

This note documents the configuration required on a Cisco IOS-XE switch — the Network Access Device, or NAD — to integrate with Cisco ISE for 802.1X / MAB authentication, dynamic authorization (CoA), endpoint profiling, and Centralized Web Authentication for guests.

### Default Values Overridden

Quick reference of explicit choices made in this configuration vs. the IOS defaults they override:

|Setting|Default|Configured|Reason|
|---|---|---|---|
|`radius-server timeout`|5 s|5 s (explicit)|Explicit baseline; tune only after measuring real ISE RTT.|
|`radius-server retransmit`|3|3 (explicit)|4 attempts total before failover, 20 s worst case.|
|`radius-server deadtime`|0 (off)|15 min|Ignore dead servers for 15 min to prevent per-auth retries.|
|`dot1x timeout tx-period`|30 s|7 s|Reach MAB fallback in 28 s instead of 90 s for non-supplicant devices.|
|`dot1x max-reauth-req`|2|3|One extra retry to tolerate slow / flaky supplicants without lengthening total too much.|
|`access-session host-mode`|single-host|multi-domain|Allow phone + PC on the same port.|
|`access-session control-direction`|both|in|Permit Wake-on-LAN to unauthenticated endpoints.|
|`access-session port-control`|force-auth|auto|Required for 802.1X to actually run.|
|`access-session closed`|open|closed|Block all pre-auth traffic; full secure-by-default posture.|
|`access-session mac-move`|deny|permit (`no ... deny`)|Allow MACs to move between ports without err-disable.|
|IPDT default policy|aggressive|custom (`IPDT_POLICY`)|Default ARP probing breaks some endpoints.|
|DHCP Option 82 insertion|enabled|disabled|Access switch is not a relay agent; many servers reject Option 82 from untrusted sources.|

---

### AAA Framework

#### Enabling AAA — `aaa new-model` 

Activates the AAA framework, replacing the legacy authentication engine. This is the prerequisite that enables the `aaa authentication`, `aaa authorization`, and `aaa accounting` command families.

> [!warning] Lockout risk 
> Enable this only after a local fallback user is defined or a RADIUS server is reachable. Without either, the next login attempt may lock you out of the switch.

#### Shared Session ID — `aaa session-id common` 

Forces the switch to use a <strong>single shared session ID</strong> across authentication, authorization, and accounting for the same session.

```
Authentication  ┐
Authorization   ├──→ all share the same session ID
Accounting      ┘
```

Without this, each AAA service generates its own ID and correlating records in ISE becomes painful — Live Sessions, accounting history, and CoA targeting all rely on a consistent identifier.

> [!note] What it actually changes 
> For 802.1X / MAB, authentication and authorization are usually combined into a single Access-Request / Access-Accept exchange. 
> Accounting then runs in parallel (Start, Update, Stop). 
> `aaa session-id common` ensures the `Acct-Session-Id` carried in accounting matches the session referenced in authentication, so ISE stitches them into one record. 

---

### RADIUS Server Configuration

_Defines how the switch reaches ISE, how it health-checks it, and where its packets come from on the wire._

#### Local Probe User 

```cisco
username test-user privilege 0 password 7 06120A3258031918160405041E00
```

A local account whose only purpose is to populate the RADIUS health-check probe. `automate-tester` (configured on the RADIUS server block below) sends periodic Access-Requests using these credentials to verify ISE is alive.

| Field         | Meaning                                                                                                                                                                                   |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `privilege 0` | Lowest privilege level — allows only `disable`, `enable`, `exit`, `help`, and `logout`. Deliberately useless for management, so even if the credentials leak, the account grants nothing. |
| `password 7`  | Cisco Type-7 reversible encryption. Weak — meaningful only as obfuscation. ISE will normally reject this account on policy (no matching identity), which is fine for the probe.           |

> [!info] How the probe works 
> The probe doesn't need to _succeed_ — a clean `Access-Reject` from ISE is enough to prove the server is responsive. What matters is that ISE answers at all.

#### RADIUS Server Definition 

```cisco
radius server ISE01
 address ipv4 10.140.2.31 auth-port 1812 acct-port 1813
 automate-tester username test-user ignore-acct-port probe-on
 key 7 075F02457D0A36162421045C
```

##### `radius server ISE01`

A locally significant name for this ISE node. The label has no meaning to ISE itself — it is purely how the switch refers to this server internally and inside server groups.

##### `address ipv4 10.140.2.31 auth-port 1812 acct-port 1813`

|Element|Meaning|
|---|---|
|`address ipv4 10.140.2.31`|IP of the ISE Policy Service Node (PSN)|
|`auth-port 1812`|UDP port for Access-Request / Accept / Reject|
|`acct-port 1813`|UDP port for Accounting Start / Stop / Update|

> 1812 and 1813 are the IANA-standard RADIUS ports. Use them unless ISE has been explicitly configured otherwise.

##### `automate-tester username test-user ignore-acct-port probe-on` 

Three behaviors rolled into one command:

|Keyword|Purpose|
|---|---|
|`automate-tester username ...`|Send periodic test probes using the named local account. ISE's response confirms the server is responsive.|
|`ignore-acct-port`|Probe the auth port only. ISE may not always answer probes on 1813 the same way, and including it can cause false "dead" detections.|
|`probe-on`|Probe <strong>only when the server is currently marked dead</strong>. Without this, the switch probes continuously, generating unnecessary RADIUS traffic.|

##### `key 7 075F02457D0A36162421045C`

The RADIUS shared secret. Must match the value configured on ISE for this NAD entry, otherwise every Access-Request fails the message-authenticator check.

#### AAA Server Group — `ISESERV` 

```cisco
aaa group server radius ISESERV
 server name ISE01
 server name ISE02
 deadtime 15
 ip radius source-interface Vlan800
```

A server group lets method lists reference one logical name instead of individual servers, and scopes timer / source-interface behaviour to this group only.

|Line|Effect|
|---|---|
|`server name ISE01` / `ISE02`|Add the previously defined `radius server` blocks as members. Order matters — ISE01 is tried first, ISE02 is the failover.|
|`deadtime 15`|A server marked dead is ignored for 15 minutes before being retried. Scoped to this group.|
|`ip radius source-interface Vlan800`|All RADIUS packets from this group are sourced from VLAN 800. <strong>Critical</strong> — ISE identifies the NAD by source IP, and this must match the IP recorded in the ISE NAD configuration.|

#### Global RADIUS Timers 

##### `radius-server timeout 5`

How long the switch waits for a single RADIUS response before declaring that attempt failed.

##### `radius-server retransmit 3`

How many additional attempts the switch makes against the same server before moving to the next one in the group.

```
Attempt 1 → wait 5s → no response
Attempt 2 → wait 5s → no response
Attempt 3 → wait 5s → no response
Attempt 4 → wait 5s → no response
        ↓
Give up on ISE01 → try ISE02
```

> Worst-case failover time to the secondary server: <strong>(retransmit + 1) × timeout = 4 × 5 = 20 seconds</strong>.

##### `radius-server dead-criteria time 5 tries 3`

The threshold that causes a server to be marked <strong>dead</strong>. Both conditions must be true simultaneously:

- `time 5` — at least 5 seconds have elapsed without a valid response.
- `tries 3` — at least 3 consecutive failures occurred in that window.

```
Failure 1 at 0s   ─┐
Failure 2 at 5s    ├── 3 failures + 5s elapsed → DEAD
Failure 3 at 10s  ─┘
        ↓
ISE01 marked dead, failover to ISE02
automate-tester begins probing ISE01
```

Requiring both conditions prevents a single slow response from prematurely killing the server.

##### `radius-server deadtime 15`

The global equivalent of the group-level `deadtime 15` above. Once a server is marked dead, ignore it for 15 minutes before probing again.

---

### RADIUS Attribute

_Shapes what the switch puts into RADIUS packets so that ISE has the context it needs for policy decisions and profiling._

> [!important] Why these matter 
> Default attribute formatting often does <strong>not</strong> match what ISE expects. The single most common cause of "MAB doesn't work" is the MAC address being sent in Cisco-default format (`0050.56ab.cdef`) instead of IETF upper-case (`00-50-56-AB-CD-EF`). The attribute commands in this section quietly determine whether your authentication policy will ever match.

#### Service-Type (Attribute 6)

##### `radius-server attribute 6 on-for-login-auth` 

Includes [[#Service-Type]] in Access-Request packets for login authentication. 

ISE policy conditions that match on `Service-Type` will not evaluate correctly without it.

##### `radius-server attribute 6 support-multiple` 

Allows multiple [[#Service-Type]] values in the same RADIUS packet — required when 802.1X and MAB run on the same ports, because they advertise different values (`Framed` for dot1x, `Call-Check` for MAB).

```
Single Service-Type:
  Service-Type = Framed (2)       

Multiple Service-Type:
  Service-Type = Framed (2)
  Service-Type = Call-Check (10)
```

#### Framed-IP-Address (Attribute 8)

##### `radius-server attribute 8 include-in-access-req` 

Includes the endpoint's <strong>IP address</strong> in Access-Requests. ISE uses this for profiling, IP-based policy conditions, and correlation with DHCP snooping data.

> [!note] Requires [[#Device Tracking Policies|IPDT]] 
> The switch can only populate this attribute if it has actually learned an IP for the endpoint. Device tracking must be functional, otherwise the field will be empty or `0.0.0.0`.

```
Without this:
  Access-Request → no IP address included
  ISE sees: MAC address only

With this:
  Access-Request → includes device IP address
  ISE sees: MAC address + IP address
```

#### Class (Attribute 25)

##### `radius-server attribute 25 access-request include` 

Causes the switch to echo the `Class` attribute from previous Access-Accepts back into subsequent Access-Requests. 
ISE uses this to maintain continuity across re-authentication and CoA — it can recognize the session as a continuation of a previous one rather than treating it as brand new.

```
Normal flow:
  Switch → ISE: Access-Request (no Class attribute)
  ISE → Switch: Access-Accept (includes Class attribute)

With this command:
  Switch → ISE: Access-Request (includes Class from previous session)
  ISE → Switch: Access-Accept (includes updated Class attribute)
```
#### Calling-Station-Id (Attribute 31)

##### `radius-server attribute 31 mac format ietf upper-case` 

Controls how MAC addresses are formatted in `Calling-Station-Id`.

|Format|Example|
|---|---|
|Cisco default|`0050.56ab.cdef`|
|IETF upper-case|`00-50-56-AB-CD-EF`|
|IETF lower-case|`00-50-56-ab-cd-ef`|

ISE expects IETF upper-case by default. A format mismatch means ISE can't find the MAC in its endpoint database — <strong>MAB authentication will fail silently</strong>.

##### `radius-server attribute 31 send nas-port-detail mac-only` 

Limits `Calling-Station-Id` to the MAC address only. Without this, the switch appends port identifiers, which ISE cannot parse — again breaking MAB.

```
Without mac-only:
  Calling-Station-Id = 00-50-56-AB-CD-EF:GigabitEthernet1/0/1

With mac-only:
  Calling-Station-Id = 00-50-56-AB-CD-EF
```

#### NAS-Identifier (Attribute 32)

##### `radius-server attribute 32 include-in-access-req format %h` 

Includes the switch hostname (`%h`) as the `NAS-Identifier`. Enables location-aware policy in ISE — applying different rules based on which switch the endpoint connected through.

|Part|Meaning|
|---|---|
|`attribute 32`|NAS-Identifier|
|`include-in-access-req`|Send it in every Access-Request|
|`format %h`|Use the switch hostname as the value|

```
ISE sees:
  NAS-Identifier  = VM90-TEST
  NAS-IP-Address  = 10.128.0.250
  NAS-Port-Type   = Ethernet (15)
```

#### Cisco VSAs

##### `radius-server vsa send authentication` 

Includes Cisco vendor-specific attributes in Access-Requests. The most important of these is `cisco-av-pair = audit-session-id=...`, which is the unique handle ISE 
uses to track a session across its lifetime and to target CoA messages.

```
Without it:
  Access-Request → standard attributes only
  ISE receives limited context about the session

With it:
  Access-Request → standard attributes + Cisco VSAs
  ISE receives richer context:
    cisco-av-pair = audit-session-id=xxxxx
    cisco-av-pair = method=dot1x
    cisco-av-pair = client-iif-id=xxxxx
```

##### `radius-server vsa send accounting` 

Without it, ISE Live Sessions and accounting reports are missing key fields (`connect-progress`, NAS speeds, the audit-session-id binding, etc.).

```
Without it:
  Accounting-Start/Stop → standard attributes only
  ISE session records are incomplete

With it:
  Accounting-Start/Stop → standard attributes + Cisco VSAs
  ISE receives:
    cisco-av-pair = audit-session-id=xxxxx
    cisco-av-pair = connect-progress=Auth Open
    cisco-av-pair = nas-rx-speed=xxxxx
    cisco-av-pair = nas-tx-speed=xxxxx
```

---

### 802.1X Global Settings

#### `dot1x system-auth-control` 

The master switch for 802.1X on the device. Without it, 802.1X does not run on any interface regardless of per-port configuration.

#### `dot1x critical eapol` 

When ISE is unreachable and a port is placed in Critical Authentication, this command tells the switch to send an EAPOL-Success directly to the endpoint — even though no real RADIUS authentication occurred.

Without `dot1x critical eapol`:

```
ISE goes down
        ↓
Port placed in Critical Auth (via `Critical_Access` service-template)
Switch sends nothing to the supplicant
        ↓
Supplicant: stuck in a pending state
        ↓
ISE returns → reauth triggered → supplicant fails to respond cleanly
        ↓
Link bounce often required to recover
```

With `dot1x critical eapol`:

```
ISE goes down
        ↓
Port placed in Critical Auth
Switch immediately emits EAPOL-Success to the supplicant
        ↓
Supplicant: "Authorised" — clean known state
        ↓
ISE returns → reauth triggered → supplicant responds cleanly
        ↓
No user impact
```

#### `no access-session mac-move deny` 

By default IOS-XE denies a MAC address from re-appearing on a different port while the original session is still active. In a real environment — laptops moving between docking stations, phones being relocated — this causes constant blocked-port incidents.

Disabling the default behavior means the old session is automatically cleared when the same MAC appears on a new port, allowing the new authentication to proceed.

---

### Dynamic Authorization (CoA) 

```cisco
aaa server radius dynamic-author
 client 10.140.2.31 server-key 7 040B280F3C22635D3A2A0A47
 client 10.140.2.32 server-key 7 08716F473A1A2A0421380354
```

Standard RADIUS is one-way: the switch asks, ISE answers. CoA (RFC 5176) makes it bidirectional — ISE can push policy changes mid-session.

```
Standard RADIUS:
  Switch → ISE:  "Can this device access the network?"
  ISE → Switch:  "Yes, put it in VLAN 802"

  Session starts... ISE cannot modify it
```

```
With CoA:
  Switch → ISE:  "Can this device access the network?"
  ISE → Switch:  "Yes, put it in VLAN 802"

  Session running...

  ISE → Switch:  "Move that device to VLAN 805"  
  ISE → Switch:  "Disconnect that device now"     
  ISE → Switch:  "Apply this new ACL"           
```

The `dynamic-author` block opens a listener on UDP port <strong>3799</strong> (the standard CoA port) and authorizes specific ISE nodes — by IP and shared secret — to push CoA messages to this switch.

> Only the IPs explicitly listed under `client` may send CoA. Requests from any other source are dropped.

---

### AAA Method Lists

_Method lists tell the switch <strong>who to ask</strong> and <strong>what to do with the answer</strong>._

#### `aaa authentication dot1x default group ISESERV` 

Tells the switch <strong>who to ask</strong> when a device attempts to authenticate via 802.1X.

| Element                    | Meaning                                        |
| -------------------------- | ---------------------------------------------- |
| `aaa authentication dot1x` | Applies to 802.1X authentication requests      |
| `default`                  | Used on all 802.1X-enabled ports automatically |
| `group ISESERV`            | Forwards requests to the named RADIUS group    |

> When a PC plugs in and sends EAP credentials, the switch forwards them to ISE via this instruction.

#### `aaa authorization network default group ISESERV` 

After authentication succeeds, this tells the switch to apply ISE-returned network policy attributes. 

The keyword `network` specifically covers <strong>network access policy attributes</strong> pushed back from ISE in the Access-Accept packet:

|Attribute|Example|Effect|
|---|---|---|
|VLAN assignment|`Tunnel-Private-Group-ID = 802`|Dynamically place the port in a VLAN|
|Downloadable ACL|`Cisco-AVPair = ip:inacl#10=...`|Apply a per-session ACL|
|Redirect URL|`Cisco-AVPair = url-redirect=https://ise/portal/...`|Send traffic to a captive portal|
|Redirect ACL|`Cisco-AVPair = url-redirect-acl=ACL_GUEST_REDIRECT`|Which traffic gets redirected|
|SGT|`Cisco-AVPair = cts:security-group-tag=...`|Apply a Cisco TrustSec tag|

Without `aaa authorization network`, the switch ignores all policy attributes returned by ISE — endpoints authenticate successfully but never receive their VLAN, dACL, or redirect.

> Authorization in standard RADIUS is request/response — the switch must ask. ISE cannot push policy unilaterally; the only exception is CoA.

#### `aaa accounting identity default start-stop group ISESERV` 

Sends a Start record when an identity session opens and a Stop record when it closes. The keyword `identity` scopes this to 802.1X / MAB subscriber sessions specifically.

#### `aaa accounting system default start-stop group ISESERV` 

Sends accounting records for <strong>switch-level events</strong> such as <strong>reloads</strong> and <strong>configuration changes</strong>. 

> Useful for audit trails — ISE logs when the switch rebooted or came back online.

#### `aaa accounting update newinfo periodic 2880` 

Two distinct behaviors combined:

| Keyword         | Purpose                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `newinfo`       | When session attributes change mid-flight (e.g. a CoA replaces the VLAN), immediately emit an interim accounting update. |
| `periodic 2880` | Send a keepalive accounting update every 2880 minutes (48 hours) even if nothing has changed.                            |

---

### Layer-2 Security

_Defends the binding tables and the L2 control plane against rogue clients and ARP / DHCP attacks._

#### DHCP Snooping 

```cisco
ip dhcp snooping
ip dhcp snooping vlan 800,802,805,850
no ip dhcp snooping information option
```

| Command                                  | Effect                                                                                                                                                                                                      |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ip dhcp snooping`                       | Globally enables DHCP snooping. Without this, every other snooping command is inert. All ports start out untrusted; uplinks and DHCP server ports must be explicitly trusted with `ip dhcp snooping trust`. |
| `ip dhcp snooping vlan 800,802,805,850`  | Activates snooping on the listed VLANs.                                                                                                                                                                     |
| `no ip dhcp snooping information option` | Disables Option 82 insertion. Disabled in access-layer deployments because the access switch is not a DHCP relay.                                                                                           |

The snooping process builds the <strong>binding table</strong> — IP / MAC / VLAN / port / lease time — which feeds Dynamic ARP Inspection and IP Device Tracking.

> On trunk ports facing other infrastructure: `ip dhcp snooping trust`.

#### Dynamic ARP Inspection 

```cisco
ip arp inspection vlan 800,802,805,850
```

DAI intercepts every ARP packet on untrusted ports and validates source IP / source MAC against the DHCP snooping binding table. Mismatches are dropped, defeating ARP-spoofing attacks.

- <strong>Trusted ports</strong> (uplinks): ARP passes without inspection.
- <strong>Untrusted ports</strong> (access): every ARP is checked.
- <strong>Static-IP hosts</strong> need manual ARP ACLs because they have no snooping entry.

DAI is entirely dependent on DHCP snooping — configure snooping first.

> On trunk ports facing other infrastructure: `ip arp inspection trust`.

### IP Device Tracking — Global

```cisco
device-tracking tracking
```

Enables active device tracking (SISF — Switch Integrated Security Features) globally. Once enabled, attaching a `device-tracking policy` to an interface causes the switch to maintain IP-to-MAC bindings on that port by snooping DHCP and ARP and, optionally, sending ARP probes.

The resulting binding table is consumed by:

- <strong>ISE</strong> — to know where an endpoint is physically connected.
- <strong>802.1X / MAB</strong> — to associate the session's MAC with its eventual IP.
- <strong>DAI</strong> — as a binding source.
- <strong>CoA</strong> — to find the correct port when bouncing a session.
- <strong>Downloadable ACLs</strong> — when they refer to source IPs.

> [!warning] Don't mix legacy with SISF 
> The legacy global `ip device tracking` family is deprecated on modern IOS-XE. 
> 
> Mixing it with `device-tracking policy` causes duplicate or stale bindings that fail silently. Use SISF exclusively.

Verification:
```cisco
show ip dhcp snooping
show ip dhcp snooping binding
show ip arp inspection
show ip arp inspection statistics
show device-tracking database
show device-tracking policies
```

---

### Device Tracking Policies

_Attached per-port. Tunes how aggressively the switch maintains IP-to-MAC bindings and how it treats peers._

#### Access-Port Policy — `IPDT_POLICY` 

```cisco
device-tracking policy IPDT_POLICY
 security-level glean
 limit address-count 10
 tracking enable
```

Applied to access ports where end devices connect.

|Setting|Effect|
|---|---|
|`security-level glean`|Passively learns bindings from observed DHCP and ARP traffic without enforcement. The stricter `guard` would drop packets that violate the binding table.|
|`limit address-count 10`|Caps the number of IPs that can be tracked per port — defeats binding-table exhaustion. Ten accommodates a PC, an IP phone, a couple of VMs, etc. without abuse.|
|`tracking enable`|The switch actively probes hosts (ARP / ND) to verify they are still present and to refresh stale entries.|

#### Trunk / Uplink Policy — `Disable_DT_Trunk` 

```cisco
device-tracking policy Disable_DT_Trunk
 trusted-port
 device-role switch
```

Applied to uplinks and inter-switch links.

| Setting              | Effect                                                                                                                              |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `trusted-port`       | Skip validation and inspection for bindings learned on this port — the peer switch is trusted infrastructure.                       |
| `device-role switch` | Tells SISF the neighbor is a switch, not a host. The switch won't try to ARP-probe it and won't attempt to track it as an endpoint. |

> [!tip] 
> Default policy can be aggressive on modern IOS-XE, the default SISF policy probes endpoints fairly aggressively, which can cause problems with some IP phones, older Windows hosts, and certain IoT devices. Always attach an explicit policy rather than relying on defaults.

---

### Device Sensor — Endpoint Profiling

_Passively reads DHCP / CDP traffic the switch already sees and forwards selected fields to ISE for profiling._

Device Sensor is a passive sensor — it does not generate any of this traffic. It collects from what is already flowing through the switch, caches it, and forwards selected fields to ISE in RADIUS authentication and accounting messages.

#### `cdp run` 

Enables CDP globally. Device Sensor cannot collect CDP TLVs from neighbors if CDP itself isn't running. CDP is on by default but is stated explicitly here for clarity.

#### DHCP Filter — Which Options to Collect 

```cisco
device-sensor filter-list dhcp list dhcp_list
 option name host-name
 option name requested-address
 option name parameter-request-list
 option name class-identifier
 option name client-identifier
device-sensor filter-spec dhcp include list dhcp_list
```

The `filter-list` defines _what is available_ to collect; the `filter-spec ... include list` activates it. Without the `filter-spec` line, the list is defined but never used.

| DHCP Option | Name                     | Why ISE Wants It                                                                                                                                                          |
| ----------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 12          | `host-name`              | The endpoint's configured hostname (e.g. `LAPTOP-ABC123`). Useful for profiling and user/device correlation.                                                              |
| 50          | `requested-address`      | The <strong>IP</strong> the client is asking for. Helps correlate the endpoint with a specific lease.                                                                     |
| 55          | `parameter-request-list` | The list of <strong>DHCP options</strong> the client asks the server for. Different OS and devices ask in different orders — this is a very strong profiling fingerprint. |
| 60          | `class-identifier`       | <strong>Vendor class identifier</strong> (e.g. `MSFT 5.0`, `dhcpcd`). Another strong device-type signal.                                                                  |
| 61          | `client-identifier`      | <strong>Unique client identifier</strong>, typically the <strong>MAC</strong>. ISE uses this to track devices across sessions.                                            |

#### CDP Filter — Which TLVs to Collect 

```cisco
device-sensor filter-list cdp list cdp_list
 tlv name device-name
 tlv name address-type
 tlv name capabilities-type
 tlv name platform-type
 tlv name version-type
device-sensor filter-spec cdp include list cdp_list
```

|TLV|Why ISE Wants It|
|---|---|
|`device-name`|The neighbour's hostname — typically meaningful for Cisco IP phones.|
|`address-type`|The neighbour's IP, as advertised in CDP.|
|`capabilities-type`|Device class (switch, router, telephone, host). For an IP phone this immediately identifies it as `telephone`.|
|`platform-type`|Exact hardware model (e.g. `Cisco IP Phone 8841`). One of the most valuable profiling signals.|
|`version-type`|Firmware version. Useful for compliance policies (e.g. "phones below firmware X get quarantined").|

#### `device-sensor notify all-changes` 

Notifies ISE immediately whenever a tracked attribute changes mid-session. Without this, ISE only sees sensor data at session start, and a profile change wouldn't trigger a policy re-evaluation.

#### Sending Sensor Data to ISE 

Device Sensor collects data into a local cache. The following commands wire that cache into RADIUS messages so ISE actually receives it.

```cisco
access-session attributes filter-list list sensor_list
 cdp
 dhcp
access-session accounting attributes filter-spec include list sensor_list
access-session authentication attributes filter-spec include list sensor_list
```

|Command|Effect|
|---|---|
|`access-session attributes filter-list list sensor_list`|Define a named list (`sensor_list`) of which sensor sources (CDP, DHCP) feed into access-session messages.|
|`access-session accounting attributes filter-spec include list ...`|Include those sources in RADIUS Accounting (Start / Update / Stop). ISE uses this for ongoing profiling.|
|`access-session authentication attributes filter-spec include list ...`|Include them in Access-Requests as well. Allows ISE to make profiling-based decisions at authentication time, not just after-the-fact.|

> Without these `access-session` wiring commands, Device Sensor collects data but it never leaves the switch.

#### Verification

```cisco
show device-sensor cache all
show device-sensor cache interface <int>
show running-config | section device-sensor
```

#### What Breaks If Missing

|Omission|Symptom|
|---|---|
|`filter-spec ... include`|Filter list is defined but unused; no attributes collected.|
|`access-session ... filter-spec include`|Attributes collected locally but never sent to ISE — profiling fails.|
|`cdp run` disabled|All CDP-based profiling silent; IP phones may be misclassified or invisible.|
|`notify all-changes`|ISE never sees mid-session profile changes; CoA-driven re-classification doesn't fire.|

---

### IBNS 2.0 Classification — Class-Maps

_The predicates. Each class-map matches on session state, not on packet content. They are consumed by the policy-map in the next section._

<strong>Syntax:</strong>

```cisco
class-map type control subscriber match-all|match-any|match-none <name>
  match <condition>
```

|Match Type|Logic|
|---|---|
|`match-all`|All conditions must be true (AND)|
|`match-any`|At least one condition must be true (OR)|
|`match-none`|None of the conditions must be true (NOT / NOR)|

#### Method Identification

```cisco
class-map type control subscriber match-all DOT1X
 match method dot1x

class-map type control subscriber match-all MAB
 match method mab
```

Broad matches — true whenever the named method is the one in play. Used by `event authentication-success` to branch on which method succeeded.

#### dot1x Failure Modes

```cisco
class-map type control subscriber match-all DOT1X_DENIED
 match method dot1x
 match result-type method dot1x authoritative

class-map type control subscriber match-all DOT1X_TIMEOUT
 match method dot1x
 match result-type method dot1x method-timeout

class-map type control subscriber match-all DOT1X_NO_SUPPLICANT
 match result-type method dot1x agent-not-found
```

|Class|Condition|Meaning|
|---|---|---|
|`DOT1X_DENIED`|dot1x ran and got an <strong>authoritative</strong> answer — ISE returned an Access-Reject.|Hard deny by the server.|
|`DOT1X_TIMEOUT`|dot1x started but the method timer expired before completion.|Supplicant present but stalled (slow boot, EAP method hang).|
|`DOT1X_NO_SUPPLICANT`|No EAPOL response at all — the switch's EAPOL-Identity-Request frames got no reply.|Endpoint has no supplicant (printer, IoT device, dumb camera).|

#### MAB Failure Mode

```cisco
class-map type control subscriber match-all MAB_DENIED
 match method mab
 match result-type method mab authoritative
```

MAB ran and ISE returned an authoritative Access-Reject — the MAC is unknown or blacklisted.

#### AAA-Down Cases

```cisco
class-map type control subscriber match-all AAA-DOWN_UNAUTH_USER
 match result-type aaa-timeout
 match authorization-status unauthorized

class-map type control subscriber match-all AAA-DOWN_GUEST_USER
 match result-type aaa-timeout
 match activated-service-template Guest_Redirect

class-map type control subscriber match-all AAA-DOWN_AUTH_USER
 match result-type aaa-timeout
 match authorization-status authorized
```

These three differentiate AAA-unreachable cases by the session's <strong>prior state</strong>, which is what allows the policy to take different actions for previously-authorized users, guests-in-redirect, and never-authenticated newcomers.

|Class|Prior state|Intended behaviour|
|---|---|---|
|`AAA-DOWN_AUTH_USER`|Already authorized|Keep them working — do not disturb the existing session.|
|`AAA-DOWN_GUEST_USER`|In a Guest redirect state|Clear the broken redirect, drop into Critical Access.|
|`AAA-DOWN_UNAUTH_USER`|Never authorized|Provide local Critical Access as a fallback.|

#### Critical-Auth State

```cisco
class-map type control subscriber match-all CRITICAL_AUTH
 match activated-service-template Critical_Access

class-map type control subscriber match-none NOT_CRITICAL_AUTH
 match activated-service-template Critical_Access
```

Complementary predicates:

- `CRITICAL_AUTH` is true when the session is currently running under the local Critical Access fallback.
- `NOT_CRITICAL_AUTH` uses `match-none` on the same condition, so it is true when the session is <strong>not</strong> under Critical Access.

> [!note] How `match-none` works here The `match-none` keyword is part of the class-map header itself, not a separate match line. The class-map says: "match if none of the conditions below are true." Combined with the single condition that follows, it evaluates as the logical inverse of `CRITICAL_AUTH`.

#### Verification

```cisco
show class-map type control subscriber
show class-map type control subscriber name <CLASS-NAME>
```

Related: [[#IBNS 2.0 Policy Engine — `ISE-NAC-POLICY`]]

---

### IBNS 2.0 Policy Engine — `ISE-NAC-POLICY`

_The state machine. Consumes the class-maps above and orchestrates the lifecycle of every authentication session on every port that sources the [[#Interface Template — `NAC-INT-TEMPLATE`|interface template]]._

#### Evaluation Mechanics

When an event fires, the policy-map engine walks the classes under that event in numeric order (5, 10, 20, …). Two things govern execution:

<strong>At the event level:</strong>

|Keyword|Behaviour|
|---|---|
|`match-all`|Every class whose conditions match has its action list executed (in order).|
|`match-first`|Only the first matching class runs; the rest are skipped entirely.|

<strong>At the class level:</strong>

|Keyword|Behaviour|
|---|---|
|`do-until-failure`|Run actions 10, 20, 30… in order; stop at the first failure. _(Used throughout this policy.)_|
|`do-all`|Run every action regardless of success or failure.|
|`do-until-success`|Run actions until one succeeds, then stop.|

The inner action numbers (`10`, `20`, `30`) are just ordering — they have no semantic meaning. Gaps allow new actions to be inserted later without renumbering.

#### Action Verbs Reference

|Verb|Effect|
|---|---|
|`authenticate using <method> priority <n>`|Start a method instance. Lower priority number wins when multiple methods succeed.|
|`terminate <method>`|Destroy a specific method instance. The session itself survives.|
|`authorize`|Apply the authorization attributes returned by RADIUS or by an active service-template.|
|`unauthorize`|Remove the authorization but keep the session record. The port is effectively blocked.|
|`clear-session`|Destroy the entire session — next packet from the endpoint triggers a fresh session.|
|`pause reauthentication`|Keep the session but stop the periodic reauth timer.|
|`resume reauthentication`|Re-enable the periodic reauth timer.|
|`activate service-template <name>`|Apply a locally-defined attribute bundle (used when no RADIUS profile is available).|
|`authentication-restart <seconds>`|Re-run the full state machine after the specified delay.|
|`restrict`|In violation context: drop the offending traffic without disabling the port.|

#### High-Level Flow

```
Device plugs in
      │
      ▼
[session-started] ──► dot1x + MAB (dot1x preferred)
      │
      ├── dot1x succeeds ──► [auth-success: DOT1X] ──► authorize
      ├── MAB succeeds ───► [auth-success: MAB]   ──► authorize
      │
      └── failure ──► [auth-failure: match-first]
                           │
                    ┌──────┼──────────────────────┐
              ISE denied   │  ISE unreachable     │
              → try MAB    │  → Critical Auth     │ Unknown → restart 60s
                           │  (3 sub-cases)
                           │
                    Supplicant detected later?
                    → [agent-found] → upgrade to dot1x
                           │
                    ISE returns?
                    → [aaa-available] → clear or resume
```

#### Event: `session-started match-all`

Triggered when a new subscriber session is created — link up, or a new MAC learned on a multi-auth / multi-domain port.

```cisco
10 class always do-until-failure
  10 authenticate using dot1x priority 10
  20 authenticate using mab priority 20
```

Both methods are launched, but with priorities 10 and 20 — <strong>lower number = higher precedence</strong>. dot1x runs first; MAB sits in the wings and is only relied on if something tells the state machine that dot1x has failed or that no supplicant is present. If dot1x succeeds, MAB never gets to authorize.

#### Event: `authentication-failure match-first`

The brain of the policy. `match-first` means classes are evaluated in numeric order and <strong>exactly one runs</strong>. The class ordering deliberately puts the most specific conditions first and the catch-all last.

##### Class 5 — `DOT1X_DENIED`

```
10 terminate dot1x
20 authenticate using mab priority 20
```

ISE explicitly rejected the dot1x identity. Terminate dot1x and fall back to MAB — useful when the certificate or user credentials failed but the MAC is still allowed (e.g. an IP phone whose dot1x supplicant misbehaves).

##### Class 10 — `AAA-DOWN_GUEST_USER`

```
10 clear-session
20 activate service-template Critical_Access
30 authorize
40 pause reauthentication
```

ISE went down with the endpoint mid-redirect. The redirect can't complete, so tear the session down, apply the local `Critical_Access` template, and stop hammering the dead AAA server.

##### Class 20 — `AAA-DOWN_AUTH_USER`

```
10 authorize
20 pause reauthentication
```

ISE went down but the endpoint was already fully authorized. Do <strong>not</strong> disturb the session — just refresh the existing authorization and pause reauth so timers don't expire against a dead server. <strong>Zero user-visible impact.</strong>

##### Class 30 — `AAA-DOWN_UNAUTH_USER`

```
10 activate service-template Critical_Access
20 authorize
30 pause reauthentication
```

ISE went down before the endpoint authenticated. There's no prior profile to keep — apply the local fallback so the device gets at least limited access.

##### Class 40 — `DOT1X_TIMEOUT`

```
10 terminate dot1x
20 authenticate using mab priority 20
```

dot1x started but did not complete in time. Kill it, try MAB.

##### Class 50 — `MAB_DENIED`

```
10 terminate mab
20 unauthorize
```

The MAC is explicitly rejected by ISE. There's nowhere left to go — `unauthorize` puts the session into a blocked state until something kicks the state machine (link bounce, inactivity timeout, CoA).

##### Class 60 — `DOT1X_NO_SUPPLICANT`

```
10 terminate dot1x
20 authenticate using mab priority 20
```

Endpoint has no 802.1X supplicant. Same remediation as DOT1X_TIMEOUT — fall to MAB.

> The three dot1x failure classes (DENIED / TIMEOUT / NO_SUPPLICANT) are separated despite sharing remediation, because the failure reason matters for logging and troubleshooting (`show access-session` reports the type).

##### Class 70 — catch-all (`always`)

```
10 terminate mab
20 terminate dot1x
30 authentication-restart 60
```

If we reached this class, no named failure condition matched. Tear down both methods, wait 60 seconds, then restart the whole state machine. The delay prevents tight loops against a misbehaving endpoint.

#### Event: `aaa-available match-all`

Triggered when AAA reachability is restored.

```cisco
10 class CRITICAL_AUTH do-until-failure
  10 clear-session
20 class NOT_CRITICAL_AUTH do-until-failure
  10 resume reauthentication
```

- Sessions currently in Critical Access → `clear-session` → forces a fresh `session-started` event so the endpoint re-authenticates against the now-live ISE and picks up its real policy.
- Sessions that had reauth paused but never entered Critical → `resume reauthentication` → normal reauth resumes on schedule.

The two classes are logical complements, so for any given session exactly one runs. This is the "graceful restoration" pair, mirroring the "graceful degradation" handled by the AAA-DOWN classes.

#### Event: `agent-found match-all`

Triggered when an EAPOL frame is observed on a session that wasn't already running dot1x.

```cisco
10 class always do-until-failure
  10 terminate mab
  20 authenticate using dot1x priority 10
```

Classic scenario: a Windows PC boots slowly, dot1x times out (about 28 seconds with this template's timers), MAB authorizes the MAC, then the 802.1X supplicant finally starts. EAPOL arrives, this event fires, and the policy <strong>upgrades</strong> the session from MAB to dot1x — giving the endpoint its proper identity-based policy instead of the weaker MAC-only one.

#### Event: `inactivity-timeout match-all`

```cisco
10 class always do-until-failure
  10 clear-session
```

Idle session expires → tear it down. The next packet from the endpoint triggers a fresh session-started.

#### Event: `authentication-success match-all`

```cisco
10 class DOT1X do-until-failure
  10 authorize
20 class MAB do-until-failure
  10 authorize
```

`authorize` is what actually commits the RADIUS-returned attributes (VLAN, dACL, redirect URL, SGT) to the session — until it runs, ISE's success message is just data. Splitting by method allows method-specific post-auth behaviour to be added later.

#### Event: `violation match-all`

```cisco
10 class always do-until-failure
  10 restrict
```

When a host-mode constraint is violated (e.g. a second data MAC on a `multi-domain` port), drop the offending traffic but <strong>leave the port up</strong> and the legitimate session intact.

|Action|Behaviour|
|---|---|
|`shutdown`|Err-disable the port. Requires manual or auto recovery.|
|`protect`|Silently drop offending traffic. No logging.|
|`restrict`|Drop offending traffic, log it via SNMP/syslog. Selected here.|

#### Verification

```cisco
show policy-map type control subscriber name ISE-NAC-POLICY
show access-session interface <int> details
show access-session method-list all
show access-session event-logging interface <int>
```

#### What Breaks If Missing

|Omission|Symptom|
|---|---|
|`event authentication-success` ... `authorize`|Endpoints authenticate but never receive their VLAN/dACL.|
|`event session-started`|New connections never start any authentication method.|
|`event authentication-failure` AAA-DOWN classes|ISE outages disrupt users — no critical-auth fallback fires.|
|Missing `agent-found`|Slow-booting Windows PCs stay on MAB even after their supplicant comes up.|

---

### Interface Template — `NAC-INT-TEMPLATE`

_The interface-level building block that pairs with [[#IBNS 2.0 Policy Engine — `ISE-NAC-POLICY`|the policy-map]]. The policy-map defines what to do; the template defines how the port behaves._

```cisco
template NAC-INT-TEMPLATE
 description NAC INTERFACE
 switchport mode access
 switchport access vlan 802
 ip dhcp snooping limit rate 20
 ip arp inspection limit rate 100
 spanning-tree portfast
 spanning-tree bpduguard enable
 authentication periodic
 authentication timer reauthenticate server
 mab
 access-session control-direction in
 access-session host-mode multi-domain
 access-session closed
 access-session port-control auto
 dot1x pae authenticator
 dot1x timeout tx-period 7
 dot1x max-reauth-req 3
 device-tracking attach-policy IPDT_POLICY
 service-policy type control subscriber ISE-NAC-POLICY
```

> [!note] IBNS 1.0 syntax inside an IBNS 2.0 deployment The `authentication periodic` and `authentication timer reauthenticate server` lines are IBNS 1.0 syntax. They remain valid alongside the IBNS 2.0 policy-map and continue to be supported on modern IOS-XE. They're kept because the equivalent IBNS 2.0 way of doing reauth is more verbose for no operational benefit. This is not an inconsistency — it is a deliberate, supported mix.

#### Applying the Template to Real Interfaces

The template itself does nothing until sourced from an interface:

```cisco
interface range GigabitEthernet1/0/1 - 48
 source template NAC-INT-TEMPLATE
```

Changes to the template propagate automatically to every interface that sources it — this is the operational reason for using templates instead of repeating the same block per port.

#### Basic Port Configuration

|Command|Effect|
|---|---|
|`switchport mode access`|Force access mode — no trunk negotiation.|
|`switchport access vlan 802`|<strong>Real client data VLAN.</strong> This is where authenticated endpoints actually live — it is the production access VLAN, not a quarantine. With `access-session closed`, the port blocks all traffic before authentication regardless of VLAN, so placing the static assignment directly on the production VLAN is safe. ISE can still override per-role via `Tunnel-Private-Group-ID`, but the default destination is fully functional.|

#### Layer-2 Hardening

|Command|Effect|
|---|---|
|`ip dhcp snooping limit rate 20`|Rate-limit DHCP packets to 20 pps; excess err-disables the port. Defeats DHCP flood attacks and binding-table exhaustion.|
|`ip arp inspection limit rate 100`|Same idea for DAI — cap ARP packets at 100 pps to prevent CPU overload.|
|`spanning-tree portfast`|Skip STP listening/learning; transition directly to forwarding. Required for end-host ports so they get DHCP before timing out.|
|`spanning-tree bpduguard enable`|Safety partner to PortFast — if any BPDU arrives (somebody plugged in a switch), err-disable the port.|

#### Reauthentication Behaviour

```
authentication periodic
authentication timer reauthenticate server
```

Periodic reauth is enabled and the interval is taken from the RADIUS `Session-Timeout` attribute (combined with `Termination-Action = RADIUS-Request`). Centralising the timer in ISE lets you tune reauth per identity group rather than per switch.

#### Method Enablement

|Command|Effect|
|---|---|
|`mab`|Makes MAB <strong>available</strong> on this port. Whether it actually runs is controlled by the policy-map. Without this, the policy can't fall back to MAB.|
|`dot1x pae authenticator`|Declares this port as the 802.1X authenticator (the switch side of the dot1x conversation). Without it, EAPOL frames are ignored.|

#### Access-Session Behaviour

|Command|Effect|
|---|---|
|`access-session control-direction in`|Block traffic _from_ the host _to_ the network before authorization; allow traffic in the reverse direction. This enables Wake-on-LAN. The alternative `both` blocks both directions.|
|`access-session host-mode multi-domain`|Allows one data MAC plus one voice MAC on the port — the classic IP phone + PC scenario. Voice domain is signalled by CDP or LLDP-MED.|
|`access-session closed`|Pre-auth state blocks <strong>all</strong> traffic (including DHCP, DNS) until authorization completes.|
|`access-session port-control auto`|The on switch for 802.1X port control. Other values: `force-authorized` (always allow, dot1x off) and `force-unauthorized` (always block).|

##### Host-Mode Options

|Mode|Behaviour|
|---|---|
|`single-host`|Exactly one MAC.|
|`multi-host`|One MAC authenticates; all others are passively allowed (legacy, weak).|
|`multi-auth`|Each MAC authenticates independently. For unmanaged switches or hubs behind the port.|
|`multi-domain`|Exactly one data MAC plus one voice MAC. Used here.|

#### 802.1X Timing

```
dot1x timeout tx-period 7
dot1x max-reauth-req 3
```

Controls how aggressively the switch hunts for an 802.1X supplicant before falling back to MAB.

|Parameter|Meaning|
|---|---|
|`tx-period 7`|Wait 7 seconds between EAPOL-Identity-Request retransmissions (default: 30).|
|`max-reauth-req 3`|Send up to 3 additional retransmissions after the initial one (4 attempts total).|

<strong>Total fallback time = `tx-period × (max-reauth-req + 1) = 7 × 4 = 28 seconds</strong>, vs. the default of 90 seconds.

#### Device Tracking and Policy Attachment

```
device-tracking attach-policy IPDT_POLICY
service-policy type control subscriber ISE-NAC-POLICY
```

The first attaches the IPDT policy that maintains IP-to-MAC bindings. The second binds the entire IBNS 2.0 policy-map to this port — <strong>without this line, the port has 802.1X and MAB available but no orchestrator to run them.</strong>

#### Template / Policy Interlock

The template and the policy-map are co-dependent:

- `authenticate using dot1x` in the policy requires `dot1x pae authenticator` and `port-control auto` here.
- `authenticate using mab` in the policy requires `mab` here.
- The 28-second `DOT1X_NO_SUPPLICANT` fallback time is set by `tx-period` × `max-reauth-req` here.
- `access-session closed` makes the pre-auth state actually block traffic.
- `multi-domain` host-mode is what lets the policy run two independent state machines (data and voice) on the same port.

#### Verification

```cisco
show access-session interface <int> details
show derived-config interface <int>            ! shows the template merged into the interface
show running-config interface <int>
show authentication sessions interface <int>   ! legacy syntax, still works
```

#### What Breaks If Missing

|Omission|Symptom|
|---|---|
|`service-policy type control subscriber`|Port does no authentication regardless of `mab` / `dot1x` lines.|
|`dot1x pae authenticator`|EAPOL frames are ignored; only MAB can ever run.|
|`mab`|No fallback method for non-supplicant devices; printers / IoT can never connect.|
|`device-tracking attach-policy`|dACLs don't apply correctly; CWA never redirects.|
|`access-session port-control auto`|Whole authentication machinery is dormant on the port.|
|`access-session closed`|Endpoints can communicate freely before authentication completes.|
|Forgot `source template` on actual interface|Template is defined but never applied; ports stay at defaults.|

---

### Centralized Web Authentication (CWA) for Guests

_Cisco model where the switch does not host a login page itself. It intercepts the guest's HTTP/HTTPS traffic and hands the session off to the ISE Guest Portal via an HTTP 302 redirect._

#### Guest VLAN — `vlan 805`

```cisco
vlan 805
 name LAN-GUEST-ACCESS
```

Layer-2 segment for unauthenticated guest traffic. All guest ports drop into this VLAN before authentication completes. The entire redirect flow happens within this VLAN.

#### HTTP/HTTPS Server Configuration <strong>[Required for CWA]</strong>

|Command|Purpose|
|---|---|
|`ip http server`|Enable the HTTP server. Required — the switch needs an HTTP server to issue the redirect response.|
|`ip http secure-server`|Enable the HTTPS server. Required when `intercept-https-enable` is used in the parameter-map.|
|`ip http active-session-modules none`|Disable all HTTP-based web management modules. Server stays up for redirect, but UI is closed.|
|`ip http secure-active-session-modules none`|Same lock-down for HTTPS modules.|
|`ip http authentication aaa login-authentication HTTPSRV`|If anyone ever does manage to reach the web UI, authenticate via the `HTTPSRV` method list.|
|`ip http client source-interface Vlan800`|Outbound HTTP requests from the switch itself (image downloads, etc.) are sourced from management.|

> [!important] Web server enabled, web UI closed The combination above is deliberate: the HTTP/HTTPS server must be running to serve the redirect, but the management UI is locked off.

#### Redirect ACL — `ACL_GUEST_REDIRECT`

```cisco
ip access-list extended ACL_GUEST_REDIRECT
 10 deny   udp any any eq domain
 20 deny   udp any any eq bootps
 30 deny   ip  any host 10.140.2.31
 40 deny   ip  any host 10.140.2.32
 50 permit tcp any any eq www
 60 permit tcp any any eq 443
```

> [!important] Redirect-ACL verbs are inverted This is <strong>not</strong> a packet filter. In a redirect ACL:
> 
> - `permit` → <strong>intercept</strong> this traffic and redirect it.
> - `deny` → <strong>let it pass freely</strong>, do not redirect.

|Line|Rule|Reason|
|---|---|---|
|`10`|Don't redirect DNS|Browsers cannot resolve the portal URL without DNS — block DNS and the redirect target is unreachable.|
|`20`|Don't redirect DHCP|The guest must be able to acquire an IP before any of this works.|
|`30`|Don't redirect traffic to ISE PSN 1|After the 302, the browser follows the redirect _to_ ISE. If that follow-up were intercepted, the flow would loop infinitely.|
|`40`|Don't redirect traffic to ISE PSN 2|Same reason, for the second PSN. Both must be exempt because either may handle the session.|
|`50`|Redirect HTTP|HTTP on port 80 is intercepted by the webauth parameter-map; the switch issues the 302 toward the ISE portal.|
|`60`|Redirect HTTPS|HTTPS on port 443 is intercepted as well. Requires `intercept-https-enable` in the parameter-map.|

> The redirect ACL is <strong>not</strong> statically applied to the interface — ISE pushes it dynamically per the `Redirect_Guest_Wired` authorization profile. The Access-Accept carries both the ACL name and the redirect URL.

#### WebAuth Parameter Map

```cisco
parameter-map type webauth global
 type webauth
 virtual-ip ipv4 192.0.2.1
 intercept-https-enable
```

The redirect ACL identifies _which_ traffic to catch. The parameter-map decides _what to do with it_.

|Line|Purpose|
|---|---|
|`parameter-map ... global`|Global definition — applies to any port receiving a redirect instruction from ISE.|
|`type webauth`|Operate as a CWA interceptor (handing off to the ISE portal) rather than hosting a local login page.|
|`virtual-ip ipv4 192.0.2.1`|The IP the switch uses as the source of its 302 response to the guest's browser. Spoofed and non-routable by design.|
|`intercept-https-enable`|Enable interception on TCP 443 as well. Without it, only port 80 is caught — and modern browsers default to HTTPS for nearly everything.|

##### Why `192.0.2.1`?

This address belongs to <strong>TEST-NET-1</strong>, defined in [RFC 5737](https://datatracker.ietf.org/doc/html/rfc5737) as reserved for documentation and guaranteed never to be a real routable destination. Using a real IP here would risk redirecting guest traffic to an unintended host.

##### Redirect Sequence

```
TCP session is open to the switch (handled at the SVI)
        ↓
Guest sends:   GET / HTTP/1.1
               Host: example.com
        ↓
Switch responds AS 192.0.2.1:
               HTTP/1.1 302 Found
               Location: https://<ISE-PSN>/portal/...
        ↓
Browser follows the 302 → ISE CWA portal
        ↓
TCP session to the switch closes
```

##### HTTPS Interception Caveat

When HTTPS is intercepted, the switch cannot present a valid certificate for the destination site — it terminates the TCP session before TLS handshake completes. Behaviour from here depends on the OS:

- iOS / macOS — captive-portal detection (CNA) handles this transparently in most cases.
- Android / Windows — usually similar, with the captive-portal helper.
- Manual browsing — a TLS warning is likely.

#### Guest Intercept SVI

```cisco
interface Vlan805
 description GUEST-INTERCEPT-SVI
 ip address <ip> <mask>
 no shutdown
```

The SVI gives the switch a <strong>Layer-3 presence on the guest subnet</strong>, which is what makes TCP interception possible.

Without CWA, the TCP handshake goes straight to the intended destination:

```
Guest SYN  ────────────────────────►  example.com
Guest     ◄────────────────────────  SYN-ACK from example.com
Guest ACK ────────────────────────►  example.com
TCP established with example.com
```

With CWA, the switch intercepts the SYN and completes the handshake itself using the SVI as its L3 endpoint — the guest ends up with a TCP session open to the <strong>switch</strong>, not to the destination:

```
Guest SYN  ────────────────────────►  intended destination
Guest     ◄────────────────────────  SYN-ACK from the switch
Guest ACK ────────────────────────►  switch
TCP established with the SWITCH
```

From there the webauth parameter-map issues the 302 redirect as `192.0.2.1`.

If the SVI is missing:

```
No SVI on VLAN 805
        ↓
Switch has no L3 presence on the guest subnet
        ↓
parameter-map webauth has no interface to intercept on
        ↓
Guest traffic passes through unintercepted — redirect never fires
```

##### SVI IP vs. Virtual IP

||SVI IP|Virtual IP (`192.0.2.1`)|
|---|---|---|
|<strong>What it is</strong>|Real IP assigned to the switch on VLAN 805|Spoofed IP used in the HTTP 302 response|
|<strong>Who sees it</strong>|Used internally for L3 termination|Visible to the guest's browser in the redirect|
|<strong>Purpose</strong>|Lets the switch terminate TCP sessions on the guest subnet|Triggers the browser to follow the redirect to the ISE portal|

#### Device Tracking for CWA

CWA requires [[#IP Device Tracking — Global <strong>[Required for ISE / dACL / CWA]</strong>|device tracking]] to be in place — the redirect is IP-based but the session is keyed on MAC, so something has to bind them.

> [!important] Without device tracking, CWA breaks silently MAB authenticates by MAC. The redirect ACL is IP-based. ISE-pushed policy is keyed against the session, which is itself keyed by MAC. Device tracking is what links MAC and IP. CoA also relies on this binding to find the right session to modify when the guest finally logs in.

```
MAB completes   →  session known by MAC, no IP yet
        ↓
Guest DHCP DISCOVER / OFFER / REQUEST / ACK
        ↓
Device tracking observes the exchange (DHCP snooping integration)
        ↓
IP-to-MAC binding recorded against the port
        ↓
ACL_GUEST_REDIRECT now applies to the guest's traffic
        ↓
HTTP/HTTPS interception fires → CWA flow proceeds
```

#### Service Template — `Guest_Redirect`

```cisco
service-template Guest_Redirect
```

A locally-declared shell that ISE pushes content into. ISE's MAB Access-Accept references this template name (`subscriber:service-name=Guest_Redirect`) and supplies the redirect URL and ACL name. The local declaration just needs to exist so the reference resolves.

Two reasons to have the local declaration even though it's bare:

1. <strong>Default attributes</strong> — anything you define locally inside the template acts as a fallback if ISE doesn't push the equivalent attribute.
2. <strong>Matching anchor</strong> — other policy logic can match on whether this template is currently active on a session. That is exactly how the [[#AAA-Down Cases|AAA-DOWN_GUEST_USER]] class-map detects guests caught mid-flow when ISE goes dark.

#### Verification

```cisco
show ip http server status
show parameter-map type webauth global
show ip access-lists ACL_GUEST_REDIRECT
show ip access-lists interface <int>     ! shows the ACL ISE pushed live
show access-session interface <int> details
show ip http server session-module
```

#### What Breaks If Missing

|Omission|Symptom|
|---|---|
|`ip http secure-server` + `intercept-https-enable`|HTTPS traffic isn't redirected; modern browsers (which prefer HTTPS) never reach the portal.|
|SVI on VLAN 805|Switch has no L3 presence; redirect never fires; guests sit on an open TCP connection that goes nowhere.|
|`device-tracking` on access port|No IP-to-MAC binding; redirect ACL has no IP to match; CWA fails silently.|
|`service-template Guest_Redirect`|ISE-pushed `subscriber:service-name=Guest_Redirect` doesn't resolve; redirect is ignored.|
|`dynamic-author` (CoA)|Guest logs in on portal but switch never receives the access-grant CoA — session stuck.|

---

### Guest Timeline — Wired Visitor with CWA

End-to-end view of what happens to a visitor sitting down with a laptop, from cable insertion to fully-authenticated network access.

```
T+0s    Cable plugged in
        Link up → PortFast forwards immediately
        IBNS [session-started] event fires
        → dot1x and MAB both armed (dot1x priority 10, MAB 20)

T+0s    Switch sends EAPOL-Identity-Request to laptop
        Laptop has no corporate supplicant → no response

T+28s   tx-period 7 × (max-reauth-req 3 + 1) = 28s elapsed with no EAPOL
        IBNS class DOT1X_NO_SUPPLICANT fires
        → terminate dot1x, authenticate using mab

T+28s   Switch sends RADIUS Access-Request to ISE
        Calling-Station-Id = 00-50-56-AB-CD-EF (IETF upper-case)
        Service-Type = Call-Check (MAB)
        cisco-av-pair = audit-session-id=...
        + DHCP / CDP sensor data (if already collected)

T+29s   ISE looks up the MAC
        Unknown endpoint → matches "Guest Default" authorization policy
        Sends Access-Accept with:
          • subscriber:service-name=Guest_Redirect
          • Cisco-AVPair = url-redirect-acl=ACL_GUEST_REDIRECT
          • Cisco-AVPair = url-redirect=https://<PSN>/portal/...

T+29s   Switch activates the Guest_Redirect template on the session
        IBNS [authentication-success] event fires for MAB → authorize
        Port now permits traffic but redirects HTTP/HTTPS

T+30s   Guest's laptop sends DHCP DISCOVER (passes through, ACL exempts DHCP)
        Switch's device-tracking observes the lease
        IP-to-MAC binding recorded against the port
        ip dhcp snooping binding now contains the lease

T+35s   Guest opens browser, types google.com
        Browser sends DNS query (passes through, ACL exempts DNS)
        Browser sends TCP SYN to google.com:443
        Switch (via VLAN 805 SVI) terminates the SYN at L3
        Switch sends HTTP 302 as 192.0.2.1
            Location: https://<PSN>/portal/?sessionId=...

T+36s   Browser follows the 302
        Traffic to PSN1/PSN2 (10.140.2.31/32) is ACL-exempt → passes through
        Portal page loads in the browser

T+90s   Guest fills out sponsor email / accepts AUP / logs in
        Portal completes on ISE side

T+91s   ISE sends CoA-ReAuth to the switch (UDP 3799)
        Switch matches CoA to the session by audit-session-id
        Switch tears down the redirect-bearing session and re-authenticates

T+92s   Fresh MAB Access-Request to ISE
        ISE now recognises the endpoint as a successfully-authenticated guest
        Returns Access-Accept WITHOUT the redirect attributes
          • Tunnel-Private-Group-ID = 805 (or post-auth VLAN)
          • Optional dACL = PERMIT_GUEST

T+92s   IBNS [authentication-success] → authorize applies new attributes
        Redirect ACL removed from the port
        Guest now has unfiltered internet (per the post-auth ACL)

T+92s+  Periodic accounting updates flow to ISE
        ISE Live Sessions shows the session with username = sponsor-provided email
```

---

### Happy Path Walkthrough — Domain Windows Laptop

A managed Windows machine with a working 802.1X supplicant. Every line of this config touches the flow somewhere — this walkthrough connects them.

<strong>Step 1 — Cable plugged in.</strong> PortFast forwards the port immediately (`spanning-tree portfast`); BPDU Guard is on standby (`spanning-tree bpduguard enable`). The port is in access mode in VLAN 802 (`switchport mode access` / `switchport access vlan 802`) and the session is currently in pre-auth, so [[#Access-Session Behaviour|`access-session closed`]] blocks all data plane traffic.

<strong>Step 2 — IBNS session-started event fires.</strong> The interface sources `NAC-INT-TEMPLATE`, which attaches `ISE-NAC-POLICY`. The policy's `event session-started` runs `authenticate using dot1x priority 10` and `authenticate using mab priority 20`. dot1x kicks off first because of the lower priority number.

<strong>Step 3 — EAPOL-Identity-Request goes out.</strong> `dot1x pae authenticator` makes this possible. `tx-period 7` controls retransmission interval. The supplicant on the laptop replies promptly with an EAPOL-Identity-Response containing the user/machine identity.

<strong>Step 4 — Switch builds the Access-Request to ISE.</strong> The packet is sourced from VLAN 800 (`ip radius source-interface Vlan800` in the `ISESERV` group) so ISE recognises the NAD. The attributes inside include:

- `User-Name` from the EAP identity
- `Calling-Station-Id` = `00-50-56-AB-CD-EF` (IETF upper-case, thanks to `radius-server attribute 31 mac format ietf upper-case` + `mac-only`)
- `NAS-Identifier` = the switch hostname (`attribute 32 ... format %h`)
- `NAS-IP-Address` = the VLAN 800 IP
- `Service-Type` = `Framed` (`attribute 6 on-for-login-auth`)
- `Framed-IP-Address` — populated only if device tracking has already learned it (`attribute 8 include-in-access-req`)
- Cisco-VSAs including `audit-session-id` (`vsa send authentication`)
- DHCP-derived attributes (`access-session authentication attributes filter-spec include list sensor_list`)

<strong>Step 5 — RADIUS exchange runs.</strong> ISE sends EAP messages back through the switch. The supplicant completes EAP-TLS (or PEAP-MSCHAPv2, depending on the supplicant config). ISE issues an Access-Accept with:

- No `Tunnel-Private-Group-ID` in the normal case — the static VLAN 802 already places the endpoint in the correct production VLAN. ISE only pushes a dynamic VLAN for specific roles that need to land somewhere else (e.g. contractors → 850).
- `Cisco-AVPair = ip:inacl#10=permit ip any any` (or a downloadable ACL name to fetch)
- `Class` attribute (the switch will echo this on the next reauth — `attribute 25 access-request include`)
- `Session-Timeout = 28800` + `Termination-Action = RADIUS-Request` (drives the next reauth — `authentication timer reauthenticate server`)

<strong>Step 6 — IBNS authentication-success fires.</strong> Matches the `DOT1X` class-map (because `match method dot1x` is true). The action `authorize` commits ISE's attributes to the session:

- Port stays in VLAN 802 (the static client VLAN); closed-mode releases data plane traffic now that authorization has succeeded.
- Per-session ACL is applied.
- `Critical_Access` template is <strong>not</strong> activated (this is normal-path).

<strong>Step 7 — Device tracking learns the IP.</strong> The laptop sends DHCP. `ip dhcp snooping` (global + per-VLAN) intercepts the exchange. `device-tracking attach-policy IPDT_POLICY` (with `security-level glean`) records the binding into the SISF table. DAI on VLAN 802 (`ip arp inspection vlan ...`) will now validate the laptop's ARP packets against this binding.

<strong>Step 8 — Accounting flows.</strong> `aaa accounting identity default start-stop group ISESERV` sends Accounting-Start. `aaa accounting update newinfo periodic 2880` ensures attribute changes (or 48-hour keepalives) flow to ISE so Live Sessions stays accurate.

<strong>Step 9 — Periodic reauthentication.</strong> At `Session-Timeout` expiry, dot1x reauthenticates without disrupting the data plane. Because `attribute 25 access-request include` is set, ISE recognises the reauth as a continuation of the existing session.

<strong>Step 10 — Mid-day CoA (optional).</strong> An ISE admin changes policy on this endpoint. ISE sends CoA-Reauth to UDP/3799 on the switch (`aaa server radius dynamic-author`). The switch finds the session by `audit-session-id`, triggers a new authentication, and applies the new attributes — no data plane interruption if `dot1x critical eapol` mechanics aren't in play.

<strong>Step 11 — Laptop unplugs.</strong> Link down → IBNS clears the session → Accounting-Stop sent → ISE Live Sessions removes the entry → SISF binding ages out.

---

### ISE-Side Configuration Reference

Every switch command in this note has a counterpart on the ISE side. This table maps the most common pairings so a reader can find the matching ISE configuration when troubleshooting.

|Switch-side|ISE-side counterpart|
|---|---|
|`radius server ISE01` / `key ...`|<strong>Administration → Network Resources → Network Devices</strong> — NAD entry must list the switch's IP (or subnet) and matching shared secret.|
|`ip radius source-interface Vlan800`|The IP recorded against the NAD entry must equal the VLAN 800 address.|
|`aaa server radius dynamic-author`|The CoA port (3799) and CoA shared secret on the NAD entry. ISE will send CoA from its PSN IPs.|
|Per-NAD configuration in `automate-tester`|Optionally configure ISE to expect / answer probe traffic from this NAD without flagging it.|
|`radius-server attribute 31 mac format ietf upper-case`|<strong>Settings → MAB Settings</strong> — MAC format must match. Default is fine if switches send IETF upper-case.|
|`vsa send authentication` / `accounting`|ISE policy uses `audit-session-id` to find sessions; CoA targets by this attribute.|
|`aaa authorization network default`|<strong>Policy → Policy Sets → Authorization Profile</strong> — the VLAN, dACL, redirect URL, etc. that get pushed back.|
|`service-template Guest_Redirect` (local shell)|<strong>Policy → Policy Elements → Results → Authorization Profile</strong> = `Redirect_Guest_Wired`. References the redirect ACL name.|
|`service-template Critical_Access` (local content)|Not an ISE concept — defined entirely on the switch as the local fallback.|
|Device Sensor attributes flowing in accounting|<strong>Profiling Service</strong> must be enabled on at least one PSN; profile policies use these attributes to classify endpoints.|
|`ip dhcp snooping` binding feeding device tracking|ISE relies on the `Framed-IP-Address` and Device Sensor data; without bindings, profiling collapses to MAC OUI only.|
|CWA portal URL pushed via `url-redirect`|<strong>Work Centers → Guest Access → Portals & Components → Guest Portals</strong> — URL composed from the portal's FQDN and ID.|
|Redirect ACL name (`ACL_GUEST_REDIRECT`)|The ISE authorization profile must reference the <strong>exact same name</strong> as defined on the switch.|

> [!tip] Naming alignment The single most common ISE/switch desync is the redirect ACL name. ISE pushes a string; the switch looks up an ACL by that string. A typo on either side fails silently — the switch logs nothing useful, ISE shows the auth as successful. Always copy-paste names between the two sides.v