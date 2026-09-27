import base64
import io
import json

import httpx
from fastapi import HTTPException
from PIL import Image

from .detection import image_hash, load_image
from .schemas import Detection


class CellServiceError(Exception):
    pass


class RoboflowClient:
    def __init__(self, api_key: str, model: str, base_url: str = "https://detect.roboflow.com"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        if model.startswith("http"):
            self.url = model
        else:
            self.url = f"{self.base_url}/{model}"

    async def infer(self, data: bytes) -> list[Detection]:
        if not self.api_key or not self.model:
            raise CellServiceError(
                "Hosted cell detection is not configured (missing ROBOFLOW_API_KEY or ROBOFLOW_MODEL)"
            )
        image = load_image(data)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        try:
            response = await httpx.AsyncClient(timeout=15.0).post(
                self.url,
                params={"api_key": self.api_key},
                content=encoded,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise CellServiceError(str(exc)) from exc
        return self._to_detections(payload, image)

    def _to_detections(self, payload: dict, image: Image.Image) -> list[Detection]:
        width, height = image.size
        detections = []
        for pred in payload.get("predictions", []):
            cx, cy = float(pred["x"]), float(pred["y"])
            w, h = float(pred["width"]), float(pred["height"])
            x1 = max(0.0, (cx - w / 2) / width)
            y1 = max(0.0, (cy - h / 2) / height)
            x2 = min(1.0, (cx + w / 2) / width)
            y2 = min(1.0, (cy + h / 2) / height)
            detections.append(
                Detection(
                    label=str(pred.get("class", "cell cluster")),
                    confidence=round(float(pred.get("confidence", 0.0)), 4),
                    bbox=(x1, y1, x2, y2),
                )
            )
        return detections


def roboflow_client_dep():
    from .config import get_settings

    settings = get_settings()
    return RoboflowClient(settings.roboflow_api_key, settings.roboflow_model)


def lookup_cached_annotations(canned_dir, data: bytes) -> list[Detection] | None:
    annotations = load_canned(canned_dir, "annotations.json")
    if annotations is None:
        return None
    entry = annotations.get(image_hash(data))
    if entry is None:
        return None
    return [Detection(**d) for d in entry["detections"]]


def load_canned(canned_dir, filename: str) -> dict | None:
    path = canned_dir / filename
    if not path.exists():
        return None
    return json.loads(path.read_text())
