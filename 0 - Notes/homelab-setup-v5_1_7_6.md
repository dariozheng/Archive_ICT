# Homelab Setup Guide v5.1.7.6 — Ubuntu Server 24.04 LTS on Raspberry Pi 5
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
8. [Nginx Proxy Manager + local DNS records](#8-nginx-proxy-manager)
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
# NPM's 80/443 are unaffected — those match the RELATED,ESTABLISHED RETURN first.
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

**What cannot be a Portainer stack** (these stay as systemd services):
- Portainer itself — chicken-and-egg, must exist before stacks can be created
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
      FTLCONF_dns_upstreams: "172.30.0.2#5335"   # Pi-hole v6 keeps the v5 "#port" separator
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

> ⚠️ **If upstream resolution fails after deploying:** the `<ip>#<port>` syntax was inherited from v5's dnsmasq backend. v6 replaces dnsmasq with FTL's own resolver, and at least one user reports v6 also accepts `<ip>:<port>`. If `nslookup google.com 192.168.70.5` times out, exec into Pi-hole and check `/etc/pihole/pihole.toml` — under `[dns]` the `upstreams` value should be `["172.30.0.2#5335"]`. If FTL logs show "unable to parse upstream", try `FTLCONF_dns_upstreams: "172.30.0.2:5335"` instead and redeploy.

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
# CLI fallback:
cd /opt/step-ca && docker compose up -d
```

> ⚠️ **Save the provisioner password now.** Step-CA prints it exactly once on first start. Run the following immediately and store the password in your password manager:
> ```bash
> docker logs step-ca 2>&1 | grep -i -E "password|Password"
> ```
> If you lose it you must re-initialise the CA and re-install the root cert on every device.

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
    entrypoint: ["/bin/sh", "-c", "update-ca-certificates && /init"]
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

Access `http://127.0.0.1:81` via SSH tunnel: `ssh -L 81:127.0.0.1:81 pi@192.168.70.5`. Default login `admin@example.com` / `changeme` — change immediately.

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
'
```

The drill confirms the six config paths most critical to a working network (VPN keys, static IP, NTP, kernel tunables, cloud-init network disable, and SSH hardening) are present in the snapshot. Clean up after: `sudo rm -rf /tmp/restore-test`.

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
# CLI fallback:
cd /opt/watchtower && docker compose up -d
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
| Port forward 80/TCP | → `192.168.70.5:80` (NPM, optional if you want public access) |
| Port forward 443/TCP | → `192.168.70.5:443` (NPM, optional) |

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
sudo systemctl stop wg-quick@protonvpn
curl --max-time 5 ifconfig.me           # should fail (kill switch active)
chronyc tracking                        # should STILL work — NTP is in the kill-switch exception
sudo systemctl start wg-quick@protonvpn
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

> ℹ️ Home Assistant intentionally stays on `network_mode: host` (mDNS / HomeKit requirement) and so its port 8123 remains reachable from the whole LAN. If you want to enforce NPM-only access to HA as well, add a UFW rule: `sudo ufw deny from 192.168.68.0/22 to any port 8123` (NPM reaches HA at `192.168.70.5:8123` — its traffic originates from the `172.31.x.x` Docker bridge, not `192.168.68.0/22`, so it is unaffected by this rule).

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

The last `OK` size + 28 (ICMP+IP headers) is your true effective MTU. If it's below 1280, drop both the wg0 server and client `MTU` values to match (or to 1240 as a conservative floor). Mismatched MTUs typically show up as "WireGuard connects but big requests hang" — HTTPS handshakes complete, but large responses stall.

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
| Slow VPN throughput / random disconnects | MTU too high through stacked tunnels | wg0 is already set to 1280 (fix #62); run the MTU probe in §15 and lower wg0 + clients further if the stall persists (1240 is a safe conservative value) |
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

`/opt/*/docker-compose.yml`, `/etc/netplan/50-cloud-init.yaml`, `/etc/sysctl.d/99-homelab.conf`, `/etc/ssh/sshd_config.d/99-hardening.conf`, `/etc/chrony/chrony.conf`, `/etc/wireguard/protonvpn-up.sh`, `/etc/wireguard/protonvpn-down.sh`, `/usr/local/bin/homelab-backup.sh`, `/usr/local/bin/homelab-health-push.sh`, `/usr/local/bin/docker-user-rules.sh`, `/etc/systemd/system/docker-user-rules.service`, `/etc/cron.d/homelab-health`, the rest of the systemd unit files, and a sanitised version of `wg0.conf` (keys redacted). Commit the lot to a private GitHub repo with `gitleaks` as a pre-commit hook. Restic handles the rest (data); git handles the recipe.

Keep the on-disk compose files in sync with what you paste into Portainer. The easiest habit: edit the file on disk first, then paste the updated content into the Portainer stack editor. That way git always has the source of truth.
