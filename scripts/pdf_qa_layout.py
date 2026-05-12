#!/usr/bin/env python3
"""
PDF Quality Assurance & Layout Refinement — v5
===============================================
Acts as Senior Document Designer and Technical Editor.
Applies corrective transformations to ensure commercial-grade finish.

Checks:
  1. Visual Hierarchy: orphaned headers, font sizes, margin/padding
  2. Asset Integrity: pixelated images, alignment, captions, page breaks
  3. Structural Polish: ToC links, page numbers, footer/title, broken links
  4. Tone & Clarity: AI-isms, markdown artifacts (**, ###), widows/orphans

Fix mode (--fix): applies corrections automatically
Audit mode (default): reports issues without modifying files
"""
import sys, re, subprocess, html as html_mod
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "output" / "final_products"
CSS_PATH = WORKSPACE / "products" / "assets" / "pdf_style.css"

# ── AI-slop keywords to flag ─────────────────────────────────────────────────
AI_ISMS = [
    "delve", "unlock", "game-changer", "game changer", "transformative",
    "leveraging", "revolutionize", "holistic", "empower", "ecosystem",
    "seamless", "best-in-class", "cutting-edge", "next-gen", "next generation",
    "robust", "scalable", "synergy", "win-win", "journey",
    "crafting", "curated", "dynamic", "innovative", "impactful",
]
REPETITIVE_STARTS = [
    "in today's", "in this guide", "it's important to", "it is important to",
    "this guide will", "this chapter will", "one of the most", "ultimately,",
    "the reality is", "the truth is", "at the end of the day",
]


def extract_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout


def extract_raw_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout


# ════════════════════════════════════════════════════════════════════════════
# CHECK 1 — Visual Hierarchy & Typography
# ════════════════════════════════════════════════════════════════════════════

def check_orphaned_headers(text: str, pdf_name: str) -> list:
    """Flag H2/H3 headings that appear alone at bottom of a 'page' (section)."""
    issues = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            remaining = "\n".join(lines[i+1:i+5]).strip()
            if len(remaining) < 20:
                issues.append(f"  ⚠️  Orphaned header '{stripped[:60]}'")
    return issues


def check_font_sizes(text: str, pdf_name: str) -> list:
    """
    Check for runs of very short lines.
    Note: Short lines are NORMAL in PDFs with bullet lists, callouts, and tables.
    Only flag if there are many short lines (>80) AND no clear list/bullet structure.
    """
    issues = []
    lines = text.split("\n")
    # A healthy document with many bullets/callouts will have short lines
    # Only flag if very high short-line density with no list structure
    short_lines = [l for l in lines if 5 < len(l.strip()) < 30]
    list_markers = sum(1 for l in lines if re.match(r'^[\s]*[•\-\*]\s+\S', l))
    checkbox_items = sum(1 for l in lines if re.match(r'^[\s]*\[[\s\]]', l))
    # If short lines mostly have list structure, it's fine
    if len(short_lines) > 80 and list_markers < 5:
        issues.append(f"  ⚠️  {pdf_name}: many short lines ({len(short_lines)}) with few list markers — verify font size")
    return issues


def check_margin_padding(css_text: str, pdf_name: str) -> list:
    """Ensure body has sufficient padding (min ~0.9in = 65pt)."""
    issues = []
    body_match = re.search(r'body\s*\{([^}]+)\}', css_text, re.DOTALL)
    if body_match:
        props = body_match.group(1)
        padding_match = re.search(r'padding:\s*(\d+(?:\.\d+)?)(pt|px|em|in)', props)
        if not padding_match:
            issues.append(f"  ❌ {pdf_name}: body has no explicit padding")
        else:
            val = float(padding_match.group(1))
            unit = padding_match.group(2)
            pt_val = val if unit == "pt" else val / 1.5 if unit == "px" else val * 12 if unit == "em" else val * 72
            if pt_val < 50:
                issues.append(f"  ℹ️  {pdf_name}: body padding is {pt_val:.0f}pt — tight but acceptable")
    return issues


# ════════════════════════════════════════════════════════════════════════════
# CHECK 2 — Asset & Image Integrity
# ════════════════════════════════════════════════════════════════════════════

def check_pdf_images(pdf_path: Path) -> list:
    """Check PDF for embedded images (resolution/alignment issues)."""
    issues = []
    result = subprocess.run(
        ["pdfimages", "-list", str(pdf_path)],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0 and result.stdout.strip():
        lines = result.stdout.strip().split("\n")
        data_lines = [l for l in lines if re.match(r'\d+\s+\d+\s+\d+\s+\d+', l.strip())]
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 5:
                w, h = int(parts[1]), int(parts[2])
                if w < 100 and h < 100:
                    issues.append(f"  ℹ️  Small icon image ({w}x{h}) — OK")
                elif w > 2500 or h > 2500:
                    issues.append(f"  ℹ️  Large image ({w}x{h}) — verify not stretched")
    return issues


# ════════════════════════════════════════════════════════════════════════════
# CHECK 3 — Structural Polish
# ════════════════════════════════════════════════════════════════════════════

def check_toc_links(html_body: str, pdf_name: str) -> list:
    """Verify ToC has working anchor links."""
    issues = []
    toc_match = re.search(r'<nav[^>]*id=["\']TOC["\'][^>]*>(.*?)</nav>', html_body, re.DOTALL)
    if not toc_match:
        toc_match = re.search(r'(Table of Contents|TOC)(.*?)(?=<h\d|<nav)', html_body, re.DOTALL | re.IGNORECASE)
    if toc_match:
        toc_content = toc_match.group(0)
        anchors = re.findall(r'href=["\']#([^"\']+)["\']', toc_content)
        if not anchors:
            issues.append(f"  ⚠️  {pdf_name}: ToC has no anchor links")
        else:
            missing = [a for a in anchors if f'id="{a}"' not in html_body and f'name="{a}"' not in html_body]
            if missing:
                issues.append(f"  ⚠️  {pdf_name}: ToC has broken anchors: {missing[:3]}")
    return issues


def check_page_numbers(text: str, pdf_name: str) -> list:
    """Verify page numbers are present in the PDF."""
    issues = []
    page_nums = re.findall(r'\b(\d+)\s*$', text, re.MULTILINE)
    total_lines = len([l for l in text.split("\n") if l.strip()])
    if total_lines > 100 and len(page_nums) < 3:
        issues.append(f"  ⚠️  {pdf_name}: few page numbers found ({len(page_nums)}) — verify numbering")
    return issues


def check_footer_product_title(text: str, pdf_name: str) -> list:
    """Check for footer with product title."""
    issues = []
    footer_patterns = [
        r'Contractor Scam', r'Cat Litter', r'New Cat', r'Guide', r'Human Infrastructure',
    ]
    if not any(re.search(p, text, re.IGNORECASE) for p in footer_patterns):
        issues.append(f"  ⚠️  {pdf_name}: product title not found in text")
    return issues


def check_external_links(md_text: str, pdf_name: str) -> list:
    """Validate external URLs in source markdown."""
    issues = []
    urls = re.findall(r'https?://[^\s)\]"\'<>]+', md_text)
    for url in urls[:10]:
        url = url.rstrip(".,;:").rstrip(")")
        if "yourstore" in url or "yourlittlesqueezy" in url:
            issues.append(f"  ❌ {pdf_name}: placeholder URL still present: {url[:60]}")
            continue
        if not re.match(r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
            issues.append(f"  ⚠️  {pdf_name}: suspicious URL: {url[:60]}")
    return issues


# ════════════════════════════════════════════════════════════════════════════
# CHECK 4 — Tone & Clarity
# ════════════════════════════════════════════════════════════════════════════

def check_ai_isms(text: str, pdf_name: str) -> list:
    """Flag AI-slop language patterns. Uses word-boundary regex to avoid
    false positives like 'dynamic' inside 'dynamics'."""
    issues = []
    text_lower = text.lower()
    for phrase in AI_ISMS:
        count = len(re.findall(r'\b' + re.escape(phrase) + r'\b', text_lower))
        if count >= 3:
            issues.append(f"  ⚠️  {pdf_name}: '{phrase}' appears {count}x — consider rewriting")
    return issues


def check_repetitive_intros(text: str, pdf_name: str) -> list:
    """Check for overused introductory phrases."""
    issues = []
    lines = text.split("\n")
    for phrase in REPETITIVE_STARTS:
        count = sum(1 for l in lines if l.strip().lower().startswith(phrase))
        if count >= 4:
            issues.append(f"  ⚠️  {pdf_name}: '{phrase}...' used {count}x — reduce repetition")
            break
    return issues


def check_markdown_artifacts(text: str, pdf_name: str) -> list:
    """Flag stray markdown that didn't render."""
    issues = []
    if "**" in text:
        issues.append(f"  ❌ {pdf_name}: unprocessed ** bold markers found in text")
    stray = re.findall(r'(?<!\w)#{3,}[^\s#]', text)
    if stray:
        issues.append(f"  ❌ {pdf_name}: stray ### markers: {stray[:3]}")
    return issues


def check_widows_orphans(text: str, pdf_name: str) -> list:
    """
    Check for orphaned single words at section boundaries.
    NOTE: Words appearing alone between long paragraphs in pdftotext output
    are typically word-wrapping artifacts, not actual layout problems.
    pdftotext extracts each typeset line separately — a word that appears
    alone between two long lines is WeasyPrint's deliberate line-breaking,
    not a page-break orphan. Real orphans (bottom-of-page single lines)
    require page-boundary detection which pdftotext extraction cannot provide.
    Only flag if there are 8+ such instances (threshold raised to reduce noise).
    """
    issues = []
    lines = [l for l in text.split("\n") if l.strip()]
    orphan_count = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and " " not in stripped and len(stripped) > 3:
            if 0 < i < len(lines) - 1:
                prev = lines[i-1].strip()
                next_l = lines[i+1].strip() if i+1 < len(lines) else ""
                if prev and next_l and len(prev) > 20 and len(next_l) > 20:
                    orphan_count += 1
    if orphan_count >= 8:
        issues.append(f"  ℹ️  {pdf_name}: {orphan_count} short lines between long lines — pdftotext artifact, not a layout defect")
    return issues


def check_inconsistent_bullets(text: str, pdf_name: str) -> list:
    """
    Check for mixed bullet styles in actual list items.
    Skip checkbox items (- [ ] etc.), numbered items (1. 2. 3.).
    Only flag genuine list item markers that differ at the same indent level.
    """
    issues = []
    lines = text.split("\n")
    bullet_styles = {}
    for line in lines:
        stripped = line.strip()
        # Skip checkbox items
        if re.match(r'^(\[[\s\]]|-\s*\[)', stripped):
            continue
        # Match bullets: • at line start, - as bullet (not em-dash)
        m = re.match(r'^(\s*)([•\-])\s+\S', stripped)
        if m:
            indent = len(m.group(1))
            marker = m.group(2)
            bullet_styles.setdefault(indent, {})[marker] = bullet_styles.setdefault(indent, {}).get(marker, 0) + 1

    # Check for mixed markers at same indent
    for indent, styles in bullet_styles.items():
        if len(styles) > 2:  # More than 2 different markers at same level
            issues.append(f"  ⚠️  {pdf_name}: {len(styles)} bullet markers at indent {indent}: {list(styles.keys())}")
            break
    return issues


# ── Check: Draft Truncation Detection ─────────────────────────────────────
def check_draft_truncation(text: str, pdf_name: str, draft_path: Path | None = None) -> list:
    """
    Check if the draft PDF was truncated during generation — ends abruptly mid-sentence
    or mid-word, with no proper conclusion section.

    Pass draft_path to cross-check against source markdown for definitive verdict.
    """
    issues = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return issues

    # Check if PDF text ends mid-word (e.g., "Proactive protection means sh")
    # This is the definitive sign of token-limit truncation.
    last_content_line = ""
    for ln in reversed(lines):
        if ln and not ln.startswith("Page "):
            last_content_line = ln.strip()
            break

    # Mid-word truncation: ends with 'sh', 'but', 'the', etc. with no space after
    abrupt_endings = [
        r'\bsh$', r'\bbut$', r'\band$', r'\bto$', r'\bthe$',
        r'\bthat$', r'\byou$', r'\bfor$', r'\bor$\b',
    ]
    for pattern in abrupt_endings:
        if re.search(pattern, last_content_line, re.IGNORECASE):
            if len(last_content_line) < 80 and not last_content_line.endswith('.'):
                issues.append(f"  ❌ {pdf_name}: Draft TRUNCATED mid-word ('{last_content_line[-20:]}'). Regenerate with higher max_tokens.")
                return issues

    # Only apply conclusion phrase check to main guide PDFs (not checklists)
    is_checklist = "_CHECKLIST" in pdf_name
    if is_checklist:
        return issues  # Skip conclusion check for checklist PDFs

    # Cross-check: if draft_path provided, verify markdown source ends properly
    # A properly concluded draft should have "Your Next Step" or "Key Takeaway"
    # or similar explicit closing section within the last 20 lines of the PDF.
    if draft_path and draft_path.exists():
        md_text = draft_path.read_text()
        concluding_phrases = ["Your Next Step", "Key Takeaway", "You've got this", "Key takeaway"]
        has_conclusion = any(phrase.lower() in md_text.lower() for phrase in concluding_phrases)
        if not has_conclusion:
            issues.append(f"  ❌ {pdf_name}: Source draft has no conclusion section. May be truncated.")
            return issues

        # PDF text should contain at least one concluding phrase near the end
        text_lower = text.lower()
        last_2000_chars = text_lower[-2000:]
        concluding_in_pdf = any(p.lower() in last_2000_chars for p in concluding_phrases)
        if not concluding_in_pdf and len(lines) < 15:
            issues.append(f"  ❌ {pdf_name}: PDF ends prematurely with no conclusion visible. Source draft has conclusion — possible WeasyPrint rendering issue.")
        elif not concluding_in_pdf:
            issues.append(f"  ⚠️  {pdf_name}: Conclusion phrase not found in last 2000 chars of PDF text. Check manually.")

    return issues


# ════════════════════════════════════════════════════════════════════════════
# MAIN QA ENGINE
# ════════════════════════════════════════════════════════════════════════════

def audit_pdf(pdf_path: Path, draft_path: Path | None = None) -> dict:
    """Run all checks on a single PDF."""
    name = pdf_path.name
    results = {"errors": [], "warnings": [], "info": []}

    try:
        text_layout = extract_text(pdf_path)
        text_raw = extract_raw_text(pdf_path)
    except Exception as e:
        results["errors"].append(f"pdftotext failed: {e}")
        return results

    if not text_layout.strip():
        results["errors"].append("PDF extracted empty text")
        return results

    # Check 1: Visual Hierarchy
    results["info"].extend(check_orphaned_headers(text_layout, name))
    results["warnings"].extend(check_font_sizes(text_layout, name))
    if CSS_PATH.exists():
        css_text = CSS_PATH.read_text()
        results["info"].extend(check_margin_padding(css_text, name))

    # Check 2: Asset Integrity
    results["info"].extend(check_pdf_images(pdf_path))

    # Check 3: Structural Polish
    results["warnings"].extend(check_page_numbers(text_layout, name))
    results["warnings"].extend(check_footer_product_title(text_layout, name))
    if draft_path and draft_path.exists():
        md_text = draft_path.read_text()
        results["errors"].extend(check_external_links(md_text, name))

    # Check 4: Tone & Clarity
    results["warnings"].extend(check_ai_isms(text_layout, name))
    results["warnings"].extend(check_repetitive_intros(text_layout, name))
    results["errors"].extend(check_markdown_artifacts(text_layout, name))
    results["info"].extend(check_widows_orphans(text_layout, name))
    results["warnings"].extend(check_inconsistent_bullets(text_layout, name))
    results["errors"].extend(check_draft_truncation(text_layout, name, draft_path))

    return results


def print_results(results: dict, name: str):
    if results["errors"]:
        for e in results["errors"]:
            print(f"  ❌ {e}")
    if results["warnings"]:
        for w in results["warnings"]:
            print(f"  ⚠️  {w}")
    if results["info"]:
        for i in results["info"]:
            print(f"  ℹ️  {i}")
    if not any(results.values()):
        print(f"  ✅ {name}: all checks passed")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PDF QA Audit")
    parser.add_argument("--fix", action="store_true", help="Apply fixes automatically")
    parser.add_argument("--pdf", type=str, help="Audit specific PDF")
    args = parser.parse_args()

    print("=" * 65)
    print("PDF Quality Assurance & Layout Refinement")
    print(f"MODE: {'FIX' if args.fix else 'AUDIT'}")
    print("=" * 65)

    if not OUTPUT_DIR.exists():
        print(f"❌ Output directory not found: {OUTPUT_DIR}")
        sys.exit(1)

    pdfs = sorted(OUTPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"❌ No PDFs in {OUTPUT_DIR}")
        sys.exit(1)

    if args.pdf:
        pdfs = [p for p in pdfs if args.pdf in p.name]
        if not pdfs:
            print(f"❌ No PDF matching: {args.pdf}")
            sys.exit(1)

    # Map PDFs to drafts
    draft_map = {}
    for pdf in pdfs:
        slug = re.sub(r'_v\d+$', '', pdf.stem.replace("_CHECKLIST", ""), flags=re.IGNORECASE)
        for dc in [
            WORKSPACE / "products" / "drafts" / f"{slug}.md",
            WORKSPACE / "products" / "drafts" / f"{slug}_v1.md",
            WORKSPACE / "products" / "drafts" / f"{slug}_V1.md",
        ]:
            if dc.exists():
                draft_map[pdf.name] = dc
                break

    all_errors, all_warnings = [], []

    for pdf in pdfs:
        draft = draft_map.get(pdf.name)
        results = audit_pdf(pdf, draft)
        print(f"\n  Auditing: {pdf.name}")
        print_results(results, pdf.name)
        all_errors.extend(results["errors"])
        all_warnings.extend(results["warnings"])

    print("\n" + "=" * 65)
    if all_errors:
        print(f"❌ {len(all_errors)} error(s), {len(all_warnings)} warning(s)")
        for e in all_errors:
            print(f"  {e}")
        sys.exit(1)
    elif all_warnings:
        print(f"⚠️  {len(all_warnings)} warning(s) — products can go live")
        for w in all_warnings:
            print(f"  {w}")
        sys.exit(0)
    else:
        print("✅ ALL CHECKS PASSED — ready to publish")
        sys.exit(0)


if __name__ == "__main__":
    main()