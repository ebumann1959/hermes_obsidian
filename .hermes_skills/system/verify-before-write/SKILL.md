---
name: verify-before-write
description: "Mandatory pre-flight checklist before editing any file. Prevents hallucinated paths, unintended overwrites, and scope creep. Load this at the start of any coding task."
version: 1.0.0
metadata:
  hermes:
    tags: [safety, quality, files, guardrails, minimax]
---

# Verify Before Write

MiniMax (and small models generally) hallucinate file paths, function signatures, and API shapes. This skill prevents those errors from silently shipping.

## The Rule

**You may not edit a file you have not read in this session.**

## Pre-flight Checklist (run before EVERY file edit)

```bash
# 1. File exists?
ls -la <path>

# 2. Read the section you're about to change
sed -n '<start>,<end>p' <path>
# or for a function
grep -n "def <function_name>\|class <ClassName>" <path>

# 3. Check imports/dependencies actually exist
grep -n "from \|import " <path> | head -20

# 4. Understand the current behavior before changing it
# Ask: what does this code do RIGHT NOW?
```

## Post-edit Checklist

```bash
# 1. Review what you actually changed
git diff <path>

# 2. Did you touch only the files in scope?
git diff --stat

# 3. Does the file still parse?
python3 -m py_compile <path>   # for Python
node --check <path>            # for JS/TS

# 4. Run the narrowest test that covers your change
python3 -m pytest tests/test_<module>.py -x -q
```

## When to Stop and Ask

Stop editing and output ESCALATE if:
- The file doesn't exist at the expected path
- The function/class you were told to edit isn't there
- The current code is materially different from what was described in the task
- Your change requires touching a file outside the stated scope
