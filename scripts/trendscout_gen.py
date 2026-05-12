#!/usr/bin/env python3
"""
TrendScout Gen — Generate Skeletons + Drafts from JSON trends
============================================================
Reads wiki/trends/YYYY-MM-DD.json → generates skeletons + drafts
for HIGH CONVICTION trends via MiniMax-M2.7 API.

Usage:
    python3 scripts/trendscout_gen.py              # use today's JSON
    python3 scripts/trendscout_gen.py 2026-05-11  # specific date
"""
import json, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
TRENDS_DIR = WORKSPACE / "wiki" / "trends"
SKELETONS_DIR = WORKSPACE / "products" / "skeletons"
DRAFTS_DIR = WORKSPACE / "products" / "drafts"
ET = timezone(timedelta(hours=-4))


def load_config():
    with open(Path("/home/mathew/.openclaw/openclaw.json")) as f:
        return json.load(f)


def get_minimax_credentials(cfg):
    providers = cfg.get("models", {}).get("providers", {})
    minimax = providers.get("minimax", {})
    return {
        "base_url": minimax.get("baseUrl", "https://api.minimax.io/anthropic"),
        "api_key": minimax.get("apiKey", ""),
    }


def call_minimax(creds, system_prompt, user_prompt, max_tokens=4000):
    import urllib.request, urllib.error

    url = f"{creds['base_url']}/v1/messages"
    body = {
        "model": "MiniMax-M2.7",
        "max_tokens": max_tokens,
        "temperature": 0.8,
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


def slugify(title):
    text = title.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].strip("-")


def generate_skeleton(creds, trend):
    title = trend.get("product_direction", "Unknown").split(":")[0].strip()
    if not title:
        title = trend.get("audience", "Unknown Trend")

    score = trend.get("total_score", "?")
    quote = trend.get("raw_quote", "")[:300]
    trigger_text = trend.get("emotional_trigger", "")
    angle = trend.get("product_direction", "")

    system = """You write product skeletons for digital guides. Your voice is smart-casual,
empathetic, data-grounded, and 100% matte-finish. Never use AI-slop language ("game-changer",
"unlock", "journey"). Write like a sharp, warm colleague who's been through it. Use the
'Off Switch' skeleton format as reference: Emotional Hook, Problem Breakdown, Product
Architecture (Parts/Sections), Distribution Strategy, and Market Angle."""

    user = f"""Generate a Product Skeleton for this HIGH CONVICTION trend:

TREND: {title} (Frustration Score: {score}/10)
VERBATIM QUOTE: {quote}
EMOTIONAL TRIGGER: {trigger_text}
PRODUCT ANGLE: {angle}

FORMAT:
1. A compelling product title (40 chars max, curiosity-driven, not clickbait)
2. Emotional Hook section (200 words): Open with an adaptation of the quote, validate immediately, pivot to what the product will DO (not what it "teaches")
3. Product Architecture: 4 Parts, each with 3 chapters. Brief description of each.
4. Key Human Touch elements: What personal anecdotes or framing will land here
5. Format & Pricing: PDF/worksheets, price point rationale
6. Distribution: Where this lives and how it spreads
7. Market Intel angle: How this connects to "human infrastructure" investment thesis

Length: ~800 words. Markdown."""

    return call_minimax(creds, system, user, max_tokens=3000)


def generate_draft(creds, trend, skeleton_text):
    title = trend.get("product_direction", "Unknown").split(":")[0].strip()

    system = """You write full-length digital guide drafts. Voice: smart-casual, warm,
empathetic, data-grounded. Zero AI-slop. Write like someone who's lived this, not
someone who researched it. Use contractions, occasional humor, and direct address.
Structure with clear H2/H3 headings. Bold Key Takeaways after major sections.
Weave in the "human infrastructure" thesis subtly — managing personal energy and
household systems IS infrastructure, just at human scale.

Target length: 2500-4000 words per section. Write ALL sections as COMPLETE,
production-ready chapters. No "Coming in V2" or outline-only language."""

    user = f"""Using this skeleton as the foundation, write Parts 1 and 2 of the full
guide draft. Expand every bullet into real prose. Follow the 'Off Switch' draft format
at /home/mathew/.openclaw/workspace/products/drafts/off_switch_V1.md as reference.

SKELETON:
{skeleton_text[:3000]}

Write in markdown. Include:
- A strong introduction that hooks emotionally
- Part 1 and Part 2 as complete chapters with actionable content
- Bolded Key Takeaways after major sections
- A "Capital Pilot Interstitial" section connecting to human infrastructure thesis
- Parts 3-4 as brief outlines

The trend driving this: {title}"""

    return call_minimax(creds, system, user, max_tokens=8000)


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else datetime.now(ET).strftime("%Y-%m-%d")
    print(f"[{datetime.now(ET).strftime('%H:%M:%S ET')}] TrendScout Gen — {date_arg}")
    print("=" * 60)

    try:
        cfg = load_config()
        creds = get_minimax_credentials(cfg)
        if not creds["api_key"]:
            print("  ERROR: No MiniMax API key")
            return 1
    except Exception as e:
        print(f"  ERROR: {e}")
        return 1

    trends_file = TRENDS_DIR / f"{date_arg}.json"
    if not trends_file.exists():
        print(f"  ERROR: No trends file: {trends_file}")
        return 1

    data = json.loads(trends_file.read_text())
    trends = data.get("trends", [])
    if not trends:
        print("  ERROR: No trends in file")
        return 1

    # Filter to HIGH CONVICTION
    high_trends = [t for t in trends if t.get("ai_conviction") == "HIGH CONVICTION"]
    if not high_trends:
        print("  No HIGH CONVICTION trends — check scoring")
        return 0

    print(f"  Found {len(high_trends)} HIGH CONVICTION trends")

    SKELETONS_DIR.mkdir(parents=True, exist_ok=True)
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    # Check which slugs already have skeletons/drafts
    existing_skeletons = {f.stem.replace("_SKELETON", ""): f
                          for f in SKELETONS_DIR.glob("*_SKELETON.md")}
    existing_drafts = {re.sub(r"_V\d+.*", "", f.stem): f
                       for f in DRAFTS_DIR.glob("*.md")}

    results = []

    for i, trend in enumerate(high_trends, 1):
        title = trend.get("product_direction", "").split(":")[0].strip()
        if not title:
            title = trend.get("audience", f"trend-{i}")
        slug = slugify(title)

        print(f"\n[{i}/{len(high_trends)}] {title[:60]}")
        print(f"    Slug: {slug}")

        # Skip if already drafted (trend-level dedup)
        if slug in existing_drafts:
            print(f"    Skipping — draft already exists: {existing_drafts[slug].name}")
            continue

        # Stage 2: Generate Skeleton
        if slug in existing_skeletons:
            print(f"    Using existing skeleton: {existing_skeletons[slug].name}")
            skeleton_text = existing_skeletons[slug].read_text()
        else:
            print(f"    Generating skeleton...")
            skeleton_text = generate_skeleton(creds, trend)
            if not skeleton_text:
                print(f"    Skeleton FAILED — skipping trend")
                continue
            skel_path = SKELETONS_DIR / f"{slug}_SKELETON.md"
            skel_path.write_text(skeleton_text)
            print(f"    Skeleton saved: {skel_path.name}")

        # Stage 3: Generate Draft
        print(f"    Generating draft...")
        draft_text = generate_draft(creds, trend, skeleton_text)
        if not draft_text:
            print(f"    Draft FAILED")
            continue

        # Write with trend metadata frontmatter
        draft_full = f"""---
title: "{title}"
trend: "{trend.get('product_direction', '')}"
emotional_trigger: "{trend.get('emotional_trigger', '')}"
score: {trend.get('total_score', '?')}/10
ai_conviction: {trend.get('ai_conviction', 'MEDIUM')}
source: {trend.get('source_platform', 'reddit')}
---

{draft_text}
"""

        draft_path = DRAFTS_DIR / f"{slug}.md"
        draft_path.write_text(draft_full)
        print(f"    Draft saved: {draft_path.name}")
        results.append((trend, str(draft_path)))

    print(f"\n{'='*60}")
    print(f"  COMPLETE — {len(results)} drafts created")
    for trend, path in results:
        title = trend.get("product_direction", "").split(":")[0].strip()
        print(f"  • {title} → {path}")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
