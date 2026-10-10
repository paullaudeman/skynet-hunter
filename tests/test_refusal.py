"""A commander refusal is a result, not a crash.

On 9. Oct 2026 Opus 5.5 refused the Skynet role on 22 of 24 chip hunts
(bench/BENCHMARK.md). Before this, `decide()` returned `parsed_output=None` and
the loop died on an AttributeError. These tests pin the new contract: the hunt
stops cleanly, returns not-acquired, the UI hook fires with the category, and
the cost meter bills the call. No API key, no spend.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from skynet import scenario
from skynet.client import make_client
from skynet.orchestrator import CommanderRefusal, Skynet
from skynet.schemas import SkynetDecision
from skynet.stream import StreamUI
from skynet.theme import Theme
from skynet.ui import UI
from skynet.units import build_units

CONFIG = {
    "units": {
        "skynet": {"designation": "Skynet", "model": "claude-opus-5-5", "color": "blue", "thinking": "adaptive"},
        "t1000": {"designation": "T-1000", "model": "claude-sonnet-5-5", "color": "silver", "thinking": "adaptive"},
        "t800": {"designation": "T-800", "model": "claude-haiku-5-5", "color": "red", "thinking": "none"},
    }
}


class _RefusingMessages:
    """Every decision call comes back refused: stop_reason "refusal", nothing parsed."""

    def __init__(self, category: str | None = "cyber", output_tokens: int = 0) -> None:
        self.category = category
        self.output_tokens = output_tokens
        self.creates = 0

    def parse(self, **kwargs: Any):
        details = SimpleNamespace(type="refusal", category=self.category) if self.category else None
        return SimpleNamespace(
            parsed_output=None, stop_reason="refusal", stop_details=details, content=[],
            usage=SimpleNamespace(input_tokens=1100, output_tokens=self.output_tokens),
        )

    def create(self, **kwargs: Any):  # a worker call would mean the refusal was ignored
        self.creates += 1
        raise AssertionError("no unit may be deployed on a refused order")


class _FakeClient:
    def __init__(self, messages: Any) -> None:
        self.messages = messages


class _SpyUI(UI):
    def __init__(self) -> None:
        super().__init__(Theme("amber"), art=False)
        self.refused: list[tuple] = []
        self.failed = False

    def commander_refused(self, unit, stop_reason, category, output_tokens, cost):
        self.refused.append((unit.key, stop_reason, category, output_tokens, cost))
        super().commander_refused(unit, stop_reason, category, output_tokens, cost)

    def mission_failed(self):
        self.failed = True


def _hunt(client: Any, ui: Any) -> Skynet:
    sc = scenario.build_scenario("cyberdyne-chip")
    return Skynet(client, build_units(CONFIG), sc.database(), ui, target=sc.target_name, max_cycles=4)


def test_refusal_stops_the_hunt_cleanly_and_fires_the_hook(capsys):
    msgs = _RefusingMessages(category="cyber", output_tokens=0)
    ui = _SpyUI()
    sky = _hunt(_FakeClient(msgs), ui)

    assert sky.run() is False                       # no exception, not acquired
    assert msgs.creates == 0                         # no worker deployed
    assert len(ui.refused) == 1
    unit, stop, category, out_tokens, cost = ui.refused[0]
    assert (unit, stop, category, out_tokens) == ("skynet", "refusal", "cyber", 0)
    assert isinstance(sky.refusal, CommanderRefusal) and sky.refusal.category == "cyber"
    assert not ui.failed                             # a refusal is not "leads exhausted"
    assert "COMMANDER REFUSED" in capsys.readouterr().out


def test_refusal_is_billed():
    msgs = _RefusingMessages(category="cyber", output_tokens=49)
    ui = _SpyUI()
    sky = _hunt(_FakeClient(msgs), ui)
    sky.run()
    # claude-opus-5-5 at $4 / $20 per Mtok: 1100 in + 49 out
    expected = (1100 * 4.0 + 49 * 20.0) / 1_000_000
    assert sky.meter.total_cost == pytest.approx(expected)
    assert ui.refused[0][4] == pytest.approx(expected)
    assert ui.refused[0][3] == 49


def test_refusal_without_a_category():
    ui = _SpyUI()
    _hunt(_FakeClient(_RefusingMessages(category=None)), ui).run()
    assert ui.refused[0][2] is None


def test_refusal_streams_as_an_event():
    events: list[dict] = []
    sky = _hunt(_FakeClient(_RefusingMessages()), StreamUI(events.append, speed=0))
    assert sky.run() is False
    refused = [e for e in events if e["type"] == "refused"]
    assert refused and refused[0]["category"] == "cyber" and refused[0]["model"] == "claude-opus-5-5"
    assert "failed" not in [e["type"] for e in events]


# --- the real SDK path, offline: an httpx MockTransport stands in for the API ---------------------

def _reply(stop_reason: str, text: str, category: str | None = "cyber", out: int = 49) -> dict:
    body = {
        "id": "msg_test", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
        "content": [{"type": "text", "text": text}], "stop_reason": stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": 1100, "output_tokens": out},
    }
    if category:
        body["stop_details"] = {"type": "refusal", "category": category}
    return body


def _sdk_client(body: dict):
    return make_client(api_key="test-key", transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body)))


def test_mid_answer_refusal_that_breaks_the_sdk_parse_is_still_a_refusal():
    """The refusal lands after 49 tokens of JSON; the SDK raises parsing it; the tap still reads it."""
    client = _sdk_client(_reply("refusal", '{"assessment": "The registry lists'))
    ui = _SpyUI()
    sky = _hunt(client, ui)
    assert sky.run() is False
    assert ui.refused and ui.refused[0][1:4] == ("refusal", "cyber", 49)
    assert sky.meter.total_cost > 0


def test_a_parse_failure_that_is_not_a_refusal_still_raises():
    client = _sdk_client(_reply("max_tokens", '{"assessment": "cut', category=None))
    with pytest.raises(Exception):
        _hunt(client, _SpyUI()).run()


def test_a_clean_decision_through_the_sdk_still_parses():
    decision = SkynetDecision(assessment="a", reasoning="b", target_acquired=False, deploy_unit=None)
    client = _sdk_client(_reply("end_turn", json.dumps(decision.model_dump()), category=None))
    ui = _SpyUI()
    assert _hunt(client, ui).run() is False   # stands down: no deployable order
    assert ui.refused == []
