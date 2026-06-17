# 🤖 Skynet Hunter

> An agentic Terminator demo. **Skynet** orchestrates terminator sub-agents that use tools to hunt **John Connor** across a synthetic 1984 Los Angeles grid ~ and the three terminator models map onto a real engineering tradeoff.

```
▓▒░ SKYNET HUNTER ~ AGENTIC PURSUIT PROTOCOL ░▒▓
```

It's a toy with a real lesson inside it: **multi-agent orchestration, tool use, and structured output**, costumed as a Skynet command hierarchy. The command structure *is* the agent topology. The model tiers *are* an architecture decision.

---

## The idea

A canonical **orchestrator → worker → tools** loop:

1. 🔵 **Skynet** (the orchestrator) gets the mission and decides which unit to deploy, with what directive. It never touches the grid itself ~ it reasons over intel.
2. It dispatches a terminator that runs its **own** tool-use loop over the grid.
3. The unit returns a structured intel report. Skynet ingests it and decides: `TARGET ACQUIRED`, or run another cycle with a different strategy.
4. Loop until the target is confirmed, the leads run dry, or the engagement budget is spent.

The twist that makes it *agentic* and not just a database lookup: John Connor is **concealed**. A literal `query_grid(name_contains="Connor")` returns his mother and a pile of decoys ~ never him. He's filed under an alias. Only by **cross-referencing** a known associate (Sarah Connor) and **interrogating** the linked record does the target surface. The blunt unit fails; the adaptive unit reasons its way in.

## The lesson: model tier is an architecture decision

| Unit | Colour | Model | Thinking | Role |
|------|--------|-------|----------|------|
| 🔵 **Skynet** | blue | `claude-opus-4-8` | adaptive, `effort=xhigh` | Plans, synthesizes intel, decides. Expensive ~ runs once per cycle. |
| ⚪ **T-1000** | silver | `claude-sonnet-4-6` | adaptive | The morph *is* adaptive thinking ~ it reshapes its search when brute force stalls. |
| 🔴 **T-800** | red | `claude-haiku-4-5` | none | The original. Blunt, relentless, cheap, literal. Doesn't deliberate ~ pursues. |

Skynet burns Opus because reasoning is the bottleneck. The T-800 is Haiku because you want ten cheap passes, not one expensive one. *(Haiku rejects the `effort` / `budget_tokens` params ~ it 400s ~ so the T-800 stays deliberately bare-metal. Fitting for a 1984 endoskeleton.)*

Swap any model string in `config.toml` and the same demo runs on a different tier. That swap is the whole point.

---

## Run it

Needs [uv](https://docs.astral.sh/uv/).

```bash
# Offline ~ deterministic, no API key, no credit spent. Start here.
uv run python -m skynet --simulate

# Live ~ real Claude agents calling tools. Needs a key.
cp .env.example .env          # then paste your ANTHROPIC_API_KEY
uv run python -m skynet

# Interactive TUI ~ a 3-pane HUD (Textual). Press r to engage, q to quit.
uv run python -m skynet --tui
uv run python -m skynet --tui --scenario random

# Scenario randomiser ~ a different hunt each run
uv run python -m skynet --simulate --scenario random        # reroll a fresh target
uv run python -m skynet --simulate --scenario random --seed 11   # reproducible reroll
uv run python -m skynet --simulate --scenario danny-dyson   # or pick a named one

# Options
uv run python -m skynet --simulate --theme amber       # platinum | silver | amber
uv run python -m skynet --simulate --no-art            # mute the BBS theater / typewriter
uv run python -m skynet --simulate --max-cycles 3
```

Named scenarios: `john-connor` (default), `danny-dyson`, `blair-brewster`, `eli-vega`, or `random`. Each run, Skynet narrates its **assessment → reasoning → expectation** and each unit reports its **method**, so the viewer sees the *why*, not just the verdict.

Tests:

```bash
uv run --extra dev pytest
```

---

## How it's built

```
skynet-hunter/
├── config.toml            # mission + per-unit model/effort/colour mapping
├── data/
│   └── los_angeles_1984.json   # synthetic grid; target obfuscated, surrounded by decoys
├── skynet/
│   ├── grid.py            # the dataset + 3 tools (query_grid / interrogate / cross_reference)
│   ├── units.py           # per-terminator model config + personas
│   ├── schemas.py         # Pydantic: IntelReport, SkynetDecision (structured output)
│   ├── orchestrator.py    # the live engine: Skynet's loop + each unit's manual tool loop
│   ├── simulate.py        # deterministic offline mirror (no API)
│   ├── theme.py / ui.py   # ANSI/BBS theater: boot, HUD, typewriter, colour-coded output
│   └── cli.py             # argparse entry point
├── docs/explainer.html    # self-contained visual explainer (intro / concepts / implementation)
└── tests/
```

**The three patterns worth internalizing:**

- **Tool use** ~ `grid.py` defines three tools as JSON schemas with one `execute_tool` dispatcher. A unit's manual agentic loop (`orchestrator.deploy`) feeds them to `client.messages.create(tools=...)`, runs tool calls, feeds results back, repeats until `stop_reason != "tool_use"`.
- **Structured output** ~ Skynet's decisions and every intel report come back as validated Pydantic models via `client.messages.parse(output_format=...)`. No fragile string parsing between agents.
- **Orchestration** ~ the orchestrator reasons (Skynet) and the workers execute (terminators + tools). That separation is the reusable shape; the Terminator skin is just paint.

📖 **Full walkthrough:** open `docs/explainer.html` in a browser.

---

## Roadmap

Future build-out lives in [`ROADMAP.md`](ROADMAP.md) ~ PyPI packaging, a live OSINT grid, persisted run history, and more units.

## License

MIT.
