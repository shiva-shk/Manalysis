"""Indication and dosing text for FDA rows, from the openFDA drug label endpoint.

openFDA labels are the FDA's SPL (DailyMed) label data. Labels are looked up
by application number in batches. Only NDA and BLA applications are enriched:
ANDA labels repeat the brand label and would add about 20,000 more lookups.
Extracted text is cached in data/raw/cache/labels.json so re-runs are quick.
"""

import json
import re
import time
from datetime import datetime

import requests

try:
    from .common import CACHE_DIR
except ImportError:
    from common import CACHE_DIR

LABEL_URL = "https://api.fda.gov/drug/label.json"
BATCH = 20
PAGE = 100
CACHE_FILE = CACHE_DIR / "labels.json"
CACHE_HOURS = 24 * 7
MAX_INDICATION = 1200
MAX_DOSING = 1000

_HEADING = re.compile(r"^\s*(?:\d+(?:\.\d+)*\s*)?(?:INDICATIONS?\s*(?:AND|&)\s*USAGE|DOSAGE\s*(?:AND|&)\s*ADMINISTRATION)\s*:?\s*", re.I)


def _clean(parts, limit: int):
    text = re.sub(r"\s+", " ", " ".join(parts or [])).strip()
    text = _HEADING.sub("", text).strip()
    if not text:
        return None
    if len(text) > limit:
        cut = text[:limit]
        stop = max(cut.rfind(". "), cut.rfind("; "))
        text = (cut[: stop + 1] if stop > limit // 2 else cut.rstrip()) + " ..."
    return text


def _iso(yyyymmdd):
    try:
        return datetime.strptime(yyyymmdd, "%Y%m%d").date().isoformat()
    except (TypeError, ValueError):
        return None


def _query(apps: list[str]):
    search = " OR ".join(f'openfda.application_number:"{a}"' for a in apps)
    skip = 0
    while True:
        for attempt in range(4):
            response = requests.get(LABEL_URL, params={"search": search, "limit": PAGE, "skip": skip}, timeout=120)
            if response.status_code == 404:  # openFDA's way of saying no matches
                return
            if response.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            break
        else:
            response.raise_for_status()
        body = response.json()
        yield from body["results"]
        skip += PAGE
        if skip >= body["meta"]["results"]["total"] or skip > 25000:
            return
        time.sleep(0.3)


def _best(labels: list[dict], app: str, brand: str):
    def score(label):
        of = label.get("openfda") or {}
        brands = [b.lower() for b in of.get("brand_name") or []]
        return (
            "HUMAN PRESCRIPTION DRUG" in (of.get("product_type") or []),
            (brand or "").lower() in brands,
            bool(label.get("indications_and_usage")),
            label.get("effective_time") or "",
        )
    candidates = [l for l in labels if app in (l.get("openfda") or {}).get("application_number", [])]
    return max(candidates, key=score) if candidates else None


def fetch_label_text(apps_brands: dict[str, str]) -> dict[str, dict]:
    """{application_number: {indication, dosing, label_effective_date}} for the apps found."""
    cache = {}
    if CACHE_FILE.exists() and time.time() - CACHE_FILE.stat().st_mtime < CACHE_HOURS * 3600:
        cache = json.loads(CACHE_FILE.read_text())
    todo = [a for a in apps_brands if a not in cache]
    for i in range(0, len(todo), BATCH):
        batch = todo[i : i + BATCH]
        labels = list(_query(batch))
        for app in batch:
            label = _best(labels, app, apps_brands[app])
            cache[app] = None if label is None else {
                "indication": _clean(label.get("indications_and_usage"), MAX_INDICATION),
                "dosing": _clean(label.get("dosage_and_administration"), MAX_DOSING),
                "label_effective_date": _iso(label.get("effective_time")),
            }
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache))
        time.sleep(0.3)
    return {a: cache[a] for a in apps_brands if cache.get(a)}


def enrich_fda_rows(rows: list[dict]) -> int:
    targets = {r["application_number"]: r["brand_name"] for r in rows
               if r["region"] == "FDA" and r["application_type"] in ("NDA", "BLA")}
    found = fetch_label_text(targets)
    for r in rows:
        extra = found.get(r["application_number"]) if r["region"] == "FDA" else None
        if extra:
            r.update(extra)
    return len(found)
