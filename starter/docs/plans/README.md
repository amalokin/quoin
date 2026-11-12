# Plans — one dated plan per planning session

A plan is `docs/plans/YYYY-MM-DD-<slug>.md`, written by a planning session and executed by a fresh implementation
session once its planning PR has merged ([process.md](../process.md) §II, stages 3–5). It carries its plan-level
rulings (`R-<item>-<n>`, mirrored into the design's decision log; see [id-registry.md](../id-registry.md)) and its
pinned facts, and names its gate record by link: the design's decision log, where the plan check reads it. Plans stay
where they are: documents cite them by path, code and tests by ruling id.

**The record freeze.** A merged plan is edited only by its banner, the one blockquote under its "For agentic workers"
line, written by the PR that executed it. The one exception is a ruling of the loop that amends a parameter a plan
ruling or a pinned fact sets: that ruling or fact is rewritten in place, marked with whose ruling it is, so a reader
sees the current parameter ([process.md](../process.md) §Canonical and pointer sites, the record freeze; §Model
policy, Records). A plan is a record: where the design's body or a report differs from it, they are the live text.

**Reading the table.** *Status* is planned until the implementation PR merges, then implemented. *PR* names the
planning PR that merged the plan and, once it has run, the PR that executed it. *Gate record* links the rows of the
design's decision log, or of its companion log where the review records have moved ([process.md](../process.md)
§Doc taxonomy), that record the plan's gate rounds. *Live home of* names what the plan still holds alone, which its
banner repeats. A new plan gets its row in its planning PR (§II, the hard stop); the implementation PR fills the rest. A
PR's number, in this table and in a plan's banner, is written once the PR is open, by one more commit
([process.md](../process.md) §II, stage 7).

| Date | Item | Plan | Status | PR | Gate record | Live home of |
|---|---|---|---|---|---|---|

**The banner.** Every executed plan carries one blockquote under its "For agentic workers" line, written by the PR that
executed it: *Record — implemented in PR #N (‹the PR's date›). Not maintained: paths, line numbers, code and counts
are as of the plan; the tree and ‹the design› are authoritative. Index: README.md.* A plan that is still cited for text
it holds alone adds what is cited and where the live rule is.
