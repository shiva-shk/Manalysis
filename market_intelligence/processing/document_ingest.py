"""Extract text from uploaded PDFs and tag pages with product/company/
ingredient mentions, keeping the file name and page number as citation.

Full document-understanding (tables, OCR for scans) is a later phase;
this covers the common case of a text-based brochure, IFU, or regulatory
letter.
"""

import io
from datetime import datetime, timezone

from pypdf import PdfReader

from processing.ingredient_dictionary import INGREDIENTS
from processing.query_classifier import COMPANY_TERMS


def extract_pdf_pages(file_bytes: bytes) -> list[dict]:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page_number": i, "text": text})
    return pages


def find_mentions(text: str) -> dict:
    lower = text.lower()
    ingredient_hits = [key for key in INGREDIENTS if key in lower]
    company_hits = [term for term in COMPANY_TERMS if term in lower]
    return {"ingredients": ingredient_hits, "companies": company_hits}


def ingest_pdf(file_bytes: bytes, file_name: str, source_type: str = "manufacturer",
               confidence: float = 0.6) -> list[dict]:
    """Returns one record per page, ready for database storage."""
    records = []
    for page in extract_pdf_pages(file_bytes):
        mentions = find_mentions(page["text"])
        records.append({
            "file_name": file_name,
            "page_number": page["page_number"],
            "extracted_text": page["text"][:5000],
            "ingredient_mentions": ", ".join(mentions["ingredients"]) or None,
            "company_mentions": ", ".join(mentions["companies"]) or None,
            "source_type": source_type,
            "confidence": confidence,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        })
    return records
