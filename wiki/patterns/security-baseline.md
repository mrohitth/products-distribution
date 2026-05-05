# Security Baseline — Mitty's Reference Document

**Owner:** [M] Mitty | **Owner:** [K] Kitty  
**Type:** Security Pattern | **Scope:** Daily 11 PM Eastern Audit  
**Docs Ref:** [OpenClaw Security](https://docs.openclaw.ai/gateway/security)

---

## Security Model

OpenClaw operates a **personal assistant trust model** — one trusted operator boundary per gateway. The host (`~/.openclaw/`) and config are trusted; Mitty treats them as safe.

**Not in scope:** Hostile multi-tenant isolation. This is a single-user workspace.

---

## Trust Boundary Matrix (Quick Reference)

| Boundary | What It Means | Mitty's Check |
|----------|---------------|---------------|
| `gateway.auth` | Authenticates callers to gateway APIs | Token/password not exposed in workspace files |
| `~/.openclaw/openclaw.json` | Gateway config + credentials | No accidental credential exposure |
| `authorized_keys` | SSH access control | No unexpected keys |
| Cron jobs | Scheduled task surface | Only expected jobs running |
| Exec approvals | Guardrails for operator intent | No unauthorized exec policy changes |

---

## Mitty's Daily Audit Checklist

### 1. SSH Access
```bash
# Check authorized keys
cat ~/.ssh/authorized_keys

# Check recent failed SSH attempts
grep "Failed password" /var/log/auth.log | tail -20

# Check successful logins
last -20
```

**Trigger:** Any unexpected key or unusual IP source → CRITICAL

---

### 2. Gateway Config & Credentials
```bash
# Check openclaw.json for exposed keys
cat ~/.openclaw/openclaw.json | grep -i "key\|token\|secret\|password"

# Run OpenClaw security audit
openclaw security audit
openclaw security audit --deep
```

**Trigger:** Any hardcoded credential in workspace files → CRITICAL

---

### 3. Cron Job Integrity
```bash
# List all cron jobs
openclaw cron list

# Expected jobs:
# - Kitty Heartbeat:     every 30 min
# - Capital Pilot:       daily 8:00 AM EST
# - Mitty Security Audit: daily 11:00 PM EST
```

**Trigger:** Unknown cron job added → HIGH

---

### 4. Memory/File Exposure
```bash
# Scan workspace for exposed keys
grep -r "sk-\|api_key\|token\|secret" ~/.openclaw/workspace/ --include="*.md" --include="*.json" -l

# Check git remotes
cd ~/.openclaw/workspace && git remote -v
# Must be: mrohitth repos only
```

**Trigger:** Exposed key in workspace files → CRITICAL  
**Trigger:** Unknown git remote → HIGH

---

### 5. RAM & Process Health (Zombie Check)
```bash
# Check RAM availability
free -m

# Check for zombie processes
ps aux | grep -E "defunct|Z" | grep -v grep

# Top memory consumers
ps aux --sort=-%mem | head -10

# OpenClaw process check
pgrep -a openclaw
```

**Thresholds:**
| Metric | Safe | Warning | Critical |
|--------|------|---------|----------|
| Available RAM | > 500MB | 200-500MB | < 200MB |
| Zombies | 0 | 1-3 | > 3 |
| openclaw memory | < 1.5GB | 1.5-2.5GB | > 2.5GB |

---

### 6. OpenClaw Gateway Health
```bash
# Gateway status
openclaw gateway status

# Check for crashed/errored sessions
ls ~/.openclaw/agents/main/sessions/
```

**Trigger:** Gateway not healthy → HIGH  
**Trigger:** Multiple errored sessions → MEDIUM

---

### 7. Filesystem Permissions
```bash
# Check workspace permissions
ls -la ~/.openclaw/workspace/

# No world-writable files
find ~/.openclaw -type f -perm -002 2>/dev/null | grep -v ".next"
```

**Trigger:** World-writable sensitive files → HIGH

---

## Severity & Response

| Severity | Definition | Action |
|----------|------------|--------|
| **CRITICAL** | Exposed keys, unauthorized access, malware indicators | Page Mathew via Telegram immediately |
| **HIGH** | Unexpected cron changes, unknown git remotes, gateway unhealthy | Log + flag in journal |
| **MEDIUM** | RAM pressure, zombie processes, gateway degraded | Log + schedule fix |
| **LOW** | Routine clean findings | Log only |

---

## Audit Output Template

```markdown
## Audit Findings — YYYY-MM-DD

**Time:** 11:00 PM EST  
**Agent:** Mitty [M]  
**Gateway Health:** ✅ / ⚠️ / 🚨

### 1. SSH Access — [PASS/FAIL]
**Findings:** ...

### 2. Gateway Config — [PASS/FAIL]
**Findings:** ...

### 3. Cron Jobs — [PASS/FAIL]
**Findings:** ...

### 4. Memory/File Exposure — [PASS/FAIL]
**Findings:** ...

### 5. RAM & Process Health — [PASS/FAIL]
**Memory Used:** XGB / 8GB  
**Available:** XGB  
**Zombies:** N  
**Status:** ...

### 6. OpenClaw Gateway — [PASS/FAIL]
**Findings:** ...

### 7. Filesystem Permissions — [PASS/FAIL]
**Findings:** ...

### Action Items
- [ ] [item] — due [date]
```

---

## Key Files & Paths

| Path | Purpose |
|------|---------|
| `~/.openclaw/openclaw.json` | Gateway config — check for credential exposure |
| `~/.openclaw/agents/main/agent/auth-profiles.json` | API keys (MiniMax etc.) — must not be in workspace |
| `~/.openclaw/workspace/` | Workspace files — scan for leaked credentials |
| `~/.ssh/authorized_keys` | SSH access — verify only expected keys |
| `/var/log/auth.log` | SSH login attempts |
| `~/.openclaw/workspace/memory/` | Daily logs — Mitty writes audit findings here |

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./index.md](./index.md) — Patterns index  
→ [./security-audit-protocol.md](./security-audit-protocol.md) — Full audit protocol  
→ [../people/mitty.md](../people/mitty.md) — Mitty's profile