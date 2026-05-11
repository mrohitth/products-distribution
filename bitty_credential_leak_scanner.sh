#!/bin/bash
#
# bitty_credential_leak_scanner.sh — Bitty Credential Leak Scanner
# Scans all workspace repos for hardcoded secrets: tokens, keys, passwords.
# Runs every 6h via cron. Silent if clean; alerts Telegram if anything found.
#
set -euo pipefail

WORKSPACE="/home/mathew/.openclaw/workspace"
LOG_PREFIX="[CRED-SCAN]"

log()  { echo "$(date '+%Y-%m-%d %I:%M:%S %p ET') $LOG_PREFIX $*"; }
crit() { echo "$(date '+%Y-%m-%d %I:%M:%S %p ET') [CRIT] $LOG_PREFIX $*"; FOUND=1; }

FOUND=0
ISSUES=""

# Token patterns
TOKEN_PAT='(ghp_|gho_|github_pat_)[A-Za-z0-9_]{20,}'
AWS_PAT='AKIA[A-Z0-9]{16}'

log "Starting credential scan..."

# Scan files in workspace repos (excluding node_modules, dist, .git, __pycache__)
for repo_dir in \
    /home/mathew/.openclaw/workspace \
    /home/mathew/workspace/oasis-redesign \
    /home/mathew/workspace/katzen \
    /home/mathew/MarketBot; do

  [[ -d "$repo_dir" ]] || continue
  name=$(basename "$repo_dir")

  while IFS= read -r -d '' file; do
    if grep -qPIE "$TOKEN_PAT|$AWS_PAT" "$file" 2>/dev/null; then
      crit "LEAK: $name — ${file#$repo_dir/}"
      token=$(grep -Po "$TOKEN_PAT|$AWS_PAT" "$file" 2>/dev/null | head -1 || echo "found")
      crit "  Token: ${token:0:12}..."
      ISSUES="${ISSUES}LEAK in $name/${file#$repo_dir/}; "
      FOUND=1
    fi
  done < <(find "$repo_dir" -type f \
    \( -path "*/.git/*" -o -path "*/node_modules/*" -o -path "*/dist/*" \
       -o -path "*/.next/*" -o -path "*/build/*" -o -path "*/__pycache__/*" \
       -o -path "*/.env" \) -prune -o \
    -type f -print0 2>/dev/null)

  # Check for .git-credentials files (flat-file credential store — should not exist)
  for git_cred_file in ~/.git-credentials ~/.config/git/credentials; do
    if [[ -s "$git_cred_file" ]]; then
      crit "LEAK: $name — $git_cred_file exists with plaintext credentials (use gh auth setup-git instead)"
      ISSUES="${ISSUES}GIT_CRED_FILE $git_cred_file; "
      FOUND=1
    fi
  done

  # Check git remotes for embedded tokens
  remote=$(git -C "$repo_dir" remote get-url origin 2>/dev/null || echo "")
  if [[ -n "$remote" ]] && [[ "$remote" != git@*github.com* ]] && [[ "$remote" == *@*github.com* ]]; then
    crit "LEAK: $name — embedded token in git remote URL"
    ISSUES="${ISSUES}EMBEDDED TOKEN in $name git remote; "
    FOUND=1
  fi
done

# Check workspace .env and oasis-redesign .env (NOT MarketBot/.env — gitignored by design)
for env_file in \
    /home/mathew/.openclaw/workspace/.env \
    /home/mathew/workspace/oasis-redesign/.env; do
  [[ -f "$env_file" ]] || continue
  if grep -qE "TOKEN|PASSWORD|SECRET|KEY" "$env_file" 2>/dev/null; then
    if ! grep -qE "your_token|example|placeholder|xxx|changeme" "$env_file" 2>/dev/null; then
      crit "WARN: $env_file contains what looks like real credentials"
      ISSUES="${ISSUES}Credentials in $env_file; "
      FOUND=1
    fi
  fi
done

# Result
if (( FOUND == 1 )); then
  echo "CRITICAL: Credential leak(s) detected!"
  echo "Issues: ${ISSUES:-none}"
  exit 1
else
  log "Clean — no exposed credentials detected"
  exit 0
fi
