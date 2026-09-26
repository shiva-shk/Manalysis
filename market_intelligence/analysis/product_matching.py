"""Weighted product-identity matching, distinct from the fuzzy
name-similarity clustering in entity_resolution.py: this compares
structured fields (name, manufacturer, regulatory number, family,
country) with fixed weights, for deciding whether two records from
different sources describe the same real-world product.

Never merges on name similarity alone — a regulatory number match or a
manufacturer+name match carries real evidentiary weight; a bare name
match does not, since two different companies can sell differently
formulated products under confusingly similar names.
"""

AUTOMATIC_MATCH_THRESHOLD = 0.90
ANALYST_REVIEW_THRESHOLD = 0.70


def product_match_score(a: dict, b: dict) -> float:
    """Both dicts may carry: normalized_name, manufacturer,
    regulatory_number, product_family, country. A missing/None field on
    either side never contributes points — it's neither evidence for nor
    against a match, just unknown."""
    score = 0.0

    if a.get("normalized_name") and a.get("normalized_name") == b.get("normalized_name"):
        score += 0.30

    if a.get("manufacturer") and a.get("manufacturer") == b.get("manufacturer"):
        score += 0.25

    if a.get("regulatory_number") and a.get("regulatory_number") == b.get("regulatory_number"):
        score += 0.30

    if a.get("product_family") and a.get("product_family") == b.get("product_family"):
        score += 0.10

    if a.get("country") and a.get("country") == b.get("country"):
        score += 0.05

    return round(score, 2)


def match_decision(score: float) -> str:
    """One of "automatic_match", "analyst_review", "no_match"."""
    if score >= AUTOMATIC_MATCH_THRESHOLD:
        return "automatic_match"
    if score >= ANALYST_REVIEW_THRESHOLD:
        return "analyst_review"
    return "no_match"
