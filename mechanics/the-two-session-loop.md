# The two-session loop

## What

Every item is planned in one session and implemented in another, and the owner starts both. The planning session ends at
the planning pull request, which the owner merges. The implementation session starts fresh from that merged plan, runs
the plan check, carries the plan out and cuts the pull request the owner reviews.

## Why

In one item a planning session passed its plan through the adversarial gate and went on to implement it: the digest's
next line chained the two steps, and the gate stood in for the owner's review. A gate is not that review: the hard stop
puts the owner's review between the plan and the code and compute spent on it. The plan check is the other half: a
session with no merged, gated plan stops and flags it, where it would improvise (process.md §II, the hard stop and the
plan check). The two session classes have a second reason: the strongest model's weekly allowance ran out mid-item, and
the implementation class finished it from a written handoff, with no loss in quality (process.md §Model policy).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the loop (§II) and the session classes (§Model policy).
- [starter/docs/skeletons/kickoff-planning-session.md](../starter/docs/skeletons/kickoff-planning-session.md) — the
  planning prompt.
- [starter/docs/skeletons/kickoff-implementation-session.md](../starter/docs/skeletons/kickoff-implementation-session.md)
  — the implementation prompt.
- [starter/docs/skeletons/pr-description.md](../starter/docs/skeletons/pr-description.md) — the layered description of
  both pull requests.
- [starter/CLAUDE.md](../starter/CLAUDE.md) — the digest bullets on the sessions, and the Next line.
- [starter/.gitignore](../starter/.gitignore) — the `/local/` entry.

## Depends on

- [`roadmap-as-the-spec`](roadmap-as-the-spec.md) — the entry names the plan.
- [`design-docs`](design-docs.md) — the plan check reads its depth marker and gate record.
- [`plans`](plans.md) — the hard stop's product.
- [`subagent-driven-development`](subagent-driven-development.md) — stage 5.
- [`working-with-the-owner`](working-with-the-owner.md) — the reports and the asks.
- [`the-small-change-lane`](the-small-change-lane.md) — the exception, and the ratchet back.
- [`adversarial-gates`](adversarial-gates.md), [`model-policy-and-seats`](model-policy-and-seats.md),
  [`counsel-triggers`](counsel-triggers.md) — `later` rows this one needs: the design gate's record, both seat types,
  the triggers.
- [`worktrees-and-checkouts`](worktrees-and-checkouts.md) — each session's worktree off `origin/main`.
- Superpowers (`superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:subagent-driven-development`), the
  Codex plugin, `gh` and git — skills, gates, pull requests, the ancestry test.

## Variants

- **The default.** Two classes on two models; one plan, one session, one ledger named after the plan's file (process.md
  §II, stage 5).
- **One model for every class.** A host offered a single model binds each class to it; the split still pays, in the hard
  stop and the fresh context (process.md §Model policy, The binding table).
- **A plan executed in parts, one session each.** Each session begins its own ledger, named for the plan and the part,
  but a session that resumes the same plan after an in-place amendment continues its ledger. A continuation's kickoff
  names its ledger and the preceding part's merged pull request, which its plan check tests as an ancestor. The contract
  has no such rule; a host that wants it adds it to its process.md and log.

## Grafting

1. Settle the checklist rows this touches: the PR review as the owner's gate, the models and the seats' binding, Codex's
   availability and where the ledger lives (ADOPTING.md).
2. Write the loop (§II) into the host's process.md in its own words for sessions and branches, with the scope sentence
   (ADOPTING.md, Path B). Its Checkouts paragraph goes with [`worktrees-and-checkouts`](worktrees-and-checkouts.md), its
   stage 5 with [`subagent-driven-development`](subagent-driven-development.md).
3. Copy the two kickoffs and `pr-description.md` into the host's skeletons, and append `/local/` to its `.gitignore`.
4. Bind what the plan check reads: a design with a depth marker and a gate record, and both seat types (process.md §II,
   Implementation session).
5. Write CLAUDE.md's Status and Next lines to name sessions one by one, never a chain (process.md §Roadmap upkeep), with
   the digest bullets on the sessions.
6. Run the first item as two sessions, the owner's merge between them.
7. **Entering later.** The host's own flow stands until then. The loop (§II) stays out of its process.md, its Checkouts
   paragraph too until [`worktrees-and-checkouts`](worktrees-and-checkouts.md) is taken. Reword or cut the text that
   names the sessions; the main sites are CLAUDE.md's digest bullets and Next line, AGENTS.md's session-class bullet,
   both kickoffs and, in process.md, the ideation paragraph, the Plan row, the roadmap upkeep's last bullet and the
   model policy's class sentences (§I; §Doc taxonomy; §Roadmap upkeep; §Model policy).
   `git grep -n -E 'planning (session|PR|class)|implementation (session|class)|hard stop|plan check'` finds the rest
   (process.md §Canonical and pointer sites).
