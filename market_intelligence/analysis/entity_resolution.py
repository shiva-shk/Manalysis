"""Clusters stored search results into canonical entities across every
query that has ever been run, not just a single search's results.

Uses the same matching rule as processing.deduplication (similar title
plus a matching identifier or company) so a result from a "Profhilo"
search and one from a later "hyaluronic acid" search still land in the
same entity if they clearly describe the same product.
"""

from processing.deduplication import title_similarity, SIMILARITY_THRESHOLD


def _same_entity(a: dict, b: dict) -> bool:
    if title_similarity(a.get("title"), b.get("title")) < SIMILARITY_THRESHOLD:
        return False

    if a.get("identifier") and b.get("identifier") and a["identifier"] == b["identifier"]:
        return True

    if a.get("company") and b.get("company") and a["company"].lower().strip() == b["company"].lower().strip():
        return True

    return False


def _build_clusters(rows: list[dict]) -> list[list[dict]]:
    clusters: list[list[dict]] = []
    for row in rows:
        match_index = None
        for i, cluster in enumerate(clusters):
            if any(_same_entity(row, member) for member in cluster):
                match_index = i
                break

        if match_index is None:
            clusters.append([row])
        else:
            clusters[match_index].append(row)
    return clusters


def cluster_entities(rows: list[dict]) -> list[dict]:
    """Groups rows into entities. Each entity carries its canonical title
    (the highest-evidence-score row's title), every distinct company,
    country, and source seen for it, and the member record count."""
    entities = []
    for cluster in _build_clusters(rows):
        best = max(cluster, key=lambda r: r.get("evidence_score") or 0)
        entities.append({
            "canonical_title": best.get("title"),
            "companies": sorted({r["company"] for r in cluster if r.get("company")}),
            "countries": sorted({r["country"] for r in cluster if r.get("country")}),
            "source_types": sorted({r["source_type"] for r in cluster if r.get("source_type")}),
            "record_count": len(cluster),
            "queries": sorted({r["query"] for r in cluster if r.get("query")}),
            "max_evidence_score": round(max((r.get("evidence_score") or 0) for r in cluster), 2),
        })

    entities.sort(key=lambda e: e["record_count"], reverse=True)
    return entities


def cluster_entities_with_members(rows: list[dict]) -> list[dict]:
    """Same clustering as cluster_entities, but keeps each cluster's raw
    member rows for the promotion workflow, which needs to turn every
    member's title/company/source into an alias or a piece of evidence."""
    entities = cluster_entities(rows)
    clusters = _build_clusters(rows)
    # _build_clusters and cluster_entities iterate `rows` identically, so
    # pairing them by position is safe as long as callers don't reorder
    # `entities` before matching members back up.
    by_title = {}
    for cluster in clusters:
        best = max(cluster, key=lambda r: r.get("evidence_score") or 0)
        by_title.setdefault(best.get("title"), []).append(cluster)

    for entity in entities:
        candidates = by_title.get(entity["canonical_title"], [])
        entity["members"] = candidates.pop(0) if candidates else []

    return entities
