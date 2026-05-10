---
name: node-inspect-debugger
description: "Debug Node.js processes on the Pi using --inspect flag and Chrome DevTools Protocol or node:inspect."
version: 1.0.0
metadata:
  hermes:
    tags: [debugging, nodejs, inspect, javascript]
---

# Node.js Debugging

## Option A: Built-in REPL inspector (terminal only)

```bash
node --inspect-brk your_script.js
# Then in another terminal:
node inspect localhost:9229
```

Commands:
```
cont (c)    — continue
next (n)    — next line
step (s)    — step into
out (o)     — step out
repl        — open REPL at current frame
watch('x')  — watch expression x
```

## Option B: console.log with structured output (pragmatic)

For Pi/Hermes scripts, structured logging beats a debugger most of the time:

```javascript
console.log(JSON.stringify({ label: "checkpoint", value, state }, null, 2));
```

## Option C: Node debugger + SSH tunnel (for remote debugging)

```bash
# On Pi: launch with inspect
node --inspect=0.0.0.0:9229 your_script.js

# On PC: forward the port
ssh -L 9229:localhost:9229 Evan@10.0.0.9

# Open Chrome → chrome://inspect → configure localhost:9229
```

## Checking Hermes Node processes

```bash
# Find running node processes
ps aux | grep node

# Check what's listening
ss -tlnp | grep node

# Kill and restart
pkill -f "node your_script.js"
node your_script.js
```
