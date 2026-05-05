# KATZEN — Kitty's Zen

**Owner:** [K] Kitty  
**Type:** Next.js Web Application  
**Status:** Phase 1 complete | Phase 2 (multi-agent swarm) in progress  
**Repos:** `mrohitth/katzen` (primary), `mrohitth/personal` (support)  
**Dev Server:** `npm run dev` → localhost:3000

---

## What It Is

Visual layer over OpenClaw workspace — "Digital Zen Garden." Real-time reflection of Kitty's state. No mock data in production views.

**Tech Stack:** Next.js App Router, Tailwind CSS, shadcn/ui, TypeScript

**Visual Style — Bio-Digital Noir:**
- Obsidian background: `#0B0E14`
- Moss active states: `#4ADE80`
- Violet memory accents: `#A78BFA`
- Amber alerts: `#FBBF24`
- Font: JetBrains Mono (metrics), Inter (UI prose)

---

## Features (Phase 1)

| Feature | Description |
|---------|-------------|
| Tasks | Quick Add + optimistic UI + [KITTY] toast notifications |
| Memory | Morning Briefing from `/api/memory/digest` |
| Projects | GitHub Stats, Budget Card, Portfolio P/L (donut chart) |
| Zen Office | Blooming flower mechanic (1 bloom / 3 completed tasks) |
| Command Bar | Heartbeat countdown, budget burn, focus slot |
| Click-to-Edit | Inline editing on Kanban cards |
| AgentStatusHUD | Header bar with agent status |
| Memory Tooltips | Task hover shows memory context |
| Ctrl+K Search | Full-text search across memory files |
| Market Signal Bar | NVDA/SMH/SCHG with BULL/BEAR signals |

---

## API Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/tasks` | GET/POST/PATCH | Task CRUD from `memory/YYYY-MM-DD.md` |
| `/api/memory/digest` | GET | Morning briefing (parses all ## Tasks sections) |
| `/api/search?q=` | GET | Full-text search |
| `/api/scheduler` | GET | Next heartbeat countdown |
| `/api/heartbeat` | GET | Heartbeat count |
| `/api/usage` | GET | Token cost vs $1/day budget |
| `/api/usage/minimax` | GET | Live MiniMax API usage |
| `/api/github/stats` | GET | GitHub repo stats |
| `/api/market/signal` | GET | NVDA/SMH/SCHG/QQQ/SCHD/VXUS/VOOG signals |
| `/api/projects` | GET | Workspace directories list |

---

## Portfolio P/L Card (Latest)

Redesigned 2026-05-03 to focus on profit/loss (not per-share prices):
- Large total P/L display: `+$3,027.95 (+7.44%)`
- SVG donut chart showing allocation across 10 positions
- Top 3 Gainers + Top 3 Losers with % and absolute $
- Total Value, Cost Basis, Unrealized G/L bar

---

## Phase Roadmap

| Phase | Target | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Done | Mission Control Live |
| Phase 2 | Q2 2026 | Multi-Agent Swarm — Witty/Mitty/Bitty/Titty come online |
| Phase 3 | Q3 2026 | Investment Autonomy — live market data |
| Phase 4 | Q4 2026 | Data Engineering Co-Pilot |
| Phase 5 | 2027 | Fully Autonomous Workspace |

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./index.md](./index.md) — Projects index  
→ [marketbot.md](./marketbot.md) — Related project: MarketBot  
→ [../decisions/portfolio-pl-card.md](../decisions/portfolio-pl-card.md) — P/L card redesign decision