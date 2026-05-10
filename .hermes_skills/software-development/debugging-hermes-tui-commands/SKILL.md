---
name: debugging-hermes-tui-commands
description: "Debug Hermes TUI, gateway, and CLI commands. Covers log locations, gateway state, restart flows, and common failure modes."
version: 1.0.0
metadata:
  hermes:
    tags: [debugging, hermes, tui, gateway, cli]
---

# Debugging Hermes TUI Commands

## Log Locations

| Log | What it contains |
|-----|-----------------|
| `~/.hermes/logs/agent.log` | Full agent output — tool calls, responses, errors |
| `~/.hermes/logs/errors.log` | Exceptions only — start here for crashes |
| `~/.hermes/logs/gateway.log` | Discord/Telegram/WhatsApp gateway events |
| `/tmp/sr_runner.log` | show_runner output |
| `~/.hermes/interrupt_debug.log` | Interrupt/signal events |

```bash
# Tail errors live
tail -f ~/.hermes/logs/errors.log

# Last 50 lines of agent log
tail -50 ~/.hermes/logs/agent.log

# Search for a specific error
grep -i "traceback\|Error\|exception" ~/.hermes/logs/errors.log | tail -30
```

## Gateway State

```bash
# Check if gateway is running
cat ~/.hermes/gateway_state.json

# Check process list
cat ~/.hermes/processes.json

# Running processes
ps aux | grep hermes
```

## Restart Flows

```bash
# Restart hermes agent (TUI)
pkill -f "hermes" && sleep 2 && hermes

# Restart just the gateway
hermes gateway restart

# Full reset (clears session state)
hermes /reset
```

## Common Failures

### "Tool call failed silently"
Check `errors.log` — most silent failures leave a traceback there.

### "Gateway not responding"
```bash
cat ~/.hermes/gateway_state.json  # is it CONNECTED?
hermes gateway status
```

### "SSH tool hangs in gateway"
Pi ssh-agent must have key loaded:
```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa
```

### "state.db locked"
```bash
fuser ~/.hermes/state.db  # who holds the lock?
# If nothing: WAL needs checkpoint
sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

### MiniMax "finish_reason: content_filter"
Not a network error — model blocked the content. Rephrase the prompt or check `dialogue_engine.py` logs for the exact message that triggered it.
