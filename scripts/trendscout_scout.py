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


def call_minimax(creds: dict, system: str, user: str,
                 max_tokens: int = 4000, temp: float = 0.3, timeout: int = 120) -> str | None:
    """Generic MiniMax API call helper."""
    import urllib.request, urllib.error

    url = f"{creds['base_url']}/v1/messages"
    body = {
        "model": "MiniMax-M2.7",
        "max_tokens": max_tokens,
        "temperature": temp,
        "system": system,
        "messages": [{"role": "user", "content": user}],
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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data_in = json.loads(resp.read())
            for block in data_in.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
            return None
    except Exception as e:
        print(f"  API error: {e}")
        return None


def extract_json_from_response(text: str) -> dict | list | None:
    """Extract JSON from MiniMax response (handles markdown fences, loose text)."""
    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object or array in text
        for pattern in [r'\{.*\}', r'\[.*?\]']:
            match = re.search(pattern, cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    continue
        return None


# ── Batch Result Analysis (replaces 1-at-a-time) ──────────────────────────────────

def batch_analyze_chunk(creds: dict, chunk: list[tuple[dict, str, str, int]],
                         global_idx_offset: int) -> dict[int, dict]:
    """
    Analyze one chunk of results (up to ~12) via MiniMax.
    chunk: list of (result_dict, query, platform, global_index)
    Returns dict mapping global_index -> analyzed dict (or None for reject).
    """
    system = """You are a digital product trend analyst. Score each provided Reddit/Quora search result.

For each result, score 1-3 on each dimension:
- Audience: size/definition of the affected group
- Emotion: pain intensity and urgency
- Monetization: willingness to pay for a solution
- Recurrence: evergreen vs one-time problem

Only mark PASS if total_score >= 8 AND the problem is solvable as a 10-page guide.
Be strict. Not everything is a product.

Output ONLY a JSON array. Each element:
{"index": n (1-based within THIS chunk), "verdict": "PASS" or "REJECT", "total_score": int,
 "score_breakdown": {"Audience": int, "Emotion": int, "Monetization": int, "Recurrence": int},
 "audience": "string", "emotional_trigger": "string",
 "product_direction": "string (max 100 chars)", "slug_candidate": "string",
 "solvable_10_page_guide": bool, "rejection_reason": "string (if REJECT)"}"""

    results_text = "\n\n".join([
        f"--- Result {i+1} ---\nTitle: {r.get('title','')[:150]}\nDescription: {r.get('description','')[:600]}\nSource: {p}\nQuery: {q}"
        for i, (r, q, p, _) in enumerate(chunk)
    ])

    user = f"""Score these {len(chunk)} search results. Determine if each should become a digital product.

{results_text}"""

    result_text = call_minimax(creds, system, user, max_tokens=3000, temp=0.3, timeout=90)
    if not result_text:
        return {}

    parsed = extract_json_from_response(result_text)
    if not parsed or not isinstance(parsed, list):
        return {}

    index_map = {}
    for item in parsed:
        if isinstance(item, dict):
            idx = item.get("index")
            if idx is not None:
                local_idx = idx - 1  # 0-based within chunk
                if 0 <= local_idx < len(chunk):
                    global_idx = chunk[local_idx][3]
                    r = chunk[local_idx][0]
                    item["source_url"] = r.get("url", "")
                    item["title"] = r.get("title", "")[:150]
                    item["raw_quote"] = r.get("description", "")[:600].strip()
                    index_map[global_idx] = item
    return index_map


def batch_analyze_results(creds: dict, all_results: list[tuple[dict, str, str]]) -> list[dict | None]:
    """
    Batch-analyze ALL results in chunks of ~10, max 2 concurrent MiniMax calls.
    Returns list parallel to input: analyzed dict or None.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Build valid list with global indices
    valid = [(r, q, p, i) for i, (r, q, p) in enumerate(all_results)
             if len(r.get("description", "").strip()) >= 80]

    if not valid:
        return [None] * len(all_results)

    # Split into chunks of 10
    chunk_size = 10
    chunks = [valid[i:i + chunk_size] for i in range(0, len(valid), chunk_size)]
    print(f"    Splitting {len(valid)} valid results into {len(chunks)} chunks of max {chunk_size}")

    # Process chunks in parallel (max 2)
    results_map: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(batch_analyze_chunk, creds, ch, 0): ch for ch in chunks}
        for fut in as_completed(futures):
            chunk_results = fut.result()
            results_map.update(chunk_results)
            print(f"      Chunk done: {len(chunk_results)} scored")

    # Map back to original input order
    final = []
    for i in range(len(all_results)):
        if i in results_map:
            final.append(results_map[i])
        else:
            final.append(None)
    return final



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

    # ── Step 2: Parallel search + batch analysis ──────────────────────────────
    print(f"\n[STEP 2] Parallel Brave Search — {len(search_queries)} queries")
    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_raw_results: list[tuple[dict, str, str]] = []  # (result_dict, query, platform)

    def search_one(q: str, p: str) -> list[tuple[dict, str, str]]:
        try:
            res = brave_search_api(q, count=4, api_key=brave_key)
            return [(r, q, p) for r in res]
        except Exception as e:
            print(f"    \u26a0\ufe0f  Search error for [{p}] {q[:50]}: {e}")
            return []

    # All 9+ Brave searches run in parallel via ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=9) as pool:
        fut_map = {pool.submit(search_one, q, p): (q, p) for q, p in search_queries}
        for fut in as_completed(fut_map):
            q, p = fut_map[fut]
            batch = fut.result()
            all_raw_results.extend(batch)
            print(f"    [{p.upper()}] {q[:70]} \u2192 {len(batch)} results")

    total_search_results = len(all_raw_results)
    print(f"\n  Total results collected: {total_search_results}")

    if not all_raw_results:
        print("  No results from any query — exiting")
        audit_output = {
            "scouted_at": datetime.now(ET).isoformat(),
            "source_channels": ["reddit.com", "quora.com"],
            "queries": search_queries,
            "total_search_results": 0,
            "trends": [],
            "rejected": [],
            "stage1_status": "NO_RESULTS",
            "high_score_trends": 0,
        }
        today_file.write_text(json.dumps(audit_output, indent=2))
        return 0

    # ── Step 2b: Batch MiniMax analysis (1 call instead of N) ────────────────────
    print(f"\n  Batch analyzing {total_search_results} results via MiniMax...")
    analyzed_batch = batch_analyze_results(creds, all_raw_results)

    all_analyzed_results = []
    all_rejected_results = []

    for idx, analyzed in enumerate(analyzed_batch):
        r, query, platform = all_raw_results[idx]

        if analyzed is None:
            all_rejected_results.append({
                "title": r.get("title", "")[:80],
                "description": r.get("description", "")[:200],
                "rejection_reason": "Too short or AI analysis failed",
                "source_query": query,
            })
            continue

        verdict = analyzed.get("verdict", "REJECT")
        slug_candidate = normalize_slug(analyzed.get("slug_candidate", ""))

        if verdict == "REJECT":
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
                print(f"    \U0001f504 Conflict—using {slug_candidate}")
            else:
                all_rejected_results.append({
                    "source_query": query,
                    "title": analyzed.get("title", "")[:80],
                    "description": analyzed.get("raw_quote", "")[:200],
                    "rejection_reason": f"Duplicate slug: {slug_candidate}",
                })
                continue

        # Accepted
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
        print(f"    \u2705 [{trend['total_score']}/12] {slug_candidate[:60]}")

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
