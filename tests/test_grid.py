"""The grid is the adversarial core ~ these lock in the obfuscation that makes
the hunt require reasoning rather than a single lookup. Built per scenario.
"""

import json

from skynet import scenario


def sc():
    return scenario.build_scenario("cyberdyne-chip")


def test_literal_name_query_misses_the_target():
    """A blunt part sweep returns the custody record + decoys, never the asset."""
    s = sc()
    hits = s.database().query(name_contains="CPU")
    ids = {r["id"] for r in hits}
    assert s.target_id not in ids, "Asset must NOT be reachable by name query"
    assert s.custody_id in ids, "The custody record (the thread) should appear"
    assert len(hits) >= 3, "Decoys should create noise"


def test_query_returns_only_summary_fields():
    hits = sc().database().query(location="Lab 2")
    assert hits, "Lab 2 should hold inventory"
    for r in hits:
        assert set(r.keys()) == {"id", "name", "category", "location", "clearance"}
        assert "serial" not in r and "notes" not in r and "custodian" not in r


def test_cross_reference_reaches_the_target():
    """Cross-referencing the custody record surfaces the codename asset."""
    s = sc()
    links = s.database().cross_reference(s.custody_name)
    assert s.target_id in {r["id"] for r in links}, "cross_reference must be the path to the asset"


def test_interrogate_reveals_profile_but_not_internal_flag():
    s = sc()
    rec = s.database().interrogate(s.target_id)
    assert rec["serial"] is None
    assert rec["clearance"] == 5
    assert s.custody_name in rec["custody_links"]
    assert "_target" not in rec, "Internal flag must never leak to an agent"


def test_interrogate_unknown_id_is_graceful():
    from skynet import grid
    assert "error" in grid.GridDatabase.load().interrogate("CYB-1984-9999")


def test_execute_tool_dispatch():
    from skynet import grid
    s = sc()
    out = json.loads(grid.execute_tool(s.database(), "cross_reference", {"name": s.custody_name}))
    assert any(r["id"] == s.target_id for r in out)


def test_registry_holds_assets_not_people():
    """The pivot, locked in: no record in any scenario carries a person-shaped
    field, and the custodian is never a searchable query filter."""
    from skynet import grid
    person_fields = {"age", "ssn", "occupation", "known_associates"}
    for name in scenario.TEMPLATES:
        for r in scenario.build_scenario(name, seed=1).records:
            assert person_fields.isdisjoint(r), f"{name}: {r['id']} carries a person field"
    query_params = set(grid.TOOL_SCHEMAS[0]["input_schema"]["properties"])
    assert "custodian" not in query_params
