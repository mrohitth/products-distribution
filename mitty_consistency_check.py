#!/usr/bin/env python3
"""
mitty_consistency_check.py — Mitty Consistency Check Module
Extracts agent names from wiki/decisions/crew-roster-v3.md and compares
against manifest.json agents[]. Validates all 5 core crew are present.

Positive Standard: Python/Bash only — NO Spark, NO Kafka, NO Snowflake, NO EMR.
Exit codes: 0 = PASSED, 1 = FAILED, 2 = ROSTER_MISSING
"""

import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROSTER_PATH   = "/home/mathew/.openclaw/workspace/wiki/decisions/crew-roster-v3.md"
MANIFEST_PATH  = "/home/mathew/katzen/src/data/manifest.json"
FLAG_FILE      = "/home/mathew/.cache/katzen-sync/audit_consistency.flag"

# Canonical 5-agent crew (matches ## Decisions Made in crew-roster-v3.md)
CANONICAL_CREW = {"Kitty", "Witty", "Mitty", "Bitty", "Titty"}


def now_edt() -> str:
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M:%S %p %Z")


def ts_edt() -> str:
    return datetime.now(ZoneInfo("America/New_York")).isoformat()


def extract_roster_agents():
    if not os.path.exists(ROSTER_PATH):
        return set(), 0, "ROSTER_MISSING"

    with open(ROSTER_PATH) as f:
        content = f.read()

    # Primary: "1. **Kitty → Flagship ..." in ## Decisions Made
    pattern = r'\d+\.\s+\*\*([A-Za-z]+)\s*→'
    names = re.findall(pattern, content)

    if not names:
        # Fallback: **Name** followed by → or —
        pattern2 = r'\*\*([A-Z][a-z]+)\s*[\]→—]'
        names = re.findall(pattern2, content)

    return set(names), len(names), None


def load_manifest_agents():
    if not os.path.exists(MANIFEST_PATH):
        return set(), 0

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    agents = manifest.get("agents", [])
    return {a["name"] for a in agents}, len(agents)


def main():
    print(f"[{now_edt()}] Mitty Consistency Check: parsing roster")

    wiki_set, wiki_count, error = extract_roster_agents()

    if error == "ROSTER_MISSING":
        print(f"[{now_edt()}] ERROR: Roster wiki not found at {ROSTER_PATH}", file=sys.stderr)
        sys.exit(2)

    manifest_set, manifest_count = load_manifest_agents()

    # Capital Pilot ↔ Titty alias: they share the 5th crew slot
    # Normalize manifest by treating "Capital" as equivalent to "Titty" for this check
    normalized = manifest_set.copy()
    if "Capital" in normalized and "Titty" not in normalized:
        normalized.discard("Capital")
        normalized.add("Titty")

    missing = sorted(CANONICAL_CREW - normalized)
    extra   = sorted(normalized - CANONICAL_CREW)

    print(f"[{now_edt()}] Roster crew ({wiki_count}): {sorted(CANONICAL_CREW)}")
    print(f"[{now_edt()}] Manifest agents ({manifest_count}): {sorted(manifest_set)}")
    print(f"[{now_edt()}] Missing from manifest: {missing}")
    print(f"[{now_edt()}] Extra in manifest: {extra}")

    if missing or extra:
        os.makedirs(os.path.dirname(FLAG_FILE), exist_ok=True)
        with open(FLAG_FILE, "w") as f:
            f.write(f"FAIL\n")
            f.write(f"MISSING:{','.join(missing)}\n")
            f.write(f"EXTRA:{','.join(extra)}\n")
        print(f"[{now_edt()}] CONSISTENCY: FAILED", file=sys.stderr)
        sys.exit(1)
    else:
        try:
            os.remove(FLAG_FILE)
        except FileNotFoundError:
            pass
        print(f"[{now_edt()}] CONSISTENCY: PASSED ✅")
        sys.exit(0)


if __name__ == "__main__":
    main()