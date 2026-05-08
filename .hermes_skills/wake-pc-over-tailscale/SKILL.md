---
name: wake-pc-over-tailscale
category: networking
description: Wake a sleeping Windows PC (MX25Rig) remotely by sending a WoL magic packet over Tailscale VPN from the Pi, bypassing the router's broadcast domain limitation.
---

# Wake PC Over Tailscale

Wake MX25Rig (10.0.0.91) from the Pi when it's in sleep/hibernate, even across subnets, using Tailscale VPN as the transport layer.

## Why Tailscale (not router)

The xB6 router (CGM4140COM) has a broadcast domain boundary between WiFi and ethernet — WoL magic packets from Pi (WiFi) never reach PC (ethernet). The router admin panel has no WoL forwarding feature.

Tailscale VPN creates a virtual ethernet interface on both machines. When Pi sends a magic packet to PC's Tailscale IP (`100.66.220.82`), it travels over the VPN tunnel and arrives at the PC's Tailscale interface, which forwards it to the ethernet port where WoL is listening.

## Prerequisites

- Tailscale installed on both Pi and PC (PC already at `100.66.220.82`)
- WoL enabled in PC BIOS/UEFI
- WoL enabled in OS: `ethtool -s eth0 wol g` (confirmed working)
- WoL persistent: `ethtool -s eth0 wol g` added to `/etc/rc.local` on PC

## WoL Command (from Pi)

```python
python3 -c "
import socket
mac = bytes.fromhex('a036bca77f53'.replace(':',''))
packet = b'\\xff'*6 + mac*16
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(packet, ('100.66.220.82', 9))
"
```

Or via CLI:
```bash
wakeonlan -i 100.66.220.82 a0:36:bc:a7:7f:53
```

## PC Details

| | |
|--|--|
| LAN IP | 10.0.0.91 |
| Tailscale IP | 100.66.220.82 |
| MAC | a0:36:bc:a7:7f:53 |
| User | Evan |
| WoL port | 9 (standard) |
| OS | MX Linux (systemd) |

## Verify PC Is Asleep

```bash
ping -c 1 10.0.0.91   # should timeout if asleep
ping -c 1 100.66.220.82  # same over Tailscale
```

## After Waking — SSH from Pi

```bash
ssh Evan@10.0.0.91
```

Key auth is configured — no password needed from Pi.

## Troubleshooting

- **Magic packet not arriving**: Check PC's Tailscale is connected (`tailscale status` on PC)
- **PC wakes but doesn't boot**: WoL may be disabled in BIOS — enter BIOS setup and find "Wake on LAN" / "Power by PCI-E" option
- **Ping works but WoL doesn't**: Some PCs require WoL on Magic Packet specifically, not just general network wake
