"""Cost-per-unit, margin, and break-even calculations for a cost_models
row. Pure functions over plain numbers — the database layer stores the
inputs and the result, this just does the arithmetic so it's not
duplicated (or silently inconsistent) between the UI and any report.
"""

COST_FIELDS = [
    "material_cost", "packaging_cost", "manufacturing_cost",
    "analytical_cost", "regulatory_cost", "distribution_cost",
]


def estimated_cogs(costs: dict) -> float:
    return round(sum(costs.get(field) or 0 for field in COST_FIELDS), 2)


def gross_margin(target_price: float, cogs: float) -> float | None:
    """Returns gross margin as a fraction of price (0-1), or None if the
    price is zero/unset — margin is undefined, not zero, in that case."""
    if not target_price:
        return None
    return round((target_price - cogs) / target_price, 4)


def break_even_volume(fixed_investment: float, target_price: float, cogs: float) -> float | None:
    """Units needed to recover a fixed investment at the given price and
    per-unit cost. None if price <= cogs, since it's never recovered."""
    contribution = target_price - cogs
    if not fixed_investment or contribution <= 0:
        return None
    return round(fixed_investment / contribution, 0)


def sensitivity(target_price: float, cogs: float, cost_shift_pct: float) -> dict:
    """How margin moves if COGS shifts by cost_shift_pct (e.g. 0.10 for a
    10% raw-material price increase). A quick answer to "how exposed are
    we to a supplier price hike," not a full Monte Carlo sensitivity."""
    shifted_cogs = cogs * (1 + cost_shift_pct)
    return {
        "base_margin": gross_margin(target_price, cogs),
        "shifted_cogs": round(shifted_cogs, 2),
        "shifted_margin": gross_margin(target_price, shifted_cogs),
    }
