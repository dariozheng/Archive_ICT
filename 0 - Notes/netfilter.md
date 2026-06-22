---
categories:
  - "[[Linux]]"
topic@linux:
tags:
icon: SiLinux
iconColor: "#000000"
---
The <strong>netfilter</strong> project is a community-driven collaborative FOSS project that provides <strong>packet filtering software</strong> for the Linux 2.4.x and later kernel series. The netfilter project is commonly associated with [[iptables]] and its successor [[nftables]].

The netfilter project provides a framework that enables packet filtering, network address and port translation (NAT), packet logging, connection tracking, userspace packet queueing and other [[security glossary#packet mangling|packet mangling]].

The netfilter framework provides a powerful mechanism for intercepting and manipulating network packets in the Linux kernel. This framework has 2 components to it – <strong>Netfilter hooks</strong> and <strong>conntrack</strong>.

The [[#netfilter hooks]] are a framework inside the Linux kernel that allows kernel modules to register callback functions at different locations of the Linux network stack. 
The registered callback function is then called back for every packet that traverses the respective hook within the Linux network stack.

[[iptables]] is a generic firewalling software that allows you to define rulesets. Each rule within an IP table consists of a number of classifiers (iptables matches) and one connected action (iptables target).

[[nftables]] is the successor of iptables, it allows for much more flexible, scalable and performance packet classification. This is where all the fancy new features are developed. 

## Main Features
- stateless packet filtering (IPv4 and IPv6)
- stateful packet filtering (IPv4 and IPv6)
- all kinds of network address and port translation, e.g. NAT/NAPT (IPv4 and IPv6)
- flexible and extensible infrastructure
- multiple layers of API's for 3rd party extensions
## What can I do with netfilter?
- build internet firewalls based on stateless and stateful packet filtering
- deploy highly available stateless and stateful firewall clusters
- use NAT and masquerading for sharing internet access if you don't have enough public IP addresses
- use NAT to implement transparent proxies
- aid the <strong>tc</strong> and <strong>iproute2</strong> systems used to build sophisticated QoS and policy routers
- do further packet manipulation (mangling) like altering the TOS/DSCP/ECN bits of the IP header
## What value does nftables provide?
- a single tool with consistent syntax as opposed to the fragmented {ip,ip6,eb,arp}tables and ipset
- faster kernel-side transactional ruleset updates, no need for user-space locking
- sets are more flexible and powerful than ipset, maps push the concept even further
- full ruleset flexibility:
    
    - no pre-defined tables and chains
    - arbitrary number of user-defined tables to separate the ruleset into "namespaces"
    - base chain's hook and priority are configurable
    
- more flexible rules: No mandatory parts (like counters), multiple actions allowed (e.g. log and drop)
- ingress hook attaching a chain to an interface for early filtering right after TC
- egress hook attaching a chain to an interface for transmit path filtering right before TC
- flowtables provide a software fast path and hardware acceleration
- some limited scripting ability embedded in the syntax (define variables, include other files), support for extensive scripting via JSON input and output
# Netfilter Hooks
There are five `netfilter` hooks that programs can register with. 

<mark style="background: #BBFABBA6;">As packets progress through the stack, they will trigger the kernel modules that have registered with these hooks</mark>. 

The hooks that a packet will trigger depends on whether the packet is incoming or outgoing, the packet’s destination, and whether the packet was dropped or rejected at a previous point.

<strong>Netfilter hooks</strong> allow the kernel modules to implement custom firewall rules, network address translation, packet filtering, logging, and more. 
Pre-defined functions that are performing tasks such as filtering and logging can be hot-plugged into the kernel, which makes them easier to use.

There are five predefined netfilter hook points:

## `NF_IP_PRE_ROUTING`
 This hook will be triggered by <mark style="background: #FF5582A6;">any incoming traffic</mark> very soon after entering the network stack. This hook is processed before any routing decisions have been made regarding where to send the packet i.e. <mark style="background: #FFB8EBA6;">to check if this packet is destined for another interface</mark>, or <mark style="background: #FFB86CA6;">a local process</mark>. The routing code may drop packets that are unrouteable.

## `NF_IP_LOCAL_IN`
This hook is triggered <mark style="background: #FFB86CA6;">after an incoming packet has been routed</mark> <mark style="background: #FFF3A3A6;">if the packet is destined for the local system</mark>.

## `NF_IP_FORWARD`
This hook is triggered <mark style="background: #BBFABBA6;">after an incoming packet has been routed</mark> <mark style="background: #ABF7F7A6;">if the packet is to be forwarded to another host</mark>.

## `NF_IP_LOCAL_OUT`
This hook is triggered by <mark style="background: #ADCCFFA6;">any locally created outbound traffic</mark> <mark style="background: #FFB86CA6;">as soon as it hits the network stack</mark>.

## `NF_IP_POST_ROUTING`
This hook is triggered by <mark style="background: #FFB8EBA6;">any outgoing or forwarded traffic</mark> <mark style="background: #FF5582A6;">after routing has taken place and just before being sent out on the wire</mark>.
#
Each hook point corresponds to a different stage of packet processing, as shown in the diagram below:

![[Pasted image 20260622123654.png]]

When a packet arrives at or leaves a network interface, it passes through each of these hook points in order. At each hook point, the kernel calls all the registered netfilter hook functions for that hook point. Each netfilter hook function can inspect the packet and decide what to do with it. The possible actions are:

- Accept: The packet is allowed to continue to the next hook point or the destination.
- Drop: The packet is silently discarded and no further processing is done.
- Queue: The packet is queued for userspace processing by a daemon such as iptables or nftables.
- Repeat: The packet is re-injected at the same hook point for another round of processing.
- Stop: The packet is accepted and no further processing is done.

Netfilter [[linux glossary#kernel modules|kernel modules]] <mark style="background: #ABF7F7A6;">that need to register at these hooks</mark> must also provide a <strong>priority number</strong> <mark style="background: #BBFABBA6;">to help determine the order in which the <strong>kernel modules</strong> will be called when the hook is triggered</mark>. 
<mark style="background: #ADCCFFA6;">This provides the means for multiple modules</mark> (or multiple instances of the same module) <mark style="background: #D2B3FFA6;">to be connected to each of the hooks (multiple modules can be connected to a single host) with deterministic ordering</mark>. 

<mark style="background: #ABF7F7A6;">Each module will be called in turn</mark> and <mark style="background: #ADCCFFA6;">will return a decision to the</mark> `netfilter` <strong>framework</strong> after <strong>a processing</strong> <mark style="background: #CACFD9A6;">that indicates what should be done with the packet</mark>.