import os
import tempfile

import pytest

from processing.ingredient_seed_data import SEED_INGREDIENTS, seed_ingredients


def test_every_seed_entry_has_a_source_url():
    assert all(entry.get("source_url") for entry in SEED_INGREDIENTS)


def test_every_seed_entry_has_a_preferred_name():
    names = [entry["preferred_name"] for entry in SEED_INGREDIENTS]
    assert len(names) == len(set(names)), "duplicate preferred_name in seed data"


def test_exosome_entries_correctly_have_no_cas_number():
    ev_entries = [e for e in SEED_INGREDIENTS if "Extracellular Vesicles" in e["preferred_name"]]
    assert ev_entries
    assert all(e["cas_number"] is None for e in ev_entries)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.remove(path)


def test_seed_ingredients_populates_registry(db_path):
    from database.registry_db import fetch_ingredients

    ids = seed_ingredients(db_path=db_path)
    assert len(ids) == len(SEED_INGREDIENTS)

    stored = fetch_ingredients(db_path=db_path)
    assert len(stored) == len(SEED_INGREDIENTS)
