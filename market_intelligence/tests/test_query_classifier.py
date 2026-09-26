from processing.query_classifier import classify_query


def test_classifies_ingredient():
    assert classify_query("Hyaluronic acid filler") == "ingredient"


def test_classifies_company():
    assert classify_query("Galderma") == "company"


def test_classifies_product_type():
    assert classify_query("dermal filler") == "product_type"


def test_classifies_clinical_trial_id():
    assert classify_query("NCT01234567") == "clinical_trial"


def test_classifies_regulatory_id():
    assert classify_query("K123456") == "regulatory_or_trial_id"
    assert classify_query("P100018") == "regulatory_or_trial_id"


def test_classifies_patent_number():
    assert classify_query("US11230586B2") == "patent_number"
    assert classify_query("WO2025123456A1") == "patent_number"
    assert classify_query("EP1234567B1") == "patent_number"


def test_defaults_to_brand_or_product():
    assert classify_query("Profhilo") == "brand_or_product"
