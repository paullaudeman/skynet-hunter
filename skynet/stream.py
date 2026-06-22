"""Streaming UI adapter ~ the phase-2 event source.

Same interface the CLI and TUI front-ends consume (it is a `ui` object), but instead
of rendering it serializes each engine call to a plain dict event and hands it to a
sink callable. A web front-end consumes those events (over SSE / websocket) and drives
its own renderer. The engine is unchanged ~ renderer and event-source stay decoupled,
which is the whole point of the `ui` seam.

Pacing: mirrors the CLI's dramatic beats with small sleeps so the stream arrives
animated rather than all-at-once. Set `speed=0` for an instant (test) stream.
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable


def _summary(out: str) -> str:
    try:
        data = json.loads(out)
    except (json.JSONDecodeError, TypeError):
        return str(out)[:60]
    if isinstance(data, list):
        return f"{len(data)} record(s)"
    if isinstance(data, dict) and "error" in data:
        return data["error"]
    if isinstance(data, dict):
        return data.get("name", data.get("id", "1 record"))
    return str(data)[:60]


class StreamUI:
    """Implements the `ui` interface; emits dict events instead of rendering."""

    def __init__(self, sink: Callable[[dict[str, Any]], None], speed: float = 1.0):
        self.sink = sink
        self.speed = speed

    def _emit(self, **ev: Any) -> None:
        self.sink(ev)

    def _pause(self, seconds: float) -> None:
        if self.speed:
            time.sleep(seconds * self.speed)

    # -- opening ----------------------------------------------------------
    def boot(self) -> None:
        self._emit(type="boot")

    def mission_briefing(self, target: str, profile: str | None = None) -> None:
        self._emit(type="briefing", target=target, profile=profile or "")
        self._pause(0.3)

    # -- per-cycle --------------------------------------------------------
    def cycle_header(self, cycle: int, total: int) -> None:
        self._emit(type="cycle", cycle=cycle, total=total)
        self._pause(0.15)

    def skynet_decision(self, unit: Any, decision: Any) -> None:
        self._emit(
            type="skynet", model=getattr(unit, "model", ""),
            assessment=getattr(decision, "assessment", "") or "",
            reasoning=decision.reasoning,
            deploy=getattr(decision, "deploy_unit", None),
            acquired=bool(getattr(decision, "target_acquired", False)),
            expectation=getattr(decision, "expectation", None),
        )
        self._pause(0.5)

    def deploy(self, unit: Any, directive: str) -> None:
        self._emit(type="deploy", unit=unit.key, designation=unit.designation,
                   model=unit.model, directive=directive)
        self._pause(0.3)

    def unit_says(self, unit: Any, text: str) -> None:
        self._emit(type="say", unit=unit.key, text=text)
        self._pause(0.2)

    def tool_call(self, unit: Any, name: str, tool_input: dict[str, Any]) -> None:
        self._emit(type="tool_call", unit=unit.key, name=name, args=tool_input)
        self._pause(0.35)

    def tool_result(self, unit: Any, name: str, out: str) -> None:
        records = []
        try:
            data = json.loads(out)
            items = data if isinstance(data, list) else ([data] if isinstance(data, dict) and "error" not in data else [])
            records = [{"id": r.get("id"), "name": r.get("name")} for r in items if isinstance(r, dict)][:8]
        except (json.JSONDecodeError, TypeError):
            pass
        self._emit(type="tool_result", unit=unit.key, name=name, summary=_summary(out), records=records)
        self._pause(0.25)

    def intel_report(self, unit: Any, report: Any) -> None:
        self._emit(
            type="intel", unit=unit.key, confidence=report.confidence,
            method=getattr(report, "method", "") or "", summary=report.summary,
            target_record_id=report.target_record_id, notes=report.notes,
        )
        self._pause(0.5)

    # -- cost -------------------------------------------------------------
    def cost_tick(self, unit: Any, step_cost: float, running_total: float, estimated: bool = False) -> None:
        self._emit(type="cost", unit=unit.key, step=step_cost, total=running_total)

    def cost_summary(self, meter: Any, units: dict[str, Any]) -> None:
        pass  # the web HUD keeps its own scoreboard

    # -- terminal states --------------------------------------------------
    def target_acquired(self, record: dict[str, Any], decision: Any) -> None:
        self._emit(type="acquired", record=record, reasoning=decision.reasoning)

    def mission_failed(self) -> None:
        self._emit(type="failed")

    def note(self, text: str) -> None:
        self._emit(type="note", text=text)

    # -- arena (counter-terminator) ---------------------------------------
    def faction_banner(self, label: str, color: str = "green") -> None:
        self._emit(type="banner", label=label, color=color)

    def arena_result(self, outcome: str, scenario: Any) -> None:
        self._emit(type="arena", outcome=outcome)
