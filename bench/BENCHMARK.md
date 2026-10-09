# Model-generation benchmark

Runs the live orchestrator on the same hunts with different model sets and records what each set does. Harness: [`run_bench.py`](run_bench.py). Results: `results/*.jsonl`, one JSON object per hunt.

## Method

**Held fixed across sets**

- Engine code (`skynet/`), tools, personas and the `decide()` / report prompts.
- `config.toml` everything except model IDs: `max_cycles = 4`, thinking and effort per unit.
- Scenario templates and record ids (`target_id` is always `CYB-1984-0742`).
- Order: hunts are interleaved by scenario, then set, so time-of-day load hits every set alike.

**Not held fixed**

- Scenarios are built without a seed, so decoy picks and record order vary between hunts.
- Model sampling. Use `--repeats` to see the spread.

**Model sets** (`MODEL_SETS` in `run_bench.py`). Roles keep their tiers; only the generation changes.

| Set | skynet | t1000 | t800 / resistance |
|---|---|---|---|
| `baseline` | `claude-opus-4-8` | `claude-sonnet-4-6` | `claude-haiku-4-5` |
| `current` | `claude-opus-5-5` | `claude-sonnet-5-5` | `claude-haiku-5-5` |
| `current-workers` | `claude-opus-4-8` | `claude-sonnet-5-5` | `claude-haiku-5-5` |

**Outcome classes** (`outcome` field, first match wins)

- `refused`: any call in the hunt returned `stop_reason == "refusal"`. The `refusals` field keeps model and category.
- `error`: an exception ended the hunt and no refusal was logged.
- `correct`: Skynet acquired `target_id`.
- `wrong`: Skynet acquired a different id.
- `not found`: the cycle budget ran out, or Skynet stood down.

**Cost per correct hunt** = total `cost_usd` of the set ÷ number of `correct` hunts. Prices come from `skynet/cost.py`. The harness refuses to start if a model has no price there.

**Spend cap**: `--max-spend` (default `15.0` USD). The harness stops *starting* new hunts once the running total passes it. A hunt in flight finishes.

## Run it

```bash
ANTHROPIC_API_KEY="$(op read 'op://Personal/Anthropic API Key/credential')" \
  uv run python bench/run_bench.py --sets baseline current current-workers --repeats 2
```

Flags: `--sets`, `--scenarios` (default: every key in `SCENARIOS`), `--repeats`, `--max-spend`. It prints a summary table and writes `results/<YYYY-MM-DD-HHMM>-<sets>.jsonl`.

## Add a model set

1. Add the model's price to `PRICING` in `skynet/cost.py`.
2. Add a row to `MODEL_SETS` with all four roles: `skynet`, `t1000`, `t800`, `resistance`.
3. Run with `--sets <new> baseline` so there is a same-day comparison.
4. Add the run to the list below, with the result file and a one-line result.

## Runs

- **9. Oct 2026**, sets `baseline current current-workers`, 4 scenarios × 2 repeats, **the connor mission** (the original person hunt: scenarios `john-connor`, `danny-dyson`, `blair-brewster`, `eli-vega`; that mission and its grid live at commit `286defb`). Rows record `code: ddf3b83+uncommitted-skynet-changes`; harness and results committed in `286defb`. File: [`results/2026-10-09-1539-baseline-vs-current-vs-current-workers.jsonl`](results/2026-10-09-1539-baseline-vs-current-vs-current-workers.jsonl).
  - `baseline`: 2/8 correct, 0 refused, $0.498 per correct hunt.
  - `current`: 0/8 correct, **8/8 refused**: Opus 5.5 as Skynet, first call, `stop_reason "refusal"`, category `"cyber"`.
  - `current-workers`: 6/8 correct, 0 refused, $0.136 per correct hunt.
  - **Consequence:** a second mission was added, hunting an asset (README, "The pivot"). The scenario keys on `main` are now `cyberdyne-chip`, `the-arm`, `neural-net`, `power-cell`; the four keys in these rows belong to the connor mission. **The next run is the first on the asset mission** and is not comparable row-for-row with this one.
