"""The arena's whole point: the Resistance's disruption must CHANGE the outcome.
These lock in that the scrub really severs the hunt ~ the cross-reference in
cycle 2 returns nothing, and Skynet ends the run without the target.
"""

import json

from skynet import arena, scenario
from skynet.units import build_units

CONFIG = {"units": {
    "skynet": {"designation": "Skynet", "model": "claude-opus-4-8", "color": "blue", "thinking": "adaptive"},
    "t1000": {"designation": "T-1000", "model": "claude-sonnet-4-6", "color": "silver", "thinking": "adaptive"},
    "t800": {"designation": "T-800", "model": "claude-haiku-4-5", "color": "red", "thinking": "none"},
    "resistance": {"designation": "Protector", "model": "claude-haiku-4-5", "color": "green", "thinking": "none"},
}}


class Rec:
    """Records every UI call ~ accepts the full UI surface via __getattr__."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def __getattr__(self, name):
        def f(*args, **kwargs):
            self.calls.append((name, args))
            return None
        return f


def run() -> Rec:
    units = build_units(CONFIG)
    sc = scenario.build_scenario("john-connor")
    ui = Rec()
    result = arena.run_arena_simulation(units, sc, ui, max_cycles=4)
    assert result is False, "Skynet must NOT acquire ~ the target is safeguarded"
    return ui


def test_protector_scrubs_the_flag():
    ui = run()
    scrubs = [a for (n, a) in ui.calls if n == "tool_result" and len(a) >= 2 and a[1] == "scrub_flag"]
    assert scrubs, "the Resistance must play scrub_flag"


def test_the_scrub_really_severs_the_cross_reference():
    """After the scrub, the T-1000's cross_reference returns NOTHING ~ the real
    consequence of mutating the grid, not a scripted line."""
    ui = run()
    xrefs = [a for (n, a) in ui.calls if n == "tool_result" and len(a) >= 3 and a[1] == "cross_reference"]
    assert xrefs, "a cross_reference must have been played"
    assert json.loads(xrefs[-1][2]) == [], "the severed link must yield zero records"


def test_outcome_is_safeguarded():
    ui = run()
    assert any(n == "arena_result" and a and a[0] == "safeguarded" for (n, a) in ui.calls)
