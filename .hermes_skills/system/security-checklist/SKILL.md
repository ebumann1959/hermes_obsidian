---
name: security-checklist
description: "OWASP-based mechanical security review. Grep-driven checks for injection, hardcoded secrets, missing auth, unsafe deserialization, and exposed credentials. Run before any PR touching auth, DB, or external APIs."
version: 1.0.0
metadata:
  hermes:
    tags: [security, owasp, checklist, code-review, injection, secrets, auth]
    related_skills: [requesting-code-review, scope-check]
---

# Security Checklist

80% of real security bugs are mechanical — findable by grep. Run this before marking any security-adjacent task done. Not a substitute for Claude-level security review on complex auth flows, but catches the common stuff.

## Run the Full Checklist

```bash
PROJECT="$1"  # e.g., ~/shadys-analytics or ~/.hermes/show_runner
echo "=== Security scan: $PROJECT ==="
```

---

### 1. Hardcoded Secrets

```bash
# API keys, passwords, tokens hardcoded in source
grep -rn \
  'api_key\s*=\s*["\x27][^"${\x27]' \
  'password\s*=\s*["\x27][^"${\x27]' \
  'secret\s*=\s*["\x27][^"${\x27]' \
  'token\s*=\s*["\x27][^"${\x27]' \
  "$PROJECT" \
  --include="*.py" --include="*.js" --include="*.ts" --include="*.env" \
  2>/dev/null | grep -v "test_\|_test\|example\|placeholder\|your_"

# Anything that looks like a real key pattern
grep -rEn '[A-Za-z0-9]{32,}' "$PROJECT" \
  --include="*.py" --include="*.js" 2>/dev/null \
  | grep -i "key\|token\|secret\|pass" | grep -v "test\|example\|hash\|#" | head -10
```

**Flag if:** any result has a real-looking value (not `os.environ`, not a variable reference).

---

### 2. SQL Injection

```bash
# f-string or %-formatted SQL — never safe
grep -rEn 'execute\s*\(\s*f["\x27]|execute\s*\(\s*".*%s.*"\s*%' \
  "$PROJECT" --include="*.py" 2>/dev/null

# String concatenation into SQL
grep -rEn '"SELECT|"INSERT|"UPDATE|"DELETE' "$PROJECT" --include="*.py" 2>/dev/null \
  | grep -v "?" | grep "+" | head -10
```

**Flag if:** SQL string is built with f-string, `%` formatting, or `+` concatenation instead of parameterized `?` / `:param`.

---

### 3. Command Injection

```bash
# shell=True with any variable input
grep -rEn 'subprocess\.(run|call|Popen|check_output).*shell\s*=\s*True' \
  "$PROJECT" --include="*.py" 2>/dev/null

# os.system with f-string
grep -rEn 'os\.system\s*\(\s*f["\x27]' "$PROJECT" --include="*.py" 2>/dev/null

# eval/exec on external input
grep -rEn '\beval\s*\(|\bexec\s*\(' "$PROJECT" --include="*.py" 2>/dev/null \
  | grep -v "#\|test_" | head -10
```

**Flag if:** any `shell=True` where the command string contains a variable.

---

### 4. Missing Auth / Auth Bypass

```bash
# FastAPI / Flask routes without auth decorator
grep -rEn '@(app|router)\.(get|post|put|delete|patch)\(' "$PROJECT" --include="*.py" 2>/dev/null \
  | grep -v "dependencies\|Depends\|login_required\|require_auth\|@login" | head -20
```

**Flag if:** any route that should be protected lacks a dependency/decorator.

---

### 5. Unsafe Deserialization

```bash
# pickle.loads on untrusted input
grep -rEn 'pickle\.loads?\s*\(' "$PROJECT" --include="*.py" 2>/dev/null | head -5

# yaml.load without Loader (uses unsafe loader by default)
grep -rEn 'yaml\.load\s*\([^,)]+\)' "$PROJECT" --include="*.py" 2>/dev/null \
  | grep -v "Loader=" | head -5
```

**Flag if:** `pickle.loads()` on any input not from your own code, or `yaml.load()` without `Loader=yaml.SafeLoader`.

---

### 6. Credentials in Logs

```bash
# Logging statements that might include secrets
grep -rEn 'log\.(info|debug|warning|error).*\b(password|token|key|secret)\b' \
  "$PROJECT" --include="*.py" 2>/dev/null | head -10

# Print statements with auth context
grep -rEn 'print.*\b(password|token|api_key)\b' "$PROJECT" --include="*.py" 2>/dev/null | head -5
```

---

### 7. Environment Variables (Shadys-specific)

```bash
# Check no DSN or key is hardcoded in Shadys
grep -rEn 'postgresql://|mysql://|redis://' ~/shadys-analytics \
  --include="*.py" 2>/dev/null | grep -v "POSTGRES_DSN\|os.environ\|getenv\|config\[" | head -5

# Confirm all secrets go through env vars
grep -rEn 'MINIMAX_API_KEY\|DISCORD_TOKEN\|POSTGRES_DSN' ~/shadys-analytics \
  --include="*.py" 2>/dev/null | grep -v 'os.environ\|getenv\|environ\[' | head -5
```

---

## Checklist Summary Output

```bash
# Quick pass — print PASS/FAIL per check
run_check() {
    local name="$1"; local cmd="$2"
    result=$(eval "$cmd" 2>/dev/null)
    if [ -z "$result" ]; then echo "PASS: $name"
    else echo "FLAG: $name"; echo "$result" | head -3; fi
}

run_check "No hardcoded secrets" "grep -rEn 'api_key\s*=\s*[\"'\'''][^\"'\''\$\{]' $PROJECT --include='*.py' 2>/dev/null"
run_check "No shell=True injection" "grep -rEn 'shell\s*=\s*True' $PROJECT --include='*.py' 2>/dev/null"
run_check "No f-string SQL" "grep -rEn 'execute.*f[\"'\'']' $PROJECT --include='*.py' 2>/dev/null"
run_check "No unsafe yaml.load" "grep -rEn 'yaml\.load\(' $PROJECT --include='*.py' 2>/dev/null | grep -v Loader="
run_check "No pickle.loads" "grep -rEn 'pickle\.loads' $PROJECT --include='*.py' 2>/dev/null"
```

## Escalate to Claude if

- Any auth/session handling logic is changing
- JWT signing, token rotation, or permission scopes are involved
- A flag above has a hit you can't explain — don't guess, escalate
