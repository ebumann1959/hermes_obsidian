---
name: claims-ai
status: active
stack: python, chromadb, claude, sentence-transformers
host: ''
port: ''
path: /mnt/Data/claims_ai
last_updated: 2026-05-09
tags: [pc, rag, insurance, acc]
---

## Overview
RAG assistant for ACC's roofing insurance supplementation workflow. Drafts arguments, surfaces precedent, answers claim-specific questions using ChromaDB + Claude.

## Current State
- Knowledge base ingested (38 files from Obsidian battle book, SOPs, templates, IRC codes)
- ClaimWizard, QuickBooks, email integrations TBD (user working on exports/API access)

## Blockers
- ClaimWizard data: needs API or CSV export from user
- QuickBooks: TBD
- Email (Gmail IMAP or .eml): TBD

## Key Facts
- Project root: `/mnt/Data/claims_ai/`
- Venv: `/mnt/Data/claims_ai/.venv`
- ChromaDB: PersistentClient at `/mnt/Data/claims_ai/chroma_data/`
- Embeddings: `BAAI/bge-base-en-v1.5` (sentence-transformers)
- Query model: `claude-sonnet-4-6` (Anthropic API)
- Obsidian knowledge vault: `/mnt/Data/claims_ai/vault/07-knowledge/`
- ChromaDB collections: `supp_knowledge`, `supp_claims`, `supp_line_items`, `supp_financials`, `supp_emails`, `supp_docs`
- Scripts: `ingest_knowledge.py`, `ingest_claimwizard.py`, `ingest_docs.py`, `ingest_email.py`, `rag_query.py`

## Decisions
- Separate ChromaDB instance per project (not shared with Pi's port 8000)
- One collection per data source for clean retrieval separation
