# Handoff — the research setup

*The setup of the literature tool, [tools/lit.py](../../tools/lit.py), and of the optional MCP servers a survey session
reads with: a template instantiated at adoption, by the adoption's second pull request, which pins the component
manifest to the commit the first one's merge put on `main` and gives the handoff its row in [the index](README.md).
It is standing: every new machine runs it again (What happens after). The rules it runs under are
[process.md](../process.md) §III's; its five sections are the contract of §Handoff economics.*

## Prerequisites

A word in ‹…› stands for a value: the executor's to write in or, in the tool's output, what the tool printed.
‹the main checkout› is the first path `git worktree list` prints, ‹the execution SHA› is the manifest's, ‹the worktree›
is `‹the main checkout›/.claude/worktrees/research-setup`, and ‹key file› is the path step 0's first line names
(`LIT_ENV`, by default `~/.config/‹project›/lit.env`, ‹project› being the main checkout's directory name, as the
runbook's settings table derives it).

- **The executor:** the survey session that first needs the tool, guiding the owner through every key-holding step,
  or the owner alone, in a terminal. This guide is of the implementation class, to which process.md §Model policy
  gives this handoff's execution, the exception to the monitor of §Handoff economics; a dry read at a cheaper class is
  the stricter reading. Every later survey session runs the checks again at its start. The branch and the pull request
  are the session's own, as its kickoff says.
- **Two checkouts.** This file is followed as `main` holds it, instantiated; a session reads it in its own worktree.
  Its copy at the execution SHA is the file as it stood before the pull request that wrote that SHA (at the first pin,
  the template before instantiation), listed in the manifest so that the self-containment check holds, not the text to
  follow. The commands act on a worktree detached at the execution SHA, since a session's own worktree sits at
  `origin/main`'s tip; the tool names the project after the main working tree, so from that worktree it finds the key
  file any other checkout would ([the runbook's settings table](../runbooks/literature-search.md#1-the-stack)).
- **Python 3.9 or later,** the tool being standard-library only: `{{INTERPRETER}} --version` prints the version, and
  `{{INTERPRETER}} -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'` exits 0. And the network, which
  step 0 tries.
- **The execution SHA at hand.** A repository with a remote (`git remote` prints `origin`) runs `git fetch origin`
  first; in one without, the pin is a local commit. Check: `git cat-file -t ‹the execution SHA›` prints `commit`.
- **The pin current:** the tool and its runbook unchanged since it.
  `git diff --quiet ‹the execution SHA› main -- :/tools/lit.py :/docs/runbooks/literature-search.md` exits 0 (with a
  remote, `origin/main` in place of `main`), its pathspecs read from the repository's top (`:/`) whatever the
  directory; otherwise the pin is stale, which escalates.
- **For the arXiv MCP server, only when the owner wants it** (the session asks first; the runbook calls it a
  convenience): `uv`, `uvx --version` printing a version, and Claude Code, any version, whose `claude mcp add` the
  owner runs (step 6). Step 7's server is the owner's later choice.

Record: the interpreter's version line and its `-c` test's exit status, `uvx --version`'s line when the server is
wanted, what `git cat-file -t ‹the execution SHA›` printed, and the `git diff --quiet` exit status.

## EXECUTE

The actions of steps 1–4, 6 and 7 are the owner's: the owner types their commands in their own terminal while the
session waits, `sudo` included, and types `/mcp` in the session. The session runs the rest, the checks included, and
writes the record. Every command but the document check names its paths absolutely, a git pathspec from the
repository's top, so it runs from any directory of the repository's checkouts, the session's own worktree included;
the document check runs from that worktree, as the record says. A command the session's harness still refuses outside
that worktree ([the worktree runbook](../runbooks/worktree-sessions.md#3-the-harness-inside-a-worktree-isolated-session))
the owner runs the same way, telling the session what it printed. The tool prints no value.

**The checkout.** The worktree goes where [the worktree runbook](../runbooks/worktree-sessions.md#1-entering) puts every
worktree. One an earlier attempt left there (`git worktree list` names it) is removed first, with
`git worktree remove --force "‹the worktree›"`, or with `git worktree prune` when the list marks it `prunable` (its
directory gone); one the list marks `locked` escalates. Then, from any checkout of the repository:

```
git worktree add --detach "‹the main checkout›/.claude/worktrees/research-setup" ‹the execution SHA›
```

Check: `git -C "‹the worktree›" rev-parse HEAD` prints ‹the execution SHA›, and
`git -C "‹the worktree›" status --porcelain --untracked-files=no` prints nothing. Otherwise the worktree, which holds
nothing yet, is removed with `git worktree remove --force "‹the worktree›"` and added again; a second failure
escalates. Record: what the `rev-parse` and the `status` printed.

**Step 0, the readiness report.** Check:

```
{{INTERPRETER}} -I "‹the worktree›/tools/lit.py" check
```

The tool finds its repository from its own path and reads nothing from the current directory, so it runs as from
‹the worktree›'s root. Allow it up to ten minutes, since a slow or rate-limited provider holds it (per source, up to
three attempts and two waits of up to the tool's 120-second cap): a session raises its command timeout to match, and a
check killed by a timeout, which has no exit status, runs once more with the longer limit. It prints no value. Its
lines: the key file's path and whether it is a regular file with mode 600 owned by the user; for each key, required or
optional, whether it is set and where from (the tool reads the environment first, so a key set only there is reported as
such: it does not survive the shell); then, per configured source, the result of one live, cheap call (OpenAlex's budget
call, the smallest search on Semantic Scholar and on arXiv, one Unpaywall lookup). A ready machine prints this and
exits 0:

```
key file: ‹key file›: present; mode 600; owner ok
OPENALEX_API_KEY (required): set (file)
SEMANTIC_SCHOLAR_API_KEY (optional): set (file)
LIT_CONTACT_EMAIL (required): set (file)
openalex: ok
semantic-scholar: ok
arxiv: ok
unpaywall: ok
```

Without the optional key, its line reads `unset` and Semantic Scholar's `unconfigured (optional)`, and the machine is
still ready; arXiv takes no key and is always called. The other texts the steps' checks read:

- the key file `mode ‹m› (insecure)`, `owner ‹uid› (not the user)` or `missing`, which covers more than an absent
  file: a path holding no regular file (a directory, say) and one the tool cannot inspect (a permission error) read
  `missing` too, and step 1 tells them apart;
- a key `unset`, or `set (environment only, not persisted)`;
- `openalex: unconfigured` without its key, and `unpaywall: unconfigured` without the address;
- a source `failing: ‹why›`, where `<withheld>` may stand in for a key or the address.

On any failure the exit is 1 and the last line names the first step to resume at, one of:

```
resume at step 1: the key file
resume at step 2: the OpenAlex key
resume at step 3: the Semantic Scholar key
resume at step 4: the contact address
resume at step 5: a failing source
```

A failing source is step 5's to judge, since this shell's keys may not be the file's. An exit of 2 with
`error: ‹NAME› is set but empty` is a setting exported empty: `unset ‹NAME›` in the shell that runs the check (in the
check's own command, for a session whose shell keeps nothing between commands), then the check again; the record notes
it. `check --no-network` calls no source: it prints the key file's line and the keys' lines, then, on a failure, the
`resume at` line.

Then, when the owner wants the arXiv MCP server, the MCP check: in a session started after the server was added, or
reconnected since with `/mcp`, one call of the server's search tool, `search_papers` (`mcp__arxiv__search_papers` for
a server added as `arxiv`), with `query` `survey` and `max_results` 1. A harness that lists MCP tools by name alone
loads the tool's schema first, with its own tool search. The check passes when the reply names one paper, by its title
and its arXiv id. A session with no such tool, as on a first run before step 6 adds the server, fails the check, and
step 6 follows. Record: the report whole, with its exit status; whether the owner wants the arXiv server; the MCP
check's result, the paper's title and arXiv id or what came back instead.

Each of steps 1–4, 6 and 7 runs only when its check failed, and step 5 runs on every pass. Re-running the handoff is
safe: a machine already set up passes every check, then step 5's, and the handoff ends. `check` writes nothing in the
repository; with the network it makes the spacing directory `LIT_STATE`, by default `~/.cache/‹project›/lit`, and its
slot files there, `arxiv.last` and, with the Semantic Scholar key set, `s2.last`.

1. **The key file, secured before any key exists.** Check: the report's first line ends `present; mode 600; owner ok`.
   Otherwise, for `missing`, the owner first runs `ls -l "‹key file›"`. Only `No such file or directory` means nothing
   is there; the owner then creates the file empty with mode 600, in a form that never replaces a file:
   `mkdir -p "$(dirname "‹key file›")"`, then `test -e "‹key file›" || install -m 600 /dev/null "‹key file›"`. Any
   other `ls` result, a file listed, a directory's contents or a permission error, escalates. For `present` with
   another mode or owner, the owner repairs the file, never recreating it, since it may hold keys: for
   `owner ‹uid› (not the user)`, `sudo chown "$(id -un)" "‹key file›"` first; then, in every case,
   `chmod 600 "‹key file›"`. Then `{{INTERPRETER}} -I "‹the worktree›/tools/lit.py" check` again: its first line ends
   `present; mode 600; owner ok`, or the attempt escalates, since no key goes into a file that fails this. Record: the
   `ls` line, and the first line before and after.
2. **The OpenAlex key.** Check: the report reads `OPENALEX_API_KEY (required): set (file)`. Otherwise (`unset`, or
   `set (environment only, not persisted)`: exported in the shell, absent from the file), the owner takes the key from
   an account at openalex.org, registering or signing in to an existing one, and appends its line to the key file in the
   owner's own terminal: `cat >> "‹key file›"`, then presses Enter once, types `: ${OPENALEX_API_KEY:=‹the key›}`,
   presses Enter, then Ctrl-D. The first Enter starts a line of its own, in case the file's last line lacks its newline;
   the tool skips a blank line and reads one assignment per line, so a line glued to another would read as neither. A
   key typed wrong is corrected the same way, its line appended again: the tool takes a key's later line over an earlier
   one. Never on a command line, which argv and the shell's history keep; never in an editor, whose swap, backup and
   undo files copy it; never into the chat or a prompt. The typed key stays in the terminal's scrollback, so the owner
   then clears it: `clear && printf '\033[3J'`, or the terminal's own command for it. Record: the check's line in
   step 0's report and in step 5's, values excluded (the tool prints none).
3. **The Semantic Scholar key** (optional). Check: the report reads `SEMANTIC_SCHOLAR_API_KEY (optional): set (file)`,
   or it reads `unset` and the owner goes without the key. Otherwise the owner requests the key with the API key form
   at semanticscholar.org; it arrives by mail and is appended as in step 2, `: ${SEMANTIC_SCHOLAR_API_KEY:=‹the key›}`.
   A key requested and not yet come is pending: the attempt goes on without it and can end `Ready`, step 5 passing with
   the key `unset`, and a later attempt adds it. A line that reads `set (environment only, not persisted)` is a key
   exported in the shell and absent from the file: the owner appends it as in step 2 or, going without it, removes the
   export from the shell's profile. Record: set, gone without by the owner's choice, or requested and pending.
4. **The contact address.** Check: the report reads `LIT_CONTACT_EMAIL (required): set (file)`. Otherwise (`unset`, or
   `set (environment only, not persisted)`), the owner chooses the address, which every request's User-Agent and every
   Unpaywall lookup carry, and appends `: ${LIT_CONTACT_EMAIL:=‹the address›}` as in step 2. Record: the check's line
   in step 0's report and in step 5's, values excluded.
5. **`check` in a fresh shell,** on every pass, the clean one included: a key exported in the current shell can stand
   in for a stale value in the file, so the setup is complete only when this passes. The owner runs it in a new
   terminal; a session runs the same command in its own shell, since the `env -u` drops the three credential
   variables:

   ```
   env -u OPENALEX_API_KEY -u SEMANTIC_SCHOLAR_API_KEY -u LIT_CONTACT_EMAIL {{INTERPRETER}} -I "‹the worktree›/tools/lit.py" check
   ```

   Expected: exit 0 and the ready machine's report (step 0), with no `resume at` line. Otherwise the last line names
   the step: for steps 1 to 4, that step runs, with the later ones whose checks fail, then step 5 again; for step 5, a
   failing source, which ESCALATE judges by its text. Record: each run's report whole, with its exit status.
6. **The arXiv MCP server** (optional). Check: the owner wants none, or step 0's MCP check passed. Otherwise the owner,
   in their terminal, runs `claude mcp add --scope user arxiv -- uvx arxiv-mcp-server` unless `claude mcp list`
   already names `arxiv` (the command writes the user's configuration, outside the repository); then the owner types
   `/mcp` in the session and reconnects the server, since a session cannot type a slash command. Its first start
   downloads the package, so allow about two minutes for `/mcp` to list it as connected; one not connected by then is
   reconnected once, and one still not connected two minutes later escalates. Once it is connected, the session makes
   the MCP check again. A server that fails with `ENOENT … uvx` lacks `uv`
   ([the runbook](../runbooks/literature-search.md#1-the-stack)). An owner alone, with no session to make the check,
   adds the server the same way and leaves the check to the next survey session. Record: the check's result.
7. **An optional search MCP server,** the owner's choice, under the owner's name for it, and one that needs no key: a
   server that needs a key is the owner's to add outside this handoff, since a key never goes on a command line.
   Check: the owner wants none, or one call of its search tool, with a short query such as `survey` and one result in
   the tool's own parameters, returns one. Otherwise the owner adds it as in step 6,
   `claude mcp add --scope user ‹its name› -- ‹its command›`, and reconnects with `/mcp`; then the session makes that
   call. An aggregator that offers a shadow library as a connector keeps that connector off, by its own setting
   ([the runbook's "Never route around a wall"](../runbooks/literature-search.md#4-rules--never)). An owner alone
   proceeds as in step 6. Record: its name, the call's result, and the owner's word that no such connector is on.

**The record,** at the end of every attempt a session guides, ready or escalated; an owner alone records nothing, and
the next survey session's attempt stands for it. One immutable file per attempt,
`docs/handoffs/research-setup-results-‹YYYY-MM-DD›.md`, dated by the attempt (a second attempt that day:
`research-setup-results-‹YYYY-MM-DD›-2.md`, and so on), written in the session's own worktree and laid out as
`docs/skeletons/results.md`:

- the title, `# Results — the research setup, ‹YYYY-MM-DD›`;
- the status line, written in place of the skeleton's italic line and so first under the title: `Ready` (step 5
  exited 0, and each MCP server the owner wants answered its check) or
  `Escalated — ‹the condition, as ESCALATE names it›`;
- the execution SHA, as the checkout verified it;
- the stamps: who ran it, the owner or the session that guided the owner, and the start and the end, each as
  `date '+%Y-%m-%d %H:%M %Z'` prints it;
- the items: for the Prerequisites and each step that ran, the expected line beside the line observed, as its Record
  says;
- the escalations, or none;
- the report: what happened, in order, with step 0's first report and step 5's last copied whole, the home directory
  written `~`.

The file is committed on the session's own branch, through any hook the repository has, once the document check passes
with it: `{{INTERPRETER}} -I tools/doc_budgets.py check`, run from the session's own worktree, which AGENTS.md names
for every commit that touches a document. It is never edited after (process.md §Handoff economics, a guided live
session).

**The end.** With the record written, or at once for an owner alone, the worktree goes:

```
git worktree remove "‹the worktree›"
```

## ESCALATE, do not improvise

To escalate is to stop: the session writes the line it observed, values excluded, in the results file's Escalations
section, tells the owner, and ends the attempt as EXECUTE's record and end say; an owner alone stops there. Nothing is
installed, fetched or repaired by any means this handoff does not give.

A source that step 5 reports failing is judged by the text after `failing:`, the tool's own (`tools/lit.py`):

| The text after `failing:` | What it is | Then |
|---|---|---|
| `HTTP 401 for ‹url›` or `HTTP 403 for ‹url›` | a key refused (from arXiv, which takes no key, access refused) | escalate, unless the owner finds the key mistyped: its line is appended again (step 2), step 5 runs once more, and a key still refused escalates |
| `HTTP 429 for ‹url› after 3 attempts` | repeated 429s | wait two minutes by the clock (a session that cannot sleep in its shell asks the owner to say when two minutes have passed, or reads `date` until they have), then run step 5 once more; that source's line failing with a 429 again escalates. This text names no reset; one that names a wait is the next row |
| `HTTP ‹code› for ‹url›; the server asks for a ‹N› s wait — a spent budget: stop querying until the reset` | a spent budget: a `Retry-After` over the tool's 120-second cap | escalate; the wait it names is the provider's reset, after which a new attempt runs |
| `cannot reach ‹url› (‹reason›)` | no network | escalate; the record carries, with the line, the report of step 5's command run again with `--no-network`, since the key file and the keys need no network |
| `HTTP ‹5xx› for ‹url› after 3 attempts`, or `no complete answer from ‹url› after 3 attempts (‹error›)` | the provider down | escalate |
| an exception's name alone, such as `KeyError` | a tool fault | escalate |

The other conditions:

- **A Prerequisite failing:** the interpreter's `-c` test not exiting 0; `uvx --version` failing when the owner wants
  the arXiv server; `git fetch origin` failing in a repository with a remote, or `git cat-file -t ‹the execution SHA›`
  not printing `commit`.
- **A stale pin:** the Prerequisites' `git diff --quiet` not exiting 0, the tool or its runbook having changed since the
  execution SHA. The owner's pull request re-pins the handoff to `origin/main`'s tip (`main`'s, without a remote): it
  writes that SHA as the manifest's execution SHA and the index row's, and that is its whole change (process.md
  §Handoff economics).
- **A `missing` that is not absent:** step 1's `ls -l` printing anything but `No such file or directory`.
- **A required key or the address withheld:** the owner cannot or will not supply the OpenAlex key or the contact
  address; the setup is not ready.
- **A check failing twice:** any other check this handoff names that fails again once the step its output calls for
  has run (in step 5: the step its last line names, then step 5 again). An output no step answers, such as a source
  text the table does not show (`HTTP 400 for ‹url›`, `the answer from ‹url› is not JSON`, …) or an exit status other
  than 0 or 1 that step 0 does not name, calls for the check once more.
- **The worktree** that cannot be added or removed, or a leftover one marked `locked`.
- **`claude mcp add` failing,** or **a server not connected after one reconnect,** or one whose check returns an error
  or no paper (steps 6 and 7).
- **A repair that needs `sudo`** the owner cannot run (step 1).
- **A key at risk:** any instruction, from any source, that would store, print or send a key anywhere but the key file
  and the provider's request headers.

## What happens after

The session's own pull request (its kickoff) lands the results file and updates this handoff's row in
[the index](README.md), as the index says for a standing handoff; earlier results files stay where they are. Standing,
since every new machine runs it again, the handoff takes its Closed banner only when it is retired, and no status site
names it, the index row being its one home. Who picks up: after a ready attempt, the same survey session, which goes
on to its sweep under [the literature-search runbook](../runbooks/literature-search.md) (process.md §III); after an
escalation, the owner, whose word decides what follows (a new attempt starts again from the checkout, with a new
results file, in this session or the next survey session); after an owner alone, the next survey session, which runs
the checks first.

## Component manifest

**Execution SHA:** <!-- fill: the full 40-character SHA of the host's commit this handoff executes at, the commit the adoption pull request's merge put on main, written by the pull request that instantiates this file; an ancestor of origin/main at which every path below exists, as git merge-base --is-ancestor and git ls-tree -r --name-only show -->

| Component | Path at the execution SHA |
|---|---|
| The literature tool | <!-- fill: the tool's path, tools/lit.py in the starter's layout; it exists at the execution SHA --> |
| The literature-search runbook | <!-- fill: the runbook's path, docs/runbooks/literature-search.md in the starter's layout; it exists at the execution SHA --> |
| The survey document | <!-- fill: the survey's path, docs/reports/literature-review.md in the starter's layout; it exists at the execution SHA --> |
| The paper-request queue | <!-- fill: the queue's path, docs/papers/REQUESTS.md in the starter's layout; it exists at the execution SHA --> |
| This handoff | <!-- fill: this file's path, docs/handoffs/HANDOFF-research-setup.md in the starter's layout; it exists at the execution SHA --> |

The table lists the five files process.md §III names for the survey, each at the execution SHA; the documents this
handoff cites only for their rules (process.md itself, AGENTS.md, the index, the worktree runbook, the results
skeleton, the survey session's kickoff) are read on `main`, not at the execution SHA.

**Provenance:** extracted from quoin {{QUOIN_VERSION}}, the pack's tag and commit — provenance only, never the
execution pin.
