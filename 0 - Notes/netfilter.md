---
categories:
  - "[[Linux]]"
topic@linux:
tags:
icon: SiLinux
iconColor: "#000000"
---
The <strong>netfilter</strong> project is a community-driven collaborative FOSS project that provides <strong>packet filtering software</strong> for the Linux 2.4.x and later kernel series. The netfilter project is commonly associated with [[iptables]] and its successor [[nftables]].

<mark style="background: #FFF3A3A6;">The netfilter project enables packet filtering, network address and port translation (NAT), packet logging, userspace packet queueing and other [[security glossary#packet mangling|packet mangling]]</mark>.

 The <strong>netfilter hooks</strong> are a framework inside the Linux kernel that allows kernel modules to register callback functions at different locations of the Linux network stack. 
 
 The registered callback function is then called back for every packet that traverses the respective hook within the Linux network stack.

[[iptables]] is a generic firewalling software that allows you to define rulesets. Each rule within an IP table consists of a number of classifiers (iptables matches) and one connected action (iptables target).

[[nftables]] is the successor of iptables, it allows for much more flexible, scalable and performance packet classification. This is where all the fancy new features are developed. 
# Netfilter Hooks
There are five `netfilter` hooks that programs can register with. 

As packets progress through the stack, they will trigger the kernel modules that have registered with these hooks. 

The hooks that a packet will trigger depends on whether the packet is incoming or outgoing, the packet’s destination, and whether the packet was dropped or rejected at a previous point.

The following hooks represent these well-defined points in the networking stack:

## `NF_IP_PRE_ROUTING`
 This hook will be triggered by any incoming traffic very soon after entering the network stack. This hook is processed before any routing decisions have been made regarding where to send the packet.

## `NF_IP_LOCAL_IN`
This hook is triggered after an incoming packet has been routed if the packet is destined for the local system.

## `NF_IP_FORWARD`
This hook is triggered after an incoming packet has been routed if the packet is to be forwarded to another host.

## `NF_IP_LOCAL_OUT`
This hook is triggered by any locally created outbound traffic as soon as it hits the network stack.

## `NF_IP_POST_ROUTING`
This hook is triggered by any outgoing or forwarded traffic after routing has taken place and just before being sent out on the wire.

Kernel modules that need to register at these hooks must also provide a priority number to help determine the order in which they will be called when the hook is triggered. 

This provides the means for multiple modules (or multiple instances of the same module) to be connected to each of the hooks with deterministic ordering. 

Each module will be called in turn and will return a decision to the `netfilter` framework after processing that indicates what should be done with the packet.