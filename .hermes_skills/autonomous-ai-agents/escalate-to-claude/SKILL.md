---
name: escalate-to-claude
description: "Hand off a task to Claude Code when it exceeds MiniMax capability. REQUIRES Evan's explicit permission before routing UNLESS this session was started with --source claude-delegated."
version: 2.0.0
metadata:
  hermes:
    tags: [escalation, claude, handoff, multi-agent, delegation, permission]
    related_skills: [subagent-driven-development, verify-before-write]
---

# Escalate to Claude

## Permission Gate (read this first)

**You MUST ask Evan's permission before routing anything to Claude Code.**

The only exception: if this Hermes session was started via `hermes_dispatch.sh` with `--source claude-delegated`, you are already inside a Claude-initiated roundtrip and may return results to it. Check your session context — the `--source` flag will be visible in how you were invoked.

For every other session (Discord, Terminus/iPhone, cron, gateway, direct terminal): **stop and ask Evan first**. No silent SSH to the PC. No background delegate_task calls. No writing to ESCALATIONS.md and running it. Just ask.

---

## When to Consider Escalating

- Failed the same step twice with different approaches
- Task requires redesigning a public interface or cross-cutting architecture
- Security-sensitive code (auth, secrets, DB schema)
- The diff is >300 lines across >5 files (too much for reliable MiniMax context)
- Ambiguous spec requiring product judgment

## Step 1: Ask Permission

Output this and stop:

```
I need to escalate this to Claude Code — OK to proceed?

Task: <one sentence — what were you trying to do>
Blocker: <exactly what went wrong or what decision is needed>
Tried: <what you attempted, with error messages>
Files: <exact paths>
```

Wait for Evan to respond with "yes" / "go ahead" / equivalent.

## Step 2: After Permission Granted, Route to Claude

```bash
# SSH to PC and run Claude Code with task context
ssh Evan@10.0.0.91 "cd <project-dir> && claude --print '<task description>' 2>&1 | tee /tmp/claude-result.txt"
cat /tmp/claude-result.txt
```

Or write a structured handoff note to the vault (Evan picks it up in Claude):

```bash
cat >> /mnt/nvme/obsidian-vault/ESCALATIONS.md << 'EOF'

## $(date +%Y-%m-%d %H:%M) Escalation from Hermes
Task: <task>
Blocker: <blocker>
Tried: <attempts>
Files: <files>
EOF
bash ~/sync-vault.sh
echo "Handoff written to vault — Evan can pick this up in Claude."
```

## Capability Matrix (pre-task check)

Use this BEFORE starting to decide whether to ask Evan upfront:

| Task type | Handle locally? | Ask before starting? |
|-----------|----------------|----------------------|
| Edit single function | ✅ | No |
| New endpoint, single file | ✅ | No |
| Smoke test / log read | ✅ | No |
| Refactor across 3+ files | ⚠️ | Consider asking |
| Multi-file architecture change | ❌ | Yes — before starting |
| Debug subtle async race | ❌ | Yes — before starting |
| Write DB migrations + backfill | ⚠️ | Yes if complex |
| Security review | ❌ | Yes — before starting |
| Unity C# (no Pi tooling) | ❌ | Yes — route to PC |

If the task is clearly in the "❌" column, don't attempt it first — tell Evan upfront that this needs Claude and ask if you should escalate.
