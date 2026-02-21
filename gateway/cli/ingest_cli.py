"""
ingest_cli.py  —  Index a PDF into Qdrant

Usage:
    python ingest_cli.py contracts/Lease_Agreement_2024.pdf
    python ingest_cli.py report.pdf --collection legal_docs --qdrant http://localhost:6333
"""
import argparse
from gateway.services.rag.chunker import AgreementChunker
from gateway.services.rag.embedder import Embedder
from gateway.services.rag.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(description="Ingest a PDF into the RAG vector store.")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--collection", default="legal_docs")
    parser.add_argument("--qdrant", default="http://localhost:6333")
    args = parser.parse_args()

    print(f"📄 Chunking: {args.pdf}")
    chunker = AgreementChunker()
    chunks = chunker.chunk_pdf(args.pdf)
    print(f"   → {len(chunks)} chunks")

    print("🔢 Embedding...")
    embedder = Embedder()
    chunk_embeddings = embedder.embed_chunks(chunks)

    print(f"💾 Storing in Qdrant collection '{args.collection}'...")
    store = VectorStore(url=args.qdrant, collection=args.collection)
    store.create_collection(vector_size=embedder.dimension)
    store.upsert(chunk_embeddings)

    print(f"✅ Done — {len(chunks)} chunks indexed from {args.pdf}")


if __name__ == "__main__":
    main()