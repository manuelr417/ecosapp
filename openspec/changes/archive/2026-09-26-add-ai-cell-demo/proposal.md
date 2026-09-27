# Proposal

## Why

We need a demo web app for a 50-minute outreach talk to high school students on the theme "AI and Cell Manufacturing." The talk needs a fast, visually impressive, and reliable live demonstration: the audience watches AI detect objects in photos, then sees the same technique specialized to detecting stem cell clusters in microscopy imagery. The app must survive unreliable venue networking, so reliability (rehearsed content plus layered fallbacks) is a first-class requirement, not an afterthought.

## What Changes

- Add a demo web application with a Python/FastAPI backend and a Vite + React + MUI (Material UI) single-page frontend, served from one process on the presenter's laptop over the local network.
- Add object detection (Act 1): local YOLO (COCO-pretrained) inference that draws bounding boxes over uploaded or sample photos.
- Add cell cluster detection (Act 2): hosted model inference (Roboflow) that annotates cell clusters in microscopy images, with pre-computed annotations for lab-owned rehearsal images.
- Add AI narration of detections: streaming, kid-friendly explanations of what the model saw, served through a fallback ladder (lab vLLM → secondary lab LLM endpoint → canned responses).
- Add a one-page demo UI: dark theme, hero, upload + canned sample images, canvas overlay for detections, confidence chips, streamed narration display.
- Process all images in memory only (no database, no disk persistence) to support the privacy talking point ("your photo never left this room").

## Capabilities

### New Capabilities

- `demo-web-ui`: The one-page demo frontend (MUI dark theme) that presents upload and canned sample entry points, renders detection overlays on canvas, and displays streamed AI narration. Includes LAN reachability from audience devices via a QR-code URL.
- `object-detection`: Act 1 backend capability - detecting everyday objects in audience-submitted or sample photos using a locally hosted COCO-pretrained YOLO model, returning boxes, labels, and confidence scores.
- `cell-cluster-detection`: Act 2 backend capability - detecting and annotating cell clusters in microscopy images via a hosted detection service, with pre-computed annotations for the lab-owned rehearsal images.
- `ai-narration`: Conversational narration of detection results via an LLM, with a three-rung fallback ladder (primary lab LLM endpoint, secondary lab LLM endpoint, canned responses) and streaming output.

### Modified Capabilities

(none - greenfield; no specs exist yet)

## Impact

- **New code**: `server/` (FastAPI app: detection endpoints, narration endpoint, static file serving) and `client/` (Vite + React + MUI app, built output served statically).
- **New dependencies**: Python - `fastapi`, `uvicorn`, `ultralytics`, `openai`, `httpx`, `python-multipart`. Node (dev-time only) - Vite, React, MUI, Emotion. Narration uses the lab-hosted LLM endpoint (vLLM GLM-5.3) with an OpenAI ChatGPT fallback (`OPENAI_API_KEY` from the environment) and canned responses as the final rung; no models are downloaded or run on the presenter laptop.
- **External services**: lab vLLM endpoint (`136.145.77.22:8000/v1`, campus network) and Roboflow hosted inference (internet, free API key). Both have offline fallbacks.
- **No database, no auth, no Docker**: LAN-only, ephemeral, single-process demo.
- **Operational prep**: pre-downloaded model weights, pre-built client bundle, pre-cached narrations and annotations for rehearsal images, QR code slide.
