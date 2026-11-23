# Mechanics

quoin's way of working comes apart into sixteen mechanics, and a repository that already has conventions adopts them one
at a time instead of taking the starter whole. The fusion session of [ADOPTING.md](../ADOPTING.md) reads this index
along with the repository's own conventions and proposes which mechanics enter now and which later. Each mechanic has a
page here in one shape: What, Why, Files (where it lives in [the starter](../starter/)), Depends on, Variants (the
common alternatives, and the default) and Grafting (how to add it to an existing repository, in steps, the last of them
what stays out of the repository until the mechanic is taken). A page describes the mechanic; its rule is the
contract's, [starter/docs/process.md](../starter/docs/process.md), at the section its row cites. The last column is
where a fusion session usually begins: `first` is what it adopts at once in a service repository, the loop's backbone;
`later` is what earns its keep once the loop is running; `measurement only` is for what serves only long computations
and the reading of their results, and enters only where the repository does such work (no mechanic here is that: the
rules of that work are [an extension](../starter/docs/process.md#extension--measurement-work) of the contract, kept or
deleted whole). The column orders a proposal, not the dependencies: a `later` row can be a dependency of another row, a
`first` one included (the loop's plan check needs a design-gate record and both seat types; the survey's setup is a
handoff), and each page's Depends on says which. A session that adopts [`the-two-session-loop`](the-two-session-loop.md)
takes [`adversarial-gates`](adversarial-gates.md), [`model-policy-and-seats`](model-policy-and-seats.md) and
[`counsel-triggers`](counsel-triggers.md) with it. The repository's conventions and the session's reconciliation
decide.

| Mechanic | One line | Path B |
|---|---|---|
| [`roadmap-as-the-spec`](roadmap-as-the-spec.md) | The roadmap is the spec: items in order, each with its anchor, the check that certifies it; "Now and next" is the only queue (process.md §Roadmap upkeep). | first |
| [`design-docs`](design-docs.md) | One design per roadmap item in a fixed house shape, from header and decisions to anchor, work breakdown and an append-only decision log (process.md §I). | first |
| [`the-two-session-loop`](the-two-session-loop.md) | Plan in one session that ends at a hard stop, implement in another that starts from the merged plan; the owner's review is the merge gate (process.md §II). | first |
| [`plans`](plans.md) | A dated, task-level plan per item, carrying its own rulings and pinned facts, written by the planning session for the implementation session (process.md §II, stage 3). | first |
| [`adversarial-gates`](adversarial-gates.md) | A second model's challenge review of the design and plan in the planning session and of the branch in the implementation session, from committed history, each gate's rounds capped (process.md §Adversarial review protocol). | later |
| [`model-policy-and-seats`](model-policy-and-seats.md) | Each role of the loop has its model bound in one table, beside the role that stands in for it; the seats, counsel and reviewer, are read-only subagents pinned in their own files (process.md §Model policy). | later |
| [`counsel-triggers`](counsel-triggers.md) | A fixed set of events sends a question to the counsel seat instead of the orchestrator ruling alone; what data settles, the orchestrator rules (process.md §Model policy, Counsel triggers). | later |
| [`subagent-driven-development`](subagent-driven-development.md) | The loop's implementation stage: the plan carried out task by task by one implementer subagent at a time, each report checked before it is acted on (process.md §II, stage 5). | first |
| [`handoffs-and-monitors`](handoffs-and-monitors.md) | Work longer than the handoff threshold runs under a handoff contract, executed by a cheaper monitor or the owner and resumed from its results (process.md §Handoff economics). | later |
| [`one-home-per-fact`](one-home-per-fact.md) | Every fact has one canonical home and every other site points at it; status sites are replaced at merge within budgets that one check holds (process.md §Canonical and pointer sites; §Budgets). | first |
| [`worktrees-and-checkouts`](worktrees-and-checkouts.md) | Every session works in a git worktree cut from `origin/main` and never touches the shared main checkout (process.md §II, Checkouts). | first |
| [`survey-and-literature`](survey-and-literature.md) | A recurring survey session keeps the external landscape as one standing document, with a literature tool and a verification pass over every citation (process.md §III). | later |
| [`explainers`](explainers.md) | Basics-to-advanced write-ups of the methods a project uses, behind an index, so that a fresh session or a reviewer can ramp up (process.md §Doc taxonomy). | later |
| [`working-with-the-owner`](working-with-the-owner.md) | Ask the owner only what only the owner can answer; reports lead with what is done, the results, the recommendations and the ask (process.md §II). | first |
| [`evidence-rules`](evidence-rules.md) | Claims cite measurements, anchors or file and line; every number carries its source; a dismissed finding gets a ruling too (process.md §Purpose and principles). | first |
| [`the-small-change-lane`](the-small-change-lane.md) | Typos, one-line bugs and doc corrections go branch, fix, pull request, with no design, plan or gates; a change that grows upgrades to the loop (process.md §Small-change lane). | first |
