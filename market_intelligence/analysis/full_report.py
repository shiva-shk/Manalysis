"""Builds one consolidated report out of a single search: product
comparison, ingredients, patents, approvals, clinical studies, and any
stored Market Data rows relevant to the query (market analysis, sales,
market share).

Every section is a view over data the platform already has — the search
results just returned, the ingredient reference table, and whatever
Market Data rows an analyst already entered or uploaded — not a new
data source. A query with no matching Market Data rows gets an empty
market/sales/share section rather than a fabricated one, since this
platform never estimates a number no source actually provided.
"""

import pandas as pd

from processing.ingredient_dictionary import lookup_ingredient, search_ingredients

REGULATORY_ENTITY_TYPES = ["medical_device", "drug_product"]
STUDY_ENTITY_TYPES = ["clinical_study"]
PATENT_ENTITY_TYPES = ["patent"]


def _rows_for_entity_types(df: pd.DataFrame, entity_types: list[str]) -> list[dict]:
    if df.empty or "entity_type" not in df.columns:
        return []
    return df[df["entity_type"].isin(entity_types)].to_dict("records")


def build_product_comparison(results: list[dict]) -> list[dict]:
    """One row per distinct product title with the fields useful for a
    side-by-side comparison. A display grouping by exact title match, not
    a verified entity merge."""
    df = pd.DataFrame(results)
    if df.empty:
        return []

    rows = []
    for title, group in df.groupby("title"):
        rows.append({
            "title": title,
            "company": next((c for c in group["company"] if pd.notna(c)), None),
            "country": next((c for c in group["country"] if pd.notna(c)), None),
            "category": next((c for c in group["category"] if pd.notna(c)), None),
            "regulatory_status": next((r for r in group["regulatory_status"] if pd.notna(r)), None),
            "source_count": len(group),
            "avg_evidence_score": round(group["evidence_score"].mean(), 2),
            "sources": ", ".join(sorted(set(group["source_name"].dropna()))),
        })
    return sorted(rows, key=lambda r: r["avg_evidence_score"], reverse=True)


def match_market_data(market_rows: list[dict], query: str) -> list[dict]:
    """Market Data rows whose category or subcategory text-matches the
    query — a filter over already-sourced rows, not a new lookup."""
    q = query.lower().strip()
    matches = []
    for row in market_rows:
        category = (row.get("category") or "").lower()
        subcategory = (row.get("subcategory") or "").lower()
        if not q:
            continue
        if q in category or q in subcategory or (category and category in q):
            matches.append(row)
    return matches


def build_ingredient_section(query: str) -> dict:
    return {
        "exact_match": lookup_ingredient(query),
        "related": search_ingredients(query),
    }


def build_full_report(query: str, results: list[dict], market_rows: list[dict]) -> dict:
    df = pd.DataFrame(results)

    return {
        "query": query,
        "product_comparison": build_product_comparison(results),
        "ingredients": build_ingredient_section(query),
        "patents": _rows_for_entity_types(df, PATENT_ENTITY_TYPES),
        "approvals": _rows_for_entity_types(df, REGULATORY_ENTITY_TYPES),
        "studies": _rows_for_entity_types(df, STUDY_ENTITY_TYPES),
        "market_data": match_market_data(market_rows, query),
    }
