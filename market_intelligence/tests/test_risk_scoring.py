import pytest

from analysis.risk_scoring import check_stop_criteria, risk_acceptability, risk_priority_number


def test_risk_priority_number_multiplies():
    assert risk_priority_number(3, 4, 2) == 24


def test_risk_priority_number_rejects_out_of_range():
    with pytest.raises(ValueError):
        risk_priority_number(6, 3, 3)
    with pytest.raises(ValueError):
        risk_priority_number(3, 0, 3)


def test_risk_acceptability_bands():
    assert risk_acceptability(4) == "acceptable"
    assert risk_acceptability(20) == "acceptable_with_controls"
    assert risk_acceptability(50) == "requires_mitigation"
    assert risk_acceptability(100) == "unacceptable"


def test_check_stop_criteria_detects_keyword():
    triggered = check_stop_criteria(["Endotoxin levels showed unacceptable endotoxin risk"])
    assert "unacceptable endotoxin" in triggered


def test_check_stop_criteria_no_match():
    assert check_stop_criteria(["Minor cosmetic packaging defect"]) == []


def test_check_stop_criteria_ignores_none_values():
    assert check_stop_criteria([None, "", "no viable margin at this price point"]) == ["no viable margin"]
