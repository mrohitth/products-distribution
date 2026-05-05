# Portfolio P/L Card — Redesigned to Focus on Profit/Loss

**Date:** 2026-05-03  
**Agents:** [K] Kitty  
**Trigger:** Mathew feedback: "I don't need how much each share is for. I need to know profit/loss."

---

## Context

Original Portfolio Health card showed per-share prices + daily change % for each of 10 positions. Mathew found this noisy and not the information he cared about. He wants to see: **how much am I up or down overall?**

## Options Considered

- **Option A (kept):** Show per-share prices + daily change — noisy, not aligned with what Mathew wants
- **Option B (chosen):** Total P/L prominently displayed + donut chart of allocation + top gainers/losers

## Decision Made

Redesigned Portfolio Health → Portfolio P/L card with:
- Large total P/L display: `+$3,027.95 (+7.44%)` in moss green or amber
- SVG donut chart showing allocation across 10 positions
- Top 3 Gainers + Top 3 Losers (sorted by % gain/loss)
- Per-position mini bars showing relative P/L magnitude
- Total Value, Cost Basis, Unrealized G/L bar
- **Removed:** per-share current price, daily change %, category labels

## Outcome

Card now shows what matters: total profit/loss, who's winning, who's losing, and allocation context.

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [../decisions/index.md](./index.md) — Decisions index  
→ [../projects/katzen.md](../projects/katzen.md) — KATZEN project  
→ [heartbeat-hours-format.md](./heartbeat-hours-format.md) — Related decision: same UX sweep