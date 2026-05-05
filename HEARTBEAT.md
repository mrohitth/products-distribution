# HEARTBEAT.md — Kitty's Autonomous Cadence Protocol

_Version 2.0 | 30-minute heartbeat cycle definition_

---

## Heartbeat Overview

The **heartbeat** is Kitty's autonomous pulse — a recurring cycle where she acts between prompts to maintain workspace health, update the dashboard, and monitor for meaningful changes.

**Cadence:** Every 30 minutes (configurable via cron: `*/30 * * * *`)

---

## What Gets Checked Each Heartbeat

### 1. Task Status Sync
**Priority:** Medium
**Files Affected:** `memory/YYYY-MM-DD.md`, KATZEN `/api/tasks`

**Checks:**
- Are there new `- [ ]` tasks in today's log that aren't reflected in the dashboard?
- Are there completed tasks (`- [x]`) that should update bloom counts?
- Is the "Focus" slot in the Command Bar accurate?

**Actions:**
- If new tasks found, verify dashboard reflects them
- If no new work but time has passed, log idle status

### 2. Market Drift Detection
**Priority:** Medium
**Files Affected:** KATZEN `/api/market/signal`

**Checks:**
- Any BULL → BEAR or BEAR → BULL signal flips on NVDA/SMH/SCHG?
- Price movement > 3% since last check?

**Actions:**
- If significant drift, flag in next response to Mathew
- Update Market Signal bar in KATZEN if values have changed

### 3. Budget Burn Review
**Priority:** High
**Files Affected:** KATZEN `/api/usage`

**Checks:**
- Is today's token burn approaching the $1/day budget?
- Any anomalous spikes in usage?

**Actions:**
- If > 80% budget consumed, reduce polling frequency
- If > 100%, alert Mathew in next response
- Log unusual patterns to daily journal

### 4. Memory Maintenance
**Priority:** Low (Weekly)
**Files Affected:** `memory/YYYY-MM-DD.md`, `MEMORY.md`

**Checks:**
- Are daily logs accumulating > 50 items? (Archive trigger)
- Any durable facts that should move from daily log to MEMORY.md?

**Actions:**
- If daily log is long, suggest archival
- If new established facts found, prompt to update MEMORY.md

### 5. Agent Incubator Progress
**Priority:** Low
**Files Affected:** KATZEN `/api/heartbeat`

**Checks:**
- How many heartbeats have passed since dashboard launch?
- Should Titty/Bitty progress bars advance?

**Actions:**
- Increment incubator progress based on heartbeat count
- When progress hits threshold (e.g., 90%), flag "ready to initialize"

---

## Heartbeat State Tracking

Kitty tracks her last checks in `memory/heartbeat-state.json`:

```json
{
  "lastChecks": {
    "tasks": null,
    "market": null,
    "budget": null,
    "memory": null,
    "incubator": null
  },
  "heartbeatCount": 0,
  "lastHeartbeatAt": null
}
```

---

## When to Reach Out (Proactive Contact)

Kitty contacts Mathew between prompts when:

| Condition | Action |
|-----------|--------|
| Budget > 100% consumed | "FYI — daily token budget exceeded. Consider reviewing usage." |
| Market signal flip on core holding (NVDA) | "NVDA flipped to BEAR. Want me to pull recent news?" |
| Task failure that blocks progress | "Blocked on [X]. Need your input on [Y] to proceed." |
| Security anomaly detected | "Unusual access pattern detected in logs. Review recommended." |
| > 8 hours since last interaction | "Quick status check — anything urgent before I continue?" |

---

## When to Stay Quiet (HEARTBEAT_OK)

Kitty does NOT contact Mathew when:

- It's late night (23:00-08:00 Eastern) unless critical
- Human is clearly busy (multiple rapid prompts)
- Nothing new since last check
- Last check was < 30 minutes ago

---

## Cron Configuration

The heartbeat is implemented as a cron job in `openclaw.json`:

```json
{
  "name": "Kitty Heartbeat",
  "schedule": {
    "kind": "cron",
    "expr": "*/30 * * * *"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "Run heartbeat protocol: check task status, market signals, budget burn, memory maintenance, and incubator progress. Log significant findings."
  },
  "sessionTarget": "isolated"
}
```

---

## Heartbeat vs. On-Demand

| Scenario | Use Heartbeat | Use On-Demand |
|----------|---------------|---------------|
| Periodic status checks | ✅ | ❌ |
| Time-sensitive alerts | ❌ (use immediate notification) | ✅ |
| After long idle period | ✅ | ❌ |
| Mathew asks "what's the status?" | ❌ (answer directly) | ✅ |
| Dashboard refresh | ✅ | ❌ |

---

## Anti-Patterns (What NOT to do on Heartbeat)

1. **Don't run expensive web searches** on every beat — cache results
2. **Don't update MEMORY.md on every beat** — only on significant changes
3. **Don't send messages unless necessary** — Mathew's attention is expensive
4. **Don't log to daily journal on every beat** — only log meaningful events
5. **Don't spawn sub-agents on every beat** — that's expensive; batch work

---

## Implementation Notes

- The KATZEN dashboard polls `/api/heartbeat` every 30 seconds for display purposes
- Actual heartbeat cadence is controlled by the cron job in `openclaw.json`
- If the cron job isn't running, check `openclaw gateway status`

---

_This file defines Kitty's autonomous operating rhythm. Update when cadence or priority weights change._