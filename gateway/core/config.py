"""
Application configuration settings.

Loads configuration from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Gateway service configuration."""
    
    # Application metadata
    APP_NAME: str = "Edge AI Gateway"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/v1"
    DEBUG: bool = False

    # Security settings
    API_KEYS: List[str] = Field(default_factory=list, description="List of valid API keys")

    # Resource limits
    MAX_TOKENS: int = Field(8192, description="Maximum tokens allowed per request")
    MAX_CONCURRENCY: int = Field(30, description="Maximum concurrent requests")
    REQUEST_TIMEOUT: int = Field(120, description="Request timeout in seconds")

    # Infra
    VLLM_API_URL: str = "http://vllm:8000/v1/chat/completions"
    MODEL_ID: str = "llama-3b"      
    SERVED_MODEL: str = "llama-3b"  # This should match the model name used in the vLLM server config

    model_config = {
        "extra": "ignore"
    }


settings = Settings()
