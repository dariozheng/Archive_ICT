---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - claude
  - cisco
icon: SiCisco
iconColor: "#1BA0D7"
---
Cisco DNA Center, is an intent-based network controller and central management platform for Cisco enterprise campus, branch, and WAN networks. It replaces per-device CLI management with a single point of administration that automates the full lifecycle of Catalyst switches, routers, and wireless: onboarding, configuration, software image control, policy enforcement, and health monitoring. The administrator expresses intent in the GUI or through the northbound API, and the controller translates that intent into device configuration and pushes it consistently across the network.

> [!info] Two names, one product 
> The platform was renamed from Cisco DNA Center to Cisco Catalyst Center in 2023. Both names refer to the same product. Older appliances, community posts, and most existing documentation still say "DNA Center", while current Cisco software, support pages, and image downloads use "Catalyst Center". The software-defined architecture (Cisco Digital Network Architecture, or Cisco DNA) is the framework; the controller is its on-premises implementation. That architecture, and the intent-based networking concepts behind it, are covered in [[Cisco Digital Network Architecture]]. This note uses the names interchangeably.

The platform is organised around four configuration domains — [[#Design|Design]], [[#Policy|Policy]], [[#Provisioning|Provisioning]], and [[#Assurance|Assurance]] — sitting on top of a programmable [[#Platform and APIs|platform]] layer. These domains are not independent: each depends on artifacts produced by the one before it, and the [[#Configuration workflow|configuration workflow]] section below makes that dependency order explicit.

## Architecture

_The physical and software shape of the controller, and what it takes to run it reliably._

Catalyst Center is delivered as a dedicated on-premises appliance (or a virtual appliance on VMware ESXi). It is not a passive monitoring tool; it holds the intended state of the network and actively reconciles devices against it.

### Appliance and form factors

Catalyst Center ships as a physical UCS-based appliance in several core sizes (the second- and third-generation appliances differ in CPU core count and the number of devices and endpoints they support), and as a virtual appliance for smaller or lab deployments.

Each appliance presents several network interfaces with distinct roles:

- Enterprise: toward the managed network.
- Management: administrative and GUI access.
- Internet (cloud): software updates, cloud services, and Plug and Play redirection.
- Cluster: intra-cluster communication in a multi-node deployment.

Sizing is driven by the number of managed devices, the number of endpoints, and whether SD-Access and Assurance telemetry are in use, since telemetry ingestion is the heaviest workload.

### The controller stack

Internally the appliance runs a container-based application stack orchestrated by Kubernetes (the platform was historically branded Maglev). Functionality is delivered as packages — system packages and application packages — that are updated independently of the base OS through the [[#System updates and packages|software management]] feature. This is why a Catalyst Center upgrade is really two layers: the underlying system and the application bundles riding on top of it.

### High availability and scale

_Redundancy is achieved by clustering within a site, and by a separate disaster-recovery design between sites._

A single appliance is a valid deployment, but production environments commonly run a three-node cluster. The three nodes share state and present a single virtual IP; a node failure is tolerated without losing the managed state.

> [!warning] Three-node clusters need an odd quorum 
> High availability is built around a three-node cluster precisely so that a surviving majority can maintain quorum. A two-node arrangement does not provide the same protection — losing one node of two breaks quorum. Plan for three nodes if you need the database to survive a node failure.

In-site clustering is distinct from disaster recovery between locations. For site-level resilience, Catalyst Center supports a disaster-recovery deployment built from a main site, a recovery site, and a lightweight witness site that arbitrates which side is active, so the managed state survives the loss of an entire location. Network interface controller (NIC) bonding is supported on second- and later-generation appliances to provide link redundancy toward the management network, using LACP in active mode with a fast rate on the connected switch ports.

## Configuration workflow

_The order in which things must be built, because later domains consume what earlier ones produce._

The single most important thing to internalise about Catalyst Center is that configuration is sequential. You cannot meaningfully [[#Provisioning|provision]] a device before it is in [[#Inventory|inventory]], and provisioning only does something useful if the [[#Design|design]] hierarchy and settings already exist for the site the device belongs to. The recommended order is below.

```text
                 ┌──────────────────────────────────────────────┐
                 │                    DESIGN                      │
                 │  hierarchy · network settings · credentials    │
                 │  IP pools · wireless · images · profiles       │
                 └───────────────────────┬────────────────────────┘
                                         │  settings inherited by each site
                                         ▼
   ┌────────────────┐        ┌───────────────────────────┐
   │   DISCOVERY     │ ─────▶ │          INVENTORY         │
   │ CDP / LLDP /    │        │  managed devices · roles   │
   │ IP range / CIDR │        │  compliance · config drift │
   └────────────────┘        └─────────────┬───────────────┘
                                           │  assign device to a site
                                           ▼
                             ┌───────────────────────────┐
                             │        PROVISIONING        │
                             │  push site settings +      │
                             │  Day-N templates + image   │
                             └─────────────┬───────────────┘
                               ┌───────────┴────────────┐
                               ▼                         ▼
                     ┌───────────────────┐    ┌────────────────────┐
                     │       POLICY        │    │      ASSURANCE      │
                     │  SGT / GBAC · QoS   │    │  telemetry-driven   │
                     └───────────────────┘    └────────────────────┘
```

[[#Plug and Play|Plug and Play]] is an alternative entry point into this flow: instead of discovering an already-configured device, a factory-fresh device contacts the controller and is onboarded unattended, after which it lands in inventory like any other device.

## Design

_The foundation. Everything provisioned later inherits from what is defined here._

The Design domain (`Design` in the GUI) is where global and per-site intent is declared once and then reused. Nothing here touches a device directly; it builds the model that [[#Provisioning|provisioning]] later renders onto hardware.

### Network hierarchy

_A tree of locations that scopes every setting and profile._

The hierarchy is `Global > Area > Building > Floor`. Areas are organisational containers; buildings carry a civic address and geographic coordinates; floors carry a floor plan image used for wireless heatmaps and AP placement. Settings defined at a parent level are inherited by children, and a child can override an inherited value. Designing the hierarchy first matters because credentials, servers, IP pools, and profiles are all assigned against nodes in this tree.

### Network settings

_The shared infrastructure values that get pushed to devices during provisioning._

Under `Design > Network Settings`, the following are defined per site (or globally and inherited):

- [[#Device credentials|Device credentials]] for management access.
- Server and protocol settings: AAA, DHCP, DNS, NTP, time zone, banner, syslog, SNMP traps, and NetFlow collector.
- [[#IP address pools|IP address pools]] for automation and SD-Access.
- [[#Service provider profiles|Service provider profiles]] for WAN QoS.
- [[#Wireless settings|Wireless settings]] for SSIDs and RF behaviour.

#### Device credentials

_How the controller authenticates to a device to manage it._

Multiple credential sets are stored and one of each type is marked as the site default. The relevant types:

- CLI credentials (username, password, and enable password) for configuration management and the running-config archive.
- SNMP read and SNMP write community strings (SNMPv2c), or SNMPv3 with auth and privacy, used for [[#Discovery|discovery]] and inventory collection.
- HTTPS read and write credentials for platforms that expose a programmatic interface.
- NETCONF with a chosen port (commonly 830), required for model-driven [[#Telemetry activation|telemetry]] on supported IOS-XE platforms.

> [!important] Credentials defined here must match the device 
> [[#Discovery|Discovery]] and provisioning both use these credentials. If SNMP is wrong the device is only partially collected; if CLI or NETCONF is wrong the device cannot be fully managed. A device therefore needs a working baseline of SSH, SNMP, and (for telemetry) NETCONF before the controller can manage it — which is also what [[#Device controllability|device controllability]] can establish automatically.

#### Network and server settings

_The AAA, DHCP, DNS, NTP, logging, and flow-export targets every site needs._

These values are rendered into device configuration at [[#Provisioning|provisioning]] time. AAA is defined in two roles that should not be confused: servers for network device administration (device login, typically TACACS+) and servers for client and endpoint authentication (802.1X and MAB, typically RADIUS to [[#Cisco ISE and pxGrid|Cisco ISE]]). DHCP, DNS, and NTP servers establish baseline reachability and time synchronisation; syslog and SNMP-trap destinations and the NetFlow collector establish baseline observability.

#### IP address pools

_Address space the controller can hand out for automation and fabric onboarding._

Global pools are defined as CIDR blocks (optionally synchronised from an [[#IP address management|external IPAM]]). Subsets are then reserved per site. These reserved pools feed [[#LAN Automation|LAN Automation]] and [[#Virtual networks and host onboarding|SD-Access host onboarding]], where a pool is bound to a virtual network and a gateway is allocated automatically.

#### Service provider profiles

_Named WAN bandwidth and QoS classes for provider-facing links._

SP profiles describe the service-provider class model (for example, a four- or eight-class model) so that QoS marking and queuing toward a WAN provider can be provisioned consistently.

#### Wireless settings

_SSIDs, RF behaviour, and AP grouping for wireless provisioning._

Enterprise and guest SSIDs, their security (for example WPA2/WPA3 Enterprise tied to [[#Cisco ISE and pxGrid|ISE]], or a guest portal), RF profiles, and AP profiles are defined here and later applied when a wireless LAN controller and its access points are provisioned. Floors in the [[#Network hierarchy|hierarchy]] provide the maps onto which APs are positioned.

### Image repository

_Where device software images live and where a per-role golden image is declared._

Images are imported into the repository (`Design > Image Repository`) from a managed device, a URL, or cisco.com, and an image is then marked golden for a device family, role, and site. The golden mark is the intended-state declaration that the [[#Software Image Management|SWIM]] workflow enforces.

### Network profiles

_The binding layer that ties [[#Templates|templates]] and settings to sites._

Network profiles (`Design > Network Profiles`) come in types such as switching, routing, wireless, and assurance. A profile is assigned to one or more sites, and it is the object through which Day-0 onboarding templates and [[#Day-0 and Day-N templates|Day-N]] configuration templates are attached. When a device in a profiled site is [[#Provisioning|provisioned]], the controller renders the attached templates and pushes them. This is the mechanism that connects the abstract template to a concrete site.

### Device controllability

_Configuration the controller pushes on its own to make a device manageable._

Device controllability is a global or site-level setting that lets Catalyst Center automatically push a baseline of management configuration to a device when it is discovered or provisioned — for example SNMP and NETCONF settings, IP device tracking, the controller's certificate, and the configuration needed for telemetry. It removes the need to pre-stage every management detail by hand, but it also means the controller adds and modifies configuration beyond what is in any explicit [[#Templates|template]].

> [!warning] Device controllability changes config without a template Because device controllability writes configuration on its own initiative, it can surprise an operator who expects a device to carry only what a template defined. Review which controllability settings are enabled, especially in a brownfield network where the controller's additions may overlap with configuration that is already present.

## Discovery

_Bringing existing, already-reachable devices under management._

Discovery (`Tools > Discovery`) finds devices on the network and places them in [[#Inventory|inventory]]. It is the path for brownfield devices that already have a working management configuration, as opposed to [[#Plug and Play|Plug and Play]] for factory-fresh hardware.

### Discovery methods

_Three ways to tell the controller where to look._

- CDP: seed one device and let the controller walk Cisco Discovery Protocol neighbours up to a configurable hop count.
- LLDP: the vendor-neutral equivalent for neighbour-based discovery.
- IP address range or CIDR: scan an explicit range or subnet.

### Discovery credentials and protocols

_What the controller needs to log in and read state._

Discovery uses the global [[#Device credentials|device credentials]] or a discovery-specific set. SNMP is required to collect inventory detail; CLI is required to manage configuration and archive the running config; NETCONF is required where model-driven [[#Telemetry activation|telemetry]] will be enabled. A device discovered without working SNMP will appear with incomplete data.

### Preferred management address

_Which interface address the controller should treat as the device's identity._

Discovery can be told to prefer a device loopback as the management address rather than the interface it was first reached on, which keeps management stable if physical interfaces change.

## Inventory

_The authoritative database of managed devices and their current state._

Inventory (`Provision > Inventory`) is the single source of truth. Every later action — [[#Provisioning|provisioning]], [[#Software Image Management|image upgrades]], [[#Policy|policy]] — operates against the devices recorded here.

### Device reachability and managed state

_How the controller tracks whether it is actually in control of a device._

A device is shown as managed, unmanaged, unreachable, or partially collected. Reachability is verified with ICMP and SNMP, and the controller periodically resyncs to refresh collected data and re-archive the configuration.

### Device roles

_The topology and targeting label assigned to each device._

Each device is assigned a role — access, distribution, core, border router, or unknown. Roles drive the topology view and, importantly, scope the [[#Golden images|golden image]] target so that an access-layer image is not applied to a core device.

### Configuration drift and compliance

_Detecting when a device no longer matches its intended configuration._

Catalyst Center continuously compares each device against intended state and flags compliance violations: configuration drift between intended and running config, a mismatch between startup and running config, an image that differs from the golden image, and outstanding security advisories. Compliance is where the controller surfaces unmanaged change, and it interacts directly with how [[#Compliance markers|templates declare which lines to ignore]].

### Device replacement

_Swapping failed hardware while preserving intended state._

The Return Material Authorization (RMA) workflow lets a faulty device be replaced by a like-for-like unit: the replacement is onboarded, the failed device's intended configuration and software image are applied, and inventory is updated to point at the new serial number.

## Provisioning

_Rendering design intent onto real devices._

Provisioning (`Provision > Inventory`, then the provision action) is the step that actually writes configuration to hardware. Everything it pushes comes from [[#Design|Design]].

### Assigning devices to sites

_Placing a device in the hierarchy so it inherits the right settings._

Before provisioning, a device is assigned to a site in the [[#Network hierarchy|hierarchy]]. This assignment determines which [[#Network and server settings|server settings]], credentials, and [[#Network profiles|network profile]] (and therefore which templates) apply.

### The provisioning workflow

_What a provision action pushes, and in what shape._

Provisioning renders the inherited [[#Network settings|network settings]] (AAA, DHCP, DNS, NTP, syslog, SNMP, NetFlow) into device configuration, applies any [[#Day-0 and Day-N templates|Day-N templates]] bound through the [[#Network profiles|network profile]], and — for wireless — applies SSIDs and RF and AP profiles to the WLC and its access points. The controller shows a preview of the generated configuration before it is deployed.

### Telemetry activation

_Turning on the data feed that the monitoring domain depends on._

Provisioning is also where telemetry is enabled (often surfaced as an "Update Telemetry Settings" or "Enable Telemetry" action). This pushes the model-driven telemetry and NETCONF subscriptions that feed [[#Assurance|Assurance]]. Without this step, a device is managed but produces no health data.

## Templates

_The programmable core of configuration. Where reusable, parameterised device config is authored._

Templates are how Catalyst Center applies configuration that goes beyond the standardised [[#Network settings|network settings]] — anything site-specific, feature-specific, or organisation-specific. For an environment that already maintains hand-built configuration, templates are the bridge between that configuration and automated, repeatable deployment.

### Template Hub and projects

_Where templates are organised, versioned, and committed._

Templates live in projects in the Template Hub (`Tools > Template Hub`; the interface was named Template Editor before release 2.3.5). A special "Onboarding Configuration" project holds Day-0 templates used by [[#Plug and Play|Plug and Play]]. The editor offers syntax checking, a system-variable assistant, version history, and a template simulator that renders a template against sample values without touching a device. A template must be committed to a version before it can be attached to a [[#Network profiles|network profile]] and provisioned; uncommitted edits are drafts.

### Regular and composite templates

_Single templates, and ordered sequences of them._

A regular template is one body of configuration. A composite template is an ordered collection of regular templates that are applied as a unit, which is useful when a device's configuration is naturally built from independent, separately maintained blocks.

### Velocity and Jinja2

_The two templating languages, and how to choose._

Template bodies are written in either Apache Velocity (VTL) or Jinja2. Both support variable substitution, conditionals, and loops, and both can reach the device-context [[#Variables and bindings|system bind variables]] described below; the choice between them is largely a matter of preference and existing skill. Velocity uses `#if`, `#foreach`, and `$variable`; Jinja2 uses `{% if %}`, `{% for %}`, and `{{ variable }}`.

#### Variables and bindings

_How a template receives per-device and per-interface values._

Variables can be free-form (the operator types a value at provision time), constrained to a selection list, or given a default and marked required. Beyond operator-supplied variables, Catalyst Center exposes system bind variables — special read-only variables, all prefixed with a double underscore, that it populates from inventory and global settings rather than prompting for. The two most used are `__device` (attributes of the target device, read in dot notation such as `__device.hostname`) and `__interface` (a list of the device's interfaces, iterated to read attributes such as `portName`, `vlanId`, and `portMode`). These bindings are what let one template adapt to every device it is pushed to.

```bash
{% block interfaces %}
{% for interface in __interface %}
{% if interface.vlanId == 802 %}
interface {{ interface.portName }}
 source template ACCESS-PORT-TEMPLATE
{% elif interface.portMode == 'trunk' %}
interface {{ interface.portName }}
 ip dhcp snooping trust
 switchport trunk allowed vlan add 802,805,850
{% endif %}
{% endfor %}
{% endblock %}
```

> [!note] System bind variables are not available at Day-0 System bind variables and [[#Interactive commands|interactive commands]] both depend on the device already existing in inventory, so neither can be used in onboarding (Day-0) templates — at first contact through [[#Plug and Play|Plug and Play]] the device has no inventory record yet. Reserve them for [[#Day-0 and Day-N templates|Day-N]] templates.

#### Conditionals and loops

_Branching and iteration inside a template body._

Conditional blocks include or exclude configuration based on a variable or a device attribute, and loops repeat a block across a collection (most commonly the interface list). This is how a single template can, for example, apply one stanza to access ports and a different stanza to trunks within the same push.

### Day-0 and Day-N templates

_Onboarding configuration versus ongoing configuration._

A Day-0 template lives in the onboarding project and is applied by [[#Plug and Play|Plug and Play]] when a factory device first comes up. A Day-N (regular) template is everything applied during or after [[#Provisioning|provisioning]] through a [[#Network profiles|network profile]] — the steady-state configuration of a managed device. Day-0 templates are deliberately limited (no [[#Variables and bindings|system bind variables]] and no interactive commands); Day-N templates have the full feature set.

### Interactive commands

_Answering device CLI prompts inside an automated push._

Some IOS-XE commands prompt for confirmation, which would stall an unattended push. Catalyst Center handles this with interactive-command markers: the command is wrapped in `#INTERACTIVE` ... `#ENDS_INTERACTIVE`, and within it the prompt and the answer are separated by `<IQ>` (the expected interactive question, given as a regular expression) and `<R>` (the response).

```bash
#INTERACTIVE
no access-session mac-move deny<IQ>.*Do you wish to continue\? \[yes\]:\s*<R>yes
#ENDS_INTERACTIVE
```

The controller issues the command, matches the device's confirmation prompt with the regex after `<IQ>`, and sends the text after `<R>` (here `yes`), so the push completes without operator intervention. When the prompting command must run in privileged EXEC mode, the interactive block is nested inside an [[#Enable-mode and multi-line commands|enable-mode block]].

### Enable-mode and multi-line commands

_Constructs for commands that need privileged EXEC mode or span multiple lines._

By default a template's commands are sent in global configuration mode, one line at a time. Two constructs handle the exceptions:

- Enable-mode commands are wrapped in `#MODE_ENABLE` ... `#MODE_END_ENABLE`, which runs the enclosed commands in privileged EXEC mode (for example `write memory`, or a `show` used to drive an [[#Interactive commands|interactive]] step). An interactive block may be nested inside.
- Multi-line commands — banners, certificate blocks, or a single long command wrapped for readability — are enclosed in `<MLTCMD>` and `</MLTCMD>` tags. The tags must each sit on their own line (not the same line) and must not begin with a space; without them, each line is sent to the device separately.

```bash
#MODE_ENABLE
write memory
#MODE_END_ENABLE
```

### Compliance markers

_Telling the compliance engine which lines not to treat as drift._

Configuration that legitimately differs from intended state, or that should never trigger a [[#Configuration drift and compliance|drift]] flag, can be fenced with `! @start-ignore-compliance` and `! @end-ignore-compliance`. The leading `!` makes these lines comments to the device, so IOS-XE ignores them, while the Catalyst Center compliance engine reads them as directives to exclude the enclosed configuration from drift evaluation.

```bash
! @start-ignore-compliance
radius-server vsa send authentication
radius-server vsa send accounting
! @end-ignore-compliance
```

> [!note] Why fence these lines Commands like `write memory`, or settings that vary per device or are re-ordered by the parser, would otherwise be reported as configuration drift on every compliance check. Fencing them keeps the compliance report meaningful — it flags only the differences that actually matter.

### Design conflicts

_Where template CLI overlaps with the controller's own intent-based configuration._

Some configuration Catalyst Center manages through its intent-based workflows (the GUI features for [[#Network settings|network settings]], wireless, [[#Policy|policy]], and [[#SD-Access fabric|SD-Access]]) and some you write as raw CLI in a template. When a template pushes a command that the controller also manages by intent, the two can compete, and the outcome depends on push order. The editor's design-conflict check flags these commands so they can be removed from the template and left to intent provisioning, which is the recommended division of labour.

> [!warning] Don't template what the controller provisions by intent Re-issuing intent-managed configuration from a template invites configuration drift and unpredictable overwrites. Use templates for what intent does not cover, and let the built-in workflows own the rest.

### Binding templates through network profiles

_The last step that makes a template take effect._

A committed template does nothing until it is attached to a [[#Network profiles|network profile]] and that profile is assigned to a site. When a device in the site is [[#Provisioning|provisioned]], the template is rendered with its variable values and the device context, and pushed. Authoring, committing, binding, and provisioning are four distinct steps, and skipping the binding step is the most common reason a template "isn't applying".

## Software Image Management

_Standardising and upgrading device software at scale. Commonly abbreviated SWIM._

SWIM enforces a consistent software version across the estate, replacing manual per-device upgrades.

### Golden images

_The declared correct image for a device family and role._

An image marked golden in the [[#Image repository|image repository]] is the intended software state for a given device family, [[#Device roles|role]], and site. Any managed device not running its golden image is flagged in [[#Configuration drift and compliance|compliance]].

### Distribution and activation

_The two-phase, low-risk upgrade procedure._

Upgrades are split deliberately: distribution copies the image to the device's flash without disrupting traffic, and activation reloads the device onto the new image (with In-Service Software Upgrade on platforms that support it). Separating the two means staging can be done during the day and the disruptive reload scheduled for a maintenance window.

### Upgrade readiness

_Pre-flight checks before an activation._

Before activation, the controller runs readiness pre-checks — flash space, configuration register, hardware and version compatibility — so that an upgrade is only attempted on devices that will succeed. Pre- and post-upgrade checks can be compared to confirm the device returned to a healthy state.

## Plug and Play

_Unattended Day-0 onboarding of factory-fresh devices. Commonly abbreviated PnP._

PnP brings up a brand-new device with no manual console session, which is what makes remote-site deployment without an on-site engineer possible.

### The onboarding workflow

_How a factory device finds the controller and configures itself._

A factory-default device with network connectivity locates the PnP server (Catalyst Center) through one of several mechanisms: DHCP option 43, a DNS entry for `pnpserver`, or cloud redirection via Cisco's PnP Connect service tied to the Smart Account. Once it reaches the controller, it requests its configuration.

### Claiming devices

_Authorising a device and assigning what it should become._

Devices can be pre-registered by serial number (planned) or appear as unclaimed when they call home. Claiming a device assigns it to a site, selects the software image to load, and applies the Day-0 [[#Day-0 and Day-N templates|onboarding template]] from the onboarding project. The device then provisions itself unattended and lands in [[#Inventory|inventory]] as a managed device, after which normal [[#Provisioning|provisioning]] applies.

## LAN Automation

_Zero-touch buildout of an IS-IS routed-access underlay from a seed device._

LAN Automation is the alternative to standing up a new routed network by hand. From one already-managed seed device it discovers the factory-default switches cabled beneath it, brings them to their [[#Golden images|golden image]] through [[#Software Image Management|SWIM]], and pushes a best-practice Layer 3 routed-access configuration to the whole tier with no per-device CLI. It is most often used to build the underlay an [[#SD-Access fabric|SD-Access fabric]] runs on, but the routed network it produces is equally valid for a traditional routed-access design. It reuses the [[#Plug and Play|Plug and Play]] onboarding mechanism, so the same prerequisites apply: a [[#Network hierarchy|network hierarchy]], global [[#Network and server settings|network servers]] and [[#Device credentials|device credentials]], a reserved [[#IP address pools|IP pool]], and at least the seed device already in [[#Inventory|inventory]].

### Seed devices and discovery

_How the controller reaches and onboards the new switches._

A session runs from a seed (primary) device — an existing, managed switch at the core or distribution layer — and optionally a peer seed so that discovered switches can be dual-homed. The controller configures a temporary DHCP scope on the seed; the factory-default Catalyst 9000 switches cabled to it boot as PnP agents, obtain an address, and contact the controller. Discovery extends a maximum of two hops from the seed, so starting the boundary at the core or distribution layer is what lets a run reach the access layer. Devices farther than two hops may be seen but are not automated.

### What LAN Automation provisions

_The underlay configuration written to each discovered device._

Addresses come from a reserved IP pool of type LAN. From it, each discovered device receives a unique /31 on every point-to-point link and a /32 for `Loopback0`, which becomes the device's router ID and management address. The controller also sets the system MTU, enables IP routing, brings the device to its golden image, and configures the routing protocol:

- IS-IS is always the underlay IGP. It is chosen because its adjacencies form without any IP dependency, it can peer over loopbacks, and it treats IPv4, IPv6, and non-IP traffic alike — all of which make an automated, ordered buildout more robust.
- Underlay multicast is an optional attribute (needed for fabric Layer 2 flooding and native multicast); when enabled, the seeds are configured as PIM rendezvous points.
- The LAN pool summary can optionally be advertised into a BGP process preconfigured on the seeds, so the controller keeps reachability to the discovered devices without static routes.

> [!note] Why IS-IS rather than OSPF or EIGRP IS-IS runs directly over Layer 2 and does not need an IP address to form an adjacency, so the controller can bring neighbours up before addressing has converged. That property, together with native dual-stack support and loopback peering, is why Cisco standardised the automated underlay on IS-IS.

### Starting and stopping a session

_The two phases, and what actually happens at Stop._

A run is launched from `Provision > LAN Automation` by selecting the seed (and peer), the seed interfaces to use, the target site, and the IP pool; up to five sessions can run across sites at once. Start opens the session and onboards devices as they appear — DHCP, image, and base configuration are applied while the session stays open. Stop finalises it: the point-to-point links between the seed and the discovered devices are converted to routed Layer 3 links, the temporary DHCP scope and VLAN 1 configuration are removed, and the DHCP subpool is returned to the LAN pool. The devices then appear in [[#Inventory|inventory]] as ordinary managed devices, ready to be [[#Provisioning|provisioned]] and to receive [[#Templates|templates]].

> [!important] The underlay isn't finished until you Stop The Layer 3 conversion and cleanup happen at Stop, not at Start. A session left open keeps the seed's temporary DHCP scope and the discovered devices on transient addressing, so a run must be stopped to reach its final, supported state.

## Policy

_Defining who and what may communicate, and how traffic is treated._

The Policy domain (`Policy` in the GUI) is the intent layer for access control and quality of service. Its access-control capabilities depend on [[#Cisco ISE and pxGrid|ISE]] as the runtime AAA and distribution engine.

### Group-Based Access Control

_Segmentation by security group rather than by IP address._

Group-Based Access Control (GBAC) is Catalyst Center's front end to Cisco TrustSec. Endpoints are assigned a Scalable Group Tag (SGT) at authentication, and a group-based policy matrix defines which source groups may reach which destination groups, independent of IP addressing. Catalyst Center authors the SGTs and the policy matrix and synchronises them to [[#Cisco ISE and pxGrid|ISE]]; ISE assigns the SGT to each endpoint at authorization and distributes the matching Security Group ACLs (SGACLs) to the network devices, which carry out the actual enforcement.

> [!important] ISE is a prerequisite for group-based policy Group-Based Access Control is only available when [[#Cisco ISE and pxGrid|Cisco ISE]] is integrated as the authentication and policy server. On installation or upgrade, the controller checks for a connected ISE of a compatible version; if it is absent, the platform installs but group-based policy stays disabled. Existing SGT and policy data is brought over through a one-time policy data migration from ISE.

### Application policy

_End-to-end QoS driven by application identity._

Application policy lets you classify applications into groups, mark each as business-relevant, default, or business-irrelevant, and bind them to a queuing profile. The controller then renders the corresponding QoS marking and queuing configuration (using the [[#Service provider profiles|SP profile]] class model on WAN links) and pushes it to the devices in scope.

### IP-based access control

_Classic ACL-style control for non-SGT environments._

Where SGT-based segmentation is not in use, IP-based access control policies apply permit and deny rules between IP pools, giving a more traditional access-list model managed centrally.

## Assurance

_Continuous, telemetry-driven visibility into network and client health._

Assurance (`Assurance` in the GUI) consumes the [[#Telemetry activation|telemetry]] enabled at provisioning to score health and surface problems. It is primarily a monitoring domain, but it has real configuration dependencies — chiefly that telemetry must be turned on and, for synthetic testing, that sensors and tests are defined.

### Health dashboards

_Aggregated health scores across the network._

Assurance presents overall, network, client, and application health dashboards, each rolling individual metrics into a score and letting an operator drill from a site down to a single device or client session. Per-entity Device 360, Client 360, and Application 360 views gather everything known about one device, client, or application onto a single timeline.

### Issues and machine reasoning

_Automated detection and guided root-cause analysis._

Detected problems are raised as issues, prioritised by impact. The Machine Reasoning Engine offers guided or automated root-cause workflows for common failure patterns, reducing the manual correlation an engineer would otherwise do by hand.

### Sensors and synthetic tests

_Actively probing the network from the client's perspective._

Beyond passively collected telemetry, dedicated sensors or access points acting as sensors run synthetic tests — association, authentication against [[#Cisco ISE and pxGrid|ISE]], DHCP, DNS, and application reachability — so that client experience is measured proactively rather than only after a user complains. The tests, their target SSIDs, and their schedule are configured in Assurance. For deeper wireless troubleshooting, Intelligent Capture collects on-demand or scheduled packet and RF data directly from access points and clients.

## Integrations

_Connecting Catalyst Center to the surrounding ecosystem._

Integrations are configured under `System > Settings` and the [[#Bundles and integration settings|integration bundles]]. The most consequential by far is ISE.

### Cisco ISE and pxGrid

_The identity and policy partner, integrated in both directions._

Catalyst Center integrates Cisco ISE as its authentication and policy server. The connection uses pxGrid for contextual exchange (endpoint and group data) together with an ERS API connection for configuration, and it is the foundation for [[#Group-Based Access Control|group-based access control]] and [[#SD-Access fabric|SD-Access]]. The integration runs in two directions worth distinguishing:

- Catalyst Center to ISE: the controller programmes SGTs and group-based policy into ISE and consumes endpoint context from it.
- ISE to Catalyst Center: ISE can also act as the [[#External authentication|external authentication]] source for the Catalyst Center GUI itself, returning an administrative role to RADIUS logins through a `cisco-av-pair` of the form `ROLE=<role-name>` (for example `ROLE=SUPER-ADMIN-ROLE`).

### IP address management

_Synchronising address space with an external IPAM._

An external IP Address Manager (such as Infoblox or BlueCat) can be integrated so that the [[#IP address pools|address pools]] used for automation are sourced from, and reconciled with, the organisation's authoritative IPAM rather than maintained twice.

### IT service management

_Tying network change and incidents into the service desk._

ITSM integration (most commonly ServiceNow) links Assurance issues and provisioning changes to the service-management process, so that incidents can be opened automatically and configuration changes can flow through change control.

### Other integrations

_Security analytics, WAN, and collaboration._

Additional integrations include Cisco Secure Network Analytics (Stealthwatch) for flow-based security telemetry, Catalyst SD-WAN (vManage) for WAN orchestration alongside the campus, and Webex for client experience correlation. These are enabled through the relevant integration bundles as needed.

## SD-Access fabric

_An optional overlay architecture for policy-based, location-independent segmentation._

SD-Access is a major, optional capability rather than a baseline requirement; a deployment can manage a traditional campus through [[#Design|Design]] and [[#Provisioning|provisioning]] without ever building a fabric. Where it is used, Catalyst Center automates the construction of an overlay network on top of a routed underlay.

### Underlay and overlay

_The transport beneath the fabric, and the virtual network on top._

The underlay is a routed IP network (built manually or by [[#LAN Automation|LAN Automation]], which uses IS-IS). The overlay carries user traffic and is built on three planes: a LISP control plane for endpoint location and resolution, a VXLAN data plane that encapsulates user traffic across the underlay, and a Cisco TrustSec policy plane that carries [[#Group-Based Access Control|SGT]] for segmentation. Separate fabric sites are joined by a transit: an IP-based transit across a traditional routed network, or an SD-Access transit that preserves virtual-network and SGT information end to end between sites.

### Fabric roles

_The functions devices perform inside a fabric._

- Control plane node: the LISP map server and map resolver that tracks where every endpoint is.
- Border node: the gateway between the fabric and the outside world (other fabrics, the data centre, the internet).
- Edge node: the access layer that endpoints connect to and where they are registered into the fabric.
- Fabric WLC and fabric-mode APs extend the same model to wireless.

### Virtual networks and host onboarding

_Mapping address pools and groups into segmented virtual networks._

Virtual networks (VNs) are the fabric's VRFs, providing macro-segmentation. Host onboarding binds an [[#IP address pools|IP pool]] to a VN, assigns [[#Group-Based Access Control|SGTs]] for micro-segmentation within it, and selects the port authentication template (closed, open, or low-impact) that governs how endpoints are admitted. Every edge node shares the same distributed anycast gateway for a given pool, so an endpoint's default gateway is identical wherever it connects and roaming does not require renumbering.

## System administration

_Operating the controller itself: access, data protection, and software._

System settings (`System` in the GUI) govern the platform rather than the managed network.

### Users and role-based access control

_Controlling who can do what inside Catalyst Center._

Access is governed by role-based access control (RBAC). Built-in roles include SUPER-ADMIN (full control), NETWORK-ADMIN, and OBSERVER (read-only), and custom roles can scope access to specific functional areas. The role a user holds is exactly what the [[#External authentication|external authentication]] integration returns for remote logins.

### External authentication

_Delegating GUI login to an external AAA server._

The Catalyst Center GUI can authenticate administrators against an external RADIUS or TACACS+ server such as [[#Cisco ISE and pxGrid|Cisco ISE]]. The server returns the user's Catalyst Center role in a `cisco-av-pair` containing `ROLE=<role-name>` (for example `ROLE=SUPER-ADMIN-ROLE`), which the controller maps to the corresponding [[#Users and role-based access control|RBAC role]]. A local fallback account should always be retained so that loss of the AAA server does not lock administrators out.

### Backup and restore

_Protecting the controller's database and configuration._

Backups are written to an external server (commonly NFS) and can be scheduled. Because the controller holds the intended state of the entire network, a current backup is operationally critical — a restore rebuilds the managed model, not just the appliance.

### System updates and packages

_Keeping the platform current across its two layers._

Software management updates the system package and the application packages, sourced either from the cloud catalogue or, for isolated networks, from an air-gapped ISO. Releases follow a time-based cadence (roughly three feature releases per year with periodic patches), and Cisco designates a recommended release for production. Upgrade paths between versions are constrained, so the supported path should be checked before any jump.

### Certificates

_Establishing trust for the GUI and for device communication._

A PKI server certificate can be imported so that the GUI and API are presented over a trusted certificate rather than the self-signed default, and the controller's trust store holds the certificates needed to validate integrated systems and managed devices.

## Platform and APIs

_The programmable layer beneath the GUI. Everything the interface does is an API call underneath._

The Platform domain (`Platform` in the GUI) exposes Catalyst Center for automation and integration, and is what makes the controller a building block rather than a closed appliance.

### Intent API

_The northbound REST interface for automating the controller._

The Intent API is a northbound REST API that mirrors the GUI's intent model: discovery, inventory, sites, templates, provisioning, and policy can all be driven programmatically. Calls are authenticated with a token and scoped by the caller's [[#Users and role-based access control|RBAC]] role, so API access respects the same permission model as the GUI. Alongside it, westbound integration APIs connect external systems such as [[#IT service management|ITSM]] and [[#IP address management|IPAM]], and a southbound multivendor SDK with device packs lets the controller manage selected third-party devices.

### Bundles and integration settings

_Toggling the controller's integration and feature packages._

![[Pasted image 20260707174858.png]]

Integration bundles (for example ITSM, or the Rogue Management and aWIPS application) are enabled and configured here. Enabling a bundle exposes its specific settings and, where relevant, its API endpoints.

### Events and notifications

_Pushing controller events outward to other systems._

![[Pasted image 20260707174945.png]]

Catalyst Center can publish events — from Assurance issues to system notifications — to external consumers over webhooks, email, syslog, or SNMP, driven by an event catalogue that enumerates what can be subscribed to. This is how the controller feeds dashboards, chat-ops, and ticketing systems in near real time. A separate reporting engine produces scheduled and on-demand reports — inventory, compliance, client, and executive summaries — in formats such as PDF and CSV.

## Licensing

_What is required to manage devices and unlock feature tiers._

Catalyst Center is the management console; the right to use its features is carried by per-device subscription licenses. Historically these were Cisco DNA Essentials, Advantage, and Premier tiers, now aligned under the Cisco Networking subscription model that accompanied the Catalyst rebrand. The higher tiers unlock the more advanced capabilities — for instance, [[#SD-Access fabric|SD-Access]] and full [[#Assurance|Assurance]] require Advantage-level licensing. Licenses are managed through Cisco Smart Licensing against a Smart Account in Cisco Smart Software Manager, and the controller reports compliance against the entitlements it sees.