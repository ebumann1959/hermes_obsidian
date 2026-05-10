---
name: paperclip-edge
status: active
stack: python3.13, duckdb, pandas, streamlit, httpx
host: ''
port: ''
path: /home/Evan/paperclip-edge
last_updated: 2026-05-09
tags: [local, trading, sports-betting]
---

## Overview
Fully local dual-engine research tool: sports betting (+EV, CLV, props, line movement) and stock swing trading (TA signals, momentum, options).

## Current State
Architecture defined, build order agreed. Not yet fully built.

## Blockers
- `ODDS_API_KEY` (The Odds API) — TBD
- `SCHWAB_CLIENT_ID` / `SCHWAB_CLIENT_SECRET` (Schwab API) — TBD

## Key Facts
- DB: `data/paperclip.duckdb` (DuckDB, local only)
- Package layout:
  - `paperclip/core/` — kelly.py, ev.py, backtest.py (shared statistical core, build first)
  - `paperclip/sports/` — ingest.py (The Odds API)
  - `paperclip/stocks/` — ingest.py (Schwab + yfinance)
  - `paperclip/db/` — schema.py (DuckDB bootstrap)
  - `paperclip/dashboard/` — app.py (Streamlit)
  - `tests/` — mirrors core/

## Decisions
- No cloud infra — fully local
- Kelly + EV are shared statistical primitives for both engines
- Engines decoupled but share core/
- Build order: core/ → sports/ ingest → stocks/ ingest → dashboard
