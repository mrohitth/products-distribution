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

## Market Discovery (2026-05-10)

Three-layer discovery engine integrated into the 30-min opportunity scanner:

### 1. Tag-Along Logic
- Parses Finnhub news headlines for known WATCHLIST_TICKER + unknown ticker co-occurrences
- Example: "NVDA partners with Nokia" → surfaces NOK for technical screen
- Fetches RSI, MA50, MA200, volume, 52w high for strangers

### 2. Volume/Momentum Screen
- Scans 40 broad-market tickers (sector ETFs + liquid caps like AAPL, TSLA, GE, NOK)
- Flags: volume >= 2x 10-week avg OR daily move >= 4%
- Gated: max once per 4 hours (respects Yahoo Finance rate limits)

### 3. Warm Bench Queue
- Persisted to `data/discovery-queue.json`
- Status lifecycle: new → reviewed → promoted → dismissed
- Auto-expires entries > 30 days old
- Reply `DISCOVER /ticker` to promote, `DISMISS /ticker` to remove

### Key Files
| File | Purpose |
|------|---------|
| `src/lib/market_discovery.ts` | Discovery engine (Tag-Along, volume screen, queue) |
| `data/discovery-queue.json` | Warm Bench — persistents tickers awaiting review |
| `data/discovery-volume-gate.txt` | Time gate for volume screen (4h cooldown) |

### Cost
- Tag-along: 1 Finnhub API call + ~1-5 quote fetches = negligible ($0, free tiers)
- Volume screen: ~40 quote fetches every 4h ≈ 240/day. Same free-tier Yahoo Finance as main scanner.

**Cross-links:**
→ [../index.md](../index.md) — Wiki central
→ [./index.md](./index.md) — Projects index
→ [katzen.md](./katzen.md) — Related project: KATZEN
→ [../decisions/telegram-delivery.md](../decisions/telegram-delivery.md) — Delivery channel decision