# KATZEN — Kitty's Zen Dashboard

**Spec Version:** 1.0  
**Last Updated:** 2026-05-03  
**Status:** Phase 1 — Building

---

## 🎯 Overview

A Next.js "Mission Control" dashboard for the OpenClaw agentic system. Transforms workspace files into a "Digital Zen Garden" — organic, calm, highly functional.

**Screens (Phase 1):**
1. Tasks — Kanban board from Markdown checkbox syntax
2. Memory — Journal-style feed of daily logs + MEMORY.md
3. Projects — Directory/tag grouping (empty state until work accumulates)

**Future Phases:**
- Docs (indexed library)
- Zen Office (organic 2D visualization)
- GitHub integration

---

## 🎨 Visual Style Guide

### Colors
| Token | Hex | Usage |
|-------|-----|-------|
| Background | `#0B0E14` | Ultra-dark obsidian base |
| Surface | `#131920` | Card backgrounds |
| Border | `#1E2630` | Subtle card borders |
| Moss-Green | `#4ADE80` | Active states, success |
| Violet | `#A78BFA` | Memory, past events |
| Amber | `#FBBF24` | Alerts, warnings |
| Text-Primary | `#F1F5F9` | High contrast headers |
| Text-Secondary | `#94A3B8` | Subdued labels |

### Typography
- **UI:** Inter / Geist (clean sans-serif)
- **System:** JetBrains Mono (timestamps, word counts, file paths)

### Layout
- **Nav:** Left vertical rail with icons
- **Content:** Watchlist pattern — high-contrast headers, status tags, health-bar progress
- **Cards:** Rounded corners, 1px glowing borders (moss-green active, violet for memory, amber for alerts)

---

## 📂 Data Sources

### Workspace Structure
```
~/.openclaw/workspace/
├── AGENTS.md          # System instructions
├── SOUL.md            # Agent personality
├── USER.md            # User profile
├── IDENTITY.md        # Agent identity
├── MEMORY.md          # Long-term memory (curated)
├── HEARTBEAT.md       # Periodic task checklist
├── TOOLS.md           # Tool preferences
├── memory/
│   └── YYYY-MM-DD.md  # Daily session logs
└── [project dirs]/    # User-created project folders
```

### Task Parsing
- Source: `memory/YYYY-MM-DD.md` → `## Tasks` section
- Syntax: `- [ ]` = PENDING, `- [x]` = DONE
- Fallback: `runs.sqlite` task_runs table (currently empty)

### Memory Parsing
- Daily logs: `memory/YYYY-MM-DD.md`
- Long-term: `MEMORY.md`

### Projects
- Directories in workspace that aren't system folders (memory/, .openclaw/)
- Frontmatter `Project:` tags in files

---

## 🔧 Technical Stack

- **Framework:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS + shadcn/ui
- **State:** Server Components + filesystem reads (no mock data)
- **Icons:** Lucide React

---

## 📦 Phase 1 Scope

1. Scaffold Next.js project with shadcn/ui
2. Dark obsidian theme configured
3. Left nav with icon rail
4. Tasks screen — parse `## Tasks` from current day's memory log, render as Kanban
5. Memory screen — journal feed of all `memory/*.md` + MEMORY.md
6. Projects screen — workspace directory listing (empty state handling)
7. Real data, no mocks

---

## 🚧 Constraints

- NO mock data — must read actual workspace files
- NO lorem ipsum
- runs.sqlite is empty (no historical tasks) — use Markdown parsing as bridge
- GitHub integration not in Phase 1 scope