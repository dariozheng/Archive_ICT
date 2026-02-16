---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-16T16:44:40+01:00
modified: 2026-02-16T16:58:42+01:00
---
Palo Alto Networks firewalls are built with a <mark style="background: #FFB8EBA6;">dedicated <strong>out-of-band Ethernet network management interface</strong></mark> labeled <mark style="background: #FFB8EBA6;"><strong>MGT</strong></mark>. 

<mark style="background: #FF5582A6;">This interface passes only management traffic for the firewall and cannot be configured as a standard traffic interface</mark>. 

<mark style="background: #FFB86CA6;">It is used for direct connectivity to the management plane of the firewall</mark>. 

<mark style="background: #FFF3A3A6;">You can configure the firewall to allow <strong>management traffic</strong> over the standard, in-band traffic interfaces</mark>.
# Initial Access to the Firewall
Default MGT IP Addressing:
- For the PA-Series firewall models, the MGT port has a factory default IP address of 192.168.1.1/24. 
- For VM-Series firewalls, the MGT port is configured as a DHCP client. 
- You can also configure the MGT port of any firewall model to use DHCP.

You accomplish the initial configuration of the firewall by connecting to the dedicated out-of-band management Ethernet interface (<strong>MGT</strong>) or the serial console port on the firewall. 
The serial console port is an RJ-45 connection on all firewalls. It has default configuration values of <strong>9600-8-N-1</strong>.

The factory default for each firewall is to have a single administrative account named '<strong>admin</strong>' with a password of '<strong>admin</strong>'. 

Once you have successfully logged on to the firewall, the firewall will require you to change the predefined admin account password at first login. 

<mark style="background: #FFB8EBA6;">The local admin password is stored in the firewall’s XML configuration file but is encrypted using the firewall’s master key</mark>.
#