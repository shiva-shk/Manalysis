from processing.ingredient_dictionary import lookup_ingredient, search_ingredients


def test_lookup_known_ingredient():
    entry = lookup_ingredient("PDRN")
    assert entry is not None
    assert entry["cas_number"] == "9007-49-2"


def test_lookup_unknown_ingredient():
    assert lookup_ingredient("unobtainium") is None


def test_search_matches_partial_term():
    matches = search_ingredients("acid")
    keys = {m["key"] for m in matches}
    assert "hyaluronic acid" in keys
