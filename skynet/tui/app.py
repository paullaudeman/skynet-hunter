"""Phase 1 TUI: a 3-pane HUD that runs a scenario and lights up as it goes.

`TextualUI` is the star ~ it implements the exact method surface the engine
calls on its injected `ui` (mission_briefing, skynet_decision, deploy,
tool_call, tool_result, intel_report, target_acquired, …) but posts to Textual
widgets instead of printing ANSI. The engine is unchanged.

The pursuit runs in a worker thread; the adapter marshals every update back to
the UI thread via `app.call_from_thread`.
"""

from __future__ import annotations

import json
import time
from typing import Any

from rich.markup import escape
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, RichLog, Static

from .themes import CSS, PALETTE
from .widgets import ScenarioPanel, UnitsPanel

_BOOT = [
    "CYBERDYNE SYSTEMS MODEL 101 ~ NEURAL NET CPU ONLINE",
    "uplink to defense grid ......... OK",
    "civil records LOS ANGELES 1984 .. OK",
    "autonomous engagement .......... AUTHORIZED",
]


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
    """Drop-in for the ANSI `UI` ~ same methods, posts to Textual widgets."""

    def __init__(self, app: "Any", delay: float = 1.0) -> None:
        self.app = app
        self.delay = delay  # pacing scaler; tests pass 0

    # -- plumbing --
    def _w(self, markup: str, pause: float = 0.18) -> None:
        self.app.call_from_thread(self.app.log_line, markup)
        if self.delay:
            time.sleep(self.delay * pause)

    def _status(self, key: str, status: str) -> None:
        self.app.call_from_thread(self.app.set_status, key, status)

    # -- the UI interface --
    def boot(self) -> None:
        for line in _BOOT:
            self._w(f"[{PALETTE['dim']}]{escape(line)}[/]", 0.12)

    def mission_briefing(self, target: str, profile: str | None = None) -> None:
        self._w(f"[bold {PALETTE['redhud']}]▓▒░ MISSION BRIEFING ░▒▓[/]")
        self._w(f"[bold {PALETTE['amber']}]PRIMARY OBJECTIVE: terminate {escape(target)}[/]")
        if profile:
            self._w(f"[{PALETTE['dim']}]COUNTERMEASURES: {escape(profile)}[/]")

    def cycle_header(self, cycle: int, total: int) -> None:
        self._w(f"[bold {PALETTE['red']}]── ENGAGEMENT CYCLE {cycle} / {total} ──[/]", 0.25)

    def skynet_decision(self, unit: Any, decision: Any) -> None:
        self._status("skynet", "thinking")
        self._w(f"[bold {PALETTE['skynet']}]◤ SKYNET[/] [{PALETTE['dim']}]\\[{unit.model}][/]")
        assessment = getattr(decision, "assessment", "")
        if assessment:
            self._w(f"[{PALETTE['dim']}]  ANALYSIS  ▸[/] [{PALETTE['skynet']}]{escape(assessment)}[/]")
        self._w(f"[{PALETTE['dim']}]  REASONING ▸[/] [{PALETTE['skynet']}]{escape(decision.reasoning)}[/]")
        if decision.target_acquired:
            self._w(f"[bold {PALETTE['green']}]  DECISION  ▸ TARGET CONFIRMED[/]")
        elif decision.deploy_unit:
            self._w(f"[bold {PALETTE['amber']}]  DECISION  ▸ deploy {escape(decision.deploy_unit)}[/]")
            exp = getattr(decision, "expectation", None)
            if exp:
                self._w(f"[{PALETTE['dim']}]  EXPECT    ▸ {escape(exp)}[/]")
        self._status("skynet", "idle")

    def deploy(self, unit: Any, directive: str) -> None:
        self._status(unit.key, "deployed")
        color = PALETTE.get(unit.color, PALETTE["silver"])
        self._w(f"[bold {color}]❖ DEPLOYING {escape(unit.designation)}[/] [{PALETTE['dim']}]\\[{unit.model}][/]")
        self._w(f"[{PALETTE['dim']}]  DIRECTIVE: {escape(directive)}[/]")

    def unit_says(self, unit: Any, text: str) -> None:
        color = PALETTE.get(unit.color, PALETTE["silver"])
        for line in text.strip().splitlines():
            if line.strip():
                self._w(f"[{color}]  {escape(unit.designation)} »[/] [{PALETTE['fg']}]{escape(line.strip())}[/]")

    def tool_call(self, unit: Any, name: str, tool_input: dict[str, Any]) -> None:
        args = ", ".join(f"{k}={v!r}" for k, v in tool_input.items()) or "~"
        self._w(f"[{PALETTE['dim']}]    ├ {escape(name)}({escape(args)})[/]", 0.12)

    def tool_result(self, unit: Any, name: str, out: str) -> None:
        self._w(f"[{PALETTE['dim']}]    └ grid ▸ {escape(_summarize(out))}[/]", 0.1)

    def intel_report(self, unit: Any, report: Any) -> None:
        color = PALETTE.get(unit.color, PALETTE["silver"])
        self._w(f"[bold {color}]  ▣ {escape(unit.designation)} INTEL[/] [{PALETTE['dim']}]conf {report.confidence:.0%}[/]")
        method = getattr(report, "method", "")
        if method:
            self._w(f"[{PALETTE['dim']}]    method ▸ {escape(method)}[/]")
        self._w(f"[{PALETTE['fg']}]    {escape(report.summary)}[/]")
        if report.target_record_id:
            self._w(f"[bold {PALETTE['green']}]    candidate ▸ {escape(report.target_record_id)}[/]")
        self._status(unit.key, "idle")

    def target_acquired(self, record: dict[str, Any], decision: Any) -> None:
        self._w(f"[bold {PALETTE['redhud']}]▓▒░ TARGET ACQUIRED ░▒▓[/]", 0.3)
        self._w(f"[bold {PALETTE['green']}]◉ {escape(str(record.get('name')))}  ({escape(str(record.get('id')))})[/]")
        self._w(f"[{PALETTE['fg']}]  age {record.get('age')} ~ {escape(str(record.get('occupation')))} ~ {escape(str(record.get('location')))}[/]")
        self._w(f"[{PALETTE['dim']}]  \"Come with me if you want to live.\"[/]")
        self.app.call_from_thread(self.app.mark_done)

    def mission_failed(self) -> None:
        self._w(f"[bold {PALETTE['amber']}]LEADS EXHAUSTED ~ target not confirmed within budget.[/]")
        self.app.call_from_thread(self.app.mark_done)

    def note(self, text: str) -> None:
        self._w(f"[{PALETTE['dim']}]{escape(text)}[/]")


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

    def compose(self) -> ComposeResult:
        yield Static(
            f" CYBERDYNE // SKYNET TERMINAL    ::    OBJECTIVE: {self.scenario.target_name} ",
            id="titlebar",
        )
        with Horizontal(id="body"):
            yield UnitsPanel(self.units)
            yield RichLog(id="log", markup=True, wrap=True, highlight=False, auto_scroll=True)
            yield ScenarioPanel(self.scenario)
        yield Footer()

    def on_mount(self) -> None:
        self.units_panel = self.query_one(UnitsPanel)
        self.query_one("#log", RichLog).write(
            f"[{PALETTE['dim']}]Terminal ready. Press [bold {PALETTE['red']}]r[/] to engage the pursuit.[/]"
        )

    # -- thread-safe widget updates (called via call_from_thread) --
    def log_line(self, markup: str) -> None:
        self.query_one("#log", RichLog).write(markup)

    def set_status(self, key: str, status: str) -> None:
        self.units_panel.set_status(key, status)

    def mark_done(self) -> None:
        self.running = False

    # -- actions --
    def action_run(self) -> None:
        if self.running:
            return
        self.running = True
        log = self.query_one("#log", RichLog)
        log.clear()
        for key in self.units:
            self.units_panel.set_status(key, "idle")
        self.run_pursuit()

    @work(thread=True)
    def run_pursuit(self) -> None:
        from ..simulate import run_simulation

        ui = TextualUI(self, delay=1.0)
        try:
            run_simulation(self.units, self.scenario, ui, self.max_cycles)
        except Exception as exc:  # surface engine errors in the log, don't crash the app
            self.call_from_thread(self.log_line, f"[bold {PALETTE['redhud']}]ERROR:[/] {escape(str(exc))}")
            self.call_from_thread(self.mark_done)


def run_tui(units: dict[str, Any], scenario: Any, max_cycles: int) -> None:
    SkynetApp(units, scenario, max_cycles).run()
