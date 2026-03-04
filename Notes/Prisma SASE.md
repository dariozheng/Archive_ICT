---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/sase
aliases:
  - SASE
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
The <strong>secure web gateway</strong> functions of Prisma Access help protect the hybrid workforce against <strong>internet-sourced threats</strong> by securing <strong>end-user internet use</strong>.

The SWG provides the following services:
- Detection and prevention of threats using URL filtering, anti-malware, anti-spyware, and antivirus protection
- SaaS application discovery and control
- Data loss prevention (DLP) capabilities
- Enforcement of corporate and regulatory policy compliance
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
Palo Alto Networks [[App-ID™|App-ID]], [[User-ID™|User-ID]], and [[Device-ID|Device-ID]] deliver rich context and a more granular approach to allowing access to applications. 

The App-ID capabilities of Prisma Access are stateful and continuously gather information about the Transmission Control Protocol (TCP) session, the application handshakes, the application behavior, the stateful protocols, and more. 
Simultaneously, User-ID and Device-ID controls also persistently collect information about users and their devices.

This integration offers insights into users' access to specific applications they request while continuously gathering additional context, such as user or app behavior or device ID changes. As a result, it allows for real-time responses to these changes. 
### Continuous Protection
Prisma SASE protection starts once access is granted to an app. 

It will continually assess both the user behavior and the app behavior to verify no changes have taken place. 

If there are any changes, Prisma SASE will respond appropriately. 

However, Prisma SASE does not stop there. It provides continuous ongoing deep inspection of all traffic, even for allowed connections to prevent all threats, including zero-day threats. It will also provide continuous protection across all apps used in the enterprise, including private apps and SaaS, with a single DLP policy.
## Firewall as a Service
Next-generation firewalls (NGFWs) provide deep packet inspections that are beyond legacy port and protocol inspections and blocking to add an application inspection.
## Cloud Access Security Brokers
CASBs can be on-premises or cloud-based services that provide security policy enforcement points between those who use or consume the cloud service and those who provide it.

A CASB offers products and services that will address any security deficiencies within an enterprise's use of cloud services. 

CASB addresses the issues of securing the cloud services being adopted both inside and outside the traditional fixed perimeter of the network, along with the increased implementation of direct cloud-to-cloud access. 

The CASB sits between the two and allows cloud service providers to implement security policies for cloud-based data and applications. Prisma SASE delivers CASB services, which include the following capabilities:
- Inspect data, application, and user behavior in cloud services via provider application programming interfaces (APIs).
- Operate inline between users and cloud services or optionally offer Remote Browser Isolation (RBI) as an alternative.
- Support the ability to provide visibility and perform access control of any user, device, or location.
- Integrate with an enterprise’s existing identity provider, security information and event management (SIEM) tool, and unified endpoint management (UEM) product.
-  Apply a variety of analytics when monitoring the behavior of users, third-party applications, and data.
- Identify and respond to malicious and unwanted sessions using multiple methods.
- Distinguish between corporate and personal instances of cloud services and provide the ability to limit or block the exchange of data between them.