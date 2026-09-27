import os
from dataclasses import dataclass
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = SERVER_DIR.parent


@dataclass(frozen=True)
class Settings:
    yolo_weights: Path
    roboflow_api_key: str
    roboflow_model: str
    llm_primary_base_url: str
    llm_primary_model: str
    llm_fallback_base_url: str
    llm_fallback_model: str
    llm_fallback_api_key: str
    llm_timeout_seconds: float
    canned_dir: Path
    max_upload_bytes: int


def get_settings() -> Settings:
    return Settings(
        yolo_weights=Path(
            os.getenv("YOLO_WEIGHTS") or SERVER_DIR / "models" / "yolo11n.pt"
        ),
        roboflow_api_key=os.getenv("ROBOFLOW_API_KEY", ""),
        roboflow_model=os.getenv("ROBOFLOW_MODEL", "mouse-stem-cells/1"),
        llm_primary_base_url=os.getenv(
            "LLM_PRIMARY_BASE_URL", "http://136.145.77.22:8000/v1"
        ),
        llm_primary_model=os.getenv("LLM_PRIMARY_MODEL", "glm-5.3-flash"),
        llm_fallback_base_url=os.getenv(
            "LLM_FALLBACK_BASE_URL", "https://api.openai.com/v1"
        ),
        llm_fallback_model=os.getenv("LLM_FALLBACK_MODEL", "gpt-4o-mini"),
        llm_fallback_api_key=os.getenv("LLM_FALLBACK_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "3")),
        canned_dir=Path(os.getenv("CANNED_DIR") or SERVER_DIR / "canned"),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
    )


def client_dist_dir() -> Path:
    return PROJECT_DIR / "client" / "dist"
