from processing.query_classifier import classify_query


def test_classifies_ingredient():
    assert classify_query("Hyaluronic acid filler") == "ingredient"


def test_classifies_company():
    assert classify_query("Galderma") == "company"


def test_classifies_product_type():
    assert classify_query("dermal filler") == "product_type"


def test_classifies_regulatory_id():
    assert classify_query("NCT01234567") == "regulatory_or_trial_id"


def test_defaults_to_brand_or_product():
    assert classify_query("Profhilo") == "brand_or_product"
