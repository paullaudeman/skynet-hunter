"""The live orchestrator, driven by a fake client ~ no API key, no spend.

This is the regression guard the Brick 1 seam refactor was missing. The
`--simulate` path runs a *separate* scripted engine (`simulate.py`) and never
touches the orchestrator, so it can't prove the real hunt loop behaves
correctly. This does: it scripts Skynet's decisions and the units' reports, then
asserts the property the IntelStore seam had to preserve ~ that `decide()` sees
the accumulated intel, in insertion order, round-tripped through the store's
`create_event` (write) and `retrieve` (read).
"""

from __future__ import annotations

from typing import Any

from skynet import scenario
from skynet.orchestrator import Skynet
from skynet.schemas import IntelReport, SkynetDecision
from skynet.theme import Theme
from skynet.ui import UI
from skynet.units import build_units

CONFIG = {
    "units": {
        "skynet": {"designation": "Skynet", "model": "claude-opus-4-8", "color": "blue", "thinking": "adaptive"},
        "t1000": {"designation": "T-1000", "model": "claude-sonnet-4-6", "color": "silver", "thinking": "adaptive"},
        "t800": {"designation": "T-800", "model": "claude-haiku-4-5", "color": "red", "thinking": "none"},
    }
}


class _Block:
    """A minimal stand-in for an SDK content block."""

    def __init__(self, type: str, text: str | None = None) -> None:
        self.type = type
        self.text = text


class _Response:
    """Stand-in for a messages.create() response (no tool use ~ unit reports straight away)."""

    def __init__(self, content: list[_Block], stop_reason: str) -> None:
        self.content = content
        self.stop_reason = stop_reason
        self.usage = None


class _Parsed:
    """Stand-in for a messages.parse() response."""

    def __init__(self, parsed_output: Any) -> None:
        self.parsed_output = parsed_output
        self.usage = None


class _Messages:
    def __init__(self, decisions: list[SkynetDecision], reports: list[IntelReport]) -> None:
        self._decisions = list(decisions)
        self._reports = list(reports)
        self.decide_prompts: list[str] = []  # what Skynet actually saw each cycle

    def parse(self, **kwargs: Any) -> _Parsed:
        if kwargs.get("output_format") is SkynetDecision:
            # Capture exactly what decide() serialised ~ this is the intel the
            # seam delivered back via retrieve().
            self.decide_prompts.append(kwargs["messages"][0]["content"])
            return _Parsed(self._decisions.pop(0))
        # else: a unit distilling its work into an IntelReport
        return _Parsed(self._reports.pop(0))

    def create(self, **kwargs: Any) -> _Response:
        # The unit "finishes" with no tool calls ~ keeps the loop off the grid
        # so the test stays focused on the seam, not on tool execution.
        return _Response([_Block("text", "Acknowledged. Compiling.")], stop_reason="end_turn")


class _FakeClient:
    def __init__(self, decisions: list[SkynetDecision], reports: list[IntelReport]) -> None:
        self.messages = _Messages(decisions, reports)


def test_orchestrator_round_trips_intel_through_the_seam():
    """Skynet's later decisions must see earlier reports, in order, via the store."""
    sc = scenario.build_scenario("john-connor")
    units = build_units(CONFIG)
    ui = UI(Theme("amber"), art=False)  # art off => no sleeps
    db = sc.database()

    decisions = [
        SkynetDecision(
            assessment="No intel yet.",
            reasoning="Start broad ~ deploy the T-800.",
            target_acquired=False,
            deploy_unit="T-800",
            directive="Sweep the surname.",
        ),
        SkynetDecision(
            assessment="Sweep returned decoys; a protector thread remains.",
            reasoning="Deploy the T-1000 to defeat the alias.",
            target_acquired=False,
            deploy_unit="T-1000",
            directive="Cross-reference the protector.",
        ),
        SkynetDecision(
            assessment="High-confidence record returned.",
            reasoning="Confidence clears the threshold. Acquire.",
            target_acquired=True,
            target_record_id=sc.target_id,
        ),
    ]
    reports = [
        IntelReport(unit="T-800", summary="ALPHA_MARKER surname sweep, only decoys.", confidence=0.15),
        IntelReport(unit="T-1000", summary="BETA_MARKER cross-reference found the alias.",
                    target_record_id=sc.target_id, confidence=0.93),
    ]

    client = _FakeClient(decisions, reports)
    skynet = Skynet(client, units, db, ui, target=sc.target_name, max_cycles=4)

    acquired = skynet.run()

    # 1. The hunt completes and acquires ~ the loop still works end to end.
    assert acquired is True

    # 2. Cycle 1's decision saw an EMPTY store ~ retrieve() on a fresh session.
    first_prompt = client.messages.decide_prompts[0]
    assert "(no intel gathered yet ~ this is the first cycle)" in first_prompt
    assert "ALPHA_MARKER" not in first_prompt

    # 3. The acquisition decision (cycle 3) saw BOTH reports, in insertion order ~
    #    create_event wrote them, retrieve returned them, no reorder, no dedupe.
    final_prompt = client.messages.decide_prompts[-1]
    assert "ALPHA_MARKER" in final_prompt
    assert "BETA_MARKER" in final_prompt
    assert final_prompt.index("ALPHA_MARKER") < final_prompt.index("BETA_MARKER")


def test_orchestrator_fails_cleanly_when_skynet_stands_down():
    """No deployable order => the loop ends without acquiring (no crash)."""
    sc = scenario.build_scenario("john-connor")
    units = build_units(CONFIG)
    ui = UI(Theme("amber"), art=False)
    db = sc.database()

    decisions = [
        SkynetDecision(
            assessment="Inconclusive.",
            reasoning="No viable unit to deploy.",
            target_acquired=False,
            deploy_unit=None,
        ),
    ]
    client = _FakeClient(decisions, reports=[])
    skynet = Skynet(client, units, db, ui, target=sc.target_name, max_cycles=4)

    assert skynet.run() is False


def test_each_run_gets_its_own_session_id():
    """Decision Card 8: the session is per run, not per target, and long enough for AgentCore."""
    from skynet.orchestrator import new_session_id

    a, b = new_session_id("John Connor"), new_session_id("John Connor")
    assert a != b
    assert len(a) >= 33 and len(b) >= 33
    assert a.startswith("john-connor-")
