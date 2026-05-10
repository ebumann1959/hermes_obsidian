---
name: hermes-agent-skill-authoring
description: "How to write a new Hermes skill: SKILL.md format, naming conventions, tagging, vault sync, and testing."
version: 1.0.0
metadata:
  hermes:
    tags: [skills, authoring, hermes, meta, self-improvement]
---

# Hermes Skill Authoring

Skills are markdown files that load into the agent context on demand. They encode reusable knowledge, procedures, and environment-specific facts.

## Directory Structure

```
~/.hermes/skills/<category>/<skill-name>/SKILL.md
```

Skills are synced to both Pi and PC via the vault:
```
/mnt/nvme/obsidian-vault/.hermes_skills/<category>/<skill-name>/SKILL.md
```

Always write new skills to the vault path first, then run `bash ~/sync-vault.sh` to deploy.

## SKILL.md Format

```markdown
---
name: my-skill-name
description: "One sentence: what this skill enables and when to use it."
version: 1.0.0
metadata:
  hermes:
    tags: [tag1, tag2, tag3]
    related_skills: [other-skill]
---

# Skill Title

Brief overview.

## When to Use
- Bullet list of trigger conditions

## <Section>
Content...
```

## Rules for Good Skills

1. **Description is load-bearing** — it's what the agent reads to decide whether to load the skill. Make it specific and action-oriented.
2. **When to Use is required** — without it, the skill is used randomly.
3. **Commands must be copy-pasteable** — test every bash snippet before committing.
4. **Env-specific facts belong here** — Pi paths, MiniMax quirks, vault locations.
5. **Keep it under 300 lines** — if longer, split into sub-skills.

## Adding a Skill

```bash
# 1. Write to vault (canonical source)
mkdir -p /mnt/nvme/obsidian-vault/.hermes_skills/<category>/<name>
cat > /mnt/nvme/obsidian-vault/.hermes_skills/<category>/<name>/SKILL.md << 'EOF'
---
name: <name>
...
EOF

# 2. Deploy to local skills
mkdir -p ~/.hermes/skills/<category>/<name>
cp /mnt/nvme/obsidian-vault/.hermes_skills/<category>/<name>/SKILL.md \
   ~/.hermes/skills/<category>/<name>/SKILL.md

# 3. Sync to GitHub + PC
bash ~/sync-vault.sh
```

## Testing a Skill

Ask the agent to perform the skill's exact trigger scenario and verify it:
1. Follows the procedure (not a hallucinated alternative)
2. Uses the correct Pi paths
3. Produces the stated output
