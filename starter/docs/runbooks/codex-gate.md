# Runbook — the codex adversarial-review gate

*The rule is [process.md](../process.md) §Adversarial review protocol. How a session runs the codex gates — the design
gate at stage 4, the final gate at stage 6, the document-review variant — through the plugin runtime from Bash, and
what running them teaches about focus texts, dead rounds and usage windows. The durations and quotas it names are
typical observations, not limits.*

## 1. The invocation

```
git fetch origin                                     # first, every time
tools/codex_gate.sh FOCUS_FILE --base origin/main    # the usual base; Scopes names the base of each gate
tools/codex_gate.sh FOCUS_FILE --base <sha>          # a re-gate: the base the gate transitions give
```

The launcher is a bash script: run it directly, as above, never under the interpreter of the repository's Python
tools. Which base each gate takes, why a worktree always passes one and what a gate reads (committed history only) are
the protocol's ([process.md](../process.md) §Adversarial review protocol, Scopes; §II, Checkouts). Two details it
leaves out: a run with no flag on a clean tree compares against the local `main`, as `--scope branch` does (the plugin
strips `origin/` from `origin/HEAD`), and a worktree cannot move that branch while the shared checkout holds it.

The launcher resolves the plugin's versioned path at run time: `$CODEX_PLUGIN` when set, else the newest
`~/.claude/plugins/cache/openai-codex/codex/*/`. Its usage also names `--cwd DIR`, the companion's own option, passed
through to review DIR instead, which a session running its own checkout's launcher never needs.

Run the launcher in the harness's background mode and wait on the job as the protocol says (Waiting on a job). The
companion blocks the foreground until the job registers (over two minutes on a large branch) and `--background` still
tails the job, so the verdict block is at the end of the launch output. The companion's `result` command prints the
latest job's result and `status --all` lists the jobs; both are run as
`node <plugin>/scripts/codex-companion.mjs <command>`.

The focus text lives in a file (the scratchpad is fine) because a worktree-isolated session's harness refuses long
inline commands ([worktree-sessions.md](worktree-sessions.md) §3 lists what it refuses). The file carries no dash-led
token (the protocol's The gate package): the companion tokenizes arguments it gets as one quoted string, as the
plugin's slash command passes them, and a test command quoted in the text, `python -m pytest`, once became the model
flag ("The 'pytest' model is not supported"); write "as the pytest module, in module mode" instead. A dash-led token is
a hyphen followed by a letter (quotes, backslashes or more hyphens may sit between), at a line start or after
whitespace, a quote or a backslash; a hyphenated word, a list bullet and an em dash are not one. The launcher refuses
such a file, though it passes the options and the focus text as separate arguments, the text after `--`, so that a path
with a space stays whole.

## 2. The focus text

What the focus text carries is the protocol's ([process.md](../process.md) §Adversarial review protocol, The gate
package; the skeleton is [docs/skeletons/gate-focus.md](../skeletons/gate-focus.md)). Beyond the mandatory reads and the
questions, ask for the findings in priority order and end with "END WITH A VERDICT; run the tests at most once". A
design gate on a plan that embeds code gets a code review: the companion loads the plan's code blocks into an in-memory
copy and runs read-only probes, so the plan's tests must cover its claims literally, the plan must state the behaviour
as the code does it, and the task order must match the imports.

On a **re-gate**, add "do not reopen confirmed areas unless the fix broke them" to what the package already carries
(the protocol's The gate package): a focused round takes a few minutes where a first round on a large branch takes
about twenty minutes. A fix that adds an assumption (a date, a default, a lookahead) gets probed the next round; state
the invariant and make the input required instead. A fix that makes something happen "at once" must list the readers
of the changed state and refresh each.

The **document-review variant** opens with "Document review, not a code diff: read … at <absolute path>" and a
numbered review charter (correctness of named claims first, then skipped steps, then structure); it works for a
document on `main` or committed on the branch, named by its absolute path in the worktree.

The codex sandbox runs no tests ("execution outside the sandbox" required): run the covered tests yourself and record
it in the log row. A check the gate greps for that has documented exceptions needs them named in the focus text, or
the gate reports them as false hits.

## 3. Rounds, dead rounds and the usage window

Codex usage is metered in a window of some hours, and a handful of full reviews of a large branch can exhaust it; a
round can die during its run ("You've hit your usage limit … try again at HH:MM") or on "model at capacity"
("Selected model is at capacity"), usually at launch, before it has captured anything. A dead round is not a verdict.
Whether it counts and what runs in its place are [the gate transitions](../process.md#the-gate-transitions); what this
runbook adds is the harvest. The launch log still holds every `[codex] Assistant message captured: …` line and the
reasoning summaries: read them all, judge each as a finding, verify the hinted ones yourself, and record in the round's
row that the round was cut short.

When the window is shared (another session is waiting on codex), give the round a scoped, budgeted focus — the code
diff first, long reports by line range, a cap on how many files or functions the round may open, the hygiene checks
run locally — and say so in the package and in the round's row, since the gate then skips what the whole-branch review
reads in full.

Size the rounds to the work. A final gate can run beside the last task's review, since a gate job is a background job
and not a subagent ([process.md](../process.md) §Model policy, Dispatch). When two rounds in a row find lifecycle
corners in a mechanism described in prose, simplify the mechanism rather than patch the case.

## 4. Recording a round

Every round is a dated row in the design's decision log (or its companion log once the wave is closed): the scope, the
verdict and each finding's severity. How each finding is judged and logged, and that the review is advisory input and
never an auto-apply, are the protocol's ([process.md](../process.md) §Adversarial review protocol, Judging); what
follows the round — whether a fix wave earns another round, what counts toward the cap, what replaces a round that
died — is [the gate transitions](../process.md#the-gate-transitions). The launcher's job id goes to the owner when a
session reports.
