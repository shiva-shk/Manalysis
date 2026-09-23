from connectors.base import SearchResult
from processing.monitoring import find_new_results


def make_result(identifier):
    return SearchResult(
        title="Example study",
        entity_type="clinical_study",
        source_name="ClinicalTrials.gov",
        source_url="https://example.com",
        source_type="official",
        identifier=identifier,
    )


def test_finds_only_unseen_identifiers():
    results = [make_result("NCT001"), make_result("NCT002")]
    new = find_new_results(results, known_identifiers={"NCT001"})
    assert [r.identifier for r in new] == ["NCT002"]


def test_excludes_results_without_identifier():
    results = [make_result(None)]
    assert find_new_results(results, known_identifiers=set()) == []


def test_no_known_identifiers_means_everything_is_new():
    results = [make_result("NCT001"), make_result("NCT002")]
    new = find_new_results(results, known_identifiers=set())
    assert len(new) == 2
