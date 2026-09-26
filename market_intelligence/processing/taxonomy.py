"""Controlled vocabularies shared across the product/company/ingredient
registry, so free-text values don't drift into a dozen spellings of the
same thing. Pulled from the architecture spec's taxonomy and confidence
sections; trimmed to what the current build actually uses.
"""

PRODUCT_TYPES = [
    "dermal_filler", "skin_booster", "mesotherapy_injectable",
    "pdrn_product", "polynucleotide_product", "exosome_or_ev_product",
    "botulinum_toxin", "caha_biostimulator", "plla_biostimulator",
    "pcl_biostimulator", "collagen_product", "fat_dissolving_injection",
    "hair_injectable", "topical_cosmeceutical", "energy_based_device",
    "microneedling_device", "combination_product",
]

REGULATORY_CATEGORIES = [
    "cosmetic", "medical_device", "medicinal_product", "biologic",
    "combination_product", "quasi_drug", "professional_use_product",
    "investigational_product", "human_tissue_material", "unknown",
]

ROUTES = [
    "topical", "intradermal", "subcutaneous", "intramuscular",
    "microneedling", "oral", "ophthalmic", "implantable", "unknown",
]

INGREDIENT_ROLES = [
    "active_substance", "excipient", "carrier", "crosslinker",
    "anesthetic", "buffer", "preservative", "stabilizer", "antioxidant",
    "isotonic_agent", "viscosity_modifier", "process_aid",
    "residual_reagent", "contaminant", "unknown",
]

CONCENTRATION_TYPES = ["exact", "nominal", "range", "minimum", "maximum", "estimated", "not_disclosed"]

COMPANY_ROLES = [
    "brand_owner", "legal_manufacturer", "contract_manufacturer",
    "applicant", "oem", "cdmo", "technology_owner", "licensee",
    "authorized_representative", "importer", "distributor", "local_sponsor",
]

ALIAS_TYPES = [
    "brand_name", "product_name", "product_family", "regulatory_name",
    "generic_name", "model_name", "former_name", "translated_name",
    "internal_code", "distributor_name",
]

REGULATORY_STATUS_VALUES = [
    "approved", "cleared", "registered", "listed", "notified",
    "under_review", "withdrawn", "recalled", "not_found", "conflicting_sources",
]

VERIFICATION_STATUSES = [
    "machine_extracted", "awaiting_review", "analyst_verified",
    "quality_reviewed", "approved_for_strategy", "rejected", "superseded",
]

MISSING_DATA_VALUES = [
    "not_disclosed", "not_found", "not_applicable",
    "conflicting_sources", "requires_document_review", "not_verified",
]

CQA_CATEGORIES = [
    "identity", "purity", "strength", "molecular_weight", "particle_size",
    "viscosity", "rheology", "ph", "osmolality", "sterility", "endotoxin",
    "potency", "degradation", "syringeability", "injectability",
    "container_compatibility", "appearance",
]

RISK_CATEGORIES = [
    "identity", "quality", "sterility", "endotoxin", "immunogenicity",
    "toxicity", "clinical", "regulatory", "manufacturing", "supply_chain",
    "patent", "commercial", "pharmacovigilance", "reputation",
]

RISK_ACCEPTABILITY = ["acceptable", "acceptable_with_controls", "requires_mitigation", "unacceptable"]

STAGE_GATE_STAGES = [
    "gate_0_opportunity_discovery", "gate_1_feasibility", "gate_2_candidate_selection",
    "gate_3_prototype_development", "gate_4_verification_validation", "gate_5_commercialization",
]

STAGE_GATE_DECISIONS = ["go", "conditional_go", "hold", "rework", "stop"]

RECOMMENDED_ACTIONS = [
    "develop_internally", "license", "private_label", "co_develop",
    "acquire", "monitor", "do_not_pursue",
]

MARKET_SCOPE_LEVELS = ["global", "regional", "country"]

DATA_QUALITY_FLAGS = [
    "source_conflict", "outdated", "incomplete", "estimated",
    "machine_extracted", "analyst_verified", "regulator_confirmed",
    "supplier_claimed", "not_independently_verified",
]

# Source-type reliability weights, used as the starting point for
# field_evidence.confidence before completeness/recency adjustments.
SOURCE_RELIABILITY = {
    "official_regulatory_record": 0.95,
    "batch_lab_report": 0.95,
    "patent_office_record": 0.90,
    "peer_reviewed_study": 0.90,
    "official_company_document": 0.85,
    "supplier_coa": 0.85,
    "commercial_market_report": 0.75,
    "distributor_document": 0.65,
    "clinic_website": 0.50,
    "ecommerce_listing": 0.40,
    "social_media_claim": 0.20,
}


def validate_against(value: str, allowed: list[str], field_name: str) -> list[str]:
    """Returns an error list (empty if valid) for a controlled-vocabulary field."""
    if value is None:
        return []
    if value not in allowed:
        return [f"'{field_name}' value '{value}' is not in the controlled vocabulary"]
    return []
