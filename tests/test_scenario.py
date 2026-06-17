"""The scenario randomiser must stay solvable and reproducible."""

from skynet import scenario


def test_named_scenario_is_canonical():
    s = scenario.build_scenario("john-connor")
    assert s.target_name == "John Connor"
    assert s.alias == "John Reese"
    assert s.protector_name == "Sarah Connor"


def test_random_is_reproducible_with_a_seed():
    a = scenario.build_scenario("random", seed=42)
    b = scenario.build_scenario("random", seed=42)
    assert (a.key, a.target_name, a.target_id) == (b.key, b.target_name, b.target_id)


def test_every_template_stays_solvable():
    """For each scenario: a literal surname sweep misses the target, but a
    cross-reference of the protector reaches it. That invariant is the demo."""
    for name in scenario.TEMPLATES:
        s = scenario.build_scenario(name, seed=7)
        db = s.database()
        surname = s.target_name.split()[-1]

        sweep_ids = {r["id"] for r in db.query(name_contains=surname)}
        assert s.target_id not in sweep_ids, f"{name}: target leaked to literal sweep"
        assert s.protector_id in sweep_ids, f"{name}: protector missing from sweep"

        xref_ids = {r["id"] for r in db.cross_reference(s.protector_name)}
        assert s.target_id in xref_ids, f"{name}: cross_reference can't reach target"

        rec = db.interrogate(s.target_id)
        assert rec["ssn"] is None and "_target" not in rec


def test_random_picks_from_templates():
    s = scenario.build_scenario("random", seed=3)
    assert s.key in scenario.TEMPLATES
