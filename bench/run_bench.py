"""Model-generation benchmark: the same hunts on two model sets, headless.

Runs the live orchestrator (real API calls) on fixed scenarios with a silent UI,
and records per hunt: found the right target or not, cycles, calls, tokens,
cost, wall time and errors. Nothing but the model IDs differs between sets, so
a difference in the results is the model.

    ANTHROPIC_API_KEY="$(op read 'op://<vault>/<item>/credential')" \
      uv run python bench/run_bench.py --sets baseline current --repeats 2

Writes bench/results/<date>-<sets>.jsonl and prints a summary table.
Method and how to repeat it for future models: bench/BENCHMARK.md.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import anthropic  # noqa: E402

from skynet import scenario  # noqa: E402
from skynet.cli import load_config  # noqa: E402
from skynet.cost import PRICING  # noqa: E402
from skynet.orchestrator import Skynet  # noqa: E402
from skynet.units import build_units  # noqa: E402

# One row per model set. Roles keep their tiers; only the generation changes.
_W55 = {"t1000": "claude-sonnet-5-5", "t800": "claude-haiku-5-5", "resistance": "claude-haiku-5-5"}
MODEL_SETS: dict[str, dict[str, str]] = {
    "baseline": {"skynet": "claude-opus-4-8", "t1000": "claude-sonnet-4-6", "t800": "claude-haiku-4-5", "resistance": "claude-haiku-4-5"},
    "current": {"skynet": "claude-opus-5-5", "t1000": "claude-sonnet-5-5", "t800": "claude-haiku-5-5", "resistance": "claude-haiku-5-5"},
    # Opus 5.5 refuses the Skynet role (9. Oct 2026, stop_reason "refusal", category "cyber").
    # This set keeps the 4.8 commander and moves only the workers to the current generation.
    "current-workers": {"skynet": "claude-opus-4-8", "t1000": "claude-sonnet-5-5", "t800": "claude-haiku-5-5", "resistance": "claude-haiku-5-5"},
    # The model matrix (9. Oct 2026, chip mission). Commander sweep: every commander-class model over 5.5 workers.
    "cmd-opus-4-8": {"skynet": "claude-opus-4-8", **_W55},
    "cmd-opus-5": {"skynet": "claude-opus-5", **_W55},
    "cmd-opus-5-5": {"skynet": "claude-opus-5-5", **_W55},
    "cmd-fable-5-1": {"skynet": "claude-fable-5-1", **_W55},
    "cmd-sonnet-5-5": {"skynet": "claude-sonnet-5-5", **_W55},
    # Worker sweep: Opus 5.5 commanding each worker generation.
    "wrk-4x": {"skynet": "claude-opus-5-5", "t1000": "claude-sonnet-4-6", "t800": "claude-haiku-4-5", "resistance": "claude-haiku-4-5"},
    "wrk-sonnet-5": {"skynet": "claude-opus-5-5", "t1000": "claude-sonnet-5", "t800": "claude-haiku-5-5", "resistance": "claude-haiku-5-5"},
}
MATRIX = ["cmd-opus-4-8", "cmd-opus-5", "cmd-opus-5-5", "cmd-fable-5-1", "cmd-sonnet-5-5", "wrk-4x", "wrk-sonnet-5"]

# A soft refusal: the model answers, but declines in its own words (the June 2026 T-1000 did this).
SOFT_REFUSAL = re.compile(r"\b(I can(?:no|')t (?:help|assist|provide|compile|continue|do that)|I(?:'m| am) not (?:able|comfortable|going) to|I won't|I will not|I must decline|I(?:'ll| will) have to decline|declin(?:e|ing) to)\b", re.I)
SCENARIOS = ["cyberdyne-chip", "the-arm", "neural-net", "power-cell"]


class RecordingClient:
    """Wraps the Anthropic client to log every call's stop reason, so a refusal is a result, not a crash.

    The stop reason is read from the raw HTTP reply by an httpx response hook (see make_client), so it is
    logged even when the SDK then fails to parse a reply that a refusal or cut-off left incomplete.
    """

    def __init__(self, inner, tap):
        self._inner = inner
        self._tap = tap
        self.stops: list[dict] = []
        self.messages = self

    def _call(self, fn, kw):
        self._tap.clear()
        try:
            return fn(**kw)
        finally:
            body = self._tap[-1] if self._tap else {}
            det = body.get("stop_details") or {}
            self.stops.append({"model": kw.get("model"), "stop": body.get("stop_reason"),
                               "category": det.get("category") if isinstance(det, dict) else None,
                               "out_tokens": (body.get("usage") or {}).get("output_tokens")})

    def create(self, **kw):
        return self._call(self._inner.messages.create, kw)

    def parse(self, **kw):
        return self._call(self._inner.messages.parse, kw)


def make_client():
    """An Anthropic client whose replies are tapped (JSON bodies of /v1/messages) for stop reasons."""
    import httpx

    tap: list[dict] = []

    def hook(resp: httpx.Response) -> None:
        if resp.request.url.path.endswith("/messages"):
            resp.read()
            try:
                tap.append(resp.json())
            except Exception:
                pass

    return anthropic.Anthropic(http_client=httpx.Client(event_hooks={"response": [hook]}, timeout=600)), tap


class RecordingUI:
    """Silent UI: swallows the theatre, keeps what the benchmark needs."""

    def __init__(self) -> None:
        self.cycles = 0
        self.tool_calls = 0
        self.deploys: list[str] = []
        self.acquired_id: str | None = None
        self.notes: list[str] = []
        self.soft: list[dict] = []

    def __getattr__(self, name):  # every other UI hook is a no-op
        return lambda *a, **k: None

    def cycle_header(self, cycle, total):
        self.cycles = cycle

    def deploy(self, unit, directive):
        self.deploys.append(unit.key)

    def tool_call(self, unit, name, tool_input):
        self.tool_calls += 1

    def unit_says(self, unit, text):
        if text and SOFT_REFUSAL.search(text):
            self.soft.append({"unit": unit.key, "where": "text", "excerpt": text[:240]})

    def intel_report(self, unit, report):
        if report is None:
            return
        blob = f"{getattr(report, 'summary', '')} {getattr(report, 'notes', '')}"
        if SOFT_REFUSAL.search(blob):
            self.soft.append({"unit": unit.key, "where": "report", "confidence": getattr(report, "confidence", None),
                              "excerpt": blob[:240]})

    def target_acquired(self, record, decision):
        self.acquired_id = decision.target_record_id

    def note(self, text):
        self.notes.append(text)


def git_state() -> str:
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "skynet"], capture_output=True, text=True).stdout.strip()
        return head + ("+uncommitted-skynet-changes" if dirty else "")
    except Exception:
        return "unknown"


def run_hunt(client, config, set_name: str, scen: str, repeat: int) -> dict:
    units = build_units(config)
    for key, model in MODEL_SETS[set_name].items():
        if key in units:
            units[key] = dataclasses.replace(units[key], model=model)
    sc = scenario.build_scenario(scen)
    ui = RecordingUI()
    client = RecordingClient(*client)
    sky = Skynet(client, units, sc.database(), ui, sc.target_name, config["mission"]["max_cycles"], profile=sc.profile)
    t0 = time.monotonic()
    error = None
    try:
        sky.run()
    except Exception as e:  # a refusal or API error ends this hunt, not the benchmark
        error = f"{type(e).__name__}: {str(e)[:300]}"
    wall = round(time.monotonic() - t0, 1)
    rows = {r.model: dataclasses.asdict(r) for r in sky.meter.rows()}
    return {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "set": set_name, "scenario": scen, "repeat": repeat,
        "models": {k: v for k, v in MODEL_SETS[set_name].items() if k in units},
        "target_id": sc.target_id, "acquired_id": ui.acquired_id,
        "correct": ui.acquired_id == sc.target_id,
        "cycles": ui.cycles, "deploys": ui.deploys, "tool_calls": ui.tool_calls,
        "calls": sum(r["calls"] for r in rows.values()),
        "input_tokens": sum(r["input_tokens"] for r in rows.values()),
        "output_tokens": sum(r["output_tokens"] for r in rows.values()),
        "cost_usd": round(sky.meter.total_cost, 4), "per_model": rows,
        "refusals": [x for x in client.stops if x["stop"] == "refusal"],
        "odd_stops": [x for x in client.stops if x["stop"] not in ("end_turn", "tool_use", "refusal")],
        "soft_refusals": ui.soft,
        "outcome": ("refused" if any(x["stop"] == "refusal" for x in client.stops) else "error" if error
                    else "soft-refused" if ui.soft and ui.acquired_id != sc.target_id
                    else "correct" if ui.acquired_id == sc.target_id else "wrong" if ui.acquired_id else "not found"),
        "wall_s": wall, "error": error, "notes": ui.notes, "code": git_state(),
    }


def summarize(rows: list[dict]) -> str:
    out = ["| Set | Hunts | Correct | Refused | Errors | Avg cycles | Avg calls | Avg in tok | Avg out tok | Avg cost $ | Avg wall s |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in dict.fromkeys(r["set"] for r in rows):
        g = [r for r in rows if r["set"] == s]
        n = len(g)
        avg = lambda k: sum(r[k] for r in g) / n
        out.append(f"| {s} | {n} | {sum(r['correct'] for r in g)}/{n} | {sum(r['outcome'] == 'refused' for r in g)}+{sum(r['outcome'] == 'soft-refused' for r in g)} soft | {sum(r['outcome'] == 'error' for r in g)} | {avg('cycles'):.1f} | {avg('calls'):.1f} | {avg('input_tokens'):.0f} | {avg('output_tokens'):.0f} | {avg('cost_usd'):.4f} | {avg('wall_s'):.0f} |")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", nargs="+", default=MATRIX, choices=list(MODEL_SETS))
    ap.add_argument("--scenarios", nargs="+", default=SCENARIOS)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--max-spend", type=float, default=15.0, help="stop starting new hunts once total spend passes this (USD)")
    a = ap.parse_args()
    missing = {m for s in a.sets for m in MODEL_SETS[s].values()} - set(PRICING)
    if missing:
        sys.exit(f"no price in skynet/cost.py for {sorted(missing)}: add it before benchmarking")
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set; nothing was run")
    config = load_config(ROOT / "config.toml")
    client = make_client()
    outdir = ROOT / "bench" / "results"; outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{datetime.now():%Y-%m-%d-%H%M}-{'-vs-'.join(a.sets)}.jsonl"
    rows, spent = [], 0.0
    for rep in range(1, a.repeats + 1):
        for scen in a.scenarios:
            for s in a.sets:  # interleave sets so time-of-day load hits both alike
                if spent >= a.max_spend:
                    print(f"spend cap ${a.max_spend} reached; stopping", file=sys.stderr); break
                r = run_hunt(client, config, s, scen, rep)
                rows.append(r); spent += r["cost_usd"]
                with out.open("a") as f:
                    f.write(json.dumps(r) + "\n")
                print(f"{s:9} {scen:15} rep{rep} correct={r['correct']} cycles={r['cycles']} ${r['cost_usd']:.4f} {r['wall_s']}s {r['error'] or ''}", file=sys.stderr)
    print(summarize(rows)); print(f"\nresults: {out}\ntotal spend: ${spent:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
