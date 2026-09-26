"""Licensing-potential assessment for a promoted product.

Deliberately not a single score: patent/freedom-to-operate risk is too
consequential and too uncertain to compress into one number the way
opportunity_score.py does for market attractiveness. Instead this
returns structured findings — patent status, regulatory breadth,
clinical evidence, safety signals — plus plain-language considerations
an analyst reads and weighs themselves. An absence of patents in the
registry is reported as exactly that (no patent record found), never as
"freedom to operate confirmed": this platform's own patent connector
coverage is partial, so absence of evidence isn't evidence of absence.
"""

# Legal-status values (as returned by the EPO connector / entered
# manually) that mean the patent still blocks/protects, as opposed to
# expired, lapsed, or withdrawn ones.
_ACTIVE_LEGAL_STATUSES = {"active", "granted", "in force", "pending"}


def _patent_status(patents: list[dict]) -> dict:
    if not patents:
        return {
            "state": "no_patents_found",
            "active_count": 0,
            "total_count": 0,
        }

    active = [
        p for p in patents
        if (p.get("legal_status") or "").strip().lower() in _ACTIVE_LEGAL_STATUSES
    ]
    return {
        "state": "active_patents_present" if active else "patents_found_none_active",
        "active_count": len(active),
        "total_count": len(patents),
    }


def _regulatory_breadth(regulatory_records: list[dict]) -> dict:
    jurisdictions = {r.get("jurisdiction") for r in regulatory_records if r.get("jurisdiction")}
    return {
        "jurisdiction_count": len(jurisdictions),
        "jurisdictions": sorted(jurisdictions),
    }


def _clinical_evidence(clinical_studies: list[dict]) -> dict:
    return {
        "study_count": len(clinical_studies),
        "evidence_levels": sorted({s["evidence_level"] for s in clinical_studies if s.get("evidence_level")}),
    }


def _safety_profile(safety_signals: list[dict]) -> dict:
    return {
        "signal_count": len(safety_signals),
        "signal_types": sorted({s["signal_type"] for s in safety_signals if s.get("signal_type")}),
    }


def build_licensing_analysis(
    patents: list[dict], regulatory_records: list[dict],
    clinical_studies: list[dict], safety_signals: list[dict],
) -> dict:
    patent_status = _patent_status(patents)
    regulatory_breadth = _regulatory_breadth(regulatory_records)
    clinical_evidence = _clinical_evidence(clinical_studies)
    safety_profile = _safety_profile(safety_signals)

    considerations = []

    if patent_status["state"] == "active_patents_present":
        considerations.append(
            f"{patent_status['active_count']} active patent(s) found — licensing-in requires "
            "either a license from the holder or a freedom-to-operate clearance; licensing-out "
            "is a real option if this platform's registry holds the rights holder's own patents."
        )
    elif patent_status["state"] == "patents_found_none_active":
        considerations.append(
            f"{patent_status['total_count']} patent record(s) found, none showing an active "
            "legal status — worth verifying directly with the patent office before assuming "
            "the field is clear, since legal-status data can lag actual status."
        )
    else:
        considerations.append(
            "No patent record found in the registry. This reflects patent connector coverage "
            "(EPO only, and only for clusters that were promoted with a patent-type member) — "
            "it is not a freedom-to-operate clearance. A proper FTO search covers jurisdictions "
            "and applicants this platform doesn't."
        )

    if regulatory_breadth["jurisdiction_count"] >= 3:
        considerations.append(
            f"Regulatory record in {regulatory_breadth['jurisdiction_count']} jurisdiction(s) "
            f"({', '.join(regulatory_breadth['jurisdictions'])}) — broader approval generally "
            "means lower incremental regulatory cost for a licensing partner already active there."
        )
    elif regulatory_breadth["jurisdiction_count"] > 0:
        considerations.append(
            f"Regulatory record limited to {regulatory_breadth['jurisdiction_count']} "
            f"jurisdiction(s) ({', '.join(regulatory_breadth['jurisdictions'])}) — a licensing "
            "partner targeting other markets would carry that regulatory cost themselves."
        )
    else:
        considerations.append("No regulatory record found in any jurisdiction in this registry.")

    if clinical_evidence["study_count"] > 0:
        considerations.append(
            f"{clinical_evidence['study_count']} clinical study record(s) found — clinical "
            "evidence strengthens a licensing case, though evidence_level here reflects "
            "registration status, not effect size or trial quality."
        )
    else:
        considerations.append("No clinical study record found for this product.")

    if safety_profile["signal_count"] > 0:
        considerations.append(
            f"{safety_profile['signal_count']} safety signal(s) on record "
            f"({', '.join(safety_profile['signal_types']) or 'type not specified'}) — review "
            "these directly before any licensing decision; this platform doesn't grade severity."
        )

    return {
        "patent_status": patent_status,
        "regulatory_breadth": regulatory_breadth,
        "clinical_evidence": clinical_evidence,
        "safety_profile": safety_profile,
        "considerations": considerations,
    }
