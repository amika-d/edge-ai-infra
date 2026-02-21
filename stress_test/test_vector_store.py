import uuid
import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from gateway.services.rag.vector_store import VectorStore
from gateway.services.rag.chunker import Chunk


def test_vector_store_integration():
    """
    Integration test:
    - Creates a temporary collection
    - Inserts dummy embeddings
    - Runs similarity search using query_points (replaces deprecated .search())
    - Verifies retrieval works
    - Cleans up after itself
    """

    collection_name = f"test_collection_{uuid.uuid4().hex[:6]}"

    # Initialize vector store
    store = VectorStore(url="http://localhost:6333")

    # FIX 1: recreate_collection is deprecated.
    # Use collection_exists() + create_collection() instead.
    if store.client.collection_exists(collection_name):
        store.client.delete_collection(collection_name)

    store.client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )

    # Dummy chunks
    chunks = [
        Chunk(
            chunk_id=1,
            text="Termination clause states that contract ends with 30 days notice.",
            metadata={"tenant_id": "tenant_1", "page_number": 4},
        ),
        Chunk(
            chunk_id=2,
            text="Payment terms require invoice within 15 days.",
            metadata={"tenant_id": "tenant_1", "page_number": 2},
        ),
    ]

    # Dummy embeddings
    embeddings = [
        [0.1, 0.2, 0.3, 0.4],
        [0.9, 0.1, 0.1, 0.1],
    ]

    # Insert points
    store.client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=chunk.chunk_id,
                vector=embedding,
                payload=chunk.metadata,
            )
            for chunk, embedding in zip(chunks, embeddings)
        ],
    )

    # FIX 2: .search() is fully removed in recent qdrant-client versions.
    # Use .query_points() instead — the unified search API.
    results = store.client.query_points(
        collection_name=collection_name,
        query=[0.1, 0.2, 0.3, 0.4],   # query= replaces query_vector=
        limit=1,
    ).points                            # .points gives you the ScoredPoint list

    assert len(results) == 1
    assert results[0].id == 1

    print(f"✅ Vector store test passed for collection: {collection_name}")
    print(f"   Top result → id={results[0].id}, score={results[0].score:.4f}")
    print(f"   Payload    → {results[0].payload}")

    # Cleanup
    store.client.delete_collection(collection_name)