---
categories:
  - "[[Security]]"
topic@security:
  - "[[Palo Alto Networks]]"
tags:
  - palo_alto/ngfw
created: 2026-02-20T15:06:36+01:00
modified: 2026-02-20T16:42:42+01:00
---
<strong>Device-ID</strong> is a PAN-OS policy construct for enforcement and visibility. 
It allows administrators <mark style="background: #FFB8EBA6;">to apply consistent <strong>policy control</strong> and <strong>threat prevention</strong> to a <strong>device</strong></mark> <mark style="background: #FF5582A6;">no matter where it <strong>moves</strong> within the network or what its <strong>IP address</strong> is at any given time</mark>. 
<mark style="background: #FFB86CA6;">The presence of device identity information in firewall logs provides visibility</mark> <mark style="background: #FFF3A3A6;">that enables workflows for threat assessment, incident response, and remediation</mark>.

Device-ID operates similarly to how [[User-ID™|User-ID]] provides user-based policy and [[App-ID™|App-ID]] provides app-based policy. 

Device-ID provides traceability for devices and the ability <mark style="background: #BBFABBA6;">to associate network events with specific devices</mark>. <mark style="background: #ABF7F7A6;">It thus allows you to gain context for how <strong>events</strong> relate to <strong>devices</strong></mark> and <mark style="background: #ADCCFFA6;">write policies that are associated with devices</mark>, <mark style="background: #D2B3FFA6;">instead of users, locations, or IP addresses, which can change over time</mark>.

You can use <strong>Device-ID</strong> in <strong>Security</strong>, <strong>Decryption</strong>, <strong>Quality of Service</strong> (QoS), and <strong>Authentication</strong> policies.

# IoT Security
<mark style="background: #CACFD9A6;">For <strong>Device-ID</strong> features to be available on a firewall</mark>, <mark style="background: #FFB8EBA6;">you must purchase an <strong>IoT Security subscription</strong></mark> and select the firewall during the <strong>IoT Security onboarding process</strong>. 

There are two types of IoT Security subscriptions:
- <strong>IoT Security Subscription</strong>
- <strong>IoT Security – Doesn’t Require Data Lake (DRDL) Subscription</strong>
With the first subscription, <mark style="background: #FF5582A6;">firewalls send data logs to the logging service</mark>, <mark style="background: #FFB86CA6;">which streams them to <strong>IoT Security</strong> for analysis</mark> and <mark style="background: #FFF3A3A6;">to a <strong>Cortex Data Lake instance</strong> for storage</mark>. The <strong>data lake instance</strong> can either be a new or existing one. 

With the second subscription, <mark style="background: #BBFABBA6;">firewalls send data logs to the logging service</mark>, <mark style="background: #ABF7F7A6;">which streams them to IoT Security for analysis</mark> <mark style="background: #ADCCFFA6;">but not to a Cortex Data Lake instance for storage</mark>. 

<mark style="background: #D2B3FFA6;">It’s important to note that both <strong>IoT Security</strong> and <strong>IoT Security (DRDL)</strong> subscriptions provide the same functionality in terms of <strong>IoT Security</strong> and <strong>Device-ID</strong></mark>.

<mark style="background: #CACFD9A6;">To permit connections to IoT Security</mark>, <mark style="background: #FFB8EBA6;">a firewall needs a <strong>device license</strong></mark>; and <mark style="background: #FF5582A6;">to permit connections to the logging service</mark>, <mark style="background: #FFB86CA6;">it needs a <strong>logging service license</strong></mark>. 

<mark style="background: #FFF3A3A6;">A firewall also requires a <strong>device certificate</strong> to <strong>authenticate itself</strong> when connecting to <strong>IoT Security</strong> and the <strong>logging service</strong></mark>.

If you use PAN-OS version 8.1.0 through PAN-OS 9.1.x on a firewall, the <mark style="background: #BBFABBA6;">IoT Security license provides <strong>device classification</strong>, <strong>behavior analysis</strong>, and <strong>threat analysis</strong> for your devices</mark>. If you use PAN-OS 10.0 or later, <mark style="background: #ABF7F7A6;">you can use Device-ID to obtain <strong>IP address-to-device mappings</strong></mark> <mark style="background: #ADCCFFA6;">to view <strong>device context</strong> for <strong>network events</strong></mark>, <mark style="background: #D2B3FFA6;">use IoT Security to obtain policy rule recommendations for these devices</mark>, and <mark style="background: #CACFD9A6;">gain visibility for devices in <strong>reports</strong> and the <strong>ACC</strong></mark>.
## Device-ID Classification 
<mark style="background: #FFB8EBA6;">To identify and classify devices</mark>, <mark style="background: #FF5582A6;">the <strong>IoT Security app</strong> uses <strong>metadata</strong> from <strong>network protocols</strong> and <strong>sessions</strong></mark> and <mark style="background: #FFB86CA6;">sends the <strong>metadata</strong> to the cloud</mark> <mark style="background: #FFF3A3A6;">in <strong>Session logs</strong> and <strong>Enhanced Application logs</strong> (<strong>EALs</strong>)</mark>. 

<mark style="background: #BBFABBA6;">The metadata collected does not include private or sensitive information or data that is not relevant for device identification</mark>. 

<mark style="background: #ABF7F7A6;">Metadata also forms the basis of the expected behavior for the device profile to allow only trusted behavior, which formulates the policy rule recommendation</mark>.

There are six levels of classification (also known as attributes) for devices:

| ATTRIBUTE  | EXAMPLE           |
| ---------- | ----------------- |
| Category   | Printer           |
| Profile    | Sharp Printer     |
| Model      | MX-6070N          |
| Os Version | ThreadX 5         |
| Os Family  | ThreadX RTOS      |
| Vendor     | SHARP Corporation |
When a firewall imports <mark style="background: #ADCCFFA6;">Security policy rule recommendations</mark> and <mark style="background: #D2B3FFA6;">IP address-to-device mappings</mark> from <mark style="background: #CACFD9A6;">IoT Security</mark>, <mark style="background: #FFB8EBA6;">the firewall sends its device certificate to an edge server to authenticate itself</mark>. <mark style="background: #FF5582A6;">The edge server authenticates itself to the firewall by sending its own certificate</mark>. <mark style="background: #FFB86CA6;">The firewall uses Online Certificate Status Protocol (OCSP) to validate the server’s certificate by checking it against the following sites using HTTP on TCP port 80</mark>:
- \*.o.lencr.org
- x1.c.lencr.org
Panorama performs the same check to validate the edge server’s certificate when Panorama imports policy rule recommendations from IoT Security.


# 