---
categories:
  - "[[Networking]]"
  - "[[Security]]"
topic@networking:
  - "[[Networking General]]"
topic@security:
  - "[[Security General]]"
tags:
  - project
  - nac
  - cisco
  - scor/sise
  - ccnp
  - tech_doc
icon: SiCisco
iconColor: "#1BA0D7"
aliases:
  - Identity Service Engine
  - Cisco Identity Service Engine
  - ISE
---
Cisco <strong>Identity Service Engine</strong> (ISE) is a <strong>Network Access Control</strong> solution that manages access to network ensuring only authenticated, authorized, and compliant users and devices can connect. 

An ISE-based network access control solution has four components: <mark style="background: #FFB86CA6;"><strong>endpoints</strong></mark>, <mark style="background: #FFB8EBA6;"><strong>network access devices (NAD)</strong></mark>, <mark style="background: #ABF7F7A6;"><strong>Cisco ISE</strong></mark>, and <mark style="background: #FFF3A3A6;"><strong>external services</strong></mark>.
<strong>Endpoints</strong> need <mark style="background: #BBFABBA6;">network access</mark> and the <strong>network access devices (NAD)</strong> provide network access to endpoints, based on instructions from <strong>ISE</strong>. 
ISE can leverage <strong>external services</strong> to understand more about the corresponding endpoints for policy decisions.

<mark style="background: #FFB8EBA6;">The server ISE acts as the core, it's where the policies are defined</mark>. <mark style="background: #FF5582A6;">The network devices acts as the authenticator</mark> and <strong>enforce</strong> the policies from the server ISE. <mark style="background: #FFF3A3A6;">The endpoint receives the response</mark> <mark style="background: #FFB86CA6;">given by the server ISE</mark> <mark style="background: #BBFABBA6;">from the network access device</mark>. Most of the high level host endpoint have <mark style="background: #ABF7F7A6;">supplicants that allow them to communicate with the authenticator or NAD</mark>.  <mark style="background: #D2B3FFA6;">The server ISE can use external services</mark>, such as the <strong>Microsoft Active Directory</strong>, <mark style="background: #D2B3FFA6;">to get knowledge about the users</mark>. 
# ISE Server
Cisco Identity Services Engine (ISE) is an <strong>identity-based network access control</strong> and <strong>policy enforcement system</strong>. It functions as a common policy engine that enables <mark style="background: #FFF3A3A6;">endpoint access control </mark>and <mark style="background: #BBFABBA6;">network device administration</mark> for enterprises.
## Identity Management
Identity Management managed all identities for ISE, from ISE GUI admins to users that have to authenticate to ISE.

![[Pasted image 20260508100508.png]]
### Identities 
Cisco ISE has a built-in internal user database that can be used for a limited number of user accounts, referred to as internal users, also as network access users.
In identities it's possible to configure local users, they can be identities that are used to log in the ISE GUI or identities used for network access. 

This internal identity store can be used to authenticate and authorize a preconfigured account for a contractor or other temporary worker to access the wireless network, without adding them to the company’s main identity store.

Any internal user accounts configured can then be associated with a defined user identity group that sets the type of internal account being created.

![[Pasted image 20260508105029.png]]

![[Pasted image 20260508105040.png]]

### Groups 
Endpoint and User Groups, they can be used as attributes in Policy Sets.

![[Pasted image 20260508105117.png]]

#### Endpoint Identity Groups

![[Pasted image 20260513164133.png]]

Endpoint Identity Groups stores information about all the endpoint devices that connect to the network infrastructure or they can be filled through an CSV import.
It's possible to create groups to use as attributes in Policy Sets.

![[Pasted image 20260508105729.png]]

![[Pasted image 20260508105738.png]]

For new CSV import template use the <strong>Generate a Template</strong> function else use this template:
```csv
MACAddress,EndPointPolicy,IdentityGroup,PortalUser.GuestType,Description,PortalUser.Location,PortalUser.GuestStatus,StaticAssignment,User-Name,DeviceRegistrationStatus,PortalUser.CreationType,AUPAccepted,PortalUser.EmailAddress,PortalUser.PhoneNumber,FirstName,ip,Device Type,host-name,StaticGroupAssignment,MDMEnrolled,MDMOSVersion,PortalUser.LastName,PortalUser.GuestSponsor,EmailAddress,PortalUser,PortalUser.FirstName,BYODRegistration,MDMServerName,LastName,MDMServerID,Location

60:18:95:30:CA:DB,,Printers,,,,,,,,,,,,,,,,,,,,,,,,,,,,
```

##### PBA_Blacklist
All MAC Address that must be denied access to the network. 
##### PBA_Printers
All Printers MAC Addresses, there are child groups that distribute the MAC Addresses by location. 
The Printers MAC Addresses can be get from the ARP table in the core switches/routers, and they and be imported with the CSV.
##### PBA_Whitelist
MAC Addresses that must be whitelisted. Used in the MAB Access.
#### User Identity Groups

![[Pasted image 20260508110112.png]]

The User Identity Group accept only Internal Users. 
### External Identity Sources 
External Identity Sources can leverage existing external identity store for network authentication. 

![[Pasted image 20260508100508.png]]

#### External Identity Sources - Certificate Authentication Profile 
This is an important setting for certificate based authentication. 
See [[#Certificate Authentication Profile certificates|Link]].
#### External Identity Sources  - Active Directory 
Microsoft’s Active Directory (AD) is a highly available distributed database deployments. 

![[Example AD Forest.png]]

It follows the X.500 structure, like the DNS does, the AD is very tightly coupled with DNS and requires DNS for AD to function normally.

AD leverages AD domains, which are groupings of users and machine accounts, permissions, and policies.

AD domains belong to an AD forest, which is a collection of domains with trust relationships between them.

---

To join Cisco ISE to an AD domain, the ISE machine account used need to have the permissions: 
- to Search AD (to see if the ISE machine account already exists)
- to add Workstation to Domain (if it does not already exist)
- to set Attributes on the New Machine Account

To join an AD Domain go to <strong>Administration > Identity Management > External Identity Sources > Active Directory</strong>, add the domain and use a domain admin account to join. 

![[Pasted image 20260508113216.png]]

Allowed Domains set the scope for identity extraction, here it's set to everything is allowed. 

![[Pasted image 20260508113401.png]]

In this section it's possible to retrieve groups from Active Directory and use them as attributes for Policy Sets
![[Pasted image 20260508113546.png]]

### Identity Source Sequences
Identity Source Sequences (ISS) checks a series of identity sources from top to bottom, enabling a single authentication rule to check several identity sources instead of just one. It includes the selection of Certificate Authentication Profile. 

![[Pasted image 20260508113927.png]]

In the Publiacqua deployment the ISS is Publiacqua_ISS which have [[#External Identity Sources - Certificate Authentication Profile|EAP_PBA]] as CAP and only [[#External Identity Sources - Active Directory|Publiacqua_AD]] in its list. 

![[Pasted image 20260508113958.png]]

## Admin Access 
In Admin Access are configured ISE GUI permissions for each group or type of users. 

![[Pasted image 20260508114440.png]]
### Admin Access - Authorization
#### Admin Access - Authorization - Permissions
##### Menu Access
Menu Access List is used to set which menu section is allowed and which is not.

If you want to allow only a specific section of the submenu like showing only <strong>Groups</strong> while hiding the <strong>Identities</strong>, <strong>External Identity Source</strong>, and others under the menu <strong>Identity Management</strong>. You have to show <strong>Identity Management</strong>, save, then go back and hide the not allowed menu section manually.

![[Pasted image 20260508114835.png]]
##### Data Access
The Data Access List is used to configure which data a user is allowed to see or to modify. 
These changes impact the type of log one can see, so if you want to limit data access It's best put them in Read Only instead of No Access.

![[Pasted image 20260508115415.png]]

#### Admin Access - Authorization - RBAC Policy
In this section you use the permissions set in Menu Access and Data Access to configure the RBAC policy for Admin Groups. 

![[Pasted image 20260511145530.png]]
### Admin Access - Administrators
#### Admin Access - Administrators - Admin Groups
In Admin Groups, you can configure the groups for which you can build a RBAC Policy around. 

![[Pasted image 20260511145958.png]]

![[Pasted image 20260511150013.png]]

## Network Resources
In <strong>Network Resources</strong> are managed <strong>Network Access Devices</strong> (<strong>NAD</strong>), they are the point of access for an endpoint and the main enforcement point of policies set by the server ISE.
Common NAD types include the following:
- Wired Ethernet switch
- Wireless LAN controller (WLC)
- Cisco Adaptive Security Appliance (ASA)
- Cisco Firepower device
- Load balancer
- Software application that uses ISE for AAA
### Network Devices Profiles
ISE supports third-party NADs through the use of network device profiles. The NAD profiles are configured to define the capabilities and attributes of these third-party devices.

![[Pasted image 20260505104543.png]]

![[Pasted image 20260505104601.png]]

In a Cisco dominant environment the default network device profile for Cisco is enough.
#### Authentication/Authorization

![[Pasted image 20260505110156.png]]

![[Pasted image 20260505110209.png]]

It’s possible to set the conditions for which, based on the attributes received on the header, the packet is considered a Wired, Wireless, MAB, or 802.1X connection.
##### Flow Type Conditions
Enter the <strong>attributes</strong> and <strong>values</strong> that your device vendor uses for the network flows types in the <strong>Flow Type Conditions</strong>: 
- Wired MAB
- Wireless MAB
- Wired 802.1x
- Wireless 802.1x
- Wired Web Authentication
- Wireless Web Authentication

This is necessary for ISE to detect the right flow type for your device according to the attributes it uses.
###### Cisco

![[Pasted image 20260513100654.png]]

Cisco uses the <strong>attribute</strong> and <strong>value</strong> pair:

Radius:NAS-Port-Type = <strong>Ethernet</strong> for wired flows
Radius:NAS-Port-Type = <strong>Wireless - IEEE 802.11</strong> for wireless flows

Radius:Service-Type = <strong>Call Check</strong> for MAB access
Radius:Service-Type = <strong>Framed</strong> for 802.1X access
Radius:Service-Type = <strong>Login</strong> for Web Portal access
###### ArubaWireless

![[Pasted image 20260513105840.png]]

<strong>Aruba Networks</strong> views all wireless access as a user initiating a standard data session. Because of this, the Aruba controller sends the exact same generic `Service-Type` for both authentication methods.

Radius:NAS-Port-Type = <strong>Wireless - IEEE 802.11</strong> for wireless flows

Radius:User-Name = <strong>Radius:Calling-Station-ID</strong> for MAB access

Radius:Service-Type = <strong>Login</strong> for all wireless 
##### Attribute Aliasing
<mark style="background: #FF5582A6;"><strong>Attribute Aliasing</strong> allows a <strong>NAD Profile</strong> to map vendor-specific attributes to a common attribute so that policy rules can use the friendly name</mark>. 
It simplifies attribute selection, reduces the number of authentication/authorization policy rules required for different vendor devices, and is potentially less error prone. 
<mark style="background: #ADCCFFA6;">For example, the Wireless SSID involved in a flow could be included in the <strong>Airespace-Wlan-ID</strong>, <strong>Aruba-ESSID-Name</strong>, or <strong>Called-Station-ID</strong> depending on the type of NAD involved</mark>. They can all be aliased to <strong>SSID</strong>.
##### Host Lookup
<strong>Host Lookup</strong> allows you to define which attributes and protocols your device uses for MAB.
Different (non-Cisco) vendors populate the RADIUS Calling-Station-ID and password attributes differently while doing a MAB authentication. For Cisco NADs doing MAB, enabling the Process Host Lookup option is sufficient.
#### Permissions

![[Pasted image 20260505111657.png]]

This section defines which <mark style="background: #FFB86CA6;">attributes your device uses for setting a VLAN or ACL</mark>. 
<mark style="background: #FFF3A3A6;">They may be IETF standard attributes or vendor specific</mark>. These are usually published in your device’s Admin Guide.

For the VLAN permission, you can specify a single RADIUS attribute (e.g. Aruba-User-VLAN).

For the ACL permission, you can specify a single RADIUS attribute, to be used for setting a named ACL on NADs relevant to the current NAD profile.
#### Change of Authorization (CoA)

![[Pasted image 20260505112153.png]]

This section allows you to define what CoA capabilities your device has. 
Refer to your device documentation for information – look for references to terms like “<strong>RFC 5176</strong>”, “<strong>Change of Authorization</strong>” or “<strong>CoA</strong>”. 

Most non-Cisco devices with RFC 5176 support will support “Push” and “Disconnect”, but not Re-authenticate, so if unsure try enabling the two checkboxes marked “RFC 5176”.

<mark style="background: #ABF7F7A6;">While RFC 5176 defines the types of CoA requests, the required attributes in the requests vary from device to device</mark>. Some devices are very particular about attributes sent in the CoA request.

If your CoA requests are getting a CoA ‘NAK’ back from the device, check some of the following tips:
- Some require the RADIUS User-Name attribute from the access-request to be included in CoA requests
- Some do not accept both Calling-Station-ID and Acct-Session-ID sent in the same request (send one)
- Some do not accept other vendors VSAs in a request
- Some devices can be configured to expect (or not) Event-Timestamp and the CoA configuration above must match
#### URL Redirect
This section defines the device’s URL Redirect capabilities. 
URL redirection is necessary for complex flows like Guest, BYOD and Posture. It needs to be capable of redirecting to an ISE portal, i.e. local web auth is not sufficient.

There are two general types of URL redirect found on devices; <strong>static</strong> and <strong>dynamic</strong>. 

Static means a URL has to be configured into the device (manually). It does not support being told where to redirect dynamically via a RADIUS attribute. Typically, you copy and paste the ISE portal URL into the device’s configuration.

The other type is <strong>dynamic URL</strong> – this is where <mark style="background: #FF5582A6;">ISE can use a RADIUS attribute to tell the device where to redirect to dynamically</mark>. It is not necessary to manually configure the device. 

The <strong>Parameter Names</strong> are arguments passed by the device in the redirect URL. ISE needs to be told the names of these parameters so it can extract them correctly from the URL. <mark style="background: #BBFABBA6;">It uses them to identify the client and session, as well as the original URL the client was trying to get to so that it can redirect it</mark>.

### Network Devices Groups 

![[Pasted image 20260505125347.png]]

Network Device Groups can be set to define NAD attributes that will be used in policy sets, they can be whatever you want to. Here there are Device Types and Locations. 
### Network Devices

![[Pasted image 20260505125643.png]]

To add a NAD, navigate to <strong>Administration > Network Resources > Network Devices</strong> and click <strong>Add</strong>. 

They can be configured with Network Device Profile, Model Name, Software Version or with the attributes set in the Network Device Groups. 

The network device is added to ISE as an object.

The object has a shared secret key for RADIUS, TACACS authentication settings, SNMP community strings, and TrustSec configuration. The RADIUS shared secret key must match the configured key on the NAD exactly.

Each NAD object must be configured with one or more IP addresses. Each NAD can be assigned to one NDG of each type: one Location group, one Device Type group, and one of each manually created top-level NDGs.

![[Pasted image 20260505125842.png]]

The SNMP Settings section is where the SNMP community for the NAD is configured, the ISE will use this to query the NAD for profiling attributes such as CDP and LLDP cache information. The SNMP setting should be configured only for device that do not use the device sensor to send ISE profiling data within RADIUS accounting packets.

The NADs can be imported with a CSV. 
## Policy 
In Policy section are defined the Policy Sets, Dictionaries, Conditions and Results. 
### Dictionaries
Cisco ISE dictionary attributes are pre-defined or custom RADIUS and system-level parameters used to create policy conditions, such as device type, user group, or location, for authentication and authorization. 

These parameters are built on System and Vendor-Specific Attributes:
- <strong>IETF RADIUS Attributes:</strong> The default base, defined by the Internet Engineering Task Force.
- <strong>System-Defined Dictionaries:</strong> Read-only dictionaries populated during installation, covering core system data and network protocols.
- <strong>Vendor-Specific Attributes (VSAs):</strong> Dictionaries for specific hardware vendors, which can be imported or created, often used to define RADIUS Vendor-Specific Attributes.
- <strong>External Identity Sources:</strong> Dictionaries generated by LDAP or Active Directory, allowing ISE to use directory groups and attributes in policy creation.
- <strong>User-Defined Dictionaries:</strong> Custom attributes managed via the GUI, often used for profiling or specific endpoint data

These attributes, found in <strong>Policy > Policy Elements > Dictionaries</strong>, allow network admins to build granular policies.
#### Radius Dictionary

![[Pasted image 20260513115115.png]]

##### NAS-Port-Type

![[Pasted image 20260513115848.png]]

Radius Attribute that indicates the port type. 
Common values are:
- <strong>Wireless - IEEE 802.11 (Value 19):</strong> Sent by Wireless LAN Controllers (WLCs) when a user connects via Wi-Fi.
- <strong>Ethernet (Value 15):</strong> Sent by a network switch when a user plugs directly into a physical wall port.
- <strong>Virtual (Value 5):</strong> Typically indicates an incoming VPN connection or an administrator initiating an SSH session.
- <strong>Async (Value 0):</strong> Used almost exclusively when an administrator connects directly to a switch via a physical Console port.
##### Service - Type

![[Pasted image 20260513120458.png]]
Service-Type is a RADIUS attribute (Attribute 6) that defines the nature of the network access request being made, allowing ISE to understand how a user or device is trying to connect.

Common Service-Type values:
- <strong>Framed (Value: 2)</strong>: Indicates standard network access control (NAC) sessions, such as Wired or Wireless 802.1X and VPN connections.
- <strong>Login / Executive (Value: 1)</strong>: Indicates terminal/shell access. It is typically present when an administrator attempts to log into the Command Line Interface (CLI) of a switch, router, or firewall.
- <strong>Call Check (Value: 10)</strong>: Used specifically for MAC Authentication Bypass (MAB). It informs ISE that the device is authenticating strictly via its hardware MAC address without user credentials.
- <strong>Outbound (Value: 5)</strong>: Used during certain tunneling or secondary authentication handshakes.

For the switch to send this data it needs to be configured with `radius-server attribute 6 on-for-login-auth

##### Called-Station-ID

![[Pasted image 20260513121704.png]]

This attribute identifies the <strong>infrastructure access point</strong> or <strong>port where the endpoint is physically or logically connecting</strong>.

The contents change drastically depending on whether the connection is <strong>Wired</strong> or <strong>Wireless</strong>:

1. On Wireless Networks (Sent by WLCs)

It transmits the MAC address of the Access Point's radio (BSSID) combined with the name of the Wi-Fi network (SSID).

- <strong>Format:</strong> `AA-BB-CC-DD-EE-FF:Corporate-Wi-Fi` or `Corporate-Wi-Fi` (depending on configuration).
- <strong>Why it is notable in ISE:</strong> This allows you to write specific rules based on the Wi-Fi network name. You can create a policy rule stating: _If `Radius.Called-Station-ID ENDS_WITH :Guest-Wi-Fi`, push the Guest web-portal redirect._

2. On Wired Networks (Sent by Switches)

It traditionally transmits the MAC address of the physical switch chassis or the specific VLAN/port identifier where the Ethernet cable is plugged in.

- <strong>Format:</strong> Typically the MAC address of the switch interface or the bridge group ID.

##### Calling-Station-ID

![[Pasted image 20260513121938.png]]

This attribute identifies the <strong>endpoint device</strong> that is requesting access to the network.

- <strong>What it contains:</strong> In almost all modern enterprise networks (Wired, Wireless, and VPN), it transmits the <strong>MAC address</strong> of the client machine, smartphone, or IoT device.
- <strong>Format:</strong> The format depends on the brand of your network switch or wireless controller. Common formats include:
    - `aa-bb-cc-dd-ee-ff`
    - `aabb.ccdd.eeff`
    - `AA:BB:CC:DD:EE:FF`
- <strong>Why it is notable in ISE:</strong>
    - <strong>MAC Authentication Bypass (MAB):</strong> For headless devices like printers or security cameras, ISE copies the MAC address from this attribute and checks it against the internal endpoint database.
    - <strong>Device Profiling:</strong> The ISE Profiler evaluates this MAC address vendor prefix (OUI) to help determine if the device is an Apple iPhone, a Windows workstation, or an IP phone.
##### Dynamic VLAN Assignment Attributes

For a network switch to accept a dynamic VLAN assignment from Cisco ISE, it must receive three IETF helper attributes in the [[#Authorization Profiles|Authorization Profile]].

<strong>`Tunnel-Private-Group-ID` (RADIUS Attribute 81)</strong> is a standard IETF attribute used as an <strong>Authorization Result</strong> to dynamically assign a user or device to a specific <strong>VLAN</strong> upon successful authentication.

![[Pasted image 20260513152509.png]]

<strong>`Tunnel-Type` (RADIUS Attribute 64)</strong> is an industry-standard IETF attribute used during the authorization phase to specify the <strong>tunneling protocol or virtualization method</strong> that a network device must apply to a user's session.
<strong>VLAN (Value: 13)</strong> is  By far the most common value used in Cisco ISE. It instructs the switch to dynamically shift the physical access port into a specific VLAN ID.

![[Pasted image 20260513153658.png]]

<strong>`Tunnel-Medium-Type` (RADIUS Attribute 65)</strong> is an industry-standard IETF attribute used during authorization to tell the network device the <strong>specific transport medium protocol</strong> running over the virtual tunnel.
<strong>802 (Value: 6)</strong> is the most heavily used value in modern enterprise deployments. It indicates standard IEEE 802 networks, which includes all campus Ethernet switches (802.3) and enterprise Wireless LANs (802.11). 
<strong>IPv4 (Value: 1):</strong> Used in Layer 3 tunneling architectures where packets travel natively over an IP backbone.

![[Pasted image 20260513153903.png]]

#### Cisco Dictionary

![[Pasted image 20260513115229.png]]

##### cisco-av-pair

![[Pasted image 20260513122119.png]]

In Cisco ISE, <strong>`cisco-avpair`</strong> is a Vendor-Specific Attribute (VSA) classified under the <strong>RADIUS > Cisco</strong> dictionary (Vendor ID: `9`, Sub-ID: `1`)

The syntax always follows a strict string format: `protocol:attribute=value`.

Common uses:

<strong>Central Web Authentication (CWA)</strong> and Guest Portals: When an unknown device connects to the network, ISE uses two specific AV pairs to tell the switch to intercept the user's web browser traffic and redirect them to a login portal:

 - <strong>url-redirect</strong>: Tells the switch exactly where the ISE Guest or Hotspot portal is hosted. 
 ```cisco-av-pair = url-redirect=https://guestportal1.publiacqua.it:port/portal/gateway?sessionId=SessionIdValue&portal=4f145223-7d12-411b-a511-92abfafef0d8&action=cwa```

- <strong>url-redirect-acl</strong>: Specifies the name of the local Access Control List (ACL) pre-configured on the switch that defines what traffic should be redirected versus allowed (e.g., allow DNS and DHCP, but redirect HTTP).
```cisco-av-pair = url-redirect-acl=ACL_GUEST_REDIRECT```

<strong>Network Controller Access Control (Role-Based Access)</strong>: When managing logins to Cisco fabric platforms like Cisco DNA Center (Catalyst Center) or Cisco APIC (ACI) via RADIUS, ISE passes the exact user roles through an AV pair:

Cisco DNA Center / Catalyst Center Login:
```cisco-av-pair = ROLE=SUPER-ADMIN-ROLE```

Cisco APIC / ACI Fabric Login:
```cisco-avpair=shell:domains=all/admin/```

<strong>Administrative Privilege Levels</strong> (Switch CLI via RADIUS): If you are using RADIUS (instead of TACACS+) to secure administrative command-line access to Cisco switches and firewalls, you must use an AV pair to drop the administrator directly into the privileged executive mode (`enable`):
<strong>shell:priv-lvl</strong>: Grants immediate execution privileges.
```cisco-av-pair = shell:priv-lvl=15```
#### Network Access Dictionary
##### UseCase

![[Pasted image 20260514153230.png]]

`NetworkAccess:UseCase` is an internal system enumeration attribute used to track the contextual state of an endpoint's session.

When this attribute evaluates to `Guest Flow` (formatted as `NetworkAccess:UseCase = GuestFlow`), it explicitly means that <strong>the endpoint has successfully completed web authentication (WebAuth) via an ISE guest portal and is now executing a post-portal network re-authorization</strong>.

### Conditions
Cisco ISE policy conditions are rule-based elements (attributes, operators, values) used to define network access, profiling, posture, and guest services. They enable granular control, allowing policies based on user identity, device type, location, or time. Conditions can be Simple (one attribute) or Compound (combined using AND/OR) and are managed within the Conditions Studio
#### Library Conditions
Cisco ISE <strong>library conditions</strong> are pre-configured, reusable policy elements found under <strong>Policy > Policy Elements > Conditions</strong>. They allow administrators to define complex logic once (e.g., specific device types, time ranges, or location attributes) and reuse them across multiple authorization policies, simplifying policy management and reducing errors.

![[Pasted image 20260512150602.png]]

##### EAPs
The EAPs condition check the if the client request is using one of these [[#Allowed Protocols|EAP protocols]].
The EAP protocols inside the conditions are PEAP, EAP-TLS and TEAP, the admin should be using one of these protocols. 

![[Pasted image 20260514110551.png]]

##### ID_Admin_User
Users in the AD group [[#External Identity Sources - Active Directory|InfrastructureAdmin]].

![[Pasted image 20260514112106.png]]

##### ID_Domain_User
Check if the user is in the AD group [[#External Identity Sources - Active Directory|Utenti_Publiacqua]].

![[Pasted image 20260514111525.png]]

##### Blacklist 
MAC Addresses in [[#PBA_Blacklist|PBA_Blacklist]].

![[Pasted image 20260514114124.png]]

##### Whitelist
MAC Addresses in [[#PBA_Whitelist|PBA_Whitelist]].

##### Authentication Passed
Check if the AuthenticationStatus is a Passed

![[Pasted image 20260514110848.png]]
##### Authentication Failed
Check if the AuthenticationStatus is a Failed

![[Pasted image 20260514111110.png]]
##### TEAP_Machine
This condition will match if the client using TEAP protocol have the [[#Domain Computer Certificate|machine certificate]] pass the authentication but fail the [[#Domain Users Certificate|user certificate]] authentication. 

![[Pasted image 20260514111237.png]]

##### Not_TEAP
This condition is used if you want to get a computer certificate but you don't want the computer certificate to pass from TEAP EAP protocol.

![[Pasted image 20260514113635.png]]
##### Client Authorizations
Client Authorizations conditions check if the client user is [[#ID_Domain_User]] and if the EAP protocol they use is PEAP or TEAP. The domain users should use only TEAP and PEAP in rare occasions.

![[Pasted image 20260514140414.png]]

##### Guest_Flow
Condition is hit if the client request packet has attribute [[#UseCase|NetworkAccess:UserCase]].

When this attribute evaluates to `Guest Flow` (formatted as `NetworkAccess:UseCase = GuestFlow`), it explicitly means that <strong>the endpoint has successfully completed web authentication (WebAuth) via an ISE guest portal and is now executing a post-portal network re-authorization</strong>.

![[Pasted image 20260514155208.png]]

#### Smart Conditions
Cisco ISE smart conditions are pre-defined, intelligent policy building blocks designed to simplify policy rule creation by abstracting complex RADIUS attribute-value pairs into human-readable, usable logic. 

These RADIUS attribute-value pairs are mapped from [[#Authentication/Authorization|Network Device Profiles]] 

![[Pasted image 20260512145913.png]]

![[Pasted image 20260512150521.png]]

### Policy Sets

![[Pasted image 20260512103918.png]]

<strong>Policy Sets</strong> are high-level containers that group authentication and authorization rules into manageable logical buckets. 
Instead of managing one giant list of rules, policy sets allow you to organize network access by use case, such as separating Wired, Wireless, VPN, or Guest access.

Each policy set functions as a "rule book" evaluated from the top down. Once a request matches a policy set's top-level conditions, ISE evaluates the internal policies in this order: 
- <strong>Top-Level Condition</strong>: The "gatekeeper" that determines if a request belongs in that specific set. If the request is Wireless, Wired, from a specific location, time ecc.
- <strong>[[#Allowed Protocols|Allowed Protocols]]</strong>: Defines which protocols (like PAP, CHAP, or EAP-TLS) are permitted for the initial connection.
- <strong>Authentication Policy</strong>: Verifies the identity of the user or device using identity sources like Active Directory or internal databases.
- <strong>Authorization Policy</strong>: Grants specific permissions—such as VLAN assignment, Security Group Tags (SGTs), or Downloadable ACLs (dACLs)—based on the user's role or device posture.

The Top-Level Condition in this deployment are <strong>Wired</strong>, <strong>Wired_Monitor</strong>, <strong>Wireless</strong> and <strong>DNAC</strong>, they distribute the client requests based on the type of connection (Wired or Wireless) and if the Device Type is a DNAC-server. 

![[Pasted image 20260512152559.png]]

The <strong>Wired_Monitor</strong> Top-Level Condition is used temporarily in Cisco ISE monitoring deployments alongside the <strong>Network Access Device</strong> command `no access-session closed` to gather visibility data without restricting network access. 

In this deployment model, the system only generates ACCEPT or DENY responses, and all DENY requests are ignored to ensure clients maintain uninterrupted connectivity. 

Because Cisco ISE functions strictly as an information-gathering tool in this phase, authorization profiles must not apply Downloadable ACLs or VLAN changes, as these active policies cannot be ignored and will directly disrupt user network access.

The active deployment logic is:
- Top Rule Condition = Wired, Wireless or DNAC
- Allowed Protocol
- Authentication Policy
	- Condition = MAB or 802.1X
	- Identity Store = [[#Endpoint Identity Groups|Internal Endpoint]] for MAB or [[#Publiacqua_ISS]] for 802.1X.
- Authorization Policy
	- Is computer in Blacklist?
	- Is user an Admin?
	- Is User not logged on?
	- Is Client a normal Domain User with Domain Computer?
	- Is the Client a PC that must be always accessible in RDP?
	- Is the computer in Whitelist?
	- Guest Redirect
#### Authentication Policy

![[Pasted image 20260512154735.png]]

An authentication policy is a set of rules and criteria used to verify the identity of a user or device before they are allowed access to a system. 
In Cisco ISE, it specifically determines how a connection request should be identified and where to look up their credentials (like [[#External Identity Sources - Active Directory|Active Directory]] or an [[#User Identity Groups|internal database]])

There are three predefined policies:
##### MAB (MAC Authentication Bypass)
<strong>MAC Authentication Bypass (MAB)</strong> is a fallback network access control method that uses a device's <strong>MAC address</strong> to grant or deny access. It is primarily used for "headless" devices that cannot run an 802.1X supplicant, such as printers, IP phones, cameras, and IoT equipment.

When a device connects to a switch port configured for 802.1X/MAB, the following process typically occurs:
1. <strong>Detection</strong>: The switch initially tries to authenticate the device via 802.1X.
2. <strong>Fallback</strong>: If the device fails to respond to 802.1X requests (usually after a timeout), the switch "falls back" to MAB.
3. <strong>RADIUS Request</strong>: The switch sends a RADIUS Access-Request to Cisco ISE, using the device's MAC address as both the username and password.
4. <strong>ISE Decision</strong>: ISE checks the MAC address against all MAC addresses in the [[#Endpoint Identity Groups|Internal Endpoints]] database or performs <strong>Profiling</strong> to identify the device type.
5. <strong>Authorization</strong>: Based on your configured <strong>Policy Sets</strong>, ISE sends back a RADIUS Access-Accept with specific permissions, such as a VLAN assignment or a Downloadable ACL (dACL).

In the current deployment even if the MAB check fails, the server ISE allow the authentication request to continue to the authorization policies, where they will be met with [[#Guest Redirect|Guest Redirect]] Authorization Policy. 

The conditions for MAB is the [[#Flow Type Conditions|predefined Wired_Mab]].
##### Dot1X (802.1X)
Dot1X (802.1X) should be the most used/default authentication policy. 

It's the authentication policy where the client has a supplicant ([[#Group Policy Management|Windows Native Supplicant]]) that uses an [[#Extensible Authentication Protocols|EAP]] protocol to authenticate itself to the ISE server.

The condition for the request to hit this authentication policy is the predefined [[#Smart Conditions|Wired_802.1X]] and it check the user identity in the Identity Store [[#Identity Source Sequences|Publiacqua_ISS]].
If the user is found in the ISS then it is authenticated and the request is passed for authorization policy check. 
If it's not found in the Identity Store, it is also passed for authorization policy check, though it will probably hit the [[#Guest Redirect]] policy.
##### Default
The Default authentication policy is a catch all type of policy, set to deny all request.
It's usually used for requests that the policies before this one could not catch. 
In this deployment it's shouldn't be hit at all. 
#### Authorization Policy
Authorization Policies decides which [[#Authorization Profiles]] does the client get.

![[Pasted image 20260514115226.png]]

The authorization policies order is first match, the client get authorization profile of the fist authorization policy it hits.
##### Deny Access
The fist authorization policy is to check if the client computer is on the [[#PBA_Blacklist|Blacklist]], if the MAC address is found on the [[#PBA_Blacklist|Endpoint Identity Group]] they will reject the client request, if it's not found then the policy is not hit and ISE will check the following policy. 
##### Admin Access
Admin Access allows all users in the admin AD group to get the authorization profile for the VLAN Admin, which is set to VLAN 850. The authorization profile is configured in the same way as the one for [[#Vlan_802_Lan_Client|VLAN 802]] except for the VLAN ID.

The condition to hit this policy is that [[#EAPs|the client must use an EAP protocol]], [[#ID_Admin_User|the user must be in the Admin group]] and [[#Authentication Passed|the authentication result is a pass]].

The authorization profile is configured to give only the VLAN Admin while the admin permissions are provided by the network and security configuration for VLAN Admin.
##### Machine Access
The Machine Access an authorization protocol created for situations where the [[#Domain Users Certificate|User Certificate]] is not available: 
- User is not logged-on the domain computer
- New user needs to access a domain computer
- Problems with user certificate
In these case the Machine Access policy provides the client with Internet access and connection to Domain Controller and the Certificate Authority Server. 

The conditions to hit Machine Access are [[#TEAP_Machine]] and [[#Authentication Passed]]. 
The authorization profiles it provides is [[#Pre-Auth-profile]].
##### Client Access
The Client Access is the default policy for Publiacqua Domain Users, when this policy is hit the user get access to VLAN 802 which is the LAN Client. 

The conditions to hit this policy is [[#Client Authorizations]] and [[#Authentication Passed]]. 

The Authorization Profiles is [[#Vlan_802_Lan_Client]].
##### RDP Access
The RDP Access authorization policy is used for computer that for most of the time must be accessible through RDP but are not servers. 
The Machine Access DACL is too limited, so there is a specific policy that gives access to VLAN 802.

The hit conditions are EAP-TLS machine certificate, [[#Not_TEAP]], and [[#Authentication Passed]].

The Authorization Profiles is [[#Vlan_802_Lan_Client]].
##### MAB Access
MAB Access is for computer or devices that for reasons don't have a supplicant to send 802.1X authentication packets. At the moment the authorization profiles for this access is also VLAN 802

The hit conditions are [[#Smart Conditions|Wired_MAB]], [[#PBA_Whitelist|Whitelist]] and [[#Authentication Passed]]. 

The Authorization Profiles is [[#Vlan_802_Lan_Client]]. 
##### Guest Access
The Guest Access is used together with [[#Guest Redirect]] and it will be hit only if the client user authenticate to [[#Guest Redirect]]. 

The hit condition is [[#Guest_Flow]].
The Authorization Profiles is VLAN Guest which is VLAN 805. It has the same configuration of [[#Vlan_802_Lan_Client|VLAN 802]] except for the VLAN ID.
##### Guest Redirect
The Guest Redirect authorization protocol is the catch all for all devices and users not authorized/authenticated and for guest users. 

The hit condition is all [[#Authentication Failed]], [[#Smart Conditions|Wired_MAB]] or [[#Smart Conditions|Wired_802.1X]]. 
The Authorization Profiles is [[#Redirect_Guest_Wired]], if the Guest Authentication is a success it will hit the default [[#UseCase|Guest Flow]] condition of [[#Guest Access]], and the client will have Internet access. 
### Results
#### Policy - Results - Authentication
Authentication Results are results from authentication policy checks, if the top rule authentication policy is passed, the server ISE will check the Allowed Protocols.
##### Allowed Protocols
After the conditions are matched in a top-level rule,  ISE determines what authentication protocols are permitted for that policy set. If the user send a authentication request that is not in the allowed protocol, the request is denied.

<strong>Policy > Policy Elements > Results > Authentication > Allowed Protocols</strong>

In the current deployment:

![[Screenshot 2026-05-12 at 11-06-37 Identity Services Engine.png]]
- Process Host Lookup for MAB Access
- EAP-TLS for Admin Users who uses MacOs and for RDP Access
- PEAP MSCHAPv2 for occasional clients
- PEAP EAP-TLS for Admin Users with non domain computers
- TEAP for default Domain Users

The allowed protocols definition:
###### Extensible Authentication Protocols 
- <strong>PAP</strong>: With <strong>Password Authentication Protocol</strong> (<strong>PAP</strong>), the username is sent in plaintext, and the password is optionally encrypted.
  
- <strong>CHAP</strong>: With <strong>Challenge Handshake Authentication Protocol</strong> (<strong>CHAP</strong>), the username and password are encrypted using a challenge sent from the server. CHAP is not often used with network access.
  
- <strong>Extensible Authentication Protocol (EAP) types</strong>: <strong>EAP</strong> is an authentication framework that provides for the transport and use of identity credentials. EAP encapsulates the usernames, passwords, and certificates that a client is sending for purposes of authentication. There are many different EAP types, each with benefits and downsides. (802.1X defines EAP over LAN.)
    - <strong>EAP-MD5</strong>: EAP-MD5 uses a Message Digest algorithm to hide the credentials in a hash. The hash is sent to the server, where it is compared to a local hash to see if the credentials are accurate. EAP-MD5 does not have a mechanism for mutual authentication. This means the server is validating the client, but the client does not authenticate the server. EAP-MD5 is common on some IP phones, and it is also possible for some switches to send MAB requests within EAP-MD5.
    - <strong>EAP-TLS</strong>: This EAP type uses TLS (Transport Layer Security) to provide secure identity transactions. EAP-TLS is considered universally supported across many different operating systems and mobile devices. EAP-TLS uses X.509 certificates and provides the ability to support mutual authentication, where the client must trust the server’s certificate and vice versa. It is considered among the most secure EAP types because password capture is not an option; the endpoint must have the private key.
- <strong>Tunneled EAP types</strong>: The previous EAP types transmit credentials immediately. These following EAP types of form encrypted secure tunnels first and then transmit the credentials within the tunnel
    - <strong>PEAP</strong>: <strong>Protected EAP</strong> (<strong>PEAP</strong>), is an EAP tunnel type. PEAP forms a potentially encrypted TLS tunnel between the clients and server using the X.509 certificate on the server in much the same way an SSL tunnel is established between a web browser and a secure website. After the tunnel has been formed, PEAP uses another EAP type as an “inner method” to authenticate the client using EAP within the outer tunnel. PEAP supports the following inner methods:
        - <strong>EAP MSCHAPv2</strong>: Using this inner method, the client’s credentials are sent to the server encrypted within an MS-CHAPv2 session. It allows for simple transmission of username and password or even computer name and computer password to the RADIUS server, which authenticates them to Active Directory.
        - <strong>EAP-GTC</strong>: <strong>EAP-Generic Token Card</strong> (<strong>GTC</strong>) is an inner method created by Cisco as an alternative to MS-CHAPv2 that allows generic authentications to virtually any identity store, including one-time-password (OTP) token servers, LDAP, Novell eDirectory, and more.
        - <strong>EAP-TLS</strong>: PEAP is capable of using EAP-TLS as an inner method. EAP-TLS adds an additional layer of security by tunneling the EAP authentication.
    - <strong>EAP-FAST</strong>: <strong>Flexible Authentication via Secure Tunneling (FAST)</strong> is very similar to PEAP. Cisco created FAST as an alternative to PEAP that allows for faster re-authentication and supports faster wireless roaming. FAST forms a TLS outer tunnel and then transmits the client credentials within that TLS tunnel. Where FAST differs from the PEAP is in the ability to use Protected Access Credentials (PACs). A PAC can be thought of as a secure cookie that is stored locally on the host as proof of a successful authentication. The Windows native supplicant does not support EAP-FAST. Instead, the AnyConnect software client with the Network Access Manager (NAM) can be installed on endpoints running Windows Vista and later. NAM acts as the supplicant for the endpoint, which allows Windows to support arrange of new EAP options. EAP-FAST supports the following inner methods:
        - <strong>EAP MSCHAPv2</strong>
        - <strong>EAP-GTC</strong>
        - <strong>EAP-TLS</strong>
        - <strong>EAP chaining with EAP-FASTv2</strong>: Windows AnyConnect NAM software. As an enhancement to EAP-FAST, a differentiation was made <strong>to have both a user credential and a machine credential authenticated</strong>. These credentials can be certificates or username and password. This provides ISE administrators the ability to validate that a machine is an authenticated domain computer and to validate the credentials of the user. EAP chaining makes it possible for multiple credentials to be authenticated within a single EAP transaction.
    - <strong>EAP-TTLS</strong>: It encapsulates a TLS session by using a handshake phase and a data phase. During the handshake, the server authenticates itself to the client or they both mutually authenticate using standard TLS. The server can then use that established tunnel to authenticate the client. Versions of Windows prior to Windows 8 do not support EAP-TTLS natively. However, Microsoft has included native supplicant support in Windows 8 and later. The EAP inner methods that are accepted with EAP-TTLS include PAP, CHAP, MS-CHAPv1, MS-CHAPv2, and EAP-MD5.
	-  <strong>TEAP</strong>: It enables secure communication between a peer and server using TLS to establish a mutually authenticated tunnel. EAP-Chaining is possible.
#### Policy - Results - Authorization
Authorization Results are the results for each authorization policy. 
##### Authorization Profiles
Authorization Profiles are reusable policy objects that define the specific access permissions, such as VLANs, Downloadable ACLs (dACLs), or security group tags, granted to a user or device after successful authentication and passing the authorization policy.
![[Pasted image 20260512122923.png]]
###### Pre-Auth-profile

![[Pasted image 20260512124255.png]]

The Pre-Auth-Profile is used by the Authorization Policy Machine Access and it sends a ACCESS_ACCEPT with the DACL [[#Pre-Auth|Pre-Auth]] that limit the computer network access to Internet, Domain Controller and Certificate Authority.

This DACL is used for computer that have authenticated with machine certificate but not with user certificate for various reasons:
- The user is not logged-on, so the user certificate is not available
- There change in user happening 
- The user does not have a certificate enrolled

For these case the DACL allow the connection to Internet, Domain Controller and Certificate Authority for the update of GPO, and enrollment of user certificates.
###### Vlan_802_Lan_Client

![[Pasted image 20260512142840.png]]

Vlan_802_Lan_Client should be the default Authorization Policy for most of domain users. 
It sends the VLAN for clients and the re-authentication timer.
- <strong>Access Type = ACCESS_ACCEPT</strong> : Authentication status is a pass
- [[#Dynamic VLAN Assignment Attributes|Tunnel-Private-Group-ID]] = 1:802 : VLAN 802
- [[#Dynamic VLAN Assignment Attributes|Tunnel-Type = 1:13]] : This specifies the tunneling protocol being used. In this context, value 13 explicitly tells the device that the "tunnel" is a Virtual LAN (VLAN).
- [[#Dynamic VLAN Assignment Attributes|Tunnel-Medium-Type = 1:6]] : This indicates the transport medium. Value 6 represents IEEE 802, which includes Ethernet and wireless media.
###### Redirect_Guest_Wired

![[Pasted image 20260512143139.png]]

The Redirect_Guest_Wired is the first Authorization Profile for guest users, it send a redirection URL to the CWA guest portal.  
- <strong>Access Type = ACCESS_ACCEPT</strong> : Authentication status is a pass
- [[#Dynamic VLAN Assignment Attributes|Tunnel-Private-Group-ID = 1:805]] : Put the client in VLAN 805
- [[#Dynamic VLAN Assignment Attributes|Tunnel-Type = 1:13]] : This specifies the tunneling protocol being used. In this context, value 13 explicitly tells the device that the "tunnel" is a Virtual LAN (VLAN).
- [[#Dynamic VLAN Assignment Attributes|Tunnel-Medium-Type = 1:6]] : This indicates the transport medium. Value 6 represents IEEE 802, which includes Ethernet and wireless media.
- [[#cisco-av-pair|cisco-av-pair = url-redirect-acl=ACL_GUEST_REDIRECT]] : This indicate which local access list the client must use. 
- [[#cisco-av-pair|cisco-av-pair = url-redirect=https://guestportal1.publiacqua.it:port/portal/gateway?sessionId=SessionIdValue&portal=4f145223-7d12-411b-a511-92abfafef0d8&action=cwa]] : The redirect guest portal from the CWA
- <strong>Session-Timeout = 43200</strong> : The timer for the session
- <strong>Termination-Action = Default</strong> : When the timer of Session-Timeout runs out, kick the user off and make them start over
- <strong>Idle-Timeout = 7200</strong> : Tells the switch or WLC to disconnect the user if their device is completely silent for 2 hours
- <strong>cisco-av-pair = subscriber:service-name=Guest_Redirect</strong> : This tells the switch to activate the local service-template [[#Guest_Redirect|Guest_Redirect]], in this deployment the Guest_Redirect service-template is empty. It's used to trick the switch to match for <strong>class-map type control subscriber match-all AAA-DOWN_GUEST_USER</strong>.
##### Downloadable ACLs
They are Access Lists that are configured on the server ISE and are meant to be sent dynamically to the NAD that calls it. 

![[Pasted image 20260512124736.png]]

##### Pre-Auth
This DACL is used for computer that have authenticated with machine certificate but not with user certificate for various reasons:
- The user is not logged-on, so the user certificate is not available
- There change in user happening 
- The user does not have a certificate enrolled
- ect

For these case the DACL allow the connection to Internet, Domain Controller and Certificate Authority for the update of GPO, and enrollment of user certificates.

DC01 and DC02 = 10.140.4.250 and 10.140.4.252
subordinateca01 and subordinateca02 = 10.140.2.198 and 10.140.2.199

```text
permit udp any any eq bootps
permit udp any any eq bootpc
permit udp any any eq domain
permit tcp any any eq domain
permit icmp any any

permit udp any host 10.140.4.250 eq 123
permit tcp any host 10.140.4.250 eq 88
permit udp any host 10.140.4.250 eq 88
permit tcp any host 10.140.4.250 eq 135
permit tcp any host 10.140.4.250 eq 389
permit udp any host 10.140.4.250 eq 389
permit tcp any host 10.140.4.250 eq 464
permit udp any host 10.140.4.250 eq 464
permit tcp any host 10.140.4.250 eq 636
permit tcp any host 10.140.4.250 eq 3268
permit tcp any host 10.140.4.250 eq 445
permit tcp any host 10.140.4.250 range 49152 65535

permit udp any host 10.140.4.252 eq 123
permit tcp any host 10.140.4.252 eq 88
permit udp any host 10.140.4.252 eq 88
permit tcp any host 10.140.4.252 eq 135
permit tcp any host 10.140.4.252 eq 389
permit udp any host 10.140.4.252 eq 389
permit udp any host 10.140.4.252 eq 464
permit tcp any host 10.140.4.252 eq 464
permit tcp any host 10.140.4.252 eq 636
permit tcp any host 10.140.4.252 eq 3268
permit tcp any host 10.140.4.252 eq 445
permit tcp any host 10.140.4.252 range 49152 65535


permit tcp any host 10.140.2.198 eq 135
permit tcp any host 10.140.2.198 eq 80
permit tcp any host 10.140.2.198 eq 443
permit tcp any host 10.140.2.198 range 49152 65535

permit tcp any host 10.140.2.199 eq 135
permit tcp any host 10.140.2.199 eq 80
permit tcp any host 10.140.2.199 eq 443
permit tcp any host 10.140.2.199 range 49152 65535

permit tcp any host 10.140.2.31 eq 8443
permit tcp any host 10.140.2.31 eq 8905
permit tcp any host 10.140.2.31 eq 443
permit tcp any host 10.140.2.32 eq 8443
permit tcp any host 10.140.2.32 eq 8905
permit tcp any host 10.140.2.32 eq 443
deny ip any any
```

# Microsoft Servers
In most cases the external services used are Microsoft Servers, with Active Directory as identity store, Certificate Authority for the certificates to use together with the user and/or host on the Active Directory and Group Policy Management to rollout the configuration to clients.  
## Active Directory 

![[Pasted image 20260421124607.png]]

Cisco ISE can join Microsoft Active Directory as an External Identity Source under the item Active Directory. 

The AD is used to identify the users when they do an authentication. They can be checked with their domain password or with the domain certificates they provide ISE.

For the server ISE to be able to join the domain, it has to have a machine account in the domain and a DNS entry, while the AD User Name must have the permissions to join ISE to AD. 

![[Pasted image 20260421152119.png]]

On this section it is also possible to retrieve groups from the AD to create policies around the user group identity. 

![[Pasted image 20260421125524.png]]

## Certificate Authority #certificates
The Certificate Authority service is used to provide certificates to both ISE server itself and clients that will use it to do network access authentication. 
### Server Certificates
The ISE server has two types of certificates, system certificates that are used to identify itself, and trusted certificates that are used to validate clients.
#### System Certificates
There are many portals hosted in ISE. All the ISE portals require encryption by default. In other words, all portals in ISE use HTTPS, and a certificate on ISE is used to secure the communication.
Certificates are also used to secure EAP communications, to form a Transport Layer Security (TLS) tunnel between an endpoint and a RADIUS server, or to identify the RADIUS server (ISE) to the client (supplicant)

![[Pasted image 20260421153234.png]]

##### Admin Certificate
For <mark style="background: #FF5582A6;">ISE Admin Portal</mark>. If this is chosen the ISE node needs to restart all services to use the newly applied certificate.
##### EAP Authentication Certificate
ISE will use this certificate for <mark style="background: #FFB86CA6;">EAP protocols that use SSL/TLS tunneling</mark>. <mark style="background: #FFF3A3A6;">This is the certificate the ISE will present to the client to prove itself as trusted server</mark>.
##### RADIUS DTLS Certificate
RADIUS over Datagram Transport Layer Security encrypt the full packet. The certificate can be used to establish and secure the communication between the <mark style="background: #FFB8EBA6;">ISE server and the NAD</mark>.
##### Portal Certificate
Certificates used for ISE <mark style="background: #BBFABBA6;">user portals</mark>. Which can be Guest Portal, Client Provisioning Portal, MDM Portal, BYOD Portal, Sponsor Portal, or My Devices Portal. The Guest Portal usually should have a public certificate as it should be used to external devices. 
##### pxGrid Certificate
This certificate will be used to establish trust and build a <mark style="background: #ABF7F7A6;">secure connection between ISE and third-party pxGrid clients</mark> to share contextual information. 
#### Certificate Signing Request
To create a certificate signed the a external Certificate Authority like Microsoft AD CS, create <strong>a Certificate Signing Request (CSR)</strong> in <strong>Administration > System > Certificates > Certificate Signing Request</strong> 

![[Pasted image 20260427150149.png]]
- <strong>Common Name (CN)</strong> : The CN should be a <mark style="background: #FF5582A6;">FQDN that will resolve via DNS to the IP address of ISE node</mark>.
- <strong>Organization(O)</strong>: The organization the certificate is meant ot represent, the org implementing ISE
- <strong>Organizational Unit(OU)</strong>: This is the division of the organization that is controlling the device for which the certificate is being used
- <strong>Locality(L)</strong>: The city where the entity resides
- <strong>State(ST)</strong>: The state or the province the entity resides in
- <strong>Country(C)</strong>: This is the country that the entity resides in

The ISE GUI also allows the customization of the Subject Alternative Name (SAN) field, which is meant to carry a number of different attributes, each designed to aid in the identification of the certificate:

- <strong>DNS Name</strong>: This is the FQDN of the ISE node. If the certificate will be a wildcard certificate, be sure to specify the wildcard notation <strong>*</strong>, like <strong>*.publiacqua.it</strong>.
- <strong>IP Address</strong>: This is the IP address of the ISE node associated with the certificate
- <strong>Uniform Resource Name</strong>: This is the URI associated with the certificate.
- <strong>Directory Name</strong>: This is a string representation of the distinguished name (DN). DNs are defined in RFC 2253.

A client that is presented with a certificate compare <mark style="background: #ABF7F7A6;">the name of the host</mark> with <mark style="background: #ADCCFFA6;">the CN field of the certificate subject</mark>. If the hostname or FQDN used to reach the host doesn’t match what is in the CN field, a certificate mismatch occurs.

The newly created CSR is saved in the <strong>Certificate Signing Requests</strong> section and it can be exported, it is a <strong>Base64-encoded plaintext file</strong> known as a <strong>PEM</strong> file.
Open the CSR with a text editor, copy its content and paste it on the certificate authority web server similar to the procedure in [[#Enrollment - Windows Manual | this link]] except that the CSR is already present.

Once the <strong>certnew.cer</strong> is downloaded, go back to the <strong>Certificate Signing Requests</strong> section and link to the certificate to the CSR used to make this cert. 

The new cert should show on System Certificates list.
#### Trusted Certificates
Trusted certificates are used for validation. <mark style="background: #FFF3A3A6;">They are the certificates</mark> (usually Root or Intermediate CA certificates) <mark style="background: #FFF3A3A6;">that ISE uses to verify the identity of someone else</mark>. 

In <strong>Administration > System > Certificates > Trusted Certificates</strong> a copy of the <mark style="background: #FF5582A6;">signing certificate authority’s public key must be stored</mark>, and that certificate must be trusted for purpose of authentication.

![[Pasted image 20260427145832.png]]

When a client presents a certificate for EAP authentication protocol, the ISE server will check if the issuer of the client certificate is present on the list of Trusted Certificates. 

![[Pasted image 20260427162757.png | 200]]

![[Pasted image 20260427165456.png]]

If the issuing certificate authority is not present among the Trusted Certificate the authentication fails. 
##### CRL Revocation List
In the Trusted Certificates is also set the CRL validation for the selected certificate. 
The Certificate Revocation List is a list of the revoked certificates, it is used to check for certificates that are not expired but are not usable because they are expired. 

![[Pasted image 20260504121014.png]]

The Retrieve CRL timers should be set accordingly to the CA CRL timers.

![[Pasted image 20260504122151.png | 200]]

- <strong>Effective date</strong> is the date the CRL will start to be valid. 
- <strong>Next update</strong> is the time the CRL will expire.
- <strong>Next CRL Publish</strong> is when the new CRL will be published but is still not active
The Retrieve CRL set to 8 hours before expiration is set 8 hours before the <strong>Next update</strong> so it will retrive the <strong>Next CRL Publish</strong> CRL.
The old CRL and the new CRL have 8 hours overlap in which both CRL are active, so the timer set to Automatically 8 hour before expire with 10 minutes of wait before retry, is correct and leave no black periods. 

The CRL Distribution URL can be retrieved from the Certificate Authority server

![[Pasted image 20260427170031.png]]

When a certificate is revoked outside of the automated cycle, you must trigger a manual CRL publication to synchronize the revocation status across all validating clients:

![[Pasted image 20260427170213.png]]

![[Pasted image 20260427170229.png]]

When doing a manual CRL publication do a manual download of the CRL in ISE server too, by setting the Retrieve CRL download to every 1 minute and then change back. 
#### Certificate Authentication Profile #certificates 

![[Pasted image 20260424144802.png]]

<strong>Certificate Authentication Profile</strong>(CAP) section is used to decide which <mark style="background: #FF5582A6;">attribute of the certificate</mark> the server ISE will use to check identity of the client. 

Here it is set to Subject Alternate Name (SAN) as the CAP will be used for both Machine and User EAP authentication protocols. The Users in the SAN will use the UPN while the Machines will use the DNS Name.

| User Certificate                     | Machine Certificate                  |
| ------------------------------------ | ------------------------------------ |
| ![[Pasted image 20260424145144.png]] | ![[Pasted image 20260424145227.png]] |

The selection <strong>Match Client Certificate Against Certificate In Identity Store</strong>:
- <strong>Only to resolve identity ambiguity</strong>: This is the standard setting. It tells ISE to use the certificate information to identify the user in AD, but it doesn't require a byte-for-byte match of the certificate itself against an AD attribute.
- <strong>Always perform binary comparison</strong>: <mark style="background: #FF5582A6;">Use this only if you have physically uploaded or published the user/machine certificates into the <strong>userCertificate</strong> attribute in Active Directory</mark>. <mark style="background: #FFB86CA6;">ISE will then perform a byte-for-byte comparison between the certificate the client presents and the one stored in AD</mark>. If they don't match exactly, authentication will fail.
   [[#Domain Users Certificate| Link to configuration of a domain user certificate and the img of userCertificate attribute]]
   [[#Script To Remove Expired userCertificate| Link to the managing of expired userCertificate attribute]]
- <strong>Never:</strong> Choose this if you are not using an identity store at all for this profile. This would be common for Guest or BYOD setups where you just want to verify that the certificate is valid and signed by a trusted CA without checking it against an AD account.
### Client Certificates 
Client Certificates are used by users, machine or both to authenticate to ISE. 
In the server SubordinateCA, on the Certificate Authority service create the Certificate Templates that will be used by Domain Users, Domain Machines, and non Domain Users. 
#### Domain Users Certificate
For Users Certificates, duplicate from the default <strong>User</strong> certificate template:
- On the <u>General tab</u> create a logical template name. The <strong>Publish certificate in Active Directory</strong> is used to publish the certificate into the user <strong>userCertificate</strong> attribute in Active Directory. ![[Pasted image 20260424150748.png|200]]
- On the <u>Request Handling tab</u>, uncheck the <strong>Allow private key to be exported</strong> box. 
- On the <u>Extensions tab</u>, highlight the <strong>Application Policies</strong> and click <strong>Edit</strong>. The <strong>Edit Application Policies Extension</strong> window will pop up. Click the <strong>Add</strong> button. Then, add the <strong>Server Authentication</strong> policy to the <strong>Application Policies</strong>. Then click <strong>OK</strong> to close the <strong>Edit Application Policies Extension</strong> window.
- On the <u>Security tab</u>, highlight <strong>Domain Users</strong> and check the <strong>Allow</strong> boxes for <strong>Read</strong>, <strong>Enroll</strong>, and <strong>Autoenroll</strong> under the Permissions pane. <mark style="background: #FF5582A6;">This will be important when configuring our Group Policy to <strong>auto-enroll</strong> users with a user certificate</mark> for EAP authentication when they log into their computers. 
- On the <u>Subject Name tab</u>. If this is a lab environment, <mark style="background: #ADCCFFA6;">you may want to exclude email addresses from the Certificate template</mark> as your environment may not have an Exchange server or SMTP server integrated with Active Directory to pre-populate that information in the AD. <mark style="background: #ADCCFFA6;">If that information is not in the Active Directory record and this box is checked in the template, your certificate will not be issued to the user</mark>. <mark style="background: #FFB8EBA6;">The UPN in Alternate Subject Name (SAN) is what the ISE Server will use to check the identity of the machine in the Active Directory</mark>, if the Certificate Authentication Profile is configured with the SAN.

| General tab               | Request Handling tab               | Extensions tab               | Security tab               | Subject Name tab               |
| ------------------------- | ---------------------------------- | ---------------------------- | -------------------------- | ------------------------------ |
| ![[General tab.png\|200]] | ![[Request Handling tab.png\|200]] | ![[Extensions tab.png\|200]] | ![[Security tab.png\|200]] | ![[Subject Name tab.png\|200]] |

Once the Domain Users Certificate Template is created, <mark style="background: #FF5582A6;">issue the template only on one of the SubordinateCA server</mark> <mark style="background: #FFB86CA6;">if the design is to separate User Certificates</mark> from <mark style="background: #BBFABBA6;">Machine Certificates</mark>. 
In this case the <strong>User Certificate</strong> is issued on the <strong>SubordinateCA01</strong>.

![[Pasted image 20260424135651.png]]

#### Domain Admin Certificate
For the <strong>Domain Admin Certificate</strong> template copy the <strong>Domain User Certificate</strong> template and <mark style="background: #FFF3A3A6;">change Security tab <strong>Group or user names</strong> section</mark>, <mark style="background: #FFB86CA6;">remove Domain Users</mark> and in <mark style="background: #ABF7F7A6;">Domain Admin permissions, allow Read, Write, and Enroll</mark>. The Write permission is used to modify the certificate template. 

As the Domain Admin Certificate is made for admins that have a domain user account but not a domain computer, the enrollment is done manually. 
##### Enrollment - Windows Manual
![[Manual Enrollment of Admin Certificate.mp4]]
##### Enrollment - Windows Script
This is a script that enroll a non domain computer with a domain certificate if the user is an admin with a account in the Active Directory. 

To correctly activate this script, it must be saved with <strong>.ps1</strong> extension in the format <strong>UTF-8 with BOM</strong>.

It's advised to install the 64-base <strong>certnew.p7b</strong> certificate chain, for easiest install, but the <strong>certnew.cer</strong> certificate works too.

```powershell
param(
    [ValidateSet("All", "Step1", "Step2")]
    [string]$Step = "All",
    [string]$CertPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Require elevation — CA chain import writes to LocalMachine stores
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "This script must be run as Administrator (right-click → Run as administrator)."
}

# Verify certreq is available before doing anything else
if (-not (Get-Command certreq.exe -ErrorAction SilentlyContinue)) {
    throw "certreq.exe not found on this system. This script requires the Windows certificate request utility."
}

# Load VB assembly once at script scope (used by Move-UsedFilesToRecycleBin)
Add-Type -AssemblyName Microsoft.VisualBasic

# Paths
$desktop      = [Environment]::GetFolderPath('Desktop')
$downloadsDir = Join-Path $env:USERPROFILE 'Downloads'
$infPath      = Join-Path $env:TEMP "cert_request.inf"
$csrPath      = Join-Path $desktop  "request.csr"
$subcaBase    = "https://subordinateca01.publiacqua.it/certsrv"
$subcaUrl     = "$subcaBase/certrqxt.asp"
$caChainPage  = "$subcaBase/certcarc.asp"
$scriptName   = $MyInvocation.MyCommand.Name
$eventSource  = "EAPEnroll"

# Expected template name (for display only)
$expectedTemplate = "EAP-Admin-User"

$script:Step1StartTime = $null
$IsCertPathExplicit    = $PSBoundParameters.ContainsKey('CertPath')

$infContent = @"
[NewRequest]
Subject = "CN=$env:USERNAME"
KeyLength = 2048
Exportable = TRUE
MachineKeySet = FALSE
RequestType = PKCS10
ProviderName = "Microsoft Software Key Storage Provider"

[EnhancedKeyUsageExtension]
OID = 1.3.6.1.5.5.7.3.2 ; Client Authentication
"@

function Write-EnrollmentEvent {
    param(
        [string]$Message,
        [ValidateSet('Information','Warning','Error')]
        [string]$EntryType = 'Information'
    )
    try {
        if (-not [System.Diagnostics.EventLog]::SourceExists($eventSource)) {
            try { New-EventLog -LogName Application -Source $eventSource -ErrorAction Stop } catch { return }
        }
        Write-EventLog -LogName Application -Source $eventSource -EventId 1000 `
            -EntryType $EntryType -Message $Message -ErrorAction Stop
    }
    catch {
        # Best-effort.
    }
}

function Find-NewestCertificate {
    param([datetime]$SinceTime)

    if (-not (Test-Path $downloadsDir)) { return $null }

    $candidates = Get-ChildItem -Path $downloadsDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.cer','.p7b' }

    if ($SinceTime) {
        $candidates = $candidates | Where-Object { $_.LastWriteTime -ge $SinceTime }
    }

    $newest = $candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($newest) { return $newest.FullName }
    return $null
}

function Test-IsCACertificate {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)

    $bcExt = $Certificate.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.19' } | Select-Object -First 1
    if (-not $bcExt) { return $false }
    return ([System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension]$bcExt).CertificateAuthority
}

function Test-DownloadedCertificate {
    <#
    Accepts either a single-cert (.cer) or PKCS#7 chain (.p7b).
    For a chain, finds the leaf (non-CA) certificate and validates it.
    #>
    param([string]$Path)

    $result = [ordered]@{
        Valid       = $false
        Reason      = $null
        Certificate = $null
        CACerts     = @()
    }

    $collection = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2Collection
    try {
        $collection.Import($Path)
    }
    catch {
        $result.Reason = "File could not be parsed as a certificate or PKCS#7 chain: $_"
        return $result
    }

    if ($collection.Count -eq 0) {
        $result.Reason = "File contains no certificates."
        return $result
    }

    $leafCandidates = @()
    $caCerts        = @()
    foreach ($c in $collection) {
        if (Test-IsCACertificate -Certificate $c) { $caCerts += $c }
        else { $leafCandidates += $c }
    }

    if ($leafCandidates.Count -eq 0) {
        $result.Reason = "File contains only CA certificates — no user/leaf certificate found. Did you download the CA chain instead of your issued certificate?"
        return $result
    }
    if ($leafCandidates.Count -gt 1) {
        $result.Reason = "File contains multiple non-CA certificates ($($leafCandidates.Count)). Cannot determine which is yours."
        return $result
    }

    $cert = $leafCandidates[0]
    $result.Certificate = $cert
    $result.CACerts     = $caCerts

    $clientAuthOid = '1.3.6.1.5.5.7.3.2'
    $ekuExts = $cert.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.37' }
    if (-not $ekuExts) {
        $result.Reason = "Certificate has no Enhanced Key Usage extension. Wrong template?"
        return $result
    }

    $ekuOids = foreach ($ext in $ekuExts) {
        ([System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]$ext).EnhancedKeyUsages |
            ForEach-Object { $_.Value }
    }

    if ($clientAuthOid -notin $ekuOids) {
        $result.Reason = "Certificate is missing Client Authentication EKU. Found EKUs: $($ekuOids -join ', ')"
        return $result
    }

    $now = Get-Date
    if ($cert.NotAfter -lt $now) {
        $result.Reason = "Certificate is already expired (NotAfter: $($cert.NotAfter))."
        return $result
    }
    if ($cert.NotBefore -gt $now) {
        $result.Reason = "Certificate is not yet valid (NotBefore: $($cert.NotBefore)) — possible clock skew."
        return $result
    }

    $result.Valid = $true
    return $result
}

function Install-CAChainFromCerts {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2[]]$CACerts)

    if (-not $CACerts -or $CACerts.Count -eq 0) { return $false }

    $rootStore = $null
    $caStore   = $null
    try {
        $rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store('Root','LocalMachine')
        $caStore   = New-Object System.Security.Cryptography.X509Certificates.X509Store('CA','LocalMachine')
        $rootStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
        $caStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)

        foreach ($c in $CACerts) {
            $isSelfSigned = ($c.Subject -eq $c.Issuer)
            if ($isSelfSigned) {
                $rootStore.Add($c)
                Write-Host "  Installed root: $($c.Subject)" -ForegroundColor DarkGreen
            } else {
                $caStore.Add($c)
                Write-Host "  Installed intermediate: $($c.Subject)" -ForegroundColor DarkGreen
            }
        }
        return $true
    }
    catch {
        Write-Warning " CA chain import failed: $_"
        return $false
    }
    finally {
        if ($rootStore) { $rootStore.Close() }
        if ($caStore)   { $caStore.Close() }
    }
}

function Install-CAChainViaBrowser {
    <#
    Asks the user to download the CA certificate chain .p7b through their browser
    (auth is handled by the browser), then finds it in Downloads, validates that
    it contains only CA certs, and installs it.

    Returns the path to the installed .p7b on success, or $null on failure.
    #>

    Write-Host ""
    Write-Host " The downloaded certificate does not include the CA chain." -ForegroundColor Yellow
    Write-Host " The CA chain must be installed before the certificate can be bound to its private key." -ForegroundColor Yellow
    Write-Host ""
    Write-Host " Opening the CA certificate download page:" -ForegroundColor Cyan
    Write-Host "   $caChainPage" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " On that page:" -ForegroundColor Cyan
    Write-Host "   1. Select 'Base 64'" -ForegroundColor Cyan
    Write-Host "   2. Click 'Download CA certificate chain'" -ForegroundColor Cyan
    Write-Host "   3. Save the .p7b file to your Downloads folder" -ForegroundColor Cyan

    $promptTime = Get-Date
    Start-Process $caChainPage

    [void](Read-Host "`n Press ENTER once the .p7b is downloaded")

    Write-Host " Looking for newly downloaded .p7b in $downloadsDir..." -ForegroundColor Cyan
    $p7bPath = $null
    for ($i = 0; $i -lt 10; $i++) {
        $candidate = Get-ChildItem -Path $downloadsDir -Filter '*.p7b' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $promptTime } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($candidate) { $p7bPath = $candidate.FullName; break }
        Start-Sleep -Milliseconds 500
    }

    if (-not $p7bPath) {
        Write-Error " No .p7b file found in $downloadsDir newer than $($promptTime.ToString('HH:mm:ss'))."
        return $null
    }
    Write-Host " Found chain file: $p7bPath" -ForegroundColor Cyan

    try {
        $coll = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2Collection
        $coll.Import($p7bPath)
    }
    catch {
        Write-Error " Could not parse $p7bPath as PKCS#7: $_"
        return $null
    }

    if ($coll.Count -eq 0) {
        Write-Error " The downloaded file contains no certificates."
        return $null
    }

    # Refuse anything that isn't a CA cert — we're installing into trusted stores
    $caOnly = @($coll | Where-Object { Test-IsCACertificate -Certificate $_ })
    if ($caOnly.Count -ne $coll.Count) {
        Write-Error " The downloaded chain file contains non-CA certificates. Aborting for safety — you may have downloaded the wrong file."
        return $null
    }

    Write-Host " Installing $($caOnly.Count) CA cert(s) from the chain..." -ForegroundColor Cyan
    if (-not (Install-CAChainFromCerts -CACerts $caOnly)) {
        return $null
    }

    return $p7bPath
}

function Move-UsedFilesToRecycleBin {
    param(
        [string]$ResolvedCertPath,
        [string]$CAChainPath
    )

    $filesToMove = @($infPath, $csrPath, $ResolvedCertPath, $CAChainPath)
    foreach ($file in $filesToMove) {
        if ($file -and (Test-Path $file)) {
            try {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                    $file,
                    [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                    [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin
                )
            }
            catch {
                Write-Warning "Could not move '$file' to Recycle Bin: $_"
            }
        }
    }
}

function Invoke-Step1 {
    if (Test-Path $csrPath) { Remove-Item $csrPath -Force }
    if (Test-Path $infPath) { Remove-Item $infPath -Force }

    $script:Step1StartTime = Get-Date

    Set-Content -Path $infPath -Value $infContent -Encoding ASCII

    certreq -new $infPath $csrPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $csrPath)) {
        Write-Error "certreq -new failed (exit code $LASTEXITCODE). CSR was not generated."
        return $false
    }

    $csrText = Get-Content $csrPath -Raw

    $clipboardOk = $false
    try {
        $csrText | Set-Clipboard
        $clipboardOk = $true
    }
    catch {
        Write-Warning "Clipboard unavailable: $_"
    }

    if ($clipboardOk) {
        Write-Host "`n CSR saved and copied to clipboard (your previous clipboard contents have been replaced)." -ForegroundColor Green
    }
    else {
        Write-Host "`n CSR saved to: $csrPath" -ForegroundColor Yellow
        Write-Host " Clipboard was unavailable — open the file and copy its contents manually." -ForegroundColor Yellow
    }

    Write-Host "`n Use Publiacqua domain credentials." -ForegroundColor Green
    Write-Host "`n Paste the CSR to $subcaUrl" -ForegroundColor Green
    Write-Host "`n Certificate Template must be $expectedTemplate." -ForegroundColor Green
    Write-Host "`n Download the Base64 certificate (.cer) OR full chain (.p7b) to the Downloads folder." -ForegroundColor Green

    Start-Process $subcaUrl
    return $true
}

function Invoke-Step2 {
    $resolvedPath = $null

    if ($IsCertPathExplicit) {
        $resolvedPath = $CertPath
    }
    else {
        Write-Host "`n Looking for newly downloaded .cer or .p7b in $downloadsDir..." -ForegroundColor Cyan
        for ($i = 0; $i -lt 10; $i++) {
            $resolvedPath = Find-NewestCertificate -SinceTime $script:Step1StartTime
            if ($resolvedPath) { break }
            Start-Sleep -Milliseconds 500
        }

        if (-not $resolvedPath) {
            Write-Error "`n No .cer or .p7b file found in $downloadsDir$(if ($script:Step1StartTime) { " newer than $($script:Step1StartTime.ToString('HH:mm:ss'))" })."
            Write-Host " If needed, specify it explicitly:" -ForegroundColor Yellow
            Write-Host "   .\$scriptName -Step Step2 -CertPath 'C:\path\certnew.cer'" -ForegroundColor Yellow
            return $false
        }
        Write-Host " Auto-detected: $resolvedPath" -ForegroundColor Cyan
    }

    if (-not (Test-Path $resolvedPath)) {
        Write-Error "`n Certificate file not found: $resolvedPath"
        return $false
    }

    $validation = Test-DownloadedCertificate -Path $resolvedPath
    if (-not $validation.Valid) {
        Write-Error "`n Certificate validation failed: $($validation.Reason)"
        Write-Host "   File: $resolvedPath" -ForegroundColor Yellow
        Write-Host "   Re-download from $subcaUrl using template '$expectedTemplate'." -ForegroundColor Yellow
        return $false
    }

    Write-Host " Certificate validated (Subject: $($validation.Certificate.Subject), Issuer: $($validation.Certificate.Issuer))." -ForegroundColor Green
    if ($validation.CACerts.Count -gt 0) {
        Write-Host " Found $($validation.CACerts.Count) CA cert(s) bundled in the file." -ForegroundColor Green
    }

    # Install CA chain — either from the downloaded .p7b, or by asking the user to download one
    $chainP7bPath = $null
    if ($validation.CACerts.Count -gt 0) {
        Write-Host "`n Installing CA chain from the downloaded file..." -ForegroundColor Cyan
        if (-not (Install-CAChainFromCerts -CACerts $validation.CACerts)) {
            Write-Error " CA chain installation failed."
            return $false
        }
        Write-Host " CA chain installed." -ForegroundColor Green
    } else {
        $chainP7bPath = Install-CAChainViaBrowser
        if (-not $chainP7bPath) {
            Write-Error " CA chain not installed. certreq -accept would fail with UNTRUSTEDROOT."
            return $false
        }
        Write-Host " CA chain installed." -ForegroundColor Green
    }

    # certreq -accept handles both .cer and .p7b; binds the issued cert to the private key in the CSP
    certreq -accept $resolvedPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "`n certreq -accept failed (exit code $LASTEXITCODE). The issued certificate could not be bound to its private key."
        return $false
    }

    $imported = Get-ChildItem Cert:\CurrentUser\My |
        Where-Object {
            $_.Thumbprint -eq $validation.Certificate.Thumbprint -and $_.HasPrivateKey
        } |
        Select-Object -First 1

    if (-not $imported) {
        Write-Warning "Certificate accepted, but no matching cert with a private key was found in CurrentUser\My. EAP authentication may fail."
    }
    else {
        Write-Host "`n Certificate installed to CurrentUser\Personal store (thumbprint $($imported.Thumbprint))." -ForegroundColor Green
        Write-EnrollmentEvent -Message "EAP cert enrolled for $env:USERNAME on $env:COMPUTERNAME, thumbprint $($imported.Thumbprint), source file $resolvedPath"
    }

    Move-UsedFilesToRecycleBin -ResolvedCertPath $resolvedPath -CAChainPath $chainP7bPath
    Write-Host "`n Used files sent to user Recycle Bin." -ForegroundColor Green
    return $true
}

switch ($Step) {
    'Step1' {
        if (-not (Invoke-Step1)) { exit 1 }
    }
    'Step2' {
        if (-not (Invoke-Step2)) { exit 1 }
    }
    'All' {
        if (-not (Invoke-Step1)) { exit 1 }

        $userInput = Read-Host "`n Once the certificate is downloaded, press ENTER to continue or Q to quit"
        if ($userInput -match '^[Qq]$') {
            Write-Host "`n Stopped after Step 1. You can later run: .\$scriptName -Step Step2" -ForegroundColor Yellow
            exit 0
        }

        if (-not (Invoke-Step2)) { exit 1 }
    }
}
```

##### Enrollment - Apple Script

```applescript
-- Define paths
set userName to short user name of (system info)
set desktopPath to (path to desktop)
set downloadsPath to (path to downloads folder)
set csrPath to (desktopPath as string) & "request.csr"
set keyPath to (desktopPath as string) & "private.key"
set p12Path to (desktopPath as string) & "identity.p12"
set certName to "certnew.cer"
set subCaUrl to "https://subordinateca01.publiacqua.it/certsrv/certrqxt.asp"
set tempPass to "1234"

set certInDownloads to (downloadsPath as string) & certName

-- Files to move to Trash at the end
set filesToTrash to {csrPath, keyPath, p12Path, certInDownloads}
set caughtError to ""

try
	-- 1. Generate Private Key and CSR
	do shell script "openssl req -new -newkey rsa:2048 -nodes -keyout " & quoted form of POSIX path of keyPath & " -out " & quoted form of POSIX path of csrPath & " -subj '/CN=" & userName & "'"
	
	-- 2. Copy CSR and open portal
	set csrText to do shell script "cat " & quoted form of POSIX path of csrPath
	set the clipboard to csrText
	open location subCaUrl
	
	-- 3. Wait for user
	display dialog "CSR COPIED! 

1. Paste into portal and select Template: EAP-Admin-User.
2. Download the 'Base 64 encoded' certificate.
3. Click 'Finalize' to link the key, install into Keychain, and clean up temporary files" with icon note buttons {"Finalize"} default button 1
	
	-- 4. Ensure downloaded certificate exists in Downloads
	set certDownloadsPosix to quoted form of POSIX path of certInDownloads
	do shell script "test -f " & certDownloadsPosix
	
	-- 5. Create PKCS#12 bundle from key + cert
	do shell script "openssl pkcs12 -export -out " & quoted form of POSIX path of p12Path & " -inkey " & quoted form of POSIX path of keyPath & " -in " & quoted form of POSIX path of certInDownloads & " -passout pass:" & quoted form of tempPass
	
	-- Import into the login keychain
	-- -P provides the password for the P12; -T allows the codesign tool access
	do shell script "security import " & quoted form of POSIX path of p12Path & " -k ~/Library/Keychains/login.keychain-db -P " & quoted form of tempPass & " -T /usr/bin/codesign"
	
	display notification "Certificate and key installed in Keychain!" with title "Success"
	
on error anyError
	set caughtError to anyError
end try

my moveToTrash(filesToTrash)
if caughtError is not "" and caughtError does not contain "User canceled" then
	display dialog "Error: " & caughtError buttons {"OK"} default button 1
end if

-- TRASH HANDLER
on moveToTrash(fileList)
	tell application "Finder"
		repeat with filePath in fileList
			if exists file filePath then
				delete file filePath
			end if
		end repeat
	end tell
end moveToTrash
```

#### Domain Computer Certificate
For Computer Certificates, duplicate from the default <strong>Workstation Authentication</strong> certificate template:
- On the <u>General tab</u> create a logical template name, the <strong>Publish certificate in Active Directory</strong> is used to publish the certificate into the computer <strong>userCertificate</strong> attribute in Active Directory. ![[Pasted image 20260424150609.png|200]]
- On the <u>Extensions tab</u>, highlight the <strong>Application Policies</strong> and click <strong>Edit</strong>. The <strong>Edit Application Policies Extension</strong> window will pop up. Click the <strong>Add</strong> button. Then, add the <strong>Server Authentication</strong> policy to the <strong>Application Policies</strong>. Then click <strong>OK</strong> to close the <strong>Edit Application Policies Extension</strong> window.
- On the <u>Security tab</u>, highlight <strong>Domain Computers</strong> and check the <strong>Allow</strong> boxes for <strong>Read</strong>, <strong>Enroll</strong>, and <strong>Autoenroll</strong> under the Permissions pane. <mark style="background: #FF5582A6;">This will be important when configuring our Group Policy to <strong>auto-enroll</strong> computers with a machine certificate</mark> for EAP authentication when they log into their computers. 
- On the <u>Subject Name tab</u> under Subject Name Format, change it to <strong>Fully distinguished name</strong>, and leave the DNS Name checked. <mark style="background: #FFB8EBA6;">The DNS name in Alternate Subject Name (SAN) is what the ISE Server will use to check the identity of the machine in the Active Directory</mark>, if the Certificate Authentication Profile is configured with the SAN.

| General tab                          | Extensions tab                       | Security tab                         | Subject Name tab                     |
| ------------------------------------ | ------------------------------------ | ------------------------------------ | ------------------------------------ |
| ![[Pasted image 20260424150448.png]] | ![[Pasted image 20260424141629.png]] | ![[Pasted image 20260424141754.png]] | ![[Pasted image 20260424141809.png]] |

Like the User certificate templates <mark style="background: #FF5582A6;">issue the template only on one of the SubordinateCA server</mark> <mark style="background: #FFB86CA6;">if the design is to separate User Certificates</mark> from <mark style="background: #BBFABBA6;">Machine Certificates</mark>. 
In this case the <strong>Machine Certificate</strong> is issued on the <strong>SubordinateCA02</strong>.

![[Pasted image 20260424141851.png]]

#### Script To Remove Expired userCertificate
The expired certificates in the userCertificate attribute cannot be removed automatically, we should remove them manually or with the help of a script. 
By default this script is in read only mode, read the description for the how to use.

[[Script To Remove Expired userCertificate]]
## Group Policy Management
The Group Policy Management service is used to deploy the configuration of Windows native supplicant and the rollout of the Client Certificates and other setting to manage the user and computer configuration. 

Make sure the GPO with the desired configuration is winning against other GPOs and its policies are enforced, and the <strong>Security Filtering</strong> is applied correctly. This is possible to check on <strong>Group Policy Results Wizard</strong> on <strong>Group Policy Management</strong>.
### Computer GPO
This GPO will be used to <mark style="background: #FFF3A3A6;">enroll Domain Computers</mark> with the [[#Domain Computer Certificate]] and enable <mark style="background: #FFB86CA6;">Wired AutoConfig</mark> on computers. 

All computer GPO must be create in the <strong>Group Policy Management → Forest: publiacqua.it → Domains → publiacqua.it → ComputerXp</strong> which is where the Domain Computer accounts are stored.
<mark style="background: #FFB8EBA6;"><u>At each change of computer GPO, there must be a <strong>gpupdate /force</strong> CMD command and a reboot of the client computer to apply the GPO configuration</u></mark>.

<strong>Wired AutoConfig</strong> (<strong>DOT3SVC</strong>) is a Windows service that manages <mark style="background: #FF5582A6;">IEEE 802.1X authentication on Ethernet connections</mark>. It enables computers to authenticate themselves on secure networks, often used in corporate environments to enforce network access control. 
<strong>Computer Configuration → Policies → Windows Settings → Security Settings → System Services → Wired AutoConfig</strong>

![[Pasted Graphic 2.png]]

The [[#Domain Computer Certificate]] has Auto-Enrollment configured on its certificate template, so to enroll the computers we just need to enable the Auto-Enrollment.

To activate Auto-Enrollment go to <strong>Computer Configuration → Policies → Windows Settings → Security Settings → Public Key Policies → Certificate Services Client - Auto-Enrollment</strong> 

![[Pasted Graphic.png]]

<mark style="background: #ABF7F7A6;">Core 802.1X configuration is the <strong>Wired Network (IEEE 802.3) Policies</strong></mark> in <strong>Computer Configuration → Policies → Windows Settings → Security Settings → Wired Network (IEEE 802.3) Policies</strong>, in the current deployment there are <strong>PEAP</strong>, <strong>TEAP</strong> and <strong>EAP-TLS</strong>.

GPO hierarchy: <strong>EAP-TLS → PEAP-MSCHAPv2 → TEAP</strong>
- <strong>TEAP</strong> GPO — scoped to <strong>Domain Computers</strong>. This makes TEAP the default authentication method for the entire fleet.
- <strong>PEAP MSCHAPv2</strong> GPO — scoped to a custom security group (e.g., <strong>GPO_C_PC_Enable_PEAP</strong>) for machines that require PEAP.
- <strong>EAP-TLS</strong> GPO — scoped to a custom security group (e.g., <strong>GPO_C_PC_Enable_EAP-TLS</strong>) for machines that require EAP-TLS.

Because the EAP-TLS and PEAP GPOs are linked at higher precedence than TEAP, <mark style="background: #FFB86CA6;">any computer added to one of the custom groups will have that GPO's wired profile applied last and override the default TEAP profile</mark>. <mark style="background: #BBFABBA6;">To switch a machine's authentication method, just add its computer object to the appropriate group</mark> — no per-machine configuration needed.

The default is TEAP and when some computers need EAP-TLS or PEAP they just need to be dropped in to the custom groups, they will automatically pick the correct authentication method at new reboot. 
#### PEAP MSCHAPv2
PEAP is used for Domain Users that cannot or do not want to use the certification to authenticate to ISE.

- <strong>General tab</strong>: enable <strong>Use Windows Wired Auto Config service for clients</strong>
- <strong>Security tab</strong>:
    - Enable <strong>Use IEEE 802.1X authentication for network access</strong>
	- Network authentication method: <strong>Microsoft: Protected EAP (PEAP)</strong>, go to <strong>Properties...</strong>
		- Tick <strong>Verify server's identity by validating certificate</strong>
		- <strong>Connect to these servers</strong>: Cisco ISE server FQDN
		- In Trusted Root Certification Authorities select the Root CA that signed the ISE [[#EAP Authentication Certificate]], <strong>Don't ask user to authorize new servers or trusted CAs</strong>.
		- Authentication Method: <strong>Secured password (EAP-MSCHAP v2)</strong>
		- Tick <strong>Enable Fast Reconnect</strong>
	- Authentication Mode: <strong>User authentication</strong>
	- Max authentication failures: 1–3
	- Tick <strong>Cache user information for subsequent connections</strong>, to decide if to tick or not. 

Under <strong>Scope → Security Filtering</strong> of the GPO add the Group for which this GPO will be applied. In <strong>Delegation → Advanced</strong> ensure this Group has <strong>Apply group policy</strong> and <strong>Read</strong> in <strong>Allow</strong>.
#### EAP-TLS
This is a GPO with authentication protocol set in EAP-TLS, made specifically for RDP connection, see the policy rule made for this. 

- <strong>General tab</strong>: enable <strong>Use Windows Wired Auto Config service for clients</strong>
- <strong>Security tab</strong>:
    - Enable <strong>Use IEEE 802.1X authentication for network access</strong>
	- Network authentication method: <strong>Microsoft: Smart Card or other certificate</strong>
		- Tick <strong>Use a certificate on this computer</strong>
		- Tick <strong>Use simple certificate selection</strong> 
		- Tick <strong>Verify server's identity by validating certificate</strong> 
		- Tick <strong>Connect to these servers</strong>: Cisco ISE servers FQDN 
		- In <strong>Trusted Root Certificate Authorities</strong> select the Root CA (only the Root CA) that signed the ISE [[#EAP Authentication Certificate]] 
		- Tick <strong>don't prompt user to authorize new servers or trusted certification authorities</strong>.
	- Authentication Mode: <strong>Computer only</strong>
	- Max authentication failures: 1–3

Under <strong>Scope → Security Filtering</strong> of the GPO add the Group for which this GPO will be applied. In <strong>Delegation → Advanced</strong> ensure this Group has <strong>Apply group policy</strong> and <strong>Read</strong> in <strong>Allow</strong>.
#### TEAP
TEAP authentication protocol is the default protocol used by Domain Users and Domain Computers. 

On Group Policy Management editor, the TEAP authentication method is broken, to rollout this type of authentication method we need to import a XML configuration from a working Win10/11 client. 
##### TEAP profile 
First we need to create a TEAP profile to export as XML. 

On a domain-joined client that has both the machine and user certs already enrolled, configure the wired NIC manually so you can export it.

Open the NIC <strong>properties</strong> → <strong>Authentication</strong> tab:
1. Tick <strong>Enable IEEE 802.1X authentication</strong>.
2. Network authentication method → <strong>Microsoft: Tunnel EAP (TEAP)</strong>.
3. Click <strong>Settings</strong>:
    - <strong>Identity privacy</strong> → anonymous.
	    - <strong>Connect to these servers</strong>: Cisco ISE servers FQDN.
	    - <strong>Trusted Root Certification Authorities</strong> → tick the root that signed the ISE [[#EAP Authentication Certificate]]. (If you have a 2-tier PKI, <mark style="background: #FF5582A6;">only tick the <strong>offline root</strong></mark>, not the issuing CA)
	    - Tick <strong>Don't prompt user if unable to authorize server</strong>
    - <strong>Client authentication</strong>:
        - <strong>Primary EAP method </strong>→ <mark style="background: #FFF3A3A6;">Microsoft: Smart Card or other certificate (EAP-TLS)</mark> → this is the computer authentication.
	        -  Tick <strong>Use a certificate on this computer</strong>
			- Tick <strong>Use simple certificate selection</strong> 
			- Tick <strong>Verify server's identity by validating certificate</strong> 
			- Tick <strong>Connect to these servers</strong>: Cisco ISE servers FQDN 
			- In <strong>Trusted Root Certificate Authorities</strong> select the Root CA (only the Root CA) that signed the ISE [[#EAP Authentication Certificate]] 
			- Tick <strong>don't prompt user to authorize new servers or trusted certification authorities</strong>.
        - <strong>Secondary EAP method</strong> → <mark style="background: #FFF3A3A6;">Microsoft: Smart Card or other certificate (EAP-TLS)</mark> → this becomes the user auth.
	        - Tick <strong>Use a certificate on this computer</strong>
			- Tick <strong>Use simple certificate selection</strong> 
			- Tick <strong>Verify server's identity by validating certificate</strong> 
			- Tick <strong>Connect to these servers</strong>: Cisco ISE servers FQDN 
			- In <strong>Trusted Root Certificate Authorities</strong> select the Root CA (only the Root CA) that signed the ISE [[#EAP Authentication Certificate]] 
			- Tick <strong>don't prompt user to authorize new servers or trusted certification authorities</strong>.
4. Back on the <strong>Authentication</strong> tab → <strong>Additional settings</strong> 
	- Tick <strong>Specify authentication mode</strong> → <strong>User or computer authentication</strong>.
	- Tick <strong>Enable Single Sign On for this network</strong> 
		- Tick <strong>Perform immediately before user logon</strong>
		- Tick <strong>This network uses different VLAN for authentication with machine and user credentials</strong> 
The <strong>Fallback to unauthorized network access</strong> must remain <strong>ticked</strong>, as without this option enabled if the user connect to a switch with no authenticator it will not get network access.
##### Export the profile to XML
From an elevated cmd on the same client:
```powershell
netsh lan show profiles
netsh lan export profile folder=C:\Temp interface="Ethernet"
```
The interface="" depends on the show lan profiles.

Note that the <strong>netsh</strong> can have a bug where the TrustedRootCAHash block have malformed hash like `fc 5 c2 6 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e
where bytes `0x05` and `0x06` came out as single hex digits. Change it like `fc 05 c2 06 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e`.

When there are more than one FQDN in the ServerNames block, separate the FQDNs with a semicolon <strong>;</strong> with no trailing spaces.

Open the resulting XML and copy everything inside the OneX block. 
```xml
<OneX xmlns="http://www.microsoft.com/networking/OneX/v1">
				<cacheUserData>false</cacheUserData>
				<heldPeriod>20</heldPeriod>
				<authPeriod>18</authPeriod>
				<startPeriod>3</startPeriod>
				<maxStart>2</maxStart>
				<maxAuthFailures>1</maxAuthFailures>
				<authMode>machineOrUser</authMode>
				<singleSignOn>
					<type>preLogon</type>
					<maxDelay>10</maxDelay>
					<allowAdditionalDialogs>false</allowAdditionalDialogs>
					<userBasedVirtualLan>true</userBasedVirtualLan>
				</singleSignOn>
				<EAPConfig><EapHostConfig xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><EapMethod><Type xmlns="http://www.microsoft.com/provisioning/EapCommon">55</Type><VendorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorId><VendorType xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorType><AuthorId xmlns="http://www.microsoft.com/provisioning/EapCommon">311</AuthorId></EapMethod><Config xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><EapTeap xmlns="http://www.microsoft.com/provisioning/EapTeapConnectionPropertiesV1"><ServerValidation><ServerNames>cisco-ise1.publiacqua.it;pba-ise02.publiacqua.it</ServerNames><TrustedRootCAHash>fc 05 c2 06 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e</TrustedRootCAHash><DisablePrompt>true</DisablePrompt><DownloadTrustedServerRoot>false</DownloadTrustedServerRoot></ServerValidation><Phase2Authentication><InnerMethodConfig><EapHostConfig xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><EapMethod><Type xmlns="http://www.microsoft.com/provisioning/EapCommon">13</Type><VendorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorId><VendorType xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorType><AuthorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</AuthorId></EapMethod><Config xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><Eap xmlns="http://www.microsoft.com/provisioning/BaseEapConnectionPropertiesV1"><Type>13</Type><EapType xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV1"><CredentialsSource><CertificateStore><SimpleCertSelection>true</SimpleCertSelection></CertificateStore></CredentialsSource><ServerValidation><DisableUserPromptForServerValidation>true</DisableUserPromptForServerValidation><ServerNames>cisco-ise1.publiacqua.it;pba-ise02.publiacqua.it</ServerNames><TrustedRootCA>fc 05 c2 06 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e</TrustedRootCA></ServerValidation><DifferentUsername>false</DifferentUsername><PerformServerValidation xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">true</PerformServerValidation><AcceptServerName xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">true</AcceptServerName></EapType></Eap></Config></EapHostConfig></InnerMethodConfig><InnerMethodConfig><EapHostConfig xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><EapMethod><Type xmlns="http://www.microsoft.com/provisioning/EapCommon">13</Type><VendorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorId><VendorType xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorType><AuthorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</AuthorId></EapMethod><Config xmlns="http://www.microsoft.com/provisioning/EapHostConfig"><Eap xmlns="http://www.microsoft.com/provisioning/BaseEapConnectionPropertiesV1"><Type>13</Type><EapType xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV1"><CredentialsSource><CertificateStore><SimpleCertSelection>true</SimpleCertSelection></CertificateStore></CredentialsSource><ServerValidation><DisableUserPromptForServerValidation>true</DisableUserPromptForServerValidation><ServerNames>cisco-ise1.publiacqua.it;pba-ise02.publiacqua.it</ServerNames><TrustedRootCA>fc 05 c2 06 c0 a7 f0 6e 66 10 3f f0 65 3b ad 49 bf 59 85 9e</TrustedRootCA></ServerValidation><DifferentUsername>false</DifferentUsername><PerformServerValidation xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">true</PerformServerValidation><AcceptServerName xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">true</AcceptServerName></EapType></Eap></Config></EapHostConfig></InnerMethodConfig></Phase2Authentication><Phase1Identity><IdentityPrivacy>true</IdentityPrivacy><AnonymousIdentity>anonymous</AnonymousIdentity></Phase1Identity></EapTeap></Config></EapHostConfig></EAPConfig>
			</OneX>
```
##### Create the GPO
On the DC open Group Policy Management and create a new GPO linked to the OU that contains your domain computers. Edit it. 
<strong>Computer Configuration → Policies → Windows Settings → Security Settings → Wired Network (IEEE 802.3) Policies → right-click → Create A New Wired Network Policy for Windows Vista and Later Releases</strong>.

1. Make a dummy authentication profile that will be rewritten by the XML config file. 
	- <strong>General tab</strong>: Choose a <strong>Policy Name</strong>, enable <strong>Use Windows Wired Auto Config service for clients</strong>
	- <strong>Security tab</strong>:
	    - Enable <strong>Use IEEE 802.1X authentication for network access</strong>
		- Network authentication method: Pick <strong>Microsoft: Protected EAP (PEAP)</strong> for placeholder, it will be overwritten. 
	- <strong>Security → Advanced</strong>:
	    - Tick <strong>Enforce advanced 802.1X settings</strong>
		    - <strong>Max Eapol-Start Msgs</strong>: 2
		    - <strong>Held Period</strong>: 60
		    - <strong>Start Period</strong>: 3
		    - <strong>Auth Period</strong>: 30
	    - Tick <strong>Enable Single Sign On for this network</strong> → <strong>Perform immediately before user logon</strong>.
	    - Tick <strong>This network uses different VLAN for authentication with machine and user credentials</strong>.
2. Save the policy, go to <strong>Group Policy Management → Forest: publiacqua.it → Domains → publiacqua.it → Group Policy Objects</strong>, find the saved policy.
3. Back Up... → Choose the Location (C:\Users\Username\Desktop).
4. Open the folder and open <strong>Backup.xml</strong> file with a text editor.
5. Find the block <strong>OneX xmlns="http://www.microsoft.com/networking/OneX/v1"</strong> 
6. Replace the whole block with the customized one, save and close. 
7. Return to <strong>Group Policy Objects</strong>, click <strong>Restore from Backup...</strong> 
8. Select Backup folder, if the the GUID folder was inside <strong>C:\Users\username\Desktop</strong> just select <strong>C:\Users\username\Desktop</strong> and not the GUID folder.
9. And finish the restore of the backup.
10. Check that it works.

Under <strong>Scope → Security Filtering</strong> of the GPO add <strong>Domain Computers</strong> which is the group this GPO will be applied to. In <strong>Delegation → Advanced</strong> ensure this Group has <strong>Apply group policy</strong> and <strong>Read</strong> in <strong>Allow</strong>.
### User GPO
This GPO will be used to <mark style="background: #FFF3A3A6;">enroll Domain Users</mark> with the [[#Domain Users Certificate]].

All computer GPO must be create in the <strong>Group Policy Management → Forest: publiacqua.it → Domains → publiacqua.it → Publiacqua</strong> which is where the Domain User accounts are stored.
<mark style="background: #CACFD9A6;">At each change of computer GPO, there must be a <strong>gpupdate /force</strong> CMD command to apply the GPO configuration</mark>.

To activate Auto-Enrollment go to <strong>User Configuration → Policies → Windows Settings → Security Settings → Public Key Policies → Certificate Services Client - Auto-Enrollment</strong> 

![[Pasted Graphic 3.png]]

The GPO should be in <strong>Enforced</strong> mode to ensure that it will be applied.
# Network Access Devices
Network Access Devices are the point of access for an endpoint and the main enforcement point of policies set by the server ISE. 

NAD types include the following:
- Access switch
- Wireless LAN controller (WLC)
- Cisco Adaptive Security Appliance (ASA)
- Cisco Firepower device
- Load balancer
- Software application that uses ISE for AAA
## Access Switch
### Initial Configuration
All NAD should have at least these configuration set for it be configurable with Cisco DNA or to be reachable in SSH.

```bash
conf t
hostname <HOSTNAME>
ip domain name publiacqua.it
!
enable secret 9 $14$kOh9$BYiVhdtn8rdhuU$ZksoQp0DSO9GhUJnJUWH1zmtTb2ChF1iXZC/etIkbb.
!
username admin privilege 15 secret 9 $14$GFW4$GKyL6MNZejulQU$A2EEwLhU1gQd2Ac.AjYj0CqlvW6qW.9cWZPDoda06fo
!
crypto key generate rsa modulus 2048
ip ssh version 2
ip ssh time-out 30
ip ssh bulk-mode 131072
ip ssh source-interface Vlan800
!
vlan 800
 name LAN-MGMT
!
interface Vlan800
 description LAN-MGMT
 ip address <IP-ADDRESS> <SUBNET-MASK>
 no shutdown
!
ip default-gateway <DEFAULT-GATEWAY>
!
interface <UPLINK-INTERFACE>
 ip dhcp snooping trust
 switchport mode trunk
 switchport trunk allowed vlan add 800
!
aaa new-model
!
line vty 0 4
 transport input ssh
 login local
!
snmp-server community publiacqua RO
snmp-server community publiacquarw RW
!
netconf-yang
!
end
write memory
```

### General Configuration

```bash
clock timezone CET 1 0
clock summer-time ROME recurring last Sun Mar 2:00 last Sun Oct 2:00
```

```bash
vrf definition Mgmt-vrf
!
address-family ipv4
exit-address-family
!
address-family ipv6
exit-address-family
```

```bash
vtp mode transparent
!
spanning-tree mode rapid-pvst
spanning-tree extend system-id
```

```bash
vlan 800
 name LAN-MGMT
!
vlan 801
 name LAN-STAMPANTI
!
vlan 802
 name LAN-CLIENT
!
vlan 803
 name LAN-THIN-CLIENT
!
vlan 804
 name WLAN-CLIENT
!
vlan 805
 name LAN-GUEST-ACCESS
!
vlan 806
 name WLAN-MGMT
!
vlan 808
 name LAN-TIMBRATORI
!
vlan 812
 name LAN-VOIP
!
vlan 830
 name MGMNT-AP
!
vlan 850
 name LAN-ADMIN
```

```bash
interface Vlan800
 no shut
 no ip route-cache
!
interface Vlan805
 no shut
 description GUEST-INTERCEPT-SVI
!
```

```bash
ip name-server 10.140.4.250 10.140.4.252 172.20.129.250 172.20.129.252
ip domain name publiacqua.it
```

```bash
radius server radius-mgmnt-auth01
 address ipv4 10.140.2.27 auth-port 1812 acct-port 1813
 timeout 2
 retransmit 3
 key 7 11593A0C2411241F37192474
!
ip radius source-interface Vlan800
!
aaa group server radius RADSERV
 server name radius-mgmnt-auth01
```

```bash
aaa authentication login default group RADSERV local-case 
aaa authentication login console local-case
aaa authentication login HTTPSRV group RADSERV local-case
!
aaa authentication enable default enable
!
aaa authorization exec default group RADSERV if-authenticated
aaa authorization exec HTTPSRV group RADSERV if-authenticated
!
aaa accounting exec default start-stop group RADSERV
!
aaa session-id common 
```

```bash
ntp source Vlan800
ntp server 172.20.129.64
ntp server 172.20.129.65 prefer
```

```bash
snmp-server community publiacqua RO
snmp-server community publiacquarw RW
snmp-server trap-source Vlan800
```

```bash
logging facility local6
logging source-interface Vlan800
logging host 10.140.2.181
logging host 10.140.2.24
logging host 10.139.108.10
```

```bash
ip http server
ip http secure-server
ip http secure-active-session-modules none
ip http active-session-modules none
ip http authentication aaa login-authentication default
ip http client source-interface Vlan800
ip forward-protocol nd
ip ssh bulk-mode 131072
ip ssh time-out 30
ip ssh version 2
ip ssh source-interface Vlan800
```

```bash
errdisable recovery cause udld
errdisable recovery interval 90
```

```bash
line con 0
 session-timeout 5
 exec-timeout 30 0
 privilege level 15
 logging synchronous
 login authentication console
 stopbits 1
line vty 0 4
 session-timeout 60
 exec-timeout 60 0
 logging synchronous
 history size 64
 transport input ssh
line vty 5 15
 session-timeout 60
 exec-timeout 60 0
 logging synchronous
 history size 64
 transport input ssh
```

```bash
end
write memory
```

#### DNA - PBA BASIC

```bash
!
service password-encryption 
service call-home
!
!
!
vrf definition Mgmt-vrf
 !
 address-family ipv4
 exit-address-family
 !
 address-family ipv6
 exit-address-family
!
!
!
clock timezone CET 1 0
clock summer-time ROME recurring last Sun Mar 2:00 last Sun Oct 2:00
!
!
!
ip name-server 10.140.4.250 10.140.4.252 172.20.129.250 172.20.129.252
ip domain name publiacqua.it
!
!
!
enable secret 9 $14$kOh9$BYiVhdtn8rdhuU$ZksoQp0DSO9GhUJnJUWH1zmtTb2ChF1iXZC/etIkbb.
!
username admin privilege 15 secret 9 $14$GFW4$GKyL6MNZejulQU$A2EEwLhU1gQd2Ac.AjYj0CqlvW6qW.9cWZPDoda06fo
!
!
!
! @start-ignore-compliance
ip ssh version 2
! @end-ignore-compliance
ip ssh time-out 30
ip ssh bulk-mode 131072
ip ssh source-interface Vlan800
!
!
!
aaa new-model
!
radius server radius-mgmnt-auth01
 address ipv4 10.140.2.27 auth-port 1812 acct-port 1813
 timeout 2
 retransmit 3
 key 7 11593A0C2411241F37192474
!
!
!
ip radius source-interface Vlan800
!
!
!
aaa group server radius RADSERV
 server name radius-mgmnt-auth01
!
!
!
aaa authentication login default group RADSERV local-case 
aaa authentication login console local-case
aaa authentication login HTTPSRV group RADSERV local-case
!
aaa authentication enable default enable
!
aaa authorization exec default group RADSERV if-authenticated
aaa authorization exec HTTPSRV group RADSERV if-authenticated
!
aaa accounting exec default start-stop group RADSERV
!
aaa session-id common 
!
login on-success log
!
!
!
netconf-yang
!
!
!
vtp mode transparent
!
spanning-tree mode rapid-pvst
spanning-tree extend system-id
!
!
!
vlan 800
 name LAN-MGMT
!
vlan 801
 name LAN-STAMPANTI
!
vlan 802
 name LAN-CLIENT
!
vlan 803
 name LAN-THIN-CLIENT
!
vlan 804
 name WLAN-CLIENT
!
vlan 805
 name LAN-GUEST-ACCESS
!
vlan 806
 name WLAN-MGMT
!
vlan 808
 name LAN-TIMBRATORI
!
vlan 812
 name LAN-VOIP
!
vlan 830
 name MGMNT-AP
!
vlan 850
 name LAN-ADMIN
!
!
!
{% block interfaces %}
{% endblock %}
!
!
!
interface Vlan1
 no ip address
 no ip route-cache
 shutdown
!
!
!
interface Vlan800
 no ip route-cache
 no shutdown
!
!
!
interface Vlan805
 description GUEST-INTERCEPT-SVI
 no shutdown
!
!
!
snmp-server community publiacqua RO
snmp-server community publiacquarw RW
snmp-server trap-source Vlan800
snmp-server location {{ SNMPLocation }}
snmp-server contact operationcenter@publiacqua.it
!
!
!
logging facility local6
logging source-interface Vlan800
logging host 10.140.2.181
logging host 10.140.2.24
logging host 10.139.108.10
!
!
!
ntp source Vlan800
ntp server 172.20.129.64
ntp server 172.20.129.65 prefer
!
!
!
ip http server
ip http secure-server
ip http secure-active-session-modules none
ip http active-session-modules none
ip http authentication aaa login-authentication default
ip http client source-interface Vlan800
ip forward-protocol nd
!
!
!
errdisable recovery cause udld
errdisable recovery interval 90
!
diagnostic bootup level minimal
!
!
!
line con 0
 session-timeout 5
 exec-timeout 30 0
 privilege level 15
 logging synchronous
 login authentication console
 stopbits 1
line vty 0 4
 session-timeout 60
 exec-timeout 60 0
 logging synchronous
 history size 64
 transport input ssh
line vty 5 15
 session-timeout 60
 exec-timeout 60 0
 logging synchronous
 history size 64
 transport input ssh
!
!
!
end
! @start-ignore-compliance
wr 
! @end-ignore-compliance
!
```

### NAD Configuration

```bash

```

```bash

```













# Packet Flow with Cisco ISE
Certificate authentication: 
CLIENT send certificate, ISE CHECK if issuer is in trusted, the expiry date, CRL, proof of possession (server privat key + client public key (the certificate sent for authentication) + random data) the client need to decrypt the data with client private key and server public key. 


# Reference 


| Voce                                               | Topic        | Link                                                                                                      |
| -------------------------------------------------- | ------------ | --------------------------------------------------------------------------------------------------------- |
| Cisco Identity Services Engine Administrator Guide | General      | https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/admin_guide/b_ise_admin_3_5.html                   |
| ISE BERG                                           | General      | https://community.cisco.com/t5/security-knowledge-base/ise-berg/ta-p/5041171                              |
| Windows Certificates                               | Certificates | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/certreq_1                |
| Certificate Templates                              | Certificates | https://sendthepayload.com/configuring-certificate-templates-with-active-directory-certificate-services/# |
