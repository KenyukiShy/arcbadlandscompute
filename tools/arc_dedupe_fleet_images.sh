#!/usr/bin/env bash
# arc_dedupe_fleet_images.sh
# Removes 22 confirmed byte-for-byte duplicate photos (keeps the descriptive
# filename, drops the old plain-numbered one), and gitignores aider's local
# tool-state files that shouldn't be in a public repo. Read-only until you
# confirm — prints what it WOULD remove first, only deletes with --apply.

set -euo pipefail
REPO="/home/kjonescbplus/arc_mirror/MyFiles/GCP/arcbadlands-site/arcbadlands-site"
MODE="${1:-}"

cd "$REPO"

# Pairs confirmed identical via md5sum — format: "keep|remove"
PAIRS=(
  "fleet_assets/TownCar/03_TownCar_Side_Profile.jpg|fleet_assets/TownCar/03_TC.jpg"
  "fleet_assets/TownCar/10_TownCar_Door_Controls.jpg|fleet_assets/TownCar/10_TC.jpg"
  "fleet_assets/TownCar/17_TC_Trunk.jpg|fleet_assets/TownCar/15_TC.jpg"
  "fleet_assets/MKZ/01_MKZ_Exterior_Front.jpg|fleet_assets/MKZ/01_MKZ.jpg"
  "fleet_assets/Jayco/02_Jayco_Entry.jpg|fleet_assets/Jayco/02_Camper_Exterior_Entry.jpg"
  "fleet_assets/Jayco/02_Jayco_Entry.jpg|fleet_assets/Jayco/05_Jayco.jpg"
  "fleet_assets/MKZ/03_MKZ_Driver_Gauges.jpg|fleet_assets/MKZ/03_MKZ.jpg"
  "fleet_assets/Jayco/13_Jayco_Bed.jpg|fleet_assets/Jayco/04_Jayco.jpg"
  "fleet_assets/Jayco/13_Jayco_Bed.jpg|fleet_assets/Jayco/17_Jayco_Underside.jpg"
  "fleet_assets/Jayco/15_Jayco_Jacks.jpg|fleet_assets/Jayco/03_Jayco.jpg"
  "fleet_assets/Jayco/01_Jayco.jpg|fleet_assets/Jayco/01_Camper_Exterior_Rear_Angle.jpg"
  "fleet_assets/Jayco/01_Jayco.jpg|fleet_assets/Jayco/08_Jayco_Rear.jpg"
  "fleet_assets/TownCar/06_TownCar_Wheel_Detail.jpg|fleet_assets/TownCar/06_TC.jpg"
  "fleet_assets/Jayco/14_Jayco_Panel.jpg|fleet_assets/Jayco/08_Jayco.jpg"
  "fleet_assets/TownCar/12_TownCar_Headlight_Detail.jpg|fleet_assets/TownCar/12_TC.jpg"
  "fleet_assets/TownCar/11_TownCar_Center_Stack.jpg|fleet_assets/TownCar/11_TC.jpg"
  "fleet_assets/Jayco/10_Jayco.jpg|fleet_assets/Jayco/02_Jayco.jpg"
  # NOTE: 09_F350_Extra.jpg / 13_F350.jpg are also identical — NOT auto-removed,
  # since 13 may be a distinct vehicle-slot placeholder. Check manually first.
  "fleet_assets/Jayco/11_Jayco_Fireplace.jpg|fleet_assets/Jayco/06_Jayco.jpg"
  "fleet_assets/TownCar/05_TownCar_Rear.jpg|fleet_assets/TownCar/05_TC.jpg"
  "fleet_assets/Jayco/12_Jayco_Bunks.jpg|fleet_assets/Jayco/06_Jayco_Bunks.jpg"
  "fleet_assets/TownCar/02_TownCar_Front.jpg|fleet_assets/TownCar/02_TC.jpg"
)

echo "=== F350 13 vs 09 — needs your manual check, not auto-removed ==="
echo "fleet_assets/F350/09_F350_Extra.jpg and fleet_assets/F350/13_F350.jpg are byte-identical."
echo "If f350.html references both as separate photos, one slot is showing a duplicate image."
echo

total_bytes=0
for pair in "${PAIRS[@]}"; do
  keep="${pair%%|*}"
  remove="${pair##*|}"
  if [ -f "$remove" ]; then
    sz=$(stat -c%s "$remove" 2>/dev/null || echo 0)
    total_bytes=$((total_bytes + sz))
    if [ "$MODE" = "--apply" ]; then
      # Also remove the matching .meta.json sidecar for the removed duplicate, if present
      git rm -q "$remove" 2>/dev/null || rm -f "$remove"
      [ -f "${remove}.meta.json" ] && { git rm -q "${remove}.meta.json" 2>/dev/null || rm -f "${remove}.meta.json"; }
      echo "REMOVED: $remove  (kept: $keep)"
    else
      echo "WOULD REMOVE: $remove  (${sz} bytes, kept: $keep)"
    fi
  else
    echo "SKIP (already gone): $remove"
  fi
done

echo
echo "Total reclaimed: $((total_bytes / 1024)) KB"

if [ "$MODE" = "--apply" ]; then
  echo "tools/*.json" > /tmp/gitignore_check
  grep -qxF "tools/*.json" .gitignore 2>/dev/null || echo "tools/*.json" >> .gitignore
  grep -qxF ".aider*" .gitignore 2>/dev/null || echo ".aider*" >> .gitignore
  echo
  echo "=== Updated .gitignore ==="
  cat .gitignore
  echo
  echo "Run 'git status' to review, then commit:"
  echo '  git add -A'
  echo '  git commit -m "chore: remove 21 duplicate fleet photos (6.9MB), gitignore aider local state"'
else
  echo
  echo "Dry run only. Re-run with --apply to actually remove files and update .gitignore."
fi
