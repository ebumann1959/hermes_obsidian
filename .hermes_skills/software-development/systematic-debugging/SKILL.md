---
name: systematic-debugging
description: "Universal debugging framework: reproduce → isolate → hypothesize → test → fix → verify. Use for any bug that isn't immediately obvious."
version: 1.0.0
metadata:
  hermes:
    tags: [debugging, troubleshooting, systematic, root-cause]
---

# Systematic Debugging

Never guess. Follow the loop.

## The Loop

### Step 1: Reproduce
Get a minimal, reliable reproduction first. If you can't reproduce it, you can't debug it.

```bash
# Establish baseline: does this ALWAYS fail or sometimes?
# What's the exact command/input that triggers it?
# What's the exact error message / wrong output?
```

### Step 2: Isolate
Binary-search the failure. Remove everything that isn't the bug.

```bash
# Comment out half the code. Still fails? Bug is in the other half.
# Add print statements at the boundary — before and after the suspected site.
# Check: is the INPUT wrong, or is the PROCESSING wrong?
```

### Step 3: Hypothesize
State your hypothesis explicitly before testing it.

```
Hypothesis: the WebSocket server drops the connection because 
            the client sends a malformed JSON frame (missing "type" key).
Test: add json.dumps(msg) before send and log it.
```

### Step 4: Test the Hypothesis
Run the minimal test. If the hypothesis was wrong, say so and form a new one.

```bash
# Add logging at the exact suspect site
# Re-run the reproduction case
# Read the output before writing any fix
```

### Step 5: Fix and Verify
Fix ONLY what the hypothesis says is broken. Then re-run the reproduction case.

```bash
# Run the original failing case — does it pass?
# Run related cases — did you break anything adjacent?
```

## Pi-specific Gotchas

- Logs at `~/.hermes/logs/agent.log` and `errors.log` — tail them, don't grep blindly
- `state.db` WAL mode: reads may lag writes by one checkpoint — use `PRAGMA wal_checkpoint(PASSIVE)` to flush
- MiniMax content filter: check `finish_reason` in dialogue_engine.py logs — "content_filter" means the model stopped, not a network error
- WebSocket drops: check `ws://10.0.0.9:8765` is listening with `ss -tlnp | grep 8765`
- Show runner log: `/tmp/sr_runner.log` — always check here before agent.log for show_runner bugs

## Anti-Patterns (stop doing these)

- Changing multiple things at once and re-running
- Guessing the fix without reading the error
- "Fixing" the symptom (retry loop) instead of the cause
- Asking the user "does this work?" without running it yourself first
