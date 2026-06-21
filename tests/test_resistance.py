"""The Resistance counter-tools must actually break the hunt ~ these lock in
that scrub_flag severs the cross_reference path the adaptive hunter relies on.
A disruption tool that doesn't disrupt is theater; this asserts it bites.
"""

import json

from skynet import grid, scenario


def sc():
    return scenario.build_scenario("john-connor")


def test_scrub_flag_breaks_the_cross_reference_path():
    """Before: cross_reference(protector) reaches the target. After scrub_flag on
    the protector: the thread is gone ~ the hunt's one path is severed."""
    s = sc()
    db = s.database()
    before = {r["id"] for r in db.cross_reference(s.protector_name)}
    assert s.target_id in before, "precondition: the hunt reaches the target"

    out = db.scrub_flag(s.protector_id)
    assert "error" not in out
    assert s.target_id in out["severed_links_to"]

    after = {r["id"] for r in db.cross_reference(s.protector_name)}
    assert s.target_id not in after, "scrub_flag must sever the path to the target"


def test_re_alias_changes_the_filed_name():
    s = sc()
    db = s.database()
    out = db.re_alias(s.target_id, "Marcus Vale")
    assert out["old_name"] == s.alias
    assert db.interrogate(s.target_id)["name"] == "Marcus Vale"


def test_resistance_tools_dispatch_through_execute_tool():
    s = sc()
    db = s.database()
    res = json.loads(grid.execute_tool(db, "scrub_flag", {"record_id": s.protector_id}))
    assert res["status"].startswith("flag scrubbed")


def test_resistance_schemas_are_separate_from_hunter_tools():
    """The hunters must never be handed the write tools ~ separate schema lists."""
    hunter = {t["name"] for t in grid.TOOL_SCHEMAS}
    resistance = {t["name"] for t in grid.RESISTANCE_TOOL_SCHEMAS}
    assert hunter.isdisjoint(resistance)
    assert resistance == {"scrub_flag", "re_alias"}


def test_scrub_flag_on_missing_record_is_graceful():
    db = sc().database()
    assert "error" in db.scrub_flag("LA-9999-0000")
