import io
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def test_env(tmp_path_factory):
    canned = tmp_path_factory.mktemp("canned")
    keys = (
        "CANNED_DIR",
        "LLM_PRIMARY_BASE_URL",
        "LLM_FALLBACK_BASE_URL",
        "LLM_PRIMARY_MODEL",
        "LLM_FALLBACK_MODEL",
        "LLM_TIMEOUT_SECONDS",
        "SKIP_MODEL_LOAD",
        "YOLO_WEIGHTS",
        "ROBOFLOW_API_KEY",
        "ROBOFLOW_MODEL",
    )
    saved = {k: os.environ.get(k) for k in keys}
    os.environ["CANNED_DIR"] = str(canned)
    os.environ["LLM_PRIMARY_BASE_URL"] = "http://127.0.0.1:9/v1"
    os.environ["LLM_FALLBACK_BASE_URL"] = "http://127.0.0.1:9/v1"
    os.environ["LLM_TIMEOUT_SECONDS"] = "0.2"
    os.environ.pop("SKIP_MODEL_LOAD", None)
    os.environ.pop("YOLO_WEIGHTS", None)
    os.environ.pop("ROBOFLOW_API_KEY", None)
    os.environ.pop("ROBOFLOW_MODEL", None)
    yield canned
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture(scope="session")
def demo_client(test_env):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def png_bytes():
    def make(size=(64, 64), color=(255, 255, 255)):
        from PIL import Image

        buffer = io.BytesIO()
        Image.new("RGB", size, color).save(buffer, format="PNG")
        return buffer.getvalue()

    return make


@pytest.fixture
def snapshot_files():
    def snapshot() -> set[str]:
        from app.config import PROJECT_DIR

        skip = {".venv", "__pycache__", ".pytest_cache", "node_modules", ".git", "dist"}
        found = set()
        for base, dirs, files in os.walk(PROJECT_DIR):
            dirs[:] = [d for d in dirs if d not in skip]
            for name in files:
                found.add(str(Path(base, name).relative_to(PROJECT_DIR)))
        return found

    return snapshot


@pytest.fixture
def ultralytics_assets():
    import ultralytics

    return Path(ultralytics.__file__).parent / "assets"
