"""Validate manually entered or uploaded market-data rows before storage.

Market figures are never scraped from paywalled reports — an analyst
either uploads a licensed export or types the figure in, with its source
and a confidence rating, so the number's provenance is never lost.
"""

from datetime import datetime, timezone

REQUIRED_FIELDS = ["category", "source"]

OPTIONAL_FIELDS = [
    "subcategory", "region", "year", "market_value", "currency", "volume",
    "market_share", "growth_rate", "forecast_year", "source_url",
    "definition", "confidence_score",
]

ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


def validate_row(row: dict) -> list[str]:
    """Returns a list of validation error messages; empty means valid."""
    errors = []
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            errors.append(f"'{field}' is required")

    confidence = row.get("confidence_score")
    if confidence not in (None, ""):
        try:
            value = float(confidence)
            if not 0 <= value <= 1:
                errors.append("'confidence_score' must be between 0 and 1")
        except (TypeError, ValueError):
            errors.append("'confidence_score' must be numeric")

    return errors


def prepare_rows(records: list[dict]) -> tuple[list[dict], list[str]]:
    """Validate a batch of records, returning (valid rows with timestamp
    added, error messages for rejected rows)."""
    valid_rows = []
    all_errors = []

    for i, record in enumerate(records):
        row = {field: record.get(field) for field in ALL_FIELDS}
        errors = validate_row(row)
        if errors:
            all_errors.append(f"Row {i + 1}: {'; '.join(errors)}")
            continue
        row["uploaded_at"] = datetime.now(timezone.utc).isoformat()
        valid_rows.append(row)

    return valid_rows, all_errors
