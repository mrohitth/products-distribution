#!/bin/bash
# Weekly /tmp deep clean — removes files >500MB older than 12h
LOGFILE="$HOME/.openclaw/workspace/logs/tmp-cleanup.log"
mkdir -p "$(dirname "$LOGFILE")"
echo "[$(date)] Cleaning /tmp..." >> "$LOGFILE"
find /tmp -type f -size +500M -mmin +720 -delete -print >> "$LOGFILE" 2>&1
echo "[$(date)] Done" >> "$LOGFILE"
