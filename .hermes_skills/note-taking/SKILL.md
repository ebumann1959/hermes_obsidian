---
name: session-journaling
description: Append detailed session summaries to Obsidian vault SESSION_LOG.md and update PROJECT_STATE.md. Designed for cross-context-compaction continuity — reads like a complete lab notebook, not just a summary.
---

# Session Journaling

Vault: `/mnt/nvme/obsidian-vault/`

## Files
- `SESSION_LOG.md` — chronological session summaries (append-only, newest at bottom)
- `PROJECT_STATE.md` — current project status, updated on change

---

## Start-of-session ritual (MANDATORY)

### Step 1 — Launch watchdog (background subprocess)

Start the watchdog as a background subprocess of this session:

```bash
nohup python3 /home/Evan/.hermes/scripts/session_watchdog.py >> /home/Evan/.hermes/logs/watchdog.log 2>&1 &
echo "Watchdog PID: $!"
```

The watchdog stays alive for this session's lifetime. If Hermes restarts (new session ID detected), watchdog exits gracefully.

### Step 2 — Recovery check (before reading SESSION_LOG)

Check if the previous session was interrupted by compaction:

```python
python3 -c "
import json, pathlib, sys
# Run recovery check
sys.path.insert(0, '/home/Evan/.hermes/scripts')
from session_watchdog import check_recovery, SNAPSHOT_DIR
should_restore, snap_path, prev_id = check_recovery()
if should_restore:
    print(f'RESTORE: prev_session={prev_id}, snapshot={snap_path}')
    snap = json.loads(pathlib.Path(snap_path).read_text()) if snap_path else None
    print(f'Session had {len(snap[\"messages\"])} messages before compaction')
else:
    print('NO_RESTORE: previous session ended cleanly')
"
```

- **RESTORE returned:** Load the snapshot's messages into context — the previous session was interrupted. Say "Resuming from previous session" in the opening response.
- **NO_RESTORE returned:** Previous session ended cleanly, start fresh.

### Step 3 — Vault sync

```bash
bash ~/sync-vault.sh pull
```

### Step 4 — Read context

```bash
tail -n 150 /mnt/nvme/obsidian-vault/SESSION_LOG.md
cat /mnt/nvme/obsidian-vault/PROJECT_STATE.md
```

Reference them in opening response — acknowledge what's in flight, what was blocked, where we left off.

## End-of-session ritual (MANDATORY)

Before session ends, push vault changes:
```bash
bash ~/sync-vault.sh
```
This commits and pushes all vault changes made during this session to GitHub, so the other agent sees them next time.

---

## When to write

Write at these moments, not just end of session:

1. **After every context compaction** — when I notice older turns are gone, capture what was lost
2. **After any significant decision** — what we chose, what we rejected, and why
3. **After discarded options** — what didn't work, why it was abandoned, what idea from it survived
4. **When user corrects me** — note what I got wrong and what the right understanding is
5. **End of session** — full summary if no other trigger fired

---

**Vault paths (agent-specific local path — sync-vault.sh handles the right path per machine):**
- Pi: `/mnt/nvme/obsidian-vault/`
- PC: `/mnt/Data/obsidian_vault/`

Both agents pull from GitHub at session start (`bash ~/sync-vault.sh pull`) — local vault may have updates from the other agent.

**Detail Standard — Lab Notebook, Not Summary**

Write like a lab notebook, not a commit message.

**Minimum per entry:**
- What we did
- Why we did it that way
- What was rejected and why
- What the next action is
- Any convention, path, or fact discovered that isn't in memory

**Good example:**
```markdown
## 2026-04-20 15:30 — Scene 7 Beat Rhythm Fix

**What:** Revised beat timing in scene 7. Becky's bot was responding before Richard finished his line.

**Why:** Original beat spacing was 2s pause between beats — too tight when combined with dialogue overlap in the recorded audio. Made exchanges feel rushed.

**Rejected:** Tried 3s first — felt too slow, killed momentum. Tried variable spacing based on line length — added too much latency for short exchanges.

**Decided:** 2.5s base with 0.5s per exclamation point. Feels natural in testing.

**Next:** Test with full cast on scene 8. Becky flagged that morgan's response timing might have same issue — check scene 8 before tomorrow.

**Discovery:** Audio file sample rate (44.1k vs 48k) affects how BeatScheduler interprets timing constants. Need to normalise all audio to 44.1k before import — noted in SHOW_RUNNER/audio_pipeline.md.
```

**Bad example:**
```markdown
Fixed beat timing issue.
## Maintenance

A ChromaDB index of all SESSION_LOG entries is maintained at `/mnt/nvme/chromadb/`.
Use the `search_vault` tool to retrieve relevant past context by topic — not just recency.

**Searching the vault:**
- At session start: `grep` SESSION_LOG.md directly for topics relevant to this session
- When the user references past work: `grep -i "<keyword>" /mnt/nvme/obsidian-vault/SESSION_LOG.md`
- When you need to check if a decision was already made or a path/convention
- ChromaDB index at `/mnt/nvme/chromadb/` was planned but not implemented — do not attempt to use `search_vault` as a tool; it does not exist

**Pre-compaction save (RESOLVED — token-based watchdog as subprocess):**

Watchdog (`session_watchdog.py`) is spawned as a subprocess of Hermes and only runs during active sessions. No systemd, no cron.

**Trigger:** Estimated tokens > 80k (compaction fires ~100k). Token estimate: `chars / 4`.

**Pre-compaction flow:**
1. Tokens cross 80k threshold → snapshot saved to `~/.hermes/session_snapshots/` + vault `sessions/`
2. PRE-COMPACTION marker written into session JSON metadata
3. Pointer file written: `~/.hermes/last_session.json` → `{session_id, snapshot_path, snapshot_ts}`
4. Compaction fires naturally at ~100k, session continues with same ID

**Recovery (automatic at session start):**
1. `check_recovery()` reads `last_session.json` → finds previous session ID + snapshot path
2. Reads previous session file → checks for COMPACTION marker
3. If COMPACTION marker found → snapshot exists → restore: load snapshot's messages into context
4. If no COMPACTION marker → previous session ended cleanly → skip restore, start fresh

**Key fact:** Session ID is stable across compaction (verified: same ID before and after). Recovery is deterministic — no guessing.

**Snapshot naming:** `pre_compact_<session_id>_<timestamp>.json`
**Archive:** `~/.hermes/session_snapshots/` (50 max) + `/mnt/nvme/obsidian-vault/sessions/` (mirror)

**Stale snapshot prune:** Snapshots older than 24h are automatically removed.
