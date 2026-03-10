"""
services/vllm_client.py

Handles all communication with the vLLM backend API.
Uses plain Python exceptions — safe to call from both CLI and FastAPI routes.
"""
import aiohttp
import asyncio
import logging
from gateway.core.config import settings

logger = logging.getLogger("edge-gateway")


class ModelEngineError(Exception):
    """vLLM returned a non-200 response."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail      = detail
        super().__init__(f"[{status_code}] {detail}")


class ModelEngineTimeout(Exception):
    """vLLM did not respond in time."""


class ModelEngineUnavailable(Exception):
    """Cannot connect to vLLM."""


async def send_chat_request(payload: dict) -> dict:
    """
    Send a chat completion request to vLLM.

    Raises:
        ModelEngineError       — vLLM returned 4xx/5xx
        ModelEngineTimeout     — request timed out
        ModelEngineUnavailable — cannot connect
    """
    try:
        timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(settings.VLLM_API_URL, json=payload) as response:
                logger.info(f"vLLM response status: {response.status}")

                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"vLLM API error [{response.status}]: {error_text}")
                    raise ModelEngineError(response.status, error_text)

                return await response.json()

    except asyncio.TimeoutError:
        logger.error(f"vLLM timed out after {settings.REQUEST_TIMEOUT}s")
        raise ModelEngineTimeout("Model request timed out")

    except aiohttp.ClientConnectorError as e:
        logger.error(f"Cannot connect to vLLM: {e}")
        raise ModelEngineUnavailable(f"Cannot connect to Model Engine: {e}")

    except (ModelEngineError, ModelEngineTimeout, ModelEngineUnavailable):
        raise

    except Exception as e:
        logger.exception("Unexpected error communicating with vLLM")
        raise ModelEngineError(500, str(e))