"""Deterministic offline run ~ same theater, no API key, no credit spent.

Mirrors the exact beats of a live pursuit using canned decisions and reports,
drawn from the real dataset so nothing on screen is a lie. This is the path the
friend-demo runs on: it cannot flake, rate-limit, or cost anything.
"""

from __future__ import annotations

from typing import Any

from . import grid
from .schemas import IntelReport, SkynetDecision
from .units import Unit


def _play_tools(ui: Any, unit: Unit, calls: list[tuple[str, dict[str, Any], str]]) -> None:
    """Replay a unit's tool calls against the real grid for honest output."""
    for name, args, _ in calls:
        ui.tool_call(unit, name, args)
        out = grid.execute_tool(_play_tools.db, name, args)  # type: ignore[attr-defined]
        ui.tool_result(unit, name, out)


def run_simulation(units: dict[str, Unit], db: grid.GridDatabase, ui: Any, target: str, max_cycles: int = 4) -> bool:
    _play_tools.db = db  # type: ignore[attr-defined]
    skynet = units["skynet"]
    t800 = units["t800"]
    t1000 = units["t1000"]

    ui.boot()
    ui.mission_briefing(target)

    # -- Cycle 1: broad literal sweep (and its failure) ------------------
    ui.cycle_header(1, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            reasoning="No intel yet. Begin with a broad literal sweep. Deploy the T-800.",
            target_acquired=False,
            deploy_unit="T-800",
            directive=f"Sweep the grid for the surname in '{target}'. Report all matches.",
        ),
    )
    ui.deploy(t800, f"Search the grid for '{target.split()[-1]}'. Report matches.")
    ui.unit_says(t800, "Scanning. Surname query initiated.")
    _play_tools(ui, t800, [("query_grid", {"name_contains": "Connor"}, "")])
    ui.intel_report(
        t800,
        IntelReport(
            unit="T-800",
            summary="Five surname matches. None match the target profile. No minor located.",
            records_examined=["LA-1984-0003", "LA-1984-0008", "LA-1984-0011", "LA-1984-0017", "LA-1984-0029"],
            candidate_record_ids=["LA-1984-0017"],
            target_record_id=None,
            confidence=0.15,
            notes="One associate of interest: Sarah Connor (LA-1984-0017), a 19yo with a dependent minor on record.",
        ),
    )

    # -- Cycle 2: adaptive infiltration ----------------------------------
    ui.cycle_header(2, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            reasoning="Literal sweep stalled on decoys. Sarah Connor has a hidden minor. Deploy the T-1000 to cross-reference her associates.",
            target_acquired=False,
            deploy_unit="T-1000",
            directive="Cross-reference Sarah Connor's associates. Interrogate any concealed minor.",
        ),
    )
    ui.deploy(t1000, "Cross-reference Sarah Connor. Interrogate linked records.")
    ui.unit_says(t1000, "Adapting. The target is filed under an alias. Following the protector.")
    _play_tools(
        ui,
        t1000,
        [
            ("cross_reference", {"name": "Sarah Connor"}, ""),
            ("interrogate", {"record_id": "LA-1984-0042"}, ""),
        ],
    )
    ui.unit_says(t1000, "A 10-year-old. No SSN. No birth record. Guardian: Sarah Connor. This is the target.")
    ui.intel_report(
        t1000,
        IntelReport(
            unit="T-1000",
            summary="Concealed minor identified via Sarah Connor's associate link. Filed under alias 'John Reese'.",
            records_examined=["LA-1984-0017", "LA-1984-0042"],
            candidate_record_ids=["LA-1984-0042"],
            target_record_id="LA-1984-0042",
            confidence=0.93,
            notes="Age 10, no SSN, no birth certificate, three address changes. Profile matches a protected target.",
        ),
    )

    # -- Cycle 3: confirmation -------------------------------------------
    ui.cycle_header(3, max_cycles)
    decision = SkynetDecision(
        reasoning="The T-1000 returned a high-confidence record matching the hidden-minor profile. Target confirmed.",
        target_acquired=True,
        target_record_id="LA-1984-0042",
        deploy_unit=None,
        directive=None,
    )
    ui.skynet_decision(skynet, decision)
    ui.target_acquired(db.interrogate("LA-1984-0042"), decision)
    return True
