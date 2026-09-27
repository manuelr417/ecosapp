import asyncio
import dataclasses
import hashlib
import json

import app.narration as narration
from app.config import get_settings
from app.schemas import Detection


def run(coro):
    return asyncio.run(coro)


async def collect(gen):
    return [c async for c in gen]


def make_stream(chunks=None, delay=0.0, error=None, capture=None):
    async def fake_stream(provider, messages, timeout_seconds):
        if capture is not None:
            capture.append((provider, messages, timeout_seconds))
        if delay:
            await asyncio.sleep(delay)
        if error is not None:
            raise error
        for chunk in chunks or []:
            yield chunk

    return fake_stream


def detection_list():
    return [Detection(label="person", confidence=0.97, bbox=(0.1, 0.1, 0.5, 0.5))]


def seed_narrations(canned_dir, mapping: dict):
    canned_dir.mkdir(parents=True, exist_ok=True)
    (canned_dir / "narrations.json").write_text(json.dumps(mapping))


class TestNarrationLadder:
    def test_primary_rung_wins(self, monkeypatch, test_env):
        capture = []
        monkeypatch.setattr(
            narration, "stream_from_provider", make_stream(chunks=["Hi ", "there"], capture=capture)
        )
        chunks = run(collect(narration.narrate(detection_list(), "h", get_settings())))
        assert chunks == ["Hi ", "there"]
        assert len(capture) == 1
        assert capture[0][2] == get_settings().llm_timeout_seconds

    def test_falls_back_when_primary_fails(self, monkeypatch, test_env):
        behaviors = iter(
            [
                make_stream(error=RuntimeError("primary down")),
                make_stream(chunks=["fallback ", "text"]),
            ]
        )

        def fake_stream(provider, messages, timeout_seconds):
            return next(behaviors)(provider, messages, timeout_seconds)

        monkeypatch.setattr(narration, "stream_from_provider", fake_stream)
        chunks = run(collect(narration.narrate(detection_list(), "h", get_settings())))
        assert "".join(chunks) == "fallback text"

    def test_falls_back_on_slow_primary(self, monkeypatch, test_env):
        settings = dataclasses.replace(get_settings(), llm_timeout_seconds=0.05)
        behaviors = iter(
            [
                make_stream(chunks=["never"], delay=1.0),
                make_stream(chunks=["quick"]),
            ]
        )

        def fake_stream(provider, messages, timeout_seconds):
            return next(behaviors)(provider, messages, timeout_seconds)

        monkeypatch.setattr(narration, "stream_from_provider", fake_stream)
        chunks = run(collect(narration.narrate(detection_list(), "h", settings)))
        assert "".join(chunks) == "quick"

    def test_canned_served_when_all_models_down(self, test_env):
        digest = hashlib.sha256(b"sample-image").hexdigest()
        seed_narrations(
            test_env,
            {"_generic": "generic message", digest: "canned sample narration"},
        )
        chunks = run(collect(narration.narrate(detection_list(), digest, get_settings())))
        assert "".join(chunks) == "canned sample narration"

    def test_generic_canned_for_unknown_hash(self, test_env):
        seed_narrations(test_env, {"_generic": "generic message"})
        chunks = run(collect(narration.narrate([], "unknown-hash", get_settings())))
        assert "".join(chunks) == "generic message"


class TestPromptContent:
    def test_payload_is_text_only(self, monkeypatch, test_env):
        capture = []
        monkeypatch.setattr(
            narration, "stream_from_provider", make_stream(chunks=["ok"], capture=capture)
        )
        run(collect(narration.narrate(detection_list(), "h", get_settings())))
        _, messages, _ = capture[0]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        for message in messages:
            content = message["content"]
            assert isinstance(content, str)
            assert not isinstance(content, bytes)
            assert "data:image" not in content

    def test_zero_detections_message(self, test_env):
        messages = narration.build_messages([])
        assert "No familiar objects" in messages[1]["content"]

    def test_detections_summarized_in_prompt(self, test_env):
        messages = narration.build_messages(detection_list())
        assert "person" in messages[1]["content"]


class TestNarrationEndpoint:
    def test_endpoint_streams_canned_narration(self, demo_client, test_env):
        seed_narrations(test_env, {"_generic": "streamed generic message"})
        response = demo_client.post(
            "/api/narrate",
            json={"detections": [], "image_hash": "no-match"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text == "streamed generic message"
