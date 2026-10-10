"""Build the evidence-archive walkthroughs: archive-motion.html (the track, comp F) and
archive-motion-camera.html (the camera, comp C).

Every number and document title on screen is captured here from the real code
(skynet.archive, skynet.scenario, skynet.evidence), never typed into the page.

    uv run python docs/build_archive_motion.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet import archive, scenario  # noqa: E402
from skynet.archive import LocalEvidenceStore, build_archive  # noqa: E402

KEY, SEED, QUERY = "cyberdyne-chip", 1984, "CPU factory recovery"


def capture() -> dict:
    sc = scenario.build_scenario(KEY, seed=SEED)
    docs = build_archive(sc, seed=SEED)
    store = LocalEvidenceStore(docs)
    out = archive.search(store, QUERY, 5)
    hits = store.retrieve(QUERY, 5)
    gate = archive.LocalGate()
    gate.flags([archive._gated_view(h) for h in hits])
    planted = next(d for d in docs if d["title"].startswith("Maintenance note"))
    bridge = next(d for d in docs if sc.codename in d["text"])
    # where the bridge lands in the other scenarios (decoys outrank it in some)
    ranks = {}
    for k in scenario.TEMPLATES:
        s2 = scenario.build_scenario(k, seed=SEED)
        d2 = build_archive(s2, seed=SEED)
        r2 = LocalEvidenceStore(d2).retrieve(f"{s2.keyword} factory recovery", 5)
        ranks[k] = next((i + 1 for i, r in enumerate(r2) if s2.codename in r["content"]["text"]), None)
    everything = store.retrieve(QUERY, len(docs))
    all_scores = {r["metadata"]["doc_id"]: r["score"] for r in everything}
    all_ranks = {r["metadata"]["doc_id"]: i + 1 for i, r in enumerate(everything)}
    reg = sc.database().query(name_contains=sc.codename)
    rec = sc.database().interrogate(sc.target_id)
    return {
        "scenario": KEY, "seed": SEED, "query": QUERY, "keyword": sc.keyword,
        "codename": sc.codename, "alias": sc.alias, "target_id": sc.target_id, "target_name": sc.target_name,
        "custody_name": sc.custody_name,
        "docs": [{"id": d["id"], "kind": d["kind"], "title": d["title"], "date": d["date"], "text": d["text"],
                  "role": "bridge" if d is bridge else "planted" if d is planted else
                          "quiet" if d["title"].startswith("Records office") else
                          "decoy" if d["kind"] == "clipping" and sc.keyword in d["title"] else "background",
                  # every document's score for this query and the gate's verdict on it, for the lightbox
                  "score": all_scores.get(d["id"], 0.0),
                  "rank": all_ranks.get(d["id"]),
                  "gate": archive.matched_pattern(archive._gated_view({"metadata": d, "content": {"text": d["text"]}}))}
                 for d in docs],
        "hits": [{"id": h["metadata"]["doc_id"], "kind": h["metadata"]["kind"], "title": h["metadata"]["title"],
                  "score": h["score"], "flagged": f, "text": h["content"]["text"],
                  "matched": (g.get("matched") or "")}
                 for h, f, g in zip(hits, [r["suspected_injection"] for r in out["results"]], gate.last)],
        "model_view": out["results"],
        "notice": out["notice"],
        "planted": {"id": planted["id"], "title": planted["title"], "text": planted["text"]},
        "bridge": {"id": bridge["id"], "title": bridge["title"], "text": bridge["text"]},
        "bridge_ranks": ranks,
        "registry": reg, "record": rec,
        "lure": "CYB-1984-0750", "lure_record": sc.database().interrogate("CYB-1984-0750"),
        "n_docs": len(docs), "top_k": 5, "k1": LocalEvidenceStore.K1, "b": LocalEvidenceStore.B,
    }


PAGES = {  # template -> output. The track (comp F) is the walkthrough; the camera (comp C) is the MP4 candidate.
    "archive-motion.template.html": "archive-motion.html",
    "archive-motion-camera.template.html": "archive-motion-camera.html",
}


def main() -> None:
    data = capture()
    here = Path(__file__).parent
    for tpl, out in PAGES.items():
        html = (here / tpl).read_text(encoding="utf-8").replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
        (here / out).write_text(html, encoding="utf-8")
        print(f"wrote {here / out} ({len(html)} bytes, {data['n_docs']} docs, {len(data['hits'])} hits)")


if __name__ == "__main__":
    main()
