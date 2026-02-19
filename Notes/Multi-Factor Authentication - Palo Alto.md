---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
  - "[[Security General]]"
tags:
  - palo_alto/ngfw
  - tobecompleted
created: 2026-02-06T11:59:10+01:00
modified: 2026-02-19T16:54:44+01:00
aliases:
  - MFA
---
![[Multi-Factor Authentication - Palo Alto.png]]
1) Bob attempts to access a web-based resource in the corporate data center
2) Determine whether Bob’s request matches an Authentication policy rule that will require Bob to authenticate. Based on the rule, the firewall could prompt Bob to authenticate using one or more Captive Portal authentication methods, such as a username and password.
3) The Action field of the Authentication policy rule is configured with an authentication enforcement object that specifies the Captive Portal authentication method to use to collect Bob’s credentials. The authentication enforcement object also specifies an Authentication Profile that defines which authentication service to use to verify Bob’s credentials.
4) An Authentication Profile also can define authentication factors to use in addition to the first authentication factor. Other factors include the MFA Phone, SMS, Push, and PIN Code methods described previously in this module.
5) The Authentication Profile also specifies a Server Profile that defines the connection settings to the authentication service. In the example, the Authentication Profile specifies a Server Profile that connects to an LDAP server.
6) The Authentication policy rule invokes MFA to challenge Bob. Bob then enters the additional authentication factor.
7) After Bob has authenticated to the authentication service and any additional MFA challenges, the firewall checks the Security policy to determine whether Bob is authorized to access the web-based resource in the corporate data center. In the example, the Security policy permits Bob’s access and the firewall forwards the traffic to the web server.
# Configuration
