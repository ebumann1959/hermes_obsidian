---
name: subagent-driven-development
description: "Orchestrate parallel subagents for independent workstreams. Use delegate_task patterns to split work, then aggregate results."
version: 1.0.0
metadata:
  hermes:
    tags: [subagent, orchestration, parallel, delegation, multi-agent]
---

# Subagent-Driven Development

Use subagents when a task has two or more truly independent workstreams that can run in parallel. Don't use them for sequential tasks — overhead isn't worth it.

## When to Subagent

- ✅ "Write tests for A AND refactor B" — independent, parallelize
- ✅ "Search three different APIs and combine results" — independent I/O
- ❌ "Read file X, then update file Y based on it" — sequential, stay inline
- ❌ Any task under ~5 minutes — overhead exceeds benefit

## Spawning a Subagent

```python
# Via hermes delegate_task (if available in your session)
result = await delegate_task(
    agent="coder-hermes",
    task="Refactor dialogue_engine.py to extract retry logic into a helper. "
         "Files: ~/.hermes/show_runner/core/dialogue_engine.py. "
         "Constraint: do not change the public API. "
         "Return: unified diff of changes."
)
```

Or via the CLI:
```bash
hermes subagent "task description here" --agent coder-hermes
```

## Writing Good Subagent Tasks

Every subagent task needs:
1. **What to do** — specific, not vague ("refactor X" → "extract Y into helper Z")
2. **Files to touch** — exact paths, not "the dialogue engine"
3. **Constraints** — what NOT to change (public API, interfaces, other files)
4. **Return format** — diff, summary, JSON, file path?

## Aggregating Results

```bash
# Collect results from parallel agents
result_a=$(cat /tmp/subagent-result-a.txt)
result_b=$(cat /tmp/subagent-result-b.txt)

# Merge or compare
diff <(echo "$result_a") <(echo "$result_b")
```

## Escalation Rule

If a subagent fails twice on the same task, don't retry. Escalate to Claude using the `escalate-to-claude` skill — the task is likely under-specified or outside MiniMax's capability.
