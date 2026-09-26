import os
import tempfile

import pytest

from database.registry_db import (
    add_control,
    add_cost_model,
    add_cpp,
    add_cqa,
    add_portfolio_gap,
    add_qttp,
    add_risk_assessment,
    add_stage_gate_decision,
    create_product,
    current_stage,
    fetch_controls,
    fetch_cost_models,
    fetch_cpps,
    fetch_cqas,
    fetch_portfolio_gaps,
    fetch_qttp,
    fetch_risk_assessments,
    fetch_stage_gate_decisions,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.remove(path)


@pytest.fixture
def product_id(db_path):
    return create_product("Example Filler", db_path=db_path)


def test_qttp(db_path, product_id):
    add_qttp(product_id, db_path=db_path, dosage_form="gel", route="intradermal")
    rows = fetch_qttp(product_id, db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["route"] == "intradermal"


def test_cqa_and_cpp_and_control(db_path, product_id):
    add_cqa(product_id, "Endotoxin", db_path=db_path, attribute_category="endotoxin", criticality="high")
    add_cpp(product_id, "Sterilization temperature", db_path=db_path, process_step="terminal sterilization")
    add_control(product_id, "Endotoxin LAL assay", db_path=db_path, acceptance_criteria="< 0.5 EU/mL")

    assert len(fetch_cqas(product_id, db_path=db_path)) == 1
    assert len(fetch_cpps(product_id, db_path=db_path)) == 1
    assert len(fetch_controls(product_id, db_path=db_path)) == 1


def test_risk_assessment(db_path, product_id):
    add_risk_assessment(
        "sterility", "Endotoxin contamination", db_path=db_path, product_id=product_id,
        severity=5, occurrence=2, detectability=2, risk_priority_number=20,
    )
    risks = fetch_risk_assessments(product_id, db_path=db_path)
    assert len(risks) == 1
    assert risks[0]["risk_priority_number"] == 20


def test_stage_gate_decision_and_current_stage(db_path, product_id):
    add_stage_gate_decision(product_id, "gate_0_opportunity_discovery", "go", db_path=db_path)
    add_stage_gate_decision(product_id, "gate_1_feasibility", "conditional_go", db_path=db_path)

    history = fetch_stage_gate_decisions(product_id, db_path=db_path)
    assert len(history) == 2

    latest = current_stage(product_id, db_path=db_path)
    assert latest["stage"] == "gate_1_feasibility"
    assert latest["decision"] == "conditional_go"


def test_current_stage_none_when_no_decisions(db_path, product_id):
    assert current_stage(product_id, db_path=db_path) is None


def test_cost_model(db_path, product_id):
    add_cost_model(
        product_id, db_path=db_path, scenario="base_case",
        material_cost=10, estimated_cogs=20, target_price=40, gross_margin=0.5,
    )
    models = fetch_cost_models(product_id, db_path=db_path)
    assert len(models) == 1
    assert models[0]["gross_margin"] == 0.5


def test_portfolio_gap(db_path):
    add_portfolio_gap(
        "skin_booster", db_path=db_path, geography="Korea",
        recommended_action="license",
    )
    gaps = fetch_portfolio_gaps(db_path=db_path)
    assert len(gaps) == 1
    assert gaps[0]["recommended_action"] == "license"
