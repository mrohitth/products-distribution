#!/usr/bin/env python3
"""
Pipeline Manager — Digital Product Workflow, Stages 2-4
========================================================
Scans wiki/trends/ for HIGH CONVICTION flags, triggers
skeleton + draft generation via MiniMax M2.7 API, runs
.bak purge, and reports completion.

Designed to chain after TrendScout Stage 1 completion.
"""
import json, os, sys, time, subprocess, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
TRENDS_DIR = WORKSPACE / "wiki" / "trends"
SKELETONS_DIR = WORKSPACE / "products" / "skeletons"
DRAFTS_DIR = WORKSPACE / "products" / "drafts"
SESSIONS_DIR = Path("/home/mathew/.openclaw/agents/main/sessions")
CONFIG_PATH = Path("/home/mathew/.openclaw/openclaw.json")

ET = timezone(timedelta(hours=-4))


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_minimax_credentials(cfg):
    """Extract MiniMax API key and base URL from openclaw config."""
    providers = cfg.get("models", {}).get("providers", {})
    minimax = providers.get("minimax", {})
    return {
        "base_url": minimax.get("baseUrl", "https://api.minimax.io/anthropic"),
        "api_key": minimax.get("apiKey", ""),
    }


def check_existing_skeleton(topic_title, skeletons_dir):
    """
    Stage 2 dedup: Check if a skeleton already exists for this topic.
    Returns (existing_path, "skeleton") if found, else (None, None).
    Uses topic title similarity via slug overlap.
    """
    import difflib
    if not skeletons_dir.exists():
        return None, None
    incoming_slug = slugify(topic_title)
    for existing in skeletons_dir.glob("*_SKELETON.md"):
        existing_slug = existing.stem.replace("_SKELETON", "")
        # Exact slug match
        if incoming_slug == existing_slug:
            return existing, "skeleton"
        # Fuzzy title match (Levenshtein-like)
        sim = difflib.SequenceMatcher(None, incoming_slug, existing_slug).ratio()
        if sim > 0.75:
            return existing, "skeleton"
    return None, None


def extract_title_from_draft(draft_path):
    """Extract canonical title from a draft file (frontmatter title: or first H1)."""
    try:
        content = draft_path.read_text()
        # Try frontmatter title: field first
        for line in content.split('\n')[:20]:
            if line.strip().startswith('title:'):
                return line.split('title:', 1)[1].strip().strip('"')
        # Fallback: first H1 heading
        for line in content.split('\n')[:30]:
            if line.startswith('# '):
                return line[2:].strip()
    except Exception:
        pass
    return None


def check_existing_draft(slug, drafts_dir):
    """
    Stage 3 dedup: Check if a draft already exists for this slug.
    Returns (existing_path, "draft") if found, else (None, None).
    Looks for {slug}_V*.md (canonical V1, V2, _FINAL, etc.).
    Also checks title-level dedup to catch same product with different slug.
    """
    if not drafts_dir.exists():
        return None, None
    for draft_file in drafts_dir.glob("*.md"):
        draft_slug = draft_file.stem
        # Strip version suffixes to get base slug
        base_slug = re.sub(r'_V(\d+|_FINAL|_v\d+)$', '', draft_slug)
        if base_slug == slug:
            return draft_file, "draft"
    return None, None


def check_existing_draft_by_trend(trend_title, drafts_dir):
    """
    Stage 3 trend-level dedup: Check if any existing draft was generated from
    the same trend. Same trend = same product (regardless of title or slug).
    Returns (existing_path, "trend_match") if found, else (None, None).
    """
    if not drafts_dir.exists():
        return None, None
    for draft_file in drafts_dir.glob("*.md"):
        try:
            content = draft_file.read_text()
            for line in content.split('\n')[:30]:
                if line.strip().startswith('trend:'):
                    existing_trend = line.split('trend:', 1)[1].strip().strip('"')
                    # Normalize both for comparison
                    norm_existing = re.sub(r'[^a-z0-9]', '', existing_trend.lower())
                    norm_incoming = re.sub(r'[^a-z0-9]', '', trend_title.lower())
                    if norm_existing == norm_incoming:
                        return draft_file, "trend_match"
                    break
        except Exception:
            pass
    return None, None


def check_existing_draft_by_title(trend_title, drafts_dir, min_title_sim=0.75):
    """
    Stage 3 title-level dedup: Check if any existing draft has the same title.
    Handles the case where two skeletons get different slugs but same product.
    Returns (existing_path, "title_match") if found, else (None, None).
    Uses Levenshtein-like similarity on normalized titles.
    """
    if not drafts_dir.exists():
        return None, None
    import difflib
    # Normalize incoming title
    norm_incoming = re.sub(r'[^a-z0-9]', '', trend_title.lower())
    for draft_file in drafts_dir.glob("*.md"):
        title = extract_title_from_draft(draft_file)
        if title:
            norm_existing = re.sub(r'[^a-z0-9]', '', title.lower())
            sim = difflib.SequenceMatcher(None, norm_incoming, norm_existing).ratio()
            if sim >= min_title_sim:
                return draft_file, "title_match"
    return None, None


def normalize_to_canonical(drafts_dir, slug, source_path):
    """
    Move any existing canonical version of this slug to archive/.
    Renames _FINAL, _V2, _v2 → _V1 as the canonical form.
    archive/ is created inside drafts_dir.
    """
    archive_dir = drafts_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Find all versions of this slug
    for existing in drafts_dir.glob(f"{slug}_*.md"):
        stem = existing.stem
        # Already canonical
        if re.search(r'_V\d+$', stem):
            # Archive it (newer version coming)
            dest = archive_dir / existing.name
            import shutil
            shutil.move(str(existing), str(dest))
            print(f"  Archive: {existing.name} → archive/")


def find_latest_trends():
    """Find the most recent status: scored trends file."""
    if not TRENDS_DIR.exists():
        return None
    scored_files = sorted(
        [f for f in TRENDS_DIR.glob("*.md") if f.stem.startswith("202")],
        reverse=True,
    )
    for f in scored_files:
        content = f.read_text()
        if "status: scored" in content and "[HIGH CONVICTION]" in content:
            return f
    return None


def parse_trends(filepath):
    """Extract trends with HIGH CONVICTION flags from a scored file."""
    content = filepath.read_text()
    trends = []
    in_high = False
    current = {}
    
    for line in content.split("\n"):
        if "[HIGH CONVICTION]" in line and "Trend" in line:
            if current and "title" in current:
                trends.append(current)
            current = {}
            in_high = True
            # Parse title and score
            parts = line.split("—")
            if len(parts) >= 1:
                title_part = parts[0].replace("[HIGH CONVICTION]", "").strip()
                title_part = title_part.replace("##", "").strip()
                current["title"] = title_part
            if len(parts) >= 2:
                score_part = parts[1].strip()
                current["score"] = score_part.split("/")[0].strip()
        elif in_high and current and "Quote:" in line:
            current["quote"] = line.split("Quote:")[-1].strip().strip('"*')
        elif in_high and current and "Emotional trigger:" in line:
            current["trigger"] = line.split("trigger:")[-1].strip()
        elif in_high and current and "Product angle:" in line:
            current["angle"] = line.split("angle:")[-1].strip()
    
    if current and "title" in current:
        trends.append(current)
    
    return trends


def slugify(title):
    """Convert title to filesystem-safe slug."""
    return title.lower().replace(" ", "_").replace("'", "").replace('"', "")[:60]


def call_minimax(creds, system_prompt, user_prompt, max_tokens=4000):
    """Call MiniMax M2.7 API via Anthropic-compatible endpoint."""
    import urllib.request, urllib.error
    
    url = f"{creds['base_url']}/v1/messages"
    body = {
        "model": "MiniMax-M2.7",
        "max_tokens": max_tokens,
        "temperature": 0.8,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds['api_key']}",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            content = data.get("content", [])
            for block in content:
                if block.get("type") == "text":
                    return block["text"]
            return ""
    except urllib.error.HTTPError as e:
        print(f"  API error: {e.code} {e.reason}")
        return None
    except Exception as e:
        print(f"  API exception: {e}")
        return None


def generate_skeleton(creds, trend):
    """Stage 2: Generate product skeleton for a HIGH CONVICTION trend."""
    title = trend.get("title", "Unknown Trend")
    score = trend.get("score", "?")
    quote = trend.get("quote", "")
    trigger_text = trend.get("trigger", "")
    angle = trend.get("angle", "")
    
    system = """You write product skeletons for digital guides. Your voice is smart-casual, 
empathetic, data-grounded, and 100% matte-finish. Never use AI-slop language ("game-changer," 
"unlock," "journey"). Write like a sharp, warm colleague who's been through it. Use the 
'Off Switch' skeleton format as reference: Emotional Hook, Problem Breakdown, Product 
Architecture (Parts/Sections), Distribution Strategy, and Market Angle."""

    user = f"""Generate a Product Skeleton for this HIGH CONVICTION trend:

TREND: {title} (Frustration Score: {score}/10)
VERBATIM QUOTE: {quote}
EMOTIONAL TRIGGER: {trigger_text}
PRODUCT ANGLE: {angle}

FORMAT:
1. A compelling product title (40 chars max, curiosity-driven, not clickbait)
2. Emotional Hook section (200 words): Open with an adaptation of the quote, validate immediately, pivot to what the product will DO (not what it "teaches")
3. Product Architecture: 4 Parts, each with 3 chapters. Brief description of each.
4. Key Human Touch elements: What personal anecdotes or framing will land here
5. Format & Pricing: PDF/audio/worksheets, price point rationale
6. Distribution: Where this lives and how it spreads
7. Market Intel angle: How this connects to "human infrastructure" investment thesis

Length: ~800 words. Markdown."""
    
    return call_minimax(creds, system, user, max_tokens=3000)


def generate_draft(creds, trend, skeleton_text):
    """Stage 3: Generate full first draft from skeleton."""
    title = trend.get("title", "Unknown Trend")
    
    system = """You write full-length digital guide drafts. Voice: smart-casual, warm, 
empathetic, data-grounded. Zero AI-slop. Write like someone who's lived this, not 
someone who researched it. Use contractions, occasional humor, and direct address. 
Structure with clear H2/H3 headings. Bold Key Takeaways after major sections. 
Weave in the "human infrastructure" thesis subtly — managing personal energy and 
household systems IS infrastructure, just at human scale. 

Target length: 2500-4000 words per section. Write ALL sections as COMPLETE,
production-ready chapters. No "Coming in V2" or outline-only language — every
section must be a finished chapter ready to ship."""

    user = f"""Using this skeleton as the foundation, write Parts 1 and 2 of the full 
guide draft. Expand every bullet into real prose. Follow the 'Off Switch' draft format 
at /home/mathew/.openclaw/workspace/products/drafts/off_switch_V1.md as reference.

SKELETON:
{skeleton_text[:3000]}

Write in markdown. Include:
- A strong introduction that hooks emotionally
- Part 1 and Part 2 as complete chapters with actionable content
- Bolded Key Takeaways after major sections
- A "Capital Pilot Interstitial" section connecting to human infrastructure thesis
- Parts 3-4 as brief outlines

The trend driving this: {title}"""
    
    return call_minimax(creds, system, user, max_tokens=8000)


def purge_bak_files():
    """Delete .bak-* files older than 24 hours from session directory."""
    if not SESSIONS_DIR.exists():
        return 0, 0
    cutoff = time.time() - 86400
    count, size = 0, 0
    for bak in SESSIONS_DIR.glob("*.bak-*"):
        try:
            stat = bak.stat()
            if stat.st_mtime < cutoff:
                size += stat.st_size
                bak.unlink()
                count += 1
        except OSError:
            pass
    return count, size


def send_draft_via_telegram(draft_path, creds):
    """Send draft as a Telegram document using bot API."""
    cfg = load_config()
    bot_token = None
    # Extract bot token from channels config
    channels = cfg.get("channels", {}).get("telegram", {})
    bot_token = channels.get("botToken", "")
    if not bot_token:
        # Also check provider config
        providers = cfg.get("providers", {})
        if isinstance(providers, dict):
            tg = providers.get("telegram", {})
            bot_token = tg.get("botToken", "")
    
    chat_id = "5607383477"
    
    if not bot_token or len(bot_token) < 10:
        print("  ⚠️  No Telegram bot token found — skipping file send")
        return None
    
    import urllib.request
    
    # Read file content
    draft_bytes = Path(draft_path).read_bytes()
    filename = Path(draft_path).name
    
    # Build multipart form data manually
    boundary = "----PipelineBoundary"
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode()
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="caption"\r\n\r\n[Draft] {filename}\r\n'.encode()
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode()
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += draft_bytes
    body += f"\r\n--{boundary}--\r\n".encode()
    
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            if data.get("ok"):
                doc = data.get("result", {}).get("document", {})
                file_id = doc.get("file_id", "")
                print(f"  📄 Draft sent via Telegram: {file_id[:16]}...")
                return file_id
            else:
                print(f"  ⚠️  Telegram send failed: {data.get('description', 'unknown')}")
                return None
    except Exception as e:
        print(f"  ⚠️  Telegram API error: {e}")
        return None


def sync_to_github(file_path, repo="mrohitth/products-distribution", branch="main"):
    """
    Phase 1: Git integration for versioned release archival.
    Runs after Stage 5 Pandoc conversion.

    Logic:
      - Stages the PDF via git add
      - Commits with annotated message: "prod: release v{version} for {slug}"
      - Pushes to the target repository

    Args:
        file_path: Absolute path to the generated PDF
        repo: Target GitHub repo in "owner/repo" format
        branch: Target branch (default: main)

    Returns:
        True on success, False on failure
    """
    import subprocess as _subprocess

    pdf_path = Path(file_path)
    if not pdf_path.exists():
        print(f"  ❌ sync_to_github: file not found: {file_path}")
        return False

    slug = pdf_path.stem  # e.g. "off_switch_V1"
    # Extract version from slug (expects *_V{n} format)
    version_match = re.search(r'_V(\d+)$', slug)
    version = version_match.group(1) if version_match else "1"

    # Build commit message
    commit_msg = f"prod: release v{version} for {slug}"

    # Use GIT_WORK_TREE to push from output dir to the target repo
    # Assumes the repo is cloned at OUTPUT_DIR/repos/products-distribution
    OUTPUT_DIR = WORKSPACE / "output"
    REPO_DIR = OUTPUT_DIR / "repos" / repo.replace("/", "_")

    # Ensure the bare repo checkout exists
    if not REPO_DIR.exists():
        print(f"  Cloning {repo} into {REPO_DIR}...")
        try:
            clone_result = _subprocess.run(
                ["git", "clone",
                 _subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip(),
                 str(REPO_DIR)],
                capture_output=True, text=True, timeout=60,
            )
            if clone_result.returncode != 0:
                print(f"  ⚠️  Clone failed: {clone_result.stderr[:200]}")
                return False
        except Exception as e:
            print(f"  ❌ sync_to_github: clone failed: {e}")
            return False

    # Ensure push works: sync remote URL to match workspace (which has token embedded)
    _subprocess.run(
        ["git", "-C", str(REPO_DIR), "remote", "set-url", "origin",
         _subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()],
        capture_output=True, text=True,
    )

    # Copy PDF into the repo working tree
    dest = REPO_DIR / pdf_path.name
    import shutil
    shutil.copy2(str(pdf_path), str(dest))

    # Stage, commit, push
    cmds = [
        ["git", "-C", str(REPO_DIR), "add", pdf_path.name],
        ["git", "-C", str(REPO_DIR), "commit", "-m", commit_msg],
        ["git", "-C", str(REPO_DIR), "push", "origin", branch],
    ]
    for cmd in cmds:
        result = _subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            # Check if it's a "nothing to commit" case — not an error
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                print(f"  ℹ️  Nothing to commit — {slug} already synced")
                return True
            print(f"  ❌ sync_to_github failed: {' '.join(cmd)}")
            print(f"     {result.stderr[:200]}")
            return False

    print(f"  ✅ Synced {pdf_path.name} → {repo}:{branch} | commit: {commit_msg}")
    return True


def create_github_release(pdf_path, repo="mrohitth/products-distribution", tag=None, title=None, body=None):
    """
    Phase 1: Create a GitHub Release and attach the PDF as a binary asset.

    Uses the GitHub CLI (gh) to:
      - Create an annotated tag: "v{version}"
      - Create a release attached to that tag
      - Upload the PDF as a release asset

    This gives each product a permanent, versioned URL:
      https://github.com/{repo}/releases/download/v{version}/{slug}.pdf

    Args:
        pdf_path: Absolute path to the PDF file to attach
        repo: Target GitHub repo in "owner/repo" format
        tag: Override tag (default: auto from slug)
        title: Override release title
        body: Override release notes (markdown)

    Returns:
        True on success, False on failure
    """
    import subprocess as _subprocess

    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"  ❌ create_github_release: file not found: {pdf_path}")
        return False

    slug = pdf.stem
    # Parse version from slug
    version_match = re.search(r'_V(\d+)$', slug)
    version = version_match.group(1) if version_match else "1"
    release_tag = tag or f"v{version}"
    release_title = title or f"prod: {slug} v{version}"
    release_body = body or (
        f"## Release {release_tag}\n\n"
        f"**Product:** {slug}\n"
        f"**Version:** {version}\n"
        f"**Generated:** {datetime.now().date()}\n\n"
        f"---\n\n"
        f"*Human Infrastructure — Human-scale systems, maintained.*"
    )

    # Read GitHub token from env (set by caller or git-credentials fallback)
    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not gh_token:
        cred_path = Path.home() / ".git-credentials"
        if cred_path.exists():
            for line in cred_path.read_text().strip().split("\n"):
                if "github.com" in line:
                    # Extract token from URL after ://
                    try:
                        token_start = line.index("://") + 3
                        token_end = line.index("@", token_start)
                        gh_token = line[token_start:token_end].split(":")[-1]
                        break
                    except ValueError:
                        pass
    if not gh_token:
        print("  ❌ No GitHub token found — set GH_TOKEN or GITHUB_TOKEN")
        return False

    # Use REST API directly (avoids gh CLI auth requirement)
    import urllib.request, urllib.error

    api_base = f"https://api.github.com/repos/{repo}"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json",
    }

    # Step 1: Create the release
    release_payload = json.dumps({
        "tag_name": release_tag,
        "name": release_title,
        "body": release_body,
        "draft": False,
        "target_commitish": "main",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{api_base}/releases", data=release_payload,
        headers=headers, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            release_data = json.loads(resp.read())
            upload_url = release_data.get("upload_url", "").split("{?name,label}")[0]
            release_url = release_data.get("html_url", "")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        if e.code == 422 and "already exists" in err_body.lower():
            # Get existing release
            req = urllib.request.Request(f"{api_base}/releases/tags/{release_tag}", headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                release_data = json.loads(resp.read())
                upload_url = release_data.get("upload_url", "").split("{?name,label}")[0]
                release_url = release_data.get("html_url", "")
        else:
            print(f"  ❌ Release create failed ({e.code}): {err_body[:200]}")
            return False

    # Step 2: Upload PDF as release asset
    file_bytes = pdf.read_bytes()
    file_size = len(file_bytes)
    upload_req = urllib.request.Request(
        f"{upload_url}?name={pdf.name}",
        data=file_bytes,
        headers={
            "Authorization": f"Bearer {gh_token}",
            "Content-Type": "application/octet-stream",
            "Content-Length": str(file_size),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(upload_req, timeout=60) as resp:
            asset = json.loads(resp.read())
            asset_url = asset.get("browser_download_url", "")
            print(f"  ✅ Asset uploaded: {asset_url}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        if e.code == 422:
            # Asset exists — delete and re-upload
            list_req = urllib.request.Request(
                f"{api_base}/releases/{release_data['id']}/assets",
                headers=headers,
            )
            with urllib.request.urlopen(list_req, timeout=15) as resp:
                for a in json.loads(resp.read()):
                    if a["name"] == pdf.name:
                        del_req = urllib.request.Request(
                            f"{api_base}/releases/assets/{a['id']}",
                            headers=headers, method="DELETE"
                        )
                        try:
                            urllib.request.urlopen(del_req, timeout=15)
                        except Exception:
                            pass
                        break
            # Retry
            upload_req = urllib.request.Request(
                f"{upload_url}?name={pdf.name}",
                data=file_bytes,
                headers={
                    "Authorization": f"Bearer {gh_token}",
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(file_size),
                },
                method="POST",
            )
            with urllib.request.urlopen(upload_req, timeout=60) as resp:
                asset = json.loads(resp.read())
                print(f"  ✅ Asset re-uploaded (clobbered): {asset.get('browser_download_url','')}")
        else:
            print(f"  ❌ Asset upload failed ({e.code}): {err_body[:200]}")
            return False

    print(f"  ✅ Release {release_tag} in {repo} — {release_url}")
    return True


def cleanup_for_production(md_text, dry_run=False):
    r"""
    Strip draft artifacts from markdown before PDF generation.

    Removes:
      - YAML front matter (--- blocks at top)
      - Version/draft header lines (### Version 1 Draft | TrendScout...)
      - Trailing draft metadata lines (*Version 1 Draft ..., *TrendScout...)
      - "Coming in V2:" italic paragraphs
      - Lone horizontal rules used as non-YAML section dividers
      - Blank-line runs > 2 lines (compact)
      - [AI-GENERATED], [FIRST DRAFT] bracket markers

    Transforms:
      - **Key Takeaway:** blocks → <div class="callout-takeaway"> wrapped
      - **Say:** / **Don't say:** blocks → <div class="callout-script"> wrapped

    Args:
        md_text: Raw markdown string
        dry_run: If True, return cleaned text but print stats only

    Returns:
        Cleaned markdown string
    """
    import re as _re

    lines = md_text.split("\n")
    cleaned = []
    in_yaml = False
    yaml_closed = False
    consecutive_blanks = 0

    # Regex patterns (compiled once)
    re_version_hdr = _re.compile(r"^###\s+Version\s+\d+\s+Draft", _re.IGNORECASE)
    re_product_meta = _re.compile(r"^#\s+PRODUCT\s+METADATA", _re.IGNORECASE)
    re_about_author = _re.compile(r"^#\s+ABOUT\s+THE\s+AUTHOR", _re.IGNORECASE)
    re_coming_v2 = _re.compile(r"^\*(Coming in V2|What.s coming in V2):", _re.IGNORECASE)
    re_coming_v2_section = _re.compile(r"Coming in V2", _re.IGNORECASE)
    re_trailing_meta = _re.compile(
        r"^\*(Version\s+\d+\s+Draft|Draft.*generated|Awaiting review|TrendScout|Pipeline:|Next:\s+Stage|"
        r"This draft is matte|Framework:|Top Conviction:)",
        _re.IGNORECASE,
    )
    re_ai_marker = _re.compile(r"\[(AI-GENERATED|FIRST.DRAFT|TEMP|DRAFT ONLY)\]", _re.IGNORECASE)
    re_key_takeaway = _re.compile(r"^\*\*Key Takeaway:\*\*\s*(.*)")
    re_script_block = _re.compile(r"^\*\*(Say|Don't\s+say):\*\*\s*(.*)")
    re_chapter_hdr = _re.compile(r"^###\s+Chapter\s+\d+:", _re.IGNORECASE)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── YAML front matter ──
        if not yaml_closed and i <= 2 and stripped == "---":
            in_yaml = True
            i += 1
            continue

        # Close YAML when we hit the second ---
        if in_yaml and stripped == "---":
            in_yaml = False
            yaml_closed = True
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        if in_yaml:
            i += 1
            continue

        # ── Strip bracket markers [AI-GENERATED], [FIRST DRAFT], [TEMP] ──
        if re_ai_marker.search(stripped):
            i += 1
            continue

        # ── Version/draft header ──
        if re_version_hdr.match(stripped):
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        # ── "Coming in V2:" italic paragraphs ──
        if re_coming_v2.match(stripped):
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        # ── "Coming in V2:" italic paragraphs ──
        if re_coming_v2.match(stripped):
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        # ── Any heading containing "Coming in V2" — strip heading + entire section block ──
        if re_coming_v2_section.search(stripped):
            i += 1
            # Skip all content until the next top-level H2 or higher heading
            while i < len(lines):
                line_text = lines[i].strip()
                # Stop at next H2+ heading (section boundary)
                h_match = re_coming_v2_section.match(line_text)
                if h_match:
                    # This is a new "Coming in V2" section — skip it too
                    i += 1
                    continue
                # H2 headings start the next real section — stop before them
                if line_text.startswith("## "):
                    break
                # Skip everything else (bullets, paragraphs, HRs in the V2 block)
                i += 1
            continue

        # ── PRODUCT METADATA block (H1 + table) ──
        if re_product_meta.match(stripped):
            i += 1
            while i < len(lines) and not re_about_author.match(lines[i].strip()) \
                   and not lines[i].strip().startswith("# "):
                i += 1
            continue

        # ── ABOUT THE AUTHOR block (H1 + paragraphs) ──
        if re_about_author.match(stripped):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("# "):
                i += 1
            continue

        # ── Trailing draft metadata ──
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        # ── Lone horizontal rule used as body divider ──
        # Only strip if it's followed by blank+heading (section divider pattern)
        if stripped == "---":
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            # If next non-blank is a heading, this HR is a section divider — strip it
            if j < len(lines) and lines[j].strip().startswith("#"):
                i = j  # skip HR + blanks, go to heading
                continue
            # Otherwise leave the HR as-is (content separator)
            i += 1
            continue

        # ── Transform: **Key Takeaway:** → callout-takeaway div ──
        kt_match = re_key_takeaway.match(stripped)
        if kt_match:
            inner = kt_match.group(1)
            cleaned.append('<div class="callout-takeaway"><strong>Key Takeaway</strong>')
            cleaned.append(inner)
            cleaned.append('</div>')
            cleaned.append('')
            consecutive_blanks = 0
            i += 1
            continue

        # ── Transform: **Say:** / **Don't say:** → callout-script div ──
        scr_match = re_script_block.match(stripped)
        if scr_match:
            label = scr_match.group(1)
            text = scr_match.group(2).strip()
            if text:
                cleaned.append('<div class="callout-script"><strong>' + label + '</strong>')
                cleaned.append(text)
                cleaned.append('</div>')
                cleaned.append('')
                consecutive_blanks = 0
            i += 1
            continue

        # ── Transform: "### Chapter N: Title" → "## Title" (promote chapter to H2) ──
        ch_match = re_chapter_hdr.match(stripped)
        if ch_match:
            title = stripped[stripped.index(":") + 1:].strip()
            cleaned.append("## " + title)
            cleaned.append("")
            consecutive_blanks = 0
            i += 1
            continue

        # ── Blank-line compaction (max 2) ──
        if stripped == "":
            consecutive_blanks += 1
            if consecutive_blanks <= 2:
                cleaned.append(line)
            i += 1
            continue
        else:
            consecutive_blanks = 0

        cleaned.append(line)
        i += 1

    # Strip trailing blank lines
    while cleaned and cleaned[-1].strip() == "":
        cleaned.pop()

    result = "\n".join(cleaned)

    stripped_bytes = len(md_text.encode("utf-8")) - len(result.encode("utf-8"))
    if dry_run:
        print(f"  [DRY-RUN] Would strip ~{stripped_bytes} bytes of draft artifacts")
        return result
    else:
        print(f"  Stripped ~{stripped_bytes} bytes of draft artifacts")
        return result


def _preprocess_for_pdf(md_text):
    """
    Pre-process markdown before HTML conversion:
    1. Normalize H1 Part/N section headings → H2 (preserve hierarchy, fix page breaks)
    2. Convert *"quoted italic text"* at start of paragraph to styled blockquote
    3. Convert ### Key Insight/Takeaway headings to callout-insight divs (with — prefix)
    """
    import re

    # ── 1. Normalize H1 Part/N headings → H2 ─────────────────────────────────
    # Keep the first H1 as the document title. Demote all subsequent H1s
    # (including # PART N: sections) to H2 so they don't render oversized.
    # Also title-case the demoted headings for consistent presentation.
    # ── Smart heading level assignment ────────────────────────────────────────
    # Rules:
    #  - First H1 = document title (keep)
    #  - H1 that starts with "Part N:" or "Day N" or "Step N" → H2 (major section, gets page break)
    #  - All other H1 (conceptual section openers like "The Floppy Paradox") → H2
    #  - After processing: any H2 that is NOT a "Part N:" or "Day N" section → H3 (subsection)
    #  - First H1 (title) → add page break after so content starts on page 2
    lines = md_text.split('\n')
    first_h1_done = False
    result_lines = []
    title_idx = None
    for line in lines:
        is_h1 = re.match(r'^#\s+\S', line)
        if is_h1 and not first_h1_done:
            first_h1_done = True
            title_idx = len(result_lines)
        elif is_h1 and first_h1_done:
            # Demote to H2 and title-case
            heading_text = line.lstrip('#').strip()
            title_cased = heading_text.title()
            line = f'## {title_cased}'
        result_lines.append(line)
    md_text = '\n'.join(result_lines)

    # ── Title page: cover div is added at HTML output stage (stage5) ────────
    # This avoids the markdown preprocessing complexities.
    # Demote non-Part, non-Day H2s to H3 (these are conceptual openers, not chapters)
    major_section_pattern = re.compile(r'^##\s+(Part\s+\d+|Day\s+\d+|Step\s+\d+)', re.IGNORECASE)
    lines = md_text.split('\n')
    result_lines = []
    for line in lines:
        is_h2_major = bool(major_section_pattern.match(line))
        if line.startswith('## ') and not is_h2_major:
            # Demote to H3
            line = line.replace('## ', '### ', 1)
        result_lines.append(line)
    md_text = '\n'.join(result_lines)

    # ── 1. Blockquote conversion ──────────────────────────────────────────────
    # Pattern: paragraph that STARTS with *"..."* (italic + leading quote)
    # Convert to <blockquote> with em-dash prefix for visual punch
    md_text = re.sub(
        r'^(\S.*?)\n?(\*"[^"]+"\*)',
        lambda m: f'<blockquote class="script-quote"><p>{m.group(2)[1:-1]}</p></blockquote>\n\n{m.group(1)}',
        md_text, flags=re.M | re.DOTALL
    )

    # ── 3. Explicit page breaks before major Part sections ─────────────────────
    # Insert a page-break div BEFORE Part headings (CSS page-break-after was causing blank pages)
    lines = md_text.split('\n')
    result = []
    major_section_pattern = re.compile(r'^##\s+(Part\s+\d+|Day\s+\d+|Step\s+\d+)', re.IGNORECASE)
    for line in lines:
        is_major = bool(major_section_pattern.match(line))
        if is_major and result:
            result.append('<div style="page-break-before: always;"></div>')
        result.append(line)
    md_text = '\n'.join(result)

    # ── 4. Key Insight / Key Takeaway headings ────────────────────────────────
    def convert_insight(m):
        label = m.group(1).capitalize()
        text = m.group(2).strip()
        return f'<div class="callout-insight"><strong>Key {label}</strong><p>— {text}</p></div>'

    md_text = re.sub(
        r'^#{1,3}\s+\*{0,2}Key\s+(Insight|Takeaway)\*{0,2}:\*{0,2}\s*(.*)',
        convert_insight, md_text, flags=re.MULTILINE
    )

    # ── 4. Normalize em-dashes (WeasyPrint handles unicode but be safe) ────────
    md_text = md_text.replace('—', '—').replace('"', '"').replace('"', '"')

    return md_text


def stage5_production_weasyprint(draft_path, css_path=None):
    """
    Stage 5: WeasyPrint PDF generation with professional styling.
    Uses pdf_style.css — TOC, Key Insight callouts, page breaks all included.
    Returns the path to the generated PDF, or None on failure.
    """
    import markdown, io
    CSS_PATH = Path(css_path) if css_path else WORKSPACE / "products" / "assets" / "pdf_style.css"
    OUTPUT_DIR = WORKSPACE / "output" / "final_products"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not CSS_PATH.exists():
        print(f"  ⚠️  CSS not found: {CSS_PATH} — skipping PDF generation")
        return None

    slug = Path(draft_path).stem
    output_pdf = OUTPUT_DIR / f"{slug}.pdf"

    try:
        import weasyprint
    except ImportError:
        print("  ⚠️  WeasyPrint not installed — cannot generate PDF")
        return None

    # Read, clean, and convert markdown
    with open(draft_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Pre-process: strip draft artifacts
    md_content = cleanup_for_production(md_content)

    # Pre-process: convert Key Insight/Takeaway headings to styled callout divs
    md_content = _preprocess_for_pdf(md_content)

    # Convert with TOC extension
    md = markdown.Markdown(extensions=["extra", "meta", "toc"])
    html_body = md.convert(md_content)

    # Read CSS
    css_text = CSS_PATH.read_text()

    # ── Wrap first h1 in div.cover at HTML level ─────────────────────────────
    # This is the cleanest approach: wrap the first H1 element in the HTML
    # with a div.cover so the title-page CSS rules apply.
    first_h1_match = re.search(r'(<h1[^>]*>.*?</h1>)', html_body, re.DOTALL)
    if first_h1_match:
        wrapped = f'<div class="cover">\n{first_h1_match.group(1)}\n</div>'
        html_body = html_body[:first_h1_match.start()] + wrapped + html_body[first_h1_match.end():]

    # Build full HTML document
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>\n{css_text}\n</style>
</head>
<body>\n{html_body}\n</body>
</html>"""

    try:
        wp_doc = weasyprint.HTML(string=html_doc)
        wp_doc.write_pdf(str(output_pdf))
        size_kb = output_pdf.stat().st_size / 1024
        print(f"  ✅ PDF generated (WeasyPrint): {output_pdf} ({size_kb:.0f} KB)")
        return str(output_pdf)
    except Exception as e:
        print(f"  ❌ WeasyPrint failed: {e}")
        return None



def stage5_production(draft_path):
    """Stage 5: Production — convert Markdown draft to styled PDF via Pandoc."""
    import shutil
    CSS_PATH = WORKSPACE / "products" / "assets" / "pandoc_style.css"
    OUTPUT_DIR = WORKSPACE / "output" / "final_products"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not shutil.which("pandoc"):
        print("  ⚠️  Pandoc not installed — skipping PDF generation")
        return None
    
    slug = Path(draft_path).stem
    output_pdf = OUTPUT_DIR / f"{slug}.pdf"
    cmd = [
        "pandoc", str(draft_path), "-o", str(output_pdf),
        "--pdf-engine=xelatex", f"--css={CSS_PATH}",
        "--toc", "--toc-depth=2", "--number-sections",
        "-V", "geometry:margin=1in",
        "-V", "mainfont=Charter",
        "-V", "sansfont=Inter",
        "-V", "fontsize=11pt",
        "--from=markdown+smart",
    ]
    print(f"  Stage 5: Running Pandoc...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            size_kb = output_pdf.stat().st_size / 1024
            print(f"  ✅ PDF generated: {output_pdf} ({size_kb:.0f} KB)")
            return str(output_pdf)
        else:
            print(f"  ❌ Pandoc failed: {result.stderr[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Pandoc error: {e}")
        return None


def send_report(trend, skeleton_path, draft_path):
    """Write completion report for agent delivery."""
    report = f"""🚨 Pipeline Complete — {datetime.now(ET).strftime('%Y-%m-%d %H:%M ET')}

[HIGH CONVICTION] {trend.get('title', 'Unknown')} ({trend.get('score', '?')}/10)

Skeleton: {skeleton_path}
Draft: {draft_path}
Distribution Flywheel: distro/flywheel.py — Reddit, Pinterest, TikTok, LinkedIn, email sequence, Notion upsell auto-generated

Human Infrastructure Angle: This product scales because it solves the highest-cost 
problem in any system — operator burnout. Single parents are running a household 
without backup. The scripts and energy audit give them the maintenance cycle every 
infrastructure asset requires. Distribution via Reddit communities (8.2M r/Parenting) 
gives it zero-cost organic reach. Notion template upsell creates recurring digital revenue 
from a one-time product."""
    
    report_path = WORKSPACE / "memory" / "pipeline_report.md"
    report_path.write_text(report)
    return report


def main():
    print(f"[{datetime.now(ET).strftime('%H:%M:%S ET')}] Pipeline Manager — Stage 2-4")
    
    # 0. Load config
    try:
        cfg = load_config()
        creds = get_minimax_credentials(cfg)
        if not creds["api_key"]:
            print("  ERROR: No MiniMax API key found")
            return 1
    except Exception as e:
        print(f"  ERROR loading config: {e}")
        return 1
    
    # 0a. Purge .bak files
    bak_count, bak_size = purge_bak_files()
    if bak_count:
        print(f"  BAK purge: {bak_count} files, {bak_size/1024/1024:.1f} MB reclaimed")
    
    # 1. Find latest scored trends
    trends_file = find_latest_trends()
    if not trends_file:
        print("  No HIGH CONVICTION trends found — pipeline complete")
        return 0
    
    print(f"  Trends file: {trends_file.name}")
    
    # 2. Parse HIGH CONVICTION trends
    trends = parse_trends(trends_file)
    if not trends:
        print("  No parseable trends — exiting")
        return 0
    
    # Take top-scoring trend
    top = trends[0]
    top["score"] = top.get("score", "8")
    print(f"  Top trend: {top['title']} ({top['score']}/10)")
    
    # 2b. Stage 2 dedup check
    dup_skeleton, dup_type = check_existing_skeleton(top["title"], SKELETONS_DIR)
    if dup_skeleton:
        print(f"  ℹ️  Skeleton already exists for '{top['title']}' — {dup_skeleton.name}")
        print(f"      Skipping Stage 2. Use --force-skeleton to override.")
        if "--force-skeleton" not in sys.argv:
            # Skip to Stage 3 if skeleton exists, but check for draft too
            dup_draft, _ = check_existing_draft(slug, DRAFTS_DIR)
            if dup_draft:
                print(f"  ℹ️  Draft also exists — {dup_draft.name}")
                print(f"      Nothing to do. Exiting.")
                return 0
            skeleton_text = dup_skeleton.read_text()
        else:
            skeleton_text = None
    else:
        skeleton_text = None

    # 3. Stage 2: Generate Skeleton
    if not skeleton_text:
        print(f"  Stage 2: Generating skeleton...")
        skeleton = generate_skeleton(creds, top)
        if not skeleton:
            print("  ERROR: Skeleton generation failed")
            return 1

        slug = slugify(top["title"])
        skeleton_path = SKELETONS_DIR / f"{slug}_SKELETON.md"
        SKELETONS_DIR.mkdir(parents=True, exist_ok=True)
        skeleton_path.write_text(skeleton)
        print(f"  Skeleton saved: {skeleton_path}")
        skeleton_text = skeleton

    # 3b. Stage 3 dedup check (slug level)
    dup_draft, _ = check_existing_draft(slug, DRAFTS_DIR)
    if dup_draft:
        print(f"  ℹ️  Draft already exists — {dup_draft.name}")
        print(f"      Skipping Stage 3. Use --force-draft to override.")
        if "--force-draft" not in sys.argv:
            print(f"      Pipeline complete (dedup). Run with --force-draft to regenerate.")
            return 0

    # 3c. Stage 3 dedup check (title level — catches same product, different slug)
    dup_by_title, match_type = check_existing_draft_by_title(top.get("title", ""), DRAFTS_DIR)
    if dup_by_title:
        print(f"  ℹ️  Draft with same title already exists — {dup_by_title.name}")
        print(f"      This product has a different slug but same title. Archive the existing")
        print(f"      version first, or use --force-draft to override.")
        if "--force-draft" not in sys.argv:
            print(f"      Pipeline blocked (title dedup). Use --force-draft to archive and proceed.")
            return 0

    # 3d. Stage 3 dedup check (trend level — primary dedup for same product)
    dup_by_trend, trend_match = check_existing_draft_by_trend(top.get("title", ""), DRAFTS_DIR)
    if dup_by_trend:
        print(f"  ℹ️  Draft from same trend already exists — {dup_by_trend.name}")
        print(f"      Same trend = same product. Skipping Stage 3.")
        print(f"      Use --force-draft to override.")
        if "--force-draft" not in sys.argv:
            return 0

    # 4. Stage 3: Generate Draft
    print(f"  Stage 3: Generating draft...")
    draft = generate_draft(creds, top, skeleton_text)
    if not draft:
        print("  WARNING: Draft generation failed — skeleton available")
        send_report(top, str(skeleton_path if 'skeleton_path' in dir() else SKELETONS_DIR / f"{slug}_SKELETON.md"), "FAILED")
        return 1

    # Normalize: archive any existing canonical version before writing new one
    normalize_to_canonical(DRAFTS_DIR, slug, None)

    draft_path = DRAFTS_DIR / f"{slug}_V1.md"
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(draft)
    print(f"  Draft saved: {draft_path}")
    
    # 5. Stage 5: Production (WeasyPrint first, Pandoc fallback)
    print(f"  Stage 5: Generating PDF...")
    pdf_path = stage5_production_weasyprint(str(draft_path))
    if not pdf_path:
        # Fallback to Pandoc if WeasyPrint fails
        pdf_path = stage5_production(str(draft_path))

    # 5b. Phase 1: GitHub archival + Release (versioned permanent URL)
    if pdf_path:
        print(f"  Phase 1: Archiving to GitHub...")
        sync_to_github(pdf_path)
        create_github_release(pdf_path)
    else:
        print(f"  Phase 1: Skipped — no PDF generated")

    # 6. Auto-register in distro manifest
    sys.path.insert(0, str(WORKSPACE / "distro"))
    try:
        from manifest import register_product as mp_register
        mp_register(
            slug,
            top.get("title", top.get("name", slug)),
            27,
            str(draft_path),
            "trendscout",
        )
        print(f"  Stage 6: Registered '{slug}' in distro manifest")
    except Exception as e:
        print(f"  Stage 6: WARNING — could not register product: {e}")

    # 6b. Run distribution flywheel in background (non-blocking)
    import subprocess as _subprocess
    distro_script = WORKSPACE / "distro" / "flywheel.py"
    if distro_script.exists():
        pid = _subprocess.Popen(
            [sys.executable, str(distro_script), "run", slug],
            cwd=str(WORKSPACE),
        ).pid
        print(f"  Stage 6b: Distribution flywheel launched (PID {pid})")
    else:
        print(f"  Stage 6b: Distribution flywheel not found — skipping")

    # 7. Send draft via Telegram
    send_draft_via_telegram(str(draft_path), creds)

    # 8. Report
    success_report = send_report(top, str(skeleton_path), str(draft_path))
    if pdf_path:
        success_report = success_report.replace(
            "Draft:",
            f"Draft: {draft_path}\nPDF: {pdf_path}\nDraft file:"
        )
    print(f"  Report: {success_report[:200]}...")
    
    print(f"[{datetime.now(ET).strftime('%H:%M:%S ET')}] Pipeline complete ✅")
    return 0



def stage5_production_docx(draft_path):
    """
    Stage 5b: Generate editable DOCX from draft markdown using pandoc.
    Output: output/final_products/{draft_name}.docx
    DOCX is fully editable — Mathew can make direct formatting tweaks.
    """
    import subprocess
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.pipeline_manager import cleanup_for_production

    draft_path = Path(draft_path)
    output_dir = Path("output/final_products")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{draft_path.stem}.docx"

    md_content = draft_path.read_text()
    md_content = cleanup_for_production(md_content)

    # Write cleaned markdown to temp file for pandoc
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write(md_content)
        tmp_path = tmp.name

    # Convert to DOCX using pandoc
    cmd = [
        "pandoc", tmp_path,
        "-o", str(output_path),
        "--from=markdown",
        "--to=docx",
        "--standalone",
        "--highlight-style=tango",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    import os
    os.unlink(tmp_path)

    if result.returncode == 0 and output_path.exists():
        size_kb = output_path.stat().st_size // 1024
        print(f"✅ DOCX generated: {output_path} ({size_kb} KB)")
        return str(output_path)
    else:
        print(f"❌ DOCX failed: {result.stderr[:300]}")
        return None



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--pdf-only":
        # Production mode: clean + PDF + GitHub on latest draft (no MiniMax call)
        if not DRAFTS_DIR.exists():
            print("No drafts directory")
            sys.exit(1)
        drafts = sorted(DRAFTS_DIR.glob("*_V1.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not drafts:
            drafts = sorted(DRAFTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not drafts:
            print("No drafts found")
            sys.exit(1)
        latest_draft = drafts[0]
        print(f"Processing: {latest_draft.name}")
        pdf = stage5_production_weasyprint(str(latest_draft))
        if pdf:
            gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
            if gh_token:
                sync_to_github(pdf)
                create_github_release(pdf)
            else:
                print("  ⚠️  GH_TOKEN not set — skipping GitHub sync/release")
        sys.exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "--docx-only":
        # Generate DOCX from latest draft
        if not DRAFTS_DIR.exists():
            print("No drafts directory")
            sys.exit(1)
        drafts = sorted(DRAFTS_DIR.glob("*_V1.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not drafts:
            drafts = sorted(DRAFTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not drafts:
            print("No drafts found")
            sys.exit(1)
        latest_draft = drafts[0]
        print(f"Generating DOCX: {latest_draft.name}")
        docx = stage5_production_docx(str(latest_draft))
        if docx:
            print(f"✅ {docx}")
        sys.exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        # Preview mode: show cleaned markdown for latest draft without generating PDF
        if not DRAFTS_DIR.exists():
            print("No drafts directory")
            sys.exit(1)
        drafts = sorted(DRAFTS_DIR.glob("*_V1.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not drafts:
            drafts = sorted(DRAFTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not drafts:
            print("No drafts found")
            sys.exit(1)
        latest = drafts[0]
        raw = latest.read_text()
        cleaned = cleanup_for_production(raw, dry_run=True)
        out = WORKSPACE / "output" / "final_products" / f"PREVIEW_{latest.stem}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(cleaned)
        print(f"  Preview saved: {out}")
        print(f"  Original: {len(raw)} bytes → Cleaned: {len(cleaned)} bytes")
        print(f"  Lines: {cleaned.count(chr(10))}")
        sys.exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "--share-only":
        # Share mode: find latest draft and send via Telegram
        if not DRAFTS_DIR.exists():
            print("No drafts directory")
            sys.exit(1)
        drafts = sorted(DRAFTS_DIR.glob("*_V1.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not drafts:
            print("No drafts found")
            sys.exit(1)
        latest = drafts[0]
        cfg = load_config()
        creds = get_minimax_credentials(cfg)
        result = send_draft_via_telegram(str(latest), creds)
        if result:
            print(f"✅ Shared: {latest.name}")
            sys.exit(0)
        else:
            print(f"❌ Failed to share: {latest.name}")
            sys.exit(1)
    else:
        sys.exit(main())
