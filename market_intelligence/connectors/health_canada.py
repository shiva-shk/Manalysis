"""Health Canada Medical Devices Active Licence Listing (MDALL) connector.

MDALL has no public API — this drives the same search form a person uses
at health-products.canada.ca/mdall-limh, since it's a plain server-rendered
government site with no anti-bot measures encountered so far (no robots.txt
disallow, no CAPTCHA). It needs a session cookie and a CSRF token pulled
from the search page before the actual POST, since Spring Security ties
the token to that session.

Health Canada also publishes bulk data extracts for MDALL, which is the
more resilient option for anything beyond ad hoc lookups — see
https://www.canada.ca/en/health-canada/services/drugs-health-products/md/... .
"""

import re
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_TIMEOUT
from connectors.base import ConnectorError, SearchResult

BASE_URL = "https://health-products.canada.ca/mdall-limh"
PREPARE_URL = f"{BASE_URL}/prepareSearch"
SEARCH_URL = f"{BASE_URL}/search"

# Values the MDALL search form uses for its "option" radio group.
SEARCH_OPTIONS = {
    "company": "0",
    "licence": "1",
    "device": "2",
    "companyId": "3",
    "licenceId": "4",
    "deviceId": "5",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def search_mdall_devices(query: str, licence_type: str = "active") -> str:
    """Returns the raw results-page HTML for a device-name search."""
    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        prepare_response = session.get(
            PREPARE_URL, params={"type": licence_type}, timeout=DEFAULT_TIMEOUT
        )
        prepare_response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"Health Canada MDALL request failed: {exc}") from exc

    soup = BeautifulSoup(prepare_response.text, "html.parser")
    csrf_input = soup.find("input", attrs={"name": "_csrf"})
    if not csrf_input or not csrf_input.get("value"):
        raise ConnectorError("Health Canada MDALL: could not find a CSRF token on the search page.")

    try:
        search_response = session.post(
            SEARCH_URL,
            data={
                "_csrf": csrf_input["value"],
                "option": SEARCH_OPTIONS["device"],
                "name": query,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        search_response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"Health Canada MDALL search failed: {exc}") from exc

    return search_response.text


def _query_param(href: str, key: str) -> str | None:
    return (parse_qs(urlparse(href).query).get(key) or [None])[0]


def normalize_mdall(html: str) -> list[SearchResult]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="results")
    results = []

    if not table:
        return results

    for row in table.find_all("tr"):
        cell = row.find("td")
        if not cell:
            continue

        links = cell.find_all("a")
        if not links:
            continue

        device_link = links[0]
        device_name = device_link.get_text(strip=True)
        device_id = _query_param(device_link.get("href", ""), "deviceId")
        licence_id = _query_param(device_link.get("href", ""), "licenceId")

        company_link = links[1] if len(links) > 1 else None
        company_name = company_link.get_text(strip=True) if company_link else None

        licence_match = re.search(r"Licence No\.:\s*(\S+)", cell.get_text(" ", strip=True))
        licence_number = licence_match.group(1) if licence_match else licence_id

        address_spans = []
        if company_link:
            for sibling in company_link.find_next_siblings("span"):
                text = sibling.get_text(strip=True)
                if text:
                    address_spans.append(text)
        address = ", ".join(address_spans) or None

        # The last address line is "City, Province/State, Country, Postal code".
        country = None
        if address_spans:
            parts = [p.strip() for p in address_spans[-1].split(",")]
            if len(parts) >= 2:
                country = parts[-2]

        results.append(
            SearchResult(
                title=device_name,
                entity_type="medical_device",
                entity_name=device_name,
                company=company_name,
                country=country,
                category="medical_device",
                regulatory_status="Health Canada active licence",
                summary=address,
                identifier=licence_number,
                source_name="Health Canada MDALL",
                source_url=(
                    f"{BASE_URL}/information?deviceId={device_id}&licenceId={licence_id}&type=active&lang=eng"
                    if device_id else SEARCH_URL
                ),
                source_type="official",
            )
        )
    return results
