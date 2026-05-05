# Crew Roster v3 — 5-Agent Crew Established

**Date:** 2026-05-03  
**Updated:** 2026-05-03 (v3.3 — model tier refresh)  
**Agents:** Kitty [K], Witty [W], Mitty [M], Bitty [B], Titty [T]  
**Model Tier:** Flagship (DeepSeek V4 Pro) → Mid (DeepSeek V4 Flash, MiniMax M2.7) → Lightweight (Gemini Flash, Llama 3.2 3B)  
**Trigger:** Mathew formalizes crew structure with Hybrid Pro-Mini model strategy

---

## Context

Mathew formalized a 5-agent crew with clear role delineation, tier-based model selection, and a core principle: **Obsessive Documentation & Wiki-linking**.

**Updated v3.3:** Gateway Router strategy active — DeepSeek V4 Flash (L1) → MiniMax M2.7 Titty (L2) → DeepSeek V4 Pro Kitty (L3). Reasoning Depth > Context-Only escalation. Titty preserved for Linear Tasks.

---

## Decisions Made

1. **Kitty → Flagship (DeepSeek V4 Pro):** Chief of Staff, lead decision maker, Logic & Budget Check
2. **Witty → Mid (DeepSeek V4 Flash):** Memory Architect, owns `/wiki`, drives documentation culture
3. **Titty → Mid (MiniMax M2.7):** Technical Lead, Data Engineering & ETL (Python + PostgreSQL + dbt + Airflow + MinIO)
4. **Mitty → Lightweight (Gemini Flash):** Security & Audit, daily 11 PM Eastern
5. **Bitty → Local (Llama 3.2 3B):** Routine & Local Privacy, no data leaves machine, RAM Watchdog

## Core Principle

**Obsessive Documentation & Wiki-linking:** If it's not documented, it didn't happen. Every significant decision, pattern, and lesson learned goes in `/wiki` with cross-links.

---

## Escalation Ladder (v2.0)

| Level | Agent | Model | Routing Trigger |
|-------|-------|-------|----------------|
| L1 Routine | Gateway | DeepSeek V4 Flash | Simple lookups, status checks |
| L2 Technical | Titty | MiniMax M2.7 | Linear ETL tasks, bulk docs, standard Python boilerplate |
| L3 Strategic | Kitty | DeepSeek V4 Pro | Cross-domain logic, >3 files, 2+ build failures, >3 iteration turns |

**Triage Bypass → Kitty immediately:** Cross-Domain Logic, Architectural Refactoring (>3 files), Recursive Debugging (2+ failures), Iteration Tax (>3 turns projected)

---

## Related
- [AGENTS.md](../../AGENTS.md) — Crew hierarchy & conventions (v3.3)
- [SOUL.md](../../SOUL.md) — Kitty's personality matrix
- [Gateway_Router_Implementation.md](./Gateway_Router_Implementation.md) — v2.0 Reasoning Depth escalation
- [../index.md](../index.md) — Wiki central