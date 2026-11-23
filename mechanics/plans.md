# Plans

## What

A plan is the task-level breakdown of one item, written by the planning session for the implementation session to carry
out. It holds its own decision record, its rulings and pinned facts, and names the record of the design gate that
challenged it; once it has run it is frozen as a record (process.md §II, stage 3; §Doc taxonomy, the Plan row).

## Why

A design states intent, and the ground truth decides facts. In one item the only formula a plan prescribed without an
observation behind it proved wrong, refuted by a trace of the real system at the last fix wave. So every number in a
plan carries its source, and a formula with none is marked unpinned, with the observation that would pin it (process.md
§II, stage 3). The plan is also the implementation session's whole scope, and work it does not cover stops (process.md
§II, stage 5): hence its numbered rulings with their cost if wrong, and its gate record named by link, since the
record's rows move to the companion log when the wave closes.

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the plan's stage of the loop (§II), the Plan row (§Doc
  taxonomy) and the record freeze (§Canonical and pointer sites).
- [starter/docs/skeletons/plan.md](../starter/docs/skeletons/plan.md) — the house shape: banner line, goal, rulings,
  pinned facts, constraints, tasks.
- [starter/docs/plans/README.md](../starter/docs/plans/README.md) — the plans index, the record freeze and the banner.
- [starter/docs/id-registry.md](../starter/docs/id-registry.md) — the series of plan rulings and pinned facts.
- [starter/docs/skeletons/kickoff-planning-session.md](../starter/docs/skeletons/kickoff-planning-session.md) — how the
  planning session writes the plan.

## Depends on

- [`the-two-session-loop`](the-two-session-loop.md) — the hard stop's product, and the implementation session's input.
- [`design-docs`](design-docs.md) — the plan implements one design, and its log holds the gate record.
- [`roadmap-as-the-spec`](roadmap-as-the-spec.md) — the entry names the plan, and its status becomes planned.
- [`evidence-rules`](evidence-rules.md) — every number's source, and the unpinned mark.
- [`adversarial-gates`](adversarial-gates.md) — the design gate over the plan, whose closed record the plan check reads.
- [`one-home-per-fact`](one-home-per-fact.md) — the record freeze, and a gate record linked rather than copied.
- `superpowers:writing-plans` — the skill that writes the plan; where its defaults differ, the repository's skeleton and
  folders govern.

## Variants

- **The default.** One dated Markdown plan per item under `docs/plans/`, its tasks written as steps.
- **Code carried as file blocks.** A plan that carries its code as blocks has them proven in a scratch copy of the
  repository before the planning pull request. The contract holds this as
  [an extension](../starter/docs/process.md#extension--plans-verified-in-an-overlay), with `tools/plan_blocks.py`, which
  a host keeps or deletes whole.
- **Plans where the host's layout puts them.** The document check treats only `docs/plans/` and `docs/handoffs/` as
  dated records, so a plan kept elsewhere under `docs/` has its dead links fail at once instead of being pinned
  (ADOPTING.md, the layout note).

## Grafting

1. Settle the checklist rows this touches: layout and vocabulary (where plans live, how a plan's file is named) and the
   id registry on or off (ADOPTING.md).
2. Copy `docs/plans/README.md` and `docs/skeletons/plan.md` into the host. They hold no token or fill comment; point the
   index's links to process.md and the id registry at the host's paths, and the skeleton's section citations at its
   headings.
3. Write the plan's stage of the loop (§II), the Plan row (§Doc taxonomy) and the record freeze (§Canonical and pointer
   sites) into the host's process.md in its vocabulary.
4. With the id registry on, keep its plan-ruling and pinned-fact rows.
5. Make `superpowers:writing-plans` available (SETUP.md); without it the planning session writes the plan by hand.
6. The first plan lands with its index row in its planning pull request; the executing pull request fills the rest and
   adds the banner.
7. **Entering later.** Until then the host's task breakdown stands, and the texts of step 3 stay out of its process.md.
   Where the starter's text cites a plan, reword it or cut it; the main sites are stage 4's "amend the plan", the hard
   stop's plans-index row, the plan check's plan and gate-record clauses, stage 5's rule on work the plan does not
   cover, CLAUDE.md's doc-map row for the plans index and the plan-ruling and pinned-fact rows of the id registry.
   `git grep -n -i -E 'docs/plans|the plan'` finds the rest (process.md §Canonical and pointer sites).
