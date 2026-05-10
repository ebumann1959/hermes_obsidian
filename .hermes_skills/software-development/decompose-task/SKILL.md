---
name: decompose-task
description: "Break any multi-file task into a written sequence of single-file atomic steps before touching code. Converts multi-file complexity into a series of verifiable single-file operations."
version: 1.0.0
metadata:
  hermes:
    tags: [planning, decomposition, multi-file, reliability, orchestration]
    related_skills: [writing-plans, diff-workflow, subagent-driven-development]
---

# Decompose Task

Multi-file changes fail because context gets too large and MiniMax loses track of what's changed. The fix: decompose first, execute one file at a time, verify between each step.

## When to Use

Any task that touches more than 2 files. Do not start coding until the decomposition is written.

## Step 1: Write the Decomposition (before any code)

```markdown
## Decomposition: <task name>

### Files affected
1. `path/to/file_a.py` — <what changes and why>
2. `path/to/file_b.py` — <what changes and why>
3. `path/to/test_a.py` — <what changes and why>

### Execution order (dependencies first)
1. [ ] Edit `file_a.py`: <specific change — one verb, one thing>
   Verify: `python3 -m py_compile file_a.py && pytest tests/test_a.py -x -q`
2. [ ] Edit `file_b.py`: <specific change>
   Verify: `python3 -m py_compile file_b.py`
3. [ ] Update `test_a.py`: add test for <new behavior>
   Verify: `pytest tests/test_a.py -x -v`

### Integration verify (after all steps)
<one command that proves the full feature works>
```

Save to `.hermes/plans/<task-name>.md` before proceeding.

## Step 2: Execute One Step at a Time

For each step in order:
1. Load ONLY that file's context (`sed -n` for relevant section)
2. Make the change (use diff-workflow skill)
3. Run the step's verify command — must pass before moving on
4. Check off the step in the decomposition
5. Only then load the next file

**Never have two files open and dirty simultaneously.**

## Step 3: Integration Verify

After all steps are checked off, run the full integration test from the decomposition.

```bash
# If something fails here, check off-marks — did a step's verify actually pass?
# Roll back the last step: git diff <file>, git checkout <file>
```

## Decomposition Rules

- Each step has **one verb** (edit, add, rename, delete) and **one file**
- Steps are ordered by dependency (what other steps need it must come first)
- Every step has a concrete verify command — not "check if it works"
- If you can't write a verify command for a step, the step is too vague — split it

## Red Flags (rewrite your decomposition)

- A step says "update X and Y" — split into two steps
- A step has no verify command — make it testable
- Steps 3+ depend on step 1 AND step 2 simultaneously — you may need a different order
- More than 7 steps — probably two separate tasks, do them separately
