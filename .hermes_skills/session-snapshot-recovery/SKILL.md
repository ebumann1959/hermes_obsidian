---
name: session-snapshot-recovery
description: Recover full context from pre-compaction session snapshots stored in the vault. Use after context compaction to restore what was lost, or to search historical session state.
---

# Session Snapshot Recovery

Snapshots of session context (full JSON) are captured by the session watchdog before every compaction and stored at:
- Local: `~/.hermes/session_snapshots/`
- Vault: `/mnt/nvme/obsidian-vault/sessions/`

The watchdog also maintains `~/.hermes/session_snapshots/snapshot_index.json` — a list of all captured snapshots with timestamps and MD5 hashes.

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

## Limitations

- Snapshots are raw JSON session files — large and unfiltered. Use selective extraction.
- The watchdog must be running to capture pre-compaction state. If it wasn't running, you only have what the compaction summary preserved.
- Snapshot retention: last 50 locally, copies persist in vault indefinitely.
