import io

from reportlab.pdfgen import canvas

from processing.document_ingest import extract_pdf_pages, find_mentions, ingest_pdf


def _make_pdf_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def test_extract_pdf_pages_returns_text():
    pdf_bytes = _make_pdf_bytes("Contains hyaluronic acid and is made by Galderma")
    pages = extract_pdf_pages(pdf_bytes)
    assert len(pages) == 1
    assert "hyaluronic" in pages[0]["text"].lower()


def test_find_mentions_detects_ingredient_and_company():
    mentions = find_mentions("This product contains hyaluronic acid and is made by galderma")
    assert "hyaluronic acid" in mentions["ingredients"]
    assert "galderma" in mentions["companies"]


def test_ingest_pdf_produces_citable_records():
    pdf_bytes = _make_pdf_bytes("Contains pdrn, manufactured by merz")
    records = ingest_pdf(pdf_bytes, "brochure.pdf")
    assert len(records) == 1
    assert records[0]["file_name"] == "brochure.pdf"
    assert records[0]["page_number"] == 1
    assert "pdrn" in (records[0]["ingredient_mentions"] or "")


def test_ingest_pdf_tags_known_supplier_not_in_company_terms():
    pdf_bytes = _make_pdf_bytes("Certificate of Analysis")
    records = ingest_pdf(pdf_bytes, "coa.pdf", source_type="supplier_technical",
                          known_supplier="Acme Raw Materials Ltd")
    assert "Acme Raw Materials Ltd" in records[0]["company_mentions"]


def test_ingest_pdf_known_supplier_not_duplicated_if_already_detected():
    pdf_bytes = _make_pdf_bytes("Manufactured by galderma")
    records = ingest_pdf(pdf_bytes, "spec.pdf", known_supplier="galderma")
    assert records[0]["company_mentions"].count("galderma") == 1


def test_ingest_pdf_without_known_supplier_unchanged():
    pdf_bytes = _make_pdf_bytes("Manufactured by merz")
    records = ingest_pdf(pdf_bytes, "spec.pdf")
    assert records[0]["company_mentions"] == "merz"
