# Dead User Path Sweep — Session File Behavior

## Current Session File Keeps Reacquiring Old Paths

**Problem:** The live session file (`.hermes/sessions/session_YYYYMMDD_HHMMSS_*.json`) is the current working context. Every time context compacts and repopulates from prior turns, the old path string gets re-injected into the session file via the compaction summary. Running `sed` on it makes it clean temporarily, but the NEXT context compaction re-injects the old path.

**This is expected behavior.** The session file is a living document of the current conversation, not a dead artifact.

**What this means for cleanup:**
- The current session file will ALWAYS show `grep -c "/home/shady"` > 0 during an active session
- After the conversation ends and a new session starts, that old session file becomes a historical transcript
- At that point it is safe to clean with the full sweep (PASS 2 including sessions)
- During the session: text files, pastes, skills, configs, and SQLite DBs are what matters

## Correct Interpretation of "ALL OF IT"

When Evan says "ALL OF IT" or "get rid of everything":
- Means: ALL file types including session transcripts and SQLite state databases
- Does NOT mean: the current session file (it will reacquire old paths during the session naturally)
- Does mean: every historical session file, every past transcript, every paste

## SQLite REPLACE() vs JSON Text Files

Session JSON files use `sed 's|/old|/new|g'` — this works because they are plain text.

SQLite databases cannot be touched by sed/grep. Use:
```python
conn.execute("UPDATE table SET col = REPLACE(col, '/old/path', '/new/path') WHERE col LIKE '%/old/path%'")
```

This is the ONLY way to clean SQLite. It must be done ON the machine hosting the DB.
