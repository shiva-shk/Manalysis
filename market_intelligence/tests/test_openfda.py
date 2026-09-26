from unittest.mock import Mock, patch

from connectors.openfda import (
    normalize_openfda_devices,
    normalize_openfda_drug_labels,
    normalize_openfda_pma,
    normalize_openfda_udi,
    search_openfda_devices,
    search_openfda_drug_labels,
)

SAMPLE_PMA_RAW = {
    "results": [
        {
            "pma_number": "P050052",
            "supplement_number": "S104",
            "applicant": "Merz North America, Inc.",
            "trade_name": "RADIESSE (+) Lidocaine Dermal Filler 1.5CC",
            "product_code": "LMH",
            "decision_code": "OK30",
            "ao_statement": "Modify the sterilization load.",
        },
    ]
}

SAMPLE_UDI_RAW = {
    "results": [
        {
            "brand_name": "FILLER",
            "company_name": "KLS-Martin L.P.",
            "commercial_distribution_status": "Not in Commercial Distribution",
            "identifiers": [{"id": "00888118096111", "type": "Primary", "issuing_agency": "GS1"}],
            "product_codes": [{"code": "DZN", "name": "INSTRUMENTS, DENTAL HAND"}],
        },
    ]
}


def test_normalize_openfda_pma_extracts_key_fields():
    results = normalize_openfda_pma(SAMPLE_PMA_RAW)
    assert len(results) == 1
    r = results[0]
    assert r.title == "RADIESSE (+) Lidocaine Dermal Filler 1.5CC"
    assert r.entity_type == "medical_device"
    assert r.company == "Merz North America, Inc."
    assert r.identifier == "P050052/S104"
    assert "FDA PMA" in r.regulatory_status


def test_normalize_openfda_pma_handles_no_supplement():
    raw = {"results": [{"pma_number": "P123456", "trade_name": "Widget", "applicant": "Acme"}]}
    results = normalize_openfda_pma(raw)
    assert results[0].identifier == "P123456"


def test_normalize_openfda_udi_extracts_key_fields():
    results = normalize_openfda_udi(SAMPLE_UDI_RAW)
    assert len(results) == 1
    r = results[0]
    assert r.title == "FILLER"
    assert r.company == "KLS-Martin L.P."
    assert r.identifier == "00888118096111"
    assert r.category == "INSTRUMENTS, DENTAL HAND"


def test_normalize_openfda_udi_handles_missing_identifiers():
    raw = {"results": [{"brand_name": "NoID Device", "company_name": "Acme"}]}
    results = normalize_openfda_udi(raw)
    assert results[0].identifier is None


def test_normalize_openfda_devices_and_drug_labels_still_work():
    device_raw = {"results": [{"device_name": "Widget", "k_number": "K123456", "applicant": "Acme"}]}
    assert normalize_openfda_devices(device_raw)[0].identifier == "K123456"

    label_raw = {"results": [{"openfda": {"brand_name": ["Widget"], "manufacturer_name": ["Acme"]}}]}
    assert normalize_openfda_drug_labels(label_raw)[0].title == "Widget"


def test_search_openfda_devices_quotes_multi_word_query():
    """A multi-word query must be quoted as one phrase, or openFDA's
    Lucene-style search treats it as OR — "Rejuran Healer" unquoted would
    match any record containing "Rejuran" OR "Healer" alone, which is
    exactly the false-positive noise (e.g. "CONTOUR HEALER") this caused
    before the fix."""
    with patch("connectors.openfda.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=200, json=lambda: {"results": []})
        mock_get.return_value.raise_for_status = lambda: None
        search_openfda_devices("Rejuran Healer")
        params = mock_get.call_args.kwargs["params"]
        assert params["search"] == 'device_name:"Rejuran Healer"'


def test_search_openfda_drug_labels_quotes_multi_word_query():
    with patch("connectors.openfda.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=200, json=lambda: {"results": []})
        mock_get.return_value.raise_for_status = lambda: None
        search_openfda_drug_labels("Rejuran Healer")
        params = mock_get.call_args.kwargs["params"]
        assert params["search"] == 'openfda.brand_name:"Rejuran Healer"'


def test_openfda_404_is_treated_as_zero_results_not_an_error():
    """openFDA returns HTTP 404 for a search with zero matching records —
    documented behavior, not a real failure — so it must not raise."""
    with patch("connectors.openfda.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=404)
        result = search_openfda_devices("something with no matches")
        assert result == {"results": []}
