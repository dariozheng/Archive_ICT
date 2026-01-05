---
categories:
  - "[[Security]]"
topic@security:
  - "[[Security General]]"
tags:
created: 2025-12-31T16:46:31+01:00
modified: 2026-01-04T21:20:38+01:00
---
Security groups <mark style="background: #BBFABBA6;">define the network traffic that should be <strong>explicitly</strong> <strong>permitted</strong></mark> and <mark style="background: #ABF7F7A6;">deny any traffic that is not explicitly permitted</mark>. 

<mark style="background: #FFB8EBA6;">A security group is attached to an [[Cloud Computing Glossary#instance network interface|instance network interface]] not to the VM itself</mark>, and <mark style="background: #FFB86CA6;">it has separate <strong>inbound</strong> and <strong>outbound</strong> policies</mark>.

Security groups are <strong>stateful</strong>, meaning that <mark style="background: #ABF7F7A6;">they also permit return traffic associated with permitted rules</mark>. 

Security groups can control traffic on any protocol that has a standard protocol number. 

<mark style="background: #FF5582A6;">A VM-Series firewall in the traffic path is required to enforce traffic at the application layer</mark>. 

When <mark style="background: #FFF3A3A6;">you deploy a new security group, the default setting contains no inbound rule, and the outbound rule permits all traffic</mark>. <mark style="background: #BBFABBA6;">The effect of this default is to permit all outbound network traffic originating from your instance and its associated return traffic, and to deny external traffic that is inbound to an instance.</mark>

Security groups:
- Apply to the instance network interface
- Allow action rules only—there is no explicit deny action
- Have separate inbound and outbound policies
- Are stateful—return traffic associated with permitted traffic is also permitted
- Have order-dependent rules
- Enforce at Layer 3 and Layer 4 (standard protocol port numbers)