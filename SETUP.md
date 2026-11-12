# Setting up the environment

The way of working quoin carries assumes an environment, and this guide lists it: eleven pieces, each with what the pack
uses it for and how to check that it is there. The pieces belong to the machine and the account, not to a repository, so
none of them is copied into a repository that adopts the pack; [ADOPTING.md](ADOPTING.md) assumes them for both paths. A
missing piece seldom stops the work: [What degrades without each piece](#what-degrades-without-each-piece), at the end,
says what still works and which rule of the contract, [starter/docs/process.md](starter/docs/process.md), governs what
changes.

Commands are for bash or zsh. Each was read against its tool's own help (`--help`) on the author's machine before it was
written here, and each that only reports was also run there, except `claude auto-mode config`, which prints the
author's own auto-mode settings; the commands that change something (`claude update`, the plugin commands that add and
install, `codex login`, `gh auth login`) were read against their help and not run. Slash commands and settings keys have
no `--help`: the contract and Claude Code's settings schema name them. Where a tool has no command for something, the
guide says where the information is and gives none. The versions the pack was written against are Superpowers 7.0.0
and the Codex plugin 1.0.6. A word in angle brackets, such as ‹your notifier› or `<source>`, is yours to substitute.

## The pieces

### 1. Claude Code

**For.** Every session of the pack is a Claude Code session, and the plugins, agents, hooks and settings below are its
own.

**Check.** `claude --version` prints its version, and `claude auth status` shows whether it is signed in.
`claude --help` lists the `--model` and `--effort` options and the `plugin` and `auto-mode` commands that the pieces
below use; if one of them is missing, update Claude Code (`claude update`; a package-manager install updates through
the package manager).

### 2. The Superpowers and Codex plugins

**For.** Superpowers supplies the skills the loop names: `superpowers:brainstorming`, which an ideation session may use,
`superpowers:writing-plans` for the plan and `superpowers:subagent-driven-development` for the implementation
(process.md §I; §II, stages 3 and 5). The Codex plugin supplies the adversarial gate's runtime: the owner's
`/codex:adversarial-review` and the companion script that `tools/codex_gate.sh` runs (process.md §Adversarial review
protocol; [docs/runbooks/codex-gate.md](starter/docs/runbooks/codex-gate.md)).

**Install.** A plugin comes from a marketplace, added first with `claude plugin marketplace add <source>` and then
installed as `<plugin>@<marketplace>`:

```
claude plugin marketplace add anthropics/claude-plugins-official
claude plugin install superpowers@claude-plugins-official
claude plugin marketplace add openai/codex-plugin-cc
claude plugin install codex@openai-codex
```

`claude plugin marketplace list` shows the marketplaces already configured; add only those it lacks. The default scope
is user, so every project sees the plugins. Open a new session afterwards.

**Check.** `claude plugin list` shows `superpowers@claude-plugins-official` and `codex@openai-codex`, each enabled, with
its version.

### 3. The Codex CLI, logged in

**For.** The Codex plugin runs its reviews through the Codex CLI, whose configured default model is the gate's
(process.md §Model policy, the binding table; `codex --help` names its configuration file, `~/.codex/config.toml`), and
the gate launcher runs the plugin's script with Node.js.

**Install.** Install the Codex CLI and Node.js as their own documentation describes, then sign in with `codex login`
(`codex login --help` lists the ways). The plugin also has a `codex:setup` skill, described as checking whether the
local CLI is ready.

**Check.** `codex login status` shows the login state, `codex --version` the CLI's version and `node --version`
Node.js's.

### 4. `gh`, authenticated

**For.** GitHub is the default forge and `gh` the pack's pull-request tool (process.md §Conventions);
[ADOPTING.md](ADOPTING.md) step 11 and the worktree runbook's section 6 name it.

**Check.** `gh auth status` shows the account signed in to each GitHub host, and exits 1 when one has an authentication
problem (`gh auth status --help`); `gh auth login` signs in.

### 5. git, with worktrees

**For.** Every session works in a git worktree cut from `origin/main`, never in the shared main checkout (process.md
§II, Checkouts; [docs/runbooks/worktree-sessions.md](starter/docs/runbooks/worktree-sessions.md)).

**Check.** `git --version` prints the version, and `git worktree list`, run inside any repository, lists its working
trees. The loop also uses `git worktree add` and `git worktree remove`.

### 6. Python 3.9 or later

**For.** The pack's tools (the document check, the literature tool and the plan-blocks tool) are standard-library
Python, run as `python3 -I tools/<tool>.py …` (`-I` is Python's isolated mode, which `python3 --help` lists), and they
need Python 3.9 or later whatever language the project is written in. A host whose own suite is not Python runs the
document check from its CI by the command, `python3 -I tools/doc_budgets.py check`, which exits 0 when the documents
are within their budgets; the starter's wrapper test, `tests/docs/test_doc_budgets.py`, serves a host whose suite is
Python (process.md §Budgets). The starter's own tests, the tools' and that wrapper, are pytest tests: a Python host's
fast suite runs them with pytest, and a host whose suite is not pytest installs pytest for them or, as above, runs the
document check by its command from CI.

**Check.** `python3 --version` prints the version, and this exits 0 when it is new enough:

```
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'
```

To find the system interpreter, which a CI image or a machine with no other Python runs the tools with,
`type -a python3` lists every `python3` the shell can find, in the order it tries them (a version manager's or a
package manager's may come before the system's). On macOS and most Linux distributions the system's is
`/usr/bin/python3`, which the two commands above check when run with that path.

### 7. `uv`, for the arXiv server

**For.** The survey session's optional arXiv MCP server runs through `uvx`, which comes with `uv`. The literature
runbook describes the server ([docs/runbooks/literature-search.md](starter/docs/runbooks/literature-search.md), section
1), and step 6 of the research setup handoff
([docs/handoffs/HANDOFF-research-setup.md](starter/docs/handoffs/HANDOFF-research-setup.md)) registers it. The
literature tool itself needs only Python (item 6).

**Check.** `uv --version` and `uvx --version` print the versions. Install `uv` as its own documentation describes.

### 8. The effort pin at launch

**For.** An orchestrator session is launched with its effort pinned, and the owner confirms it with `/effort`
(process.md §Model policy, the binding table):

```
claude --model <id> --effort max
```

`<id>` is the model the binding table gives the session's class, and the kickoff prompts in
[docs/skeletons/](starter/docs/skeletons/) open with this line.

**Check.** `claude --help` lists `--effort <level>`, which takes low, medium, high, xhigh or max, and `--model <model>`.

### 9. The dispatch rule

**For.** The loop runs one subagent at a time unless the owner names the fan-out; that is the owner's standing gate on
parallel dispatch (process.md §Model policy, Dispatch). The settings can carry the gate as a rule: the settings schema
describes the `soft_deny` list of `autoMode` as the auto mode classifier's soft-block rules, which the user's own intent
can clear, and the rule below is an entry for it. The rule holds a session only in auto mode (`claude --help` lists the
permission modes, `auto` among them), so it backs the contract and does not replace it. It belongs in the `soft_deny`
list of the user settings, `~/.claude/settings.json`, after `"$defaults"` so that the built-in rules stay. Its wording
is the author's, copied from the author's own settings:

```json
{
  "autoMode": {
    "soft_deny": [
      "$defaults",
      "Do not launch parallel agent fan-outs or bulk fetch sweeps — several subagents at once (directly or via a workflow script), or fetching many URLs in a batch — unless the user has named that specific fan-out in this session. This is a standing approval gate over parallel dispatch, not an efficiency preference: the user, not an agent, decides when work fans out. A single subagent on a scoped task is normal, and so is spawning subagents sequentially, one at a time, each after the previous returns."
    ]
  }
}
```

If the file already has an `autoMode` object or a `soft_deny` list, add the entry to it and keep what is there; the file
is never replaced.

**Check.** `claude auto-mode config` prints the effective auto-mode configuration as JSON ("your settings where set,
defaults otherwise", by `claude auto-mode --help`); the entry belongs in its `soft_deny` list.

### 10. Notification hooks, optional

**For.** A session ends at a hard stop or a pull request and waits for the owner, a round can be flagged as the owner's,
and a background job such as a gate round finishes unattended (process.md §II; §Adversarial review protocol, Waiting on
a job). A hook that alerts you when a session stops or asks for attention saves watching the terminal. The pack depends
on none.

Hooks live under the `hooks` key of the user settings, `~/.claude/settings.json`, one list per event: `Notification`
runs when Claude Code raises a notification and `Stop` when Claude stops.

```json
{
  "hooks": {
    "Notification": [
      { "hooks": [ { "type": "command", "command": "‹your notifier›" } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "‹your notifier›" } ] }
    ]
  }
}
```

‹your notifier› is any command that alerts you, such as your platform's notifier or a sound player. If the file already
has a `hooks` object, or a list for either event, add the entry to it and keep what is there; the file is never
replaced. Claude Code also has built-in notification settings, `preferredNotifChannel` among them, which may be all that
is wanted.

**Check.** `/hooks` in a session shows the hooks in force and lets you edit or disable them.

### 11. Listing the models an environment offers

**For.** The binding table gives each role a default model, and a default that the account does not offer is rebound at
adoption (process.md §Model policy, The binding table; [ADOPTING.md](ADOPTING.md) step 6), so what the account offers is
the first thing to know.

**Check.** There is no `claude` command that lists models: the command list of `claude --help` has none. In a session,
`/model` opens the picker, which shows what the account offers; an organisation can narrow it with the `availableModels`
setting of its managed settings, so what the picker shows is what counts. `--model` takes an alias for a family's latest
model or a model's full name (`claude --help`), and the binding table writes full names. Compare the picker with the
defaults the binding table names.

## What degrades without each piece

Each row names a missing piece, says what still works and what changes, and points at the rule, which is the contract's.
A model named here is a default of the binding table.

| Without | What still works, and what changes | The rule |
|---|---|---|
| The Superpowers plugin (item 2) | The loop is unchanged, with its gates and seats. The planning session writes the plan by hand, laid out as [the plan skeleton](starter/docs/skeletons/plan.md); the implementation session carries it out itself, task by task, in the shape of Superpowers' `executing-plans` skill, with no per-task subagents, and keeps the ledger by hand at the same path. | process.md §II, stages 3 and 5 |
| The Codex plugin, its CLI logged in, or Node.js (items 2 and 3) | The loop is unchanged. The gate's tool is unavailable, so the reviewer seat in gate mode runs each gate round. | process.md §Adversarial review protocol, The gate transitions |
| `gh`, or not signed in to it (item 4) | Nothing in the loop needs the tool: pull requests are opened, read and merged on the forge's own page. The two commands of the pack that name it are a convenience (ADOPTING.md step 11; the worktree runbook, section 6). | process.md §Conventions |
| Python 3.9 or later (item 6) | The document check, the literature tool and the plan-blocks tool do not run. A host leaves the budgets off (the checklist's row on budgets in ADOPTING.md). Nothing else of the pack runs on Python. | process.md §Budgets |
| `uv` (item 7) | The arXiv MCP server is off, and a survey session reads filed PDFs with the Read tool, which is the canonical way to read a paper in any case. The literature tool runs on Python alone. | docs/runbooks/literature-search.md, section 1 |
| The effort pin at launch (item 8) | The orchestrator runs at the effort Claude Code starts with, not the binding table's max; the owner's `/effort` check at the start of a session is what catches it. | process.md §Model policy, The binding table |
| The dispatch rule in the settings (item 9) | The contract still binds the sessions; only Claude Code's own hold on a session that would fan out is missing. | process.md §Model policy, Dispatch |
| `fable` not offered (the default of the planning class, counsel and the reviewer) | The strongest model the account offers takes the planning class and both seats, rebound at adoption in the binding table and the two seat files. The two session classes stay. | process.md §Model policy, The binding table; ADOPTING.md step 6 |
| `opus` not offered (the default of the implementation class) | Rebound at adoption in the same way, in the binding table, to the strongest model offered. | process.md §Model policy, The binding table |
