#!/usr/bin/env python3
"""
Polished PDF Generator — WeasyPrint with enhanced CSS injection
================================================================
Applies the full CSS payload including dynamic product title per PDF.
Generates both main guide PDF + checklist PDF for each product.

Usage:
    python3 polish_pdfs.py [--products cat-litter contractor-scam new-cat]
"""
import sys, os, re, html as html_mod
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "output" / "final_products"
CSS_BASE = WORKSPACE / "products" / "assets" / "pdf_style.css"

# ── Base CSS (loaded from pdf_style.css) ────────────────────────────────────
def load_base_css() -> str:
    if CSS_BASE.exists():
        return CSS_BASE.read_text()
    return ""

# ── Extra CSS payload (appended to base CSS) ────────────────────────────────
def extra_css(product_title: str) -> str:
    # Escape the product title for use in CSS string content
    safe_title = html_mod.escape(product_title, quote=False)
    return f"""
/* ── POLISHED PDF ENHANCEMENTS ────────────────────────────────────────── */
@page {{
    size: A4;
    margin: 2cm;
    @bottom-right {{ content: "Page " counter(page); font-family: 'Inter', Georgia, serif; font-size: 9pt; color: #666; }}
    @bottom-left {{ content: "{safe_title}"; font-family: 'Inter', Georgia, serif; font-size: 9pt; color: #666; }}
}}

img {{ max-width: 100%; height: auto; display: block; margin: 1.5rem auto; }}
table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 1rem; }}
td, th {{ overflow-wrap: break-word; word-break: break-word; padding: 8pt; border: 1px solid #eee; }}
h1, h2, h3 {{ page-break-after: avoid; }}
table, blockquote {{ page-break-inside: avoid; }}
body {{ font-family: 'Inter', Georgia, serif; line-height: 1.6; }}
"""

# ── Markdown to HTML conversion (same as pipeline_manager.py) ───────────────
def md_to_html(md_content: str) -> str:
    import markdown
    md = markdown.Markdown(extensions=["extra", "meta", "toc"])
    return md.convert(md_content)

# ── Preprocess markdown (same as _preprocess_for_web in pipeline_manager.py) ─
def preprocess_md(md_text: str) -> str:
    """Normalize markdown for PDF/HTML output. Preserves structure."""
    lines = md_text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Normalize horizontal rules
        if re.match(r"^---+$", line.strip()):
            result.append("---")
            i += 1
            continue
        # Normalize ATX headings
        line = re.sub(r"^(#{1,6})\s*(.*?)(\s*#*)$", lambda m: m.group(1) + " " + m.group(2).rstrip(), line)
        # Skip purely computational lines (trend:, score:, etc.)
        stripped = line.strip()
        if re.match(r"^(trend|score|date|from|subject|to|reply-to):\s*", stripped, re.I):
            i += 1
            continue
        # Skip HTML comment blocks
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

# ── Wrap first h1 in cover div ────────────────────────────────────────────────
def wrap_cover(html_body: str) -> str:
    first_h1_match = re.search(r"(<h1[^>]*>.*?</h1>)", html_body, re.DOTALL)
    if first_h1_match:
        wrapped = f'<div class="cover">\n{first_h1_match.group(1)}\n</div>'
        html_body = html_body[:first_h1_match.start()] + wrapped + html_body[first_h1_match.end():]
    return html_body

# ── Build full HTML doc ───────────────────────────────────────────────────────
def build_html(body_content: str, css: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>\n{css}\n</style>
</head>
<body>
{body_content}
</body>
</html>"""

# ── Generate polished PDF ─────────────────────────────────────────────────────
def generate_polished_pdf(
    draft_path: Path,
    product_title: str,
    output_pdf: Path
) -> bool:
    """Generate a polished PDF with enhanced CSS. Returns True on success."""
    try:
        import weasyprint
    except ImportError:
        print("  ⚠️  WeasyPrint not available")
        return False

    # Read and preprocess markdown
    md_content = draft_path.read_text(encoding="utf-8")
    md_content = preprocess_md(md_content)

    # Convert to HTML
    html_body = md_to_html(md_content)
    html_body = wrap_cover(html_body)

    # Build CSS: base + extra
    base_css = load_base_css()
    extra = extra_css(product_title)
    full_css = base_css + extra

    # Generate PDF
    html_doc = build_html(html_body, full_css)
    wp_doc = weasyprint.HTML(string=html_doc)
    wp_doc.write_pdf(str(output_pdf))
    return True


# ── Product definitions ────────────────────────────────────────────────────────
PRODUCTS = {
    "cat-litter": {
        "draft": "products/drafts/cat-litter-box-rescue-guide_v1.md",
        "title": "Cat Litter Box Rescue Guide",
        "slug": "cat-litter-box-rescue-guide_v1",
    },
    "contractor-scam": {
        "draft": "products/drafts/contractor-scam-protection-guide_v1.md",
        "title": "Contractor Scam Protection Guide",
        "slug": "contractor-scam-protection-guide_v1",
    },
    "new-cat": {
        "draft": "products/drafts/new-cat-first-weeks-survival-guide_v1.md",
        "title": "New Cat First Weeks Survival Guide",
        "slug": "new-cat-first-weeks-survival-guide_v1",
    },
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Polished PDF Generator")
    parser.add_argument("--products", nargs="+",
                        choices=["cat-litter", "contractor-scam", "new-cat"],
                        help="Specific products to process (default: all)")
    args = parser.parse_args()

    targets = args.products if args.products else ["cat-litter", "contractor-scam", "new-cat"]

    print("=" * 60)
    print("Polished PDF Generator")
    print(f"Products: {targets}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for key in targets:
        if key not in PRODUCTS:
            print(f"❌ Unknown product: {key}")
            continue

        prod = PRODUCTS[key]
        draft_path = WORKSPACE / prod["draft"]

        if not draft_path.exists():
            print(f"❌ Draft not found: {draft_path}")
            continue

        print(f"\n  Processing: {prod['title']}")

        # ── Main PDF ────────────────────────────────────────────────────
        main_pdf = OUTPUT_DIR / f"{prod['slug']}.pdf"
        ok = generate_polished_pdf(draft_path, prod["title"], main_pdf)
        if ok and main_pdf.exists():
            size = main_pdf.stat().st_size / 1024
            print(f"  ✅ {main_pdf.name} ({size:.0f} KB)")
        else:
            print(f"  ❌ Failed: {main_pdf}")

        # ── Checklist PDF ───────────────────────────────────────────────
        import subprocess as sp
        cl_result = sp.run(
            ["python3", str(WORKSPACE / "scripts" / "generate_checklist.py"), str(draft_path)],
            capture_output=True, text=True, timeout=60
        )
        if cl_result.returncode == 0:
            cl_pdf = OUTPUT_DIR / f"{prod['slug']}_CHECKLIST.pdf"
            if cl_pdf.exists():
                size = cl_pdf.stat().st_size / 1024
                print(f"  ✅ {cl_pdf.name} ({size:.0f} KB)")
        else:
            print(f"  ⚠️  Checklist gen failed: {cl_result.stderr[:100]}")

    print("\n" + "=" * 60)
    print("All PDFs generated.")


if __name__ == "__main__":
    main()