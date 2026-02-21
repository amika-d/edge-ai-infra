import re
import fitz  # PyMuPDF
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class PageContent:
    """Raw content extracted from a single PDF page."""
    page_number: int          # 1-based
    raw_text: str
    headings: list[str] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """Full parsed representation of a PDF document."""
    document_id: str          # e.g. SHA-256 hash or a UUID
    document_name: str        # original filename
    file_path: str
    total_pages: int
    pages: list[PageContent] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Heading detection
# ---------------------------------------------------------------------------

# Patterns that suggest a line is a section heading in legal documents.
_HEADING_PATTERNS = [
    # ALL-CAPS lines (common in contracts: "TERMINATION", "REPRESENTATIONS")
    re.compile(r"^[A-Z][A-Z\s\-&,\.]{4,}$"),
    # Numbered sections: "1.", "1.1", "Section 2", "Article IV"
    re.compile(r"^(?:Section|Article|Clause|Schedule|Exhibit|Annex)?\s*\d+(?:\.\d+)*[\.\)]\s+\S", re.I),
    # Roman numeral headings: "IV. Obligations"
    re.compile(r"^[IVXLCDM]+\.\s+\S", re.I),
    # Title-case lines that are short (≤ 80 chars) and end without a period
    re.compile(r"^[A-Z][A-Za-z\s]{3,79}[^.]$"),
]


def _detect_headings(text: str) -> list[str]:
    """Return a list of lines from *text* that look like section headings."""
    headings = []
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) > 120:
            continue
        for pattern in _HEADING_PATTERNS:
            if pattern.match(line):
                headings.append(line)
                break
    return headings


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

class DocumentParser:
    """
    Parse a PDF file and return a :class:`ParsedDocument` with per-page
    text and detected headings.

    Usage::

        parser = DocumentParser()
        doc = parser.parse("contracts/Lease_Agreement_2024.pdf")
        for page in doc.pages:
            print(page.page_number, page.headings)
    """

    def __init__(self, detect_headings: bool = True):
        self.detect_headings = detect_headings

    # ------------------------------------------------------------------
    # Public API
    
    # ------------------------------------------------------------------

    def parse(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> ParsedDocument:
        """
        Parse *file_path* and return a fully-populated :class:`ParsedDocument`.

        Args:
            file_path: Path to the PDF file.
            document_id: Optional stable identifier. Defaults to the stem of
                         the filename if not provided.

        Returns:
            ParsedDocument with one :class:`PageContent` entry per page.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid PDF.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        doc_name = path.name
        doc_id = document_id or path.stem

        pages: list[PageContent] = []

        try:
            pdf = fitz.open(str(path))
        except Exception as exc:
            raise ValueError(f"Could not open PDF '{path}': {exc}") from exc

        with pdf:
            total_pages = pdf.page_count
            for page_index in range(total_pages):
                page = pdf[page_index]
                page_number = page_index + 1  # convert to 1-based

                # Extract text – "text" mode gives plain UTF-8 output
                raw_text = page.get_text("text")
                raw_text = self._clean_text(raw_text)

                headings = (
                    _detect_headings(raw_text) if self.detect_headings else []
                )

                pages.append(
                    PageContent(
                        page_number=page_number,
                        raw_text=raw_text,
                        headings=headings,
                    )
                )

        return ParsedDocument(
            document_id=doc_id,
            document_name=doc_name,
            file_path=str(path.resolve()),
            total_pages=total_pages,
            pages=pages,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Light normalisation:
          - Remove null bytes and form-feeds.
          - Collapse runs of more than two blank lines.
          - Strip trailing whitespace from each line.
        """
        text = text.replace("\x00", "").replace("\f", "\n")
        text = "\n".join(line.rstrip() for line in text.splitlines())
        # Collapse 3+ consecutive blank lines into 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def parse_pdf(
    file_path: str | Path,
    document_id: Optional[str] = None,
) -> ParsedDocument:
    """
    Module-level shortcut for one-off parsing.

    Example::

        from services.rag.document_parser import parse_pdf


        doc = parse_pdf("contracts/Lease_Agreement_2024.pdf")
        print(doc.total_pages)
        print(doc.pages[0].headings)
    """
    return DocumentParser().parse(file_path, document_id=document_id)

