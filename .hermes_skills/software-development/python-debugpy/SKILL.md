---
name: python-debugpy
description: "Attach a Python debugger (debugpy/pdb) to a running process on the Pi. Use for stepping through show_runner, hermes agent, or any Python service."
version: 1.0.0
metadata:
  hermes:
    tags: [debugging, python, debugpy, pdb, breakpoint]
---

# Python Debugging (debugpy + pdb)

## Option A: pdb (no install needed)

Add a breakpoint inline — fastest for one-off debugging:

```python
import pdb; pdb.set_trace()
# or Python 3.7+
breakpoint()
```

Run the script normally. It will drop into pdb at the breakpoint.

```
(Pdb) p variable_name     # print variable
(Pdb) l                   # list current code
(Pdb) n                   # next line
(Pdb) s                   # step into function
(Pdb) c                   # continue to next breakpoint
(Pdb) q                   # quit
```

## Option B: Post-mortem (crash debugging)

```bash
python3 -m pdb -c continue your_script.py
# Drops into pdb at the exception site
```

Or wrap the call:
```python
import pdb, traceback
try:
    your_function()
except Exception:
    traceback.print_exc()
    pdb.post_mortem()
```

## Option C: debugpy (remote attach from VS Code or another terminal)

```bash
pip install debugpy  # in the venv if needed

# Launch with debugpy listening
python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client your_script.py
```

Then attach from another terminal:
```bash
python3 << 'EOF'
import debugpy
debugpy.connect(("localhost", 5678))
debugpy.wait_for_client()
EOF
```

## Show Runner Specific

```bash
# Run show_runner with pdb on first exception
cd ~/.hermes/show_runner
source ~/.hermes/hermes-agent/venv/bin/activate
python3 -m pdb show_runner.py

# Tail the log in another terminal while debugging
tail -f /tmp/sr_runner.log
```

## Logging Instead of Breakpoints (preferred for daemons)

```python
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
log.debug("variable=%r", variable)
```

Check output: `tail -100 ~/.hermes/logs/agent.log`
