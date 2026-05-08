#!/usr/bin/env python3
"""
Lightweight cron script — snapshot session context if compaction occurred.
Run via cron every 3 minutes: */3 * * * * /usr/bin/python3 /home/Evan/.hermes/scripts/session_snapshot_cron.py

Designed to run alongside the watchdog daemon (which handles active-session compaction capture).
This catches compactions that fire while the watchdog is idle (user away from keyboard).
"""

import json
import os
import shutil
import hashlib
import time
from pathlib import Path
from datetime import datetime

SESSIONS_DIR   = Path.home() / ".hermes" / "sessions"
SNAPSHOT_DIR   = Path.home() / ".hermes" / "session_snapshots"
INDEX_FILE     = SNAPSHOT_DIR / "snapshot_index.json"
VAULT_SESSIONS = Path("/mnt/nvme/obsidian-vault/sessions")

def log(msg):
    print(f"[snapshot_cron] {datetime.now().strftime('%H:%M:%S')} {msg}", flush=True)

def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_index():
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text())
        except Exception:
            pass
    return {"snapshots": [], "last_session_md5": {}}

def save_index(idx):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(idx, indent=2))

def has_compaction_marker(path):
    try:
        with open(path) as f:
            return "CONTEXT COMPACTION" in f.read()
    except Exception:
        return False

def snapshot_session(src_path):
    name = f"cron_snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{src_path.stem}.json"
    dst  = SNAPSHOT_DIR / name
    vdst = VAULT_SESSIONS / name
    try:
        shutil.copy2(src_path, dst)
        if not VAULT_SESSIONS.exists():
            VAULT_SESSIONS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, vdst)
        log(f"Saved: {name} ({os.path.getsize(dst)} bytes)")
        return name
    except Exception as e:
        log(f"Failed: {e}")
        return None

RECENT_WINDOW   = 1800   # only check sessions modified within the last 30 minutes

def recent_sessions():
    """Yield session files modified within RECENT_WINDOW seconds."""
    now = time.time()
    for f in SESSIONS_DIR.glob("session_*.json"):
        if now - f.stat().st_mtime < RECENT_WINDOW:
            yield f

def main():
    idx = load_index()
    last_md5 = idx.get("last_session_md5", {})

    found_new = False
    for sess_file in recent_sessions():
        sess_md5 = md5(sess_file)
        sess_id  = sess_file.stem

        prev_md5 = last_md5.get(sess_id)

        if has_compaction_marker(sess_file):
            if sess_md5 != prev_md5:
                # New compaction on this session
                snap = snapshot_session(sess_file)
                if snap:
                    info = {
                        "path": str(SNAPSHOT_DIR / snap),
                        "timestamp": datetime.now().isoformat(),
                        "session_id": sess_id,
                        "size": os.path.getsize(sess_file),
                        "md5": sess_md5,
                        "source": "cron"
                    }
                    idx["snapshots"].append(info)
                    last_md5[sess_id] = sess_md5
                    found_new = True
            else:
                # Already snapshot-saved this compaction state
                pass

    idx["last_session_md5"] = last_md5
    save_index(idx)

    if found_new:
        log(f"Snapshot(s) saved — total: {len(idx['snapshots'])}")
    # else: silent, nothing new

if __name__ == "__main__":
    main()
