---
name: show-runner-smoke-test
description: "End-to-end smoke test for the show_runner system: inject a test beat on Pi, verify WebSocket delivery to Unity on PC, confirm telemetry roundtrip. Run after any show_runner code change."
version: 1.0.0
metadata:
  hermes:
    tags: [show_runner, smoke-test, websocket, unity, integration-test, pi]
    related_skills: [show-runner-dev, systematic-debugging]
---

# Show Runner Smoke Test

## Prerequisites

- Pi WebSocket server running (`show_runner.py` or `ws_bridge.py`)
- PC (10.0.0.91) Unity project open and running in Play mode
- SSH key auth working: `ssh Evan@10.0.0.91 echo ok`

## Step 1: Verify Pi Server is Listening

```bash
ss -tlnp | grep 8765
# Expected: LISTEN on 0.0.0.0:8765

# If not listening, start it:
cd ~/.hermes/show_runner
source ~/.hermes/hermes-agent/venv/bin/activate
python3 show_runner.py &
sleep 3
ss -tlnp | grep 8765
```

## Step 2: Inject a Test Beat

```bash
# Inject via the test file (show_runner polls this)
echo "TEST: susan says hello to the room" > /tmp/sr_inject.txt

# Watch the log for processing
tail -20 /tmp/sr_runner.log
# Expected: dialogue_beat or narration logged, not an error
```

## Step 3: Verify WebSocket Delivery

```bash
# Quick Python WS client test — sends a ping and reads back
python3 << 'EOF'
import asyncio, websockets, json

async def test():
    async with websockets.connect("ws://localhost:8765") as ws:
        # Send a test dialogue_beat
        msg = {
            "type": "dialogue_beat",
            "character": "susan",
            "text": "Smoke test message",
            "animation": "idle"
        }
        await ws.send(json.dumps(msg))
        print("Sent dialogue_beat OK")
        # Try to receive spatial_telemetry from Unity (may time out if Unity not running)
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(response)
            print(f"Received: {data.get('type', 'unknown')} from Unity OK")
        except asyncio.TimeoutError:
            print("No response from Unity (not running or not connected)")

asyncio.run(test())
EOF
```

## Step 4: Check PC Unity Side (if Unity is running)

```bash
# SSH to PC and check Unity log for our test message
ssh Evan@10.0.0.91 "grep -i 'smoke test\|dialogue_beat\|ShowRunner' \
  ~/Library/Logs/Unity/*.log 2>/dev/null | tail -10 || \
  find /mnt/Data -name '*.log' -newer /tmp/sr_inject.txt 2>/dev/null | head -3"
```

## Step 5: Verify Spatial Telemetry (roundtrip)

```bash
# Check the Pi received telemetry from Unity
grep "spatial_telemetry\|zone\|character_id" /tmp/sr_runner.log | tail -10
```

## Pass/Fail Criteria

| Check | Pass | Fail → Action |
|-------|------|---------------|
| Port 8765 listening | `ss` shows LISTEN | Start show_runner.py |
| Log shows beat processed | No exception in sr_runner.log | Check dialogue_engine.py |
| WS client connected | "Sent dialogue_beat OK" | Check firewall, `ss -tlnp` |
| Unity received message | Unity log shows ShowRunner output | Check ShowRunnerClient.cs |
| Telemetry roundtrip | spatial_telemetry in sr_runner.log | Check SpatialBroadcaster.cs |

## Quick Health Check (30 seconds)

```bash
echo "=== Port ===" && ss -tlnp | grep 8765
echo "=== Log tail ===" && tail -5 /tmp/sr_runner.log
echo "=== WS ping ===" && python3 -c "
import asyncio,websockets
async def p():
    async with websockets.connect('ws://localhost:8765',open_timeout=2) as ws:
        print('WS OK')
try: asyncio.run(p())
except Exception as e: print(f'WS FAIL: {e}')
"
```
