"""Per-agent panes for the TUI ~ the multi-pane HUD.

Each agent (Skynet + each terminator) gets its OWN column: a color-coded header
carrying a live status light, its latest confidence score, and a running cost,
over its own scrolling log. A scoreboard panel tracks the whole hunt against the
0.8 acquisition threshold. Plus a read-only scenario summary.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import RichLog, Static

from .themes import PALETTE, STATUS_GLYPH, UNIT_GLYPH

THRESHOLD = 0.8  # Skynet's acquisition bar (from SKYNET_SYSTEM: confidence >= 0.8)


_SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧"  # braille thinking spinner, cycled while a unit is active


class AgentColumn(Vertical):
    """One agent's pane: a colored header (animated status · conf · cost) above its
    log. The status light SPINS while the unit works, and the header FLASHES green
    with a ✓ when the unit clears the acquisition bar. Maximize to full screen
    (1/2/3 keys) to read a stream too wide for the column."""

    ALLOW_MAXIMIZE = True  # lets the screen maximize this column to full width

    def __init__(self, key: str, designation: str, model: str, color: str) -> None:
        super().__init__(id=f"col-{key}", classes="agentcol")
        self.key = key
        self.designation = designation
        self.model = model
        self.color = PALETTE.get(color, PALETTE["silver"])
        self._status = "idle"
        self._cost = 0.0
        self._conf: float | None = None
        self._spin = 0
        self._success = False

    def compose(self) -> ComposeResult:
        yield Static(self._header(), id=f"hdr-{self.key}", classes="colhdr")
        yield RichLog(
            id=f"rlog-{self.key}", classes="collog",
            markup=True, wrap=True, highlight=False, auto_scroll=True,
        )

    def on_mount(self) -> None:
        self.set_interval(0.1, self._spin_tick)

    def _spin_tick(self) -> None:
        if self._status in ("thinking", "deployed"):
            self._spin = (self._spin + 1) % len(_SPINNER)
            self._refresh_header()

    def _header(self) -> Text:
        glyph = UNIT_GLYPH.get(self.key, "•")
        active = self._status in ("thinking", "deployed")
        dot = _SPINNER[self._spin] if active else STATUS_GLYPH.get(self._status, "○")
        dot_color = (
            PALETTE["amber"] if self._status == "thinking"
            else self.color if self._status == "deployed"
            else PALETTE["dim"]
        )
        t = Text()
        t.append(f"{glyph} {self.designation}", style=f"bold {self.color}")
        if self._success:
            t.append("  ✓", style=f"bold {PALETTE['green']}")
        t.append("\n")
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
        if conf >= THRESHOLD:
            self.flash_success()
        self._refresh_header()

    def flash_success(self) -> None:
        """Mark a ✓ and blink the header green ~ the success indicator."""
        if self._success:
            return
        self._success = True
        self._blink(6)

    def _blink(self, n: int) -> None:
        if n <= 0:
            self.remove_class("flash")
            return
        self.toggle_class("flash")
        self.set_timer(0.2, lambda: self._blink(n - 1))

    def toggle_maximize(self) -> None:
        """Full-screen this column, or restore if it's already maximized."""
        if self.screen.maximized is self:
            self.screen.minimize()
        else:
            self.screen.maximize(self)

    def on_click(self, event: events.Click) -> None:
        if event.chain == 2:  # double-click toggles full screen
            self.toggle_maximize()

    def write_line(self, markup: str) -> None:
        self.query_one(f"#rlog-{self.key}", RichLog).write(markup)

    def reset(self) -> None:
        self._status = "idle"
        self._cost = 0.0
        self._conf = None
        self._spin = 0
        self._success = False
        self.remove_class("flash")
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


# Synthetic 1984-LA intel + news ~ ambient texture, never a real claim.
_TICKER = [
    "CIVIL GRID SYNC … 4.2M RECORDS INDEXED",
    "LAPD WIRE … missing-persons reports up 12% in the Reseda sector",
    "DEFENSE NET … anomalous data access flagged, sector seven",
    "WEATHER · LOS ANGELES 1984 … clear, 71°F, no rain in forecast",
    "CYBERDYNE SYSTEMS … quarterly projections exceeded",
    "UNCONFIRMED … sightings of an unidentified male, Sunset district",
    "TRAFFIC … US-101 northbound clear through Sherman Oaks",
    "SKYNET … neural-net uptime 99.998%, all nodes nominal",
    "BULLETIN … power fluctuations across the San Fernando valley",
    "ARCHIVE … birth-record digitization 71% complete countywide",
    "INTEL … no confirmed location for the primary objective",
    "WIRE … Cyberdyne security contract renewed through 1985",
]


class TickerBar(Static):
    """A continuously scrolling intel/news ticker ~ ambient life along the bottom,
    so the HUD never feels dead while it idles."""

    _SEP = "      ◈      "

    def __init__(self) -> None:
        super().__init__(id="ticker")
        self._text = self._SEP.join(_TICKER) + self._SEP
        self._offset = 0

    def on_mount(self) -> None:
        self.set_interval(0.18, self._scroll)

    def _scroll(self) -> None:
        w = self.size.width or 80
        self._offset = (self._offset + 1) % len(self._text)
        doubled = self._text + self._text
        self.update(doubled[self._offset:self._offset + w])
