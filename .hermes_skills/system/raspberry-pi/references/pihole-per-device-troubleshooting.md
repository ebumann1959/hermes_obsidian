# Pi-hole Per-Device DNS Troubleshooting

## Key Lesson from This Session

**Multiple devices may share the same WiFi network but have DIFFERENT DNS configs.** Pi-hole only sees devices that are actually pointed at it. A device not in Pi-hole's query log = that device is NOT using Pi-hole as DNS.

Symptoms of this:
- Popups still appearing on device X
- Device X doesn't appear in Pi-hole client list
- `dig @10.0.0.67 domain.com` works from Pi-hole itself, but device X is still hitting a different DNS

## Quick Diagnostic Commands

### From Pi-hole: check all clients ever seen
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT ip FROM client_by_id;"'
```

### From Pi-hole: query count per client
```bash
ssh Evan@<pi-ip> 'sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT c.ip, COUNT(*) FROM query_storage q JOIN client_by_id c ON q.client = c.id GROUP BY c.ip;"'
```

### From Linux device: check actual DNS in use
```bash
resolvectl status | grep DNS
cat /etc/resolv.conf
```

### From Linux device: test if Pi-hole is blocking
```bash
dig @10.0.0.67 doubleclick.net +short
# Should return 0.0.0.0 (blocked)
# Any other IP = not using Pi-hole
```

## Real Scenario (This Session)

- MX Linux laptop at 10.0.0.64: NOT in Pi-hole client list → DNS not set to Pi-hole
- Work laptop at 10.0.0.123: in Pi-hole, working fine
- Pirate Bay popup: from MX Linux (10.0.0.64), which was using Comcast DNS, not Pi-hole

## Action

1. Run `resolvectl status` on each device to find its actual DNS
2. Each device needs DNS set to 10.0.0.67 manually (no router DHCP on Comcast XB6)
3. After setting DNS, device must disconnect/reconnect WiFi for config to take
4. Verify with `dig @10.0.0.67` from that device's terminal
