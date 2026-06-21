"""Deterministic offline run ~ same theater, no API key, no credit spent.

Scenario-driven: it reads the chosen Scenario's real fields (target, alias,
protector, ids) and plays the exact beats of a live pursuit against the real
grid, so nothing on screen is a lie and it adapts to `--scenario random`.
"""

from __future__ import annotations

from typing import Any

from . import grid
from .cost import CostMeter, estimate
from .schemas import IntelReport, SkynetDecision
from .scenario import Scenario
from .units import Unit

# Representative per-call token counts for the offline path ~ honest ballparks,
# flagged EST on screen. Skynet reasons hard (xhigh thinking) so it spends the
# most; the T-800's literal sweep is cheap; the T-1000's cross-reference sits
# between. (input, output) tokens.
_EST = {
    "skynet_decide": (1500, 2400),   # Opus, thinking-heavy strategic call
    "skynet_confirm": (1800, 900),   # Opus, the shorter acquisition call
    "t800_sweep": (900, 450),        # Haiku, blunt single-query report
    "t1000_xref": (1400, 1700),      # Sonnet, adaptive multi-tool reasoning
}


def _play_tools(ui: Any, unit: Unit, db: grid.GridDatabase, calls: list[tuple[str, dict[str, Any]]]) -> None:
    """Replay a unit's tool calls against the real grid for honest output."""
    for name, args in calls:
        ui.tool_call(unit, name, args)
        ui.tool_result(unit, name, grid.execute_tool(db, name, args))


def run_simulation(units: dict[str, Unit], scenario: Scenario, ui: Any, max_cycles: int = 4) -> bool:
    db = scenario.database()
    skynet, t800, t1000 = units["skynet"], units["t800"], units["t1000"]

    meter = CostMeter()

    def bill(unit: Unit, beat: str) -> None:
        """Record one beat's estimated usage and tick the meter on screen."""
        in_tok, out_tok = _EST[beat]
        cost = meter.record(unit.model, estimate(in_tok, out_tok), estimated=True)
        if hasattr(ui, "cost_tick"):
            ui.cost_tick(unit, cost, meter.total_cost, meter.estimated)

    first = scenario.target_name.split()[0]
    last = scenario.target_name.split()[-1]
    sweep = db.query(name_contains=last)
    sweep_ids = [r["id"] for r in sweep]

    ui.boot()
    ui.mission_briefing(scenario.target_name, scenario.profile)

    # -- Cycle 1: broad literal sweep (and its failure) ------------------
    ui.cycle_header(1, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            assessment="No intel yet. The target name is known but the grid may file them under an alias.",
            reasoning="Start cheap and broad. A literal surname sweep is the T-800's whole purpose ~ deploy it first.",
            target_acquired=False,
            deploy_unit="T-800",
            directive=f"Sweep the grid for the surname '{last}'. Report all matches.",
            expectation="A list of surname matches to triage ~ and confirmation of whether a literal sweep is enough.",
        ),
    )
    bill(skynet, "skynet_decide")
    ui.deploy(t800, f"Search the grid for '{last}'. Report matches.")
    ui.unit_says(t800, "Scanning. Surname query initiated.")
    _play_tools(ui, t800, db, [("query_grid", {"name_contains": last})])
    ui.intel_report(
        t800,
        IntelReport(
            unit="T-800",
            method="Single literal query_grid on the surname. No alias reasoning ~ that is not my function.",
            summary=f"{len(sweep)} surname matches. None match the target profile. No minor located.",
            records_examined=sweep_ids,
            candidate_record_ids=[scenario.protector_id],
            target_record_id=None,
            confidence=0.15,
            notes=f"One associate of interest: {scenario.protector_name} ({scenario.protector_id}) ~ flagged with a dependent minor on record.",
        ),
    )
    bill(t800, "t800_sweep")

    # -- Cycle 2: adaptive infiltration ----------------------------------
    ui.cycle_header(2, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            assessment=f"The literal sweep returned only decoys, but {scenario.protector_name} carries a dependent-minor flag. That is the thread.",
            reasoning="A blunt query cannot defeat an alias. The T-1000 can cross-reference the protector and interrogate whoever is concealed behind them.",
            target_acquired=False,
            deploy_unit="T-1000",
            directive=f"Cross-reference {scenario.protector_name}'s associates. Interrogate any concealed minor.",
            expectation="The aliased record of the hidden minor, surfaced via the protector's associate link.",
        ),
    )
    bill(skynet, "skynet_decide")
    ui.deploy(t1000, f"Cross-reference {scenario.protector_name}. Interrogate linked records.")
    ui.unit_says(t1000, "Adapting. The target is filed under an alias. Following the protector.")
    _play_tools(
        ui, t1000, db,
        [("cross_reference", {"name": scenario.protector_name}), ("interrogate", {"record_id": scenario.target_id})],
    )
    ui.unit_says(t1000, f"A minor. No SSN. No birth record. Guardian: {scenario.protector_name}. This is the target.")
    ui.intel_report(
        t1000,
        IntelReport(
            unit="T-1000",
            method=f"cross_reference on {scenario.protector_name} to defeat the alias, then interrogate the linked record.",
            summary=f"Concealed minor identified via {scenario.protector_name}'s associate link. Filed under alias '{scenario.alias}'.",
            records_examined=[scenario.protector_id, scenario.target_id],
            candidate_record_ids=[scenario.target_id],
            target_record_id=scenario.target_id,
            confidence=0.93,
            notes="No SSN, no birth certificate, multiple address changes. Profile matches a protected target.",
        ),
    )
    bill(t1000, "t1000_xref")

    # -- Cycle 3: confirmation -------------------------------------------
    ui.cycle_header(3, max_cycles)
    decision = SkynetDecision(
        assessment=f"The T-1000 returned a high-confidence record ({scenario.target_id}) matching the hidden-minor profile.",
        reasoning="Confidence exceeds the acquisition threshold and the profile fits. No further deployment is warranted.",
        target_acquired=True,
        target_record_id=scenario.target_id,
        deploy_unit=None,
        directive=None,
        expectation=None,
    )
    ui.skynet_decision(skynet, decision)
    bill(skynet, "skynet_confirm")
    ui.target_acquired(db.interrogate(scenario.target_id), decision)
    if hasattr(ui, "cost_summary"):
        ui.cost_summary(meter, units)
    return True
