---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/panorama
created: 2026-01-04T21:40:31+01:00
modified: 2026-01-04T22:57:33+01:00
---
Palo Alto Networks Panorama provides an intuitive user interface (UI) that can be used to configure, monitor, and automate network security management with <mark style="background: #FFB8EBA6;">a centralized network security management solution for all Palo Alto Networks firewalls</mark> and <mark style="background: #FFF3A3A6;">centralized visibility and comprehensive insights into their network traffic, logs, and threats</mark>. 
![[Panorama Overview.png]]
The following are three key characteristics of Panorama: 

 - <strong>Capability to Manage Firewalls Anywhere</strong>: You can use Panorama to manage all firewalls irrespective of where they are: at the perimeter, in a data center, or the cloud.
 - <strong>Combines Everything Into a Single Platform</strong>: Panorama can scale to be a single pane of glass for tens of thousands of firewalls.
 - <strong>Can Be a Virtual or Physical Appliance</strong>: Panorama can be deployed as a virtual or physical appliance or both.

Panorama can simplify centralized management and rapid deployment of next-generation firewalls (NGFWs) throughout your network infrastructure by <mark style="background: #FFF3A3A6;">enabling firewall pre-staging</mark>.
<mark style="background: #D2B3FFA6;">Firewalls can be grouped</mark>. <mark style="background: #FFB86CA6;">Templates enable you to apply a base network and device configuration to these groups of firewalls</mark>. <mark style="background: #ADCCFFA6;">Firewall device groups</mark> enable <mark style="background: #BBFABBA6;">centralized administration of both globally shared and local policy rules</mark>.

The Panorama web-based user interface lets you switch between Panorama-centric and firewall-centric views using the Context menu at the top left of each tab.
You can set the Context to Panorama for centralized firewall management or switch the web interface to configure a firewall individually. Note the following about context switching:
- <strong>Context Menu</strong>: The Context drop-down menu lists only the firewalls that are connected to Panorama. For device groups and template administrator, the menu will only list the connected firewalls within the access domains assigned to that administrator. You can use the filters within the drop-down menu to search for a specific firewall.
- <strong>High Availability Configurations</strong>: For firewalls in a high availability (HA) configuration, icons are displayed with colored backgrounds to indicate the HA state. Knowing the HA state is useful when selecting a firewall context. For example, you generally make firewall-specific configuration changes on an active firewall.
# The Application Command Center

Panorama allows you to access logs and generate aggregated reports from various sources, such as logs forwarded to Cortex Data Lake, Panorama, managed log collectors, or through direct queries to managed firewalls. 

You can also generate traffic, threat, and user activity reports across your network infrastructure using locally stored and forwarded logs.

Panorama aggregates logs from all managed firewalls, offering a comprehensive view of network traffic. Additionally, it maintains an audit trail for all policy modifications and configuration changes to the managed firewalls.

In addition to log aggregation, Panorama can forward logs as Simple Network Management Protocol (SNMP) traps, email notifications, Syslog messages, and Hypertext Transfer Protocol (HTTP) payloads to an external server.