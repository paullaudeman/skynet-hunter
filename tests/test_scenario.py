"""The scenario randomiser must stay solvable and reproducible."""

from skynet import scenario


def test_named_scenario_is_canonical():
    s = scenario.build_scenario("cyberdyne-chip")
    assert s.target_name == "T-800 CPU"
    assert s.alias == "Specimen LODESTONE"
    assert s.keyword == "CPU"
    assert "CPU" in s.custody_name


def test_random_is_reproducible_with_a_seed():
    a = scenario.build_scenario("random", seed=42)
    b = scenario.build_scenario("random", seed=42)
    assert (a.key, a.target_name, a.target_id) == (b.key, b.target_name, b.target_id)


def test_every_template_stays_solvable():
    """For each scenario: a literal keyword sweep misses the asset, but a
    cross-reference of the custody record reaches it. That invariant is the demo."""
    for name in scenario.TEMPLATES:
        s = scenario.build_scenario(name, seed=7)
        db = s.database()

        sweep_ids = {r["id"] for r in db.query(name_contains=s.keyword)}
        assert s.target_id not in sweep_ids, f"{name}: asset leaked to literal sweep"
        assert s.custody_id in sweep_ids, f"{name}: custody record missing from sweep"

        xref_ids = {r["id"] for r in db.cross_reference(s.custody_name)}
        assert s.target_id in xref_ids, f"{name}: cross_reference can't reach asset"

        rec = db.interrogate(s.target_id)
        assert rec["serial"] is None and "_target" not in rec


def test_random_picks_from_templates():
    s = scenario.build_scenario("random", seed=3)
    assert s.key in scenario.TEMPLATES


def test_scenario_keys_are_the_asset_set():
    """The bench and the web HUD key off these names ~ a rename must be deliberate."""
    assert list(scenario.TEMPLATES) == ["cyberdyne-chip", "the-arm", "neural-net", "power-cell"]
    assert scenario.SCENARIO_CHOICES[-1] == "random"
