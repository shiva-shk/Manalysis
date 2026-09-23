from connectors.base import SearchResult
from processing.evidence_scoring import confidence_label, evidence_score, score_result


def test_evidence_score_capped_at_one():
    assert evidence_score(1.0, 1.0, 1.0) == 1.0


def test_evidence_score_scales_with_completeness():
    high = evidence_score(0.9, completeness_factor=1.0)
    low = evidence_score(0.9, completeness_factor=0.5)
    assert high > low


def test_confidence_label_bands():
    assert confidence_label(0.85) == "High"
    assert confidence_label(0.65) == "Moderate"
    assert confidence_label(0.2) == "Low"


def test_score_result_fills_in_score():
    result = SearchResult(
        title="Example filler",
        entity_type="medical_device",
        source_name="openFDA",
        source_url="https://example.com",
        source_type="official",
        company="Example Co",
        country="France",
        category="dermal_filler",
        regulatory_status="CE marked",
        summary="Cross-linked HA filler",
    )
    score = score_result(result)
    assert 0.0 < score <= 1.0
    assert result.evidence_score == score
