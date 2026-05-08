---
name: session-snapshot-recovery
description: Recover full context from pre-compaction session snapshots stored in the vault. Automatic recovery at session start — no manual trigger needed.
---

# Session Snapshot Recovery

**Architecture: token-based watchdog as Hermes subprocess**

Watchdog is spawned as a subprocess of Hermes at session start, killed at session end. No systemd, no cron, no idle daemon.

**Trigger:** Estimated tokens > 80k (compaction fires ~100k). Token estimate: `chars / 4`.

**Pre-compaction flow:**
1. Tokens cross 80k → snapshot saved to `~/.hermes/session_snapshots/` + vault `sessions/`
2. PRE-COMPACTION marker written into session JSON metadata
3. Pointer file written: `~/.hermes/last_session.json` → `{session_id, snapshot_path, snapshot_ts}`
4. Compaction fires naturally at ~100k, session continues with same session ID

**Recovery (automatic at session start):**
1. `check_recovery()` reads `last_session.json` → finds previous session ID + snapshot path
2. Reads previous session file → checks for COMPACTION marker
3. If COMPACTION marker found → snapshot exists → restore: load snapshot's messages into context
4. If no COMPACTION marker → previous session ended cleanly → skip restore, start fresh

**Key invariant (verified):** Session ID is stable across compaction — same ID before and after. Recovery is deterministic.

---

## When recovery fires

Recovery is automatic at session start. The `check_recovery()` function in `session_watchdog.py` handles the logic — you don't need to call it manually.

**Conditions for restore:**
- Previous session file has a COMPACTION marker (session was interrupted)
- Snapshot exists for that session ID

**Conditions to skip restore:**
- No `last_session.json` (fresh start)
- Previous session has no COMPACTION marker (closed cleanly)
- Snapshot file missing and not recoverable from vault

---

## Manual recovery check

```python
import sys
sys.path.insert(0, '/home/Evan/.hermes/scripts')
from session_watchdog import check_recovery, SNAPSHOT_DIR

should_restore, snap_path, prev_id = check_recovery()
print(f"should_restore={should_restore}, prev_session={prev_id}")
print(f"Available snapshots: {sorted(SNAPSHOT_DIR.glob('pre_compact_*.json'))[-3:]}")
```

---

## Read a specific snapshot

```bash
cat ~/.hermes/session_snapshots/pre_compact_<session_id>_<timestamp>.json | python3 -c "
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

---

## What to restore

After compaction, recover from the snapshot:

1. **Message history** — full conversation up to the PRE-COMPACTION marker
2. **System prompt** — current personality, memory, injected context
3. **Tool call history** — what was tried, what succeeded/failed
4. **Session decisions** — what was chosen, what was rejected, what's next

Then write a SESSION_LOG entry capturing what was lost so the record is complete.

---

## Vault copies

Snapshots are mirrored to `/mnt/nvme/obsidian-vault/sessions/` — available to PC via git sync.

**PC vault path:** `/mnt/Data/obsidian_vault/sessions/` (or equivalent on that machine)

Vault sessions dir is NOT git-tracked — local redundancy mirror only.

---

## Implementation

**Script:** `~/.hermes/scripts/session_watchdog.py`

**Key functions:**
- `check_recovery()` — reads pointer file, returns `(should_restore, snapshot_path, prev_session_id)`
- `save_snapshot()` — copies session file to local + vault
- `write_pre_compaction_marker()` — writes marker into session JSON
- `has_compaction_marker()` — checks if previous session was interrupted

**Pointer file:** `~/.hermes/last_session.json`
```json
{
  "session_id": "20260507_184031_992e34",
  "snapshot_path": "/home/Evan/.hermes/session_snapshots/pre_compact_20260507_184031_992e34_185100.json",
  "snapshot_ts": "2026-05-07T18:51:00"
}
```

**Snapshot naming:** `pre_compact_<session_id>_<timestamp>.json`
**Retention:** Last 50 local snapshots, 24h stale prune. Vault copies persist indefinitely.

---

## Limitations

- Snapshots are raw JSON — use selective extraction, don't load the whole thing into context verbatim
- Snapshot is only as fresh as the last watchdog check (every 180s) — there is a small gap between snapshot and actual compaction
- Vault sessions dir is NOT git-tracked — cross-agent continuity relies on SESSION_LOG for long-term history
