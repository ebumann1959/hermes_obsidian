---
name: async-race-debugging
description: "Debug async race conditions in Python (asyncio) and Unity (coroutines/WebSocket) by injecting structured timestamp logging at every await boundary, then parsing the event timeline."
version: 1.0.0
metadata:
  hermes:
    tags: [async, race-condition, debugging, asyncio, websocket, coroutine, timing]
    related_skills: [systematic-debugging, python-debugpy, show-runner-dev]
---

# Async Race Debugging

Races are invisible because they're timing-dependent. The fix: make timing visible by injecting timestamps at every `await` and every state transition. Collect 30s of logs, then read the timeline.

## Step 1: Identify the Boundaries

A race lives between two async operations. Find them first:

```bash
# Find all awaits in the suspect module
grep -n "await\|async def\|asyncio\.\|create_task\|gather\|ensure_future" \
  ~/.hermes/show_runner/core/ws_bridge.py | head -30

# Find state mutations (shared state is where races bite)
grep -n "self\.\w* =\|_state\|_connected\|_queue" \
  ~/.hermes/show_runner/core/ws_bridge.py | head -20
```

## Step 2: Inject Timestamp Logging

Add a structured log at every `await` and every state mutation in the suspect file. Don't be subtle — log everything for one debug session.

```python
import asyncio, time, logging
log = logging.getLogger(__name__)

# Replace every significant await with a timed version:
_t = time.perf_counter
def _log_await(label):
    log.debug(f"[RACE] t={_t():.4f} task={asyncio.current_task().get_name() if asyncio.current_task() else 'none'} {label}")

# In suspect code, insert before/after each await:
_log_await("BEFORE: ws.recv()")
msg = await websocket.recv()
_log_await(f"AFTER: ws.recv() msg_type={type(msg).__name__} len={len(msg) if msg else 0}")

# At every state mutation:
_log_await(f"STATE: _connected {self._connected} → True")
self._connected = True
```

## Step 3: Enable DEBUG Logging and Collect

```bash
# Temporarily enable DEBUG for the suspect module
# Add to the top of the runner script or via env:
export PYTHONPATH=~/.hermes/show_runner
python3 -c "
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(name)s %(message)s',
    datefmt='%H:%M:%S',
    filename='/tmp/race_debug.log'
)
" 2>/dev/null

# Run show_runner for 30 seconds under load (inject test beats)
cd ~/.hermes/show_runner
source ~/.hermes/hermes-agent/venv/bin/activate
python3 show_runner.py &
SR_PID=$!
sleep 5
for i in $(seq 1 5); do echo "test beat $i" >> /tmp/sr_inject.txt; sleep 2; done
sleep 10
kill $SR_PID
```

## Step 4: Parse the Timeline

```bash
# Extract just the race-debug log lines in order
grep "\[RACE\]" /tmp/race_debug.log > /tmp/race_timeline.txt

# Look for: tasks interleaving at the wrong moment
# Pattern: task A writes state, then task B reads stale state before task A finishes
cat /tmp/race_timeline.txt | head -60

# Find the gap: where did the wrong ordering happen?
# Look for STATE changes that are not immediately followed by expected operations
grep "STATE:\|BEFORE:\|AFTER:" /tmp/race_timeline.txt | head -40
```

## Step 5: Identify the Race Pattern

Common patterns to look for in the timeline:

| Pattern | What it looks like | Fix |
|---------|-------------------|-----|
| **Check-then-act** | `_connected=True` then `BEFORE: recv()` from two tasks | Use `asyncio.Lock()` around the check+act |
| **Lost wakeup** | `await queue.get()` starts, item added, but different task takes it | Use `asyncio.Queue` not a plain list |
| **Stale state read** | Task B reads `_state` before Task A's write completes | `asyncio.Event` to signal completion |
| **Concurrent writes** | Two tasks both do `self._data = ...` | Lock around mutation |

## Step 6: Fix

```python
# Most async races in Python fix with a lock or an Event:
self._lock = asyncio.Lock()

async def safe_send(self, msg):
    async with self._lock:   # only one sender at a time
        await self._ws.send(msg)

# Or use Event for "wait until ready":
self._ready = asyncio.Event()
# producer:
self._ready.set()
# consumer:
await self._ready.wait()
```

## WebSocket-Specific (ws_bridge.py)

```bash
# Common race: message received while reconnect in progress
# Check: does recv() loop hold a reference to the old websocket?
grep -n "self._ws\|websocket\|_conn" ~/.hermes/show_runner/core/ws_bridge.py

# The fix pattern for reconnect races:
# Store a generation counter — if reconnect increments it, old recv() loops discard their result
```

## Cleanup

Remove all `_log_await()` calls after fixing. They're noisy and slow.

```bash
grep -n "_log_await\|RACE\]" ~/.hermes/show_runner/core/ws_bridge.py
# Delete those lines, or wrap in: if os.environ.get("DEBUG_RACE"): ...
```
