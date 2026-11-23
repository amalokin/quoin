# The roadmap as the spec

## What

The roadmap is the one file that says what the repository builds, in what order and in what state: each item's entry is
the spec a session reads, names the anchor that certifies the item and carries a status that each merge keeps current,
and "Now and next" is the one queue (process.md §II, stage 1; §Roadmap upkeep; §Purpose and principles, Validation
anchors).

## Why

A brief ages as the roadmap moves; the entry is the text a merge keeps current. In one item a session was handed a
previous session's working notes as its brief, took them for the spec and began work of another kind than the entry
described, until the owner redirected it to the roadmap. So the entry outranks every brief (process.md §II, stage 1).
The anchor is there for the same reason in time: later work builds on an item's result, so what certifies it must exist
before the work, and an item without one is not ready to implement (process.md §Purpose and principles, Validation
anchors). A status that every merge adds to outgrows reading, so a status paragraph is replaced, not appended to
([`one-home-per-fact`](one-home-per-fact.md)).

## Files

- [starter/docs/roadmap.md](../starter/docs/roadmap.md) — the skeleton: goal, "Now and next", an entry, parking lot,
  standing decisions.
- [starter/docs/process.md](../starter/docs/process.md) — four texts: the roadmap upkeep (§Roadmap upkeep), the Roadmap
  row (§Doc taxonomy), the Validation anchors bullet (§Purpose and principles) and stage 1's spec sentence (§II).
- [starter/CLAUDE.md](../starter/CLAUDE.md) — the doc-map row, Status and Next lines.
- [starter/docs/doc-budgets.json](../starter/docs/doc-budgets.json) — the roadmap's caps.
- [starter/tools/doc_budgets.py](../starter/tools/doc_budgets.py) — the check of the caps and of the status rules.

## Depends on

- [`design-docs`](design-docs.md) — each entry links its item's design, whose header repeats the anchor.
- [`the-two-session-loop`](the-two-session-loop.md) — the sessions read the entry, and the merge replaces its status.
- [`plans`](plans.md) — the entry names its plan, where the plan check starts.
- [`one-home-per-fact`](one-home-per-fact.md) — a status paragraph is a pointer site, replaced within its budget.
- `tools/doc_budgets.py` — the document check.
- `gh` — the forge's number for the "PR #N" a status line carries.

## Variants

- **The default.** Items, each with its design doc (process.md §Conventions, the first row) and its plan and report as
  they come. An item delivered in waves has an umbrella entry that carries its state alone, and a status paragraph per
  wave (process.md §Roadmap upkeep; §I).
- **Phases and sub-phases.** A host that already speaks of phases keeps the word and its numbering, and rewrites the
  Conventions row and every site that uses it together; entries, anchors and status paragraphs are the same.

## Grafting

1. Settle the checklist rows this touches: layout and vocabulary (items or phases, the file's path) and whether the
   budgets are on (ADOPTING.md).
2. Copy `docs/roadmap.md` into the host's docs, fill its tokens and fill comments as the
   [placeholder table](../ADOPTING.md#the-placeholders) says, and write the goal, linking the host's backlog.
3. Write each known item as an entry in dependency order, its anchor a check that exists in the host: its suite, a
   benchmark, a reference. The first entry is the adoption itself unless the owner names one (ADOPTING.md, Path B).
4. Write "Now and next" with a bullet per upcoming session, its class, its gate and its spec, naming sessions one by one
   and never as a chain.
5. Write those four texts into the host's process.md, and the doc-map row, Status and Next lines into CLAUDE.md.
6. With the budgets on, copy `tools/doc_budgets.py` and run `python3 -I tools/doc_budgets.py init`, then `check`
   (ADOPTING.md, the note on budgets).
7. **Entering later.** Until then the host's backlog does the roadmap's work, and those four texts stay out of its
   process.md. Where the starter's text names the roadmap, reword it to name the backlog or cut it; the main sites are
   stage 1's reading order, the plan check's first clause, the hard stop's status and queue sentence, stage 7's status
   sentences, CLAUDE.md's doc-map row, Status and Next lines, and both kickoffs' spec line. `git grep -n -i roadmap`
   finds the rest (process.md §Canonical and pointer sites). The document check needs `docs/roadmap.md`, so the budgets
   wait for it (ADOPTING.md, the note on budgets).
