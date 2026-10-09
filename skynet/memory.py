"""The IntelStore seam ~ Ports & Adapters applied to AgentCore Memory.

Brick 1 of the AgentCore migration. The orchestrator's reasoning loop should
depend on an *interface* for storing and recalling intel, not on a raw list it
mutates in place. That interface (the "port") is shaped deliberately like
AgentCore Memory's own API ~ create_event / retrieve ~ so the eventual cloud
port is "write an AgentCoreIntelStore adapter and swap one line," not a redesign.

LocalIntelStore is the trivial local adapter: an in-memory dict keyed by
session. It is behaviour-identical to the list the orchestrator used before ~
retrieve returns every event for the session, in insertion order, no reorder,
no dedupe. Brick 1 ignores `query` on purpose; honouring it is a later brick
(semantic recall). Changing the returned order/shape now would change decide()'s
prompt and therefore the model's path ~ which is the one thing this refactor
must not do.
"""

from __future__ import annotations

from typing import Any, Protocol


class IntelStore(Protocol):
    """Port: how the orchestrator stores and recalls intel.

    Shaped after AgentCore Memory (create_event / retrieve) so the managed
    adapter is a drop-in swap behind this same interface.
    """

    def create_event(self, session: str, actor: str, report: dict[str, Any]) -> None:
        """Append one intel event (a unit's report) to the session's record."""
        ...

    def retrieve(self, session: str, query: str | None = None) -> list[dict[str, Any]]:
        """Return the session's intel. Brick 1: all events, in order, query ignored."""
        ...


class LocalIntelStore:
    """In-memory adapter ~ behaviour-identical to the orchestrator's old list.

    Keyed by session so one process can host many hunts without cross-talk ~
    the same per-session isolation AgentCore Memory gives you for free.
    """

    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}

    def create_event(self, session: str, actor: str, report: dict[str, Any]) -> None:
        # `actor` is accepted to match the AgentCore Memory shape, but Brick 1
        # stores only the report ~ folding actor into the payload would change
        # what decide() serialises into its prompt. A later brick can use it.
        self._events.setdefault(session, []).append(report)

    def retrieve(self, session: str, query: str | None = None) -> list[dict[str, Any]]:
        # Brick 1: all events for the session, in insertion order. No reorder,
        # no dedupe ~ decide() must see exactly what the old list held.
        return self._events.get(session, [])
