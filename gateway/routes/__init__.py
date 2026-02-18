"""
Gateway API routes package.

Organizes all API endpoints for the edge AI gateway.
"""

from gateway.routes.chat import router as chat_router
from gateway.routes.metrics import router as metrics_router

__all__ = ["chat_router", "metrics_router"]
