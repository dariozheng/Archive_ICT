# Homelab Setup Guide v5.1.7.11 — Ubuntu Server 24.04 LTS on Raspberry Pi 5

> **Bug-fix changelog (v5.1.7.11):**
> - §4 `protonvpn-up.sh` kill switch: added `iptables -A PROTON_KS -d 172.16.0.0/12 -j RETURN` before the final `REJECT`. Without it, host→container traffic over Docker bridges is rejected by the kill switch: the host's own DNS queries (resolv.conf → `127.0.0.1:53` → docker-proxy → Pi-hole container at `172.30.0.x`), `curl 127.0.0.1:9443` to Portainer, `curl 127.0.0.1:3001` to Kuma from the health-push script, etc. all carry a destination of a *container* IP, which is not a LOCAL address (so the `ADDRTYPE LOCAL` RETURN doesn't catch it) and not in the LAN/wg0 ranges — so it falls through to `REJECT`. Same class as fix #58, which added `-s 127.0.0.0/8` to `DOCKER-USER` for the host-loopback *source* direction; this is the host→container *destination* direction in `PROTON_KS`. Symptom: after §4, Portainer/Pi-hole admin and the Pi's own DNS all break; `systemctl stop wg-quick@protonvpn` makes them work again because that tears the chain down. `protonvpn-down.sh` needs no edit — it flushes the whole chain (fix #103)
> - §8 NPM `entrypoint:`: changed `update-ca-certificates && /init` to `update-ca-certificates && exec /init`. Without `exec`, `/bin/sh` stays as PID 1 and `/init` runs as its child; NPM's s6-overlay base image hard-checks `getpid() == 1` in `s6-overlay-suexec` and aborts with `fatal: can only run as pid 1`, so the container crash-loops forever (the cert-update line prints once per restart, masking the loop on a casual log glance). `exec` replaces the shell process so `/init` inherits PID 1. Fix #3 introduced the entrypoint override with the right intent but dropped `exec`; `jc21/nginx-proxy-manager:2.12.3` ships s6-overlay v3.x which enforces the PID 1 check strictly (fix #104)
> - §8 SSH tunnel example: changed `ssh -L 81:127.0.0.1:81` to `ssh -L 8081:127.0.0.1:81`. Port 81 is privileged (<1024); binding it on the *client* side fails with `bind: Permission denied` for any non-root user on macOS/Linux. The forwarded-to port on the Pi stays `81` (that's where NPM's admin UI listens); only the local listen-port changes. Same pattern §6 already uses correctly with `8080:127.0.0.1:8080`. Access URL updated to `http://127.0.0.1:8081` to match (fix #105)
> - §2 UFW + §10 + §15: added `ufw allow` rules for port 8123. Home Assistant runs `network_mode: host`, binding directly to `0.0.0.0:8123` on the Pi — it is NOT behind Docker's port-publishing NAT, so Docker adds no iptables rules for it and UFW's `default deny incoming` drops every packet to 8123. The §2 rule set never opened the port, yet §10 says "Access `http://192.168.70.5:8123` and onboard" and §15 claimed 8123 "remains reachable from the whole LAN" — both false as written. Worse, NPM (a container on `172.31.x.x`) forwarding `ha.berrypi5.lan` to `192.168.70.5:8123` is also dropped, so the HA proxy host 504s. Added `ufw allow from 172.16.0.0/12 to any port 8123` (NPM→HA, required) and `ufw allow from 192.168.68.0/22 to any port 8123` (LAN-direct, for the §10 onboarding step) to §2; updated the §15 deny-to-restrict note to use `ufw insert 1` so the deny precedes the allow (fix #106)
> - §6 Pi-hole `FTLCONF_dns_upstreams`: changed `172.30.0.2#5335` to `172.30.0.2` and corrected the surrounding comment and the §6 troubleshooting callout. The `#5335` port convention comes from *bare-metal* Pi-hole + Unbound setups, where both run on the host and Unbound must listen on a non-53 port to avoid colliding with Pi-hole's own `:53`. In this guide Unbound runs in its own container with its own IP (`172.30.0.2`) and its own port namespace — the `mvance/unbound-rpi` image listens on **port 53** by default, so `172.30.0.2#5335` pointed Pi-hole at a port nothing was listening on and upstream resolution silently failed (no internet via Pi-hole). Dropping the `#5335` lets FTL default to port 53, which is where Unbound actually is. The stale comment ("Pi-hole v6 keeps the v5 #port separator") and the troubleshooting callout's `["172.30.0.2#5335"]` / `172.30.0.2:5335` references were corrected to match (fix #107)

> **Bug-fix changelog (v5.1.7.10):**
> - §7 Step-CA CLI fallback: regression introduced by fix #92 — the Portainer-path instructions correctly tell the user to set `DOCKER_STEPCA_INIT_PASSWORD` in the stack's env-vars panel, but the immediately-adjacent CLI fallback (`cd /opt/step-ca && docker compose up -d`) silently ignored the password requirement; a user following the CLI path would get the random-generated-and-logged behaviour back (the very thing fix #92 set out to eliminate). Patched the CLI fallback to pass `DOCKER_STEPCA_INIT_PASSWORD='...'` inline, matching the pattern used by the Pi-hole `dns` stack's CLI fallback (fix #101)
> - §13 Watchtower CLI fallback: pre-existing same-class bug — the prose tells the user to set `WATCHTOWER_NOTIFICATION_URL` in the Portainer env-vars panel, but the CLI fallback (`cd /opt/watchtower && docker compose up -d`) didn't pass it inline, so a user following the CLI path would deploy Watchtower with notifications silently disabled and the Sunday update schedule would fire without any Telegram alerts. Patched the CLI fallback to pass `WATCHTOWER_NOTIFICATION_URL='telegram://<token>@telegram?chats=<chat-id>'` inline with a placeholder format (fix #102)

> **Bug-fix changelog (v5.1.7.9):**
> - §14 kill-switch test: replaced `systemctl stop wg-quick@protonvpn` with `ip link set protonvpn down` — the systemctl approach runs `protonvpn-down.sh` (the wg-quick PreDown hook), which removes the `PROTON_KS` chain from `OUTPUT` before the verification curl runs; the curl then succeeds (route falls back to the ISP), making the entire block a "did wg-quick clean up correctly?" test rather than a "does the kill switch hold when the tunnel drops?" test. `ip link set` drops the interface without invoking PreDown, leaving the chain loaded so the curl can actually be blocked by it. Recovery is now `systemctl restart wg-quick@protonvpn` (handshake state needs a full restart, not just `ip link set up`) (fix #95)
> - §15 MTU verification + breakage table: aligned both spots with fix #82's IPv6-minimum constraint — the verification prose said "(or to 1240 as a conservative floor)" and the breakage table said "1240 is a safe conservative value" without acknowledging that fix #82 (in §4) established 1280 as the absolute floor for retaining IPv6 on wg0; dropping below 1280 sacrifices v6 on wg0. Rewrote both as an explicit trade-off ("v4-only on wg0 in exchange for no fragmentation") so the user can choose knowingly (fix #96)
> - §3 `docker-user-rules.sh` comment: corrected the claim that "NPM's 80/443 are unaffected — those match the RELATED,ESTABLISHED RETURN first" — RELATED,ESTABLISHED only matches reply traffic in a connection that's already been allowed; the *initial* SYN from a LAN client to NPM 80/443 matches the LAN-source RETURN (`-s 192.168.68.0/22`). Reply packets in the same connection then match RELATED,ESTABLISHED. Both rules are needed; neither alone is sufficient. Rewrote the comment to describe both directions correctly (fix #97)
> - §14 router-config table + new ⚠️ note: the rows for "optional 80/TCP and 443/TCP port forwards" implied a router-side toggle was sufficient to publicly expose NPM, but DOCKER-USER drops WAN-sourced packets to containers — the source IP (external client) doesn't match any of the `-j RETURN` rules, the final `-j DROP` applies, and the public connection silently fails. Added a footnote under the table explaining the trade-off and showing the additional `iptables -A DOCKER-USER -p tcp -m multiport --dports 80,443 -j RETURN` rule that would be needed in `docker-user-rules.sh` if the user actually wants public NPM exposure (and the auth-strength implications that come with it) (fix #98)
> - §3 "What cannot be a Portainer stack" list: added `docker-socket-proxy` — the list documented Portainer, wg0, ProtonVPN, and Restic as the four non-stack components, but docker-socket-proxy is also a non-stack `docker run` (deployed in §3 above Portainer for the same chicken-and-egg reason: Portainer's `DOCKER_HOST` env var targets the proxy and needs it running first). Now listed alongside Portainer with the rationale (fix #99)
> - §8 TOC entry: removed misleading "+ local DNS records" suffix — the local-DNS-records subsection (Pi-hole admin → Local DNS → DNS Records) lives in §6, not §8. The TOC entry was a leftover from an earlier doc structure that has since shifted the DNS records to where they actually run (against Pi-hole) (fix #100)

> **Bug-fix changelog (v5.1.7.8):**
> - §7 Step-CA provisioner password: switched from "let Step-CA generate a random password and grep it out of `docker logs step-ca`" to "set `DOCKER_STEPCA_INIT_PASSWORD` in the Portainer stack's env-vars panel before first deploy" — the log-extraction approach is fragile because the log line is printed exactly once and Docker's default `json-file` driver with `max-size=10m, max-file=3` (per `daemon.json`) can age it out within hours; users who miss the window have no recovery short of destroying the `step-ca-data` volume and re-initialising the CA (which forces re-installing the new root cert on every device). Same pattern Pi-hole already uses for `FTLCONF_webserver_api_password`. Updated the YAML comment, the surrounding callout, and added historical context noting why the legacy approach existed (fix #92)
> - §12 restic backup paths + restore drill + §15 git list: added `/etc/apt/apt.conf.d/50unattended-upgrades` — §2 modifies this file to set `Unattended-Upgrade::Automatic-Reboot "true"` and `Unattended-Upgrade::Automatic-Reboot-Time "02:00"` (so security updates reboot the Pi at a sane hour), but the file was never in the backup paths, restore drill, or "what to put in git" list; a restore would silently land with the default package config and lose the customised reboot window. Updated the drill prose count from "six" to "seven config paths" (fix #93)
> - §12 setup: pre-pull `alpine:3.21` during initial restic setup — the backup script's volume-tarball loop runs `docker run --rm -v "$vol":/src -v "$STAGING":/dst alpine:3.21 tar czf ...`; if `alpine:3.21` is not in the local Docker cache when the first scheduled 04:00 backup fires and ProtonVPN is down at that moment (kill switch blocks egress), the pull fails, `set -euo pipefail` aborts the script, the `OnFailure` unit fires a Telegram alert, and no backup completes. Pulling once during setup (with the tunnel known-up) caches the image; the pin prevents Watchtower from pruning it (fix #94)

> **Bug-fix changelog (v5.1.7.7):**
> - Top-of-doc revision-notes chain: deleted. Every `**Revision notes vs vX:**` line was a one-liner pointer of the form "N bugs fixed (see vY changelog below)", adding nothing the corresponding changelog block right below it didn't already say in more detail. The chain grew by one entry per release and had become pure bloat. Fixes #81 (added missing v5.1.7.2 line) and #84 (added missing v5 + v5.1 lines) were correctly applied to the doc state at the time; the text they edited is now gone wholesale, but their numbered fix entries remain in the historical changelog as written (fix #91)

> **Bug-fix changelog (v5.1.7.6):**
> - Revision notes header: added missing `Revision notes vs v5:` and `Revision notes vs v5.1:` lines between the `vs v4.1` and `vs v5.1.3` entries — both v5.1 (changelog block with 23 fixes #9–#31) and v5.1.3 (changelog block with 15 fixes #32–#46) were real releases with their own blockquote changelogs and summary tables, but the top-of-doc chain of revision notes jumped straight from "vs v4.1" → "vs v5.1.3" with no headers describing what changed in v5.1 (vs v5) or v5.1.3 (vs v5.1); fix #81's claim that "every other version in the chain has a corresponding header" was therefore inaccurate when applied to the broader chain (fix #84)
> - Changelog formatting: removed two extra blank lines between the v5.1.7.4 and v5.1.7.3 changelog sections — three consecutive blank lines had been introduced when the v5.1.7.4 changelog block was inserted in v5.1.7.4 and survived through v5.1.7.5; only a single blank line is used as a section separator everywhere else in the changelogs (same class of bug as fix #75 fixed for v5.1.4/v5.1.3) (fix #85)
> - §12 backup script trap comment: updated the prose list of services that would otherwise be left stopped to include `mosquitto` — the comment listed "Pi-hole, HA, NPM, Portainer, and Kuma" (5 services) but `STOP_LIST` has had `mosquitto` in it since fix #56 (v5.1.6), giving 6 services; same class of doc-lag-behind-code bug as fix #48 and fix #79 (fix #86)
> - §10 Mosquitto bind mount: removed `:ro` from the `mosquitto.passwd` mount and added a pre-deploy `touch` step — the existing instructions tell the user to populate the password file via `docker exec -it mosquitto mosquitto_passwd -c /mosquitto/config/mosquitto.passwd <user>`, which is a write operation that fails with EACCES on a read-only mount; additionally, without a pre-deploy `touch`, Docker auto-creates the bind-mount source as a *directory* on first deploy, causing Mosquitto's config parse to fail (same class as fix #44 fixed for relative paths) (fix #87)
> - §3 directory mkdir: added `portainer` to the brace expansion in `mkdir -p /opt/{...}` — the §15 directory tree showed `/opt/portainer/` (with a "no compose file — bootstrapped via docker run" note) but `/opt/portainer` was never actually created on disk because it was missing from the `mkdir` line; either the directory had to exist or the §15 tree had to drop the row — chose the former to match the existing §15 documentation (fix #88)
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
> - §5.1 changelog: added missing fix #24 entry — fix #24 (removing `-k` from the §14 functional test `curl` call) appeared in the v5.1 summary table and was correctly applied to the document, but was never logged in the v5.1 changelog text, leaving a gap between #23 and #25; the summary also claimed "23 new fixes" while the changelog only listed 22 (fix #73)
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
> - §15 MTU verification: corrected stale description — fix #62 set wg0 to MTU 1280 but the §15 prose still said "both tunnels are MTU 1320"; updated the ping probe range and the threshold guidance to match the new values; also corrected the troubleshooting table row that still said "lower MTU to 1280" (fix #66)
> - §12 `homelab-backup.service`: added `Requires=docker.service` — `After=` alone only orders startup; if Docker is manually stopped, the backup fires at 04:00, `docker volume ls` returns nothing, the volume-tarball loop produces no files, and restic completes successfully with only `/opt` and config files — a silent partial backup with a green exit code and no notification (fix #67)
> - §12 Restore drill: added `/etc/cloud/cloud.cfg.d` restore and `ls` step — fix #64 added this path to the backup but the drill was never updated; a drill that doesn't verify the cloud-init disable file gives false confidence that a restore will land with static IP intact (fix #68)

> **Bug-fix changelog (v5.1.7):**
> - §13 Health push script: removed stale `--cacert /opt/step-ca/homelab-root-ca.crt` from all three `curl` calls — fix #49 changed `KUMA_BASE` to `http://127.0.0.1` (plain HTTP); curl silently ignores `--cacert` on plain HTTP connections; the flag was dead code and its TLS/MITM rationale no longer applies to a loopback call (fix #57)
> - §3 DOCKER-USER chain: added `iptables -A DOCKER-USER -s 127.0.0.0/8 -j RETURN` before the DROP — host-to-container traffic on loopback (health push to `127.0.0.1:3001`, `docker run` calls in the backup volume loop) has source `127.x.x.x` which is not matched by the `172.16.0.0/12` inter-container rule and was silently DROP'd (fix #58)
> - §10 Mosquitto: corrected port binding comment — port is bound to `192.168.70.5:1883` (LAN interface only); nothing listens on `127.0.0.1:1883`; HA must connect to `192.168.70.5`, not `localhost` (fix #59)
> - §2 Unattended upgrades: changed `Automatic-Reboot-Time` from `03:00` to `02:00` and added note explaining the conflict — the backup timer runs at `04:00` with `Persistent=true`; a reboot finishing close to 04:00 can trigger the backup before containers are healthy; 02:00 provides a clean two-hour margin (fix #60)
> - §15 gitleaks: replaced `pip install --user pre-commit` with `pipx install pre-commit` — Ubuntu 24.04 enforces PEP 668 and `pip install` outside a virtual environment exits with "externally-managed-environment"; `pipx` is the Ubuntu-recommended approach and handles its own isolated environment (fix #61)

> **Bug-fix changelog (v5.1.6):**
> - §5 Client config: corrected `Address = 10.10.0.2/24, fd00:10:10::2/64` → `/32, /128` — using subnet masks on the client `Address` field tells the WireGuard interface it owns the entire subnet locally, causing the client to bypass the tunnel for peer-to-peer VPN traffic and potentially conflicting with the client device's routing table; host masks (`/32`, `/128`) are correct and consistent with the `AllowedIPs` in the server's `[Peer]` blocks (fix #52)
> - §12 `homelab-backup.service`: added `[Install]` section with `WantedBy=multi-user.target` — without it `systemctl enable homelab-backup.service` fails with "Unit file has no [Install] section"; the timer remains the correct activation path but the section prevents confusing errors during troubleshooting (fix #53)
> - §15 UFW deny note for HA port 8123: corrected wrong claim that "NPM reaches it via the host loopback" — NPM is a container on the `172.31.x.x` Docker bridge and reaches HA at `192.168.70.5:8123`; the conclusion (rule won't break NPM) was coincidentally correct but the stated reason was wrong (fix #54)
> - §12 Backup script: pinned `alpine` → `alpine:3.21` in the volume tar loop — the only unpinned image in the guide; an implicit `:latest` pull during a backup run could silently change behaviour on an Alpine major bump or fail if the registry is temporarily unavailable (fix #55)
> - §12 Backup script: added `mosquitto` to `STOP_LIST` — Mosquitto has an active broker writing to its data volume; listing it is safe unconditionally because `docker stop` is a no-op for containers that aren't running (fix #56)

> **Bug-fix changelog (v5.1.5):**
> - §13 Health push script: changed `KUMA_BASE` from `https://kuma.berrypi5.lan/api/push` to `http://127.0.0.1:3001/api/push` — the NPM/DNS chain requires Pi-hole and NPM to be running; the loopback URL hits Kuma directly and keeps pushes working when either is down or quiesced during a backup run (fix #49)
> - §12 Backup script: changed `/etc/systemd/system/homelab-backup.service.d` (directory) to `/etc/systemd/system/homelab-backup.service.d/notify.conf` (explicit file) — all other systemd unit entries in the backup path list individual files; backing up the directory works but is inconsistent and could pick up unrelated drop-ins added by other packages (fix #50)
> - §15 Troubleshooting: added `cd /opt/<service> &&` to the Watchtower rollback fix — the `docker compose` commands require a compose file in the working directory; without the `cd`, the command fails silently with "no configuration file provided" if run from any other directory (fix #51)

> **Bug-fix changelog (v5.1.4):**
> - §12 Backup failure notifications: changed `OnFailure=homelab-backup-notify@%n.service` to `@%p.service` — `%n` expands to the full unit name including its `.service` suffix (`homelab-backup.service`), producing the invalid instance `homelab-backup-notify@homelab-backup.service.service` and silently failing to trigger the notification on backup failure (fix #47)
> - §12 Restore drill: corrected "three config dirs" to "four" — fix #35 added `/etc/sysctl.d` to the drill, making it four directories (wireguard, netplan, chrony, sysctl.d), but the prose description was never updated (fix #48)

> **Bug-fix changelog (v5.1.3):**
> - §12 Backup script: replaced `for vol in $(docker volume ls -q)` with `mapfile -t VOLUMES < <(docker volume ls -q)` + `for vol in "${VOLUMES[@]}"` — the original command word-splits on volume names containing spaces or special characters, silently skipping them (fix #32)
> - §3 daemon.json: changed `default-address-pools` base from `172.17.0.0/16` to `172.20.0.0/14` — `172.17.x` is Docker's own `docker0` bridge address; using it as the auto-allocation pool risks collisions with the pre-existing bridge on restart (fix #33)
> - §13 Kuma push monitors: added explicit note to set each Push monitor's heartbeat interval to ≥60s — the cron fires every 60s, and a shorter heartbeat causes false "down" alerts between pushes (fix #34)
> - §12 Restore drill: expanded to also restore and verify `/etc/netplan`, `/etc/chrony`, and `/etc/sysctl.d` — the original only tested `/etc/wireguard`, leaving critical config dirs unverified (fix #35)
> - §3 Portainer: moved the "no `-v /var/run/docker.sock`" explanation to a callout *before* the `docker run` command rather than a note after it — readers scanning the command block need the context before running it (fix #36)
> - §15 troubleshooting table: replaced `sudo ip rule flush` with targeted `ip rule del priority 50/51` — `ip rule flush` deletes kernel-default rules at priorities 0/32766/32767, breaking all routing until reboot (fix #37)
> - §8 NPM proxy hosts: added "Ignore Certificate" warning for `stepca.berrypi5.lan` — Step-CA's backend is HTTPS with a cert that NPM may not automatically trust, same as Portainer; missing this causes a 502 (fix #38)
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
> - §3 + §15 Portainer: added `-e DOCKER_HOST=tcp://docker-socket-proxy:2375` to both the initial `docker run` and the update command in §15; updated first-run wizard note accordingly (fix #17)
> - §5 wg0.conf: clarified that ip6tables FORWARD rules are unconditional — comment previously implied they were optional like the MASQUERADE rule (fix #18)
> - §3 daemon.json: added `default-address-pools` to prevent Docker's auto-allocator colliding with the manually-pinned `proxy-net` (`172.31.0.0/24`) and `dns-net` (`172.30.0.0/24`) subnets (fix #19)
> - §2 + §6 systemd-resolved: moved `chattr +i /etc/resolv.conf` out of the §2 early-setup block (where it would block netplan/cloud-init) into a new deferred step at the end of §6 after Pi-hole is confirmed working (fix #20)
> - §10 Mosquitto: added warning that `mosquitto_passwd -c` overwrites the password file — must not be used when adding a second user (fix #21)
> - §3 Docker install: added warning that `newgrp docker` only affects the current shell; a fresh login is needed before running `docker` commands without `sudo` in other terminals (fix #22)
> - §11 DDNS: fixed typo "fastback-up" → "fallback" (fix #23)
> - §14 Functional tests: removed `-k` from `curl -k https://ha.berrypi5.lan` — `-k` suppresses TLS errors, defeating the entire point of the test (verifying the root CA is trusted on the client); added inline comment explaining the check is intentionally strict (fix #24)
> - §9 gateway table: renamed "Option C" → "Option B" — the table jumped from A to C after an earlier edit removed Option B (fix #25)
> - §15 Ubuntu gotchas: updated `chattr +i` cross-reference from "(see §2)" → "(see §6)" following fix #20 (fix #26)
> - §12 restore drill: added `sudo bash -c '...'` wrapper — `/root/.restic-env` is `chmod 600` root-only; running `source` without sudo gives "Permission denied" for the `pi` user (fix #27)
> - §15 troubleshooting table: fixed `docker compose pull && up -d` → `docker compose pull && docker compose up -d` — `up -d` alone is not a valid command (fix #28)
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
> - §15 troubleshooting table: removed the stale "don't chattr +i" note that contradicted §2's deliberate use of it after setup (fix #7)
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
- Step-CA — internal certificate authority
- Nginx Proxy Manager — reverse proxy with Step-CA ACME
- Portainer — Docker UI
- Uptime Kuma — service monitoring
- Restic — encrypted backups
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
8. [Nginx Proxy Manager](#8-nginx-proxy-manager)
9. [LAN Gateway — keep the router, not the Pi](#9-lan-gateway--keep-the-router-not-the-pi)
10. [Home Assistant Container](#10-home-assistant-container)
11. [DDNS](#11-dynamic-dns-ddns)
12. [Backups (Restic)](#12-backups-with-restic)
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
          - 1.1.1.1    # fallback during initial setup before Pi-hole is running
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
nameserver 1.1.1.1
options edns0 timeout:1" | sudo tee /etc/resolv.conf
```

The fallback `1.1.1.1` is only used if `127.0.0.1:53` is unreachable (Pi-hole container down). With `timeout:1` the resolver fails over fast. This is preferable to a DNS-less box during maintenance.

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

# NPM (HTTP/HTTPS reverse proxy)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# WireGuard remote access
sudo ufw allow 51820/udp

# DNS / web from VPN clients
sudo ufw allow in on wg0 to any port 53 comment 'DNS for VPN clients'
sudo ufw allow in on wg0 to any port 80,443 proto tcp comment 'NPM via VPN'

# DNS from home LAN (Pi-hole)
sudo ufw allow from 192.168.68.0/22 to any port 53

# FIX #106: Home Assistant (§10) runs network_mode: host, binding directly to
# 0.0.0.0:8123 on the Pi. It is NOT behind Docker's port-publishing NAT, so
# Docker adds no iptables rules for it and UFW's `default deny incoming` would
# otherwise drop every packet to 8123 — breaking both LAN-direct access AND
# NPM's ha.berrypi5.lan proxy host (NPM is a container on 172.31.x.x and
# forwards to 192.168.70.5:8123). These rules are added now even though HA is
# deployed in §10; UFW happily allows a port nothing is listening on yet.
sudo ufw allow from 172.16.0.0/12 to any port 8123 comment 'NPM container -> HA on host network'
sudo ufw allow from 192.168.68.0/22 to any port 8123 comment 'HA direct from LAN'
# Optional — also allow wg0 clients to reach HA directly (not just via NPM):
# sudo ufw allow in on wg0 to any port 8123 comment 'HA via VPN'

sudo ufw enable
sudo ufw status verbose
```

### ⚠️ Docker bypasses UFW — closed in §3

When a container exposes a port with `-p 9443:9443`, Docker writes rules into the `DOCKER` chain that run **before** UFW's user rules. The result: Portainer (9443), NPM admin (81), Step-CA (9000), Kuma (3001), Pi-hole admin (8080), and Home Assistant (8123, host network) would otherwise be reachable from every LAN client even though `ufw status` claims only 22/80/443/53/51820 are open.

This is addressed in **§3** (after Docker is installed) by:
1. Binding admin-port containers to `127.0.0.1` only, so NPM on a shared bridge is the only thing that can reach them.
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
  ]
}
```

> ℹ️ **Why `default-address-pools`:** This guide manually pins `proxy-net` to `172.31.0.0/24` and `dns-net` to `172.30.0.0/24`. Both sit inside Docker's default auto-allocation range (`172.16.0.0/12`). Without this setting, Docker could auto-assign a new network the same prefix, causing an address conflict that silently breaks routing. The pool above confines auto-allocation to `172.20.0.0/14` (covering `172.20–172.23.x`), which avoids both the `docker0` default bridge (`172.17.x`) and our manually-pinned `172.30–172.31.x` ranges. If you already have Docker networks from a previous install, inspect them with `docker network ls` and `docker network inspect <name>` before restarting.

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
# NPM's 80/443 from LAN: the initial SYN matches the LAN-source RETURN
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

# ip6tables equivalents — containers that bind to '::' (IPv6 all-interfaces)
# would otherwise bypass the lockdown entirely on IPv6. Docker creates a
# DOCKER-USER chain for ip6tables in the same way it does for iptables.
ip6tables -F DOCKER-USER
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
sudo ip6tables -nvL DOCKER-USER    # verify the IPv6 chain is populated
```

Test it later (once you have a container running on a port): from another LAN host, hit one of the loopback-bound admin ports — it should fail. From a wg0 client, it should fail too (because the RETURN happens before the container's exposed port; the LAN/wg0 RETURNs only catch ports bound to 0.0.0.0). The intent is: a container that forgets to bind to loopback is still not exposed to a hypothetical WAN-side attacker if someone accidentally port-forwards.

### Create the shared `proxy-net` network

Every web UI in this guide binds its admin port to `127.0.0.1` so it can't be reached directly from the LAN. NPM (§8) sits on a shared bridge network with all of them so it can reach each container by name. Create that network once, up front:

```bash
docker network create --driver bridge --subnet 172.31.0.0/24 proxy-net
```

### docker-socket-proxy (Portainer + Watchtower backend)

Both Portainer and Watchtower need Docker API access. Mounting `/var/run/docker.sock` into a container is root-equivalent on the host — a CVE in either image gives an attacker the whole machine. `tecnativa/docker-socket-proxy` exposes only the API endpoints each tool actually needs:

```bash
docker run -d \
  --name docker-socket-proxy \
  --restart=unless-stopped \
  --network proxy-net \
  --read-only \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e CONTAINERS=1 \
  -e IMAGES=1 \
  -e NETWORKS=1 \
  -e VOLUMES=1 \
  -e SERVICES=1 \
  -e TASKS=1 \
  -e NODES=1 \
  -e INFO=1 \
  -e VERSION=1 \
  -e SYSTEM=1 \
  -e POST=1 \
  -e DELETE=1 \
  -e EXEC=0 \
  -e BUILD=0 \
  -e COMMIT=0 \
  -e CONFIGS=0 \
  -e DISTRIBUTION=0 \
  -e PLUGINS=0 \
  -e SECRETS=0 \
  -e SESSION=0 \
  -e SWARM=0 \
  -e AUTH=0 \
  tecnativa/docker-socket-proxy:0.3.0
```

> ℹ️ **FIX #6:** `DELETE=1` is required. Watchtower's `WATCHTOWER_CLEANUP: "true"` issues `DELETE /images/{id}` after pulling a new image. Without this flag the proxy blocks those calls, Watchtower silently skips cleanup, and old image layers accumulate on the SSD over time.

### Portainer (pinned, loopback-bound)

> ⚠️ **Start `docker-socket-proxy` first** (above), then Portainer. Portainer is configured with `DOCKER_HOST=tcp://docker-socket-proxy:2375` and will attempt to reach the proxy immediately on startup. If the proxy container isn't running yet, Portainer logs a connection error. Docker's `--restart=unless-stopped` will keep retrying, so it recovers automatically — but starting in order avoids the noise.

> ℹ️ **No `-v /var/run/docker.sock` mount.** Portainer talks to Docker exclusively through `docker-socket-proxy` over `proxy-net`. A Portainer compromise therefore can't run arbitrary host commands. Access via NPM at `https://portainer.berrypi5.lan` once §8 is up. During initial bootstrap, before NPM exists, use the SSH tunnel: `ssh -L 9443:127.0.0.1:9443 pi@192.168.70.5` then open `https://127.0.0.1:9443` on your laptop.

```bash
docker volume create portainer_data

docker run -d \
  --name portainer \
  --restart=unless-stopped \
  --network proxy-net \
  -p 127.0.0.1:9443:9443 \
  -e DOCKER_HOST=tcp://docker-socket-proxy:2375 \
  -v portainer_data:/data \
  portainer/portainer-ce:2.27.5
```

### Portainer first-run with socket-proxy — the manual bit

Because `DOCKER_HOST=tcp://docker-socket-proxy:2375` is now passed as an env var, Portainer will attempt to use the proxy automatically. However, it still won't auto-create a "local" environment from it at first login — you need to confirm the connection in the UI:

1. Open `https://127.0.0.1:9443` over the SSH tunnel mentioned above.
2. Create the admin user when prompted (long password, store in your password manager).
3. On the "Quick Setup" screen, choose **Get Started** → it will show "no environments." That's expected.
4. Go to the left sidebar → **Environments** → **+ Add environment**.
5. Select **Docker Standalone** → **Start Wizard** → **API**.
6. **Environment URL:** `tcp://docker-socket-proxy:2375` (this is the container DNS name on `proxy-net`, and matches the `DOCKER_HOST` env var already set).
7. Leave TLS off. Click **Connect**.
8. The new environment appears in the Environments list. Click into it — you should see your existing containers (`portainer`, `docker-socket-proxy`).

> ℹ️ With `EXEC=0` on the socket-proxy, Portainer's "Console" tab on each container is disabled (you'll see an error if you click it). This is intentional — it's the main mitigation. To shell into a container in an emergency, SSH to the host and `docker exec -it <name> sh` directly.

> All Docker images in this guide are pinned to a specific tag. Update them deliberately via Watchtower or manual `docker compose pull`. **Do not** use `:latest` — silent breaking changes will destroy your homelab on a random Tuesday.

### Deploying services via Portainer Stacks

Everything from §6 onward (Pi-hole, Step-CA, NPM, Home Assistant, Uptime Kuma, Watchtower) is deployed as a **Portainer Stack** instead of raw `docker compose` CLI commands. Portainer stores the stack definition, manages the containers, and gives you one-click redeploy, live logs, and restart from the UI.

**What cannot be a Portainer stack** (these stay as systemd services or bare `docker run`):
- Portainer itself — chicken-and-egg, must exist before stacks can be created
- `docker-socket-proxy` — same chicken-and-egg: Portainer's `DOCKER_HOST` points at it, so it must exist before Portainer can connect; deployed as a `docker run` above (FIX #99)
- WireGuard `wg0` — requires host network config and `wg-quick` systemd integration
- ProtonVPN — same as above
- Restic backups — a systemd timer, not a container

**How to create a stack in Portainer:**

1. Open Portainer → **Stacks** → **+ Add stack**
2. Give it the name shown in each section (e.g. `dns`, `step-ca`, `npm`)
3. Select **Web editor** and paste the YAML shown below
4. Set any environment variables in the **Environment variables** panel if noted
5. Click **Deploy the stack**

The YAML is also written to `/opt/<name>/docker-compose.yml` on disk for git tracking and Restic backups. Portainer and the on-disk file are independent — if you edit one, sync the other.

```bash
# Create the /opt directory structure once, for backups and git.
# FIX #88: include `portainer` so /opt/portainer exists on disk — the §15
# directory tree lists it (with a "no compose file — bootstrapped via docker
# run" note), but earlier versions of this mkdir didn't actually create it.
sudo mkdir -p /opt/{dns,step-ca,npm,homeassistant,kuma,watchtower,portainer}
```

**To update a stack** (e.g. bump an image tag): Portainer → Stacks → select the stack → **Editor** tab → change the tag → **Update the stack**. Portainer pulls the new image and recreates only the affected containers.

---

## 4. ProtonVPN via WireGuard

### Install tools

```bash
sudo apt install -y wireguard wireguard-tools
```

### Get config from Proton

1. https://account.proton.me/vpn → Downloads → WireGuard configuration
2. Pick a server, generate config, download `.conf`
3. Copy to `/etc/wireguard/protonvpn.conf` and `chmod 600`

### Replace the file with this corrected version

```bash
sudo nano /etc/wireguard/protonvpn.conf
```

```ini
[Interface]
PrivateKey = <your-proton-private-key>
Address = 10.2.0.2/32
# 1320 is ProtonVPN's own MTU ceiling — their servers reject larger packets.
# wg0 is set to 1280 because wg0 encapsulation adds ~60 B overhead on top of
# this tunnel. Strict no-fragmentation through Proton would require wg0
# ≤ 1320 - 60 = 1260, but 1280 is the IPv6 minimum MTU — drop below it and
# IPv6 stops working on the wg0 interface. We pick 1280 as a deliberate
# trade-off: packets larger than ~1260 inner bytes incur some PMTU-discovery
# overhead on the stacked path, but IPv6 keeps working. In practice the
# overhead is small; the §15 probe quantifies it.
# If your ISP's path MTU is below 1320 (rare but possible on PPPoE links),
# lower this value to match; the §15 MTU probe is the right diagnostic tool.
# 1280 remains the absolute floor for retaining IPv6 on wg0.
MTU = 1320

# All PostUp/PreDown logic lives in external scripts — wg-quick inline PostUp
# has unreliable shell-escaping on Ubuntu 24.04 (iptables 1.8.10, nf_tables).
PostUp  = /etc/wireguard/protonvpn-up.sh %i
PreDown = /etc/wireguard/protonvpn-down.sh %i

[Peer]
PublicKey = <proton-public-key>
Endpoint  = <proton-server>:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

Create the two scripts (make them executable with `sudo chmod +x` after saving):

**`/etc/wireguard/protonvpn-up.sh`**
```bash
#!/bin/bash
set -e
IFACE=$1

# Routing exceptions — LAN and wg0 bypass the VPN tunnel
ip rule del priority 50 2>/dev/null || true
ip rule del priority 51 2>/dev/null || true
ip rule add to 192.168.68.0/22 lookup main priority 50
ip rule add to 10.10.0.0/24    lookup main priority 51

# NAT for wg0 clients going out through Proton
iptables -t nat -A POSTROUTING -s 10.10.0.0/24 -o "$IFACE" -j MASQUERADE

# IPv4 kill switch (named chain — iptables 1.8.10 rejects multiple -d flags)
iptables -N PROTON_KS 2>/dev/null || iptables -F PROTON_KS
iptables -A PROTON_KS -o "$IFACE" -j RETURN
iptables -A PROTON_KS -d 192.168.68.0/22 -j RETURN
iptables -A PROTON_KS -d 10.10.0.0/24 -j RETURN
iptables -A PROTON_KS -m mark --mark "$(wg show "$IFACE" fwmark)" -j RETURN
iptables -A PROTON_KS -m addrtype --dst-type LOCAL -j RETURN
# NTP exception — clock sync must work even when Proton is down or the Pi
# can't validate any TLS cert (Step-CA leafs included) on next boot.
# chrony.conf in §2 prefers the LAN router (already in the bypass), but the
# public pool is the backup, and we let UDP/123 to public NTP through here.
iptables -A PROTON_KS -p udp --dport 123 -j RETURN
# FIX #103: exempt Docker bridge subnets. Without this, host->container traffic
# over Docker bridges is REJECT'd: the host's own DNS queries (resolv.conf
# 127.0.0.1:53 -> docker-proxy -> Pi-hole container at 172.30.0.x), curl to
# 127.0.0.1:9443 (Portainer) or 127.0.0.1:3001 (Kuma, from the health-push
# script), etc. all have a *container* IP as their destination. A container IP
# is not a LOCAL address, so the ADDRTYPE LOCAL RETURN above does not match it,
# and it is not in the LAN/wg0 ranges -- so it falls through to the REJECT
# below. Same class as fix #58, which added -s 127.0.0.0/8 to DOCKER-USER for
# the host-loopback *source* direction; this is the host->container
# *destination* direction. 172.16.0.0/12 covers docker0 (172.17.x), the
# auto-allocation pool (172.20.0.0/14 per daemon.json), and the manually-pinned
# dns-net (172.30.0.0/24) and proxy-net (172.31.0.0/24).
iptables -A PROTON_KS -d 172.16.0.0/12 -j RETURN
iptables -A PROTON_KS -j REJECT
iptables -I OUTPUT -j PROTON_KS

# IPv6 kill switch
# FIX #2: added -o wg0 and fd00:10:10::/64 exemptions. Without them the Pi
# host cannot reach wg0 peers over IPv6 while Proton is running, because wg0
# traffic leaves on the wg0 interface (not protonvpn), so the -o "$IFACE"
# RETURN doesn't match it and the final REJECT drops it.
ip6tables -N PROTON_KS 2>/dev/null || ip6tables -F PROTON_KS
ip6tables -A PROTON_KS -o "$IFACE" -j RETURN
ip6tables -A PROTON_KS -o wg0 -j RETURN
ip6tables -A PROTON_KS -d fd00:10:10::/64 -j RETURN
ip6tables -A PROTON_KS -m mark --mark "$(wg show "$IFACE" fwmark)" -j RETURN
ip6tables -A PROTON_KS -m addrtype --dst-type LOCAL -j RETURN
ip6tables -A PROTON_KS -p udp --dport 123 -j RETURN
ip6tables -A PROTON_KS -j REJECT
ip6tables -I OUTPUT -j PROTON_KS
```

**`/etc/wireguard/protonvpn-down.sh`**
```bash
#!/bin/bash
IFACE=$1

ip rule del priority 50 2>/dev/null || true
ip rule del priority 51 2>/dev/null || true

iptables -t nat -D POSTROUTING -s 10.10.0.0/24 -o "$IFACE" -j MASQUERADE 2>/dev/null || true
iptables -D OUTPUT -j PROTON_KS 2>/dev/null || true
iptables -F PROTON_KS 2>/dev/null || true
iptables -X PROTON_KS 2>/dev/null || true

ip6tables -D OUTPUT -j PROTON_KS 2>/dev/null || true
ip6tables -F PROTON_KS 2>/dev/null || true
ip6tables -X PROTON_KS 2>/dev/null || true
```

```bash
sudo chmod +x /etc/wireguard/protonvpn-up.sh /etc/wireguard/protonvpn-down.sh
```

### What this does (so you can debug it later)

- `wg-quick` with `AllowedIPs=0.0.0.0/0` automatically sets `fwmark` and adds a rule like `not from all fwmark 0xca6c lookup 51820` at priority 32766. Default route in table 51820 = the tunnel.
- Our priority 50/51 rules run **before** that and exempt LAN + wg0 destinations, sending those to the main routing table (direct).
- Result: **the Pi itself and its Docker containers** route public internet through Proton; the Pi's LAN-bound traffic stays direct; **wg0 clients' internet** also goes through Proton (full-tunnel remote = Pi-hole + Proton on the road).
- LAN clients (your phone on home WiFi, laptops, TV, etc.) never hit any of this — their gateway is still the router, so their traffic goes straight to the ISP.
- Kill switch uses a named chain (`PROTON_KS`) with individual RETURN exceptions, then REJECT at the bottom — required on Ubuntu 24.04's iptables 1.8.10 (nf_tables backend) which rejects multiple `! -d` flags on a single rule. Both IPv4 (`iptables`) and IPv6 (`ip6tables`) chains are set, so neither address family leaks on tunnel drop.
- The IPv6 chain also exempts `wg0` egress and the `fd00:10:10::/64` ULA prefix so the Pi can talk to its own VPN clients over IPv6 while Proton is running (fix #2).
- UDP/123 (NTP) is an explicit exception so chrony can keep the clock synced when Proton is down.

### Enable

```bash
sudo systemctl enable --now wg-quick@protonvpn
sudo wg show
```

### Verify

```bash
# Should be a Proton IP (not your home WAN IP)
curl --interface protonvpn ifconfig.me

# From the Pi itself (also via Proton)
curl ifconfig.me
```

---

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
# Both IPv4 and IPv6 DNS entries are required. With AllowedIPs = ::/0 all
# IPv6 traffic routes through the tunnel; IPv6-first OSes (iOS, Android,
# macOS) will attempt DNS over IPv6 and will bypass Pi-hole — leaking to
# the carrier resolver — if only the IPv4 address is listed here.
DNS = 10.10.0.1, fd00:10:10::1             # Pi-hole (IPv4 + IPv6)
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
      FTLCONF_webserver_port: "8080"        # admin UI on 8080; HTTP only (no TLS — NPM terminates it)
      FTLCONF_webserver_tls_port: "-1"     # disable HTTPS on the Pi-hole container; NPM handles TLS
    volumes:
      - pihole-data:/etc/pihole
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      # Admin UI bound to loopback only; reach via NPM at pihole.berrypi5.lan
      - "127.0.0.1:8080:8080/tcp"
    networks:
      dns-net:
      proxy-net:
    depends_on:
      - unbound

networks:
  dns-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/24
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

### Add local DNS records (so `*.berrypi5.lan` resolves)

Pi-hole's admin port is bound to `127.0.0.1` only — `http://192.168.70.5:8080/admin` is not reachable from the LAN. NPM doesn't exist yet at this point in the guide, so access via SSH tunnel:

```bash
ssh -L 8080:127.0.0.1:8080 pi@192.168.70.5
# then open http://127.0.0.1:8080/admin on your laptop
```

In the Pi-hole admin → **Local DNS → DNS Records**, add:

| Domain | IP |
|---|---|
| `ha.berrypi5.lan` | `192.168.70.5` |
| `portainer.berrypi5.lan` | `192.168.70.5` |
| `pihole.berrypi5.lan` | `192.168.70.5` |
| `npm.berrypi5.lan` | `192.168.70.5` |
| `stepca.berrypi5.lan` | `192.168.70.5` |
| `kuma.berrypi5.lan` | `192.168.70.5` |

### Router DNS — primary AND secondary

In your router's DHCP settings:
- Primary DNS: `192.168.70.5`
- Secondary DNS: `1.1.1.1` (or another public resolver)

The secondary is intentional. If you only set primary and the Pi reboots, your house has no internet for 5 minutes. Yes, secondary will sometimes bypass Pi-hole during outages — that's the trade-off. If you want belt-and-braces, run a second Pi-hole on a Pi Zero 2 W and use it as secondary.

### Verify

```bash
nslookup google.com 192.168.70.5
nslookup ha.berrypi5.lan 192.168.70.5    # should return 192.168.70.5
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
      # Bound to loopback — reach via NPM at stepca.berrypi5.lan, or via
      # SSH tunnel during initial bootstrap before NPM exists.
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
      # NPM's ACME client connects to https://step-ca:9000 via Docker DNS on
      # proxy-net. The TLS certificate Step-CA presents must include "step-ca"
      # as a SAN, or the client rejects it with x509: certificate is valid for
      # [other names] not step-ca — even though the root CA is trusted.
      # FIX #43: added "localhost" and "127.0.0.1" — the guide directs bootstrap
      # access via `https://127.0.0.1:9000` over SSH tunnel, but without these
      # entries the TLS cert lacks the required IP SAN and clients get:
      #   x509: certificate is valid for [other IPs], not 127.0.0.1
      DOCKER_STEPCA_INIT_DNS_NAMES: "step-ca,localhost,127.0.0.1,berrypi5,192.168.70.5,stepca.berrypi5.lan"
      DOCKER_STEPCA_INIT_PROVISIONER_NAME: "admin@berrypi5"
      DOCKER_STEPCA_INIT_ACME: "true"
    networks:
      - proxy-net

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
# Save to /opt/step-ca/ specifically — NPM (§8) mounts this exact path read-only
# into its container so its ACME client can validate Step-CA's TLS cert.
docker exec step-ca cat /home/step/certs/root_ca.crt | sudo tee /opt/step-ca/homelab-root-ca.crt
cp /opt/step-ca/homelab-root-ca.crt ~/homelab-root-ca.crt    # for installing on devices
docker logs step-ca 2>&1 | grep -i acme
```

The ACME URL looks like `https://step-ca:9000/acme/acme/directory` (reachable from NPM via the shared `proxy-net` Docker DNS). Save it for NPM. For a host-reachable URL during bootstrap, use `https://127.0.0.1:9000/acme/acme/directory` over the SSH tunnel.

Install `homelab-root-ca.crt` on every device — see the trust-store table at the bottom.

---

## 8. Nginx Proxy Manager

**Stack name in Portainer:** `npm`

```bash
sudo nano /opt/npm/docker-compose.yml
```

```yaml
services:
  npm:
    image: jc21/nginx-proxy-manager:2.12.3
    container_name: npm
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      # Admin UI bound to loopback — reach via NPM's own proxy host at
      # npm.berrypi5.lan, or via SSH tunnel during initial setup.
      - "127.0.0.1:81:81"
    volumes:
      - npm-data:/data
      - npm-ssl:/etc/letsencrypt
      # Trust the Step-CA root so NPM's ACME client can validate Step-CA's
      # TLS cert when registering. Without this, ACME registration fails
      # with x509: signed by unknown authority. Path on host populated in §7.
      - /opt/step-ca/homelab-root-ca.crt:/usr/local/share/ca-certificates/homelab-root-ca.crt:ro
    environment:
      DISABLE_IPV6: "true"
    # FIX #3: run update-ca-certificates on every container start, not once
    # manually. The one-off `docker exec npm update-ca-certificates` approach
    # only writes into the container's writable layer, which is discarded on
    # every image update, stack redeploy, or host reboot where the container
    # is recreated. After any such event the cert is mounted but not in the
    # trust bundle, silently breaking ACME until someone remembers to re-run
    # the command. The entrypoint override rebuilds the bundle from the
    # volume-mounted cert on every start, making it idempotent.
    # FIX #104: the `exec` before `/init` is MANDATORY, not cosmetic. Without
    # it, `/bin/sh` stays as PID 1 and `/init` runs as its child; NPM's
    # s6-overlay base image hard-checks `getpid() == 1` in s6-overlay-suexec
    # and aborts with `fatal: can only run as pid 1`, crash-looping the
    # container forever. `exec` replaces the shell process so `/init` inherits
    # PID 1. (jc21/nginx-proxy-manager:2.12.3 ships s6-overlay v3.x, which
    # enforces this strictly; older s6 versions were more lenient, which is why
    # fix #3's original `&& /init` appeared to work on earlier image tags.)
    entrypoint: ["/bin/sh", "-c", "update-ca-certificates && exec /init"]
    networks:
      - proxy-net

networks:
  proxy-net:
    external: true

volumes:
  npm-data:
  npm-ssl:
```

```bash
# Portainer → Stacks → + Add stack → name: npm → Web editor → paste YAML → Deploy
# CLI fallback:
cd /opt/npm && docker compose up -d
```

Access `http://127.0.0.1:8081` via SSH tunnel: `ssh -L 8081:127.0.0.1:81 pi@192.168.70.5`. (The local listen-port is `8081`, not `81` — port 81 is privileged and `ssh -L` can't bind it on the client side without root. The Pi-side target stays `81`, where NPM's admin UI listens. Same pattern §6 uses for the Pi-hole tunnel.) Default login `admin@example.com` / `changeme` — change immediately.

### Add proxy hosts

Now that everything is on the shared `proxy-net` Docker bridge, the forwards reference container names instead of `192.168.70.5:<port>`. NPM resolves them via Docker's internal DNS.

| Domain | Forward | SSL |
|---|---|---|
| `ha.berrypi5.lan` | `192.168.70.5:8123` (HA is on host network) | Step-CA |
| `portainer.berrypi5.lan` | `portainer:9443` (HTTPS) | Step-CA |
| `pihole.berrypi5.lan` | `pihole:8080` | Step-CA |
| `npm.berrypi5.lan` | `npm:81` | Step-CA |
| `stepca.berrypi5.lan` | `step-ca:9000` (HTTPS) | Step-CA |
| `kuma.berrypi5.lan` | `uptime-kuma:3001` | Step-CA |

> ⚠️ **Portainer backend is HTTPS with a self-signed cert.** In the NPM proxy host for `portainer.berrypi5.lan`, set the scheme to **HTTPS** and enable **"Ignore Certificate"** in the Advanced tab. Without this NPM will refuse to proxy to Portainer's self-signed cert and return a 502. Alternatively, configure Portainer to use a Step-CA certificate so the chain is trusted end-to-end.

> ⚠️ **Step-CA backend is also HTTPS with a self-signed cert.** Apply the same treatment to `stepca.berrypi5.lan`: scheme **HTTPS**, **"Ignore Certificate"** enabled. Step-CA's own TLS cert is signed by the homelab root CA, which NPM trusts (via the volume mount + entrypoint), but the CN/SAN on the cert is `step-ca` — NPM proxying to `step-ca:9000` will validate the hostname against the cert. If you see a 502 for `stepca.berrypi5.lan`, enable "Ignore Certificate" as the quick fix, or confirm `step-ca` is listed in `DOCKER_STEPCA_INIT_DNS_NAMES` (it is, per fix #1).

For SSL, register an ACME provider in NPM pointing at the Step-CA directory URL captured above.

---

## 9. LAN Gateway — keep the router, not the Pi

Your chosen design: **only the Pi and its Docker containers go through ProtonVPN.** Other LAN devices (phone on WiFi, laptop, TV, etc.) use the home router as their gateway and reach the internet normally — no ProtonVPN, no Pi-hole-only-DNS bottleneck.

### What this means in practice

- **DHCP gateway stays as the router** (`192.168.68.1`). Don't change it.
- **DHCP DNS stays as the Pi** (`192.168.70.5`) with `1.1.1.1` secondary. LAN clients still get ad blocking — only their internet path bypasses Proton.
- The Pi's own outbound and Docker container outbound (Pi-hole's recursive lookups via Unbound, NPM, HA telemetry, container image pulls, etc.) all flow through Proton.
- wg0 clients (your phone/laptop when remote) get full-tunnel: their internet flows phone → Pi → Proton.
- **If the Pi goes down, your house keeps internet.** Only DNS via Pi-hole stops, and clients fail over to the secondary DNS (`1.1.1.1`).

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

## 11. Dynamic DNS (DDNS)

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

## 12. Backups with Restic

The thing v1 was missing entirely. Without backups, an SD-card death (or a finger-fumbled `docker volume rm`) is a full rebuild.

### Install

```bash
sudo apt install -y restic
```

```bash
# FIX #94: pre-pull the alpine image the backup script uses for tar'ing Docker
# volumes. Without this, the very first scheduled 04:00 backup is what pulls
# alpine:3.21 — and if ProtonVPN happens to be down at 04:00 (the kill switch
# blocks all egress), the pull fails, set -euo pipefail aborts the script,
# and the OnFailure unit fires a Telegram alert before any backup has ever
# succeeded. Pulling now (with the tunnel up during setup) caches the image
# locally; Watchtower's WATCHTOWER_CLEANUP only prunes images that have been
# *updated*, and we pin to alpine:3.21, so the cached layer survives.
sudo docker pull alpine:3.21
```

### Set up a Backblaze B2 bucket with split keys + Object Lock

Sign up at backblaze.com → create a bucket. Cheap (~$0.005/GB/month).

**Critical: split your B2 application keys into two, and enable Object Lock.** With v3's single full-permission key sitting in `/root/.restic-env`, a root compromise on the Pi means an attacker can wipe every backup before encrypting your data. Belt-and-braces:

1. **Enable Object Lock on the bucket** (Backblaze web UI → bucket settings → File Lock → Enable, Governance mode, retention e.g. 14 days). Backblaze will refuse to delete files younger than the lock period regardless of API key permissions.
2. **Create two B2 application keys:**
   - **`berrypi5-backup-write`** — bucket: this bucket only; capabilities: `listBuckets`, `listFiles`, `readFiles`, `writeFiles`. **No** `deleteFiles`. This key lives on the Pi.
   - **`berrypi5-backup-admin`** — full capabilities including `deleteFiles`. **Do not store on the Pi.** Keep it in your password manager. Used manually from a different machine for `restic forget --prune`.

This means the daily backup on the Pi can write new snapshots but cannot remove old ones. Even if root is compromised, your historical backups survive the Object Lock period.

### Init the repo

> ⚠️ **Use the admin key for `restic init`, then swap to the write-only key.** The write-only key (`berrypi5-backup-write`) is what goes in `/root/.restic-env` for daily backups, but the *repo must be initialised* before that key is written to disk. The easiest approach is to run `restic init` from your workstation using the admin key, so the deletion-capable key never touches the Pi at all. If you prefer to do it on the Pi, temporarily substitute the admin key ID and application key in the block below, run `restic init`, then immediately overwrite the file with the write-only key as shown.

```bash
# Write the daily write-only key — used for all normal backup runs
cat <<EOF | sudo tee /root/.restic-env
export RESTIC_REPOSITORY="b2:berrypi5-backup"
export RESTIC_PASSWORD="<long-strong-password-saved-in-bitwarden>"
export B2_ACCOUNT_ID="<keyID-of-berrypi5-backup-write>"
export B2_ACCOUNT_KEY="<applicationKey-of-berrypi5-backup-write>"
EOF
sudo chmod 600 /root/.restic-env
```

Init the repo from your **workstation** using the admin key (preferred — keeps the delete-capable key off the Pi):

```bash
export RESTIC_REPOSITORY="b2:berrypi5-backup"
export RESTIC_PASSWORD="<long-strong-password-saved-in-bitwarden>"
export B2_ACCOUNT_ID="<keyID-of-berrypi5-backup-admin>"
export B2_ACCOUNT_KEY="<applicationKey-of-berrypi5-backup-admin>"
restic init
```

Or, if you prefer to init on the Pi, temporarily use the admin key:

```bash
# On the Pi — substitute admin key just for init, then the file already
# has the write-only key from the block above, so no further change needed
sudo B2_ACCOUNT_ID="<keyID-of-berrypi5-backup-admin>" \
     B2_ACCOUNT_KEY="<applicationKey-of-berrypi5-backup-admin>" \
     restic --no-cache -r "b2:berrypi5-backup" init
```

### Backup script

```bash
sudo nano /usr/local/bin/homelab-backup.sh
```

```bash
#!/bin/bash
set -euo pipefail
source /root/.restic-env

# Quiesce ALL containers with non-trivial on-disk state before tarring their volumes:
#   pihole         — SQLite query DB, active writes
#   homeassistant  — SQLite recorder DB
#   npm            — SQLite + Let's Encrypt accounts.json
#   portainer      — BoltDB; live tar produces inconsistent snapshots
#   uptime-kuma    — SQLite heartbeat history; live tar drops most recent writes
#   mosquitto      — active broker writing to mosquitto-data; include if deployed
#                    (docker stop is a no-op for containers that aren't running,
#                    so it's safe to list it unconditionally)
# Watchtower, step-ca, unbound, docker-socket-proxy: stateless or write-rarely;
# tarring live is fine. Step-CA's signing key is in a quiesced JSON file, not a DB.
STOP_LIST="pihole homeassistant npm portainer uptime-kuma mosquitto"

# FIX #4: trap ensures containers are always restarted, even if the script
# exits early due to set -e firing (e.g. restic error, full disk, Docker blip).
# Without this, a mid-backup failure leaves Pi-hole, HA, NPM, Portainer, Kuma,
# and Mosquitto stopped with no automatic recovery.
# STAGING is also cleaned up here — without this, a mid-run failure leaves
# potentially several GB of volume tarballs in /tmp/ until the next reboot,
# which can fill the SSD. The rm uses the variable directly (not a subshell)
# so it's always defined by the time the trap fires.
# FIX #46: renamed from TMPDIR to STAGING. TMPDIR is the POSIX standard env var
# that programs (including restic) consult when creating their own scratch files.
# With the old name, restic wrote pack-assembly scratch into the staging dir and
# those files were then included in the restic backup, inflating every snapshot.
STAGING=$(mktemp -d)
# Double-quoted trap: $STOP_LIST and $STAGING are expanded NOW (at definition time),
# not at fire time. This is safe under set -u because both variables are already
# set above. A single-quoted trap would defer expansion to exit time, where a very
# early failure could leave $STOP_LIST unset and trip the -u guard.
trap "docker start $STOP_LIST 2>/dev/null || true; rm -rf \"$STAGING\"" EXIT

docker stop $STOP_LIST 2>/dev/null || true

# Back up Docker volumes via tarballs to a temp dir
# mapfile avoids word-splitting on volume names with spaces or special chars
mapfile -t VOLUMES < <(docker volume ls -q)
for vol in "${VOLUMES[@]}"; do
    docker run --rm -v "$vol":/src -v "$STAGING":/dst alpine:3.21 \
      tar czf "/dst/${vol}.tar.gz" -C /src .
done

# Restic snapshot (write-only B2 key — cannot delete, see §12 init notes)
# Covers: WireGuard keys+scripts, network config, SSH hardening, NTP config,
# compose files + scripts in /opt, Docker volume tarballs, and the systemd/cron
# units that aren't in /opt. Git tracks the same files without secrets; restic
# is the authoritative restore source because it captures the live state.
restic backup \
  /etc/wireguard \
  /etc/netplan \
  /etc/ssh \
  /etc/chrony \
  /etc/sysctl.d \
  /etc/cron.d \
  /etc/cloud/cloud.cfg.d \
  /etc/apt/apt.conf.d/50unattended-upgrades \
  /etc/systemd/system/homelab-backup.service \
  /etc/systemd/system/homelab-backup.service.d/notify.conf \
  /etc/systemd/system/homelab-backup.timer \
  /etc/systemd/system/homelab-backup-notify@.service \
  /etc/systemd/system/docker-user-rules.service \
  /usr/local/bin/homelab-backup.sh \
  /usr/local/bin/homelab-health-push.sh \
  /usr/local/bin/docker-user-rules.sh \
  /opt \
  "$STAGING" \
  --tag homelab \
  --exclude='*.log'

# NOTE: 'restic forget --prune' is NOT run here. The daily B2 key has no
# deleteFiles capability — prune would fail anyway. Pruning runs weekly
# from a different machine (or manually) using the admin key. See below.
# The trap at the top handles docker start on both success and failure paths.
```

```bash
sudo chmod 700 /usr/local/bin/homelab-backup.sh
```

### Schedule daily at 04:00

```bash
sudo nano /etc/systemd/system/homelab-backup.service
```

```
[Unit]
Description=Homelab Restic backup
After=docker.service
# Requires= (not just After=) prevents the backup from running if Docker is
# stopped. Without it, docker volume ls returns nothing, the volume-tarball
# loop produces no files, and restic backs up /opt + config only — a silent
# partial backup with a successful exit code and no notification.
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/homelab-backup.sh

[Install]
# This service is invoked by homelab-backup.timer, not enabled directly.
# The [Install] section is here so `systemctl enable homelab-backup.service`
# doesn't fail with "Unit file has no [Install] section" if someone tries it
# while troubleshooting. The timer is the correct activation path.
WantedBy=multi-user.target
```

```bash
sudo nano /etc/systemd/system/homelab-backup.timer
```

```
[Unit]
Description=Daily homelab backup

[Timer]
OnCalendar=*-*-* 04:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now homelab-backup.timer
sudo systemctl list-timers homelab-backup.timer
```

### Backup failure notifications

Without this, a failed backup is silent until you manually check `systemctl status homelab-backup`. Add an `OnFailure` drop-in that fires the same Telegram channel used by Watchtower:

```bash
sudo mkdir -p /etc/systemd/system/homelab-backup.service.d
sudo nano /etc/systemd/system/homelab-backup.service.d/notify.conf
```

```
[Unit]
OnFailure=homelab-backup-notify@%p.service
```

```bash
sudo nano /etc/systemd/system/homelab-backup-notify@.service
```

```
[Unit]
Description=Notify on backup failure
# Telegram requires network connectivity. Without this, a very early boot
# failure (before the network stack is up) causes the curl to fail silently
# and no notification is sent.
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -s --max-time 10 \
  "https://api.telegram.org/bot<token>/sendMessage" \
  -d chat_id=<chat-id> \
  -d text="⚠️ homelab-backup FAILED on berrypi5 — check: journalctl -u homelab-backup"
```

```bash
sudo systemctl daemon-reload
```

### Weekly `forget` and `prune` (manual, from a different machine)

Once a week, from your workstation (not the Pi), using the **admin** B2 key:

```bash
export RESTIC_REPOSITORY="b2:berrypi5-backup"
export RESTIC_PASSWORD="<long-strong-password>"
export B2_ACCOUNT_ID="<keyID-of-berrypi5-backup-admin>"
export B2_ACCOUNT_KEY="<applicationKey-of-berrypi5-backup-admin>"

restic forget --prune \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6
```

Doing this off-Pi has two benefits: (1) the deletion-capable key never touches the machine it's protecting, and (2) `prune` is expensive — it can rewrite a meaningful chunk of the repo on each run, which costs B2 transactions and Pi CPU. Run it from your laptop or a tiny VPS instead. Set a calendar reminder. Object Lock means files within the retention period can't actually be deleted regardless, so missing a week is harmless.

### Restore drill (do this once now, not when you actually need it)

```bash
sudo bash -c '
source /root/.restic-env
restic snapshots
restic restore latest --target /tmp/restore-test --include /etc/wireguard
restic restore latest --target /tmp/restore-test --include /etc/netplan
restic restore latest --target /tmp/restore-test --include /etc/chrony
restic restore latest --target /tmp/restore-test --include /etc/sysctl.d
restic restore latest --target /tmp/restore-test --include /etc/cloud/cloud.cfg.d
restic restore latest --target /tmp/restore-test --include /etc/ssh
restic restore latest --target /tmp/restore-test --include /etc/apt/apt.conf.d/50unattended-upgrades
# Verify all six paths inside the same privileged shell — avoids false
# confidence if a restore failed early and left the target dir empty or
# partial. Running ls outside the sudo bash -c block would succeed even on
# an incomplete restore because /tmp is world-readable.
ls /tmp/restore-test/etc/wireguard/
ls /tmp/restore-test/etc/netplan/
ls /tmp/restore-test/etc/chrony/
ls /tmp/restore-test/etc/sysctl.d/
ls /tmp/restore-test/etc/cloud/cloud.cfg.d/
ls /tmp/restore-test/etc/ssh/
ls /tmp/restore-test/etc/apt/apt.conf.d/
'
```

The drill confirms the seven config paths most critical to a working network and host (VPN keys, static IP, NTP, kernel tunables, cloud-init network disable, SSH hardening, and the unattended-upgrades reboot-window config) are present in the snapshot. Clean up after: `sudo rm -rf /tmp/restore-test`.

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
      # Bound to loopback — reach via NPM at kuma.berrypi5.lan
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
      - proxy-net

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

Open `https://kuma.berrypi5.lan` and add monitors for:
- `https://ha.berrypi5.lan` (HTTPS)
- `https://portainer.berrypi5.lan` (HTTPS)
- `https://pihole.berrypi5.lan` (HTTPS)
- `1.1.1.1` (ping — checks Proton tunnel is alive end-to-end)
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

# FIX #49: use the direct loopback URL instead of the NPM/DNS chain. The health
# script must keep pushing even when Pi-hole DNS or NPM itself is down (or during
# a backup run when NPM is quiesced). The loopback address bypasses both, hitting
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
      - proxy-net

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
sudo systemctl list-timers homelab-backup.timer
```

Containers expected up: `pihole`, `unbound`, `step-ca`, `npm`, `portainer`, `docker-socket-proxy`, `homeassistant`, `uptime-kuma`, `watchtower`. (No DDNS container — TP-Link router handles it.)

**Verify all stacks are healthy in Portainer:** Portainer → **Stacks** — each stack should show **Active** in green. Any stack showing **Unhealthy** or **Inactive** → click in → **Logs** tab to diagnose.

| Stack name | Containers | Portainer status |
|---|---|---|
| `dns` | `pihole`, `unbound` | Active |
| `step-ca` | `step-ca` | Active |
| `npm` | `npm` | Active |
| `homeassistant` | `homeassistant` | Active |
| `kuma` | `uptime-kuma` | Active |
| `watchtower` | `watchtower` | Active |

Plus the two containers that aren't stacks: `portainer` itself and `docker-socket-proxy`. Check both with `docker ps`.

### Router config

| Setting | Value |
|---|---|
| DHCP range | `192.168.68.50 – 192.168.69.250` |
| DHCP gateway | `192.168.68.1` (router itself — LAN clients bypass Proton) |
| DHCP DNS primary | `192.168.70.5` (Pi-hole) |
| DHCP DNS secondary | `1.1.1.1` (fallback if Pi-hole down) |
| Port forward 51820/UDP | → `192.168.70.5:51820` (WireGuard) |
| Port forward 80/TCP | → `192.168.70.5:80` (NPM, optional if you want public access — see note below) |
| Port forward 443/TCP | → `192.168.70.5:443` (NPM, optional — see note below) |

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
nslookup ha.berrypi5.lan               # 192.168.70.5 (Pi-hole answered)
curl https://ha.berrypi5.lan           # HA login page — NO -k; this validates the root CA is trusted
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
open https://ha.berrypi5.lan           # HA loads
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

Admin ports are now bound to `127.0.0.1` on the Pi — they aren't reachable from the LAN directly. Use NPM via `*.berrypi5.lan` for normal use, or SSH tunneling for bootstrap and debugging:

```bash
# example: reach Portainer directly via SSH tunnel
ssh -L 9443:127.0.0.1:9443 pi@192.168.70.5
# then open https://127.0.0.1:9443 on your laptop
```

| Service | Direct (on Pi only, via SSH tunnel) | Via NPM (any LAN/VPN client) |
|---|---|---|
| Home Assistant | `http://192.168.70.5:8123` (host network, LAN-reachable) | `https://ha.berrypi5.lan` |
| Portainer | `https://127.0.0.1:9443` | `https://portainer.berrypi5.lan` |
| Pi-hole | `http://127.0.0.1:8080/admin` | `https://pihole.berrypi5.lan` |
| NPM | `http://127.0.0.1:81` | `https://npm.berrypi5.lan` |
| Step-CA | `https://127.0.0.1:9000` | `https://stepca.berrypi5.lan` |
| Uptime Kuma | `http://127.0.0.1:3001` | `https://kuma.berrypi5.lan` |

> ℹ️ Home Assistant intentionally stays on `network_mode: host` (mDNS / HomeKit requirement). §2's UFW rules (fix #106) explicitly open port 8123 to the LAN and to the Docker bridge range, so `http://192.168.70.5:8123` is reachable from the whole LAN and `ha.berrypi5.lan` works through NPM. If you want to enforce NPM-only access to HA — i.e. block LAN devices from hitting `192.168.70.5:8123` directly while still letting NPM proxy it — you must **insert** a deny rule *before* the `allow from 192.168.68.0/22 ... 8123` rule, because UFW is first-match-wins and the allow was added first: `sudo ufw insert 1 deny from 192.168.68.0/22 to any port 8123`. NPM is unaffected — its traffic originates from the `172.31.x.x` Docker bridge (matched by the separate `from 172.16.0.0/12` allow), not from `192.168.68.0/22`. Re-check ordering afterwards with `sudo ufw status numbered`.

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
  ping -M do -s "$s" -c 1 -W 2 1.1.1.1 >/dev/null 2>&1 \
    && echo "$s OK" \
    || echo "$s FAIL"
done
```

The last `OK` size + 28 (ICMP+IP headers) is your true effective MTU. **Going below 1280 breaks IPv6 on the wg0 interface** — 1280 is the IPv6 minimum MTU (see fix #82 in §4). If the probe shows the path can't carry 1280-byte packets and you must lower wg0 further, you're making a deliberate trade-off: no IPv6 on wg0 in exchange for no fragmentation. Drop both server and client to e.g. 1240 only if you accept v4-only on wg0. Mismatched MTUs typically show up as "WireGuard connects but big requests hang" — HTTPS handshakes complete, but large responses stall.

### Image-pin review cadence

Pinning images protects against silent breakage but, left alone, silently rots into "running known-CVE versions on purpose." Add a recurring calendar entry — quarterly is reasonable — to:

1. Check the changelogs of each pinned image (Pi-hole, HA, NPM, Portainer, Step-CA, Kuma, Mosquitto, Watchtower, Unbound, docker-socket-proxy)
2. Bump pins one stack at a time via Portainer's Stack editor → Update
3. Watch logs for ≥24h before bumping the next
4. Commit the updated compose files to git

Pi-hole 5→6 was a one-way migration with a new env var schema. Step-CA, Portainer, and NPM occasionally have breaking config changes too. Reading release notes before bumping is the difference between a 5-minute update and a 2-hour rollback.

### gitleaks pre-commit

You're committing compose files, netplan, sysctl, SSH hardening, and a sanitised `wg0.conf` to a private repo. "Sanitised" by hand is exactly the kind of thing that goes wrong once. Add [gitleaks](https://github.com/gitleaks/gitleaks) as a pre-commit hook so a private key, B2 application key, or `WEBPASSWORD` left in by accident gets caught before it hits GitHub:

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
| Cert errors on `*.berrypi5.lan` | Root CA not installed on that device | See trust-store table |
| Slow VPN throughput / random disconnects | MTU too high through stacked tunnels | wg0 is already set to 1280 (fix #62, IPv6 minimum per fix #82); run the MTU probe in §15. Only lower wg0 + clients further if the stall persists **and** you accept losing IPv6 on the wg0 interface — 1240 is conservative but makes wg0 v4-only |
| Watchtower broke a service | Bad image tag picked up | `cd /opt/<service> && docker compose pull && docker compose up -d` with last-known-good tag |

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
├── npm/              # Nginx Proxy Manager
├── portainer/        # no compose file — Portainer + docker-socket-proxy bootstrapped via docker run (see §3)
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
├── homelab-backup.sh
├── homelab-health-push.sh
└── docker-user-rules.sh

/etc/cron.d/
└── homelab-health    # SoC + NVMe push to Kuma every minute

/etc/systemd/system/
├── homelab-backup.service
├── homelab-backup.service.d/
│   └── notify.conf
├── homelab-backup.timer
├── homelab-backup-notify@.service
└── docker-user-rules.service
```

### What to put in git

`/opt/*/docker-compose.yml`, `/etc/netplan/50-cloud-init.yaml`, `/etc/sysctl.d/99-homelab.conf`, `/etc/ssh/sshd_config.d/99-hardening.conf`, `/etc/chrony/chrony.conf`, `/etc/apt/apt.conf.d/50unattended-upgrades`, `/etc/wireguard/protonvpn-up.sh`, `/etc/wireguard/protonvpn-down.sh`, `/usr/local/bin/homelab-backup.sh`, `/usr/local/bin/homelab-health-push.sh`, `/usr/local/bin/docker-user-rules.sh`, `/etc/systemd/system/docker-user-rules.service`, `/etc/cron.d/homelab-health`, the rest of the systemd unit files, and a sanitised version of `wg0.conf` (keys redacted). Commit the lot to a private GitHub repo with `gitleaks` as a pre-commit hook. Restic handles the rest (data); git handles the recipe.

Keep the on-disk compose files in sync with what you paste into Portainer. The easiest habit: edit the file on disk first, then paste the updated content into the Portainer stack editor. That way git always has the source of truth.

---

**v5.1 bug-fix summary** — the 5 fixes applied to v5 plus 23 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 9 | §6 Pi-hole | `http://192.168.70.5:8080/admin` is unreachable before NPM exists — port 8080 is bound to `127.0.0.1` only | Replaced with SSH-tunnel instructions for pre-NPM access |
| 10 | §12 Backup | `trap` restarted containers but never cleaned up `$TMPDIR`; a mid-run `set -e` exit left GB-sized tarballs in `/tmp/`; also `TMPDIR` was created after the trap, so the variable could be unset when the trap fired | Moved `TMPDIR=$(mktemp -d)` before the trap; added `rm -rf "$TMPDIR"` to the trap body |
| 11 | §2 systemd-resolved | Heading said "no chattr" and intro said not to use `chattr +i`, but the body correctly used it — stale text from v1 that was never updated when v4 reversed the decision | Rewrote heading and intro paragraph to match the actual instructions |
| 12 | §12 restic init | Admin-key warning appeared *after* `restic init` was already invoked with the write-only key — users following top-to-bottom would hit the wrong credential order | Moved warning before the init steps; restructured into clearly separated write-only env block and admin-key init block |
| 13 | v4 changes summary | Watchtower `1.7.1` was pinned in the compose file (§13) but absent from the end-of-document image-pins table used for quarterly review | Added `Watchtower 1.7.1` to the pins table |
| 14 | Header | "Revision notes vs v5" was a self-reference — current doc IS v5; should read "vs v4.1" | Corrected to "vs v4.1" |
| 15 | §6 Pi-hole compose | `FTLCONF_webserver_port: "8080o"` — the `o` suffix is not a valid Pi-hole v6 port specifier and would likely break the web server | Corrected to `"8080"` with explicit `FTLCONF_webserver_tls_port: "-1"` to disable container HTTPS |
| 16 | §12 Backup script | Redundant `rm -rf "$TMPDIR"` on the success path after restic — EXIT trap already covers cleanup; also trap was single-quoted, deferring `$STOP_LIST` expansion to fire time, which is fragile under `set -u` | Removed redundant rm; switched trap to double-quoted expansion |
| 17 | §3 + §15 Portainer | `-e DOCKER_HOST=tcp://docker-socket-proxy:2375` was missing from both the initial `docker run` and the §15 update command — after any container recreate, Portainer would lose its socket-proxy connection | Added env var to both commands; updated first-run wizard note |
| 18 | §5 wg0.conf | Comment implied ip6tables FORWARD rules were optional (like the ip6tables MASQUERADE rule) — they are unconditional and always needed for the tunnel to carry IPv6 | Clarified comment; rules unchanged |
| 19 | §3 daemon.json | `proxy-net` (`172.31.0.0/24`) and `dns-net` (`172.30.0.0/24`) sit inside Docker's default auto-allocation pool (`172.16.0.0/12`); Docker could auto-assign a new network the same prefix, silently breaking routing | Added `default-address-pools` to `daemon.json` (base `172.17.0.0/16` — later corrected to `172.20.0.0/14` by fix #33) |
| 20 | §2 + §6 systemd-resolved | `chattr +i /etc/resolv.conf` was placed in the §2 early-setup code block, but running it there blocks netplan and cloud-init for the rest of initial setup — the inline comment even said "run after setup only" | Removed `chattr +i` from §2; added a new deferred "Pin resolv.conf" step at the end of §6 after Pi-hole is confirmed working |
| 21 | §10 Mosquitto | `mosquitto_passwd -c` creates and overwrites the password file — using it to add a second user silently deletes the first; no warning was present | Added explicit warning; showed the no-`-c` form for adding subsequent users |
| 22 | §3 Docker install | `newgrp docker` only applies the group to the current shell; other open terminals require a full logout/login before `docker` works without `sudo` | Added warning and recommended `exit` + re-SSH before continuing |
| 23 | §11 DDNS | Typo "fastback-up" instead of "fallback" | Fixed |
| 24 | §14 Functional tests | `curl -k https://ha.berrypi5.lan` suppresses TLS errors with `-k`, defeating the entire point of verifying the root CA is trusted on the client | Removed `-k`; added inline comment explaining the test is intentionally strict |
| 25 | §9 gateway table | Table labels jumped from "Option A" to "Option C" — Option B had been deleted in an earlier edit but the label on C was never updated | Renamed "Option C" to "Option B" |
| 26 | §15 Ubuntu gotchas | `chattr +i` cross-reference said "(see §2)" after the step was moved to §6 in fix #20 | Updated to "(see §6)" |
| 27 | §12 restore drill | `source /root/.restic-env` shown without `sudo` — the file is `chmod 600` root-only; running as `pi` gives "Permission denied" | Wrapped commands in `sudo bash -c '...'` |
| 28 | §15 troubleshooting table | `docker compose pull && up -d` — `up -d` is not a standalone command; would fail with "command not found" | Fixed to `docker compose pull && docker compose up -d` |
| 29 | §3 container startup order | `docker run portainer` appeared before `docker run docker-socket-proxy`; Portainer's `DOCKER_HOST` env var points at the proxy and tries to connect immediately — proxy must exist first | Swapped order: docker-socket-proxy first, then Portainer; added explanatory note |
| 30 | §13 health script | `TEMP_MC` had no guard against empty/unreadable sysfs output; an empty value caused `awk` arithmetic syntax error, silently crashing the script | Added empty-value check; script now pushes a "down" status with a clear message if sysfs is unreadable |
| 31 | §2 formatting | Two consecutive blank lines left after removing `chattr +i` from §2 in fix #20 | Removed extra blank line |

**v5.1.7.11 bug-fix summary** — 5 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 103 | §4 `protonvpn-up.sh` kill switch | `PROTON_KS` had no exemption for Docker bridge subnets; host→container traffic over the bridges (host DNS via docker-proxy→Pi-hole, `curl 127.0.0.1:9443`→Portainer, health-push→Kuma) carries a container IP as destination, which is not LOCAL and not in the LAN/wg0 ranges, so it falls through to the final `REJECT`. After §4, Portainer/Pi-hole admin and the Pi's own DNS all break | Added `iptables -A PROTON_KS -d 172.16.0.0/12 -j RETURN` before the `REJECT`, with a comment. Same class as fix #58 but for the host→container *destination* direction. `protonvpn-down.sh` needs no edit (it flushes the whole chain) |
| 104 | §8 NPM `entrypoint:` | `update-ca-certificates && /init` leaves `/bin/sh` as PID 1 and runs `/init` as its child; NPM's s6-overlay v3.x base image hard-checks `getpid() == 1` and aborts with `s6-overlay-suexec: fatal: can only run as pid 1`, crash-looping the container forever | Changed to `update-ca-certificates && exec /init` so `/init` replaces the shell and inherits PID 1; expanded the comment to document why `exec` is mandatory |
| 105 | §8 SSH tunnel example | `ssh -L 81:127.0.0.1:81` fails with `bind: Permission denied` — port 81 is privileged and the `-L` local listen-port can't be bound by a non-root user on macOS/Linux | Changed local listen-port to `8081` (`ssh -L 8081:127.0.0.1:81`); Pi-side target stays `81`; access URL updated to `http://127.0.0.1:8081`. Same pattern §6 already uses |
| 106 | §2 UFW + §10 + §15 | HA runs `network_mode: host` on `0.0.0.0:8123`, outside Docker's port-NAT, so UFW's `default deny incoming` drops all traffic to 8123 — but §2 never opened the port while §10 and §15 both assumed it was reachable. NPM's `ha.berrypi5.lan` proxy host 504s as a result | Added `ufw allow from 172.16.0.0/12 to any port 8123` (NPM→HA) and `ufw allow from 192.168.68.0/22 to any port 8123` (LAN-direct) to §2; rewrote the §15 deny-to-restrict note to use `ufw insert 1` so the deny precedes the allow (UFW is first-match-wins) |
| 107 | §6 Pi-hole `FTLCONF_dns_upstreams` | `172.30.0.2#5335` pointed FTL at port 5335, but the `mvance/unbound-rpi` container listens on port 53 — the `#5335` convention is for bare-metal setups where Unbound must dodge Pi-hole's own `:53`. Result: upstream resolution silently failed, no internet via Pi-hole | Changed to `172.30.0.2` (FTL defaults to port 53); corrected the stale inline comment and the §6 troubleshooting callout that referenced `#5335` / `:5335` |

**v5.1.7.10 bug-fix summary** — 2 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 101 | §7 Step-CA CLI fallback | Regression from fix #92: the Portainer-path instructions correctly tell the user to set `DOCKER_STEPCA_INIT_PASSWORD` in the stack's env-vars panel, but the adjacent CLI fallback (`cd /opt/step-ca && docker compose up -d`) didn't pass the env var inline; a CLI-path user would get the random-generated-and-logged behaviour back — the very thing fix #92 set out to eliminate | Patched the CLI fallback to `cd /opt/step-ca && DOCKER_STEPCA_INIT_PASSWORD='...' docker compose up -d`, matching the pattern used by the Pi-hole `dns` stack's CLI fallback (`FTLCONF_webserver_api_password='...'`) |
| 102 | §13 Watchtower CLI fallback | Pre-existing same-class bug: the prose tells the user to set `WATCHTOWER_NOTIFICATION_URL` in the Portainer env-vars panel, but the CLI fallback didn't pass it inline; a CLI-path user would deploy Watchtower with notifications silently disabled and the Sunday update schedule would fire without any Telegram alerts | Patched the CLI fallback to `WATCHTOWER_NOTIFICATION_URL='telegram://<token>@telegram?chats=<chat-id>' docker compose up -d` with a placeholder showing the expected shoutrrr URL format |

**v5.1.7.9 bug-fix summary** — 6 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 95 | §14 kill-switch test | `systemctl stop wg-quick@protonvpn` runs the `protonvpn-down.sh` PreDown hook, which removes the `PROTON_KS` chain from `OUTPUT`; the verification curl that followed therefore succeeded (route falls back to ISP) — the test was checking wg-quick teardown, not the kill switch itself | Replaced with `ip link set protonvpn down`, which drops the interface without invoking PreDown — the chain stays loaded and the curl is actually blocked; recovery is `systemctl restart wg-quick@protonvpn` so the handshake state is rebuilt cleanly |
| 96 | §15 MTU verification + breakage table | Both spots recommended dropping wg0 to 1240 "as a conservative value", contradicting fix #82's establishment of 1280 as the IPv6 minimum below which IPv6 breaks on wg0; fix #82 only updated the §4 comment | Rewrote both as an explicit IPv4-only-on-wg0 trade-off with cross-reference to fix #82 |
| 97 | §3 `docker-user-rules.sh` comment | Said "NPM's 80/443 are unaffected — those match the RELATED,ESTABLISHED RETURN first" — wrong; RELATED,ESTABLISHED only matches reply traffic in an already-allowed connection. The initial SYN from LAN to NPM 80/443 matches the LAN-source RETURN; reply packets ride RELATED,ESTABLISHED. Both rules are needed | Rewrote the comment to describe both directions correctly |
| 98 | §14 router-config table | Rows for "optional 80/443 port forwards (NPM, optional if you want public access)" implied a router-side toggle was sufficient, but DOCKER-USER's final DROP applies to WAN-sourced packets reaching the FORWARD chain; the public exposure silently fails | Added a ⚠️ footnote under the table explaining the DOCKER-USER constraint and showing the additional `iptables -A DOCKER-USER -p tcp -m multiport --dports 80,443 -j RETURN` rule that would be needed in `docker-user-rules.sh` |
| 99 | §3 "What cannot be a Portainer stack" list | Listed Portainer, wg0, ProtonVPN, and Restic as the four non-stack components but omitted `docker-socket-proxy`, which is also a non-stack `docker run` for the same chicken-and-egg reason as Portainer (Portainer's `DOCKER_HOST` targets it and needs it running first) | Added `docker-socket-proxy` as a bullet alongside Portainer with the rationale |
| 100 | §8 TOC entry | Read `[Nginx Proxy Manager + local DNS records](#8-nginx-proxy-manager)` — but the local-DNS-records subsection lives in §6 (Pi-hole admin → Local DNS → DNS Records), not §8; misleading TOC suffix from an earlier doc structure that has since shifted | Dropped the "+ local DNS records" suffix; entry now matches the actual section title |

**v5.1.7.8 bug-fix summary** — 3 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 92 | §7 Step-CA | Provisioner password was generated by Step-CA on first start and printed to logs exactly once — fragile because the log line can be missed and `daemon.json`'s `max-size=10m, max-file=3` log rotation can age it out within hours; lost password = destroy volume + re-init CA + re-install root cert on every device | Set `DOCKER_STEPCA_INIT_PASSWORD` in Portainer's stack env-vars panel before first deploy (same pattern as Pi-hole's `FTLCONF_webserver_api_password`); rewrote the surrounding callout to describe the env-vars approach with the legacy log-extraction noted as historical context |
| 93 | §12 backup script + restore drill + §15 git list | `/etc/apt/apt.conf.d/50unattended-upgrades` (the file §2 edits to set the 02:00 automatic-reboot window) was absent from restic backup paths, the restore drill, and the "what to put in git" list — a restore would silently revert to the package's default config and lose the customised reboot window | Added the path to all three places (backup, drill `--include` + `ls`, git list); updated the drill prose count from "six" to "seven config paths" |
| 94 | §12 setup | `alpine:3.21` (used by the backup script's volume-tarball loop) was never explicitly pre-pulled; the first scheduled 04:00 backup would be what triggers the pull, and if ProtonVPN happens to be down at that moment the kill switch blocks the pull, `set -euo pipefail` aborts the script, the `OnFailure` unit fires a Telegram alert, and no backup ever completes | Added `sudo docker pull alpine:3.21` step right after `apt install -y restic`, with a comment explaining the failure mode and why the image survives Watchtower cleanup (it's pinned, never auto-updated) |

**v5.1.7.7 bug-fix summary** — 1 new fix:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 91 | Top-of-doc revision-notes chain | Each `**Revision notes vs vX:**` line was a pure pointer to the changelog block immediately below it ("N bugs fixed, see vY changelog below") — no unique information, growing by one line per release; pure bloat | Deleted the entire chain |

**v5.1.7.6 bug-fix summary** — 7 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 84 | Revision notes header | Chain at top of doc jumped from `vs v4.1` straight to `vs v5.1.3` — both v5.1 (changelog block with 23 fixes #9–#31) and v5.1.3 (changelog block with 15 fixes #32–#46) were real releases with their own blockquote changelogs and summary tables, but no `vs v5` or `vs v5.1` headers existed in the chain to describe the v5→v5.1→v5.1.3 transitions; fix #81's claim that "every other version in the chain has a corresponding header" was inaccurate when applied to this gap | Inserted `Revision notes vs v5:` and `Revision notes vs v5.1:` lines between the `vs v4.1` and `vs v5.1.3` entries, in chronological position |
| 85 | Changelog formatting | Three consecutive blank lines between the v5.1.7.4 and v5.1.7.3 changelog sections — introduced when the v5.1.7.4 changelog block was inserted in v5.1.7.4 and survived through v5.1.7.5; only a single blank line is used as a section separator everywhere else in the changelogs | Reduced to a single blank line, consistent with all other changelog section separators (same class of fix as #75) |
| 86 | §12 backup script trap comment | Prose listed "Pi-hole, HA, NPM, Portainer, and Kuma" (5 services) as the things left stopped on a mid-backup failure, but `STOP_LIST` has had `mosquitto` in it since fix #56 (v5.1.6) — six services in total; doc lagged code | Updated comment to list six services including Mosquitto |
| 87 | §10 Mosquitto bind mount | `mosquitto.passwd` mount declared `:ro`, but the §10 instructions immediately tell the user to populate the file via `docker exec -it mosquitto mosquitto_passwd -c /mosquitto/config/mosquitto.passwd <user>` — a write operation that fails with EACCES on a read-only mount; additionally, on first deploy without a pre-existing host file, Docker auto-creates the bind-mount source as a *directory*, causing Mosquitto's config parse to fail (same class as fix #44) | Dropped `:ro` from the `mosquitto.passwd` mount; added an explicit `touch` step before stack deploy and an explanatory note in the YAML comment about the trade-off |
| 88 | §3 directory mkdir | `mkdir -p /opt/{dns,step-ca,npm,homeassistant,kuma,watchtower}` omitted `portainer` from the brace expansion, but the §15 directory tree at the end of the doc lists `/opt/portainer/` (with a "no compose file — bootstrapped via docker run" note); either the directory had to exist on disk or the §15 row had to be dropped | Added `portainer` to the brace expansion so the directory matches what §15 documents |
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
| 78 | §12 `homelab-backup-notify@.service` | `curl` call had no `--max-time`; an unreachable `api.telegram.org` caused the notify unit to hang indefinitely, blocking systemd's failure-handling path — the same class of bug fixed in the health script by fix #76 | Added `--max-time 10` |
| 79 | §12 Restore drill | `/etc/ssh` is included in the restic backup but was never restored or verified in the drill; prose said "five config paths" | Added `restic restore … --include /etc/ssh` and matching `ls` step; updated prose count to "six" |
| 80 | §13 Health push script | Stale `FIX #49` comment appeared inside the sysfs-unreadable `else` branch explaining that `--cacert` is unnecessary on plain HTTP — true, but irrelevant inside the error branch; the explanation already appears correctly on the `KUMA_BASE` declaration | Removed the misplaced comment from the error branch |

**v5.1.7.3 bug-fix summary** — 4 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 73 | v5.1 changelog | Fix #24 (remove `-k` from §14 functional test curl) was in the summary table and applied to the doc, but absent from the changelog text — the sequence jumped #23 → #25; the "23 new fixes" header was correct against the table but misleading against the changelog | Added the missing changelog entry between #23 and #25 |
| 74 | Revision notes (top of doc) | "Revision notes vs v4" and "vs v4.1" both said "see v5 bug-fix changelog below" — no such section existed; the five structural v5 changes had no changelog | Added `v5 bug-fix summary` table documenting the five v5 structural changes |
| 75 | Changelog formatting | Three consecutive blank lines between v5.1.4 and v5.1.3 changelog sections — fix #31 removed a stray double blank line elsewhere but this one was missed | Reduced to a single blank line, consistent with all other changelog section separators |
| 76 | §13 Health push script | All four `curl` calls had no `--max-time` — on a temporarily unresponsive Kuma, each call blocks for curl's default timeout (~2 min); the script's `if/else` structure means exactly two calls fire per invocation (one SoC branch + one NVMe branch), so a single run can stall for ~4 minutes; with a 60-second cron period, processes pile up and don't resolve until Kuma recovers | Added `--max-time 5` to all four calls |

**v5.1.7.2 bug-fix summary** — 4 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 69 | v5.1.7.1 summary table | Header said "4 new fixes" but the table contained 7 entries (#62–#68); the revision note at the top correctly said "Seven bugs fixed" | Corrected to "7 new fixes" |
| 70 | §12 `homelab-backup-notify@.service` | No `After=`/`Wants=network-online.target` — a backup failure before the network stack was ready caused the Telegram `curl` to fail silently with no notification delivered | Added `After=network-online.target` and `Wants=network-online.target` |
| 71 | §12 Restore drill | Five `ls` verification steps ran outside the `sudo bash -c` block as the `pi` user — they executed even when a restore had failed early, since `/tmp` is world-readable; a partial or empty restore target looked like a success | Moved all `ls` steps inside the `sudo bash -c` block so they only run after the restores complete and fail visibly if any path is missing |
| 72 | §4 `protonvpn.conf` | `MTU = 1320` had no comment explaining it is ProtonVPN's server ceiling, why it differs from wg0's 1280, or what to do on low-path-MTU ISP links — left readers without context on the relationship between the two MTU values | Added inline comment explaining the ceiling, the stacked-encapsulation arithmetic, and the §15 probe as the diagnostic tool |

**v5.1.7.1 bug-fix summary** — 7 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 62 | §5 wg0 server config | `MTU = 1320` — after wg0 encapsulation (~60 B overhead) the packet exceeds protonvpn's own 1320-byte MTU, causing fragmentation or silent large-transfer stalls on the stacked tunnel | Lowered to `MTU = 1280` (IPv6 minimum MTU, safe floor for wg0-inside-protonvpn); added comment explaining the interaction |
| 63 | §5 wg0 client config | `DNS = 10.10.0.1` only — with `AllowedIPs = ::/0`, IPv6-first OSes (iOS, Android, macOS) attempt DNS over IPv6 and bypass Pi-hole entirely when no IPv6 DNS address is listed, leaking DNS to the carrier resolver; also client `MTU = 1320` didn't match the now-corrected server value | Added `fd00:10:10::1` to DNS field; aligned client MTU to `1280` |
| 64 | §12 Backup script | `/etc/cloud/cloud.cfg.d` absent from restic backup paths — fix #41 added the cloud-init network-management disable step but its config file was never included in the backup; a restic-only restore loses it and cloud-init overwrites `50-cloud-init.yaml` with DHCP on the next reboot | Added `/etc/cloud/cloud.cfg.d` to the `restic backup` invocation |
| 65 | §13 Health push script | No `else` branch on the `if [ -e "$NVME_DEV" ]` check — when the device path is wrong or missing, no push is sent; Kuma's push monitor heartbeat expires silently and shows "down" with no message, indistinguishable from a real SMART critical warning | Added `else` branch that pushes `status=down&msg=NVME_DEV+<path>+not+found` with a pointer to `lsblk` for diagnosis |
| 66 | §15 MTU verification | §15 prose said "Both wg0 and protonvpn are set to MTU 1320" — fix #62 changed wg0 to 1280; the stale description, ping probe range, and troubleshooting table row all referred to the old value | Updated prose, probe range, and troubleshooting row to reflect wg0 MTU 1280 |
| 67 | §12 `homelab-backup.service` | `After=docker.service` without `Requires=` — if Docker is stopped manually, the backup fires at 04:00, `docker volume ls` returns nothing, the volume-tarball loop is empty, and restic exits successfully with only config files backed up; no volumes, no alert | Added `Requires=docker.service`; systemd now refuses to start the backup if Docker is not running |
| 68 | §12 Restore drill | `/etc/cloud/cloud.cfg.d` added to the backup by fix #64 but not to the drill — the drill gave false confidence that a restore would land correctly, since it never verified the cloud-init disable file that prevents the DHCP revert | Added `restic restore … --include /etc/cloud/cloud.cfg.d` and matching `ls` step; updated the prose count from "four" to "five" |

**v5.1.7 bug-fix summary** — 5 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 57 | §13 Health push script | All three `curl` calls carried `--cacert /opt/step-ca/homelab-root-ca.crt` — fix #49 changed `KUMA_BASE` to `http://` (plain HTTP); curl ignores `--cacert` on plain HTTP; the flag was dead code and the TLS/MITM rationale in the comment was stale | Removed `--cacert` from all three calls; updated comment to note that loopback HTTP needs no certificate |
| 58 | §3 DOCKER-USER chain | Missing `127.0.0.0/8` RETURN rule — host-to-container loopback traffic (health push to `127.0.0.1:3001`, `docker run` in backup volume loop) has source `127.x.x.x`, which is not matched by the `172.16.0.0/12` inter-container RETURN and was silently DROP'd | Added `iptables -A DOCKER-USER -s 127.0.0.0/8 -j RETURN` before the DROP, with explanatory comment |
| 59 | §10 Mosquitto | Port binding comment claimed `localhost:1883` works alongside `192.168.70.5:1883` — port is bound to `192.168.70.5` only; nothing listens on `127.0.0.1:1883`; HA MQTT integration configured with `localhost` would get connection refused | Corrected comment to state HA must use `192.168.70.5:1883` |
| 60 | §2 Unattended upgrades | `Automatic-Reboot-Time "03:00"` — backup timer runs at `04:00` with `Persistent=true`; a reboot finishing close to 04:00 can trigger backup immediately before containers are fully up | Changed to `02:00`; added note explaining the 04:00 backup timer interaction and the dead zone to avoid |
| 61 | §15 gitleaks | `pip install --user pre-commit` fails on Ubuntu 24.04 with "externally-managed-environment" (PEP 668 enforcement); `--user` does not bypass this restriction | Replaced with `sudo apt install -y pipx && pipx install pre-commit && pipx ensurepath`; added note explaining why |

**v5.1.6 bug-fix summary** — 5 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 52 | §5 Client config | `Address = 10.10.0.2/24, fd00:10:10::2/64` — subnet masks on a WireGuard client `Address` cause the interface to claim ownership of the whole subnet locally, breaking peer-to-peer VPN routing and potentially conflicting with the client device's routing table | Corrected to `/32` and `/128` (host masks), consistent with the server-side `[Peer]` `AllowedIPs` |
| 53 | §12 `homelab-backup.service` | Missing `[Install]` section — `systemctl enable homelab-backup.service` would fail with "Unit file has no [Install] section"; the timer is the correct activation path but the absence causes confusing errors during troubleshooting | Added `[Install]` with `WantedBy=multi-user.target` and a comment clarifying the timer is the intended trigger |
| 54 | §15 UFW deny note | Claimed NPM reaches HA "via the host loopback" — NPM is a container on the `172.31.x.x` Docker bridge and reaches HA at `192.168.70.5:8123`; the conclusion (rule won't block NPM) was coincidentally correct but the reason was factually wrong | Corrected to state NPM traffic originates from `172.31.x.x`, not the LAN range, so the LAN deny rule does not affect it |
| 55 | §12 Backup script | `alpine` (implicit `:latest`) was the only unpinned image in the guide — could silently change behaviour on a major Alpine bump or fail if the registry is unavailable mid-backup | Pinned to `alpine:3.21` |
| 56 | §12 Backup script | `mosquitto` missing from `STOP_LIST` — its `mosquitto-data` volume was being tarred while the broker was live and writing; `docker stop` on a non-existent container is a no-op so it is safe to include unconditionally | Added `mosquitto` to `STOP_LIST` with explanatory comment |

**v5.1.5 bug-fix summary** — 3 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 49 | §13 Health push script | `KUMA_BASE` used `https://kuma.berrypi5.lan/api/push` — this resolves via Pi-hole DNS then traverses NPM; if either is down (or quiesced during a backup run), the push fails silently with a DNS/connection error instead of a meaningful status push | Changed to `http://127.0.0.1:3001/api/push`, which hits Kuma directly on its loopback-bound port, bypassing Pi-hole and NPM entirely |
| 50 | §12 Backup script | `/etc/systemd/system/homelab-backup.service.d` was listed as a directory entry — inconsistent with every other unit in the backup path list, which are individual files; could silently pick up unrelated drop-ins from other packages in the same directory | Changed to the explicit file `/etc/systemd/system/homelab-backup.service.d/notify.conf` |
| 51 | §15 Troubleshooting | "Watchtower broke a service" fix showed `docker compose pull && docker compose up -d` without a `cd` — fails with "no configuration file provided" if run from any directory other than `/opt/<service>` | Prepended `cd /opt/<service> &&` to make the command self-contained |

**v5.1.4 bug-fix summary** — 2 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 47 | §12 Backup failure notifications | `OnFailure=homelab-backup-notify@%n.service` — `%n` expands to the full unit name including its `.service` suffix (`homelab-backup.service`), so the instantiated unit name becomes `homelab-backup-notify@homelab-backup.service.service` (double suffix), which systemd can't find; backup failures were silently swallowed | Changed to `@%p.service`; `%p` expands to the prefix without the suffix (`homelab-backup`), giving the correct instance `homelab-backup-notify@homelab-backup.service` |
| 48 | §12 Restore drill | Prose said "the three config dirs most critical to a working network (VPN keys, static IP, NTP)" — but fix #35 added `/etc/sysctl.d` to the drill, making it four directories; the description was never updated | Corrected to "four config dirs" with the updated parenthetical "(VPN keys, static IP, NTP, and kernel tunables)" |

**v5.1.3 bug-fix summary** — 15 new fixes:

| # | Where | What was wrong | What changed |
|---|---|---|---|
| 32 | §12 Backup script | `for vol in $(docker volume ls -q)` word-splits on volume names with spaces or special characters, silently skipping them and producing a broken tar path | Replaced with `mapfile -t VOLUMES < <(docker volume ls -q)` + `for vol in "${VOLUMES[@]}"` |
| 33 | §3 daemon.json | `default-address-pools` base was `172.17.0.0/16` — Docker's own `docker0` bridge defaults to `172.17.0.1`; using the same range as the auto-allocation pool risks a prefix collision on daemon restart | Changed base to `172.20.0.0/14`, which avoids both `docker0` (`172.17.x`) and the manually-pinned `172.30–172.31.x` ranges |
| 34 | §13 Kuma push monitors | No instruction to set the Push monitor heartbeat interval — default may be shorter than the 60s cron period, causing false "down" alerts between script runs | Added explicit callout: set heartbeat interval to ≥60s when creating the Push monitors |
| 35 | §12 Restore drill | Drill only restored and verified `/etc/wireguard`; `/etc/netplan`, `/etc/chrony`, and `/etc/sysctl.d` are equally critical to a working network after a restore but were never tested | Expanded drill to restore and `ls`-verify all four dirs; added cleanup reminder |
| 36 | §3 Portainer | The "no `-v /var/run/docker.sock`" security note appeared *after* the `docker run` command — readers scanning the command block had no context before running it | Converted to a `> ℹ️` callout placed *before* the command; removed the trailing inline note |
| 37 | §15 troubleshooting table | `sudo ip rule flush` deletes all routing policy rules including the kernel defaults at priorities 0/32766/32767, breaking all routing until reboot — presented as the fix for a stale Proton rule | Replaced with targeted `ip rule del priority 50` + `ip rule del priority 51`, which remove only the rules this guide adds |
| 38 | §8 NPM proxy hosts | No "Ignore Certificate" warning for `stepca.berrypi5.lan` — Step-CA's backend is HTTPS and NPM may not trust the cert depending on timing, same situation as Portainer which already had the warning | Added equivalent "Ignore Certificate" callout for Step-CA |
| 39 | §12 Backup script | `/etc/sysctl.d`, `/etc/cron.d`, `/usr/local/bin/homelab-*.sh`, `/usr/local/bin/docker-user-rules.sh`, and the homelab systemd unit files were absent from the restic backup paths — documented as "put in git" but git is not a backup; a restic-only restore would lose these files | Added all missing paths to the `restic backup` invocation |
| 40 | §2 Hostname | `echo -e "127.0.0.1 localhost\n192.168.70.5 berrypi5"` overwrote `/etc/hosts` without the `::1 localhost` IPv6 loopback entries — removing them breaks IPv6 loopback resolution for Docker networking and some HA integrations | Replaced with `printf` that preserves `::1 localhost ip6-localhost ip6-loopback` |
| 41 | §2 Static IP | Guide edits `50-cloud-init.yaml` directly but never disables cloud-init network management — cloud-init regenerates the file on boot and reverts the Pi to DHCP, silently breaking the static IP on the next reboot or apt upgrade that triggers cloud-init | Added `echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` immediately after `netplan apply`; also noted in the Ubuntu gotchas table |
| 42 | §10 Mosquitto | Snippet shown as "add to the homeassistant stack" was missing `mosquitto-data:` and `mosquitto-log:` entries in the top-level `volumes:` block — `docker compose up` fails with "named volume not declared" without them; also unclear that HA (host network) reaches Mosquitto via localhost | Added explicit merged `volumes:` block and network clarification comment |
| 43 | §7 Step-CA | `DOCKER_STEPCA_INIT_DNS_NAMES` lacked `localhost` and `127.0.0.1`; the guide directs bootstrap access via `https://127.0.0.1:9000` over SSH tunnel but clients got `x509: certificate is valid for [other IPs], not 127.0.0.1` | Added `localhost` and `127.0.0.1` to the DNS names list |
| 44 | §10 Mosquitto | Bind-mount paths `./mosquitto.conf` and `./mosquitto.passwd` are relative; Portainer's web-editor working directory is `/`, resolving them to `/mosquitto.conf` — Docker creates a directory instead of a file, Mosquitto fails to parse config | Changed to absolute paths `/opt/homeassistant/mosquitto.conf` and `/opt/homeassistant/mosquitto.passwd` |
| 45 | §13 Health push | All three `curl` calls used `-sk` (`-s -k`) — `-k` silently disabled TLS verification, making pushes susceptible to local MITM and undermining the whole Step-CA setup | Replaced `-k` with `--cacert /opt/step-ca/homelab-root-ca.crt`; root CA already on disk from §7, no system-wide install needed |
| 46 | §12 Backup script | Variable named `TMPDIR` shadows the POSIX standard env var of the same name; restic and other child processes read `$TMPDIR` for their own scratch space, writing into the backup staging dir; those files were then included in every restic snapshot | Renamed to `STAGING` throughout the script |

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
| 4 | §12 Backup | `set -euo pipefail` with no trap meant a mid-backup failure left Pi-hole, HA, NPM, Portainer, and Kuma stopped permanently | Added `trap 'docker start $STOP_LIST' EXIT` before the stop; removed the now-redundant explicit `docker start` at the end |
| 5 | §3 DOCKER-USER | `iptables -A DOCKER-USER -j RETURN` appeared after the terminal `DROP` — unreachable and misleading | Removed the dead RETURN |
| 6 | §3 docker-socket-proxy | `DELETE=1` missing; `WATCHTOWER_CLEANUP: "true"` silently failed, old image layers accumulated on the SSD | Added `-e DELETE=1` to the `docker run` command |
| 7 | §15 troubleshooting | Table said "don't chattr +i" — contradicted §2's deliberate use of it post-setup | Updated to explain chattr +i is intentional and applied after setup |
| 8 | §13 Watchtower | `WATCHTOWER_LABEL_ENABLE: "true"` with no labelled containers anywhere; Watchtower did nothing on every Sunday run | Added opt-in label to the Kuma stack as a worked example; added explanatory note in the Watchtower section |

**v4 changes summary** — for your own reference when comparing to v3:

- **Docker→UFW bypass closed.** All admin UIs (Portainer 9443, NPM 81, Pi-hole 8080, Step-CA 9000, Kuma 3001) bound to `127.0.0.1`. Shared `proxy-net` Docker bridge created so NPM can reach them by container name. UFW `after.rules` adds a `DOCKER-USER` chain that drops all non-LAN, non-VPN container egress as defence-in-depth.
- **IPv6 on wg0.** ULA `fd00:10:10::/64` carried inside the tunnel; clients now route `::/0` over wg0 so dual-stack mobile data doesn't leak v6 outside the tunnel.
- **Pi-hole v6** with new `FTLCONF_*` env var schema (Alpine base). Web password moved to Portainer env vars panel, out of YAML/git.
- **chrony** with LAN-router NTP preferred; NTP exception in the Proton kill switch (UDP/123 RETURN). Boot-time clock drift during Proton outages no longer cascades into Step-CA TLS failures.
- **B2 split keys + Object Lock.** Daily backup key has no `deleteFiles`; admin key for `forget --prune` lives off-Pi. Object Lock prevents historical-backup wipe even on full credentialed compromise.
- **Backup widened.** NPM, Portainer, and Kuma are now quiesced alongside Pi-hole and HA. `forget`/`prune` moved out of the daily script to a manual weekly run from a different machine.
- **docker-socket-proxy.** Portainer and Watchtower no longer mount `/var/run/docker.sock` directly; both go through `tecnativa/docker-socket-proxy` with `EXEC=0` and minimal API capabilities.
- **HA: `privileged: true` removed.** Explicit `cap_add: [NET_ADMIN, NET_RAW, SYS_NICE]` plus `devices:` for Zigbee/Z-Wave (commented examples).
- **SMART + thermal monitoring** via Kuma push monitors fed by a cron-driven script (`homelab-health-push.sh`).
- **Image pins refreshed:** Pi-hole `2026.04.0`, HA `2026.5`, NPM `2.12.3`, Portainer `2.27.5`, Step-CA `0.28.4`, Kuma `1.23.16`, Mosquitto `2.0.21`, Unbound `1.22.0`, docker-socket-proxy `0.3.0`, Watchtower `1.7.1`.
- **MTU verification** procedure for stacked wg0+Proton tunnels added to ops.
- **gitleaks pre-commit hook** for the config repo.
- **Image-pin review cadence** recommendation added (quarterly).
- **TOC anchor for §9 fixed.**
- Pre-flight cleaned up; SD-card warning removed (the rest of the doc assumes SSD).
- Active cooler recommendation added.
