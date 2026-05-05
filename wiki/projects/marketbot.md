# MarketBot — The Capital Pilot

**Owner:** [K] Kitty  
**Type:** Node.js Financial Strategist  
**Status:** ✅ VERIFIED — Brief delivered to Telegram 2026-05-03  
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
| Profit Maximizer | Semi/tech sector scanner — flags setups |
| Black Swan Rule | 8% loss threshold — requires [CONFIRMED] before alerting |
| Gmail/Fidelity Scan | Extracts trade confirmations from Fidelity emails |
| Telegram Delivery | Direct to telegram:5607383477 via OpenClaw announce |

---

## Portfolio (Real Positions — May 3, 2026)

**Total:** $43,757.84 | **G/L:** +$3,027.95 (+7.44%) | **10 positions**

| Ticker | Shares | Avg Cost | Current | Mkt Value | G/L | Weight |
|--------|--------|----------|---------|-----------|-----|--------|
| VTI | 34 | $230.97 | $260.00 | $8,826.82 | +12.6% | 20.2% |
| NVDA | 41.6 | $203.11 | $198.45 | $8,255.52 | -2.4% | 18.9% |
| VOO | 17.1 | $402.90 | $450.00 | $7,709.08 | +11.7% | 17.6% |
| QQQ | 9.4 | $596.86 | $674.15 | $6,309.36 | +13.1% | 14.4% |
| SMH | 8.1 | $503.28 | $509.82 | $4,152.99 | +1.3% | 9.5% |
| SCHG | 102.4 | $30.01 | $33.14 | $3,392.04 | +5.2% | 7.8% |
| VXUS | 29.7 | $73.16 | $82.97 | $2,464.54 | +13.4% | 5.6% |
| SCHD | 75.2 | $29.35 | $31.86 | $2,394.47 | +8.6% | 5.5% |
| SPYD | 3.7 | $40.72 | $45.00 | $165.55 | +10.5% | 0.4% |
| ASTS | 8.7 | $11.42 | $10.00 | $87.47 | -12.5% | 0.2% |

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

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./index.md](./index.md) — Projects index  
→ [katzen.md](./katzen.md) — Related project: KATZEN  
→ [../decisions/telegram-delivery.md](../decisions/telegram-delivery.md) — Delivery channel decision