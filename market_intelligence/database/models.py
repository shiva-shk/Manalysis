"""SQLite schema for cached search results.

Kept as one denormalized table for the MVP; the product/company/ingredient/
regulatory/clinical/patent/market tables from the full design can be split
out later once real entity resolution is in place.
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS search_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    query_type TEXT,
    title TEXT NOT NULL,
    entity_type TEXT,
    entity_name TEXT,
    company TEXT,
    country TEXT,
    category TEXT,
    regulatory_status TEXT,
    summary TEXT,
    identifier TEXT,
    source_name TEXT,
    source_url TEXT,
    source_type TEXT,
    retrieved_at TEXT,
    evidence_score REAL,
    confidence_label TEXT
);

CREATE INDEX IF NOT EXISTS idx_search_results_query ON search_results(query);
CREATE INDEX IF NOT EXISTS idx_search_results_source_type ON search_results(source_type);
"""
