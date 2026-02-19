---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-06T12:22:51+01:00
modified: 2026-02-13T11:53:54+01:00
aliases:
  - DUGs
---
<strong>DUGs</strong> control access to resources managed by firewall policies, including the Security policy, Authentication policy, and the Decryption policy.

User membership in a DUG is dynamic. <mark style="background: #FF5582A6;">Only tagged usernames become members of the group</mark>. Changes to group membership do not require a commit. 

<mark style="background: #FFF3A3A6;">When you create a policy rule, you add a DUG to the Source User field as a match criterion</mark>. 
<mark style="background: #FFB86CA6;">You must commit your firewall configuration after you configure a DUG name and add it to a policy rule</mark>. 
<mark style="background: #ABF7F7A6;">However, you do not have to perform a commit when users are added or removed from the DUG</mark>. 
<mark style="background: #FFB8EBA6;">User membership in a DUG is dynamic, and it is controlled by tagging and untagging usernames</mark>.
<mark style="background: #BBFABBA6;">You can manually tag and untag usernames using the web interface</mark>. 
<mark style="background: #ADCCFFA6;">Usernames can also be tagged and untagged by using the auto-tagging feature in a Log Forwarding profile or by programming another utility to invoke PAN-OS XML API commands</mark>.

# Dynamic User Group Operation
DUGs enable you to create a Security policy that provides auto-remediation in response to user behavior and activity.

![[Dynamic User Group Operation.png]]
In the example here, <mark style="background: #FFF3A3A6;">a user’s traffic is recorded in the firewall logs</mark>. 

<mark style="background: #BBFABBA6;">These logs can be analyzed directly on the firewall</mark>, or <mark style="background: #FFB86CA6;">you can configure <strong>log forwarding</strong> to forward the logs to a third-party system for analysis</mark>. 

<mark style="background: #BBFABBA6;">If logs are being analyzed locally on the firewall</mark>, <mark style="background: #ABF7F7A6;">the log forwarding configuration can <u>invoke a new built-in action</u></mark> <mark style="background: #ADCCFFA6;">that will associate a <strong>tag</strong> with a username</mark> <mark style="background: #CACFD9A6;">based on one or more events in a log</mark>. 

<mark style="background: #FFB8EBA6;">A third-party system also can associate a <strong>tag</strong> with a username using the PAN-OS XML API</mark>. 
<mark style="background: #FF5582A6;"><strong>Username-tag registrations</strong> are recorded in and maintained by a User-ID agent</mark>. 

<mark style="background: #D2B3FFA6;">The firewall uses these username-tag pairs to determine which users currently are members of a DUG</mark>. 

<mark style="background: #FFB8EBA6;">When you configure a DUG, you associate it with one or more tags</mark>. <mark style="background: #CACFD9A6;">If a user also is associated with a tag configured in a DUG, then the user becomes a member of the DUG</mark>. 

DUG membership then is used to determine future policy rule matches. 

As examples, a Security policy could block a user, an Authentication policy could force the user to use multi-factor authentication (MFA), or a Decryption policy could force the user’s traffic to be decrypted.