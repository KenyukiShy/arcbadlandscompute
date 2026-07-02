#!/usr/bin/env python3
"""
arc_vertex_image_describe.py

Walks a fleet_assets/<Vehicle>/ folder, sends each image to Vertex AI Gemini
with vehicle-specific context, and writes a real upper_caption into the
matching <filename>.meta.json sidecar (preserving title/subtitle/lower_caption).

Usage:
    python arc_vertex_image_describe.py --folder fleet_assets/F350 --dry-run
    python arc_vertex_image_describe.py --folder fleet_assets/F350
    python arc_vertex_image_describe.py --folder fleet_assets/F350 --force --limit 3

Requires:
    pip install google-genai --break-system-packages
    gcloud auth application-default login   (once, if not already done)
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

VEHICLE_CONTEXT = {
    "Jayco": (
        "This is a Jayco Eagle fifth wheel travel trailer, bunkhouse floorplan, "
        "model BHS 26.5 HT. It may show exterior siding/decals/hitch/awning/jacks, "
        "or interior bunks/kitchen/fireplace/seals."
    ),
    "TownCar": (
        "This is a 1988 Lincoln Town Car, white exterior, blue interior. "
        "It may show an exterior panel/trim angle, or interior seats/dash/trunk."
    ),
    "MKZ": (
        "This is a 2016 Lincoln MKZ Hybrid. Exterior color reads as metallic "
        "light bronze/gold/champagne/silver depending on light. Black leather interior. "
        "It may show an exterior angle or interior gauges/seats/center stack."
    ),
    "F350": (
        "This is a 2006 Ford F-350 King Ranch with saddle-colored leather interior. "
        "It may show an exterior angle, bed, tires/wheels, or interior leather/console."
    ),
}

HUB_BY_VEHICLE = {
    "F350": "South East Logistics Hub",
    "TownCar": "South East Logistics Hub",
    "MKZ": "South East Logistics Hub",
    "Jayco": "South East Logistics Hub",
}

PROMPT_TEMPLATE = """{context}

Look at this specific photo and identify exactly what it shows (which part of the
vehicle, which angle, interior vs exterior, any notable detail like wear, trim,
or feature visible).

Respond with ONLY a JSON object, no markdown fences, no preamble:
{{"upper_caption": "<4-8 word title-case caption, e.g. 'Driver Seat — Saddle Leather Detail' or 'Front 3/4 Exterior — Driver Side'>"}}
"""

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def load_client():
    return genai.Client(vertexai=True, project=PROJECT, location=LOCATION)


def caption_image(client, image_path: Path, vehicle: str) -> str:
    context = VEHICLE_CONTEXT.get(vehicle, "This is a vehicle for sale.")
    prompt = PROMPT_TEMPLATE.format(context=context)

    img_bytes = image_path.read_bytes()
    mime = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type=mime),
            prompt,
        ],
    )

    text = response.text.strip()
    # strip accidental markdown fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        data = json.loads(text)
        return data["upper_caption"].strip()
    except (json.JSONDecodeError, KeyError):
        # fall back: use raw text, truncated, if model didn't follow JSON format
        return text[:80].strip()


def process_folder(folder: Path, vehicle: str, dry_run: bool, force: bool, limit: int | None):
    client = load_client() if not dry_run else None
    hub = HUB_BY_VEHICLE.get(vehicle, "Arc Badlands Logistics Hub")

    images = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if limit:
        images = images[:limit]

    print(f"Found {len(images)} images in {folder} (vehicle={vehicle})")

    for img_path in images:
        meta_path = img_path.with_suffix(img_path.suffix + ".meta.json")

        existing = {}
        if meta_path.exists():
            try:
                existing = json.loads(meta_path.read_text())
            except json.JSONDecodeError:
                existing = {}

        already_labeled = (
            existing.get("upper_caption")
            and not existing["upper_caption"].startswith("Verification Image")
        )
        if already_labeled and not force:
            print(f"  SKIP (already labeled): {img_path.name}")
            continue

        if dry_run:
            print(f"  WOULD LABEL: {img_path.name}")
            continue

        try:
            caption = caption_image(client, img_path, vehicle)
        except Exception as e:
            print(f"  ERROR on {img_path.name}: {e}", file=sys.stderr)
            continue

        new_meta = {
            "title": existing.get("title", "Asset Detail"),
            "subtitle": existing.get("subtitle", vehicle),
            "upper_caption": caption,
            "lower_caption": existing.get("lower_caption", hub),
        }
        meta_path.write_text(json.dumps(new_meta, indent=2) + "\n")
        print(f"  LABELED: {img_path.name} -> {caption}")

        time.sleep(1.0)  # gentle rate limit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True, help="Path to fleet_assets/<Vehicle> folder")
    ap.add_argument("--dry-run", action="store_true", help="List what would be labeled, no API calls")
    ap.add_argument("--force", action="store_true", help="Re-label images that already have a real caption")
    ap.add_argument("--limit", type=int, default=None, help="Only process first N images (for spot-checking)")
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Not a directory: {folder}", file=sys.stderr)
        sys.exit(1)

    vehicle = folder.name  # e.g. "F350", "Jayco", "MKZ", "TownCar"
    if vehicle not in VEHICLE_CONTEXT:
        print(f"WARNING: no VEHICLE_CONTEXT entry for '{vehicle}' — using generic context.", file=sys.stderr)

    process_folder(folder, vehicle, args.dry_run, args.force, args.limit)


if __name__ == "__main__":
    main()
