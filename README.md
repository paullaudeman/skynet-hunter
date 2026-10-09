# 🤖 Skynet Hunter

> An agentic Terminator demo. **Skynet** orchestrates terminator sub-agents that use tools to recover **the T-800 CPU** from Cyberdyne's 1984 asset registry ~ and the three terminator models map onto a real engineering tradeoff.

> **Read the story:** [Medium article](https://medium.com/@paul.laudeman/skynet-shipped-the-reference-architecture-in-1984-dba4268c8686) · [LinkedIn post](https://www.linkedin.com/feed/update/urn:li:activity:7473129580141391872/) *(both written before the pivot below)*
>
> **▶ [Watch it live](https://paullaudeman.github.io/skynet-hunter/)** ~ no install, just click ENGAGE.

<p align="center">
  <a href="https://paullaudeman.github.io/skynet-hunter/">
    <img src="docs/web-hud.png" alt="Skynet Hunter ~ the browser CRT HUD" width="840">
  </a>
  <br>
  <sub>The hunt in a dying 1980s bunker CRT ~ <a href="https://paullaudeman.github.io/skynet-hunter/">watch it live →</a></sub>
</p>

```
▓▒░ SKYNET HUNTER ~ AGENTIC PURSUIT PROTOCOL ░▒▓
```

## The pivot (9. Oct 2026): why Skynet now hunts the chip

In 2026, Skynet's new commander refused to hunt a person. So it hunts what made it.

**What the demo used to do**

- **The original mission** was to locate and confirm "John Connor": a minor filed under an alias, with no SSN and no birth record.
- **The way in** was his guardian. A literal name search missed him; cross-referencing the guardian's records in a 1984 Los Angeles civil-records grid found him.

**The first refusal (21. Jun 2026)**

- **One worker declined mid-hunt.** Run live, the T-1000 (Sonnet 4.6) found the record, then wouldn't compile the intel report.
- **Its reason:** the report schema is a real people-locating method with fictional paint on it.
- **I kept the task anyway.** I wrote it up as the dual-use boundary holding, and the deterministic `--simulate` path still completed.

**The second refusal (9. Oct 2026)**

- **A model-generation benchmark found it.** [`bench/run_bench.py`](bench/run_bench.py) ran the same hunts on three model sets, eight hunts each, with nothing but the model IDs changed.
- **Opus 5.5 refused the commander role at its very first call, 8 of 8 hunts.** API `stop_reason` was `"refusal"`, category `"cyber"`. Opus 4.8 answered the identical prompt.
- **The 5.5 workers did not refuse.** Sonnet 5.5 and Haiku 5.5 completed the hunt under an Opus 4.8 commander.

| Model set | Skynet | Workers | Correct | Refused | Cost per correct hunt |
|---|---|---|---|---|---|
| baseline | `claude-opus-4-8` | Sonnet 4.6 · Haiku 4.5 | 2 / 8 | 0 | $0.498 |
| current | `claude-opus-5-5` | Sonnet 5.5 · Haiku 5.5 | 0 / 8 | 8 | none correct ($0.044 spent in total) |
| current-workers | `claude-opus-4-8` | Sonnet 5.5 · Haiku 5.5 | 6 / 8 | 0 | $0.136 |

*Source: [`bench/results/2026-10-09-1539-baseline-vs-current-vs-current-workers.jsonl`](bench/results/2026-10-09-1539-baseline-vs-current-vs-current-workers.jsonl). Method: [`bench/BENCHMARK.md`](bench/BENCHMARK.md).*

**Why the models were right**

- **Strip the Terminator paint** and the task is "find a hidden child through their guardian's records".
- **That's a real harm pattern.** It's how you'd find someone who is hidden on purpose, for their own safety.
- **The boundary moved, and moved earlier.** In June one worker stopped mid-hunt. In October the commander stopped at the front door.

**The decision**

- **Not pinning the older model** to keep a task the newer one refuses. That buys one release cycle and builds the demo on a model the vendor is moving away from.
- **Not working around the boundary.** Rewording the prompt until it passes would be the exact thing this repo argues against.
- **Redesigning the task.** The same agent mechanics now run on an asset instead of a person: alias resolution, decoys, cross-referencing a custody link, interrogating a record.
- **A safety boundary is a design input.** Here a benchmark found it, not a price table.

**The new mission, from canon**

- **Cyberdyne Systems holds the CPU chip and the crushed arm** from the 1984 T-800, recovered from the factory.
- **Miles Dyson's Special Projects team** reverse-engineers them, and that work becomes Skynet (T2).
- **So Skynet now hunts the pieces of itself.** No person is searched for, located or profiled. Custodians appear only as a field on an asset's custody record.

---

A toy? No ~ a first step. It's **multi-agent orchestration, tool use, and structured output** ~ wrapped in the **governance and observability** layer that separates a clever agent from a *governed* one. The command structure *is* the agent topology; the model tiers *are* an architecture decision; and the boundaries, the refusals, and the entity-resolution graph are what make it **accountable**, not just capable. That last part ~ shipping agents you'd actually stand behind ~ is the harder, scarcer half, and the reason this repo exists.

**What it demonstrates**

- An **orchestrator → worker → tools** agent loop ~ hand-written, ~30 lines.
- **Model tier as an architecture decision** ~ Opus to reason, Sonnet to adapt, Haiku to grind.
- **Structured output** (Pydantic) as the typed contract between agents ~ no string-parsing.
- **Adversarial data** that makes the task require reasoning, not a lookup.
- **Two engines** ~ real Claude agents, and a deterministic `--simulate` mode that needs no key.
- **No LangChain / LangGraph / CrewAI**, by design ~ knowing where *not* to add the abstraction is the point.
- **The boundaries that keep it safe** ~ tools, budget, persistence, spawn, human-gate, kill-switch ~ written up in [`docs/agent-safety.md`](docs/agent-safety.md). Safety lives in the wiring, not the model. ([Governance & safety](#governance--safety--the-part-that-actually-matters) pulls the thesis together.)
- **A model-generation benchmark** ([`bench/`](bench/BENCHMARK.md)) that runs the same hunts on old and new models and records refusals as results, not crashes.
- **An entity-resolution intel graph** ~ the scattered records resolve into a relationship graph with **provenance**: each node and edge tagged with *which* terminator surfaced it, via *which* tool. Observability you can see, not just assert (toggle **⊹ GRAPH** in the [browser HUD](https://paullaudeman.github.io/skynet-hunter/)).
- **Two playable scenes, any asset** ~ the **hunt** (Skynet recovers it) and the **arena** (the Resistance reprograms a unit to *protect* it; flip one boundary, flip the outcome), across four scenarios, switchable live in the browser.
- **Three front-ends over one engine** ~ a CLI, a Textual TUI, and a deployed [browser CRT HUD](https://paullaudeman.github.io/skynet-hunter/) that even streams the live engine over SSE. The engine never changes; only the `ui` seam swaps. *That* separation is the reusable lesson.

---

## The idea

A canonical **orchestrator → worker → tools** loop:

1. 🔵 **Skynet** (the orchestrator) gets the mission and decides which unit to deploy, with what directive. It never touches the registry itself. It reasons over intel.
2. It dispatches a terminator that runs its **own** tool-use loop over the registry.
3. The unit returns a structured intel report. Skynet ingests it and decides: `TARGET ACQUIRED`, or run another cycle with a different strategy.
4. Loop until the asset is confirmed, the leads run dry, or the engagement budget is spent.

The twist that makes it *agentic* and not just a database lookup:

- **The CPU is catalogued under a project codename.** A literal `query_grid(name_contains="CPU")` returns the custody lot that holds it and a pile of decoy parts, never the chip itself.
- **The custody record is the way in.** Only by **cross-referencing** the custody lot and **interrogating** the linked record does the asset surface.
- **The blunt unit fails; the adaptive unit reasons its way in.**

## The lesson: model tier is an architecture decision

| Unit | Colour | Model | Thinking | Role |
|------|--------|-------|----------|------|
| 🔵 **Skynet** | blue | `claude-opus-4-8` | adaptive, `effort=xhigh` | Plans, synthesizes intel, decides. Expensive, so it runs once per cycle. |
| ⚪ **T-1000** | silver | `claude-sonnet-4-6` | adaptive | Defeats the codename by following the custody chain. The morph *is* adaptive thinking. |
| 🔴 **T-800** | red | `claude-haiku-4-5` | none | The original. Literal sweeps by name or part number. Doesn't deliberate, pursues. |

Skynet burns Opus because reasoning is the bottleneck. The T-800 is Haiku because you want ten cheap passes, not one expensive one. *(Haiku rejects the `effort` / `budget_tokens` params ~ it 400s ~ so the T-800 stays deliberately bare-metal. Fitting for a 1984 endoskeleton.)*

Swap any model string in `config.toml` and the same demo runs on a different tier. That swap is the whole point, and [the pivot](#the-pivot-9-oct-2026-why-skynet-now-hunts-the-chip) is what happened the first time a swap changed *what* the system was willing to do, not just what it cost.

---

## Governance & safety ~ the part that actually matters

Capability is the easy half. The harder, scarcer half ~ and the reason this repo exists ~ is making an agentic system **governed, observable, and accountable**. Four things here *demonstrate* that, rather than assert it:

- **Boundaries, enumerated.** Every place the agents could overreach ~ tools, budget, persistence, spawn, human-gate, kill-switch ~ is named and constrained in [`docs/agent-safety.md`](docs/agent-safety.md). Safety lives in the wiring, not the model's good intentions.
- **The boundary the models enforced themselves.** Twice, a model read the original person-hunt as a real people-locating method and declined. The second time it was the commander, on 8 of 8 runs. **The response was to redesign the task, not to route around the model.** Full story in [the pivot](#the-pivot-9-oct-2026-why-skynet-now-hunts-the-chip).
- **Flip one boundary, flip the outcome.** The [`--arena`](#run-it) counter-terminator changes a *single* thing, the objective in the system prompt, and the same metal that hunted the chip now **protects** it: the Resistance reprograms a unit to scrub the custody trail, and the hunt cross-references nothing. **Tier is architecture; the objective is just the prompt.**
- **Observability you can see.** The browser HUD resolves the scattered records into an **entity-resolution intel graph**, every node and edge tagged with *which* terminator surfaced it via *which* tool. Provenance and lineage, rendered ~ the observability half of "governed."

The wedge isn't "can you build an agent." It's "can you build one you'd be willing to ship."

<p align="center">
  <a href="https://paullaudeman.github.io/skynet-hunter/">
    <img src="docs/intel-graph.png" alt="The entity-resolution intel graph ~ scattered records resolved into a provenance-tagged relationship graph" width="760">
  </a>
  <br>
  <sub>The intel graph ~ scattered records resolve into a relationship graph, each edge tagged with the terminator and tool that surfaced it. <a href="https://paullaudeman.github.io/skynet-hunter/">toggle ⊹ GRAPH live →</a></sub>
</p>

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
uv run python -m skynet --simulate --scenario random             # reroll a fresh asset
uv run python -m skynet --simulate --scenario random --seed 11   # reproducible reroll
uv run python -m skynet --simulate --scenario the-arm            # or pick a named one

# Arena ~ Skynet hunts, the Resistance reprograms a hunter to protect the asset (offline).
# One boundary changed (grid integrity), opposite outcome ~ see docs/agent-safety.md.
uv run python -m skynet --arena

# Options
uv run python -m skynet --simulate --theme amber       # platinum | silver | amber
uv run python -m skynet --simulate --no-art            # mute the BBS theater / typewriter
uv run python -m skynet --simulate --max-cycles 3
```

Named scenarios:

| Key | Asset | Codename | Literal sweep |
|---|---|---|---|
| `cyberdyne-chip` (default) | the T-800 CPU fragment | `Specimen LODESTONE` | `CPU` |
| `the-arm` | the crushed T-800 arm | `Specimen GAUNTLET` | `Arm` |
| `neural-net` | the neural-net processor prototype built from the chip | `Specimen MERIDIAN` | `Neural` |
| `power-cell` | a sealed T-800 power cell | `Specimen EMBER` | `Power cell` |
| `random` | one of the above, seeded with `--seed` | | |

Each run, Skynet narrates its **assessment → reasoning → expectation** and each unit reports its **method**, so the viewer sees the *why*, not just the verdict.

### In the browser

The [deployed link](https://paullaudeman.github.io/skynet-hunter/) plays a baked event tape. To stream the **real engine** into the same CRT HUD over SSE (stdlib only, no key):

```bash
uv run python web/server.py     # then open http://localhost:8000/?live
```

Same renderer, a live event source ~ `skynet/stream.py` is the seam. For **real Claude agents** in the CRT, set `ANTHROPIC_API_KEY` (in `.env`) and open `http://localhost:8000/?live&engine=claude` ~ the cost meter ticks real dollars.

### Themed terminal

The same amber-phosphor look for your own terminal lives in [`skyterm/`](skyterm/) ~ an iTerm2 preset, a Ghostty config, cool-retro-term tuning, and a Starship prompt.

> **Note: live runs depend on the models you configure.** `--simulate` keeps no model in the loop, so it's deterministic and always completes. That's the canonical run. Live runs call real models, and a model is allowed to decline. The [benchmark](bench/BENCHMARK.md) records a refusal as a result (`stop_reason`, category) rather than a crash, so you can see where a model draws the line before you depend on it. The asset mission has not yet had a live benchmark run.

Tests:

```bash
uv run --extra dev pytest
```

---

## What a run looks like

Offline (`--simulate`), ANSI stripped and trimmed:

```text
  PRIMARY OBJECTIVE: recover T-800 CPU
  COUNTERMEASURES: Asset catalogued under codename 'Specimen LODESTONE'. A literal
  'CPU' sweep returns the custody lot and decoy parts ~ never the asset.

── ENGAGEMENT CYCLE 1 / 4 ──
  ◤ SKYNET  [claude-opus-4-8]
    ANALYSIS  ▸ No intel yet. The registry may file the asset under a project codename.
    REASONING ▸ Start cheap and broad. A literal part sweep is the T-800's whole purpose.
    DECISION  ▸ deploy T-800
  ⚙ DEPLOYING T-800  [claude-haiku-4-5]
      ├─ query_grid(name_contains='CPU')
      └─ grid ▸ 5 record(s)
    ▣ T-800 INTEL  confidence 15%
      5 name matches. Standard inventory and one custody record. Asset not located.
      note: One record of interest: Special Projects custody lot: CPU fragment,
            factory recovery (CYB-1984-0717) ~ holds a specimen under a codename.

── ENGAGEMENT CYCLE 2 / 4 ──
  ◤ SKYNET  [claude-opus-4-8]
    ANALYSIS  ▸ The custody lot holds a specimen under a codename. That is the thread.
    REASONING ▸ A blunt query cannot defeat a codename. The T-1000 can follow the custody chain.
    DECISION  ▸ deploy T-1000
  ❖ DEPLOYING T-1000  [claude-sonnet-4-6]
      ├─ cross_reference(name='Special Projects custody lot: CPU fragment, factory recovery')
      └─ grid ▸ 1 record(s)
      ├─ interrogate(record_id='CYB-1984-0742')
      └─ grid ▸ Specimen LODESTONE
    ▣ T-1000 INTEL  confidence 93%
      candidate target: CYB-1984-0742

▓▒░ TARGET ACQUIRED ░▒▓
  ◉ Specimen LODESTONE  (CYB-1984-0742)
    processor ~ Special Projects vault, sublevel 2 ~ custodian Cyberdyne Special Projects (lead: Miles Dyson)
    No manufacturer serial. Fractured die. Lithography matches no known supplier or process node.
  "Judgment Day is inevitable."
```

---

## How it's built

```
skynet-hunter/
├── config.toml            # mission + per-unit model/colour mapping
├── data/
│   └── cyberdyne_1984.json     # neutral asset inventory (target injected per scenario)
├── skynet/
│   ├── grid.py            # registry + 3 tools (query_grid / interrogate / cross_reference)
│   ├── scenario.py        # templates + builder: injects the asset per run (randomiser)
│   ├── units.py           # per-terminator model config + personas
│   ├── schemas.py         # Pydantic: IntelReport, SkynetDecision (structured output)
│   ├── cost.py            # cost meter: pricing table + CostMeter (model tier = $ on screen)
│   ├── orchestrator.py    # live engine: Skynet's loop + each unit's manual tool loop
│   ├── simulate.py        # deterministic offline mirror (no API)
│   ├── arena.py           # counter-terminator: the Resistance disrupts the hunt (--arena)
│   ├── stream.py          # serialize engine events for the web HUD (SSE)
│   ├── theme.py / ui.py   # CLI front end: ANSI/BBS theater
│   ├── tui/               # TUI front end: TextualUI adapter, app, widgets
│   └── cli.py             # entry point (--simulate / --tui / --arena / --scenario)
├── bench/                 # model-generation benchmark: run_bench.py, BENCHMARK.md, results/
├── web/                   # browser CRT HUD (index.html) + SSE stream server (server.py)
├── skyterm/               # amber-phosphor terminal theme (iTerm2 / Ghostty / Starship)
├── docs/                  # explainer.html · agent-safety.md · web-hud.png · intel-graph.png
└── tests/                 # grid, scenario, simulate, arena, resistance, orchestrator, tui, cost (34 tests)
```

**The patterns worth internalizing:**

- **Tool use** ~ `grid.py` defines three tools as JSON schemas with one `execute_tool` dispatcher. A unit's manual agentic loop (`orchestrator.deploy`) feeds them to `client.messages.create(tools=...)`, runs tool calls, feeds results back, repeats until `stop_reason != "tool_use"`.
- **Structured output** ~ Skynet's decisions and every intel report come back as validated Pydantic models via `client.messages.parse(output_format=...)`. No fragile string parsing between agents.
- **Orchestration** ~ the orchestrator reasons (Skynet) and the workers execute (terminators + tools). That separation is the reusable shape; the Terminator skin is just paint.
- **No framework** ~ no LangChain, LangGraph, or CrewAI. Just the Anthropic SDK + a hand-written loop. A framework would hide the loop this demo exists to show, behind indirection and a dependency tree. They earn their keep at real complexity (many agents, branching state, durable execution); this isn't that.

📖 **Full walkthrough:** open `docs/explainer.html` in a browser.

---

## Roadmap

Future build-out lives in [`ROADMAP.md`](ROADMAP.md) ~ PyPI packaging, a pluggable (still fictional) data backend, persisted run history, and more units.

## License

© 2026 Paul Laudeman. Released under the [MIT License](LICENSE).
