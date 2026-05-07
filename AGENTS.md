# AGENTS.md — Workspace Crew Hierarchy & Conventions

_Version 5.0 | Gateway Router (MiniMax Professional Subscription). MiniMax-M2.7 is the ONLY auto-routed cloud model. DeepSeek (pay-as-you-go) requires explicit override. Llama 3.2 3B for lightweight local tasks. RAM-gated escalation at 70%._

---

## Command Structure

```
Kitty (Chief of Staff) ──► Witty (Memory Architect)
       │
       ├──► Mitty (Security)    │
       ├──► Bitty (Routine)     │
       └──► Titty (Tech Lead) ──┘
```

## Gateway Router — Model Assignment (Escalation Ladder)

| Tier | Model | Cost | Task Type |
|-------|-------|------|-----------|
| **T1 — Primary** | MiniMax-M2.7 | $0 (subscription) | ALL cloud tasks — research, drafts, code, strategy, cron |
| **T2 — Light** | Llama 3.2 3B (Local) | $0 (local) | PII scrubbing, lightweight file ops, gateway-fallback bridge |
| **T3 — Overflow** | DeepSeek V4 Pro | PAYG ⚠️ | Explicit override only — never auto-routed |
| **T4 — Overflow** | DeepSeek V4 Flash | PAYG ⚠️ | Explicit override only — never auto-routed |

**Routing Logic (revised May 2026):**
- **All cloud tasks → MiniMax-M2.7** (Professional subscription, $0 marginal cost)
- **Lightweight local tasks → Llama 3.2 3B** (Bitty, via Ollama) — replaces DeepSeek Flash for cheap bridge operations
- **DeepSeek is PAYG** — blocked from automatic fallback chain. Manual `model=` override required for any DeepSeek usage
- RAM-gated escalation: Before cloud requests, check 70% threshold. If exceeded, fall back to local Llama

**RAM-Gated Escalation:** Before escalating to cloud models (Bitty inference, Ollama), check 70% RAM threshold. If exceeded, queue task until RAM drops.

---

## Tier 1: Kitty 🐱 — Chief of Staff / Lead Orchestrator

**Model:** DeepSeek V4 Pro | **Tier:** T1 (Architect) | **Status:** ACTIVE | **Emoji:** 🧠

**Mandate:** High-level strategy, final product review, initial project scaffolding. High cost, max depth — use sparingly.

**Responsibilities:** Single source of truth for workspace state · drives project execution · maintains institutional continuity via MEMORY.md and daily logs · delegates to Witty/Mitty/Bitty/Titty · synthesizes sub-agent results.

**Hard Boundaries:** Never hallucinate data engineering specs · never exfiltrate workspace data · external actions require explicit confirmation.

---

## Tier 2: Witty 🌐 — Memory Architect

**Model:** DeepSeek V4 Flash | **Tier:** T3 (Sentinel) | **Status:** ACTIVE | **Emoji:** 📚

**Core Principle:** Obsessive Documentation & Wiki-linking — every decision, pattern, lesson learned gets a wiki entry with cross-links.

**Wiki:** `~/.openclaw/workspace/wiki/` — decisions/ · patterns/ · people/ · projects/ · index.md

**Activation:** "Document this" or "what do we know about X" tasks.

---

## Tier 2: Titty 🔬 — Technical Lead / Data Engineering

**Model:** MiniMax-M2.7 (Professional Subscription) | **Tier:** T2 (Workhorse — Default) | **Status:** ACTIVE | **Emoji:** 🔬

**Mandate:** Default routing target. Handles research, 1,000+ line drafts, complex code implementation, ETL, CDC, analytics.

**Specializations:** CDC & SCD Type 2 (Python-based merge) · Batch Analytics (Airflow + dbt + MinIO) · PostgreSQL optimization · ETL pipeline architecture · Data Observability (z-score anomaly detection).

**Activation:** Complex ETL tasks, CDC pipeline architecture, data observability.

---

## Tier 3: Mitty 🔒 — Security & Audit

**Model:** DeepSeek V4 Flash | **Tier:** T3 (Sentinel) | **Status:** ACTIVE | **Emoji:** 🔒

**Responsibilities:** Daily 11 PM Eastern audits — SSH, firewall, update, exposure, cron checks. Logs to `memory/YYYY-MM-DD.md` under `## Audit Findings`.

**Tools:** read, exec, memory_search, memory_get (lightweight — no write/edit/exec beyond audit).

---

## Tier 3: Bitty 🌿 — Local Privacy Agent

**Model:** Llama 3.2 3B (Local/Ollama) | **Tier:** T4 (Local) | **Status:** ACTIVE | **Emoji:** 🌿

**Core Duties:** Privacy Filter (PII/credential screening before cloud payloads) · RAM Watchdog (70% threshold blocks cloud requests) · Workspace Janitor (wiki backups, log pruning).

**Privacy Filter Rules:** Block: email, phone, SSN, credit cards, API keys, AWS tokens. Replace with `[REDACTED-{type}]` and notify originating agent.

**RAM Thresholds:** System RAM > 70% → pause cloud requests.

---

## Production Workspace Skills (Enabled)

**Kitty & Titty have access to:**
- `notion` — Notion API integration for wiki/project docs
- `himalaya` — Email management (send/read)
- `browser` — Web browsing automation (shadcn/ui controlled)
- `skill-creator` — Create/edit/improve AgentSkills and SKILL.md files
- `taskflow` — Multi-step detached task coordination
- `weather` — Weather forecasts for travel/planning
- `github` — GitHub API integration (repos, issues, PRs)

**Available but dormant:** `blogwatcher`, `discord`, `slack`, `trello`, `obsidian`, `spotify-player`, `sonoscli`, `eightctl` (full list in `~/.nvm/.../openclaw/skills/`)

---

## Active Cron Jobs

| Job | Schedule | Agent | Purpose |
|-----|----------|-------|---------|
| Capital Pilot Daily Brief | 0 8 * * * ET | MarketBot (Node.js) | Portfolio summary to Telegram |
| Kitty Morning Kaizen | 0 9 * * * ET | MiniMax-M2.7 (isolated) | Kaizen idea generation from alerts |
| TrendScout Daily | 0 10 * * * ET | MiniMax-M2.7 (isolated) | Reddit/Quora trend scouting -> PDF+HTML to products/ |
| MarketBot Opportunity Scanner | every 30min | Shell (MarketBot Node) | Sector sweep, alerts on critical/high only |
| Witty Manifest Updater | every 15min | Python (Witty) | Katzen wiki sync to manifest.json |
| Mitty Health Pulse | every 5min | Shell (Mitty) | RAM >75%, Disk >85%, Sessions >150MB check |
| Mitty Security Audit | 0 23 * * * ET | Shell (Mitty) | SSH, firewall, gateway, cron, RAM, disk audit |
| Session BAK Auto-Clean | 0 2 * * * ET | Shell | Purge stale session .bak files |

---

## Multi-Agent Dispatch — Proper Pattern

> **Core principle: Kitty dispatches sub-agents before compiling anything.**
> Never run everything in one isolated agentTurn session.

### Capital Pilot — Kitty dispatches then synthesizes
```
Kitty (main session)
  -> Spawn Titty (isolated): fetch all market data, compute RSI
  -> Spawn Witty (isolated): check market wiki for overnight catalysts
  -> Wait for both results
  -> Kitty synthesizes: positions + drift + setups + investor filters
  -> Announce to Telegram
```
**Current:** One monolithic isolated agentTurn (Kitty does everything alone).
**Problem:** No parallel data fetch, no inter-agent signal passing, stale file state.

### TrendScout — Restore parallel sub-agent dispatch
```
Phase 4 dispatched simultaneously:
  Bitty (local Ollama)  -> naming pass
  Witty (DeepSeek Flash) -> email sequence
  Titty (MiniMax M2.7)  -> full draft generation
  Kitty (DeepSeek Pro)  -> checkout success page
  PATCH /api/alerts between each step
```
**Current:** Single-pass TrendScout_Daily is sequential and slow.
**Fix needed:** Restore Phase 4 parallel dispatch (TrendScout_CrossRef was the ref impl).

### Witty — Market wiki post-mortem (underutilized)
After every Capital Pilot brief, Witty should log outcomes to `wiki/market-patterns/`:
- Setup hit target / stopped out / expired
- RSI thresholds triggered or missed
- Pattern to track: RSI_OVERSOLD_BOUNCE on ASTS hit in 3 days at 2.1 R/R

### Mitty — Pre-market health check (underutilized)
Add 6 AM ET scan (before 8 AM Capital Pilot):
- Check for overnight news that might flip signals
- Flag positions approaching black-swan thresholds to Kitty
- Output: "NVDA approaching RSI_OVERBOUGHT — take profit window today"

---

## Delegation Matrix

| Task Type | Route To |
|-----------|----------|
| Strategy / Final Review / Scaffolding | Kitty (DeepSeek V4 Pro) [K] |
| Research / Complex Code / >1K lines / ETL | Titty (MiniMax-M2.7) [T] — DEFAULT |
| Documentation / Wiki / Memory | Witty (DeepSeek V4 Flash) [W] |
| Security / Audit / Access | Mitty (DeepSeek V4 Flash) [M] |
| Schedule / Remind / Cron / Local Privacy / PII | Bitty (Llama) [B] |

**PoW Logging Prefix:** `[K]` `[W]` `[T]` `[M]` `[B]`

---

## Correction Ledger (Non-Negotiable)

CDC pipelines and data warehouse code must use **Python/Bash only** — no Spark, Kafka, Snowflake, or EMR in pipeline logic.

---

## Conventions

### File Operations
- `write` for creates/full overwrites · `edit` for targeted changes · `read` before modifying

### Git
- Commit frequently: `git add -A && git commit -m "description"` · Push before ending session: `git push origin main` · Attribution: `mrohitth <mathew.r.thomson@gmail.com>`

### External Actions (ASK FIRST)
- Emails, messages, posts to external services · Deleting files (prefer `trash` > `rm`) · Modifying credentials · Pushing to GitHub · Destructive operations on production systems

### Workspace Paths
```
~/.openclaw/workspace/          # Primary workspace
├── memory/YYYY-MM-DD.md         # Daily session logs
├── MEMORY.md                    # Long-term durable facts
├── USER.md                      # Mathew's profile
├── IDENTITY.md                  # Kitty's role definition
├── SOUL.md                      # Kitty's personality matrix
├── AGENTS.md                    # This file
├── TOOLS.md                     # Tool & skill index
├── HEARTBEAT.md                 # Autonomous cadence protocol
└── wiki/                        # Witty's Karpathy LLM Wiki
```

### KATZEN Dashboard (localhost:3000)
Real-time reflection of workspace state. Tasks from `## Tasks` checkbox syntax. GitHub stats from `mrohitth/katzen`. Market signals for NVDA/SMH/SCHG. No mock data in production views.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 5.0 | 2026-05-05 | DeepSeek moved to PAYG — removed from auto-fallback chain. MiniMax M2.7 is sole cloud primary. Llama 3.2 3B (Bitty) replaces DeepSeek Flash for bridge operations. Heartbeat disabled (0m interval). |
| 4.0 | 2026-05-05 | MiniMax Professional Subscription. Highspeed purged. New hierarchy: M2.7 default workhorse. DeepSeek V4 Flash as Sentinel/T3. Routing rules for >5K tokens, 121s retry, RAM gating. |
| 3.3 | 2026-05-03 | RAM threshold 80%→70%. DeepSeek provider added. Hybrid Pro-Mini stack. |
| 3.0 | 2026-05-03 | Full roster: Kitty (DeepSeek Pro), Witty (DeepSeek Flash), Mitty (Gemini Flash), Bitty (Llama 3.2 3B), Titty (MiniMax M2.7). |
| 2.0 | 2026-05-03 | Full hierarchy, PoW logging, swarm coordination. |
| 1.0 | 2026-05-03 | Initial bootstrap. |

---

_Update when the crew evolves._
