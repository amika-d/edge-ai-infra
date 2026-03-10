"""
services/rag/retriever.py

Hybrid retrieval with parent-child context expansion.
Replaces dense-only retriever + manual query_rewriter.

Flow:
  query → embed (dense + sparse) → hybrid RRF search → expand to parents
"""
from __future__ import annotations

import logging

from .embedder import Embedder
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:

    def __init__(
        self,
        embedder:           Embedder,
        store:              VectorStore,
        top_k:              int  = 5,
        use_parent_context: bool = True,
    ):
        self.embedder           = embedder
        self.store              = store
        self.top_k              = top_k
        self.use_parent_context = use_parent_context

    def retrieve(self, query: str, document_id: str | None = None) -> list[dict]:
        """
        Embed query → hybrid RRF search → expand children to parent context.
        """
        # Embed query into dense + sparse simultaneously
        dense_vector, sparse_vector = self.embedder.embed_query(query)

        results = self.store.search(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            top_k=self.top_k,
            document_id=document_id,
        )

        if not results:
            logger.warning(f"No chunks retrieved for: '{query[:80]}'")
            return []

        top_score = results[0].get("score", 0)
        logger.info(f"Retrieved {len(results)} chunks — top RRF score: {top_score:.4f}")

        if self.use_parent_context:
            return self._expand_to_parents(results)

        return results

    def _expand_to_parents(self, results: list[dict]) -> list[dict]:
        """
        Replace child text with parent text for LLM context.
        Deduplicates by parent_id so we don't send the same
        parent section twice.
        """
        seen_parents = set()
        expanded     = []

        for r in results:
            parent_id   = r.get("parent_id")
            parent_text = r.get("parent_text")

            # Deduplicate — if two children share a parent, send parent once
            if parent_id and parent_id in seen_parents:
                continue
            if parent_id:
                seen_parents.add(parent_id)

            expanded.append({
                **r,
                # LLM sees full parent section
                "text":       parent_text if parent_text else r.get("text", ""),
                # Citation shows child excerpt that triggered retrieval
                "child_text": r.get("text", ""),
            })

        return expanded