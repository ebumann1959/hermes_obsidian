---
name: diff-workflow
description: "Produce unified diffs instead of rewriting files directly. Eliminates hallucination of file content — MiniMax only reasons about the delta. Use for any file edit."
version: 1.0.0
metadata:
  hermes:
    tags: [diff, patch, editing, reliability, multi-file, minimax]
    related_skills: [verify-before-write, scope-check]
---

# Diff Workflow

Instead of rewriting a file from memory (where MiniMax hallucinates), produce a unified diff of only what changes. A script applies it. The model only needs to reason about the delta — not reconstruct the whole file.

## Step 1: Read the Target Section

```bash
# Read only the lines you need to change — not the whole file
sed -n '45,80p' path/to/file.py
# or
grep -n "def function_name" path/to/file.py
sed -n '<line>,<line+30>p' path/to/file.py
```

## Step 2: Produce the Diff (not the full file)

Output ONLY a valid unified diff. Nothing before or after it.

```diff
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -52,7 +52,9 @@
     existing context line
     existing context line
-    old line to remove
+    new line to add
+    another new line
     existing context line
```

Rules for valid diffs:
- Context lines (no prefix) must match the file exactly — copy-paste from `sed` output
- Line counts in `@@ -L,N +L,N @@` must be accurate (L=start line, N=lines in hunk)
- Use one hunk per contiguous change; multiple hunks for non-adjacent changes

## Step 3: Apply the Diff

```bash
# Dry-run first — confirms it applies cleanly
patch --dry-run -p1 < /tmp/change.patch

# Apply if dry-run passed
patch -p1 < /tmp/change.patch

# Or with git apply (cleaner error messages)
git apply --check /tmp/change.patch && git apply /tmp/change.patch
```

## Step 4: Verify

```bash
# Confirm the change looks right
git diff path/to/file.py

# Parse check
python3 -m py_compile path/to/file.py

# Run narrowest relevant test
python3 -m pytest tests/test_<module>.py -x -q
```

## Multi-File Changes

Produce one diff per file. Apply and verify each separately before moving to the next. Never batch-apply multi-file diffs without intermediate verification.

```bash
# Apply file 1, verify
patch -p1 < /tmp/change_file1.patch
python3 -m py_compile path/to/file1.py

# Apply file 2, verify
patch -p1 < /tmp/change_file2.patch
python3 -m py_compile path/to/file2.py

# Then run integration test
```

## When the Diff Rejects

```bash
patch -p1 < /tmp/change.patch
# "Hunk #1 FAILED" → context lines don't match
# Fix: re-read the file, regenerate the diff with correct context
sed -n '<line-3>,<line+10>p' path/to/file.py  # re-read context
```

Never force-apply a rejected patch. Regenerate the diff.
