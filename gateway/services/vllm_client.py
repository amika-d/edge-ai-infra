"""
vLLM client service.

Handles all communication with the vLLM backend API, including request
forwarding, error handling, and timeout management.
"""

import aiohttp
import asyncio
import logging
from gateway.core.config import settings
from fastapi import HTTPException

# Configure module logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edge-gateway")


async def send_chat_request(payload: dict) -> dict:
    """
    Send a chat completion request to the vLLM backend.
    
    Handles HTTP communication, error handling, timeouts, and connection failures.
    
    Args:
        payload: Request payload containing model, messages, and generation parameters
        
    Returns:
        dict: Parsed JSON response from vLLM backend with completion data
        
    Raises:
        HTTPException: For timeout (504), connection failure (503), or server errors (500)
    """
    try:
        timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(settings.VLLM_API_URL, json=payload) as response:
                logger.info(f"vLLM response status: {response.status}")
                
                # Handle non-200 responses
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"vLLM API error [{response.status}]: {error_text}")
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Model Engine Error: {error_text}"
                    )
                
                return await response.json()
            
    except asyncio.TimeoutError:
        logger.error("Request to vLLM backend timed out after %d seconds", settings.REQUEST_TIMEOUT)
        raise HTTPException(
            status_code=504,
            detail="Model request timed out"
        )

    except aiohttp.ClientConnectorError as e:
        logger.error(f"Connection to vLLM backend failed: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Cannot connect to Model Engine. Is it running? ({str(e)})"
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        logger.exception("Unexpected error while communicating with vLLM")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
