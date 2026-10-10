"""The hunt on Amazon Bedrock AgentCore Runtime (Phase 1).

    POST /invocations  {"scenario": "cyberdyne-chip", "seed": null, "max_cycles": 4, "archive": true}
      -> {"session_id", "outcome", "summary", "events"}

The orchestrator is unchanged. What moves to AWS is where it runs (an AgentCore Runtime microVM, one
per session) and where its models are (Bedrock inference profiles, `config.bedrock.toml`). The hunt's
UI calls are recorded as events (evidence.RecordingUI over a silent StreamUI) and returned, so the
local CLI can replay a cloud run in the same terminal (`python -m skynet --runtime <arn>`).

Every run writes its evidence bundle in the microVM and returns its summary: outcome, cost, and every
withheld document with the gate's reason. The archive is the deployed Knowledge Base, gated by the
regex and Bedrock Guardrails together, when KB_ID is set in the runtime's environment.

Config comes from the environment (set by infra/runtime): AWS_REGION, KB_ID, GUARDRAIL_ID,
GUARDRAIL_VERSION, MIN_SCORE, SKYNET_REGION. Credentials are the runtime's execution role.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from . import scenario as scenario_mod
from .archive import LocalGate, UnionGate
from .evidence import EvidenceRecorder, RecordingStore, RecordingUI
from .orchestrator import Skynet, new_session_id
from .stream import StreamUI
from .units import build_units

try:  # stdlib on 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

CONFIG = Path(__file__).resolve().parent.parent / "config.bedrock.toml"
MAX_CYCLES_CAP = 6  # the spend ceiling per invocation: a payload cannot ask for more


def _store(sc: Any, region: str) -> Any:
    kb = os.environ.get("KB_ID")
    if not kb:
        return None
    from .archive_aws import BedrockGuardrailGate, BedrockKBEvidenceStore
    gate: Any = LocalGate()
    if os.environ.get("GUARDRAIL_ID"):
        gate = UnionGate([LocalGate(), BedrockGuardrailGate(os.environ["GUARDRAIL_ID"], os.environ.get("GUARDRAIL_VERSION", "1"), region)])
    return BedrockKBEvidenceStore(kb, sc.key, region, gate=gate, min_score=float(os.environ.get("MIN_SCORE", "0.60")))


def run_hunt(payload: dict[str, Any], session_id: str | None = None, client: Any = None,
             store: Any = None, config: dict[str, Any] | None = None, runs_root: str = "/tmp/runs") -> dict[str, Any]:
    """One hunt, start to finish. Injectable client and store so tests never touch AWS."""
    region = os.environ.get("SKYNET_REGION") or os.environ.get("AWS_REGION") or "us-east-1"
    config = config or tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    key = payload.get("scenario") or "cyberdyne-chip"
    if key != "random" and key not in scenario_mod.TEMPLATES:
        return {"error": f"Unknown scenario {key!r}. One of: {', '.join(scenario_mod.SCENARIO_CHOICES)}."}
    sc = scenario_mod.build_scenario(key, seed=payload.get("seed"))
    units = build_units(config)
    max_cycles = max(1, min(int(payload.get("max_cycles") or config["mission"]["max_cycles"]), MAX_CYCLES_CAP))
    sid = session_id if session_id and len(session_id) >= 33 else new_session_id(sc.target_name)

    if client is None:
        from .client import make_bedrock_client
        client = make_bedrock_client(region)
    if store is None and payload.get("archive", True):
        store = _store(sc, region)

    rec = EvidenceRecorder(sid, root=runs_root, mode="agentcore-runtime", scenario=sc.key,
                           seed=payload.get("seed"), target=sc.target_name, target_id=sc.target_id, region=region,
                           models={k: u.model for k, u in units.items()},
                           archive=None if store is None else type(store).__name__)
    ui = RecordingUI(StreamUI(lambda e: None, speed=0), rec)
    if store is not None:
        store = RecordingStore(store, rec)

    skynet = Skynet(client, units, sc.database(), ui, sc.target_name, max_cycles,
                    profile=sc.profile, session_id=sid, archive=store)
    acquired, error = False, None
    try:
        acquired = skynet.run()
    except Exception as e:  # a crashed run still returns its evidence
        error = f"{type(e).__name__}: {e}"
    finally:
        outcome = "acquired" if acquired else ("refused" if skynet.refusal else ("error" if error else "failed"))
        if rec.cost is None:
            rec.cost = {"total_cost": round(skynet.meter.total_cost, 6), "estimated": skynet.meter.estimated}
        summary = json.loads(rec.finish(outcome, refusal=skynet.refusal, error=error).read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (rec.dir / "hunt.jsonl").read_text(encoding="utf-8").splitlines()]
    return {"session_id": sid, "outcome": outcome, "summary": summary, "events": events}


def build_app() -> Any:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    app = BedrockAgentCoreApp()

    @app.entrypoint
    def invoke(payload: dict[str, Any], context: Any = None) -> dict[str, Any]:
        return run_hunt(payload or {}, session_id=getattr(context, "session_id", None))

    return app
