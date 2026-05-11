#!/usr/bin/env python3
"""
QA Audit Script for TrendScout PDFs
Runs automated checks on all final_products PDFs before pushing to GitHub.
Exits 0 if all checks pass, 1 if any error found (warnings are non-blocking).
"""
import sys, re, subprocess
from pathlib import Path

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "output" / "final_products"

ISSUES = []
WARNINGS = []


def extract_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout


def check_literal_double_asterisks(text: str, pdf_name: str):
    """Check for literal ** markers that shouldn't appear in rendered output."""
    lines = text.split("\n")
    for i, line in enumerate(lines, 1):
        if line.strip() in ("", "\f"):
            continue
        if "**" in line:
            ISSUES.append(f"❌ {pdf_name} line {i}: literal ** found: {line[:80]!r}")


def check_blank_lines(text: str, pdf_name: str):
    """Check for 3+ consecutive blank lines (layout gap)."""
    lines = text.split("\n")
    blank_count = 0
    for line in lines:
        stripped = line.strip()
        if stripped == "" or stripped == "\f":
            blank_count += 1
        else:
            if blank_count >= 3:
                WARNINGS.append(f"⚠️  {pdf_name}: {blank_count} consecutive blank lines")
            blank_count = 0


def check_checklist_structure(text: str, pdf_name: str):
    """Verify checklist has proper checkbox items. Skip for main guides."""
    if "_CHECKLIST" not in pdf_name:
        return
    found_items = sum(1 for line in text.split("\n") if "☐" in line)
    if found_items == 0:
        ISSUES.append(f"❌ {pdf_name}: no checkbox items found")
    else:
        print(f"  ✅ {pdf_name}: {found_items} checkbox items")


def check_minimum_content(text: str, pdf_name: str, min_chars: int = 300):
    """Ensure PDF has meaningful content."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) < min_chars:
        ISSUES.append(f"❌ {pdf_name}: content too short ({len(cleaned)} chars)")


def check_asterisk_residue(text: str, pdf_name: str):
    """Check for any remaining unpaired asterisks that indicate bad bold stripping."""
    # Count lines with asterisks (excluding known good ones like URLs)
    for line in text.split("\n"):
        if line.strip() in ("", "\f"):
            continue
        if "*" in line:
            # Skip lines that are clearly URLs or starred emphasis we want to keep
            if "http" in line.lower() or "//" in line:
                continue
            # Flag any line with 2+ asterisks that didn't get stripped
            asterisk_count = line.count("*")
            if asterisk_count >= 2:
                # Filter out form feed and page numbers
                cleaned_line = re.sub(r"\f", "", line).strip()
                if cleaned_line and not re.match(r"^\d+$", cleaned_line):
                    ISSUES.append(f"❌ {pdf_name}: unstripped asterisks: {cleaned_line[:80]!r}")


def check_title_present(text: str, pdf_name: str):
    """Ensure PDF has a title."""
    lines = [l.strip() for l in text.split("\n") if l.strip() and l.strip() != "\f"]
    if not lines:
        ISSUES.append(f"❌ {pdf_name}: no title found — PDF may be empty")


def audit_pdf(pdf_path: Path) -> bool:
    name = pdf_path.name
    print(f"\n  Auditing: {name}")
    try:
        text = extract_text(pdf_path)
    except Exception as e:
        ISSUES.append(f"❌ {name}: pdftotext failed: {e}")
        return False
    if not text.strip():
        ISSUES.append(f"❌ {name}: PDF extracted empty text")
        return False

    check_literal_double_asterisks(text, name)
    check_blank_lines(text, name)
    check_checklist_structure(text, name)
    check_minimum_content(text, name)
    check_asterisk_residue(text, name)
    check_title_present(text, name)

    my_issues = [i for i in ISSUES if name in i]
    my_warnings = [i for i in WARNINGS if name in i]
    if my_issues:
        return False
    if my_warnings:
        print(f"  ⚠️  {name}: {len(my_warnings)} warning(s)")
    return True


def main():
    print("=" * 60)
    print("TrendScout PDF QA Audit")
    print("=" * 60)

    if not OUTPUT_DIR.exists():
        print(f"❌ Output directory not found: {OUTPUT_DIR}")
        sys.exit(1)

    pdfs = sorted(OUTPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"❌ No PDFs found in {OUTPUT_DIR}")
        sys.exit(1)

    print(f"\nFound {len(pdfs)} PDFs to audit:")
    all_clean = True
    for pdf in pdfs:
        clean = audit_pdf(pdf)
        if not clean:
            all_clean = False

    print("\n" + "=" * 60)
    if ISSUES:
        print(f"ERRORS: {len(ISSUES)}")
        for issue in ISSUES:
            print(f"  {issue}")
        print(f"\nWARNINGS: {len(WARNINGS)}")
        for w in WARNINGS:
            print(f"  {w}")
        sys.exit(1)
    else:
        print("✅ ALL CHECKS PASSED — PDFs are clean")
        if WARNINGS:
            for w in WARNINGS:
                print(f"  {w}")
        sys.exit(0)


if __name__ == "__main__":
    main()