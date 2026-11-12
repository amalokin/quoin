#!/usr/bin/env python3
"""Literature search for this repository — stdlib only, runnable as
`python3 -I tools/lit.py <verb>` under any Python >= 3.9.

Sources: OpenAlex (the backbone: search, references, cited-by, OA locations),
Semantic Scholar (enrichment when its key is set: search, references,
citations, TL;DR), the arXiv export API (keyless) and Unpaywall (per-DOI
lookups only; its /v2/search endpoint is retired and never called).

Verbs:
  search "<query>" [--source openalex|s2|arxiv|all] [--n 10] [--since YEAR]
  refs <id> [--source openalex|s2] [--n 50]      references, one hop
  cites <id> [--source openalex|s2] [--n 50]     citing works, one hop
  resolve <doi|arxiv-id>                         best open-access PDF or "closed"
  fetch [<doi|arxiv-id>] --as <name> [--url URL] [--queue --needed-by MEMO --why TEXT]
                                                 file <papers>/<name>.pdf, print its index row
                                                 (with --url, the identifier is optional)
  index                                          the papers directory vs the review's §6
  budget                                         OpenAlex credits left and the reset
  check [--no-network]                           the readiness report: the key file, the
                                                 keys, one cheap call per source; no value
search, refs, cites and resolve take --json. Exit codes: 0 ok, 1 error or
inconsistency (check: not ready), 2 usage, 3 fetch found no open-access PDF
("closed").

Settings come from the environment, read at import, each with its default:
LIT_PROJECT (the repository's directory name — the main working tree's from any
of its worktrees), LIT_PAPERS_DIR (docs/papers), LIT_REVIEW
(docs/reports/literature-review.md), LIT_REQUESTS (REQUESTS.md in the papers
directory), LIT_ENV (the key file, ~/.config/<LIT_PROJECT>/lit.env), LIT_STATE
(the spacing slots, ~/.cache/<LIT_PROJECT>/lit) and LIT_REPO_URL (the repository
URL the User-Agent names). A variable set but empty is a usage error, never its
default.

Keys come from the environment, then from the key file, written in the
`: ${VAR:=value}` form. They travel in request headers only, never to another
origin (a redirect within their own keeps them), and are never printed.
The runbook: docs/runbooks/literature-search.md; the setup:
docs/handoffs/HANDOFF-research-setup.md.
"""

from __future__ import annotations

import argparse
import email.utils
import gzip
import http.client
import json
import os
import re
import stat
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def repository_name(root: Path) -> str:
    """The name of the repository the checkout at `root` belongs to: the default
    project. A main checkout is named by its own directory. A linked worktree's
    `.git` is a file pointing (`gitdir: <path>`) at a directory inside the main
    repository, whose `commondir` file names the repository's own git directory;
    the name is then the main working tree's directory (a bare repository's,
    without its `.git` suffix), so every worktree of one repository shares one
    key file and one spacing directory. Anything else, a submodule, a stale
    pointer, no repository at all, is named by `root`'s own directory. This runs
    at import and never raises."""
    try:
        dotgit = root / ".git"
        if not dotgit.is_file():
            return root.name
        with dotgit.open(encoding="utf-8") as f:
            first = f.readline().strip()
        if not first.startswith("gitdir:"):
            return root.name
        gitdir = (root / first.removeprefix("gitdir:").strip()).resolve()
        commondir = (gitdir / "commondir").read_text(encoding="utf-8").strip()
        common = (gitdir / commondir).resolve()
    except (OSError, ValueError, RuntimeError):
        # Unreadable, not text, a NUL in a path, a symlink loop (a RuntimeError
        # from pathlib before Python 3.13): the checkout's own name, no crash.
        return root.name
    if common.name == ".git":
        return common.parent.name or root.name
    return common.name.removesuffix(".git") or root.name


# The settings, each read from the environment at import with its default. A
# variable set but empty is a usage error: main() refuses it before any work
# (empty_settings), so the default computed for it here is never used.
SETTINGS = (
    "LIT_PROJECT",
    "LIT_PAPERS_DIR",
    "LIT_REVIEW",
    "LIT_REQUESTS",
    "LIT_ENV",
    "LIT_STATE",
    "LIT_REPO_URL",
)


def _setting(name: str, default):
    return os.environ.get(name) or default


PROJECT = _setting("LIT_PROJECT", repository_name(REPO))
PAPERS_DIR = Path(_setting("LIT_PAPERS_DIR", REPO / "docs" / "papers"))
REVIEW_MD = Path(
    _setting("LIT_REVIEW", REPO / "docs" / "reports" / "literature-review.md")
)
REQUESTS_MD = Path(_setting("LIT_REQUESTS", PAPERS_DIR / "REQUESTS.md"))
ENV_FILE = Path(_setting("LIT_ENV", Path.home() / ".config" / PROJECT / "lit.env"))
STATE_DIR = Path(_setting("LIT_STATE", Path.home() / ".cache" / PROJECT / "lit"))
REPO_URL = _setting("LIT_REPO_URL", "{{REPO_URL}}")
CONFIG_KEYS = ("OPENALEX_API_KEY", "SEMANTIC_SCHOLAR_API_KEY", "LIT_CONTACT_EMAIL")
REQUIRED_KEYS = ("OPENALEX_API_KEY", "LIT_CONTACT_EMAIL")

EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_CLOSED = 0, 1, 2, 3


def empty_settings(environ) -> list:
    """The settings `environ` holds set but empty, in SETTINGS order."""
    return [name for name in SETTINGS if environ.get(name) == ""]


class LitError(Exception):
    """A failure reported to the user as one line; never carries a key. `status` is
    the HTTP status when the failure is an HTTP answer."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


# --------------------------------------------------------------------------- config

_ENV_LINE = re.compile(
    r"""^\s*(?::\s*\$\{(?P<a>[A-Za-z_][A-Za-z0-9_]*):=(?P<av>[^}]*)\}"""
    r"""|(?:export\s+)?(?P<b>[A-Za-z_][A-Za-z0-9_]*)=(?P<bv>.*))\s*$"""
)


def parse_env_file(text: str) -> dict:
    """Assignments in the `: ${VAR:=value}` (or `VAR=value`) form; comments ignored."""
    out = {}
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = _ENV_LINE.match(line)
        if not m:
            continue
        name = m.group("a") or m.group("b")
        value = m.group("av") if m.group("a") else m.group("bv")
        out[name] = value.strip().strip("'\"")
    return out


def key_file(environ) -> Path:
    """The key file: LIT_ENV as `environ` holds it, else the one read at import
    (ENV_FILE). Set but empty, LIT_ENV names no file and is refused, never read
    as the default."""
    value = environ.get("LIT_ENV")
    if value == "":
        raise LitError("LIT_ENV is set but empty")
    return ENV_FILE if value is None else Path(value)


def read_key_file(path) -> dict:
    """The key file's assignments; none when it is missing or unreadable."""
    try:
        return parse_env_file(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return {}


def load_config(environ: dict, path: Path | None = None) -> dict:
    """Environment first, then the key file — the shell's `${VAR:=value}`
    semantics, so an empty environment value falls through to the file."""
    from_file = read_key_file(key_file(environ) if path is None else path)
    return {k: (environ.get(k) or from_file.get(k) or None) for k in CONFIG_KEYS}


# --------------------------------------------------------------------------- names

STOPWORDS = frozenset(
    "a an and are as at be by do does for from how in into is its of on or our than that the"
    " these this to toward towards under using via we what why with".split()
)
NAME_RE = re.compile(r"^[a-z]+(?:-[a-z]+)*\d{4}[a-z]?-[a-z0-9]+(?:-[a-z0-9]+)*$")


def ascii_fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def suggest_name(family: str, year, title: str, max_words: int = 4) -> str:
    """`<firstauthor><year>-<slug>`: the first author's family name and the
    title's first significant words, lower-case ASCII (the papers directory's rule)."""
    author = re.sub(r"[^a-z]", "", ascii_fold(family).lower())
    words = re.sub(r"['’]", "", ascii_fold(title).lower())
    words = [w for w in re.split(r"[^a-z0-9]+", words) if w and w not in STOPWORDS]
    return f"{author}{year}-{'-'.join(words[:max_words])}"


def check_name(name: str) -> None:
    if not NAME_RE.match(name):
        raise LitError(
            f"bad file name {name!r}: want <firstauthor><year>-<slug> in lower-case ASCII, "
            "no extension (e.g. brown2010-information-relaxations)"
        )


# --------------------------------------------------------------------------- identifiers

_ARXIV_NEW = r"\d{4}\.\d{4,5}"
_ARXIV_OLD = r"[a-z\-]+(?:\.[A-Z]{2})?/\d{7}"


def parse_id(text: str) -> tuple:
    """Classify a paper identifier: ('doi'|'arxiv'|'openalex'|'s2', normalised value)."""
    s = text.strip()
    m = re.match(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)?(10\.\d{4,9}/\S+)$", s, re.I)
    if m:
        doi = m.group(1).lower()
        ax = re.match(r"^10\.48550/arxiv\.(.+)$", doi)
        if ax:
            return ("arxiv", re.sub(r"v\d+$", "", ax.group(1)))
        return ("doi", doi)
    m = re.match(
        rf"^(?:arxiv:|https?://(?:www\.|export\.)?arxiv\.org/(?:abs|pdf)/)?({_ARXIV_NEW}|{_ARXIV_OLD})(?:v\d+)?(?:\.pdf)?$",
        s,
        re.I,
    )
    if m:
        return ("arxiv", m.group(1))
    m = re.match(r"^(?:https?://openalex\.org/)?(W\d+)$", s, re.I)
    if m:
        return ("openalex", m.group(1).upper())
    if re.match(r"^[0-9a-f]{40}$", s):
        return ("s2", s)
    if re.match(r"^CorpusId:\d+$", s):
        return ("s2", s)
    raise LitError(f"not a DOI, arXiv id, OpenAlex id or Semantic Scholar id: {text!r}")


# --------------------------------------------------------------------------- http

# Minimum spacing per source: Semantic Scholar keys allow 1 request/s cumulative
# (a little margin on top); the arXiv API asks for 3 s between calls.
MIN_INTERVAL = {"s2": 1.1, "arxiv": 3.0}
ATTEMPTS = 3  # on 429 / 5xx: three attempts, then a clear error
BACKOFF_BASE = 2.0  # seconds; doubled per attempt unless Retry-After says otherwise
MAX_WAIT = 120.0  # a longer Retry-After means a spent budget: stop, do not sleep


def user_agent(email: str | None) -> str:
    """The polite pool's User-Agent: the project, its repository URL (LIT_REPO_URL)
    and the contact address. The project's name is cut to the characters a
    product token allows, so a directory name with a space or an accent cannot
    make every request unsendable."""
    product = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_fold(PROJECT)).strip("-")
    contact = f"; mailto:{email}" if email else ""
    return f"{product or 'repository'}-lit/1.0 (+{REPO_URL}{contact})"


class Response:
    def __init__(
        self, status: int, headers: dict, body: bytes, url: str, source: str = "web"
    ):
        self.status, self.headers, self.body, self.url = status, headers, body, url
        self.source = source

    def json(self):
        try:
            return json.loads(self.body)
        except ValueError:  # not JSON (an HTML error page), or not even UTF-8
            raise LitError(
                f"{self.source}: the answer from {self.url} is not JSON"
            ) from None

    def text(self) -> str:
        return self.body.decode("utf-8", "replace")


_UNPACK_ERRORS = (OSError, EOFError, zlib.error)  # gzip.BadGzipFile is an OSError


def _decoded(body: bytes, coding, url: str, source: str) -> bytes:
    """The body before its Content-Encoding — gzip, x-gzip, or deflate (zlib-wrapped,
    else raw) — which urllib leaves undone; other codings pass through. A body that
    still opens with gzip's magic bytes is unpacked once more: some servers (OJS at
    ojs.aaai.org) gzip without saying so, and since nothing declared it, a failure
    there keeps the bytes as sent."""
    coding = (coding or "").strip().lower()
    try:
        if coding in ("gzip", "x-gzip"):
            body = gzip.decompress(body)
        elif coding == "deflate":
            try:
                body = zlib.decompress(body)
            except zlib.error:
                body = zlib.decompress(body, -zlib.MAX_WBITS)
    except _UNPACK_ERRORS:
        raise LitError(
            f"{source}: cannot decode the {coding} answer from {url}"
        ) from None
    if body[:2] == b"\x1f\x8b":
        try:
            body = gzip.decompress(body)
        except _UNPACK_ERRORS:
            pass
    return body


def _sendable(url: str) -> bool:
    """Whether urllib and http.client can send `url` as written: an absolute http(s)
    URL with a host and a readable port, in ASCII, with no control character or
    space — urllib raises ValueError on the rest, http.client UnicodeEncodeError or
    InvalidURL."""
    try:
        parts = urllib.parse.urlsplit(url)
        _ = parts.port  # raises ValueError on a non-numeric or out-of-range port
    except ValueError:  # that, or an unclosed IPv6 bracket
        return False
    return (
        parts.scheme in ("http", "https")
        and bool(parts.hostname)
        and url.isascii()
        and not any(c <= " " or c == "\x7f" for c in url)
    )


def _idna(url: str) -> str:
    """`url` with a Unicode (IDN) host in its ASCII form, the port kept: urllib
    writes the host into the Host header as given, so it must go out encoded.
    Anything else comes back as written — a host the IDNA codec refuses is then
    _sendable's to refuse."""
    try:
        parts = urllib.parse.urlsplit(url)
        host, port = parts.hostname, parts.port
    except ValueError:
        return url
    if not host or host.isascii():
        return url
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return url
    userinfo, at, _ = parts.netloc.rpartition("@")
    netloc = userinfo + at + host + ("" if port is None else f":{port}")
    return urllib.parse.urlunsplit(parts._replace(netloc=netloc))


def _retry_after(value) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, when.timestamp() - time.time())


# Persistent-identifier resolvers: redirecting to the repository is their whole job.
RESOLVER_HOSTS = frozenset({"hdl.handle.net", "n2t.net", "purl.org"})
# The headers keys ride in (OpenAlex's, Semantic Scholar's), as urllib names them
# (str.capitalize()d).
KEY_HEADERS = ("Authorization", "X-api-key")
DEFAULT_PORTS = {"http": 80, "https": 443}


def _origin(parts):
    """A split URL's origin (RFC 6454): scheme, host, port — the scheme's default
    when none is written. None without a host, with an unreadable port, or with
    credentials in the URL (urlsplit and urllib disagree on where `x@host` points),
    so that no two such URLs ever compare equal."""
    try:
        port = parts.port
    except ValueError:
        return None
    if not parts.hostname or "@" in parts.netloc:
        return None
    return (parts.scheme, parts.hostname, port or DEFAULT_PORTS.get(parts.scheme))


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    """urllib's redirect handling with three refusals (an HTTPError with the
    redirect's code): never to a scheme but HTTP(S) (urllib's FTPHandler would
    fetch an ftp:// target), never from HTTPS to plain HTTP, and, for a request
    marked `same_host_only` (a landing page, or a PDF link a page names), never to
    another host — unless the request's host is a persistent-identifier resolver
    (RESOLVER_HOSTS), whose target then counts as the landing host. Keys ride as
    unredirected headers, which the base handler leaves behind; they are handed on
    only within their origin (scheme, host and port — an API moving a path), still
    unredirected, so a key never reaches another origin. A 308 is followed as a
    307 — the same for a GET, the only method this tool sends — since Python 3.9's
    handler knows neither its method nor its code."""

    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_302

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = urllib.parse.urlsplit(req.full_url), urllib.parse.urlsplit(newurl)
        held = getattr(req, "same_host_only", False)
        if new.scheme not in ("http", "https"):
            why = f"redirect to a non-HTTP URL ({new.scheme}:) refused"
        elif old.scheme == "https" and new.scheme != "https":
            why = "redirect from HTTPS to plain HTTP refused"
        elif (
            held and new.hostname != old.hostname and old.hostname not in RESOLVER_HOSTS
        ):
            why = "redirect off a landing page's host refused"
        else:
            moved = super().redirect_request(
                req, fp, 307 if code == 308 else code, msg, headers, newurl
            )
            if moved is not None:
                moved.same_host_only = held
                origin = _origin(old)
                if origin is not None and origin == _origin(new):
                    for name in KEY_HEADERS:
                        if name in req.unredirected_hdrs:
                            moved.add_unredirected_header(
                                name, req.unredirected_hdrs[name]
                            )
            return moved
        raise urllib.error.HTTPError(req.full_url, code, why, headers, fp)


class Http:
    """GET with the repo's User-Agent, per-source spacing and 429/5xx backoff.
    Keys travel in `secret_headers`, set as unredirected headers, which a redirect
    carries only within their origin (SafeRedirect, which every redirect goes
    through). Error messages name the URL only, and no URL this module builds
    carries a key."""

    def __init__(
        self,
        agent: str,
        opener=None,
        sleep=None,
        clock=None,
        timeout: float = 60.0,
        state_dir=None,
    ):
        self.agent = agent
        self.opener = opener or urllib.request.build_opener(SafeRedirect).open
        self.sleep = sleep or time.sleep
        self.clock = clock or time.time  # wall time: comparable across processes
        self.timeout = timeout
        self.state_dir = state_dir  # None: spacing within this process only
        self._last: dict = {}

    def _space(self, source: str) -> None:
        """Wait until `source`'s next slot and reserve it (request starts at least
        MIN_INTERVAL apart). With a state directory the slot is a locked file, so
        concurrent processes — fan-out research agents — queue behind each other.
        The directory is made here, as the first spaced request takes its slot, so
        a run that sends nothing makes nothing; one that cannot be made leaves the
        spacing to this process."""
        gap = MIN_INTERVAL.get(source)
        if gap is None:
            return
        if self.state_dir is not None:
            try:
                Path(self.state_dir).mkdir(parents=True, exist_ok=True)
            except OSError:
                self.state_dir = None
        if self.state_dir is None:
            self._wait(self._last.get(source), gap)
            self._last[source] = self.clock()
            return
        import fcntl  # Unix only; the in-process path above needs nothing

        with open(Path(self.state_dir) / f"{source}.last", "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)  # held across the wait: callers queue up
            f.seek(0)
            try:
                last = float(f.read().strip())
            except ValueError:
                last = None
            self._wait(last, gap)
            f.seek(0)
            f.truncate()
            f.write(repr(self.clock()))

    def _wait(self, last, gap: float) -> None:
        if last is not None:
            # a stale or skewed stamp waits at most one gap
            wait = min(gap, last + gap - self.clock())
            if wait > 0:
                self.sleep(wait)

    def get(
        self,
        url: str,
        headers: dict | None = None,
        source: str = "web",
        secret_headers: dict | None = None,
        same_host_only: bool = False,
    ) -> Response:
        if not _sendable(url):  # checked once: no request, no slot, no retry
            raise LitError(f"{source}: bad URL {url!r}")
        hdrs = {"User-Agent": self.agent}
        hdrs.update(headers or {})
        base = max(BACKOFF_BASE, MIN_INTERVAL.get(source, 0.0))
        for attempt in range(1, ATTEMPTS + 1):
            self._space(source)
            request = urllib.request.Request(url, headers=hdrs)
            for name, value in (secret_headers or {}).items():
                request.add_unredirected_header(name, value)
            request.same_host_only = same_host_only  # SafeRedirect reads it
            try:
                with self.opener(request, timeout=self.timeout) as resp:
                    got = {k.lower(): v for k, v in resp.headers.items()}
                    body = resp.read()
                    final = resp.geturl()  # where redirects led: the answer's URL
                    out = Response(
                        getattr(resp, "status", 200),
                        got,
                        _decoded(body, got.get("content-encoding"), final, source),
                        final,
                        source,
                    )
                return out
            except urllib.error.HTTPError as e:
                # a redirect not followed: the reason says why (SafeRedirect's refusals)
                if 300 <= e.code < 400:
                    # one line: urllib's refusal of a loop or an eleventh hop has three
                    why = " ".join(str(e.reason).split())
                    raise LitError(
                        f"{source}: HTTP {e.code} for {url} — {why}", e.code
                    ) from None
                if e.code != 429 and not 500 <= e.code < 600:
                    raise LitError(
                        f"{source}: HTTP {e.code} for {url}", e.code
                    ) from None
                if attempt == ATTEMPTS:
                    raise LitError(
                        f"{source}: HTTP {e.code} for {url} after {ATTEMPTS} attempts",
                        e.code,
                    ) from None
                wait = _retry_after(e.headers.get("Retry-After") if e.headers else None)
                if wait is None:
                    wait = base * 2 ** (attempt - 1)
                if wait > MAX_WAIT:
                    raise LitError(
                        f"{source}: HTTP {e.code} for {url}; the server asks for a {wait:.0f} s wait — "
                        "a spent budget: stop querying until the reset (`lit.py budget`)",
                        e.code,
                    ) from None
                self.sleep(wait)
            except urllib.error.URLError as e:
                raise LitError(f"{source}: cannot reach {url} ({e.reason})") from None
            except (ValueError, http.client.InvalidURL) as e:
                # Refused before sending — a redirect target or a header the check
                # above cannot see (UnicodeEncodeError is a ValueError; InvalidURL an
                # HTTPException, so this clause comes first): the same request would
                # be refused again. Only the type is named — http.client quotes a
                # refused header value, and a key is one.
                raise LitError(
                    f"{source}: cannot send a request for {url!r}, or for where it"
                    f" redirects ({type(e).__name__})"
                ) from None
            except (OSError, http.client.HTTPException) as e:
                # Sent, but the answer broke off (a timeout, a dropped connection, a
                # truncated body; urllib wraps only the send in URLError): retried
                # like a 5xx.
                if attempt == ATTEMPTS:
                    raise LitError(
                        f"{source}: no complete answer from {url} after {ATTEMPTS}"
                        f" attempts ({e!r})"
                    ) from None
                self.sleep(base * 2 ** (attempt - 1))
        raise AssertionError("unreachable")


# --------------------------------------------------------------------------- records

ARXIV_DOI_PREFIX = "10.48550/arxiv."
_ARXIV_URL = re.compile(r"arxiv\.org/(?:abs|pdf)/(.+?)(?:v\d+)?(?:\.pdf)?$", re.I)
OA_STATUSES = {"GOLD", "GREEN", "HYBRID", "BRONZE", "DIAMOND"}


def _bare_doi(value) -> str | None:
    if not value:
        return None
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.I).lower()


def _arxiv_from_doi(doi: str | None) -> str | None:
    if doi and doi.startswith(ARXIV_DOI_PREFIX):
        return re.sub(r"v\d+$", "", doi[len(ARXIV_DOI_PREFIX) :])
    return None


def _record(**fields) -> dict:
    rec = dict.fromkeys(
        (
            "source",
            "title",
            "year",
            "doi",
            "arxiv",
            "openalex",
            "s2",
            "venue",
            "authors",
            "citations",
            "oa",
            "oa_url",
            "pages",
            "tldr",
        )
    )
    rec.update(fields)
    rec["authors"] = rec["authors"] or []
    rec["oa"] = rec["oa"] or "?"
    return rec


def _pages(biblio) -> str | None:
    first, last = (biblio or {}).get("first_page"), (biblio or {}).get("last_page")
    if first and last and first != last:
        return f"pp. {first}–{last}"
    return f"p. {first}" if first else None


def record_from_openalex(work: dict) -> dict:
    doi = _bare_doi(work.get("doi"))
    arxiv = None
    for loc in work.get("locations") or []:
        for u in (loc.get("landing_page_url"), loc.get("pdf_url")):
            m = _ARXIV_URL.search(u or "")
            if m:
                arxiv = arxiv or m.group(1)
    arxiv = arxiv or _arxiv_from_doi(doi)
    oa = (work.get("open_access") or {}).get("is_oa")
    source = ((work.get("primary_location") or {}).get("source") or {}).get(
        "display_name"
    )
    return _record(
        source="openalex",
        title=work.get("display_name") or work.get("title"),
        year=work.get("publication_year"),
        doi=doi,
        arxiv=arxiv,
        openalex=(work.get("id") or "").rsplit("/", 1)[-1] or None,
        venue=source,
        authors=[
            (a.get("author") or {}).get("display_name")
            for a in work.get("authorships") or []
        ],
        citations=work.get("cited_by_count"),
        oa={True: "oa", False: "closed"}.get(oa, "?"),
        oa_url=(work.get("open_access") or {}).get("oa_url"),
        pages=_pages(work.get("biblio")),
    )


def record_from_s2(paper: dict) -> dict:
    ext = paper.get("externalIds") or {}
    doi = (ext.get("DOI") or "").lower() or None
    arxiv = ext.get("ArXiv") or _arxiv_from_doi(doi)
    pdf = paper.get("openAccessPdf") or {}
    status = (pdf.get("status") or "").upper()
    if arxiv or pdf.get("url") or status in OA_STATUSES:
        oa = "oa"
    elif status == "CLOSED":
        oa = "closed"
    else:
        oa = "?"
    return _record(
        source="s2",
        title=paper.get("title"),
        year=paper.get("year"),
        doi=doi,
        arxiv=arxiv,
        s2=paper.get("paperId"),
        venue=paper.get("venue") or None,
        authors=[a.get("name") for a in paper.get("authors") or []],
        citations=paper.get("citationCount"),
        oa=oa,
        oa_url=pdf.get("url") or None,
        tldr=(paper.get("tldr") or {}).get("text"),
    )


_ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def records_from_arxiv(feed: str) -> list:
    try:
        root = ET.fromstring(feed)
    except ET.ParseError as e:  # an HTML error page instead of the Atom feed
        raise LitError(f"arxiv: the answer is not an Atom feed ({e})") from None
    out = []
    for e in root.findall("a:entry", _ATOM):
        ident = e.findtext("a:id", "", _ATOM)
        if "/api/errors" in ident:
            raise LitError(
                f"arxiv: {' '.join(e.findtext('a:summary', '', _ATOM).split())}"
            )
        m = _ARXIV_URL.search(ident)
        if not m:
            continue
        published = e.findtext("a:published", "", _ATOM)
        doi = e.findtext("arxiv:doi", None, _ATOM)
        out.append(
            _record(
                source="arxiv",
                title=" ".join(e.findtext("a:title", "", _ATOM).split()),
                year=int(published[:4]) if published[:4].isdigit() else None,
                doi=doi.lower() if doi else None,
                arxiv=m.group(1),
                venue="arXiv",
                authors=[
                    a.findtext("a:name", "", _ATOM)
                    for a in e.findall("a:author", _ATOM)
                ],
                oa="oa",
                oa_url=f"https://arxiv.org/pdf/{m.group(1)}",
            )
        )
    return out


def _keys(rec: dict) -> list:
    keys = []
    if rec.get("doi"):
        keys.append(("doi", rec["doi"].lower()))
    if rec.get("arxiv"):
        keys.append(("arxiv", rec["arxiv"].lower()))
    return keys


def dedupe(records: list) -> list:
    """Merge records naming the same DOI or arXiv id: the first one kept wins,
    later ones fill only its missing fields."""
    out, seen = [], {}
    for rec in records:
        hit = next((seen[k] for k in _keys(rec) if k in seen), None)
        if hit is None:
            hit = dict(rec)
            out.append(hit)
        else:
            for field, value in rec.items():
                if hit.get(field) in (None, "", "?", []) and value not in (
                    None,
                    "",
                    "?",
                    [],
                ):
                    hit[field] = value
        for k in _keys(hit):
            seen.setdefault(k, hit)
    return out


def _display_id(rec: dict) -> str:
    doi, arxiv = rec.get("doi"), rec.get("arxiv")
    if doi and not doi.startswith(ARXIV_DOI_PREFIX):
        return doi
    if arxiv:
        return f"arXiv:{arxiv}"
    return doi or rec.get("openalex") or rec.get("s2") or "?"


def _cut(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def format_table(records: list, title_width: int = 80) -> str:
    """One row per record; only the title is cut — an id is pasted into the next
    resolve/refs/cites, so its column widens to the longest (32 at least)."""
    ids = [_display_id(r) for r in records]
    width = max([32] + [len(i) for i in ids])
    lines = [f"{'year':<4}  {'cites':>6}  {'OA':<6}  {'id':<{width}}  title"]
    for r, ident in zip(records, ids):
        year = str(r["year"]) if r.get("year") else "?"
        cites = str(r["citations"]) if r.get("citations") is not None else "?"
        lines.append(
            f"{year:<4}  {cites:>6}  {(r.get('oa') or '?'):<6}  {ident:<{width}}  "
            f"{_cut(r.get('title') or '?', title_width)}"
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- sources

OA_LIST_SELECT = "id,doi,display_name,publication_year,cited_by_count,open_access,primary_location,authorships"
OA_WORK_SELECT = (
    OA_LIST_SELECT + ",best_oa_location,locations,biblio,ids,type,referenced_works"
)
S2_FIELDS = "paperId,externalIds,title,year,venue,citationCount,openAccessPdf,authors"


def _query(params: dict) -> str:
    return urllib.parse.urlencode(
        {k: v for k, v in params.items() if v is not None}, safe=":,|"
    )


def _path_id(value: str) -> str:
    return urllib.parse.quote(value, safe="/:;().")


class OpenAlex:
    BASE = "https://api.openalex.org"

    def __init__(self, http: Http, key: str | None):
        self.http, self.key = http, key

    def get(self, path: str, params: dict) -> Response:
        secret = {"Authorization": f"Bearer {self.key}"} if self.key else {}
        return self.http.get(
            f"{self.BASE}{path}?{_query(params)}",
            source="openalex",
            secret_headers=secret,
        )

    def work(self, ident) -> dict:
        kind, value = parse_id(ident) if isinstance(ident, str) else ident
        if kind == "doi":
            path = f"/works/doi:{_path_id(value)}"
        elif kind == "arxiv":
            path = f"/works/doi:{ARXIV_DOI_PREFIX}{_path_id(value)}"
        elif kind == "openalex":
            path = f"/works/{value}"
        else:
            raise LitError(
                "OpenAlex cannot look up a Semantic Scholar id — use --source s2"
            )
        return self.get(path, {"select": OA_WORK_SELECT}).json()

    def search(self, query: str, n: int, since: int | None) -> list:
        # Titles and abstracts only: `search=` also matches full text, which floods
        # the results with off-topic papers, at the same 10 credits per call.
        filters = ["title_and_abstract.search:" + query.replace(",", " ")]
        if since:
            filters.append(f"from_publication_date:{since}-01-01")
        params = {"filter": ",".join(filters), "per-page": n, "select": OA_LIST_SELECT}
        return [
            record_from_openalex(w)
            for w in self.get("/works", params).json().get("results", [])
        ]

    def refs(self, ident, n: int) -> list:
        ids = [
            r.rsplit("/", 1)[-1] for r in self.work(ident).get("referenced_works") or []
        ]
        recs = []
        for i in range(0, len(ids), 50):
            params = {
                "filter": "openalex:" + "|".join(ids[i : i + 50]),
                "per-page": 50,
                "select": OA_LIST_SELECT,
            }
            recs += [
                record_from_openalex(w)
                for w in self.get("/works", params).json().get("results", [])
            ]
        recs.sort(key=lambda r: -(r["citations"] or 0))
        return recs[:n]

    def cites(self, ident, n: int) -> list:
        wid = record_from_openalex(self.work(ident))["openalex"]
        params = {
            "filter": f"cites:{wid}",
            "sort": "cited_by_count:desc",
            "per-page": n,
            "select": OA_LIST_SELECT,
        }
        return [
            record_from_openalex(w)
            for w in self.get("/works", params).json().get("results", [])
        ]

    def budget(self) -> dict:
        # A singleton lookup costs no credits but carries the rate-limit headers.
        return self.get("/works/W2741809807", {"select": "id"}).headers


class SemanticScholar:
    BASE = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, http: Http, key: str):
        self.http, self.key = http, key

    def get(self, path: str, params: dict) -> Response:
        return self.http.get(
            f"{self.BASE}{path}?{_query(params)}",
            source="s2",
            secret_headers={"x-api-key": self.key},
        )

    @staticmethod
    def pid(ident) -> str:
        kind, value = parse_id(ident) if isinstance(ident, str) else ident
        if kind == "doi":
            return f"DOI:{value}"
        if kind == "arxiv":
            return f"ARXIV:{value}"
        if kind == "s2":
            return value
        raise LitError(
            "Semantic Scholar cannot look up an OpenAlex id — use --source openalex"
        )

    def search(self, query: str, n: int, since: int | None) -> list:
        params = {
            "query": query,
            "limit": min(n, 100),
            "fields": S2_FIELDS + ",tldr",
            "year": f"{since}-" if since else None,
        }
        return [
            record_from_s2(p)
            for p in self.get("/paper/search", params).json().get("data") or []
        ]

    def _hop(self, ident, edge: str, key: str, n: int) -> list:
        data = self.get(
            f"/paper/{_path_id(self.pid(ident))}/{edge}",
            {"limit": 1000, "fields": S2_FIELDS},
        )
        recs = [
            record_from_s2(d[key])
            for d in data.json().get("data") or []
            if (d.get(key) or {}).get("title")
        ]
        recs.sort(key=lambda r: -(r["citations"] or 0))
        return recs[:n]

    def refs(self, ident, n: int) -> list:
        return self._hop(ident, "references", "citedPaper", n)

    def cites(self, ident, n: int) -> list:
        return self._hop(ident, "citations", "citingPaper", n)


class Arxiv:
    BASE = "https://export.arxiv.org/api/query"

    def __init__(self, http: Http):
        self.http = http

    def search(self, query: str, n: int, since: int | None) -> list:
        q = query if ":" in query else " AND ".join(f"all:{t}" for t in query.split())
        if since:
            q += f" AND submittedDate:[{since}01010000 TO 299912312359]"
        params = {
            "search_query": q,
            "start": 0,
            "max_results": n,
            "sortBy": "relevance",
        }
        return records_from_arxiv(
            self.http.get(f"{self.BASE}?{_query(params)}", source="arxiv").text()
        )

    def lookup(self, arxiv_id: str) -> dict | None:
        recs = records_from_arxiv(
            self.http.get(
                f"{self.BASE}?{_query({'id_list': arxiv_id})}", source="arxiv"
            ).text()
        )
        return recs[0] if recs else None


class Unpaywall:
    """Per-DOI lookups only (/v2/{doi}); the /v2/search endpoint is retired."""

    BASE = "https://api.unpaywall.org/v2"

    def __init__(self, http: Http, email_address: str):
        self.http, self.email = http, email_address

    def lookup(self, doi: str) -> dict | None:
        try:
            return self.http.get(
                f"{self.BASE}/{_path_id(doi)}?{_query({'email': self.email})}",
                source="unpaywall",
            ).json()
        except LitError as e:
            if e.status == 404:
                return None
            raise


class Clients:
    def __init__(self, config: dict, http: Http):
        self.http = http
        self.openalex = OpenAlex(http, config.get("OPENALEX_API_KEY"))
        s2_key, contact = config.get("SEMANTIC_SCHOLAR_API_KEY"), config.get(
            "LIT_CONTACT_EMAIL"
        )
        self.s2 = SemanticScholar(http, s2_key) if s2_key else None
        self.arxiv = Arxiv(http)
        self.unpaywall = Unpaywall(http, contact) if contact else None


# --------------------------------------------------------------------------- resolve

_PDF_META = re.compile(
    r"""<meta\s+[^>]*name\s*=\s*["']citation_pdf_url["'][^>]*content\s*=\s*["']([^"']+)["']"""
    r"""|<meta\s+[^>]*content\s*=\s*["']([^"']+)["'][^>]*name\s*=\s*["']citation_pdf_url["']""",
    re.I,
)


_UNSENDABLE = re.compile(r"[^\x21-\x7e]")  # non-ASCII, controls and the space


def _escape(text: str) -> str:
    return _UNSENDABLE.sub(lambda m: urllib.parse.quote(m.group(), safe=""), text)


def pdf_url_from_landing(html: str, base_url: str) -> str | None:
    """The `citation_pdf_url` meta tag repositories and publishers expose for
    indexers, resolved against the page. A link written as an IRI goes out as a
    browser sends it: a Unicode host in its IDNA form, a non-ASCII file name or a
    space percent-encoded as UTF-8 in the path, query and fragment. A link urljoin
    cannot parse (an unclosed IPv6 bracket) raises ValueError."""
    m = _PDF_META.search(html)
    if not m:
        return None
    url = _idna(urllib.parse.urljoin(base_url, (m.group(1) or m.group(2)).strip()))
    if _sendable(url):
        return url
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(
        parts._replace(
            path=_escape(parts.path),
            query=_escape(parts.query),
            fragment=_escape(parts.fragment),
        )
    )


def _candidate(source: str, url: str, license_=None, version=None) -> dict:
    return {"source": source, "url": url, "license": license_, "version": version}


def resolve(ident, clients: Clients, exhaustive: bool = False) -> dict:
    """The best open-access PDF in precedence arXiv → OpenAlex best_oa_location →
    Unpaywall best_oa_location. Unpaywall is asked only when nothing earlier has a
    PDF, unless `exhaustive` (fetch keeps the later candidates as fallbacks).
    Landing pages of open-access locations are reported, never publisher pages.
    Unpaywall is optional: its failure is a warning (stderr and `warnings`), and
    the earlier candidates stand — but the check is then `incomplete` (the failure,
    else None): a "closed" it has not established, which fetch --queue refuses to
    queue. Its 404 is an answer, not a failure. A DOI OpenAlex does not know (404)
    is a warning too, with no record: Unpaywall alone is asked."""
    kind, value = parse_id(ident) if isinstance(ident, str) else ident
    candidates, landing, record, warnings = [], [], None, []
    incomplete = None
    if kind == "arxiv":
        candidates.append(_candidate("arxiv", f"https://arxiv.org/pdf/{value}"))
    elif kind == "doi":
        try:
            work = clients.openalex.work((kind, value))
        except LitError as e:
            if e.status != 404:
                raise
            warnings.append(f"{e} — OpenAlex has no record of this DOI")
            print(f"warning: {warnings[-1]}", file=sys.stderr)
            work = None
        if work is not None:
            record = record_from_openalex(work)
            if record["arxiv"]:
                candidates.append(
                    _candidate("arxiv", f"https://arxiv.org/pdf/{record['arxiv']}")
                )
            best = work.get("best_oa_location") or {}
            if best.get("pdf_url") and not _ARXIV_URL.search(best["pdf_url"]):
                candidates.append(
                    _candidate(
                        "openalex",
                        best["pdf_url"],
                        best.get("license"),
                        best.get("version"),
                    )
                )
            for loc in [best] + list(work.get("locations") or []):
                if loc.get("is_oa") and loc.get("landing_page_url"):
                    landing.append(loc["landing_page_url"])
        if clients.unpaywall and (exhaustive or not candidates):
            try:
                upw = clients.unpaywall.lookup(value) or {}
            except LitError as e:
                incomplete = str(e)
                warnings.append(f"{e} — Unpaywall skipped; the other sources stand")
                print(f"warning: {warnings[-1]}", file=sys.stderr)
                upw = {}
            best = upw.get("best_oa_location") or {}
            if best.get("url_for_pdf"):
                candidates.append(
                    _candidate(
                        "unpaywall",
                        best["url_for_pdf"],
                        best.get("license"),
                        best.get("version"),
                    )
                )
            for loc in [best] + list(upw.get("oa_locations") or []):
                if loc.get("url_for_landing_page") or loc.get("url"):
                    landing.append(loc.get("url_for_landing_page") or loc.get("url"))
    else:
        raise LitError("resolve and fetch take a DOI or an arXiv id")
    seen, unique = set(), []
    for c in candidates:
        if c["url"] not in seen:
            seen.add(c["url"])
            unique.append(c)
    landing = [
        u for u in dict.fromkeys(landing) if "doi.org/" not in u and u not in seen
    ]
    first = unique[0] if unique else {}
    return {
        "status": "pdf" if unique else "closed",
        "url": first.get("url"),
        "source": first.get("source"),
        "license": first.get("license"),
        "version": first.get("version"),
        "candidates": unique,
        "landing": landing,
        "warnings": warnings,
        "incomplete": incomplete,
        "record": record,
    }


# --------------------------------------------------------------------------- filing


def is_pdf(data: bytes) -> bool:
    return data[:4] == b"%PDF"


def publish(target: Path, data: bytes) -> None:
    """File `data` as `target`, never overwriting: the bytes go to a unique temporary
    file beside it, and a hard link publishes them in one atomic step that fails if
    another process filed the name first. The temporary file never outlives the call."""
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(
            dir=target.parent, prefix=f".{target.stem}.", suffix=".part"
        )
        with os.fdopen(fd, "wb") as f:
            umask = os.umask(0)
            os.umask(umask)
            os.fchmod(f.fileno(), 0o666 & ~umask)  # mkstemp's 0600 would be the PDF's
            f.write(data)
        try:
            os.link(tmp, target)
        except FileExistsError:
            raise LitError(
                f"{target} was filed by another process meanwhile — reuse it"
            ) from None
    except OSError as e:  # no such directory, a full disk, no hard links here
        raise LitError(f"cannot file {target}: {e}") from None
    finally:
        if tmp is not None:
            os.unlink(tmp)


def index_row(name: str, venue, year, pages, url: str) -> str:
    what = " ".join(str(x) for x in (venue, year) if x)
    if pages:
        what = f"{what}, {pages}" if what else pages
    return f"| {name}.pdf | {what or '?'} | {url} |"


def _cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _family(name: str) -> str:
    return name.split()[-1] if name and name.split() else name


def requests_row(
    number: int,
    link: str,
    title: str,
    authors: list,
    venue,
    year,
    name: str,
    needed_by: str,
    why: str,
) -> str:
    fam = [_family(a) for a in authors if a]
    who = ", ".join(fam) if len(fam) <= 3 else f"{fam[0]} et al."
    where = ", ".join(str(x) for x in (venue, year) if x)
    paren = "; ".join(x for x in (who, where) if x)
    cite = f"{title} ({paren})" if paren else str(title)
    return f"| {number} | {link} | {_cell(cite)} → `{name}.pdf` | {_cell(needed_by)} | {_cell(why)} | open |"


def next_request_number(text: str) -> int:
    nums = [int(m.group(1)) for m in re.finditer(r"^\|\s*(\d+)\s*\|", text, re.M)]
    return max(nums, default=0) + 1


def append_request(path: Path, build_row) -> int:
    """Number and append one queue row under an exclusive lock, so concurrent
    agents never claim the same number. `build_row(number)` returns the row. The
    file must exist — it carries the table header — so it is never created."""
    import fcntl

    try:
        f = open(path, "r+", encoding="utf-8")
    except FileNotFoundError:
        raise LitError(
            f"{path} does not exist — the queue file carries the table header"
        ) from None
    except OSError as e:  # read-only, a directory
        raise LitError(f"cannot open {path}: {e}") from None
    with f:
        fcntl.flock(f, fcntl.LOCK_EX)
        text = f.read()
        number = next_request_number(text)
        f.seek(0, os.SEEK_END)
        if text and not text.endswith("\n"):
            f.write("\n")
        f.write(build_row(number) + "\n")
    return number


def index_entries(review_text: str) -> list:
    """File names in the first column of the review's §6 table."""
    names, in_six = [], False
    for line in review_text.splitlines():
        if line.startswith("## "):
            in_six = bool(re.match(r"^##\s+6\.", line))
        elif in_six and line.startswith("|"):
            cell = line.strip().strip("|").split("|")[0].strip().strip("`")
            if cell.lower().endswith(".pdf"):
                names.append(cell)
    return names


def _read_review(path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:  # missing, unreadable, not UTF-8
        raise LitError(f"cannot read {path}: {e}") from None


def check_index(papers_dir: Path, review_md: Path) -> tuple:
    files = sorted(p.name for p in Path(papers_dir).glob("*.pdf"))
    rows = index_entries(_read_review(review_md))
    return [f for f in files if f not in rows], [r for r in rows if r not in files]


# --------------------------------------------------------------------------- verbs


def _emit(records: list, as_json: bool) -> None:
    if as_json:
        print(json.dumps(records, ensure_ascii=False, indent=1))
    else:
        print(format_table(records))


def _need_s2(clients: Clients) -> SemanticScholar:
    if clients.s2 is None:
        raise LitError(
            "SEMANTIC_SCHOLAR_API_KEY is not set (the environment or the key file;"
            " `lit.py check` reports both)"
        )
    return clients.s2


def cmd_search(args, clients: Clients) -> int:
    sources = ["openalex", "s2", "arxiv"] if args.source == "all" else [args.source]
    records = []
    for source in sources:
        if source == "s2" and clients.s2 is None and args.source == "all":
            print(
                "note: SEMANTIC_SCHOLAR_API_KEY not set — Semantic Scholar skipped",
                file=sys.stderr,
            )
            continue
        client = {"openalex": clients.openalex, "arxiv": clients.arxiv}.get(
            source
        ) or _need_s2(clients)
        records += client.search(args.query, args.n, args.since)
    _emit(dedupe(records) if args.source == "all" else records, args.json)
    return EXIT_OK


def cmd_hop(args, clients: Clients) -> int:
    client = clients.openalex if args.source == "openalex" else _need_s2(clients)
    records = (
        client.refs(args.id, args.n)
        if args.verb == "refs"
        else client.cites(args.id, args.n)
    )
    _emit(records, args.json)
    return EXIT_OK


def cmd_resolve(args, clients: Clients) -> int:
    res = resolve(args.id, clients)
    if args.json:
        print(
            json.dumps(
                {k: v for k, v in res.items() if k != "record"},
                ensure_ascii=False,
                indent=1,
            )
        )
        return EXIT_OK
    if res["status"] == "pdf":
        print(f"pdf  {res['url']}")
        print(
            f"source: {res['source']}; licence: {res['license'] or '?'}; version: {res['version'] or '?'}"
        )
    else:
        print("closed")
    for url in res["landing"]:
        print(f"landing page (no direct PDF): {url}")
    return EXIT_OK


def _host(url: str):
    try:
        return urllib.parse.urlsplit(url).hostname
    except ValueError:  # an unclosed IPv6 bracket: no host to compare
        return None


# arXiv asks one address for 3 s between requests, its PDFs included: a download
# from its hosts takes the API's slot, so parallel agents queue there too.
ARXIV_HOSTS = frozenset({"arxiv.org", "export.arxiv.org", "www.arxiv.org"})


def _slot(url: str) -> str:
    """The spacing source a download from `url` takes (MIN_INTERVAL)."""
    return "arxiv" if _host(url) in ARXIV_HOSTS else "web"


def _try_pdf(
    http: Http, url: str, tried: set, landing: bool = False, pdf_only: bool = False
):
    """Download `url` and accept a PDF. Open access was vouched for `url`'s host,
    not for wherever it points, so an HTML page's citation_pdf_url is followed once
    and only when the page is on that host (or is a handle resolver's target) and
    the link is on the page's own host; `pdf_only` (`--url`, which names the PDF
    itself) follows no link at all. A landing page (`landing`) and the link are
    requested same-host-only (SafeRedirect); a vouched PDF URL may redirect
    anywhere, but a page it lands on elsewhere is not read for links. A Unicode
    host is put in its IDNA form first, so every host compared is in one form."""
    url = _idna(url)
    if url in tried:
        return None
    tried.add(url)
    try:
        resp = http.get(url, source=_slot(url), same_host_only=landing)
    except LitError as e:
        print(f"note: {e}", file=sys.stderr)
        return None
    if is_pdf(resp.body):
        return url, resp.body
    if pdf_only:
        print(
            f"note: {url} is not a PDF — --url must name the PDF itself",
            file=sys.stderr,
        )
        return None
    page = resp.url or url
    try:
        inner = pdf_url_from_landing(resp.text(), page)
    except ValueError:  # a link that is no URL costs this page only
        print(f"note: {page} names a PDF link that cannot be parsed", file=sys.stderr)
        return None
    if not inner or inner in tried:
        return None
    if _host(page) != _host(url) and _host(url) not in RESOLVER_HOSTS:
        print(
            f"note: {url} redirected to another host, whose page names a PDF"
            " — not followed",
            file=sys.stderr,
        )
        return None
    if _host(inner) != _host(page):
        print(
            f"note: {page} names its PDF on another host — not followed",
            file=sys.stderr,
        )
        return None
    tried.add(inner)
    try:
        resp2 = http.get(inner, source=_slot(inner), same_host_only=True)
    except LitError as e:
        print(f"note: {e}", file=sys.stderr)
        return None
    if is_pdf(resp2.body):
        return inner, resp2.body
    return None


def _metadata(ident, clients: Clients) -> dict | None:
    kind, value = ident
    try:
        if kind == "arxiv":
            return clients.arxiv.lookup(value)
        return record_from_openalex(clients.openalex.work(ident))
    except LitError as e:
        print(f"note: no metadata ({e})", file=sys.stderr)
        return None


def cmd_fetch(args, clients: Clients) -> int:
    check_name(args.name)
    target = Path(args.papers) / f"{args.name}.pdf"
    if target.exists():
        raise LitError(f"{target} exists — refusing to overwrite")
    if args.queue and not (args.needed_by and args.why):
        raise LitError(
            "--queue needs --needed-by <memo> and --why <the claim the paper would settle>"
        )
    if args.queue and args.id is None:
        raise LitError(
            "--queue needs a DOI or arXiv id: the queue row links the paper by it"
        )
    # none: --url alone, no lookup ("" is refused as a usage error before this)
    ident = parse_id(args.id) if args.id is not None else None
    if ident and ident[0] not in ("doi", "arxiv"):
        raise LitError("fetch takes a DOI or an arXiv id")
    incomplete = None  # why the check fell short (Unpaywall unanswered), if it did
    if args.url:
        record, candidates, landing = (
            _metadata(ident, clients) if ident else None,
            [_candidate("url", args.url)],
            [],
        )
    else:
        res = resolve(ident, clients, exhaustive=True)
        # a DOI's record is OpenAlex's, already asked (None: OpenAlex lacks it)
        record = res["record"] if ident[0] == "doi" else _metadata(ident, clients)
        candidates, landing = res["candidates"], res["landing"]
        incomplete = res["incomplete"]
    tried, got, via = set(), None, None
    for c in candidates:
        got = _try_pdf(clients.http, c["url"], tried, pdf_only=c["source"] == "url")
        if got:
            via = c["source"]
            break
    for url in [] if got else landing:
        got = _try_pdf(clients.http, url, tried, landing=True)
        if got:
            via = "landing page"
            break
    record = record or {}
    if got:
        url, body = got
        publish(target, body)
        print(f"filed {target} ({len(body):,} bytes, via {via}: {url})")
        print(f"index row for {Path(args.review).name} §6:")
        print(
            index_row(
                args.name,
                record.get("venue"),
                record.get("year"),
                record.get("pages"),
                url,
            )
        )
        return EXIT_OK
    print("closed — no open-access PDF found; nothing written")
    for url in landing:
        print(f"landing page (no direct PDF): {url}")
    if args.queue and incomplete:  # a row needs a complete check
        print(
            f"error: not queued — Unpaywall could not be asked ({incomplete});"
            " retry before queueing",
            file=sys.stderr,
        )
        return EXIT_ERROR
    if args.queue:
        req = Path(args.requests)
        link = (
            f"https://doi.org/{ident[1]}"
            if ident[0] == "doi"
            else f"https://arxiv.org/abs/{ident[1]}"
        )
        number = append_request(
            req,
            lambda n: requests_row(
                n,
                link,
                record.get("title") or args.id,
                record.get("authors") or [],
                record.get("venue"),
                record.get("year"),
                args.name,
                args.needed_by,
                args.why,
            ),
        )
        print(f"queued as #{number} in {req}")
    return EXIT_CLOSED


def cmd_index(args, clients: Clients) -> int:
    unindexed, missing = check_index(Path(args.papers), Path(args.review))
    for f in unindexed:
        print(f"unindexed (in {args.papers}, no §6 row): {f}")
    for f in missing:
        print(f"missing (§6 row, no file): {f}")
    if unindexed or missing:
        return EXIT_ERROR
    rows = index_entries(_read_review(args.review))
    print(f"index consistent: {len(rows)} files")
    return EXIT_OK


def cmd_budget(args, clients: Clients) -> int:
    h = clients.openalex.budget()
    remaining, reset = h.get("x-ratelimit-remaining", "?"), h.get(
        "x-ratelimit-reset", "?"
    )
    hours = f" ≈ {int(reset) / 3600:.1f} h" if str(reset).isdigit() else ""
    print(
        f"OpenAlex credits remaining: {remaining} of {h.get('x-ratelimit-limit', '?')}; resets in {reset} s{hours}"
    )
    print(
        "costs: a singleton lookup 0, a list/filter page 1, a search 10 (as measured;"
        " OpenAlex may change them)"
    )
    return EXIT_OK


# --------------------------------------------------------------------------- check

# The steps of the research setup handoff (docs/handoffs/HANDOFF-research-setup.md)
# check names when it fails: the first failing one is where the handoff resumes.
STEPS = {
    1: "the key file",
    2: "the OpenAlex key",
    3: "the Semantic Scholar key",
    4: "the contact address",
    5: "a failing source",
}
KEY_STEPS = {"OPENALEX_API_KEY": 2, "SEMANTIC_SCHOLAR_API_KEY": 3, "LIT_CONTACT_EMAIL": 4}
KEY_STATES = {
    "file": "set (file)",
    "environment": "set (environment only, not persisted)",
    None: "unset",
}
CHECK_QUERY = "survey"  # the smallest search: this query, one result
CHECK_DOI = "10.1287/opre.1090.0796"  # a DOI Unpaywall knows, for its one lookup
WITHHELD = "<withheld>"


def key_file_line(path: Path) -> tuple:
    """check's line for the key file, and whether the file passes: a regular file
    with mode 600, owned by the user."""
    try:
        info = path.stat()
    except OSError:
        info = None
    if info is None or not stat.S_ISREG(info.st_mode):
        return f"key file: {path}: missing", False
    mode, uid = stat.S_IMODE(info.st_mode), info.st_uid
    mode_ok, owner_ok = mode == 0o600, uid == os.getuid()
    parts = (
        "present",
        "mode 600" if mode_ok else f"mode {mode:o} (insecure)",
        "owner ok" if owner_ok else f"owner {uid} (not the user)",
    )
    return f"key file: {path}: {'; '.join(parts)}", mode_ok and owner_ok


def key_sources(environ, in_file: dict) -> dict:
    """Where each key comes from: "file" when the key file holds it, whatever the
    environment holds, since the file survives the shell; "environment" when only
    the environment does; None when neither. An empty value counts as none, as
    load_config reads it."""
    return {
        key: "file" if in_file.get(key) else "environment" if environ.get(key) else None
        for key in CONFIG_KEYS
    }


def withheld(text: str, values) -> str:
    """`text` with each value replaced by WITHHELD, as written and as a URL's path
    or query carries it."""
    for value in values:
        if value:
            for form in (
                value,
                urllib.parse.quote(value, safe=""),
                urllib.parse.quote_plus(value, safe=":,|"),
            ):
                text = text.replace(form, WITHHELD)
    return text


def _probes(clients: Clients) -> list:
    """check's sources in order, each (its name, its one live and cheap call — None
    when the source is not configured — and what an unconfigured one prints):
    OpenAlex's budget call, the smallest search on Semantic Scholar and on arXiv,
    and one Unpaywall lookup."""
    oa, s2, upw = clients.openalex, clients.s2, clients.unpaywall
    return [
        ("openalex", oa.budget if oa.key else None, "unconfigured"),
        (
            "semantic-scholar",
            (lambda: s2.search(CHECK_QUERY, 1, None)) if s2 else None,
            "unconfigured (optional)",
        ),
        ("arxiv", lambda: clients.arxiv.search(CHECK_QUERY, 1, None), None),
        ("unpaywall", (lambda: upw.lookup(CHECK_DOI)) if upw else None, "unconfigured"),
    ]


def cmd_check(args, clients: Clients) -> int:
    """The readiness report the research setup handoff runs first: one line per
    component and never a value, then, when anything fails, the handoff's step
    to resume at — the first failing one. A source's call that raises anything
    but the tool's own error, an answer of the wrong shape, is reported by the
    exception's type alone, so no line is lost to a traceback and no message can
    carry a value. Ready (exit 0): the key file present, mode 600 and the
    user's; both required keys set from it; every set key from it; and, unless
    --no-network, every configured source answering. A key in both the file and
    the environment counts as the file's: it is persisted, though this run sends
    the environment's value — so the handoff runs its step 5, this check in a
    fresh shell, which sends the file's own, on every pass, a clean one
    included."""
    environ = args.environ
    path = key_file(environ)
    line, file_ok = key_file_line(path)
    print(line)
    failing = [] if file_ok else [1]
    in_file = read_key_file(path)
    for key, where in key_sources(environ, in_file).items():
        need = "required" if key in REQUIRED_KEYS else "optional"
        print(f"{key} ({need}): {KEY_STATES[where]}")
        if where == "environment" or (where is None and key in REQUIRED_KEYS):
            failing.append(KEY_STEPS[key])
    if not args.no_network:
        values = [environ.get(k) for k in CONFIG_KEYS]
        values += [in_file.get(k) for k in CONFIG_KEYS]
        values += [clients.openalex.key, getattr(clients.s2, "key", None)]
        values += [getattr(clients.unpaywall, "email", None)]
        for name, call, unconfigured in _probes(clients):
            if call is None:
                print(f"{name}: {unconfigured}")
                continue
            try:
                call()
            except LitError as e:
                reason = re.sub(r"^(?:openalex|s2|arxiv|unpaywall): ", "", str(e))
                print(f"{name}: failing: {withheld(reason, values)}")
                failing.append(5)
            except Exception as e:  # an answer of the wrong shape: its type alone
                print(f"{name}: failing: {type(e).__name__}")
                failing.append(5)
            else:
                print(f"{name}: ok")
    if failing:
        step = min(failing)
        print(f"resume at step {step}: {STEPS[step]}")
        return EXIT_ERROR
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lit.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--papers",
        default=str(PAPERS_DIR),
        help="the papers directory (default: LIT_PAPERS_DIR, else docs/papers)",
    )
    p.add_argument(
        "--review",
        default=str(REVIEW_MD),
        help="the file holding the §6 index (default: LIT_REVIEW, else"
        " docs/reports/literature-review.md)",
    )
    p.add_argument(
        "--requests",
        default=str(REQUESTS_MD),
        help="the request queue (default: LIT_REQUESTS, else REQUESTS.md in the papers"
        " directory)",
    )
    sub = p.add_subparsers(dest="verb", required=True)

    s = sub.add_parser("search", help="search one source or all of them")
    s.add_argument("query")
    s.add_argument(
        "--source", choices=["openalex", "s2", "arxiv", "all"], default="openalex"
    )
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--since", type=int)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_search)

    for verb, text in (
        ("refs", "the works it cites"),
        ("cites", "the works citing it"),
    ):
        h = sub.add_parser(verb, help=f"{text}, most cited first")
        h.add_argument("id")
        h.add_argument("--source", choices=["openalex", "s2"], default="openalex")
        h.add_argument("--n", type=int, default=50)
        h.add_argument("--json", action="store_true")
        h.set_defaults(func=cmd_hop)

    r = sub.add_parser("resolve", help="the best open-access PDF URL, or closed")
    r.add_argument("id")
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=cmd_resolve)

    f = sub.add_parser(
        "fetch", help="file the open-access PDF as <papers>/<name>.pdf"
    )
    f.add_argument(
        "id", nargs="?", help="a DOI or arXiv id (optional with --url: no lookup)"
    )
    f.add_argument(
        "--as", dest="name", required=True, help="<firstauthor><year>-<slug>"
    )
    f.add_argument(
        "--url",
        help="download this PDF instead (e.g. an author-hosted copy found by search)",
    )
    f.add_argument(
        "--queue", action="store_true", help="if closed, append a row to REQUESTS.md"
    )
    f.add_argument("--needed-by", help="the memo that needs it (with --queue)")
    f.add_argument("--why", help="the claim the paper would settle (with --queue)")
    f.set_defaults(func=cmd_fetch, verb_parser=f)  # its usage line, for its errors

    sub.add_parser(
        "index", help="the papers directory against the review's §6"
    ).set_defaults(func=cmd_index)
    sub.add_parser("budget", help="OpenAlex credits left").set_defaults(func=cmd_budget)

    c = sub.add_parser(
        "check",
        help="the readiness report: the key file, the keys, one cheap call per source;"
        " no value printed",
    )
    c.add_argument(
        "--no-network", action="store_true", help="the key file and the keys only"
    )
    c.set_defaults(func=cmd_check)
    return p


DOI_HOSTS = frozenset({"doi.org", "dx.doi.org"})


def check_fetch_usage(args) -> None:
    """fetch's rules argparse cannot state; a breach exits 2 with fetch's usage.
    A Unicode host in --url is put in its IDNA form first, not refused."""
    error = args.verb_parser.error
    if args.id is not None and not args.id.strip():
        error("an empty identifier: give a DOI or arXiv id, or none with --url")
    if args.url is not None:
        args.url = _idna(args.url)
    if args.url is not None and not _sendable(args.url):  # nothing asked, no row
        error(
            f"bad --url {args.url!r}: an absolute http(s) URL with a host and no"
            " space, control character or non-ASCII outside the host (percent-encode"
            " them)"
        )
    if not (args.id or args.url):
        error("fetch needs a DOI or arXiv id, or --url <pdf-url>")
    if args.url and _host(args.url) in DOI_HOSTS:
        error(
            "--url names the PDF itself, never a DOI link — give the DOI as the"
            " identifier"
        )


def main(
    argv=None, *, config=None, opener=None, sleep=None, clock=None, state_dir=None
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.environ = dict(os.environ)  # what load_config and check read
    empty = empty_settings(args.environ)
    if empty:  # a usage error, before anything is read, asked or written
        for name in empty:
            print(f"error: {name} is set but empty", file=sys.stderr)
        return EXIT_USAGE
    if args.verb == "fetch":
        check_fetch_usage(args)  # exit 2
    if config is None:
        config = load_config(args.environ)
    http = Http(
        user_agent(config.get("LIT_CONTACT_EMAIL")),
        opener=opener,
        sleep=sleep,
        clock=clock,
        state_dir=state_dir,
    )
    try:
        return args.func(args, Clients(config, http))
    except LitError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_ERROR


def default_state_dir():
    """Where the cross-process spacing slots live (STATE_DIR: LIT_STATE, else
    ~/.cache/<LIT_PROJECT>/lit). Nothing is made here: Http makes the directory
    when a spaced request first takes its slot. None when a setting is set but
    empty, a run main() refuses before any request."""
    if empty_settings(os.environ):
        return None
    return STATE_DIR


if __name__ == "__main__":
    sys.exit(main(state_dir=default_state_dir()))
