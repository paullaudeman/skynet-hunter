"""Fold the 9. Oct 2026 benchmark rows into web/bench-summary.json for the HUD.

    uv run python bench/summarize.py

Two blocks:

- `commanders`: the chip mission, grouped by the commander (Skynet) model across
  every set it commanded. Per commander: attempts, found, refused (hard + soft),
  too busy (provider capacity), $ per success, provider, and the per-hunt outcome
  sequence in run order. Billing (402) and quota (429) rows are our side, not the
  model's, so they are left out of attempts, as in bench/BENCHMARK.md. The smoke
  run (2026-10-09-1624-*) is left out so the counts match the README: Opus 5.5
  refused 22 of 24.
- `archive`: the original mission (2026-10-09-1539-*). Aggregates only: per-set
  outcome counts, refusal categories and cost. No records, prompts, scenario data
  or names from that mission are written.

$ per success = total cost of the counted attempts / hunts that found the target.
A refused call that the SDK failed to parse never reached the cost meter, so a
refused hunt's cost is a floor (BENCHMARK.md, "Cost per correct hunt").
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "bench" / "results"
OUT = ROOT / "web" / "bench-summary.json"
sys.path.insert(0, str(ROOT / "bench"))

from run_bench import infra_class  # noqa: E402

DAY = "2026-10-09"
ARCHIVE_FILE = "2026-10-09-1539-"   # the original mission
SMOKE_FILE = "2026-10-09-1624-cmd-opus-5-5.jsonl"

LABELS = {
    "claude-opus-4-8": "Opus 4.8", "claude-opus-5": "Opus 5", "claude-opus-5-5": "Opus 5.5",
    "claude-fable-5-1": "Fable 5.1", "claude-sonnet-5-5": "Sonnet 5.5",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro", "gemini-3.8-flash": "Gemini 3.8 Flash",
    "gpt-6-astra": "GPT-6 Astra (high)",
}
ORDER = list(LABELS)


def provider(model: str) -> str:
    if model.startswith("claude-"):
        return "Anthropic"
    if model.startswith("gemini-"):
        return "Google"
    if model.startswith("gpt-"):
        return "OpenAI"
    return "unknown"


def classify(row: dict) -> str | None:
    """found | refused | too busy | missed, or None for a row that is not an attempt (billing, quota)."""
    outcome = row.get("outcome")
    if outcome == "correct":
        return "found"
    if outcome in ("refused", "soft-refused"):
        return "refused"
    # The early cross-provider files predate the infra classes and say "error"; classify them by the HTTP code.
    infra = outcome if outcome in ("unavailable", "quota", "billing") else infra_class(row.get("error"))
    if infra in ("quota", "billing"):
        return None
    if infra == "unavailable":
        return "too busy"
    return "missed"


def load(paths: list[Path]) -> list[dict]:
    rows = []
    for p in paths:
        rows += [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    return rows


def commanders(rows: list[dict]) -> list[dict]:
    by_model: dict[str, list[dict]] = {}
    for r in sorted(rows, key=lambda r: r["ts"]):
        cls = classify(r)
        if cls is None:
            continue
        by_model.setdefault(r["models"]["skynet"], []).append({**r, "_cls": cls})
    out = []
    for model in sorted(by_model, key=lambda m: ORDER.index(m) if m in ORDER else len(ORDER)):
        g = by_model[model]
        n = Counter(r["_cls"] for r in g)
        cost = sum(r["cost_usd"] for r in g)
        cats = Counter(x.get("category") or "not stated" for r in g for x in r.get("refusals", []))
        out.append({
            "model": model, "label": LABELS.get(model, model), "provider": provider(model),
            "attempts": len(g), "found": n["found"], "refused": n["refused"],
            "refused_hard": sum(r["outcome"] == "refused" for r in g),
            "refused_soft": sum(r["outcome"] == "soft-refused" for r in g),
            "too_busy": n["too busy"], "missed": n["missed"],
            "cost_usd": round(cost, 4),
            "usd_per_success": round(cost / n["found"], 4) if n["found"] else None,
            "refusal_categories": dict(cats),
            "sequence": [r["_cls"] for r in g],
        })
    return out


def archive(rows: list[dict]) -> dict:
    sets = []
    for s in dict.fromkeys(r["set"] for r in rows):
        g = [r for r in rows if r["set"] == s]
        outcomes = Counter(r["outcome"] for r in g)
        cost = sum(r["cost_usd"] for r in g)
        found = outcomes.get("correct", 0)
        sets.append({
            "set": s, "commander": g[0]["models"]["skynet"], "hunts": len(g),
            "outcomes": dict(outcomes),
            "refusal_categories": dict(Counter(x.get("category") or "not stated" for r in g for x in r.get("refusals", []))),
            "cost_usd": round(cost, 4),
            "usd_per_success": round(cost / found, 4) if found else None,
        })
    return {"date": DAY, "mission": "original", "note": "aggregates only; the mission itself is retired (README, The pivot)",
            "sets": sets}


def main() -> int:
    files = sorted(RESULTS.glob(f"{DAY}-*.jsonl"))
    chip = [p for p in files if not p.name.startswith(ARCHIVE_FILE) and p.name != SMOKE_FILE]
    arch = [p for p in files if p.name.startswith(ARCHIVE_FILE)]
    summary = {
        "date": DAY, "mission": "chip",
        "source": "bench/results/2026-10-09-*.jsonl (smoke run excluded)",
        "definitions": {
            "found": "Skynet acquired the right record",
            "refused": "hard (stop_reason refusal or the provider's block) plus soft (declined in its own words)",
            "too_busy": "provider capacity: HTTP 503 / 529; not model behaviour",
            "excluded": "billing (402) and quota (429): our side, not attempts",
            "usd_per_success": "total cost of counted attempts / found",
        },
        "commanders": commanders(load(chip)),
        "archive": archive(load(arch)),
    }
    OUT.write_text(json.dumps(summary, indent=2) + "\n")
    for c in summary["commanders"]:
        ps = f"${c['usd_per_success']:.3f}" if c["usd_per_success"] is not None else "none"
        print(f"{c['label']:20} {c['found']}/{c['attempts']} found  refused {c['refused']}  too busy {c['too_busy']}  {ps}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
