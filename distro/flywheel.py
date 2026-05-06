#!/usr/bin/env python3
"""
Distro Flywheel Orchestrator — Master Distribution Script
==========================================================
Runs the full distribution flywheel for all active products:
1. Content engine (Reddit, Pinterest, TikTok, LinkedIn)
2. Email funnel (lead magnet + 5-email sequence)
3. Notion template upsell
4. Manifest update + summary report

Usage:
  python3 distro/flywheel.py run [product_slug]   # run for one or all products
  python3 distro/flywheel.py status               # show current state
  python3 distro/flywheel.py register <slug>      # add product to manifest
"""
import json, os, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
CONTENT_ENGINE = WORKSPACE / "distro" / "content_engine.py"
NOTION_UPSELL = WORKSPACE / "distro" / "notion_upsell.py"
MANIFEST = WORKSPACE / "distro" / "manifest.py"
STATE_FILE = WORKSPACE / "distro" / "manifest" / "state.json"

ET = timezone(timedelta(hours=-4))


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return None


def run_content_engine(slug):
    """Run content engine for a slug."""
    result = subprocess.run(
        [sys.executable, str(CONTENT_ENGINE), "generate", slug],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
    )
    return result.returncode == 0, result.stdout, result.stderr


def run_notion_upsell(slug):
    """Run Notion template generator for a slug."""
    result = subprocess.run(
        [sys.executable, str(NOTION_UPSELL), "generate", slug],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
    )
    return result.returncode == 0, result.stdout, result.stderr


def run_flywheel(slug=None):
    """Run the full distribution flywheel."""
    state = load_state()
    if not state:
        print("[ERROR] No state found. Run: python3 distro/flywheel.py register <slug>")
        return

    products = state.get("products", {})
    if not products:
        print("[ERROR] No products registered. Run: python3 distro/flywheel.py register <slug>")
        return

    targets = [slug] if slug else list(products.keys())
    total_email_leads = 0

    print("=" * 60)
    print(f"  DISTRO FLYWHEEL — {datetime.now(ET).strftime('%Y-%m-%d %H:%M ET')}")
    print("=" * 60)

    for product_slug in targets:
        if product_slug not in products:
            print(f"[SKIP] '{product_slug}' not in manifest")
            continue

        p = products[product_slug]
        print(f"\n{'─' * 60}")
        print(f"  📦 {product_slug}")
        print(f"     Category: {p['category']} | Price: ${p['price']}")
        print(f"     Current: reddit={p['reddit_posted']} pins={p['pinterest_pins']} tiktok={p['tiktok_scripts']} linkedin={p['linkedin_posts']}")
        print(f"{'─' * 60}")

        # Layer 1: Content generation
        print("\n  [Layer 1] Content Repurposing Engine...")
        ok, out, err = run_content_engine(product_slug)
        if ok:
            for line in out.split("\n"):
                if "✓" in line or "ERROR" in line or "generating" in line.lower():
                    print(f"     {line.strip()}")
        else:
            print(f"     [ERROR] {err[:200]}")

        # Layer 2: Notion upsell
        print("\n  [Layer 2] Notion Template Upsell...")
        ok2, out2, err2 = run_notion_upsell(product_slug)
        if ok2:
            for line in out2.split("\n"):
                if "✓" in line or "ERROR" in line:
                    print(f"     {line.strip()}")
        else:
            print(f"     [ERROR] {err2[:200]}")

        # Update manifest
        manifest_state = json.loads(STATE_FILE.read_text())
        if product_slug in manifest_state["products"]:
            manifest_state["products"][product_slug]["last_content_run"] = datetime.now(ET).isoformat()
            STATE_FILE.write_text(json.dumps(manifest_state, indent=2))

    # Mark full run complete
    try:
        manifest_state = json.loads(STATE_FILE.read_text())
        manifest_state["last_full_run"] = datetime.now(ET).isoformat()
        manifest_state["flywheel_runs"] = manifest_state.get("flywheel_runs", 0) + 1
        STATE_FILE.write_text(json.dumps(manifest_state, indent=2))
    except Exception as e:
        print(f"[WARNING] Could not update manifest: {e}")

    print(f"\n{'=' * 60}")
    print(f"  ✅ Flywheel complete — {datetime.now(ET).strftime('%H:%M ET')}")
    print("=" * 60)


def show_status():
    """Show full distribution status."""
    state = load_state()
    if not state:
        print("No state file. Run: python3 distro/flywheel.py register <slug>")
        return

    print("\n=== DISTRIBUTION FLYWHEEL STATUS ===")
    print(f"Flywheel runs: {state.get('flywheel_runs', 0)}")
    print(f"Last run: {state.get('last_full_run', 'never')}")
    print(f"Total email leads: {state.get('email_leads', 0)}")

    channels = state.get("channels", {})
    print("\nChannels enabled:")
    for ch, cfg in channels.items():
        status = "✅" if cfg.get("enabled") else "❌"
        print(f"  {status} {ch}")

    print("\nProducts:")
    for slug, p in state.get("products", {}).items():
        ls_url = p.get("lemon_squeezy_url", "not set")
        print(f"\n  📦 {slug}")
        print(f"     Name: {p['name']}")
        print(f"     Price: ${p['price']}")
        print(f"     Category: {p['category']}")
        print(f"     Reddit: {p['reddit_posted']} | Pinterest: {p['pinterest_pins']} | TikTok: {p['tiktok_scripts']} | LinkedIn: {p['linkedin_posts']}")
        print(f"     Lemon Squeezy: {ls_url}")
        print(f"     Email captures: {p.get('email_capture_count', 0)}")
        print(f"     Notion upsells sent: {p.get('notion_upsell_sent', 0)}")


def register_product(slug, name, price, draft_path, category):
    """Register a new product in the manifest."""
    sys.path.insert(0, str(WORKSPACE / "distro"))
    from manifest import register_product as mp_register
    mp_register(slug, name, price, draft_path, category)
    print(f"[✓] Registered: {slug} ({name} — ${price})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "run":
        slug = sys.argv[2] if len(sys.argv) > 2 else None
        run_flywheel(slug)
    elif cmd == "status":
        show_status()
    elif cmd == "register" and len(sys.argv) >= 7:
        register_product(sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6])
    else:
        print(__doc__)