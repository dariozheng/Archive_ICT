---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/sase
---
<mark style="background: #FFB8EBA6;"><strong>Prisma SD-WAN</strong> provides a <strong>software-defined wide area network</strong> (SD-WAN) <strong>solution</strong> that transforms <strong>legacy wide area networks</strong> (WANs)</mark> <mark style="background: #FF5582A6;">into a simplified, secure, application-defined fabric</mark>, virtualizing <u>heterogeneous underlying transports</u> (MPLS, 5G, LTE, Broadband) <mark style="background: #FFB86CA6;">into a <strong>unified hybrid WAN</strong></mark>. 

<strong>Prisma SD-WAN</strong> controls <strong>network application performance</strong> based on <strong>application-performance service-level agreements</strong> (<strong>SLAs</strong>) and business priorities.

Prisma SD-WAN is a <strong>Generation 2</strong> (<strong>GEN2</strong>) <strong>SD-WAN solution</strong> that provides [[security glossary#end-to-end application performance|end-to-end application performance]] through application identification, visibility, and [[networking glossary#service-level assurance|service-level assurance]]. 

<mark style="background: #FFF3A3A6;">In addition to monitoring packet-based metrics, Prisma SD-WAN also gathers data on the performance of individual <strong>applications</strong></mark>.
<mark style="background: #CACFD9A6;">Prisma SD-WAN collects data on metrics such as <strong>app response time</strong>, <strong>app transaction time</strong>, and <strong>app reachability</strong>, as well as <strong>mean opinion score</strong> (<strong>MOS</strong>) for voice</mark>. 
<mark style="background: #BBFABBA6;">Prisma SD-WAN uses all of this application-based information (and Layer 3 packet-based data) in its <strong>path selection algorithm</strong></mark> <mark style="background: #ABF7F7A6;">to ensure that each application session receives the best performance at any given time</mark>. 
Users evaluate their experience based on the performance of the applications they use, rather than network jitter or loss. Therefore, we must deliver a network that can respond in real time to deliver the best application performance SLA.

<mark style="background: #ADCCFFA6;">Prisma SW-WAN can gather statistics such as <strong>TCP transaction</strong> and <strong>initialization failures</strong> on a per-application basis. Prisma SD-WAN can measure these metrics even when the service is running in the cloud</mark>.

<mark style="background: #D2B3FFA6;">Prisma SD-WAN has shifted the focus of the SD-WAN to make it <strong>application-centric</strong></mark>. <mark style="background: #FFB8EBA6;">Prisma SD-WAN builds an application fabric that encompasses the entire network and its configuration, provisioning, management, and monitoring</mark>. 
<mark style="background: #FF5582A6;"><strong>Prisma SD-WAN ION devices</strong> communicate with the <strong>controller</strong> over a <strong>bidirectionally authenticated Secure Sockets Layer (SSL) connection</strong></mark>. 
<mark style="background: #FFB86CA6;"><strong>The Prisma SD-WAN branch IONs</strong> automatically establish secure <strong>virtual private network (VPN) connections</strong> with the <strong>Data Center IONs</strong> across the internet</mark>, <mark style="background: #FFF3A3A6;">and across Private WAN links utilizing the same carrier</mark>. By default, a hub-and-spoke design is used.

All policy rules (network connectivity, application definitions, etc.), network topology (what devices are allowed to communicate to which other devices), encrypted certificates, and encrypted shared secrets <mark style="background: #BBFABBA6;">are communicated to the endpoints via a secure Transport Layer Security (TLS) 1.2 session</mark>. <mark style="background: #ABF7F7A6;">The devices in turn send</mark> anonymized network and application statistics (e.g., bytes transferred, link capacity, voice MOS score, transaction error rate, transaction time) events, alerts, and alarms back to the controller <mark style="background: #ABF7F7A6;">via the secure TLS connection</mark>. <mark style="background: #ADCCFFA6;">No payload or data is ever decrypted by the endpoints or transmitted to the controller</mark>.
# Prisma SD-WAN ION
<mark style="background: #FFB8EBA6;"><strong>Palo Alto Networks Prisma SD-WAN Instant-On Network (ION)</strong> <strong>devices</strong> are available in both hardware and software form factors to meet the needs of any location and any deployment scenario</mark>. 

<mark style="background: #D2B3FFA6;">All ION devices are built with <strong>FIPS 140-2</strong> as a security baseline</mark>. <mark style="background: #CACFD9A6;">Encryption keys are specific to each customer and device, with high-frequency key rotation</mark> <mark style="background: #FFB8EBA6;">occurring at a network level for large-scale, full-mesh, partial-mesh, or hub-and-spoke VPN networks</mark>. <mark style="background: #FF5582A6;">All IONs have an <strong>AUX (console) port</strong>, which you can connect at a baud rate of <strong>115200</strong> for out-of-band management</mark>.

<mark style="background: #ABF7F7A6;">Prisma SD-WAN virtual form factors can be deployed on ESXi, KVM, Hyper-V, and cloud platforms, such as Amazon Web Services (AWS), Microsoft Azure, and Google Cloud Platform (GCP)</mark>.
##### Licensing 
Depending on where the ION device will be deployed, you must purchase a bandwidth-based subscription or data-center subscription.
- Branch site: For ION devices being deployed at branch sites, the options for bandwidth-based subscriptions range from 25Mbps to 2.5Gbps.
- Data-center site: For ION devices being deployed at data-center sites, there is one data-center subscription option.
##### ION Hardware Models
![[ION Hardware Models.png]]
##### ION Software Models
Prisma SD-WAN ION software models can be deployed on ESXi, KVM, and Hyper-V. Additionally, the 7108V can be deployed on Azure, AWS, and GCP cloud platforms.
![[ION Software Models.png]]
##### Manufacturer Installed Certificate
When an ION device is purchased, and prior to shipping to an end customer, <mark style="background: #FFB8EBA6;">a device-specific <strong>manufacturer installed certificate</strong> (MIC) is installed on the device and registered to the customer</mark>. <mark style="background: #FF5582A6;">The uniqueness of the MIC is based on the serial number of the device</mark>. At this point, the device is both <strong>unclaimed</strong> and <strong>untrusted</strong> with no ability to join a customer network.

Once the device is received at the customer location, installed, and powered ON, the device will reach out to controller over any available connection. 

<mark style="background: #FFB86CA6;">The device and controller will mutually authenticate and establish a TLS 1.2 session using the installed MIC</mark>. 

<mark style="background: #FFF3A3A6;">At this point the ION device is in an effective “quarantine” state in that it has no ability to receive policy information from the controller, communicate to other ION devices on the network, or make any policy decisions</mark>. <mark style="background: #BBFABBA6;">The device will show up in an “unclaimed inventory list” for the customer on the controller</mark>.

At this point, the customer can claim the device via the controller. <mark style="background: #ABF7F7A6;">When claiming the device, the controller will generate a <strong>unique device ID</strong> for the device</mark>, <mark style="background: #ADCCFFA6;">generate a device-specific <strong>customer installed certificate (CIC)</strong></mark>, <mark style="background: #D2B3FFA6;">and register the unique <strong>device ID</strong> and <strong>CIC</strong> in the controller</mark>. 

<mark style="background: #CACFD9A6;">The CIC is then transmitted to the device over the existing TLS 443 connection</mark>. <mark style="background: #FFB8EBA6;">The TLS 1.2 session is then <strong>re-established</strong> between the device and the controller using the newly installed CIC</mark>. At this point, the device is not yet participating in the network.

<mark style="background: #FF5582A6;">In order to participate in the network, policies need to be attached to the device</mark> (via site binding) <mark style="background: #FFB86CA6;">and any relevant device specific configurations need to be configured on the device via the controller portal</mark>. 

<mark style="background: #FFF3A3A6;">Once the device configuration and policy assignment is complete</mark>, <mark style="background: #BBFABBA6;">the device will establish VPN tunnels to other ION devices and can start data forwarding as per the defined policies</mark>.

Once the device claim process is complete, and the device is bound to a site, <mark style="background: #ABF7F7A6;">the device will begin establishing IPSec VPN tunnels to authorized devices</mark>. <mark style="background: #ADCCFFA6;">The controller will send 3 encrypted shared secrets to the respective endpoints</mark>.
Each shared secret has a validity period of one day using a standard wall clock model. 
The ION endpoints will then exchange [[security glossary#nonces|nonces]] over an encrypted control channel and <mark style="background: #D2B3FFA6;">derive unique tunnel-specific session keys as per the diagram</mark>.
The session keys are re-negotiated every hour by the VPN endpoints. 
This re-negotiation does NOT require active participation by the controller, enabling both extremely high VPN re-key scale and the ability to re-key tunnels in the event that one or more endpoints loses connectivity to the controller. 
In the case that connectivity to controller is lost, Prisma SD-WAN devices can continue to secure VPNs with hourly key rotation, for a period of three days (by default), using the pre-populated shared secrets from the controller. 
Beyond that, the Prisma SD-WAN VPNs will be torn down and if allowed by policy, traffic forwarding can continue on Standard VPNs to third-party endpoints or on underlay paths.
# Prisma SD-WAN Deployment
The Prisma SD-WAN non-disruptive insertion model enables customers to easily transition existing sites to the Prisma SD-WAN. 

The Prisma SD-WAN approach is referred to as the “Crawl, Walk, Run” model: the approach enables customers to deploy Prisma SD-WAN as aggressively as they want to meet their requirements.
## Analytics Mode
In the first insertion mode (or phase), <mark style="background: #FFB8EBA6;">the Prisma SD-WAN ION hardware appliance is deployed inline at the branch between the Layer 2 or Layer 3 switch and the existing router</mark>. 

In this mode, <mark style="background: #FF5582A6;">Prisma SD-WAN simply collects rich, detailed network and application analytics data. No VPN tunnels are created and Prisma SD-WAN does not select any paths</mark>.

Most deployments initially utilize this mode for a few days to allow Prisma SD-WAN to better understand the applications running on the network and their performance characteristics. The data collected during this period can then be used to design application policies.
## Control
After a customer uses analytics-only mode, they can easily switch the device to <strong>control mode</strong>. 

In this mode, <mark style="background: #FFB86CA6;">Prisma SD-WAN utilizes all the application and network data it has collected to take action in selecting a driven path</mark>. Here, the full functionality of Prisma SD-WAN is delivered without requiring the replacement of the pre-existing router.

Many customers prefer to start their SD-WAN deployment in this mode, because they either own their existing routers and still have years left of depreciation on them or they have carrier-managed routers as part of their existing telecommunications contract.

An added benefit of control mode is that <mark style="background: #FFF3A3A6;">the <strong>Prisma SD-WAN ION device</strong> has integrated fail-to-wire interfaces, which enable an added level of high availability. If either the ION device or the router fails, the surviving device can take over without disrupting connectivity</mark>.
## Router Replacement 
Prisma SD-WAN can run in full-router-replacement mode, which eliminates the need for a router. 

Existing MPLS and internet connections can be directed into the Prisma SD-WAN ION device. Additionally, Prisma SD-WAN has a built-in application zone-based firewall, which enables the consolidation of branch firewall appliances onto the ION device.
# Prisma SD-WAN Site
Sites include brach offices and data centers. 

<mark style="background: #FFB8EBA6;">Prisma SD-WAN uses <strong>site prefixes</strong> to advertise <strong>reachability</strong> from branch sites <strong>into</strong> the SD-WAN fabric</mark>. <mark style="background: #FFB86CA6;">Site prefixes allow Prisma SD-WAN <strong>data center sites</strong> to easily advertise <strong>routes</strong> and <strong>reachability</strong> to branch sites</mark>. You can configure site prefixes for branch sites, but <mark style="background: #FFF3A3A6;">the preferred method for advertising branch reachability is through the use of global scope interfaces and static routes</mark>. From release 6.2.1, both IPv4 and IPv6 prefixes are supported. From release 6.5.1, prefixes learned from global BGP/OSPF peers by the DC ION can be exported into the SD-WAN fabric.
## Data Center Site
A data center (Hub/Transit) is where the enterprise applications and services are hosted.

<mark style="background: #BBFABBA6;">A typical <strong>Prisma SD-WAN data center site</strong> has at least two transports</mark>, but unlike a branch <mark style="background: #BBFABBA6;">the device is placed off-path</mark>, <mark style="background: #ABF7F7A6;">meaning the transports <strong>terminate</strong> on a <strong>data center core router</strong> or <strong>WAN edge router</strong></mark>. 
<mark style="background: #ADCCFFA6;">The <strong>Prisma SD-WAN data center ION device</strong> is typically a <strong>BGP peer</strong> to the <strong>data center core router</strong></mark> <mark style="background: #D2B3FFA6;">to <strong>receive</strong> and <strong>advertise</strong> routes for application reachability to and from branch sites</mark>. 

<mark style="background: #FFB8EBA6;"><strong>Branch sites</strong> automatically establish <strong>zero-touch Secure Fabric Links (Prisma SD-WAN virtual private network (VPN))</strong> to all <strong>DC sites</strong> (a hub-and-spoke design)</mark>. 

Below is the list of functions that a data center site performs.
- <mark style="background: #FF5582A6;">Terminates VPN connections from branch sites</mark>
- <mark style="background: #FFB86CA6;">Aggregation for discontiguous networks</mark> (regional MPLS)
- LQM Server for measuring application service-level agreement (SLA) assurance
- Non Disruptive Insertion with Off-path deployment
- Horizontally scalable
- <mark style="background: #FFF3A3A6;">Supports BGP and OSPF to peer with DC infrastructure</mark>
- Preserves Flow symmetry
## Branch Site
<mark style="background: #FFB8EBA6;">A typical Prisma SD-WAN branch site has at least two transports</mark>, <mark style="background: #FF5582A6;">both of which terminate on the ION device</mark>, assuming an [[networking glossary#ethernet handoff|ethernet handoff]] from the provider. 

<mark style="background: #FFB86CA6;"><strong>The Prisma SD-WAN branch ION device</strong> is typically the <strong>gateway</strong> for the branch</mark> and <mark style="background: #FFF3A3A6;">can be connected to an L2 or L3 switch for local access network (LAN) connectivity</mark>. <mark style="background: #BBFABBA6;"><strong>Branch sites</strong> automatically establish zero-touch Secure Fabric Links (Prisma SD-WAN virtual private network (VPN)) to all <strong>DC sites</strong> (a hub-and-spoke design) and to all <strong>Branch Gateway sites</strong> in the same Domain</mark>. Full or partial static mesh topologies are also supported (not dynamic mesh). 

Below is the list of functions that a branch site performs.
- <mark style="background: #ABF7F7A6;">Distributed application analytics</mark>
- <mark style="background: #ADCCFFA6;">Path selection</mark>
- <mark style="background: #D2B3FFA6;">Measurement of link quality</mark>
- <mark style="background: #FFB8EBA6;">Application service-level agreement (SLA) assurance</mark>
- <mark style="background: #FF5582A6;">Firewall enforcement and compliance</mark>
- <mark style="background: #FFB86CA6;">Standard VPN service insertion</mark>
- <mark style="background: #FFF3A3A6;">Analysis of traffic patterns</mark> from branch to data center, branch to branch, data center to branch, and branch to third-party service
- <mark style="background: #BBFABBA6;">Automatic establishment of zero-touch secure fabric links</mark> (Prisma SD-WAN VPN) <mark style="background: #BBFABBA6;">to all data-center sites</mark> (a hub-and-spoke design) <mark style="background: #BBFABBA6;">and all Branch Gateways in the same Domain as the Branch</mark>
- Support for full-mesh and partial-mesh topologies

<mark style="background: #ABF7F7A6;">The Prisma SD-WAN solution provides complete separation of the control and data planes</mark>. <mark style="background: #ADCCFFA6;">In the event that the branch site loses connectivity with the controller, the branch site is capable of executing the following functions independently</mark>:
- VPN key rotation
- Path selection
- Application service-level agreement (SLA) enforcement
- Application reachability detection
- App path brownout detection
- Buffering of statistics
- Alarm generation via SNMP traps
- Syslog export
## Branch Gateway Site
<mark style="background: #FFB8EBA6;">A <strong>branch gateway site</strong> is a hybrid site capable of hosting both <strong>users</strong> and <strong>applications</strong> while supporting <strong>VPN termination</strong> from other branch sites</mark>. 

<mark style="background: #FF5582A6;">A typical Prisma SD-WAN branch gateway looks like a standard branch site</mark>. <mark style="background: #FFB86CA6;"><strong>Branch sites</strong> automatically establish zero-touch Secure Fabric Links (Prisma SD-WAN virtual private network (VPN)) to <strong>branch gateway sites</strong> in the same domain</mark>, <mark style="background: #FFF3A3A6;">and the <strong>branch gateway site</strong> establish zero-touch Secure Fabric Links to to all <strong>DC sites</strong> enabling geographical/regional based deployments</mark>. 

<mark style="background: #BBFABBA6;">While standard branch sites only connect to hubs</mark>, <mark style="background: #ABF7F7A6;">branch gateway site act as <strong>regional hubs</strong></mark>, <mark style="background: #ADCCFFA6;">supporting automatic VPN meshes with other branches in their domain, superior throughput, and internet transit</mark>.

Below is the list of functions that a branch gateway site performs.
- <mark style="background: #BBFABBA6;">Automatic VPN creation to all Branches in the same domain</mark> 
- LQM server to branches and LQM client to data center
- Support for DIA access at the site
- <mark style="background: #ABF7F7A6;">Distributed application analytics</mark>
- <mark style="background: #ADCCFFA6;">Path selection</mark>
- <mark style="background: #D2B3FFA6;">Measurement of link quality</mark>
- Application service-level agreement (SLA) assurance
- <mark style="background: #CACFD9A6;">Firewall enforcement and compliance</mark>
- <mark style="background: #FFB8EBA6;">Standard VPN service insertion</mark>
- <mark style="background: #FF5582A6;">Analysis of traffic patterns</mark> from branch to data center, branch to branch, data center to branch, and branch to third-party service
- <mark style="background: #FFB86CA6;">Automatic establishment of zero-touch secure fabric links</mark> (Prisma SD-WAN VPN) to all branches (in the same domain) and all data-center sites (a hub-and-spoke design)
- Support for full-mesh and partial-mesh topologies
- Branch Gateway to Branch Gateway tunnels can be established for data center interconnect (DCI) purposes via an admin action in the UI
# Circuit
<strong>Circuits</strong> consist of <strong>circuit categories</strong> which are used in policy rules to identify paths allowed for an application. 

By default, there are a few pre-defined circuit categories in the system that you can use when configuring circuits.
## Circuit Category
<mark style="background: #FFB8EBA6;">Circuit categories are a logical grouping of various kinds of circuits and connectivity that may be present in the network</mark>. 

<mark style="background: #FF5582A6;">This grouping allows for simplified and reusable network policy rules for the entire network</mark>. 

Internet cable <strong>broadband</strong>, metered internet <strong>LTE</strong> links, <strong>satellite</strong> internet links, internet <strong>DSL</strong>, and private <strong>MPLS</strong> are examples of circuit groupings.

<mark style="background: #FFB86CA6;">By default, there are a few pre-defined circuit categories in the system that you can use when configuring circuits</mark>. A total of 64 circuit categories are available. A maximum of 32 public circuits and 32 private circuits are allowed for each category.

<mark style="background: #FFF3A3A6;">Each <strong>circuit category</strong> has a unique <strong>circuit Label</strong></mark>. <mark style="background: #BBFABBA6;">The <strong>Label</strong> is used by path policies as a unique identifier</mark>. <mark style="background: #ABF7F7A6;">During the initial site setup, you must define <strong>circuits</strong> and <strong>circuit categories</strong>, but you can edit or change them at any time</mark>. <mark style="background: #ADCCFFA6;">Circuit category settings determine how the circuit will be used</mark>. 
### Circuit Category #configuration 
#### Use For Controller Connections
![[Use For Controller Connections.png]]
<mark style="background: #FFB8EBA6;">This is a <strong>tenant-wide</strong> setting for the <strong>circuit</strong> to be used for <strong>controller connections</strong></mark>.

<mark style="background: #FF5582A6;">Expensive <strong>circuits</strong> can be <strong>excluded</strong> to meet business intent</mark>. <mark style="background: #FFB86CA6;">Deselect this check box to <strong>exclude</strong> this circuit category from connecting to the controller for <strong>device related services</strong></mark>. For example, you can deselect for metered LTE circuits, which are more costly.

<mark style="background: #FFF3A3A6;">If a circuit is excluded for controller connectivity, then in the absence of any viable link, the excluded circuit can be used for minimum controller connectivity</mark> - <strong>Message Routing Layer</strong> (MRL) and <strong>Remote Access</strong>. <mark style="background: #BBFABBA6;">Statistics and logs will be written to the disk and not exported to the controller</mark>.
<mark style="background: #ABF7F7A6;">Once an allowed circuit comes up, statistics and logs will be exported to controller</mark>.
#### Application Reachability Probes and QoS
![[Application Reachability Probes and QoS.png]]
- **Use For Application Reachability Probes:** This allows the circuit category to check the reachability of an application on a given path.
- **QoS:** Select QoS to enable shaping and queuing of traffic as defined in your application policy rules.
#### Link Quality Monitoring (LQM)
![[Link Quality Monitoring (LQM).png]]
<mark style="background: #ADCCFFA6;">Select <strong>LQ Monitoring</strong> to enable link quality measurements such as <strong>latency</strong>, <strong>loss</strong>, and <strong>jitter</strong></mark>.

You can optionally check the box to use LQM for all paths.

LQM is enabled by default on branch to data center paths.
#### VPN Keep-Alive
![[VPN Keep-Alive.png]]
  
<mark style="background: #FFB8EBA6;">The <strong>Keep-Alive Failure Count</strong> indicates the number of consecutive missed keep-alive packets before a link is declared as <strong>down</strong></mark>. The default value is 3.

<mark style="background: #FF5582A6;">The <strong>Keep-Alive Interval</strong> indicates the time interval in milliseconds between two VPN Keep-Alive packets</mark>. The default value is 1000 ms.
#### L3 Reachability
![[L3 Reachability.png]]
<mark style="background: #FFB86CA6;">Prisma SD-WAN supports <strong>always-on probing</strong>, enabling measurement of key metrics such as round trip latency, packet loss, jitter and other metrics to any ICMP/DNS/HTTP/HTTPS service across all transports (Direct, Fabric, Standard VPN)</mark>. 

<mark style="background: #FFF3A3A6;">The system can utilize application health probes to determine L3 Reachability. These probes determine whether a circuit is available and usable</mark>.

<strong>Probe Profiles</strong>, which are global objects containing <strong>probe configurations</strong>, are defined at the tenant level and linked to Circuit Categories and Circuits.
Probe Profiles consist of one or more Probe Configs. 
<strong>Probe Configs</strong> specify parameters such as Protocol Type (ICMP, DNS, HTTP, HTTPS), EndPoints (IP/FQDN/URL), Frequency, Probe Cycle Duration, and Path Type (Direct, Standard VPNs, Prisma SD-WAN VPNs). 
##### Configure Probes #documentation #configuration 
![[Configure Probes.pdf]]
## Circuit Information 
The Circuit Information page provides a site-level configuration that can be used for more granular control. This takes precedence over the circuit category setting.
### Circuit Information #configuration 
#### Controller Connections
![[Circuit Information.png]]
- <strong>Use Circuit Category Setting</strong>: The circuit inherits the setting from the globally defined circuit category. This is the default.
- <strong>Yes</strong>: The circuit is eligible for all controller communications.
- <strong>No</strong>: The circuit will only be used for device configuration communication if no other methods are available.
#### Name
![[Circuit Information Name.png]]
When configuring the site-level circuit details, it is recommended that you provide a meaningful circuit name, which will help troubleshoot path-related flow details.
Use abbreviations that include Site Name, Circuit Type, and Circuit Provider.
#### Tags
![[Circuit Information Tags.png]]Users can add comments to configure a device, such as a site description, port labeling, and tags. 
The tags and descriptions help identify what the port is used for, and <mark style="background: #FFF3A3A6;">tags can also be used for automation purposes</mark>.
#### BFB Mode
![[Circuit Information BFD Mode.png]]
Aggressive mode is the default mode and is recommended by Prisma SD-WAN for fast failure detection of links.
#### Speed
![[Circuit Information Speed.png]]
<mark style="background: #FFB8EBA6;">Circuit speed hardcoding is required for proper QoS operations on the ION</mark>. 

The WAN circuit speeds must be matched with carrier-provided specifications and specifically configured. <mark style="background: #FF5582A6;">The default values should not be trusted</mark>.

<mark style="background: #FFB86CA6;">It is recommended to use a slightly lower value (1-2 %) for the download and upload bandwidth on the circuit, from the values given by the provider</mark>. 

<mark style="background: #FFF3A3A6;">This is to ensure that the ION QoS kicks in slightly before the circuit limit is reached, to ensure prioritization of the critical applications</mark>. For example, <mark style="background: #BBFABBA6;">if the circuit is rated for <strong>100Mbps</strong> down and <strong>50Mbps</strong> up</mark>, <mark style="background: #ABF7F7A6;">you can configure the circuit settings for <strong>99Mbps</strong> down, <strong>49Mbps</strong> up</mark>. This ensures that the ION QoS starts kicking in at 99Mbps down, and 49Mbps up, and starts prioritizing applications according to the configured QoS policies.
#### Minimize Cellular Usage
![[Minimize Cellular Usage.png]]
<mark style="background: #FFB8EBA6;">Minimize the data usage of <strong>metered 5G/LTE backup links</strong> when other active paths are unavailable</mark>. With this best practice, <mark style="background: #FF5582A6;">you send data over metered links</mark> <mark style="background: #FFB86CA6;">for business continuity only when the primary connection is unavailable</mark>, ensuring flexibility and agility at a lower cost.

<mark style="background: #FFF3A3A6;">Extending the <strong>VPN keep-alive timer</strong> will reduce the amount of data used on this cellular carrier</mark>, but by <mark style="background: #BBFABBA6;">extending this timer it can reduce the failover time if the ION moves from using one DC ION to another DC ION in the DC cluster</mark>.
#### Internet Circuits
![[Internet Circuits.png]]
<mark style="background: #FFB8EBA6;">When creating a circuit, you must select a circuit category and a <strong>WAN (carrier)</strong></mark>. <mark style="background: #FF5582A6;">You cannot use the same <strong>category</strong> twice at a site</mark>.

For example, you cannot designate two Internet Cable circuits at a site even if they are from different carriers. 
<mark style="background: #FFB86CA6;">This is because the circuit category defines the Circuit Label and is used in path policy</mark>. <mark style="background: #FFF3A3A6;">Having two circuits at a site with Ethernet Internet as the circuit category would not allow you to differentiate between those circuits in a path policy</mark>. 

There are 30 Internet categories and 30 public categories, including about 20 named public or private. 
These names can be changed,  so often, two or more circuit categories may be modified to a naming convention, such as ACME-INTERNET-1 and ACME-INTERNET-2.
#### Private WAN Circuits
![[Private WAN Circuits.png]]
<mark style="background: #BBFABBA6;">If a path policy requires the use of the overlay over a private path (e.g., MPLS)</mark>, <strong>make sure</strong> <mark style="background: #ABF7F7A6;">the WAN network matches at the branch site and data center</mark>. 

<mark style="background: #ADCCFFA6;">On the data center side, there could be multiple MPLS circuits from different carriers</mark>. 

<mark style="background: #D2B3FFA6;">Each carrier will have its own WAN network assigned</mark>. <mark style="background: #CACFD9A6;">So, to make sure connectivity comes over the correct carrier circuit, the WAN network needs to match</mark>. <mark style="background: #FFB8EBA6;">Otherwise, the VPN tunnels won’t come up</mark>.
# Prisma SD-WAN Interfaces 
There are two categories of interfaces in Prisma SD-WAN: <strong>ports</strong> and <strong>logical interfaces</strong>.

<strong>Ports</strong> <mark style="background: #FFB8EBA6;">are the <strong>physical interfaces</strong> on an ION device</mark>. <mark style="background: #FF5582A6;">All ION ports are ethernet and cellular</mark>: <strong>Internet ports</strong>, <strong>WAN ports</strong>, <strong>LAN ports</strong>, <strong>Controller ports</strong>, and <strong>Cellular ports</strong>.

<mark style="background: #FFB86CA6;">Logical interfaces are simply referred to as "interfaces" on an ION device</mark>: <strong>Loopback interface</strong>, <strong>Bypass pair</strong>, <strong>Sub-interface</strong>, <strong>Standard VPN</strong>, <strong>Virtual Interface</strong>, <strong>PPPoE Interface</strong>, and <strong>L3 LAN Interface</strong>.
## Port
![[Interface type port.png]]
<mark style="background: #BBFABBA6;">A Port interface type is like an IP interface on a traditional L3 device</mark>.

<mark style="background: #ABF7F7A6;">An interface type of <strong>Port</strong> can be used for <strong>Internet</strong>, <strong>Private WAN</strong>, <strong>LAN</strong>, and <strong>Virtual interfaces</strong></mark>.
### LAN PORTS
The ION 3200 and 1200-S series provide integrated L2 switch ports.
![[Interface type Layer 2.png]]
<strong>L2 LAN switch ports</strong> allow <mark style="background: #BBFABBA6;">per port configuration of <strong>access</strong> or <strong>trunk</strong> ports</mark> and <mark style="background: #ABF7F7A6;">Virtual LAN (<strong>VLAN</strong>)/Switch Virtual Interface (<strong>SVI</strong>) configuration</mark>. 
These ports are supported on ION 3200, ION 1200-S, ION 1200-S-C-NA/ROW, and ION 1200-S-C5G-WW on ports 5 -10.
L2 Switch ports require a minimum ION device version of 6.0.2 for the ION 1200-S series and 6.3.1 for the ION 3200. 
### AUX
<mark style="background: #FFB8EBA6;">The AUX port is used for out-of-band management</mark>. 

<mark style="background: #FF5582A6;">It is a <strong>serial port</strong>, allowing use of a one-time password for emergency access</mark>. <mark style="background: #FFB86CA6;">You can access interface information and configuration</mark>. <mark style="background: #FFF3A3A6;">The idea is to get a device online again, communicating with the controller</mark>. For example, the IP address could be changed from static to DHCP to get the device back online.

The dedicated (fixed) integrated port can be used for:
- Serial console access to the device (Device Toolkit). Baud rate is 115200.
- Emergency offline access using a one-time password
- Performing local diagnostics
- Configuration scope intentionally limited to Interface/IP configuration
### CELLURAR
Certain ION 1200-series models have 4G LTE and 5G connectivity that support cellular connectivity.

<mark style="background: #FFF3A3A6;">The cellular ION devices have integrated 4G or 5G cellular modem for primary or backup WAN connectivity</mark>. If there is no 4G or 5G coverage, these modems can fall back to a 3G network. <mark style="background: #BBFABBA6;">They are optionally installed with dual SIMs to provide backup connectivity when the primary SIM carrier connection is down</mark>. 

You configure the cellular feature on ION devices by setting <strong>Subscriber Identity Module (SIM)</strong> specific configuration like the primary SIM slot, SIM PIN configuration, and cellular IP interface specific configuration. 

Separate primary and backup interface configurations are supported to allow configuring different APNs and circuit labels for different SIMs.

Upgrade to the recommended Cellular model firmware.

<mark style="background: #ABF7F7A6;">On the Cellular interface (<strong>cwan</strong>), the Firmware page displays the current list of firmware versions available for the modem and the current recommended firmware and version</mark>. Upgrade the firmware when the recommended version is different from the current version for your specific carrier. The ION device downloads the new firmware from the controller inventory and then upgrades the carrier firmware on the modem.
### Controller Port
Current ION devices do not have dedicated controller ports as earlier models did. 

<mark style="background: #FFB8EBA6;"><strong>Controller connectivity</strong> is automatically established by using any <strong>L3 port</strong> starting with <strong>port 1</strong></mark>. <mark style="background: #FF5582A6;">One main use of this port is for <strong>dynamic probe generation</strong>, for <strong>application reachability detection</strong></mark>. When an application-unreachable event occurs as a result of an initialization failure or a transaction failure, the ION device marks the path as unavailable for that application and prefix.
The ION device then directs flows to the unavailable application and prefix to use an alternate path that is specified by a policy. The ION must determine when the original path can be used again. Therefore, <mark style="background: #FFB86CA6;">the ION device generates dynamic probes sourced from the controller port</mark>.

Other uses for the controller port: 
- <mark style="background: #FFF3A3A6;">Controller communication</mark>
- <mark style="background: #BBFABBA6;">Administration traffic</mark>:
	- SSH
	- SNMP Agent 
	- SNMP Trap Source
	- NTP Source
- <mark style="background: #ABF7F7A6;">ION HA control interface</mark> (where applicable)
- Also used in legacy Private L2 deployments for traffic from LQM, PCM and, BFD (such as deployments in which there are no L3 direct private forwarding interfaces). This mode is not generally implemented in favor of L3 deployments.
### Sub-Interfaces 
<mark style="background: #ADCCFFA6;">Sub-interfaces are used to <strong>divide</strong> one <strong>physical</strong> or <strong>virtual</strong> <strong>parent interface</strong> into multiple virtual interfaces, thereby implementing VLANs</mark>.

![[Interface type Sub-Interface.png]]
<mark style="background: #D2B3FFA6;">The parent interface can be an Ethernet port, a virtual port, or a bypass pair that does not contain any configuration</mark>. 
<mark style="background: #CACFD9A6;">You cannot configure a sub-interface on the controller port or any interfaces or bypass pairs already configured with loopback as a member with PPPoE or standard VPNs</mark>.

<mark style="background: #FFB8EBA6;">Multiple sub-interfaces may be configured on a physical or virtual interface or bypass pairs</mark>. <mark style="background: #FFB86CA6;">If multiple interfaces are configured</mark>, <mark style="background: #FFF3A3A6;">a VLAN ID is required to create and uniquely identify each sub-interface</mark>.
### Internet
<mark style="background: #D2B3FFA6;">The Internet port is used as an interface to an <strong>untrusted boundary</strong></mark>.

<mark style="background: #CACFD9A6;">When a port is designated as an Internet port, firewall rules are automatically installed that allow only <strong>UDP port 500/4500</strong> and <strong>ESP/IP Protocol 50</strong></mark>. <mark style="background: #FFB8EBA6;">There is no configuration required from end user to block inbound traffic on the Internet port</mark>. <mark style="background: #FF5582A6;">An Internet port can be configured to allow additional inbound services</mark>. 

<mark style="background: #FFB86CA6;">By default, an Internet port is an automatic network address translation (NAT) boundary for application traffic</mark> <mark style="background: #FFF3A3A6;">that is permitted by policy to go direct on the internet</mark>. 

<mark style="background: #BBFABBA6;">NAT can be configured for advanced capabilities, including NoNAT, source network address translation (SNAT), and destination network address translation (DNAT)</mark>. 
- <mark style="background: #ABF7F7A6;">Prisma SD-WAN VPN tunnels over the internet come up automatically between the branch and the data center</mark>.
- <mark style="background: #ADCCFFA6;">The Internet port can be used to establish Border Gateway Protocol (BGP) adjacency with the service provider</mark>.
- <mark style="background: #D2B3FFA6;">A sub-interface (NATIVE or with VLAN tag), a Point-to-Point Protocol over Ethernet (PPPoE) interface, or a virtual Interface can also be used as an Internet port</mark>.
- <mark style="background: #CACFD9A6;">A port or a bypass pair can be assigned as an Internet port</mark>.
## Interface
### Bypass Pair
![[Interface type Bypass Pair.png]]
<mark style="background: #FFB8EBA6;">A bypass pair is a <strong>hardware relay circuit</strong> that is formed by a pair of interfaces for inline fail-to-wire</mark>.

<mark style="background: #FF5582A6;">If a device that physically terminates the WAN connection fails</mark>, <mark style="background: #FFB86CA6;">the <strong>hardware bypass pair</strong> enables the ION <strong>to continue to bridge</strong> traffic even if <u>it's physically powered off</u></mark>. 

<mark style="background: #FFF3A3A6;">As such, the other ION device can continue to forward traffic over that WAN circuit through the failed ION</mark>. 

Additionally, when the site is in Analytics mode or in Control mode, <mark style="background: #BBFABBA6;">a <strong>bypass pair port</strong> type allow for the transparent insertion of an ION device between Layer 2 and Layer 3 devices at the branch</mark>. Thereby, making proof of concepts and migrations minimally disruptive, requiring little to know configuration changes in the surrounding branch infrastructure.
### Standard VPN
<mark style="background: #BBFABBA6;">Prisma SD-WAN seamlessly integrates <strong>third-party security solutions</strong> by using <strong>CloudBlades</strong> to establish <strong>VPNs</strong> to these endpoints in a fully automated fashion</mark>.

<mark style="background: #ADCCFFA6;">Prisma SD-WAN enables you to have multiple <strong>active/active VPN paths</strong> to <strong>third-party security endpoints</strong></mark>. <mark style="background: #D2B3FFA6;">These <strong>VPN paths</strong> can be used in the path selection algorithm along with overlay and underlay paths</mark>. <mark style="background: #CACFD9A6;">Standard VPNs can be manually configured and brought up between a Prisma SD-WAN branch ION and a third-party device</mark>. 
You can also automate these tunnel setups by using CloudBlades, or, in the case of Prisma Access, by using native SASE integration. 

Standard VPN interfaces are used to communicate with systems that require traditional IKE and ESP secure tunnel negotiation.

Commonly deployed standard VPN endpoints are:
- Palo Alto Networks Prisma Access
- Zscaler Internet Access
- AWS
- Azure
- Google Cloud Platform
#### Standard VPN #configuration 
![[Interface typeStandard VPN configuration.png]]
![[Interface typeStandard VPN configuration2.png]]
The following are configuration parameters for standard VPNs:
- Name and Description
- <strong>Parent Interface</strong>: All standard VPN tunnels must be attached to a parent Interface (internet or private WAN).
- <strong>Scope</strong> (Local or Global): Determines whether the inner tunnel IP address is advertised through the fabric via routing protocols
- <strong>Endpoint</strong>: Used in application policy for path selection and can contain a list of IP addresses and hostnames
- <strong>Peer Hostname</strong>: Used to determine the IPSec tunnel remote system IP address
- <strong>Peer IP</strong>: Used to determine the IPSec tunnel remote system IP address when no DNS name is available
- <strong>IPSec Profile</strong>: Used for Basic IKE and ESP parameters
- <strong>IPSec Authentication Override</strong>: Used for locally significant override of IPSec Profile AUTH information (to keep the number of required IPSec profiles to a minimum)
- <strong>NAT Configuration</strong>: NAT Zone, NAT Pools
- <strong>Advanced Options</strong>: MTU
### Prisma SD-WAN VPN
<mark style="background: #FF5582A6;">Prisma SD-WAN VPNs are the secure fabric links between <strong>Prisma SD-WAN ION devices</strong></mark>.

Prisma SD-WAN VPNs are automatically created between a branch and data center ION device.

By default, Prisma SD-WAN VPNs use a hub and spoke design. From the web interface or using the SDK/API, you can create a full or partial mesh.

VPNs are secured by session keys that are rotated hourly.

The controller pre-loads multiple keying parameters to the ION devices.

In the unlikely event that the ION device loses connectivity with the controller, the ION device still maintains the Prisma SD-WAN secure fabric VPNs and rotates the unique session keys for each VPN every hour for up to 72 hours.
### Loopback 
Loopback Interfaces are not the traditional loopbacks that are used in customer networks.

<mark style="background: #FFB8EBA6;">The loopback interfaces in a Prisma SD-WAN ION device</mark> <mark style="background: #FF5582A6;">combine the ports on a physical ION 2000 to form a <strong>bypass pair</strong></mark>. 
<mark style="background: #FFB86CA6;">The primary use case for this interface is to conserve ports in an ION 2000 for <strong>private L2 interface use</strong></mark>.
![[Interface type loopback.png]]
### Private WAN
The private WAN interface is used for the following purposes:
- <mark style="background: #FFB8EBA6;">Communication with MPLS or across a point-to-point link</mark>
- Establishment of BGP adjacency with a provider
- <mark style="background: #FF5582A6;">Formation of zero-touch VPN tunnels to ION devices with the same WAN label defined on an interface</mark>
- <mark style="background: #FFB86CA6;">Forwarding of traffic directly to the <strong>Private WAN link un-encapsulated</strong> or via <strong>VPN</strong></mark>
- <mark style="background: #FFF3A3A6;">Support as a sub-interface with native or with a VLAN tag</mark>
- <mark style="background: #BBFABBA6;">Assignment to a port or a bypass pair</mark>
### LAN
A LAN interface can be used for the following purposes:
- <mark style="background: #FFB8EBA6;">As an interface with the LAN (client side)</mark>
- <mark style="background: #FF5582A6;">As a transit network for environments with L3 switches</mark>
- <mark style="background: #FFB86CA6;">As a sub-interface as NATIVE or with a VLAN tag</mark>
- For static and BGP/OSPF LAN routing
- <mark style="background: #FFF3A3A6;"><strong>Assigned to a port or a bypass pair</strong></mark>
- As a Dynamic Host Configuration Protocol (DHCP) relay or listener for a local DHCP server
- For network context definition to denote the originating network for traffic and in path-selection policies to configure different paths and priorities for traffic coming from different networks: 
    - For example, Gmail traffic from corporate Wi-Fi and guest Wi-Fi can have different policies and different network contexts.
### High Availability (HA)
<mark style="background: #FFB8EBA6;">The HA interface exchanges heartbeats between the two ION devices in an HA configuration</mark> and <mark style="background: #FF5582A6;">connects the standby device to the controller through the active ION device</mark>. You can use this interface to send management traffic like App Probe, NTP, SNMP, RADIUS, and IPFIX.

<mark style="background: #FFB86CA6;">The HA ports between the IONs should not be directly connected, they should be connected to each other through a LAN switch</mark>.
### Private L2
<mark style="background: #FFF3A3A6;">A Private L2 interface enables the transparent insertion of a Prisma SD-WAN ION device between</mark><mark style="background: #BBFABBA6;"> a Layer 2 switch at the branch</mark> and <mark style="background: #ABF7F7A6;">a Layer 3 device at the WAN edge</mark>. 

<mark style="background: #ADCCFFA6;">Private L2 interface configuration is supported only when the interface type is a bypass pair and not as a sub-interface</mark>.
A Private L2 interface is used:
- In topologies where transparent inline operation is required
- As a bridge interface with ability to intercept traffic
- For sites where router interoperability is required
### Virtual Interface
<mark style="background: #FFB8EBA6;">A virtual interface combines two physical ports into one logical interface</mark>. 

<mark style="background: #FF5582A6;">Virtual interfaces provide increased redundancy in areas of the network where uptime is critical and additional design flexibility is needed</mark>.

A virtual interface can be created, updated, or deleted. A virtual interface will be shown as down only if both the member interfaces are operationally down. If at least one member is operationally up, the virtual interface is shown as up.
![[Virtual Interface.png]]

<mark style="background: #FFB86CA6;">A virtual interface can contain a maximum of two member interfaces</mark>. <mark style="background: #FFF3A3A6;">A virtual interface ensures redundant physical connectivity from a device to one or more switches, routers, or firewalls</mark>. For example, two controller ports can be connected to two L2 switches for physical redundancy of controller port connectivity.
<mark style="background: #BBFABBA6;">The physical port of a virtual interface cannot be a bypass pair or a logical interface</mark>. 
<mark style="background: #ABF7F7A6;">A controller port can only be added to a virtual interface with another controller port</mark>.
<mark style="background: #ADCCFFA6;">The member interface cannot have any type of IP, sub-interface, used-for, circuit label, or PPPoE configuration</mark>.

There are two types of virtual interfaces.
<strong>Virtual Interface With Controller Ports</strong>
<mark style="background: #D2B3FFA6;">The admin state cannot go down for virtual interfaces with controller ports. This type of virtual interface is not cleaned up automatically when the device is unassigned from a site</mark>.
<strong>Virtual Interface With Non-Controller Ports</strong>
This type of virtual interface is supported on all platforms and supports used_for (public | private | LAN) configuration and site WAN interface attachment. 

<mark style="background: #CACFD9A6;">This type of virtual interface can be a parent of a sub-interface and service link. Virtual interfaces used for LAN will be cleaned up automatically when the device is unassigned from a site</mark>.

<mark style="background: #FFB8EBA6;">If the device can only connect to the controller through the controller interfaces</mark>, <mark style="background: #FF5582A6;">a virtual interface with controller ports cannot be created in a single operation</mark>:
- <mark style="background: #FFB86CA6;">Reset the configuration of one of the controller interfaces. Ensure that the element can connect through the other controller interface</mark>.
- <mark style="background: #FFF3A3A6;">Create the virtual interface with one controller interface and configure the IP address</mark>. The element should be able to connect through the virtual interface.
- <mark style="background: #BBFABBA6;">Reset the configuration of the second controller interface and add the second controller to the virtual interface</mark>.
#### Virtual Interface Use Cases
Virtual interfaces can be configured on both branch and data center ION devices.
##### Controller Port Redundancy
In this scenario, <mark style="background: #ABF7F7A6;">the virtual interface provides physical redundancy</mark> <mark style="background: #ADCCFFA6;">from a single Prisma SD-WAN ION device with dual controller ports to two L2 switches</mark> if a port failure occurs between the ION devices and one of the switches. 

<mark style="background: #D2B3FFA6;"><strong>Each controller port of the ION device is physically connected to a separate switch</strong></mark>. <mark style="background: #CACFD9A6;">A new virtual interface is configured with the two member interfaces</mark>, controller ports 1 and 2. 
<mark style="background: #FFB8EBA6;">IP address information is configured on the virtual interface controller port</mark>. If a switch or controller port is lost, controller connectivity remains uninterrupted.
![[Controller Port Redundancy.png]]
##### Two Core Peers In The Same Subnet
In this scenario, <mark style="background: #FF5582A6;">a virtual interface is used to provide redundant physical connections to a pair of Layer 3 core switches</mark>. The ION device is peering via BGP with both switches in the same IP network.
![[Two Core Peers In The Same Subnet.png]]
##### Internet Circuits To Firewall
In this scenario, <mark style="background: #FFB86CA6;">a virtual interface is used to provide redundant physical connections to a pair of Layer 2 switches that are connected to an internet-facing firewall pair</mark>. The ION device uses the firewall for the default gateway for the redundant internet-facing ports.
![[Internet Circuits To Firewall.png]]
# IP Directed Broadcast
The IP Directed Broadcast feature was introduced in 5.4.1 to <mark style="background: #FFB8EBA6;">help with scenarios</mark> (such as WakeOnLAN) <mark style="background: #FFB8EBA6;">where traffic needs to be broadcast to all devices in a LAN subnet</mark>. This IP Directed Broadcast feature can be used in some branch scenarios instead of multicast. 

<mark style="background: #FF5582A6;">The traffic could be arriving on the WAN from another site</mark>, or <mark style="background: #FFB86CA6;">from the LAN from another segment</mark>. 
<mark style="background: #FFF3A3A6;">With the IP Directed Broadcast enabled, traffic sent to the LAN segments broadcast IP address (e.g., 192.168.1.255)</mark> <mark style="background: #BBFABBA6;">will be forwarded to all hosts in that LAN subnet</mark> <mark style="background: #ABF7F7A6;">by using a broadcast destination MAC address</mark>.

<mark style="background: #ADCCFFA6;">LAN-to-LAN directed broadcast at a branch site is supported</mark>. <mark style="background: #D2B3FFA6;">WAN-to-LAN directed broadcast will be supported only if these packets are received on a Prisma SD-WAN-VPN path (from another ION device)</mark>. <mark style="background: #CACFD9A6;">Any response unicast traffic generated by end-hosts will be treated as a new/unique flow that goes through a Zone-Based Policy Firewall (ZBFW), Path, QoS, NAT policy independently</mark>.
## IP Directed Broadcast #configuration 
The IP Directed Broadcast configuration is at an interface-level. 
![[Enable Layer 3 LAN Interfaces.png]]
To use the IP Directed Broadcast feature, the branch ION device needs to have <mark style="background: #FFB8EBA6;">both L3 LAN Forwarding</mark> and <mark style="background: #FFB8EBA6;">L3 WAN Forwarding enabled</mark> in the Device Basic Info tab.

<mark style="background: #FF5582A6;">The IP Directed Broadcast is disabled by default. Select <strong>Yes</strong> to enable it on any L3 LAN interface or sub-interface on the device</mark>.

Once enabled, the IP broadcast traffic will be evaluated by Path, Security, QoS, NAT policies, and reported in the Flow Analytics like any other unicast traffic.
# Prisma SD-WAN Policies
The goal of the <mark style="background: #FFB8EBA6;">app-defined Prisma SD-WAN design</mark> is to provide a level <mark style="background: #FF5582A6;">of <strong>configuration abstraction</strong> that allows for a given <strong>configuration element</strong> to be created once and used at scale across the enterprise</mark>.

Examples of the <strong>abstracted configuration elements</strong> include <strong>multiple policy modules</strong>, <strong>application definitions</strong>, and <strong>prefix filters</strong>. 
<mark style="background: #BBFABBA6;">These modules can be thought of as interchangeable building blocks that can be reused across policy sets throughout an enterprise</mark>.
The following policy modules are abstracted:
- Path Policy 
- Performance Policy
- QoS Policy 
- Security Policy 
- NAT Policy

<mark style="background: #ABF7F7A6;">All policies are <strong>centralized</strong> and maintained within the <strong>Prisma SD-WAN controller</strong> and bound at a site level</mark>. <mark style="background: #ADCCFFA6;">Each branch or branch gateway site will have a default policy stack for <strong>path</strong>, <strong>performance</strong>, <strong>NAT</strong>, and <strong>QoS</strong>, and will be assigned intelligent defaults for each</mark> <mark style="background: #CACFD9A6;">a <strong>security</strong> policy set can be applied</mark>. <mark style="background: #D2B3FFA6;">Data center sites do not require path policies as they are the head end of the SD-WAN</mark>. 

<strong><mark style="background: #FFB8EBA6;">Prisma SD-WAN first and foremost is an application routing system</mark></strong>. <mark style="background: #FF5582A6;">Policy is written based on <strong>applications within the environment</strong></mark> and <mark style="background: #ADCCFFA6;">on <strong>policies</strong> for these applications</mark> and <mark style="background: #ABF7F7A6;">their business relevancy and criticality</mark>. <mark style="background: #FFB86CA6;">Policies and actions for business or non-business applications</mark> <mark style="background: #FFF3A3A6;">then are mapped to the paths these applications are allowed to take</mark>. Prisma SD-WAN supports multiple path types, which can be abstracted into terms such as "Any Public" and "Any Private" to simplify policy.
## Path Policy Rules
Each <strong>path policy set</strong> has one or more <strong>rules</strong> that define <strong>match criteria</strong>, <strong>allowed paths</strong>, and <strong>services</strong>. 

Path Policy rules have several components:
- <strong>Application(s)</strong>: <mark style="background: #FFB8EBA6;">Applications defined for this path policy rule</mark>
- <strong>Paths allowed</strong>: <mark style="background: #FF5582A6;"><strong>Paths that the application(s) are allowed to take</strong> by policy for a given rule</mark>
- <strong>Service</strong> or <strong>DC transit</strong>: Defines whether a <strong>transit point</strong> (data center, as an example) is required or <strong>third-party service</strong>, such as Prisma Access
- <strong>Order</strong>: Priority that a given rule is to have
    - Default is 1024 for a value.
    - Lower values have higher priority.
- <strong>Network context</strong>
- <strong>Source and destination prefix</strong>
### Default Path Policy Set
<strong>Default Rule</strong>:
- By default allow all paths
- Applied to traffic outside of the enterprise network (i.e., non-RFC 1918 or 4193 IP addressing)
<strong>Enterprise-default rule</strong>:
- By default allow all paths except direct on any public
- Applied to traffic destined to any enterprise prefix (i.e., non-RFC 1918 or 4193 IP addressing)
## QoS Policy Rules
Each <strong>QoS policy set</strong> has one or more <strong>rules</strong> that define the <strong>match criteria</strong>, <strong>priority</strong>, and (optionally) <strong>DSCP marking</strong>. QoS Policy rules also have several components:
- <strong>Application(s)</strong>: Applications defined for this Path policy rule
- <strong>QoS Priority</strong>: Priority to give an application from the four tiers
- <strong>Order</strong>: Priority that a given rule is to have
    - Default is 1024 for a value.
    - Lower values have higher priority.
- <strong>Network context</strong>
- <strong>Source and destination prefix</strong>
- <strong>DSCP Markings</strong>: By default Prisma SD-WAN honors and passes any received DSCP values, but can be overridden in policy.
### Default QoS Policy Set
<strong>Default Rule </strong>
- By default priority is Bronze 
- Applied to traffic outside of the enterprise network (i.e., non-RFC 1918 or 4193 IP addressing)

<strong>Enterprise-Default Rule </strong>
- By default priority is Silver
- Applied on traffic destined to an enterprise prefix (i.e., non-RFC 1918 or 4193 IP addressing)
## Stacked Policies
<mark style="background: #BBFABBA6;">Prisma SD-WAN <strong>stacked policies</strong> are ordered from left to right</mark> and may comprise the following policy sets:  <strong>Path, NAT, Performance, Security, and QoS</strong>. There are two policy types for each set, a <strong>default rule policy</strong> and a <strong>policy set</strong>, with the default rule policy acting as a fallback. 

<mark style="background: #ABF7F7A6;">Policy rules may be <strong>explicitly</strong> ordered by a user</mark> or <mark style="background: #ADCCFFA6;">will be subject to <strong>implicit</strong> ordering when no explicit rules exist</mark>.
#### Explicit Ordering
With explicit ordering, <mark style="background: #D2B3FFA6;">the Order Numbers are evaluated for a match</mark>. 

<mark style="background: #CACFD9A6;">The first match in the lowest numerical (highest priority) rule will be used</mark>, <mark style="background: #FFB8EBA6;">regardless of whether a more-specific match can be found further in the rulesets</mark>.
![[Explicit Ordering.png]]
#### Implicit Ordering
With implicit ordering, <mark style="background: #FF5582A6;">the Order Numbers are all the same</mark>. T<mark style="background: #FFB86CA6;">he policy that has the <strong>most specific match</strong> will be used</mark>, <mark style="background: #FFF3A3A6;">if all of the rules in the policy have the same Order (Priority) number</mark>.
![[Implicit Ordering.png]]
### Simple Stacked Policy
<mark style="background: #D2B3FFA6;">A Simple Stack is a collection of <strong>policy rules</strong> in a <strong>single policy set</strong></mark>. <mark style="background: #CACFD9A6;">Organizations can create <strong>customized policy rules</strong>, which then will be merged with the <strong>default policy set</strong></mark>.
At a minimum, a Simple Path or QoS Stack will consist of two policy rules:
- Default rule
- Enterprise default rule
#### Simple Stacked Policy #configuration 
From the <strong>Controller</strong> web interface, a Simple Path Stack can be created manually, or an existing Simple Stack can be cloned and then modified to meet an organization’s requirements.
##### Add Path Stack
Under <strong>Manage > Prisma SD-WAN > Policies > Path</strong>, then select <strong>Path Stacks</strong>. Click <strong>Simple</strong>, then click <strong>Add Stack</strong>.

Path prefixes can be configured and used in path policies. From release 6.2.1, both IPv4 and IPv6 path prefixes are supported.
![[Add Path Stack.png]]

##### Add QoS Stack
Under <strong>Manage > Prisma SD-WAN > Policies > QoS</strong>, then select <strong>QoS Stacks</strong>. Click <strong>Simple</strong>, then click <strong>Add Stack</strong>.

QoS prefixes can be configured and used in QoS policies. From release 6.2.1, both IPv4 and IPv6 QoS prefixes are supported.
![[Add QoS Stack.png]]
##### Define Policy Rule
###### Path Policy Rule
Within a simple Path policy rule, <mark style="background: #ABF7F7A6;">applications and their desired path and policy behaviors are configured as shown</mark>. Prisma SD-WAN supports unified App-IDs to provide application detection services for Prisma SD-WAN and Palo Alto Network applications. Sites must have their ION devices updated to 6.0.1 to take advantage of the new applications. To filter applications based on the ION device version, use the options at the top of the page.
![[Path Policy Rule.png]]
###### QoS Policy Rule
Within a simple QoS policy rule, applications and their desired priority are configured. Optionally, the applications defined have their DSCP values re-marked.
![[QoS Policy Rule.png]]
##### User-ID in Path and QoS Policy Rules
<mark style="background: #ADCCFFA6;">Users and/or groups can be specified in the Users tab's path and QoS policy rules</mark>. <mark style="background: #D2B3FFA6;">The Cloud Identity Engine (CIE) and the user agent must have been previously configured to enable the Users tab, allowing one or more users and/or groups to be specified in policy rules</mark>.
### Advanced Stacked Policy
<mark style="background: #CACFD9A6;"><strong>Advanced Stacked Policy</strong> is a collection of <strong>Path</strong> or <strong>QoS</strong> <strong>policy sets</strong> that are stacked</mark>, <mark style="background: #FFB8EBA6;">stack maximum of <strong>four policy sets</strong> and <strong>one default rule policy set</strong></mark> and they are ordered from left to right, with the left-most as highest priority. 
![[Advanced Stacked Policy.png]]
#### Advanced Stacked Policy #configuration 
Select <strong>Stacked Policies</strong>, <strong>Path</strong> or <strong>QoS</strong>. Depending on which stacked policy you selected, you can select <strong>Path Stacks</strong> or <strong>QoS Stacks</strong> and create a new policy set. Then add a Path or QoS Stack that references the new/modified policy set.

The policies will be evaluated from left to right until a match is found. If no match is found in the defined policy sets 1 through 4, the default rule policy set then will be used.
![[Advanced Stacked Policy config.png]]
## Performance Policy
<mark style="background: #FFB8EBA6;">Measuring application and system health performance and delivering App SLAs is a core component of Prisma SD-WAN</mark>.

<mark style="background: #FF5582A6;">Performance Policy builds upon the existing App SLA configuration to provide a policy framework for measuring, enforcing, and alerting for application SLAs</mark>.
### Performance Policy Stack
The Performance Policy Stacks is a collection of performance sets containing the performance policy rules. <mark style="background: #FFB86CA6;">Performance policy sets specify traffic engineering</mark> and can accommodate a maximum of <strong>four policy sets</strong> and <strong>one default rule policy set</strong> for each policy stack.
![[Performance Policy Stack.png]]
### Performance Policy Set
The Performance Sets tab contains policy rules and are a part of the policy set stacks. <mark style="background: #FFF3A3A6;">A policy set has <strong>default policy rules</strong> which cannot be changed, removed, or deleted</mark>. <mark style="background: #BBFABBA6;">User can create custom policy rules to take precedence over the default policy rules</mark>.
![[Performance Policy Set.png]]
### Performance Policy Rule
<mark style="background: #ABF7F7A6;">Performance Policy rules can be defined with <strong>Link Quality</strong> and <strong>Application metrics</strong> thresholds</mark>. <mark style="background: #ADCCFFA6;">Users can apply the rule at an <strong>application</strong> or <strong>transfer type</strong> level</mark>, select path types, path filters and path category, select Path Filters, Circuit labels, Path types, and Data center groups.
![[Performance Policy Rule.png]]
#### General
 - When creating a rule, <mark style="background: #D2B3FFA6;">the <strong>rule type</strong> specifies if the rule applies to the <strong>Application SLA</strong> or the <strong>System Health</strong></mark>.
 ![[Performance Policy Rule1.png]]
#### Action
- <mark style="background: #CACFD9A6;">The <strong>Create Incident</strong> action generates incidents for Applications and System Health events based on Performance SLA criteria</mark>.
- <mark style="background: #FFB8EBA6;">The <strong>Move Flows</strong> action moves existing flows</mark> and <mark style="background: #FF5582A6;">excludes paths for new flows that violate a performance SLA</mark>. These include both <strong>Link Quality</strong> and <strong>Application Metrics</strong>. <mark style="background: #FFB86CA6;">When the <strong>Move Flows</strong> field is empty in a rule, the datapath won't consider LQM measurements during path selection</mark>. 
- The <strong>Visibility</strong> action affects the <strong>secure fabric link</strong> time series while projecting the performance SLA indicators. The visibility action relies on <strong>Link Quality Metrics</strong>. 
- The <strong>Packet Duplication</strong> and <strong>FEC</strong> (<strong>Forward Error Correction</strong>) actions <mark style="background: #FFF3A3A6;">are mutually exclusive and must be enabled along with the Move Flows action</mark>. <mark style="background: #BBFABBA6;"><strong>FEC</strong> only relies on the loss and latency Link Quality Metrics</mark> and does not use Application metrics. <mark style="background: #ABF7F7A6;">FEC takes effect only on Prisma SD-WAN VPNs</mark>.
![[Performance Policy Rule2.png]]
#### Match Criteria (Application SLA)
- <strong>App Filters</strong> : to select an Application(s) to apply the policy rule. You can select 256 applications for one policy rule. 
- <strong>Application by Transfer Type</strong> : Bulk, Audio, Video, or Transactional. 
- <strong>Path Filters</strong>:
    - Path Category - an overlay and a Circuit Category for a path. 
    - Path Type as Direct, Prisma SD-WAN VPN, or Standard VPN. 
- (Optional) Select the DC Group value from the drop-down. By default, all DC Groups are included.
![[Performance Policy Rule 3.png]]
#### Match Criteria (System Health)
- System Health Metrics: CPU, Memory, or Disk utilization and the thresholds required for generating an incident. 
- Flow Metrics: Concurrent flow utilization. 
- Circuit Utilization: Circuit Utilization.
![[Performance Policy Rule4.png]]
## Policy Use Cases
### Active/Active Path Policy
A common use case for organizations is to have <mark style="background: #FFB8EBA6;">both an <strong>internet path</strong> and <strong>a private WAN</strong> (MPLS) for a given branch</mark> making a Hybrid WAN.
![[Active-Active Path Policy.png]]
<strong>VPN on Any Public</strong>
Any circuit labeled as “To internet” with a Secure Fabric established
<strong>Direct on Any Private</strong>
Any circuit labeled as “Private WAN” (MPLS), send directly on the path
<strong>VPN on Any Private</strong>
Any ”Private WAN” (MPLS) in which both sides are part of the same provider and a Secure Fabric is established
### Active/Backup Path Policy
Organizations tend to configure their policy this way because broadband/internet circuits very likely will have higher bandwidth than legacy MPLS/private WAN paths. With this in mind, Prisma SD-WAN will be implemented using the following logic.

<strong>Active Path</strong>
Under normal conditions with no application brownouts/congestion detected at the Prisma SD-WAN branch, this will be the preferred path.
<strong>Backup Path</strong>
<mark style="background: #FFB8EBA6;">If an application (such as voice) has a <strong>brownout</strong></mark> (e.g., <mark style="background: #FF5582A6;">the application is not sustainable over the active path</mark>), <mark style="background: #FFB86CA6;">the backup path then will be used for the session</mark>. <mark style="background: #FFF3A3A6;">A backup path chosen for an application such as voice does not preclude the next session or application from using the active path</mark> (e.g., FTP and web browsing).

![[Active-Backup Path Policy.png]]
<strong>Active Path VPN on Any Public</strong>
Any circuit labeled as “To internet” with a the Prisma SD-WAN secure environment established.
<strong>Backup Path VPN on Any Private</strong>
Any circuit labeled as “Private WAN” (MPLS), send directly on the path.
### Dual Active/Single Backup Path Policy
In addition to the <mark style="background: #BBFABBA6;">two active paths</mark>, <strong>Prisma SD-WAN VPN on Primary Internet</strong> and <strong>Prisma SD-WAN VPN on Any Private</strong>, the business now has added a backup path to its policy: <strong>Direct on Any Private</strong>. 
"Primary Internet" should be used as the first active path circuit category opposed to "Any Public" as LTE circuits would be included in any public.

The organization prefers to have encrypted traffic where possible, <mark style="background: #ABF7F7A6;">but as a backup path, it will forgo encryption and send directly on the MPLS/private WAN</mark>. <mark style="background: #ADCCFFA6;">Remember that Dynamic Path Selection will evaluate the two active paths for the viability of carrying an application session</mark>. If not, it will utilize the backup path for a new session.

Lastly, <mark style="background: #D2B3FFA6;">the organization wants to have a policy path of last resort. This goal is accomplished through an <strong>L3 failure path</strong> in its policy</mark>. The organization has now added a backup path to its policy: <strong>Prisma SD-WAN VPN on Metered 3G/4G/LTE</strong>.
![[Dual Active-Single Backup Path Policy.png]]
![[Dual Active--Single Backup Path Policy.png]]
### Policy for Trusted SaaS Applications
<mark style="background: #BBFABBA6;">Certain applications such as <strong>SaaS applications</strong> are encrypted</mark> and <mark style="background: #ABF7F7A6;">have their security controls applied through other mechanisms</mark>, if needed. Enterprise organizations can elect <mark style="background: #ADCCFFA6;">to trust theses applications</mark> and <mark style="background: #D2B3FFA6;">send them directly on an internet path</mark> without going through a data center or third-party service:
<strong>Active Policy</strong>
Trusted SaaS applications will use <strong>Direct Internet Access (DIA) links</strong> where no firewall inspection is done at the branch or ISP level.
<strong>Backup Policy</strong>
The backup policy will be used when the application <mark style="background: #CACFD9A6;">needs to fail over the flows</mark> and <mark style="background: #FFB8EBA6;">this policy will transit to enterprise data centers and route to the internet via the data centers</mark>.
#### Policy for Trusted SaaS Applications #configuration 
##### Direct Internet Access
Here we define <mark style="background: #FF5582A6;">the applications that are part of our Trusted SaaS</mark>, and <mark style="background: #FFB86CA6;">our Active Path is defined as Direct on “Any Public”</mark>. This will send<mark style="background: #FFF3A3A6;"> any of the identified Trusted SaaS applications across any public interface labeled as “To Internet”</mark>.
![[Direct Internet Access.png]]
##### General Web Browsing - Back to Data Center
<mark style="background: #BBFABBA6;">With any other applications</mark>,<mark style="background: #ABF7F7A6;"> we want to send them to our data center for policy inspection/enforcement</mark>. In this example, <mark style="background: #ADCCFFA6;">SSL and HTTP are not trusted natively</mark>, <mark style="background: #D2B3FFA6;">so they will be sent via VPN</mark> (Prisma SD-WAN Secure Fabric) <mark style="background: #CACFD9A6;">to the Primary data center and/or Backup data center for inspection</mark>.
![[General Web Browsing - Back to Data Center.png]]
### Policy Control Based on Network Context
Network context such as Guest Traffic can be identified.
For example, the Guest Traffic can be configured to be only allowed to go direct on any public interface.
![[Policy Control Based on Network Context.png]]
# Dynamic Path Selection 
The goal of the Prisma SD-WAN architecture is <mark style="background: #ABF7F7A6;">to intelligently make application path decisions</mark>. 

Prisma SD-WAN uses <strong>Dynamic Path Selection</strong> and uses the following to account for application performance:
- <mark style="background: #ADCCFFA6;">Measure transport performance </mark>
- <mark style="background: #D2B3FFA6;">Address Layer 7 app reachability issues</mark>
- <mark style="background: #CACFD9A6;">Account for Layer 3 reachability and availability</mark>
- Support cloud, media, and enterprise encrypted and custom apps
- Guarantee [[security glossary#flow symmetry|flow symmetry]]
- Be able to support “single ended” direct Internet paths
- <mark style="background: #FFB8EBA6;">Allow third-party service transit</mark> with performance monitoring
- <mark style="background: #FF5582A6;">Allow explicit data center transit</mark>

Before understanding how Dynamic Path Selection works, you must understand the logic of <mark style="background: #D2B3FFA6;"><strong>when a new path selection is made</strong></mark>. <mark style="background: #FFB86CA6;">The <strong>new path</strong> selection criteria used within the system are as follows</mark>:
- <mark style="background: #FFF3A3A6;">When a new flow is created</mark>
- <mark style="background: #BBFABBA6;">When a path flaps</mark> (goes down or up)
- <mark style="background: #ADCCFFA6;">When performance policy SLAs rules apply</mark> 
- <mark style="background: #D2B3FFA6;">When asymmetry occurs in the network</mark> (<mark style="background: #CACFD9A6;">when the <strong>return path</strong> is different from the path chosen by the flow when exiting the branch</mark>)
- <mark style="background: #FFB8EBA6;">Active and backup path selection</mark>

<mark style="background: #FF5582A6;">Before a path can be chosen, it must be evaluated as to whether it can be used to carry the <strong>application(s)</strong></mark>. The evaluation criteria used are as follows:
- Network and Security policy
- Link status (up or down)
- <mark style="background: #FFB86CA6;">Data center transit</mark>
- <mark style="background: #FFF3A3A6;">Path preference</mark>
- <mark style="background: #BBFABBA6;">Link or path performance per app thresholds</mark> (latency, loss, jitter)
- <mark style="background: #ABF7F7A6;">Layer 3 reachability on both the direct and VPN paths</mark>
- <mark style="background: #ADCCFFA6;">Application-specific reachability</mark> (TCP initiation failures and transaction failures)
- <mark style="background: #D2B3FFA6;">Application-specific performance characteristics</mark> (round-trip time, network transit time, transaction failure percentage, initialization failure percentage, and media MOS score)
- <mark style="background: #CACFD9A6;">Path affinity</mark>
- <mark style="background: #FFB8EBA6;">Select a path with the most available bandwidth</mark>
# Service and Data-Center Groups
Service and data-center groups allow for very simple or very granular policies. 

<mark style="background: #FFB8EBA6;">Mapping of third-party services utilizing standard <strong>IPSec/GRE endpoints</strong> for <strong>service integration</strong></mark> and <mark style="background: #FF5582A6;"><strong>Prisma SD-WAN data centers</strong> allows for <strong>geolocation-based service</strong> and <strong>data-center choices</strong></mark>. <mark style="background: #FFB86CA6;">Service and data-center groups are used to map services or data centers as <strong>optional</strong> or <strong>mandatory</strong> <strong>transit points</strong> for traffic</mark>.

For example, <mark style="background: #FFF3A3A6;">if a <strong>branch</strong> has internet-only connectivity</mark> and <mark style="background: #BBFABBA6;">needs to access traffic within a data center or internal resource</mark>, <mark style="background: #ABF7F7A6;">a <strong>data center (DC) group</strong> must be defined and listed as part of the optional transit path for that <strong>branch</strong> or <strong>traffic flow</strong></mark>.

<strong>Service and DC groups</strong> can be used to create <mark style="background: #ADCCFFA6;">geographic groupings for resources</mark> to best suit an organization’s business needs. For example, <mark style="background: #D2B3FFA6;">European traffic would have a primary data center in EMEA</mark> and <mark style="background: #D2B3FFA6;">a backup location in New York</mark>.  

<mark style="background: #CACFD9A6;">These transit locations can be made optional or mandatory. For mandatory transit, traffic must go to that service or DC group for policy inspection</mark>.
![[Service and Data-Center Groups.png]]
##### Service and Data-Center Groups #configuration 
<mark style="background: #FFB8EBA6;">Service and data-center groups are created and mapped by an organization to meet its requirements</mark>. After sites are created, <mark style="background: #FF5582A6;">they then are mapped to their respective domain, service, or data-center groups</mark>. Within the policy, <mark style="background: #FFB86CA6;">the service or data-center group then is configured for the given application or traffic flow</mark>. <mark style="background: #FFF3A3A6;">If the service or data-center group is required to flow through a given instance for inspection, then the <strong>Required</strong> checkbox would be enabled</mark>.

<mark style="background: #BBFABBA6;">Define primary and backup Prisma SD-WAN data-centers groups per domain for simplified policy management</mark>.
![[Service & DC Groups.png]]

<mark style="background: #ABF7F7A6;">Reference the data-center group in policy rules</mark>; <mark style="background: #ADCCFFA6;">the branch site to which the domain is bound will determine the definition of the group</mark>. As an example, <mark style="background: #D2B3FFA6;">all internet-bound web traffic should transit through the primary DC over any transport</mark>, <mark style="background: #CACFD9A6;">and if not available or meeting service-level agreements (SLAs), use the backup DC</mark>.
![[Service & DC Groups 2.png]]

Setting the <strong>Required</strong> check box <mark style="background: #FFB8EBA6;">forces traffic to use the <strong>service</strong> or <strong>DC group</strong> referenced even if a direct path is available</mark>. <mark style="background: #FFB86CA6;">If the box is left unchecked and there is a direct path allowed and available, the system will optionally use the transit path with preference given to the direct path if the SLA is met</mark>.
![[Service & DC Groups 3.png]]
## Standard VPN Service Groups
The process of configuring <strong>standard virtual private network (VPN) service groups</strong> is identical to configuring <strong>data-center groups</strong>. <mark style="background: #FFB8EBA6;">The groups are added and used in the same way as a data-center group</mark>.

Prisma SD-WAN uses mapping of <strong>standard VPN services</strong> and <strong>Prisma SD-WAN data centers</strong> to allow flexibility when policy rules are created, while accounting for uniqueness across sites. <mark style="background: #FF5582A6;"><strong>Service</strong> and <strong>DC group</strong> labels can be used in Path policy rules</mark> <mark style="background: #FFB86CA6;">to express intent to allow or require traffic to transit through a <strong>Prisma SD-WAN data center</strong> or a <strong>cloud security service</strong> such as <strong>Palo Alto Networks Prisma Access</strong> for Networks</mark>.
![[Standard VPN Service Groups.png]]
# Transport Quality Metrics
<mark style="background: #FFB8EBA6;"><strong>Link quality metrics (LQM)</strong> probes are sent periodically between <strong>Instant-On Network (ION) devices</strong></mark> and measure the [[networking glossary#loss|loss]], [[networking glossary#latency|latency]], and [[networking glossary#jitter|jitter]] on that path. <mark style="background: #FF5582A6;">These probes are sent from branch  IONs to hub IONs</mark>. <mark style="background: #FFB86CA6;">The probes are sent on all the overlay <strong>virtual private network (VPN) tunnels</strong> (public and private) and on <strong>the private WAN underlay path</strong></mark>.

<mark style="background: #FFF3A3A6;"><strong>LQM metrics</strong> for each path are measured in both directions</mark>, <mark style="background: #BBFABBA6;">giving you both ingress and egress metrics from the branch perspective</mark>. 

<mark style="background: #ABF7F7A6;">For the <strong>overlay</strong>, the probes are between the <strong>tunnel endpoints</strong>, through the tunnel</mark>. <mark style="background: #ADCCFFA6;">The probes for the <strong>MPLS underlay</strong> are sent from the branch ION <strong>controller port</strong> or <strong>WAN (MPLS) port</strong>, depending on whether the ION is in L2 or L3 mode configuration</mark>.

<strong>Bidirectional forwarding detection (BFD)</strong> probes are also <mark style="background: #D2B3FFA6;">sent between the IONs on the overlay (public and private)</mark> and <mark style="background: #CACFD9A6;">the underlay (private) paths</mark> <mark style="background: #FFB8EBA6;">as heartbeats for detecting the liveliness of the paths</mark>. <mark style="background: #FF5582A6;">These <strong>BFD probes</strong> are sourced and sent in the same way as the LQM probes</mark>.
![[Transport Quality Metrics.png]]
## LQM Measurement on Underlay
The probes for the MPLS underlay are sent from the <strong>branch ION controller port</strong> or <strong>WAN (MPLS) port</strong>, depending on whether the ION is in <strong>L2</strong> or <strong>L3</strong> mode configuration.
### Branch ION 3K in L2 mode
![[Branch ION 3K in L2 mode.png]]The following diagram shows an ION 3K in <mark style="background: #FFB86CA6;">L2 mode configuration</mark>. <mark style="background: #FFF3A3A6;">The WAN/LAN ports are set up as an L2 bypass pair</mark>. In this case, <mark style="background: #BBFABBA6;">LQM probes originate from the ION 3K <strong>controller port</strong></mark>, <mark style="background: #ABF7F7A6;">pass through the LAN, and continue out to the WAN via the L2 private bypass port</mark>.
<mark style="background: #ADCCFFA6;">The destination is the WAN port on the hub ION 9K</mark>.
### Branch ION 3K in L3 mode
![[Branch ION 3K in L3 mode.png]]
The following diagram shows an ION 3K in <mark style="background: #FF5582A6;">L3 mode configuration</mark>. <mark style="background: #FFB86CA6;">In this case, the <strong>WAN port</strong> on the ION 3K is being used as an <strong>individual port</strong></mark> (with L3 WAN Forwarding enabled),<mark style="background: #FFF3A3A6;"> and the LQM probes originate directly from the <strong>WAN interface</strong></mark>.
<mark style="background: #BBFABBA6;">The destination is the WAN port on the hub ION 9K</mark>.
# Application Performance Measurement
Given that the IONs perform real time measurement and analysis from Layers 3 to 7, we can provide rich application performance metrics and react in real time to application performance anomalies.
## Application Health Distribution
<mark style="background: #FFB8EBA6;">Used to track the performance and health of applications</mark>. <mark style="background: #FF5582A6;">This information can be used to identify problems with applications</mark> and <mark style="background: #FFB86CA6;">to make changes to improve performance and reliability</mark>. Based on the latest health score, the graph displays the distribution of Good, Fair, and Poor Applications for a given tenant.
- **Good** (70-100)
- **Fair** (30-69)
- **Poor** (0-29)
![[Application Health Distribution.png]]
## Application Initialization and Transaction Failures
<mark style="background: #BBFABBA6;"><strong>Application initialization</strong> and <strong>transaction failures</strong> are tracked on a <strong>per-destination/application/path basis</strong></mark>, allowing for granular and specific path changes to be made based on each destination IP within a specific application.

- **Init Failure:** <mark style="background: #ADCCFFA6;">Failure to complete the <strong>three-way handshake</strong></mark>. Reasons for failure may include a misconfigured firewall, an application server issue, a misconfigured network access control list, or a WAN network provider issue.
- **TXNs Failure:** <mark style="background: #ABF7F7A6;">Unsuccessful transfer of data after the completion of the three-way handshake</mark>. Reasons for failure can include a misconfigured firewall, an application server issue, a misconfigured network access control list, or a WAN network provider issue.
## Concurrent Flows
<mark style="background: #D2B3FFA6;">The Concurrent Flow chart helps to understand how many connections are active on your network by application</mark>. 

<mark style="background: #CACFD9A6;">The chart provides a granular view by transmission control protocol (TCP) and user datagram protocol (UDP) flows for an application, a specific set of applications, or all applications</mark>. 

Concurrent flows are the currently active flows, including all new flows and mature flows in the system.

The Concurrent Flows charts are used to:
- <mark style="background: #FFB8EBA6;">Analyze a site in terms of connections per second</mark>.
- <mark style="background: #FFB86CA6;">Monitor any unlikely increase in the number of flows for a particular application, such as DNS or any critical application, which could be a sign of malicious activity</mark>.
![[Concurrent Flows.png]]
# 