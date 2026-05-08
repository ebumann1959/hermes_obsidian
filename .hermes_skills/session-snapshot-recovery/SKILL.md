---
name: session-snapshot-recovery
description: Recover full context from pre-compaction session snapshots stored in the vault. Use after context compaction to restore what was lost, or to search historical session state.
---

# Session Snapshot Recovery

Two-layer capture system ensures no compaction is missed, even during long idle periods:

**Layer 1 — Watchdog daemon** (`session-watchdog.service`):
- Runs during active sessions, uses inotify to detect compaction the instant it happens
- Captures pre-compaction snapshot to `~/.hermes/session_snapshots/` + vault
- Self-destructs after 10 min idle (systemd auto-restarts on next session activity)

**Layer 2 — Cron fallback** (`session_snapshot_cron.py`, `*/3 * * * *`):
- Runs every 3 minutes, even when no session is active
- Scans sessions modified in last 30 min for new compaction markers
- Catches compactions that fired while watchdog was idle
- Prevents context loss from idle-time compactions

**Archive locations:**
- Local: `~/.hermes/session_snapshots/` (indexed, 50 max retained)
- Vault mirror: `/mnt/nvme/obsidian-vault/sessions/` (non-git, Pi-only)

## When to use

1. **After compaction** — context window just compacted and you want to restore the full picture of what was lost
2. **Session start** — check if there are snapshots from recent sessions that weren't captured in SESSION_LOG
3. **Cross-session investigation** — need to look at a specific past session's full state

## Index (list available snapshots)

```bash
cat ~/.hermes/session_snapshots/snapshot_index.json
```

## Read a specific snapshot

```bash
cat ~/.hermes/session_snapshots/pre_compact_session_YYYYMMDD_HHMMSS_*.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
msgs = d.get('messages', [])
print(f'Session: {d.get(\"session_id\")}')
print(f'Messages: {len(msgs)}')
for m in msgs[-10:]:
    role = m.get('role')
    content = str(m.get('content', ''))[:200]
    print(f'  [{role}] {content}...')
"
```

## Reconstruct context for current session

The most powerful use: grab the most recent snapshot and use its `system_prompt` + message history to restore state:

```python
import json
from pathlib import Path

snapshots = sorted(Path.home().glob(".hermes/session_snapshots/pre_compact_*.json"))
if snapshots:
    latest = snapshots[-1]
    d = json.loads(latest.read_text())
    # Print system prompt (personality + memory)
    print(d.get("system_prompt", "")[:2000])
    # Print last N messages
    for m in d.get("messages", [])[-20:]:
        print(f'\\n=== [{m["role"]}] ===')
        print(str(m.get("content", ""))[:500])
```

## Vault copies

Snapshots are also pushed to `/mnt/nvme/obsidian-vault/sessions/` so they're available to the PC agent via git sync. PC looks at `C:\Users\...\obsidian_vault\sessions\` (or the equivalent path on that machine).

## What to restore after compaction

After compaction, you lose the raw conversation history. What you can recover from a snapshot:

1. **System prompt** — current personality, memory, and injected context
2. **Message history** — full conversation up to compaction
3. **Tool call history** — what was tried, what succeeded/failed
4. **Session variables** — any in-session state

**Workflow after compaction:**
1. `search_vault("session snapshots")` or read the index
2. Load the most recent snapshot
3. Extract the key context that was lost — decisions made, files being edited, etc.
4. Write a detailed entry to SESSION_LOG capturing what was lost and what needs to continue
5. Inject key facts into your response to continue the session coherently

## Implementation

The watchdog is implemented as two files:
- `~/.hermes/scripts/session_watchdog.py` — the Python watchdog (also in vault at `.hermes_skills/session-snapshot-recovery/scripts/session_watchdog.py`)
- `~/.config/systemd/user/session-watchdog.service` — systemd unit (also in vault)

**Install on a new machine:**
```bash
cp .hermes_skills/session-snapshot-recovery/scripts/session_watchdog.py ~/.hermes/scripts/
cp .hermes_skills/session-snapshot-recovery/scripts/session-watchdog.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now session-watchdog
```

**Pitfalls discovered during build:**
- systemd `ExecStart` needs the **absolute path** to python3 — `python3` alone won't resolve. Use `/usr/bin/python3`.
- `inotifywait` can emit events with no filename (e.g. `ISDIR` or overflow events). The parse loop must guard against `split()` returning fewer than 2 parts.
- The vault path in the watchdog script was `Path.home() / "mnt" / "nvme" / ...` which resolves to `$HOME/mnt/nvme/...` — wrong. The actual vault is at `/mnt/nvme/obsidian-vault/`, not `$HOME/mnt/...`. Hardcode `/mnt/nvme/obsidian-vault/` as an absolute path.

## Limitations

- Snapshots are raw JSON session files — large and unfiltered. Use selective extraction.
- The watchdog must be running to capture pre-compaction state. If it wasn't running, you only have what the compaction summary preserved.
- Snapshot retention: last 50 locally, copies persist in vault indefinitely.
