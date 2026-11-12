# Process — the way of working

*{{PROJECT}}'s way of working. This document is the live contract: it states the current rule only. Its history — the
provenance and the dated rulings — is [docs/process-log.md](process-log.md). The per-session digest lives in
[CLAUDE.md](../CLAUDE.md), the repository's mechanics in [AGENTS.md](../AGENTS.md), the decision series and their
anchors in [docs/id-registry.md](id-registry.md).*

## Purpose and principles

The repository is built across many sessions by orchestrator agents, with {{OWNER}} — *the owner* below — as reviewer
and decision-maker. The docs are the memory: a **fresh orchestrator must be able to open CLAUDE.md → roadmap → the
next item's design doc — its Read-first sections and its Active obligations — and start productive work with no other
context.** An assistant's private memory is a pointer into the repository, canonical only for live machine state and
preferences not yet codified: a rule that lives only in memory is how rules get lost. Everything below serves that.
Which model sits in which seat is the [Model policy](#model-policy).

- **PR gate everything.** All work — code, docs, roadmap edits — lands via feature branch and a PR the owner reviews.
  No direct-to-main.
- **Evidence over vibes.** Claims cite measurements, anchors or file:line, and every number carries its source: the
  command that printed it, the file and line, or the observation. Decisions get recorded rulings with rationale (the
  decision-log habit), including *dismissals* of review findings. A web source is quoted only from raw page text
  fetched with `curl`, never a summariser's output. A coverage claim needs a mutation check, and a surviving mutant is
  a pin to add. An anchor that asks for the owner's judgment of something visual ships a rendering of it, never the
  bare numbers behind it.
- **Validation anchors.** Every roadmap item names the check that certifies it before anything builds on it. An item
  without an anchor isn't ready to implement.
- **One home per fact.** Every fact has one canonical home and every other site points at it (§Canonical and pointer
  sites; the taxonomy's last column). Docs are updated at merge time, in the same PR: the roadmap's status paragraph,
  the design's header and Active obligations and CLAUDE.md's Status are *replaced*, never appended to (§II stage 7).
  Merge = docs current; a stale status line is a bug, and so is a second copy of a claim.

## Session types

### I. Ideation session

Ad-hoc or deliberate planning — native discussion or `superpowers:brainstorming` — whose output is a **design doc** in
`docs/designs/<slug>-design.md` plus a roadmap entry (or an update to an existing directional doc before its
implementation starts). Work happens on a feature branch, PR-gated like everything else. Design docs marked
*directional* in their header **must** get an ideation pass (updating the doc, resolving its open questions) before
the item is planned; *implementable* docs may go straight to the planning session. Ideation is owner-interactive: it
runs as a main session of the planning class (§Model policy) and, like every session of that class, ends at its PR; it
implements only what the owner sanctions in that session.

**The house shape of a design doc** (its skeleton: [docs/skeletons/design.md](skeletons/design.md)): a **header** within its budget
(§Budgets) — the roadmap item, the dates (written, last updated), the depth marker, one status per wave in the
roadmap's template, the anchor in one line, where the rules, the rulings, the review records, the report, the plan and
the explainer are, and a **Read first** line naming the sections a fresh session needs and their size; no headline
figure and no ruling (a ruling made when the header is written is a dated log row the header cites); the goal and
non-goals; the decisions, their series registered in [docs/id-registry.md](id-registry.md); the architecture; the
validation anchor (with a labelled Result line once it ran); the work breakdown; an **Active obligations** section
before the decision log — the open items for the item, and what it hands to a named next item with a fallback, each
citing its source, updated at every merge that opens or closes one ("none open" is valid); and the **decision log** (a
dated ruling + rationale table).

**The decision log is a pair:** the table in the design and, where a wave's review records exceed about a thousand
words that no plan or report already holds, the companion log `docs/designs/<slug>-design-log.md`. Rulings,
adjudications, pre-registrations, pinned facts (a verdict, an anchor, a measured result later claims stand on), the
owner's and counsel's rulings, the plan-level `R-<item>-<n>` rows, obligations and notes for the next session stay in
the design with their titles verbatim — these are the rows code, tests and the plan check cite. Gate rounds with their
findings' dispositions, fix waves, re-reviews, status and PR rows, seat logs and pointer rows move to the companion log
once the wave is closed: merged, and no pending session names its rows. A pending session is one "Now and next" lists,
and it names a row when its spec — the roadmap bullet, a design's Active obligations, a plan, or the owner's prompt as
it stands or as a proposal re-points it — cites the row by id, date or title; a PR that moves a named row and
re-points that spec in the same PR may move it. Each row moves verbatim with its date and position, never renumbered.
A ruling that binds later work — a standing exception, a pinned fact, a pre-registration, an open obligation — stays
whatever the title of the row that holds it: such a mixed row is split by function, the original moving whole and the
design keeping an excerpt row of the same date titled "(excerpt of the row '‹the row key›' — the original verbatim in
the companion log)"; a row whose title names neither class stays. A log row is never edited: a ruling later overturned
gets a new dated row appended at the end; "rewritten in place" (§Canonical and pointer sites) is for the body.

### II. The loop — one item, two sessions

Every item, on the roadmap or outside it, is planned in one session and implemented in another, and the owner starts
both. The **planning session** runs on the planning class and ends at a hard stop. The **implementation session** runs
on the implementation class and starts only from a plan that is already on `main`. Either session analyses
intermediate results, makes educated decisions, and asks the owner only what only the owner can answer (batched via
structured questions; trivia gets a default and a recorded ruling instead). The [Model policy](#model-policy) binds the
models, the seats and their triggers.

**Checkouts.** No session checks out, resets, cleans, commits to or edits the main checkout: concurrent sessions share
it, and a live process that imports from it — a server, a long run — freezes it until the owner stops it, pulls and
restarts it. Every session fetches (`git fetch origin`) and works from `origin/main`: its branch is cut from it in a
git worktree (`EnterWorktree`, the branch renamed to `docs/<slug>-plan` or `feature/<slug>`; or
`git worktree add --no-track -b <branch> <path> origin/main`, without tracking it, since git's hint for a tracking
branch is a push to `main`), the plan check verifies that the merge commits it depends on are ancestors of HEAD
(`git merge-base --is-ancestor <sha> HEAD`), and every gate passes an explicit `--base` (§Adversarial review protocol,
Scopes), never the local `main`. The local `main` serves only when it equals
`origin/main`: a shared or frozen checkout lags, and a branch cut from it lacks the plan. A worktree's checks run its
own source, with dependencies and built artefacts compatible with that revision. Only these write into the main
checkout, beside the host's own writes listed below: the two copies — the SDD workspace into its `.superpowers/sdd/`
at stage 8, and a new file beside the owner's prompts in its `local/` (a proposal, never an edit of the original),
copied from the worktree with `cp` where the harness's write tools refuse paths outside it — ignored paths that move
neither HEAD nor a tracked file; and the post-merge fast-forward of stage 8, made only when no peer session is in the
checkout, no live process freezes it and the merge leaves the dependency manifests and lockfiles unchanged (an install
is the owner's). The operating detail is [docs/runbooks/worktree-sessions.md](runbooks/worktree-sessions.md).

<!-- fill: this host's worktree environment and its own writes into the main checkout — the interpreter by absolute path, the gitignored data reached by absolute path, each command that writes there with its reason; the rule above, the recipe in docs/runbooks/worktree-sessions.md -->

**Planning session — stages 1–4**

1. **Start clean.** A fresh session, a worktree off `origin/main` (Checkouts). Read CLAUDE.md → roadmap → the item's
   design doc (its Read-first sections and its Active obligations) → the report sections its Read-first line and its
   Active obligations cite. The roadmap entry is the spec: a prior session's brief or kickoff prompt yields to it on
   scope, order and purpose. Confirm the item's dependencies are merged; if not, stop and surface it.
2. **Branch.** `docs/<slug>-plan` off `origin/main`.
3. **Design doc, then the plan.** If the design doc is missing or still *directional*, run the ideation pass first (the
   same session is fine). Then write the plan in `docs/plans/` with `superpowers:writing-plans` (where its defaults
   differ, the repository's skeleton, folders and process govern):
   - The design doc states intent; the ground truth decides facts — the code, the committed fixtures, the shipped
     artefacts, the recorded observations. Where they disagree the ground truth wins and the plan records the
     correction.
   - Every number in the plan carries its source (§Purpose and principles); a formula with no observation behind it is
     marked **unpinned**, with the observation that would pin it.
   - Plan-level rulings are numbered `R-<item>-<n>`, each with its rationale and its cost if wrong, and are mirrored
     into the design doc's decision log. The plan names its gate record by link.
   - Survey with scripts, and read slices of large dumps rather than the dumps.
4. **Adversarial design review.** The adversarial gate after `git fetch origin`, scoped so the design doc is in the
   reviewed diff (§Adversarial review protocol, Scopes), with focus text pointing at the design doc and the plan. Judge
   every finding against the ground truth: **incorporate or dismiss, each with a recorded ruling** in the design doc's
   decision log, and amend the plan. The log records each round and whether a re-gate follows
   ([the gate transitions](#the-gate-transitions)); none is left pending at the hard stop. Findings the session cannot
   adjudicate with data or logic escalate to the owner.

**Hard stop.** The planning session ends by opening the **planning PR**: the plan with its row in the plans index
([docs/plans/README.md](plans/README.md); §Doc taxonomy, the Plan row), the design doc with its rulings and gate rows, the roadmap's
status paragraph set to *planned* with the plan's path, and the queue's update — "Now and next" and CLAUDE.md's Status
naming the next session (§Roadmap upkeep). The PR's number follows at the status sites and in the plan's index row, by
one more commit (stage 7). The description lists the rulings made in the owner's place and the questions only the
owner can answer. The session dispatches no implementers and writes no code or tests for the item.
Merging the planning PR is the owner's go-ahead to implement. The one exception is implementation the owner sanctions
in that session, for a change small and contained enough for the small-change lane.

**Implementation session — stages 5–8**

It opens as stage 1 does — a fresh session, a worktree off `origin/main`, the same reads plus the plan and the Model
policy — and runs the **plan check**: the roadmap entry (or the "Now and next" line, for work outside the roadmap's
items) names the item's plan; the plan is on `origin/main` and its merge commit is an ancestor of HEAD
(`git merge-base --is-ancestor <sha> HEAD`); the gate record the plan names by link — in the design doc's decision log,
never a companion log — records the design gate over that plan, with every finding ruled and the record closed
([the gate transitions](#the-gate-transitions) say when); the depth marker reads *implementable*; the session's agent
list shows both seat types. If any of these fails, stop and tell the owner what is missing. The orchestrator does not
write, extend or replace a plan; it edits one only as the record freeze allows (§Canonical and pointer sites). Then
branch `feature/<slug>` off `origin/main`.

5. **Implement.** `superpowers:subagent-driven-development` against the plan; TDD; the fast suite
   (`{{TEST_COMMAND}}`) and the checks AGENTS.md names green throughout — implementers run the touched test files, and
   the orchestrator runs the full fast suite in the background beside each task review and gates the next dispatch on
   it. The orchestrator monitors progress and analyses intermediate results rather than delegating blind. A
   subagent's report is a claim: before acting on it the orchestrator checks the part that matters itself (the tree
   state, the named tests, the fact a later task will build on). The **counsel triggers** apply throughout. Work the
   plan does not cover — a new task, module or interface — is planning: stop and flag it. Fix waves that implement
   ruled findings are part of the loop. The SDD ledger lives in `.superpowers/sdd/<date-slug>/` (the plan's file name
   without `.md`), local and untracked (gitignored), kept and never deleted, holding the rulings (§Model policy,
   Records); everything durable from it is promoted into the design doc's decision log and the item's report.
6. **Final adversarial review.** With every change committed (`git status --short` clean, stage 7's records included
   but for what follows the gate: the gate's and the seats' decision-log rows, the open items the whole-branch review's
   triage defers, and the PR number), the checks AGENTS.md names for a commit green and
   `git diff --stat origin/main...HEAD` covering the intended files, the adversarial gate `--base origin/main`
   (§Adversarial review protocol). Every finding addressed or explicitly acknowledged with a ruling. Then the
   **whole-branch review**: the reviewer seat and the second whole-branch review (§Model policy), one after the other,
   each on the same package — the branch diff, the plan, the ledger's rulings, the gate's findings with the
   orchestrator's proposed ruling on each — and neither shown the other's report, the SDD ledger included, until both
   return. Their findings go into one fix wave. Every fix wave, the gate's and that one, follows
   [the gate transitions](#the-gate-transitions); a gate round after the whole-branch review counts, and its findings
   are trigger 1's.
7. **PR.** Cut for owner review — the description, the test evidence (which gates ran), the anchor status, screenshots
   for visible changes, the rulings made in the owner's place and the seat log (§Model policy). The same PR
   **replaces** (never appends to) the item's roadmap status paragraph, the status line of its design's header and
   CLAUDE.md's Status, each within its budget (§Budgets): the previous text leaves, what it said lives in the report or
   the log, and every figure cut from a status site is grepped at its canonical home first and migrated there
   verbatim, with its label, if absent. The same PR updates the design's Active obligations (resolved items leave, new
   ones enter) and records what it hands on in the report's open-items section — every deferred minor by file and
   symbol, with a destination and a fallback, routed to the next item if logical and to the later one otherwise (a
   parking-lot bullet where none exists), none lost, never only in the SDD ledger. A status site carries "PR #N" and the
   PR's own date (the day it is cut) and states the result the merge makes true — "merged" is written in the PR, since
   the text reaches `main` only if the PR merges — never a merge SHA, a merge date or a branch name: git records the
   merge. The number is written once the PR is open, by one more commit on the branch. A docs-only PR after a merge is
   for a real post-merge event (a handoff's results, a ruling that changes a rule), never for stamping. The PR
   description, like every report to the owner, leads with the high-level layer — done, results, recommendations, the
   ask — with the detail behind it, in plain words: no internal labels or ruling ids in the top layer, and each ask says
   what is needed, why and by when. Review comments are addressed in-PR until approval.
8. **Post-merge.** Any leftover tasks completed or filed as roadmap entries. The session confirms the merge as
   §Conventions' merge-method row says, copies the SDD workspace from the worktree into the main checkout's
   `.superpowers/sdd/`, then removes the worktree (`git worktree remove`) and deletes the merged branch, local and
   remote; the main checkout's `main` is fast-forwarded as Checkouts allows, or else pulled by the owner. A ruling the
   owner makes in chat at the review lands in the next PR that touches the design (Standing decisions or the design's
   decision log); memory and the owner's local prompts may hold it only until then. The roadmap is ready for the next
   clean session.

### III. Survey session

Recurring review of the **external landscape** — literature, released code, tools, prior art — kept as one standing
document, [docs/reports/literature-review.md](reports/literature-review.md): standing sections revised in place, the
index of filed papers, a dated sweep log, and a **watchlist** the next sweep starts from; a living document, exempt
from the record freeze of §Canonical and pointer sites. Three jobs: *reuse* (what is solved — adopt it or cross-check
against it), *novelty* (what stays unsolved — where the project's results stand), *feasibility watch* (external claims
against our understanding). Method: research subagents — a parallel fan-out only when the owner names it in the
session (§Model policy, Dispatch) — primary sources cited inline and their PDFs filed under `docs/papers/` (a
paywalled one queued for the owner in [docs/papers/REQUESTS.md](papers/REQUESTS.md)), every citation checked against
its source by an independent **verification pass**, the survey's gate, and the findings landing through the usual PR
gate. The tool is [tools/lit.py](../tools/lit.py) and the procedure
[docs/runbooks/literature-search.md](runbooks/literature-search.md); the tool's setup is the five-section handoff
[docs/handoffs/HANDOFF-research-setup.md](handoffs/HANDOFF-research-setup.md), instantiated at adoption — its checks
first, each step idempotent and run only when its check fails, the closing fresh-shell check on every pass, every
key-holding action the owner's — so a machine already set up passes every check and the handoff ends, and a
half-configured one resumes at its first failing step.
**Triggers:** before the ideation of an item whose methods the field may already hold, before any public writeup or
release, when a watchlist item fires, or on the owner's request.

### Small-change lane

Typos, one-line bugs, doc corrections: branch → fix → PR. No design doc, no plan, no gates, no ceremony. Judgment
call; when a "small change" starts growing opinions, it upgrades to the loop (the one-way ratchet) — and the loop
starts with a planning session, so an implementation session that reaches this point stops and flags it. Work an
orchestrator did inline that belonged in the loop is declared as such in its PR and gets a retrospective review there
— a gate round or a seat review — before it lands.

## Adversarial review protocol

- **Reviewer:** OpenAI Codex through the codex plugin — a challenge review of approach, tradeoffs and assumptions, not
  just a defect pass. Model: the CLI's configured default; override per run only with a recorded reason.
- **Two entry points, one runtime.** The owner types
  `/codex:adversarial-review [--background] [--base <ref>] [--scope branch] <focus text>`; the slash command is
  user-invocable only, so the orchestrator runs the same runtime from Bash through the launcher,
  `tools/codex_gate.sh FOCUS_FILE [--scope branch | --base REF]`, which runs the plugin's
  `codex-companion.mjs adversarial-review` in background mode from the root of its own checkout (a worktree's launcher
  reviews that worktree); `status` and `result` from the same companion script collect. Everything after the flags is
  focus text — a stray `--help` runs a review instead of printing usage. The recipe and the gotchas:
  [docs/runbooks/codex-gate.md](runbooks/codex-gate.md).
- **Waiting on a job.** A background review is waited on with a harness-tracked background poll of `status <job>`
  until it reads completed or failed — never a detached launch left unread — and the owner is told the job id and that
  a waiter is armed. A launch that exits non-zero on a quota refusal is the first signal that the round is a seat
  round ([the gate transitions](#the-gate-transitions)).
- **Scopes.** Both gates read **committed history only**: `--base <ref>` (and `--scope branch`) diff `<base>...HEAD`,
  and staged, unstaged and untracked work is invisible. Commit before each gate and check that
  `git diff --stat <base>...HEAD` lists the files the gate is meant to see. From a worktree every gate passes `--base`,
  since the plugin's branch scope compares against the local `main`, which a fetch never moves (§II, Checkouts). The
  design gate (stage 4) takes `--base origin/main` when the design doc is on the branch and, when the doc already
  merged on its own PR, `--base <the commit before that PR merged>`, so the doc is in the reviewed diff; the final
  gate (stage 6) takes `--base origin/main`; a re-gate takes its base from
  [the gate transitions](#the-gate-transitions). `--scope working-tree` exists for an informal look at uncommitted
  work; it is not a gate. Background mode for anything beyond a couple of files. The review reads the diff plus
  [AGENTS.md](../AGENTS.md), so AGENTS.md must be current.
- **The gate package.** The focus text lives in a file (its skeleton: [docs/skeletons/gate-focus.md](skeletons/gate-focus.md))
  and names its **mandatory reads** — the design sections that govern the diff and the item's editable surface with its exceptions
  — and the questions that matter; on a re-gate it names the fix commit, lists the areas earlier rounds confirmed and
  asks for a verdict. It carries no dash-led token: the companion reads one as a flag, and the launcher refuses the
  file. The review states what it read or discloses the context it lacked.
- **Document-review variant.** The same gate reviews prose — design docs, explainers, this document; the focus text
  names the questions the document must survive.
- **Judging.** The orchestrator is the judge, not a stenographer. Each finding → *incorporated* (with the change) or
  *dismissed* (with data or logic), logged in the design doc's decision-log table. A finding that survives two rounds
  of disagreement between orchestrator and reviewer, and is material, goes to the owner.
- The review is **advisory input to the orchestrator**, never an auto-apply. Superpowers' own reviewers (the SDD spec
  and quality reviewers, `requesting-code-review`) remain the per-task inner loop; the gates are the outer loop at
  stages 4 and 6.

### The gate transitions

Rounds are counted per gate, and a round counts once it has returned a finding or a verdict. The loop's stage 6 and
the Model policy's cap cite this table instead of restating it.

| Event | What follows |
|---|---|
| The gate returns findings | each ruled incorporated or dismissed in the decision log; the fix wave is normal commits |
| A fix wave that changes substance — a rule, a decision, an acceptance criterion, a gate, a tolerance, an interface or code behaviour, in any file — with rounds left under the cap | one more gate round on the wave (`--base` the previous round's commit); substance takes precedence over file type |
| A fix wave that changes no substance — wording, status sites, links, formatting — whatever the file | a scoped re-review by an implementation-class subagent, at the implementation orchestrator's model (the binding table); no gate round |
| The cap (three rounds) is reached | no further round for that gate, whatever later changes; every later change is listed in the PR as ungated with its scoped re-review; a change that touches a ruling goes to counsel; the whole-branch review rules on the wave if it has not yet run |
| A post-cap fix wave applies a scoped re-review's findings as the review worded them | one confirmation pass by a subagent of the review's class, each fix checked against the review's wording — not a fresh re-review; the pass's own items are applied without a further pass and listed in its row (the cap row's counsel clause still governs one that touches a ruling); a fix the pass finds not applied as worded is redone and confirmed again on that fix alone; the gate's record closes with the pass |
| A tool round returns neither a finding nor a verdict (refused at launch, killed before any finding, wedged at start) | not a round: cancelled and replaced by one reviewer-seat round in gate mode, which counts once it returns a finding or a verdict; the tool round's captured messages are judged as findings |
| A seat round in gate mode returns nothing (dies mid-run) | not a round: dispatched once more; dying again, an implementation session gives the package to the stand-in (provisional, listed in the PR) and a planning session waits for the seat; the stand-in returning nothing ends the ladder — the session stops and flags the round as the owner's |
| A round returned findings and died before its verdict | a round: its findings are judged; the verdict is recorded as absent |
| The gate's tool is unavailable (quota, outage) | the reviewer seat in gate mode runs the round, which counts; the owner is told |
| A seat's bound model is unavailable at run time | its stand-in (the binding table) with the same package, the ruling provisional and listed in the PR; in a planning session, planning waits |
| The stand-in is unavailable too, or is the model that failed | the ladder ends: the session stops and flags the round as the owner's, in its ledger and last message, and in a PR once cut; nothing is ruled in its place |
| The owner waives the cap for a named round | recorded in the decision log; the round runs and counts |

A gate's record is **closed** when no round is owed and either its last round approved or every finding of that
round is ruled and any scoped re-review or confirmation pass has run or is listed as not run.

## Handoff economics

**The pattern.** An orchestrator babysitting a long serial computation burns its prompt cache between checks and
re-sends a long history every poll — expensive exactly when nothing intelligent is happening. So:

1. The orchestrator prepares the batch and writes `docs/handoffs/HANDOFF-<name>.md` with the five-section contract
   below, plus any helper scripts beside it.
2. A **cheaper monitor session** (the binding table) — or the owner, in a terminal — executes the handoff: launches,
   watches, restarts per its instructions, collects the artefacts, and writes `docs/handoffs/<name>-results.md` when
   done.
3. A **fresh orchestrator** resumes from the results doc and the roadmap — not from the old session's transcript —
   once it has checked that the handoff and the results doc are committed on the branch it reads them from and that
   the results doc names the handoff's execution SHA. When the results feed an item in flight, this is an
   implementation session.

**The handoff contract** — five sections (the skeleton: [docs/skeletons/handoff.md](skeletons/handoff.md); the handoffs
are indexed in [docs/handoffs/README.md](handoffs/README.md)):

- **Prerequisites** — the machine, the branch and commit, the environment, the files that must exist; checked before
  starting.
- **EXECUTE** — the numbered steps, verbatim commands, expected outputs, what to record.
- **ESCALATE, do not improvise** — the conditions under which the monitor stops and asks a human instead of getting
  creative. This section is load-bearing: monitors execute, they do not redesign.
- **What happens after** — where the results go, who picks up, which docs get updated.
- **Component manifest** — the handoff's **execution SHA** (the commit the executing session checks out) and a table
  of every artefact the handoff references → its path in that commit.

**The self-containment check** before shipping: the SHA is committed and, for a cross-machine handoff, pushed and
reachable from the remote branch (`git fetch origin`, then `git merge-base --is-ancestor <sha> origin/<branch>` —
pushing the feature branch for this is part of the loop, not a PR); every component path exists in that commit
(`git ls-tree -r --name-only <sha> -- <path>`), not merely in the local index, which `git ls-files` reports and which
passes staged and unpushed work; every command is inlined, never "see the procedure in a local report"; every script
runs against that commit's code alone. **The executor's first EXECUTE step verifies the checkout, not just its HEAD:**
`git rev-parse HEAD` equals the SHA **and** `git status --porcelain --untracked-files=no` is empty (tracked files
unmodified; untracked run artefacts are expected), and any built artefact is **rebuilt from that clean checkout** at
launch — one installed earlier survives a change of checkout and cannot certify which source built it.

**The dry read.** Before a handoff for a cheaper model is published, a subagent of that class dry-reads it under hard
limits (no writes, nothing that touches the live system) and runs the read-only prerequisite checks: the author knows
too much, and the dry read finds what the author cannot.

**A guided live session** uses the same contract. When a step needs the owner at a running system and no judgment from
the orchestrator, a monitor-class session (for the research setup, the implementation-class survey session:
§Model policy) guides the owner through the runbook from a handoff and reports what was observed; it interprets nothing,
and the session that owns the question rules from its results. The results a guide writes are one immutable file per
attempt with a status line, finalised after the checks AGENTS.md names for a commit have run on it, by hand in a
repository without hooks. Such a handoff can run beside an implementation session, which must not wait for it. The
research setup handoff (§III) is **standing**: run on every new machine by the survey session or the owner, with
`<name>-results-<YYYY-MM-DD>.md` per attempt, a banner only when retired, and its manifest and index row re-pinned by
the owner's pull request when its tool or runbook changes, the record freeze's exception for it.

The same contract serves **cross-machine** work: the handoff is written so the remote session needs nothing but the
repository and the doc. **Threshold judgment:** a five-minute test run is not a handoff; a parameter sweep, an
overnight batch or anything serially longer than the handoff threshold ([Conventions](#conventions)) is. When several
short runs chain into a long serial window, treat the window, not the runs.

**Runbooks and handoffs:** a *runbook* ([docs/runbooks/](runbooks/)) is durable and reusable — how to operate a thing;
a *handoff* is one-shot — this batch, this window, these results. Handoffs cite runbooks instead of repeating them.

## Doc taxonomy

| Type | Location / naming | Created | Purpose | Canonical for |
|---|---|---|---|---|
| Roadmap | `docs/roadmap.md` | once; updated at merges and ideation | Ordered items, anchors, one status paragraph each, "Now and next", the parking lot, standing decisions | Item state, the queue, reorders, parked items |
| Process | `docs/process.md` | once; amended by PR | This document | The rules of work |
| Process log | `docs/process-log.md` | at adoption | The history of this document: its provenance and the dated rulings on it | A ruling on this document |
| Digest | `CLAUDE.md` | at adoption; replaced at every merge | The auto-loaded digest: the Status, the doc map, the way-of-working digest, the Load-bearing facts | A pointer site (§Canonical and pointer sites): the next session in the Status; durable findings as labelled lines |
| Front page | `README.md` | once | Setup, quick start, the producing commands | — |
| Id registry | `docs/id-registry.md` | at adoption; a row per new series | Every decision series → the document and section of its effective text and of its rulings; collisions recorded | The map of ids |
| Design | `docs/designs/<slug>-design.md` | ideation | Per item, in the house shape of §I: the header within its budget, goals, decisions, anchor, work breakdown, Active obligations, decision log; depth *implementable* or *directional* | Live decisions, open obligations, rulings |
| Companion log | `docs/designs/<slug>-design-log.md` | when a wave's records pass the threshold | The design's review records moved verbatim: gate rounds, fix waves, re-reviews, status and PR rows, seat logs | Review records |
| Plan | `docs/plans/YYYY-MM-DD-<slug>.md` | planning session (writing-plans); lands by the planning PR | Task-level breakdown consumed by SDD; carries its own decision record — its plan-level rulings and pinned facts — and names its gate record by link; indexed in [docs/plans/README.md](plans/README.md), banner-marked when executed, otherwise edited after its merge only as the record freeze allows (§Canonical and pointer sites) | Its plan-level rulings' full text with their evidence |
| Report | `docs/reports/<topic>-report.md` | when an anchor runs or a measurement lands | Certification records, audit results, measured figures with their labels, the dated record of what the merge handed on; frozen at its merge under a banner | Figures |
| Survey | `docs/reports/literature-review.md`; the papers it files under `docs/papers/`, with the queue `REQUESTS.md` | the first sweep; revised per sweep (§III) | The external landscape: standing sections, the papers index, the watchlist, the dated sweep log — a living document, exempt from the record freeze | The external record |
| Runbook | `docs/runbooks/<machine-or-op>.md` | first operational need | Durable how-to-operate; manual or Claude-assisted | Operating rules |
| Handoff | `docs/handoffs/HANDOFF-<name>.md` → `<name>-results.md` | per compute window or guided live session | One-shot execution contract and its outcome; indexed in [docs/handoffs/README.md](handoffs/README.md), banner-marked when executed | The execution record |
| Explainer | `docs/explainers/NN-<topic>.md` + `00-index.md` | when a method deserves a ramp-up | Basics-to-advanced explanation of the methods used; Markdown with LaTeX is canonical, a rendering may be regenerated at milestones; a currency line names the rows that amended its math since | The explanation |
| Skeletons | `docs/skeletons/<document>.md` | at adoption | Each document's house shape — its headings with one line of guidance each, no content — and the session kickoff prompts, which the owner copies into `local/` | — |
| Budgets | `docs/doc-budgets.json` | at adoption (`init --force`) | The item caps, the totals and the baselines (§Budgets) | The budgets |
| SDD ledger | `.superpowers/sdd/<date-slug>/` | by the SDD skill | Execution record; local, untracked (gitignored), never deleted; durable outcomes promoted to the decision log and the report | — |
| Seat definition | `.claude/agents/counsel.md`, `.claude/agents/reviewer.md` | at adoption; amended by PR | Model, effort and charter of each seat an implementation session dispatches (§Model policy) | The charter |

## Canonical and pointer sites

**Canonical sites** hold a claim: the item's report (a measured figure with its label and interval), the design body (a
live decision, in its current wording), the design's decision log (a ruling's rationale; the owner's and counsel's
rulings), the companion log (review records), this document (a rule), AGENTS.md (mechanics), the roadmap (item state,
the queue, reorders), the explainer, the PR description. **Pointer sites** restate: CLAUDE.md (its Status, its
Load-bearing facts, its doc map), the roadmap's status paragraphs, the design header. A pointer site carries a link; two
of them may add a **headline** — the one-sentence result a report's summary states first — copied verbatim with its
label: the roadmap's status paragraph, and CLAUDE.md's Load-bearing facts (one labelled line per durable finding). A
**label** is the claim's population, estimator, uncertainty, registration status and limitations; none is dropped, no
figure is re-derived or rounded, and a pre-registered reading never stands beside a post-hoc one without the label.
CLAUDE.md's Status carries the current state — what is in flight, what is open, the next session — and no figure; a
design header carries neither a figure nor a ruling. Before editing a claim, grep every doc — CLAUDE.md, AGENTS.md,
README, `docs/` (the plans and handoffs reported, edited only as the record freeze allows), the tests' docstrings — for
its distinctive numbers and phrases, list every hit as a site in the task's brief and the PR, and anchor edits by quoted
text, never by line number. A changed rule, decision or ruling is **rewritten in place**: it keeps its id and states
the current rule only — no dated "amended", "superseded" or "overturned" note, no old wording beside the new — and the
change, its date and its reason go in the decision log's row where a suitable log exists (git holds the rest); a log
row is never edited (§I); contradictory live text is a bug a reviewer flags. **The record freeze:** a certification
report is frozen at its merge — one banner under its title, pointer lines at the head of a section a later item
amended, no row edited; a plan or handoff gets a banner and an index row, a plan also the in-place rewrite of a plan
ruling or pinned fact when a ruling of the loop amends the parameter it sets (§Model policy, Records), and a standing
handoff its re-pin (§Handoff economics) — nothing else.

## Model policy

The split keeps the strongest model where its judgment is distinctive — ideation, planning, counsel, review — and hands
the loop itself to the implementation orchestrator. There are two session classes, and the orchestrator's model
follows the class (the binding table): the **planning class** runs ideation and planning (§I; §II stages 1–4) and ends
at its PR; the **implementation class** runs the rest — §II from the plan check; the small-change lane, as the main
session and without a plan; the preparation of a handoff and the pickup of its results, the execution being the
monitor's; and the execution of the research setup handoff (§III).

### The binding table

Each role's model is bound here, and the two seat files' frontmatter carry their own rows.

| Role | Default | Stand-in | Where set |
|---|---|---|---|
| Ideation and planning orchestrator | `fable`, max effort | the strongest model offered — an adoption-time rebinding only | at launch: `claude --model <id> --effort max` |
| Implementation orchestrator | `opus`, max effort | the same | at launch, the same |
| Counsel | `fable`, max effort | the implementation orchestrator's model, its ruling provisional | `.claude/agents/counsel.md` |
| Reviewer | `fable`, max effort | the same | `.claude/agents/reviewer.md` |
| Second whole-branch review | `opus`, max effort: a general-purpose subagent on the reviewer seat's package at stage 6 | none — listed in the PR as not run | named on the dispatch |
| Monitors and guides | `sonnet`, default effort | — (named per dispatch) | named on the dispatch |
| Adversarial gate | the Codex CLI's configured default | the reviewer seat in gate mode | the CLI's own configuration |
| Implementers and task reviewers | the least capable model that carries the role | — (named per dispatch) | named on every dispatch |

A default the environment does not offer is **rebound at adoption**, in this table and the seat files: the seats and
the planning class to the strongest model offered. The two-class split still earns its keep, since its value is the
hard stop at the plan and the fresh context, not only the model. A bound model that fails **at run time** takes its
stand-in by [the gate transitions](#the-gate-transitions), which also say where the ladder ends, and an implementation
session lists in its PR what no seat reviewed. The two cases stay apart. Changing a binding is two edits by PR, the
seat file and this table; no other site names a model. An orchestrator's effort is pinned at launch, since settings
cannot pin max effort, and the owner confirms `/effort` at the session's start — a slash command the session cannot
type. A session asked for work that belongs to the other class says so before it starts.

### The seats

Two subagent types, defined in [.claude/agents/](../.claude/agents/) with the model and effort pinned in their frontmatter and the
file-writing tools removed; Bash stays for checks, and the charter forbids writes and commits through it. The session
itself runs at max effort, so a seat runs at max by inheritance even where a pin were ignored. A seat is called
whenever its trigger fires — the orchestrator does not weigh whether the call is needed — and is dispatched by agent
type with no `model` parameter, which would override the pin.

| Seat | Agent type | Called |
|---|---|---|
| Counsel | `counsel` | When a counsel trigger fires ([Counsel triggers](#counsel-triggers)). |
| Reviewer | `reviewer` | Stage 6, after the final gate returns: the whole-branch review, which also rules on the gate's findings and on every ruling made during the loop; and, in gate mode (its charter's Gate mode), any gate round the gate's tool cannot run. |

**The second whole-branch review and the stand-ins.** The second whole-branch reviewer at stage 6 is a general-purpose
subagent at the binding table's model, briefed with the reviewer charter's Cover and Report sections and given the same
package. A *stand-in* is a general-purpose subagent at the model the binding table's Stand-in column names, given a
seat's charter and package when the seat cannot run; its rulings are provisional. Neither is a seat, and neither is
pinned.

**Rules for a seat call.**

- **A written package.** The question or charter, the evidence paths, what has been ruled out, the rulings at stake
  (the skeletons: [docs/skeletons/counsel-package.md](skeletons/counsel-package.md),
  [docs/skeletons/reviewer-package.md](skeletons/reviewer-package.md)). Seats have tools: they read the repository and
  run their own checks rather than trusting the package.
- **Full budget, or skipped.** A seat is never briefed to economise.
- **Fresh context.** Every call starts from its package. No seat agent is continued from an earlier call: a resumed
  agent re-reads everything it has seen.
- **No advisor.** `/advisor` stays off in implementation sessions: each consult re-reads the whole transcript uncached,
  subagents inherit it, and it cannot read files or run checks.
- **When a seat's model is unavailable** — its allowance cannot carry one full-budget call (by default, under about a
  tenth remaining), or the call fails on limits or dies mid-run (its partial output is evidence for the orchestrator,
  not a ruling) — the stand-in takes the call by the gate transitions. The PR description lists each provisional
  ruling and skipped seat, and the owner decides whether the seat clears them before the merge.

### Counsel triggers

**The three-tier rule.** The orchestrator rules alone on what data settles: a value or fact readable from a committed
file, a committed artefact or a certified reference, under a ruling that already says which source wins (a reviewer's
claim against a committed artefact is not a second source: the artefact settles it); and on a question the plan leaves
open when no later task in the item builds on the answer. Both kinds are recorded as the orchestrator's and go to the
reviewer seat at stage 6. Each of the following goes to counsel when it happens, and the ruling is recorded as
counsel's. Scope and anchors are the owner's (trigger 6).

1. A gate finding no stage-6 seat will see — a re-gate after the whole-branch review, a replacement round — when data
   does not settle it or when the orchestrator would dismiss it at medium severity or higher (the gate tool's scale;
   Important on the seats' Critical, Important and Minor scale). The final gate's findings before the seats go into
   their package with the orchestrator's proposed rulings. A task review's finding belongs to the SDD inner loop, not
   to this trigger.
2. A report or review that contradicts a recorded ruling and data does not settle it; or a question the plan leaves
   open, when the answer sets an interface, a pinned fact, a semantic rule or an acceptance criterion that a later task
   in the item builds on.
3. A disagreement between the orchestrator and a reviewer that survives one round — a round being the finding and the
   orchestrator's written response to it; a re-review that re-raises the finding makes it survive. Counsel's ruling
   ends it. A counsel ruling the reviewer seat overturns at stage 6 is not re-decided by the orchestrator: it goes to
   the owner in the PR as a disagreement between seats.
4. The third fix round on one finding, or the second failed attempt at one root cause.
5. An anchor, certificate or observation that disagrees with the code, when one investigation pass has not found the
   cause.
6. Dropping a task, or changing the item's anchor or an acceptance criterion that changes what the item certifies.
   Counsel first, for a recommendation; then the session stops and flags it — scope is the owner's decision, and the
   go-ahead is an amended plan by a planning PR, gated and merged (§II, the hard stop); a ruling's in-place amendment
   (Records) settles a parameter, never the scope. (Adding work the plan does not cover is not a counsel matter: stop
   and flag it, stage 5.)

One event may fire several triggers: it is one counsel call whose package names each, and the seat log records each. A
gate-mode call is logged as a gate round, with no trigger.

**Records.** During the loop every ruling — the orchestrator's, counsel's, a stand-in's — is written in the SDD ledger
as it is made, with its tier or trigger; at the item's close the durable ones are promoted to the design's decision log
(counsel's marked as counsel's, stand-ins' as provisional), and a ruling that amends a plan parameter is also written
into the plan's decision record as it is made — the plan ruling or pinned fact rewritten in place and marked as whose
ruling it is — so the plan's readers see the current parameter. The **seat log** — every seat call with its seat, its
trigger and what it changed (rulings made, findings by severity), and every provisional ruling and skipped seat — lives
in the PR description and is copied into the design's decision log as the row "Seat log — ‹the session›", so it outlives
the session; it moves to the companion log when the wave closes. The PR's "rulings made in the owner's place" are the
tier-1 rulings on open questions and the orchestrator's dismissals; a tier-1 reading of a value from a committed source
is listed, not reviewed.

### The cap

At most three rounds per gate, counting the gate tool's rounds and their replacement seat rounds on that gate together;
counsel calls and the whole-branch review do not count. Which rounds count, what replaces a dead one and what follows
the cap are [the gate transitions](#the-gate-transitions). A start is wedged when the job logs no task thread within
about four minutes; a healthy run logs it within a second. Past the cap the orchestrator records each change, the
verification it ran and each finding's status in the decision log, and the PR lists anything still open as the
owner's.

### Dispatch

**Other subagents** — implementers, task reviewers, fix waves, research fan-out — take the binding table's last row:
the least capable model that can carry the role, chosen per dispatch and named on it. They inherit the session's
effort. A stuck implementer is retried within those models or goes to counsel (trigger 4), never to an implementer on
the seats' model. Second opinions go through the seats: a counsel package when a trigger fires, the
reviewer seat at stage 6.

**One subagent at a time.** This is the owner's standing gate on parallel dispatch: the owner, not an agent, decides
when work fans out, so running subagents concurrently needs the owner to name that fan-out in the session. The reviewer
seat and the second whole-branch review therefore run one after the other. A gate job is a background job, not a
subagent, and may run beside one.

**Review of this policy.** Any of these reopens the policy at the owner's review: a Critical finding, at the final gate
or the whole-branch review, that traces to an orchestrator ruling a trigger should have sent to counsel; the owner
having to correct course mid-loop; a defect that reached a gate because the orchestrator acted on a subagent's report
without checking it. Recheck at every model release: a release moves both the capability gap and the price.

## Roadmap upkeep

- Status paragraphs change **in the PR that changes the status** (stage 7), replacing the previous one within its
  budget (§Budgets): `**Status: ‹state› ‹date› (PR #N).** ‹one headline with its label› [‹link›]` — one bolded status
  paragraph per item and sub-item entry, its PR and date as stage 7 sets them (the date in the owner's local time); an
  item not started, or an umbrella entry over waves, carries its state alone, with no date or PR
  (`**Status: not started.**`); where the headline with its labels would not fit, the link alone; the narrative it
  replaces lives in the report or the log.
- Discoveries mid-implementation that grow beyond the item's scope become new roadmap entries or parking-lot bullets (a
  sentence and an anchor placeholder are enough to park them) — not silent scope creep, not lost.
- Ordering is dependency-first, leverage-second; a reorder is an ideation-session decision or the owner's ruling. **"Now
  and next" is the only queue:** the current state, one bullet per upcoming session with its class, its gate and its
  spec doc, the owner's open items. Every reorder is a dated line in Standing decisions, written in the PR that makes
  it; a reorder ruled in chat lands in the next PR.
- CLAUDE.md's **Status** paragraph is the merge-time digest: the current state within its budget (§Budgets), the
  queue's next session named and linked to "Now and next". Detail lives behind the doc map's links. The next step is
  named session by session — "the planning session in one session, the owner's review, the implementation session in
  the next" — never as a chain that reads as one session.

## Budgets

The boot files and the design headers have word and line budgets, enforced by one fast check,
`{{INTERPRETER}} -I tools/doc_budgets.py check` over [docs/doc-budgets.json](doc-budgets.json) (`init` writes the baselines for a fresh
repository; [tests/docs/test_doc_budgets.py](../tests/docs/test_doc_budgets.py) wraps the check for a Python host). The same check holds the no-SHA rule at
status sites, that no id a design's Active obligations cites lives only in its companion log, and that every relative
link in CLAUDE.md, AGENTS.md, README.md, the seat charters and `docs/` resolves to a file or a directory — links inside
fenced code ignored, and the dated plans and handoffs held to a pinned list of their known dead links, so that a new one
fails and a resolved one leaves the pin. The lists that grow — CLAUDE.md's doc map and Load-bearing facts, the
roadmap's item entries, parking lot and standing decisions — are capped item by item and never in total, so a new item
needs no raise: a doc-map row, an entry (its `###` or `####` heading and its text up to the next heading) or a
top-level bullet (a line starting `- ` and the lines after it up to the next one, a blank line or a heading), each
within its cap. The rest of those two files, process.md, AGENTS.md and README have totals that leave room to grow, and
the boot path's total is a coarse alarm. Counting rules: words and tokens are whitespace-split tokens, characters are
code points; a header or H1 block is the text after the title line up to the first `## ` heading; a doc-map row is
counted whole; a status paragraph is the run of lines, up to a blank line or a heading, that contains `**Status:`, and
every entry carries exactly one, bolded; lines inside fenced code and lines whose first non-blank character is `|` are
exempt from the line limit; a design header's budget applies once its `active` flag in the JSON is set: from its first
PR for a new design, from the PR that brings an existing header within its budget. The numbers — the item caps, the
rests' totals, the whole-file totals and the baselines, CLAUDE.md's H1 block, the roadmap's status paragraphs, the
design headers, the boot-path total and the line limit — live in the JSON alone; the assistant's memory index, outside
the repository, is checked by hand against the number recorded there. A new design
gets its row in the JSON's `design_headers` in the PR that adds it (the check fails on a design without one). Raising
any number takes a dated row in [docs/process-log.md](process-log.md) and the change to the JSON in the same PR.

## Conventions

Each default below is a choice the rest of this document assumes; beside it stands, where one is given, a common
alternative a host may have chosen. An adopter rewrites a row — the choice and every site that uses it — states the
current choice only, and records the deviation and its reason on a line below.

| The default | The alternative |
|---|---|
| Roadmap *items*, each with its design doc | *phases* and *sub-phases* |
| `docs/designs/` and `docs/reports/` | a flat `docs/`: `docs/<slug>-design.md`, `docs/<slug>-report.md` |
| *Runbooks*, under `docs/runbooks/` | *playbooks* |
| Conventional Commits, `type(scope): subject` | `slug:` prefixes, `<slug>: <subject>` |
| The *planning session* and the *implementation session* | the *plan session* and the implementation session |
| The decision-maker is *the owner*, whatever the title — at work, the service's owner | — |
| The default branch `main` | — |
| The forge GitHub: `gh`, and "PR #N" at the status sites | — |
| A merge commit, `gh pr merge --merge`: stage 8 finds the tip on `origin/main` | A squash or a rebase: stage 8 reads the PR's merged state instead |
| The handoff threshold: about thirty minutes serial | about an hour serial, where runs are long |

<!-- fill: this repository's deviations from the defaults above, one line each with the reason; process.md states the current rule only -->

## History

The provenance of this document — the quoin version it was adopted from — and every dated ruling on it are
[docs/process-log.md](process-log.md).

## Extension — measurement work

*Adopt this extension when the project's plans end in measurements — computations that run for hours, and results
that set a verdict, a gate or a headline figure; otherwise delete it whole.*

When the work is running and monitoring computation rather than writing code, these rules hold; each was paid for
once.

- **Detach anything serially longer than the handoff threshold** (§Conventions): harness-tracked background tasks are
  killed after a couple of hours. Launch detached —
  `nohup <the pinned checkout's interpreter> <the run> > results/<name>.log 2>&1 & disown`, kept awake where the
  machine would sleep — record the PID, and watch the filesystem: the output file landing, the PID gone without output.
  Shorter work may use in-session waits. Design long computations to checkpoint and resume. A detached computation is
  neither a subagent nor a gate job (§Model policy, Dispatch).
- **Never hold an orchestrator session across a long run:** an orchestrator's context re-read on every wake-up at an
  expired cache is the most expensive no-op there is. Write the handoff, end the session, resume fresh (§Handoff
  economics).
- **Gates from bounds, not weak baselines.** An acceptance band or tolerance is derived from a proven bound, an
  independent witness or a termination criterion — never from the numbers of methods already known to be weak. Gate
  only on proven bounds or witnesses independent of the computation (sampling self-checks, independent
  implementations, hashes); label any plausibility prior "prior, not a gate" and say where it came from; derive a
  tolerance from the termination criteria of the things compared (two fixed-point iterations of contraction factor
  `a`, each stopped at a step below `tol`, may differ by `2·tol/(1−a)`); prefer certificates — the stored object
  re-checked against its own defining equation — over comparing two approximations. A handoff's numeric ESCALATE
  conditions obey this rule too.
- **The run window is frozen.** During an official run the executing checkout takes no pulls, no commits, no rebuilds
  and no dependency updates; the run's runbook is the authority, and the monitor escalates instead of improvising.
- **Artefacts.** Measurements land as committed JSON under `results/` with the command that produced them recorded;
  value tables and checkpoints are never committed — their hashes and manifests are.

**Counsel triggers 7–9** join triggers 1–6 (§Model policy, Counsel triggers) where plans end in measurements and the
judgment errors of record are gates and readings, not code. They take precedence over the three-tier rule's
data-settled tier: a verdict or a headline figure is never "what data settles", even when it is the mechanical
comparison of a committed number with a pre-registered gate.

7. A tolerance, threshold, acceptance band or ESCALATE condition that decides a measurement gate, a certificate or an
   anchor comparison, which planned work needs and the plan did not derive — the gates-from-bounds rule applied by a
   second pair of eyes. Counsel derives it from a bound or witness; the orchestrator puts the ruling in the task brief
   or the handoff before the work starts, and an implementer that needs one the brief lacks reports back instead of
   inventing it. An ordinary test tolerance is the implementer's; a gate that changes what the item certifies is
   trigger 6.
8. The reading of a measurement that sets a verdict or a headline figure: a measurement gate's PASS or FAIL (a test
   suite is not a measurement gate), a step called resolved or not, a number bound for a canonical or pointer site.
   Counsel rules on the reading before it is written at any such site; until then the numbers live in `results/` and
   the results doc, where a pre-registered gate script's printout is data, not the claim.
9. A statistical frame or estimator the plan did not fix: pooled against per-group, paired against raw, the interval
   construction, the labelling of a reading as pre-registered or post hoc. A pre-registered frame is never re-specified
   after its result is known without the owner.

Counsel's rulings on these settle parameters of planned work — a tolerance, a threshold, a frame the plan called for
but did not derive — and are recorded as in-place amendments in the plan's decision record; they never widen the plan.
A boundary reading can fire 5, 7, 8 and 9 at once, still one counsel call, and reading a handoff's results is where 8
and 9 fire most. **Trigger 8's publication sites are the union of canonical and pointer sites** (§Canonical and
pointer sites): an approved claim — one a counsel ruling read — may be copied verbatim with its label under that
standing; a changed reading — a new comparison, a new population, a step called resolved — goes to counsel again; the
results document keeps its exception, the numbers living there before counsel rules. A verdict or headline figure
written at a canonical or pointer site without a counsel ruling reopens the model policy at the owner's review (§Model
policy, Dispatch).

## Extension — plans verified in an overlay

*Adopt this extension when plans carry their code as file blocks and the planning session should prove the blocks
before the planning PR; otherwise delete it whole, with [tools/plan_blocks.py](../tools/plan_blocks.py), its tests and
the worktree runbook's section on applying a plan's blocks.*

At stage 3 (§II), the plan's code blocks may be verified before the planning PR by extracting them into a scratch copy
of the repository — the overlay — and running the formatters, the lint, the type checks and the suite there, the
fixtures the plan pins built there by the plan's own tools; nothing from the copy is committed, and the hard stop is
unchanged. A plan's code is a set of file blocks under its task headings — a `**File:**` marker line naming the path
and whether the block is a whole file or a unified diff against `main`, then a fenced block — which
[tools/plan_blocks.py](../tools/plan_blocks.py) lists, extracts, checks, regenerates and verifies. A plan written in an
overlay is generated by the tool's `regen` and proven by its `verify`, so a block that does not apply is a plan defect
to flag, never one to patch by hand. The orchestrator runs `check` on every DONE report, and the design gate's focus
text names the overlay's path. The operating detail is
[docs/runbooks/worktree-sessions.md](runbooks/worktree-sessions.md), its section on applying a plan's blocks.
