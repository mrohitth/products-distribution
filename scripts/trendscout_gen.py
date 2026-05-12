#!/usr/bin/env python3
"""
TrendScout Gen — Generate Skeletons + Full Drafts from JSON trends
===================================================================
Reads wiki/trends/YYYY-MM-DD.json → generates skeletons + full 4-part draft
for HIGH CONVICTION trends via MiniMax-M2.7 API.

Changes from v1:
  - All 4 parts generated as COMPLETE chapters (no outlines)
  - No reference to non-existent off_switch_V1.md
  - Consistent slug versioning with trendscout_scout.py (same normalize_slug)
  - Reads `slug_candidate` from trend JSON (already versioned by scout)
  - Parallel processing: max 2 concurrent MiniMax calls (ThreadPoolExecutor)

Usage:
    python3 scripts/trendscout_gen.py              # use today's JSON
    python3 scripts/trendscout_gen.py 2026-05-11  # specific date
"""
import json, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
TRENDS_DIR = WORKSPACE / "wiki" / "trends"
SKELETONS_DIR = WORKSPACE / "products" / "skeletons"
DRAFTS_DIR = WORKSPACE / "products" / "drafts"
ET = timezone(timedelta(hours=-4))


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


def call_minimax(creds: dict, system_prompt: str, user_prompt: str, max_tokens: int = 8000) -> str | None:
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
        with urllib.request.urlopen(req, timeout=1800) as resp:
            data = json.loads(resp.read())
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
            return ""
    except Exception as e:
        print(f"  API error: {e}")
        return None


def normalize_slug(base: str) -> str:
    """Consistent slugification — same as trendscout_scout.py."""
    text = base.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].strip("-")


# ── Stage 2: Generate Skeleton ──────────────────────────────────────────────────

SKELETON_SYSTEM = """You write product skeletons for digital guides. Your voice is smart-casual,
empathetic, data-grounded, and 100% matte-finish. Never use AI-slop language ("game-changer",
"unlock", "journey"). Write like a sharp, warm colleague who's been through it.

Format:
1. Product Title (40 chars max, curiosity-driven, not clickbait)
2. Emotional Hook (200 words): Open with an adaptation of the user's pain, validate it immediately, pivot to what the product WILL do
3. Product Architecture: 4 Parts, each with 3 chapters. Each chapter is a real actionable thing the reader will learn to do.
4. Key Human Touch elements: What personal anecdotes or framing will land here
5. Format & Pricing: PDF/worksheets, price point rationale
6. Market Intel angle: How this connects to broader life infrastructure thesis

Each chapter must be described with concrete outputs — what the reader will BE ABLE TO DO after reading. No vague promises."""


def generate_skeleton(creds: dict, trend: dict) -> str | None:
    title = trend.get("product_direction", "Unknown").split(":")[0].strip()
    if not title:
        title = trend.get("audience", "Unknown Trend")

    score = trend.get("total_score", "?")
    quote = trend.get("raw_quote", "")[:400]
    trigger_text = trend.get("emotional_trigger", "")
    angle = trend.get("product_direction", "")
    audience = trend.get("audience", "")

    user = f"""Generate a Product Skeleton for this HIGH CONVICTION trend:

TREND: {title} (Score: {score}/12)
VERBATIM QUOTE: {quote}
EMOTIONAL TRIGGER: {trigger_text}
PRODUCT ANGLE: {angle}
TARGET AUDIENCE: {audience}

Every part must have concrete, actionable chapters — not "coming in V2" or "discussed later."
All 4 parts must be fully described."""

    return call_minimax(creds, SKELETON_SYSTEM, user, max_tokens=3000)


# ── Stage 3: Generate Full Draft (ALL 4 Parts) ──────────────────────────────────

DRAFT_SYSTEM = """You write full-length digital guide drafts. Your voice is smart-casual, warm,
empathetic, and data-grounded. Zero AI-slop. Write like someone who has lived this,
not someone who researched it. Use contractions, occasional humor, and direct address.

Structure with clear H2/H3 headings. After each major section, add a bolded Key Takeaway.
Weave in the "human infrastructure" thesis subtly — managing personal energy and
household systems IS infrastructure, just at human scale.

CRITICAL: You MUST write ALL 4 parts as COMPLETE, production-ready chapters.
Every chapter must include actionable steps the reader can actually take.
No outlines, no "Full version coming soon," no placeholders, no "in V2."
Each chapter is 500-1200 words of real actionable content.

Total target: 10-15 pages of content."""


def generate_draft(creds: dict, trend: dict, skeleton_text: str) -> str | None:
    title = trend.get("product_direction", "Unknown").split(":")[0].strip()
    quote = trend.get("raw_quote", "")[:300]
    audience = trend.get("audience", "")
    trigger = trend.get("emotional_trigger", "")
    score = trend.get("total_score", "?")
    angle = trend.get("product_direction", "")

    user = f"""Using this skeleton as the foundation, write the COMPLETE 4-PART guide draft.

SKELETON:
{skeleton_text[:4000]}

CONTEXT:
- Trend title: {title}
- Audience: {audience}
- Pain trigger: {trigger}
- Score: {score}/12
- Product angle: {angle}
- Quote: {quote}

REQUIREMENTS:
1. ALL 4 parts must be FULLY WRITTEN — no outlines, no "full version soon"
2. Each part is ~2000-4000 words with clear subheadings
3. Every chapter must have actionable steps — things the reader can DO today
4. Start with a strong Introduction that hooks emotionally + explains what the guide solves
5. End with a Conclusion that summarizes + includes:
   - A clear call to action (next step for the reader)
   - Signposting that this pairs with the Action Checklist (the companion PDF)
6. Bold Key Takeaways after each part
7. No placeholder text, no AI-slop, no "game-changer" or "unlock your potential" language

Write a complete, production-ready guide. This is the final product."""

    return call_minimax(creds, DRAFT_SYSTEM, user, max_tokens=100000)


# ── Main (Parallel) ──────────────────────────────────────────────────────────────

def process_one_trend(creds: dict, trend: dict, date_arg: str) -> tuple[dict, str | None]:
    """Process a single trend: skeleton -> draft. Returns (trend, draft_path) or (trend, None)."""
    slug = trend.get("slug_candidate", "")
    if not slug:
        return (trend, None)

    title = trend.get("product_direction", "").split(":")[0].strip()
    if not title:
        title = slug.replace("-", " ").title()

    print(f"  {title[:60]} -> {slug}")

    draft_path = DRAFTS_DIR / f"{slug}.md"
    skel_path = SKELETONS_DIR / f"{slug}_SKELETON.md"

    if draft_path.exists():
        print(f"    Skipping -- draft exists")
        return (trend, str(draft_path))

    # Stage 2: Skeleton
    if skel_path.exists():
        skeleton_text = skel_path.read_text()
        print(f"    Skeleton: cached")
    else:
        print(f"    Skeleton: generating...")
        skeleton_text = generate_skeleton(creds, trend)
        if not skeleton_text:
            print(f"    Skeleton FAILED")
            return (trend, None)
        skel_path.write_text(skeleton_text)

    # Stage 3: Draft
    print(f"    Draft: generating...")
    draft_text = generate_draft(creds, trend, skeleton_text)
    if not draft_text:
        print(f"    Draft FAILED")
        return (trend, None)

    draft_full = f"""---
title: "{title}"
slug: "{slug}"
trend: "{trend.get('product_direction', '')}"
audience: "{trend.get('audience', '')}"
emotional_trigger: "{trend.get('emotional_trigger', '')}"
score: {trend.get('total_score', '?')}/12
ai_conviction: {trend.get('ai_conviction', 'MEDIUM')}
date: {date_arg}
source_platform: {trend.get('source_platform', 'reddit')}
---

{draft_text}
"""

    draft_path.write_text(draft_full)
    print(f"    Draft: saved -> {draft_path.name}")
    return (trend, str(draft_path))


def main() -> int:
    date_arg = sys.argv[1] if len(sys.argv) > 1 else datetime.now(ET).strftime("%Y-%m-%d")
    print(f"[{datetime.now(ET).strftime('%H:%M:%S ET')}] TrendScout Gen -- {date_arg}")
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

    print(f"  Found {len(trends)} trends to process")
    SKELETONS_DIR.mkdir(parents=True, exist_ok=True)
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    print(f"  Processing (max 2 concurrent MiniMax calls)...")
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(process_one_trend, creds, t, date_arg): t for t in trends}
        for fut in as_completed(futures):
            trend, draft_path = fut.result()
            if draft_path:
                results.append((trend, draft_path))
                print(f"  + {Path(draft_path).stem}")

    print(f"\n{'='*60}")
    print(f"  COMPLETE -- {len(results)} drafts created")
    for trend, path in results:
        title = trend.get("product_direction", "").split(":")[0].strip()
        slug = trend.get("slug_candidate", "?")
        print(f"  * {title} ({slug}) -> {path}")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
