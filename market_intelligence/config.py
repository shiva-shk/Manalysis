"""Central configuration: source registry and app-wide constants."""

SOURCES = {
    "clinicaltrials": {
        "name": "ClinicalTrials.gov",
        "source_type": "official",
        "api_available": True,
        "supports": ["product", "ingredient", "company"],
        "evidence_weight": 0.95,
    },
    "openfda_device": {
        "name": "openFDA (510k devices)",
        "source_type": "official",
        "api_available": True,
        "supports": ["device", "company"],
        "evidence_weight": 0.95,
    },
    "openfda_drug": {
        "name": "openFDA (drug labels)",
        "source_type": "official",
        "api_available": True,
        "supports": ["drug", "company"],
        "evidence_weight": 0.95,
    },
    "pubmed": {
        "name": "PubMed / Europe PMC",
        "source_type": "scientific",
        "api_available": True,
        "supports": ["product", "ingredient", "company"],
        "evidence_weight": 0.90,
    },
    "openfda_pma": {
        "name": "openFDA (PMA devices)",
        "source_type": "official",
        "api_available": True,
        "supports": ["device", "company"],
        "evidence_weight": 0.95,
    },
    "openfda_udi": {
        "name": "openFDA (UDI/GUDID)",
        "source_type": "official",
        "api_available": True,
        "supports": ["device", "company"],
        "evidence_weight": 0.90,
    },
    "dailymed": {
        "name": "DailyMed",
        "source_type": "official",
        "api_available": True,
        "supports": ["drug", "company"],
        "evidence_weight": 0.90,
    },
    "ema": {
        "name": "EMA (European Medicines Agency)",
        "source_type": "official",
        "api_available": True,
        "supports": ["drug", "company"],
        "evidence_weight": 0.90,
    },
    "pubchem": {
        "name": "PubChem (chemical identity)",
        "source_type": "official",
        "api_available": True,
        "supports": ["ingredient"],
        "evidence_weight": 0.85,
    },
    "patents": {
        "name": "EPO Open Patent Services",
        "source_type": "official",
        "api_available": "requires_credentials",
        "supports": ["product", "ingredient", "company"],
        "evidence_weight": 0.90,
    },
    "eudamed": {
        "name": "EUDAMED (EU medical devices)",
        "source_type": "official",
        "api_available": "undocumented",
        "supports": ["device", "company"],
        "evidence_weight": 0.85,
    },
    "health_canada": {
        "name": "Health Canada MDALL",
        "source_type": "official",
        "api_available": "undocumented",
        "supports": ["device", "company"],
        "evidence_weight": 0.85,
    },
}

# Confidence bands used across the app when displaying evidence scores.
CONFIDENCE_BANDS = [
    (0.80, 1.01, "High"),
    (0.60, 0.80, "Moderate"),
    (0.0, 0.60, "Low"),
]

DEFAULT_TIMEOUT = 30
DEFAULT_PAGE_SIZE = 20

DB_PATH = "market_intelligence.db"
