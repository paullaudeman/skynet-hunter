"""The cost meter is the model-tier-as-architecture thesis made arithmetic ~
these lock in the pricing, the tier spread, and the sim/live honesty flag.
"""

from skynet import cost
from skynet.cost import CostMeter, cost_for, estimate


def test_pricing_table_covers_every_unit_model():
    """A missing tier here would silently fall back to top-tier pricing."""
    for model in ("claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5"):
        assert model in cost.PRICING


def test_cost_for_uses_input_and_output_rates():
    # 1M input + 1M output on Opus = $5 + $25.
    assert cost_for("claude-opus-4-8", 1_000_000, 1_000_000) == 30.0
    # Haiku is 5x cheaper on both axes.
    assert cost_for("claude-haiku-4-5", 1_000_000, 1_000_000) == 6.0


def test_unknown_model_never_under_reports():
    """An unrecognised model assumes the top tier, never zero."""
    assert cost_for("mystery-model", 1_000_000, 0) == cost_for("claude-opus-4-8", 1_000_000, 0)


def test_meter_accumulates_per_model_and_ranks_by_cost():
    m = CostMeter()
    m.record("claude-haiku-4-5", estimate(900, 450))
    m.record("claude-opus-4-8", estimate(1500, 2400))
    m.record("claude-opus-4-8", estimate(1800, 900))

    rows = m.rows()
    assert rows[0].model == "claude-opus-4-8", "Opus should rank first ~ it's the dear tier"
    assert rows[0].calls == 2
    assert m.total_cost > 0


def test_the_tier_spread_is_real():
    """The whole lesson: the same token shape costs 5x more on Opus than Haiku."""
    opus = cost_for("claude-opus-4-8", 1000, 1000)
    haiku = cost_for("claude-haiku-4-5", 1000, 1000)
    assert opus == haiku * 5


def test_estimated_flag_tracks_sim_vs_live():
    m = CostMeter()
    m.record("claude-opus-4-8", estimate(100, 100))  # live-shaped, no flag
    assert m.estimated is False
    m.record("claude-opus-4-8", estimate(100, 100), estimated=True)
    assert m.estimated is True


def test_none_usage_bills_nothing():
    """A failed call (no usage object) must not crash or invent cost."""
    m = CostMeter()
    assert m.record("claude-opus-4-8", None) == 0.0
    assert m.total_cost == 0.0
