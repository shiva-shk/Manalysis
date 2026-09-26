"""Validate manually entered or uploaded market-data rows before storage.

Market figures are never scraped from paywalled reports — an analyst
either uploads a licensed export or types the figure in, with its source
and a confidence rating, so the number's provenance is never lost.

`region` and `country` are kept as separate fields on purpose: a "MENA"
regional figure and an "Iran" country-specific figure describe different
things even when they're about the same underlying market, and merging
them into one free-text field would make it impossible to tell later
which level a given row actually reports at. `scope_level` makes that
level explicit rather than inferred from which fields happen to be filled.
"""

from datetime import datetime, timezone

from processing.taxonomy import MARKET_SCOPE_LEVELS

REQUIRED_FIELDS = ["category", "source", "scope_level"]

OPTIONAL_FIELDS = [
    "subcategory", "region", "country", "year", "market_value", "currency",
    "volume", "market_share", "growth_rate", "forecast_year", "source_url",
    "definition", "confidence_score",
]

ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


def _is_missing(value) -> bool:
    """True for None, empty string, or pandas' float NaN — which plain
    `not value` doesn't catch, since NaN is truthy. A CSV/Excel upload's
    blank cells become NaN once read into a DataFrame, so without this a
    blank required field would silently pass validation."""
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN != NaN
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def validate_row(row: dict) -> list[str]:
    """Returns a list of validation error messages; empty means valid."""
    errors = []
    for field in REQUIRED_FIELDS:
        if _is_missing(row.get(field)):
            errors.append(f"'{field}' is required")

    scope_level = row.get("scope_level")
    if scope_level and scope_level not in MARKET_SCOPE_LEVELS:
        errors.append(f"'scope_level' must be one of {MARKET_SCOPE_LEVELS}")
    if scope_level == "country" and _is_missing(row.get("country")):
        errors.append("'country' is required when scope_level is 'country'")
    if scope_level == "regional" and _is_missing(row.get("region")):
        errors.append("'region' is required when scope_level is 'regional'")

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
        row = {
            field: (None if _is_missing(record.get(field)) else record.get(field))
            for field in ALL_FIELDS
        }
        errors = validate_row(row)
        if errors:
            all_errors.append(f"Row {i + 1}: {'; '.join(errors)}")
            continue
        row["uploaded_at"] = datetime.now(timezone.utc).isoformat()
        valid_rows.append(row)

    return valid_rows, all_errors
