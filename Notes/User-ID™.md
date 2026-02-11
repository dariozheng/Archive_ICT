---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-04T14:45:11+01:00
modified: 2026-02-11T17:44:23+01:00
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
![[User-ID Mapping Recommendati.png]]
## Server Monitoring 
<mark style="background: #BBFABBA6;"><u>User-ID agents</u> monitors <strong>Microsoft AD domain controllers</strong>, <strong>Microsoft Exchange servers</strong>, or <strong>Novell eDirectory servers</strong></mark> for <mark style="background: #ADCCFFA6;"><strong>login</strong> or <strong>logout</strong> events recorded in Authentication logs</mark>.

<mark style="background: #ABF7F7A6;">The User-ID agent will then record the IP-to-user mapping</mark>.

User-ID also reads session tables to confirm known IP address-to-username mappings based on current Windows file and printer shares.
### Microsoft Active Directory Domain Controllers

![[User-ID Domain Controller Monitoring.png]]
1. When the User-ID agent first starts up, it will parse the security event logs and record all the user login events.
2. Afterward, it will check the Security logs on a regular basis only for new login or logout events.
3. User mappings are cached for an amount of time equal to the timeout value set in the User-ID agent interface.
To ensure that security events are recorded in the Security logs, <mark style="background: #FFB86CA6;">the AD domain must be configured <strong>to log</strong> successful account login events</mark>. 

Because users can authenticate to any domain controller in a domain and the Security logs are not replicated between domain controllers, you also <mark style="background: #FF5582A6;">must set up server monitoring for all domain controllers to capture all user login events</mark>. 

<mark style="background: #FFB8EBA6;">Each User-ID agent can monitor multiple <strong>domain controllers per domain</strong>. However, each User-ID agent can monitor only a <strong>single domain</strong></mark>.

<mark style="background: #FFF3A3A6;">Because server monitoring requires very little overhead and because the majority of users generally can be mapped using this method, Palo Alto Networks recommends it as the base user mapping method for most User-ID deployments</mark>.
#### Windows Session Monitoring
Clients who have connected to a shared file or print resource will have their session information stored on the domain controller. 

An additional Windows-based method to resolve IP addresses to users is to consult the shared resource session table recorded on the domain controller.
![[User-ID Windows Session Monitoring.png]]
## Client Probing
Client Probing is a legacy method to create IP-to-user mappings and is not recommended as a best practice today. 

In this method, <mark style="background: #D2B3FFA6;">the <u>User-ID agent</u> probes every Windows client using [[Windows Management Instrumentation|WMI]]</mark>.
## Syslog Listenig 
With this integration, the <mark style="background: #FF5582A6;">NGFWs are able to listen for auth syslog messages</mark> from <mark style="background: #BBFABBA6;"><strong>Network Access Control</strong> (NAC) systems, <strong>wireless controllers</strong>, 802.1x devices, Apple Open Directory servers, and proxy servers</mark>. 
It's possible <mark style="background: #FFB8EBA6;">to configure these services to send syslog messages that contain information about login and logout events</mark> and <mark style="background: #ABF7F7A6;">configure the User‐ID agent to parse those messages</mark>.
### Receiving Syslog Messages
Both the integrated and Windows-based agents <mark style="background: #D2B3FFA6;">can receive syslog messages</mark>. 

The User‐ID agent can parse for login events to map IP addresses to usernames and parse for logout events so that the firewall deletes outdated mappings. 

Deletion of outdated mappings is particularly useful in environments where IP address assignments change often.
### Parsing Syslog Messages
Both the PAN‐OS integrated User‐ID agent and the Windows‐based User‐ID agent <mark style="background: #ABF7F7A6;">use <strong>Syslog Parse Profiles</strong> to parse syslog messages</mark>. 

In environments where services send the messages in different formats, you can create a custom profile for each format and associate multiple profiles with each sender. 

If you use the PAN‐OS integrated User‐ID agent, you also can use predefined Syslog Parse Profiles that Palo Alto Networks provides through Applications content updates.
## Terminal Server Agent
On shared desktop environments where many users will use a single machine, it can be challenging to map specific activity to individual users. 

<mark style="background: #CACFD9A6;"><strong>The <u>Terminal Server Agent</u></strong> (TSA) monitors traffic to assign usernames to specific traffic in these circumstances</mark> <mark style="background: #FF5582A6;">giving administrators the same visibility and control as they have when users are on individual devices</mark>.
## Captive Portal 
When Captive Portal is deployed, <mark style="background: #FFB86CA6;">web requests that match an Authentication Policy rule will be redirected to a login portal before being able to proceed</mark>. 

This login portal could be for any traffic coming from an IP address that doesn't already have a user associated with it or as a way to increase security by having a user complete MFA before proceeding to sensitive parts of the network.
## GlobalProtect
<mark style="background: #BBFABBA6;">Every GlobalProtect user has an <strong>agent</strong> or <strong>app</strong> running on the client that requires the user to <u>enter login credentials</u> for VPN access to the firewall</mark>. 
<mark style="background: #FF5582A6;">The firewall adds this GlobalProtect login information to the User-ID user mapping table for visibility and user-based policy rule enforcement</mark>.

<mark style="background: #FFF3A3A6;">User-ID information also can be provided from clients that are connected to an internal network via an internal GlobalProtect gateway without establishing a VPN tunnel to a firewall</mark>. <mark style="background: #ADCCFFA6;">Every <strong>internal</strong> GlobalProtect user has an agent or app running on the internal client that requires the user to enter <strong>login credentials</strong> that can be used by the firewall</mark>.

<mark style="background: #ABF7F7A6;">Because GlobalProtect users must authenticate to gain access to the network, the IP address-to-username mapping is explicitly known</mark>. 

<mark style="background: #FFB8EBA6;">GlobalProtect keeps the mapping up to date by automatically re-authenticating the user every time there is a network status change on the endpoint</mark>.
## XML API 
Some organizations have applications or devices that capture user information but cannot natively integrate with User-ID. 
For example, they might have a custom, internally developed application or a device that is not supported by standard user mapping methods. 

In such cases, you can <mark style="background: #ABF7F7A6;">use the <strong>PAN-OS XML API</strong> to create custom scripts that send the information to the PAN-OS integrated User-ID agent or directly to the firewall</mark>.
## XFF Headers 
When a proxy server is deployed between the users on a network and the firewall, the firewall might see the proxy server IP address as the source IP address rather than the IP address of the client that requested the content. 

In many cases, <mark style="background: #FF5582A6;">the proxy server adds an <strong>X-Forwarded-For</strong> (XFF) header to traffic packets that includes the actual IP address of the client that requested the content</mark>. 

In such cases,<mark style="background: #D2B3FFA6;"> you can configure the firewall to extract the end user IP address from the <strong>XFF</strong> so that User-ID can create an IP-to-user mapping</mark>.
# User-ID Configuration Steps 

![[User-ID Configuration Steps.png]]
## Enable User-ID
Enable User-ID technology per zone on the firewall.
![[Enable User-ID.png]]
### Enable User Identification 
<mark style="background: #FFF3A3A6;">For each zone you must select the <strong>Enable User Identification</strong> check box to permit User-ID to probe for users on the zone</mark>. 

<mark style="background: #BBFABBA6;">User-ID tracks only users associated with the source zone of a session</mark>. 

<mark style="background: #FF5582A6;"><strong>Never enable User-ID for a zone that contains the internet</strong>, or your firewall will attempt to identify every user from outside your network</mark>. 

By default, <mark style="background: #ABF7F7A6;">User-ID will try to map users from all subnetworks found within a User-ID-enabled zone</mark>.
### Include List
<mark style="background: #FFB8EBA6;">Use the Include List to limit the subnetworks or specific addresses that the firewall will attempt to map to users</mark>.

>[!info] WMI probing
><strong>WMI probing</strong> is a Palo Alto Networks User-ID feature that queries Windows endpoints via [[Windows Management Instrumentation|Windows Management Instrumentation]] to map IP addresses to active users

<mark style="background: #D2B3FFA6;">If WMI probing is enabled, WMI will probe private IP addresses but not probe public IP addresses by default</mark>. 

<mark style="background: #FFB86CA6;">To enable WMI probing</mark> <mark style="background: #ABF7F7A6;">to map public addresses</mark>, <mark style="background: #FFB86CA6;">you must use the addresses or address ranges in the Include List</mark>.
### Exclude List
Use the Exclude List only to exclude user mapping information for a subset of the subnetworks you added to the Include List.
## Define the Monitored Server(s)
Each User-ID agent must be configured for the servers it needs to monitor.





# User-ID Operation 
Before User-ID can operate, it must be enabled on the security zone. 

If User-ID is enabled, then the firewall consults the administrator-defined User-ID configuration to determine which agents the firewall has available to gather IP address and username information. 

Depending on the configuration, User-ID on the firewall could query either an integrated agent or a Windows-based agent. 
The agent retrieves IP address and username information from the domain controller.

After User-ID has retrieved the IP address and username information from an agent, it can use the firewall’s LDAP configuration to retrieve user-to-group mapping information from an LDAP server.

At this point, User-ID will have an IP address associated with a username and possibly a username associated with one or more group names.