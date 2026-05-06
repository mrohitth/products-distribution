#!/usr/bin/env python3
"""
Distro Manifest — Distribution State Tracker
=============================================
Tracks every product across every channel and status.
Single source of truth for the distribution flywheel.

State file: distro/manifest/state.json
"""
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
STATE_FILE = WORKSPACE / "distro" / "manifest" / "state.json"

ET = timezone(timedelta(hours=-4))


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return _blank_state()


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _blank_state():
    return {
        "products": {},
        "channels": {
            "reddit": {"enabled": True, "posts_per_week": 2},
            "pinterest": {"enabled": True, "pins_per_week": 15},
            "tiktok": {"enabled": True, "scripts_per_week": 3},
            "linkedin": {"enabled": True, "posts_per_week": 2},
            "email_list": {"enabled": True},
        },
        "email_leads": 0,
        "last_full_run": None,
        "flywheel_runs": 0,
    }


def register_product(slug, name, price, draft_path, category):
    state = load_state()
    if slug not in state["products"]:
        state["products"][slug] = {
            "name": name,
            "price": price,
            "draft_path": str(draft_path),
            "category": category,
            "reddit_posted": 0,
            "pinterest_pins": 0,
            "tiktok_scripts": 0,
            "linkedin_posts": 0,
            "email_capture_count": 0,
            "notion_upsell_sent": 0,
            "lemon_squeezy_url": None,
            "created_at": datetime.now(ET).isoformat(),
        }
    save_state(state)


def bump_email_leads(state=None, count=1):
    s = state or load_state()
    s["email_leads"] += count
    save_state(s)


def mark_reddit_posted(slug):
    state = load_state()
    if slug in state["products"]:
        state["products"][slug]["reddit_posted"] += 1
    save_state(state)


def mark_pinterest_pin(slug):
    state = load_state()
    if slug in state["products"]:
        state["products"][slug]["pinterest_pins"] += 1
    save_state(state)


def mark_tiktok_script(slug):
    state = load_state()
    if slug in state["products"]:
        state["products"][slug]["tiktok_scripts"] += 1
    save_state(state)


def mark_linkedin_post(slug):
    state = load_state()
    if slug in state["products"]:
        state["products"][slug]["linkedin_posts"] += 1
    save_state(state)


def set_lemon_url(slug, url):
    state = load_state()
    if slug in state["products"]:
        state["products"][slug]["lemon_squeezy_url"] = url
    save_state(state)


def full_run_complete():
    state = load_state()
    state["last_full_run"] = datetime.now(ET).isoformat()
    state["flywheel_runs"] = state.get("flywheel_runs", 0) + 1
    save_state(state)


def print_summary():
    state = load_state()
    print("=== DISTRO MANIFEST ===")
    print(f"Email leads: {state['email_leads']}")
    print(f"Flywheel runs: {state['flywheel_runs']}")
    print(f"Last run: {state['last_full_run']}")
    for slug, p in state["products"].items():
        print(f"\n  [{slug}]")
        print(f"    Reddit: {p['reddit_posted']} posts")
        print(f"    Pinterest: {p['pinterest_pins']} pins")
        print(f"    TikTok: {p['tiktok_scripts']} scripts")
        print(f"    LinkedIn: {p['linkedin_posts']} posts")
        print(f"    LS URL: {p['lemon_squeezy_url']}")
    print()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print_summary()
    elif len(sys.argv) > 2 and sys.argv[1] == "register":
        register_product(sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6])
    elif len(sys.argv) > 2 and sys.argv[1] == "leads":
        print(load_state()["email_leads"])
    else:
        print_summary()