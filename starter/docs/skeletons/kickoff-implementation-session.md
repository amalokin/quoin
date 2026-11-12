# Implementation session — ‹the item›

## Launch

This is an implementation-class session, launched with `claude --model ‹the implementation class's model, process.md §Model policy, the binding table› --effort max`, the owner confirming `/effort` reads max; if the work asked of you belongs to the planning class, say so before you start (process.md §Model policy).

## The item and its plan

Implement ‹the roadmap item› from its merged plan, ‹docs/plans/YYYY-MM-DD-slug.md›; the roadmap entry is the spec, and this prompt yields to it on scope, order and purpose (process.md §II, stage 1).

## Reads

Start clean, a fresh session in a git worktree off `origin/main`: read `CLAUDE.md`, the roadmap, the item's design doc (its Read-first sections and its Active obligations), the report sections they cite, the plan and the Model policy, the seats and the counsel triggers included (process.md §II, Implementation session; §Model policy).

## The plan check

Run the plan check before any work; if any part of it fails, stop and tell the owner what is missing, and write, extend or replace no plan (process.md §II, Implementation session).

## Branch

Then cut `feature/‹slug›` from `origin/main` (process.md §II, Implementation session).

## Implement (stage 5)

Implement the plan with `superpowers:subagent-driven-development` and TDD, the fast suite and the checks `AGENTS.md` names green throughout, one subagent at a time unless the owner names a fan-out; check a subagent's report before acting on it, and stop and flag work the plan does not cover (process.md §II, stage 5; §Model policy, Dispatch).

## The SDD ledger

Keep the ledger in `.superpowers/sdd/`, local, untracked and never deleted; write each ruling in it as you make it, with its tier or trigger, and promote the durable ones into the design's decision log and the item's report (process.md §II, stage 5; §Model policy, Records).

## The seats and the counsel triggers

Call `counsel` whenever a counsel trigger fires and `reviewer` at stage 6, each by agent type with no model parameter and a written package laid out as `docs/skeletons/counsel-package.md` or `docs/skeletons/reviewer-package.md` (process.md §Model policy, Counsel triggers; The seats).

## Final review (stage 6)

With every change committed, stage 7's records below included but for the gate's and the seats' decision-log rows, the open items the whole-branch review's triage defers and the PR number, run the final adversarial gate against `origin/main`, then the reviewer seat and the second whole-branch review one after the other on the same package, neither shown the other's report until both return, and apply their findings in one fix wave that follows the gate transitions (process.md §II, stages 6 and 7; §Adversarial review protocol).

## The PR (stage 7)

Before the final review, write stage 7's records: replace, never append to, the roadmap's status paragraph, the design header's status and CLAUDE.md's Status, update the design's Active obligations, and record what the merge hands on in the report's open items, the report laid out as `docs/skeletons/report.md`; after the review, add the gate's rows and the seat log to the design's decision log and the minors its triage defers to the report's open items, cut the PR for the owner's review, its description laid out as `docs/skeletons/pr-description.md`, and write the PR's number by one more commit at the status sites, in the plans index's PR cell and in the plan's and the report's banners (process.md §II, stages 6 and 7).

## Post-merge (stage 8)

After the merge, confirm the merge as stage 8 says (the merge method's row), copy the SDD workspace into the main checkout's `.superpowers/sdd/`, remove the worktree and delete the merged branch (process.md §II, stage 8; §Conventions).

## Asking the owner

Ask the owner only what only the owner can answer, batched as structured questions; trivia gets a default and a recorded ruling (process.md §II).
