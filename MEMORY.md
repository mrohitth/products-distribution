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
| **T1 — Primary** | Kitty 🐱 / Titty 🔬 | MiniMax-M2.7 | $0 (subscription) | ALL cloud tasks — research, drafts, code, strategy, cron |
| **T2 — Local** | Bitty 🌿 | Llama 3.2 3B (Ollama) | $0 (local) | PII scrubbing, lightweight ops, gateway-fallback bridge |
| **T3 — Overflow** | Witty 🌐 / Mitty 🔒 | DeepSeek V4 Pro | PAYG ⚠️ | Explicit override only — never auto-routed |
| **T4 — Overflow** | — | DeepSeek V4 Flash | PAYG ⚠️ | Explicit override only — never auto-routed |

### Routing Rules
- **All cloud tasks → MiniMax-M2.7** (Professional subscription, $0 marginal cost)
- **Lightweight local tasks → Llama 3.2 3B** (Bitty, via Ollama) — replaces DeepSeek Flash for bridge operations
- **DeepSeek is PAYG** — removed from automatic fallback chain. Manual `model=` override required for any DeepSeek usage
- **RAM >70% →** Pause cloud requests; fall back to local Llama

### Command Structure
```
Kitty (Chief of Staff) ──► Witty (Memory Architect)
       ├──► Mitty (Security & Audit)
       ├──► Bitty (Routine & Local)
       └──► Titty (Technical Lead / Data Engineering)
```

### Kitty 🐱 — Chief of Staff
**Model:** DeepSeek V4 Pro · **Status:** ACTIVE · **Tools:** All tools · **Tier:** T1

### Titty 🔬 — Technical Lead / Data Engineering
**Model:** MiniMax-M2.7 (Professional Subscription) · **Status:** ACTIVE · **Tools:** read, write, exec, web_search, web_fetch, memory_search, memory_get · **Tier:** T2 (Default Workhorse)

### Witty 🌐 — Memory Architect
**Model:** DeepSeek V4 Flash · **Status:** ACTIVE · **Tools:** read, write, web_search, web_fetch, memory_search, memory_get · **Tier:** T3

### Mitty 🔒 — Security & Audit
**Model:** DeepSeek V4 Flash · **Status:** ACTIVE · **Tools:** read, exec, memory_search, memory_get · Daily 11 PM Eastern audits · **Tier:** T3

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

### MiniMax Professional Subscription — Activated
- **Date:** 2026-05-05 · **Model:** MiniMax-M2.7 (reasoning, 200K context) · **Role:** T2 Workhorse
- **Highspeed removed** — no longer in subscription; all traces purged from config and docs
- **New primary model:** `minimax/MiniMax-M2.7` with reasoning enabled
- **New fallback chain:** MiniMax-M2.7 → DeepSeek V4 Pro → DeepSeek V4 Flash

### Bitty Local Engine — Setup Complete
- **Binary:** `~/.local/bin/ollama` v0.22.1 · **Model:** `llama3.2:3b` (Q4_K_M, ~2GB)  
- **Model path:** `/run/media/mathew/OS/ollama/models/` · **Privacy Engine:** `bitty_core.py`
- **RAM Threshold:** 70% · **API:** `http://127.0.0.1:11434`
- **GPU note:** GTX 1650 Ti 4GB VRAM CC 7.5 — GPU acceleration inactive (CPU only, /tmp disk quota issue)

### Mitty Security Audit — Enabled
- **Cron ID:** `ab1be4b3-4dc0-46fd-b185-058fc4847ec6` · **Schedule:** `0 23 * * *` (11 PM Eastern)
- **Delivery:** announce → `telegram:5607383477` · **Payload:** Full SSH/firewall/gateway/cron/ram/filesystem audit

---

## 🔒 Correction Ledger (Immutable)

CDC pipelines and warehouse code must use **Python/Bash only**. Forbidden: Spark, Kafka, Snowflake, EMR, PySpark.

## 📚 Model Specifications

> **→ SOURCE OF TRUTH: [MODEL_SPECS.md](MODEL_SPECS.md)**
> Complete operating parameters for MiniMax M2.7 (default), DeepSeek V4 Pro, and DeepSeek V4 Flash.
> Includes context windows, pricing, caching strategies, thinking modes, and routing decision matrix.

## 🏭 Digital Product Workflow — 4-Stage Pipeline

> **All stages use MiniMax M2.7 (Professional Subscription) — $0 marginal cost.**
> DeepSeek reserved for overflow/fallback only.

### STAGE 1: The Scout 🎯
| Field | Value |
|-------|-------|
| **Cron** | TrendScout Daily — 10:00 AM ET |
| **Model** | MiniMax M2.7 |
| **Action** | Scout Reddit/Quora for 3 emotional pain points |
| **Output** | `wiki/trends/YYYY-MM-DD.md` with Frustration Scores (1-10) |
| **Trigger** | If score > 8/10 → flag [HIGH CONVICTION] → advance to Stage 2 |

### STAGE 2: The Architect 🏗️
| Field | Value |
|-------|-------|
| **Trigger** | Any trend scores > 8/10 in Stage 1 |
| **Model** | MiniMax M2.7 |
| **Action** | Generate Product Skeleton from HIGH CONVICTION trend |
| **Focus** | Human Touch elements — personal anecdotes, empathetic framing, actionable steps |
| **Output** | `products/skeletons/[SLUG]_SKELETON.md` |
| **Tone** | Matte-finish / smart-casual — never AI-slop, never hypey |

### STAGE 3: The Draft 📝
| Field | Value |
|-------|-------|
| **Trigger** | Skeleton approved (by Mathew or auto if score = 10/10) |
| **Model** | MiniMax M2.7 |
| **Action** | Expand skeleton into full first draft |
| **Format** | eBook, Guide, or Tool depending on product angle |
| **Constraint** | 100% matte-finish/smart-casual voice. Cohesive with 2026 Vision Board. |
| **Output** | `products/drafts/[SLUG]_DRAFT.md` |

### STAGE 4: Capital Pilot Integration 📊
| Field | Value |
|-------|-------|
| **Trigger** | Draft complete |
| **Model** | MiniMax M2.7 or shell script |
| **Action** | Cross-reference product niche with semiconductor/AI portfolio |
| **Goal** | Identify automation angle or Market Intel upsell opportunity |
| **Output** | Appended to draft as `## Market Intel Angle` section |

### STAGE 5: Production 📦
| Field | Value |
|-------|-------|
| **Trigger** | Draft complete |
| **Action** | Pandoc conversion: Markdown → styled PDF |
| **Design** | Smart-Casual: Inter/Charter fonts, Deep Navy accents, callout boxes |
| **Output** | `output/final_products/[SLUG]_V1.pdf` |
| **Note** | Requires pandoc + texlive-xelatex |

### STAGE 6: Distribution Flywheel 🚀
| Field | Value |
|-------|-------|
| **Trigger** | Draft complete (auto from pipeline) |
| **Action** | Reddit posts (active) · Pinterest pins (planned) · TikTok scripts (planned) · LinkedIn (not planned) · email lead magnet + sequence (active) |
| **Output** | `distro/content/{slug}/` + `distro/email/{slug}_*` |
| **Delivery** | Background subprocess — non-blocking (session stays responsive) |
| **Channel gating** | Reads `distro/manifest/state.json` channels.enabled — skips disabled platforms |
| **Email funnel** | Welcome sequence → Notion template upsell ($17) |
| **Current active** | Reddit + Email list |
| **Planned (no account yet)** | Pinterest, TikTok |
| **Not planned** | LinkedIn |

### Workflow State Machine
```
[10:00 AM] Scout → Score > 8? → YES → Architect → Skeleton
                                              → Draft → Production (PDF)
                                              → Telegram (document + announcement)
                     → NO  → Log & wait for tomorrow
```

### 🤖 Autonomous Mode — Primary Operational Flow

**Effective 2026-05-05.** The pipeline operates autonomously via a single chained cron job.

| Rule | Detail |
|------|--------|
| **Cron** | `1e85c944` — TrendScout_Daily (10:00 AM ET, isolated agentTurn) |
| **Model** | MiniMax M2.7 — single pass, all 3 stages |
| **Trigger** | Cron fires → agent scouts + scores → if HIGH CONVICTION found → immediately generates skeleton + draft |
| **Output** | Trends file → Skeleton(s) → Draft → Telegram announcement (one message, full chain) |
| **BAK purge** | Pipeline includes `.bak-*` cleanup at end of run; BAK Auto-Clean cron (`8f38b6fc`) runs daily at 2 AM ET |
| **Silence rule** | If no HIGH CONVICTION trends, only the trends summary is announced — no skeleton/draft |
| **Manual override** | Run `python3 scripts/pipeline_manager.py` or `bash scripts/pipeline_chain.sh` |

**Telegram ping format (autonomous completion):**
```
🚨 Pipeline Complete — [DATE]
[HIGH CONVICTION] Trend Name (X/10)
Skeleton: products/skeletons/[SLUG]_SKELETON.md
Draft: products/drafts/[SLUG]_V1.md
Human Infrastructure: [1-sentence scale thesis]
```

### Current Pipeline Status
| Stage | Status | Latest Output |
|-------|--------|---------------|
| Stage 1 | ✅ Active (daily cron) | `wiki/trends/2026-05-05.md` |
| Stage 2 | ✅ Done (manual) | `single_parent_burnout_SKELETON.md` |
| Stage 3 | ✅ Done (manual) | `off_switch_V1.md` |
| Stage 4 | ✅ Done | `products/assets/` — Lemon Squeezy copy, insight post, order bump |
| Stage 5 | ✅ Active | `scripts/pipeline_manager.py` + `products/assets/pdf_style.css` — WeasyPrint PDF with professional styling |
| Stage 5b | ✅ Active | `stage5_production_docx()` — pandoc HTML→DOCX + `_docx_apply_styling()` for visual parity with PDF |

### Stage 5 — PDF Production Standards

**CSS:** `products/assets/pdf_style.css` — Inter font, navy palette, TOC, page breaks, callout boxes

**Strip from all PDFs before rendering:**
- `# PRODUCT METADATA` block (H1 + table)
- `# ABOUT THE AUTHOR` block (H1 + paragraphs)
- `## What's Coming in V2` / sections with "Coming in V2" placeholders
- `*Awaiting review*` / `*Draft V1 generated*` footer metadata

**Page breaks:** Only before `## Part N:` major sections — not every H2 subsection

**H1 normalization:** H1 Part headings (ragdoll-style) → H2 so page breaks target correctly

**Key Insight styling:** `### Key Insight:` / `### Key Takeaway:` → `.callout-insight` gradient div

**Blockquotes:** Opening `*"..."*` paragraphs → `<blockquote class="script-quote">` with left border

### Stage 5b — DOCX Production (Visual Parity with PDF)

**Pipeline:**
1. `_preprocess_for_docx()` — same structural normalization as PDF (H1→H2, callout divs, blockquote conversion), strips page-break divs
2. `markdown.Markdown()` → HTML body
3. `pandoc HTML→DOCX` with `products/assets/reference.docx` for base styles (Charter body, Inter headings)
4. `_docx_apply_styling()` — XML-level post-processing (python-docx + lxml):
   - **CoverTitle:** first non-empty `Heading 1` paragraph → `CoverTitle` style + 3pt bottom border (`w:pBdr/w:bottom`)
   - **PartHeading:** paragraphs matching `Part N:` → `PartHeading` style + dark blue fill (`w:shd`) + white bold runs
   - **InsightBox:** paragraphs whose first bold run starts with `Key Takeaway` or `Key Insight` → navy fill + white text
   - **QuoteBox:** blockquote paragraphs → light grey fill

**reference.docx styles:** CoverTitle (Inter 28pt), PartHeading (Inter 16pt white on navy), InsightBox/TakeawayBox (Inter, navy fill), QuoteBox (Calibri italic, grey fill)

**Key insight:** pandoc strips HTML classes/IDs/comments during HTML parsing — visual styling cannot be CSS-driven. All formatting (borders, shading, colors) must be applied via XML manipulation in python-docx post-processing, identified by paragraph style + content patterns.
| Stage 6 | ✅ Active | `distro/flywheel.py` — Distribution engine auto-triggered after draft |
| Phase 1 (GitHub) | ✅ Added | `scripts/pipeline_manager.py::sync_to_github()` + `create_github_release()` |
| Phase 2 (Storefront) | ✅ Done | `products/storefront_manifest.md` + `products/email_sequence.md` |
| Phase 3 (MarketBot) | ✅ Added | `scripts/marketbot_feedback.py` — webhook listener + Scout re-weighting |
| Phase 4 (Pre-Flight) | ✅ Done | `scripts/preflight_check.sh` — green light diagnostic |

### Pipeline Deduplication Guards (2026-05-06)
**Problem:** Pipeline was generating duplicate skeletons and drafts for the same topic, and treating rewrites as new products.

**Fixes applied:**
- `check_existing_skeleton(topic_title, skeletons_dir)` — fuzzy slug match at Stage 2, prevents duplicate skeleton generation
- `check_existing_draft(slug, drafts_dir)` — base-slug dedup at Stage 3, prevents duplicate draft generation
- `normalize_to_canonical()` — archives any existing `_V1` before writing a new one (ensures one canonical version only)
- `--force-skeleton` / `--force-draft` flags to override when intentional rewrite is needed
- Naming convention enforced: `*_V1.md` = canonical only. `_FINAL`, `_v2`, `_V2` suffixes prohibited
- Archived duplicates live in `products/archive/`

### Deployment Infrastructure
| Component | Path | Status |
|-----------|------|--------|
| Pipeline Manager | `scripts/pipeline_manager.py` | Stages 2-5 + Stage 6 auto-register + distro launch |
| Distribution Flywheel | `distro/flywheel.py` | Reddit/Pinterest/TikTok/LinkedIn/email + Notion upsell |
| GitHub Release Tagger | `scripts/pipeline_manager.py::create_github_release()` | Needs `gh` auth |
| Webhook Listener | `scripts/marketbot_feedback.py` | Ready to run |
| Sales DB | `output/sales_performance.db` | Auto-created on first sale |
| Storefront Manifest | `products/storefront_manifest.md` | Lemon Squeezy config reference |
| Email Sequence | `products/email_sequence.md` | 3-email post-purchase sequence |
| Pre-Flight Script | `scripts/preflight_check.sh` | Run before any production push |

---

_Last updated: 2026-05-06T01:24:00Z_

### MarketBot v2 — Live ✅ (2026-05-05T19:15:00Z)
- **Portfolio coverage:** All 10 holdings (VTI, NVDA, VOO, QQQ, SMH, SCHG, VXUS, SCHD, SPYD, ASTS) — expanded from 3
- **Macro tickers:** SPY, QQQ, DXY, TLT, GLD — market context fetch
- **Sector sweep:** 20 semi/tech stocks for Profit Maximizer scanner
- **Data source:** Yahoo Finance via `yahoo-finance2` — no API key needed (replaced Alpha Vantage)
- **Capital Pilot cron fixed:** Cron `3276d08a` converted from `systemEvent` → `agentTurn` with `delivery.mode: "announce"` → Telegram (was broken: stdout to execution log, never to Telegram)
- **Live test:** 10 portfolio + 4 macro + 20 sector tickers fetched; 9 rebalance recommendations generated
- **Repo:** `mrohitth/MarketBot` (c71cd94 pushed)
