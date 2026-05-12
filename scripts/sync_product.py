#!/usr/bin/env python3
"""
sync_product.py — Sync PDF + Checklist to GitHub products-distribution repo
Uses gh CLI (keyring auth) — no PATs or credentials stored in files.

FIX v2: Content-level diff check. If the local file bytes differ from the
git HEAD version, we commit and push. If they're byte-identical, skip
with "already synced" message. Never do a wasteful empty commit.

Usage: python3 sync_product.py <pdf_path> [checklist_path]
"""
import sys, subprocess, hashlib
from pathlib import Path

REPO = "mrohitth/products-distribution"
WORKSPACE = Path("/home/mathew/.openclaw/workspace")
CLONE_DIR = WORKSPACE / "output" / "repos" / "mrohitth_products-distribution"
DEFAULT_BRANCH = "dev"  # Pipeline pushes to dev; --release flag required for main


def sync_to_github(pdf_path, checklist_path=None, branch=None):
    branch = branch or DEFAULT_BRANCH
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"  ❌ PDF not found: {pdf_path}")
        return False

    local_pdf_hash = hashlib.md5(pdf_path.read_bytes()).hexdigest()

    # Clone or use existing clone
    if not CLONE_DIR.exists():
        remote_url = f"https://github.com/{REPO}.git"
        r = subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout", remote_url, str(CLONE_DIR)],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0:
            print(f"  ❌ Clone failed: {r.stderr[:200]}")
            return False

    subprocess.run(["git", "-C", str(CLONE_DIR), "fetch", "origin", "--quiet"],
                    capture_output=True, timeout=30)

    # Checkout remote HEAD
    subprocess.run(
        ["git", "-C", str(CLONE_DIR), "reset", "--hard", f"origin/{branch}"],
        capture_output=True, timeout=15
    )

    final_dir = CLONE_DIR / "final_products"
    final_dir.mkdir(parents=True, exist_ok=True)

    # ── PDF ──────────────────────────────────────────────────────────────────────────
    dest_pdf = final_dir / pdf_path.name
    remote_has_pdf = (CLONE_DIR / pdf_path.name).exists()
    remote_pdf_hash = None
    if remote_has_pdf:
        remote_pdf_hash = hashlib.md5((CLONE_DIR / pdf_path.name).read_bytes()).hexdigest()

    pdf_changed = (not remote_has_pdf) or (local_pdf_hash != remote_pdf_hash)
    if pdf_changed:
        import shutil
        shutil.copy2(str(pdf_path), str(dest_pdf))
        print(f"  ✅ {pdf_path.name} → final_products/ ({pdf_path.stat().st_size // 1024} KB)")
    else:
        print(f"  ℹ️  {pdf_path.name} — byte-identical to remote, skipping")

    # ── Checklist ─────────────────────────────────────────────────────────────────
    cl_changed = False
    if checklist_path:
        cl = Path(checklist_path)
        if cl.exists():
            dest_cl = final_dir / cl.name
            local_cl_hash = hashlib.md5(cl.read_bytes()).hexdigest()
            remote_cl_hash = None
            if (CLONE_DIR / cl.name).exists():
                remote_cl_hash = hashlib.md5((CLONE_DIR / cl.name).read_bytes()).hexdigest()
            cl_changed = (not (CLONE_DIR / cl.name).exists()) or (local_cl_hash != remote_cl_hash)
            if cl_changed:
                import shutil
                shutil.copy2(str(cl), str(dest_cl))
                print(f"  ✅ {cl.name} → final_products/ ({cl.stat().st_size // 1024} KB)")
            else:
                print(f"  ℹ️  {cl.name} — byte-identical to remote, skipping")

    # ── Commit + Push ─────────────────────────────────────────────────────────────
    if not pdf_changed and not cl_changed:
        print(f"  ℹ️  No changes to push — all files byte-identical")
        return True

    subprocess.run(["git", "-C", str(CLONE_DIR), "add", "."],
                   capture_output=True)
    slug = pdf_path.stem.replace("_v1", "")
    msg = f"prod: {slug} — {'+ checklist' if cl_changed else 'PDF only'}"
    r = subprocess.run(["git", "-C", str(CLONE_DIR), "commit", "-m", msg],
                       capture_output=True, text=True)
    if r.returncode != 0 and "nothing to commit" not in r.stdout + r.stderr:
        print(f"  ❌ Commit failed: {r.stderr[:200]}")
        return False

    push = subprocess.run(
        ["git", "-C", str(CLONE_DIR), "push", "origin", branch],
        capture_output=True, text=True, timeout=30
    )
    if push.returncode != 0:
        print(f"  ❌ Push failed: {push.stderr[:200]}")
        return False

    print(f"  ✅ GitHub push complete — https://github.com/{REPO}/tree/{branch}/final_products")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sync_product.py <pdf_path> [checklist_path]")
        sys.exit(1)
    pdf = sys.argv[1]
    cl = sys.argv[2] if len(sys.argv) > 2 else None
    success = sync_to_github(pdf, cl)
    sys.exit(0 if success else 1)