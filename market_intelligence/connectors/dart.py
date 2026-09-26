"""Korea Financial Supervisory Service OpenDART connector.

Docs: https://opendart.fss.or.kr/guide/main.do

OpenDART requires a free registered API key, read from DART_API_KEY.
Unlike the other connectors here, DART isn't a keyword search over
filings — it's a two-step lookup: resolve a company name to its DART
`corp_code` from a bulk corp-code list, then pull that company's filed
financial statements by year. Both steps need the key.

Covers only companies that file with Korean regulators (listed companies,
and private companies above the external-audit disclosure threshold).
A private company below that threshold simply won't appear here — that's
a real absence of a public filing, not a connector failure.
"""

import io
import os
import zipfile
import xml.etree.ElementTree as ET

import requests

from config import DEFAULT_TIMEOUT
from connectors.base import ConnectorError

CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
FINANCIALS_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"

# Standard annual-report code for OpenDART's single-company financial
# statement API (11011 = business (annual) report).
ANNUAL_REPORT_CODE = "11011"


def _get_api_key() -> str:
    key = os.environ.get("DART_API_KEY")
    if not key:
        raise ConnectorError(
            "DART is not configured: set DART_API_KEY (free registration at "
            "https://opendart.fss.or.kr) to enable Korean corporate filing lookups."
        )
    return key


def fetch_corp_code_list() -> bytes:
    """Downloads OpenDART's full corp-code list as a zipped XML file.

    This is a bulk file (all Korean corp codes, tens of thousands of
    entries) — callers should cache the parsed result rather than
    re-downloading per lookup.
    """
    key = _get_api_key()
    try:
        response = requests.get(
            CORP_CODE_URL, params={"crtfc_key": key}, timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"DART corp-code download failed: {exc}") from exc

    content_type = response.headers.get("Content-Type", "")
    if "zip" not in content_type and not response.content.startswith(b"PK"):
        # DART returns a small JSON error body (not a zip) on a bad key
        # or other request-level failure.
        raise ConnectorError(f"DART corp-code request did not return a zip file: {response.text[:200]}")

    return response.content


def parse_corp_code_list(zip_bytes: bytes) -> list[dict]:
    """Parses the corp-code zip into a list of {corp_code, corp_name, stock_code}."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        xml_bytes = zf.read(zf.namelist()[0])

    root = ET.fromstring(xml_bytes)
    entries = []
    for el in root.findall(".//list"):
        entries.append({
            "corp_code": (el.findtext("corp_code") or "").strip(),
            "corp_name": (el.findtext("corp_name") or "").strip(),
            "stock_code": (el.findtext("stock_code") or "").strip() or None,
        })
    return entries


def find_corp_code(entries: list[dict], company_name: str) -> list[dict]:
    """Case-insensitive substring match on corp_name against a parsed corp-code list."""
    needle = company_name.strip().lower()
    return [e for e in entries if needle in e["corp_name"].lower()]


def fetch_financial_statements(corp_code: str, year: int, report_code: str = ANNUAL_REPORT_CODE) -> dict:
    """Returns the parsed JSON body from DART's single-company financial-statement API."""
    key = _get_api_key()
    params = {
        "crtfc_key": key,
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": report_code,
    }
    try:
        response = requests.get(FINANCIALS_URL, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectorError(f"DART financial-statement request failed: {exc}") from exc

    data = response.json()
    status = data.get("status")
    if status != "000":
        # "013" = no data found for that year/report combination, which is
        # a normal outcome (e.g. company didn't file that year), not an error.
        if status == "013":
            return {"status": status, "message": data.get("message"), "list": []}
        raise ConnectorError(f"DART API error {status}: {data.get('message')}")

    return data


def normalize_financial_statements(data: dict) -> list[dict]:
    """Flattens DART's financial-statement line items into a simpler shape
    for display: account name, amount, fiscal year, and statement type."""
    rows = []
    for item in data.get("list", []):
        rows.append({
            "account_name": item.get("account_nm"),
            "amount": item.get("thstrm_amount"),
            "fiscal_year": item.get("bsns_year"),
            "statement_type": item.get("sj_nm"),
            "currency": "KRW",
        })
    return rows
