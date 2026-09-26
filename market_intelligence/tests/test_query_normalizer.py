from processing.query_normalizer import normalize_query


def test_normalize_query_strips_accent_and_trademark_symbol():
    assert normalize_query("Juvéderm® Voluma XC") == "juvederm voluma xc"


def test_normalize_query_strips_registered_and_copyright_symbols():
    assert normalize_query("Restylane™ Lyft©") == "restylane lyft"


def test_normalize_query_collapses_punctuation_and_whitespace():
    assert normalize_query("PDRN  --  injection!!") == "pdrn injection"


def test_normalize_query_handles_plain_ascii_unchanged():
    assert normalize_query("Rejuran Healer") == "rejuran healer"


def test_normalize_query_handles_empty_string():
    assert normalize_query("") == ""
