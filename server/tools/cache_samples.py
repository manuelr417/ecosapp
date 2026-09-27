"""Pre-compute canned annotations and narrations for demo sample images.

Run this during talk-day prep after replacing the Act 2 placeholders
with real lab images:

    .venv/bin/python tools/cache_samples.py --with-narrations

Requires ROBOFLOW_API_KEY and ROBOFLOW_MODEL for Act 2 annotations.
Narrations are generated through the primary LLM endpoint; without
--with-narrations, existing canned narrations are left untouched.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVER_DIR))

from openai import OpenAI  # noqa: E402

from app.cells import RoboflowClient, CellServiceError  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.narration import NARRATION_SYSTEM_PROMPT  # noqa: E402

PROJECT_DIR = SERVER_DIR.parent
SAMPLES_DIR = PROJECT_DIR / "client" / "public" / "samples"
CANNED_DIR = SERVER_DIR / "canned"

FALLBACK_GENERIC_NARRATION = (
    "Even my robot eyes could not spot anything familiar in that one! "
    "Let's try another photo. Remember: AI can only recognize what it "
    "has been taught to look for."
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def summarize(detections: list[dict]) -> str:
    if not detections:
        return "No cell clusters were found in this microscope image. Tell the audience that in a fun way."
    counts = {}
    for d in detections:
        counts[d["label"]] = counts.get(d["label"], 0) + 1
    parts = [f"{v} {k}{'s' if v > 1 else ''}" for k, v in counts.items()]
    return (
        "This is a microscope image. I found " + ", ".join(parts) + ". "
        "Describe them to high school students in a fun way."
    )


def generate_narration(settings, detections: list[dict]) -> str:
    client = OpenAI(base_url=settings.llm_primary_base_url, api_key="local", timeout=30.0)
    completion = client.chat.completions.create(
        model=settings.llm_primary_model,
        messages=[
            {"role": "system", "content": NARRATION_SYSTEM_PROMPT},
            {"role": "user", "content": summarize(detections)},
        ],
        max_tokens=100,
    )
    return completion.choices[0].message.content.strip()


def write_manifest() -> dict:
    manifest = {"act1": [], "act2": []}
    for act in ("act1", "act2"):
        act_dir = SAMPLES_DIR / act
        if not act_dir.exists():
            continue
        for image in sorted(act_dir.glob("*.jpg")):
            manifest[act].append(
                {"id": image.stem, "file": f"samples/{act}/{image.name}"}
            )
    (SAMPLES_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-narrations", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    annotations_path = CANNED_DIR / "annotations.json"
    narrations_path = CANNED_DIR / "narrations.json"
    annotations = load_json(annotations_path)
    narrations = load_json(narrations_path)
    roboflow = RoboflowClient(settings.roboflow_api_key, settings.roboflow_model)

    act2_dir = SAMPLES_DIR / "act2"
    annotated = 0
    errors = []
    if act2_dir.exists():
        import asyncio

        for image in sorted(act2_dir.glob("*.jpg")):
            data = image.read_bytes()
            digest = sha256(data)
            try:
                detections = asyncio.run(roboflow.infer(data))
            except CellServiceError as exc:
                errors.append(f"{image.name}: {exc}")
                continue
            annotations[digest] = {
                "image": f"act2/{image.name}",
                "detections": [json.loads(d.model_dump_json()) for d in detections],
            }
            annotated += 1
            if args.with_narrations:
                narrations[digest] = generate_narration(settings, annotations[digest]["detections"])

    narrations.setdefault("_generic", FALLBACK_GENERIC_NARRATION)

    CANNED_DIR.mkdir(parents=True, exist_ok=True)
    annotations_path.write_text(json.dumps(annotations, indent=2))
    narrations_path.write_text(json.dumps(narrations, indent=2))
    manifest = write_manifest()

    print(f"annotated {annotated} act2 images; manifest has "
          f"{len(manifest['act1'])} act1 and {len(manifest['act2'])} act2 samples")
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
