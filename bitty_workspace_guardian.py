#!/usr/bin/env python3
"""
Bitty Workspace Guardian — Proactive Maintenance Agent
Runs every 15 minutes. Keeps the workspace healthy without user intervention.
"""

import os, sys, re, json, subprocess, datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
BOOTSTRAP_MAX_CHARS = 60000
MAX_PER_FILE_CHARS  = 12000

TODAY = datetime.datetime.now().strftime("%Y-%m-%d")
LOG_FILE = MEMORY_DIR / f"{TODAY}.md"

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p %Z")
    line = f"- [{ts}] [Bitty Guardian] {msg}"
    print(line)
    # Append to daily log
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or os.path.expanduser("~"))
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), 1

def check_agents_md():
    """Trim verbose changelog tables in AGENTS.md if >80% capacity. Returns action string or None."""
    file = WORKSPACE / "AGENTS.md"
    if not file.exists():
        return None

    raw = file.read_text()
    size = len(raw)
    limit = MAX_PER_FILE_CHARS
    pct = size / limit * 100

    if pct < 80:
        return None  # silent — no action needed

    # Remove verbose Version History changelog tables — keep header row only
    # Pattern: tables with many " | " columns and "---" rows (changelog entries)
    original = raw
    lines = raw.split("\n")
    clean = []
    skip_block = False
    for i, line in enumerate(lines):
        # Detect changelog block start (## Version History section)
        if re.match(r"^#{1,3}\s+Version\s+History", line.strip()):
            # Keep this header + the table header line that follows
            clean.append(line)
            # Find next non-blank line
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                clean.append(lines[j])
                j += 1
            # Keep the table header if it's a markdown table row
            if j < len(lines) and re.match(r"^\|.*\|.*\|", lines[j]):
                clean.append(lines[j])
                j += 1
                # Skip all subsequent table rows until blank or new header
            while j < len(lines):
                if not lines[j].strip():
                    clean.append(lines[j])
                    j += 1
                    continue
                if re.match(r"^#{1,3}\s+", lines[j]):  # next section
                    break
                # Skip table rows (markdown rows with |)
                if re.match(r"^\|", lines[j]):
                    j += 1
                    continue
                break
            # Continue from j
            continue
        clean.append(line)

    new_raw = "\n".join(clean)
    new_size = len(new_raw)
    saved = size - new_size
    if saved > 500:
        file.write_text(new_raw)
        return f"AGENTS.md trimmed: -{saved} chars ({new_size} remain)"
    else:
        return f"AGENTS.md at {pct:.0f}% — needs manual review"

def check_memory_md():
    """Archive old events in MEMORY.md to keep it under bootstrap threshold. Returns action string or None."""
    file = WORKSPACE / "MEMORY.md"
    if not file.exists():
        return None

    raw = file.read_text()
    size = len(raw)
    limit = MAX_PER_FILE_CHARS
    pct = size / limit * 100

    if pct < 85:
        return None

    # Archive the "## Memory Events" section entries older than 30 days
    # Move old event blocks to a compressed summary
    lines = raw.split("\n")
    kept = []
    archived_count = 0
    in_events = False
    result = None
    cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
    event_pat = re.compile(r"^###\s+\[([\d-]+)\]")

    for line in lines:
        if line.startswith("## Memory Events"):
            in_events = True
            kept.append(line)
            continue
        if in_events and re.match(r"^#{1,3}\s+", line) and not event_pat.match(line):
            in_events = False
            kept.append(line)
            continue
        if in_events:
            m = event_pat.match(line)
            if m:
                date_str = m.group(1)
                try:
                    d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    if d < cutoff:
                        archived_count += 1
                        continue  # drop old entry
                except:
                    pass
        kept.append(line)

    if archived_count:
        new_raw = "\n".join(kept)
        new_size = len(new_raw)
        saved = size - new_size
        file.write_text(new_raw)
        result = f"MEMORY.md archived: {archived_count} events pruned, -{saved} chars"

    # If still oversized, do a deeper trim — collapse older sections to single-line summaries
    if len(file.read_text()) > MAX_PER_FILE_CHARS:
        raw2 = file.read_text()
        # Compress any remaining long "### [date]" blocks >3 lines to 1 line
        lines2 = raw2.split("\n")
        compressed = []
        i = 0
        while i < len(lines2):
            m = event_pat.match(lines2[i])
            if m and i + 2 < len(lines2):
                # Check if next 2 lines are normal prose (not blank/not header)
                next_lines = []
                j = i + 1
                while j < len(lines2) and len(next_lines) < 2:
                    if lines2[j].strip() and not re.match(r"^#{1,3}\s+", lines2[j].strip()):
                        next_lines.append(lines2[j].strip()[:80])
                        j += 1
                    else:
                        break
                if next_lines:
                    # Collapse to single line
                    compressed.append(f"### [{m.group(1)}] {'; '.join(s[:60] for s in next_lines[:2])}")
                    i = j
                    continue
            compressed.append(lines2[i])
            i += 1

        new_raw2 = "\n".join(compressed)
        if len(new_raw2) < len(raw2) - 200:
            file.write_text(new_raw2)
            result = f"MEMORY.md deep-compressed: {len(raw2) - len(new_raw2)} chars saved"
    return result  # will be None if no action or a string if action taken

def clean_session_baks():
    """Remove stale .bak session files. Returns action string or None."""
    bak_files = list(Path.home().glob(".openclaw/agents/**/*/*.bak"))
    if not bak_files:
        return None
    count = 0
    total_size = 0
    for f in bak_files[:50]:  # cap per run
        try:
            sz = f.stat().st_size
            age_days = (datetime.datetime.now() - datetime.datetime.fromtimestamp(f.stat().st_mtime)).days
            if age_days >= 3:
                f.unlink()
                count += 1
                total_size += sz
        except Exception:
            pass
    if count:
        return f"Session BAK cleanup: {count} files, {total_size/1024:.0f} KB freed"
    return None

def check_uncommitted():
    """Check key repos for uncommitted changes. Auto-commit if stale (>3 days). Returns action string or None."""
    actions = []
    repos = {
        "oasis-redesign": "/home/mathew/workspace/oasis-redesign",
        "katzen": "/home/mathew/workspace/katzen",
        "MarketBot": "/home/mathew/MarketBot",
        "workspace": str(WORKSPACE),
    }
    for name, path in repos.items():
        out, rc = run("git status --porcelain", cwd=path)
        if rc != 0 or not out.strip():
            continue
        
        # Check if oldest uncommitted change is >3 days old
        oldest_ts, _ = run('git log -1 --format=%ct 2>/dev/null || echo 0', cwd=path)
        if oldest_ts.strip() and oldest_ts.strip() != '0':
            try:
                oldest_sec = int(oldest_ts.strip())
                age_hours = (datetime.datetime.now().timestamp() - oldest_sec) / 3600
                if age_hours > 72:  # 3 days
                    run('git add -A && git commit -m "Bitty: auto-commit stale changes"', cwd=path)
                    actions.append(f"{name}: auto-committed ({age_hours:.0f}h stale)")
                    continue
            except ValueError:
                pass
        
        actions.append(f"{name}: {out.strip()[:80]}")
        # Still do daily workspace MEMORY syncs
        if name == "workspace" and "MEMORY.md" in out:
            run('git add MEMORY.md && git commit -m "Bitty: daily memory sync"', cwd=path)
    
    if actions:
        return "Changes: " + " | ".join(actions)
    return None

def main():
    actions_taken = []
    
    r1 = check_agents_md()
    if r1: actions_taken.append(r1)
    r2 = check_memory_md()
    if r2: actions_taken.append(r2)
    r3 = clean_session_baks()
    if r3: actions_taken.append(r3)
    r4 = check_uncommitted()
    if r4: actions_taken.append(r4)
    
    # Only log to daily memory if something actually happened
    if actions_taken:
        log("Actions: " + " | ".join(actions_taken))
    else:
        # Silent — no log entry for routine clean sweeps
        pass

if __name__ == "__main__":
    main()