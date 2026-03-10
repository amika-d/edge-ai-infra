"""
cli/ingest_cli.py

Ingest any PDF into Qdrant with dense + sparse vectors.
One universal chunker config — Docling handles document structure detection.

Usage:
    uv run gateway/cli/ingest_cli.py path/to/any_document.pdf
    uv run gateway/cli/ingest_cli.py path/to/doc.pdf --collection legal_docs
"""
import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ingest")


def main():
    parser = argparse.ArgumentParser(description="Ingest a PDF into the RAG vector store.")
    parser.add_argument("pdf",          help="Path to the PDF file")
    parser.add_argument("--collection", default="legal_docs")
    parser.add_argument("--qdrant",     default=None, help="Qdrant URL (overrides .env)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        logger.error(f"File not found: {pdf_path}")
        sys.exit(1)

    # Lazy imports
    from gateway.services.rag.chunker      import HierarchicalDocChunker, HierarchicalChunkConfig
    from gateway.services.rag.embedder     import Embedder
    from gateway.services.rag.vector_store import VectorStore

    # One universal config for all document types.
    # Docling detects headings, tables, layout automatically.
    # No document type detection needed here.
    config = HierarchicalChunkConfig(
    parent_max_tokens = 500,
    child_max_tokens  = 150,
    child_overlap     = 20,
)
    chunker = HierarchicalDocChunker(config)

    logger.info(f"Chunking: {pdf_path.name}")
    chunks = chunker.chunk_pdf(str(pdf_path))
    logger.info(f"  -> {len(chunks)} chunks")

    if not chunks:
        logger.error("No chunks produced — check PDF and Docling installation")
        sys.exit(1)

    logger.info("Loading embedder (dense + sparse)...")
    embedder = Embedder()

    logger.info("Embedding chunks...")
    chunk_embeddings = embedder.embed_chunks(chunks)

    logger.info("Connecting to Qdrant...")
    store = VectorStore(url=args.qdrant, collection=args.collection)

    # Create collection + payload indexes BEFORE uploading
    store.create_collection(vector_size=embedder.dimension)

    info = store.collection_info()
    logger.info(f"Collection: {info['status']} | points before: {info['points_count']}")

    logger.info("Uploading to Qdrant...")
    store.upsert(chunk_embeddings)

    info = store.collection_info()
    logger.info(f"Done — points after: {info['points_count']}")
    logger.info(f"Documents in collection: {store.list_document_ids()}")


if __name__ == "__main__":
    main()