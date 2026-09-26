"""Rough keyword-based classification of a free-text search query.

A production system would back this with a controlled vocabulary and an
entity-recognition model; this keyword version is enough to route a query
to the right connectors for the MVP.
"""

import re

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

REGULATORY_PREFIXES = ("k1", "k2", "de novo", "p1", "p2")

# NCT01234567 (ClinicalTrials.gov registry ID format: NCT + 8 digits).
CLINICAL_TRIAL_RE = re.compile(r"^nct\d{8}$")

# Patent publication number formats across the major offices this
# platform's connectors (or a future trademark/patent connector) would
# realistically see: WO2025123456(A1), EP1234567(B1), US11230586B2,
# PCT/US2025/012345.
PATENT_NUMBER_RE = re.compile(
    r"^(wo\d{10,12}|ep\d{6,8}|us\d{7,11}|pct/\w{2}\d{4}/\d{5,6})"
    r"[ab]\d?$|^(wo\d{10,12}|ep\d{6,8}|us\d{7,11}|pct/\w{2}\d{4}/\d{5,6})$"
)


def classify_query(query: str) -> str:
    """Return one of: clinical_trial, patent_number, regulatory_or_trial_id,
    ingredient, company, product_type, brand_or_product."""
    q = query.lower().strip()
    q_compact = q.replace(" ", "")

    if CLINICAL_TRIAL_RE.match(q_compact):
        return "clinical_trial"

    if PATENT_NUMBER_RE.match(q_compact):
        return "patent_number"

    if q.startswith(REGULATORY_PREFIXES):
        return "regulatory_or_trial_id"

    if any(term in q for term in INGREDIENT_TERMS):
        return "ingredient"

    if any(term in q for term in COMPANY_TERMS):
        return "company"

    if any(term in q for term in PRODUCT_TYPE_TERMS):
        return "product_type"

    return "brand_or_product"
