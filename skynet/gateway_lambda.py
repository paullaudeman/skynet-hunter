"""AgentCore Gateway Lambda target: `search_archive` as an MCP tool.

Gateway calls this Lambda with the tool's arguments as the event and names the
tool in the client context as `<target>___<tool>`. Verify both on the first
deploy: they are read against the AWS docs, not observed.

Config comes from the environment Terraform sets: KB_ID, SCENARIO (the default),
GUARDRAIL_ID, GUARDRAIL_VERSION, AWS_REGION. A call may name its own `scenario`;
the KB holds all four and filters per call. The handler dispatches by tool name,
so the grid tools can join this target later without a second Lambda.

Every call logs one JSON line per retrieval and per gate verdict (evidence.LogRecorder),
including the full text of anything withheld and why, tagged with the caller's
`session_id` (or the Lambda request id when there is none). collect_aws.py pulls them
back into the run's evidence bundle.

Errors come back as `{"error": ...}` results, the same convention as the grid
tools, so the model reads them as tool output rather than a failed call.
"""

from __future__ import annotations

import os
from typing import Any

from . import archive
from .archive import LocalGate, UnionGate
from .evidence import LogRecorder, RecordingStore
from .archive_aws import BedrockGuardrailGate, BedrockKBEvidenceStore
from .scenario import TEMPLATES

_STORES: dict[str, BedrockKBEvidenceStore] = {}  # one per scenario, reused across warm invocations
_GATE: UnionGate | None = None


def _store(scenario_key: str) -> BedrockKBEvidenceStore:
    global _GATE
    if scenario_key not in _STORES:
        region = os.environ["AWS_REGION"]
        if _GATE is None:
            # both gates, withhold on either (probe, 10. Oct 2026: they miss different attacks)
            _GATE = UnionGate([LocalGate(), BedrockGuardrailGate(os.environ["GUARDRAIL_ID"], os.environ["GUARDRAIL_VERSION"], region)])
        _STORES[scenario_key] = BedrockKBEvidenceStore(os.environ["KB_ID"], scenario_key, region, gate=_GATE,
                                                       min_score=float(os.environ.get("MIN_SCORE", "0.60")))
    return _STORES[scenario_key]


def tool_name(context: Any) -> str:
    custom = getattr(getattr(context, "client_context", None), "custom", None) or {}
    full = custom.get("bedrockAgentCoreToolName", "")
    return full.split("___", 1)[-1]


def handler(event: dict[str, Any], context: Any, store: Any = None) -> dict[str, Any]:
    name = tool_name(context)
    if name != "search_archive":
        return {"error": f"Unknown tool {name!r}."}
    query = str(event.get("query") or "").strip()
    if not query:
        return {"error": "query is required."}
    # no silent default: an empty scenario is refused, never searched unfiltered
    scenario_key = str(event.get("scenario") or os.environ.get("SCENARIO") or "")
    if scenario_key not in TEMPLATES:
        return {"error": f"Unknown scenario {scenario_key!r}. One of: {', '.join(TEMPLATES)}."}
    session = str(event.get("session_id") or getattr(context, "aws_request_id", "") or "no-session")
    rec = LogRecorder(session, source="gateway-lambda", tool=name, scenario=scenario_key)
    out = archive.search(RecordingStore(store or _store(scenario_key), rec), query, archive._top_k(event.get("top_k")))
    rec.write("summary", event="search", query=query, returned=len(out["results"]),
              withheld=[w["doc_id"] for w in rec.withheld], gate_fault=out.get("gate_fault"))
    return out
