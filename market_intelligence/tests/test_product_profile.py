from analysis.product_profile import build_profile

ROWS = [
    {
        "title": "Example Filler", "entity_type": "medical_device", "company": "Example Co",
        "country": "France", "evidence_score": 0.9,
    },
    {
        "title": "Example Filler", "entity_type": "clinical_study", "company": "Example Sponsor",
        "country": "Belgium", "evidence_score": 0.85,
    },
    {
        "title": "Unrelated Product", "entity_type": "medical_device", "company": "Other Co",
        "country": "Germany", "evidence_score": 0.7,
    },
]


def test_build_profile_filters_to_focus_title():
    profile = build_profile(ROWS, "Example Filler")
    assert profile["source_count"] == 2
    assert "Example Co" in profile["companies"]
    assert "Other Co" not in profile["companies"]


def test_build_profile_splits_into_sections():
    profile = build_profile(ROWS, "Example Filler")
    assert len(profile["sections"]["regulatory"]) == 1
    assert len(profile["sections"]["clinical"]) == 1


def test_build_profile_empty_rows():
    profile = build_profile([], "Anything")
    assert profile["sections"] == {}
