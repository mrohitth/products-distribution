#!/usr/bin/env python3
"""
Notion Upsell Generator — Distribution Flywheel Layer 3
========================================================
Takes a product draft and generates a Notion template version.
Notion templates are near-zero production cost, 80%+ margin.

Usage:
  python3 distro/notion_upsell.py generate <product_slug>
  python3 distro/notion_upsell.py list
"""
import json, os, sys, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
import http.client

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
CONFIG_PATH = Path("/home/mathew/.openclaw/openclaw.json")
OUT_DIR = WORKSPACE / "distro" / "assets" / "notion_templates"

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


def mm_completion(creds, prompt, system="You are a helpful assistant.", max_tokens=800):
    if not creds["api_key"]:
        print("ERROR: No MiniMax API key found in config")
        return None

    headers = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json"}
    payload = {
        "model": "MiniMax-M2.7",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "thinking": {"type": "off"},
    }

    conn = http.client.HTTPSConnection("api.minimax.io", timeout=30)
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
    drafts_dir = WORKSPACE / "products" / "drafts"
    if slug in SLUG_TO_DRAFT:
        f = drafts_dir / SLUG_TO_DRAFT[slug]
        if f.exists():
            return f.read_text()
    for f in drafts_dir.glob("*.md"):
        if slug.lower().replace("-", "_") in f.name.lower():
            return f.read_text()
    return None


def generate_notion_template(slug):
    """Generate a Notion template structure as markdown."""
    draft = load_product_draft(slug)
    if not draft:
        print(f"ERROR: No draft found for '{slug}'")
        return

    # Extract product name
    lines = draft.split("\n")
    product_name = slug.replace("_", " ").replace("-", " ").title()
    for line in lines[:20]:
        if line.startswith("#"):
            product_name = line.lstrip("#").strip()
            break

    # Detect category
    category = "Self-Help"
    for kw in ["single parent", "parenting", "teen"]:
        if kw in draft.lower():
            category = "Parenting"
    for kw in ["cat", "kitten", "pet"]:
        if kw in draft.lower():
            category = "Pet Care"

    system = """You are a productivity consultant who specializes in Notion workspace design.
You create clean, functional Notion templates that mirror the structure of a PDF guide.
Templates use:
- Headers: ## for page titles
- Properties: database field names
- Toggle blocks: for expandable content
- Callout blocks: for tips/warnings
- Bulleted lists: for steps
Be practical, not decorative."""

    prompt = f"""Product: {product_name}
Category: {category}

Create a Notion template structure based on this product. The template should:
1. Be a Notion database with one page per chapter/section
2. Include a master dashboard with properties (Status, Priority, Week, Notes)
3. Have each section page with: overview, key takeaways, action items as checkboxes, notes section
4. Mirror the workflow/framework from the original product

Product content (first 1500 chars):
{draft[:1500]}

Output as a markdown Notion template. Use these conventions:
- ## Page Title (top-level)
- ### Section Header
- - [ ] checkbox item (action step)
- > Callout/tip text
- **bold** for key terms
- Database properties listed at top

Format: Notion-compatible markdown that someone could copy into Notion."""

    result = mm_completion(
        creds,
        prompt,
        system,
        max_tokens=2000,
    )

    if result:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_file = OUT_DIR / f"{slug}_notion_template.md"
        out_file.write_text(f"# {product_name} — Notion Template\n\n{result}")
        print(f"[✓] Notion template → {out_file}")
        print(f"    Price point for this template: $17 (LS upsell)")

    return result


def list_templates():
    print("\n=== NOTION TEMPLATES ===")
    if not OUT_DIR.exists():
        print("No templates generated yet.")
        return
    for f in sorted(OUT_DIR.glob("*notion*")):
        size = len(f.read_text())
        print(f"  {f.stem}: {size} chars")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "generate" and len(sys.argv) >= 3:
        cfg = load_config()
        creds = get_minimax_creds(cfg)
        generate_notion_template(sys.argv[2])
    elif cmd == "list":
        list_templates()
    else:
        print(__doc__)