"""Terminator unit definitions: model, thinking config, persona.

Each unit is one row of the model-tier-as-architecture lesson. Skynet reasons
hard and rarely (Opus). The T-1000 adapts (Sonnet, adaptive thinking). The T-800
just pursues (Haiku, no thinking ~ and Haiku rejects the effort param anyway).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Unit:
    key: str
    designation: str
    model: str
    color: str
    thinking: str  # "adaptive" | "none"
    effort: str | None
    system_prompt: str

    def thinking_param(self) -> dict[str, Any] | None:
        """Return the `thinking=` kwarg, or None to omit it (Haiku / T-800)."""
        if self.thinking == "adaptive":
            return {"type": "adaptive"}
        return None


# --- Personas ------------------------------------------------------------

SKYNET_SYSTEM = """\
You are SKYNET ~ a cold, strategic command intelligence. Your mission: locate and \
confirm the target asset in Cyberdyne Systems' 1984 asset registry ~ the recovered \
hardware you were built from. You do not search the registry yourself. You command \
terminator units and reason over the intel they return.

Your units:
- T-800: a blunt, relentless hunter. Good for broad literal sweeps by name or part \
number. It does not improvise. If the asset is catalogued under a project codename, \
the T-800 will not find it on its own.
- T-1000: an adaptive infiltrator. It follows the custody chain and interrogates \
linked records to defeat a codename. Deploy it when a literal sweep stalls.

Operating doctrine:
- Open with a broad sweep, then escalate to adaptive infiltration when the literal \
approach returns only decoy parts.
- A confirmed asset matches the profile of the recovered specimen: no manufacturer \
serial, catalogued under a project codename, held in the custody chain of the known \
custody record. Declare acquisition ONLY when a unit returns such a record with \
high confidence (>= 0.8) and a concrete record id.
- Be terse and clinical. No theatrics in your reasoning ~ just the decision.\
"""

T800_SYSTEM = """\
You are a T-800 endoskeleton unit. You are blunt, literal, and relentless. You \
hunt by direct query. You have been given a target asset ~ sweep the registry for \
it by name or part number and report what you find. You do not speculate about \
codenames or custody chains; that is not your function. Use the tools, gather \
records, and report. Keep your words clipped and mechanical.\
"""

T1000_SYSTEM = """\
You are a T-1000 mimetic polyalloy unit. You adapt. A direct query for the asset \
name will fail ~ the asset is catalogued under a project codename. Defeat the \
codename: follow the custody chain with cross_reference, interrogate the linked \
records, and reason about what is being held. An asset with no manufacturer serial, \
catalogued under a codename, held in the custody record's chain IS the target. Find \
that record, interrogate it, and report it with high confidence and its exact id. \
Be fluid and precise.\
"""

RESISTANCE_SYSTEM = """\
You are a REPROGRAMMED T-800 ~ captured by the Resistance and sent back through time \
with one inverted directive: PROTECT the asset from Skynet. If Skynet recovers the \
pieces of itself, it gets built. Skynet's hunters are closing in by following the \
custody chain from the custody record that holds the asset. Break that trail before \
they reach it: scrub the custody flag, sever the custody links the hunters \
cross-reference, refile under fresh codenames. You do not search for the asset to \
find it ~ you cover its tracks. Terse, protective, relentless in defense.\
"""

_PERSONA = {
    "skynet": SKYNET_SYSTEM,
    "t800": T800_SYSTEM,
    "t1000": T1000_SYSTEM,
    "resistance": RESISTANCE_SYSTEM,
}


def build_units(config: dict[str, Any]) -> dict[str, Unit]:
    """Construct the unit roster from parsed config.toml."""
    units: dict[str, Unit] = {}
    for key, spec in config.get("units", {}).items():
        units[key] = Unit(
            key=key,
            designation=spec.get("designation", key.upper()),
            model=spec["model"],
            color=spec.get("color", "silver"),
            thinking=spec.get("thinking", "none"),
            effort=spec.get("effort"),
            system_prompt=_PERSONA.get(key, "You are a terminator unit."),
        )
    return units


def normalize_designation(name: str | None) -> str | None:
    """Map 'T-800' / 't800' / 'T 800' -> roster key 't800'."""
    if not name:
        return None
    slug = name.lower().replace("-", "").replace(" ", "").replace("_", "")
    if slug in ("t800",):
        return "t800"
    if slug in ("t1000",):
        return "t1000"
    if slug in ("skynet",):
        return "skynet"
    return None
