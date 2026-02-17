---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
  - ngfw
created: 2026-02-16T16:44:40+01:00
modified: 2026-02-17T14:20:01+01:00
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
## During boot up with an Unknown Admin User Password
If you do not know the admin account password, you must first boot the firewall into maintenance mode. 
- As the firewall is booting up, type the operational command **maint** into the CLI through the serial console port. 
- After some time has elapsed, you can choose **Reset to Factory Default** to reset the firewall to its factory default settings. 
- You can set the default admin password or load a previous configuration file if the admin password has been inadvertently changed or an invalid config has been loaded.
# Activation, Licensing and Software
Before you can start using your firewall to secure the traffic on your network, you must <mark style="background: #D2B3FFA6;">register</mark> your firewall with Palo Alto Networks, <mark style="background: #D2B3FFA6;">activate your support license</mark>, and then <mark style="background: #D2B3FFA6;">activate the licenses for each subscription that you purchased</mark>.
## Activation Steps 
<mark style="background: #FFB8EBA6;">To register a hardware firewall, click <strong>Assets</strong> on the Palo Alto Networks Customer Support Portal</mark>, <mark style="background: #FF5582A6;">enter your serial number</mark>, and click <mark style="background: #FFB8EBA6;"><strong>Register Device</strong></mark>. <mark style="background: #FFB86CA6;">The Customer Support Portal is located on the Palo Alto Networks website</mark>.

<mark style="background: #FFF3A3A6;">When you purchase a VM-Series firewall, you receive a set of authorization codes activation code associated with each subscription by email</mark>. 

The email typically includes authorization codes to license the VM-Series model that was purchased. 

To use the authorization code, <mark style="background: #BBFABBA6;">first register the code to the Support account on the Customer Support Portal</mark>. 
<mark style="background: #ABF7F7A6;">Click <strong>Device > Support</strong> and then click <strong>Activate support using authorization code</strong></mark>.

If you have an existing Support account, click the <mark style="background: #ADCCFFA6;"><strong>VM-Series Authentication Code</strong> link on the Customer Support Portal to manage the VM-Series firewall licenses and download the software</mark>. 

If you do not have an existing Support account, <mark style="background: #D2B3FFA6;">use the capacity auth-code to register and create an account on the Customer Support Portal</mark>. 

After the new account is verified and the registration is complete, <mark style="background: #CACFD9A6;">you can log in and download the software package that is needed to install the VM-Series firewall</mark>.

<mark style="background: #FFB8EBA6;">If the firewall is already installed, you can activate the subscriptions on <strong>Device > Licenses</strong></mark>. 
When active, <mark style="background: #FF5582A6;">most <strong>subscription services</strong> can use dynamic content updates to provide new and updated functionality to the firewall</mark>.
##  Subscriptions Services list
![[Subscriptions You Can Use With the Firewall.pdf]]
## ​PAN-OS Software Updates​
The firewall requires updates to the PAN-OS software and threat databases to maintain the most current protection levels. 

The MGT interface can be used to acquire these updates or an in-band traffic interface can be configured to acquire these updates. 

The firewall requires DNS server configuration to connect to the update servers.

To upgrade to a new release of the PAN-OS software, click <strong>Check Now</strong> to display the list of available versions of the PAN-OS software. 
Read the release notes for each version and then select a version to download and install. A support license is required for the download. Software updates require a firewall reboot.

The software can be downloaded directly from the Palo Alto Networks update server. 

The software can also be downloaded to another system, such as a user desktop or a Panorama management appliance, and then uploaded to the firewall. 

After you manually upload a software image to the Palo Alto Networks firewall, the image appears in the list of available software at <strong>Device > Software</strong>.

Click <strong>Install</strong> just as you would with software that is downloaded from the update server.
### Recommended upgrade path
The recommended upgrade path includes installing the latest maintenance release in each version before you download the base image for the next feature release version. 

For example, to upgrade PAN-OS 10.1.x to PAN-OS 11.0, you should download and install the latest preferred PAN-OS 10.1 maintenance release and reboot the firewall. 

Then download and install PAN-OS 10.2.0 and the latest preferred 10.2 maintenance release and so on. Finally, download and install PAN-OS 11.0.
#### Log Collectors 
Before upgrading managed firewalls from Panorama, you must upgrade Panorama and its Log Collectors to PAN-OS 11.0. 

When upgrading Log Collectors to 11.0, you must upgrade all Log Collectors simultaneously due to changes in the logging infrastructure. 

Once Panorama and the Log Collectors have been upgraded to PAN-OS 11.0, you can upgrade your managed firewalls running PAN-OS 10.1 and above to 11.0 without following the feature release path.
#### Legacy Mode
Note: When upgrading Panorama, you will need to decide whether to stay in Legacy mode if the Panorama virtual appliance is in Legacy mode on upgrade to PAN-OS 11.0. 

Legacy mode is not supported for a new Panorama virtual appliance deployment running PAN-OS 9.1 or a later release. 

Suppose you upgrade the Panorama virtual appliance from PAN-OS 9.0 or earlier release to PAN-OS 11.0. 

In that case, Palo Alto Networks recommends reviewing the Setup Prerequisites for the Panorama Virtual Appliance documentation and changing the mode to either Panorama Mode or Management Only mode based on your needs. 

If you want to keep the Panorama virtual appliance in Legacy mode, increase the number of CPUs to a minimum of 16vCPUs and the amount of memory allocated to a minimum of 32GB on the Panorama virtual appliance.
