---
name: writing-plans
description: "Write a structured implementation plan before starting any non-trivial task. Produces a .hermes/plans/<name>.md file with Goal, Tasks, Paths, and Verification sections."
version: 1.0.0
metadata:
  hermes:
    tags: [planning, tdd, implementation, workflow]
---

# Writing Plans

Before touching code on any task with 3+ steps, write a plan. Plans prevent scope creep, expose unknowns early, and give MiniMax a stable anchor to work from.

## When to Use
- Any feature, refactor, or bug fix that touches more than one file
- Anything ambiguous — write the plan to clarify, not to document after
- Before spawning a subagent (they need a plan to not hallucinate scope)

## Format

Create `.hermes/plans/<task-name>.md`:

```markdown
# Plan: <task name>

## Goal
One sentence: what does success look like from the user's perspective?

## Tasks
1. [ ] <action verb> — <specific file or component>
2. [ ] <action verb> — <specific file or component>
...

## Paths
- **Chosen:** <approach> — why
- **Rejected:** <alternative> — why not

## Verification
- [ ] <how to confirm task 1 is done>
- [ ] <how to confirm task 2 is done>
- [ ] Smoke test: <one command that proves the feature works end-to-end>
```

## Rules
- Goal is an **outcome**, not an implementation ("user can log in" not "write auth.py")
- Each task is ONE coherent action — split if it has two verbs
- Verification steps must be runnable commands or observable facts, not "check if it works"
- Never start implementation before the plan exists in writing

## Example

```markdown
# Plan: add WebSocket reconnect backoff

## Goal
ShowRunner client reconnects to Pi automatically after network drop without manual restart.

## Tasks
1. [ ] Add exponential backoff loop to ShowRunnerClient.cs Connect()
2. [ ] Expose maxRetries and baseDelay as Inspector fields
3. [ ] Log reconnect attempts to Unity console

## Paths
- **Chosen:** exponential backoff in coroutine — stays on main thread, no threading issues
- **Rejected:** polling from Update() — wastes CPU every frame

## Verification
- [ ] Kill Pi WebSocket server, confirm Unity retries every 2/4/8s
- [ ] After 5 failures, confirm error logged, not infinite loop
- [ ] Reconnect after Pi restart, confirm dialogue resumes
```
