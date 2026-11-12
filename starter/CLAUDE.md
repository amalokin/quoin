# {{PROJECT}}

Goal: <!-- fill: the project's goal in two or three lines, what it builds and for whom; the roadmap's goal section holds the detail and this line points at it -->

**Status (<!-- fill: today's date, YYYY-MM-DD; the Status states the current state only and is replaced at every merge -->):**
the way of working is adopted from quoin; nothing of the project is built yet. Per-item status and the queue:
[docs/roadmap.md](docs/roadmap.md).
<!-- fill: what is merged, in flight and open, with "PR #N" and the PR's own date; no figure, no commit hash, no merge date and no branch name (process.md §II stage 7) -->

**Next:** the first ideation session, a planning-class session that writes the first item's design doc; the queue is
the roadmap's [Now and next](docs/roadmap.md#now-and-next).

## Doc map — read before reinventing anything

| Doc | Read when |
|---|---|
| [docs/roadmap.md](docs/roadmap.md) | Start here: the items in order, their anchors, one status paragraph each, "Now and next" (the only queue), the parking lot, standing decisions |
| [docs/process.md](docs/process.md) | Before any work: session types, the loop, checkouts, gates, handoffs, the doc taxonomy, the model policy (seats, triggers), budgets |
| [docs/process-log.md](docs/process-log.md) | process.md's history: its provenance and a dated decision log of every ruling on it |
| [docs/id-registry.md](docs/id-registry.md) | Finding a decision by id: every series, its document and anchors, the collisions |
| [AGENTS.md](AGENTS.md) | Mechanics: layout, build and test commands, style, commits and PRs, the worktree rule |
| [docs/designs/](docs/designs/) | One design per roadmap item: decisions, anchor, work breakdown, Active obligations, decision log; read it before touching its code |
| [docs/reports/](docs/reports/) | Per-item certification records: measured figures with their labels, the rulings, the dated open-items sections; the standing survey, [literature-review.md](docs/reports/literature-review.md) |
| [docs/plans/README.md](docs/plans/README.md) | One dated plan per planning session (the input to subagent-driven development); executed plans are records; the index |
| [docs/handoffs/README.md](docs/handoffs/README.md) | One-shot contracts for long runs and guided sessions, with their results; the index |
| [docs/runbooks/](docs/runbooks/) | How to operate: worktree sessions, the codex gate, the literature search |
| [docs/skeletons/](docs/skeletons/) | Writing a document or starting a session: each document's house shape, and the kickoff prompts the owner copies into `local/` |
| [docs/explainers/00-index.md](docs/explainers/00-index.md) | Method ramp-ups, basics to advanced; the index |
| [.claude/agents/](.claude/agents/) | The two seat charters, `counsel` and `reviewer` (model and effort pinned) |
| [docs/papers/](docs/papers/) | Local PDFs of primary sources; [REQUESTS.md](docs/papers/REQUESTS.md) queues the paywalled ones |

## Way of working — the digest (the contract is [docs/process.md](docs/process.md); this digest cites it and adds nothing)

- Your session class fixes your model, how you start and where you end; a session asked for the other class's work
  says so first (process.md §Model policy).
- An implementation session reads the plan and the Model policy, the seats and the counsel triggers included, before
  its plan check; nothing here restates them (process.md §II, Implementation session; §Model policy).
- Everything lands via feature branch and PR; trivial fixes take the small-change lane (process.md §Purpose and
  principles; §Small-change lane).
- A planning session ends at its planning PR; an implementation session starts from a merged plan, runs the plan
  check, and stops and flags when it fails; a Next line names sessions, never a chain (process.md §II, the hard stop
  and the plan check; §Roadmap upkeep).
- Work in a git worktree off `origin/main`; never check out, reset, clean, commit to or edit the main checkout but
  for the writes Checkouts lists, and run a worktree's checks against its own source (process.md §II, Checkouts).
- One subagent at a time unless the owner names the fan-out; seats are dispatched by agent type with no `model`
  parameter (process.md §Model policy, Dispatch and The seats).
- Anything over the handoff threshold runs under a handoff, and a handoff for a cheaper model is dry-read first
  (process.md §Handoff economics; the threshold: §Conventions).
- One home per fact: status sites are replaced at merge within their budgets, a claim is grepped at every site
  before it is edited, and a changed rule is rewritten in place (process.md §Canonical and pointer sites; §Budgets).
- Ask the owner only what only the owner can answer; defaults get recorded rulings (process.md §II).

## Load-bearing facts (one labelled line each; the home linked)

- <!-- fill: one durable finding as a labelled line, the claim with its label (population, estimator, uncertainty, registration status, limitations) and a link to the report that holds it; copied verbatim from the report, never re-derived or rounded (process.md §Canonical and pointer sites) -->
