"""The grid ~ synthetic 1984 LA civil records plus the three tools the
terminators use to search it.

This module is the learning core. The tools are plain functions with JSON-Schema
definitions (`TOOL_SCHEMAS`) and a single `execute_tool` dispatcher ~ exactly the
shape a manual agentic loop feeds to `client.messages.create(tools=...)`.

The target (John Connor) is deliberately unreachable by a literal name query.
`query_grid(name_contains="Connor")` returns his mother and a pile of decoys but
NOT him ~ he is filed under an alias. Only `cross_reference` from a known
associate, followed by `interrogate`, surfaces the record. That gap is what
separates the blunt T-800 from the adaptive T-1000.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "los_angeles_1984.json"

# Fields returned by a broad query ~ never the sensitive ones.
_SUMMARY_FIELDS = ("id", "name", "age", "occupation", "location")


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
        occupation: str | None = None,
        location: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
    ) -> list[dict[str, Any]]:
        """Blunt filter. Returns SUMMARY fields only (no ssn, associates, notes)."""
        out = []
        for r in self.records:
            if name_contains and name_contains.lower() not in r["name"].lower():
                continue
            if occupation and occupation.lower() not in r["occupation"].lower():
                continue
            if location and location.lower() not in r["location"].lower():
                continue
            if age_min is not None and r["age"] < age_min:
                continue
            if age_max is not None and r["age"] > age_max:
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
        """Find records that list `name` among their known associates.

        This is the path to the target: the alias record lists 'Sarah Connor'
        as an associate, so cross_reference('Sarah Connor') surfaces it even
        though a name query for 'Connor' never would.
        """
        needle = name.lower().strip()
        out = []
        for r in self.records:
            for assoc in r.get("known_associates", []):
                if needle in assoc.lower():
                    out.append(
                        {"id": r["id"], "name": r["name"], "linked_via": assoc}
                    )
                    break
        return out

    # -- Resistance tool: scrub_flag --------------------------------------
    def scrub_flag(self, record_id: str) -> dict[str, Any]:
        """Resistance counter-tool: erase a record's dependent-minor flag and
        sever its concealed associate links in BOTH directions. This breaks the
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
            before = other.get("known_associates", [])
            kept = [a for a in before if needle not in a.lower()]
            if len(kept) != len(before):
                other["known_associates"] = kept
                severed.append(other["id"])
        r["known_associates"] = []
        r["notes"] = "Record sanitized. No dependent-minor flag on file."
        return {
            "id": record_id,
            "severed_links_to": sorted(set(severed)),
            "status": "flag scrubbed; associate links severed",
        }

    # -- Resistance tool: re_alias ----------------------------------------
    def re_alias(self, record_id: str, new_name: str) -> dict[str, Any]:
        """Resistance counter-tool: refile a record under a fresh alias. A hunter
        that cached the old name, or re-queries it, now finds nothing."""
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
            "Search the civil grid by simple filters. Returns only summary "
            "fields (id, name, age, occupation, location). A literal name search "
            "will miss anyone filed under an alias."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name_contains": {"type": "string", "description": "Substring of the name."},
                "occupation": {"type": "string"},
                "location": {"type": "string"},
                "age_min": {"type": "integer"},
                "age_max": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "interrogate",
        "description": (
            "Pull the FULL record for one id: ssn, known_associates, and notes. "
            "Use this to inspect a candidate and read its associate links."
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
            "Find every record that lists the given name among its known "
            "associates. The way to reach someone hiding under an alias is to "
            "cross-reference a person they are connected to."
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
            "Erase a record's dependent-minor flag and sever its concealed "
            "associate links. Use this on the protector to break the trail a "
            "hunter would follow by cross-referencing them."
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
            "Refile a record under a fresh alias so a hunter who cached or "
            "re-queries the old name finds nothing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string"},
                "new_name": {"type": "string", "description": "The new alias to file under."},
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


def load_civilians(path: Path | str = DATA_PATH) -> list[dict[str, Any]]:
    """Return just the neutral civilian population. The target, protector, and
    surname-decoys are injected per scenario by `scenario.build_scenario`."""
    return json.loads(Path(path).read_text(encoding="utf-8"))["records"]
