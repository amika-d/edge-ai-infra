"""
services/rag/retriever.py
"""
import logging
from .embedder import Embedder
from .vector_store import VectorStore
from .query_rewriter import rewrite_for_logging

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        top_k: int = 5,
        use_parent_context: bool = True,
    ):
        self.embedder           = embedder
        self.store              = store
        self.top_k              = top_k
        self.use_parent_context = use_parent_context

    def retrieve(self, query: str, document_id: str | None = None) -> list[dict]:
        # Expand query with domain terms before embedding
        expanded, matched_terms = rewrite_for_logging(query)

        if matched_terms:
            logger.info(f"Query rewriter matched: {matched_terms}")
            logger.debug(f"Expanded query:\n{expanded}")

        query_vector = self.embedder.embed_query(expanded)
        results      = self.store.search(
            query_vector,
            top_k=self.top_k,
            document_id=document_id,
        )

        if not results:
            logger.warning(f"No chunks retrieved for query: '{query[:80]}'")
            return []

        logger.info(f"Retrieved {len(results)} chunks — top score: {results[0].get('score', 0):.3f}")

        if self.use_parent_context:
            return self._expand_to_parents(results)

        return results

    def _expand_to_parents(self, results: list[dict]) -> list[dict]:
        seen_parents = set()
        expanded     = []

        for r in results:
            parent_id   = r.get("parent_id")
            parent_text = r.get("parent_text")

            if parent_id and parent_id in seen_parents:
                continue
            if parent_id:
                seen_parents.add(parent_id)

            expanded.append({
                **r,
                "text":       parent_text if parent_text else r.get("text", ""),
                "child_text": r.get("text", ""),
            })

        return expanded