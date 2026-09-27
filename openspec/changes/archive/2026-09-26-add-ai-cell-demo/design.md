# Design

## Context

Greenfield scaffold: `client/` and `server/` are empty placeholders; no stack was chosen before this change. The demo context and motivation are in [proposal.md](proposal.md); the behavioral contracts are in the four spec deltas under `specs/`. Key constraints that shape the design: the app runs on one presenter laptop during a 50-minute talk, the venue network is usable but not trustworthy, the lab LLM node (`136.145.77.22:8000/v1`) is reachable on the campus network, and the audience interacts live after a presenter-led first pass.

## Goals / Non-Goals

**Goals:**

- One process, one laptop: the whole demo boots with a single server command on talk day.
- Rehearsed core, live edges: the scripted moments (canned samples, Act 2 lab images, their narrations) are pre-computed and cannot fail; live uploads are the disposable part.
- Layered fallbacks for every external dependency (LLM ladder, Act 2 cached annotations).
- Visual payoff suitable for projection: dark theme, overlays drawn on the image, streaming text.

**Non-Goals:**

- No persistence, user accounts, or deployment beyond the laptop (no DB, no Docker, no auth).
- No production hardening, rate limiting, or input sanitization beyond format checks.
- No training of custom models; Act 2 uses a hosted pretrained model.
- No mobile app or PWA; the audience uses their phone browsers.

## Decisions

### D1. Backend: Python + FastAPI
YOLO inference is Python-native (Ultralytics), and FastAPI gives async endpoints plus streaming responses for narration with minimal ceremony.
*Alternatives:* Node/Express (would require shelling out to Python or ONNX runtime bindings for detection); Flask (fine, weaker streaming ergonomics).

### D2. Act 1 model: Ultralytics YOLO11n, COCO-pretrained, local CPU
~100–300 ms per image on CPU; a single local `.pt` file; fully offline. `n`-size is deliberate: demo pacing beats marginal accuracy.
*Alternatives:* in-browser ONNX (flashier "AI in your browser" story, but conversion friction and another failure surface); larger YOLO sizes (slower, no demo benefit).

### D3. Act 2: Roboflow hosted inference
Outsourcing was chosen over training: free API key, no training pipeline to maintain, several pretrained cell/microscopy models exist on Roboflow Universe to evaluate. Pre-computed annotations for the designated lab rehearsal images cover the offline case (spec: `cell-cluster-detection`).
*Alternatives:* fine-tune a tiny YOLO on a Roboflow Universe dataset (offline-capable live inference, but a training detour this project deliberately skips); Cellpose (true segmentation, heavier setup).

### D4. Narration fallback ladder: lab vLLM → OpenAI (ChatGPT) → canned
All OpenAI-compatible endpoints, so the backend uses one chat-completions client with a swappable base URL. Rungs: (1) lab vLLM GLM-5.3 (`136.145.77.22`, the model configured in `opencode.jsonc`); (2) OpenAI ChatGPT (`gpt-4o-mini`, key from the environment's `OPENAI_API_KEY`) — a fully independent provider and network path, so narration stays live even when the lab is unreachable (e.g. presenter on a phone hotspot); (3) canned narrations for rehearsal images, generic pre-written message otherwise. Per-rung first-token timeout is bounded (a few seconds) with automatic failover on error/timeout. GLM-5.3 is a reasoning model: the local rung disables thinking (`chat_template_kwargs.thinking=false`) and uses a generation budget (200 tokens) large enough that reasoning cannot starve the visible narration. Only detection text (labels/confidences) ever leaves for the cloud — never the image (spec: `ai-narration`).
*Alternatives:* lab SGLang node as rung 2 (same-network dependency, weak insurance; replaced by user decision); local Ollama on the laptop (rejected — no model downloads on the presenter laptop); cache-only (safe but loses the "live AI" feel).

### D5. Frontend: Vite + React + MUI, dark theme, single page
MUI's marketing-page aesthetic (hero, cards, chips, dark palette) fits a projected demo better than a hand-rolled plain page. The `npm run build` output is static files served by FastAPI, so the build step is a dev-time cost only — talk day runs the same single command as a no-build stack would.
*Alternatives:* vanilla JS + CSS (zero toolchain, but visibly plain for the audience); Tailwind (polish requires hand-building every component).

### D6. Detection overlays: raw HTML5 canvas inside the React app
MUI does not draw boxes; a `<canvas>` absolutely positioned over the displayed image handles both bounding boxes (Act 1) and cluster outlines (Act 2). No charting/annotation library.

### D7. Ephemeral processing: in memory only
Images are processed in memory and never written to disk (spec requirement in both detection capabilities). This is both the privacy talking point and a simplification.
*Alternatives:* temp files (simpler debugging; rejected — privacy claim must be literally true).

### D8. Upload path: client-side downscale to ~640 px
Phone photos are multi-MB; the browser resizes via canvas before upload, making uploads instant and CPU inference faster under a classroom-sized burst (~25 near-simultaneous requests).
*Alternatives:* server-side resize (uploads stay slow on venue WiFi).

### D9. Reachability: bind 0.0.0.0, QR code on a slide
Audience devices open `http://<laptop-ip>:8000` via a QR code. No auth — LAN-only, ephemeral.
*Alternatives:* tunnel service (external dependency, rejected).

## Risks / Trade-offs

- [Venue WiFi has AP isolation; audience devices cannot reach the laptop] → Test with one audience device in the actual room beforehand; if isolated, switch to the presenter's phone hotspot (narration then runs on the OpenAI rung, which needs only the hotspot's internet — D4 exists so this scenario still works end to end).
- [Lab vLLM node unreachable from the venue] → LLM ladder rung 2; verify reachability from the room during rehearsal.
- [First-run model weight downloads hang on stage] → Pre-download YOLO weights and run the Roboflow caching step before talk day; no other model downloads exist (narration uses lab endpoints only).
- [Roboflow free-tier rate limits under a classroom burst] → Act 2 live uploads are the "live edge" (acceptable loss); rehearsal images are cached.
- [A lab LLM node goes down mid-talk] → Rung 2 targets a different host and serving stack (vLLM vs SGLang); short narrations (bounded token budget) and client-side downscale keep queueing brief; visible in-progress state (spec: `demo-web-ui`) makes waits feel intentional; canned rung always answers.
- [Audience uploads inappropriate/embarrassing photos] → In-memory processing (D7), presenter controls the projector; nothing persists.
- [CO CO classes miss unfamiliar objects in Act 1] → Intentional: "YOLO only knows what we taught it" is the bridge to Act 2.

## Migration Plan

Initial build, no migration. Talk-day runbook (all steps before the talk):

1. `pip install` server requirements; pre-download YOLO11n weights (offline-safe).
2. Verify both lab LLM endpoints answer from the venue network (rung 1 and rung 2).
3. Configure the Roboflow API key; evaluate 2–3 candidate cell models against the lab images; pre-compute and cache their annotations and narrations.
4. `npm run build` the client; confirm FastAPI serves the bundle.
5. Rehearse both acts fully offline (ladder rungs 2–3) and on campus network (rung 1).
6. QR-code slide pointing at the laptop's LAN address; connectivity test with one audience device in the room.

Rollback is trivial: the previous state is an empty scaffold.

## Open Questions

- Which Roboflow Universe cell-detection model performs best on the lab's own images (evaluate 2–3 candidates during prep; does not affect specs or task structure).
- Narration prompt tuning for tone/length — resolved during rehearsal, not a design blocker.
