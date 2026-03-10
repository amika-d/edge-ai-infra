"""
routes/chat.py

Chat completion endpoint — delegates to vLLM via vllm_client.
"""
import time
import uuid
import logging
from fastapi import APIRouter, HTTPException

from gateway.schemas.schemas import (
    ChatRequest,
    ChatResponse,
    ChatChoice,
    ChatMessage,
    ChatUsage,
)
from gateway.core.config import settings
from gateway.services.vllm_client import (
    send_chat_request,
    ModelEngineError,
    ModelEngineTimeout,
    ModelEngineUnavailable,
)
from gateway.metrics.metrics import (
    CHAT_REQUESTS_TOTAL,
    CHAT_PROMPT_TOKENS_TOTAL,
    CHAT_COMPLETION_TOKENS_TOTAL,
    ACTIVE_REQUESTS,
    REQUEST_LATENCY_SECONDS,
    TOKENS_PER_SECOND,
)

logger = logging.getLogger("edge-gateway")
router = APIRouter()


@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):

    ACTIVE_REQUESTS.inc()
    start_time = time.time()

    try:
        if request.max_tokens > settings.MAX_TOKENS:
            raise HTTPException(
                status_code=400,
                detail=f"max_tokens exceeds limit ({settings.MAX_TOKENS})",
            )

        payload = {
            "model":       settings.SERVED_MODEL,
            "messages":    [m.model_dump(mode="json") for m in request.messages],
            "max_tokens":  request.max_tokens,
            "temperature": request.temperature if request.temperature is not None else 0.7,
            "stream":      False,
        }

        logger.info(f"Forwarding to vLLM: {settings.VLLM_API_URL}")
        data = await send_chat_request(payload)

        raw_latency       = time.time() - start_time
        latency           = round(raw_latency, 2)
        usage_data        = data.get("usage", {})
        prompt_tokens     = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        total_tokens      = usage_data.get("total_tokens", 0)
        tokens_per_sec    = round(completion_tokens / raw_latency, 2) if raw_latency > 0 else 0.0

        CHAT_REQUESTS_TOTAL.labels(model=settings.MODEL_ID, status="success").inc()
        CHAT_PROMPT_TOKENS_TOTAL.inc(prompt_tokens)
        CHAT_COMPLETION_TOKENS_TOTAL.inc(completion_tokens)
        REQUEST_LATENCY_SECONDS.observe(raw_latency)
        TOKENS_PER_SECOND.set(tokens_per_sec)

        logger.info(f"Done | latency={latency}s | tokens={completion_tokens} | {tokens_per_sec} tok/s")

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
            usage=ChatUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency=latency,
                tokens_per_sec=tokens_per_sec,
            ),
        )

    except HTTPException:
        CHAT_REQUESTS_TOTAL.labels(model=settings.MODEL_ID, status="error").inc()
        raise

    except ModelEngineUnavailable as e:
        CHAT_REQUESTS_TOTAL.labels(model=settings.MODEL_ID, status="error").inc()
        raise HTTPException(status_code=503, detail=str(e))

    except ModelEngineTimeout:
        CHAT_REQUESTS_TOTAL.labels(model=settings.MODEL_ID, status="error").inc()
        raise HTTPException(status_code=504, detail="Model request timed out")

    except ModelEngineError as e:
        CHAT_REQUESTS_TOTAL.labels(model=settings.MODEL_ID, status="error").inc()
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    finally:
        ACTIVE_REQUESTS.dec()