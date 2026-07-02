#!/usr/bin/env python3
"""
arc_vertex_inventory.py

Scans ALL fleet_assets/*/ folders and classifies every image with Vertex AI —
which vehicle it actually shows, or flags it as non-vehicle content (financial
docs, screenshots, unrelated photos, etc). Writes a JSON manifest ONLY.
Does NOT move, rename, or overwrite any meta.json files.

Review the manifest, edit it if needed, THEN run arc_vertex_apply_sort.py
against it to actually move files.

Usage:
    python arc_vertex_inventory.py --root fleet_assets --out inventory.json
    python arc_vertex_inventory.py --root fleet_assets --out inventory.json --limit 5
"""

import argparse
import json
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

PROJECT = "commplex-493805"
LOCATION = "us-central1"
MODEL = "gemini-2.5-flash"

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

CLASSIFY_PROMPT = """Look at this image carefully and classify it.

Valid vehicle categories (these are for sale listings):
- F350: 2006 Ford F-350 King Ranch truck, saddle leather interior
- TownCar: 1988 Lincoln Town Car, white exterior, blue interior
- MKZ: 2016 Lincoln MKZ Hybrid, bronze/gold/champagne/silver exterior, black interior
- Jayco: Jayco Eagle fifth wheel travel trailer/RV, bunkhouse floorplan

If the image does NOT clearly match one of these four vehicles — including if
it's a document, screenshot, financial/bank record, unrelated photo, or any
other RV/vehicle that isn't the Jayco Eagle described above — classify it as
"OTHER" and describe what it actually is.

Respond with ONLY a JSON object, no markdown fences, no preamble:
{"category": "F350|TownCar|MKZ|Jayco|OTHER", "caption": "<4-8 word description of what's actually shown>", "flag_sensitive": true|false}

Set flag_sensitive to true if the image contains any financial information,
account numbers, personal documents, screenshots of apps/websites unrelated
to vehicles, or anything that looks like it doesn't belong in a public vehicle
sales gallery.
"""


def load_client():
    return genai.Client(vertexai=True, project=PROJECT, location=LOCATION)


def classify_image(client, image_path: Path) -> dict:
    img_bytes = image_path.read_bytes()
    mime = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type=mime),
            CLASSIFY_PROMPT,
        ],
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        data = json.loads(text)
        return {
            "category": data.get("category", "OTHER"),
            "caption": data.get("caption", "").strip(),
            "flag_sensitive": bool(data.get("flag_sensitive", False)),
        }
    except (json.JSONDecodeError, KeyError):
        return {"category": "OTHER", "caption": text[:80], "flag_sensitive": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Path to fleet_assets/ root")
    ap.add_argument("--out", required=True, help="Path to write JSON manifest")
    ap.add_argument("--limit", type=int, default=None, help="Only process first N images total (spot-check)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    all_images = []
    for subfolder in sorted(root.iterdir()):
        if not subfolder.is_dir():
            continue
        for img in sorted(subfolder.iterdir()):
            if img.suffix.lower() in IMAGE_EXTS:
                all_images.append((subfolder.name, img))

    if args.limit:
        all_images = all_images[: args.limit]

    print(f"Classifying {len(all_images)} images across {root}")

    client = load_client()
    manifest = []
    sensitive_hits = []

    for current_folder, img_path in all_images:
        try:
            result = classify_image(client, img_path)
        except Exception as e:
            print(f"  ERROR on {img_path}: {e}", file=sys.stderr)
            continue

        entry = {
            "current_path": str(img_path),
            "current_folder": current_folder,
            "detected_category": result["category"],
            "caption": result["caption"],
            "flag_sensitive": result["flag_sensitive"],
            "mismatch": result["category"] != current_folder,
        }
        manifest.append(entry)

        tag = "SENSITIVE" if result["flag_sensitive"] else ("MISMATCH" if entry["mismatch"] else "ok")
        print(f"  [{tag}] {img_path} -> {result['category']}: {result['caption']}")

        if result["flag_sensitive"]:
            sensitive_hits.append(str(img_path))

        time.sleep(1.0)

    Path(args.out).write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nWrote {len(manifest)} entries to {args.out}")

    mismatches = [m for m in manifest if m["mismatch"]]
    print(f"Mismatched folder: {len(mismatches)}")
    if sensitive_hits:
        print(f"\n*** {len(sensitive_hits)} SENSITIVE FILES FLAGGED — review before doing anything else: ***")
        for s in sensitive_hits:
            print(f"  {s}")


if __name__ == "__main__":
    main()
