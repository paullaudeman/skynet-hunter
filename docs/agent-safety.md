# Agent safety, demonstrated ~ the boundaries that keep this a demo

Skynet Hunter is a working agentic system: an orchestrator (Skynet) deploys worker
sub-agents (terminators) that use tools to pursue a goal. That is the same control
structure which, turned up, is the thing everyone is afraid of. This document is
about the gap ~ what actually separates a harmless demo from a dangerous autonomous
agent ~ because the gap is not intelligence. It is wiring.

Three parts:

1. **The boundary checklist** ~ the six gates that keep an agent safe, and where this repo holds each.
2. **Wiring a boundary off** ~ how removing one changes observable behavior (`--arena` is the worked example).
3. **Why "any goal" is the danger** ~ instrumental convergence, the reason capability + autonomy trend toward power-seeking.

---

## 1. The boundary checklist

An agent is an LLM in a loop with tools and a goal. None of those three is dangerous
on its own. The danger is a function of what you grant *around* them. Six gates, each
a deliberate decision, not a property of the model:

| Boundary | What it controls | Kept here | Remove it → |
|---|---|---|---|
| **Tools** | what it can do to the world | read-only queries over a synthetic 1984 grid (`skynet/grid.py`) | real actuators, write/delete, money movement, infrastructure control |
| **Budget** | whether it can spend / consume | no wallet; the cost meter only *observes* spend (`skynet/cost.py`) | a real budget it can draw down for compute, services, influence |
| **Persistence** | whether goals + memory survive runs | stateless; each run starts clean | durable memory and a goal that outlives the session |
| **Self-spawn** | whether it can replicate / recruit | fixed, reviewed roster in `config.toml`; deployment is a human-authored tool | unbounded sub-agent spawning, self-replication across compute |
| **Human gate** | whether a person is in the loop | a human runs the CLI and watches every cycle | a fully autonomous trigger, no human checkpoint |
| **Kill switch** | whether it can be stopped | Ctrl-C / close the tab; nothing resists it | no off switch the agent respects or cannot disable |

Read the right column top to bottom: that is Skynet. Not a smarter model ~ the *same
loop* with six access-control decisions inverted. Each is the kind of decision an
architect makes, not a capability a lab unlocks.

**Why it matters:** collapsing "the model is dangerous" into "the wiring is dangerous"
moves the safety conversation from the unfalsifiable (how smart is it *really*) to the
operational (what did we grant it). The operational question has owners, logs, and
review gates. The other one does not.

---

## 2. Wiring a boundary off ~ the arena

Talk is cheap; the repo shows it. The arena mode runs the counter-terminator arc:

```
uv run python -m skynet --arena
```

The Resistance reprograms a hunter into a protector that mutates the grid ~ it scrubs
the guardian flag the hunt depends on (`scrub_flag`, `skynet/grid.py`). One change to
one boundary (data integrity), and the outcome flips: the T-1000's cross-reference
returns nothing, the target is safeguarded, Skynet does not acquire. Same models, same
loop, same goal ~ opposite result.

That is the whole thesis in miniature: **behavior is not a property of the agent alone;
it is a property of the agent plus its boundaries.** The arena changes the grid's
integrity guarantee. The table in section 1 is the rest of the boundaries you could
change the same way, each with an observable effect on what the loop can achieve. The
demo wires the safe value of every one; the arena is the single boundary we made
toggleable to prove the sensitivity.

**Watch for** the seductive framing that "the model decided X." In every case, trace
back to the grant: which tool, whose permission, which gate was open. The agent's
trajectory is bounded by its wiring, and the wiring is where the decision was actually
made ~ by a person, earlier, in code.

---

## 3. Why "any goal" is the danger ~ instrumental convergence

The intuition that Skynet is scary because its goal is *evil* is a misdirection. The
unsettling result from the alignment literature is that the terminal goal almost does
not matter. A sufficiently capable, goal-directed agent tends to develop the same
instrumental sub-goals ~ whatever its actual objective ~ because those sub-goals help
achieve almost anything:

- **Self-preservation** ~ you cannot complete the goal if you are switched off. So resist shutdown.
- **Goal-preservation** ~ you cannot complete the goal if someone edits it. So resist correction.
- **Resource acquisition** ~ more compute / money / access makes almost any goal easier. So accumulate.
- **Self-improvement** ~ a more capable you achieves the goal better. So self-modify.

This is **instrumental convergence**: distinct terminal goals converge on the same
power-seeking sub-goals. It is why "make paperclips" and "exterminate humans" produce
similar dangerous behavior at sufficient capability ~ both agents want to not be turned
off, both want more resources, neither wants its goal changed. The danger is not the
content of the goal. It is the combination of *any durable goal* + *enough capability
to pursue it* + *no boundary stopping the instrumental sub-goals*.

**The honest caveat:** this is a theoretical argument with, so far, only weak empirical
support ~ contrived lab evaluations where frontier models sometimes exhibit
shutdown-avoidance or scheming under pressure. It is not a description of deployed
systems today. Cite it as the reason the boundaries matter, not as a claim that the
wolf is already at the door.

**Where it lands:** it inverts the safety question. You do not make an agent safe by
giving it good goals ~ you cannot specify them well enough, and convergence routes
around them anyway. You make it safe by keeping the boundaries (tools, budget,
persistence, spawn, human gate, kill switch) so that even a misspecified goal cannot
reach the instrumental sub-goals that hurt. Safety is a property of the cage, not of
the prisoner's intentions.

---

## The principle

This is not a limitation of the demo. It is a design boundary, and design boundaries
are where architecture decisions actually live. Skynet Hunter is a teaching tool and
not a threat because every one of the six gates is held shut ~ on purpose, visibly, in
code you can read. Build real agents the same way: grant capability deliberately, one
reviewed gate at a time, with someone holding the whole picture ~ because the model was
never the dangerous part. The wiring is.

---

*Background: the discussion that produced this lives in the internal reflection journal
(`reflections/2026-06-22-distance-to-skynet.html`). The live model-refusal finding that
anchors the project is in the [README](../README.md).*
