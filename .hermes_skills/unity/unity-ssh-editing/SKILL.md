---
name: unity-ssh-editing
description: "Read, edit, and compile-check Unity C# files on the PC (10.0.0.91) via SSH from the Pi. Covers the show_runner file layout, safe edit patterns, and headless compile verification."
version: 1.0.0
metadata:
  hermes:
    tags: [unity, csharp, ssh, pc, show_runner, editing]
    related_skills: [show-runner-dev, diff-workflow, escalate-to-claude]
---

# Unity SSH Editing

Hermes can read and edit Unity C# files on the PC without touching the Unity Editor GUI. All operations go through `ssh Evan@10.0.0.91`.

## File Layout (PC: 10.0.0.91)

```
/mnt/Data/show_runner/Assets/ShowRunner/
├── Scripts/
│   ├── ShowRunnerClient.cs      — WebSocket client, auto-reconnect
│   ├── ShowRunnerManager.cs     — spawns characters, message handlers
│   ├── SpatialBroadcaster.cs   — telemetry every 100ms
│   ├── CharacterRegistry.cs    — character GameObject tracking
│   ├── DialogueHUD.cs          — per-character speech bubble
│   ├── DialogueHUDManager.cs   — HUD lifecycle
│   ├── NarrationOverlay.cs     — narration text overlay
│   ├── NeighborhoodScene.cs    — scene setup
│   └── CameraDirector.cs       — camera logic
└── Editor/
    ├── CompileCheck.cs          — headless compile trigger
    └── CreateShowRunnerScene.cs — scene builder
```

## Safe Read Operations

```bash
# Read a file
ssh Evan@10.0.0.91 "cat '/mnt/Data/show_runner/Assets/ShowRunner/Scripts/ShowRunnerClient.cs'"

# Read a specific method (find line number first)
ssh Evan@10.0.0.91 "grep -n 'void Connect\|IEnumerator\|private.*reconnect' '/mnt/Data/show_runner/Assets/ShowRunner/Scripts/ShowRunnerClient.cs'"
ssh Evan@10.0.0.91 "sed -n '45,90p' '/mnt/Data/show_runner/Assets/ShowRunner/Scripts/ShowRunnerClient.cs'"

# Check all .cs files for a symbol
ssh Evan@10.0.0.91 "grep -rn 'StartTelemetry\|spatial_telemetry' /mnt/Data/show_runner/Assets/ShowRunner/"
```

## Edit Pattern (always use diff-workflow)

```bash
# 1. Read the target section on PC
ssh Evan@10.0.0.91 "sed -n '<start>,<end>p' '/mnt/Data/show_runner/Assets/ShowRunner/Scripts/<File>.cs'"

# 2. Generate diff locally (or write to Pi temp file)
cat > /tmp/unity_change.patch << 'DIFF'
--- a/Assets/ShowRunner/Scripts/ShowRunnerClient.cs
+++ b/Assets/ShowRunner/Scripts/ShowRunnerClient.cs
@@ -52,6 +52,8 @@
 existing context
-old line
+new line
 existing context
DIFF

# 3. Copy patch to PC and apply
scp /tmp/unity_change.patch Evan@10.0.0.91:/tmp/unity_change.patch
ssh Evan@10.0.0.91 "cd /mnt/Data/show_runner && patch --dry-run -p1 < /tmp/unity_change.patch"
ssh Evan@10.0.0.91 "cd /mnt/Data/show_runner && patch -p1 < /tmp/unity_change.patch"
```

## Compile Verification (headless)

Unity project must compile cleanly after any C# edit. Do not leave the PC in a broken compile state — it will break the editor on next open.

```bash
# Option A: Use the CompileCheck editor script (if Unity is NOT running)
UNITY="/home/Evan/.steam/debian-installation/compatibilitytools.d/unity"  # adjust path
ssh Evan@10.0.0.91 "find /opt /home -name 'Unity' -type f 2>/dev/null | head -3"

# Option B: Check for obvious syntax errors with dotnet (if installed)
ssh Evan@10.0.0.91 "which dotnet && dotnet build /mnt/Data/show_runner/*.sln 2>&1 | tail -20" 2>/dev/null

# Option C: Check for matching braces / obvious C# syntax
ssh Evan@10.0.0.91 "python3 -c \"
import re, sys
src = open('/mnt/Data/show_runner/Assets/ShowRunner/Scripts/ShowRunnerClient.cs').read()
opens = src.count('{')
closes = src.count('}')
print(f'Braces: {{ {opens} vs }} {closes} — balanced={opens==closes}')
\""
```

## Escalation Triggers for Unity Tasks

Escalate to Claude (with Evan's permission) for:
- Changes to message handler dispatch logic (complex async patterns)
- Adding new WebSocket message types (requires Pi + PC coordination)
- Anything that changes the public interface between ShowRunnerClient and ShowRunnerManager

For those cases use `escalate-to-claude` skill — Claude Code on PC can edit and verify Unity files natively.

## C# Conventions in This Codebase

- `StartCoroutine()` for async Unity operations — do NOT use `async/await` in MonoBehaviours
- `ShowRunnerClient.Instance` is the singleton — never call `new ShowRunnerClient()`
- `SpatialBroadcaster` is the sole telemetry source — do NOT call `StartTelemetry()` from elsewhere
- Log with `Debug.Log($"[ComponentName] message")` — prefix with component name
