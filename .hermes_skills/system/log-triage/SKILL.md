---
name: log-triage
description: "Efficiently triage Hermes agent logs, errors.log, and show_runner logs without drowning in output. Windows around errors, filters noise, extracts signal."
version: 1.0.0
metadata:
  hermes:
    tags: [logging, debugging, triage, errors, pi, system]
---

# Log Triage

Never dump a full log. Window around the error, then read context.

## Log Locations

| Log | Size limit before triage | Content |
|-----|--------------------------|---------|
| `~/.hermes/logs/errors.log` | Always triage | Exceptions only |
| `~/.hermes/logs/agent.log` | >10k lines → triage | Full agent output |
| `~/.hermes/logs/gateway.log` | >5k lines → triage | Gateway events |
| `/tmp/sr_runner.log` | Always triage | show_runner output |
| `~/.hermes/interrupt_debug.log` | <500 lines, read all | Signal events |

## Quick Error Scan

```bash
# All errors in the last session
grep -n "Traceback\|Error\|Exception\|CRITICAL" ~/.hermes/logs/errors.log | tail -20

# With 5 lines of context around each match
grep -n -A5 "Traceback" ~/.hermes/logs/errors.log | tail -60

# Errors from the last hour
grep -n "$(date +'%Y-%m-%d %H:')" ~/.hermes/logs/errors.log | grep -i "error\|exception"
```

## Windowed Log Reading

For large agent.log — read 50 lines around a known timestamp:

```bash
# Find line number of a timestamp or error
grep -n "2025-05-09 18:4" ~/.hermes/logs/agent.log | head -5

# Read 25 lines before and after that line number
sed -n '1234,1284p' ~/.hermes/logs/agent.log  # adjust line numbers
```

## show_runner Log

```bash
# Last 30 lines (most common starting point)
tail -30 /tmp/sr_runner.log

# Find content_filter blocks (MiniMax censored)
grep -n "content_filter\|finish_reason" /tmp/sr_runner.log | tail -10

# Find WebSocket events
grep -n "websocket\|ws_bridge\|connected\|disconnected" /tmp/sr_runner.log | tail -20

# Find empty response events (MiniMax returned nothing)
grep -n "empty\|retry\|None" /tmp/sr_runner.log | tail -10
```

## Gateway Log

```bash
# Discord/Telegram events
grep -n "discord\|telegram\|message_received\|command" ~/.hermes/logs/gateway.log | tail -20

# Connection issues
grep -n "reconnect\|disconnect\|timeout\|error" ~/.hermes/logs/gateway.log | tail -10
```

## Log Rotation (manual)

If a log is >50MB, rotate it:

```bash
# Rotate (keep last 10k lines, archive the rest)
tail -10000 ~/.hermes/logs/agent.log > /tmp/agent.log.tmp
mv ~/.hermes/logs/agent.log ~/.hermes/logs/agent.log.$(date +%Y%m%d)
mv /tmp/agent.log.tmp ~/.hermes/logs/agent.log
gzip ~/.hermes/logs/agent.log.$(date +%Y%m%d)

# Check disk usage freed
ls -lh ~/.hermes/logs/
```

## MiniMax-Specific Noise to Ignore

These are NOT errors — filter them out when triaging:
- `"finish_reason": "stop"` — normal completion
- `[INFO] gateway heartbeat` — normal ping
- `session checkpoint` — normal snapshot
- `wal_checkpoint` — normal DB maintenance
