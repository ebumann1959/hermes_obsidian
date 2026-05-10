---
name: escalate-to-claude
description: "Package and hand off a task to Claude Code (PC) when it exceeds MiniMax/Hermes capability. Use when stuck, when scope is ambiguous, or when a decision requires architecture-level reasoning."
version: 1.0.0
metadata:
  hermes:
    tags: [escalation, claude, handoff, multi-agent, delegation]
    related_skills: [subagent-driven-development, verify-before-write]
---

# Escalate to Claude

When MiniMax has hit its limit, hand off cleanly to Claude Code running on the PC. Don't struggle past 2 failed attempts — escalate early.

## When to Escalate

- Failed the same step twice with different approaches
- Task requires redesigning a public interface or cross-cutting architecture
- Security-sensitive code (auth, secrets, database schema changes)
- Ambiguous spec that needs Evan's input before proceeding
- QA-Hermes flagged a structural issue the coder can't resolve
- Diff > 300 lines across > 5 files (too much for reliable MiniMax context)

## Escalation Format

Produce this block and stop:

```
ESCALATE TO CLAUDE
==================
Task: <one sentence — what were you trying to do?>
Blocker: <exactly what went wrong or what decision is needed>
Attempts: <what you tried — be specific, include error messages>
Files: <exact paths involved>
State: <what is currently working vs broken>
Suggested next step: <your best guess at what Claude should try>
==================
```

## How to Actually Route to Claude

```bash
# Option 1: SSH to PC and launch Claude Code with context
ssh Evan@10.0.0.91 "cd <project-dir> && claude --print '<task description>' 2>&1 | tee /tmp/claude-result.txt"
cat /tmp/claude-result.txt

# Option 2: Write the escalation to the vault for Evan to pick up
cat >> /mnt/nvme/obsidian-vault/ESCALATIONS.md << 'EOF'

## $(date +%Y-%m-%d) Escalation from Hermes
Task: <task>
Blocker: <blocker>
Files: <files>
EOF
bash ~/sync-vault.sh
```

## Capability Matrix

Use this to decide whether to escalate BEFORE starting:

| Task type | MiniMax OK? | Escalate? |
|-----------|-------------|-----------|
| Edit single function | ✅ | No |
| Add a new endpoint | ✅ | No |
| Refactor across 3+ files | ⚠️ | Probably |
| Multi-file architecture change | ❌ | Yes |
| Debug a subtle async race | ❌ | Yes |
| Write migrations + backfill | ⚠️ | If complex |
| Smoke test / log read | ✅ | No |
| Security review | ❌ | Yes |
| Unity C# (no Pi tooling) | ❌ | Yes → PC |
