import os
import tempfile

import pytest

from analysis.registry_search import search_registry
from database.registry_db import add_product_alias, create_product, upsert_company, upsert_ingredient


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.remove(path)


def test_search_matches_product_name(db_path):
    create_product("Profhilo", db_path=db_path)
    hits = search_registry("profhilo", db_path=db_path)
    assert any(h["entity_type"] == "product" for h in hits)


def test_search_matches_alias(db_path):
    product_id = create_product("Example Canonical Name", db_path=db_path)
    add_product_alias(product_id, "ASCE Plus SRLV", db_path=db_path)
    hits = search_registry("ASCE Plus", db_path=db_path)
    assert any("alias" in h["matched_on"] for h in hits)


def test_search_matches_company_and_ingredient(db_path):
    upsert_company("ExoCoBio Inc", db_path=db_path)
    upsert_ingredient("Rosa Damascena Callus Extracellular Vesicles", db_path=db_path)

    company_hits = search_registry("ExoCoBio", db_path=db_path)
    assert any(h["entity_type"] == "company" for h in company_hits)

    ingredient_hits = search_registry("Rosa Damascena", db_path=db_path)
    assert any(h["entity_type"] == "ingredient" for h in ingredient_hits)


def test_search_empty_query_returns_nothing(db_path):
    assert search_registry("", db_path=db_path) == []


def test_search_no_match_returns_empty(db_path):
    create_product("Profhilo", db_path=db_path)
    assert search_registry("completely unrelated term xyz", db_path=db_path) == []
