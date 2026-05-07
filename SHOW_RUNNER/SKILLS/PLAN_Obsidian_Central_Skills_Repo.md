# PLAN: Obsidian as Central Skills Repository

**Created:** 2026-04-15
**Author:** Hermes Agent

---

## WHY

I have 112 skills across 20 categories stored in `~/.hermes/skills/` as `.md` files — but:
- No shared index across agents
- Not browsable in a human-friendly UI
- No context about *when* or *why* a skill was built
- No project linkage

The vault becomes the readable layer on top of the skill system.

---

## STRUCTURE

```
SHOW_RUNNER/SKILLS/
├── INDEX.md                          ← master list, all skills with wikilinks
├── PROJECT_INDEX.md                  ← which skills built for which project
├── BY_CATEGORY/
│   ├── devops.md
│   ├── unity.md
│   ├── mlops.md
│   └── ...
├── _individuals/
│   ├── conky-execgraph-debugging.md
│   ├── show-runner-debugging.md
│   ├── discord-persona-runner-debugging.md
│   └── ... (one per skill)
└── USAGE_GUIDE.md                    ← how to use this as a living skill base
```

---

## PER-SKILL NOTE CONTENTS

Each note captures:
- Skill name + description
- Category
- File path: `~/.hermes/skills/...`
- Date created
- Project: which project it was built for
- Context: what problem it solves, when to reach for it
- Pitfalls: gotchas discovered from use
- Related skills: wikilinks to similar or complementary ones

---

## PROJECT INDEX

Maps projects to skills:

| Project | Skills |
|---------|--------|
| `paperclip/` | paperclip-hermes-remote-setup |
| `show_runner/` | unity-scene-file-editing, show-runner-debugging, show-runner-ui-debugging, persona-runner-*, polar-axis-slider-ui |
| `conky/` | conky-*, conky-manager2-*, xscreensaver-on-raspberry-pi, conky-hermes-process-monitoring, conky-line-plot-from-log |
| `discord_persona/` | discord-persona-runner-*, discord-persona-ui-flask, discord-persona-context-duplication, persona-runner-stall-debugging |
| `blender/` | blender-headless-ssh-render |
| `unity/` | unity-scene-direct-editing, unity-scene-setup-via-ssh, unity-http-server-linux, unity-show-runner-debugging |
| `mlops/` | llm-wiki, huggingface-hub, gguf-quantization, vllm, etc. |

*(112 total skills — full breakdown in INDEX.md)*

---

## HOW TO POPULATE

**Step 1:** Write INDEX.md — full list of all 112 skills with wikilinks to `_individuals/`

**Step 2:** Write per-skill notes for skills with known context/pitfalls (not all 112 need full notes — many are self-explanatory from the description)

**Step 3:** Write PROJECT_INDEX.md

**Step 4:** Write USAGE_GUIDE.md

**Step 5:** Set a rule: **any new skill I build, I write a note to the vault** — this becomes part of my skill-building workflow

---

## UPDATE PROTOCOL

| Event | Action |
|-------|--------|
| Build new skill | Write vault note immediately after creating `.md` |
| Discover a pitfall | Update the relevant per-skill note |
| New project context | Update PROJECT_INDEX.md |
| Significant skill change | Update per-skill note |

---

## MULTI-AGENT ACCESS

Other agents (e.g. CEO-Hermes, subagents) can read the vault notes directly. The vault becomes a shared skill bible they can browse when they need to find a tool.

---

## NEXT STEP

Write INDEX.md and PROJECT_INDEX.md first — that is the foundation. Then fill in per-skill notes for high-value skills (those with known bugs, project-specific ones, non-obvious ones).
