# Survey and literature

## What

A survey session reviews the external landscape on a recurring basis and keeps the result as one standing document with
a watchlist, using a literature tool and a runbook; an independent verification pass checks every citation before
anything lands (process.md §III).

## Why

A survey's failure mode is a confident wrong citation, and the witness that catches it is the primary source. The first
verification pass over a survey's findings found mismatches in what it attributed to its sources: wrong identifiers,
pages and years, a result cited without the conditions it holds under, an inference that read as a source's claim. So
the pass is the survey's own gate: a fresh subagent re-finds every claim in the filed source and reports, and the
orchestrator fixes or deletes each mismatch (process.md §III; the literature runbook, section 5). A sweep starts from
what the last one left and resolves every seed before citing it, since titles from memory are right more often than
venues and years (the runbook, section 3).

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the survey session (§III), its taxonomy row and its exemption
  from the record freeze.
- [starter/tools/lit.py](../starter/tools/lit.py) — the literature tool, standard library only: search, refs, cites,
  resolve, fetch, index, budget and check.
- [starter/tests/test_lit.py](../starter/tests/test_lit.py) — its offline tests, over recorded fixtures.
- [starter/docs/runbooks/literature-search.md](../starter/docs/runbooks/literature-search.md) — the procedure, the
  verification pass, and what transfers at work.
- [starter/docs/reports/literature-review.md](../starter/docs/reports/literature-review.md) — the standing survey, with
  its sweep log and watchlist.
- [starter/docs/papers/REQUESTS.md](../starter/docs/papers/REQUESTS.md) — the owner's queue of paywalled papers.
- [starter/docs/handoffs/HANDOFF-research-setup.md](../starter/docs/handoffs/HANDOFF-research-setup.md) — the standing
  setup handoff: key file, keys, optional servers.
- [starter/docs/skeletons/kickoff-survey-session.md](../starter/docs/skeletons/kickoff-survey-session.md) — the survey
  session's prompt.

## Depends on

- [`handoffs-and-monitors`](handoffs-and-monitors.md) — the setup is a standing handoff; every key-holding action is the
  owner's.
- [`evidence-rules`](evidence-rules.md) — raw page text for a web source, and each citation checked.
- [`model-policy-and-seats`](model-policy-and-seats.md) — a survey session is of the implementation class; its subagents
  are named per dispatch.
- [`one-home-per-fact`](one-home-per-fact.md) — the survey is a living document, exempt from the record freeze.
- [`worktrees-and-checkouts`](worktrees-and-checkouts.md) — a survey session starts in a worktree.
- [`the-two-session-loop`](the-two-session-loop.md) — a survey can come before an ideation; its findings land by pull
  request.
- Python 3.9 or later, `curl`, and optionally `uv` with the arXiv MCP server (SETUP.md, items 6 and 7).

## Variants

- **The default.** The tool's four sources, the repository as the store of filed papers, and a standing survey of six
  sections.
- **At work.** The literature is prior art, vendor documentation and the organisation's own records: the sweep, the
  primary-source rule and the verification pass transfer, the tool's four sources do not (the runbook, "At work").
- **A reference manager as the store.** The runbook keeps the repository as the store and says when to revisit it: when
  the papers outgrow one index table or a second person joins.
- **A repository others can read.** Only open-access copies are filed in it, and a paywalled one stays out of git; the
  runbook's fill comment records whether the repository is private.

## Grafting

1. Settle the checklist rows this touches: the host's own privacy rules for documents, layout and vocabulary, and the PR
   review as the owner's gate (ADOPTING.md).
2. Write the survey session (§III), the Survey row of the taxonomy and the record freeze's exemption into the host's
   process.md, in its vocabulary.
3. Copy the tool with its tests, the runbook, the survey, the queue, the setup handoff and the kickoff; fill their
   tokens, the repository's address in the tool's `LIT_REPO_URL` default among them, and answer their fill comments, the
   handoff's manifest apart (ADOPTING.md, the placeholder table and step 2).
4. Once the adoption has merged, instantiate the setup handoff's manifest by a second, small pull request (ADOPTING.md,
   step 11); the first survey session then runs it, the owner holding every key.
5. **Entering later.** Until then the host's own way of reading the field stands, and the texts of step 2 stay out of
   its process.md. Where the starter's text names the survey, reword it or cut it; the main sites are the model policy's
   class sentences, the handoff section's mentions of the research setup, the planning kickoff's survey-trigger clause,
   the doc map's rows for the reports, runbooks and papers, and AGENTS.md's tool lines and key rule.
   `git grep -n -i -E 'survey|literature|lit\.py|watchlist|research setup|papers|III'` finds the rest (process.md
   §Canonical and pointer sites).
