# Gateway Router Implementation — v2.0

**Date:** 2026-05-03  
**Updated by:** Mathew  
**Status:** ✅ LIVE — v2.0

---

## What Changed

**Deprecated:** "Context-Only" escalation — routing purely based on how much context a task needs.

**Replaced by:** "Reasoning Depth" escalation — routing based on how many reasoning steps, cross-domain connections, or iterative loops a task is expected to require.

---

## New Escalation Ladder

| Level | Agent | Model | Cost/1M in | Cost/1M out | Trigger |
|-------|-------|-------|-----------|-------------|---------|
| **L1 Routine** | Gateway | DeepSeek V4 Flash | $0.07 | $0.27 | Simple lookups, status checks, file reads |
| **L2 Technical** | Titty | MiniMax M2.7 | $0.30 | $1.20 | Linear ETL tasks, bulk docs, standard Python boilerplate |
| **L3 Strategic** | Kitty | DeepSeek V4 Pro | $0.50 | $2.00 | Cross-domain logic, architectural refactoring, recursive debugging |

---

## Triage Rule (L1 Flash)

Before routing any task to Titty, Flash performs a **Complexity Audit**. Escalate directly to Kitty (V4 Pro) — bypassing Titty — if ANY of the following is true:

### A. Cross-Domain Logic
The task mixes distinct technical domains in a non-trivial way:
- dbt SQL logic + Next.js frontend state management simultaneously
- PostgreSQL schema changes + Airflow DAG restructure together
- Python CDC extraction + TypeScript API route changes in one pass
- **Rule:** If it requires holding two distinct stack layers in mind at once → V4 Pro

### B. Architectural Refactoring
The task impacts more than 3 files OR touches core schema definitions:
- Any change to `manifest.json` schema or API route contracts
- More than 3 files modified in a single PR
- Changes to auth, cron, or agent configuration
- **Rule:** If scope > 3 files OR contract-level changes → V4 Pro

### C. Recursive Debugging
A task has failed a Mitty "Build Shield" check more than twice:
- Same task returned with build errors 2+ times
- Iterative debugging loop detected by repeat failures
- **Rule:** 2 failures → V4 Pro takes over immediately to break the loop

### D. Iteration Tax
If the task is projected to require more than 3 back-and-forth turns with a mid-tier model to reach Definition of Done:
- Estimate turns at triage time, not after
- Mid-tier models are optimized for linear, low-iteration tasks
- **Rule:** Projected turns > 3 → V4 Pro one-shot execution

---

## Titty (MiniMax) Preservation

Titty is the **primary worker for Linear Tasks**. These stay with L2:

| Task Type | Examples |
|-----------|----------|
| Bulk documentation | Generating wiki entries from a template |
| Repetitive CSS styling | Component variants, consistent theming |
| Standard Python boilerplate | CRUD scripts, SCD Type 2 merge with defined schema |
| Data transformation | Batch ETL with well-defined dbt models |
| Bulk API integration | Standardized PATCH/GET routes |

**Titty is NOT for:**
- Novel architectural decisions
- Tasks requiring novel multi-file coordination
- Anything already failed twice at L2

---

## Reasoning Depth vs Context-Only

| Old (Context-Only) | New (Reasoning Depth) |
|-------------------|------------------------|
| Route based on input size | Route based on reasoning steps required |
| Large context → escalate to V4 Pro | Novel cross-domain → V4 Pro even with small context |
| "Flash can handle most things" | "Flash triages, then routes correctly" |
| No tracking of iteration loops | 2 build failures → auto-escalate to V4 Pro |

---

## Logging — Escalation Tracking

In the `/alerts` hub, every escalation event is logged as:

```
[TIMESTAMP] [GATEWAY] [ESCALATION: COMPLEXITY] — [REASON] — [TASK SUMMARY]
```

**Reason codes:**
- `[ESCALATION: COMPLEXITY]` — Cross-domain or architectural (bypassed Titty)
- `[ESCALATION: ITERATION]` — >3 turns projected (one-shot to V4 Pro)
- `[ESCALATION: DEBUG]` — 2+ build failures (recursive debugging loop)
- `[ESCALATION: RAM]` — Bitty RAM threshold hit (local queue)

**Tracking goal:** Measure % of tasks escalated vs. L2 one-shot completions. Target: >60% resolved at L2.

---

## RAM-Gated Escalation (unchanged)

Before any local inference (Bitty/Ollama):
1. Check `memory_check()` in bitty_core.py
2. Threshold: 70% system RAM
3. If blocked → queue task, do not bypass

---

## Files Modified

- `~/.openclaw/openclaw.json` — DeepSeek provider added, V4 Flash set as primary
- `AGENTS.md` — Gateway Router section + v3.3
- `wiki/decisions/Gateway_Router_Implementation.md` — v2.0 with Reasoning Depth rules

---

## Cross-Links
→ [../index.md](../index.md) — Wiki central  
→ [./Crew_Roster_v3.md](./crew-roster-v3.md) — Agent definitions  
→ [./Correction_Ledger.md](./correction-ledger.md) — What NOT to use (Python/Bash only)