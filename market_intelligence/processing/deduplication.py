"""Fuzzy-match and drop near-duplicate results across sources.

Two results are only merged when they share a similar title AND at least
one strong secondary signal (company or identifier) — a similar name alone
is not enough, since many unrelated products share generic naming.
"""

from rapidfuzz import fuzz

SIMILARITY_THRESHOLD = 0.85


def title_similarity(a: str, b: str) -> float:
    return fuzz.token_set_ratio((a or "").lower().strip(), (b or "").lower().strip()) / 100


def _is_duplicate(a, b) -> bool:
    if title_similarity(a.title, b.title) < SIMILARITY_THRESHOLD:
        return False

    if a.identifier and b.identifier and a.identifier == b.identifier:
        return True

    if a.company and b.company and a.company.lower().strip() == b.company.lower().strip():
        return True

    return False


def deduplicate(results: list) -> list:
    """Keep the highest-evidence-score result from each duplicate cluster."""
    kept: list = []
    for candidate in results:
        match_index = None
        for i, existing in enumerate(kept):
            if _is_duplicate(candidate, existing):
                match_index = i
                break

        if match_index is None:
            kept.append(candidate)
        elif candidate.evidence_score > kept[match_index].evidence_score:
            kept[match_index] = candidate

    return kept
