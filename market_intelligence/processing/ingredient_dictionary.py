"""Static reference data for common aesthetic-medicine ingredients.

Not a substitute for CosIng or a pharmacopoeia lookup — a small curated
table so an ingredient-type query returns identity data (INCI name, CAS
number, class) even when no connector has a record for it yet.
"""

INGREDIENTS = {
    "hyaluronic acid": {
        "preferred_name": "Hyaluronic acid",
        "inci_name": "Sodium Hyaluronate",
        "cas_number": "9067-32-7",
        "ingredient_class": "glycosaminoglycan",
        "function": "tissue volumizer, humectant",
        "notes": "Cross-linked forms used in dermal fillers; uncross-linked forms used in skin boosters.",
    },
    "pdrn": {
        "preferred_name": "Polydeoxyribonucleotide (PDRN)",
        "inci_name": "Sodium DNA",
        "cas_number": "9007-49-2",
        "ingredient_class": "nucleotide polymer",
        "function": "tissue regeneration, wound healing",
        "notes": "Derived from salmon or trout sperm DNA; distinct from polynucleotide (PN) by fragment length.",
    },
    "polynucleotide": {
        "preferred_name": "Polynucleotides (PN)",
        "inci_name": "Sodium DNA",
        "cas_number": "9007-49-2",
        "ingredient_class": "nucleotide polymer",
        "function": "tissue regeneration, skin quality",
        "notes": "Longer-chain relative of PDRN; naming is not standardized across manufacturers.",
    },
    "niacinamide": {
        "preferred_name": "Niacinamide",
        "inci_name": "Niacinamide",
        "cas_number": "98-92-0",
        "ingredient_class": "vitamin B3 derivative",
        "function": "barrier support, brightening",
        "notes": "Common in topical cosmeceuticals and mesotherapy blends.",
    },
    "botulinum toxin": {
        "preferred_name": "Botulinum toxin type A",
        "inci_name": None,
        "cas_number": "93384-43-1",
        "ingredient_class": "neurotoxin protein",
        "function": "neuromuscular blockade",
        "notes": "Prescription-only biologic; regulated as a drug/biologic, not a device.",
    },
    "calcium hydroxylapatite": {
        "preferred_name": "Calcium hydroxylapatite (CaHA)",
        "inci_name": "Calcium Hydroxyapatite",
        "cas_number": "1306-06-5",
        "ingredient_class": "mineral-based filler",
        "function": "volumizer, biostimulator",
        "notes": "Suspended in a carboxymethylcellulose gel carrier.",
    },
    "poly-l-lactic acid": {
        "preferred_name": "Poly-L-lactic acid (PLLA)",
        "inci_name": "Polylactic Acid",
        "cas_number": "26100-51-6",
        "ingredient_class": "biostimulatory polymer",
        "function": "collagen stimulation",
        "notes": "Reconstituted microparticle suspension; effect is delayed and cumulative.",
    },
    "exosome": {
        "preferred_name": "Exosomes",
        "inci_name": None,
        "cas_number": None,
        "ingredient_class": "extracellular vesicle",
        "function": "cell signaling, tissue repair",
        "notes": "Regulatory status varies sharply by country and source (plant vs. stem-cell derived).",
    },
}


def lookup_ingredient(term: str) -> dict | None:
    return INGREDIENTS.get(term.lower().strip())


def search_ingredients(term: str) -> list[dict]:
    q = term.lower().strip()
    return [
        {"key": key, **data}
        for key, data in INGREDIENTS.items()
        if q in key or q in (data.get("preferred_name") or "").lower()
    ]
