"""The grid ~ Cyberdyne Systems' 1984 asset registry plus the three tools the
terminators use to search it.

This module is the learning core. The tools are plain functions with JSON-Schema
definitions (`TOOL_SCHEMAS`) and a single `execute_tool` dispatcher ~ exactly the
shape a manual agentic loop feeds to `client.messages.create(tools=...)`.

The target (the T-800 CPU recovered from the 1984 factory) is deliberately
unreachable by a literal name query. `query_grid(name_contains="CPU")` returns
the custody lot that holds it and a pile of decoy parts but NOT the asset itself
~ it is catalogued under a project codename. Only `cross_reference` from the
custody record, followed by `interrogate`, surfaces it. That gap is what
separates the blunt T-800 from the adaptive T-1000.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "cyberdyne_1984.json"

# Fields returned by a broad query ~ never the custody detail.
_SUMMARY_FIELDS = ("id", "name", "category", "location", "clearance")


class GridDatabase:
    """Loads the records and answers the three tool calls. Pure + testable."""

    def __init__(self, records: list[dict[str, Any]]):
        self.records = records
        self._by_id = {r["id"]: r for r in records}

    @classmethod
    def load(cls, path: Path | str = DATA_PATH) -> "GridDatabase":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data["records"])

    # -- tool: query_grid -------------------------------------------------
    def query(
        self,
        name_contains: str | None = None,
        category: str | None = None,
        location: str | None = None,
        clearance_min: int | None = None,
        clearance_max: int | None = None,
    ) -> list[dict[str, Any]]:
        """Blunt filter. Returns SUMMARY fields only (no serial, custody, notes)."""
        out = []
        for r in self.records:
            if name_contains and name_contains.lower() not in r["name"].lower():
                continue
            if category and category.lower() not in r["category"].lower():
                continue
            if location and location.lower() not in r["location"].lower():
                continue
            if clearance_min is not None and r["clearance"] < clearance_min:
                continue
            if clearance_max is not None and r["clearance"] > clearance_max:
                continue
            out.append({k: r[k] for k in _SUMMARY_FIELDS})
        return out

    # -- tool: interrogate ------------------------------------------------
    def interrogate(self, record_id: str) -> dict[str, Any]:
        """Full record for one id ~ minus the internal `_target` flag."""
        r = self._by_id.get(record_id)
        if r is None:
            return {"error": f"No record with id {record_id!r}."}
        return {k: v for k, v in r.items() if k != "_target"}

    # -- tool: cross_reference -------------------------------------------
    def cross_reference(self, name: str) -> list[dict[str, Any]]:
        """Find records that list `name` in their custody chain.

        This is the path to the target: the codename record lists its custody
        lot in `custody_links`, so cross_reference('<custody lot>') surfaces it
        even though a name query for 'CPU' never would.
        """
        needle = name.lower().strip()
        out = []
        for r in self.records:
            for link in r.get("custody_links", []):
                if needle in link.lower():
                    out.append(
                        {"id": r["id"], "name": r["name"], "linked_via": link}
                    )
                    break
        return out

    # -- Resistance tool: scrub_flag --------------------------------------
    def scrub_flag(self, record_id: str) -> dict[str, Any]:
        """Resistance counter-tool: erase a custody record's specimen flag and
        sever its custody links in BOTH directions. This breaks the
        cross_reference path the hunter relies on ~ the thread simply vanishes.
        """
        r = self._by_id.get(record_id)
        if r is None:
            return {"error": f"No record with id {record_id!r}."}
        needle = r["name"].lower()
        severed: list[str] = []
        for other in self.records:
            if other is r:
                continue
            before = other.get("custody_links", [])
            kept = [a for a in before if needle not in a.lower()]
            if len(kept) != len(before):
                other["custody_links"] = kept
                severed.append(other["id"])
        r["custody_links"] = []
        r["notes"] = "Record sanitized. No specimen held under this lot."
        return {
            "id": record_id,
            "severed_links_to": sorted(set(severed)),
            "status": "flag scrubbed; custody links severed",
        }

    # -- Resistance tool: re_alias ----------------------------------------
    def re_alias(self, record_id: str, new_name: str) -> dict[str, Any]:
        """Resistance counter-tool: refile a record under a fresh codename. A
        hunter that cached the old name, or re-queries it, now finds nothing."""
        r = self._by_id.get(record_id)
        if r is None:
            return {"error": f"No record with id {record_id!r}."}
        old = r["name"]
        r["name"] = new_name
        return {"id": record_id, "old_name": old, "new_name": new_name, "status": "re-aliased"}


# --- Tool schemas (what the model sees) ---------------------------------
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "query_grid",
        "description": (
            "Search Cyberdyne's asset registry by simple filters. Returns only "
            "summary fields (id, name, category, location, clearance). A literal "
            "name search will miss any asset catalogued under a project codename."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name_contains": {"type": "string", "description": "Substring of the catalogue name or part number."},
                "category": {"type": "string"},
                "location": {"type": "string"},
                "clearance_min": {"type": "integer"},
                "clearance_max": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "interrogate",
        "description": (
            "Pull the FULL vault record for one id: serial, custodian, "
            "custody_links, and notes. Use this to inspect a candidate asset and "
            "read its custody chain."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"record_id": {"type": "string"}},
            "required": ["record_id"],
        },
    },
    {
        "name": "cross_reference",
        "description": (
            "Find every record that lists the given name in its custody chain. "
            "The way to reach an asset catalogued under a codename is to "
            "cross-reference the custody record that holds it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
]


# --- Resistance counter-tools (the protector agent's WRITE surface) ------
# Deliberately separate from TOOL_SCHEMAS: the hunters never see these. The
# Resistance orchestrator deploys a protector that mutates the grid mid-hunt to
# break the trail ~ this is the adversarial-multi-agent escalation.
RESISTANCE_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "scrub_flag",
        "description": (
            "Erase a custody record's specimen flag and sever its custody links. "
            "Use this on the custody lot to break the trail a hunter would follow "
            "by cross-referencing it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"record_id": {"type": "string"}},
            "required": ["record_id"],
        },
    },
    {
        "name": "re_alias",
        "description": (
            "Refile an asset under a fresh codename so a hunter who cached or "
            "re-queries the old name finds nothing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string"},
                "new_name": {"type": "string", "description": "The new codename to file under."},
            },
            "required": ["record_id", "new_name"],
        },
    },
]


def execute_tool(db: GridDatabase, name: str, tool_input: dict[str, Any]) -> str:
    """Dispatch a tool call to the database. Returns a JSON string (tool_result)."""
    if name == "query_grid":
        result: Any = db.query(**tool_input)
    elif name == "interrogate":
        result = db.interrogate(tool_input["record_id"])
    elif name == "cross_reference":
        result = db.cross_reference(tool_input["name"])
    elif name == "scrub_flag":
        result = db.scrub_flag(tool_input["record_id"])
    elif name == "re_alias":
        result = db.re_alias(tool_input["record_id"], tool_input["new_name"])
    else:
        result = {"error": f"Unknown tool {name!r}."}
    return json.dumps(result, ensure_ascii=False)


def load_inventory(path: Path | str = DATA_PATH) -> list[dict[str, Any]]:
    """Return just the neutral background inventory. The target asset, its
    custody record, and the name-match decoys are injected per scenario by
    `scenario.build_scenario`."""
    return json.loads(Path(path).read_text(encoding="utf-8"))["records"]
