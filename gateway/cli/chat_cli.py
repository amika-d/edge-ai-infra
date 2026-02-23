"""
gateway/cli/chat_cli.py

Usage:
    python gateway/cli/chat_cli.py --doc uber-annual-report
    python gateway/cli/chat_cli.py --collection legal_docs
"""
import asyncio
import argparse
import logging
import sys

from gateway.services.rag.embedder import Embedder
from gateway.services.rag.vector_store import VectorStore
from gateway.services.rag.retriever import Retriever
from gateway.services.rag.rag_service import RAGService

# ---------------------------------------------------------------------------
# Logging — structured, goes to stdout so Docker can capture it
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("chat-cli")


# ---------------------------------------------------------------------------
# Startup checks
# ---------------------------------------------------------------------------

def check_qdrant(store: VectorStore, collection: str):
    """Fail fast if Qdrant is unreachable or collection doesn't exist."""
    try:
        exists = store.client.collection_exists(collection)
        if not exists:
            logger.error(f"Collection '{collection}' not found in Qdrant.")
            logger.error("Run: python gateway/cli/ingest_cli.py <your_pdf>")
            sys.exit(1)
        info = store.client.get_collection(collection)
        logger.info(f"Qdrant collection '{collection}' — {info.points_count} chunks indexed")
    except Exception as e:
        logger.error(f"Cannot reach Qdrant: {e}")
        logger.error("Is Qdrant running? Check: docker compose ps")
        sys.exit(1)


def check_document_id(store: VectorStore, collection: str, document_id: str):
    """Warn if the document_id doesn't match any indexed chunk."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    try:
        results = store.client.scroll(
            collection_name=collection,
            scroll_filter=Filter(
                must=[FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )]
            ),
            limit=1,
            with_payload=False,
        )
        if not results[0]:
            logger.warning(f"document_id '{document_id}' not found in collection.")
            # Show what document_ids ARE available
            all_chunks = store.client.scroll(
                collection_name=collection,
                limit=100,
                with_payload=True,
            )
            ids = set(p.payload.get("document_id") for p in all_chunks[0] if p.payload)
            logger.warning(f"Available document_ids: {sorted(ids)}")
            logger.warning("Queries will return 'No relevant clause found.' — fix --doc argument")
    except Exception as e:
        logger.warning(f"Could not verify document_id: {e}")


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

async def chat_loop(args):
    logger.info("Initialising RAG pipeline...")

    try:
        embedder = Embedder()
        logger.info(f"Embedder ready — model: {embedder.model.get_sentence_embedding_dimension()}d")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        sys.exit(1)

    try:
        store = VectorStore(url=args.qdrant, collection=args.collection)
        check_qdrant(store, args.collection)
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"VectorStore init failed: {e}")
        sys.exit(1)

    if args.doc:
        check_document_id(store, args.collection, args.doc)
    else:
        
        all_chunks = store.client.scroll(args.collection, limit=200, with_payload=True)
        ids = set(p.payload.get("document_id") for p in all_chunks[0] if p.payload)
        logger.info(f"Available document_ids: {sorted(ids)}")   
        

    retriever = Retriever(embedder, store, top_k=args.top_k)
    rag       = RAGService(retriever, max_tokens=args.max_tokens)

    scope = f" (scoped to: {args.doc})" if args.doc else " (all documents)"
    print(f"\n💬 Legal RAG ready{scope}. Type 'exit' to quit.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not query or query.lower() == "exit":
            break

        logger.info(f"Query: '{query[:80]}' | doc_id={args.doc}")

        try:
            result = await rag.query(query, document_id=args.doc)

        except ConnectionError as e:
            # vLLM gateway unreachable
            logger.error(f"Gateway unreachable: {e}")
            print("❌ Cannot reach the LLM gateway. Is it running? Check: docker compose ps\n")
            continue

        except Exception as e:
            logger.exception(f"Unexpected error during query: {e}")
            print(f"❌ Unexpected error: {e}\n")
            continue

        answer    = result["answer"]
        citations = result["citations"]
        usage     = result.get("usage", {})

        if answer == "No relevant clause found.":
            logger.warning(f"No chunks retrieved for query: '{query[:80]}'")
            print(f"\nAnswer: {answer}\n")
            if args.doc:
                print(f"  Tip: verify --doc matches an indexed document_id\n")
            continue

        print(f"\nAnswer: {answer}\n")

        for c in citations:
            print(f"  📎 {c['doc']} | Page {c['page']} | {c['section']} (score: {c['score']})")

        if usage:
            logger.info(
                f"tokens={usage.get('completion_tokens','?')} | "
                f"latency={usage.get('latency','?')}s | "
                f"tok/s={usage.get('tokens_per_sec','?')}"
            )
            print(
                f"\n  ⚡ {usage.get('completion_tokens','?')} tokens | "
                f"{usage.get('latency','?')}s | "
                f"{usage.get('tokens_per_sec','?')} tok/s"
            )
        print()


def main():
    parser = argparse.ArgumentParser(description="Chat with your legal documents.")
    parser.add_argument("--doc",        default="uber-annual-report",                   help="document_id to scope queries (must match indexed name)")
    parser.add_argument("--collection", default="uber-report")
    parser.add_argument("--qdrant",     default="http://localhost:6333")
    parser.add_argument("--top-k",      type=int, default=5)
    parser.add_argument("--max-tokens", type=int, default=512)
    args = parser.parse_args()

    asyncio.run(chat_loop(args))


if __name__ == "__main__":
    main()