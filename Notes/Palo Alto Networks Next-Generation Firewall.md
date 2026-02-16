---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-16T16:44:40+01:00
modified: 2026-02-16T17:56:12+01:00
---
Palo Alto Networks firewalls are built with a <mark style="background: #FFB8EBA6;">dedicated <strong>out-of-band Ethernet network management interface</strong></mark> labeled <mark style="background: #FFB8EBA6;"><strong>MGT</strong></mark>. 

<mark style="background: #FF5582A6;">This interface passes only management traffic for the firewall and cannot be configured as a standard traffic interface</mark>. 

<mark style="background: #FFB86CA6;">It is used for direct connectivity to the management plane of the firewall</mark>. 

<mark style="background: #FFF3A3A6;">You can configure the firewall to allow <strong>management traffic</strong> over the standard, in-band traffic interfaces</mark>.
# Initial Setup and Configuration for NGFWs #configuration 
You accomplish the initial configuration of the firewall by connecting to the dedicated out-of-band management Ethernet interface (<strong>MGT</strong>) or the serial console port on the firewall. 
The serial console port is an RJ-45 connection on all firewalls. It has default configuration values of <strong>9600-8-N-1</strong>.
![[Perform the Initial Setup and Configuration for NGFWs.pdf]]
# Service Route
<mark style="background: #BBFABBA6;">A <strong>service route</strong> is a path from the <strong>interface</strong> to the <u>service on a server</u></mark>. <mark style="background: #ABF7F7A6;">The <strong>service packets</strong> exit the firewall <u>on the port assigned for the external service</u></mark>, and <mark style="background: #ADCCFFA6;">the <strong>server</strong> responds <u>to the configured source interface and source IP address</u></mark>.
<mark style="background: #D2B3FFA6;">A <strong>service route</strong> enables the firewall to <u>access external services</u> through an <strong>in-band port</strong></mark>.

<mark style="background: #CACFD9A6;">The firewall uses the management (<strong>MGT</strong>) interface by default to access external services</mark>, such as DNS servers, external authentication servers, Palo Alto Networks services such as software, URL updates, licenses and AutoFocus. 

<mark style="background: #FFB8EBA6;">An alternative to using the MGT interface is to configure a <strong>service route</strong> which is a <strong>data port</strong> (a regular interface) to access these services</mark>. 
## Set Up Network Access for External Services #configuration 
![[Set Up Network Access for External Services.pdf]]
## Configure Service Routes #configuration 
![[Configure Service Routes.pdf]]
# Reset to Factory Configuration
## From the CLI with a Known Admin User Password
You can use the CLI operational command: **>** **request system private-data-reset** if you know the admin account password. This method:
- Erases all logs.
- Resets all settings, including IP addressing, which causes loss of connectivity.
- Saves a default configuration after the MGT IP address is changed.
## During Bootup with an Unknown Admin User Password
If you do not know the admin account password, you must first boot the firewall into maintenance mode. 
- As the firewall is booting up, type the operational command **maint** into the CLI through the serial console port. 
- After some time has elapsed, you can choose **Reset to Factory Default** to reset the firewall to its factory default settings. 
- You can set the default admin password or load a previous configuration file if the admin password has been inadvertently changed or an invalid config has been loaded.
#