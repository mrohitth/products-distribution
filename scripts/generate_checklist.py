#!/usr/bin/env python3
"""
Stage 5.6 — Checklist Generator (v5)
--------------------------------------
MAJOR FIXES over v4:
  - Fragment guard: lines starting with orphan conjunctions
    (And/But/When/If/etc.) under 25 chars are rejected as standalone
    context items — no meaningful action on their own.
  - Low-value guard: items under 5 words or under 25 raw chars rejected.
  - Sub-bullet recovery: following indented/bullet sub-lines are
    appended to the main item with " — " separator, making a complete
    actionable thought (fixes items like "Ask specifically for:" that
    have trailing bullets in the source).
  - Fragment orphans correctly skipped now:
      "And it still keeps happening."     → SKIPPED
      "Ask specifically for:" (orphaned) → SKIPPED (no action verb, < 25)
      "**Do not respond**..."            → KEPT + enriched

FIXES v4:
  - OLD: items starting with bold phrases captured verbatim but
    orphaned context lines ("And it still keeps happening.") kept,
    creating hollow fragments in the checklist output.
  - NEW: orphan/fragment detection blocks sub-standard items.
  - Added bullet-sub-line recovery for context items.

"""
import sys, re, html as html_mod
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "output" / "final_products"

SKIP_PREFIXES = ["[ ]", "[x]", "[X]", "##", "###", "#", "```"]

ACTION_KEYWORDS = [
    "verify", "check", "call", "ask", "review", "inspect", "compare",
    "get", "obtain", "request", "sign", "pay",
    "read", "find", "look", "search", "visit", "submit", "file",
    "contact", "hire", "choose", "select", "avoid", "never", "don't",
    "do ", "make sure", "ensure", "keep", "save", "document",
    "step ", "action ", "tip:", "warning:", "important:",
]
LOW_PRIORITY = [
    "may", "might", "could", "sometimes", "if possible", "optional",
    "example:", "e.g.", "i.e.", "see also", "related:", "note:",
]

# Lines starting with any of these are isolated context/fragments,
# not standalone actions — skip them unless they exceed 25 chars
# (shorter = definitely orphaned sub-thoughts).
_ORPHAN_PREFIXES = [
    "And ", "But ", "Or ", "When ", "If ", "Unless ",
    "What ", "Even ", "Still ", "Already ", "Just ", "So ",
]


def strip_bold(text: str) -> str:
    """Remove bold markers cleanly, preserving ALL inner text."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*\*+", "", text)
    return text


def _is_orphan(line: str) -> bool:
    """True if line is a standalone context/fragment."""
    stripped = line.strip()
    if len(stripped) < 25:
        return True
    if any(stripped.startswith(p) for p in _ORPHAN_PREFIXES):
        return True
    return False


def _collect_sub_lines(lines: list[str], start_idx: int) -> list[str]:
    """Collect following bullet sub-lines (and indented continuations)
    until a new top-level action item is encountered or end of list."""
    collected = []
    i = start_idx + 1
    while i < len(lines):
        raw = lines[i].strip()
        if not raw:
            i += 1
            continue
        # Stop at a new top-level numbered action
        if re.match(r"^\d+\.\s+[A-Z]", raw) or re.match(r"^\d+\.\s+[^a-z]", raw):
            break
        # Skip section headers and horizontal rules
        if raw.startswith("#"):
            break
        if raw.startswith("---"):
            break
        # Collect indented/bullet sub-content
        bullet_or_indent = (
            raw.startswith("- ") or
            raw.startswith("* ") or
            (raw.startswith("  ") and len(raw) > 10)
        )
        if bullet_or_indent:
            sub = re.sub(r"^\s*[-*]\s+", "", raw)
            sub = re.sub(r"^\s*\d+\.\s+", "", sub)
            sub = strip_bold(sub)
            sub = sub.replace("*", "").strip()
            if len(sub) >= 10:
                collected.append(sub)
            i += 1
            continue
        # Stop at another orphan-style context line
        if _is_orphan(raw):
            break
        i += 1
    return collected


def is_action_item(line: str) -> bool:
    """Return True if this line is a meaningful action item."""
    lower = line.lower()
    if any(line.strip().startswith(p) for p in SKIP_PREFIXES):
        return False
    if re.match(r"^\s*[-*]\s*$", line) or re.match(r"^\s*\d+\.\s*$", line):
        return False
    if len(line.strip()) < 25:
        return False
    if any(line.strip().startswith(p) for p in _ORPHAN_PREFIXES):
        return False
    if any(p in lower for p in LOW_PRIORITY):
        return False
    if any(kw in lower for kw in ACTION_KEYWORDS):
        return True
    if re.match(r"^\d+\.\s+[A-Z]", line):
        return True
    return False


def extract_action_items(draft_path: Path, max_items: int = 12) -> list[str]:
    """Extract up to max_items most important action items from a draft.
    For each qualifying main item, optionally collects following bullet
    sub-lines to form a complete actionable thought."""
    content = draft_path.read_text(encoding="utf-8")
    raw_items = []
    lines = content.split("\n")

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(p) for p in SKIP_PREFIXES):
            continue

        if not is_action_item(line):
            continue

        clean = re.sub(r"^\s*[-*]\s+", "", line)
        clean = re.sub(r"^\s*\d+\.\s+", "", clean)

        # Strip bold markers BUT PRESERVE inner text
        clean = strip_bold(clean)

        # Strip leading action/step/tip/warning prefixes
        clean = re.sub(
            r"^(action|step|tip|warning|important)\s*[:\-]\s*", "",
            clean, flags=re.I
        )

        # Remove any remaining bare asterisks
        clean = clean.replace("*", "").strip()

        if len(clean) < 15:
            continue

        # Block orphan standalone context/fragment lines
        if _is_orphan(clean):
            continue

        # Collect following bullet sub-lines to enrich this item
        sub_lines = _collect_sub_lines(lines, idx)
        if sub_lines:
            sub_text = " — ".join(sub_lines)
            if sub_text not in clean:
                clean = f"{clean}. {sub_text}"

        raw_items.append(clean)

    seen = set()
    deduped = []
    for item in raw_items:
        key = item.lower()[:80].strip()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped[:max_items]


def checklist_css() -> str:
    return """
    /* ── CHECKLIST v5 CSS ─────────────────────────────────────────────────── */
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
    }

    /* ── Typography ─────────────────────────────────────────────────── */
    h1 {
        font-size: 24pt;
        font-weight: 700;
        color: #1a1a2e;
        border-bottom: 1px solid #eee;
        padding-bottom: 6pt;
        margin-bottom: 12pt;
        line-height: 1.25;
    }

    h2 {
        font-size: 18pt;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 8pt;
        line-height: 1.3;
    }

    /* ── Page ──────────────────────────────────────────────────────── */
    .page {
        padding: 24px 28px;
        max-width: 7in;
        margin: 0 auto;
    }

    .header {
        border-bottom: 2.5px solid #1a1a2e;
        padding-bottom: 10px;
        margin-bottom: 14px;
    }

    .meta {
        font-size: 9px;
        color: #888;
        margin-top: 4px;
        letter-spacing: 0.04em;
    }

    /* ── Checklist items ───────────────────────────────────────────── */
    ol.items {
        list-style: none;
        padding: 0;
    }

    li.item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 5pt;
        font-size: 11.5px;
        line-height: 1.4;
        color: #2d2d4a;
        padding: 3pt 0 3pt 0;
        border-bottom: 1px solid #f0f0f0;
    }

    li.item:last-child {
        border-bottom: none;
    }

    .cb {
        font-size: 13px;
        color: #4ADE80;
        flex-shrink: 0;
        line-height: 1.4;
        margin-top: 1pt;
    }

    .label {
        flex: 1;
    }

    /* ── Footer ───────────────────────────────────────────────────── */
    .footer {
        margin-top: 12pt;
        padding-top: 8pt;
        border-top: 1px solid #e0e0e0;
        font-size: 8px;
        color: #aaa;
        text-align: center;
    }
    """


def generate_checklist_pdf(draft_path: str) -> str | None:
    """Generate a 1-page printable checklist PDF. Returns path on success."""
    draft_path = Path(draft_path)
    slug = draft_path.stem
    checklist_path = OUTPUT_DIR / f"{slug}_CHECKLIST.pdf"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    items = extract_action_items(draft_path)

    if not items:
        title = slug.replace("-", " ").replace("_", " ").title()
        items = [
            f"Review the full {title} guide",
            "Identify your top 3 priority actions",
            "Complete your first action today",
            "Set a 7-day reminder for the next step",
        ]

    checkbox_rows = ""
    for item in items:
        safe = html_mod.escape(item, quote=True)
        display = safe[:90] + ("..." if len(safe) > 90 else "")
        checkbox_rows += (
            f'<li class="item">'
            f'<span class="cb">&#x2610;</span>'
            f'<span class="label">{display}</span>'
            f'</li>\n'
        )

    title_str = slug.replace("-", " ").replace("_", " ").title()
    date_str = datetime.now().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>{checklist_css()}</style>
</head>
<body>
  <div class="page">
    <div class="header">
      <h1 class="title">{html_mod.escape(title_str)} — Action Checklist</h1>
      <div class="meta">GENERATED {date_str} &nbsp;|&nbsp; Print this page and keep it somewhere visible</div>
    </div>
    <ol class="items">
{checkbox_rows}    </ol>
    <div class="footer">Companion to the full guide in your Lemon Squeezy library &mdash; check off each item as you complete it.</div>
  </div>
</body>
</html>"""

    try:
        import weasyprint
        wp_doc = weasyprint.HTML(string=html)
        wp_doc.write_pdf(str(checklist_path))
        size_kb = checklist_path.stat().st_size / 1024
        print(f"  ✅ Checklist ({len(items)} items): {checklist_path} ({size_kb:.0f} KB)")
        return str(checklist_path)
    except ImportError:
        print("  ⚠️  WeasyPrint not installed")
        return None
    except Exception as e:
        print(f"  ❌ WeasyPrint failed: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_checklist.py /path/to/draft.md")
        sys.exit(1)
    result = generate_checklist_pdf(sys.argv[1])
    sys.exit(0 if result else 1)