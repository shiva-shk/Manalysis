import os
import tempfile

import pytest

from database.registry_db import (
    fetch_audit_log,
    fetch_change_events,
    log_audit_event,
    log_change_event,
)
from processing.entity_promotion import promote_cluster


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.remove(path)


def test_log_and_fetch_audit_event(db_path):
    log_audit_event("tester", "manual_test", "product", db_path=db_path, entity_id=1, details="testing")
    events = fetch_audit_log(db_path=db_path)
    assert len(events) == 1
    assert events[0]["actor"] == "tester"
    assert events[0]["action"] == "manual_test"


def test_fetch_audit_log_filters_by_entity(db_path):
    log_audit_event("tester", "action_a", "product", db_path=db_path, entity_id=1)
    log_audit_event("tester", "action_b", "product", db_path=db_path, entity_id=2)
    events = fetch_audit_log("product", 1, db_path=db_path)
    assert len(events) == 1
    assert events[0]["action"] == "action_a"


def test_promote_cluster_writes_audit_event(db_path):
    members = [{
        "title": "Example Filler", "company": "Example Co", "country": "France",
        "entity_type": "medical_device", "category": "class-iii",
        "regulatory_status": "on-the-market", "identifier": "K123456",
        "source_name": "openFDA", "source_url": "https://example.com",
        "source_type": "official", "evidence_score": 0.95,
    }]
    product_id = promote_cluster("Example Filler", members, analyst="tester", db_path=db_path)
    events = fetch_audit_log("product", product_id, db_path=db_path)
    assert len(events) == 1
    assert events[0]["action"] == "promote_cluster"
    assert events[0]["actor"] == "tester"


def test_log_and_fetch_change_event(db_path):
    log_change_event(
        "search_result", "new_product", db_path=db_path,
        new_value="NCT00000001", source="ClinicalTrials.gov",
    )
    events = fetch_change_events(db_path=db_path)
    assert len(events) == 1
    assert events[0]["change_type"] == "new_product"
    assert events[0]["review_status"] == "awaiting_review"
