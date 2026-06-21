"""Per-agent panes for the TUI ~ the multi-pane HUD.

Each agent (Skynet + each terminator) gets its OWN column: a color-coded header
carrying a live status light, its latest confidence score, and a running cost,
over its own scrolling log. A scoreboard panel tracks the whole hunt against the
0.8 acquisition threshold. Plus a read-only scenario summary.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import RichLog, Static

from .themes import PALETTE, STATUS_GLYPH, UNIT_GLYPH

THRESHOLD = 0.8  # Skynet's acquisition bar (from SKYNET_SYSTEM: confidence >= 0.8)


class AgentColumn(Vertical):
    """One agent's pane: a colored header (status · conf · cost) above its log."""

    def __init__(self, key: str, designation: str, model: str, color: str) -> None:
        super().__init__(id=f"col-{key}", classes="agentcol")
        self.key = key
        self.designation = designation
        self.model = model
        self.color = PALETTE.get(color, PALETTE["silver"])
        self._status = "idle"
        self._cost = 0.0
        self._conf: float | None = None

    def compose(self) -> ComposeResult:
        yield Static(self._header(), id=f"hdr-{self.key}", classes="colhdr")
        yield RichLog(
            id=f"rlog-{self.key}", classes="collog",
            markup=True, wrap=True, highlight=False, auto_scroll=True,
        )

    def _header(self) -> Text:
        glyph = UNIT_GLYPH.get(self.key, "•")
        dot = STATUS_GLYPH.get(self._status, "○")
        dot_color = (
            PALETTE["amber"] if self._status == "thinking"
            else self.color if self._status == "deployed"
            else PALETTE["dim"]
        )
        t = Text()
        t.append(f"{glyph} {self.designation}\n", style=f"bold {self.color}")
        t.append(f"{self.model}\n", style=PALETTE["dim"])
        t.append(f"{dot} {self._status}", style=dot_color)
        if self._conf is not None:
            conf_color = PALETTE["green"] if self._conf >= THRESHOLD else PALETTE["amber"]
            t.append(f"  {self._conf:.0%}", style=f"bold {conf_color}")
        t.append(f"  ${self._cost:.4f}", style=PALETTE["dim"])
        return t

    def _refresh_header(self) -> None:
        self.query_one(f"#hdr-{self.key}", Static).update(self._header())

    def set_status(self, status: str) -> None:
        self._status = status
        self._refresh_header()

    def add_cost(self, delta: float) -> None:
        self._cost += delta
        self._refresh_header()

    def set_conf(self, conf: float) -> None:
        self._conf = conf
        self._refresh_header()

    def write_line(self, markup: str) -> None:
        self.query_one(f"#rlog-{self.key}", RichLog).write(markup)

    def reset(self) -> None:
        self._status = "idle"
        self._cost = 0.0
        self._conf = None
        self._refresh_header()
        self.query_one(f"#rlog-{self.key}", RichLog).clear()


class ScoreboardPanel(Static):
    """Live scoreboard ~ cycle, best confidence vs the acquisition bar, spend."""

    def __init__(self, total_cycles: int, threshold: float = THRESHOLD) -> None:
        super().__init__(id="scoreboard")
        self.total_cycles = total_cycles
        self.threshold = threshold
        self.cycle = 0
        self.best_conf = 0.0
        self.cost = 0.0
        self.state = "standby"

    def _bar(self, width: int = 14) -> str:
        filled = int(round(self.best_conf * width))
        thr = int(round(self.threshold * width))
        out = []
        for i in range(width):
            if i == thr:
                out.append("│")          # the acquisition bar
            elif i < filled:
                out.append("█")
            else:
                out.append("░")
        return "".join(out)

    def render(self) -> Text:
        t = Text()
        t.append("SCOREBOARD\n\n", style=f"bold {PALETTE['amber']}")
        t.append(f"{'cycle':>10} ", style=PALETTE["dim"])
        t.append(f"{self.cycle}/{self.total_cycles}\n", style=PALETTE["fg"])
        conf_color = PALETTE["green"] if self.best_conf >= self.threshold else PALETTE["amber"]
        t.append(f"{'best conf':>10} ", style=PALETTE["dim"])
        t.append(f"{self.best_conf:.0%}\n", style=f"bold {conf_color}")
        t.append(f"{'':>10} ", style=PALETTE["dim"])
        t.append(f"{self._bar()}\n", style=conf_color)
        t.append(f"{'acquire ≥':>10} ", style=PALETTE["dim"])
        t.append(f"{self.threshold:.0%}\n", style=PALETTE["dim"])
        t.append(f"{'spend':>10} ", style=PALETTE["dim"])
        t.append(f"${self.cost:.4f}\n\n", style=PALETTE["fg"])
        state_color = {
            "ACQUIRED": PALETTE["green"], "EXHAUSTED": PALETTE["red"], "HUNTING": PALETTE["amber"],
        }.get(self.state, PALETTE["dim"])
        t.append(f"  {self.state}\n", style=f"bold {state_color}")
        return t

    def set_cycle(self, n: int) -> None:
        self.cycle = n
        self.refresh()

    def report_conf(self, conf: float) -> None:
        self.best_conf = max(self.best_conf, conf)
        self.refresh()

    def set_cost(self, cost: float) -> None:
        self.cost = cost
        self.refresh()

    def set_state(self, state: str) -> None:
        self.state = state
        self.refresh()

    def reset(self) -> None:
        self.cycle = 0
        self.best_conf = 0.0
        self.cost = 0.0
        self.state = "HUNTING"
        self.refresh()


class ScenarioPanel(Static):
    """Read-only summary of the active scenario."""

    def __init__(self, scenario: Any) -> None:
        super().__init__(id="scenario")
        self.scenario = scenario

    def render(self) -> Text:
        s = self.scenario
        t = Text()
        t.append("SCENARIO\n\n", style=f"bold {PALETTE['amber']}")
        rows = [
            ("key", s.key),
            ("target", s.target_name),
            ("alias", s.alias),
            ("protector", s.protector_name),
            ("relation", s.relation),
        ]
        for label, value in rows:
            t.append(f"{label:>10} ", style=PALETTE["dim"])
            t.append(f"{value}\n", style=PALETTE["fg"])
        t.append("\n")
        t.append("press ", style=PALETTE["dim"])
        t.append("r", style=f"bold {PALETTE['red']}")
        t.append(" to engage\n", style=PALETTE["dim"])
        return t
