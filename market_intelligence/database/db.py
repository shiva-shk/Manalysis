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


def init_db(db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


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


def fetch_market_data(category: str | None = None, db_path: str = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        if category:
            return conn.execute(
                "SELECT * FROM market_data WHERE category = ? ORDER BY year DESC",
                (category,),
            ).fetchall()
        return conn.execute("SELECT * FROM market_data ORDER BY uploaded_at DESC").fetchall()


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
