"""Application configuration.

All secrets live in environment variables / .env file.
External services (DeepSeek / PaddleOCR) degrade gracefully to a local
"mock" mode when credentials are absent so the MVP runs out of the box.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# All writable paths can be overridden via env vars. This matters on read-only
# serverless filesystems (e.g. Aliyun FC) where the code directory is read-only
# and data must live under /tmp. Defaults keep local/Docker behaviour unchanged.
DATA_DIR = Path(os.getenv("RECALL_DATA_DIR", str(BASE_DIR / "data")))
UPLOAD_DIR = Path(os.getenv("RECALL_UPLOAD_DIR", str(BASE_DIR / "uploads")))
CHROMA_DIR = Path(os.getenv("RECALL_CHROMA_DIR", str(DATA_DIR / "chroma")))
DB_PATH = Path(os.getenv("RECALL_DB_PATH", str(DATA_DIR / "recall.db")))

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)


class Settings:
    # --- Paths ---
    base_dir: Path = BASE_DIR
    data_dir: Path = DATA_DIR
    upload_dir: Path = UPLOAD_DIR
    chroma_dir: Path = CHROMA_DIR
    database_url: str = f"sqlite:///{DB_PATH}"

    # --- External services ---
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv(
        "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
    )
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # When true (or when no API key) OCR/AI fall back to deterministic local mocks.
    mock_external: bool = os.getenv("MOCK_EXTERNAL", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    # --- Limits (from PRD / UI spec) ---
    max_upload_size: int = 10 * 1024 * 1024  # 10 MB
    allowed_image_types: tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")
    max_text_length: int = 10000

    # CORS — allow the Vite dev server during development.
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Embedding dimension used by the vector store.
    embedding_dim: int = 1024


settings = Settings()
