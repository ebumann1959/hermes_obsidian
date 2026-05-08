---
name: software-development-workflow
description: "End-to-end software development lifecycle on Hermes — planning (writing-plans, plan), investigation/spike, systematic debugging (Python debugpy, Node --inspect, Hermes TUI commands), code review (requesting-code-review), test-driven development, subagent orchestration (subagent-driven-development), and Hermes skill authoring (hermes-agent-skill-authoring)."
category: software-development
---

# Software Development Workflow

Covers: planning → investigation → implementation → debugging → review → testing, plus Hermes-specific tooling (skill authoring, TUI commands, subagent delegation).

## Skill Map

| Task | Primary Skill | Notes |
|------|--------------|-------|
| Write implementation plan | `software-development/writing-plans` | Start here for any feature/bug |
| Quick plan check | `software-development/plan` | Lightweight plan reader |
| Investigate / validate idea | `software-development/spike` | Throwaway experiments |
| Debug Python | `software-development/python-debugpy` | Remote DAP + pdb |
| Debug Node.js | `software-development/node-inspect-debugger` | Chrome DevTools Protocol |
| Debug Hermes TUI commands | `software-development/debugging-hermes-tui-commands` | Python/gateway/Ink UI |
| Systematic debugging | `software-development/systematic-debugging` | Universal framework |
| Code review | `software-development/requesting-code-review` | Pre-commit quality gates |
| Test-driven development | `software-development/test-driven-development` | RED-GREEN-REFACTOR |
| Orchestrate subagents | `software-development/subagent-driven-development` | delegate_task patterns |
| Author Hermes skills | `software-development/hermes-agent-skill-authoring` | SKILL.md format |

---

## Section 1: Planning (software-development/writing-plans)

**Primary skill for writing implementation plans.** Use when building anything non-trivial.

### When to Use
- Feature implementation, refactor, or significant bug fix
- Multi-step task that needs decomposition
- Any time you'd open a `TODO.md`

### Pattern
```bash
# Write plan to .hermes/plans/<name>.md
skill_view(name='software-development/writing-plans')  # Load the skill for format guidance
```

### Plan Structure
1. **Goal** — what success looks like (outcome, not implementation)
2. **Tasks** — numbered steps, each is a single coherent action
3. **Paths** — alternative approaches considered, with tradeoffs
4. **Verification** — how to confirm each task is done

### Related
- `plan` skill — lightweight plan reader/checker for existing plans
- `systematic-debugging` — when the "plan" is actually a bug investigation

---

## Section 2: Investigation / Spike (software-development/spike)

**Throwaway experiments to validate an idea before committing to implementation.**

### When to Use
- "Will X work for this use case?"
- Evaluating library/algorithm choices
- Proving feasibility before writing the real implementation
- Validating bug reproduction

### Pattern
- Create isolated experiment (separate dir, separate venv)
- Run once, observe, discard
- Do NOT commit spike code to the main project
- If spike succeeds: write the real implementation based on what you learned

### Anti-Pattern
- Spikes that grow into real code — if the experiment worked, rewrite it properly
- Spikes without a clear pass/fail criterion

---

## Section 3: Python Debugging (software-development/python-debugpy)

**Remote debugging via debugpy DAP (Debug Adapter Protocol).**

### Setup
```bash
# Target environment
pip install debugpy

# In the Python file to debug, add at the top (before other imports):
import debugpy
debugpy.listen(('0.0.0.0', 5678))  # or any free port
debugpy.wait_for_client()  # blocks until VS Code attaches
```

### VS Code launch.json
```json
{
  "name": "Python: Remote Attach",
  "type": "debugpy",
  "request": "attach",
  "host": "<target-ip>",
  "port": 5678
}
```

### Alternative: pdb
```bash
# Drop into pdb at a specific line
import pdb; pdb.set_trace()

# pdb on stdin/stdout (foreground only)
python -m pdb script.py
```

### Common Issues
- Port already in use → pick a different port
- Firewall blocking → open port on target machine
- pdb hangs in background process → use debugpy + VS Code for remote

---

## Section 4: Node.js Debugging (software-development/node-inspect-debugger)

**Chrome DevTools Protocol debugging for Node.js.**

### Setup
```bash
# Start with --inspect
node --inspect=0.0.0.0:9229 server.js

# Or for a running process
kill -USR1 <pid>  # sends SIGUSR1 to enable debugging
```

### Connect Chrome DevTools
```
chrome://inspect → Configure → Add target (host:port)
```

### vscode
```json
{
  "type": "node",
  "request": "attach",
  "host": "<target-ip>",
  "port": 9229
}
```

---

## Section 5: Hermes TUI Command Debugging (software-development/debugging-hermes-tui-commands)

**Debug slash commands in Hermes TUI — Python REPL, gateway, Ink UI.**

### When to Use
- A slash command isn't working
- Python REPL in TUI hangs or crashes
- Gateway connectivity issues

### Pattern
```bash
# Run Hermes with verbose logging
hermes --verbose 2>&1 | tee hermes-debug.log

# Check TUI state
# Ctrl+\  to quit, or check /tmp/hermes-tui.log
```

### Common Issues
- TUI not responding → check if `hermes` process is running
- Python REPL crash → check Python version mismatch
- Gateway timeout → verify network + auth token

---

## Section 6: Systematic Debugging (software-development/systematic-debugging)

**Universal debugging framework — works for any language, any system.**

### The Core Loop
1. **Hypothesis** — form a specific, falsifiable hypothesis
2. **Prediction** — predict what you'd see if hypothesis is true
3. **Probe** — run the minimal experiment to test prediction
4. **Observation** — did reality match prediction?
5. **Iterate** — refine hypothesis based on what you found

### Key Principle
**Fix the first occurrence, not the symptom.** If error message says "X is None", find where X becomes None, not where X is used downstream.

### Rubber Duck Debugging
Explain the code line-by-line to an inanimate object. If you can't explain WHY a line does what it does, that's the gap — investigate there.

### Reproduction Recipe
Before debugging anything:
1. Write the minimal reproduction script (10-50 lines max)
2. Confirm it reproduces the bug
3. Fix in reproduction
4. Confirm fix
5. Run full test suite

### When Stuck
- Write down every assumption you've made, then verify each one
- Check the version of every dependency
- Look at the git history — what changed since last working state?
- Search the error message exactly — Stack Overflow / GitHub issues

---

## Section 7: Code Review (software-development/requesting-code-review)

**Pre-commit review: security scan, quality gates, auto-fix.**

### When to Use
- Before opening a PR
- Before merging a significant change
- After a spike becomes real code

### Quality Gates
1. **Security** — `pip audit`, `npm audit`, or language-equivalent
2. **Linting** — `ruff`, `eslint`, or language linter
3. **Tests pass** — run the test suite
4. **Type check** — `mypy`, `tsc --noEmit`
5. **No secrets** — no API keys, tokens, or credentials in code

### Auto-fix Pattern
```bash
# Ruff auto-fix
ruff check --fix .

# ESLint auto-fix
eslint --fix .
```

---

## Section 8: Test-Driven Development (software-development/test-driven-development)

**RED-GREEN-REFACTOR cycle.**

### The Cycle
1. **RED** — Write a failing test that describes the behavior you want
2. **GREEN** — Write the minimum code to make the test pass
3. **REFACTOR** — Improve code quality without changing behavior (tests still pass)

### Test Naming
`test_<method>__<condition>__<expected_result>`

```python
def test_divide__by_zero__raises_divide_by_zero():
    with pytest.raises(DivideByZeroError):
        divide(1, 0)
```

### What to Test
- Unit test: pure functions, each behavior in isolation
- Integration test: interactions between components
- NOT: implementation details (test behavior, not how it works)

### Anti-Patterns
- Writing tests after code (not TDD)
- Brittle tests that break on refactors
- Tests that depend on other tests (isolation matters)

---

## Section 9: Subagent Orchestration (software-development/subagent-driven-development)

**delegate_task patterns for multi-agent workflows.**

### When to Use
- Task decomposes into independent parallel workstreams
- Codebase too large for single agent to hold in context
- Research + implementation need separate agents

### delegate_task Patterns
```python
# Parallel (orchestrator role)
delegate_task(tasks=[
    {"goal": "implement feature X", "context": "...", "toolsets": ["terminal", "file"]},
    {"goal": "implement feature Y", "context": "...", "toolsets": ["terminal", "file"]},
], role="orchestrator")

# Sequential
result_a = delegate_task(goal="do step 1", ...)
result_b = delegate_task(goal="do step 2 using result: " + result_a, ...)
```

### Golden Rules
- Pass all context explicitly — subagents have no memory of your conversation
- Use `role="orchestrator"` for tasks that spawn more tasks
- Use `toolsets` to restrict toolset (reduces token overhead)
- When done: verify output before proceeding (don't trust unverified subagent claims)

---

## Section 10: Hermes Skill Authoring (software-development/hermes-agent-skill-authoring)

**Format and conventions for writing SKILL.md files.**

### SKILL.md Format
```markdown
---
name: skill-name
description: "One-line description of what this skill does. Include trigger conditions."
category: <category>
---

# Skill Title

## Overview
What this skill covers, when to load it.

## When to Use
- bullet of appropriate trigger conditions
- bullet of appropriate trigger conditions

## When NOT to Use
- bullet of inappropriate trigger conditions

## Commands / Usage
```bash
# exact commands
```

## Pitfalls
- Known failure modes
- Common mistakes to avoid
```

### Frontmatter Fields
| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | lowercase, hyphens, max 64 chars |
| `description` | Yes | One-line, include trigger conditions |
| `category` | Recommended | Groups skills in listings |

### Support Files
- `references/<name>.md` — session-specific detail, knowledge banks, API quirks
- `templates/<name>.<ext>` — starter files to copy and modify
- `scripts/<name>.<ext>` — statically re-runnable verification scripts

---

## Common Workflow Sequence

1. **New feature**: `writing-plans` → write plan → `requesting-code-review` on plan
2. **Validate idea**: `spike` → if passes, write real code
3. **Implement**: Write code → `test-driven-development` (write tests first)
4. **Debug**: `systematic-debugging` → `python-debugpy` or `node-inspect-debugger` as needed
5. **Review**: `requesting-code-review` → fix any quality gates
6. **Delegate complex work**: `subagent-driven-development`
7. **Extend Hermes**: `hermes-agent-skill-authoring`
