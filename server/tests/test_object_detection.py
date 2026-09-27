import os
from pathlib import Path

from app.config import get_settings
from app.detection import get_model


class TestObjectDetectionEndpoint:
    def test_detects_known_objects(self, demo_client, ultralytics_assets):
        photo = (ultralytics_assets / "bus.jpg").read_bytes()
        response = demo_client.post(
            "/api/detect", files={"upload": ("bus.jpg", photo, "image/jpeg")}
        )
        assert response.status_code == 200
        body = response.json()
        labels = {d["label"] for d in body["detections"]}
        assert "person" in labels
        assert "bus" in labels
        for d in body["detections"]:
            assert 0.0 <= d["confidence"] <= 1.0
            x1, y1, x2, y2 = d["bbox"]
            assert 0.0 <= x1 < x2 <= 1.0
            assert 0.0 <= y1 < y2 <= 1.0
        assert len(body["image_hash"]) == 64
        assert body["source"] == "local"

    def test_blank_image_returns_zero_detections(self, demo_client, png_bytes):
        response = demo_client.post(
            "/api/detect", files={"upload": ("blank.png", png_bytes(), "image/png")}
        )
        assert response.status_code == 200
        assert response.json()["detections"] == []

    def test_rejects_text_file(self, demo_client):
        response = demo_client.post(
            "/api/detect", files={"upload": ("note.txt", b"hello world", "text/plain")}
        )
        assert response.status_code == 400
        assert "JPEG or PNG" in response.json()["detail"]

    def test_rejects_pdf_file(self, demo_client):
        payload = b"%PDF-1.4\n" + b"x" * 256
        response = demo_client.post(
            "/api/detect", files={"upload": ("doc.pdf", payload, "application/pdf")}
        )
        assert response.status_code == 400

    def test_images_processed_in_memory_only(
        self, demo_client, ultralytics_assets, snapshot_files
    ):
        get_model(get_settings())
        before = snapshot_files()
        photo = (ultralytics_assets / "bus.jpg").read_bytes()
        response = demo_client.post(
            "/api/detect", files={"upload": ("bus.jpg", photo, "image/jpeg")}
        )
        assert response.status_code == 200
        assert snapshot_files() == before

    def test_model_weights_live_on_disk(self):
        settings = get_settings()
        get_model(settings)
        assert Path(settings.yolo_weights).exists()
