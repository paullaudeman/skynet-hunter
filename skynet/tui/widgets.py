"""Side panels for the TUI: the unit roster (with status lights) and a
read-only scenario summary. (Editing the scenario is phase 3.)"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.widgets import Static

from .themes import PALETTE, STATUS_GLYPH, UNIT_GLYPH

_ORDER = ["skynet", "t1000", "t800"]


class UnitsPanel(Static):
    """The terminator roster with live status lights."""

    def __init__(self, units: dict[str, Any]) -> None:
        super().__init__(id="units")
        self.units = units
        self.status = {k: "idle" for k in units}

    def set_status(self, key: str, status: str) -> None:
        if key in self.status:
            self.status[key] = status
            self.refresh()

    def render(self) -> Text:
        t = Text()
        t.append("UNITS\n\n", style=f"bold {PALETTE['amber']}")
        for key in _ORDER:
            unit = self.units.get(key)
            if unit is None:
                continue
            color = PALETTE.get(unit.color, PALETTE["silver"])
            status = self.status.get(key, "idle")
            glyph = UNIT_GLYPH.get(key, "•")
            t.append(f"{glyph} {unit.designation}\n", style=f"bold {color}")
            dot = STATUS_GLYPH.get(status, "○")
            dot_color = PALETTE["amber"] if status == "thinking" else (color if status == "deployed" else PALETTE["dim"])
            t.append(f"  {dot} ", style=dot_color)
            t.append(f"{status}\n", style=PALETTE["dim"])
            t.append(f"  {unit.model}\n\n", style=PALETTE["dim"])
        return t


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
