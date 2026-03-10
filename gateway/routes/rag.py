"""
routes/rag.py

RAG query endpoint.
Exposes the full retrieval + generation pipeline over HTTP.

POST /v1/rag/query
{
    "question":    "What is the annual revenue?",
    "document_id": "uber-annual-report",   // optional — scope to one doc
    "collection":  "uber",                 // optional — defaults to .env value
    "max_tokens":  256                     // optional
}
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gateway.core.config import settings
from gateway.services.rag.embedder     import Embedder
from gateway.services.rag.vector_store import VectorStore
from gateway.services.rag.retriever    import Retriever
from gateway.services.rag.rag_service  import RAGService
from gateway.services.vllm_client import (
    ModelEngineError,
    ModelEngineTimeout,
    ModelEngineUnavailable,
)

logger = logging.getLogger("edge-gateway")
router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────

class RAGRequest(BaseModel):
    question:    str
    document_id: str | None = None
    collection:  str | None = None
    max_tokens:  int        = 512


class Citation(BaseModel):
    doc:     str | None
    page:    int | None
    section: str | None
    score:   float


class RAGResponse(BaseModel):
    answer:    str
    citations: list[Citation]
    usage:     dict


# ── Retriever cache — models are heavy, load once per collection ──────────

_retrievers: dict[str, Retriever] = {}


def _get_retriever(collection: str) -> Retriever:
    """
    Lazy-load and cache the Retriever (embedder + vector store) per collection.
    RAGService is intentionally NOT cached so max_tokens is honoured per-request.
    """
    if collection not in _retrievers:
        logger.info(f"Initialising RAG pipeline for collection '{collection}'...")
        embedder  = Embedder()
        logger.info(f"Embedder device: {embedder._dense.device}")
        store     = VectorStore(collection=collection)
        _retrievers[collection] = Retriever(embedder=embedder, store=store, top_k=4)
        logger.info("RAG pipeline ready")

    return _retrievers[collection]


# ── Endpoint ──────────────────────────────────────────────────────────────

@router.post("/rag/query", response_model=RAGResponse)
async def rag_query(request: RAGRequest):
    """
    Retrieve relevant document chunks and generate a cited answer.
    """
    collection = request.collection or settings.QDRANT_COLLECTION

    try:
        retriever = _get_retriever(collection)
        pipeline  = RAGService(retriever=retriever, max_tokens=request.max_tokens)
        result    = await pipeline.query(
            question    = request.question,
            document_id = request.document_id,
        )

        return RAGResponse(
            answer    = result["answer"],
            citations = result["citations"],
            usage     = result.get("usage", {}),
        )

    except ModelEngineUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    except ModelEngineTimeout:
        raise HTTPException(status_code=504, detail="Model request timed out")

    except ModelEngineError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    except Exception as e:
        logger.exception(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))