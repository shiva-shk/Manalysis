from analysis.entity_resolution import cluster_entities

ROWS = [
    {
        "title": "Example Filler", "company": "Example Co", "country": "France",
        "source_type": "official", "query": "example filler", "evidence_score": 0.9,
        "identifier": "K111",
    },
    {
        "title": "Example Filler", "company": "Example Co", "country": "Belgium",
        "source_type": "scientific", "query": "hyaluronic acid", "evidence_score": 0.8,
        "identifier": None,
    },
    {
        "title": "Totally Different Product", "company": "Other Co", "country": "Germany",
        "source_type": "official", "query": "other co", "evidence_score": 0.7,
        "identifier": "K222",
    },
]


def test_clusters_same_product_across_queries():
    entities = cluster_entities(ROWS)
    assert len(entities) == 2
    example_entity = next(e for e in entities if e["canonical_title"] == "Example Filler")
    assert example_entity["record_count"] == 2
    assert set(example_entity["queries"]) == {"example filler", "hyaluronic acid"}


def test_keeps_distinct_products_separate():
    entities = cluster_entities(ROWS)
    titles = {e["canonical_title"] for e in entities}
    assert "Totally Different Product" in titles


def test_empty_input_returns_no_entities():
    assert cluster_entities([]) == []
