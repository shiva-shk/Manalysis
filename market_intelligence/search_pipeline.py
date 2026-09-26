"""Ties the connectors and processing steps into one search call.

Query -> classify -> expand synonyms -> call selected connectors ->
normalize -> score -> dedupe -> return.
"""

from connectors.base import ConnectorError, SearchResult
from connectors.clinicaltrials import normalize_clinical_trials, search_clinical_trials
from connectors.dailymed import normalize_dailymed_spls, search_dailymed_spls
from connectors.ema import normalize_ema_medicines, search_ema_medicines
from connectors.eudamed import normalize_eudamed, search_eudamed_devices
from connectors.health_canada import normalize_mdall, search_mdall_devices
from connectors.openfda import (
    normalize_openfda_devices,
    normalize_openfda_drug_labels,
    normalize_openfda_pma,
    normalize_openfda_udi,
    search_openfda_devices,
    search_openfda_drug_labels,
    search_openfda_pma,
    search_openfda_udi,
)
from connectors.patents import normalize_patents, search_patents
from connectors.pubchem import normalize_pubchem, search_pubchem
from connectors.pubmed import normalize_pubmed, search_pubmed
from processing.deduplication import deduplicate
from processing.evidence_scoring import score_result
from processing.query_classifier import classify_query
from processing.synonyms import expand_query


def run_search(
    query: str, sources: list[str], page_size: int = 20
) -> tuple[list[SearchResult], list[str], str]:
    """Returns (deduplicated and scored results, connector warnings, query type)."""
    query_type = classify_query(query)
    search_terms = expand_query(query)
    primary_term = search_terms[0]

    all_results: list[SearchResult] = []
    warnings: list[str] = []

    if "clinicaltrials" in sources:
        try:
            raw = search_clinical_trials(primary_term, page_size=page_size)
            all_results.extend(normalize_clinical_trials(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "pubmed" in sources:
        try:
            raw = search_pubmed(primary_term, page_size=page_size)
            all_results.extend(normalize_pubmed(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "openfda_device" in sources:
        try:
            raw = search_openfda_devices(primary_term, limit=page_size)
            all_results.extend(normalize_openfda_devices(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "openfda_drug" in sources:
        try:
            raw = search_openfda_drug_labels(primary_term, limit=page_size)
            all_results.extend(normalize_openfda_drug_labels(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "openfda_pma" in sources:
        try:
            raw = search_openfda_pma(primary_term, limit=page_size)
            all_results.extend(normalize_openfda_pma(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "openfda_udi" in sources:
        try:
            raw = search_openfda_udi(primary_term, limit=page_size)
            all_results.extend(normalize_openfda_udi(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "dailymed" in sources:
        try:
            raw = search_dailymed_spls(primary_term, page_size=page_size)
            all_results.extend(normalize_dailymed_spls(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "ema" in sources:
        try:
            raw = search_ema_medicines(primary_term, limit=page_size)
            all_results.extend(normalize_ema_medicines(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "pubchem" in sources:
        try:
            raw = search_pubchem(primary_term)
            all_results.extend(normalize_pubchem(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "patents" in sources:
        try:
            raw = search_patents(primary_term, limit=page_size)
            all_results.extend(normalize_patents(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "eudamed" in sources:
        try:
            raw = search_eudamed_devices(primary_term, page_size=page_size)
            all_results.extend(normalize_eudamed(raw))
        except ConnectorError as exc:
            warnings.append(str(exc))

    if "health_canada" in sources:
        try:
            html = search_mdall_devices(primary_term)
            all_results.extend(normalize_mdall(html)[:page_size])
        except ConnectorError as exc:
            warnings.append(str(exc))

    for result in all_results:
        score_result(result)

    deduped = deduplicate(all_results)
    deduped.sort(key=lambda r: r.evidence_score, reverse=True)

    return deduped, warnings, query_type
