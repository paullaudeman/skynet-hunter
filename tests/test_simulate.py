"""The offline path must always complete and acquire the target ~ it's the
friend-demo, so it cannot flake.
"""

from skynet import scenario, simulate
from skynet.theme import Theme
from skynet.ui import UI
from skynet.units import build_units

CONFIG = {
    "units": {
        "skynet": {"designation": "Skynet", "model": "claude-opus-4-8", "color": "blue", "thinking": "adaptive"},
        "t1000": {"designation": "T-1000", "model": "claude-sonnet-4-6", "color": "silver", "thinking": "adaptive"},
        "t800": {"designation": "T-800", "model": "claude-haiku-4-5", "color": "red", "thinking": "none"},
    }
}


def test_simulation_acquires_target(capsys):
    units = build_units(CONFIG)
    sc = scenario.build_scenario("john-connor")
    ui = UI(Theme("platinum"), art=False)  # art off => no sleeps

    acquired = simulate.run_simulation(units, sc, ui, max_cycles=4)

    assert acquired is True
    out = capsys.readouterr().out
    assert "TARGET ACQUIRED" in out
    assert "John Reese" in out          # the alias the target was hiding under
    assert "T-800" in out and "T-1000" in out
    assert "ANALYSIS" in out            # the explanatory reasoning is surfaced


def test_simulation_works_for_a_random_scenario(capsys):
    units = build_units(CONFIG)
    sc = scenario.build_scenario("random", seed=11)
    ui = UI(Theme("amber"), art=False)

    assert simulate.run_simulation(units, sc, ui, max_cycles=4) is True
    out = capsys.readouterr().out
    assert "TARGET ACQUIRED" in out
    assert sc.alias in out
