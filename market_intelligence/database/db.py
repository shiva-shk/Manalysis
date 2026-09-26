"""Thin sqlite3 access layer: create schema, save a search run, read history."""

import sqlite3
from contextlib import contextmanager

from config import DB_PATH
from database.models import SCHEMA
from processing.evidence_scoring import confidence_label
from processing.market_data import ALL_FIELDS


@contextmanager
def get_connection(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# Columns added after a table already shipped. CREATE TABLE IF NOT EXISTS
# in SCHEMA only creates the table on a fresh database — an existing
# market_intelligence.db from before these columns existed needs them
# added explicitly, hence this small guarded migration list instead of a
# full migration framework for what's still a single-file local cache.
COLUMN_MIGRATIONS = [
    ("market_data", "country", "TEXT"),
    ("market_data", "scope_level", "TEXT DEFAULT 'global'"),
    ("companies", "former_names", "TEXT"),
    ("companies", "address", "TEXT"),
    ("companies", "manufacturing_sites", "TEXT"),
    ("companies", "certifications", "TEXT"),
    ("products", "product_subtype", "TEXT"),
    ("products", "target_area", "TEXT"),
    ("ingredients", "korean_name", "TEXT"),
    ("product_ingredients", "page_number", "INTEGER"),
    ("product_ingredients", "verification_status", "TEXT DEFAULT 'machine_extracted'"),
    ("regulatory_records", "product_category", "TEXT"),
    ("regulatory_records", "approval_number", "TEXT"),
    ("regulatory_records", "notification_number", "TEXT"),
    ("regulatory_records", "authorized_representative", "TEXT"),
    ("regulatory_records", "claim_type", "TEXT"),
    ("regulatory_records", "expiry_date", "TEXT"),
    ("regulatory_records", "source_document", "TEXT"),
    ("clinical_studies", "ingredient_id", "INTEGER REFERENCES ingredients(id)"),
    ("clinical_studies", "route", "TEXT"),
    ("clinical_studies", "dose", "TEXT"),
    ("clinical_studies", "population", "TEXT"),
    ("clinical_studies", "sample_size", "INTEGER"),
    ("clinical_studies", "primary_outcome", "TEXT"),
    ("clinical_studies", "publication_id", "TEXT"),
    ("patents", "application_number", "TEXT"),
    ("patents", "patent_family", "TEXT"),
    ("patents", "priority_date", "TEXT"),
    ("patents", "expiration_date", "TEXT"),
]


def init_db(db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)
        for table, column, coltype in COLUMN_MIGRATIONS:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
            except sqlite3.OperationalError:
                pass  # column already exists


def save_results(query: str, query_type: str, results: list, db_path: str = DB_PATH) -> int:
    init_db(db_path)
    rows = []
    for r in results:
        d = r.to_dict()
        rows.append((
            query, query_type, d["title"], d["entity_type"], d["entity_name"],
            d["company"], d["country"], d["category"], d["regulatory_status"],
            d["summary"], d["identifier"], d["source_name"], d["source_url"],
            d["source_type"], d["retrieved_at"], d["evidence_score"],
            confidence_label(d["evidence_score"]),
        ))

    with get_connection(db_path) as conn:
        conn.executemany(
            """INSERT INTO search_results (
                query, query_type, title, entity_type, entity_name,
                company, country, category, regulatory_status,
                summary, identifier, source_name, source_url,
                source_type, retrieved_at, evidence_score, confidence_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        return conn.execute("SELECT changes()").fetchone()[0]


def fetch_history(limit: int = 50, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT DISTINCT query, query_type, MAX(retrieved_at) as last_run "
            "FROM search_results GROUP BY query, query_type "
            "ORDER BY last_run DESC LIMIT ?",
            (limit,),
        ).fetchall()


def fetch_results_for_query(query: str, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM search_results WHERE query = ? ORDER BY evidence_score DESC",
            (query,),
        ).fetchall()


def fetch_all_results(db_path: str = DB_PATH) -> list[sqlite3.Row]:
    """Every stored result across every query — used for cross-query entity
    browsing rather than a single search run's results."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM search_results ORDER BY evidence_score DESC").fetchall()


def fetch_known_identifiers(query: str, db_path: str = DB_PATH) -> set:
    """Identifiers already stored for a query, used to detect what's new
    the next time the same search is re-run."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT identifier FROM search_results "
            "WHERE query = ? AND identifier IS NOT NULL",
            (query,),
        ).fetchall()
        return {row["identifier"] for row in rows}


def save_market_data(rows: list[dict], db_path: str = DB_PATH) -> int:
    init_db(db_path)
    columns = ALL_FIELDS + ["uploaded_at"]
    values = [tuple(row.get(col) for col in columns) for row in rows]

    with get_connection(db_path) as conn:
        conn.executemany(
            f"INSERT INTO market_data ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _ in columns)})",
            values,
        )
        return conn.execute("SELECT changes()").fetchone()[0]


def fetch_market_data(category: str | None = None, scope_level: str | None = None,
                       db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    clauses, params = [], []
    if category:
        clauses.append("category = ?")
        params.append(category)
    if scope_level:
        clauses.append("scope_level = ?")
        params.append(scope_level)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order = "year DESC" if category else "uploaded_at DESC"
    with get_connection(db_path) as conn:
        return conn.execute(
            f"SELECT * FROM market_data {where} ORDER BY {order}", params
        ).fetchall()


DOCUMENT_COLUMNS = [
    "file_name", "page_number", "extracted_text", "ingredient_mentions",
    "company_mentions", "source_type", "confidence", "uploaded_at",
]


def save_document_pages(records: list[dict], db_path: str = DB_PATH) -> int:
    init_db(db_path)
    values = [tuple(record.get(col) for col in DOCUMENT_COLUMNS) for record in records]

    with get_connection(db_path) as conn:
        conn.executemany(
            f"INSERT INTO document_sources ({', '.join(DOCUMENT_COLUMNS)}) "
            f"VALUES ({', '.join('?' for _ in DOCUMENT_COLUMNS)})",
            values,
        )
        return conn.execute("SELECT changes()").fetchone()[0]


def fetch_documents(db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT id, file_name, page_number, ingredient_mentions, company_mentions, "
            "source_type, confidence, uploaded_at FROM document_sources "
            "ORDER BY uploaded_at DESC"
        ).fetchall()
