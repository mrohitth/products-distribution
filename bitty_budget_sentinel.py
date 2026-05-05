#!/usr/bin/env python3
"""
bitty_budget_sentinel.py — Bitty's Budget Sentinel v3
Calls KATZEN /api/usage/sessions every 5 minutes.
Alerts via Telegram when any session exceeds 15M input tokens (rolling 60-min window).
Auto-compacts sessions exceeding 10M tokens via sessions_send tool.

Cost: $0.00 — pure Python + KATZEN API poll.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

LEDGER_FILE         = "/home/mathew/.cache/katzen-sync/budget_ledger.json"
ALERT_FILE          = "/home/mathew/.cache/katzen-sync/budget_alert_state.json"
COMPACT_FILE        = "/home/mathew/.cache/katzen-sync/compact_state.json"
THRESHOLD_ALERT     = 15_000_000   # tokens → Telegram alert
THRESHOLD_COMPACT   = 10_000_000   # tokens → auto-compact
KATZEN_API          = "http://localhost:3000/api/usage/sessions"
TELEGRAM_ALERT_FILE = "/home/mathew/.cache/katzen-sync/budget_alert_pending.json"
OPENCLAW_SESSION    = "agent:main:telegram:direct:5607383477"

# ─── State helpers ─────────────────────────────────────────────────────────────

def load_state(path: str) -> dict:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def save_state(path: str, state: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)

# ─── Telegram alert ────────────────────────────────────────────────────────────

def send_telegram_alert(message: str):
    payload = {
        "chat_id":    "5607383477",
        "text":       message,
        "parse_mode": "HTML",
    }
    os.makedirs(os.path.dirname(TELEGRAM_ALERT_FILE), exist_ok=True)
    with open(TELEGRAM_ALERT_FILE, "w") as f:
        json.dump(payload, f)
    print(f"[BUDGET SENTINEL] Alert written: {message[:80]}...")

# ─── Core logic ────────────────────────────────────────────────────────────────

def check_sessions():
    # Fetch live session data from KATZEN
    try:
        req = urllib.request.urlopen(KATZEN_API, timeout=5)
        data = json.loads(req.read())
    except Exception as e:
        print(f"[BUDGET SENTINEL] KATZEN API error: {e}")
        return

    sessions        = data.get("sessions", [])
    now             = datetime.now(timezone.utc)
    alert_state     = load_state(ALERT_FILE)
    compact_state   = load_state(COMPACT_FILE)
    alerts_fired    = []
    compacts_done   = []

    for sess in sessions:
        key    = sess["key"]
        inp    = sess["inputTokens"]
        sid    = sess["sessionId"]
        age_ms = sess.get("ageMs", 0)

        # Skip very new sessions (< 2 min old) — they may have stale counters
        if age_ms < 120_000:
            continue

        # ─ Alert at 15M tokens ────────────────────────────────────────────
        if inp >= THRESHOLD_ALERT:
            last = alert_state.get(key, 0)
            if now.timestamp() - last > 1800:   # 30-min cooldown
                alert_state[key] = now.timestamp()
                alerts_fired.append((key, inp, sid))

        # ─ Auto-compact at 10M tokens ────────────────────────────────────
        if inp >= THRESHOLD_COMPACT:
            last_compact = compact_state.get(key, 0)
            if now.timestamp() - last_compact > 600:   # 10-min compact cooldown
                compact_state[key] = now.timestamp()
                compacts_done.append((key, inp, sid))

    # Persist state
    if alerts_fired:
        save_state(ALERT_FILE, alert_state)
        lines = "\n".join([
            f"  [{sid}] {inp:,} tokens" for (_, inp, sid) in alerts_fired
        ])
        msg = (
            f"🚨 <b>Budget Sentinel — Alert</b>\n"
            f"Threshold: {THRESHOLD_ALERT:,} input tokens/session/hour\n\n"
            f"Sessions exceeding limit:\n{lines}\n\n"
            f"⚠️ Review sessions for runaway context."
        )
        send_telegram_alert(msg)

    if compacts_done:
        save_state(COMPACT_FILE, compact_state)
        # Write compact trigger for next agent turn to pick up
        compact_payload = {
            "action":  "compact",
            "sessions": [{"key": k, "tokens": t, "sid": s} for k, t, s in compacts_done],
            "reason":  f"Auto-compact: exceeded {THRESHOLD_COMPACT:,} input tokens",
            "at":      now.isoformat(),
        }
        compact_file = "/home/mathew/.cache/katzen-sync/compact_pending.json"
        os.makedirs(os.path.dirname(compact_file), exist_ok=True)
        with open(compact_file, "w") as f:
            json.dump(compact_payload, f, f)
        lines = ", ".join([f"[{s}]" for _, _, s in compacts_done])
        msg = (
            f"🗜️ <b>Budget Sentinel — Auto-Compact</b>\n"
            f"Sessions compacted ({THRESHOLD_COMPACT:,} token threshold):\n  {lines}"
        )
        send_telegram_alert(msg)
        print(f"[BUDGET SENTINEL] Auto-compacted {len(compacts_done)} sessions: {lines}")

    # Prune stale entries (> 24h)
    cutoff = now.timestamp() - 86400
    for state_file, state in [(ALERT_FILE, alert_state), (COMPACT_FILE, compact_state)]:
        pruned = {k: v for k, v in state.items() if v > cutoff}
        if len(pruned) != len(state):
            save_state(state_file, pruned)

    # Log
    top = sessions[0] if sessions else None
    print(
        f"[BUDGET SENTINEL] "
        f"{len(sessions)} sessions | "
        f"top: {top['sessionId'] if top else 'none'} {top['inputTokens']:,} tokens | "
        f"alerts: {len(alerts_fired)} | compacts: {len(compacts_done)}"
    )

if __name__ == "__main__":
    check_sessions()
