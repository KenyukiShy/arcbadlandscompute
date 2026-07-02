#!/usr/bin/env python3
"""
arc_vertex_ocr_payments.py

OCRs the Zelle/bank payment screenshots pulled during Wave 0 and extracts
structured fields (date, amount, counterparty, memo) plus a best-guess
vehicle attribution (MKZ vs TownCar vs Unclear) based on keyword matches
in the memo/description text. Writes a JSON manifest ONLY — does not move,
rename, publish, or delete anything.

This does NOT decide what goes public. Review the manifest yourself, then
route each file: keep private in the evidence folder, or copy the specific
approved image into a public fleet_assets/<Vehicle>/ or evidence page.

Usage:
    python arc_vertex_ocr_payments.py --folder ~/Documents/Tax/MKZ_Evidence/PaymentProof --out payments_ocr.json
    python arc_vertex_ocr_payments.py --folder fleet_assets/F350 --out payments_ocr.json --limit 3
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

PROJECT = "commplex-493805"
LOCATION = "us-central1"
MODEL = "gemini-2.5-flash"

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

# Keywords that hint at which vehicle a payment/memo relates to.
VEHICLE_KEYWORDS = {
    "MKZ": ["mkz", "lincoln mkz", "autostar", "auto star", "shipper", "transport",
            "carrier", "hauling", "pickup", "sherrie", "doug", "appleby"],
    "TownCar": ["town car", "towncar", "1988 lincoln", "town-car"],
}

OCR_PROMPT = """This is a screenshot of a bank app, Zelle, or mobile payment transaction.

Read every piece of text visible in the image carefully, including small print,
and extract the following as JSON. If a field isn't visible, use null.

{
  "platform": "<Zelle|bank app name|other, as shown>",
  "date": "<date exactly as shown, or null>",
  "amount": "<dollar amount exactly as shown, or null>",
  "counterparty_name": "<the other party's name/business as shown, or null>",
  "memo_or_description": "<any memo, note, or description text visible, or null>",
  "reference_or_confirmation_number": "<if visible, or null>",
  "full_ocr_text": "<all readable text in the image, verbatim, newline-separated>"
}

Respond with ONLY the JSON object, no markdown fences, no preamble.
"""


def load_client():
    return genai.Client(vertexai=True, project=PROJECT, location=LOCATION)


def ocr_image(client, image_path: Path) -> dict:
    img_bytes = image_path.read_bytes()
    mime = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type=mime),
            OCR_PROMPT,
        ],
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "platform": None, "date": None, "amount": None,
            "counterparty_name": None, "memo_or_description": None,
            "reference_or_confirmation_number": None,
            "full_ocr_text": text[:500],
        }


def guess_vehicle(ocr: dict) -> tuple[str, list[str]]:
    haystack = " ".join(str(ocr.get(k, "") or "") for k in
                         ("counterparty_name", "memo_or_description", "full_ocr_text")).lower()
    hits = {v: [kw for kw in kws if kw in haystack] for v, kws in VEHICLE_KEYWORDS.items()}
    hits = {v: kws for v, kws in hits.items() if kws}

    if len(hits) == 1:
        vehicle = next(iter(hits))
        return vehicle, hits[vehicle]
    elif len(hits) > 1:
        return "Ambiguous (multiple matches)", [kw for kws in hits.values() for kw in kws]
    else:
        return "Unclear", []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True, help="Path to folder containing payment screenshots")
    ap.add_argument("--out", required=True, help="Path to write JSON manifest")
    ap.add_argument("--limit", type=int, default=None, help="Only process first N images (spot-check)")
    args = ap.parse_args()

    folder = Path(args.folder).expanduser()
    if not folder.is_dir():
        print(f"Not a directory: {folder}", file=sys.stderr)
        sys.exit(1)

    images = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if args.limit:
        images = images[: args.limit]

    print(f"OCR'ing {len(images)} images in {folder}")

    client = load_client()
    manifest = []

    for img_path in images:
        try:
            ocr = ocr_image(client, img_path)
        except Exception as e:
            print(f"  ERROR on {img_path.name}: {e}", file=sys.stderr)
            continue

        vehicle_guess, matched_keywords = guess_vehicle(ocr)

        entry = {
            "file": str(img_path),
            "vehicle_guess": vehicle_guess,
            "matched_keywords": matched_keywords,
            **ocr,
        }
        manifest.append(entry)
        print(f"  {img_path.name}  ->  {vehicle_guess}  "
              f"(amount={ocr.get('amount')}, date={ocr.get('date')}, "
              f"counterparty={ocr.get('counterparty_name')})")

        time.sleep(1.0)

    Path(args.out).write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nWrote {len(manifest)} entries to {args.out}")

    unclear = [m for m in manifest if m["vehicle_guess"] in ("Unclear", "Ambiguous (multiple matches)")]
    if unclear:
        print(f"\n{len(unclear)} file(s) need manual review (no clean keyword match):")
        for m in unclear:
            print(f"  {m['file']}  — {m['vehicle_guess']}")


if __name__ == "__main__":
    main()
