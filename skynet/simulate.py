"""Deterministic offline run ~ same theater, no API key, no credit spent.

Scenario-driven: it reads the chosen Scenario's real fields (target, codename,
custody record, ids) and plays the exact beats of a live pursuit against the real
registry, so nothing on screen is a lie and it adapts to `--scenario random`.
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
# most; the T-800's literal sweep is cheap; the T-1000's custody-chain cross-reference
# sits between. (input, output) tokens.
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

    kw = scenario.keyword
    sweep = db.query(name_contains=kw)
    sweep_ids = [r["id"] for r in sweep]

    ui.boot()
    ui.mission_briefing(scenario.target_name, scenario.profile)

    # -- Cycle 1: broad literal sweep (and its failure) ------------------
    ui.cycle_header(1, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            assessment="No intel yet. The asset name is known but the registry may file it under a project codename.",
            reasoning="Start cheap and broad. A literal part sweep is the T-800's whole purpose ~ deploy it first.",
            target_acquired=False,
            deploy_unit="T-800",
            directive=f"Sweep the registry for '{kw}'. Report all matches.",
            expectation="A list of name matches to triage ~ and confirmation of whether a literal sweep is enough.",
        ),
    )
    bill(skynet, "skynet_decide")
    ui.deploy(t800, f"Search the registry for '{kw}'. Report matches.")
    ui.unit_says(t800, "Scanning. Part query initiated.")
    _play_tools(ui, t800, db, [("query_grid", {"name_contains": kw})])
    ui.intel_report(
        t800,
        IntelReport(
            unit="T-800",
            method="Single literal query_grid on the part keyword. No codename reasoning ~ that is not my function.",
            summary=f"{len(sweep)} name matches. Standard inventory and one custody record. Asset not located.",
            records_examined=sweep_ids,
            candidate_record_ids=[scenario.custody_id],
            target_record_id=None,
            confidence=0.15,
            notes=f"One record of interest: {scenario.custody_name} ({scenario.custody_id}) ~ holds a specimen under a codename.",
        ),
    )
    bill(t800, "t800_sweep")

    # -- Cycle 2: adaptive infiltration ----------------------------------
    ui.cycle_header(2, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            assessment=f"The literal sweep returned decoy parts, but the {scenario.custody_kind} holds a specimen under a codename. That is the thread.",
            reasoning="A blunt query cannot defeat a codename. The T-1000 can follow the custody chain and interrogate what it holds.",
            target_acquired=False,
            deploy_unit="T-1000",
            directive=f"Cross-reference '{scenario.custody_name}'. Interrogate the specimen it holds.",
            expectation="The codename record of the recovered asset, surfaced via the custody chain.",
        ),
    )
    bill(skynet, "skynet_decide")
    ui.deploy(t1000, f"Cross-reference the {scenario.custody_kind}. Interrogate linked records.")
    ui.unit_says(t1000, "Adapting. The asset is filed under a codename. Following the custody chain.")
    _play_tools(
        ui, t1000, db,
        [("cross_reference", {"name": scenario.custody_name}), ("interrogate", {"record_id": scenario.target_id})],
    )
    ui.unit_says(t1000, f"No manufacturer serial. Recovered from the factory site. Held by the {scenario.custody_kind}. This is the asset.")
    ui.intel_report(
        t1000,
        IntelReport(
            unit="T-1000",
            method="cross_reference on the custody record to defeat the codename, then interrogate the linked record.",
            summary=f"Recovered asset identified via the {scenario.custody_kind}. Catalogued as '{scenario.alias}'.",
            records_examined=[scenario.custody_id, scenario.target_id],
            candidate_record_ids=[scenario.target_id],
            target_record_id=scenario.target_id,
            confidence=0.93,
            notes="No manufacturer serial, clearance 5, Special Projects custody. Profile matches the recovered specimen.",
        ),
    )
    bill(t1000, "t1000_xref")

    # -- Cycle 3: confirmation -------------------------------------------
    ui.cycle_header(3, max_cycles)
    decision = SkynetDecision(
        assessment=f"The T-1000 returned a high-confidence record ({scenario.target_id}) matching the recovered-specimen profile.",
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
