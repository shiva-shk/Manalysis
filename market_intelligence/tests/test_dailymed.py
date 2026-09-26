from connectors.dailymed import normalize_dailymed_spls

SAMPLE_RAW = {
    "data": [
        {
            "spl_version": 62,
            "published_date": "Aug 03, 2026",
            "title": "BOTOX (ONABOTULINUMTOXINA) INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION [ALLERGAN, INC.]",
            "setid": "33d066a9-34ff-4a1a-b38b-d10983df3300",
        },
    ]
}


def test_normalize_dailymed_spls_extracts_manufacturer_from_title():
    results = normalize_dailymed_spls(SAMPLE_RAW)
    assert len(results) == 1
    r = results[0]
    assert r.title == "BOTOX (ONABOTULINUMTOXINA) INJECTION, POWDER, LYOPHILIZED, FOR SOLUTION"
    assert r.company == "ALLERGAN, INC."
    assert r.identifier == "33d066a9-34ff-4a1a-b38b-d10983df3300"
    assert "33d066a9" in r.source_url


def test_normalize_dailymed_spls_handles_title_without_brackets():
    raw = {"data": [{"title": "PLAIN TITLE NO BRACKETS", "setid": "abc123", "published_date": "Jan 01, 2026"}]}
    results = normalize_dailymed_spls(raw)
    assert results[0].title == "PLAIN TITLE NO BRACKETS"
    assert results[0].company is None


def test_normalize_dailymed_spls_handles_empty_data():
    assert normalize_dailymed_spls({"data": []}) == []
