#!/bin/bash
# mitty_health_pulse.sh — Pure shell health check, zero token cost
# Runs every 5 min. Writes to /home/mathew/.cache/health_pulse.log
# Alert thresholds: RAM>75%, Disk>85%, Sessions>100MB

LOG="/home/mathew/.cache/health_pulse.log"
SESSIONS_DIR="/home/mathew/.openclaw/agents/main/sessions"
ALERT_RAM=75
ALERT_DISK=85
ALERT_SESS_MB=150

TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S%z)

# RAM: used/total percentage
RAM_PCT=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')

# Disk: root partition usage %
DISK_PCT=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

# Session size in MB
SESS_MB=$(du -sm "$SESSIONS_DIR" 2>/dev/null | awk '{print $1}')

# BAK file count
BAK_COUNT=$(find "$SESSIONS_DIR" -name "*.bak-*" 2>/dev/null | wc -l)

# Status
if   (( RAM_PCT > ALERT_RAM )) || (( DISK_PCT > ALERT_DISK )) || (( SESS_MB > ALERT_SESS_MB )); then
  STATUS="HEALTH_WARN"
else
  STATUS="HEALTH_OK"
fi

ENTRY="${TIMESTAMP} ${STATUS} RAM=${RAM_PCT}% DISK=${DISK_PCT}% SESSIONS=${SESS_MB}MB BAK=${BAK_COUNT}"

# Append to log
echo "$ENTRY" >> "$LOG"

# Alert if needed (logs to stderr so cron captures it)
if [[ "$STATUS" == "HEALTH_WARN" ]]; then
  echo "⚠️ Health Alert: RAM=${RAM_PCT}% DISK=${DISK_PCT}% SESSIONS=${SESS_MB}MB" >&2
fi