---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - claude
  - cisco
icon: SiCisco
iconColor:
---
Cisco Digital Network Architecture (Cisco DNA) is Cisco's intent-based networking architecture for the enterprise campus, branch, and WAN. It is a framework, not a single product: a software-driven approach that treats the network as one programmable system expressing business intent, rather than as a collection of independently configured devices. The controller, the fabric, the policy model, and the analytics that appear as concrete products are the implementation of this architecture — most visibly the controller, whose configuration is documented separately in [[Cisco DNA Center]]. This note covers the concepts behind the architecture.

> [!info] Architecture versus controller "Cisco DNA" names the architecture and its guiding ideas. "Cisco DNA Center" (now Catalyst Center) is the on-premises controller that realises those ideas. The theory here is vendor-framed but largely general to intent-based networking; the product note is specific to the controller.

## From devices to intent

_Why intent-based networking exists, and the shift in thinking it represents._

Traditional networks are operated one device at a time. That model is the root of most of the operational pain the architecture sets out to remove.

### The limits of box-by-box operation

_What breaks when the network is a set of independently configured boxes._

When each switch, router, and access point is configured individually through the CLI, several problems follow: change is slow and manual, configuration drifts out of consistency across devices, visibility is limited to per-device counters and SNMP polls, security is bolted on box by box rather than designed in, and there is no direct link between what the business wants and how the network is configured. None of this scales as the number of devices and the rate of change grow.

### Imperative versus declarative networking

_The difference between telling the network how and telling it what._

Box-by-box configuration is imperative: the operator specifies the exact commands — the how — on every device. Intent-based networking is declarative: the operator specifies the desired outcome — the what — and the system works out the configuration needed to achieve it and keeps it that way. Declaring that finance endpoints may reach finance servers and nothing else is intent; the VLANs, ACLs, and tags that implement it are the system's concern, not the operator's.

### Building on software-defined networking

_How intent-based networking extends, rather than replaces, SDN._

Software-defined networking (SDN) was the prior step in this evolution: it centralised control and made the network programmable, separating control decisions from the forwarding hardware and exposing them through a controller and open interfaces. Intent-based networking builds directly on that programmable, centralised base rather than replacing it. What it adds on top is the [[#Translation|translation]] of high-level intent into policy and a continuous [[#Assurance|assurance]] loop that verifies the outcome — turning a programmable network into a self-aligning one. Without the programmability and central control that SDN established, there would be nothing for [[#Activation|activation]] to drive or for assurance to measure.

## Intent-based networking

_The operating model at the centre of Cisco DNA._

Intent-based networking (IBN) captures business intent, translates it into policy, applies that policy across the whole network automatically, and then continuously checks that the network is actually delivering it. Cisco frames this as a closed loop of three functions — [[#Translation|translation]], [[#Activation|activation]], and [[#Assurance|assurance]] — running on top of a programmable infrastructure.

### Translation

_Turning human intent into a consistent policy model._

Translation is the capture and characterisation of intent. The operator expresses what the network should do in declarative terms, and the system converts that into network and security policies. Before anything is deployed, translation checks the new policy against what is already in place, so that contradictory or overlapping intents are caught rather than pushed onto the network.

### Activation

_Applying the policy everywhere, through automation._

Activation interprets the validated policy into device configuration and deploys it network-wide through automation, with pre- and post-checks on each device. It is the step that actually connects to the infrastructure and writes the change. Activation can confirm that the configuration was applied successfully, but it cannot, on its own, confirm that the intent is being met — that is left to assurance.

### Assurance

_Continuously verifying that the network is delivering the intent._

Assurance runs a continuous validation-and-verification loop fed by telemetry from the network. It compares the network's actual behaviour against the expressed intent, raises problems — ideally before they cause an outage — and points toward remediation. Because the infrastructure streams operational data back continuously, assurance closes the loop: a deviation becomes new input that drives correction.

### The closed loop

_How the three functions form a self-correcting cycle._

The functions are not a one-way pipeline; they form a loop. Intent is translated, activated, and run on the network; assurance observes the result and, on a deviation, feeds back into translation or remediation so the network re-converges on the intent. This closed-loop behaviour — the network continuously aligning itself to intent without per-device intervention — is what distinguishes IBN from ordinary scripted automation.

```text
                    ┌───────────────────────────────────────┐
                    │                 INTENT                  │
                    │   business / network outcome ("what")   │
                    └──────────────────┬──────────────────────┘
                                       ▼
                                 TRANSLATION
                          intent → validated policy
                                       ▼
                                  ACTIVATION
                       policy → configuration, network-wide
                                       ▼
                            ┌─────────────────────┐
                            │     THE NETWORK      │
                            │    runs the intent   │
                            └──────────┬───────────┘
                                       │  telemetry
                                       ▼
                                  ASSURANCE
                        verify the intent is being met
                                       │
                        deviation → remediate / re-translate
                                       │
                                       └────────▶ back to INTENT
```

## Guiding principles

_The design tenets that shape every part of the architecture._

Cisco DNA is built on a small set of recurring principles, each of which reappears in the [[#The Cisco DNA architecture|architecture]] below:

- Policy-driven: behaviour is expressed as intent and as policy about groups and outcomes, decoupled from device-level configuration and IP addressing.
- Software-driven and automated: configuration is generated and deployed by software, not typed per device, so change is fast, consistent, and repeatable.
- Insight-driven: the network is treated as a source of data; telemetry and analytics turn that data into visibility and, increasingly, machine-assisted reasoning.
- Secure by design: segmentation and policy are part of the fabric rather than an afterthought, and the network itself acts as both a sensor and an enforcer.
- Open and programmable: open APIs and model-driven interfaces make the architecture extensible and scriptable, so it integrates with the wider IT ecosystem.
- Cloud-ready: the same intent and policy model is meant to extend toward cloud and software-defined WAN rather than stopping at the campus edge.

## The Cisco DNA architecture

_The functional building blocks that turn the principles into a working system._

The architecture is a stack: programmable hardware at the bottom, a controller that abstracts and drives it, a fabric and policy model layered on top, analytics observing the whole thing, and open interfaces exposing it.

### Programmable infrastructure

_The foundation: hardware and software that a controller can drive._

Intent-based networking only works if the underlying devices are programmable. Cisco DNA assumes a foundation of programmable platforms — the Catalyst 9000 family with flexible, reprogrammable ASICs, running IOS-XE with model-driven interfaces (NETCONF, RESTCONF, YANG), on-box programmability, and [[#Model-driven networking and streaming telemetry|streaming telemetry]]. This is what lets the controller both configure devices and receive rich operational data from them.

### The network controller

_The central point that abstracts the network and drives intent into it._

The controller is the brain of the architecture. It holds the intended state of the network as a [[#Abstraction and the single source of truth|single source of truth]], performs [[#Translation|translation]] and [[#Activation|activation]], and orchestrates automation across every managed device. In Cisco DNA this role is filled by [[Cisco DNA Center#Architecture|Cisco DNA Center]] (Catalyst Center), which exposes the design, policy, provisioning, and assurance workflows through which intent is expressed.

### Network fabric

_An overlay that abstracts connectivity from the physical topology._

The fabric is a virtual network built on top of the physical one, so that services, mobility, and policy no longer depend on where a device is cabled. In Cisco DNA this is [[Cisco DNA Center#SD-Access fabric|SD-Access]]. Its conceptual mechanics — the underlay, the overlay, and the separate control, data, and policy planes — are covered under [[#Overlays and the underlay|foundational concepts]].

### Policy and segmentation

_Expressing access and isolation in terms of groups, not addresses._

Policy in Cisco DNA is group-based: endpoints are placed in groups, and policy is written between groups, independent of topology and IP addressing. Macro-segmentation separates whole virtual networks; micro-segmentation separates groups within one. The mechanism — Scalable Group Tags and context — is detailed under [[#Group-based policy and context|foundational concepts]], and its configuration under [[Cisco DNA Center#Group-Based Access Control|group-based access control]].

### Analytics and assurance

_Treating the network as a sensor and reasoning over what it reports._

Every device is a source of telemetry; the architecture treats the network as a distributed sensor and analyses what it reports to score health, detect anomalies against learned baselines, and guide troubleshooting with machine reasoning. This is the data foundation of the [[#Assurance|assurance]] function, realised as [[Cisco DNA Center#Assurance|Catalyst Assurance]].

### Open APIs and the platform

_Making the architecture programmable and extensible from the outside._

The controller is itself programmable through open APIs: a northbound intent API for automation, integration APIs toward IT systems, and a southbound model for managing devices. This is what lets the architecture participate in a larger ecosystem rather than being a closed appliance, and it is documented as the controller's [[Cisco DNA Center#Platform and APIs|platform]] and [[Cisco DNA Center#Intent API|Intent API]].

### Pervasive security

_Security as a property of the whole network, not a bolt-on._

Security in Cisco DNA is woven through the other building blocks rather than added at the edge. Segmentation and group-based policy are themselves security controls; the network acts as an enforcer of those policies and as a sensor for threats. Encrypted Traffic Analytics, for example, infers malicious activity from the metadata and behavioural patterns of encrypted flows without decrypting them, so visibility does not require breaking confidentiality.

## Foundational concepts

_The conceptual mechanisms the architecture rests on._

These are the ideas that make the building blocks behave the way they do.

### Abstraction and the single source of truth

_Operating on a model of the network instead of on individual devices._

The central abstraction of Cisco DNA is that the network is one system with a single, controller-held model of intended state. Operators work with high-level objects — sites, address pools, policies, groups — and the controller renders those into device configuration. Because intended state lives in one place, consistency and verification become possible: the controller knows what every device should look like and can detect when it does not.

### Overlays and the underlay

_Why connectivity is virtualised, and the planes that make it work._

A fabric separates the network into two layers. The underlay is the physical, routed IP transport whose only job is to move packets between devices reliably. The overlay is a virtual network of tunnels carried over the underlay, and it is where user traffic, segmentation, and policy actually live. The value of the split is that services and policy become independent of physical topology — an endpoint keeps its addressing and policy as it moves, and segmentation no longer depends on VLAN boundaries. Three planes cooperate:

- Control plane: tracks which endpoint is located where (in SD-Access, LISP).
- Data plane: encapsulates and carries user traffic across the underlay (VXLAN).
- Policy plane: carries group identity alongside the traffic so policy can be enforced anywhere (Cisco TrustSec and the Scalable Group Tag).

### Group-based policy and context

_Policy that follows the user, derived from who and what rather than where._

Group-based policy decouples access rules from addresses: an endpoint is assigned to a group, and policy is written between groups. The group assignment is driven by context — the identity of the user or device established at authentication, the device type, the location, the application, and the time. Because policy is expressed in terms of groups and follows the endpoint through the [[#Overlays and the underlay|overlay]], the same intent holds wherever the endpoint connects, which is what makes consistent segmentation and zero-trust-style enforcement practical at scale.

### Model-driven networking and streaming telemetry

_Structured interfaces for configuration, and a continuous push of operational state._

Cisco DNA depends on devices being model-driven: their configuration and operational state are described by structured data models (YANG) and accessed programmatically through NETCONF, RESTCONF, and gNMI rather than scraped from CLI output. For observability it relies on streaming, model-driven telemetry, where devices push selected operational data continuously by subscription instead of the controller polling SNMP at intervals. The result is data that is more granular, more timely, and more scalable to collect — which is precisely what the [[#Assurance|assurance]] closed loop needs to verify intent in near real time.