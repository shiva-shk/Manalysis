"""Streamlit UI for the Medical Product Intelligence Platform.

Searches official/scientific sources (ClinicalTrials.gov, PubMed/Europe PMC,
openFDA, EPO patents when configured), scores results by evidence quality,
and exports to Excel/PDF. A separate tab holds manually entered or uploaded
market data, since commercial market-research sources are not queried
automatically.
"""

import pandas as pd
import streamlit as st

from analysis.summary import confidence_breakdown, summarize_results
from database.db import fetch_history, fetch_market_data, save_market_data, save_results
from processing.evidence_scoring import confidence_label
from processing.ingredient_dictionary import lookup_ingredient
from processing.market_data import ALL_FIELDS, prepare_rows
from reports.excel_report import build_excel_report
from reports.pdf_report import build_pdf_report
from search_pipeline import run_search

st.set_page_config(page_title="Medical Product Intelligence Platform", layout="wide")

st.title("Medical Product Intelligence Platform")
st.caption(
    "Searches official and scientific sources only (ClinicalTrials.gov, "
    "PubMed/Europe PMC, openFDA, EPO patents when configured). Commercial "
    "market data is never scraped — upload licensed exports or enter figures "
    "manually in the Market Data tab, each with its own source and confidence."
)

search_tab, market_tab = st.tabs(["Search", "Market Data"])

with search_tab:
    with st.sidebar:
        st.header("Search settings")

        source_labels = {
            "clinicaltrials": "ClinicalTrials.gov",
            "pubmed": "PubMed / Europe PMC",
            "openfda_device": "openFDA — 510(k) devices",
            "openfda_drug": "openFDA — drug labels",
            "patents": "EPO patents (requires API credentials)",
        }
        default_labels = [v for k, v in source_labels.items() if k != "patents"]
        selected_labels = st.multiselect(
            "Sources", options=list(source_labels.values()), default=default_labels
        )
        selected_sources = [k for k, v in source_labels.items() if v in selected_labels]

        page_size = st.slider("Results per source", min_value=5, max_value=50, value=20, step=5)
        min_confidence = st.slider("Minimum evidence score", 0.0, 1.0, 0.0, 0.05)

        st.divider()
        st.subheader("Recent searches")
        for row in fetch_history(limit=10):
            st.caption(f"{row['query']} ({row['query_type']}) — {row['last_run'][:10]}")

    query = st.text_input(
        "Search product, brand, ingredient, or company",
        placeholder="e.g. Profhilo, PDRN, hyaluronic acid filler, Galderma",
    )

    run = st.button("Search", type="primary", disabled=not query)

    if run and query:
        with st.spinner("Querying sources..."):
            results, warnings, query_type = run_search(query, selected_sources, page_size=page_size)

        for w in warnings:
            st.warning(w)

        ingredient_entry = lookup_ingredient(query) if query_type == "ingredient" else None
        if ingredient_entry:
            with st.expander(f"Ingredient reference: {ingredient_entry['preferred_name']}", expanded=True):
                c1, c2 = st.columns(2)
                c1.write(f"**INCI name:** {ingredient_entry['inci_name'] or 'n/a'}")
                c1.write(f"**CAS number:** {ingredient_entry['cas_number'] or 'n/a'}")
                c2.write(f"**Class:** {ingredient_entry['ingredient_class']}")
                c2.write(f"**Function:** {ingredient_entry['function']}")
                st.caption(ingredient_entry["notes"])

        if not results:
            st.info("No results found. Try a broader term or a different source selection.")
        else:
            df = pd.DataFrame([r.to_dict() for r in results])
            df["confidence_label"] = df["evidence_score"].apply(confidence_label)
            df = df[df["evidence_score"] >= min_confidence]

            save_results(query, query_type, results)

            st.subheader(f"Results for \"{query}\" — classified as: {query_type}")

            summary = summarize_results(df)
            conf = confidence_breakdown(df)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total results", summary["total_results"])
            col2.metric("Distinct companies", summary["companies"])
            col3.metric("Distinct countries", summary["countries"])
            col4.metric("Avg. evidence score", summary["avg_evidence_score"])

            if conf:
                st.caption(
                    "Confidence mix — "
                    + ", ".join(f"{label}: {count}" for label, count in conf.items())
                )

            st.dataframe(
                df[[
                    "title", "entity_type", "company", "country", "category",
                    "regulatory_status", "source_name", "source_type",
                    "evidence_score", "confidence_label", "source_url",
                ]],
                use_container_width=True,
                hide_index=True,
            )

            with st.expander("Top companies"):
                st.write(summary["top_companies"])

            with st.expander("Results by source type"):
                st.write(summary["by_source_type"])

            dl_col1, dl_col2 = st.columns(2)
            excel_bytes = build_excel_report(df, summary, query)
            dl_col1.download_button(
                "Download Excel report",
                data=excel_bytes,
                file_name=f"{query.replace(' ', '_')}_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            pdf_bytes = build_pdf_report(df.to_dict("records"), summary, query)
            dl_col2.download_button(
                "Download PDF report",
                data=pdf_bytes,
                file_name=f"{query.replace(' ', '_')}_report.pdf",
                mime="application/pdf",
            )

    st.divider()
    st.caption(
        "Data limitations: results reflect what each public API currently indexes, not full "
        "market coverage. FDA-cleared, CE-marked, and registered are distinct regulatory "
        "statuses and are not interchangeable."
    )

with market_tab:
    st.subheader("Licensed market data")
    st.caption(
        "Upload a CSV/Excel export from a licensed source (IQVIA, Euromonitor, "
        "Mintel, etc.) or enter a figure manually. Every row keeps its own "
        "source, definition, and confidence rating rather than being blended "
        "into the search results above."
    )

    with st.expander("Add a figure manually"):
        with st.form("manual_market_entry"):
            c1, c2, c3 = st.columns(3)
            category = c1.text_input("Category*", placeholder="dermal filler")
            region = c2.text_input("Region", placeholder="EU")
            year = c3.number_input("Year", min_value=1990, max_value=2100, value=2026, step=1)

            c4, c5, c6 = st.columns(3)
            market_value = c4.number_input("Market value", min_value=0.0, value=0.0, step=1.0)
            currency = c5.text_input("Currency", placeholder="USD")
            growth_rate = c6.number_input("Growth rate (%)", value=0.0, step=0.1)

            source = st.text_input("Source*", placeholder="e.g. Mintel GNPD, 2026 report")
            definition = st.text_area("Category definition", placeholder="What exactly this figure covers")
            confidence_score = st.slider("Confidence", 0.0, 1.0, 0.6, 0.05)

            submitted = st.form_submit_button("Add figure")
            if submitted:
                record = {
                    "category": category, "region": region, "year": year or None,
                    "market_value": market_value or None, "currency": currency,
                    "growth_rate": growth_rate or None, "source": source,
                    "definition": definition, "confidence_score": confidence_score,
                }
                valid_rows, errors = prepare_rows([record])
                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    save_market_data(valid_rows)
                    st.success("Figure added.")

    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            upload_df = pd.read_csv(uploaded_file)
        else:
            upload_df = pd.read_excel(uploaded_file)

        missing = set(ALL_FIELDS) - set(upload_df.columns)
        if missing:
            st.error(
                f"Upload is missing expected columns: {', '.join(sorted(missing))}. "
                f"Required columns: {', '.join(ALL_FIELDS)}."
            )
        else:
            st.dataframe(upload_df, use_container_width=True, hide_index=True)
            if st.button("Import uploaded rows"):
                valid_rows, errors = prepare_rows(upload_df.to_dict("records"))
                for e in errors:
                    st.error(e)
                if valid_rows:
                    save_market_data(valid_rows)
                    st.success(f"Imported {len(valid_rows)} row(s).")

    st.divider()
    st.subheader("Stored market data")
    stored = fetch_market_data()
    if stored:
        stored_df = pd.DataFrame([dict(r) for r in stored])
        st.dataframe(stored_df, use_container_width=True, hide_index=True)
    else:
        st.info("No market data stored yet.")
