---
categories:
  - "[[Networking]]"
  - "[[Privacy]]"
topic@privacy: "[[Privacy General]]"
tags:
  - claude
  - Networking
  - Privacy
icon: SiTorproject
iconColor: "#4F2C5F"
last_update: 2026-07-15
---
<strong>Tor</strong> (originally an acronym for <strong>The Onion Router</strong>) is a free, open-source overlay network for anonymous communication. It routes TCP traffic through a worldwide volunteer network of [[#Relays|relays]], wrapping the traffic in multiple layers of encryption so that no single point in the path can link the source of a connection to its destination.

Tor separates two things that are normally coupled on the Internet: who you are (your IP address) and what you are talking to (the destination). Each relay in a [[#Circuits|circuit]] only knows its immediate predecessor and successor — never the full path.

The project consists of:

- The Tor protocol and its reference implementations (the C daemon `tor` and the Rust rewrite [[#Arti]])
- The public Tor network of volunteer-run relays
- End-user software, most notably the [[#Tor Browser]]
- [[#Onion Services]], which allow servers to be reached without revealing their location
- [[#The Tor Project Organization|The Tor Project, Inc.]], the non-profit that maintains it all

## Threat Model

Tor is designed against a local adversary — one that can observe, control, or inject traffic on some fraction of the network, but not all of it. Typical adversaries in scope:

- Your ISP or local network operator, who can see that you connect to Tor but not where the traffic goes
- The destination website, which sees traffic arriving from a Tor [[#Exit Relay|exit relay]] but not your IP
- Any single relay operator, including a malicious one
- A censor trying to block access to Tor itself (addressed by [[#Bridges|bridges]] and [[#Pluggable Transports|pluggable transports]])

Explicitly out of scope is a global passive adversary — one that can watch both ends of a connection at once. Such an adversary can perform [[#End-to-End Correlation|end-to-end correlation]] by matching traffic timing and volume at the entry and exit, and Tor deliberately does not attempt to defeat this, because the padding and latency required would make the network unusable. Tor is a low-latency anonymity network; this is the fundamental trade-off it makes compared to high-latency designs like mix networks.

## Onion Routing

Onion routing is the core technique that gives Tor its name. The client selects a path of (normally) three relays, negotiates a symmetric key with each of them, and encrypts every message once per relay, innermost layer first — like the layers of an onion. Each relay peels off exactly one layer, learning only where to send the remainder.

```
Client ──[K1[K2[K3[payload]]]]──▶ Guard ──[K2[K3[payload]]]──▶ Middle ──[K3[payload]]──▶ Exit ──[payload]──▶ Destination
```

- The [[#Guard Relay|guard]] knows the client's IP but sees only encrypted data addressed to the middle.
- The [[#Middle Relay|middle]] knows only the guard and the exit — neither endpoint.
- The [[#Exit Relay|exit]] sees the destination and the plaintext of the application traffic (unless the application itself uses TLS), but not who originated it.

### Cells

All Tor traffic travels in fixed-size units called cells, 514 bytes on current link protocol versions. Fixed sizing prevents trivial traffic analysis based on message length. Cells come in two families:

|Family|Purpose|Examples|
|---|---|---|
|Control cells|Interpreted by the receiving relay itself|`CREATE2` / `CREATED2` (circuit setup), `DESTROY` (teardown), `PADDING`|
|Relay cells|Carried end-to-end along the circuit, one encryption layer per hop|`RELAY_BEGIN` (open a TCP stream), `RELAY_DATA` (stream payload), `RELAY_EXTEND2` (grow the circuit), `RELAY_END`|

Multiple application TCP streams are multiplexed over a single circuit, each identified by a stream ID inside the relay cells.

### Layered Encryption

Two distinct layers of cryptography are involved:

1. Link encryption — every connection between two Tor nodes (client-to-guard, relay-to-relay) is wrapped in TLS. This protects against an observer on the wire between any two hops.
2. Circuit (onion) encryption — inside the TLS tunnels, each relay shares a set of symmetric AES keys with the client, negotiated during [[#Circuit Construction|circuit construction]] using the ntor handshake (Curve25519-based Diffie-Hellman). The client applies one AES layer per hop; each relay removes (or, for return traffic, adds) exactly one.

Because keys are negotiated with forward secrecy, compromising a relay's long-term identity key later does not decrypt past traffic.

### Circuits

A circuit is the client's established path through the network — the ordered set of relays plus the per-hop symmetric keys. Key properties:

- Circuits normally have three hops: [[#Guard Relay|guard]] → [[#Middle Relay|middle]] → [[#Exit Relay|exit]]. Three is enough that no relay knows both endpoints; more hops add latency without a proportional anonymity gain.
- Circuits are pre-built in the background so that application requests don't wait for setup.
- A circuit is reused for roughly ten minutes, after which new streams get a fresh circuit. Existing long-lived streams stay on their circuit.
- Tor Browser additionally isolates circuits per first-party site, so activity on two different websites is not linkable through a shared exit.

#### Circuit Construction

Circuits are built incrementally, or telescopically — the client extends the tunnel one hop at a time, negotiating keys with each new relay through the tunnel it already has:

```
Client                     Guard                     Middle                    Exit
  │── CREATE2 ──────────────▶│
  │◀─ CREATED2 ──────────────│                          (client ↔ guard key K1)
  │── RELAY_EXTEND2 ────────▶│── CREATE2 ──────────────▶│
  │◀─ RELAY_EXTENDED2 ───────│◀─ CREATED2 ──────────────│  (client ↔ middle key K2)
  │── RELAY_EXTEND2 ────────▶│─────────────────────────▶│── CREATE2 ─────────▶│
  │◀─ RELAY_EXTENDED2 ───────│◀──────────────────────────│◀─ CREATED2 ─────────│  (client ↔ exit key K3)
```

The `EXTEND2` requests are themselves onion-encrypted, so the guard cannot see which exit the client picked, and the exit never learns who asked for the extension. Once all three keys exist, the client sends `RELAY_BEGIN` through the finished circuit and the exit opens the outbound TCP connection.

#### Path Selection

The client — never a directory or any relay — chooses the path, using the network view from the [[#Consensus|consensus]]. The main rules:

- Relays are picked with probability weighted by their measured bandwidth, so high-capacity relays carry proportionally more traffic and the network load-balances itself.
- No two relays in one circuit may be in the same /16 subnet or the same declared relay family, preventing one operator from occupying multiple positions on the same path.
- The first hop is always taken from the client's small, long-lived [[#Guard Relay|guard set]].
- The final hop must have an [[#Exit Policy|exit policy]] permitting the destination port and address.

## Network Components

The Tor network as of recent years consists of several thousand volunteer relays, a small fixed set of [[#Directory Authorities|directory authorities]], and an unlisted population of [[#Bridges|bridges]].

### Relays

A relay is a server running Tor in relaying mode, forwarding cells for others. Every relay has a long-term Ed25519 identity key, publishes a signed descriptor (address, keys, bandwidth, exit policy), and is measured and voted on by the [[#Directory Authorities|directory authorities]]. Relays are assigned flags in the [[#Consensus|consensus]] — `Guard`, `Exit`, `Fast`, `Stable`, `HSDir` — which determine what roles clients will use them for.

The position a relay occupies in a circuit implies very different exposure, which is why the roles are worth treating separately.

#### Guard Relay

The entry point of a circuit — the only relay that sees the client's real IP address. To limit the damage of malicious guards, Tor does not pick a random entry per circuit. Instead each client selects a small guard set (in practice, one primary guard) and keeps it for months.

The reasoning is counterintuitive but sound: if entries were random, a client building thousands of circuits would eventually pick an attacker-owned entry, and combined with an attacker exit that circuit is fully deanonymized. With a fixed guard, the client either chose a bad guard once (and is consistently at risk, which is no worse in expectation) or chose a good one and is consistently safe. Rotating guards maximizes the chance of eventually being caught; pinning them minimizes it.

Guard status requires the relay to have demonstrated bandwidth and uptime over time, so the pool is comparatively trustworthy and stable.

#### Middle Relay

The middle hop sees only encrypted cells from the guard and forwards them to the exit. It learns neither the client nor the destination, making it the lowest-risk position to operate — new relay operators are encouraged to start here. Freshly joined relays are effectively middle-only until they earn `Guard` status or opt into exiting.

#### Exit Relay

The last hop, where traffic leaves the Tor network for the open Internet. The exit performs the actual DNS resolution and opens the TCP connection to the destination, so:

- The destination sees the exit's IP address, not the client's.
- The exit can observe (and tamper with) any plaintext traffic — which is why end-to-end TLS between the client and the destination remains essential; Tor's onion layers end at the exit.
- Abuse complaints (scraping, attacks, spam originating from Tor users) arrive at the exit operator's door, making exits the operationally and legally riskiest role. They are run disproportionately by universities and dedicated NGOs.

##### Exit Policy

Every relay publishes an exit policy — an ordered accept/reject list of destination addresses and ports, structurally similar to a firewall ACL:

```
reject *:25          # no outbound SMTP (spam prevention)
accept *:80
accept *:443
reject *:*
```

Clients read exit policies from the [[#Consensus|consensus]] and only select exits whose policy allows the intended destination. A relay with `reject *:*` is a non-exit; the extremely common policy above (web only, no mail) exists because port 25 abuse historically got exit IPs blacklisted instantly.

### Directory Authorities

A small, hard-coded set (on the order of nine, plus a dedicated bridge authority) of independently operated servers that form the network's root of trust. Their identities and keys ship inside every Tor client. Each authority:

- Collects the descriptors that relays upload
- Tests relay reachability and evaluates bandwidth measurements
- Votes hourly on the state of every relay (which flags it deserves, whether it is running)

Distributing this role across independent operators in different jurisdictions means no single organization can unilaterally add fake relays to, or remove honest relays from, the network view — a majority of authorities would have to collude.

#### Consensus

The hourly product of the authorities' votes: a single signed document listing every running relay, its flags, address, keys, and bandwidth weight. Clients require the consensus to be signed by a majority of the authorities they know, then use it for [[#Path Selection|path selection]]. Because every client works from the same consensus, an attacker cannot feed a targeted victim a doctored network view without breaking the signature threshold.

Clients don't fetch the consensus from the authorities directly (that would not scale); they fetch it from ordinary relays acting as directory caches.

### Bridges

Relays are public — the [[#Consensus|consensus]] is world-readable, so a censor can simply block every listed relay IP. Bridges are the answer: relays that are deliberately not listed in the consensus. Their addresses are handed out in small, rate-limited doses through BridgeDB / the `bridges.torproject.org` distribution channels (HTTPS, email, Telegram, and built into Tor Browser via moat), so that a censor cannot cheaply enumerate them all.

A bridge functions as the client's entry hop in place of a [[#Guard Relay|guard]]. Blocking by address is only half the censorship problem, though — Tor's TLS handshake itself is fingerprintable by deep packet inspection, which is what pluggable transports address.

#### Pluggable Transports

Pluggable transports are traffic-obfuscation layers between the client and the bridge. They wrap Tor's protocol so it no longer looks like Tor on the wire. The interface is deliberately modular ("pluggable") so new transports can be deployed as censors adapt, without changing Tor itself.

```
Client ── transport (looks like noise / HTTPS / WebRTC) ──▶ Bridge ── normal Tor ──▶ Middle ──▶ Exit
```

##### obfs4

The current default obfuscation transport. It re-encrypts the entire stream so it is indistinguishable from random bytes, and requires the client to prove knowledge of the bridge's public key before the server responds at all — defeating active probing, where a censor connects to a suspected bridge to confirm what it is.

##### Snowflake

Routes the client's first hop through short-lived WebRTC connections to volunteer proxies running in ordinary web browsers. Because proxies are numerous, ephemeral, and hosted on residential connections, there is no stable address list to block, and the traffic resembles a video call. A broker (reached via [[#meek|domain fronting]]) matches clients with currently available proxies.

##### meek

Tunnels traffic through large cloud/CDN infrastructure using domain fronting: the TLS connection appears to go to a major hosted domain, while the true destination rides inside the encrypted HTTP Host header. Blocking it means blocking the entire cloud provider — collateral damage most censors avoid. Slower than the alternatives; used where nothing else survives.

## Onion Services

Onion services (formerly hidden services) invert Tor's usual direction of protection: instead of anonymizing the client, they anonymize the server. A service reachable at a `.onion` address never reveals its IP; both sides build circuits toward each other and meet in the middle. Traffic never leaves the Tor network — there is no [[#Exit Relay|exit relay]] involved — so the connection is end-to-end encrypted by Tor itself, with no exit able to snoop.

Self-authentication is the second property: the address is the public key, so if you have the correct address, no certificate authority is needed to know you're talking to the right server.

### Onion Addresses

A v3 onion address is 56 base32 characters ending in `.onion`, and encodes the service's full Ed25519 public key plus a checksum and version byte:

```
onion_address = base32( PUBKEY || CHECKSUM || VERSION ) + ".onion"
```

Because the address is the key, addresses cannot be forged, but they are also not human-memorable. The older, deprecated v2 addresses (16 characters, truncated RSA hash) were removed from the network in 2021 due to weak cryptography.

### Descriptors and HSDirs

A running onion service builds circuits to a few relays chosen as [[#Introduction Points|introduction points]], then publishes a signed descriptor — the list of those introduction points plus the keys needed to use them — to a set of relays carrying the `HSDir` flag. Which HSDirs are responsible for a given service rotates daily according to a shared random value the [[#Directory Authorities|directory authorities]] generate collectively, preventing an attacker from positioning relays to become the HSDir for a targeted service.

In v3, the descriptor is encrypted such that only someone who already knows the onion address can read it — an HSDir cannot learn the addresses of the services whose descriptors it stores.

### Rendezvous Protocol

The connection establishment dance, with every arrow below being a full Tor circuit built by the respective party:

```
Onion Service                HSDir            Intro Point         Rendezvous Point              Client
      │── 1. publish ─────────▶│                    │                     │                        │
      │                        │◀─────────────────────────────────────────── 2. fetch descriptor ──│
      │                        │                    │                     │◀── 3. establish, ──────│
      │                        │                    │                     │    leave cookie        │
      │◀── 4. INTRODUCE ───────┼────────────────────│◀────────────────────┼── 4. INTRODUCE ────────│
      │── 5. RENDEZVOUS ───────┼────────────────────┼────────────────────▶│                        │
      │                        │                    │                     │  (cookie matches:      │
      │◀═══════════════ spliced circuit, application data ═══════════════▶│◀═ circuits joined) ═══▶│
```

1. The service publishes its descriptor to the responsible HSDirs.
2. The client fetches the descriptor using the onion address.
3. The client picks a random relay as [[#Rendezvous Point|rendezvous point]], builds a circuit to it, and leaves a one-time cookie.
4. The client asks one of the service's [[#Introduction Points|introduction points]] to relay an introduction message containing the rendezvous point and cookie.
5. The service builds a fresh circuit to the rendezvous point and presents the cookie; the point splices the two circuits together.

The result is a six-hop path (three hops from each side). Neither party ever learns the other's IP, and no single relay sees both identities.

#### Introduction Points

Long-lived relays the service maintains circuits to, acting as its public contact points. They only ever forward the small introduction message — actual application data never flows through them, so compromising one reveals nothing about the service's traffic or location.

#### Rendezvous Point

A relay chosen by the client, fresh for every connection, where the two half-circuits are joined. It sees only encrypted cells passing between two circuits and knows neither party.

## Client Software

### Tor Browser

The flagship client: a hardened Firefox ESR fork bundled with Tor. Routing through Tor alone does not make browsing anonymous — the browser itself leaks identity through cookies, fingerprintable characteristics, and plugins. Tor Browser therefore:

- Normalizes the fingerprint (letterboxed window sizes, uniform fonts and user agent) so all Tor Browser users look alike
- Isolates cookies, cache, and circuits per first-party site, and clears everything on exit
- Disables or gates APIs commonly abused for [[#Browser Fingerprinting|fingerprinting]], with a user-facing security level slider (Standard / Safer / Safest) that progressively disables JavaScript and media
- Ships HTTPS-Only mode and NoScript, and includes the [[#Pluggable Transports|pluggable transport]] clients for censored users

### Tails

A live Linux distribution booted from USB that forces every application's traffic through Tor and leaves no trace on the host machine — the operating-system-level complement to Tor Browser, aimed at high-risk users who cannot trust the installed OS.

### Orbot

The Tor client for Android (with an iOS counterpart), able to route individual apps or the whole device through Tor. Onion Browser is the corresponding iOS browser.

### Arti

The ground-up rewrite of the Tor client in Rust, replacing the two-decade-old C implementation. Motivations are memory safety (a large fraction of historical Tor security bugs were memory errors impossible in safe Rust) and embeddability — Arti is designed as a library that applications can link directly rather than managing a separate daemon. It reached stable client functionality and is the project's long-term future; relay support is the ongoing frontier.

## Interfaces

### SOCKS Proxy

Applications reach Tor as a local SOCKS5 proxy, by default on `127.0.0.1:9050` (9150 for the copy bundled in Tor Browser). Two practical rules matter:

- DNS must be resolved through the proxy (SOCKS5 with hostname, not raw IPs), otherwise the application leaks every destination it visits to the local DNS resolver before the traffic ever enters Tor.
- Only TCP is carried; UDP-based protocols do not traverse Tor.

### Control Port

A separate local port (default `9051`) speaking a line-based text protocol through which external programs can inspect and steer the Tor daemon — build circuits, change configuration, subscribe to events. Tools like Nyx (the terminal status monitor) and the Stem Python library are control-port clients. Access is protected by cookie or password authentication, since control-port access is full control of the client's anonymity.

## Security Considerations

### What Tor Protects

| Observer                  | What they see                                                          | What they don't         |
| ------------------------- | ---------------------------------------------------------------------- | ----------------------- |
| Local network / ISP       | That you use Tor (unless on a [[#Bridges\|bridge]]), timing and volume | Destinations, content   |
| [[#Guard Relay\|Guard]]   | Your IP, encrypted cells                                               | Destination, content    |
| [[#Middle Relay\|Middle]] | Guard and exit identities                                              | Both endpoints, content |
| [[#Exit Relay\|Exit]]     | Destination, plaintext if no TLS                                       | Your identity           |
| Destination               | Exit IP, application data you send                                     | Your IP                 |

### Known Attack Vectors

#### End-to-End Correlation

An adversary observing both the client's entry traffic and the exit (or destination) traffic can match flows by timing and volume, deanonymizing the circuit without breaking any cryptography. This is the attack Tor explicitly does not defend against (see [[#Threat Model]]); guard pinning exists precisely to reduce the probability that an attacker's relay occupies the entry position over time.

#### Malicious Exit Relays

Because onion encryption terminates at the exit, a hostile exit can read and modify plaintext — historically abused for credential sniffing and SSL-stripping, and more recently for rewriting cryptocurrency addresses in transit. Mitigations: end-to-end TLS everywhere, [[#Onion Services|onion services]] (no exit involved), and the network health team actively scanning for and ejecting misbehaving exits.

#### Browser Fingerprinting

Even with perfect routing anonymity, a website can identify a visitor by the unique combination of browser characteristics. This is an application-layer attack that Tor the network cannot address — it is the reason [[#Tor Browser]] exists as a distinct, fingerprint-normalized browser rather than a proxy setting.

#### Denial of Service

Onion services in particular have suffered floods of introduction requests, each of which forces expensive circuit building. The v3 protocol added a proof-of-work defense (activated in 2023): under load, the service demands clients solve a small client-puzzle before their introduction is queued, prioritizing real users over flood traffic.

#### Sybil Attacks

An adversary running many relays increases its odds of landing in useful circuit positions. Countermeasures are the [[#Directory Authorities|authorities']] vetting and flag requirements, family declarations, the /16 and family constraints in [[#Path Selection|path selection]], and ongoing network-health monitoring that has repeatedly ejected large malicious relay groups.

### Operational Limits

- Tor anonymizes the transport, not the payload: logging into a personal account over Tor identifies you to that site regardless of routing.
- Only TCP is carried (see [[#SOCKS Proxy]]); applications with UDP side channels leak.
- Latency is inherently higher than a direct connection — three hops plus queueing — and this is by design (see [[#Threat Model]]).

## The Tor Project Organization

The Tor Project, Inc. is the US 501(c)(3) non-profit (founded 2006) that develops the software, coordinates the volunteer relay community, and runs the supporting infrastructure. Historical arc in brief:

- Onion routing originated at the U.S. Naval Research Laboratory in the mid-1990s (Syverson, Reed, Goldschlag).
- The Tor design by Dingledine, Mathewson, and Syverson was published in 2004 and released as free software.
- Funding is a mix of government grants (historically a majority, a recurring point of discussion), foundations, and individual donations; the code and network are fully open and auditable, which is the community's answer to funding-based trust concerns.

The organization's work spans development (core Tor, [[#Arti]], [[#Tor Browser]]), anti-censorship ([[#Pluggable Transports|transports]], bridge distribution), network health (measurement via the Tor Metrics portal, malicious-relay hunting), and user support and advocacy. The relays themselves are not run by the organization — the network's capacity is entirely volunteer-operated, which is both its resilience and its dependence.