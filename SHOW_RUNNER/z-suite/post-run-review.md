# Z Suite Run Post-Review: show-runner (2026-04-29)

## Run Overview
- **Project:** show-runner
- **Started:** 2026-04-29 ~10:48
- **Goal:** Build complete two-machine show_runner pipeline (Pi Python WS bridge + Unity 6 C# renderer)
- **Tasks:** 11 tasks across 5 waves
- **Final state:** TBD (in progress at time of note)

## Known Failure Patterns

### 1. Forge wrote no code (Team B)
- **Symptom:** Gate fail — "artifact: forge output contains no code blocks — only descriptions/intentions"
- **Task affected:** Task 3/4 (dialogue_engine.py + show_runner.py updates)
- **Root cause:** Unknown — requires review of Team B event log
- **File:** `/home/Evan/.hermes/vault/z-suite/teams/b/events.ndjson`

### 2. Team C — CharacterRegistry.cs failed 3x consecutively
- **Symptom:** Critic FAIL (3 critical findings), 3 retries
- **Triggered:** ESCALATE_TO_ZEO → ziral_decision.json intervention
- **Critical issues found:**
  1. **Duplicate BillboardLabel type (CS0101)** — forge generated nested `class BillboardLabel` inside CharacterRegistry.cs conflicting with standalone `BillboardLabel.cs`
  2. **Coroutine mismatch** — `StopCoroutine("Move_" + id)` used with `StartCoroutine(MoveOverTime(...))` (IEnumerator overload, not string)
  3. **Contract violations** — Critic flagged undefined references: `AddHandler`, `AutoReconnectCoroutine`, `Awake`
- **Root cause:** Forge not respecting standalone component architecture; confused about Unity component composition
- **Task:** Task 6 (ShowRunnerClient.cs + CharacterRegistry.cs)

### 3. All teams hit thrashing warnings
- Multiple teams' critics issued `thrashing_warning` (reads++ without writes)
- Soft warning only — did not block progress

### 4. no_import_evidence warnings (Teams A, D, E)
- Critic passed but flagged "no_import_evidence" — output claims imports but no actual evidence in file
- Soft warning — did not block

## Post-Run Action Items
- [ ] Review Team B events.ndjson for no-code artifact
- [ ] Audit CharacterRegistry.cs final state for duplicate type and coroutine fix
- [ ] Understand why contract references (AddHandler, Awake) were not validated before critic
- [ ] Determine if ziral_decision.json manual intervention is the right fix vs automated retry policy
- [ ] Review whether Unity C# task prompts were sufficiently clear about standalone component reuse
- [x] **Path canonicalization**: `/home/Evan/show_runner/My project/` was DELETED but skills and learnings still referenced it. Purged from all active skills. Current canonical path: `/mnt/Data/show_runner/`. Added path verification protocol to learnings. Z Suite agents must verify target paths exist before writing.
- [ ] Certs missing — `/home/Evan/show_runner/comms.pfx` not found. Need to regenerate for UnityComms TLS.
