"""
services/rag/vector_store.py

Qdrant client with:
- Named vectors: "dense" (768-dim cosine) + "sparse" (SPLADE)
- Payload indexes created BEFORE any data upload
- HNSW config explicit (m=16, ef_construct=200)
- Batched upsert via upload_points
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    HnswConfigDiff,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    Prefetch,
    SearchParams,
    SparseIndexParams,
    SparseVectorParams,
    VectorParams,
)

from gateway.core.config import settings
from .embedder import ChunkEmbedding

logger = logging.getLogger(__name__)


class VectorStore:

    def __init__(
        self,
        url:        str | None = None,
        api_key:    str | None = None,
        collection: str | None = None,
    ):
        self.url        = url        or settings.QDRANT_URL
        self.api_key    = api_key    or getattr(settings, "QDRANT_API_KEY", None)
        self.collection = collection or settings.QDRANT_COLLECTION

        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=60,
        )

    # ── Collection setup ──────────────────────────────────────────────────

    def create_collection(self, vector_size: int = 768) -> None:
        """
        Create collection with named dense + sparse vectors.
        Payload indexes are created BEFORE any data so HNSW
        builds filter-aware links correctly.
        """
        if self.client.collection_exists(self.collection):
            logger.info(f"Collection '{self.collection}' already exists — skipping create")
            return

        logger.info(f"Creating collection '{self.collection}' (dense={vector_size}d + sparse)")

        self.client.create_collection(
            collection_name=self.collection,
            vectors_config={
                "dense": VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                    hnsw_config=HnswConfigDiff(
                        m=16,            # balanced connectivity
                        ef_construct=200, # good build quality
                    ),
                ),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False),
                ),
            },
        )

        # ── Payload indexes BEFORE data upload ────────────────────────────
        # Critical: HNSW builds filter-aware subgraph links during ingestion.
        # Adding indexes after data means inefficient search until rebuild.

        for field, schema in [
            ("document_id", PayloadSchemaType.KEYWORD),
            ("parent_id",   PayloadSchemaType.KEYWORD),
            ("chunk_type",  PayloadSchemaType.KEYWORD),  # "child" | "parent"
            ("page_number", PayloadSchemaType.INTEGER),
        ]:
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name=field,
                field_schema=schema,
            )
            logger.info(f"  Created payload index: {field}")

        logger.info(f"Collection '{self.collection}' ready")

    # ── Ingestion ─────────────────────────────────────────────────────────

    def upsert(self, embeddings: list[ChunkEmbedding]) -> None:
        """Batch upsert — dense + sparse vectors with full payload."""
        points = []

        for emb in embeddings:
            chunk = emb.chunk
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense": emb.dense_vector,
                    "sparse": {
                        "indices": emb.sparse_indices,
                        "values":  emb.sparse_values,
                    },
                },
                payload=chunk,
            )
            points.append(point)

        logger.info(f"Upserting {len(points)} points to '{self.collection}'...")

        # upload_points handles lazy batching + retries
        self.client.upload_points(
            collection_name=self.collection,
            points=points,
            batch_size=100,
            parallel=1,
        )

        logger.info("Upsert complete")

    # ── Retrieval ─────────────────────────────────────────────────────────

    def search(
        self,
        dense_vector:   list[float],
        sparse_vector:  dict,
        top_k:          int = 5,
        document_id:    str | None = None,
    ) -> list[dict]:
        """
        Hybrid search: dense + sparse prefetch → RRF fusion.
        Optionally scoped to a single document via document_id filter.
        """
        doc_filter = None
        if document_id:
            doc_filter = Filter(
                must=[FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )]
            )

        prefetch_limit = top_k * 10  # cast wider net before fusion

        results = self.client.query_points(
            collection_name=self.collection,
            prefetch=[
                Prefetch(
                    query=dense_vector,
                    using="dense",
                    filter=doc_filter,
                    limit=prefetch_limit,
                    params=SearchParams(hnsw_ef=128),
                ),
                Prefetch(
                    query={
                        "indices": sparse_vector["indices"],
                        "values":  sparse_vector["values"],
                    },
                    using="sparse",
                    filter=doc_filter,
                    limit=prefetch_limit,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            with_payload=True,
            score_threshold=0.1,
        ).points

        return [{"score": r.score, **r.payload} for r in results]

    # ── Inspection ────────────────────────────────────────────────────────

    def collection_info(self) -> dict:
        info = self.client.get_collection(self.collection)
        return {
            "status":          str(info.status),
            "points_count":    info.points_count,
            "indexed_vectors": info.indexed_vectors_count,
        }

    def list_document_ids(self) -> list[str]:
        """Return all unique document_ids in the collection."""
        results = self.client.scroll(
            collection_name=self.collection,
            with_payload=["document_id"],
            limit=1000,
        )[0]
        ids = {r.payload.get("document_id") for r in results if r.payload}
        return sorted(ids - {None})