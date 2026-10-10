"""Per-model latency probe: time-to-first-token and output tokens per second, Anthropic API vs Bedrock.

    ANTHROPIC_API_KEY=... AWS_PROFILE=... uv run python bench/latency/probe.py --n 5 > bench/latency/<date>.jsonl

Each call streams one fixed prompt that asks for ~300 tokens of prose, no thinking, so the numbers isolate the model
and the route. TTFT = request sent to first text delta. tps = output tokens / (last delta - first delta).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone

PROMPT = ("Write about 250 words describing how a records office catalogues recovered hardware: intake, custody, "
          "labelling, storage. Plain prose, no lists.")
API = ["claude-opus-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
# the control: the Bedrock arm's own models, on the Anthropic API, so route and model generation can be separated
API_CONTROL = ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"]
BEDROCK = ["global.anthropic.claude-opus-4-6-v1", "global.anthropic.claude-sonnet-4-6",
           "global.anthropic.claude-haiku-4-5-20251001-v1:0"]


def one(client, model: str) -> dict:
    t0 = time.perf_counter(); first = last = None
    with client.messages.stream(model=model, max_tokens=600, messages=[{"role": "user", "content": PROMPT}]) as s:
        for ev in s:
            if ev.type == "content_block_delta" and getattr(ev.delta, "type", "") == "text_delta":
                now = time.perf_counter(); first = first or now; last = now
        msg = s.get_final_message()
    out = msg.usage.output_tokens
    gen = (last - first) if first and last and last > first else None
    return {"model": model, "ttft_s": round(first - t0, 3) if first else None, "total_s": round(time.perf_counter() - t0, 3),
            "output_tokens": out, "tps": round(out / gen, 1) if gen else None}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=5); ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--control", action="store_true", help="only the 4.x models on the Anthropic API")
    a = ap.parse_args()
    import anthropic
    routes = ([("anthropic-api", anthropic.Anthropic(), API_CONTROL)] if a.control else
              [("anthropic-api", anthropic.Anthropic(), API), ("bedrock", anthropic.AnthropicBedrock(aws_region=a.region), BEDROCK)])
    for i in range(a.n):
        for route, client, models in routes:
            for m in models:
                try:
                    r = one(client, m)
                except Exception as e:  # record the failure, keep going
                    r = {"model": m, "error": f"{type(e).__name__}: {str(e)[:120]}"}
                r.update(route=route, rep=i, ts=datetime.now(timezone.utc).isoformat(timespec="seconds"))
                print(json.dumps(r), flush=True); print(f"{route:13} {m:48} {r.get('ttft_s')}s ttft {r.get('tps')} tok/s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
