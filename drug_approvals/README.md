# Drug Approvals Tracker data pipeline

Builds the JSON behind the Drug Approvals Tracker page (`web/index.html`).

```
pip install -r requirements.txt
python scripts/export_json.py        # writes data/out/approvals-N.json, manifest.json, meta.json
python -m pytest tests
```

Publish `web/index.html` together with the files from `data/out/` placed under `data/`.

## Sources

| Region | Source | What a row is | Approval date |
|---|---|---|---|
| FDA | openFDA Drugs@FDA bulk file (`download.open.fda.gov/drug/drugsfda`) | One application (NDA, BLA or ANDA) | Date of the original (ORIG) submission that reached approval. Tentative-only applications are skipped. |
| EMA | EMA medicines bulk JSON report | One centrally authorised human medicine | European Commission marketing authorisation date (DD/MM/YYYY in the source). Positive CHMP opinions still awaiting the decision are kept and dated by the opinion. |
| FDA text | openFDA drug label endpoint (DailyMed SPL data) | Indication, dosing and label date for NDA and BLA rows, matched by application number | n/a |
| TGA | Manual ARTG export, stored as `data/raw/manual/tga_artg/tga_normalized.json.gz` | One ARTG entry | From the export |

Downloads are cached for 12 hours in `data/raw/cache/`.

## What changed from the earlier tracker data

- FDA rows came from the Orange Book, which left 30% of rows with no approval date and mixed marketing status into the status column. They now come from Drugs@FDA, so every row has the original approval date and NDA/BLA/ANDA type.
- EMA was cut off at 500 of about 2,700 records, mixed in veterinary medicines, refused and withdrawn applications, and used the wrong date. It now covers all human medicines that were authorised, with the correct date.
- Orphan flags are real booleans.

## Known gaps

- FDA rows have no orphan flag, because Drugs@FDA does not carry it. ANDA rows have no indication or dosing text, because only NDA and BLA labels are looked up. Use `--skip-labels` to skip the slow label lookup.
- EMA rows have no dosage form or strength. The EMA report does not publish them.
- Veterinary EMA medicines are excluded (`normalize_ema(..., include_veterinary=True)` keeps them).
