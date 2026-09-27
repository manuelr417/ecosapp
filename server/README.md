# Talk-Day Runbook — AI + Cell Manufacturing Demo

Everything on this page happens BEFORE the 50-minute talk. On the day, the only
command is the boot command below.

## One-time setup (on your desk)

```bash
cd server
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
mkdir -p models
./.venv/bin/python -c "from app.detection import get_model; from app.config import get_settings; get_model(get_settings())"
cd ../client
npm install
npm run build
```

The last server command downloads `yolo11n.pt` into `server/models/` — after this,
Act 1 needs no internet at all.

## Boot command (talk day)

```bash
cd server && ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000` on the projector laptop. Audience devices use
the QR code (next section).

## QR code slide

- Print the laptop's LAN address on the slide, e.g. `http://192.168.68.113:8000`
  (find it with `ipconfig getifaddr en0`).
- Generate the QR code the morning of the talk (any generator), pointing at that URL.
- The address changes with the network — regenerate the QR after connecting to the venue WiFi.

## Pre-flight checklist (in the actual room)

1. **Endpoint checks** (from the venue network):
   ```bash
   curl -m 5 http://136.145.77.22:8000/v1/models   # rung 1: vLLM GLM-5.3
   echo $OPENAI_API_KEY | wc -c                    # rung 2: OpenAI (nonzero = set)
   ```
   If the lab node is down, narration automatically uses ChatGPT, then canned text.
2. **Audience device test**: connect one phone to the venue WiFi and open the
   LAN URL. If it does not load, the network has AP isolation — switch the laptop
   and phones to your phone hotspot (see fallback below).
3. **Offline rehearsal**: with WiFi off on the laptop, run both acts on canned
   samples. Act 1 detection runs locally; Act 2 samples return pre-computed
   annotations; narrations come from `server/canned/narrations.json`.

## Hotspot fallback procedure (AP isolation or dead venue WiFi)

1. Enable the phone hotspot; connect the laptop and audience phones to it.
2. Boot command stays the same. Lab LLM nodes become unreachable — narration
   falls back to canned text automatically (by design).
3. Act 1 stays fully live (local YOLO). Act 2 works for rehearsal images
   (cached); live cell uploads need internet, so skip live Act 2 uploads.

## Act 2 model choice + caching (when you have your lab images)

**Status**: Roboflow key verified; hosted inference live. Default model is
provisionally set to `mouse-stem-cells/1` (Roboflow Universe, "mouse stem cells"
by testinglabeling, mAP 98.95 / precision 96.68). Universe candidates probed
live on proxy images (public blood-smear crops - inconclusive, all weak):

| Model (Universe) | Endpoint id | mAP | Proxy result |
| --- | --- | --- | --- |
| mouse stem cells (testinglabeling) | `mouse-stem-cells/1` | 98.95 | 3/3 conf 1.0 on synthetic blobs, 0 on smears |
| carlostumo cells-in-culture | `carlostumo/cell-detection-5hlob/1` (serverless URL) | 74.97 | 0-1 weak |
| Konsultera cell counting | `konsultera/cell-detection-yjhjp/2` (serverless URL) | 96.96 | 0-1 weak |
| Benam Lab (incl. `bubble` class) | `benam-lab/cell-detection-qppjv/1` (serverless URL) | 61.21 | 1 `bubble` ~0.5 |

`ROBOFLOW_MODEL` accepts a bare id (`mouse-stem-cells/1`) or a full URL
(`https://serverless.roboflow.com/<slug>/<version>`) for models that only live
on the serverless host. Final pick MUST be validated on your real lab images.

1. Drop your 1-2 lab microscopy images into `client/public/samples/act2/`
   (JPG, replacing the placeholders).
2. Evaluate the default model on them (and 1-2 alternatives from Universe by
   changing `ROBOFLOW_MODEL`), then cache:
   ```bash
   cd server
   export ROBOFLOW_API_KEY=...            # your private key
   export ROBOFLOW_MODEL=mouse-stem-cells/1
   ./.venv/bin/python tools/cache_samples.py --with-narrations
   ```
   This regenerates `canned/annotations.json`, `canned/narrations.json`, and the
   client sample manifest, and rebuild is NOT needed (samples are served
   statically from `client/public`).
3. Rebuild the client only if you added/renamed sample files:
   `cd client && npm run build`.

## Hotspot fallback procedure (AP isolation or dead venue WiFi)

1. Enable the phone hotspot; connect the laptop and audience phones to it.
2. Boot command stays the same. The lab LLM node becomes unreachable — narration
   automatically runs on the OpenAI ChatGPT rung (needs only the hotspot's
   internet; the key comes from the environment).
3. Act 1 stays fully live (local YOLO). Act 2 works for rehearsal images
   (cached); live cell uploads also work as long as the hotspot has internet.

## Measured performance (this laptop, Apple Silicon, CPU)

| Check | Result |
| --- | --- |
| Single detection latency (warm) | ~0.035 s average (trimmed), well under the 5 s bound |
| Detection with network blocked | works (weights are local) |
| 10 concurrent uploads | all HTTP 200 in 1.3 s wall time |
| vLLM GLM-5.3 first token (thinking off) | ~1.3 s |

## Known limits (by design)

- No database, no auth: images live in memory only and never touch disk.
- Live Act 2 uploads require internet (Roboflow hosted model).
- Venue WiFi AP isolation breaks audience access — use the hotspot fallback.
- Narration sends only detection text to LLM providers, never the image.
