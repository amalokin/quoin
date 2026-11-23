# Explainers

## What

An explainer is a basics-to-advanced write-up of a method the project uses, kept behind an index, so that a fresh
session or a reviewer can ramp up on the method without rebuilding it from the code. Each carries a currency line, and
the index says where it stands against the rulings that amended it (process.md §Doc taxonomy, the Explainer row).

## Why

A design states what was decided and a report what was measured; an explainer teaches the method from its reader's level
up, gently enough to reconstruct it from first principles (the explainers index's fill comment). It also goes stale, so
each opens with a currency line naming the rows that amended its math (process.md §Doc taxonomy, the Explainer row), and
its row in the index says where it stands against them. A later measurement and a later reading of the real system once
amended some of one explainer's rules: its banner then said which sections were out of date and where the current
formulas were, and its rendering was retired until the math was re-derived, which the contract has no rule for. The
Markdown is the source of truth, and a rendering names the file and the commit it was made from (the index).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the Explainer row of the taxonomy, the document-review variant
  that puts one through a gate and the explanation as a canonical site.
- [starter/docs/explainers/00-index.md](../starter/docs/explainers/00-index.md) — the index: the audience (a fill
  comment), a row per explainer with what it feeds and where it stands, and the rendering's rule.
- [starter/docs/skeletons/explainer.md](../starter/docs/skeletons/explainer.md) — the house shape: the currency line,
  what it is for, basics, advanced.
- [starter/tools/doc_budgets.py](../starter/tools/doc_budgets.py) — the document check, whose link scan covers every
  Markdown file under `docs/`, the explainers among them.
- [starter/CLAUDE.md](../starter/CLAUDE.md) — the doc-map row that points a session at the index.

## Depends on

- [`design-docs`](design-docs.md) — a design's header names its explainer, and a ruling that amends the math is a log
  row the currency line names.
- [`one-home-per-fact`](one-home-per-fact.md) — the explanation has its one home here, and a pointer to it carries a
  link, not a copy.
- [`adversarial-gates`](adversarial-gates.md) — the document-review variant puts an explainer through a gate.
- [`evidence-rules`](evidence-rules.md) — an explainer's numbers carry their sources.
- A renderer of the host's choice, only if it wants a rendering.

## Variants

- **The default.** Markdown with LaTeX math and figures as committed SVGs, canonical in the repository behind the index,
  with a rendering regenerated at milestones if the host wants one.
- **No rendering.** A host whose forge renders Markdown and math reads the source and keeps none.
- **Explainers without math.** A host whose methods are architectures or protocols writes the same shape in prose: what
  it is for, basics, advanced.
- **A wiki or a docs site.** The contract has no such rule: its explainer lives in the repository. A host that keeps
  them elsewhere names that site as the explanation's canonical site in its process.md and keeps only a link in the
  index (process.md §Canonical and pointer sites).

## Grafting

1. Settle the checklist rows this touches: layout and vocabulary (where explainers live) and the host's own privacy
   rules for documents (ADOPTING.md).
2. Write the Explainer row of the taxonomy and the document-review sentence into the host's process.md, in its
   vocabulary.
3. Copy the index and the skeleton, and answer the index's fill comment with who reads the explainers and what they can
   already do.
4. Add the doc-map row to CLAUDE.md. With the budgets on, the check's link scan covers the explainers.
5. Write the first explainer from the skeleton and give it its index row in the same pull request; a pull request that
   amends the math an explainer teaches updates that row's Status.
6. **Entering later.** Until then the host's own explanations stand, and the texts of step 2 stay out of its process.md.
   Where the starter's text names an explainer, reword it or cut it; the main sites are the ideation paragraph's header
   list, the document-review sentence, the canonical sites' list, the doc-map row and AGENTS.md's docs line.
   `git grep -n -i explainer` finds the rest (process.md §Canonical and pointer sites).
