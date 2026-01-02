---
categories:
  - "[[Security]]"
topic@security:
  - "[[Security General]]"
tags:
aliases:
  - Cyber Attack Lifecycle
created: 2026-01-01T22:39:10+01:00
modified: 2026-01-02T10:21:48+01:00
---
# Phase 1: Reconnaissance

In the first stage of the attack lifecycle, cyber adversaries carefully plan their method of attack. They research, identify, and select targets that will allow them to meet their objectives.

Attackers often gather intelligence through publicly available sources, social media, and corporate websites. 

They scan for vulnerabilities that can be exploited within the target network, its services, and its applications. Then they tighten their focus on perceived weaknesses. 

In this phase, attackers are looking for advantages based on both the human and systems perspective.

___
To prevent attacks at the reconnaissance stage:

- Continuously inspect network traffic flows to detect and prevent port scans and host sweeps.

- Implement security awareness training so that users are mindful about what they should and should not be posting (such as sensitive documents, customer lists, event attendees, job roles/responsibilities, the specific security tools used within an organization, etc.)

# Phase 2: Weaponization and Delivery

In this phase, attackers prepare their toolbox with the tools they need to breach the network. Attackers then determine which methods to use to deliver malicious payloads. 

Some of these methods might be automated tools such as exploit kits, spear phishing attacks with malicious links, attachments, and malvertising.

___
To prevent attacks at weaponization and delivery stage:

- Get full visibility into all traffic, including SSL, firewall high-risk applications, and extend protection to remote and mobile devices

- Block user access to malicious or risky websites through URL filtering

- Block known exploits, malware, and inbound C2 communications using multiple threat prevention disciplines, including IPS, anti-malware, anti-C2, DNS monitoring and sinkholing, and file and content blocking

- Provide ongoing education to users on spear phishing, recognition of unknown email sources, links to risky websites, etc.

# Phase 3: Exploitation

Attackers deploy an exploit or run code against a vulnerable application or system, typically using an exploit kit or weaponized document. 

The internal execution of an exploit initiates the establishment of a reusable entry point into the organization.

___
To prevent attacks at the exploitation stage:

- Block high-risk applications

- Detect unknown malware by equipping security gateways (firewalls) with automated sandboxing solutions

- Automatically deliver new protections globally to thwart follow-up attacks

# Phase 4: Installation

After attackers have established an initial foothold, they then install malware and back doors that enable them to conduct further operations. 

Careful and persistent attackers maintain access for an extended period of time and strategically escalate their network privileges and capabilities.

___
To prevent the many attempts to trick a user or system into executing an exploit, you should take the following measures:

- Prevent malware installation, known or unknown, on the endpoint, network, and cloud services

- Establish secure zones with strictly enforced user access controls and provide ongoing monitoring and inspection of all traffic between zones (using the Zero Trust model)

- Limit local user administrative access

- Train users to identify the signs of a malware infection and know how to follow up if suspicious activity occurs

# Phase 5: Command and Control (C2)

With malware installed, attackers own both sides of the connection. Data passes back and forth between infected devices and the attacker's own external infrastructure, allowing attackers to actively and persistently control the system.

___
To prevent attacks at the command-and-control stage:

- Block outbound C2 communications as well as file and data pattern uploads

- Redirect malicious outbound communication to internal sinkholes to identify and block compromised hosts

- Block outbound communication to known malicious URLs through URL filtering

- Create a database of malicious domains to ensure global awareness and prevention through DNS monitoring

- Limit the attackers’ ability to move laterally with unknown tools and scripts by implementing granular control of applications to allow only authorized applications

# Phase 6: Actions on Objectives

Now that attackers have control points, persistent regeneration capabilities, and ongoing communication, they act upon their goals. 

Specific goals could be exfiltrating data, destroying critical infrastructure, defacing web property, generating fear, or establishing the means for extortion.

___

To prevent attacks at the act-on-objective stage:

- Proactively hunt for indicators of compromise on the network using threat intelligence tools

- Build bridges between the Security Operations Center (SOC) and the Network Operations Center (NOC) to put the right prevention-based controls in place

- Monitor and inspect all traffic between zones and enforce user access controls for secure zones

- Block outbound C2 communications, as well as file and data pattern uploads

- Block outbound communication to known malicious URLs through URL filtering

- Implement granular control of applications and user control to enforce file-transfer and application policies to limit the attackers’ ability to move laterally with unknown tools and scripts