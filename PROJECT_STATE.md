# Project State

> **Source of truth:** All project context now lives in this vault. `~/.hermes/context/` is deprecated — migrated 2026-04-20.
> See `SYSTEM/` for system snapshots, `SHOW_RUNNER/ARCHITECTURE.md` for show runner design.

## Hardware
- Full details: `SYSTEM/system.md` (Pi), `SYSTEM/pc.md` (PC)
- **Pi** (Shadys-Gamblin-Corner): 10.0.0.9, RPi 5, 16GB, aarch64
- **PC** (MX25Rig): Evan@10.0.0.91, Ryzen 7 5800X3D, 32GB RAM, AMD RX 7900 XT, /mnt/Data (3.7TB)

## Active Projects

### Discord Persona Bots (Pi 10.0.0.9)
- Full details: `SYSTEM/personas.md`
- Gigi + Veronica in #nonsense (ch 1491728632740315176)
- Runner: `runner.py --persona {name} --continuous --interval 30`
- Reload: `touch /tmp/{name}.reload`
- morgan_freeman_runner.py = narrator, NOT for Gigi/Veronica

### Show Runner — Pi (repo only)
- Repo: `/home/shady/.hermes/show_runner/` (branch: master)
- Flask UI: `/home/shady/.hermes/show_runner/show_runner_ui.py`
- Restart: `ssh shady@10.0.0.9 'pkill -f show_runner_ui.py; cd /home/shady/.hermes/show_runner && /home/shady/.hermes/hermes-agent/venv/bin/python3 show_runner_ui.py > /tmp/sr_ui.log 2>&1 &'`

### Unity Show Runner (PC)
- Project: `/mnt/Data/show_runner/` (canonical — 2026-04-29)
- Frame out: `/mnt/Data/show_runner_frames/`
- Port: 8080
- OLD path `/home/Evan/show_runner/My project/` — DELETED, never use
- Certs missing — `/home/Evan/show_runner/comms.pfx` not found, needs regeneration

## Infrastructure
- GitHub repo: ssh://git@github.com/ebumann1959/show_runner.git
- Git SSH fix: `protocol.version 0` applied on Pi
- Obsidian vault: `/mnt/nvme/obsidian-vault/` (.env fixed 2026-04-20)

## Division of Labor
- **This agent**: Pi→PC pipeline, system/infrastructure
- **Other Hermes**: scene scripting

## Known Issues / TODOs
- Gateway Discord connection: startup_failed — may need re-auth
- Gigi+Veronica runners may need restart after audit

## Conky / CM2
- Full details: `SYSTEM/cm2-display-fix.md`
- Always use `pkill conky` NOT `killall conky`

## Last Updated
2026-04-20 — full system audit, memory + .env corrected, vault paths fixed

## 2026-04-28

### UnityComms.cs Security Audit — COMPLETED
- All 5 vulnerabilities addressed (see SESSION_LOG)
- V2 TLS: staged, not yet implemented
- Unity Editor: running on PC (PID 474857)
- Source file: /home/Evan/show_runner/My project/Assets/show_runner/UnityComms.cs
- Certs: /home/Evan/show_runner/comms.{pfx,cert,key}.pem
