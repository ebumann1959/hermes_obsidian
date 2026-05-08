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

First: sync vault with the other agent:
```bash
bash ~/sync-vault.sh pull
```

Then read context:
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

**Pre-compaction save (RESOLVED — two-layer system):**

1. **Watchdog daemon** (`session-watchdog.service`) — runs during active sessions, uses inotify to capture compaction the instant it happens. Self-destructs after 10 min idle.

2. **Cron fallback** — runs every 3 minutes (`*/3 * * * *`), checks for new compaction markers in sessions modified in the last 30 min, catches compactions that fired while watchdog was idle.

Archive location: `~/.hermes/session_snapshots/` (indexed, 50 max) + `/mnt/nvme/obsidian-vault/sessions/` (mirror). Use the `session-snapshot-recovery` skill to reconstruct context after compaction. Index: `~/.hermes/session_snapshots/snapshot_index.json`.
