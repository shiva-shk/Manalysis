"""Normalizes a free-text query into a canonical ASCII form for matching
and comparison — strips trademark symbols and diacritics so "Juvéderm®"
and "juvederm" compare equal, without changing what gets displayed to
the user (this is for matching/lookup, not presentation).
"""

import re
import unicodedata


def normalize_query(query: str) -> str:
    # Strip trademark/copyright symbols before NFKD decomposition — under
    # NFKD, U+2122 (™) decomposes into the literal letters "TM", which
    # would otherwise survive as word noise ("restylanetm") instead of
    # disappearing.
    text = re.sub(r"[®™©]", "", query)

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()
