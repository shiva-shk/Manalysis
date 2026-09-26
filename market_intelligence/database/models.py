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
    country TEXT,
    scope_level TEXT DEFAULT 'global',
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
    former_names TEXT,
    parent_company TEXT,
    company_type TEXT,
    country TEXT,
    address TEXT,
    website TEXT,
    manufacturing_sites TEXT,
    certifications TEXT,
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
    product_subtype TEXT,
    regulatory_category TEXT,
    route TEXT,
    intended_use TEXT,
    target_area TEXT,
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
    korean_name TEXT,
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
    page_number INTEGER,
    verification_status TEXT DEFAULT 'machine_extracted',
    confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_product_ingredients_product ON product_ingredients(product_id);
CREATE INDEX IF NOT EXISTS idx_product_ingredients_ingredient ON product_ingredients(ingredient_id);

CREATE TABLE IF NOT EXISTS regulatory_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    jurisdiction TEXT NOT NULL,
    authority TEXT,
    product_category TEXT,
    regulatory_category TEXT,
    classification TEXT,
    registration_number TEXT,
    approval_number TEXT,
    notification_number TEXT,
    applicant TEXT,
    manufacturer TEXT,
    authorized_representative TEXT,
    indication TEXT,
    claim_type TEXT,
    status TEXT,
    approval_date TEXT,
    expiry_date TEXT,
    source_url TEXT,
    source_document TEXT,
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

CREATE TABLE IF NOT EXISTS clinical_studies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    ingredient_id INTEGER REFERENCES ingredients(id),
    registry_name TEXT,
    registry_id TEXT,
    study_title TEXT NOT NULL,
    study_type TEXT,
    status TEXT,
    intervention TEXT,
    route TEXT,
    dose TEXT,
    population TEXT,
    sample_size INTEGER,
    condition_summary TEXT,
    primary_outcome TEXT,
    sponsor TEXT,
    country TEXT,
    publication_id TEXT,
    evidence_level TEXT,
    source_url TEXT,
    added_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_clinical_studies_product ON clinical_studies(product_id);
CREATE INDEX IF NOT EXISTS idx_clinical_studies_registry_id ON clinical_studies(registry_id);

CREATE TABLE IF NOT EXISTS patents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    company_id INTEGER REFERENCES companies(id),
    patent_number TEXT NOT NULL,
    application_number TEXT,
    patent_family TEXT,
    jurisdiction TEXT,
    title TEXT,
    applicant TEXT,
    inventors TEXT,
    priority_date TEXT,
    publication_date TEXT,
    expiration_date TEXT,
    legal_status TEXT,
    patent_type TEXT,
    claim_summary TEXT,
    source_url TEXT,
    added_at TEXT,
    UNIQUE(patent_number)
);

CREATE INDEX IF NOT EXISTS idx_patents_product ON patents(product_id);

CREATE TABLE IF NOT EXISTS trademarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    jurisdiction TEXT,
    application_number TEXT,
    registration_number TEXT,
    status TEXT,
    goods_and_services TEXT,
    source_url TEXT,
    added_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_trademarks_brand_name ON trademarks(brand_name);
CREATE INDEX IF NOT EXISTS idx_trademarks_company ON trademarks(company_id);

CREATE TABLE IF NOT EXISTS safety_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    jurisdiction TEXT,
    signal_type TEXT,
    severity TEXT,
    description TEXT,
    signal_date TEXT,
    source_url TEXT,
    source_type TEXT,
    added_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_safety_signals_product ON safety_signals(product_id);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    supplier_name TEXT NOT NULL,
    supplier_type TEXT,
    material_category TEXT,
    country TEXT,
    gmp_status TEXT,
    iso_certifications TEXT,
    regulatory_regions TEXT,
    technical_capability TEXT,
    notes TEXT,
    source_url TEXT,
    verification_status TEXT DEFAULT 'awaiting_review',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS supplier_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    ingredient_id INTEGER REFERENCES ingredients(id),
    trade_name TEXT,
    grade_name TEXT,
    catalog_number TEXT,
    minimum_order_quantity TEXT,
    price TEXT,
    currency TEXT,
    lead_time TEXT,
    coa_available INTEGER DEFAULT 0,
    source_url TEXT
);

CREATE INDEX IF NOT EXISTS idx_supplier_materials_supplier ON supplier_materials(supplier_id);

CREATE TABLE IF NOT EXISTS competitor_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    product_id INTEGER REFERENCES products(id),
    strategic_segment TEXT,
    target_customer TEXT,
    price_position TEXT,
    clinical_positioning TEXT,
    technology_position TEXT,
    geographic_presence TEXT,
    evidence_strength TEXT,
    competitive_advantage TEXT,
    competitive_weakness TEXT,
    threat_level TEXT,
    analyst TEXT,
    last_reviewed TEXT
);

CREATE INDEX IF NOT EXISTS idx_competitor_profiles_company ON competitor_profiles(company_id);

-- Formulation-development framework (QTPP / CQA / CPP / control strategy) --

CREATE TABLE IF NOT EXISTS qttp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    dosage_form TEXT,
    route TEXT,
    strength TEXT,
    intended_use TEXT,
    target_population TEXT,
    container_closure TEXT,
    stability_target TEXT,
    sterility_requirement TEXT,
    regulatory_target TEXT,
    notes TEXT,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_qttp_product ON qttp(product_id);

CREATE TABLE IF NOT EXISTS critical_quality_attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    attribute_name TEXT NOT NULL,
    attribute_category TEXT,
    target TEXT,
    acceptable_range TEXT,
    criticality TEXT,
    rationale TEXT,
    analytical_method TEXT,
    risk_level TEXT
);

CREATE INDEX IF NOT EXISTS idx_cqa_product ON critical_quality_attributes(product_id);

CREATE TABLE IF NOT EXISTS critical_process_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    process_step TEXT,
    parameter_name TEXT NOT NULL,
    target TEXT,
    acceptable_range TEXT,
    criticality TEXT,
    monitoring_method TEXT,
    control_strategy TEXT
);

CREATE INDEX IF NOT EXISTS idx_cpp_product ON critical_process_parameters(product_id);

CREATE TABLE IF NOT EXISTS control_strategy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    material_attribute TEXT,
    process_parameter TEXT,
    test_or_control TEXT NOT NULL,
    acceptance_criteria TEXT,
    sampling_plan TEXT,
    release_or_in_process TEXT,
    responsible_function TEXT
);

CREATE INDEX IF NOT EXISTS idx_control_strategy_product ON control_strategy(product_id);

-- Risk management --

CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    risk_category TEXT NOT NULL,
    risk_event TEXT NOT NULL,
    cause TEXT,
    effect TEXT,
    severity INTEGER,
    occurrence INTEGER,
    detectability INTEGER,
    risk_priority_number INTEGER,
    existing_controls TEXT,
    additional_controls TEXT,
    residual_risk TEXT,
    owner TEXT,
    status TEXT DEFAULT 'open',
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_risk_assessments_product ON risk_assessments(product_id);

-- Stage-gate workflow --

CREATE TABLE IF NOT EXISTS stage_gate_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    stage TEXT NOT NULL,
    decision TEXT NOT NULL,
    criteria TEXT,
    evidence TEXT,
    open_risks TEXT,
    required_actions TEXT,
    decision_owner TEXT,
    decision_date TEXT
);

CREATE INDEX IF NOT EXISTS idx_stage_gate_product ON stage_gate_decisions(product_id);

-- Cost model --

CREATE TABLE IF NOT EXISTS cost_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    scenario TEXT DEFAULT 'base_case',
    material_cost REAL,
    packaging_cost REAL,
    manufacturing_cost REAL,
    analytical_cost REAL,
    regulatory_cost REAL,
    distribution_cost REAL,
    estimated_cogs REAL,
    target_price REAL,
    gross_margin REAL,
    break_even_volume REAL,
    currency TEXT DEFAULT 'USD',
    assumptions TEXT,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_cost_models_product ON cost_models(product_id);

-- Portfolio-gap analysis --

CREATE TABLE IF NOT EXISTS portfolio_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    customer_segment TEXT,
    geography TEXT,
    indication TEXT,
    current_coverage TEXT,
    competitor_coverage TEXT,
    market_attractiveness TEXT,
    internal_capability TEXT,
    recommended_action TEXT,
    analyst TEXT,
    created_at TEXT
);

-- Audit trail and change monitoring --
-- No login system sits in front of this app (single-machine tool, no
-- session/auth infrastructure), so "actor" is a free-text name someone
-- types in, not an authenticated identity. It's provenance, not access
-- control — good enough to answer "who logged this," not "who is
-- allowed to."

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    details TEXT,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);

CREATE TABLE IF NOT EXISTS change_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    change_date TEXT,
    source TEXT,
    change_type TEXT,
    review_status TEXT DEFAULT 'awaiting_review'
);

CREATE INDEX IF NOT EXISTS idx_change_events_entity ON change_events(entity_type, entity_id);
"""
