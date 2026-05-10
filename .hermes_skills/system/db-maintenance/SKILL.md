---
name: db-maintenance
description: "Vacuum, checkpoint, and size-check the Hermes state.db SQLite database. Run when state.db exceeds 500MB or sessions feel slow. Prevents WAL bloat and disk exhaustion on the Pi."
version: 1.0.0
metadata:
  hermes:
    tags: [database, sqlite, maintenance, pi, system, cleanup]
---

# Hermes DB Maintenance

`state.db` is a SQLite database in WAL mode. Without periodic maintenance it accumulates dead pages and WAL frames, growing unboundedly.

## Check Current Size

```bash
ls -lh ~/.hermes/state.db ~/.hermes/state.db-wal ~/.hermes/state.db-shm 2>/dev/null
# Warn if state.db > 500MB or state.db-wal > 100MB
du -sh ~/.hermes/state.db
```

## Safe Maintenance (while Hermes is not running)

```bash
# 1. Confirm hermes agent is stopped
ps aux | grep -v grep | grep "hermes\|gateway" && echo "RUNNING - stop first" || echo "safe to proceed"

# 2. Checkpoint WAL (flush pending writes to main DB)
sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 3. Vacuum (reclaim dead space, rebuild pages)
sqlite3 ~/.hermes/state.db "VACUUM;"

# 4. Check integrity
sqlite3 ~/.hermes/state.db "PRAGMA integrity_check;" | head -5

# 5. Verify size reduced
ls -lh ~/.hermes/state.db
```

## Safe Maintenance (while Hermes IS running)

Only do the passive checkpoint — never VACUUM a live database:

```bash
sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(PASSIVE);"
# WAL will shrink incrementally without blocking the agent
```

## Prune Old Sessions (optional, if DB is very large)

```bash
# See what tables exist and rough row counts
sqlite3 ~/.hermes/state.db ".tables"
sqlite3 ~/.hermes/state.db "SELECT name, COUNT(*) FROM sqlite_master WHERE type='table' GROUP BY name;"

# Check session table size
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM sessions;" 2>/dev/null

# Delete sessions older than 30 days (adjust table/column names to match schema)
# ALWAYS dry-run first:
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM sessions WHERE created_at < datetime('now', '-30 days');" 2>/dev/null
# Then delete if count looks right:
# sqlite3 ~/.hermes/state.db "DELETE FROM sessions WHERE created_at < datetime('now', '-30 days');"
# sqlite3 ~/.hermes/state.db "VACUUM;"
```

## Disk Space Check

```bash
df -h /home/Evan
df -h /mnt/nvme
# If /home < 2GB free: prune sessions aggressively, then VACUUM
```

## Schedule

Run full maintenance (checkpoint + vacuum) monthly or when:
- `state.db` > 500MB
- `state.db-wal` > 50MB
- Pi disk usage > 80%

The `on_session_finalize` hook runs a passive checkpoint automatically after each session — this skill is for the periodic deep clean.
