"""Structured-output schemas shared by the live orchestrator and the simulator.

Using the same Pydantic models for both engines means the UI renders identical
shapes whether the intel came from a real Claude call or the scripted path.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IntelReport(BaseModel):
    """What a deployed terminator returns to Skynet."""

    unit: str = Field(description="Designation of the reporting unit, e.g. 'T-800'.")
    method: str = Field(default="", description="How you searched ~ which tools, in what order, and why.")
    summary: str = Field(description="One or two sentences on what the unit did and found.")
    records_examined: list[str] = Field(default_factory=list, description="Record ids inspected.")
    candidate_record_ids: list[str] = Field(default_factory=list, description="Possible matches.")
    target_record_id: str | None = Field(default=None, description="Confirmed target id, if found.")
    confidence: float = Field(description="0.0 to 1.0 confidence the target was identified.")
    notes: str = Field(default="", description="Reasoning, dead ends, anything Skynet should weigh.")


class SkynetDecision(BaseModel):
    """Skynet's next-action decision after weighing the intel so far."""

    assessment: str = Field(description="What the intel gathered so far tells you ~ read the board for the viewer.")
    reasoning: str = Field(description="Why this is the right next move, given the assessment.")
    target_acquired: bool = Field(description="True only when the target is confirmed.")
    target_record_id: str | None = Field(default=None, description="The confirmed target's id.")
    deploy_unit: str | None = Field(default=None, description="'T-800' or 'T-1000' to deploy next, else null.")
    directive: str | None = Field(default=None, description="The order issued to the deployed unit.")
    expectation: str | None = Field(default=None, description="What you expect the deployed unit to achieve.")
