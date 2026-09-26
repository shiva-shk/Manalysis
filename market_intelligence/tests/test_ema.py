from connectors.ema import normalize_ema_medicines, search_ema_medicines

SAMPLE_MEDICINES = [
    {
        "name_of_medicine": "Tyruko",
        "active_substance": "natalizumab",
        "therapeutic_area_mesh": "Multiple Sclerosis, Relapsing-Remitting",
        "medicine_status": "Authorised",
        "pharmacotherapeutic_group_human": "Immunosuppressants",
        "marketing_authorisation_developer_applicant_holder": "Sandoz GmbH",
        "ema_product_number": "EMEA/H/C/005752",
        "therapeutic_indication": "Indicated for relapsing remitting multiple sclerosis.",
    },
    {
        "name_of_medicine": "Botulinum Toxin Product X",
        "active_substance": "botulinum toxin type a",
        "therapeutic_area_mesh": "Dystonia",
        "medicine_status": "Withdrawn",
        "pharmacotherapeutic_group_human": "Muscle relaxants",
        "marketing_authorisation_developer_applicant_holder": "Acme Pharma",
        "ema_product_number": "EMEA/H/C/999999",
        "therapeutic_indication": None,
    },
]


def test_search_ema_medicines_matches_active_substance(monkeypatch):
    monkeypatch.setattr("connectors.ema.fetch_ema_medicines", lambda: SAMPLE_MEDICINES)
    results = search_ema_medicines("botulinum")
    assert len(results) == 1
    assert results[0]["name_of_medicine"] == "Botulinum Toxin Product X"


def test_search_ema_medicines_matches_name(monkeypatch):
    monkeypatch.setattr("connectors.ema.fetch_ema_medicines", lambda: SAMPLE_MEDICINES)
    results = search_ema_medicines("tyruko")
    assert len(results) == 1


def test_search_ema_medicines_respects_limit(monkeypatch):
    monkeypatch.setattr("connectors.ema.fetch_ema_medicines", lambda: SAMPLE_MEDICINES)
    results = search_ema_medicines("a", limit=1)
    assert len(results) == 1


def test_normalize_ema_medicines_maps_fields():
    results = normalize_ema_medicines(SAMPLE_MEDICINES)
    assert len(results) == 2
    r = results[0]
    assert r.title == "Tyruko"
    assert r.entity_type == "eu_medicine"
    assert r.company == "Sandoz GmbH"
    assert r.country == "European Union"
    assert r.regulatory_status == "Authorised"
    assert r.identifier == "EMEA/H/C/005752"


def test_normalize_ema_medicines_handles_missing_indication():
    results = normalize_ema_medicines([SAMPLE_MEDICINES[1]])
    assert results[0].summary is None
