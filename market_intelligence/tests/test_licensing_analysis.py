from analysis.licensing_analysis import build_licensing_analysis

ACTIVE_PATENT = [{"patent_number": "US1234567B2", "legal_status": "Active"}]
INACTIVE_PATENT = [{"patent_number": "US1234567B2", "legal_status": "Lapsed"}]
REG_RECORDS = [
    {"jurisdiction": "US", "status": "cleared"},
    {"jurisdiction": "EU", "status": "CE marked"},
    {"jurisdiction": "KR", "status": "approved"},
]
STUDIES = [{"evidence_level": "registered_trial"}]
SIGNALS = [{"signal_type": "Recall Terminated"}]


def test_no_patents_found_state():
    result = build_licensing_analysis([], [], [], [])
    assert result["patent_status"]["state"] == "no_patents_found"
    assert "No patent record found" in result["considerations"][0]


def test_active_patent_state():
    result = build_licensing_analysis(ACTIVE_PATENT, [], [], [])
    assert result["patent_status"]["state"] == "active_patents_present"
    assert result["patent_status"]["active_count"] == 1
    assert "active patent" in result["considerations"][0]


def test_inactive_patent_state():
    result = build_licensing_analysis(INACTIVE_PATENT, [], [], [])
    assert result["patent_status"]["state"] == "patents_found_none_active"
    assert result["patent_status"]["active_count"] == 0


def test_regulatory_breadth_counts_distinct_jurisdictions():
    result = build_licensing_analysis([], REG_RECORDS, [], [])
    assert result["regulatory_breadth"]["jurisdiction_count"] == 3
    assert result["regulatory_breadth"]["jurisdictions"] == ["EU", "KR", "US"]


def test_no_regulatory_records_reported_plainly():
    result = build_licensing_analysis([], [], [], [])
    assert "No regulatory record found" in " ".join(result["considerations"])


def test_clinical_evidence_counted():
    result = build_licensing_analysis([], [], STUDIES, [])
    assert result["clinical_evidence"]["study_count"] == 1
    assert result["clinical_evidence"]["evidence_levels"] == ["registered_trial"]


def test_safety_signals_surfaced_in_considerations():
    result = build_licensing_analysis([], [], [], SIGNALS)
    assert result["safety_profile"]["signal_count"] == 1
    assert any("safety signal" in c for c in result["considerations"])


def test_no_safety_signals_produces_no_safety_consideration():
    result = build_licensing_analysis([], [], [], [])
    assert not any("safety signal" in c for c in result["considerations"])


def test_full_picture_produces_four_considerations():
    result = build_licensing_analysis(ACTIVE_PATENT, REG_RECORDS, STUDIES, SIGNALS)
    assert len(result["considerations"]) == 4
