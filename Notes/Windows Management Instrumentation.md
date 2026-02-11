---
categories:
  - "[[Microsoft]]"
product:
  - "[[Windows]]"
tags:
created: 2026-02-11T15:41:15+01:00
modified: 2026-02-11T17:18:59+01:00
aliases:
  - WMI
---
<mark style="background: #ABF7F7A6;"><strong>Windows Management Instrumentation</strong> (WMI) is the infrastructure for management data and operations on Windows-based operating systems</mark>. It is standard technology for accessing management information in an enterprise environment. 

![[WMI.png]]
<mark style="background: #FFB86CA6;">It provides a <strong>common interface</strong> and <strong>object model</strong></mark> <mark style="background: #BBFABBA6;">to access management information about operating system, devices, applications and services</mark>. <mark style="background: #ADCCFFA6;">If this service is stopped, most Windows-based software will not function properly</mark>. <mark style="background: #FFB8EBA6;">If this service is disabled, any services that explicitly depend on it will fail to start</mark>.

WMI is the implementation of [[Web-Based Enterprise Management|WBEM]] and uses [[Common Information Model|CIM]] industry standard to represent systems, applications, networks, devices, and other managed components.

Although <mark style="background: #FFF3A3A6;">you can write WMI scripts or applications to automate administrative tasks on remote computers</mark>, <mark style="background: #BBFABBA6;">WMI also supplies management data to other parts of the operating system and products</mark>. For example, <mark style="background: #FFB8EBA6;"><strong>System Center Operations Manager</strong> or <strong>Windows Remote Management</strong></mark>.

WMI is fully supported by Microsoft. The latest version of administrative scripting and control is available through the Windows Management Infrastructure (MI). 

MI is fully compatible with previous versions of WMI, and provides a host of features and benefits that make designing and developing providers and clients easy. 

