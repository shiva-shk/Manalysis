from connectors.openfda import (
    normalize_openfda_devices,
    normalize_openfda_drug_labels,
    normalize_openfda_pma,
    normalize_openfda_udi,
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
