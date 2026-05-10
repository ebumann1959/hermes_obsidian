---
name: test-driven-development
description: "RED-GREEN-REFACTOR cycle for writing tests on the Pi. Covers pytest for Python, and shell-based integration tests for show_runner and Hermes workflows."
version: 1.0.0
metadata:
  hermes:
    tags: [tdd, testing, pytest, integration-test]
---

# Test-Driven Development

## The Cycle

1. **RED** — write a failing test that describes the desired behavior
2. **GREEN** — write the minimum code to make it pass
3. **REFACTOR** — clean up without breaking the test

Never skip RED. Running a test that passes immediately means the test is wrong.

## Python (pytest)

```bash
# Install in venv if needed
source ~/.hermes/hermes-agent/venv/bin/activate
pip install pytest

# Run tests
python3 -m pytest tests/ -x -q        # stop on first failure, quiet
python3 -m pytest tests/ -v            # verbose, see each test name
python3 -m pytest tests/test_foo.py::TestBar::test_baz  # single test
```

### Test file structure

```python
# tests/test_dialogue_engine.py
import pytest
from core.dialogue_engine import DialogueEngine

def test_strips_think_blocks():
    engine = DialogueEngine()
    raw = "<think>internal</think>Hello world"
    assert engine.strip_think(raw) == "Hello world"

def test_empty_response_triggers_retry(monkeypatch):
    # ...
```

## Shell Integration Tests

For show_runner and Hermes workflows, use a simple shell test harness:

```bash
#!/bin/bash
# tests/smoke_test.sh
set -e

PASS=0; FAIL=0

check() {
    local desc="$1"; local cmd="$2"; local expected="$3"
    actual=$(eval "$cmd" 2>&1)
    if echo "$actual" | grep -q "$expected"; then
        echo "PASS: $desc"; ((PASS++))
    else
        echo "FAIL: $desc"; echo "  Expected: $expected"; echo "  Got: $actual"; ((FAIL++))
    fi
}

check "WebSocket listening" "ss -tlnp | grep 8765" "8765"
check "State DB accessible" "sqlite3 ~/.hermes/state.db '.tables'" "sessions"

echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ]
```

## What to Test

**Test these:** pure functions, data transformations, message parsing, state transitions
**Don't test:** external APIs (mock them), file paths (use tmp), UI rendering

## Coverage Quick Check

```bash
pip install pytest-cov
python3 -m pytest --cov=core --cov-report=term-missing tests/
```
