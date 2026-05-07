#!/bin/bash
#
# mitty_security_audit.sh — Mitty Security Audit
# Pure shell, zero token cost. Runs 11 PM ET daily.
# Checks: SSH, Firewall, Gateway, Cron health, RAM, Filesystem.
# Positive Standard: Python/Bash only — NO Spark, NO Kafka, NO Snowflake, NO EMR.
#
# Exit codes: 0 = clean, 1 = issues found
#
set -euo pipefail

LOG_FILE="${LOG_FILE:-/tmp/mitty_security_audit_$(date +%Y%m%d).log}"
MEMORY_DIR="/home/mathew/.openclaw/workspace/memory"
AUDIT_DATE="$(date +%Y-%m-%d)"
MEMORY_FILE="$MEMORY_DIR/${AUDIT_DATE}.md"
ALERT_THRESH_RAM=80
ALERT_THRESH_DISK=85
FOUND_ISSUES=0

log()  { echo "[$(date '+%Y-%m-%d %I:%M:%S %p ET')] $*" | tee -a "$LOG_FILE"; }
crit() { echo "[CRIT] $*" >&2; FOUND_ISSUES=$((FOUND_ISSUES+1)); }

log "🔒 Mitty Security Audit — START"

# ─── 1. SSH Check ──────────────────────────────────────────────────────────
SSH_STATUS=$(systemctl is-active ssh 2>/dev/null || systemctl is-active sshd 2>/dev/null || echo "inactive")
if [[ "$SSH_STATUS" == "active" ]]; then
  crit "SSH is ACTIVE — should be disabled on personal workstation"
else
  log "SSH: inactive ✅"
fi

# ─── 2. Firewall Check ───────────────────────────────────────────────────────
FW_STATUS=$(systemctl is-active ufw 2>/dev/null || systemctl is-active firewalld 2>/dev/null || echo "inactive")
if [[ "$FW_STATUS" == "active" ]]; then
  log "Firewall: active ✅"
else
  log "Firewall: inactive (no firewall detected)"
fi

# ─── 3. Gateway Check ──────────────────────────────────────────────────────
GW_OUTPUT=$(openclaw gateway status 2>/dev/null || echo "unknown")
if echo "$GW_OUTPUT" | grep -qiE "systemd|running|service|active"; then
  log "Gateway: running ✅"
else
  crit "Gateway may not be running — check 'openclaw gateway status'"
fi

# ─── 4. Cron Health ─────────────────────────────────────────────────────────
_raw=$(openclaw cron list --json 2>/dev/null || echo '{"jobs":[]}')
CRON_ERRORS=$(printf '%s' "$_raw" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(sum(j["state"].get("consecutiveErrors",0) for j in d["jobs"]))' 2>/dev/null || echo "0")
CRON_ERRORS=${CRON_ERRORS//[^0-9]/}
CRON_ERRORS=${CRON_ERRORS:-0}
if [[ "$CRON_ERRORS" != "0" ]] && [[ -n "$CRON_ERRORS" ]]; then
  crit "Cron jobs have $CRON_ERRORS consecutive error(s)"
else
  log "Cron health: no consecutive errors ✅"
fi

# ─── 5. RAM Check ───────────────────────────────────────────────────────────
RAM_PCT=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
if (( RAM_PCT > ALERT_THRESH_RAM )); then
  crit "RAM at ${RAM_PCT}% — above ${ALERT_THRESH_RAM}% threshold"
else
  log "RAM: ${RAM_PCT}% ✅"
fi

# ─── 6. Filesystem Check ─────────────────────────────────────────────────────
DISK_PCT=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if (( DISK_PCT > ALERT_THRESH_DISK )); then
  crit "Disk at ${DISK_PCT}% — above ${ALERT_THRESH_DISK}% threshold"
else
  log "Disk: ${DISK_PCT}% ✅"
fi

# ─── 7. Recent failed logins ────────────────────────────────────────────────
FAILED_LOGINS=$(journalctl --since "24 hours ago" -u ssh 2>/dev/null | grep -ciE "failed|invalid" 2>/dev/null || echo "0")
FAILED_LOGINS=${FAILED_LOGINS:-0}
if [[ "$FAILED_LOGINS" != "0" ]] && [[ -n "$FAILED_LOGINS" ]]; then
  if (( FAILED_LOGINS > 5 )); then
    log "Failed logins (24h): $FAILED_LOGINS — investigate if unexpected"
  else
    log "Failed logins (24h): $FAILED_LOGINS ✅"
  fi
else
  log "Failed logins (24h): 0 ✅"
fi

# ─── 8. Sessions size ───────────────────────────────────────────────────────
SESS_SIZE=$(du -sm /home/mathew/.openclaw/agents/main/sessions/ 2>/dev/null | awk '{print $1}')
if (( SESS_SIZE > 200 )); then
  log "Sessions dir: ${SESS_SIZE}MB — consider cleanup if >200MB"
else
  log "Sessions dir: ${SESS_SIZE}MB ✅"
fi

# ─── Summary ────────────────────────────────────────────────────────────────
log "🔒 Mitty Security Audit — END. Issues found: $FOUND_ISSUES"

if (( FOUND_ISSUES == 0 )); then
  log "✅ Audit clean — SSH inactive, Gateway up, RAM ${RAM_PCT}%, Disk ${DISK_PCT}%, Cron OK."
  EXIT_CODE=0
else
  log "⚠️ Audit found $FOUND_ISSUES issue(s) — review log: $LOG_FILE"
  EXIT_CODE=1
fi

# ─── Append to memory log ────────────────────────────────────────────────
if [[ -f "$MEMORY_FILE" ]]; then
  python3 - <<PYEOF 2>/dev/null || true
audit_date = '$AUDIT_DATE'
memory_file = '$MEMORY_FILE'
summary = '''## Audit Findings\nSSH: $SSH_STATUS | Firewall: $FW_STATUS | Gateway: systemd OK\nCron consecutive errors: $CRON_ERRORS | RAM: ${RAM_PCT}% | Disk: ${DISK_PCT}%\nSessions: ${SESS_SIZE}MB | Failed logins (24h): ${FAILED_LOGINS}\n'''
with open(memory_file, 'a') as f:
    f.write(audit_date + ': ' + summary + '\n')
PYEOF
  log "Audit findings appended to $MEMORY_FILE"
else
  log "Memory file not found: $MEMORY_FILE — skipping append"
fi

exit $EXIT_CODE
