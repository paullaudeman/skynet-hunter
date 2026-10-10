"""Phase 1: the hunt on AgentCore Runtime with Bedrock models. Fake clients only; nothing calls AWS."""

from __future__ import annotations

from typing import Any

from skynet import scenario
from skynet.agentcore_app import MAX_CYCLES_CAP, run_hunt
from skynet.cost import base_model, cost_for
from skynet.runtime_client import replay
from skynet.schemas import IntelReport, SkynetDecision
from skynet.units import build_units
from tests.test_orchestrator import CONFIG, _FakeClient

CFG = {"mission": {"max_cycles": 4}, **CONFIG}


def _client(sc):
    return _FakeClient(
        [SkynetDecision(assessment="a", reasoning="b", target_acquired=False, deploy_unit="T-1000", directive="go"),
         SkynetDecision(assessment="a", reasoning="b", target_acquired=True, target_record_id=sc.target_id)],
        [IntelReport(unit="T-1000", summary="found it", target_record_id=sc.target_id, confidence=0.93)])


def test_run_hunt_returns_outcome_events_and_evidence(tmp_path):
    sc = scenario.build_scenario("cyberdyne-chip")
    out = run_hunt({"scenario": "cyberdyne-chip", "archive": False}, session_id="s" * 40,
                   client=_client(sc), config=CFG, runs_root=str(tmp_path))
    assert out["outcome"] == "acquired" and out["session_id"] == "s" * 40
    names = [e["event"] for e in out["events"]]
    assert names[0] == "mission_briefing" and "target_acquired" in names and "cost_summary" in names
    assert out["summary"]["mode"] == "agentcore-runtime" and out["summary"]["outcome"] == "acquired"


def test_short_session_ids_are_replaced(tmp_path):
    sc = scenario.build_scenario("cyberdyne-chip")
    out = run_hunt({"archive": False}, session_id="short", client=_client(sc), config=CFG, runs_root=str(tmp_path))
    assert len(out["session_id"]) >= 33


def test_payload_cannot_raise_the_cycle_ceiling(tmp_path):
    sc = scenario.build_scenario("cyberdyne-chip")
    out = run_hunt({"archive": False, "max_cycles": 999}, client=_client(sc), config=CFG, runs_root=str(tmp_path))
    first = next(e for e in out["events"] if e["event"] == "cycle_header")
    assert first["args"][1] == MAX_CYCLES_CAP


def test_unknown_scenario_is_an_error_not_a_crash(tmp_path):
    assert "error" in run_hunt({"scenario": "skynet"}, config=CFG, runs_root=str(tmp_path))


class _Calls:
    """A UI that records which methods were called with which (simplified) arguments."""

    def __init__(self):
        self.calls: list[tuple] = []

    def __getattr__(self, name):
        def f(*a, **k):
            self.calls.append((name, tuple(getattr(x, "key", None) or type(x).__name__ for x in a)))
        return f


def test_replay_makes_the_same_ui_calls_as_a_local_run(tmp_path):
    from skynet.evidence import EvidenceRecorder, RecordingUI
    from skynet.orchestrator import Skynet
    sc = scenario.build_scenario("cyberdyne-chip")
    units = build_units(CFG)
    direct = _Calls()
    Skynet(_client(sc), units, sc.database(), direct, sc.target_name, 4, profile=sc.profile).run()
    out = run_hunt({"archive": False}, client=_client(sc), config=CFG, runs_root=str(tmp_path))
    replayed = _Calls()
    replay(out, replayed, units)
    # same methods, same order, and units resolve back to the same roster keys
    assert [c[0] for c in replayed.calls] == [c[0] for c in direct.calls]
    assert [c for c in replayed.calls if c[0] == "deploy"] == [c for c in direct.calls if c[0] == "deploy"]


def test_bedrock_profile_ids_price_like_their_models():
    assert base_model("global.anthropic.claude-opus-4-6-v1") == ("claude-opus-4-6", 1.0)
    assert base_model("us.anthropic.claude-haiku-4-5-20251001-v1:0") == ("claude-haiku-4-5", 1.10)
    assert cost_for("global.anthropic.claude-sonnet-4-6", 1_000_000, 0) == cost_for("claude-sonnet-4-6", 1_000_000, 0)
    assert abs(cost_for("us.anthropic.claude-opus-4-6-v1", 0, 1_000_000) - 27.5) < 1e-9   # $25 x 1.1 regional


def test_bedrock_tap_reads_invoke_replies():
    import httpx
    from skynet.client import make_bedrock_client

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "m", "type": "message", "role": "assistant", "content": [{"type": "text", "text": "ok"}],
                                         "model": "x", "stop_reason": "end_turn", "stop_sequence": None,
                                         "usage": {"input_tokens": 1, "output_tokens": 1}})
    c = make_bedrock_client("us-east-1", transport=httpx.MockTransport(handler),
                            aws_access_key="test", aws_secret_key="test")
    c.messages.create(model="global.anthropic.claude-haiku-4-5-20251001-v1:0", max_tokens=5,
                      messages=[{"role": "user", "content": "hi"}])
    assert c.last_reply and c.last_reply["stop_reason"] == "end_turn"
