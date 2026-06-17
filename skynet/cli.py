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
        description="Agentic Terminator demo: Skynet hunts John Connor across a synthetic 1984 LA grid.",
    )
    p.add_argument("--simulate", action="store_true", help="Run offline (no API key, deterministic).")
    p.add_argument("--theme", choices=["platinum", "silver", "amber"], help="Override the terminal theme.")
    p.add_argument("--scenario", choices=scenario.SCENARIO_CHOICES, default="john-connor",
                   help="Which hunt to run. 'random' rerolls a fresh scenario.")
    p.add_argument("--seed", type=int, help="Seed for --scenario random (reproducible rerolls).")
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

    if args.simulate:
        simulate.run_simulation(units, sc, ui, max_cycles)
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

    import anthropic  # lazy ~ keeps --simulate dependency-light

    from .orchestrator import Skynet

    client = anthropic.Anthropic()
    ui.boot()
    skynet = Skynet(client, units, db, ui, target, max_cycles, profile=sc.profile)
    acquired = skynet.run()
    return 0 if acquired else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
