## Foundations

_What a coin actually is, why the problem is hard, and the vocabulary the rest of the note depends on._

A cryptocurrency is a distributed, append-only ledger replicated across mutually distrusting machines, together with a set of rules that let those machines agree on the ledger's contents without a central operator. A "coin" is not a file, an object, or a token you hold. It is an entry in that ledger, and ownership is proved by the ability to produce a valid cryptographic signature.

Everything else in this note is machinery in service of one goal: making that shared ledger converge on a single history that nobody can rewrite cheaply.

### What a Coin Is

A coin is a unit of account defined by the protocol itself. It exists at the consensus layer, meaning every node that validates the chain must independently track it and enforce its rules. Three properties follow:

- Its supply is enforced by consensus rules, not by an issuer's promise.
- It is the asset used to pay for blockspace, so the network cannot function without it.
- It cannot be destroyed or created by any party outside the protocol rules, including the developers.

Bitcoin's BTC, Ethereum's ETH, Monero's XMR, and Solana's SOL are coins in this sense. Each has its own chain, its own validators, and its own rules.

### Coins Versus Tokens

A token is an entry in the state of a smart contract that runs on somebody else's chain. USDC, UNI, and most of what is listed on exchanges are tokens, not coins.

|Aspect|Coin|Token|
|---|---|---|
|Where it lives|Consensus rules of its own chain|Storage of a contract on a host chain|
|Who enforces supply|Every validating node|The contract's code, and whoever can upgrade it|
|Pays transaction fees|Yes, it is the native fee asset|No, fees are paid in the host chain's coin|
|Can be frozen or minted arbitrarily|No, absent a chain-wide fork|Yes, if the contract permits it|
|Failure mode|Requires attacking the chain|Requires only a contract bug or a privileged key|

The distinction is not pedantic. A token inherits the host chain's settlement guarantees but adds the contract's own trust assumptions on top. See [[#Token Standards|token standards]] for how those contracts are structured.

### Denominations

Every protocol defines its coin in indivisible integer units, and the familiar name is only a display convention. All consensus arithmetic is integer arithmetic: floating point never appears, because rounding differences between implementations would break agreement.

|Chain|Base unit|Base units per coin|Common intermediate unit|
|---|---|---|---|
|Bitcoin|satoshi|100,000,000 (10^8)|None in general use|
|Ethereum|wei|1,000,000,000,000,000,000 (10^18)|gwei, 10^9 wei, used to quote gas prices|
|Monero|piconero|1,000,000,000,000 (10^12)|None in general use|
|Litecoin|litoshi|100,000,000 (10^8)|None in general use|

> [!warning] Never hold balances in floating point Binary floating point cannot represent most decimal fractions exactly, so a script that adds `0.1` and `0.2` will not produce `0.3`, and the error compounds across operations. Parse, store, and compare amounts as integers in the base unit, and convert only at the moment of display.

### The Double-Spend Problem

Digital data copies perfectly. If a coin were merely a signed message saying "I own 1 unit", the holder could send that same message to two recipients, and neither could tell which came first. Traditional payment systems solve this with a central database that serialises operations.

A decentralised system has no such authority, so it must answer a harder question: given two conflicting transactions that both spend the same funds, which one is real?

The answer is not cryptographic, it is economic. The network picks whichever transaction appears in the chain that the most resources have been committed to extending. See [[#Consensus|consensus]] for the mechanisms that make this expensive to subvert.

> [!note] Ordering is the whole product Cryptography proves authorisation. It cannot prove ordering. Determining which of two validly signed, mutually exclusive transactions came first is the only part of the problem that requires a blockchain at all.

### Coins Do Not Move

No coin ever travels across the network. What propagates is a signed instruction to modify the ledger, and every node applies that instruction to its own local copy of the state.

```text
  Alice's wallet                 Network                  Bob's wallet
       │                            │                          │
       │  build + sign transaction  │                          │
       ├───────────────────────────►│                          │
       │                            │  gossip to peers         │
       │                            ├──────────────►           │
       │                            │                          │
       │                    included in a block                │
       │                            │                          │
       │                    every node updates                 │
       │                    its own ledger copy                │
       │                            │                          │
       │                            │  Bob's node observes     │
       │                            │  an output he can spend  │
       │                            ├─────────────────────────►│
```

A wallet does not contain coins. It contains keys, and it scans the ledger for entries those keys can authorise. Losing the wallet application loses nothing; losing the keys loses everything. See [[#Keys, Addresses, and Wallets|keys and wallets]].

---

## Cryptographic Primitives

_The three building blocks every chain is assembled from: hashes, signatures, and Merkle trees._

### Hash Functions

A cryptographic hash function maps input of any length to a fixed-length digest, deterministically and irreversibly.

#### Properties That Matter

|Property|Meaning|What it protects|
|---|---|---|
|Preimage resistance|Given `H(x)`, finding `x` is infeasible|Commitments, address derivation|
|Second-preimage resistance|Given `x`, finding `x' ≠ x` with the same digest is infeasible|Transaction identity|
|Collision resistance|Finding any pair `x ≠ x'` with the same digest is infeasible|Merkle trees, block identity|
|Avalanche effect|Flipping one input bit changes roughly half the output bits|Mining, tamper evidence|
|Determinism|Same input always yields the same digest|Independent verification by every node|

The avalanche property is what makes hashing usable as a lottery. There is no way to steer the output, so the only strategy for producing a digest below a target value is to try inputs at random. That is the entire basis of [[#Proof of Work|proof of work]].

#### Hash Functions in Practice

|Chain|Algorithm|Used for|
|---|---|---|
|Bitcoin|SHA-256 applied twice (`HASH256`)|Block hashing, transaction IDs, Merkle nodes|
|Bitcoin|RIPEMD-160 over SHA-256 (`HASH160`)|Legacy and SegWit v0 address derivation|
|Bitcoin|Tagged SHA-256 (BIP-340)|Taproot leaf and branch commitments|
|Ethereum|Keccak-256|Addresses, storage slots, state trie, event topics|
|Monero|RandomX|Proof of work, deliberately CPU-friendly|
|Litecoin, Dogecoin|Scrypt|Proof of work, memory-hard by design|

> [!warning] Keccak-256 is not SHA3-256 Ethereum adopted Keccak before NIST changed the padding rule during standardisation. The two produce different digests for the same input. Libraries that expose `sha3_256` are usually wrong for Ethereum work — the correct function is `keccak256`.

### Digital Signatures

_Proves that whoever produced a message knew a private key, without revealing that key._

A signature commits to a digest, not to a transaction as a user perceives it. What that digest covers is protocol-specific, and getting it wrong is a recurring source of both bugs and losses. See [[#Signing and Signature Hashes|signature hashes]].

#### Elliptic Curve Keys

A private key is simply a very large random integer. A public key is derived from it by elliptic curve point multiplication, an operation that is cheap forward and infeasible to reverse.

```text
private key  d     (a random 256-bit integer, 1 ≤ d < n)
                   │
                   │  P = d · G        elliptic curve scalar multiplication
                   ▼
public key   P     (a point on the curve, 33 bytes compressed)
                   │
                   │  hash + encode
                   ▼
address            (a short, checksummed, human-transcribable string)
```

`G` is the curve's generator point, fixed in the protocol. `n` is the order of the group, roughly 1.158 × 10^77 for secp256k1. Recovering `d` from `P` requires solving the elliptic curve discrete logarithm problem, for which no practical classical algorithm is known.

|Curve|Used by|Notes|
|---|---|---|
|secp256k1|Bitcoin, Ethereum, and most forks of either|Koblitz curve, chosen for fast verification|
|Ed25519|Solana, Cardano, Monero, Stellar|Twisted Edwards curve, deterministic signing, faster|
|NIST P-256|Some enterprise chains, passkey integrations|Widely available in hardware and HSMs|

> [!important] Key generation is only as good as its entropy A private key derived from a weak random source is guessable regardless of the curve. Historic losses have come almost entirely from bad entropy, reused nonces, and backup mistakes, never from breaking the curve.

#### ECDSA

The Elliptic Curve Digital Signature Algorithm produces a pair `(r, s)` from the message digest, the private key, and a per-signature random nonce `k`.

The nonce is the fragile part. Reusing `k` across two different messages lets anyone solve for the private key with simple algebra, which is exactly how several early wallet and console breaches happened. RFC 6979 deterministic nonce generation, now standard in wallet libraries, derives `k` from the key and message so no randomness is needed at signing time.

Bitcoin additionally requires low-`s` encoding (BIP-62) because ECDSA signatures are inherently malleable: both `s` and `n − s` are valid, so an attacker could alter a signature in flight and change the transaction ID without invalidating it.

Ethereum signatures carry a third value `v`, a recovery identifier that lets the verifier recompute the signer's public key from the signature alone. This is why Ethereum transactions do not carry an explicit sender field.

#### Schnorr Signatures

BIP-340 added Schnorr signatures to Bitcoin as part of Taproot. They are linear, which brings three practical benefits:

- Signatures from multiple parties can be aggregated into one that is indistinguishable from a single-signer signature.
- No malleability, so no low-`s` rule is needed.
- Simpler security proof under standard assumptions.

The result is that a multisignature spend or a complex contract can appear on-chain as an ordinary single-key payment, improving both privacy and block space efficiency. See [[#Taproot|Taproot]].

### Merkle Trees

_Lets a verifier confirm that one item belongs to a large set while downloading almost none of that set._

Transactions in a block are hashed pairwise up a binary tree until a single root remains. That root goes in the block header, so committing to the header commits to every transaction in the block.

```text
                    Merkle root
                   ╱           ╲
             H(AB)               H(CD)
            ╱     ╲             ╱     ╲
        H(A)      H(B)      H(C)      H(D)
          │         │         │         │
        tx A      tx B      tx C      tx D
```

To prove that `tx C` is in the block, a verifier needs only `H(D)`, `H(AB)`, and the header — three values instead of the whole block. The proof size grows logarithmically, so a block with a million transactions needs about twenty hashes.

This is the mechanism behind [[#Node Types|light clients]] and behind cross-chain proofs. Ethereum extends the idea into a Merkle Patricia Trie that commits not just to transactions but to the entire world state, so a node can prove any account balance or storage slot against a single root hash. See [[#State Storage|state storage]].

> [!note] Merkle proofs prove inclusion, not validity A proof shows that a transaction is in a block whose header you have. It says nothing about whether that block follows the consensus rules. Only a validating node checks that.

---

## Keys, Addresses, and Wallets

_Everything a user actually controls, and the derivation chain that turns one secret into an unlimited number of accounts._

### From Entropy to Private Key

The whole hierarchy descends from a single block of randomness.

```text
  128–256 bits of entropy
            │
            │  append checksum, split into 11-bit groups, map to wordlist
            ▼
  BIP-39 mnemonic  ("witch collapse practice feed shame open ...")
            │
            │  PBKDF2-HMAC-SHA512, 2048 iterations
            │  salt = "mnemonic" + optional passphrase
            ▼
  512-bit seed
            │
            │  HMAC-SHA512 with key "Bitcoin seed"
            ▼
  master private key  +  master chain code        (BIP-32)
            │
            │  repeated child key derivation along a path
            ▼
  account keys ──► address keys ──► addresses
```

The optional passphrase is sometimes called the twenty-fifth word. It is mixed into the PBKDF2 salt, so every distinct passphrase yields a completely different and equally valid wallet. There is no way to tell a wrong passphrase from a right one; a wrong one simply opens an empty wallet.

> [!warning] The passphrase has no recovery path Because any passphrase produces a valid wallet, a typo is indistinguishable from a deliberate choice. It must be backed up with the same rigour as the mnemonic, and separately from it.

### Hierarchical Deterministic Wallets

BIP-32 defines a one-way tree: from a parent key and a chain code you can derive an unbounded number of child keys, and the derivation is reproducible from the seed alone. This is why a twelve-word backup restores an entire wallet history rather than a single address.

#### Hardened and Non-Hardened Derivation

Non-hardened derivation allows an extended public key (`xpub`) to generate child public keys without any private material. That is how watch-only wallets and payment processors work: the server holds only an `xpub` and can issue fresh receive addresses indefinitely.

The trade-off is that an `xpub` combined with any one leaked child private key reveals the parent private key, and therefore the whole branch. Hardened derivation, marked with an apostrophe in the path, breaks that relationship at the cost of losing `xpub` derivation below that point. Account-level and above is conventionally hardened for this reason.

#### Derivation Paths

The path format is `m / purpose' / coin_type' / account' / change / index`.

|Path|Standard|Address type|
|---|---|---|
|`m/44'/0'/0'/0/0`|BIP-44|Bitcoin legacy P2PKH, addresses starting `1`|
|`m/49'/0'/0'/0/0`|BIP-49|Bitcoin nested SegWit, addresses starting `3`|
|`m/84'/0'/0'/0/0`|BIP-84|Bitcoin native SegWit, addresses starting `bc1q`|
|`m/86'/0'/0'/0/0`|BIP-86|Bitcoin Taproot, addresses starting `bc1p`|
|`m/44'/60'/0'/0/0`|BIP-44, SLIP-44 coin 60|Ethereum and EVM chains|

The `change` field is `0` for receive addresses and `1` for internal change addresses. See [[#Outpoints and Change|change outputs]].

> [!tip] Same seed, different path, different wallet A recovery that appears to show an empty wallet is far more often a path mismatch than a lost seed. Before assuming the worst, try the other standard paths and confirm the wallet's script type.

### Address Formats

An address is an encoding of a commitment to a public key or a script, wrapped in a checksum so that transcription errors fail loudly rather than sending funds into the void.

|Format|Example prefix|Encoding|Checksum|
|---|---|---|---|
|P2PKH|`1`|Base58Check|Double SHA-256, first 4 bytes|
|P2SH|`3`|Base58Check|Double SHA-256, first 4 bytes|
|P2WPKH, P2WSH|`bc1q`|Bech32|BCH code, detects up to 4 errors|
|P2TR|`bc1p`|Bech32m|BCH code, variant fixing a Bech32 length flaw|
|Ethereum|`0x`|Hex, 20 bytes|EIP-55 mixed-case, optional|

Bech32 is case-insensitive and uses an alphabet that omits `1`, `b`, `i`, and `o` to reduce ambiguity, which is why native SegWit addresses are safer to read aloud or copy by hand.

> [!warning] Ethereum's checksum is advisory An all-lowercase Ethereum address is valid and carries no error detection at all. EIP-55 encodes a checksum in the capitalisation pattern, but only wallets that choose to verify it will catch a typo. A mistyped address that happens to be well-formed sends funds to a key nobody holds.

### What a Wallet Actually Stores

A wallet holds keys and a view of the chain. Concretely:

- The seed or the derived private keys, ideally encrypted at rest.
- Derivation state, meaning how far along each branch addresses have been generated.
- A cached view of spendable entries belonging to those keys.
- Optionally, labels and metadata that exist nowhere on-chain.

The cached view is reconstructible from the chain; the keys are not.

### Custody Models

|Model|Key location|Compromise requires|Typical use|
|---|---|---|---|
|Custodial|Third party|Trusting or breaching that party|Exchanges, brokerages|
|Hot wallet|Internet-connected host|Compromising that host|Daily spending, small balances|
|Hardware wallet|Dedicated signing device|Physical access plus PIN, or supply-chain attack|Individual long-term holdings|
|Air-gapped signer|Offline machine, PSBT or QR transfer|Physical access to the offline device|High-value single-party custody|
|Multisignature|`m` of `n` keys, geographically split|Compromising `m` distinct locations|Treasuries, inheritance planning|
|Threshold signatures|Shares of one key, never reassembled|Compromising the threshold of shares|Institutional custody|

Multisignature and threshold schemes differ in where the policy lives. A multisig quorum is enforced by the chain's own script rules and is publicly auditable; a threshold scheme produces one ordinary signature and keeps the policy off-chain. Under Schnorr, the on-chain distinction largely disappears.

---

## Ledger Models

_Two ways to represent "who owns what". Nearly every design decision downstream follows from this choice._

### The UTXO Model

_Bitcoin's model. The ledger is a set of discrete unspent outputs, and a transaction consumes some and creates others._

There are no balances anywhere in the protocol. An output is a `(value, locking script)` pair. A transaction destroys the outputs it references and creates new ones, and validity requires that every referenced output exists, is unspent, and that the provided data satisfies its locking script.

```text
        tx1                          tx2                        tx3
   ┌───────────┐              ┌───────────┐              ┌───────────┐
   │ out 0.7 ──┼─────────────►│ in        │              │           │
   │ out 0.3   │              │ out 0.5 ──┼─────────────►│ in        │
   └───────────┘              │ out 0.19  │              │ out 0.18  │
                              └───────────┘              └───────────┘
                                 fee 0.01                  fee 0.01

   Consumed outputs vanish from the UTXO set. New ones are added.
   The fee is never written down — it is inputs minus outputs.
```

#### Outpoints and Change

An input identifies its source by an outpoint: the transaction ID plus the output index. Because an output must be spent in full, any remainder must be returned to the spender as an explicit change output. Forgetting the change output does not fail validation — it donates the remainder to the miner as fee. Several six-figure losses have happened exactly this way.

#### Coinbase Transactions

Every block starts with one transaction that has no inputs. It creates the block subsidy plus the sum of all fees in the block, and is the only mechanism by which new coins come into existence. Its outputs cannot be spent for 100 blocks, so that a chain reorganisation cannot leave already-spent newly-minted coins stranded. See [[#Bitcoin's Emission Schedule|emission schedule]].

#### Consequences of the UTXO Design

- Validation of independent transactions parallelises cleanly, since they touch disjoint parts of the set.
- There is no global mutable state, which sharply limits what contracts can express.
- Privacy is better by default because a new address per payment is natural, though [[#Chain Analysis Heuristics|clustering heuristics]] undo much of it.
- Wallets must perform coin selection, choosing which outputs to spend, which affects fees and leaks information.

### The Account Model

_Ethereum's model. The ledger is a key-value map from address to account state, and transactions mutate it in place._

The world state maps each 20-byte address to a record:

|Field|Meaning|
|---|---|
|`nonce`|Transactions sent from this account, or contracts it has created|
|`balance`|Wei held by the account|
|`storageRoot`|Merkle Patricia Trie root of the account's persistent storage|
|`codeHash`|Keccak-256 of the account's bytecode|

#### Account Types

An externally owned account is controlled by a private key, has no code, and is the only kind that can originate a transaction. A contract account has code and storage, no key, and acts only when called, executing on the [[#The Ethereum Virtual Machine|EVM]].

EIP-7702, introduced in the Pectra upgrade of May 2025, blurs this: an externally owned account can delegate to contract code for the duration of a transaction, giving key-controlled accounts batching, sponsored fees, and custom authorisation rules without migrating to a new address.

#### Nonces

Each account carries a strictly incrementing counter. A transaction is only valid if its nonce equals the account's current nonce, which does three things at once:

- Prevents replay of a previously broadcast transaction.
- Forces a total order on that account's transactions.
- Creates head-of-line blocking, since a stuck low-nonce transaction blocks every later one from that account.

The standard fix for a stuck transaction is to rebroadcast the same nonce with a higher fee, which is the account-model equivalent of [[#Replacement and Acceleration|fee replacement]].

### Comparing the Two Models

|Dimension|UTXO|Account|
|---|---|---|
|State representation|Set of unspent outputs|Map of address to account record|
|Replay protection|Implicit, an output can only be spent once|Explicit per-account nonce|
|Parallel validation|Natural|Requires dependency analysis|
|Contract expressiveness|Deliberately limited|Arbitrary, Turing-complete within a [[#Gas Metering|
|State growth|Bounded by the unspent set|Grows monotonically without expiry mechanisms|
|Default privacy|Better, new address per payment|Worse, address reuse is the norm|
|Fee specification|Implicit, inputs minus outputs|Explicit gas limit and price|
|Typical user error|Missing change output|Wrong nonce or insufficient gas|

---

## Transactions

_How an intent becomes a signed, fee-paying, network-propagated instruction._

### Anatomy of a UTXO Transaction

|Field|Purpose|
|---|---|
|`version`|Signals which consensus rules the transaction opts into|
|`inputs[]`|Outpoints being spent, each with an unlocking script and sequence number|
|`outputs[]`|New `(value, locking script)` pairs|
|`witness[]`|Signatures and scripts moved outside the transaction ID computation by SegWit|
|`locktime`|Earliest block height or timestamp at which the transaction may be mined|

SegWit's separation of witness data from the transaction ID fixed third-party malleability: with signatures excluded from the ID, nobody can alter a signature in transit and change the identifier that dependent transactions reference. That fix is what made [[#Payment Channels|payment channels]] practical.

The `sequence` field on each input drives relative timelocks (BIP-68) and opt-in replaceability (BIP-125).

### Anatomy of an Account-Model Transaction

|Field|Purpose|
|---|---|
|`nonce`|Sequence number for the sending account|
|`to`|Recipient address, or empty for contract creation|
|`value`|Wei transferred|
|`data`|Calldata, interpreted as a function call by contract accounts|
|`gasLimit`|Maximum computation the sender will pay for|
|`maxFeePerGas`|Absolute ceiling on the per-gas price|
|`maxPriorityFeePerGas`|Tip offered to the block proposer|
|`chainId`|Prevents replay of the transaction on a different EVM chain|
|`v, r, s`|Signature, from which the sender address is recovered|

`chainId` was introduced by EIP-155 after the 2016 chain split, when transactions valid on one branch were replayable on the other. See [[#Chain Splits|chain splits]].

### Signing and Signature Hashes

What the signature covers is not the transaction as displayed, but a serialisation of selected parts of it.

In Bitcoin, a `SIGHASH` flag on each signature selects the scope:

|Flag|Commits to|Effect|
|---|---|---|
|`SIGHASH_ALL`|All inputs and all outputs|Default. The transaction is fixed once signed.|
|`SIGHASH_NONE`|All inputs, no outputs|Anyone may redirect the funds. Almost never correct.|
|`SIGHASH_SINGLE`|All inputs, one matching output|Used in coordinated multi-party constructions.|
|`SIGHASH_ANYONECANPAY`|Only this input|Combinable with the above; allows others to add inputs.|

Ethereum's equivalent concern is what a signed message authorises. EIP-712 typed structured data exists so that wallets can display a meaningful, domain-separated summary rather than an opaque hex blob.

> [!warning] Blind signing is the dominant loss vector Approvals, permits, and delegation signatures often grant open-ended authority over token balances and cost no gas to produce, so they never appear as a transaction the user recognises. A signature request that a wallet cannot decode into human-readable terms should be refused by default.

### Transaction Fees

_Blockspace is a scarce good sold by auction. The auction design differs sharply between models._

#### Fee Estimation in UTXO Chains

The fee is implicit and the market prices it per unit of transaction size, expressed in satoshis per virtual byte. Virtual size counts witness data at one quarter weight, which is why SegWit and Taproot spends are cheaper for the same economic effect.

Two consequences follow. First, consolidating many small outputs is expensive because each input adds size. Second, an output whose value is below the cost of spending it is economically dead, a condition called dust.

```text
  fee = feerate (sat/vB) × virtual size (vB)

  virtual size = (base size × 3 + total size) / 4
```

#### EIP-1559 Fee Markets

Ethereum replaced the first-price auction with a two-part fee:

- A base fee per gas, set algorithmically by the protocol and adjusted each block toward a target utilisation. It is burned, not paid to anyone.
- A priority fee per gas, the tip that goes to the block proposer.

The sender specifies a maximum total and a maximum tip; the difference between the max and the actual charge is refunded. Because the base fee moves predictably by at most 12.5 percent per block, fee estimation becomes a matter of choosing how many blocks of headroom to buy rather than guessing what competitors will bid.

The burn is the mechanism that makes ETH issuance able to go net negative under load. See [[#Ethereum's Issuance and Burn|issuance and burn]].

> [!note] Gas limit is a ceiling, not a price Setting a high gas limit does not cost more if the transaction uses less. Setting it too low causes the transaction to run out of gas, revert, and still consume the fee for the work performed — a failed transaction is not a free transaction.

### The Mempool

Each node keeps its own pool of validated but unconfirmed transactions. There is no single mempool; policies differ between implementations and operators, so a transaction visible on one node may be absent from another.

Node-level policy rules are distinct from consensus rules. A transaction can be perfectly valid by consensus yet refused relay for being non-standard, too low-feerate, or exceeding ancestor and descendant package limits. Miners are free to include such transactions if they receive them by other means.

Transactions leave the mempool when confirmed, when evicted for low feerate under memory pressure, or when they expire.

### Replacement and Acceleration

|Technique|Model|Mechanism|
|---|---|---|
|Replace-by-fee|UTXO|Rebroadcast the same inputs with a higher fee, superseding the original (BIP-125)|
|Child-pays-for-parent|UTXO|Spend an output of the stuck transaction with a high-fee child; miners evaluate the package feerate|
|Nonce replacement|Account|Rebroadcast the same nonce with a higher tip, usually as a self-transfer to cancel|

Child-pays-for-parent is the only option when the original transaction did not signal replaceability, and it is the tool available to a recipient rather than a sender.

### The Transaction Lifecycle

_The end-to-end path, tying the preceding subsections together._

```text
  1. CONSTRUCT   The wallet selects inputs, or reads the account nonce,
                 builds outputs, and estimates a fee.
                          │
  2. SIGN        Private keys produce signatures over the protocol's
                 signature hash. Nothing has touched the network yet.
                          │
  3. BROADCAST   The signed transaction is submitted to a node, which
                 checks it against both consensus and policy rules.
                          │
  4. RELAY       Accepted into that node's mempool and gossiped onward.
                 Still fully reversible: it can be replaced or dropped.
                          │
  5. SELECT      A miner or block builder includes it in a candidate
                 block, ordering by feerate and extractable value.
                          │
  6. CONFIRM     The block is found or proposed and propagates. One
                 confirmation. Reversal is now possible but costly.
                          │
  7. SETTLE      Further blocks accumulate. Under proof of work the
                 assurance is probabilistic; under proof of stake,
                 finality is explicit after two epochs.
```

Steps 1 and 2 are entirely local and involve no network at all, which is exactly what makes air-gapped signing possible. Everything from step 3 onward is best effort: no step is guaranteed, and a transaction whose fee never clears the market can sit unconfirmed indefinitely, or be forgotten entirely when nodes evict it.

---

## Blocks and the Chain

_Batching transactions into an ordered, tamper-evident sequence._

### Block Structure

A block is a header plus a list of transactions. The header is small and self-contained, which is what allows light clients to verify proof of work without the block body.

Bitcoin's header is exactly 80 bytes:

|Field|Size|Contents|
|---|---|---|
|`version`|4 bytes|Rule signalling and soft-fork activation bits|
|`prev_block_hash`|32 bytes|Hash of the previous block's header|
|`merkle_root`|32 bytes|[[#Merkle Trees|
|`timestamp`|4 bytes|Miner-supplied Unix time, loosely constrained|
|`nBits`|4 bytes|Compact encoding of the current difficulty target|
|`nonce`|4 bytes|The value miners iterate|

Ethereum's header is larger because it commits to state as well as to transactions: it carries a state root, a receipts root, the gas used and gas limit, the base fee, the withdrawals root, and [[#Data Availability|blob]]-related fields.

> [!note] Four bytes of nonce is not enough At modern hashrates the 32-bit nonce is exhausted in a fraction of a second. Miners get additional search space from the [[#Coinbase Transactions|coinbase transaction]]'s extranonce field, which changes the Merkle root, and from rolling the timestamp and version bits.

### Chaining and Tamper Evidence

Each header contains the hash of its predecessor, so the headers form a chain in which every block depends on all of its ancestors.

```text
   Block n-1              Block n                Block n+1
 ┌────────────┐        ┌────────────┐         ┌────────────┐
 │ prev ──────┼───────►│ prev ──────┼────────►│ prev       │
 │ merkle root│        │ merkle root│         │ merkle root│
 │ nonce      │        │ nonce      │         │ nonce      │
 └────────────┘        └────────────┘         └────────────┘
       │                      │                      │
   [ tx set ]             [ tx set ]             [ tx set ]

  Altering any transaction changes its block's Merkle root,
  which changes that block's hash, which invalidates the
  "prev" field of every block after it.
```

Immutability is therefore not a cryptographic guarantee but a cost. Rewriting history requires redoing the work or restaking the stake for every block since the point of divergence, faster than the honest network extends the tip.

### Confirmations and Reorganisations

A transaction's confirmation count is the number of blocks built on top of the block containing it. Each additional block multiplies the cost of reversal.

A reorganisation happens when a node learns of a chain with more accumulated work or a better fork-choice score than the one it was following. It disconnects blocks back to the common ancestor, reconnects the new branch, and returns the orphaned transactions to its [[#The Mempool|mempool]]. Short reorgs of one block are routine and mostly harmless; deep reorgs are the signature of an attack or a severe consensus bug.

The conventional six confirmations for Bitcoin is a heuristic, not a protocol rule. The right threshold depends on transaction value against the cost of mounting a [[#Majority Attacks|majority attack]], and exchanges routinely apply different thresholds per asset and amount.

---

## Consensus

_How thousands of independent machines with no shared clock and no trusted party agree on one history._

### The Sybil Problem

Any open network can be flooded with fake identities at negligible cost, so "one node, one vote" is meaningless. Consensus therefore has to bind voting power to something that is genuinely scarce and expensive to fake.

|Mechanism|Scarce resource|Cost of attack|
|---|---|---|
|Proof of work|Energy and hardware|External, ongoing operational expenditure|
|Proof of stake|The chain's own coin|Internal, destroyed capital when misbehaviour is detected|
|Proof of authority|Reputation of named validators|Legal and reputational, not cryptoeconomic|
|Proof of space and time|Allocated storage|Capital cost of drives|

The second requirement is a rule for choosing between competing histories, since even with honest participants network delay produces temporary forks.

### Proof of Work

_Ties the right to extend the chain to verifiable expenditure of energy._

#### The Mining Loop

```text
  1. Collect transactions from the mempool, ordered by feerate.
  2. Build a coinbase transaction paying subsidy + fees to self.
  3. Compute the Merkle root over the whole transaction set.
  4. Assemble the 80-byte header.
  5. Compute HASH256(header).
  6. Is the result ≤ target?
        no  ──► increment nonce (or roll extranonce / timestamp) ──► go to 3 or 5
        yes ──► broadcast the block
```

There is no shortcut. Because the hash function has no exploitable structure, the expected number of attempts is `2^256 / (target + 1)`, which works out to roughly `difficulty × 2^32` hashes per block found.

Verification, in contrast, is a single hash. This asymmetry — expensive to produce, trivial to check — is the entire point.

#### Difficulty and Retargeting

Bitcoin adjusts the target every 2016 blocks so that, at the hashrate observed over that window, blocks would arrive every ten minutes on average. The adjustment is clamped to a factor of four in either direction to limit the damage from timestamp manipulation or sudden hashrate collapse.

Because block discovery is a Poisson process, intervals vary widely even at perfectly stable hashrate. A forty-minute gap between blocks is unremarkable; so is a pair of blocks thirty seconds apart.

> [!warning] Timestamps are not trustworthy A block's timestamp is chosen by its miner, constrained only to exceed the median of the previous eleven blocks and to not exceed network-adjusted time by more than two hours. Never use block timestamps as a precise clock; use block height where ordering matters.

#### Hardware Specialisation

Mining moved from CPUs to GPUs to FPGAs to application-specific integrated circuits within a few years of Bitcoin's launch. Any algorithm with a fixed, simple inner loop rewards specialised silicon by orders of magnitude in efficiency, so general-purpose hardware is priced out permanently.

Chains that want to preserve commodity-hardware participation choose deliberately hostile algorithms. Scrypt and Ethash are memory-hard, raising the cost of the memory subsystem rather than the arithmetic unit. RandomX goes further by generating random programs and executing them, which plays to exactly the branch prediction and instruction-level parallelism a general-purpose CPU is built for.

> [!note] ASIC resistance is a process, not a property No algorithm is permanently unspecialisable. Chains committed to resistance treat it as maintenance, hard-forking the algorithm whenever dedicated hardware appears.

#### Mining Pools

Solo mining at any realistic hashrate means an expected time-to-block measured in centuries. Pools solve the variance problem by having participants submit shares, which are hashes meeting a much easier pool target, as statistical proof of work performed. Rewards are then distributed proportionally.

|Scheme|Behaviour|
|---|---|
|Pay-per-share|Fixed payment per share, pool absorbs all variance and charges for it|
|Full pay-per-share|Pay-per-share including an expected fee component|
|Pay-per-last-N-shares|Pays from actual blocks found, discourages pool hopping, higher variance|

The centralisation concern is that pools historically chose the transaction set, concentrating censorship power in a handful of operators regardless of how widely the hashrate itself is distributed. Protocols such as Stratum V2 push template construction back to the individual miner to address this.

#### Majority Attacks

An attacker with more than half the hashrate can, for as long as the advantage lasts:

- Reverse their own recent transactions by mining a longer competing branch, enabling a double spend.
- Exclude specific transactions from the blocks they mine, censoring them.
- Deny other miners their rewards by orphaning their blocks.

The attacker cannot:

- Spend coins belonging to anyone else, since that requires the private key.
- Create coins beyond the subsidy schedule, since every node checks the rule.
- Change the supply cap, the block size, or any other consensus rule.

This distinction matters. A majority attack degrades settlement assurance; it does not compromise ownership. Smaller chains that share a hash algorithm with a larger one are structurally vulnerable, because rentable hashrate from the larger network can exceed their entire security budget.

### Proof of Stake

_Ties the right to extend the chain to coin at risk of destruction._

Ethereum's implementation is the reference design, and the terminology below follows it.

#### Validators and Deposits

A validator is created by depositing ETH into the deposit contract and registering a BLS public key for consensus duties. The base deposit is 32 ETH. Since EIP-7251 in the Pectra upgrade, a validator using the newer withdrawal credential type can hold an effective balance of up to 2048 ETH, so a large operator can consolidate what previously required dozens of separate validators into one.

Validators sign with BLS signatures rather than ECDSA, because BLS aggregates: the tens of thousands of attestations produced each epoch compress into a handful of aggregate signatures.

#### Slots, Epochs, and Duties

```text
  ├─ slot ─┤
  0    1    2    3    4   ...  31        32   33  ...
  │    │    │    │    │         │         │
  └────┴────┴────┴────┴─────────┘         └── next epoch
         one epoch = 32 slots = 6.4 minutes
         one slot  = 12 seconds

  Per slot:   1 proposer builds a block
              a committee of validators attests to what they see
  Per epoch:  every validator attests exactly once
```

Proposer selection is pseudorandom, seeded by RANDAO, a value each proposer contributes to and which no single party controls. An attestation is a vote carrying three claims: the head of the chain, the current justification source, and the target checkpoint.

#### Fork Choice and Finality

Two algorithms work together. LMD-GHOST selects the head by following, at each fork, the branch with the greatest weight of most-recent validator votes. Casper FFG runs on top and finalises checkpoints.

```text
  epoch N     epoch N+1     epoch N+2
     │             │             │
  checkpoint    checkpoint    checkpoint
     │             │             │
     └─ ⅔ of stake votes ───────►│   epoch N+1 justified
                   └─ ⅔ votes ──►│   epoch N   finalised
```

Once a checkpoint is finalised, reverting it requires at least one third of all staked ETH to have signed contradictory votes, which is provable on-chain and results in that stake being destroyed. This is economic finality, and it is qualitatively different from Bitcoin's probabilistic finality: the cost of reversion is a specific, quantifiable sum that is burned rather than an ongoing expenditure that can be repeated.

In normal operation finality lags the head by roughly 12.8 minutes.

#### Penalties and Slashing

|Condition|Consequence|
|---|---|
|Missed or late attestation|Small reward forfeiture proportional to the miss|
|Extended non-participation while the chain fails to finalise|Inactivity leak, draining offline validators until the active set can finalise again|
|Two different blocks proposed for one slot|Slashing|
|Two conflicting attestations for the same target|Slashing|
|One attestation surrounding another from the same validator|Slashing|

Slashing burns part of the stake immediately, forces an exit, and applies a correlation penalty scaled by how many other validators were slashed nearby in time. A lone misconfiguration is expensive; a coordinated attack by a large operator is ruinous.

> [!warning] Duplicate signing is the operator's real risk Almost all slashing incidents come from running the same validator keys on two machines at once, typically during a botched failover or migration. Redundancy at the key level is not resilience — it is the failure mode.

#### Withdrawals and Exits

Since the Shapella upgrade of April 2023, staked ETH is withdrawable. Withdrawals are not transactions and pay no fee; the protocol sweeps eligible balances automatically.

- A partial withdrawal skims any balance above the validator's maximum effective balance, leaving it staked and active.
- A full exit removes the validator from the active set after a queue delay and returns the entire balance.

Both entry and exit are rate-limited by churn limits, which prevent the validator set from turning over faster than the network's security assumptions allow.

### Other Sybil-Resistance Mechanisms

|Mechanism|Used by|Principle|
|---|---|---|
|Delegated proof of stake|EOS, Tron|Coin holders elect a small fixed set of block producers|
|Proof of history|Solana|A verifiable delay function timestamps events, so ordering precedes consensus|
|Proof of space and time|Chia|Plots of allocated disk prove committed storage|
|Proof of authority|Consortium and testnet chains|A known, permissioned validator set|
|Nakamoto-style hybrids|Decred|Proof of work blocks ratified by staked ticket holders|

### Comparing Proof of Work and Proof of Stake

|Dimension|Proof of work|Proof of stake|
|---|---|---|
|Security budget|Ongoing energy and hardware spend|Capital locked and slashable|
|Cost of attack|Rent or build hashrate for the attack window|Acquire and then forfeit a third of the stake|
|Attack repeatability|Hardware survives, attack can be repeated|Stake is burned, attack is one-shot|
|Finality|Probabilistic, strengthening with depth|Economic, explicit after two epochs|
|Entry requirement|Capital plus cheap electricity|Capital plus a reliable, always-on host|
|Failure under partition|Both branches continue, longest wins on heal|Neither finalises, inactivity leak resolves it|
|New-entrant sync trust|Fully objective from genesis|Requires a recent trusted checkpoint, called weak subjectivity|

The weak-subjectivity difference is the one with practical consequences for operators: a proof-of-work node can verify the correct chain from genesis using nothing but the protocol rules, while a proof-of-stake node syncing from scratch must be given a recent finalised checkpoint out of band to rule out a long-range alternative history. See [[#Synchronisation|synchronisation]].

---

## The Peer-to-Peer Network

_The transport layer. Consensus rules define what is valid; the network layer determines what each node gets to see._

### Discovery and Gossip

A new node needs a way into the mesh. Bitcoin queries hardcoded DNS seeds, falls back to a compiled-in address list, then maintains its own peer database. Ethereum uses discv5, a Kademlia-style distributed hash table over UDP, seeded by bootnodes.

Once connected, transactions and blocks propagate by flooding. Bitcoin announces identifiers first and lets peers request bodies only for what they lack, and uses compact block relay (BIP-152) to send a block as a short list of transaction identifiers plus any transactions the peer is presumed to be missing. Ethereum's consensus layer uses libp2p gossipsub with topic-based subscription.

|Chain|Transport|Default port|
|---|---|---|
|Bitcoin|Custom binary P2P protocol over TCP|8333|
|Ethereum execution|RLPx over TCP, discv5 over UDP|30303|
|Ethereum consensus|libp2p gossipsub over TCP, discv5 over UDP|9000|

Propagation delay is a direct security parameter. Slow relay means more orphaned blocks, which advantages large, well-connected miners and pushes toward centralisation.

### Node Types

|Type|Stores|Verifies|Trust assumption|
|---|---|---|---|
|Archival|Every block plus all historical state|Everything from genesis|None|
|Full|Every block, current state, recent history|Everything from genesis or a checkpoint|None, or a checkpoint|
|Pruned|Recent blocks plus current state|Everything, then discards old block data|None|
|Light or SPV|Headers only|Proof of work on headers, Merkle inclusion proofs|Assumes the most-work header chain is valid|
|Remote RPC|Nothing|Nothing|Full trust in the provider|

Only a validating node enforces the rules for you. A light client verifies that a transaction is in a block whose header has valid work, but not that the block obeys consensus rules. A wallet pointed at a third-party endpoint verifies nothing at all and is trusting that provider for balances, fee estimates, and broadcast.

BIP-157 and BIP-158 compact block filters improve light clients meaningfully: the node downloads a small filter per block, decides locally whether the block is of interest, and requests only those blocks — without revealing to the server which addresses it cares about, as the older BIP-37 bloom filters did.

### Synchronisation

|Mode|Chain|Behaviour|
|---|---|---|
|Initial block download|Bitcoin|Fetch and validate every block from genesis, with signature checks skipped below a hardcoded assumed-valid hash|
|Snap sync|Ethereum execution|Download a recent state snapshot, then verify forward and heal the trie in the background|
|Full sync|Ethereum execution|Re-execute every transaction from genesis, the only way to independently reconstruct all historical state|
|Checkpoint sync|Ethereum consensus|Start from a recent finalised state root obtained out of band|

Checkpoint sync is where [[#Comparing Proof of Work and Proof of Stake|weak subjectivity]] becomes operational. The checkpoint should come from a source you actually trust, and ideally be cross-checked against several independent providers or a block explorer before the node is left to run unattended.

### Ethereum's Split Client Architecture

Since the Merge in September 2022, an Ethereum node is two processes:

```text
   ┌──────────────────────────┐        ┌──────────────────────────┐
   │   Execution client       │        │   Consensus client       │
   │   (Geth, Nethermind,     │        │   (Lighthouse, Prysm,    │
   │    Besu, Erigon, Reth)   │        │    Teku, Nimbus, Lodestar)│
   │                          │        │                          │
   │  • EVM execution         │◄──────►│  • Fork choice           │
   │  • State and storage     │ Engine │  • Attestations          │
   │  • Transaction pool      │  API   │  • Finality              │
   │  • JSON-RPC to users     │  :8551 │  • Validator duties      │
   └──────────────────────────┘  JWT   └──────────────────────────┘
              │                                    │
         devp2p :30303                      libp2p :9000
```

The Engine API between them is authenticated with a shared JWT secret. Both processes must be running and in sync for the node to be usable; an execution client alone cannot follow the chain, because it no longer has a fork-choice rule of its own.

Client diversity is a live safety concern rather than a preference. If a single execution or consensus client holding more than a third of the network produced an invalid block, finality would stall; above two thirds, an incorrect chain could finalise. Running a minority client is a meaningful contribution to network health.

---

## Monetary Policy and Issuance

_Where new coins come from, and what stops there being more of them._

### Bitcoin's Emission Schedule

The subsidy starts at 50 BTC per block and halves every 210,000 blocks, roughly every four years.

|Era|Block height|Subsidy|
|---|---|---|
|2009|0|50 BTC|
|2012|210,000|25 BTC|
|2016|420,000|12.5 BTC|
|2020|630,000|6.25 BTC|
|2024|840,000|3.125 BTC|
|Next, expected 2028|1,050,000|1.5625 BTC|

Integer arithmetic means the subsidy reaches zero after 33 halvings, around the year 2140, converging on a supply just under 21 million. Around 20 million had been issued by 2026, so more than 95 percent of all bitcoin that will ever exist already does.

> [!note] The cap is a rule, not a reservoir There is no pool of unissued coins anywhere. The cap is the arithmetic consequence of the halving schedule, checked independently by every validating node on every block. A block paying itself more than the schedule allows is simply rejected.

The long-term question this creates is the security budget: as the subsidy trends to zero, proof of work must be paid for entirely by transaction fees. Whether fee demand will be sufficient, and how volatile it will be, is unresolved and is the strongest argument advanced for and against alternative designs.

### Ethereum's Issuance and Burn

ETH issuance is paid to [[#Validators and Deposits|validators]] and scales roughly with the square root of total stake, so per-validator yield falls as more ETH is staked. There is no cap and no halving.

Against this runs the EIP-1559 base fee burn, which destroys the base fee of every transaction. Net supply change is therefore:

```text
  net issuance = validator rewards − base fee burned

  low network activity   ──►  net issuance positive, supply grows slowly
  high network activity  ──►  net issuance negative, supply shrinks
```

The result is a supply schedule that varies with demand for blockspace rather than following a fixed curve. Rollup adoption complicates this: activity that moves to layer two burns far less base fee on layer one, which is why the network has generally been mildly inflationary in low-fee periods. See [[#Rollups|rollups]].

### Other Supply Designs

|Design|Example|Rationale|
|---|---|---|
|Hard cap with halvings|Bitcoin, Litecoin|Absolute scarcity, predictable schedule|
|Perpetual tail emission|Monero, 0.6 XMR per block|Permanent security budget, avoids fee-only reliance|
|Uncapped, demand-linked|Ethereum|Issuance targets security, burn offsets it|
|Fixed inflation rate|Many proof-of-stake chains|Predictable validator yield, dilutes non-stakers|
|Fully pre-mined|Ripple, Stellar|No issuance, distribution decided at launch|
|Deflationary burns|Various tokens|Discretionary, usually a marketing mechanism rather than a monetary policy|

The trade-off is always the same. A hard cap maximises the scarcity narrative but leaves the long-run security budget dependent on the fee market; a tail emission guarantees a security budget but permanently dilutes holders.

---

## Protocol Change and Forks

_Changing the rules of a system whose defining property is that nobody controls it._

### Soft Forks

A soft fork tightens the rules: everything valid under the new rules was already valid under the old. Old nodes still accept the new blocks, since they cannot tell that a stricter rule is being applied.

Bitcoin has used this repeatedly, encoding new features inside constructs old nodes treat as unconditionally valid.

|Soft fork|Year|Mechanism|
|---|---|---|
|P2SH (BIP-16)|2012|Redefines a previously-anyone-can-spend pattern to require a script matching a hash|
|CLTV, CSV|2015–2016|Repurposes no-operation opcodes as absolute and relative timelocks|
|SegWit (BIP-141)|2017|Moves witness data to a structure old nodes do not parse|
|Taproot (BIP-341)|2021|Redefines a new witness version, invisible to old nodes|

The compatibility is one-directional and partial. An old node relays and accepts the blocks but does not enforce the new rule, so it is trusting the upgraded majority for that specific rule.

### Hard Forks

A hard fork loosens or changes rules so that new blocks are invalid under the old software. Every node must upgrade or be left on a different chain. Ethereum's upgrades are all hard forks, coordinated by scheduling activation at a specific block height or epoch and shipping every client ahead of time.

|Upgrade|Date|Principal change|
|---|---|---|
|The Merge|September 2022|Replaced proof of work with [[#Proof of Stake|
|Shapella|April 2023|Enabled validator withdrawals|
|Dencun|March 2024|Introduced blobs (EIP-4844) for rollup data|
|Pectra|May 2025|Raised the maximum effective balance, added EOA code delegation, doubled blob throughput|
|Fusaka|December 2025|PeerDAS data availability sampling, standardised a higher gas limit, per-transaction gas cap|

Coordinated hard forks are not inherently contentious. What makes a fork dangerous is disagreement about whether it should happen, not the technical class of the change.

### Activation Mechanisms

|Mechanism|How it works|
|---|---|
|Flag day|Activates at a fixed height or timestamp regardless of signalling|
|BIP-9 version bits|Miners signal readiness in the header; activates on reaching a threshold within a window, otherwise expires|
|BIP-8|Like BIP-9, but with an optional mandatory activation at timeout|
|Speedy Trial|A short BIP-9 signalling window with a deferred activation height, used for Taproot|
|User-activated soft fork|Economic nodes begin enforcing on a set date, obliging miners to follow|

Miner signalling is a coordination device, not a vote. Miners choose block contents; the nodes that economic participants run choose which blocks are valid. A soft fork enforced by exchanges, wallets, and merchants succeeds regardless of miner preference.

### Chain Splits

When a hard fork is contentious, both branches persist and the coin exists twice from the split point onward. Every holder at the split height controls funds on both.

|Split|Origin|
|---|---|
|Ethereum Classic, 2016|Disagreement over reversing the DAO exploit|
|Bitcoin Cash, 2017|Disagreement over block size versus SegWit|
|Bitcoin SV, 2018|Further split from Bitcoin Cash|

Replay protection is the essential technical detail. Without it, a transaction broadcast on one branch is valid on the other, so spending on one chain can unintentionally spend on both. Ethereum solved this with `chainId` in EIP-155; Bitcoin Cash added a modified signature hash. See [[#Anatomy of an Account-Model Transaction|chainId]].

### Governance

There is no formal governance in Bitcoin or Ethereum. Change proceeds through published proposals — BIPs and EIPs — implemented in client software, adopted voluntarily by node operators.

|Stakeholder|Actual power|
|---|---|
|Client developers|Write and ship the code, but cannot force adoption|
|Node operators|Choose which rules to enforce; collectively decisive|
|Miners or validators|Order transactions and produce blocks within the rules|
|Exchanges and custodians|Determine which chain carries the ticker and the liquidity|
|Users and merchants|Determine which chain has economic value at all|

On-chain governance chains such as Tezos and Cosmos formalise this with coin-weighted voting and automatic deployment. The trade-off is explicit: faster, more legible upgrades in exchange for plutocratic control and a much larger attack surface around the voting mechanism itself.

---

## Programmability

_What the chain will let you express, and what it charges you for expressing it._

### Bitcoin Script

A stack-based, deliberately constrained language with no loops, no recursion, and no access to state beyond the transaction being validated. This is a design choice: it makes validation cost predictable from the transaction's size alone.

A spend succeeds when the unlocking data, followed by the locking script, leaves a true value on the stack.

```text
  scriptSig (from the input)      scriptPubKey (from the output being spent)
  <signature> <pubkey>            OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG
  └────────────────────────────────┴──────────────────────────────────────┘
                     executed left to right on one stack
```

|Opcode|Purpose|
|---|---|
|`OP_CHECKSIG`|Verify a signature against a public key and the signature hash|
|`OP_CHECKMULTISIG`|Verify `m` of `n` signatures|
|`OP_CHECKLOCKTIMEVERIFY`|Fail unless an absolute height or time has passed|
|`OP_CHECKSEQUENCEVERIFY`|Fail unless a relative age has elapsed since the output was created|
|`OP_RETURN`|Mark an output provably unspendable, used to embed small data commitments|

The timelock opcodes are what make payment channels enforceable, since they let a script say "this branch becomes spendable only after a delay".

#### Taproot

Taproot combines [[#Schnorr Signatures|Schnorr signatures]] with a Merkle tree of alternative spending scripts, called MAST.

An output commits to a public key that is itself a normal key tweaked by the Merkle root of a script tree. It can be spent two ways:

- Key path: everyone agrees, so they produce one aggregated Schnorr signature. On-chain this is indistinguishable from a simple single-signature payment.
- Script path: cooperation failed, so the spender reveals only the one branch being used, plus a Merkle proof. All other branches remain secret forever.

The privacy and efficiency gains are substantial. A complex contract that settles cooperatively leaves no trace of its complexity, and even a contested settlement discloses only the branch actually taken.

### The Ethereum Virtual Machine

A deterministic, quasi-Turing-complete stack machine with 256-bit words. Every node executes every transaction and must arrive at exactly the same resulting state, which forbids anything non-deterministic: no real randomness, no clock beyond block values, no network or filesystem access.

#### Gas Metering

Every operation has a gas cost, and the transaction's gas limit bounds total consumption. When the limit is exhausted, execution reverts entirely but the gas is still consumed. This is the halting-problem workaround: the EVM does not need to decide whether a program terminates, because the sender has paid for a finite budget in advance.

|Operation class|Relative cost|Reason|
|---|---|---|
|Arithmetic and stack|Very low|Pure computation|
|Memory expansion|Grows quadratically|Discourages unbounded allocation|
|`SLOAD`, storage read|Moderate, cheaper if already warm within the transaction|Touches the state trie|
|`SSTORE`, storage write|High, with a refund for clearing a slot|Permanently enlarges state every node must keep|
|Contract creation|Very high|Adds code every node stores forever|

The cost table encodes a policy: operations that impose permanent costs on every future node are priced far above operations that are merely computation. EIP-7825, activated with Fusaka, additionally caps any single transaction at roughly 16.78 million gas.

#### State Storage

Ethereum's state lives in a Merkle Patricia Trie, a radix trie with hashed nodes. The root is committed in every block header, so any account balance or storage slot can be proved against a single 32-byte value.

The cost of this design is state growth. Every contract deployed and every storage slot written must be retained by every full node indefinitely. History expiry, which drops pre-Merge block bodies, has recovered substantial disk space, but expiring live state remains an open problem on the roadmap.

### Token Standards

A token is a contract that maintains its own internal ledger. There is no protocol-level concept of a token; the chain only sees a contract's storage changing.

|Standard|Type|Core interface|
|---|---|---|
|ERC-20|Fungible|`balanceOf`, `transfer`, `approve`, `transferFrom`|
|ERC-721|Non-fungible|`ownerOf`, `safeTransferFrom`, per-token identifiers|
|ERC-1155|Multi-token|Batch operations over fungible and non-fungible identifiers in one contract|
|ERC-4626|Tokenised vault|Standardised deposit and redemption accounting for yield-bearing shares|

Two consequences deserve emphasis:

- Sending tokens costs the chain's native coin. An account holding tokens but no ETH cannot move them.
- The `approve` pattern grants a spender an allowance that persists until revoked. Unlimited approvals to compromised or malicious contracts are one of the most common causes of loss, and they are granted by a signature that costs nothing and looks innocuous. See [[#Endpoint and Key Compromise|endpoint compromise]].

---

## Scaling

_Why base layers are slow on purpose, and what gets built to work around it._

### The Base-Layer Constraint

Every full node validates every transaction. Raising throughput raises the cost of running a node, which reduces the number of independent verifiers, which weakens the property that made the system worth using.

This is usually framed as a trilemma between decentralisation, security, and scalability, in which a monolithic design can prioritise two. It is not a theorem, but it is a useful summary of the pressure: bandwidth, storage, and validation CPU all scale with throughput, and each one prices out a class of would-be node operators.

The modular response is to keep the base layer small and verifiable, and move execution elsewhere while still settling on it.

### Payment Channels

Two parties lock funds in a multisignature output and then exchange signed transactions off-chain, each superseding the last. Only opening and closing touch the chain.

```text
  on-chain: funding transaction    (2-of-2 multisig, 1.0 BTC)
                    │
      off-chain ────┼──── state 1:  Alice 0.9  Bob 0.1
                    │     state 2:  Alice 0.7  Bob 0.3
                    │     state 3:  Alice 0.4  Bob 0.6     ← thousands of updates
                    │
  on-chain: settlement transaction (pays out the final agreed state)
```

The security problem is that an old, more favourable state is still a validly signed transaction. Lightning solves it with a revocation mechanism: publishing a revoked state lets the counterparty claim the entire channel balance during a timelock window. Watchtowers can monitor for this on behalf of an offline node.

Hash time-locked contracts extend two-party channels into a routed network, so payments hop across channels without any intermediate node being able to steal in transit. The trade-offs are real: liquidity must be committed in advance and is directional, receiving requires inbound capacity, and both parties must be online to transact.

### Rollups

A rollup executes transactions off-chain and posts the resulting data, plus a correctness argument, to the base layer. The base layer never re-executes but does guarantee the data is available, so anyone can reconstruct and challenge the rollup's state.

|Type|Correctness argument|Withdrawal delay|Trade-off|
|---|---|---|---|
|Optimistic|Assumed valid; anyone may submit a fraud proof during a challenge window|Around seven days|Simple and EVM-compatible, but slow exits|
|Zero-knowledge (validity)|A succinct proof verified on-chain with every batch|Minutes to hours|Fast finality, but proving is expensive and the circuits are complex|

A rollup inherits the base layer's data availability and settlement, not its liveness or its governance. Most production rollups still run a single sequencer and retain upgrade keys, so the honest description is that they inherit security conditional on the escape hatches actually working.

### Data Availability

The dominant cost for a rollup is publishing its data. Ethereum's answer has been a dedicated, cheaper lane:

|Stage|Mechanism|
|---|---|
|Before March 2024|Rollup data posted as calldata, competing directly with regular transactions for gas|
|Dencun, EIP-4844|Blobs — large data attachments priced in their own fee market and pruned by nodes after roughly 18 days|
|Pectra|Blob target and maximum per block raised|
|Fusaka, EIP-7594|PeerDAS, where validators sample fragments of blob data instead of downloading it whole, and blob-parameter-only forks that raise capacity without a full hard fork|

Sampling is the key idea. A validator that randomly checks a few fragments and finds them all present has high statistical confidence that the whole blob was published, so capacity can rise without every node's bandwidth rising in proportion.

### Sidechains and Bridges

A sidechain is an independent chain with its own consensus and its own security budget, connected by a bridge. It does not inherit anything from the chain it is pegged to.

Bridges hold assets on one side and issue representations on the other, which makes the lock contract or custodian a single concentrated target. Bridge compromises account for several of the largest losses in the industry's history, and the reason is structural rather than incidental: the bridge holds the full value of everything it has ever issued.

> [!warning] A wrapped asset is a claim, not the asset Wrapped BTC on another chain is a token backed by a custodian or a bridge contract. Its risk profile is that custodian's, not Bitcoin's, however similar the ticker looks.

---

## Privacy

_Public ledgers are permanent and globally readable. Privacy is an active effort, never a default._

### Pseudonymity Is Not Anonymity

Addresses are not names, but every transaction they ever make is permanently public and linkable. One disclosure — a KYC exchange deposit, a donation address on a website, a reused address — retroactively deanonymises the entire history connected to it, and prospectively deanonymises everything that follows.

There is no expiry. Analysis techniques improve over time and are applied to a dataset that never disappears.

### Chain Analysis Heuristics

|Heuristic|Inference|
|---|---|
|Common input ownership|All inputs to a transaction are usually controlled by one party|
|Change detection|Round-number outputs are payments; the odd remainder is change|
|Address reuse|Directly links every transaction sharing an address|
|Script type fingerprinting|Wallet software is identifiable from address types, input ordering, locktime, and version fields|
|Timing and amount correlation|Links deposits and withdrawals across services|
|Network-level observation|A well-connected observer can often infer which node first broadcast a transaction|

The account model is worse in practice, because a single address is typically reused indefinitely and the entire balance and history is visible from one lookup.

### Privacy Techniques on Transparent Chains

|Technique|Effect|Limitation|
|---|---|---|
|Address reuse avoidance|Breaks the simplest linkage|Undone by common-input-ownership|
|CoinJoin|Many participants build one transaction with uniform outputs, breaking input-output linkage|Requires coordination; participation is itself visible|
|PayJoin|The recipient contributes an input, falsifying the common-input heuristic|Requires an interactive, capable recipient|
|Silent payments (BIP-352)|A single published address from which the sender derives a unique unlinkable output|Requires wallet scanning support|
|Taproot key-path spends|Complex contracts appear as ordinary payments|Only when all parties cooperate|
|Running your own node|Removes address disclosure to a third-party server|Does not affect on-chain linkability|

### Privacy-by-Default Chains

Monero makes privacy mandatory rather than optional, which matters because an optional privacy set is small enough to be suspicious by itself.

|Mechanism|Hides|
|---|---|
|Stealth addresses|The recipient — every payment goes to a fresh one-time address derived by the sender|
|RingCT|The amount, via Pedersen commitments and range proofs|
|Ring signatures|The sender, by proving membership of a set that includes decoys|
|Dandelion++|The originating node, by relaying along a random stem before diffusion|

Ring signatures are the historically weakest link, because a bounded decoy set is amenable to statistical attack. Full-chain membership proofs (FCMP++) are the intended replacement, proving membership of the entire output set rather than a small ring; the deployment timeline has moved more than once, so its current status should be checked against the project's own release notes rather than assumed.

Zcash takes the alternative route of optional shielded transactions using zk-SNARKs, which are cryptographically strong but suffer from a smaller shielded pool in practice.

> [!note] Auditability is the cost Confidential amounts mean the total supply cannot be verified by simple summation. A chain with hidden amounts relies instead on the soundness of its range proofs, and a flaw there permits inflation that nobody can detect by inspecting the ledger. This is not hypothetical: Zcash patched a counterfeiting vulnerability found in 2018, and Monero patched an inflation bug in 2017. Both were caught by review rather than by observing the supply.

---

## Stablecoins

_Instruments pegged to an external asset. Almost all are [[#Coins Versus Tokens|tokens]], and their risk lives entirely outside the consensus layer._

|Type|Peg mechanism|Principal risk|
|---|---|---|
|Fiat-collateralised|Reserves held by an issuer, redeemable at par|Issuer solvency, banking access, freeze and blacklist authority|
|Crypto-collateralised|Overcollateralised on-chain positions with liquidation|Collateral crash faster than liquidations can clear|
|Commodity-backed|Physical reserve with an attestation|Custodian and audit quality|
|Algorithmic|Supply expansion and contraction against a companion asset|Reflexive collapse once confidence breaks|

The failure of algorithmic designs is not a matter of implementation quality. A peg maintained by minting a companion token depends on that token having value, which depends on the peg holding — a circularity that unwinds catastrophically under sustained redemption pressure.

For fiat-backed stablecoins, note that the issuer typically retains the ability to freeze balances at specific addresses. That is a feature for law enforcement and a counterparty risk for the holder, and it is not something the chain can prevent.

---

## Threat Model

_What can go wrong, sorted by which layer it attacks._

### Protocol-Level Attacks

|Attack|Applies to|Description|
|---|---|---|
|Majority hashrate|Proof of work|Reorganise recent history to double-spend or censor, for as long as the hashrate advantage lasts|
|Long-range|Proof of stake|Build an alternative history from an old checkpoint using withdrawn keys; mitigated by weak subjectivity checkpoints|
|Finality reversion|Proof of stake|Requires one third of stake signing conflicting votes, and burns that stake|
|Selfish mining|Proof of work|Withhold found blocks to waste competitors' work, profitable above a hashrate threshold|
|Time-warp|Proof of work|Manipulate timestamps to lower difficulty; constrained by the median-time rule|
|Consensus bug|Any|A client disagreeing with its peers about validity causes an unintentional chain split|

### Network-Level Attacks

|Attack|Description|
|---|---|
|Eclipse|Monopolise all of a victim node's peer connections and feed it a fabricated view of the chain|
|Partition|Split the network by BGP hijack or routing manipulation, so branches diverge|
|Transaction censorship|Refuse to relay or include specific transactions|
|Denial of service|Exhaust mempool memory, connection slots, or validation CPU with cheap junk|

Eclipse is the enabler for most of the rest. Its practical countermeasures are the mundane ones: allow inbound connections, use diverse and manually specified peers where appropriate, and never rely on a single network path.

### Economic Extraction

Maximal extractable value is the profit available to whoever orders transactions in a block.

|Form|Mechanism|
|---|---|
|Front-running|Insert a transaction ahead of a known profitable one|
|Sandwiching|Trade before and after a victim's swap, capturing the price movement|
|Back-running|Follow a state change immediately, taking an arbitrage or liquidation|
|Time-bandit reorg|Reorganise past blocks to re-extract value, threatening consensus stability itself|

Proposer-builder separation splits block construction from block proposal so that proposers auction the ordering right rather than exercising it. Enshrining this in the protocol is a central goal of Ethereum's next upgrade cycle.

### Endpoint and Key Compromise

Practically all realised losses happen here, not at the protocol layer.

|Vector|Countermeasure|
|---|---|
|Malware capturing seeds or clipboard contents|Hardware signer, verify the address on the device screen|
|Phishing sites and fake wallet applications|Bookmarks over search results, verify software signatures|
|Malicious token approvals|Review and revoke allowances, avoid unlimited approvals|
|Blind signing of opaque payloads|Refuse signatures the wallet cannot decode into human-readable terms|
|Address poisoning, dust sent from lookalike addresses|Never copy an address from transaction history|
|Supply-chain compromise of dependencies or firmware|Verify release signatures and reproducible builds|
|SIM swap against SMS-based recovery|Hardware second factor, no phone-based recovery|
|Backup loss or a single point of failure|Geographically distributed backups, multisignature, tested recovery|

> [!important] Test the recovery, not the backup A backup that has never been restored is a hypothesis. Restore from the seed onto a clean device and confirm the addresses match before the backup is relied on for anything of value.

---

## Verifying Things Yourself

_The property that distinguishes a cryptocurrency from a database is that you can check it. That property is only real if you exercise it._

### Why Run a Node

A node lets you enforce the rules rather than trusting somebody's report of them. Concretely, running your own node means:

- Consensus rules are enforced by software you chose, so a fork you disagree with does not silently become your chain.
- Balances and confirmations are computed locally, so no server can lie about them.
- Wallet queries do not reveal your addresses to a third party.
- Transactions are broadcast directly rather than through an intermediary that could delay or drop them.

### What a Node Actually Verifies

|Check|Purpose|
|---|---|
|Proof of work or attestation validity on every header|The chain represents real expenditure or real stake|
|Every signature on every input|No unauthorised spending|
|No output spent twice|The double-spend rule|
|Subsidy and fee arithmetic in each coinbase|Supply cap enforcement|
|Script or EVM execution of every transaction|Contract rules were honoured|
|Block size, weight, or gas limits|Resource bounds respected|
|Timestamp and difficulty rules|Schedule integrity|

Note what is absent: nothing about price, nothing about intent, and nothing about whether a transaction was a good idea.

### Practical Verification Habits

```bash
# Verify a release before running it — signatures first, then the hash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum --ignore-missing --check SHA256SUMS

# Bitcoin Core: confirm the node is fully synced and validating
bitcoin-cli getblockchaininfo | jq '{blocks, headers, verificationprogress, pruned}'
bitcoin-cli getnetworkinfo   | jq '{version, connections, networkactive}'

# Confirm a transaction independently rather than trusting an explorer
bitcoin-cli getrawtransaction <txid> 1 | jq '{confirmations, blockhash}'

# Ethereum: check the two clients agree and are actually in sync
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}' \
  http://127.0.0.1:8545
curl -s http://127.0.0.1:5052/eth/v1/node/syncing | jq
```

> [!tip] Cross-check the checkpoint When bootstrapping a consensus client from a checkpoint, compare the finalised block root against two or more independent sources before leaving the node unattended. It is the one moment where a proof-of-stake node genuinely depends on external trust.

---

## Coin Architecture Comparison

_A summary of how the design choices above combine in production systems._

|Chain|Consensus|Ledger model|Signature scheme|Block interval|Supply policy|
|---|---|---|---|---|---|
|Bitcoin|Proof of work, SHA-256|UTXO|ECDSA and Schnorr on secp256k1|~10 minutes|Capped at 21 million, halving every 210,000 blocks|
|Ethereum|Proof of stake, Casper FFG with LMD-GHOST|Account|ECDSA on secp256k1, BLS for consensus|12-second slots|Uncapped, offset by base fee burn|
|Litecoin|Proof of work, Scrypt|UTXO|ECDSA on secp256k1|~2.5 minutes|Capped at 84 million|
|Monero|Proof of work, RandomX|UTXO with confidential amounts|Ring signatures on Ed25519|~2 minutes|Tail emission of 0.6 XMR per block|
|Solana|Proof of stake with proof of history|Account|Ed25519|~400 ms|Fixed inflation decaying to a floor|
|Cardano|Proof of stake, Ouroboros|Extended UTXO|Ed25519|~20 seconds between blocks|Capped at 45 billion|
|Zcash|Proof of work|UTXO with optional shielded pool|Ed25519 with zk-SNARKs|~75 seconds|Capped at 21 million|

> [!note] Read the comparison as a set of trade-offs Faster blocks buy latency at the cost of higher orphan rates and heavier bandwidth requirements. Richer contract expressiveness buys functionality at the cost of a larger attack surface and unbounded state growth. Mandatory privacy buys fungibility at the cost of supply auditability. None of the rows above is strictly better than another; each one is a different position on the same set of trade-offs.