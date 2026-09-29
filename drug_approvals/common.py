"""Shared helpers: HTTP with a local cache, and the unified approval row shape."""

import hashlib
import time
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent / "data"
CACHE_DIR = DATA_DIR / "raw" / "cache"
TIMEOUT = 120

ROW_FIELDS = [
    "id", "region", "brand_name", "inn", "originator", "dosage_form", "strength",
    "route", "indication", "dosing", "label_effective_date", "approval_date",
    "approval_year", "orphan_designation", "status", "application_number",
    "application_type", "approval_category", "te_code", "atc_code", "source",
    "source_url",
]


class FetchError(Exception):
    pass


def new_row(**values) -> dict:
    row = {k: None for k in ROW_FIELDS}
    row["orphan_designation"] = False
    unknown = set(values) - set(ROW_FIELDS)
    if unknown:
        raise KeyError(f"unknown row fields: {sorted(unknown)}")
    row.update(values)
    return row


def year_of(iso_date):
    return int(iso_date[:4]) if iso_date else None


def download(url: str, max_age_hours: float = 12) -> bytes:
    """GET a URL, reusing a cached copy younger than max_age_hours."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / hashlib.sha1(url.encode()).hexdigest()
    if path.exists() and time.time() - path.stat().st_mtime < max_age_hours * 3600:
        return path.read_bytes()
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"request failed for {url}: {exc}") from exc
    path.write_bytes(response.content)
    return response.content
