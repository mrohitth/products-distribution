# TrendScout Pipeline — v2.1 Golden Stack

**Owner:** Kitty 🐱  
**Type:** Autonomous Digital Product Factory  
**Cron:** `1e85c944` — Daily 10:00 AM ET  
**Model:** MiniMax M2.7 (locked, no fallbacks)  
**Search:** Brave Search API (r/Parenting, r/CatAdvice, r/Homeowners, Quora)  
**Delivery:** Telegram announce to mrohitth  
**Target:** Lemon Squeezy deployment

---

## Output Directory Structure

```
workspace/
├── wiki/trends/[date].json                    # Stage 1 JSON handoff
├── products/skeletons/[SLUG]_v[N]_SKELETON.md  # Stage 2 fact-checked skeleton
├── products/drafts/[SLUG]_v[N].md              # Stage 3 self-critiqued draft
├── products/distribution/[SLUG]_v[N]_distribution.md  # Stage 4 Reddit Bridge + Pinterest
├── output/final_products/[SLUG].pdf            # Stage 5 production PDF
├── output/final_products/[SLUG]_CHECKLIST.pdf  # Stage 5.5 companion checklist
└── GitHub: final_products/ → same two PDF files
```

## Core Pipeline Rules

| # | Rule | Detail |
|---|------|--------|
| 1 | **JSON-Only Handoffs** | All Stage 1-3 transitions use strict JSON schemas. No conversational text between stages. |
| 2 | **Zero Placeholders** | "Coming in V2" or "Full version soon" = critical failure. Research it or delete the section. |
| 3 | **Slug Collision** | If `[SLUG].md` exists, read first 50 lines. >80% similar → SKIP. New angle → `_v[N]`. |
| 4 | **Matte-Finish Voice** | Zero AI-slop. No "delve," "embark," or "unlocking potential." Smart-casual, data-grounded, empathetic. |
| 5 | **Golden Stack CTA** | Final page must include: Lemon Squeezy Checkout link (new users) + Member's Area link (existing customers). "Your Bonus: [SLUG] Checklist Included" — never "Get the free checklist." |
| 6 | **Companion Bundle** | Every PDF gets a `_CHECKLIST.pdf` companion (1-page printable protocol). Stage 6 confirms both files. |

## Stage Breakdown

### Stage 1: Scout (Search-Driven Discovery)
- Brave Search 3 Reddit/Quora problem posts
- Must have raw user quote with emotional anchor
- Score 1-10 across Audience/Emotion/Monetization/Recurrence
- Must pass "10-page standalone guide today?" test — if not, score = 0
- Output: `wiki/trends/[date].json`

### Stage 2: Architect (Verified Skeleton)
- Only runs for trends with total_score > 8/10
- Problem diagnosis + 3 solution pillars
- **Mandatory Fact-Check**: Each pillar marked VERIFIED (sourced), PLAUSIBLE, or UNCERTAIN
- UNCERTAIN pillars get warning note — research or remove
- Output: JSON skeleton → `products/skeletons/[SLUG]_v[N]_SKELETON.md`

### Stage 3: Draft (Full Production)
- 10-page standalone guide with actionable how-to content
- **Self-Critic Pass**: Check for repetitive starts, vague adjectives, generic intros — rewrite
- **Golden Stack CTA**: Lemon Squeezy link + Member's Area link on final page
- Output: `products/drafts/[SLUG]_v[N].md`

### Stage 4: Distribution (NO Social Media)
- **Reddit Bridge**: Value-first post quoting user's problem, high-value advice, mention free checklist as resource, soft close ("happy to share")
- **Pinterest Solution Pin**: SEO-optimized title + 500-char keyword description
- Output: `products/distribution/[SLUG]_v[N]_distribution.md`

### Stage 5: Production + Stage 5.5: Companion
- `cleanup_for_production()` — strip AI metadata/YAML
- PDF via WeasyPrint
- **Stage 5.5**: Auto-generate `_CHECKLIST.pdf` — 1-page printable protocol/cheat sheet
- GitHub sync to `final_products/`
- FILE DELIVERY: Attach .md + .pdf + _CHECKLIST.pdf to session

### Stage 6: Announce
```
🚨 Pipeline Complete — [DATE]
📊 Stage 1: Scout → [trend names + scores]
🏗️ Stage 2: Architect → [pillar verification log]
📝 Stage 3: Draft → [slug]_v[N].md
📄 Stage 4: Distribution → Reddit Bridge + Pinterest Pin
📦 Stage 5: Production → [SLUG].pdf ([size]KB)
🎁 Stage 5.5: Companion → [SLUG]_CHECKLIST.pdf ([size]KB)
```

### Error Handling
- 0 high-conviction trends → `{"status":"SKIPPED","reason":"No high-value pain points found"}`
- JSON malformed → STOP + Telegram alert
- No VERIFIED pillars → proceed with PLAUSIBLE, note in skeleton
- >80% similar to existing → SKIP silently

## Key Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `pipeline_manager.py` | `scripts/pipeline_manager.py` | PDF generation, GitHub sync, distro registration |
| `bitty_wiki_guardian.py` | `bitty_wiki_guardian.py` | Correction Ledger enforcement (no Spark/Kafka/Snowflake in wiki) |
| `pipeline_chain.sh` | `scripts/pipeline_chain.sh` | Manual off-schedule pipeline runner |

## GitHub Release Tags

Format: `v1-{slug}` (strips `_v[N]` from slug). Example:
- File: `cat-litter-box-rescue-guide_v1.pdf`
- Tag: `v1-cat-litter-box-rescue-guide`
- Location: `https://github.com/mrohitth/products-distribution`

---

*Last updated: 2026-05-10 | v2.1 — Golden Stack*
