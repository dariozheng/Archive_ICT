---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - category/networking/networking_general
icon: FasNetworkWired
iconColor:
last_update:
---
AWS networking is software-defined: instead of racking routers, switches, and firewalls, you describe the network you want and AWS realises it on shared physical infrastructure. The Virtual Private Cloud is the foundation — a logically isolated virtual network that behaves like a private data-centre network you design and control. This note covers the core building blocks of a VPC and how they fit together, with analogies to traditional on-premises networking throughout.

## Virtual Private Cloud

_A logically isolated virtual network, scoped to one AWS Region, in which you place and connect your resources._

A VPC is the top-level container for everything you build. It spans a single Region and every Availability Zone within it, and it is isolated from every other VPC by default — traffic cannot flow between VPCs, or between a VPC and the internet, unless you explicitly build a path. Inside the VPC you carve out subnets, attach gateways, and write [[Routing|routing]] and security rules.

Because the VPC is isolated at creation, the mental model is inverted from a physical network: you start with a sealed, private space and open only the paths you intend, rather than starting connected and locking things down afterwards.

> [!info] On-premises analogy A VPC is your own private data-centre network or campus L3 domain — the address space, routers, and firewalls that would live in your building, except defined in software and running on AWS's shared fabric.

### CIDR Blocks and IP Addressing

_The private address range that defines the VPC's size and the pool every subnet draws from._

A VPC is defined by an IPv4 CIDR block chosen when you create it — for example `10.0.0.0/16`. The prefix length can range from `/16` (65,536 addresses) down to `/28` (16 addresses). You normally pick a private range from RFC 1918 space (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), the same ranges you would use on-prem.

The primary CIDR block is effectively permanent: although secondary blocks can be added later, the primary cannot be resized, so it should be sized generously and — critically — chosen so it does not overlap with other VPCs or on-prem networks you might later connect. Overlapping ranges make peering and hybrid connectivity impossible, because routing cannot distinguish two identical prefixes.

[[IPv6]] is supported as an optional, additional addressing layer: a VPC can be dual-stack, carrying both an IPv4 CIDR and an Amazon-assigned `/56` IPv6 block.

> [!tip] Plan address space up front Overlapping CIDRs are the single most common cause of failed peering and VPN designs. Treat VPC addressing like on-prem IP planning: allocate non-overlapping ranges across every environment before you build.

### Regions and Availability Zones

_The geographic and fault-isolation structure the VPC is built on._

A Region is a geographic location, such as `eu-south-1` in Milan. Within each Region are multiple Availability Zones — physically separate data centres with independent power, cooling, and networking, interconnected by low-latency links. A VPC spans all zones in its Region, but each subnet lives in exactly one zone.

Designing across multiple zones is how you build fault tolerance: if one zone fails, resources in another continue serving. This zone boundary is why most production VPCs duplicate their subnet layout across two or more Availability Zones.

> [!info] On-premises analogy A Region is like a metro area with several data centres; an Availability Zone is one of those independent buildings. Spreading subnets across zones is the cloud equivalent of dual-site redundancy.

## Subnets

_Address ranges carved from the VPC CIDR, each bound to a single Availability Zone._

A subnet is a slice of the VPC's CIDR block — for instance `10.0.1.0/24` within a `10.0.0.0/16` VPC. Each subnet is pinned to one Availability Zone, and every resource you launch lives, through its network interface, in exactly one subnet and therefore one zone. Subnets are how you both segment traffic and place resources in specific failure domains.

Unlike a traditional [[VLANs|VLAN]], a subnet is a pure Layer 3 construct: there is no broadcast domain in the classic sense, and the switching is handled invisibly by the AWS fabric. You size and number subnets, but you never manage spanning tree, trunking, or a physical switch.

> [!info] On-premises analogy A subnet resembles a VLAN plus its IP subnet — a segment where a group of hosts live. The difference is that it is Layer 3 only, zone-scoped, and has no L2 fabric for you to configure.

### Public and Private Subnets

_The public/private distinction is a routing outcome, not a subnet setting._

There is no checkbox that makes a subnet public. A subnet is public if its associated [[#Route Tables|route table]] sends internet-bound traffic (`0.0.0.0/0`) to an [[#Internet Gateway]]; it is private if it does not. That single routing decision is the whole distinction.

- Public subnet: has a default route to an Internet Gateway. Resources holding a public IP can both reach and be reached from the internet.
- Private subnet: has no route to an Internet Gateway. Resources have no direct internet path; for outbound-only access they route through a [[#NAT Gateway]] that itself sits in a public subnet.

> [!note] Why this matters conceptually Because public is just a route, moving a workload between public and private is a routing change, not a rebuild. It also means a subnet can be accidentally public simply by pointing its route table at an Internet Gateway — routing, not naming, is the source of truth.

### Reserved Addresses

_AWS reserves five addresses in every subnet, so usable host count is the block size minus five._

In each subnet, AWS reserves the first four addresses and the last address:

|Address|Purpose|
|---|---|
|`.0`|Network address|
|`.1`|Reserved for the implicit VPC router|
|`.2`|Reserved for the Amazon-provided DNS resolver|
|`.3`|Reserved for future use|
|Last address|Network broadcast (broadcast is unsupported, but the address is still reserved)|

A `/24` subnet therefore offers 251 usable addresses, not 256. This matters when sizing small subnets: a `/28` yields only 11 usable hosts.

> [!info] On-premises analogy Reserving the network and broadcast addresses is familiar from any IP subnet; AWS simply reserves three more for the router and DNS addresses it runs on your behalf.

## Routing

_How traffic is directed within the VPC and toward external destinations._

### Route Tables

_A set of rules matching destination CIDRs to targets; each subnet uses exactly one._

A route table is an ordered set of routes, each mapping a destination CIDR to a target — a gateway, a network interface, or the local VPC. Every subnet is associated with exactly one route table; if you do not associate one explicitly, the subnet falls back to the VPC's main route table.

A minimal route table contains only the local route. To give a subnet internet access you add a route such as `0.0.0.0/0 → igw-xxxx`; to send traffic elsewhere you point the relevant CIDR at the appropriate gateway (NAT, peering, VPN, and so on).

> [!info] On-premises analogy A route table is the routing table of a router or L3 switch, and associating it with a subnet is like applying that routing context to a VLAN interface. The difference is that the router itself is invisible and fully managed.

### The Implicit Router

_Every VPC has a built-in router that owns all route tables and connects the subnets._

You never see or configure a router object, but one exists: the implicit router is the element that actually forwards packets according to your route tables. It is the reason subnets in the same VPC can talk to each other with no configuration at all.

That intra-VPC reachability comes from the local route — an entry present in every route table, covering the whole VPC CIDR, that cannot be edited or removed:

```text
Destination      Target
10.0.0.0/16      local     ← the local route (always present, immutable)
0.0.0.0/0        igw-xxxx  ← added by you for internet access
```

Because the local route always covers the entire VPC, all subnets are mutually reachable by default; segmentation between them is enforced by security controls, not by routing.

### Route Priority

_When multiple routes match, the most specific prefix wins._

If several routes could match a destination, the VPC router uses longest-prefix match: the route with the most specific (longest) CIDR is chosen. A route to `10.0.5.0/24` is preferred over `10.0.0.0/16`, which is preferred over `0.0.0.0/0`. This is the same longest-match logic physical routers use, and it is what lets a narrow route to a peering connection or endpoint override a broad default route.

> [!info] On-premises analogy Longest-prefix match is identical to how any IP router selects routes; the local route behaves like a directly connected route that always takes precedence for in-VPC destinations.

## Internet Connectivity

_The gateways that connect a VPC to the public internet, in each direction._

### Internet Gateway

_A managed, redundant gateway enabling bidirectional internet access and 1:1 NAT for public IPs._

An Internet Gateway is attached to a VPC — one per VPC — and provides the path to and from the public internet. It is horizontally scaled and redundant by design, not a device you size or a bottleneck you manage. Two things must be true for a resource to be internet-reachable through it: the subnet's route table must have a default route to the gateway, and the resource must hold a public IPv4 address (or an IPv6 address).

The Internet Gateway also performs the translation between a resource's private IP and its public IP. The instance only ever sees its private address; the gateway maps inbound traffic destined for the public IP to the private IP, and the reverse on the way out.

> [!info] On-premises analogy An Internet Gateway is the internet edge — your border router plus the static 1:1 NAT that maps public addresses to internal hosts — collapsed into one managed, always-redundant service.

### NAT Gateway

_A managed gateway letting private-subnet resources initiate outbound traffic without being reachable inbound._

A NAT Gateway gives resources in a [[#Public and Private Subnets|private subnet]] outbound-only internet access — to fetch updates or call external APIs — while preventing any unsolicited inbound connection. It performs source NAT, or port address translation: many private hosts share the NAT Gateway's single public Elastic IP.

Placement is the part worth internalising. The NAT Gateway itself sits in a public subnet, because it needs the Internet Gateway to reach the internet, while the private subnets' route tables send `0.0.0.0/0` to the NAT Gateway rather than to the Internet Gateway. A NAT Gateway is zone-scoped, so a fault-tolerant design places one in each Availability Zone.

```text
Private subnet route:  0.0.0.0/0 → nat-xxxx   (NAT Gateway, in a public subnet)
Public subnet route:   0.0.0.0/0 → igw-xxxx   (Internet Gateway)

[ private host ] → NAT Gateway → Internet Gateway → Internet
       ▲                                              │
       └───────────  return traffic only  ◄───────────┘
       (the internet cannot initiate connections inbound)
```

> [!info] On-premises analogy A NAT Gateway is classic outbound PAT or masquerading on a firewall: internal hosts reach the internet behind one public address, and the outside cannot start connections back in.

### Egress-Only Internet Gateway

_The IPv6 equivalent of a NAT Gateway: outbound-only internet access, without translation._

IPv6 addresses in AWS are globally routable, so there is no NAT for IPv6. To get the same outbound-only behaviour — let IPv6 resources reach the internet but block anything inbound — you use an Egress-Only Internet Gateway. It is stateful and outbound-initiated only, mirroring what a NAT Gateway does for IPv4, but without rewriting addresses.

> [!info] On-premises analogy This is the IPv6 answer to outbound NAT: since every host already has a public IPv6 address, you drop the translation and keep only the stateful outbound-only firewall behaviour.

## Addresses and Network Interfaces

_How IP addresses are actually attached to resources._

### Elastic Network Interface

_A virtual NIC that carries a resource's addresses, MAC, and security groups._

An Elastic Network Interface is a virtual network card that lives in one subnet. It is the thing that actually holds a private IP — and optionally a public IP, an Elastic IP, and a MAC address — and it is where security groups are applied. An instance has at least one interface, its primary, and can carry several, letting it sit on multiple subnets or present multiple addresses.

Because the interface, not the instance, owns the network identity, it can be detached from one instance and attached to another, moving its IPs, MAC, and security groups with it.

> [!info] On-premises analogy An Elastic Network Interface is a physical or virtual NIC. Moving one between instances is like pulling a NIC — with its cabling, MAC, and firewall policy — out of one server and slotting it into another.

### Private, Public, and Elastic IP Addresses

_Three kinds of address, differing in scope and persistence._

|Type|Scope|Persistence|
|---|---|---|
|Private IP|Routable only inside the VPC and connected networks|Fixed for the life of the interface|
|Public IP|Reachable from the internet|Ephemeral — reassigned when the instance stops and starts|
|Elastic IP|Reachable from the internet|Static — held by your account until you release it|

Every interface receives a private IP from its subnet's range. A public IP is optional and, importantly, dynamic — stop and start an instance and its automatically assigned public IP changes. When you need a fixed public address — for a DNS record, an allow-list entry, or a NAT Gateway — you allocate an Elastic IP, which stays constant until you deliberately release it.

> [!info] On-premises analogy A private IP is your internal address; a public IP is a lease from a dynamic pool; an Elastic IP is a static public address you own and can re-point between hosts — like a reserved public IP you control.

## Network Security

_Two independent filtering layers: one at the interface, one at the subnet boundary._

AWS provides two distinct firewalls that operate at different points and with different semantics. Using both is defence in depth: a packet must pass the subnet's Network ACL and the interface's security group before it is delivered.

### Security Groups

_Stateful, allow-only filters applied at the network interface._

A security group is a stateful firewall attached to an [[#Elastic Network Interface|elastic network interface]]. It carries allow rules only — there is no explicit deny — so anything not matched by an allow rule is implicitly denied. Because it is stateful, return traffic is permitted automatically: if you allow an outbound request, its response is allowed back in without a matching inbound rule, and the reverse.

Rules can reference other security groups as their source or destination, not just IP ranges. This lets you express intent such as "the web tier may talk to the app tier" by referencing the tiers' groups, so the policy keeps working as instances come and go.

> [!info] On-premises analogy A security group is a stateful host-based firewall wrapped around each interface — closest to iptables or nftables on the host, or a per-VM firewall — that also tracks connection state, so you only write the initiating direction.

### Network ACLs

_Stateless, ordered allow/deny filters applied at the subnet boundary._

A Network ACL is a stateless filter evaluated at the edge of a subnet, on traffic entering or leaving it. Unlike a security group it supports both allow and deny rules, and rules are numbered and evaluated in order — the first match wins and evaluation stops there.

Being stateless is the key behavioural difference: the ACL remembers no connections, so you must explicitly permit return traffic. Replies to inbound requests leave on ephemeral ports, so a working ACL needs an outbound rule for the ephemeral port range in addition to the rule for the service port, and the reverse for outbound-initiated flows.

The default Network ACL that ships with a VPC allows all inbound and outbound traffic, so security groups are the effective control unless you deliberately tighten it. A newly created custom ACL does the opposite — it denies everything until you add rules.

> [!info] On-premises analogy A Network ACL is a router or switch ACL applied to a subnet boundary: ordered, numbered, allow-and-deny, and stateless — so, just as with a classic ACL, you account for return traffic and ephemeral ports yourself.

### Security Groups Versus Network ACLs

_The two layers compared side by side._

|Property|Security Group|Network ACL|
|---|---|---|
|Applies at|Network interface|Subnet boundary|
|State|Stateful — return traffic auto-allowed|Stateless — return traffic must be permitted|
|Rules|Allow only|Allow and deny|
|Evaluation|All rules considered; any allow permits|Numbered order; first match wins|
|Can reference|IP ranges and other security groups|IP ranges only|
|Default|New group allows all outbound, no inbound until you add rules|Default ACL allows all; custom ACL denies all|

```text
        Internet / another subnet
                  │
        ┌─────────▼──────────┐
        │   Network ACL      │  ← subnet boundary: stateless, ordered allow/deny
        └─────────┬──────────┘
                  │  (must allow the request AND the return direction)
        ┌─────────▼──────────┐
        │  Security Group    │  ← interface: stateful, allow-only, return auto-allowed
        └─────────┬──────────┘
                  │
            [ instance / ENI ]
```

The practical division of labour: security groups carry the day-to-day workload policy — which tiers may talk to which — while Network ACLs act as a coarse, subnet-wide guardrail, for example blocking a known-bad CIDR across a whole subnet regardless of instance-level rules.

## VPC Endpoints

_Private connectivity from a VPC to AWS services, without traversing the internet._

By default, reaching an AWS service such as S3 from a private subnet means going out through a NAT Gateway to a public endpoint. A VPC endpoint provides a private path instead: traffic to the service stays on the AWS network and never touches the internet, which improves the security posture and removes NAT data-processing costs for that traffic. There are two kinds.

### Gateway Endpoints

_Route-table entries that privately reach S3 and DynamoDB._

A gateway endpoint is added as a route in your route tables, sending traffic for a specific AWS service to that service over the AWS backbone. Gateway endpoints exist only for Amazon S3 and DynamoDB. They cost nothing and are implemented purely as routing — no interface or IP is placed in your subnet.

### Interface Endpoints

_An interface with a private IP in your subnet, fronting a service via PrivateLink._

An interface endpoint, powered by AWS PrivateLink, places an elastic network interface with a private IP inside your subnet, and traffic to the service is sent to that private address. Most AWS services — along with third-party and your own services — are reached this way. Because it is a real interface in your subnet, it is governed by security groups and billed per hour and per amount of data processed.

> [!info] On-premises analogy VPC endpoints are like a private peering or leased line to a specific service, replacing a trip out through your internet edge. A gateway endpoint is a route you add; an interface endpoint is a local presence — an interface with an address — that represents the remote service inside your own network.

## Mapping to On-Premises Networking

_A consolidated translation between AWS constructs and their traditional equivalents._

|AWS construct|On-premises equivalent|Notes|
|---|---|---|
|VPC|Private data-centre network / L3 domain|Isolated by default; software-defined|
|Subnet|VLAN + IP subnet|Layer 3 only, zone-scoped, no L2 fabric to manage|
|Availability Zone|An independent data-centre building|Fault-isolation boundary|
|Route table|Router / L3-switch routing table|Applied per subnet; the router itself is invisible|
|Implicit router|The routing engine of your core router|Fully managed; only its route tables are yours|
|Internet Gateway|Border router + 1:1 NAT at the internet edge|Managed and inherently redundant|
|NAT Gateway|Outbound PAT / masquerade on the firewall|Many private hosts behind one public IP|
|Egress-only gateway|Outbound-only IPv6 firewall, no NAT|IPv6 has no address translation|
|Elastic network interface|Physical or virtual NIC|Detachable; carries IPs, MAC, and policy|
|Elastic IP|Static public IP you own|Re-assignable between resources|
|Security group|Stateful per-host firewall|Allow-only; can reference other groups|
|Network ACL|Stateless router / subnet ACL|Ordered allow/deny; mind return traffic|
|VPC endpoint|Private link or peering to a specific service|Keeps service traffic off the internet|

The recurring theme: every physical box you would rack — router, firewall, NAT appliance, NIC — becomes a managed, software-defined construct that you declare rather than cable, and that AWS makes redundant on your behalf. What stays exactly the same is the logic: IP planning, longest-prefix routing, stateful versus stateless filtering, and the discipline of non-overlapping address space.

## Reference Architecture

_A conventional two-zone VPC that ties the building blocks together._

The canonical starting design places public and private subnets in two Availability Zones behind a single VPC and Internet Gateway. Public subnets hold internet-facing entry points and the NAT Gateways; private subnets hold application and database resources that reach out only through NAT.

```text
Region: eu-south-1
┌────────────────────────────────────────────────────────────────┐
│ VPC  10.0.0.0/16                          [ Internet Gateway ]   │
│                                                    │            │
│   ── Availability Zone A ──          ── Availability Zone B ──   │
│   ┌───────────────────────┐        ┌───────────────────────┐    │
│   │ Public  10.0.0.0/24   │        │ Public  10.0.1.0/24   │    │
│   │  0.0.0.0/0 → IGW      │        │  0.0.0.0/0 → IGW      │    │
│   │  [ NAT Gateway A ]    │        │  [ NAT Gateway B ]    │    │
│   └───────────┬───────────┘        └───────────┬───────────┘    │
│               │                                │                │
│   ┌───────────▼───────────┐        ┌───────────▼───────────┐    │
│   │ Private 10.0.10.0/24  │        │ Private 10.0.11.0/24  │    │
│   │  0.0.0.0/0 → NAT-A    │        │  0.0.0.0/0 → NAT-B    │    │
│   │  [ app / db hosts ]   │        │  [ app / db hosts ]   │    │
│   └───────────────────────┘        └───────────────────────┘    │
│                                                                 │
│   local route  10.0.0.0/16 → local   (all subnets interconn.)   │
└────────────────────────────────────────────────────────────────┘
```

Reading the diagram against the concepts:

- The VPC's `10.0.0.0/16` block is subdivided into four `/24` subnets, two per zone, so a single zone failure never takes out an entire tier.
- Public subnets carry a default route to the Internet Gateway; that route is the only thing that makes them public.
- Private subnets carry a default route to the NAT Gateway in their own zone, giving outbound-only internet access with no inbound exposure.
- The immutable local route means every subnet can already reach every other; whether they may is decided by security groups and Network ACLs, not by routing.

> [!info] On-premises analogy This is the cloud rendering of a classic DMZ-plus-internal design: a public tier at the internet edge for load balancers and NAT, and a protected internal tier for applications and data — drawn twice for dual-site redundancy across Availability Zones.