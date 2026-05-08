# Pi-hole FTL Database Query Reference

Pi-hole v6+ uses FTL (FTLv6) with SQLite databases in `/etc/pihole/`.

## Key Tables

- `/etc/pihole/pihole-FTL.db` — query log (query_storage, domain_by_id, client_by_id, forward_by_id)
- `/etc/pihole/gravity.db` — blocklist domains (gravity table, adlist table)

## Common Queries

### Total queries and blocked counts
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT COUNT(*) FROM query_storage;"'
```

### Top domains by query count
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT d.domain, COUNT(*) FROM query_storage q JOIN domain_by_id d ON q.domain = d.id GROUP BY q.domain ORDER BY COUNT(*) DESC LIMIT 20;"'
```

### Top clients by query count
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT c.ip, COUNT(*) FROM query_storage q JOIN client_by_id c ON q.client = c.id GROUP BY q.client;"'
```

### Recent queries from a specific client (e.g., 10.0.0.123)
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT d.domain, q.reply_type, q.status FROM query_storage q JOIN domain_by_id d ON q.domain = d.id WHERE q.client = (SELECT id FROM client_by_id WHERE ip = '\''10.0.0.123'\'') ORDER BY q.id DESC LIMIT 30;"'
```

### Domain list count in gravity
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/gravity.db "SELECT COUNT(*) FROM gravity;"'
```

### Adlist sources
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/gravity.db "SELECT address, enabled FROM adlist;"'
```

## Reply Type Codes (queries.reply_type) / Status Codes (queries.status) — FTLv6+

**Pi-hole v6 / FTLv6 note:** The old `query_storage` table is deprecated. All queries go to `queries` table. Status `3` = blocked (gravity match). The dashboard and `queries` table are the authoritative source.

### Status Codes (queries.status)

| Code | Meaning |
|------|---------|
| `0`  | Unknown |
| `1`  | Unknown |
| `2`  | OK (allowed, forwarded upstream) |
| `3`  | Blocked (gravity blocklist match — Pi-hole returned 0.0.0.0) |
| `4`  | BOGUS (dnsmasq marked reply bogus) |
| `5`  | DNSSEC validated but insecure |
| `6`  | Disabled (Pi-hole DNS disabled for client) |
| `7`  | HAIRPIN (hairpin loopback query) |
| `8`  | HOSTFILE (blocked via /etc/hosts) |
| `16` | DNSSEC key query (allowed) |
| `17` | DS query (allowed) |

### Reply Type Codes (queries.reply_type)

| Code | Meaning |
|------|---------|
| `1`  | Unknown |
| `4`  | IP (A/AAAA returned — real IP or 0.0.0.0 for blocked) |
| `5`  | NODATA |
| `6`  | NXDOMAIN |
| `7`  | PTR reply |

## Debugging "popups still showing" / "device not appearing in Pi-hole"

**Key insight:** If a device isn't in Pi-hole's client list, it's NOT using Pi-hole as DNS. Pi-hole can only block what it sees.

**Step 1 — Confirm the device is hitting Pi-hole:**
```bash
# On the device itself, check its DNS
resolvectl status | grep DNS
cat /etc/resolv.conf
```
If it shows Comcast DNS (75.75.75.75) or anything other than 10.0.0.67, the device is bypassing Pi-hole.

**Step 2 — Check what Pi-hole actually sees:**
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT ip FROM client_by_id;"'
```
Only IPs in this list are routing through Pi-hole DNS.

**Step 3 — Add device DNS to Pi-hole:**
- Linux (NetworkManager): Settings → Network → Connection → IPv4/IPv6 → DNS → set 10.0.0.67,1.1.1.1
- iOS: Wi-Fi → (i) → Configure DNS → Manual → add 10.0.0.67
- TCL Roku TV: Home → Settings → Network → Wireless → IP Config → DNS → Manual → 10.0.0.67
- Reconnect the network after changing DNS

**Step 4 — Verify blocking:**
```bash
dig @10.0.0.67 doubleclick.net +short
# Should return 0.0.0.0
```

**If popup domain is still getting through after Pi-hole is confirmed working:**
The ad domain is not yet in the blocklist. Add it:
```bash
ssh Evan@<pi-ip> 'sudo pihole -b example-bad-domain.com'
```

1. Identify client IP from `client_by_id` query
2. Get recent domains that client queried with `reply_type` and `status`
3. If domains have `reply_type=4` (real IP returned) and `status=2` (allowed) — domain is NOT in blocklist
4. If a popup domain is returning a real IP (not 0.0.0.0), add it to the blocklist manually:
   ```bash
   ssh Evan@<pi-ip> 'sudo pihole -b example-bad-domain.com'
   ```

## Quick Health Check
```bash
ssh Evan@<pi-ip> 'sudo pihole status && echo "---Gravity domains:---" && sudo sqlite3 /etc/pihole/gravity.db "SELECT COUNT(*) FROM gravity;" && echo "---Recent blocked:---" && sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT d.domain FROM query_storage q JOIN domain_by_id d ON q.domain = d.id WHERE q.status=0 ORDER BY q.id DESC LIMIT 5;"'
```