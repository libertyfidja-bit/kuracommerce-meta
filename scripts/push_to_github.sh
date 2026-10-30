#!/usr/bin/env bash
# Commit and push everything to GitHub from your Codespace terminal.
# Usage:  bash scripts/push_to_github.sh "your commit message"
set -euo pipefail

# Always run from the repository root, wherever the script is called from
cd "$(git rev-parse --show-toplevel)"

MSG="${1:-}"
if [ -z "$MSG" ]; then
  read -r -p "Commit message: " MSG
fi
[ -n "$MSG" ] || { echo "A commit message is required."; exit 1; }

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "Repository: $(git remote get-url origin)"
echo "Branch:     $BRANCH"

# Safety: never commit secrets
if git ls-files --error-unmatch .env >/dev/null 2>&1 || git ls-files --error-unmatch backend/.env >/dev/null 2>&1; then
  echo "STOP: a .env file is tracked by git. Run:  git rm --cached .env backend/.env"
  echo "Then rotate your META_API_KEY, because it may already be in the history."
  exit 1
fi

git add -A

# Safety: refuse if a .env or database file slipped into the staging area
if git diff --cached --name-only | grep -E '(^|/)\.env$|\.db$|\.sqlite3$' >/dev/null; then
  echo "STOP: a .env or database file is staged. Check .gitignore, then run: git reset"
  exit 1
fi

if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -m "$MSG"
fi

git pull --rebase origin "$BRANCH" || { echo "Pull/rebase had conflicts. Fix them, then run: git rebase --continue"; exit 1; }
git push origin "$BRANCH"
echo "Done. Pushed to origin/$BRANCH."
