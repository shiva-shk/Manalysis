import os
import tempfile

import pytest

from database.registry_db import (
    add_clinical_study,
    add_competitor_profile,
    add_supplier,
    add_supplier_material,
    clinical_study_exists,
    create_product,
    fetch_clinical_studies,
    fetch_competitor_profiles,
    fetch_patents,
    fetch_suppliers,
    fetch_supplier_materials,
    upsert_company,
    upsert_ingredient,
    upsert_patent,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.remove(path)


def test_add_and_fetch_clinical_study(db_path):
    product_id = create_product("Example Filler", db_path=db_path)
    add_clinical_study(
        "A study of Example Filler", db_path=db_path,
        product_id=product_id, registry_name="ClinicalTrials.gov", registry_id="NCT00000001",
    )
    studies = fetch_clinical_studies(product_id, db_path=db_path)
    assert len(studies) == 1
    assert studies[0]["registry_id"] == "NCT00000001"


def test_clinical_study_exists(db_path):
    add_clinical_study(
        "A study", db_path=db_path, registry_id="NCT00000002",
    )
    assert clinical_study_exists("NCT00000002", db_path=db_path)
    assert not clinical_study_exists("NCT99999999", db_path=db_path)


def test_upsert_patent_is_idempotent(db_path):
    id_1 = upsert_patent("US1234567", db_path=db_path, title="Example patent")
    id_2 = upsert_patent("US1234567", db_path=db_path, title="Example patent")
    assert id_1 == id_2
    assert len(fetch_patents(db_path=db_path)) == 1


def test_supplier_and_material(db_path):
    supplier_id = add_supplier("Example Supplier Co", db_path=db_path, country="DE")
    ingredient_id = upsert_ingredient("Example Active", db_path=db_path)
    add_supplier_material(
        supplier_id, db_path=db_path, ingredient_id=ingredient_id,
        trade_name="ExampleGrade 100", catalog_number="EG-100",
    )
    suppliers = fetch_suppliers(db_path=db_path)
    assert len(suppliers) == 1

    materials = fetch_supplier_materials(supplier_id, db_path=db_path)
    assert len(materials) == 1
    assert materials[0]["ingredient_name"] == "Example Active"


def test_competitor_profile(db_path):
    company_id = upsert_company("Example Co", db_path=db_path)
    add_competitor_profile(
        company_id, db_path=db_path, strategic_segment="injectables",
        threat_level="high",
    )
    profiles = fetch_competitor_profiles(db_path=db_path)
    assert len(profiles) == 1
    assert profiles[0]["company_name"] == "Example Co"
    assert profiles[0]["threat_level"] == "high"
