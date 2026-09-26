"""Cross-jurisdiction regulatory comparison for a promoted product.

Groups a product's regulatory_records by jurisdiction and, against an
optional list of target jurisdictions, flags which ones have no record
at all — an explicit gap, not a silent omission. This only reports what
the registry actually has; it never infers or estimates a status for a
jurisdiction with no record.
"""

# A jurisdiction is treated as "approved" if its most relevant record's
# status contains one of these words — matches the platform's existing
# REGULATORY_STATUS_VALUES vocabulary (approved/cleared/registered/
# listed/notified all count as some form of market authorization).
_POSITIVE_STATUS_MARKERS = ("approved", "cleared", "registered", "listed", "notified")


def _is_positive_status(status: str | None) -> bool:
    if not status:
        return False
    lowered = status.lower()
    return any(marker in lowered for marker in _POSITIVE_STATUS_MARKERS)


def build_regulatory_comparison(
    regulatory_records: list[dict], target_jurisdictions: list[str] | None = None,
) -> dict:
    by_jurisdiction: dict[str, list[dict]] = {}
    for record in regulatory_records:
        jurisdiction = record.get("jurisdiction") or "unknown"
        by_jurisdiction.setdefault(jurisdiction, []).append(record)

    status_summary = {}
    for jurisdiction, records in by_jurisdiction.items():
        positive = [r for r in records if _is_positive_status(r.get("status"))]
        if positive:
            status_summary[jurisdiction] = "approved"
        else:
            # Most recent record's own status, whatever it says — never
            # invented, just the last word the registry actually has.
            status_summary[jurisdiction] = (records[-1].get("status") or "unknown")

    result = {
        "jurisdictions_covered": sorted(by_jurisdiction.keys()),
        "by_jurisdiction": by_jurisdiction,
        "status_summary": status_summary,
    }

    if target_jurisdictions:
        covered = set(by_jurisdiction.keys())
        result["gaps"] = [j for j in target_jurisdictions if j not in covered]
        result["target_jurisdictions"] = target_jurisdictions

    return result
