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
ingestion, opportunity scoring, and product profiling — all against canned
data or generated fixtures, no network calls in the test suite.

## Known limitations

- FDA-cleared, CE-marked, registered, and approved are distinct regulatory
  statuses and are shown as reported, not normalized into one label.
- A product appearing in a source does not mean it is currently marketed
  everywhere.
- The product/entity profile groups records by an exact title match — a
  stand-in for real entity resolution, not a verified merge.
- Patent search only works with a registered EPO OPS key and network access
  to `ops.epo.org`; regional regulatory registries (TGA ARTG, EUDAMED,
  Health Canada, MFDS, PMDA) don't expose simple public APIs and are not
  yet connected.
- Document ingestion handles text-based PDFs; scanned documents need OCR,
  which isn't wired in yet.
- The opportunity score is a decision-support aid based on analyst-entered
  1-5 ratings, not an objective measure.
