---
name: tailscale-universal-vpn
category: networking
description: Set up Tailscale as a relay VPN on a Pi (or any Linux machine) behind NAT — no router port forwarding or admin access needed. Use instead of WireGuard/PiVPN when remote router config is unavailable.
---

# Tailscale VPN Setup (No Router Port Forwarding Required)

## When to Use
- Pi/Linux machine sits behind a NAT router you can't configure
- No port forwarding available on the router
- WireGuard/PiVPN would require opening ports on the router (which you can't do remotely)
- User is SSH'd into the Pi and needs LAN access from outside

## Why Tailscale Instead of WireGuard
- Tailscale uses DERP relay servers — works through NAT without port forwarding
- No router admin access needed
- Installed on this Pi already: `tailscale` command available
- Free tier: up to 20 devices, 1 subnet relay

## Setup Steps

### 1. Authenticate the Pi to Tailscale
```bash
tailscale up --accept-routes
```
This will print a URL. The user needs to open it on their phone/browser to authenticate.

### 2. Verify the connection
```bash
tailscale status
```

### 3. Enable subnet relay (so phone becomes part of LAN)
```bash
tailscale up --accept-routes --advertise-routes=10.0.0.0/24
```
Note: The user needs to approve this subnet in the Tailscale admin console (tailscale.com/admin/machines).

### 4. Install Tailscale on phone
- iOS/Android: Install "Tailscale" app from App Store/Play Store
- Log in with same account
- Phone will appear as a node in the tailnet

### 5. Verify LAN access from phone
Once connected to Tailscale, the phone can reach:
- Router admin: `http://10.0.0.1`
- PC: `10.0.0.91`
- Pi: `10.0.0.9`

## Key Differences from WireGuard
| | Tailscale | WireGuard/PiVPN |
|---|---|---|
| Port forwarding | Not needed | Required |
| Router admin | Not needed | Required |
| Setup complexity | Low | Medium |
| Works behind CGNAT | Yes | No (without relay) |
| relay server | Tailscale's DERP | None (P2P) |

## Verification Commands
```bash
tailscale status        # show connected nodes
tailscale ip           # show this node's Tailscale IP
tailscale logout       # disconnect
```

## Gotchas
- Subnet relay requires approval in Tailscale admin console (free tier allows this)
- First `tailscale up` produces auth URL — user must complete auth
- If phone is on mobile data (not WiFi), Tailscale still works via its relay

## WoL over Tailscale — Wake PC Remotely

Wake MX25Rig (the PC) remotely when it's asleep, using Wake-on-LAN sent over the Tailscale VPN tunnel.

### PC Identity

| Field | Value |
|-------|-------|
| PC LAN IP | `10.0.0.91` |
| PC Tailscale IP | `100.66.220.82` |
| PC MAC | `a0:36:bc:a7:7f:53` |
| WoL port | `9` (UDP) |

### Pre-flight Check

From the Pi, verify PC is asleep (unreachable on both IPs):
```bash
ping -c 2 100.66.220.82  # should fail
ping -c 2 10.0.0.91      # should fail
```

### Wake Command

Run from the Pi:
```bash
python3 -c "
import socket
mac = bytes.fromhex('a036bca77f53'.replace(':',''))
packet = b'\xff'*6 + mac*16
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(packet, ('100.66.220.82', 9))
print('WoL sent to 100.66.220.82:9')
s.close()
"
```

### Confirm Wake

Wait ~10 seconds, then:
```bash
ping -c 3 100.66.220.82
```
Once responding (2-5ms latency), SSH in:
```bash
ssh Evan@100.66.220.82
# or
ssh Evan@10.0.0.91
```

### Persistent WoL

WoL is set via `/etc/rc.local` on the PC:
```
/usr/sbin/ethtool -s eth0 wol g
```

### Wake Methods (in order of reliability)

1. **LAN broadcast** (most reliable): `python3 -c "import socket; mac=bytes.fromhex('a036bca77f53'.replace(':','')); packet=b'\xff'*6+mac*16; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1); s.sendto(packet,('10.0.0.255',9)); s.close()"`
2. **Tailscale-directed** (sometimes fails): WoL to `100.66.220.82:9` — do NOT rely on this alone

**2026-04-22**: Tailscale-directed WoL failed; LAN broadcast to `10.0.0.255` succeeded. Always try LAN broadcast first if Tailscale WoL doesn't wake the PC after 45s.

### Troubleshooting

- **WoL fails**: PC may need power cycle for NIC to re-arm WoL after AC loss
- **Tailscale unreachable**: Check PC's Tailscale daemon is running (`ssh Evan@10.0.0.91 'pgrep -a tailscaled'`)
- **SSH fails after wake**: Wait 15s for OS to fully boot; check `ping 100.66.220.82`
- **SSH host key error on Tailscale IP**: Use LAN IP `10.0.0.91` instead — Tailscale SSH host key verification is unreliable from Pi

## xB6 Router WoL Note
Xfinity XB6 (CGM4140COM) has a `/wol` endpoint that returns 200 — it exists but requires router admin login. Defaultcreds (`admin`/`password`) don't work. If router admin credentials are obtained, WoL can be sent from the router's LAN interface, which solves the broadcast-domain problem. Relevant URLs: `/wol`, `/tools`, `/lan` all return 200 when accessed from LAN.
