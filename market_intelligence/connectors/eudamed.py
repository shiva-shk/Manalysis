"""EUDAMED (EU medical device database) connector.

EUDAMED has no documented public API — this calls the same JSON endpoint
its own Angular frontend uses (found by capturing the network request a
real browser search fires against https://ec.europa.eu/tools/eudamed).
That endpoint isn't a stable contract: it can change or be rate-limited
without notice, and typically takes 10-20+ seconds to respond. Prefer
EUDAMED's official bulk data export (linked from the search page) for
anything beyond ad hoc lookups.
"""

import requests

from connectors.base import ConnectorError, SearchResult

BASE_URL = "https://ec.europa.eu/tools/eudamed/api/devices/udiDiData"
EUDAMED_TIMEOUT = 45

# EUDAMED's gateway rejects the default python-requests user agent (502);
# a browser-like one is required.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def search_eudamed_devices(query: str, page_size: int = 20) -> dict:
    params = {
        "page": 0,
        "pageSize": page_size,
        "size": page_size,
        "iso2Code": "en",
        "languageIso2Code": "en",
        "sort": ["primaryDi,desc", "versionNumber,DESC"],
        "tradeName": query,
        "deviceStatusCode": "refdata.device-model-status.on-the-market",
    }
    try:
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=EUDAMED_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"EUDAMED request failed: {exc}") from exc

    return response.json()


def normalize_eudamed(raw: dict) -> list[SearchResult]:
    results = []
    for record in raw.get("content", []):
        trade_name = record.get("tradeName") or record.get("reference") or "Unnamed device"
        risk_class = (record.get("riskClass") or {}).get("code", "")
        status = (record.get("deviceStatusType") or {}).get("code", "")

        results.append(
            SearchResult(
                title=trade_name,
                entity_type="medical_device",
                entity_name=trade_name,
                company=record.get("manufacturerName"),
                country=None,
                category=risk_class.replace("refdata.risk-class.", "") or None,
                regulatory_status=status.replace("refdata.device-model-status.", "") or None,
                summary=record.get("reference"),
                identifier=record.get("primaryDi") or record.get("uuid"),
                source_name="EUDAMED",
                source_url="https://ec.europa.eu/tools/eudamed/#/screen/search-device",
                source_type="official",
            )
        )
    return results
