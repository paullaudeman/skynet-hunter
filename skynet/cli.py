"""Command-line entry point.

    python -m skynet              live pursuit (needs ANTHROPIC_API_KEY)
    python -m skynet --simulate   offline, deterministic, no key
    python -m skynet --theme amber --no-art --max-cycles 3
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

try:  # stdlib on 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from . import scenario, simulate
from .theme import Theme
from .ui import UI
from .units import build_units

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config.toml"


def load_config(path: Path | str) -> dict[str, Any]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Tiny .env loader ~ avoids a dependency. Only sets unset keys."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skynet",
        description="Agentic Terminator demo: Skynet hunts the recovered T-800 CPU across a synthetic 1984 Cyberdyne asset registry.",
    )
    p.add_argument("--simulate", action="store_true", help="Run offline (no API key, deterministic).")
    p.add_argument("--arena", action="store_true", help="Two-orchestrator arena ~ Skynet hunts, the Resistance disrupts (offline).")
    p.add_argument("--tui", action="store_true", help="Launch the interactive Textual TUI (offline).")
    p.add_argument("--theme", choices=["platinum", "silver", "amber"], help="Override the terminal theme.")
    p.add_argument("--scenario", choices=scenario.SCENARIO_CHOICES, default="cyberdyne-chip",
                   help="Which hunt to run. 'random' rerolls a fresh scenario.")
    p.add_argument("--seed", type=int, help="Seed for --scenario random (reproducible rerolls).")
    p.add_argument("--archive", action="store_true",
                   help="Attach the 1984 document archive (search_archive): a second route to the target.")
    p.add_argument("--archive-kb", metavar="KB_ID",
                   help="Use a Bedrock Knowledge Base as the archive instead of the local one (implies --archive).")
    p.add_argument("--guardrail", metavar="ID:VERSION",
                   help="Gate archive results with Bedrock Guardrails (numbered version, never DRAFT).")
    p.add_argument("--aws-region", help="Region for --archive-kb / --guardrail. Always explicit.")
    p.add_argument("--record", action="store_true",
                   help="Write an evidence bundle to runs/<session_id>/ (always on for live runs).")
    p.add_argument("--no-record", action="store_true", help="Live runs only: skip the evidence bundle.")
    p.add_argument("--max-cycles", type=int, help="Override the engagement budget.")
    p.add_argument("--no-art", action="store_true", help="Mute the BBS theater / typewriter delays.")
    p.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to config.toml.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)

    max_cycles = args.max_cycles or config["mission"]["max_cycles"]
    theme_name = args.theme or config["theme"]["name"]

    sc = scenario.build_scenario(args.scenario, seed=args.seed)
    target = sc.target_name
    db = sc.database()

    theme = Theme(theme_name)
    ui = UI(theme, art=not args.no_art)
    units = build_units(config)
    store = None
    cloud = bool(args.archive_kb or args.guardrail)
    if (args.archive or cloud) and (args.tui or args.arena):
        sys.stderr.write("  --archive is not wired into --tui or --arena yet. Use it with --simulate or a live run.\n")
        return 1
    if cloud and args.simulate:
        # --simulate promises no spend; a Knowledge Base or Guardrail would bill every search.
        sys.stderr.write("  --archive-kb and --guardrail call AWS and bill per search; --simulate never spends. Drop one.\n")
        return 1
    if cloud:
        if not args.aws_region:
            sys.stderr.write("  --archive-kb and --guardrail need an explicit --aws-region.\n")
            return 1
        try:
            import boto3  # noqa: F401
        except ModuleNotFoundError:
            sys.stderr.write("  The AWS archive needs boto3: uv sync --extra aws\n")
            return 1
        from . import archive_aws
        gate = None
        if args.guardrail:
            gid, sep, ver = args.guardrail.partition(":")
            if not (gid and sep and ver):
                sys.stderr.write("  --guardrail takes ID:VERSION, e.g. abc123:1 (a numbered version, never DRAFT).\n")
                return 1
            from .archive import LocalGate, UnionGate
            # both gates, withhold on either (probe, 10. Oct 2026: they miss different attacks)
            gate = UnionGate([LocalGate(), archive_aws.BedrockGuardrailGate(gid, ver, args.aws_region)])
        if args.archive_kb:
            store = archive_aws.BedrockKBEvidenceStore(args.archive_kb, sc.key, args.aws_region, gate=gate)
        else:
            from .archive import LocalEvidenceStore, build_archive
            store = LocalEvidenceStore(build_archive(sc, seed=args.seed))
            store.gate = gate
    elif args.archive:
        from .archive import LocalEvidenceStore, build_archive
        store = LocalEvidenceStore(build_archive(sc, seed=args.seed))

    if args.tui:
        from .tui.app import run_tui
        run_tui(units, sc, max_cycles)
        return 0

    if args.arena:
        from . import arena
        arena.run_arena_simulation(units, sc, ui, max_cycles)
        return 0

    # Evidence bundle: on for live runs (they cost money; the record must not be missing),
    # opt-in for --simulate. Wrapping only records; what the model and the screen get is unchanged.
    from .orchestrator import new_session_id
    session_id = new_session_id(target)
    rec = None
    if args.record or (not args.simulate and not args.no_record):
        from .evidence import EvidenceRecorder, RecordingStore, RecordingUI
        rec = EvidenceRecorder(session_id, mode="simulate" if args.simulate else "live",
                               scenario=sc.key, seed=args.seed, target=target,
                               models={k: u.model for k, u in units.items()},
                               archive=None if store is None else type(store).__name__,
                               gate=None if store is None else type(getattr(store, "gate", None)).__name__)
        ui = RecordingUI(ui, rec)
        if store is not None:
            store = RecordingStore(store, rec)

    def bundle_done(outcome: str, **extra) -> None:
        if rec is not None:
            path = rec.finish(outcome, **extra)
            sys.stderr.write(theme.paint("dim", f"\n  evidence ▸ {path.parent}\n"))

    if args.simulate:
        ok = simulate.run_simulation(units, sc, ui, max_cycles, archive=store)
        bundle_done("acquired" if ok else "failed")
        ui.hold()
        return 0

    # Live path needs a key.
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.stderr.write(
            theme.paint("bad", "\n  No ANTHROPIC_API_KEY found.\n", bold=True)
            + theme.paint("dim", "  Set it (or copy .env.example to .env), or run the offline demo:\n")
            + theme.paint("accent", "      python -m skynet --simulate\n\n")
        )
        return 1

    from .client import make_client  # lazy ~ keeps --simulate dependency-light
    from .orchestrator import Skynet

    client = make_client()
    ui.boot()
    skynet = Skynet(client, units, db, ui, target, max_cycles, profile=sc.profile,
                    session_id=session_id, archive=store)
    acquired = False
    try:
        acquired = skynet.run()
    finally:
        # a crashed run still leaves its evidence
        refusal = skynet.refusal
        outcome = "acquired" if acquired else ("refused" if refusal else "failed")
        if rec is not None and rec.cost is None:
            rec.cost = {"total_cost": round(skynet.meter.total_cost, 6), "estimated": skynet.meter.estimated}
        bundle_done(outcome, refusal=refusal)
    gate = getattr(store, "gate", None)
    if getattr(gate, "errors", 0):
        sys.stderr.write(theme.paint("bad", f"\n  Guardrail errors: {gate.errors}. Those documents were withheld (fail closed).\n"))
    ui.hold()
    return 0 if acquired else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
