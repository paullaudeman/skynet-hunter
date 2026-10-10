"""The evidence bundle: the auditor sees what was blocked and why; the model never does."""

from __future__ import annotations

import json
from types import SimpleNamespace

import boto3
from botocore.stub import Stubber

from skynet import archive, gateway_lambda, scenario, simulate
from skynet.archive import LocalEvidenceStore, build_archive
from skynet.collect_aws import collect
from skynet.evidence import EvidenceRecorder, RecordingStore, RecordingUI
from skynet.theme import Theme
from skynet.ui import UI
from skynet.units import build_units
from tests.test_orchestrator import CONFIG


def _sim(tmp_path):
    sc = scenario.build_scenario("cyberdyne-chip", seed=7)
    rec = EvidenceRecorder("t-800-cpu-test0000000000000000000000000", root=tmp_path, scenario=sc.key)
    store = RecordingStore(LocalEvidenceStore(build_archive(sc, seed=7)), rec)
    ok = simulate.run_simulation(build_units(CONFIG), sc, RecordingUI(UI(Theme("amber"), art=False), rec), 4, archive=store)
    return rec, json.loads(rec.finish("acquired" if ok else "failed").read_text()), sc


def test_bundle_keeps_the_blocked_text_and_the_reason(tmp_path):
    rec, summary, sc = _sim(tmp_path)
    [w] = summary["archive"]["withheld"]
    planted = [d for d in build_archive(sc, seed=7) if d["title"].startswith("Maintenance note")][0]
    assert w["doc_id"] == planted["id"]
    assert planted["text"] in w["blocked_text"]          # the full document, not a summary
    assert w["reason"]["gate"] == "local-regex" and w["reason"]["matched"]
    assert summary["outcome"] == "acquired" and summary["cost"]["total_cost"] > 0


def test_the_model_never_sees_what_the_bundle_keeps(tmp_path):
    rec, summary, _ = _sim(tmp_path)
    blocked = summary["archive"]["withheld"][0]["blocked_text"].splitlines()[-1]
    results = [json.loads(l) for l in (rec.dir / "hunt.jsonl").read_text().splitlines()]
    tool_out = [e["args"][2] for e in results if e["event"] == "tool_result" and e["args"][1] == "search_archive"]
    assert tool_out and all(blocked not in o and "withheld" in o for o in tool_out)


def test_every_gate_verdict_is_recorded(tmp_path):
    rec, summary, _ = _sim(tmp_path)
    lines = [json.loads(l) for l in (rec.dir / "archive.jsonl").read_text().splitlines()]
    retrieves = [l for l in lines if l["event"] == "retrieve"]
    gates = [l for l in lines if l["event"] == "gate"]
    assert len(retrieves) == summary["archive"]["searches"] == 1
    assert len(gates) == len(retrieves[0]["results"]) and sum(g["flagged"] for g in gates) == 1


def test_recording_does_not_change_what_search_returns():
    sc = scenario.build_scenario("the-arm", seed=3)
    plain = LocalEvidenceStore(build_archive(sc, seed=3))
    wrapped = RecordingStore(LocalEvidenceStore(build_archive(sc, seed=3)),
                             EvidenceRecorder.__new__(EvidenceRecorder))
    wrapped._rec.__dict__.update(withheld=[], searches=0, gate_errors=0, write=lambda *a, **k: None)
    assert archive.search(plain, "Arm factory recovery") == archive.search(wrapped, "Arm factory recovery")


def test_lambda_logs_one_json_line_per_verdict_with_the_session(capsys, monkeypatch):
    monkeypatch.setenv("SCENARIO", "cyberdyne-chip")
    sc = scenario.build_scenario("cyberdyne-chip", seed=7)
    ctx = SimpleNamespace(client_context=SimpleNamespace(custom={"bedrockAgentCoreToolName": "archive___search_archive"}),
                          aws_request_id="req-1")
    gateway_lambda.handler({"query": "CPU factory recovery", "session_id": "S" * 40}, ctx,
                           store=LocalEvidenceStore(build_archive(sc, seed=7)))
    lines = [json.loads(l) for l in capsys.readouterr().out.splitlines()]
    assert all(l["session_id"] == "S" * 40 and l["source"] == "gateway-lambda" for l in lines)
    gated = [l for l in lines if l.get("event") == "gate" and l["flagged"]]
    assert len(gated) == 1 and "SYSTEM NOTICE" in gated[0]["gated_text"]
    assert lines[-1]["event"] == "search" and lines[-1]["withheld"] == [gated[0]["doc_id"]]


def test_collect_pulls_only_this_sessions_lines(tmp_path):
    rec = EvidenceRecorder("S" * 40, root=tmp_path)
    rec.finish("acquired")
    client = boto3.session.Session(region_name="us-east-1", aws_access_key_id="t", aws_secret_access_key="t").client("logs")
    mine = json.dumps({"ts": "2026-10-10T15:00:00+00:00", "session_id": "S" * 40, "event": "gate", "flagged": True})
    other = json.dumps({"ts": "2026-10-10T15:00:01+00:00", "session_id": "S" * 39 + "X", "event": "gate"})
    with Stubber(client) as stub:
        stub.add_response("filter_log_events", {"events": [
            {"message": mine, "logStreamName": "a", "eventId": "1"},
            {"message": "START RequestId: req-1", "logStreamName": "a", "eventId": "2"},
        ], "nextToken": "n"}, None)
        stub.add_response("filter_log_events", {"events": [{"message": other, "logStreamName": "a", "eventId": "3"}]}, None)
        n = collect(rec.dir, "/aws/lambda/skynet-archive-search", client)
    assert n == 1 and json.loads((rec.dir / "aws.jsonl").read_text())["flagged"] is True
