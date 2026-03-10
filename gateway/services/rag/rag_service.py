"""
services/rag/rag_service.py
"""
import logging
from .retriever import Retriever
from .prompt_builder import build_prompt
from gateway.core.config import settings
from gateway.services.vllm_client import send_chat_request

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(
        self,
        retriever:   Retriever,
        max_tokens:  int   = 512,
        temperature: float = 0.0,
    ):
        self.retriever   = retriever
        self.max_tokens  = max_tokens
        self.temperature = temperature

    async def query(self, question: str, document_id: str | None = None) -> dict:
        chunks = self.retriever.retrieve(question, document_id=document_id)

        if not chunks:
            return {"answer": "No relevant clause found.", "citations": [], "usage": {}}

        messages = build_prompt(question, chunks)

        payload = {
            "model":       settings.SERVED_MODEL,
            "messages":    messages,
            "max_tokens":  self.max_tokens,
            "temperature": self.temperature,
            "stream":      False,
        }

        data   = await send_chat_request(payload)
        answer = data["choices"][0]["message"]["content"]

        citations = [
            {
                "doc":     c.get("document_name"),
                "page":    c.get("page_number"),
                "section": c.get("section_title"),
                "score":   round(c.get("score", 0), 4),
            }
            for c in chunks
        ]

        return {
            "answer":    answer,
            "citations": citations,
            "usage":     data.get("usage", {}),
        }