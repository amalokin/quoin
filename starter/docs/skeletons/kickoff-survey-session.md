# Survey session — ‹the trigger›

## Launch

This is an implementation-class session, since a survey is neither ideation nor planning and that class runs the rest, launched with `claude --model ‹the implementation class's model, process.md §Model policy, the binding table› --effort max`, the owner confirming `/effort` reads max; if the work asked of you belongs to the planning class, say so before you start (process.md §Model policy).

## Why now

Start from the trigger that fired, ‹which one›, and the sweep it asks for (process.md §III).

## Reads

Start clean in a git worktree off `origin/main`: read `CLAUDE.md`, the roadmap, the standing survey `docs/reports/literature-review.md` with its watchlist and sweep log first, and the procedure `docs/runbooks/literature-search.md` (process.md §III; §II, Checkouts).

## Setup

Run the checks of the research setup handoff, `docs/handoffs/HANDOFF-research-setup.md`, first, in a checkout at its manifest's commit as its Prerequisites say, and resume it at its first failing step; every key-holding action is the owner's (process.md §III).

## The three jobs

Sweep for reuse (what is solved), novelty (what stays unsolved) and the feasibility watch (external claims against our understanding) (process.md §III).

## Method

Use research subagents, one at a time unless the owner names a parallel fan-out in this session, and the literature tool `tools/lit.py`; cite primary sources inline, file their PDFs under `docs/papers/` and queue a paywalled one in `docs/papers/REQUESTS.md` for the owner (process.md §III; §Model policy, Dispatch).

## The verification pass

Before anything lands, have an independent verification pass check every citation against its source; it is the survey's gate (process.md §III).

## The document

Revise the standing sections of `docs/reports/literature-review.md` in place, and update the papers index, the dated sweep log and the watchlist the next sweep starts from (process.md §III).

## The PR

Land the findings through the usual PR gate, reporting to the owner in layers (process.md §III; §II, stage 7).
