"""Terminal theater ~ boot sequence, HUD, typewriter, colored unit output.

Pure rendering. Reads attributes off Unit / IntelReport / SkynetDecision objects
so it doesn't care whether the intel came from a live agent or the simulator.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

from .theme import Theme

_W = 64

_TITLE = r"""
 ███████╗██╗  ██╗██╗   ██╗███╗   ██╗███████╗████████╗
 ██╔════╝██║ ██╔╝╚██╗ ██╔╝████╗  ██║██╔════╝╚══██╔══╝
 ███████╗█████╔╝  ╚████╔╝ ██╔██╗ ██║█████╗     ██║
 ╚════██║██╔═██╗   ╚██╔╝  ██║╚██╗██║██╔══╝     ██║
 ███████║██║  ██╗   ██║   ██║ ╚████║███████╗   ██║
 ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝   ╚═╝
"""

_BOOT_LINES = [
    "CYBERDYNE SYSTEMS MODEL 101 ~ NEURAL NET CPU ONLINE",
    "establishing uplink to defense grid ......... OK",
    "loading civil records: LOS ANGELES / 1984 .... OK",
    "mission parameters ........................... LOADED",
    "autonomous engagement ........................ AUTHORIZED",
]


class UI:
    def __init__(self, theme: Theme, art: bool = True):
        self.t = theme
        self.art = art

    # -- low-level --------------------------------------------------------
    def _out(self, s: str = "") -> None:
        sys.stdout.write(s + "\n")
        sys.stdout.flush()

    def _type(self, s: str, delay: float = 0.0008) -> None:
        if not self.art:
            self._out(s)
            return
        for ch in s:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write("\n")
        sys.stdout.flush()

    def _pause(self, seconds: float) -> None:
        if self.art:
            time.sleep(seconds)

    # -- opening ----------------------------------------------------------
    def boot(self) -> None:
        self._out(self.t.paint("frame", _TITLE, bold=True))
        self._out(self.t.band("SKYNET HUNTER ~ AGENTIC PURSUIT PROTOCOL"))
        self._out()
        for line in _BOOT_LINES:
            self._type(self.t.paint("dim", "  " + line))
            self._pause(0.12)
        self._out()

    def mission_briefing(self, target: str) -> None:
        self._out(self.t.band("MISSION BRIEFING"))
        self._out(self.t.unit("blue", "  SKYNET", bold=True) + self.t.paint("dim", "  command intelligence online"))
        self._out(self.t.paint("accent", f"  PRIMARY OBJECTIVE: terminate {target}", bold=True))
        self._out(self.t.paint("dim", "  RESISTANCE COUNTERMEASURES: target concealed under alias"))
        self._out()
        self._pause(0.3)

    # -- per-cycle --------------------------------------------------------
    def cycle_header(self, cycle: int, total: int) -> None:
        self._out(self.t.band(f"ENGAGEMENT CYCLE {cycle} / {total}"))

    def skynet_decision(self, unit: Any, decision: Any) -> None:
        tag = self.t.unit("blue", "  ◤ SKYNET", bold=True)
        self._out(tag + self.t.paint("dim", f"  [{unit.model}]"))
        self._type(self.t.unit("blue", f"    {decision.reasoning}"))
        if decision.target_acquired:
            self._out(self.t.paint("ok", "    DECISION: TARGET CONFIRMED", bold=True))
        elif decision.deploy_unit:
            self._out(self.t.paint("accent", f"    DECISION: deploy {decision.deploy_unit}", bold=True))
        self._out()
        self._pause(0.2)

    def deploy(self, unit: Any, directive: str) -> None:
        c = unit.color
        glyph = "⚙" if unit.key == "t800" else "❖"
        self._out(self.t.unit(c, f"  {glyph} DEPLOYING {unit.designation}", bold=True) + self.t.paint("dim", f"  [{unit.model}]"))
        self._type(self.t.paint("dim", f"    DIRECTIVE: {directive}"))
        self._pause(0.15)

    def unit_says(self, unit: Any, text: str) -> None:
        for line in text.strip().splitlines():
            if line.strip():
                self._out(self.t.unit(unit.color, f"    {unit.designation} » ") + self.t.paint("accent", line.strip()))

    def tool_call(self, unit: Any, name: str, tool_input: dict[str, Any]) -> None:
        args = ", ".join(f"{k}={v!r}" for k, v in tool_input.items()) or "~"
        self._out(self.t.paint("dim", f"      ├─ {name}({args})"))

    def tool_result(self, unit: Any, name: str, out: str) -> None:
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            data = out
        if isinstance(data, list):
            summary = f"{len(data)} record(s)"
        elif isinstance(data, dict) and "error" in data:
            summary = data["error"]
        elif isinstance(data, dict):
            summary = data.get("name", data.get("id", "1 record"))
        else:
            summary = str(data)[:60]
        self._out(self.t.paint("dim", f"      └─ grid ▸ {summary}"))
        self._pause(0.05)

    def intel_report(self, unit: Any, report: Any) -> None:
        c = unit.color
        conf = f"{report.confidence:.0%}"
        self._out(self.t.unit(c, f"    ▣ {unit.designation} INTEL", bold=True) + self.t.paint("dim", f"  confidence {conf}"))
        self._out(self.t.paint("accent", f"      {report.summary}"))
        if report.target_record_id:
            self._out(self.t.paint("ok", f"      candidate target: {report.target_record_id}", bold=True))
        if report.notes:
            self._out(self.t.paint("dim", f"      note: {report.notes}"))
        self._out()
        self._pause(0.2)

    # -- terminal states --------------------------------------------------
    def target_acquired(self, record: dict[str, Any], decision: Any) -> None:
        self._out()
        self._out(self.t.band("TARGET ACQUIRED"))
        self._out(self.t.paint("ok", f"  ◉ {record.get('name')}  ({record.get('id')})", bold=True))
        self._out(self.t.paint("accent", f"    age {record.get('age')} ~ {record.get('occupation')} ~ {record.get('location')}"))
        if record.get("notes"):
            self._out(self.t.paint("dim", f"    {record['notes']}"))
        self._out(self.t.unit("blue", f"  SKYNET: {decision.reasoning}"))
        self._out()
        self._out(self.t.paint("bad", "  ▓▒░ MISSION COMPLETE ░▒▓", bold=True))
        self._out(self.t.paint("dim", '  "Come with me if you want to live."'))
        self._out()

    def mission_failed(self) -> None:
        self._out()
        self._out(self.t.band("LEADS EXHAUSTED"))
        self._out(self.t.paint("warn", "  Target not confirmed within engagement budget.", bold=True))
        self._out(self.t.paint("dim", "  The future is not set. There is no fate but what we make."))
        self._out()

    def note(self, text: str) -> None:
        self._out(self.t.paint("dim", f"  {text}"))
