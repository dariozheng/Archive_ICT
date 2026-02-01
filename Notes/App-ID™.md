---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
  - complete
created: 2026-01-30T15:07:03+01:00
modified: 2026-02-01T22:55:46+01:00
aliases:
  - applipedia
---
<mark style="background: #FF5582A6;">App-ID is a <strong>traffic classification system</strong> available only in Palo Alto Networks firewalls</mark>. 

<mark style="background: #FFB8EBA6;">App-ID instantly applies multiple classification mechanisms to the network traffic stream,</mark> as soon as the device sees it, <mark style="background: #FFB8EBA6;">to</mark> accurately <mark style="background: #FFB8EBA6;"><strong>identify applications</strong></mark>. 

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
### Application Signatures
Signatures are used first to l<mark style="background: #FFF3A3A6;">ook for unique application properties</mark> and <mark style="background: #FFF3A3A6;">related transaction characteristics</mark> to <mark style="background: #FFB8EBA6;">correctly identify the application regardless of the protocol and port being used</mark>. 

<mark style="background: #BBFABBA6;">The signature also determines if the application is being used on its default port or it is using a non-standard port</mark>. 
If the identified application is allowed by security policy, further analysis of the traffic is done to identify more granular applications as well as scan for threats,
### SSL and SSH Decryption
 <mark style="background: #ADCCFFA6;">If App-ID determines that SSL encryption is in use and a decryption policy is in place, the traffic is decrypted and then passed to other identification mechanisms as needed</mark>. <mark style="background: #FFB86CA6;">If no policy is in place, then SSL decryption is not employed</mark>. 
 
 Once the application is identified, and deemed acceptable by policy, threat prevention profiles are applied and the traffic is then delivered to its destination. 
 
 A similar approach is used with SSH to determine if port forwarding is in use as a means to tunnel traffic over SSH. Such tunneled traffic is identified as ssh-tunnel and can be controlled via security policy.
### Application and Protocol Decoding
<mark style="background: #ABF7F7A6;">Decoders for known protocols are used to apply additional context-based signatures to detect other applications that may be tunneling inside of the protocol</mark> (e.g., Yahoo! Instant Messenger used across HTTP). 

Decoders validate the traffic conforms to the protocol specification and provide support for NAT traversal and opening dynamic pinholes for applications such as VoIP or FTP. <mark style="background: #FFF3A3A6;">Decoders for popular applications are used to identify the <strong>individual functions</strong> within the application as well</mark> (e.g., webex-file-sharing). 

In addition to identifying applications, <mark style="background: #FFB8EBA6;">decoders also identify files and other content that should be scanned for threats or sensitive data</mark>.
### Heuristics
In certain cases, evasive applications still cannot be detected even through advanced signature and protocol analysis. 

In those situations, <mark style="background: #BBFABBA6;">it is necessary to apply additional heuristic, or behavioral analysis to identify certain applications</mark> such as peer-to-peer file-sharing or VoIP applications that use proprietary encryption.

<mark style="background: #CACFD9A6;">Heuristic analysis is used as needed, with the other App-ID techniques discussed here, to provide visibility into applications that might otherwise elude positive identification</mark>. 

<mark style="background: #FFB8EBA6;">The actual heuristics used are specific to an application and include checks based on such things as the packet length, session rate, packet source, etc</mark>.
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
> An <strong>App-ID filter</strong> is a mechanism that allows you to create a dynamic list of applications that address the required needs. 

![[Application Filter.png]]
<mark style="background: #FFF3A3A6;">If you choose to exclude applications from a specific tag, new content updates will honor those exclusions</mark>.

You can <mark style="background: #ABF7F7A6;">create custom tags</mark> <mark style="background: #BBFABBA6;">to define application types based on your policy requirements</mark>.
# Policy Optimizer
After monitoring the application usage for a while, you can use <mark style="background: #FFB8EBA6;">the Policy Optimizer to choose only applications that have been seen on the firewall and then keep only those applications in the Security policy rule</mark>. 

<mark style="background: #FFF3A3A6;">By using the Policy Optimizer, you can convert a port-based rule to an application-based rule</mark>. 
<mark style="background: #FFB86CA6;">This conversion enables you to include only the applications you want to allow in an allow list and deny access to all other applications</mark>, <mark style="background: #ABF7F7A6;">while restricting application traffic to its default port, preventing an evasive application from running on a nonstandard port</mark>.

The Policy Optimizer provides a simple workflow to migrate your legacy or port-based security policy rulebase to an App-ID-based rulebase. 
### Phase 1
In Phase 1, you identify existing legacy port-based Security policy rules and determine which policy rules to convert and in which order. 

A gradual conversion is safer than migration of a large rulebase at one time and allows you to more easily ensure that new application-based rules control the necessary applications. 

The Policy Optimizer provides sorting options to help you prioritize which rules to convert or clean up.
### Phase 2
In Phase 2, you use the Security Policy’s Policy Optimizer tool to add application-based rules to the Security policy. 

Add each new application-based rule above its corresponding port-based rule. 

The goal is to ensure that traffic matches the application-based rule before it can match the legacy port-based rule. 

Matching of traffic to a specific application reduces your attack surface.
### Phase 3
Phase 3 is the final cleanup of the Security policy. You can review rules and application usage from Policy Optimizer. 
It will provide you app usage statistics, including last time a certain traffic matched this rule. 
If no legitimate traffic has matched a legacy rule, then that legacy rule can be safely removed. 
If traffic has matched a legacy rule, the corresponding application-based rule is updated to match the traffic. 
At the end of Phase 3, you will have removed all or most of the legacy rules, and the attack surface will be minimized.
# App-ID Based Policies
Security policies can specify <mark style="background: #FFB86CA6;">dynamic application filters</mark> t<mark style="background: #FFF3A3A6;">hat apply enforcement to groups of applications</mark> <mark style="background: #BBFABBA6;">that meet a combination of criteria, such as blocking file-sharing peer-to-peer applications or high-risk encrypted-tunnel applications</mark>. 

<mark style="background: #ADCCFFA6;">Dynamic application filters automatically keep your Security rules up to date with new applications that match the criteria</mark>.