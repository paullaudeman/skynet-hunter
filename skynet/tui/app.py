"""The multi-pane TUI: one column per agent, output routed per-unit, plus a live
scoreboard tracking the hunt against the acquisition threshold.

`TextualUI` implements the exact method surface the engine calls on its injected
`ui` (mission_briefing, skynet_decision, deploy, tool_call, intel_report,
cost_tick, …) but posts each agent's stream to that agent's OWN column instead of
one shared log. Skynet's column carries the command narrative; each terminator's
column carries its field activity. Confidence + cost land in the column headers;
the scoreboard accumulates the run.

The pursuit runs in a worker thread; the adapter marshals every update back to
the UI thread via `app.call_from_thread`. The engine is unchanged.
"""

from __future__ import annotations

import json
import time
from typing import Any

from rich.markup import escape
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Static

from .themes import CSS, PALETTE
from .widgets import AgentColumn, ScenarioPanel, ScoreboardPanel

_BOOT = [
    "CYBERDYNE MODEL 101 ~ NEURAL NET CPU ONLINE",
    "uplink to defense grid ......... OK",
    "civil records LA 1984 .......... OK",
    "autonomous engagement .......... AUTHORIZED",
]

_ORDER = ["skynet", "t1000", "t800"]


def _summarize(out: str) -> str:
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return str(out)[:60]
    if isinstance(data, list):
        return f"{len(data)} record(s)"
    if isinstance(data, dict) and "error" in data:
        return str(data["error"])
    if isinstance(data, dict):
        return str(data.get("name", data.get("id", "1 record")))
    return str(data)[:60]


class TextualUI:
    """Drop-in for the ANSI `UI` ~ same methods, routes each agent to its column."""

    def __init__(self, app: "Any", delay: float = 1.0) -> None:
        self.app = app
        self.delay = delay  # pacing scaler; tests pass 0

    # -- plumbing --
    def _w(self, key: str, markup: str, pause: float = 0.18) -> None:
        self.app.call_from_thread(self.app.log_to, key, markup)
        if self.delay:
            time.sleep(self.delay * pause)

    def _status(self, key: str, status: str) -> None:
        self.app.call_from_thread(self.app.set_status, key, status)

    def _color(self, unit: Any) -> str:
        return PALETTE.get(unit.color, PALETTE["silver"])

    # -- the UI interface (Skynet column = command narrative) --
    def boot(self) -> None:
        for line in _BOOT:
            self._w("skynet", f"[{PALETTE['dim']}]{escape(line)}[/]", 0.12)

    def mission_briefing(self, target: str, profile: str | None = None) -> None:
        self._w("skynet", f"[bold {PALETTE['redhud']}]▓▒░ MISSION BRIEFING ░▒▓[/]")
        self._w("skynet", f"[bold {PALETTE['amber']}]OBJECTIVE: terminate {escape(target)}[/]")
        if profile:
            self._w("skynet", f"[{PALETTE['dim']}]{escape(profile)}[/]")

    def cycle_header(self, cycle: int, total: int) -> None:
        self.app.call_from_thread(self.app.score_cycle, cycle)
        self._w("skynet", f"[bold {PALETTE['red']}]── CYCLE {cycle} / {total} ──[/]", 0.25)

    def skynet_decision(self, unit: Any, decision: Any) -> None:
        self._status("skynet", "thinking")
        assessment = getattr(decision, "assessment", "")
        if assessment:
            self._w("skynet", f"[{PALETTE['dim']}]ANALYSIS ▸[/] [{PALETTE['skynet']}]{escape(assessment)}[/]")
        self._w("skynet", f"[{PALETTE['dim']}]REASON ▸[/] [{PALETTE['skynet']}]{escape(decision.reasoning)}[/]")
        if decision.target_acquired:
            self._w("skynet", f"[bold {PALETTE['green']}]DECISION ▸ TARGET CONFIRMED[/]")
        elif decision.deploy_unit:
            self._w("skynet", f"[bold {PALETTE['amber']}]DECISION ▸ deploy {escape(decision.deploy_unit)}[/]")
            exp = getattr(decision, "expectation", None)
            if exp:
                self._w("skynet", f"[{PALETTE['dim']}]EXPECT ▸ {escape(exp)}[/]")
        self._status("skynet", "idle")

    # -- worker columns = field activity --
    def deploy(self, unit: Any, directive: str) -> None:
        self._status(unit.key, "deployed")
        self._w(unit.key, f"[bold {self._color(unit)}]❖ DEPLOY[/]  [{PALETTE['dim']}]{escape(directive)}[/]")

    def unit_says(self, unit: Any, text: str) -> None:
        c = self._color(unit)
        for line in text.strip().splitlines():
            if line.strip():
                self._w(unit.key, f"[{c}]»[/] [{PALETTE['fg']}]{escape(line.strip())}[/]")

    def tool_call(self, unit: Any, name: str, tool_input: dict[str, Any]) -> None:
        args = ", ".join(f"{k}={v!r}" for k, v in tool_input.items()) or "~"
        self._w(unit.key, f"[{PALETTE['dim']}]├ {escape(name)}({escape(args)})[/]", 0.12)

    def tool_result(self, unit: Any, name: str, out: str) -> None:
        self._w(unit.key, f"[{PALETTE['dim']}]└ grid ▸ {escape(_summarize(out))}[/]", 0.1)

    def intel_report(self, unit: Any, report: Any) -> None:
        c = self._color(unit)
        self._w(unit.key, f"[bold {c}]▣ INTEL[/] [{PALETTE['dim']}]conf {report.confidence:.0%}[/]")
        method = getattr(report, "method", "")
        if method:
            self._w(unit.key, f"[{PALETTE['dim']}]method ▸ {escape(method)}[/]")
        self._w(unit.key, f"[{PALETTE['fg']}]{escape(report.summary)}[/]")
        if report.target_record_id:
            self._w(unit.key, f"[bold {PALETTE['green']}]candidate ▸ {escape(report.target_record_id)}[/]")
        self.app.call_from_thread(self.app.set_conf, unit.key, report.confidence)
        self.app.call_from_thread(self.app.score_conf, report.confidence)
        self._status(unit.key, "idle")

    def target_acquired(self, record: dict[str, Any], decision: Any) -> None:
        self.app.call_from_thread(self.app.score_state, "ACQUIRED")
        self._w("skynet", f"[bold {PALETTE['redhud']}]▓▒░ TARGET ACQUIRED ░▒▓[/]", 0.3)
        self._w("skynet", f"[bold {PALETTE['green']}]◉ {escape(str(record.get('name')))} ({escape(str(record.get('id')))})[/]")
        self._w("skynet", f"[{PALETTE['fg']}]age {record.get('age')} ~ {escape(str(record.get('occupation')))} ~ {escape(str(record.get('location')))}[/]")
        self._w("skynet", f"[{PALETTE['dim']}]\"Come with me if you want to live.\"[/]")
        self.app.call_from_thread(self.app.mark_done)

    def mission_failed(self) -> None:
        self.app.call_from_thread(self.app.score_state, "EXHAUSTED")
        self._w("skynet", f"[bold {PALETTE['amber']}]LEADS EXHAUSTED ~ target not confirmed within budget.[/]")
        self.app.call_from_thread(self.app.mark_done)

    def note(self, text: str) -> None:
        self._w("skynet", f"[{PALETTE['dim']}]{escape(text)}[/]")

    # -- cost meter ~ per-column header (cumulative) + scoreboard (total) --
    def cost_tick(self, unit: Any, step_cost: float, running_total: float, estimated: bool = False) -> None:
        self.app.call_from_thread(self.app.add_cost, unit.key, step_cost)
        self.app.call_from_thread(self.app.score_cost, running_total)

    def cost_summary(self, meter: Any, units: dict[str, Any]) -> None:
        self._w("skynet", f"[bold {PALETTE['amber']}]── ENGAGEMENT COST ──[/]")
        by_model = {u.model: u for u in units.values()}
        for row in meter.rows():
            u = by_model.get(row.model)
            c = PALETTE.get(u.color, PALETTE["silver"]) if u else PALETTE["silver"]
            desig = u.designation if u else row.model
            self._w("skynet", f"[{c}]{escape(desig)}[/] [{PALETTE['dim']}]${row.cost:.4f}[/]")
        tag = " (est)" if meter.estimated else ""
        self._w("skynet", f"[bold {PALETTE['green']}]TOTAL ${meter.total_cost:.4f}{tag}[/]")


class SkynetApp(App):
    CSS = CSS
    TITLE = "Skynet Hunter"
    BINDINGS = [("r", "run", "Run"), ("q", "quit", "Quit")]

    def __init__(self, units: dict[str, Any], scenario: Any, max_cycles: int) -> None:
        super().__init__()
        self.units = units
        self.scenario = scenario
        self.max_cycles = max_cycles
        self.running = False
        self.columns: dict[str, AgentColumn] = {}
        self.scoreboard: ScoreboardPanel | None = None

    def compose(self) -> ComposeResult:
        yield Static(
            f" CYBERDYNE // SKYNET TERMINAL    ::    OBJECTIVE: {self.scenario.target_name} [blink]█[/] ",
            id="titlebar",
        )
        with Horizontal(id="body"):
            for key in _ORDER:
                u = self.units.get(key)
                if u is None:
                    continue
                col = AgentColumn(key, u.designation, u.model, u.color)
                self.columns[key] = col
                yield col
            with Vertical(id="sidebar"):
                yield ScenarioPanel(self.scenario)
                self.scoreboard = ScoreboardPanel(self.max_cycles)
                yield self.scoreboard
        yield Footer()

    def on_mount(self) -> None:
        for col in self.columns.values():
            col.write_line(f"[{PALETTE['dim']}]standby ~ press [bold {PALETTE['red']}]r[/] to engage[/]")
        self._power_on()

    def _power_on(self) -> None:
        """CRT warm-up flicker ~ ramp the screen opacity with a couple of dips."""
        self.screen.styles.opacity = 0.0
        for delay, value in [(0.05, 0.65), (0.12, 0.12), (0.19, 0.9), (0.28, 0.35), (0.38, 1.0)]:
            self.set_timer(delay, lambda v=value: self._screen_opacity(v))

    def _screen_opacity(self, value: float) -> None:
        self.screen.styles.opacity = value

    # -- thread-safe widget updates (called via call_from_thread) --
    def log_to(self, key: str, markup: str) -> None:
        col = self.columns.get(key)
        if col is not None:
            col.write_line(markup)

    def set_status(self, key: str, status: str) -> None:
        col = self.columns.get(key)
        if col is not None:
            col.set_status(status)

    def add_cost(self, key: str, delta: float) -> None:
        col = self.columns.get(key)
        if col is not None:
            col.add_cost(delta)

    def set_conf(self, key: str, conf: float) -> None:
        col = self.columns.get(key)
        if col is not None:
            col.set_conf(conf)

    def score_cycle(self, n: int) -> None:
        if self.scoreboard is not None:
            self.scoreboard.set_cycle(n)

    def score_conf(self, conf: float) -> None:
        if self.scoreboard is not None:
            self.scoreboard.report_conf(conf)

    def score_cost(self, cost: float) -> None:
        if self.scoreboard is not None:
            self.scoreboard.set_cost(cost)

    def score_state(self, state: str) -> None:
        if self.scoreboard is not None:
            self.scoreboard.set_state(state)

    def mark_done(self) -> None:
        self.running = False

    # -- actions --
    def action_run(self) -> None:
        if self.running:
            return
        self.running = True
        for col in self.columns.values():
            col.reset()
        if self.scoreboard is not None:
            self.scoreboard.reset()
        self.run_pursuit()

    @work(thread=True)
    def run_pursuit(self) -> None:
        from ..simulate import run_simulation

        ui = TextualUI(self, delay=1.0)
        try:
            run_simulation(self.units, self.scenario, ui, self.max_cycles)
        except Exception as exc:  # surface engine errors in Skynet's column, don't crash
            self.call_from_thread(self.log_to, "skynet", f"[bold {PALETTE['redhud']}]ERROR:[/] {escape(str(exc))}")
            self.call_from_thread(self.mark_done)


def run_tui(units: dict[str, Any], scenario: Any, max_cycles: int) -> None:
    SkynetApp(units, scenario, max_cycles).run()
