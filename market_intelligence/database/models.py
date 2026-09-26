"""SQLite schema for cached search results plus the normalized product
registry (products, companies, ingredients) built on top of it.

search_results / market_data / document_sources are the raw+normalized
cache connectors write to directly. The registry tables below are the
"verified evidence" layer: an analyst promotes a cluster of search_results
rows into a canonical product/company record, and field_evidence records
where every promoted field actually came from. Nothing in the registry
is written by a connector automatically, only by the promotion workflow
in processing/entity_promotion.py, so a registry record always means a
person looked at it.
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

CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    subcategory TEXT,
    region TEXT,
    year INTEGER,
    market_value REAL,
    currency TEXT,
    volume REAL,
    market_share REAL,
    growth_rate REAL,
    forecast_year INTEGER,
    source TEXT NOT NULL,
    source_url TEXT,
    definition TEXT,
    confidence_score REAL,
    uploaded_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_market_data_category ON market_data(category, region);

CREATE TABLE IF NOT EXISTS document_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    page_number INTEGER,
    extracted_text TEXT,
    ingredient_mentions TEXT,
    company_mentions TEXT,
    source_type TEXT,
    confidence REAL,
    uploaded_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_document_sources_file ON document_sources(file_name);

-- Product/company registry (the "verified evidence" layer) --

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL,
    legal_name TEXT,
    parent_company TEXT,
    company_type TEXT,
    country TEXT,
    website TEXT,
    verification_status TEXT DEFAULT 'awaiting_review',
    created_at TEXT,
    UNIQUE(canonical_name)
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL,
    brand_name TEXT,
    product_family TEXT,
    product_type TEXT,
    regulatory_category TEXT,
    route TEXT,
    intended_use TEXT,
    country_of_origin TEXT,
    launch_year INTEGER,
    status TEXT DEFAULT 'awaiting_review',
    identity_confidence REAL,
    last_verified TEXT,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_products_canonical_name ON products(canonical_name);

CREATE TABLE IF NOT EXISTS product_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    alias_name TEXT NOT NULL,
    alias_type TEXT,
    language TEXT,
    country TEXT,
    source TEXT,
    source_url TEXT,
    verified INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_product_aliases_product ON product_aliases(product_id);
CREATE INDEX IF NOT EXISTS idx_product_aliases_name ON product_aliases(alias_name);

CREATE TABLE IF NOT EXISTS product_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    company_id INTEGER NOT NULL REFERENCES companies(id),
    role TEXT NOT NULL,
    country TEXT,
    registration_number TEXT,
    source_url TEXT,
    confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_product_companies_product ON product_companies(product_id);

CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preferred_name TEXT NOT NULL,
    inci_name TEXT,
    chemical_name TEXT,
    cas_number TEXT,
    ec_number TEXT,
    material_family TEXT,
    ingredient_function TEXT,
    synonyms TEXT,
    regulatory_notes TEXT,
    source_url TEXT,
    UNIQUE(preferred_name)
);

CREATE TABLE IF NOT EXISTS product_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    ingredient_role TEXT,
    declared_name TEXT,
    concentration TEXT,
    concentration_unit TEXT,
    concentration_type TEXT DEFAULT 'not_disclosed',
    source_document TEXT,
    confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_product_ingredients_product ON product_ingredients(product_id);
CREATE INDEX IF NOT EXISTS idx_product_ingredients_ingredient ON product_ingredients(ingredient_id);

CREATE TABLE IF NOT EXISTS regulatory_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    jurisdiction TEXT NOT NULL,
    authority TEXT,
    regulatory_category TEXT,
    classification TEXT,
    registration_number TEXT,
    applicant TEXT,
    manufacturer TEXT,
    indication TEXT,
    status TEXT,
    approval_date TEXT,
    source_url TEXT,
    source_type TEXT,
    verification_date TEXT
);

CREATE INDEX IF NOT EXISTS idx_regulatory_records_product ON regulatory_records(product_id);
CREATE INDEX IF NOT EXISTS idx_regulatory_records_jurisdiction ON regulatory_records(jurisdiction);

CREATE TABLE IF NOT EXISTS field_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    field_value TEXT,
    source_id TEXT,
    source_name TEXT,
    source_url TEXT,
    document_id INTEGER,
    page_number INTEGER,
    retrieved_date TEXT,
    confidence REAL,
    verification_status TEXT DEFAULT 'machine_extracted',
    analyst_comment TEXT
);

CREATE INDEX IF NOT EXISTS idx_field_evidence_entity ON field_evidence(entity_type, entity_id);
"""
