"""Export search results (plus a summary sheet) to an .xlsx workbook."""

import io

import pandas as pd


def build_excel_report(df: pd.DataFrame, summary: dict, query: str) -> bytes:
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Results", index=False)

        summary_rows = [
            {"Metric": "Query", "Value": query},
            {"Metric": "Total results", "Value": summary.get("total_results", 0)},
            {"Metric": "Distinct companies", "Value": summary.get("companies", 0)},
            {"Metric": "Distinct countries", "Value": summary.get("countries", 0)},
            {"Metric": "Average evidence score", "Value": summary.get("avg_evidence_score", 0)},
        ]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary", index=False)

        top_companies = summary.get("top_companies", {})
        if top_companies:
            pd.DataFrame(
                list(top_companies.items()), columns=["Company", "Count"]
            ).to_excel(writer, sheet_name="Top Companies", index=False)

    buffer.seek(0)
    return buffer.read()
