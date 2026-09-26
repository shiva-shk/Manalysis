from processing.market_data import prepare_rows, validate_row


def test_validate_row_requires_category_source_and_scope():
    errors = validate_row({})
    assert "'category' is required" in errors
    assert "'source' is required" in errors
    assert "'scope_level' is required" in errors


def test_validate_row_checks_confidence_range():
    errors = validate_row({
        "category": "filler", "source": "Mintel", "scope_level": "global",
        "confidence_score": 1.5,
    })
    assert any("confidence_score" in e for e in errors)


def test_validate_row_rejects_unknown_scope_level():
    errors = validate_row({"category": "filler", "source": "Mintel", "scope_level": "planetary"})
    assert any("scope_level" in e for e in errors)


def test_validate_row_requires_country_when_scope_is_country():
    errors = validate_row({"category": "filler", "source": "Mintel", "scope_level": "country"})
    assert any("country" in e for e in errors)


def test_validate_row_requires_region_when_scope_is_regional():
    errors = validate_row({"category": "filler", "source": "Mintel", "scope_level": "regional"})
    assert any("region" in e for e in errors)


def test_validate_row_country_scope_with_country_is_valid():
    errors = validate_row({
        "category": "filler", "source": "Internal Iran data", "scope_level": "country",
        "country": "Iran",
    })
    assert errors == []


def test_prepare_rows_splits_valid_and_invalid():
    records = [
        {"category": "filler", "source": "Mintel", "scope_level": "regional", "region": "EU"},
        {"category": "", "source": "Mintel", "scope_level": "global"},
    ]
    valid, errors = prepare_rows(records)
    assert len(valid) == 1
    assert len(errors) == 1
    assert "uploaded_at" in valid[0]


def test_validate_row_rejects_nan_required_field():
    """A CSV/Excel upload's blank cell becomes pandas' float NaN, not None
    or "" — `not row.get(field)` doesn't catch that, since NaN is truthy."""
    errors = validate_row({
        "category": float("nan"), "source": "Mintel", "scope_level": "global",
    })
    assert "'category' is required" in errors


def test_validate_row_rejects_nan_country_when_scope_is_country():
    errors = validate_row({
        "category": "filler", "source": "Mintel", "scope_level": "country",
        "country": float("nan"),
    })
    assert any("country" in e for e in errors)


def test_prepare_rows_normalizes_nan_to_none():
    records = [{"category": "filler", "source": "Mintel", "scope_level": "global",
                "region": float("nan"), "country": float("nan")}]
    valid, errors = prepare_rows(records)
    assert not errors
    assert valid[0]["region"] is None
    assert valid[0]["country"] is None
