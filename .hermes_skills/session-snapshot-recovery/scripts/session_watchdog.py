#!/usr/bin/env python3
"""
Session Watchdog — captures session context before compaction.
Runs as a systemd user service. Watches ~/.hermes/sessions/ for compaction
events and archives pre-compaction snapshots to the vault.

Compaction detection:
  - File size decreases significantly (compaction rewrites the session file smaller)
  - A "CONTEXT COMPACTION" marker appears in a user message
  - File transitions from large to small within a short window
"""

import json
import os
import sys
import time
import hashlib
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from collections import deque

# ── Config ────────────────────────────────────────────────────────────────────
SESSIONS_DIR = Path.home() / ".hermes" / "sessions"
SNAPSHOT_DIR = Path.home() / ".hermes" / "session_snapshots"
INDEX_FILE   = SNAPSHOT_DIR / "snapshot_index.json"
VAULT_SESSIONS = Path("/mnt/nvme/obsidian-vault/sessions")
VAULT_SESSIONS.mkdir(parents=True, exist_ok=True)

POLL_INTERVAL   = 180   # seconds between periodic snapshots
COMPACTION_GRACE = 5    # seconds: if file shrinks within this window → compaction
MIN_SIZE_DROP   = 0.5   # fraction: file must shrink by this much to count as compaction
MAX_SNAPSHOTS   = 50    # keep this many local snapshots (oldest purged)
IDLE_TIMEOUT    = 600   # seconds of session inactivity before self-destruct (10 min)
SESSION_ACTIVITY_WINDOW = 60  # seconds: a session file modified within this many seconds = active

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg):
    print(f"[session_watchdog] {datetime.now().strftime('%H:%M:%S')} {msg}", flush=True)

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
    return {"snapshots": [], "last_md5": None, "last_size": None}

def save_index(idx):
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(idx, indent=2))

def snapshot_name(session_id):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"pre_compact_{session_id}_{ts}.json"

def current_session_file():
    """Return the most recently modified session file."""
    files = list(SESSIONS_DIR.glob("session_*.json"))
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)

def is_session_active(threshold=SESSION_ACTIVITY_WINDOW):
    """Return True if any session file was modified within the threshold seconds."""
    now = time.time()
    for f in SESSIONS_DIR.glob("session_*.json"):
        if now - f.stat().st_mtime < threshold:
            return True
    return False

def save_snapshot(src_path, label=""):
    """Copy session file to local snapshot dir and vault."""
    if not src_path or not src_path.exists():
        return None
    name = snapshot_name(src_path.stem)
    dst  = SNAPSHOT_DIR / name
    vault_dst = VAULT_SESSIONS / name
    try:
        import shutil
        shutil.copy2(src_path, dst)
        shutil.copy2(src_path, vault_dst)
        log(f"Saved snapshot: {name} ({dst.stat().st_size} bytes)")
        return str(dst)
    except Exception as e:
        log(f"Snapshot failed: {e}")
        return None

def update_index(snap_path):
    idx = load_index()
    info = {
        "path":         str(snap_path),
        "timestamp":    datetime.now().isoformat(),
        "session_id":   current_session_file().stem if current_session_file() else "unknown",
        "size":         os.path.getsize(snap_path) if snap_path else 0,
        "md5":          md5(snap_path) if snap_path and os.path.exists(snap_path) else None,
    }
    idx["snapshots"].append(info)
    # prune old snapshots
    while len(idx["snapshots"]) > MAX_SNAPSHOTS:
        old = idx["snapshots"].pop(0)
        old_path = Path(old["path"])
        if old_path.exists():
            try: old_path.unlink()
            except: pass
    save_index(idx)
    return info

def detect_compaction(prev_size, prev_mtime, curr_size, curr_mtime, curr_path):
    """Return True if curr file looks like a post-compaction version."""
    if prev_size is None:
        return False
    # Size must have dropped significantly
    if prev_size == 0 or curr_size >= prev_size * (1 - MIN_SIZE_DROP):
        return False
    # Must have happened quickly (within COMPACTION_GRACE seconds of previous activity)
    elapsed = curr_mtime - prev_mtime
    if elapsed > COMPACTION_GRACE:
        return False
    # Verify compaction marker
    try:
        with open(curr_path) as f:
            content = f.read()
        if "CONTEXT COMPACTION" in content:
            return True
    except Exception:
        pass
    return False

# ── Polling watcher (backstop) ────────────────────────────────────────────────
class PeriodicSnapshot:
    def __init__(self, interval=POLL_INTERVAL):
        self.interval = interval
        self.running   = False

    def start(self):
        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            time.sleep(self.interval)
            sess = current_session_file()
            if sess:
                snap = save_snapshot(sess)
                if snap:
                    update_index(snap)

# ── inotify watcher ───────────────────────────────────────────────────────────
class InotifyWatcher:
    def __init__(self):
        self.proc   = None
        self.running = False
        self.prev_size  = None
        self.prev_mtime = None
        self.sess_path  = None

    def start(self):
        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def stop(self):
        self.running = False
        if self.proc:
            self.proc.terminate()

    def _loop(self):
        sess = current_session_file()
        if not sess:
            log("No session file found, waiting...")
            time.sleep(5)
            sess = current_session_file()
        if sess:
            self.sess_path  = str(sess)
            self.prev_size  = sess.stat().st_size
            self.prev_mtime = sess.stat().st_mtime
            log(f"Watching: {self.sess_path} ({self.prev_size} bytes)")

        # Use inotifywait to watch the sessions dir for close events
        cmd = ["inotifywait", "-m", "-e", "CLOSE", "-e", "MODIFY",
               "--format", "%e %f", str(SESSIONS_DIR)]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        log("inotifywait started")

        last_check = time.time()
        while self.running:
            line = self.proc.stdout.readline()
            if not line:
                break
            parts = line.strip().split(None, 1)
            if len(parts) < 2:
                continue
            event, fname = parts
            if not fname.startswith("session_") or not fname.endswith(".json"):
                continue

            now = time.time()
            if now - last_check < 0.5:
                continue  # debounce
            last_check = now

            sess = SESSIONS_DIR / fname
            if not sess.exists():
                continue
            curr_size  = sess.stat().st_size
            curr_mtime  = sess.stat().st_mtime

            # Detect compaction
            is_compact = detect_compaction(self.prev_size, self.prev_mtime, curr_size, curr_mtime, sess)

            if is_compact:
                log(f"COMPACTION DETECTED! {self.prev_size} → {curr_size} bytes")
                snap = save_snapshot(sess)
                if snap:
                    update_index(snap)
                # Reset tracking to new (smaller) baseline
                self.prev_size  = curr_size
                self.prev_mtime  = curr_mtime
            else:
                self.prev_size  = curr_size
                self.prev_mtime  = curr_mtime

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    log("Session watchdog starting...")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    periodic = PeriodicSnapshot(interval=POLL_INTERVAL)
    inotify  = InotifyWatcher()

    periodic.start()
    inotify.start()

    log(f"Watching {SESSIONS_DIR} — snapshots every {POLL_INTERVAL}s, compaction detection active")

    try:
        idle_since = None
        while True:
            time.sleep(60)
            active = is_session_active()
            if active:
                idle_since = None
            else:
                if idle_since is None:
                    idle_since = time.time()
                    log("Session inactive — starting idle timer")
                elapsed = time.time() - idle_since
                log(f"Idle {int(elapsed)}s / {IDLE_TIMEOUT}s")
                if elapsed >= IDLE_TIMEOUT:
                    log(f"IDLE TIMEOUT — self-destructing")
                    inotify.stop()
                    periodic.stop()
                    return
            # Heartbeat + prune old vault snapshots
            idx = load_index()
            log(f"Heartbeat: {len(idx['snapshots'])} snapshots")
    except KeyboardInterrupt:
        log("Shutting down...")
        inotify.stop()
        periodic.stop()

if __name__ == "__main__":
    main()
