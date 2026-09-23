from processing.market_data import prepare_rows, validate_row


def test_validate_row_requires_category_and_source():
    errors = validate_row({})
    assert "'category' is required" in errors
    assert "'source' is required" in errors


def test_validate_row_checks_confidence_range():
    errors = validate_row({"category": "filler", "source": "Mintel", "confidence_score": 1.5})
    assert any("confidence_score" in e for e in errors)


def test_prepare_rows_splits_valid_and_invalid():
    records = [
        {"category": "filler", "source": "Mintel", "region": "EU"},
        {"category": "", "source": "Mintel"},
    ]
    valid, errors = prepare_rows(records)
    assert len(valid) == 1
    assert len(errors) == 1
    assert "uploaded_at" in valid[0]
