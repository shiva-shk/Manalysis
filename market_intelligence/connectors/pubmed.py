"""PubMed connector via the Europe PMC REST API (no API key required).

Docs: https://europepmc.org/RestfulWebService
"""

import requests

from config import DEFAULT_PAGE_SIZE, DEFAULT_TIMEOUT
from connectors.base import ConnectorError, SearchResult

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def search_pubmed(query: str, page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size,
        "resultType": "core",
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"PubMed/Europe PMC request failed: {exc}") from exc
    return response.json()


def normalize_pubmed(raw: dict) -> list[SearchResult]:
    results = []
    for entry in raw.get("resultList", {}).get("result", []):
        pmid = entry.get("pmid")
        doi = entry.get("doi")
        source_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else (
            f"https://doi.org/{doi}" if doi else BASE_URL
        )

        results.append(
            SearchResult(
                title=entry.get("title", "Untitled publication"),
                entity_type="publication",
                entity_name=None,
                company=entry.get("authorString"),
                country=None,
                category=entry.get("pubType"),
                regulatory_status=None,
                summary=entry.get("abstractText", "")[:500] or None,
                identifier=pmid or doi,
                source_name="PubMed / Europe PMC",
                source_url=source_url,
                source_type="scientific",
            )
        )
    return results
