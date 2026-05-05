#!/usr/bin/env python3
"""
bitty_wiki_guardian.py — Bitty's Wiki Correction Ledger Scanner
Pure Python file scan — zero LLM, zero cloud cost.

Scans /wiki for any document mentioning the forbidden stack
(Spark, Kafka, Snowflake, PySpark, EMR) in a production/implemented context.
Flags violations to /tmp/wiki_guardian_violations.flag + returns exit code.

Positive Standard: Python/Bash only — NO Spark, NO Kafka, NO Snowflake, NO EMR.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

WORKSPACE      = "/home/mathew/.openclaw/workspace"
FLAG_FILE      = "/tmp/wiki_guardian_violations.flag"
VIOLATION_LOG  = "/home/mathew/.cache/katzen-sync/vram_transitions.log"

FORBIDDEN = {
    "spark", "pyspark", "apache_spark", "emr", "elastic mapreduce",
    "kafka", "apache_kafka", "confluent",
    "snowflake", "snowflakedb",
}


def now_edt() -> str:
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M:%S %p %Z")


def ts_edt() -> str:
    return datetime.now(ZoneInfo("America/New_York")).isoformat()


def scan_wiki() -> list[dict]:
    """
    Walk /wiki — skip archive/ subtrees.
    Flag any .md file that mentions a forbidden term (case-insensitive).
    """
    wiki_root = Path(WORKSPACE) / "wiki"
    violations = []

    for path in wiki_root.rglob("*.md"):
        if "/archive/" in str(path):
            continue  # skip archived logs

        try:
            content = path.read_text(errors="ignore").lower()
        except OSError:
            continue

        for term in FORBIDDEN:
            if term in content:
                idx    = content.index(term)
                snippet = content[max(0, idx-40):idx+60].replace("\n", " ").strip()
                violations.append({
                    "file":     path.name,
                    "path":     str(path),
                    "term":     term,
                    "snippet":  snippet,
                    "timestamp": ts_edt(),
                })
                break  # one violation per file is enough

    return violations


def main():
    print(f"[{now_edt()}] Bitty Wiki Guardian: scanning /wiki")

    violations = scan_wiki()

    if violations:
        print(f"[{now_edt()}] Bitty Wiki Guardian: {len(violations)} VIOLATION(S) FOUND")
        for v in violations:
            print(f"  WIKI GUARDIAN VIOLATION: {v['file']} — contains '{v['term']}'")
            print(f"    → {v['snippet'][:80]}")
        with open(FLAG_FILE, "w") as f:
            for v in violations:
                f.write(f"VIOLATION|{v['file']}|{v['term']}|{v['path']}|{v['timestamp']}\n")
        sys.exit(1)
    else:
        print(f"[{now_edt()}] Bitty Wiki Guardian: No contradictions detected. /wiki is clean. ✅")
        try:
            os.remove(FLAG_FILE)
        except FileNotFoundError:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()
