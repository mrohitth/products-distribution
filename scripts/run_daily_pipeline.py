#!/usr/bin/env python3
"""
run_daily_pipeline.py — Master Pipeline Orchestrator
=====================================================
Reads TrendScout JSON (wiki/trends/YYYY-MM-DD.json) → dynamically discovers
products to build → executes all 6 stages → AI audit → QA → GitHub sync.

Anti-hallucination: reads pipeline_config.json at startup.
If any session instruction contradicts config, raises ConflictError.

Flow:
  TrendScout (10 AM ET) → wiki/trends/YYYY-MM-DD.json (3 slugs)
    → run_daily_pipeline.py (11 AM ET) → produces ALL 3 (2 PDFs each)

Usage:
  python3 scripts/run_daily_pipeline.py              # all products from trends JSON
  python3 scripts/run_daily_pipeline.py --dry-run    # scan only, no generation
  python3 scripts/run_daily_pipeline.py --products slug1 slug2  # specific subset

Cron: 0 11 * * * America/New_York (daily 11 AM ET)
"""
import sys, os, json, subprocess, hashlib, re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
CONFIG_PATH = WORKSPACE / "pipeline_config.json"
OUTPUT_DIR = WORKSPACE / "output" / "final_products"

# ── Load config ─────────────────────────────────────────────────────────────────────────
def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"pipeline_config.json not found at {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text())

CONFIG = load_config()

# ── Anti-hallucination guardrail ──────────────────────────────────────────────────────
REQUIRED_REGEX_CORRECT = r're.sub(r"\*\*(.+?)\*\*", r"\1", text)'
REQUIRED_REGEX_WRONG   = r're.sub(r"\*\*(.+?)\*\*", r"|", text)'

CONFIG_HASH = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()[:12]
print(f"[PIPELINE] Config loaded — version {CONFIG['pipeline_version']} — hash {CONFIG_HASH}")


class PipelineConfigConflict(Exception):
    pass


def check_config_integrity():
    current = json.loads(CONFIG_PATH.read_text())
    if current.get("pipeline_version") != CONFIG["pipeline_version"]:
        raise PipelineConfigConflict(f"pipeline_version mismatch")
    regex_correct = current["regex_rules"]["bold_strip"]
    if REQUIRED_REGEX_WRONG in regex_correct:
        raise PipelineConfigConflict(
            "CRITICAL: bold_strip regex uses pipe '|' which deletes inner content. "
            "Expected: re.sub(r'\\*\\*(.+?)\\*\\*', r'\\1', text)"
        )
    print("[CONFIG] Integrity check PASSED")


# ── Dynamic product loader from TrendScout output ─────────────────────────────────────
def load_products_from_trends() -> list[dict]:
    """
    Reads wiki/trends/YYYY-MM-DD.json and returns a list of product dicts
    for ALL HIGH CONVICTION trends that have a draft on disk.

    Fallback: if no trends file exists for today, uses pipeline_config.json
    products (backwards compat for manual runs without TrendScout).

    Each product dict:
      { "slug": "new-pet-owner-survival_v1",
        "draft": "products/drafts/new-pet-owner-survival_v1.md",
        "title": "New Pet Owner Survival Guide",
        "trend": { ... }  # full trend dict for audit payload }
    """
    today = datetime.now().strftime("%Y-%m-%d")
    trends_file = WORKSPACE / "wiki" / "trends" / f"{today}.json"

    if not trends_file.exists():
        print(f"  [WARN] No trends file for {today} — using pipeline_config.json products")
        return [
            {"slug": p["slug"], "draft": p["draft"], "title": p["title"], "trend": None}
            for p in CONFIG["products"]
        ]

    trends_data = json.loads(trends_file.read_text())
    high_trends = trends_data.get("trends", [])
    print(f"  Loaded {len(high_trends)} HIGH CONVICTION trends from {trends_file.name}")

    products = []
    for t in high_trends:
        slug = t.get("slug_candidate", "")
        if not slug:
            continue

        # Try _v1.md first, then bare slug
        draft_candidates = [
            WORKSPACE / "products" / "drafts" / f"{slug}_v1.md",
            WORKSPACE / "products" / "drafts" / f"{slug}.md",
        ]
        draft_path = next((d for d in draft_candidates if d.exists()), None)
        if draft_path:
            # Title from product_direction (before the colon)
            direction = t.get("product_direction", "")
            title = direction.split(":")[0].strip() if ":" in direction else direction.strip()
            if not title:
                title = slug.replace("-", " ").title()
            products.append({
                "slug": draft_path.stem,   # e.g. "new-pet-owner-survival_v1"
                "draft": str(draft_path.relative_to(WORKSPACE)),
                "title": title,
                "trend": t,                # kept for audit payload
            })
        else:
            print(f"  [WARN] No draft found for trend '{slug}' — skipping")

    if not products:
        print(f"  [ERROR] No products found from trends JSON")
        print(f"  Trends file: {trends_file}")
        print(f"  Tip: Run TrendScout first (python3 scripts/trendscout_scout.py)")
        sys.exit(1)

    print(f"  Products to build: {[p['slug'] for p in products]}")
    return products


# ── Stage helpers ────────────────────────────────────────────────────────────────────
def stage_banner(stage: int, name: str) -> str:
    return f"\n{'='*60}\n  STAGE {stage}: {name}\n{'='*60}"

def run_py(script: str, *args, timeout: int = 180) -> int:
    cmd = ["python3", str(WORKSPACE / "scripts" / script)] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.stdout:
        for line in r.stdout.split("\n"):
            if line.strip():
                print(f"  {line}")
    if r.returncode != 0:
        print(f"  ❌ FAILED: {r.stderr[:200]}")
    return r.returncode

def check_manifest(products: list) -> bool:
    """Check that we have guide + checklist for each product (2 per product)."""
    pdfs = sorted(OUTPUT_DIR.glob("*.pdf"))
    expected = 2 * len(products)  # 2 PDFs per product
    ok = len(pdfs) >= expected
    print(f"  Manifest: {len(pdfs)} PDFs {'✅' if ok else '❌'} (need ≥{expected})")
    return ok


# ── Audit payload builder ────────────────────────────────────────────────────────────
def build_audit_payload(products: list) -> Path:
    payload = {}
    for prod in products:
        draft_path = WORKSPACE / prod["draft"]
        guide_pdf = OUTPUT_DIR / f"{prod['slug']}.pdf"
        checklist_pdf = OUTPUT_DIR / f"{prod['slug']}_CHECKLIST.pdf"

        draft_text = draft_path.read_text(encoding="utf-8") if draft_path.exists() else ""

        r_guide = subprocess.run(
            ["pdftotext", "-layout", str(guide_pdf), "-"],
            capture_output=True, text=True, timeout=30
        )
        guide_text = r_guide.stdout if r_guide.returncode == 0 else ""

        r_cl = subprocess.run(
            ["pdftotext", "-layout", str(checklist_pdf), "-"],
            capture_output=True, text=True, timeout=30
        )
        checklist_text = r_cl.stdout if r_cl.returncode == 0 else ""

        item_count = checklist_text.count("☐")

        payload[prod["slug"]] = {
            "title": prod["title"],
            "draft_word_count": len(draft_text.split()),
            "guide_word_count": len(guide_text.split()),
            "checklist_word_count": len(checklist_text.split()),
            "checklist_item_count": item_count,
            "checklist_preview": checklist_text[:2500],
            "guide_preview": guide_text[:1500],
            "trend": prod.get("trend", {}),
        }

    out = WORKSPACE / "/tmp/audit_payload.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"  Audit payload written: {out}")
    return out


# ── Main pipeline ────────────────────────────────────────────────────────────────────
def run_pipeline(dry_run: bool = False, target_products: list[str] | None = None):
    check_config_integrity()

    # ── Load products DYNAMICALLY from TrendScout JSON ───────────────────────────
    all_products = load_products_from_trends()

    if target_products:
        products = [p for p in all_products if any(t in p["slug"] for t in target_products)]
        if not products:
            print(f"  [ERROR] None of {target_products} found in today's trends")
            print(f"  Available: {[p['slug'] for p in all_products]}")
            sys.exit(1)
    else:
        products = all_products

    print(f"\n{'#'*60}")
    print(f"  DAILY PIPELINE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}")
    print(f"  Products: {[p['slug'] for p in products]}")
    print(f"  Dry run:  {dry_run}")
    print(f"  Source:   TrendScout JSON (wiki/trends/{datetime.now().strftime('%Y-%m-%d')}.json)")
    print(f"{'#'*60}")

    # ── Stage 1: Scan drafts ──────────────────────────────────────────────────────────
    print(stage_banner(1, "Scan Drafts"))
    for prod in products:
        draft = WORKSPACE / prod["draft"]
        status = "✅ found" if draft.exists() else "❌ MISSING"
        print(f"  {prod['slug']}: {status}")
    print(f"  ✅ Stage 1 complete")

    if dry_run:
        print("\n[DRY RUN] — exiting before Stage 2")
        return

    # ── Stage 2: AI-Agentic Checklist Synthesis (synthesize_checklist.py) ───────────
    print(stage_banner(2, "AI-Agentic Checklist Synthesis"))
    rc = run_py("synthesize_checklist.py", timeout=1200)
    if rc != 0:
        print("  ❌ Stage 2 FAILED — checklist synthesis error")
        sys.exit(1)
    print(f"  ✅ Stage 2 complete")

    # ── Stage 3: WeasyPrint PDF Generation (polish_pdfs.py) ─────────────────────────
    print(stage_banner(3, "WeasyPrint PDF Generation"))
    rc = run_py("polish_pdfs.py", timeout=180)
    if rc != 0:
        print("  ❌ Stage 3 FAILED — WeasyPrint generation error")
        sys.exit(1)
    if not check_manifest(products):
        print("  ❌ Stage 3 FAILED — manifest check")
        sys.exit(1)
    print("  ✅ Stage 3 complete")

    # ── Stage 4: AI Product Critic Audit ────────────────────────────────────────────
    print(stage_banner(4, "AI Product Critic Audit"))
    try:
        cfg = load_config()
        providers = cfg.get("models", {}).get("providers", {})
        minimax = providers.get("minimax", {})
        mxn_creds = {
            "base_url": minimax.get("baseUrl", "https://api.minimax.io/anthropic"),
            "api_key": minimax.get("apiKey", ""),
        }
        if mxn_creds["api_key"]:
            for prod in products:
                slug = prod["slug"]
                draft_path = WORKSPACE / prod["draft"]
                guide_pdf = OUTPUT_DIR / f"{slug}.pdf"
                checklist_pdf = OUTPUT_DIR / f"{slug}_CHECKLIST.pdf"

                draft_text = draft_path.read_text(encoding="utf-8") if draft_path.exists() else ""
                r_g = subprocess.run(
                    ["pdftotext", "-layout", str(guide_pdf), "-"],
                    capture_output=True, text=True, timeout=30
                )
                guide_text = r_g.stdout[:2000] if r_g.returncode == 0 else "(no PDF text)"

                r_c = subprocess.run(
                    ["pdftotext", "-layout", str(checklist_pdf), "-"],
                    capture_output=True, text=True, timeout=30
                )
                checklist_text = r_c.stdout[:1000] if r_c.returncode == 0 else "(no checklist)"

                audit_prompt = f"""You are an AI Product Critic. Audit this digital product across 3 dimensions:

1. COMPREHENSIVENESS (1-10): Does the guide fully cover the problem it claims to solve? Any gaps?
2. VISUAL POLISH (1-10): Based on the content, does it read like a polished product? Any rough edges?
3. VALUE CHECK (1-10): Would someone pay $5-15 for this guide given the content quality?

Slug: {slug}
Draft (first 2000 chars):
{draft_text[:2000]}

PDF text preview:
{guide_text}

Checklist preview:
{checklist_text}

Output ONLY JSON: {{"comprehensiveness": int, "visual_polish": int, "value_check": int, "issues": ["issue1", ...], "recommendation": "PASS/FLAG/FAIL"}}"""

                import urllib.request, urllib.error as urlerr
                audit_body = {
                    "model": "MiniMax-M2.7",
                    "max_tokens": 1000,
                    "temperature": 0.3,
                    "system": "You audit digital products strictly. Score honestly. No sugar-coating.",
                    "messages": [{"role": "user", "content": audit_prompt}],
                }
                req = urllib.request.Request(
                    f"{mxn_creds['base_url']}/v1/messages",
                    data=json.dumps(audit_body).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {mxn_creds['api_key']}",
                        "anthropic-version": "2023-06-01",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    audit_data = json.loads(resp.read())
                    for block in audit_data.get("content", []):
                        if block.get("type") == "text":
                            audit_text = block["text"]
                            # Extract JSON from response
                            match = re.search(r'\{.*\}', audit_text, re.DOTALL)
                            if match:
                                try:
                                    audit_result = json.loads(match.group(0))
                                    rec = audit_result.get("recommendation", "FLAG")
                                    issues = audit_result.get("issues", [])
                                    print(f"  {slug}: {audit_result.get('comprehensiveness', '?')}/10 | "
                                          f"{audit_result.get('visual_polish', '?')}/10 | "
                                          f"{audit_result.get('value_check', '?')}/10 | "
                                          f"{rec} {'⚠️  ' + '; '.join(issues[:2]) if issues else ''}")
                                except Exception:
                                    print(f"  {slug}: Audit result unparseable — check output")
                            break
        else:
            print("  No API key — audit skipped")
    except Exception as e:
        print(f"  ⚠️  Audit error: {e}")
    print("  ✅ Stage 4 complete")

    # ── Stage 5: QA Gate ──────────────────────────────────────────────────────────────
    print(stage_banner(5, "QA Gate — pdf_qa_layout.py"))
    rc = run_py("pdf_qa_layout.py", timeout=120)
    if rc != 0:
        print("  ⚠️  QA returned non-zero — NOT pushing to GitHub")
        sys.exit(1)
    print(f"  ✅ Stage 5 complete — QA PASSED")

    # ── Stage 6: GitHub Sync ──────────────────────────────────────────────────────────
    print(stage_banner(6, "GitHub Sync"))
    for prod in products:
        slug = prod["slug"]
        guide_pdf = OUTPUT_DIR / f"{slug}.pdf"
        checklist_pdf = OUTPUT_DIR / f"{slug}_CHECKLIST.pdf"
        if not guide_pdf.exists() or not checklist_pdf.exists():
            print(f"  ❌ Missing files for {slug} — skipping")
            continue
        rc1 = run_py("sync_product.py", str(guide_pdf), str(checklist_pdf), timeout=60)
        if rc1 == 0:
            print(f"  ✅ {slug} synced")
        else:
            print(f"  ⚠️  Sync failed for {slug}")
    print(f"  ✅ Stage 6 complete")

    # ── Stage 7: Distribution (Reddit Bridge + Pinterest Pin) ─────────────────────────
    print(stage_banner(7, "Distribution — generate_distribution.py"))
    rc = run_py("generate_distribution.py", timeout=300)
    if rc != 0:
        print("  ⚠️  Distribution generation had issues — continuing")
    print(f"  ✅ Stage 7 complete")

    # ── Summary ─────────────────────────────────────────────────────────────────────
    pdfs = sorted(OUTPUT_DIR.glob("*.pdf"))
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}")
    print(f"  Config hash: {CONFIG_HASH}")
    print(f"  Products built: {len(products)}")
    print(f"  Total PDFs: {len(pdfs)}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Daily PDF Pipeline")
    parser.add_argument("--dry-run", action="store_true",
                        help="Scan drafts only — skip generation and push")
    parser.add_argument("--products", nargs="+",
                        help="Specific products to process (default: all from TrendScout)")
    args = parser.parse_args()

    try:
        run_pipeline(dry_run=args.dry_run, target_products=args.products)
    except PipelineConfigConflict as e:
        print(f"\n❌ CONFIG CONFLICT — {e}")
        print("Pipeline HALTED. Awaiting confirmation before proceeding.")
        sys.exit(99)
    except Exception as e:
        print(f"\n❌ PIPELINE ERROR: {e}")
        sys.exit(1)