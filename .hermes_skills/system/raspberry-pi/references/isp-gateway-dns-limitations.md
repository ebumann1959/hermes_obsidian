# ISP Gateway DNS Limitations

## The Problem

Many ISP-provided combination gateway/routers (e.g., cablemodem+router combos) do not expose DNS configuration to the user. The DNS fields in the admin panel are **read-only status displays**, not editable inputs. This means you cannot set Pi-hole as the network-wide DNS server via router DHCP.

## Affected Gateways

- **Comcast Technicolor XB6 (CGM4140COM)** — DNS fields in XFINITY Network tab are read-only. WAN DNS shown: 75.75.75.75 / 75.75.76.76 (Comcast assigned), not editable.
- Most ISP-provided combination gateways from Comcast, Spectrum, AT&T, etc.

## Per-Device DNS Configuration

When router DNS cannot be changed, configure each device individually to use Pi-hole.

### Linux (KDE Plasma)
```
System Settings → Network → Connections → [WiFi/Ethernet] → IPv4/IPv6 → DNS
Clear existing → Add: 10.0.0.67, 1.1.1.1 → Apply
May need to reconnect WiFi for changes to take effect.
```

### iPhone / iOS
```
Settings → Wi-Fi → tap (i) next to network → Configure DNS → Manual
Clear existing → Add: 10.0.0.67, 1.1.1.1 → Save (top right)
```

### TCL Roku TV (tested: 75q750g, 2023 Roku OS)
```
Home → Settings → Network → Wireless → [your network] → Configure IP → DNS Server
Set: Manual → Primary: 10.0.0.67, Secondary: 1.1.1.1 → Apply/OK
Restart TV after applying.
```

### Android
```
Settings → Network & Internet → Wi-Fi → tap connected network → Advanced → DNS
Set: 10.0.0.67, 1.1.1.1
```

### macOS
```
System Settings → Wi-Fi → [network name] → Details → DNS
Remove existing → Add: 10.0.0.67, 1.1.1.1
```

## Diagnosing Which Devices Are NOT Using Pi-hole

If a device shows ads but isn't appearing in Pi-hole query log, check on the device:

```bash
# Check current DNS
resolvectl status | grep DNS
cat /etc/resolv.conf

# Test if Pi-hole is resolving a domain
dig +short thepiratebay.org
# If it returns a real IP (not 0.0.0.0), DNS is NOT pointing to Pi-hole
```

**The telltale sign:** A device not in Pi-hole's client list (`SELECT ip FROM client_by_id`) is not using Pi-hole as DNS. Only one device had ever hit Pi-hole in this session — the others were bypassing it.

## The Real Fix

Replace the ISP gateway with a **third-party router** that supports custom DNS in DHCP:
- UniFi Dream Machine (UDM, UDM-Pro)
- Eero (any model)
- TP-Link Omada
- Any router that runs OpenWRT/DD-WRT

Set the third-party router's DHCP DNS to Pi-hole's IP (10.0.0.67). Put the ISP gateway into bridge mode so it just passes traffic without doing NAT/routing.
