---
name: requesting-code-review
description: "Self-review checklist before committing. Run through this before every commit or PR to catch regressions and quality issues."
version: 1.0.0
metadata:
  hermes:
    tags: [code-review, quality, checklist, git]
---

# Requesting Code Review

Run this checklist before marking any task done. MiniMax should self-review before reporting completion to Evan.

## Pre-commit Checklist

```bash
# 1. See what changed
git diff --stat
git diff

# 2. Check for obvious mistakes
grep -rn "TODO\|FIXME\|HACK\|XXX\|print(\|console.log(" <changed-files>

# 3. Run tests if they exist
python3 -m pytest tests/ -x -q 2>/dev/null || echo "no pytest"

# 4. Verify the feature works end-to-end (not just "it compiles")
# Run the actual smoke test or the verification from the plan
```

## Self-Review Questions (answer each before committing)

1. **Does it do what the task said?** Re-read the task. Test the exact case described.
2. **Did I change more than asked?** `git diff --stat` — anything unexpected?
3. **Does the happy path work?** Run it.
4. **Does an edge case break it?** Empty input, network down, file missing?
5. **Did I introduce a hardcoded path/credential?** `grep -r "10.0.0\|password\|api_key" <changed-files>`
6. **Did I remove anything I shouldn't have?** `git diff | grep "^-" | grep -v "^---"`

## Escalate to Evan/Claude When
- Review reveals a design flaw (not a typo)
- Test is failing and root cause is unclear after 10 minutes
- The change is larger than expected and needs sign-off
- You're not confident the approach is correct

See `escalate-to-claude` skill for escalation format.
