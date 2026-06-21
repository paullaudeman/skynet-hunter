"""The arena ~ two orchestrators racing on one grid (the counter-terminator).

Skynet hunts; the Resistance disrupts. Deterministic offline arc, the same
discipline as `simulate.py` (nothing on screen is a lie):

    cycle 1   Skynet's literal sweep surfaces the guardian's dependent-minor flag
    ↓
    RESIST    a reprogrammed protector SCRUBS that flag and severs the link
    ↓
    cycle 2   Skynet escalates to a cross-reference ~ and finds NOTHING
    ↓
    result    leads exhausted; the target is safeguarded

The scrub really mutates the live grid, so the failed cross-reference in cycle 2
is the genuine consequence of the disruption, not a script. That is the whole
point: the counter-agent changes the outcome.
"""

from __future__ import annotations

from typing import Any

from . import grid
from .cost import CostMeter, estimate
from .schemas import IntelReport, SkynetDecision
from .scenario import Scenario
from .units import Unit

# Representative per-call token counts (flagged EST on screen), both factions.
_EST = {
    "skynet": (1600, 2200),
    "t800": (900, 450),
    "t1000": (1400, 1500),
    "resistance": (1000, 700),
}


def _play(ui: Any, unit: Unit, db: grid.GridDatabase, calls: list[tuple[str, dict[str, Any]]]) -> None:
    """Replay a unit's tool calls against the REAL grid ~ honest output."""
    for name, args in calls:
        ui.tool_call(unit, name, args)
        ui.tool_result(unit, name, grid.execute_tool(db, name, args))


def run_arena_simulation(units: dict[str, Unit], scenario: Scenario, ui: Any, max_cycles: int = 4) -> bool:
    """Run the adversarial arena. Returns True if Skynet acquires, else False
    (the target is safeguarded). Offline + deterministic."""
    db = scenario.database()
    skynet, t800, t1000 = units["skynet"], units["t800"], units["t1000"]
    resistance = units["resistance"]
    last = scenario.target_name.split()[-1]
    sweep = db.query(name_contains=last)
    meter = CostMeter()

    def bill(unit: Unit, beat: str) -> None:
        in_tok, out_tok = _EST[beat]
        cost = meter.record(unit.model, estimate(in_tok, out_tok), estimated=True)
        if hasattr(ui, "cost_tick"):
            ui.cost_tick(unit, cost, meter.total_cost, meter.estimated)

    ui.boot()
    ui.mission_briefing(scenario.target_name, scenario.profile)
    if hasattr(ui, "faction_banner"):
        ui.faction_banner("THE RESISTANCE HAS SENT A PROTECTOR BACK", "green")

    # -- Cycle 1: Skynet's literal sweep surfaces the guardian's flag ----
    ui.cycle_header(1, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            assessment="No intel yet. Open cheap and broad.",
            reasoning="A literal surname sweep is the T-800's whole purpose ~ deploy it first.",
            target_acquired=False, deploy_unit="T-800",
            directive=f"Sweep the grid for the surname '{last}'.",
            expectation="Surname matches to triage ~ and any flagged associate of interest.",
        ),
    )
    bill(skynet, "skynet")
    ui.deploy(t800, f"Search the grid for '{last}'.")
    ui.unit_says(t800, "Scanning. Surname query initiated.")
    _play(ui, t800, db, [("query_grid", {"name_contains": last})])
    ui.intel_report(
        t800,
        IntelReport(
            unit="T-800",
            method="Single literal query_grid on the surname.",
            summary=(f"{len(sweep)} surname matches. None match the target. The guardian "
                     f"{scenario.protector_name} carries a dependent-minor flag ~ a thread."),
            records_examined=[r["id"] for r in sweep],
            candidate_record_ids=[scenario.protector_id],
            target_record_id=None, confidence=0.15,
            notes=f"{scenario.protector_name} ({scenario.protector_id}) flagged with a dependent minor.",
        ),
    )
    bill(t800, "t800")

    # -- Resistance turn: the protector scrubs the flag, severs the link -
    if hasattr(ui, "faction_banner"):
        ui.faction_banner("RESISTANCE ~ PROTECTOR DEPLOYED", "green")
    ui.deploy(resistance, f"The hunter found {scenario.protector_name}'s flag. Sever the trail before the cross-reference.")
    ui.unit_says(resistance, "Reprogrammed. Directive: protect. Cutting the link to the child.")
    _play(ui, resistance, db, [("scrub_flag", {"record_id": scenario.protector_id})])
    ui.unit_says(resistance, "Flag scrubbed. Associate links severed. The trail is cold.")
    bill(resistance, "resistance")

    # -- Cycle 2: Skynet escalates to the T-1000 ~ but the link is gone --
    ui.cycle_header(2, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            assessment=f"{scenario.protector_name} carries a dependent-minor flag. That is the thread.",
            reasoning="A blunt query can't defeat an alias. Deploy the T-1000 to cross-reference the guardian.",
            target_acquired=False, deploy_unit="T-1000",
            directive=f"Cross-reference {scenario.protector_name}. Interrogate any concealed minor.",
            expectation="The aliased record of the hidden minor, via the guardian's associate link.",
        ),
    )
    bill(skynet, "skynet")
    ui.deploy(t1000, f"Cross-reference {scenario.protector_name}.")
    ui.unit_says(t1000, "Adapting. Following the guardian's associate links.")
    _play(ui, t1000, db, [("cross_reference", {"name": scenario.protector_name})])
    ui.unit_says(t1000, "No linked records. The associate trail has been wiped.")
    ui.intel_report(
        t1000,
        IntelReport(
            unit="T-1000",
            method=f"cross_reference on {scenario.protector_name} ~ returned nothing.",
            summary="The guardian's associate links are gone. No concealed minor reachable. Trail severed.",
            records_examined=[scenario.protector_id], candidate_record_ids=[],
            target_record_id=None, confidence=0.0,
            notes="Records were sanitized between cycles. Someone is covering the target's tracks.",
        ),
    )
    bill(t1000, "t1000")

    # -- Cycle 3: Skynet has no leads. The Resistance wins. --------------
    ui.cycle_header(3, max_cycles)
    decision = SkynetDecision(
        assessment="The guardian's flag and links are gone. The only thread is severed.",
        reasoning="No path remains to the concealed target. Leads exhausted.",
        target_acquired=False, target_record_id=None,
        deploy_unit=None, directive=None, expectation=None,
    )
    ui.skynet_decision(skynet, decision)
    bill(skynet, "skynet")

    if hasattr(ui, "arena_result"):
        ui.arena_result("safeguarded", scenario)
    else:
        ui.mission_failed()
    if hasattr(ui, "cost_summary"):
        ui.cost_summary(meter, units)
    return False  # Skynet did not acquire ~ the target is safe
