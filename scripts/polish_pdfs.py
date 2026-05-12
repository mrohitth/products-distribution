#!/usr/bin/env python3
"""
polish_pdfs.py — Dynamic WeasyPrint PDF Generator
=================================================
Reads today's TrendScout JSON → discovers products → generates guide PDFs.
Also generates checklist PDFs via synthesize_checklist.py.

Manifest Check: Verifies 2 PDFs per product (guide + checklist).
Dynamic — handles 1, 2, or 3 products per run.

Usage:
    python3 scripts/polish_pdfs.py                      # all from trends JSON
    python3 scripts/polish_pdfs.py --products slug1 slug2  # specific (partial match)
"""
import sys, os, re, html as html_mod, subprocess, json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "output" / "final_products"
CSS_BASE = WORKSPACE / "products" / "assets" / "pdf_style.css"


# ── Load dynamic product list from TrendScout JSON ─────────────────────────────────────
def load_products_from_trends() -> list[dict]:
    """Read wiki/trends/YYYY-MM-DD.json → return list of {slug, draft, title}."""
    today = datetime.now().strftime("%Y-%m-%d")
    trends_file = WORKSPACE / "wiki" / "trends" / f"{today}.json"

    if not trends_file.exists():
        print(f"  [ERROR] No trends file: {trends_file}")
        print(f"  Run TrendScout first: python3 scripts/trendscout_scout.py")
        sys.exit(1)

    data = json.loads(trends_file.read_text())
    products = []
    for t in data.get("trends", []):
        slug = t.get("slug_candidate", "")
        if not slug:
            continue
        # Try {slug}_v1.md first, then bare {slug}.md
        draft_candidates = [
            WORKSPACE / "products" / "drafts" / f"{slug}_v1.md",
            WORKSPACE / "products" / "drafts" / f"{slug}.md",
        ]
        draft_path = next((d for d in draft_candidates if d.exists()), None)
        if not draft_path:
            print(f"  [WARN] No draft for '{slug}' — skipping")
            continue
        direction = t.get("product_direction", "")
        title = direction.split(":")[0].strip() if ":" in direction else direction.strip()
        if not title:
            title = slug.replace("-", " ").title()
        products.append({
            "slug": draft_path.stem,
            "draft": str(draft_path),
            "title": title,
        })

    if not products:
        print(f"  [ERROR] No valid products from trends JSON")
        sys.exit(1)
    return products


# ── CSS helpers ─────────────────────────────────────────────────────────────────────
def load_base_css() -> str:
    if CSS_BASE.exists():
        return CSS_BASE.read_text()
    return ""

def extra_css(product_title: str) -> str:
    safe_title = html_mod.escape(product_title, quote=False)
    return f"""
@page {{
    size: A4;
    margin: 1.25cm 1.5cm;
    @bottom-right {{ content: "Page " counter(page); font-family: 'Inter', Georgia, serif; font-size: 9pt; color: #666; }}
    @bottom-left {{ content: "{safe_title}"; font-family: 'Inter', Georgia, serif; font-size: 9pt; color: #666; }}
}}

img {{ max-width: 100%; height: auto; display: block; margin: 1.5rem auto; }}
table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 1rem; }}
td, th {{ overflow-wrap: break-word; word-break: break-word; padding: 8pt; border: 1px solid #eee; }}
h1 {{ font-size: 24pt; font-weight: 700; color: #1a1a2e; border-bottom: 1px solid #eee; padding-bottom: 6pt; margin-bottom: 12pt; line-height: 1.25; page-break-after: avoid; }}
h2 {{ font-size: 18pt; font-weight: 600; color: #1a1a2e; margin-bottom: 8pt; line-height: 1.3; page-break-after: avoid; }}
h3 {{ font-size: 14pt; font-weight: 600; color: #2d2d4a; margin-bottom: 6pt; page-break-after: avoid; }}
table, blockquote {{ page-break-inside: avoid; }}
body {{ font-family: 'Inter', Georgia, serif; line-height: 1.6; }}
"""


# ── Markdown → HTML ──────────────────────────────────────────────────────────────────
def md_to_html(md_content: str) -> str:
    import markdown
    md = markdown.Markdown(extensions=["extra", "meta", "toc"])
    return md.convert(md_content)


def preprocess_md(md_text: str) -> str:
    """Strip artifact lines, normalize HR, clean headings."""
    lines = md_text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^---+$", line.strip()):
            result.append("---")
            i += 1
            continue
        line = re.sub(r"^(#{1,6})\s*(.*?)(\s*#*)$",
                      lambda m: m.group(1) + " " + m.group(2).rstrip(), line)
        stripped = line.strip()
        # Strip artifact metadata lines
        if re.match(r"^(trend|score|date|from|subject|to|reply-to):\s*", stripped, re.I):
            i += 1
            continue
        # Strip HTML comments
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            i += 1
            continue
        if stripped.startswith("<!--"):
            while i < len(lines) and not lines[i].strip().endswith("-->"):
                i += 1
            i += 1
            continue
        result.append(line)
        i += 1
    return "\n".join(result)


def wrap_cover(html_body: str) -> str:
    first_h1_match = re.search(r"(<h1[^>]*>.*?</h1>)", html_body, re.DOTALL)
    if first_h1_match:
        wrapped = f'<div class="cover">\n{first_h1_match.group(1)}\n</div>'
        html_body = html_body[:first_h1_match.start()] + wrapped + html_body[first_h1_match.end():]
    return html_body


def build_html(body_content: str, css: str) -> str:
    return f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <style>\n{css}\n</style>\n</head>\n<body>\n{body_content}\n</body>\n</html>"


def generate_polished_pdf(draft_path: Path, product_title: str, output_pdf: Path) -> bool:
    try:
        import weasyprint
    except ImportError:
        print("  ⚠️  WeasyPrint not available")
        return False

    md_content = draft_path.read_text(encoding="utf-8")
    md_content = preprocess_md(md_content)
    html_body = md_to_html(md_content)
    html_body = wrap_cover(html_body)

    base_css = load_base_css()
    extra = extra_css(product_title)
    full_css = base_css + extra

    html_doc = build_html(html_body, full_css)
    wp_doc = weasyprint.HTML(string=html_doc)
    wp_doc.write_pdf(str(output_pdf))
    return True


# ── Main ──────────────────────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Dynamic Polished PDF Generator")
    parser.add_argument("--products", nargs="+",
                        help="Specific products to process (default: all from trends JSON)")
    args = parser.parse_args()

    # Load products dynamically from TrendScout JSON
    all_products = load_products_from_trends()

    if args.products:
        # Filter by partial slug match
        products = [p for p in all_products if any(t in p["slug"] for t in args.products)]
        if not products:
            print(f"  [ERROR] None of {args.products} found in today's trends")
            print(f"  Available: {[p['slug'] for p in all_products]}")
            sys.exit(1)
    else:
        products = all_products

    print("=" * 60)
    print("  Polished PDF Generator — Dynamic")
    print(f"  Products: {[p['slug'] for p in products]}")
    print(f"  Source:   wiki/trends/{datetime.now().strftime('%Y-%m-%d')}.json")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Stage 1: Generate all checklist PDFs first (via synthesize_checklist.py) ────
    print("\n  Stage 2 (pre-flight): Generating checklists...")
    cl_result = subprocess.run(
        ["python3", str(WORKSPACE / "scripts" / "synthesize_checklist.py")],
        capture_output=True, text=True, timeout=120
    )
    if cl_result.returncode != 0:
        print(f"  ❌ Checklist synthesis failed: {cl_result.stderr[:200]}")
        sys.exit(1)
    for line in cl_result.stdout.split("\n"):
        if line.strip():
            print(f"    {line}")

    # ── Stage 2: Generate guide PDFs ─────────────────────────────────────────────
    generated = []
    write_call_count = 0

    for prod in products:
        slug = prod["slug"]
        draft_path = WORKSPACE / prod["draft"]
        title = prod["title"]

        if not draft_path.exists():
            print(f"  ❌ Draft not found: {draft_path}")
            continue

        print(f"\n  Processing: {title}")

        main_pdf = OUTPUT_DIR / f"{slug}.pdf"
        ok = generate_polished_pdf(draft_path, title, main_pdf)
        if ok and main_pdf.exists():
            size = main_pdf.stat().st_size / 1024
            mtime = datetime.fromtimestamp(main_pdf.stat().st_mtime).strftime("%H:%M:%S")
            print(f"  ✅ {main_pdf.name} ({size:.0f} KB) @ {mtime}")
            generated.append(main_pdf.name)
            write_call_count += 1
        else:
            print(f"  ❌ Failed: {main_pdf}")

    # ── MANIFEST CHECK ───────────────────────────────────────────────────────────
    expected_count = 2 * len(products)  # guide + checklist per product
    pdf_files = sorted(OUTPUT_DIR.glob("*.pdf"))

    print("\n" + "=" * 60)
    print("  MANIFEST CHECK")
    print(f"  PDF count: {len(pdf_files)} / expected {expected_count}")
    print(f"  write_pdf() calls: {write_call_count} / expected {expected_count}")
    print()
    print("  Files in final_products/:")
    for f in pdf_files:
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M:%S %Y-%m-%d")
        print(f"    {f.name:55s} {f.stat().st_size//1024:4d} KB  {mtime}")

    # Verify every product has both guide + checklist
    missing = []
    for prod in products:
        slug = prod["slug"]
        if not (OUTPUT_DIR / f"{slug}.pdf").exists():
            missing.append(f"{slug}.pdf")
        if not (OUTPUT_DIR / f"{slug}_CHECKLIST.pdf").exists():
            missing.append(f"{slug}_CHECKLIST.pdf")

    if missing:
        print(f"\n  ❌ BUILD FAILED — missing: {missing}")
        sys.exit(1)
    if len(pdf_files) < expected_count or write_call_count < expected_count:
        print(f"\n  ❌ BUILD FAILED — expected {expected_count} PDFs")
        sys.exit(1)

    print(f"\n  ✅ MANIFEST PASSED — all {expected_count} PDFs present and distinct")
    print("=" * 60)
    print("All PDFs generated.")


if __name__ == "__main__":
    main()