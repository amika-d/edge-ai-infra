"""
chat_cli.py  —  Chat with your indexed documents via the vLLM gateway

Usage:
    python chat_cli.py
    python chat_cli.py --doc lease_agreement
    python chat_cli.py --doc lease_agreement --debug
    python chat_cli.py --collection legal_docs
"""
import os
import asyncio
import argparse
from gateway.services.rag.embedder import Embedder
from gateway.services.rag.vector_store import VectorStore
from gateway.services.rag.retriever import Retriever
from gateway.services.rag.rag_service import RAGService


async def chat_loop(args):
    embedder  = Embedder()
    store     = VectorStore(url=args.qdrant, collection=args.collection)
    retriever = Retriever(embedder, store, top_k=args.top_k)
    rag       = RAGService(retriever, max_tokens=args.max_tokens)

    scope = f" (scoped to: {args.doc})" if args.doc else " (all documents)"
    print(f"💬 Legal RAG ready{scope}. Type 'exit' to quit.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not query or query.lower() == "exit":
            break

        if args.debug:
            query_vector = embedder.embed_query(query)
            chunks = store.search(query_vector, top_k=args.top_k, document_id=args.doc)
            if not chunks:
                print(f"\n  ⚠️  No chunks retrieved for document_id='{args.doc}'")
                print("  Check http://localhost:6333/dashboard to see stored document_ids\n")
                continue
            print(f"\n  📦 {len(chunks)} chunks retrieved:")
            for i, c in enumerate(chunks, 1):
                print(f"  [{i}] doc={c.get('document_id')} | page={c.get('page_number')} | score={c.get('score', 0):.4f}")
                print(f"       {c['text'][:200]}...\n")

        try:
            result = await rag.query(query, document_id=args.doc)
        except Exception as e:
            print(f"❌ Error: {e}\n")
            continue

        print(f"\nAnswer: {result['answer']}\n")

        for c in result["citations"]:
            print(f"  📎 {c['doc']} | Page {c['page']} | {c['section']} (score: {c['score']})")

        usage = result.get("usage", {})
        if usage:
            print(
                f"\n  ⚡ {usage.get('completion_tokens', '?')} tokens | "
                f"{usage.get('latency', '?')}s | "
                f"{usage.get('tokens_per_sec', '?')} tok/s"
            )
        print()


def main():
    parser = argparse.ArgumentParser(description="Chat with your legal documents.")
    parser.add_argument("--doc",        default=None,                   help="document_id to scope (e.g. 'lease_agreement')")
    parser.add_argument("--collection", default=os.getenv("COLLECTION", "legal_docs"))
    parser.add_argument("--qdrant",     default=os.getenv("QDRANT_URL",  "http://localhost:6333"))
    parser.add_argument("--top-k",      type=int, default=5)
    parser.add_argument("--max-tokens", type=int, default=int(os.getenv("MAX_TOKENS", 512)))
    parser.add_argument("--debug",      action="store_true",            help="Show retrieved chunks before answer")
    args = parser.parse_args()

    asyncio.run(chat_loop(args))


if __name__ == "__main__":
    main()