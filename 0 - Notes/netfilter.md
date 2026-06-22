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

The following hooks represent these well-defined points in the networking stack:

## `NF_IP_PRE_ROUTING`
 This hook will be triggered by <mark style="background: #FF5582A6;">any incoming traffic</mark> very soon after entering the network stack. This hook is processed before any routing decisions have been made regarding where to send the packet.

## `NF_IP_LOCAL_IN`
This hook is triggered <mark style="background: #FFB86CA6;">after an incoming packet has been routed</mark> <mark style="background: #FFF3A3A6;">if the packet is destined for the local system</mark>.

## `NF_IP_FORWARD`
This hook is triggered <mark style="background: #BBFABBA6;">after an incoming packet has been routed</mark> <mark style="background: #ABF7F7A6;">if the packet is to be forwarded to another host</mark>.

## `NF_IP_LOCAL_OUT`
This hook is triggered by <mark style="background: #ADCCFFA6;">any locally created outbound traffic</mark> <mark style="background: #FFB86CA6;">as soon as it hits the network stack</mark>.

## `NF_IP_POST_ROUTING`
This hook is triggered by <mark style="background: #FFB8EBA6;">any outgoing or forwarded traffic</mark> <mark style="background: #FF5582A6;">after routing has taken place and just before being sent out on the wire</mark>.

--- 
# 
<mark style="background: #FFF3A3A6;">[[linux glossary#kernel modules|kernel modules]] that need to register at these hooks</mark> must also provide a <strong>priority number</strong> <mark style="background: #BBFABBA6;">to help determine the order in which they will be called when the hook is triggered</mark>. 

<mark style="background: #ADCCFFA6;">This provides the means for multiple modules</mark> (or multiple instances of the same module) <mark style="background: #D2B3FFA6;">to be connected to each of the hooks with deterministic ordering</mark>. 

<mark style="background: #ABF7F7A6;">Each module will be called in turn</mark> and <mark style="background: #ADCCFFA6;">will return a decision to the</mark> `netfilter` <strong>framework</strong> after processing that indicates what should be done with the packet.