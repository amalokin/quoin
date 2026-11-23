# Changelog

One `## <version>` heading per release, newest first, each entry in the pack's own terms.

## v0.2.0

- `mechanics/`, a page for each of the sixteen mechanics the index lists, every page in one shape: **What**, one
  paragraph; **Why**, the reason the mechanic exists, with the incident that paid for it where there was one; **Files**,
  bullets that each open with a link to a path of `starter/` and say what it holds; **Depends on**, the other mechanics
  and the tools the mechanic needs, a `later` row that a `first` one needs included; **Variants**, the default first and
  then the common alternatives; and **Grafting**, the numbered steps that add the mechanic to a repository that already
  has conventions. The last step, "Entering later", says which text of the contract a repository that takes the
  mechanic after the rest keeps out until then, and gives the `git grep` that finds the other sites. A page describes
  the mechanic and cites the contract's section for its rule; it carries no date and names no model. The starter and
  the two guides change in a few places as well, which the last three bullets of this entry list for a repository that
  took v0.1.0.
- `mechanics/README.md`, the index: each row's name is now a link to its page, its opening paragraph describes the
  pages where it had said they were to come, and the description of `model-policy-and-seats` no longer repeats the
  contract's counts of session classes and seats and says that the seats are read-only subagents pinned in their own
  files. `README.md`'s map line for `mechanics/` reads "a page for each", and the fusion-session prompt in `ADOPTING.md`
  tells the session to read the page of each mechanic it takes.
- The pack's tests now hold the pages. Each of the sixteen mechanics has its page, checked from the list of the sixteen
  names and not from the pages found, so that a page that goes missing fails on its own, and so does a page that is no
  mechanic's. A page opens with its title, the mechanic's name in words, and has the six sections in order; a What of
  one paragraph of prose; Files that are bullets, each opening with a link whose text is the path from the pack's root
  and whose target is the same path from the page, to a path that exists under `starter/`, followed by what it holds;
  Variants whose first bullet is the default; and a Grafting that is a numbered list of at least two steps, the last the
  "Entering later" step. A page has no date (an ISO date, or a month with its year, wrapped or not) and no model's name;
  every link of it that names an anchor reaches a heading; it cites the contract, by a `§` or by a link with an anchor,
  and every `§` it writes names a core section of it; and the index links it. The index holds a row for each of the
  sixteen names, in order, the name as code in a link to its page, and neither the index nor a page names a mechanic as
  code without the link.
- `starter/docs/process.md`, the contract: each change is a clause or a sentence and no heading moves, so a repository
  that took v0.1.0 can carry them across one by one. The hard stop's list adds what a planning PR also carries: the
  design's Active obligations that it opens or closes, the design's series' rows in the id registry, and the roadmap
  entry's Design line linking the plan, to which stage 7 adds the report; stage 7 also says that until the PR is open
  its status sites, the plan's index row and the banners carry the lower-case placeholder `#n`, which the commit that
  writes the number fills, and that a `git grep` finds one left. The companion-log rule says who moves a closed wave's
  review records: the PR whose merge closes the wave hands the move on in Active obligations, and the next PR that
  touches the design makes it. The Counsel triggers' lead-in says that trigger 1 is the implementation session's, a
  planning session ruling on its gate's findings by stage 4 and listing its dismissals in its PR, and that the other
  triggers and the cap row's counsel clause bind both session classes; trigger 1 says which gate rounds it means, a
  re-gate after the whole-branch review or any round when the stage-6 seats cannot run, and that a round the reviewer
  seat or its stand-in runs in the tool's place is the tool's round. In the gate transitions the first row says that a
  finding left for later is dismissed for the round, its destination named, and the Judging bullet points at it; a
  scoped re-review says what it receives and what it returns; and the end of the ladder says that the session stops the
  round and flags it as the owner's, a planning session then waiting for the owner and an implementation session listing
  the round in its PR among what no seat reviewed, while the row for a stand-in that returns nothing points at it. The
  cap counts the rounds that replace the tool's, a seat's or its stand-in's; the rules for a seat call name the gate's
  package for a round in gate mode; and the wrapper test of the document check is for a host whose suite runs pytest.
- The starter's other files that change. `docs/id-registry.md`: the R row's pattern matches an item key that has a
  hyphen, a ticket's `ABC-123` as in `R-ABC-123-4`, and its note says the key is written whole; the Q row's note says
  how a later design registers its series, with the same letter in a row of its own that names the design and the
  collision written in the Collisions section. `.claude/agents/reviewer.md`: the description names gate mode beside the
  whole-branch review, the Gate mode section says that a gate round's findings are not triaged *fix before merge* or
  *can wait* and cites the gate transitions for the orchestrator's ruling on each, and the sixth item of its cover says
  that the placeholder for the PR's number is not a finding at the review. `docs/runbooks/literature-search.md` writes
  its queue marker as `[awaiting #N]` and `REQUESTS.md #N`, in capitals, so that `#n` in lower case is the placeholder
  of a PR's number alone. `tools/doc_budgets.py` and `tests/docs/test_doc_budgets.py` change in their docstrings alone,
  with no change of behaviour: the first says a new design's row in `design_headers` names its first PR in
  `target_from`, the second that the test is for a host whose suite runs pytest. The planning-session and
  implementation-session kickoffs in `docs/skeletons/` list what the contract now lists for the planning PR and for
  stage 7.
- `ADOPTING.md` and `SETUP.md`, and the pages of `mechanics/` that say the same. The reconciliation checklist says its
  second column cites the pack's files and is copied as the pack's, and its Budgets cell names the Budgets note and its
  privacy cell says that §III is where the survey is taken. Step 6 says `/model` is the owner's to type: a session that
  does the adoption asks the owner, in its one batch of questions, whether the account offers every default, and the
  shipped binding stands until the answer, the ask listed in the pull request. The fusion prompt's fourth step says that
  where the owner names the first roadmap entry the adoption is a standing decision of the roadmap, and the design's
  header says it is the adoption, with no item. Until the adoption's pull request is open, path A's Status line and the
  status sites of the fusion prompt carry the placeholder `#n` for its number. The layout note says what the
  Active-obligations path is rewritten to, lists the docstrings that name the designs folder, and says that the flat
  alternative moves designs and reports alone, so plans and handoffs keep their folders and their pin unless the host
  moves them and rewrites `RECORD_DIRS`; step 7 follows it. `SETUP.md` says the binding table writes aliases, not full
  names, that only the owner can type `/model`, and that the wrapper test, with the import setup of `tests/conftest.py`,
  serves a host whose suite runs pytest, and it cites the worktree runbook's sections by their titles, as
  `subagent-driven-development` does. `one-home-per-fact` says the wrapper test is for a pytest suite, and its Grafting
  copies the wrapper test with `tests/conftest.py`'s import setup and sets each file's root count to the host's layout;
  `working-with-the-owner` and `the-small-change-lane` say that the host's pull request template file is left as it is,
  the host's copy of the description skeleton nesting its sections inside the template's headings, and
  `model-policy-and-seats` names the owner's `/model`.

## v0.1.0

- `README.md` (what quoin is, the map and the two paths), `LICENSE` (MIT), this changelog, and `tests/test_pack.py`, the
  pack's own checks. They hold every file to UTF-8 text with no NUL byte, the placeholder set, the grammar of fill
  comments, relative links that resolve inside the pack and no address or key shape, and they check the license and the
  changelog's order.
- `starter/docs/process.md`, the contract: the purpose and principles; the ideation session, the two-session loop with
  its hard stop at the plan, the survey session and the small-change lane; the adversarial review protocol with one
  table of gate transitions; handoff economics; the doc taxonomy; canonical and pointer sites; the model policy, its
  models bound in one table beside their stand-ins, with the seats, counsel triggers 1–6, the cap and dispatch; roadmap
  upkeep; budgets; the conventions it assumes, a table of defaults with an alternative beside each default that has
  one; and two extensions an adopter keeps or deletes whole — measurement work, with counsel triggers 7–9, and plans
  verified in an overlay. The pack's tests hold its headings to the contract, its length to 10,500 words, and check
  that deleting either extension, or both, leaves no reference dangling.
- `starter/` boot files and document stubs: `CLAUDE.md` (the status, the doc map, a digest that cites the contract and
  adds nothing, the load-bearing facts), `AGENTS.md` (its seven sections of repository mechanics), `README.md`,
  `.gitignore` (the sessions' local state and the usual caches), and under `docs/` the process log, the roadmap, the id
  registry with its five house series, the indexes of plans, handoffs and explainers, and the designs directory. Each
  is complete as shipped, with its sections and its rules of upkeep, and carries placeholders and fill comments where a
  project's facts go. The pack's tests hold the eleven files present, the `.gitignore`'s entries, every bullet
  of the digest to a citation of a core section of the contract, and the status sites free of commit hashes.
- `starter/.claude/agents/`, the two seat charters, named for their roles and bound to a model in the contract's
  binding table and each file's frontmatter: `counsel` (who calls it and why, what it gets, the kinds of question to
  fill in with generic examples that stand until replaced, what it returns, its boundaries) and `reviewer` (its cover
  list, how it works, the shape of its report and its gate mode). Each file's frontmatter pins the model and effort its
  row of the table names and removes the file-writing tools. The pack's tests hold a model, an id or an alias, to the
  binding table, the seat files' frontmatter and the table of what degrades in `SETUP.md`, each seat file to its row of
  the table, and the reviewer charter to the section names the contract cites.
- `starter/tools/codex_gate.sh`, the adversarial gate's launcher, and `starter/docs/runbooks/codex-gate.md` and
  `worktree-sessions.md`, its two operating guides. The launcher is a bash script run directly, never under the
  interpreter of the Python tools: it reads the focus text from a file, refuses a focus text with a dash-led token that
  the companion would read as a flag, and finds the codex plugin through `CODEX_PLUGIN` or the newest installed version.
  `codex-gate.md` covers the invocation, the focus text, dead rounds and the usage window, and recording a round, and
  cites the contract's table of gate transitions instead of copying it. `worktree-sessions.md` covers entering a
  worktree; the environment as one rule — a worktree's checks run its own source — with the conditions for reusing the
  main checkout's environment and a Python worked example; working within the harness's limits; applying a plan's
  blocks, for the plan-overlay extension; checking a subagent's report; finishing a PR; and cleaning up. The contract
  and the boot files link to them. The pack's tests run the launcher against a fake `node` (its two refusals, and
  its happy path from a stub plugin: it moves to the repository root and hands the companion its options and the focus
  text as separate arguments, so that a checkout path with a space stays one), hold its executable bit, and check that
  `codex-gate.md` cites the transition table and that neither runbook copies it.
- The research stack. `starter/tools/lit.py`, the literature tool (standard library only): search OpenAlex, Semantic
  Scholar and arXiv, follow references and citations, file open-access PDFs and queue closed ones, check the papers
  index, report the OpenAlex budget, and `check`, the readiness report — the key file's path, mode and owner, where
  each key comes from, one cheap call per configured source, never a value, and the setup step to resume at. Its
  settings are `LIT_*` variables with defaults (the project name is the repository's directory name, the main working
  tree's from any of its worktrees), and an empty one is a usage error. `starter/tests/test_lit.py` serves
  the tool recorded responses in place of the network (`tests/fixtures/lit/`; their capture and the few edits made to
  them are in `tests/fixtures/README.md`). Around it: `docs/runbooks/literature-search.md` (operating the tool, the
  sweep, the verification pass, and what carries over to work outside academia), `docs/reports/literature-review.md`
  (the standing survey, its six sections shipped with their upkeep rules), `docs/papers/REQUESTS.md` (the queue of
  paywalled papers) and `docs/handoffs/HANDOFF-research-setup.md` (the setup, a template the adoption instantiates).
  The contract and the boot files link to them. The pack's tests hold the one placeholder in code to the tool's
  repository-URL default, the survey to its sections and its index to §6, the queue's table to the end of its file,
  and the setup handoff to the five sections with its manifest's fill cells.
- `starter/tools/doc_budgets.py`, the document check (standard library only). `check` holds the boot files and the
  design headers to `docs/doc-budgets.json` — the growing lists capped item by item, the rests and the other files to
  their totals, the boot path's total as an alarm, CLAUDE.md's H1 block, the roadmap's status paragraphs, the line
  limit — and checks that no commit hash stands at a status site, that no id a design's Active obligations cite lives
  only in its companion log, that every design has its row and every row its design, and that every relative link
  resolves, the dated plans' and handoffs' dead links held to a pin; each problem is printed as `<path>: <message>`,
  and the exit status is 0, 1, or 2 for a missing or malformed budgets file. Before the first design, no design header
  is required. `init` writes the budgets file for a fresh repository, its baselines measured as the files stand, then
  runs the check. `starter/docs/doc-budgets.json` is the starter's own, as `init` writes it, so an adopter re-measures
  it with `init --force`; the starter's tests pin the counting rules and the checks over fixtures and run both
  commands over temporary repositories, and `tests/docs/test_doc_budgets.py` runs the check as one test for a Python
  host. The pack's tests run the check over the starter and count process.md's words with the check's own counter.
- `starter/tools/plan_blocks.py`, the tool of the plan-overlay extension (standard library only). A plan carries its
  code as file blocks under its task headings, each a whole file or a unified diff against `main`. The tool lists them;
  extracts a task's blocks; checks the working tree against them, a diff applied to the base's blob with `patch -p1 -l`;
  tries every diff against a base; regenerates every block from an overlay copy; and verifies in a scratch copy that the
  blocks rebuild the overlay byte for byte. `verify` refuses, before it deletes anything, a scratch directory that
  overlaps either input, and every command refuses a block path outside the tree. `imports` lists the repository imports
  that no tree file and no block of the same or an earlier task provides, and checks the names of a package's `from`
  imports: the repository's packages are read from the working directory and the plan's own paths, a directory
  without an `__init__.py` is read as a namespace package, as the starter's own `tools/` is, and each part of a dotted
  import is resolved as Python resolves it — a package, then a module file, then a namespace directory — so an import
  through a module file is reported.
  `starter/tests/tools/test_plan_blocks.py` runs the tool over temporary repositories — regenerate and verify, check,
  applies and extract, the refusals — and pins the import check's package set, its namespace reading and that order.
  The contract's extension and the worktree runbook's section on applying a plan's blocks link to the tool.
- `starter/docs/skeletons/`, the fourteen templates: for the design doc, the plan, the handoff and its results, the
  report, the explainer, the pull request description, the gate's focus text and the packages handed to the two seats,
  each a document's house shape as a title and headings with one line of guidance under each and no content, and the
  four session kickoff prompts (a planning session, an implementation session, the pickup of a handoff's results and a
  survey session) that the owner copies into a gitignored `local/`. A kickoff opens with a launch line that leaves the
  model to the contract's binding table, and each of its sections is one instruction that cites the contract by section.
  A skeleton links nothing and holds no fill comment, and the handoff's headings are the contract's five. The contract,
  the starter's README and the gate runbook link to them. The pack's tests hold the fourteen names, one line of
  guidance under every heading, the handoff's five headings, every citation to a core section of the contract, no link
  or fill comment in a skeleton, the kickoffs' launch lines and, by running the launcher itself, no dash-led token in
  the gate-focus skeleton.
- `ADOPTING.md`, the guide to the two paths. Path A is twelve numbered steps from copying `starter/` to the first
  ideation session: fill the placeholders; write `AGENTS.md`'s layout and commands and the roadmap's first items with
  their anchors; keep or delete each extension with its satellite files; bind the seats; rewrite a Conventions row
  where the project chooses otherwise; write the pack's version and sweep the fill comments left; run the document check
  last (`init --force`, then `check`); commit as the adoption pull request; instantiate the research setup handoff by a
  second pull request once the first has merged, pinned to the commit the merge put on `main`; and start the
  planning-class session from a kickoff copied into the gitignored `local/`. Its placeholder table has a row for each of
  the eight tokens, saying where the token stands and when it is filled. Path B is the fusion session: its kickoff
  prompt, in one block to paste into a session in the existing repository with the pack cloned beside it. The
  reconciliation checklist is a table of the eleven decisions the session makes, each with the pack's default and the
  host's choice left empty, with two notes for a host on what the document check counts, links included, and on where it
  finds designs, plans and handoffs. The setup handoff template says how that pin is run, in a worktree detached at the
  manifest's commit, and the survey kickoff has the session run it in a checkout at that commit, as the template's
  Prerequisites say. The pack's tests hold the guide's three sections, the prompt's single block and what it names, the
  checklist's header and its eleven rows, the placeholder table to a row for each token, and the version token's row to
  the files where the token stands. `README.md` links the guide.
- `SETUP.md`, the environment the pack assumes, in eleven pieces: Claude Code; the Superpowers and Codex plugins, with
  the install commands as `claude plugin` prints them; the Codex CLI logged in, and Node.js for the gate launcher; `gh`
  authenticated; git with worktrees; Python 3.9 or later, with how to find the system interpreter, what a host whose
  suite is not Python does with the document check, and that the starter's own tests are pytest tests; `uv` for the
  arXiv server; the effort pin at launch; the dispatch rule, as the entry for the `autoMode.soft_deny` list of the user
  settings; optional notification hooks; and how to list the models an account offers. Each piece says what the pack
  uses it for, citing the contract or the runbook, and how to check it is there. A closing table says what degrades
  without each piece and which rule governs the change, and is the one place in the guide that names a model.
  `mechanics/README.md`, the index of the sixteen mechanics path B picks from: one line each, citing the contract's
  section that holds the mechanic, and a column saying whether a fusion session usually takes it first, later or only
  for measurement work; the pages themselves come in a later release. `README.md` and `ADOPTING.md` link both. The
  pack's tests hold the table to its heading and at least four rows, with a row each for the Codex plugin, Superpowers
  and `uv`, and a model it names to one the binding table binds; every section the guide cites to a core section of the
  contract; the model-id check to the table's rows as a site that must name a model; and the index to its sixteen names
  in order, each description citing a core section of the contract and the third column one of its three values.
- `tests/fixtures/host/`, the example host that path B is rehearsed on: a small service whose conventions differ from
  the starter's defaults on purpose. Its `docs/` is flat, with decision records under `docs/adr/` and a
  `docs/runbook.md` that means operating the service (start, stop, health check, rollback). Its commit subjects are
  `SVC-<n>: <subject>` and its merges are squash merges, as `CONTRIBUTING.md` sets down beside a pull request
  template; a `CODEOWNERS` file names the reviewing team; and its CI runs `make check`, the host's fast suite: one unit
  test of the handler `svc.app.handle`, run by `unittest discover` over a `src/` layout, with the `tests/__init__.py`
  that Python 3.9's discovery needs. The host knows nothing of the pack. The pack's collection skips it, since it has a
  suite of its own; the pack's tests run its `make check` with bytecode writing off, so that the run leaves nothing
  behind, and hold its twelve files, each with the convention it carries.
