"""Run a hunt on AgentCore Runtime and replay it in this terminal.

    python -m skynet --runtime <agent-runtime-arn> --aws-region us-east-1 [--scenario ...] [--seed N]

The runtime returns the hunt's UI calls as events (agentcore_app.run_hunt). Replaying them through the
local UI prints exactly what a local run prints; only the place it ran is different.
"""

from __future__ import annotations

import json
import uuid
from types import SimpleNamespace
from typing import Any

from .schemas import IntelReport, SkynetDecision


def invoke(arn: str, region: str, payload: dict[str, Any], client: Any = None) -> dict[str, Any]:
    if client is None:
        import boto3
        from botocore.config import Config
        # a hunt takes minutes; boto3's default 60 s read timeout would abandon it mid-run (and retry it)
        client = boto3.client("bedrock-agentcore", region_name=region,
                              config=Config(read_timeout=900, retries={"max_attempts": 1}))
    resp = client.invoke_agent_runtime(
        agentRuntimeArn=arn,
        runtimeSessionId=f"skynet-hunt-{uuid.uuid4()}",   # 48 chars: AgentCore wants 33+
        payload=json.dumps(payload).encode(),
        qualifier="DEFAULT",
    )
    body = resp["response"]
    raw = body.read() if hasattr(body, "read") else b"".join(body)
    return json.loads(raw)


class _Meter:
    """Enough of a CostMeter for ui.cost_summary: rows(), total_cost, estimated."""

    def __init__(self, d: dict[str, Any]) -> None:
        self.total_cost = d.get("total_cost", 0.0)
        self.estimated = d.get("estimated", False)
        self._rows = [SimpleNamespace(**r) for r in d.get("rows", [])]

    def rows(self) -> list[Any]:
        return self._rows


def _unit(d: Any, units: dict[str, Any]) -> Any:
    if isinstance(d, dict) and {"key", "designation", "model"} <= set(d):
        return units.get(d["key"]) or SimpleNamespace(color="silver", **d)
    return d


def replay(result: dict[str, Any], ui: Any, units: dict[str, Any]) -> None:
    for e in result.get("events", []):
        name, args, kwargs = e["event"], list(e.get("args", [])), dict(e.get("kwargs", {}))
        args = [_unit(a, units) for a in args]
        if name in ("skynet_decision", "target_acquired") and len(args) > 1 and isinstance(args[1], dict):
            args[1] = SkynetDecision(**args[1])
        elif name == "intel_report" and len(args) > 1 and isinstance(args[1], dict):
            args[1] = IntelReport(**args[1])
        elif name == "cost_summary":
            args = [_Meter(args[0]), units]
        fn = getattr(ui, name, None)
        if callable(fn):
            fn(*args, **kwargs)
