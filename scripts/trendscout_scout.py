#!/usr/bin/env python3
"""
trendscout_scout.py — Stage 1: AI-Driven Trend Discovery
=========================================================
Replaces the old hardcoded-query + keyword-scoring approach with:
  - AI-driven query generation (MiniMax proposes diverse queries based on catalog gaps)
  - AI-powered scoring/rating (MiniMax evaluates ALL trends, no force-feeding)
  - Cross-date slug deduplication
  - Full audit trail (rejected + accepted trends saved)
  - Consistent slug + version normalization
  - DuckDuckGo search (no API key needed)

Usage:
  python3 scripts/trendscout_scout.py                  # normal run
  python3 scripts/trendscout_scout.py --force           # re-scout today
  python3 scripts/trendscout_scout.py --dry-run         # show proposed queries only

Output: wiki/trends/{date}.json + wiki/trends/{date}_audit.json
"""
import json, re, sys, time, html as html_mod
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests as req_lib
import urllib.request, urllib.error

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
TRENDS_DIR = WORKSPACE / "wiki" / "trends"
SKELETONS_DIR = WORKSPACE / "products" / "skeletons"
DRAFTS_DIR = WORKSPACE / "products" / "drafts"
ET = timezone(timedelta(hours=-4))

# ── Helper: Brave Search via API (key from openclaw.json) ──────────────────────────

def get_brave_api_key() -> str:
    """Read Brave Search API key from OpenClaw config."""
    try:
        with open(Path("/home/mathew/.openclaw/openclaw.json")) as f:
            cfg = json.load(f)
        tools = cfg.get("tools", {})
        ws = tools.get("web", {}).get("search", {})
        return ws.get("apiKey", "") or ws.get("api_key", "") or ""
    except Exception:
        return ""


def brave_search_api(query: str, count: int = 5, api_key: str = "") -> list[dict]:
    """
    Search via Brave Search API (key from OpenClaw config).
    Returns list of {title, description, url, source}.
    """
    if not api_key:
        api_key = get_brave_api_key()
    if not api_key:
        print(f"    \u26a0\ufe0f  No Brave Search API key found")
        return []

    try:
        resp = req_lib.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": min(count, 10), "safesearch": "off"},
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            },
            timeout=20,
        )
        if resp.status_code == 429:
            print(f"    \u26a0\ufe0f  Brave API rate limited (429) — try again later")
            return []
        if resp.status_code != 200:
            print(f"    \u26a0\ufe0f  Brave API returned {resp.status_code}")
            return []

        data = resp.json()
        results = []

        # Brave API returns web search results in data.web.results
        web_results = data.get("web", {}).get("results", []) if isinstance(data, dict) else []
        if not web_results:
            # Try organic results as fallback
            web_results = data.get("organic", []) if isinstance(data, dict) else []

        for item in web_results[:count]:
            if isinstance(item, dict):
                results.append({
                    "title": (item.get("title") or "").strip(),
                    "description": (item.get("description") or item.get("snippet") or "").strip(),
                    "url": (item.get("url") or item.get("link") or "").strip(),
                    "source": "brave-api",
                })

        return results[:count]
    except Exception as e:
        print(f"    \u26a0\ufe0f  Brave API search error: {e}")
        return []


# ── Helper: Load existing product catalog for gap analysis ─────────────────────────

def load_existing_catalog() -> dict:
    """
    Load all existing draft slugs and trend files for catalog-awareness.
    Returns { "draft_slugs": [...], "past_trend_keywords": [...], "existing_product_titles": [...] }
    """
    draft_slugs = set()
    if DRAFTS_DIR.exists():
        for f in DRAFTS_DIR.glob("*.md"):
            if f.stem and "_SKELETON" not in f.stem:
                draft_slugs.add(f.stem)

    skeleton_slugs = set()
    if SKELETONS_DIR.exists():
        for f in SKELETONS_DIR.glob("*_SKELETON.md"):
            slug = f.stem.replace("_SKELETON", "")
            skeleton_slugs.add(slug)

    past_keywords = set()
    existing_titles = []
    if TRENDS_DIR.exists():
        for f in sorted(TRENDS_DIR.glob("*.json"), reverse=True)[:30]:
            try:
                data = json.loads(f.read_text())
                for t in data.get("trends", []):
                    title = t.get("product_direction", "")
                    if title:
                        existing_titles.append(title[:80])
                    keywords = re.sub(r"[^a-z0-9\s]", " ", (title + " " + (t.get("audience", ""))).lower())
                    past_keywords.update(keywords.split())
            except Exception:
                pass

    return {
        "draft_slugs": sorted(draft_slugs),
        "skeleton_slugs": sorted(skeleton_slugs),
        "past_keywords": sorted(past_keywords),
        "existing_product_titles": existing_titles[-20:],
    }


# ── AI-Driven Query Generation ─────────────────────────────────────────────────────

def generate_queries_ai(creds: dict, catalog: dict) -> list[tuple[str, str]]:
    """
    Use MiniMax to propose diverse search queries based on catalog gaps,
    target subreddits, and evergreen pain point categories.
    Returns list of [(query_string, platform), ...] — 8-12 queries.
    """
    existing = catalog["existing_product_titles"]
    existing_slugs = catalog["draft_slugs"] + catalog["skeleton_slugs"]

    # Seed categories to ensure coverage beyond what's already done
    categories = [
        "cat behavioral issues (litter box, aggression, anxiety) on Reddit",
        "homeowner contractor/home repair problems on Reddit",
        "new pet owner struggles on Reddit",
        "roommate/freelance/client payment disputes on Reddit",
        "new parent / parenting overwhelm on Reddit",
        "weight loss / fitness plateau frustration on Reddit",
        "job search / career rejection burnout on Reddit",
        "first-time homebuyer regret/anxiety on Reddit",
        "pet health emergencies / owner uncertainty on Reddit",
        "home renovation / DIY gone wrong on Reddit",
    ]

    system = """You are a trend discovery strategist for a digital product factory.
Your job is to propose diverse search queries to find emotionally-charged
problem posts on Reddit and Quora that could become digital guide products.

Rules:
- Each query should include the word "Reddit" or "Quora" as a keyword (NOT site: filters)
- Queries must be diverse — no more than 2 queries per topic category
- Prioritize evergreen emotional pain points (scared, overwhelmed, desperate,
  lost money, frustrated, can't figure it out)
- The post must be solveable as a 10-page guide or checklist
- Avoid topics already covered by existing products
- Include at least 1 Quora query for diversity

Output ONLY a JSON array of objects:
[{"query": "the search string", "platform": "reddit" or "quora"}]

Example good query: "cat not using litter box frustrated Reddit"
Example bad query: cat not using litter box site:reddit.com (DO NOT USE)"""

    user_prompt = f"""Generate 9 diverse search queries to discover new digital product opportunities.

Existing products (AVOID these topics unless you find a NEW angle):
{chr(10).join(f"  - {t[:70]}" for t in existing[-10:]) if existing else "  (none yet — first run)"}

Existing slugs:
{chr(10).join(f"  - {s}" for s in existing_slugs[-10:]) if existing_slugs else "  (none)"}

Seed categories (you may use some, but also invent 2-3 new ones):
{chr(10).join(f"  - {c}" for c in categories)}

Requirements:
1. Include "Reddit" or "Quora" as a keyword — do NOT use site: filters
2. Queries should use emotional wording that surfaces high-engagement posts
3. Cover at LEAST 4 different subreddits mentioned naturally (e.g. "Reddit CatAdvice")
4. At most 2 queries from any single subreddit
5. Output ONLY a JSON array — no explanation, no markdown."""

    import urllib.request, urllib.error

    url = f"{creds['base_url']}/v1/messages"
    body = {
        "model": "MiniMax-M2.7",
        "max_tokens": 2000,
        "temperature": 0.8,
        "system": system,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds['api_key']}",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data_in = json.loads(resp.read())
    except Exception as e:
        print(f"  \u26a0\ufe0f  Query generation API error: {e}")
        return get_fallback_queries()

    text = ""
    for block in data_in.get("content", []):
        if block.get("type") == "text":
            text = block["text"]
            break

    if not text:
        return get_fallback_queries()

    # Try to extract JSON — handle markdown fences and loose JSON
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    try:
        queries = json.loads(cleaned)
        if not isinstance(queries, list):
            raise ValueError("Not a list")
        validated = []
        for q in queries:
            qry = (q.get("query") or "").strip()
            platform = (q.get("platform") or "reddit").strip().lower()
            if len(qry) > 15:
                validated.append((qry, platform))
        if validated:
            return validated
    except (json.JSONDecodeError, ValueError):
        # Try to find JSON array in the text
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if match:
            try:
                queries = json.loads(match.group(0))
                validated = []
                for q in queries:
                    qry = (q.get("query") or "").strip()
                    platform = (q.get("platform") or "reddit").strip().lower()
                    if len(qry) > 15:
                        validated.append((qry, platform))
                if validated:
                    return validated
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

    return get_fallback_queries()


def get_fallback_queries() -> list[tuple[str, str]]:
    """Diverse fallback queries when AI generation fails."""
    return [
        ("cat not using litter box frustrated site:reddit.com/r/CatAdvice", "reddit"),
        ("contractor didn't finish job lost money site:reddit.com/r/HomeImprovement", "reddit"),
        ("new kitten aggressive biting site:reddit.com/r/Kitten", "reddit"),
        ("homeowner overwhelmed repairs site:reddit.com/r/FirstTimeHomeBuyer", "reddit"),
        ("freelance client won't pay site:reddit.com/r/freelance", "reddit"),
        ("weight loss plateau can't lose more site:reddit.com/r/loseit", "reddit"),
        ("parenting toddler exhausted burned out site:reddit.com/r/Parenting", "reddit"),
        ("new cat peeing outside litter box site:reddit.com/r/Cats", "reddit"),
        ("cat aggressive biting owner site:quora.com", "quora"),
        ("home contractor scam money lost site:quora.com", "quora"),
    ]


# ── Cross-date slug dedup ──────────────────────────────────────────────────────────

def get_seen_slugs_latest() -> set:
    """Load slugs from the most recent 14 days of trend files."""
    seen = set()
    if not TRENDS_DIR.exists():
        return seen
    files = sorted(TRENDS_DIR.glob("*.json"), reverse=True)[:14]
    for f in files:
        try:
            data = json.loads(f.read_text())
            for t in data.get("trends", []):
                slug = t.get("slug_candidate", "")
                if slug:
                    seen.add(slug)
        except Exception:
            pass
    return seen


# ── Slug + Version Normalization ───────────────────────────────────────────────────

def normalize_slug(base: str) -> str:
    """Consistent slugification — same as in trendscout_gen.py."""
    text = base.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].strip("-")


def get_next_version(base_slug: str) -> str:
    """
    Check existing drafts and skeletons for slug conflicts.
    Returns the slug with the next available version e.g. 'cat-litter-box-rescue-guide_v2'
    """
    existing = {}
    if DRAFTS_DIR.exists():
        for f in DRAFTS_DIR.glob("*.md"):
            if "_SKELETON" in f.stem:
                continue
            existing[f.stem] = "draft"
    if SKELETONS_DIR.exists():
        for f in SKELETONS_DIR.glob("*_SKELETON.md"):
            slug = f.stem.replace("_SKELETON", "")
            existing[slug] = "skeleton"

    # Check if base_slug exists without version
    if base_slug not in existing and base_slug not in [s.rsplit("_v", 1)[0] for s in existing]:
        return f"{base_slug}_v1"

    # Find existing versioned variants
    max_v = 0
    base_key = f"{base_slug}_v"
    for existing_slug in existing:
        if existing_slug == base_slug:
            max_v = max(max_v, 1)
        elif existing_slug.startswith(base_key):
            try:
                v = int(existing_slug.split("_v")[-1])
                max_v = max(max_v, v)
            except ValueError:
                pass

    return f"{base_slug}_v{max_v + 1}"


# ── AI Result Analysis ───────────────────────────────────────────────────────────

def analyze_search_result_ai(creds: dict, result: dict) -> dict | None:
    """
    Use MiniMax to analyze a single search result and produce:
    {audience, emotional_trigger, score_breakdown, total_score,
     solvable_10_page_guide, product_direction, slug_candidate}
    Returns None if the result is not product-worthy.
    """
    title = result.get("title", "")[:150]
    description = result.get("description", "")[:600]
    url = result.get("url", "")

    if len(description) < 80:
        return None

    system = """You are a digital product trend analyst. Given a Reddit/Quora search result,
determine if the problem is worth building a digital product (guide/checklist) around.

Score each dimension 1-3:
- Audience (1=small niche, 2=moderate, 3=large defined group actively searching)
- Emotion (1=low pain, 2=annoyed, 3=visceral urgency or anxiety)
- Monetization (1=unlikely to pay, 2=might buy a $5 checklist, 3=would pay $12+)
- Recurrence (1=one-off problem, 2=seasonal, 3=evergreen — people will search this forever)

Only recommend products where:
- The problem is clearly stated with emotional weight
- A 10-page guide or checklist is a SOLVABLE approach
- The audience is identifiable and large enough
- The problem recurs (new people search this weekly)

Output ONLY JSON with these fields:
- "score_breakdown": {"Audience": int, "Emotion": int, "Monetization": int, "Recurrence": int}
- "total_score": int (sum)
- "audience": "string — describe the audience"
- "emotional_trigger": "string — describe the emotion"
- "product_direction": "string — the guide angle (max 100 chars)"
- "solvable_10_page_guide": bool
- "slug_candidate": "string — URL-friendly slug from product direction"
- "verdict": "PASS" or "REJECT" (REJECT means total_score < 8 or not solvable)
- "rejection_reason": "string — only if REJECT, explain briefly"
No markdown, just JSON."""

    import urllib.request, urllib.error

    url_api = f"{creds['base_url']}/v1/messages"
    body = {
        "model": "MiniMax-M2.7",
        "max_tokens": 1000,
        "temperature": 0.3,
        "system": system,
        "messages": [{"role": "user", "content": f"""Title: {title}
Description: {description}
Source URL: {url}
Analyze this Reddit/Quora post and determine if it should become a digital product."""}],
    }

    req = urllib.request.Request(
        url_api,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds['api_key']}",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    text = None
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data_in = json.loads(resp.read())
            text = ""
            for block in data_in.get("content", []):
                if block.get("type") == "text":
                    text = block["text"]
                    break

            if not text:
                return None

            cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
            parsed = json.loads(cleaned)
            parsed["source_url"] = url
            parsed["title"] = title
            parsed["raw_quote"] = description[:600]
            return parsed
    except (json.JSONDecodeError, Exception):
        # Fallback: try to find JSON in the text
        if text and isinstance(text, str):
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    parsed["source_url"] = url
                    parsed["title"] = title
                    parsed["raw_quote"] = description[:600]
                    return parsed
                except (json.JSONDecodeError, ValueError):
                    pass
        return None


# ── Config helpers ─────────────────────────────────────────────────────────────────

def load_config() -> dict:
    cfg_path = Path("/home/mathew/.openclaw/openclaw.json")
    with open(cfg_path) as f:
        return json.load(f)


def get_minimax_credentials(cfg: dict) -> dict:
    providers = cfg.get("models", {}).get("providers", {})
    minimax = providers.get("minimax", {})
    return {
        "base_url": minimax.get("baseUrl", "https://api.minimax.io/anthropic"),
        "api_key": minimax.get("apiKey", ""),
    }


# ── Main ───────────────────────────────────────────────────────────────────────────

def main() -> int:
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv

    print(f"[{datetime.now(ET).strftime('%H:%M:%S ET')}] TrendScout Stage 1 — AI-Driven Discovery")
    print("=" * 72)

    try:
        cfg = load_config()
        creds = get_minimax_credentials(cfg)
        if not creds["api_key"]:
            print("  ERROR: No MiniMax API key")
            return 1
    except Exception as e:
        print(f"  ERROR: {e}")
        return 1

    today_str = datetime.now(ET).strftime("%Y-%m-%d")
    today_file = TRENDS_DIR / f"{today_str}.json"
    audit_file = TRENDS_DIR / f"{today_str}_audit.json"

    if today_file.exists() and not force:
        existing = json.loads(today_file.read_text())
        high_count = len([t for t in existing.get("trends", [])
                          if t.get("ai_conviction") == "HIGH CONVICTION"])
        if high_count >= 1:
            print(f"  Already scouted today ({high_count} trends) — use --force to rescout")
            return 0

    # ── Load existing catalog for gap-aware queries ────────────────────────────
    catalog = load_existing_catalog()
    print(f"  Existing drafts: {len(catalog['draft_slugs'])} | skeletons: {len(catalog['skeleton_slugs'])}")
    if catalog["existing_product_titles"]:
        print(f"  Recent products: {catalog['existing_product_titles'][-3:]}")

    # ── Step 1: Generate diverse queries ──────────────────────────────────────────
    print("\n[STEP 1] Generating diverse search queries...")
    search_queries = generate_queries_ai(creds, catalog)
    print(f"  Generated {len(search_queries)} queries")

    # ── Load cross-date seen slugs for dedup ──────────────────────────────────
    seen_slugs = get_seen_slugs_latest()

    if dry_run:
        print(f"\n{'='*72}")
        print("  DRY RUN — Proposed queries:")
        for i, (q, p) in enumerate(search_queries, 1):
            print(f"  [{i}] [{p.upper()}] {q}")
        print(f"{'='*72}")
        return 0

    TRENDS_DIR.mkdir(parents=True, exist_ok=True)
    brave_key = get_brave_api_key()
    if not brave_key:
        print("  WARNING: No Brave Search API key — searches will fail")

    # ── Step 2: Search & AI-analyze each result ──────────────────────────────────
    print(f"\n[STEP 2] Searching and analyzing — {len(search_queries)} queries")
    all_analyzed_results = []
    all_rejected_results = []
    total_search_results = 0

    for q_idx, (query, platform) in enumerate(search_queries, 1):
        print(f"\n  [{q_idx}/{len(search_queries)}] [{platform.upper()}] {query[:80]}")
        results = brave_search_api(query, count=4, api_key=brave_key)
        total_search_results += len(results)

        if not results:
            print(f"    No results")
            continue

        for r_idx, r in enumerate(results):
            analyzed = analyze_search_result_ai(creds, r)

            if analyzed is None:
                print(f"    \u26a0\ufe0f  Skipping result {r_idx+1}: too short or AI error")
                all_rejected_results.append({
                    "title": r.get("title", "")[:80],
                    "description": r.get("description", "")[:200],
                    "rejection_reason": "Too short to analyze or AI error",
                    "source_query": query,
                })
                continue

            verdict = analyzed.get("verdict", "REJECT")
            slug_candidate = normalize_slug(analyzed.get("slug_candidate", ""))

            if verdict == "REJECT":
                print(f"    \u274c Rejected: {analyzed.get('slug_candidate', r['title'][:60])[:60]}")
                all_rejected_results.append({
                    "source_query": query,
                    "title": analyzed.get("title", "")[:80],
                    "description": analyzed.get("raw_quote", "")[:200],
                    "rejection_reason": analyzed.get("rejection_reason", "Low score"),
                    "score_breakdown": analyzed.get("score_breakdown", {}),
                    "total_score": analyzed.get("total_score", 0),
                })
                continue

            # Cross-date slug dedup
            if slug_candidate and slug_candidate in seen_slugs:
                versioned = get_next_version(slug_candidate)
                if versioned != f"{slug_candidate}_v1":
                    slug_candidate = versioned
                    print(f"    \U0001f504 Conflict — using {slug_candidate}")
                else:
                    print(f"    \u23ed\ufe0f  Skipping duplicate slug: {slug_candidate}")
                    all_rejected_results.append({
                        "source_query": query,
                        "title": analyzed.get("title", "")[:80],
                        "description": analyzed.get("raw_quote", "")[:200],
                        "rejection_reason": f"Duplicate slug: {slug_candidate}",
                    })
                    continue

            # Success — add to accepted list
            trend = {
                "trend_id": len(all_analyzed_results) + 1,
                "audience": analyzed.get("audience", ""),
                "raw_quote": analyzed.get("raw_quote", ""),
                "emotional_trigger": analyzed.get("emotional_trigger", ""),
                "score_breakdown": analyzed.get("score_breakdown", {}),
                "total_score": analyzed.get("total_score", 0),
                "solvable_10_page_guide": analyzed.get("solvable_10_page_guide", True),
                "product_direction": analyzed.get("product_direction", ""),
                "slug_candidate": slug_candidate,
                "ai_conviction": "HIGH CONVICTION" if analyzed.get("total_score", 0) >= 8 else "MEDIUM",
                "source_url": analyzed.get("source_url", ""),
                "source_query": query,
                "source_platform": platform,
            }
            all_analyzed_results.append(trend)
            seen_slugs.add(slug_candidate)
            total_score = trend["total_score"]
            print(f"    \u2705 [{total_score}/12] {slug_candidate[:60]}")

        time.sleep(0.5)

    # ── Step 3: Final ranking ──────────────────────────────────────────────────────
    print(f"\n[STEP 3] Results summary")
    print(f"  Total search results fetched: {total_search_results}")
    print(f"  Accepted (PASS): {len(all_analyzed_results)}")
    print(f"  Rejected: {len(all_rejected_results)}")

    if not all_analyzed_results:
        print("\n  No PASS-worthy trends found.")
        audit_output = {
            "scouted_at": datetime.now(ET).isoformat(),
            "source_channels": ["reddit.com", "quora.com"],
            "queries": search_queries,
            "total_search_results": total_search_results,
            "trends": [],
            "rejected": all_rejected_results,
            "stage1_status": "COMPLETE_NO_TRENDS",
            "high_score_trends": 0,
        }
        today_file.write_text(json.dumps(audit_output, indent=2))
        print(f"  Saved empty report: {today_file}")
        return 0

    # Sort by total_score descending
    all_analyzed_results.sort(key=lambda t: t.get("total_score", 0), reverse=True)

    # ── NO FORCE-FEEDING ──
    high_trends = [t for t in all_analyzed_results if t["total_score"] >= 8]
    if len(high_trends) == 0:
        print(f"  \u26a0\ufe0f  No genuine HIGH CONVICTION trends (score >= 8) — using top {min(3, len(all_analyzed_results))} trends as MEDIUM")
        high_trends = all_analyzed_results[:3]
        for t in high_trends:
            t["ai_conviction"] = "MEDIUM"

    # ── Step 4: Save output ────────────────────────────────────────────────────────
    output = {
        "scouted_at": datetime.now(ET).isoformat(),
        "source_channels": ["reddit.com", "quora.com"],
        "queries_used": [q[0] for q in search_queries],
        "trends": high_trends,
        "stage1_status": "COMPLETE",
        "high_score_trends": len(high_trends),
        "total_scored": len(all_analyzed_results),
        "version": "v3",
    }
    today_file.write_text(json.dumps(output, indent=2))

    # Audit trail with ALL results
    audit_output = {
        "scouted_at": datetime.now(ET).isoformat(),
        "date": today_str,
        "queries": search_queries,
        "accepted": high_trends,
        "rejected": all_rejected_results,
        "total_accepted": len(high_trends),
        "total_rejected": len(all_rejected_results),
    }
    audit_file.write_text(json.dumps(audit_output, indent=2))

    print(f"\n  Results saved:")
    print(f"    \u2705 {today_file.name} — {len(high_trends)} accepted trends")
    print(f"    \U0001f4cb {audit_file.name} — {len(all_rejected_results)} rejected (audit trail)")

    for i, t in enumerate(high_trends, 1):
        slug = t.get("slug_candidate", "?")
        score = t.get("total_score", 0)
        dir_snippet = t.get("product_direction", "")[:60]
        print(f"\n  [{i}] {slug} (score: {score}/12)")
        print(f"      {dir_snippet}")

    print(f"\n[{datetime.now(ET).strftime('%H:%M:%S ET')}] TrendScout Stage 1 complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
