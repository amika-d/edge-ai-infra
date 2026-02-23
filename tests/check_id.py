# run this standalone
from gateway.services.rag.embedder import Embedder
from gateway.services.rag.vector_store import VectorStore

embedder = Embedder()
store    = VectorStore(url="http://localhost:6333", collection="uber-report")

query  = "What was Uber's total revenue for the year 2024?"
vector = embedder.embed_query(query)


# raw search — no document_id filter
results = store.client.query_points(
    collection_name="uber-report",
    query=vector,
    limit=5,
    with_payload=True,
).points

for r in results:
    print(f"score={r.score:.3f} | page={r.payload.get('page_number')} | {r.payload.get('section_title')[:50]}")
    print(f"  {r.payload.get('text','')[:150]}")
    print()