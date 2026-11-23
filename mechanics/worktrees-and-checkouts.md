# Worktrees and checkouts

## What

Every session works in a git worktree cut from `origin/main` and never touches the shared main checkout, which
concurrent sessions and live processes depend on. A worktree's checks run its own source, with dependencies compatible
with that revision (process.md §II, Checkouts).

## Why

The main checkout is shared. A checkout and a reset made in one session once wiped another session's uncommitted work,
so no session touches it and each works in a worktree off `origin/main`. A live process that imports from the main
checkout, a server say, freezes it, since its code loads lazily from there. And an install run in a worktree while the
shell still exported the main checkout's virtual environment changed that environment under a running process; a bare
console script run in a worktree imports the package from the main checkout, so the check reads the wrong source. Hence
a worktree's checks run its own source, and an install into the shared environment is the owner's (process.md §II,
Checkouts; the worktree runbook, section 2).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — Checkouts: the rule, the base ref, the two allowed copies, the
  post-merge fast-forward and the host's own writes (a fill comment); stage 8's cleanup.
- [starter/docs/runbooks/worktree-sessions.md](../starter/docs/runbooks/worktree-sessions.md) — entering, the
  environment, the harness's refusals, checking a DONE report, finishing a pull request, cleaning up.
- [starter/AGENTS.md](../starter/AGENTS.md) — the worktree lines of the commands and of the agent instructions.
- [starter/CLAUDE.md](../starter/CLAUDE.md) — the digest bullet on working in a worktree.
- [starter/.gitignore](../starter/.gitignore) — the `.claude/worktrees/` and `/local/` entries.
- [starter/docs/skeletons/kickoff-planning-session.md](../starter/docs/skeletons/kickoff-planning-session.md) — the
  reads that start in a fresh worktree off `origin/main`, and the branch cut.

## Depends on

- [`the-two-session-loop`](the-two-session-loop.md) — each session starts in a worktree, and the plan check relies on
  the base.
- [`adversarial-gates`](adversarial-gates.md) — a worktree's gate passes an explicit base.
- [`subagent-driven-development`](subagent-driven-development.md) — a DONE report is checked in the worktree, and the
  ledger is copied out after the merge.
- [`handoffs-and-monitors`](handoffs-and-monitors.md) — a live run freezes its checkout, and an executor works at the
  execution SHA.
- [`working-with-the-owner`](working-with-the-owner.md) — an install into the shared environment is the owner's.
- Git worktrees (SETUP.md, item 5), Claude Code's `EnterWorktree` tool and `gh`.

## Variants

- **The default.** A worktree per session off `origin/main`, writing into the main checkout only as Checkouts allows
  (process.md §II, Checkouts).
- **Reusing the main checkout's environment.** The runbook gives the two cases, reuse and an isolated environment of the
  worktree's own, and the test that chooses between them (the runbook, section 2).
- **A squash or a rebase merge.** Stage 8 and the runbook's cleanup confirm the merge by the pull request's merged
  state, not the tip's ancestry (process.md §Conventions).
- **A clone per session.** The contract has no such rule; it names worktrees, which share one object store. A host that
  clones rewrites Checkouts and the runbook's cleanup for its clones.

## Grafting

1. Settle the checklist rows this touches: layout and vocabulary (branch names), the host's quality gates as the fast
   suite, and where the ledger lives (ADOPTING.md).
2. Write Checkouts (§II) into the host's process.md in its vocabulary, rewording its mentions of the plan check, the
   gates' base and stage 8's copies for what the host has taken, and answer its fill comment: the interpreter by
   absolute path, the gitignored data reached by absolute path and each command that writes into the main checkout.
3. Copy the worktree runbook, with the host's environment commands in AGENTS.md; keep its section 4 only with the
   plan-blocks extension (ADOPTING.md, step 5).
4. Add the worktree bullets to AGENTS.md and CLAUDE.md, and `.claude/worktrees/` and `/local/` to the host's
   `.gitignore`.
5. **Entering later.** Until then the host's own checkout practice stands, and Checkouts stays out of its process.md.
   Where the starter's text sends a session to a worktree off `origin/main`, reword it or cut it; the main sites are
   both stages 1 and 2, the plan check's ancestry test, stage 8's cleanup, the gates' base in Scopes, both charters'
   mentions of the worktree's own source, the kickoffs' reads, CLAUDE.md's digest bullet and AGENTS.md's worktree lines.
   `git grep -n -i -E 'worktree|main checkout|origin/main'` finds the rest (process.md §Canonical and pointer sites).
