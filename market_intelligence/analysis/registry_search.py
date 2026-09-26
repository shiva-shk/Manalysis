"""Fuzzy search across the whole registry (products, aliases, companies,
ingredients) in one query.

This is fuzzy text matching (RapidFuzz), not embeddings-based semantic
search — no model or vector store is wired in here. It's named plainly
so it isn't mistaken for more than it is: a single search box that
tolerates typos and partial names across every registry table instead
of requiring you to know which table an entity lives in.
"""

from rapidfuzz import fuzz

from database.registry_db import fetch_aliases, fetch_companies, fetch_ingredients, fetch_products

MATCH_THRESHOLD = 60


def search_registry(query: str, db_path: str | None = None) -> list[dict]:
    kwargs = {"db_path": db_path} if db_path else {}
    query = query.strip()
    if not query:
        return []

    results = []

    for product in fetch_products(**kwargs):
        score = fuzz.partial_ratio(query.lower(), (product["canonical_name"] or "").lower())
        if score >= MATCH_THRESHOLD:
            results.append({
                "entity_type": "product", "entity_id": product["id"],
                "matched_on": product["canonical_name"], "match_score": score,
            })

        for alias in fetch_aliases(product["id"], **kwargs):
            alias_score = fuzz.partial_ratio(query.lower(), (alias["alias_name"] or "").lower())
            if alias_score >= MATCH_THRESHOLD:
                results.append({
                    "entity_type": "product", "entity_id": product["id"],
                    "matched_on": f"alias: {alias['alias_name']}", "match_score": alias_score,
                })

    for company in fetch_companies(**kwargs):
        score = fuzz.partial_ratio(query.lower(), (company["canonical_name"] or "").lower())
        if score >= MATCH_THRESHOLD:
            results.append({
                "entity_type": "company", "entity_id": company["id"],
                "matched_on": company["canonical_name"], "match_score": score,
            })

    for ingredient in fetch_ingredients(**kwargs):
        for field in ("preferred_name", "inci_name"):
            value = ingredient[field]
            if not value:
                continue
            score = fuzz.partial_ratio(query.lower(), value.lower())
            if score >= MATCH_THRESHOLD:
                results.append({
                    "entity_type": "ingredient", "entity_id": ingredient["id"],
                    "matched_on": value, "match_score": score,
                })
                break

    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results
