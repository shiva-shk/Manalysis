import os
import tempfile

import pytest

from database.registry_db import (
    add_field_evidence,
    add_product_alias,
    add_regulatory_record,
    create_product,
    fetch_aliases,
    fetch_companies,
    fetch_field_evidence,
    fetch_ingredients,
    fetch_product_companies,
    fetch_product_ingredients,
    fetch_products,
    fetch_regulatory_records,
    link_product_company,
    link_product_ingredient,
    upsert_company,
    upsert_ingredient,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.remove(path)


def test_create_product_and_fetch(db_path):
    product_id = create_product("Example Filler", db_path=db_path, product_type="dermal_filler")
    products = fetch_products(db_path=db_path)
    assert len(products) == 1
    assert products[0]["canonical_name"] == "Example Filler"
    assert products[0]["id"] == product_id


def test_upsert_company_is_idempotent(db_path):
    id_1 = upsert_company("Example Co", db_path=db_path, country="KR")
    id_2 = upsert_company("Example Co", db_path=db_path, country="KR")
    assert id_1 == id_2
    assert len(fetch_companies(db_path=db_path)) == 1


def test_product_company_role_link(db_path):
    product_id = create_product("Example Filler", db_path=db_path)
    company_id = upsert_company("Example Co", db_path=db_path)
    link_product_company(product_id, company_id, role="brand_owner", db_path=db_path)

    links = fetch_product_companies(product_id, db_path=db_path)
    assert len(links) == 1
    assert links[0]["role"] == "brand_owner"
    assert links[0]["company_name"] == "Example Co"


def test_product_alias(db_path):
    product_id = create_product("Example Filler", db_path=db_path)
    add_product_alias(product_id, "Example Filler Plus", alias_type="brand_name", db_path=db_path)
    aliases = fetch_aliases(product_id, db_path=db_path)
    assert len(aliases) == 1
    assert aliases[0]["alias_name"] == "Example Filler Plus"


def test_ingredient_upsert_and_link(db_path):
    product_id = create_product("Example Filler", db_path=db_path)
    ingredient_id = upsert_ingredient(
        "Hyaluronic Acid", db_path=db_path, cas_number="9067-32-7"
    )
    upsert_ingredient("Hyaluronic Acid", db_path=db_path)  # idempotent
    assert len(fetch_ingredients(db_path=db_path)) == 1

    link_product_ingredient(
        product_id, ingredient_id, ingredient_role="active_substance",
        concentration="20", concentration_unit="mg/mL", db_path=db_path,
    )
    linked = fetch_product_ingredients(product_id, db_path=db_path)
    assert len(linked) == 1
    assert linked[0]["preferred_name"] == "Hyaluronic Acid"
    assert linked[0]["cas_number"] == "9067-32-7"


def test_regulatory_record(db_path):
    product_id = create_product("Example Filler", db_path=db_path)
    add_regulatory_record(
        product_id, jurisdiction="US", db_path=db_path,
        authority="FDA", status="not_found",
    )
    records = fetch_regulatory_records(product_id, db_path=db_path)
    assert len(records) == 1
    assert records[0]["jurisdiction"] == "US"


def test_field_evidence_lineage(db_path):
    product_id = create_product("Example Filler", db_path=db_path)
    add_field_evidence(
        "product", product_id, "company", db_path=db_path,
        field_value="Example Co", source_name="openFDA", confidence=0.95,
    )
    evidence = fetch_field_evidence("product", product_id, db_path=db_path)
    assert len(evidence) == 1
    assert evidence[0]["field_value"] == "Example Co"
    assert evidence[0]["verification_status"] == "machine_extracted"
