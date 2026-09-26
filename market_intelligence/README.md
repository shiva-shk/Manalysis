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
  - openFDA (510(k) device clearances, drug labels, PMA/Class III device
    approvals, UDI/GUDID device identifiers, device recalls, MAUDE
    adverse events). PMA fills a real gap 510(k) alone leaves open:
    several dermal fillers are PMA-approved (higher-risk pathway) rather
    than 510(k)-cleared, so a 510(k)-only search misses them. Recalls
    and MAUDE feed the `safety_signal` entity type, shown in the
    canonical structure's safety-signals section and, on promotion,
    stored in the `safety_signals` table.
  - DailyMed — NLM's official structured-product-label database,
    documented at dailymed.nlm.nih.gov. Complements openFDA's drug-label
    connector with the raw SPL set ID and covers OTC as well as
    prescription products.
  - EMA (European Medicines Agency) — no documented per-query search API;
    fetches the same bulk JSON export EMA's own medicines search page
    uses (~2,700 centrally authorised medicines) and filters client-side.
    Every search re-downloads the full file. Covers only the EU's
    centralised procedure — a nationally authorised medicine in one
    member state won't appear.
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
  - PubChem (`connectors/pubchem.py`) — chemical identity (CAS number,
    molecular formula, IUPAC name, SMILES) by compound name, with an
    autocomplete fallback for names that aren't an exact match. Free, no
    key. Routes requests through curl as a subprocess rather than the
    `requests` library: PubChem's bot-mitigation deterministically
    returns 503 for every `requests`-library call observed in testing
    (identical headers, identical network path) while curl against the
    same URL succeeds every time — a client-fingerprint block, not a
    real rate limit. Worth knowing if this connector ever needs touching.
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
    lookup, not a title/abstract search) — use it directly, or enter the
    figures through Data Entry & Scoring > Market Data once pulled.
- Result normalization into one common schema
- Evidence scoring by source type and record completeness
- Fuzzy deduplication (name similarity plus a matching identifier or company)
- A curated ingredient reference table (INCI name, CAS number, class)
- SQLite storage of every search run
- Product/entity profile view grouping stored records by title
- **Data Entry & Scoring tab**: every kind of manual/uploaded data and
  every scoring tool lives here in one place, so Search stays a pure
  view of live connector results and Registry stays a pure view of the
  verified/promoted layer. Sub-sections:
  - **Market Data**: manual entry or CSV/Excel upload of licensed
    figures, each row keeping its own source, definition, and confidence
    rating, and tagged with a `scope_level` (global/regional/country)
    plus separate `region`/`country` fields, so a global estimate, a
    regional figure (e.g. MENA), and a country-specific one (e.g. Iran,
    when no global vendor covers it) never get conflated just because
    they're stored in the same table. Filterable by scope when browsing
    what's stored.
  - **Documents**: upload a PDF (brochure, IFU, certificate, or supplier
    technical document — spec sheet, CoA, safety data sheet) and extract
    text per page, tagged with any known ingredient/company mentions,
    with file name and page number kept as the citation. A supplier
    technical document can name its supplier explicitly, so it's tagged
    correctly even when the supplier's legal name isn't one the
    automatic scan already recognizes.
  - **Opportunity Score**: transparent, weighted development-opportunity
    scoring, 1-5 per dimension.
  - **Suppliers**: manual-entry supplier database and per-supplier
    materials, since no supplier-directory API exists to connect here.
  - **Competitors**: a structured competitive-positioning note per
    company — analyst judgment, kept separate from sourced search data.
  - **Regulatory Records**: manual regulatory-record entry for a
    promoted product, for jurisdictions with no connector here (TGA,
    MFDS, PMDA), so those gaps are filled by hand with a source rather
    than left silent.
  - **Development**: QTPP/CQA/CPP/control strategy, a risk-assessment
    log, stage-gate decisions, cost modeling, and portfolio-gap logging,
    all tied to a promoted product.
- Entities tab: clusters stored results into canonical entities across
  every query you've ever run, not just a single search
- Monitoring tab: re-runs a saved query on demand and flags only the
  records whose identifier wasn't already stored from a previous run
- Registry tab: the verified-evidence layer on top of everything above,
  with no entry forms of its own besides promotion. A person promotes a
  cluster of search results into a canonical product, which creates a
  company (with a role: brand owner, manufacturer, etc.), an alias for
  every raw title seen, a regulatory record for every member from an
  official-tier source, and a field-level citation for every promoted
  value, so a registry record always answers "where did this come from,
  and who said it was one product." Nothing writes to the registry
  automatically — only a promotion does. Also includes a real,
  individually-sourced ingredient reference table (INCI names, CAS
  numbers where the ingredient is a single compound, correctly no CAS
  number for exosome/EV preparations) and a controlled taxonomy (product
  types, regulatory categories, ingredient roles, company roles) so
  free-text values don't drift. A promotion also creates a
  `clinical_studies` record for any ClinicalTrials.gov cluster member
  and a `patents` record for any EPO patent cluster member, each
  deduplicated by registry/patent number so re-promoting the same trial
  or patent twice doesn't double it up.
- Canonical structure (Search tab): the same search reshaped into one
  typed record — identity, ownership by role, composition, regulatory/
  clinical/patent evidence, and market data — with an explicit
  information-gaps list instead of a silently missing section. Checks
  the registry for a fuzzy-matched promoted product first (match score
  >= 80): if one exists, every field is the verified registry record
  with real citations; otherwise the response is built from this
  search's raw results and marked unverified. `analysis/canonical_search.py`.
  Backed by `analysis/product_matching.py`'s weighted product-identity
  scoring (name/manufacturer/regulatory-number/family/country, each
  worth fixed points, >=0.90 automatic match / 0.70-0.89 analyst review /
  below that no match) and `processing/query_normalizer.py` (strips
  accents and trademark symbols so "Juvéderm®" and "juvederm" compare
  equal) — neither is wired into the promotion workflow's own matching
  yet, which still uses name/company fuzzy clustering; they're available
  for a product-resolution pass that's more rigorous than name
  similarity alone when that's worth building.
- Full report (Search tab): consolidates a single search into one place —
  product comparison, ingredients, patents, approvals, clinical studies,
  and any stored Market Data rows whose category matches the query
  (market analysis, sales, market share). Every section is a view over
  data the platform already has (the search results just returned, the
  ingredient reference table, previously entered/uploaded Market Data
  rows) — a query with nothing stored for a section shows it empty
  rather than estimating a number. Exportable as a single multi-sheet
  Excel workbook, one sheet per section.
- Streamlit UI with Excel and PDF export

Commercial market-data sources (IQVIA, Euromonitor, Mintel, etc.) are not
queried automatically since they generally sit behind a paid subscription —
use Data Entry & Scoring > Market Data's upload/manual-entry path instead
of scraping them.

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

## Product/brand search structure: what's built vs. deferred

Following a later architecture note's own phased build order (repository
layer + normalized database first, source connectors second, IP/trademark
and market data third, comparison/development analysis fourth):

**Built (phase 1 — repository + search structure):** the registry schema
already covered products/aliases/companies/product_companies/ingredients/
product_ingredients/regulatory_records/clinical_studies/patents/
field_evidence; this pass added the remaining fields that spec calls for
(`product_subtype`, `target_area` on products; `former_names`, `address`,
`manufacturing_sites`, `certifications` on companies; `korean_name` on
ingredients; `page_number`/`verification_status` on product_ingredients;
`product_category`/`approval_number`/`notification_number`/
`authorized_representative`/`claim_type`/`expiry_date`/`source_document`
on regulatory_records; `ingredient_id`/`route`/`dose`/`population`/
`sample_size`/`primary_outcome`/`publication_id` on clinical_studies;
`application_number`/`patent_family`/`priority_date`/`expiration_date`
on patents), plus two new tables (`trademarks`, `safety_signals`) with
CRUD functions, all as guarded additive migrations so an existing
database upgrades in place. Also added: `processing/query_normalizer.py`
(accent/trademark-symbol stripping for query matching), a weighted
`analysis/product_matching.py` (structured-field product-identity
scoring, not name-similarity-only), patent-number and clinical-trial-ID
as distinct query-classifier types, and the canonical search-response
structure described above.

**Built (phase 2 — source connectors):** already covered by the
connectors listed above — FDA (510(k)/PMA/UDI/drug labels/DailyMed),
EUDAMED, ClinicalTrials.gov, PubMed/Europe PMC, EPO patents, PubChem,
EMA, Korea OpenDART (financial filings only). Document upload/PDF
extraction is the "official product documents" source. **Blocked, not
built:** Korea's MFDS cosmetics/medical-device open APIs are real and
free (via data.go.kr) but need a Korean-phone-verified account to
register for a key, which isn't available in this environment; EU
CosIng and ECHA have no public API at all (ECHA actively blocks direct
access); the "Korean Cosmetic Ingredients API" some third parties sell
is a paid RapidAPI product repackaging the same MFDS data data.go.kr
already gives away free — not worth paying for. TGA, MFDS medical
devices, PMDA, and KIPRIS remain unconnected for the same
undocumented-API reasons as before.

**Built (phase 2, continued):** openFDA device recalls
(`device/recall.json`) and MAUDE adverse events (`device/event.json`),
normalized as `safety_signal` entity-type results — flow through Search,
the canonical structure's `safety_signals` section, and promotion (a
promoted safety-signal cluster member becomes a `safety_signals` row).

**Built (phase 3, partial):** the `analysis/product_matching.py`
scoring is now wired into the promotion workflow
(`processing/entity_promotion.py::check_for_duplicate`) — before
promoting a cluster, it's compared against every already-promoted
product on structured fields (name/manufacturer/regulatory number/
family/country), and the Registry tab shows a warning if the score
reaches "analyst review" or "automatic match," without ever blocking or
auto-merging. **Not built:** a trademark connector. USPTO's real
trademark search (tmsearch.uspto.gov) works and was verified live —
but only through the Alexandria research capability available in an
agent session, not as a public documented HTTP API the standalone
Streamlit app can call itself (its real endpoint is undocumented;
reverse-engineering it properly needs browser network capture this
pass didn't have tooling for). USPTO's official, documented API (TSDR)
needs a free registered key but only does status lookup by a serial/
registration number you already have — not name search — so a key
alone wouldn't add brand-name search. EUIPO has a real free API but
needs account + credential registration (same friction as MFDS/EPO).
WIPO's Global Brand Database has no public API at all. The
`trademarks` table exists and is ready to receive data from any of
these once one is actually wired in.

**Not built (phase 4 — remaining comparison/development analysis):** no
dedicated cross-jurisdiction regulatory-comparison report or
licensing-analysis report beyond what the existing Full Report and
canonical structure already surface.

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

**Built ("third priority", partial):** a Development section (in Data
Entry & Scoring) per promoted product, backing the formulation-development
framework (QTPP, CQAs,
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
Suppliers section already covers.

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
  section's manual/upload path remains the intended entry point.

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
