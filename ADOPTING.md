# Adopting quoin

quoin comes in two forms (see [README.md](README.md)), so this guide has two paths. Path A is for a repository that has
no way of working yet: copy the starter whole, make it yours and start. Path B is for a repository that has conventions,
a CI and docs of its own: a session, the fusion session, reconciles them with the mechanics you choose, and the adoption
lands by pull request. Both start from a clone of the pack at a release tag, and both assume the environment
[SETUP.md](SETUP.md) describes: Claude Code, the plugins, the tools, and what degrades without each.

The rules these steps act on are [starter/docs/process.md](starter/docs/process.md)'s. This guide says what to do and
cites the section for why; it restates no rule. Commands run from the root of the repository being adopted and are
written `python3 -I tools/<tool>.py …`. The starter's own documents write the interpreter as `{{INTERPRETER}}`, which
the fill (step 2) turns into the repository's own spelling; this guide sits outside the starter and is never filled, so
it spells the interpreter `python3`. A word in angle brackets, such as ‹pack›, is yours to substitute.

## Path A — a fresh repository

You need an empty repository whose `main` already holds a first commit (a pull request needs something to land on), the
pack cloned beside it, and the owner to review the result. Steps 1 to 10 are the adoption, one pull request; step 11
instantiates the setup handoff by a second, small one once the first has merged; step 12 starts the work.

1. **Copy the starter.** Cut the adoption branch from `main` (`git switch -c docs/adopt-quoin`), then copy the whole of
   [starter/](starter/) into the repository's root, hidden files included: `cp -R ‹pack›/starter/. .` The starter's
   `README.md` and `.gitignore` replace any the first commit made: keep nothing of those, or merge them by hand from
   `main` (`git show main:README.md`).

2. **Fill the placeholders.** A placeholder is a token such as `{{PROJECT}}`; the table below this list says what each
   stands for and where. Replace every token with its value, `{{QUOIN_VERSION}}` apart (step 8), with a script or an
   editor's literal replace, since a quote, a backslash or `&` in a value (a lint command often has one) breaks a `sed`
   replacement. `git grep -nI --untracked -e '{{[A-Z_]*}}'` lists those left; it skips ignored files, a project's own
   `.venv/` among them.

   The starter also carries fill comments, `<!-- fill: what; the rule it follows -->`, which mark places for the
   project's own facts: write what a comment asks, following its rule, or delete it when there is nothing to say yet.
   Steps 3 to 7 take up the ones they name, and step 8 sweeps the rest.

3. **Write AGENTS.md's layout and commands.** [AGENTS.md](starter/AGENTS.md) is the repository's mechanics. Its fill
   comments ask for the layout, the install, build and run commands, the style and test conventions, the commit scopes,
   the constraints on agents and the security notes: write the layout and the commands now and the rest as far as the
   project knows them, with "none yet" for a line it has nothing for, here or in the README (a module, a command a
   reader can run). Keep the file factual and current, since the adversarial gate reads it with every diff.

4. **Write the roadmap's first items, each with its anchor.** [docs/roadmap.md](starter/docs/roadmap.md) is the spec the
   sessions work from. Write its goal, then each item you know as an entry under Items, in dependency order: what it
   delivers and what it does not, its Anchor, the check that certifies it before anything builds on it (an item without
   one is not ready to implement; process.md §Purpose and principles), and one bolded status paragraph in the template
   of process.md §Roadmap upkeep. An entry's Design line reads "none yet" until the design doc the first ideation
   session writes lands, since a link to a file that is not there fails the check. The fill comment above the status
   paragraph only describes its later upkeep: delete it.

5. **Keep or delete each extension.** [docs/process.md](starter/docs/process.md) ends with two extensions, each a
   section that opens with the sentence saying when to adopt it; keep one whole or delete it whole. *Extension —
   measurement work* has no satellite file; the seat charters' generic examples that echo its triggers stand until the
   project replaces them: two of counsel's three kinds of question, as `counsel.md`'s fill comment says (the third, an
   anchor that disagrees with the code, is core trigger 5's), and the reviewer's seeds and statistical frames.
   *Extension — plans verified in an overlay* has three satellites that go with it:
   [tools/plan_blocks.py](starter/tools/plan_blocks.py),
   [tests/tools/test_plan_blocks.py](starter/tests/tools/test_plan_blocks.py) and section 4 of
   [docs/runbooks/worktree-sessions.md](starter/docs/runbooks/worktree-sessions.md), "Applying a plan's blocks". Record
   each choice, by the extension's name, in the first row of the decision log in
   [docs/process-log.md](starter/docs/process-log.md); the fill comment in that row says how.

6. **Bind the seats.** The binding table in process.md §Model policy gives each role a default model, and says what to
   do where the environment does not offer one: rebind it at adoption, in the table and in the seat files. The seat
   files are [.claude/agents/counsel.md](starter/.claude/agents/counsel.md) and
   [reviewer.md](starter/.claude/agents/reviewer.md), whose `model` and `effort` must say what their rows say. This
   guide names no model, since the table is the one place that does; `/model` in a Claude Code session lists what the
   account offers, and a `git grep -n --untracked` for the default's model name lists its sites, among them rows that
   are not a seat's, such as the planning orchestrator's, each of which stays unless the environment lacks its model
   too. Where every default is offered, the shipped binding stands. Note a rebinding in the same first row of the
   process log.

7. **Rewrite a Conventions row where the project chooses otherwise.** process.md §Conventions gives each default, with
   an alternative beside it where it has one, and says how a row is rewritten: the choice and every site that uses it,
   which a grep finds before the edit (process.md §Canonical and pointer sites), the default it replaces moving to the
   alternative's cell. The merge method's row is the owner's choice, asked or read from the repository's settings on the
   forge. Record the deviation with its reason on the line below the table, where a fill comment asks for it, and in the
   first row of the process log. One consequence to know, set out in the layout note under the checklist: the document
   check finds designs and the dated records only where its layout constants say, so a flat `docs/`, as the alternative
   has it, gets no design checks and no pin for its dated records.

8. **Write the pack's version, then sweep the fill comments.** `{{QUOIN_VERSION}}` is the pack's tag and the commit it
   names, read from the clone you copied (`git -C ‹pack› describe --tags` and `git -C ‹pack› rev-parse --short HEAD`)
   and written as, for example, `v0.1.0 (commit 1a2b3c4)`. Write it at the four places the table names and nowhere
   else.

   `git grep -nI --untracked -e '-- fill:' -- . ':!docs/handoffs/HANDOFF-research-setup.md'` then lists the fill
   comments left, ignored files skipped: answer or delete each, wrapping an answer so that no line passes the document
   check's line limit (`line_limit_chars` in `docs/doc-budgets.json`, 400 characters as shipped). `CLAUDE.md`'s Status
   states the result the merge makes true, so it says the adoption is merged ("merged" is written in the pull request,
   since the text reaches `main` only if the pull request merges; process.md §II, stage 7), and step 10 adds the pull
   request's number and date. The setup handoff's own, which that command leaves out, wait for step 11. Two lists the
   check counts item by item each keep one bullet, which may say none yet: `CLAUDE.md`'s Load-bearing facts and the
   roadmap's Parking lot.

9. **Run the document check, last before the commit,** after every other edit:
   `python3 -I tools/doc_budgets.py init --force`, then `python3 -I tools/doc_budgets.py check`. `--force` because the
   starter ships a budgets file measured on its own stubs: `init` re-measures your files as they now stand, pins the
   dated records' dead links as they stand and runs the check once against what it wrote. `check` is the command to run
   from now on. It prints each problem as `<path>: <message>` and exits 1, or exits 0 when there is none, and before the
   first design exists it holds no design header. Fix what it names and run `check` again, not `init --force` again,
   which would accept a new dead link along with the rest. If your fills leave `process.md` over its total, which
   `init --force`'s own closing check reports like any `check`, trim them or raise the total by the contract's rule
   (process.md §Budgets): a dated row in the process log, here one clause of the adoption row, and the new
   `target_words` in the budgets file, in the same pull request; then run `check`, since `init --force` would write the
   default again. The numbers are in [docs/doc-budgets.json](starter/docs/doc-budgets.json), the rules in process.md
   §Budgets and in the tool's usage text, `python3 -I tools/doc_budgets.py --help`.

10. **Commit as the adoption pull request.** Commit everything on the branch (the subject in the commit style of step 7,
    `docs: adopt the quoin way of working` by default), push it and open the pull request, its description laid out as
    [pr-description.md](starter/docs/skeletons/pr-description.md). Once it is open, add `(PR #N, YYYY-MM-DD)`, its
    number and the day it was cut, to the `CLAUDE.md` Status line that says the adoption is merged, by one more commit
    (process.md §II, stage 7), and run `check` again after it. The owner's review is the gate (process.md §Purpose and
    principles).

11. **Instantiate the research setup handoff, once the owner has merged the adoption pull request.**
    [docs/handoffs/HANDOFF-research-setup.md](starter/docs/handoffs/HANDOFF-research-setup.md) is a template whose
    manifest names the commit it executes at: the commit the adoption's merge put on `main`, whatever the merge made of
    the branch (a merge commit, a squash or a rebase), since the branch's commits need not reach `main` and the branch
    is deleted after the merge. `git fetch origin`, then `git rev-parse origin/main` prints it while nothing else has
    merged; on GitHub, `gh pr view ‹number› --json mergeCommit -q .mergeCommit.oid` names it whatever merged since.

    Cut a branch off `origin/main` without tracking it (`git switch --no-track -c docs/setup-handoff origin/main`),
    since git's hint for a tracking branch is a push to `main`. In the manifest, replace the execution SHA's fill
    comment with that SHA in full, all 40 characters as both commands print it, and each of the five components' with
    its path (the comment names the starter's path, which stands unless step 7 moved it). Confirm
    `git merge-base --is-ancestor ‹sha› origin/main` (exit 0) and `git ls-tree -r --name-only ‹sha› -- ‹path›` for
    each path (process.md §Handoff economics, the self-containment check).

    Add the handoff's row to [docs/handoffs/README.md](starter/docs/handoffs/README.md): Handoff, a link to the file,
    `[Research setup](HANDOFF-research-setup.md)`; Window "the start of the first survey session"; Execution SHA, the
    same full SHA; Ruled or consumed by "each survey session, which runs its checks first"; Results and Status empty
    until the results pull request, as the index says (a link to a results file that is not there fails the check).
    Run `python3 -I tools/doc_budgets.py check`: it treats the handoff as a dated record, held to the pin `init` wrote,
    so a link of it that dies after `init` fails as a dead link. Commit (the subject in step 7's commit style,
    `docs: instantiate the research setup handoff` by default), push the branch by name
    (`git push -u origin docs/setup-handoff`) and open the pull request, a docs-only one after a merge, for the event
    the merge made (process.md §II, stage 7). It stamps no status site, neither `CLAUDE.md`'s
    Status nor the roadmap: the pending run shows only in the index row. Instantiating fills the manifest only: the
    first survey session runs the handoff, in a checkout at that commit (process.md §III; the handoff's
    Prerequisites).

12. **Start the first ideation session,** once the owner has merged both pull requests. The owner creates the gitignored
    `local/` (`mkdir -p local`) and copies
    [kickoff-planning-session.md](starter/docs/skeletons/kickoff-planning-session.md) from `docs/skeletons/` into it,
    then fills its `‹…›` blanks there: the item (the roadmap's first), its slug and the Launch line's model, read from
    the binding table. The skeletons stay templates and are never edited in place. The owner launches the session as the
    table says, `claude --model ‹that model› --effort max`, confirms `/effort` reads max and pastes the kickoff. It is a
    session of the planning class (process.md §I), and the kickoff drives all of it: the ideation pass that writes the
    first item's design doc, since none exists yet, then the plan, the design gate and the hard stop at the planning
    pull request (process.md §II, stages 3 and 4 and the hard stop). When the first item's methods may already be in
    the field, a survey session runs first (process.md §III, Triggers), from
    [kickoff-survey-session.md](starter/docs/skeletons/kickoff-survey-session.md) copied and filled the same way, and
    runs the setup handoff at its start.

### The placeholders

A token is two braces around an upper-case name. The set is these eight and no other; anything else a project must
supply is a fill comment.

| Placeholder | Meaning | Example |
|---|---|---|
| `{{PROJECT}}` | The repository's name. Stands in the titles of `CLAUDE.md`, `README.md`, the roadmap and the survey document, and in a sentence each of `README.md`, `docs/process.md` and `.gitignore`. Filled in step 2. | `orders-service` |
| `{{OWNER}}` | The decision-maker's name or role; "the owner" is the default (process.md §Conventions). Stands in `README.md`, in `docs/process.md`'s Purpose and in the adoption row of the process log. Filled in step 2. | `the owner` |
| `{{REPO_URL}}` | The repository's address on its forge. Stands in `README.md`'s setup section and the literature runbook's settings table, and once in code: `tools/lit.py`'s default for `LIT_REPO_URL`, the address its requests' User-Agent names. Filled in step 2. | `https://github.com/example-org/orders-service` |
| `{{PACKAGE}}` | The code's top-level package or service directory. Stands in `AGENTS.md`'s project structure. Filled in step 2; a repository with no code yet names the directory its code will have. | `orders` |
| `{{TEST_COMMAND}}` | The command that runs the fast suite, which runs the starter's `tests/` too, with pytest ([SETUP.md](SETUP.md), item 6). Stands in `README.md`, `AGENTS.md` and `docs/process.md`'s implementation session. Filled in step 2. | `pytest -q` |
| `{{LINT_COMMAND}}` | The command for lint, formatting and the other static checks. Stands in `README.md` and `AGENTS.md`. Filled in step 2. | `ruff check .` |
| `{{INTERPRETER}}` | The command that runs the repository's own Python tools, `-I` following it: the document check, the literature tool and the plan-blocks tool. Stands in `AGENTS.md`, `README.md`, the runbooks, the paper queue, the setup handoff and `docs/process.md`'s Budgets. Filled in step 2; the tools need Python 3.9 or later whatever the project's language. | `python3` |
| `{{QUOIN_VERSION}}` | The pack's tag and the commit it names. Stands in `docs/process-log.md` (the Provenance and the first row of the decision log), `docs/roadmap.md` (the standing decision) and `docs/handoffs/HANDOFF-research-setup.md` (the Provenance line). Filled in step 8, and never at a status site (the Status of CLAUDE.md, the roadmap's status paragraphs and Now and next), where a commit hash fails the document check. | `v0.1.0 (commit 1a2b3c4)` |

## Path B — an existing repository: the fusion session

A repository that already has conventions, a CI and docs does not take the starter whole. It takes mechanics, one at a
time, through a fusion session: an ideation session of the planning class (process.md §I) in the host repository, with
the pack cloned beside it. The session reads the host's conventions and [mechanics/README.md](mechanics/README.md), the
index of the mechanics, and proposes the reconciliation as a design doc in the host: which mechanics enter now and
which later, which of the host's conventions win, and the model binding and the gate tool as available there. The scope
is this repository, the service, to begin with, not the team's other repositories, and the host's process.md states it.
Then the adoption lands by pull request. [The reconciliation checklist](#the-reconciliation-checklist) names every
decision the session makes.

To open the session, clone the pack beside the host at a release tag. Launch a session in the host as the binding table
in [starter/docs/process.md](starter/docs/process.md) (§Model policy) launches the planning class,
`claude --model ‹the table's model for the ideation and planning orchestrator› --effort max`, with the owner
confirming `/effort` reads max, and paste the prompt below, filling its one blank, `‹path›`, with where the pack is
cloned.

```
This is the fusion session: an ideation session of the planning class, in this repository, the host, with the pack
cloned at ‹path›. You were launched as the pack's binding table says for that class (`starter/docs/process.md`, Model
policy, The binding table); if the work asked of you belongs to the implementation class, say so before you start.

Scope: this repository, the service, to begin with, not the team's other repositories. The host's process.md states
that in one sentence.

1. Read the host's conventions first, before the pack: the contributing guide, the CI configuration, the pull request
   templates, the code owners, the branch rules, and the existing docs with their layout. What the host has decided
   stands unless the owner says otherwise.
2. Read the pack: `mechanics/README.md`, the index of its mechanics, and `starter/docs/process.md`, the contract they
   come from; for each mechanic you take, read its page under `mechanics/` where the pack has one. Take mechanics,
   never the starter whole.
3. Propose the reconciliation as a design doc in the host, in the house shape of `starter/docs/skeletons/design.md`,
   placed where the host keeps such documents. It decides which mechanics enter now and which later; which of the
   host's conventions win where they differ from the pack's defaults; the model binding and the gate tool as available
   here; and every row of the reconciliation checklist in `ADOPTING.md`, at the pack's root: copy its table into the
   design doc and fill the host's choice for each row, with the reason. Ask the owner only what only the owner can
   answer, in one batch; every other row gets a default and a recorded ruling.
4. Land the adoption by pull request, the owner's review its gate: the design doc, the host's process.md, which carries
   the scope sentence, and the files of the mechanics that enter now, laid out as the host's conventions require.
   `CLAUDE.md`, `AGENTS.md` and the process log enter with the first mechanic, and the roadmap's first entry is the
   adoption itself unless the owner names one. Where a mechanic needs the starter's `.gitignore` entries (the ledger's
   `.superpowers/`, the owner's prompts' `/local/` and the session worktrees' `.claude/worktrees/`), append those to
   the host's file, creating it if the host has none, and never replace it. The host's own checks stay green, and its
   commit style and pull request template apply. Describe the pull request in the host's template with the sections of
   `starter/docs/skeletons/pr-description.md` inside it, listing the rulings you made in the owner's place. Once it is
   open, write its number and date where the status sites name the adoption, by one more commit
   (`starter/docs/process.md` §II, stage 7), then stop: implement nothing else.
```

## The reconciliation checklist

The fusion session decides every row. The third column is empty here: the session copies the table into the host's
design doc and writes there, for each row, the host's choice and its reason, naming the default where the host keeps it.
The defaults cite the sections of [starter/docs/process.md](starter/docs/process.md).

| Decision | The pack's default | The host's choice |
|---|---|---|
| Layout and vocabulary | `docs/designs/` and `docs/reports/`; roadmap *items*, *runbooks*, the *planning session* and the *implementation session*, *the owner* (process.md §Conventions) |  |
| Commit style | Conventional Commits, `type(scope): subject` (process.md §Conventions) |  |
| The host's quality gates as the fast suite | One fast suite and the checks AGENTS.md names, green throughout implementation and before every review (process.md §II, stages 5 and 6) |  |
| The PR review as the owner's gate | Every change lands by feature branch and a pull request the owner reviews; nothing goes to `main` directly (process.md §Purpose and principles) |  |
| The models available and the seats' binding | The binding table's defaults; a default the environment does not offer is rebound at adoption, in the table and the seat files (process.md §Model policy, The binding table) |  |
| Codex's availability | The adversarial gate runs through the Codex plugin; without it the reviewer seat in gate mode runs the round (process.md §Adversarial review protocol, The gate transitions) |  |
| Budgets on or off | On: the document check over `docs/doc-budgets.json` (process.md §Budgets; the first note below) |  |
| The id registry on or off | On: `docs/id-registry.md` maps every decision series to its document and anchors (process.md §Doc taxonomy) |  |
| The handoff threshold | About thirty minutes serial (process.md §Conventions; §Handoff economics) |  |
| Where the ledger lives | `.superpowers/sdd/<date-slug>/`, local, gitignored and never deleted (process.md §II, stage 5; §Doc taxonomy) |  |
| The host's own privacy rules for documents | No secrets in git and a key held by the owner; the host adds its own (AGENTS.md, Security & Configuration Tips; process.md §III) |  |

Two notes on the rows.

- **Budgets.** `init` needs the five files the check budgets, `CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/roadmap.md`
  and `docs/process.md`, and `check` then holds each to the starter's shape. A file that lacks a section the check
  counts fails by name: `CLAUDE.md`'s header block with its Status and Next lines, its Doc map and its Load-bearing
  facts; the roadmap's Now and next, Items, Parking lot and Standing decisions, with a status paragraph in each item. A
  host whose files will not take that shape leaves the budgets off. Run `init` without `--force`, which is for a
  budgets file that already exists. It marks every file and every design active, so a file over its budget fails
  `check` until its entry is set inactive (`active: false`, which holds it to the size `init` measured) or its number
  is raised by a dated row of the process log (process.md §Budgets). The line limit is a number of its own,
  `line_limit_chars`, which no entry silences. The links are checked too: `check` reads the host's `CLAUDE.md`, `AGENTS.md`,
  `README.md`, seat charters and every Markdown file under its `docs/` for relative links that resolve to nothing (a
  link starting with `/` counts as dead), and `init` pins only the dead links of the dated plans and handoffs, so any
  other dead link in an older host's docs fails its first `check`.
- **Layout.** The check keeps part of the layout in code, in `tools/doc_budgets.py`, and a layout choice (step 7)
  rewrites those sites with the rest: `DESIGNS` is the folder where it finds designs, the files `*-design.md` directly
  in it; `RECORD_DIRS` names the folders of the dated records, `docs/plans/` and `docs/handoffs/`; and the
  Active-obligations check names `docs/designs/` itself, in `obligations_only_in_companion_logs`. As shipped, a flat
  host's designs are not found: `init` writes no row for them, and the design-row rule, the header budget and the
  Active-obligations check do not run over them. Set to `docs`, `DESIGNS` brings the first two to them; the third stays
  off until its own path is rewritten. A flat host's plans and handoffs are not records to the check, so none is pinned
  and a link in one that dies fails `check` at once. While no design is found the tool prints "no design yet" on every
  run, as it does on a flat host left as shipped; it is information, not a problem.
