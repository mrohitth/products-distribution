#!/usr/bin/env python3
"""
Content Repurposing Engine — Distribution Flywheel Layer 2
==========================================================
Takes a product draft and generates multi-platform content:
- Reddit posts (1 per product per week)
- Pinterest pins (batch of 30 per product)
- TikTok/Reels scripts (3 per product per week)
- LinkedIn carousels (2 per product per week)
- Email lead magnet (free checklist → email capture)

All generation uses MiniMax M2.7 API at near-zero marginal cost.
Output: distro/content/{product_slug}/{platform}/

Usage:
  python3 distro/content_engine.py generate <product_slug>
  python3 distro/content_engine.py status
"""
import json, os, sys, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
import http.client
import hashlib

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
CONFIG_PATH = Path("/home/mathew/.openclaw/openclaw.json")
OUT_DIR = WORKSPACE / "distro" / "content"
EMAIL_DIR = WORKSPACE / "distro" / "email"

ET = timezone(timedelta(hours=-4))


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_minimax_creds(cfg):
    providers = cfg.get("models", {}).get("providers", {})
    minimax = providers.get("minimax", {})
    return {
        "base_url": minimax.get("baseUrl", "https://api.minimax.io/anthropic"),
        "api_key": minimax.get("apiKey", ""),
    }


def mm_completion(creds, prompt, system="You are a world-class content creator.", max_tokens=800):
    """Call MiniMax M2.7 API with a prompt. Returns text."""
    if not creds["api_key"]:
        print("ERROR: No MiniMax API key found in config")
        return None

    headers = {
        "Authorization": f"Bearer {creds['api_key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "MiniMax-M2.7",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "thinking": {"type": "off"},
    }

    conn = http.client.HTTPSConnection("api.minimax.io", timeout=60)
    try:
        conn.request("POST", "/v1/chat/completions", json.dumps(payload), headers)
        resp = conn.getresponse()
        data = json.loads(resp.read().decode())
        if "error" in data:
            print(f"API error: {data['error']}")
            return None
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Request failed: {e}")
        return None
    finally:
        conn.close()


SLUG_TO_DRAFT = {
    "you-first-for-once": "off_switch_V1.md",
    "first-30-days-cat-crisis": "first_30_days_cat_crisis_V1.md",
    "single-parent-teen-burnout": "single_parent_teen_burnout_V1.md",
    "ragdoll-first-month": "ragdoll-first-month_FINAL.md",
}


def load_product_draft(slug):
    """Find and load the draft file for a product slug."""
    drafts_dir = WORKSPACE / "products" / "drafts"
    # Direct mapping first
    if slug in SLUG_TO_DRAFT:
        f = drafts_dir / SLUG_TO_DRAFT[slug]
        if f.exists():
            return f.read_text()
    # Fuzzy match: look for slug string in filename
    for f in drafts_dir.glob("*.md"):
        if slug.lower().replace("-", "_") in f.name.lower():
            return f.read_text()
    return None


# ─── Content Generators ────────────────────────────────────────────────────────

def generate_reddit_post(creds, product_name, product_copy, category):
    """Generate 2 Reddit posts: one Reddit-style story + one educational post."""
    system = """You are a Reddit copywriter. You write like a real human Redditor — casual, self-aware, not promotional. 
No hashtags. No emoji except sparingly. First person voice only. End with a question to drive comments."""

    prompt = f"""Product: {product_name}
Category: {category}
Product summary: {product_copy[:500]}

Generate 2 Reddit posts:

## POST 1 — "Relatable Story" format (for r/Parenting or similar)
Write a first-person Reddit post that opens with a relatable struggle, shows vulnerability, and naturally hints at the solution without selling. 200-400 words. Tone: self-deprecating, honest, warm.

## POST 2 — "Help Me Figure This Out" format (for r/{category} or similar)  
Write a Reddit post that poses a genuine question/struggle, shares context, and invites people to share their experience. 150-250 words. Tone: curious, not preachy.

Format output as:
===REDDIT_POST_1===
[content]
===REDDIT_POST_2===
[content]
"""
    return mm_completion(creds, prompt, system, max_tokens=1200)


def generate_pinterest_pins(creds, product_name, product_copy, category, count=30):
    """Generate batch of Pinterest pins as markdown list."""
    system = """You are a Pinterest content strategist. You write in Pinterest style: 
- Bold hooks in caps
- Short punchy bullets  
- Emojis used purposefully (1-3 per pin)
- Hook + value proposition + CTA structure
- Each pin must feel distinct, not templated

Pin format per item:
PIN | Headline | Description (2 sentences) | Board category"""

    prompt = f"""Product: {product_name} ({category})
Product copy: {product_copy[:600]}

Generate {count} distinct Pinterest pins. Each pin must have a different angle, headline style, and description. Mix of:
- How-to pins (tutorial style)
- Relatable pins (emotional hook)
- List pins (X things...)
- Quote pins (motivation/identity)
- Checklist pins (free resource angle)

For each pin write:
PIN | HEADLINE (max 60 chars) | Description (max 200 chars) | Board category

Return as a markdown list, one pin per line starting with "- "."""

    result = mm_completion(creds, prompt, system, max_tokens=1500)
    return result if result else ""


def generate_tiktok_scripts(creds, product_name, product_copy, category, count=3):
    """Generate TikTok/Reels video scripts."""
    system = """You are a TikTok script writer. Write short, punchy video scripts that feel like talking to a friend.
Hook in the first 3 seconds. Practical value in the middle. Soft CTA at end.
Format: [HOOK] / [BODY] / [CTA]
Each script = 45-60 second read-aloud."""

    prompt = f"""Product: {product_name} ({category})
Product copy: {product_copy[:500]}

Write {count} TikTok/Reels scripts. Each should:
- Open with a pattern interrupt (question, bold statement, or relatable situation)
- Deliver 1 core insight or tip in 30 seconds
- Close with a soft CTA (follow for more, link in bio, comment your experience)

Format each script as:
---SCRIPT 1---
[HOOK - 3 seconds]
[BODY - 45 seconds]
[CTA]

Return {count} scripts."""

    result = mm_completion(creds, prompt, system, max_tokens=1200)
    return result if result else ""


def generate_linkedin_carousels(creds, product_name, product_copy, category, count=2):
    """Generate LinkedIn carousel posts."""
    system = """You are a LinkedIn content writer. Write professional but human carousel copy.
Tone: thoughtful leader, shares hard-won insights, no humble brags.
Format: Slide number + headline + 2-3 bullet points per slide.
Carousel: 5-8 slides total per post."""

    prompt = f"""Product: {product_name} ({category})
Product copy: {product_copy[:600]}

Write {count} LinkedIn carousel posts. Each carousel:
- Slide 1: Hook headline (question or bold statement)
- Slides 2-6: Value slides (practical insights or framework)
- Final slide: CTA (comment, share, or link)

Each slide format:
[SILDE n] HEADLINE
- Bullet 1
- Bullet 2

Return {count} complete carousel structures."""

    result = mm_completion(creds, prompt, system, max_tokens=1200)
    return result if result else ""


def generate_email_lead_magnet(creds, product_name, product_copy, category):
    """Generate a free checklist lead magnet that feeds into the sales funnel."""
    system = """You are an email marketing strategist. You write lead magnets that are genuinely useful AND pre-sell naturally.
Free checklist format: 10-15 actionable items, no fluff, immediately usable.
The checklist solves a specific pain point and ends with a soft pitch to the full product."""

    prompt = f"""Product: {product_name}
Category: {category}
Product copy: {product_copy[:600]}

Write a FREE CHECKLIST lead magnet (10-15 items) that:
1. Solves a specific, immediate problem the reader faces
2. Is immediately actionable (can start today)
3. Demonstrates the same expertise/approach as the full product
4. Ends with a natural bridge to the full guide ("if you want the full system, link to product")

Format:
# [Product Name] — Quick-Start Checklist
## Section 1: [Theme]
- [Actionable item]
[repeat 10-15 items total across 2-3 sections]

## Want the Full System?
[1-2 sentence pitch for the paid product with link placeholder]

Output as markdown. Keep copy tight and credible."""

    result = mm_completion(creds, prompt, system, max_tokens=1000)
    return result if result else ""


def generate_email_sequence(creds, product_name, product_copy, category):
    """Generate 5-email welcome sequence for new subscribers."""
    system = """You are an email sequence writer. Conversational, warm, respects the reader's time.
Each email should be 150-250 words. Natural prose, not bullet-heavy.
Email 1: Welcome + deliver the lead magnet
Email 2: Value-add (related tip or insight)
Email 3: Social proof + story
Email 4: Soft product mention
Email 5: Clear call to action + unsubscribe friendly"""

    prompt = f"""Product: {product_name}
Category: {category}
Product copy: {product_copy[:600]}

Write a 5-email welcome sequence for new subscribers who downloaded the free checklist.

Email 1 (Day 0 — immediate): Welcome, deliver the checklist, set expectations (3 emails in next week)
Email 2 (Day 2): Share the most impactful tip from the checklist topic — go deeper
Email 3 (Day 4): Share a short testimonial or success story (use a composite/imagined one if none exist)
Email 4 (Day 6): Naturally mention the full product — what problem it solves, who it's for
Email 5 (Day 8): Clear CTA to buy + mention the $27 price point

Subject line format: [EMAIL SUBJECT]
Body format: plain text markdown, conversational

Output as:
---EMAIL 1---
Subject: [subject]
Body: [content]
---EMAIL 2---
[etc]"""

    result = mm_completion(creds, prompt, system, max_tokens=2000)
    return result if result else ""


# ─── Main Dispatch ─────────────────────────────────────────────────────────────

def generate_all(slug):
    """Generate all content for a product slug."""
    print(f"[DISTRO] Generating content for: {slug}")

    draft = load_product_draft(slug)
    if not draft:
        print(f"ERROR: No draft found for slug '{slug}'")
        return

    # Extract product name and category from draft
    lines = draft.split("\n")
    product_name = slug.replace("_", " ").replace("-", " ").title()
    category = "self-help"
    product_copy = draft[:1000]

    # Detect category
    for kw in ["single parent", "parenting", "teen"]:
        if kw in draft.lower():
            category = "parenting"
    for kw in ["cat", "kitten", "pet"]:
        if kw in draft.lower():
            category = "petcare"

    # Load MiniMax credentials
    cfg = load_config()
    creds = get_minimax_creds(cfg)
    if not creds["api_key"]:
        print("ERROR: No MiniMax API key")
        return

    output_dir = OUT_DIR / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    generators = [
        ("reddit", generate_reddit_post),
        ("pinterest", lambda creds, n, c, g: generate_pinterest_pins(creds, n, c, g, count=30)),
        ("tiktok", generate_tiktok_scripts),
        ("linkedin", generate_linkedin_carousels),
    ]

    for platform, gen_fn in generators:
        print(f"  Generating {platform}...")
        content = gen_fn(creds, product_name, product_copy, category)
        if content:
            (output_dir / f"{platform}_posts.md").write_text(content)
            print(f"    ✓ {platform} → {output_dir / f'{platform}_posts.md'}")

    # Email funnel
    print("  Generating email funnel...")
    lead_magnet = generate_email_lead_magnet(creds, product_name, product_copy, category)
    if lead_magnet:
        (EMAIL_DIR / f"{slug}_lead_magnet.md").write_text(lead_magnet)
        print(f"    ✓ lead_magnet → {EMAIL_DIR / f'{slug}_lead_magnet.md'}")

    email_seq = generate_email_sequence(creds, product_name, product_copy, category)
    if email_seq:
        (EMAIL_DIR / f"{slug}_email_sequence.md").write_text(email_seq)
        print(f"    ✓ email_sequence → {EMAIL_DIR / f'{slug}_email_sequence.md'}")

    print(f"\n[✓] All content generated for '{slug}'")
    print(f"    Output: {output_dir}")


def status():
    """Show content generation status for all products."""
    print("\n=== DISTRO CONTENT STATUS ===")
    if not OUT_DIR.exists():
        print("No content generated yet.")
        return

    for product_dir in sorted(OUT_DIR.iterdir()):
        if product_dir.is_dir():
            print(f"\n  📦 {product_dir.name}")
            for f in sorted(product_dir.iterdir()):
                lines = len(f.read_text().split("\n")) if f.exists() else 0
                print(f"    {f.name} ({lines} lines)")

    email_files = list(EMAIL_DIR.glob("*")) if EMAIL_DIR.exists() else []
    if email_files:
        print(f"\n  📧 Email Funnel")
        for f in email_files:
            print(f"    {f.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "generate" and len(sys.argv) >= 3:
        generate_all(sys.argv[2])
    elif cmd == "status":
        status()
    else:
        print(__doc__)