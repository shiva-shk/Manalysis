"""Rough keyword-based classification of a free-text search query.

A production system would back this with a controlled vocabulary and an
entity-recognition model; this keyword version is enough to route a query
to the right connectors for the MVP.
"""

INGREDIENT_TERMS = [
    "hyaluronic", "pdrn", "polynucleotide", "polydeoxyribonucleotide",
    "niacinamide", "botulinum", "exosome", "collagen", "peptide",
]

COMPANY_TERMS = [
    "galderma", "merz", "allergan", "croma", "ipsen", "revance",
]

PRODUCT_TYPE_TERMS = [
    "filler", "skin booster", "rf device", "mesotherapy",
    "botulinum toxin", "dermal filler",
]

REGULATORY_PREFIXES = ("nct", "k1", "k2", "de novo", "p1", "p2")


def classify_query(query: str) -> str:
    """Return one of: regulatory_or_trial_id, ingredient, company,
    product_type, brand_or_product."""
    q = query.lower().strip()

    if q.startswith(REGULATORY_PREFIXES):
        return "regulatory_or_trial_id"

    if any(term in q for term in INGREDIENT_TERMS):
        return "ingredient"

    if any(term in q for term in COMPANY_TERMS):
        return "company"

    if any(term in q for term in PRODUCT_TYPE_TERMS):
        return "product_type"

    return "brand_or_product"
