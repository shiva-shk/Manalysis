"""Builds a single product/entity profile out of stored search results.

This is a lightweight stand-in for full entity resolution: it groups
already-deduplicated rows by a shared title or company rather than
running fuzzy matching across the whole database, and it is explicit
about that so a profile is never mistaken for a verified single record.
"""

import pandas as pd

SECTION_ENTITY_TYPES = {
    "regulatory": ["medical_device", "drug_product", "eu_medicine"],
    "clinical": ["clinical_study"],
    "patents": ["patent"],
    "literature": ["publication"],
}


def build_profile(rows: list[dict], focus_title: str) -> dict:
    df = pd.DataFrame(rows)
    if df.empty:
        return {"focus_title": focus_title, "sections": {}, "companies": [], "countries": []}

    matches = df[df["title"].str.lower() == focus_title.lower().strip()]
    if matches.empty:
        matches = df

    sections = {}
    for section, entity_types in SECTION_ENTITY_TYPES.items():
        section_rows = matches[matches["entity_type"].isin(entity_types)]
        sections[section] = section_rows.to_dict("records")

    return {
        "focus_title": focus_title,
        "sections": sections,
        "companies": sorted(matches["company"].dropna().unique().tolist()),
        "countries": sorted(matches["country"].dropna().unique().tolist()),
        "source_count": len(matches),
        "avg_evidence_score": round(matches["evidence_score"].mean(), 2) if "evidence_score" in matches else None,
    }
