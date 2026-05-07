# Show Runner — Architecture & Design

**Migrated:** 2026-04-20 from `~/.hermes/context/SHOW_RUNNER_CONTEXT.md`
**Last updated:** 2026-04-12 (original), verified 2026-04-20

---

## What It Is

A real-time AI-driven character simulation platform. Multiple animated personas exist in a shared neighborhood environment (Unity/PC), interact autonomously based on their personalities and relationships, and can be directed by Evan at any time. Think: a soap opera you can steer, with characters who have genuine emotional stakes in each other.

## Infrastructure

| Machine | IP | Role |
|---------|----|------|
| Pi (Shadys-Gamblin-Corner) | 10.0.0.9 | AI brains, coordination, persona runners |
| PC (MX25Rig) | 10.0.0.91 | Unity with animated character models |

- **Communication:** SSH between Pi↔PC
- **Bridge:** HTTP bidirectional. Pi POSTs to Unity (10.0.0.9:8080).

## Architecture Overview

```
[EVAN] → prompts, scene definitions, steer injection
           │
           ▼
    ┌─────────────────────┐
    │   SHOW RUNNER CORE   │  (Pi side)
    │  /home/Evan/show_runner/
    │  • scene_state.py     ← tracks: character positions, rooms, objects
    │  • turn_manager.py     ← whose turn to speak/act
    │  • dialogue_engine.py  ← LLM: generates dialogue + action
    │  • relationship_graph.py ← dynamic relationships from vault
    │  • director.py         ← Evan can steer scene-wide or per-char
    │  • unity_bridge.py     ← sends commands to Unity
    └──────────┬──────────┘
               │ (bridge TBD)
               ▼
    ┌─────────────────────┐
    │     UNITY SIDE       │  (PC side)
    │ /home/Evan/show_runner/My project/Assets/show_runner/
    │  • Animated models    ← pre-made, later custom
    │  • Scene geometry     ← house(s), lawn, driveway, street
    │  • ActionExecutor     ← interprets and applies animation/gesture commands
    │  → SensorData         ← sends back world state to Pi
    └─────────────────────┘
```

## Core Concepts

### Scenes

Evan defines a scene via prompt:
> "Kitchen: Richard at the table reading the paper, Susan at the stove cooking burgers, Gigi at the front door wanting to borrow sugar"

A **Scene** is a location (Room) containing:
- **Characters** (who's present, their positions)
- **Objects** (relevant props, furniture)
- **Atmosphere** (lighting, mood, time of day)

Example locations: kitchen, living room, front lawn, driveway, across the street (Gigi's place)

### Turn System

All characters are **simultaneously present and aware**, but speak **one at a time** to avoid overlapping dialogue.

- Turn order: managed by TurnManager (can be influenced by who's engaged, proximity, emotional tension)
- Evan can interrupt with "Susan snaps at Richard" → forces Susan's turn immediately
- Characters can **exit** a room → automatically removed from that scene context
- Characters entering a room → added to active scene context

### Dialogue + Action

LLM generates both:
- **Dialogue:** what the character says
- **Action/Gesture:** what they do while saying it (e.g. "*stirs aggressively*", "*puts down the spatula and goes quiet*")

Unity maps action tags to animation triggers.

### World State (Real-time)

Continuously updated:
- Which characters are in which rooms
- Object states ("the burgers are burning", "the TV is on")
- Character states ("Gigi is leaning against the doorframe", "Susan has her arms crossed")
- Proximity / spatial relationships ("Richard is sitting next to Susan at the table")

### Emotional Graph

Each persona has a **Relationship Matrix** (from vault). These are dynamic:
- Love, resentment, jealousy, curiosity — all tracked per-character-pair
- Shifts based on what actually happens in scenes
- Affects what characters say, how they react, what triggers them

### Direction / Injection

Evan can inject at any time:
- **Scene-wide:** "make it awkward", "introduce a fight"
- **Character-specific:** "Susan suddenly brings up the prom", "Gigi gets defensive"
- **Temporal:** "fast forward to dinner", "skip to the argument"

## Character Roster

| Character | Brief | Status |
|-----------|-------|--------|
| Susan | Mid-40s, tired, nags as love language, jealous, catty | Active |
| Richard | Exhausted husband, checked out, sighs at everything | Active |
| Gigi | Hot younger neighbor, dismissive, living free | Active — **was Becky, renamed** |
| Veronica | Scary cholla neighbor, wild dogs | Active |
| Morgan Freeman | Narrator voice — omniscient observer of #nonsense. Posts [* scene narration *] between beats and across scenes. Lives in the vault. | Active |
| Auntie | Elder figure, Sunday best energy | Active |

## Character State System

Each character has independent emotional/behavioral axes, each 0–10:

| Axis | Description |
|------|-------------|
| drunk | slurred speech, lowered filter, emotional intensity |
| angry | clipped, sharp, escalating |
| stressed | tight, distracted, short fuse |
| frustrated | tired of trying, giving up |
| calm | centered, present, more honest |
| sad | quiet, withdrawn, things surface |
| horny | bold, flirty, heightened awareness |
| anxious | nervous energy, overthinking, physical tells |
| grief | heavy, slow, everything reminds them of loss |
| ... | extensible |

**Stacking:** States combine. drunk+angry = different from drunk alone. drunk+angry+calm = conflicted, unpredictable.

**Injection syntax:**
```
/susan drunk=7 angry=3     — set multiple states at once
/susan calm=8              — override calm level
/susan -drunk              — remove state entirely
/susan +horny              — add or increase (default 5)
"make Susan have a rough day" — natural language
```

**Persistence:**
- Arc-level states (grief, long-running resentment) persist across sessions until Evan explicitly adjusts
- Scene-level states (drunk, temporary anger) reset at scene boundaries unless specified

## Layered Objectives

| Level | Scope | Example | Duration |
|-------|-------|---------|----------|
| Arc | Full character journey | "Susan is deciding whether to leave Richard" | Season/series |
| Episode | Session arc | "Tonight's dinner is about the prom" | One session |
| Scene | Moment-to-moment | "Susan wants Richard to admit he was wrong" | One scene |
| Beat | Single exchange | "Susan pushes, Richard deflects" | One turn |

## Design Decisions

| Question | Decision |
|----------|----------|
| Turn order | Simultaneous presence, sequential speaking. TurnManager picks active speaker based on proximity, tension, silence duration, or Evan's override. |
| Action format | Tags embedded in dialogue: `*stirs aggressively* These burgers are FINE, Richard` |
| SceneState authority | Pi owns canonical world state. Unity sends position updates as ground truth. DialogueEngine reads from SceneState. |
| Scene definition | Evan defines via text prompts. System parses: room, characters + positions, objects, atmosphere. |
| Memory | Keep vault format. Persist across sessions. |
| Bridge protocol | HTTP (commands, existing) + WebSocket (events, planned upgrade). Pi drives via HTTP POST; Unity pushes positions + events via WebSocket. See `/home/Evan/.hermes/vault/z-suite/teams/a/runs/2026-04-27-realtime-agent-arch-plan.md` for full plan. |
| Direction style | Interpretive — characters reframe Evan's injections through their own voice/state |
| State vs. Relationship | Separate systems both feeding the prompt; significant events shift both |
