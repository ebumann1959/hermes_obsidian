---
name: scope-check
description: "Verify an agent stayed within task scope before marking done. Catches unintended file changes, dependency additions, and feature creep from MiniMax."
version: 1.0.0
metadata:
  hermes:
    tags: [scope, quality, safety, guardrails, git, minimax]
---

# Scope Check

MiniMax loves to "improve" things that weren't asked. This skill catches scope creep before it ships.

## The Rule

**If a file wasn't mentioned in the task, you may not change it.**

Exception: if changing file A requires updating file B's import (e.g., a rename), that's acceptable — but document it in your completion comment.

## Pre-commit Scope Verification

Run this BEFORE every commit:

```bash
# List every file you changed
git diff --stat HEAD

# Expected output: only files mentioned in the task
# Unexpected files = scope violation, do not commit
```

## For the Agent (self-check)

Before marking any task done, answer these:

1. `git diff --stat` — how many files changed?
2. Are ALL of them in the task description?
3. Did you add any new dependencies (`pip install`, `import`, `require()`)?
4. Did you change any config or env files not in scope?
5. Did you modify any tests that weren't about your change?

If any answer raises a flag: **do not commit, report what happened**.

## For Reviewer / QA

```bash
# Check the diff against the ticket scope
git show HEAD --stat

# Flag any file that looks wrong
# Common MiniMax violations:
# - editing __init__.py when not asked
# - "improving" adjacent functions in the same file
# - adding logging/comments to files outside scope
# - changing requirements.txt without being asked to add a dep
```

## Unstaging Out-of-Scope Changes

If you accidentally staged files you shouldn't have:

```bash
# Unstage a specific file (keeps your changes locally)
git restore --staged <filepath>

# If you already committed: create a revert for just that file
git show HEAD:<filepath> > /tmp/original.py
# Edit the file back to original, then amend or create a new commit
```

## Note, Don't Fix

If you notice something outside scope that should be fixed:

```
SCOPE NOTE: while working on <task>, I noticed <issue> in <file>.
Not fixing it — out of scope. Recommend creating a separate task.
```

Never silently "fix" something that wasn't asked.
