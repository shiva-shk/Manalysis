from analysis.canonical_search import build_canonical_search_response

RAW_RESULTS = [
    {
        "title": "Rejuran Healer", "entity_type": "clinical_study", "company": "Pharma Research",
        "country": "South Korea", "category": "skin booster", "regulatory_status": None,
        "source_name": "ClinicalTrials.gov", "evidence_score": 0.9,
    },
    {
        "title": "Rejuran Healer", "entity_type": "medical_device", "company": "Pharma Research",
        "country": "South Korea", "category": "skin booster", "regulatory_status": "510(k) cleared",
        "source_name": "openFDA", "evidence_score": 0.85,
    },
]

MARKET_ROWS = [{"category": "skin booster", "market_value": 87.7, "year": 2024}]


def test_raw_fallback_builds_unverified_entity():
    response = build_canonical_search_response("Rejuran Healer", "brand_or_product", RAW_RESULTS, [])
    assert response["canonical_entity"]["verified"] is False
    assert response["canonical_entity"]["confidence"] is None
    assert len(response["companies"]) == 1
    assert response["companies"][0]["name"] == "Pharma Research"
    assert response["companies"][0]["role"] is None
    assert len(response["regulatory_records"]) == 1
    assert len(response["clinical_studies"]) == 1


def test_raw_fallback_flags_registry_gap():
    response = build_canonical_search_response("Rejuran Healer", "brand_or_product", RAW_RESULTS, [])
    assert any("not yet verified" in gap for gap in response["information_gaps"])


def test_raw_fallback_flags_missing_sections():
    response = build_canonical_search_response("something obscure", "brand_or_product", [], [])
    gaps = " ".join(response["information_gaps"])
    assert "company" in gaps
    assert "ingredient" in gaps
    assert "regulatory" in gaps
    assert "clinical" in gaps
    assert "patent" in gaps
    assert "market" in gaps


def test_ingredient_query_pulls_reference_entry():
    response = build_canonical_search_response("pdrn", "ingredient", [], [])
    assert len(response["ingredients"]) == 1
    assert "Polydeoxyribonucleotide" in response["ingredients"][0]["name"]


def test_registry_match_builds_verified_entity():
    registry_match = {
        "product": {"canonical_name": "Rejuran Healer", "product_type": "skin_booster", "identity_confidence": 0.92},
        "companies": [{"company_name": "PharmaResearch Co.", "role": "brand_owner", "confidence": 0.95, "source_url": "https://example.com"}],
        "ingredients": [{"ingredient_name": "PDRN", "ingredient_role": "active_substance", "concentration": "1%", "confidence": 0.9}],
        "regulatory_records": [{"jurisdiction": "KR", "status": "approved"}],
        "clinical_studies": [{"study_title": "A skin rejuvenation trial"}],
        "patents": [],
        "trademarks": [],
        "safety_signals": [],
    }
    response = build_canonical_search_response("Rejuran Healer", "brand_or_product", [], [], registry_match)

    assert response["canonical_entity"]["verified"] is True
    assert response["canonical_entity"]["confidence"] == 0.92
    assert response["companies"][0]["role"] == "brand_owner"
    assert response["ingredients"][0]["name"] == "PDRN"
    assert not any("not yet verified" in gap for gap in response["information_gaps"])
    assert any("patent" in gap for gap in response["information_gaps"])


def test_market_data_rows_passed_through():
    response = build_canonical_search_response("skin booster", "product_type", [], MARKET_ROWS)
    assert response["market_data"] == MARKET_ROWS
    assert not any("market" in gap for gap in response["information_gaps"])


def test_publication_author_string_excluded_from_companies():
    """PubMed puts its author list in the `company` field — a real
    company should never be confused with a comma-separated list of
    researcher names."""
    raw_results = [
        {
            "title": "A study", "entity_type": "publication",
            "company": "Oh S, Kim YH, Kim BR.", "source_name": "PubMed / Europe PMC",
        },
        {
            "title": "A device", "entity_type": "medical_device",
            "company": "Acme Devices Inc.", "source_name": "openFDA",
        },
    ]
    response = build_canonical_search_response("query", "brand_or_product", raw_results, [])
    names = [c["name"] for c in response["companies"]]
    assert "Acme Devices Inc." in names
    assert "Oh S, Kim YH, Kim BR." not in names
