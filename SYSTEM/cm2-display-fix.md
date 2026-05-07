# Conky Manager 2 + DISPLAY=:1 Bug — Root Cause & Fix

**Date:** April 13, 2026
**System:** Pi at 10.0.0.9 (Shadys-Gamblin-Corner, RPi 5 16GB), DISPLAY=:1
**Migrated:** 2026-04-20 to vault

---

## Problem

Conky Manager 2 (CM2) fails to render any conky widgets on DISPLAY=:1. Toggling widgets ON in CM2's UI appears to succeed (toggle stays checked) but no window appears. `killall conky` from terminal works but CM2's stop/start cycle is broken.

**Symptoms:**
- CM2 toggle checked, no visible window
- `conky -c <file>` exits 0 silently with `conky: can't open display:` when run from CM2's spawned script
- All 6 widgets render fine when run manually with `DISPLAY=:1 conky -c <file>`

---

## Root Cause

**CM2 spawns scripts without inheriting the DISPLAY environment variable.**

CM2 runs with `DISPLAY=:1` in its process environment (inherited from the LXDE session). When it toggles a widget ON, it writes a shell script to `/tmp/conky-manager/` and executes it:

```bash
#!/bin/bash
cd "/home/shady/.conky"
conky -c "/home/shady/.conky/hermes_runners.conkyrc"
```

The script runs as a child of CM2, but `fork()+exec()` strips the environment — DISPLAY is **not** passed to the child. The conky process starts with no DISPLAY, fails silently (exit 0), and renders nothing.

The kill scripts (`/tmp/conky-manager/*STOP*.sh`) don't exist — CM2 tracks PIDs internally and uses `kill(pid, SIGTERM)` directly, bypassing any killall mechanism.

---

## Files

| File | Purpose |
|------|---------|
| `/usr/bin/conky` | C wrapper — sets DISPLAY=:1 then execs conky.bin |
| `/usr/bin/conky.bin` | Original conky binary (renamed) |
| `/tmp/conky-manager/*.sh` | CM2-generated start/stop scripts (transient, overwritten every toggle) |

---

## Current Fix

C wrapper at `/usr/bin/conky` that sets `DISPLAY=:1` before exec'ing the real binary:

```c
int main(int argc, char *argv[]) {
    setenv("DISPLAY", ":1", 1);
    execv("/usr/bin/conky.bin", argv);
    return 1;
}
```

**Verified:**
- All 6 widgets (hermes_runners, hermes_sessions, hermes_children, hermes_supporters, hermes_instances, system_info) render on DISPLAY=:1 ✅
- CM2 stop (PID-based SIGTERM) works ✅
- CM2 start works ✅

---

## Limitation

**`killall conky` won't work from terminal.** The kernel's `comm` field (used by killall) is set from the binary's name at exec time. Since we exec `conky.bin`, comm = `conky.bin`. Cannot override this.

**Workaround for manual kill:**
```bash
kill $(pgrep conky)
pkill conky
```

**Always use:** `pkill conky` (not `killall conky`)

---

## XScreensaver GL Mode Blocks CM2 Toggles

**Date:** April 13, 2026, ~19:30

**Problem:** CM2 toggles stop responding after XScreensaver (with `glmatrix --root` GL mode) blanks and unblanks the screen.

**Root Cause:** XScreensaver's `glmatrix --root` mode intercepts pointer input when active. After unblanking, input routing may not fully recover. CM2's custom-drawn toggles require precise input delivery that gets blocked.

**Fix:**
```bash
killall xscreensaver; xscreensaver -no-splash &
```

**Prevention:** Avoid GL-mode screensavers (glmatrix, glsnake, glblur, etc.) if you need CM2 toggles while XScreensaver is running.

---

## Recompile Commands (if needed after conky update)

```bash
cat > /tmp/conky-wrapper.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    setenv("DISPLAY", ":1", 1);
    execv("/usr/bin/conky.bin", argv);
    return 1;
}
EOF

gcc /tmp/conky-wrapper.c -o /tmp/conky-wrapper
sudo cp /tmp/conky-wrapper /usr/bin/conky
sudo chmod +x /usr/bin/conky
```
