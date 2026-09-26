from analysis.full_report import (
    build_full_report,
    build_ingredient_section,
    build_product_comparison,
    match_market_data,
)

SAMPLE_RESULTS = [
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
    {
        "title": "ASCE Plus", "entity_type": "patent", "company": "ExoCoBio",
        "country": "South Korea", "category": "exosome", "regulatory_status": None,
        "source_name": "EPO Open Patent Services", "evidence_score": 0.8,
    },
]

SAMPLE_MARKET_ROWS = [
    {"category": "skin booster", "subcategory": None, "market_value": 87.7, "year": 2024,
     "market_share": None, "volume": None, "source": "Grand View Research"},
    {"category": "dermal filler", "subcategory": None, "market_value": 500, "year": 2024,
     "market_share": None, "volume": None, "source": "Mintel"},
]


def test_build_product_comparison_groups_by_title():
    rows = build_product_comparison(SAMPLE_RESULTS)
    assert len(rows) == 2
    rejuran = next(r for r in rows if r["title"] == "Rejuran Healer")
    assert rejuran["source_count"] == 2
    assert rejuran["regulatory_status"] == "510(k) cleared"
    assert "ClinicalTrials.gov" in rejuran["sources"]


def test_build_product_comparison_empty_results():
    assert build_product_comparison([]) == []


def test_match_market_data_filters_by_category_substring():
    matches = match_market_data(SAMPLE_MARKET_ROWS, "skin booster")
    assert len(matches) == 1
    assert matches[0]["source"] == "Grand View Research"


def test_match_market_data_no_match_returns_empty():
    assert match_market_data(SAMPLE_MARKET_ROWS, "botulinum toxin") == []


def test_build_ingredient_section_exact_and_related():
    section = build_ingredient_section("pdrn")
    assert section["exact_match"]["preferred_name"].startswith("Polydeoxyribonucleotide")
    assert any(r["key"] == "pdrn" for r in section["related"])


def test_build_full_report_assembles_all_sections():
    report = build_full_report("skin booster", SAMPLE_RESULTS, SAMPLE_MARKET_ROWS)
    assert report["query"] == "skin booster"
    assert len(report["product_comparison"]) == 2
    assert len(report["patents"]) == 1
    assert len(report["approvals"]) == 1
    assert len(report["studies"]) == 1
    assert len(report["market_data"]) == 1


def test_build_full_report_handles_no_results_or_market_data():
    report = build_full_report("nonexistent query xyz", [], [])
    assert report["product_comparison"] == []
    assert report["patents"] == []
    assert report["approvals"] == []
    assert report["studies"] == []
    assert report["market_data"] == []
