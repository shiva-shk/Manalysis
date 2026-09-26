# Medical Product Intelligence Platform

A traceable research tool for aesthetic/medical products, ingredients, and
companies. Every result carries its source and an evidence score, so
verified regulatory data is never presented with the same confidence as a
market estimate or a discovery-source lead.

## What's in it

- Query classifier (brand vs. ingredient vs. company vs. regulatory ID)
- Synonym expansion for ingredient naming (PDRN, polynucleotide, etc.)
- Connectors to official/scientific sources with public APIs:
  - ClinicalTrials.gov (v2 REST API)
  - PubMed, via the Europe PMC REST API
  - openFDA (510(k) device clearances, drug labels)
  - EPO Open Patent Services (needs `EPO_OPS_CONSUMER_KEY` /
    `EPO_OPS_CONSUMER_SECRET` — free registration at developers.epo.org)
  - EUDAMED (EU medical devices) — no documented public API; this calls the
    same JSON endpoint its own search page's frontend uses. Off by default:
    it's undocumented, can take 15-20+ seconds per search, and can break or
    rate-limit without notice. Prefer EUDAMED's official bulk data export
    (linked from its search page) for anything beyond ad hoc lookups.
  - Health Canada MDALL (medical device active licences) — no public API;
    this drives the search form directly (session cookie + CSRF token,
    then a device-name search), parsing the HTML results table. Off by
    default for the same reasons as EUDAMED.
- Result normalization into one common schema
- Evidence scoring by source type and record completeness
- Fuzzy deduplication (name similarity plus a matching identifier or company)
- A curated ingredient reference table (INCI name, CAS number, class)
- SQLite storage of every search run
- Product/entity profile view grouping stored records by title
- Market Data tab: manual entry or CSV/Excel upload of licensed figures,
  each row keeping its own source, definition, and confidence rating
- Document ingestion: upload a PDF (brochure, IFU, certificate) and extract
  text per page, tagged with any known ingredient/company mentions, with
  file name and page number kept as the citation
- Development-opportunity scoring (transparent, weighted, 1-5 per dimension)
- Entities tab: clusters stored results into canonical entities across
  every query you've ever run, not just a single search
- Monitoring tab: re-runs a saved query on demand and flags only the
  records whose identifier wasn't already stored from a previous run
- Registry tab: the verified-evidence layer on top of everything above.
  A person promotes a cluster of search results into a canonical
  product, which creates a company (with a role: brand owner,
  manufacturer, etc.), an alias for every raw title seen, a regulatory
  record for every member from an official-tier source, and a
  field-level citation for every promoted value, so a registry record
  always answers "where did this come from, and who said it was one
  product." Nothing writes to the registry automatically — only a
  promotion does. Also includes a real, individually-sourced ingredient
  reference table (INCI names, CAS numbers where the ingredient is a
  single compound, correctly no CAS number for exosome/EV preparations)
  and a controlled taxonomy (product types, regulatory categories,
  ingredient roles, company roles) so free-text values don't drift.
- Streamlit UI with Excel and PDF export

Commercial market-data sources (IQVIA, Euromonitor, Mintel, etc.) are not
queried automatically since they generally sit behind a paid subscription —
use the Market Data tab's upload/manual-entry path instead of scraping them.

## Running it

```
pip install -r requirements.txt
streamlit run app.py
```

## Running tests

```
pytest
```

Tests cover the classifier, synonym expansion, evidence scoring,
deduplication, connector normalization, market-data validation, document
ingestion, opportunity scoring, product profiling, cross-query entity
clustering, the monitoring diff logic, and the registry layer (entity
promotion, field-level lineage, taxonomy validation, ingredient seed
data) — all against canned data or generated fixtures, no network calls
in the test suite.

## Architecture: what's built vs. deferred

This app is built against a larger target architecture (source layer →
data management → knowledge database → analysis → decision support →
reports/monitoring). Following that design's own stated build order:

**Built (its "first priority" list):** product/company identity with
role separation, product aliases, an ingredient/composition registry,
field-level citations, official regulatory connectors, document
ingestion, Excel/PDF export.

**Deferred (its "second/third/fourth priority" lists, not started):**
formulation development (QTPP, CQAs, CPPs, control strategy), stability
and batch management, supplier/licensing database, cost modeling,
stage-gate workflow, a real risk-management system, a knowledge graph,
semantic search, scheduled/automated monitoring, multi-user access and
audit trails, and connectors to TGA, MFDS, PMDA, KIPRIS, and paid market
data providers (IQVIA, Euromonitor, Mintel, etc.). Building all of this
in one pass would mean a lot of thin, undertested surface area; the
priority order in the design doc is the intended sequence for adding
the rest.

## Known limitations

- FDA-cleared, CE-marked, registered, and approved are distinct regulatory
  statuses and are shown as reported, not normalized into one label.
- A product appearing in a source does not mean it is currently marketed
  everywhere.
- The product/entity profile groups records by an exact title match — a
  stand-in for real entity resolution, not a verified merge.
- Patent search only works with a registered EPO OPS key and network access
  to `ops.epo.org`. TGA ARTG, MFDS, and PMDA don't expose simple public
  APIs and aren't connected yet; TGA also publishes a downloadable bulk
  data extract, which would be more reliable than scraping its site.
- EUDAMED and Health Canada MDALL have no documented API at all — both
  connectors reverse-engineer the request their own frontend/search form
  makes (EUDAMED needs a browser-like User-Agent header or it 502s;
  MDALL needs a session cookie and CSRF token pulled from the search
  page first). Treat both as best-effort scrapers, not stable
  integrations — they can break silently if either site changes, and
  MDALL only matches literal substrings of a device name, so a phrase
  like "dermal filler" can return nothing even though "filler" alone
  returns real results.
- Document ingestion handles text-based PDFs; scanned documents need OCR,
  which isn't wired in yet.
- The opportunity score is a decision-support aid based on analyst-entered
  1-5 ratings, not an objective measure.
- The Entities tab clusters by name/company similarity, the same rule used
  for within-search deduplication — a match cluster, not a verified merge.
- Monitoring only diffs records that carry an identifier (NCT number,
  510(k) number, etc.); there's no background scheduler, so "monitoring"
  means re-running a saved query on demand, not continuous polling.
