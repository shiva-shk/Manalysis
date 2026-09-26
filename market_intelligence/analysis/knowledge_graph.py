"""Builds a NetworkX graph over the registry (products, companies,
ingredients, patents, clinical studies, regulatory records) for a
single product, matching the relationship shape from the design spec:

    Brand A
      |-- owned_by / manufactured_by / distributed_by -> Company X
      |-- contains -> Ingredient
      |-- approved_by -> Regulatory authority
      |-- studied_in -> Clinical trial
      `-- covered_by -> Patent

A relational database is the source of truth; this is a read-only view
built on demand from it, not a separate store to keep in sync.
"""

import networkx as nx

from database.registry_db import (
    fetch_clinical_studies,
    fetch_patents,
    fetch_product,
    fetch_product_companies,
    fetch_product_ingredients,
    fetch_regulatory_records,
)

ROLE_TO_RELATIONSHIP = {
    "brand_owner": "owned_by",
    "legal_manufacturer": "manufactured_by",
    "contract_manufacturer": "manufactured_by",
    "cdmo": "manufactured_by",
    "oem": "manufactured_by",
    "distributor": "distributed_by",
    "importer": "imported_by",
    "authorized_representative": "represented_by",
    "licensee": "licensed_to",
    "technology_owner": "technology_from",
}


def build_product_graph(product_id: int, db_path: str | None = None) -> nx.DiGraph:
    kwargs = {"db_path": db_path} if db_path else {}
    graph = nx.DiGraph()

    product = fetch_product(product_id, **kwargs)
    if product is None:
        return graph

    product_node = f"product:{product_id}"
    graph.add_node(product_node, label=product["canonical_name"], node_type="product")

    for link in fetch_product_companies(product_id, **kwargs):
        company_node = f"company:{link['company_id']}"
        relationship = ROLE_TO_RELATIONSHIP.get(link["role"], f"role:{link['role']}")
        graph.add_node(company_node, label=link["company_name"], node_type="company")
        graph.add_edge(product_node, company_node, relationship=relationship)

    for ingredient in fetch_product_ingredients(product_id, **kwargs):
        ingredient_node = f"ingredient:{ingredient['ingredient_id']}"
        graph.add_node(ingredient_node, label=ingredient["preferred_name"], node_type="ingredient")
        graph.add_edge(product_node, ingredient_node, relationship="contains")

    for record in fetch_regulatory_records(product_id, **kwargs):
        authority_node = f"authority:{record['jurisdiction']}:{record['authority'] or 'unknown'}"
        graph.add_node(authority_node, label=record["authority"] or record["jurisdiction"], node_type="authority")
        graph.add_edge(product_node, authority_node, relationship="approved_by", status=record["status"])

    for study in fetch_clinical_studies(product_id, **kwargs):
        study_node = f"study:{study['id']}"
        graph.add_node(study_node, label=study["registry_id"] or study["study_title"], node_type="clinical_study")
        graph.add_edge(product_node, study_node, relationship="studied_in")

    for patent in fetch_patents(product_id, **kwargs):
        patent_node = f"patent:{patent['id']}"
        graph.add_node(patent_node, label=patent["patent_number"], node_type="patent")
        graph.add_edge(product_node, patent_node, relationship="covered_by")

    return graph


def graph_to_edge_list(graph: nx.DiGraph) -> list[dict]:
    """Flattens a graph into rows a dataframe/table can render."""
    rows = []
    for source, target, data in graph.edges(data=True):
        rows.append({
            "from": graph.nodes[source].get("label", source),
            "relationship": data.get("relationship"),
            "to": graph.nodes[target].get("label", target),
            "to_type": graph.nodes[target].get("node_type"),
        })
    return rows


def graph_summary(graph: nx.DiGraph) -> dict:
    node_types = {}
    for _, data in graph.nodes(data=True):
        node_type = data.get("node_type", "unknown")
        node_types[node_type] = node_types.get(node_type, 0) + 1
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "node_types": node_types,
    }
