# quoin

quoin is a starting pack for working with coding agents in Claude Code sessions. It carries a way of working proven
in daily use: the roadmap as the spec, a two-session loop with a hard stop at the plan, subagent-driven development,
a model policy with two seats and counsel triggers, adversarial review gates run through Codex, handoffs for long
work, one home per fact, and a survey session with its literature tool. It comes in two forms: a drop-in tree that a
fresh repository copies whole, and a menu of mechanics that an existing repository adopts one at a time.

## The map

```
quoin/
├── README.md                 this file
├── LICENSE                   MIT
├── SETUP.md                  the environment: Claude Code, the plugins, the tools, and what degrades without each
├── ADOPTING.md               path A, path B, the fusion-session prompt and the reconciliation checklist
├── CHANGELOG.md              one entry per release
├── mechanics/                README.md, the index of the sixteen mechanics path B picks from; the pages are to come
├── starter/                  the drop-in tree path A copies whole
│   ├── CLAUDE.md  AGENTS.md  README.md  .gitignore
│   ├── .claude/agents/counsel.md  reviewer.md
│   ├── docs/
│   │   ├── process.md  process-log.md  roadmap.md  id-registry.md  doc-budgets.json
│   │   ├── designs/  reports/literature-review.md  explainers/00-index.md
│   │   ├── plans/README.md  handoffs/README.md  handoffs/HANDOFF-research-setup.md
│   │   ├── runbooks/codex-gate.md  worktree-sessions.md  literature-search.md
│   │   ├── papers/REQUESTS.md
│   │   └── skeletons/        fourteen files
│   ├── tools/lit.py  codex_gate.sh  doc_budgets.py  plan_blocks.py
│   └── tests/
│       ├── conftest.py  test_lit.py  fixtures/lit/
│       ├── docs/test_doc_budgets.py
│       └── tools/test_doc_budgets_functions.py  test_plan_blocks.py
└── tests/test_pack.py  fixtures/host/    the pack's own checks; the example host repository for path B
```

## Path A — a fresh repository

Copy `starter/` to the root of the new repository, fill the placeholders, and write `AGENTS.md`'s layout and
commands. Write the roadmap's first items, each with its anchor, the check that shows it done. Keep or delete the two
optional extensions, bind the seats to the models you have, and run the document check: `init --force`, then `check`
(`--force` because the budgets file the starter ships was measured on its own stubs, and `init` re-measures your
files). Commit the result as the adoption pull request; once it has merged, instantiate the research setup handoff by a
second, small pull request, and start the first ideation session. [ADOPTING.md](ADOPTING.md) has the numbered steps and
the placeholder table; [SETUP.md](SETUP.md) has the environment they assume.

## Path B — an existing repository

Open a planning session in the repository with this pack cloned beside it, and paste the kickoff prompt from
[ADOPTING.md](ADOPTING.md). That session, the fusion session, reads the repository's own conventions and
[mechanics/README.md](mechanics/README.md), then proposes the reconciliation as a design document in the repository.
It says which mechanics enter now and which later, which of the repository's conventions win, and the scope, which
begins as that one repository. The adoption then lands by pull request. [ADOPTING.md](ADOPTING.md) also holds the
reconciliation checklist; [SETUP.md](SETUP.md) has the environment.

## License

MIT; see [LICENSE](LICENSE). What each release carries is listed in [CHANGELOG.md](CHANGELOG.md).
