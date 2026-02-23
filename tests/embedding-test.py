from gateway.services.rag.vector_store import VectorStore

store = VectorStore(url="http://localhost:6333", collection="legal_docs")

# scroll through a few chunks
results = store.client.scroll(
    collection_name="legal_docs",
    limit=10,
    with_payload=True,
)

for point in results[0]:
    p = point.payload
    parent_len = len(p.get("parent_text", "").split())
    child_len  = len(p.get("text", "").split())
    same       = "same" if parent_len == child_len else "expanded"
    print(f"Page {p.get('page_number'):>3} | {p.get('section_title')[:40]:40} | child={child_len:>4}w parent={parent_len:>4}w | {same}")