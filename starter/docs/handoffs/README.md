# Handoffs — one-shot contracts and their results

A handoff is the one-shot execution contract of a compute window or a guided live session, `HANDOFF-<name>.md`, in the
five-section shape of [process.md](../process.md) §Handoff economics: Prerequisites, EXECUTE, ESCALATE (do not
improvise), What happens after, and a component manifest pinned to an execution SHA. A monitor session, or the owner,
executes it and writes `<name>-results.md`; the session that owns the question rules from the results. A *standing*
handoff, the research setup, is the exception: every new machine runs it again, by the executor it names, and each
attempt writes its own results file, `<name>-results-<YYYY-MM-DD>.md`. For the dry read that precedes publishing a
handoff, see [process.md](../process.md) §Handoff economics. Helper scripts sit beside their handoff and run against
the committed code alone. Everything stays where it is, since documents and tests cite it by path.

| Handoff | Window | Execution SHA | Results | Ruled or consumed by | Status |
|---|---|---|---|---|---|

**The banner.** Every closed handoff carries one line under its title: *Closed — ran ‹date›; results ‹link› (PR #N);
ruled in ‹report §›. Index: README.md.* A standing handoff takes it only when retired. A new handoff gets a row in the
PR that writes it; the results PR fills *Results* and *Status*, and for a standing handoff each results PR points them
at its newest results file and that file's status line.
