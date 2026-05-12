#!/usr/bin/env python3
"""
AI Agentic Checklist Synthesizer — v7 (Dynamic)
=================================================
Three core improvements over v6:
  1. NO HARDCODED ITEMS — reads actual draft content from products/drafts/
  2. AI-GENERATED checklists via MiniMax based on real trendscout data
  3. Cached for efficiency — regenerates only when draft content changes

Each item follows the Senior Content Strategist formula:
    [Bolded Header] + [Action Verb] + [Main Task] + [Why/How Detail]

Usage:
    python3 scripts/synthesize_checklist.py                          # all active slugs
    python3 scripts/synthesize_checklist.py cat-litter-box-rescue-guide_v1  # specific slug
    python3 scripts/synthesize_checklist.py --force                  # force regenerate cache
"""
import sys, html as html_mod, json, hashlib, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "output" / "final_products"
DRAFTS_DIR = WORKSPACE / "products" / "drafts"
TRENDS_DIR = WORKSPACE / "wiki" / "trends"
CACHE_DIR = WORKSPACE / "products" / ".checklist_cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

MAX_CHARS_PER_SLUG = 12  # 12 items per checklist


# ── Config helpers (shared) ────────────────────────────────────────────────────

def load_config() -> dict:
    with open(Path("/home/mathew/.openclaw/openclaw.json")) as f:
        return json.load(f)


def get_minimax_credentials(cfg: dict) -> dict:
    providers = cfg.get("models", {}).get("providers", {})
    minimax = providers.get("minimax", {})
    return {
        "base_url": minimax.get("baseUrl", "https://api.minimax.io/anthropic"),
        "api_key": minimax.get("apiKey", ""),
    }


def call_minimax(creds: dict, system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str | None:
    import urllib.request, urllib.error

    url = f"{creds['base_url']}/v1/messages"
    body = {
        "model": "MiniMax-M2.7",
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "system": system_prompt,
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
            data = json.loads(resp.read())
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
            return ""
    except Exception as e:
        print(f"  API error: {e}")
        return None


# ── Active slug discovery (dynamic from TrendScout JSON) ─────────────────────

def get_active_slugs() -> list[str]:
    """Load slugs from today's TrendScout JSON. Falls back to slugs from drafts dir."""
    today = datetime.now().strftime("%Y-%m-%d")
    trends_file = TRENDS_DIR / f"{today}.json"

    if trends_file.exists():
        data = json.loads(trends_file.read_text())
        slugs = []
        for t in data.get("trends", []):
            slug = t.get("slug_candidate", "")
            # Also try as-is: the slug_candidate from scout includes _v{N}
            draft = DRAFTS_DIR / f"{slug}.md"
            if draft.exists():
                slugs.append(slug)
            else:
                # Try without version suffix
                base = slug.rsplit("_v", 1)[0] if "_v" in slug else slug
                for f in sorted(DRAFTS_DIR.glob(f"{base}*.md"), reverse=True):
                    slugs.append(f.stem)
                    break
        if slugs:
            return slugs

    # Fallback: discover all draft slugs
    slugs = []
    if DRAFTS_DIR.exists():
        for f in DRAFTS_DIR.glob("*.md"):
            if "_SKELETON" not in f.stem:
                slugs.append(f.stem)
    return slugs


# ── Cache system ──────────────────────────────────────────────────────────────

def get_draft_hash(slug: str) -> str:
    """MD5 hash of draft content for cache invalidation."""
    draft_path = DRAFTS_DIR / f"{slug}.md"
    if not draft_path.exists():
        return ""
    return hashlib.md5(draft_path.read_bytes()).hexdigest()


def load_cached_items(slug: str) -> tuple[list[str], list[str]] | None:
    """Returns (items[], category_labels[]) from cache if draft unchanged."""
    cache_path = CACHE_DIR / f"{slug}.json"
    if not cache_path.exists():
        return None
    try:
        cache = json.loads(cache_path.read_text())
        current_hash = get_draft_hash(slug)
        if cache.get("draft_hash") == current_hash:
            return cache.get("items", []), cache.get("categories", [])
    except Exception:
        pass
    return None


def save_cached_items(slug: str, items: list[str], categories: list[str]) -> None:
    """Save generated items + categories to cache."""
    cache_path = CACHE_DIR / f"{slug}.json"
    cache = {
        "slug": slug,
        "draft_hash": get_draft_hash(slug),
        "items": items,
        "categories": categories,
        "generated_at": datetime.now().isoformat(),
    }
    cache_path.write_text(json.dumps(cache, indent=2))


# ── AI-driven checklist generation ────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Senior Content Strategist writing action checklists that
always COMPLEMENT a full guide — they are NOT standalone.

Each checklist item follows this exact structure:
[Bolded Header] + [Action Verb] + [Main Task] + [Why/How Detail]

Format: "Bolded Header: Complete sentence explaining what to do and why it matters."
The bolded header and the body are separated by ": " — the header is a short descriptive label, the body is a complete sentence.

Rules:
- ALL items must be COMPLETE SENTENCES — no fragments
- Every item must be at least 20 words — short items are not helpful
- Plain English only — no academic terms
- Each item must be a REAL, ACTIONABLE step — not a concept or idea
- Write in the imperative: "Call your vet..." NOT "You should call your vet..."
- Group items into exactly 3 categories with 4 items each (12 items total)
- Category labels must be short (max 40 chars), imperative, and specific
- No placeholder text, no "Coming in V2," no vague promises
- Draw the items DIRECTLY from the guide content — don't invent new steps

Output ONLY a JSON object:
{
  "categories": ["Category 1 Label", "Category 2 Label", "Category 3 Label"],
  "items": [
    "Category 1, Item 1: Complete sentence...",
    "Category 1, Item 2: Complete sentence...",
    ...
    "Category 3, Item 4: Complete sentence..."
  ]
}

Exactly 12 items. 3 categories. 4 items per category.
No markdown, no extra text, just the JSON object."""


def generate_checklist_items(creds: dict, slug: str, draft_text: str, trend_data: dict | None) -> tuple[list[str], list[str]] | None:
    """
    Generate 12 checklist items + 3 category labels using MiniMax.
    Returns (items[], categories[]) or None on failure.
    """
    # Build context from trend data (the pain point, audience, etc.)
    trend_context = ""
    if trend_data:
        trend_context = (
            f"Audience: {trend_data.get('audience', '')}\n"
            f"Pain Point: {trend_data.get('raw_quote', '')[:300]}\n"
            f"Emotional Trigger: {trend_data.get('emotional_trigger', '')}\n"
            f"Guide Direction: {trend_data.get('product_direction', '')}\n"
        )

    # Extract key sections from draft (first ~6000 chars of body content)
    # Strip YAML frontmatter
    body = draft_text
    if body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()

    draft_excerpt = body[:6000]
    word_count = len(body.split())

    user = f"""Read this guide draft and create a 12-item action checklist that helps the reader implement the guide's advice.

Guide Slug: {slug}
Guide Word Count: {word_count}
{trend_context}

DRAFT CONTENT:
{draft_excerpt}

Generate 12 actionable checklist items (4 per category, 3 categories) that capture the ESSENTIAL steps from this guide."""

    result = call_minimax(creds, SYSTEM_PROMPT, user, max_tokens=3000)
    if not result:
        return None

    # Parse JSON — handle markdown fences
    cleaned = re.sub(r"```(?:json)?\s*", "", result).strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        else:
            return None

    items = parsed.get("items", [])
    categories = parsed.get("categories", [])

    # Validate
    if len(items) != 12:
        print(f"    ⚠️  Expected 12 items, got {len(items)} — padding/shrinking")
        while len(items) < 12:
            items.append(f"Check the Full Guide: This step is described in detail in the companion guide — open {slug}.md and review the relevant section.")
        items = items[:12]

    if len(categories) != 3:
        categories = ["First Steps", "Core Actions", "Follow-Through"]
        print(f"    ⚠️  Expected 3 categories, got {len(categories)} — using defaults")

    return items, categories


# ── CSS — v7 ──────────────────────────────────────────────────────────────────

def checklist_css() -> str:
    return """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    @page {
        size: A4;
        margin: 1.25cm 1.5cm;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
        font-family: 'Inter', sans-serif;
        background: #fff;
        color: #1a1a2e;
        font-size: 12pt;
        line-height: 1.5;
    }

    .page {
        padding: 24px 28px;
        max-width: 7in;
        margin: 0 auto;
    }

    h1 {
        font-size: 22pt;
        font-weight: 700;
        color: #1a1a2e;
        border-bottom: 2.5px solid #1a1a2e;
        padding-bottom: 8pt;
        margin-bottom: 10pt;
        line-height: 1.25;
    }

    h2 {
        font-size: 9pt;
        font-weight: 400;
        color: #888;
        margin-bottom: 14pt;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .category-header {
        font-size: 10pt;
        font-weight: 700;
        color: #4ADE80;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 14pt 0 6pt 0;
        padding-bottom: 4pt;
        border-bottom: 1.5px solid #4ADE80;
    }

    .category-header:first-of-type {
        margin-top: 0;
    }

    ol.items {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    li.item {
        display: flex;
        align-items: flex-start;
        gap: 9px;
        margin-bottom: 8pt;
        font-size: 11.5pt;
        line-height: 1.45;
        color: #2d2d4a;
        padding: 4pt 0 4pt 0;
        border-bottom: 1px solid #f0f0f0;
    }

    li.item:last-child {
        border-bottom: none;
    }

    .cb {
        font-size: 13px;
        color: #4ADE80;
        flex-shrink: 0;
        line-height: 1.45;
        margin-top: 1pt;
    }

    .label {
        flex: 1;
    }

    .item-header {
        font-weight: 700;
        color: #1a1a2e;
    }

    .item-body {
        font-weight: 400;
        color: #555555;
    }

    .footer {
        margin-top: 14pt;
        padding-top: 9pt;
        border-top: 1px solid #e0e0e0;
        font-size: 8pt;
        color: #aaa;
        text-align: center;
    }
    """


def item_to_html(raw: str) -> str:
    """Parse: 'Bolded Header: Descriptive sentence.' → <li> with two spans."""
    raw = raw.strip()
    if ": " in raw:
        header, body = raw.split(": ", 1)
    else:
        header, body = raw, raw

    safe_header = html_mod.escape(header.strip())
    safe_body = html_mod.escape(body.strip())

    return (
        f'<li class="item">'
        f'<span class="cb">&#x2610;</span>'
        f'<span class="label">'
        f'<span class="item-header">{safe_header}:</span> '
        f'<span class="item-body">{safe_body}</span>'
        f'</span>'
        f'</li>\n'
    )


# ── Load trend data for context ─────────────────────────────────────────────

def load_trend_data(slug: str) -> dict | None:
    """Search recent trend files for matching slug and return trend data."""
    if not TRENDS_DIR.exists():
        return None
    for f in sorted(TRENDS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            for t in data.get("trends", []):
                cand = t.get("slug_candidate", "")
                if cand and (cand == slug or slug.startswith(cand)):
                    return t
                # Also try matching base slug (without _v{N})
                base = slug.rsplit("_v", 1)[0] if "_v" in slug else slug
                if cand == base:
                    return t
        except Exception:
            pass
    return None


# ── Title extraction from draft frontmatter ─────────────────────────────────

def extract_title_from_draft(slug: str) -> str:
    """Read frontmatter title from draft, or fallback to slug."""
    draft_path = DRAFTS_DIR / f"{slug}.md"
    if draft_path.exists():
        text = draft_path.read_text()
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 2:
                fm = parts[1]
                for line in fm.split("\n"):
                    if line.startswith("title:"):
                        return line.split(":", 1)[1].strip().strip('"\'')
    # Fallback from slug
    return slug.replace("-", " ").replace("_v1", "").replace("_v2", "").title()


# ── Main generation ──────────────────────────────────────────────────────────

def generate_checklist_pdf(slug: str, title_str: str,
                           items: list[str], categories: list[str]) -> str | None:
    """Generate PDF from items + categories for a given slug."""
    if not items:
        print(f"  No items for '{slug}' — skipping")
        return None

    checklist_path = OUTPUT_DIR / f"{slug}_CHECKLIST.pdf"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%B %d, %Y")

    # Chunk items into 3 groups of 4
    chunks = [items[i:i+4] for i in range(0, len(items), 4)]

    html_parts = []
    for chunk, cat_label in zip(chunks, categories):
        html_parts.append(f'<div class="category-header">{html_mod.escape(cat_label)}</div>')
        html_parts.append('<ol class="items">')
        for it in chunk:
            html_parts.append(item_to_html(it))
        html_parts.append('</ol>')

    checklist_rows = "".join(html_parts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>{checklist_css()}</style>
</head>
<body>
  <div class="page">
    <h1>{html_mod.escape(title_str)} — Action Checklist</h1>
    <h2>Print this page and keep it somewhere visible &nbsp;|&nbsp; Generated {date_str}</h2>
    {checklist_rows}
    <div class="footer">Companion to the full guide in your Lemon Squeezy library &mdash; check off each item as you complete it.</div>
  </div>
</body>
</html>"""

    try:
        import weasyprint
        wp_doc = weasyprint.HTML(string=html)
        wp_doc.write_pdf(str(checklist_path))
        size_kb = checklist_path.stat().st_size / 1024
        print(f"  ✅ {checklist_path.name} ({len(items)} items, {size_kb:.0f} KB)")
        return str(checklist_path)
    except Exception as e:
        print(f"  ❌ WeasyPrint failed: {e}")
        return None


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run(slugs: list[str] | None = None, force: bool = False) -> int:
    print("=" * 55)
    print("AI Agentic Checklist Synthesizer v7 (Dynamic)")
    print("=" * 55)

    try:
        cfg = load_config()
        creds = get_minimax_credentials(cfg)
        if not creds["api_key"]:
            print("  ERROR: No MiniMax API key")
            return 1
    except Exception as e:
        print(f"  ERROR: {e}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Discover slugs
    if slugs is None:
        slugs = get_active_slugs()

    if not slugs:
        print("  No active slugs found. Run TrendScout first or place drafts in products/drafts/")
        return 1

    print(f"  Active products: {slugs}")

    for slug in slugs:
        print(f"\n  [{slug}]")

        # Read draft
        draft_path = DRAFTS_DIR / f"{slug}.md"
        if not draft_path.exists():
            print(f"    ⚠️  No draft file: {draft_path.name} — skipping")
            continue

        draft_text = draft_path.read_text(encoding="utf-8")
        title = extract_title_from_draft(slug)

        # Check cache
        cached = None if force else load_cached_items(slug)
        if cached:
            items, categories = cached
            print(f"    📋 Loaded from cache ({len(items)} items)")
        else:
            # Load trend data for context
            trend_data = load_trend_data(slug)

            # Generate via AI
            print(f"    Generating checklist from draft content...")
            result = generate_checklist_items(creds, slug, draft_text, trend_data)
            if result is None:
                print(f"    ❌ Generation failed — skipping")
                continue

            items, categories = result
            save_cached_items(slug, items, categories)
            print(f"    ✅ Generated {len(items)} items in {len(categories)} categories")

        # Generate PDF
        generate_checklist_pdf(slug, title, items, categories)

    print(f"\n{'='*55}")
    return 0


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    slugs = args if args else None
    sys.exit(run(slugs=slugs, force=force))
