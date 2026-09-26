"""Promotes a cluster of raw search_results rows into the verified
product/company registry, recording where every promoted field came
from. This is the one place raw/normalized data is allowed to become a
registry record — nothing else writes to products/companies/ingredients.

Matches the four-stage model: raw data -> normalized data -> verified
evidence -> analyst interpretation. A promotion is the analyst's act of
saying "yes, this cluster is one real product," which is a judgment call
the system should never make silently.
"""

from collections import Counter

from analysis.product_matching import match_decision, product_match_score
from config import DB_PATH
from database.registry_db import (
    add_clinical_study,
    add_field_evidence,
    add_product_alias,
    add_regulatory_record,
    add_safety_signal,
    clinical_study_exists,
    create_product,
    fetch_product_companies,
    fetch_products,
    fetch_regulatory_records,
    link_product_company,
    log_audit_event,
    upsert_company,
    upsert_patent,
)
from processing.query_normalizer import normalize_query

REGULATORY_ENTITY_TYPES = {"medical_device", "drug_product", "eu_medicine"}
CLINICAL_ENTITY_TYPES = {"clinical_study"}
PATENT_ENTITY_TYPES = {"patent"}
SAFETY_ENTITY_TYPES = {"safety_signal"}


def _cluster_match_fields(canonical_name: str, members: list[dict]) -> dict:
    manufacturer = Counter(m["company"] for m in members if m.get("company")).most_common(1)
    regulatory_number = next(
        (m.get("identifier") for m in members
         if m.get("entity_type") in REGULATORY_ENTITY_TYPES and m.get("identifier")),
        None,
    )
    country = Counter(m["country"] for m in members if m.get("country")).most_common(1)

    return {
        "normalized_name": normalize_query(canonical_name),
        "manufacturer": manufacturer[0][0] if manufacturer else None,
        "regulatory_number": regulatory_number,
        "product_family": None,
        "country": country[0][0] if country else None,
    }


def _existing_product_match_fields(product: dict, db_path: str) -> dict:
    companies = fetch_product_companies(product["id"], db_path=db_path)
    manufacturer = companies[0]["company_name"] if companies else None
    records = fetch_regulatory_records(product["id"], db_path=db_path)
    regulatory_number = records[0]["registration_number"] if records else None

    return {
        "normalized_name": normalize_query(product["canonical_name"]),
        "manufacturer": manufacturer,
        "regulatory_number": regulatory_number,
        "product_family": product.get("product_family"),
        "country": product.get("country_of_origin"),
    }


def check_for_duplicate(canonical_name: str, members: list[dict], db_path: str = DB_PATH) -> dict | None:
    """Compares a cluster about to be promoted against every already-
    promoted product using the weighted product_match_score (structured
    fields — name, manufacturer, regulatory number, family, country —
    not name similarity alone). Returns the best match if its score
    reaches at least the analyst-review threshold, else None. This never
    blocks or auto-merges a promotion — it's advisory, so an analyst can
    see "this might already be in the registry" before creating a
    duplicate, then decide.
    """
    candidate = _cluster_match_fields(canonical_name, members)
    best = None

    for product in fetch_products(db_path=db_path):
        existing = _existing_product_match_fields(dict(product), db_path)
        score = product_match_score(candidate, existing)
        if best is None or score > best["score"]:
            best = {
                "product_id": product["id"], "product_name": product["canonical_name"],
                "score": score, "decision": match_decision(score),
            }

    if best and best["decision"] != "no_match":
        return best
    return None


def promote_cluster(canonical_name: str, members: list[dict], analyst: str = "unattributed",
                     product_type: str | None = None, regulatory_category: str = "unknown",
                     db_path: str = DB_PATH) -> int:
    """Creates a product record from a cluster's member rows, an alias
    for every distinct raw title seen, a company link for every distinct
    company (role defaults to brand_owner since search results don't
    distinguish applicant/manufacturer/distributor), and a regulatory
    record for every member that came from a regulatory-tier source.
    Returns the new product_id.
    """
    if not members:
        raise ValueError("Cannot promote an empty cluster — nothing to attach evidence to.")

    best = max(members, key=lambda r: r.get("evidence_score") or 0)
    product_id = create_product(
        canonical_name,
        db_path=db_path,
        brand_name=best.get("title"),
        product_type=product_type,
        regulatory_category=regulatory_category,
        country_of_origin=best.get("country"),
        status="awaiting_review",
        identity_confidence=round(sum(m.get("evidence_score") or 0 for m in members) / len(members), 2),
    )

    seen_titles = set()
    seen_companies: dict[str, int] = {}

    for member in members:
        title = member.get("title")
        if title and title not in seen_titles:
            seen_titles.add(title)
            add_product_alias(
                product_id, title,
                db_path=db_path,
                alias_type="product_name",
                source=member.get("source_name"),
                source_url=member.get("source_url"),
                verified=0,
            )

        company_name = member.get("company")
        if company_name and company_name not in seen_companies:
            company_id = upsert_company(company_name, db_path=db_path, verification_status="awaiting_review")
            seen_companies[company_name] = company_id
            link_product_company(
                product_id, company_id, role="brand_owner",
                db_path=db_path,
                country=member.get("country"),
                source_url=member.get("source_url"),
                confidence=member.get("evidence_score"),
            )

        if member.get("entity_type") in REGULATORY_ENTITY_TYPES:
            add_regulatory_record(
                product_id, jurisdiction=_infer_jurisdiction(member),
                db_path=db_path,
                authority=member.get("source_name"),
                classification=member.get("category"),
                registration_number=member.get("identifier"),
                status=member.get("regulatory_status"),
                source_url=member.get("source_url"),
                source_type=member.get("source_type"),
            )

        if member.get("entity_type") in CLINICAL_ENTITY_TYPES:
            registry_id = member.get("identifier")
            if not registry_id or not clinical_study_exists(registry_id, db_path=db_path):
                add_clinical_study(
                    member.get("title") or "Untitled study",
                    db_path=db_path,
                    product_id=product_id,
                    registry_name=member.get("source_name"),
                    registry_id=registry_id,
                    status=member.get("regulatory_status"),
                    intervention=member.get("entity_name"),
                    condition_summary=member.get("summary"),
                    sponsor=member.get("company"),
                    country=member.get("country"),
                    evidence_level="registered_trial",
                    source_url=member.get("source_url"),
                )

        if member.get("entity_type") in SAFETY_ENTITY_TYPES:
            add_safety_signal(
                product_id,
                db_path=db_path,
                jurisdiction=_infer_jurisdiction(member),
                signal_type=member.get("regulatory_status"),
                description=member.get("summary"),
                source_url=member.get("source_url"),
                source_type=member.get("source_type"),
            )

        if member.get("entity_type") in PATENT_ENTITY_TYPES and member.get("identifier"):
            upsert_patent(
                member["identifier"],
                db_path=db_path,
                product_id=product_id,
                jurisdiction=member.get("country"),
                title=member.get("title"),
                applicant=member.get("company"),
                publication_date=member.get("regulatory_status"),
                source_url=member.get("source_url"),
            )

        for field_name in ("title", "company", "country", "regulatory_status", "category"):
            value = member.get(field_name)
            if value:
                add_field_evidence(
                    "product", product_id, field_name,
                    db_path=db_path,
                    field_value=str(value),
                    source_name=member.get("source_name"),
                    source_url=member.get("source_url"),
                    confidence=member.get("evidence_score"),
                    verification_status="machine_extracted",
                    analyst_comment=f"promoted by {analyst}",
                )

    log_audit_event(
        analyst, "promote_cluster", "product", db_path=db_path,
        entity_id=product_id,
        details=f"promoted {len(members)} member row(s) as '{canonical_name}'",
    )

    return product_id


def _infer_jurisdiction(member: dict) -> str:
    source = (member.get("source_name") or "").lower()
    if "fda" in source:
        return "US"
    if "eudamed" in source:
        return "EU"
    if "health canada" in source:
        return "CA"
    if "clinicaltrials" in source:
        return member.get("country") or "unknown"
    return "unknown"


def registry_completeness(product_id: int, db_path: str = DB_PATH) -> dict:
    """A quick sanity check an analyst can run after promoting: does this
    product have any regulatory backing, clinical evidence, or patent
    coverage at all, or is it evidence-free?"""
    from database.registry_db import fetch_clinical_studies, fetch_patents, fetch_safety_signals

    records = fetch_regulatory_records(product_id, db_path=db_path)
    studies = fetch_clinical_studies(product_id, db_path=db_path)
    patents = fetch_patents(product_id, db_path=db_path)
    safety_signals = fetch_safety_signals(product_id, db_path=db_path)
    return {
        "product_id": product_id,
        "regulatory_record_count": len(records),
        "jurisdictions": sorted({r["jurisdiction"] for r in records}),
        "has_any_regulatory_evidence": len(records) > 0,
        "clinical_study_count": len(studies),
        "patent_count": len(patents),
        "safety_signal_count": len(safety_signals),
    }
