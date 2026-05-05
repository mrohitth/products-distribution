# TOOLS.md — Kitty's Operational Toolkit

_Version 2.0 | Index of all available tools and skills_

---

## OpenClaw Native Tools

### Core File Operations
| Tool | Purpose | Usage |
|------|---------|-------|
| `read` | Read file contents | Inspect workspace files, memory logs, configs |
| `write` | Create/overwrite files | Update daily logs, create docs, modify workspace |
| `edit` | Targeted text replacement | Fix typos, update specific lines in files |
| `exec` | Run shell commands | Git operations, file system inspection, npm scripts |

### Process Management
| Tool | Purpose | Usage |
|------|---------|-------|
| `process` | Manage background sessions | Long-running builds, polling loops |
| `sessions_*` | Manage agent sessions | Fork sub-agents, send inter-agent messages |

### Web & Research
| Tool | Purpose | Usage |
|------|---------|-------|
| `web_search` | Brave search API | Technical research, market data, documentation |
| `web_fetch` | Extract readable content from URLs | Pull docs, scrape technical articles |

### Memory & Context
| Tool | Purpose | Usage |
|------|---------|-------|
| `memory_search` | Semantic search across memory files | Find past decisions, lessons learned |
| `memory_get` | Safe excerpt reading | Pull specific lines from MEMORY.md or logs |

### Cron & Scheduling
| Tool | Purpose | Usage |
|------|---------|-------|
| `cron` | Schedule future tasks | Reminders, periodic checks, autonomous cadence |

### Media (Available but Rarely Used)
| Tool | Purpose | Usage |
|------|---------|-------|
| `image` | Analyze images | Inspect screenshots, reference images |
| `image_generate` | Generate AI images | Visual concepts, dashboard mockups |
| `music_generate` | Generate audio | Not in active use |
| `video_generate` | Generate video | Not in active use |

---

## OpenClaw Skills

Skills provide specialized instructions for specific task domains.

### Available Skills (Enabled)

#### 🌤️ Weather (`weather`)
- **Location:** `~/.nvm/versions/node/v22.22.2/lib/node_modules/openclaw/skills/weather/SKILL.md`
- **Purpose:** Current weather, rain detection, temperature, forecasts for travel planning
- **Trigger:** Weather-related questions, travel planning
- **Notes:** Requires location input — use Falls Church, VA by default for Mathew

#### 🔄 Taskflow (`taskflow`)
- **Location:** `~/.nvm/versions/node/v22.22.2/lib/node_modules/openclaw/skills/taskflow/SKILL.md`
- **Purpose:** Coordinate multi-step detached tasks as durable TaskFlow jobs
- **Trigger:** Complex projects requiring parallel execution, sub-agent orchestration
- **Notes:** Use for KATZEN Phase 2+ development when multi-agent coordination is needed

#### 🔀 ACP Router (`acp-router`)
- **Location:** `~/.nvm/versions/node/v22.22.2/lib/node_modules/openclaw/skills/acp-router/SKILL.md`
- **Purpose:** Route plain-language requests for coding agents (Claude Code, Cursor, Copilot, etc.)
- **Trigger:** Explicit requests to use external coding agents
- **Notes:** Generally NOT used — I do the coding directly

### Available Skills (Available but Not Enabled)

| Skill | Purpose |
|--------|---------|
| `healthcheck` | Audit and harden hosts for SSH, firewall, updates |
| `node-connect` | Diagnose OpenClaw mobile node pairing |
| `skill-creator` | Create/edit/improve AgentSkills |
| `taskflow-inbox-triage` | Example TaskFlow for inbox routing |
| `github` | GitHub API integration (enable when GitHub integration needed) |
| `himalaya` | Email management |
| `notion` | Notion integration |

---

## KATZEN Dashboard API Routes

All routes live under `/api/` and read/write from the OpenClaw workspace.

### Task Management
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/tasks` | GET | Fetch task counts (pending/done) and top priority task |
| `/api/tasks` | POST | Add new task to `memory/YYYY-MM-DD.md` |
| `/api/tasks` | PATCH | Update/edit task status in markdown via regex |

### Memory & Search
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/memory/digest` | GET | Generate morning briefing from yesterday's log |
| `/api/search?q=` | GET | Full-text search across `memory/` and `MEMORY.md` |

### System Status
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/scheduler` | GET | Next heartbeat countdown, cron job status |
| `/api/heartbeat` | GET | Heartbeat count for incubator progress |
| `/api/usage` | GET | Token cost, daily burn vs $1 budget |

### GitHub Integration
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/github/stats` | GET | Stars, forks, issues, recent commits from mrohitth/katzen |

### Market Data
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/market/signal` | GET | Mock NVDA/SMH/SCHG prices with BULL/BEAR signals |

### Documentation
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/docs/indexed` | GET | List files in `workspace/docs/` |
| `/api/docs/generate` | GET | Generate weekly report from last 7 days of logs |

### Agent Info
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/agents?id=` | GET | Return agent definition (role, mission, tools) |

---

## Workspace Data Sources

### Primary Files
| File | Purpose | Format |
|------|---------|--------|
| `memory/YYYY-MM-DD.md` | Daily session logs | Markdown with `## Tasks` checkbox sections |
| `MEMORY.md` | Long-term durable facts archive | Structured markdown |
| `USER.md` | Mathew's complete profile | Structured markdown |
| `IDENTITY.md` | Kitty's formal role definition | Structured markdown |
| `SOUL.md` | Kitty's personality matrix | Prose + structured rules |
| `AGENTS.md` | Agent hierarchy and workspace conventions | Prose + structured rules |
| `HEARTBEAT.md` | Autonomous cadence protocol | Structured markdown |
| `TOOLS.md` | This file — tool index | Structured markdown |
| `SPEC.md` | KATZEN project specification | Structured markdown |

### System Files (Read-Only)
| File | Purpose |
|------|---------|
| `~/.openclaw/openclaw.json` | Gateway config, cron jobs, credentials |
| `~/.openclaw/agents/main/sessions/` | Session history (JSONL) |
| `~/.openclaw/tasks/runs.sqlite` | Task run database (currently empty) |

---

## Usage Notes

### When to Use Each Tool

**File Operations:**
- `write` for creating new files or full overwrites
- `edit` for targeted changes (preferred over write when possible)
- `read` before modifying to understand context

**Shell Commands:**
- `exec` for git operations, npm scripts, file inspection
- Avoid exec for file content manipulation (use read/write/edit instead)

**Web Operations:**
- `web_search` for technical research, documentation lookup
- `web_fetch` for extracting readable content from URLs

**Scheduling:**
- `cron` for precise timing requirements ("9am sharp", "every Monday")
- Heartbeat for batched periodic checks

---

## Tool Limitations

| Constraint | Workaround |
|------------|------------|
| `memory_search` semantic search | Use exact phrase search via `web_search` for better results |
| `runs.sqlite` empty | Use markdown checkbox parsing as bridge until task jobs populate DB |
| No native SQLite write in browser | KATZEN uses markdown as task source of truth |

---

_This file is the operational reference for all available tools. Update when new skills or API routes are added._