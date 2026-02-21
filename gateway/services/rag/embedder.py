from sentence_transformers import SentenceTransformer
from typing import List
from .chunker import Chunk

class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_chunks(self, chunks: list[Chunk]) -> list[tuple[Chunk, list[float]]]:
        texts = [c.text for c in chunks]
        vectors = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        return list(zip(chunks, [v.tolist() for v in vectors]))

    def embed_query(self, query: str) -> list[float]:
        return self.model.encode(query, convert_to_numpy=True).tolist()