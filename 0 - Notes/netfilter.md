---
categories:
  - "[[Linux]]"
topic@linux:
tags:
icon: SiLinux
iconColor: "#000000"
---
 The <strong>netfilter</strong> project is a community-driven collaborative FOSS project that provides packet filtering software for the Linux 2.4.x and later kernel series. The netfilter project is commonly associated with iptables and its successor [[nftables]].

<mark style="background: #FFF3A3A6;">The netfilter project enables packet filtering, network address and port translation (NAT), packet logging, userspace packet queueing and other [[security glossary#packet mangling|packet mangling]]</mark>.

The <strong>netfilter hooks</strong> are a <strong>framework</strong> inside the Linux kernel that allows <mark style="background: #FF5582A6;">kernel modules</mark> <mark style="background: #FFB8EBA6;">to register callback functions at different locations of the Linux network stack</mark>. The registered callback function is then called back for every packet that traverses the respective hook within the Linux network stack.

The hooks that allow kernel modules to inspect, modify, drop, or reroute network packets as they flow through the networking stack.