#!/usr/bin/env python3
"""
witty_manifest_updater.py — Witty Manifest Guardian
Pure Python file I/O — zero token cost, zero LLM calls.
Scans wiki/ for recent changes and updates katzen manifest.json.
Runs every 15 min via cron (systemEvent). No model needed.

Positive Standard: Python/Bash only — NO Spark, NO Kafka, NO Snowflake, NO EMR.
Exit codes: 0 = ok, 1 = error
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

WIKI_DIR   = Path("/home/mathew/.openclaw/workspace/wiki")
MANIFEST   = Path("/home/mathew/katzen/src/data/manifest.json")
STATE_FILE = Path("/home/mathew/.cache/katzen-sync/.last_sync_state.json")
CACHE_DIR  = CACHE_DIR = STATE_FILE.parent


def ts_edt():
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M:%S %p %Z")


def ts_iso():
    return datetime.now(ZoneInfo("America/New_York")).isoformat()


def _read_manifest() -> dict:
    if not MANIFEST.exists():
        print(f"[{ts_edt()}] ERROR: manifest.json not found at {MANIFEST}", file=sys.stderr)
        sys.exit(1)
    with open(MANIFEST) as f:
        return json.load(f)


def _write_manifest(data: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(MANIFEST)


def _load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_sync": None, "last_files": {}}


def _save_state(state: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    tmp.replace(STATE_FILE)


def _scan_wiki(since_ts: str | None) -> list[dict]:
    """Return list of dicts for files changed since since_ts (ISO str or None)."""
    changes = []
    cutoff = None
    if since_ts:
        try:
            cutoff = datetime.fromisoformat(since_ts.replace("Z", "+00:00"))
        except ValueError:
            cutoff = None

    for path in WIKI_DIR.rglob("*.md"):
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if cutoff and mtime <= cutoff:
            continue
        # Read first 200 chars for summary
        try:
            with open(path, errors="replace") as f:
                content = f.read(200)
            summary = content[:120].replace("\n", " ").strip()
        except Exception:
            summary = "(read error)"

        changes.append({
            "filename": path.name,
            "filepath": str(path),
            "action": "modified",
            "summary": f"Modified: {path.name}. Key content: {summary}...",
            "timestamp": mtime.isoformat(),
            "size_bytes": path.stat().st_size,
        })
    return changes


def main():
    print(f"[{ts_edt()}] Witty Manifest Guardian: scanning wiki")

    manifest = _read_manifest()
    state    = _load_state()

    last_sync = state.get("last_sync")
    changes   = _scan_wiki(last_sync)

    if not changes:
        print(f"[{ts_edt()}] Witty: No new wiki changes since last sync ({last_sync or 'first run'}).")
        sys.exit(0)

    print(f"[{ts_edt()}] Witty: Found {len(changes)} changed file(s): {[c['filename'] for c in changes]}")

    # Prepend new changes to recent_activity, keep last 50
    existing = manifest.get("recent_activity", [])
    manifest["recent_activity"] = (changes + existing)[:50]
    manifest["last_updated"]    = ts_iso()

    _write_manifest(manifest)

    # Update state
    state["last_sync"] = ts_iso()
    state["last_files"] = {c["filename"]: c["timestamp"] for c in changes}
    _save_state(state)

    print(f"[{ts_edt()}] Witty: manifest.json updated with {len(changes)} change(s). ✅")


if __name__ == "__main__":
    main()
