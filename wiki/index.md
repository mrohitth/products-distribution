# Karpathy LLM Wiki — Central Node

_🌐 Owner: Witty | Core principle: Obsessive Documentation & Wiki-linking_

> **If it's not documented, it didn't happen. If it's not linked, it's not findable.**

---

## Quick Navigation

| Category | Index | What You'll Find |
|----------|-------|-----------------|
| **Projects** | [projects/](./projects/index.md) | KATZEN, MarketBot, CDC Platform, Batch Analytics |
| **People** | [people/](./people/index.md) | Mathew's profile, preferences, investment thesis |
| **Decisions** | [decisions/](./decisions/index.md) | Crew roster, portfolio choices, architecture calls |
| **Patterns** | [patterns/](./patterns/index.md) | Engineering patterns, anti-patterns, audit protocols |

---

## Projects (5 entries)

| Project | Owner | Status | Summary |
|---------|-------|--------|---------|
| [batch-analytics-platform.md](./batch-analytics-platform.md) | [T] Titty | Production | Batch ELT — Airflow + dbt + MinIO, handles event stream deduplication |
| [data-observability-platform.md](./data-observability-platform.md) | [T] Titty | Production | Anomaly detection — z-score baselines, schema contracts, CI/CD alerting |
| [MarketBot](./projects/marketbot.md) | [K] Kitty | ✅ Live | Daily Capital Pilot brief via Telegram — budget + portfolio |
| [CDC Platform](./projects/cdc-platform.md) | [T] Titty | Production | End-to-end change data capture with temporal SCD Type 2 |
| [Batch Analytics](./projects/batch-analytics.md) | [T] Titty | Production | High-volume batch processing with distributed compute |

---

## People

| Person | Role | Wiki Entry |
|--------|------|-----------|
| Mathew R. Thomson | User / Stakeholder | [mathew.md](./people/mathew.md) |
| Kitty 🐱 | Chief of Staff | [kitty.md](./people/kitty.md) |
| Witty 🌐 | Memory Architect | [witty.md](./people/witty.md) |

---

## Decisions (Recent)

| Date | Decision | Entry |
|------|----------|-------|
| 2026-05-03 | [5-Agent Crew Roster v3](./decisions/crew-roster-v3.md) | Kitty, Witty, Mitty, Bitty, Titty formalized |
| 2026-05-03 | [Portfolio P/L Card](./decisions/portfolio-pl-card.md) | Redesigned to focus on total P/L, not per-share prices |
| 2026-05-03 | [Heartbeat Hours Format](./decisions/heartbeat-hours-format.md) | Countdown shows hours when > 60 minutes |

---

## Patterns

| Pattern | Summary |
|---------|---------|
| [SCD Type 2 Implementation](./patterns/scd-type2.md) | Slowly Changing Dimensions pattern for temporal data |
| [CDC Pipeline](./patterns/cdc-pipeline.md) | Change Data Capture patterns for warehouse builds |
| [Security Audit Protocol](./patterns/security-audit-protocol.md) | Daily audit checklist for Mitty |

---

## Capabilities (1 entry)

| Capability | Owner | Summary |
|------------|-------|---------|
| [Data Engineering Stack](./Data_Engineering_Stack.md) | [T] Titty | Python + Bash + PostgreSQL + Airflow + dbt + MinIO |

---

---

## 🔗 Wiki Linking Rules (Enforced by Witty)

Every entry MUST include:
1. **At least one cross-link** to a related entry
2. **Category index link** (e.g., `→ [projects/](./projects/index.md)`)
3. **Owner tag** — who created/maintains it

Every task completion MUST trigger:
```
[Witty] Index and Link → update the relevant wiki entry + update category index + cross-link
```

---

## 🏗️ Directory Structure

```
wiki/
├── index.md              ← YOU ARE HERE (central node)
├── projects/
│   ├── index.md          ← Project category index
│   ├── katzen.md         ← KATZEN dashboard
│   ├── marketbot.md      ← MarketBot Capital Pilot
│   ├── cdc-platform.md   ← CDC & Historical Warehouse
│   └── batch-analytics.md← Batch Analytics Platform
├── people/
│   ├── index.md          ← People category index
│   ├── mathew.md         ← Mathew's profile & preferences
│   ├── kitty.md          ← Kitty's role definition
│   └── witty.md          ← Witty's role definition
├── decisions/
│   ├── index.md          ← Decision log index
│   └── crew-roster-v3.md ← Crew roster decision
├── patterns/
│   ├── index.md          ← Patterns category index
│   └── scd-type2.md      ← SCD Type 2 pattern
│   └── cdc-pipeline.md   ← CDC pipeline pattern
│   └── security-audit-protocol.md ← Mitty's audit protocol
└── README.md             ← This file (wiki bootstrap)
```

---

_Last updated: 2026-05-03 by Kitty [K] — Bootstrap complete_  
_Next: [Witty] Index and Link → update all category indexes with cross-links_