"""
Hierarchical document chunking for RAG systems.

This module provides a hybrid chunking strategy that creates parent-child
chunk relationships for improved context retrieval. Parent chunks maintain
full section context while child chunks enable precise semantic search.

Strategy:
  PARENT chunks (800-1000 tokens) — full sections via HierarchicalChunker
                                     stored for context expansion at query time
  CHILD chunks (200-400 tokens) — token-bounded via HybridChunker
                                   embedded + stored for similarity search

Query flow:
  1. Search child chunks → precise semantic match
  2. Retrieve parent_id → fetch parent chunk for full context
  3. Send parent text to LLM → complete, coherent answer

This prevents "context dilution" where a specific figure loses its meaning
because the surrounding section was cut off.

Classes:
    HierarchicalChunkConfig: Configuration for chunking behavior
    ParentChunk: Full section chunk for context expansion
    Chunk: Embeddable child chunk with parent reference
    HierarchicalDocChunker: Main chunking implementation

Functions:
    chunk_pdf: Convenience function for single-file processing

Example:
    >>> config = HierarchicalChunkConfig.annual_report()
    >>> chunker = HierarchicalDocChunker(config)
    >>> chunks = chunker.chunk_pdf("document.pdf")
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Generator

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat, ConversionStatus
from docling.chunking import HybridChunker
from docling_core.transforms.chunker import HierarchicalChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

# Configure module logger
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Token estimation and splitting
DEFAULT_WORD_TO_TOKEN_RATIO = 0.75
DEFAULT_OVERLAP_RATIO = 0.15
MIN_EXCERPT_LENGTH = 150
UUID_LENGTH = 8

# Default model
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class HierarchicalChunkConfig:
    """
    Configuration for hybrid hierarchical chunking.

    This class defines chunking parameters and provides preset configurations
    optimized for different document types.

    Attributes:
        parent_max_tokens: Token ceiling for parent chunks (broad context)
        child_max_tokens: Token ceiling for child chunks (retrieval units)
        min_chunk_words: Skip fragments below this word count
        do_ocr: Enable OCR for scanned documents
        do_table_structure: Enable TableFormer for financial documents
        embedding_model: HuggingFace model ID for tokenizer

    Raises:
        ValueError: If configuration parameters are invalid
    """
    parent_max_tokens: int = 1000
    child_max_tokens: int = 300
    min_chunk_words: int = 30
    do_ocr: bool = False
    do_table_structure: bool = True
    embedding_model: str = DEFAULT_EMBEDDING_MODEL

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.parent_max_tokens <= 0:
            raise ValueError("parent_max_tokens must be positive")
        if self.child_max_tokens <= 0:
            raise ValueError("child_max_tokens must be positive")
        if self.child_max_tokens >= self.parent_max_tokens:
            raise ValueError("child_max_tokens must be less than parent_max_tokens")
        if self.min_chunk_words < 0:
            raise ValueError("min_chunk_words cannot be negative")
        if not self.embedding_model.strip():
            raise ValueError("embedding_model cannot be empty")

    @classmethod
    def agreement(cls) -> "HierarchicalChunkConfig":
        """
        Configuration for short legal contracts.
        
        Optimized for lease agreements, NDAs, employment agreements.
        Uses smaller chunks and disables table processing for text-focused documents.
        
        Returns:
            Configuration optimized for legal agreements
        """
        return cls(
            parent_max_tokens=800,
            child_max_tokens=250,
            min_chunk_words=20,
            do_table_structure=False,
        )

    @classmethod
    def annual_report(cls) -> "HierarchicalChunkConfig":
        """
        Configuration for large financial filings.
        
        Optimized for SEC filings, 10-K forms, annual reports.
        Enables table processing for financial statements.
        
        Returns:
            Configuration optimized for financial documents
        """
        return cls(
            parent_max_tokens=1000,
            child_max_tokens=350,
            min_chunk_words=40,
            do_table_structure=True,
        )

    @classmethod
    def regulatory(cls) -> "HierarchicalChunkConfig":
        """
        Configuration for regulatory and compliance documents.
        
        Optimized for dense technical documents with complex structure.
        
        Returns:
            Configuration optimized for regulatory documents
        """
        return cls(
            parent_max_tokens=900,
            child_max_tokens=300,
            min_chunk_words=30,
            do_table_structure=True,
        )


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ParentChunk:
    """
    Full section chunk for context expansion.
    
    Parent chunks are NOT embedded but stored in Qdrant payload.
    Retrieved via parent_id reference from child chunks.
    
    Attributes:
        parent_id: Unique identifier for this parent chunk
        text: Full section text content
        metadata: Document metadata including provenance information
    """
    parent_id: str
    text: str
    metadata: Dict[str, Any]


@dataclass
class Chunk:
    """
    Embeddable child chunk with parent reference.
    
    Child chunks are embedded and stored as vectors in Qdrant.
    Contains parent_id for context expansion during retrieval.
    
    Attributes:
        chunk_id: Unique identifier for this chunk
        text: Chunk text content for embedding
        metadata: Includes parent_id and parent_text for context expansion
    """
    chunk_id: str
    text: str
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Core Chunker
# ---------------------------------------------------------------------------

class HierarchicalDocChunker:
    """
    Hybrid hierarchical chunker producing parent-child chunk pairs.
    
    This class implements a two-stage chunking strategy:
    1. Create parent chunks from document structure (no token limits)
    2. Split parents into token-bounded child chunks for embedding
    
    Args:
        config: Chunking configuration, defaults to base config
        
    Raises:
        ValueError: If configuration is invalid
        RuntimeError: If component initialization fails
        
    Example:
        >>> # Annual report processing
        >>> config = HierarchicalChunkConfig.annual_report()
        >>> chunker = HierarchicalDocChunker(config)
        >>> chunks = chunker.chunk_pdf("report.pdf")
        
        >>> # Stream processing for large files
        >>> for chunk in chunker.chunk_pdf_stream("big_report.pdf"):
        ...     vector_store.add(chunk)
    """

    def __init__(self, config: Optional[HierarchicalChunkConfig] = None) -> None:
        self.config = config or HierarchicalChunkConfig()
        
        try:
            self._initialize_components()
            logger.info("Initialized HierarchicalDocChunker with model: %s", 
                       self.config.embedding_model)
        except Exception as e:
            logger.error("Failed to initialize chunker components: %s", e)
            raise RuntimeError(f"Chunker initialization failed: {e}") from e

    def _initialize_components(self) -> None:
        """Initialize document converter and chunker components."""
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

        tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(self.config.embedding_model),
            max_tokens=self.config.child_max_tokens,
        )

        # HierarchicalChunker for structure-based parent chunks
        self._hier_chunker = HierarchicalChunker()

        # HybridChunker for token-bounded child chunks
        self._hybrid_chunker = HybridChunker(
            tokenizer=tokenizer,
            merge_peers=True,
        )

    # ------------------------------------------------------------------ public

    def chunk_pdf(self, path: Union[str, Path]) -> List[Chunk]:
        """
        Parse and chunk a PDF into parent-child chunk pairs.
        
        Args:
            path: Path to the PDF file to process
            
        Returns:
            List of child chunks with parent context in metadata
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            RuntimeError: If document conversion fails
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"PDF file not found: {path_obj}")
            
        doc_name = path_obj.name
        doc_id = path_obj.stem

        logger.info("Converting document: %s", doc_name)
        result = self._converter.convert(str(path_obj))

        if result.status == ConversionStatus.FAILURE:
            errors = "; ".join(e.error_message for e in result.errors)
            logger.error("Document conversion failed for '%s': %s", doc_name, errors)
            raise RuntimeError(f"Docling failed for '{doc_name}': {errors}")

        dl_doc = result.document

        # Step 1: Build parent chunks from document hierarchy
        logger.debug("Building parent chunks using HierarchicalChunker")
        parent_chunks = self._build_parents(dl_doc, doc_id, doc_name)
        logger.info("Built %d parent sections", len(parent_chunks))

        # Step 2: Split each parent into child chunks
        logger.debug("Splitting into child chunks (max=%d tokens)", 
                    self.config.child_max_tokens)
        child_chunks = self._build_children(parent_chunks, doc_id, doc_name)
        logger.info("Generated %d child chunks", len(child_chunks))

        return child_chunks

    def chunk_pdf_stream(self, path: Union[str, Path]) -> Generator[Chunk, None, None]:
        """
        Generator version that yields child chunks one by one.
        
        Useful for processing large documents without loading all chunks into memory.
        
        Args:
            path: Path to the PDF file to process
            
        Yields:
            Individual child chunks
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            RuntimeError: If document conversion fails
        """
        for chunk in self.chunk_pdf(path):
            yield chunk

    # ----------------------------------------------------------------- private

    def _build_parents(self, dl_doc: Any, doc_id: str, doc_name: str) -> List[ParentChunk]:
        """
        Create full-section parent chunks using HierarchicalChunker.
        
        These chunks capture complete context without token limits
        and serve as the source for child chunk generation.
        
        Args:
            dl_doc: Docling document object
            doc_id: Document identifier
            doc_name: Document name for metadata
            
        Returns:
            List of parent chunks with complete section content
        """
        parents = []
        for raw in self._hier_chunker.chunk(dl_doc):
            text = raw.text.strip()
            if not text or len(text.split()) < self.config.min_chunk_words:
                continue

            page_number = self._extract_page(raw)
            headings = getattr(raw.meta, "headings", []) or []
            section_title = headings[0] if headings else "Unknown Section"
            parent_id = f"{doc_id}_parent_{uuid.uuid4().hex[:UUID_LENGTH]}"

            parents.append(ParentChunk(
                parent_id=parent_id,
                text=text,
                metadata={
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "page_number": page_number,
                    "section_title": section_title,
                    "headings": headings,
                },
            ))
        return parents

    def _build_children(
        self,
        parents: List[ParentChunk],
        doc_id: str,
        doc_name: str,
    ) -> List[Chunk]:
        """
        Split parent chunks into token-bounded child chunks.
        
        Each child chunk carries its parent_id and parent_text
        to enable context expansion during retrieval.
        
        Args:
            parents: List of parent chunks to split
            doc_id: Document identifier
            doc_name: Document name for metadata
            
        Returns:
            List of child chunks with parent references
        """
        children = []
        child_index = 0

        for parent in parents:
            sub_texts = self._token_split(parent.text)

            for sub_text in sub_texts:
                if len(sub_text.split()) < self.config.min_chunk_words:
                    continue

                chunk_id = f"{doc_id}_child_{uuid.uuid4().hex[:UUID_LENGTH]}"

                children.append(Chunk(
                    chunk_id=chunk_id,
                    text=sub_text,
                    metadata={
                        # Core provenance
                        "document_id": parent.metadata["document_id"],
                        "document_name": parent.metadata["document_name"],
                        "page_number": parent.metadata["page_number"],
                        "section_title": parent.metadata["section_title"],
                        "headings": parent.metadata["headings"],
                        "chunk_index": child_index,
                        # Parent reference for context expansion
                        "parent_id": parent.parent_id,
                        "parent_text": parent.text,
                    },
                ))
                child_index += 1

        return children

    def _token_split(self, text: str) -> List[str]:
        """
        Split text into child-sized chunks respecting token limits.
        
        Uses word-based approximation with configurable overlap to maintain
        context continuity between adjacent chunks.
        
        Args:
            text: Text to split into smaller chunks
            
        Returns:
            List of text chunks within token limits
        """
        words = text.split()
        max_words = int(self.config.child_max_tokens * DEFAULT_WORD_TO_TOKEN_RATIO)
        overlap = int(max_words * DEFAULT_OVERLAP_RATIO)

        if len(words) <= max_words:
            return [text]

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + max_words, len(words))
            chunks.append(" ".join(words[start:end]))
            start += max_words - overlap

        return chunks

    @staticmethod
    def _extract_page(raw: Any) -> Optional[int]:
        """
        Extract page number from raw chunk metadata.
        
        Args:
            raw: Raw chunk from HierarchicalChunker
            
        Returns:
            Page number if available, None otherwise
        """
        doc_items = getattr(raw.meta, "doc_items", [])
        if doc_items:
            prov = getattr(doc_items[0], "prov", [])
            if prov:
                return getattr(prov[0], "page_no", None)
        return None


# ---------------------------------------------------------------------------
# Keep AgreementChunker as a simple alias for backward compatibility
# ---------------------------------------------------------------------------

class AgreementChunker(HierarchicalDocChunker):
    """
    Specialized chunker for short legal agreements.
    
    Backward-compatible alias that uses agreement-optimized configuration
    by default. Suitable for contracts, NDAs, and employment agreements.
    
    Args:
        config: Optional custom configuration, defaults to agreement preset
    """
    def __init__(self, config: Optional[HierarchicalChunkConfig] = None) -> None:
        super().__init__(config or HierarchicalChunkConfig.agreement())


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def chunk_pdf(
    path: Union[str, Path],
    config: Optional[HierarchicalChunkConfig] = None,
) -> List[Chunk]:
    """
    Convenience function for single-file PDF processing.
    
    Args:
        path: Path to PDF file
        config: Chunking configuration, defaults to base config
        
    Returns:
        List of child chunks with parent context
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        RuntimeError: If document conversion fails
        
    Example:
        >>> from gateway.services.rag.chunker import chunk_pdf, HierarchicalChunkConfig
        
        >>> # Process annual report
        >>> chunks = chunk_pdf("annual-report.pdf", 
        ...                   HierarchicalChunkConfig.annual_report())
        
        >>> # Process legal agreement  
        >>> chunks = chunk_pdf("contract.pdf",
        ...                   HierarchicalChunkConfig.agreement())
        
        >>> # Inspect results
        >>> for chunk in chunks[:3]:
        ...     print(f"Page {chunk.metadata['page_number']} | 
        ...            {chunk.metadata['section_title']}")
        ...     print(f"Child: {chunk.text[:150]}")
    """
    return HierarchicalDocChunker(config).chunk_pdf(path)