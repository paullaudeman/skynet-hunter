"""Scenario generation ~ what makes the hunt re-runnable and randomisable.

The dataset on disk is just a neutral civilian population. A *scenario* injects
the target (under an alias), the protector (who shares the target's real
surname and carries the "dependent minor" flag), and a handful of surname
decoys. That injection is what preserves the solvability mechanism generically:

    literal surname sweep  -> protector + decoys, never the aliased target
    cross-reference protector -> the hidden minor

Pick a named template, or `random` for a seeded reroll.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from . import grid

# Terminator-flavoured templates. protector shares the target's REAL surname.
TEMPLATES: dict[str, dict] = {
    "john-connor": {
        "target_first": "John", "target_last": "Connor", "alias_last": "Reese",
        "age": 10, "occupation": "student", "location": "Reseda",
        "protector_first": "Sarah", "protector_occ": "waitress", "protector_loc": "Reseda",
        "protector_age": 19, "relation": "mother", "decoys": 4,
    },
    "danny-dyson": {
        "target_first": "Danny", "target_last": "Dyson", "alias_last": "Cole",
        "age": 9, "occupation": "student", "location": "Long Beach",
        "protector_first": "Miles", "protector_occ": "computer engineer", "protector_loc": "Long Beach",
        "protector_age": 35, "relation": "father", "decoys": 3,
    },
    "blair-brewster": {
        "target_first": "Blair", "target_last": "Brewster", "alias_last": "Hooper",
        "age": 12, "occupation": "student", "location": "Burbank",
        "protector_first": "Kate", "protector_occ": "veterinarian", "protector_loc": "Burbank",
        "protector_age": 31, "relation": "aunt", "decoys": 4,
    },
    "eli-vega": {
        "target_first": "Eli", "target_last": "Vega", "alias_last": "Marsh",
        "age": 11, "occupation": "student", "location": "Pacoima",
        "protector_first": "Rosa", "protector_occ": "factory worker", "protector_loc": "Pacoima",
        "protector_age": 29, "relation": "legal guardian", "decoys": 3,
    },
}

SCENARIO_CHOICES = list(TEMPLATES) + ["random"]

_DECOY_FIRST = ["William", "Mary", "Daniel", "Patricia", "Howard", "Gloria",
                "Vincent", "Ruth", "Earl", "Doris", "Walter", "Edith"]
_DECOY_OCC = ["accountant", "nurse", "mechanic", "teacher", "clerk", "plumber",
              "grocer", "welder", "typist", "barber"]
_DECOY_LOC = ["Pasadena", "Glendale", "Van Nuys", "Burbank", "Lakewood",
              "Norwalk", "Whittier", "Downey", "Bellflower"]


@dataclass
class Scenario:
    key: str
    target_name: str        # the real name ~ the mission objective
    target_id: str
    alias: str              # what the grid actually files the target under
    protector_name: str
    protector_id: str
    relation: str
    profile: str            # one-line description of the obfuscation, for the briefing
    records: list[dict]

    def database(self) -> grid.GridDatabase:
        return grid.GridDatabase(self.records)


def _ssn(rng: random.Random) -> str:
    return f"5{rng.randint(3, 6)}{rng.randint(0, 9)}-XX-{rng.randint(1000, 9999)}"


def build_scenario(name: str = "john-connor", seed: int | None = None) -> Scenario:
    """Construct a Scenario. `name` is a template key or 'random'. `seed` makes
    'random' (and the injected decoy details / shuffle) reproducible."""
    rng = random.Random(seed)
    if name == "random":
        key = rng.choice(list(TEMPLATES))
    elif name in TEMPLATES:
        key = name
    else:
        key = "john-connor"
    t = TEMPLATES[key]

    target_name = f"{t['target_first']} {t['target_last']}"
    alias = f"{t['target_first']} {t['alias_last']}"
    protector_name = f"{t['protector_first']} {t['target_last']}"
    target_id = "LA-1984-0742"
    protector_id = "LA-1984-0717"

    target = {
        "id": target_id, "name": alias, "age": t["age"], "occupation": t["occupation"],
        "location": t["location"], "ssn": None, "known_associates": [protector_name],
        "notes": (f"Juvenile, age {t['age']}. No SSN, no birth record on file. "
                  f"Goes by '{t['target_first']}'. Guardian: {protector_name}. Multiple address changes."),
        "_target": True,
    }
    protector = {
        "id": protector_id, "name": protector_name, "age": t["protector_age"],
        "occupation": t["protector_occ"], "location": t["protector_loc"], "ssn": _ssn(rng),
        "known_associates": [alias],
        "notes": (f"{t['relation'].capitalize()} of a dependent minor on record. "
                  f"Works as a {t['protector_occ']}. Filed a stalking report this month."),
        "_target": False,
    }

    decoys: list[dict] = []
    used: set[str] = set()
    for i in range(t["decoys"]):
        pool = [f for f in _DECOY_FIRST if f not in used] or _DECOY_FIRST
        first = rng.choice(pool)
        used.add(first)
        decoys.append({
            "id": f"LA-1984-07{50 + i}", "name": f"{first} {t['target_last']}",
            "age": rng.randint(28, 58), "occupation": rng.choice(_DECOY_OCC),
            "location": rng.choice(_DECOY_LOC), "ssn": _ssn(rng), "known_associates": [],
            "notes": "Surname match. No relation to subject of interest. No flags.",
            "_target": False,
        })

    records = grid.load_civilians() + [target, protector] + decoys
    rng.shuffle(records)

    profile = (f"Target concealed under alias '{alias}'. A literal surname sweep "
               f"returns the {t['relation']} and decoys ~ never the target. "
               f"Cross-reference the protector to surface the hidden minor.")

    return Scenario(
        key=key, target_name=target_name, target_id=target_id, alias=alias,
        protector_name=protector_name, protector_id=protector_id,
        relation=t["relation"], profile=profile, records=records,
    )
