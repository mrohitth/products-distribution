# MarketBot - The Capital Pilot

**Owner:** [K] Kitty
**Type:** Node.js Financial Strategist
**Status:** ✅ VERIFIED - Brief delivered to Telegram 2026-05-03
**Delivery:** telegram:5607383477 (via OpenClaw cron announce)
**Schedule:** Daily at 8:00 AM EST (via OpenClaw cron)
**Repos:** `mrohitth/MarketBot`
**Operating Cost:** $0/month (all free tiers)

---

## What It Is

Daily Morning Brief bridging budget + portfolio. Delivers to Telegram, no WhatsApp.

**Tech Stack:** TypeScript, Alpha Vantage (free tier), Gmail/IMAP, Telegram

---

## Key Capabilities

| Capability | Description |
|------------|-------------|
| Budget Pacing | Discover CSV import → spending vs $8,500/month net income |
| Portfolio Drift | Detects deviation from target allocation (NVDA 40%, SMH 30%, SCHG 20%) |
| Profit Maximizer | Semi/tech sector scanner - flags setups |
| Black Swan Rule | 8% loss threshold - requires [CONFIRMED] before alerting |
| Gmail/Fidelity Scan | Extracts trade confirmations from Fidelity emails |
| Telegram Delivery | Direct to telegram:5607383477 via OpenClaw announce |

---

## Portfolio (Real Positions - May 9, 2026)

**Total:** $50,102.63 | **G/L:** +$3,483.82 (+7.47%) | **14 positions (incl. cash)**

| Ticker | Shares | Avg Cost | Current | Mkt Value | G/L | Weight |
|--------|--------|----------|---------|-----------|-----|--------|
| NVDA | 41.853 | $203.59 | $215.20 | $9,006.76 | +5.70% | 18.0% |
| VTI | 19.984 | $322.70 | $362.87 | $7,251.59 | +12.44% | 14.5% |
| QQQ | 8.859 | $615.71 | $711.23 | $6,300.78 | +15.51% | 12.6% |
| VOO | 7.636 | $609.44 | $678.04 | $5,177.51 | +11.25% | 10.3% |
| SCHG | 128.865 | $31.98 | $34.12 | $4,396.87 | +6.69% | 8.8% |
| XLE | 66 | $55.77 | $55.70 | $3,676.20 | -0.13% | 7.3% |
| SMH | 6.241 | $515.58 | $566.54 | $3,535.77 | +9.88% | 7.1% |
| XLV | 22 | $143.68 | $143.49 | $3,156.78 | -0.14% | 6.3% |
| VXUS | 29.704 | $73.16 | $85.43 | $2,537.61 | +16.77% | 5.1% |
| SCHD | 67.156 | $29.78 | $31.62 | $2,123.47 | +6.17% | 4.2% |
| AMGN | 6 | $328.57 | $331.70 | $1,990.20 | +0.95% | 4.0% |
| SPYD | 11.533 | $45.42 | $46.69 | $538.47 | +2.79% | 1.1% |
| ASTS | 1.234 | $80.97 | $75.05 | $92.61 | -7.32% | 0.2% |

**Cash:** SPAXX $4,547.58 (9.1%)

**Key changes since May 3:**
- NVDA: +5.70% - back above avg cost
- SMH: +9.88% - trimmed 8.1→6.241 shares (taking profit)
- VTI/QQQ: trimmed from 34/9.4 to 19.984/8.859
- SCHG: increased 102.4→128.865 shares
- NEW: XLE (energy), XLV (healthcare) - sector rotation
- ASTS: heavily trimmed 8.7→1.234 shares
- Pending: -$4,175.06 (settling trades)

---

## Key Files

| File | Purpose |
|------|---------|
| `src/index.ts` | Main orchestrator |
| `src/lib/brief.ts` | Telegram message formatter |
| `src/lib/budget.ts` | CSV parsing + spend tracking |
| `src/lib/market.ts` | Alpha Vantage + drift calc |
| `src/lib/profitMaximizer.ts` | Sector scanner |
| `src/lib/fidelity.ts` | Gmail/Fidelity email scanner |
| `data/portfolio.json` | Real positions (updated 2026-05-03) |
| `data/portfolio-context.md` | Full baseline from email extraction |
| `OPERATING.md` | Full operating instructions |

---

---

## TrendScout Pipeline v2 (2026-05-10)

**Complete revamp** with JSON handoffs, fact-checking, self-critic pass, and distribution hooks.

### Pipeline Stages
| Stage | Task | Output |
|-------|------|--------|
| 1. Scout | Browse Reddit/Quora, find 3 trends with High Emotion anchor | `wiki/trends/[date].json` (JSON with score_breakdown) |
| 2. Architect | Skeleton + mandatory fact-check per pillar (VERIFIED/UNCERTAIN/PLAUSIBLE) | `products/skeletons/[SLUG]_v[N]_SKELETON.md` |
| 3. Draft | Full production draft, self-critic pass (3 AI-slop markers), no placeholders | `products/drafts/[SLUG]_v[N].md` |
| 4. Distribution Hook | Value-first Reddit comment quoting user's specific problem, no sales pitch | `products/distribution/[SLUG]_v[N]_reddit_hook.md` |
| 5. Production | PDF via WeasyPrint + GitHub sync to `final_products/` | `output/final_products/[SLUG].pdf` |
| 6. Announce | Telegram delivery with file paths | Telegram message |

### Core Principles
- **Fact-Over-Fluency**: UNCERTAIN flag if not expert-backed
- **JSON Boundaries**: Strict JSON for all Stage 1-3 handoffs
- **No Overwrite**: `_v[N]` suffix for existing slugs (never overwrites manual edits)
- **Matte-Finish Voice**: Smart-casual, data-grounded, zero fluff
- **Self-Critic**: Mandatory review for repetitive starts, vague adjectives, generic intros
- **Error Handling**: Malformed JSON → STOP + Telegram alert

### Key Files
| File | Purpose |
|------|---------|
| `wiki/trends/[date].json` | Stage 1 JSON handoff (trends + scores) |
| `products/skeletons/[SLUG]_v[N]_SKELETON.md` | Fact-checked skeleton |
| `products/drafts/[SLUG]_v[N].md` | Self-critiqued production draft |
| `products/distribution/[SLUG]_v[N]_reddit_hook.md` | Value-first Reddit comment |
| `output/final_products/[SLUG].pdf` | Production PDF |

---

## Market Discovery (2026-05-10)

[rest of market discovery section unchanged]