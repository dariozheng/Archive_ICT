---
categories:
  - "[[Security]]"
  - "[[Privacy]]"
topic@security:
  - "[[VPN]]"
topic@privacy:
  - "[[Privacy General]]"
tags:
  - claude
  - vpn
  - category/privacy/privacy_general
  - category/security/vpn
icon: SiWireguard
iconColor: "#87151F"
last_update: 2026-07-09
---

<strong>WireGuard</strong> is a fast, modern VPN that runs as a <strong>virtual network interface</strong> in the Linux kernel, mainline since 5.6 (with portable userspace implementations such as wireguard-go and BoringTun for other platforms).

It builds an encrypted tunnel out of a small, fixed set of cryptographic primitives, identifies every participant by a public key rather than a username or certificate, and decides where packets go with a single mechanism — <strong>cryptokey routing</strong> — that doubles as its access-control model.

You drive it with two userspace tools, `wg` and `wg-quick`, and everything around the tunnel — <strong>routing between interfaces</strong>, <strong>NAT</strong> and <strong>filtering</strong> — is left to the kernel and to [[nftables]].

> [!info] WireGuard moves packets; the kernel routes them 
> 
> WireGuard only encrypts packets into, and decrypts them out of, a [[#The Tunnel Interface|tunnel interface]].
> 
> Forwarding between that interface and the rest of the network, [[Netfilter#Network Address Translation|NAT]], and filtering are the kernel's job, driven by [[nftables]]. The firewall rules that turn a WireGuard host into a gateway are the [[nftables#WireGuard Gateway|WireGuard gateway recipe]]; this note covers everything on the WireGuard side of that line — keys, peers, [[#AllowedIPs|AllowedIPs]], the [[#The Cryptographic Handshake|handshake]] and the [[#Configuration|configuration]].

---

# The WireGuard Model

_The three nouns everything else is built from: an interface, its keys, and the peers it talks to._

WireGuard's entire object model is small. A host has <mark style="background: #FFB8EBA6;">one or more tunnel interfaces</mark>; <mark style="background: #FFB86CA6;">each interface owns a single key pair and a list of peers</mark>; <mark style="background: #FFF3A3A6;">each peer is identified by its public key</mark> and carries the handful of attributes needed to reach it and to decide which traffic belongs to it. There are no connections, sessions or users to manage as first-class objects — those exist only inside the protocol and are created and torn down automatically.

## The Tunnel Interface

_A virtual network interface that happens to encrypt._

A <mark style="background: #FF5582A6;">WireGuard tunnel</mark> is a <mark style="background: #FF5582A6;">network interface</mark>, conventionally named `wg0`, `wg1` and so on.

To the rest of the system it behaves like any other interface: it has an IP address, it appears in the [[Routing|routing]] table, and packets routed to it are sent, while packets it receives are delivered up the stack.

The difference is hidden inside: <mark style="background: #FFF3A3A6;">on transmit it encrypts each packet and wraps it in UDP</mark> to a peer; on receive it decrypts and unwraps.

Because it is an ordinary interface, <mark style="background: #D2B3FFA6;">it lives in exactly one</mark> [[Netfilter#Network Namespaces|network namespace]] <mark style="background: #D2B3FFA6;">at a time</mark> and <mark style="background: #CACFD9A6;">is filtered by matching its name in</mark> [[nftables]], exactly like a physical NIC.

Unlike a TCP-based VPN, the interface is connectionless and always "up" once configured. There is no dial sequence and no persistent socket to a server; the interface simply sends an encrypted UDP datagram whenever it has a packet for a peer, and a [[#The Cryptographic Handshake|handshake]] happens on demand the first time keys are needed.

## Keys

_A Curve25519 key pair per interface; the public half is the identity._

Each interface has one private key and the public key derived from it, using Curve25519. <mark style="background: #BBFABBA6;">The private key is a secret known only to that host</mark>; <mark style="background: #ABF7F7A6;">the public key is shared with every peer that needs to talk to the interface</mark>. <mark style="background: #FF5582A6;">Identity</mark> in WireGuard is nothing more than this <mark style="background: #FF5582A6;">public key</mark> — there is no separate username, certificate or account.

A peer that holds your public key, and whose own public key you have configured, is authorized to exchange traffic; anyone else is ignored.

Keys are 32 raw bytes, normally handled in their 44-character base64 encoding.

### Generating Keys

The `wg` tool generates keys. A private key is produced on its own, and the public key is derived from it on demand:

```bash
wg genkey | tee privatekey | wg pubkey > publickey
```

`wg genkey` emits a new private key, `tee` saves it, and `wg pubkey` reads a private key on standard input and writes the matching public key.

Because the private key is a secret, set a restrictive umask first so the file is not world-readable:

```bash
umask 077
wg genkey > privatekey
wg pubkey < privatekey > publickey
```

### Pre-shared Keys

In addition to the per-interface key pair, any pair of peers may share an optional pre-shared key — a 32-byte symmetric secret generated with `wg genpsk`.

It is mixed into the [[#The Noise Handshake|handshake]] <mark style="background: #FFB8EBA6;">as an extra layer on top of the public-key cryptography</mark>.

Its purpose is defense in depth: even if Curve25519 were broken in the future, traffic recorded today could not be decrypted without also having the pre-shared key, which makes it a practical hedge against later cryptographic advances (see [[#Key Management|key management]]). It is symmetric, so the same value is configured on both ends of the pair.

## Peers

_The remote endpoints an interface will talk to, each keyed by its public key._

A peer is a remote WireGuard interface this one is configured to communicate with.

Each peer entry carries its public key (which identifies it), the set of addresses that belong to it ([[#AllowedIPs|AllowedIPs]]), optionally where to reach it on the underlying network (its [[#Endpoints|endpoint]]), optionally a [[#Pre-shared Keys]], and optionally a [[#Persistent Keepalive|keepalive]] interval.

An interface may have one peer (a point-to-point link) or many (a server with many clients).

### Endpoints

_The real network address where a peer's encrypted packets are sent._

The endpoint is the peer's address and UDP port on the underlying network — the actual IP and port the encrypted datagrams travel to, as opposed to the tunnel-internal address that traffic appears to come from. It is written as `host:port`, for example `vpn.example.com:51820`.

An endpoint is only required for peers this host needs to initiate contact with. A central server typically configures no endpoint for its roaming clients, because their addresses are unknown and change; instead it learns each client's current endpoint automatically from the source of that client's authenticated packets (see [[#Roaming|roaming]]). A client, by contrast, must configure the server's endpoint so it knows where to send the first packet.

When the endpoint is written as a hostname it is resolved once, when the tunnel comes up, and not re-resolved afterwards, so an endpoint on dynamic DNS needs a periodic re-resolve (see [[#Troubleshooting|troubleshooting]]).

### AllowedIPs

_The list of addresses associated with a peer — the heart of WireGuard's routing and access control._

AllowedIPs is a list of IP prefixes that are considered to belong to a peer. It is the single most important concept in WireGuard and does two jobs at once — selecting the peer for outbound packets and authorizing the source of inbound ones. Because that dual role is what makes WireGuard distinctive, it has its own section: see [[#Cryptokey Routing|cryptokey routing]].

### Persistent Keepalive

_An authenticated heartbeat that keeps a NAT or firewall mapping open._

WireGuard is silent by design: with no traffic to send, it sends nothing. That is ideal for stealth but breaks down behind [[#NAT Traversal|NAT]], where the mapping that lets return packets back in expires after a period of silence. Persistent keepalive makes the interface send a small authenticated empty packet to a peer every N seconds (25 is the usual value) so the mapping never lapses. It is off by default and is normally set only on the side that sits behind NAT, pointing at the peer that has a stable public endpoint.

---

# Cryptokey Routing

_How [[#AllowedIPs|AllowedIPs]] binds public keys to address ranges, serving as routing table and access-control list in one._

<strong>Cryptokey routing</strong> is the idea that gives WireGuard its name and its simplicity: the association between a peer's public key and the set of IP addresses allowed to travel to and from that key. Each peer's [[#AllowedIPs|AllowedIPs]] is consulted in two directions, and understanding both is the key to configuring WireGuard correctly.

![[wireguard-cryptokey-routing.png]]

## Outbound: Choosing a Peer

When the interface has a packet to send, it looks at the packet's destination address and finds the peer whose AllowedIPs contains it, using a longest-prefix match exactly as an ordinary routing table would. That peer's key encrypts the packet, and the result is sent to that peer's [[#Endpoints|endpoint]]. If no peer's AllowedIPs matches the destination, the packet has nowhere to go and is dropped. In this direction AllowedIPs behaves like a routing table indexed by public key.

## Inbound: Authorizing a Source

When an encrypted packet arrives and is successfully decrypted with a given peer's keys, <strong>WireGuard</strong> checks the <mark style="background: #FF5582A6;">source address</mark> of the inner packet against that same <mark style="background: #FF5582A6;">peer's AllowedIPs</mark>. If the source is not inside the set, the packet is discarded. This stops a peer from injecting traffic that claims to come from an address it has no right to use — a peer can only send packets sourced from within its own AllowedIPs. <mark style="background: #FFF3A3A6;">In this direction the same list behaves like an inbound access-control list bound to the peer's identity</mark>.

> [!warning] Broad AllowedIPs widens both doors 
> 
> Because the one list both routes outbound traffic and authorizes inbound sources, a wide AllowedIPs does more than send more traffic to a peer — it also lets that peer send packets claiming any source address within the range. <strong>On a server, keep each client's AllowedIPs as tight as its real addresses, usually a single</strong> `/32` or `/128`. Reserve broad ranges like `0.0.0.0/0` for the trusted upstream peer <strong>on a client</strong>, <strong>never for arbitrary clients on a server</strong>.

## One Address, One Peer

Because outbound selection is a routing lookup, a given address can belong to only one peer on an interface: if two peers both claimed `10.0.0.5`, the interface could not decide which to send to. Overlapping prefixes resolve by longest match, just like routes, so a peer with `0.0.0.0/0` catches everything not claimed more specifically by another peer. That `0.0.0.0/0, ::/0` case — routing all traffic to a single peer — is how a full-tunnel VPN is expressed; its routing-table consequences are covered in [[#Full-Tunnel Routing|full-tunnel routing]].

> [!important] AllowedIPs is not the same as the kernel routing table 
> 
> AllowedIPs is WireGuard's own internal map of keys to addresses. For the operating system to actually hand outbound packets to the tunnel in the first place, there must also be a normal route pointing those destinations at the `wg` interface. [[#wg-quick|wg-quick]] creates those system routes automatically from each peer's AllowedIPs, which is why the two are easy to conflate — but the bare [[#wg|wg]] tool sets only the internal map and leaves kernel routing to you.

## A Worked Example

_One hub, two peers — following a packet each way._

Take a hub at `10.0.0.1` with two peers: a laptop whose `AllowedIPs` is `10.0.0.2/32`, and a branch router whose `AllowedIPs` is `10.0.0.3/32, 192.168.50.0/24`.

Outbound, the hub has a packet for `192.168.50.10`. It matches each peer's list against the destination address: it is not in `10.0.0.2/32` and not in `10.0.0.3/32`, but it is inside `192.168.50.0/24` — so the branch router is chosen. The packet is encrypted with the router's key and sent to its endpoint, and the router decrypts it and forwards it onto its LAN. A packet for `10.0.0.2` instead matches the laptop's `/32`.

Inbound, a packet arrives and decrypts with the branch router's key; its inner source address is `192.168.50.10`. That address is inside the router's AllowedIPs, so the packet is accepted. Had the inner source been an address the router has no claim to, it would be dropped even though it decrypted correctly — the same list that selected the peer outbound now authorizes what that peer may send inbound.

So AllowedIPs is read against the destination on the way out and against the source on the way in.

### What a Peer's Range Means

_A single host versus a gateway for a whole network._

The size of a peer's prefix says what that peer stands for. A `/32` (or `/128` for [[IPv6]]) is a single host — a laptop, a phone, one machine's tunnel address — that speaks only for itself. A whole subnet like `192.168.50.0/24` means the peer is the gateway for that network: anything destined into the range is sent to that peer, which forwards it to the real hosts behind it, as in a [[#Site-to-Site|site-to-site]] link or a [[#Hub-and-Spoke and Mesh|hub]] routing for its spokes.

The distinction describes what is reachable through the peer, not what kind of machine it is. A central VPN server is not marked as such by its own AllowedIPs — from the server's side every client is a `/32`; it is from the client's side that the server appears as `0.0.0.0/0` (a [[#Full-Tunnel Routing|full tunnel]]) or as the server's subnets (a [[#Split Tunneling|split tunnel]]). The same host can be a `/32` to one peer and a subnet gateway to another.

---

# The Cryptographic Handshake

_Establishing session keys over the Noise protocol, with forward secrecy and silence by default._

Before any data flows between two peers, they perform a brief handshake that authenticates each side and derives the symmetric keys used to encrypt traffic. It happens automatically and on demand — the first time the interface has a packet for a peer with no live session — and repeats periodically for as long as traffic continues.

## The Noise Handshake

_A one-round-trip exchange based on the Noise framework's IK pattern._

WireGuard's handshake is built on the Noise protocol framework, using its IK pattern with the optional pre-shared-key mixing — formally `Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s`. It is a one-round-trip exchange: the initiator sends a handshake initiation, the responder sends a handshake response, and after those two messages both sides have derived the shared pair of session keys. The initiator may then send transport data immediately; the responder, however, holds off until the initiator's first transport packet arrives — which implicitly confirms the response was received — before sending data of its own.

```
Initiator                                    Responder
    │                                            │
    │ ── Handshake Initiation (type 1) ────────▶ │  responder identifies the
    │    initiator's ephemeral key, encrypted    │  initiator (a configured peer)
    │    static identity, timestamp              │  and derives keys
    │                                            │
    │ ◀── Handshake Response (type 2) ────────── │  responder's ephemeral key,
    │     empty authenticated payload            │  empty payload
    │                                            │
    │ ═══ session established — 1-RTT ══════════ │
    │                                            │
    │ ── Transport Data (type 4) ──────────────▶ │  initiator may send at once
    │ ◀── Transport Data (type 4) ────────────── │  responder sends only after
    │                                            │  the initiator's first packet
```

Each handshake generates fresh ephemeral keys that are combined with the long-term static keys, so every session has its own keys that cannot be recovered from the static private key alone. This is what gives WireGuard forward secrecy: compromising a host's private key does not expose traffic from past sessions. The initiator also proves liveness with a timestamp (a TAI64N value), which the responder uses to reject replayed initiations.

## Session Lifetime and Rekeying

_Short-lived keys, renewed roughly every two minutes of active use._

Session keys are deliberately short-lived. A new handshake is started once a session is about two minutes old (or after a large number of messages), and a session is rejected outright once it passes roughly three minutes without renewal. Rekeying is driven by data: as long as packets are flowing, the initiator quietly performs a fresh handshake in the background before the current keys expire, so there is no interruption. When traffic stops, handshakes stop too, and the session is simply allowed to lapse. The frequent rotation keeps the window of any single set of keys small and continually refreshes forward secrecy.

## Roaming

_Endpoints follow peers across address changes, learned from authenticated traffic._

A peer's [[#Endpoints|endpoint]] is not fixed for the life of the configuration. Whenever an authenticated packet arrives from a peer, WireGuard updates its record of that peer's endpoint to the packet's source address and port. This is roaming: a laptop that moves from Wi-Fi to a mobile network, or whose NAT mapping changes, keeps working without reconfiguration, because the server simply starts replying to wherever the client's latest valid packet came from. Authentication is what makes this safe — only a packet that decrypts correctly can move an endpoint, so an attacker cannot redirect a peer's traffic by spoofing a source address.

## Cookies and Denial-of-Service Resistance

_Proving willingness to respond before the responder commits expensive work._

Public-key operations are costly, so an attacker who could force a responder to perform them for every spoofed initiation could exhaust its CPU. WireGuard defends against this with a cookie mechanism. Under load, instead of processing an initiation a responder may reply with a cookie tied to the sender's source address; a legitimate initiator includes a MAC derived from that cookie in its next handshake message, proving it can actually receive packets at the address it claims. Because a spoofed source cannot receive the cookie, it cannot complete the exchange, and the responder spends its expensive cryptography only on senders that have demonstrated a real return path. This works together with WireGuard's general [[#Silence and Stealth|silence]] toward unauthenticated traffic.

---

# Packet Flow and Encapsulation

_How a packet is wrapped, sent over UDP and unwrapped, and where it meets the kernel firewall._

A packet bound for the VPN is an ordinary IP packet until it reaches the tunnel interface. There it becomes the payload of an encrypted UDP datagram addressed between the two hosts' real addresses; on the far side the datagram is decrypted back into the original inner packet and injected into that host's stack. Two packets are therefore in play at once: the inner packet (tunnel addresses, what the application sees) and the outer packet (real addresses, what the network sees).

```
SEND                                          RECEIVE
application writes inner packet               outer UDP datagram arrives on eth0
        │                                             │
   routing: dest -> wg0                          wg0 decrypts, checks source
        ▼                                        against the peer's AllowedIPs
wg0: pick peer by AllowedIPs,                         │
     encrypt, wrap in UDP                        routing: deliver inner packet
        ▼                                             ▼
   routing: outer dest -> eth0                   local socket, or forward out
        ▼
   eth0 -> wire (UDP to peer endpoint)
```

## The Encrypted Outer Packet

_A single UDP port carries every peer's traffic._

On the wire WireGuard is UDP, by default on port 51820, and that is all an observer sees of the contents: UDP datagrams between two addresses, with an encrypted payload and no visible indication of the protocol carried inside. A single listen port serves every peer at once — peers are told apart by the keys their packets decrypt with, not by separate ports or connections. Each data packet carries a monotonic counter as its nonce, and the receiver keeps a sliding window of recently seen counters to reject replays and badly reordered packets, the same anti-replay scheme IPsec uses. Running over a single UDP flow, with no cleartext handshake for a middlebox to key on and no reply to anything unauthenticated, is what lets WireGuard [[#Roaming|roam]] and stay invisible to active probing — though not, as [[#Silence and Stealth|Silence and Stealth]] describes, to passive traffic analysis.

## Interaction with the Network Stack

_The firewall sees the inner and outer packets at different interfaces._

WireGuard's <mark style="background: #FF5582A6;">encryption</mark> and <mark style="background: #FF5582A6;">decryption</mark> <mark style="background: #FFB86CA6;">happen inside the interface's own transmit and receive path</mark>, not at a [[Netfilter]] hook, so to the firewall the `wg` interface is simply another interface whose traffic traverses the normal [[Netfilter#Hooks and Packet Flow|hooks]]. <mark style="background: #FFF3A3A6;">The consequence is that the two packets are filtered at two different places</mark>:

- The outer, <mark style="background: #FF5582A6;">encrypted</mark> UDP packets traverse the hooks on the physical interface (`eth0`). <mark style="background: #FFB8EBA6;">You permit the tunnel itself by allowing its listen port there, with</mark> `udp dport 51820`.
- The inner, <mark style="background: #FF5582A6;">decrypted</mark> packets traverse the hooks with the <strong>`wg` interface</strong> <strong>as their input or output interface</strong>. <mark style="background: #ABF7F7A6;">You filter VPN traffic</mark> — what peers may reach, and what they may route through —<mark style="background: #ABF7F7A6;"> by matching</mark> `iifname "wg0"` and `oifname "wg0"`.

[[Netfilter#Connection Tracking|Conntrack]] tracks the two independently: <mark style="background: #FFB8EBA6;">the outer UDP flow is one tracked connection on `eth0`</mark>, <mark style="background: #ADCCFFA6;">and each inner flow is tracked separately as it crosses the `wg` interface</mark>. This split is exactly what the [[nftables#WireGuard Gateway|gateway recipe]] relies on — one rule opens the outer listen port, another governs the inner forwarded traffic — and it is why a working tunnel can still fail to route until both halves are permitted.

---

# Configuration

_The wg-quick configuration file: one interface section and one section per peer._

WireGuard is configured through a small INI-style file, conventionally `/etc/wireguard/wg0.conf`, whose name (minus the extension) becomes the interface name. The file has one `[Interface]` section describing the local end, followed by one `[Peer]` section for each remote end.

## The Configuration File

_An INI file split into [Interface] and [Peer] sections._

Two layers share this file.

A core set of directives is understood by the [[#wg|wg]] tool itself and configures the protocol: in `[Interface]`, the private key, listen port and firewall mark; in `[Peer]`, the public key, pre-shared key, allowed IPs, endpoint and keepalive.

A second set — addressing, DNS, MTU, routing table and lifecycle hooks — is understood only by [[#wg-quick|wg-quick]], the wrapper that sets up everything around the protocol.

The distinction matters when configuring WireGuard by hand without wg-quick, because the wg-quick-only directives are then yours to perform yourself.

## The Interface Section

_The local end: who this host is and how its tunnel should be set up._

### Identity and Addressing

- `PrivateKey` — this interface's private [[#Keys|key]]. Required, and understood by `wg`.
- `Address` — the tunnel-internal IP address (or addresses) to assign to the interface, in CIDR form, e.g. `10.0.0.1/24`. A wg-quick directive; with the bare tool you assign the address with `ip address` instead.
- `ListenPort` — the UDP port to listen on, e.g. `51820`. Optional; if omitted the kernel picks a random port, which is normal for a client that only ever initiates.

### DNS and MTU

- `DNS` — resolver(s), and optionally search domains, to use while the tunnel is up. A wg-quick directive, applied through the system's resolver integration; common on full-tunnel clients so name resolution also goes through the VPN.
- `MTU` — the tunnel interface MTU. Optional; if omitted, wg-quick derives it from the route to the [[#Endpoints|endpoint]] (see [[#MTU and MSS|MTU and MSS]]).

### Routing Controls

- `Table` — which routing table wg-quick should install the peers' routes into. `Table = off` disables automatic route creation entirely, leaving routing to you; a numeric value directs routes into a custom table. A wg-quick directive.
- `FwMark` — a [[Netfilter#Packet and Connection Marks|firewall mark]] <mark style="background: #FFB8EBA6;">to stamp on this interface's outgoing encrypted packets</mark>, <mark style="background: #FFB86CA6;">so they can be singled out by</mark> [[Netfilter#Marks and Policy Routing|policy routing]]. Understood by `wg`; wg-quick sets it automatically when it needs it for [[#Full-Tunnel Routing|full-tunnel routing]].

### Lifecycle Hooks

- `PreUp`, `PostUp`, `PreDown`, `PostDown` — arbitrary shell commands wg-quick runs before and after bringing the interface up or down. This is where the [[nftables#WireGuard Gateway|masquerade and forward rules]] for a gateway are commonly placed, tying them to the interface's lifecycle. A wg-quick directive.
- `SaveConfig` — when true, wg-quick writes the live configuration (including any runtime changes, such as learned endpoints) back to the file when the interface goes down. A wg-quick directive.

## The Peer Section

_A remote end: its identity, the addresses it owns, and how to reach it._

### Identifying the Peer

- `PublicKey` — the peer's public [[#Keys|key]]. Required; this is the peer's identity.
- `PresharedKey` — the optional symmetric [[#Pre-shared Keys|pre-shared key]] shared with this peer. The directive is one word; only the prose name is hyphenated.
- `AllowedIPs` — the prefixes that belong to this peer, the basis of [[#Cryptokey Routing|cryptokey routing]]. Required; a comma-separated list such as `10.0.0.2/32` for a single client, or `0.0.0.0/0, ::/0` to route everything to this peer.

### Endpoint and Keepalive

- `Endpoint` — where to send this peer's encrypted packets, as `host:port`. Optional; omitted for roaming peers whose [[#Endpoints|endpoint]] is learned from their traffic.
- `PersistentKeepalive` — seconds between [[#Persistent Keepalive|keepalive]] packets, e.g. `25`. Optional; set on a peer that sits behind NAT.

## A Complete Example

_A server and one client, shown as a matching pair._

A server offering its clients access to a `10.0.0.0/24` VPN subnet, listening on the standard port:

```bash
# /etc/wireguard/wg0.conf — server
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <server-private-key>

[Peer]
# a laptop
PublicKey = <laptop-public-key>
AllowedIPs = 10.0.0.2/32
```

The matching client, configured to reach the server and to send all of its traffic through the tunnel:

```bash
# /etc/wireguard/wg0.conf — client
[Interface]
Address = 10.0.0.2/24
PrivateKey = <laptop-private-key>
DNS = 10.0.0.1

[Peer]
PublicKey = <server-public-key>
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

The server lists the client's tunnel address as its [[#AllowedIPs|AllowedIPs]] and needs no endpoint for it (it learns one when the client connects). The client lists `0.0.0.0/0, ::/0` to route everything through the server (a full tunnel), gives the server's endpoint, and sets a keepalive because it is likely behind NAT. For the server to actually forward this traffic to the internet it still needs the kernel-side plumbing in [[#Routing, NAT and Firewalling|routing, NAT and firewalling]].

---

# Tools and Operation

_The two userspace tools — wg for the protocol, wg-quick for the plumbing — and bringing a tunnel up._

WireGuard ships with two commands, from the `wireguard-tools` package. `wg` configures the protocol on an interface that already exists; `wg-quick` is a wrapper that creates the interface, applies the configuration, and sets up the surrounding addressing, routing and DNS in one step. Besides these, network managers such as systemd-networkd and NetworkManager can configure WireGuard interfaces natively through the same kernel module, which is the usual choice on systems already managed that way (see [[#Managing with systemd-networkd|systemd-networkd]]).

## wg

_The low-level tool: it configures the protocol, nothing more._

`wg` operates on an existing WireGuard interface and deals only with keys, ports, peers and their attributes. It does not create interfaces, assign addresses or touch routing.

```bash
wg show                       # summarize all interfaces and peers
wg show wg0                   # one interface in detail
wg show wg0 latest-handshakes # per-peer time of last handshake
wg show wg0 transfer          # per-peer bytes sent and received
wg showconf wg0               # dump the interface's config (includes the private key)

wg genkey                     # generate a private key
wg pubkey                     # derive a public key from a private key on stdin
wg genpsk                     # generate a pre-shared key

# set fields directly on a running interface
wg set wg0 listen-port 51820 private-key ./privatekey
wg set wg0 peer <pubkey> endpoint 203.0.113.7:51820 allowed-ips 10.0.0.2/32   # allowed-ips replaces this peer's list
wg set wg0 peer <pubkey> remove          # delete a peer

wg setconf wg0 wg0.conf       # replace the whole config from a file
wg syncconf wg0 wg0.conf      # apply changes without disturbing live sessions
```

> [!note] setconf resets, syncconf does not 
> 
> `wg setconf` makes the interface match the file exactly, removing peers not listed and resetting affected sessions. `wg syncconf` applies only the differences, so unchanged peers keep their current [[#The Cryptographic Handshake|handshake]] and sessions stay up — the right choice for editing a live ruleset. `syncconf` expects a config with the [[#wg-quick|wg-quick]]-only directives stripped, which `wg-quick strip wg0` produces.

`wg show` never prints private or pre-shared keys; only `wg showconf` does, so it should be treated as sensitive.

## wg-quick

_The high-level wrapper: interface, addresses, routes and DNS in one command._

`wg-quick up` reads a configuration file and does everything needed to make the tunnel usable: it creates the interface, assigns the `Address`, applies the protocol settings with `wg`, installs routes for every peer's [[#AllowedIPs|AllowedIPs]], sets the `MTU` and `DNS`, and runs the `PostUp` hooks. `wg-quick down` reverses all of it. Given a bare interface name it looks the file up in `/etc/wireguard`.

```bash
wg-quick up wg0               # bring up using /etc/wireguard/wg0.conf
wg-quick down wg0             # tear it down
wg-quick strip wg0            # print the config with wg-quick-only keys removed
wg-quick save wg0             # write the live config back to the file
```

The route installation is the important part: it is what bridges WireGuard's internal [[#Cryptokey Routing|cryptokey routing]] to the kernel routing table, so the system actually sends matching destinations to the tunnel. For the default-route case it does something more elaborate, described in [[#Full-Tunnel Routing|full-tunnel routing]].

## Bringing a Tunnel Up by Hand

_The manual equivalent of wg-quick, for when you want explicit control._

Without wg-quick, you assemble the tunnel from `ip` and `wg`. This is what wg-quick automates, and it is worth knowing for custom routing or namespaced setups.

```bash
ip link add dev wg0 type wireguard            # create the interface
wg set wg0 private-key ./privatekey listen-port 51820 \
    peer <pubkey> allowed-ips 10.0.0.2/32 endpoint 203.0.113.7:51820
ip address add 10.0.0.1/24 dev wg0            # assign the tunnel address
ip link set wg0 up                            # bring it up
ip route add 10.0.0.0/24 dev wg0              # route the VPN subnet into the tunnel
```

A tunnel interface can also be moved into another [[Netfilter#Network Namespaces|network namespace]] after creation — the basis of [[#WireGuard in a Network Namespace|running it in an isolated namespace]], where the encrypted packets still exit through the host's network.

## WireGuard in a Network Namespace

_Isolating the tunnel so a namespace can reach the network only through it._

A WireGuard interface remembers the [[Netfilter#Network Namespaces|network namespace]] it was created in and keeps its encrypted UDP socket there for the life of the interface, even after the interface itself is moved elsewhere.

Moving the cleartext side of the tunnel into a second namespace while the encrypted side stays in the first produces a powerful arrangement: processes in the second namespace can reach the network only through the tunnel, yet the encryption still egresses through the first namespace's real connection.

![[wireguard-network-namespaces.png]]

The interface is created in the init namespace — which has internet access — and then moved into a dedicated namespace whose only route is the tunnel:

```bash
ip netns add vpn                                       # create the namespace
ip link add wg0 type wireguard                         # created in init -> its socket stays here
ip link set wg0 netns vpn                              # move the interface into vpn
ip -n vpn addr add 10.0.0.2/32 dev wg0                 # tunnel address, inside vpn
ip netns exec vpn wg setconf wg0 <(wg-quick strip wg0) # keys and peers (wg-quick-only keys removed)
ip -n vpn link set wg0 up
ip -n vpn route add default dev wg0                    # wg0 is the only way out of vpn
ip netns exec vpn curl https://example.com             # run something inside the namespace
```

Because the namespace holds no other interface, this is a killswitch by construction: if the tunnel drops, nothing inside has a path to the network, so no traffic can leak onto the underlying link.

Two details are easy to miss — DNS in a namespace is read from `/etc/netns/vpn/resolv.conf` rather than the global file, and each namespace is unfirewalled until you load rules into it. This is also how a container's traffic can be forced entirely through WireGuard: hand the container the namespace as its own.

## Running as a Service

_Persisting a tunnel across reboots with systemd._

The packaged `wg-quick@.service` template ties an interface's lifecycle to systemd, reading the matching file from `/etc/wireguard`:

```bash
systemctl enable --now wg-quick@wg0           # start now and on every boot
systemctl status wg-quick@wg0
```

## Managing with systemd-networkd

_Configuring the same tunnel declaratively, without wg-quick._

On hosts already managed by systemd-networkd, the tunnel can be described in a `.netdev` (the interface and its protocol settings) and a `.network` (its addresses and routes), with no wg-quick involved:

```ini
# /etc/systemd/network/wg0.netdev
[NetDev]
Name = wg0
Kind = wireguard

[WireGuard]
PrivateKey = <server-private-key>
ListenPort = 51820

[WireGuardPeer]
PublicKey = <peer-public-key>
AllowedIPs = 10.0.0.2/32
Endpoint = vpn.example.com:51820
PersistentKeepalive = 25
```

```ini
# /etc/systemd/network/wg0.network
[Match]
Name = wg0

[Network]
Address = 10.0.0.1/24
```

Each peer is a separate `[WireGuardPeer]` section. The `[WireGuard]` and `[WireGuardPeer]` keys mirror the [[#The Interface Section|interface]] and [[#The Peer Section|peer]] directives of a wg-quick file, while addressing and routing move into the `.network` file. For secrets, `PrivateKeyFile` can point at a file instead of inlining the key. NetworkManager offers an equivalent through its own WireGuard connection type.

## Inspecting a Running Tunnel

_Reading peer state, handshake age and transfer counters._

`wg show` is the primary diagnostic. For each peer it reports the current [[#Endpoints|endpoint]], the configured [[#AllowedIPs|allowed IPs]], the time of the latest [[#The Cryptographic Handshake|handshake]], and the bytes transferred each way.

```bash
wg show wg0
```

The latest-handshake time is the quickest health check: a recent timestamp means keys are live and traffic is being exchanged, while a handshake that never appears points at the outer UDP packets not arriving — a closed listen port on the [[Netfilter#Hooks and Packet Flow|firewall]], a wrong [[#Endpoints|endpoint]], or NAT in the way. A handshake that succeeds but no inner traffic flowing instead points at [[#AllowedIPs|AllowedIPs]], routing or the [[#Routing, NAT and Firewalling|forward and NAT rules]].

---

# Routing, NAT and Firewalling

_Turning a host into a gateway: forwarding, masquerade, the full-tunnel route trick, and MTU._

WireGuard moves packets in and out of its interface and stops there.

Everything that makes a host a useful gateway — routing the decrypted packets onward, translating their addresses, and filtering them — is ordinary kernel networking, configured with `sysctl`, `ip` and [[nftables]]. This is the same boundary the nftables note draws around its [[nftables#WireGuard Gateway|gateway recipe]]; the points below are the WireGuard-side context for it.

## Forwarding and Masquerade

_Letting peers reach beyond the tunnel._

For a host to forward traffic between its `wg` interface and another interface, kernel IP forwarding must be enabled, exactly as for any [[nftables#NAT Gateway|router]]:

```bash
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1
```

If the peers' tunnel addresses are private and need to reach the internet, the gateway also [[Netfilter#Masquerade|masquerades]] their traffic onto its public address as it leaves the upstream interface. The forward and masquerade rules belong in [[nftables]] — see the [[nftables#WireGuard Gateway|WireGuard gateway recipe]] — and are often attached to the interface through wg-quick's [[#Lifecycle Hooks|PostUp and PostDown]] hooks. With globally routable IPv6 addresses on the tunnel there is usually [[Netfilter#No NAT by Default|no masquerade]] at all — the gateway simply forwards — so inbound protection there falls entirely to the [[Netfilter#Forward|forward]] filter rather than to the side effect of an address translation.

WireGuard itself has no masquerade or NAT directive: `wg` and the configuration file describe only the tunnel, and the translation is the kernel's job. So the rule lives either in a persistent [[nftables]] ruleset or, for a self-contained tunnel, in the [[#Lifecycle Hooks|PostUp and PostDown]] hooks, where `%i` expands to the interface name. A clean nftables form creates a dedicated table on the way up and drops it on the way down:

```bash
# server [Interface] — masquerade tunnel traffic out the WAN (eth0)
PostUp   = nft add table inet wg0
PostUp   = nft add chain inet wg0 postrouting '{ type nat hook postrouting priority srcnat; }'
PostUp   = nft add rule  inet wg0 postrouting oifname "eth0" masquerade
PostDown = nft delete table inet wg0
```

The single `nft delete table inet wg0` on `PostDown` removes everything the `PostUp` lines added. The same thing with the older iptables tooling is the form seen in most tutorials:

```bash
PostUp   = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
```

In both, `eth0` is the upstream (WAN) interface, forwarding must already be enabled as shown above, and filtering of the forwarded traffic still belongs in the main [[nftables]] ruleset.

## Full-Tunnel Routing

_Sending all of a client's traffic through the VPN without a routing loop._

Setting a peer's [[#AllowedIPs|AllowedIPs]] to `0.0.0.0/0, ::/0` declares that all traffic should go to that peer. The obvious implementation — a default route pointing at the tunnel — creates a loop: <mark style="background: #FFB8EBA6;">WireGuard's own encrypted packets</mark>, <mark style="background: #FFF3A3A6;">on their way to the peer's real [[#Endpoints|endpoint]]</mark>, <mark style="background: #FFB86CA6;">would themselves match the default route and be sent back into the tunnel</mark>.

[[#wg-quick|wg-quick]] solves this with a [[Netfilter#Packet and Connection Marks|firewall mark]] and [[Netfilter#Marks and Policy Routing|policy routing]] rather than a plain default route. <mark style="background: #BBFABBA6;">It stamps the interface's outgoing encrypted packets with a <strong>mark</strong></mark>, puts <mark style="background: #ABF7F7A6;">the default route in a dedicated routing table</mark>, and <mark style="background: #ADCCFFA6;">adds policy rules so that only marked packets</mark> — <mark style="background: #D2B3FFA6;">WireGuard's own encapsulated traffic</mark> — <mark style="background: #CACFD9A6;">bypass that table and route to the real endpoint normally</mark>, while everything else is sent into the tunnel. A `suppress_prefixlength 0` rule keeps any more-specific routes in the main table winning over the tunnel's default, so local and link-local destinations are not swallowed. The result is that all ordinary traffic goes through the VPN while the tunnel's own packets still find their way out.

```bash
# what wg-quick installs for AllowedIPs = 0.0.0.0/0 (IPv4 shown; ::/0 is analogous)
wg set wg0 fwmark 51820                            # mark WireGuard's own encrypted packets
ip route add 0.0.0.0/0 dev wg0 table 51820         # the tunnel default lives in its own table
ip rule add not fwmark 51820 table 51820           # unmarked traffic -> the tunnel table
ip rule add table main suppress_prefixlength 0     # keep specific routes in main winning
sysctl -w net.ipv4.conf.all.src_valid_mark=1       # let the marked replies survive rp_filter
```

![[wireguard-full-tunnel-routing.png]]

The mark is what makes the two paths diverge: an ordinary packet carries no mark, so it falls into the tunnel table and is encrypted, while the encrypted result then re-enters routing carrying the mark, fails the `not fwmark` test, and is routed out the real interface by the main table — no loop.

Put plainly: all application traffic rides the VPN, while the encrypted packets that carry the VPN travel out normally to reach the peer's endpoint — following the default route in the main table, which is ordinarily your WAN uplink. The tunnel is built over your real internet connection; only the traffic inside it is redirected.

The `src_valid_mark` sysctl (with companion connmark rules that restore the mark on inbound replies) keeps strict reverse-path filtering from dropping the returning encrypted packets.

## Split Tunneling

_Routing only chosen destinations through the VPN._

The opposite of a full tunnel is to list only specific prefixes in a peer's [[#AllowedIPs|AllowedIPs]] — for example `10.0.0.0/24, 192.168.50.0/24` to reach just the networks behind the peer. Only traffic to those destinations enters the tunnel; everything else uses the host's normal route. Because [[#wg-quick|wg-quick]] installs system routes straight from AllowedIPs, split tunnelling needs nothing beyond choosing the right prefixes, and it avoids the routing-table machinery that [[#Full-Tunnel Routing|full-tunnel routing]] requires.

## MTU and MSS

_Leaving room for the encryption overhead._

Every tunnelled packet carries the inner packet plus WireGuard's own overhead: the outer IP header, the UDP header, and WireGuard's data-message header and authentication tag — roughly 60 bytes over IPv4 and 80 over IPv6. The tunnel MTU must be small enough that an inner packet plus this overhead still fits the path's real MTU, or the encrypted datagrams fragment or are dropped. [[#wg-quick|wg-quick]] sets the tunnel MTU from the route to the [[#Endpoints|endpoint]] minus 80 bytes, which lands at 1420 on a standard 1500-byte link.

For forwarded TCP, the same reduced MTU is the classic cause of large transfers stalling when Path MTU Discovery is broken. The fix is the same one used for any tunnel: clamp the TCP MSS to the path MTU on forwarded SYNs, covered in [[Netfilter#MSS Clamping|MSS clamping]] and shown in the [[nftables#WireGuard Gateway|gateway recipe]].

## NAT Traversal

_Working from behind NAT with one UDP port and a keepalive._

WireGuard needs no special NAT-traversal protocol. Because all of a peer's traffic uses a single outbound UDP flow to the server's [[#Endpoints|endpoint]], a client behind NAT can reach a server with a public endpoint with no inbound port forwarding at all — the NAT creates an outbound mapping when the client sends its first packet, and the server replies through it, learning the client's current endpoint by [[#Roaming|roaming]]. The only requirement is to keep that mapping alive during idle periods, which is what [[#Persistent Keepalive|persistent keepalive]] is for. Two peers both behind NAT, with neither holding a reachable endpoint, is the case WireGuard cannot solve on its own and where an intermediary with a public address is needed.

---

# Deployment Topologies

_Common arrangements, from a single link to a routed site-to-site tunnel._

The same interface-and-peers model expresses every topology; what changes is how many peers each side lists and what each peer's [[#AllowedIPs|AllowedIPs]] contains.

## Point-to-Point

_Two hosts, one peer each._

The simplest case: each host has one peer, the other. Each lists the other's tunnel address (a `/32`) as its [[#AllowedIPs|AllowedIPs]], and at least one side configures the other's [[#Endpoints|endpoint]] so a handshake can start. This is a direct encrypted link between two machines, useful for securing a single service or joining two hosts across the internet.

## Remote Access

_Many clients reaching one server — the road-warrior pattern._

A central server lists each client as a [[#Peers|peer]] with a single-address [[#AllowedIPs|AllowedIPs]] and no [[#Endpoints|endpoint]] (clients roam). Each client lists only the server, with the server's endpoint and a [[#Persistent Keepalive|keepalive]]. Whether a client runs a [[#Full-Tunnel Routing|full tunnel]] (`0.0.0.0/0, ::/0`) or a [[#Split Tunneling|split tunnel]] (just the server's subnets) is purely a matter of what its single peer's AllowedIPs contains. For clients to reach anything beyond the server, the server needs [[#Forwarding and Masquerade|forwarding and masquerade]].

## Site-to-Site

_Joining two networks through a tunnel between their routers._

A router at each site runs WireGuard and lists the other as a peer, but here each peer's [[#AllowedIPs|AllowedIPs]] is the whole subnet behind the remote router (for example `192.168.20.0/24`) rather than a single host. Each router enables [[#Forwarding and Masquerade|forwarding]] so that LAN hosts behind it can reach the remote subnet through the tunnel, and ordinary routes on the LAN hosts (or on the routers) direct that subnet's traffic at the tunnel. The two networks behave as if directly connected, with the encrypted link between the routers invisible to the hosts.

## Hub-and-Spoke and Mesh

_Choosing between a central relay and direct links among many peers._

With several sites or hosts there are two arrangements. In hub-and-spoke, every spoke peers only with a central hub, whose [[#AllowedIPs|AllowedIPs]] for each spoke covers that spoke's addresses, and the hub forwards traffic between spokes; spoke-to-spoke traffic takes two tunnel hops through the hub, but each spoke needs only one peer. In a full mesh, every host peers directly with every other, so traffic takes one hop, but each host must list every other as a peer and the configuration grows with the square of the number of hosts. Hub-and-spoke is simpler to manage and is the usual choice; a mesh is worth the bookkeeping when direct, low-latency paths between every pair matter.

---

# Security Properties

_What the protocol guarantees and what it deliberately omits._

WireGuard's security posture is shaped as much by what it leaves out as by what it includes. The design favours a small, fixed, auditable core over flexibility.

## Cryptographic Design

_A fixed suite, chosen rather than negotiated._

WireGuard does not negotiate cipher suites. It uses one set of primitives for everyone: ChaCha20-Poly1305 for authenticated encryption, Curve25519 for [[#Keys|key]] agreement, BLAKE2s for hashing, HKDF for key derivation, and SipHash for its internal hash-table keys. There is no downgrade negotiation to attack and no menu of weak options to misconfigure; if a primitive ever needs replacing, that is a versioned protocol change, not a per-connection choice. Together with a deliberately small implementation, this keeps the attack surface narrow and the protocol easy to reason about.

## Silence and Stealth

_No reply to anything that does not authenticate._

A WireGuard interface answers only packets that authenticate — that decrypt correctly under a configured peer's keys and pass replay checks. Anything else, including a port scan or a spoofed [[#The Cryptographic Handshake|handshake]] from an unknown key, receives no response at all. To anything actively probing the port it is indistinguishable from a closed one, with no banner or reply to give the service away. This silence is also the foundation of WireGuard's [[#Cookies and Denial-of-Service Resistance|denial-of-service resistance]]: work is spent only on senders that have already proven themselves.

That invisibility is only against active probing, though. A passive observer watching the traffic can still recognize WireGuard: its fixed message-type header and characteristic packet sizes — the handshake initiation is always 148 bytes — form a static signature that deep-packet-inspection systems fingerprint readily, and standard WireGuard is blocked or throttled in a number of heavily censored networks. Concealing that WireGuard is in use needs an obfuscation layer on top: forks such as AmneziaWG randomize the headers and packet sizes and can mimic other UDP protocols, and lighter junk-packet injection defeats simpler filters. None of this changes the tunnel's cryptography — it is about hiding the protocol, not protecting the data.

## Key Management

_No PKI; trust comes from exchanging public keys._

WireGuard has no certificate authority and no built-in key-distribution mechanism. Trust between two peers is established by exchanging [[#Keys|public keys]] out of band and configuring each as the other's `PublicKey`. A peer's public key is simultaneously its identity and, through its [[#AllowedIPs|AllowedIPs]], its authorization to use particular addresses. Rotating keys means generating a new pair, distributing the new public key to every peer, and updating the configurations. WireGuard also has no mechanism to push addresses, routes or DNS to a peer the way some VPNs do — each end is configured independently, so provisioning many clients is a matter of templates or external tooling rather than anything the protocol negotiates. For environments that need automated provisioning, revocation or short-lived credentials, that machinery is layered on top by separate tooling; the protocol itself stays minimal. A [[#Pre-shared Keys|pre-shared key]] can be added to any peering as a symmetric second factor and as a hedge against a future break of the public-key cryptography.

---

# Troubleshooting

_Reading the symptoms: what a given failure usually points to._

Most WireGuard problems fall into a handful of patterns, and [[#Inspecting a Running Tunnel|wg show]] narrows them down quickly — the latest-handshake time alone separates a tunnel that never formed from one that is up but not carrying traffic.

- No handshake ever appears. The encrypted outer packets are not completing a round trip. Check that the server's [[#The Encrypted Outer Packet|listen port]] is reachable — allowed with `udp dport 51820` on the [[Netfilter#Hooks and Packet Flow|firewall]], and port-forwarded through any NAT in front of the server — and that the client's [[#Endpoints|endpoint]] is correct. A public-key mismatch produces the same silence, since each side ignores a peer it does not recognize. And because the handshake carries a TAI64N timestamp, a badly wrong clock on either end can cause initiations to be rejected.
    
- The handshake succeeds but no traffic flows. Keys are fine; routing or authorization is not. The destination may fall outside the peer's [[#AllowedIPs|AllowedIPs]] — nothing matches outbound, or the inbound source is rejected. With the bare [[#wg|wg]] tool there may be no kernel route pointing at the interface. On a gateway, [[#Forwarding and Masquerade|IP forwarding]] may be off, masquerade may be missing for private tunnel addresses, or the [[Netfilter#Forward|forward]] filter may be dropping the packets.
    
- Small exchanges work but large transfers stall — a shell logs in, web pages load halfway. This is the classic [[#MTU and MSS|MTU]] black hole when Path MTU Discovery is broken. Clamp the TCP MSS on forwarded SYNs, or lower the tunnel MTU.
    
- The tunnel works, then dies after the server's address changes. An [[#Endpoints|endpoint]] given as a hostname is resolved only once, when the interface comes up, and wg-quick does not re-resolve it. For a dynamic-DNS endpoint, run the `reresolve-dns` helper shipped with wireguard-tools on a timer.
    
- Return traffic is silently dropped. Asymmetric paths — common with a [[#Full-Tunnel Routing|full tunnel]] — can trip strict reverse-path filtering. The full-tunnel setup handles this with `src_valid_mark`; otherwise set `rp_filter` to loose mode on the interfaces involved.
    
- You edited a peer and locked part of it out. `wg set … allowed-ips` replaces that peer's whole list rather than adding to it. Re-apply the complete list, or edit the file and use [[#wg|wg syncconf]] so live sessions survive.
    
- DNS misbehaves. A tunnel in a [[#WireGuard in a Network Namespace|network namespace]] reads its resolver from `/etc/netns/<ns>/resolv.conf`, not the global file; and wg-quick's `DNS=` only takes effect if a resolver integration — `resolvconf`, `openresolv` or systemd-resolved — is present.