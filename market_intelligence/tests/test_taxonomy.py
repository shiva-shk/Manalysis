from processing.taxonomy import (
    PRODUCT_TYPES,
    REGULATORY_CATEGORIES,
    SOURCE_RELIABILITY,
    validate_against,
)


def test_validate_against_accepts_known_value():
    assert validate_against("cosmetic", REGULATORY_CATEGORIES, "regulatory_category") == []


def test_validate_against_rejects_unknown_value():
    errors = validate_against("not_a_real_category", REGULATORY_CATEGORIES, "regulatory_category")
    assert len(errors) == 1
    assert "regulatory_category" in errors[0]


def test_validate_against_allows_none():
    assert validate_against(None, PRODUCT_TYPES, "product_type") == []


def test_source_reliability_values_are_bounded():
    assert all(0.0 <= weight <= 1.0 for weight in SOURCE_RELIABILITY.values())
