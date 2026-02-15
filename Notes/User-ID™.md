---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-04T14:45:11+01:00
modified: 2026-02-15T21:32:27+01:00
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
User-ID provides multiple [[#IP-to-Username Mapping Methods|methods]] to map IP addresses to users. <mark style="background: #ABF7F7A6;">Some methods require specific directory structures to be in place, while other methods may require software agents or clients to be installed</mark>. 
If any of the methods map an IP address to a user successfully, that data can be used by the firewall for both reports and policies.
## Plan User Groups and Access Rights 
Once an IP address is mapped to a username, <mark style="background: #FFF3A3A6;">administrators need a way to determine which group the user belongs to</mark> so they can apply policy based on each group's business function(s). 

This is called <strong>group mapping</strong>, and it <mark style="background: #FFB86CA6;">can be enabled by using LDAP and/or the XML API</mark> <mark style="background: #BBFABBA6;">to read group information directly from directory services</mark>. 

Administrators are also able to apply individual policy to specific users in the case where they have individual needs.

![[group mapping.png]]
## Implement Identity-Based Policies
With identity-based security, it's possible to know who is accessing which applications regardless of location or device, and who is transferring files or introducing threats. 
By allowing only the required users to access resources, you can successfully protect your organization from cyber breaches.
# User-ID Components
User-ID technology has three main components. 
### Palo Alto Networks Firewall
- Maps IP addresses to usernames
- Maps usernames to group names
### User-ID Agent
- PAN-OS Integrated User-ID Agent
- Windows-Based User-ID Agent

<mark style="background: #BBFABBA6;">A firewall can communicate with both <strong>integrated</strong> and <strong>Windows-based</strong> agent types at the same time</mark>. 

<mark style="background: #D2B3FFA6;">Both agent types monitor up to 100 domain controllers or Exchange servers</mark>. 

<mark style="background: #FFB8EBA6;">Both agent types can monitor users and domain controllers only from a single Active Directory (or AD) domain</mark>.
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
<mark style="background: #FFF3A3A6;">With server monitoring a <strong>User-ID agent</strong></mark>—<mark style="background: #FF5582A6;">either a Windows-based agent <strong>running on a domain server in your network</strong></mark>, or <mark style="background: #BBFABBA6;">the PAN-OS integrated User-ID agent <strong>running on the firewall</strong></mark>—<mark style="background: #FFF3A3A6;"><strong>monitors</strong> the security event logs for specified <strong>Microsoft Exchange Servers</strong>, <strong>Domain Controllers</strong>, or <strong>Novell eDirectory servers</strong> for <strong>login</strong> events or <strong>logout</strong> events recorded in Authentication logs</mark>.

<mark style="background: #ABF7F7A6;">The User-ID agent will then <strong>record</strong> the IP-to-user mapping</mark>.

For example, in an AD environment, you can configure the User-ID agent to monitor the security logs for Kerberos ticket grants or renewals, Exchange server access (if configured), and file and print service connections. 
For these events to be recorded in the security log, the AD domain must be configured to log successful account login events. 
In addition, <mark style="background: #D2B3FFA6;">because users can log in to any of the servers in the domain, you must set up server monitoring for all servers to capture all user login events</mark>. 
### Microsoft Active Directory Domain Controllers

![[User-ID Domain Controller Monitoring.png]]
1. When the User-ID agent first starts up, it will parse the security event logs and record all the user login events.
2. Afterward, it will check the Security logs on a regular basis only for new login or logout events.
3. User mappings are cached for an amount of time equal to the timeout value set in the User-ID agent interface.
To ensure that security events are recorded in the Security logs, <mark style="background: #FFB86CA6;">the AD domain must be configured <strong>to log</strong> successful account login events</mark>. 

Because users can authenticate to any domain controller in a domain and the Security logs are not replicated between domain controllers, you also <mark style="background: #FF5582A6;">must set up [[#Server Monitoring|server monitoring]] for all domain controllers to capture all user login events</mark>. 

<mark style="background: #FFB8EBA6;">Each User-ID agent can monitor multiple <strong>domain controllers per domain</strong>. However, each User-ID agent can monitor only a <strong>single domain</strong></mark>.

<mark style="background: #FFF3A3A6;">Because [[#Server Monitoring|server monitoring]] requires very little overhead and because the majority of users generally can be mapped using this method, Palo Alto Networks recommends it as the base user mapping method for most User-ID deployments</mark>.
### Windows Session Monitoring
<mark style="background: #BBFABBA6;">Clients who have connected to a shared file or print resource will have their session information stored on the domain controller</mark>. 

<mark style="background: #D2B3FFA6;">An additional Windows-based method to resolve IP addresses to users is to consult the shared resource session table recorded on the domain controller</mark>.
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
<mark style="background: #CACFD9A6;">In environments with multi-user systems—such as <strong>Microsoft Terminal Server</strong>, <strong>Citrix</strong> environments or other shared desktop environments</mark>—<mark style="background: #ABF7F7A6;">many users share the same IP address</mark>. 

<mark style="background: #BBFABBA6;">In this case, the user-to-IP address mapping process requires knowledge of the source port of each client</mark>. 

<mark style="background: #ABF7F7A6;">To perform this type of mapping, you must install the <strong>Palo Alto Networks Terminal Server Agent</strong> on the <strong>Windows/Citrix terminal server</strong> itself</mark> <mark style="background: #FFB8EBA6;">to intermediate the assignment of <strong>source ports</strong> to the various user processes</mark>. 

<mark style="background: #CACFD9A6;"><strong>The Terminal Server Agent</strong> (TSA) monitors traffic to assign usernames to specific traffic in these circumstances</mark> <mark style="background: #FF5582A6;">giving administrators the same visibility and control as they have when users are on individual devices</mark>.

<mark style="background: #FFF3A3A6;">For terminal servers that do not support the Terminal Server agent, such as Linux terminal servers, you can use the <strong>XML API</strong> to send user mapping information from login and logout events to User-ID</mark>.
## Authentication Policy and Authentication Portal
In some cases, the User-ID agent can’t map an IP address to a username using server monitoring or other methods—for example, if the user isn’t logged in or uses an operating system such as Linux that your domain servers don’t support. 

In other cases, you might want users to authenticate when accessing sensitive applications regardless of which methods the User-ID agent uses to perform user mapping. 

For all these cases, <mark style="background: #FFF3A3A6;">you can configure a <strong>Authentication policy</strong> and map IP addresses to username using a <strong>Authentication Portal</strong></mark>. 

<mark style="background: #FFB8EBA6;">Any web traffic (<strong>HTTP</strong> or <strong>HTTPS</strong>) that matches an <strong>Authentication policy rule</strong> prompts the user to authenticate through <strong>Authentication Portal</strong></mark>. 
This ensures that you know exactly who is accessing your most sensitive applications and data. 

Based on user information collected during authentication, the firewall creates a new IP address-to-username mapping or updates the existing mapping for that user.
### Authentication Portal or Captive Portal
#### Authentication Portal Authentication Methods
Authentication Portal uses the following methods to authenticate users whose web requests match Authentication Policy rules:
##### Kerberos SSO
The firewall uses <strong>Kerberos single sign-on</strong> (<strong>SSO</strong>) to transparently obtain user credentials from the browser. 

To use this method, your network requires a Kerberos infrastructure, including a key distribution center (<strong>KDC</strong>) with an authentication server and ticket granting service. 

The firewall must have a Kerberos account.

If Kerberos SSO authentication fails, the firewall falls back to web form or client certificate authentication, depending on your Authentication policy and Authentication Portal configuration.
##### Web Form
<mark style="background: #FFF3A3A6;">The firewall redirects web requests to a web form for authentication</mark>. 

For this method, <mark style="background: #FFB86CA6;">you can configure Authentication policy to use [[Multi-Factor Authentication|MFA]], SAML, Kerberos, TACACS+, RADIUS, or LDAP authentication</mark>. 

<mark style="background: #FFF3A3A6;">Although users have to manually enter their login credentials, this method works with all browsers and operating systems</mark>.
##### Client Certificate Authentication
<mark style="background: #BBFABBA6;">The firewall prompts the browser to present a valid client certificate to authenticate the user</mark>. 

<mark style="background: #CACFD9A6;">To use this method, you must provision client certificates on each user system and install the trusted certificate authority (CA) certificate used to issue those certificates on the firewall</mark>.
#### Authentication Portal Modes
The Authentication Portal mode defines how the firewall captures web requests for authentication:
##### Transparent
<mark style="background: #FF5582A6;">The firewall intercepts the browser traffic per the Authentication policy rule</mark> and <mark style="background: #FFB86CA6;">impersonates the original destination URL</mark>, <mark style="background: #BBFABBA6;">issuing an HTTP 401 to invoke authentication</mark>. 

<mark style="background: #ABF7F7A6;">However, because the firewall does not have the real certificate for the destination URL, the browser displays a certificate error to users attempting to access a secure site</mark>. 

<mark style="background: #ADCCFFA6;">Therefore, use this mode only when absolutely necessary, such as in Layer 2 or virtual wire deployments</mark>.
##### Redirect
<mark style="background: #D2B3FFA6;">The firewall intercepts unknown HTTP or HTTPS sessions and redirects them to a Layer 3 interface on the firewall</mark> <mark style="background: #BBFABBA6;">using an HTTP 302 redirect to perform authentication</mark>. 

This is the preferred mode because it provides a better end-user experience (no certificate errors). 

However, it does require additional Layer 3 configuration. 

Another benefit of the Redirect mode is that <mark style="background: #FF5582A6;">it provides for the use of session cookies</mark>, <mark style="background: #FFB8EBA6;">which enable the user to continue browsing to authenticated sites without requiring re-mapping each time the timeouts expire</mark>. 
This is especially useful for users who roam from one IP address to another (for example, from the corporate LAN to the wireless network) because they won’t need to re-authenticate when the IP address changes as long as the session stays open.

<mark style="background: #BBFABBA6;">If you use <strong>Kerberos SSO</strong>, you must use Redirect mode because the browser will provide credentials only to trusted sites</mark>. 

<mark style="background: #D2B3FFA6;"><strong>Redirect</strong> mode is also required if you use <strong>Multi-Factor Authentication</strong> to authenticate Authentication Portal users</mark>.
#### Configure Authentication Portal #configuration 
Based on their sensitivity, the applications that users access through <strong>Authentication Portal</strong> require different authentication methods and settings. 

To accommodate all authentication requirements, you can use <strong>default</strong> and <strong>custom</strong> authentication enforcement objects. 

<mark style="background: #FFB86CA6;">Each object associates an <strong>Authentication rule</strong> with an <strong>authentication profile</strong> and an <strong>Authentication Portal</strong> authentication method</mark>. <mark style="background: #FFF3A3A6;"><strong>Authentication profiles</strong> are necessary only if users authenticate through a <strong>Authentication Portal Web Form</strong> or <strong>Kerberos SSO</strong></mark> not on <strong>Certificate Authentication</strong> method.
##### Default authentication enforcement objects
<mark style="background: #FFB8EBA6;">Use the <strong>default objects</strong> if you want to associate multiple <strong>Authentication rules</strong> with the same <strong>global authentication profile</strong></mark>. 

<mark style="background: #BBFABBA6;">You must configure an <strong>authentication profile</strong> before configuring <strong>Authentication Portal</strong>, and then assign it in the <strong>Authentication Portal Settings</strong></mark>. 

For <strong>Authentication rules</strong> that require <strong>Multi-Factor Authentication</strong> (MFA), you cannot use default authentication enforcement objects.
##### Custom authentication enforcement objects
<mark style="background: #FFF3A3A6;">Use a custom object for each <strong>Authentication rule</strong> that requires an authentication profile that differs from the global profile</mark>. 

<mark style="background: #FF5582A6;">Custom objects are mandatory for <strong>Authentication rules</strong> that require MFA</mark>. 

To use custom objects, create <strong>authentication profiles</strong> and assign them to the objects after configuring <strong>Authentication Portal</strong>,when you configure the Authentication Policy.
##### Certificate Authentication
![[Configure Authentication Portal.pdf]]

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
<mark style="background: #FFF3A3A6;">When a proxy server is deployed between the users on a network and the firewall, the firewall might see the proxy server IP address as the source IP address</mark> <mark style="background: #FFB86CA6;">rather than the IP address of the client that requested the content</mark>. 

In many cases, <mark style="background: #FF5582A6;">the proxy server adds an <strong>X-Forwarded-For</strong> (XFF) header to traffic packets that includes the actual IP address of the client that requested the content or from whom the request originated</mark>. 

In such cases,<mark style="background: #D2B3FFA6;"> you can configure the firewall to extract the end user IP address from the <strong>XFF</strong> so that User-ID can create an IP-to-user mapping</mark>.

<mark style="background: #FFF3A3A6;">This enables you to use <strong>XFF values</strong> for policies and logging source users</mark>, so that you can enforce user-based policy to safely enable access to web-based for your users behind a proxy server.
# User-ID Configuration Steps #configuration

![[Enable User-ID 0.png]]
## Enable User-ID #configuration 
Enable User-ID technology per zone on the firewall.
![[Enable User-ID 1.png]]
### Enable User Identification 
<mark style="background: #FFF3A3A6;">For each zone you must select the <strong>Enable User Identification</strong> check box to permit User-ID to probe for users on the zone</mark>. 

<mark style="background: #BBFABBA6;">User-ID tracks only users associated with the source zone of a session</mark>. 

<mark style="background: #FF5582A6;"><strong>Never enable User-ID for a zone that contains the internet</strong>, or your firewall will attempt to identify every user from outside your network</mark>. 

By default, <mark style="background: #ABF7F7A6;">User-ID will try to map users from all subnetworks found within a User-ID-enabled zone</mark>.
### Include List
<mark style="background: #FFB8EBA6;">Use the <strong>Include List</strong> to limit the subnetworks or specific addresses that the firewall will attempt to map to users</mark>.

<mark style="background: #D2B3FFA6;">If [[#WMI Client Probing|WMI Probing]] is enabled, WMI will probe private IP addresses but not probe public IP addresses by default</mark>. 

<mark style="background: #FFB86CA6;">To enable WMI probing</mark> <mark style="background: #ABF7F7A6;">to map public addresses</mark>, <mark style="background: #FFB86CA6;">you must use the addresses or address ranges in the Include List</mark>.
### Exclude List
Use the <strong>Exclude List</strong> only to exclude user mapping information for a subset of the subnetworks you added to the Include List.
## PAN-OS Integrated User-ID Agent Configuration #configuration 
![[Define the Monitored Server(s).png]]
### Define the Monitored Server(s)
Each User-ID agent must be configured for the servers it needs to monitor.

The agent includes an autodiscovery feature that, via DNS, automatically identifies available Microsoft Windows servers for event log monitoring. 
<mark style="background: #FFF3A3A6;">The integrated agent supports [[Windows Management Instrumentation|WMI]] and [[Windows Remote Management Protocol|WinRM]] protocols to map IP addresses to usernames</mark>. 

<mark style="background: #BBFABBA6;">The firewall will discover domain controllers based on the domain name entered in the Domain field of the <strong>Device > Setup > Management > General Settings</strong> page</mark>.

![[Define the Monitored Server(s) 1.png]]
### Define the User-ID Agent Account
![[Define the User-ID Agent Account.png]]
<mark style="background: #ABF7F7A6;">Set the domain credentials for the account the firewall will use to access Windows resources</mark>. 

<mark style="background: #ADCCFFA6;">This setting is required for monitoring domain controllers and Exchange servers. 
The information in the Username field must be entered using the format <strong>domain\username</strong></mark>.
#### Configuring Permissions 
No special permissions configuration is necessary if <mark style="background: #FFB86CA6;">the integrated agent runs as an account that belongs to the Domain Administrators group or belongs to the Server Operators and Event Log Readers groups</mark>. 

However, membership in these groups provides the account with more permissions than just the capability to perform [[#Server Monitoring|server monitoring]] or client probing. 

Therefore, <mark style="background: #D2B3FFA6;">you might want to run the agent using a restricted account with minimal permissions</mark>. 

The steps to configure an account with minimal Windows permissions depend on the Windows operating system version you have.
### Session Monitoring 
To enable [[#Windows Session Monitoring|session monitoring]], select the <strong>Enable Session</strong> check box

This setting enables <mark style="background: #FFB8EBA6;">the integrated agent to use current file and print sharing information to verify current IP address-to-username mappings</mark>.
![[attachments/Session Monitoring.png]]
### WMI Client Probing
<strong>WMI probing</strong> is a Palo Alto Networks User-ID feature that <mark style="background: #FFB8EBA6;">queries Windows endpoints via [[Windows Management Instrumentation|Windows Management Instrumentation]] to map IP addresses to active users</mark>.

You can enable the integrated agent to perform <mark style="background: #BBFABBA6;">WMI probing for each client system that the user mapping process identifies</mark>. 

<mark style="background: #FFF3A3A6;">The integrated agent periodically probes each learned IP address to verify that the same user still is logged in</mark>. 

<mark style="background: #D2B3FFA6;">When a firewall encounters an IP address for which it has no user mapping, it sends the address to the integrated agent for an immediate probe</mark>.
![[WMI Client Probing.png]]
## Windows-Based Agent Configuration #configuration 

<img src="Windows-Based Agent Configuration.png" style="background-color:grey;" />
### Installation Location 
The Windows-based agent can be installed on machines running Windows Server 2008 or later.  

<mark style="background: #CACFD9A6;">You should install the agent in the same network site as the monitored server to optimize bandwidth use</mark>. 

<mark style="background: #FFB86CA6;">You should install two agents on two member servers for redundancy in case one agent or one domain controller fails</mark>.
![[Installation Location.png]]
Although an agent could be installed directly on a domain controller, that is not a best practice.
### User-ID Agent Software
Use your Palo Alto Networks support account to log in to the Support website. 

After you are logged in, click the Updates > Software Updates link to open the page shown here. 

To simplify finding the User-ID agent download links, use the <strong>Filter By menu</strong> to filter the list for <strong>User Identification Agent</strong>. Then find and download the User-ID agent version that matches your PAN-OS version.
![[User-ID Agent Software.png]]
The installation can be <strong>manual</strong>, <mark style="background: #ADCCFFA6;">installing each agent individually by manually launching the downloaded MSI file</mark>, or <strong>automated</strong> where it's possible <mark style="background: #BBFABBA6;">to use endpoint management software such as <strong>Microsoft System Center Configuration Manager</strong> (or SCCM) to remotely install, configure, or upgrade multiple agents in a single operation</mark>.
### Agent Setup Process
![[Agent Setup Process.png]]
<mark style="background: #FFF3A3A6;">Click <strong>Setup</strong> to configure the User-ID agent, click the <strong>Edit</strong> button to open a separate tabbed window that enables you to change any of the settings shown in the Setup pane.
Then, click <strong>Save</strong> to save your configuration changes but not activate them. Click <strong>Commit</strong> to save and activate your configuration changes. Click <strong>Exit</strong> to close the window without saving your changes</mark>.

By default, <mark style="background: #ADCCFFA6;">the User-ID agent uses TCP port 5007 to communicate to the firewall</mark>. You can change to another port, if necessary, by clicking Edit and then clicking the <strong>Agent Service</strong> tab in the window that opens.
### Configure the User-ID Agent Account
The agent should run with a Windows service account that has the necessary permissions to read the security event logs or to perform WMI probing.
##### Authentication tab
Use the Authentication tab to <mark style="background: #FFF3A3A6;">configure the agent to use a specific <strong>Windows service account</strong></mark>. 
<mark style="background: #BBFABBA6;">The authentication information must be configured before you can configure access to monitored servers</mark>. 

<mark style="background: #ADCCFFA6;">By default, the Windows agent runs as the user account used to install the <strong>.msi</strong> file</mark>. 

<mark style="background: #FFB8EBA6;">Most of the necessary permissions are provided if the <strong>Windows-based agent</strong> runs as <u>an account that belongs to the <strong>Domain Administrators</strong> group or to the <strong>Server Operators</strong> and <strong>Event Log Readers</strong> groups</u></mark>. 

<mark style="background: #FFB86CA6;">The user account running the agent also must have permissions to start a <strong>Windows service</strong></mark>. 

However, membership in these groups provides the account with more permissions than just the capability to perform [[#Server Monitoring|server monitoring]] or client probing. 

<mark style="background: #FFF3A3A6;">Therefore, you might want to run the agent using a restricted account with minimal permissions</mark>. 
<mark style="background: #ADCCFFA6;">The steps to configure an account with minimal Windows permissions depend on the Windows operating system version you have</mark>.
![[Authentication tab.png]]
##### Server Monitor Tab
Use the Server Monitor tab to configure [[#Server Monitoring|server monitoring]] or to enable the optional [[#Windows Session Monitoring|session monitoring]].
![[Server Monitor Tab.png]]
##### Client Probing Tab
<mark style="background: #FFB8EBA6;">You can use the Client Probing tab to configure the agent <u>to probe IP addresses</u> for username information</mark>. 

Unlike server monitoring, probing is an active method: 
- <mark style="background: #BBFABBA6;">The User-ID agent sends a probe</mark> at a configurable interval <mark style="background: #BBFABBA6;">to each learned IP address in its list to verify that the same user still is logged in</mark>. 
- <mark style="background: #D2B3FFA6;">The results of the probes are used to update the records on the agent</mark>, <mark style="background: #CACFD9A6;">which are passed on to the firewall</mark>. 
- <mark style="background: #FFB86CA6;">Each learned IP is probed once per interval period</mark>. 
- <mark style="background: #FF5582A6;"><strong>WMI probing must be enabled on the Windows machines for the probe to succeed</strong></mark>.

<mark style="background: #FFF3A3A6;">Ensure that large environments have a long enough interval for all IP addresses to be probed</mark>. <mark style="background: #ABF7F7A6;">For example, a network with 6,000 users and an interval of 10 minutes would require 10 WMI requests a second from each agent</mark>. These probes are queued and processed by the agent as needed.

<mark style="background: #FF5582A6;">The <strong>NetBIOS probing</strong> is available primarily for backward compatibility with Windows XP and earlier and is not recommended</mark>.

If you enable the optional NetBIOS client probing feature, <mark style="background: #D2B3FFA6;">then the agent requires access through the Windows firewall to port 139</mark>. <mark style="background: #D2B3FFA6;">Windows file and print services also must be enabled</mark>.
![[Client Probing Tab.png]]
### Configure the Monitored Servers 
![[Configure the Monitore Servers.png]]
Select <strong>Discovery</strong> in the left pane to configure the monitored servers and networks.

<mark style="background: #FF5582A6;">The Auto Discover button works only for domain controllers</mark>. 

<mark style="background: #FFF3A3A6;">Use the <strong>Add</strong> button to add <strong>Exchange servers</strong>, <strong>Novell eDirectory servers</strong>, and <strong>syslog senders</strong>, or to manually add domain controllers</mark>. 
<mark style="background: #CACFD9A6;">Click Add to open a separate window, where you are prompted for a server name, server address, and server type</mark>.
### Configure the Firewall to Connect to the Agent
<mark style="background: #FFB86CA6;">The firewall must be configured with information for every User-ID agent to which it will connect</mark>. 
Communication between the firewall and a User-ID agent is secured using an encrypted SSL connection.
![[Configure the Firewall to Connect to the Agent.png]]
##### Agent Host Type
You can add an agent using Serial Number or Host and Port. 
###### Serial Number
If the firewall will connect to a <mark style="background: #FFF3A3A6;"><strong>Panorama management appliance</strong></mark> to collect User-ID information, then select **Serial Number** as the host type.
###### Host and Port
If the firewall will connect to a <mark style="background: #BBFABBA6;"><strong>Windows-based agent</strong> or an agent on another firewall</mark>, then select <strong>Host and Port</strong> as the host type. 

If you select Host and Port, <mark style="background: #ABF7F7A6;">then you must specify each agent’s IP address and listening port</mark>. 

Communication between the firewall and a User-ID agent is secured using an encrypted SSL connection.
##### Non Configurable Timers
The firewall has non-configurable timers for its communication to the agent.
###### 2 Seconds 
<mark style="background: #FFF3A3A6;">Get the list of new IP address-to-username mappings from the agent</mark>. <mark style="background: #D2B3FFA6;">This list contains <strong>only</strong> new mappings since the last interval</mark>.
###### 2 Seconds 
<mark style="background: #FFB86CA6;">Send the list of unknown IP addresses that were encountered in traffic to the agent</mark>.
###### 5 Seconds
Get the agent status.
###### 1 Hour
<mark style="background: #FF5582A6;">Get the full list of IP address-to-username mappings from the agent</mark>.
### Confirm Connection to the User-ID Agent #troubleshooting
To confirm connection to the User-ID agent device, browse to <strong>Device > Data Redistribution > Agents</strong>.

Use the firewall’s web interface and the Windows agent to confirm connectivity between the firewall and the Windows agent. 

Mappings can be displayed from the Windows agent or from the firewall CLI.
![[Confirm Connection to the User-ID Agent.png]]
##### From the Windows Agent
Use the **Monitoring** tab in the Windows agent to display IP address-to-username mappings by the Windows agent.
![[From the Windows Agent.png]]
##### From the Firewall CLI
You can display how users and IP addresses are being mapped on the firewall only by using the firewall’s CLI.

Commonly used commands for checking User-ID mappings include the following:
```
show user user-id-agent statistics
```
```
show user user-ids all
```
```
show user ip-user-mapping all
```
```
show user ip-user-mapping <ip/netmask>
```
![[From the Firewall CLI.png]]
## Data Redistribution 
<mark style="background: #FFF3A3A6;">Every firewall that enforces user-based policies requires user mapping information</mark>. 
In a large-scale network,<mark style="background: #FFB86CA6;"> each firewall would have to directly query all of the mapping information sources to map IP addresses to usernames</mark>. 
<mark style="background: #ABF7F7A6;">With <strong>data redistribution</strong>, you can streamline resource usage by configuring <strong>one</strong> or <strong>more firewalls</strong> <strong>to collect mapping information through redistribution</strong></mark>.

<mark style="background: #FF5582A6;">Redistribution enables you to enforce user-based policies</mark> <mark style="background: #ADCCFFA6;">when users rely on <strong>local sources</strong> for authentication</mark>, such as a regional directory services, <mark style="background: #ADCCFFA6;">but need access to <strong>remote services and applications</strong>, such as a data center application</mark>.

![[Data Redistribution.png]]
In the example, <mark style="background: #FFB86CA6;">the top-layer <strong>Windows-based User-ID agents</strong> are running on <strong>Windows servers</strong> that <u>map IP addresses to usernames</u></mark>. 
<mark style="background: #ABF7F7A6;">A single firewall is connecting to each Windows server to obtain the User-ID mappings</mark>. 
<mark style="background: #BBFABBA6;">Each lower-layer firewall receives the <strong>mapping information and authentication timestamps</strong> from the upper-layer firewall</mark>. 
<mark style="background: #FF5582A6;">Each firewall can receive mapping information and authentication timestamps from up to 100 redistribution points</mark>.
### Configure the Firewall to Connect to the Redistribution Point #configuration 
With data redistribution, <mark style="background: #FFB8EBA6;">you configure the <strong>source</strong> or <strong>redistribution point</strong> the firewall will connect to</mark> and <mark style="background: #ADCCFFA6;">then select the type of information you want it to redistribute</mark>.

<mark style="background: #ABF7F7A6;">You can connect to the source device by using either the serial number or the host and port numbers</mark>. 
<mark style="background: #D2B3FFA6;">The type of information you select can include IP address-to-username mappings, IP address-to-tag mappings, username-to-tag mappings, Host Information Profile HIP data, or quarantined devices</mark>.
![[Redistribution Point.png]]
Optionally, <mark style="background: #FFB8EBA6;">you can configure which networks you want the agent or agents to include in the data redistribution</mark> and <mark style="background: #FFF3A3A6;">which networks you want to exclude from data redistribution</mark>.
![[Redistribution Point 2.png]]
## Configure Group Mapping #configuration 
<mark style="background: #FFB8EBA6;">A <strong>Server Profile</strong> specifies which <strong>LDAP servers</strong> will be contacted, the <strong>order</strong> in which they are contacted, and <strong>how</strong> and <strong>where</strong> to search the <strong>LDAP directory tree</strong></mark>. 
![[Configure Group Mapping.png]]
- Base DN is the point in LDAP tree where the firewall will begin its search for users and groups.
- <mark style="background: #D2B3FFA6;">Bind DN (<strong>cn=paloalto,ou=Users,ou=IT_Services,DC=publiacqua,DC=it</strong>) and password field contains the AD username and its attributes with its password</mark>. <mark style="background: #BBFABBA6;">It's an account that only the firewall will use</mark>. 
- For SSL connection, in the <strong>Server List</strong> use the port <strong>636</strong> and check <strong>SSL secured connection</strong> in the <strong>Server Settings</strong>. 

![[Group Mapping Settings.png]]
Here is where it's possible to configure the Group Mapping settings. 
<mark style="background: #FFB8EBA6;">The group and user objects lists are dynamically populated from the firewall LDAP server profile</mark>. <mark style="background: #BBFABBA6;">By modifying the options in these fields it's possible to search for groups or users in non standard LDAP tree</mark>.

![[User and Group Attributes.png]]
The User and Group Attributes tab is how the firewall identifies the Users and Groups. 

![[Group Include List.png]]
In this tab it's possible to narrow down the list of necessary groups from the LDAP tree.

In the custom group tap it's possible to create custom group based on LDAP filter, it's used when there isn't a AD security group.