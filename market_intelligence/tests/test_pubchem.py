from unittest.mock import Mock, patch

from connectors.base import ConnectorError
from connectors.pubchem import _curl_get, normalize_pubchem, search_pubchem

SAMPLE_PROPS_RESPONSE = {
    "PropertyTable": {
        "Properties": [{
            "CID": 5526, "MolecularFormula": "C8H15NO2", "MolecularWeight": "157.21",
            "IUPACName": "4-(aminomethyl)cyclohexane-1-carboxylic acid",
            "CanonicalSMILES": "C1CC(CCC1CN)C(=O)O", "InChIKey": "GYDJEQRTZSCIOI-UHFFFAOYSA-N",
        }]
    }
}

SAMPLE_SYNONYMS_RESPONSE = {
    "InformationList": {
        "Information": [{"CID": 5526, "Synonym": ["701-54-2", "Tranexamic acid", "AMCHA"]}]
    }
}


def test_search_pubchem_exact_match():
    with patch("connectors.pubchem._curl_get") as mock_curl:
        mock_curl.side_effect = [
            (200, SAMPLE_PROPS_RESPONSE),
            (200, SAMPLE_SYNONYMS_RESPONSE),
        ]
        result = search_pubchem("tranexamic acid")

    assert result["matched_name"] == "tranexamic acid"
    assert result["cid"] == 5526
    assert result["cas_number"] == "701-54-2"
    assert result["MolecularFormula"] == "C8H15NO2"


def test_search_pubchem_falls_back_to_autocomplete():
    with patch("connectors.pubchem._curl_get") as mock_curl:
        mock_curl.side_effect = [
            (404, {}),
            (200, {"dictionary_terms": {"compound": ["Tranexamic acid"]}}),
            (200, SAMPLE_PROPS_RESPONSE),
            (200, SAMPLE_SYNONYMS_RESPONSE),
        ]
        result = search_pubchem("tranexemic acidd")

    assert result["matched_name"] == "Tranexamic acid"
    assert result["cid"] == 5526


def test_search_pubchem_returns_none_when_nothing_matches():
    with patch("connectors.pubchem._curl_get") as mock_curl:
        mock_curl.side_effect = [
            (404, {}),
            (200, {"dictionary_terms": {}}),
        ]
        result = search_pubchem("complete gibberish xyz123")

    assert result is None


def test_search_pubchem_raises_connector_error_on_server_error():
    with patch("connectors.pubchem._curl_get") as mock_curl:
        mock_curl.return_value = (503, {"Fault": {"Message": "Server too busy"}})
        try:
            search_pubchem("niacinamide")
            assert False, "expected ConnectorError"
        except ConnectorError as exc:
            assert "Server too busy" in str(exc)


def test_normalize_pubchem_maps_fields():
    result = {
        "matched_name": "Tranexamic acid", "cid": 5526, "cas_number": "701-54-2",
        "MolecularFormula": "C8H15NO2",
    }
    results = normalize_pubchem(result)
    assert len(results) == 1
    r = results[0]
    assert r.title == "Tranexamic acid"
    assert r.entity_type == "chemical_compound"
    assert r.identifier == "CID 5526"
    assert r.summary == "CAS 701-54-2"
    assert "5526" in r.source_url


def test_normalize_pubchem_handles_no_match():
    assert normalize_pubchem(None) == []


def test_normalize_pubchem_handles_no_cas_number():
    result = {"matched_name": "Widget", "cid": 1, "cas_number": None, "MolecularFormula": "X"}
    assert normalize_pubchem(result)[0].summary is None


def test_curl_get_parses_status_and_body():
    with patch("connectors.pubchem.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout='{"CID": 936}\n200')
        status_code, data = _curl_get("https://example.com")
    assert status_code == 200
    assert data == {"CID": 936}


def test_curl_get_raises_on_nonzero_exit_code():
    with patch("connectors.pubchem.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=6, stdout="")
        try:
            _curl_get("https://example.com")
            assert False, "expected ConnectorError"
        except ConnectorError:
            pass
