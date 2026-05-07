# System Snapshot — Pi (Shadys-Gamblin-Corner)

**Updated:** 2026-04-20

## Host
| Field | Value |
|-------|-------|
| hostname | Shadys-Gamblin-Corner |
| OS | Debian GNU/Linux 13 (trixie) |
| kernel | 6.12.75+rpt-rpi-2712 |
| arch | aarch64 (RPi 5) |
| user | shady |
| Tailscale | 100.104.189.48 |

## Network
| Interface | State | Address |
|-----------|-------|---------|
| lo | UP | 127.0.0.1/8 |
| wlan0 | UP | 10.0.0.9/24 |
| tailscale0 | UP | 100.104.189.48/32 |
| eth0 | DOWN | — |

## Listening Ports
| Port | Service |
|------|---------|
| 22 | ssh |
| 5900 | vnc |
| 111 | rpc |
| 631 | cups |
| 43737 | mDNS |
| 41641 | tailscale |

## Hermes
| Component | Path | State |
|-----------|------|-------|
| agent venv | /home/shady/.hermes/hermes-agent/venv/bin/python3 | running |
| gateway | hermes_cli/main.py gateway run | startup_failed (discord) |
| conky | hermes_runners.conkyrc + 3 others | running |

## Paths
| Key | Path |
|-----|------|
| hermes_root | /home/shady/.hermes |
| persona_runners | /home/shady/.hermes/persona-runners |
| show_runner | /home/shady/.hermes/show_runner/ |
| context | /home/shady/.hermes/context |
| conky_scripts | /home/shady/.conky |
