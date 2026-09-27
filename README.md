# ecosapp — AI + Cell Manufacturing Demo

A demo web app for a 50-minute high-school outreach talk on **AI and Cell
Manufacturing**. The audience watches AI *see*: first finding everyday objects
in photos, then finding stem-cell clusters in microscopy images — the same
technique, specialized to a new domain.

Built to survive a live demo: everything important can run without internet,
and every external dependency has a fallback.

## The two acts

| Act | What happens | Where it runs |
| --- | --- | --- |
| **1 — Everyday objects** | Upload or pick a photo; YOLO draws boxes around what it recognizes; an LLM explains it in plain language | Fully local (YOLO weights on the laptop) |
| **2 — Cell clusters** | Same pipeline with a microscopy image; cluster outlines drawn over the image | Hosted model (Roboflow), with pre-computed annotations for rehearsal images so it works offline |

The "AI says…" narration streams from the **lab LLM (GLM-5.3 on vLLM)**, with a
fallback ladder: lab vLLM → OpenAI ChatGPT (`OPENAI_API_KEY`) → canned text.
Submitted images are processed **in memory only** — nothing is written to disk,
and only detection text (never the image) is sent to any LLM.

## Architecture

```
  audience phones / projector
        |  QR -> http://<laptop-ip>:8000
        v
+---------------------------------------------------------------+
| FastAPI (one process, laptop, 0.0.0.0:8000)                   |
|   POST /api/detect    local YOLO (COCO, offline)              |
|   POST /api/cells     Roboflow hosted + cached annotations    |
|   POST /api/narrate   LLM ladder (vLLM -> OpenAI -> canned)   |
|   serves client/dist statically                                       |
+---------------------------------------------------------------+
         ^                                          ^
         |                                          |
  client/ (Vite + React + MUI,              lab GPU node 136.145.77.22
  dark theme, canvas overlays)              (vLLM, GLM-5.3 FP16)
```

## Running it

Prerequisites: Python 3.12+, Node 18+, internet once for setup.

```bash
# 1. Server deps + local YOLO weights (downloads yolo11n.pt once)
cd server
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -c "from app.detection import get_model; from app.config import get_settings; get_model(get_settings())"

# 2. Client build
cd ../client
npm install
npm run build

# 3. Boot (from server/)
cd ../server
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000** (or `http://<laptop-ip>:8000` from another
device on the same network).

### Environment variables (all optional)

| Variable | Default | Purpose |
| --- | --- | --- |
| `ROBOFLOW_API_KEY` | — | Enables live Act 2 hosted detection |
| `ROBOFLOW_MODEL` | `mouse-stem-cells/1` | Cell model id or full serverless URL |
| `LLM_PRIMARY_BASE_URL` | `http://136.145.77.22:8000/v1` | Lab vLLM (GLM-5.3) |
| `LLM_FALLBACK_BASE_URL` / `LLM_FALLBACK_MODEL` | `https://api.openai.com/v1` / `gpt-4o-mini` | ChatGPT fallback rung |
| `OPENAI_API_KEY` | — | Key for the fallback rung (read from env) |

Act 1 and the narration fallback ladder work with **zero** configuration.

## Tests

```bash
cd server && ./.venv/bin/pytest tests/ -q
```

## Talk-day runbook

Prep checklist, QR-code slide, offline rehearsal, hotspot fallback, and
measured latencies: **[server/README.md](server/README.md)**.

## Project layout

```
server/          FastAPI app, tests, canned demo data, prep tools
client/          Vite + React + MUI single-page demo UI
openspec/        OpenSpec specs (behavior contract) + archived change history
```
