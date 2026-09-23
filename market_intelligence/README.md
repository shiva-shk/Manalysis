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
clustering, and the monitoring diff logic — all against canned data or
generated fixtures, no network calls in the test suite.

## Known limitations

- FDA-cleared, CE-marked, registered, and approved are distinct regulatory
  statuses and are shown as reported, not normalized into one label.
- A product appearing in a source does not mean it is currently marketed
  everywhere.
- The product/entity profile groups records by an exact title match — a
  stand-in for real entity resolution, not a verified merge.
- Patent search only works with a registered EPO OPS key and network access
  to `ops.epo.org`. TGA ARTG, Health Canada, MFDS, and PMDA don't expose
  simple public APIs and aren't connected yet; TGA and Health Canada both
  publish downloadable bulk data extracts, which would be more reliable
  than scraping their search pages.
- EUDAMED has no documented API at all — the connector reverse-engineers
  the request its own frontend makes, including a browser-like User-Agent
  header the endpoint requires (it 502s on the default `python-requests`
  one). Treat it as best-effort, not a stable integration.
- Document ingestion handles text-based PDFs; scanned documents need OCR,
  which isn't wired in yet.
- The opportunity score is a decision-support aid based on analyst-entered
  1-5 ratings, not an objective measure.
- The Entities tab clusters by name/company similarity, the same rule used
  for within-search deduplication — a match cluster, not a verified merge.
- Monitoring only diffs records that carry an identifier (NCT number,
  510(k) number, etc.); there's no background scheduler, so "monitoring"
  means re-running a saved query on demand, not continuous polling.
