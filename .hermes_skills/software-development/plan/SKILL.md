---
name: plan
description: "Read and check an existing plan from .hermes/plans/. Use at the start of a session to orient before touching code."
version: 1.0.0
metadata:
  hermes:
    tags: [planning, workflow, orientation]
---

# Plan Reader

Load and orient from an existing plan before starting work.

## Usage

```bash
# List available plans
ls ~/.hermes/plans/ 2>/dev/null || echo "No plans directory yet"

# Read the active plan
cat ~/.hermes/plans/<task-name>.md

# Check off a completed task (in-place edit)
sed -i 's/- \[ \] <task text>/- [x] <task text>/' ~/.hermes/plans/<task-name>.md
```

## Session Start Ritual
1. `ls ~/.hermes/plans/` — what plans exist?
2. Read the relevant plan — what's the current task?
3. Check git status — where did the last session leave off?
4. Only then start working

## Keeping Plans Current
- Check off tasks as they complete (don't batch)
- Add tasks discovered mid-implementation under a `## Discovered` section
- Never delete rejected tasks — move them to Paths with a note
- Archive completed plans to `.hermes/plans/archive/` when the feature ships
