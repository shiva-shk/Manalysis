# Supplements sales ledger

A cleaned, combined ledger of Iranian dietary supplement sales (manufacturer to distributor), built
from the supplement producers syndicate yearbooks for Jalali years 1390 to 1404.

## Files

- `supplements_sales_ledger.xlsx` is the workbook.
  - `Summary`: totals and growth by year, with two charts.
  - `Ledger`: one line per company, product and year (18,656 lines), filterable.
  - `By company`, `By category`, `By dosage form`: sales value by year, built with live formulas over the Ledger.
  - `Cleaning log`, `Company merges`, `Excluded rows`: everything that was changed or left out.
- `supplements_sales_ledger_clean.csv` is the same ledger as plain text for other tools.
- `supplements_ledger_1.html` is the interactive dashboard (overview, companies, product explorer, ingredient and company deep dives, categories, dosage forms, ledger lines, IRR/USD view). It is one self-contained page. Rebuild it with `python -m supplements_ledger.build_dashboard`.
- `parse_raw.py` reads the raw yearbook tables, `clean.py` holds the cleaning rules,
  `families.py` assigns ingredient families, `build_ledger.py` writes the workbook and `build_dashboard.py` writes the dashboard.

## Rebuild

The raw yearbooks are not stored in the repo. Put them in one folder (file names ending in `-1396.md`
and so on, plus the combined file ending in `-1390-95.md`) and run from the repo root:

    SUPPLEMENTS_RAW_DIR=/path/to/yearbooks python -m supplements_ledger.build_ledger supplements_ledger/supplements_sales_ledger.xlsx

Open the result in Excel or LibreOffice and let it recalculate once so the formulas show values.

## Things to know

- Values are nominal rials. Growth from year to year is mostly price change.
- 1403 lists far fewer companies than 1402 and its publication date looks mistyped, so check it before trusting trends.
- From 1401 the yearbooks carry fewer descriptive columns, so license, manufacturer and status are empty for those years.
- Category is a standard grouping derived from the functional group each company reported. The original text is kept.
