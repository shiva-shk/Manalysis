# Medical Product Intelligence Platform — Phase 1 MVP

A traceable research tool for aesthetic/medical products, ingredients, and
companies. Every result carries its source and an evidence score, so
verified regulatory data is never presented with the same confidence as a
market estimate or a discovery-source lead.

## What's in this phase

- Query classifier (brand vs. ingredient vs. company vs. regulatory ID)
- Synonym expansion for ingredient naming (PDRN, polynucleotide, etc.)
- Connectors to official/scientific sources with public APIs:
  - ClinicalTrials.gov (v2 REST API)
  - PubMed, via the Europe PMC REST API
  - openFDA (510(k) device clearances, drug labels)
- Result normalization into one common schema
- Evidence scoring by source type and record completeness
- Fuzzy deduplication (name similarity plus a matching identifier or company)
- SQLite storage of every search run
- Streamlit UI with Excel export

Commercial market-data sources (IQVIA, Euromonitor, Mintel, etc.) are not
queried automatically since they generally sit behind a paid subscription.
Later phases add a manual upload path for licensed exports instead of
attempting to bypass access controls.

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
deduplication, and connector normalization against canned API responses —
no network calls in the test suite.

## Known limitations

- FDA-cleared, CE-marked, registered, and approved are distinct regulatory
  statuses and are shown as reported, not normalized into one label.
- A product appearing in a source does not mean it is currently marketed
  everywhere.
- Patent and full commercial market-size connectors are planned for later
  phases; see the project design notes for the full roadmap.
