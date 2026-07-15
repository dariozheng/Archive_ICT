---
categories:
  - "[[Networking]]"
topic@networking:
  - "[[Networking General]]"
tags:
  - ccnp
  - networking
  - claude
  - encor/routing
icon: FasNetworkWired
iconColor: "#003791"
last_update: 2026-07-14
---
_Subnetting moves the boundary between the network portion and the host portion of an IP address, so that one allocated block can be split into smaller networks that route independently._

Every IPv4 address is a single 32-bit integer. A mask declares which of those bits identify the network and which identify a host inside it. 

The whole discipline reduces to four questions asked of any address and prefix:

- Where does this subnet start? → the [[#The Network Address|network address]]
- Where does it end? → the [[#The Broadcast Address|broadcast address]]
- Which addresses can actually be assigned? → the [[#The Usable Host Range|usable host range]]
- How many of these fit inside the parent block? → the [[#Counting Subnets|subnet count]]

---

## IPv4 Address

_An IPv4 address is 32 bits. Every subnetting rule follows from where those 32 bits are cut in two._

### Dotted Decimal and Binary

The 32 bits are written as four <strong>8-bit groups</strong> (<strong>octets</strong>), each rendered in decimal and separated by dots. Each octet holds a value from 0 to 255.

Within an octet, the bit weights are always the same eight numbers:

```
bit position  →   1     2    3    4    5    6    7    8
weight        →  128   64   32   16    8    4    2    1
```

An address in both forms:

```
    192   .   168    .    10    .   200
 11000000 . 10101000 . 00001010 . 11001000
```

Decimal is only a display convention. The router, the kernel and the [[#The Subnet Mask|mask]] all operate on the flat 32-bit value.

### The Network Portion and the Host Portion

The mask splits the 32 bits into a leading run of network bits and a trailing run of host bits:

```
 ┌──────────────────────── 32 bits ────────────────────────┐
 ├──────────────────────────────────┬──────────────────────┤
 │          network prefix          │      host bits       │
 └──────────────────────────────────┴──────────────────────┘
 ◄─────────── n bits (fixed) ───────►◄─── 32 − n bits ─────►
       identical for every host          varies per host
        in the same subnet                in the subnet
```

Two combinations of the host bits are reserved by definition:

|Host bits|Meaning|
|---|---|
|all zeros|the network address — names the subnet itself|
|all ones|the broadcast address — reaches every host in the subnet|

These two reservations are the sole reason for the "minus two" that appears in every host count.

### The Subnet Mask

A subnet mask is a 32-bit value written in the same dotted-decimal form, whose bits are a contiguous run of ones followed by a contiguous run of zeros. Ones mark network bits, zeros mark host bits.

```
address  192.168.10.200   11000000 10101000 00001010 11001000
mask     255.255.255.224  11111111 11111111 11111111 11100000
                          └────────── 27 ones ─────────┘└ 5 ┘
```

Because the ones must be contiguous, only nine octet values can ever appear in a valid mask:

|Ones in the octet|0|1|2|3|4|5|6|7|8|
|---|---|---|---|---|---|---|---|---|---|
|Octet value|0|128|192|224|240|248|252|254|255|

> [!note] Non-contiguous masks 
> A mask such as `255.255.0.255` is syntactically expressible but is not valid in any modern stack, routing protocol or allocation policy. If a mask octet is not one of the nine values above, the mask is wrong.

### CIDR Prefix Notation

Since the mask is fully described by the number of leading ones, it is written as a slash followed by that count. `255.255.255.224` and `/27` are the same statement.

```
192.168.10.200/27   ≡   192.168.10.200  255.255.255.224
```

The prefix length is the only form used by routing protocols, the Linux `ip` command, nftables, WireGuard `AllowedIPs`, and every allocation registry. Dotted-decimal masks persist chiefly in Cisco interface configuration and in Windows dialogs.

### The Wildcard Mask

The wildcard mask is the bitwise inverse of the subnet mask: zeros mark bits that must match, ones mark bits that are free to vary. Compute it by subtracting each mask octet from 255.

```
              255 . 255 . 255 . 255      all ones
mask        − 255 . 255 . 255 . 224      /27
              ─────────────────────
wildcard        0 .   0 .   0 .  31      0.0.0.31
```

|Prefix|Subnet mask|Wildcard mask|
|---|---|---|
|/26|255.255.255.192|0.0.0.63|
|/27|255.255.255.224|0.0.0.31|
|/20|255.255.240.0|0.0.15.255|
|/13|255.248.0.0|0.7.255.255|

Wildcards appear in Cisco ACLs and OSPF `network` statements. Linux tooling never uses them, though Python exposes the same value as the `hostmask` attribute of a network object. The wildcard is numerically identical to the block size minus one in the octet where the boundary falls.

---

## From Classful to Classless

_Classful addressing derived the mask from the first bits of the address itself. Its failure is the reason prefixes are carried explicitly today._

### Classful Addressing

Before 1993, the boundary was implied by the leading bits of the address, and only three boundaries existed.

|Class|Leading bits|First octet range|Implied prefix|Networks|Hosts per network|
|---|---|---|---|---|---|
|A|0|1 – 126|/8|126|16,777,214|
|B|10|128 – 191|/16|16,384|65,534|
|C|110|192 – 223|/24|2,097,152|254|
|D|1110|224 – 239|—|multicast|—|
|E|1111|240 – 255|—|reserved|—|

The 127.0.0.0/8 range is carved out of Class A for loopback, which is why the Class A range stops at 126.

### Why Classful Broke

The three sizes were severely mismatched to actual demand:

- An organisation with 300 hosts was too big for a Class C (254 hosts) and so received a Class B (65,534 hosts), wasting more than 65,000 addresses.
- A Class A allocation consumed 1/256th of the entire address space for a single organisation.
- Because the mask was implied rather than carried, routes could not be aggregated. Every allocated network needed its own entry in the global routing table.

Class B exhaustion and routing table growth were the two forcing functions.

### CIDR

Classless Inter-Domain Routing (RFC 4632, originally RFC 1519) discards the class boundaries entirely and carries the <strong>prefix length</strong> explicitly in every route advertisement and interface configuration.

Three capabilities follow directly:

- Allocations can be sized to demand rather than to a class — an organization with 300 hosts receives a /23, not a /16.
- Different subnets of the same block can carry different prefix lengths, which is [[#Variable Length Subnet Masking|VLSM]].
- Contiguous, aligned blocks can be advertised as one shorter prefix, which is [[#Route Summarization|route summarization]].

> [!info] The classes are gone, the vocabulary is not 
> Terms such as "Class C address" persist in vendor documentation and in informal usage. They now denote no more than a /24-sized block drawn from the 192–223 range. No modern device derives a mask from the first octet.

---

## Subnetting Arithmetic

_The complete set of formulas. Everything after this section is a faster way of evaluating them._

### Borrowing Host Bits

To create subnets within a block, bits are taken from the host portion and assigned to the network portion. The prefix lengthens; the host portion contracts.

A /24 subnetted into eight pieces, borrowing three bits:

```
/24   11111111 11111111 11111111 │ 00000000    8 host bits
      └──── 24 network bits ───┘   └── 8 ─┘    2⁸ = 256 addresses, 1 subnet

                      borrow 3 host bits  ↓

/27   11111111 11111111 11111111 111 │ 00000   5 host bits
      └────── 27 network bits ─────┘   └ 5 ┘   2⁵ = 32 addresses per subnet
                                 └┬┘
                                  └── 3 borrowed bits → 2³ = 8 subnets
                                      
```

The number of bits borrowed is `new prefix − old prefix`. No addresses are created: the total is conserved, since 8 subnets × 32 addresses = 256.

### Counting Subnets

```
subnets = 2 ^ (new prefix − old prefix)
```

Borrowing 3 bits from a /24 yields 2³ = 8 subnets of /27. Borrowing 6 bits from a /16 yields 2⁶ = 64 subnets of /22.

The same formula determines how many networks of a given size fit within a parent block: a /22 contains 2^(26−22) = 16 networks of /26.

### Counting Addresses and Usable Hosts

```
total addresses = 2 ^ (32 − prefix)
usable hosts    = 2 ^ (32 − prefix) − 2
```

The minus two removes the [[#The Network Address|network address]] and the [[#The Broadcast Address|broadcast address]]. In practice one more address is consumed by the default gateway, so a /24 with 254 usable hosts accommodates 253 endpoints.

### Point-to-Point and Host Prefixes

The minus-two rule has three exceptional cases:

| Prefix | Addresses | Usable | Use                                                                                                                                                                                                   |
| ------ | --------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| /30    | 4         | 2      | The classic point-to-point link. Half the block is burned on network and broadcast.                                                                                                                   |
| /31    | 2         | 2      | Point-to-point links per RFC 3021. The network and broadcast reservations are explicitly suppressed, because a two-node link needs neither. Supported by IOS-XE, Linux, and modern routers generally. |
| /32    | 1         | 1      | A single host route. Used for loopbacks, anycast service addresses, WireGuard peer `AllowedIPs`, and static routes to one destination.                                                                |

> [!tip] Prefer /31 over /30 for router-to-router links 
> A /31 halves point-to-point consumption. On a network with 200 such links, that is 400 addresses recovered. Platform support should be confirmed before deployment; a /30 on one end and a /31 on the other will not form an adjacency.

### The Network Address

The network address is obtained by ANDing the address with the mask, which is the same as zeroing every host bit.

```
address    192.168.10.200   11000000 10101000 00001010 11001000
mask /27   255.255.255.224  11111111 11111111 11111111 11100000
AND        ───────────────────────────────────────────────────────
network    192.168.10.192   11000000 10101000 00001010 11000000
```

The network address names the subnet. It is never assigned to an interface.

### The Broadcast Address

The broadcast address is the network address with every host bit set to one.

```
network    192.168.10.192   11000000 10101000 00001010 11000000
host bits  set to 1                                     ───11111
broadcast  192.168.10.223   11000000 10101000 00001010 11011111
```

Arithmetically, it is the last address in the block:

```
broadcast = network address + total addresses − 1
```

### The Usable Host Range

Everything strictly between the network address and the broadcast address:

```
first usable = network address + 1
last usable  = broadcast address − 1
```

For 192.168.10.192/27: first `.193`, last `.222`, 30 usable addresses.

### Subnet Zero and the All-Ones Subnet

The first subnet of a block (all borrowed bits zero) and the last (all borrowed bits one) were historically avoided, because their network addresses can be confused with the parent block's own network and broadcast addresses.

This restriction is obsolete. Cisco IOS has enabled `ip subnet-zero` by default since 12.0, the command itself is deprecated on IOS-XE, and Linux never had the restriction. Both subnets are fully usable, and every host-count table in this note assumes so.

> [!warning] Certification curricula may differ 
> Some older curricula still expect `2^s − 2` for the subnet count. Production equipment does not impose this restriction. The applicable convention depends on the context in which the question is posed.

---

## Fast Manual Calculation

_The objective is to determine network, broadcast and range for any prefix within seconds, without expanding to binary._

### The Two Ladders

Two mirrored sequences carry the entire method; both must be immediately recallable.

```
bits borrowed   1     2     3     4     5     6     7     8
mask octet    128   192   224   240   248   252   254   255
block size    128    64    32    16     8     4     2     1
                    ▲                              ▲
                    └── the two rows always sum to 256 ──┘
```

The block size — also called the magic number or the increment — is the distance between consecutive subnet boundaries in the octet where the prefix boundary falls.

```
block size = 256 − mask octet value
```

The ladder is read in either direction: the mask octet yields the block size, and the block size yields the mask octet.

### Finding the Interesting Octet

The interesting octet is the one containing the prefix boundary — the first octet whose mask value is not 255.

```
interesting octet = ⌈ prefix / 8 ⌉
```

|Prefix range|Interesting octet|Mask shape|
|---|---|---|
|/1 – /8|first|`m.0.0.0`|
|/9 – /15|second|`255.m.0.0`|
|/17 – /23|third|`255.255.m.0`|
|/25 – /31|fourth|`255.255.255.m`|

Prefixes /8, /16, /24 and /32 fall exactly on an octet boundary. They have no partially-masked octet, and their block size is a full 256 in the octet immediately to the right.

Everything to the left of the interesting octet is fixed and may be copied verbatim. Everything to its right is 0 in the network address and 255 in the broadcast address. Only the interesting octet requires arithmetic, which is the source of the method's speed.

### The Magic Number Method

Five steps, without binary expansion:

1. Find the [[#Finding the Interesting Octet|interesting octet]].
2. Compute the block size: `256 − mask value of that octet`.
3. Divide the address's value in that octet by the block size and discard the remainder. Multiply back by the block size. That is the interesting octet of the network address.
4. Broadcast: add the block size, subtract 1, in that octet. Octets to the right become 255.
5. Usable range: network + 1 through broadcast − 1.

Stated as a single line for the interesting octet:

```
network octet   = ⌊ address octet / block ⌋ × block
broadcast octet = network octet + block − 1
```

The multiples of the block size are the only legal subnet boundaries. For a block of 32 they are 0, 32, 64, 96, 128, 160, 192, 224 — a sequence that should be recallable without computation.

### Worked Example in the Fourth Octet

```
Given:  172.16.10.100/26
```

| Step              | Work                                     | Result                       |
| ----------------- | ---------------------------------------- | ---------------------------- |
| Interesting octet | ⌈26/8⌉ = 4                               | fourth                       |
| Mask              | 26 − 24 = 2 borrowed bits → ladder → 192 | 255.255.255.192              |
| Block             | 256 − 192                                | 64                           |
| Boundaries        | multiples of 64                          | 0, 64, 128, 192              |
| Network           | ⌊100/64⌋ = 1 → 1 × 64 = 64               | 172.16.10.64                 |
| Broadcast         | 64 + 64 − 1 = 127                        | 172.16.10.127                |
| Usable            | 65 through 126                           | 172.16.10.65 – 172.16.10.126 |
| Host count        | 2^(32−26) − 2                            | 62                           |

### Worked Example in the Third Octet

Octets to the left of the interesting octet are copied; those to its right are filled with 0 or 255.

```
Given:  10.14.99.200/20
```

| Step              | Work                                        | Result                            |
| ----------------- | ------------------------------------------- | --------------------------------- |
| Interesting octet | ⌈20/8⌉ = 3                                  | third                             |
| Mask              | 20 − 16 = 4 borrowed bits → ladder → 240    | 255.255.240.0                     |
| Block             | 256 − 240                                   | 16                                |
| Boundaries        | multiples of 16 in octet 3                  | 0, 16, 32, 48, 64, 80, 96, 112, … |
| Network           | ⌊99/16⌋ = 6 → 6 × 16 = 96, fourth octet → 0 | 10.14.96.0                        |
| Broadcast         | 96 + 16 − 1 = 111, fourth octet → 255       | 10.14.111.255                     |
| Usable            | —                                           | 10.14.96.1 – 10.14.111.254        |
| Host count        | 2^(32−20) − 2                               | 4094                              |

The `.200` in the fourth octet was never used. Once the interesting octet is identified, all octets to its right are irrelevant to the network calculation.

### Worked Example in the Second Octet

```
Given:  10.13.5.6/13
```

|Step|Work|Result|
|---|---|---|
|Interesting octet|⌈13/8⌉ = 2|second|
|Mask|13 − 8 = 5 borrowed bits → ladder → 248|255.248.0.0|
|Block|256 − 248|8|
|Boundaries|multiples of 8 in octet 2|0, 8, 16, 24, 32, …|
|Network|⌊13/8⌋ = 1 → 1 × 8 = 8, rest → 0|10.8.0.0|
|Broadcast|8 + 8 − 1 = 15, rest → 255|10.15.255.255|
|Usable|—|10.8.0.1 – 10.15.255.254|
|Host count|2^(32−13) − 2|524,286|

The same procedure confirms that 172.16.0.0/12 spans 172.16.0.0 through 172.31.255.255: block = 256 − 240 = 16 in the second octet, so the range runs from 172.16 to 172.31.

### Sizing a Subnet from a Host Count

Work backwards from the [[#Powers of Two|powers of two]]. Find the smallest host-bit count `h` such that `2^h − 2` covers the requirement, then the prefix is `32 − h`.

| Hosts needed | 2^h − 2 must cover it | Host bits | Prefix | Usable |
| ------------ | --------------------- | --------- | ------ | ------ |
| 2            | 2                     | 2         | /30    | 2      |
| 10           | 14                    | 4         | /28    | 14     |
| 25           | 30                    | 5         | /27    | 30     |
| 50           | 62                    | 6         | /26    | 62     |
| 100          | 126                   | 7         | /25    | 126    |
| 200          | 254                   | 8         | /24    | 254    |
| 500          | 510                   | 9         | /23    | 510    |
| 1000         | 1022                  | 10        | /22    | 1022   |

> [!warning] Do not size to the exact requirement 
> A department with exactly 254 devices does not fit within a /24 once the gateway, an HSRP virtual address, printers and a DHCP reservation pool are accounted for. Where a requirement approaches a boundary, size to the next power of two.

### Sizing a Subnet from a Subnet Count

The mirror image of the preceding rule. Determine the smallest bit count `s` such that `2^s` covers the number of subnets required, then add `s` to the parent prefix.

```
Need 6 subnets from 192.168.1.0/24
2² = 4  → not enough
2³ = 8  → enough, s = 3
prefix  = 24 + 3 = /27
result  = 8 subnets of 30 usable hosts each
```

The two surplus subnets are not waste; they constitute the growth budget.

### The Same-Subnet Test

To determine whether two addresses can communicate without traversing a router, compare their network addresses. In practice this reduces to a single division:

```
Are 10.14.99.200 and 10.14.104.9 in the same /20 ?

block = 16 in the third octet
⌊ 99 / 16⌋ = 6   →  network 10.14.96.0
⌊104 / 16⌋ = 6   →  network 10.14.96.0
same → yes, same subnet
```

```
Are 10.14.99.200 and 10.14.115.9 in the same /20 ?

⌊ 99 / 16⌋ = 6   →  10.14.96.0
⌊115 / 16⌋ = 7   →  10.14.112.0
different → no, they need a router
```

All octets to the left of the interesting octet must also match.

### Binary AND as a Cross-Check

The magic number method is a decimal shortcut for a binary operation. Where a result appears incorrect, revert to the definition and perform the AND explicitly:

```
address    192.168.10.200   11000000 10101000 00001010 11001000
mask /27   255.255.255.224  11111111 11111111 11111111 11100000
network    192.168.10.192   11000000 10101000 00001010 11000000
broadcast  192.168.10.223   11000000 10101000 00001010 11011111
                                                       └──┬──┘
                                            host bits: 00000 → network
                                                       11111 → broadcast
```

Only the interesting octet ever needs to be expanded into binary. The other three are either all-ones (copy) or all-zeros (0 or 255).

### Sanity Checks

Four checks that detect nearly every manual error:

- The network address must be an exact multiple of the block size in the interesting octet.
- `broadcast − network + 1` must equal the total address count from `2^(32−prefix)`.
- The next subnet's network address must equal this subnet's broadcast plus one.
- The original address must lie between the first and last usable addresses, unless it is itself the network or broadcast address.

---

## Reference Tables

_Lookup material. The block size column is the operative one in the [[#The Magic Number Method|magic number method]]._

### Fourth-Octet Prefixes

The /24 to /32 range. Mask `255.255.255.m`; the block applies to the fourth octet.

|Prefix|Mask|Block|Subnets per /24|Addresses|Usable hosts|
|---|---|---|---|---|---|
|/24|255.255.255.0|256|1|256|254|
|/25|255.255.255.128|128|2|128|126|
|/26|255.255.255.192|64|4|64|62|
|/27|255.255.255.224|32|8|32|30|
|/28|255.255.255.240|16|16|16|14|
|/29|255.255.255.248|8|32|8|6|
|/30|255.255.255.252|4|64|4|2|
|/31|255.255.255.254|2|128|2|2|
|/32|255.255.255.255|1|256|1|1|

### Third-Octet Prefixes

The /16 to /23 range. Mask `255.255.m.0`; the block applies to the third octet.

|Prefix|Mask|Block|Subnets per /16|Addresses|Usable hosts|
|---|---|---|---|---|---|
|/16|255.255.0.0|256|1|65,536|65,534|
|/17|255.255.128.0|128|2|32,768|32,766|
|/18|255.255.192.0|64|4|16,384|16,382|
|/19|255.255.224.0|32|8|8,192|8,190|
|/20|255.255.240.0|16|16|4,096|4,094|
|/21|255.255.248.0|8|32|2,048|2,046|
|/22|255.255.252.0|4|64|1,024|1,022|
|/23|255.255.254.0|2|128|512|510|

### Second-Octet Prefixes

The /8 to /15 range. Mask `255.m.0.0`; the block applies to the second octet.

|Prefix|Mask|Block|Subnets per /8|Addresses|Usable hosts|
|---|---|---|---|---|---|
|/8|255.0.0.0|256|1|16,777,216|16,777,214|
|/9|255.128.0.0|128|2|8,388,608|8,388,606|
|/10|255.192.0.0|64|4|4,194,304|4,194,302|
|/11|255.224.0.0|32|8|2,097,152|2,097,150|
|/12|255.240.0.0|16|16|1,048,576|1,048,574|
|/13|255.248.0.0|8|32|524,288|524,286|
|/14|255.252.0.0|4|64|262,144|262,142|
|/15|255.254.0.0|2|128|131,072|131,070|

### Powers of Two

The table that warrants outright memorisation, as it governs both host sizing and subnet sizing.

|n|2^n|n|2^n|
|---|---|---|---|
|0|1|8|256|
|1|2|9|512|
|2|4|10|1,024|
|3|8|11|2,048|
|4|16|12|4,096|
|5|32|13|8,192|
|6|64|14|16,384|
|7|128|15|32,768|

---

## Variable Length Subnet Masking

_Different subnets of the same parent block carry different prefix lengths, each sized to its actual requirement._

### Why Fixed-Length Subnetting Wastes Space

Subnetting a /24 into eight equal /27s gives every segment 30 usable addresses. If one segment holds 60 servers it does not fit, and if another is a two-router link it wastes 28 addresses.

Fixed-length subnetting forces every subnet to the size of the largest requirement. VLSM removes that constraint by subnetting the subnets.

### The Largest-First Rule

Allocation must proceed from the largest requirement to the smallest. The reason is alignment: a /26 can begin only at a multiple of 64, and placing the smaller blocks first fragments the space such that no aligned /26 boundary remains.

1. Sort the requirements descending by host count.
2. Round each up to a prefix using [[#Sizing a Subnet from a Host Count|the host-count rule]].
3. Assign each from the lowest free address that is correctly aligned.
4. Record what remains free.

### Worked VLSM Allocation

Parent block `192.168.1.0/24`. Requirements: 60 hosts, 28 hosts, 12 hosts, and two point-to-point links.

| Order | Requirement | Prefix | Network       | Range       | Broadcast     | Usable |
| ----- | ----------- | ------ | ------------- | ----------- | ------------- | ------ |
| 1     | 60 hosts    | /26    | 192.168.1.0   | .1 – .62    | 192.168.1.63  | 62     |
| 2     | 28 hosts    | /27    | 192.168.1.64  | .65 – .94   | 192.168.1.95  | 30     |
| 3     | 12 hosts    | /28    | 192.168.1.96  | .97 – .110  | 192.168.1.111 | 14     |
| 4     | link A      | /30    | 192.168.1.112 | .113 – .114 | 192.168.1.115 | 2      |
| 5     | link B      | /30    | 192.168.1.116 | .117 – .118 | 192.168.1.119 | 2      |

Each allocation begins exactly one address after the preceding broadcast. That is the invariant to verify.

VLSM is recursive halving. Every allocation splits the smallest enclosing free block in two, and takes the lower half:

```
192.168.1.0/24
├── 192.168.1.0/25
│   ├── 192.168.1.0/26 ──────────────── LAN A   60 hosts   (62 usable)
│   └── 192.168.1.64/26
│       ├── 192.168.1.64/27 ─────────── LAN B   28 hosts   (30 usable)
│       └── 192.168.1.96/27
│           ├── 192.168.1.96/28 ─────── LAN C   12 hosts   (14 usable)
│           └── 192.168.1.112/28
│               ├── 192.168.1.112/29
│               │   ├── 192.168.1.112/30 ── link A          (2 usable)
│               │   └── 192.168.1.116/30 ── link B          (2 usable)
│               └── 192.168.1.120/29 ─── free               (6 usable)
└── 192.168.1.128/25 ────────────────── free             (126 usable)
```

Alignment is not enforced retrospectively; it is a consequence of the halving. This is also why the largest block must be placed first: had the two /30 links been taken from the bottom of the range, no aligned /26 boundary would have survived for the 60-host segment.

### Tracking Free Space

After the five allocations above, the remaining space is not an amorphous remainder but a set of aligned blocks:

- `192.168.1.120/29` — 8 addresses (6 usable)
- `192.168.1.128/25` — 128 addresses (126 usable)

Recording free space as CIDR blocks rather than as address ranges is what preserves the correctness of subsequent allocations. A range expressed as ".120 to .255" conceals the fact that no single /25 begins at .120.

> [!important] Overlap is silent 
> No router will report that 192.168.1.64/26 overlaps 192.168.1.96/28. The symptom appears later as intermittent unreachability. An allocation plan should be validated with tooling before deployment — see [[#The Python ipaddress Module|the ipaddress module]].

---

## Route Summarization

_The inverse of subnetting: several contiguous, aligned prefixes advertised as one shorter prefix._

### Finding the Common Prefix

The networks are written in binary and the bits common to all of them are counted. That count is the summary prefix length.

```
172.16.0.0/24    10101100 00010000 00000000 00000000
172.16.1.0/24    10101100 00010000 00000001 00000000
172.16.2.0/24    10101100 00010000 00000010 00000000
172.16.3.0/24    10101100 00010000 00000011 00000000
                 └──── 22 identical ────┘▲▲
                                         ││
                                         └┴─ 2 varying bits → 2² = 4 networks

summary → 172.16.0.0/22
```

Only the third octet needs expanding: 0, 1, 2 and 3 share their leading six bits, so 16 + 6 = 22.

The decimal shortcut applies the same block-size logic in reverse: four consecutive /24s imply that the third octet advances in a block of 4; a block of 4 corresponds to a mask octet of 252, which is /22.

### Alignment and Block Boundaries

A summary is valid only if its network address is an exact multiple of its own block size. This is the rule most frequently violated in summarization attempts.

```
192.168.8.0/24 … 192.168.15.0/24    → 8 networks, block 8, starts at 8 (a multiple of 8)
                                    → 192.168.8.0/21   valid
```

```
172.16.1.0/24 … 172.16.4.0/24       → 4 networks, block 4, starts at 1 (not a multiple of 4)
                                    → 172.16.0.0/22 would advertise .0 which is not ours
                                    → invalid
```

The second case cannot be expressed as a single prefix. It collapses to three:

```
172.16.1.0/24
172.16.2.0/23
172.16.4.0/24
```

### Worked Summarization

Summarize the four site LANs `10.20.16.0/24`, `10.20.17.0/24`, `10.20.18.0/24`, `10.20.19.0/24`.

|Step|Work|Result|
|---|---|---|
|Count the networks|4 consecutive /24s|4|
|Bits to release|2² = 4 → 2 bits|2|
|Summary prefix|24 − 2|/22|
|Block in octet 3|256 − 252|4|
|Alignment check|16 mod 4 = 0|valid|
|Summary|—|10.20.16.0/22|
|Coverage|10.20.16.0 – 10.20.19.255|exactly the four LANs|

### Discontiguous and Overlapping Blocks

Two failure modes warrant attention:

- Summarizing beyond the allocated range. A summary that spans addresses allocated elsewhere will blackhole them. Coverage must be verified, not merely alignment.
- Summarizing across a discontiguity. If 10.20.18.0/24 belongs to another site, no single prefix covers only 16, 17 and 19.

> [!note] Why summarization is worth designing for 
> A summarized routing table is smaller, converges faster, and hides flapping links from the rest of the network. A link failure inside 10.20.16.0/22 does not withdraw the summary, so the rest of the topology never recomputes. This is only achievable if the underlying subnets were allocated in aligned, contiguous blocks in the first place — which is a design decision taken before the first address is assigned.

---

## Designing an Addressing Plan

_Subnetting arithmetic is mechanical; the placement of blocks is not._

### Allocate Hierarchically

Every level of the topology should receive a block that can be summarized upward. A workable pattern for a multi-site enterprise using 10.0.0.0/8:

```
10.0.0.0/8                            the enterprise
 ├── 10.0.0.0/16      site A          one /16 per site → 256 sites
 │    ├── 10.0.0.0/20     access      16 × /20 available per site
 │    │    ├── 10.0.0.0/24    VLAN 10    data
 │    │    ├── 10.0.1.0/24    VLAN 20    voice
 │    │    └── 10.0.2.0/24    VLAN 30    printers
 │    ├── 10.0.16.0/20    servers
 │    └── 10.0.240.0/20   infrastructure
 │         ├── 10.0.254.0/24  point-to-point links, carved into /31s
 │         └── 10.0.255.0/24  loopbacks, one /32 each
 ├── 10.1.0.0/16      site B
 └── 10.2.0.0/16      site C
```

Each site advertises a single /16 to the core. Its internal structure is invisible to the remainder of the network.

### Leave Room to Grow

The most common failure in an addressing plan is not address exhaustion but the exhaustion of aligned space adjacent to an existing block. A /24 immediately followed by another assigned /24 cannot be grown to a /23.

Blocks should be allocated at intervals larger than current need, so that a subnet may be doubled in place. Reservation carries no cost; renumbering does.

### Encode Meaning in the Address

Where possible, the address should be self-documenting, so that traffic may be classified from the address alone:

| Convention                                  | Example                         |
| ------------------------------------------- | ------------------------------- |
| Third octet mirrors the VLAN ID             | VLAN 30 → 10.5.30.0/24          |
| A fixed sub-block for infrastructure        | `.240/20` of every site         |
| Loopbacks always /32 from a single block    | 10.255.0.0/24                   |
| Point-to-point links from a dedicated block | 10.255.1.0/24, carved into /31s |

This also makes ACLs, [[#Route Summarization|summaries]] and firewall rules shorter, because related subnets are naturally contiguous.

---

## Reserved and Special-Purpose Ranges

_Blocks that must never be routed on the public internet, or that carry special semantics regardless of the mask applied to them._

### RFC 1918 Private Space

|Block|Range|Size|Notes|
|---|---|---|---|
|10.0.0.0/8|10.0.0.0 – 10.255.255.255|16,777,216|One former Class A. The default choice for anything that may grow.|
|172.16.0.0/12|172.16.0.0 – 172.31.255.255|1,048,576|Sixteen /16s. Frequently mis-stated as 172.16.0.0/16 — verify with the block rule: 256 − 240 = 16, so 172.16 through 172.31.|
|192.168.0.0/16|192.168.0.0 – 192.168.255.255|65,536|256 /24s. Ubiquitous in home and small-office equipment, which makes it a poor choice for a VPN-terminating site, as overlap with a remote worker's home LAN is near-certain.|

### Other Reserved IPv4 Blocks

|Block|Purpose|
|---|---|
|0.0.0.0/8|"This network." 0.0.0.0/0 as a route means "everything" — the default route.|
|100.64.0.0/10|Carrier-grade NAT shared address space (RFC 6598). Not private space, do not use it internally.|
|127.0.0.0/8|Loopback. The entire /8, not only 127.0.0.1.|
|169.254.0.0/16|Link-local (RFC 3927). Self-assigned when DHCP fails. Its presence on an interface is a diagnostic signal, not a configuration.|
|192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24|Documentation (RFC 5737). Use these in examples and runbooks, never a real customer prefix.|
|198.18.0.0/15|Benchmarking (RFC 2544).|
|224.0.0.0/4|Multicast.|
|240.0.0.0/4|Reserved (former Class E).|
|255.255.255.255/32|Limited broadcast. Never forwarded by a router.|

---

## How the Mask Is Used at Runtime

_The mask is not merely documentation. It is consulted on every packet, in two distinct places._

### The Host Forwarding Decision

Before sending any packet, a host ANDs the destination address with its own mask and compares the result to its own network address:

```
same network   → resolve the destination MAC with ARP, send directly on the wire
different      → send to the default gateway's MAC, with the destination IP unchanged
```

An incorrect mask therefore produces a characteristic asymmetric failure: a host configured with a /24 mask on a network that is in fact a /23 will reach half of its own subnet directly and attempt to route the remainder through a gateway, which holds no better information about the destination.

```
Host   10.0.1.50/24   thinks its network is 10.0.1.0 – 10.0.1.255
Truth  the LAN is     10.0.0.0/23  (10.0.0.0 – 10.0.1.255)

destination 10.0.1.90  → same /24 → ARP → works
destination 10.0.0.90  → not in its /24 → sent to gateway → the gateway is on
                         the same wire, so it may work via ICMP redirect, or
                         silently fail depending on the platform
```

### Longest Prefix Match

A router that holds several routes covering the same destination always selects the one with the longest prefix — the most specific — regardless of protocol or metric.

```
routing table
  0.0.0.0/0        via 203.0.113.1     default
  10.0.0.0/8       via 10.255.0.1      summary
  10.20.16.0/22    via 10.255.0.5      site summary
  10.20.18.7/32    via 10.255.0.9      host route

packet to 10.20.18.7   → matches all four → /32 wins
packet to 10.20.18.8   → matches three    → /22 wins
packet to 10.99.0.1    → matches two      → /8  wins
packet to 8.8.8.8      → matches one      → /0  wins
```

This is the mechanism by which a /32 host route overrides a summary, and the reason an inadvertently advertised more-specific prefix can divert traffic that an aggregate was intended to carry.

---

## IPv6 Subnetting

_The arithmetic is identical; the scale and the conventions are not._

### What Changes

|Aspect|IPv4|IPv6|
|---|---|---|
|Address length|32 bits|128 bits|
|Notation|four decimal octets|eight hexadecimal groups (hextets) of 16 bits|
|Broadcast address|reserved, subtracted|does not exist — no minus two|
|Reserved in a subnet|network + broadcast|the all-zeros interface identifier is the subnet-router anycast address (RFC 4291)|
|Host subnet size|sized to the host count|effectively always /64|
|Masks|dotted-decimal or prefix|prefix only|

Consequently, IPv6 subnetting is not concerned with conserving host addresses. A /64 holds 2⁶⁴ addresses whether it contains three hosts or three thousand. Subnetting determines only how many /64 segments a site requires.

### Nibble Boundaries

One hex digit is four bits — a nibble. A prefix that is a multiple of 4 aligns to a hex digit boundary, which makes the subnet ID directly readable in the address text. Prefix lengths that fall mid-nibble are legal and function correctly, but they require binary conversion for every calculation.

```
2001:0db8:abcd:0000::/64
└─────┬────┘ └┬─┘ └┬─┘
   /32 from    │    │
   the RIR     │    └── interface identifier (64 bits)
               │
               └── subnet ID — each hex digit is 4 more bits of subnetting
```

Each nibble of subnetting multiplies the subnet count by 16:

|Prefix|Subnet bits below a /48|/64s available|
|---|---|---|
|/48|0|65,536|
|/52|4|4,096|
|/56|8|256|
|/60|12|16|
|/64|16|1|

### Standard Allocation Sizes

| Prefix | Typically assigned to                                               |
| ------ | ------------------------------------------------------------------- |
| /32    | An ISP, from its RIR                                                |
| /48    | A site or enterprise — the standard end-site allocation             |
| /56    | A residential or small-business customer                            |
| /64    | A single LAN segment or VLAN                                        |
| /127   | A point-to-point router link (RFC 6164), the IPv6 analogue of a /31 |
| /128   | A single host or loopback                                           |
|        |                                                                     |

> [!warning] Do not subnet longer than /64 on a LAN 
> SLAAC requires a 64-bit interface identifier. A /80 or /112 on a host segment breaks stateless autoconfiguration and, on some stacks, breaks neighbour discovery behaviour that assumes a /64. The only accepted exceptions are point-to-point links (/127) and loopbacks (/128). No address-conservation argument supports a longer prefix: a /48 already contains 65,536 /64s.

### Quick Hex Subnetting

Because the split falls on a nibble boundary, no arithmetic is required; the subnets are enumerated directly in hexadecimal.

```
Given a /48:   2001:db8:abcd::/48
Subnet to /64: 16 bits of subnet ID → the fourth hextet

  2001:db8:abcd:0000::/64     subnet 0
  2001:db8:abcd:0001::/64     subnet 1
  2001:db8:abcd:000a::/64     subnet 10
  ...
  2001:db8:abcd:ffff::/64     subnet 65535
```

```
Given a /56:   2001:db8:abcd:ab00::/56
Subnet to /64: 8 bits → the low byte of the fourth hextet

  2001:db8:abcd:ab00::/64     first
  2001:db8:abcd:ab01::/64
  ...
  2001:db8:abcd:abff::/64     last  (256 subnets)
```

A practical convention is to mirror the IPv4 plan in the subnet ID — VLAN 30 becomes `...:0030::/64` — so that dual-stack subnets are recognisably paired.

### Reserved IPv6 Ranges

|Block|Purpose|
|---|---|
|::/128|Unspecified address|
|::1/128|Loopback|
|2000::/3|Global unicast — the currently allocated range|
|fc00::/7|Unique local addresses (RFC 4193). In practice `fd00::/8`, with a randomly generated 40-bit global ID. The IPv6 counterpart of [[#RFC 1918 Private Space\|RFC 1918]] space — and the random global ID is precisely what prevents the overlap problem 192.168.0.0/16 suffers from.|
|fe80::/10|Link-local. Always present, always used as the next-hop for IPv6 routing.|
|ff00::/8|Multicast. IPv6 has no broadcast; its role is taken by multicast groups such as ff02::1.|
|2001:db8::/32|Documentation (RFC 3849).|

---

## Verification and Tooling

_Manual calculation serves for reading a configuration at speed. Any value to be committed should be verified with tooling._

### ipcalc and sipcalc

`ipcalc` prints the full decomposition, including binary, in one shot.

```bash
ipcalc 192.168.10.200/27
```

```
Address:   192.168.10.200       11000000.10101000.00001010.110 01000
Netmask:   255.255.255.224 = 27 11111111.11111111.11111111.111 00000
Wildcard:  0.0.0.31             00000000.00000000.00000000.000 11111
=>
Network:   192.168.10.192/27    11000000.10101000.00001010.110 00000
HostMin:   192.168.10.193       11000000.10101000.00001010.110 00001
HostMax:   192.168.10.222       11000000.10101000.00001010.110 11110
Broadcast: 192.168.10.223       11000000.10101000.00001010.110 11111
Hosts/Net: 30                    Class C, Private Internet
```

`sipcalc` handles IPv6 and can enumerate subnets directly:

```bash
sipcalc -s 26 192.168.1.0/24      # split a /24 into /26s
sipcalc 2001:db8:abcd::/48        # full IPv6 decomposition
```

### The Python ipaddress Module

Part of the standard library, and the most efficient means of validating an entire allocation plan.

```python
import ipaddress

net = ipaddress.ip_network("192.168.10.192/27")
net.network_address      # 192.168.10.192
net.broadcast_address    # 192.168.10.223
net.netmask              # 255.255.255.224
net.hostmask             # 0.0.0.31   (the wildcard mask)
net.num_addresses        # 32
list(net.hosts())[0]     # 192.168.10.193
list(net.hosts())[-1]    # 192.168.10.222
```

An interface carries an address together with its prefix; a network is the block itself. Conflating the two is a frequent source of error:

```python
iface = ipaddress.ip_interface("192.168.10.200/27")
iface.ip                 # 192.168.10.200   the host
iface.network            # 192.168.10.192/27  the subnet it belongs to
```

Subnetting, supernetting and overlap detection:

```python
# split a block
list(ipaddress.ip_network("10.0.0.0/22").subnets(new_prefix=24))
# → [10.0.0.0/24, 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24]

# summarize — collapse_addresses does the alignment check for you
ipaddress.collapse_addresses([
    ipaddress.ip_network("172.16.0.0/24"),
    ipaddress.ip_network("172.16.1.0/24"),
    ipaddress.ip_network("172.16.2.0/24"),
    ipaddress.ip_network("172.16.3.0/24"),
])
# → [172.16.0.0/22]

# overlap check — run this over every pair in an allocation plan
a = ipaddress.ip_network("192.168.1.64/26")
b = ipaddress.ip_network("192.168.1.96/28")
a.overlaps(b)            # True — the plan is broken
```

The same-subnet test, in one line:

```python
ipaddress.ip_interface("10.14.99.200/20").network == \
ipaddress.ip_interface("10.14.104.9/20").network      # True
```

### Inspecting a Live Linux Host

```bash
ip -br addr show                  # every interface address with its prefix
ip route get 8.8.8.8              # which route wins, and via which source address
ip route show table all           # the full forwarding table, longest-prefix ordered
ip -6 addr show                   # IPv6, including the fe80::/10 link-local
```

An address is added with its prefix, never with a separate mask:

```bash
ip addr add 10.14.96.10/20 dev eth0
ip route add 10.20.16.0/22 via 10.14.96.1
```

The kernel derives the on-link route from the prefix automatically, which is precisely the [[#The Host Forwarding Decision|host forwarding decision]] installed as a route.

---

## Common Pitfalls

_Ordered approximately by frequency of occurrence in live incidents._

|Pitfall|Symptom|Check|
|---|---|---|
|Block size applied to the wrong octet|Network address is nonsense|Recompute ⌈prefix/8⌉ before anything else|
|Mask mismatch between two hosts on one wire|Asymmetric reachability — A reaches B, B does not reach A|Compare `ip -br addr` on both; see [[#The Host Forwarding Decision\|the forwarding decision]]|
|Forgetting the minus two|Off-by-two in capacity planning, DHCP pool collides with the gateway|Recount usable hosts, then subtract the gateway|
|Applying minus two to a /31 or /32|Concluding a /31 has zero usable addresses|See [[#Point-to-Point and Host Prefixes\|the tail cases]]|
|Unaligned summary|Blackholed traffic, or advertisement of unallocated space|The summary network must be a multiple of its block; see [[#Alignment and Block Boundaries\|the alignment rule]]|
|Overlapping VLSM allocations|Intermittent unreachability that appears weeks later|`overlaps()` across every pair in the plan|
|Wildcard mask written where a subnet mask belongs|ACL matches far too much or nothing at all|0.0.0.31 and 255.255.255.224 are not interchangeable; see [[#The Wildcard Mask\|the wildcard mask]]|
|172.16.0.0/12 read as 172.16.0.0/16|Traffic to 172.20.x.x escapes a private-space rule|Block is 16 in the second octet → 172.16 to 172.31|
|192.168.x.x chosen for a VPN-terminating site|Remote workers cannot reach the office because their home LAN uses the same prefix|Prefer 10.x from an unusual range|
|Subnetting an IPv6 LAN longer than /64|SLAAC silently fails, hosts get only a link-local address|Keep host segments at /64; see [[#Standard Allocation Sizes\|the allocation sizes]]|
|Assuming subnet zero is unusable|Losing the first and last subnet of every block for no reason|Modern platforms permit both; see [[#Subnet Zero and the All-Ones Subnet\|subnet zero]]|

---

## Quick Reference Card

_Everything needed to subnet by hand, in one screen._

```
MASK / BLOCK LADDER
  borrowed bits   1     2     3     4     5     6     7     8
  mask octet    128   192   224   240   248   252   254   255
  block size    128    64    32    16     8     4     2     1
                                    (the two rows sum to 256)

FORMULAS
  block size       = 256 − mask octet
  interesting octet= ⌈ prefix / 8 ⌉
  network octet    = ⌊ address octet / block ⌋ × block
  broadcast octet  = network octet + block − 1
  total addresses  = 2 ^ (32 − prefix)
  usable hosts     = 2 ^ (32 − prefix) − 2      (/31 and /32 excepted)
  subnets          = 2 ^ (new prefix − old prefix)
  wildcard octet   = 255 − mask octet

RECIPE — given an address and a prefix
  1. interesting octet  = ⌈ prefix / 8 ⌉
  2. block              = 256 − mask value there
  3. network            = round the address's octet DOWN to a multiple of block
                          octets to the left: copy      octets to the right: 0
  4. broadcast          = network octet + block − 1
                          octets to the right: 255
  5. usable             = network + 1  …  broadcast − 1

RECIPE — given a host requirement
  smallest h with 2^h − 2 ≥ hosts   →   prefix = 32 − h

RECIPE — given a subnet requirement
  smallest s with 2^s ≥ subnets     →   prefix = parent prefix + s

FOURTH-OCTET CHEATSHEET
  /25 → 128 → 126 hosts      /29 →   8 →   6 hosts
  /26 →  64 →  62 hosts      /30 →   4 →   2 hosts
  /27 →  32 →  30 hosts      /31 →   2 →   2 hosts (RFC 3021)
  /28 →  16 →  14 hosts      /32 →   1 →   1 host

IPv6
  /48 site  ·  /56 customer  ·  /64 LAN  ·  /127 P2P  ·  /128 host
  never subnet a host segment longer than /64
  each nibble (4 bits) of subnet ID multiplies the subnet count by 16
```