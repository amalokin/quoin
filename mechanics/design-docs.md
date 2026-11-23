# Design docs

## What

Every roadmap item has one design doc, written in an ideation session to a fixed house shape: the place where the item's
decisions, the anchor that certifies it, its open obligations and a dated log of rulings live. A depth marker in its
header says how finished it is, and so whether it may be planned yet (process.md §I).

## Why

A full design for every item was chosen over lean seeds, knowing it would be shallow; the depth marker keeps it honest
about that. Three rules keep a design usable by a fresh session. Its header is budgeted and names what to read first,
because one design had grown so long that planning from it needed only a few thousand of its words. Its log is
append-only, because code, tests and plans cite rows by id, date and title, and an edited or renumbered row breaks every
citation. And its open items sit in its active obligations, because a minor parked only in a local ledger is lost to the
next session (process.md §I, the house shape of a design doc; §II, stage 7).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the ideation session and the house shape (§I), the Design and
  Companion log rows (§Doc taxonomy) and the header budgets (§Budgets).
- [starter/docs/skeletons/design.md](../starter/docs/skeletons/design.md) — the house shape as headings with a guidance
  line each.
- [starter/docs/designs/](../starter/docs/designs/) — where designs live, empty until the first one.
- [starter/docs/id-registry.md](../starter/docs/id-registry.md) — the series a design's decisions, anchors and rulings
  register in.
- [starter/docs/doc-budgets.json](../starter/docs/doc-budgets.json) — the design headers' rows and budget.
- [starter/tools/doc_budgets.py](../starter/tools/doc_budgets.py) — the check of each design's row and header budget.
- [starter/CLAUDE.md](../starter/CLAUDE.md) — the doc-map row for `docs/designs/`.
- [starter/docs/roadmap.md](../starter/docs/roadmap.md) — each entry's Design line, which links its design.

## Depends on

- [`roadmap-as-the-spec`](roadmap-as-the-spec.md) — a design belongs to an item; its header cites the item and its
  anchor.
- [`the-two-session-loop`](the-two-session-loop.md) — an ideation session writes it and ends at its pull request.
- [`plans`](plans.md) — a plan implements one design and names its gate record in the design's log.
- [`adversarial-gates`](adversarial-gates.md) — the design gate's rounds are rows of the log.
- [`one-home-per-fact`](one-home-per-fact.md) — the log as a pair, rewriting in place and the header budget.
- `tools/doc_budgets.py` — fails a design with no budgets row, and holds its header to its budget.
- `superpowers:brainstorming` — the skill an ideation session may use.

## Variants

- **The default.** One design per item under `docs/designs/`, and a companion log beside it once a wave's review records
  pass the contract's threshold (process.md §I).
- **A flat layout.** `docs/<slug>-design.md` (process.md §Conventions). The document check finds designs only where its
  layout constants say, so a flat host gets no design checks until they are set (ADOPTING.md, the layout note).
- **Decision records.** A host that keeps short architecture decision records keeps them for single decisions. The
  design stays the item's document and cites them, so that decisions have one home.

## Grafting

1. Settle the checklist rows this touches: layout and vocabulary (where designs live), budgets on or off and the id
   registry on or off (ADOPTING.md).
2. Write the ideation session (§I) into the host's process.md in its vocabulary, with the Design and Companion log rows
   (§Doc taxonomy).
3. Copy `docs/skeletons/design.md` into the host's skeletons and create the designs folder. The first design is the
   reconciliation itself, written in this shape by the fusion session (ADOPTING.md, Path B).
4. With the registry on, copy `docs/id-registry.md`; a new series gets its row in the pull request that introduces it.
5. With the budgets on, give each design its row in `design_headers` by hand in its first pull request, since the check
   fails on a design without one (process.md §Budgets).
6. Link each design from its roadmap entry's Design line, and add the doc-map row for `docs/designs/` to CLAUDE.md.
7. **Entering later.** Until then the host's own decision records stand, and the texts of step 2 stay out of its
   process.md. Where the starter's text reads a design, name the host's records instead or cut it; the main sites are
   stage 1's reading order, stage 3's missing-design rule, the plan check's gate-record and depth-marker clauses, stage
   7's header and obligations sentences, the plans index's gate-record column and the doc-map row.
   `git grep -n -i -E 'design doc|decision log|depth marker|Active obligations'` finds the rest (process.md §Canonical
   and pointer sites).
