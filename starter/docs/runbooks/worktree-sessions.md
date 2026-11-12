# Runbook — a session in a git worktree

*The rule is [process.md](../process.md) §II, Checkouts. How a session enters a worktree of the shared checkout, runs
the suite there, finishes a PR and cleans up — with the harness's refusals inside a worktree-isolated session and the
routes round them.*

## 1. Entering

The main checkout is shared by concurrent sessions, and a checkout or reset made in one of them can wipe another
session's uncommitted work; the rule that follows is [process.md](../process.md) §II, Checkouts. To enter:
`git fetch origin`, then `EnterWorktree` (the harness's tool), which creates `.claude/worktrees/<name>` on a branch
named `worktree-<name>`; rename it at once to the branch name Checkouts gives (`git branch -m <branch>`), then check
its base. `git merge-base --is-ancestor origin/main HEAD` must succeed — the tool may branch from the shared checkout's
`HEAD`, which a fetch does not move — and when it fails, run `git merge --ff-only origin/main` in the new worktree
before any work. Without the tool, `git worktree add --no-track -b <branch> <path> origin/main` from the main checkout,
when no peer session is in it (`ListAgents`, `lsof -d cwd`): `--no-track`, since git's hint for a branch that tracks
`origin/main` is a push to `main`. Inspect the shared checkout only after leaving the worktree.

## 2. The environment

A worktree has no environment of its own. The rule is [process.md](../process.md) §II, Checkouts: a worktree's checks
run its own source, with dependencies and built artefacts compatible with that revision. Two cases meet it.

**Reuse the main checkout's environment** only when both of these hold:

- the dependency manifests and lockfiles are identical between the worktree and the revision that environment was
  built from, so that `git diff <that revision> -- <the lockfiles>` prints nothing; and
- no built artefact the checks import (a compiled module, a generated file, a bundle) has changed since that revision,
  so that `git diff <that revision> -- <the artefact's sources>` prints nothing, or the artefact is rebuilt in the
  worktree.

**Otherwise the worktree gets an isolated environment of its own,** installed from its own manifests and lockfiles. An
install into the main checkout's environment is the owner's (Checkouts), and is never made while a live process runs
from it.

The revision is the one recorded when the owner installed the environment; a revision that nobody recorded cannot be
diffed against, so the worktree gets an environment of its own. A host with no manifest, lockfile or built artefact has
nothing to diff and no revision to record: its worktrees reuse the main checkout's environment by absolute path.

<!-- fill: where this host records the revision its main checkout's environment was built from, and the sources of each built artefact the checks import; the rule is one line each, updated by whoever installs or rebuilds -->

**A worked example, Python.** Reuse runs the main checkout's interpreter by absolute path from the worktree root, in
module mode, with bytecode writing off so that the run leaves nothing in the main checkout's environment:

```
env PYTHONDONTWRITEBYTECODE=1 <main checkout>/.venv/bin/python -m pytest -q -p no:cacheprovider
env PYTHONDONTWRITEBYTECODE=1 <main checkout>/.venv/bin/python -m mypy <packages>
```

Module mode matters: `python -m` puts the working directory first on `sys.path`, so the worktree's packages are the
ones imported, where a bare console script (`pytest`) would import the package from the main checkout through its
editable install. A scratch script run by path puts its own directory first instead: run it with `PYTHONPATH=.` from
the worktree root.

Isolation needs one more step. A shell that has the main checkout's virtual environment active exports `VIRTUAL_ENV`
(and `VIRTUAL_ENV_PROMPT`), and a package manager's `run` wrapper resolves through it to the main checkout's
environment. So build the worktree's own environment with the inherited variables removed:

```
env -u VIRTUAL_ENV -u VIRTUAL_ENV_PROMPT <the host's install command>
```

Then run the worktree's `.venv/bin/python` by explicit path; an `unset` in one command does not carry to the next, and
the wrapper is never used from a worktree.

Gitignored data (a dataset, a generated build) exists in the main checkout only; a check that reads it takes
its location, by absolute path in the main checkout, from a variable or an argument. The host's own commands — the
interpreter's path, the lockfiles, the data's location — are written in [AGENTS.md](../../AGENTS.md) and in the host
paragraph of Checkouts. A hook runner that lints tracked or staged files only (pre-commit does) cannot see a new file:
`git add` it before running the hooks.

## 3. The harness inside a worktree-isolated session

The harness refuses a Bash command it cannot prove stays in the worktree: shell loops, a variable or a computed value
where an option may stand (`sed -n "$(grep …)"`), heredocs inside a compound command, long `&&` chains that `cd`
elsewhere, `git -C <the shared checkout>`, and strings that look like git operations (URLs with "github", `find` with
`$HOME`). Keep one plain command per call with absolute paths, put loops and heredocs in scratchpad scripts and run
them by path (`bash /path/script.sh`), and do the fetching (`git fetch origin`, any source to be read) before entering
the worktree. Parallel Bash calls share one shell cwd, so a `cd` in one call breaks the others: absolute paths always.
The Write and Edit tools refuse every path outside the worktree and the scratchpad: a file for the owner's `local/` or
the shared checkout's `.superpowers/sdd/` is written to the scratchpad and copied with `cp` (the two copies Checkouts
lists). The Write tool decodes a lone `\uXXXX` escape in its content, and a heredoc sent through the Bash tool was
decoded too: build such text without the literal escape (`chr(92)` for the backslash, or `\N{NAME}` for the character,
in a Python script), and grep the file afterwards.

## 4. Applying a plan's blocks

This section serves the plan-overlay extension of [process.md](../process.md); where that extension is not adopted,
delete this section.

`{{INTERPRETER}} -I tools/plan_blocks.py list PLAN` names every file block by task; `extract PLAN TASK OUTDIR` writes a
task's blocks (a diff gets a `.diff` suffix); `check PLAN TASK main` byte-compares the tree with them, applying a diff
to main's blob with `patch -p1 -l` (a whitespace hook strips the diff's blank context lines, which `-l` ignores). A
block that is a diff is against `main`, so when an earlier task already changed the file, apply the diff to main's
blob (`git show main:path`): the result is both changes. An implementer extracts a task's blocks and copies or patches
them in; the orchestrator runs `check` on every DONE report (the extension's rule). The tool's other verbs are described
in [its usage text](../../tools/plan_blocks.py); what they prove, and what a block that does not apply means, are the
extension's own text in process.md.

## 5. Checking a DONE report

A subagent's report is a claim ([process.md](../process.md) §II, stage 5): run `git status` on every DONE (an
implementer can report DONE with the work staged but uncommitted) and re-run the named tests and the anchors. Never
commit from the orchestrator while an implementer has unstaged work in the same worktree: a pre-commit framework
stashes and restores unstaged files around a commit, which pulls *their* files out from under them. A re-review that
must execute commands needs a model that does, and the dispatch says to run them: the least capable models may check
only that a recipe's imports resolve. Which model carries a role is [process.md](../process.md) §Model policy,
Dispatch. Some subagent types decline to write report files: ask for the report in the final message and save it from
the transcript (the hand-back is the `message` field of the subagent's `SubagentHandback` tool use in its JSONL).

## 6. Finishing a PR from another session

A PR is merged after the owner's review ([process.md](../process.md) §Purpose and principles). To merge one another
session built: `gh pr merge N --merge --match-head-commit <sha>` makes the merge exactly the tested tip, and
`git rev-parse <merge>^{tree}` equal to the tip's tree proves it without re-running the suite. The builder's worktree
stays locked while its session lives: `.git/worktrees/<name>/locked` names the pid; if `ps -p` shows it alive, ask the
owner before `git worktree unlock` and `remove`. Late results onto an open PR from a new session: a new worktree from
`origin/<pr-branch>`, the builder's SDD ledger copied and continued, the push a fast-forward
(`git merge-base --is-ancestor`), a results PR brought in with `git merge --no-ff`.

## 7. Cleaning up after the merge

The steps are [process.md](../process.md) §II, stage 8; this is the detail under a worktree-isolated harness. Confirm
the tip is on `origin/main` (`git branch -r --contains <tip>`) and copy the SDD workspace into the main checkout's
`.superpowers/sdd/` (a plain `cp -R` runs where `git -C` is refused). Checkouts allows no hand move of other
gitignored data into the main checkout (the host's commands that produce such data write it there by absolute path
themselves), so a worktree that holds some, listed by `git status --short --ignored`, is named to the owner and kept
until the owner has answered: removing it would discard the only copy. Then `ExitWorktree` with `discard_changes` (it
compares against the local original branch and refuses otherwise).

From the main checkout: `git branch -D <branch>` (`-d` refuses while local `main` is behind; use `-D` after
`git merge-base --is-ancestor <tip> origin/main`), `git push origin --delete <branch>` (unless the forge deletes merged
branches itself), and `git merge --ff-only origin/main` under the conditions Checkouts gives.

Under a squash or a rebase merge ([process.md](../process.md) §Conventions) the tip never reaches `origin/main`: both
checks above, `git branch -r --contains <tip>` and `--is-ancestor`, give way to the PR's merged state,
`gh pr view ‹number› --json state -q .state` reading `MERGED`.
