"""Scores each result by source reliability, adjusted for completeness."""

from config import CONFIDENCE_BANDS

SOURCE_TYPE_WEIGHTS = {
    "official": 0.95,
    "scientific": 0.90,
    "commercial": 0.75,
    "manufacturer": 0.70,
    "discovery": 0.45,
}


def evidence_score(source_weight: float, completeness_factor: float = 1.0,
                    recency_factor: float = 1.0) -> float:
    score = source_weight * recency_factor * completeness_factor
    return round(min(score, 1.0), 2)


def completeness_factor(result_dict: dict, fields: list[str]) -> float:
    """Fraction of the given fields that are populated, floored so an
    empty record doesn't collapse to zero."""
    if not fields:
        return 1.0
    filled = sum(1 for f in fields if result_dict.get(f))
    return max(0.5, filled / len(fields))


CORE_FIELDS = ["company", "country", "category", "regulatory_status", "summary"]


def score_result(result) -> float:
    """Attach an evidence score to a SearchResult in place and return it."""
    weight = SOURCE_TYPE_WEIGHTS.get(result.source_type, 0.5)
    completeness = completeness_factor(result.to_dict(), CORE_FIELDS)
    result.evidence_score = evidence_score(weight, completeness)
    return result.evidence_score


def confidence_label(score: float) -> str:
    for low, high, label in CONFIDENCE_BANDS:
        if low <= score < high:
            return label
    return "Low"
