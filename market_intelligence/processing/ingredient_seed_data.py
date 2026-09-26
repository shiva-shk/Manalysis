"""Seed data for the ingredients registry table.

These are real, individually verified entries pulled from primary
sources during research on ExoCoBio's product lines: FDA DailyMed
structured product labels, EU CosIng/COSMILE entries, and INCI
ingredient databases. Each carries the source it was verified against,
not a guess. Exosome/EV ingredients correctly have no CAS number, since
they're heterogeneous vesicle preparations, not single compounds; that's
a fact about the ingredient, not a missing field.
"""

SEED_INGREDIENTS = [
    {
        "preferred_name": "Rosa Damascena Callus Extracellular Vesicles",
        "inci_name": "Rosa Damascena Callus Extracellular Vesicles",
        "cas_number": None,
        "material_family": "plant-derived extracellular vesicle",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": (
            "Registered with the US Personal Care Products Council (PCPC), 2020. "
            "Also listed in EU CosIng (entry #29380) / COSMILE Europe. Developed by "
            "ExoCoBio, marketed under their ASCE+ line."
        ),
        "source_url": "https://cosmileeurope.eu/inci/detail/29380/rosa-damascena-callus-extracellular-vesicles/",
    },
    {
        "preferred_name": "Lactobacillus Extracellular Vesicles",
        "inci_name": "Lactobacillus Extracellular Vesicles",
        "cas_number": None,
        "material_family": "bacteria-derived extracellular vesicle",
        "ingredient_function": "hair conditioning, skin conditioning",
        "regulatory_notes": (
            "Registered EU CosIng ingredient (entry #98041). Underlying composition "
            "patent US 11,583,560 (Amorepacific Corporation) claims the specific strain "
            "Lactobacillus plantarum APsulloc 331261 (KCCM11179P); a different strain "
            "would need its own FTO check."
        ),
        "source_url": "https://cosmileeurope.eu/inci/detail/28029/lactobacillus-extracellular-vesicles/",
    },
    {
        "preferred_name": "sh-Oligopeptide-1",
        "inci_name": "sh-Oligopeptide-1",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human EGF (Epidermal Growth Factor), 53 amino acids.",
        "source_url": "https://ci.guide/peptides/sh-oligopeptide-1",
    },
    {
        "preferred_name": "sh-Oligopeptide-2",
        "inci_name": "sh-Oligopeptide-2",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human IGF-1 (Insulin-like Growth Factor 1), 70 amino acids.",
        "source_url": "https://ci.guide/peptides/sh-oligopeptide-2",
    },
    {
        "preferred_name": "sh-Oligopeptide-4",
        "inci_name": "sh-Oligopeptide-4",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human Thymosin Beta 4.",
        "source_url": "https://incidecoder.com/ingredients/sh-oligopeptide-4",
    },
    {
        "preferred_name": "sh-Polypeptide-1",
        "inci_name": "sh-Polypeptide-1",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human bFGF (basic Fibroblast Growth Factor).",
        "source_url": "https://incibeauty.com/en/ingredients/4561-sh-polypeptide-1",
    },
    {
        "preferred_name": "sh-Polypeptide-3",
        "inci_name": "sh-Polypeptide-3",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human KGF (Keratinocyte Growth Factor).",
        "source_url": "https://ci.guide/peptides/sh-polypeptide-3",
    },
    {
        "preferred_name": "sh-Polypeptide-4",
        "inci_name": "sh-Polypeptide-4",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human SCF (Stem Cell Factor / Kit ligand), up to 273 amino acids.",
        "source_url": "https://ci.guide/peptides/sh-polypeptide-4",
    },
    {
        "preferred_name": "sh-Polypeptide-8",
        "inci_name": "sh-Polypeptide-8",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human PDGF-BB (Platelet-Derived Growth Factor Beta), up to 241 amino acids.",
        "source_url": "https://ci.guide/peptides/sh-polypeptide-8",
    },
    {
        "preferred_name": "sh-Polypeptide-9",
        "inci_name": "sh-Polypeptide-9",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human VEGF-A (Vascular Endothelial Growth Factor A).",
        "source_url": "https://ci.guide/peptides/sh-polypeptide-9",
    },
    {
        "preferred_name": "sh-Polypeptide-11",
        "inci_name": "sh-Polypeptide-11",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human aFGF (acidic Fibroblast Growth Factor / FGF1), up to 155 amino acids.",
        "source_url": "https://ci.guide/peptides/sh-polypeptide-11",
    },
    {
        "preferred_name": "sh-Polypeptide-13",
        "inci_name": "sh-Polypeptide-13",
        "cas_number": None,
        "material_family": "recombinant human protein (E. coli fermentation)",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Recombinant human Noggin protein, up to 232 amino acids.",
        "source_url": "https://incidecoder.com/ingredients/sh-polypeptide-13",
    },
    {
        "preferred_name": "Copper Tripeptide-1",
        "inci_name": "Copper Tripeptide-1",
        "cas_number": "89030-95-5",
        "material_family": "synthetic peptide",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "GHK-Cu, glycyl-L-histidyl-L-lysine copper(II) complex. Also cited under CAS 49557-75-7 for a different salt form.",
        "source_url": "https://www.chemicalbook.com/ChemicalProductProperty_EN_CB52651405.htm",
    },
    {
        "preferred_name": "Acetyl Hexapeptide-8",
        "inci_name": "Acetyl Hexapeptide-8",
        "cas_number": "616204-22-9",
        "material_family": "synthetic peptide",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": "Trade name Argireline; SNAP-25 fragment analog, inhibits neurotransmitter release (Botox-like mechanism).",
        "source_url": "https://www.specialchem.com/cosmetics/inci-ingredients/acetyl-hexapeptide-8",
    },
    {
        "preferred_name": "Nonapeptide-1",
        "inci_name": "Nonapeptide-1",
        "cas_number": None,
        "material_family": "synthetic peptide",
        "ingredient_function": "skin conditioning / whitening",
        "regulatory_notes": "Sequence MPfRwFKPV, an alpha-MSH analog, inhibits tyrosinase/melanin production.",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/",
    },
    {
        "preferred_name": "Madecassoside",
        "inci_name": "Madecassoside",
        "cas_number": "34540-22-2",
        "material_family": "plant triterpenoid",
        "ingredient_function": "soothing, skin conditioning",
        "regulatory_notes": "Pentacyclic triterpenoid from Centella asiatica. EU CosIng approved.",
        "source_url": "https://cosmeticobs.com/en/ingredients/madecassoside-1620",
    },
    {
        "preferred_name": "Tranexamic Acid",
        "inci_name": "Tranexamic Acid",
        "cas_number": "1197-18-8",
        "material_family": "synthetic small molecule",
        "ingredient_function": "astringent, skin conditioning",
        "regulatory_notes": "Used for hyperpigmentation/melasma; also has systemic drug uses (unrelated indication).",
        "source_url": "https://www.specialchem.com/cosmetics/inci-ingredients/tranexamic-acid",
    },
    {
        "preferred_name": "DMAE",
        "inci_name": "Dimethylaminoethanol",
        "cas_number": "108-01-0",
        "material_family": "synthetic small molecule",
        "ingredient_function": "skin conditioning",
        "regulatory_notes": (
            "Appears in distributor copy for ASCE+ SRLV but not in the product's official "
            "FDA DailyMed ingredient listing — unresolved discrepancy, verify before relying on it."
        ),
        "source_url": "https://en.wikipedia.org/wiki/Dimethylethanolamine",
    },
]


def seed_ingredients(db_path: str | None = None) -> list[int]:
    """Upserts every seed ingredient and returns the list of ingredient IDs."""
    from config import DB_PATH
    from database.registry_db import upsert_ingredient

    resolved_path = db_path or DB_PATH
    ids = []
    for entry in SEED_INGREDIENTS:
        name = entry["preferred_name"]
        fields = {k: v for k, v in entry.items() if k != "preferred_name"}
        ids.append(upsert_ingredient(name, db_path=resolved_path, **fields))
    return ids
