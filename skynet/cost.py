"""The cost meter ~ the model-tier-as-architecture thesis, made arithmetic.

The whole demo argues one thing: match the model tier to the job, don't burn
Opus on a literal sweep. This module puts that argument on screen in dollars.
The T-800 (Haiku) flails cheap; the T-1000 (Sonnet) cross-references for real
money; Skynet (Opus) reasons at 5x the T-800's rate. Watching the spread climb
IS the lesson.

One pricing table is the single source of truth. Two feeders cost out through
it: the live orchestrator records the real `usage` object off each Claude
response; the simulator records representative counts flagged `estimated` (the
offline demo has no real usage ~ an honest ballpark beats a dark meter, since
`--simulate` is the only path a viewer without a key ever runs).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

# USD per million tokens, (input, output). Verified against the published
# Anthropic pricing for these exact model ids. Swap a tier here and the meter
# re-costs the entire hunt ~ that swap is the architecture decision the demo is
# about.
PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.0, 25.0),    # Skynet  ~ reasons hard and rarely
    "claude-sonnet-4-6": (3.0, 15.0),  # T-1000  ~ adaptive infiltrator
    "claude-haiku-4-5": (1.0, 5.0),    # T-800   ~ blunt literal sweep
}

# Prompt-cache economics: a read is ~0.1x the input rate, a write ~1.25x.
# Unused here (no cache_control on the calls), but counted for honesty so the
# figures stay true if caching is ever added.
CACHE_READ_MULT = 0.10
CACHE_WRITE_MULT = 1.25

# Unknown model ~ assume the top tier so the meter never *under*-reports cost.
_FALLBACK = (5.0, 25.0)


def cost_for(model: str, input_tokens: int, output_tokens: int, cache_read: int = 0, cache_write: int = 0) -> float:
    """Dollars for one call's token usage on `model`."""
    in_rate, out_rate = PRICING.get(model, _FALLBACK)
    return (
        input_tokens * in_rate
        + output_tokens * out_rate
        + cache_read * in_rate * CACHE_READ_MULT
        + cache_write * in_rate * CACHE_WRITE_MULT
    ) / 1_000_000


def estimate(input_tokens: int, output_tokens: int, cache_read: int = 0, cache_write: int = 0) -> SimpleNamespace:
    """A usage-shaped stand-in for the offline path (no real API call to read)."""
    return SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read,
        cache_creation_input_tokens=cache_write,
    )


@dataclass
class Row:
    """Running totals for one model tier."""

    model: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0
    cost: float = 0.0


class CostMeter:
    """Accumulates token spend per model and costs it out.

    `record` is duck-typed on the usage object: it reads the same attribute
    names the Anthropic `usage` exposes, so a real response and the simulator's
    `estimate()` stand-in both work unchanged.
    """

    def __init__(self) -> None:
        self._rows: dict[str, Row] = {}
        self.estimated = False  # True once any recorded usage was a sim estimate

    def record(self, model: str, usage: Any, *, estimated: bool = False) -> float:
        """Fold one call's usage into the totals; return that call's cost."""
        if usage is None:  # a failed call has nothing to bill
            return 0.0
        it = int(getattr(usage, "input_tokens", 0) or 0)
        ot = int(getattr(usage, "output_tokens", 0) or 0)
        cr = int(getattr(usage, "cache_read_input_tokens", 0) or 0)
        cw = int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
        cost = cost_for(model, it, ot, cr, cw)

        row = self._rows.setdefault(model, Row(model))
        row.calls += 1
        row.input_tokens += it
        row.output_tokens += ot
        row.cache_read += cr
        row.cache_write += cw
        row.cost += cost

        if estimated:
            self.estimated = True
        return cost

    def rows(self) -> list[Row]:
        """Per-model totals, most expensive first ~ the tier spread, ranked."""
        return sorted(self._rows.values(), key=lambda r: r.cost, reverse=True)

    @property
    def total_cost(self) -> float:
        return sum(r.cost for r in self._rows.values())

    @property
    def total_tokens(self) -> int:
        return sum(
            r.input_tokens + r.output_tokens + r.cache_read + r.cache_write
            for r in self._rows.values()
        )
