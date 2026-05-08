---
name: raspberry-pi
description: Headless Raspberry Pi setup — SSH via boot partition, WiFi, user rename, regulatory domain, headless imaging workflow
tags: ["raspberry-pi", "headless", "linux", "ssh", "pi-cluster"]
related_skills:
  - desktop-power-management
---

# raspberry-pi

Headless Raspberry Pi setup and management from a Linux workstation.

## Trigger

User is setting up a Raspberry Pi — headless, SSH-only, or with WiFi — and wants to configure it remotely from their Linux machine.

---

## Enable SSH on a Fresh Pi Image

Raspberry Pi OS has SSH disabled by default. Enable it before first boot by touching a file in the boot partition.

```bash
# Find the SD card device (replace X with actual letter)
lsblk
# boot partition is typically /dev/sdX1

sudo mount /dev/sdX1 /mnt/boot
sudo touch /mnt/boot/ssh        # empty file named "ssh" enables SSH
sudo umount /mnt/boot
```

SSH is now enabled. Boot the Pi with ethernet connected. Find its IP from your router or:

```bash
arp -a | grep raspberry
ip neigh show | grep <pi-mac-prefix>
```

Default login: `pi` / `raspberry` (change immediately).

---

## Rename Default User (evan → Evan)

Pi Imager creates a user `evan` (lowercase, POSIX-compliant). To get `Evan` on the Pi (matching your Linux workstation):

**Pi Imager enforces POSIX username rules (lowercase only). `Evan` with capital E is not allowed during imaging. Rename post-install is required.**

---

### Prerequisite: Passwordless Sudo (required for SSH rename)

SSH sudo times out because `echo pw | sudo -S cmd` does NOT work over SSH — sudo reads from TTY, not stdin, regardless of `-S`. Fix by configuring passwordless sudo on the Pi first:

```bash
# On the Pi (keyboard/monitor), as evan:
echo "evan ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/evan
```

Or configure from your Linux host via the boot partition:

```bash
# Mount the Pi's rootfs from the SD card (replace X with device letter)
sudo mount /dev/sdX2 /mnt/rootfs
echo "evan ALL=(ALL) NOPASSWD: ALL" | sudo tee /mnt/rootfs/etc/sudoers.d/evan
sudo umount /mnt/rootfs
```

---

### Method A: Direct Rename (requires evan NOT logged in)

`usermod -l` refuses to rename a user who is currently active (any process running as that user).

**If evan is logged in over SSH:** `pkill -u evan` from within the evan session will kill your own connection — DON'T do that. Use console/monitor instead.

**If evan is logged in at console (tty1):** A `login -- evan` process holds the user busy. Kill it with:
```bash
sudo kill -9 <pid-of-login-process>
```

Then rename:
```bash
ssh evan@<pi-ip> 'sudo usermod -l Evan -d /home/Evan -m evan && sudo groupmod -n Evan evan && sudo chpasswd Evan'
```

**Verify:**
```bash
ssh Evan@<pi-ip> 'id'
# should show uid=1000(Evan), gid=1000(Evan), groups=...sudo...
```

---

### Method B: Create Evan First, Then Delete Evan (preferred — reliable even when evan is stubborn)

This is the recommended workflow. It avoids all the "user currently used by process" deadlocks.

**Step 1 — Create Evan user with sudo from evan's SSH session:**
```bash
ssh evan@<pi-ip> 'sudo adduser Evan && sudo usermod -aG sudo Evan'
```

**Step 2 — Set Evan password (bypasses TTY issues):**
```bash
ssh evan@<pi-ip> 'echo "Evan:1717" | sudo chpasswd Evan'
```

**Step 3 — Push SSH public key for passwordless auth:**
```bash
# On your Linux host:
cat ~/.ssh/id_ed25519.pub
# Output: ssh-ed25519 AAAAC3... user@host

# As Evan on the Pi (from evan's SSH session):
ssh evan@<pi-ip> 'sudo mkdir -p /home/Evan/.ssh && sudo chmod 700 /home/Evan/.ssh && echo "<your-public-key>" | sudo tee /home/Evan/.ssh/authorized_keys > /dev/null && sudo chmod 600 /home/Evan/.ssh/authorized_keys && sudo chown -R Evan:Evan /home/Evan/.ssh'
```

**Step 4 — Configure passwordless sudo for Evan (from Evan's session via SSH key):**
```bash
ssh Evan@<pi-ip> 'echo "Evan ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/evan && sudo chmod 440 /etc/sudoers.d/evan'
```

**Step 5 — Delete evan (from Evan's session — SSH key auth, no password needed):**
```bash
ssh Evan@<pi-ip> 'sudo pkill -9 -u evan; sleep 1; sudo deluser -f --remove-home evan'
```
Force delete (`-f`) is required — systemd respawns evan user processes, and plain `deluser` will fail with "user is currently used by process".

**Verify:**
```bash
ssh Evan@<pi-ip> 'id evan 2>&1; ls /home/evan 2>&1; echo "--- Evan:"; id; ls /home/Evan'
```
Expected: `evan: no such user`, Evan has uid=1000( Evan) and home directory.

---

### Why SSH sudo with piped passwords always fails

```bash
# THIS TIMES OUT — sudo reads from TTY, not stdin, regardless of -S
ssh evan@<pi-ip> 'echo pw | sudo -S cmd'
# Also fails: -t, -tt, none of it works because sudo requires a real TTY

# WORKING approaches:
# 1. Passwordless sudo configured on the Pi (Step 4 above)
# 2. Method B — create Evan first, SSH key auth, delete evan from Evan's session
# 3. Physical keyboard/monitor on the Pi console
```

### Known evan deletion pitfalls

**PITFALL:** `pkill -u evan` run FROM an evan SSH session kills YOUR OWN connection. Run it from Evan's session.
**PITFALL:** Even after `pkill -9 -u evan`, systemd respawns evan processes. Use `sudo deluser -f` (force) — it bypasses the "user currently used" check.
**PITFALL:** `login -- evan` on tty1 (console) must be killed separately. Find it with `ps aux | grep evan`, then `sudo kill -9 <pid>` from Evan's session.

---

### Quick-Reference: Why SSH sudo piped passwords fail

```bash
# THIS TIMES OUT — sudo reads TTY, not stdin, despite -S
ssh evan@<pi-ip> 'echo pw | sudo -S cmd'

# THIS ALSO FAILS — stdin is not a TTY
ssh -t evan@<pi-ip> 'echo pw | sudo -S cmd'
ssh -tt evan@<pi-ip> 'echo pw | sudo -S cmd'
```

**Working approaches for sudo over SSH:**
1. Configure NOPASSWD sudo on the Pi first (see prerequisite above)
2. Keyboard/monitor on the Pi console directly
3. Method B above — create Evan first, delete evan from Evan's session

---

## Fix 5GHz WiFi Not Showing

**Symptom:** 2.4GHz WiFi works, 5GHz SSIDs don't appear in scan.

**Cause:** Regulatory domain not set — the WiFi adapter can't scan 5GHz channels without it.

**Fix — on the Pi over SSH:**
```bash
sudo raspi-config
# Navigate: Localization Options → WLAN Country → select your country
# e.g., US, GB, DE, etc.
```

Or from command line:
```bash
# Check current
iw reg get

# Set permanently
sudo raspi-config nonint do_wifi_country US
```

Then reboot: `sudo reboot`

---

## WiFi Configuration (wpa_supplicant)

If you need to configure WiFi manually before the Pi boots:

```bash
sudo mount /dev/sdX2 /mnt/rootfs   # rootfs partition

cat << 'EOF' | sudo tee /mnt/rootfs/etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={
    ssid="YourSSID"
    psk="yourpassword"
}
EOF

sudo umount /mnt/rootfs
```

---

## Static IP on WiFi (dhcpcd.conf)

Pi-hole and most network services need a static IP. On Raspberry Pi OS (bookworm/trixie), interfaces are managed by `dhcpcd` by default. If the Pi is on WiFi with a dynamic DHCP lease, add static config:

```bash
# Append to /etc/dhcpcd.conf
interface wlan0
static ip_address=10.0.0.67/24
static routers=10.0.0.1
static domain_name_servers=10.0.0.67 1.1.1.1 9.9.9.9
```

- `wlan0` not `eth0` — check `ip addr` to confirm which interface is active
- Use the same IP the Pi currently has (check `ip -4 addr show wlan0`)
- Gateway is usually `.1` on the subnet — verify with `ip route | grep default`
- Reboot after adding: `sudo reboot`
- Pi-hole installer will pre-fill the IP if it matches what the Pi currently has

## Pi-hole Installation

Pi-hole's official installer (`curl -sSL https://install.pi-hole.net | bash`) is **fully interactive** and requires a **real TTY** — it CANNOT be run over SSH with piped bash. The install uses `dialog`-style prompts that read from `/dev/tty` regardless of stdin redirection.

**Headless install is not supported by the official installer.** Attempts like `curl ... | bash`, `ssh ... 'echo pw | sudo -S bash'`, or `expect` scripts all fail for the same reason: sudo requires a TTY that SSH cannot provide from a remote host.

**Recommended approach — run from Pi console (fastest):**

1. Connect monitor + keyboard to the Pi, or use a console session
2. Run:
   ```bash
   sudo bash
   curl -sSL https://install.pi-hole.net | bash
   ```
3. Picks during install:
   - **Upstream DNS:** Cloudflare (`1.1.1.1`) or Quad9 (`9.9.9.9`)
   - **Blocklists:** Accept defaults (press Enter)
   - **Static IP:** Accept pre-filled value (10.0.0.67) — Pi already has static config in dhcpcd
   - **Web interface:** Yes
   - **Lighttpd:** Yes
   - **Log queries:** Yes
   - **Privacy level:** 0 (show everything)
   - **Firewall:** 1 (On)
4. Note the random admin password shown at end of install
5. Reboot: `sudo reboot`

**After install — reset web admin password:**
```bash
ssh Evan@<pi-ip> 'sudo pihole -a -p'
```

**Verify (MUST DO — headless installs often leave gravity.db empty):**
```bash
ssh Evan@<pi-ip> 'sudo pihole status'
# Should show FTL listening on port 53, blocking enabled

# CRITICAL: Check gravity.db has blocklists
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/gravity.db "SELECT COUNT(*) FROM adlist; SELECT COUNT(*) FROM gravity"'
# If both return 0, default blocklists were NOT populated — blocking won't work
```

**PITFALL: Pi-hole headless install leaves gravity.db empty:**
The installer skips blocklist population during unattended/headless installs, producing a gravity.db with zero entries. `pihole -g` then has nothing to pull from and gravity stays empty. The fix is to populate the adlist table manually before running gravity:
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/gravity.db "INSERT INTO adlist (address, enabled, date_added) VALUES
('\''https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts'\'', 1, strftime('\''%s'\''','\''now'\'''\'')),
('\''https://adaway.org/hosts.txt'\'', 1, strftime('\''%s'\''','\''now'\'''\'')),
('\''https://v.firebog.net/hosts/AdguardDNS.txt'\'', 1, strftime('\''%s'\''','\''now'\'''\'')),
('\''https://v.firebog.net/hosts/Easyprivacy.txt'\'', 1, strftime('\''%s'\''','\''now'\'''\''));'"
ssh Evan@<pi-ip> 'sudo pihole -g'
# Expected: ~295K domains pulled in
```

**Fix empty gravity.db (if above shows 0):**
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/gravity.db "
INSERT INTO adlist (address, enabled, date_added) VALUES
('\''https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts'\'', 1, strftime('\''%s'\'', '\''now'\'')),
('\''https://adaway.org/hosts.txt'\'', 1, strftime('\''%s'\'', '\''now'\'')),
('\''https://v.firebog.net/hosts/AdguardDNS.txt'\'', 1, strftime('\''%s'\'', '\''now'\'')),
('\''https://v.firebog.net/hosts/Easyprivacy.txt'\'', 1, strftime('\''%s'\'', '\''now'\''));"
sudo pihole -g  # Pull in blocklists (~295K domains)
```

**Verify blocking works:**
```bash
dig @<pi-ip> doubleclick.net +short
# Should return 0.0.0.0 (blocked) not a real IP
dig @<pi-ip> google.com +short
# Should return a real IP (not blocked)
```

**Dashboard:** `http://10.0.0.67/admin`

## VNC Server Setup (RealVNC on Raspberry Pi OS)

Raspberry Pi OS ships with RealVNC Server pre-installed. Do NOT install tigervnc packages — they conflict with RealVNC and provide a different, incompatible experience.

**Check if RealVNC is already running:**
```bash
ss -tlnp | grep 5900
# If output, VNC is already active
```

**Set VNC password (required before first connection):**
```bash
vncpasswd -virtual
# Enter password (min 6 characters), confirm
# Password stored in ~/.vnc/config.d/vncserver-x11-virtual
```

**Start VNC server (Virtual Mode — headless):**
```bash
vncserver-virtual :1 -geometry 1280x800 -depth 24
```

**PITFALL — `-localhost no` flag does not exist on RealVNC ARM:**
```bash
# WRONG — causes "Unrecognized option: no" error
vncserver :1 -localhost no -geometry 1280x800

# CORRECT — use vncserver-virtual (not vncserver) for headless virtual desktop
vncserver-virtual :1 -geometry 1280x800 -depth 24
```

**VNC Password Requirements:** VNC requires minimum 6-character passwords. `1717` is too short — use `evan1717` or similar.

**VNC password change:**
```bash
vncpasswd -virtual
# Enter new password (min 6 chars)
```

**Conky Manager on ARM — "missing import" error:**

**List active sessions:**
```bash
vncserver -list
```

**Stop a session:**
```bash
vncserver -kill :1
```

**Verify it's running:**
```bash
ss -tlnp | grep 5900
# Should show: LISTEN 0 16 *:5900 *:*
```

**Connect from VNC client:**
- Address: `10.0.0.67:5900` (or just `10.0.0.67` on default port 5900)
- Password: whatever was set via `vncpasswd -virtual`

**ISP Gateway Limitation:** Many ISP-provided gateways (e.g., Comcast Technicolor XB6/CGM4140COM) do NOT allow changing DNS or DHCP DNS settings — the DNS fields are read-only status displays showing what Comcast assigns. In this case, per-device DNS config is the only option. See `references/isp-gateway-dns-limitations.md` for per-device setup.

**Conky Manager on ARM — "missing import" error:**
Conky Manager needs `imagemagick` (provides the `import` command used for generating theme previews). Install with:
```bash
sudo apt-get install -y imagemagick
```

**Conky themes segfault on ARM with old syntax:**
The themes packaged with Conky Manager use old conky syntax that causes segfaults on conky 1.22+ when run with `DISPLAY=:N` over SSH. The conky binary itself works — test with console mode:
```bash
conky -c ~/.conky-manager/t.lua   # lua syntax works
```
For the GUI, run directly in a VNC terminal session, not over SSH with DISPLAY set. The segfault is a display/X11 issue, not a config issue.

## Conky Manager on Raspberry Pi OS (ARM)

Conky Manager from teejee2008 has no ARM build. Install conky (conky-std) from apt, and build Conky Manager from source.

**Install conky:**
```bash
sudo apt-get update
sudo apt-get install -y conky-std
```

**Install build dependencies:**
```bash
sudo apt-get install -y valac libgtk-3-dev libgee-0.8-dev libjson-glib-dev
```

**Clone and build Conky Manager:**
```bash
cd /tmp
git clone https://github.com/teejee2008/conky-manager.git
cd conky-manager
make
```

The `make` will fail at the translation step (`xgettext`/`msgfmt` not installed) but the binary compiles successfully. To install anyway:
```bash
sudo cp src/conky-manager /usr/bin/
sudo mkdir -p /usr/share/conky-manager/{icons,scripts,themepacks}
sudo cp -r icons/* /usr/share/conky-manager/icons/
sudo cp -r scripts/* /usr/share/conky-manager/scripts/
sudo cp -r themepacks /usr/share/conky-manager/
```

**Launch from VNC:**
```bash
conky-manager
```

Or find it in the desktop menu under Accessories or System Tools.

**PITFALL:** The official Conky Manager `.deb` and `.run` binaries are `amd64` only — they will refuse to install on ARM with "package architecture (amd64) does not match system (armhf)". Only the source build works.

## Pi-hole Conky Widget

Custom Conky widget showing live Pi-hole stats — runs on the Pi itself (VNC desktop) or from another machine pointing at the Pi's databases.

### Prerequisites

Evan must be able to read the FTL database directly (no sudo password prompts in Conky):

```bash
ssh Evan@<pi-ip> 'sudo usermod -aG pihole Evan && sudo chmod 640 /etc/pihole/pihole-FTL.db /etc/pihole/gravity.db'
# Then log out and back in for group membership to take effect
```

### Conky Config

Save as `~/.conky/pihole.conky` on the Pi:

```
conky.config = {
  alignment = 'top_right',
  background = false,
  default_color = 'white',
  font = 'Droid Sans Mono:size=11',
  gap_x = 20,
  gap_y = 20,
  minimum_width = 240,
  own_window = true,
  own_window_argb_visual = true,
  own_window_argb_value = 200,
  own_window_colour = '000000',
  own_window_type = 'desktop',
  update_interval = 30,
  use_xft = true,
  xftalpha = 0.8,
};

conky.text = [[
${color orange}${hr}
${color orange}PI.HOLE
${color lightgrey}Domains: ${color}${execi 30 sqlite3 /etc/pihole/gravity.db "SELECT COUNT(*) FROM gravity;"}
${color lightgrey}Queries: ${color}${execi 30 sqlite3 /etc/pihole/pihole-FTL.db "SELECT COUNT(*) FROM queries;"}
${color lightgrey}Blocked: ${color}${execi 30 sqlite3 /etc/pihole/pihole-FTL.db "SELECT COUNT(*) FROM queries WHERE status=3;"}
${color lightgrey}Block Rate: ${color}${execi 30 python3 /home/Evan/.conky/block_rate.py}
${color orange}${hr}
${color lightgrey}Uptime: ${color}${execi 30 uptime -p | sed 's/up //'}
${color lightgrey}Load: ${color}${loadavg}
${color lightgrey}RAM: ${color}${mem}/${memmax} ${memperc}%
${color lightgrey}CPU: ${color}${cpu}%
${color orange}${hr}
]]
```

**PITFALL:** `execi` with `sudo sqlite3` will HANG — Conky waits for a TTY password prompt that never comes. Use one of:
1. Evan is in the `pihole` group and can read `/etc/pihole/pihole-FTL.db` directly (no sudo needed)
2. Or pre-install `block_rate.py` script that handles permissions internally

### Block Rate Script

Save as `~/.conky/block_rate.py`:

```python
#!/usr/bin/env python3
"""Block rate calculator — queries table, status=3 = blocked."""
import sqlite3
try:
    conn = sqlite3.connect('/etc/pihole/pihole-FTL.db')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM queries")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM queries WHERE status=3")
    blocked = cur.fetchone()[0]
    conn.close()
    if total > 0:
        print(f"{(blocked/total*100):.1f}%")
    else:
        print("0%")
except:
    print("--")
```

```bash
chmod +x ~/.conky/block_rate.py
```

### Run

```bash
conky -c ~/.conky/pihole.conky
```

### Auto-start (VNC desktop)

Create `~/.config/autostart/conky-pihole.desktop`:
```
[Desktop Entry]
Name=Conky Pi-hole
Exec=conky -c ~/.conky/pihole.conky
Type=Application
```

---

## One-Shot Remote Config (Single SSH Command)

Requires passwordless sudo (see prerequisites in Rename section above):
```bash
ssh evan@<pi-ip> 'sudo usermod -l Evan -d /home/Evan -m evan && sudo groupmod -n Evan evan && sudo chpasswd Evan'
```

Then connect as `Evan@<pi-ip>`.

---

## Raspberry Pi Imager — Username Restriction

- The Imager enforces POSIX username rules during OS write.
- It WILL NOT let you create a user named `Evan` (capital E).
- Workaround: write with `evan`, rename post-install (see above).
- Your Linux workstation may allow `Evan` (non-standard) — Pi OS does not.

---

## References

- `references/pi-cluster-notes.md` — Session-specific notes from Evan's Pi cluster setup (WiFi issue, user rename steps, boot partition commands)
- `references/isp-gateway-dns-limitations.md` — Comcast XB6 DNS limitation and per-device DNS setup for Linux, iOS, TCL Roku, Android, Windows, macOS
- `references/pihole-gravity-empty-fix.md` — Fix for empty gravity.db after headless Pi-hole install (adlist population, blocklist URLs, gravity pull, FTL query SQL)
- `references/pihole-ftl-queries.md` — Pi-hole FTL database: FTLv6 `queries` table (not `query_storage`), status=3 blocked, reply_type codes, common SQL queries, health check, block rate script reference
- `references/pihole-per-device-troubleshooting.md` — Why a device not appearing in Pi-hole query log means it's not using Pi-hole as DNS, with diagnostic commands