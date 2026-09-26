import os
import tempfile

from database.db import fetch_market_data, save_market_data
from processing.market_data import prepare_rows


def test_save_and_fetch_market_data():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        valid_rows, errors = prepare_rows([
            {"category": "dermal filler", "scope_level": "regional", "region": "EU",
             "source": "Mintel", "confidence_score": 0.7},
        ])
        assert not errors

        inserted = save_market_data(valid_rows, db_path=path)
        assert inserted == 1

        stored = fetch_market_data(db_path=path)
        assert len(stored) == 1
        assert stored[0]["category"] == "dermal filler"
    finally:
        os.remove(path)


def test_fetch_market_data_filters_by_scope_level():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        valid_rows, errors = prepare_rows([
            {"category": "dermal filler", "scope_level": "global", "source": "Grand View Research"},
            {"category": "dermal filler", "scope_level": "country", "country": "Iran", "source": "Internal"},
        ])
        assert not errors
        save_market_data(valid_rows, db_path=path)

        country_only = fetch_market_data(scope_level="country", db_path=path)
        assert len(country_only) == 1
        assert country_only[0]["country"] == "Iran"

        global_only = fetch_market_data(scope_level="global", db_path=path)
        assert len(global_only) == 1
        assert global_only[0]["scope_level"] == "global"
    finally:
        os.remove(path)
