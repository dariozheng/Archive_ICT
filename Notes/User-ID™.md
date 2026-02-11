---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-04T14:45:11+01:00
modified: 2026-02-11T10:47:27+01:00
---
<strong>User-ID™</strong> technology enables the next-generation firewalls (NGFWs) <mark style="background: #FFB86CA6;">to identify users in all locations, no matter what their device type or operating system is</mark>, <mark style="background: #BBFABBA6;">giving visibility into application activity based on users and groups</mark>, instead of IP addresses.

<mark style="background: #FFB8EBA6;">With User-ID, you can define application access policies based on <strong>users</strong> or <strong>groups</strong> of users</mark>. 

User-ID enable enable the [[Multi-Factor Authentication|Multi-Factor Authentication]], [[Phishing Protection|credential phishing prevention]] and [[Dynamic User Groups|dynamic user groups]] (<strong>DUGs</strong>).

<mark style="background: #CACFD9A6;">With User-ID organization are able to enforce least privilege, where user are enabled only to network they need to</mark>. 
# User-ID Implementation Overview
Here are the steps needed to deploy a identity-aware policy:
- Understand the environment 
- Develop IP-to-User Mapping Strategies for Visibility
- Plan User Groups and Access Rights
- Implement Identity-Based Policies
![[step to deploy identiy-aware policy.png]]
## Understand the Environment
Check: 
- Identity posture 
- Number of users 
- The presence of existing identity providers in the environment that Palo Alto Networks can use for IP-to-user mapping like GlobalProtect, Active Directory Domain Controllers, Cisco ISE or else 
- Which Directory Service is in use, Active Directory, Azure AD, Ping, Okta or else
- The presence of critical assets where [[Multi-Factor Authentication|MFA]] should be implemented 
- The source of enforcement, like a single firewall or multiple firewalls. 
## Identify IP-to-User Mapping Strategies for Visibility
User-ID provides multiple methods to map IP addresses to users. <mark style="background: #ABF7F7A6;">Some methods require specific directory structures to be in place, while other methods may require software agents or clients to be installed</mark>. 
If any of the methods map an IP address to a user successfully, that data can be used by the firewall for both reports and policies.
### [[#IP-to-Username Mapping Methods|User-ID Mapping Methods]]
### User Visibility 
User Visibility require the deployment of <u>User-ID Agents</u>, <u>Terminal Server Agents</u>, and/or integrating <u>third-party IP-to-user mapping sources</u>.
#### [[Data Redistribution Agent|Data Redistribution Agent]] 
<mark style="background: #ADCCFFA6;">Data Redistribution is a mechanism that <strong>shares</strong> IP-to-user mapping, group memberships, and tags across multiple firewalls or Panorama</mark>, <mark style="background: #FFB86CA6;">ensuring consistent identity-based security policies in large-scale, distributed, or multi-site environments</mark>. 
## Plan User Groups and Access Rights 
Once an IP address is mapped to a username, <mark style="background: #FFF3A3A6;">administrators need a way to determine which group the user belongs to</mark> so they can apply policy based on each group's business function(s). 

This is called <strong>group mapping</strong>, and it <mark style="background: #FFB86CA6;">can be enabled by using LDAP and/or the XML API</mark> <mark style="background: #BBFABBA6;">to read group information directly from directory services</mark>. 

Administrators are also able to apply individual policy to specific users in the case where they have individual needs.
![[group mapping.png]]
## Implement Identity-Based Policies
With identity-based security, it's possible to know who is accessing which applications regardless of location or device, and who is transferring files or introducing threats. 

By allowing only the required users to access resources, you can successfully protect your organization from cyber breaches.
#  User-ID Components
User-ID technology has three main components. The following are the primary characteristics of each component.
### Palo Alto Networks Firewall
- Maps IP addresses to usernames
- Maps usernames to group names
### User-ID Agent
- PAN-OS Integrated User-ID Agent
- Windows-Based User-ID Agent

A firewall can communicate with both <strong>integrated</strong> and <strong>Windows-based</strong> agent types at the same time. 

Both agent types monitor up to 100 domain controllers or Exchange servers. 

Both agent types can monitor users and domain controllers only from a single Active Directory (or AD) domain.
#### PAN-OS Integrated User-ID Agent
- Runs on the firewall
- Collects IP address-to-username information
<mark style="background: #ABF7F7A6;">The PAN-OS integrated agent is included with PAN-OS software</mark>. 

The integrated agent is designed for small and midsize deployments such as small remote offices or lab environments.

<mark style="background: #BBFABBA6;">The PAN-OS integrated agent uses either the <strong>[[Windows Management Instrumentation]]</strong> (<strong>WMI</strong>) or the <strong>[[Windows Remote Management Protocol]]</strong> (<strong>WinRM</strong>)</mark>, <mark style="background: #FF5582A6;">which enables the agent to retrieve only the relevant User-ID information from the Windows Security logs</mark>.![[PAN-OS Integrated User-ID Agent.png]]
#### Windows-Based User-ID Agent
- Runs on a domain member
- Collects IP address-to-username information
- Sends information to the firewall
<mark style="background: #FFB86CA6;">The Windows-based agent is available for download from Palo Alto Networks and can be installed on one or more Windows systems</mark>. 

Multiple Windows-based agents can be deployed to handle larger environments or multiforest domains.

<mark style="background: #FFB8EBA6;">The Windows-based agent uses <strong>[[Microsoft Remote Procedure Call|MS-RPC]]</strong></mark>, <mark style="background: #FFF3A3A6;">which requires the full <u>Windows Security logs</u> to be sent to the agent</mark>, <mark style="background: #D2B3FFA6;">where they are filtered for the relevant User-ID information</mark>.
![[indows-Based User-ID Agent.png]]
### Palo Alto Networks Terminal Services Agent
- Runs on Microsoft and Citrix terminal servers
- Collects IP and port number-to-username information
- Sends information to firewall
# IP-to-Username Mapping Methods
#### Server Monitoring 
<mark style="background: #BBFABBA6;">The <strong><u>User-ID agent</u></strong> can monitors <strong>Exchange Servers</strong>, <strong>domain controllers</strong>, or <strong>Novell eDirectory</strong> servers</mark> for <mark style="background: #D2B3FFA6;">log in events</mark>. 

<mark style="background: #ABF7F7A6;">The User-ID agent will then record the IP-to-user mapping</mark>.
#### Client Probing
Client Probing is a legacy method to create IP-to-user mappings and is not recommended as a best practice today. 

In this method, <mark style="background: #D2B3FFA6;">the <u>User-ID agent</u> probes every Windows client using <strong>Windows Management Instrumentation</strong> (WMI)</mark>.
#### Syslog Listenig 
With this integration, the <mark style="background: #FF5582A6;">NGFWs are able to listen for auth syslog messages</mark> from <mark style="background: #BBFABBA6;"><strong>Network Access Control</strong> (NAC) systems, <strong>wireless controllers</strong>, 802.1x devices, Apple Open Directory servers, and proxy servers</mark>.
#### Terminal Server Agent
On shared desktop environments where many users will use a single machine, it can be challenging to map specific activity to individual users. 

<mark style="background: #CACFD9A6;"><strong>The <u>Terminal Server Agent</u></strong> (TSA) monitors traffic to assign usernames to specific traffic in these circumstances</mark> <mark style="background: #FF5582A6;">giving administrators the same visibility and control as they have when users are on individual devices</mark>.
#### Captive Portal 
When Captive Portal is deployed, <mark style="background: #FFB86CA6;">web requests that match an Authentication Policy rule will be redirected to a login portal before being able to proceed</mark>. 

This login portal could be for any traffic coming from an IP address that doesn't already have a user associated with it or as a way to increase security by having a user complete MFA before proceeding to sensitive parts of the network.
#### GlobalProtect
When a customer deploys GlobalProtect <mark style="background: #BBFABBA6;">users have to input their credentials to use the client VPN</mark>. 

<mark style="background: #FF5582A6;">User-ID is able to store that information as an IP-to-user mapping</mark>. 

<mark style="background: #FFB8EBA6;">GlobalProtect then keeps the mapping up to date by automatically re-authenticating the user every time there is a network status change on the endpoint</mark>.
#### XML API 
Some organizations have applications or devices that capture user information but cannot natively integrate with User-ID. 
For example, they might have a custom, internally developed application or a device that is not supported by standard user mapping methods. 

In such cases, you can <mark style="background: #ABF7F7A6;">use the <strong>PAN-OS XML API</strong> to create custom scripts that send the information to the PAN-OS integrated User-ID agent or directly to the firewall</mark>.
#### XFF Headers 
When a proxy server is deployed between the users on a network and the firewall, the firewall might see the proxy server IP address as the source IP address rather than the IP address of the client that requested the content. 

In many cases, <mark style="background: #FF5582A6;">the proxy server adds an <strong>X-Forwarded-For</strong> (XFF) header to traffic packets that includes the actual IP address of the client that requested the content</mark>. 

In such cases,<mark style="background: #D2B3FFA6;"> you can configure the firewall to extract the end user IP address from the <strong>XFF</strong> so that User-ID can create an IP-to-user mapping</mark>.