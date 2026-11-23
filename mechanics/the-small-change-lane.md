# The small-change lane

## What

The lane is for changes too small for the loop, a typo or a one-line fix: they land through a branch and a pull request
that the owner reviews, with none of the loop's ceremony. Whether a change is small is a judgment call, which a one-way
ratchet back into the loop and a retrospective review of inline work keep honest (process.md §Small-change lane).

## Why

Ceremony should be in proportion to the change. A design, a plan and gates around a typo cost more than they protect, so
the owner's review stands alone for a change that small. The lane stays honest at its two edges: a change that grows
leaves the lane at once, and work that went around the loop is reviewed after the fact. When a tool that an orchestrator
had written inline, outside the loop, was reviewed afterwards, the review found defects, a credential-handling flaw
among them (process.md §Small-change lane).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the lane (§Small-change lane), the hard stop's exception for
  what the owner sanctions in a planning session (§II) and the lane's place in the class sentences (§Model policy).
- [starter/CLAUDE.md](../starter/CLAUDE.md) — the digest bullet that sends trivial fixes to the lane.
- [starter/docs/skeletons/pr-description.md](../starter/docs/skeletons/pr-description.md) — the "Open and ungated"
  section, which lists inline work that belonged in the loop.
- [starter/AGENTS.md](../starter/AGENTS.md) — the commit and pull request guidelines that the lane's pull request
  follows like any other.

## Depends on

- [`the-two-session-loop`](the-two-session-loop.md) — where a change that has grown goes.
- [`working-with-the-owner`](working-with-the-owner.md) — the owner's review is the lane's only gate.
- [`adversarial-gates`](adversarial-gates.md) and [`model-policy-and-seats`](model-policy-and-seats.md) — a
  retrospective review is a gate round or a seat's review.
- `gh` and git — the branch and the pull request.

## Variants

- **The default.** The session's judgment draws the line, and the retrospective review checks that judgment after the
  fact.
- **A written bar.** A host may state what counts as small in its own terms, such as a path, a size or a label its CI
  reads. That replaces the judgment call and keeps the ratchet and the retrospective review.
- **The host's reviewers as the gate.** Where the host requires its reviewers' approval on every pull request, theirs is
  the lane's gate in place of the owner's (ADOPTING.md, the checklist's row on the PR review).

## Grafting

1. Settle with the host what counts as small, in its own words, and the checklist rows on commit style and on the PR
   review as the owner's gate (ADOPTING.md).
2. Write the lane (§Small-change lane) into the host's process.md in its vocabulary, with the ratchet and the
   retrospective review.
3. Add the digest bullet to CLAUDE.md, and keep the "Open and ungated" section of `pr-description.md` in the host's
   copy, nested with the rest inside the headings of the host's pull request template, so that the declaration of
   inline work has a place; the template's own file is left as it is (ADOPTING.md, Path B).
4. Tell the sessions what the lane skips and what it keeps: no design, plan or gate, but the host's branch rules, its
   checks and its review.
5. Name who runs the retrospective review: a gate round or the reviewer seat, so the lane needs one of
   [`adversarial-gates`](adversarial-gates.md) and [`model-policy-and-seats`](model-policy-and-seats.md), or else the
   host's own reviewer, named in the reconciliation.
6. **Entering later.** Until then every change goes through the host's own path, and the lane stays out of its
   process.md. Where the starter's text names the lane, reword it or cut it; the main sites are the hard stop's
   exception for what the owner sanctions, the class sentences of the model policy and the digest bullet in CLAUDE.md.
   `git grep -n -i -E 'small-change|small change|inline work|did inline'` finds the rest (process.md §Canonical and
   pointer sites).
