---
categories:
  - "[[Cloud Computing]]"
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
topic@cloud:
  - "[[Cloud Computing General]]"
tags:
  - palo_alto/casb
created: 2026-01-01T22:38:35+01:00
modified: 2026-01-05T12:29:00+01:00
---
<strong>Cloud Access Security Broker</strong> is a [[Cloud Computing Glossary#on premise| on premise]] or [[Cloud Computing Glossary#### cloud-based| cloud-based]] software that sits between cloud services users and cloud application, and it monitors all activity and enforces security policies.

<mark style="background: #FFB8EBA6;"><strong>Cloud Access Security Broker</strong> (CASB) solutions insert <strong>inspection</strong>, <strong>threat-detection</strong>, and <strong>governance</strong> over the access</mark> <mark style="background: #ABF7F7A6;">to</mark> and <mark style="background: #BBFABBA6;">use</mark> of <mark style="background: #FFB8EBA6;">software-as-a-service (SaaS) applications</mark>, such as Microsoft 365, Google Workspace, Dropbox, and Salesforce, just to name a few.
![[CASB elements.png]]

 The graphic depicts how lack of visibility leaves valuable data at risk.
 
![[Data Exposure Threat.png]]

# Data in Motion
## SaaS Visibility

#### Visibility Enhancement 
SaaS visibility enables an initial tier of SaaS security where <mark style="background: #FFB8EBA6;">user access to SaaS destinations is detected</mark>, <mark style="background: #FFB86CA6;">the SaaS application (and, ideally, sub-application) is identified</mark>, and <mark style="background: #ADCCFFA6;">the network-level access to the destination is subject to security policy</mark>. 
#### Policy Inspection
The <mark style="background: #BBFABBA6;">network-access security policy may block or allow the traffic and</mark>, if allowed, then <mark style="background: #CACFD9A6;">inspect the contents of the “data in motion"</mark>. <mark style="background: #ADCCFFA6;">SaaS visibility is provided by a “sensor” function</mark>. In some solutions, the sensor may sit out-of-band from network-traffic control points.
#### Integrated Sensors
<mark style="background: #FFF3A3A6;">Control points are <strong>gateway devices</strong>, typically <strong>firewalls</strong>, <strong>web proxies</strong>, or other <strong>access-control systems</strong></mark>.In solutions, such as the Palo Alto Networks CASB solution, the sensor functionality is integrated with the control point to provide a real-time, inline detection capability.

## SaaS Network-Access Control

#### Gateway Action
SaaS network-access control requires <mark style="background: #BBFABBA6;">action to be taken from a gateway device</mark>, <mark style="background: #ABF7F7A6;">informed by information from the sensor function</mark>. 
#### Sensor Integration
Traditional firewall gateways and proxies work well for combined sensor-enforcement control points. 
Out-of-band sensors are almost always integrated via API with one or more top-tier firewall and/or proxy vendors. 
#### Efficient Solutions
The most efficient CASB solutions are based on <strong>direct gateway integration</strong>, and the gateways are deployed for <mark style="background: #FFF3A3A6;">in-line traffic</mark> <mark style="background: #BBFABBA6;">routing</mark> <mark style="background: #D2B3FFA6;">from central networks</mark> and <mark style="background: #D2B3FFA6;">individual mobile users</mark> <mark style="background: #CACFD9A6;">to various network-access points in the cloud</mark>.

## CASB Integrated Architecture
The Palo Alto Networks solution integrates <mark style="background: #FFB8EBA6;">sensor</mark> and <mark style="background: #FFB86CA6;">access-control</mark> by way of a <mark style="background: #ABF7F7A6;">shared PAN-OS-based infrastructure</mark> that <mark style="background: #BBFABBA6;">spans hardware and software firewalls</mark>, <mark style="background: #CACFD9A6;">whether on-premises or in-cloud</mark>, and <mark style="background: #FFF3A3A6;"><strong>regionally</strong> and <strong>globally</strong> distributed <strong>Prisma Access gateways</strong></mark> for mobile users and remote branches.
![[CASB solution.png]]

# Data at Rest
<mark style="background: #FF5582A6;">Cloud-native, cloud-delivered security tools</mark> like <strong>Prisma Cloud</strong> <mark style="background: #FFB86CA6;">connect directly to services</mark> such as Microsoft 365 or Google Workspace <mark style="background: #ABF7F7A6;">using APIs</mark> to monitor data, activity, and settings inside the application, providing an additional layer of security beyond network protection.

Enabling a <mark style="background: #BBFABBA6;">cloud-delivered SaaS security service</mark> with credentials for security access to the sanctioned SaaS applications, all “data at rest” may then be inspected.

The <mark style="background: #D2B3FFA6;">organizational configuration of the SaaS application</mark> itself may also be inspected and <mark style="background: #FFB86CA6;">application-level access</mark> to <mark style="background: #FFB8EBA6;">SaaS resources</mark> <mark style="background: #ABF7F7A6;">may be dynamically controlled in response to events</mark>.

## Securing Data at Rest
<mark style="background: #FFB8EBA6;">Cloud-application configuration visibility, data inspection, and access-and-content control for data at rest</mark> i<mark style="background: #FF5582A6;">s provided by cloud-to-cloud</mark>, <mark style="background: #FF5582A6;">API-based integration</mark>. The depth and quality of these functions depends on the cloud-delivered–security-services vendor selected.

### Sanctioned vs. Unsanctioned SaaS Applications

A <strong>sanctioned</strong> SaaS application is a cloud-based software service that <mark style="background: #FFF3A3A6;">an organization has officially approved, sponsored, and manages, ensuring it meets security, compliance, and business requirements</mark>.

An <strong>unsanctioned</strong> SaaS application is a cloud-based tool or service used by employees without formal IT approval, creating security blind spots, compliance risks, and potential data breaches.
<mark style="background: #FFF3A3A6;">Use of unsanctioned SaaS applications may be referred to as “shadow IT”</mark>, <mark style="background: #FF5582A6;">because <strong>without</strong> a <strong>network-sensor function</strong></mark>, <mark style="background: #FFF3A3A6;">the use of such applications is unseen, hidden in the shadow (or noise) of other web traffic</mark>.

If an application is <strong>sanctioned</strong>, the CASB solution selected may not provide additional API-based integration to further inspect the data that the application contains or govern any user-credentialed access to the data. 
In such cases, the capability of the sensor-gateway must be relied upon to provide deeper content-level inspection, which may be limited.

![[Inline Flow Governance for SaaS Applications.png]]

#### Advanced API-Based Protection for Sanctioned Apps
Where API-based integrations are supported, the following significant benefits may be achieved, depending on the solution (or solution licensing) selected:

![[Advanced API-Based Protection for Sanctioned Apps.png]]

## Palo Alto Networks CASB Solution at a Glance
Governing organizational use of SaaS applications is a multifaceted challenge. 
<mark style="background: #FFF3A3A6;">CASB solutions require a multiplatform, multi-layered solution</mark>, <mark style="background: #FFF3A3A6;">that is multi-platform</mark> across the <mark style="background: #FFB8EBA6;">cloud-delivered security services application</mark>, <mark style="background: #FFB86CA6;">destination SaaS applications</mark>, <mark style="background: #ADCCFFA6;">gateways</mark>, and <mark style="background: #D2B3FFA6;">mobile/remote access points</mark>.

The specific console view and location of CASB-related information and configuration tools varies based on a customer’s licensing and management of the larger Prisma SASE platform.

![[Palo Alto Networks CASB solution.png]]