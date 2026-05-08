---
name: paperclip-hermes-remote-setup
category: autonomous-ai-agents
description: Connect a remote Hermes agent (running on a Pi) as a CEO/agent in Paperclip running on the local PC. Includes adapter config, DB updates via API, instructions setup, and known bug fixes.
---

# Paperclip hermes-remote Adapter Setup

Connect a Hermes agent (running on a remote Pi) as a CEO/agent in Paperclip running on the local PC.

## Adapter Architecture

- Paperclip (PC, port 3100) SSHs to the remote Pi as the configured user
- Runs `hermes chat -Q` on the Pi with CEO instructions
- Sessions stored on the Pi at `~/.hermes/sessions/`
- MINIMAX_API_KEY is read from `~/.hermes/auth.json` on the PC and forwarded over SSH
- PAPERCLIP_API_URL is set to the PC's LAN IP (10.0.0.x) so Hermes can reach it from the Pi

## Adapter Architecture

```json
{
  "hermesCommand": "/home/Evan/.hermes/hermes-agent/venv/bin/hermes",
  "model": "MiniMax-M2.7",
  "provider": "minimax",
  "sshHost": "10.0.0.14",
  "sshPort": 22,
  "sshUser": "shady",
  "instructionsFilePath": "/home/Evan/.hermes/agents/ceo-hermes/instructions/AGENTS.md",
  "instructionsBundleMode": "external",
  "graceSec": 20,
  "timeoutSec": 0,
  "persistSession": true,
  "toolsets": "terminal,file"
}
```

> `hermesCommand` is **required** — the default in `constants.ts` is hardcoded to `/home/evan/.hermes/...` which will 404 on any non-Evan remote. `instructionsBundleMode: "external"` is also required when instructions live on the remote Pi rather than in Paperclip's managed workspace.

## Required DB Updates

Use the API (no auth on localhost):

1. **Main agent config** — `PATCH /api/agents/:id`:
   ```json
   {
     "role": "ceo",
     "status": "idle",
     "adapterConfig": { ... },
     "runtimeConfig": {
       "heartbeat": {
         "enabled": true,
         "cooldownSec": 10,
         "intervalSec": 300,
         "wakeOnDemand": true,
         "maxConcurrentRuns": 1
       }
     }
   }
   ```

2. **Permissions** — `PATCH /api/agents/:id/permissions`:
   ```json
   { "canCreateAgents": true, "canAssignTasks": true }
   ```
   Note: This endpoint requires BOTH fields. Omitting `canAssignTasks` returns a 400.

3. **Reset error status** — `PATCH /api/agents/:id` with `{"status":"idle"}`

## Instructions Setup on the Pi

Create at the `instructionsFilePath` on the Pi:
- `SOUL.md` — CEO persona and voice
- `HEARTBEAT.md` — execution checklist, heartbeat workflow
- `AGENTS.md` — role description, delegation rules, references to SOUL.md and HEARTBEAT.md
- `TOOLS.md` — tools reference (can be minimal)

Entry point is `AGENTS.md` (the `instructionsFilePath` should end in `AGENTS.md`).

## Known Bugs

### execViaSSH cwd bug (CRITICAL — heartbeat hangs forever, no output)

**Files:** Both `src/server/execute.ts` AND `dist/server/execute.js` must be patched.

**Symptom:** Heartbeat run starts but never completes. Session file grows on the Pi. Paperclip shows the run as "running" indefinitely. No stdout/stderr is captured. The SSH connection appears to succeed (MINIMAX_API_KEY is injected) but nothing comes back.

**Root cause:** The `execViaSSH` function had broken SSH argument construction when `cwd` was set. It pushed both `bash -c "cd /cwd && cmd"` AND the raw `command args[]` onto the SSH args array, producing:
```
ssh ... user@host bash -c "cd /cwd && cmd" cmd arg1 arg2
```
The remote shell tries to run `cmd` as a second command after the `bash -c` invocation, with wrong cwd and no proper handling. When `cwd` is null (as it is for this adapter), the bug doesn't trigger — explaining why it wasn't caught earlier.

**Fix in `src/server/execute.ts` — `execViaSSH` function:**
```typescript
// WRONG — broken cwd handling:
const remoteCmd = command + " " + args.map((a) => shellQuote(a)).join(" ");
const sshArgs = [
  "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
  "-o", "ConnectTimeout=10", "-p", port, user + "@" + host,
];
if (cwd) {
  sshArgs.push("bash", "-c", "cd " + JSON.stringify(cwd) + " && " + remoteCmd);
}
sshArgs.push(command);          // ← BUG: command pushed twice when cwd is set
for (const arg of args) { sshArgs.push(arg); }

// RIGHT — single remoteCmd with optional cd prefix:
const quotedArgs = args.map((a) => shellQuote(a)).join(" ");
let remoteCmd = command + " " + quotedArgs;
if (cwd) {
  remoteCmd = "cd " + JSON.stringify(cwd) + " && " + remoteCmd;
}
const sshArgs = [
  "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
  "-o", "ConnectTimeout=10", "-p", port.toString(), user + "@" + host,
  remoteCmd,                       // ← single argument: the full remote command
];
```

Also fix the port type coercion: `port` is a string/number but must be `.toString()`.

**Fix in `dist/server/execute.js` (compiled output):**
The dist has different formatting (separate `let` declarations). Line-level edits needed:
1. Add back `let stdout = "";` (can get deleted during edits)
2. Ensure `sshArgs` array has: `"-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "-p", port.toString(), user + "@" + host, remoteCmd, ];`
3. Remove any orphaned `sshArgs.push(command)` and `for (const arg of args)` loop
4. Ensure `let stdout = ""; let stderr = "";` both exist

**Restart Paperclip after patching** — `tsx` caching means the server won't pick up changes until `pkill` + restart.

### Buffer trimEnd crash (CRITICAL — crashes server on first heartbeat)
**Files:** Both the TypeScript source AND the compiled output must be patched.

**Symptom:** `TypeError: chunk.trimEnd is not a function` — Paperclip crashes immediately when Hermes produces any stderr output.

**Root cause:** Node.js passes `Buffer` objects to `proc.stderr.on("data")` and `proc.stdout.on("data")` callbacks, NOT strings — regardless of what the TypeScript type annotation says (`chunk: string`).

**Fix in `packages/adapters/hermes-remote/src/server/execute.ts`:**

```typescript
// Line ~283 — the data handlers (TypeScript says string, runtime is Buffer):
// Wrong:
proc.stdout.on("data", (chunk: string) => { stdout += chunk; });
proc.stderr.on("data", (chunk: string) => { onLog("stderr", chunk); });
// Right:
proc.stdout.on("data", (chunk: Buffer | string) => { stdout += String(chunk); });
proc.stderr.on("data", (chunk: Buffer | string) => { onLog("stderr", String(chunk)); });

// Line ~157 — the trimEnd call in wrappedOnLog:
// Wrong:
const trimmed = chunk.trimEnd();
// Right:
const trimmed = String(chunk).trimEnd();
```

**Fix in `packages/adapters/hermes-remote/dist/server/execute.js` (compiled output):**
```javascript
// Line ~271 — same data handler issue in compiled JS:
// Wrong:
proc.stdout.on("data", (chunk) => { stdout += chunk; });
proc.stderr.on("data", (chunk) => { onLog("stderr", chunk); });
// Right:
proc.stdout.on("data", (chunk) => { stdout += String(chunk); });
proc.stderr.on("data", (chunk) => { onLog("stderr", String(chunk)); });

// Line ~156 — same trimEnd fix:
// Wrong:
const trimmed = chunk.trimEnd();
// Right:
const trimmed = String(chunk).trimEnd();
```

**Important:** `tsx` does not reliably recompile on each run. After patching the `.ts` source, also patch the `.js` in `dist/` directly, then restart.

### multer ESM import
**File:** `server/src/routes/issues.ts`, line 3

**Symptom:** `ERR_MODULE_NOT_FOUND: Cannot find package 'multer'`

**Fix:**
```typescript
// Wrong:
import multer from "multer";
// Right:
import multer from "multer/index.js";
```

## Restarting Paperclip After Fixes

```bash
ssh Evan@10.0.0.91
pkill -f 'tsx.*paperclip'
cd /home/Evan/paperclip
PNP_WORKSPACE_LIST_RETRY=true pnpm --filter @paperclipai/server run dev &
# Wait ~20s for startup
curl http://localhost:3100/api/health
```

## Testing the Connection

```bash
# Reset to idle
curl -X PATCH http://localhost:3100/api/agents/<AGENT_ID> \
  -H 'Content-Type: application/json' \
  -d '{"status":"idle"}'

# Trigger manual heartbeat
curl -X POST http://localhost:3100/api/agents/<AGENT_ID>/heartbeat/invoke \
  -H 'Content-Type: application/json' \
  -d '{"source":"manual"}'

# Check run status (replace RUN_ID)
curl http://localhost:3100/api/heartbeat-runs/<RUN_ID>

# Watch logs
tail -f /home/Evan/.paperclip/instances/default/logs/server.log
```

## Key Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/agents/:id` | Get agent config |
| PATCH | `/api/agents/:id` | Update agent config |
| PATCH | `/api/agents/:id/permissions` | Update permissions |
| POST | `/api/agents/:id/heartbeat/invoke` | Trigger heartbeat |
| GET | `/api/heartbeat-runs/:id` | Check run result |
| GET | `/api/health` | Server health check |

## Heartbeat Run Lifecycle

A heartbeat run stays `"status": "running"` the entire time Hermes is working or waiting for board input — it does NOT mean the run is stuck. It completes (status: `"completed"` or `"failed"`) only when Hermes exits and returns control to Paperclip. If Hermes is waiting for a board reply, the run stays `"running"` indefinitely.

**Board reply flow:** When the agent has a question, it stops and waits. The live run stays "running" in Paperclip. You can reply via the Paperclip UI (live run reply box), or assign tasks via the issues API — the next scheduled heartbeat (every 5 min) will pick them up.

## API Routes for Heartbeat Runs

| Route | Works? | Notes |
|-------|--------|-------|
| `GET /api/heartbeat-runs/:id` | YES | Direct run lookup |
| `GET /api/companies/:id/heartbeat-runs` | Internal Server Error | Bug — avoid |
| `GET /api/companies/:id/heartbeat-runs?agentId=` | Internal Server Error | Bug — avoid |

Use `/api/heartbeat-runs/:id` for direct lookups. The company-level route returns 500.

## tsx Caching Gotcha

After patching `execute.ts` source, `tsx` does NOT reliably recompile on restart. **Always also patch `dist/server/execute.js`** when fixing runtime bugs, then restart. The server can stay up but won't pick up changes until you `pkill` and restart.

## HEARTBEAT.md Uses Hardcoded localhost — Must Be Fixed

**File:** `/home/Evan/.hermes/agents/ceo-hermes/instructions/HEARTBEAT.md` on the Pi

The HEARTBEAT.md template hardcodes `http://localhost:3100` in all API calls. When CEO-Hermes runs on the Pi and makes API calls, `localhost` resolves to the Pi itself — not the PC running Paperclip. All instances of `localhost:3100` in HEARTBEAT.md must be replaced with the Paperclip PC's LAN IP (e.g. `http://10.0.0.91:3100`).

Also note: Paperclip uses `/api/issues` not `/api/tasks`. Verify paths when editing.

### contextSnapshot Missing taskBody/title (Agent Gets Empty Task Context)

**Symptom:** CEO-Hermes receives `Issue ID: <uuid>` but no title or body content. It spends time exploring the filesystem trying to figure out what the task actually is.

**Root cause:** `buildSystemPromptExtension` reads `context.taskBody` and `context.taskTitle`, but the Paperclip server only populates `issueId` in `contextSnapshot` — not the full issue content. The agent gets the ID but not the what/why.

**Workaround:** Agent MUST call `GET /api/issues/:id` immediately on wake to fetch issue content before doing anything else. HEARTBEAT.md checklist should include this as the first step, but agents may skip it.

**HEARTBEAT.md checklist (mandatory first steps):**
1. `GET /api/issues/:id` to fetch title + body
2. If empty response, try `GET /api/issues` to list available issues
3. Then proceed with the actual task

### CEO Explores Wrong Workspace (/mnt/ssd/paperclip)

CEO-Hermes explores `/mnt/ssd/paperclip` (the Edge betting platform on the Pi) instead of working the ticket. This wastes time because the agent wakes with no issue body, explores prominent local directories, and gets sidetracked. Its actual workspace content is on the PC at `/home/Evan/.paperclip/instances/default/workspaces/<agent-id>`. This is expected — the agent just needs to fetch issue content via API immediately.

## PC Has No Obsidian Vault Access (RESOLUTION IN PROGRESS)

**Vault paths:**
- Pi vault: `/mnt/nvme/obsidian-vault/` (NVME, 3.9MB, 102 files)
- PC vault: `/mnt/Data/obsidian_vault/` (cloned from GitHub)
- Both agents must sync via git at session boundaries (see Git Sync Workflow below)

**Skill parity gap — PC is missing these Pi skill categories:**
- `networking`, `unity`, `unity-maestro`, `system-configuration`, `paperclip-hermes-remote-setup`
- Copy to PC: `scp -r ~/.hermes/skills/{networking,unity,unity-maestro,system-configuration,paperclip-hermes-remote-setup} Evan@10.0.0.91:~/.hermes/skills/`
- Skills are local to each machine — one-way copy, no auto-propagation
- PC has `optional/`, `system/`, `agentic/` categories the Pi lacks (one-directional)

---

### Git Sync Workflow (VAULT SYNC)

Both Pi and PC clone from the same GitHub repo. Each agent syncs at session boundaries:

```
SESSION START (both agents):
  cd /mnt/nvme/obsidian-vault && git pull

SESSION END (both agents):
  cd /mnt/nvme/obsidian-vault && git add -A && git commit -m "session: $(date +%Y-%m-%d)" && git push
```

**PC vault setup** (one-time):
```bash
# PC: clone into the designated path
git clone git@github.com:ebumann1959/obsidian-vault.git /mnt/Data/obsidian_vault
```

**GitHub repo:** `git@github.com:ebumann1959/obsidian-vault.git` (private)

**CAVEAT — `gh` CLI on Pi requires interactive browser auth:**
- `gh auth login` opens a web flow — cannot be done over SSH non-interactively
- If GitHub auth is not yet set up on a machine, create the repo manually at github.com first, then push from Pi
- SSH key auth to GitHub (`git@github.com`) is already confirmed working on both Pi and PC
- `gh` package is available on Pi (`apt install gh`) but not yet logged in

**Edge cases:**
- Simultaneous edits → second push gets merge rejection → manual resolution needed (rare in practice)
- Pi offline → PC works from local copy, pushes when Pi returns
- PC offline → Pi works normally, PC pulls on next session start

## piHernan esNot Installed on Pi

The CEO instructions reference `para-memory-files` skill which is not installed on the Pi. This causes the agent to note the missing skill but does NOT crash — it logs a warning and continues. The agent falls back to its internal memory approach.

## Critical Distinction: Paperclip AI Manager vs Paperclip Edge

These are COMPLETELY DIFFERENT projects — do NOT confuse them:

| | Paperclip (AI Manager) | Paperclip Edge |
|--|--|--|
| Location | PC at `/home/Evan/paperclip` | Pi at `/mnt/ssd/paperclip` |
| Purpose | AI company orchestration platform | Sports/crypto betting research |
| Tech | Node.js + TypeScript + Postgres | Python + DuckDB + Streamlit |
| User | Evan | shady |
| IP | 10.0.0.91 | 10.0.0.14 |

**From the Pi, SSH to PC as:** `ssh Evan@10.0.0.91` (user is Evan, NOT shady)
- Pi user: `shady`
- PC user: `Evan`
- SSH key on Pi: `~/.ssh/id_ed25519` (pub key must be in PC's `authorized_keys`)

**Finding Paperclip on the PC from Pi:**
```bash
ssh -o "StrictHostKeyChecking=no" Evan@10.0.0.91 "find ~ -maxdepth 5 -iname '*paperclip*' 2>/dev/null | grep -v '.git\|node_modules\|venv'"
```

**Key Paperclip PC paths:**
- Source: `/home/Evan/paperclip/`
- Storage: `/home/Evan/.paperclip/instances/default/data/` (162MB used)
- DB backups: `/home/Evan/.paperclip/instances/default/data/backups/`
- Workspaces: `/home/Evan/.paperclip/instances/default/workspaces/`