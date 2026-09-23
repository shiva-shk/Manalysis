import os
import tempfile

from database.db import fetch_market_data, save_market_data
from processing.market_data import prepare_rows


def test_save_and_fetch_market_data():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        valid_rows, errors = prepare_rows([
            {"category": "dermal filler", "region": "EU", "source": "Mintel", "confidence_score": 0.7},
        ])
        assert not errors

        inserted = save_market_data(valid_rows, db_path=path)
        assert inserted == 1

        stored = fetch_market_data(db_path=path)
        assert len(stored) == 1
        assert stored[0]["category"] == "dermal filler"
    finally:
        os.remove(path)
