"""EPO Open Patent Services (OPS) connector.

Docs: https://www.epo.org/en/searching-for-patents/data/web-services/ops

OPS requires a free registered consumer key/secret (client-credentials
OAuth2), read from EPO_OPS_CONSUMER_KEY / EPO_OPS_CONSUMER_SECRET. When
those aren't set, or the host isn't reachable from this environment,
search_patents raises ConnectorError with a message the UI can show
instead of a stack trace.
"""

import os
import xml.etree.ElementTree as ET

import requests

from config import DEFAULT_TIMEOUT
from connectors.base import ConnectorError, SearchResult

TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search"
NS = {"ops": "http://ops.epo.org", "ex": "http://www.epo.org/exchange"}


def _get_access_token() -> str:
    key = os.environ.get("EPO_OPS_CONSUMER_KEY")
    secret = os.environ.get("EPO_OPS_CONSUMER_SECRET")
    if not key or not secret:
        raise ConnectorError(
            "EPO OPS is not configured: set EPO_OPS_CONSUMER_KEY and "
            "EPO_OPS_CONSUMER_SECRET (free registration at "
            "https://developers.epo.org) to enable patent search."
        )

    try:
        response = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(key, secret),
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"EPO OPS authentication failed: {exc}") from exc

    return response.json()["access_token"]


def search_patents(query: str, limit: int = 20) -> str:
    """Returns raw OPS XML for a title/abstract keyword search."""
    token = _get_access_token()
    cql = f'ti="{query}" or ab="{query}"'
    params = {"q": cql, "Range": f"1-{limit}"}
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"EPO OPS search failed: {exc}") from exc

    return response.text


def normalize_patents(raw_xml: str) -> list[SearchResult]:
    root = ET.fromstring(raw_xml)
    results = []

    for doc in root.findall(".//ex:exchange-document", NS):
        country = doc.get("country", "")
        doc_number = doc.get("doc-number", "")
        kind = doc.get("kind", "")
        patent_number = f"{country}{doc_number}{kind}"

        title_el = doc.find(".//ex:invention-title[@lang='en']", NS)
        title = title_el.text if title_el is not None else f"Patent {patent_number}"

        applicant_el = doc.find(".//ex:applicant//ex:name", NS)
        applicant = applicant_el.text if applicant_el is not None else None

        date_el = doc.find(".//ex:publication-reference//ex:date", NS)
        pub_date = date_el.text if date_el is not None else None

        results.append(
            SearchResult(
                title=title,
                entity_type="patent",
                entity_name=title,
                company=applicant,
                country=country or None,
                category="patent",
                regulatory_status=f"Published {pub_date}" if pub_date else None,
                summary=None,
                identifier=patent_number,
                source_name="EPO Open Patent Services",
                source_url=f"https://worldwide.espacenet.com/patent/search/family/publication/{patent_number}",
                source_type="official",
            )
        )
    return results
