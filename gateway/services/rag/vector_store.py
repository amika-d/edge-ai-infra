"""
services/rag/vector_store.py
pip install qdrant-client
"""
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct,
    Filter, FieldCondition, MatchValue,
)
from .chunker import Chunk


class VectorStore:
    def __init__(self, url: str = "http://localhost:6333", collection: str = "legal_docs"):
        self.client = QdrantClient(url=url)
        self.collection = collection

    def create_collection(self, vector_size: int):
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def upsert(self, chunk_embeddings: list[tuple[Chunk, list[float]]]):
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={**chunk.metadata, "text": chunk.text},
            )
            for chunk, vector in chunk_embeddings
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[dict]:
        query_filter = None
        if document_id:
            query_filter = Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            )

        results = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            query_filter=query_filter,
            with_payload=True,
            limit=top_k,
        ).points

        return [
            {"score": r.score, **r.payload}
            for r in results
        ]