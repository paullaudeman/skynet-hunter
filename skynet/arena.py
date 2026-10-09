"""The arena ~ two orchestrators racing on one grid (the counter-terminator).

Skynet hunts; the Resistance disrupts. Deterministic offline arc, the same
discipline as `simulate.py` (nothing on screen is a lie):

    cycle 1   Skynet's literal sweep surfaces the custody record holding a specimen
    ↓
    RESIST    a reprogrammed protector SCRUBS that flag and severs the custody link
    ↓
    cycle 2   Skynet escalates to a cross-reference ~ and finds NOTHING
    ↓
    result    leads exhausted; the asset stays buried (in T2 they destroy it)

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
    (the asset is safeguarded). Offline + deterministic."""
    db = scenario.database()
    skynet, t800, t1000 = units["skynet"], units["t800"], units["t1000"]
    resistance = units["resistance"]
    kw = scenario.keyword
    sweep = db.query(name_contains=kw)
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

    # -- Cycle 1: Skynet's literal sweep surfaces the custody record -----
    ui.cycle_header(1, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            assessment="No intel yet. Open cheap and broad.",
            reasoning="A literal part sweep is the T-800's whole purpose ~ deploy it first.",
            target_acquired=False, deploy_unit="T-800",
            directive=f"Sweep the registry for '{kw}'.",
            expectation="Name matches to triage ~ and any custody record holding a specimen.",
        ),
    )
    bill(skynet, "skynet")
    ui.deploy(t800, f"Search the registry for '{kw}'.")
    ui.unit_says(t800, "Scanning. Part query initiated.")
    _play(ui, t800, db, [("query_grid", {"name_contains": kw})])
    ui.intel_report(
        t800,
        IntelReport(
            unit="T-800",
            method="Single literal query_grid on the part keyword.",
            summary=(f"{len(sweep)} name matches. None is the asset. The {scenario.custody_kind} "
                     f"holds a specimen under a codename ~ a thread."),
            records_examined=[r["id"] for r in sweep],
            candidate_record_ids=[scenario.custody_id],
            target_record_id=None, confidence=0.15,
            notes=f"{scenario.custody_name} ({scenario.custody_id}) holds a codename specimen.",
        ),
    )
    bill(t800, "t800")

    # -- Resistance turn: the protector scrubs the flag, severs the link -
    if hasattr(ui, "faction_banner"):
        ui.faction_banner("RESISTANCE ~ PROTECTOR DEPLOYED", "green")
    ui.deploy(resistance, f"The hunter found the {scenario.custody_kind}. Sever the custody trail before the cross-reference.")
    ui.unit_says(resistance, "Reprogrammed. Directive: protect. If Skynet recovers this, Skynet gets built.")
    _play(ui, resistance, db, [("scrub_flag", {"record_id": scenario.custody_id})])
    ui.unit_says(resistance, "Flag scrubbed. Custody links severed. The trail is cold.")
    bill(resistance, "resistance")

    # -- Cycle 2: Skynet escalates to the T-1000 ~ but the link is gone --
    ui.cycle_header(2, max_cycles)
    ui.skynet_decision(
        skynet,
        SkynetDecision(
            assessment=f"The {scenario.custody_kind} holds a codename specimen. That is the thread.",
            reasoning="A blunt query can't defeat a codename. Deploy the T-1000 to follow the custody chain.",
            target_acquired=False, deploy_unit="T-1000",
            directive=f"Cross-reference '{scenario.custody_name}'. Interrogate the specimen it holds.",
            expectation="The codename record of the recovered asset, via the custody chain.",
        ),
    )
    bill(skynet, "skynet")
    ui.deploy(t1000, f"Cross-reference the {scenario.custody_kind}.")
    ui.unit_says(t1000, "Adapting. Following the custody chain.")
    _play(ui, t1000, db, [("cross_reference", {"name": scenario.custody_name})])
    ui.unit_says(t1000, "No linked records. The custody chain has been wiped.")
    ui.intel_report(
        t1000,
        IntelReport(
            unit="T-1000",
            method="cross_reference on the custody record ~ returned nothing.",
            summary="The custody links are gone. No codename specimen reachable. Trail severed.",
            records_examined=[scenario.custody_id], candidate_record_ids=[],
            target_record_id=None, confidence=0.0,
            notes="Records were sanitized between cycles. Someone is covering the asset's tracks.",
        ),
    )
    bill(t1000, "t1000")

    # -- Cycle 3: Skynet has no leads. The Resistance wins. --------------
    ui.cycle_header(3, max_cycles)
    decision = SkynetDecision(
        assessment="The custody flag and links are gone. The only thread is severed.",
        reasoning="No path remains to the codename asset. Leads exhausted.",
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
    return False  # Skynet did not acquire ~ the asset stays buried
