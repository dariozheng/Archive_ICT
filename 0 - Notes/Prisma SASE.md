---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/sase
aliases:
  - SASE
icon: SiPaloaltonetworks
iconColor: "#F04E23"
---
![[Prisma SASE Overview.png]]
<mark style="background: #FFB8EBA6;"><strong>Prisma SASE</strong> is a cloud-native architecture</mark> <mark style="background: #FF5582A6;">that unifies <strong>networking</strong> and <strong>security</strong> as a <strong>service</strong> (SaaS) functions into a single <strong>platform</strong></mark>.

![[Prisma Secure Access Service Edge.png]]
### Security as a Service 
<mark style="background: #FFB86CA6;"><strong>Prisma Access</strong> is Palo Alto Networks cloud-delivered <strong>security</strong> platform</mark> <mark style="background: #FFF3A3A6;">that seamlessly connects and secures <strong>any user</strong> from <strong>any device</strong> accessing <strong>any app</strong></mark>.
### Network as a Service 
<strong>Prisma SD-WAN</strong> ensures great user and network experiences in a lightweight, easy-to-deploy solution for branch offices and some home offices.
### Digital Experience Management
<mark style="background: #BBFABBA6;"><strong>Autonomous Digital Experience Management</strong> (<strong>ADEM</strong>) is a service</mark> <mark style="background: #ABF7F7A6;">that provides native <strong>end-to-end visibility</strong> and <strong>performance metrics</strong> for <strong>real application traffic</strong> in your <strong>Secure Access Service Edge</strong> (<strong>SASE</strong>) environment</mark>.
# Prisma SASE Components
## Prisma Access
Prisma Access is the primary security component of the Prisma SASE platform, utilizing a cloud-native virtual infrastructure to protect the hybrid workforce.
![[Prisma Access.png]]
## Secure Web Gateway
The <strong>secure web gateway</strong> functions of Prisma Access help protect the hybrid workforce against <strong>internet-sourced threats</strong> by <strong>securing end-user internet use</strong>.

The <strong>SWG</strong> provides the following services:
- <mark style="background: #FFB8EBA6;">Detection and prevention of threats</mark> using <strong>URL filtering</strong>, <mark style="background: #FF5582A6;">anti-malware</mark>, <mark style="background: #FFB86CA6;">anti-spyware</mark>, and <mark style="background: #FFF3A3A6;">antivirus protection</mark>.
- SaaS <mark style="background: #BBFABBA6;">application discovery and control</mark>
- <strong>Data loss prevention</strong> (<strong>DLP</strong>) capabilities
- <mark style="background: #ABF7F7A6;">Enforcement</mark> of corporate and regulatory <mark style="background: #ABF7F7A6;">policy</mark> compliance
## Explicit Proxy
![[Explicit Proxy.png]]
<strong>Explicit Proxy</strong> uses a <strong>proxy auto-configuration</strong> (<strong>PAC</strong>) file that <mark style="background: #FFB8EBA6;">instructs a web browser to forward traffic to the web proxy server</mark> <mark style="background: #FF5582A6;">instead of the destination server</mark>, effectively <mark style="background: #FFB86CA6;">protecting your web-based internet (HTTP and HTTPS) traffic</mark>.

<mark style="background: #BBFABBA6;">The Explicit Proxy provides <strong>security</strong> and <strong>visibility</strong> for internet traffic</mark> and is an ideal solution for organizations facing specific challenges:
### Cloud Migration Challenge
The organization already uses a web proxy and wants to simplify the migration to a complete cloud-based remote-access solution by using a cloud-based SWG as an intermediate step.
### VPN Client Limitations
The organization is unable or unwilling to install the VPN client (or app) that the remote-access solution requires. 

This includes cases where they use a VPN client for private application access, but the remote-access solution does not provide internet access.
### Lack of Direct Routed Path
There is no direct routed path to the internet. This includes networks that do not provide default routing capabilities.
## Zero Trust Network Access
It is important <mark style="background: #FFB8EBA6;">to identify the protection surface</mark> and <mark style="background: #FF5582A6;">where sensitive data is stored</mark>, <mark style="background: #FFB86CA6;">determine who will need access to that data</mark>, and then <mark style="background: #FFF3A3A6;">implement the necessary required security prevention methods</mark> to protect the data with <strong>ZTNA</strong>. 

These include <strong>multi-factor authentication</strong> (MFA), <strong>least privilege access</strong>, <strong>unified policies</strong>, <strong>micro-segmentation</strong>, and more. 

With ZTNA, there is no trust whatsoever. All users and devices are thoroughly examined without any exceptions.
### Least Privilege Access
Palo Alto Networks [[App-ID™|App-ID]], [[User-ID™|User-ID]], and [[Device-ID|Device-ID]] deliver rich <strong>context</strong> and a more granular approach to <mark style="background: #FFF3A3A6;">allowing access to applications</mark>. 

The App-ID capabilities of Prisma Access are stateful and continuously gather information about the Transmission Control Protocol (TCP) session, the application handshakes, the application behavior, the stateful protocols, and more. 
Simultaneously, User-ID and Device-ID controls also persistently collect information about users and their devices.

This integration offers insights into users' access to specific applications they request while continuously gathering additional context, such as user or app behavior or device ID changes. As a result, it allows for real-time responses to these changes. 
### Continuous Protection
<mark style="background: #FFB8EBA6;">Prisma SASE protection starts once access is granted to an app</mark>. 
It will <mark style="background: #FF5582A6;">continually assess</mark> both <mark style="background: #FFB86CA6;">the user behavior</mark> and the <mark style="background: #FFF3A3A6;">app behavior</mark> <mark style="background: #BBFABBA6;">to verify no changes have taken place</mark>. 
If there are any changes, Prisma SASE will respond appropriately. 

It provides continuous ongoing <mark style="background: #ABF7F7A6;">deep inspection of all traffic</mark>, even for allowed connections to prevent all threats, including zero-day threats. It will also provide continuous protection across all apps used in the enterprise, including private apps and SaaS, with a single DLP policy.
## Firewall as a Service
<strong>NGFWs</strong> provide <mark style="background: #FF5582A6;">deep packet inspections</mark> that are beyond legacy port and protocol inspections and blocking to add an application inspection.
- Traditional stateful firewall features
- Application-aware, deep packet content inspection
- Unified threat management (UTM), including intrusion detection and prevention systems (IDPSs)
- Advanced visibility across the entire attack surface
- Flexibility to address the evolving threat landscape
## Cloud Access Security Brokers
<strong>CASBs</strong> can be on-premises or cloud-based <mark style="background: #FFB8EBA6;"><strong>services</strong> that provide <strong>security policy enforcement points</strong></mark> between <mark style="background: #FFB86CA6;">those who use or consume the cloud service</mark> and <mark style="background: #FFF3A3A6;">those who provide it</mark>.

CASB addresses the issues of <strong>securing</strong> <mark style="background: #BBFABBA6;">the cloud services being adopted both inside and outside the traditional fixed perimeter of the network</mark>, along with the increased implementation of direct cloud-to-cloud access. 

<mark style="background: #ABF7F7A6;">The <strong>CASB</strong> sits between the two</mark> and allows cloud service providers to implement security policies for cloud-based data and applications. Prisma SASE delivers CASB services, which include the following capabilities:
- <strong>Inspect</strong> <mark style="background: #FF5582A6;">data</mark>, <mark style="background: #FFB8EBA6;">application</mark>, and <mark style="background: #FFB86CA6;">user</mark> behavior in cloud services <mark style="background: #FFF3A3A6;">via provider application programming interfaces (APIs)</mark>.
- Operate <strong>inline</strong> between <mark style="background: #BBFABBA6;">users and cloud services</mark> or optionally offer Remote Browser Isolation (RBI) as an alternative.
- Support the ability to provide <strong>visibility</strong> and <mark style="background: #ADCCFFA6;">perform access control of any user, device, or location</mark>.
- <strong>Integrate</strong> with an enterprise’s existing <mark style="background: #D2B3FFA6;">identity provider</mark>, <mark style="background: #CACFD9A6;">security information and event management (SIEM) tool</mark>, and <mark style="background: #FFF3A3A6;">unified endpoint management (UEM) product</mark>.
- Apply a variety of analytics when monitoring the behavior of users, third-party applications, and data.
- Identify and respond to malicious and unwanted <mark style="background: #D2B3FFA6;">sessions</mark> using multiple methods.
- <mark style="background: #FFB8EBA6;">Distinguish between corporate and personal instances of cloud services</mark> and <mark style="background: #FFF3A3A6;">provide the ability to limit or block the exchange of data between them</mark>.
# 