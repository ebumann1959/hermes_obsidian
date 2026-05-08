# Remote Headless Execution — Shared Patterns

Both `unity-editor-scripting` and `blender-headless-ssh-render` share these patterns. Keep in sync.

## The 5 Universal Rules

### 1. ALWAYS Kill Stale Processes First
Old processes hold resources (files, ports, GPU memory) and cause silent failures.
```bash
ssh user@host "killall -9 -f <process_name> 2>/dev/null; sleep 2"
```

### 2. ALWAYS Use Unique Output Filenames
Never use `output.png`, `render.png`, `test.png`. Always include a version/iteration:
```
room_v6.png  vs  test_render.png  # old file from previous run masks missing new output
```
Old files from prior runs make it look like the current run succeeded when it didn't.

### 3. ALWAYS Run Foreground, Not Background
Background execution (`&`) with SSH is **unreliable** — the `&` detaches before completion, stdout/stderr are lost, and there's no way to detect silent failure. The file never appears or has a stale timestamp.
```bash
# WRONG — silent failure, undetectable
ssh user@host "command --background &"

# RIGHT — foreground, stdout captured, failure is visible
timeout 120 ssh user@host "command" 2>&1 | tail -20
```

### 4. ALWAYS Verify After
```bash
# Check file exists and is recent
ssh user@host "stat /path/to/output.png"
# Average pixel color check (grey ~59 everywhere = failure)
convert /tmp/output.png -resize 1x1! txt:-
```

### 5. Write Scripts Locally, Then SCP
Heredocs via SSH (`cat > file << 'EOF'`) lose quotes and whitespace. Scripts with subscript notation lose quotes through terminal SSH. Write locally with `write_file` tool, then `scp`:
```bash
scp /tmp/render_scene.py user@host:/home/Evan/render_scene.py
```
Do NOT use `ssh user@host 'cat > /path << "EOF" ... EOF'` for scripts.

## Shared DISPLAY / GPU Context

Both Blender and Unity need a display context on the remote GPU machine:
- Blender: `xvfb-run -a` for virtual framebuffer
- Unity: `xvfb-run -a` similarly
- Both: AMD 7900 XT at MX25Rig (10.0.0.91)

Both are on MX Linux on MX25Rig. SSH user: `Evan`.
