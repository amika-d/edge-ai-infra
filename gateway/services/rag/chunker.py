"""
services/rag/chunker.py

pip install docling docling-core sentence-transformers
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat, ConversionStatus
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer


# ---------------------------------------------------------------------------
# Config & Output model
# ---------------------------------------------------------------------------

@dataclass
class AgreementChunkConfig:
    max_tokens: int = 512
    overlap_tokens: int = 100
    min_chunk_words: int = 30
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    do_ocr: bool = False
    do_table_structure: bool = False  # leases/agreements rarely need this


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------

class AgreementChunker:
    """
    Chunks a legal agreement PDF using Docling's HybridChunker.

    Usage::

        chunker = AgreementChunker()
        chunks = chunker.chunk_pdf("contracts/Lease_Agreement_2024.pdf")

        # Custom config
        config = AgreementChunkConfig(max_tokens=400, min_chunk_words=20)
        chunker = AgreementChunker(config)
        chunks = chunker.chunk_pdf("NDA.pdf")
    """

    def __init__(self, config: Optional[AgreementChunkConfig] = None):
        self.config = config or AgreementChunkConfig()

        self._converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=PdfPipelineOptions(
                        do_ocr=self.config.do_ocr,
                        do_table_structure=self.config.do_table_structure,
                        generate_page_images=False,
                    )
                )
            }
        )

        self._chunker = HybridChunker(
            tokenizer=HuggingFaceTokenizer(
                tokenizer=AutoTokenizer.from_pretrained(self.config.embedding_model),
                max_tokens=self.config.max_tokens,
            ),
            merge_peers=True,
        )

    def chunk_pdf(self, path: str | Path) -> list[Chunk]:
        path = str(path)
        doc_name = Path(path).name
        doc_id = Path(path).stem

        result = self._converter.convert(path)

        if result.status == ConversionStatus.FAILURE:
            errors = "; ".join(e.error_message for e in result.errors)
            raise RuntimeError(f"Docling conversion failed for '{doc_name}': {errors}")

        raw_chunks = list(self._chunker.chunk(result.document))
        chunks = []

        for idx, raw in enumerate(raw_chunks):
            text = raw.text.strip()
            if not text or len(text.split()) < self.config.min_chunk_words:
                continue

            page_number = self._extract_page(raw)
            headings = getattr(raw.meta, "headings", []) or []
            section_title = " > ".join(headings) if headings else "Unknown Section"

            chunks.append(Chunk(
                chunk_id=f"{doc_id}_{uuid.uuid4().hex[:8]}",
                text=text,
                metadata={
                    "document_id":   doc_id,
                    "document_name": doc_name,
                    "page_number":   page_number,
                    "section_title": section_title,
                    "chunk_index":   idx,
                },
            ))

        return chunks

    @staticmethod
    def _extract_page(raw) -> Optional[int]:
        doc_items = getattr(raw.meta, "doc_items", [])
        if doc_items:
            prov = getattr(doc_items[0], "prov", [])
            if prov:
                return getattr(prov[0], "page_no", None)
        return None