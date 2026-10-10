"""Pull a run's AWS-side records into its evidence bundle (runs/<session_id>/aws.jsonl).

    uv run python -m skynet.collect_aws runs/<session_id> --region us-east-1 \
        --log-group /aws/lambda/skynet-archive-search [--profile NAME] [--slack-s 300]

Reads the Lambda's JSON log lines (evidence.LogRecorder) inside the run's time window,
keeps the ones carrying this session_id, and appends them. Read-only: one paginated
FilterLogEvents call. CloudWatch can lag a few seconds; re-run it and nothing duplicates,
because the file is rewritten, not appended to.

The CLI path calls the KB and the guardrail directly, so its records are already in
archive.jsonl. This covers the Gateway path, the one place our process doesn't see the call.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso).timestamp() * 1000)


def collect(bundle: Path | str, log_group: str, client: Any, slack_s: int = 300) -> int:
    bundle = Path(bundle)
    summary = json.loads((bundle / "summary.json").read_text(encoding="utf-8"))
    session = summary["session_id"]
    kwargs: dict[str, Any] = {
        "logGroupName": log_group,
        "startTime": _ms(summary["started"]) - slack_s * 1000,
        "endTime": _ms(summary["ended"]) + slack_s * 1000,
        "filterPattern": f'"{session}"',
    }
    lines: list[dict[str, Any]] = []
    while True:
        resp = client.filter_log_events(**kwargs)
        for ev in resp.get("events", []):
            try:
                rec = json.loads(ev["message"])
            except (json.JSONDecodeError, KeyError):
                continue  # Lambda START/END/REPORT lines and anything not ours
            if rec.get("session_id") == session:
                rec["cloudwatch"] = {"logStreamName": ev.get("logStreamName"), "eventId": ev.get("eventId")}
                lines.append(rec)
        token = resp.get("nextToken")
        if not token:
            break
        kwargs["nextToken"] = token
    lines.sort(key=lambda r: r.get("ts", ""))
    (bundle / "aws.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in lines), encoding="utf-8")
    return len(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="collect_aws")
    p.add_argument("bundle")
    p.add_argument("--region", required=True)
    p.add_argument("--log-group", required=True)
    p.add_argument("--profile")
    p.add_argument("--slack-s", type=int, default=300)
    a = p.parse_args(argv)
    import boto3
    client = boto3.session.Session(profile_name=a.profile, region_name=a.region).client("logs")
    n = collect(a.bundle, a.log_group, client, a.slack_s)
    print(f"{n} AWS record(s) -> {Path(a.bundle) / 'aws.jsonl'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
