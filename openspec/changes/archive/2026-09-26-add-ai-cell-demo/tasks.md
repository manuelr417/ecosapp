# Tasks

## 1. Scaffold and Dependencies

- [x] 1.1 Create `server/` structure (`app` module with entry point), add `requirements.txt` (fastapi, uvicorn, ultralytics, openai, httpx, python-multipart), install into a virtualenv, and verify `pip check` passes
- [x] 1.2 Scaffold `client/` with Vite + React, add MUI (`@mui/material`, `@emotion/react`, `@emotion/styled`, `@mui/icons-material`), and verify `npm install` and `npm run build` succeed
- [x] 1.3 Wire FastAPI to serve the built client bundle as static files and verify a browser request to `http://localhost:8000` returns the app page

## 2. Object Detection Backend (Act 1)

- [x] 2.1 Add the local COCO-pretrained YOLO model loader (weights pre-downloaded to disk, loaded once at startup) and verify detection runs with network disabled
- [x] 2.2 Implement the detection endpoint returning label, confidence, and region per object; verify with a test photo containing known objects (e.g. person, cup) via pytest and a curl smoke test
- [x] 2.3 Verify empty-detection images return a successful zero-detection result (pytest with a blank/sky photo)
- [x] 2.4 Verify non-image uploads are rejected with a clear error (pytest submitting text and PDF payloads)
- [x] 2.5 Verify images are processed in memory only: submit an image and assert no new files appear on disk (pytest with tmpdir snapshot)
- [x] 2.6 Measure single-image detection latency on the demo laptop and confirm it is under 5 seconds; record the measured value in the runbook

## 3. Cell Cluster Detection Backend (Act 2)

- [ ] 3.1 Add Roboflow hosted-inference client with the API key from config, evaluate 2–3 candidate cell models against the lab's own microscopy images, and record the selected model in the runbook (verification: side-by-side annotated outputs reviewed)
- [x] 3.2 Implement the cell-detection endpoint returning cluster regions; verify with a microscopy image via pytest and curl while the hosted service is reachable
- [x] 3.3 Implement pre-computed annotations for the designated lab rehearsal images (generate and store annotations at build time, serve them in place of live inference); verify offline fallback via pytest with the hosted client unreachable
- [x] 3.4 Verify a non-sample image submitted while offline returns an explicit service-unavailable error, and that hosted-service errors surface as failures rather than empty results (pytest with a stubbed failing client)
- [x] 3.5 Verify microscopy images are processed in memory only (pytest with tmpdir snapshot, mirroring 2.5)

## 4. AI Narration Backend

- [x] 4.1 Implement an OpenAI-compatible chat client factory with configurable base URL/model (env-driven) and verify it reaches the lab vLLM endpoint and streams a completion (manual smoke test on campus network)
- [x] 4.2 Implement the narration endpoint: takes detection results, builds the kid-friendly prompt (short, simple language, handles zero detections), streams text chunks; verify with pytest against a stubbed client for both populated and empty detections
- [ ] 4.3 Implement the fallback ladder (primary lab LLM → OpenAI ChatGPT → canned) with a bounded per-rung first-token timeout; verify each rung via pytest with stubbed failing/slow clients, and verify the real OpenAI fallback streams narration with the primary endpoint unreachable
- [x] 4.4 Add canned narrations for the designated rehearsal images plus a generic offline message; verify canned serving when both model rungs are down (pytest)
- [x] 4.5 Verify narration requests contain detection text only and no image bytes (pytest asserting the request payload captured by the stubbed client)

## 5. Demo Frontend

- [ ] 5.1 Build the single-page layout (AppBar, hero, image panel, results panel) with the MUI dark theme and verify it renders correctly at projector resolution in the browser
- [ ] 5.2 Add image submission: file upload and canned sample thumbnails (bundle sample images in `client/public/samples/`); verify both paths load an image into the result panel and trigger analysis
- [ ] 5.3 Add the canvas overlay component drawing bounding boxes (Act 1) and cluster outlines (Act 2) aligned over the displayed image; verify visually with real and canned detections at multiple window sizes
- [ ] 5.4 Add the detection list with label + confidence chips and the in-progress indicator; verify states during a real analysis round-trip
- [ ] 5.5 Add progressive narration display consuming the streaming endpoint; verify text appears incrementally against the running backend
- [ ] 5.6 Add client-side image downscale to ~640 px before upload and error banners for rejected files and service-unavailable responses; verify with an oversized phone photo and a non-image file

## 6. Integration and Demo Readiness

- [ ] 6.1 Bind the server to `0.0.0.0`, document the laptop's LAN-address workflow, and verify an audience device on the same network loads and uses the full demo end to end
- [ ] 6.2 Run a concurrency smoke test (≥10 near-simultaneous uploads from separate devices/tabs) and confirm all requests complete with the in-progress state shown; record observed queueing in the runbook
- [x] 6.3 Write the talk-day runbook (`server/README.md` or `docs/`): prep steps (weights, endpoint checks, build, caching, model choice), boot command, QR-code slide note, hotspot fallback procedure, and measured latencies
- [ ] 6.4 Full rehearsal: run both acts completely offline (ladder rungs 2–3, cached Act 2 annotations) and on campus network (rung 1), confirming every canned sample plays its pre-computed path; fix and re-run anything that fails
