#!/usr/bin/env python3
"""
generate_distribution.py — Stage 4 Distribution Generator
===========================================================
Generates Reddit value-first posts + Pinterest pins from draft + trend data.
Supports the full v2.1 "Reddit Bridge" and "Pinterest Solution Pin" spec.

Usage:
    python3 scripts/generate_distribution.py                          # all active slugs
    python3 scripts/generate_distribution.py cat-litter-box-rescue-guide_v1  # specific slug
    python3 scripts/generate_distribution.py --force                  # force regenerate
"""
import json, sys, re, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
DRAFTS_DIR = WORKSPACE / "products" / "drafts"
DIST_DIR = WORKSPACE / "products" / "distribution"
TRENDS_DIR = WORKSPACE / "wiki" / "trends"
CACHE_DIR = WORKSPACE / "products" / ".checklist_cache"
OUTPUT_DIR = WORKSPACE / "output" / "final_products"
ET = timezone(timedelta(hours=-4))


# ── Config ───────────────────────────────────────────────────────────────────────

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


def call_minimax(creds: dict, system: str, user: str, max_tokens: int = 3000, temp: float = 0.6) -> str | None:
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
            return None
    except Exception as e:
        print(f"  API error: {e}")
        return None


# ── Slug Discovery ──────────────────────────────────────────────────────────────

def get_active_slugs() -> list[str]:
    """Find all draft slugs that need distribution files."""
    today = datetime.now(ET).strftime("%Y-%m-%d")
    trends_file = TRENDS_DIR / f"{today}.json"
    slugs = []

    # First from today's trends
    if trends_file.exists():
        data = json.loads(trends_file.read_text())
        for t in data.get("trends", []):
            slug = t.get("slug_candidate", "")
            if slug and (DRAFTS_DIR / f"{slug}.md").exists():
                slugs.append(slug)

    if not slugs:
        # Fallback: all drafts
        if DRAFTS_DIR.exists():
            for f in DRAFTS_DIR.glob("*.md"):
                if "_SKELETON" not in f.stem:
                    slugs.append(f.stem)
    return slugs


# ── Trend Data Loader ───────────────────────────────────────────────────────────

def load_trend_data(slug: str) -> dict | None:
    """Search recent trend files for matching slug."""
    if not TRENDS_DIR.exists():
        return None
    for f in sorted(TRENDS_DIR.glob("*.json"), reverse=True)[:14]:
        try:
            data = json.loads(f.read_text())
            for t in data.get("trends", []):
                cand = t.get("slug_candidate", "")
                if cand and (cand == slug or slug.startswith(cand)):
                    return t
                base = slug.rsplit("_v", 1)[0] if "_v" in slug else slug
                if cand == base:
                    return t
        except Exception:
            pass
    return None


# ── Reddit Hook Generator ──────────────────────────────────────────────────────

REDDIT_SYSTEM = """You write value-first Reddit community posts. Your voice is smart-casual,
warm, and genuinely helpful — not marketing. You sound like someone who has been through
the exact same problem and wants to share what worked.

Rules:
- Start by validating the OP's frustration. They're not stupid. The problem is genuinely hard.
- Share 2-3 specific, actionable pieces of advice drawn DIRECTLY from the guide's content
- Mention the free checklist as a resource, not the main point: "I found a checklist that walked me through the exact sequence — happy to share if it helps"
- End with a warm, encouraging close — not a sales pitch
- Length: 150-250 words (Reddit comment length)
- NO links to Lemon Squeezy or store
- NO "DM me" or "check my profile" — just genuine value
- Use the exact quote from the OP if provided
- Write in first person ("I went through this too")"""


def generate_reddit_hook(creds: dict, slug: str, draft_text: str, trend: dict | None) -> str | None:
    """Generate a Reddit value-first post."""
    quote = ""
    audience = ""
    direction = ""
    if trend:
        quote = trend.get("raw_quote", "")[:400]
        audience = trend.get("audience", "")
        direction = trend.get("product_direction", "")[:100]

    # Strip frontmatter
    body = draft_text
    if body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()

    # Get key excerpts — intro + first actionable section
    body_excerpt = body[:4000]

    user = f"""Write a Reddit value-first post for this product.

PRODUCT SLUG: {slug}
AUDIENCE: {audience}
PRODUCT ANGLE: {direction}
{('ORIGINAL POST QUOTE: ' + quote) if quote else ''}

GUIDE EXCERPT:
{body_excerpt[:3000]}

Write a helpful Reddit comment that:
1. Validates the OP's frustration
2. Gives 2-3 specific pieces of advice from the guide
3. Mentions the free checklist naturally
4. Ends with encouragement

Length: 150-250 words. First-person voice. No hard selling."""

    return call_minimax(creds, REDDIT_SYSTEM, user, max_tokens=1500)


# ── Pinterest Pin Generator ─────────────────────────────────────────────────────

PINTEREST_SYSTEM = """You write SEO-optimized Pinterest pins. Write keyword-rich, specific,
and curiosity-driven. Pin titles must be questions or pain-point-first: "New Cat Crying at
Night? Here's What Actually Works."

Rules:
- Pin Title (Primary): 40-60 chars, question or pain-point-first
- Pin Title (Alt): 40-60 chars, different angle
- Description: 300-500 chars, keyword-rich but natural, includes what the reader will learn
- Board Placement: 1 primary + 2 secondary boards
- Metadata: keywords relevant to the target audience
- CTA: Short and natural ("Free Checklist in Bio" or similar)
- NO markdown formatting in descriptions
- NO AI-slop ("journey", "unlock", "transform")"""


def generate_pinterest_pin(creds: dict, slug: str, draft_text: str, trend: dict | None) -> str | None:
    """Generate a Pinterest solution pin."""
    direction = ""
    if trend:
        direction = trend.get("product_direction", "")[:100]

    body = draft_text
    if body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()

    body_excerpt = body[:3000]

    user = f"""Generate a Pinterest solution pin for this product.

PRODUCT: {slug}
{direction}

GUIDE CONTENT:
{body_excerpt[:2500]}

OUTPUT FORMAT:

## Pin Title (Primary)
[40-60 chars, pain-point question]

## Pin Title (Alt for testing)
[40-60 chars, different angle]

## Description (keyword-rich)
[300-500 chars, what the reader will learn, problem it solves]

## Board Placement
- Primary Board: [board name]
- Secondary boards: [2 board names]

## Pin Metadata
- Topic: [comma-separated keywords]
- Audience intent: [who needs this]
- Search priority keywords: [comma-separated]

## Call-to-Action Text on Pin
[short CTA]

## Notes
[visual recommendations, content notes]

Write plain markdown with the headings shown above."""

    return call_minimax(creds, PINTEREST_SYSTEM, user, max_tokens=2000, temp=0.7)


# ── Save Distribution Files ────────────────────────────────────────────────────

def save_distribution(slug: str, reddit_text: str, pinterest_text: str) -> tuple[str, str]:
    """Save both distribution files. Returns (reddit_path, pinterest_path)."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    reddit_path = DIST_DIR / f"{slug}_reddit_hook.md"
    reddit_path.write_text(reddit_text)
    print(f"    ✅ Reddit hook saved: {reddit_path.name} ({len(reddit_text.split())} words)")

    pinterest_path = DIST_DIR / f"{slug}_pinterest_pin.md"
    pinterest_path.write_text(pinterest_text)
    print(f"    ✅ Pinterest pin saved: {pinterest_path.name} ({len(pinterest_text.split())} words)")

    return str(reddit_path), str(pinterest_path)


# ── Cache System ───────────────────────────────────────────────────────────────

def get_draft_hash(slug: str) -> str:
    draft_path = DRAFTS_DIR / f"{slug}.md"
    if not draft_path.exists():
        return ""
    return hashlib.md5(draft_path.read_bytes()).hexdigest()


def distribution_needs_regeneration(slug: str) -> bool:
    """Check if distribution files need regeneration (draft changed or not generated yet)."""
    reddit_path = DIST_DIR / f"{slug}_reddit_hook.md"
    pinterest_path = DIST_DIR / f"{slug}_pinterest_pin.md"

    if not reddit_path.exists() or not pinterest_path.exists():
        return True

    # Check if draft hash changed
    cache_path = CACHE_DIR / f"{slug}_distro.json"
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
            if cache.get("draft_hash") == get_draft_hash(slug):
                return False
        except Exception:
            pass
    return True


def save_distro_cache(slug: str) -> None:
    cache_path = CACHE_DIR / f"{slug}_distro.json"
    cache_path.write_text(json.dumps({
        "slug": slug,
        "draft_hash": get_draft_hash(slug),
        "generated_at": datetime.now(ET).isoformat(),
    }))


# ─── Main ──────────────────────────────────────────────────────────────────────

def run(slugs: list[str] | None = None, force: bool = False) -> int:
    print("=" * 55)
    print("Distribution Generator — Reddit Bridge + Pinterest Pin")
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

    # Discover slugs
    if slugs is None:
        slugs = get_active_slugs()

    if not slugs:
        print("  No active slugs found.")
        return 0

    print(f"  Products to generate: {slugs}")

    results = []
    def process_one_slug(slug: str) -> None:
        draft_path = DRAFTS_DIR / f"{slug}.md"
        if not draft_path.exists():
            print(f"  [{slug}] No draft file -- skipping")
            return
        if not force and not distribution_needs_regeneration(slug):
            print(f"  [{slug}] Up to date")
            return
        draft_text = draft_path.read_text(encoding="utf-8")
        trend = load_trend_data(slug)
        reddit_text = generate_reddit_hook(creds, slug, draft_text, trend)
        if not reddit_text:
            print(f"  [{slug}] Reddit hook failed")
            return
        pinterest_text = generate_pinterest_pin(creds, slug, draft_text, trend)
        if not pinterest_text:
            print(f"  [{slug}] Pinterest pin failed")
            return
        save_distribution(slug, reddit_text, pinterest_text)
        save_distro_cache(slug)
        print(f"  [{slug}] Done")

    print(f"  Processing {len(slugs)} products (max 2 concurrent)...")
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(process_one_slug, s): s for s in slugs}
        for fut in as_completed(futures):
            pass


    print(f"\n{'='*55}")
    print(f"  COMPLETE — {len(results)} products distributed")
    for slug, rp, pp in results:
        print(f"  • {slug}")
        print(f"    Reddit: {Path(rp).name}")
        print(f"    Pinterest: {Path(pp).name}")
    print(f"{'='*55}")
    return 0


if __name__ == "__main__":
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    slugs = args if args else None
    sys.exit(run(slugs=slugs, force=force))
