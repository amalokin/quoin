# Counsel triggers

## What

A fixed list of events sends a question to the counsel seat, so that the orchestrator does not rule alone on a judgment
the plan's author or the owner would otherwise make; what data settles stays the orchestrator's (process.md §Model
policy, Counsel triggers).

## Why

The triggers exist so that the orchestrator is not left to judge the contract itself: each finding of the first gate
round on the policy's text was a gap where it would have had to. So the seat is called whenever a trigger fires, and the
orchestrator does not weigh whether the call is needed (process.md §Model policy, The seats). In one item a fix wave
closed the malformed inputs a review named, and its re-gate found more of the same kind, the second failed attempt at
one root cause (trigger 4); counsel ruled to close the whole class by one mechanism, with a sweep over the class as the
acceptance test. A full-budget call is costly, so the orchestrator rules alone on what data settles, and those rulings
go to the reviewer seat at stage 6 (§Model policy, Counsel triggers).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the three-tier rule, the triggers and their records, and the
  rules for a seat call.
- [starter/.claude/agents/counsel.md](../starter/.claude/agents/counsel.md) — the seat's charter: what it gets, what it
  returns, its boundaries, and a fill comment for the host's own questions.
- [starter/docs/skeletons/counsel-package.md](../starter/docs/skeletons/counsel-package.md) — the written package:
  triggers fired, question, options, evidence, what is ruled out, rulings at stake.
- [starter/docs/skeletons/kickoff-implementation-session.md](../starter/docs/skeletons/kickoff-implementation-session.md)
  — its section on the seats and the counsel triggers.
- [starter/docs/skeletons/pr-description.md](../starter/docs/skeletons/pr-description.md) — the rulings made in the
  owner's place, and the seat log.
- [starter/AGENTS.md](../starter/AGENTS.md) — the testing line that treats a moved pinned value as counsel trigger 5.

## Depends on

- [`model-policy-and-seats`](model-policy-and-seats.md) — the counsel seat, its binding and stand-in, and the rules for
  a call.
- [`subagent-driven-development`](subagent-driven-development.md) — the triggers apply through stage 5; a stuck
  implementer is trigger 4.
- [`adversarial-gates`](adversarial-gates.md) — triggers 1 and 3 begin in a gate finding or a reviewer's disagreement.
- [`plans`](plans.md) — a counsel ruling that amends a plan parameter is written into its record.
- [`design-docs`](design-docs.md) — counsel's rulings are promoted to the decision log, marked as counsel's.
- [`working-with-the-owner`](working-with-the-owner.md) — scope and anchors are the owner's, as is a counsel ruling the
  reviewer overturns.

## Variants

- **The default.** The triggers as the contract lists them, one counsel call per event with a package naming each
  trigger it fires.
- **With the measurement triggers.** Where plans end in measurements,
  [an extension](../starter/docs/process.md#extension--measurement-work) adds three more triggers, which a host keeps or
  deletes whole.
- **The host's own questions.** The charter's section on what the repository's questions look like is a fill comment:
  the host writes the kinds of question its seat gets, in its own terms, in place of the generic examples.

## Grafting

1. Settle the checklist rows this touches: the models and the seats' binding, and where the ledger lives, since rulings
   are written there as they are made (ADOPTING.md).
2. Write the triggers, with the seat rules they use (§Model policy, Counsel triggers; The seats), into the host's
   process.md in its vocabulary, keeping their numbers, which the contract and AGENTS.md cite.
3. Copy the counsel charter, bound as the model policy says, and `counsel-package.md`, and write the host's own kinds of
   question into the charter.
4. Add the kickoff's section on the seats and triggers, and the pull request description's sections for the rulings made
   in the owner's place and the seat log.
5. Have each session write its rulings in the ledger with their tier or trigger, and promote the durable ones, counsel's
   marked as its own, to the decision log at the item's close.
6. **Entering later.** Until then the host's own way of settling hard questions stands, and the texts of step 2 stay out
   of its process.md. Where the starter's text names counsel or a trigger, reword it or cut it; the main sites are stage
   5's counsel sentence, stage 6's trigger-1 clause, the cap's counsel clause, the records, Dispatch's stuck-implementer
   clause, the review of the policy, the kickoff's seats section and AGENTS.md's testing line.
   `git grep -n -i -E 'counsel|trigger'` finds the rest (process.md §Canonical and pointer sites).
