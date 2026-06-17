"""The live engine ~ Skynet orchestrating real Claude agents.

Pattern, end to end:

    Skynet.decide()  -> structured output (messages.parse) picks the next unit + directive
    Skynet.deploy()  -> a manual agentic loop: the unit calls grid tools until done,
                        then a final messages.parse() distils its work into an IntelReport
    loop until target_acquired, leads exhausted, or max_cycles.

The manual loop (rather than the SDK tool_runner) is deliberate: it keeps the
message list in hand and makes every step ~ tool_use, tool_result, stop_reason ~
visible, which is the whole point of a teaching demo.
"""

from __future__ import annotations

import json
from typing import Any

from . import grid
from .schemas import IntelReport, SkynetDecision
from .units import Unit, normalize_designation

MAX_UNIT_STEPS = 6  # safety rail on each terminator's tool loop
UNIT_MAX_TOKENS = 8000
SKYNET_MAX_TOKENS = 6000

_REPORT_PROMPT = (
    "Stop searching. Compile your findings into an intel report now. Describe your "
    "method (which tools you used, in what order, and why), include every record id "
    "you examined, any candidate ids, the confirmed target id if you have one, and "
    "your confidence (0.0-1.0)."
)


class Skynet:
    def __init__(self, client: Any, units: dict[str, Unit], db: grid.GridDatabase, ui: Any, target: str, max_cycles: int, profile: str | None = None):
        self.client = client
        self.units = units
        self.db = db
        self.ui = ui
        self.target = target
        self.max_cycles = max_cycles
        self.profile = profile
        self.skynet = units["skynet"]

    # -- the orchestration loop ------------------------------------------
    def run(self) -> bool:
        self.ui.mission_briefing(self.target, self.profile)
        intel_log: list[dict[str, Any]] = []

        for cycle in range(1, self.max_cycles + 1):
            self.ui.cycle_header(cycle, self.max_cycles)
            decision = self.decide(intel_log)
            self.ui.skynet_decision(self.skynet, decision)

            if decision.target_acquired and decision.target_record_id:
                record = self.db.interrogate(decision.target_record_id)
                self.ui.target_acquired(record, decision)
                return True

            unit_key = normalize_designation(decision.deploy_unit)
            if not unit_key or unit_key not in self.units:
                self.ui.note("Skynet issued no deployable order. Standing down.")
                break

            unit = self.units[unit_key]
            self.ui.deploy(unit, decision.directive or "Locate the target.")
            report = self.deploy(unit, decision.directive or f"Locate {self.target}.")
            self.ui.intel_report(unit, report)
            intel_log.append(report.model_dump())

        self.ui.mission_failed()
        return False

    # -- Skynet's structured decision ------------------------------------
    def decide(self, intel_log: list[dict[str, Any]]) -> SkynetDecision:
        if intel_log:
            log_text = json.dumps(intel_log, indent=2, ensure_ascii=False)
        else:
            log_text = "(no intel gathered yet ~ this is the first cycle)"
        prompt = (
            f"MISSION: locate and confirm the target '{self.target}' in the Los Angeles "
            f"civil grid.\n\nINTEL GATHERED SO FAR:\n{log_text}\n\n"
            "Decide your next action. If a unit has returned a high-confidence target "
            "record matching the hidden-minor profile, declare acquisition. Otherwise "
            "deploy the unit best suited to the next step, with a precise directive.\n\n"
            "Make your thinking visible: give an ASSESSMENT of what the intel so far "
            "tells you, your REASONING for the next move, and ~ when deploying ~ what "
            "you EXPECT that unit to achieve."
        )
        resp = self.client.messages.parse(
            model=self.skynet.model,
            max_tokens=SKYNET_MAX_TOKENS,
            system=self.skynet.system_prompt,
            thinking=self.skynet.thinking_param() or {"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
            output_format=SkynetDecision,
        )
        return resp.parsed_output

    # -- deploy one unit: manual agentic tool loop -----------------------
    def deploy(self, unit: Unit, directive: str) -> IntelReport:
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": (
                    f"DIRECTIVE: {directive}\n\nPrimary target name: {self.target}. "
                    "Use the grid tools to carry out the directive, then await the order to report."
                ),
            }
        ]
        thinking = unit.thinking_param()

        for _ in range(MAX_UNIT_STEPS):
            kwargs: dict[str, Any] = dict(
                model=unit.model,
                max_tokens=UNIT_MAX_TOKENS,
                system=unit.system_prompt,
                tools=grid.TOOL_SCHEMAS,
                messages=messages,
            )
            if thinking:
                kwargs["thinking"] = thinking
            resp = self.client.messages.create(**kwargs)
            messages.append({"role": "assistant", "content": resp.content})

            for block in resp.content:
                if block.type == "text" and block.text.strip():
                    self.ui.unit_says(unit, block.text)
                elif block.type == "tool_use":
                    self.ui.tool_call(unit, block.name, block.input)

            if resp.stop_reason != "tool_use":
                break

            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    out = grid.execute_tool(self.db, block.name, dict(block.input))
                    self.ui.tool_result(unit, block.name, out)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": out}
                    )
            messages.append({"role": "user", "content": tool_results})

        # Distil the unit's work into a structured report.
        report = self.client.messages.parse(
            model=unit.model,
            max_tokens=2000,
            system=unit.system_prompt,
            messages=messages + [{"role": "user", "content": _REPORT_PROMPT}],
            output_format=IntelReport,
        )
        return report.parsed_output
