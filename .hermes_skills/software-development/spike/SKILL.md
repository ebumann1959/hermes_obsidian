---
name: spike
description: "Throwaway experiment to validate an idea before committing to implementation. Use when uncertain about an API, library, or approach."
version: 1.0.0
metadata:
  hermes:
    tags: [spike, investigation, prototyping, validation]
---

# Spike

A spike is a time-boxed throwaway experiment. The goal is a yes/no answer to a technical question, not working code.

## When to Use
- You're not sure if a library/API works the way you think
- An approach has never been tried in this codebase
- The plan has an assumption that needs validating

## Process

```bash
# 1. Create spike directory (always throwaway)
mkdir -p /tmp/spike-<question-slug>
cd /tmp/spike-<question-slug>

# 2. Write the minimal code to answer the question
# 3. Run it
# 4. Write the answer as a one-liner
echo "RESULT: <library X does/does not support Y because Z>" > result.txt

# 5. Copy relevant snippet to the real codebase if useful, then delete spike
rm -rf /tmp/spike-<question-slug>
```

## Rules
- Spike files NEVER go in the real repo — always `/tmp/`
- Time-box to 15 minutes. If you can't answer in 15 min, the question is too broad
- The output is a **decision**, not code. Write it as "We will / We won't use X because Y"
- After a spike, update the plan's Paths section with what you learned

## Example

```bash
# Question: does MiniMax API support streaming?
mkdir -p /tmp/spike-minimax-streaming
cat > /tmp/spike-minimax-streaming/test.py << 'EOF'
import openai, os
client = openai.OpenAI(
    api_key=os.environ["MINIMAX_API_KEY"],
    base_url="https://api.minimax.chat/v1"
)
stream = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[{"role":"user","content":"say hi"}],
    stream=True
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="", flush=True)
EOF
python3 /tmp/spike-minimax-streaming/test.py
# RESULT: streaming works, use stream=True in dialogue_engine.py
```
