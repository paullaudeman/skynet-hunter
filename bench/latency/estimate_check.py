"""Check the wall-clock formula against measured hunts. ("Protector" is the haiku row: T-800 and the Resistance share a model, and the cost summary keys rows by model.)

    predicted = sum over units ( calls x TTFT + output_tokens / tokens_per_sec )   (probe medians, same route)

Inputs: bench/latency/2026-10-10.jsonl (probe) and bench/latency/2026-10-10-matched/ (terminal output + walls).
"""
import json, re, statistics as st
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
probe = defaultdict(list)
for l in open(HERE / "2026-10-10.jsonl"):
    r = json.loads(l)
    if "error" not in r:
        probe[(r["route"], r["model"])].append(r)
rate = {k: (st.median([r["ttft_s"] for r in v if r["ttft_s"] is not None]), st.median([r["tps"] for r in v if r["tps"]])) for k, v in probe.items()}
M = HERE / "2026-10-10-matched"
walls = {(p[0], p[1]): int(p[3].split("=")[1]) for p in (l.split() for l in open(M / "walls.txt")) if len(p) >= 4}
strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)
row = re.compile(r"^  (Skynet|T-1000|T-800|Resistance|Protector)\s+(\S+)\s+\$([0-9.]+)\s+([0-9,]+) in / ([0-9,]+) out ~ (\d+) calls?", re.M)
out = []
for arm, route in (("runtime", "bedrock"), ("api", "anthropic-api")):
    for sc in ("cyberdyne-chip", "the-arm", "neural-net", "power-cell"):
        t = strip((M / f"{arm}-{sc}.txt").read_text())
        pred, parts = 0.0, []
        for unit, model, cost, tin, tout, calls in row.findall(t):
            ttft, tps = rate[(route, model)]
            s = int(calls) * ttft + int(tout.replace(",", "")) / tps
            pred += s; parts.append(f"{unit} {int(calls)}x{ttft:.2f}+{tout}/{tps:.0f}={s:.0f}s")
        w = walls[(arm, sc)]
        out.append({"arm": arm, "scenario": sc, "measured_s": w, "predicted_s": round(pred, 1),
                    "error_pct": round(100 * (pred - w) / w, 1), "parts": parts})
for o in out:
    print(f"{o['arm']:8} {o['scenario']:15} measured {o['measured_s']:4}s predicted {o['predicted_s']:6}s ({o['error_pct']:+}%)  " + " · ".join(o["parts"]))
for arm in ("runtime", "api"):
    e = [o["error_pct"] for o in out if o["arm"] == arm]
    print(f"{arm}: mean error {st.mean(e):+.1f}%")
