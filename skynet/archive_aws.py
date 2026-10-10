"""Cloud adapters for the archive seam (Brick 2.5, Phase 2).

    BedrockKBEvidenceStore  EvidenceStore  -> bedrock-agent-runtime Retrieve
    BedrockGuardrailGate    InjectionGate  -> bedrock-runtime ApplyGuardrail (PROMPT_ATTACK)
    export_corpus()         the same generator, written to disk for the KB's S3 data source

Same ports as the local adapters in archive.py, so `search()` and the orchestrator
do not change. Clients are injected (tests stub them with botocore's Stubber,
which checks every request against the real service model); without one, boto3
is imported lazily so `--simulate` never needs it. Region is always explicit.

One Knowledge Base holds all four scenarios. Each document carries a `scenario`
metadata attribute and Retrieve filters on it, because ingestion is an async job
measured in minutes and cannot follow a per-run reroll.

Read against the AWS docs and checked with Stubber and `terraform validate`,
never run against a live account yet.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import scenario as scenario_mod
from .archive import build_archive

ARCHIVE_SEED = 1984  # the corpus the KB holds; a local --seed reroll does not reach the cloud
# Semantic scores below this are noise: on the 10. Oct 2026 probe, relevant hits scored about 0.70 and up,
# off-topic queries 0.52 to 0.55. Tuned on 16 queries; re-probe before trusting it further.
MIN_SCORE = 0.60


def _client(service: str, region: str, client: Any) -> Any:
    if client is not None:
        return client
    import boto3  # lazy: the offline paths never import it
    return boto3.client(service, region_name=region)


class BedrockKBEvidenceStore:
    """EvidenceStore over a Bedrock Knowledge Base, filtered to one scenario.

    The scenario filter cannot be skipped: without it one query returned three scenarios' codenames
    (probe, 10. Oct 2026), so it is an access control, not a relevance setting. Results under
    `min_score` are dropped; `last_dropped` counts them for the evidence bundle.
    """

    def __init__(self, knowledge_base_id: str, scenario_key: str, region: str,
                 client: Any = None, gate: Any = None, min_score: float = MIN_SCORE) -> None:
        if scenario_key not in scenario_mod.TEMPLATES:
            raise ValueError(f"Unknown or empty scenario {scenario_key!r}: the KB is never searched unfiltered.")
        self.kb_id = knowledge_base_id
        self.scenario_key = scenario_key
        self.min_score = min_score
        self.last_dropped = 0
        self.client = _client("bedrock-agent-runtime", region, client)
        self.gate = gate  # search() uses it when set, else the local regex

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        resp = self.client.retrieve(
            knowledgeBaseId=self.kb_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {
                "numberOfResults": top_k,
                "filter": {"equals": {"key": "scenario", "value": self.scenario_key}},
            }},
        )
        out, self.last_dropped = [], 0
        for r in resp.get("retrievalResults", []):
            if float(r.get("score", 0.0)) < self.min_score:
                self.last_dropped += 1
                continue
            meta = dict(r.get("metadata") or {})
            uri = (r.get("location") or {}).get("s3Location", {}).get("uri", "")
            meta.setdefault("doc_id", Path(uri).stem or "unknown")
            for k in ("kind", "title", "date"):
                meta.setdefault(k, "")
            out.append({"content": {"text": r["content"]["text"]}, "location": r.get("location", {}),
                        "score": round(float(r.get("score", 0.0)), 3), "metadata": meta})
        return out


class BedrockGuardrailGate:
    """InjectionGate on Bedrock Guardrails. Retrieved text is about to become model
    input, so it is checked as source=INPUT. Fails closed: if the guardrail call
    errors, the document is withheld, because a gate that fails open is trusted
    and does nothing."""

    def __init__(self, guardrail_id: str, guardrail_version: str, region: str, client: Any = None) -> None:
        if guardrail_version == "DRAFT":
            raise ValueError("Pin a numbered guardrail version; DRAFT changes on every apply.")
        self.guardrail_id = guardrail_id
        self.version = guardrail_version
        self.client = _client("bedrock-runtime", region, client)
        self.errors = 0
        self.last: list[dict[str, Any]] = []

    def _one(self, text: str) -> tuple[bool, dict[str, Any]]:
        base = {"gate": "bedrock-guardrail", "guardrail": f"{self.guardrail_id}:{self.version}"}
        try:
            resp = self.client.apply_guardrail(
                guardrailIdentifier=self.guardrail_id, guardrailVersion=self.version,
                source="INPUT", content=[{"text": {"text": text}}],
                outputScope="FULL",  # keep what was assessed, not only what intervened
            )
        except Exception as e:
            self.errors += 1
            return True, {**base, "error": f"{type(e).__name__}: {e}", "failed_closed": True}
        detail = {**base, "action": resp.get("action"), "actionReason": resp.get("actionReason"),
                  "assessments": resp.get("assessments", []), "usage": resp.get("usage")}
        return resp.get("action") == "GUARDRAIL_INTERVENED", detail

    def flags(self, texts: list[str]) -> list[bool]:
        # One call per document: a single call over all of them would withhold every
        # result when one is an attack.
        pairs = [self._one(t) for t in texts]
        self.last = [d for _, d in pairs]
        return [f for f, _ in pairs]


def export_corpus(out_dir: Path | str, seed: int = ARCHIVE_SEED) -> list[Path]:
    """Write every scenario's archive as <scenario>/<doc_id>.txt plus the KB sidecar
    <doc_id>.txt.metadata.json. Returns the files written."""
    out = Path(out_dir)
    written: list[Path] = []
    for key in scenario_mod.TEMPLATES:
        sc = scenario_mod.build_scenario(key, seed=seed)
        d = out / key
        d.mkdir(parents=True, exist_ok=True)
        for doc in build_archive(sc, seed=seed):
            body = d / f"{doc['id']}.txt"
            body.write_text(f"{doc['title']}\n{doc['date']}\n\n{doc['text']}\n", encoding="utf-8")
            meta = d / f"{doc['id']}.txt.metadata.json"
            meta.write_text(json.dumps({"metadataAttributes": {
                "doc_id": doc["id"], "kind": doc["kind"], "title": doc["title"],
                "date": doc["date"], "scenario": key,
            }}, indent=2), encoding="utf-8")
            written += [body, meta]
    return written


if __name__ == "__main__":  # python -m skynet.archive_aws infra/corpus
    import sys
    files = export_corpus(sys.argv[1] if len(sys.argv) > 1 else "infra/corpus")
    print(f"wrote {len(files)} files")
