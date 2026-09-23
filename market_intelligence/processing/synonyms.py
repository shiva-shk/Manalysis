"""Synonym/terminology expansion so a search also catches how other
sources name the same concept (INCI names, abbreviations, trade jargon)."""

SYNONYMS = {
    "pdrn": [
        "polydeoxyribonucleotide",
        "polydesoxyribonucleotide",
    ],
    "polynucleotide": [
        "PN",
        "polynucleotides",
        "DNA polynucleotide",
        "salmon DNA",
    ],
    "dermal filler": [
        "soft tissue filler",
        "hyaluronic acid filler",
        "facial filler",
        "injectable filler",
    ],
    "skin booster": [
        "injectable skin booster",
        "mesotherapy injectable",
        "biorevitalization",
    ],
    "botulinum toxin": [
        "botulinum toxin type A",
        "BoNT-A",
        "neuromodulator",
    ],
}


def expand_query(term: str) -> list[str]:
    """Return the original term plus any known synonyms, original first."""
    key = term.lower().strip()
    expansions = SYNONYMS.get(key, [])
    return [term, *expansions]
