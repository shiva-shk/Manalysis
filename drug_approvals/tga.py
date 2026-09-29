"""TGA (ARTG) rows.

The ARTG register has no public API. Rows are loaded from
data/raw/manual/tga_artg/tga_normalized.json.gz, which holds the rows from
the manually exported ARTG file, already in the unified row shape.
"""

import gzip
import json

try:
    from .common import DATA_DIR, ROW_FIELDS, new_row
except ImportError:
    from common import DATA_DIR, ROW_FIELDS, new_row

TGA_PATH = DATA_DIR / "raw" / "manual" / "tga_artg" / "tga_normalized.json.gz"


def load_tga() -> list[dict]:
    if not TGA_PATH.exists():
        return []
    with gzip.open(TGA_PATH, "rt", encoding="utf-8") as fh:
        rows = json.load(fh)
    return [new_row(**{k: v for k, v in r.items() if k in ROW_FIELDS}) for r in rows]
