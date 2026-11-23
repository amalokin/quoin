# One home per fact

## What

Every fact has one canonical home and every other site points at it. Status sites are replaced at merge, never appended
to, within word budgets that one check holds, and a changed rule is rewritten in place, with its history kept in a log
(process.md §Canonical and pointer sites; §Budgets).

## Why

An audit of a repository's documents found that most of its boot file's status and most of its roadmap restated content
that had a canonical home, and the copies had drifted: stale figures, a stale finding, the queue stated in several
versions and a superseded policy still standing at several sites. The old rule, keep the status current, had let a
status outgrow reading ([`roadmap-as-the-spec`](roadmap-as-the-spec.md)). What held was one home per fact: a pointer
site carries a link and, at two sites, a headline with its label, and a check fails a file over its budget (process.md
§Canonical and pointer sites; §Budgets). A claim is grepped at every site before it is edited, since contradictory live
text is a bug a reviewer must flag.

## Files

- [starter/docs/process.md](../starter/docs/process.md) — the canonical and pointer sites, the record freeze, the
  budgets and the taxonomy's last column.
- [starter/docs/doc-budgets.json](../starter/docs/doc-budgets.json) — the budgets' numbers, which live nowhere else;
  `init` writes it for a host.
- [starter/tools/doc_budgets.py](../starter/tools/doc_budgets.py) — the document check: budgets, status rules, no hash
  at a status site, resolving links.
- [starter/tests/docs/test_doc_budgets.py](../starter/tests/docs/test_doc_budgets.py) — the check as a test, for a
  pytest suite.
- [starter/tests/conftest.py](../starter/tests/conftest.py) — puts the repository's root on the import path for the
  starter's tests, the wrapper test's `from tools import doc_budgets` among them.
- [starter/CLAUDE.md](../starter/CLAUDE.md) — the pointer site every session loads: Status, doc map, Load-bearing facts.
- [starter/docs/roadmap.md](../starter/docs/roadmap.md) — status paragraphs, each a pointer site with one headline.
- [starter/docs/id-registry.md](../starter/docs/id-registry.md) — where each decision series' text lives.
- [starter/docs/process-log.md](../starter/docs/process-log.md) — the contract's history, which process.md leaves out.

## Depends on

- [`roadmap-as-the-spec`](roadmap-as-the-spec.md) — a status paragraph is a pointer site, replaced within its budget.
- [`design-docs`](design-docs.md) — the log as a pair, rows never edited, the header budget.
- [`plans`](plans.md) — the record freeze: a banner and an index row.
- [`evidence-rules`](evidence-rules.md) — a figure keeps its label wherever it is copied.
- [`the-two-session-loop`](the-two-session-loop.md) — stage 7 replaces the status sites in the pull request that changes
  them.
- [`working-with-the-owner`](working-with-the-owner.md) — memory is a pointer, and a chat ruling lands in the
  repository.
- `tools/doc_budgets.py`, with Python 3.9 or later (SETUP.md, item 6), and `git grep`.

## Variants

- **The default.** Budgets on, their numbers in the JSON alone and the check in the fast suite, and the id registry on.
- **Budgets off.** A host whose files will not take the check's shape keeps the rules and leaves the check out
  (ADOPTING.md, the note on budgets).
- **The check from CI.** A host whose suite is not pytest runs the check by its command from CI, not through the wrapper
  test (SETUP.md, item 6).
- **No id registry.** A host with few decision series may leave it off (ADOPTING.md, the checklist's row on it).

## Grafting

1. Settle the checklist rows this touches: layout and vocabulary, budgets on or off and the id registry on or off
   (ADOPTING.md).
2. Write the canonical and pointer sites, the budgets and the taxonomy's last column (§Canonical and pointer sites;
   §Budgets; §Doc taxonomy) into the host's process.md, in its vocabulary, with stage 7's replace-not-append rule (§II,
   stage 7).
3. Name each canonical home in the host's layout, and mark CLAUDE.md's Status, doc map and Load-bearing facts, the
   roadmap's status paragraphs and the design header as pointer sites.
4. With the budgets on, copy the check and, for a pytest suite, the wrapper test, which imports `tools.doc_budgets` and
   so needs the repository's root on the import path: copy the starter's `tests/conftest.py` where the host has no such
   file, merge its lines into the host's own where it has one, and add nothing where the host already puts its root on
   the path another way. The starter's conftest and wrapper sit at `tests/conftest.py` and
   `tests/docs/test_doc_budgets.py` and find the root in their `ROOT` lines by counting directories up from their own
   paths, `parents[1]` and `parents[2]`: where a file of the host sits at another depth, set its count to the number of
   directories between that file and the root. Let `init` write the budgets file from the host's own files, then run
   `check` (ADOPTING.md, the note on budgets) and the wrapper by the host's own test command, since `check` reads
   neither count; with the registry on, copy it too.
5. Move the contract's history into `docs/process-log.md`, so that process.md states the current rule only.
6. **Entering later.** Until then the host's own way of keeping its documents current stands, and the texts of step 2
   stay out of its process.md. Where the starter's text names a site, a budget or the registry, reword it or cut it; the
   main sites are the principles' one-home bullet, stage 7's replace rule, the roadmap upkeep's status template, both
   charters' citations of the sites, CLAUDE.md's digest bullet and AGENTS.md's document-check lines.
   `git grep -n -i -E 'canonical|pointer site|budget|id.registry|status site'` finds the rest (process.md §Canonical and
   pointer sites).
