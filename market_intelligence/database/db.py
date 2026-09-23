"""Thin sqlite3 access layer: create schema, save a search run, read history."""

import sqlite3
from contextlib import contextmanager

from config import DB_PATH
from database.models import SCHEMA
from processing.evidence_scoring import confidence_label


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
