#!/usr/bin/env python3
"""
sync_product.py — Sync PDF + Checklist to GitHub products-distribution repo
Uses gh CLI (keyring auth) — no PATs or credentials stored in files.
Usage: python3 sync_product.py <pdf_path> <checklist_path>
"""
import sys, subprocess, shutil
from pathlib import Path

REPO = "mrohitth/products-distribution"
WORKSPACE = Path("/home/mathew/.openclaw/workspace")
CLONE_DIR = WORKSPACE / "output" / "repos" / "mrohitth_products-distribution"

def gh(args):
    result = subprocess.run(["gh", "api", "--header", "X-GitHub-Api-Version:2022-11-28"] + args, capture_output=True, text=True)
    return result

def sync_to_github(pdf_path, checklist_path=None):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"  ❌ PDF not found: {pdf_path}")
        return False

    slug = pdf_path.stem.replace("_v1", "")  # strip _v1 suffix for clean folder name

    # Clone or update repo
    if CLONE_DIR.exists():
        subprocess.run(["git", "-C", str(CLONE_DIR), "fetch", "origin"], capture_output=True, timeout=30)
    else:
        remote = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, cwd=str(CLONE_DIR.parent)).stdout.strip() if CLONE_DIR.exists() else None
        if not remote:
            remote = subprocess.run(["gh", "repo", "view", REPO, "--json", "url", "-q", ".url"], capture_output=True, text=True).stdout.strip()
            remote = f"https://github.com/{REPO}.git"
        subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", remote, str(CLONE_DIR)], capture_output=True, timeout=60)

    # Ensure clean remote URL
    subprocess.run(["git", "-C", str(CLONE_DIR), "remote", "set-url", "origin", f"https://github.com/{REPO}.git"], capture_output=True)

    final_dir = CLONE_DIR / "final_products"
    final_dir.mkdir(parents=True, exist_ok=True)

    # Copy PDFs
    import shutil
    dest_pdf = final_dir / pdf_path.name
    shutil.copy2(str(pdf_path), str(dest_pdf))
    print(f"  ✅ Synced: {pdf_path.name} → final_products/")

    checklist_pdf = None
    if checklist_path:
        cl = Path(checklist_path)
        if cl.exists():
            dest_cl = final_dir / cl.name
            shutil.copy2(str(cl), str(dest_cl))
            checklist_pdf = cl.name
            print(f"  ✅ Synced: {cl.name} → final_products/")
        else:
            print(f"  ⚠️  Checklist not found: {cl}")

    # Commit and push
    subprocess.run(["git", "-C", str(CLONE_DIR), "add", "."], capture_output=True)
    msg = f"prod: {slug} — {'+ checklist' if checklist_pdf else 'PDF only'}"
    result = subprocess.run(["git", "-C", str(CLONE_DIR), "commit", "-m", msg], capture_output=True, text=True)
    if "nothing to commit" in result.stdout + result.stderr:
        print(f"  ℹ️  No changes to push")
        return True
    # Pull first (handle non-fast-forward from concurrent runs or rebased remote)
    subprocess.run(["git", "-C", str(CLONE_DIR), "pull", "--rebase", "origin", "main"], capture_output=True, timeout=30)
    push = subprocess.run(["git", "-C", str(CLONE_DIR), "push", "origin", "main"], capture_output=True, timeout=30)
    if push.returncode != 0:
        print(f"  ❌ Push failed: {push.stderr[:200]}")
        return False

    print(f"  ✅ GitHub push complete — https://github.com/{REPO}/tree/main/final_products")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sync_product.py <pdf_path> [checklist_path]")
        sys.exit(1)
    pdf = sys.argv[1]
    cl = sys.argv[2] if len(sys.argv) > 2 else None
    success = sync_to_github(pdf, cl)
    sys.exit(0 if success else 1)