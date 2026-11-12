# Paper requests — the owner's fulfilment queue

*Paywalled or bot-walled sources that a survey needs. Agents append rows (status `open`) with
`{{INTERPRETER}} -I tools/lit.py fetch <doi|arxiv-id> --as <name> --queue --needed-by <memo> --why "<the claim it
would settle>"` — only after `fetch` found no open-access copy. The owner obtains the open rows in one sitting, through
a library or from the authors, saves each PDF as `docs/papers/<name>.pdf` under the name the row gives, and flips the
status to `filed`; the next agent session reads the file and adds its row to
[literature-review.md](../reports/literature-review.md) §6. Or the owner drops the PDFs, under whatever names they
came with, into `docs/papers/intake/`: the next agent session identifies each from its first page, files it under the
row's name with its §6 row, flips the status and has the claims that awaited it checked. A row whose "Why" an
already-filed open-access source has settled can be skipped (status `skipped`, with the reason). Never route around a
wall — the rules are in [the literature-search runbook](../runbooks/literature-search.md). The table stays last in
this file: `fetch --queue` appends its rows at the end.*

| # | DOI / URL | Title (authors, venue, year) | Needed by (memo) | Why | Status |
|---|---|---|---|---|---|
