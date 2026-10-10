"""The web server's commander picker: allow-listed, threaded to the orchestrator, never paid in tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from test_refusal import _FakeClient, _RefusingMessages

_spec = importlib.util.spec_from_file_location("web_server", Path(__file__).resolve().parent.parent / "web" / "server.py")
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)


def test_allow_list_is_config_plus_anthropic_bench_commanders():
    allowed = server.allowed_commanders()
    assert "claude-opus-5" in allowed               # config.toml
    assert "claude-opus-5-5" in allowed             # benched, selectable (expect a refusal)
    assert "claude-sonnet-5-5" in allowed
    assert not any(m.startswith(("gemini-", "gpt-")) for m in allowed)   # bench only


@pytest.mark.parametrize("bad", ["gpt-6-astra", "gemini-3.8-flash", "claude-made-up", "../../etc"])
def test_run_hunt_rejects_a_commander_off_the_list(bad):
    with pytest.raises(ValueError):
        server.run_hunt(lambda ev: None, engine="claude", commander=bad, client_factory=lambda: None)


def test_live_hunt_runs_on_the_picked_commander_and_streams_the_refusal():
    events: list[dict] = []
    seen: list[str] = []

    class _Watching(_RefusingMessages):
        def parse(self, **kw):
            seen.append(kw["model"])
            return super().parse(**kw)

    server.run_hunt(events.append, engine="claude", commander="claude-opus-5-5",
                    client_factory=lambda: _FakeClient(_Watching()))
    assert seen == ["claude-opus-5-5"]
    assert {"type": "commander", "model": "claude-opus-5-5"} in events
    refused = [e for e in events if e["type"] == "refused"]
    assert refused and refused[0]["category"] == "cyber"
