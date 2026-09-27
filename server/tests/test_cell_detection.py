import hashlib
import json

import app.cells as cells
from app.main import app
from app.schemas import Detection


class FakeNeverCalled:
    async def infer(self, data):
        raise AssertionError("hosted client must not be called for cached images")


class FakeLive:
    async def infer(self, data):
        return [
            Detection(label="cell cluster", confidence=0.91, bbox=(0.1, 0.1, 0.4, 0.4)),
            Detection(label="cell cluster", confidence=0.87, bbox=(0.5, 0.5, 0.9, 0.9)),
        ]


class FailingClient:
    async def infer(self, data):
        raise cells.CellServiceError("service down")


def override(client_instance):
    app.dependency_overrides[cells.roboflow_client_dep] = lambda: client_instance


def teardown_function():
    app.dependency_overrides.pop(cells.roboflow_client_dep, None)


def seed_annotations(canned_dir, data: bytes, detections: list[dict]) -> str:
    canned_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()
    (canned_dir / "annotations.json").write_text(
        json.dumps({digest: {"detections": detections}})
    )
    return digest


class TestCellDetectionEndpoint:
    def test_cached_annotation_served_without_hosted_call(
        self, demo_client, test_env, png_bytes
    ):
        data = png_bytes()
        digest = seed_annotations(
            test_env,
            data,
            [{"label": "cell cluster", "confidence": 0.9, "bbox": [0.1, 0.1, 0.4, 0.4]}],
        )
        override(FakeNeverCalled())
        response = demo_client.post(
            "/api/cells", files={"upload": ("cells.png", data, "image/png")}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "cached"
        assert body["image_hash"] == digest
        assert len(body["detections"]) == 1

    def test_live_inference_when_not_cached(self, demo_client, test_env, png_bytes):
        override(FakeLive())
        data = png_bytes(color=(10, 10, 10))
        response = demo_client.post(
            "/api/cells", files={"upload": ("cells.png", data, "image/png")}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "live"
        assert len(body["detections"]) == 2

    def test_offline_non_sample_image_returns_503(
        self, demo_client, test_env, png_bytes
    ):
        override(FailingClient())
        data = png_bytes(color=(20, 20, 20))
        response = demo_client.post(
            "/api/cells", files={"upload": ("cells.png", data, "image/png")}
        )
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

    def test_hosted_error_surfaces_as_failure_not_empty(
        self, demo_client, test_env, png_bytes
    ):
        override(FailingClient())
        data = png_bytes(color=(30, 30, 30))
        response = demo_client.post(
            "/api/cells", files={"upload": ("cells.png", data, "image/png")}
        )
        assert response.status_code == 503
        assert response.json()["detail"]

    def test_missing_config_is_service_unavailable(
        self, demo_client, test_env, png_bytes
    ):
        override(cells.RoboflowClient("", ""))
        data = png_bytes(color=(40, 40, 40))
        response = demo_client.post(
            "/api/cells", files={"upload": ("cells.png", data, "image/png")}
        )
        assert response.status_code == 503

    def test_rejects_non_image(self, demo_client, test_env):
        override(FakeNeverCalled())
        response = demo_client.post(
            "/api/cells", files={"upload": ("note.txt", b"not an image", "text/plain")}
        )
        assert response.status_code == 400

    def test_microscopy_images_processed_in_memory_only(
        self, demo_client, test_env, png_bytes, snapshot_files
    ):
        before = snapshot_files()
        override(FakeLive())
        response = demo_client.post(
            "/api/cells",
            files={"upload": ("cells.png", png_bytes(color=(50, 50, 50)), "image/png")},
        )
        assert response.status_code == 200
        assert snapshot_files() == before
