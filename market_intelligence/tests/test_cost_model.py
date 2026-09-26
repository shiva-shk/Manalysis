from analysis.cost_model import break_even_volume, estimated_cogs, gross_margin, sensitivity


COSTS = {
    "material_cost": 10, "packaging_cost": 2, "manufacturing_cost": 5,
    "analytical_cost": 1, "regulatory_cost": 1, "distribution_cost": 1,
}


def test_estimated_cogs_sums_all_cost_fields():
    assert estimated_cogs(COSTS) == 20.0


def test_estimated_cogs_treats_missing_field_as_zero():
    assert estimated_cogs({"material_cost": 10}) == 10.0


def test_gross_margin_as_fraction_of_price():
    assert gross_margin(target_price=40, cogs=20) == 0.5


def test_gross_margin_none_when_price_is_zero():
    assert gross_margin(target_price=0, cogs=20) is None


def test_break_even_volume():
    assert break_even_volume(fixed_investment=1000, target_price=40, cogs=20) == 50.0


def test_break_even_volume_none_when_price_below_cogs():
    assert break_even_volume(fixed_investment=1000, target_price=15, cogs=20) is None


def test_sensitivity_shows_margin_compression():
    result = sensitivity(target_price=40, cogs=20, cost_shift_pct=0.10)
    assert result["base_margin"] == 0.5
    assert result["shifted_cogs"] == 22.0
    assert result["shifted_margin"] < result["base_margin"]
