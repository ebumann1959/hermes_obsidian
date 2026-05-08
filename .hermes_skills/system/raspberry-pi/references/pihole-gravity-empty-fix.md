# Pi-hole Gravity Database — Empty After Install

## The Problem

During headless/unattended Pi-hole installs, the gravity database (`/etc/pihole/gravity.db`) often comes up **empty** — `adlist` and `gravity` tables both show 0 rows. This means `pihole -g` has nothing to sync against, and blocking never works even though Pi-hole appears to be running.

## Symptoms

```bash
$ sudo sqlite3 /etc/pihole/gravity.db "SELECT COUNT(*) FROM adlist; SELECT COUNT(*) FROM gravity;"
0
0

$ sudo pihole status
  [✓] FTL is listening on port 53
  [✓] Pi-hole blocking is enabled
  [✗] Gravity database is not responding
```

Or in the web dashboard: **0 domains** on the blocklist, and no queries ever show as blocked.

## Root Cause

The Pi-hole installer skips blocklist population when run in a non-interactive (headless/SSH) context. The `gravity` database is created but the `adlist` table (which stores blocklist URLs) is never populated. Running `pihole -g` without entries in `adlist` results in an empty gravity.

## Fix — Populate adlist Table Manually, Then Run Gravity

```bash
# Step 1: Insert blocklist URLs into adlist table
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/gravity.db "INSERT INTO adlist (address, enabled, date_added, type) VALUES
('\''https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts'\'', 1, strftime('\''%s'\'','\''now'\'''\''''), 0),
('\''https://adaway.org/hosts.txt'\'', 1, strftime('\''%s'\'','\''now'\'''\''''), 0),
('\''https://v.firebog.net/hosts/AdguardDNS.txt'\'', 1, strftime('\''%s'\'','\''now'\'''\''''), 0),
('\''https://v.firebog.net/hosts/Easyprivacy.txt'\'', 1, strftime('\''%s'\'','\''now'\'''\''''), 0);"'

# Step 2: Run gravity to pull in all domains
ssh Evan@<pi-ip> 'sudo pihole -g'

# Expected output:
#   [✓] Neutrino emissions analyzed...
#   [✓] Building tree...
#   [✓] Swapping trees...
#   [✓] Sorted 295090 domains (256359 unique)
```

## Verify Blocking Works

```bash
# Blocked domain should return 0.0.0.0
dig @<pi-ip> doubleclick.net +short
# Expected: 0.0.0.0

# Non-blocked domain should return real IP
dig @<pi-ip> google.com +short
# Expected: a real IP like 142.251.46.142
```

## Blocklist Sources Used (Tested in This Session)

| Source | Domains | URL |
|--------|---------|-----|
| Steven Black hosts | ~80,799 | https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts |
| Adaway | ~6,540 | https://adaway.org/hosts.txt |
| Adguard DNS | ~165,136 | https://v.firebog.net/hosts/AdguardDNS.txt |
| Easyprivacy | ~42,615 | https://v.firebog.net/hosts/Easyprivacy.txt |
| **Total** | **~295,090** | |
| **Unique** | **~256,359** | |

## Checking Query Log (FTL Database)

```bash
# Total queries logged
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT COUNT(*) FROM query_storage;"'

# Queries by client
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT c.ip, COUNT(*) FROM query_storage q JOIN client_by_id c ON q.client = c.id GROUP BY q.client;"'

# Top domains
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT d.domain, COUNT(*) FROM query_storage q JOIN domain_by_id d ON q.domain = d.id GROUP BY q.domain ORDER BY COUNT(*) DESC LIMIT 10;"'

# Check if any domains are being blocked (reply_type=0 means blocked by gravity)
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT reply_type, COUNT(*) FROM query_storage GROUP BY reply_type;"'
```

reply_type codes: 0=UNKNOWN, 1=IPv4, 2=IPv6, 3=NULL, 4=NXDOMAIN, 5=NODATA, 6=REFUSED, 7=OTHER
