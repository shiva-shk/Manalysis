"""openFDA connector for 510(k) device clearances and drug labels.

Docs: https://open.fda.gov/apis/
"""

import requests

from config import DEFAULT_TIMEOUT
from connectors.base import ConnectorError, SearchResult

DEVICE_URL = "https://api.fda.gov/device/510k.json"
DRUG_LABEL_URL = "https://api.fda.gov/drug/label.json"


def _get(url: str, search: str, limit: int) -> dict:
    params = {"search": search, "limit": limit}
    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"openFDA request failed: {exc}") from exc
    return response.json()


def search_openfda_devices(query: str, limit: int = 20) -> dict:
    return _get(DEVICE_URL, f"device_name:{query}", limit)


def search_openfda_drug_labels(query: str, limit: int = 20) -> dict:
    return _get(DRUG_LABEL_URL, f"openfda.brand_name:{query}", limit)


def normalize_openfda_devices(raw: dict) -> list[SearchResult]:
    results = []
    for record in raw.get("results", []):
        k_number = record.get("k_number", "")
        results.append(
            SearchResult(
                title=record.get("device_name", "Unnamed device"),
                entity_type="medical_device",
                entity_name=record.get("device_name"),
                company=record.get("applicant"),
                country="United States",
                category=record.get("product_code"),
                regulatory_status=f"FDA 510(k) {record.get('decision_description', '')}".strip(),
                summary=record.get("statement_or_summary"),
                identifier=k_number,
                source_name="openFDA (510k devices)",
                source_url=f"https://api.fda.gov/device/510k.json?search=k_number:{k_number}" if k_number else DEVICE_URL,
                source_type="official",
            )
        )
    return results


def normalize_openfda_drug_labels(raw: dict) -> list[SearchResult]:
    results = []
    for record in raw.get("results", []):
        openfda = record.get("openfda", {})
        brand_names = openfda.get("brand_name", [])
        manufacturers = openfda.get("manufacturer_name", [])
        title = brand_names[0] if brand_names else "Unnamed product"
        indications = record.get("indications_and_usage", [])

        results.append(
            SearchResult(
                title=title,
                entity_type="drug_product",
                entity_name=title,
                company=manufacturers[0] if manufacturers else None,
                country="United States",
                category="medicinal_product",
                regulatory_status="FDA labeled product",
                summary=(indications[0][:500] if indications else None),
                identifier=(openfda.get("application_number", [None])[0]),
                source_name="openFDA (drug labels)",
                source_url=DRUG_LABEL_URL,
                source_type="official",
            )
        )
    return results
