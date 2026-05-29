---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You can decompress Drawing data with the command palette: 'Decompress current Excalidraw file'. For more info check in plugin settings under 'Saving'


# Excalidraw Data

## Text Elements
Identity Management ^cRoBchoy

Identity Management manages all identities for ISE,
from ISE GUI admins to users that have to
authenticate to ISE. ^D7d7D5bv

Identities ^IAl447nI

Cisco ISE includes a built-in internal identity store
that supports a limited number of locally defined
user accounts, commonly referred to as internal users
or network access users. Within the Identities
section, administrators can configure local user
accounts serving one of two purposes: logging into
the ISE GUI, or authenticating for network access. ^9tZrVdeR

Groups ^rxQggMCP

Endpoint and User Groups can be used as attributes in
Policy Sets. ^WWLmpCsm

Endpoint Identity Groups ^whmQVteT

Endpoint Identity Groups store information about all
the endpoint devices that connect to the network
infrastructure or they can be filled through a CSV
import. Endpoint Groups can be used as attributes in
Policy Sets. ^2fMe2ApU

PBA_Blacklist ^001WiFo3

All MAC Address that must be denied access to the
network are put in this Endpoint Group. ^DPCvKqt6

PBA_Printers ^n8XuTmTE

All Printers MAC Addresses, there are child groups
that distribute the MAC Addresses by location. The
Printers MAC Addresses can be obtained from the ARP
table in the core switches/routers, and they can be
imported with the CSV. ^ihONqSk7

PBA_Whitelist ^AjMDf0ny

MAC Addresses that must be whitelisted. Used in the
MAB Access. ^wh3NyTew

User Identity Groups ^623ADJMe

The User Identity Group accept only Internal Users. ^VO8qRKI7

External Identity Sources ^jjKnEBYm

External Identity Sources can leverage existing
external identity store for network authentication. ^GEKcEoN4

External Identity Sources - Certificate Authentication Profile ^dBOxQY6g

This is an important setting for certificate based
authentication. See Link. ^Io8B1yhn

External Identity Sources - Active Directory ^t3KPtQ6h

Microsoft’s Active Directory (AD) is a highly
available distributed database deployment. It follows
the X. ^Rt8br4M2

Identity Source Sequences ^oCjq45RS

Identity Source Sequences (ISS) checks a series of
identity sources from top to bottom, enabling a
single authentication rule to check several identity
sources instead of just one. It includes the
selection of Certificate Authentication Profile. ^ZPT65c8g

Admin Access ^AVNRX7MY

ISE GUI permissions are configured in Admin Access
for each group or type of users. ^13fqgMfi

Admin Access - Authorization ^v2IvkooO

Admin Access - Authorization - Permissions ^BDuFjfKl

Menu Access ^ZgQYGOdV

Menu Access List is used to set which menu section is
allowed and which is not. If you want to allow only a
specific section of the submenu like showing only
Groups while hiding the Identities, External Identity
Source, and others under the menu Identity
Management. ^R1lkv9Xp

Data Access ^UXNj4ALA

The Data Access List is used to configure which data
a user is allowed to see or to modify. These changes
impact the type of log one can see, so if you want to
limit data access it's best to put them in Read Only
instead of No Access. ^Px1osXxJ

Admin Access - Authorization - RBAC Policy ^vVScWt6N

In this section you use the permissions set in Menu
Access and Data Access to configure the RBAC policy
for Admin Groups. ^1PE4wzZw

Admin Access - Administrators ^u1ON1iZR

Admin Access - Administrators - Admin Groups ^TB6tlS2W

In Admin Groups, you can configure the groups for
which you can build an RBAC Policy around. ^yY2kEZdy

Network Resources ^O6RC4HLG

In Network Resources are managed Network Access
Devices (NAD), they are the point of access for an
endpoint and the main enforcement point of policies
set by the server ISE. ^kCdUPm2x

Network Devices Profiles ^G8tHmUni

ISE supports third-party NADs through the use of
network device profiles. The NAD profiles are
configured to define the capabilities and attributes
of these third-party devices. ^JCFj0mjA

Authentication/Authorization ^Qmzpmkcn

It’s possible to set the conditions for which, based
on the attributes received on the header, the packet
is considered a Wired, Wireless, MAB, or 802. 1X
connection. ^zw7G7Kow

Flow Type Conditions ^jFqIO1Xn

Enter the attributes and values that your device
vendor uses for the network flow types in the Flow
Type Conditions: - Wired MAB - Wireless MAB - Wired
802. 1x - Wireless 802. ^0uxDBU7z

Cisco ^VtAkLauo

Cisco uses the attribute and value pair:
Radius:NAS-Port-Type = Ethernet for wired flows
Radius:NAS-Port-Type = Wireless - IEEE 802. 11 for
wireless flows Radius:Service-Type = Call Check for
MAB access Radius:Service-Type = Framed for 802. ^t4BhvnL5

ArubaWireless ^u92h1zj9

Aruba Networks views all wireless access as a user
initiating a standard data session. Because of this,
the Aruba controller sends the exact same generic
Service-Type for both authentication methods. ^aD6KUda9

Attribute Aliasing ^2jUzMDDs

Attribute Aliasing allows a NAD Profile to map
vendor-specific attributes to a common attribute so
that policy rules can use the friendly name. It
simplifies attribute selection, reduces the number of
authentication/authorization policy rules required
for different vendor devices, and is potentially less
error prone. ^tw21nVGX

Host Lookup ^puSVg5eJ

Host Lookup allows you to define which attributes and
protocols your device uses for MAB. Different
(non-Cisco) vendors populate the RADIUS
Calling-Station-ID and password attributes
differently while doing a MAB authentication. ^dtr3i8T7

Permissions ^u0iqdJvl

This section defines which attributes your device
uses for setting a VLAN or ACL. They may be IETF
standard attributes or vendor specific. ^uU58IZqv

Change of Authorization (CoA) ^7vWpxioF

This section allows you to define what CoA
capabilities your device has. Refer to your device
documentation for information – look for references
to terms like “RFC 5176”, “Change of Authorization”
or “CoA”. ^5TBKXskO

URL Redirect ^Q7ha59Dq

This section defines the device’s URL Redirect
capabilities. URL redirection is necessary for
complex flows like Guest, BYOD and Posture. ^Iailk97t

Network Devices Groups ^G3biSL5J

Network Device Groups can be set to define NAD
attributes that will be used in policy sets, they can
be whatever you want to. Here there are Device Types
and Locations. ^niJ6WJuN

Network Devices ^liYc4VRx

To add a NAD, navigate to Administration Network
Resources Network Devices and click Add. They can be
configured with Network Device Profile, Model Name,
Software Version or with the attributes set in the
Network Device Groups. ^4EMupCSo

Policy ^8rDzdZA9

In Policy section defines the Policy Sets,
Dictionaries, Conditions and Results. ^lWSbwtoP

Dictionaries ^I5huQqBx

Cisco ISE dictionary attributes are pre-defined or
custom RADIUS and system-level parameters used to
create policy conditions, such as device type, user
group, or location, for authentication and
authorization. These parameters are built on System
and Vendor-Specific Attributes: - IETF RADIUS
Attributes: The default base, defined by the Internet
Engineering Task Force. ^QT75NHSY

Radius Dictionary ^aArvMxW0

NAS-Port-Type ^Km03WE1n

Radius Attribute that indicates the port type. Common
values are: - Wireless - IEEE 802. ^IgVtjZyR

Service-Type ^Ee1cflyj

Service-Type is a RADIUS attribute (Attribute 6) that
defines the nature of the network access request
being made, allowing ISE to understand how a user or
device is trying to connect. Common Service-Type
values: - Framed (Value: 2): Indicates standard
network access control (NAC) sessions, such as Wired
or Wireless 802. ^1RNHQ9mt

Called-Station-ID ^hCXJJqXz

This attribute identifies the infrastructure access
point or port where the endpoint is physically or
logically connecting. The contents change drastically
depending on whether the connection is Wired or
Wireless: 1. ^H4buTY5H

Calling-Station-ID ^FtaHs19O

This attribute identifies the endpoint device that is
requesting access to the network. - What it contains:
In almost all modern enterprise networks (Wired,
Wireless, and VPN), it transmits the MAC address of
the client machine, smartphone, or IoT device. ^wnxZxZUW

Dynamic VLAN Assignment Attributes ^Im2wBsyx

For a network switch to accept a dynamic VLAN
assignment from Cisco ISE, it must receive three IETF
helper attributes in the Authorization Profile.
Tunnel-Private-Group-ID (RADIUS Attribute 81) is a
standard IETF attribute used as an Authorization
Result to dynamically assign a user or device to a
specific VLAN upon successful authentication. ^Al3SJQID

Cisco Dictionary ^JLCpPW4e

cisco-av-pair ^dtft3YCZ

In Cisco ISE, cisco-av-pair is a Vendor-Specific
Attribute (VSA) classified under the RADIUS Cisco
dictionary (Vendor ID: 9, Sub-ID: 1) Common uses:
Central Web Authentication (CWA) and Guest Portals:
When an unknown device connects to the network, ISE
uses two specific AV pairs to tell the switch to
intercept the user's web browser traffic and redirect
them to a login portal: - url-redirect: Tells the
switch exactly where the ISE Guest or Hotspot portal
is hosted. cisco-av-pair =
url-redirect=https://guestportal1. ^6wjcT20I

Network Access Dictionary ^VH4YoHNl

UseCase ^5jHkSwJm

NetworkAccess:UseCase is an internal system
enumeration attribute used to track the contextual
state of an endpoint's session. When this attribute
evaluates to Guest Flow (formatted as
NetworkAccess:UseCase = GuestFlow), it explicitly
means that the endpoint has successfully completed
web authentication (WebAuth) via an ISE guest portal
and is now executing a post-portal network
re-authorization. ^moZdvHDG

Conditions ^Aqr4DMJh

Cisco ISE policy conditions are rule-based elements
(attributes, operators, values) used to define
network access, profiling, posture, and guest
services. They enable granular control, allowing
policies based on user identity, device type,
location, or time. ^HhGUzqFa

Library Conditions ^hpcglSuW

Cisco ISE library conditions are pre-configured,
reusable policy elements found under Policy Policy
Elements Conditions. They allow administrators to
define complex logic once (e. ^uwjrTJhj

EAPs ^nAOARBiV

The EAPs condition check the if the client request is
using one of these EAP protocols. The EAP protocols
inside the conditions are PEAP, EAP-TLS and TEAP, the
admin should be using one of these protocols. ^sqTvcsS2

ID_Admin_User ^j1i1NNdc

Users in the AD group InfrastructureAdmin. ^q5XO8w2s

ID_Domain_User ^crXvlg1W

Check if the user is in the AD group
UtentiPubliacqua. ^ecxzwPW3

Blacklist ^gJQRFB7E

MAC Addresses in PBABlacklist. ^y9acGhqc

Whitelist ^ToerMXRQ

MAC Addresses in PBAWhitelist. ^e1Cs4PeV

Authentication Passed ^EH432RCt

Check if the AuthenticationStatus is a Passed ^xuijWYFE

Authentication Failed ^zyrVoViF

Check if the AuthenticationStatus is a Failed ^yCOUgAew

TEAP_Machine ^HFbtLutO

This condition will match if the client using TEAP
protocol has the machine certificate pass the
authentication but fail the user certificate
authentication. ^qthN0c0i

Not_TEAP ^Yz2oLeAl

This condition is used if you want to get a computer
certificate but you don't want the computer
certificate to pass from TEAP EAP protocol. ^g6Yryf1F

Client Authorizations ^GJWqEAyT

Client Authorizations conditions check if the client
user is IDDomainUser and if the EAP protocol they use
is PEAP or TEAP. The domain users should use only
TEAP and PEAP on rare occasions. ^NcOMYsBg

Guest_Flow ^o79HcHiR

Condition is hit if the client request packet has
attribute NetworkAccess:UseCase. When this attribute
evaluates to Guest Flow (formatted as
NetworkAccess:UseCase = GuestFlow), it explicitly
means that the endpoint has successfully completed
web authentication (WebAuth) via an ISE guest portal
and is now executing a post-portal network
re-authorization. ^sbAJTPQx

Smart Conditions ^q3A96mxO

Cisco ISE smart conditions are pre-defined,
intelligent policy building blocks designed to
simplify policy rule creation by abstracting complex
RADIUS attribute-value pairs into human-readable,
usable logic. ^OhB22W2S

Policy Sets ^tDrR8PHI

Policy Sets are high-level containers that group
authentication and authorization rules into
manageable logical buckets. Instead of managing one
giant list of rules, policy sets allow you to
organize network access by use case, such as
separating Wired, Wireless, VPN, or Guest access. ^lo1LuQim

Authentication Policy ^shua3AOi

An authentication policy is a set of rules and
criteria used to verify the identity of a user or
device before they are allowed access to a system. ^hLKkAIWP

MAB (MAC Authentication Bypass) ^5o4DKdSQ

MAC Authentication Bypass (MAB) is a fallback network
access control method that uses a device's MAC
address to grant or deny access. It is primarily used
for "headless" devices that cannot run an 802. ^UsfGH3lH

Dot1X (802.1X) ^3z2ROxKQ

Dot1X (802. 1X) should be the most used/default
authentication policy. ^3qlwt68t

Default ^5s3kuL9l

The Default authentication policy is a catch all type
of policy, set to deny all requests. It's usually
used for requests that the policies before this one
could not catch. ^eEfH57Wa

Authorization Policy ^cMkjwjLE

Authorization Policies decide which Authorization
Profiles the client gets. The authorization policies
order is first match, the client gets authorization
profile of the first authorization policy it hits. ^eGCVZaYZ

Deny Access ^gwj9iszU

The first authorization policy is to check if the
client computer is on the Blacklist, if the MAC
address is found on the Endpoint Identity Group they
will reject the client request, if it's not found
then the policy is not hit and ISE will check the
following policy. ^Udy1XOwH

Admin Access ^UBmcsQxS

Admin Access allows all users in the admin AD group
to get the authorization profile for the VLAN Admin,
which is set to VLAN 850. The authorization profile
is configured in the same way as the one for VLAN 802
except for the VLAN ID. ^d9wo3xJq

Machine Access ^jAei0NZP

The Machine Access is an authorization policy created
for situations where the User Certificate is not
available: - User is not logged-on the domain
computer - New user needs to access a domain computer
- Problems with user certificate In these case the
Machine Access policy provides the client with
Internet access and connection to Domain Controller
and the Certificate Authority Server. The conditions
to hit Machine Access are TEAPMachine and
Authentication Passed. ^7FyfSKtP

Client Access ^vIIecY9f

The Client Access is the default policy for
Publiacqua Domain Users. When this policy is hit the
user gets access to VLAN 802 which is the LAN Client. ^wnDSyR38

RDP Access ^tmc7R5wY

The RDP Access authorization policy is used for
computers that must be accessible most of the time
through RDP but are not servers. The Machine Access
DACL is too limited, so there is a specific policy
that gives access to VLAN 802. ^EZfFlWkY

MAB Access ^cxAri7pp

MAB Access is for computers or devices that, for
various reasons, don't have a supplicant to send 802.
1X authentication packets. ^3eEov44u

Guest Access ^uMicuPAW

The Guest Access is used together with Guest Redirect
and it will be hit only if the client user
authenticates to Guest Redirect. The hit condition is
GuestFlow. ^E2tQkzEl

Guest Redirect ^0sJQ04SM

The Guest Redirect authorization policy is the
catch-all for all devices and users not
authorized/authenticated and for guest users. The hit
condition is include Authentication Failed, WiredMAB
or Wired802. ^UFDxjITO

Results ^ksvvureY

Policy - Results - Authentication ^aLKbdK3e

Authentication Results are results from
authentication policy checks, if the top rule
authentication policy is passed, the server ISE will
check the Allowed Protocols. ^VXND8p8n

Allowed Protocols ^ZSXOJkhf

After the conditions are matched in a top-level rule,
ISE determines what authentication protocols are
permitted for that policy set. If the user send an
authentication request that is not in the allowed
protocol, the request is denied. ^YJXnXVPV

Extensible Authentication Protocols ^d0Ul51Hx

- PAP: With Password Authentication Protocol (PAP),
the username is sent in plaintext, and the password
is optionally encrypted. - CHAP: With Challenge
Handshake Authentication Protocol (CHAP), the
username and password are encrypted using a challenge
sent from the server. ^B5u3LUoi

Policy - Results - Authorization ^2aJ7QuCb

Authorization Results are the results for each
authorization policy. ^p078BlVx

Authorization Profiles ^vLwTYJj0

Authorization Profiles are reusable policy objects
that define the specific access permissions, such as
VLANs, Downloadable ACLs (dACLs), or security group
tags, granted to a user or device after successful
authentication and passing the authorization policy.
! ^Co3arFtF

Pre-Auth-profile ^I2xFoOr1

The Pre-Auth-Profile is used by the Authorization
Policy Machine Access and it sends an ACCESSACCEPT
with the DACL Pre-Auth that limit network access to
Internet, Domain Controller and Certificate
Authority. This DACL is used for computer that have
authenticated with machine certificate but not with
user certificate for various reasons: - The user is
not logged-on, so the user certificate is not
available - There change in user happening - The user
does not have a certificate enrolled In these cases
the DACL allow the connection to Internet, Domain
Controller and Certificate Authority for the update
of GPO, and enrollment of user certificates. ^FptzH3lp

Vlan_802_Lan_Client ^z4SVI46J

Vlan802LanClient should be the default Authorization
Policy for most of domain users. It sends the VLAN
for clients and the re-authentication timer. ^wJwHWbFN

Redirect_Guest_Wired ^FyBKw7UK

The RedirectGuestWired is the first Authorization
Profile for guest users, it send a redirection URL to
the CWA guest portal. - Access Type = ACCESSACCEPT :
Authentication status is a pass -
Tunnel-Private-Group-ID = 1:805 : Put the client in
VLAN 805 - Tunnel-Type = 1:13 : This specifies the
tunneling protocol being used. ^hwJYBmly

Downloadable ACLs ^Xu9xfxju

They are Access Lists that are configured on the
server ISE and are meant to be sent dynamically to
the NAD that calls it. ^lTAnondi

Pre-Auth ^32RLH147

This DACL is used for computer that have
authenticated with machine certificate but not with
user certificate for various reasons: - The user is
not logged-on, so the user certificate is not
available - There change in user happening - The user
does not have a certificate enrolled - ect. In these
cases the DACL allow the connection to Internet,
Domain Controller and Certificate Authority for the
update of GPO, and enrollment of user certificates. ^YXTw2hBt

## Element Links
cRoBchoy: [[PBA - NAC - ISE Server#Identity Management]]

IAl447nI: [[PBA - NAC - ISE Server#Identities]]

rxQggMCP: [[PBA - NAC - ISE Server#Groups]]

whmQVteT: [[PBA - NAC - ISE Server#Endpoint Identity Groups]]

001WiFo3: [[PBA - NAC - ISE Server#PBA_Blacklist]]

n8XuTmTE: [[PBA - NAC - ISE Server#PBA_Printers]]

AjMDf0ny: [[PBA - NAC - ISE Server#PBA_Whitelist]]

623ADJMe: [[PBA - NAC - ISE Server#User Identity Groups]]

jjKnEBYm: [[PBA - NAC - ISE Server#External Identity Sources]]

dBOxQY6g: [[PBA - NAC - ISE Server#External Identity Sources - Certificate Authentication Profile]]

t3KPtQ6h: [[PBA - NAC - ISE Server#External Identity Sources - Active Directory]]

oCjq45RS: [[PBA - NAC - ISE Server#Identity Source Sequences]]

AVNRX7MY: [[PBA - NAC - ISE Server#Admin Access]]

v2IvkooO: [[PBA - NAC - ISE Server#Admin Access - Authorization]]

BDuFjfKl: [[PBA - NAC - ISE Server#Admin Access - Authorization - Permissions]]

ZgQYGOdV: [[PBA - NAC - ISE Server#Menu Access]]

UXNj4ALA: [[PBA - NAC - ISE Server#Data Access]]

vVScWt6N: [[PBA - NAC - ISE Server#Admin Access - Authorization - RBAC Policy]]

u1ON1iZR: [[PBA - NAC - ISE Server#Admin Access - Administrators]]

TB6tlS2W: [[PBA - NAC - ISE Server#Admin Access - Administrators - Admin Groups]]

O6RC4HLG: [[PBA - NAC - ISE Server#Network Resources]]

G8tHmUni: [[PBA - NAC - ISE Server#Network Devices Profiles]]

Qmzpmkcn: [[PBA - NAC - ISE Server#Authentication/Authorization]]

jFqIO1Xn: [[PBA - NAC - ISE Server#Flow Type Conditions]]

VtAkLauo: [[PBA - NAC - ISE Server#Cisco]]

u92h1zj9: [[PBA - NAC - ISE Server#ArubaWireless]]

2jUzMDDs: [[PBA - NAC - ISE Server#Attribute Aliasing]]

puSVg5eJ: [[PBA - NAC - ISE Server#Host Lookup]]

u0iqdJvl: [[PBA - NAC - ISE Server#Permissions]]

7vWpxioF: [[PBA - NAC - ISE Server#Change of Authorization (CoA)]]

Q7ha59Dq: [[PBA - NAC - ISE Server#URL Redirect]]

G3biSL5J: [[PBA - NAC - ISE Server#Network Devices Groups]]

liYc4VRx: [[PBA - NAC - ISE Server#Network Devices]]

8rDzdZA9: [[PBA - NAC - ISE Server#Policy]]

I5huQqBx: [[PBA - NAC - ISE Server#Dictionaries]]

aArvMxW0: [[PBA - NAC - ISE Server#Radius Dictionary]]

Km03WE1n: [[PBA - NAC - ISE Server#NAS-Port-Type]]

Ee1cflyj: [[PBA - NAC - ISE Server#Service-Type]]

hCXJJqXz: [[PBA - NAC - ISE Server#Called-Station-ID]]

FtaHs19O: [[PBA - NAC - ISE Server#Calling-Station-ID]]

Im2wBsyx: [[PBA - NAC - ISE Server#Dynamic VLAN Assignment Attributes]]

JLCpPW4e: [[PBA - NAC - ISE Server#Cisco Dictionary]]

dtft3YCZ: [[PBA - NAC - ISE Server#cisco-av-pair]]

VH4YoHNl: [[PBA - NAC - ISE Server#Network Access Dictionary]]

5jHkSwJm: [[PBA - NAC - ISE Server#UseCase]]

Aqr4DMJh: [[PBA - NAC - ISE Server#Conditions]]

hpcglSuW: [[PBA - NAC - ISE Server#Library Conditions]]

nAOARBiV: [[PBA - NAC - ISE Server#EAPs]]

j1i1NNdc: [[PBA - NAC - ISE Server#ID_Admin_User]]

crXvlg1W: [[PBA - NAC - ISE Server#ID_Domain_User]]

gJQRFB7E: [[PBA - NAC - ISE Server#Blacklist]]

ToerMXRQ: [[PBA - NAC - ISE Server#Whitelist]]

EH432RCt: [[PBA - NAC - ISE Server#Authentication Passed]]

zyrVoViF: [[PBA - NAC - ISE Server#Authentication Failed]]

HFbtLutO: [[PBA - NAC - ISE Server#TEAP_Machine]]

Yz2oLeAl: [[PBA - NAC - ISE Server#Not_TEAP]]

GJWqEAyT: [[PBA - NAC - ISE Server#Client Authorizations]]

o79HcHiR: [[PBA - NAC - ISE Server#Guest_Flow]]

q3A96mxO: [[PBA - NAC - ISE Server#Smart Conditions]]

tDrR8PHI: [[PBA - NAC - ISE Server#Policy Sets]]

shua3AOi: [[PBA - NAC - ISE Server#Authentication Policy]]

5o4DKdSQ: [[PBA - NAC - ISE Server#MAB (MAC Authentication Bypass)]]

3z2ROxKQ: [[PBA - NAC - ISE Server#Dot1X (802.1X)]]

5s3kuL9l: [[PBA - NAC - ISE Server#Default]]

cMkjwjLE: [[PBA - NAC - ISE Server#Authorization Policy]]

gwj9iszU: [[PBA - NAC - ISE Server#Deny Access]]

UBmcsQxS: [[PBA - NAC - ISE Server#Admin Access]]

jAei0NZP: [[PBA - NAC - ISE Server#Machine Access]]

vIIecY9f: [[PBA - NAC - ISE Server#Client Access]]

tmc7R5wY: [[PBA - NAC - ISE Server#RDP Access]]

cxAri7pp: [[PBA - NAC - ISE Server#MAB Access]]

uMicuPAW: [[PBA - NAC - ISE Server#Guest Access]]

0sJQ04SM: [[PBA - NAC - ISE Server#Guest Redirect]]

ksvvureY: [[PBA - NAC - ISE Server#Results]]

aLKbdK3e: [[PBA - NAC - ISE Server#Policy - Results - Authentication]]

ZSXOJkhf: [[PBA - NAC - ISE Server#Allowed Protocols]]

d0Ul51Hx: [[PBA - NAC - ISE Server#Extensible Authentication Protocols]]

2aJ7QuCb: [[PBA - NAC - ISE Server#Policy - Results - Authorization]]

vLwTYJj0: [[PBA - NAC - ISE Server#Authorization Profiles]]

I2xFoOr1: [[PBA - NAC - ISE Server#Pre-Auth-profile]]

z4SVI46J: [[PBA - NAC - ISE Server#Vlan_802_Lan_Client]]

FyBKw7UK: [[PBA - NAC - ISE Server#Redirect_Guest_Wired]]

Xu9xfxju: [[PBA - NAC - ISE Server#Downloadable ACLs]]

32RLH147: [[PBA - NAC - ISE Server#Pre-Auth]]

%%
## Drawing
```compressed-json
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
```
%%