"""Generate placeholder demo samples and their canned annotations.

Creates Act 1 samples from bundled ultralytics assets and synthetic
Act 2 "microscopy" placeholders with known cluster positions, then
writes server/canned/annotations.json and the client sample manifest.

Replace the Act 2 placeholders with real lab images and run
tools/cache_samples.py to regenerate annotations for production use.
"""

import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVER_DIR))

PROJECT_DIR = SERVER_DIR.parent
SAMPLES_DIR = PROJECT_DIR / "client" / "public" / "samples"
CANNED_DIR = SERVER_DIR / "canned"

ACT1_SOURCES = ("bus.jpg", "zidane.jpg")

BLOB_LAYOUTS = {
    "cells-01.jpg": [
        (0.18, 0.22, 0.10),
        (0.55, 0.35, 0.13),
        (0.80, 0.70, 0.09),
        (0.35, 0.78, 0.08),
    ],
    "cells-02.jpg": [
        (0.30, 0.30, 0.12),
        (0.70, 0.25, 0.08),
        (0.62, 0.68, 0.11),
        (0.15, 0.65, 0.07),
        (0.88, 0.50, 0.06),
    ],
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_microscopy_placeholder(path: Path, blobs) -> bytes:
    size = 640
    image = Image.new("RGB", (size, size), (12, 10, 16))
    draw = ImageDraw.Draw(image)
    import random

    rng = random.Random(42)
    for _ in range(240):
        x, y = rng.randint(0, size), rng.randint(0, size)
        r = rng.randint(0, 1)
        shade = rng.randint(28, 60)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(shade, shade, shade + 6))
    glow = Image.new("RGB", (size, size), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for cx, cy, radius in blobs:
        px, py, pr = int(cx * size), int(cy * size), int(radius * size)
        glow_draw.ellipse(
            (px - pr, py - pr, px + pr, py + pr), fill=(235, 240, 250)
        )
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    image = Image.composite(glow, image, glow.convert("L"))
    image = image.filter(ImageFilter.GaussianBlur(0.5))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    path.write_bytes(buffer.getvalue())
    return buffer.getvalue()


def placeholder_annotations(blobs) -> list[dict]:
    detections = []
    for cx, cy, radius in blobs:
        x1 = max(0.0, cx - radius)
        y1 = max(0.0, cy - radius)
        x2 = min(1.0, cx + radius)
        y2 = min(1.0, cy + radius)
        detections.append(
            {"label": "cell cluster", "confidence": 0.93, "bbox": [x1, y1, x2, y2]}
        )
    return detections


def write_manifest():
    manifest = {"act1": [], "act2": []}
    for act in ("act1", "act2"):
        act_dir = SAMPLES_DIR / act
        act_dir.mkdir(parents=True, exist_ok=True)
        for image in sorted(act_dir.glob("*.jpg")):
            manifest[act].append(
                {"id": image.stem, "file": f"samples/{act}/{image.name}"}
            )
    (SAMPLES_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main():
    for act in ("act1", "act2"):
        (SAMPLES_DIR / act).mkdir(parents=True, exist_ok=True)
    annotations_path = CANNED_DIR / "annotations.json"
    annotations = (
        json.loads(annotations_path.read_text()) if annotations_path.exists() else {}
    )

    import ultralytics

    assets = Path(ultralytics.__file__).parent / "assets"
    for name in ACT1_SOURCES:
        source = assets / name
        if source.exists():
            shutil.copy(source, SAMPLES_DIR / "act1" / name)

    for name, blobs in BLOB_LAYOUTS.items():
        data = make_microscopy_placeholder(SAMPLES_DIR / "act2" / name, blobs)
        annotations[sha256(data)] = {"image": f"act2/{name}", "detections": placeholder_annotations(blobs)}

    CANNED_DIR.mkdir(parents=True, exist_ok=True)
    annotations_path.write_text(json.dumps(annotations, indent=2))
    manifest = write_manifest()
    print(f"annotations for {len(BLOB_LAYOUTS)} placeholders written")
    print(f"manifest: {json.dumps(manifest)}")


if __name__ == "__main__":
    main()
