"""
Edge AI Gateway - Main application entry point.

Provides a FastAPI gateway for chat completion requests to the vLLM backend.
"""

from fastapi import FastAPI
from gateway.auth.routes import router as auth_router
from gateway.core.config import settings
import uvicorn

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Gateway service for edge AI model inference"
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Register API routes
app.include_router(auth_router, prefix=settings.API_PREFIX)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
