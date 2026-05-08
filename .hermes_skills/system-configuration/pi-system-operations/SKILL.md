---
name: pi-system-operations
description: "Raspberry Pi system administration — SSH agent workarounds, systemd user services, XScreensaver, LXPanel, and Conky monitoring widgets (CM2 ARM64, execgraph plots, process tracking)."
category: system-configuration
---

# Pi System Operations

Raspberry Pi system administration covering SSH agent, systemd user services, XScreensaver, and LXPanel customization.

---

## SSH Agent Workaround

**Problem:** SSH auth fails on Pi even with valid key — agent forwarding doesn't work, key not offered.

**Fix — start ssh-agent per session:**
```bash
eval $(ssh-agent -s) && ssh-add ~/.ssh/id_ed25519 && ssh-add -l
```

**Verify:**
```bash
ssh -o ConnectTimeout=5 10.0.0.91 "echo OK"
```

**If target not in known_hosts:**
```bash
ssh-keyscan -t ed25519 -H 10.0.0.91 >> ~/.ssh/known_hosts 2>/dev/null
```

---

## Systemd User Service — graphical-session.target

User systemd does NOT have `graphical.target`. Use `graphical-session.target`:

```ini
[Unit]
After=graphical-session.target
PartOf=graphical-session.target
[Install]
WantedBy=graphical-session.target
```

`graphical.target` silently fails — `systemctl --user status conky.service` shows "inactive (dead)" with no error.

---

## XScreensaver on Raspberry Pi (GL Matrix Effect)

Install and configure XScreensaver with GL hacks on the Pi desktop:

```bash
sudo apt-get install -y xscreensaver xscreensaver-gl-extra
```

Configure: **Menu → Settings → Screensaver** (or run `xscreensaver-demo`).

**For GL matrix effect:** Select "Matrix" from the GL hacks list.

**XScreensaver + CM2 Incompatibility:** When XScreensaver runs with GL hacks, it covers the screen and intercepts all input. CM2 GUI toggles fail silently. Use CLI toggle instead:
```bash
/home/Evan/bin/cm2-toggle <widget> [on|off|toggle]
```

---

## LXPanel XScreensaver Button

Customize the LXPanel logout button to launch XScreensaver:

**Find the button config:**
```bash
ls ~/.config/lxpanel/*/plugins/  # look for taskbar or pwidgets
grep -r "xscreensaver\|screensaver\|logout" ~/.config/lxpanel/ 2>/dev/null
```

**Restart LXPanel after config change:**
```bash
lxpanelctl restart
# or
killall lxpanel && lxpanel &
```

---

## DISPLAY on RPi5 LXDE

Xorg runs on `DISPLAY=:0` (verify: `w` or `ps aux | grep Xorg`). Not `:1`.

All scripts, systemd services, and conky startup must `export DISPLAY=:0`.

---

## Conky Operations (from conky-operations)

Umbrella skill for all Conky configuration, installation, and operations on the Raspberry Pi. Covers Conky Manager 2 (ARM64), old-style `.conkyrc` widgets, Lua/GTK widgets, execgraph line plots, systemd user services, and DISPLAY inheritance debugging.

### ⚠️ First Rule — Old-Style vs Lua Syntax

**Conky Manager 2 (CM2) only detects old-style `TEXT` syntax**, NOT Lua/GTK `conky.text = [[...]]`.

Every widget file must have a bare `TEXT` on its own line to appear in CM2's widget list:

```
alignment top_right
gap_x 10
gap_y 10

TEXT
${alignc}${sysname}
```

CM2 scans with `grep -r "^[[:blank:]]*TEXT[[:blank:]]*$"` — Lua style is silently ignored.

For transparency in old-style:
```
own_window_transparent yes
own_window_argb_visual yes
own_window_argb_value 0
```

### CM2 on ARM64 (No arm64 .deb Available)

CM2 (`teeedubb/conky-manager2`) only publishes amd64 debs. Build from the `zcot/conky-manager2` fork:

```bash
# 1. Remove old CM1 first (masks CM2 binary!)
sudo rm /usr/bin/conky-manager /usr/share/applications/conky-manager.desktop /usr/share/pixmaps/conky-manager*.png

# 2. Install dependencies
sudo apt-get install -y libgtk-3-dev cmake valac libgee-0.8-dev libjson-glib-dev imagemagick

# 3. Build from fork
cd /tmp && curl -sL "https://codeload.github.com/zcot/conky-manager2/tar.gz/master" -o zcot.tar.gz
tar -xzf zcot.tar.gz
cd conky-manager2-master/src && make && sudo cp conky-manager /usr/bin/
```

**CM2 JSON config** (`~/.config/conky-manager.json`): `search-locations` must include your conky path. Empty `[]` = nothing scanned.

**DISPLAY inheritance fix** — CM2 sets `DISPLAY=:1` in its env but child `conky -c <file>` scripts don't inherit it. Fix: rename real conky and install a C wrapper at `/usr/bin/conky` that calls `conky.bin` with DISPLAY set before `exec`. See `references/cm2-display-wrapper.md`.

**Shell wrapper caveat on RPi 5** — `/usr/bin/conky` may be a shell script (not ELF). See `references/rpi5-conky-shell-wrapper.md`.

### Multiple Old-Style Conky Only-Renders-One

**Root cause**: All configs with `own_window_type desktop` compete for the X11 root window. Only one wins.

**Fix**: Give each config a unique `own_window_target`:
```
own_window_target unique_name_here
```
Names: `conky_hermes_runners`, `conky_sessions`, `conky_supporters`, `conky_system`.

Verify: each conky logs a different created window ID:
```
conky: drawing to created window (0x1200002)
conky: drawing to created window (0x1a00002)
```

### Execgraph Syntax — The First Argument Must Be a Command

`${execgraph}` runs a command, not a file path. This FAILS:
```
${execgraph -t 20,180 /tmp/fan_rpm_log}
```
This WORKS:
```
${execgraph "cat /tmp/fan_rpm_log" 80,180 100 -t}
```

Syntax order: `${execgraph "command" HEIGHT,WIDTH SCALE -t}`. Quote the entire command. `-t` = temperature gradient. Without `-t` = filled area graph.

**Scale must be 0–100**: raw RPM values (~2000) cause "exec value not between 0 and 100". Always log percentage (0–100), not raw values.

**Execgraph requires a persistent background logger daemon**, not `${execi}` inside conky. The logger must run before conky starts. See `scripts/fan_rpm_logger.sh`.

### Execbar Rendering 0-Width Bars

On some builds, `execbar` returns 0-width bars even with valid 0–100 values. Workaround: use `${execgraph}` instead. If execbar is required, verify the command returns a simple integer on a single line with no whitespace.

### Text-Based Progress Bars (ASCII)

For simple percentage displays without execgraph complexity:
```
${execbar cat /tmp/some_value}
```
Value must be 0–100. For multi-segment bars, use a script that outputs aligned `█`/`░` characters. See `references/ascii-progress-bars.md`.

### Hermes Process Monitoring Scripts

Scripts in `/home/Evan/.conky/`. Key scripts: `hermes_instances.sh`, `hermes_sessions.sh`, `hermes_runners.sh`, `hermes_supporters.sh`, `hermes_children.sh`, `top_ram.sh`, `token_rate_bars.py`.

**Output format** (name left, duration right-aligned at col 20, RSS MB col 30):
```
Richard        01:01   131M  1.6%
Susan          00:13   134M  1.7%
```

**Self-monitoring exclusion** — monitoring scripts must exclude themselves.

**Subshell variable scoping trap**: `cmd | while read line` runs loop in a subshell — variables are LOST after the loop. Write to a temp file first.

**Token Rate Tracking (Delta-Based Windows)**: Querying by `started_at > cutoff` misses active sessions that started before the window. Track total token count over time in a history file, compute deltas. See `references/token-rate-delta-tracking.md`.

### User Service — Use graphical-session.target, NOT graphical.target

User systemd does NOT have `graphical.target`. Use `graphical-session.target`:

```ini
[Unit]
After=graphical-session.target
PartOf=graphical-session.target
[Install]
WantedBy=graphical-session.target
```

`graphical.target` silently fails — `systemctl --user status conky.service` shows "inactive (dead)" with no error.

### DISPLAY=:0 on RPi5 LXDE (Not :1)

Xorg runs on `DISPLAY=:0` (verify: `w` or `ps aux | grep Xorg`). The systemd service and `conky-startup.sh` must both `export DISPLAY=:0`.

### Conky Process Name — It's conky.bin, NOT conky

- `killall conky` → **NO EFFECT** (process named `conky.bin`)
- `pkill conky` → works
- `killall conky.bin` → works

### CM2 + XScreensaver Incompatibility

When XScreensaver GL hacks run, they cover the screen and intercept clicks. CM2 GUI toggles fail silently. **Use CLI toggle instead**:
```bash
/home/Evan/bin/cm2-toggle <widget> [on|off|toggle]
/home/Evan/bin/cm2-toggle all on
/home/Evan/bin/cm2-toggle killall    # nuclear stop
```

### Conky Silently Crashes on Invalid exec Hardware Path

Adding `${exec cat /sys/class/hwmon/hwmon1/fan1_input}` can crash the entire conky silently. Test commands standalone first.

### minimum_width Must Be Unquoted Number

```
minimum_width 300      # correct — bare number
minimum_width "300"     # WRONG — triggers "Invalid value of type 'string'"
```

### if_existing Requires Two Arguments

On this conky 1.22.1 build:
```
${if_existing /proc/123/cmdline, somevar}   # correct — comma-separated
${if_existing /proc/123/cmdline}              # WRONG — "if_existing needs an argument or two"
```

---

## Dead User Path Sweep — Nuke ALL References in ONE Pass

**Problem:** When a Linux user is deleted and replaced (e.g., `shady` → `Evan`), old path references accumulate across `.hermes/`, `show_runner/`, session transcripts, pastes, archived skills, and SQLite state databases. A partial sweep misses files and the user has to correct you MULTIPLE TIMES, which is infuriating. The user does NOT say "just the code files" — they say ALL OF IT.

**The rule:** When told a user doesn't exist, do ONE comprehensive sweep. Do NOT skip session files, do NOT skip SQLite DBs. The user will not explain twice.

---

### PASS 1 — Text files (Pi + PC)

---

## Conky Operations

Conky system monitoring on Raspberry Pi — covers Conky Manager 2 (ARM64), old-style `.conkyrc` widgets, Lua/GTK widgets, execgraph line plots, systemd user services, and DISPLAY inheritance debugging.

### ⚠️ First Rule — Old-Style vs Lua Syntax

**Conky Manager 2 (CM2) only detects old-style `TEXT` syntax**, NOT Lua/GTK `conky.text = [[...]]`.

Every widget file must have a bare `TEXT` on its own line to appear in CM2's widget list:

```
alignment top_right
gap_x 10
gap_y 10

TEXT
${alignc}${sysname}
```

CM2 scans with `grep -r "^[[:blank:]]*TEXT[[:blank:]]*$"` — Lua style is silently ignored.

### CM2 on ARM64 (No arm64 .deb Available)

CM2 (`teeedubb/conky-manager2`) only publishes amd64 debs. Build from the `zcot/conky-manager2` fork:

```bash
# 1. Remove old CM1 first (masks CM2 binary!)
sudo rm /usr/bin/conky-manager /usr/share/applications/conky-manager.desktop /usr/share/pixmaps/conky-manager*.png

# 2. Install dependencies
sudo apt-get install -y libgtk-3-dev cmake valac libgee-0.8-dev libjson-glib-dev imagemagick

# 3. Build from fork
cd /tmp && curl -sL "https://codeload.github.com/zcot/conky-manager2/tar.gz/master" -o zcot.tar.gz
tar -xzf zcot.tar.gz
cd conky-manager2-master/src && make && sudo cp conky-manager /usr/bin/
```

**DISPLAY inheritance fix** — CM2 sets `DISPLAY=:1` in its env but child `conky -c <file>` scripts don't inherit it. Fix: rename real conky and install a C wrapper. See `references/cm2-display-wrapper.md`.

### Multiple Old-Style Conky Only-Renders-One

**Root cause**: All configs with `own_window_type desktop` compete for the X11 root window. Only one wins.

**Fix**: Give each config a unique `own_window_target`:
```
own_window_target unique_name_here
```
Names: `conky_hermes_runners`, `conky_sessions`, `conky_supporters`, `conky_system`.

### Execgraph Syntax — The First Argument Must Be a Command

`${execgraph}` runs a command, not a file path. This FAILS:
```
${execgraph -t 20,180 /tmp/fan_rpm_log}
```
This WORKS:
```
${execgraph "cat /tmp/fan_rpm_log" 80,180 100 -t}
```

Syntax order: `${execgraph "command" HEIGHT,WIDTH SCALE -t}`. Quote the entire command. `-t` = temperature gradient. Scale must be 0–100 (log percentage, not raw values).

### Process Monitoring Scripts

Scripts in `/home/Evan/.conky/`. Key scripts: `hermes_instances.sh`, `hermes_sessions.sh`, `hermes_runners.sh`, `hermes_supporters.sh`, `hermes_children.sh`, `top_ram.sh`, `token_rate_bars.py`.

**Output format** (name left, duration right-aligned at col 20, RSS MB col 30):
```
Richard        01:01   131M  1.6%
Susan          00:13   134M  1.7%
```

**Self-monitoring exclusion** — monitoring scripts must exclude themselves.

**Token rate tracking** — query by `started_at > cutoff` misses active sessions that started before the window. Use delta-based tracking. See `references/token-rate-delta-tracking.md` and `scripts/token_rate_bars.py`.

**Fan RPM logger daemon** — persistent background logger for execgraph. See `scripts/fan_rpm_logger.sh`.

### Conky Process Name — It's conky.bin, NOT conky

- `killall conky` → **NO EFFECT** (process named `conky.bin`)
- `pkill conky` → works
- `killall conky.bin` → works

### CM2 + XScreensaver Incompatibility

When XScreensaver GL hacks run, they cover the screen and intercept clicks. CM2 GUI toggles fail silently. **Use CLI toggle instead**:
```bash
/home/Evan/bin/cm2-toggle <widget> [on|off|toggle]
/home/Evan/bin/cm2-toggle all on
/home/Evin/bin/cm2-toggle killall    # nuclear stop
```

### References

- `references/token-rate-delta-tracking.md`
- `references/cm2-display-wrapper.md`
- `references/pwm_rpm_sweep_data.md`
- `references/ascii-progress-bars.md`
- `references/rpi5-conky-shell-wrapper.md`
- `scripts/fan_rpm_logger.sh`



Run on both machines:

```bash
# Find ALL remaining references
cd /home/Evan && find .hermes/ show_runner/ .claude/ -type f \
  \( -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.cs" -o -name "*.txt" \) \
  ! -path "*/venv/*" ! -path "*/node_modules/*" \
  -exec grep -l "/home/OLD_USER" {} \; 2>/dev/null | sort -u

# Fix ALL of them in one sed call
sed -i 's|/home/OLD_USER|/home/Evan|g' file1 file2 file3 ...
```

**Verify:**
```bash
cd /home/Evan && find .hermes/ show_runner/ .claude/ -type f \
  \( -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.cs" -o -name "*.txt" \) \
  ! -path "*/venv/*" ! -path "*/node_modules/*" \
  -exec grep -l "/home/OLD_USER" {} \; 2>/dev/null
# Should return EMPTY
```

---

### PASS 2 — Session transcript JSON files (Pi + PC)

```bash
# Pi
cd /home/Evan && find .hermes/sessions/ -type f -size -10M \
  -exec sed -i 's|/home/OLD_USER|/home/Evan|g' {} + 2>/dev/null

# PC — also clean .claude sessions
ssh USER@HOST "find /home/Evan/.hermes/sessions /home/Evan/.claude -type f -size -10M \
  -exec sed -i 's|/home/OLD_USER|/home/Evan|g' {} + 2>/dev/null"
```

---

### PASS 3 — SQLite state databases (Pi + PC)

Text-file tools (sed/grep) do NOT touch SQLite databases. Use Python:

**On target machine, for each `.db` file:**
```python
python3 - << 'EOF'
import sqlite3
import glob

for db_path in glob.glob("/home/Evan/**/state.db", recursive=True) + \
               glob.glob("/home/Evan/**/esuite.db", recursive=True):
    conn = sqlite3.connect(db_path)
    for table in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        table = table[0]
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        for col in cols:
            if col in ('content', 'value', 'path', 'data', 'tool_calls', 'reasoning',
                       'reasoning_details', 'message_metadata', 'title', 'name', 'description'):
                n = conn.execute(
                    f"UPDATE {table} SET {col} = REPLACE({col}, '/home/OLD_USER', '/home/Evan') "
                    f"WHERE {col} LIKE '%/home/OLD_USER%'"
                ).rowcount
                if n:
                    print(f'{db_path} {table}.{col}: {n} rows')
    conn.commit()
    conn.close()
EOF
```

**Known SQLite DBs that hold path data:**
- `/home/Evan/.hermes/state.db` — Hermes session messages, tool_calls, reasoning, reasoning_details
- `/home/Evan/Projects/e-suite/backend/data/esuite.db` — project tasks, messages

**After cleaning, verify no references remain:**
```bash
# Text
grep -rl '/home/OLD_USER' /home/Evan/.hermes/ /home/Evan/Projects/ /home/Evan/.claude/ /home/Evan/Documents/ 2>/dev/null | wc -l
# Should be 0

# SQLite
python3 -c "
import sqlite3, glob
for f in glob.glob('/home/Evan/.hermes/state.db') + glob.glob('/home/Evan/Projects/e-suite/backend/data/esuite.db'):
    conn = sqlite3.connect(f)
    for t in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"):
        for r in conn.execute(f'PRAGMA table_info({t[0]})'):
            if r[2] in ('TEXT',):
                n = conn.execute(f'SELECT COUNT(*) FROM {t[0]} WHERE {r[1]} LIKE \"%OLD_USER%\"').fetchone()[0]
                if n: print(f'{f} {t[0]}.{r[1]}: {n}')
    conn.close()
"
```

---

### Common files with stale paths after user migration

**Always check these by name (not just grep):**
- `.hermes/context/hermes.json`, `paths.json`, `system.json`
- `.hermes/gateway_state.json`
- `.hermes/memories/MEMORY.md`
- `.hermes/runner.py`, `.hermes/show_runner/show_runner.py`, `.hermes/auntie_runner.py`
- `.hermes/persona-runners/config.py`, `runner.py`, `reset_scene.sh`, `wipe_and_reset.py`, `morgan_freeman_runner.py`, `launch_ui.sh`
- `.hermes/persona-runners/PROJECT_NOTES.md`
- `.hermes/agents/*/instructions/AGENTS.md`, `.hermes/agents/*/memory/*.md`
- `.hermes/skills/.archive/*/SKILL.md`
- `.hermes/skills/paperclip-hermes-remote-setup/SKILL.md`
- `.hermes/skills/system-configuration/pi-system-operations/SKILL.md`
- `.hermes/prompt_builder.py`, `.hermes/persona_manager.py`
- `.hermes/gigi_runner.py`, `.hermes/richard_runner.py`, `.hermes/veronica_runner.py`, `.hermes/susan_runner.py`
- `.hermes/discord_bridge.py`, `.hermes/ui.py`
- `.hermes/show_runner/launch_ui.sh`
- `.hermes/show_runner/core/config.py`, `turn_manager.py`, `relationship_graph.py`, `state_manager.py`
- `.hermes/pastes/*.txt`
- `.hermes/vault/z-suite/decompose-history/*.json`
- `.hermes/vault/z-suite/teams/*/runs-archive/**`
- `.hermes/projects/*/docs/research-*.md`
- `.hermes/projects/*/deliverables/*.md`
- `.config/uv/uv-receipt.json`
- `show_runner/docs/`, `show_runner/docs_v2/`
- `show_runner/README.md`
- On PC: `.claude/paste-cache/`, `.claude/projects/*/memory/`
- On PC: `Documents/chatbot_boot.txt`, `Documents/hermes_pi_chat_ref.txt`
- On PC: `Projects/e-suite/projects/*/docs/REPORT.md`
- On PC: `paperclip-edge/.claude/settings.local.json`

**Session file behavior during active sessions:** The current session file will keep reacquiring old paths as context compacts. See `references/dead-user-sweep-session-behavior.md` for details.

**The user will NOT tell you twice.** If you find more after the first pass, do the second pass immediately without prompting.
