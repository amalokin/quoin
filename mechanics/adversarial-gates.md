# Adversarial gates

## What

A second model challenges the approach, tradeoffs and assumptions of the design and plan before the code, and of the
branch before its pull request; the orchestrator judges each finding and records the ruling. A gate's rounds are counted
and capped, and a seat takes a round the tool cannot run (process.md §Adversarial review protocol, The gate transitions;
§Model policy, The cap).

## Why

A gate reads committed history only: staged, unstaged and untracked work is invisible to it, as the first gate run on a
contract like this one found, so a gate run before the commit reviews a branch without the work (process.md §Adversarial
review protocol, Scopes). Its tool is also metered and can fail: a round can die at launch or mid-run before it returns
anything, and a loop that waited on one would stall (§Adversarial review protocol, The gate transitions).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the protocol, the transitions, the cap and the gate's binding
  row.
- [starter/tools/codex_gate.sh](../starter/tools/codex_gate.sh) — the launcher, which refuses a dash-led focus file.
- [starter/docs/runbooks/codex-gate.md](../starter/docs/runbooks/codex-gate.md) — the invocation, the focus text and
  dead rounds.
- [starter/docs/skeletons/gate-focus.md](../starter/docs/skeletons/gate-focus.md) — the house shape of a focus text.
- [starter/.claude/agents/reviewer.md](../starter/.claude/agents/reviewer.md) — its Gate mode, for a round the tool
  cannot run.
- [starter/AGENTS.md](../starter/AGENTS.md) — read by every gate with its diff, and the launcher's line.
- [starter/docs/skeletons/pr-description.md](../starter/docs/skeletons/pr-description.md) — the sections that report the
  gates and what ran ungated.

## Depends on

- [`model-policy-and-seats`](model-policy-and-seats.md) — the gate's row, and the seat that stands in for the tool.
- [`design-docs`](design-docs.md) — each round is a row of the design's decision log.
- [`the-two-session-loop`](the-two-session-loop.md) — the design gate is stage 4, the final gate stage 6.
- [`worktrees-and-checkouts`](worktrees-and-checkouts.md) — a worktree's gate passes an explicit base.
- [`counsel-triggers`](counsel-triggers.md) — a finding no stage-6 seat will see may go to counsel (trigger 1).
- [`working-with-the-owner`](working-with-the-owner.md) — a material finding that survives two rounds of disagreement
  goes to the owner.
- The Codex plugin and CLI (SETUP.md, items 2 and 3), Node.js, git and `tools/codex_gate.sh`.

## Variants

- **The default.** The Codex plugin's review through `tools/codex_gate.sh`, with the reviewer seat in gate mode as its
  stand-in.
- **Codex absent for good.** The contract frames a missing tool as an outage, so a host without it for good rebinds at
  adoption instead (process.md §Model policy, The binding table): the gate row's default becomes the reviewer seat in
  gate mode, its stand-in the reviewer row's, and where it is set the reviewer's seat file. The host drops the launcher,
  the runbook and their mentions in AGENTS.md and the doc map, and rewords every sentence that names the tool, the
  plugin or a replaced round: the protocol's first three bullets, Scopes' flags, the dash-led sentence and its echoes,
  the two transition rows about the tool, and the clauses in the Seats row, the cap, trigger 1, the charter and the pull
  request skeleton. A seat round is a subagent, so Dispatch runs a gate round alone. The rounds, the cap and the rest of
  the transitions stand: they bind the gate, not its tool. The host gives up a second model: the gate is the seat's own,
  and the stage-6 reviewer rules on findings its own seat made.
  `git grep -n -i -E 'codex|plugin|gate.?s? tool|wedged|dash-led|replacement|you replace|job id|gate job|on a job'`
  finds them all, the extension's gate-job sentence included.

## Grafting

1. Settle the checklist rows this touches: Codex's availability, and the models and the seats' binding (ADOPTING.md).
2. Write the protocol, its transitions table and the cap (§Adversarial review protocol, The gate transitions; §Model
   policy, The cap) into the host's process.md, in its vocabulary.
3. Install the Codex plugin and CLI (SETUP.md), copy the launcher, the runbook and `gate-focus.md`, and name the
   launcher in AGENTS.md; without Codex, take the variant above.
4. Record each round as a row of the design's decision log, and report the gates in the pull request description.
5. **Entering later.** Until then the host's own review stands, and the texts of step 2 stay out of its process.md.
   Where the starter's text names a gate, reword it or cut it; the main sites are stages 4 and 6, the plan check's
   gate-record clause, the binding table's gate row, the seats' gate mode, both kickoffs' gate sections and the plans
   index's Gate record column. `git grep -n -i -E 'gate|codex|adversarial'` finds the rest (process.md §Canonical and
   pointer sites).
