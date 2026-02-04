---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
  - complete
created: 2026-01-30T15:07:03+01:00
modified: 2026-02-04T22:59:09+01:00
aliases:
  - applipedia
---
<mark style="background: #FF5582A6;">App-ID is a <strong>traffic classification system</strong> available only in Palo Alto Networks firewalls</mark>. 

<mark style="background: #FFB8EBA6;">App-ID instantly applies multiple classification mechanisms to the network traffic stream,</mark> as soon as the device sees it, <mark style="background: #FFB8EBA6;">to</mark> accurately <mark style="background: #FFB8EBA6;"><strong>identify applications</strong></mark>. 

> [!info] Application
> In Palo Alto Networks terms, an application is a specific program or feature whose communication can be labeled, monitored, and controlled. 

<mark style="background: #FFB86CA6;">App-ID</mark> uses four identification techniques to <mark style="background: #FFB86CA6;">determine the exact identity of applications</mark> traversing the network, <mark style="background: #FFF3A3A6;"><strong>regardless</strong> of port, protocol, evasive tactic, or SSL encryption</mark>. 

<mark style="background: #D2B3FFA6;">App-ID provides <strong>visibility</strong> and <strong>control</strong> over applications that can <strong>evade</strong> detection</mark> by masquerading as legitimate traffic, hopping ports or sneaking through the firewall using encryption (SSL and SSH).

<mark style="background: #BBFABBA6;">App-ID can identify</mark> not only a particular application, but also <mark style="background: #BBFABBA6;">some of the specific operations of an application</mark>. <mark style="background: #ABF7F7A6;">For example, there are granular App-IDs for Dropbox that can be used to <strong>allow</strong> downloading of a file or the ability to edit a document but will <strong>block</strong> files from being uploaded</mark>.
![[App-ID dropbox.png]]
When used in conjunction with User-ID™, you can see exactly who is using the application based on their identity, not just an IP address. 

![[App-ID application.png]]
# App-ID Traffic Classification Technology

![[App-ID classification.png]]
- Traffic is first classified based on the IP address and port.
- <strong>Signatures</strong> are then applied to allowed traffic to identify the application based on unique application properties and related transaction characteristics.
- If App-ID determines that encryption (SSL or SSH) is in use, and a decryption policy is in place, the application is decrypted and application signatures are applied again on the decrypted flow.
- Decoders for known protocols are then used to apply additional context-based signatures to detect other applications that may be tunneling inside of the protocol.
- For applications that are particularly evasive and cannot be identified through advanced signature and protocol analysis, heuristics or behavioral analysis may be used to determine the identity of the application.
## Application Signatures
Signatures are used first to <mark style="background: #FFF3A3A6;">look for unique application properties</mark> and <mark style="background: #FFF3A3A6;">related transaction characteristics</mark> to <mark style="background: #FFB8EBA6;">correctly identify the application regardless of the protocol and port being used</mark>. 

<mark style="background: #BBFABBA6;">The signature also determines if the application is being used on its default port or it is using a non-standard port</mark>. 
If the identified application is allowed by security policy, further analysis of the traffic is done to identify more granular applications as well as scan for threats,
## SSL and SSH Decryption
 <mark style="background: #ADCCFFA6;">If App-ID determines that SSL encryption is in use and a decryption policy is in place, the traffic is decrypted and then passed to other identification mechanisms as needed</mark>. <mark style="background: #FFB86CA6;">If no policy is in place, then SSL decryption is not employed</mark>. 
 
 A similar approach is used with SSH to determine if port forwarding is in use as a means to tunnel traffic over SSH. Such tunneled traffic is identified as ssh-tunnel and can be controlled via security policy.
## Application and Protocol Decoding
<mark style="background: #ABF7F7A6;">Decoders for known protocols are used to apply additional context-based signatures to detect other applications that may be tunneling inside of the protocol</mark> (e.g., Yahoo! Instant Messenger used across HTTP). 

Decoders validate that the traffic conforms to the protocol specification and provide support for NAT traversal and opening dynamic pinholes for applications such as VoIP or FTP. <mark style="background: #FFF3A3A6;">Decoders for popular applications are used to identify the <strong>individual functions</strong> within the application as well</mark> (e.g., webex-file-sharing). 

In addition to identifying applications, <mark style="background: #FFB8EBA6;">decoders also identify files and other content that should be scanned for threats or sensitive data</mark>.
## Heuristics
In certain cases, evasive applications still cannot be detected even through advanced signature and protocol analysis. 

In those situations, <mark style="background: #BBFABBA6;">it is necessary to apply additional heuristic, or behavioral analysis to identify certain applications</mark> such as peer-to-peer file-sharing or VoIP applications that use proprietary encryption.

<mark style="background: #CACFD9A6;">Heuristic analysis is used as needed, with the other App-ID techniques discussed here, to provide visibility into applications that might otherwise elude positive identification</mark>. 

<mark style="background: #FFB8EBA6;">The actual heuristics used are specific to an application and include checks based on such things as the packet length, session rate, packet source, etc</mark>.
## Application Shift
<mark style="background: #ADCCFFA6;">Even after App-ID initially has identified an application</mark>, <mark style="background: #D2B3FFA6;">App-ID continues to use the protocol decoders to determine whether the original application has <strong>shifted</strong> to a new application</mark>. 

<mark style="background: #FFB8EBA6;">Decoders for known protocols use additional context-based signatures to detect other applications that might be tunneling inside of the protocol</mark>. 
For example, Yahoo! Instant Messenger can be carried in the HTTP protocol. 

If an application shift is detected, the firewall checks the Security policy again to determine what to do with the traffic.![[App shift.gif]]
### Dependent Applications 
<mark style="background: #BBFABBA6;">Some applications are dependent on one or more other applications</mark>. 
Also, <mark style="background: #ABF7F7A6;">network traffic can shift from one application to another during the lifetime of a session</mark>. 
![[Dependent Applications.png]]
For these reasons, when you create a policy to allow applications, you also <mark style="background: #FFB8EBA6;">ensure that the firewall allows the other applications on which the application depends</mark>.

<mark style="background: #BBFABBA6;">When a policy is created with unresolved dependencies they will be reported after a commit</mark>. Then it's possible to correct the policies, adding the missing dependencies in the policy rule. 
![[Unresolved dependencies.png]]
# Applipedia 
https://applipedia.paloaltonetworks.com

<mark style="background: #FFF3A3A6;"><strong>Applipedia</strong> is the application database that Palo Alto Networks uses along with App-ID to identify applications traveling through your Palo Alto Networks firewall</mark>. 

The application data listed in Applipedia can be used to help determine what applications to allow through the firewall.

Other popular use cases for using applipedia is to search if a particular App-ID is supported or to investigate application characteristics, classification, and dependencies. 

Application data includes the Application Name, Description, Additional Information, Standard Ports, Depends on Applications, and Implicitly Use Applications.
# Dynamic Updates
Palo Alto Networks provides <strong>Applications and Threats</strong> <mark style="background: #FFF3A3A6;">content updates</mark> <mark style="background: #ADCCFFA6;">that contain new application and threat signatures developed by Palo Alto Networks</mark>.

Under <strong>Device > Dynamic Updates</strong> it's possible to view a list of the new and modified App-IDs that the update includes.

<mark style="background: #FFB86CA6;"><strong>The Applications and Threats</strong> section lists</mark> <mark style="background: #FF5582A6;">updates to applications, threats, and other content that includes <strong>decoders</strong>, <strong>signatures</strong>, and <strong>modified or new App-IDs</strong></mark>. New App-IDs are updated once a month (every third Tuesday), while other content can be updated more frequently. You can click the hyperlink next to **Schedule** to set timely (weekly) updates.
![[PaloAlto Dynamic Updates.png]]
# App-ID Tags 
<mark style="background: #FFF3A3A6;">App-ID tags is a mechanisms that helps to navigate among the <strong>numerous</strong> APP-IDs</mark>. <mark style="background: #D2B3FFA6;">They are used to organize and classify applications so that they can be referenced in security policy, QoS, decryption or logging</mark>.

> [!info] App-ID tags
> App-ID tags are <strong>labels</strong> used to group applications.

<mark style="background: #BBFABBA6;">Tags allow you to easily choose all existent and future App-IDs related to <strong>one or more specific characteristics</strong></mark>.

<mark style="background: #ADCCFFA6;">Palo Alto Networks takes on the task of researching <strong>applications with common attributes</strong></mark> and <mark style="background: #FFF3A3A6;">delivers the results of this research through <strong>tags</strong></mark> <mark style="background: #ABF7F7A6;">in dynamic content updates</mark>.
![[App-ID tags.png]]

<mark style="background: #ADCCFFA6;">The firewall can use a <strong>tag-based application filter</strong> to dynamically enforce new and updated existing App-IDs</mark> <mark style="background: #FFB86CA6;"><strong>without</strong> requiring you to review or update policy rules whenever new applications are added</mark>.

> [!info] App-ID filter
> An <strong>App-ID filter</strong> is a mechanism that allows you to create a dynamic list of applications based on application attributes that you select from the App-ID database. 
> The selectable attributes are <strong>Category</strong>, <strong>Subcategory</strong>, <strong>Risk</strong>, <strong>Tags</strong>, and <strong>Characteristic</strong>. 

![[Application Filter.png]]
<mark style="background: #FFF3A3A6;">If you choose to exclude applications from a specific tag, new content updates will honor those exclusions</mark>.
## Custom tags
You can <mark style="background: #ABF7F7A6;">create custom tags</mark> <mark style="background: #BBFABBA6;">to define application types based on your policy requirements</mark>.
![[custom tag panorama.png]]
![[custom tag panorama 2.png]]
![[custom tag panorama 3.png]]
<mark style="background: #FF5582A6;">Now all new application which will have the TAI tags will be automatically added to this Application Filter.</mark>
# Policy Optimizer
After monitoring the application usage for a while, you can use <mark style="background: #FFB8EBA6;">the Policy Optimizer to choose only applications that have been seen on the firewall and then keep only those applications in the Security policy rule</mark>. 

<mark style="background: #FFF3A3A6;">By using the Policy Optimizer, you can convert a port-based rule to an application-based rule</mark>. 
<mark style="background: #FFB86CA6;">This conversion enables you to include only the applications you want to allow in an allow list and deny access to all other applications</mark>, <mark style="background: #ABF7F7A6;">while restricting application traffic to its default port, preventing an evasive application from running on a nonstandard port</mark>.

The Policy Optimizer provides a simple workflow to migrate your legacy or port-based security policy rulebase to an App-ID-based rulebase. 
### Phase 1
In Phase 1, you <mark style="background: #FFF3A3A6;">identify existing legacy port-based Security policy rules and determine which policy rules to convert and in which order</mark>. 

A gradual conversion is safer than migration of a large rulebase at one time and allows you to more easily ensure that new application-based rules control the necessary applications. 

The Policy Optimizer provides sorting options to help you prioritize which rules to convert or clean up.
### Phase 2
In Phase 2, you <mark style="background: #FFF3A3A6;">use the Security Policy’s Policy Optimizer tool to add application-based rules to the Security policy</mark>. 

<mark style="background: #FFF3A3A6;">Add each new application-based rule above its corresponding port-based rule</mark>. 

<mark style="background: #FFF3A3A6;">The goal is to ensure that traffic matches the application-based rule before it can match the legacy port-based rule</mark>. 

Matching of traffic to a specific application reduces your attack surface.
### Phase 3
Phase 3 is the final cleanup of the Security policy. You can <mark style="background: #FFF3A3A6;">review rules and application usage from Policy Optimizer</mark>. 
<mark style="background: #FFF3A3A6;">It will provide you app usage statistics, including last time a certain traffic matched this rule</mark>. 
<mark style="background: #FFF3A3A6;">If no legitimate traffic has matched a legacy rule, then that legacy rule can be safely removed</mark>. 
<mark style="background: #FFF3A3A6;">If traffic has matched a legacy rule, the corresponding application-based rule is updated to match the traffic</mark>. 
At the end of Phase 3, you will have removed all or most of the legacy rules, and the attack surface will be minimized.
# App-ID Based Policies
Security policies can specify <mark style="background: #FFB86CA6;">dynamic application filters</mark> <mark style="background: #FFF3A3A6;">that apply enforcement to groups of applications</mark> <mark style="background: #BBFABBA6;">that meet a combination of criteria, such as blocking file-sharing peer-to-peer applications or high-risk encrypted-tunnel applications</mark>. 

<mark style="background: #ADCCFFA6;">Dynamic application filters automatically keep your Security rules up to date with new applications that match the criteria</mark>.
# App-ID Identification Operation 
## App-ID and TCP
<mark style="background: #FFB86CA6;">Applications that use Transmission Control Protocol (TCP) usually require multiple packet transfers to identify an application</mark>. 

HTTP web request example:
![[http connection request workflow.png]]
 <mark style="background: #FFF3A3A6;">The first packet is a TCP SYN packet</mark>. Though <mark style="background: #FFB8EBA6;">the first packet does contain the source and destination addresses and ports</mark>, <mark style="background: #FF5582A6;">it contains no application data</mark>. In fact, <mark style="background: #ABF7F7A6;">the next two packets just complete the required TCP three-way handshake and do not contain any application data</mark>.
 ![[TCP three-way handshake.png]]
  ![[TCP packet summary.png]]

<mark style="background: #FFF3A3A6;">The application data could reside in either the client’s HTTP GET request or in the server’s reply</mark>. 
For this reason, <mark style="background: #BBFABBA6;">the firewall might have to examine the fifth packet, for example, before App-ID can detect either the application or the presence of encrypted traffic</mark>.

If the traffic is encrypted, the firewall must evaluate the administrator-defined Decryption policy to determine what to do next. 

Depending on the configured policy, the traffic could be allowed or blocked in either encrypted or decrypted form. 
![[App data.png]]
## App-ID and UDP
A Palo Alto Networks firewall examining User Datagram Protocol (UDP) packets must often <mark style="background: #FF5582A6;">examine only a single UDP packet to identify the application</mark>. <mark style="background: #FFF3A3A6;">In most cases, all the information that the firewall needs is contained in the first packet</mark>: source and destination IP address, source and destination ports and the application data. 
![[udp Src and Dst Address.png]]
![[udp Src and Dst Port.png]]
![[udp Application Data.png]]
# Application Labels
<mark style="background: #FFF3A3A6;">App-ID labels traffic observed by the firewall</mark>. The label is displayed in various logs and reports as an application name.
## Labeling TCP Traffic 
App-ID labels the TCP traffic seen by the firewall. 
If enough packets are received for App-ID to identify the application, then App-ID assigns an application label such as gmail-base. 
![[APP-ID labeling TCP.png]]
If App-ID cannot identify the application, then it assigns labels such as <strong>not-applicable</strong>, <strong>incomplete</strong>, <strong>insufficient-data</strong>, <strong>unknown-tcp</strong>, or <strong>unknown-p2p</strong>.
### not-applicable 
App-ID labels traffic as not-applicable when <mark style="background: #FFB86CA6;">the firewall discards the traffic because the Security policy does not allow it</mark>. 

For example, <mark style="background: #ABF7F7A6;">if a Security policy allows HTTP traffic on only TCP port 80 but the traffic arrives on a different port, then the firewall blocks the traffic and App-ID assigns the label not-applicable in logs and reports</mark>.
### incomplete
App-ID labels traffic as incomplete when either the <mark style="background: #BBFABBA6;">three-way TCP handshake does not complete</mark> or <mark style="background: #D2B3FFA6;">when the handshake completes but no data follows the handshake</mark>. <mark style="background: #ADCCFFA6;">Traffic labeled as incomplete by App-ID is not really an application</mark>.
### insufficient-data
App-ID labels the traffic as insufficient-data when <mark style="background: #FFB8EBA6;">not enough data is received in the payload to identify the application</mark>. In this case, the three-way TCP handshake completes, but not enough data follows the handshake to identify the traffic.
### ‹application_name> or unknown-tcp or unknown-p2p
App-ID labels the traffic as <strong>unknown-tcp</strong> when <mark style="background: #ABF7F7A6;">the three-way TCP handshake is complete and data is flowing, but App-ID cannot identify the application</mark>.

App-ID labels the traffic as <strong>unknown-p2p</strong> when <mark style="background: #BBFABBA6;">App-ID cannot match the traffic to a specific application, but the traffic exhibits generic peer-to-peer behavior</mark>. 

An unknown-tcp or unknown-p2p label <mark style="background: #ADCCFFA6;">could be the result of an internally developed application, commercial application, or malware for which the firewall has no signature</mark>.
## Labeling UDP Traffic
App-ID labels the UDP traffic seen by the firewall. 

It assigns an application label such as dns or call-of-duty when the application is recognized. 

In cases where App-ID cannot recognize the application, labels like unknown-udp or unknown-p2p are assigned.
![[APP-ID labeling UDP.png]]
### not-applicable 
App-ID labels the traffic as not-applicable when <mark style="background: #FFF3A3A6;">the firewall discards the traffic because the Security policy does not allow it</mark>. 

For example, if a Security policy does not allow Network Time Protocol (NTP) but traffic to port 123 is detected, then the firewall blocks the traffic, and App-ID assigns the label not-applicable in logs and reports.
### <application_name> or unknown-udp or unknown-p2p
App-ID labels the traffic as <strong>unknown-udp</strong> when <mark style="background: #ABF7F7A6;">App-ID cannot identify the application</mark>.

App-ID labels the traffic as <strong>unknown-p2p</strong> when <mark style="background: #FFB86CA6;">App-ID cannot match the UDP traffic to a specific application, but the traffic exhibits generic peer-to-peer behavior</mark>.

An unknown-udp or unknown-p2p label could be the result of an internally developed application, commercial application, or malware for which the firewall has no signature.
# Applications​ Known and Unknown
Applications can be divided into two main categories: <mark style="background: #FFB8EBA6;">applications <strong>known</strong> to App-ID</mark> and <mark style="background: #ADCCFFA6;">applications <strong>unknown</strong> to App-ID</mark>. 

Applications known to App-ID are labeled in the Traffic log and reports.

![[flowchart unknown APP.png]]
<mark style="background: #FFB8EBA6;">Applications unknown to App-ID initially might be identified as <strong>generic ssl</strong> if HTTPS is detected</mark>. 

If you have configured the firewall to decrypt the traffic, then <mark style="background: #FFF3A3A6;">App-ID might be able to further identify the decrypted traffic as a specific application</mark>. 

<mark style="background: #ABF7F7A6;">If HTTP is detected rather than HTTPS, then applications unknown to App-ID initially might be identified as generic web-browsing</mark>. 

<mark style="background: #BBFABBA6;">As more packet data becomes available, then App-ID might be able to further identify the generic web-browsing application as something more specific</mark>. 
For example, web-browsing might be further identified as google-docs-base. 

<mark style="background: #FF5582A6;">When App-ID cannot identify an application or label the traffic as generic web-browsing,</mark> then App-ID labels the traffic as <strong>unknown-tcp</strong>, <strong>unknown-udp</strong>, or <strong>unknown-p2p</strong>.
## Unknown Applications​
The firewall has at least three methods available for processing traffic identified only as unknown-tcp, unknown-udp, unknown-p2p, or web-browsing.

![[flowchart control unknown app.png]]
### Block Application 
Control unknown applications by blocking unknown-tcp, unknown-udp, or unknown-p2p traffic in the Security policy.
### Custom Application 
Create a custom application rather than block unknown traffic. 

First, <mark style="background: #FF5582A6;">use a network packet capture to identify unique bit patterns in the application</mark>. 

Next, <mark style="background: #BBFABBA6;">create a custom application signature to match that bit pattern and then name the new custom application</mark>. 

Last, <mark style="background: #ADCCFFA6;">use the custom application in a Security, QoS, or PBF policy rule just like you use the Palo Alto Networks predefined applications</mark>.
### Application Override
Create an Application Override policy rule. 

For example, if you need to control a custom application, <mark style="background: #FFF3A3A6;">an Application Override policy rule can be used</mark> <mark style="background: #BBFABBA6;">to identify traffic for that application</mark> <mark style="background: #ABF7F7A6;">based on its source zone and IP address, its destination zone and IP address, and its port and protocol</mark>. 

You must create a Security policy rule to allow the application to traverse between firewall security zones.
# Implicit Applications 
For many applications, <mark style="background: #FFB86CA6;">the App-ID database implicitly allows the required parent application without the need for you to explicitly add the parent application to the Security policy</mark>.
## Implicit Dependencies 
<mark style="background: #FF5582A6;">App-ID defines implicit dependencies because <strong>the addition of parent applications</strong> to a rule in the Security policy <strong>could allow more traffic than intended</strong></mark>. 
For example, enablement of web-browsing just to allow facebook-base would allow users to browse other websites.

It's possible to check the implicit dependencies on the Application details or on the Applipedia. 
![[Implicitly Uses.png]]
## Implicit Permissions
<mark style="background: #ADCCFFA6;">Implicit permissions for a parent application are processed only if you have <strong>not</strong> added an explicit Security policy rule for the parent application</mark>. 
This implicit support also applies to administrator-defined custom applications that are based on HTTP, SSL, MS-RPC, or RTSP.

![[Implicit permission example.png]]
In the example, <mark style="background: #FFF3A3A6;">the facebook-base application<strong> implicitly allows</strong> the required web-browsing application without the need for you to explicitly add a web-browsing rule to the Security policy</mark>. 
<mark style="background: #CACFD9A6;">The facebook-chat and facebook-apps applications depend on facebook-base, so facebook-base <strong>explicitly must be added to the rules</strong> to enable users to chat or email using Facebook</mark>. 
# Application Ports
## application-default
<mark style="background: #FFB8EBA6;">The <strong>application-default</strong> service setting in a <strong>policy rule</strong> enabled the applications <strong>only</strong> on their APP-ID-defined standard ports</mark> and, in some cases, for the <mark style="background: #ABF7F7A6;">SSL-encrypted applications, their <strong>default SSL secure ports</strong> in addition to the application's <strong>standard ports</strong></mark>. 

<mark style="background: #FFF3A3A6;">For a cleartext session, application-default matches against the Standard Ports for the application</mark>. 

<mark style="background: #FFB86CA6;">For an encrypted session, application-default matches against the Secure Ports for the application</mark>. 

For example, a Security policy designed to allow web-browsing on only the application-default ports now will allow cleartext web-browsing traffic on the standard TCP port 80 and SSL-encrypted web-browsing traffic on the secure TCP port 443.

<mark style="background: #D2B3FFA6;">The <strong>application-default</strong> setting for both standard and secure ports is supported for the applications web-browsing, SMTP, FTP, LDAP, POP3, and IMAP</mark>. <mark style="background: #BBFABBA6;">For any of these applications, you can view the Standard Ports and Secure Ports that Palo Alto Networks has defined for the application by navigating to <strong>Objects > Applications</strong></mark>.
![[default ports for APP-ID.png]]
## Control Applications Ports
Malicious traffic often uses non-standard application ports to try to evade network security features. 
<mark style="background: #FFB86CA6;">To block applications not running on standard ports, select the value <strong>application-default</strong> in the <strong>Service</strong> column in your<strong> Security policy</strong></mark>. <mark style="background: #FF5582A6;">Linking the application to their default ports defined in the Palo Alto Networks APP-ID database</mark>.
![[application-default.png]]
<mark style="background: #BBFABBA6;">The <strong>any</strong> option will allow any ports to go through</mark>. 
<mark style="background: #ADCCFFA6;">While the <strong>select</strong> option requires the creation of specific port on the <strong>Objects>Services</strong>, where it's possible to define the a number of ports which will be linked to the applications in the Policies rulebase</mark>.
![[Panorama Services.png]]
# ​Identify Applications in SSL Traffic​
When an SSL/TLS client connects to a secure web server, the application layer data is encrypted. But, if configured, the firewall can decrypt the SSL/TLS traffic. 

<mark style="background: #CACFD9A6;">App-ID cannot use <strong>signatures</strong> and <strong>decoders</strong> to identify applications in encrypted traffic</mark>. However, the firewall can attempt to identify the encrypted application using two other methods. 

<mark style="background: #FFB8EBA6;">The first method relies on the Common Name field in a certificate, which typically contains either the FQDN of the server or its IP address</mark>. 

<mark style="background: #ABF7F7A6;">The second method relies on a TLS protocol extension named <strong>Server Name Indication</strong> (<strong>SNI</strong>) that enables multiple hostnames to be served over HTTPS from the same IP address</mark>.
## Encrypted SSL Traffic - Single Site
![[ssl traffic decrypt 2.png]]
<mark style="background: #ADCCFFA6;">If a web server hosts only a single website, then the Common Name (or CN) is used to identify the application</mark>. <mark style="background: #FFB86CA6;">The SSL client initiates an SSL/TLS connection to the web server and requests access to the website</mark>. <mark style="background: #D2B3FFA6;">The web server responds with its certificate</mark>. <mark style="background: #FF5582A6;">The firewall uses the FQDN in the CN field to attempt to identify the application</mark>. 

In the example, <mark style="background: #FFF3A3A6;">the SSL client initiates a connection to www.twitter.com. The web server certificate, which includes the Common Name www.twitter.com, is used to identify the application as Twitter</mark>.
## Encrypted SSL Traffic - Multiple Sites
![[ssl traffic decrypt 3.png]]
The requirement that every website have its own unique FQDN and IP address is not practical, so many web servers host multiple websites. The CN field of a certificate cannot be used to identify the application, because multiple web-based applications share a common FQDN and IP address. Instead, <mark style="background: #FF5582A6;">the firewall can use SNI to attempt to identify the application</mark>. 

During the TLS handshake, <mark style="background: #FFB8EBA6;">browsers and applications use <strong>SNI</strong> to send the web server the FQDN of the website to which they want to connect</mark>. <mark style="background: #BBFABBA6;">The firewall reads the SNI field and attempts to use the FQDN in the SNI to identify the application</mark>. <mark style="background: #ABF7F7A6;">The web server reads the SNI field to determine which certificate to send back to the client to verify the identity of the website</mark>. 

In the example, <mark style="background: #FFF3A3A6;">the SSL client initiates a connection to www.app2.com and includes www.app2.com in the SNI field. The firewall uses the SNI information to identify the application</mark>.

<mark style="background: #FFB8EBA6;">If the firewall cannot identify the traffic using either the CN field in the certificate or the SNI field in the TLS handshake, then the traffic is identified generically as SSL</mark>.
# Application Block Page​
<mark style="background: #FF5582A6;">If the <strong>Application Block Page</strong> is enabled</mark> and <mark style="background: #FFB86CA6;">a Security policy rule denies a web-based application</mark>, <mark style="background: #ADCCFFA6;">then a browser-based response page is displayed</mark>. 

<mark style="background: #ABF7F7A6;">The default response page includes the prohibited application name and the user’s name if the User-ID feature has been configured</mark>.
<mark style="background: #D2B3FFA6;">If User-ID has not been configured, then the user’s name appears as an IP address</mark>. 

<mark style="background: #FFB8EBA6;">Application block response pages must be enabled using an <strong>Interface Management Profile</strong></mark>. 

The generic response page might result in additional support calls if users do not correctly interpret the message. <mark style="background: #BBFABBA6;">You can create and upload a custom HTML response page</mark>.
![[Application Block Page.gif]]
# Application Group
<mark style="background: #FFF3A3A6;"><strong>Application group</strong> is a static, administrator-defined set of applications</mark>. 

<mark style="background: #ABF7F7A6;">Application groups enable you to create a logical grouping of applications that can be applied to Security and QoS policy rules</mark>.
An Application group is used when you want to treat a set of applications similarly in a policy. 
Instead of you adding the same list of applications to multiple rules, you can create an application group and add the group to multiple rules.
