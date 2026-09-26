"""Streamlit UI for the Medical Product Intelligence Platform.

Searches official/scientific sources (ClinicalTrials.gov, PubMed/Europe PMC,
openFDA, EPO patents when configured), scores results by evidence quality,
and exports to Excel/PDF. Every other kind of data entry — market figures,
documents, opportunity scoring, suppliers, competitor profiles, manual
regulatory records, and the product-development tools — lives in one
"Data Entry & Scoring" tab, kept separate from Search (which only shows
what a live connector search returns) and Registry (which only shows the
verified/promoted layer, with no entry forms of its own besides promotion).
"""

import json

import pandas as pd
import streamlit as st

from analysis.canonical_search import build_canonical_search_response
from analysis.cost_model import break_even_volume, estimated_cogs, gross_margin
from analysis.entity_resolution import cluster_entities, cluster_entities_with_members
from analysis.full_report import build_full_report
from analysis.knowledge_graph import build_product_graph, graph_summary, graph_to_edge_list
from analysis.opportunity_score import DIMENSIONS, opportunity_score, score_breakdown
from analysis.product_profile import build_profile
from analysis.registry_search import search_registry
from analysis.risk_scoring import check_stop_criteria, risk_acceptability, risk_priority_number
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
from database.registry_db import (
    add_competitor_profile,
    add_control,
    add_cost_model,
    add_cpp,
    add_cqa,
    add_portfolio_gap,
    add_qttp,
    add_regulatory_record,
    add_risk_assessment,
    add_stage_gate_decision,
    add_supplier,
    add_supplier_material,
    fetch_aliases,
    fetch_audit_log,
    fetch_change_events,
    fetch_clinical_studies,
    fetch_competitor_profiles,
    fetch_companies,
    fetch_controls,
    fetch_cost_models,
    fetch_cpps,
    fetch_cqas,
    fetch_field_evidence,
    fetch_ingredients,
    fetch_patents,
    fetch_portfolio_gaps,
    fetch_product_companies,
    fetch_product_ingredients,
    fetch_products,
    fetch_qttp,
    fetch_regulatory_records,
    fetch_safety_signals,
    fetch_trademarks,
    log_change_event,
    fetch_risk_assessments,
    fetch_stage_gate_decisions,
    fetch_suppliers,
    fetch_supplier_materials,
    link_product_ingredient,
)
from processing.document_ingest import ingest_pdf
from processing.entity_promotion import promote_cluster, registry_completeness
from processing.evidence_scoring import confidence_label
from processing.ingredient_dictionary import lookup_ingredient
from processing.ingredient_seed_data import seed_ingredients
from processing.market_data import ALL_FIELDS, prepare_rows
from processing.monitoring import find_new_results
from processing.taxonomy import (
    CQA_CATEGORIES,
    PRODUCT_TYPES,
    RECOMMENDED_ACTIONS,
    REGULATORY_CATEGORIES,
    RISK_CATEGORIES,
    STAGE_GATE_DECISIONS,
    STAGE_GATE_STAGES,
)
from reports.excel_report import build_excel_report, build_full_report_excel
from reports.pdf_report import build_pdf_report
from search_pipeline import run_search

st.set_page_config(page_title="Medical Product Intelligence Platform", layout="wide")

st.title("Medical Product Intelligence Platform")
st.caption(
    "Search runs live queries across every connected source and shows what "
    "each one returns for a product, brand, ingredient, or company. Manual "
    "and uploaded data, plus every scoring tool, lives in Data Entry & "
    "Scoring. Registry is the verified layer — only a promoted product "
    "counts as confirmed, and it has no entry forms of its own."
)

(search_tab, data_entry_tab, entities_tab, monitoring_tab, registry_tab) = st.tabs(
    ["Search", "Data Entry & Scoring", "Entities", "Monitoring", "Registry"]
)

with search_tab:
    with st.sidebar:
        st.header("Search settings")

        source_labels = {
            "clinicaltrials": "ClinicalTrials.gov",
            "pubmed": "PubMed / Europe PMC",
            "openfda_device": "openFDA — 510(k) devices",
            "openfda_drug": "openFDA — drug labels",
            "openfda_pma": "openFDA — PMA devices (Class III approvals)",
            "openfda_udi": "openFDA — UDI/GUDID device identifiers",
            "dailymed": "DailyMed — structured product labels",
            "ema": "EMA — EU centrally authorised medicines",
            "pubchem": "PubChem — chemical identity (CAS, formula, IUPAC name)",
            "patents": "EPO patents (requires API credentials)",
            "eudamed": "EUDAMED — EU devices (undocumented, slow)",
            "health_canada": "Health Canada MDALL (undocumented)",
        }
        default_off = {"patents", "eudamed", "health_canada"}
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
        if "health_canada" in selected_sources:
            st.caption(
                "Health Canada MDALL has no public API — this drives its search "
                "form directly (device-name search only) and can break if the "
                "site changes."
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
            st.subheader("Full report")
            st.caption(
                "Consolidates this search into one report — product comparison, "
                "ingredients, patents, approvals, clinical studies, and any stored "
                "Market Data rows matching this query (market analysis, sales, "
                "market share). Every section pulls from data already in the "
                "platform; a section with nothing stored shows empty rather than "
                "an estimate. Market/sales/share figures come from the Market "
                "Data section of the Data Entry & Scoring tab."
            )

            stored_market_rows = [dict(r) for r in fetch_market_data()]
            full_report = build_full_report(query, df.to_dict("records"), stored_market_rows)

            report_sections = [
                ("Product comparison", full_report["product_comparison"]),
                ("Patents", full_report["patents"]),
                ("Approvals", full_report["approvals"]),
                ("Clinical studies", full_report["studies"]),
                ("Market analysis / sales / market share", full_report["market_data"]),
            ]
            for label, rows in report_sections:
                with st.expander(f"{label} ({len(rows)})", expanded=bool(rows)):
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.caption("Nothing found for this query in this section.")

            ingredient_section = full_report["ingredients"]
            with st.expander(
                f"Ingredients ({(1 if ingredient_section['exact_match'] else 0) + len(ingredient_section['related'])})",
                expanded=bool(ingredient_section["exact_match"] or ingredient_section["related"]),
            ):
                if ingredient_section["exact_match"]:
                    st.write("**Exact match:**", ingredient_section["exact_match"])
                if ingredient_section["related"]:
                    st.dataframe(
                        pd.DataFrame(ingredient_section["related"]),
                        use_container_width=True, hide_index=True,
                    )
                if not ingredient_section["exact_match"] and not ingredient_section["related"]:
                    st.caption("No ingredient reference entry matches this query.")

            if not full_report["market_data"]:
                st.caption(
                    "No Market Data rows are tagged with a matching category yet — "
                    "add them in the Market Data section of Data Entry & Scoring "
                    "(manual entry or licensed upload) to have market/sales/share "
                    "figures show up here."
                )

            full_report_excel = build_full_report_excel(full_report, query)
            st.download_button(
                "Download full report (Excel, all sections)",
                data=full_report_excel,
                file_name=f"{query.replace(' ', '_')}_full_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.divider()
            st.subheader("Canonical structure")
            st.caption(
                "The same search result reshaped into one structured record — "
                "identity, ownership by role, composition, regulatory/clinical/"
                "patent evidence, and market data — with an explicit list of "
                "what wasn't found rather than leaving a gap silent. If this "
                "product has been promoted in the Registry tab, every field "
                "below comes from that verified record with real citations; "
                "otherwise it's built from this search's raw results and "
                "marked unverified."
            )

            registry_hits = search_registry(query)
            top_hit = next((h for h in registry_hits if h["entity_type"] == "product"), None)
            registry_match = None
            if top_hit and top_hit["match_score"] >= 80:
                matched_product = next(
                    (p for p in fetch_products() if p["id"] == top_hit["entity_id"]), None
                )
                if matched_product:
                    registry_match = {
                        "product": dict(matched_product),
                        "companies": [dict(c) for c in fetch_product_companies(matched_product["id"])],
                        "ingredients": [dict(i) for i in fetch_product_ingredients(matched_product["id"])],
                        "regulatory_records": fetch_regulatory_records(matched_product["id"]),
                        "clinical_studies": fetch_clinical_studies(matched_product["id"]),
                        "patents": fetch_patents(matched_product["id"]),
                        "trademarks": [],
                        "safety_signals": fetch_safety_signals(matched_product["id"]),
                    }

            canonical = build_canonical_search_response(
                query, query_type, df.to_dict("records"), full_report["market_data"], registry_match,
            )

            if canonical["canonical_entity"]["verified"]:
                st.success(f"Matched a promoted registry product (fuzzy match score {top_hit['match_score']}).")
            else:
                st.info("No promoted registry product matched closely enough — built from raw search results.")

            if canonical["information_gaps"]:
                with st.expander(f"Information gaps ({len(canonical['information_gaps'])})", expanded=True):
                    for gap in canonical["information_gaps"]:
                        st.caption(f"• {gap}")

            canon_col1, canon_col2 = st.columns(2)
            canon_col1.write("**Companies**")
            canon_col1.dataframe(pd.DataFrame(canonical["companies"]), use_container_width=True, hide_index=True)
            canon_col2.write("**Ingredients**")
            canon_col2.dataframe(pd.DataFrame(canonical["ingredients"]), use_container_width=True, hide_index=True)

            st.download_button(
                "Download canonical structure (JSON)",
                data=json.dumps(canonical, indent=2, default=str),
                file_name=f"{query.replace(' ', '_')}_canonical.json",
                mime="application/json",
            )

    st.divider()
    st.caption(
        "Data limitations: results reflect what each public API currently indexes, not full "
        "market coverage. FDA-cleared, CE-marked, and registered are distinct regulatory "
        "statuses and are not interchangeable."
    )

with data_entry_tab:
    st.caption(
        "Every kind of manual or uploaded data, plus every scoring tool, lives here — "
        "market figures, documents, opportunity scoring, suppliers, competitor "
        "profiles, manual regulatory records, and the product-development tools. "
        "The Search tab only shows what a live connector search returns; Registry "
        "only shows what's been promoted."
    )

    (market_subtab, documents_subtab, opportunity_subtab, suppliers_de_subtab,
     competitors_de_subtab, regulatory_de_subtab, development_subtab) = st.tabs(
        ["Market Data", "Documents", "Opportunity Score", "Suppliers", "Competitors",
         "Regulatory Records", "Development"]
    )

    with market_subtab:
        st.subheader("Licensed and manually sourced market data")
        st.caption(
            "Upload a CSV/Excel export from a licensed source (IQVIA, Euromonitor, "
            "Mintel, etc.) or enter a figure manually. Every row keeps its own "
            "source, definition, and confidence rating, and is tagged Global, "
            "Regional, or Country so a global estimate is never confused with a "
            "country-specific number just because they're stored side by side. "
            "No global vendor publishes Iran-specific data for most medical/"
            "aesthetic categories — that gap is exactly what the Country level "
            "and manual upload exist for."
        )

        with st.expander("Add a figure manually", expanded=True):
            with st.form("manual_market_entry"):
                category = st.text_input("Category*", placeholder="dermal filler")
                scope_level = st.selectbox("Scope*", options=["global", "regional", "country"])
                c1, c2, c3 = st.columns(3)
                region = c1.text_input("Region (required if Regional)", placeholder="MENA")
                country = c2.text_input("Country (required if Country)", placeholder="Iran")
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
                        "category": category, "scope_level": scope_level,
                        "region": region or None, "country": country or None,
                        "year": year or None, "market_value": market_value or None,
                        "currency": currency, "growth_rate": growth_rate or None,
                        "source": source, "definition": definition,
                        "confidence_score": confidence_score,
                    }
                    valid_rows, errors = prepare_rows([record])
                    if errors:
                        for e in errors:
                            st.error(e)
                    else:
                        save_market_data(valid_rows)
                        st.success("Figure added.")

        st.caption(
            f"CSV/Excel upload columns: {', '.join(ALL_FIELDS)}. `scope_level` must be "
            "one of global/regional/country."
        )
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
        scope_filter = st.radio("Scope", options=["All", "global", "regional", "country"], horizontal=True)
        stored = fetch_market_data(scope_level=None if scope_filter == "All" else scope_filter)
        if stored:
            stored_df = pd.DataFrame([dict(r) for r in stored])
            st.dataframe(stored_df, use_container_width=True, hide_index=True)
        else:
            st.info("No market data stored at this scope yet.")

    with documents_subtab:
        st.subheader("Document ingestion")
        st.caption(
            "Upload a brochure, IFU, certificate, supplier technical document, or other "
            "PDF. Text is extracted per page and scanned for known ingredient and company "
            "names, keeping the file name and page number as the citation for anything "
            "pulled from it."
        )

        pdf_files = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=True)
        doc_source_type = st.selectbox(
            "Document type",
            ["manufacturer", "regulatory", "scientific", "commercial", "supplier_technical"],
        )
        known_supplier = None
        if doc_source_type == "supplier_technical":
            known_supplier = st.text_input(
                "Supplier name (optional)",
                placeholder="e.g. a raw-material supplier from the Suppliers section",
                help="Tagged into every page's company mentions even if it isn't a name "
                     "the automatic scan already recognizes — spec sheets, CoAs, and "
                     "safety data sheets often use a supplier's legal name, not a brand "
                     "the platform has seen before.",
            )

        if pdf_files and st.button("Extract and store"):
            total_pages = 0
            for pdf_file in pdf_files:
                records = ingest_pdf(
                    pdf_file.read(), pdf_file.name, source_type=doc_source_type,
                    known_supplier=known_supplier or None,
                )
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

    with opportunity_subtab:
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
            opp_submitted = st.form_submit_button("Calculate score")

        if opp_submitted:
            score = opportunity_score(scores)
            st.metric("Opportunity score", score)
            st.dataframe(pd.DataFrame(score_breakdown(scores, notes)), use_container_width=True, hide_index=True)

    with suppliers_de_subtab:
        st.caption(
            "Manual entry only — no supplier directory API exists to connect here. "
            "Use this for raw-material suppliers you've identified through research, "
            "trade shows, or direct outreach."
        )
        with st.form("add_supplier_form"):
            supplier_name = st.text_input("Supplier name*")
            s_col1, s_col2 = st.columns(2)
            supplier_type = s_col1.text_input("Supplier type (e.g. API supplier, CDMO)")
            supplier_country = s_col2.text_input("Country")
            gmp_status = s_col1.text_input("GMP status")
            material_category = s_col2.text_input("Material category")
            supplier_source_url = st.text_input("Source URL")
            supplier_submitted = st.form_submit_button("Add supplier")
        if supplier_submitted and supplier_name:
            add_supplier(
                supplier_name, supplier_type=supplier_type or None, country=supplier_country or None,
                gmp_status=gmp_status or None, material_category=material_category or None,
                source_url=supplier_source_url or None,
            )
            st.success("Supplier added.")

        suppliers = fetch_suppliers()
        if suppliers:
            supplier_df = pd.DataFrame([dict(s) for s in suppliers])
            st.dataframe(supplier_df, use_container_width=True, hide_index=True)

            sel_supplier_id = st.selectbox(
                "Inspect a supplier's materials",
                options=supplier_df["id"].tolist(),
                format_func=lambda sid: supplier_df.loc[supplier_df["id"] == sid, "supplier_name"].iloc[0],
            )
            with st.form("add_supplier_material_form"):
                trade_name = st.text_input("Trade/grade name")
                catalog_number = st.text_input("Catalog number")
                moq = st.text_input("Minimum order quantity")
                material_submitted = st.form_submit_button("Add material")
            if material_submitted and trade_name:
                add_supplier_material(
                    sel_supplier_id, trade_name=trade_name,
                    catalog_number=catalog_number or None, minimum_order_quantity=moq or None,
                )
                st.success("Material added — refresh to see it below.")

            materials = fetch_supplier_materials(sel_supplier_id)
            if materials:
                st.dataframe(pd.DataFrame([dict(m) for m in materials]), use_container_width=True, hide_index=True)
        else:
            st.info("No suppliers added yet.")

    with competitors_de_subtab:
        st.caption(
            "A structured competitive-positioning note per company — separate from raw "
            "search results, since this is analyst judgment, not a sourced fact."
        )
        companies = fetch_companies()
        if not companies:
            st.info("No companies in the registry yet — promote a product cluster in the Registry tab first.")
        else:
            company_df = pd.DataFrame([dict(c) for c in companies])
            with st.form("add_competitor_profile_form"):
                comp_company_id = st.selectbox(
                    "Company", options=company_df["id"].tolist(),
                    format_func=lambda cid: company_df.loc[company_df["id"] == cid, "canonical_name"].iloc[0],
                )
                c1, c2 = st.columns(2)
                strategic_segment = c1.text_input("Strategic segment")
                threat_level = c2.text_input("Threat level")
                competitive_advantage = st.text_area("Competitive advantage")
                competitive_weakness = st.text_area("Competitive weakness")
                profile_analyst = st.text_input("Your name")
                profile_submitted = st.form_submit_button("Save competitor profile")
            if profile_submitted:
                add_competitor_profile(
                    comp_company_id, strategic_segment=strategic_segment or None,
                    threat_level=threat_level or None,
                    competitive_advantage=competitive_advantage or None,
                    competitive_weakness=competitive_weakness or None,
                    analyst=profile_analyst or None,
                )
                st.success("Profile saved.")

            profiles = fetch_competitor_profiles()
            if profiles:
                st.dataframe(pd.DataFrame([dict(p) for p in profiles]), use_container_width=True, hide_index=True)
            else:
                st.info("No competitor profiles yet.")

    with regulatory_de_subtab:
        st.caption(
            "For jurisdictions without a connector here (TGA, MFDS, PMDA) — enter what "
            "you found by hand, with its own source, rather than leaving the gap silent. "
            "A product must be promoted in the Registry tab first."
        )
        reg_products = fetch_products()
        if not reg_products:
            st.info("No products promoted yet — go to the Registry tab first.")
        else:
            reg_product_df = pd.DataFrame([dict(p) for p in reg_products])
            reg_product_id = st.selectbox(
                "Product",
                options=reg_product_df["id"].tolist(),
                format_func=lambda pid: reg_product_df.loc[reg_product_df["id"] == pid, "canonical_name"].iloc[0],
                key="regulatory_de_product_select",
            )

            existing_reg_records = fetch_regulatory_records(reg_product_id)
            st.write(f"**Existing regulatory records** ({len(existing_reg_records)})")
            if existing_reg_records:
                st.dataframe(
                    pd.DataFrame([dict(r) for r in existing_reg_records]),
                    use_container_width=True, hide_index=True,
                )
            else:
                st.caption("None yet for this product.")

            with st.form("manual_regulatory_form"):
                jurisdiction = st.text_input("Jurisdiction (e.g. AU, KR, JP)")
                authority = st.text_input("Authority (e.g. TGA, MFDS, PMDA)")
                status = st.text_input("Status")
                registration_number = st.text_input("Registration/approval number")
                manual_source_url = st.text_input("Source URL")
                manual_submitted = st.form_submit_button("Add record")
            if manual_submitted and jurisdiction:
                add_regulatory_record(
                    reg_product_id, jurisdiction=jurisdiction, authority=authority,
                    status=status or None, registration_number=registration_number or None,
                    source_url=manual_source_url or None, source_type="analyst_manual_entry",
                )
                st.success("Added — refresh to see it above.")

    with development_subtab:
        st.caption(
            "Formulation development, risk management, stage-gate tracking, cost modeling, "
            "and portfolio-gap analysis — all tied to a promoted product from the Registry tab. "
            "A market-attractive product can still fail a stop criterion here; the two are "
            "checked independently on purpose."
        )

        dev_products = fetch_products()
        if not dev_products:
            st.info("No products promoted yet — go to the Registry tab first.")
        else:
            dev_product_df = pd.DataFrame([dict(p) for p in dev_products])
            dev_product_id = st.selectbox(
                "Product",
                options=dev_product_df["id"].tolist(),
                format_func=lambda pid: dev_product_df.loc[dev_product_df["id"] == pid, "canonical_name"].iloc[0],
                key="dev_product_select",
            )

            (qttp_subtab, risk_subtab, stage_gate_subtab,
             cost_subtab, portfolio_subtab) = st.tabs(
                ["QTPP / CQA / CPP", "Risk Assessment", "Stage Gate", "Cost Model", "Portfolio Gaps"]
            )

            with qttp_subtab:
                st.write("**Quality Target Product Profile**")
                with st.form("qttp_form"):
                    q1, q2 = st.columns(2)
                    dosage_form = q1.text_input("Dosage form")
                    route = q2.text_input("Route")
                    strength = q1.text_input("Strength")
                    sterility_requirement = q2.text_input("Sterility requirement")
                    qttp_submitted = st.form_submit_button("Save QTTP")
                if qttp_submitted:
                    add_qttp(dev_product_id, dosage_form=dosage_form or None, route=route or None,
                              strength=strength or None, sterility_requirement=sterility_requirement or None)
                    st.success("Saved.")
                existing_qttp = fetch_qttp(dev_product_id)
                if existing_qttp:
                    st.dataframe(pd.DataFrame([dict(q) for q in existing_qttp]), use_container_width=True, hide_index=True)

                st.write("**Critical Quality Attributes**")
                with st.form("cqa_form"):
                    attribute_name = st.text_input("Attribute name")
                    c1, c2 = st.columns(2)
                    attribute_category = c1.selectbox("Category", options=[""] + CQA_CATEGORIES)
                    criticality = c2.text_input("Criticality")
                    acceptable_range = st.text_input("Acceptable range")
                    cqa_submitted = st.form_submit_button("Add CQA")
                if cqa_submitted and attribute_name:
                    add_cqa(dev_product_id, attribute_name, attribute_category=attribute_category or None,
                             criticality=criticality or None, acceptable_range=acceptable_range or None)
                    st.success("Added.")
                cqas = fetch_cqas(dev_product_id)
                if cqas:
                    st.dataframe(pd.DataFrame([dict(c) for c in cqas]), use_container_width=True, hide_index=True)

                st.write("**Critical Process Parameters**")
                with st.form("cpp_form"):
                    parameter_name = st.text_input("Parameter name")
                    process_step = st.text_input("Process step")
                    cpp_range = st.text_input("Acceptable range", key="cpp_range")
                    cpp_submitted = st.form_submit_button("Add CPP")
                if cpp_submitted and parameter_name:
                    add_cpp(dev_product_id, parameter_name, process_step=process_step or None,
                             acceptable_range=cpp_range or None)
                    st.success("Added.")
                cpps = fetch_cpps(dev_product_id)
                if cpps:
                    st.dataframe(pd.DataFrame([dict(c) for c in cpps]), use_container_width=True, hide_index=True)

                st.write("**Control Strategy**")
                with st.form("control_form"):
                    test_or_control = st.text_input("Test or control")
                    acceptance_criteria = st.text_input("Acceptance criteria")
                    control_submitted = st.form_submit_button("Add control")
                if control_submitted and test_or_control:
                    add_control(dev_product_id, test_or_control, acceptance_criteria=acceptance_criteria or None)
                    st.success("Added.")
                controls = fetch_controls(dev_product_id)
                if controls:
                    st.dataframe(pd.DataFrame([dict(c) for c in controls]), use_container_width=True, hide_index=True)

            with risk_subtab:
                st.caption(
                    "Risk priority number = severity x occurrence x detectability (1-5 each, 1-125 total). "
                    "A stop-criterion match overrides any opportunity score — it's checked "
                    "independently, not folded into a single number."
                )
                with st.form("risk_form"):
                    risk_category = st.selectbox("Risk category", options=RISK_CATEGORIES)
                    risk_event = st.text_input("Risk event")
                    effect = st.text_area("Effect")
                    r1, r2, r3 = st.columns(3)
                    severity = r1.slider("Severity", 1, 5, 3)
                    occurrence = r2.slider("Occurrence", 1, 5, 3)
                    detectability = r3.slider("Detectability", 1, 5, 3)
                    existing_controls = st.text_input("Existing controls")
                    risk_submitted = st.form_submit_button("Add risk")
                if risk_submitted and risk_event:
                    rpn = risk_priority_number(severity, occurrence, detectability)
                    add_risk_assessment(
                        risk_category, risk_event, product_id=dev_product_id, effect=effect or None,
                        severity=severity, occurrence=occurrence, detectability=detectability,
                        risk_priority_number=rpn, existing_controls=existing_controls or None,
                        residual_risk=risk_acceptability(rpn),
                    )
                    stops = check_stop_criteria([risk_event, effect])
                    if stops:
                        st.error(f"Stop-criterion language detected: {', '.join(stops)} — review before proceeding.")
                    else:
                        st.success(f"Added. RPN = {rpn} ({risk_acceptability(rpn)}).")

                risks = fetch_risk_assessments(dev_product_id)
                if risks:
                    st.dataframe(pd.DataFrame([dict(r) for r in risks]), use_container_width=True, hide_index=True)
                else:
                    st.info("No risks logged for this product yet.")

            with stage_gate_subtab:
                current = fetch_stage_gate_decisions(dev_product_id)
                if current:
                    st.metric("Current stage", current[0]["stage"])
                    st.metric("Last decision", current[0]["decision"])

                with st.form("stage_gate_form"):
                    stage = st.selectbox("Stage", options=STAGE_GATE_STAGES)
                    decision = st.selectbox("Decision", options=STAGE_GATE_DECISIONS)
                    criteria = st.text_area("Criteria required for this gate")
                    evidence = st.text_area("Evidence presented")
                    open_risks = st.text_input("Open risks")
                    decision_owner = st.text_input("Decision owner")
                    gate_submitted = st.form_submit_button("Record decision")
                if gate_submitted:
                    add_stage_gate_decision(
                        dev_product_id, stage, decision, criteria=criteria or None,
                        evidence=evidence or None, open_risks=open_risks or None,
                        decision_owner=decision_owner or None,
                    )
                    st.success("Recorded.")

                history = fetch_stage_gate_decisions(dev_product_id)
                if history:
                    st.dataframe(pd.DataFrame([dict(h) for h in history]), use_container_width=True, hide_index=True)

            with cost_subtab:
                with st.form("cost_form"):
                    scenario = st.selectbox("Scenario", options=["base_case", "optimistic_case", "conservative_case"])
                    c1, c2, c3 = st.columns(3)
                    material_cost = c1.number_input("Material cost", min_value=0.0, value=0.0)
                    packaging_cost = c2.number_input("Packaging cost", min_value=0.0, value=0.0)
                    manufacturing_cost = c3.number_input("Manufacturing cost", min_value=0.0, value=0.0)
                    analytical_cost = c1.number_input("Analytical cost", min_value=0.0, value=0.0)
                    regulatory_cost = c2.number_input("Regulatory cost", min_value=0.0, value=0.0)
                    distribution_cost = c3.number_input("Distribution cost", min_value=0.0, value=0.0)
                    target_price = st.number_input("Target price", min_value=0.0, value=0.0)
                    fixed_investment = st.number_input("Fixed launch investment (for break-even)", min_value=0.0, value=0.0)
                    cost_submitted = st.form_submit_button("Save cost model")

                if cost_submitted:
                    costs = {
                        "material_cost": material_cost, "packaging_cost": packaging_cost,
                        "manufacturing_cost": manufacturing_cost, "analytical_cost": analytical_cost,
                        "regulatory_cost": regulatory_cost, "distribution_cost": distribution_cost,
                    }
                    cogs = estimated_cogs(costs)
                    margin = gross_margin(target_price, cogs)
                    bev = break_even_volume(fixed_investment, target_price, cogs)
                    add_cost_model(
                        dev_product_id, scenario=scenario, **costs,
                        estimated_cogs=cogs, target_price=target_price or None,
                        gross_margin=margin, break_even_volume=bev,
                    )
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Estimated COGS", cogs)
                    col2.metric("Gross margin", f"{margin:.1%}" if margin is not None else "n/a")
                    col3.metric("Break-even volume", bev if bev is not None else "n/a")

                cost_models = fetch_cost_models(dev_product_id)
                if cost_models:
                    st.dataframe(pd.DataFrame([dict(c) for c in cost_models]), use_container_width=True, hide_index=True)

            with portfolio_subtab:
                st.caption(
                    "Not tied to a single product — a portfolio gap is about a category/segment/"
                    "geography combination your team doesn't cover yet, evaluated against what "
                    "competitors already offer there."
                )
                with st.form("portfolio_gap_form"):
                    portfolio_category = st.text_input("Category")
                    p1, p2 = st.columns(2)
                    customer_segment = p1.text_input("Customer segment")
                    geography = p2.text_input("Geography")
                    current_coverage = st.text_input("Current coverage")
                    competitor_coverage = st.text_input("Competitor coverage")
                    recommended_action = st.selectbox("Recommended action", options=[""] + RECOMMENDED_ACTIONS)
                    gap_submitted = st.form_submit_button("Add gap")
                if gap_submitted and portfolio_category:
                    add_portfolio_gap(
                        portfolio_category, customer_segment=customer_segment or None, geography=geography or None,
                        current_coverage=current_coverage or None, competitor_coverage=competitor_coverage or None,
                        recommended_action=recommended_action or None,
                    )
                    st.success("Added.")

                gaps = fetch_portfolio_gaps()
                if gaps:
                    st.dataframe(pd.DataFrame([dict(g) for g in gaps]), use_container_width=True, hide_index=True)
                else:
                    st.info("No portfolio gaps logged yet.")

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
                for r in new_results:
                    log_change_event(
                        "search_result", "new_product",
                        entity_id=None, field_name="identifier", new_value=r.identifier,
                        source=r.source_name, review_status="awaiting_review",
                    )
            else:
                st.info("No new records since the last run.")

with registry_tab:
    st.subheader("Product registry")
    st.caption(
        "The verified layer. Nothing here is written automatically — a search result "
        "cluster only becomes a product when someone promotes it, at which point every "
        "field gets a citation back to the source row it came from. This is the "
        "raw → normalized → verified evidence → analyst interpretation pipeline: "
        "everything in Search/Entities is raw or normalized; only a promoted product "
        "here counts as verified. There are no other entry forms here — suppliers, "
        "competitor profiles, and manual regulatory records are entered in the "
        "Data Entry & Scoring tab."
    )

    (promote_subtab, browse_subtab, ingredients_subtab,
     search_subtab, audit_subtab) = st.tabs(
        ["Promote a cluster", "Browse products", "Ingredients", "Search", "Audit Log"]
    )

    with promote_subtab:
        all_rows = [dict(r) for r in fetch_all_results()]
        if not all_rows:
            st.info("No stored results yet — run a search first.")
        else:
            clusters = cluster_entities_with_members(all_rows)
            options = [c["canonical_title"] for c in clusters if c["record_count"] >= 1]
            chosen_title = st.selectbox("Cluster to promote", options=options)
            chosen = next(c for c in clusters if c["canonical_title"] == chosen_title)

            st.write(f"**{chosen['record_count']} record(s)** from sources: "
                     f"{', '.join(chosen['source_types']) or 'none'}")
            st.dataframe(pd.DataFrame(chosen["members"]), use_container_width=True, hide_index=True)

            with st.form("promote_form"):
                canonical_name = st.text_input("Canonical product name", value=chosen_title)
                product_type = st.selectbox("Product type", options=[""] + PRODUCT_TYPES)
                regulatory_category = st.selectbox(
                    "Regulatory category", options=REGULATORY_CATEGORIES,
                    index=REGULATORY_CATEGORIES.index("unknown"),
                )
                analyst = st.text_input("Your name (recorded on every citation)", value="unattributed")
                submitted = st.form_submit_button("Promote to product registry")

            if submitted:
                product_id = promote_cluster(
                    canonical_name, chosen["members"], analyst=analyst,
                    product_type=product_type or None,
                    regulatory_category=regulatory_category,
                )
                completeness = registry_completeness(product_id)
                st.success(f"Promoted as product #{product_id}.")
                if not completeness["has_any_regulatory_evidence"]:
                    st.warning(
                        "No regulatory-tier source contributed to this cluster — this "
                        "product has commercial/discovery evidence only so far."
                    )

    with browse_subtab:
        products = fetch_products()
        if not products:
            st.info("No products promoted yet.")
        else:
            product_df = pd.DataFrame([dict(p) for p in products])
            st.dataframe(product_df, use_container_width=True, hide_index=True)

            selected_id = st.selectbox(
                "Inspect a product",
                options=product_df["id"].tolist(),
                format_func=lambda pid: product_df.loc[product_df["id"] == pid, "canonical_name"].iloc[0],
            )

            aliases = fetch_aliases(selected_id)
            companies = fetch_product_companies(selected_id)
            reg_records = fetch_regulatory_records(selected_id)
            prod_ingredients = fetch_product_ingredients(selected_id)
            evidence = fetch_field_evidence("product", selected_id)

            st.write(f"**Aliases** ({len(aliases)})")
            st.dataframe(pd.DataFrame([dict(a) for a in aliases]), use_container_width=True, hide_index=True)

            st.write(f"**Companies** ({len(companies)})")
            st.dataframe(pd.DataFrame([dict(c) for c in companies]), use_container_width=True, hide_index=True)

            st.write(f"**Regulatory records** ({len(reg_records)})")
            if reg_records:
                st.dataframe(pd.DataFrame([dict(r) for r in reg_records]), use_container_width=True, hide_index=True)
            else:
                st.caption(
                    "None yet — this product has no regulatory-tier evidence attached. "
                    "Add one manually in Data Entry & Scoring > Regulatory Records."
                )

            clinical_studies = fetch_clinical_studies(selected_id)
            st.write(f"**Clinical studies** ({len(clinical_studies)})")
            if clinical_studies:
                st.dataframe(pd.DataFrame([dict(s) for s in clinical_studies]), use_container_width=True, hide_index=True)
            else:
                st.caption("None promoted yet — clinical_study-type cluster members become studies automatically on promotion.")

            product_patents = fetch_patents(selected_id)
            st.write(f"**Patents** ({len(product_patents)})")
            if product_patents:
                st.dataframe(pd.DataFrame([dict(p) for p in product_patents]), use_container_width=True, hide_index=True)
            else:
                st.caption("None promoted yet — patent-type cluster members become patent records automatically on promotion.")

            st.write(f"**Ingredients** ({len(prod_ingredients)})")
            all_ingredients = fetch_ingredients()
            if all_ingredients:
                with st.form("link_ingredient_form"):
                    ing_df = pd.DataFrame([dict(i) for i in all_ingredients])
                    ing_choice = st.selectbox(
                        "Add an ingredient from the registry",
                        options=ing_df["id"].tolist(),
                        format_func=lambda iid: ing_df.loc[ing_df["id"] == iid, "preferred_name"].iloc[0],
                    )
                    role = st.text_input("Role in this product (e.g. active_substance)")
                    concentration = st.text_input("Concentration (leave blank if not disclosed)")
                    link_submitted = st.form_submit_button("Link ingredient")
                if link_submitted:
                    link_product_ingredient(
                        selected_id, ing_choice, ingredient_role=role or None,
                        concentration=concentration or None,
                        concentration_type="not_disclosed" if not concentration else "exact",
                    )
                    st.success("Linked — refresh to see it below.")
            if prod_ingredients:
                st.dataframe(pd.DataFrame([dict(i) for i in prod_ingredients]), use_container_width=True, hide_index=True)

            with st.expander(f"Field-level citations ({len(evidence)})"):
                st.dataframe(pd.DataFrame([dict(e) for e in evidence]), use_container_width=True, hide_index=True)

            with st.expander("Knowledge graph"):
                st.caption(
                    "Built on demand from the registry tables above — not a separate "
                    "store, just a relationship view over the same rows."
                )
                graph = build_product_graph(selected_id)
                graph_summary_data = graph_summary(graph)
                if graph_summary_data["edge_count"] == 0:
                    st.info("No relationships yet — link a company, ingredient, study, or patent first.")
                else:
                    g1, g2 = st.columns(2)
                    g1.metric("Nodes", graph_summary_data["node_count"])
                    g2.metric("Edges", graph_summary_data["edge_count"])
                    st.write(graph_summary_data["node_types"])
                    st.dataframe(pd.DataFrame(graph_to_edge_list(graph)), use_container_width=True, hide_index=True)

    with ingredients_subtab:
        st.caption(
            "The ingredient registry includes a seed set of real, individually verified "
            "entries pulled from FDA DailyMed labels, EU CosIng, and INCI databases during "
            "prior research — including recombinant growth factors identified by their "
            "actual biological identity, not just their INCI code."
        )
        if st.button("Load seed ingredients (INCI-verified entries)"):
            ids = seed_ingredients()
            st.success(f"{len(ids)} ingredient(s) present in the registry (existing entries kept as-is).")

        ingredients = fetch_ingredients()
        if ingredients:
            st.dataframe(pd.DataFrame([dict(i) for i in ingredients]), use_container_width=True, hide_index=True)
        else:
            st.info("No ingredients in the registry yet.")

    with search_subtab:
        st.caption(
            "Fuzzy text search across products, aliases, companies, and ingredients in one "
            "box — RapidFuzz matching, not embeddings-based semantic search, so it tolerates "
            "typos and partial names but doesn't understand meaning or synonyms beyond what's "
            "already in the alias/synonym tables."
        )
        registry_query = st.text_input("Search the registry")
        if registry_query:
            hits = search_registry(registry_query)
            if hits:
                st.dataframe(pd.DataFrame(hits), use_container_width=True, hide_index=True)
            else:
                st.info("No matches above the similarity threshold.")

    with audit_subtab:
        st.caption(
            "Every promotion is logged here with who did it and what it touched. There's no "
            "login system in front of this app, so 'actor' is whatever name was typed into "
            "the promotion form — provenance, not access control."
        )
        audit_rows = fetch_audit_log()
        if audit_rows:
            st.dataframe(pd.DataFrame([dict(a) for a in audit_rows]), use_container_width=True, hide_index=True)
        else:
            st.info("No audit events yet.")

        st.write("**Change events** (new records surfaced by the Monitoring tab)")
        change_rows = fetch_change_events()
        if change_rows:
            st.dataframe(pd.DataFrame([dict(c) for c in change_rows]), use_container_width=True, hide_index=True)
        else:
            st.info("No change events logged yet — run a check in the Monitoring tab.")
