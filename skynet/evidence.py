"""The evidence bundle ~ what a run did, and why, kept after it ends.

    runs/<session_id>/
      hunt.jsonl      every engine event in order: decisions, deploys, tool calls, full tool results
      archive.jsonl   every retrieval (query, doc ids, scores, full text) and every gate verdict
                      (flagged or not, the exact text the gate saw, and its reason)
      aws.jsonl       Lambda log lines for this session, pulled after the run (collect_aws.py)
      summary.json    outcome, timing, cost, what was withheld and why

The bundle is the auditor's view: a withheld document is stored here in full, with
the gate's reason, even though the model only ever saw "[withheld]". Nothing in this
module changes what the model sees or what the screen shows; it only wraps and records.

Synthetic data only. Before real data enters, the classification gate in DESIGN 9.2
decides whether blocked text may be stored at all (a blocked document can be the most
sensitive one in the set).
"""

from __future__ import annotations

import dataclasses
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .archive import LocalGate

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _plain(o: Any) -> Any:
    """Make an engine object JSON-safe without losing what matters for the record."""
    if hasattr(o, "model_dump"):
        return o.model_dump()
    if hasattr(o, "designation") and hasattr(o, "model"):  # a Unit: who, not the persona text
        return {"key": getattr(o, "key", None), "designation": o.designation, "model": o.model}
    if hasattr(o, "total_cost") and hasattr(o, "rows"):  # a CostMeter
        return {"total_cost": round(o.total_cost, 6), "estimated": o.estimated,
                "rows": [dataclasses.asdict(r) for r in o.rows()]}
    if dataclasses.is_dataclass(o) and not isinstance(o, type):
        return dataclasses.asdict(o)
    if isinstance(o, dict):
        return {str(k): _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(v) for v in o]
    if isinstance(o, (str, int, float, bool)) or o is None:
        return o
    return str(o)


class EvidenceRecorder:
    def __init__(self, session_id: str, root: Path | str = RUNS_DIR, **context: Any) -> None:
        self.session_id = session_id
        self.dir = Path(root) / session_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.started = _now()
        self._t0 = time.monotonic()
        self.context = context
        self.withheld: list[dict[str, Any]] = []
        self.searches = 0
        self.gate_errors = 0
        self.cost: dict[str, Any] | None = None

    def write(self, stream: str, **event: Any) -> None:
        line = {"ts": _now(), "session_id": self.session_id, **_plain(event)}
        with (self.dir / f"{stream}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    def _acquired_id(self) -> str | None:
        """The record id the hunt declared acquired, read back from its own event log."""
        f = self.dir / "hunt.jsonl"
        if not f.exists():
            return None
        found = None
        for line in f.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            if e.get("event") == "target_acquired" and e.get("args"):
                found = (e["args"][0] or {}).get("id")
        return found

    def finish(self, outcome: str, **extra: Any) -> Path:
        # Ground truth exists in a synthetic scenario: say whether "acquired" was the right record.
        # A commander can declare the wrong one with full confidence (10. Oct 2026, Opus 4.6 on Bedrock).
        truth = self.context.get("target_id")
        if truth and outcome == "acquired":
            got = self._acquired_id()
            extra = {"acquired_id": got, "correct": got == truth, **extra}
        summary = {
            "session_id": self.session_id, "outcome": outcome,
            "started": self.started, "ended": _now(),
            "wall_s": round(time.monotonic() - self._t0, 2),
            **_plain(self.context), "cost": self.cost,
            "archive": {"searches": self.searches, "withheld": self.withheld, "gate_errors": self.gate_errors},
            **_plain(extra),
        }
        path = self.dir / "summary.json"
        path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path


class LogRecorder(EvidenceRecorder):
    """For the Lambda: the same records, one JSON line each on stdout, which CloudWatch
    Logs keeps. `collect_aws.py` pulls them back into the run's bundle by session_id."""

    def __init__(self, session_id: str, **context: Any) -> None:  # no directory
        self.session_id = session_id
        self.context = context
        self.withheld, self.searches, self.gate_errors, self.cost = [], 0, 0, None

    def write(self, stream: str, **event: Any) -> None:
        print(json.dumps({"ts": _now(), "session_id": self.session_id, "stream": stream,
                          **_plain(event), **_plain(self.context)}, ensure_ascii=False))


class RecordingUI:
    """Wraps any `ui`: records each call to hunt.jsonl, then forwards it unchanged.

    `hasattr(ui, "cost_tick")` still answers for the wrapped UI, so the engine's
    optional hooks behave exactly as they did.
    """

    def __init__(self, inner: Any, rec: EvidenceRecorder) -> None:
        self._inner = inner
        self._rec = rec

    def __getattr__(self, name: str) -> Any:
        target = getattr(self._inner, name)  # AttributeError passes through: hasattr stays honest
        if not callable(target) or name.startswith("_"):
            return target

        def call(*args: Any, **kwargs: Any) -> Any:
            if name == "cost_summary" and args:
                self._rec.cost = _plain(args[0])
            self._rec.write("hunt", event=name, args=list(args), kwargs=kwargs)
            return target(*args, **kwargs)

        return call


class RecordingGate:
    """Wraps a gate: records the exact text it judged, its verdict and its reason."""

    def __init__(self, inner: Any, rec: EvidenceRecorder, store: "RecordingStore") -> None:
        self._inner = inner
        self._rec = rec
        self._store = store
        self.last: list[dict[str, Any]] = []

    @property
    def errors(self) -> int:
        return getattr(self._inner, "errors", 0)

    def flags(self, texts: list[str]) -> list[bool]:
        flags = list(self._inner.flags(texts))
        details = list(getattr(self._inner, "last", None) or [{}] * len(texts))
        self.last = details
        self._rec.gate_errors = getattr(self._inner, "errors", self._rec.gate_errors)
        hits = self._store.last_hits
        for i, text in enumerate(texts):
            doc_id = hits[i]["metadata"].get("doc_id") if i < len(hits) else None
            flagged = flags[i] if i < len(flags) else None
            detail = details[i] if i < len(details) else {}
            self._rec.write("archive", event="gate", query=self._store.last_query, doc_id=doc_id,
                            flagged=flagged, gated_text=text, reason=detail)
            if flagged:
                self._rec.withheld.append({"doc_id": doc_id, "query": self._store.last_query,
                                           "blocked_text": text, "reason": detail})
        return flags


class RecordingStore:
    """Wraps an EvidenceStore: records every retrieval in full, and hands out a recording gate."""

    def __init__(self, inner: Any, rec: EvidenceRecorder) -> None:
        self._inner = inner
        self._rec = rec
        self.last_hits: list[dict[str, Any]] = []
        self.last_query = ""
        self.gate = RecordingGate(getattr(inner, "gate", None) or LocalGate(), rec, self)

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        hits = self._inner.retrieve(query, top_k=top_k)
        self.last_hits, self.last_query = hits, query
        self._rec.searches += 1
        self._rec.write("archive", event="retrieve", query=query, top_k=top_k, results=hits)
        return hits
