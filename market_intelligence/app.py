"""Streamlit UI for the Medical Product Intelligence Platform.

Searches official/scientific sources (ClinicalTrials.gov, PubMed/Europe PMC,
openFDA, EPO patents when configured), scores results by evidence quality,
and exports to Excel/PDF. A separate tab holds manually entered or uploaded
market data, since commercial market-research sources are not queried
automatically.
"""

import pandas as pd
import streamlit as st

from analysis.entity_resolution import cluster_entities, cluster_entities_with_members
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
from database.registry_db import (
    add_competitor_profile,
    add_regulatory_record,
    add_supplier,
    add_supplier_material,
    fetch_aliases,
    fetch_clinical_studies,
    fetch_competitor_profiles,
    fetch_companies,
    fetch_field_evidence,
    fetch_ingredients,
    fetch_patents,
    fetch_product_companies,
    fetch_product_ingredients,
    fetch_products,
    fetch_regulatory_records,
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
from processing.taxonomy import PRODUCT_TYPES, REGULATORY_CATEGORIES
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

search_tab, market_tab, documents_tab, opportunity_tab, entities_tab, monitoring_tab, registry_tab = st.tabs(
    ["Search", "Market Data", "Documents", "Opportunity Score", "Entities", "Monitoring", "Registry"]
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

with registry_tab:
    st.subheader("Product registry")
    st.caption(
        "The verified layer. Nothing here is written automatically — a search result "
        "cluster only becomes a product when someone promotes it, at which point every "
        "field gets a citation back to the source row it came from. This is the "
        "raw → normalized → verified evidence → analyst interpretation pipeline: "
        "everything in Search/Entities is raw or normalized; only a promoted product "
        "here counts as verified."
    )

    (promote_subtab, browse_subtab, ingredients_subtab,
     suppliers_subtab, competitors_subtab) = st.tabs(
        ["Promote a cluster", "Browse products", "Ingredients", "Suppliers", "Competitors"]
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
                st.caption("None yet — this product has no regulatory-tier evidence attached.")

            with st.expander("Add a regulatory record manually"):
                st.caption(
                    "For jurisdictions without a connector here (TGA, MFDS, PMDA) — enter "
                    "what you found by hand, with its own source, rather than leaving the "
                    "gap silent."
                )
                with st.form("manual_regulatory_form"):
                    jurisdiction = st.text_input("Jurisdiction (e.g. AU, KR, JP)")
                    authority = st.text_input("Authority (e.g. TGA, MFDS, PMDA)")
                    status = st.text_input("Status")
                    registration_number = st.text_input("Registration/approval number")
                    manual_source_url = st.text_input("Source URL")
                    manual_submitted = st.form_submit_button("Add record")
                if manual_submitted and jurisdiction:
                    add_regulatory_record(
                        selected_id, jurisdiction=jurisdiction, authority=authority,
                        status=status or None, registration_number=registration_number or None,
                        source_url=manual_source_url or None, source_type="analyst_manual_entry",
                    )
                    st.success("Added — refresh to see it above.")

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

    with suppliers_subtab:
        st.caption(
            "Manual entry only — no supplier directory API exists to connect here. "
            "Use this for raw-material suppliers you've identified through research, "
            "trade shows, or direct outreach."
        )
        with st.form("add_supplier_form"):
            supplier_name = st.text_input("Supplier name*")
            s_col1, s_col2 = st.columns(2)
            supplier_type = s_col1.text_input("Supplier type (e.g. API supplier, CDMO)")
            country = s_col2.text_input("Country")
            gmp_status = s_col1.text_input("GMP status")
            material_category = s_col2.text_input("Material category")
            supplier_source_url = st.text_input("Source URL")
            supplier_submitted = st.form_submit_button("Add supplier")
        if supplier_submitted and supplier_name:
            add_supplier(
                supplier_name, supplier_type=supplier_type or None, country=country or None,
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

    with competitors_subtab:
        st.caption(
            "A structured competitive-positioning note per company — separate from raw "
            "search results, since this is analyst judgment, not a sourced fact."
        )
        companies = fetch_companies()
        if not companies:
            st.info("No companies in the registry yet — promote a product cluster first.")
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
