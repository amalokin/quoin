# Repository Guidelines

> Repository mechanics only: layout, commands, style, test conventions, commits and PRs. What a module decides and
> why is its design doc's, what it measured is its report's, and how work happens is
> [docs/process.md](docs/process.md) (the digest: [CLAUDE.md](CLAUDE.md)). The adversarial gate reads this file with
> every diff, so keep it factual and current.

## Project Structure & Module Organization

- `{{PACKAGE}}/` — the code's top-level package or service. One line per module, each naming the design doc that
  decides it.
- `tests/` — the test suites, mirroring the layout of `{{PACKAGE}}/`; fixtures sit under `tests/fixtures/<topic>/`, one
  directory per topic, as `lit/` does.
- `tools/` — the repository's own tooling, never imported by runtime code: the literature tool, the gate launcher
  and the document check.
- `docs/` — the process, the roadmap, the designs, the reports, the plans, the runbooks, the handoffs, the
  explainers, the id registry and the budgets ([docs/doc-budgets.json](docs/doc-budgets.json)); the taxonomy is
  [docs/process.md](docs/process.md) §Doc taxonomy.
- [.claude/agents/](.claude/agents/) — the two seat definitions an implementation session dispatches (`counsel`,
  `reviewer`), model and effort pinned in their frontmatter ([docs/process.md](docs/process.md) §Model policy).
- `README.md` — setup and the quick-start commands; `CLAUDE.md` — the digest every session loads first.

<!-- fill: this project's layout, one line per directory and module with the design doc that decides it, what never imports what, and the build manifest, lockfile and tool configuration at the root; the rule is one line per module -->

## Build, Test, and Development Commands

- The fast suite: `{{TEST_COMMAND}}`. Who runs it, and when, is [docs/process.md](docs/process.md) §II, stage 5.
- Lint, format and the other static checks: `{{LINT_COMMAND}}`.
- The document check: `{{INTERPRETER}} -I tools/doc_budgets.py check` holds the boot files and the design headers to
  [docs/doc-budgets.json](docs/doc-budgets.json), and checks every relative link and the status sites
  ([docs/process.md](docs/process.md) §Budgets); `init` writes the baselines for a fresh repository.
- The Python tools run as `{{INTERPRETER}} -I <tool>`: the document check above and [tools/lit.py](tools/lit.py), the
  literature tool (its procedure is [docs/runbooks/literature-search.md](docs/runbooks/literature-search.md)).
- The gate's launcher, [tools/codex_gate.sh](tools/codex_gate.sh), is a bash script run directly, not under
  `{{INTERPRETER}}`. Its usage and the base to pass are in [docs/process.md](docs/process.md) §Adversarial review
  protocol (Two entry points; Scopes); its recipe and gotchas are
  [docs/runbooks/codex-gate.md](docs/runbooks/codex-gate.md).
- In a git worktree every check runs the worktree's own source; the rule is [docs/process.md](docs/process.md) §II,
  Checkouts, and the environment recipe is
  [docs/runbooks/worktree-sessions.md](docs/runbooks/worktree-sessions.md).

<!-- fill: this project's install, build and run commands, one line each with its flags and what it prints, the toolchain version, and the one-time setup that is the owner's and never a session's; the rule is a command per line -->

## Coding Style & Naming Conventions

- Files are UTF-8 with no trailing whitespace; `{{LINT_COMMAND}}` enforces the rest of the style, with no hand-formatted
  exceptions.
- Keep modules free of side effects at import or load time; put demonstrations behind functions.

<!-- fill: the language and its version, the formatter and linter with their settings, the naming scheme per kind of name, the annotation policy and the layering rule, which package never imports which; the rule is one line each -->

## Testing Guidelines

- Write the failing test first ([docs/process.md](docs/process.md) §II, stage 5); tests live under `tests/`, mirroring
  the package path.
- Cover validation rules and invariants; add regression tests with descriptive names; prefer small, isolated units
  over integration. A coverage claim needs a mutation check ([docs/process.md](docs/process.md) §Purpose and
  principles).
- A pinned value that moves while its file's other assertions hold is a format change: stop and report it (counsel
  trigger 5, [docs/process.md](docs/process.md) §Model policy), do not re-pin it.
- The document check (under Build, Test, and Development Commands) also runs as a test,
  [tests/docs/test_doc_budgets.py](tests/docs/test_doc_budgets.py), which wraps it; run it before every commit
  that touches a document.
- A skip says why it skips. On the owner's machine none may skip: read the runner's skip report for the unexpected
  ones.

<!-- fill: the test framework and layout, the fast suite and what it skips, any slow gate and when it is required, and the project's differential or property-test pattern; the rule is one line each -->

## Commit & Pull Request Guidelines

- Commit subjects follow the format in [docs/process.md](docs/process.md) §Conventions.
- Branch names, and where a branch is cut from, are in [docs/process.md](docs/process.md) §II, Checkouts.
- Commits and pushes belong to the loop: each task commits, since the gates read committed history only
  ([docs/process.md](docs/process.md) §Adversarial review protocol, Scopes); a branch is pushed when a handoff or a
  cross-machine step needs its commit on `origin` ([docs/process.md](docs/process.md) §Handoff economics); nothing is
  ever pushed to `main`. Outside the loop, open a PR, commit or push only at the owner's ask.
- A PR is cut and described as [docs/process.md](docs/process.md) §II, stage 7 says. The checks (`{{LINT_COMMAND}}`,
  `{{TEST_COMMAND}}`) pass before review is requested.

<!-- fill: the commit scopes this project uses and any rule the host adds, such as a ticket reference or a sign-off; the rule is that process.md holds the format and this file only what is the project's own -->

## Agent-Specific Instructions

- Work in a git worktree off `origin/main` and leave the main checkout alone but for the writes it lists: the rule is
  [docs/process.md](docs/process.md) §II, Checkouts, and the recipe is
  [docs/runbooks/worktree-sessions.md](docs/runbooks/worktree-sessions.md).
- The evidence rules, how a web source is quoted and what a number must carry, are
  [docs/process.md](docs/process.md) §Purpose and principles.
- Start with your session class and its reads ([docs/process.md](docs/process.md) §Model policy; §II, stage 1).

<!-- fill: this host's constraints on agents, such as whether the checks must run outside a sandbox, the paths a running process owns that no session may touch, the commands to avoid, and the runbook that governs each; the rule is one line each -->

## Security & Configuration Tips

- No secrets in git: keys and tokens live in the environment or in a gitignored file outside the repository, never in
  a tracked file, a test, a fixture or a document. A key is created and held by the owner, never by a session
  ([docs/process.md](docs/process.md) §III).
- Do not commit large binaries, generated data or virtual environments; commit their hashes and manifests, and rely
  on `.gitignore`.

<!-- fill: where this project's secrets and configuration live, what is gitignored and why, and anything private that must never enter a tracked file; the rule is one line each -->
