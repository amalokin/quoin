# Evidence rules

## What

The repository's claims are written so that someone who was not there can check them, and three things cheapest to fake
have rules of their own: a quoted web page, a claim of test coverage and a judgment that needs the owner's eye
(process.md §Purpose and principles, Evidence over vibes).

## Why

Each rule was paid for once. A report's first pass, written through a summariser, produced a false verdict and
paraphrases presented as quotes, so a web source is quoted from the page itself. A review's mutation probe found a test
that still passed with the thing it guarded broken, so a coverage claim needs a mutation check. A wrong claim in the
file every gate reads would mislead every review after it, so a number or a claim with no source is a defect before it
is a matter of style. And the owner cannot judge a picture from the numbers behind it, so an anchor that needs the
owner's eye ships a rendering. The plan's version of the rule, a formula with no observation behind it, is told on
[`plans`](plans.md).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the Evidence over vibes bullet (§Purpose and principles) and
  the sourcing rules of stage 3 (§II).
- [starter/AGENTS.md](../starter/AGENTS.md) — the testing line on coverage claims, and the agent instruction pointing at
  the rules.
- [starter/.claude/agents/reviewer.md](../starter/.claude/agents/reviewer.md) — its Cover on recomputing figures, and
  the web-source rule.
- [starter/.claude/agents/counsel.md](../starter/.claude/agents/counsel.md) — the same web-source rule.
- [starter/docs/skeletons/plan.md](../starter/docs/skeletons/plan.md) — the pinned facts, and the mark for an unpinned
  formula.
- [starter/docs/skeletons/report.md](../starter/docs/skeletons/report.md) — the outcome with its label, each figure with
  its command.

## Depends on

- [`plans`](plans.md) — a plan's numbers carry their sources.
- [`design-docs`](design-docs.md) — rulings and dismissals are log rows; an anchor's result is a labelled line.
- [`roadmap-as-the-spec`](roadmap-as-the-spec.md) — an anchor is the check that certifies an item.
- [`adversarial-gates`](adversarial-gates.md) — a dismissed finding gets a ruling, like an incorporated one.
- [`model-policy-and-seats`](model-policy-and-seats.md) — the seats' charters carry the web-source rule and the
  reviewer's Cover on figures.
- [`one-home-per-fact`](one-home-per-fact.md) — a figure keeps its label wherever it is copied.
- [`survey-and-literature`](survey-and-literature.md) — its verification pass checks each citation.
- `curl` and the host's test runner — raw page text, and the mutation check.

## Variants

- **The default.** A citation is a measurement, an anchor or `path:line`, and a coverage claim needs a mutation check.
- **A coverage percentage as the claim.** A host with a line-coverage gate in its CI keeps the gate. It shows which
  lines ran, not that a test can fail, so the mutation check stays for any claim that a test guards something.
- **Citations as links.** A host whose documents are read on its forge may cite a file and line as a permalink.

## Grafting

1. Settle the checklist rows this touches: the host's quality gates as the fast suite, and the host's privacy rules for
   documents, since a cited path or a recorded measurement can name something private (ADOPTING.md).
2. Write the Evidence over vibes bullet (§Purpose and principles) and stage 3's sourcing bullets (§II) into the host's
   process.md, in its vocabulary. The host's own sources, a benchmark's recorded run or a CI log, count as sources
   there.
3. Add the two lines to AGENTS.md, the coverage claim and the pointer at the rules, and the web-source rule to the seat
   charters where the host has them.
4. Name the host's mutation tool in AGENTS.md, or say that a mutation is made by hand, and ask for a mutation check
   wherever a task claims coverage.
5. Carry the plan skeleton's pinned-facts rule and the report skeleton's labelled outcome into the host's plan and
   report templates, where it has them.
6. **Entering later.** Until then the host's own standards of proof stand, and the texts of step 2 stay out of its
   process.md. Where the starter's text points at the rules, reword it or cut it; the main sites are AGENTS.md's
   coverage line and agent instruction, the web-source line in both seat charters, the reviewer's Cover on numbers and
   the plan and report skeletons.
   `git grep -n -i -E "evidence over vibes|raw page text|mutation|unpinned|file:line|evidence rules"` finds the rest
   (process.md §Canonical and pointer sites).
