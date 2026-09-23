from processing.synonyms import expand_query


def test_expands_known_term():
    expansions = expand_query("pdrn")
    assert expansions[0] == "pdrn"
    assert "polydeoxyribonucleotide" in expansions


def test_unknown_term_returns_itself_only():
    assert expand_query("some unmapped ingredient") == ["some unmapped ingredient"]
