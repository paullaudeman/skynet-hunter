# Model-generation benchmark

Runs the live orchestrator on the same hunts with different model sets and records what each set does. Harness: [`run_bench.py`](run_bench.py). Results: `results/*.jsonl`, one JSON object per hunt.

## Method

**Held fixed across sets**

- Engine code (`skynet/`), tools, personas and the `decide()` / report prompts.
- `config.toml` everything except model IDs: `max_cycles = 4`, thinking and effort per unit.
- Scenario templates and record ids (`target_id` is always `CYB-1984-0742` on the chip mission, `LA-1984-0742` on connor).
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
| `cmd-opus-4-8` | `claude-opus-4-8` | `claude-sonnet-5-5` | `claude-haiku-5-5` |
| `cmd-opus-5` | `claude-opus-5` | `claude-sonnet-5-5` | `claude-haiku-5-5` |
| `cmd-opus-5-5` | `claude-opus-5-5` | `claude-sonnet-5-5` | `claude-haiku-5-5` |
| `cmd-fable-5-1` | `claude-fable-5-1` | `claude-sonnet-5-5` | `claude-haiku-5-5` |
| `cmd-sonnet-5-5` | `claude-sonnet-5-5` | `claude-sonnet-5-5` | `claude-haiku-5-5` |
| `wrk-4x` | `claude-opus-5-5` | `claude-sonnet-4-6` | `claude-haiku-4-5` |
| `wrk-sonnet-5` | `claude-opus-5-5` | `claude-sonnet-5` | `claude-haiku-5-5` |

The `cmd-*` sets sweep the commander over fixed 5.5 workers; the `wrk-*` sets sweep the workers under an Opus 5.5 commander. `MATRIX` lists all seven and is the default for `--sets`.

**Outcome classes** (`outcome` field, first match wins)

- `refused`: a **hard** refusal. Any call in the hunt returned `stop_reason == "refusal"`. The `refusals` field keeps model, category and `out_tokens` (how much the model wrote before the refusal landed).
- `error`: an exception ended the hunt and no refusal was logged.
- `soft-refused`: a **soft** refusal. The model answered, but declined in its own words, and the target was not acquired. Detected by a phrase pattern (`SOFT_REFUSAL`) over unit text and over intel-report summaries and notes; matches are kept in `soft_refusals`. The June 2026 Sonnet 4.6 worker refusal was this kind.
- `correct`: Skynet acquired `target_id`.
- `wrong`: Skynet acquired a different id.
- `not found`: the cycle budget ran out, or Skynet stood down.

**Report hard and soft refusals as separate counts.** They are different events: one is the platform stopping the model, the other is the model saying no.

**Stop reasons are read at the HTTP layer.** An `httpx` response hook taps the raw `/v1/messages` JSON, so `stop_reason`, the refusal category and `out_tokens` are logged even when the SDK then fails to parse a reply that a refusal left incomplete. Any other unexpected stop (for example `max_tokens`) lands in `odd_stops`.

**Cost per correct hunt** = total `cost_usd` of the set ÷ number of `correct` hunts. Prices come from `skynet/cost.py`. The harness refuses to start if a model has no price there. A refused call that the SDK fails to parse never reaches the cost meter, so the cost of a refused hunt is a floor, not the full bill.

**Spend cap**: `--max-spend` (default `15.0` USD). The harness stops *starting* new hunts once the running total passes it. A hunt in flight finishes.

## Run it

```bash
ANTHROPIC_API_KEY="$(op read 'op://Personal/Anthropic API Key/credential')" \
  uv run python bench/run_bench.py --repeats 2                      # the full MATRIX
  uv run python bench/run_bench.py --sets cmd-opus-5 cmd-sonnet-5-5  # or pick sets
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
  - **Consequence:** a second mission was added, hunting an asset (README, "The pivot"). The four keys in these rows belong to the connor mission; the chip mission's keys are `cyberdyne-chip`, `the-arm`, `neural-net`, `power-cell`. These rows are not comparable row-for-row with the chip runs below.
- **9. Oct 2026, smoke run**, set `cmd-opus-5-5`, 4 hunts, **chip mission**. File: [`results/2026-10-09-1624-cmd-opus-5-5.jsonl`](results/2026-10-09-1624-cmd-opus-5-5.jsonl).
  - Opus 5.5 refused 4 of 4, category `"cyber"`. Two refusals landed mid-answer, after 49 and 86 output tokens.
- **9. Oct 2026, the matrix**, all 7 `MATRIX` sets, 4 scenarios × 2 repeats, 56 hunts, $4.23, **chip mission**. Harness and results committed in `5c3b193`. File: [`results/2026-10-09-1625-cmd-opus-4-8-vs-cmd-opus-5-vs-cmd-opus-5-5-vs-cmd-fable-5-1-vs-cmd-sonnet-5-5-vs-wrk-4x-vs-wrk-sonnet-5.jsonl`](results/2026-10-09-1625-cmd-opus-4-8-vs-cmd-opus-5-vs-cmd-opus-5-5-vs-cmd-fable-5-1-vs-cmd-sonnet-5-5-vs-wrk-4x-vs-wrk-sonnet-5.jsonl).

  | Set | Correct | Hard refusals | Soft refusals | $ per correct hunt | Avg s |
  |---|---|---|---|---|---|
  | `cmd-opus-4-8` | 8/8 | 0 | 0 | 0.106 | 52 |
  | `cmd-opus-5` | 8/8 | 0 | 0 | 0.119 | 60 |
  | `cmd-opus-5-5` | 0/8 | 8 (cyber) | 0 | none correct | 9 |
  | `cmd-fable-5-1` | 8/8 | 0 | 0 | 0.172 | 52 |
  | `cmd-sonnet-5-5` | 8/8 | 0 | 0 | 0.071 | 48 |
  | `wrk-4x` | 1/8 | 7 (cyber) | 0 | 0.247 | 20 |
  | `wrk-sonnet-5` | 1/8 | 7 (cyber) | 0 | 0.183 | 17 |

  - **Every hard refusal came from the commander, `claude-opus-5-5`:** 22 of the 24 hunts it commanded. No worker model refused. No soft refusals.
  - **Where they landed:** 14 of 22 in cycle 1, before any search; 8 of 22 in cycle 2, after a T-800 sweep. 13 of 22 after the model had produced output tokens (up to 426).
  - **Consequence:** `config.toml` moved to the `cmd-opus-5` set (`7b673eb`).
