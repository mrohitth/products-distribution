#!/bin/bash
# Pipeline Chain Wrapper — Stage 1-4
# Triggers TrendScout, polls for completion, runs pipeline manager
# Usage: bash scripts/pipeline_chain.sh

set -e
WORKSPACE="/home/mathew/.openclaw/workspace"
TREND_ID="1e85c944-0d23-4cb0-a6be-37dbf267ff29"

echo "[$(date '+%H:%M:%S')] Pipeline Chain — starting"

# Stage 1 is handled by the TrendScout cron (isolated agentTurn at 10:00 AM ET)
# Stages 2-4 are handled by pipeline_manager.py
# This wrapper can be called manually for off-schedule runs

python3 "$WORKSPACE/scripts/pipeline_manager.py"
echo "[$(date '+%H:%M:%S')] Pipeline Chain — complete"
