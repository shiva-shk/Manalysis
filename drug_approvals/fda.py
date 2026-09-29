"""FDA approvals from the openFDA Drugs@FDA bulk file.

Source: https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip
(one record per application, listed in https://api.fda.gov/download.json).

One row per application. The approval date is the date of the original
(ORIG) submission that reached approval status, not a label or supplement
date. Applications with only a tentative approval are skipped, because
they are not marketable approvals.
"""

import io
import json
import zipfile
from datetime import datetime

try:
    from .common import download, new_row, year_of
except ImportError:
    from common import download, new_row, year_of

DRUGSFDA_URL = "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip"
OVERVIEW_URL = "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo={}"
SOURCE = "openFDA drugsfda"


def load_drugsfda() -> list[dict]:
    raw = download(DRUGSFDA_URL)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".json"))
        return json.loads(zf.read(name))["results"]


def _iso(yyyymmdd):
    if not yyyymmdd or len(yyyymmdd) != 8:
        return None
    try:
        return datetime.strptime(yyyymmdd, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def _application_type(number: str) -> str:
    for prefix in ("ANDA", "NDA", "BLA"):
        if number.startswith(prefix):
            return prefix
    return number.rstrip("0123456789")


def _approval(submissions: list[dict]):
    """(iso date, category) of the original approval, or (None, None)."""
    approved = [s for s in submissions if s.get("submission_status") == "AP" and _iso(s.get("submission_status_date"))]
    originals = [s for s in approved if s.get("submission_type") == "ORIG"]
    pool = originals or approved
    if not pool:
        return None, None
    first = min(pool, key=lambda s: s["submission_status_date"])
    category = first.get("submission_class_code_description")
    if category in ("UNKNOWN", "N/A", "Unknown"):
        category = None
    return _iso(first["submission_status_date"]), category


def _status(products: list[dict]) -> str:
    marketing = {p.get("marketing_status") for p in products}
    if "Prescription" in marketing:
        return "Prescription"
    if "Over-the-counter" in marketing:
        return "Over-the-counter"
    if marketing == {"Discontinued"}:
        return "Discontinued"
    return "Not marketed"


def _uniq(values, limit=None):
    seen = []
    for v in values:
        if v and v not in seen:
            seen.append(v)
    return seen[:limit] if limit else seen


def _inn(record: dict) -> str:
    generic = (record.get("openfda") or {}).get("generic_name") or []
    names = generic or [
        ai.get("name") for p in record["products"] for ai in p.get("active_ingredients") or []
    ]
    return "; ".join(n.lower() for n in _uniq(names, 4))


def normalize_fda(records: list[dict]) -> list[dict]:
    rows = []
    for record in records:
        number = record.get("application_number") or ""
        products = record.get("products") or []
        if not number or not products:
            continue
        date, category = _approval(record.get("submissions") or [])
        if date is None:
            continue  # tentative approval only, or no dated approval on file

        openfda = record.get("openfda") or {}
        brands = _uniq(p.get("brand_name") for p in products)
        strengths = _uniq(
            "; ".join(f"{ai.get('name', '').lower()} {ai.get('strength', '')}".strip()
                      for ai in p.get("active_ingredients") or [])
            for p in products
        )
        rows.append(new_row(
            id=f"FDA-{number}",
            region="FDA",
            brand_name=brands[0] if brands else None,
            inn=_inn(record),
            originator=record.get("sponsor_name"),
            dosage_form=", ".join(_uniq((p.get("dosage_form") or "").lower() for p in products)[:3]) or None,
            strength=" | ".join(strengths[:3]) or None,
            route=", ".join(_uniq((p.get("route") or "").lower() for p in products)[:3]) or None,
            approval_date=date,
            approval_year=year_of(date),
            status=_status(products),
            application_number=number,
            application_type=_application_type(number),
            approval_category=category,
            te_code=next((p["te_code"] for p in products if p.get("te_code")), None),
            source=SOURCE,
            source_url=OVERVIEW_URL.format(number.lstrip("ABDLN")),
        ))
    return rows
