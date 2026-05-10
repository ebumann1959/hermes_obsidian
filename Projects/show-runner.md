---
name: show-runner
status: active
stack: python, unity6, websockets, minimax
host: 10.0.0.9
port: '8765'
path: /home/Evan/.hermes/show_runner
last_updated: 2026-05-09
tags: [pi, pc, unity, ai, soap-opera]
---

## Overview
Two-machine AI soap opera director. Pi (10.0.0.9) is the narrative brain + WebSocket server. PC (10.0.0.91, MX25Rig) runs the Unity 6 renderer.

## Current State
End-to-end pipeline confirmed working as of 2026-04-30:
- Pi → MiniMax-M2.5 → dialogue beat (5–25s)
- Pi → WebSocket → Unity → speech bubble (billboard, font 22, 6s)
- Camera holds on speaker, returns wide after 8s silence
- Telemetry: SpatialBroadcaster → ws_bridge → spatial_context injected into every prompt
- Walls 1m so wide camera sees kitchen/living-room props

## Blockers
None known.

## Key Facts
- Pi show_runner path: `/home/Evan/.hermes/show_runner/`
- Unity project (PC): `/mnt/Data/show_runner/` (canonical — /home/Evan/Projects/show_runner was deleted)
- Inject file: `/tmp/sr_inject.txt`
- Log: `/tmp/sr_runner.log`
- LLM: MiniMax-M2.5 (`MINIMAX_API_KEY` in `/home/Evan/.hermes/.env`)
- Endpoint: `https://api.minimax.io/v1`
- Personalities: `/home/Evan/.hermes/show_runner/personality-vault/` (gigi, veronica, susan, richard, auntie, morgan_freeman)
- Restart: `cd /home/Evan/.hermes/show_runner && nohup /home/Evan/.hermes/hermes-agent/venv/bin/python3 -u show_runner.py > /tmp/sr_runner.log 2>&1 &`
- Full dev detail in Hermes skill: `/home/Evan/.hermes/skills/domain/show-runner-dev/SKILL.md`

## Decisions
- MiniMax-M2.5 not M2.7-highspeed (not on plan) and not M2.1 (content-filter gaps for Susan)
- Direct OpenAI client, NOT subprocess for LLM calls
- Single-client WebSocket rule (ws_bridge)
- SpatialBroadcaster is the sole telemetry source — do not call StartTelemetry from ShowRunnerClient
- Walls at 1m (architectural — needed for camera sight lines)
