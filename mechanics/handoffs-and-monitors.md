# Handoffs and monitors

## What

Work that would hold an expensive session, a run longer than the handoff threshold or a step that needs the owner at a
running system, is written down as a handoff and executed by a cheaper monitor session or by the owner. A fresh
orchestrator then resumes from the results, not from the old session's transcript (process.md §Handoff economics).

## Why

An orchestrator babysitting a long run burns its prompt cache between checks and re-sends a long history every poll,
which is expensive exactly when nothing needs judging (process.md §Handoff economics). The shape of the contract was
paid for by a failure: a launch checklist named a git-ignored script that needed uncommitted code, and it was found dead
on the remote machine only when the remote session tried to run it. Hence the execution SHA, the manifest and the
self-containment check, and an executor whose first step verifies its checkout and rebuilds any built artefact from it,
since one built earlier survives a change of checkout and cannot say which source made it. A handoff for a cheaper model
is dry-read first, because its author knows too much.

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the pattern, the five-section contract, the self-containment
  check, the dry read, the guided live session and the threshold (§Conventions).
- [starter/docs/skeletons/handoff.md](../starter/docs/skeletons/handoff.md) — the five sections as headings with a
  guidance line each.
- [starter/docs/skeletons/results.md](../starter/docs/skeletons/results.md) — the results file of one attempt.
- [starter/docs/skeletons/kickoff-pickup-session.md](../starter/docs/skeletons/kickoff-pickup-session.md) — the session
  that checks first, then rules from the results.
- [starter/docs/handoffs/README.md](../starter/docs/handoffs/README.md) — the index, and the banner a closed handoff
  carries.
- [starter/docs/handoffs/HANDOFF-research-setup.md](../starter/docs/handoffs/HANDOFF-research-setup.md) — a standing
  handoff, the contract at full length.
- [starter/AGENTS.md](../starter/AGENTS.md) — the push rule: a branch is pushed when a handoff needs its commit on
  `origin`.

## Depends on

- [`model-policy-and-seats`](model-policy-and-seats.md) — the monitors-and-guides row, and the class that prepares a
  handoff and picks up its results.
- [`worktrees-and-checkouts`](worktrees-and-checkouts.md) — the executor works in a checkout at the execution SHA.
- [`one-home-per-fact`](one-home-per-fact.md) — a handoff gets a banner and an index row, and cites runbooks rather than
  repeating them.
- [`survey-and-literature`](survey-and-literature.md) — its tool's setup is the starter's standing handoff.
- [`counsel-triggers`](counsel-triggers.md) — a guide interprets nothing: the owning session rules from the results, and
  calls counsel when a trigger fires.
- [`the-two-session-loop`](the-two-session-loop.md) — results that feed an item in flight are picked up by an
  implementation session.
- Git: `git merge-base --is-ancestor` and `git ls-tree` for the self-containment check.

## Variants

- **The default.** A monitor-class session executes the handoff, or the owner does in a terminal, above a threshold of
  about thirty minutes serial (process.md §Conventions).
- **A longer threshold.** A host whose runs are long sets it at about an hour, in the same row.
- **A guided live session.** A step that needs the owner at a running system and no judgment from the orchestrator uses
  the same contract, and the guide reports what it observed (process.md §Handoff economics).
- **Runs of hours.** [An extension](../starter/docs/process.md#extension--measurement-work) holds the rules for runs
  that last hours, which a host keeps or deletes whole.

## Grafting

1. Settle the checklist rows this touches: the handoff threshold, and the models and the seats' binding for the monitors
   (ADOPTING.md).
2. Write the handoff economics, the Handoff row of the taxonomy and the threshold's row of the Conventions into the
   host's process.md, in its vocabulary.
3. Copy the handoffs index, the two skeletons and the pickup kickoff into the host's tree, and add the push rule to
   AGENTS.md.
4. For the first handoff, write it from the skeleton, run the self-containment check, have a subagent of the executing
   class dry-read it, and land it with its index row.
5. **Entering later.** Until then the host's own way of running long work stands, and the texts of step 2 stay out of
   its process.md. Where the starter's text names a handoff or a monitor, reword it or cut it; the main sites are the
   model policy's class sentences and monitors row, stage 7's post-merge sentence, the taxonomy's Handoff row, the
   record freeze's handoff clause, the counsel charter's boundary on long computations, the doc map's row and
   CLAUDE.md's digest bullet, and AGENTS.md's push rule. `git grep -n -i -E 'handoff|monitor'` finds the rest
   (process.md §Canonical and pointer sites).
