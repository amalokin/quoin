# Id registry — where each decision series lives

Decisions, rulings and findings carry ids (`Q4`, `A2`, `R-1-3`, `F7`, `O2`), and code, tests and documents cite them
without their document. This table gives each **series** the one document and section that hold its **effective
text**, the place where its **rulings and history** sit, and its **collisions**: a letter that two series use means
nothing bare until its series is known. Where a live decision's text lives, and why, is
[process.md](process.md) §Canonical and pointer sites; the digest is [CLAUDE.md](../CLAUDE.md). The plans and the
handoffs are indexed in [plans/README.md](plans/README.md) and [handoffs/README.md](handoffs/README.md).

**Reading a row.** *Pattern* is a regular expression that lists the series' citing documents over `docs/`. It is in
Perl or Python syntax (with `\b`), so run it with a tool that reads that syntax, such as `rg` or `git grep -P`; whether
`grep -E` reads `\b`, or `grep` has `-P`, depends on the platform. Inside the table a pattern's `|` is written `\|`,
Markdown's escape for a pipe in a cell: read it, and run it, as `|`. A quoted *anchor* is a heading, or the title of a
decision-log row, in the document named before it: find it with `grep -n -F "<anchor>" <document>`. "The design's
decision log" is the table headed *Decision log* in the design; a row that has moved to a companion log
(`<slug>-design-log.md`) is cited by its date and title there. Ids are never renumbered; a row is amended in the PR
that moves its anchors.

| Series | Pattern | Effective text | Rulings and history | Collisions and notes |
|---|---|---|---|---|
| **Q · a design's decisions** | `\bQ[0-9]{1,2}\b` | the decisions section of the design's body: `docs/designs/<slug>-design.md` | the design's decision log: the rationale, the gate rounds, the owner's and counsel's rulings | A series belongs to one design: the first design is its holder, and the path shown is its path; a later design registers a series of its own here, in the PR that adds it. |
| **A · validation anchors** | `\bA[0-9]{1,2}\b` | the validation-anchor section of the design; the roadmap entry's Anchor line names the check | the item's report, where the anchor's result is recorded with its label | One series per design, like Q. |
| **R · plan rulings** | `\bR-[0-9A-Za-z]+-[0-9]{1,2}\b` | the rulings section of the plan, with their evidence and cost if wrong: `docs/plans/YYYY-MM-DD-<slug>.md` | mirrored into the design's decision log; a ruling that amends a plan parameter is rewritten in place in the plan, marked with whose ruling it is | Written `R-<item>-<n>`, the roadmap item and then the ruling's number, so one plan's R never collides with another's. |
| **F · pinned facts** | `\bF[0-9]{1,2}\b` | the pinned-facts section of the plan: each a verified value the plan builds on, with the observation that pins it | the design's decision log, where a ruling amends one; the item's report, for measured figures | Restarts in each plan, so outside its plan an F is cited with the plan. |
| **O · owner decisions** | `\bO[0-9]{1,2}\b` | the design's decision log: the rows the owner ruled, in their dated order | a standing one is also a dated line in the roadmap's Standing decisions | One series per design, like Q. A ruling made in chat: process.md §II, stage 8. |

<!-- fill: one row per series the project introduces, above this line: its letter and what it numbers, its pattern, the document and section of its effective text, where its rulings and history sit, and the series it collides with; the rule is a row in the PR that introduces the series (process.md §Doc taxonomy) -->

## Collisions — telling a bare id apart

A bare id is read by the words beside it, such as the document it sits in or the plan a neighbouring id names, and,
failing them, by its subject.

<!-- fill: this project's collisions, one paragraph per letter that more than one series uses: the series that share it, the files that cite each, and the words that tell them apart; the rule is a paragraph in the PR that creates the collision -->

**Not decision ids.** A task's number in a plan, a roadmap item's number, a wave's letter and a line citation written
`L<n>` after a document's name look like ids and are not.

<!-- fill: the project's other look-alikes, such as a part number or a version label; the rule is one line each -->

## Keeping it current

A new series gets a row in the PR that introduces it (process.md §Doc taxonomy). The document check verifies that this
file's links resolve, not its anchors: a renamed heading, or a decision log split from its companion log, moves
anchors, and the PR that moves them updates the rows. Before relying on a row, run its `grep -n -F`.
