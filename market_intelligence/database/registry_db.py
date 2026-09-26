"""Access layer for the product/company/ingredient registry: the
"verified evidence" tables a person promotes search results into, as
opposed to the raw/normalized cache in database.db.

Every write here that isn't a lookup also expects a source, so a
registry record can always answer "where did this come from."
"""

import sqlite3
from datetime import datetime, timezone

from config import DB_PATH
from database.db import get_connection, init_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- companies ---

def upsert_company(canonical_name: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    with get_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM companies WHERE canonical_name = ?", (canonical_name,)
        ).fetchone()
        if existing:
            return existing["id"]

        cols = ["canonical_name", "created_at"] + list(fields.keys())
        vals = [canonical_name, _now()] + list(fields.values())
        conn.execute(
            f"INSERT INTO companies ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_companies(db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM companies ORDER BY canonical_name").fetchall()


# --- products ---

def create_product(canonical_name: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    cols = ["canonical_name", "created_at"] + list(fields.keys())
    vals = [canonical_name, _now()] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO products ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_products(db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM products ORDER BY canonical_name").fetchall()


def fetch_product(product_id: int, db_path: str = DB_PATH) -> sqlite3.Row | None:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()


# --- product aliases ---

def add_product_alias(product_id: int, alias_name: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    cols = ["product_id", "alias_name"] + list(fields.keys())
    vals = [product_id, alias_name] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO product_aliases ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_aliases(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM product_aliases WHERE product_id = ?", (product_id,)
        ).fetchall()


# --- product-company roles ---

def link_product_company(product_id: int, company_id: int, role: str,
                          db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    cols = ["product_id", "company_id", "role"] + list(fields.keys())
    vals = [product_id, company_id, role] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO product_companies ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_product_companies(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT pc.*, c.canonical_name AS company_name FROM product_companies pc "
            "JOIN companies c ON c.id = pc.company_id WHERE pc.product_id = ?",
            (product_id,),
        ).fetchall()


# --- ingredients ---

def upsert_ingredient(preferred_name: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    with get_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM ingredients WHERE preferred_name = ?", (preferred_name,)
        ).fetchone()
        if existing:
            return existing["id"]

        cols = ["preferred_name"] + list(fields.keys())
        vals = [preferred_name] + list(fields.values())
        conn.execute(
            f"INSERT INTO ingredients ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_ingredients(db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM ingredients ORDER BY preferred_name").fetchall()


def link_product_ingredient(product_id: int, ingredient_id: int,
                             db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    cols = ["product_id", "ingredient_id"] + list(fields.keys())
    vals = [product_id, ingredient_id] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO product_ingredients ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_product_ingredients(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT pi.*, i.preferred_name, i.inci_name, i.cas_number, i.material_family "
            "FROM product_ingredients pi JOIN ingredients i ON i.id = pi.ingredient_id "
            "WHERE pi.product_id = ?",
            (product_id,),
        ).fetchall()


# --- regulatory records ---

def add_regulatory_record(product_id: int, jurisdiction: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    cols = ["product_id", "jurisdiction"] + list(fields.keys())
    vals = [product_id, jurisdiction] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO regulatory_records ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_regulatory_records(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM regulatory_records WHERE product_id = ?", (product_id,)
        ).fetchall()


# --- field-level evidence / lineage ---

def add_field_evidence(entity_type: str, entity_id: int, field_name: str,
                        db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("retrieved_date", _now())
    cols = ["entity_type", "entity_id", "field_name"] + list(fields.keys())
    vals = [entity_type, entity_id, field_name] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO field_evidence ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_field_evidence(entity_type: str, entity_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM field_evidence WHERE entity_type = ? AND entity_id = ? "
            "ORDER BY field_name",
            (entity_type, entity_id),
        ).fetchall()


# --- clinical studies ---

def add_clinical_study(study_title: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("added_at", _now())
    cols = ["study_title"] + list(fields.keys())
    vals = [study_title] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO clinical_studies ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_clinical_studies(product_id: int | None = None, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        if product_id is not None:
            return conn.execute(
                "SELECT * FROM clinical_studies WHERE product_id = ? ORDER BY added_at DESC",
                (product_id,),
            ).fetchall()
        return conn.execute("SELECT * FROM clinical_studies ORDER BY added_at DESC").fetchall()


def clinical_study_exists(registry_id: str, db_path: str = DB_PATH) -> bool:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT 1 FROM clinical_studies WHERE registry_id = ?", (registry_id,)
        ).fetchone() is not None


# --- patents ---

def upsert_patent(patent_number: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("added_at", _now())
    with get_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM patents WHERE patent_number = ?", (patent_number,)
        ).fetchone()
        if existing:
            return existing["id"]

        cols = ["patent_number"] + list(fields.keys())
        vals = [patent_number] + list(fields.values())
        conn.execute(
            f"INSERT INTO patents ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_patents(product_id: int | None = None, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        if product_id is not None:
            return conn.execute(
                "SELECT * FROM patents WHERE product_id = ? ORDER BY publication_date DESC",
                (product_id,),
            ).fetchall()
        return conn.execute("SELECT * FROM patents ORDER BY added_at DESC").fetchall()


# --- trademarks ---

def upsert_trademark(brand_name: str, db_path: str = DB_PATH, **fields) -> int:
    """Deduplicated by (brand_name, jurisdiction, registration_number) —
    unlike patents, a brand name alone isn't unique (many companies can
    file the same word mark in different classes/jurisdictions), so the
    dedup key needs more than just the name."""
    init_db(db_path)
    fields.setdefault("added_at", _now())
    jurisdiction = fields.get("jurisdiction")
    registration_number = fields.get("registration_number")

    with get_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM trademarks WHERE brand_name = ? AND jurisdiction IS ? "
            "AND registration_number IS ?",
            (brand_name, jurisdiction, registration_number),
        ).fetchone()
        if existing:
            return existing["id"]

        cols = ["brand_name"] + list(fields.keys())
        vals = [brand_name] + list(fields.values())
        conn.execute(
            f"INSERT INTO trademarks ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_trademarks(company_id: int | None = None, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        if company_id is not None:
            return conn.execute(
                "SELECT * FROM trademarks WHERE company_id = ? ORDER BY added_at DESC",
                (company_id,),
            ).fetchall()
        return conn.execute("SELECT * FROM trademarks ORDER BY added_at DESC").fetchall()


# --- safety signals ---

def add_safety_signal(product_id: int, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("added_at", _now())
    cols = ["product_id"] + list(fields.keys())
    vals = [product_id] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO safety_signals ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_safety_signals(product_id: int | None = None, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        if product_id is not None:
            return conn.execute(
                "SELECT * FROM safety_signals WHERE product_id = ? ORDER BY signal_date DESC",
                (product_id,),
            ).fetchall()
        return conn.execute("SELECT * FROM safety_signals ORDER BY added_at DESC").fetchall()


# --- suppliers ---

def add_supplier(supplier_name: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("created_at", _now())
    cols = ["supplier_name"] + list(fields.keys())
    vals = [supplier_name] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO suppliers ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_suppliers(db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM suppliers ORDER BY supplier_name").fetchall()


def add_supplier_material(supplier_id: int, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    cols = ["supplier_id"] + list(fields.keys())
    vals = [supplier_id] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO supplier_materials ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_supplier_materials(supplier_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT sm.*, i.preferred_name AS ingredient_name FROM supplier_materials sm "
            "LEFT JOIN ingredients i ON i.id = sm.ingredient_id WHERE sm.supplier_id = ?",
            (supplier_id,),
        ).fetchall()


# --- competitor profiles ---

def add_competitor_profile(company_id: int, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("last_reviewed", _now())
    cols = ["company_id"] + list(fields.keys())
    vals = [company_id] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO competitor_profiles ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_competitor_profiles(db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT cp.*, c.canonical_name AS company_name FROM competitor_profiles cp "
            "JOIN companies c ON c.id = cp.company_id ORDER BY cp.last_reviewed DESC"
        ).fetchall()


# --- QTPP / CQA / CPP / control strategy ---

def add_qttp(product_id: int, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("created_at", _now())
    cols = ["product_id"] + list(fields.keys())
    vals = [product_id] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO qttp ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})", vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_qttp(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM qttp WHERE product_id = ? ORDER BY created_at DESC", (product_id,)
        ).fetchall()


def add_cqa(product_id: int, attribute_name: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    cols = ["product_id", "attribute_name"] + list(fields.keys())
    vals = [product_id, attribute_name] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO critical_quality_attributes ({', '.join(cols)}) "
            f"VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_cqas(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM critical_quality_attributes WHERE product_id = ?", (product_id,)
        ).fetchall()


def add_cpp(product_id: int, parameter_name: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    cols = ["product_id", "parameter_name"] + list(fields.keys())
    vals = [product_id, parameter_name] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO critical_process_parameters ({', '.join(cols)}) "
            f"VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_cpps(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM critical_process_parameters WHERE product_id = ?", (product_id,)
        ).fetchall()


def add_control(product_id: int, test_or_control: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    cols = ["product_id", "test_or_control"] + list(fields.keys())
    vals = [product_id, test_or_control] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO control_strategy ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_controls(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM control_strategy WHERE product_id = ?", (product_id,)
        ).fetchall()


# --- risk assessments ---

def add_risk_assessment(risk_category: str, risk_event: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("created_at", _now())
    cols = ["risk_category", "risk_event"] + list(fields.keys())
    vals = [risk_category, risk_event] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO risk_assessments ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_risk_assessments(product_id: int | None = None, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        if product_id is not None:
            return conn.execute(
                "SELECT * FROM risk_assessments WHERE product_id = ? "
                "ORDER BY risk_priority_number DESC",
                (product_id,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM risk_assessments ORDER BY risk_priority_number DESC"
        ).fetchall()


# --- stage-gate decisions ---

def add_stage_gate_decision(product_id: int, stage: str, decision: str,
                             db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("decision_date", _now())
    cols = ["product_id", "stage", "decision"] + list(fields.keys())
    vals = [product_id, stage, decision] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO stage_gate_decisions ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_stage_gate_decisions(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM stage_gate_decisions WHERE product_id = ? ORDER BY decision_date DESC",
            (product_id,),
        ).fetchall()


def current_stage(product_id: int, db_path: str = DB_PATH) -> sqlite3.Row | None:
    """Most recent stage-gate decision for a product, or None if it has
    never been through a gate."""
    decisions = fetch_stage_gate_decisions(product_id, db_path=db_path)
    return decisions[0] if decisions else None


# --- cost model ---

def add_cost_model(product_id: int, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("created_at", _now())
    cols = ["product_id"] + list(fields.keys())
    vals = [product_id] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO cost_models ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_cost_models(product_id: int, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM cost_models WHERE product_id = ? ORDER BY created_at DESC",
            (product_id,),
        ).fetchall()


# --- portfolio gaps ---

def add_portfolio_gap(category: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("created_at", _now())
    cols = ["category"] + list(fields.keys())
    vals = [category] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO portfolio_gaps ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_portfolio_gaps(db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM portfolio_gaps ORDER BY created_at DESC").fetchall()


# --- audit log ---

def log_audit_event(actor: str, action: str, entity_type: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("created_at", _now())
    cols = ["actor", "action", "entity_type"] + list(fields.keys())
    vals = [actor, action, entity_type] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO audit_log ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})", vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_audit_log(entity_type: str | None = None, entity_id: int | None = None,
                     limit: int = 200, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        if entity_type and entity_id is not None:
            return conn.execute(
                "SELECT * FROM audit_log WHERE entity_type = ? AND entity_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (entity_type, entity_id, limit),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()


# --- change events ---

def log_change_event(entity_type: str, change_type: str, db_path: str = DB_PATH, **fields) -> int:
    init_db(db_path)
    fields.setdefault("change_date", _now())
    cols = ["entity_type", "change_type"] + list(fields.keys())
    vals = [entity_type, change_type] + list(fields.values())
    with get_connection(db_path) as conn:
        conn.execute(
            f"INSERT INTO change_events ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})", vals,
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_change_events(limit: int = 200, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM change_events ORDER BY change_date DESC LIMIT ?", (limit,)
        ).fetchall()
