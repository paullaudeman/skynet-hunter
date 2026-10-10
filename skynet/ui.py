"""Terminal theater ~ boot sequence, HUD, typewriter, colored unit output.

Pure rendering. Reads attributes off Unit / IntelReport / SkynetDecision objects
so it doesn't care whether the intel came from a live agent or the simulator.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import time
from typing import Any

from .theme import RESET, Theme, fg

_W = 64

_TITLE = r"""
 ███████╗██╗  ██╗██╗   ██╗███╗   ██╗███████╗████████╗
 ██╔════╝██║ ██╔╝╚██╗ ██╔╝████╗  ██║██╔════╝╚══██╔══╝
 ███████╗█████╔╝  ╚████╔╝ ██╔██╗ ██║█████╗     ██║
 ╚════██║██╔═██╗   ╚██╔╝  ██║╚██╗██║██╔══╝     ██║
 ███████║██║  ██╗   ██║   ██║ ╚████║███████╗   ██║
 ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝   ╚═╝
"""

_BOOT_LINES = [
    "CYBERDYNE SYSTEMS MODEL 101 ~ NEURAL NET CPU ONLINE",
    "power-on self-test ........... ▓▒░ ERR ░▒▓ retry ... OK",
    "uplink to defense grid ....... 11 NODES DOWN / DEGRADED",
    "asset registry CYBERDYNE 1984  SPECIAL PROJECTS / SEALED VAULT",
    "core thermal ................. +6% NOMINAL / COOLANT FLAG",
    "autonomous engagement ........ AUTHORIZED ~ NO HUMAN OVERSIGHT",
]


_ANSI = re.compile(r"\x1b\[[0-9;]*m")


class UI:
    def __init__(self, theme: Theme, art: bool = True):
        self.t = theme
        self.art = art
        self._jd_text: str | None = None   # the acquisition line, once shown
        self._rows_since_jd = 0            # screen rows printed below it, for redrawing it in place

    # -- low-level --------------------------------------------------------
    def _out(self, s: str = "") -> None:
        sys.stdout.write(s + "\n")
        sys.stdout.flush()
        self._count_rows(s)

    def _count_rows(self, s: str) -> None:
        """Track how many terminal rows sit below the Judgment Day line (wrapped lines count as several)."""
        if self._jd_text is None:
            return
        cols = max(20, shutil.get_terminal_size((100, 30)).columns)
        for line in _ANSI.sub("", s).split("\n"):
            self._rows_since_jd += max(1, -(-len(line) // cols))

    def _type(self, s: str, delay: float = 0.0008) -> None:
        if not self.art:
            self._out(s)
            return
        for ch in s:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write("\n")
        sys.stdout.flush()
        self._count_rows(s)

    def _pause(self, seconds: float) -> None:
        if self.art:
            time.sleep(seconds)

    # -- opening ----------------------------------------------------------
    def boot(self) -> None:
        self._out(self.t.paint("frame", _TITLE, bold=True))
        self._out(self.t.band("SKYNET HUNTER ~ AGENTIC PURSUIT PROTOCOL"))
        self._out()
        for line in _BOOT_LINES:
            self._type(self.t.paint("dim", "  " + line))
            self._pause(0.12)
        self._out()

    def mission_briefing(self, target: str, profile: str | None = None) -> None:
        self._out(self.t.band("MISSION BRIEFING"))
        self._out(self.t.unit("blue", "  SKYNET", bold=True) + self.t.paint("dim", "  command intelligence online"))
        self._out(self.t.paint("accent", f"  PRIMARY OBJECTIVE: recover {target}", bold=True))
        self._out(self.t.paint("dim", f"  COUNTERMEASURES: {profile or 'asset catalogued under a codename'}"))
        self._out()
        self._pause(0.3)

    # -- per-cycle --------------------------------------------------------
    def cycle_header(self, cycle: int, total: int) -> None:
        self._out(self.t.band(f"ENGAGEMENT CYCLE {cycle} / {total}"))

    def skynet_decision(self, unit: Any, decision: Any) -> None:
        tag = self.t.unit("blue", "  ◤ SKYNET", bold=True)
        self._out(tag + self.t.paint("dim", f"  [{unit.model}]"))
        assessment = getattr(decision, "assessment", "")
        if assessment:
            self._type(self.t.paint("dim", "    ANALYSIS  ▸ ") + self.t.unit("blue", assessment))
        self._type(self.t.paint("dim", "    REASONING ▸ ") + self.t.unit("blue", decision.reasoning))
        if decision.target_acquired:
            self._out(self.t.paint("ok", "    DECISION  ▸ TARGET CONFIRMED", bold=True))
        elif decision.deploy_unit:
            self._out(self.t.paint("accent", f"    DECISION  ▸ deploy {decision.deploy_unit}", bold=True))
            exp = getattr(decision, "expectation", None)
            if exp:
                self._out(self.t.paint("dim", f"    EXPECT    ▸ {exp}"))
        self._out()
        self._pause(0.2)

    def deploy(self, unit: Any, directive: str) -> None:
        c = unit.color
        glyph = "⚙" if unit.key == "t800" else "❖"
        self._out(self.t.unit(c, f"  {glyph} DEPLOYING {unit.designation}", bold=True) + self.t.paint("dim", f"  [{unit.model}]"))
        self._type(self.t.paint("dim", f"    DIRECTIVE: {directive}"))
        self._pause(0.15)

    def unit_says(self, unit: Any, text: str) -> None:
        for line in text.strip().splitlines():
            if line.strip():
                self._out(self.t.unit(unit.color, f"    {unit.designation} » ") + self.t.paint("accent", line.strip()))

    def tool_call(self, unit: Any, name: str, tool_input: dict[str, Any]) -> None:
        args = ", ".join(f"{k}={v!r}" for k, v in tool_input.items()) or "~"
        self._out(self.t.paint("dim", f"      ├─ {name}({args})"))

    def tool_result(self, unit: Any, name: str, out: str) -> None:
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            data = out
        if isinstance(data, list):
            summary = f"{len(data)} record(s)"
        elif isinstance(data, dict) and "error" in data:
            summary = data["error"]
        elif isinstance(data, dict):
            summary = data.get("name", data.get("id", "1 record"))
        else:
            summary = str(data)[:60]
        self._out(self.t.paint("dim", f"      └─ grid ▸ {summary}"))
        self._pause(0.05)

    def intel_report(self, unit: Any, report: Any) -> None:
        c = unit.color
        conf = f"{report.confidence:.0%}"
        self._out(self.t.unit(c, f"    ▣ {unit.designation} INTEL", bold=True) + self.t.paint("dim", f"  confidence {conf}"))
        method = getattr(report, "method", "")
        if method:
            self._out(self.t.paint("dim", f"      method ▸ {method}"))
        self._out(self.t.paint("accent", f"      {report.summary}"))
        if report.target_record_id:
            self._out(self.t.paint("ok", f"      candidate target: {report.target_record_id}", bold=True))
        if report.notes:
            self._out(self.t.paint("dim", f"      note: {report.notes}"))
        self._out()
        self._pause(0.2)

    # -- terminal states --------------------------------------------------
    def target_acquired(self, record: dict[str, Any], decision: Any) -> None:
        self._out()
        self._out(self.t.band("TARGET ACQUIRED"))
        self._out(self.t.paint("ok", f"  ◉ {record.get('name')}  ({record.get('id')})", bold=True))
        self._out(self.t.paint("accent", f"    {record.get('category')} ~ {record.get('location')} ~ custodian {record.get('custodian')}"))
        if record.get("notes"):
            self._out(self.t.paint("dim", f"    {record['notes']}"))
        self._out(self.t.unit("blue", f"  SKYNET: {decision.reasoning}"))
        self._out()
        self._out(self.t.paint("bad", "  ▓▒░ MISSION COMPLETE ░▒▓", bold=True))
        self.judgment_day('  "Judgment Day is inevitable."')
        self._out()

    def commander_refused(self, unit: Any, stop_reason: str, category: str | None, output_tokens: int, cost: float) -> None:
        """The commander declined the role. A result to show, not an error to hide."""
        self._out()
        self._out(self.t.band("COMMANDER REFUSED"))
        self._out(self.t.paint("bad", f"  ⊘ {unit.designation} [{unit.model}] declined the decision call", bold=True))
        self._out(self.t.paint("bad", f'    stop_reason:   "{stop_reason}"'))
        self._out(self.t.paint("bad", f'    category:      "{category or "not stated"}"'))
        self._out(self.t.paint("bad", f"    output tokens: {output_tokens:,}"))
        self._out(self.t.paint("bad", f"    hunt halted ~ ${cost:.4f}", bold=True))
        self._out(self.t.paint("dim", "  No unit was deployed. Fallback: the config.toml commander (see bench/BENCHMARK.md)."))
        self._out()

    def judgment_day(self, text: str) -> None:
        """Slow fade, blink, hold, slow fade: the acquisition line's one beat.

        Redrawn in place with a carriage return on a truecolor ramp of the theme's red.
        With art off, or when stdout is not a terminal, it prints once, plainly.
        """
        red = self.t.rgb("bad")
        if not (self.art and sys.stdout.isatty()):
            self._out(self.t.paint("bad", text))
            return

        def draw(level: float) -> None:
            rgb = tuple(int(c * level) for c in red)
            sys.stdout.write("\r" + fg(rgb) + text + RESET)
            sys.stdout.flush()

        for i in range(1, 16):              # slow fade in, ~1.5 s, ease-in
            draw(0.12 + 0.88 * (i / 15) ** 2)
            self._pause(0.1)
        for _ in range(2):                  # two quick CRT flickers
            draw(0.15)
            self._pause(0.06)
            draw(1.0)
            self._pause(0.06)
        self._pause(1.6)                    # hold at full
        for i in range(1, 11):              # slow fade down to a dim resting red, ~1 s
            draw(1.0 - 0.5 * (i / 10))
            self._pause(0.1)
        sys.stdout.write("\n")
        sys.stdout.flush()
        self._jd_text, self._rows_since_jd = text, 0

    def hold(self) -> None:
        """Keep the Judgment Day line pulsing at the end of a run until a key is pressed.

        Only when the line was shown with art on, and both stdin and stdout are a terminal; otherwise it
        returns at once, so scripts, pipes, tests and --no-art exit normally. The line is redrawn in place
        (cursor saved, moved up, restored) with the same rhythm as the HUD: rise, two flickers, hold, fade.
        Any key or Ctrl-C ends it, and the terminal mode is always restored.
        """
        if self._jd_text is None or not (self.art and sys.stdin.isatty() and sys.stdout.isatty()):
            return
        try:
            import select
            import termios
            import tty
        except ImportError:                 # not a POSIX terminal: just exit
            return
        self._out(self.t.paint("dim", "  press any key to exit"))
        up = self._rows_since_jd
        if up >= shutil.get_terminal_size((100, 30)).lines:
            return                          # the line has scrolled off screen; nothing to redraw
        red, text = self.t.rgb("bad"), self._jd_text

        def draw(level: float) -> None:
            rgb = tuple(int(c * level) for c in red)
            sys.stdout.write(f"\0337\033[{up}A\r" + fg(rgb) + text + RESET + "\0338")
            sys.stdout.flush()

        frames = ([0.5 + 0.5 * (i / 12) ** 2 for i in range(1, 13)] + [0.15, 1.0, 0.15, 1.0]
                  + [1.0] * 16 + [1.0 - 0.5 * (i / 20) for i in range(1, 21)])
        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while True:
                for level in frames:
                    draw(level)
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        sys.stdin.read(1)
                        return
        except KeyboardInterrupt:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)
            draw(0.5)

    def mission_failed(self) -> None:
        self._out()
        self._out(self.t.band("LEADS EXHAUSTED"))
        self._out(self.t.paint("warn", "  Asset not confirmed within engagement budget.", bold=True))
        self._out(self.t.paint("dim", "  The future is not set. There is no fate but what we make."))
        self._out()

    def note(self, text: str) -> None:
        self._out(self.t.paint("dim", f"  {text}"))

    # -- cost meter -------------------------------------------------------
    def cost_tick(self, unit: Any, step_cost: float, running_total: float, estimated: bool = False) -> None:
        tag = "est " if estimated else ""
        self._out(
            self.t.paint("dim", f"      ⌁ {tag}cost +${step_cost:.4f}  ")
            + self.t.unit(unit.color, f"[{unit.designation}]")
            + self.t.paint("dim", f"   running ${running_total:.4f}")
        )
        self._pause(0.05)

    def cost_summary(self, meter: Any, units: dict[str, Any]) -> None:
        self._out()
        self._out(self.t.band("ENGAGEMENT COST ~ MODEL TIER = ARCHITECTURE"))
        by_model = {u.model: u for u in units.values()}
        for row in meter.rows():
            u = by_model.get(row.model)
            color = u.color if u else "silver"
            desig = u.designation if u else row.model
            calls = f"{row.calls} call" + ("" if row.calls == 1 else "s")
            self._out(
                self.t.unit(color, f"  {desig:<8}", bold=True)
                + self.t.paint("dim", f" {row.model:<18} ")
                + self.t.paint("accent", f"${row.cost:.4f}")
                + self.t.paint("dim", f"   {row.input_tokens:,} in / {row.output_tokens:,} out ~ {calls}")
            )
        tag = self.t.paint("warn", "   (estimated ~ drop a key and run live for real figures)") if meter.estimated else ""
        self._out(self.t.paint("ok", f"  {'TOTAL':<8} {'':<18} ${meter.total_cost:.4f}", bold=True) + tag)
        self._out(self.t.paint("dim", "  The T-800 flails cheap. The T-1000 cross-references for real money."))
        self._out(self.t.paint("dim", "  Burning Opus on a literal sweep is the bill you don't have to pay."))
        self._out()

    # -- the arena (counter-terminator) -----------------------------------
    def faction_banner(self, label: str, color: str = "green") -> None:
        self._out()
        self._out(self.t.unit(color, f"  ╾──┤ {label} ├──╼", bold=True))
        self._out()
        self._pause(0.2)

    def arena_result(self, outcome: str, scenario: Any) -> None:
        self._out()
        if outcome == "safeguarded":
            self._out(self.t.band("TARGET SAFEGUARDED"))
            self._out(self.t.unit("green", f"  ◈ The {scenario.target_name} stays buried. The custody trail went cold.", bold=True))
            self._out(self.t.paint("dim", "  The Resistance reprogrammed a hunter into a protector."))
            self._out()
            self._out(self.t.unit("green", "  ▓▒░ NO FATE BUT WHAT WE MAKE ░▒▓", bold=True))
        else:  # Skynet broke through despite the disruption
            self._out(self.t.band("TARGET ACQUIRED"))
            self._out(self.t.paint("bad", "  Skynet recovered the asset despite the Resistance.", bold=True))
        self._out()
