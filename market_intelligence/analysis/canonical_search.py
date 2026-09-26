"""Builds the canonical product/brand search response: one structure
combining identity, ownership, composition, regulatory status, clinical
evidence, patents, and market data — with an explicit information_gaps
list rather than silently omitting what wasn't found.

Two modes, chosen by whether `registry_match` is given:

- **Registry-verified**: the query matches an already-promoted product.
  Every field comes from the verified registry tables (companies with
  their actual role and citation, ingredients with declared
  concentration, regulatory/clinical/patent records with real
  identifiers) — this is the "verified" tier of the raw → normalized →
  verified evidence → analyst interpretation pipeline the rest of the
  platform follows.
- **Raw fallback**: nothing's been promoted yet, so the response is
  built from this search's own connector results — companies and
  regulatory/clinical/patent records are grouped by entity_type with no
  claim of a verified role or merge, and confidence is left unset rather
  than invented.

Callers fetch the registry rows themselves (matching the rest of this
codebase's pattern of keeping analysis/ functions DB-agnostic) and pass
them in as `registry_match`.
"""

import pandas as pd

from processing.ingredient_dictionary import lookup_ingredient

REGULATORY_ENTITY_TYPES = ["medical_device", "drug_product", "eu_medicine"]
CLINICAL_ENTITY_TYPES = ["clinical_study"]
PATENT_ENTITY_TYPES = ["patent"]
SAFETY_ENTITY_TYPES = ["safety_signal"]


def _rows_for_entity_types(df: pd.DataFrame, entity_types: list[str]) -> list[dict]:
    if df.empty or "entity_type" not in df.columns:
        return []
    return df[df["entity_type"].isin(entity_types)].to_dict("records")


# PubMed's connector puts its author list in the `company` field (there's
# no better slot in the shared SearchResult schema for "who wrote this") —
# real for a results table with an entity_type column giving context, but
# misleading in a section literally titled "Companies", so publications
# are excluded here specifically.
_COMPANY_FIELD_EXCLUDED_ENTITY_TYPES = {"publication"}


def _raw_companies(raw_results: list[dict]) -> list[dict]:
    seen = {}
    for r in raw_results:
        if r.get("entity_type") in _COMPANY_FIELD_EXCLUDED_ENTITY_TYPES:
            continue
        name = r.get("company")
        if not name or name in seen:
            continue
        seen[name] = {
            "name": name, "role": None, "confidence": None,
            "source": r.get("source_name"),
        }
    return list(seen.values())


def _registry_companies(registry_match: dict) -> list[dict]:
    return [
        {
            "name": c.get("company_name") or c.get("canonical_name"),
            "role": c.get("role"),
            "confidence": c.get("confidence"),
            "source": c.get("source_url") or "Registry (promoted)",
        }
        for c in registry_match.get("companies", [])
    ]


def _registry_ingredients(registry_match: dict) -> list[dict]:
    return [
        {
            "name": i.get("ingredient_name") or i.get("preferred_name") or i.get("declared_name"),
            "role": i.get("ingredient_role"),
            "concentration": i.get("concentration"),
            "confidence": i.get("confidence"),
        }
        for i in registry_match.get("ingredients", [])
    ]


def build_canonical_search_response(
    query: str, query_type: str, raw_results: list[dict], market_rows: list[dict],
    registry_match: dict | None = None,
) -> dict:
    df = pd.DataFrame(raw_results)

    if registry_match:
        product = registry_match["product"]
        canonical_entity = {
            "name": product.get("canonical_name"),
            "type": product.get("product_type"),
            "confidence": product.get("identity_confidence"),
            "verified": True,
        }
        companies = _registry_companies(registry_match)
        ingredients = _registry_ingredients(registry_match)
        regulatory_records = [dict(r) for r in registry_match.get("regulatory_records", [])]
        clinical_studies = [dict(r) for r in registry_match.get("clinical_studies", [])]
        patents = [dict(r) for r in registry_match.get("patents", [])]
        trademarks = [dict(r) for r in registry_match.get("trademarks", [])]
        safety_signals = [dict(r) for r in registry_match.get("safety_signals", [])]
    else:
        ingredient_entry = lookup_ingredient(query) if query_type == "ingredient" else None
        canonical_entity = {
            "name": query,
            "type": query_type,
            "confidence": None,
            "verified": False,
        }
        companies = _raw_companies(raw_results)
        ingredients = (
            [{
                "name": ingredient_entry["preferred_name"], "role": ingredient_entry.get("function"),
                "concentration": None, "confidence": None,
            }] if ingredient_entry else []
        )
        regulatory_records = _rows_for_entity_types(df, REGULATORY_ENTITY_TYPES)
        clinical_studies = _rows_for_entity_types(df, CLINICAL_ENTITY_TYPES)
        patents = _rows_for_entity_types(df, PATENT_ENTITY_TYPES)
        trademarks = []
        safety_signals = _rows_for_entity_types(df, SAFETY_ENTITY_TYPES)

    information_gaps = []
    if not registry_match:
        information_gaps.append("Product not yet verified or promoted in the registry — every field below is unverified/raw.")
    if not companies:
        information_gaps.append("No company or ownership information found.")
    if not ingredients:
        information_gaps.append("No ingredient or composition data found.")
    if not regulatory_records:
        information_gaps.append("No regulatory record found in any connected jurisdiction.")
    if not clinical_studies:
        information_gaps.append("No clinical evidence found.")
    if not patents:
        information_gaps.append("No patent information found.")
    if not market_rows:
        information_gaps.append("No market/sales/share data stored for this category.")

    return {
        "query": query,
        "query_type": query_type,
        "canonical_entity": canonical_entity,
        "companies": companies,
        "ingredients": ingredients,
        "regulatory_records": regulatory_records,
        "clinical_studies": clinical_studies,
        "patents": patents,
        "trademarks": trademarks,
        "safety_signals": safety_signals,
        "market_data": market_rows,
        "information_gaps": information_gaps,
    }
