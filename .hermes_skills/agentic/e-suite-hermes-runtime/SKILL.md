---
name: e-suite-hermes-runtime
description: E-Suite runtime daemon — Hermes subprocess executor for board message processing
triggers:
  - esuite runtime daemon
  - hermes chat -q subprocess
  - e-suite board message pipeline
---

# E-Suite Hermes Runtime Fixes

## Key Finding: Hermes Environment

Hermes requires `HOME=/home/Evan` to function. Without it, subprocess calls hang indefinitely.

```python
def _hermes_env() -> dict:
    env = dict(os.environ)
    env.setdefault("HOME", "/home/Evan")
    env["TERM"] = "dumb"
    return env

    result = subprocess.run(
    [HERMES_CLI, "chat", "-q", goal, "-Q"],
    capture_output=True,
    timeout=600,  # Increased from 300 — prompts are very large (40-60KB)
    env=_hermes_env(),
)
```

Always use `-Q` flag to suppress TUI box-drawing characters in output.

## Captain Prompt Architecture

`hermes chat -q` has NO `-s` flag for system prompt. The full system prompt must be embedded in the query string:

```python
def build_captain_prompt(board_message, active_teams, idle_teams, max_teams):
    system = load_prompt("/tmp/prompts/zeo.md")
    status = f"## Current System Status\n- Active teams: {active_teams}\n- Idle teams: {idle_teams}\n..."
    return f"{system}\n{status}\n\n## Board Message\n{board_message}\n\nProduce JSON commands..."
```

## Captain JSON Parsing

Hermes outputs both TUI characters AND JSON. Strip TUI before parsing:

```python
def parse_captain_output(raw: str) -> List[Dict]:
    # Strip TUI box-drawing chars
    cleaned = re.sub(r'╭─.*?─╮', '', raw)  # Remove box header
    cleaned = re.sub(r'─+', '', cleaned)   # Remove lines
    cleaned = re.sub(r'╰.*', '', cleaned)   # Remove box footer
    cleaned = re.sub(r'`+', '', cleaned)   # Remove backticks
    cleaned = re.sub(r'\s+', ' ', cleaned) # Collapse whitespace
    # Now search for JSON array
    ...
```

Also: parser finds JSON in both thinking text AND JSON block → returns duplicates. Need to find only the LAST complete JSON array.

## Report Viewer (added recently)

Pipeline reports now flow through the task system:
- Runtime saves `report_path` to `task.outputs` on completion: `{"report_path": "...", "project_dir": "...", "pipeline": "..."}`
- `GET /tasks/{id}` returns `outputs` field
- `GET /reports/{task_id}` returns `{"report_path": "...", "content": "..."}`
- Frontend KanbanBoard shows "report →" on done tasks with a slide-in viewer

## Pending Issues

1. `_register()` always 404s because `/internal/hermes/register` endpoint doesn't exist in FastAPI. Safe to ignore — polling works anyway.
2. `idle_teams=0` was hardcoded → Captain queued but never dispatched — FIXED: now queries API for actual team counts.
3. TUI box chars (`╭─ ╰─`) were polluting `captain_raw` in DB — FIXED: stripped before storage.

## Python3.11 Dependencies

The daemon runs on python3.11 (Hermes's Python). Install deps:
```bash
python3.11 -m pip install --break-system-packages httpx aiosqlite
```

## Startup

```bash
cd /home/Evan/Projects/e-suite/backend
nohup python3.11 -u esuite_runtime.py start --api http://localhost:8000 >> /tmp/esuite_final.log 2>&1 &
```
