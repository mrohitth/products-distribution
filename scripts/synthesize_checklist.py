#!/usr/bin/env python3
"""
Stage 5.7 — AI Agentic Checklist Synthesizer (v6)
=================================================
Three changes from v5:
  1. COMPLETE SENTENCES — all items fully written, no truncation
  2. PLAIN ENGLISH — no academic terms (crepuscular → dawn and dusk, etc.)
  3. GROUPED INTO 3 CATEGORIES with sub-header rows
     CSS: align-items: flex-start for checkboxes, #555 for item descriptions

Each item follows the Senior Content Strategist formula:
    [Bolded Header] + [Action Verb] + [Main Task] + [Why/How Detail]
Prohibitions: No fragments | No items under 20 words | No academic language
"""
import sys, html as html_mod, json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "output" / "final_products"


# ══════════════════════════════════════════════════════════════════
#  SYNTHESIZED CHECKLIST ITEMS — v6
#  All complete sentences | Plain English | 3 categories each (4 items)
# ══════════════════════════════════════════════════════════════════

SYNTHESIZED_ITEMS = {

    # ── CAT-LITTER BOX RESCUE GUIDE ─────────────────────────────────
    # Category 1: Medical Check (items 1-4)
    # Category 2: Box Setup (items 5-8)
    # Category 3: Recovery Plan (items 9-12)

    "cat-litter-box-rescue-guide_v1": [
        # ── Category 1: Medical Check ──
        "Schedule a Vet Urinalysis Within 3 Days: Peeing outside the box is a medical signal before it's a behavioral one. A urinalysis rules out UTI, bladder stones, FLUTD, and kidney disease — the most common medical causes.",
        "Request a Blood Panel If Your Cat Is Middle-Aged or Older: Kidney disease and diabetes both cause increased urination that owners mistake for behavioral problems. A basic blood panel costs $80-$150 and gives you a clean baseline or an early warning.",
        "Watch for These Signs That Need an Emergency Vet Visit: Straining to pee with little output, crying while in the box, blood in urine, or lethargy combined with not eating. These are not wait-and-see symptoms — they indicate a potential blockage.",
        "Ask Your Vet to Rule Out Diabetes and Hyperthyroidism: Both conditions increase water intake and urination volume. If your cat is drinking more and peeing more, these are on the differential diagnosis list alongside UTI.",
        # ── Category 2: Box Setup ──
        "Switch to an Uncovered Box That's 1.5x Your Cat's Body Length: Most store-bought boxes are too small. A storage tote with a cut-out entrance gives most cats enough room to turn around and dig without their back touching the walls.",
        "Follow the N+1 Rule for Box Count: One box per cat, plus one extra. In a two-cat home, that means three boxes on separate floors with at least two escape routes each — cats don't want to feel cornered mid-elimination.",
        "Use Unscented Clumping Litter at 2 Inches Deep, Scooped Daily: Scented litters repel cats with sensitive noses. Unscented clumping litter at the right depth prevents paw-pad discomfort and makes daily scooping fast enough to actually happen.",
        "Keep Every Litter Box Away From Food Bowls and Loud Appliances: Cats evolved to eliminate away from their food source. Boxes near refrigerators, washers, or furnaces get avoided — the sound and vibration feel threatening during a vulnerable moment.",
        # ── Category 3: Recovery Plan ──
        "Soak Accident Spots With Cat-Specific Enzymatic Cleaner for 15 Minutes Before Blotting: Generic cleaners leave uric acid residue that cats can still smell. A cat-labeled enzymatic formula (Rocco & Roxie or similar) breaks it down fully — let it sit 15 minutes, then blot, never scrub.",
        "Run a Feliway Diffuser in the Room Where Accidents Happened Most: Feliway mimics the calming facial pheromone cats leave when they feel safe. One diffuser covers about 700 square feet and takes 2-3 weeks to reach full effectiveness — don't judge it before day 21.",
        "Add a Third Box in the Area With the Most Accidents Before Day 14: Extra boxes catch more of the house and give cats options. Place this third box in the most accident-prone area, not in a remote corner the cat already avoids.",
        "Book a Follow-Up Vet Visit at Day 30 If Accidents Haven't Stopped Completely: Medical and environmental fixes take 3-4 weeks to show full effect. If you're not at 90% improvement by day 30, go back to the vet or ask for a referral to a veterinary behaviorist.",
    ],

    # ── CONTRACTOR SCAM PROTECTION GUIDE ───────────────────────────
    # Category 1: Vet Before You Sign (items 1-4)
    # Category 2: Payment Protection (items 5-8)
    # Category 3: If You've Been Hit (items 9-12)

    "contractor-scam-protection-guide_v1": [
        # ── Category 1: Vet Before You Sign ──
        "Search Your State's License Board by Name and License Number Before Hiring: Every state has a Contractor State License Board or equivalent. A 5-minute search at cslb.ca.gov or your state's equivalent tells you if the license is current, clean, and tied to a real business.",
        "Ask for Proof of General Liability Insurance and Workers' Comp — Written, Not Verbal: A contractor who says they're insured but can't produce a policy document isn't insured. Minimum recommended coverage is $1M general liability. For big projects, call the insurance company directly to confirm.",
        "Check Your State's Consumer Protection Site for Filed Complaints: Most states publish complaint history online. Search the contractor's name and license number together — a pattern of unresolved complaints from multiple homeowners is a clear walk-away signal.",
        "Get Three Written Bids That Include Full Scope, Materials, Timeline, and Payment Schedule: Verbal estimates don't bind anyone. A written bid that refuses to specify materials or timeline isn't a real bid — it's a setup for a surprise invoice later.",
        # ── Category 2: Payment Protection ──
        "Never Pay More Than $1,000 or 10% Down — Whichever Is Less — for Residential Work: This isn't just good advice, it's the law in California and a model in many other states. If a contractor asks for more upfront before starting, that is a red flag — walk away.",
        "Pay by Check, Credit Card, or a Platform With Fraud Protection — Never Cash: Cash leaves no trail and is untraceable if something goes wrong. A credit card gives you a chargeback option. If a contractor insists on cash, that's two red flags at once.",
        "Get These Six Clauses in Every Contract Before Signing: Scope of work with materials list, payment schedule tied to milestones, change order process with pricing, warranty clause, termination clause, and lien waiver. Without all six, you have no legal protection.",
        "File a Mechanics Lien on Your Property Within 90 Days of Any Payment if Work Stops: A mechanics lien prevents the contractor from collecting from other sources using your property as collateral. It also puts other subcontractors on notice that your title isn't clean — act within your state's deadline.",
        # ── Category 3: If You've Been Hit ──
        "File a Complaint With Your State License Board Within Your State's Filing Window: Most states have a specific deadline — don't assume you have unlimited time. The CSLB or equivalent can revoke a contractor's license and order restitution. Time matters in regulatory recovery.",
        "File a Police Report If the Amount Exceeds Your State's Threshold — Typically $950+: Contractor fraud above that threshold crosses into felony territory in most states. A police report creates a paper trail and may trigger an investigation if other victims have filed similar reports.",
        "Report the Fraud to the FTC at ReportFraud.ftc.gov Even if the Amount Is Small: Your individual report may not lead to immediate recovery, but it contributes to a pattern case. The FTC builds cases across state lines and your data matters even in small-dollar cases.",
        "Consult a Construction Litigation Attorney if the Amount Lost Exceeds Your State's Small Claims Limit: Small claims court handles up to your state's limit (typically $5,000-$15,000). For larger amounts, a construction attorney can file in superior court and potentially attach assets or liens.",
    ],

    # ── NEW CAT FIRST WEEKS SURVIVAL GUIDE ─────────────────────────
    # Category 1: First 48 Hours (items 1-4)
    # Category 2: Week 1 Routine (items 5-8)
    # Category 3: Week 2 and Beyond (items 9-12)
    # Plain English: crepuscular → dawn and dusk, etc.

    "new-cat-first-weeks-survival-guide_v1": [
        # ── Category 1: First 48 Hours ──
        "Pick One Small Room as the Safe Room — Not the Whole House: Give your new cat one bedroom or small area with a litter box (away from food), one hiding spot, and water. Forcing full-house access on day one creates panic — let them come to you.",
        "Keep the Room Quiet and Low-Traffic for the First 48 Hours: No loud music, no visitors, no vacuuming near the safe room. Dim the lights slightly if there's a lot of outside movement. Your goal is a space where the cat feels safe enough to start exploring.",
        "Sit Quietly in the Room Without Looking at the Cat — Offer Treats From Your Lap: Read your phone or a book out loud at low volume. This gets your cat used to your presence without the pressure of eye contact. Eye contact from a stranger is a threat signal in cat language.",
        "Use Slow Blinks and Look Away When Making Eye Contact — This Signals Non-Threat: Slow blinking at a cat is how cats say I trust you. Practice it when your cat looks at you. Within a day or two, your cat will slow-blink back — that's the first sign of real bonding.",
        # ── Category 2: Week 1 Routine ──
        "Set Feeding to Happen Right Before Your Bedtime — Roughly 10 to 11pm: Cats are naturally active at dawn and dusk. Moving the last meal of the day to your bedtime means your cat's natural drowsiness overlaps with yours — and they sleep through the night with you.",
        "Run a 15-Minute Active Play Session Before the Final Meal Using a Wand Toy: Active play at dusk tires out the hunting instinct. Use a wand toy or laser pointer for 15 minutes, then feed. The play-exhaust-hunt-satisfy cycle is how cats naturally end their day.",
        "Do Not Get Up or Make Eye Contact When Your Cat Cries at Night — Silence Breaks the Loop: Cats quickly learn that meowing at night gets human attention. If you don't want 5am wake-ups for the next decade, don't reinforce the behavior in the first week. Zero response, zero eye contact.",
        "Weigh Your Cat Once a Week on a Kitchen Scale to Confirm Normal Adjustment: Weight loss of more than 5-7% of body weight in one week is a medical red flag, not a behavioral one. Track the trend — a single low reading means nothing, a downward trend means call the vet.",
        # ── Category 3: Week 2 and Beyond ──
        "Open Access to One New Room Per Week — Always With an Escape Route Back to the Safe Room: Let your cat discover one new room per week. They need to know they can retreat to the safe room whenever they want. Forcing full-house access before week 3 causes sustained stress.",
        "Keep Food and Water in a Different Room From the Litter Box — Cats Won't Eat Near Their Bathroom: This is an instinctive territorial rule. If the litter box is in the same room as food and water, your cat may start avoiding the box — move one or the other to prevent this.",
        "Watch for These Warning Signs That Need a Vet Call Within 24 Hours: Not eating for 24+ hours, hiding for more than 3 days without coming out briefly, visible aggression (swatting or hissing when you enter the room), or any straining to urinate. These aren't wait-and-see situations.",
        "Schedule a Post-Adoption Vet Check Within 14 Days With Your Adoption Records: Bring whatever the shelter gave you — medical records, behavioral notes, food information. Many medical issues (Giardia, upper respiratory infections) surface in the first two weeks after shelter exposure.",
    ],

}


# ══════════════════════════════════════════════════════════════════
#  CSS — v6
#   • align-items: flex-start on checkboxes (better vertical alignment)
#   • .item-body in #555 to distinguish from bold headers
#   • Category sub-headers styled distinctly
# ══════════════════════════════════════════════════════════════════

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

    /* ── Typography ─────────────────────────────────────────────── */
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

    /* ── Category sub-header ─────────────────────────────────── */
    .category-header {
        font-size: 10pt;
        font-weight: 700;
        color: #4ADE80;       /* moss green accent */
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 14pt 0 6pt 0;
        padding-bottom: 4pt;
        border-bottom: 1.5px solid #4ADE80;
    }

    .category-header:first-of-type {
        margin-top: 0;
    }

    /* ── Checklist items ─────────────────────────────────────────── */
    ol.items {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    li.item {
        display: flex;
        align-items: flex-start;   /* v6: checkbox top-aligned */
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

    /* Bolded header inline */
    .item-header {
        font-weight: 700;
        color: #1a1a2e;
    }

    /* Plain English description — v6: #555 dark gray */
    .item-body {
        font-weight: 400;
        color: #555555;
    }

    /* ── Footer ─────────────────────────────────────────────────── */
    .footer {
        margin-top: 14pt;
        padding-top: 9pt;
        border-top: 1px solid #e0e0e0;
        font-size: 8pt;
        color: #aaa;
        text-align: center;
    }
    """


def parse_items(raw_items: list) -> list:
    """
    Split a flat list of 12 items into 3 categories of 4.
    Categories are inferred from product type and position.
    Returns list of (category_label, items) tuples.
    """
    # Each product has exactly 12 items in groups of 4
    chunks = [raw_items[i:i+4] for i in range(0, len(raw_items), 4)]
    return chunks


# Category labels per product
CATEGORY_LABELS = {
    "cat-litter-box-rescue-guide_v1": [
        "Medical Check — Rule Out Health Problems First",
        "Box Setup — Create the Right Environment",
        "Recovery Plan — 30-Day Reset With Milestones",
    ],
    "contractor-scam-protection-guide_v1": [
        "Before You Sign — Verify Everything",
        "Payment Protection — Lock Down Your Money",
        "If You've Been Hit — Recovery Steps",
    ],
    "new-cat-first-weeks-survival-guide_v1": [
        "First 48 Hours — Set Up for Success",
        "Week 1 Routine — Build the Sleep Schedule",
        "Week 2 and Beyond — Expand and Monitor",
    ],
}


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


def generate_checklist_pdf(slug: str, title_str: str) -> str | None:
    items = SYNTHESIZED_ITEMS.get(slug, [])
    if not items:
        return None

    categories = CATEGORY_LABELS.get(slug, [])
    category_chunks = parse_items(items)

    checklist_path = OUTPUT_DIR / f"{slug}_CHECKLIST.pdf"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%B %d, %Y")

    # Build HTML: iterate categories + items
    html_parts = []
    for chunk, cat_label in zip(category_chunks, categories):
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


SYNTHESIZED_SLUGS = {
    "cat-litter-box-rescue-guide_v1":      "Cat Litter Box Rescue Guide",
    "contractor-scam-protection-guide_v1":  "Contractor Scam Protection Guide",
    "new-cat-first-weeks-survival-guide_v1": "New Cat First Weeks Survival Guide",
}


def get_active_slugs():
    """Load slugs from today's TrendScout JSON. Fallback to all SYNTHESIZED_SLUGS."""
    today = datetime.now().strftime("%Y-%m-%d")
    trends_file = WORKSPACE / "wiki" / "trends" / f"{today}.json"
    if trends_file.exists():
        data = json.loads(trends_file.read_text())
        active = [t["slug_candidate"] for t in data.get("trends", [])
                  if t.get("slug_candidate") in SYNTHESIZED_SLUGS]
        if active:
            return active
    return list(SYNTHESIZED_SLUGS.keys())


if __name__ == "__main__":
    print("=" * 60)
    print("AI Agentic Checklist Synthesizer (v6 — Complete + Plain English)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    active = get_active_slugs()
    print(f"  Active products: {active}")

    for slug in active:
        title = SYNTHESIZED_SLUGS.get(slug)
        if not title:
            print(f"  [WARN] No title for '{slug}' — skipping")
            continue
        result = generate_checklist_pdf(slug, title)
        if result:
            print(f"  ✅ {result}")
        else:
            print(f"  ❌ Failed: {slug}")

    print("=" * 60)