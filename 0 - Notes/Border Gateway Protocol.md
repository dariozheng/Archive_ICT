---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - category/networking/networking_general
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-08-26
aliases:
  - BGP
  - Border Gateway Protocol
---
<strong>Border Gateway Protocol (BGP)</strong> is the core routing protocol that manages how data packets are directed across the internet by exchanging routing and reachability information between different networks or [[Autonomous System]].

# Path Attributes
<strong>BGP</strong> uses <strong>path attributes (PAs)</strong> associated with each network path. 
<strong>BGP routers</strong> evaluate these attributes in a strict, sequential order to prevent routing loops, classify prefixes, and determine the single best path to a network destination.

Every path attribute falls into one of four standard categories based on whether all routers must recognize it and whether it must be passed across different networks.

Per RFC 4271, <strong>well-known attributes</strong> must be recognized by all BGP implementations. <strong>Well-known mandatory attributes</strong> must be included with every prefix advertisement; <strong>well-known discretionary attributes</strong> may or may not be included with a prefix advertisement.

<strong>Optional attributes</strong> do not have to be recognized by all BGP implementations. Optional attributes can be set so that they are <strong>transitive</strong> and stay with the route advertisement from AS to AS. Other PAs are <strong>non-transitive</strong> and cannot be shared from AS to AS.
## Well-known mandatory
Every <strong>BGP-compliant router</strong> <mark style="background: #FFB8EBA6;">must recognize these attributes</mark>, and they <strong>must be included</strong> in every BGP route update message.
### AS_PATH
A chronological list of all Autonomous Systems (AS) that the route has traveled through to help prevent loops.
### NEXT_HOP
The specific IP address of the next router used to reach the destination.
Every single BGP route must have a valid, reachable next-hop IP address. If the router's routing table cannot find a valid path to reach this `NEXT_HOP` IP, the BGP route is completely ignored.
### ORIGIN
Identifies how the route was first injected into BGP (e.g., via Interior Gateway Protocol, Exterior Gateway Protocol, or an incomplete/unknown source).
## Well-known discretionary 
Every BGP router <strong>must recognize</strong> these attributes, but they are <strong>optional</strong> to include in a route update
### LOCAL_PREF
Instructs routers within the local network which path to prefer when exiting the system.
This is the primary tool for engineering <strong>outbound traffic</strong>. If your company has two internet providers, you give a higher <strong>Local Preference</strong> to your primary provider so all internal routers choose it first.
### ATOMIC_AGGREGATE
Warns downstream routers that specific routing data was lost due to route summarization
## Optional transitive
Routers do not have to recognize these attributes. If a router does not recognize it, it will still <strong>keep the attribute intact and pass it along</strong> to neighboring routers.
### COMMUNITY
A tagging mechanism used to group destinations and apply routing policies dynamically.

While not part of the standard step-by-step decision tree, <strong>BGP Communities</strong> are <mark style="background: #FFB8EBA6;">strings of numbers</mark> used to <mark style="background: #FF5582A6;">group routes</mark>. It is heavily used by Internet Service Providers (ISPs) to let customers dynamically trigger `LOCAL_PREF` or `AS_PATH` changes on the provider's side.
### AGGREGATOR
Specifies the AS number and IP address of the router that performed route summarization.
## Optional non-transitive
Routers do not have to recognize these attributes. If a router does not recognize it, or if the route crosses into a different network, the attribute is <strong>quietly deleted and not passed forward</strong>.
### MED (Multi-Exit Discriminator)
Suggests to external neighbors which path they should prefer when entering your network.
This is used to influence <strong>inbound traffic</strong> from a directly connected neighbor. If you have two physical connections to the same provider, you send a lower MED value on the link you want them to use.
### ORIGINATOR_ID
A tie-breaker ID used to prevent routing loops in networks utilizing Route Reflectors.
