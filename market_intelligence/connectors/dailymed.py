"""DailyMed connector — NLM's official database of FDA structured
product labels (SPLs), documented at
https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm

Complements the openFDA drug-label connector: DailyMed's SPL search
covers both prescription and OTC products and gives the raw SPL set ID
that links back to the full label, which openFDA's label endpoint
doesn't expose in the same form.
"""

import re

import requests

from config import DEFAULT_TIMEOUT
from connectors.base import ConnectorError, SearchResult

BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
SPLS_URL = f"{BASE_URL}/spls.json"

# DailyMed SPL titles follow "BRAND (GENERIC) FORM [MANUFACTURER]" —
# not a documented format, just an observed convention, so extraction
# falls back to leaving manufacturer unset rather than guessing.
_MANUFACTURER_RE = re.compile(r"\[([^\]]+)\]\s*$")


def search_dailymed_spls(query: str, page_size: int = 20) -> dict:
    params = {"drug_name": query, "pagesize": page_size}
    try:
        response = requests.get(SPLS_URL, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"DailyMed request failed: {exc}") from exc
    return response.json()


def normalize_dailymed_spls(raw: dict) -> list[SearchResult]:
    results = []
    for record in raw.get("data", []):
        title = record.get("title", "Unnamed product")
        set_id = record.get("setid")
        manufacturer_match = _MANUFACTURER_RE.search(title)

        results.append(
            SearchResult(
                title=title.split(" [")[0].strip() if manufacturer_match else title,
                entity_type="drug_product",
                entity_name=title,
                company=manufacturer_match.group(1) if manufacturer_match else None,
                country="United States",
                category="structured_product_label",
                regulatory_status=f"SPL published {record.get('published_date', '')}".strip(),
                summary=None,
                identifier=set_id,
                source_name="DailyMed",
                source_url=f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}" if set_id else SPLS_URL,
                source_type="official",
            )
        )
    return results
