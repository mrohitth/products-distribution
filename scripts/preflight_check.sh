#!/usr/bin/env bash
#============================================================
# preflight_check.sh — Green Light Script
# Human Infrastructure Deployment | Phase 4 Pre-Flight
#============================================================
# Run this before any production pipeline push.
# Exit codes: 0 = all green, 1 = one or more failures.
#============================================================

set -euo pipefail

WORKSPACE="${HOME}/.openclaw/workspace"

# ANSI color codes — use printf %b to interpret them
RED="\033[0;31m"; GREEN="\033[0;32m"; YELLOW="\033[1;33m"; NC="\033[0m"

pass() { printf '%b%s%b\n' "$GREEN" "  ✅  $1" "$NC"; }
fail() { printf '%b%s%b\n' "$RED"   "  ❌  $1" "$NC"; }
warn() { printf '%b%s%b\n' "$YELLOW" "  ⚠️   $1" "$NC"; }
info() { printf '       %s\n' "$1"; }

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   PRE-FLIGHT CHECK — Human Infrastructure v1     ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

EXIT_CODE=0

#─────────────────────────────────────────────────────────
# 1. PDF Generation stack (WeasyPrint primary, Pandoc fallback)
#─────────────────────────────────────────────────────────
echo "━━ Infrastructure: PDF Generation ━━"

if command -v python3 &>/dev/null; then
    if python3 -c "import weasyprint" 2>/dev/null; then
        WP_VER=$(python3 -c "import weasyprint; print(weasyprint.__version__)")
        pass "WeasyPrint ${WP_VER} (primary PDF engine)"
    else
        warn "WeasyPrint not installed — run: pip3 install weasyprint --break-system-packages"
    fi
else
    fail "python3 not found"
    EXIT_CODE=1
fi

if command -v pandoc &>/dev/null; then
    PANDOC_VERSION=$(pandoc --version 2>&1 | head -1)
    if command -v xelatex &>/dev/null; then
        pass "Pandoc + XeLaTeX (fallback PDF engine)"
    else
        warn "Pandoc ${PANDOC_VERSION#pandoc } installed, XeLaTeX missing (WeasyPrint is primary)"
    fi
else
    info "Pandoc not found — WeasyPrint handles all PDF generation"
fi

#─────────────────────────────────────────────────────────
# 2. GitHub integration
#─────────────────────────────────────────────────────────
echo ""
echo "━━ GitHub Integration ━━"

GH_TOKEN=""

# Check env token first
if [[ -n "${GH_TOKEN:-}" ]]; then
    pass "GH_TOKEN found in environment"
elif [[ -n "${GITHUB_TOKEN:-}" ]]; then
    pass "GITHUB_TOKEN found in environment"
    GH_TOKEN="$GITHUB_TOKEN"
elif [[ -f "${HOME}/.git-credentials" ]]; then
    # Extract token from git-credentials
    TOKEN_LINE=$(grep "github.com" "${HOME}/.git-credentials" 2>/dev/null | head -1 || true)
    if [[ -n "$TOKEN_LINE" ]]; then
        # Extract part after ://
        TOKEN_PART=${TOKEN_LINE##*://}
        TOKEN_PART=${TOKEN_PART%%@*}
        # Split on ':' — format is username:token
        if [[ "$TOKEN_PART" == *:* ]]; then
            GH_TOKEN="${TOKEN_PART#*:}"   # everything after the first ':'
            pass "GitHub token extracted from ~/.git-credentials"
        elif [[ -n "$TOKEN_PART" ]]; then
            GH_TOKEN="$TOKEN_PART"
            pass "GitHub token extracted from ~/.git-credentials"
        fi
    fi
else
    warn "No GH_TOKEN / GITHUB_TOKEN env var and no ~/.git-credentials found"
fi

# Validate token by calling GitHub API
if [[ -n "$GH_TOKEN" ]]; then
    API_RESP=$(curl -s -o /dev/null -w "%{http_code}" \
        "https://api.github.com/user" \
        -H "Authorization: Bearer $GH_TOKEN" \
        2>/dev/null || echo "000")
    if [[ "$API_RESP" == "200" ]]; then
        pass "GitHub token validated (API: 200 OK)"
    else
        fail "GitHub token invalid (API: ${API_RESP})"
        EXIT_CODE=1
    fi
fi

# Check gh CLI
if command -v gh &>/dev/null; then
    GH_VER=$(gh --version 2>&1 | head -1)
    pass "gh CLI installed: ${GH_VER#gh version }"
else
    info "gh CLI not in PATH (API-only mode works fine)"
fi

#─────────────────────────────────────────────────────────
# 3. CSS / Template paths
#─────────────────────────────────────────────────────────
echo ""
echo "━━ Template Paths ━━"

CSS_PATH="${WORKSPACE}/products/assets/pandoc_style.css"
TEMPLATE_DIR="${WORKSPACE}/products/template"

if [[ -f "${CSS_PATH}" ]]; then
    pass "CSS found: $(basename "${CSS_PATH}") ($(wc -c < "${CSS_PATH}") bytes)"
else
    fail "CSS not found: ${CSS_PATH}"
    EXIT_CODE=1
fi

if [[ -d "${TEMPLATE_DIR}" ]]; then
    TEMPLATE_COUNT=$(find "${TEMPLATE_DIR}" -name "*.md" | wc -l)
    pass "Template dir OK: ${TEMPLATE_COUNT} template(s) found"
else
    warn "Template dir not found: ${TEMPLATE_DIR} (optional)"
fi

#─────────────────────────────────────────────────────────
# 4. Git state — working directory must be clean
#─────────────────────────────────────────────────────────
echo ""
echo "━━ Git State ━━"

if [[ -d "${WORKSPACE}/.git" ]]; then
    cd "${WORKSPACE}"
    if git diff --quiet && git diff --cached --quiet; then
        pass "Working directory is clean"
    else
        fail "Working directory has uncommitted changes"
        info "  Run: git status"
        info "  Commit or stash before production push"
        EXIT_CODE=1
    fi

    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    if [[ "${CURRENT_BRANCH}" == "main" ]] || [[ "${CURRENT_BRANCH}" == "master" ]]; then
        pass "On production branch: ${CURRENT_BRANCH}"
    else
        warn "Not on main/master — current: ${CURRENT_BRANCH}"
    fi
else
    warn "No git repo in workspace — git state check skipped"
fi

#─────────────────────────────────────────────────────────
# 5. Output directory writable
#─────────────────────────────────────────────────────────
echo ""
echo "━━ Output Directory ━━"

OUTPUT_DIR="${WORKSPACE}/output/final_products"
REPO_DIR="${WORKSPACE}/output/repos"

if [[ -d "${OUTPUT_DIR}" ]]; then
    if [[ -w "${OUTPUT_DIR}" ]]; then
        pass "Output dir writable: ${OUTPUT_DIR}"
    else
        fail "Output dir not writable: ${OUTPUT_DIR}"
        EXIT_CODE=1
    fi
else
    if mkdir -p "${OUTPUT_DIR}" 2>/dev/null; then
        pass "Output dir created: ${OUTPUT_DIR}"
    else
        fail "Cannot create output dir: ${OUTPUT_DIR}"
        EXIT_CODE=1
    fi
fi

#─────────────────────────────────────────────────────────
# 6. Pipeline scripts
#─────────────────────────────────────────────────────────
echo ""
echo "━━ Pipeline Scripts ━━"

PIPELINE_SCRIPT="${WORKSPACE}/scripts/pipeline_manager.py"
CHAIN_SCRIPT="${WORKSPACE}/scripts/pipeline_chain.sh"
FEEDBACK_SCRIPT="${WORKSPACE}/scripts/marketbot_feedback.py"

for script in "${PIPELINE_SCRIPT}" "${CHAIN_SCRIPT}" "${FEEDBACK_SCRIPT}"; do
    if [[ -f "${script}" ]]; then
        pass "$(basename "${script}")"
    else
        warn "$(basename "${script}") not found"
    fi
done

# Python syntax check
if command -v python3 &>/dev/null; then
    if python3 -m py_compile "${PIPELINE_SCRIPT}" 2>/dev/null; then
        pass "pipeline_manager.py: syntax OK"
    else
        fail "pipeline_manager.py: syntax error"
        EXIT_CODE=1
    fi
    if python3 -m py_compile "${FEEDBACK_SCRIPT}" 2>/dev/null; then
        pass "marketbot_feedback.py: syntax OK"
    else
        fail "marketbot_feedback.py: syntax error"
        EXIT_CODE=1
    fi
fi

#─────────────────────────────────────────────────────────
# 7. Network / connectivity
#─────────────────────────────────────────────────────────
echo ""
echo "━━ Connectivity ━━"

if curl -s --max-time 5 https://api.github.com/zen &>/dev/null; then
    pass "GitHub API reachable"
else
    warn "GitHub API not reachable — check internet/proxy"
fi

if curl -s --max-time 5 https://fonts.googleapis.com/ &>/dev/null; then
    pass "Google Fonts API reachable (for CSS @import)"
else
    warn "Google Fonts not reachable — fonts will fall back to system defaults"
fi

#─────────────────────────────────────────────────────────
# 8. Python dependencies
#─────────────────────────────────────────────────────────
echo ""
echo "━━ Python Dependencies ━━"

DEPS="weasyprint markdown fastapi uvicorn"
for dep in $DEPS; do
    if python3 -c "import ${dep%% *}" 2>/dev/null; then
        pass "$dep"
    else
        warn "$dep not installed"
    fi
done

#─────────────────────────────────────────────────────────
# SUMMARY
#─────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   PRE-FLIGHT SUMMARY                              ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

if [[ ${EXIT_CODE} -eq 0 ]]; then
    pass "ALL SYSTEMS GO — pipeline is clear for production"
    echo ""
    echo "  Next steps:"
    echo "    GH_TOKEN=... python3 ${PIPELINE_SCRIPT}  # Run full pipeline"
    echo "    python3 ${FEEDBACK_SCRIPT} --port 5000   # Start webhook listener"
    echo "    bash ${WORKSPACE}/scripts/preflight_check.sh  # Re-verify"
    echo ""
else
    fail "BLOCKED — one or more pre-flight checks failed"
    echo ""
    echo "  Fix the issues above, then re-run this script."
    echo ""
fi

exit ${EXIT_CODE}
