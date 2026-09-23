"""Streamlit UI for the Medical Product Intelligence Platform (Phase 1 MVP).

Searches official/scientific sources (ClinicalTrials.gov, PubMed/Europe PMC,
openFDA), scores results by evidence quality, and exports to Excel.
"""

import pandas as pd
import streamlit as st

from analysis.summary import confidence_breakdown, summarize_results
from database.db import fetch_history, save_results
from processing.evidence_scoring import confidence_label
from reports.excel_report import build_excel_report
from search_pipeline import run_search

st.set_page_config(page_title="Medical Product Intelligence Platform", layout="wide")

st.title("Medical Product Intelligence Platform")
st.caption(
    "Searches official and scientific sources only (ClinicalTrials.gov, "
    "PubMed/Europe PMC, openFDA). Commercial market data and paywalled "
    "sources are not queried automatically — upload licensed files separately."
)

with st.sidebar:
    st.header("Search settings")

    source_labels = {
        "clinicaltrials": "ClinicalTrials.gov",
        "pubmed": "PubMed / Europe PMC",
        "openfda_device": "openFDA — 510(k) devices",
        "openfda_drug": "openFDA — drug labels",
    }
    selected_labels = st.multiselect(
        "Sources", options=list(source_labels.values()), default=list(source_labels.values())
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

        excel_bytes = build_excel_report(df, summary, query)
        st.download_button(
            "Download Excel report",
            data=excel_bytes,
            file_name=f"{query.replace(' ', '_')}_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

st.divider()
st.caption(
    "Data limitations: results reflect what each public API currently indexes, not full "
    "market coverage. FDA-cleared, CE-marked, and registered are distinct regulatory "
    "statuses and are not interchangeable. Commercial market-share figures require "
    "licensed sources and are out of scope for this automated search."
)
