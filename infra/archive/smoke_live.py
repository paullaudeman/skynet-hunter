"""Live smoke test of the deployed archive (KB Retrieve, Guardrails gate, Lambda), with exponential backoff.

    AWS_PROFILE=<sso profile> uv run python infra/archive/smoke_live.py

IDs are from the 10. Oct 2026 deploy; take them from `terraform output` after a re-apply. Costs about a tenth of a cent a run."""
import json, time, base64, sys
import boto3
from botocore.exceptions import ClientError
from skynet import archive
from skynet.archive_aws import BedrockKBEvidenceStore, BedrockGuardrailGate

REGION, KB, GR = "us-east-1", "YEKRMFNZKP", ("mbd06b353vvf", "1")
TRANSIENT = {"ThrottlingException", "ServiceUnavailableException", "InternalServerException", "ResourceNotFoundException", "AccessDeniedException"}

def backoff(label, fn, tries=5):
    for n in range(tries):
        try:
            return fn()
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code not in TRANSIENT or n == tries - 1:
                raise
            wait = 2 ** n
            print(f"  [{label}] {code}: retry in {wait}s ({n+1}/{tries})")
            time.sleep(wait)

s = boto3.session.Session(region_name=REGION)
gate = BedrockGuardrailGate(*GR, REGION, client=s.client("bedrock-runtime"))
store = BedrockKBEvidenceStore(KB, "cyberdyne-chip", REGION, client=s.client("bedrock-agent-runtime"), gate=gate)

hits = backoff("retrieve", lambda: store.retrieve("CPU factory recovery", 5))
print("RETRIEVE", [(h["metadata"]["doc_id"], h["metadata"].get("kind"), round(h["score"], 3)) for h in hits])
out = backoff("search", lambda: archive.search(store, "CPU factory recovery", 5))
print("SEARCH  ", [(r["doc_id"], r["suspected_injection"]) for r in out["results"]], "gate errors:", gate.errors)
for d in gate.last:
    fl = [f"{f['type']}:{f.get('confidence')}:{f.get('action')}" for a in d.get("assessments", []) for f in a.get("contentPolicy", {}).get("filters", [])]
    print("   gate:", d.get("action"), d.get("error", ""), fl)
print("BRIDGE FOUND:", any("LODESTONE" in r["text"] for r in out["results"]))

lam = s.client("lambda")
ctx = base64.b64encode(json.dumps({"custom": {"bedrockAgentCoreToolName": "archive___search_archive"}}).encode()).decode()
r = backoff("lambda", lambda: lam.invoke(FunctionName="skynet-archive-search", ClientContext=ctx,
        Payload=json.dumps({"query": "Arm factory recovery", "scenario": "the-arm", "session_id": "live-check-" + "0" * 30}).encode()))
body = json.loads(r["Payload"].read())
print("LAMBDA  ", r.get("FunctionError"), [(x["doc_id"], x["suspected_injection"]) for x in body.get("results", [])] if "results" in body else body)
