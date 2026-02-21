"""
services/rag/retriever.py
"""
from .embedder import Embedder
from .vector_store import VectorStore


class Retriever:
    def __init__(self, embedder: Embedder, store: VectorStore, top_k: int = 5):
        self.embedder = embedder
        self.store = store
        self.top_k = top_k

    def retrieve(self, query: str, document_id: str | None = None) -> list[dict]:
        query_vector = self.embedder.embed_query(query)
        return self.store.search(query_vector, top_k=self.top_k, document_id=document_id)