"""ClinicalTrials.gov v2 API connector.

Docs: https://clinicaltrials.gov/data-api/api
"""

import requests

from config import DEFAULT_PAGE_SIZE, DEFAULT_TIMEOUT
from connectors.base import ConnectorError, SearchResult

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


def search_clinical_trials(query: str, page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    params = {
        "query.term": query,
        "pageSize": page_size,
        "format": "json",
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"ClinicalTrials.gov request failed: {exc}") from exc

    return response.json()


def _extract_countries(protocol: dict) -> str:
    locations = (
        protocol.get("contactsLocationsModule", {}).get("locations", []) or []
    )
    countries = sorted({loc.get("country") for loc in locations if loc.get("country")})
    return ", ".join(countries)


def normalize_clinical_trials(raw: dict) -> list[SearchResult]:
    results = []
    for study in raw.get("studies", []):
        protocol = study.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        design_module = protocol.get("designModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        arms_module = protocol.get("armsInterventionsModule", {})

        nct_id = identification.get("nctId", "")
        title = identification.get("briefTitle", "Untitled study")
        sponsor = sponsor_module.get("leadSponsor", {}).get("name")
        interventions = ", ".join(
            i.get("name", "") for i in arms_module.get("interventions", [])
        )
        conditions = ", ".join(conditions_module.get("conditions", []))
        sample_size = design_module.get("enrollmentInfo", {}).get("count")

        summary_parts = [p for p in [
            f"Condition: {conditions}" if conditions else None,
            f"Intervention: {interventions}" if interventions else None,
            f"Sample size: {sample_size}" if sample_size else None,
        ] if p]

        results.append(
            SearchResult(
                title=title,
                entity_type="clinical_study",
                entity_name=interventions or None,
                company=sponsor,
                country=_extract_countries(protocol) or None,
                category="clinical_trial",
                regulatory_status=status_module.get("overallStatus"),
                summary="; ".join(summary_parts) or None,
                identifier=nct_id,
                source_name="ClinicalTrials.gov",
                source_url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else BASE_URL,
                source_type="official",
            )
        )
    return results
