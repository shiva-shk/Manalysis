"""European Medicines Agency (EMA) connector.

No documented REST search API — this fetches the same bulk JSON export
EMA's own "medicines" search page uses (its full list of centrally
authorised medicines, ~2,700 records) and filters client-side. Not a
per-query endpoint like ClinicalTrials.gov or openFDA, so every search
re-downloads the same file; callers doing more than a few lookups should
cache the raw fetch themselves.

Covers only centrally authorised medicines (the EU-wide procedure) — a
medicine authorised nationally in individual member states won't appear
here even if it's legally on the EU market.
"""

import requests

from config import DEFAULT_TIMEOUT
from connectors.base import ConnectorError, SearchResult

MEDICINES_URL = (
    "https://www.ema.europa.eu/en/documents/report/"
    "medicines-output-medicines_json-report_en.json"
)


def fetch_ema_medicines() -> list[dict]:
    try:
        response = requests.get(
            MEDICINES_URL,
            headers={"Accept": "application/json"},
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"EMA request failed: {exc}") from exc

    data = response.json()
    records = data.get("data") if isinstance(data, dict) else data
    if not isinstance(records, list):
        raise ConnectorError("EMA response did not contain a medicines list")
    return records


def search_ema_medicines(query: str, limit: int = 20) -> list[dict]:
    """Client-side filter over the full medicines list: matches the query
    against medicine name, active substance, or therapeutic area."""
    q = query.lower().strip()
    all_medicines = fetch_ema_medicines()

    matches = [
        m for m in all_medicines
        if q in (m.get("name_of_medicine") or "").lower()
        or q in (m.get("active_substance") or "").lower()
        or q in (m.get("therapeutic_area_mesh") or "").lower()
    ]
    return matches[:limit]


def normalize_ema_medicines(records: list[dict]) -> list[SearchResult]:
    results = []
    for record in records:
        title = record.get("name_of_medicine", "Unnamed medicine")

        results.append(
            SearchResult(
                title=title,
                entity_type="eu_medicine",
                entity_name=title,
                company=record.get("marketing_authorisation_developer_applicant_holder"),
                country="European Union",
                category=record.get("pharmacotherapeutic_group_human"),
                regulatory_status=record.get("medicine_status"),
                summary=(record.get("therapeutic_indication") or "")[:500] or None,
                identifier=record.get("ema_product_number"),
                source_name="EMA (European Medicines Agency)",
                source_url="https://www.ema.europa.eu/en/medicines",
                source_type="official",
            )
        )
    return results
