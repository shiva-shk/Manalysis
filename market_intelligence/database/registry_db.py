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
