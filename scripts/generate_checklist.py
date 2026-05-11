#!/usr/bin/env python3
"""
Stage 5.5 — Checklist Generator
Takes a draft .md path, extracts key action items and creates a 1-page
printable checklist PDF in output/final_products/[slug]_CHECKLIST.pdf
"""
import sys, re, subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "output" / "final_products"

def extract_checklist_items(draft_path):
    """Extract actionable items from a draft markdown file."""
    content = Path(draft_path).read_text(encoding="utf-8")
    items = []
    
    # Extract bullet points and numbered action items
    for line in content.split("\n"):
        line = line.strip()
        # Match bullet points, numbered items, or action-oriented lines
        if re.match(r"^[-*]\s+\S", line) or re.match(r"^\d+\.\s+\S", line):
            # Clean and add
            clean = re.sub(r"^[-*]\s+", "", line)
            clean = re.sub(r"^\d+\.\s+", "", clean)
            # Skip if it's a section header or too short
            if len(clean) > 15 and not clean.startswith("#"):
                items.append(clean)
        # Also capture "Action:" or "Step:" prefixed lines
        elif re.search(r"(action|step|tip|warning|important)\s*[:\-]", line, re.I):
            clean = re.sub(r"^(action|step|tip|warning|important)\s*[:\-]\s*", "", line, re.I)
            if len(clean) > 10:
                items.append(clean)
    
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for item in items:
        norm = item.lower()[:80]
        if norm not in seen:
            seen.add(norm)
            deduped.append(item)
    
    return deduped[:15]  # Cap at 15 items

def generate_checklist_pdf(draft_path):
    """Generate a 1-page printable checklist PDF from a draft."""
    draft_path = Path(draft_path)
    slug = draft_path.stem
    checklist_path = OUTPUT_DIR / f"{slug}_CHECKLIST.pdf"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    items = extract_checklist_items(draft_path)
    if not items:
        # Fallback: create a basic checklist from the title
        title = slug.replace("-", " ").replace("_", " ").title()
        items = [f"Review {title} guide", "Identify your priority action step", 
                 "Complete the first action today", "Set reminder for step 2"]

    # Build HTML checklist
    title = slug.replace("-", " ").replace("_", " ").title()
    date_str = datetime.now().strftime("%B %d, %Y")
    
    checkbox_html = "\n".join([
        f'<li class="item"><span class="check">☐</span><span class="text">{item}</span></li>'
        for item in items
    ])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    body {{ font-family: 'Inter', sans-serif; margin: 0; padding: 24px; color: #1a1a2e; }}
    .header {{ border-bottom: 3px solid #1a1a2e; margin-bottom: 20px; padding-bottom: 12px; }}
    .title {{ font-size: 22px; font-weight: 700; margin: 0 0 4px 0; }}
    .subtitle {{ font-size: 11px; color: #666; margin: 0; }}
    .section {{ margin-bottom: 16px; }}
    .section-label {{ font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #888; margin-bottom: 6px; }}
    ol.items {{ margin: 0; padding: 0; list-style: none; }}
    li.item {{ display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; font-size: 12px; line-height: 1.4; }}
    .check {{ font-size: 16px; flex-shrink: 0; }}
    .text {{ flex: 1; }}
    .footer {{ margin-top: 16px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 9px; color: #999; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title">{title} — Action Checklist</div>
    <div class="subtitle">Generated {date_str} | Keep this page for quick reference</div>
  </div>
  <div class="section">
    <div class="section-label">Your Priority Actions</div>
    <ol class="items">
    {checkbox_html}
    </ol>
  </div>
  <div class="footer">
    Companion to the full guide in your Lemon Squeezy library. Keep this checklist handy — print it, pin it, use it.
  </div>
</body>
</html>"""

    try:
        import weasyprint
        wp_doc = weasyprint.HTML(string=html)
        wp_doc.write_pdf(str(checklist_path))
        size_kb = checklist_path.stat().st_size / 1024
        print(f"  ✅ Checklist generated: {checklist_path} ({size_kb:.0f} KB)")
        return str(checklist_path)
    except ImportError:
        print("  ⚠️  WeasyPrint not installed — trying pandoc fallback")
        return _pandoc_fallback(html, checklist_path)
    except Exception as e:
        print(f"  ❌ Checklist generation failed: {e}")
        return None

def _pandoc_fallback(html, output_path):
    """Pandoc fallback for PDF generation."""
    import tempfile, subprocess
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8") as f:
        f.write(html)
        tmp = f.name
    try:
        result = subprocess.run(
            ["pandoc", tmp, "-o", str(output_path), "--pdf-engine=weasyprint", "-V", "geometry:margin=0.75in"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"  ✅ Checklist via Pandoc: {output_path}")
            return str(output_path)
    except Exception as e:
        print(f"  ⚠️  Pandoc failed: {e}")
    finally:
        Path(tmp).unlink(missing_ok=True)
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_checklist.py /path/to/draft.md")
        sys.exit(1)
    result = generate_checklist_pdf(sys.argv[1])
    sys.exit(0 if result else 1)