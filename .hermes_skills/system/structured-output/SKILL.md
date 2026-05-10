---
name: structured-output
description: "Force MiniMax to produce reliable structured output (JSON, diffs, tables) by framing requests precisely. Use when tool results or reports need machine-parseable format."
version: 1.0.0
metadata:
  hermes:
    tags: [structured-output, json, reliability, minimax, prompting]
---

# Structured Output

MiniMax produces more reliable output when you constrain the format explicitly. Use this for any response that will be parsed, stored, or handed to another tool.

## Pattern 1: JSON Output

Wrap the instruction in a JSON schema contract:

```
Respond with ONLY valid JSON. No prose before or after. No markdown fences.
Schema:
{
  "status": "pass" | "fail",
  "files_changed": ["path1", "path2"],
  "summary": "one sentence"
}
```

Test your parser before relying on it:
```python
import json
try:
    result = json.loads(model_output)
except json.JSONDecodeError as e:
    print(f"Model produced invalid JSON: {e}")
    # Retry with stricter prompt or extract with regex
```

## Pattern 2: Unified Diff

When asking for code changes, request diff format:

```
Show changes as a unified diff only. No explanations. Format:
--- a/<filepath>
+++ b/<filepath>
@@ ... @@
 context
-removed line
+added line
```

Apply with:
```bash
echo "<diff_output>" | patch -p1
# or
git apply <<< "<diff_output>"
```

## Pattern 3: Checklist / Table

For status reports, force table or checklist format:

```
Output a markdown checklist only:
- [x] task if complete
- [ ] task if incomplete
No prose.
```

## Pattern 4: One-Line Answer

When you need a single value (a path, a command, a boolean):

```
Answer with EXACTLY ONE LINE. No explanation. No newline at the end.
Example format: /home/Evan/.hermes/show_runner/core/dialogue_engine.py
```

## Retry Strategy

If the model ignores the format constraint:
1. Repeat the format instruction at the END of the prompt (models anchor to recency)
2. Add "IMPORTANT: violating this format means your answer is wrong"
3. If still failing after 2 tries, extract with regex rather than expecting perfect JSON
