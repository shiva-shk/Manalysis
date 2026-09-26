from analysis.regulatory_comparison import build_regulatory_comparison

RECORDS = [
    {"jurisdiction": "US", "status": "FDA 510(k) cleared", "registration_number": "K123456"},
    {"jurisdiction": "EU", "status": "CE marked", "registration_number": "EU-1"},
    {"jurisdiction": "KR", "status": "withdrawn", "registration_number": "KR-1"},
]


def test_groups_records_by_jurisdiction():
    result = build_regulatory_comparison(RECORDS)
    assert result["jurisdictions_covered"] == ["EU", "KR", "US"]
    assert len(result["by_jurisdiction"]["US"]) == 1


def test_status_summary_uses_positive_marker_words():
    result = build_regulatory_comparison(RECORDS)
    assert result["status_summary"]["US"] == "approved"


def test_status_summary_falls_back_to_actual_status_when_not_positive():
    result = build_regulatory_comparison(RECORDS)
    assert result["status_summary"]["KR"] == "withdrawn"


def test_no_target_jurisdictions_means_no_gaps_key():
    result = build_regulatory_comparison(RECORDS)
    assert "gaps" not in result


def test_flags_gaps_against_target_jurisdictions():
    result = build_regulatory_comparison(RECORDS, target_jurisdictions=["US", "EU", "KR", "CA", "AU", "JP"])
    assert result["gaps"] == ["CA", "AU", "JP"]


def test_empty_records_with_targets_flags_all_as_gaps():
    result = build_regulatory_comparison([], target_jurisdictions=["US", "EU"])
    assert result["gaps"] == ["US", "EU"]
    assert result["jurisdictions_covered"] == []


def test_missing_jurisdiction_field_grouped_as_unknown():
    result = build_regulatory_comparison([{"status": "approved", "registration_number": "X"}])
    assert "unknown" in result["jurisdictions_covered"]
