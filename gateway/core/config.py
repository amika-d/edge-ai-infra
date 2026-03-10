"""
Application configuration settings.

Loads configuration from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from pathlib import Path


from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    """Gateway service configuration."""

    # =============================
    # Gateway settings (prefixed)
    # =============================

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # =============================
    # Application metadata
    # =============================

    APP_NAME: str = "Edge AI Gateway"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/v1"

    # =============================
    # Security
    # =============================

    API_KEYS: List[str] = Field(default_factory=list)

    # =============================
    # Resource limits
    # =============================

    MAX_TOKENS: int = 8192
    MAX_CONCURRENCY: int = 30
    REQUEST_TIMEOUT: int = 120

    # =============================
    # Infra
    # =============================

    VLLM_API_URL: str = "http://vllm:8000/v1/chat/completions"
    MODEL_ID: str = ""
    SERVED_MODEL: str = ""

    # =============================
    # RAG
    # =============================
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "default"


    
    DATA_PATH: Path = BASE_DIR / "gateway" / "data"
    MODEL_DIR: Path = BASE_DIR / "models"

    # =============================
    # Pydantic config
    # =============================

    model_config = {
        "env_file": ".env",
        
        "extra": "ignore",
    }


settings = Settings()
