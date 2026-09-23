from connectors.base import SearchResult
from processing.deduplication import deduplicate


def make_result(title, company=None, identifier=None, score=0.5):
    return SearchResult(
        title=title,
        entity_type="medical_device",
        source_name="src",
        source_url="https://example.com",
        source_type="official",
        company=company,
        identifier=identifier,
        evidence_score=score,
    )


def test_keeps_distinct_results():
    results = [make_result("Product A"), make_result("Completely different product")]
    assert len(deduplicate(results)) == 2


def test_merges_same_identifier():
    results = [
        make_result("Example Filler", identifier="K123456", score=0.6),
        make_result("Example Filler", identifier="K123456", score=0.9),
    ]
    deduped = deduplicate(results)
    assert len(deduped) == 1
    assert deduped[0].evidence_score == 0.9


def test_does_not_merge_similar_name_different_company():
    results = [
        make_result("Filler Plus", company="Company A"),
        make_result("Filler Plus", company="Company B"),
    ]
    assert len(deduplicate(results)) == 2
