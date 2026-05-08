# Token Rate Delta Tracking

## Problem with started_at window queries
Querying sessions by `started_at > cutoff` misses active sessions that started before the window but are still burning tokens.

## Delta solution
Track cumulative total tokens in a history file; rate = (total_now - total_N_minutes_ago) / N minutes.

## History file format
```
timestamp,total_tokens
1749999600,48219320
1749999660,48220780
```

## Key insight
- `readings[0]` = oldest reading in the window (e.g., 5 minutes ago)
- `history[-1]` = most recent reading (now)
- `delta = total_now - total_5m_ago` = tokens burned in that window
- Rate (tok/min) = delta / minutes

## Windows tracked (1m, 5m, 15m, 60m)
Each as tok/min rate and absolute delta. Total is cumulative.

## Implementation
See `scripts/token_rate_bars.py` in this skill for the full Python implementation that runs every 10s via `${execi 10}` and writes output to `/tmp/hermes_token_rate.txt`.
