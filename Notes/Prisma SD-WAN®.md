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

# Palo Alto Prisma SD-WAN ION
<mark style="background: #BBFABBA6;"><strong>Palo Alto Networks Prisma SD-WAN Instant-On Network (ION)</strong> <strong>devices</strong> are available in both hardware and software form factors to meet the needs of any location and any deployment scenario</mark>. 

<mark style="background: #D2B3FFA6;">All ION devices are built with <strong>FIPS 140-2</strong> as a security baseline</mark>. <mark style="background: #CACFD9A6;">Encryption keys are specific to each customer and device, with high-frequency key rotation</mark> <mark style="background: #FFB8EBA6;">occurring at a network level for large-scale, full-mesh, partial-mesh, or hub-and-spoke VPN networks</mark>. <mark style="background: #FF5582A6;">All IONs have an <strong>AUX (console) port</strong>, which you can connect at a baud rate of <strong>115200</strong> for out-of-band management</mark>.

<mark style="background: #ABF7F7A6;">Prisma SD-WAN virtual form factors can be deployed on ESXi, KVM, Hyper-V, and cloud platforms, such as Amazon Web Services (AWS), Microsoft Azure, and Google Cloud Platform (GCP)</mark>.
##### Licensing 
Depending on where the ION device will be deployed, you must purchase a bandwidth-based subscription or data-center subscription.
- Branch site: For ION devices being deployed at branch sites, the options for bandwidth-based subscriptions range from 25Mbps to 2.5Gbps.
- Data-center site: For ION devices being deployed at data-center sites, there is one data-center subscription option.
##### ION Hardware Models
![[ION Hardware Models.png]]
#### ION Software Models
Prisma SD-WAN ION software models can be deployed on ESXi, KVM, and Hyper-V. Additionally, the 7108V can be deployed on Azure, AWS, and GCP cloud platforms.
![[ION Software Models.png]]
# Prisma SD-WAN Deployment
The Prisma SD-WAN non-disruptive insertion model enables customers to easily transition existing sites to the Prisma SD-WAN. 

The Prisma SD-WAN approach is referred to as the “Crawl, Walk, Run” model: the approach enables customers to deploy Prisma SD-WAN as aggressively as they want to meet their requirements.
## Analytics Mode
In the first insertion mode (or phase), <mark style="background: #FFB8EBA6;">the Prisma SD-WAN ION hardware appliance is deployed inline at the branch between the Layer 2 or Layer 3 switch and the existing router</mark>. 

In this mode, <mark style="background: #FF5582A6;">Prisma SD-WAN simply collects rich, detailed network and application analytics data. No VPN tunnels are created and Prisma SD-WAN does not select any paths</mark>.

Most deployments initially utilize this mode for a few days to allow Prisma SD-WAN to better understand the applications running on the network and their performance characteristics. The data collected during this period can then be used to design application policies.
## Control
After a customer uses analytics-only mode, they can easily switch the device to control mode. 

In this mode, <mark style="background: #FFB86CA6;">Prisma SD-WAN utilizes all the application and network data it has collected to take action in selecting a driven path</mark>. Here, the full functionality of Prisma SD-WAN is delivered without requiring the replacement of the pre-existing router.

Many customers prefer to start their SD-WAN deployment in this mode, because they either own their existing routers and still have years left of depreciation on them or they have carrier-managed routers as part of their existing telecommunications contract.

An added benefit of control mode is that <mark style="background: #FFF3A3A6;">the <strong>Prisma SD-WAN ION device</strong> has integrated fail-to-wire interfaces, which enable an added level of high availability. If either the ION device or the router fails, the surviving device can take over without disrupting connectivity</mark>.
## Router Replacement 
Prisma SD-WAN can run in full-router-replacement mode, which eliminates the need for a router. 

Existing MPLS and internet connections can be directed into the Prisma SD-WAN ION device. Additionally, Prisma SD-WAN has a built-in application zone-based firewall, which enables the consolidation of branch firewall appliances onto the ION device.
# Prisma SD-WAN Site and Devices
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
#