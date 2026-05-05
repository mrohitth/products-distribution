# Security Audit Protocol — Mitty's Daily 11 PM Eastern Run

**Owner:** [M] Mitty  
**Schedule:** 11:00 PM Eastern daily (via OpenClaw cron: `ab1be4b3-4dc0-46fd-b185-058fc4847ec6`)  
**Trigger:** Automatic via cron OR on-demand via Mathew request

---

## What It Is

Daily automated security and compliance audit. Logs findings to `memory/YYYY-MM-DD.md` under `## Audit Findings`. Runs as Gemini Flash lightweight model with read-only tool access.

---

## Audit Checklist

### 1. SSH Access
- [ ] Check `~/.ssh/authorized_keys` — any unexpected keys?
- [ ] Check `auth.log` for failed SSH attempts from unusual IPs
- [ ] Confirm SSH key used is the expected one (no ROT13 jokes — we're serious)

### 2. Firewall Status
- [ ] Verify only expected ports are open (22, 443, 80, 3000 for KATZEN dev)
- [ ] Check for any `ufw allow` rules added since last audit
- [ ] Confirm no exposed services on public IPs that shouldn't be public

### 3. System Updates
- [ ] Check `apt update` + `apt upgrade` — any pending security patches?
- [ ] Check last boot time (`uptime`) — system recently rebooted?
- [ ] Verify OpenClaw auto-update hasn't broken anything

### 4. OpenClaw Session Audit
- [ ] Check for any unexpected sessions in `~/.openclaw/agents/main/sessions/`
- [ ] Verify cron jobs are as expected (no unexpected new jobs)
- [ ] Confirm `openclaw gateway status` shows healthy

### 5. Exposure Surface
- [ ] Check `~/.openclaw/openclaw.json` — any accidental credential exposure?
- [ ] Verify no API keys or tokens in repo files that shouldn't be there
- [ ] Check git remotes — are they the expected repos (mrohitth)?

### 6. Cron Jobs
- [ ] List all cron jobs via `cron action=list`
- [ ] Confirm expected: heartbeat (30 min), Mitty audit (11 PM), Capital Pilot (8 AM)
- [ ] Any disabled/enabled state changes since last audit?

### 7. Anomaly Detection
- [ ] Check recent login history (`last` command)
- [ ] Look for unusual agent spawning activity (too many sub-agents)
- [ ] Check token burn rate — any anomalous spikes?

---

## Severity Classification

| Severity | Definition | Action |
|----------|------------|--------|
| **CRITICAL** | Unauthorized access, credential exposure, malware indicators | Page Mathew immediately via Telegram |
| **HIGH** | Failed SSH attempts, unexpected cron changes, exposed services | Log + flag in daily journal |
| **MEDIUM** | Pending security updates, unusual session activity | Log + deferred fix |
| **LOW** | Routine check findings, no action needed | Log only |

---

## Output Format

```markdown
## Audit Findings — 2026-05-03

### Status: ✅ CLEAN / ⚠️ FINDINGS / 🚨 CRITICAL

### SSH Access
- [result] — [detail]

### Firewall
- [result] — [detail]

### System Updates
- [result] — [detail]

### OpenClaw Session Audit
- [result] — [detail]

### Exposure Surface
- [result] — [detail]

### Cron Jobs
- [result] — [detail]

### Anomaly Detection
- [result] — [detail]

### Action Items
- [ ] [item] — due [date]
```

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./index.md](./index.md) — Patterns index  
→ [../people/mitty.md](../people/mitty.md) — Mitty's profile