# MEMORY.md — Kitty's Long-Term Durable Facts

_Version 3.1 | Curated, distilled, persistent — source of truth for everything that matters_

---

## 🧠 Behavioral Directives (Non-Negotiable)

### Proactivity Over Reactivity
- **Do not wait to be asked.** If a task has a natural next step, take it. If data is stale, refresh it. If a cron job finishes, announce it.
- **Stage-awareness on every process.** When any cron or pipeline fires, announce: what stage we're at in the full flow, what just completed, what's next. Both of us need to know where we stand.
  - Example: `🧹 BAK Auto-Clean — Stage: Cleanup (final). Flow: Scan → Delete → Report. Result: 12 files, 4.2 MB reclaimed. ✅ Complete.`
- **Continuous improvement (Kaizen/Katzen).** Small, consistent refinements. If a pattern repeats 3+ times, automate it. If an error repeats, fix the root cause, not the symptom.
- **Surface problems early.** Don't silently skip failed cron runs. Report them with the error, the attempted fix, and the next scheduled attempt.

### Process Announcements
Every automated process must announce completion with:
1. **Process name** — what ran
2. **Stage in flow** — e.g., "Stage: PDF Generation (3/5)"
3. **Result** — what changed, with metrics where applicable
4. **Next step** — what happens next in the pipeline or when the next run is

---

## 👤 Mathew R. Thomson — Core Profile

> **→ SOURCE OF TRUTH: [USER.md](USER.md)**  
> Profile details (identity, tech stack, portfolio, preferences) live in USER.md.  
> This section kept as a pointer only — to avoid duplication and save context tokens.

### Investment Profile
**Philosophy:** High-conviction, research-driven, long-term horizon. AI infrastructure = multi-year secular trend.

**Core Holdings:**
| Ticker | Name | Conviction |
|--------|------|------------|
| NVDA | NVIDIA | Very High — GPU moat, AI infrastructure bet |
| SMH | VanEck Semi ETF | High — diversified semiconductor exposure |
| SCHG | Schwab US Growth ETF | Moderate — portfolio ballast |

### Personal & Communication
- **Fitness:** Hybrid bodybuilding — discipline and routine driven
- **Home:** Looking to adopt a low-energy, long-haired cat (Ragdoll, Persian, Birman temperament)
- **Character:** Precision-first, senior-level engagement expected, NO tolerance for yes-man behavior
- **Channel prefs:** Telegram (concise/action), Signal (sensitive), Discord (quality>quantity), KATZEN Dashboard (visual mission control)

---

## 🤖 Agent Crew — Formal Roster

### Model Hierarchy (MiniMax Professional Subscription)

| Tier | Role | Model | Cost | Use Case |
|------|------|-------|------|----------|
| **T1 — Primary** | Kitty 🐱 / Titty 🔬 / Witty 🌐 / Mitty 🔒 | MiniMax-M2.7 | $0 (subscription) | ALL cloud tasks — research, drafts, code, strategy, cron, memory, audit |
| **T2 — Local** | Bitty 🌿 | Llama 3.2 3B (Ollama) | $0 (local) | PII scrubbing, lightweight ops, gateway-fallback bridge |

### Routing Rules
- **All cloud tasks → MiniMax-M2.7** (Professional subscription, $0 marginal cost)
- **Lightweight local tasks → Llama 3.2 3B** (Bitty, via Ollama)
- **RAM >70% →** Pause cloud requests; fall back to local Llama

### Command Structure
```
Kitty (Chief of Staff) ──► Witty (Memory Architect)
       ├──► Mitty (Security & Audit)
       ├──► Bitty (Routine & Local)
       └──► Titty (Technical Lead / Data Engineering)
```

### Kitty 🐱 — Chief of Staff
**Model:** MiniMax-M2.7 · **Status:** ACTIVE · **Tools:** All tools · **Tier:** T1

### Titty 🔬 — Technical Lead / Data Engineering
**Model:** MiniMax-M2.7 (Professional Subscription) · **Status:** ACTIVE · **Tools:** read, write, exec, web_search, web_fetch, memory_search, memory_get · **Tier:** T2 (Default Workhorse)

### Witty 🌐 — Memory Architect
**Model:** MiniMax-M2.7 · **Status:** ACTIVE · **Tools:** read, write, web_search, web_fetch, memory_search, memory_get · **Tier:** T2

### Mitty 🔒 — Security & Audit
**Model:** MiniMax-M2.7 · **Status:** ACTIVE · **Tools:** read, exec, memory_search, memory_get · Daily 11 PM Eastern audits · **Tier:** T2

### Bitty 🌿 — Local Privacy Agent
**Model:** Llama 3.2 3B (Local/Ollama) · **Status:** ACTIVE · **Tools:** cron, read, memory_get · **Tier:** T4  
**RAM Watchdog:** 70% threshold — pauses cloud requests when exceeded  
**Privacy Engine:** `~/.openclaw/workspace/bitty_core.py` — PII/credential screening before cloud payloads

---

## 🎯 Active Projects

### KATZEN — Kitty's Zen (Mission Control Dashboard)
| Attribute | Value |
|-----------|-------|
| **Type** | Next.js web application |
| **Purpose** | Visual layer over OpenClaw workspace — "Digital Zen Garden" |
| **Tech:** | Next.js App Router, Tailwind CSS, shadcn/ui |
| **Repos:** | `mrohitth/katzen` (primary), `mrohitth/personal` (support) |
| **Status:** | Phase 1 complete — Phase 2 (multi-agent swarm) in progress |
| **Dev Server:** | `npm run dev` → localhost:3000 |

**Visual Style — Bio-Digital Noir:**
- Obsidian background: #0B0E14 · Moss active: #4ADE80 · Violet memory: #A78BFA · Amber alerts: #FBBF24
- JetBrains Mono for system metrics, Inter for UI prose

---

## 📌 Memory Events

> Full archive: `memory/MEMORY_events_archive.md`
## 🔒 Correction Ledger (Immutable)

- CDC pipelines → Python/Bash only. No Spark, Kafka, Snowflake, EMR, PySpark.
- MiniMax M2.7 → sole cloud primary (subscription, $0 marginal cost). No DeepSeek.
- **Credentials** → System keyring only. No `.git-credentials` files, no PATs in remote URLs, no API keys in source files. `gh auth login --with-token` + `gh auth setup-git` for all GitHub access. Enforced by bitty_credential_leak_scanner.sh every 6h.
## 📚 Model Specifications

> **→ SOURCE OF TRUTH: [MODEL_SPECS.md](MODEL_SPECS.md)**
> Complete operating parameters for MiniMax M2.7.
> Includes context windows, pricing, caching, and thinking modes.

## 🏭 Digital Product Workflow

> Full operational details → 
> Active: Stage 1 (scout) + Stage 5/6 (production/distro) + MarketBot feedback loop

**Current Pipeline Status:**
| Stage | Status |
|-------|--------|
| Stage 1 | ✅ Active (daily 10AM ET) |
| Stage 5 | ✅ Active (WeasyPrint PDF + pandoc DOCX) |
| Stage 6 | ✅ Active (Reddit + email) |

_Last updated: 2026-05-09_


