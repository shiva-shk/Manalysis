"""openFDA connector for 510(k) device clearances, drug labels, PMA
(premarket approval) records, and UDI/GUDID device identifiers.

Docs: https://open.fda.gov/apis/

PMA and UDI fill a real gap 510(k) doesn't cover: 510(k) is the clearance
pathway for lower-risk devices found "substantially equivalent" to one
already on the market, while PMA is the approval pathway for higher-risk
(Class III) devices — dermal fillers among them, several of which are
PMA-approved rather than 510(k)-cleared. UDI/GUDID gives the device
identifier record independent of which pathway a device went through.
"""

import requests

from config import DEFAULT_TIMEOUT
from connectors.base import ConnectorError, SearchResult

DEVICE_URL = "https://api.fda.gov/device/510k.json"
DRUG_LABEL_URL = "https://api.fda.gov/drug/label.json"
PMA_URL = "https://api.fda.gov/device/pma.json"
UDI_URL = "https://api.fda.gov/device/udi.json"
RECALL_URL = "https://api.fda.gov/device/recall.json"
MAUDE_URL = "https://api.fda.gov/device/event.json"


def _quote(query: str) -> str:
    """Wraps a query in double quotes for openFDA's Lucene-style search
    syntax, so a multi-word product name is matched as one phrase rather
    than OR'd word-by-word — unquoted, "Rejuran Healer" would match any
    record containing "Rejuran" OR "Healer" alone (e.g. unrelated devices
    with "Healer" in the name)."""
    return f'"{query.replace(chr(34), "")}"'


def _get(url: str, search: str, limit: int) -> dict:
    params = {"search": search, "limit": limit}
    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        if response.status_code == 404:
            # openFDA returns 404 for a search with zero matching records —
            # documented behavior, not a real error.
            return {"results": []}
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"openFDA request failed: {exc}") from exc
    return response.json()


def search_openfda_devices(query: str, limit: int = 20) -> dict:
    return _get(DEVICE_URL, f"device_name:{_quote(query)}", limit)


def search_openfda_drug_labels(query: str, limit: int = 20) -> dict:
    return _get(DRUG_LABEL_URL, f"openfda.brand_name:{_quote(query)}", limit)


def search_openfda_pma(query: str, limit: int = 20) -> dict:
    return _get(PMA_URL, f"trade_name:{_quote(query)}", limit)


def search_openfda_udi(query: str, limit: int = 20) -> dict:
    return _get(UDI_URL, f"brand_name:{_quote(query)}", limit)


def search_openfda_recalls(query: str, limit: int = 20) -> dict:
    return _get(RECALL_URL, f"product_description:{_quote(query)}", limit)


def search_openfda_maude(query: str, limit: int = 20) -> dict:
    return _get(MAUDE_URL, f"device.generic_name:{_quote(query)}", limit)


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


def normalize_openfda_pma(raw: dict) -> list[SearchResult]:
    results = []
    for record in raw.get("results", []):
        pma_number = record.get("pma_number", "")
        supplement = record.get("supplement_number")
        identifier = f"{pma_number}{'/' + supplement if supplement else ''}"

        results.append(
            SearchResult(
                title=record.get("trade_name", "Unnamed device"),
                entity_type="medical_device",
                entity_name=record.get("trade_name"),
                company=record.get("applicant"),
                country="United States",
                category=record.get("product_code"),
                regulatory_status=f"FDA PMA {record.get('decision_code', '')}".strip(),
                summary=record.get("ao_statement"),
                identifier=identifier or None,
                source_name="openFDA (PMA devices)",
                source_url=f"https://api.fda.gov/device/pma.json?search=pma_number:{pma_number}" if pma_number else PMA_URL,
                source_type="official",
            )
        )
    return results


def normalize_openfda_udi(raw: dict) -> list[SearchResult]:
    results = []
    for record in raw.get("results", []):
        identifiers = record.get("identifiers", [])
        di = identifiers[0].get("id") if identifiers else None
        product_codes = record.get("product_codes", [])
        category = product_codes[0].get("name") if product_codes else None

        results.append(
            SearchResult(
                title=record.get("brand_name", "Unnamed device"),
                entity_type="medical_device",
                entity_name=record.get("brand_name"),
                company=record.get("company_name"),
                country="United States",
                category=category,
                regulatory_status=record.get("commercial_distribution_status"),
                summary=None,
                identifier=di,
                source_name="openFDA (UDI/GUDID)",
                source_url=f"https://api.fda.gov/device/udi.json?search=identifiers.id:{di}" if di else UDI_URL,
                source_type="official",
            )
        )
    return results


def normalize_openfda_recalls(raw: dict) -> list[SearchResult]:
    results = []
    for record in raw.get("results", []):
        results.append(
            SearchResult(
                title=record.get("recalling_firm", "Unnamed recall"),
                entity_type="safety_signal",
                entity_name=(record.get("product_description") or "")[:200] or None,
                company=record.get("recalling_firm"),
                country="United States",
                category=record.get("product_code"),
                regulatory_status=f"Recall {record.get('recall_status', '')}".strip(),
                summary=record.get("reason_for_recall"),
                identifier=record.get("product_res_number"),
                source_name="openFDA (device recalls)",
                source_url="https://api.fda.gov/device/recall.json",
                source_type="official",
            )
        )
    return results


def normalize_openfda_maude(raw: dict) -> list[SearchResult]:
    results = []
    for record in raw.get("results", []):
        devices = record.get("device", [])
        device = devices[0] if devices else {}
        brand_name = device.get("brand_name") or device.get("generic_name") or "Unnamed device"

        texts = record.get("mdr_text", [])
        description = next(
            (t.get("text") for t in texts if t.get("text_type_code") == "Description of Event or Problem"),
            (texts[0].get("text") if texts else None),
        )

        results.append(
            SearchResult(
                title=brand_name,
                entity_type="safety_signal",
                entity_name=device.get("generic_name"),
                company=device.get("manufacturer_d_name"),
                country="United States",
                category=device.get("device_report_product_code"),
                regulatory_status=record.get("event_type"),
                summary=(description or "")[:500] or None,
                identifier=record.get("report_number"),
                source_name="openFDA (MAUDE adverse events)",
                source_url="https://api.fda.gov/device/event.json",
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
