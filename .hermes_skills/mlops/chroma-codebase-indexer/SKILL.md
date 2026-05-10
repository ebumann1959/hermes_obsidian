---
name: chroma-codebase-indexer
description: "Index a codebase into ChromaDB so Hermes can retrieve relevant functions/classes by semantic search before editing. Solves context-window exhaustion on large projects."
version: 1.0.0
metadata:
  hermes:
    tags: [chroma, rag, codebase, search, context, indexing, semantic-search]
    related_skills: [decompose-task, verify-before-write]
---

# Chroma Codebase Indexer

Before editing a large codebase, index it. Then query instead of reading whole files — pull only the 3-5 most relevant chunks into context.

## Index a Project

```bash
# Index show_runner (Pi-side)
python3 ~/.hermes/scripts/index_codebase.py ~/.hermes/show_runner --collection show_runner

# Index shadys-analytics
python3 ~/.hermes/scripts/index_codebase.py ~/shadys-analytics --collection shadys

# Index Unity scripts on PC
ssh Evan@10.0.0.91 "cat /mnt/Data/show_runner/Assets/ShowRunner/Scripts/*.cs" > /tmp/unity_scripts_combined.txt
# (Unity C# — index the Pi-side copy after ssh-reading the files)
```

Indexes live at `~/.hermes/chroma_codebase/`. Re-run after significant code changes.

## Query Before Editing

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, "/home/Evan/.hermes/hermes-agent/venv/lib/python3.11/site-packages")
import chromadb

client = chromadb.PersistentClient(path="/home/Evan/.hermes/chroma_codebase")
col = client.get_collection("show_runner")   # or "shadys"

results = col.query(
    query_texts=["WebSocket reconnect backoff exponential"],
    n_results=4,
)

for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
    print(f"\n--- Result {i+1}: {meta['path']} lines {meta['start_line']}-{meta['end_line']} ---")
    print(doc[:600])
EOF
```

## Workflow: Query → Read Exact Lines → Edit

```bash
# 1. Query for relevant context
# (run query above — note path + line numbers)

# 2. Read the exact section
sed -n '<start_line>,<end_line>p' ~/.hermes/show_runner/<path>

# 3. Now edit with full context (diff-workflow)
# Only load what the query returned — not the whole file
```

## Which Collections Exist

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, "/home/Evan/.hermes/hermes-agent/venv/lib/python3.11/site-packages")
import chromadb
client = chromadb.PersistentClient(path="/home/Evan/.hermes/chroma_codebase")
for c in client.list_collections():
    print(f"{c.name}: {c.count()} chunks")
EOF
```

## Re-index Trigger

Re-index when:
- A new module or file is added
- A function is renamed or moved
- The project structure changes significantly

Re-indexing is fast (<30s for shadys or show_runner). Add to the plan's verification step for any large refactor.

## Query Tips

- Search by **behavior** not **name**: "reconnect on disconnect" not "Connect()"
- Search by **error symptom**: "content_filter finish_reason empty response"
- Search by **data flow**: "spatial telemetry zone character_id"
- Use 4-6 results (`n_results=4`) — more than that usually adds noise
