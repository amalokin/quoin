# Working with the owner

## What

The owner is the reviewer and the decision-maker, and the loop spends the owner's attention only where nothing else can
answer: a session asks the owner only what only the owner can answer, its reports lead in plain words, and what the
owner rules in chat is written into the repository (process.md §II, the opening and stages 7 and 8).

## Why

The owner's review is the one gate no session can stand in for, and the owner's time is the loop's scarcest input. Two
corrections shaped the rules. Pull request descriptions thick with internal labels and ruling ids were called obtuse, so
the top layer is plain words and each ask says what it needs, why and by when (process.md §II, stage 7). And a bundle of
asks, some needing more research, was sent back to be unbundled, so the owner's practice is one decision to an ask,
which the contract does not carry (see Variants). A ruling made in chat lands in the repository because a rule that
lives only in an assistant's memory is how rules get lost (process.md §II, stage 8; §Purpose and principles).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the loop's opening on asking and stages 7 and 8 on reports and
  chat rulings (§II), and the note on memory (§Purpose and principles).
- [starter/docs/skeletons/pr-description.md](../starter/docs/skeletons/pr-description.md) — the layered description, and
  the rulings made in the owner's place.
- [starter/docs/skeletons/kickoff-implementation-session.md](../starter/docs/skeletons/kickoff-implementation-session.md)
  — the closing "Asking the owner" section, which the planning kickoff has too.
- [starter/CLAUDE.md](../starter/CLAUDE.md) — the digest bullet on asking.
- [starter/docs/roadmap.md](../starter/docs/roadmap.md) — the owner's open items in "Now and next", and the standing
  decisions.

## Depends on

- [`the-two-session-loop`](the-two-session-loop.md) — the hard stop's description, stage 7's report, stage 8's rulings.
- [`roadmap-as-the-spec`](roadmap-as-the-spec.md) — the owner's open items, and the standing decisions a chat ruling can
  become.
- [`design-docs`](design-docs.md) — the decision log, where a chat ruling lands.
- [`model-policy-and-seats`](model-policy-and-seats.md) — a provisional ruling or a skipped seat is listed in the pull
  request for the owner.
- [`one-home-per-fact`](one-home-per-fact.md) — memory is a pointer, and a rule lives in the repository.
- `gh` — the pull request description.

## Variants

- **The default.** One owner, whatever the title, whose review of the pull request is the merge gate (process.md
  §Conventions; §Purpose and principles).
- **One decision to an ask.** Each question of a batch holds one decision, its options and a recommendation, after the
  session and its reviewers have tried to settle it. The contract has no such rule: a host that wants it adds it to its
  process.md and log.
- **Reviewers beside the owner.** At work, the service's owner answers the asks while the host's reviewers or code
  owners approve the pull request, and their approval is the gate (ADOPTING.md, the checklist's row on the PR review).

## Grafting

1. Settle the checklist row on the PR review as the owner's gate: who answers the asks, and who approves a merge
   (ADOPTING.md).
2. Write the loop's opening on asking, stage 7's reporting rule and stage 8's rule on chat rulings (§II) into the host's
   process.md, in its vocabulary.
3. Copy `docs/skeletons/pr-description.md` with its sections nested inside the headings of the host's pull request
   template, the top layer first, and leave the template's own file as it is (ADOPTING.md, Path B); a host whose owner
   wants the sections in that file edits it by the host's own rules.
4. Copy the "Asking the owner" section into the host's kickoffs and the digest bullet on asking into CLAUDE.md.
5. End "Now and next" with the owner's open items, as the roadmap skeleton does.
6. Tell the sessions where a chat ruling lands: the next pull request that touches the design, in its decision log or
   the standing decisions.
7. **Entering later.** Until then the host's own way of asking and reporting stands, and the texts of step 2 stay out of
   its process.md. Where the starter's text sends a report or an ask to the owner, reword it or cut it; the main sites
   are the hard stop's description sentence, the records of the model policy (§Model policy), CLAUDE.md's digest bullet
   on asking, AGENTS.md's pull request line, both kickoffs' last section and the roadmap's open items.
   `git grep -n -i -E "only what only the owner|high-level layer|owner's open items|in the owner's place"` finds the
   rest (process.md §Canonical and pointer sites).
