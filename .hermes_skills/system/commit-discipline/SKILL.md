---
name: commit-discipline
description: "Git commit rules for Hermes agents: one logical change per commit, conventional messages, pull-before-push, never force-push main. Prevents merge disasters on shared repos."
version: 1.0.0
metadata:
  hermes:
    tags: [git, commits, discipline, workflow, safety]
---

# Commit Discipline

## The Rules

1. **One logical change per commit** — if `git diff --stat` shows files from two different concerns, split into two commits
2. **Pull before push** — always `git pull --rebase origin main` (or the current branch) before pushing
3. **Never force-push main** — if you need to `--force`, you've made a mistake; escalate instead
4. **Conventional commit messages** — format enforced below
5. **No "WIP" or "fix" commits on main** — they hide what changed; use a branch if the work is unfinished

## Commit Message Format

```
<type>(<scope>): <short description>

[optional body — what and why, not how]
```

Types:
- `feat` — new feature
- `fix` — bug fix
- `refactor` — code change that isn't a feature or fix
- `test` — adding or fixing tests
- `chore` — build, deps, config
- `docs` — documentation only

Scope = the module or file area (e.g., `dialogue_engine`, `ws_bridge`, `shadys/sports`)

Examples:
```
feat(dialogue_engine): extract retry logic into helper function
fix(ws_bridge): handle reconnect when client sends malformed frame
chore(deps): pin chromadb to 0.4.22 for Pi arm64 compatibility
```

## Pre-Push Checklist

```bash
# 1. See what you're about to push
git log origin/main..HEAD --oneline

# 2. Pull latest (rebase keeps history clean)
git pull --rebase origin main

# 3. Run tests one more time
python3 -m pytest tests/ -x -q 2>/dev/null | tail -10

# 4. Push
git push origin <branch>
```

## GitHub SSH Note (Pi-specific)

If `git push` hangs interactively:
```bash
git config --global protocol.version 0
```
This prevents the interactive protocol negotiation that hangs on push.

## Vault Changes

After any vault edit, sync:
```bash
bash ~/sync-vault.sh
```
The vault sync uses git internally — same rules apply.
