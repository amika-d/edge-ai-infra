"""
services/rag/rag_service.py
"""
import os
import httpx
from .retriever import Retriever
from .prompt_builder import build_prompt

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8080")


class RAGService:
    def __init__(
        self,
        retriever: Retriever,
        gateway_url: str = GATEWAY_URL,
        max_tokens: int = int(os.getenv("MAX_TOKENS", 512)),
        temperature: float = 0.0,
    ):
        self.retriever = retriever
        self.endpoint = f"{gateway_url}/v1/chat/completions"
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def query(self, question: str, document_id: str | None = None) -> dict:
        chunks = self.retriever.retrieve(question, document_id=document_id)

        if not chunks:
            return {"answer": "No relevant clause found.", "citations": [], "usage": {}}

        messages = build_prompt(question, chunks)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.endpoint,
                json={
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            )
            response.raise_for_status()
            data = response.json()

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

        return {"answer": answer, "citations": citations, "usage": data.get("usage", {})}