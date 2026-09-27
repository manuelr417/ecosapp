import hashlib
import io

from PIL import Image
from ultralytics import YOLO

from .config import Settings, get_settings
from .schemas import Detection

JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG"

_model = None
_model_weights = None


def is_supported_image(data: bytes) -> bool:
    return data[:3] == JPEG_MAGIC or data[:4] == PNG_MAGIC


def load_image(data: bytes) -> Image.Image:
    if not is_supported_image(data):
        raise ValueError("Unsupported file: expected a JPEG or PNG image")
    try:
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:
        raise ValueError("Could not decode image") from exc


def get_model(settings: Settings | None = None):
    global _model, _model_weights
    settings = settings or get_settings()
    weights = str(settings.yolo_weights)
    if _model is None or _model_weights != weights:
        _model = YOLO(weights)
        _model_weights = weights
    return _model


def detect(data: bytes, settings: Settings | None = None) -> list[Detection]:
    settings = settings or get_settings()
    image = load_image(data)
    model = get_model(settings)
    results = model.predict(image, verbose=False)
    detections = []
    for result in results:
        names = result.names
        for box in result.boxes:
            x1, y1, x2, y2 = (float(v) for v in box.xyxyn[0].tolist())
            detections.append(
                Detection(
                    label=names[int(box.cls[0])],
                    confidence=round(float(box.conf[0]), 4),
                    bbox=(x1, y1, x2, y2),
                )
            )
    return detections


def image_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
