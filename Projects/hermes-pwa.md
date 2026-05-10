---
name: hermes-pwa
status: active
stack: python, fastapi, uvicorn, websockets, acp
host: 10.0.0.9
port: '9120'
path: /home/Evan/.hermes/pwa
last_updated: 2026-05-09
tags: [pi, pwa, ios, hermes]
---

## Overview
PWA (Progressive Web App) that lets Evan connect to Hermes from his iPhone home screen over Tailscale. Persistent conversations, sidebar history, iOS keyboard support.

## Current State
Working end-to-end:
- FastAPI server on Pi port 9120, served via Tailscale (100.104.189.48:9120)
- One ACP subprocess per chat thread — persistent hermes process, not one-shot
- Per-thread message logs at `~/.hermes/pwa/logs/{tid}.json`
- Thread registry at `~/.hermes/pwa/threads.json`
- CLI handoff: ⌨ button copies `hermes --resume {session_id}` to clipboard
- Active instances chip: polls every 5s, shows RAM/PID/uptime, has kill button
- `sync_session_to_db()` called after each turn so CLI `--resume` works

## Blockers
None known.

## Key Facts
- Server: `~/.hermes/pwa/server.py` (canonical copy at `/home/Evan/hermes-pwa-server.py` on PC)
- Service: `~/.config/systemd/user/hermes-pwa.service` (check if enabled)
- Session files: `~/.hermes/sessions/session_{uuid}.json`
- State DB: hermes internal SQLite (`db.replace_messages()` called post-turn)
- Tailscale IP: 100.104.189.48

## Decisions
- ACP persistent subprocess per thread (not hermes -z one-shot)
- User message appended client-side immediately on send (not waiting for server echo)
- Thread IDs are local UUIDs — separate from hermes session UUIDs
- `--accept-hooks` flag required (hooks_auto_accept was blocking startup)
- Switching chats always allowed even mid-response (removed busy guard from loadThread)
