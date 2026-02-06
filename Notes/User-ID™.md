---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-04T14:45:11+01:00
modified: 2026-02-06T12:08:26+01:00
---
<strong>User-ID™</strong> technology enables the next-generation firewalls (NGFWs) <mark style="background: #FFB86CA6;">to identify users in all locations, no matter what their device type or operating system is</mark>, <mark style="background: #BBFABBA6;">giving visibility into application activity based on users and groups</mark>, instead of IP addresses.

<mark style="background: #FFB8EBA6;">With User-ID, you can define application access policies based on <strong>users</strong> or <strong>groups</strong> of users</mark>. 

User-ID enable enable the <strong>[[Multi-Factor Authentication|Multi-Factor Authentication]]</strong>, <strong>credential phishing prevention</strong> and <strong>dynamic user groups</strong> (<strong>DUGs</strong>).

<mark style="background: #CACFD9A6;">With User-ID organization are able to enforce least privilege, where user are enabled only to network they need to</mark>. 
# User-ID Implementation 
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
- The presence of critical assets where MFA should be implemented 
- The source of enforcement, like a single firewall or multiple firewalls. 
