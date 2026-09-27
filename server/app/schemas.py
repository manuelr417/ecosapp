from pydantic import BaseModel, Field


class Detection(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: tuple[float, float, float, float] = Field(min_length=4, max_length=4)


class AnalysisResponse(BaseModel):
    detections: list[Detection]
    image_hash: str
    source: str = "live"


class NarrationRequest(BaseModel):
    detections: list[Detection]
    image_hash: str = ""
