"""
services/rag/chunker.py

Hierarchical parent-child chunker using Docling for PDF parsing.

Strategy:
  Docling parses PDF → detects headings, tables, layout
  Parent chunks  → full document sections (800-1000 tokens)
  Child chunks   → smaller slices of each parent (200-350 tokens)
  
  Children carry:
    - parent_id    → pointer back to parent
    - parent_text  → full section text (stored in payload, not as vector)
    - document_id  → for Qdrant filtering
    - page_number  → for citations
    - section_title → heading Docling detected

Only CHILD chunks get embedded as vectors.
Parent text rides along in the payload for context expansion at query time.

What changed vs old AgreementChunker:
  - Works for ANY document type (not just agreements)
  - Two config presets: agreement() and annual_report()
  - chunk_type field added ("child") for payload index
  - Cleaner token splitting using transformers tokenizer
  - document_id derived from filename (no manual passing)
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HierarchicalChunkConfig:
    """
    Universal config — works for any document type.
    Docling handles structural understanding (headings, tables, layout).
    We just apply consistent token windows on top.
    No per-document-type presets needed.
    """
    # Parent sizing
    parent_max_tokens: int = 900
    parent_min_words:  int = 30

    # Child sizing
    child_max_tokens:  int = 300
    child_min_words:   int = 15
    child_overlap:     int = 30   # token overlap between siblings

    # Embedding model for token counting
    embedding_model: str = "BAAI/bge-base-en-v1.5"


@dataclass
class Chunk:
    text:          str
    document_id:   str
    document_name: str
    page_number:   int
    section_title: str
    headings:      list[str]
    chunk_index:   int
    parent_id:     str
    parent_text:   str
    chunk_type:    str = "child"   # always "child" — parents live in payload only

    def to_dict(self) -> dict:
        return {
            "text":          self.text,
            "document_id":   self.document_id,
            "document_name": self.document_name,
            "page_number":   self.page_number,
            "section_title": self.section_title,
            "headings":      self.headings,
            "chunk_index":   self.chunk_index,
            "parent_id":     self.parent_id,
            "parent_text":   self.parent_text,
            "chunk_type":    self.chunk_type,
        }


class HierarchicalDocChunker:
    """
    Parses a PDF with Docling, produces parent sections,
    splits each into child chunks, returns list of Chunk dicts
    ready for embedding.
    """

    def __init__(self, config: HierarchicalChunkConfig | None = None):
        self.config = config or HierarchicalChunkConfig()
        self._tokenizer = self._load_tokenizer()

    def _load_tokenizer(self):
        try:
            from transformers import AutoTokenizer
            tok = AutoTokenizer.from_pretrained(self.config.embedding_model)
            logger.info(f"Tokenizer loaded: {self.config.embedding_model}")
            return tok
        except Exception as e:
            logger.warning(f"Tokenizer load failed ({e}) — falling back to word count")
            return None

    def _token_count(self, text: str) -> int:
        if self._tokenizer:
            return len(self._tokenizer.encode(text, add_special_tokens=False))
        return len(text.split())  # fallback: word count

    # ── Public API ────────────────────────────────────────────────────────

    def chunk_pdf(self, pdf_path: str) -> list[dict]:
        """
        Main entry point.
        Returns list of chunk dicts ready for Embedder.embed_chunks().
        """
        path          = Path(pdf_path)
        document_id   = path.stem.lower().replace(" ", "-")
        document_name = path.name

        logger.info(f"Parsing PDF: {path.name}")
        docling_chunks = self._parse_with_docling(str(path))
        logger.info(f"  Docling produced {len(docling_chunks)} raw sections")

        parents = self._build_parents(docling_chunks, document_id, document_name)
        logger.info(f"  Built {len(parents)} parent sections")

        children = self._build_children(parents)
        logger.info(f"  Split into {len(children)} child chunks")

        return [c.to_dict() for c in children]

    # ── Docling parsing ───────────────────────────────────────────────────

    def _parse_with_docling(self, pdf_path: str) -> list[dict]:
        """
        Use Docling HybridChunker to parse PDF into structured sections.
        Each section has: text, page_number, headings.
        """
        from docling.document_converter import DocumentConverter
        from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
        from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker

        converter = DocumentConverter()
        result    = converter.convert(pdf_path)
        doc       = result.document

        # Use Docling's HybridChunker for initial section detection
        chunker = HybridChunker(
            tokenizer=self.config.embedding_model,
            max_tokens=self.config.parent_max_tokens,
            merge_peers=True,
        )

        raw_chunks = []
        for chunk in chunker.chunk(doc):
            meta = chunk.meta

            # Extract page number — use first page reference if available
            page_num = 0
            if hasattr(meta, "doc_items") and meta.doc_items:
                for item in meta.doc_items:
                    if hasattr(item, "prov") and item.prov:
                        page_num = item.prov[0].page_no
                        break

            # Extract headings from metadata
            headings = []
            if hasattr(meta, "headings") and meta.headings:
                headings = [str(h) for h in meta.headings]

            section_title = headings[-1] if headings else "General"

            text = chunk.text.strip()
            if not text:
                continue

            raw_chunks.append({
                "text":          text,
                "page_number":   page_num,
                "headings":      headings,
                "section_title": section_title,
            })

        return raw_chunks

    # ── Parent building ───────────────────────────────────────────────────

    def _build_parents(
        self,
        raw_chunks:    list[dict],
        document_id:   str,
        document_name: str,
    ) -> list[dict]:
        """
        Merge small adjacent sections into parents up to parent_max_tokens.
        Each parent gets a stable parent_id hash.
        """
        parents = []
        buffer_chunks: list[dict] = []
        buffer_tokens = 0

        def flush_buffer():
            if not buffer_chunks:
                return
            merged_text = "\n\n".join(c["text"] for c in buffer_chunks)
            word_count  = len(merged_text.split())

            if word_count < self.config.parent_min_words:
                return  # too short — skip

            # Stable ID from content hash
            parent_id = f"{document_id}_parent_{hashlib.md5(merged_text[:200].encode()).hexdigest()[:8]}"

            parents.append({
                "text":          merged_text,
                "document_id":   document_id,
                "document_name": document_name,
                "page_number":   buffer_chunks[0]["page_number"],
                "section_title": buffer_chunks[0]["section_title"],
                "headings":      buffer_chunks[0]["headings"],
                "parent_id":     parent_id,
            })

        for chunk in raw_chunks:
            tokens = self._token_count(chunk["text"])

            # If adding this chunk exceeds parent limit — flush first
            if buffer_tokens + tokens > self.config.parent_max_tokens and buffer_chunks:
                flush_buffer()
                buffer_chunks = []
                buffer_tokens = 0

            buffer_chunks.append(chunk)
            buffer_tokens += tokens

        flush_buffer()
        return parents

    # ── Child building ────────────────────────────────────────────────────

    def _build_children(self, parents: list[dict]) -> list[Chunk]:
        """
        Split each parent into overlapping child chunks.
        Children embed as vectors; parent_text rides in payload.
        """
        children    = []
        chunk_index = 0

        for parent in parents:
            child_texts = self._token_split(
                parent["text"],
                max_tokens=self.config.child_max_tokens,
                overlap=self.config.child_overlap,
            )

            for child_text in child_texts:
                word_count = len(child_text.split())
                if word_count < self.config.child_min_words:
                    continue  # skip noise

                children.append(Chunk(
                    text          = child_text,
                    document_id   = parent["document_id"],
                    document_name = parent["document_name"],
                    page_number   = parent["page_number"],
                    section_title = parent["section_title"],
                    headings      = parent["headings"],
                    chunk_index   = chunk_index,
                    parent_id     = parent["parent_id"],
                    parent_text   = parent["text"],
                    chunk_type    = "child",
                ))
                chunk_index += 1

        return children

    def _token_split(
        self,
        text:       str,
        max_tokens: int,
        overlap:    int = 30,
    ) -> list[str]:
        """
        Split text into overlapping token windows.
        Falls back to word splitting if tokenizer unavailable.
        """
        if self._tokenizer:
            return self._tokenizer_split(text, max_tokens, overlap)
        return self._word_split(text, max_tokens, overlap)

    def _tokenizer_split(self, text: str, max_tokens: int, overlap: int) -> list[str]:
        token_ids = self._tokenizer.encode(text, add_special_tokens=False)

        if len(token_ids) <= max_tokens:
            return [text]

        chunks = []
        start  = 0
        step   = max_tokens - overlap

        while start < len(token_ids):
            end    = min(start + max_tokens, len(token_ids))
            chunk  = self._tokenizer.decode(token_ids[start:end], skip_special_tokens=True)
            chunks.append(chunk.strip())
            if end == len(token_ids):
                break
            start += step

        return [c for c in chunks if c]

    def _word_split(self, text: str, max_tokens: int, overlap: int) -> list[str]:
        words  = text.split()
        if len(words) <= max_tokens:
            return [text]

        chunks = []
        start  = 0
        step   = max_tokens - overlap

        while start < len(words):
            end = min(start + max_tokens, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start += step

        return chunks