# ChromaDB Semantic Memory — Agent Guide

**Collection:** `session_log`  
**Server:** `localhost:8000` (HTTP, no auth)  
**What's in it:** Every Claude Code session Evan has had, converted to markdown and embedded. Also memory files and vault notes.  
**Updated:** nightly at 03:07 via cron, plus after every PC session via rsync Stop hook.

---

## Quick Start (Python)

```python
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000, ssl=False)
col    = client.get_collection("session_log")

# Semantic search
results = col.query(
    query_texts=["what decisions were made about show_runner WebSocket"],
    n_results=5,
)
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"[{meta['type']}] {meta['source']}")
    print(doc[:400])
    print()
```

---

## Metadata Fields

| Field | Type | Description |
|---|---|---|
| `source` | str | Absolute path to source markdown file |
| `project` | str | Project name (e.g. `"Home Evan"`, `"Home Evan Show Runner"`) |
| `type` | str | `"conversation"` \| `"memory"` \| `"note"` \| `"guide"` |
| `file_mtime` | float | Source file modification time (epoch seconds) |
| `chunk_index` | int | Position of this chunk within the source file |

---

## Common Queries

```python
# Find past decisions about a topic
col.query(query_texts=["show_runner exit detection fix"], n_results=5)

# Filter by type (only conversations)
col.query(
    query_texts=["asyncio cross-loop threading bug"],
    n_results=5,
    where={"type": {"$eq": "conversation"}},
)

# Filter by project
col.query(
    query_texts=["unity bridge spawn character"],
    n_results=5,
    where={"project": {"$eq": "Home Evan"}},
)

# Check what's indexed
col.count()                     # total chunks
client.list_collections()       # all collections
```

---

## What the `session_log` Collection Contains

- **Conversations** — Claude Code sessions from Evan's PC (`~/.claude/projects/`)  
  Path pattern: `/mnt/nvme/obsidian-vault/Conversations/<ProjectName>/<date>__<uuid8>.md`  
  Each session has frontmatter: `project`, `session_id`, `started_at`, `first_user_prompt`

- **Memory** — Per-project memory files synced from the PC  
  Path pattern: `/mnt/nvme/obsidian-vault/Memory/...`

- **Notes & Guides** — Any other `.md` in the vault (this file included)

---

## Safety Rules (for agents that write to Chroma)

- **Never run seed_chroma.py while more than 1 `chroma-mcp` process is running** — concurrent writers corrupt the HNSW index silently. The script enforces this via preflight.
- **Never call `collection.delete(where={...})` on this collection** — Rust segfaults above ~10k chunks. Always delete by explicit ID list.
- **Never call `collection.get(offset=N, where={...})`** — pagination + metadata filter is broken in current Chroma versions. Paginate without a `where` filter.
- **If the index is corrupt:** stop all chroma-mcp processes, `rm -rf /mnt/nvme/chromadb`, re-run `python3 /home/Evan/.claude/scripts/seed_chroma.py --full --force`. The vault markdown is the source of truth.

---

## Files

| File | Location | Purpose |
|---|---|---|
| `seed_chroma.py` | `/home/Evan/.claude/scripts/seed_chroma.py` | Vault → ChromaDB embeddings |
| `run_full_sync.py` | `/home/Evan/.claude/scripts/run_full_sync.py` | Nightly cron wrapper |
| `convert_conversations.py` | PC: `~/.claude/scripts/` | JSONL → markdown (runs on PC Stop hook) |
| Sync log | `/home/Evan/.claude/logs/sync.log` | Audit trail |
| Cron log | `/home/Evan/.claude/logs/cron.log` | Nightly run output |
