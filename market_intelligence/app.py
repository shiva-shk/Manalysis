"""Streamlit UI for the Medical Product Intelligence Platform.

Searches official/scientific sources (ClinicalTrials.gov, PubMed/Europe PMC,
openFDA, EPO patents when configured), scores results by evidence quality,
and exports to Excel/PDF. A separate tab holds manually entered or uploaded
market data, since commercial market-research sources are not queried
automatically.
"""

import pandas as pd
import streamlit as st

from analysis.entity_resolution import cluster_entities
from analysis.opportunity_score import DIMENSIONS, opportunity_score, score_breakdown
from analysis.product_profile import build_profile
from analysis.summary import confidence_breakdown, summarize_results
from database.db import (
    fetch_all_results,
    fetch_documents,
    fetch_history,
    fetch_known_identifiers,
    fetch_market_data,
    fetch_results_for_query,
    save_document_pages,
    save_market_data,
    save_results,
)
from processing.document_ingest import ingest_pdf
from processing.evidence_scoring import confidence_label
from processing.ingredient_dictionary import lookup_ingredient
from processing.market_data import ALL_FIELDS, prepare_rows
from processing.monitoring import find_new_results
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

search_tab, market_tab, documents_tab, opportunity_tab, entities_tab, monitoring_tab = st.tabs(
    ["Search", "Market Data", "Documents", "Opportunity Score", "Entities", "Monitoring"]
)

with search_tab:
    with st.sidebar:
        st.header("Search settings")

        source_labels = {
            "clinicaltrials": "ClinicalTrials.gov",
            "pubmed": "PubMed / Europe PMC",
            "openfda_device": "openFDA — 510(k) devices",
            "openfda_drug": "openFDA — drug labels",
            "patents": "EPO patents (requires API credentials)",
            "eudamed": "EUDAMED — EU devices (undocumented, slow)",
        }
        default_off = {"patents", "eudamed"}
        default_labels = [v for k, v in source_labels.items() if k not in default_off]
        selected_labels = st.multiselect(
            "Sources", options=list(source_labels.values()), default=default_labels
        )
        selected_sources = [k for k, v in source_labels.items() if v in selected_labels]
        if "eudamed" in selected_sources:
            st.caption(
                "EUDAMED calls the same JSON endpoint its own search page uses "
                "(no documented public API) and can take 15-20+ seconds per search."
            )

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

            st.subheader("Product / entity profile")
            st.caption(
                "Groups the stored records that share an exact title — a stand-in "
                "for full entity resolution, not a verified single record."
            )
            profile_title = st.selectbox("Focus on", options=sorted(df["title"].unique()))
            if profile_title:
                history_rows = [dict(r) for r in fetch_results_for_query(query)]
                profile = build_profile(history_rows, profile_title)

                pc1, pc2, pc3 = st.columns(3)
                pc1.metric("Records", profile["source_count"])
                pc2.metric("Companies", len(profile["companies"]))
                pc3.metric("Avg. evidence score", profile["avg_evidence_score"])

                for section, section_rows in profile["sections"].items():
                    if section_rows:
                        with st.expander(f"{section.capitalize()} ({len(section_rows)})"):
                            st.dataframe(pd.DataFrame(section_rows), use_container_width=True, hide_index=True)

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

with documents_tab:
    st.subheader("Document ingestion")
    st.caption(
        "Upload a brochure, IFU, certificate, or other PDF. Text is extracted per page "
        "and scanned for known ingredient and company names, keeping the file name and "
        "page number as the citation for anything pulled from it."
    )

    pdf_files = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=True)
    source_type = st.selectbox(
        "Document type", ["manufacturer", "regulatory", "scientific", "commercial"]
    )

    if pdf_files and st.button("Extract and store"):
        total_pages = 0
        for pdf_file in pdf_files:
            records = ingest_pdf(pdf_file.read(), pdf_file.name, source_type=source_type)
            save_document_pages(records)
            total_pages += len(records)
        st.success(f"Extracted and stored {total_pages} page(s) from {len(pdf_files)} file(s).")

    st.divider()
    st.subheader("Stored documents")
    documents = fetch_documents()
    if documents:
        st.dataframe(pd.DataFrame([dict(r) for r in documents]), use_container_width=True, hide_index=True)
    else:
        st.info("No documents uploaded yet.")

with opportunity_tab:
    st.subheader("Development-opportunity score")
    st.caption(
        "A transparent, weighted decision-support score, not an objective verdict — "
        "score each dimension 1 (poor) to 5 (excellent) and record why."
    )

    with st.form("opportunity_form"):
        scores = {}
        notes = {}
        for key, meta in DIMENSIONS.items():
            c1, c2 = st.columns([1, 3])
            scores[key] = c1.slider(f"{meta['label']} ({meta['weight']:.0%})", 1, 5, 3, key=f"score_{key}")
            notes[key] = c2.text_input("Reasoning", key=f"notes_{key}", label_visibility="collapsed",
                                        placeholder=f"Why this score for {meta['label'].lower()}?")
        submitted = st.form_submit_button("Calculate score")

    if submitted:
        score = opportunity_score(scores)
        st.metric("Opportunity score", score)
        st.dataframe(pd.DataFrame(score_breakdown(scores, notes)), use_container_width=True, hide_index=True)

with entities_tab:
    st.subheader("Entities across all searches")
    st.caption(
        "Clusters every stored result — across every query you've run — into "
        "canonical entities using the same name/company matching rule as "
        "deduplication within a single search. Not full entity resolution: "
        "an entity here is a match cluster, not a verified single product."
    )

    all_rows = [dict(r) for r in fetch_all_results()]
    if not all_rows:
        st.info("No stored results yet — run a search first.")
    else:
        entities = cluster_entities(all_rows)
        st.metric("Distinct entities", len(entities))
        st.dataframe(pd.DataFrame(entities), use_container_width=True, hide_index=True)

with monitoring_tab:
    st.subheader("Check a saved search for new records")
    st.caption(
        "There's no background scheduler here — this re-runs a query on demand "
        "and flags only the records whose identifier (NCT number, 510(k) number, "
        "etc.) wasn't already stored from a previous run of the same query."
    )

    history_queries = sorted({row["query"] for row in fetch_history(limit=100)})
    if not history_queries:
        st.info("No saved searches yet — run a search first.")
    else:
        monitor_query = st.selectbox("Query to check", options=history_queries)
        monitor_sources = st.multiselect(
            "Sources to check",
            options=["clinicaltrials", "pubmed", "openfda_device", "openfda_drug"],
            default=["clinicaltrials", "pubmed", "openfda_device", "openfda_drug"],
        )

        if st.button("Check for updates") and monitor_query:
            known = fetch_known_identifiers(monitor_query)
            with st.spinner("Re-running search..."):
                fresh_results, fresh_warnings, _ = run_search(monitor_query, monitor_sources)

            for w in fresh_warnings:
                st.warning(w)

            new_results = find_new_results(fresh_results, known)
            if new_results:
                st.success(f"{len(new_results)} new record(s) since the last run.")
                st.dataframe(
                    pd.DataFrame([r.to_dict() for r in new_results]),
                    use_container_width=True,
                    hide_index=True,
                )
                save_results(monitor_query, "monitoring_check", new_results)
            else:
                st.info("No new records since the last run.")
