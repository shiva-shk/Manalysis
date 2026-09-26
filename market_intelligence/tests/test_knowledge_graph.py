import os
import tempfile

import pytest

from analysis.knowledge_graph import build_product_graph, graph_summary, graph_to_edge_list
from database.registry_db import (
    add_clinical_study,
    add_regulatory_record,
    create_product,
    link_product_company,
    link_product_ingredient,
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


def test_build_product_graph_includes_all_relationship_types(db_path):
    product_id = create_product("Example Filler", db_path=db_path)
    company_id = upsert_company("Example Co", db_path=db_path)
    link_product_company(product_id, company_id, role="legal_manufacturer", db_path=db_path)

    ingredient_id = upsert_ingredient("Hyaluronic Acid", db_path=db_path)
    link_product_ingredient(product_id, ingredient_id, db_path=db_path)

    add_regulatory_record(product_id, jurisdiction="US", db_path=db_path, authority="FDA", status="cleared")
    add_clinical_study("A study", db_path=db_path, product_id=product_id, registry_id="NCT00000001")
    upsert_patent("US1234567", db_path=db_path, product_id=product_id)

    graph = build_product_graph(product_id, db_path=db_path)
    summary = graph_summary(graph)

    assert summary["node_types"]["company"] == 1
    assert summary["node_types"]["ingredient"] == 1
    assert summary["node_types"]["authority"] == 1
    assert summary["node_types"]["clinical_study"] == 1
    assert summary["node_types"]["patent"] == 1
    assert summary["edge_count"] == 5


def test_manufacturer_role_maps_to_manufactured_by(db_path):
    product_id = create_product("Example Filler", db_path=db_path)
    company_id = upsert_company("Example Co", db_path=db_path)
    link_product_company(product_id, company_id, role="legal_manufacturer", db_path=db_path)

    graph = build_product_graph(product_id, db_path=db_path)
    edges = graph_to_edge_list(graph)
    assert edges[0]["relationship"] == "manufactured_by"


def test_empty_product_graph_has_no_edges(db_path):
    product_id = create_product("Lonely Product", db_path=db_path)
    graph = build_product_graph(product_id, db_path=db_path)
    assert graph_summary(graph)["edge_count"] == 0


def test_unknown_product_returns_empty_graph(db_path):
    graph = build_product_graph(99999, db_path=db_path)
    assert graph.number_of_nodes() == 0
