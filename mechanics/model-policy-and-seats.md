# Model policy and seats

## What

The model policy binds each role of the loop to a model in one place, the binding table, beside the role that stands in
for it, and defines the seats, counsel and reviewer: subagents with their model pinned in their own files. A model that
is not offered, or that fails, costs a rebinding or a stand-in, not a redesign (process.md §Model policy).

## Why

The split spends the strongest model where its judgment is distinctive and lets another run the loop. Its case is not
the bill, which was projected to stay about where it was, but what an outage of the strongest model does to an item: the
work goes on under the implementation class where it once stopped ([`the-two-session-loop`](the-two-session-loop.md)
tells it). A seat is never briefed to economise: one told to be efficient declined to judge the one formula of an item
that was wrong, and a second review of the same package found it ([`plans`](plans.md)). One table binds the models
because no one place did: a seat's model was to change by a one-line edit, yet its name stood at many sites (process.md
§Model policy, The binding table; The seats).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the binding table, the seats, the rules for a seat call,
  dispatch and the review of the policy.
- [starter/.claude/agents/counsel.md](../starter/.claude/agents/counsel.md) — the counsel seat: model and effort pinned,
  writing tools removed.
- [starter/.claude/agents/reviewer.md](../starter/.claude/agents/reviewer.md) — the reviewer seat: the whole-branch
  review and Gate mode.
- [starter/docs/skeletons/counsel-package.md](../starter/docs/skeletons/counsel-package.md) — the written package of a
  counsel call.
- [starter/docs/skeletons/reviewer-package.md](../starter/docs/skeletons/reviewer-package.md) — the written package of
  the whole-branch review.
- [starter/docs/skeletons/kickoff-implementation-session.md](../starter/docs/skeletons/kickoff-implementation-session.md)
  — its Launch line leaves the model to the table, and its seats section.
- [starter/docs/skeletons/pr-description.md](../starter/docs/skeletons/pr-description.md) — the seat log, and what no
  seat reviewed.

## Depends on

- [`counsel-triggers`](counsel-triggers.md) — the events that call the counsel seat.
- [`adversarial-gates`](adversarial-gates.md) — the gate's row, and the reviewer seat in gate mode.
- [`the-two-session-loop`](the-two-session-loop.md) — its sessions are the classes, and its plan check lists both seat
  types.
- [`subagent-driven-development`](subagent-driven-development.md) — each dispatch names the least capable model for its
  role.
- [`handoffs-and-monitors`](handoffs-and-monitors.md) — the monitors-and-guides row.
- [`working-with-the-owner`](working-with-the-owner.md) — the pull request lists provisional rulings and skipped seats.
- Claude Code: `--model`, `--effort`, `/model`, `/effort` and the `.claude/agents/` folder (SETUP.md, items 1, 8 and
  11).

## Variants

- **The default.** The table as the starter ships it: each role at the model its row binds, the seats pinned in their
  files.
- **Rebound at adoption.** An environment that does not offer a default binds the seats and the planning class to the
  strongest model it offers, in the table and the seat files (process.md §Model policy, The binding table; ADOPTING.md,
  step 6).
- **One model for every role.** A host offered a single model binds the classes and the seats to it. The stand-in is
  then the model that failed, so the ladder ends at the first failure and the session stops and flags the round as the
  owner's (process.md §Adversarial review protocol, The gate transitions); the split still earns its keep in the hard
  stop and the fresh context.

## Grafting

1. Settle the checklist rows this touches: the models and the seats' binding, Codex's availability and the PR review as
   the owner's gate (ADOPTING.md).
2. Write the model policy into the host's process.md, in its vocabulary, with the table bound to the models the account
   offers (the owner's `/model`, SETUP.md, item 11).
3. Copy the seat files and the package skeletons, and set each seat's `model` and `effort` to what its row says: a
   rebinding is two edits, the seat file and the table, and no other site names a model.
4. Launch each session as its class's row says in its Where set cell, the owner confirming `/effort` (SETUP.md, item 8).
5. **Entering later.** Until then the host's own choice of models stands, and the texts of step 2 stay out of its
   process.md. Where the starter's text names a class or a seat, reword it or cut it; the main sites are the class
   sentences of the ideation and loop paragraphs, the plan check's seat clause, stages 6 and 7, the taxonomy's seat row,
   the kickoffs' Launch lines, CLAUDE.md's digest bullets and AGENTS.md's layout line.
   `git grep -n -i -E 'binding table|seat|stand-in|planning class|implementation class|--effort|model policy'` finds the
   rest (process.md §Canonical and pointer sites).
