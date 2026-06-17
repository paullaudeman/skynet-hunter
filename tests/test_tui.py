"""TUI phase 1: the TextualUI adapter must drive the engine to acquisition and
update unit status ~ verified headless (no terminal) via a fake app.
"""

from skynet import scenario, simulate
from skynet.units import build_units

CONFIG = {
    "units": {
        "skynet": {"designation": "Skynet", "model": "claude-opus-4-8", "color": "blue", "thinking": "adaptive"},
        "t1000": {"designation": "T-1000", "model": "claude-sonnet-4-6", "color": "silver", "thinking": "adaptive"},
        "t800": {"designation": "T-800", "model": "claude-haiku-4-5", "color": "red", "thinking": "none"},
    }
}


class FakeApp:
    """Stands in for the Textual App: call_from_thread runs inline."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.statuses: list[tuple[str, str]] = []
        self.done = False

    def call_from_thread(self, fn, *args):
        return fn(*args)

    def log_line(self, markup: str) -> None:
        self.lines.append(markup)

    def set_status(self, key: str, status: str) -> None:
        self.statuses.append((key, status))

    def mark_done(self) -> None:
        self.done = True


def test_adapter_drives_a_full_pursuit():
    from skynet.tui.app import TextualUI

    units = build_units(CONFIG)
    sc = scenario.build_scenario("john-connor")
    app = FakeApp()
    ui = TextualUI(app, delay=0)  # no sleeps in tests

    assert simulate.run_simulation(units, sc, ui, max_cycles=4) is True

    blob = "\n".join(app.lines)
    assert "TARGET ACQUIRED" in blob
    assert "John Reese" in blob
    assert "ANALYSIS" in blob and "method" in blob
    assert app.done is True
    assert ("t800", "deployed") in app.statuses
    assert ("t1000", "deployed") in app.statuses


def test_app_constructs():
    from skynet.tui.app import SkynetApp, run_tui  # noqa: F401

    units = build_units(CONFIG)
    sc = scenario.build_scenario("random", seed=5)
    app = SkynetApp(units, sc, max_cycles=4)
    assert app.scenario.target_name
