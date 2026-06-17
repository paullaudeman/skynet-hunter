# Roadmap

First pass shipped the full agentic demo (3 units, adversarial grid, both engines, ANSI/BBS theater, synced HTML explainer). These are deliberate **out-of-scope** items held for future build-out.

## Deferred from first pass

| Idea | Why it was deferred | What it would add |
|------|--------------------|-------------------|
| **PyPI packaging** | Runs fine via `uv run` / `python -m skynet` for now | `pipx install skynet-hunter`; a real console entry point for non-devs |
| **Live OSINT / real grid** | The synthetic grid is the point ~ safe, deterministic, no targeting of real people | A pluggable data backend (still fictional sources) to show tool-use against changing data |
| **Persisted run history** | Each run is self-contained | A `runs/` log of every pursuit (decisions, intel, cost) for replay + a cost dashboard |

## Other directions worth a look

- **More units** ~ a T-X (hybrid) on a 4th model; a Resistance counter-agent that actively obfuscates records mid-hunt (adversarial multi-agent).
- **Streaming output** ~ render live tokens under the colour theme via `messages.stream()` + `.get_final_message()` instead of per-turn batches.
- **Cost meter** ~ surface `usage` per call so the model-tier tradeoff is visible in dollars on screen.
- **asciinema cast** ~ record the live run for the README so the GitHub page shows the theater without a key.
- **Difficulty levels** ~ deeper obfuscation (multi-hop association chains) that force more cycles and reward the adaptive unit harder.
- **Web TUI** ~ a browser front end mirroring the HUD for a shareable link.

## Bigger swing: a Skynet-themed MUD 🌐

A persistent, hostable, multiplayer Skynet world you can actually log into and play. This is the natural evolution of the orchestration pattern ~ same bones, more agents and state:

- **The grid becomes a world.** Rooms, zones, a real map of 1984 LA (and the post-Judgment-Day future) instead of a flat record set.
- **Terminators become live NPCs.** Each is an agent on its own model tier, patrolling, hunting, adapting ~ the T-1000 actually stalks you across rooms.
- **Skynet becomes the dungeon master.** The orchestrator runs the world: spawns units, escalates the hunt, narrates. Players are the Resistance.
- **Persistence + multiplayer.** Telnet/SSH or a websocket front end, a tick loop, saved world state, multiple players sharing the same hunt.
- **Tech sketch:** asyncio server + a tick scheduler; the existing `units.py` / tool patterns carry over; per-NPC agent loops gated by cost (cheap models for ambient NPCs, Opus only for the boss). The current `--simulate` discipline becomes "scripted NPCs" for a no-key local server.

Effectively: this demo is the combat encounter; the MUD is the whole game around it.
