#!/usr/bin/env bash
# Fetch the latest ΠΡΟΓΡΑΜΜΑ and, if anything changed, commit and push it.
# The push triggers .github/workflows/pages.yml, which rebuilds the site.
set -euo pipefail
cd "$(dirname "$0")"

git pull -q --ff-only
./fetch_programma.py

git add -A pdfs programma-latest.pdf .state.json
if git diff --cached --quiet; then
  echo "Nothing to push."
  exit 0
fi
if git diff --cached --quiet -- pdfs; then
  msg="Update .state.json"  # same PDF, new ETag/Last-Modified
else
  msg="New: $(python3 -c 'import json; print(json.load(open(".state.json"))["title"])')"
fi
git commit -q -m "$msg"
git push -q
echo "Pushed: $msg"
