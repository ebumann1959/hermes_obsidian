# Evan's Pi Cluster Setup — Session Notes

## Hardware/Software
- Host machine: MX25Rig (MX Linux 25, KDE Plasma)
- Pi model: Raspberry Pi 3
- Pi OS image written with Raspberry Pi Imager 2.0.7 (AppImage at `/home/Evan/Documents/imager_2.0.7_amd64.AppImage`)

## User Setup
- Evan wants `Evan` as username on all Pis (matching his Linux workstation)
- Same password across all Pis
- Pi Imager only allows lowercase usernames during write → workaround: write as `evan`, rename post-install

## Rename evan→Evan (live session notes — 2025-05-07)

### What actually worked: Method B (create Evan first, then delete evan)

```bash
# 1. As evan, create Evan with sudo
ssh evan@<pi-ip> 'sudo adduser Evan && sudo usermod -aG sudo Evan'
ssh evan@<pi-ip> 'echo Evan:1717 | sudo chpasswd Evan'

# 2. Set Evan password via tee (chpasswd approach fails with TTY)
ssh evan@<pi-ip> 'echo "Evan:1717" | sudo tee /etc/sudoers.d Evan.tmp > /dev/null 2>&1 || echo Evan:1717 | sudo chpasswd Evan'

# 3. Push SSH public key for passwordless auth
ssh Evan@<pi-ip> 'mkdir -p /home/Evan/.ssh && chmod 700 /home/Evan/.ssh'
ssh Evan@<pi-ip> 'echo "<ed25519-pub-key>" >> /home/Evan/.ssh/authorized_keys'
ssh Evan@<pi-ip> 'chmod 600 /home/Evan/.ssh/authorized_keys && chown -R Evan:Evan /home/Evan/.ssh'

# 4. Configure passwordless sudo for Evan
ssh Evan@<pi-ip> 'echo "Evan ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/evan && sudo chmod 440 /etc/sudoers.d/evan'

# 5. Delete evan — must be done from Evan's session (not evan's!)
ssh Evan@<pi-ip> 'sudo pkill -9 -u evan'
ssh Evan@<pi-ip> 'sudo deluser -f --remove-home evan'   # -f (force) bypasses "user currently used" check

# 6. Verify
ssh Evan@<pi-ip> 'id evan 2>&1; ls /home/evan 2>&1; echo "evan gone"; ls /home/Evan'
```

### Key findings from this session

- `deluser --remove-home` alone fails with "user currently used by process" — systemd keeps respawning evan via `--user` instance
- `deluser -f` (force) bypasses the check and succeeds even when processes remain
- `pkill -9 -u evan` run from evan's own SSH session kills that session — must run from Evan
- `login -- evan` on tty1 must be killed separately; it's the console login session, not a regular user process
- After `pkill -9 -u evan`, evan processes respawn because systemd --user instance restarts them — `deluser -f` is the fix, not waiting for clean state
- Passwordless sudo + SSH key auth = fully non-interactive management, no passwords ever needed

### SSH sudo piped-password failure (confirmed root cause)

`sudo -S` reads from stdin but sudo itself also reads from `/dev/tty` for the password prompt. When SSH pipes stdin, `/dev/tty` is not a terminal, so sudo's password prompt hangs indefinitely.

Working alternatives:
1. Passwordless sudo (`NOPASSWD`) — best, set up via boot partition before first boot
2. SSH key auth + `sudo tee` approach for password file edits
3. Keyboard/monitor on Pi console

### Outcome (this session)
- evan deleted successfully, Evan active at 10.0.0.67
- SSH key auth working, passwordless sudo configured
- User's requirement: no password prompts ever, agent handles everything

### Fix for next time — configure passwordless sudo BEFORE first SSH session
On a fresh Pi Imager install, configure passwordless sudo via the boot partition before first boot:
```bash
# Mount SD card rootfs (replace X with device)
sudo mount /dev/sdX2 /mnt/rootfs
echo "evan ALL=(ALL) NOPASSWD: ALL" | sudo tee /mnt/rootfs/etc/sudoers.d/evan
sudo umount /mnt/rootfs
```
Then direct rename works over SSH without any of the session/lock issues.

### Gravity database empty after headless install (CRITICAL BUG — 2026-05-07)

After running the Pi-hole installer from console, gravity.db was **completely empty**:
```
domainlist: 0 domains
adlist: 0 entries
gravity: 0 entries
```

Blocking appeared enabled (`pihole status` green) but no domains blocked — ad servers resolved normally. The headless/unattended installer skips configuring default blocklists.

**Fix — add blocklists via sqlite3 then run gravity:**
```bash
# The adlist table requires 'type' column (Pi-hole v6). Omitting it causes silent failure.
sudo sqlite3 /etc/pihole/gravity.db "INSERT INTO adlist (address, enabled, date_added, type) VALUES
('https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts', 1, strftime('%s','now'), 0),
('https://adaway.org/hosts.txt', 1, strftime('%s','now'), 0),
('https://v.firebog.net/hosts/AdguardDNS.txt', 1, strftime('%s','now'), 0),
('https://v.firebog.net/hosts/Easyprivacy.txt', 1, strftime('%s','now'), 0);"
sudo pihole -g
```

Result: 295,090 domains pulled in. Blocking confirmed: `dig @10.0.0.67 doubleclick.net` → `0.0.0.0`.

**Always verify after headless install:**
```bash
sudo sqlite3 /etc/pihole/gravity.db "SELECT COUNT(*) FROM adlist; SELECT COUNT(*) FROM gravity"
```
Non-zero = good. 0/0 = blocking is dead.

**Pi-hole FTL query DB (pihole-FTL.db):**
```
sudo required to read — file owned by pihole:pihole
query_storage fields: id, timestamp, type, status, domain, client, forward, reply_type, reply_time, dnssec, list_id, ede
reply_type: 0=unknown, 1=IP, 2=NXDOMAIN, 3=NULL, 4=BLOCKED (0.0.0.0), 5=CNAME, 6=AAAA
status: 0=unknown, 1=OK, 2=blocked, 3=blocked-denylist, 4=blocked-regex, 5=allowed, 6=allowed-stale
type: 1=DNS query, 2=DNS reply, 6=AAAA reply, 7=PTR reply
```
Quick check: `sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT reply_type, COUNT(*) FROM query_storage GROUP BY reply_type;"`

### Pi-hole (installed 2026-05-07)
- Pi-hole v6.4.2 installed (Core v6.4.2, Web v6.5, FTL v6.6.1)
- Running on Pi 3 at 10.0.0.67 (wlan0, static via dhcpcd.conf)
- Dashboard: http://10.0.0.67/admin
- Upstream DNS: Cloudflare (1.1.1.1) — user selected during wizard
- Query logging: enabled
- Gravity domains: 295,090 (Steven Black + Adaway + Adguard DNS + Easyprivacy)
- Network: Evan manually set DNS on his PC to 10.0.0.67 to test (not yet set in router)
- Router: Xfinity gateway at 10.0.0.1 — Evan doesn't know admin password, couldn't set DNS there yet

### Static IP for Pi-hole (required before install)
The Pi had a dynamic DHCP lease on wlan0. Fixed before install by appending to `/etc/dhcpcd.conf`:
```
interface wlan0
static ip_address=10.0.0.67/24
static routers=10.0.0.1
static domain_name_servers=10.0.0.67 1.1.1.1 9.9.9.9
```
The Pi-hole installer pre-fills the static IP if it matches the current lease — confirmed working.

### Pi-hole installer key insight
**Cannot be run over SSH.** The installer requires a real TTY (/dev/tty) for its interactive prompts. Evan ran it from the Pi console directly. This is the correct approach.

### evan rename outcome
- evan deleted, Evan active at 10.0.0.67
- SSH key auth working (Evan's id_ed25519.pub installed)
- Passwordless sudo configured via /etc/sudoers.d/evan
- No passwords needed for any SSH/sudo operations

### VNC Setup (2026-05-07) — RealVNC (NOT tigervnc)

RealVNC was already installed (RealVNC Server 7.13.1). Do NOT install tigervnc on Raspberry Pi OS — RealVNC is already there and works.

```bash
# Check RealVNC is running
ss -tlnp | grep 5900

# Set VNC password
vncpasswd -virtual   # interactive, min 6 chars

# Start VNC server (Virtual Mode, headless)
vncserver-virtual :1 -geometry 1280x800 -depth 24

# Connect: 10.0.0.67:5900, password evan1717
```

**PITFALL:** RealVNC ARM does NOT support `-localhost no` flag. Using it causes "Unrecognized option: no" error. Always use `vncserver-virtual` (not `vncserver`) on Raspberry Pi OS.

### Conky Manager ARM Build (2026-05-07)

Conky Manager has no ARM build. Official `.deb` and `.run` are amd64 only. Built from source:

```bash
# conky-std from apt (conky-all has conflicts on ARM)
sudo apt-get install -y conky-std

# Build deps (may need dpkg --configure -a after lock interruption)
sudo dpkg --configure -a
sudo apt-get install -y valac libgtk-3-dev libgee-0.8-dev libjson-glib-dev

# Clone and build (fails at translation step, binary still compiles)
cd /tmp
git clone https://github.com/teejee2008/conky-manager.git
cd conky-manager
make

# Install manually (xgettext/msgfmt missing — skip translation)
sudo cp src/conky-manager /usr/bin/
sudo mkdir -p /usr/share/conky-manager/{icons,scripts,themepacks}
sudo cp -r icons/* /usr/share/conky-manager/icons/
sudo cp -r scripts/* /usr/share/conky-manager/scripts/
sudo cp -r themepacks /usr/share/conky-manager/

# Launch from VNC desktop menu or terminal
conky-manager
```

**dpkg lock fix:** If apt-get fails with "dpkg lock frontend", kill the stale process and run `sudo dpkg --configure -a`.

### DNS Troubleshooting — Devices Not Appearing in Pi-hole

**Symptom:** Device getting popups/ads, but its IP doesn't show in Pi-hole query log.

**Root cause:** Device is using a different DNS server (e.g., Comcast 75.75.75.75) — not Pi-hole. Pi-hole only sees traffic from devices pointed at it.

**Diagnostic — run on the device itself:**
```bash
# Check what DNS the device is actually using
resolvectl status | grep DNS
cat /etc/resolv.conf
```

**If DNS is wrong on the device:** Set it to Pi-hole (10.0.0.67) in the device's network settings, then disconnect/reconnect WiFi.

**Check Pi-hole's known clients:**
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT ip FROM client_by_id;"'
```

Only devices that appear here are using Pi-hole as DNS.

**MX Linux (10.0.0.64) — example from this session:**
- MX Linux laptop wasn't appearing in Pi-hole client list
- Cause: DNS was not set to 10.0.0.67 on that laptop — it was still using Comcast DNS
- Fix: Set DNS manually in MX Linux network settings to 10.0.0.67
- Pirate Bay ads coming through = same root cause, device isn't using Pi-hole DNS

### WiFi Issue
- 2.4GHz WiFi: works fine
- 5GHz WiFi: SSID not showing up in scan
- Likely cause: regulatory domain not set (country code)
- Fix: `sudo raspi-config` → Localization Options → WLAN Country → set country
- Or: `sudo raspi-config nonint do_wifi_country US`

## SSH Setup
- SSH enabled via boot partition: `sudo touch /mnt/boot/ssh` before first boot
- Pi connected via CAT5 ethernet cable for initial setup
- Evan's preference: SSH in from Linux machine rather than hook up keyboard/display

## Boot Partition Access
```bash
lsblk  # find SD card device (e.g., /dev/sdb)
sudo mount /dev/sdX1 /mnt/boot   # boot partition
sudo touch /mnt/boot/ssh         # enables SSH
sudo umount /mnt/boot
```

## After Boot — Finding Pi IP
```bash
arp -a | grep raspberry
# Or check router's connected devices page
```

## Default Pi Credentials (before change)
- Username: `pi` / `raspberry` or `evan` / `1717` (Pi Imager default)
