from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import cells, detection, narration
from .config import Settings, client_dist_dir, get_settings
from .schemas import AnalysisResponse, NarrationRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os

    if not os.getenv("SKIP_MODEL_LOAD"):
        detection.get_model(get_settings())
    yield


app = FastAPI(title="AI + Cell Manufacturing Demo", lifespan=lifespan)


async def read_upload(upload: UploadFile, settings: Settings) -> bytes:
    data = await upload.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    return data


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/detect")
async def detect_objects(upload: UploadFile) -> AnalysisResponse:
    settings = get_settings()
    data = await read_upload(upload, settings)
    try:
        detections = detection.detect(data, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AnalysisResponse(
        detections=detections, image_hash=detection.image_hash(data), source="local"
    )


@app.post("/api/cells")
async def detect_cells(
    upload: UploadFile, client: cells.RoboflowClient = Depends(cells.roboflow_client_dep)
) -> AnalysisResponse:
    settings = get_settings()
    data = await read_upload(upload, settings)
    try:
        detection.load_image(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    cached = cells.lookup_cached_annotations(settings.canned_dir, data)
    if cached is not None:
        return AnalysisResponse(
            detections=cached, image_hash=detection.image_hash(data), source="cached"
        )
    try:
        result = await client.infer(data)
    except cells.CellServiceError as exc:
        raise HTTPException(status_code=503, detail=f"Cell detection service unavailable: {exc}")
    return AnalysisResponse(
        detections=result, image_hash=detection.image_hash(data), source="live"
    )


@app.post("/api/narrate")
async def narrate_detections(
    body: NarrationRequest,
) -> StreamingResponse:
    settings = get_settings()

    async def generate() -> AsyncIterator[str]:
        async for chunk in narration.narrate(body.detections, body.image_hash, settings):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


dist = client_dist_dir()
if dist.exists():
    app.mount("/", StaticFiles(directory=dist, html=True), name="client")
else:
    @app.get("/")
    def no_client() -> dict:
        return {"hint": "client bundle not built yet; run npm run build in client/"}
