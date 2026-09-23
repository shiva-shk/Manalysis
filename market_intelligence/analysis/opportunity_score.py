"""Transparent, weighted development-opportunity scoring.

Each dimension is scored 1-5 by an analyst; the model only combines them.
It is a decision-support aid, not a verdict — callers should keep the
per-dimension reasoning alongside the score, not just the final number.
"""

DIMENSIONS = {
    "market": {"label": "Market attractiveness", "weight": 0.20},
    "clinical": {"label": "Clinical evidence", "weight": 0.15},
    "regulatory": {"label": "Regulatory feasibility", "weight": 0.15},
    "manufacturing": {"label": "Manufacturing feasibility", "weight": 0.15},
    "differentiation": {"label": "Competitive differentiation", "weight": 0.15},
    "ip": {"label": "Patent / FTO risk", "weight": 0.10},
    "strategic_fit": {"label": "Strategic fit", "weight": 0.10},
}

SCORE_MIN, SCORE_MAX = 1, 5


def validate_scores(scores: dict) -> list[str]:
    errors = []
    for key in DIMENSIONS:
        if key not in scores:
            errors.append(f"Missing score for '{DIMENSIONS[key]['label']}'")
            continue
        value = scores[key]
        if not isinstance(value, (int, float)) or not (SCORE_MIN <= value <= SCORE_MAX):
            errors.append(
                f"'{DIMENSIONS[key]['label']}' must be between {SCORE_MIN} and {SCORE_MAX}"
            )
    return errors


def opportunity_score(scores: dict) -> float:
    """Weighted average, rescaled from the 1-5 input range to 0-1."""
    errors = validate_scores(scores)
    if errors:
        raise ValueError("; ".join(errors))

    weighted_sum = sum(scores[key] * DIMENSIONS[key]["weight"] for key in DIMENSIONS)
    normalized = (weighted_sum - SCORE_MIN) / (SCORE_MAX - SCORE_MIN)
    return round(normalized, 2)


def score_breakdown(scores: dict, notes: dict | None = None) -> list[dict]:
    """Per-dimension rows for display: label, weight, score, and the
    analyst's reasoning if supplied."""
    notes = notes or {}
    return [
        {
            "dimension": meta["label"],
            "weight": meta["weight"],
            "score": scores.get(key),
            "notes": notes.get(key, ""),
        }
        for key, meta in DIMENSIONS.items()
    ]
