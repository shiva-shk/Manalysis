"""EMA approvals from the medicines bulk JSON report.

Source: https://www.ema.europa.eu/en/documents/report/medicines-output-medicines_json-report_en.json
(the full list of centrally authorised medicines, ~2,700 records).

Dates in this file are DD/MM/YYYY. The approval date is the European
Commission marketing authorisation date, not the record's last-updated
date. Medicines that were only refused, or whose application was withdrawn
before authorisation, are not approvals and are skipped. Medicines with a
positive CHMP opinion still awaiting the Commission decision are kept and
dated by the opinion.
"""

import json
from datetime import datetime

try:
    from .common import download, new_row, year_of
except ImportError:
    from common import download, new_row, year_of

MEDICINES_URL = (
    "https://www.ema.europa.eu/en/documents/report/"
    "medicines-output-medicines_json-report_en.json"
)
SOURCE = "EMA bulk JSON report (medicines)"


def load_ema_medicines() -> list[dict]:
    data = json.loads(download(MEDICINES_URL))
    records = data.get("data") if isinstance(data, dict) else data
    if not isinstance(records, list):
        raise ValueError("EMA response did not contain a medicines list")
    return records


def _iso(ddmmyyyy):
    if not ddmmyyyy:
        return None
    try:
        return datetime.strptime(ddmmyyyy.strip(), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def _yes(value) -> bool:
    return (value or "").strip().lower() == "yes"


def normalize_ema(records: list[dict], include_veterinary: bool = False) -> list[dict]:
    rows = []
    for r in records:
        if r.get("category") == "Veterinary" and not include_veterinary:
            continue
        authorised = _iso(r.get("marketing_authorisation_date")) or _iso(r.get("european_commission_decision_date"))
        pending = r.get("opinion_status") == "Positive" and not authorised
        if not (authorised or pending):
            continue
        date = authorised or _iso(r.get("opinion_adopted_date"))
        if date is None:
            continue

        status = r.get("medicine_status") or ""
        if pending:
            status = "CHMP positive opinion (awaiting EC decision)"

        if _yes(r.get("biosimilar")):
            kind = "Biosimilar"
        elif _yes(r.get("generic")):
            kind = "Generic"
        else:
            kind = "Original"

        flags = [label for key, label in (
            ("conditional_approval", "Conditional approval"),
            ("exceptional_circumstances", "Exceptional circumstances"),
            ("accelerated_assessment", "Accelerated assessment"),
            ("advanced_therapy", "Advanced therapy"),
            ("prime_priority_medicine", "PRIME"),
        ) if _yes(r.get(key))]

        number = r.get("ema_product_number")
        rows.append(new_row(
            id=f"EMA-{number}",
            region="EMA",
            brand_name=r.get("name_of_medicine"),
            inn=(r.get("international_non_proprietary_name_common_name") or r.get("active_substance") or "").strip(),
            originator=r.get("marketing_authorisation_developer_applicant_holder") or None,
            indication=(r.get("therapeutic_indication") or "").strip() or None,
            approval_date=date,
            approval_year=year_of(date),
            orphan_designation=_yes(r.get("orphan_medicine")),
            status=status,
            application_number=number,
            application_type=kind,
            approval_category=", ".join(flags) or None,
            atc_code=r.get("atc_code_human") or r.get("atcvet_code_veterinary") or None,
            source=SOURCE,
            source_url=r.get("medicine_url") or MEDICINES_URL,
        ))
    return rows
