from analysis.product_matching import match_decision, product_match_score

PRODUCT_A = {
    "normalized_name": "juvederm voluma xc", "manufacturer": "Allergan",
    "regulatory_number": "P100018", "product_family": "juvederm", "country": "US",
}


def test_identical_records_score_full_marks():
    assert product_match_score(PRODUCT_A, dict(PRODUCT_A)) == 1.00


def test_regulatory_number_match_alone_is_strong_evidence():
    b = {"regulatory_number": "P100018"}
    score = product_match_score(PRODUCT_A, b)
    assert score == 0.30


def test_name_only_match_is_not_automatic():
    """Two different companies can sell similarly-named products — a bare
    name match must never cross the automatic-match threshold alone."""
    b = {"normalized_name": "juvederm voluma xc"}
    score = product_match_score(PRODUCT_A, b)
    assert score == 0.30
    assert match_decision(score) != "automatic_match"


def test_name_plus_manufacturer_plus_family_and_country_reaches_analyst_review():
    b = {
        "normalized_name": "juvederm voluma xc", "manufacturer": "Allergan",
        "product_family": "juvederm", "country": "US",
    }
    score = product_match_score(PRODUCT_A, b)
    assert score == 0.70
    assert match_decision(score) == "analyst_review"


def test_no_overlapping_fields_scores_zero():
    assert product_match_score(PRODUCT_A, {}) == 0.0
    assert match_decision(0.0) == "no_match"


def test_missing_field_on_either_side_never_contributes():
    a = {"normalized_name": "widget", "manufacturer": None}
    b = {"normalized_name": "widget", "manufacturer": "Acme"}
    assert product_match_score(a, b) == 0.30


def test_match_decision_thresholds():
    assert match_decision(0.90) == "automatic_match"
    assert match_decision(0.89) == "analyst_review"
    assert match_decision(0.70) == "analyst_review"
    assert match_decision(0.69) == "no_match"
