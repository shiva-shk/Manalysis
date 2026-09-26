import os
import tempfile

import pytest

from database.registry_db import (
    fetch_aliases,
    fetch_clinical_studies,
    fetch_field_evidence,
    fetch_patents,
    fetch_product_companies,
    fetch_regulatory_records,
)
from processing.entity_promotion import promote_cluster, registry_completeness

MEMBERS = [
    {
        "title": "Example Filler", "company": "Example Co", "country": "France",
        "entity_type": "medical_device", "category": "class-iii",
        "regulatory_status": "on-the-market", "identifier": "K123456",
        "source_name": "openFDA (510k devices)", "source_url": "https://example.com/1",
        "source_type": "official", "evidence_score": 0.95,
    },
    {
        "title": "Example Filler Injectable", "company": "Example Co", "country": "Belgium",
        "entity_type": "publication", "category": None,
        "regulatory_status": None, "identifier": None,
        "source_name": "PubMed / Europe PMC", "source_url": "https://example.com/2",
        "source_type": "scientific", "evidence_score": 0.45,
    },
    {
        "title": "Trial of Example Filler for scar treatment", "company": "Example Hospital",
        "country": "Germany", "entity_type": "clinical_study", "category": "clinical_trial",
        "regulatory_status": "RECRUITING", "identifier": "NCT01234567",
        "entity_name": "Example Filler injection",
        "source_name": "ClinicalTrials.gov", "source_url": "https://example.com/3",
        "source_type": "official", "evidence_score": 0.95,
    },
    {
        "title": "Cross-linked composition for Example Filler", "company": "Example Co",
        "country": "EP", "entity_type": "patent", "category": "patent",
        "regulatory_status": "Published 20200101", "identifier": "EP1234567A1",
        "source_name": "EPO Open Patent Services", "source_url": "https://example.com/4",
        "source_type": "official", "evidence_score": 0.90,
    },
]


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.remove(path)


def test_promote_cluster_creates_product_alias_and_company(db_path):
    product_id = promote_cluster("Example Filler", MEMBERS, analyst="tester", db_path=db_path)

    aliases = fetch_aliases(product_id, db_path=db_path)
    alias_names = {a["alias_name"] for a in aliases}
    assert "Example Filler" in alias_names
    assert "Example Filler Injectable" in alias_names

    companies = fetch_product_companies(product_id, db_path=db_path)
    company_names = {c["company_name"] for c in companies}
    assert company_names == {"Example Co", "Example Hospital"}


def test_promote_cluster_creates_regulatory_record_for_official_member(db_path):
    product_id = promote_cluster("Example Filler", MEMBERS, analyst="tester", db_path=db_path)
    records = fetch_regulatory_records(product_id, db_path=db_path)
    assert len(records) == 1
    assert records[0]["registration_number"] == "K123456"
    assert records[0]["jurisdiction"] == "US"


def test_promote_cluster_writes_field_evidence(db_path):
    product_id = promote_cluster("Example Filler", MEMBERS, analyst="tester", db_path=db_path)
    evidence = fetch_field_evidence("product", product_id, db_path=db_path)
    assert len(evidence) > 0
    assert all("tester" in (e["analyst_comment"] or "") for e in evidence)


def test_registry_completeness_flags_missing_regulatory_evidence(db_path):
    discovery_only = [{
        "title": "Unverified Product", "company": "Some Co", "country": None,
        "entity_type": "publication", "category": None, "regulatory_status": None,
        "identifier": None, "source_name": "Google", "source_url": "https://example.com",
        "source_type": "discovery", "evidence_score": 0.4,
    }]
    product_id = promote_cluster("Unverified Product", discovery_only, db_path=db_path)
    completeness = registry_completeness(product_id, db_path=db_path)
    assert completeness["has_any_regulatory_evidence"] is False


def test_promote_empty_cluster_raises(db_path):
    with pytest.raises(ValueError):
        promote_cluster("Nothing", [], db_path=db_path)


def test_promote_cluster_creates_clinical_study(db_path):
    product_id = promote_cluster("Example Filler", MEMBERS, analyst="tester", db_path=db_path)
    studies = fetch_clinical_studies(product_id, db_path=db_path)
    assert len(studies) == 1
    assert studies[0]["registry_id"] == "NCT01234567"
    assert studies[0]["sponsor"] == "Example Hospital"


def test_promote_cluster_creates_patent_record(db_path):
    product_id = promote_cluster("Example Filler", MEMBERS, analyst="tester", db_path=db_path)
    patents = fetch_patents(product_id, db_path=db_path)
    assert len(patents) == 1
    assert patents[0]["patent_number"] == "EP1234567A1"


def test_registry_completeness_counts_studies_and_patents(db_path):
    product_id = promote_cluster("Example Filler", MEMBERS, analyst="tester", db_path=db_path)
    completeness = registry_completeness(product_id, db_path=db_path)
    assert completeness["clinical_study_count"] == 1
    assert completeness["patent_count"] == 1
