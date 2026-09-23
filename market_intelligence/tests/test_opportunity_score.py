import pytest

from analysis.opportunity_score import opportunity_score, score_breakdown, validate_scores

FULL_SCORES = {
    "market": 4, "clinical": 3, "regulatory": 4, "manufacturing": 3,
    "differentiation": 5, "ip": 2, "strategic_fit": 4,
}


def test_validate_scores_flags_missing_dimension():
    incomplete = dict(FULL_SCORES)
    del incomplete["ip"]
    errors = validate_scores(incomplete)
    assert any("Patent / FTO risk" in e for e in errors)


def test_validate_scores_flags_out_of_range():
    bad = dict(FULL_SCORES)
    bad["market"] = 9
    errors = validate_scores(bad)
    assert any("Market attractiveness" in e for e in errors)


def test_opportunity_score_all_max_is_one():
    all_max = {k: 5 for k in FULL_SCORES}
    assert opportunity_score(all_max) == 1.0


def test_opportunity_score_all_min_is_zero():
    all_min = {k: 1 for k in FULL_SCORES}
    assert opportunity_score(all_min) == 0.0


def test_opportunity_score_raises_on_invalid_input():
    with pytest.raises(ValueError):
        opportunity_score({})


def test_score_breakdown_includes_notes():
    breakdown = score_breakdown(FULL_SCORES, notes={"market": "Growing 12% YoY"})
    market_row = next(r for r in breakdown if r["dimension"] == "Market attractiveness")
    assert market_row["notes"] == "Growing 12% YoY"
