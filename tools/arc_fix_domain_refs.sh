#!/usr/bin/env bash
# arc_fix_domain_refs.sh
# Fixes dead shy2shy.github.io domain refs + stale local phone number
# across the canonical arcbadlandscompute repo.
#
# Usage:
#   ./arc_fix_domain_refs.sh            (dry run — shows what's broken, no changes)
#   ./arc_fix_domain_refs.sh --apply    (fixes files, then offers to commit+push)

set -euo pipefail

REPO="/home/kjonescbplus/arc_mirror/MyFiles/GCP/arcbadlands-site/arcbadlands-site"
OLD_DOMAIN="shy2shy.github.io/arcbadlands-site"
NEW_DOMAIN="kenyukishy.github.io/arcbadlandscompute"
OLD_PHONE="870-5235"
NEW_PHONE="888-5090"

MODE="${1:-}"

cd "$REPO"

echo "== Files referencing dead domain ($OLD_DOMAIN) =="
grep -rl "$OLD_DOMAIN" . --include="*.html" || echo "  none found"

echo
echo "== Files referencing dead local number ($OLD_PHONE) =="
grep -rl "$OLD_PHONE" . --include="*.html" || echo "  none found"

echo
echo "== NOT touched (separate biz contacts, confirm separately) =="
grep -rln "@shy2shy\.com" . --include="*.html" || echo "  none found"

if [ "$MODE" = "--apply" ]; then
  echo
  echo "== Applying fixes =="
  grep -rl "$OLD_DOMAIN" . --include="*.html" | xargs -r sed -i "s#${OLD_DOMAIN}#${NEW_DOMAIN}#g"
  grep -rl "$OLD_PHONE" . --include="*.html" | xargs -r sed -i "s/${OLD_PHONE}/${NEW_PHONE}/g"

  echo
  echo "== Verify: both should return nothing =="
  grep -rn "$OLD_DOMAIN" . --include="*.html" || echo "  clean: domain"
  grep -rn "$OLD_PHONE" . --include="*.html" || echo "  clean: phone"

  echo
  echo "== git status =="
  git status -s

  echo
  read -rp "Commit and push these changes? [y/N] " CONFIRM
  if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    git add -A
    git commit -m "fix: unify domain to kenyukishy.github.io/arcbadlandscompute, correct SMS opt-out number to 888-5090"
    git push
    echo "Pushed."
  else
    echo "Skipped commit/push — changes are on disk only, uncommitted."
  fi
else
  echo
  echo "(dry run only — no files changed. Re-run with --apply to fix.)"
fi
