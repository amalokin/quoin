# Contributing to svc

## Tickets and branches

Every change has a ticket, numbered `SVC-<n>`. Cut your branch from `main` and name it for the ticket and a short slug,
for example `svc-214-return-404`.

## Commits

A commit subject reads `SVC-<n>: <subject>`: the ticket, a colon, then a subject in the imperative of at most 72
characters, with no full stop. For example, `SVC-214: Return 404 for unknown paths`. A body is optional and says why.

## Pull requests

Open a pull request against `main` and fill in [the template](.github/PULL_REQUEST_TEMPLATE.md). We squash and merge:
the pull request title becomes the commit subject on `main`, so it takes the same `SVC-<n>: <subject>` form, and the
commits on your branch do not reach `main`.

## Review

[CODEOWNERS](CODEOWNERS) names `@example-org/svc-maintainers`, and a maintainer's approval is needed to merge. `main`
takes no direct pushes. Run `make check` before you push; CI runs it again on every push and pull request, and a red
run blocks the merge.

## Documents

`docs/` is flat: one file for each topic, and decision records in `docs/adr/`. A decision that shapes the service gets
an ADR; [the first one](docs/adr/0001-record-architecture-decisions.md) says how. How to operate the service is in
[docs/runbook.md](docs/runbook.md). Nothing from production goes in a ticket, a pull request or a document: no customer
data, no tokens, no addresses of internal systems.
