#!/bin/bash
# hermes-deploy.sh — deploy vault skills + shared config to local Hermes
# Usage: bash ~/hermes-deploy.sh [--check | --fix]

set -euo pipefail

MODE="deploy"
[[ "${1:-}" == "--check" ]] && MODE="check"
[[ "${1:-}" == "--fix" ]]   && MODE="fix"

# ── Detect machine ───────────────────────────────────────────────────────────
if grep -q "Raspberry" /sys/firmware/devicetree/base/model 2>/dev/null \
   || [[ "$(hostname)" == *"raspberry"* ]] || [[ "$(hostname)" == "pi"* ]]; then
    MACHINE="pi"
    VAULT_DIR="/mnt/nvme/obsidian-vault"
else
    MACHINE="pc"
    VAULT_DIR="/mnt/Data/obsidian_vault"
fi

SKILLS_SRC="$VAULT_DIR/.hermes_skills"
SKILLS_DST="$HOME/.hermes/skills"
SCRIPTS_SRC="$VAULT_DIR/scripts"
SCRIPTS_DST="$HOME/.hermes/scripts"
HERMES_CFG="$HOME/.hermes/config.yaml"
VAULT_SOUL="$VAULT_DIR/SOUL.md"
LOCAL_SOUL="$HOME/.hermes/SOUL.md"

NEW=0; UPDATED=0; UNCHANGED=0
log()  { echo "[hermes-deploy] $*"; }
warn() { echo "[hermes-deploy] WARN: $*" >&2; }

# ── 1. Skills ────────────────────────────────────────────────────────────────
log "Deploying skills ($MACHINE, mode=$MODE)..."
if [ -d "$SKILLS_SRC" ]; then
    while IFS= read -r -d '' src; do
        rel="${src#$SKILLS_SRC/}"
        dst="$SKILLS_DST/$rel"
        if [ ! -f "$dst" ]; then
            if [ "$MODE" != "check" ]; then mkdir -p "$(dirname "$dst")"; cp "$src" "$dst"; fi
            log "NEW: $rel"; NEW=$((NEW+1))
        elif ! diff -q "$src" "$dst" > /dev/null 2>&1; then
            if [ "$MODE" != "check" ]; then cp "$src" "$dst"; fi
            log "UPDATED: $rel"; UPDATED=$((UPDATED+1))
        else
            UNCHANGED=$((UNCHANGED+1))
        fi
    done < <(find "$SKILLS_SRC" -name "SKILL.md" -print0 2>/dev/null)
fi

# ── 2. Scripts ───────────────────────────────────────────────────────────────
if [ -d "$SCRIPTS_SRC" ] && [ "$MODE" != "check" ]; then
    mkdir -p "$SCRIPTS_DST"
    for f in "$SCRIPTS_SRC"/*.py "$SCRIPTS_SRC"/*.sh; do
        [ -f "$f" ] || continue
        dst="$SCRIPTS_DST/$(basename "$f")"
        if ! diff -q "$f" "$dst" > /dev/null 2>&1; then
            cp "$f" "$dst" && chmod +x "$dst"
            log "SCRIPT: $(basename "$f")"
        fi
    done
fi

# ── 3. SOUL.md (shared rules, machine identity injected) ─────────────────────
if [ -f "$VAULT_SOUL" ] && [ "$MODE" != "check" ]; then
    cp "$VAULT_SOUL" "$LOCAL_SOUL"
    if [ "$MACHINE" = "pi" ]; then
        sed -i "s/running on the PC (10.0.0.91, MX25Rig)/running on the Pi (10.0.0.9)/" "$LOCAL_SOUL" 2>/dev/null || true
        sed -i "s/running on the PC/running on the Pi (10.0.0.9)/" "$LOCAL_SOUL" 2>/dev/null || true
    else
        sed -i "s/running on the Pi (10.0.0.9)/running on the PC (10.0.0.91, MX25Rig)/" "$LOCAL_SOUL" 2>/dev/null || true
        sed -i "s/running on the Pi/running on the PC (10.0.0.91, MX25Rig)/" "$LOCAL_SOUL" 2>/dev/null || true
    fi
fi

# ── 4. Config drift ──────────────────────────────────────────────────────────
DRIFT=()
if [ -f "$HERMES_CFG" ]; then
    grep -q "provider: minimax-coding-plan" "$HERMES_CFG" || DRIFT+=("provider")
    grep -q "reasoning_effort: high"        "$HERMES_CFG" || DRIFT+=("reasoning_effort")
    grep -q "on_session_finalize"           "$HERMES_CFG" || DRIFT+=("hook")
fi

if [ ${#DRIFT[@]} -gt 0 ]; then
    warn "Config drift: ${DRIFT[*]}"
    if [ "$MODE" = "fix" ] || [ "$MODE" = "deploy" ]; then
        python3 - "$HERMES_CFG" << 'PYEOF'
import re, sys
cfg = sys.argv[1]
with open(cfg) as f: c = f.read()
orig = c
c = re.sub(r"^(model:\n  default: MiniMax-M2\.\d+\n  provider: )minimax$",
           r"\1minimax-coding-plan", c, count=1, flags=re.MULTILINE)
c = re.sub(r"^  reasoning_effort: medium$", "  reasoning_effort: high",
           c, flags=re.MULTILINE)
if "on_session_finalize" not in c:
    c = c.replace("hooks: {}",
        "hooks:\n  on_session_finalize:\n    - command: /home/Evan/.hermes/scripts/hook_session_finalize.sh\n      timeout: 60")
if c != orig:
    with open(cfg, "w") as f: f.write(c)
    print("[hermes-deploy] Config drift fixed")
PYEOF
    else
        warn "Run: bash ~/hermes-deploy.sh --fix"
    fi
fi

# ── 5. Summary ───────────────────────────────────────────────────────────────
log "Skills: +$NEW new  ~$UPDATED updated  $UNCHANGED unchanged"
log "Done ($MACHINE)"
