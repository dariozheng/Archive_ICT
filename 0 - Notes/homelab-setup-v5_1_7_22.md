# Homelab Setup Guide v5.1.7.22 — Ubuntu Server 24.04 LTS on Raspberry Pi 5

> **Bug-fix changelog (v5.1.7.22):**
> - **New §11 — PostgreSQL 18.4-alpine database server for future self-hosted web apps.** Pinned `postgres:18.4-alpine`. Picked PostgreSQL over MariaDB/MySQL because the modern self-hosted ecosystem (Immich, Paperless-ngx, Authentik, Vaultwarden's `vaultwarden-postgres`, Gitea/Forgejo, Synapse, Mastodon, Nextcloud's recommended backend) almost uniformly defaults to or recommends Postgres; pinned to the Alpine variant for ~80MB image vs ~150MB for the Debian variant and a smaller running RSS on the Pi 5's 8 GB. **Two PG 18 gotchas baked into the §11 compose to save the next deploy:** (a) `PGDATA` changed to `/var/lib/postgresql/18/docker` (was `/var/lib/postgresql/data`) and the declared VOLUME moved from `/var/lib/postgresql/data` → `/var/lib/postgresql` (PR docker-library/postgres#1259, released with PG 18 GA Sept 2025) — mounting the old path on PG 18 gets you `Error: ... configured to store database data in a format which is compatible with "pg_ctlcluster" ... Counter to that, there appears to be PostgreSQL data in: /var/lib/postgresql/data (unused mount/volume)` and the container won't start; the §11 compose mounts `postgres-data:/var/lib/postgresql` (the new convention, which also lets future `pg_upgrade --link` between major versions work without crossing mount-point boundaries); (b) the Alpine PG 18 image ships a compatibility symlink `/var/lib/postgresql/data → .` that the Debian variant does **not** — sticking with Alpine therefore preserves the option of bind-mounting the legacy path in a one-off recovery scenario, the Debian variant would not. The 18.4 line specifically also adds `liburing` / `--with-liburing` for io_uring async I/O on the arm64 build, which on NVMe-backed Pi 5s gives a measurable read latency drop on heavy concurrent workloads. SCRAM-SHA-256 is the default password auth method (since PG 14) so `pg_hba.conf` needs no tweaks for that.
> - **New shared bridge `db-net` (`172.29.0.0/24`), pre-created in §11 with the same `external: true` pattern proxy-net uses.** Lives below dns-net (`172.30.0.0/24`) and proxy-net (`172.31.0.0/24`), and crucially **outside the §3 `default-address-pools` range `172.20.0.0/14`** (which covers `172.20–172.23.x`) — so no daemon.json edit is required and Docker's auto-allocator can't collide with it. Postgres pins to `172.29.0.10` following the same static-IP convention fix #120 established for proxy-net/dns-net. Future web-app stacks attach to **both** `db-net` and `proxy-net` (db-net for the Postgres connection, proxy-net for Caddy to reverse-proxy them); the §11 "Adding a web app later" subsection has the worked compose snippet plus the Caddyfile stanza, Pi-hole local DNS record, and Kuma monitor entries.
> - **No port published to the host on the Postgres container.** Admin happens via `docker exec -it postgres psql -U postgres`, not via a `127.0.0.1:5432` bind. The reasoning matches fix #120's general direction: every additional `127.0.0.1:*` bind is one more thing to remember to firewall, one more thing the DOCKER-USER chain (§3) needs to reason about, and one more attack surface for any future LAN-side compromise. Web apps reach Postgres at `postgres:5432` over db-net (Docker embedded DNS resolves the container name), which is the only path that needs to work — and that path doesn't need a host-side port publish at all. Adminer / pgAdmin can be added as a separate proxy-net+db-net container later if a UI becomes useful; the §11 prose calls this out without prescribing it.
> - **POSTGRES_PASSWORD via Portainer env-vars panel, not in YAML.** Same convention §6 Pi-hole (`FTLCONF_webserver_api_password`), §7 Step-CA (`DOCKER_STEPCA_INIT_PASSWORD`), and §12 Watchtower (`WATCHTOWER_NOTIFICATION_URL`) already use, with the same `cd /opt/postgres && POSTGRES_PASSWORD='...' docker compose up -d` CLI fallback that matches the pattern the v5.1.7.10 fix #101/#102 sweep established. Per-app database+role creation is documented as a post-deploy `psql` step rather than via `/docker-entrypoint-initdb.d/*.sql` mounts — init scripts run **only** on first init (empty PGDATA), so using them for the per-app schemas creates a quietly different behaviour between "deployed today" and "redeployed after a volume wipe", which is exactly the kind of footgun the rest of this guide spends pages avoiding.
> - **Backup gap explicitly acknowledged in §11.** §12 Restic was removed in v5.1.7.19 (fix #122), so the database has **no automated backup** unless the user adds one. The §11 prose includes a one-paragraph recommendation: a `pg_dumpall` cron entry to `/opt/postgres/dumps/` (gitignored) is the minimum that preserves data across a volume wipe. Not auto-deployed — adding it without a corresponding offsite copy creates a false-confidence loop (backups exist on the same SSD that's failing), and the user removed Restic deliberately. This is flagged rather than fixed; the user makes the call.
> - **Sections renumbered.** Old §11 DDNS → new §12; old §12 Monitoring + Watchtower → new §13; old §13 Final Checklist → new §14; old §14 Operations and Troubleshooting → new §15. The renumber sweep updated: the live cross-references in §2 (`smartmontools ... (§14)` → `(§15)`), §8 Caddyfile callout (`installed (§13 trust-store table)` → `(§14)` and `Add a Kuma monitor for it (§12)` → `(§13)`), §12 DDNS (`In Uptime Kuma (§12)` → `(§13)`), and §15 troubleshooting (`run the MTU probe in §14` → `§15`). The bug-history table at the bottom keeps the original §X numbers per the v5.1.7.19 convention — those rows describe doc state at the time of the fix and intentionally aren't rewritten.
> - **Incidental TOC fix carried over from v5.1.7.19.** v5.1.7.19 renumbered the doc sections and updated the TOC's anchor URLs but missed the displayed numbers — the TOC read `1, 2, … 10, 11, 13, 14, 15` (skipping 12 entirely, with the 13/14/15 anchors pointing to `#12-…/#13-…/#14-…`). The v5.1.7.22 TOC rewrite is `1, 2, … 11, 12, 13, 14, 15` with all anchors matching. No action required for users who already followed v5.1.7.19+, this is documentation-only.
> - **Stack section (top-of-doc) gets a PostgreSQL line.** Added between Home Assistant and Step-CA so the stack inventory matches what's actually deployed. (Note: that section still lists "Nginx Proxy Manager" rather than Caddy — that's a pre-existing v5.1.7.17 oversight, intentionally NOT corrected here to keep this changelog scoped; it'll get caught in a future cleanup pass.)
> - **§14 Final Checklist updates.** `postgres` added to the "Containers expected up" list and the stack-status table (`postgres / postgres / Active`).
> - **§15 Operations updates.** Directory tree gains `postgres/` under `/opt/`; "What to put in git" path list gains `/opt/postgres/docker-compose.yml` (the `dumps/` subdir is gitignored — write `dumps/` to `/opt/postgres/.gitignore`). Two new rows in the troubleshooting table: (a) the PG 18 wrong-volume-path startup error keyed off the `(unused mount/volume)` log message, with the migration command for anyone who upgraded a PG 17 volume in place; (b) "web app can't reach postgres" → check the app stack attaches both `db-net` AND `proxy-net` as `external: true`, not just one.
>
> **Operational notes:** there is no v5.1.7.21 → v5.1.7.22 migration step — §11 is purely additive. To bring it up on a running v5.1.7.21 Pi: `docker network create --driver bridge --subnet 172.29.0.0/24 db-net`, then `sudo mkdir -p /opt/postgres && cd /opt/postgres`, write the compose YAML from §11, set `POSTGRES_PASSWORD` in Portainer's env-vars panel (or pass it inline on the CLI fallback), `docker compose up -d`. Verify with `docker exec -it postgres pg_isready -U postgres` (expect `accepting connections`) and `docker exec -it postgres psql -U postgres -c '\\l'` (lists databases: `postgres`, `template0`, `template1` on a fresh init). The renumber doesn't change any on-disk paths or systemd unit names; it's a documentation-only renumber so existing deployments don't need touching.

> **Bug-fix changelog (v5.1.7.21):**
> - **§4 entirely rewritten — single Proton tunnel → N parallel Proton tunnels with per-client routing (fix #124).** The previous design ran one `protonvpn` tunnel that all Pi-side outbound and all forwarded wg0 client traffic went through. The new design runs `protonvpn0`, `protonvpn1`, … in parallel, each terminating at a different exit country, and uses iptables-mangle `MARK` rules in PREROUTING to tag each wg0 client peer's packets with a per-tunnel routing-table ID — Phone (10.10.0.2) gets mark 100 → routes through protonvpn0's table → Netherlands exit; Laptop (10.10.0.3) gets mark 101 → routes through protonvpn1's table → USA exit. The mapping lives in `/etc/wireguard/proton.conf` (the only file you edit when adding tunnels or reassigning clients) and is applied at boot by `proton-routing.service` and reloadable via `systemctl reload proton-routing.service`. A `proton-healthcheck.service` daemon pings through each tunnel every 60s and (a) restarts wg-quick@protonvpnN on three consecutive failures, (b) reroutes affected clients to `DEFAULT_TUNNEL` if restart doesn't fix it, (c) restores normal routing when the tunnel comes back. `proton-status.sh` gives a one-shot human overview (tunnels, client-routing-mark status, failover overrides, exit IPs).
> - **Pi-side outbound semantics changed.** This is the biggest behaviour difference and is called out in the §4 "What changed" table. Previously, the Pi's own outbound (Docker pulls, Step-CA ACME calls, Caddy ACME challenges reaching out, Watchtower hitting registries, container egress generally) went through the single Proton tunnel because `wg-quick` auto-installed `ip rule not fwmark 51820 lookup 51820`. In v5.1.7.21 each `protonvpnN.conf` sets `Table = off`, which suppresses wg-quick's auto-routing entirely — so the unmarked Pi-host traffic falls through to the kernel-default main-table route via eth0 → home ISP, unmasked. Only the *forwarded* wg0 client traffic gets per-tunnel marks from `proton-routing.sh`. If you don't want Pi-host outbound exposed to your ISP, stay on v5.1.7.20.
> - **Fix #117 stance preserved but the plumbing changed.** `FwMark = 51820` on wg0's [Interface] is still load-bearing (and now finally written into the §5 wg0.conf YAML block — the v5.1.7.19 changelog described adding it but the block itself was missed during the §12 deletion sweep). The fwmark-51820 exemption in `PROTON_KS` that previously came for free with the single-tunnel wg-quick is now installed explicitly by the new `/usr/local/bin/proton-killswitch-init.sh`. The fix #117 comment in §5 wg0.conf updated to explain the v5.1.7.21 plumbing change. §14 troubleshooting row for the inbound-148-no-outbound-92 tcpdump signature updated to point at `proton-killswitch-init.service` for the chain origin.
> - **`/usr/local/bin/proton-killswitch-init.sh` is new (fix #125).** Creates the `PROTON_KS` chain in both `iptables` and `ip6tables`, installs the permanent baseline RETURN rules (LAN, wg0 subnet, Docker bridges, multicast, NTP, addrtype LOCAL, **and the fwmark 51820 wg0-protocol exemption**), and ends with the final REJECT. Per-tunnel `-o protonvpnN` and `-m mark --mark <table>` RETURN lines are inserted by `proton-tunnel-up.sh` at each tunnel's PostUp and removed at PreDown. The chain is created by `proton-killswitch-init.service` which orders `Before=wg-quick@protonvpn0.service wg-quick@protonvpn1.service`, so the chain exists before any individual tunnel comes up. Note: systemd has no globbing in `Before=`, so adding `protonvpn2` later requires editing this unit and `systemctl daemon-reload`. The §4 "Add a new tunnel" subsection documents this.
> - **`Table = off` is mandatory in each `protonvpnN.conf` (fix #126).** Without it, every `wg-quick@protonvpnN` would auto-install its own ip rule + auto-table with the default fwmark 51820 (the same value!), and the two (or N) tunnels would fight over the same table/rule pair on startup, producing nondeterministic routing depending on which came up last. With `Table = off`, all routing is owned by `proton-tunnel-up.sh`. The template in §4 documents this with an inline comment cross-referencing this exact failure mode.
> - **MTU pinned to 1320 per Proton tunnel (corrects user's template).** The earlier multi-tunnel script template the user uploaded had `MTU = 1420` — that's the ProtonVPN.com recommendation for direct-to-internet WireGuard, but the homelab stacks wg0 (1280) *inside* protonvpnN, so the outer tunnel needs the canonical 1320 ProtonVPN-server-side ceiling. 1420 caused fragmentation and silent large-transfer stalls in testing.
> - **IPv6 parity throughout (fix #127).** The user's uploaded scripts were IPv4-only; the v5.1.7.21 doc replicates every mangle / nat / route / rule operation in `ip6tables` and `ip -6`. wg0 carries `fd00:10:10::/64` and the multi-tunnel design now routes that ULA prefix through the same per-client marks as v4. The IPv6 derivation in `proton-routing.sh` is naive but correct for this exact wg0 numbering (10.10.0.N ↔ fd00:10:10::N).
> - **`proton-healthcheck.sh` hardened (fix #128).** `attempt_restart` sleep bumped from 5s → 15s (cold-path Proton handshake on a freshly restarted tunnel can take 10–15s). `proton-healthcheck.service` gains `StartLimitBurst=5, StartLimitIntervalSec=300` so a config-error crash loop gives up after 5 restarts in 5 minutes instead of filling the journal forever. The `CONNMARK --save-mark` lines from the user's upload removed — the return-path packet routes correctly via main table's `10.10.0.0/24 dev wg0` without needing the mark, so save without matching restore was cosmetic.
> - **`proton-routing.service` cleanups.** Removed the hardcoded `wg-quick@protonvpn0.service wg-quick@protonvpn1.service` from `After=` (using `After=network-online.target proton-killswitch-init.service` instead, which works regardless of tunnel count); removed `PartOf=wg-quick@protonvpn0.service` which would have torn down routing for laptop if protonvpn0 specifically stopped. Three separate systemd-unit files instead of the user's one-file-with-two-units-concatenated.
> - **Migration commands for upgrading from v5.1.7.20.** `systemctl disable --now wg-quick@protonvpn`, `rm /etc/wireguard/protonvpn.conf /etc/wireguard/protonvpn-up.sh /etc/wireguard/protonvpn-down.sh`, then walk through the new file installs and enable order. Documented at the bottom of §4.

> **Bug-fix changelog (v5.1.7.20):**
> - **Bumped `tecnativa/docker-socket-proxy` from `0.3.0` to `v0.4.2`** in the §3 Portainer + docker-socket-proxy combined compose, and updated the matching line in the closing image-pin summary list. v0.4.x is the HAProxy-3.x line (0.3.x ran HAProxy 2.x; an interim attempt at HAProxy 3.x was reverted before 0.3.0, then landed properly in v0.4.0). v0.4.2 specifically added a `touch /var/lib/haproxy/server-state` in the entrypoint to satisfy HAProxy 3.x's expectation that the server-state file exists before workers start — without that, HAProxy 3.x logs `config: Can't open global server state file '/var/lib/haproxy/server-state': No such file or directory` at boot. Tag format also changed: pre-v0.4.x used a bare `0.3.0`/`0.2`-style tag; v0.4.x is prefixed `v0.4.0`/`v0.4.1`/`v0.4.2`. The `--read-only` situation is unchanged in v0.4.x — the entrypoint still sed-renders `haproxy.cfg.template` -> `haproxy.cfg` in `/usr/local/etc/haproxy/`, so the FIX #113 stance (no `--read-only`, `security_opt: [no-new-privileges:true]` instead) still applies. Env var allowlist (`CONTAINERS=1`, `IMAGES=1`, `POST=1`, `DELETE=1`, `EXEC=0`, etc.) is unchanged between 0.3.x and 0.4.x. Upgrade path on a running Pi: edit `/opt/portainer/docker-compose.yml`, change the image tag, then `cd /opt/portainer && sudo docker compose pull docker-socket-proxy && sudo docker compose up -d docker-socket-proxy` — Portainer will briefly lose its `DOCKER_HOST` connection during the recreate, recovers automatically on restart. The compose `depends_on: docker-socket-proxy.service_started` from v5.1.7.19 ensures Portainer is recreated in the right order on any subsequent `docker compose up -d`. (fix #123)

> **Bug-fix changelog (v5.1.7.19):**
> - **wg0 + ProtonVPN coexistence: `FwMark = 51820` on the wg0 [Interface] block (fix #117).** Without this, when ProtonVPN is up, wg0's protocol traffic (handshake responses, keepalives, data packets generated by the kernel WG module on the wg0 listening socket) follows the host's default route — which after Proton comes up is the Proton tunnel itself. The reply egresses with source IP `10.2.0.x` (Proton's), the remote client expects a reply from the home WAN IP, drops it, and the handshake silently fails forever. tcpdump on eth0 shows inbound length-148 (`MessageInitiation`) with no outbound length-92 (`MessageResponse`). Reusing ProtonVPN's wg-quick-assigned fwmark `51820` is the cleanest fix because wg-quick already installed both pieces of infrastructure we need for it: the routing rule `ip rule not fwmark 51820 lookup 51820` (sends marked packets via the main table = eth0) AND the kill-switch exception `PROTON_KS -m mark --mark 51820 -j RETURN` (skips the OUTPUT-chain REJECT). A different fwmark would route correctly but get REJECT'd by the kill switch before reaching the wire. The §5 wg0.conf now carries `FwMark = 51820` in the [Interface] block plus an explanatory comment cross-referencing this exact failure mode, and the §14 troubleshooting table gets a dedicated row keyed off the tcpdump signature
> - **`wg-add-client.sh` helper script in §5 (fix #118).** Generating client keypairs by hand has bitten this guide at least twice: stale `# --- phone ---` markers accumulating in wg0.conf after re-runs (because `wg addconf` is additive-only), private keys getting echoed to stdout and saved in shell history, and `Address` lines using `/24` instead of `/32` (deviates from the cryptokey-routing convention). The new script lives at `/usr/local/bin/wg-add-client` and: refuses to re-add an existing client name (forces deliberate cleanup of stale Peer blocks); auto-assigns next free `10.10.0.N` with a sane default for the first-client-on-empty-conf edge case; uses `umask 077` so the privkey is never world-readable; writes /32+/128 on the client Address; appends the Peer block to wg0.conf; hot-reloads via the temp-file syncconf pattern (fix #119, below); prints a QR code; never prints the privkey to stdout
> - **Temp-file pattern for `wg syncconf` (fix #119).** `sudo wg syncconf wg0 <(sudo wg-quick strip wg0)` fails with `fopen: No such file or directory`. Process substitution creates a `/dev/fd/63` FIFO that's visible in the parent shell, but `sudo` closes file descriptors > 2 on the new process before exec'ing wg — so wg tries to `fopen("/dev/fd/63")` inside the sudo'd process where that FD no longer exists. Replace with `wg-quick strip wg0 > /tmp/wg0.stripped && wg syncconf wg0 /tmp/wg0.stripped && rm /tmp/wg0.stripped`. Works whether you're running as root or via sudo. The `wg-add-client.sh` script uses this pattern internally; the §14 troubleshooting row documents the standalone failure mode
> - **Static IPs on `proxy-net` and `dns-net` (fix #120).** Each container that lives on either bridge now pins to a specific address via `networks.<bridge>.ipv4_address` in compose: caddy → 172.31.0.10, step-ca → 172.31.0.11, portainer → 172.31.0.12, docker-socket-proxy → 172.31.0.13, pihole → 172.31.0.14 (and 172.30.0.3 on dns-net), uptime-kuma → 172.31.0.15, watchtower → 172.31.0.16, unbound → 172.30.0.2. Documented as a table at the top of §3 (Create the shared proxy-net network). The motivation: HA's `trusted_proxies` can shrink from "the whole `/24`" to "Caddy's specific 172.31.0.10" so any future container on the same bridge doesn't auto-inherit trusted-proxy status, the §14 service URL / firewall debugging gets a stable IP map, and `docker network inspect proxy-net` becomes a deterministic reference. dns-net also gets an explicit `gateway: 172.30.0.1` for symmetry. Container names still resolve via Docker's embedded DNS — the static IPs are belt-and-braces, not the primary mechanism. §8 Caddyfile callout updated to use `trusted_proxies: [172.31.0.10, 127.0.0.1, ::1]`
> - **Portainer + docker-socket-proxy merged into one Compose stack at `/opt/portainer/docker-compose.yml` (fix #121).** Previously both were `docker run` invocations because of the chicken-and-egg ordering (Portainer can't deploy itself or the proxy it depends on). The new approach keeps the bootstrap-CLI ordering — `cd /opt/portainer && sudo docker compose up -d` — but stores both definitions as YAML, with `depends_on: docker-socket-proxy.service_started` ensuring the proxy comes up first. Portainer auto-discovers the resulting stack as "External" (Compose project labels make it picked up by Portainer's stack scanner), so subsequent edits/redeploys happen from the Portainer UI like any other stack — only the first deploy is CLI-only. The `--read-only` / `--security-opt=no-new-privileges` / `EXEC=0` / volumes / network-IP configuration all translate verbatim from the v5.1.7.18 `docker run` form. §3 "What cannot be a Portainer-managed stack" list now collapses to just the `portainer` stack itself plus wg0 and ProtonVPN (Restic is gone — see next bullet)
> - **Removed §12 (Backups with Restic) entirely (fix #122).** The user-driven removal — `restic backup` to Backblaze B2, the `homelab-backup.sh` script, the systemd timer, the Telegram-notify unit, the restore drill, the B2 split-key + Object Lock setup. §13/14/15 renumbered down to §12/13/14 (Monitoring + Watchtower, Final Checklist, Operations and Troubleshooting). The §14 directory tree drops `homelab-backup.sh`/`homelab-backup.service`/`homelab-backup.service.d/`/`homelab-backup.timer`/`homelab-backup-notify@.service`; the §14 "What to put in git" path list drops `/usr/local/bin/homelab-backup.sh`; the §14 verify-everything-running commands drop `sudo systemctl list-timers homelab-backup.timer`; the §8 Caddy compose volumes-comment drops the "in the §12 backup STOP_LIST" sentence; the closing prose summary drops the "Backup widened" and "B2 split keys" bullets. **The bug-history table also lost 26 rows** — every entry whose Section column was `§12 *` is gone (the historical fixes were specific to the removed script and aren't actionable in v5.1.7.19's stack). Section-renumber sweep also caught in-prose `§13 Kuma` → `§12 Kuma`, `§14 git list` → `§13 git list`, `§15 service URL table` → `§14 service URL table`, and the anchor links in the TOC. Older changelog entries near the top of this doc still reference `§12 backup-quiesce window` etc. — those are historical narrative describing the doc state at the time of the change and were intentionally not rewritten
>
> **Operational notes:** to apply the fix-#119 syncconf fix on a running Pi: `wg-quick strip wg0 > /tmp/wg0.stripped && wg syncconf wg0 /tmp/wg0.stripped && rm /tmp/wg0.stripped`. To apply the fix-#117 fwmark: edit `/etc/wireguard/wg0.conf`, add `FwMark = 51820` to the [Interface] block, then `sudo systemctl restart wg-quick@wg0`. Verify with `sudo wg show wg0 fwmark` (expect `0xca6c`). To apply the fix-#120 static IPs on an existing deployment: edit each stack's compose, recreate the affected containers (`docker compose up -d` per stack — Docker rejects the request if the IP is already taken, which is why the allocations are distinct). To apply fix-#121 (Portainer compose): `docker stop portainer docker-socket-proxy && docker rm portainer docker-socket-proxy`, write the new `/opt/portainer/docker-compose.yml`, then `cd /opt/portainer && sudo docker compose up -d`. The `portainer-data` named volume from the old `docker run` and the `portainer_data` named volume from the new compose differ in underscore-vs-hyphen — rename the volume or pre-create the new one with `docker volume create portainer-data` and copy contents over: `docker run --rm -v portainer_data:/from -v portainer-data:/to alpine sh -c 'cp -a /from/. /to/'`

> **Bug-fix changelog (v5.1.7.18):**
> - Replaced every reference to `1.1.1.1` with `9.9.9.9` (Quad9) across all 12 occurrences in the doc. The swap covers: the host's `/etc/resolv.conf` second nameserver and the netplan fallback during initial setup (§2); `daemon.json` `dns: [...]` second-listed fallback for containers (§3 / fix #111); the router's secondary DHCP DNS (§6 prose, §14 router-config table); the §9 LAN-gateway-design failover narrative (what LAN clients hit if Pi-hole is down); the §12 Kuma "Proton tunnel alive" ping target; and the §14 MTU-verification ping. Quad9 was picked over Cloudflare for three reasons that matter for this specific role (secondary/fallback resolver behind Pi-hole, where Pi-hole handles the steady-state queries and the fallback only sees traffic when Pi-hole is quiesced or down): (1) Quad9 is operated by PCH out of Zurich, a privacy-friendlier jurisdiction with no advertising business behind it — Cloudflare's `1.1.1.1` has good stated policies but is run by an ad-adjacent CDN business and has been subject to repeated US-court-ordered DNS blocking; (2) Quad9's default service blocks known malware/phishing domains via threat-intel feeds, which is a meaningful belt-and-braces against the case where Pi-hole's gravity update fails silently or hasn't run after a long power-off; (3) Quad9 honors DNSSEC by default and returns SERVFAIL on validation failures rather than ignoring the chain. Latency cost vs Cloudflare is ~5–15 ms higher on average in EU, irrelevant when Pi-hole is the primary and the fallback only runs during the §12 backup-quiesce window. **One thing this changelog can't change automatically** — if you've already deployed the Kuma "Proton tunnel alive" monitor with `1.1.1.1` as the ping target, edit the monitor in Kuma's UI (Monitors → that monitor → Edit → Hostname/IP) and swap it to `9.9.9.9`; the doc's monitor list in §13 is the source of truth, but Kuma stores its own copy in its database. Same for any local scripts you've already deployed that hardcoded `1.1.1.1` — `grep -r 1.1.1.1 /opt/ /usr/local/bin/ ~/` on the Pi to catch any stragglers (fix #116)

> **Bug-fix changelog (v5.1.7.17):**
> - **Removed Nginx Proxy Manager entirely; replaced with Caddy as the reverse proxy + ACME client.** NPM was a persistent source of friction in this guide and the immediately-preceding version. The driving incompatibility is that NPM's Let's Encrypt UI is hardcoded against LE's directory — the project has rejected custom-ACME-server feature requests four times since 2021 (NPM #301, #1417, #3518, #4820) — so Step-CA integration required all of: fix #1 (SAN list manipulation), fix #3 (entrypoint override to keep the trust bundle from being wiped on container recreate), fix #14 (now-moot), fix #104 (s6-overlay PID-1 footgun that crash-looped the container after image bumps), fix #114 (acme.sh + per-proxy-host nginx Custom Configuration snippets carrying the ACME account thumbprint, plus a separate NPM-API deploy hook for cert upload). None of that machinery is needed with Caddy: `acme_ca https://step-ca:9000/acme/acme/directory` + `acme_ca_root /etc/ssl/certs/homelab-root-ca.crt` in the global block of a 30-line Caddyfile cover the entire flow, and Caddy validates the new config in-process on every `caddy reload` with atomic swap, so editing the file can't break a running deploy. Trade-off taken explicitly: no point-and-click proxy-host editor (the Caddyfile is the UI). The new §8 covers the Caddy stack and a full NPM-removal procedure (`docker stop npm`, drop the named volumes `npm-data`/`npm-ssl`, remove `/opt/npm`, uninstall any `~/.acme.sh` from the v5.1.7.16 detour, delete the `npm.home.arpa` Pi-hole record, and verify ports 80/443 are free with `ss -ltnp`). The old §8.5 (acme.sh + NPM deploy hook) was deleted in full — Caddy obsoletes every step in it. Pi-hole Local DNS records lose `npm.home.arpa`; §14 service URL table drops the NPM row and renames the column header to "Via Caddy"; §13 expected-containers list and stack-status table drop the `npm` row and add `caddy`; §12 backup `STOP_LIST` swaps `npm` for `caddy` and the documented contents of the named volumes update accordingly (`/data` holds the ACME account + issued certs, re-issuable but losing it forces full re-registration with Step-CA). All inline "reach via NPM" comments on Pi-hole / Step-CA / Kuma admin-port bindings updated to "reach via Caddy" — the loopback-binding pattern is unchanged, only the proxy-name. The doc adds a Caddy-specific HA caveat that wasn't documented for NPM either: HA needs `http.use_x_forwarded_for: true` + `trusted_proxies: [172.31.0.0/24, 127.0.0.1, ::1]` in `configuration.yaml` so the auth log records real client IPs instead of Caddy's bridge IP and the IP-based ban-list doesn't immediately ban the proxy. Historical fixes #1, #3, #14, #104, #114 stay in the bug-history table at the bottom as audit trail of how the previous reverse-proxy choice broke — they're cited from the new §8 prose so future-me can see at a glance why the migration happened. Image pin: `caddy:2.8.4-alpine` (fix #115)

> **Bug-fix changelog (v5.1.7.16):**
> - §8 NPM cert workflow + new §8.5 "Step-CA cert issuance via acme.sh": replaced the long-standing-wrong instruction "register an ACME provider in NPM pointing at the Step-CA directory URL" with a full working flow. NPM does not, and has never, supported custom ACME servers — its Let's Encrypt UI is hardcoded against LE's directory, and the project has rejected the feature request four separate times since 2021 (NPM #301, #1417, #3518, #4820). The doc's documented path didn't have a corresponding UI panel to click. New §8.5 covers the actual workable approach: `acme.sh` installed on the host runs as the ACME client, registers with Step-CA's directory at `https://127.0.0.1:9000/acme/acme/directory` (Step-CA's port-9000 publish is loopback-only) using `/opt/step-ca/homelab-root-ca.crt` as the trust bundle, uses `--stateless` mode so NPM itself serves the HTTP-01 challenge response via a one-time per-proxy-host Custom Nginx Configuration snippet (`location ~ "^/.well-known/acme-challenge/(.+)$" { return 200 "$1.<THUMBPRINT>"; }`), and pushes the issued cert into NPM as a Custom certificate via `acme.sh`'s built-in `nginx_proxy_manager` deploy hook (which talks to NPM's REST API at `http://127.0.0.1:81/api`). Step-CA's ACME provisioner is bumped from the 24h default to 30 days (`step ca provisioner update acme --x509-default-dur 720h --x509-max-dur 720h`) so the daily `acme.sh --cron` renewal cycle is reasonable rather than running every 16 hours. Renewal cron is wrapped to source NPM API creds from a 600-mode `~/.acme.sh/data/npm-creds` file so the deploy hook fires unattended without putting the password in the more widely-sourced `~/.acme.sh/account.conf`. Also fixed the §7 "Get root cert + ACME URL" paragraph that previously said "Save it for NPM" — the URL is for `acme.sh` on the host, not NPM, and the comment in the `cp` block was updated to reflect that NPM mounts the root cert to validate Step-CA's TLS during proxy operations (which is still load-bearing) but no longer for ACME (which `acme.sh` handles separately). This is a workflow fix, not just documentation: the entire ACME pipeline described in earlier revisions of the guide never had a UI control corresponding to "register ACME provider in NPM" — anyone following the doc would have hit the dead end the user did. Fix #111 (Docker daemon DNS pointing at Pi-hole) remains load-bearing here: Step-CA's HTTP-01 validator queries DNS from inside the container, so it needs Pi-hole reachability to resolve `*.home.arpa` to `192.168.70.5` and reach NPM (fix #114)

> **Bug-fix changelog (v5.1.7.15):**
> - §3 `docker-socket-proxy` `docker run` (**corrects fix #112**): dropped `--read-only` and the `--tmpfs /usr/local/etc/haproxy` mount that v5.1.7.14 added. v5.1.7.14 swapped one failure mode for another: the tmpfs mount made the entrypoint's write succeed but masked the image-shipped `/usr/local/etc/haproxy/haproxy.cfg.template` (the file the entrypoint `sed`s to generate the final config), so the entrypoint then failed at the *read* step with `sed: /usr/local/etc/haproxy/haproxy.cfg.template: No such file or directory` and the container still restart-looped. The upstream Dockerfile confirms the template-in-same-dir layout (`COPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg.template`); there is no clean way to keep `--read-only` because the directory must simultaneously be writable (for the generated config) and contain the image-shipped template (for sed to read), and Docker tmpfs mounts cannot be pre-seeded from the image. Tecnativa's own README examples run this container without `--read-only`, so dropping the flag matches the image's intended runtime model. Added `--security-opt=no-new-privileges` in its place — it prevents any process inside the container from gaining new capabilities via setuid binaries, which is a more useful hardening for this specific container than `--read-only` would have been. The Docker socket stays `:ro`, the API surface is still restricted by the env-var allowlist, and the proxy container is still firewalled from the LAN by the §3 DOCKER-USER rules, so the net security posture vs. v5.1.7.13-and-prior is essentially unchanged (fix #113)

> **Bug-fix changelog (v5.1.7.14):**
> - §3 `docker-socket-proxy` `docker run`: added `--tmpfs /usr/local/etc/haproxy:rw,nosuid,size=64k`. `tecnativa/docker-socket-proxy:0.3.0` (the version this guide pins to) is the HAProxy-based rewrite — its entrypoint *generates* `/usr/local/etc/haproxy/haproxy.cfg` from the `CONTAINERS=1`/`IMAGES=1`/`EXEC=0`/etc. environment variables at container startup, then `exec`s HAProxy with that config. Older `0.1.x` tags baked the config into the image at build time, which is why no prior version of this guide needed a writable mount and why the `--read-only` flag worked there. With `0.3.0` + `--read-only` the entrypoint hits `can't create /usr/local/etc/haproxy/haproxy.cfg: Read-only file system` at line 18, exits non-zero, the container restart-loops, and Portainer (which is configured with `DOCKER_HOST=tcp://docker-socket-proxy:2375`) then fails to start its environment with `Cannot connect to the Docker daemon at tcp://docker-socket-proxy:2375` — the user-visible symptom that surfaces the underlying bug. Mounting an in-memory tmpfs over only the haproxy config directory preserves the read-only-root hardening for the rest of the container while giving the entrypoint the writable path it needs. 64 KiB is well above the few-KiB generated config; `nosuid` removes a setuid-escalation path inside the tmpfs. Confirm with `docker ps | grep socket-proxy` showing `Up …` (not `Restarting`) and `docker logs docker-socket-proxy` showing HAProxy worker-fork messages rather than the read-only filesystem errors (fix #112)

> **Bug-fix changelog (v5.1.7.13):**
> - **Shortened all FQDNs from `*.berrypi5.home.arpa` to `*.home.arpa`.** `home.arpa` is itself the RFC 8375 zone for home-network use; service names live as direct children of that zone (`ha.home.arpa`, `portainer.home.arpa`, etc.), which is the canonical form and one label shorter. NPM accepts subdomains of `home.arpa` the same way it accepts `mycompany.co.uk` — `home.arpa` is on the PSL via its `.arpa` parent, so an `eTLD+1` like `ha.home.arpa` validates cleanly. Updated all six proxy host entries, all six Pi-hole Local DNS records, the Step-CA SAN list, the Kuma monitor list, the §14 service URL table, the cert-error troubleshooting row, and every prose reference. The bare `berrypi5` hostname (host identity, not a domain pattern) and `berrypi5-backup` (B2 bucket name) are untouched
> - §3 `daemon.json`: added `"dns": ["192.168.70.5", "9.9.9.9"]`. Without an explicit `dns:` key, Docker reads the host's `/etc/resolv.conf`, filters out loopback entries (containers can't reach the host's `127.0.0.1`), and uses only `9.9.9.9` as the upstream resolver for every container. Pi-hole is bypassed entirely from inside containers, and queries for `*.home.arpa` hit `9.9.9.9` and return `NXDOMAIN`. The visible failure mode is that Step-CA's ACME HTTP-01 validation never succeeds: Step-CA cannot resolve `ha.home.arpa` (or any other proxy host) when it tries to GET the challenge URL, so NPM never receives a cert and the doc's documented Step-CA ACME path silently doesn't work on first deployment. Pointing every container at Pi-hole via the host's LAN IP (`192.168.70.5`, where Pi-hole publishes `0.0.0.0:53`) makes `*.home.arpa` resolvable from inside any container, unblocks ACME HTTP-01, and gives Pi-hole visibility into container DNS for ad-blocking and logging. `9.9.9.9` stays in second position as a fallback so external resolution still works during the window Pi-hole is quiesced for the §12 backup. Pi-hole's existing `FTLCONF_dns_listeningMode: "ALL"` (§6) already allows it to answer queries arriving from container bridge subnets, so no Pi-hole-side change is required (fix #111)

> **Bug-fix changelog (v5.1.7.12):**
> - **Domain change `berrypi5.lan` → `berrypi5.home.arpa` everywhere.** NPM 2.10+ validates proxy host domain names against the Public Suffix List (via the `psl` library); `.lan` is not on the PSL and recent NPM releases reject it at the "Add Proxy Host" save step with "Domain name is not valid". `home.arpa` is the RFC 8375-reserved TLD for home networks (a real `.arpa` subdomain that IS on the PSL), so NPM accepts it without complaint. Updated all six proxy host entries in §8, the Pi-hole Local DNS records table in §6, the Step-CA `DOCKER_STEPCA_INIT_DNS_NAMES` SAN list in §7, the Kuma monitor list and §14 service URL table, the cert-error troubleshooting row, and every prose mention in §2/§4/§14. The bare `berrypi5` hostname (used by `hostnamectl`, `/etc/hosts`, the Step-CA provisioner name `admin@berrypi5`, the `berrypi5-backup` B2 bucket, and the Telegram alert text) is unchanged — those aren't FQDNs and don't go through NPM
> - §3 `docker-user-rules.sh` IPv6 block: switched `ip6tables -F DOCKER-USER` to `ip6tables -N DOCKER-USER 2>/dev/null || ip6tables -F DOCKER-USER`. Contrary to the earlier comment in the script, Docker does NOT auto-create the DOCKER-USER chain on ip6tables — it only manages ip6tables (and creates the chain on it) when `"ip6tables": true` is set in `/etc/docker/daemon.json`, which this guide does not enable by default. On stock config the chain doesn't exist, `ip6tables -F DOCKER-USER` fails with "No chain by that name", `set -e` aborts the script, and the IPv6 lockdown rules never get applied. The IPv4 rules above happen to apply because they come first, so `iptables -nvL DOCKER-USER` looks healthy in casual checks — only `systemctl status docker-user-rules` reveals the failure. The create-or-flush pattern (same idiom §4 already uses for `PROTON_KS`) makes the script idempotent regardless of whether Docker auto-created the chain or not. Also expanded the comment to document that these rules are dormant on the default v4-only Docker config and what to add to `daemon.json` if you ever turn on Docker v6 (fix #108)
> - §13 `homelab-health-push.sh`: added explicit `PATH=/usr/bin:/bin:/usr/sbin:/sbin` near the top of the script. Cron's default PATH for `/etc/cron.d/` jobs is `/usr/bin:/bin` — it does NOT include `/usr/sbin`, where `smartctl` lives on Ubuntu 24.04. Without an explicit PATH, the bare `smartctl -A` call silently failed under cron with "command not found", `$SMART` came back empty, `awk` parsing produced nothing, the `: "${WEAR:=100}"` default kicked in, and the SMART monitor reported "down" (wear 100% > 80% threshold) on EVERY push — a permanent false alarm with no obvious cause. Worst part: manual testing via `sudo /usr/local/bin/homelab-health-push.sh` masks the bug entirely because sudo's `secure_path` includes `/usr/sbin`. Same class of bug as the cron `root` field one §13 already documents (fix #109)
> - §5 wg0 client config: removed `fd00:10:10::1` from the client `DNS = ` line. Pi-hole's container only binds port 53 on IPv4 (Docker doesn't manage ip6tables unless `"ip6tables": true` is enabled — same root cause as fix #108), so nothing on the Pi actually listens on `[fd00:10:10::1]:53`. v6-first clients send the first DNS query to the v6 server, time out, then fall back to v4 — adding latency on every first lookup and producing the occasional "DNS feels slow on WireGuard" report. The earlier comment defending the v6 DNS entry ("IPv6-first OSes will bypass Pi-hole if only a v4 DNS is listed") was a misconception: WireGuard clients pin the resolver in the tunnel profile, so the OS sends ALL DNS (A and AAAA queries) to the configured server(s) regardless of network preference; with `AllowedIPs = 0.0.0.0/0, ::/0` no DNS leaks out of the tunnel. Updated the comment to document this and to note that the v6 DNS entry can be re-added if Docker IPv6 is later enabled and Pi-hole is exposed on v6 (fix #110)

> **Bug-fix changelog (v5.1.7.11):**
> - §4 `protonvpn-up.sh` kill switch: added `iptables -A PROTON_KS -d 172.16.0.0/12 -j RETURN` before the final `REJECT`. Without it, host→container traffic over Docker bridges is rejected by the kill switch: the host's own DNS queries (resolv.conf → `127.0.0.1:53` → docker-proxy → Pi-hole container at `172.30.0.x`), `curl 127.0.0.1:9443` to Portainer, `curl 127.0.0.1:3001` to Kuma from the health-push script, etc. all carry a destination of a *container* IP, which is not a LOCAL address (so the `ADDRTYPE LOCAL` RETURN doesn't catch it) and not in the LAN/wg0 ranges — so it falls through to `REJECT`. Same class as fix #58, which added `-s 127.0.0.0/8` to `DOCKER-USER` for the host-loopback *source* direction; this is the host→container *destination* direction in `PROTON_KS`. Symptom: after §4, Portainer/Pi-hole admin and the Pi's own DNS all break; `systemctl stop wg-quick@protonvpn` makes them work again because that tears the chain down. `protonvpn-down.sh` needs no edit — it flushes the whole chain (fix #103)
> - §8 NPM `entrypoint:`: changed `update-ca-certificates && /init` to `update-ca-certificates && exec /init`. Without `exec`, `/bin/sh` stays as PID 1 and `/init` runs as its child; NPM's s6-overlay base image hard-checks `getpid() == 1` in `s6-overlay-suexec` and aborts with `fatal: can only run as pid 1`, so the container crash-loops forever (the cert-update line prints once per restart, masking the loop on a casual log glance). `exec` replaces the shell process so `/init` inherits PID 1. Fix #3 introduced the entrypoint override with the right intent but dropped `exec`; `jc21/nginx-proxy-manager:2.12.3` ships s6-overlay v3.x which enforces the PID 1 check strictly (fix #104)
> - §8 SSH tunnel example: changed `ssh -L 81:127.0.0.1:81` to `ssh -L 8081:127.0.0.1:81`. Port 81 is privileged (<1024); binding it on the *client* side fails with `bind: Permission denied` for any non-root user on macOS/Linux. The forwarded-to port on the Pi stays `81` (that's where NPM's admin UI listens); only the local listen-port changes. Same pattern §6 already uses correctly with `8080:127.0.0.1:8080`. Access URL updated to `http://127.0.0.1:8081` to match (fix #105)
> - §2 UFW + §10 + §15: added `ufw allow` rules for port 8123. Home Assistant runs `network_mode: host`, binding directly to `0.0.0.0:8123` on the Pi — it is NOT behind Docker's port-publishing NAT, so Docker adds no iptables rules for it and UFW's `default deny incoming` drops every packet to 8123. The §2 rule set never opened the port, yet §10 says "Access `http://192.168.70.5:8123` and onboard" and §14 claimed 8123 "remains reachable from the whole LAN" — both false as written. Worse, NPM (a container on `172.31.x.x`) forwarding `ha.home.arpa` to `192.168.70.5:8123` is also dropped, so the HA proxy host 504s. Added `ufw allow from 172.16.0.0/12 to any port 8123` (NPM→HA, required) and `ufw allow from 192.168.68.0/22 to any port 8123` (LAN-direct, for the §10 onboarding step) to §2; updated the §14 deny-to-restrict note to use `ufw insert 1` so the deny precedes the allow (fix #106)
> - §6 Pi-hole `FTLCONF_dns_upstreams`: changed `172.30.0.2#5335` to `172.30.0.2` and corrected the surrounding comment and the §6 troubleshooting callout. The `#5335` port convention comes from *bare-metal* Pi-hole + Unbound setups, where both run on the host and Unbound must listen on a non-53 port to avoid colliding with Pi-hole's own `:53`. In this guide Unbound runs in its own container with its own IP (`172.30.0.2`) and its own port namespace — the `mvance/unbound-rpi` image listens on **port 53** by default, so `172.30.0.2#5335` pointed Pi-hole at a port nothing was listening on and upstream resolution silently failed (no internet via Pi-hole). Dropping the `#5335` lets FTL default to port 53, which is where Unbound actually is. The stale comment ("Pi-hole v6 keeps the v5 #port separator") and the troubleshooting callout's `["172.30.0.2#5335"]` / `172.30.0.2:5335` references were corrected to match (fix #107)

> **Bug-fix changelog (v5.1.7.10):**
> - §7 Step-CA CLI fallback: regression introduced by fix #92 — the Portainer-path instructions correctly tell the user to set `DOCKER_STEPCA_INIT_PASSWORD` in the stack's env-vars panel, but the immediately-adjacent CLI fallback (`cd /opt/step-ca && docker compose up -d`) silently ignored the password requirement; a user following the CLI path would get the random-generated-and-logged behaviour back (the very thing fix #92 set out to eliminate). Patched the CLI fallback to pass `DOCKER_STEPCA_INIT_PASSWORD='...'` inline, matching the pattern used by the Pi-hole `dns` stack's CLI fallback (fix #101)
> - §13 Watchtower CLI fallback: pre-existing same-class bug — the prose tells the user to set `WATCHTOWER_NOTIFICATION_URL` in the Portainer env-vars panel, but the CLI fallback (`cd /opt/watchtower && docker compose up -d`) didn't pass it inline, so a user following the CLI path would deploy Watchtower with notifications silently disabled and the Sunday update schedule would fire without any Telegram alerts. Patched the CLI fallback to pass `WATCHTOWER_NOTIFICATION_URL='telegram://<token>@telegram?chats=<chat-id>'` inline with a placeholder format (fix #102)

> **Bug-fix changelog (v5.1.7.9):**
> - §13 kill-switch test: replaced `systemctl stop wg-quick@protonvpn` with `ip link set protonvpn down` — the systemctl approach runs `protonvpn-down.sh` (the wg-quick PreDown hook), which removes the `PROTON_KS` chain from `OUTPUT` before the verification curl runs; the curl then succeeds (route falls back to the ISP), making the entire block a "did wg-quick clean up correctly?" test rather than a "does the kill switch hold when the tunnel drops?" test. `ip link set` drops the interface without invoking PreDown, leaving the chain loaded so the curl can actually be blocked by it. Recovery is now `systemctl restart wg-quick@protonvpn` (handshake state needs a full restart, not just `ip link set up`) (fix #95)
> - §14 MTU verification + breakage table: aligned both spots with fix #82's IPv6-minimum constraint — the verification prose said "(or to 1240 as a conservative floor)" and the breakage table said "1240 is a safe conservative value" without acknowledging that fix #82 (in §4) established 1280 as the absolute floor for retaining IPv6 on wg0; dropping below 1280 sacrifices v6 on wg0. Rewrote both as an explicit trade-off ("v4-only on wg0 in exchange for no fragmentation") so the user can choose knowingly (fix #96)
> - §3 `docker-user-rules.sh` comment: corrected the claim that "NPM's 80/443 are unaffected — those match the RELATED,ESTABLISHED RETURN first" — RELATED,ESTABLISHED only matches reply traffic in a connection that's already been allowed; the *initial* SYN from a LAN client to NPM 80/443 matches the LAN-source RETURN (`-s 192.168.68.0/22`). Reply packets in the same connection then match RELATED,ESTABLISHED. Both rules are needed; neither alone is sufficient. Rewrote the comment to describe both directions correctly (fix #97)
> - §13 router-config table + new ⚠️ note: the rows for "optional 80/TCP and 443/TCP port forwards" implied a router-side toggle was sufficient to publicly expose NPM, but DOCKER-USER drops WAN-sourced packets to containers — the source IP (external client) doesn't match any of the `-j RETURN` rules, the final `-j DROP` applies, and the public connection silently fails. Added a footnote under the table explaining the trade-off and showing the additional `iptables -A DOCKER-USER -p tcp -m multiport --dports 80,443 -j RETURN` rule that would be needed in `docker-user-rules.sh` if the user actually wants public NPM exposure (and the auth-strength implications that come with it) (fix #98)
> - §3 "What cannot be a Portainer stack" list: added `docker-socket-proxy` — the list documented Portainer, wg0, ProtonVPN, and Restic as the four non-stack components, but docker-socket-proxy is also a non-stack `docker run` (deployed in §3 above Portainer for the same chicken-and-egg reason: Portainer's `DOCKER_HOST` env var targets the proxy and needs it running first). Now listed alongside Portainer with the rationale (fix #99)
> - §8 TOC entry: removed misleading "+ local DNS records" suffix — the local-DNS-records subsection (Pi-hole admin → Local DNS → DNS Records) lives in §6, not §8. The TOC entry was a leftover from an earlier doc structure that has since shifted the DNS records to where they actually run (against Pi-hole) (fix #100)

> **Bug-fix changelog (v5.1.7.8):**
> - §7 Step-CA provisioner password: switched from "let Step-CA generate a random password and grep it out of `docker logs step-ca`" to "set `DOCKER_STEPCA_INIT_PASSWORD` in the Portainer stack's env-vars panel before first deploy" — the log-extraction approach is fragile because the log line is printed exactly once and Docker's default `json-file` driver with `max-size=10m, max-file=3` (per `daemon.json`) can age it out within hours; users who miss the window have no recovery short of destroying the `step-ca-data` volume and re-initialising the CA (which forces re-installing the new root cert on every device). Same pattern Pi-hole already uses for `FTLCONF_webserver_api_password`. Updated the YAML comment, the surrounding callout, and added historical context noting why the legacy approach existed (fix #92)
> - §12 restic backup paths + restore drill + §14 git list: added `/etc/apt/apt.conf.d/50unattended-upgrades` — §2 modifies this file to set `Unattended-Upgrade::Automatic-Reboot "true"` and `Unattended-Upgrade::Automatic-Reboot-Time "02:00"` (so security updates reboot the Pi at a sane hour), but the file was never in the backup paths, restore drill, or "what to put in git" list; a restore would silently land with the default package config and lose the customised reboot window. Updated the drill prose count from "six" to "seven config paths" (fix #93)
> - §12 setup: pre-pull `alpine:3.21` during initial restic setup — the backup script's volume-tarball loop runs `docker run --rm -v "$vol":/src -v "$STAGING":/dst alpine:3.21 tar czf ...`; if `alpine:3.21` is not in the local Docker cache when the first scheduled 04:00 backup fires and ProtonVPN is down at that moment (kill switch blocks egress), the pull fails, `set -euo pipefail` aborts the script, the `OnFailure` unit fires a Telegram alert, and no backup completes. Pulling once during setup (with the tunnel known-up) caches the image; the pin prevents Watchtower from pruning it (fix #94)

> **Bug-fix changelog (v5.1.7.7):**
> - Top-of-doc revision-notes chain: deleted. Every `**Revision notes vs vX:**` line was a one-liner pointer of the form "N bugs fixed (see vY changelog below)", adding nothing the corresponding changelog block right below it didn't already say in more detail. The chain grew by one entry per release and had become pure bloat. Fixes #81 (added missing v5.1.7.2 line) and #84 (added missing v5 + v5.1 lines) were correctly applied to the doc state at the time; the text they edited is now gone wholesale, but their numbered fix entries remain in the historical changelog as written (fix #91)

> **Bug-fix changelog (v5.1.7.6):**
> - Revision notes header: added missing `Revision notes vs v5:` and `Revision notes vs v5.1:` lines between the `vs v4.1` and `vs v5.1.3` entries — both v5.1 (changelog block with 23 fixes #9–#31) and v5.1.3 (changelog block with 15 fixes #32–#46) were real releases with their own blockquote changelogs and summary tables, but the top-of-doc chain of revision notes jumped straight from "vs v4.1" → "vs v5.1.3" with no headers describing what changed in v5.1 (vs v5) or v5.1.3 (vs v5.1); fix #81's claim that "every other version in the chain has a corresponding header" was therefore inaccurate when applied to the broader chain (fix #84)
> - Changelog formatting: removed two extra blank lines between the v5.1.7.4 and v5.1.7.3 changelog sections — three consecutive blank lines had been introduced when the v5.1.7.4 changelog block was inserted in v5.1.7.4 and survived through v5.1.7.5; only a single blank line is used as a section separator everywhere else in the changelogs (same class of bug as fix #75 fixed for v5.1.4/v5.1.3) (fix #85)
> - §12 backup script trap comment: updated the prose list of services that would otherwise be left stopped to include `mosquitto` — the comment listed "Pi-hole, HA, NPM, Portainer, and Kuma" (5 services) but `STOP_LIST` has had `mosquitto` in it since fix #56 (v5.1.6), giving 6 services; same class of doc-lag-behind-code bug as fix #48 and fix #79 (fix #86)
> - §10 Mosquitto bind mount: removed `:ro` from the `mosquitto.passwd` mount and added a pre-deploy `touch` step — the existing instructions tell the user to populate the password file via `docker exec -it mosquitto mosquitto_passwd -c /mosquitto/config/mosquitto.passwd <user>`, which is a write operation that fails with EACCES on a read-only mount; additionally, without a pre-deploy `touch`, Docker auto-creates the bind-mount source as a *directory* on first deploy, causing Mosquitto's config parse to fail (same class as fix #44 fixed for relative paths) (fix #87)
> - §3 directory mkdir: added `portainer` to the brace expansion in `mkdir -p /opt/{...}` — the §14 directory tree showed `/opt/portainer/` (with a "no compose file — bootstrapped via docker run" note) but `/opt/portainer` was never actually created on disk because it was missing from the `mkdir` line; either the directory had to exist or the §14 tree had to drop the row — chose the former to match the existing §14 documentation (fix #88)
> - §3 DOCKER-USER prose: corrected "binding admin ports to `127.0.0.1`, which we do from §6 onward" → "from §3 onward" — Portainer's own `docker run` in §3 already binds to `127.0.0.1:9443:9443`, so the loopback-binding pattern starts in §3, not §6; the prose lagged the code (fix #89)
> - §13 health push script: replaced `[ "$CRIT" = "0x00" ]` with `[ "$((CRIT))" -eq 0 ]` — the strict string match flagged a healthy drive as critical whenever `smartctl` emitted the Critical Warning value as bare `0` instead of `0x00` (which it does on some smartmontools versions, depending on output style); arithmetic expansion normalizes both `0` and `0x00` (and any other hex value) to an integer, so a real critical warning still produces a non-zero result and the comparison still flips the monitor to `down` (fix #90)

> **Bug-fix changelog (v5.1.7.5):**
> - Revision notes header: added missing `Revision notes vs v5.1.7.2:` line between the `vs v5.1.7.1` and `vs v5.1.7.3` entries — v5.1.7.3 was a released version with its own changelog block and summary table, but the top-of-doc chain of revision notes jumped straight from v5.1.7.1 to v5.1.7.3, with no header describing what changed in v5.1.7.3 vs v5.1.7.2; every other version in the chain has a corresponding header (fix #81)
> - §4 `protonvpn.conf` MTU comment: rewrote the math/rationale paragraph — fix #72 added a comment that asserted "keeping wg0 below 1320 - 60 = 1260 prevents the stacked packet from exceeding 1320 and causing fragmentation" and then closed with "1280 is the safe floor (IPv6 minimum MTU)", silently contradicting itself since 1280 is *not* below 1260; the comment now states explicitly that strict no-fragmentation would need wg0 ≤ 1260, that 1280 is the IPv6 minimum below which IPv6 breaks on the interface, and that 1280 is therefore a deliberate trade-off (slight PMTU-discovery noise in exchange for keeping IPv6 working) (fix #82)
> - v5.1.7.3 changelog text + summary table: corrected the fix #76 entry's per-invocation arithmetic — the original wording said "all four `curl` calls" (correct count in the script) but then claimed "with three calls that is up to 6 minutes per invocation"; the script's `if/else` structure means exactly two calls fire per invocation (one of the SoC branches, one of the NVMe branches), so the worst-case stall is closer to ~4 minutes, not 6; same wording was mirrored in the v5.1.7.3 summary table near the end of the doc and was corrected there too (fix #83)

> **Bug-fix changelog (v5.1.7.4):**
> - §3 `docker-user-rules.sh`: added `ip6tables` DOCKER-USER chain rules to mirror the existing `iptables` block — containers that bind to `::` (IPv6 all-interfaces) were not covered by the IPv4-only rules, leaving the DOCKER-USER lockdown entirely ineffective for IPv6; added `RELATED,ESTABLISHED`, `wg0`, ULA (`fc00::/7`), and loopback (`::1/128`) RETURN rules followed by DROP; also updated the post-install verification command to check both `iptables` and `ip6tables` chains (fix #77)
> - §12 `homelab-backup-notify@.service`: added `--max-time 10` to the Telegram `curl` call — fix #76 added timeouts to the health push script but the notify service had the identical problem; an unreachable `api.telegram.org` causes the notify unit to hang indefinitely, blocking systemd's failure-handling path (fix #78)
> - §12 Restore drill: added `/etc/ssh` restore and `ls` verification step — `/etc/ssh` (including `sshd_config.d/99-hardening.conf`) is backed up by the restic invocation but was never included in the drill; updated the prose count from \"five\" to \"six\" config paths (fix #79)
> - §13 Health push script: removed stale `FIX #49` comment from the sysfs-unreadable `else` branch — the comment explained that `--cacert` is unnecessary on plain HTTP, which is true of the main code path but irrelevant inside the error branch; the correct explanation belongs on the `KUMA_BASE` declaration, where it already appears (fix #80)

> **Bug-fix changelog (v5.1.7.3):**
> - §5.1 changelog: added missing fix #24 entry — fix #24 (removing `-k` from the §13 functional test `curl` call) appeared in the v5.1 summary table and was correctly applied to the document, but was never logged in the v5.1 changelog text, leaving a gap between #23 and #25; the summary also claimed "23 new fixes" while the changelog only listed 22 (fix #73)
> - Changelog headers: added missing `v5 bug-fix summary` section — the revision notes for v4 and v4.1 both reference "see v5 bug-fix changelog below" but no such section existed; the five structural changes made in the v5 rewrite had no corresponding changelog entry, leaving two broken cross-references (fix #74)
> - Changelog formatting: removed two extra blank lines between the v5.1.4 and v5.1.3 changelog sections — three consecutive blank lines had survived since fix #31 (which removed a double blank line elsewhere); only a single blank line is used as a section separator everywhere else in the changelogs (fix #75)
> - §13 Health push script: added `--max-time 5` to all four `curl` calls — the script runs every 60 seconds via cron; without a timeout, a temporarily unresponsive Kuma causes each `curl` to block for curl's default connect timeout (~2 minutes per call); the script's `if/else` structure means exactly two calls fire per invocation (one of the SoC branches, one of the NVMe branches), giving up to ~4 minutes per invocation; successive cron firings then pile up processes that do not resolve until Kuma recovers (fix #76)

> **Bug-fix changelog (v5.1.7.2):**
> - §12 `v5.1.7.1 bug-fix summary` table: corrected "4 new fixes" → "7 new fixes" — the table lists fixes #62–#68 (seven entries) and the revision header on line 15 also says "seven", but the summary table header was never updated from an earlier draft count (fix #69)
> - §12 `homelab-backup-notify@.service`: added `After=network-online.target` and `Wants=network-online.target` — a backup failure that occurs very early at boot (before the network stack is ready) causes the `curl` to `api.telegram.org` to fail with a connection error; the failure is swallowed silently and no Telegram notification is sent (fix #70)
> - §12 Restore drill: moved all five `ls` verification steps inside the `sudo bash -c` block — running them outside as the `pi` user means they execute even if a restore failed early and left the target dir empty or partial; since `/tmp` is world-readable, `ls` on a non-existent or empty path would appear to succeed, giving false confidence (fix #71)
> - §4 `protonvpn.conf` MTU comment: added explanation that 1320 is ProtonVPN's server-imposed ceiling, why it differs from wg0's 1280 (stacked encapsulation overhead), and what to do if the ISP path MTU is below 1320 (PPPoE links) — previously the value appeared with no comment while wg0's MTU had a detailed explanation, leaving readers without context on the relationship between the two values (fix #72)

> **Bug-fix changelog (v5.1.7.1):**
> - §5 wg0 server config: lowered `MTU` from `1320` to `1280` — at 1320 the wg0 encapsulation overhead (~60 B) pushes packets past protonvpn's own 1320-byte MTU, causing fragmentation or silent large-transfer stalls; 1280 is the IPv6 minimum MTU and the safe floor for a wg0-inside-protonvpn stack (fix #62)
> - §5 wg0 client config: added `fd00:10:10::1` to the `DNS` field and aligned client `MTU` to `1280` — with `AllowedIPs = ::/0`, all IPv6 traffic routes through the tunnel; IPv6-first OSes (iOS, Android, macOS) attempt DNS over IPv6 and bypass Pi-hole entirely if only the IPv4 address is listed, leaking DNS to the carrier resolver (fix #63)
> - §12 Backup script: added `/etc/cloud/cloud.cfg.d` to the restic backup paths — fix #41 added the cloud-init network-management disable step but its config file was never backed up; a restic-only restore loses it, causing cloud-init to overwrite `50-cloud-init.yaml` with DHCP on the next reboot (fix #64)
> - §13 Health push script: added `else` branch to the NVMe device check — when `$NVME_DEV` doesn't exist (wrong path, USB SSD, forgotten update) no push was sent; Kuma's push monitor heartbeat expired silently and showed "down" with no message, indistinguishable from a real SMART failure; now pushes `status=down` with a clear "not found" message (fix #65)
> - §14 MTU verification: corrected stale description — fix #62 set wg0 to MTU 1280 but the §14 prose still said "both tunnels are MTU 1320"; updated the ping probe range and the threshold guidance to match the new values; also corrected the troubleshooting table row that still said "lower MTU to 1280" (fix #66)
> - §12 `homelab-backup.service`: added `Requires=docker.service` — `After=` alone only orders startup; if Docker is manually stopped, the backup fires at 04:00, `docker volume ls` returns nothing, the volume-tarball loop produces no files, and restic completes successfully with only `/opt` and config files — a silent partial backup with a green exit code and no notification (fix #67)
> - §12 Restore drill: added `/etc/cloud/cloud.cfg.d` restore and `ls` step — fix #64 added this path to the backup but the drill was never updated; a drill that doesn't verify the cloud-init disable file gives false confidence that a restore will land with static IP intact (fix #68)

> **Bug-fix changelog (v5.1.7):**
> - §13 Health push script: removed stale `--cacert /opt/step-ca/homelab-root-ca.crt` from all three `curl` calls — fix #49 changed `KUMA_BASE` to `http://127.0.0.1` (plain HTTP); curl silently ignores `--cacert` on plain HTTP connections; the flag was dead code and its TLS/MITM rationale no longer applies to a loopback call (fix #57)
> - §3 DOCKER-USER chain: added `iptables -A DOCKER-USER -s 127.0.0.0/8 -j RETURN` before the DROP — host-to-container traffic on loopback (health push to `127.0.0.1:3001`, `docker run` calls in the backup volume loop) has source `127.x.x.x` which is not matched by the `172.16.0.0/12` inter-container rule and was silently DROP'd (fix #58)
> - §10 Mosquitto: corrected port binding comment — port is bound to `192.168.70.5:1883` (LAN interface only); nothing listens on `127.0.0.1:1883`; HA must connect to `192.168.70.5`, not `localhost` (fix #59)
> - §2 Unattended upgrades: changed `Automatic-Reboot-Time` from `03:00` to `02:00` and added note explaining the conflict — the backup timer runs at `04:00` with `Persistent=true`; a reboot finishing close to 04:00 can trigger the backup before containers are healthy; 02:00 provides a clean two-hour margin (fix #60)
> - §14 gitleaks: replaced `pip install --user pre-commit` with `pipx install pre-commit` — Ubuntu 24.04 enforces PEP 668 and `pip install` outside a virtual environment exits with "externally-managed-environment"; `pipx` is the Ubuntu-recommended approach and handles its own isolated environment (fix #61)

> **Bug-fix changelog (v5.1.6):**
> - §5 Client config: corrected `Address = 10.10.0.2/24, fd00:10:10::2/64` → `/32, /128` — using subnet masks on the client `Address` field tells the WireGuard interface it owns the entire subnet locally, causing the client to bypass the tunnel for peer-to-peer VPN traffic and potentially conflicting with the client device's routing table; host masks (`/32`, `/128`) are correct and consistent with the `AllowedIPs` in the server's `[Peer]` blocks (fix #52)
> - §12 `homelab-backup.service`: added `[Install]` section with `WantedBy=multi-user.target` — without it `systemctl enable homelab-backup.service` fails with "Unit file has no [Install] section"; the timer remains the correct activation path but the section prevents confusing errors during troubleshooting (fix #53)
> - §14 UFW deny note for HA port 8123: corrected wrong claim that "NPM reaches it via the host loopback" — NPM is a container on the `172.31.x.x` Docker bridge and reaches HA at `192.168.70.5:8123`; the conclusion (rule won't break NPM) was coincidentally correct but the stated reason was wrong (fix #54)
> - §12 Backup script: pinned `alpine` → `alpine:3.21` in the volume tar loop — the only unpinned image in the guide; an implicit `:latest` pull during a backup run could silently change behaviour on an Alpine major bump or fail if the registry is temporarily unavailable (fix #55)
> - §12 Backup script: added `mosquitto` to `STOP_LIST` — Mosquitto has an active broker writing to its data volume; listing it is safe unconditionally because `docker stop` is a no-op for containers that aren't running (fix #56)

> **Bug-fix changelog (v5.1.5):**
> - §13 Health push script: changed `KUMA_BASE` from `https://kuma.home.arpa/api/push` to `http://127.0.0.1:3001/api/push` — the NPM/DNS chain requires Pi-hole and NPM to be running; the loopback URL hits Kuma directly and keeps pushes working when either is down or quiesced during a backup run (fix #49)
> - §12 Backup script: changed `/etc/systemd/system/homelab-backup.service.d` (directory) to `/etc/systemd/system/homelab-backup.service.d/notify.conf` (explicit file) — all other systemd unit entries in the backup path list individual files; backing up the directory works but is inconsistent and could pick up unrelated drop-ins added by other packages (fix #50)
> - §14 Troubleshooting: added `cd /opt/<service> &&` to the Watchtower rollback fix — the `docker compose` commands require a compose file in the working directory; without the `cd`, the command fails silently with "no configuration file provided" if run from any other directory (fix #51)

> **Bug-fix changelog (v5.1.4):**
> - §12 Backup failure notifications: changed `OnFailure=homelab-backup-notify@%n.service` to `@%p.service` — `%n` expands to the full unit name including its `.service` suffix (`homelab-backup.service`), producing the invalid instance `homelab-backup-notify@homelab-backup.service.service` and silently failing to trigger the notification on backup failure (fix #47)
> - §12 Restore drill: corrected "three config dirs" to "four" — fix #35 added `/etc/sysctl.d` to the drill, making it four directories (wireguard, netplan, chrony, sysctl.d), but the prose description was never updated (fix #48)

> **Bug-fix changelog (v5.1.3):**
> - §12 Backup script: replaced `for vol in $(docker volume ls -q)` with `mapfile -t VOLUMES < <(docker volume ls -q)` + `for vol in "${VOLUMES[@]}"` — the original command word-splits on volume names containing spaces or special characters, silently skipping them (fix #32)
> - §3 daemon.json: changed `default-address-pools` base from `172.17.0.0/16` to `172.20.0.0/14` — `172.17.x` is Docker's own `docker0` bridge address; using it as the auto-allocation pool risks collisions with the pre-existing bridge on restart (fix #33)
> - §12 Kuma push monitors: added explicit note to set each Push monitor's heartbeat interval to ≥60s — the cron fires every 60s, and a shorter heartbeat causes false "down" alerts between pushes (fix #34)
> - §12 Restore drill: expanded to also restore and verify `/etc/netplan`, `/etc/chrony`, and `/etc/sysctl.d` — the original only tested `/etc/wireguard`, leaving critical config dirs unverified (fix #35)
> - §3 Portainer: moved the "no `-v /var/run/docker.sock`" explanation to a callout *before* the `docker run` command rather than a note after it — readers scanning the command block need the context before running it (fix #36)
> - §14 troubleshooting table: replaced `sudo ip rule flush` with targeted `ip rule del priority 50/51` — `ip rule flush` deletes kernel-default rules at priorities 0/32766/32767, breaking all routing until reboot (fix #37)
> - §8 NPM proxy hosts: added "Ignore Certificate" warning for `stepca.home.arpa` — Step-CA's backend is HTTPS with a cert that NPM may not automatically trust, same as Portainer; missing this causes a 502 (fix #38)
> - §12 Backup script: added `/etc/sysctl.d`, `/etc/cron.d`, `/usr/local/bin/homelab-*.sh`, `/usr/local/bin/docker-user-rules.sh`, and the homelab systemd unit files to the restic backup paths — previously only in git, leaving a restic-only restore incomplete (fix #39)
> - §2 Hostname: restored `::1 localhost` entries stripped by the original `echo` command — removing IPv6 loopback from `/etc/hosts` breaks IPv6 loopback resolution for Docker and some HA integrations (fix #40)
> - §2 Static IP: added `echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` step after `netplan apply` — without this cloud-init regenerates `50-cloud-init.yaml` on boot and reverts the Pi to DHCP, losing the static IP and breaking every dependent service (fix #41)
> - §10 Mosquitto: snippet was missing the top-level `volumes:` entries for `mosquitto-data` and `mosquitto-log`; without them `docker compose up` fails with "volume not declared"; also added note that HA reaches Mosquitto via localhost since both use host networking (fix #42)
> - §7 Step-CA: added `localhost` and `127.0.0.1` to `DOCKER_STEPCA_INIT_DNS_NAMES` — the guide directs bootstrap access via `https://127.0.0.1:9000` over SSH tunnel but the TLS cert lacked those SANs, causing x509 validation failure (fix #43)
> - §10 Mosquitto: changed relative bind-mount paths (`./mosquitto.conf`, `./mosquitto.passwd`) to absolute paths (`/opt/homeassistant/…`) — Portainer's web-editor working directory is `/`, so relative paths resolved to `/mosquitto.conf` and Docker created a directory instead of a file, causing Mosquitto to fail on config parse (fix #44)
> - §13 Health push script: removed `-k` (skip-TLS-verify) from all three `curl` calls and replaced with `--cacert /opt/step-ca/homelab-root-ca.crt` — `-k` silently disabled TLS verification on every push, making the calls susceptible to local MITM; the root CA is already on disk from §7 so no system-wide CA install is required (fix #45)
> - §12 Backup script: renamed `TMPDIR` variable to `STAGING` — `TMPDIR` is the POSIX standard env var that programs (including restic) consult when creating their own temp files; with the old name, restic wrote pack-assembly scratch into the staging dir and those files were included in every snapshot, inflating backup size (fix #46)

> **Bug-fix changelog (v5.1):**
> - §6 Pi-hole admin URL: replaced `http://192.168.70.5:8080/admin` (unreachable — port is loopback-only) with SSH tunnel instructions for pre-NPM access (fix #9)
> - §12 Backup script: added `TMPDIR` cleanup to the trap so a mid-run failure doesn't leave GB-sized volume tarballs in `/tmp/` indefinitely; also moved `TMPDIR=$(mktemp -d)` before the trap so the variable is always in scope when the trap fires (fix #10)
> - §2 systemd-resolved: removed stale "no chattr" from heading and intro sentence — the body correctly uses `chattr +i` after setup; heading was a carry-over from v1 (fix #11)
> - §12 restic init: moved admin-key warning to *before* the init steps and restructured the block so the write-only env file and admin-key init path are unambiguously separate (fix #12)
> - v4 changes summary: added Watchtower `1.7.1` to the image-pins table, which listed all other pinned images but omitted it (fix #13)
> - Header: corrected "Revision notes vs v5" → "vs v4.1" (fix #14)
> - §6 Pi-hole compose: corrected `FTLCONF_webserver_port: "8080o"` (invalid) → `"8080"` with explicit `FTLCONF_webserver_tls_port: "-1"` to disable container-level HTTPS (fix #15)
> - §12 Backup script: removed redundant `rm -rf "$TMPDIR"` after restic — the EXIT trap already handles cleanup on all paths; switched trap to double-quoted expansion to be safe under `set -u` (fix #16)
> - §3 + §14 Portainer: added `-e DOCKER_HOST=tcp://docker-socket-proxy:2375` to both the initial `docker run` and the update command in §15; updated first-run wizard note accordingly (fix #17)
> - §5 wg0.conf: clarified that ip6tables FORWARD rules are unconditional — comment previously implied they were optional like the MASQUERADE rule (fix #18)
> - §3 daemon.json: added `default-address-pools` to prevent Docker's auto-allocator colliding with the manually-pinned `proxy-net` (`172.31.0.0/24`) and `dns-net` (`172.30.0.0/24`) subnets (fix #19)
> - §2 + §6 systemd-resolved: moved `chattr +i /etc/resolv.conf` out of the §2 early-setup block (where it would block netplan/cloud-init) into a new deferred step at the end of §6 after Pi-hole is confirmed working (fix #20)
> - §10 Mosquitto: added warning that `mosquitto_passwd -c` overwrites the password file — must not be used when adding a second user (fix #21)
> - §3 Docker install: added warning that `newgrp docker` only affects the current shell; a fresh login is needed before running `docker` commands without `sudo` in other terminals (fix #22)
> - §11 DDNS: fixed typo "fastback-up" → "fallback" (fix #23)
> - §13 Functional tests: removed `-k` from `curl -k https://ha.home.arpa` — `-k` suppresses TLS errors, defeating the entire point of the test (verifying the root CA is trusted on the client); added inline comment explaining the check is intentionally strict (fix #24)
> - §9 gateway table: renamed "Option C" → "Option B" — the table jumped from A to C after an earlier edit removed Option B (fix #25)
> - §14 Ubuntu gotchas: updated `chattr +i` cross-reference from "(see §2)" → "(see §6)" following fix #20 (fix #26)
> - §12 restore drill: added `sudo bash -c '...'` wrapper — `/root/.restic-env` is `chmod 600` root-only; running `source` without sudo gives "Permission denied" for the `pi` user (fix #27)
> - §14 troubleshooting table: fixed `docker compose pull && up -d` → `docker compose pull && docker compose up -d` — `up -d` alone is not a valid command (fix #28)
> - §3 container startup order: moved `docker-socket-proxy` before Portainer — Portainer's `DOCKER_HOST` env var points at the proxy and attempts to connect immediately on start; proxy must exist first (fix #29)
> - §13 health script: added empty-value guard around `TEMP_MC` — if sysfs is unreadable, the unguarded `awk` arithmetic produced a syntax error; script now reports "down" with a clear message instead of crashing (fix #30)
> - §2 formatting: removed double blank line left by the `chattr` relocation in fix #20 (fix #31)

> **Bug-fix changelog (v4.1):**
> - §7 Step-CA: added `step-ca` to `DOCKER_STEPCA_INIT_DNS_NAMES` — without it NPM's ACME client fails x509 hostname validation when connecting to `https://step-ca:9000` (fix #1)
> - §4 IPv6 kill switch: added `ip6tables -A PROTON_KS -o wg0 -j RETURN` and `fd00:10:10::/64` exemption — without them the Pi host couldn't reach wg0 peers over IPv6 while Proton was running (fix #2)
> - §8 NPM: replaced one-off `docker exec npm update-ca-certificates` with an `entrypoint:` override that re-runs it on every container start — previously the trust bundle was wiped on any container recreate, silently breaking ACME (fix #3)
> - §12 Backup script: added `trap 'docker start …' EXIT` so quiesced services are always restarted even when the script exits early due to a failure (fix #4)
> - §3 DOCKER-USER chain: removed the unreachable `iptables -A DOCKER-USER -j RETURN` that followed a terminal `DROP` (fix #5)
> - §3 docker-socket-proxy: added `-e DELETE=1` so Watchtower's `WATCHTOWER_CLEANUP: "true"` can actually delete old images; without it old image layers accumulate on the SSD (fix #6)
> - §14 troubleshooting table: removed the stale "don't chattr +i" note that contradicted §2's deliberate use of it after setup (fix #7)
> - §13 Watchtower: added the opt-in label to an example service (Kuma) and a note explaining `WATCHTOWER_LABEL_ENABLE` requires it — previously Watchtower ran every Sunday and did nothing (fix #8)

## Network Info

| Setting | Value |
|---|---|
| Hostname | `berrypi5` |
| Pi static IP | `192.168.70.5/22` |
| Subnet | `192.168.68.0/22` |
| Netmask | `255.255.252.0` |
| Gateway (router) | `192.168.68.1` |
| DHCP range | `192.168.68.50 — 192.168.69.250` (shrunk so statics live above) |
| Static range | `192.168.70.0 — 192.168.71.250` |
| wg0 subnet (VPN clients) | `10.10.0.0/24` |
| ProtonVPN tunnel IP | `10.2.0.2/32` (assigned by Proton) |

> ⚠️ **Pre-flight**
> 1. In your router's DHCP settings, shrink the dynamic range to `192.168.68.50 – 192.168.69.250`. The Pi's static IP `192.168.70.5` is now well outside the pool — no conflict possible.
> 2. Boot the Pi from an NVMe SSD (PCIe HAT) or a quality USB SSD. The rest of this guide assumes SSD; SD cards will not survive Docker write churn long enough to matter.
> 3. Use the 8 GB Pi 5 model. The 4 GB will run out under HA + Docker + everything else.
> 4. Have a Pi 5 active cooler (or equivalent fan + heatsink) attached. Without it the SoC will thermal-throttle under sustained load, degrading every service silently — see §15 for monitoring.

## Stack

- Ubuntu Server 24.04 LTS — bare metal
- WireGuard (`wg0`) — remote access for phone + laptop
- ProtonVPN — outbound internet for the home LAN
- Pi-hole + Unbound — ad-blocking DNS + recursive resolver
- Home Assistant Container (not Supervised — see §10)
- PostgreSQL 18.4 — database server for self-hosted web apps (see §11)
- Step-CA — internal certificate authority
- Nginx Proxy Manager — reverse proxy with Step-CA ACME
- Portainer — Docker UI
- Uptime Kuma — service monitoring
- Watchtower — controlled image updates
- TP-Link router-built-in DDNS (`greenhouse.tplinkdns.com`)

---

## Table of Contents

1. [Flash Ubuntu](#1-flash-ubuntu-server-via-pi-imager)
2. [Initial system setup + SSH hardening](#2-initial-system-setup)
3. [Docker, Portainer, log rotation](#3-docker--portainer)
4. [ProtonVPN (corrected routing + kill switch)](#4-protonvpn-via-wireguard)
5. [WireGuard remote access — wg0](#5-wireguard-remote-access--wg0)
6. [Pi-hole + Unbound](#6-pi-hole--unbound)
7. [Step-CA](#7-step-ca)
8. [Caddy reverse proxy](#8-caddy-reverse-proxy)
9. [LAN Gateway — keep the router, not the Pi](#9-lan-gateway--keep-the-router-not-the-pi)
10. [Home Assistant Container](#10-home-assistant-container)
11. [PostgreSQL database server](#11-postgresql-database-server)
12. [DDNS](#12-dynamic-dns-ddns)
13. [Monitoring (Uptime Kuma) + Watchtower](#13-monitoring--watchtower)
14. [Final checklist + verification](#14-final-checklist)
15. [Operations and troubleshooting](#15-operations-and-troubleshooting)

---

## 1. Flash Ubuntu Server via Pi Imager

In Pi Imager:
1. **Device** → Raspberry Pi 5
2. **OS** → Other general-purpose OS → Ubuntu → **Ubuntu Server 24.04 LTS (64-bit)**
3. **Storage** → SSD/NVMe

Click the gear icon ⚙ before writing:
- Hostname: `berrypi5`
- SSH: enabled, **public key only**, paste your public key
- Username: `pi`
- Timezone: `Europe/Rome`

Save → Write.

---

## 2. Initial System Setup

```bash
ssh pi@192.168.70.5
```

### Remove snapd

```bash
sudo systemctl disable --now snapd.service snapd.socket snapd.seeded.service 2>/dev/null
sudo apt purge -y snapd
sudo apt-mark hold snapd
sudo rm -rf ~/snap /snap /var/snap /var/lib/snapd
```

### Update + base packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nano ufw net-tools gnupg2 ca-certificates \
  apt-transport-https software-properties-common fail2ban \
  unattended-upgrades chrony smartmontools
# NOTE: iptables-persistent is intentionally omitted — UFW handles its own
# rule persistence. Installing both causes iptables-persistent to restore a
# stale snapshot on boot before UFW loads, silently breaking wg0 forwarding.
# chrony replaces systemd-timesyncd — we want a real NTP client that can
# survive Proton outages by pointing at the LAN router. See further down.
# smartmontools is for monitoring NVMe wear (§15).
```

### Static IP via Netplan

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.70.5/22
      routes:
        - to: default
          via: 192.168.68.1
      nameservers:
        addresses:
          - 127.0.0.1
          - 9.9.9.9    # fallback during initial setup before Pi-hole is running
```

```bash
sudo chmod 600 /etc/netplan/50-cloud-init.yaml   # netplan complains otherwise
sudo netplan apply
```

> ⚠️ **Disable cloud-init network management.** Cloud-init regenerates `50-cloud-init.yaml` on boot if it believes it still owns networking, overwriting your static IP with a DHCP config. Prevent this with one line:
> ```bash
> sudo bash -c 'echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg'
> ```
> Without this, an apt upgrade that triggers a cloud-init re-run can silently revert the Pi to DHCP on the next reboot — losing the static IP and breaking every service that depends on it.

### Hostname

```bash
sudo hostnamectl set-hostname berrypi5
# Keep ::1 localhost — stripping it breaks IPv6 loopback resolution for
# any service that resolves 'localhost' over IPv6 (Docker, some HA integrations).
printf '127.0.0.1 localhost\n::1 localhost ip6-localhost ip6-loopback\n192.168.70.5 berrypi5\n' | sudo tee /etc/hosts
```

### Disable systemd-resolved

`systemd-resolved` listens on port 53, blocking Pi-hole. Disable it and write a static `resolv.conf` now. The file is pinned with `chattr +i` **later** (at the end of §6, once Pi-hole is confirmed working) so Ubuntu point-release updates and cloud-init can't reinstate the `systemd-resolved` symlink. Pinning it now would block netplan and cloud-init during the rest of initial setup.

```bash
sudo systemctl disable --now systemd-resolved
sudo rm -f /etc/resolv.conf
echo "nameserver 127.0.0.1
nameserver 9.9.9.9
options edns0 timeout:1" | sudo tee /etc/resolv.conf
```

The fallback `9.9.9.9` is only used if `127.0.0.1:53` is unreachable (Pi-hole container down). With `timeout:1` the resolver fails over fast. This is preferable to a DNS-less box during maintenance.

> ⚠️ **Do NOT run `chattr +i` yet.** The file needs to remain writable during the rest of initial setup (netplan, cloud-init, and package installs can all touch it). Pin it only after Pi-hole is confirmed working — see the deferred step at the end of §6.

### SSH hardening

```bash
sudo nano /etc/ssh/sshd_config.d/99-hardening.conf
```

```
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
KbdInteractiveAuthentication no
MaxAuthTries 3
LoginGraceTime 20
AllowUsers pi
X11Forwarding no
AllowAgentForwarding no
```

```bash
sudo systemctl restart ssh
sudo systemctl enable --now fail2ban
```

### Enable IP forwarding

```bash
sudo nano /etc/sysctl.d/99-homelab.conf
```

```
net.ipv4.ip_forward=1
net.ipv4.conf.all.src_valid_mark=1
net.ipv6.conf.all.forwarding=1
```

```bash
sudo sysctl --system
```

### chrony — NTP with LAN fallback

The Proton kill switch (§4) blocks all egress when the tunnel is down, including UDP 123. If the Pi reboots while Proton is down, the clock drifts; once it drifts past Step-CA leaf-cert validity skew, every internal TLS handshake fails simultaneously and very confusingly. Two mitigations: (a) point chrony at the LAN router so NTP keeps working even when Proton is down (a router that actually runs an NTP server is the ideal); (b) add an NTP exception to the kill switch itself (covered in §4) so the public pool also works.

> ⚠️ **Most consumer routers (including most TP-Link models) are NTP clients, not servers** — they sync their own clock from upstream but don't serve NTP to LAN clients. Test yours before relying on it (see the verification step below). If yours doesn't serve NTP, drop the `server 192.168.68.1` line; the kill-switch UDP/123 exception in §4 alone keeps the public-pool path working.

```bash
sudo nano /etc/chrony/chrony.conf
```

Replace contents with:

```
# LAN router first — only useful if your router actually runs an NTP server.
# Test with `chronyc sources -v` after enabling chrony. If 192.168.68.1 sits at
# state "?" or "x" (not reaching), comment this line out — the public pool
# below is reached via the kill-switch UDP/123 exception in §4.
server 192.168.68.1 iburst prefer

# Public pool — backup for when the router doesn't serve NTP, OR primary if
# you commented the line above out. Reachable when Proton is up; also
# reachable when Proton is down thanks to the kill-switch exception (§4).
pool 2.ubuntu.pool.ntp.org iburst maxsources 4

driftfile /var/lib/chrony/chrony.drift
makestep 1.0 3
rtcsync
logdir /var/log/chrony
```

```bash
sudo systemctl disable --now systemd-timesyncd 2>/dev/null || true
sudo systemctl enable --now chrony

# Wait ~30s for chrony to reach out, then verify:
sleep 30
chronyc tracking      # "Leap status: Normal" and Stratum should be non-zero
chronyc sources -v    # check whether 192.168.68.1 ever reaches state ^* or ^+
```

If `chronyc sources -v` shows the router at `?` or `x` after a couple of minutes, your router isn't serving NTP. Edit `chrony.conf`, remove the `server 192.168.68.1` line, and `sudo systemctl restart chrony`. The public-pool path via the kill-switch exception is still sufficient.

### UFW

The big difference from v1: forward policy must be `ACCEPT`, and we open the right ports for VPN clients to reach DNS and HTTP.

```bash
# Forward policy — without this, wg0 forwarding silently fails
sudo sed -i 's/^DEFAULT_FORWARD_POLICY=.*/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw

sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH
sudo ufw allow ssh

# Caddy (HTTP/HTTPS reverse proxy)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# WireGuard remote access
sudo ufw allow 51820/udp

# DNS / web from VPN clients
sudo ufw allow in on wg0 to any port 53 comment 'DNS for VPN clients'
sudo ufw allow in on wg0 to any port 80,443 proto tcp comment 'Caddy via VPN'

# DNS from home LAN (Pi-hole)
sudo ufw allow from 192.168.68.0/22 to any port 53

# FIX #106: Home Assistant (§10) runs network_mode: host, binding directly to
# 0.0.0.0:8123 on the Pi. It is NOT behind Docker's port-publishing NAT, so
# Docker adds no iptables rules for it and UFW's `default deny incoming` would
# otherwise drop every packet to 8123 — breaking both LAN-direct access AND
# Caddy's ha.home.arpa proxy (Caddy is a container on 172.31.x.x and
# forwards to 192.168.70.5:8123). These rules are added now even though HA is
# deployed in §10; UFW happily allows a port nothing is listening on yet.
sudo ufw allow from 172.16.0.0/12 to any port 8123 comment 'Caddy container -> HA on host network'
sudo ufw allow from 192.168.68.0/22 to any port 8123 comment 'HA direct from LAN'
# Optional — also allow wg0 clients to reach HA directly (not just via Caddy):
# sudo ufw allow in on wg0 to any port 8123 comment 'HA via VPN'

sudo ufw enable
sudo ufw status verbose
```

### ⚠️ Docker bypasses UFW — closed in §3

When a container exposes a port with `-p 9443:9443`, Docker writes rules into the `DOCKER` chain that run **before** UFW's user rules. The result: Portainer (9443), Step-CA (9000), Kuma (3001), Pi-hole admin (8080), and Home Assistant (8123, host network) would otherwise be reachable from every LAN client even though `ufw status` claims only 22/80/443/53/51820 are open.

This is addressed in **§3** (after Docker is installed) by:
1. Binding admin-port containers to `127.0.0.1` only, so Caddy on a shared bridge is the only thing that can reach them.
2. A systemd service that populates Docker's `DOCKER-USER` chain on every Docker start, providing defence-in-depth against future containers that forget to bind to loopback.

Both need Docker to exist first; come back to those after §3.

### Unattended security updates

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```

Choose **Yes**. Edit `/etc/apt/apt.conf.d/50unattended-upgrades` to allow all distro security updates and reboot at 02:00 if required:

```
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
```

> ℹ️ **Why 02:00, not 03:00:** the backup timer runs at 04:00 with `Persistent=true`. If the Pi reboots at 03:00 and is still settling when 04:00 arrives, systemd may fire the backup before all containers are healthy. 02:00 gives a clean two-hour margin. Do not use 03:00–04:30.

---

## 3. Docker + Portainer

### Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo systemctl enable --now docker
newgrp docker
```

> ⚠️ `newgrp docker` only applies the new group membership to the **current shell session**. Any other open terminals, or SSH sessions started before this point, still won't have the `docker` group — `docker ps` will return "permission denied" in them. The cleanest fix is to log out and back in (`exit`, then `ssh pi@192.168.70.5` again) before continuing. The `newgrp docker` above works if you're running everything in one session, but a fresh login is safer.

### Log rotation (critical)

Without this, Pi-hole logs alone will fill your disk.

```bash
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-address-pools": [
    { "base": "172.20.0.0/14", "size": 24 }
  ],
  "dns": ["192.168.70.5", "9.9.9.9"]
}
```

> ℹ️ **Why `default-address-pools`:** This guide manually pins `proxy-net` to `172.31.0.0/24` and `dns-net` to `172.30.0.0/24`. Both sit inside Docker's default auto-allocation range (`172.16.0.0/12`). Without this setting, Docker could auto-assign a new network the same prefix, causing an address conflict that silently breaks routing. The pool above confines auto-allocation to `172.20.0.0/14` (covering `172.20–172.23.x`), which avoids both the `docker0` default bridge (`172.17.x`) and our manually-pinned `172.30–172.31.x` ranges. If you already have Docker networks from a previous install, inspect them with `docker network ls` and `docker network inspect <name>` before restarting.

> ℹ️ **Why explicit `dns:` (FIX #111):** Without this, Docker reads the host's `/etc/resolv.conf`, drops the `127.0.0.1` entry (containers can't reach the host's loopback), and uses what's left — `9.9.9.9` — as the upstream resolver for every container. Pi-hole is bypassed entirely from inside any container, and `*.home.arpa` queries hit `9.9.9.9` and return `NXDOMAIN`. This silently breaks Step-CA's ACME HTTP-01 validation: Step-CA can't resolve `ha.home.arpa` (or any other proxy host) to fetch the challenge URL, so NPM never gets a cert issued and the doc's documented ACME path doesn't actually work on first deployment. The fix is to point every container at Pi-hole via the host's LAN IP `192.168.70.5` (where Pi-hole's `0.0.0.0:53` publish lives), with `9.9.9.9` as the second-listed fallback so external resolution still works if Pi-hole is down or quiesced during a backup run. Pi-hole's `FTLCONF_dns_listeningMode: "ALL"` (§6) is what makes it answer queries arriving from container subnets like `172.20–172.23.x`/`172.30.x`/`172.31.x`.

```bash
sudo systemctl restart docker
```

### DOCKER-USER chain — defence-in-depth against container port exposure

The architectural fix for the Docker-bypasses-UFW issue (warned about in §2) is binding admin ports to `127.0.0.1`, which we do from §3 onward (Portainer in this section already binds to `127.0.0.1:9443`). As belt-and-braces, populate Docker's `DOCKER-USER` chain so any container that *does* bind a port on `0.0.0.0` is still only reachable from the LAN and wg0 — never from anywhere we didn't intend.

We do this via a systemd oneshot that runs after `docker.service`, not via `/etc/ufw/after.rules`. Two reasons: (1) the `DOCKER-USER` chain only exists when Docker is running, so `iptables-restore` from UFW's after-hooks fails if Docker isn't up yet; (2) Docker restarts (during package upgrades, daemon.json reloads, etc.) wipe and recreate the chain. A systemd service bound to `docker.service` via `PartOf=` re-applies the rules every time Docker starts.

```bash
sudo nano /usr/local/bin/docker-user-rules.sh
```

```bash
#!/bin/bash
# Flush and rebuild DOCKER-USER chain to lock down container egress.
# Container ports bound to 0.0.0.0:* will only be reachable from LAN + wg0.
# Caddy's 80/443 from LAN: the initial SYN matches the LAN-source RETURN
# below (`-s 192.168.68.0/22`); subsequent reply traffic in the same
# connection matches the RELATED,ESTABLISHED RETURN at the top of the
# chain. Both directions need a RETURN somewhere — neither rule alone is
# sufficient. (FIX #97: earlier wording claimed NPM's new connections
# matched the RELATED,ESTABLISHED RETURN first; they don't — that rule
# is for reply traffic only.)
set -e
iptables -F DOCKER-USER
iptables -A DOCKER-USER -m state --state RELATED,ESTABLISHED -j RETURN
iptables -A DOCKER-USER -i wg0 -j RETURN
iptables -A DOCKER-USER -s 192.168.68.0/22 -j RETURN
iptables -A DOCKER-USER -s 172.16.0.0/12 -j RETURN
# FIX #58: allow host-to-container loopback traffic. Without this, calls from
# the Pi host to container-exposed ports on 127.0.0.1 (e.g. the health push
# script hitting Kuma at 127.0.0.1:3001, docker run calls in the backup loop)
# are silently DROP'd — their source address is 127.x.x.x, not a Docker bridge
# address, so the 172.16.0.0/12 rule above doesn't match them.
iptables -A DOCKER-USER -s 127.0.0.0/8 -j RETURN
iptables -A DOCKER-USER -j DROP

# ip6tables equivalents. FIX #108: contrary to an earlier comment here, Docker
# does NOT auto-create the DOCKER-USER chain on ip6tables. Docker only manages
# ip6tables (and creates DOCKER-USER on it) when `"ip6tables": true` is set in
# /etc/docker/daemon.json — which this guide does not enable by default. On a
# stock setup the IPv6 DOCKER-USER chain does not exist, and `ip6tables -F
# DOCKER-USER` fails with "No chain by that name". With `set -e` at the top of
# this script, that single line aborted the entire run, leaving the IPv4 rules
# applied (they happen to come first) but the systemd unit in `failed` state
# — easy to miss until you check `systemctl status docker-user-rules`.
#
# Switched to the same create-or-flush idiom §4's PROTON_KS uses, so the
# script is idempotent regardless of whether the chain exists.
#
# Note these IPv6 rules are *dormant* on the default config: Docker doesn't
# route container traffic through ip6tables FORWARD unless `"ip6tables": true`
# is set. They become effective only if you later enable Docker IPv6 by adding
# to /etc/docker/daemon.json:
#     "ipv6": true,
#     "ip6tables": true,
#     "fixed-cidr-v6": "fd00:dead:beef::/48"
# and restarting Docker — at which point the existing rules below already lock
# down v6 ingress to containers using the same model as the v4 rules above.
# Leaving them in place pre-emptively means turning on Docker v6 later doesn't
# also require remembering to come back here.
ip6tables -N DOCKER-USER 2>/dev/null || ip6tables -F DOCKER-USER
ip6tables -A DOCKER-USER -m state --state RELATED,ESTABLISHED -j RETURN
ip6tables -A DOCKER-USER -i wg0 -j RETURN
ip6tables -A DOCKER-USER -s fc00::/7 -j RETURN   # ULA — covers fd00:10:10::/64
ip6tables -A DOCKER-USER -s ::1/128 -j RETURN     # loopback equivalent of 127.0.0.0/8
ip6tables -A DOCKER-USER -j DROP
```

```bash
sudo chmod 700 /usr/local/bin/docker-user-rules.sh

sudo nano /etc/systemd/system/docker-user-rules.service
```

```ini
[Unit]
Description=Apply DOCKER-USER hardening rules
After=docker.service
Requires=docker.service
PartOf=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/docker-user-rules.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now docker-user-rules.service
sudo iptables -nvL DOCKER-USER     # verify the IPv4 chain is populated
sudo ip6tables -nvL DOCKER-USER    # verify the IPv6 chain is populated (created on first run if Docker hadn't auto-created it — see FIX #108 in the script)
```

Test it later (once you have a container running on a port): from another LAN host, hit one of the loopback-bound admin ports — it should fail. From a wg0 client, it should fail too (because the RETURN happens before the container's exposed port; the LAN/wg0 RETURNs only catch ports bound to 0.0.0.0). The intent is: a container that forgets to bind to loopback is still not exposed to a hypothetical WAN-side attacker if someone accidentally port-forwards.

### Create the shared `proxy-net` network

Every web UI in this guide binds its admin port to `127.0.0.1` so it can't be reached directly from the LAN. Caddy (§8) sits on a shared bridge network with all of them so it can reach each container by name. Create that network once, up front:

```bash
docker network create --driver bridge --subnet 172.31.0.0/24 proxy-net
```

### Portainer + docker-socket-proxy (combined bootstrap stack)

Both Portainer and Watchtower need Docker API access. Mounting `/var/run/docker.sock` directly into either is root-equivalent on the host — a CVE in either image gives an attacker the whole machine. `tecnativa/docker-socket-proxy` sits between them and exposes only the API endpoints each tool actually needs (with `EXEC=0` blocking the most dangerous `/exec` family — Portainer's "Console" tab is intentionally disabled by this).

These two containers form the bootstrap layer: every Portainer-managed stack (§6 onward) needs Portainer to exist first, and Portainer needs `docker-socket-proxy` to exist before its first reach. The pair therefore lives on disk as one compose file and gets brought up via `docker compose` from the CLI, not via the Portainer UI. Portainer **does** see this stack once it's running — Compose project labels make it auto-discoverable under **Stacks → External** — so subsequent updates can be done from the Portainer UI; only the **first** deploy is CLI-only.

```bash
sudo mkdir -p /opt/portainer
sudo nano /opt/portainer/docker-compose.yml
```

```yaml
services:
  docker-socket-proxy:
    image: tecnativa/docker-socket-proxy:v0.4.2
    container_name: docker-socket-proxy
    restart: unless-stopped
    # FIX #113 (corrects #112), still load-bearing under v0.4.x: no --read-only here.
    # The image's entrypoint sed-renders /usr/local/etc/haproxy/haproxy.cfg.template
    # -> haproxy.cfg in the same directory at every start; --read-only or --tmpfs
    # over that path breaks the entrypoint. v0.4.x didn't change this behaviour,
    # only the underlying HAProxy bump from 2.x to 3.x. `no-new-privileges` is the
    # hardening that does still work — blocks setuid escalation inside the container,
    # which is a more relevant attack class here than --read-only's filesystem-tamper
    # protection. Docker socket stays :ro, API surface remains restricted by the
    # env-var allowlist, container is firewalled from the LAN by §3 DOCKER-USER rules.
    security_opt:
      - no-new-privileges:true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      # API endpoint allowlist. Both Portainer's normal operation and
      # Watchtower's WATCHTOWER_CLEANUP=true (which issues DELETE /images/{id})
      # need POST and DELETE — without DELETE=1 Watchtower silently skips
      # cleanup and old image layers accumulate on the SSD (fix #6).
      CONTAINERS: 1
      IMAGES: 1
      NETWORKS: 1
      VOLUMES: 1
      SERVICES: 1
      TASKS: 1
      NODES: 1
      INFO: 1
      VERSION: 1
      SYSTEM: 1
      POST: 1
      DELETE: 1
      # Hard NO list:
      EXEC: 0          # blocks Portainer's "Console" tab — intentional mitigation
      BUILD: 0
      COMMIT: 0
      CONFIGS: 0
      DISTRIBUTION: 0
      PLUGINS: 0
      SECRETS: 0
      SESSION: 0
      SWARM: 0
      AUTH: 0
    networks:
      proxy-net:
        ipv4_address: 172.31.0.13

  portainer:
    image: portainer/portainer-ce:2.27.5
    container_name: portainer
    restart: unless-stopped
    # No /var/run/docker.sock mount — Portainer reaches Docker exclusively
    # through docker-socket-proxy. A Portainer compromise therefore can't run
    # arbitrary host commands. Access via Caddy at https://portainer.home.arpa
    # once §8 is up. During initial bootstrap, before Caddy exists, use the
    # SSH tunnel: `ssh -L 9443:127.0.0.1:9443 pi@192.168.70.5` then open
    # https://127.0.0.1:9443 on your laptop.
    environment:
      # Tells Portainer's daemon-connection logic to use the proxy by default.
      # Still needs the manual one-time "Add environment" step on first login
      # (see "Portainer first-run with socket-proxy" below).
      DOCKER_HOST: "tcp://docker-socket-proxy:2375"
    ports:
      - "127.0.0.1:9443:9443"
    volumes:
      - portainer-data:/data
    networks:
      proxy-net:
        ipv4_address: 172.31.0.12
    depends_on:
      docker-socket-proxy:
        condition: service_started

networks:
  proxy-net:
    external: true

volumes:
  portainer-data:
```

Bring it up:

```bash
cd /opt/portainer && sudo docker compose up -d
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "portainer|socket-proxy"
# Expect both Up <n>s, portainer with 127.0.0.1:9443->9443/tcp
docker logs docker-socket-proxy 2>&1 | head -5     # expect HAProxy worker-fork output
```

### Portainer first-run with socket-proxy — the manual bit

Portainer doesn't auto-create a "local" environment from `DOCKER_HOST` at first login — you confirm the connection in the UI once:

1. Open `https://127.0.0.1:9443` over the SSH tunnel (`ssh -L 9443:127.0.0.1:9443 pi@192.168.70.5`).
2. Create the admin user when prompted (long password, store in your password manager).
3. On the "Quick Setup" screen, choose **Get Started** → it will show "no environments." Expected.
4. Left sidebar → **Environments** → **+ Add environment**.
5. Select **Docker Standalone** → **Start Wizard** → **API**.
6. **Environment URL:** `tcp://docker-socket-proxy:2375` (matches the `DOCKER_HOST` env var, container DNS name on proxy-net).
7. Leave TLS off. Click **Connect**.
8. The new environment appears in the list. Click in — you should see your existing containers (`portainer`, `docker-socket-proxy`).

> ℹ️ With `EXEC=0` on the socket-proxy, Portainer's "Console" tab on each container is disabled (you'll see an error if you click it). This is intentional — it's the main mitigation. To shell into a container in an emergency, SSH to the host and `docker exec -it <name> sh` directly.

> ℹ️ **Portainer discovers this stack as "External".** After step 8, navigate to **Stacks** — you'll see `portainer` listed with the "External" badge (Portainer detects it via Compose project labels). Portainer can browse/edit/redeploy it from this point onward; only the *initial* deploy is CLI-only.

> All Docker images in this guide are pinned to a specific tag. Update them deliberately via Watchtower or manual `docker compose pull`. **Do not** use `:latest` — silent breaking changes will destroy your homelab on a random Tuesday.

### Deploying services via Portainer Stacks

Everything from §6 onward (Pi-hole, Step-CA, Caddy, Home Assistant, Uptime Kuma, Watchtower) is deployed as a **Portainer Stack** instead of raw `docker compose` CLI commands. Portainer stores the stack definition, manages the containers, and gives you one-click redeploy, live logs, and restart from the UI.

**What cannot be a Portainer-managed stack** (these have to come up before Portainer itself, so they're CLI-deployed):
- The `portainer` stack itself (Portainer + docker-socket-proxy) — chicken-and-egg, described above. Portainer manages it after first boot via the "External" badge.
- WireGuard `wg0` — requires host network config and `wg-quick` systemd integration
- ProtonVPN — same reason

**How to create a stack in Portainer:**

1. Open Portainer → **Stacks** → **+ Add stack**
2. Give it the name shown in each section (e.g. `dns`, `step-ca`, `caddy`)
3. Select **Web editor** and paste the YAML shown below
4. Set any environment variables in the **Environment variables** panel if noted
5. Click **Deploy the stack**

The YAML is also written to `/opt/<name>/docker-compose.yml` on disk for git tracking. Portainer and the on-disk file are independent — if you edit one, sync the other.

```bash
# Create the /opt directory structure once, for git.
# /opt/portainer was created above when you wrote the bootstrap compose.
sudo mkdir -p /opt/{dns,step-ca,caddy,homeassistant,kuma,watchtower}
```

**To update a stack** (e.g. bump an image tag): Portainer → Stacks → select the stack → **Editor** tab → change the tag → **Update the stack**. Portainer pulls the new image and recreates only the affected containers.

---

## 4. ProtonVPN via WireGuard — multi-tunnel with per-client routing

v5.1.7.21 replaces the single-tunnel ProtonVPN design with N parallel Proton tunnels, each terminating at a different exit country, plus iptables-mangle MARK rules that route individual wg0 client peers through the tunnel of your choice. Driving use case: pin the phone to a Netherlands exit while the laptop egresses via USA for geo-blocked content, with a health-check daemon failing each client over to a configured fallback tunnel if its primary goes down.

### What changed vs the previous single-tunnel design

| Concern               | Single-tunnel (≤ v5.1.7.20)                                  | Multi-tunnel (v5.1.7.21+)                                                                                                                        |
| --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Pi-side outbound      | Through ProtonVPN (kill switch enforced)                     | **Direct via eth0** — Pi container egress, ACME calls, Watchtower pulls all go via home ISP, unmasked                                            |
| wg0 client outbound   | Through the one Proton tunnel                                | Through the per-client assigned tunnel; unlisted clients use `DEFAULT_TUNNEL`                                                                    |
| Kill-switch scope     | All Pi outbound + forwarded wg0 traffic                      | **Only forwarded wg0 traffic** — if a client's tunnel is down and no fallback is available, that client is REJECT'd rather than leaking via eth0 |
| Tunnel count          | 1 (`protonvpn`)                                              | N (`protonvpn0`, `protonvpn1`, …)                                                                                                                |
| Fwmark per tunnel     | 51820 (wg-quick auto-assigned)                               | Manual, equals each tunnel's routing-table ID (100, 101, …)                                                                                      |
| wg0 protocol fwmark   | 51820, exempted by wg-quick's auto-installed rule (fix #117) | Still 51820, exempted by an explicit `PROTON_KS -m mark --mark 51820 -j RETURN` installed by `proton-killswitch-init.sh`                         |
| wg-quick auto-routing | Active (`AllowedIPs = 0.0.0.0/0` with default Table)         | **Disabled** (`Table = off`); all routing managed by `proton-tunnel-up.sh`                                                                       |

**Read carefully:** the "Pi-side outbound now direct" row is the biggest behaviour change. Docker image pulls, Step-CA ACME validation calls reaching out, Caddy ACME challenges fetching content for HTTP-01, Watchtower checking image registries — all now go through your home ISP unmasked. If you don't want that, stay on v5.1.7.20's single-tunnel design.

### Install tools

```bash
sudo apt install -y wireguard wireguard-tools qrencode iproute2
```

### Pick your tunnels

Decide which ProtonVPN exits you want to terminate. Two is the practical minimum — one country pair gives you a primary plus a fallback for the health-check daemon. Five is the doc's example ceiling (more would mean expanding the `rt_tables` allocation).

Recommended starter pair: Netherlands (low latency from EU, strict no-logs jurisdiction) + Sweden or Switzerland (different jurisdiction for failover). Add USA / UK / Japan as geo-region needs dictate.

### Routing-table IDs

Append to `/etc/iproute2/rt_tables` once. Each line maps a numeric ID to a human-readable name (the `iproute2` tools accept either):

```bash
sudo tee -a /etc/iproute2/rt_tables <<'EOF'

# ProtonVPN multi-tunnel routing tables (fix #124)
100   proton0
101   proton1
102   proton2
103   proton3
104   proton4
EOF
```

Reserve up to whichever ID matches your tunnel count. Don't reuse numbers that already exist in `/etc/iproute2/rt_tables` (the defaults occupy 0, 253, 254, 255).

### Central config

```bash
sudo nano /etc/wireguard/proton.conf
sudo chmod 600 /etc/wireguard/proton.conf
```

```bash
# /etc/wireguard/proton.conf — multi-tunnel central config
# This is the ONLY file you edit when adding tunnels or reassigning clients.

# The WireGuard server interface that clients connect to.
WG_CLIENT_IFACE="wg0"

# Tunnels: "interface_name:routing_table_id:country_label"
# The routing_table_id must be unique and match the line in /etc/iproute2/rt_tables.
# country_label is cosmetic — only used by proton-status.sh.
TUNNELS=(
  "protonvpn0:100:Netherlands"
  "protonvpn1:101:USA"
  # "protonvpn2:102:UK"          # uncomment + add a protonvpn2.conf to enable
  # "protonvpn3:103:Switzerland"
)

# Client→tunnel mapping: "label:wg0_peer_ip:tunnel_interface"
# wg0_peer_ip is the address that peer holds INSIDE wg0 (10.10.0.0/24, see §5).
# Verify with `sudo wg show wg0` after the client's tunnel is up.
CLIENTS=(
  "phone:10.10.0.2:protonvpn0"
  "laptop:10.10.0.3:protonvpn1"
  # "tablet:10.10.0.4:protonvpn0"
)

# Fallback tunnel for any wg0 peer not listed in CLIENTS.
DEFAULT_TUNNEL="protonvpn0"

# Health check: ping HEALTH_CHECK_HOST through each tunnel every INTERVAL seconds.
# Mark tunnel DOWN after FAILURES consecutive misses.
HEALTH_CHECK_HOST="9.9.9.9"          # Quad9, matches the doc's standardised resolver
HEALTH_CHECK_INTERVAL=60
HEALTH_CHECK_FAILURES=3
```

### Per-tunnel WireGuard config

Download a WireGuard config from `https://account.proton.me/vpn → Downloads → WireGuard configuration` for each country you picked. Save each as `/etc/wireguard/protonvpnN.conf` (N = 0, 1, 2, …). Replace the `[Interface]` section with the template below (keep the `[Peer]` section that Proton gave you, verbatim).

```bash
sudo nano /etc/wireguard/protonvpn0.conf
sudo chmod 600 /etc/wireguard/protonvpn0.conf
```

```ini
[Interface]
# Keep the PrivateKey and Address that Proton gave you.
PrivateKey = <paste-proton-private-key-here>
Address = 10.2.0.2/32

# 1320 is ProtonVPN's MTU ceiling. Don't raise it — their servers reject larger packets,
# silently stalling large transfers. wg0 (§5) is set to 1280 to leave overhead for THIS
# tunnel's encapsulation; raising this would invalidate that calculation.
MTU = 1320

# Table = off tells wg-quick NOT to install its default routing rules / fwmark for this
# interface. All routing is managed by proton-tunnel-up.sh and proton-routing.sh below.
# Without this, wg-quick auto-assigns fwmark 51820 to EVERY Proton tunnel — they collide,
# and both fight the manual rules the script adds.
Table = off

# FwMark on the wg socket itself. proton-tunnel-up.sh installs an `ip rule fwmark $TABLE
# lookup $TABLE` for client traffic; this FwMark is the SAME value so the wg socket's
# own protocol traffic (handshakes to the Proton server) ALSO uses this table. That table
# has only `default dev protonvpnN` — but the Proton server endpoint is reached via the
# main table's default route via eth0, not via the tunnel itself, so set this to the
# table ID to keep behaviour consistent. Replace TABLE_ID below with the matching number
# for THIS tunnel (100 for protonvpn0, 101 for protonvpn1, etc.)
FwMark = 100

# DO NOT set DNS = ... here. Pi-hole handles DNS for everything in §6.

# Hooks — proton-tunnel-up.sh manages routing-table population and per-tunnel kill-switch
# exemptions. %i expands to the interface name (protonvpn0). Replace TABLE_ID below.
PostUp   = /usr/local/bin/proton-tunnel-up.sh up   %i 100
PostDown = /usr/local/bin/proton-tunnel-up.sh down %i 100

# === [Peer] section: paste EXACTLY as Proton downloaded it, no edits ===
[Peer]
PublicKey = <proton-server-public-key>
Endpoint = <proton-server-ip>:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

For each subsequent tunnel, copy this file and update **three numbers** — the `FwMark`, both `TABLE_ID`s in the PostUp/PostDown lines — to match the table ID for that tunnel (`protonvpn1` → 101, `protonvpn2` → 102, …). And of course replace the `[Peer]` block.

### Kill-switch chain initialiser

This script previously lived inside the old `protonvpn-up.sh`, tied to the single tunnel's lifecycle. In the multi-tunnel design it's split out so the chain exists *before* any individual tunnel comes up and survives any single tunnel restart.

```bash
sudo nano /usr/local/bin/proton-killswitch-init.sh
sudo chmod 755 /usr/local/bin/proton-killswitch-init.sh
```

```bash
#!/bin/bash
# /usr/local/bin/proton-killswitch-init.sh
# Creates the PROTON_KS chain with the permanent baseline exemptions.
# Per-tunnel RETURN rules are added/removed by /usr/local/bin/proton-tunnel-up.sh.
set -euo pipefail

ACTION="${1:-up}"
LOG_TAG="proton-killswitch"
log() { logger -t "$LOG_TAG" "$*"; echo "[$(date '+%H:%M:%S')] $*"; }

create_chain_v4() {
  iptables -N PROTON_KS 2>/dev/null || iptables -F PROTON_KS

  # Permanent exemptions — order matters (most-specific first).
  iptables -A PROTON_KS -d 192.168.68.0/22 -j RETURN              # LAN
  iptables -A PROTON_KS -d 10.10.0.0/24    -j RETURN              # wg0 client subnet
  iptables -A PROTON_KS -d 172.16.0.0/12   -j RETURN              # Docker bridges
  iptables -A PROTON_KS -d 224.0.0.0/4     -j RETURN              # multicast
  iptables -A PROTON_KS -m addrtype --dst-type LOCAL -j RETURN    # loopback / local services
  iptables -A PROTON_KS -p udp --dport 123 -j RETURN              # NTP (chrony fallback)

  # wg0's own protocol traffic — fix #117 stance preserved: wg0 sets FwMark = 51820 on
  # its UDP socket so handshake replies to remote phone/laptop peers escape the kill switch.
  # In the single-tunnel design wg-quick auto-installed an equivalent rule; here it's explicit.
  iptables -A PROTON_KS -m mark --mark 51820 -j RETURN

  # Per-tunnel RETURNs (-o protonvpnN  and  --mark <table>) are added by proton-tunnel-up.sh
  # when each tunnel comes up, INSERTED above this final REJECT.

  iptables -A PROTON_KS -j REJECT --reject-with icmp-port-unreachable

  # Hook into OUTPUT. Without this jump, the chain exists but does nothing.
  iptables -C OUTPUT -j PROTON_KS 2>/dev/null || iptables -I OUTPUT -j PROTON_KS
}

create_chain_v6() {
  ip6tables -N PROTON_KS 2>/dev/null || ip6tables -F PROTON_KS

  ip6tables -A PROTON_KS -d fd00:10:10::/64 -j RETURN             # wg0 IPv6 ULA
  ip6tables -A PROTON_KS -d fc00::/7        -j RETURN             # any ULA (LAN if you have one)
  ip6tables -A PROTON_KS -d fe80::/10       -j RETURN             # link-local
  ip6tables -A PROTON_KS -d ff00::/8        -j RETURN             # multicast
  ip6tables -A PROTON_KS -m addrtype --dst-type LOCAL -j RETURN
  ip6tables -A PROTON_KS -p udp --dport 123 -j RETURN

  ip6tables -A PROTON_KS -m mark --mark 51820 -j RETURN

  ip6tables -A PROTON_KS -j REJECT --reject-with icmp6-port-unreachable

  ip6tables -C OUTPUT -j PROTON_KS 2>/dev/null || ip6tables -I OUTPUT -j PROTON_KS
}

destroy_chain_v4() {
  iptables -D OUTPUT -j PROTON_KS 2>/dev/null || true
  iptables -F PROTON_KS 2>/dev/null || true
  iptables -X PROTON_KS 2>/dev/null || true
}
destroy_chain_v6() {
  ip6tables -D OUTPUT -j PROTON_KS 2>/dev/null || true
  ip6tables -F PROTON_KS 2>/dev/null || true
  ip6tables -X PROTON_KS 2>/dev/null || true
}

case "$ACTION" in
  up)   log "Initialising PROTON_KS chain (v4 + v6)"; create_chain_v4; create_chain_v6 ;;
  down) log "Tearing down PROTON_KS chain (v4 + v6)"; destroy_chain_v4; destroy_chain_v6 ;;
  *)    echo "Usage: $0 up|down" >&2; exit 1 ;;
esac
```

### Per-tunnel up/down hook

```bash
sudo nano /usr/local/bin/proton-tunnel-up.sh
sudo chmod 755 /usr/local/bin/proton-tunnel-up.sh
```

```bash
#!/bin/bash
# /usr/local/bin/proton-tunnel-up.sh
# Called by PostUp / PostDown in each /etc/wireguard/protonvpnN.conf.
# Adds (or removes) per-tunnel routing and kill-switch exemptions.
set -euo pipefail

ACTION="${1:?up|down}"
IFACE="${2:?interface}"
TABLE="${3:?table_id}"
LOG_TAG="proton-tunnel"
log() { logger -t "$LOG_TAG" "$*"; echo "[$(date '+%H:%M:%S')] $*"; }

case "$ACTION" in
  up)
    log "Bringing up routing for $IFACE (table $TABLE)"

    # IPv4 routing table — flush stale, install default via tunnel.
    ip route flush table "$TABLE" 2>/dev/null || true
    ip route add default dev "$IFACE" table "$TABLE"

    # Marked traffic uses this table. Use $TABLE as the rule priority too — keeps
    # priorities collision-free as long as table IDs are unique.
    ip rule del fwmark "$TABLE" table "$TABLE" 2>/dev/null || true
    ip rule add fwmark "$TABLE" table "$TABLE" priority "$TABLE"

    # IPv6 — mirror v4 if Proton handed out a v6 address in this tunnel.
    # (Harmless to install even if Proton didn't — no v6 traffic matches.)
    ip -6 route flush table "$TABLE" 2>/dev/null || true
    ip -6 route add default dev "$IFACE" table "$TABLE" 2>/dev/null || true
    ip -6 rule del fwmark "$TABLE" table "$TABLE" 2>/dev/null || true
    ip -6 rule add fwmark "$TABLE" table "$TABLE" priority "$TABLE" 2>/dev/null || true

    # MASQUERADE for wg0 client traffic egressing via this tunnel.
    iptables  -t nat -C POSTROUTING -s 10.10.0.0/24    -o "$IFACE" -j MASQUERADE 2>/dev/null || \
    iptables  -t nat -A POSTROUTING -s 10.10.0.0/24    -o "$IFACE" -j MASQUERADE
    ip6tables -t nat -C POSTROUTING -s fd00:10:10::/64 -o "$IFACE" -j MASQUERADE 2>/dev/null || \
    ip6tables -t nat -A POSTROUTING -s fd00:10:10::/64 -o "$IFACE" -j MASQUERADE 2>/dev/null || true

    # Kill-switch exemptions for THIS tunnel — INSERTED at the top so they fire before
    # the final REJECT. The chain itself was created by proton-killswitch-init.sh.
    if iptables -L PROTON_KS >/dev/null 2>&1; then
      iptables  -I PROTON_KS -o "$IFACE"           -j RETURN
      iptables  -I PROTON_KS -m mark --mark "$TABLE" -j RETURN
    else
      log "WARNING: PROTON_KS chain not found — kill switch is not protecting traffic for $IFACE"
    fi
    if ip6tables -L PROTON_KS >/dev/null 2>&1; then
      ip6tables -I PROTON_KS -o "$IFACE"           -j RETURN 2>/dev/null || true
      ip6tables -I PROTON_KS -m mark --mark "$TABLE" -j RETURN 2>/dev/null || true
    fi

    log "Tunnel $IFACE (table $TABLE) up"
    ;;

  down)
    log "Tearing down routing for $IFACE (table $TABLE)"

    ip rule del fwmark "$TABLE" table "$TABLE" priority "$TABLE" 2>/dev/null || true
    ip route flush table "$TABLE" 2>/dev/null || true
    ip -6 rule del fwmark "$TABLE" table "$TABLE" priority "$TABLE" 2>/dev/null || true
    ip -6 route flush table "$TABLE" 2>/dev/null || true

    iptables  -t nat -D POSTROUTING -s 10.10.0.0/24    -o "$IFACE" -j MASQUERADE 2>/dev/null || true
    ip6tables -t nat -D POSTROUTING -s fd00:10:10::/64 -o "$IFACE" -j MASQUERADE 2>/dev/null || true

    iptables  -D PROTON_KS -o "$IFACE"           -j RETURN 2>/dev/null || true
    iptables  -D PROTON_KS -m mark --mark "$TABLE" -j RETURN 2>/dev/null || true
    ip6tables -D PROTON_KS -o "$IFACE"           -j RETURN 2>/dev/null || true
    ip6tables -D PROTON_KS -m mark --mark "$TABLE" -j RETURN 2>/dev/null || true

    log "Tunnel $IFACE (table $TABLE) down"
    ;;
esac
```

### Per-client routing

This reads `/etc/wireguard/proton.conf` and installs mangle-PREROUTING `MARK` rules so each client peer's packets get tagged with the right tunnel's table ID. It runs once at boot via systemd, and on-demand via `sudo proton-routing.sh reload` after editing `proton.conf`.

```bash
sudo nano /usr/local/bin/proton-routing.sh
sudo chmod 755 /usr/local/bin/proton-routing.sh
```

```bash
#!/bin/bash
# /usr/local/bin/proton-routing.sh
# Applies wg0-client → tunnel mangle MARK rules from /etc/wireguard/proton.conf.
set -euo pipefail

CONFIG="/etc/wireguard/proton.conf"
LOG_TAG="proton-routing"
COMMENT="proton-routing-managed"
log() { logger -t "$LOG_TAG" "$*"; echo "[$(date '+%H:%M:%S')] $*"; }
die() { log "ERROR: $*"; exit 1; }

[[ -f "$CONFIG" ]] || die "Config not found: $CONFIG"
# shellcheck source=/dev/null
source "$CONFIG"

declare -A TUNNEL_TABLE
for entry in "${TUNNELS[@]}"; do
  IFS=: read -r iface table _country <<< "$entry"
  TUNNEL_TABLE["$iface"]="$table"
done

flush_rules() {
  log "Flushing managed mangle rules..."
  for chain in PREROUTING OUTPUT; do
    while iptables -t mangle -L "$chain" --line-numbers 2>/dev/null | grep -q "$COMMENT"; do
      local line
      line=$(iptables -t mangle -L "$chain" --line-numbers 2>/dev/null | grep "$COMMENT" | head -1 | awk '{print $1}')
      iptables -t mangle -D "$chain" "$line" 2>/dev/null || break
    done
    while ip6tables -t mangle -L "$chain" --line-numbers 2>/dev/null | grep -q "$COMMENT"; do
      local line
      line=$(ip6tables -t mangle -L "$chain" --line-numbers 2>/dev/null | grep "$COMMENT" | head -1 | awk '{print $1}')
      ip6tables -t mangle -D "$chain" "$line" 2>/dev/null || break
    done
  done
}

apply_rules() {
  local applied=0
  for entry in "${CLIENTS[@]}"; do
    IFS=: read -r label client_ip tunnel_iface <<< "$entry"
    local table="${TUNNEL_TABLE[$tunnel_iface]:-}"
    if [[ -z "$table" ]]; then
      log "WARN: client '$label': tunnel '$tunnel_iface' not in TUNNELS — skipping"
      continue
    fi
    log "  $label ($client_ip) → $tunnel_iface (mark $table)"

    iptables -t mangle -A PREROUTING -s "$client_ip" \
      -m comment --comment "$COMMENT" -j MARK --set-mark "$table"

    # IPv6: derive the corresponding fd00:10:10::N from 10.10.0.N
    local last_octet="${client_ip##*.}"
    ip6tables -t mangle -A PREROUTING -s "fd00:10:10::${last_octet}/128" \
      -m comment --comment "$COMMENT" -j MARK --set-mark "$table" 2>/dev/null || true

    applied=$(( applied + 1 ))
  done

  # Default fallback for unlisted clients
  if [[ -n "${DEFAULT_TUNNEL:-}" ]]; then
    local default_table="${TUNNEL_TABLE[$DEFAULT_TUNNEL]:-}"
    if [[ -n "$default_table" ]]; then
      log "  Default → $DEFAULT_TUNNEL (mark $default_table)"
      iptables -t mangle -A PREROUTING -i "$WG_CLIENT_IFACE" \
        -m mark --mark 0 -m comment --comment "$COMMENT" \
        -j MARK --set-mark "$default_table"
      ip6tables -t mangle -A PREROUTING -i "$WG_CLIENT_IFACE" \
        -m mark --mark 0 -m comment --comment "$COMMENT" \
        -j MARK --set-mark "$default_table" 2>/dev/null || true
    fi
  fi
  log "Applied $applied client rules."
}

case "${1:-apply}" in
  apply)  apply_rules ;;
  flush)  flush_rules ;;
  reload) flush_rules; apply_rules; log "Reload complete." ;;
  *) die "Unknown action. Use: apply | flush | reload" ;;
esac
```

### Health-check daemon

```bash
sudo nano /usr/local/bin/proton-healthcheck.sh
sudo chmod 755 /usr/local/bin/proton-healthcheck.sh
```

```bash
#!/bin/bash
# /usr/local/bin/proton-healthcheck.sh
# Per-tunnel liveness via ping through the iface. On failure: restart wg-quick@iface.
# If restart fails: reroute affected clients to DEFAULT_TUNNEL (or first healthy alt).
set -uo pipefail

CONFIG="/etc/wireguard/proton.conf"
LOG_TAG="proton-health"
ROUTING="/usr/local/bin/proton-routing.sh"
log() { logger -t "$LOG_TAG" "$*"; echo "[$(date '+%H:%M:%S')] $*"; }

[[ -f "$CONFIG" ]] || { log "ERROR: $CONFIG not found"; exit 1; }
# shellcheck source=/dev/null
source "$CONFIG"

declare -A FAIL_COUNT TUNNEL_DOWN TUNNEL_TABLE
for entry in "${TUNNELS[@]}"; do
  IFS=: read -r iface table _country <<< "$entry"
  FAIL_COUNT["$iface"]=0
  TUNNEL_DOWN["$iface"]=0
  TUNNEL_TABLE["$iface"]="$table"
done

check_tunnel() { ping -c 1 -W 5 -I "$1" "$HEALTH_CHECK_HOST" &>/dev/null; }

attempt_restart() {
  local iface="$1"
  log "WARN: attempting restart of wg-quick@${iface}"
  systemctl restart "wg-quick@${iface}" || return 1
  # Allow time for handshake to complete on cold paths — 5s is too short.
  sleep 15
  check_tunnel "$iface"
}

reroute_clients_away_from() {
  local dead_iface="$1" fallback="$DEFAULT_TUNNEL"
  if [[ "$dead_iface" == "$fallback" ]]; then
    for entry in "${TUNNELS[@]}"; do
      IFS=: read -r iface _ _ <<< "$entry"
      [[ "$iface" != "$dead_iface" && "${TUNNEL_DOWN[$iface]:-1}" == "0" ]] && { fallback="$iface"; break; }
    done
  fi
  [[ "$dead_iface" == "$fallback" ]] && { log "ERROR: no healthy tunnels — clients will lose connectivity (kill-switch active)"; return; }

  log "WARN: rerouting clients from $dead_iface → $fallback"
  local fallback_table="${TUNNEL_TABLE[$fallback]}"
  for entry in "${CLIENTS[@]}"; do
    IFS=: read -r label client_ip tunnel_iface <<< "$entry"
    if [[ "$tunnel_iface" == "$dead_iface" ]]; then
      log "    $label ($client_ip) → $fallback"
      iptables -t mangle -A PREROUTING -s "$client_ip" \
        -m comment --comment "proton-failover" -j MARK --set-mark "$fallback_table"
    fi
  done
}

restore_clients_to() {
  log "Tunnel $1 back UP — clearing failover overrides"
  while iptables -t mangle -L PREROUTING --line-numbers 2>/dev/null | grep -q "proton-failover"; do
    local line
    line=$(iptables -t mangle -L PREROUTING --line-numbers | grep "proton-failover" | head -1 | awk '{print $1}')
    iptables -t mangle -D PREROUTING "$line" 2>/dev/null || break
  done
  "$ROUTING" reload >/dev/null || true
}

log "Daemon started (interval ${HEALTH_CHECK_INTERVAL}s, ${HEALTH_CHECK_FAILURES} strikes to fail)"
while true; do
  for entry in "${TUNNELS[@]}"; do
    IFS=: read -r iface _ country <<< "$entry"
    if check_tunnel "$iface"; then
      if [[ "${TUNNEL_DOWN[$iface]}" == "1" ]]; then
        TUNNEL_DOWN[$iface]=0; FAIL_COUNT[$iface]=0
        restore_clients_to "$iface"
      fi
    else
      FAIL_COUNT[$iface]=$(( FAIL_COUNT[$iface] + 1 ))
      log "WARN: $iface ($country) failed (${FAIL_COUNT[$iface]}/${HEALTH_CHECK_FAILURES})"
      if (( FAIL_COUNT[$iface] >= HEALTH_CHECK_FAILURES )) && [[ "${TUNNEL_DOWN[$iface]}" == "0" ]]; then
        log "ERROR: $iface ($country) DOWN — attempting recovery"
        TUNNEL_DOWN[$iface]=1
        attempt_restart "$iface" || reroute_clients_away_from "$iface"
      fi
    fi
  done
  sleep "$HEALTH_CHECK_INTERVAL"
done
```

### Status display

```bash
sudo nano /usr/local/bin/proton-status.sh
sudo chmod 755 /usr/local/bin/proton-status.sh
```

```bash
#!/bin/bash
# /usr/local/bin/proton-status.sh — one-shot human overview.
# Run as root for full info: `sudo proton-status.sh` (or with `--no-ip` to skip exit-IP lookup).
CONFIG="/etc/wireguard/proton.conf"
[[ -f "$CONFIG" ]] || { echo "Config not found: $CONFIG"; exit 1; }
# shellcheck source=/dev/null
source "$CONFIG"

R='\033[0;31m'; G='\033[0;32m'; Y='\033[0;33m'; B='\033[0;34m'; C='\033[0;36m'; W='\033[1;37m'; N='\033[0m'
hr()  { printf "${B}──────────────────────────────────────────────────────────${N}\n"; }
hdr() { printf "\n${W}%s${N}\n" "$1"; hr; }

declare -A TUNNEL_TABLE TUNNEL_COUNTRY
for entry in "${TUNNELS[@]}"; do
  IFS=: read -r iface table country <<< "$entry"
  TUNNEL_TABLE[$iface]="$table"; TUNNEL_COUNTRY[$iface]="$country"
done

check_tunnel_up() {
  ip link show "$1" >/dev/null 2>&1 && wg show "$1" >/dev/null 2>&1
}
last_handshake() {
  local ts; ts=$(wg show "$1" latest-handshakes 2>/dev/null | awk '{print $2}' | head -1)
  [[ -z "$ts" || "$ts" == 0 ]] && { echo "never"; return; }
  local ago=$(( $(date +%s) - ts ))
  if   (( ago < 60 )); then echo "${ago}s"
  elif (( ago < 3600 )); then echo "$(( ago/60 ))m"
  else echo "$(( ago/3600 ))h$(( (ago%3600)/60 ))m"
  fi
}
get_exit_ip() {
  curl -s --interface "$1" --max-time 5 https://ipinfo.io/ip 2>/dev/null || echo "?"
}

echo; printf "${W}  ProtonVPN multi-tunnel status${N}  $(date '+%a %d %b %H:%M:%S')\n"; hr
hdr "  Tunnels"
for entry in "${TUNNELS[@]}"; do
  IFS=: read -r iface table country <<< "$entry"
  if check_tunnel_up "$iface"; then
    printf "  ${W}%-14s${N} ${G}● up${N}  table=%s  country=%s\n" "$iface" "$table" "$country"
    printf "    handshake: %s ago\n" "$(last_handshake "$iface")"
    [[ "${1:-}" != "--no-ip" ]] && printf "    exit IP:   %s\n" "$(get_exit_ip "$iface")"
  else
    printf "  ${W}%-14s${N} ${R}● down${N} table=%s  country=%s\n" "$iface" "$table" "$country"
  fi
done

hdr "  Client routing"
printf "  %-12s  %-16s  %-14s  %-6s  %s\n" "Label" "Peer IP" "Tunnel" "Mark" "Status"
hr
for entry in "${CLIENTS[@]}"; do
  IFS=: read -r label client_ip tunnel_iface <<< "$entry"
  table="${TUNNEL_TABLE[$tunnel_iface]:-?}"
  country="${TUNNEL_COUNTRY[$tunnel_iface]:-?}"
  if iptables -t mangle -L PREROUTING -n 2>/dev/null | grep -q "$client_ip"; then
    printf "  %-12s  %-16s  %-14s  %-6s  ${G}active${N}  (%s)\n" "$label" "$client_ip" "$tunnel_iface" "$table" "$country"
  else
    printf "  %-12s  %-16s  %-14s  %-6s  ${R}missing${N} (%s)\n" "$label" "$client_ip" "$tunnel_iface" "$table" "$country"
  fi
done

hdr "  Failover overrides"
fover=$(iptables -t mangle -L PREROUTING -n 2>/dev/null | grep "proton-failover")
[[ -z "$fover" ]] && echo "  ${G}none${N}" || echo "$fover" | sed "s/^/  ${Y}/;s/$/${N}/"

hdr "  System"
printf "  Uptime:    %s\n" "$(uptime -p)"
printf "  WG dyndbg: "
if grep -q "wireguard" /sys/kernel/debug/dynamic_debug/control 2>/dev/null; then
  printf "${G}enabled${N}\n"
else
  printf "${Y}disabled${N}  (enable with: echo 'module wireguard +p' | sudo tee /sys/kernel/debug/dynamic_debug/control)\n"
fi
echo
```

### systemd units

Three separate files. The first creates the kill-switch chain *before* any wg-quick@protonvpn* starts; the second applies client→tunnel routing *after* all tunnels are up; the third runs the health-check daemon continuously.

```bash
sudo tee /etc/systemd/system/proton-killswitch-init.service >/dev/null <<'EOF'
[Unit]
Description=ProtonVPN kill-switch chain (PROTON_KS) initialiser
After=network-pre.target
Before=wg-quick@protonvpn0.service wg-quick@protonvpn1.service wg-quick@protonvpn2.service
DefaultDependencies=no

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/proton-killswitch-init.sh up
ExecStop=/usr/local/bin/proton-killswitch-init.sh down
StandardOutput=journal
StandardError=journal
SyslogIdentifier=proton-killswitch

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/proton-routing.service >/dev/null <<'EOF'
[Unit]
Description=ProtonVPN client routing marks (wg0 peers → tunnels)
After=network-online.target proton-killswitch-init.service
Wants=network-online.target
# Per-tunnel wg-quick units pull in their own dependencies; not enumerated here so
# adding a new protonvpnN doesn't require editing this file.

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/proton-routing.sh apply
ExecStop=/usr/local/bin/proton-routing.sh flush
ExecReload=/usr/local/bin/proton-routing.sh reload
StandardOutput=journal
StandardError=journal
SyslogIdentifier=proton-routing

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/proton-healthcheck.service >/dev/null <<'EOF'
[Unit]
Description=ProtonVPN tunnel health-check and failover daemon
After=proton-routing.service
Wants=proton-routing.service
# Throttle restart loop — a config-error crash shouldn't fill journal.
StartLimitBurst=5
StartLimitIntervalSec=300

[Service]
Type=simple
ExecStart=/usr/local/bin/proton-healthcheck.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=proton-health

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
```

> ⚠️ Notice that `proton-killswitch-init.service`'s `Before=` line enumerates a hardcoded set of `wg-quick@protonvpn*.service` units. Systemd does not support globbing in `Before=` / `After=`. If you add `protonvpn3`/`protonvpn4`, edit this unit and append them to the `Before=` line, then `systemctl daemon-reload`. The TUNNELS array in `proton.conf` is the source of truth for runtime behaviour; the systemd `Before=` is only there for boot ordering and is fine if a tunnel isn't listed — it just means the chain race-condition is theoretically possible on that one tunnel.

### Migration from the single-tunnel design

If you're upgrading from v5.1.7.20 or earlier:

```bash
# 1. Stop and disable the old single-tunnel setup.
sudo systemctl disable --now wg-quick@protonvpn

# 2. Remove the old WireGuard config and hook scripts.
#    (They'll be replaced by protonvpn0.conf, etc., plus the new helper scripts.)
sudo rm -f /etc/wireguard/protonvpn.conf
sudo rm -f /etc/wireguard/protonvpn-up.sh
sudo rm -f /etc/wireguard/protonvpn-down.sh

# 3. Confirm PROTON_KS chain and ip rules from the old setup are gone.
sudo iptables -L PROTON_KS 2>/dev/null && echo "STILL THERE — old chain wasn't torn down by wg-quick down"
sudo ip rule list | grep -E "fwmark 0xca6c"   # should print nothing now

# 4. Write the new files (proton.conf, protonvpn0.conf, protonvpn1.conf, all five scripts,
#    rt_tables append, three systemd units) per the steps above.

# 5. Enable everything in order.
sudo systemctl enable --now proton-killswitch-init.service
sudo systemctl enable --now wg-quick@protonvpn0
sudo systemctl enable --now wg-quick@protonvpn1
sudo systemctl enable --now proton-routing.service
sudo systemctl enable --now proton-healthcheck.service

# 6. Verify.
sudo proton-status.sh
```

### Verify

```bash
sudo proton-status.sh
```

Should show every tunnel `● up`, every client `active`, no `failover overrides`. Test the per-client egress from the actual client (after wg0 handshake completes):

```bash
# On the phone (assigned to protonvpn0 → Netherlands):
curl -s https://ipinfo.io/country    # expect: NL

# On the laptop (assigned to protonvpn1 → USA):
curl -s https://ipinfo.io/country    # expect: US
```

If `country` returns your home country, the mangle MARK isn't catching that client — `sudo proton-status.sh` will show `missing` under that client's row. Common cause: wrong `wg0_peer_ip` in `proton.conf` — verify with `sudo wg show wg0`.

### Operations

**Add a new tunnel (e.g. UK):**

1. Download a UK WireGuard config from Proton, save as `/etc/wireguard/protonvpn2.conf` with the [Interface] template (`Table = off`, `FwMark = 102`, MTU 1320, hooks calling `proton-tunnel-up.sh up %i 102`).
2. Append `"protonvpn2:102:UK"` to `TUNNELS=( ... )` in `/etc/wireguard/proton.conf`.
3. Append `protonvpn2.service` to the `Before=` line in `/etc/systemd/system/proton-killswitch-init.service`. `systemctl daemon-reload`.
4. `sudo systemctl enable --now wg-quick@protonvpn2`.
5. `sudo systemctl reload proton-routing.service` (re-reads `proton.conf`).
6. `sudo proton-status.sh` — confirm protonvpn2 shows `● up` and the new mark is available for client assignment.

**Reassign a client to a different tunnel:**

Edit `/etc/wireguard/proton.conf`, change the tunnel in the client's line, then:

```bash
sudo systemctl reload proton-routing.service    # or: sudo proton-routing.sh reload
```

No reboot, no wg0 restart.

**Remove a tunnel:**

1. `sudo systemctl disable --now wg-quick@protonvpn2` (this calls `proton-tunnel-up.sh down` automatically).
2. Remove its line from `TUNNELS=( ... )` and any clients still pointing at it (move them to another tunnel first or they'll fall to `DEFAULT_TUNNEL`).
3. `sudo systemctl reload proton-routing.service`.
4. Optionally remove `/etc/wireguard/protonvpn2.conf` and the `rt_tables` line (102 proton2).

### Useful queries

```bash
sudo proton-status.sh                       # full overview (with --no-ip for fast)
journalctl -ft proton-health                # live failover log
journalctl -ft proton-routing               # live routing-apply log
sudo iptables -t mangle -L PREROUTING -nv   # what's actually marking traffic
sudo ip rule show                           # what routes by fwmark
sudo ip route show table 100                # protonvpn0's table
sudo iptables -L PROTON_KS -nv              # kill-switch chain + counters
```

## 5. WireGuard Remote Access — wg0

This single interface handles your phone, laptop, and any future roaming device. **No wg1** — site-to-site only earns its keep when there's a real LAN at the far end.

### Generate keys

```bash
cd /etc/wireguard
wg genkey | sudo tee wg0-private.key | wg pubkey | sudo tee wg0-public.key
sudo chmod 600 wg0-private.key
cat wg0-public.key   # save — you'll paste this into client configs
```

### wg0 config on the Pi

```bash
sudo nano /etc/wireguard/wg0.conf
```

```ini
[Interface]
Address = 10.10.0.1/24, fd00:10:10::1/64
ListenPort = 51820
PrivateKey = <wg0-private-key>
# FIX #117 (updated for v5.1.7.21 multi-tunnel design):
# Sets fwmark 51820 on wg0's UDP socket. Why this specific number:
#   - In the single-tunnel design (≤ v5.1.7.20), ProtonVPN's wg-quick auto-assigned
#     51820 as its own fwmark and auto-installed the matching ip rule + kill-switch
#     RETURN. Reusing 51820 for wg0 piggybacked on Proton's infrastructure for free.
#   - In the v5.1.7.21+ multi-tunnel design, wg-quick auto-routing is disabled
#     (`Table = off` in each protonvpnN.conf), so the 51820 ip rule and PROTON_KS
#     exemption are no longer auto-installed. They are now installed EXPLICITLY by
#     /usr/local/bin/proton-killswitch-init.sh: the chain's `--mark 51820 -j RETURN`
#     line, plus no ip rule (wg0 protocol traffic falls through to the default main
#     table which routes via eth0). Same end result — wg0 handshake responses egress
#     via eth0 with source IP 192.168.70.5 and bypass the kill switch — different
#     plumbing.
# Failure mode if removed: tcpdump on eth0 shows inbound length-148 handshake
# initiations from remote clients with NO outbound length-92 response; the reply
# gets stuck in the kill switch's final REJECT because no PROTON_KS rule matched.
# Verify after restart: `sudo wg show wg0 fwmark` → `0xca6c` (= 51820 decimal).
FwMark = 51820
# 1280 — safe floor for a wg0-inside-protonvpn stack. At 1320 the outer
# protonvpn encapsulation (~60 B overhead) pushes packets past protonvpn's
# own 1320-byte MTU, causing fragmentation or silent large-transfer stalls.
# 1280 is the IPv6 minimum MTU and a reliable rule of thumb for stacked
# WireGuard tunnels. Set clients to match (see client config below).
MTU = 1280

# Forward + NAT into LAN — clients see traffic as from Pi, no router static route needed
# The RELATED,ESTABLISHED rule on egress is stateful — only return traffic for
# sessions initiated from inside wg0 is let back out uninspected.
# IPv6: clients carry ULA addresses inside the tunnel. They reach v6 internet
# via the Proton tunnel (Proton hands out v6 in the tunnel). If you don't have
# v6 working through Proton, leave the ip6tables MASQUERADE off and clients
# will simply have no v6 connectivity (which is the safe default — better than
# leaking).
PostUp  = iptables -A FORWARD -i wg0 -j ACCEPT
PostUp  = iptables -A FORWARD -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT
PostUp  = iptables -t nat -A POSTROUTING -s 10.10.0.0/24 -d 192.168.68.0/22 -j MASQUERADE
# ip6tables FORWARD rules are unconditional — they allow the tunnel to carry IPv6
# regardless of whether MASQUERADE is added. IPv6 internet access for clients
# requires Proton to hand out a v6 address (which it does). If you don't have
# v6 working through Proton, clients will simply have no v6 internet connectivity
# (safe default — better than leaking). The FORWARD rules themselves are always needed.
PostUp  = ip6tables -A FORWARD -i wg0 -j ACCEPT
PostUp  = ip6tables -A FORWARD -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT
PreDown = iptables -D FORWARD -i wg0 -j ACCEPT
PreDown = iptables -D FORWARD -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT
PreDown = iptables -t nat -D POSTROUTING -s 10.10.0.0/24 -d 192.168.68.0/22 -j MASQUERADE
PreDown = ip6tables -D FORWARD -i wg0 -j ACCEPT
PreDown = ip6tables -D FORWARD -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# --- Phone ---
[Peer]
PublicKey = <phone-public-key>
AllowedIPs = 10.10.0.2/32, fd00:10:10::2/128

# --- Laptop ---
[Peer]
PublicKey = <laptop-public-key>
AllowedIPs = 10.10.0.3/32, fd00:10:10::3/128
```

### Enable

```bash
sudo systemctl enable --now wg-quick@wg0
sudo wg show wg0
```

### Client config — full tunnel (recommended)

Phone/laptop config: home LAN reachable + internet flows phone → Pi → Proton (Pi-hole + Proton on the road). The `::/0` in AllowedIPs is the critical line that v3 was missing — without it, any host IPv6 connectivity (almost universal on mobile data and home WiFi now) routes around the tunnel and leaks your real address.

```ini
[Interface]
PrivateKey = <client-private-key>
Address = 10.10.0.2/32, fd00:10:10::2/128   # .3 / ::3 for the laptop
# FIX #110: removed `fd00:10:10::1` from DNS. Pi-hole's container only binds
# port 53 on IPv4 (Docker doesn't manage ip6tables unless `"ip6tables": true`
# is in daemon.json — see FIX #108 in §3 docker-user-rules.sh). Nothing on
# the Pi actually listens on `[fd00:10:10::1]:53`, so v6-first clients would
# send the first query to the v6 server, time out, then fall back to v4 —
# adding latency and occasional "DNS is flaky" reports.
#
# The earlier comment claimed v6-first OSes "bypass Pi-hole" if only a v4 DNS
# is listed. That's a misconception: WireGuard clients pin the resolver in
# the tunnel profile, so the OS sends ALL DNS (A AND AAAA queries) to the
# configured server(s) regardless of network preference. With AllowedIPs =
# 0.0.0.0/0, ::/0 the entire tunnel — including v4 DNS traffic — flows
# through the wg0/Pi-hole/Proton chain. No leak.
#
# If you ever enable Docker IPv6 in §3 and expose Pi-hole on v6 too, you can
# re-add fd00:10:10::1 here.
DNS = 10.10.0.1                              # Pi-hole over wg0 v4
MTU = 1280                                 # match server — see wg0.conf note

[Peer]
PublicKey = <wg0-public-key>
Endpoint = greenhouse.tplinkdns.com:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

### Client config — split tunnel (alternative)

If you want local internet to stay local and only home LAN to flow over the tunnel:

```ini
AllowedIPs = 192.168.68.0/22, 10.10.0.0/24, fd00:10:10::/64
```

> On Android/iOS, the WireGuard app sometimes ignores the `DNS = ` line in pasted config text. Open the imported tunnel and confirm "DNS servers" shows `10.10.0.1` in the UI.

---

## 6. Pi-hole + Unbound

**Stack name in Portainer:** `dns`

> ⚠️ **Pi-hole v6 migration.** v6 (Alpine base, complete rewrite) uses a new `FTLCONF_*` env var schema and is a one-way upgrade. If you previously ran v5 (e.g. `pihole/pihole:2024.07.0`), back up your `pihole-data` volume before deploying this stack and read [the v6 release notes](https://pi-hole.net/blog/2025/02/18/introducing-pi-hole-v6/). Old env vars (`WEBPASSWORD`, `DNSMASQ_LISTENING`, `PIHOLE_DNS_`, `DNSSEC`) will be silently ignored.

Save to disk and deploy:

```bash
sudo nano /opt/dns/docker-compose.yml
```

```yaml
services:
  unbound:
    image: mvance/unbound-rpi:1.22.0
    container_name: unbound
    restart: unless-stopped
    networks:
      dns-net:
        ipv4_address: 172.30.0.2

  pihole:
    image: pihole/pihole:2026.04.0
    container_name: pihole
    restart: unless-stopped
    environment:
      TZ: "Europe/Rome"
      # Secrets via Portainer env vars panel, NOT this YAML:
      #   FTLCONF_webserver_api_password   <-- set in Portainer Stack env
      FTLCONF_dns_upstreams: "172.30.0.2"   # FIX #107: Unbound at 172.30.0.2, port 53 (default — no #port). The mvance/unbound-rpi image listens on 53; the "#5335" convention is for bare-metal setups where Unbound must dodge Pi-hole's own :53.
      FTLCONF_dns_dnssec: "false"          # Unbound already validates — no double-validation
      FTLCONF_dns_listeningMode: "ALL"
      FTLCONF_webserver_port: "8080"        # admin UI on 8080; HTTP only (no TLS — Caddy terminates it)
      FTLCONF_webserver_tls_port: "-1"     # disable HTTPS on the Pi-hole container; Caddy handles TLS
    volumes:
      - pihole-data:/etc/pihole
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      # Admin UI bound to loopback only; reach via Caddy at pihole.home.arpa
      - "127.0.0.1:8080:8080/tcp"
    networks:
      dns-net:
        ipv4_address: 172.30.0.3
      proxy-net:
        ipv4_address: 172.31.0.14
    depends_on:
      - unbound

networks:
  dns-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/24
          gateway: 172.30.0.1
  proxy-net:
    external: true

volumes:
  pihole-data:
```

> 🔑 **In Portainer:** under the `dns` stack's **Environment variables** panel, add `FTLCONF_webserver_api_password=<long-strong-password>`. Do not put it in the YAML.

```bash
# Save the file above to disk, then deploy via Portainer:
# Stacks → + Add stack → name: dns → Web editor → paste YAML
# → Environment variables → add FTLCONF_webserver_api_password
# → Deploy
# CLI fallback (set the env var inline or via .env file next to compose.yml):
cd /opt/dns && FTLCONF_webserver_api_password='...' docker compose up -d
```

**Why we dropped `/etc/dnsmasq.d` from volumes:** v6 collapses everything into `/etc/pihole/pihole.toml`. The old `pihole-dnsmasq` volume is unused starting at v6 and adding it back will trigger a one-time migration on first start (harmless but confusing).

> ⚠️ **If upstream resolution fails after deploying:** the `mvance/unbound-rpi` image listens on **port 53**, so `FTLCONF_dns_upstreams: "172.30.0.2"` (no port — FTL defaults to 53) is correct. The `#5335` port you may have seen in other Pi-hole + Unbound guides is for *bare-metal* setups, where Unbound and Pi-hole share a host and Unbound must avoid Pi-hole's own `:53`; it does **not** apply here and pointing FTL at `172.30.0.2#5335` makes it query a port nothing is listening on, so all resolution silently fails. If `nslookup google.com 192.168.70.5` times out, exec into Pi-hole and check `/etc/pihole/pihole.toml` — under `[dns]` the `upstreams` value should be `["172.30.0.2"]`. Confirm Unbound is actually answering on 53 with `docker exec pihole dig @172.30.0.2 -p 53 google.com` — if that returns an answer but Pi-hole still doesn't resolve, the problem is FTL's config, not Unbound.

### Add local DNS records (so `*.home.arpa` resolves)

Pi-hole's admin port is bound to `127.0.0.1` only — `http://192.168.70.5:8080/admin` is not reachable from the LAN. Caddy doesn't exist yet at this point in the guide (it's deployed in §8), so access via SSH tunnel:

```bash
ssh -L 8080:127.0.0.1:8080 pi@192.168.70.5
# then open http://127.0.0.1:8080/admin on your laptop
```

In the Pi-hole admin → **Local DNS → DNS Records**, add:

| Domain | IP |
|---|---|
| `ha.home.arpa` | `192.168.70.5` |
| `portainer.home.arpa` | `192.168.70.5` |
| `pihole.home.arpa` | `192.168.70.5` |
| `stepca.home.arpa` | `192.168.70.5` |
| `kuma.home.arpa` | `192.168.70.5` |

### Router DNS — primary AND secondary

In your router's DHCP settings:
- Primary DNS: `192.168.70.5`
- Secondary DNS: `9.9.9.9` (or another public resolver)

The secondary is intentional. If you only set primary and the Pi reboots, your house has no internet for 5 minutes. Yes, secondary will sometimes bypass Pi-hole during outages — that's the trade-off. If you want belt-and-braces, run a second Pi-hole on a Pi Zero 2 W and use it as secondary.

### Verify

```bash
nslookup google.com 192.168.70.5
nslookup ha.home.arpa 192.168.70.5    # should return 192.168.70.5
```

### Pin `/etc/resolv.conf` (deferred from §2)

Now that Pi-hole is confirmed working, pin `resolv.conf` so Ubuntu point-release updates and cloud-init can't reinstate the `systemd-resolved` symlink and silently overwrite it:

```bash
sudo chattr +i /etc/resolv.conf
```

> ℹ️ This is safe to run now because Pi-hole is up and serving DNS. If you ever need to update `resolv.conf` (e.g. change the fallback server), unpin it first: `sudo chattr -i /etc/resolv.conf`, edit, then re-pin.

---

## 7. Step-CA

**Stack name in Portainer:** `step-ca`

```bash
sudo nano /opt/step-ca/docker-compose.yml
```

```yaml
services:
  step-ca:
    image: smallstep/step-ca:0.28.4
    container_name: step-ca
    restart: unless-stopped
    ports:
      # Bound to loopback — reach via Caddy at stepca.home.arpa, or via
      # SSH tunnel during initial bootstrap before Caddy exists.
      - "127.0.0.1:9000:9000"
    volumes:
      - step-ca-data:/home/step
    environment:
      DOCKER_STEPCA_INIT_NAME: "Homelab CA"
      # FIX #92: DOCKER_STEPCA_INIT_PASSWORD is set in Portainer's stack env-vars
      # panel, NOT in this YAML — the YAML lives in git, the password does not.
      # Without this variable Step-CA generates a random password and prints it
      # to the container log exactly once on first start; if the user misses
      # that log line (or Docker log rotation ages it out) there is no recovery
      # short of destroying the step-ca-data volume and re-initialising the CA
      # (which then requires re-installing the new root cert on every device).
      # Setting it up front makes the password deterministic and recoverable
      # from the user's password manager. Same pattern as Pi-hole's
      # FTLCONF_webserver_api_password — see the callout below.
      # FIX #1: added "step-ca" (the Docker container name) as the first entry.
      # Caddy (§8) reaches Step-CA at this name for two distinct purposes — both
      # need the SAN to match or the TLS handshake aborts:
      #   (a) ACME conversation. Caddy's global `acme_ca https://step-ca:9000/...`
      #       opens a TLS connection where SNI presents `step-ca`; without the
      #       SAN, Caddy logs `tls: failed to verify certificate: x509: certificate
      #       is valid for [other names] not step-ca` and ACME registration fails.
      #       (Caddy validates against `acme_ca_root /etc/ssl/certs/homelab-root-ca.crt`,
      #       which is the same root that signed Step-CA's TLS — the issue isn't
      #       the chain, it's the hostname check.)
      #   (b) Reverse-proxy of stepca.home.arpa. The Caddyfile site for stepca uses
      #       `reverse_proxy https://step-ca:9000` with `tls_trusted_ca_certs` and
      #       again validates SNI against the cert's SANs.
      # (Earlier revisions tied this fix to "NPM's ACME client" — NPM never had
      # one for custom servers, see fix #114. Caddy does, which is why v5.1.7.17
      # dropped NPM entirely. The SAN remains load-bearing under the new stack.)
      # FIX #43: added "localhost" and "127.0.0.1" — bootstrap access via
      # `https://127.0.0.1:9000` over SSH tunnel needs the IP SAN, otherwise
      # clients get: x509: certificate is valid for [other IPs], not 127.0.0.1
      DOCKER_STEPCA_INIT_DNS_NAMES: "step-ca,localhost,127.0.0.1,berrypi5,192.168.70.5,stepca.home.arpa"
      DOCKER_STEPCA_INIT_PROVISIONER_NAME: "admin@berrypi5"
      DOCKER_STEPCA_INIT_ACME: "true"
    networks:
      proxy-net:
        ipv4_address: 172.31.0.11

networks:
  proxy-net:
    external: true

volumes:
  step-ca-data:
```

```bash
# Portainer → Stacks → + Add stack → name: step-ca → Web editor → paste YAML → Deploy
# CLI fallback (must pass DOCKER_STEPCA_INIT_PASSWORD inline — the Portainer
# env-vars panel obviously doesn't exist when running compose directly):
cd /opt/step-ca && DOCKER_STEPCA_INIT_PASSWORD='...' docker compose up -d
```

> 🔑 **In Portainer:** under the `step-ca` stack's **Environment variables** panel (the lower section of the Stack editor, *not* the YAML), add `DOCKER_STEPCA_INIT_PASSWORD=<long-strong-password>` **before clicking Deploy**. Generate it from your password manager and store it there. Do NOT put it in the YAML — the YAML lives in git, the password does not. Same pattern as Pi-hole's `FTLCONF_webserver_api_password`.
>
> The Step-CA image consumes `DOCKER_STEPCA_INIT_PASSWORD` exactly once on first start (when it generates the CA's signing keypair and writes the encrypted private key to the volume). Changing it later via env-var has no effect — the password is baked into the encrypted key file at init time. If you ever lose the password you must destroy the `step-ca-data` volume, re-initialise the CA, and re-install the new root cert on every device.
>
> The legacy approach (used in earlier revisions of this guide) was to let Step-CA generate a random password and extract it from `docker logs step-ca` on first start. That worked, but was fragile: the log line can be missed, and Docker log rotation can age it out within hours. Setting it up front via env-var is strictly better.

### Get root cert + ACME URL

```bash
# Save to /opt/step-ca/ — Caddy (§8) mounts this read-only so it can validate
# Step-CA's TLS cert when proxying to step-ca:9000 AND when talking ACME to it
# (Caddyfile global `acme_ca_root` + per-site `tls_trusted_ca_certs`).  No separate
docker exec step-ca cat /home/step/certs/root_ca.crt | sudo tee /opt/step-ca/homelab-root-ca.crt
cp /opt/step-ca/homelab-root-ca.crt ~/homelab-root-ca.crt    # for installing on devices
docker logs step-ca 2>&1 | grep -i acme
```

The ACME URL looks like `https://step-ca:9000/acme/acme/directory` from inside the `proxy-net` Docker network. Containers on `proxy-net` (Caddy specifically — see §8) reach it at that name; on the host you reach the same endpoint at `https://127.0.0.1:9000/acme/acme/directory` (Step-CA's port 9000 is published only on loopback) for ad-hoc `step` CLI use. Note this URL — it goes verbatim into the Caddyfile's `acme_ca` global option in §8.

Install `homelab-root-ca.crt` on every device — see the trust-store table at the bottom.

---

## 8. Caddy reverse proxy

v5.1.7.17 replaced Nginx Proxy Manager with Caddy. NPM was a continuing source of friction in this guide: no native custom-ACME-server support (the months of workarounds in fixes #1, #3, #14, #104, #114, and the v5.1.7.16 §8.5 acme.sh detour, were all working around that one missing feature), an s6-overlay PID-1 footgun that broke silently on image bumps, and a database-backed config that fought version control. Caddy speaks ACME against Step-CA natively in two Caddyfile lines, handles HTTP→HTTPS redirect and HTTP/3 automatically, and stores its entire config as a 30-line text file. The trade-off is no point-and-click proxy-host editor — adding a service means appending a stanza to a Caddyfile and `docker exec caddy caddy reload`.

### Remove NPM (one-time, only if upgrading from v5.1.7.16 or earlier)

Skip this if you're on a fresh install with no NPM history.

```bash
# 1. Stop and remove the NPM container.
docker stop npm 2>/dev/null && docker rm npm 2>/dev/null || true

# 2. Remove the NPM stack from Portainer.
#    Portainer → Stacks → npm → Remove → tick "Remove volumes too".
#    CLI fallback if the stack was deployed by hand: cd /opt/npm && docker compose down -v

# 3. Remove the named volumes if step 2 didn't catch them.
docker volume rm npm-data npm-ssl 2>/dev/null || true

# 4. Delete the on-disk stack directory.
sudo rm -rf /opt/npm

# 5. Tear down acme.sh if v5.1.7.16's §8.5 detour got installed.
if [ -d "$HOME/.acme.sh" ]; then
  "$HOME/.acme.sh/acme.sh" --uninstall 2>/dev/null || true
  rm -rf "$HOME/.acme.sh"
  # Drop the renewal cron line if it lingered after --uninstall.
  ( crontab -l 2>/dev/null | grep -v 'acme\.sh' ) | crontab - 2>/dev/null || true
fi

# 6. Pi-hole: delete the `npm.home.arpa` Local DNS record by hand:
#    Pi-hole admin → Local DNS → DNS Records → delete the npm.home.arpa row.
#    (Caddy doesn't need its own *.home.arpa proxy host — there's no admin UI to reach.)

# 7. Confirm ports 80/443 are now free on the host before Caddy comes up.
ss -ltnp '( sport = :80 or sport = :443 )'    # should print no LISTEN rows
```

### Stack name in Portainer: `caddy`

```bash
sudo mkdir -p /opt/caddy
sudo nano /opt/caddy/docker-compose.yml
```

```yaml
services:
  caddy:
    image: caddy:2.8.4-alpine
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"    # HTTP/3 (QUIC) — Caddy auto-enables it when 443/udp is published
    volumes:
      # Caddyfile is owned by root, edited via `sudo nano /opt/caddy/Caddyfile`, and
      # applied without restart via `docker exec caddy caddy reload --config /etc/caddy/Caddyfile`.
      - /opt/caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      # Named volumes hold all ACME state. /data contains the issued certs, private keys,
      # and the ACME account key registered with Step-CA. Losing it means re-registering
      # and re-issuing every cert.
      - caddy-data:/data
      - caddy-config:/config
      # Step-CA's root cert. Two consumers inside Caddy read this file directly:
      #   (a) Caddyfile global option `acme_ca_root` — validates Step-CA's TLS during the
      #       ACME conversation when Caddy connects to https://step-ca:9000.
      #   (b) Caddyfile site option `tls_trusted_ca_certs` on the stepca.home.arpa
      #       reverse_proxy — validates Step-CA's TLS when Caddy proxies it as a backend.
      # Caddy reads the file directly, so no system trust store / update-ca-certificates
      # plumbing is needed (this is what NPM's fix #3 entrypoint was doing).
      - /opt/step-ca/homelab-root-ca.crt:/etc/ssl/certs/homelab-root-ca.crt:ro
    networks:
      proxy-net:
        ipv4_address: 172.31.0.10

networks:
  proxy-net:
    external: true

volumes:
  caddy-data:
  caddy-config:
```

### Caddyfile

```bash
sudo nano /opt/caddy/Caddyfile
```

```Caddyfile
# Global options — apply to every site below.
{
    email forgottenshores@tutamail.com

    # Use Step-CA as the ACME issuer for every site. Caddy speaks ACME natively,
    # no acme.sh wrapper, no per-host nginx snippets, no NPM API deploy hooks.
    # The hostname `step-ca` resolves via Docker's embedded DNS on proxy-net,
    # which Caddy is also attached to.
    acme_ca https://step-ca:9000/acme/acme/directory

    # Trust Step-CA's TLS cert (signed by the homelab root) for the ACME conversation.
    # The file is mounted from /opt/step-ca/homelab-root-ca.crt on the host.
    acme_ca_root /etc/ssl/certs/homelab-root-ca.crt
}

# Home Assistant — host networking, so the backend is the host's eth0 IP rather than
# a container name. HA's configuration.yaml must also include the trusted_proxies
# block below (see callout after this code block).
ha.home.arpa {
    reverse_proxy 192.168.70.5:8123 {
        header_up X-Forwarded-For   {remote_host}
        header_up X-Forwarded-Proto {scheme}
        header_up X-Real-IP         {remote_host}
    }
}

# Portainer — HTTPS backend with its own self-signed cert. Caddy connects over TLS
# (the session cookie traffic stays encrypted on the wire between Caddy and Portainer)
# but skips validating Portainer's self-signed cert. Configure Portainer to use a
# Step-CA-issued cert if you want end-to-end chain validation; for a homelab the
# tls_insecure_skip_verify is the pragmatic call.
portainer.home.arpa {
    reverse_proxy https://portainer:9443 {
        transport http {
            tls
            tls_insecure_skip_verify
        }
    }
}

# Pi-hole admin — plain HTTP backend on the proxy-net bridge. Caddy terminates TLS;
# Pi-hole's `FTLCONF_webserver_tls_port: "-1"` (§6) keeps it from also doing TLS.
pihole.home.arpa {
    reverse_proxy pihole:8080
}

# Step-CA admin — HTTPS backend, cert signed by the homelab root which Caddy trusts
# via the same volume mount used for ACME. tls_trusted_ca_certs makes that explicit
# at this site so the connection validates without --insecure shortcuts.
stepca.home.arpa {
    reverse_proxy https://step-ca:9000 {
        transport http {
            tls
            tls_trusted_ca_certs /etc/ssl/certs/homelab-root-ca.crt
        }
    }
}

# Uptime Kuma — plain HTTP backend on the proxy-net bridge.
kuma.home.arpa {
    reverse_proxy uptime-kuma:3001
}
```

> ⚠️ **HA needs `trusted_proxies` in configuration.yaml.** With Caddy in front, HA sees every request coming from Caddy's static proxy-net IP (`172.31.0.10`) rather than the real client. Without trusted_proxies set, HA refuses `X-Forwarded-For` and the auth/history pages misbehave — and the IP-based ban list bans the proxy after a few wrong-password attempts. Add to `/opt/homeassistant/ha-config/configuration.yaml` (volume path: `docker volume inspect homeassistant_ha-config` shows the host path):
> ```yaml
> http:
>   use_x_forwarded_for: true
>   trusted_proxies:
>     - 172.31.0.10        # Caddy specifically — narrowed from /24 in v5.1.7.19 once Caddy got a static IP
>     - 127.0.0.1
>     - ::1
> ```
> Restart HA after editing (`docker restart homeassistant`). If you skipped the proxy-net static-IP convention in §3, widen this back to `172.31.0.0/24`.

Deploy:

```bash
# Portainer → Stacks → + Add stack → name: caddy → Web editor → paste YAML → Deploy
# CLI fallback:
cd /opt/caddy && docker compose up -d
```

On first start Caddy will:
1. Register an ACME account with Step-CA, one time, persisted in `caddy-data` so subsequent restarts don't re-register
2. Request a cert for every site in the Caddyfile in parallel — Step-CA's HTTP-01 validator hits each site's `http://<site>/.well-known/acme-challenge/<token>`, Caddy serves the response automatically (this is the part NPM couldn't do without the v5.1.7.16 thumbprint snippet)
3. Begin serving HTTPS on 443 with automatic HTTP→HTTPS redirect on 80

Watch first-boot:

```bash
docker logs -f caddy
# Healthy boot includes lines like:
#   "msg":"obtaining new certificate","identifier":"ha.home.arpa"
#   "msg":"certificate obtained successfully","identifier":"ha.home.arpa"
# repeated for all six sites.
# Errors:
#   "no challenges remaining" — DNS resolution failed (Step-CA can't resolve the site
#                                FQDN; verify fix #111's daemon.json `dns:` is live and
#                                Pi-hole has the *.home.arpa records from §6)
#   "x509: certificate signed by unknown authority" — acme_ca_root path is wrong or the
#                                                      root cert wasn't generated yet (§7)
#   "connection refused" on port 80 — UFW probably blocks 80/tcp; §2 should have allowed it
```

After deploy: open `https://ha.home.arpa` in a browser that has `homelab-root-ca.crt` installed (§14 trust-store table). You should see HA's login page with a valid cert and no warnings.

### Add a new proxied service later

Append a stanza, reload — no UI, no per-host snippets:

```bash
sudo nano /opt/caddy/Caddyfile
# Add e.g.:
#   newservice.home.arpa {
#       reverse_proxy newservice:8000
#   }
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Caddy validates the new config in-process and swaps it atomically — if validation fails, the old config keeps running and you have no downtime. Also remember:
1. Add `newservice.home.arpa` → `192.168.70.5` to Pi-hole's Local DNS records (§6)
2. Add a Kuma monitor for it (§13)

### Cert renewal

Automatic and continuous. No cron, no `--cron`, no deploy hook. Caddy polls its certs in the background and renews when ~⅓ of the lifetime remains. With Step-CA's default 24-hour ACME cert duration that means renewals every ~16 hours, which produces a lot of log noise. Bump the provisioner to 30-day certs:

```bash
docker exec step-ca step ca provisioner update acme \
  --x509-default-dur 720h --x509-max-dur 720h
docker restart step-ca
```

Caddy will pick up the longer-lived certs at the next renewal cycle. To force an immediate re-issue for a single site (useful for testing): `docker exec caddy rm -rf /data/caddy/certificates/acme-v02.step-ca-9000/<site>/` then `docker restart caddy`.

---

---

## 9. LAN Gateway — keep the router, not the Pi

Your chosen design: **only the Pi and its Docker containers go through ProtonVPN.** Other LAN devices (phone on WiFi, laptop, TV, etc.) use the home router as their gateway and reach the internet normally — no ProtonVPN, no Pi-hole-only-DNS bottleneck.

### What this means in practice

- **DHCP gateway stays as the router** (`192.168.68.1`). Don't change it.
- **DHCP DNS stays as the Pi** (`192.168.70.5`) with `9.9.9.9` secondary. LAN clients still get ad blocking — only their internet path bypasses Proton.
- The Pi's own outbound and Docker container outbound (Pi-hole's recursive lookups via Unbound, Caddy, HA telemetry, container image pulls, etc.) all flow through Proton.
- wg0 clients (your phone/laptop when remote) get full-tunnel: their internet flows phone → Pi → Proton.
- **If the Pi goes down, your house keeps internet.** Only DNS via Pi-hole stops, and clients fail over to the secondary DNS (`9.9.9.9`).

### Why this is the right call for your setup

| | Option A (Pi gateway) | **Option B (router gateway, chosen)** |
|---|---|---|
| LAN client → internet | via Proton | via ISP directly |
| Pi down = LAN dead? | Yes | No |
| Per-device control | All or nothing | Each device picks its path |
| Routing complexity | High | Low |
| ProtonVPN cost amortization | Used by everyone | Used only by services that need it |

If you ever want a specific device on Proton (TV, work laptop), set its gateway to `192.168.70.5` via DHCP reservation while everyone else keeps the router. That's how you graduate to a hybrid setup without rebuilding.

### No changes required to the configs above

The §4 ProtonVPN config and §5 wg0 config are already written for this exact topology. Move on to §10.

---

## 10. Home Assistant Container

> **Why not Supervised?** Officially, Supervised needs Debian 12 (HA project's words). On Ubuntu 24.04 it shows the unsupported-OS warning, breaks on AppArmor changes, and add-on support has been flaky after Ubuntu kernel updates. HA Container is officially supported, runs in your existing Docker stack, and doesn't fight Netplan or NetworkManager. The trade-off: no add-ons via the HA UI — but you can run those services as separate containers (Mosquitto, Zigbee2MQTT, ESPHome) and still have HA discover them.

**Stack name in Portainer:** `homeassistant`

> ⚠️ Home Assistant uses `network_mode: host` (required for mDNS, HomeKit, etc.). v3 used `privileged: true` as a shortcut for Bluetooth + USB access; v4 replaces this with explicit `cap_add` + `devices`, which is safer and recommended by both HA's docs and the linuxserver.io guide. You'll need to uncomment the device lines that match what's plugged into your Pi (Zigbee stick, Z-Wave stick, Bluetooth adapter, etc.).

```bash
sudo nano /opt/homeassistant/docker-compose.yml
```

```yaml
services:
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:2026.5
    container_name: homeassistant
    restart: unless-stopped
    network_mode: host           # required for mDNS, HomeKit, etc.
    # privileged: true           # removed in v4 — see cap_add + devices below
    cap_add:
      - NET_ADMIN                # network discovery, DHCP probe integrations
      - NET_RAW                  # ping integration
      - SYS_NICE                 # priority tuning for the recorder
      # - SYS_ADMIN              # only add if you actually use the supervisor-style integrations that demand it
    volumes:
      - ha-config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro   # Bluetooth via BlueZ on host
    # Uncomment the devices you actually have plugged in. Use stable
    # /dev/serial/by-id/* paths so a USB re-enumeration doesn't break HA.
    # devices:
    #   - /dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_xxxxxxx-if00-port0:/dev/ttyACM0
    #   - /dev/serial/by-id/usb-0658_0200-if00:/dev/ttyACM1                   # Z-Wave (Aeotec Z-Stick)
    environment:
      TZ: "Europe/Rome"

volumes:
  ha-config:
```

```bash
# Portainer → Stacks → + Add stack → name: homeassistant → Web editor → paste YAML → Deploy
# Then watch logs: Portainer → Stacks → homeassistant → homeassistant container → Logs
# CLI fallback:
cd /opt/homeassistant && docker compose up -d && docker logs -f homeassistant
```

Access `http://192.168.70.5:8123` and onboard.

If you need MQTT later (add as a service inside the `homeassistant` stack):

```yaml
  mosquitto:
    image: eclipse-mosquitto:2.0.21
    container_name: mosquitto
    restart: unless-stopped
    ports:
      # Bind to the LAN interface only, not 0.0.0.0 — MQTT brokers exposed
      # on every interface are a common foothold. The DOCKER-USER chain
      # would catch WAN access anyway, but tidier to scope at the bind.
      # HA uses network_mode: host. Because the port is bound to 192.168.70.5
      # (not 0.0.0.0 or 127.0.0.1), HA must reach Mosquitto at 192.168.70.5:1883
      # — NOT localhost:1883, which has nothing listening on it.
      - "192.168.70.5:1883:1883"
    volumes:
      - mosquitto-data:/mosquitto/data
      - mosquitto-log:/mosquitto/log
      # FIX #44: use absolute paths. Portainer's web-editor working directory is
      # '/', so './mosquitto.conf' resolves to '/mosquitto.conf' — a path that
      # doesn't exist. Docker creates it as a directory and Mosquitto fails to
      # parse its config. Absolute paths work for both Portainer and CLI deploys.
      # FIX #87: mosquitto.passwd mount is NOT :ro — the bootstrap instructions
      # below use `docker exec -it mosquitto mosquitto_passwd -c …` which writes
      # to this path; a read-only mount blocks the write with EACCES. The trade-
      # off is that a compromised Mosquitto container could rewrite its own
      # passwd file, but the running broker doesn't auto-reload it, so this is
      # a small security delta in exchange for the documented bootstrap working.
      # Pre-create both files at the host paths below before deploying (see
      # note below) — without that, Docker auto-creates the bind-mount source
      # as a *directory* on first deploy and Mosquitto fails to parse its config.
      - /opt/homeassistant/mosquitto.conf:/mosquitto/config/mosquitto.conf
      - /opt/homeassistant/mosquitto.passwd:/mosquitto/config/mosquitto.passwd
    # No 'networks:' needed — mosquitto ports are bound to the host IP above,
    # not to a Docker bridge. HA (network_mode: host) reaches it at 192.168.70.5:1883.
```

Add the required volume names to the existing top-level `volumes:` block (alongside `ha-config:`):

```yaml
volumes:
  ha-config:
  mosquitto-data:
  mosquitto-log:
```

> ⚠️ **Pre-create both files on the host before deploying.** If `/opt/homeassistant/mosquitto.conf` or `/opt/homeassistant/mosquitto.passwd` doesn't exist on the host when the stack is deployed, Docker auto-creates the missing bind-mount source as a **directory**, and Mosquitto then fails on config parse (same class of issue as fix #44 caught for relative paths). Create empty files first, then deploy:
> ```bash
> sudo touch /opt/homeassistant/mosquitto.conf /opt/homeassistant/mosquitto.passwd
> sudo chmod 600 /opt/homeassistant/mosquitto.passwd
> # edit /opt/homeassistant/mosquitto.conf to taste before deploying, then:
> # Portainer → Stacks → homeassistant → Update the stack
> ```

> 🔑 Put `password_file /mosquitto/config/mosquitto.passwd` in `mosquitto.conf` and `disable_anonymous true`. After deploying the stack, generate the password file with `docker exec -it mosquitto mosquitto_passwd -c /mosquitto/config/mosquitto.passwd <user>`. The password file is not in git; only `mosquitto.conf` is.
> ⚠️ The `-c` flag **creates** a new file, overwriting any existing one. Use it only for the first user. To add subsequent users without losing the first, omit `-c`: `docker exec -it mosquitto mosquitto_passwd /mosquitto/config/mosquitto.passwd <second-user>`.

---

## 11. PostgreSQL database server

Reserved for any future self-hosted web app you want to put on this Pi (Immich, Paperless-ngx, Forgejo, Authentik, Vaultwarden with the Postgres backend, etc. — all default to or recommend Postgres). The Postgres container itself sits idle until something connects to it; the "Adding a web app later" subsection at the bottom of this section is the full walkthrough for hooking one up.

**Why Postgres** (vs MariaDB/MySQL): the modern self-hosted ecosystem has converged hard on Postgres. JSONB, partial/expression indexes, `scram-sha-256` as the default password auth method since PG 14 (no `pg_hba.conf` ceremony), and `pg_dump`/`pg_dumpall` producing genuinely portable text dumps. The Alpine variant of the official image is ~80MB pulled vs ~150MB for the Debian variant, runs comfortably on the Pi 5's arm64v8, and PG 18 Alpine now ships `liburing`/io_uring async I/O which on NVMe-backed Pi 5s gives a measurable read-latency drop on concurrent workloads. MariaDB would be a reasonable second choice if you specifically need WordPress or a legacy PHP CMS, but nothing in this guide's likely future-app list needs MySQL-flavoured SQL.

> ⚠️ **No automated backup.** Restic (formerly §12) was removed in v5.1.7.19 (fix #122). This database has *zero* automated backup unless you add one. A `pg_dumpall` cron suggestion is at the bottom of this section — read it before putting anything you care about into this database. SSDs fail.

### Stack name in Portainer: `postgres`

### Pre-create the shared `db-net` bridge

Same one-time-up-front pattern §3 uses for `proxy-net`: every future web-app stack that needs the database attaches to `db-net` via `external: true`, so the network must exist before any stack references it. The subnet (`172.29.0.0/24`) sits below `dns-net` (`172.30.0.0/24`) and `proxy-net` (`172.31.0.0/24`), and crucially **outside the §3 daemon.json `default-address-pools` range `172.20.0.0/14`** (which covers `172.20–172.23.x`), so Docker's auto-allocator can't collide with it and no daemon.json edit is needed.

```bash
docker network create --driver bridge --subnet 172.29.0.0/24 db-net
```

Verify:

```bash
docker network ls | grep db-net
# Expect: <id>  db-net  bridge  local
docker network inspect db-net | grep -E 'Subnet|Gateway'
# Expect: "Subnet": "172.29.0.0/24", "Gateway": "172.29.0.1"
```

### Compose stack

```bash
sudo mkdir -p /opt/postgres
sudo nano /opt/postgres/docker-compose.yml
```

```yaml
services:
  postgres:
    image: postgres:18.4-alpine
    container_name: postgres
    restart: unless-stopped
    # No `ports:` published to the host. 5432 is reachable only from inside
    # db-net via Docker's embedded DNS as `postgres:5432`. The reasoning is
    # the same direction as fix #120's static-IP convention and the §3
    # loopback-binding default: every additional 127.0.0.1:* bind is one
    # more thing to firewall, one more thing DOCKER-USER (§3) has to reason
    # about, and one more attack surface. Admin happens via `docker exec`
    # — see the "Day-to-day admin" subsection below.
    environment:
      TZ: "Europe/Rome"
      # Secrets via Portainer env vars panel, NOT this YAML:
      #   POSTGRES_PASSWORD   <-- set in Portainer Stack env (or CLI fallback below)
      #
      # POSTGRES_USER defaults to `postgres` (the superuser). We leave it at
      # the default — per-app users are created separately via `psql` after
      # deploy, see "Per-app database and role creation" below.
      #
      # POSTGRES_DB unset — we don't want the entrypoint to auto-create a
      # named database called `postgres` (which is what setting it would do).
      # The default `postgres` DB exists anyway and is used only for admin
      # connections; real per-app DBs are created explicitly later.
      POSTGRES_INITDB_ARGS: "--locale=C.UTF-8 --encoding=UTF8"
      # --locale=C.UTF-8 + --encoding=UTF8 is the safe default: UTF-8 storage
      # without the en_US.UTF-8 sort order that pulls in glibc locale data
      # (which the Alpine base doesn't ship in full). C.UTF-8 is byte-sort,
      # fast, and stable across glibc versions. If a future app specifically
      # needs locale-aware ORDER BY (rare), override per-database at
      # CREATE DATABASE time with `LC_COLLATE='...' TEMPLATE template0`.
    volumes:
      # ⚠️ Path is /var/lib/postgresql, NOT /var/lib/postgresql/data.
      # PG 18 changed both PGDATA and the declared VOLUME — PGDATA moved
      # from /var/lib/postgresql/data to /var/lib/postgresql/18/docker, and
      # the VOLUME declared by the image moved from /var/lib/postgresql/data
      # to /var/lib/postgresql (parent dir). docker-library/postgres#1259.
      # Mounting the old path on PG 18 produces:
      #   Error: ... configured to store database data in a format which is
      #   compatible with "pg_ctlcluster" ... Counter to that, there appears
      #   to be PostgreSQL data in: /var/lib/postgresql/data (unused
      #   mount/volume)
      # ... and the container won't start. Mounting the parent /var/lib/
      # postgresql also future-proofs pg_upgrade between major versions:
      # PG 19's PGDATA will be /var/lib/postgresql/19/docker (sibling of
      # 18/docker under the same mount), which is what lets pg_upgrade
      # --link work without crossing a mount-point boundary. See the §15
      # troubleshooting row keyed off the "(unused mount/volume)" message
      # for the recovery path if you hit this from an upgrade.
      - postgres-data:/var/lib/postgresql
      - /etc/localtime:/etc/localtime:ro
    # PG default shm_size is 64 MB — fine for an idle DB, undersized once a
    # web app starts doing parallel queries (each parallel worker allocates
    # against shared memory). 256 MB is the comfortable headroom for a
    # multi-app Pi 5 homelab without giving Postgres so much RAM that
    # Home Assistant or Pi-hole start swapping. Override upward via
    # `docker compose down && docker compose up -d` if you add a heavy app
    # like Immich (their docs recommend 256+ MB for transcoding pipelines).
    shm_size: 256mb
    healthcheck:
      # pg_isready is the canonical "is the server accepting connections"
      # check; it exits 0 if the listener is up, non-zero otherwise. Don't
      # use `psql -c 'SELECT 1'` here — psql connects as a real client and
      # increments login-attempt counters on every invocation, which clutters
      # pg_stat_activity. pg_isready uses a lightweight protocol-level check.
      test: ["CMD", "pg_isready", "-U", "postgres", "-d", "postgres"]
      interval: 30s
      timeout: 5s
      retries: 5
      # start_period gives initdb time to finish on first deploy (creating
      # the cluster, running initdb, etc. takes ~10-15s on a Pi 5 NVMe).
      # Without it, the first ~5 healthchecks fail noisily during normal
      # bootstrap and Portainer flags the stack red for the first minute.
      start_period: 30s
    # FIX #122 cross-reference: Restic (formerly §12) was removed in v5.1.7.19,
    # so this volume is NOT in any automated backup. See the "Backups" subsection
    # below for the manual pg_dumpall pattern.
    networks:
      db-net:
        ipv4_address: 172.29.0.10

networks:
  db-net:
    external: true

volumes:
  postgres-data:
```

> 🔑 **In Portainer:** under the `postgres` stack's **Environment variables** panel, add `POSTGRES_PASSWORD=<long-strong-password>`. Do not put it in the YAML. This is the superuser (`postgres` role) password — store it in your password manager, you will need it for per-app role creation below. Same convention §6 Pi-hole's `FTLCONF_webserver_api_password` and §7 Step-CA's `DOCKER_STEPCA_INIT_PASSWORD` use.

```bash
# Save the file above to disk, then deploy via Portainer:
# Stacks → + Add stack → name: postgres → Web editor → paste YAML
# → Environment variables → add POSTGRES_PASSWORD
# → Deploy
# CLI fallback (set the env var inline so the entrypoint sees it on first init;
# matches the pattern fix #101/#102 established for the dns and watchtower stacks):
cd /opt/postgres && POSTGRES_PASSWORD='...' docker compose up -d
```

> ⚠️ **`POSTGRES_PASSWORD` is only consulted on first init** (i.e. when the `postgres-data` volume is empty). Once initdb runs and the cluster is created, the password is set on the `postgres` role in the database and the env var is ignored on subsequent restarts. To **change** the superuser password later, do not just edit the env var — connect with the current password and run `ALTER USER postgres WITH PASSWORD '...';`. If you've lost the current password, the recovery path is: stop the container, set `POSTGRES_HOST_AUTH_METHOD=trust` temporarily via a compose env override, restart, `ALTER USER postgres WITH PASSWORD '...';`, remove the override, restart again. Document the new password in your password manager before unsetting trust.

### Verify

```bash
# Listener is up and accepting connections:
docker exec -it postgres pg_isready -U postgres
# Expect: /var/run/postgresql:5432 - accepting connections

# Cluster initialised cleanly with the three default databases:
docker exec -it postgres psql -U postgres -c '\l'
# Expect 3 rows: postgres, template0, template1 — all owned by `postgres`,
# encoding UTF8, ctype C.UTF-8, collate C.UTF-8

# PG 18 PGDATA layout is correct (sanity check for fix above):
docker exec -it postgres ls /var/lib/postgresql/18/docker
# Expect: PG_VERSION, base/, global/, pg_wal/, postgresql.conf, ... — the real
# data directory. If you see just `data/` containing those entries instead,
# you've mounted the old PG 17 path; see the §15 troubleshooting row.

# Network reachability from another container on db-net (no app yet, so we
# use a throwaway alpine container attached to db-net for the test):
docker run --rm --network db-net alpine:3.21 sh -c \
  "apk add --no-cache postgresql-client >/dev/null && pg_isready -h postgres -p 5432 -U postgres"
# Expect: postgres:5432 - accepting connections
```

### Per-app database and role creation

Each web app should get its own database AND its own role (don't share the `postgres` superuser with apps — a compromised app shouldn't be able to drop other apps' databases). The pattern, run once per new app:

```bash
docker exec -it postgres psql -U postgres
```

```sql
-- Create a per-app role with a per-app password.
CREATE ROLE myapp WITH LOGIN PASSWORD 'long-random-per-app-password';

-- Create the database, owned by that role (so the role can create extensions etc.).
CREATE DATABASE myapp_db OWNER myapp;

-- Lock down: the role only sees its own database. PUBLIC defaults in
-- PG 15+ already block cross-database read for non-superusers, but
-- belt-and-braces:
REVOKE CONNECT ON DATABASE postgres FROM myapp;
REVOKE ALL ON DATABASE template0, template1 FROM myapp;

\q
```

The connection string for the app to use:

```
postgresql://myapp:long-random-per-app-password@postgres:5432/myapp_db
```

Where `postgres` is the container name (resolved via Docker embedded DNS on db-net), `5432` is the standard PG port, and `myapp_db` is the per-app database.

> ℹ️ **Why not `/docker-entrypoint-initdb.d/*.sql` mounts.** The official image runs `.sql`/`.sh` files in that directory on first init (i.e. when PGDATA is empty), but **only on first init** — never on subsequent starts. Using it for per-app schemas means a redeploy from an existing volume silently skips role/DB creation, while a redeploy after a volume wipe re-runs it. That divergence is exactly the kind of "behaviour depends on hidden volume state" footgun the rest of this guide spends pages avoiding. Manual `psql` is reproducible, version-controllable, and visible.

> 💾 **Document the per-app passwords.** Store each app's database password in your password manager next to the app's other credentials. Web app compose YAMLs reference the password via Portainer env vars (same pattern as `POSTGRES_PASSWORD` itself), never in the YAML committed to git. See "Adding a web app later" below for the worked compose snippet.

### Day-to-day admin

```bash
# Connect as superuser to a specific app DB (no port-binding on the host, so
# psql runs inside the container):
docker exec -it postgres psql -U postgres -d myapp_db

# Connect as the per-app role (useful for debugging permissions):
docker exec -it postgres psql -U myapp -d myapp_db
# Prompt: Password for user myapp: <paste from password manager>

# One-off SQL without entering the interactive shell:
docker exec -i postgres psql -U postgres -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database ORDER BY pg_database_size(datname) DESC;"

# Tail the Postgres logs (the same place Portainer's Logs tab shows):
docker logs -f postgres
```

If you find yourself running `psql` regularly and want a less verbose entry point, drop a tiny wrapper in `/usr/local/bin/`:

```bash
sudo tee /usr/local/bin/psql >/dev/null <<'EOF'
#!/bin/bash
# Convenience wrapper: `psql` on the host hands off to the container's psql.
# Pass `-U <role> -d <db>` etc. through unchanged.
exec docker exec -it postgres psql "$@"
EOF
sudo chmod 755 /usr/local/bin/psql
```

Then on the host: `psql -U postgres -d myapp_db`. The wrapper isn't in git (it's host-local convenience), but the §15 directory tree notes its presence.

### Backups (manual, opt-in)

Restic (formerly §12) was removed in v5.1.7.19, so there is **no automated backup** for this database. The minimum viable Postgres backup is a daily `pg_dumpall` cron entry dumping to a host directory, plus an offsite copy if you care about the data. Here's the minimum, on the Pi:

```bash
sudo mkdir -p /opt/postgres/dumps
sudo chmod 700 /opt/postgres/dumps

sudo nano /usr/local/bin/postgres-dump.sh
```

```bash
#!/bin/bash
# Daily pg_dumpall of all databases + roles + globals to /opt/postgres/dumps/.
# Run as root via cron. Keep 14 daily dumps, rotated.
set -euo pipefail
PATH=/usr/bin:/bin    # Same class as fix #109: cron's default PATH

DUMP_DIR=/opt/postgres/dumps
TS=$(date +%Y-%m-%d)
OUT="${DUMP_DIR}/pgdumpall-${TS}.sql.gz"

# pg_dumpall captures roles, tablespaces, AND every database. No password
# prompt because we exec inside the container as the postgres OS user, who
# trusts local Unix-socket connections by default in the official image.
docker exec postgres pg_dumpall -U postgres | gzip -9 > "$OUT"

# Keep 14 days. find -delete is atomic per-file.
find "$DUMP_DIR" -maxdepth 1 -name 'pgdumpall-*.sql.gz' -mtime +14 -delete
```

```bash
sudo chmod 700 /usr/local/bin/postgres-dump.sh
echo "30 3 * * * root /usr/local/bin/postgres-dump.sh" | sudo tee /etc/cron.d/postgres-dump
sudo chmod 644 /etc/cron.d/postgres-dump
```

> ⚠️ **A backup on the same SSD that's failing is not a backup.** `/opt/postgres/dumps/` is enough to survive a `docker volume rm postgres-data` mistake or a corrupted Postgres cluster, but not enough to survive the NVMe dying. If the data matters, add an offsite copy — `rclone copy /opt/postgres/dumps/ remote:postgres-dumps/` to Backblaze B2 / OneDrive / a NAS over WireGuard / wherever, run from a second cron entry an hour after the local dump. Out of scope here because the original Restic-removal decision in v5.1.7.19 was deliberate — you removed the automated-backup machinery on purpose, this section flags rather than re-introduces it.

Also gitignore the dumps directory:

```bash
echo 'dumps/' | sudo tee /opt/postgres/.gitignore
```

Restore drill:

```bash
# To a fresh container (TEST this; don't wait for an emergency):
gunzip -c /opt/postgres/dumps/pgdumpall-YYYY-MM-DD.sql.gz | docker exec -i postgres psql -U postgres
```

### Adding a web app later

When you add a self-hosted web app that needs the database, attach it to **both** `db-net` and `proxy-net`. Worked example using a fictional `myapp`:

```yaml
# /opt/myapp/docker-compose.yml
services:
  myapp:
    image: someorg/myapp:1.2.3
    container_name: myapp
    restart: unless-stopped
    environment:
      TZ: "Europe/Rome"
      # Set DATABASE_URL in Portainer env vars panel:
      #   DATABASE_URL=postgresql://myapp:<per-app-password>@postgres:5432/myapp_db
    networks:
      proxy-net:
        ipv4_address: 172.31.0.20    # next free; see §3 IP allocations
      db-net:
        # No static IP needed for outbound clients — only inbound services pin.
    # If the app has a healthcheck endpoint, depend on it being healthy before
    # Caddy proxies to it. The app does NOT depend_on postgres here because
    # they're in different compose projects (cross-stack depends_on isn't a
    # thing); the app needs its own startup retry logic for DB connect.
    ports:
      - "127.0.0.1:8000:8000"        # admin port loopback-bound; reach via Caddy

networks:
  proxy-net:
    external: true
  db-net:
    external: true
```

Then wire it into the rest of the stack:

1. **Caddyfile** (`/opt/caddy/Caddyfile`) — append a stanza:
   ```Caddyfile
   myapp.home.arpa {
       reverse_proxy myapp:8000
   }
   ```
   Reload: `docker exec caddy caddy reload --config /etc/caddy/Caddyfile`

2. **Pi-hole Local DNS** — add `myapp.home.arpa` → `192.168.70.5` in **Local DNS → DNS Records** (§6).

3. **Kuma monitor** — add an HTTPS monitor for `https://myapp.home.arpa` (§13).

4. **Create the per-app DB and role** in Postgres if you haven't already — see "Per-app database and role creation" above. The `DATABASE_URL` env var on the app must match what you created.

If the app fails to connect with `could not translate host name "postgres" to address` or similar, the most likely cause is missing `db-net` attachment in the app stack — both networks must be present and both must be `external: true`. See the §15 troubleshooting table for the symptom-keyed entry.

---

## 12. Dynamic DNS (DDNS)

Your TP-Link router already publishes `greenhouse.tplinkdns.com` and updates it on WAN IP change. **No DDNS container is needed on the Pi.**

### What's already configured

- **DDNS hostname:** `greenhouse.tplinkdns.com`
- **WAN port forward:** UDP 51820 → `192.168.70.5:51820` (WireGuard)
- **Used by:** wg0 client `Endpoint = greenhouse.tplinkdns.com:51820`

### Sanity check from outside the LAN

From a phone on mobile data (so you're hitting the public internet, not LAN shortcuts):

```bash
nslookup greenhouse.tplinkdns.com         # should return your current home WAN IP
nc -u -v greenhouse.tplinkdns.com 51820   # UDP test, won't reply but should not "host unreachable"
```

If `nslookup` returns `NXDOMAIN`, log into the TP-Link admin → Advanced → Network → Dynamic DNS and confirm the service is enabled and the status reads "Online."

### Optional: monitor the DDNS

In Uptime Kuma (§13), add a **DNS** monitor for `greenhouse.tplinkdns.com` resolving via `8.8.8.8`. If it ever stops resolving — router lost DDNS sync — you'll get a notification before you find out the hard way while standing at a hotel WiFi.

> If TP-Link DDNS ever flakes (their service goes down occasionally), the fallback plan is a free DuckDNS account with a small container on the Pi. Recipe in `docker/ddns/` of the repo (commented out by default).

---

## 13. Monitoring + Watchtower

### Uptime Kuma

**Stack name in Portainer:** `kuma`

```bash
sudo nano /opt/kuma/docker-compose.yml
```

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1.23.16
    container_name: uptime-kuma
    restart: unless-stopped
    ports:
      # Bound to loopback — reach via Caddy at kuma.home.arpa
      - "127.0.0.1:3001:3001"
    volumes:
      - kuma-data:/app/data
    # FIX #8: opt this container in to Watchtower auto-updates. With
    # WATCHTOWER_LABEL_ENABLE: "true" set on the Watchtower container, only
    # containers carrying this label are updated. Without the label on at
    # least one container, Watchtower runs its Sunday schedule and does
    # nothing — silently. Add or remove this label per-container to control
    # which services get auto-updated. Avoid adding it to Pi-hole, HA, or
    # Step-CA — those have breaking changes worth reviewing manually.
    labels:
      com.centurylinklabs.watchtower.enable: "true"
    networks:
      proxy-net:
        ipv4_address: 172.31.0.15

networks:
  proxy-net:
    external: true

volumes:
  kuma-data:
```

```bash
# Portainer → Stacks → + Add stack → name: kuma → Web editor → paste YAML → Deploy
# CLI fallback:
cd /opt/kuma && docker compose up -d
```

Open `https://kuma.home.arpa` and add monitors for:
- `https://ha.home.arpa` (HTTPS)
- `https://portainer.home.arpa` (HTTPS)
- `https://pihole.home.arpa` (HTTPS)
- `9.9.9.9` (ping — checks Proton tunnel is alive end-to-end)
- `greenhouse.tplinkdns.com` (DNS monitor via `8.8.8.8` — confirms TP-Link DDNS is updating)
- Push monitor for **NVMe SMART** (see script below) — alerts on bad sectors, high wear, or temperature
- Push monitor for **SoC temperature** (see script below) — alerts when the Pi is thermal-throttling

### SoC + NVMe health push script

In Kuma, create two **Push** monitors (Settings → Monitors → + Add monitor → Push). Note their push URLs.

> ⚠️ **Set each Push monitor's heartbeat interval to `60` seconds** (the default is 60s, but verify it). The cron job fires every minute — if the heartbeat interval is shorter than 60s, Kuma will flip the monitor to "down" between pushes and spam you with false alerts.

Then on the Pi:

```bash
sudo nano /usr/local/bin/homelab-health-push.sh
```

```bash
#!/bin/bash
# Push current SoC temp and NVMe SMART metrics to Kuma. Cron every 60s, as root.
#
# Replace the two <id> placeholders with the IDs from your Kuma push monitors.
# Replace /dev/nvme0n1 with the actual device if your SSD is on USB (typically
# /dev/sda — verify with: lsblk -d -o NAME,SIZE,MODEL)

# FIX #109: explicit PATH. Cron's default PATH for /etc/cron.d/ jobs is
# /usr/bin:/bin — it does NOT include /usr/sbin, where smartctl lives on
# Ubuntu 24.04. Without this, the bare `smartctl` call below silently fails
# with "command not found", $SMART comes back empty, the awk parses produce
# nothing, the `: "${WEAR:=100}"` default kicks in, and the SMART monitor
# then reports "down" (wear 100% > 80%) on EVERY push — a permanent false
# alarm that's hard to attribute. Manual testing via
# `sudo /usr/local/bin/homelab-health-push.sh` masks the bug because sudo's
# secure_path includes /usr/sbin; cron's environment does not. Setting PATH
# explicitly here makes both paths identical and the script self-contained.
PATH=/usr/bin:/bin:/usr/sbin:/sbin

# FIX #49: use the direct loopback URL instead of the Caddy/DNS chain. The health
# script must keep pushing even when Pi-hole DNS or Caddy itself is down (or during
# a backup run when Caddy is quiesced). The loopback address bypasses both, hitting
# Kuma directly on its bound port.
KUMA_BASE="http://127.0.0.1:3001/api/push"
TEMP_PUSH_ID="<id-for-soc-temp-monitor>"
SMART_PUSH_ID="<id-for-nvme-smart-monitor>"
NVME_DEV="/dev/nvme0n1"

# --- SoC temp from sysfs (no vcgencmd dependency — works on stock Ubuntu Server for Pi) ---
TEMP_MC=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
if [ -z "$TEMP_MC" ] || ! [ "$TEMP_MC" -eq "$TEMP_MC" ] 2>/dev/null; then
    # sysfs unreadable or not a number — report down with a sentinel value
    curl -s --max-time 5 \
      "${KUMA_BASE}/${TEMP_PUSH_ID}?status=down&msg=SoC+temp+unreadable&ping=0" >/dev/null
else
    TEMP_INT=$((TEMP_MC / 1000))
    TEMP_C=$(awk "BEGIN { printf \"%.1f\", $TEMP_MC/1000 }")
    if [ "$TEMP_INT" -lt 75 ]; then TEMP_STATUS="up"; else TEMP_STATUS="down"; fi
    curl -s --max-time 5 \
      "${KUMA_BASE}/${TEMP_PUSH_ID}?status=${TEMP_STATUS}&msg=SoC+${TEMP_C}C&ping=${TEMP_INT}" >/dev/null
fi

# --- NVMe SMART (script runs as root, no sudo needed) ---
if [ -e "$NVME_DEV" ]; then
    SMART=$(smartctl -A "$NVME_DEV" 2>/dev/null)
    WEAR=$(echo "$SMART"  | awk '/Percentage Used/ {gsub("%","",$NF); print $NF; exit}')
    NVME_TEMP=$(echo "$SMART" | awk '/^Temperature:/ {print $2; exit}')
    CRIT=$(echo "$SMART"  | awk '/Critical Warning/ {print $3; exit}')
    : "${WEAR:=100}"; : "${NVME_TEMP:=100}"; : "${CRIT:=0xFF}"

    # FIX #90: compare CRIT in arithmetic context, not as a string. Some
    # smartctl versions emit the Critical Warning value as bare `0` rather
    # than `0x00`, so a strict string match would flip a healthy drive to
    # "down". $((CRIT)) handles both 0/0x00 (→ 0) and any real warning bits
    # (→ non-zero), so the broken-state behaviour is preserved.
    if [ "$((CRIT))" -eq 0 ] && [ "$WEAR" -lt 80 ] && [ "$NVME_TEMP" -lt 70 ]; then
        SMART_STATUS="up"
    else
        SMART_STATUS="down"
    fi
    curl -s --max-time 5 \
      "${KUMA_BASE}/${SMART_PUSH_ID}?status=${SMART_STATUS}&msg=wear+${WEAR}%25+temp+${NVME_TEMP}C+crit+${CRIT}&ping=${WEAR}" >/dev/null
else
    # Device path not found — push "down" with a clear message instead of
    # sending nothing. A missing device causes the push monitor heartbeat to
    # expire silently (Kuma shows "down" with no message), making it
    # indistinguishable from a real SMART failure. Check NVME_DEV above and
    # confirm with: lsblk -d -o NAME,SIZE,MODEL
    curl -s --max-time 5 \
      "${KUMA_BASE}/${SMART_PUSH_ID}?status=down&msg=NVME_DEV+${NVME_DEV}+not+found&ping=0" >/dev/null
fi
```

```bash
sudo chmod 700 /usr/local/bin/homelab-health-push.sh
```

Cron entry — note the explicit `root` field, which `/etc/cron.d/` files **require** (unlike a user crontab). Without it cron silently ignores the entry:

```bash
echo "* * * * * root /usr/local/bin/homelab-health-push.sh" | sudo tee /etc/cron.d/homelab-health
sudo chmod 644 /etc/cron.d/homelab-health
```

Verify the cron entry is actually running after a minute:

```bash
sudo grep CRON /var/log/syslog | tail -5
```

Thresholds are starting points: 75°C for SoC (Pi 5 throttles around 80–85°C), 80% NVMe wear, 70°C NVMe temp, and any non-zero SMART critical warning. Tune to your hardware.

Configure Telegram or email notifications in Kuma so the SoC/NVMe alerts (and the service monitors) actually reach you.

### Watchtower (controlled image updates)

**Stack name in Portainer:** `watchtower`

> Use the **Environment variables** panel in Portainer to set `WATCHTOWER_NOTIFICATION_URL` (your Telegram token/chat ID) instead of hardcoding it in the YAML. This keeps secrets out of git.

> ℹ️ **FIX #8 — `WATCHTOWER_LABEL_ENABLE` requires opt-in labels.** With this flag set, Watchtower **only** updates containers carrying `com.centurylinklabs.watchtower.enable: "true"`. Without that label on a container, Watchtower skips it silently — the Sunday schedule fires, pulls nothing, and logs nothing obvious. Kuma has the label in the stack above as the worked example. Add it to any other service you want auto-updated (Mosquitto and the DDNS container are good candidates). Deliberately omit it from Pi-hole, HA, Step-CA, Portainer, and NPM — those have release notes worth reading before upgrading.

```bash
sudo nano /opt/watchtower/docker-compose.yml
```

```yaml
services:
  watchtower:
    image: containrrr/watchtower:1.7.1
    container_name: watchtower
    restart: unless-stopped
    # v3 mounted /var/run/docker.sock directly — root-equivalent on the host
    # if Watchtower's image is ever compromised. v4 routes through the
    # docker-socket-proxy created in §3 (read-only socket mount, minimal API
    # surface). Watchtower needs CONTAINERS, IMAGES, POST, DELETE; the proxy
    # grants all of these (DELETE=1 is required for WATCHTOWER_CLEANUP).
    environment:
      TZ: "Europe/Rome"
      DOCKER_HOST: "tcp://docker-socket-proxy:2375"
      WATCHTOWER_CLEANUP: "true"
      WATCHTOWER_SCHEDULE: "0 0 5 * * SUN"   # Sunday 05:00
      WATCHTOWER_NOTIFICATIONS: "shoutrrr"
      # WATCHTOWER_NOTIFICATION_URL set in Portainer env vars panel, not here
      WATCHTOWER_LABEL_ENABLE: "true"        # only update containers with the opt-in label
    networks:
      proxy-net:
        ipv4_address: 172.31.0.16

networks:
  proxy-net:
    external: true
```

```bash
# Portainer → Stacks → + Add stack → name: watchtower → Web editor → paste YAML
# Set WATCHTOWER_NOTIFICATION_URL in the Environment variables panel (not in the YAML)
# → Deploy
# CLI fallback (must pass WATCHTOWER_NOTIFICATION_URL inline — see the
# Portainer-path note just above for why it's not in the compose YAML):
cd /opt/watchtower && WATCHTOWER_NOTIFICATION_URL='telegram://<token>@telegram?chats=<chat-id>' docker compose up -d
```

---

## 14. Final Checklist

### Verify all services

```bash
sudo wg show
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
```

Containers expected up: `pihole`, `unbound`, `step-ca`, `caddy`, `portainer`, `docker-socket-proxy`, `homeassistant`, `postgres`, `uptime-kuma`, `watchtower`. (No DDNS container — TP-Link router handles it.)

**Verify all stacks are healthy in Portainer:** Portainer → **Stacks** — each stack should show **Active** in green. Any stack showing **Unhealthy** or **Inactive** → click in → **Logs** tab to diagnose.

| Stack name | Containers | Portainer status |
|---|---|---|
| `dns` | `pihole`, `unbound` | Active |
| `step-ca` | `step-ca` | Active |
| `caddy` | `caddy` | Active |
| `homeassistant` | `homeassistant` | Active |
| `postgres` | `postgres` | Active |
| `kuma` | `uptime-kuma` | Active |
| `watchtower` | `watchtower` | Active |

Plus the two containers that aren't stacks: `portainer` itself and `docker-socket-proxy`. Check both with `docker ps`.

### Router config

| Setting | Value |
|---|---|
| DHCP range | `192.168.68.50 – 192.168.69.250` |
| DHCP gateway | `192.168.68.1` (router itself — LAN clients bypass Proton) |
| DHCP DNS primary | `192.168.70.5` (Pi-hole) |
| DHCP DNS secondary | `9.9.9.9` (fallback if Pi-hole down) |
| Port forward 51820/UDP | → `192.168.70.5:51820` (WireGuard) |
| Port forward 80/TCP | → `192.168.70.5:80` (Caddy, optional if you want public access — see note below) |
| Port forward 443/TCP | → `192.168.70.5:443` (Caddy, optional — see note below) |

> ⚠️ **The optional 80/443 forwards don't work without a DOCKER-USER change** (FIX #98). When a WAN-sourced packet reaches the Pi via the router's port forward, the FORWARD chain sees the original external client IP as the source — none of the DOCKER-USER `-j RETURN` rules (`-i wg0`, `-s 192.168.68.0/22`, `-s 172.16.0.0/12`, `-s 127.0.0.0/8`) match it, and the final `-j DROP` applies. The doc's primary remote-access path is wg0, not public NPM, so this is the safe default. If you genuinely want public NPM exposure, you need to add a permissive rule to `/usr/local/bin/docker-user-rules.sh` **before** the final DROP — e.g. `iptables -A DOCKER-USER -p tcp -m multiport --dports 80,443 -j RETURN` — and accept that NPM-fronted services are now reachable from the public internet (with all the auth-strength and rate-limiting implications that follow).

### Trust-store install of `homelab-root-ca.crt`

| Device | How |
|---|---|
| Windows | `certmgr.msc` → Trusted Root CAs → Import |
| macOS | Keychain → System → Import → Trust Always |
| iOS | AirDrop the .crt → Settings → Profile Downloaded → Install → General → About → Cert Trust Settings → Enable |
| Android | Settings → Security → Encryption & credentials → Install from storage |
| Linux | `sudo cp homelab-root-ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates` |
| Firefox | Settings → Privacy → Certificates → Import |

### Functional tests

**At home, from a LAN client (phone on WiFi, laptop, etc.):**
```bash
curl ifconfig.me                       # your home WAN IP (NOT Proton — LAN bypasses it)
nslookup ha.home.arpa               # 192.168.70.5 (Pi-hole answered)
curl https://ha.home.arpa           # HA login page — NO -k; this validates the root CA is trusted
```

**At home, from the Pi itself or any Docker container:**
```bash
curl ifconfig.me                       # ProtonVPN IP (Pi's traffic IS through Proton)
# Pi-hole v6 is Alpine-based; it ships curl, but if a future image strips it
# down, fall back to: docker exec pihole wget -qO- ifconfig.me
docker exec pihole curl -s ifconfig.me # also ProtonVPN IP
```

**Remote (phone on mobile data, wg0 connected):**
```
ping 192.168.70.5                      # reaches Pi
ping 192.168.68.1                      # reaches your home router
open https://ha.home.arpa           # HA loads
curl ifconfig.me                       # ProtonVPN IP (IPv4)
curl -6 ifconfig.me                    # ProtonVPN IP (IPv6) — NOT your carrier's v6
visit dnsleaktest.com                  # only Proton DNS appears
visit ipv6leak.com                     # confirms no native v6 leak
```

**Tunnel-down behavior (intentional kill switch test):**
```bash
# FIX #95: drop the interface directly, NOT via `systemctl stop wg-quick@protonvpn`.
# `systemctl stop` runs `protonvpn-down.sh` (the wg-quick PreDown hook), which
# REMOVES the PROTON_KS chain from OUTPUT — turning this into a "did wg-quick
# clean up correctly?" check instead of a "does the kill switch actually hold
# when the tunnel drops?" check. The interface goes down here in a way that
# simulates a real tunnel drop (server reboot, transient network blip): the
# wg-quick teardown is NOT invoked, so the kill switch is still loaded in
# iptables and the curl below has nowhere to go.
sudo ip link set protonvpn down
curl --max-time 5 ifconfig.me           # should fail (kill switch active)
chronyc tracking                        # should STILL work — NTP is in the kill-switch exception
# Cleanest recovery is a full wg-quick restart — bringing the link back up
# manually doesn't re-establish the WireGuard handshake state.
sudo systemctl restart wg-quick@protonvpn
```

---

## 15. Operations and Troubleshooting

### Service URLs

Admin ports are now bound to `127.0.0.1` on the Pi — they aren't reachable from the LAN directly. Use Caddy via `*.home.arpa` for normal use, or SSH tunneling for bootstrap and debugging:

```bash
# example: reach Portainer directly via SSH tunnel
ssh -L 9443:127.0.0.1:9443 pi@192.168.70.5
# then open https://127.0.0.1:9443 on your laptop
```

| Service | Direct (on Pi only, via SSH tunnel) | Via Caddy (any LAN/VPN client) |
|---|---|---|
| Home Assistant | `http://192.168.70.5:8123` (host network, LAN-reachable) | `https://ha.home.arpa` |
| Portainer | `https://127.0.0.1:9443` | `https://portainer.home.arpa` |
| Pi-hole | `http://127.0.0.1:8080/admin` | `https://pihole.home.arpa` |
| Step-CA | `https://127.0.0.1:9000` | `https://stepca.home.arpa` |
| Uptime Kuma | `http://127.0.0.1:3001` | `https://kuma.home.arpa` |

> ℹ️ Home Assistant intentionally stays on `network_mode: host` (mDNS / HomeKit requirement). §2's UFW rules (fix #106) explicitly open port 8123 to the LAN and to the Docker bridge range, so `http://192.168.70.5:8123` is reachable from the whole LAN and `ha.home.arpa` works through Caddy. If you want to enforce Caddy-only access to HA — i.e. block LAN devices from hitting `192.168.70.5:8123` directly while still letting Caddy proxy it — you must **insert** a deny rule *before* the `allow from 192.168.68.0/22 ... 8123` rule, because UFW is first-match-wins and the allow was added first: `sudo ufw insert 1 deny from 192.168.68.0/22 to any port 8123`. Caddy is unaffected — its traffic originates from the `172.31.x.x` Docker bridge (matched by the separate `from 172.16.0.0/12` allow), not from `192.168.68.0/22`. Re-check ordering afterwards with `sudo ufw status numbered`.

### Updating images deliberately

**Via Portainer (preferred):**

1. Portainer → **Stacks** → select the stack
2. **Editor** tab → bump the image tag (e.g. `2.11.3` → `2.12.0`)
3. Click **Update the stack** — Portainer pulls the new image and recreates only the changed service
4. **Logs** tab → watch for errors

If something breaks: go back to **Editor**, revert the tag, and **Update the stack** again.

**Via CLI (fallback / Portainer itself):**

```bash
cd /opt/<service>
sudo nano docker-compose.yml     # bump tag, e.g. 2.11.3 → 2.12.0
docker compose pull
docker compose up -d
docker compose logs -f --tail=50
```

If something breaks: `git checkout` the previous compose file and `docker compose up -d`.

**Updating Portainer itself** (not a stack — must use CLI):

```bash
docker pull portainer/portainer-ce:2.x.y
docker stop portainer
docker rm portainer
docker run -d --name portainer --restart=unless-stopped \
  --network proxy-net \
  -p 127.0.0.1:9443:9443 \
  -e DOCKER_HOST=tcp://docker-socket-proxy:2375 \
  -v portainer_data:/data \
  portainer/portainer-ce:2.x.y
```

(Note: no `docker.sock` mount — Portainer talks to `docker-socket-proxy` over `proxy-net`.)

### Verify MTU through stacked tunnels

protonvpn is set to MTU 1320; wg0 is set to MTU 1280 (fix #62). Because wg0 traffic gets re-encapsulated through protonvpn (~60 B overhead), the effective inner payload MTU is approximately 1220 bytes. To verify there's no silent fragmentation hurting throughput, from a connected wg0 client:

```bash
# Linux/macOS — payload sizes climb until the DF bit causes failure
for s in 1160 1180 1200 1220 1240 1260 1280; do
  ping -M do -s "$s" -c 1 -W 2 9.9.9.9 >/dev/null 2>&1 \
    && echo "$s OK" \
    || echo "$s FAIL"
done
```

The last `OK` size + 28 (ICMP+IP headers) is your true effective MTU. **Going below 1280 breaks IPv6 on the wg0 interface** — 1280 is the IPv6 minimum MTU (see fix #82 in §4). If the probe shows the path can't carry 1280-byte packets and you must lower wg0 further, you're making a deliberate trade-off: no IPv6 on wg0 in exchange for no fragmentation. Drop both server and client to e.g. 1240 only if you accept v4-only on wg0. Mismatched MTUs typically show up as "WireGuard connects but big requests hang" — HTTPS handshakes complete, but large responses stall.

### Image-pin review cadence

Pinning images protects against silent breakage but, left alone, silently rots into "running known-CVE versions on purpose." Add a recurring calendar entry — quarterly is reasonable — to:

1. Check the changelogs of each pinned image (Pi-hole, HA, Caddy, Portainer, Step-CA, Kuma, Mosquitto, Watchtower, Unbound, docker-socket-proxy)
2. Bump pins one stack at a time via Portainer's Stack editor → Update
3. Watch logs for ≥24h before bumping the next
4. Commit the updated compose files to git

Pi-hole 5→6 was a one-way migration with a new env var schema. Step-CA, Portainer, and Caddy occasionally have breaking config changes too. Reading release notes before bumping is the difference between a 5-minute update and a 2-hour rollback.

### gitleaks pre-commit

You're committing compose files, netplan, sysctl, SSH hardening, and a sanitised `wg0.conf` to a private repo. "Sanitised" by hand is exactly the kind of thing that goes wrong once. Add [gitleaks](https://github.com/gitleaks/gitleaks) as a pre-commit hook so a private key or `WEBPASSWORD` left in by accident gets caught before it hits GitHub:

```bash
# On your dev workstation, in the repo root:
brew install gitleaks    # or: go install github.com/gitleaks/gitleaks/v8@latest

cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks
EOF

# Ubuntu 24.04 enforces PEP 668 — plain `pip install` outside a venv exits with
# "externally-managed-environment". Use pipx instead (it creates its own venv):
sudo apt install -y pipx
pipx install pre-commit
pipx ensurepath   # adds ~/.local/bin to PATH; re-login or `source ~/.bashrc` after
pre-commit install
```

Now every `git commit` runs gitleaks; a hit blocks the commit until you redact.

### Common breakage patterns

| Symptom | Likely cause | Fix |
|---|---|---|
| `wg-quick@protonvpn` fails | Stale `ip rule` from a previous run | `sudo ip rule del priority 50 2>/dev/null; sudo ip rule del priority 51 2>/dev/null; sudo systemctl restart wg-quick@protonvpn` — **do NOT use `ip rule flush`**: it deletes all rules including the kernel defaults at 0/32766/32767, breaking all routing until reboot |
| LAN clients can't reach internet after reboot | UFW reloaded forward policy back to DROP | Check `/etc/default/ufw`, ensure `DEFAULT_FORWARD_POLICY="ACCEPT"` |
| VPN clients connect but no DNS | Missing `ufw allow in on wg0 to any port 53` | Add the UFW rule, reload |
| Pi-hole won't start | `systemd-resolved` came back from updates, OR v5→v6 migration confusion | `sudo systemctl disable --now systemd-resolved`; for env vars: v6 uses `FTLCONF_*`, old `WEBPASSWORD`/`DNSMASQ_LISTENING` are silently ignored |
| Cert errors on `*.home.arpa` | Root CA not installed on that device | See trust-store table |
| Slow VPN throughput / random disconnects | MTU too high through stacked tunnels | wg0 is already set to 1280 (fix #62, IPv6 minimum per fix #82); run the MTU probe in §15. Only lower wg0 + clients further if the stall persists **and** you accept losing IPv6 on the wg0 interface — 1240 is conservative but makes wg0 v4-only |
| Watchtower broke a service | Bad image tag picked up | `cd /opt/<service> && docker compose pull && docker compose up -d` with last-known-good tag |
| wg0 phone client never connects, `tcpdump -ni eth0 'udp port 51820'` shows inbound length-148 packets but NO outbound length-92 response (Proton tunnels up) | wg0 protocol traffic getting REJECT'd by `PROTON_KS` kill-switch chain in OUTPUT because the explicit `-m mark --mark 51820 -j RETURN` rule is missing | Confirm `FwMark = 51820` is in the `[Interface]` block of `/etc/wireguard/wg0.conf` (fix #117). Verify with `sudo wg show wg0 fwmark` → should print `0xca6c`. Then verify the PROTON_KS chain has the exemption: `sudo iptables -L PROTON_KS -n \| grep '0x51820\|mark match 0xca6c'` should print a `RETURN` line. If missing: `sudo systemctl restart proton-killswitch-init.service` (creates the chain with the exemption). In v5.1.7.20 and earlier, the matching rule was auto-installed by ProtonVPN's wg-quick; in v5.1.7.21+ multi-tunnel it's explicit in `/usr/local/bin/proton-killswitch-init.sh` because `Table = off` in each `protonvpnN.conf` disables wg-quick's auto-routing |
| wg0 phone client connects but `wg show wg0` keeps showing "latest handshake: (none)", `journalctl -kf` (after `echo 'module wireguard +p' \| sudo tee /sys/kernel/debug/dynamic_debug/control`) shows `Invalid MAC of handshake` from the client's IP | Client's PrivateKey doesn't pubkey-derive to the PublicKey configured for that peer in wg0.conf. Almost always: the client's WG app preserved its old `PrivateKey` when you re-imported a QR code over an existing tunnel of the same name (Android/iOS apps both do this) | **Delete the existing tunnel entirely** in the WG app (not just toggle off) **before** scanning the new QR. Re-run `sudo wg-add-client <name>` on the Pi (§5) to generate a fresh QR. If the user keeps hitting this, "kill it with fire": delete every WG tunnel on the device, force-quit the app, re-open, then scan. Disable dyndbg after with `echo 'module wireguard -p' \| sudo tee /sys/kernel/debug/dynamic_debug/control` |
| `sudo wg syncconf wg0 <(sudo wg-quick strip wg0)` exits with `fopen: No such file or directory` | `sudo` closes file descriptors > 2 on the new process before exec'ing wg; process substitution's `/dev/fd/63` then doesn't exist inside the sudo'd `wg` process | Use a temp file: `wg-quick strip wg0 > /tmp/wg0.stripped && wg syncconf wg0 /tmp/wg0.stripped && rm /tmp/wg0.stripped`. The `wg-add-client` script uses this pattern internally for the same reason |
| Caddy log shows `tls: failed to verify certificate: x509: certificate signed by unknown authority` during ACME registration | `acme_ca_root` path wrong, root cert not mounted, or Step-CA root cert hasn't been generated yet | Verify `/opt/step-ca/homelab-root-ca.crt` exists on the host (re-run the §7 root-cert export if not), the Caddy compose mount line is present and the path inside the container matches `acme_ca_root` in the Caddyfile global block |
| `postgres` container won't start, logs include `configured to store database data in a format which is compatible with "pg_ctlcluster" ... Counter to that, there appears to be PostgreSQL data in: /var/lib/postgresql/data (unused mount/volume)` | Volume is mounted at the PG-17-era path `/var/lib/postgresql/data` but the image is PG 18+ which expects `/var/lib/postgresql` (parent dir) as the mount target and PGDATA at `/var/lib/postgresql/18/docker`. docker-library/postgres#1259. Hits anyone who reused a v5.1.7.21 PG-17 volume after bumping to `postgres:18.x` without changing the mount path | New deployment, no existing data: edit `/opt/postgres/docker-compose.yml`, change the volume line from `postgres-data:/var/lib/postgresql/data` to `postgres-data:/var/lib/postgresql`, `docker compose down -v` (drops the unused volume), `docker compose up -d`. Existing PG 17 data you want to keep: a) `docker exec postgres pg_dumpall -U postgres > /tmp/dumpall.sql` from the still-running PG 17 container (revert the image to `postgres:17-alpine` if you already changed it), b) `docker compose down -v` to drop the old volume, c) bump image to `postgres:18.4-alpine` AND fix the mount path, d) `docker compose up -d`, e) `docker exec -i postgres psql -U postgres < /tmp/dumpall.sql` to restore. There is no in-place fix that preserves the old PGDATA layout under PG 18 — the entrypoint explicitly refuses to run |
| Web app can't reach Postgres: app logs show `could not translate host name "postgres" to address: Temporary failure in name resolution` (or similar DNS error) | App container is missing the `db-net` network attachment. Docker's embedded DNS only resolves container names within networks the requesting container is attached to — being on `proxy-net` alone (so Caddy can reach the app) is not enough; the app also needs `db-net` to see `postgres` | In the app's `/opt/<app>/docker-compose.yml`, confirm BOTH `proxy-net` AND `db-net` are listed under `networks:` for the service AND in the top-level `networks:` block as `external: true`. Verify after `docker compose up -d` with `docker network inspect db-net` — the app container's name should appear in the `Containers` list. If `network not found`, you skipped the §11 `docker network create db-net` step |

### Ubuntu vs Debian gotchas

| Topic | Ubuntu specifics |
|---|---|
| Static IP | Netplan, not `/etc/network/interfaces`. Mode 600 on the YAML. Disable cloud-init network management with `echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` — without this, cloud-init overwrites `50-cloud-init.yaml` on the next boot and reverts to DHCP. |
| Port 53 conflict | Disable `systemd-resolved` and write your own `/etc/resolv.conf`. After full setup, pin it with `chattr +i` (see §6) to prevent cloud-init reinstating the symlink on point-release upgrades. |
| Snap | Remove manually, hold the package |
| HA Supervised | Don't — use HA Container (covered above) |
| AppArmor | Leave enabled; HA Container is fine with it |

### Directory structure

```
/opt/
├── dns/              # Pi-hole + Unbound
├── homeassistant/    # HA Container (+ optional Mosquitto)
├── caddy/            # Caddy reverse proxy (Caddyfile, named volumes hold ACME state)
├── portainer/        # no compose file — Portainer + docker-socket-proxy bootstrapped via docker run (see §3)
├── postgres/         # PostgreSQL 18 (see §11). dumps/ subdir is gitignored — manual pg_dumpall target.
├── step-ca/          # Step-CA
├── kuma/             # Uptime Kuma
└── watchtower/       # Watchtower (talks to docker-socket-proxy, not docker.sock directly)

/etc/wireguard/
├── protonvpn.conf
├── protonvpn-up.sh
├── protonvpn-down.sh
├── wg0.conf
├── wg0-private.key
└── wg0-public.key

/etc/netplan/
└── 50-cloud-init.yaml

/etc/chrony/
└── chrony.conf       # LAN-first NTP, see §2

/usr/local/bin/
├── homelab-health-push.sh
├── docker-user-rules.sh
├── postgres-dump.sh  # optional — manual Postgres backup, see §11 backups subsection
└── psql              # optional — convenience wrapper for `docker exec -it postgres psql`, see §11

/etc/cron.d/
├── homelab-health    # SoC + NVMe push to Kuma every minute
└── postgres-dump     # optional — daily pg_dumpall, see §11 backups subsection

/etc/systemd/system/
│   └── notify.conf
└── docker-user-rules.service
```

### What to put in git

`/opt/*/docker-compose.yml`, `/etc/netplan/50-cloud-init.yaml`, `/etc/sysctl.d/99-homelab.conf`, `/etc/ssh/sshd_config.d/99-hardening.conf`, `/etc/chrony/chrony.conf`, `/etc/apt/apt.conf.d/50unattended-upgrades`, `/etc/wireguard/protonvpn-up.sh`, `/etc/wireguard/protonvpn-down.sh`, `/usr/local/bin/homelab-health-push.sh`, `/usr/local/bin/docker-user-rules.sh`, `/etc/systemd/system/docker-user-rules.service`, `/etc/cron.d/homelab-health`, the rest of the systemd unit files, and a sanitised version of `wg0.conf` (keys redacted). If you set up the optional §11 Postgres backup: add `/usr/local/bin/postgres-dump.sh` and `/etc/cron.d/postgres-dump`. The `/opt/postgres/.gitignore` (just the one line `dumps/`) goes in too — and gets committed *before* you ever write a dump, otherwise the first run will land a multi-GB blob in your repo history. Commit the lot to a private GitHub repo with `gitleaks` as a pre-commit hook.

Keep the on-disk compose files in sync with what you paste into Portainer. The easiest habit: edit the file on disk first, then paste the updated content into the Portainer stack editor. That way git always has the source of truth.

---

**v5.1 bug-fix summary** — the 5 fixes applied to v5 plus 23 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 9 | §6 Pi-hole | `http://192.168.70.5:8080/admin` is unreachable before NPM exists — port 8080 is bound to `127.0.0.1` only | Replaced with SSH-tunnel instructions for pre-NPM access |
| 11 | §2 systemd-resolved | Heading said "no chattr" and intro said not to use `chattr +i`, but the body correctly used it — stale text from v1 that was never updated when v4 reversed the decision | Rewrote heading and intro paragraph to match the actual instructions |
| 13 | v4 changes summary | Watchtower `1.7.1` was pinned in the compose file (§12) but absent from the end-of-document image-pins table used for quarterly review | Added `Watchtower 1.7.1` to the pins table |
| 14 | Header | "Revision notes vs v5" was a self-reference — current doc IS v5; should read "vs v4.1" | Corrected to "vs v4.1" |
| 15 | §6 Pi-hole compose | `FTLCONF_webserver_port: "8080o"` — the `o` suffix is not a valid Pi-hole v6 port specifier and would likely break the web server | Corrected to `"8080"` with explicit `FTLCONF_webserver_tls_port: "-1"` to disable container HTTPS |
| 17 | §3 + §14 Portainer | `-e DOCKER_HOST=tcp://docker-socket-proxy:2375` was missing from both the initial `docker run` and the §14 update command — after any container recreate, Portainer would lose its socket-proxy connection | Added env var to both commands; updated first-run wizard note |
| 18 | §5 wg0.conf | Comment implied ip6tables FORWARD rules were optional (like the ip6tables MASQUERADE rule) — they are unconditional and always needed for the tunnel to carry IPv6 | Clarified comment; rules unchanged |
| 19 | §3 daemon.json | `proxy-net` (`172.31.0.0/24`) and `dns-net` (`172.30.0.0/24`) sit inside Docker's default auto-allocation pool (`172.16.0.0/12`); Docker could auto-assign a new network the same prefix, silently breaking routing | Added `default-address-pools` to `daemon.json` (base `172.17.0.0/16` — later corrected to `172.20.0.0/14` by fix #33) |
| 20 | §2 + §6 systemd-resolved | `chattr +i /etc/resolv.conf` was placed in the §2 early-setup code block, but running it there blocks netplan and cloud-init for the rest of initial setup — the inline comment even said "run after setup only" | Removed `chattr +i` from §2; added a new deferred "Pin resolv.conf" step at the end of §6 after Pi-hole is confirmed working |
| 21 | §10 Mosquitto | `mosquitto_passwd -c` creates and overwrites the password file — using it to add a second user silently deletes the first; no warning was present | Added explicit warning; showed the no-`-c` form for adding subsequent users |
| 22 | §3 Docker install | `newgrp docker` only applies the group to the current shell; other open terminals require a full logout/login before `docker` works without `sudo` | Added warning and recommended `exit` + re-SSH before continuing |
| 23 | §11 DDNS | Typo "fastback-up" instead of "fallback" | Fixed |
| 24 | §13 Functional tests | `curl -k https://ha.home.arpa` suppresses TLS errors with `-k`, defeating the entire point of verifying the root CA is trusted on the client | Removed `-k`; added inline comment explaining the test is intentionally strict |
| 25 | §9 gateway table | Table labels jumped from "Option A" to "Option C" — Option B had been deleted in an earlier edit but the label on C was never updated | Renamed "Option C" to "Option B" |
| 26 | §14 Ubuntu gotchas | `chattr +i` cross-reference said "(see §2)" after the step was moved to §6 in fix #20 | Updated to "(see §6)" |
| 28 | §14 troubleshooting table | `docker compose pull && up -d` — `up -d` is not a standalone command; would fail with "command not found" | Fixed to `docker compose pull && docker compose up -d` |
| 29 | §3 container startup order | `docker run portainer` appeared before `docker run docker-socket-proxy`; Portainer's `DOCKER_HOST` env var points at the proxy and tries to connect immediately — proxy must exist first | Swapped order: docker-socket-proxy first, then Portainer; added explanatory note |
| 30 | §13 health script | `TEMP_MC` had no guard against empty/unreadable sysfs output; an empty value caused `awk` arithmetic syntax error, silently crashing the script | Added empty-value check; script now pushes a "down" status with a clear message if sysfs is unreadable |
| 31 | §2 formatting | Two consecutive blank lines left after removing `chattr +i` from §2 in fix #20 | Removed extra blank line |

**v5.1.7.11 bug-fix summary** — 5 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 103 | §4 `protonvpn-up.sh` kill switch | `PROTON_KS` had no exemption for Docker bridge subnets; host→container traffic over the bridges (host DNS via docker-proxy→Pi-hole, `curl 127.0.0.1:9443`→Portainer, health-push→Kuma) carries a container IP as destination, which is not LOCAL and not in the LAN/wg0 ranges, so it falls through to the final `REJECT`. After §4, Portainer/Pi-hole admin and the Pi's own DNS all break | Added `iptables -A PROTON_KS -d 172.16.0.0/12 -j RETURN` before the `REJECT`, with a comment. Same class as fix #58 but for the host→container *destination* direction. `protonvpn-down.sh` needs no edit (it flushes the whole chain) |
| 104 | §8 NPM `entrypoint:` | `update-ca-certificates && /init` leaves `/bin/sh` as PID 1 and runs `/init` as its child; NPM's s6-overlay v3.x base image hard-checks `getpid() == 1` and aborts with `s6-overlay-suexec: fatal: can only run as pid 1`, crash-looping the container forever | Changed to `update-ca-certificates && exec /init` so `/init` replaces the shell and inherits PID 1; expanded the comment to document why `exec` is mandatory |
| 105 | §8 SSH tunnel example | `ssh -L 81:127.0.0.1:81` fails with `bind: Permission denied` — port 81 is privileged and the `-L` local listen-port can't be bound by a non-root user on macOS/Linux | Changed local listen-port to `8081` (`ssh -L 8081:127.0.0.1:81`); Pi-side target stays `81`; access URL updated to `http://127.0.0.1:8081`. Same pattern §6 already uses |
| 106 | §2 UFW + §10 + §14 | HA runs `network_mode: host` on `0.0.0.0:8123`, outside Docker's port-NAT, so UFW's `default deny incoming` drops all traffic to 8123 — but §2 never opened the port while §10 and §14 both assumed it was reachable. NPM's `ha.home.arpa` proxy host 504s as a result | Added `ufw allow from 172.16.0.0/12 to any port 8123` (NPM→HA) and `ufw allow from 192.168.68.0/22 to any port 8123` (LAN-direct) to §2; rewrote the §14 deny-to-restrict note to use `ufw insert 1` so the deny precedes the allow (UFW is first-match-wins) |
| 107 | §6 Pi-hole `FTLCONF_dns_upstreams` | `172.30.0.2#5335` pointed FTL at port 5335, but the `mvance/unbound-rpi` container listens on port 53 — the `#5335` convention is for bare-metal setups where Unbound must dodge Pi-hole's own `:53`. Result: upstream resolution silently failed, no internet via Pi-hole | Changed to `172.30.0.2` (FTL defaults to port 53); corrected the stale inline comment and the §6 troubleshooting callout that referenced `#5335` / `:5335` |

**v5.1.7.10 bug-fix summary** — 2 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 101 | §7 Step-CA CLI fallback | Regression from fix #92: the Portainer-path instructions correctly tell the user to set `DOCKER_STEPCA_INIT_PASSWORD` in the stack's env-vars panel, but the adjacent CLI fallback (`cd /opt/step-ca && docker compose up -d`) didn't pass the env var inline; a CLI-path user would get the random-generated-and-logged behaviour back — the very thing fix #92 set out to eliminate | Patched the CLI fallback to `cd /opt/step-ca && DOCKER_STEPCA_INIT_PASSWORD='...' docker compose up -d`, matching the pattern used by the Pi-hole `dns` stack's CLI fallback (`FTLCONF_webserver_api_password='...'`) |
| 102 | §13 Watchtower CLI fallback | Pre-existing same-class bug: the prose tells the user to set `WATCHTOWER_NOTIFICATION_URL` in the Portainer env-vars panel, but the CLI fallback didn't pass it inline; a CLI-path user would deploy Watchtower with notifications silently disabled and the Sunday update schedule would fire without any Telegram alerts | Patched the CLI fallback to `WATCHTOWER_NOTIFICATION_URL='telegram://<token>@telegram?chats=<chat-id>' docker compose up -d` with a placeholder showing the expected shoutrrr URL format |

**v5.1.7.9 bug-fix summary** — 6 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 95 | §13 kill-switch test | `systemctl stop wg-quick@protonvpn` runs the `protonvpn-down.sh` PreDown hook, which removes the `PROTON_KS` chain from `OUTPUT`; the verification curl that followed therefore succeeded (route falls back to ISP) — the test was checking wg-quick teardown, not the kill switch itself | Replaced with `ip link set protonvpn down`, which drops the interface without invoking PreDown — the chain stays loaded and the curl is actually blocked; recovery is `systemctl restart wg-quick@protonvpn` so the handshake state is rebuilt cleanly |
| 96 | §14 MTU verification + breakage table | Both spots recommended dropping wg0 to 1240 "as a conservative value", contradicting fix #82's establishment of 1280 as the IPv6 minimum below which IPv6 breaks on wg0; fix #82 only updated the §4 comment | Rewrote both as an explicit IPv4-only-on-wg0 trade-off with cross-reference to fix #82 |
| 97 | §3 `docker-user-rules.sh` comment | Said "NPM's 80/443 are unaffected — those match the RELATED,ESTABLISHED RETURN first" — wrong; RELATED,ESTABLISHED only matches reply traffic in an already-allowed connection. The initial SYN from LAN to NPM 80/443 matches the LAN-source RETURN; reply packets ride RELATED,ESTABLISHED. Both rules are needed | Rewrote the comment to describe both directions correctly |
| 98 | §13 router-config table | Rows for "optional 80/443 port forwards (NPM, optional if you want public access)" implied a router-side toggle was sufficient, but DOCKER-USER's final DROP applies to WAN-sourced packets reaching the FORWARD chain; the public exposure silently fails | Added a ⚠️ footnote under the table explaining the DOCKER-USER constraint and showing the additional `iptables -A DOCKER-USER -p tcp -m multiport --dports 80,443 -j RETURN` rule that would be needed in `docker-user-rules.sh` |
| 99 | §3 "What cannot be a Portainer stack" list | Listed Portainer, wg0, ProtonVPN, and Restic as the four non-stack components but omitted `docker-socket-proxy`, which is also a non-stack `docker run` for the same chicken-and-egg reason as Portainer (Portainer's `DOCKER_HOST` targets it and needs it running first) | Added `docker-socket-proxy` as a bullet alongside Portainer with the rationale |
| 100 | §8 TOC entry | Read `[Nginx Proxy Manager + local DNS records](#8-nginx-proxy-manager)` — but the local-DNS-records subsection lives in §6 (Pi-hole admin → Local DNS → DNS Records), not §8; misleading TOC suffix from an earlier doc structure that has since shifted | Dropped the "+ local DNS records" suffix; entry now matches the actual section title |

**v5.1.7.8 bug-fix summary** — 3 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 92 | §7 Step-CA | Provisioner password was generated by Step-CA on first start and printed to logs exactly once — fragile because the log line can be missed and `daemon.json`'s `max-size=10m, max-file=3` log rotation can age it out within hours; lost password = destroy volume + re-init CA + re-install root cert on every device | Set `DOCKER_STEPCA_INIT_PASSWORD` in Portainer's stack env-vars panel before first deploy (same pattern as Pi-hole's `FTLCONF_webserver_api_password`); rewrote the surrounding callout to describe the env-vars approach with the legacy log-extraction noted as historical context |

**v5.1.7.7 bug-fix summary** — 1 new fix:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 91 | Top-of-doc revision-notes chain | Each `**Revision notes vs vX:**` line was a pure pointer to the changelog block immediately below it ("N bugs fixed, see vY changelog below") — no unique information, growing by one line per release; pure bloat | Deleted the entire chain |

**v5.1.7.6 bug-fix summary** — 7 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 84 | Revision notes header | Chain at top of doc jumped from `vs v4.1` straight to `vs v5.1.3` — both v5.1 (changelog block with 23 fixes #9–#31) and v5.1.3 (changelog block with 15 fixes #32–#46) were real releases with their own blockquote changelogs and summary tables, but no `vs v5` or `vs v5.1` headers existed in the chain to describe the v5→v5.1→v5.1.3 transitions; fix #81's claim that "every other version in the chain has a corresponding header" was inaccurate when applied to this gap | Inserted `Revision notes vs v5:` and `Revision notes vs v5.1:` lines between the `vs v4.1` and `vs v5.1.3` entries, in chronological position |
| 85 | Changelog formatting | Three consecutive blank lines between the v5.1.7.4 and v5.1.7.3 changelog sections — introduced when the v5.1.7.4 changelog block was inserted in v5.1.7.4 and survived through v5.1.7.5; only a single blank line is used as a section separator everywhere else in the changelogs | Reduced to a single blank line, consistent with all other changelog section separators (same class of fix as #75) |
| 87 | §10 Mosquitto bind mount | `mosquitto.passwd` mount declared `:ro`, but the §10 instructions immediately tell the user to populate the file via `docker exec -it mosquitto mosquitto_passwd -c /mosquitto/config/mosquitto.passwd <user>` — a write operation that fails with EACCES on a read-only mount; additionally, on first deploy without a pre-existing host file, Docker auto-creates the bind-mount source as a *directory*, causing Mosquitto's config parse to fail (same class as fix #44) | Dropped `:ro` from the `mosquitto.passwd` mount; added an explicit `touch` step before stack deploy and an explanatory note in the YAML comment about the trade-off |
| 88 | §3 directory mkdir | `mkdir -p /opt/{dns,step-ca,npm,homeassistant,kuma,watchtower}` omitted `portainer` from the brace expansion, but the §14 directory tree at the end of the doc lists `/opt/portainer/` (with a "no compose file — bootstrapped via docker run" note); either the directory had to exist on disk or the §14 row had to be dropped | Added `portainer` to the brace expansion so the directory matches what §14 documents |
| 89 | §3 DOCKER-USER prose | "Binding admin ports to `127.0.0.1`, which we do from §6 onward" — Portainer's own `docker run` in §3 already binds to `127.0.0.1:9443:9443`, so the loopback-binding pattern starts in §3, not §6; the prose lagged the code | Corrected to "from §3 onward" with a parenthetical noting Portainer as the first instance |
| 90 | §13 health push script | `[ "$CRIT" = "0x00" ]` is a strict string match; some `smartctl` versions emit the Critical Warning value as bare `0` rather than `0x00`, which would flip a healthy drive's monitor to "down" as a false alarm | Replaced with `[ "$((CRIT))" -eq 0 ]` — arithmetic expansion normalizes both `0` and `0x00` (and any real warning bits) to an integer, preserving the broken-state behaviour while accepting both output formats |

**v5.1.7.5 bug-fix summary** — 3 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 81 | Revision notes header | Missing `Revision notes vs v5.1.7.2:` line — the chain at the top of the doc jumped from `vs v5.1.7.1` straight to `vs v5.1.7.3`, even though v5.1.7.3 was a released version with its own changelog block and summary table; every other version in the chain had a corresponding header | Inserted the missing line between the `vs v5.1.7.1` and `vs v5.1.7.3` entries, in chronological position |
| 82 | §4 `protonvpn.conf` MTU comment | Fix #72 added a comment that said "keeping wg0 below 1320 - 60 = 1260 prevents the stacked packet from exceeding 1320 and causing fragmentation" and then closed with "1280 is the safe floor (IPv6 minimum MTU)" — silently contradicting itself, since 1280 is not below 1260; readers were left to deduce that 1280 was a deliberate trade-off rather than a strict no-fragmentation value | Rewrote the paragraph to state the trade-off explicitly: strict no-fragmentation needs ≤1260; 1280 is the IPv6 minimum below which IPv6 breaks on wg0; we pick 1280 and accept slight PMTU-discovery overhead to keep IPv6 working |
| 83 | v5.1.7.3 changelog text + summary table | Fix #76's entry was internally inconsistent — said "all four `curl` calls" (correct count in the script) but then claimed "with three calls that is up to 6 minutes per invocation"; the script's `if/else` structure means exactly two calls fire per invocation (one SoC branch + one NVMe branch), so the worst-case stall is ~4 minutes, not 6; same wording was mirrored in the v5.1.7.3 summary table | Corrected the per-invocation count to "two" and the worst-case duration to "~4 minutes" in both the changelog text and the summary table |

**v5.1.7.4 bug-fix summary** — 4 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 77 | §3 `docker-user-rules.sh` | Only `iptables` rules were present; containers binding to `::` (IPv6 all-interfaces) bypassed the DOCKER-USER lockdown entirely on IPv6 | Added matching `ip6tables` block: RELATED,ESTABLISHED, wg0, ULA (`fc00::/7`), loopback (`::1/128`) RETURNs and a final DROP; updated verification command to check both tables |
| 80 | §13 Health push script | Stale `FIX #49` comment appeared inside the sysfs-unreadable `else` branch explaining that `--cacert` is unnecessary on plain HTTP — true, but irrelevant inside the error branch; the explanation already appears correctly on the `KUMA_BASE` declaration | Removed the misplaced comment from the error branch |

**v5.1.7.3 bug-fix summary** — 4 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 73 | v5.1 changelog | Fix #24 (remove `-k` from §13 functional test curl) was in the summary table and applied to the doc, but absent from the changelog text — the sequence jumped #23 → #25; the "23 new fixes" header was correct against the table but misleading against the changelog | Added the missing changelog entry between #23 and #25 |
| 74 | Revision notes (top of doc) | "Revision notes vs v4" and "vs v4.1" both said "see v5 bug-fix changelog below" — no such section existed; the five structural v5 changes had no changelog | Added `v5 bug-fix summary` table documenting the five v5 structural changes |
| 75 | Changelog formatting | Three consecutive blank lines between v5.1.4 and v5.1.3 changelog sections — fix #31 removed a stray double blank line elsewhere but this one was missed | Reduced to a single blank line, consistent with all other changelog section separators |
| 76 | §13 Health push script | All four `curl` calls had no `--max-time` — on a temporarily unresponsive Kuma, each call blocks for curl's default timeout (~2 min); the script's `if/else` structure means exactly two calls fire per invocation (one SoC branch + one NVMe branch), so a single run can stall for ~4 minutes; with a 60-second cron period, processes pile up and don't resolve until Kuma recovers | Added `--max-time 5` to all four calls |

**v5.1.7.2 bug-fix summary** — 4 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 69 | v5.1.7.1 summary table | Header said "4 new fixes" but the table contained 7 entries (#62–#68); the revision note at the top correctly said "Seven bugs fixed" | Corrected to "7 new fixes" |
| 72 | §4 `protonvpn.conf` | `MTU = 1320` had no comment explaining it is ProtonVPN's server ceiling, why it differs from wg0's 1280, or what to do on low-path-MTU ISP links — left readers without context on the relationship between the two MTU values | Added inline comment explaining the ceiling, the stacked-encapsulation arithmetic, and the §14 probe as the diagnostic tool |

**v5.1.7.1 bug-fix summary** — 7 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 62 | §5 wg0 server config | `MTU = 1320` — after wg0 encapsulation (~60 B overhead) the packet exceeds protonvpn's own 1320-byte MTU, causing fragmentation or silent large-transfer stalls on the stacked tunnel | Lowered to `MTU = 1280` (IPv6 minimum MTU, safe floor for wg0-inside-protonvpn); added comment explaining the interaction |
| 63 | §5 wg0 client config | `DNS = 10.10.0.1` only — with `AllowedIPs = ::/0`, IPv6-first OSes (iOS, Android, macOS) attempt DNS over IPv6 and bypass Pi-hole entirely when no IPv6 DNS address is listed, leaking DNS to the carrier resolver; also client `MTU = 1320` didn't match the now-corrected server value | Added `fd00:10:10::1` to DNS field; aligned client MTU to `1280` |
| 65 | §13 Health push script | No `else` branch on the `if [ -e "$NVME_DEV" ]` check — when the device path is wrong or missing, no push is sent; Kuma's push monitor heartbeat expires silently and shows "down" with no message, indistinguishable from a real SMART critical warning | Added `else` branch that pushes `status=down&msg=NVME_DEV+<path>+not+found` with a pointer to `lsblk` for diagnosis |
| 66 | §14 MTU verification | §14 prose said "Both wg0 and protonvpn are set to MTU 1320" — fix #62 changed wg0 to 1280; the stale description, ping probe range, and troubleshooting table row all referred to the old value | Updated prose, probe range, and troubleshooting row to reflect wg0 MTU 1280 |

**v5.1.7 bug-fix summary** — 5 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 57 | §13 Health push script | All three `curl` calls carried `--cacert /opt/step-ca/homelab-root-ca.crt` — fix #49 changed `KUMA_BASE` to `http://` (plain HTTP); curl ignores `--cacert` on plain HTTP; the flag was dead code and the TLS/MITM rationale in the comment was stale | Removed `--cacert` from all three calls; updated comment to note that loopback HTTP needs no certificate |
| 58 | §3 DOCKER-USER chain | Missing `127.0.0.0/8` RETURN rule — host-to-container loopback traffic (health push to `127.0.0.1:3001`, `docker run` in backup volume loop) has source `127.x.x.x`, which is not matched by the `172.16.0.0/12` inter-container RETURN and was silently DROP'd | Added `iptables -A DOCKER-USER -s 127.0.0.0/8 -j RETURN` before the DROP, with explanatory comment |
| 59 | §10 Mosquitto | Port binding comment claimed `localhost:1883` works alongside `192.168.70.5:1883` — port is bound to `192.168.70.5` only; nothing listens on `127.0.0.1:1883`; HA MQTT integration configured with `localhost` would get connection refused | Corrected comment to state HA must use `192.168.70.5:1883` |
| 60 | §2 Unattended upgrades | `Automatic-Reboot-Time "03:00"` — backup timer runs at `04:00` with `Persistent=true`; a reboot finishing close to 04:00 can trigger backup immediately before containers are fully up | Changed to `02:00`; added note explaining the 04:00 backup timer interaction and the dead zone to avoid |
| 61 | §14 gitleaks | `pip install --user pre-commit` fails on Ubuntu 24.04 with "externally-managed-environment" (PEP 668 enforcement); `--user` does not bypass this restriction | Replaced with `sudo apt install -y pipx && pipx install pre-commit && pipx ensurepath`; added note explaining why |

**v5.1.6 bug-fix summary** — 5 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 52 | §5 Client config | `Address = 10.10.0.2/24, fd00:10:10::2/64` — subnet masks on a WireGuard client `Address` cause the interface to claim ownership of the whole subnet locally, breaking peer-to-peer VPN routing and potentially conflicting with the client device's routing table | Corrected to `/32` and `/128` (host masks), consistent with the server-side `[Peer]` `AllowedIPs` |
| 54 | §14 UFW deny note | Claimed NPM reaches HA "via the host loopback" — NPM is a container on the `172.31.x.x` Docker bridge and reaches HA at `192.168.70.5:8123`; the conclusion (rule won't block NPM) was coincidentally correct but the reason was factually wrong | Corrected to state NPM traffic originates from `172.31.x.x`, not the LAN range, so the LAN deny rule does not affect it |

**v5.1.5 bug-fix summary** — 3 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 49 | §13 Health push script | `KUMA_BASE` used `https://kuma.home.arpa/api/push` — this resolves via Pi-hole DNS then traverses NPM; if either is down (or quiesced during a backup run), the push fails silently with a DNS/connection error instead of a meaningful status push | Changed to `http://127.0.0.1:3001/api/push`, which hits Kuma directly on its loopback-bound port, bypassing Pi-hole and NPM entirely |
| 51 | §14 Troubleshooting | "Watchtower broke a service" fix showed `docker compose pull && docker compose up -d` without a `cd` — fails with "no configuration file provided" if run from any directory other than `/opt/<service>` | Prepended `cd /opt/<service> &&` to make the command self-contained |

**v5.1.4 bug-fix summary** — 2 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|

**v5.1.3 bug-fix summary** — 15 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 33 | §3 daemon.json | `default-address-pools` base was `172.17.0.0/16` — Docker's own `docker0` bridge defaults to `172.17.0.1`; using the same range as the auto-allocation pool risks a prefix collision on daemon restart | Changed base to `172.20.0.0/14`, which avoids both `docker0` (`172.17.x`) and the manually-pinned `172.30–172.31.x` ranges |
| 36 | §3 Portainer | The "no `-v /var/run/docker.sock`" security note appeared *after* the `docker run` command — readers scanning the command block had no context before running it | Converted to a `> ℹ️` callout placed *before* the command; removed the trailing inline note |
| 37 | §14 troubleshooting table | `sudo ip rule flush` deletes all routing policy rules including the kernel defaults at priorities 0/32766/32767, breaking all routing until reboot — presented as the fix for a stale Proton rule | Replaced with targeted `ip rule del priority 50` + `ip rule del priority 51`, which remove only the rules this guide adds |
| 38 | §8 NPM proxy hosts | No "Ignore Certificate" warning for `stepca.home.arpa` — Step-CA's backend is HTTPS and NPM may not trust the cert depending on timing, same situation as Portainer which already had the warning | Added equivalent "Ignore Certificate" callout for Step-CA |
| 40 | §2 Hostname | `echo -e "127.0.0.1 localhost\n192.168.70.5 berrypi5"` overwrote `/etc/hosts` without the `::1 localhost` IPv6 loopback entries — removing them breaks IPv6 loopback resolution for Docker networking and some HA integrations | Replaced with `printf` that preserves `::1 localhost ip6-localhost ip6-loopback` |
| 41 | §2 Static IP | Guide edits `50-cloud-init.yaml` directly but never disables cloud-init network management — cloud-init regenerates the file on boot and reverts the Pi to DHCP, silently breaking the static IP on the next reboot or apt upgrade that triggers cloud-init | Added `echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` immediately after `netplan apply`; also noted in the Ubuntu gotchas table |
| 42 | §10 Mosquitto | Snippet shown as "add to the homeassistant stack" was missing `mosquitto-data:` and `mosquitto-log:` entries in the top-level `volumes:` block — `docker compose up` fails with "named volume not declared" without them; also unclear that HA (host network) reaches Mosquitto via localhost | Added explicit merged `volumes:` block and network clarification comment |
| 43 | §7 Step-CA | `DOCKER_STEPCA_INIT_DNS_NAMES` lacked `localhost` and `127.0.0.1`; the guide directs bootstrap access via `https://127.0.0.1:9000` over SSH tunnel but clients got `x509: certificate is valid for [other IPs], not 127.0.0.1` | Added `localhost` and `127.0.0.1` to the DNS names list |
| 44 | §10 Mosquitto | Bind-mount paths `./mosquitto.conf` and `./mosquitto.passwd` are relative; Portainer's web-editor working directory is `/`, resolving them to `/mosquitto.conf` — Docker creates a directory instead of a file, Mosquitto fails to parse config | Changed to absolute paths `/opt/homeassistant/mosquitto.conf` and `/opt/homeassistant/mosquitto.passwd` |
| 45 | §13 Health push | All three `curl` calls used `-sk` (`-s -k`) — `-k` silently disabled TLS verification, making pushes susceptible to local MITM and undermining the whole Step-CA setup | Replaced `-k` with `--cacert /opt/step-ca/homelab-root-ca.crt`; root CA already on disk from §7, no system-wide install needed |

**v5 bug-fix summary** — the 5 fixes applied in the initial v5 release:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| A | §4 ProtonVPN | Kill switch used inline `PostUp`/`PreDown` with multiple `! -d` flags — rejected by iptables 1.8.10 (nf_tables backend) on Ubuntu 24.04 | Moved all kill-switch logic to external `protonvpn-up.sh` / `protonvpn-down.sh` scripts; replaced multi-flag rules with a named `PROTON_KS` chain |
| B | §6 Pi-hole | v5 (Alpine base) introduced `FTLCONF_*` env var schema; old vars (`WEBPASSWORD`, `DNSMASQ_LISTENING`, `PIHOLE_DNS_`) silently ignored | Updated stack to use `FTLCONF_*` throughout; added migration note |
| C | §3 Docker | Admin ports bound to `0.0.0.0` allowed any LAN client to reach Portainer, NPM admin, Pi-hole admin, Step-CA, and Kuma directly, bypassing UFW | Bound all admin ports to `127.0.0.1`; added `DOCKER-USER` chain and `proxy-net` bridge |
| D | §12 Backup | Only Pi-hole and HA were quiesced; NPM, Portainer, and Kuma were tarred live, producing inconsistent snapshots | Added NPM, Portainer, and Kuma to `STOP_LIST` |
| E | §7 Step-CA / §8 NPM | `docker-socket-proxy` not present; Portainer and Watchtower mounted `/var/run/docker.sock` directly — root-equivalent on the host | Added `tecnativa/docker-socket-proxy`; updated Portainer and Watchtower to use `DOCKER_HOST=tcp://docker-socket-proxy:2375` |

> ℹ️ The v5 fixes above are structural changes introduced with the v5 rewrite, not individually numbered like the incremental fixes in v5.1 onward. The v5.1 changelog (#9 onward) covers bugs found after the v5 release.

**v4.1 bug-fix summary** — the 8 fixes applied to the previous revision:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 1 | §7 Step-CA | `step-ca` (Docker container name) absent from `DOCKER_STEPCA_INIT_DNS_NAMES`; NPM's ACME client failed x509 hostname validation | Added `step-ca` as first entry in DNS names |
| 2 | §4 IPv6 kill switch | `ip6tables PROTON_KS` had no exemption for `wg0` egress or `fd00:10:10::/64`; Pi couldn't reach wg0 peers over IPv6 while Proton was running | Added `-o wg0 -j RETURN` and `-d fd00:10:10::/64 -j RETURN` before the final REJECT |
| 3 | §8 NPM | `docker exec npm update-ca-certificates` only persisted into the container's writable layer, lost on every recreate; ACME broke silently after any image update or stack redeploy | Replaced one-off exec with `entrypoint:` override that runs `update-ca-certificates && /init` on every container start |
| 5 | §3 DOCKER-USER | `iptables -A DOCKER-USER -j RETURN` appeared after the terminal `DROP` — unreachable and misleading | Removed the dead RETURN |
| 6 | §3 docker-socket-proxy | `DELETE=1` missing; `WATCHTOWER_CLEANUP: "true"` silently failed, old image layers accumulated on the SSD | Added `-e DELETE=1` to the `docker run` command |
| 7 | §14 troubleshooting | Table said "don't chattr +i" — contradicted §2's deliberate use of it post-setup | Updated to explain chattr +i is intentional and applied after setup |
| 8 | §13 Watchtower | `WATCHTOWER_LABEL_ENABLE: "true"` with no labelled containers anywhere; Watchtower did nothing on every Sunday run | Added opt-in label to the Kuma stack as a worked example; added explanatory note in the Watchtower section |

**v4 changes summary** — for your own reference when comparing to v3:

- **Docker→UFW bypass closed.** All admin UIs (Portainer 9443, Pi-hole 8080, Step-CA 9000, Kuma 3001) bound to `127.0.0.1`. Shared `proxy-net` Docker bridge created so Caddy can reach them by container name. UFW `after.rules` adds a `DOCKER-USER` chain that drops all non-LAN, non-VPN container egress as defence-in-depth.
- **IPv6 on wg0.** ULA `fd00:10:10::/64` carried inside the tunnel; clients now route `::/0` over wg0 so dual-stack mobile data doesn't leak v6 outside the tunnel.
- **Pi-hole v6** with new `FTLCONF_*` env var schema (Alpine base). Web password moved to Portainer env vars panel, out of YAML/git.
- **chrony** with LAN-router NTP preferred; NTP exception in the Proton kill switch (UDP/123 RETURN). Boot-time clock drift during Proton outages no longer cascades into Step-CA TLS failures.
- **docker-socket-proxy.** Portainer and Watchtower no longer mount `/var/run/docker.sock` directly; both go through `tecnativa/docker-socket-proxy` with `EXEC=0` and minimal API capabilities.
- **HA: `privileged: true` removed.** Explicit `cap_add: [NET_ADMIN, NET_RAW, SYS_NICE]` plus `devices:` for Zigbee/Z-Wave (commented examples).
- **SMART + thermal monitoring** via Kuma push monitors fed by a cron-driven script (`homelab-health-push.sh`).
- **Image pins refreshed:** Pi-hole `2026.04.0`, HA `2026.5`, Caddy `2.8.4-alpine`, Portainer `2.27.5`, Step-CA `0.28.4`, Kuma `1.23.16`, Mosquitto `2.0.21`, Unbound `1.22.0`, docker-socket-proxy `v0.4.2`, Watchtower `1.7.1`.
- **NPM removed in v5.1.7.17.** Replaced by Caddy as the reverse proxy + ACME client — see fix #115 and the new §8.
- **MTU verification** procedure for stacked wg0+Proton tunnels added to ops.
- **gitleaks pre-commit hook** for the config repo.
- **Image-pin review cadence** recommendation added (quarterly).
- **TOC anchor for §9 fixed.**
- Pre-flight cleaned up; SD-card warning removed (the rest of the doc assumes SSD).
- Active cooler recommendation added.
