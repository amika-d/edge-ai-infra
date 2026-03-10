"""
services/rag/embedder.py

Produces BOTH dense and sparse vectors per chunk.
Dense  → BAAI/bge-base-en-v1.5 (768 dims, ONNX backend)
Sparse → FastEmbed SPLADE (BM25-style keyword vectors)

Replaces the old dense-only Embedder + manual query_rewriter.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
import torch

from gateway.core.config import settings

CACHE_DIR = settings.MODEL_DIR / "fastembed_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

DENSE_MODEL  = "BAAI/bge-base-en-v1.5"
SPARSE_MODEL = "prithivida/Splade_PP_en_v1"


@dataclass
class ChunkEmbedding:
    chunk:         dict
    dense_vector:  list[float]
    sparse_indices: list[int]
    sparse_values:  list[float]


class Embedder:
    """Dual-vector embedder — dense + sparse per text."""

    def __init__(
        self,
        dense_model:  str = DENSE_MODEL,
        sparse_model: str = SPARSE_MODEL,
    ):  
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading dense model: {dense_model} on device: {device}")
        self._dense = SentenceTransformer(dense_model, device=device, cache_folder=str(CACHE_DIR))

        logger.info(f"Loading sparse model: {sparse_model}")
        self._sparse = SparseTextEmbedding(model_name=sparse_model, cache_dir=str(CACHE_DIR))

        self.dimension = self._dense.get_sentence_embedding_dimension()
        logger.info(f"Dense dimension: {self.dimension}")

    # ── Chunk embedding (ingestion) ───────────────────────────────────────

    def embed_chunks(self, chunks: list[dict]) -> list[ChunkEmbedding]:
        """Embed a list of chunk dicts → list of ChunkEmbedding."""
        texts = [c.get("text", "") for c in chunks]

        logger.info(f"Embedding {len(texts)} chunks...")

        dense_vecs  = self._dense.encode(texts, batch_size=32, show_progress_bar=True)
        sparse_vecs = list(self._sparse.embed(texts, batch_size=32))

        results = []
        for chunk, dv, sv in zip(chunks, dense_vecs, sparse_vecs):
            results.append(ChunkEmbedding(
                chunk          = chunk,
                dense_vector   = dv.tolist(),
                sparse_indices = sv.indices.tolist(),
                sparse_values  = sv.values.tolist(),
            ))

        return results

    # ── Query embedding (retrieval) ───────────────────────────────────────

    def embed_query(self, query: str) -> tuple[list[float], dict]:
        """
        Embed a query string.
        Returns: (dense_vector, sparse_dict)
        sparse_dict = {"indices": [...], "values": [...]}
        """
        dense = self._dense.encode([query])[0].tolist()

        sparse_result = list(self._sparse.embed([query]))[0]
        sparse = {
            "indices": sparse_result.indices.tolist(),
            "values":  sparse_result.values.tolist(),
        }

        return dense, sparse