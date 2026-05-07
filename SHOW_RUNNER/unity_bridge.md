# Unity Bridge — Architecture & API Reference

**Created:** 2026-04-21
**Status:** Implemented (step 1+2 of pipeline)

---

## Overview

The bridge connects Pi (show_runner AI brain) to Unity (PC visual layer).  
Pi is the authority on all world state. Unity is a display executor.

```
Pi (10.0.0.9:8080)                  PC Unity (10.0.0.91:8080)
─────────────────────               ──────────────────────────
show_runner generates beat
  │
  ├─ bridge.play_beat()  ──POST──►  /api/state   → animation state setter
  │
  ├─ bridge.move()       ──POST──►  /api/move    → NavMeshAgent.SetDestination()
  │
  └─ Flask receives  ◄──POST──────  /api/unity/positions  (every 1s from Unity)
       /api/unity/positions
         → scene_manager.update_unity_position()
         → bridge._positions cache
```

---

## Pi-Side Files

| File | Role |
|------|------|
| `core/unity_bridge.py` | HTTP client — sends all commands to Unity |
| `show_runner_ui.py` | Flask server — receives position feedback from Unity |
| `core/scene_state.py` | `CharacterInScene` now has `unity_x`, `unity_z` fields |

### unity_bridge.py — key usage

```python
from core.unity_bridge import bridge

# Check connection
bridge.is_connected()   # → True/False

# Move a character to a named waypoint
bridge.move("susan", waypoint="kitchen_stove")

# Move to raw world coordinates
bridge.move("richard", x=2.5, z=-1.0)

# Face another character
bridge.face("susan", "richard")

# Drive a full dialogue beat (face + animate + sleep for duration)
bridge.play_beat("susan", beat_text, listener="richard")
# beat_text format: "*stirs aggressively* These burgers are FINE, Richard"

# Set animation state directly
bridge.set_state("richard", "sad", intensity=1.2)
# Valid states: idle, talking, angry, sad, happy, laughing, crying, surprised, celebrating, shocked

# Get positions from Unity (also cached in bridge._positions)
bridge.get_positions()

# Distance between two characters (from cached positions)
bridge.distance_between("susan", "richard")  # → float meters or None

# Human-readable proximity
bridge.proximity_description("susan", "richard")
# → "right next to" / "nearby" / "across the room from" / "Xm from"
```

### Flask endpoints (Pi receives)

| Endpoint | Method | Payload | Purpose |
|----------|--------|---------|---------|
| `/api/unity/positions` | POST | `{"characters":[{"id","x","y","z"}]}` | Unity pushes positions every 1s |
| `/api/unity/status` | GET | — | Check if Unity is reachable |

---

## Unity-Side Files

| File | Role |
|------|------|
| `UnityComms.cs` | HTTP server + position feedback sender |

### Unity HTTP API (receives from Pi)

| Endpoint | Method | Payload | Effect |
|----------|--------|---------|--------|
| `/api/status` | GET | — | Health check → `{"active":true,"characters":[...]}` |
| `/api/move` | POST | `{"character":"susan","waypoint":"kitchen_stove"}` | NavMesh walk to waypoint |
| `/api/move` | POST | `{"character":"susan","x":2.5,"z":-1.0}` | NavMesh walk to coordinates |
| `/api/face` | POST | `{"character":"susan","target":"richard"}` | Smooth rotation to face target |
| `/api/state` | POST | `{"character":"susan","state":"angry","intensity":1.5}` | Set Animator state |
| `/api/scene` | POST | `{"scene":"kitchen"}` | SceneSwitcher load |
| `/api/capture` | POST | `{}` | Capture frame → PNG |
| `/api/positions` | GET | — | All character world positions |
| `/api/frame` | GET | — | Last captured frame PNG | ⚠️ Not implemented |

### Animation states

| State | Animator params triggered |
|-------|--------------------------|
| `idle` | TalkIntensity=0, EmotionIntensity=0, Idle trigger |
| `talking` | TalkIntensity=intensity |
| `angry`, `sad`, `happy`, `laughing`, `crying`, `surprised`, `celebrating`, `shocked` | EmotionIntensity=intensity, Emotion trigger |

### Action tag → animation mapping (in bridge.py)

| Action tag contains | → Animation state |
|--------------------|------------------|
| laugh, chuckle, giggle | laughing |
| sob, cry, weep | crying |
| snap, slam, rage, yell, hiss | angry |
| shrug, slump, goes quiet | sad |
| grin, beam, smil | happy |
| gasp, eyes wide, jaw drop | surprised |
| (anything else) | talking |

---

## NavMesh Setup (do once per scene)

1. **Install AI Navigation package**
   `Window > Package Manager` → search "AI Navigation" → Install

2. **Bake NavMesh on scene floor**
   - Select your floor GameObject
   - Add component: `NavMesh Surface`
   - Click **Bake** in the inspector
   - Repeat for each scene/room if using multiple Unity scenes

3. **Create waypoints**
   - Create empty GameObjects at key positions (stove, table, couch, front door, etc.)
   - Add tag `Waypoint` (Edit > Project Settings > Tags and Layers > Tags)
   - Name them: `kitchen_stove`, `kitchen_table`, `living_room_couch`, `front_door`, etc.

---

## Waypoint naming convention

```
{room}_{object}
kitchen_stove
kitchen_table
kitchen_counter
living_room_couch
living_room_armchair
living_room_tv
front_door
front_yard_driveway
front_yard_lawn
```

Pi `scene_manager` position strings map to these names.  
Pi `scene_manager` position strings map to these names.

---

## Animator Controller requirements

Your Animator Controller must define:
- `Float` **TalkIntensity** (0–2)
- `Float` **EmotionIntensity** (0–2)
- `Trigger` **Emotion**
- `Trigger` **Idle**
- `Float` **MoveSpeed** (optional — drives walk blend tree)

Free Mixamo animations that work well:
- Idle: "Breathing Idle" or "Standing Idle"
- Walk: "Walking" (for blend tree with MoveSpeed)
- Talk: "Talking" or "Arguing"
- Angry: "Angry" or "Threatening"
- Sad: "Sad Idle" or "Defeated"
- Happy: "Happy Idle" or "Jump"

---

## Beat timing (without TTS)

`bridge.play_beat()` estimates speech duration from word count:
- Rate: 130 words/minute
- Minimum: 1.5 seconds
- Returns to idle automatically when done

For TTS integration (future): replace `time.sleep(duration)` in `play_beat()` with
actual audio playback + duration from TTS engine. The rest of the call chain stays the same.

---

## show_runner.py integration

After each `generate_beat()` call in the main loop, add:

```python
from core.unity_bridge import bridge

# After: beat, pending, consequences, categories = generate_beat(character, ...)
if bridge.is_connected():
    # listener = whoever spoke before (best guess for facing)
    turn_hist = turn_manager.get_turn_history(last_n=5)
    listener = next((n for n in reversed(turn_hist) if n != character), None)
    bridge.play_beat(character, beat, listener=listener, block=True)
```

`block=True` keeps the beat loop synchronized with animation.
`block=False` for non-blocking (beat loop continues while animation plays).

---

## Automated scene setup (batch mode)

ShowRunnerScene.unity was built fully headless with zero manual input:

```bash
env DISPLAY=:0 Unity -batchmode -nographics \
    -projectPath "/home/Evan/show_runner/My project" \
    -executeMethod SceneSetup.Run \
    -quit -logFile /tmp/unity_setup.log
```

**SceneSetup.cs** (`Assets/show_runner/Editor/SceneSetup.cs`) — called by `-executeMethod`:
- Creates `Assets/Scenes/ShowRunnerScene.unity`
- Builds 4 rooms: kitchen, living_room, entry, front_yard (primitive cubes with walls)
- Places 16 named waypoints tagged "Waypoint"
- Creates 6 character capsules at starting positions
- Creates `Assets/show_runner/Animations/CharacterAnimator.controller`
- Adds NavMeshSurface to ground plane, calls `BuildNavMesh()`
- Adds `UnityComms` manager GameObject
- Adds camera + directional light

**Batch mode gotchas learned:**
- Requires `DISPLAY=:0` on Linux even with `-nographics` (X socket must exist)
- `NavMeshCollectGeometry` is a native engine type inaccessible from editor assembly scripts; omit `surface.useGeometry` and use the default
- Unity "fake null" bug: never use `??` with `GetComponent<T>()` — use `if (x == null)` instead

## Security issues found (Z Suite audit 2026-04-27)

> **Critical — do not deploy to network until fixed.**

- [ ] **[CRITICAL] Path traversal** — `/api/output/<filename>` lets Pi read arbitrary files via `../` paths. `UnityComms.cs:263-269`. Fix: `Path.GetFullPath` + prefix enforcement before serving.
- [ ] **[CRITICAL] Bearer token in plaintext** — raw TCP socket exposes token in plaintext on LAN. `UnityComms.cs:16,30-32,191-201`. Plan: TLS/SslStream migration.
- [ ] **[CRITICAL] Exception message leakage** — 500 responses return `ex.Message` verbatim. `UnityComms.cs:300`. Fix: return generic `"Internal server error"` + `Debug.LogException`.
- [ ] **[CRITICAL] JsonUtility null dereference** — `FromJson` returns null on bad JSON, then NRE on `cmd.character`/`cmd.scene`. `UnityComms.cs:226,238`. Fix: try/catch + null guard.

See full findings: `/home/Evan/.hermes/projects/show-runner-review/deliverables/task-01-*.md`

## Known gaps / next steps

- [x] show_runner.py — bridge.play_beat() wired into run_beat() and auto loop (2026-04-21)
- [x] Unity scene — ShowRunnerScene.unity built headless via batch mode (2026-04-21)
- [x] Waypoints — 16 placed and named, tagged "Waypoint" (2026-04-21)
- [x] Character capsules — 6 capsules (susan, richard, gigi, veronica, auntie, morgan_freeman) (2026-04-21)
- [x] Animator Controller — CharacterAnimator.controller created with TalkIntensity, EmotionIntensity, MoveSpeed, Emotion trigger, Idle trigger (2026-04-21)
- [x] NavMesh — baked over full scene geometry via NavMeshSurface.BuildNavMesh() (2026-04-21)
- [ ] Mixamo characters — swap capsule placeholders for humanoid models (requires browser/Adobe account)
- [ ] Animator clips — assign Mixamo animation clips to controller states (Idle, Walk, Talking, Emotion)
- [ ] ProBuilder rooms — replace primitive cubes with proper room geometry (optional)
- [ ] TTS — replace sleep-based timing with audio playback
