---
categories:
  - "[[Systems]]"
topic@systems:
tags:
  - claude
  - tobecompleted
  - Systems
icon: SiBitcoin
iconColor: "#F38423"
---
_A fully self-hosted Bitcoin and Ethereum node stack — full chain validation, private wallet connectivity, and address monitoring — packaged as a hardened Docker Compose deployment with every config file included inline._

This stack lets your wallets talk directly to nodes you run and verify, instead of trusting third-party servers such as Blockchain.info, Infura, or Etherscan. It downloads and validates both blockchains, serves wallet queries over a private local connection, watches addresses for incoming and outgoing activity, and broadcasts your transactions straight to the network. It never stores private keys or holds funds — your hardware wallet does that, and it never replaces your wallet software.

## Overview and architecture

_The six services, how they connect, and how the Docker networks isolate them._

The stack runs six containers across two chains. On the Bitcoin side, `bitcoind` validates every block, Fulcrum builds an Electrum index so wallets can query balances instantly, and a monitor watches your addresses. On the Ethereum side, `geth` is the execution layer, `lighthouse` is the consensus layer required after the Merge, and a second monitor watches your Ethereum addresses.

### Services

|Service|Role|Chain|
|---|---|---|
|`bitcoind`|Full node, validates all blocks|Bitcoin|
|`fulcrum`|Electrum index, serves wallet queries|Bitcoin|
|`btc-monitor`|Watches Bitcoin addresses for activity|Bitcoin|
|`geth`|Execution layer, stores chain state|Ethereum|
|`lighthouse`|Consensus layer, required post-Merge|Ethereum|
|`eth-monitor`|Watches Ethereum addresses for activity|Ethereum|

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   YOUR MACHINE                       │
│                                                      │
│  ┌──────────────────┐    ┌────────────────────────┐  │
│  │   BITCOIN STACK  │    │   ETHEREUM STACK       │  │
│  │  bitcoind        │    │  geth (execution)      │  │
│  │    └─ fulcrum    │    │  lighthouse (consensus)│  │
│  │    └─ btc-monitor│    │  eth-monitor           │  │
│  └──────────────────┘    └────────────────────────┘  │
│                                                      │
│  Sparrow Wallet ──────────── fulcrum:50001           │
│  MetaMask / Frame ─────────── geth:8545              │
│                                                      │
│             Hardware Wallet (Ledger/Trezor)          │
│             Signs transactions offline               │
└─────────────────────────────────────────────────────┘
         │                          │
  Bitcoin P2P (8333)        Ethereum P2P (30303)
```

### Docker network isolation

_Five Docker networks separate internet-facing peer traffic from internal RPC, and keep the monitors sealed off from the outside._

```
btc-external  ── bitcoind ─────────────────────── internet (8333)
btc-internal  ── bitcoind, fulcrum, btc-monitor   (no internet)
eth-external  ── geth, lighthouse ─────────────── internet (30303, 9000)
eth-internal  ── geth, lighthouse, eth-monitor    (no internet)
monitoring    ── btc-monitor, eth-monitor         (no internet, isolated)
```

The RPC ports (8332, 8545, 8551) are never published to the host — they exist only on the internal Docker networks.

> [!important] Both monitors sit on `internal: true` networks only, so they can reach `bitcoind` and `geth` but have no route to the public internet. That is deliberate for isolation, but it means an `ALERT_WEBHOOK_URL` pointing at an external service (ntfy.sh, Discord, Slack) is unreachable. See [[#Webhook to your backend|receiving webhooks]] for the two supported options.

## Storage

_Why a trustless node is large, how fast it grows, and what you can cut._

You are storing the entire history of two blockchains — every transaction ever made, not just your own wallet. That is what makes the node trustless: it verifies everything itself rather than asking someone else.

### What each service stores

Bitcoin Core holds roughly 600 GB — every block since January 2009. The `txindex=1` option adds a secondary index of every transaction by ID, which Fulcrum and Sparrow need to look up wallet history; without it you would save about 150 GB but wallet-history queries would break.

Fulcrum holds roughly 100 GB. It builds its own address-to-UTXO index on top of Bitcoin Core so wallets can query balances instantly without rescanning the chain on every request. Periodic [[#Fulcrum database compaction|compaction]] keeps this database lean.

Geth holds roughly 950 GB with the [[#Geth path-based state scheme|path-based state scheme]]. Ethereum is larger than Bitcoin because it stores not just transactions but the current state of every smart contract, token balance, and DeFi position. Snap sync (the default) is already the most space-efficient sync mode; archive mode would be 3–4 TB.

Lighthouse holds roughly 70 GB with pruning enabled. It stores beacon-chain history since the Merge. Lighthouse v8.x prunes by default: payload pruning discards execution-layer payloads once finalised (Geth already holds them), and blob pruning removes old blob data after the minimum network retention period of about 18 days. Since the Fusaka fork, a full node custodies only a subset of blob columns under PeerDAS, keeping this footprint smaller than it was before. Lighthouse is required for Geth to know the canonical chain tip.

### Monthly growth

|Service|Current (optimised)|Growth/month|
|---|---|---|
|Bitcoin Core|~600 GB|~5 GB|
|Fulcrum|~100 GB|~1 GB|
|Geth (path-scheme)|~950 GB|~25 GB|
|Lighthouse (pruned)|~70 GB|~1 GB|
|Docker logs (rotated)|<1 GB|capped|
|Total|~1.72 TB|~32 GB/month|

Compared with the unoptimised baseline (~1.9 TB, ~38 GB/month), these settings save roughly 180 GB upfront and about 6 GB/month ongoing — without removing functionality or limiting wallet queries.

### Reducing storage further

|Option|Additional savings|Trade-off|
|---|---|---|
|Remove `txindex=1` from Bitcoin|~150 GB|Wallet tx-history lookups break|
|Replace Fulcrum with EPS|~80 GB|Much slower, only indexes your wallets|
|Drop the Ethereum stack|~1.0 TB|No ETH node|
|Drop the Bitcoin stack|~700 GB|No BTC node|
|Pruned Bitcoin node|~500 GB|Wallet queries break entirely|

Minimum viable storage is about 1.5 TB if you want both chains fully functional. The storage cost is the price of not trusting a third party.

## Storage optimization

_Non-destructive settings that preserve all wallet functionality while keeping disk use flat._

### Geth path-based state scheme

_The single most impactful setting; must be chosen before the first sync._

The path-based state scheme (`--state.scheme=path`, Geth 1.13+) saves 100–200 GB on the Geth database versus the legacy hash scheme. It stores the state trie at fixed, reusable paths instead of content-addressed hashes, so stale intermediate nodes do not accumulate.

> [!warning] This flag must be set before the first sync. It cannot be changed on existing data. The [[#Config: docker-compose.yml|compose file]] enables it by default; to migrate an existing hash-scheme node, the only safe path is to wipe `data/geth` and re-sync.

### Lighthouse payload and blob pruning

_Enabled by default in v8.x — no flags needed._

Payload pruning removes execution-layer payload bodies from the beacon database once finality is reached; Geth already holds the authoritative copy, so a duplicate in Lighthouse would waste 30–50 GB and grow indefinitely. Blob pruning removes old blob data after the network retention window (4096 epochs, about 18 days), keeping the database at a stable size. Since the Fusaka fork, a full node stores only a subset of blob columns (PeerDAS custody) rather than every blob sidecar, keeping this data smaller than it was before.

In Lighthouse v8.x both behaviours default to `true`, so the compose file does not set them. If you ever need to disable pruning (for example, running a relay that serves payloads to other peers), pass `--prune-payloads=false` — note the explicit `=true`/`=false` value, because both flags take a `<BOOLEAN>` argument and a bare flag fails to parse.

### Geth offline state pruning (legacy hash scheme only)

_Not used here; documented only to warn against running it on a path-scheme node._

> [!caution] You do not need this unless you are running the legacy hash scheme. The [[#Config: docker-compose.yml|compose file]] uses `--state.scheme=path`, which prunes state online and automatically. There is no separate prune step.

`geth snapshot prune-state` is the legacy offline pruner. The Geth source documents it as supported only in hash mode (`--state.scheme=hash`). Running it against a path-scheme database refuses to execute in newer releases and fails confusingly midway in some older ones — either way you lose hours of node downtime achieving nothing. Do not run it on a path-scheme node.

The path scheme was introduced in Geth 1.13 specifically to make this manual step obsolete: stale trie nodes are pruned online as new ones are written, so the disk footprint stays roughly flat. For a node that has run with `--state.scheme=path` from its first sync, no periodic disk-recovery action is needed. If you are migrating from a hash-mode setup, wipe `data/geth` and re-sync (see [[#Troubleshooting|troubleshooting]]).

### Fulcrum database compaction

_Reclaims 5–15 GB on a mature install; runs automatically on restart._

Fulcrum's RocksDB accumulates deleted and updated records as it indexes new blocks. Compaction rewrites the database and reclaims 5–15 GB on a mature installation. The `--compact-dbs` flag on Fulcrum's [[#Config: docker-compose.yml|compose command]] forces this on every container start, and the [[#Maintenance: maintain.sh|maintenance script]] restarts Fulcrum weekly to trigger it. RocksDB also compacts in the background as Fulcrum runs, so this forced pass is optional — it just reclaims stale space more aggressively.

### Docker log rotation

_Caps each service's logs so they cannot silently fill the disk._

Unmanaged Docker JSON logs are unbounded and can quietly consume tens of gigabytes on a long-running node. The [[#Config: docker-compose.yml|compose file]] applies a log driver config to every service:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "5"
```

This caps each service at 250 MB of logs total (five rolling 50 MB files). Adjust `max-size` and `max-file` to taste. To use system-level log management instead, switch to `driver: "journald"` and manage rotation with `journald.conf`.

### Storage monitoring

_A quick manual check of where space is going._

The [[#Maintenance: maintain.sh|maintenance script]] logs a disk-usage snapshot after every run. For a manual check:

```bash
# Per-service data directories
du -sh data/bitcoin data/fulcrum data/geth data/lighthouse

# Docker log files (JSON driver)
du -sh /var/lib/docker/containers/*/
```

## Prerequisites and first-time setup

_Hardware, install steps, directory layout, and how to bring the stack up the first time._

### System requirements

|Requirement|Minimum|Recommended|
|---|---|---|
|OS|Ubuntu 22.04 / Debian 12|Ubuntu 24.04|
|Docker|24.x|latest|
|Docker Compose|v2.x|latest|
|RAM|16 GB|32 GB|
|Disk|2 TB SSD|3 TB NVMe|
|CPU|4 cores|8 cores|
|Network|25 Mbps|100 Mbps|

### Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### Directory layout

```
.
├── docker-compose.yml         ← Config: docker-compose.yml
├── .env                       ← Config: .env
├── config/
│   └── fulcrum.conf           ← Config: fulcrum.conf
├── data/
│   └── bitcoin/
│       └── bitcoin.conf       ← Config: bitcoin.conf (create before first start)
├── scripts/
│   └── maintain.sh            ← Maintenance: maintain.sh
└── monitors/
    ├── btc/
    │   ├── monitor_btc.py     ← Monitor: monitor_btc.py
    │   ├── requirements.txt
    │   └── Dockerfile
    └── eth/
        ├── monitor_eth.js     ← Monitor: monitor_eth.js
        ├── package.json
        └── Dockerfile
```

The rest of `data/` (geth, lighthouse, fulcrum, jwt.hex) is created automatically on first start.

### Setup steps

```bash
# 1. Create the secrets file — paste the contents of Config: .env.example into
#    .env.example first, then copy and edit.
cp .env.example .env
nano .env           # fill in credentials and addresses

# 2. Exclude sensitive paths from version control
echo ".env"  >> .gitignore
echo "data/" >> .gitignore

# 3. Generate the JWT secret for Geth ↔ Lighthouse authentication
mkdir -p data
openssl rand -hex 32 > data/jwt.hex
chmod 600 data/jwt.hex

# 4. Create the Bitcoin data dir and its config, then generate the rpcauth line.
#    Paste the contents of Config: bitcoin.conf into the file first, then run
#    rpcauth.py with your chosen BTC_RPC_USER and paste the resulting
#    "rpcauth=..." line into bitcoin.conf. Put the password it prints into
#    BTC_RPC_PASSWORD in .env (bitcoind uses the salted hash; Fulcrum and the
#    monitor use the plaintext user/password).
mkdir -p data/bitcoin
nano data/bitcoin/bitcoin.conf
curl -sSL https://raw.githubusercontent.com/bitcoin/bitcoin/master/share/rpcauth/rpcauth.py \
  | python3 - "$(grep -E '^BTC_RPC_USER=' .env | cut -d= -f2)"

# 5. Create the Fulcrum config — paste the contents of Config: fulcrum.conf,
#    then set rpcuser/rpcpassword to match BTC_RPC_USER/BTC_RPC_PASSWORD in .env.
mkdir -p config
nano config/fulcrum.conf

# 6. Create the monitor sources and paste the files from the two Monitor
#    sections: monitors/btc/{monitor_btc.py, requirements.txt, Dockerfile}
#    and monitors/eth/{monitor_eth.js, package.json, Dockerfile}.
mkdir -p monitors/btc monitors/eth
# Generate the eth-monitor lockfile once (the Dockerfile uses `npm ci`).
# Pick whichever you have:
#   a) Node already installed on the host:
( cd monitors/eth && npm install )
#   b) Or run npm in a throwaway container (no host Node required). The -u flag
#      uses your host UID/GID so the generated file is owned by you, not root:
# docker run --rm -u "$(id -u):$(id -g)" -v "$(pwd)/monitors/eth:/work" \
#   -w /work node:20-slim npm install
# Either way, monitors/eth/package-lock.json must exist before `docker compose build`.

# 7. Create the scripts dir and paste maintain.sh
mkdir -p scripts
chmod +x scripts/maintain.sh

# 8. Paste docker-compose.yml into the project root, build the monitor images
#    (one-time; 1–2 min), and start the stack.
docker compose build       # builds btc-monitor + eth-monitor from their Dockerfiles
docker compose up -d
docker compose logs -f
```

After editing a monitor script later, rebuild its image to apply the change: `docker compose build btc-monitor && docker compose up -d btc-monitor` (or `eth-monitor`).

### Initial sync times

_Modern hardware; each layer starts only once its dependency is ready._

|Service|Time|
|---|---|
|Bitcoin Core|1–3 days|
|Fulcrum|12–24 hours (starts after Bitcoin syncs)|
|Geth|4–8 hours (snap sync, path-scheme)|
|Lighthouse|2–6 hours (checkpoint sync)|

### Checking sync progress

```bash
# Bitcoin
docker exec bitcoind bitcoin-cli \
  -rpcuser=$BTC_RPC_USER -rpcpassword=$BTC_RPC_PASSWORD \
  getblockchaininfo | grep -E '"blocks"|"verificationprogress"'

# Geth (returns false when fully synced)
docker exec geth geth attach \
  --exec "eth.syncing || 'fully synced'" \
  /root/.ethereum/geth.ipc

# Lighthouse
docker exec lighthouse \
  curl -s http://localhost:5052/eth/v1/node/syncing
```

## Config: .env.example

_The committed template. Copy to `.env` and fill in real values._

Commit this file to version control. Copy it to `.env` and fill in real values. The `.env` file itself must never be committed — it is excluded via `.gitignore` in the setup steps.

```env
# ── Project name ─────────────────────────────────────────────
COMPOSE_PROJECT_NAME=nodestack

# ── Bitcoin RPC credentials ─────────────────────────────────
# BTC_RPC_USER must match the user in the rpcauth line in bitcoin.conf.
# BTC_RPC_PASSWORD must be the plaintext password used to generate that line.
BTC_RPC_USER=choose_a_username
BTC_RPC_PASSWORD=use_a_long_random_string_here_min_32_chars

# ── Watched addresses ───────────────────────────────────────
BTC_WATCH_ADDRESSES=bc1qaddr1,bc1qaddr2
ETH_WATCH_ADDRESSES=0xYourAddress1,0xYourAddress2

# ── Ethereum fee recipient ───────────────────────────────────
# Set to your own wallet address to capture block proposal fees.
ETH_FEE_RECIPIENT=0x0000000000000000000000000000000000000000

# ── Alert webhook (optional) ────────────────────────────────
# See "Webhook to your backend" — the monitors are on internet-isolated
# networks, so an external URL here will not be reachable as-is.
ALERT_WEBHOOK_URL=
WEBHOOK_SECRET=
```

## Config: .env

_The live secrets file — never committed._

```env
# ── Project name ─────────────────────────────────────────────
# Sets the Docker Compose project prefix for container names and volumes.
COMPOSE_PROJECT_NAME=nodestack

# ── Bitcoin RPC credentials ─────────────────────────────────
# Use a password manager to generate a long random password.
# BTC_RPC_USER matches the user in bitcoin.conf's rpcauth line; BTC_RPC_PASSWORD
# is the plaintext password used to generate that line. Fulcrum and the monitor
# authenticate with the plaintext pair; bitcoind stores only the salted hash.
BTC_RPC_USER=choose_a_username
BTC_RPC_PASSWORD=use_a_long_random_string_here_min_32_chars

# ── Watched addresses ───────────────────────────────────────
# Comma-separated lists of RECEIVE addresses — not private keys.
# The monitor scripts watch all of them simultaneously.
# For a payment system, add one address per invoice/customer.
BTC_WATCH_ADDRESSES=bc1qaddr1,bc1qaddr2
ETH_WATCH_ADDRESSES=0xYourAddress1,0xYourAddress2

# ── Ethereum fee recipient ───────────────────────────────────
# Address that receives priority fees when your node proposes a block. This
# only matters if you attach a validator client — this stack runs none, so
# it is inert here; Lighthouse just wants a value. Defaults to burn if unset.
ETH_FEE_RECIPIENT=0x0000000000000000000000000000000000000000

# ── Alert webhook (optional) ────────────────────────────────
# Monitor scripts POST a JSON body here on any payment event.
# Compatible with ntfy.sh, Gotify, Discord, Slack, or a custom endpoint —
# but only if that endpoint is reachable from the monitors' networks.
ALERT_WEBHOOK_URL=

# ── Webhook auth secret (optional) ──────────────────────────
# Sent as Authorization: Bearer <secret> so your backend can reject spoofs.
WEBHOOK_SECRET=
```

## Config: docker-compose.yml

_The full stack definition. Images are pinned; update deliberately._

```yaml
# ============================================================
#  Hardened Bitcoin + Ethereum node stack
#
#  Usage:
#    1. Copy .env.example to .env and fill in your values
#    2. Generate JWT secret:  openssl rand -hex 32 > data/jwt.hex
#    3. Create data/bitcoin/bitcoin.conf (see "Config: bitcoin.conf") and
#       generate its rpcauth line
#    4. Paste the monitor sources, or comment out btc-monitor / eth-monitor
#       until they exist
#    5. docker compose build && docker compose up -d
#
#  Image versions: pin these to a specific tag in production instead of
#  relying on 'latest'. Check each project's releases page before bumping.
# ============================================================

networks:
  btc-external:
    internal: false   # Bitcoin p2p — needs internet
  btc-internal:
    internal: true    # Bitcoin RPC/ZMQ — no internet
  eth-external:
    internal: false   # Ethereum p2p — needs internet
  eth-internal:
    internal: true    # Ethereum RPC — no internet
  monitoring:
    internal: true    # Monitor scripts — isolated from node internals

# ── Shared log rotation applied to all services via YAML anchors ──
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "5"

services:

  # ----------------------------------------------------------
  #  Bitcoin Core full node
  #
  #  This image (bitcoin/bitcoin) forwards CLI args to bitcoind but does NOT
  #  read BITCOIN_RPCUSER / BITCOIN_EXTRA_ARGS env vars. All node configuration
  #  therefore lives in bitcoin.conf, mounted inside the data dir below and read
  #  automatically by bitcoind on startup. The two env vars here are used ONLY
  #  by the healthcheck's bitcoin-cli call.
  # ----------------------------------------------------------
  bitcoind:
    image: bitcoin/bitcoin:29.3   # maintained successor to ruimarinho/bitcoin-core (which stopped at v24). 28.x is EOL as of Core 31.0; check https://hub.docker.com/r/bitcoin/bitcoin/tags
    container_name: bitcoind
    restart: unless-stopped
    init: true           # PID 1 reaps zombies and forwards signals
    networks:
      - btc-external
      - btc-internal
    volumes:
      - ./data/bitcoin:/home/bitcoin/.bitcoin   # datadir; bitcoind reads bitcoin.conf from here
    environment:
      # Consumed only by the healthcheck below, not by bitcoind itself.
      BTC_RPC_USER: ${BTC_RPC_USER}
      BTC_RPC_PASSWORD: ${BTC_RPC_PASSWORD}
    ports:
      - "8333:8333"     # BTC p2p — required for network participation
      # 8332 (RPC), 28332/28333 (ZMQ) — internal Docker only, NOT published
    security_opt:
      - no-new-privileges:true
    logging: *default-logging
    healthcheck:
      # bitcoin-cli authenticates against the rpcauth-configured server with the
      # plaintext user/password. Succeeds once RPC is up (before full sync).
      test:
        - "CMD-SHELL"
        - "bitcoin-cli -rpcuser=$$BTC_RPC_USER -rpcpassword=$$BTC_RPC_PASSWORD getblockchaininfo > /dev/null"
      interval: 30s
      timeout: 10s
      retries: 15
      start_period: 60s

  # ----------------------------------------------------------
  #  Fulcrum — Electrum index server
  #  --compact-dbs (in the command below) forces a RocksDB compaction on each restart.
  # ----------------------------------------------------------
  fulcrum:
    image: cculianu/fulcrum:v2.1.0        # pinned — check https://github.com/cculianu/Fulcrum/releases (2.x DB is crash-safe; an existing 1.x datadir needs a one-time --db-upgrade)
    container_name: fulcrum
    restart: unless-stopped
    init: true
    depends_on:
      bitcoind:
        condition: service_healthy
    networks:
      - btc-internal
    volumes:
      - ./data/fulcrum:/data
      - ./config/fulcrum.conf:/etc/fulcrum.conf:ro
    ports:
      - "127.0.0.1:50001:50001"   # Electrum TCP — localhost only
      - "127.0.0.1:50002:50002"   # Electrum SSL — localhost only
    command: ["/usr/bin/Fulcrum", "/etc/fulcrum.conf", "--compact-dbs"]
    security_opt:
      - no-new-privileges:true
    logging: *default-logging
    healthcheck:
      # cculianu/fulcrum ships python3 (for FulcrumAdmin) but no nc — TCP-check the port with it.
      test: ["CMD", "python3", "-c", "import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(0 if s.connect_ex(('127.0.0.1',50001))==0 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 120s

  # ----------------------------------------------------------
  #  BTC address monitor
  #  Comment out until monitors/btc/monitor_btc.py exists.
  # ----------------------------------------------------------
  btc-monitor:
    build: ./monitors/btc           # Dockerfile bakes the script in; runs as non-root UID 1000
    container_name: btc-monitor
    restart: unless-stopped
    init: true
    depends_on:
      bitcoind:
        condition: service_healthy
    networks:
      - btc-internal
      - monitoring
    # No volumes / working_dir / command — the Dockerfile sets WORKDIR + CMD.
    # To update after editing: docker compose build btc-monitor && docker compose up -d btc-monitor
    environment:
      RPC_USER: ${BTC_RPC_USER}
      RPC_PASSWORD: ${BTC_RPC_PASSWORD}
      RPC_HOST: bitcoind
      RPC_PORT: "8332"
      ZMQ_HOST: bitcoind
      ZMQ_PORT: "28333"             # rawtx publisher
      ZMQ_BLOCK_PORT: "28332"       # rawblock publisher (used by the confirmation extension)
      BTC_WATCH_ADDRESSES: ${BTC_WATCH_ADDRESSES}
      ALERT_WEBHOOK_URL: ${ALERT_WEBHOOK_URL:-}
      WEBHOOK_SECRET: ${WEBHOOK_SECRET:-}
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL                         # monitor needs no kernel capabilities
    read_only: true                 # only the /tmp tmpfs below is writable
    tmpfs:
      - /tmp                        # pip cache, log buffering, liveness file — not persisted
    logging: *default-logging
    # Liveness check: the script touches /tmp/alive on every loop iteration
    # (at least every 60 s). This probe fails if that file is missing or older
    # than 120 s — i.e. if the monitor has hung or died. Uses python (present in
    # the image) so nothing extra is installed, and the probe shares no literal
    # with the script, so it cannot self-match the way a /proc cmdline grep does.
    healthcheck:
      test:
        - "CMD"
        - "python"
        - "-c"
        - "import os,time,sys; sys.exit(0 if os.path.exists('/tmp/alive') and time.time()-os.path.getmtime('/tmp/alive') < 120 else 1)"
      interval: 60s
      timeout: 5s
      retries: 3
      start_period: 60s

  # ----------------------------------------------------------
  #  Geth — Ethereum execution layer
  #
  #  --state.scheme=path  Path-based state trie (Geth 1.13+). Saves 100–200 GB
  #                        vs legacy hash scheme. Must be set before first sync.
  #  --cache.gc=25         Allocates 25% of --cache to GC.
  # ----------------------------------------------------------
  geth:
    image: ethereum/client-go:v1.17.4     # pinned; >= v1.16.7 required for the Fusaka fork (mainnet 2025-12-03) — check https://github.com/ethereum/go-ethereum/releases
    container_name: geth
    restart: unless-stopped
    init: true
    networks:
      - eth-external
      - eth-internal
    volumes:
      - ./data/geth:/root/.ethereum
      - ./data/jwt.hex:/jwt.hex:ro
    command:
      - "--http"
      - "--http.addr=0.0.0.0"
      - "--http.api=eth,net,web3"       # 'personal' intentionally omitted — unsafe
      - "--http.vhosts=geth,localhost,127.0.0.1"  # restrict to known hosts (incl. 127.0.0.1 so MetaMask can connect)
      - "--http.corsdomain=localhost"
      - "--authrpc.addr=0.0.0.0"
      - "--authrpc.vhosts=geth"         # must equal the host Lighthouse dials (geth's service name), not "lighthouse", or geth rejects the engine API
      - "--authrpc.jwtsecret=/jwt.hex"
      - "--authrpc.port=8551"
      - "--ws"
      - "--ws.addr=0.0.0.0"
      - "--ws.api=eth,net,web3"
      - "--ws.origins=localhost"
      - "--maxpeers=30"
      - "--cache=1024"
      - "--cache.gc=25"
      - "--state.scheme=path"           # path-scheme: 100–200 GB savings (new installs)
    ports:
      - "30303:30303"
      - "30303:30303/udp"
      - "127.0.0.1:8545:8545"           # HTTP JSON-RPC — localhost only (MetaMask/Frame)
      # 8546 (WS) / 8551 (authrpc) — internal Docker only, NOT published
    security_opt:
      - no-new-privileges:true
    logging: *default-logging
    healthcheck:
      test:
        - "CMD-SHELL"
        - "geth attach --exec 'eth.blockNumber' /root/.ethereum/geth.ipc || exit 1"
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 120s

  # ----------------------------------------------------------
  #  Lighthouse — Ethereum consensus layer
  #
  #  In v8.x, payload and blob pruning are enabled by default — no flags needed.
  #  Both take a <BOOLEAN> argument, so passing them as bare flags fails CLI parsing.
  # ----------------------------------------------------------
  lighthouse:
    image: sigp/lighthouse:v8.2.0         # pinned; >= v8.0.0 required for the Fusaka fork (mainnet 2025-12-03) — check https://github.com/sigp/lighthouse/releases
    container_name: lighthouse
    restart: unless-stopped
    init: true
    depends_on:
      geth:
        condition: service_healthy
    networks:
      - eth-external
      - eth-internal
    volumes:
      - ./data/lighthouse:/root/.lighthouse
      - ./data/jwt.hex:/jwt.hex:ro
    command:
      - "lighthouse"
      - "bn"
      - "--network=mainnet"
      - "--execution-endpoint=http://geth:8551"
      - "--execution-jwt=/jwt.hex"
      - "--http"
      - "--http-address=0.0.0.0"
      - "--http-port=5052"
      - "--disable-deposit-contract-sync"
      - "--checkpoint-sync-url=https://mainnet.checkpoint.sigp.io"
      - "--suggested-fee-recipient=${ETH_FEE_RECIPIENT:-0x0000000000000000000000000000000000000000}"
      # --prune-payloads and --prune-blobs default to true in v8.x — do not pass as bare flags.
    ports:
      - "9000:9000"
      - "9000:9000/udp"
      # 5052 (Beacon API) — internal only; access via: docker exec lighthouse curl ...
    security_opt:
      - no-new-privileges:true
    logging: *default-logging
    healthcheck:
      test:
        # sigp/lighthouse is ubuntu-based with no curl/wget/nc; use bash's
        # /dev/tcp to confirm the Beacon API port is listening (needs bash, not sh).
        - "CMD"
        - "bash"
        - "-c"
        - "exec 3<>/dev/tcp/localhost/5052"
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 120s

  # ----------------------------------------------------------
  #  ETH address monitor
  #  Comment out until monitors/eth/monitor_eth.js exists.
  # ----------------------------------------------------------
  eth-monitor:
    build: ./monitors/eth           # Dockerfile bakes the script in; runs as non-root node user (UID 1000)
    container_name: eth-monitor
    restart: unless-stopped
    init: true
    depends_on:
      geth:
        condition: service_healthy
    networks:
      - eth-internal
      - monitoring
    # No volumes / working_dir / command — the Dockerfile sets WORKDIR + CMD.
    # To update after editing: docker compose build eth-monitor && docker compose up -d eth-monitor
    environment:
      ETH_RPC_WS: "ws://geth:8546"
      ETH_WATCH_ADDRESSES: ${ETH_WATCH_ADDRESSES}
      ALERT_WEBHOOK_URL: ${ALERT_WEBHOOK_URL:-}
      WEBHOOK_SECRET: ${WEBHOOK_SECRET:-}
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    logging: *default-logging
    # Liveness check: the script writes /tmp/alive every 30 s from a top-level
    # timer (independent of connection state). Fails if the file is missing or
    # older than 120 s. Uses node, already present in the image.
    healthcheck:
      test:
        - "CMD"
        - "node"
        - "-e"
        - "try{const fs=require('fs');process.exit(Date.now()-fs.statSync('/tmp/alive').mtimeMs<120000?0:1)}catch(e){process.exit(1)}"
      interval: 60s
      timeout: 5s
      retries: 3
      start_period: 30s
```

## Config: bitcoin.conf

_All bitcoind settings live here, because the image ignores `BITCOIN_*` environment variables._

The `bitcoin/bitcoin` image forwards command-line arguments to `bitcoind` but does not translate `BITCOIN_RPCUSER`, `BITCOIN_RPCPASSWORD`, or a `BITCOIN_EXTRA_ARGS` variable — it only reads `BITCOIN_DATA`. Node configuration therefore goes in `bitcoin.conf`, placed inside the data directory (`data/bitcoin/bitcoin.conf`, which maps to `/home/bitcoin/.bitcoin/bitcoin.conf` in the container) and read automatically on startup. This also keeps the RPC password out of the process list, since only the salted `rpcauth` hash appears in the config.

> [!tip] Generate the `rpcauth` line once, from your chosen `BTC_RPC_USER`, and paste it below. Put the plaintext password it prints into `BTC_RPC_PASSWORD` in [[#Config: .env|.env]]; that same pair goes in [[#Config: fulcrum.conf|fulcrum.conf]]. bitcoind verifies the plaintext against the stored hash, so the three stay in sync through the one password.

```ini
# ── bitcoin.conf ────────────────────────────────────────────
# Placed in the data dir: data/bitcoin/bitcoin.conf → /home/bitcoin/.bitcoin/bitcoin.conf
# Read automatically by bitcoind on startup.

server=1                 # accept JSON-RPC connections
txindex=1                # full tx index — required by Fulcrum and wallet history
listen=1                 # accept inbound p2p connections
printtoconsole=1         # log to stdout so `docker compose logs` works

# ── RPC authentication ──────────────────────────────────────
# Generate the rpcauth line (salted hash) with your chosen BTC_RPC_USER:
#   curl -sSL https://raw.githubusercontent.com/bitcoin/bitcoin/master/share/rpcauth/rpcauth.py \
#     | python3 - <BTC_RPC_USER>
# Paste its "rpcauth=..." output below, and put the printed password into
# BTC_RPC_PASSWORD in .env. bitcoind stores only the hash; Fulcrum and the
# monitor authenticate with the plaintext user/password.
rpcauth=REPLACE_WITH_GENERATED_RPCAUTH_LINE

# ── RPC binding ─────────────────────────────────────────────
# Bind inside the container; the btc-internal network is not published to the
# host. rpcallowip must cover the Docker subnet so Fulcrum and the monitor can
# connect (loopback is always allowed, which is all the healthcheck needs).
rpcbind=0.0.0.0
rpcallowip=172.16.0.0/12
rpcallowip=192.168.0.0/16
rpcallowip=10.0.0.0/8

# ── ZMQ publishers ──────────────────────────────────────────
# rawtx (28333) drives the monitor's mempool alerts; rawblock (28332) drives
# the confirmation-tracking extension. Both internal Docker only.
zmqpubrawblock=tcp://0.0.0.0:28332
zmqpubrawtx=tcp://0.0.0.0:28333

# ── Resources ───────────────────────────────────────────────
maxconnections=40
dbcache=512              # MB — raise to 2048+ on a machine with >16 GB RAM
par=0                    # script-verification threads: 0 = auto (all cores)
```

## Config: fulcrum.conf

_The Electrum index server's configuration. Credentials must match [[#Config: .env|.env]]._

```ini
# ── Data directory ──────────────────────────────────────────
datadir = /data

# ── Bitcoin Core connection ─────────────────────────────────
# Must match BTC_RPC_USER and BTC_RPC_PASSWORD in .env exactly.
bitcoind = bitcoind:8332
rpcuser = REPLACE_WITH_BTC_RPC_USER
rpcpassword = REPLACE_WITH_BTC_RPC_PASSWORD

# ── Listeners ───────────────────────────────────────────────
# TCP — unencrypted, localhost only (bound in docker-compose.yml)
tcp = 0.0.0.0:50001

# SSL — recommended for connections from another machine on your LAN.
# Uncomment after generating a certificate (see below).
# ssl = 0.0.0.0:50002
# cert = /data/fulcrum.pem
# key  = /data/fulcrum.key

# Generate a self-signed certificate:
#   openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 \
#     -keyout ./data/fulcrum/fulcrum.key \
#     -out    ./data/fulcrum/fulcrum.pem \
#     -subj "/CN=fulcrum"

# ── Performance ─────────────────────────────────────────────
db_mem = 1024.0       # RAM for DB cache in MB — increase if available
worker_threads = 4    # CPU threads for indexing

# ── Storage ─────────────────────────────────────────────────
# Startup compaction is driven by the --compact-dbs CLI flag on the compose
# command, not by a config key — there is no `compact_on_startup` option (an
# unknown key here is silently ignored). RocksDB also auto-compacts in the
# background while Fulcrum runs, so forcing it is optional; --compact-dbs just
# reclaims stale space more aggressively on each restart (~5–15 GB on a mature
# install) at the cost of ~5–15 min added startup time. Drop the flag to skip it.

# ── Peer announcements ──────────────────────────────────────
# Prevents this server from being listed on public Electrum server lists.
peering = false
```

## Monitor: monitor_btc.py

_Watches any number of Bitcoin addresses via ZMQ, with reconnection, sequence-gap detection, and a liveness heartbeat._

The script subscribes to bitcoind's `rawtx` ZMQ topic for mempool alerts and also connects to the `rawblock` endpoint so the [[#Wait for confirmations|confirmation-tracking extension]] can subscribe without re-opening the socket. It writes `/tmp/alive` on every loop iteration so the container's liveness [[#Config: docker-compose.yml|health check]] reflects the real state of the process.

```python
"""
BTC address monitor — multi-address edition
Watches any number of Bitcoin addresses simultaneously via ZMQ.

Environment variables (injected by docker-compose.yml):
  RPC_USER, RPC_PASSWORD, RPC_HOST, RPC_PORT
  ZMQ_HOST, ZMQ_PORT         rawtx publisher (mempool alerts)
  ZMQ_BLOCK_PORT             rawblock publisher (confirmation-tracking extension)
  BTC_WATCH_ADDRESSES        comma-separated list of receive addresses
  ALERT_WEBHOOK_URL          optional POST target
  WEBHOOK_SECRET             optional Authorization: Bearer token
"""

import os
import time
import random
import logging
import threading
import requests
import zmq
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

RPC_USER     = os.environ["RPC_USER"]
RPC_PASSWORD = os.environ["RPC_PASSWORD"]
RPC_HOST     = os.environ.get("RPC_HOST", "bitcoind")
RPC_PORT     = os.environ.get("RPC_PORT", "8332")
ZMQ_HOST     = os.environ.get("ZMQ_HOST", "bitcoind")
ZMQ_PORT     = os.environ.get("ZMQ_PORT", "28333")           # rawtx publisher
ZMQ_BLOCK_PORT = os.environ.get("ZMQ_BLOCK_PORT", "28332")   # rawblock publisher
WEBHOOK_URL  = os.environ.get("ALERT_WEBHOOK_URL", "").strip()
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "").strip()

# Support both singular (legacy) and plural (multi-address) env vars
_raw = os.environ.get("BTC_WATCH_ADDRESSES") or os.environ.get("BTC_WATCH_ADDRESS", "")
WATCH_ADDRS: set[str] = {a.strip() for a in _raw.split(",") if a.strip()}

if not WATCH_ADDRS:
    raise RuntimeError("BTC_WATCH_ADDRESSES is not set or empty")

rpc_url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"

LIVENESS_FILE       = "/tmp/alive"          # touched each loop; read by the healthcheck
ZMQ_LINGER          = 0
ZMQ_RCVTIMEO_MS     = 60_000                # 60 s — also the heartbeat cadence
HEARTBEAT_INTERVAL  = 5 * 60                # log a heartbeat every 5 min of silence
BACKOFF_INITIAL_S   = 1.0                   # first reconnect delay
BACKOFF_MAX_S       = 300.0                 # cap at 5 min
WEBHOOK_MAX_ATTEMPTS = 5
WEBHOOK_RETRY_BASE_S = 1.0
WEBHOOK_RETRY_MAX_S  = 30.0


def get_rpc() -> AuthServiceProxy:
    """Create a fresh RPC connection. Call once per reconnect loop, not per message."""
    return AuthServiceProxy(rpc_url)


def touch_liveness() -> None:
    """Update the mtime of LIVENESS_FILE so the container healthcheck sees the
    process as alive. Called every loop iteration (at most every ZMQ_RCVTIMEO_MS),
    well inside the healthcheck's 120 s staleness window."""
    try:
        with open(LIVENESS_FILE, "w"):
            pass
    except OSError:
        pass


def _jittered(delay: float) -> float:
    """Half-second jitter on a backoff delay: returned in [delay*0.5, delay*1.5)."""
    return delay * (0.5 + random.random())


def _post_webhook_with_retry(payload: dict) -> None:
    """POST to WEBHOOK_URL with exponential-backoff retry.

    Retries on connection errors and HTTP 5xx; gives up on 4xx (those are
    almost always a misconfiguration that retrying won't fix). Logs the
    payload at ERROR if all attempts are exhausted so the operator can
    reconstruct missed alerts from logs.
    """
    if not WEBHOOK_URL:
        return
    headers = {"Content-Type": "application/json"}
    if WEBHOOK_SECRET:
        headers["Authorization"] = f"Bearer {WEBHOOK_SECRET}"

    delay = WEBHOOK_RETRY_BASE_S
    for attempt in range(1, WEBHOOK_MAX_ATTEMPTS + 1):
        try:
            resp = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=5)
            if resp.status_code < 400:
                return
            if 400 <= resp.status_code < 500:
                log.error("Webhook returned %d (client error, not retrying): %s",
                          resp.status_code, payload.get("txid"))
                return
            log.warning("Webhook returned %d (attempt %d/%d)",
                        resp.status_code, attempt, WEBHOOK_MAX_ATTEMPTS)
        except requests.RequestException as exc:
            log.warning("Webhook delivery failed (attempt %d/%d): %s",
                        attempt, WEBHOOK_MAX_ATTEMPTS, exc)

        if attempt < WEBHOOK_MAX_ATTEMPTS:
            time.sleep(_jittered(delay))
            delay = min(delay * 2, WEBHOOK_RETRY_MAX_S)

    log.error("Webhook GAVE UP after %d attempts; alert NOT delivered: %s",
              WEBHOOK_MAX_ATTEMPTS, payload)


def send_alert(tx_id: str, amount_btc, direction: str, address: str) -> None:
    # `amount_btc` comes from python-bitcoinrpc as a `Decimal` (preserves the full
    # 8-satoshi precision of Bitcoin amounts). Format as a string both for the
    # log line and the webhook payload — `json.dumps` (used by `requests`)
    # cannot serialize `Decimal`, so passing it directly would raise TypeError
    # the first time a transaction arrived with the webhook configured.
    amount_str = f"{amount_btc:.8f}"

    message = (
        f"[ALERT] BTC {direction} | "
        f"txid={tx_id} | "
        f"amount={amount_str} BTC | "
        f"address={address}"
    )
    log.info(message)

    if not WEBHOOK_URL:
        return

    payload = {
        "chain":    "BTC",
        "event":    direction,
        "txid":     tx_id,
        "amount":   amount_str,     # string, not Decimal — JSON-safe
        "address":  address,
        "ts":       int(time.time()),
    }
    # Fire-and-forget: webhook retry/backoff (up to ~56 s worst case) runs in
    # a daemon thread so it cannot block the ZMQ receive loop. A blocked
    # receive loop would overflow the ZMQ HWM (default 1000 messages) and
    # cause the sequence-gap detector to fire spuriously.
    # `requests` is thread-safe for one-off `requests.post(...)` calls.
    threading.Thread(
        target=_post_webhook_with_retry,
        args=(payload,),
        name=f"webhook-{tx_id[:8]}",
        daemon=True,                # don't prevent process exit
    ).start()


def inspect_decoded_tx(decoded: dict) -> None:
    """Check a fully-decoded transaction for watched outputs.

    Called with the result of decoderawtransaction, so no extra RPC call is needed.
    """
    tx_id = decoded["txid"]
    for vout in decoded.get("vout", []):
        script    = vout.get("scriptPubKey", {})
        addresses = set(script.get("addresses", []))
        address   = script.get("address", "")
        if address:
            addresses.add(address)
        matched = WATCH_ADDRS & addresses
        for addr in matched:
            send_alert(tx_id, vout["value"], "RECEIVED", addr)


def build_zmq_socket(ctx: zmq.Context) -> zmq.Socket:
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt(zmq.LINGER, ZMQ_LINGER)
    sock.setsockopt(zmq.RCVTIMEO, ZMQ_RCVTIMEO_MS)
    # rawtx and rawblock are published on separate endpoints, so a SUB socket
    # must connect to BOTH to receive both topics. The base script subscribes
    # only to rawtx; the confirmation extension adds a rawblock subscription and
    # the connection is already in place.
    sock.connect(f"tcp://{ZMQ_HOST}:{ZMQ_PORT}")         # rawtx publisher
    sock.connect(f"tcp://{ZMQ_HOST}:{ZMQ_BLOCK_PORT}")   # rawblock publisher
    sock.setsockopt(zmq.SUBSCRIBE, b"rawtx")
    return sock


def main() -> None:
    log.info("Watching %d address(es): %s", len(WATCH_ADDRS), ", ".join(sorted(WATCH_ADDRS)))
    log.info("Connecting ZMQ   : tcp://%s:%s (rawtx), tcp://%s:%s (rawblock)",
             ZMQ_HOST, ZMQ_PORT, ZMQ_HOST, ZMQ_BLOCK_PORT)
    log.info("Webhook alerts   : %s", WEBHOOK_URL or "disabled")

    ctx = zmq.Context()
    backoff = BACKOFF_INITIAL_S

    while True:
        sock = build_zmq_socket(ctx)
        log.info("ZMQ socket connected; listening for transactions...")
        rpc = get_rpc()                     # one RPC connection per outer reconnect cycle
        last_heartbeat_at = time.monotonic()
        # Track ZMQ message sequence numbers only WITHIN a connected session.
        # Resetting on each outer reconnect avoids reporting a spurious giant
        # gap when bitcoind restarts (its per-topic counter resets to 0) or
        # when we genuinely missed messages across the disconnect (in which
        # case the gap is expected, not a HWM symptom worth warning about).
        last_seq: dict[bytes, int] = {}
        inner_loop_ok = True

        def maybe_heartbeat() -> None:
            nonlocal last_heartbeat_at
            if time.monotonic() - last_heartbeat_at >= HEARTBEAT_INTERVAL:
                log.info("Heartbeat: alive (watching %d address(es))", len(WATCH_ADDRS))
                last_heartbeat_at = time.monotonic()

        try:
            while inner_loop_ok:
                try:
                    topic, body, seq_bytes = sock.recv_multipart()

                    # ZMQ sequence-gap detection. bitcoind tags every published
                    # message with a 4-byte little-endian counter, per topic.
                    # A gap means we missed at least one message — possible
                    # under high load (HWM hit) or a transient socket glitch.
                    seq = int.from_bytes(seq_bytes, byteorder="little")
                    prev = last_seq.get(topic)
                    if prev is not None:
                        # Counter wraps at 2^32; mask the diff to detect the
                        # common case (and avoid a false alarm on wrap).
                        diff = (seq - prev) & 0xFFFFFFFF
                        if diff > 1:
                            # Sanity check: anything above ~1M looks more like a
                            # counter reset (bitcoind restart) than real loss.
                            if diff > 1_000_000:
                                log.warning(
                                    "ZMQ sequence anomaly on %s: prev=%d, got=%d "
                                    "(likely bitcoind restart, not real loss)",
                                    topic.decode(errors="replace"), prev, seq,
                                )
                            else:
                                log.warning(
                                    "ZMQ sequence gap on %s: expected %d, got %d "
                                    "(missed ~%d)",
                                    topic.decode(errors="replace"), prev + 1, seq, diff - 1,
                                )
                    last_seq[topic] = seq

                    # Only rawtx is subscribed in the base script; ignore any
                    # other topic that a future subscription might deliver.
                    if topic == b"rawtx":
                        # ZMQ rawtx already provides the full raw transaction bytes.
                        # decoderawtransaction is the only RPC call needed.
                        decoded = rpc.decoderawtransaction(body.hex())
                        inspect_decoded_tx(decoded)
                    backoff = BACKOFF_INITIAL_S       # reset on first message
                except zmq.error.Again:
                    # Recv timeout: no traffic for ZMQ_RCVTIMEO_MS. Fine.
                    pass
                except zmq.ZMQError as exc:
                    log.error("ZMQ error: %s", exc)
                    inner_loop_ok = False
                    continue
                except JSONRPCException as exc:
                    log.warning("RPC error decoding transaction: %s", exc)
                    try:
                        rpc = get_rpc()
                    except Exception:  # noqa: BLE001
                        pass
                except Exception as exc:  # noqa: BLE001
                    # python-bitcoinrpc keeps an underlying HTTP connection
                    # open across calls. After long idle periods or a brief
                    # bitcoind restart, that socket can be silently closed,
                    # and the next call raises BrokenPipeError / ConnectionError
                    # / http.client.HTTPException — none of which are
                    # JSONRPCException. Without refreshing the connection
                    # here we'd log a warning and then keep failing on every
                    # subsequent transaction with the same dead socket,
                    # missing alerts indefinitely.
                    log.warning("Unexpected error processing transaction: %s", exc)
                    try:
                        rpc = get_rpc()
                    except Exception:  # noqa: BLE001
                        pass

                # Liveness + heartbeat run on every iteration, whether the recv
                # produced a message or timed out. On mainnet, mempool tx flow
                # is near-constant — Again rarely fires — so anything tied to
                # Again-only would never fire. Both are wall-time based.
                touch_liveness()
                maybe_heartbeat()
        finally:
            sock.close()

        wait = _jittered(backoff)
        log.warning("Reconnecting in %.1f s...", wait)
        touch_liveness()                    # keep liveness fresh across the backoff sleep
        time.sleep(wait)
        backoff = min(backoff * 2, BACKOFF_MAX_S)


if __name__ == "__main__":
    main()
```

Save `monitors/btc/requirements.txt` alongside it:

```
python-bitcoinrpc==1.0
pyzmq>=25.0
requests>=2.31.0
```

Save `monitors/btc/Dockerfile` — this builds the monitor image with deps baked in and the runtime UID dropped from root to 1000:

```dockerfile
# monitors/btc/Dockerfile
FROM python:3.11-slim

# Python in Docker hygiene:
# - PYTHONUNBUFFERED makes stdout/stderr unbuffered so `docker logs` shows
#   output in real time (Python block-buffers when stdout is a pipe).
# - PYTHONDONTWRITEBYTECODE disables .pyc generation. The compose runs the
#   container with read_only: true, so .pyc writes would fail silently;
#   suppressing them keeps the runtime clean.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create a non-root user for the runtime. Even though /app is read-only,
# running as root inside a container with network access is a needless risk —
# any RCE in the monitor (e.g. via a malicious webhook target redirecting back)
# would inherit UID 0. UID 1000 has no host mapping in this setup.
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin monitor

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY monitor_btc.py .

USER monitor
CMD ["python", "monitor_btc.py"]
```

The [[#Config: docker-compose.yml|compose service]] references this Dockerfile via `build:`, so dependencies are baked into the image once and the container starts in under a second instead of re-downloading wheels on every restart.

## Monitor: monitor_eth.js

_Watches Ethereum addresses for native ETH and ERC-20 transfers over a WebSocket subscription, with reconnection and a liveness heartbeat. Uses the web3.js v4 API._

The script scans each new block for native ETH transfers and subscribes to ERC-20 `Transfer` logs with two direction-bound filters. It writes `/tmp/alive` every 30 seconds from a top-level timer so the container's liveness [[#Config: docker-compose.yml|health check]] reflects process liveness independently of connection state.

```javascript
/**
 * ETH address monitor — multi-address + ERC-20 edition
 *
 * Watches any number of Ethereum addresses simultaneously for:
 *   - Native ETH transfers (inbound and outbound)
 *   - ERC-20 token transfers (inbound and outbound) — USDC, USDT, DAI, WBTC,
 *     WETH, and any other token that emits a standard Transfer event
 *
 * Environment variables (injected by docker-compose.yml):
 *   ETH_RPC_WS           — ws://geth:8546  (WebSocket only; HTTP is unused)
 *   ETH_WATCH_ADDRESSES  — comma-separated 0x addresses
 *   ALERT_WEBHOOK_URL    — optional POST target
 *   WEBHOOK_SECRET       — optional Authorization: Bearer token
 *
 * Uses web3.js v4 API.
 */

const { Web3 } = require("web3");
const https    = require("https");
const http     = require("http");
const fs       = require("fs");

// ── Config ───────────────────────────────────────────────────────────────────
const WS_URL = process.env.ETH_RPC_WS || "ws://geth:8546";
const WEBHOOK = (process.env.ALERT_WEBHOOK_URL || "").trim();
const WEBHOOK_SECRET = (process.env.WEBHOOK_SECRET || "").trim();
const LIVENESS_FILE = "/tmp/alive";        // refreshed by a timer; read by the healthcheck

// Support both singular (legacy) and plural env vars
const rawAddresses = process.env.ETH_WATCH_ADDRESSES || process.env.ETH_WATCH_ADDRESS || "";
const WATCHED = new Set(
  rawAddresses.split(",").map(a => a.trim().toLowerCase()).filter(Boolean)
);

if (WATCHED.size === 0) {
  console.error("[ERROR] ETH_WATCH_ADDRESSES is not set or empty");
  process.exit(1);
}

// ── ERC-20 constants ─────────────────────────────────────────────────────────
// keccak256("Transfer(address,address,uint256)")
const TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";

// Well-known mainnet token registry { contractAddress -> { symbol, decimals } }
// Add any token you want to track by its contract address (lowercase).
const KNOWN_TOKENS = {
  "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": { symbol: "USDC",  decimals: 6  },
  "0xdac17f958d2ee523a2206206994597c13d831ec7": { symbol: "USDT",  decimals: 6  },
  "0x6b175474e89094c44da98b954eedeac495271d0f": { symbol: "DAI",   decimals: 18 },
  "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": { symbol: "WETH",  decimals: 18 },
  "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": { symbol: "WBTC",  decimals: 8  },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Pad an Ethereum address to a 32-byte topic (left-zero-padded). */
function padAddress(addr) {
  return "0x" + addr.replace(/^0x/, "").padStart(64, "0");
}

/** Decode a 32-byte topic back to a lowercase 20-byte address (not EIP-55 checksummed). */
function unpadAddress(topic) {
  return "0x" + topic.slice(-40);
}

/** Format a raw uint256 value using a token's decimal places. */
function formatTokenAmount(rawValue, decimals) {
  // Use pure BigInt arithmetic. `10 ** decimals` would be evaluated as a JS
  // Number (IEEE 754 double) before any BigInt conversion, losing precision for
  // decimals >= 24; `10n ** BigInt(decimals)` is exact for all sizes.
  const divisor = 10n ** BigInt(decimals);
  const whole   = rawValue / divisor;
  const frac    = rawValue % divisor;
  return `${whole}.${frac.toString().padStart(decimals, "0").slice(0, 6)}`;
}

// ── Alerting ─────────────────────────────────────────────────────────────────

const WEBHOOK_MAX_ATTEMPTS = 5;
const WEBHOOK_RETRY_BASE_MS = 1_000;
const WEBHOOK_RETRY_MAX_MS  = 30_000;

function _jitterMs(delayMs) {
  return delayMs * (0.5 + Math.random());
}

function _delay(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * POST `payload` to WEBHOOK with exponential-backoff retry.
 * - Retries on connection errors and HTTP 5xx
 * - Gives up on 4xx (almost always misconfiguration; retrying won't help)
 * - On exhaustion, logs the full payload at ERROR so an operator can
 *   reconstruct missed alerts from container logs.
 */
async function sendWebhook(payload) {
  if (!WEBHOOK) return;
  const body = JSON.stringify(payload);
  const url  = new URL(WEBHOOK);
  const lib  = url.protocol === "https:" ? https : http;
  const headers = {
    "Content-Type":   "application/json",
    "Content-Length": Buffer.byteLength(body),
  };
  if (WEBHOOK_SECRET) headers["Authorization"] = `Bearer ${WEBHOOK_SECRET}`;

  const attemptOnce = () => new Promise((resolve) => {
    const req = lib.request(
      { hostname: url.hostname, port: url.port,
        path: url.pathname + url.search, method: "POST", headers, timeout: 5_000 },
      (res) => {
        res.resume();   // discard body
        if (res.statusCode < 400) resolve({ ok: true });
        else if (res.statusCode < 500) resolve({ ok: false, retry: false, code: res.statusCode });
        else resolve({ ok: false, retry: true, code: res.statusCode });
      }
    );
    req.on("timeout", () => { req.destroy(new Error("timeout")); });
    req.on("error", (err) => resolve({ ok: false, retry: true, err: err.message }));
    req.write(body);
    req.end();
  });

  let delay = WEBHOOK_RETRY_BASE_MS;
  for (let attempt = 1; attempt <= WEBHOOK_MAX_ATTEMPTS; attempt++) {
    const result = await attemptOnce();
    if (result.ok) return;
    if (!result.retry) {
      console.error(`[ERROR] Webhook returned ${result.code} (client error, not retrying)`);
      return;
    }
    const reason = result.code ? `HTTP ${result.code}` : result.err;
    console.warn(`[WARN] Webhook failed (attempt ${attempt}/${WEBHOOK_MAX_ATTEMPTS}): ${reason}`);
    if (attempt < WEBHOOK_MAX_ATTEMPTS) {
      await _delay(_jitterMs(delay));
      delay = Math.min(delay * 2, WEBHOOK_RETRY_MAX_MS);
    }
  }
  console.error(`[ERROR] Webhook GAVE UP after ${WEBHOOK_MAX_ATTEMPTS} attempts; alert NOT delivered:`, payload);
}

// BigInt-safe ETH formatter — avoids Number() precision loss above ~9 000 ETH.
const WEI_PER_ETH = 10n ** 18n;
function formatEth(weiValue) {
  const w     = BigInt(weiValue);          // handle both bigint and string inputs
  const whole = w / WEI_PER_ETH;
  const frac  = w % WEI_PER_ETH;
  return `${whole}.${frac.toString().padStart(18, "0").slice(0, 6)}`;
}

function alertETH(tx, direction) {
  // Skip zero-value transactions (contract calls, approvals, etc.) that happen
  // to involve a watched address but carry no ETH.
  if (!tx.value || BigInt(tx.value) === 0n) return;

  // BigInt arithmetic, sent as a string: `Number(BigInt(tx.value)) / 1e18` would
  // lose precision for values above 2^53 wei (~9 007 ETH).
  const valueStr = formatEth(tx.value);
  const msg = `[ALERT] ETH ${direction} | hash=${tx.hash} | value=${valueStr} ETH | block=${tx.blockNumber}`;
  console.log(msg);
  sendWebhook({ chain: "ETH", asset: "ETH", event: direction,
                hash: tx.hash, value: valueStr, block: Number(tx.blockNumber),
                from: tx.from, to: tx.to, ts: Math.floor(Date.now() / 1000) });
}

function alertToken(evt, direction, token) {
  const rawValue = BigInt(evt.data);
  const formatted = formatTokenAmount(rawValue, token.decimals);
  const from = unpadAddress(evt.topics[1]);
  const to   = unpadAddress(evt.topics[2]);
  const msg  = `[ALERT] ${token.symbol} ${direction} | hash=${evt.transactionHash} | value=${formatted} ${token.symbol} | contract=${evt.address} | block=${evt.blockNumber}`;
  console.log(msg);
  sendWebhook({ chain: "ETH", asset: token.symbol, event: direction,
                hash: evt.transactionHash, value: formatted,
                block: Number(evt.blockNumber), contract: evt.address,
                from, to, ts: Math.floor(Date.now() / 1000) });
}

// ── Block scanner for native ETH ─────────────────────────────────────────────

async function processBlock(web3, blockHash) {
  try {
    const block = await web3.eth.getBlock(blockHash, true);
    if (!block?.transactions) return;
    for (const tx of block.transactions) {
      if (tx.to   && WATCHED.has(tx.to.toLowerCase()))   alertETH(tx, "RECEIVED");
      if (tx.from && WATCHED.has(tx.from.toLowerCase())) alertETH(tx, "SENT");
    }
  } catch (err) {
    console.warn("[WARN] Block processing error:", err.message);
  }
}

// ── ERC-20 log handler ───────────────────────────────────────────────────────

// Each subscription is bound to its own direction (RECEIVED for the IN
// subscription, SENT for the OUT subscription), so this handler simply formats
// and alerts. Deriving direction here instead — by checking both `to` and
// `from` against WATCHED on every delivery — would fire four alerts when both
// sides of a transfer are watched (2 deliveries x 2 matches).
function processTransferLog(evt, direction) {
  if (!evt.topics || evt.topics.length < 3) return;

  const tokenAddr = evt.address.toLowerCase();
  const token     = KNOWN_TOKENS[tokenAddr] || { symbol: `ERC-20(${evt.address.slice(0, 8)})`, decimals: 18 };

  alertToken(evt, direction, token);
}

// ── Main connection + subscription loop ─────────────────────────────────────

const BACKOFF_INITIAL_MS = 1_000;
const BACKOFF_MAX_MS     = 300_000;        // cap at 5 min
const HEARTBEAT_MS       = 5 * 60 * 1_000; // 5-minute liveness log

async function connect() {
  console.log(`[INFO] Connecting to      : ${WS_URL}`);
  console.log(`[INFO] Watching ${WATCHED.size} address(es): ${[...WATCHED].join(", ")}`);
  console.log(`[INFO] ERC-20 tokens      : ${Object.keys(KNOWN_TOKENS).length} known contracts`);
  console.log(`[INFO] Webhook alerts     : ${WEBHOOK || "disabled"}`);

  // web3.js v4 WebSocketProvider signature: (url, socketOptions?, reconnectOptions?).
  // We own reconnection in main(), so disable web3's internal reconnect
  // (autoReconnect defaults to true) to avoid overlapping subscriptions when
  // both our loop and web3 try to reconnect at once.
  const web3 = new Web3(new Web3.providers.WebsocketProvider(WS_URL, {}, { autoReconnect: false }));

  // Wait for connection
  await new Promise((resolve, reject) => {
    web3.currentProvider.on("connect", resolve);
    web3.currentProvider.on("error",   reject);
    setTimeout(() => reject(new Error("Connection timeout after 15 s")), 15_000);
  });
  console.log("[INFO] WebSocket connected");

  // Subscription 1: new block headers → scan for native ETH transfers
  const blockSub = await web3.eth.subscribe("newBlockHeaders");
  blockSub.on("data",  (header) => processBlock(web3, header.hash));
  blockSub.on("error", (err)    => console.warn("[WARN] Block subscription error:", err.message));

  // Subscriptions 2 & 3: ERC-20 Transfer events — two subscriptions are required.
  //
  // Ethereum topic filters use AND across slots and OR within a slot array.
  // A single subscription with watched addresses in topic[2] (the `to` slot) only
  // delivers incoming transfers — outgoing logs are filtered out at the node
  // before they arrive. Two targeted subscriptions cover both directions:
  //
  //   erc20InSub  — topic[2] = WATCHED (transfers TO a watched address)   → "RECEIVED"
  //   erc20OutSub — topic[1] = WATCHED (transfers FROM a watched address) → "SENT"
  //
  // Each handler passes its own direction to processTransferLog, so a transfer
  // between two watched addresses produces exactly one RECEIVED and one SENT.
  const watchedPadded = [...WATCHED].map(padAddress);

  const erc20InSub = await web3.eth.subscribe("logs", {
    topics: [TRANSFER_TOPIC, null, watchedPadded],
  });
  erc20InSub.on("data",  (evt) => processTransferLog(evt, "RECEIVED"));
  erc20InSub.on("error", (err) => console.warn("[WARN] ERC-20 in-subscription error:", err.message));

  const erc20OutSub = await web3.eth.subscribe("logs", {
    topics: [TRANSFER_TOPIC, watchedPadded, null],
  });
  erc20OutSub.on("data",  (evt) => processTransferLog(evt, "SENT"));
  erc20OutSub.on("error", (err) => console.warn("[WARN] ERC-20 out-subscription error:", err.message));

  console.log("[INFO] Subscribed to block headers and ERC-20 Transfer logs (in + out). Waiting...");

  // Periodic heartbeat so external watchdogs / log greppers can distinguish
  // "alive and quiet" from "dead and missing alerts". Cleared on disconnect.
  const heartbeat = setInterval(() => {
    console.log("[INFO] Heartbeat: alive, subscriptions active");
  }, HEARTBEAT_MS);

  try {
    // Hold until the WebSocket drops
    await new Promise((resolve) => {
      web3.currentProvider.on("disconnect", (event) => {
        console.error("[ERROR] WebSocket disconnected:", event);
        resolve();
      });
    });
  } finally {
    clearInterval(heartbeat);
    try { web3.currentProvider.disconnect(); } catch (_) {}
  }
}

async function main() {
  // Liveness: refresh /tmp/alive every 30 s from a top-level timer, independent
  // of connection state. During a reconnect backoff the process is still alive
  // and doing its job, so liveness should track the process, not the socket.
  const touchLiveness = () => { try { fs.writeFileSync(LIVENESS_FILE, ""); } catch (_) {} };
  touchLiveness();
  setInterval(touchLiveness, 30_000);

  let backoffMs = BACKOFF_INITIAL_MS;
  while (true) {
    const startedAt = Date.now();
    try {
      await connect();
    } catch (err) {
      console.error("[ERROR] Connection failed:", err.message);
    }
    // If we stayed up for at least a minute, reset the backoff — the previous
    // session was healthy, so we don't want a brief drop after hours of uptime
    // to start us at a long delay.
    if (Date.now() - startedAt > 60_000) {
      backoffMs = BACKOFF_INITIAL_MS;
    }
    const wait = _jitterMs(backoffMs);
    console.log(`[INFO] Reconnecting in ${(wait / 1000).toFixed(1)} s...`);
    await _delay(wait);
    backoffMs = Math.min(backoffMs * 2, BACKOFF_MAX_MS);
  }
}

main().catch((err) => { console.error("[FATAL]", err); process.exit(1); });
```

Save `monitors/eth/package.json` alongside it:

```json
{
  "name": "eth-monitor",
  "version": "2.0.0",
  "main": "monitor_eth.js",
  "dependencies": {
    "web3": "^4.0.0"
  }
}
```

After creating `package.json`, generate a lockfile once (the Dockerfile below uses `npm ci`, which requires a lockfile). Commit both `package.json` and `package-lock.json` so the build is reproducible. See [[#Setup steps|the setup steps]] for a host-Node-free way to generate it.

Save `monitors/eth/Dockerfile`:

```dockerfile
# monitors/eth/Dockerfile
FROM node:20-slim

# Create a non-root user for the runtime. Same reasoning as the BTC monitor:
# even with a read-only source mount, running as UID 0 inside a container that
# holds outbound WebSocket and HTTP connections is gratuitously dangerous.
# The `node` image already includes a `node` user (UID 1000), so we reuse it.

WORKDIR /app
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund
COPY --chown=node:node monitor_eth.js .

USER node
CMD ["node", "monitor_eth.js"]
```

The [[#Config: docker-compose.yml|compose service]] references this Dockerfile via `build:`, so dependencies are baked into the image once and the container starts in under a second instead of running `npm ci` on every restart.

## Maintenance: maintain.sh

_Weekly script that updates images, forces Fulcrum compaction, prunes old images, and reports disk usage._

Run this weekly, manually or via cron. Its primary job is forcing Fulcrum's startup compaction; the image pull, prune, and storage report are secondary.

```bash
#!/usr/bin/env bash
# maintain.sh — weekly maintenance for the Bitcoin + Ethereum node stack
# Run from the project root: bash scripts/maintain.sh
# Or schedule via cron: 0 3 * * 0 cd /path/to/stack && bash scripts/maintain.sh >> /var/log/node-maintain.log 2>&1

set -euo pipefail

log() { echo "$(date '+%Y-%m-%dT%H:%M:%S') [MAINTAIN] $*"; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

log "=== Weekly maintenance starting ==="

# ── 1. Pull latest images ────────────────────────────────────────────────────
log "Pulling latest images..."
docker compose pull

# ── 2. Recreate services that have new images ───────────────────────────────
# `up -d` recreates only containers whose image hash changed during the pull.
# We do this BEFORE the explicit fulcrum restart so that, when a Fulcrum
# release was pulled, the restart in the next step uses the new image rather
# than the old one.
log "Recreating services with new images (if any)..."
docker compose up -d --remove-orphans

# ── 3. Restart Fulcrum to trigger a compaction pass ─────────────────────────
# Fulcrum's `--compact-dbs` flag (on its compose command) rewrites the RocksDB
# and reclaims 5–15 GB on a mature install. RocksDB also auto-compacts in the
# background as Fulcrum runs, so the DB does not grow unbounded without this —
# the forced pass just reclaims stale space more aggressively. The restart
# must be unconditional: most weeks no Fulcrum update is pulled, and relying
# on `up -d`'s recreate-on-image-change behaviour would skip the pass in those
# weeks. If step 2 just recreated Fulcrum with a new image, this restart is
# redundant but harmless (compaction runs once more).
log "Restarting Fulcrum for weekly DB compaction..."
docker compose restart fulcrum

# ── 4. Wait for Fulcrum to come back healthy ────────────────────────────────
log "Waiting for Fulcrum to become healthy..."
FULCRUM_HEALTHY=0
for i in $(seq 1 30); do
  if docker exec fulcrum python3 -c "import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(0 if s.connect_ex(('127.0.0.1',50001))==0 else 1)" 2>/dev/null; then
    log "Fulcrum healthy after ${i}x30s intervals"
    FULCRUM_HEALTHY=1
    break
  fi
  sleep 30
done
if [ "$FULCRUM_HEALTHY" -eq 0 ]; then
  log "WARNING: Fulcrum did not become healthy after 15 minutes — check logs: docker compose logs fulcrum"
fi

# ── 5. Prune stopped containers and old tagged images ───────────────────────
# `-a` is required to remove old tagged images that are no longer referenced
# by a running container — without it, only fully dangling (untagged) images
# are removed, so the previous version of (say) geth would sit on disk forever
# after each pull. `until=168h` keeps anything pulled in the last week so a
# fast rollback is still possible.
log "Pruning unused Docker images older than 1 week..."
docker image prune -a -f --filter "until=168h"

# ── 6. Storage report ───────────────────────────────────────────────────────
log "--- Storage usage ---"
du -sh data/bitcoin  2>/dev/null && true
du -sh data/fulcrum  2>/dev/null && true
du -sh data/geth     2>/dev/null && true
du -sh data/lighthouse 2>/dev/null && true
df -h "$PROJECT_ROOT"
log "--- End storage report ---"

log "=== Weekly maintenance complete ==="
```

### Geth periodic maintenance — none required

_Path-scheme Geth prunes online; there is no offline sweep to schedule._

The stack runs Geth with `--state.scheme=path`, which prunes state online as new blocks arrive. There is no separate offline prune step, and disk usage stays roughly flat instead of climbing 100+ GB between sweeps. If you are running the legacy `--state.scheme=hash` setup instead (not what this file configures), see [[#Geth offline state pruning (legacy hash scheme only)|the note on hash-scheme pruning]].

## Wallet setup

_Point your wallet software at the local node instead of a third-party server._

### Bitcoin — Sparrow Wallet

1. Download Sparrow from [sparrowwallet.com](https://sparrowwallet.com/) and verify the signature
2. Open Sparrow → `Preferences` → `Server`
3. Select `Private Electrum`
4. Set: Host `127.0.0.1` · Port `50001` · SSL `off`
5. Click `Test Connection` — you should see your node's block height
6. Create wallet → connect hardware wallet via USB

### Ethereum — MetaMask

1. MetaMask → network dropdown → `Add a custom network`
2. Fill in:
    - Network name: `My Geth Node`
    - RPC URL: `http://127.0.0.1:8545`
    - Chain ID: `1`
    - Symbol: `ETH`
3. Save and select the network

### Ethereum — Frame (privacy-focused alternative)

Frame routes all dApp traffic system-wide through your node.

1. Download from [frame.sh](https://frame.sh/)
2. Settings → Connections → add `http://127.0.0.1:8545`
3. Connect hardware wallet in Frame's device panel

## Cold wallet guide

_Keys live on your hardware wallet and never touch this server._

### One or two devices

One hardware wallet is sufficient. A Ledger or Trezor runs separate Bitcoin and Ethereum apps on the same device; keys derive from different BIP-44 paths and never interact.

Use two devices only for air-gapped Bitcoin signing (Coldcard) paired with a Ledger for Ethereum, or for physical redundancy with devices stored in separate locations.

### Hardware wallet comparison

|Device|Bitcoin|Ethereum|Air-gap|Notes|
|---|---|---|---|---|
|Ledger Nano X|✓|✓|No|Most compatible; disable Bluetooth|
|Trezor Model T|✓|✓|No|Open source firmware|
|Coldcard Mk4|✓|No|Yes|Bitcoin-only, strongest BTC security|
|Foundation Passport|✓|No|Yes|Bitcoin-only, open source hardware|

### Key security rules

```
1. Buy directly from manufacturer — never secondhand
2. Initialise offline; write seed phrase on paper immediately
3. Transfer seed to steel backup (Cryptosteel, Bilodal, etc.)
4. Store seed separately from the device
5. Never photograph the seed phrase
6. Never type seed into any computer, app, or website
7. Consider a second backup copy in a different location
```

Your private keys never touch this server at any point. The node only provides a trustless view of the blockchain and a private channel to broadcast transactions.

## Receiving payments

_The base stack logs alerts and optionally POSTs a webhook. A real payment flow adds four concerns on top._

For a production payment flow, extend the monitors with fresh-address derivation, amount matching, confirmation waiting, and a backend webhook. Each is covered below.

### Generate a fresh address per payment

_Never reuse an address — it harms privacy and makes reconciliation ambiguous._

Reusing a single address is bad for privacy (anyone can correlate all your payments on a block explorer) and makes reconciling orders harder — you cannot tell which payment belongs to which invoice by address alone.

Bitcoin — derive a fresh address from your xpub for each invoice. You never expose the private key; addresses are derived deterministically from the public key, so the node never needs signing capability.

```python
# Example: derive the next unused BIP-84 (native SegWit) address from an xpub
# pip install bip-utils
from bip_utils import Bip84, Bip84Coins, Bip44Changes

def derive_btc_address(xpub: str, index: int) -> str:
    bip84_acc = Bip84.FromExtendedKey(xpub, Bip84Coins.BITCOIN)
    return (
        bip84_acc
        .Change(Bip44Changes.CHAIN_EXT)
        .AddressIndex(index)
        .PublicKey()
        .ToAddress()
    )
```

Store the `xpub` in your backend (not in `.env` on the node — it is not a secret, but there is no reason to expose it). Keep a counter of the last used index in your database and increment it with each new invoice.

Ethereum — ETH addresses are reusable by design and do not leak a common root the way Bitcoin addresses do. You can safely use one address per customer or per order. A simple approach is to derive fresh addresses from an HD wallet using the BIP-44 path `m/44'/60'/0'/0/index`, the same way as Bitcoin.

### Match amounts

_Confirm the received amount matches the invoice within a tolerance._

The base monitor alerts on any activity involving a watched address. For payment verification, confirm the received amount matches the expected invoice amount within an acceptable tolerance for exchange-rate fluctuation.

```python
# monitor_btc.py extension — replace the alert call in inspect_decoded_tx.
# Add `from decimal import Decimal` to the imports at the top of the file.
EXPECTED_AMOUNTS = {}   # address -> expected_btc; populate from your backend

def inspect_decoded_tx(decoded: dict) -> None:
    tx_id = decoded["txid"]
    for vout in decoded.get("vout", []):
        script    = vout.get("scriptPubKey", {})
        addresses = set(script.get("addresses", []))
        address   = script.get("address", "")
        if address:
            addresses.add(address)
        for addr in WATCH_ADDRS & addresses:
            received = vout["value"]                # Decimal
            expected = EXPECTED_AMOUNTS.get(addr)   # Decimal from your backend
            if expected is not None and abs(received - expected) < Decimal("0.00001"):
                send_alert(tx_id, received, "PAID", addr)
            else:
                send_alert(tx_id, received, "AMOUNT_MISMATCH", addr)
```

A simpler approach for low volume: issue invoices with slightly different amounts (e.g. 0.00314159 BTC, 0.00314160 BTC) so each payment is uniquely identifiable by value alone, without per-address derivation.

### Wait for confirmations

_A zero-confirmation transaction is not final; require confirmations proportional to value._

A zero-confirmation transaction is in the mempool but not yet final — it can in theory be replaced or dropped. How many confirmations you require depends on the value at risk.

|Amount|Bitcoin confirmations|Ethereum blocks|
|---|---|---|
|Small (< $100)|1|3–5|
|Medium ($100–$1 000)|3|12|
|Large (> $1 000)|6|30–64 (~2 epochs, finality)|

For Bitcoin, the ZMQ `rawtx` topic fires on mempool entry (0 conf). The base [[#Monitor: monitor_btc.py|monitor]] already connects its socket to both the rawtx and rawblock endpoints, so tracking confirmations only requires subscribing to `rawblock` and re-checking each pending transaction on every new block.

```python
# Near the other constants — track transactions awaiting confirmation:
from decimal import Decimal
REQUIRED_CONFIRMATIONS = 3
pending_txs: dict[str, tuple[str, Decimal]] = {}   # tx_id -> (address, amount)

# When a watched output is first seen (0-conf), record it — inside
# inspect_decoded_tx, alongside the RECEIVED alert:
#     pending_txs[tx_id] = (addr, vout["value"])

# Add the rawblock subscription in build_zmq_socket (the connection to the
# rawblock endpoint is already open):
sock.setsockopt(zmq.SUBSCRIBE, b"rawblock")

# In the receive loop, handle the rawblock topic. Reuse the outer-scope `rpc`
# — do NOT create a new AuthServiceProxy per block (each call already reuses
# the same HTTP connection).
if topic == b"rawblock":
    for tx_id in list(pending_txs):
        try:
            tx = rpc.getrawtransaction(tx_id, True)
        except JSONRPCException:
            continue   # not yet retrievable, retry next block
        if tx.get("confirmations", 0) >= REQUIRED_CONFIRMATIONS:
            addr, amount = pending_txs.pop(tx_id)
            send_alert(tx_id, amount, "CONFIRMED", addr)
```

For Ethereum, `tx.blockNumber` is set once mined. Subtract it from the current block number to get the confirmation count:

```javascript
const currentBlock = await web3.eth.getBlockNumber();
const confirmations = Number(currentBlock) - Number(tx.blockNumber);
if (confirmations >= REQUIRED_CONFIRMATIONS) markInvoicePaid(invoiceId);
```

### Webhook to your backend

_Both monitors already POST structured JSON on each event — you supply the receiver._

When `ALERT_WEBHOOK_URL` is set, each monitor POSTs a JSON body on every event, with retry and exponential backoff, and adds an `Authorization: Bearer <WEBHOOK_SECRET>` header when `WEBHOOK_SECRET` is set. The two chains send slightly different shapes:

```jsonc
// BTC (monitor_btc.py)
{ "chain": "BTC", "event": "RECEIVED", "txid": "...", "amount": "0.00314159",
  "address": "bc1q...", "ts": 1710000000 }

// ETH (monitor_eth.js) — native ETH and ERC-20 differ by asset/contract
{ "chain": "ETH", "asset": "USDC", "event": "RECEIVED", "hash": "0x...",
  "value": "100.000000", "block": 19000000, "contract": "0xa0b8...",
  "from": "0x...", "to": "0x...", "ts": 1710000000 }
```

A minimal Express receiver that verifies the bearer token and reads the real fields:

```javascript
// backend/routes/payment-webhook.js
app.post("/payment-webhook", express.json(), (req, res) => {
  // Reject spoofed requests when a shared secret is configured.
  const expected = `Bearer ${process.env.WEBHOOK_SECRET || ""}`;
  if (process.env.WEBHOOK_SECRET && req.get("authorization") !== expected) {
    return res.sendStatus(401);
  }
  const { chain, event, txid, hash, amount, value, address, ts } = req.body;
  console.log(`Payment event: ${chain} ${event}`, txid || hash, amount || value, address);
  // look up invoice by address/txid, verify amount, update order status
  res.sendStatus(200);
});
```

> [!important] The monitors run on `internal: true` networks with no route to the public internet, so an `ALERT_WEBHOOK_URL` pointing at ntfy.sh, Discord, Slack, or any external host is unreachable and every POST fails after its retries. Two options: run the receiver as a container attached to the `monitoring` network (keeps the isolation), or, if you must reach an external service, give the monitors an egress path (attach them to a non-`internal` network) and accept the reduced isolation.

To run a receiver as a container on the monitoring network, add it to the [[#Config: docker-compose.yml|compose file]] and reference it by service name (e.g. `ALERT_WEBHOOK_URL=http://payment-receiver:3000/payment-webhook`):

```yaml
  payment-receiver:
    build: ./receiver          # your Express app
    container_name: payment-receiver
    restart: unless-stopped
    networks:
      - monitoring             # reachable by the monitors; still no internet
    environment:
      WEBHOOK_SECRET: ${WEBHOOK_SECRET}
```

## Security model

_What this stack defends against, what it doesn't, and how to harden further._

### Image digest pinning

_Pinning by SHA256 digest makes an image reference immutable — recommended for production._

The [[#Config: docker-compose.yml|compose file]] pins core images by tag (`bitcoin/bitcoin:29.3`, `ethereum/client-go:v1.17.4`, `sigp/lighthouse:v8.2.0`, `cculianu/fulcrum:v2.1.0`). Tags are mutable — the image maintainer can re-push the same tag pointing at different bytes at any time. In the vast majority of cases this is benign (for example, a base-image security patch republished under the same tag), but for a money-handling stack it removes a defence-in-depth layer.

Pinning by SHA256 digest makes the reference immutable:

```bash
# After a successful `docker compose pull`, capture digests for every image:
docker images --digests --format '{{.Repository}}:{{.Tag}}@{{.Digest}}' | grep -v '<none>'
# Example output (yours will differ):
#   bitcoin/bitcoin:29.3@sha256:789abc…
#   ethereum/client-go:v1.17.4@sha256:abc123…
#   sigp/lighthouse:v8.2.0@sha256:def456…
#   cculianu/fulcrum:v2.1.0@sha256:0123de…
```

> [!note] Why `--format` and not `awk`: the plain `docker images --digests` output starts with a header row (`REPOSITORY TAG DIGEST ...`), so an `awk` pipe would emit a literal `REPOSITORY:TAG@DIGEST` line as its first result. The `--format` template skips the header automatically and produces exactly the strings you paste into `image:` lines.

Then in the compose file replace each `image: name:tag` with `image: name@sha256:digest`. A future `docker compose pull` will refuse to substitute a different bytestream under that reference, even if the tag moved upstream. To update intentionally, delete the digest and pull again to get the new one. The monitor images built locally via `build:` are inherently pinned to your own Dockerfile plus lockfile, so no digest is needed for them.

> [!warning] The `bitcoin/bitcoin` image is an _unofficial_, testing-oriented build: its maintainer states it is non-trivial to verify the authenticity of the Bitcoin Core binaries inside, and recommends that non-testing users build from source or verify the binary themselves. Digest pinning makes an image reference immutable, but does not prove the bytes are authentic Bitcoin Core. For a money-handling node this is a residual trust assumption worth closing — consider building the bitcoind image yourself from verified Bitcoin Core binaries.

### What is protected

|Threat|Mitigation|
|---|---|
|RPC exposed to internet|Ports not published to host; Docker subnet restriction|
|Credential leakage|Secrets in `.env`; bitcoind holds only the salted `rpcauth` hash|
|Container lateral movement|Isolated networks per chain; monitors cannot reach node internals|
|Ethereum remote signing|`personal` namespace disabled on Geth|
|Script tampering|Monitor code baked into the image; container filesystem read-only (`read_only: true`)|
|Geth/Lighthouse spoofing|JWT secret required; unauthenticated connections rejected|
|Privilege escalation|`no-new-privileges:true` on all containers|
|Signal handling / zombie processes|`init: true` on all containers|
|Unbounded log growth|JSON log driver with `max-size`/`max-file` rotation on all services|

### What is not protected

|Threat|Notes|
|---|---|
|Host OS compromise|Securing the host is outside this stack's scope|
|Network traffic analysis|Your ISP can see you run a Bitcoin/Ethereum node|
|Physical access|Secure the machine physically|
|Seed phrase theft|Hardware wallet security is your responsibility|

### Optional: route Bitcoin over Tor

_Hide your node's IP from Bitcoin peers._

Run a Tor container on the Bitcoin external network, then point bitcoind at it by adding the proxy settings to [[#Config: bitcoin.conf|bitcoin.conf]] (this image reads its config from that file, not from environment variables):

```yaml
# docker-compose.yml
services:
  tor:
    image: goldy/tor-hidden-service:latest
    container_name: tor
    networks:
      - btc-external
```

```ini
# add to data/bitcoin/bitcoin.conf
proxy=tor:9050
onlynet=onion
```

## Networking and firewall

_Which ports face the internet, which stay internal, and the firewall rules to match._

### Published ports

|Port|Proto|Service|Purpose|
|---|---|---|---|
|8333|TCP|bitcoind|Bitcoin p2p|
|30303|TCP+UDP|geth|Ethereum p2p|
|9000|TCP+UDP|lighthouse|Consensus p2p|
|8545|TCP|geth|JSON-RPC for MetaMask/Frame (127.0.0.1 only)|
|50001|TCP|fulcrum|Electrum TCP (127.0.0.1 only)|
|50002|TCP|fulcrum|Electrum SSL (127.0.0.1 only)|

### Internal-only ports

_Reachable only on the Docker networks, never from the host._

|Port|Service|Accessed by|
|---|---|---|
|8332|bitcoind RPC|fulcrum, btc-monitor|
|28332|bitcoind ZMQ blocks|btc-monitor (confirmation tracking)|
|28333|bitcoind ZMQ tx|btc-monitor|
|8546|geth WebSocket|eth-monitor|
|8551|geth Auth RPC|lighthouse|
|5052|lighthouse Beacon API|geth (internal), docker exec only|

### ufw firewall (if the server is internet-facing)

```bash
ufw allow 8333/tcp
ufw allow 30303/tcp
ufw allow 30303/udp
ufw allow 9000/tcp
ufw allow 9000/udp
ufw allow 22/tcp        # SSH
ufw default deny incoming
ufw enable
```

Ports 50001 and 50002 are bound to `127.0.0.1` in the compose file — no firewall rule needed.

## Operations and maintenance

_Everyday commands, updates, backups, and cache tuning._

### Daily commands

```bash
# Start / stop
docker compose up -d
docker compose down

# Logs
docker compose logs -f
docker compose logs -f bitcoind   # single service

# Restart one service
docker compose restart fulcrum

# Check all container status
docker compose ps

# Disk usage per service
du -sh data/bitcoin data/fulcrum data/geth data/lighthouse
```

### Update all images

```bash
docker compose pull
docker compose up -d
# `up -d` automatically recreates only the containers whose image hash
# changed during the pull. Do NOT add --force-recreate — that would
# restart every service (including bitcoind and geth) for no reason,
# triggering re-verification of the chain state on each start.
```

### What to back up

|Item|Path|Priority|
|---|---|---|
|Secrets|`.env`|Critical|
|bitcoind config|`data/bitcoin/bitcoin.conf`|Critical — holds the `rpcauth` line|
|JWT secret|`data/jwt.hex`|Critical — regenerating requires restarting Geth + Lighthouse|
|Fulcrum config|`config/fulcrum.conf`|Important|
|Monitor sources|`monitors/`|Important|
|Maintenance script|`scripts/maintain.sh`|Important|
|Blockchain data|`data/bitcoin`, `data/geth`, etc.|Optional — re-syncable from network|

### Increase cache for faster sync

Edit [[#Config: bitcoin.conf|bitcoin.conf]] and the [[#Config: docker-compose.yml|compose file]] if you have more than 16 GB of RAM:

```ini
# data/bitcoin/bitcoin.conf — default 512
dbcache=2048
```

```yaml
# geth command in docker-compose.yml — default 1024
--cache=4096
```

```ini
# config/fulcrum.conf — default 1024
db_mem = 2048.0
```

## Troubleshooting

_Symptoms and fixes for the common failure modes._

### bitcoind won't start or healthcheck keeps failing

```bash
docker compose logs bitcoind
# Look for lines starting with "Error:"

# Possible fixes:
# Bad config:      confirm data/bitcoin/bitcoin.conf exists and its rpcauth line
#                  is valid (regenerate with rpcauth.py if unsure)
# Auth mismatch:   the rpcauth line's user must equal BTC_RPC_USER, and
#                  BTC_RPC_PASSWORD must be the password used to generate it
# Corrupted data:  add `reindex=1` to bitcoin.conf, restart, remove after sync
# Disk full:       df -h
```

The healthcheck runs `getblockchaininfo`, which succeeds as soon as the RPC server is responsive — it does not wait for full sync. A node that is up but still syncing is healthy; sync progress is a separate check (see [[#Checking sync progress|checking sync progress]]).

### Fulcrum won't start or connect

```bash
docker compose logs fulcrum
# Fulcrum will not begin indexing until bitcoind is fully synced.
# A fresh sync takes 1–3 days — this is expected.

# Check credentials match exactly:
grep rpcuser config/fulcrum.conf
grep BTC_RPC_USER .env

# --compact-dbs adds 5–15 min to Fulcrum startup — this is normal.
```

### Geth and Lighthouse not communicating

```bash
# Verify JWT secret is identical in both containers
docker exec geth cat /jwt.hex
docker exec lighthouse cat /jwt.hex
# Must be the same hex string

# If different, regenerate and restart both:
openssl rand -hex 32 > data/jwt.hex
docker compose restart geth lighthouse
```

### Geth stuck at same block

```bash
docker compose logs geth | tail -50

# Check Lighthouse is healthy:
docker compose ps lighthouse

# Check peer count (must be > 0):
docker exec geth geth attach \
  --exec "net.peerCount" /root/.ethereum/geth.ipc
# If 0, port 30303 TCP+UDP must be open in your firewall
```

### Geth: "--state.scheme=path" error on existing data

```
Error: Failed to open database: incompatible state scheme, ...
```

This means existing data was created with the hash scheme and cannot be migrated in-place. You must wipe and re-sync:

```bash
docker compose stop geth lighthouse
rm -rf data/geth
docker compose start geth lighthouse
# Allow 4–8 hours to re-sync (snap sync)
```

### Monitor containers crash-looping

```bash
docker compose logs btc-monitor
docker compose logs eth-monitor

# Most likely cause: node not fully synced yet.
# This is normal — restart: unless-stopped retries automatically.
# Once the node is healthy, monitors stabilise.
# Both monitors include reconnection logic and recover from ZMQ/WebSocket
# drops without restarting the container. The container healthcheck reads a
# /tmp/alive liveness file the script refreshes, so an "unhealthy" status
# means the process itself has hung or the upstream node is unreachable.
```

### Sparrow wallet "Could not connect"

```bash
# 1. Check Fulcrum is running
docker compose ps fulcrum

# 2. Test port from host
nc -zv 127.0.0.1 50001    # should say "open"

# 3. Sparrow settings:
#    Server → Private Electrum → Host: 127.0.0.1 · Port: 50001 · SSL: off

# 4. Wait for Fulcrum to finish indexing (can take 12–24h after Bitcoin syncs)
docker compose logs fulcrum | tail -20
```

### MetaMask showing wrong balance

```bash
# Check Geth is fully synced first
docker exec geth geth attach \
  --exec "eth.syncing || 'fully synced'" \
  /root/.ethereum/geth.ipc

# Force MetaMask refresh: click the circular arrow icon next to your account
# If still wrong: docker compose restart geth
```

### Disk growing faster than expected

```bash
# 1. Check Docker log sizes (unrotated logs are the most common surprise)
du -sh /var/lib/docker/containers/*/

# 2. Verify log rotation is active — all services should show max-size
docker inspect bitcoind | grep -A5 '"LogConfig"'

# 3. Run the maintenance script
bash scripts/maintain.sh

# 4. With path-scheme Geth, state grows ~25 GB/month and pruning is online —
# there is no offline step to run. If you see runaway growth (e.g. multiple
# hundred GB/month), check for a misconfiguration: `docker inspect geth | grep state.scheme`
# must report `path`, not `hash`.
```