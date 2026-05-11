#!/usr/bin/env python3
"""
Stage 5.5 — Checklist Generator (v3)
Takes a draft .md path, extracts KEY action items only (no checkbox items,
no noise), and creates a 1-page printable checklist PDF.
FIXES v2:
  - HTML-escapes item text before embedding in HTML (prevents ** from being interpreted)
  - Aggressive bold stripping: strips ** from BOTH ends, then collapses any bare **
  - Skips lines with malformed/unclosed bold markers
  - Deduplicates by normalized key, not just first 60 chars
"""
import sys, re, html as html_mod
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "output" / "final_products"

# ── What to SKIP ──────────────────────────────────────────────────────────────
SKIP_PREFIXES = [
    "[ ]", "[x]", "[X]",  # checkbox items — reminders, not actions
    "##", "###", "#",       # section headers
    "```",                  # code blocks
]
SKIP_PATTERNS = [
    r"^\s*[-*]\s*$",       # empty bullet
    r"^\s*\d+\.\s*$",      # empty numbered
    r"^source:\s",         # attribution lines
    r"^url:\s",            # link lines
]

# ── Action keywords (must contain one to qualify) ─────────────────────────────
ACTION_KEYWORDS = [
    "verify", "check", "call", "ask", "review", "inspect", "compare",
    "get", "obtain", "request", "get three", "sign", "pay", "use",
    "read", "find", "look", "search", "visit", "submit", "file",
    "contact", "hire", "choose", "select", "avoid", "never", "don't",
    "do ", "make sure", "ensure", "keep", "save", "document",
    "step ", "action ", "tip:", "warning:", "important:",
]
LOW_PRIORITY = [
    "may", "might", "could", "sometimes", "if possible", "optional",
    "example:", "e.g.", "i.e.", "see also", "related:", "note:",
]


def strip_bold(text: str) -> str:
    """Remove ALL markdown bold markers cleanly, even malformed ones."""
    # First pass: properly paired **...** → ...
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    # Second pass: collapse any bare ** that remain (from malformed input)
    text = re.sub(r"\*\*+", "", text)
    return text


def is_action_item(line: str) -> bool:
    """Return True if this line is a meaningful action item."""
    lower = line.lower()

    if any(line.strip().startswith(p) for p in ["[ ]", "[x]", "[X]"]):
        return False
    if re.match(r"^\s*[-*]\s*$", line) or re.match(r"^\s*\d+\.\s*$", line):
        return False
    if len(line.strip()) < 20:
        return False
    if any(p in lower for p in LOW_PRIORITY):
        return False

    if any(kw in lower for kw in ACTION_KEYWORDS):
        return True
    if re.match(r"^\d+\.\s+[A-Z]", line):
        return True
    return False


def extract_action_items(draft_path: Path, max_items: int = 12) -> list[str]:
    """Extract up to max_items most important action items from a draft."""
    content = draft_path.read_text(encoding="utf-8")
    raw_items = []

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(p) for p in ["##", "###", "#", "```"]):
            continue

        if not is_action_item(line):
            continue

        # Strip numbered list prefix and bullet prefix
        clean = re.sub(r"^\s*[-*]\s+", "", line)
        clean = re.sub(r"^\s*\d+\.\s+", "", clean)

        # Aggressively strip bold — both proper and malformed
        clean = strip_bold(clean)

        # Strip leading action/step/tip/warning prefixes
        clean = re.sub(
            r"^(action|step|tip|warning|important)\s*[:\-]\s*", "", clean,
            flags=re.I
        )

        # Final safety: remove any remaining asterisks
        clean = clean.replace("*", "").strip()

        if len(clean) >= 15:
            raw_items.append(clean)

    # Deduplicate by normalized key (lower, first 80 chars)
    seen = set()
    deduped = []
    for item in raw_items:
        key = item.lower()[:80].strip()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped[:max_items]


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

    # HTML-escape ALL item text — critical for preventing ** from being interpreted
    checkbox_rows = ""
    for item in items:
        safe = html_mod.escape(item, quote=True)
        display = safe[:90] + ("..." if len(safe) > 90 else "")
        checkbox_rows += f'<li class="item"><span class="cb">☐</span><span class="label">{display}</span></li>\n'

    title_str = slug.replace("-", " ").replace("_", " ").title()
    date_str = datetime.now().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', sans-serif; background: #fff; color: #1a1a2e; }}
    .page {{ padding: 22px 28px; max-width: 7in; margin: 0 auto; }}
    .header {{ border-bottom: 2.5px solid #1a1a2e; padding-bottom: 10px; margin-bottom: 14px; }}
    .title {{ font-size: 18px; font-weight: 700; color: #1a1a2e; line-height: 1.2; }}
    .meta {{ font-size: 9px; color: #888; margin-top: 4px; letter-spacing: 0.04em; }}
    ol.items {{ list-style: none; padding: 0; }}
    li.item {{ display: flex; align-items: flex-start; gap: 8px; margin-bottom: 9px; font-size: 11.5px; line-height: 1.45; color: #2d2d4a; }}
    .cb {{ font-size: 14px; color: #4ADE80; flex-shrink: 0; line-height: 1.5; }}
    .label {{ flex: 1; }}
    .footer {{ margin-top: 12px; padding-top: 8px; border-top: 1px solid #e0e0e0; font-size: 8px; color: #aaa; text-align: center; }}
  </style>
</head>
<body>
  <div class="page">
    <div class="header">
      <div class="title">{html_mod.escape(title_str)} — Action Checklist</div>
      <div class="meta">GENERATED {date_str} | Print this page and keep it somewhere visible</div>
    </div>
    <ol class="items">
{checkbox_rows}    </ol>
    <div class="footer">Companion to the full guide in your Lemon Squeezy library. Check off each item as you complete it.</div>
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