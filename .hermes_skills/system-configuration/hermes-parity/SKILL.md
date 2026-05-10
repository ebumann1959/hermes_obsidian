---
name: hermes-parity
description: "Protocol for keeping Pi and PC Hermes instances identical. Vault is the canonical source — any skill, rule, or script added to one machine must go through the vault to reach the other."
version: 1.0.0
metadata:
  hermes:
    tags: [parity, sync, multi-machine, pi, pc, vault, protocol]
    related_skills: [hermes-multi-agent-sync, hermes-agent-skill-authoring]
---

# Hermes Parity Protocol

Both Hermes instances (Pi 10.0.0.9 and PC 10.0.0.91) should feel identical. Interacting with one should feel like the other. The vault is the single source of truth — it flows automatically to both machines at session boundaries.

## Architecture

```
     Pi ~/.hermes/skills/          PC ~/.hermes/skills/
            ↑ auto-deploy                  ↑ auto-deploy
  /mnt/nvme/obsidian-vault/    →   /mnt/Data/obsidian_vault/
         .hermes_skills/       GitHub      .hermes_skills/
         scripts/                          scripts/
         SOUL.md                           SOUL.md
```

**What auto-syncs (vault-managed):**
- All skills in `.hermes_skills/`
- Shared scripts (`index_codebase.py`, `hermes-deploy.sh`)
- `SOUL.md` (universal rules — machine identity is injected on deploy)

**What is machine-local by design:**
- `~/.hermes/config.yaml` — config drift is detected and auto-fixed on deploy
- `~/.hermes/agents/` — agent instruction files (deploy manually when changed)
- `~/.hermes/chroma_codebase/` — ChromaDB indexes (run indexer locally per machine)
- `~/.hermes/logs/`, `state.db` — never shared

## Session Boundaries (automatic)

Both machines are wired to run parity automatically:

```
Session start:  bash ~/sync-vault.sh pull
                └─► hermes-deploy.sh (auto-called)
                    ├── deploys new/updated skills from vault
                    ├── deploys scripts
                    ├── deploys SOUL.md (with machine identity)
                    └── detects + fixes config drift

Session end:    on_session_finalize hook fires
                └─► hook_session_finalize.sh
                    ├── WAL checkpoint on state.db
                    └── bash ~/sync-vault.sh (push vault changes)
```

## Adding a New Skill (parity-safe workflow)

```bash
# 1. Write the skill on whichever machine you're on
mkdir -p ~/.hermes/skills/<category>/<name>
cat > ~/.hermes/skills/<category>/<name>/SKILL.md << 'EOF'
---
name: ...
---
# ...
EOF

# 2. Promote to vault (makes it cross-machine)
VAULT=$([ -d /mnt/nvme/obsidian-vault ] && echo /mnt/nvme/obsidian-vault || echo /mnt/Data/obsidian_vault)
mkdir -p "$VAULT/.hermes_skills/<category>/<name>"
cp ~/.hermes/skills/<category>/<name>/SKILL.md "$VAULT/.hermes_skills/<category>/<name>/SKILL.md"

# 3. Push — other machine gets it on next session start
bash ~/sync-vault.sh
```

## Manual Parity Check

```bash
# Check skill parity between vault and local
bash ~/hermes-deploy.sh --check

# Check what's on Pi but not in vault (local-only skills)
diff <(ls /mnt/nvme/obsidian-vault/.hermes_skills/ | sort) \
     <(ls ~/.hermes/skills/ | sort)
# Right-column items = Pi-local only (not synced to PC by design)

# Force full re-deploy from vault
bash ~/hermes-deploy.sh
```

## Config Parity (shared settings)

These settings must match on both machines. `hermes-deploy.sh` auto-fixes them:

| Setting | Value | Why |
|---------|-------|-----|
| `model.provider` | `minimax-coding-plan` | Free coding-optimized endpoint |
| `agent.reasoning_effort` | `high` | Full chain-of-thought on M2.7 |
| `hooks.on_session_finalize` | `hook_session_finalize.sh` | WAL checkpoint + vault sync |

## SOUL.md — Shared Rules, Machine Identity

The vault holds one `SOUL.md` with universal rules. On deploy, the machine identity line is automatically rewritten:
- Pi: `running on the Pi (10.0.0.9)`
- PC: `running on the PC (10.0.0.91, MX25Rig)`

To update shared rules: edit `SOUL.md` on either machine, push vault, both machines get it next session.

## Local-Only Skills (by design)

These skill categories exist on Pi only and are not promoted to vault. That's intentional — they're Pi-specific or unused on PC:

`apple`, `creative`, `data-science`, `devops`, `diagramming`, `dogfood`, `email`, `gaming`, `gifs`, `github`, `inference-sh`, `ios-develop`, `lua-development`, `mcp`, `media`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `yuanbao`

To promote any of these to shared: copy to vault `.hermes_skills/` and push.

## Chroma Indexes (re-index per machine)

Each machine runs its own ChromaDB. After a major refactor, re-index locally:

```bash
# Pi
source ~/.hermes/hermes-agent/venv/bin/activate
python3 ~/.hermes/scripts/index_codebase.py ~/.hermes/show_runner --collection show_runner
python3 ~/.hermes/scripts/index_codebase.py ~/shadys-analytics --collection shadys

# PC (adjust paths)
python3 ~/.hermes/scripts/index_codebase.py /mnt/Data/show_runner/Assets/ShowRunner --collection unity_scripts
python3 ~/.hermes/scripts/index_codebase.py /mnt/Data/shadys-analytics --collection shadys
```
