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
  - Korea OpenDART (`connectors/dart.py`) — official financial disclosure
    system for Korean-registered companies (needs `DART_API_KEY`, free
    registration at opendart.fss.or.kr). This isn't a keyword search like
    the others: it resolves a company name to a DART `corp_code` from a
    bulk corp-code list, then either reads a listed company's structured
    business-report financials or, for a private company that only files
    audit reports (감사보고서, common above Korea's external-audit
    threshold), pulls the audit-report document itself and reads the key
    figures (total assets, liabilities, revenue, employee count) out of
    its summary metadata. Not wired into the Search tab's generic
    multi-source flow, since it's a different query shape (a financial
    lookup, not a title/abstract search) — use it directly, or through the
    Market Data tab once figures are pulled.
- Result normalization into one common schema
- Evidence scoring by source type and record completeness
- Fuzzy deduplication (name similarity plus a matching identifier or company)
- A curated ingredient reference table (INCI name, CAS number, class)
- SQLite storage of every search run
- Product/entity profile view grouping stored records by title
- Market Data tab: manual entry or CSV/Excel upload of licensed figures,
  each row keeping its own source, definition, and confidence rating, and
  tagged with a `scope_level` (global/regional/country) plus separate
  `region`/`country` fields, so a global estimate, a regional figure
  (e.g. MENA), and a country-specific one (e.g. Iran, when no global
  vendor covers it) never get conflated just because they're stored in
  the same table. Filterable by scope when browsing what's stored.
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
  ingredient roles, company roles) so free-text values don't drift. A
  promotion also creates a `clinical_studies` record for any
  ClinicalTrials.gov cluster member and a `patents` record for any EPO
  patent cluster member, each deduplicated by registry/patent number so
  re-promoting the same trial or patent twice doesn't double it up.
  Includes manual-entry forms for suppliers, competitor profiles, and
  regulatory records from jurisdictions with no connector here (TGA,
  MFDS, PMDA), so those gaps are filled by hand with a source rather
  than left silent.
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
clustering, the monitoring diff logic, the registry layer (entity
promotion, field-level lineage, taxonomy validation, ingredient seed
data, clinical studies, patents, suppliers, competitor profiles), the
development layer (QTPP/CQA/CPP/control strategy, risk scoring and stop
criteria, stage-gate decisions, cost modeling, portfolio gaps), and the
knowledge graph/search/audit layer — all against canned data or
generated fixtures, no network calls in the test suite.

## Architecture: what's built vs. deferred

This app is built against a larger target architecture (source layer →
data management → knowledge database → analysis → decision support →
reports/monitoring). Following that design's own stated build order:

**Built ("first priority"):** product/company identity with role
separation, product aliases, an ingredient/composition registry,
field-level citations, official regulatory connectors, document
ingestion, Excel/PDF export.

**Built ("second priority", partial):** clinical-study and patent
records wired into the registry from the existing ClinicalTrials.gov
and EPO connectors; a manual-entry supplier database and
supplier-materials table; competitor profiles; manual regulatory-record
entry for jurisdictions with no connector. **Not built** from this
tier: actual TGA/MFDS/PMDA/KIPRIS connectors (still blocked or
undocumented, per the limitations below) and trademark search (no free
API found).

**Built ("third priority", partial):** a Development tab per promoted
product, backing the formulation-development framework (QTPP, CQAs,
CPPs, control strategy), a risk-assessment log (severity x occurrence x
detectability = risk priority number, mapped to an acceptability band,
plus a keyword-based stop-criteria check that's independent of any
opportunity score — a market-attractive product can still fail a stop
criterion), stage-gate decision tracking (gate 0 through 5, with a
"current stage" lookup), a cost model (COGS, gross margin, break-even
volume, and a cost-shift sensitivity check), and portfolio-gap logging
with a recommended-action taxonomy. **Not built** from this tier:
stability and batch management (needs real lab/stability data this app
has no way to generate), and licensing-partner scoring beyond what the
Suppliers tab already covers.

**Built ("fourth priority", partial):**
- A knowledge graph (NetworkX), built on demand from the registry
  tables for a single product — not a separate store to keep in sync.
  Shown as a relationship table (`owned_by`/`manufactured_by`/
  `distributed_by`/`contains`/`approved_by`/`studied_in`/`covered_by`)
  in the Registry tab's product detail view.
- Fuzzy cross-registry search (RapidFuzz) over products, aliases,
  companies, and ingredients in one box. Named plainly as fuzzy text
  matching, not "semantic search" — no embedding model or vector store
  is wired in, so it won't find something by meaning or synonym unless
  that synonym is already in the alias/synonym tables.
- An audit log: every promotion records who did it and what it
  touched. There's no login system in front of this single-machine
  app, so "actor" is a free-text name typed into a form — it's
  provenance, not access control, and the README says so rather than
  implying real authentication exists.
- A `change_events` table, logged from the Monitoring tab whenever a
  re-run surfaces a record not seen before.

**Not built, on purpose, not just "not yet":**
- **Real scheduled/automated monitoring.** Streamlit's execution model
  is request-response per page load; there's no persistent process to
  host a background scheduler safely inside the app itself. Monitoring
  stays on-demand (re-run a saved query, diff by identifier) rather
  than pretending to poll continuously when it can't.
- **Real user authentication.** Adding a login form without HTTPS
  termination, session management, or a hosting story to secure any of
  it would be security theater, worse than plainly not having it. The
  audit log captures provenance without claiming to be access control.
- **Paid market data provider integrations** (IQVIA, Euromonitor,
  Mintel, etc.) — same reasoning as always: no unauthorized scraping,
  and no licensed API credentials exist to connect. The Market Data
  tab's manual/upload path remains the intended entry point.

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
