#!/usr/bin/env python3
"""
Regenerate archive _v1.md drafts into full production-ready guides
using the improved DRAFT_SYSTEM prompt (anti-AI-slop).

Usage: python3 scripts/regenerate_archive_drafts.py
"""
import json
import sys
from pathlib import Path

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
DRAFTS_DIR = WORKSPACE / "products" / "drafts"

MINIMAX_API_KEY = "sk-cp-QO5w66jViy8-ogYC-bMVgGW0nug6sK0nXgPJ1JmLq_db"

ARCHIVE_DRAFTS = [
    {
        "slug": "cat-litter-box-rescue-guide",
        "v1_file": DRAFTS_DIR / "cat-litter-box-rescue-guide_v1.md",
        "title": "The Complete Cat Litter Box Fix",
        "audience": "Cat owners dealing with inappropriate urination or litter box avoidance — especially multi-cat households",
        "trigger": "Exhaustion from cleaning messes, guilt about returning a pet, frustration with vets who can't find medical causes",
        "trend": "Complete diagnosis and fix for cat litter box issues — covering medical causes, environmental triggers, and multi-cat dynamics",
    },
    {
        "slug": "contractor-scam-protection-guide",
        "v1_file": DRAFTS_DIR / "contractor-scam-protection-guide_v1.md",
        "title": "How to Protect Yourself from Contractor Scams",
        "audience": "Homeowners planning renovations or repairs, especially first-time homeowners or those after major weather events",
        "trigger": "Having been scammed by a contractor, or fear of being scammed — financial loss plus the violation of trusting someone in your home",
        "trend": "Contractor scam protection guide — covering red flags, payment strategies, contract clauses, and recovery if you've already been scammed",
    },
    {
        "slug": "new-cat-first-weeks-survival-guide",
        "v1_file": DRAFTS_DIR / "new-cat-first-weeks-survival-guide_v1.md",
        "title": "Your First 14 Days With a New Cat",
        "audience": "First-time cat owners or experienced cat people adopting a new adult cat with an unknown history",
        "trigger": "Anxiety about doing it right — the new cat is hiding, not eating, or aggressive, and the adopter is terrified of making it worse",
        "trend": "New cat first two weeks survival guide — room-by-room setup, slow introduction protocol, stress signals, and when to intervene",
    },
]

DRAFT_SYSTEM = """You write full-length digital guide drafts. Your voice is smart-casual, warm,
empathetic, and data-grounded. Zero AI-slop. Write like someone who has lived this,
not someone who researched it. Use contractions, occasional humor, and direct address.

AVOID THESE WORDS COMPLETELY — they are trust-destroying AI-isms:
  "holistic", "dynamic", "robust", "scalable", "seamless", "game-changer",
  "leverage", "empower", "synergy", "win-win", "journey", "delve", "unlock",
  "transformative", "cutting-edge", "next-gen", "ecosystem"
Never use these in headings, body text, or callouts. They make readers trust you less.

Structure with clear H2/H3 headings. After each major section, add a bolded Key Takeaway.
Weave in the "human infrastructure" thesis subtly — managing personal energy and
household systems IS infrastructure, just at human scale.

CRITICAL: You MUST write ALL 4 parts as COMPLETE, production-ready chapters.
Every chapter must include actionable steps the reader can actually take.
No outlines, no "Full version coming soon," no placeholders, no "in V2."
Each chapter is 500-1200 words of real actionable content.

Total target: 10-15 pages of content."""


def call_minimax(system_prompt: str, user_prompt: str, max_tokens: int = 100000) -> str | None:
    """Direct MiniMax API call — matches trendscout_gen.py format exactly."""
    import urllib.request, urllib.error

    url = "https://api.minimax.io/anthropic/v1/messages"
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
            "X-Api-Key": MINIMAX_API_KEY,
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
    except urllib.error.HTTPError as e:
        print(f"  [HTTP ERROR] {e.code}: {e.read().decode()[:300]}")
        return None
    except Exception as e:
        import traceback
        print(f"  [ERROR] {e}")
        traceback.print_exc()
        return None


def generate_full_draft(slug: str, v1_content: str, info: dict) -> str | None:
    """Expand a skeleton _v1 draft into a full 4-part guide."""
    user = f"""Using this skeleton as the foundation, write the COMPLETE 4-PART guide draft.

SKELETON:
{v1_content[:6000]}

CONTEXT:
- Trend title: {info['title']}
- Audience: {info['audience']}
- Pain trigger: {info['trigger']}
- Score: 8/12
- Product angle: {info['trend']}

REQUIREMENTS:
1. ALL 4 parts must be FULLY WRITTEN — no outlines, no "full version soon"
2. Each part is 2000-4000 words with clear subheadings
3. Use the skeleton content as your structural backbone — expand every section
4. Add concrete, actionable steps the reader can take today
5. End with a clear "Your First Step" call to action

Write the complete guide now:"""

    return call_minimax(DRAFT_SYSTEM, user, max_tokens=100000)


def save_draft(slug: str, content: str, title: str, trend: str, audience: str, trigger: str) -> Path:
    """Save a full draft with proper YAML frontmatter."""
    draft_path = DRAFTS_DIR / f"{slug}.md"
    frontmatter = f"""---
title: "{title}"
slug: "{slug}"
trend: "{trend}"
audience: "{audience}"
emotional_trigger: "{trigger}"
score: 8/12
ai_conviction: HIGH CONVICTION
date: 2026-05-12
source_platform: archive
---

"""
    draft_path.write_text(frontmatter + content)
    return draft_path


def main():
    print("=" * 60)
    print("Archive Draft Regeneration — MiniMax Expansion")
    print("=" * 60)

    for info in ARCHIVE_DRAFTS:
        slug = info["slug"]
        v1_path = info["v1_file"]

        print(f"\n[{slug}]")
        print(f"  Reading skeleton: {v1_path.name}")
        v1_content = v1_path.read_text()
        print(f"  Skeleton size: {len(v1_content)} chars")

        print(f"  Calling MiniMax to expand to full guide...")
        full_content = generate_full_draft(slug, v1_content, info)

        if not full_content:
            print(f"  ❌ FAILED — skipping")
            continue

        print(f"  Generated: {len(full_content)} chars")
        draft_path = save_draft(
            slug,
            full_content,
            info["title"],
            info["trend"],
            info["audience"],
            info["trigger"],
        )
        print(f"  Saved: {draft_path.name} ({draft_path.stat().st_size // 1024} KB)")

    print("\n✅ All drafts regenerated — ready for checklist + PDF generation")
    print("   Run: python3 scripts/synthesize_checklist.py")
    print("   Then: python3 scripts/polish_pdfs.py")


if __name__ == "__main__":
    main()
