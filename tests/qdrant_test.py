from gateway.core.config import settings

print("Testing Qdrant connection...")
print(f"QDRANT_URL: {settings.QDRANT_URL}")
print(f"QDRANT_API_KEY: {settings.QDRANT_API_KEY}")


from qdrant_client import QdrantClient
from gateway.core.config import settings

client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
info = client.get_collection("uber-annual")
print("Expected vector size:", info.config.params.vectors.size)
from gateway.services.rag.embedder import Embedder
# Check what your embedder is actually producing
embedder = Embedder()
embedding = embedder.embed_query("test")
print("Actual vector size:", len(embedding))