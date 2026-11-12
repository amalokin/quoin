# svc

svc is a small request handler. Its one entry point, `svc.app.handle`, takes a request as a `dict` and returns the
response as a `dict`; today it answers the health probe and returns a 404 for any other path. A server run by the
platform team calls it, and svc has no dependencies of its own.

## Running the checks

`make check` runs the unit tests. It needs Python 3.9 or later and nothing else installed. CI runs the same command on
every push and pull request, and a change merges only when it is green.

## Layout

- `src/svc/` is the handler.
- `tests/` holds its unit tests.
- `docs/adr/` holds the architecture decision records.
- `docs/runbook.md` is the runbook for operating the service: start, stop, health check and rollback.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before your first change. It covers ticket numbers, commit subjects, squash
merges and who reviews.
