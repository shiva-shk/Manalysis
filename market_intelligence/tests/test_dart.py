import io
import zipfile

import pytest

from connectors.base import ConnectorError
from connectors.dart import (
    fetch_corp_code_list,
    fetch_financial_statements,
    find_corp_code,
    normalize_financial_statements,
    parse_corp_code_list,
)


def test_fetch_corp_code_list_requires_api_key(monkeypatch):
    monkeypatch.delenv("DART_API_KEY", raising=False)
    with pytest.raises(ConnectorError, match="DART_API_KEY"):
        fetch_corp_code_list()


def test_fetch_financial_statements_requires_api_key(monkeypatch):
    monkeypatch.delenv("DART_API_KEY", raising=False)
    with pytest.raises(ConnectorError, match="DART_API_KEY"):
        fetch_financial_statements("01234567", 2023)

CORP_CODE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<result>
  <list>
    <corp_code>00126380</corp_code>
    <corp_name>Samsung Electronics</corp_name>
    <stock_code>005930</stock_code>
    <modify_date>20240101</modify_date>
  </list>
  <list>
    <corp_code>01234567</corp_code>
    <corp_name>ExoCoBio Inc.</corp_name>
    <stock_code></stock_code>
    <modify_date>20240101</modify_date>
  </list>
</result>
"""


def _zip_bytes(xml_bytes: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("CORPCODE.xml", xml_bytes)
    return buf.getvalue()


def test_parse_corp_code_list_extracts_entries():
    entries = parse_corp_code_list(_zip_bytes(CORP_CODE_XML))
    assert len(entries) == 2
    assert entries[0]["corp_name"] == "Samsung Electronics"
    assert entries[0]["stock_code"] == "005930"
    assert entries[1]["corp_name"] == "ExoCoBio Inc."
    assert entries[1]["stock_code"] is None


def test_find_corp_code_matches_case_insensitive_substring():
    entries = parse_corp_code_list(_zip_bytes(CORP_CODE_XML))
    matches = find_corp_code(entries, "exocobio")
    assert len(matches) == 1
    assert matches[0]["corp_code"] == "01234567"


def test_find_corp_code_no_match_returns_empty():
    entries = parse_corp_code_list(_zip_bytes(CORP_CODE_XML))
    assert find_corp_code(entries, "nonexistent company xyz") == []


def test_normalize_financial_statements_flattens_line_items():
    data = {
        "status": "000",
        "list": [
            {
                "account_nm": "Revenue",
                "thstrm_amount": "12345678",
                "bsns_year": "2023",
                "sj_nm": "Income Statement",
            },
        ],
    }
    rows = normalize_financial_statements(data)
    assert rows == [{
        "account_name": "Revenue",
        "amount": "12345678",
        "fiscal_year": "2023",
        "statement_type": "Income Statement",
        "currency": "KRW",
    }]


def test_normalize_financial_statements_handles_empty_list():
    assert normalize_financial_statements({"status": "013", "list": []}) == []
