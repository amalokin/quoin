# Subagent-driven development

## What

Stage 5 of the loop: the implementation session carries the merged plan out with the Superpowers skill of this name, one
implementer subagent per task, the orchestrator checking each report itself and keeping a ledger of the session's
rulings (process.md §II, stage 5).

## Why

One subagent at a time is the owner's standing gate on parallel dispatch, not an efficiency preference: the owner, not
an agent, decides when work fans out (process.md §Model policy, Dispatch; SETUP.md, the dispatch rule). Cost explains
the other dispatch rule: subagents carry most of a session's cost, so each dispatch names the least capable model that
carries its role. A report is a claim: implementers once reported DONE with their work staged and not committed, and the
contract reopens the policy when a defect reaches a gate through a report nobody checked, so the orchestrator looks at
the tree and re-runs the named tests before it acts (process.md §II, stage 5; §Model policy, Dispatch). The ledger is
untracked because its churn makes a poor diff, and kept because it holds the session's rulings and evidence until the
durable ones are promoted into the design's log and the report.

## Files

- [starter/docs/process.md](../starter/docs/process.md) — stage 5 of the loop (§II), the rules on other subagents
  (§Model policy, Dispatch) and the ledger's row (§Doc taxonomy).
- [starter/docs/skeletons/kickoff-implementation-session.md](../starter/docs/skeletons/kickoff-implementation-session.md)
  — the prompt's stage-5 and ledger sections.
- [starter/docs/runbooks/worktree-sessions.md](../starter/docs/runbooks/worktree-sessions.md) — its "Checking a DONE
  report", and the ledger's copy after the merge in its "Cleaning up after the merge".
- [starter/.gitignore](../starter/.gitignore) — the `.superpowers/` entry that keeps the ledger out of git.
- [starter/AGENTS.md](../starter/AGENTS.md) — the fast suite's command and the testing guidelines.

## Depends on

- [`plans`](plans.md) — the plan is the work's whole scope; work it does not cover stops.
- [`the-two-session-loop`](the-two-session-loop.md) — stage 5 follows the plan check.
- [`working-with-the-owner`](working-with-the-owner.md) — only the owner names a fan-out.
- [`model-policy-and-seats`](model-policy-and-seats.md) — each dispatch names its model; a seat is dispatched by agent
  type, with none.
- [`counsel-triggers`](counsel-triggers.md) — they apply through the stage.
- [`worktrees-and-checkouts`](worktrees-and-checkouts.md) — the worktree the work happens in, and the ledger's copy
  after the merge.
- The Superpowers plugin (`superpowers:subagent-driven-development`) and git — the skill, and each task's commit.

## Variants

- **The default.** Per-task subagents from the Superpowers skill, the full suite in the background.
- **Without the plugin.** The loop is unchanged: the session carries the plan out itself, task by task, in the shape of
  Superpowers' `executing-plans` skill, and keeps the ledger by hand at the same path (SETUP.md, what degrades).
- **A ledger elsewhere.** A host whose conventions keep ignored directories out of a repository puts the ledger at
  another local path and rewrites every site that names `.superpowers/sdd/` (ADOPTING.md, the checklist's row on where
  the ledger lives).

## Grafting

1. Settle the checklist rows this touches: the host's quality gates as the fast suite, and where the ledger lives
   (ADOPTING.md).
2. Write stage 5 (§II), the ledger's row (§Doc taxonomy) and the rules on other subagents and on one at a time (§Model
   policy, Dispatch) into the host's process.md, in its vocabulary.
3. Append `.superpowers/` to the host's `.gitignore`, creating the file if it has none.
4. Name in AGENTS.md the fast suite and the touched-tests command, with the test-first rule; implementers run the
   touched tests and the orchestrator the rest.
5. Make `superpowers:subagent-driven-development` available (SETUP.md), and copy the kickoff's stage-5 and ledger
   sections into the host's implementation kickoff.
6. On the first task, check the report yourself before the next dispatch: `git status`, then the named tests (the
   worktree runbook, "Checking a DONE report").
7. **Entering later.** Until then the host's own way of carrying a plan out stands, and the texts of step 2 stay out of
   its process.md. Where the starter's text names the skill or the ledger, reword it or cut it; the main sites are stage
   6's package and independence rule, stage 8's workspace copy, the records of the model policy, the kickoff's stage-5
   and ledger sections, the worktree runbook's "Checking a DONE report" and "Cleaning up after the merge", the plan
   skeleton's "For agentic workers" line and the seat charters' reads.
   `git grep -n -i -E 'SDD|ledger|subagent-driven'` finds the rest (process.md §Canonical and pointer sites).
