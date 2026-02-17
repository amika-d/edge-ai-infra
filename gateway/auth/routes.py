"""
Gateway authentication and chat completion routes.

This module handles incoming chat completion requests, forwards them to the vLLM backend,
and returns formatted responses to the client.
"""

import time
import uuid
import logging
import aiohttp
import asyncio
from fastapi import APIRouter, HTTPException
from gateway.auth.schemas import ChatRequest, ChatResponse, ChatChoice, ChatMessage, ChatUsage
from gateway.core.config import settings

# Configure module logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edge-gateway")

router = APIRouter()


@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """
    Handle chat completion requests.
    
    Validates incoming requests, forwards them to the vLLM backend,
    and returns formatted responses with usage statistics.
    
    Args:
        request: ChatRequest object containing messages, model config, and parameters
        
    Returns:
        ChatResponse: Formatted response with completion, usage stats, and metadata
        
    Raises:
        HTTPException: For validation errors, backend errors, or timeouts
    """
    # Validate token limit
    if request.max_tokens > settings.MAX_TOKENS:
        raise HTTPException(
            status_code=400, 
            detail=f"max_tokens exceeds allowed limit ({settings.MAX_TOKENS})"
        )

    # Prepare request payload for vLLM backend
    payload = {
        "model": settings.SERVED_MODEL,
        "messages": [m.model_dump(mode='json') for m in request.messages],
        "max_tokens": request.max_tokens,
        "temperature": request.temperature if request.temperature is not None else 0.7,
        "stream": False
    }

    start_time = time.time()
    
    # Log request details
    logger.info(f"Sending request to vLLM backend: {settings.VLLM_API_URL}")
    logger.info(f"Payload: {payload}")

    try:
        # Configure HTTP client timeout
        timeout = aiohttp.ClientTimeout(total=120)
        
        # Send request to vLLM backend
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(settings.VLLM_API_URL, json=payload) as response:
                
                logger.info(f"Response status: {response.status}")
                
                # Handle non-200 responses
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"vLLM backend error [{response.status}]: {error_text}")
                    raise HTTPException(
                        status_code=response.status, 
                        detail=f"Model Engine Error: {error_text}"
                    )

                data = await response.json()

    except asyncio.TimeoutError:
        logger.error("Request to vLLM backend timed out")
        raise HTTPException(status_code=504, detail="Model request timed out")

    except aiohttp.ClientConnectorError as e:
        logger.error(f"Connection to vLLM backend failed: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Cannot connect to Model Engine. Is it running? ({str(e)})"
        )

    except Exception as e:
        logger.exception("Unexpected error during request processing")
        raise HTTPException(status_code=500, detail=str(e))

    # Calculate performance metrics
    latency = time.time() - start_time
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    tokens_per_sec = tokens / latency if latency > 0 else 0
    
    logger.info(
        f"Request completed in {latency:.2f}s | "
        f"{tokens} tokens | "
        f"{tokens_per_sec:.1f} tokens/sec"
    )

    # Construct and return response
    return ChatResponse(
        id=str(uuid.uuid4()),
        object="chat.completion",
        created=int(time.time()), 
        model=data.get("model", settings.MODEL_ID),
        choices=[
            ChatChoice(
                index=c["index"],
                message=ChatMessage(
                    role=c["message"]["role"], 
                    content=c["message"]["content"]
                ),
                finish_reason=c.get("finish_reason", "stop"),
            )
            for c in data.get("choices", [])
        ],
        usage=ChatUsage(**data.get("usage", {
            "prompt_tokens": 0, 
            "completion_tokens": 0, 
            "total_tokens": 0
        })),
    )