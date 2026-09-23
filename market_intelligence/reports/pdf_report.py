"""One-page PDF summary of a search run, built with reportlab."""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

MAX_ROWS = 25


def build_pdf_report(rows: list[dict], summary: dict, query: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"{query} — Intelligence Report")
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Medical Product Intelligence Report: {query}", styles["Title"]))
    story.append(Spacer(1, 0.15 * inch))

    summary_lines = [
        f"Total results: {summary.get('total_results', 0)}",
        f"Distinct companies: {summary.get('companies', 0)}",
        f"Distinct countries: {summary.get('countries', 0)}",
        f"Average evidence score: {summary.get('avg_evidence_score', 0)}",
    ]
    for line in summary_lines:
        story.append(Paragraph(line, styles["Normal"]))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Top results", styles["Heading2"]))

    table_data = [["Title", "Company", "Country", "Source", "Score"]]
    for row in rows[:MAX_ROWS]:
        table_data.append([
            (row.get("title") or "")[:60],
            (row.get("company") or "")[:30],
            row.get("country") or "",
            row.get("source_name") or "",
            row.get("evidence_score") if row.get("evidence_score") is not None else "",
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "Evidence scores reflect source reliability and record completeness, not "
        "market share or clinical significance. FDA-cleared, CE-marked, and "
        "registered are distinct regulatory statuses.",
        styles["Italic"],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
