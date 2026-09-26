"""Risk Priority Number scoring (severity x occurrence x detectability)
and the stop-criteria check that overrides any opportunity score.

A high opportunity score never excuses an unacceptable risk — that's
why stop criteria are checked separately and can veto a "go" regardless
of how attractive the market looks.
"""

SCALE_MIN, SCALE_MAX = 1, 5

# A short list of automatic-stop conditions, matched by keyword against a
# free-text risk_event/effect field. Deliberately conservative: a false
# negative here just means a human still reviews it, a false positive
# blocks something that might have been fine — the safer direction.
STOP_CRITERIA_KEYWORDS = [
    "unresolved serious safety",
    "unacceptable regulatory classification",
    "no reliable source",
    "no reliable supplier",
    "unmanageable patent",
    "unacceptable sterility",
    "unacceptable endotoxin",
    "no viable margin",
    "no defensible differentiation",
]


def risk_priority_number(severity: int, occurrence: int, detectability: int) -> int:
    for name, value in (("severity", severity), ("occurrence", occurrence), ("detectability", detectability)):
        if not SCALE_MIN <= value <= SCALE_MAX:
            raise ValueError(f"'{name}' must be between {SCALE_MIN} and {SCALE_MAX}, got {value}")
    return severity * occurrence * detectability


def risk_acceptability(rpn: int) -> str:
    """Maps an RPN (1-125) to a plain acceptability band. Bands are a
    starting point, not a regulatory standard — tune thresholds per
    product class if you have one."""
    if rpn <= 8:
        return "acceptable"
    if rpn <= 27:
        return "acceptable_with_controls"
    if rpn <= 64:
        return "requires_mitigation"
    return "unacceptable"


def check_stop_criteria(risk_events: list[str]) -> list[str]:
    """Scans a list of free-text risk_event/effect strings for stop-criteria
    language. Returns the matched trigger phrases; empty means none found."""
    triggered = []
    for text in risk_events:
        lowered = (text or "").lower()
        for keyword in STOP_CRITERIA_KEYWORDS:
            if keyword in lowered:
                triggered.append(keyword)
    return sorted(set(triggered))
