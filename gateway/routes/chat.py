"""
Chat completion routes.

Handles incoming chat completion requests and delegates to the vLLM backend
through the vllm_client service.
"""

import time
import uuid
import logging
from fastapi import APIRouter, HTTPException

from gateway.auth.schemas import (
    ChatRequest,
    ChatResponse,
    ChatChoice,
    ChatMessage,
    ChatUsage,
)
from gateway.core.config import settings
from gateway.services.vllm_client import send_chat_request


from gateway.metrics.metrics import (
    CHAT_REQUESTS_TOTAL,
    CHAT_PROMPT_TOKENS_TOTAL,
    CHAT_COMPLETION_TOKENS_TOTAL,
    ACTIVE_REQUESTS,
    REQUEST_LATENCY_SECONDS,
    TOKENS_PER_SECOND,
)

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edge-gateway")

router = APIRouter()


@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """
    Handle chat completion requests.
    """

    ACTIVE_REQUESTS.inc()
    start_time = time.time()

    try:
        # Validate token limit
        if request.max_tokens > settings.MAX_TOKENS:
            raise HTTPException(
                status_code=400,
                detail=f"max_tokens exceeds allowed limit ({settings.MAX_TOKENS})",
            )

        # Prepare payload for vLLM
        payload = {
            "model": settings.SERVED_MODEL,
            "messages": [m.model_dump(mode="json") for m in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature if request.temperature is not None else 0.7,
            "stream": False,
        }

        logger.info(f"Sending request to vLLM backend: {settings.VLLM_API_URL}")

        # Call backend
        data = await send_chat_request(payload)

        # -----------------------------
        # Metrics Calculation
        # -----------------------------
        raw_latency = time.time() - start_time
        latency = round(raw_latency, 2)

        usage_data = data.get("usage", {})
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        total_tokens = usage_data.get("total_tokens", 0)

        tokens_per_sec = (
            round(completion_tokens / raw_latency, 2)
            if raw_latency > 0
            else 0.0
        )

        # -----------------------------
        # Prometheus Updates
        # -----------------------------
        CHAT_REQUESTS_TOTAL.labels(
            model=settings.MODEL_ID,
            status="success",
        ).inc()

        CHAT_PROMPT_TOKENS_TOTAL.inc(prompt_tokens)
        CHAT_COMPLETION_TOKENS_TOTAL.inc(completion_tokens)

        REQUEST_LATENCY_SECONDS.observe(raw_latency)

        TOKENS_PER_SECOND.set(tokens_per_sec)

        logger.info(
            f"Request completed | latency={latency}s | "
            f"tokens={completion_tokens} | throughput={tokens_per_sec} tokens/sec"
        )

        # -----------------------------
        # Build Response
        # -----------------------------
        usage = ChatUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency=latency,
            tokens_per_sec=tokens_per_sec,
        )

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
                        content=c["message"]["content"],
                    ),
                    finish_reason=c.get("finish_reason", "stop"),
                )
                for c in data.get("choices", [])
            ],
            usage=usage,
        )

    except Exception:
        # Track errors
        CHAT_REQUESTS_TOTAL.labels(
            model=settings.MODEL_ID,
            status="error",
        ).inc()
        raise

    finally:
        ACTIVE_REQUESTS.dec()
