# Runbook — literature search and paper filing

*The rule is [process.md](../process.md) §III. How a survey session finds, files and cites papers with
[tools/lit.py](../../tools/lit.py), and how it verifies what it wrote. Every command below runs from the repository
root on any machine with Python ≥ 3.9: the tool is standard-library only. The quotas and spacings it names are typical
observations, not limits; the tool's `--help` is authoritative.*

| | |
|---|---|
| Tool | `{{INTERPRETER}} -I tools/lit.py <verb>` — `search`, `refs`, `cites`, `resolve`, `fetch`, `index`, `budget`, `check` |
| Store | `docs/papers/<name>.pdf` and the index table in [literature-review.md](../reports/literature-review.md) §6; the queue [REQUESTS.md](../papers/REQUESTS.md) |
| Keys | the key file (`LIT_ENV`), mode 600, never in git; set up by [the research setup handoff](../handoffs/HANDOFF-research-setup.md) |
| Budget | OpenAlex's daily credits, 10,000 when observed — a search 10, a list or filter page 1, a single-work lookup 0 |

---

## 1. The stack

**Sources, in the order the tool trusts them.**

- **OpenAlex** — the backbone: search, references, cited-by, open-access locations. It needs a key: keyless calls are
  answered 429 within seconds. The tool sends the key as `Authorization: Bearer …`, never in a URL. Search runs over
  titles and abstracts (`filter=title_and_abstract.search:`): plain `search=` also matches full text and floods the
  results with off-topic papers, at the same 10 credits.
- **Semantic Scholar** — enrichment when its key is set: a second citation graph, TL;DRs, arXiv ids that OpenAlex
  lacks. The key allows **1 request per second, cumulative**; the tool spaces calls at 1.1 s. Even so it answers
  occasional 429s (`TooManyRequestsException`), which the backoff absorbs. An invalid key answers 403.
- **arXiv export API** — keyless. It asks for 3 s between calls, and a burst earns a temporary 429 block; the tool
  spaces arXiv calls at 3 s.
- **Unpaywall** — per-DOI lookups only (`/v2/{doi}?email=…`), the last fallback when a PDF is sought. No key, but every
  call must carry a contact address: the tool sends `LIT_CONTACT_EMAIL` and skips Unpaywall entirely when it is unset.
  Its `/v2/search` endpoint is retired; the tool never calls it. Unpaywall and OpenAlex are run by the same nonprofit
  and largely share their open-access data, so Unpaywall is a backstop, not a second opinion.

**Settings.** The tool reads seven variables from the environment, each with its default. A variable set but empty is
a usage error (exit 2), never its default — an unset shell variable expanded into an assignment is a mistake to see,
not a request for the default.

| Variable | Default | What it names |
|---|---|---|
| `LIT_PROJECT` | the repository's directory name — the main working tree's, from any worktree of it | the project: the User-Agent's product and the `<project>` below; set it where the directory is not named after the project |
| `LIT_PAPERS_DIR` | `docs/papers` | the papers directory (`--papers`) |
| `LIT_REVIEW` | `docs/reports/literature-review.md` | the survey document, whose §6 is the index (`--review`) |
| `LIT_REQUESTS` | `REQUESTS.md` in the papers directory | the queue (`--requests`) |
| `LIT_ENV` | `~/.config/<project>/lit.env` | the key file |
| `LIT_STATE` | `~/.cache/<project>/lit` | the spacing slots (§6 below) |
| `LIT_REPO_URL` | `{{REPO_URL}}` | the repository URL every request's User-Agent names |

**Keys** live in the key file in the `: ${VAR:=value}` form, one line each: `OPENALEX_API_KEY` and `LIT_CONTACT_EMAIL`
required, `SEMANTIC_SCHOLAR_API_KEY` optional. The tool reads the environment first, so a variable already set there
wins; a missing line leaves that source off. Setting them up — the file, each key, the MCP servers — is
[the research setup handoff](../handoffs/HANDOFF-research-setup.md).
`{{INTERPRETER}} -I tools/lit.py check` reports where the setup stands without printing a value — the key file's path,
mode and owner, where each key comes from, one cheap call per configured source — and names the handoff step to resume
at; `budget` proves the OpenAlex key by printing the credits left and the reset.

The contact address also goes into every request's User-Agent (`<project>-lit/1.0 (+<LIT_REPO_URL>; mailto:…)`), the
polite-pool convention of these APIs.

**Optional: the arXiv MCP server** (`uvx arxiv-mcp-server`, at user scope; the handoff's step 6). It converts an arXiv
paper to Markdown for reading. It needs `uv` (without it the server fails with `ENOENT … uvx`), and a session started
before the install picks it up only after `/mcp` → reconnect. A convenience: the Read tool on a filed PDF is the
canonical way to read.

**The repository is the store** — PR-gated and readable by any session — not a reference manager. Revisit that when
the papers outgrow one index table or a second person joins.

## 2. Conventions

- **File names**: `<firstauthor><year>-<slug>.pdf`, lower-case ASCII, hyphens — `tesauro1995-td-gammon`,
  `brown-smith2014-information-relaxations` (two authors), `brown2010a-…` (a second paper of the same author and
  year). `fetch --as` refuses anything else. The slug is a few significant title words; choose ones a reader
  recognises.
- **Open access first.** `fetch` tries, in order: the arXiv copy, OpenAlex's best open-access PDF, Unpaywall's, then
  the landing pages of *open-access* locations, reading their `citation_pdf_url` meta tag once. It never requests a
  publisher page for a closed paper — from a campus network such a page can serve the PDF by IP authentication, which
  is automated library access. **Open access is vouched for a host, not for where it points:** a landing page never
  redirects to another host (a handle resolver — `hdl.handle.net`, `n2t.net`, `purl.org` — may, and the host it lands
  on is then the landing page's), and a page's `citation_pdf_url` is followed only on that page's own host, and only
  when the page is on the host that was asked. A PDF URL that arXiv, OpenAlex or Unpaywall vouched for may redirect to
  another host; the tool accepts only PDF bytes from it. Each refusal prints a `note: … not followed` line (a refused
  redirect: `… redirect off a landing page's host refused`) and `fetch` moves on: a closed route, not one to work
  around. When the automatic routes fail but a search finds an author-hosted copy (a homepage, a university
  repository without a bot wall), file it with `fetch <doi> --as <name> --url <pdf-url>` — provenance is that URL.
  **`--url` is the PDF itself**, on the author's or the repository's host — never a DOI link or a publisher page:
  `fetch` accepts only PDF bytes from it and follows no link from a page (`note: … --url must name the PDF itself`).
  `fetch --url` refuses a DOI link (a usage error, exit 2), as it does a URL urllib cannot send — no scheme, a space
  or a control character, non-ASCII outside the host (percent-encode it; a Unicode host is sent in its ASCII form) —
  before any request, so `--queue` writes no row.
- **Every filed PDF gets its §6 row** in [literature-review.md](../reports/literature-review.md) — `fetch` prints it
  ready-made (`| <name>.pdf | <venue year, pages> | <provenance url> |`); edit the middle column if the metadata is
  thin (e.g. "partial capture", "preprint of …"). A source with no DOI or arXiv id (a proceedings paper without one, a
  technical report) is filed with `fetch --url <pdf-url> --as <name>`, no identifier: nothing is looked up, so its row
  prints `?` as the middle column — fill it in by hand. `{{INTERPRETER}} -I tools/lit.py index` checks both directions
  (a PDF without a row, a row without a PDF) and exits 1 on either; `tests/test_lit.py` runs it on the repository's
  own index.
- **Closed means the queue.** `fetch … --queue --needed-by <memo> --why "<claim it would settle>"` appends a numbered
  row to [REQUESTS.md](../papers/REQUESTS.md) when no open-access copy exists (exit code 3); `--needed-by` names the
  document or section that cites the paper. It refuses to queue when Unpaywall could not be asked — an outage leaves
  "closed" unestablished (its 404 is an answer and queues): `error: not queued — Unpaywall could not be asked (…);
  retry before queueing`, exit 1, nothing written. The "Why" is the claim the paper would settle, so the owner can
  skip rows an open source already settled. The owner fulfils the queue in one sitting; until then the citing text
  marks the gap `[awaiting #n]` and keeps going. The owner may drop the PDFs, under any names, into
  `docs/papers/intake/`: the next session identifies each from its first page, files it under the row's name with its
  §6 row (`index` does not look inside the folder), flips the status, and has every `[awaiting #n]` claim checked
  against the paper (a reader, then §5's verification on the changed text). A copy identical to a filed paper is
  deleted.
- **Exit codes** (for scripts and agents): 0 ok, 1 error or index inconsistency (`check`: not ready), 2 usage, 3
  `fetch` found no open-access PDF.

## 3. The sweep procedure

1. **Seed.** Start from the topic's seed list (a handoff's, or the watchlist's). Resolve every seed before citing it —
   titles from memory are right more often than venues and years:
   `{{INTERPRETER}} -I tools/lit.py search "<title words>" --n 5` and, by identifier,
   `{{INTERPRETER}} -I tools/lit.py resolve <doi>`.
2. **Expand one or two hops.** `{{INTERPRETER}} -I tools/lit.py refs <doi> --n 30` (what it builds on, most cited
   first) and `{{INTERPRETER}} -I tools/lit.py cites <doi> --n 30` (who built on it — the route to recent work and
   surveys); `--source s2` for the second graph. Add `search … --since <year>` for recent work. Prefer surveys and
   tutorials at this stage: one good review replaces ten hops.
3. **Read.** File what the argument hinges on (`fetch`), read it from `docs/papers/` (the Read tool, at most 20 pages
   per call — read the theorem and its conditions, not just the abstract), and note page or section numbers for every
   claim you will attribute.
4. **Write** the findings into [literature-review.md](../reports/literature-review.md)'s standing sections, revised
   in place. Cite primary sources only, each with venue, year, DOI or arXiv id and its `docs/papers/` file or
   `REQUESTS.md #n`.
5. **Verify** (§5) — the survey's gate.
6. **Watchlist and sweep log.** Add what the next sweep should check (venues, authors, arXiv categories, open
   questions) to the watchlist, and one dated row to the sweep log, both in
   [literature-review.md](../reports/literature-review.md).

## 4. Rules — never

- **Never route around a wall.** No shadow libraries (an aggregator that offers one as a connector keeps it off); no
  automated access through a library proxy or a logged-in browser session (library licences prohibit robotic and bulk
  access, and name AI agents; detection blocks the whole campus); no solving or evading bot challenges (a
  proof-of-work page, a browser check) — a walled page means the queue or an author-hosted copy.
- **Never share a paywalled PDF** beyond the people its licence covers: in a repository others can read, file only
  open-access copies and keep paywalled ones out of git.
  <!-- fill: whether this repository is private, and so whether paywalled PDFs may be filed in it; the rule is that a paywalled PDF never reaches anyone its licence does not cover -->
- **Never print, log or commit a key** — not in the repository, a ledger, a commit message or a log. The tool keeps
  keys in headers; never print the key file.
- **When the OpenAlex budget is spent** (`budget` shows 0, or the tool stops on a long Retry-After), stop querying
  until the reset; never create a second account.
- **Never call Unpaywall's retired `/v2/search`**; never cite a paper you have not resolved; never attribute a claim
  you have not found in the source (§5).

## 5. The verification pass (the survey's gate)

A fresh subagent with no context from the sweep gets the survey document and this section:

1. List every citation in the document. For each, resolve it (`{{INTERPRETER}} -I tools/lit.py resolve
   <doi|arxiv-id>`, or `search "<title>"` when the document gives no identifier) and confirm **authors, venue, year
   and title** match the text exactly.
2. For each claim the document attributes to a source, open the filed PDF (or the open-access URL) and find it;
   record the page or section. A claim that cannot be re-found is a mismatch, as is a theorem cited without the
   condition it needs.
3. Report a table: citation · field or claim · what the document says · what the source says · page/section ·
   verdict (match / fix / remove).

The orchestrator fixes or deletes every mismatch — a claim that cannot be re-found in its source leaves the document —
and records the pass (date, citations checked, fixed, removed) in the sweep's row of the sweep log. The independent
witness is the primary source.

## 6. Budget numbers

| Source | Limit | Cost per call | Tool's spacing |
|---|---|---|---|
| OpenAlex | 10,000 credits a day when observed; `budget` shows what is left and the reset | search 10 · list/filter page 1 (refs batches of 50, cites) · single work 0 | none; 429/5xx backoff |
| Semantic Scholar | 1 request/s, cumulative | — | 1.1 s; backoff on sporadic 429s |
| arXiv export API | 3 s between calls | — | 3 s |
| Unpaywall | a contact address required | per DOI | none |

The spacing holds **across processes**: each throttled source has a slot file in the state directory (`LIT_STATE`),
taken under an exclusive lock, so parallel research agents sharing one Semantic Scholar key queue behind each other
instead of tripping its 1 request/s limit together.

A typical topic — ten searches, ten references/cited-by hops, twenty resolves — costs about 120 OpenAlex credits, so
one day's budget covers dozens of topics. Backoff: three attempts, waits of 2 s then 4 s (arXiv 3 s then 6 s) unless
the server sends `Retry-After`; a `Retry-After` beyond 120 s stops the call at once with a message.

## 7. Later (wishes, deliberately not built)

- A local cache of API responses (a re-run of a sweep re-spends credits).
- `fetch` reading author homepages automatically (today: search, then `--url`).
- Citation export (BibTeX) for a public writeup.

## At work

At work the literature is prior art, vendor documentation and the organisation's own records — design documents,
incident reviews, decision records. What transfers: the sweep procedure (§3: seed, expand, read, write, verify, log),
the primary-source rule (cite the document itself, at the version read, never a summary of it) and the verification
pass (§5) as the survey's gate. What is academic: the tool's four sources — OpenAlex, Semantic Scholar, arXiv and
Unpaywall index papers, not a vendor's documentation or an internal wiki — and with them `fetch`'s lookups.

<!-- fill: where this organisation's prior art and records live, and how a sweep cites each; the rule is that a citation names the primary document and the version read -->
