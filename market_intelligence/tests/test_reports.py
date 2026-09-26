import io

import openpyxl

from reports.excel_report import build_full_report_excel

SAMPLE_REPORT = {
    "query": "skin booster",
    "product_comparison": [
        {"title": "Rejuran Healer", "company": "Pharma Research", "avg_evidence_score": 0.9},
    ],
    "ingredients": {
        "exact_match": {"key": "pdrn", "preferred_name": "PDRN"},
        "related": [{"key": "polynucleotide", "preferred_name": "Polynucleotides (PN)"}],
    },
    "patents": [{"title": "ASCE Plus", "company": "ExoCoBio"}],
    "approvals": [{"title": "Rejuran Healer", "regulatory_status": "510(k) cleared"}],
    "studies": [{"title": "Rejuran Healer", "entity_type": "clinical_study"}],
    "market_data": [{"category": "skin booster", "market_value": 87.7, "year": 2024}],
}


def test_build_full_report_excel_has_all_sections():
    data = build_full_report_excel(SAMPLE_REPORT, "skin booster")
    wb = openpyxl.load_workbook(io.BytesIO(data))
    expected_sheets = {
        "Overview", "Product Comparison", "Ingredients",
        "Patents", "Approvals", "Studies", "Market, Sales & Share",
    }
    assert expected_sheets.issubset(set(wb.sheetnames))


def test_build_full_report_excel_handles_empty_sections():
    empty_report = {
        "query": "nonexistent",
        "product_comparison": [],
        "ingredients": {"exact_match": None, "related": []},
        "patents": [],
        "approvals": [],
        "studies": [],
        "market_data": [],
    }
    data = build_full_report_excel(empty_report, "nonexistent")
    wb = openpyxl.load_workbook(io.BytesIO(data))
    assert "Overview" in wb.sheetnames
