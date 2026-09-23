from connectors.eudamed import normalize_eudamed

SAMPLE_RESPONSE = {
    "content": [
        {
            "primaryDi": "06978207745564",
            "uuid": "fc8247e1-72b3-4407-a329-da31dd329f77",
            "tradeName": "Example Hyaluronic Filler",
            "manufacturerName": "Example Aesthetics BV",
            "reference": "EHF-001",
            "riskClass": {"code": "refdata.risk-class.class-iii"},
            "deviceStatusType": {"code": "refdata.device-model-status.on-the-market"},
        },
        {
            "primaryDi": "06978207745571",
            "uuid": "abc123",
            "tradeName": None,
            "reference": "Unnamed reference item",
            "manufacturerName": "Other Co",
            "riskClass": {"code": "refdata.risk-class.class-i"},
            "deviceStatusType": {"code": "refdata.device-model-status.on-the-market"},
        },
    ],
    "totalElements": 2,
}


def test_normalize_eudamed_extracts_core_fields():
    results = normalize_eudamed(SAMPLE_RESPONSE)
    assert len(results) == 2
    assert results[0].title == "Example Hyaluronic Filler"
    assert results[0].company == "Example Aesthetics BV"
    assert results[0].category == "class-iii"
    assert results[0].regulatory_status == "on-the-market"
    assert results[0].identifier == "06978207745564"


def test_normalize_eudamed_falls_back_to_reference_when_no_trade_name():
    results = normalize_eudamed(SAMPLE_RESPONSE)
    assert results[1].title == "Unnamed reference item"


def test_normalize_eudamed_handles_empty_content():
    assert normalize_eudamed({"content": []}) == []
