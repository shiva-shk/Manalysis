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


def build_full_report_excel(report: dict, query: str) -> bytes:
    """One sheet per section of a full report (analysis.full_report):
    product comparison, ingredients, patents, approvals, studies, and any
    matching Market Data rows (market analysis / sales / market share)."""
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([{"Query": query}]).to_excel(writer, sheet_name="Overview", index=False)

        product_comparison = report.get("product_comparison") or []
        pd.DataFrame(product_comparison).to_excel(writer, sheet_name="Product Comparison", index=False)

        ingredients = report.get("ingredients") or {}
        ingredient_rows = []
        if ingredients.get("exact_match"):
            ingredient_rows.append(ingredients["exact_match"])
        ingredient_rows.extend(ingredients.get("related") or [])
        pd.DataFrame(ingredient_rows).to_excel(writer, sheet_name="Ingredients", index=False)

        pd.DataFrame(report.get("patents") or []).to_excel(writer, sheet_name="Patents", index=False)
        pd.DataFrame(report.get("approvals") or []).to_excel(writer, sheet_name="Approvals", index=False)
        pd.DataFrame(report.get("studies") or []).to_excel(writer, sheet_name="Studies", index=False)
        pd.DataFrame(report.get("market_data") or []).to_excel(
            writer, sheet_name="Market, Sales & Share", index=False
        )

    buffer.seek(0)
    return buffer.read()
