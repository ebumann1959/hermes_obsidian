
## Bug: review pipeline doesn't auto-route Critic to upstream `outputs` artifact

**Date**: 2026-04-28
**Session**: Z Suite ShowRunner audit

### The Problem
When a `refactor` task produces output at `scripts/unity/ShowRunnerServer.cs` but declares its `outputs` field as `...Assets/show_runner/ShowRunnerServer.cs` (or the task text uses the original path), the downstream `review` pipeline Critic reads the **original unpatched file** instead of the refactored artifact.

### Root Cause
zeo.py builds the review pipeline prompt from the task description text. The `outputs` field of upstream tasks is only used for:
1. The deliverables collection summary at end of run

It is **not** wired as an automatic routing signal to downstream pipeline steps. There is no `_route_review_to_upstream_output()` function or equivalent logic.

The decompose prompt (zeo.py:783) says review tasks should cover "previous task outputs" — but that's guidance for the LLM that writes the taskgraph, not an engine-enforced invariant. If the LLM writes the wrong path, the Critic reads the wrong file.

### The Loop It Caused
- Task 2 refactor: `outputs = scripts/unity/ShowRunnerServer.cs` (correct artifact path)
- Task 3 review: task text said `Review /home/Evan/show_runner/My project/Assets/show_runner/ShowRunnerServer.cs` (wrong path)
- Critic kept reading original → finding same 2 bugs → FAIL → retry → same result → infinite loop

### Manual Fix Applied
Patched taskgraph.json:
1. Updated Task 2 `outputs` path to match actual artifact location
2. Updated Task 3 task text to use correct path  
3. Marked Task 2 `status: completed`
4. Cleared `blocked_by` arrays that were preventing Task 3 dispatch

### Suggested Fix (for a future session)
Option A: In `_enrich_graph()`, automatically inject `review_target` field into review tasks by looking at upstream `outputs` field and patching the task text.

Option B: Add a `target_artifact` computed field in the taskgraph enrichment step that review/critic pipeline steps MUST use if present.

Option C: Add a ZEO-CRITIC pre-flight step that validates the review target file's mtime > upstream task completion time.

