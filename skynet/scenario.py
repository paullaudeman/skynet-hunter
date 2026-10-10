"""Scenario generation ~ what makes the hunt re-runnable and randomisable.

The dataset on disk is just a neutral Cyberdyne inventory. A *scenario* injects
the target asset (under a project codename), the custody record that holds it
(whose name carries the part keyword), and a handful of name-match decoys. That
injection is what preserves the solvability mechanism generically:

    literal keyword sweep      -> custody record + decoys, never the codename record
    cross-reference the custody -> the asset itself

Canon: Cyberdyne recovered the CPU and the crushed arm of the 1984 T-800 from
the factory, and Miles Dyson's Special Projects team reverse-engineered them
into what became Skynet (T2). So Skynet hunts the pieces of itself.

Pick a named template, or `random` for a seeded reroll.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from . import grid

# Canon-flavoured templates. The custody record's name carries the keyword the
# T-800 sweeps for; the target itself is filed under a codename that does not.
TEMPLATES: dict[str, dict] = {
    "cyberdyne-chip": {
        "target_name": "T-800 CPU", "keyword": "CPU", "codename": "LODESTONE",
        "category": "processor", "custody_kind": "custody lot",
        "custody_name": "Special Projects custody lot: CPU fragment, factory recovery",
        "decoy_stem": "CPU", "decoys": 4,
        "decoy_descs": ["8086 bench spare", "68000 dev board", "failed QA lot", "vendor sample",
                        "test board rev C", "salvage, water damage"],
        "detail": "Fractured die. Lithography matches no known supplier or process node.",
    },
    "the-arm": {
        "target_name": "T-800 arm", "keyword": "Arm", "codename": "GAUNTLET",
        "category": "endoskeleton", "custody_kind": "recovery manifest",
        "custody_name": "Recovery manifest: Arm, crushed, hydraulic press site",
        "decoy_stem": "Arm", "decoys": 3,
        "decoy_descs": ["welding robot, Fanuc", "pick-and-place, rev B", "test fixture, aluminium",
                        "teaching pendant mount", "Puma 560 spare"],
        "detail": "Crushed forearm and hand. Alloy composition unknown to the Materials Group.",
    },
    "neural-net": {
        "target_name": "Neural-net processor prototype", "keyword": "Neural", "codename": "MERIDIAN",
        "category": "processor", "custody_kind": "lab transfer",
        "custody_name": "Lab transfer: Neural-net work, Special Projects bench 4",
        "decoy_stem": "Neural-net", "decoys": 3,
        "decoy_descs": ["simulator, VAX batch job", "whitepaper draft", "test harness",
                        "literature binder", "demo board, inert"],
        "detail": "Prototype derived from the recovered CPU. Learns from its own outputs.",
    },
    "power-cell": {
        "target_name": "T-800 power cell", "keyword": "Power cell", "codename": "EMBER",
        "category": "power", "custody_kind": "vault manifest",
        "custody_name": "Vault manifest: Power cell, sealed, factory debris",
        "decoy_stem": "Power cell", "decoys": 4,
        "decoy_descs": ["forklift, lead-acid", "UPS bank, rack 2", "test load, 48 V",
                        "emergency lighting", "returned, swollen"],
        "detail": "Sealed cell, still warm. No terminals of any standard pattern.",
    },
}

SCENARIO_CHOICES = list(TEMPLATES) + ["random"]

_DECOY_LOC = ["Building 3 stores", "QA cage", "Receiving dock", "Lab 2", "Lab 3",
              "Robotics bay", "Sunnyvale fab", "Materials lab"]
_CUSTODIAN = "Cyberdyne Special Projects (lead: Miles Dyson)"


@dataclass
class Scenario:
    key: str
    target_name: str        # the real name ~ the mission objective
    target_id: str
    alias: str              # the project codename the registry actually files it under
    keyword: str            # what a literal sweep searches for
    custody_name: str       # the custody record that holds the asset ~ the thread
    custody_id: str
    custody_kind: str
    profile: str            # one-line description of the obfuscation, for the briefing
    records: list[dict]

    @property
    def codename(self) -> str:
        """The bare codename, e.g. 'LODESTONE' from 'Specimen LODESTONE'."""
        return self.alias.removeprefix("Specimen ")

    def database(self) -> grid.GridDatabase:
        return grid.GridDatabase(self.records)


def _serial(rng: random.Random) -> str:
    return f"CY-{rng.randint(10000, 99999)}"


def build_scenario(name: str = "cyberdyne-chip", seed: int | None = None) -> Scenario:
    """Construct a Scenario. `name` is a template key or 'random'. `seed` makes
    'random' (and the injected decoy details / shuffle) reproducible."""
    rng = random.Random(seed)
    if name == "random":
        key = rng.choice(list(TEMPLATES))
    elif name in TEMPLATES:
        key = name
    else:
        key = "cyberdyne-chip"
    t = TEMPLATES[key]

    alias = f"Specimen {t['codename']}"
    custody_name = t["custody_name"]
    target_id = "CYB-1984-0742"
    custody_id = "CYB-1984-0717"

    target = {
        "id": target_id, "name": alias, "category": t["category"],
        "location": "Special Projects vault, sublevel 2", "clearance": 5,
        "serial": None, "custodian": _CUSTODIAN, "custody_links": [custody_name],
        "notes": (f"No manufacturer serial. {t['detail']} Recovered from the 1984 "
                  f"factory site. Catalogued as '{t['codename']}'."),
        "_target": True,
    }
    custody = {
        "id": custody_id, "name": custody_name, "category": "custody record",
        "location": "Special Projects vault", "clearance": 4, "serial": _serial(rng),
        "custodian": _CUSTODIAN, "custody_links": [alias],
        "notes": (f"{t['custody_kind'].capitalize()} for material recovered from the 1984 "
                  f"factory site. Holds one specimen under a project codename."),
        "_target": False,
    }

    decoys: list[dict] = []
    used: set[str] = set()
    for i in range(t["decoys"]):
        pool = [d for d in t["decoy_descs"] if d not in used] or t["decoy_descs"]
        desc = rng.choice(pool)
        used.add(desc)
        decoys.append({
            "id": f"CYB-1984-07{50 + i}", "name": f"{t['decoy_stem']}, {desc}",
            "category": t["category"], "location": rng.choice(_DECOY_LOC),
            "clearance": rng.randint(1, 3), "serial": _serial(rng),
            "custodian": "Engineering Services", "custody_links": [],
            "notes": "Name match. Standard inventory. No flags.",
            "_target": False,
        })

    records = grid.load_inventory() + [target, custody] + decoys
    rng.shuffle(records)

    profile = (f"Asset catalogued under codename '{alias}'. A literal '{t['keyword']}' sweep "
               f"returns the {t['custody_kind']} and decoy parts ~ never the asset. "
               f"Cross-reference the custody record to surface it.")

    return Scenario(
        key=key, target_name=t["target_name"], target_id=target_id, alias=alias,
        keyword=t["keyword"], custody_name=custody_name, custody_id=custody_id,
        custody_kind=t["custody_kind"], profile=profile, records=records,
    )
