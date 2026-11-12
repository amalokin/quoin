"""Tests for tools/lit.py — the stdlib-only literature-search CLI.

Offline only: every network response is a recorded real API response
(tests/fixtures/lit/; fixtures/README.md gives the capture date, the services
each response came from and every edit made to a recording) served by a
stand-in for urllib's opener. The module is loaded from its path, as
`python3 -I tools/lit.py` runs it; the `index` tests run it under the literal
/usr/bin/python3 so the stdlib-only contract is enforced.
"""

from __future__ import annotations

import argparse
import ast
import copy
import email.message
import gzip
import hashlib
import http.client
import importlib.util
import io
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.response
import zlib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
LIT_PATH = REPO / "tools" / "lit.py"
FIX = Path(__file__).resolve().parent / "fixtures" / "lit"
PY = "/usr/bin/python3"

_spec = importlib.util.spec_from_file_location("lit", LIT_PATH)
lit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lit)

# The placeholder contact address, built from parts so that no line of this file
# has the shape of an address.
CONTACT = "owner" + "@" + "example.org"
KEYS = {
    "OPENALEX_API_KEY": "oa-secret-0123",
    "SEMANTIC_SCHOLAR_API_KEY": "s2k-secret-4567",
    "LIT_CONTACT_EMAIL": CONTACT,
}


def fixture(name):
    return (FIX / name).read_bytes()


def fixture_json(name):
    return json.loads(fixture(name))


def ok(body, headers=None, final_url=None):
    """A 200; `final_url` is where redirects led (the response's geturl())."""
    if not isinstance(body, bytes):
        body = json.dumps(body).encode()
    return (200, headers or {}, body) + ((final_url,) if final_url else ())


def fail(code, headers=None):
    return (code, headers or {}, b'{"error": "x"}')


def broken(exc):
    """A 200 whose body never arrives whole: reading it raises `exc`."""
    return (200, {}, exc)


def raises(exc):
    """A route whose request fails before any answer (urllib's getresponse())."""

    def route():
        raise exc

    return route


def gzipped(answer, coding="gzip"):
    """The answer as a compressing server sends it: the body gzip-compressed and
    `coding` its Content-Encoding (None: undeclared, as OJS sends it)."""
    status, headers, body, *final = answer
    headers = {**headers, "Content-Encoding": coding} if coding else dict(headers)
    return (status, headers, gzip.compress(body), *final)


def deflated(answer, raw=False):
    """The answer deflate-compressed: zlib-wrapped, or `raw` as some servers send it."""
    status, headers, body, *final = answer
    packer = zlib.compressobj(wbits=-zlib.MAX_WBITS if raw else zlib.MAX_WBITS)
    body = packer.compress(body) + packer.flush()
    return (status, {**headers, "Content-Encoding": "deflate"}, body, *final)


class FakeResponse:
    """The parts of http.client.HTTPResponse that urllib callers use."""

    def __init__(self, status, headers, body, url):
        self.status = status
        self.headers = email.message.Message()
        for k, v in headers.items():
            self.headers[k] = v
        self._body = body
        self._url = url

    def read(self):
        if isinstance(self._body, BaseException):
            raise self._body
        return self._body

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeWeb:
    """Stands in for urllib.request.urlopen: routes are (url substring, response
    or list of responses consumed in order); unmatched URLs fail the test. A
    response is (status, headers, body[, final URL]) or a callable returning one,
    run when the request arrives."""

    def __init__(self, routes, clock=None):
        self.routes = [(k, list(v) if isinstance(v, list) else v) for k, v in routes]
        self.requests = []
        self.times = []
        self.clock = clock

    def __call__(self, request, timeout=None):
        url = request.full_url
        self.requests.append(request)
        if self.clock is not None:
            self.times.append(self.clock.now)
        for key, resp in self.routes:
            if key in url:
                if isinstance(resp, list):
                    resp = resp.pop(0) if len(resp) > 1 else resp[0]
                if callable(resp):
                    resp = resp()
                status, headers, body, *final = resp
                if status >= 400:
                    hdrs = email.message.Message()
                    for k, v in headers.items():
                        hdrs[k] = v
                    raise urllib.error.HTTPError(
                        url, status, "err", hdrs, io.BytesIO(body)
                    )
                return FakeResponse(status, headers, body, final[0] if final else url)
        raise AssertionError(f"unexpected request: {url}")

    def urls(self):
        return [r.full_url for r in self.requests]


class FakeClock:
    def __init__(self, now=1000.0):
        self.now = now
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, s):
        self.sleeps.append(s)
        self.now += s


def run(argv, web, capsys, config=KEYS, clock=None):
    clock = clock or FakeClock()
    code = lit.main(
        argv, config=dict(config), opener=web, sleep=clock.sleep, clock=clock
    )
    out, err = capsys.readouterr()
    return code, out, err


# The variables that point git at a repository other than the one it runs in.
# git hands them to a hook (in a linked worktree, GIT_DIR and GIT_INDEX_FILE), and
# a suite a hook runs would hand them on to every git it spawns; the
# GIT_CONFIG_KEY_<n> and GIT_CONFIG_VALUE_<n> pairs go with them.
GIT_REPOSITORY_VARIABLES = frozenset(
    (
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_DIR",
        "GIT_GRAFT_FILE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_INTERNAL_SUPER_PREFIX",
        "GIT_NAMESPACE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_REPLACE_REF_BASE",
        "GIT_SHALLOW_FILE",
        "GIT_WORK_TREE",
    )
)


def child_env(tmp_path, **extra) -> dict:
    """The environment of a process a test spawns: the parent's, HOME and PATH
    included, with the key file pointed at a path that does not exist — so the
    child's load_config reads no file at all, never its default, the owner's
    ~/.config/<project>/lit.env — and without the key variables, which load_config
    reads first. The spacing slots go to a directory under `tmp_path`, so a spawned
    run makes nothing under the owner's ~/.cache. Without git's repository
    variables too, so a git a test runs acts on the repository the test made,
    never on the one whose hook runs the suite."""
    missing = Path(tmp_path) / "no-such-lit.env"
    assert not missing.exists()
    state = str(Path(tmp_path) / "lit-state")
    env = {
        name: value
        for name, value in os.environ.items()
        if name not in GIT_REPOSITORY_VARIABLES
        and not name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))
    }
    env.update(extra, LIT_ENV=str(missing), LIT_STATE=state)
    for name in lit.CONFIG_KEYS:
        env.pop(name, None)
    return env


# --------------------------------------------------------------------------- keys


def test_environment_beats_key_file_and_empty_values_fall_through(tmp_path):
    f = tmp_path / "lit.env"
    f.write_text(
        "# comment line\n"
        ": ${OPENALEX_API_KEY:=from-file}\n"
        ": ${SEMANTIC_SCHOLAR_API_KEY:=s2-from-file}\n"
        ": ${LIT_CONTACT_EMAIL:=}\n"
    )
    cfg = lit.load_config(
        {"OPENALEX_API_KEY": "from-env", "SEMANTIC_SCHOLAR_API_KEY": ""}, f
    )
    assert cfg["OPENALEX_API_KEY"] == "from-env"
    # ${VAR:=value} assigns when VAR is unset *or empty* — the file wins over "".
    assert cfg["SEMANTIC_SCHOLAR_API_KEY"] == "s2-from-file"
    assert cfg["LIT_CONTACT_EMAIL"] is None


def test_key_file_path_comes_from_the_environment_and_may_be_absent(tmp_path):
    f = tmp_path / "other.env"
    f.write_text(": ${OPENALEX_API_KEY:=abc}\n")
    assert lit.load_config({"LIT_ENV": str(f)})["OPENALEX_API_KEY"] == "abc"
    absent = lit.load_config({"LIT_ENV": str(tmp_path / "missing.env")})
    assert absent == {
        "OPENALEX_API_KEY": None,
        "SEMANTIC_SCHOLAR_API_KEY": None,
        "LIT_CONTACT_EMAIL": None,
    }
    # Set but empty names no file: refused, never read as the default key file.
    with pytest.raises(lit.LitError, match="LIT_ENV is set but empty"):
        lit.load_config({"LIT_ENV": ""})


def test_child_env_keeps_home_and_path_but_hands_on_no_key(tmp_path, monkeypatch):
    # load_config reads the environment first: a key the owner exported in the
    # shell would reach a spawned main() past the key file.
    for name in lit.CONFIG_KEYS:
        monkeypatch.setenv(name, "exported-in-the-owners-shell")
    env = child_env(tmp_path, LC_ALL="C")
    assert not any(name in env for name in lit.CONFIG_KEYS)
    assert not Path(env["LIT_ENV"]).exists()
    assert (env["HOME"], env["PATH"]) == (os.environ["HOME"], os.environ["PATH"])
    assert env["LC_ALL"] == "C"


def test_no_interpreter_a_test_spawns_can_load_the_owners_key_file():
    # A spawned `tools/lit.py <verb>` loads ~/.config/<project>/lit.env unless
    # LIT_ENV names another file. Every subprocess this module starts takes
    # child_env's environment, which names a file that does not exist — and given
    # a missing file, load_config reads none (the test above) — and carries no key
    # variable (the test before). A guard, not a proof: it sees subprocess.<name>
    # calls only, not `from subprocess import run` or os.system.
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    spawns = [
        call
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "subprocess"
    ]
    assert len(spawns) >= 4  # the index runs, the 308 smoke test, the locale test
    for call in spawns:
        env = next((k.value for k in call.keywords if k.arg == "env"), None)
        assert (
            isinstance(env, ast.Call)
            and isinstance(env.func, ast.Name)
            and env.func.id == "child_env"
        ), f"tests/test_lit.py:{call.lineno} spawns without env=child_env(...)"


SETTINGS = (  # the tool's settings, each read from the environment with its default
    "LIT_PROJECT",
    "LIT_PAPERS_DIR",
    "LIT_REVIEW",
    "LIT_REQUESTS",
    "LIT_ENV",
    "LIT_STATE",
    "LIT_REPO_URL",
)


@pytest.mark.parametrize("name", SETTINGS)
def test_empty_lit_variable_is_a_usage_error(name, monkeypatch, capsys):
    # Set but empty is a mistake — an unset shell variable expanded into an
    # assignment — never a request for the default: main() refuses it before any
    # work, so nothing is read, asked or written, and no spacing directory is made.
    monkeypatch.setenv(name, "")
    web = FakeWeb([])
    code, out, err = run(["budget"], web, capsys)
    assert code == 2 and err == f"error: {name} is set but empty\n" and out == ""
    assert web.requests == []
    assert lit.default_state_dir() is None
    assert set(lit.SETTINGS) == set(SETTINGS)


# --------------------------------------------------------------------------- project


def make_checkout(parent, name):
    """A main checkout, `parent/name`, its `.git` a directory."""
    root = Path(parent) / name
    (root / ".git").mkdir(parents=True)
    return root


def make_worktree(common, at, name="wt", pointer=None, commondir="../.."):
    """A linked worktree at `at` of the repository whose common directory is
    `common`, laid out as `git worktree add` writes it: `common/worktrees/<name>`
    holds `commondir` (git writes it relative to that directory), and the
    worktree's `.git` is a file reading `gitdir:` and that directory, as an
    absolute path or, given `pointer`, as that path relative to `at`."""
    admin = Path(common) / "worktrees" / name
    admin.mkdir(parents=True)
    (admin / "commondir").write_text(commondir + "\n", encoding="utf-8")
    at = Path(at)
    at.mkdir(parents=True)
    (at / ".git").write_text(f"gitdir: {pointer or admin}\n", encoding="utf-8")
    return at


def load_copy(root):
    """tools/lit.py copied to `root`/tools and loaded from there, as `python3 -I
    tools/lit.py` runs it in the repository at `root`: its REPO is `root`."""
    tools = Path(root) / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    copy = tools / "lit.py"
    copy.write_bytes(LIT_PATH.read_bytes())
    spec = importlib.util.spec_from_file_location("lit_copy", copy)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_main_checkout_is_named_by_its_own_directory(tmp_path):
    # `.git` a directory; or no `.git` at all, a tree that is no repository.
    main = make_checkout(tmp_path, "orders-service")
    assert lit.repository_name(main) == "orders-service"
    (tmp_path / "plain").mkdir()
    assert lit.repository_name(tmp_path / "plain") == "plain"


def test_a_linked_worktree_is_named_after_the_main_working_tree(tmp_path):
    # What `git worktree add` writes: the worktree's `.git` is one line, `gitdir:`
    # and the absolute path of `<repository>/.git/worktrees/<name>`, whose
    # `commondir` reads `../..`. A session's worktree sits under the checkout, a
    # detached setup worktree beside it; both belong to `orders-service`.
    main = make_checkout(tmp_path, "orders-service")
    under = main / ".claude" / "worktrees"
    session = make_worktree(main / ".git", under / "brisk-otter", name="brisk-otter")
    detached = make_worktree(main / ".git", tmp_path / "setup-wt", name="setup-wt")
    assert lit.repository_name(session) == "orders-service"
    assert lit.repository_name(detached) == "orders-service"


def test_a_relative_pointer_is_read_from_the_worktree(tmp_path):
    # With worktree.useRelativePaths (git 2.48 and later) the pointer is relative to
    # the worktree itself; `commondir` is as before.
    main = make_checkout(tmp_path, "orders-service")
    session = make_worktree(
        main / ".git",
        main / ".claude" / "worktrees" / "x",
        name="x",
        pointer="../../../.git/worktrees/x",
    )
    assert lit.repository_name(session) == "orders-service"


def test_an_absolute_commondir_is_read_as_it_stands(tmp_path):
    # git writes `../..`, but `commondir` may be absolute: the worktree's
    # administrative directory then need not sit inside the repository.
    main = make_checkout(tmp_path, "orders-service")
    worktree = make_worktree(
        tmp_path / "admin", tmp_path / "wt", commondir=str(main / ".git")
    )
    assert lit.repository_name(worktree) == "orders-service"


@pytest.mark.parametrize(
    "directory,name",
    [("repo.git", "repo"), ("my.repo.git", "my.repo"), ("repo", "repo")],
    ids=["suffix", "dotted-name", "no-suffix"],
)
def test_a_bare_repositorys_worktree_is_named_after_it_without_its_suffix(
    tmp_path, directory, name
):
    # The common directory is the repository itself, not a `.git` inside a tree.
    worktree = make_worktree(tmp_path / "srv" / directory, tmp_path / "bare-wt")
    assert lit.repository_name(worktree) == name


def test_a_submodule_is_named_by_its_own_directory(tmp_path):
    # Its `.git` is a file too, but the directory it names holds no `commondir`:
    # the submodule is a repository of its own.
    outer = make_checkout(tmp_path, "outer")
    (outer / ".git" / "modules" / "sub").mkdir(parents=True)
    (outer / "sub").mkdir()
    pointer = outer / "sub" / ".git"
    pointer.write_text("gitdir: ../.git/modules/sub\n", encoding="utf-8")
    assert lit.repository_name(outer / "sub") == "sub"


def test_a_stale_pointer_is_named_by_its_own_directory(tmp_path):
    # The repository the worktree belonged to is gone: its pointer names nothing.
    worktree = make_worktree(tmp_path / "main" / ".git", tmp_path / "wt")
    shutil.rmtree(tmp_path / "main")
    assert lit.repository_name(worktree) == "wt"


@pytest.mark.parametrize(
    "text",
    ["", "ref: refs/heads/main\n", "gitdir:\n"],
    ids=["empty", "not-a-pointer", "no-path"],
)
def test_a_git_file_that_points_nowhere_is_named_by_its_own_directory(tmp_path, text):
    (tmp_path / "wt").mkdir()
    (tmp_path / "wt" / ".git").write_text(text, encoding="utf-8")
    assert lit.repository_name(tmp_path / "wt") == "wt"


def test_only_a_gitdir_line_is_followed(tmp_path):
    # The path alone, without the `gitdir:` before it, is no pointer for git and
    # none for the tool: the checkout is named by its own directory.
    main = make_checkout(tmp_path, "orders-service")
    worktree = make_worktree(main / ".git", tmp_path / "wt")
    pointer = worktree / ".git"
    assert lit.repository_name(worktree) == "orders-service"
    text = pointer.read_text(encoding="utf-8")
    pointer.write_text(text.replace("gitdir: ", ""), encoding="utf-8")
    assert lit.repository_name(worktree) == "wt"


def test_a_pointer_no_one_can_follow_raises_nothing(tmp_path):
    # Bytes that are not text, a NUL in the path, a symlink loop on the way (a
    # RuntimeError from pathlib before Python 3.13): this runs at import, so an odd
    # checkout must never stop the tool from starting.
    (tmp_path / "wt").mkdir()
    (tmp_path / "loop").symlink_to("loop")
    for pointer in (
        b"gitdir: \xff\xfe\n",
        b"gitdir: /a\x00b\n",
        b"gitdir: ../loop/x\n",
    ):
        (tmp_path / "wt" / ".git").write_bytes(pointer)
        assert lit.repository_name(tmp_path / "wt") == "wt"


def test_the_defaults_name_the_repository_in_every_worktree_of_it(
    tmp_path, monkeypatch
):
    # With nothing set, the owner's terminal in the main checkout, a session's
    # worktree under it and a detached setup worktree beside it resolve one key
    # file and one spacing directory. HOME is under tmp_path: no default is
    # resolved against the real home directory.
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    for name in ("LIT_PROJECT", "LIT_ENV", "LIT_STATE"):
        monkeypatch.delenv(name, raising=False)
    main = make_checkout(tmp_path, "orders-service")
    under = main / ".claude" / "worktrees"
    session = make_worktree(main / ".git", under / "brisk-otter", name="brisk-otter")
    detached = make_worktree(main / ".git", tmp_path / "setup-wt", name="setup-wt")
    for root in (main, session, detached):
        module = load_copy(root)
        assert module.REPO == root.resolve()
        assert module.PROJECT == "orders-service"
        assert module.ENV_FILE == home / ".config" / "orders-service" / "lit.env"
        assert module.STATE_DIR == home / ".cache" / "orders-service" / "lit"
    # LIT_PROJECT still wins, in a worktree too.
    monkeypatch.setenv("LIT_PROJECT", "other")
    module = load_copy(session)
    assert module.PROJECT == "other"
    assert module.ENV_FILE == home / ".config" / "other" / "lit.env"


def run_git(tmp_path, cwd, *args):
    """`git` in `cwd` with its identity and signing given on the command line and
    no global or system configuration read; its output."""
    identity = ["-c", "user.name=tester", "-c", f"user.email={CONTACT}"]
    proc = subprocess.run(
        ["git", *identity, "-c", "commit.gpgsign=false", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=child_env(tmp_path, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1"),
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def git_worktrees(base):
    """A repository git makes under `base`, with a session's worktree under its
    `.claude/worktrees/` and a detached one beside it."""
    main = base / "orders-service"
    run_git(base, base, "init", "-q", str(main))
    run_git(base, main, "commit", "-q", "--allow-empty", "-m", "first")
    session = main / ".claude" / "worktrees" / "brisk-otter"
    run_git(base, main, "worktree", "add", "-q", str(session))
    detached = base / "setup-wt"
    run_git(base, main, "worktree", "add", "-q", "--detach", str(detached))
    return main, session, detached


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_worktrees_made_by_git_are_named_after_the_main_working_tree(tmp_path):
    # The layouts above are made by hand; this is git's own, whichever form of
    # pointer the installed git writes.
    main, session, detached = git_worktrees(tmp_path)
    assert (session / ".git").is_file() and (detached / ".git").is_file()
    for root in (main, session, detached):
        assert lit.repository_name(root) == "orders-service"


def host_state(tmp_path, host):
    """What a git pointed at the repository `host` would change there: its
    configuration, refs and worktrees, and the indexes of its two checkouts."""
    admin = host / ".git"
    return {
        "config": run_git(tmp_path, host, "config", "--list", "--local"),
        "refs": run_git(tmp_path, host, "for-each-ref"),
        "worktrees": run_git(tmp_path, host, "worktree", "list", "--porcelain"),
        "indexes": [
            hashlib.sha256(index.read_bytes()).hexdigest()
            for index in (admin / "index", admin / "worktrees" / "wt" / "index")
        ],
    }


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_spawned_git_leaves_the_host_repository_alone(tmp_path, monkeypatch):
    # git hands a hook in a linked worktree GIT_DIR and GIT_INDEX_FILE, so a suite
    # a hook runs inherits them, and a git spawned with them acts on that worktree's
    # repository, whatever directory it runs in. The host here is a scratch one.
    host = tmp_path / "host"
    run_git(tmp_path, tmp_path, "init", "-q", "-b", "main", str(host))
    (host / "README.md").write_text("the host\n", encoding="utf-8")
    run_git(tmp_path, host, "add", "README.md")
    run_git(tmp_path, host, "commit", "-q", "-m", "the host")
    worktree = tmp_path / "wt"
    run_git(tmp_path, host, "worktree", "add", "-q", "-b", "feature", str(worktree))
    before = host_state(tmp_path, host)
    admin = host / ".git" / "worktrees" / "wt"
    monkeypatch.setenv("GIT_DIR", str(admin))
    monkeypatch.setenv("GIT_INDEX_FILE", str(admin / "index"))
    spawned = tmp_path / "spawned"
    spawned.mkdir()
    main, session, detached = git_worktrees(spawned)
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_INDEX_FILE")
    assert host_state(tmp_path, host) == before
    for root in (main, session, detached):
        assert lit.repository_name(root) == "orders-service"
    # Configuration given in the environment stays out too.
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.bare")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    assert run_git(tmp_path, main, "config", "--get", "core.bare") == "false\n"


# --------------------------------------------------------------------------- names


@pytest.mark.parametrize(
    "family,year,title,want",
    [
        (
            "Brown",
            2010,
            "Information Relaxations and Duality in Stochastic Dynamic Programs",
            "brown2010-information-relaxations-duality-stochastic",
        ),
        (
            "Fürnkranz",
            2001,
            "Machine Learning in Games: A Survey",
            "furnkranz2001-machine-learning-games-survey",
        ),
        (
            "Tesauro",
            1995,
            "Temporal difference learning and TD-Gammon",
            "tesauro1995-temporal-difference-learning-td",
        ),
        ("de Man", 2018, "Syzygy", "deman2018-syzygy"),
    ],
)
def test_suggested_name_is_firstauthor_year_slug_in_ascii(family, year, title, want):
    assert lit.suggest_name(family, year, title) == want


@pytest.mark.parametrize(
    "name",
    [
        "tesauro1995-td-gammon",
        "brown-smith2014-information-relaxations",
        "brown2010a-information-relaxations",
    ],
)
def test_valid_names_pass(name):
    lit.check_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "Tesauro1995-td-gammon",  # upper case
        "tesauro1995-td-gammon.pdf",  # extension
        "tesauro1995",  # no slug
        "tesauro1995-",  # empty slug
        "../tesauro1995-x",  # path
        "tesauro1995_td",  # underscore
        "tesauro95-x",  # two-digit year
        "tesauro-td-gammon-slides",  # no year
        "müller2020-x",  # non-ASCII
    ],
)
def test_invalid_names_are_refused(name):
    with pytest.raises(lit.LitError):
        lit.check_name(name)


# --------------------------------------------------------------------------- ids


@pytest.mark.parametrize(
    "text,want",
    [
        ("10.1287/opre.1090.0796", ("doi", "10.1287/opre.1090.0796")),
        ("https://doi.org/10.1287/OPRE.1090.0796", ("doi", "10.1287/opre.1090.0796")),
        ("doi:10.1145/203330.203343", ("doi", "10.1145/203330.203343")),
        ("arXiv:1805.08328", ("arxiv", "1805.08328")),
        ("1805.08328v2", ("arxiv", "1805.08328")),
        ("https://arxiv.org/abs/2608.15146v1", ("arxiv", "2608.15146")),
        ("https://arxiv.org/pdf/1805.08328", ("arxiv", "1805.08328")),
        ("math/0601001", ("arxiv", "math/0601001")),
        ("10.48550/arXiv.1805.08328", ("arxiv", "1805.08328")),
        ("W2151786492", ("openalex", "W2151786492")),
        ("https://openalex.org/W2151786492", ("openalex", "W2151786492")),
        (
            "621f15e36572161d6f95dd012c524fca2ea6159f",
            ("s2", "621f15e36572161d6f95dd012c524fca2ea6159f"),
        ),
        ("CorpusId:1379193", ("s2", "CorpusId:1379193")),
    ],
)
def test_identifiers_are_classified_and_normalised(text, want):
    assert lit.parse_id(text) == want


def test_unrecognised_identifier_is_an_error():
    with pytest.raises(lit.LitError):
        lit.parse_id("information relaxations")


# --------------------------------------------------------------------------- http


def http_for(web, clock):
    return lit.Http(lit.user_agent(CONTACT), opener=web, sleep=clock.sleep, clock=clock)


def test_429_backs_off_exponentially_and_then_succeeds():
    clock = FakeClock()
    web = FakeWeb([("api.openalex.org", [fail(429), fail(429), ok({"x": 1})])])
    resp = http_for(web, clock).get(
        "https://api.openalex.org/works/W1", source="openalex"
    )
    assert json.loads(resp.body) == {"x": 1}
    assert len(web.requests) == 3
    assert clock.sleeps == [2.0, 4.0]


def test_retry_after_is_honoured():
    clock = FakeClock()
    web = FakeWeb([("api.openalex.org", [fail(429, {"Retry-After": "7"}), ok({})])])
    http_for(web, clock).get("https://api.openalex.org/works/W1", source="openalex")
    assert clock.sleeps == [7.0]


def test_three_429s_raise_a_clear_error_naming_the_url():
    clock = FakeClock()
    web = FakeWeb([("api.openalex.org", fail(429))])
    with pytest.raises(lit.LitError) as e:
        http_for(web, clock).get("https://api.openalex.org/works/W1", source="openalex")
    assert len(web.requests) == 3
    assert "429" in str(e.value) and "https://api.openalex.org/works/W1" in str(e.value)


def test_a_retry_after_beyond_the_cap_stops_at_once_instead_of_sleeping():
    # OpenAlex answers an exhausted daily budget with a 429 whose Retry-After is
    # the time to the reset: the tool must stop, not sleep for hours.
    clock = FakeClock()
    web = FakeWeb([("api.openalex.org", fail(429, {"Retry-After": "83324"}))])
    with pytest.raises(lit.LitError) as e:
        http_for(web, clock).get("https://api.openalex.org/works/W1", source="openalex")
    assert clock.sleeps == []
    assert len(web.requests) == 1
    assert "83324" in str(e.value)


def test_server_errors_are_retried_but_client_errors_are_not():
    clock = FakeClock()
    web = FakeWeb([("api.openalex.org", [fail(503), ok({})])])
    http_for(web, clock).get("https://api.openalex.org/works/W1", source="openalex")
    assert clock.sleeps == [2.0]
    clock2 = FakeClock()
    web2 = FakeWeb([("api.openalex.org", fail(404))])
    with pytest.raises(lit.LitError):
        http_for(web2, clock2).get(
            "https://api.openalex.org/works/W404", source="openalex"
        )
    assert len(web2.requests) == 1 and clock2.sleeps == []


BREAKS = {  # urllib wraps only the send in URLError; these escape it raw
    "timeout-before-answer": raises(socket.timeout("timed out")),
    "disconnected": raises(http.client.RemoteDisconnected("closed")),
    "timeout-mid-body": broken(socket.timeout("timed out")),
    "truncated-body": broken(http.client.IncompleteRead(b"%PDF-1.4 par", 900)),
}


@pytest.mark.parametrize("answer", BREAKS.values(), ids=BREAKS.keys())
def test_an_answer_that_breaks_off_is_retried_like_a_server_error(answer):
    clock = FakeClock()
    web = FakeWeb([("api.openalex.org", [answer, ok({"x": 1})])])
    resp = http_for(web, clock).get(
        "https://api.openalex.org/works/W1", source="openalex"
    )
    assert resp.json() == {"x": 1}
    assert len(web.requests) == 2 and clock.sleeps == [2.0]


@pytest.mark.parametrize("answer", BREAKS.values(), ids=BREAKS.keys())
def test_an_answer_that_keeps_breaking_off_is_a_one_line_error(answer):
    clock = FakeClock()
    web = FakeWeb([("api.openalex.org", answer)])
    with pytest.raises(lit.LitError) as e:
        http_for(web, clock).get("https://api.openalex.org/works/W1", source="openalex")
    assert len(web.requests) == 3
    assert "https://api.openalex.org/works/W1" in str(e.value)
    assert "\n" not in str(e.value)


BAD_URLS = {  # what urllib or http.client cannot send as written
    "no-scheme": "www.example.org/a.pdf",
    "ftp": "ftp://repo.example/a.pdf",
    "non-ascii": "https://repo.example/päper.pdf",
    "newline": "https://repo.example/a\nb.pdf",
    "space": "https://repo.example/a b.pdf",
    "no-host": "https:///a.pdf",
    "bad-port": "https://repo.example:abc/a.pdf",
    "unclosed-bracket": "https://[repo.example/a.pdf",
}


@pytest.mark.parametrize("url", BAD_URLS.values(), ids=BAD_URLS.keys())
def test_a_malformed_url_is_a_one_line_error_before_any_request(url):
    # urllib raises ValueError on a URL with no scheme, http.client UnicodeEncodeError
    # on a non-ASCII one and InvalidURL on a control character — a traceback, or an
    # HTTPException retried 2 s + 4 s as a broken answer.
    clock = FakeClock()
    web = FakeWeb([("repo.example", ok(b"%PDF-1.4"))])
    with pytest.raises(lit.LitError) as e:
        http_for(web, clock).get(url)
    assert web.requests == [] and clock.sleeps == []
    assert str(e.value) == f"web: bad URL {url!r}" and "\n" not in str(e.value)


SEND_REFUSALS = {  # raised by urllib or http.client before anything is sent
    "unicode": UnicodeEncodeError("ascii", "GET /p\xe4per HTTP/1.1", 6, 7, "ordinal"),
    "invalid-url": http.client.InvalidURL("nonnumeric port: 'x'"),
    # http.client quotes a refused header value — here a key — in its ValueError
    "header-value": ValueError(
        f"Invalid header value b'Bearer {KEYS['OPENALEX_API_KEY']}\\r\\n'"
    ),
}


@pytest.mark.parametrize("exc", SEND_REFUSALS.values(), ids=SEND_REFUSALS.keys())
def test_a_request_that_cannot_be_sent_is_a_one_line_error_with_no_retry(exc):
    # The backstop behind the URL check: the same request would be refused again, so
    # it is not retried, and the exception's text — which can quote a header, a key
    # among them — stays out of the message.
    clock = FakeClock()
    web = FakeWeb([("repo.example", raises(exc))])
    with pytest.raises(lit.LitError) as e:
        http_for(web, clock).get("https://repo.example/paper.pdf")
    assert len(web.requests) == 1 and clock.sleeps == []
    message = str(e.value)
    assert "'https://repo.example/paper.pdf'" in message and "\n" not in message
    assert KEYS["OPENALEX_API_KEY"] not in message


@pytest.mark.parametrize(
    "argv,route",
    [
        (["search", "x"], ("api.openalex.org", ok(b"<!DOCTYPE html><html>busy"))),
        (
            ["search", "x", "--source", "arxiv"],
            ("export.arxiv.org", ok(b"<!DOCTYPE html><meta charset=utf-8>busy")),
        ),
    ],
    ids=["openalex-json", "arxiv-atom"],
)
def test_an_answer_that_cannot_be_decoded_is_a_one_line_error(argv, route, capsys):
    code, out, err = run(argv, FakeWeb([route]), capsys)
    assert code == 1 and err.startswith("error: ") and err.count("\n") == 1


OA_SEARCH_DOIS = [
    "10.1287/opre.2014.1322",
    "10.1287/opre.1090.0796",
    "10.1287/opre.2018.1782",
]


@pytest.mark.parametrize("coding", ["gzip", "x-gzip"])
def test_gzip_encoded_api_answer_parses(coding, capsys):
    # urllib asks for no compression and decodes none; a server may compress anyway.
    answer = gzipped(ok(fixture_json("oa_search.json")), coding)
    web = FakeWeb([("api.openalex.org/works?", answer)])
    code, out, err = run(["search", "x", "--json"], web, capsys)
    assert code == 0, err
    assert [r["doi"] for r in json.loads(out)] == OA_SEARCH_DOIS


@pytest.mark.parametrize("raw", [False, True], ids=["zlib-wrapped", "raw"])
def test_deflate_encoded_answer_parses_zlib_wrapped_or_raw(raw, capsys):
    # "deflate" means zlib-wrapped (RFC 9110); some servers send the raw stream.
    answer = deflated(ok(fixture_json("oa_search.json")), raw)
    web = FakeWeb([("api.openalex.org/works?", answer)])
    code, out, err = run(["search", "x", "--json"], web, capsys)
    assert code == 0, err
    assert [r["doi"] for r in json.loads(out)] == OA_SEARCH_DOIS


UNDECODABLE = {  # a Content-Encoding the body does not bear out
    "gzip-but-plain": (200, {"Content-Encoding": "gzip"}, b'{"results": []}'),
    "gzip-truncated": (
        200,
        {"Content-Encoding": "gzip"},
        gzip.compress(b'{"results": []}')[:-8],
    ),
    "deflate-garbage": (200, {"Content-Encoding": "deflate"}, b"not deflate"),
}


@pytest.mark.parametrize("answer", UNDECODABLE.values(), ids=UNDECODABLE.keys())
def test_undecodable_body_is_a_one_line_error(answer):
    web = FakeWeb([("repo.example", answer)])
    with pytest.raises(lit.LitError) as e:
        http_for(web, FakeClock()).get("https://repo.example/paper")
    assert "https://repo.example/paper" in str(e.value) and "\n" not in str(e.value)


def test_a_decode_error_names_the_url_that_answered():
    # After a redirect the answer is the final URL's: naming the URL asked sends the
    # reader to the wrong server.
    answer = (200, {"Content-Encoding": "gzip"}, b"plain", "https://cdn.example/paper")
    web = FakeWeb([("repo.example", answer)])
    with pytest.raises(lit.LitError) as e:
        http_for(web, FakeClock()).get("https://repo.example/paper")
    assert "https://cdn.example/paper" in str(e.value)


def test_a_body_opening_with_gzips_magic_but_not_gzip_passes_through():
    # Undeclared, the second unpacking is a guess: when it fails, the bytes stay as
    # sent.
    body = b"\x1f\x8b but no gzip stream"
    web = FakeWeb([("repo.example", ok(body))])
    assert http_for(web, FakeClock()).get("https://repo.example/x").body == body


@pytest.mark.parametrize("coding", ["br", "identity"])
def test_other_content_codings_pass_through_unchanged(coding):
    body = b"%PDF-1.4 as sent"
    web = FakeWeb([("repo.example", ok(body, {"Content-Encoding": coding}))])
    assert http_for(web, FakeClock()).get("https://repo.example/x").body == body


def test_semantic_scholar_requests_are_spaced_at_least_a_second_apart():
    clock = FakeClock()
    web = FakeWeb([("semanticscholar", ok({}))], clock=clock)
    http = http_for(web, clock)
    for _ in range(3):
        http.get("https://api.semanticscholar.org/graph/v1/paper/x", source="s2")
    gaps = [b - a for a, b in zip(web.times, web.times[1:])]
    assert len(gaps) == 2 and all(g >= 1.0 for g in gaps)


def test_arxiv_requests_are_spaced_at_least_three_seconds_apart_but_openalex_is_not_throttled():
    clock = FakeClock()
    web = FakeWeb(
        [("export.arxiv.org", ok(b"<feed/>")), ("api.openalex.org", ok({}))],
        clock=clock,
    )
    http = http_for(web, clock)
    http.get("https://export.arxiv.org/api/query?a", source="arxiv")
    http.get("https://export.arxiv.org/api/query?b", source="arxiv")
    http.get("https://api.openalex.org/works/W1", source="openalex")
    http.get("https://api.openalex.org/works/W2", source="openalex")
    assert web.times[1] - web.times[0] >= 3.0
    assert web.times[3] - web.times[2] == 0


def test_spacing_holds_across_processes_sharing_a_state_directory(tmp_path):
    # Fan-out research agents run separate processes against one Semantic Scholar
    # key (1 request/s cumulative) and one arXiv address: the spacing must hold
    # between them, not only within one process.
    clock = FakeClock()
    web = FakeWeb(
        [("semanticscholar", ok({})), ("export.arxiv.org", ok(b"<feed/>"))],
        clock=clock,
    )
    agents = [
        lit.Http("ua", opener=web, sleep=clock.sleep, clock=clock, state_dir=tmp_path)
        for _ in range(3)
    ]
    for http in agents:
        http.get("https://api.semanticscholar.org/graph/v1/paper/x", source="s2")
    for http in agents:
        http.get("https://export.arxiv.org/api/query?q", source="arxiv")
    s2_gaps = [b - a for a, b in zip(web.times[:3], web.times[1:3])]
    ax_gaps = [b - a for a, b in zip(web.times[3:6], web.times[4:6])]
    assert len(s2_gaps) == 2 and all(g >= 1.0 for g in s2_gaps)
    assert len(ax_gaps) == 2 and all(g >= 3.0 for g in ax_gaps)


def test_a_slot_stamp_in_the_future_costs_one_gap_not_its_distance(tmp_path):
    # A skewed clock (another machine's stamp) or a stale file can leave a stamp far
    # ahead: the wait is capped at the source's gap.
    clock = FakeClock()
    (tmp_path / "s2.last").write_text(repr(clock.now + 10_000), encoding="utf-8")
    web = FakeWeb([("semanticscholar", ok({}))])
    http = lit.Http(
        "ua", opener=web, sleep=clock.sleep, clock=clock, state_dir=tmp_path
    )
    http.get("https://api.semanticscholar.org/graph/v1/paper/x", source="s2")
    assert clock.sleeps == [1.1]


@pytest.mark.skipif(not Path(PY).exists(), reason=f"no {PY}")
def test_the_state_directory_is_made_only_for_a_request_it_spaces(tmp_path):
    # The spacing slots live in LIT_STATE, by default under the user's ~/.cache:
    # --help, check --no-network and index send nothing, so they make nothing
    # there; a spaced request makes the directory as it takes its first slot.
    state = Path(child_env(tmp_path)["LIT_STATE"])
    papers, rev = make_papers(tmp_path, [])
    for argv in (
        ["--help"],
        ["check", "--no-network"],
        ["--papers", str(papers), "--review", str(rev), "index"],
    ):
        proc = subprocess.run(
            [PY, "-I", str(LIT_PATH), *argv],
            capture_output=True,
            text=True,
            env=child_env(tmp_path),
        )
        assert "Traceback" not in proc.stderr, proc.stderr
        assert not state.exists(), argv
    clock = FakeClock()
    web = FakeWeb([("export.arxiv.org", ok(b"<feed/>"))])
    http = lit.Http("ua", opener=web, sleep=clock.sleep, clock=clock, state_dir=state)
    http.get("https://export.arxiv.org/api/query?q", source="arxiv")
    assert (state / "arxiv.last").is_file()


def follow_redirect(req, newurl, code=302):
    """What urllib's http_error_30x asks the redirect handler on a Location header."""
    headers = email.message.Message()
    return lit.SafeRedirect().redirect_request(
        req, io.BytesIO(b""), code, "Found", headers, newurl
    )


def test_safe_redirect_refuses_https_downgrade():
    # A redirect to plain HTTP would replay the request in clear text.
    req = urllib.request.Request("https://api.openalex.org/works/W1")
    with pytest.raises(urllib.error.HTTPError) as e:
        follow_redirect(req, "http://evil.example/x")
    assert e.value.code == 302


KEYED_CLIENTS = [  # each keyed client and the header its key rides in
    (lambda http: lit.OpenAlex(http, KEYS["OPENALEX_API_KEY"]), "Authorization"),
    (
        lambda http: lit.SemanticScholar(http, KEYS["SEMANTIC_SCHOLAR_API_KEY"]),
        "X-api-key",
    ),
]
KEYED_IDS = ["openalex", "s2"]


def keyed_request(client):
    """The request a keyed client sends, as urllib holds it."""
    web = FakeWeb([("api.", ok({}))])
    client(http_for(web, FakeClock())).get("/x", {})
    return web.requests[0]


@pytest.mark.parametrize("client,header", KEYED_CLIENTS, ids=KEYED_IDS)
def test_credentials_are_dropped_on_redirect(client, header):
    # urllib's redirect handler copies a request's headers to the new URL, whatever
    # its origin; an unredirected header stays behind with the original request.
    web = FakeWeb([("api.", ok({}))])
    client(http_for(web, FakeClock())).get("/x", {})
    sent = web.requests[0]
    assert header in sent.unredirected_hdrs and header not in sent.headers
    moved = follow_redirect(sent, "https://other.example/")
    assert moved.full_url == "https://other.example/"
    assert moved.get_header(header) is None
    assert lit.REPO_URL in moved.get_header("User-agent")  # the rest moves on


SAME_ORIGIN = {  # the key's own origin: scheme, host, port
    "path": "https://{host}/moved",
    "default-port": "https://{host}:443/moved",
    "upper-case-host": "https://{HOST}/moved",
}


@pytest.mark.parametrize("target", SAME_ORIGIN.values(), ids=SAME_ORIGIN.keys())
@pytest.mark.parametrize("client,header", KEYED_CLIENTS, ids=KEYED_IDS)
def test_a_same_origin_redirect_keeps_the_key(client, header, target):
    # An API moving a path stays at the key's origin. Dropped there, the key turns
    # the next answer into a keyless one — for OpenAlex a 429 within seconds, which
    # reads like a spent budget.
    sent = keyed_request(client)
    host = urllib.parse.urlsplit(sent.full_url).hostname
    moved = follow_redirect(sent, target.format(host=host, HOST=host.upper()))
    assert sent.get_header(header)
    assert moved.get_header(header) == sent.get_header(header)
    # still unredirected: the base handler leaves it behind at the next hop
    assert header in moved.unredirected_hdrs and header not in moved.headers


CROSS_ORIGIN = {  # anything not provably the key's origin
    "other-host": "https://other.example/moved",
    "other-port": "https://{host}:8443/moved",
    "subdomain": "https://evil.{host}/moved",
    "suffix": "https://{host}.evil.example/moved",
    "userinfo": "https://{host}@evil.example/moved",
    # urlsplit reads the key's host here, urllib connects to "x@<host>": a URL
    # carrying credentials is no origin to hand a key to
    "userinfo-before-own-host": "https://x@{host}/moved",
}


@pytest.mark.parametrize("target", CROSS_ORIGIN.values(), ids=CROSS_ORIGIN.keys())
@pytest.mark.parametrize("client,header", KEYED_CLIENTS, ids=KEYED_IDS)
def test_a_cross_origin_redirect_drops_the_key(client, header, target):
    sent = keyed_request(client)
    host = urllib.parse.urlsplit(sent.full_url).hostname
    moved = follow_redirect(sent, target.format(host=host))
    assert moved.get_header(header) is None
    assert lit.REPO_URL in moved.get_header("User-agent")  # the rest moves on


@pytest.mark.parametrize("client,header", KEYED_CLIENTS, ids=KEYED_IDS)
def test_a_key_follows_only_an_unbroken_run_of_same_origin_hops(client, header):
    sent = keyed_request(client)
    origin = "https://" + urllib.parse.urlsplit(sent.full_url).hostname
    hop = follow_redirect(sent, origin + "/one")
    assert hop.get_header(header) == sent.get_header(header)
    away = follow_redirect(hop, "https://other.example/two")
    back = follow_redirect(away, origin + "/three")  # gone once, gone for good
    assert away.get_header(header) is None and back.get_header(header) is None
    with pytest.raises(urllib.error.HTTPError) as e:  # never in clear: refused
        follow_redirect(hop, origin.replace("https://", "http://") + "/four")
    assert "plain HTTP refused" in str(e.value.reason)


def test_the_default_opener_redirects_through_safe_redirect_only():
    # urlopen's global opener follows every redirect: unless Http builds its own
    # opener around SafeRedirect, the handler's refusals never run.
    director = lit.Http("ua").opener.__self__
    redirects = [
        h
        for h in director.handlers
        if isinstance(h, urllib.request.HTTPRedirectHandler)
    ]
    assert [type(h) for h in redirects] == [lit.SafeRedirect]


def test_a_refused_redirect_is_not_retried_and_its_error_says_why():
    def downgrade():
        req = urllib.request.Request("https://repo.example/paper.pdf")
        return follow_redirect(req, "http://repo.example/paper.pdf")  # raises

    clock = FakeClock()
    web = FakeWeb([("repo.example", downgrade)])
    with pytest.raises(lit.LitError) as e:
        http_for(web, clock).get("https://repo.example/paper.pdf")
    assert len(web.requests) == 1 and clock.sleeps == []
    assert "HTTP 302" in str(e.value) and "refused" in str(e.value)


class Transport(urllib.request.HTTPSHandler):
    """The network under a real OpenerDirector, so urllib's own redirect handling
    runs: `moves` maps a URL to the Location its 302 names, any other URL answers
    with a PDF. No socket is opened."""

    def __init__(self, moves):
        super().__init__()
        self.moves, self.seen = moves, []

    def https_open(self, req):
        self.seen.append(req.full_url)
        headers = email.message.Message()
        if req.full_url in self.moves:
            headers["Location"] = self.moves[req.full_url]
            code, msg, body = 302, "Found", b""
        else:
            code, msg, body = 200, "OK", b"%PDF-1.4"
        resp = urllib.response.addinfourl(io.BytesIO(body), headers, req.full_url, code)
        resp.msg = msg
        return resp


def real_opener(transport):
    """Http's opener — SafeRedirect, urllib's handlers — over `transport`."""
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}), lit.SafeRedirect, transport
    ).open


def test_a_redirect_loop_is_a_one_line_error():
    # urllib refuses a loop (or an eleventh hop) with a three-line reason — its
    # inf_msg; interpolated raw, it would break the one-line contract.
    url = "https://repo.example/a.pdf"
    transport = Transport({url: url})
    with pytest.raises(lit.LitError) as e:
        lit.Http("ua", opener=real_opener(transport)).get(url)
    assert "infinite loop" in str(e.value) and "\n" not in str(e.value)
    assert len(transport.seen) > 1  # followed, then refused


def test_a_redirect_to_a_scheme_other_than_http_is_refused():
    # From an http:// candidate (an OpenAlex pdf_url can be plain HTTP) urllib would
    # follow a redirect to ftp:// and fetch it with its FTPHandler.
    req = urllib.request.Request("http://repo.example/a.pdf")
    with pytest.raises(urllib.error.HTTPError) as e:
        follow_redirect(req, "ftp://repo.example/a.pdf")
    assert e.value.code == 302 and "refused" in str(e.value.reason)
    assert follow_redirect(req, "https://repo.example/a.pdf")  # an upgrade moves on


def test_landing_redirect_to_another_host_is_refused_but_handles_resolve():
    # An open-access repository page that redirects to a publisher's PDF would fetch
    # it by IP authentication from a campus network; a handle must redirect to be
    # any use, and its target is then the landing host.
    web = FakeWeb(
        [
            ("repo.example", ok(b"<html/>")),
            ("hdl.handle.net", ok(b"<html/>")),
            ("arxiv.org", ok(b"%PDF-1.4")),
        ]
    )
    http = http_for(web, FakeClock())
    http.get("https://repo.example/handle/10161/4435", same_host_only=True)
    http.get("http://hdl.handle.net/10161/4435", same_host_only=True)
    http.get("https://arxiv.org/pdf/1805.08328")  # a vouched PDF candidate
    repo, handle, vouched = web.requests
    with pytest.raises(urllib.error.HTTPError):
        follow_redirect(repo, "https://publisher.example/closed.pdf")
    same_host = "https://repo.example/bitstream/4435.pdf"
    assert follow_redirect(repo, same_host).full_url == same_host
    landed = follow_redirect(handle, "https://dukespace.example/handle/10161/4435")
    assert landed.full_url == "https://dukespace.example/handle/10161/4435"
    with pytest.raises(urllib.error.HTTPError):
        follow_redirect(landed, "https://publisher.example/closed.pdf")
    elsewhere = "https://export.arxiv.org/pdf/1805.08328"
    assert follow_redirect(vouched, elsewhere).full_url == elsewhere


def test_a_308_is_followed_even_by_a_base_handler_that_knows_only_307(monkeypatch):
    # Python 3.9's handler (/usr/bin/python3) refuses the codes it does not know —
    # 301/302/303/307 only — so every 308 would come back "HTTP 308 … — Permanent
    # Redirect", a refusal's format. For a GET a 308 is a 307.
    real = urllib.request.HTTPRedirectHandler.redirect_request

    def like_python_39(self, req, fp, code, msg, headers, newurl):
        if code not in (301, 302, 303, 307):
            raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)
        return real(self, req, fp, code, msg, headers, newurl)

    monkeypatch.setattr(
        urllib.request.HTTPRedirectHandler, "redirect_request", like_python_39
    )
    page = urllib.request.Request("https://repo.example/handle/1")
    page.same_host_only = True
    moved = follow_redirect(page, "https://repo.example/bitstream/1.pdf", code=308)
    assert moved.full_url == "https://repo.example/bitstream/1.pdf"
    assert moved.same_host_only
    with pytest.raises(urllib.error.HTTPError) as e:  # a refusal keeps its code
        follow_redirect(page, "https://publisher.example/1.pdf", code=308)
    assert e.value.code == 308


SMOKE_UNDER_SYSTEM_PYTHON = r"""
import email.message, importlib.util, io, sys, urllib.request, urllib.response

spec = importlib.util.spec_from_file_location("lit", sys.argv[1])
lit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lit)

A, B = "https://repo.example/a.pdf", "https://repo.example/b.pdf"  # one origin
C, D = "https://repo.example/c.pdf", "https://cdn.example/d.pdf"  # two
MOVES = {A: B, C: D}
seen = []


class FakeHTTPS(urllib.request.HTTPSHandler):
    # a 308 from each MOVES key to its value, a PDF anywhere else; no socket opened
    def https_open(self, req):
        seen.append((req.full_url, req.get_header("Authorization")))
        headers = email.message.Message()
        if req.full_url in MOVES:
            headers["Location"] = MOVES[req.full_url]
            code, msg, body = 308, "Permanent Redirect", b""
        else:
            code, msg, body = 200, "OK", b"%PDF-1.4"
        resp = urllib.response.addinfourl(io.BytesIO(body), headers, req.full_url, code)
        resp.msg = msg
        return resp


opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}), lit.SafeRedirect, FakeHTTPS
)
http = lit.Http("smoke", opener=opener.open)
bearer = "Bearer smoke-placeholder"  # not a key
for start, end in ((A, B), (C, D)):
    resp = http.get(start, secret_headers={"Authorization": bearer})
    assert (resp.body, resp.url) == (b"%PDF-1.4", end), (start, resp.url)
# the key stays within its origin (B) and is dropped at another (D)
assert seen == [(A, bearer), (B, bearer), (C, bearer), (D, None)], seen
print("ok", sys.version.split()[0])
"""


@pytest.mark.skipif(not Path(PY).exists(), reason=f"no {PY}")
def test_a_308_is_followed_under_system_python(tmp_path):
    # The suite runs under the venv's Python, whose handler knows 308; the tool's
    # documented interpreter is /usr/bin/python3 (3.9), whose handler does not. -I:
    # no site-packages, no PYTHON* variables — the stdlib alone.
    proc = subprocess.run(
        [PY, "-I", "-c", SMOKE_UNDER_SYSTEM_PYTHON, str(LIT_PATH)],
        capture_output=True,
        text=True,
        env=child_env(tmp_path),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.startswith("ok ")


def test_every_request_names_the_repo_and_the_contact_address():
    clock = FakeClock()
    web = FakeWeb([("api.openalex.org", ok({}))])
    http_for(web, clock).get("https://api.openalex.org/works/W1", source="openalex")
    ua = web.requests[0].get_header("User-agent")
    assert lit.REPO_URL in ua and CONTACT in ua


@pytest.mark.parametrize(
    "project,product",
    [("my project", "my-project"), ("Projét café", "Projet-cafe"), ("±§!", "repository")],
    ids=["space", "accent", "all-symbols"],
)
def test_the_user_agent_product_is_a_token_whatever_the_project_is_called(
    project, product, monkeypatch
):
    # LIT_PROJECT defaults to the repository's directory name, which may hold a
    # space or an accent; the product token the User-Agent opens with may not, and a
    # name with nothing a token allows falls back to a fixed one.
    monkeypatch.setattr(lit, "PROJECT", project)
    first = lit.user_agent(CONTACT).split(" ")[0]
    assert first == f"{product}-lit/1.0"
    assert re.fullmatch(r"[A-Za-z0-9._-]+-lit/1\.0", first)


# --------------------------------------------------------------------------- records


def test_openalex_work_normalises_to_a_record():
    r = lit.record_from_openalex(fixture_json("oa_work_brown2010.json"))
    assert (
        r["title"]
        == "Information Relaxations and Duality in Stochastic Dynamic Programs"
    )
    assert r["year"] == 2010
    assert r["doi"] == "10.1287/opre.1090.0796"
    assert r["arxiv"] is None
    assert r["openalex"] == "W2151786492"
    assert r["venue"] == "Operations Research"
    assert r["authors"] == ["David B. Brown", "James E. Smith", "Peng Sun"]
    assert r["citations"] == 245
    assert r["oa"] == "oa"


def test_openalex_arxiv_work_carries_its_arxiv_id():
    r = lit.record_from_openalex(fixture_json("oa_work_viper_arxivdoi.json"))
    assert r["arxiv"] == "1805.08328"
    assert r["year"] == 2018 and r["citations"] == 158


def test_openalex_search_results_keep_closed_status():
    results = fixture_json("oa_search.json")["results"]
    recs = [lit.record_from_openalex(w) for w in results]
    assert [r["doi"] for r in recs] == [
        "10.1287/opre.2014.1322",
        "10.1287/opre.1090.0796",
        "10.1287/opre.2018.1782",
    ]
    assert [r["oa"] for r in recs] == ["closed", "oa", "closed"]


def test_semantic_scholar_paper_normalises_to_a_record():
    r = lit.record_from_s2(fixture_json("s2_paper_brown2010.json"))
    assert r["doi"] == "10.1287/opre.1090.0796"
    assert r["year"] == 2010 and r["citations"] == 248
    assert r["oa"] == "oa"
    assert r["s2"] == "621f15e36572161d6f95dd012c524fca2ea6159f"
    assert r["tldr"].startswith(
        "This approach relaxes the nonanticipativity constraints"
    )


def test_semantic_scholar_oa_status_reads_arxiv_ids_and_closed_flags():
    search = [lit.record_from_s2(p) for p in fixture_json("s2_search.json")["data"]]
    assert search[0]["arxiv"] == "2605.22965" and search[0]["doi"] is None
    assert (
        search[0]["oa"] == "oa"
    )  # an arXiv paper is open even when S2's PDF field is empty
    assert (
        search[2]["doi"] == "10.1609/aaai.v30i1.10410" and search[2]["oa"] == "oa"
    )  # GOLD
    refs = [
        lit.record_from_s2(item["citedPaper"])
        for item in fixture_json("s2_refs.json")["data"]
    ]
    assert refs[1]["title"] == "Game theory." and refs[1]["oa"] == "closed"


def test_arxiv_feed_normalises_to_records():
    recs = lit.records_from_arxiv(fixture("arxiv_search.xml").decode())
    assert [r["arxiv"] for r in recs] == ["1805.08328", "2608.20909"]
    assert recs[0]["title"] == "Verifiable Reinforcement Learning via Policy Extraction"
    assert recs[0]["year"] == 2018
    assert recs[0]["authors"] == ["Osbert Bastani", "Yewen Pu", "Armando Solar-Lezama"]
    assert recs[0]["oa"] == "oa" and recs[0]["citations"] is None


def test_dedupe_merges_by_doi_and_by_arxiv_id_keeping_the_first_and_filling_gaps():
    oa_rec = lit.record_from_openalex(fixture_json("oa_work_brown2010.json"))
    s2_rec = lit.record_from_s2(fixture_json("s2_paper_brown2010.json"))
    s2_rec["doi"] = s2_rec["doi"].upper()
    viper_oa = lit.record_from_openalex(fixture_json("oa_work_viper_arxivdoi.json"))
    viper_ax = lit.records_from_arxiv(fixture("arxiv_search.xml").decode())[0]
    other = lit.records_from_arxiv(fixture("arxiv_search.xml").decode())[1]
    merged = lit.dedupe([oa_rec, s2_rec, viper_oa, viper_ax, other])
    assert len(merged) == 3
    brown = merged[0]
    assert brown["source"] == "openalex" and brown["citations"] == 245
    assert brown["tldr"].startswith("This approach relaxes")  # filled from S2
    assert merged[1]["arxiv"] == "1805.08328" and merged[1]["source"] == "openalex"


def test_table_marks_unknowns_truncates_titles_and_prefers_a_journal_doi():
    recs = [
        {
            "year": 2010,
            "citations": 245,
            "oa": "oa",
            "doi": "10.1287/opre.1090.0796",
            "arxiv": "1001.00001",
            "title": "Information Relaxations and Duality in Stochastic Dynamic Programs",
        },
        {
            "year": None,
            "citations": None,
            "oa": "?",
            "doi": "10.48550/arxiv.1805.08328",
            "arxiv": "1805.08328",
            "title": "x" * 200,
        },
    ]
    lines = lit.format_table(recs).splitlines()
    assert "10.1287/opre.1090.0796" in lines[1] and "arXiv:1001.00001" not in lines[1]
    assert "arXiv:1805.08328" in lines[2] and "10.48550" not in lines[2]
    assert lines[2].split()[0] == "?" and lines[2].split()[1] == "?"
    assert lines[2].endswith("…") and "x" * 200 not in lines[2]


def test_table_prints_every_id_in_full_so_it_can_be_pasted_back():
    # The printed id is the next resolve/refs/cites argument: a 40-character Semantic
    # Scholar id or a long DOI cut short is useless.
    s2_id = "621f15e36572161d6f95dd012c524fca2ea6159f"
    long_doi = "10.1002/(sici)1097-0258(19980430)17:8<857::aid-sim777>3.0.co;2-e"
    recs = [
        {"year": 2010, "citations": 248, "oa": "oa", "s2": s2_id, "title": "First"},
        {"year": 1998, "citations": 5, "oa": "?", "doi": long_doi, "title": "Second"},
    ]
    lines = lit.format_table(recs).splitlines()
    assert s2_id in lines[1] and long_doi in lines[2]
    assert lines[1].index("First") == lines[2].index("Second")  # titles aligned


# --------------------------------------------------------------------------- resolve


def oa_route(work):
    return ("api.openalex.org/works/", ok(work))


def with_pdf_location(work, url):
    w = copy.deepcopy(work)
    w["best_oa_location"] = {
        "is_oa": True,
        "landing_page_url": url.replace(".pdf", ""),
        "pdf_url": url,
        "license": "cc-by",
        "version": "acceptedVersion",
        "source": {"display_name": "Some Repository"},
    }
    return w


def upw_with_pdf(url):
    u = fixture_json("upw_brown2010.json")
    u["best_oa_location"]["url_for_pdf"] = url
    return u


def resolve_with(ident, routes, config=KEYS):
    clock = FakeClock()
    web = FakeWeb(routes)
    http = lit.Http(
        lit.user_agent(config.get("LIT_CONTACT_EMAIL")),
        opener=web,
        sleep=clock.sleep,
        clock=clock,
    )
    return lit.resolve(ident, lit.Clients(dict(config), http)), web


def test_an_arxiv_id_resolves_to_its_pdf_without_any_request():
    res, web = resolve_with("arXiv:1805.08328v2", [])
    assert (
        res["status"] == "pdf"
        and res["url"] == "https://arxiv.org/pdf/1805.08328"
        and res["source"] == "arxiv"
    )
    assert web.requests == []


def test_arxiv_copy_beats_an_openalex_pdf_location():
    work = with_pdf_location(
        fixture_json("oa_work_viper_arxivdoi.json"),
        "https://publisher.example/viper.pdf",
    )
    work["doi"] = "https://doi.org/10.5555/viper"
    res, _ = resolve_with("10.5555/viper", [oa_route(work)])
    assert res["source"] == "arxiv" and res["url"] == "https://arxiv.org/pdf/1805.08328"
    assert [c["source"] for c in res["candidates"]] == ["arxiv", "openalex"]


def test_openalex_pdf_beats_unpaywall():
    work = with_pdf_location(
        fixture_json("oa_work_brown2010.json"), "https://repo.example/brown2010.pdf"
    )
    res, _ = resolve_with(
        "10.1287/opre.1090.0796",
        [
            oa_route(work),
            (
                "api.unpaywall.org",
                ok(upw_with_pdf("https://upw.example/brown2010.pdf")),
            ),
        ],
    )
    assert (
        res["source"] == "openalex"
        and res["url"] == "https://repo.example/brown2010.pdf"
    )
    assert res["license"] == "cc-by" and res["version"] == "acceptedVersion"


def test_unpaywall_is_the_fallback_when_openalex_has_no_pdf():
    res, web = resolve_with(
        "10.1287/opre.1090.0796",
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            (
                "api.unpaywall.org",
                ok(upw_with_pdf("https://upw.example/brown2010.pdf")),
            ),
        ],
    )
    assert (
        res["source"] == "unpaywall"
        and res["url"] == "https://upw.example/brown2010.pdf"
    )
    upw_url = [u for u in web.urls() if "unpaywall" in u][0]
    contact = urllib.parse.quote(CONTACT, safe="")
    assert "/v2/10.1287/opre.1090.0796?email=" + contact in upw_url
    assert "/v2/search" not in upw_url


def test_closed_when_every_source_is_empty_and_landing_pages_are_reported():
    res, _ = resolve_with(
        "10.1287/opre.1090.0796",
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
        ],
    )
    assert res["status"] == "closed" and res["url"] is None
    assert "http://hdl.handle.net/10161/4435" in res["landing"]
    assert res["incomplete"] is None  # every source asked answered


def test_without_a_contact_address_unpaywall_is_never_called():
    cfg = dict(KEYS, LIT_CONTACT_EMAIL=None)
    res, web = resolve_with(
        "10.1287/opre.1090.0796",
        [oa_route(fixture_json("oa_work_brown2010.json"))],
        config=cfg,
    )
    assert res["status"] == "closed"
    assert not any("unpaywall" in u for u in web.urls())


def test_an_unpaywall_outage_is_a_warning_kept_in_the_resolve_result(capsys):
    res, web = resolve_with(
        "10.1287/opre.1090.0796",
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", fail(503)),
        ],
    )
    assert res["status"] == "closed"  # nothing earlier had a PDF
    assert "http://hdl.handle.net/10161/4435" in res["landing"]  # OpenAlex's stand
    assert len(res["warnings"]) == 1 and "HTTP 503" in res["warnings"][0]
    assert res["warnings"][0] in capsys.readouterr().err
    assert "HTTP 503" in res["incomplete"]  # "closed" is not established


def test_pdf_link_is_read_from_a_landing_page_citation_meta_tag():
    html = fixture("landing_arxiv_abs.html").decode()
    assert (
        lit.pdf_url_from_landing(html, "https://arxiv.org/abs/1805.08328")
        == "https://arxiv.org/pdf/1805.08328"
    )
    rel = '<html><head><meta name="citation_pdf_url" content="/bitstream/4435/paper.pdf"></head></html>'
    assert lit.pdf_url_from_landing(rel, "https://repo.example/handle/10161/4435") == (
        "https://repo.example/bitstream/4435/paper.pdf"
    )
    assert (
        lit.pdf_url_from_landing(
            fixture("landing_anubis.html").decode(), "https://dukespace.example/"
        )
        is None
    )


# --------------------------------------------------------------------------- filing


def test_pdf_check_accepts_pdf_bytes_only():
    assert lit.is_pdf(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    assert not lit.is_pdf(b"<!DOCTYPE html><html>")
    assert not lit.is_pdf(b"")


def test_index_row_format():
    assert lit.index_row(
        "brown2010-information-relaxations",
        "Operations Research",
        2010,
        "pp. 785–801",
        "https://example.org/b.pdf",
    ) == (
        "| brown2010-information-relaxations.pdf | Operations Research 2010, pp. 785–801 | https://example.org/b.pdf |"
    )
    assert lit.index_row(
        "bastani2018-verifiable-rl",
        "arXiv",
        2018,
        None,
        "https://arxiv.org/pdf/1805.08328",
    ) == (
        "| bastani2018-verifiable-rl.pdf | arXiv 2018 | https://arxiv.org/pdf/1805.08328 |"
    )


def test_requests_row_format_escapes_pipes():
    row = lit.requests_row(
        4,
        "https://doi.org/10.1287/opre.2014.1322",
        "Duality | convexity",
        ["David B. Brown", "James E. Smith"],
        "Operations Research",
        2014,
        "brown2014-information-relaxations-duality-convex",
        "T1",
        "the gradient-penalty bound",
    )
    assert row == (
        "| 4 | https://doi.org/10.1287/opre.2014.1322 | Duality \\| convexity (Brown, Smith; Operations Research, "
        "2014) → `brown2014-information-relaxations-duality-convex.pdf` | T1 | the gradient-penalty bound | open |"
    )


REVIEW_STUB = """# Literature review

## 6. Local papers index (`docs/papers/`)

| File | What | Provenance / caveats |
|---|---|---|
| a2020-alpha.pdf | X 2020 | url |
| c2022-gamma.pdf | Z 2022 | url |

## 7. Something else

| d2023-delta.pdf | not part of the index | x |
"""


def make_papers(tmp_path, files, review=REVIEW_STUB):
    papers = tmp_path / "papers"
    papers.mkdir()
    for f in files:
        (papers / f).write_bytes(b"%PDF-1.4\n")
    rev = tmp_path / "review.md"
    rev.write_text(review)
    return papers, rev


def run_index(papers, rev):
    return subprocess.run(
        [PY, "-I", str(LIT_PATH), "--papers", str(papers), "--review", str(rev), "index"],
        capture_output=True,
        text=True,
        env=child_env(papers.parent),  # main() loads the key file: not the owner's
    )


def test_index_reports_unindexed_pdfs_and_missing_files_under_system_python(tmp_path):
    papers, rev = make_papers(tmp_path, ["a2020-alpha.pdf", "b2021-beta.pdf"])
    proc = run_index(papers, rev)
    assert proc.returncode == 1
    assert "b2021-beta.pdf" in proc.stdout and "c2022-gamma.pdf" in proc.stdout
    assert "a2020-alpha.pdf" not in proc.stdout and "d2023-delta.pdf" not in proc.stdout


def test_a_missing_review_file_is_a_one_line_error(tmp_path, capsys):
    # A mistyped --review must not end in a FileNotFoundError traceback.
    papers, rev = make_papers(tmp_path, ["a2020-alpha.pdf"])
    missing = tmp_path / "no-review.md"
    argv = ["--papers", str(papers), "--review", str(missing), "index"]
    code, out, err = run(argv, FakeWeb([]), capsys)
    assert code == 1 and err.startswith(f"error: cannot read {missing}: ")
    assert err.count("\n") == 1


def test_index_is_clean_when_files_and_rows_agree(tmp_path):
    papers, rev = make_papers(tmp_path, ["a2020-alpha.pdf", "c2022-gamma.pdf"])
    proc = run_index(papers, rev)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_the_repository_papers_index_is_consistent(tmp_path):
    proc = subprocess.run(
        [PY, "-I", str(LIT_PATH), "index"],
        capture_output=True,
        text=True,
        env=child_env(tmp_path),  # main() loads the key file: not the owner's
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


UNDER_AN_ASCII_LOCALE = r"""
import importlib.util, locale, sys
from pathlib import Path

if "utf" in locale.getpreferredencoding(False).lower().replace("-", ""):
    print("skip: the locale's encoding is", locale.getpreferredencoding(False))
    sys.exit(0)
spec = importlib.util.spec_from_file_location("lit", sys.argv[1])
lit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lit)
d = Path(sys.argv[2])
review = ["--papers", str(d / "papers"), "--review", str(d / "review.md"), "index"]
checks = {
    "the key file": lambda: lit.load_config({}, d / "lit.env")["LIT_CONTACT_EMAIL"],
    "the queue": lambda: lit.append_request(d / "REQUESTS.md", lambda n: f"| {n} | Über → x |"),
    "the review": lambda: lit.main(review, config={}),
}
want = {"the key file": "owner" + "@" + "example.org", "the queue": 3, "the review": 0}
failed = []
for name, check in checks.items():
    try:
        got = check()
    except Exception as e:
        got = f"{type(e).__name__}: {e}"
    if got != want[name]:
        failed.append(f"{name}: {got!r}")
print("; ".join(failed) or "ok")
sys.exit(1 if failed else 0)
"""


@pytest.mark.skipif(not Path(PY).exists(), reason=f"no {PY}")
def test_text_files_are_read_and_written_as_utf8_under_any_locale(tmp_path):
    # The queue carries "→" and non-ASCII titles, the review "§" and "—": opened in
    # the locale's encoding they break under an ASCII locale.
    # LC_ALL=C with UTF-8 mode off (-X utf8=0) forces one.
    papers, rev = make_papers(
        tmp_path,
        ["a2020-alpha.pdf", "c2022-gamma.pdf"],
        review=REVIEW_STUB + "\nZürich — §6 is the index.\n",
    )
    (tmp_path / "lit.env").write_text(
        f"# clé — the owner's address\n: ${{LIT_CONTACT_EMAIL:={CONTACT}}}\n",
        encoding="utf-8",
    )
    (tmp_path / "REQUESTS.md").write_text(REQUESTS_STUB, encoding="utf-8")
    proc = subprocess.run(
        [PY, "-I", "-X", "utf8=0", "-c", UNDER_AN_ASCII_LOCALE, str(LIT_PATH)]
        + [str(tmp_path)],
        capture_output=True,
        text=True,
        env=child_env(tmp_path, LC_ALL="C", LANG="C"),
    )
    if proc.stdout.startswith("skip: "):
        pytest.skip(proc.stdout.strip())
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (
        (tmp_path / "REQUESTS.md")
        .read_text(encoding="utf-8")
        .endswith("| 3 | Über → x |\n")
    )


REQUESTS_STUB = """# Paper requests

| # | DOI / URL | Title (authors, venue, year) | Needed by (memo) | Why | Status |
|---|---|---|---|---|---|
| 1 | https://doi.org/10.1/a | A (X; V, 2001) → `x2001-a.pdf` | T2 | w | filed |
| 2 | https://doi.org/10.1/b | B (Y; V, 2002) → `y2002-b.pdf` | T3 | w | open |
"""


def fetch_env(tmp_path, existing=()):
    papers = tmp_path / "papers"
    papers.mkdir()
    for name, data in existing:
        (papers / name).write_bytes(data)
    req = tmp_path / "REQUESTS.md"
    req.write_text(REQUESTS_STUB)
    return papers, req


def test_fetch_refuses_to_overwrite_and_makes_no_request(tmp_path, capsys):
    papers, req = fetch_env(
        tmp_path, [("brown2010-information-relaxations.pdf", b"%PDF-old")]
    )
    web = FakeWeb([])
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
        ],
        web,
        capsys,
    )
    assert code == 1 and "exists" in err
    assert (
        papers / "brown2010-information-relaxations.pdf"
    ).read_bytes() == b"%PDF-old"
    assert web.requests == []


def test_concurrent_fetch_of_one_name_never_publishes_foreign_bytes(tmp_path, capsys):
    # Parallel research agents can fetch one paper under one name. Worker B files
    # it while worker A is still downloading: A must neither overwrite B's file nor
    # claim it, so the file keeps the bytes B's printed provenance describes.
    papers, req = fetch_env(tmp_path)
    name = "brown2010-information-relaxations"
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["10.1287/opre.1090.0796", "--as", name]
    b_url = "https://faculty.example/brown/ir.pdf"
    worker_b = {}

    def worker_b_files_first():
        web_b = FakeWeb(
            [
                oa_route(fixture_json("oa_work_brown2010.json")),
                ("faculty.example/brown/ir.pdf", ok(b"%PDF-1.6 worker B")),
            ]
        )
        worker_b["run"] = run(argv + ["--url", b_url], web_b, capsys)
        return ok(b"%PDF-1.4 worker A")

    work = with_pdf_location(
        fixture_json("oa_work_brown2010.json"), "https://repo.example/brown2010.pdf"
    )
    web_a = FakeWeb(
        [
            oa_route(work),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            ("repo.example/brown2010.pdf", worker_b_files_first),
        ]
    )
    code, out, err = run(argv, web_a, capsys)
    code_b, out_b, err_b = worker_b["run"]
    assert code_b == 0, err_b
    assert f"| {b_url} |" in out_b
    assert code == 1 and "was filed by another process meanwhile" in err
    assert out == ""  # A claims nothing: no "filed" line, no index row
    assert (papers / f"{name}.pdf").read_bytes() == b"%PDF-1.6 worker B"
    assert sorted(p.name for p in papers.iterdir()) == [f"{name}.pdf"]  # no .part


def test_a_filed_pdf_gets_the_usual_mode_and_no_temporary_file_stays(tmp_path):
    # The bytes pass through mkstemp's 0600 file and the hard link keeps its inode,
    # so without a chmod every filed PDF would be unreadable to group and others.
    target = tmp_path / "x2020-y.pdf"
    lit.publish(target, b"%PDF-1.4")
    umask = os.umask(0)
    os.umask(umask)
    assert stat.S_IMODE(target.stat().st_mode) == 0o666 & ~umask
    assert [p.name for p in tmp_path.iterdir()] == ["x2020-y.pdf"]


def test_publish_never_replaces_a_file_already_filed(tmp_path):
    # The guarantee the os.link publication exists for: a publication by
    # os.replace (or rename) would overwrite the file another process filed.
    target = tmp_path / "x2020-y.pdf"
    target.write_bytes(b"%PDF-1.4 filed first")
    with pytest.raises(lit.LitError) as e:
        lit.publish(target, b"%PDF-1.4 filed second")
    assert "was filed by another process meanwhile" in str(e.value)
    assert target.read_bytes() == b"%PDF-1.4 filed first"
    assert [p.name for p in tmp_path.iterdir()] == ["x2020-y.pdf"]  # no .part


def test_a_filesystem_failure_while_filing_is_a_one_line_error(tmp_path, monkeypatch):
    # No such directory, or a filesystem without hard links: LitError's one-line
    # contract, not a traceback, and no temporary file left behind.
    with pytest.raises(lit.LitError) as e:
        lit.publish(tmp_path / "missing" / "x2020-y.pdf", b"%PDF-1.4")
    assert "\n" not in str(e.value)

    def no_hard_links(src, dst):
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(lit.os, "link", no_hard_links)
    with pytest.raises(lit.LitError) as e:
        lit.publish(tmp_path / "x2020-y.pdf", b"%PDF-1.4")
    assert "\n" not in str(e.value)
    assert list(tmp_path.iterdir()) == []


def test_fetch_skips_a_non_pdf_candidate_and_files_the_next(tmp_path, capsys):
    papers, req = fetch_env(tmp_path)
    work = with_pdf_location(
        fixture_json("oa_work_brown2010.json"), "https://repo.example/brown2010.pdf"
    )
    web = FakeWeb(
        [
            oa_route(work),
            (
                "api.unpaywall.org",
                ok(upw_with_pdf("https://upw.example/brown2010.pdf")),
            ),
            ("repo.example/brown2010.pdf", ok(b"<!DOCTYPE html><html>login</html>")),
            ("upw.example/brown2010.pdf", ok(b"%PDF-1.4 the paper")),
        ]
    )
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
        ],
        web,
        capsys,
    )
    assert code == 0, err
    assert (
        papers / "brown2010-information-relaxations.pdf"
    ).read_bytes() == b"%PDF-1.4 the paper"
    assert (
        "| brown2010-information-relaxations.pdf | Operations Research 2010, pp. 785–801 | "
        "https://upw.example/brown2010.pdf |"
    ) in out
    assert req.read_text() == REQUESTS_STUB


HANDLE = "http://hdl.handle.net/10161/4435"  # the fixtures' open-access landing page
REPOSITORY_PAGE = "https://dukespace.example/handle/10161/4435"  # where it resolves


def landing_page(pdf_url):
    meta = f'<meta name="citation_pdf_url" content="{pdf_url}">'
    return ok(f"<html><head>{meta}</head></html>".encode(), final_url=REPOSITORY_PAGE)


def test_a_candidate_whose_answer_breaks_off_falls_through_to_the_next(
    tmp_path, capsys
):
    # A hung repository server: the timeout must cost that candidate only, not the
    # fetch — Unpaywall's copy is next.
    papers, req = fetch_env(tmp_path)
    work = with_pdf_location(
        fixture_json("oa_work_brown2010.json"), "https://repo.example/brown2010.pdf"
    )
    web = FakeWeb(
        [
            oa_route(work),
            (
                "api.unpaywall.org",
                ok(upw_with_pdf("https://upw.example/brown2010.pdf")),
            ),
            ("repo.example/brown2010.pdf", raises(socket.timeout("timed out"))),
            ("upw.example/brown2010.pdf", ok(b"%PDF-1.4 the Unpaywall copy")),
        ]
    )
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["10.1287/opre.1090.0796", "--as", "brown2010-information-relaxations"]
    code, out, err = run(argv, web, capsys)
    assert code == 0, err
    assert (
        papers / "brown2010-information-relaxations.pdf"
    ).read_bytes() == b"%PDF-1.4 the Unpaywall copy"
    assert "note: " in err and "https://repo.example/brown2010.pdf" in err


def fetch_brown2010(papers, req, web, capsys):
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["10.1287/opre.1090.0796", "--as", "brown2010-information-relaxations"]
    return run(argv, web, capsys)


def test_a_page_naming_an_unparsable_pdf_link_falls_through_to_the_next_candidate(
    tmp_path, capsys
):
    # An unclosed IPv6 bracket in a citation_pdf_url makes urljoin raise ValueError:
    # it must cost that page only, not the fetch — Unpaywall's copy is next.
    papers, req = fetch_env(tmp_path)
    work = with_pdf_location(
        fixture_json("oa_work_brown2010.json"), "https://repo.example/brown2010.pdf"
    )
    meta = '<meta name="citation_pdf_url" content="https://[repo.example/x.pdf">'
    web = FakeWeb(
        [
            oa_route(work),
            (
                "api.unpaywall.org",
                ok(upw_with_pdf("https://upw.example/brown2010.pdf")),
            ),
            (
                "repo.example/brown2010.pdf",
                ok(f"<html><head>{meta}</head></html>".encode()),
            ),
            ("upw.example/brown2010.pdf", ok(b"%PDF-1.4 the Unpaywall copy")),
        ]
    )
    code, out, err = fetch_brown2010(papers, req, web, capsys)
    assert code == 0, err
    assert (
        papers / "brown2010-information-relaxations.pdf"
    ).read_bytes() == b"%PDF-1.4 the Unpaywall copy"
    assert "note: https://repo.example/brown2010.pdf names a PDF link" in err


def test_a_non_ascii_pdf_link_is_sent_percent_encoded_and_files(tmp_path, capsys):
    # A repository naming its PDF by an IRI (a non-ASCII file name, a space): sent as
    # written, http.client cannot encode the request line; percent-encoded, as a
    # browser sends it, the PDF files — under the URL as sent.
    papers, req = fetch_env(tmp_path)
    sent = "https://dukespace.example/bitstream/10161/4435/M%C3%BCller%20paper.pdf"
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            (
                "hdl.handle.net/10161/4435",
                landing_page("/bitstream/10161/4435/Müller paper.pdf"),
            ),
            ("dukespace.example/bitstream/", ok(b"%PDF-1.5 repository copy")),
        ]
    )
    code, out, err = fetch_brown2010(papers, req, web, capsys)
    assert code == 0, err
    assert web.urls()[-1] == sent
    assert f"| {sent} |" in out


IDN = {  # a Unicode host, and the ASCII form the Host header must carry
    "plain": ("https://bücher.example/x.pdf", "https://xn--bcher-kva.example/x.pdf"),
    "port": (
        "https://bücher.example:8443/x.pdf",
        "https://xn--bcher-kva.example:8443/x.pdf",
    ),
}


@pytest.mark.parametrize("given,sent", IDN.values(), ids=IDN.keys())
def test_fetch_url_on_a_unicode_host_is_sent_in_its_ascii_form(
    given, sent, tmp_path, capsys
):
    # urllib writes the host into the Host header as given, so a Unicode host goes
    # out IDNA-encoded, its port kept — not refused as a bad URL.
    papers, req = fetch_env(tmp_path)
    web = FakeWeb([("xn--bcher-kva.example", ok(b"%PDF-1.4 the copy"))])
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["--url", given, "--as", "x2020-idn-host"]
    code, out, err = run(argv, web, capsys)
    assert code == 0, err
    assert web.urls() == [sent] and f"| {sent} |" in out


def test_a_candidate_and_its_pdf_link_on_a_unicode_host_are_followed(tmp_path, capsys):
    # An OpenAlex location on an IDN host, whose page names its PDF on that host:
    # both are sent IDNA-encoded, and the same-host rule compares the one form.
    papers, req = fetch_env(tmp_path)
    work = with_pdf_location(
        fixture_json("oa_work_brown2010.json"), "https://bücher.example/handle/1.pdf"
    )
    meta = '<meta name="citation_pdf_url" content="https://bücher.example/b/1.pdf">'
    pdf = "https://xn--bcher-kva.example/b/1.pdf"
    web = FakeWeb(
        [
            oa_route(work),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            (
                "xn--bcher-kva.example/handle/1.pdf",
                ok(f"<html><head>{meta}</head></html>".encode()),
            ),
            ("xn--bcher-kva.example/b/1.pdf", ok(b"%PDF-1.5 the IDN copy")),
            ("hdl.handle.net/10161/4435", ok(fixture("landing_anubis.html"))),
        ]
    )
    code, out, err = fetch_brown2010(papers, req, web, capsys)
    assert code == 0, err
    assert (
        papers / "brown2010-information-relaxations.pdf"
    ).read_bytes() == b"%PDF-1.5 the IDN copy"
    assert f"| {pdf} |" in out


def test_gzip_encoded_landing_page_is_decoded_and_followed(tmp_path, capsys):
    # Left compressed, the page's citation_pdf_url is missed and an open paper is
    # queued as closed.
    papers, req = fetch_env(tmp_path)
    pdf = "https://dukespace.example/bitstream/10161/4435/paper.pdf"
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            ("hdl.handle.net/10161/4435", gzipped(landing_page(pdf))),
            ("dukespace.example/bitstream/", ok(b"%PDF-1.5 repository copy")),
        ]
    )
    code, out, err = fetch_brown2010(papers, req, web, capsys)
    assert code == 0, err
    assert (
        papers / "brown2010-information-relaxations.pdf"
    ).read_bytes() == b"%PDF-1.5 repository copy"
    assert f"{pdf} |" in out


def test_a_gzip_body_sent_without_content_encoding_is_decoded(tmp_path, capsys):
    # OJS (ojs.aaai.org, for one) gzips its pages without saying so: no
    # Content-Encoding, the body opening with gzip's magic bytes.
    papers, req = fetch_env(tmp_path)
    pdf = "https://dukespace.example/bitstream/10161/4435/paper.pdf"
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            ("hdl.handle.net/10161/4435", gzipped(landing_page(pdf), coding=None)),
            (
                "dukespace.example/bitstream/",
                gzipped(ok(b"%PDF-1.5 repository copy"), coding=None),
            ),
        ]
    )
    code, out, err = fetch_brown2010(papers, req, web, capsys)
    assert code == 0, err
    assert (
        papers / "brown2010-information-relaxations.pdf"
    ).read_bytes() == b"%PDF-1.5 repository copy"


def test_fetch_follows_a_landing_page_to_its_pdf(tmp_path, capsys):
    papers, req = fetch_env(tmp_path)
    pdf = "https://dukespace.example/bitstream/10161/4435/paper.pdf"
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            ("hdl.handle.net/10161/4435", landing_page(pdf)),
            ("dukespace.example/bitstream/", ok(b"%PDF-1.5 repository copy")),
        ]
    )
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
        ],
        web,
        capsys,
    )
    assert code == 0, err
    assert (
        (papers / "brown2010-information-relaxations.pdf")
        .read_bytes()
        .startswith(b"%PDF-1.5")
    )
    assert f"{pdf} |" in out
    # the page and the link it names are both held to their host (SafeRedirect)
    held = {r.full_url: getattr(r, "same_host_only", False) for r in web.requests}
    assert held[HANDLE] and held[pdf]


def test_landing_meta_pointing_to_another_host_is_not_followed(tmp_path, capsys):
    # Open access was vouched for the repository's host, not for whatever its page
    # names: a citation_pdf_url on a publisher's host is the closed copy, which a
    # campus network would be served by IP authentication.
    papers, req = fetch_env(tmp_path)
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            (
                "hdl.handle.net/10161/4435",
                landing_page("https://publisher.example/closed.pdf"),
            ),
            ("publisher.example/closed.pdf", ok(b"%PDF-1.4 the paywalled version")),
        ]
    )
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
        ],
        web,
        capsys,
    )
    assert code == 3
    assert not any("publisher.example" in u for u in web.urls())
    assert list(papers.iterdir()) == []


def test_fetch_url_takes_only_the_pdf_itself_never_a_link_its_page_names(
    tmp_path, capsys
):
    # `--url` vouches for one PDF. A publisher's abstract page names the paywalled
    # PDF in citation_pdf_url, and a campus network would be served it by IP.
    papers, req = fetch_env(tmp_path)
    abstract = "https://pubsonline.informs.org/doi/abs/10.1287/opre.1090.0796"
    paywalled = "https://pubsonline.informs.org/doi/pdf/10.1287/opre.1090.0796"
    meta = f'<meta name="citation_pdf_url" content="{paywalled}">'
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("informs.org/doi/abs/", ok(f"<html><head>{meta}</head></html>".encode())),
            ("informs.org/doi/pdf/", ok(b"%PDF-1.4 the paywalled version")),
        ]
    )
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["10.1287/opre.1090.0796", "--as", "brown2010-information-relaxations"]
    code, out, err = run(argv + ["--url", abstract], web, capsys)
    assert code == 3
    assert paywalled not in web.urls()
    assert list(papers.iterdir()) == []


def test_a_vouched_pdf_url_redirected_to_another_host_is_not_read_for_links(
    tmp_path, capsys
):
    # OpenAlex vouched for the repository's PDF URL, not for the publisher page a
    # redirect lands on, nor for the PDF link that page names.
    papers, req = fetch_env(tmp_path)
    work = with_pdf_location(
        fixture_json("oa_work_brown2010.json"), "https://repo.example/brown2010.pdf"
    )
    meta = '<meta name="citation_pdf_url" content="https://publisher.example/pdf/x">'
    publisher_page = ok(
        f"<html><head>{meta}</head></html>".encode(),
        final_url="https://publisher.example/abs/x",
    )
    web = FakeWeb(
        [
            oa_route(work),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            ("repo.example/brown2010.pdf", publisher_page),
            ("repo.example/brown2010", ok(b"<html>the repository record</html>")),
            ("hdl.handle.net/10161/4435", ok(fixture("landing_anubis.html"))),
            ("publisher.example/pdf/x", ok(b"%PDF-1.4 the paywalled version")),
        ]
    )
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["10.1287/opre.1090.0796", "--as", "brown2010-information-relaxations"]
    code, out, err = run(argv, web, capsys)
    assert code == 3
    assert not any("publisher.example/pdf" in u for u in web.urls())
    assert list(papers.iterdir()) == []


def test_closed_paper_is_queued_with_the_next_number_and_nothing_on_disk(
    tmp_path, capsys
):
    papers, req = fetch_env(tmp_path)
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            ("hdl.handle.net/10161/4435", ok(fixture("landing_anubis.html"))),
        ]
    )
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
            "--queue",
            "--needed-by",
            "T1",
            "--why",
            "settles the penalty construction",
        ],
        web,
        capsys,
    )
    assert code == 3
    assert list(papers.iterdir()) == []
    last = req.read_text().rstrip("\n").splitlines()[-1]
    assert last == (
        "| 3 | https://doi.org/10.1287/opre.1090.0796 | Information Relaxations and Duality in Stochastic Dynamic "
        "Programs (Brown, Smith, Sun; Operations Research, 2010) → `brown2010-information-relaxations.pdf` | T1 | "
        "settles the penalty construction | open |"
    )


def test_queue_refuses_a_row_when_unpaywall_could_not_be_asked(tmp_path, capsys):
    # An Unpaywall outage leaves "closed" unestablished: a row would send the owner
    # to the library for a paper that may be open. Its 404 is an answer, and still
    # queues (the test below).
    papers, req = fetch_env(tmp_path)
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", fail(503)),
            ("hdl.handle.net/10161/4435", ok(fixture("landing_anubis.html"))),
        ]
    )
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["10.1287/opre.1090.0796", "--as", "brown2010-information-relaxations"]
    argv += ["--queue", "--needed-by", "T1", "--why", "settles the penalty"]
    code, out, err = run(argv, web, capsys)
    assert code == 1
    assert (
        "error: not queued — Unpaywall could not be asked (unpaywall: HTTP 503 for "
        "https://api.unpaywall.org/v2/10.1287/opre.1090.0796" in err
    )
    assert err.rstrip("\n").endswith("after 3 attempts); retry before queueing")
    assert req.read_text() == REQUESTS_STUB and list(papers.iterdir()) == []


def test_fetch_never_requests_a_closed_publisher_page(tmp_path, capsys):
    # A publisher page reached from a campus network can serve the paywalled PDF by IP
    # authentication — automated library access the licences forbid. Only open-access
    # locations are ever followed.
    papers, req = fetch_env(tmp_path)
    work = fixture_json("oa_work_brown2010.json")
    work["locations"][0][
        "landing_page_url"
    ] = "https://pubsonline.informs.org/doi/10.1287/opre.1090.0796"
    assert work["locations"][0]["is_oa"] is False
    web = FakeWeb(
        [
            oa_route(work),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            ("hdl.handle.net/10161/4435", ok(fixture("landing_anubis.html"))),
        ]
    )
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
        ],
        web,
        capsys,
    )
    assert code == 3
    assert not any("informs.org" in u for u in web.urls())


def test_closed_paper_without_queue_writes_nothing(tmp_path, capsys):
    papers, req = fetch_env(tmp_path)
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("api.unpaywall.org", ok(fixture_json("upw_brown2010.json"))),
            ("hdl.handle.net/10161/4435", ok(fixture("landing_anubis.html"))),
        ]
    )
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
        ],
        web,
        capsys,
    )
    assert code == 3 and "closed" in out
    assert list(papers.iterdir()) == [] and req.read_text() == REQUESTS_STUB


def test_concurrent_queue_appends_get_distinct_numbers(tmp_path, monkeypatch):
    # Parallel research agents may queue closed papers at the same moment: the
    # number is read and the row written under one lock. The hook holds the first
    # append between its read and its write while a second one runs — without the
    # lock both would read the same table and claim #3.
    req = tmp_path / "REQUESTS.md"
    req.write_text(REQUESTS_STUB)
    real, started, got = lit.next_request_number, threading.Event(), {}

    def second():
        got["b"] = lit.append_request(req, lambda k: f"| {k} | second |")

    def hooked(text):
        n = real(text)
        if not started.is_set():
            started.set()
            got["thread"] = threading.Thread(target=second)
            got["thread"].start()
            time.sleep(0.3)
        return n

    monkeypatch.setattr(lit, "next_request_number", hooked)
    got["a"] = lit.append_request(req, lambda k: f"| {k} | first |")
    got["thread"].join(5)
    assert (got["a"], got["b"]) == (3, 4)
    assert req.read_text().endswith("| 3 | first |\n| 4 | second |\n")


def test_queueing_into_a_missing_queue_file_is_an_error_not_a_headerless_file(
    tmp_path,
):
    # Opened to append, a mistyped --requests path would become a one-row file with
    # no table header.
    missing = tmp_path / "REQUESTS.md"
    with pytest.raises(lit.LitError) as e:
        lit.append_request(missing, lambda k: f"| {k} | row |")
    assert str(e.value) == (
        f"{missing} does not exist — the queue file carries the table header"
    )
    assert not missing.exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root writes a 0444 file")
def test_an_unwritable_queue_file_is_a_one_line_error(tmp_path):
    # Not only a missing file: a read-only one (or a directory) must not end in a
    # traceback out of main().
    req = tmp_path / "REQUESTS.md"
    req.write_text(REQUESTS_STUB, encoding="utf-8")
    req.chmod(0o444)
    with pytest.raises(lit.LitError) as e:
        lit.append_request(req, lambda k: f"| {k} | row |")
    assert str(e.value).startswith(f"cannot open {req}: ")
    assert "\n" not in str(e.value)
    assert req.read_text(encoding="utf-8") == REQUESTS_STUB


def test_a_doi_openalex_does_not_know_still_reaches_unpaywall_and_the_queue(
    tmp_path, capsys
):
    # OpenAlex lacks some DOIs (the book-form 10.1561/9781680839630, for one), and
    # the queue is the only channel research agents have for such a paper.
    papers, req = fetch_env(tmp_path)
    web = FakeWeb([("api.openalex.org", fail(404)), ("api.unpaywall.org", fail(404))])
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["10.1561/9781680839630", "--as", "x2020-book-form-doi", "--queue"]
    argv += ["--needed-by", "T5", "--why", "the distillation bound"]
    code, out, err = run(argv, web, capsys)
    assert code == 3, err
    assert any("api.unpaywall.org/v2/10.1561/9781680839630" in u for u in web.urls())
    assert len([u for u in web.urls() if "openalex" in u]) == 1  # no second lookup
    last = req.read_text().rstrip("\n").splitlines()[-1]
    assert last == (
        "| 3 | https://doi.org/10.1561/9781680839630 | 10.1561/9781680839630 → "
        "`x2020-book-form-doi.pdf` | T5 | the distillation bound | open |"
    )


PMLR_PDF = "https://proceedings.mlr.press/v37/perolat15.pdf"


def test_fetch_url_without_identifier_files_and_prints_a_placeholder_row(
    tmp_path, capsys
):
    # A PMLR paper or a technical report has no DOI or arXiv id: the PDF is filed
    # from its URL alone, nothing is looked up, and the §6 row's middle column is
    # left for the agent to fill in.
    papers, req = fetch_env(tmp_path)
    web = FakeWeb([("proceedings.mlr.press/v37/", ok(b"%PDF-1.4 the PMLR copy"))])
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["--url", PMLR_PDF, "--as", "perolat2015-adp-zero-sum-markov-games"]
    code, out, err = run(argv, web, capsys)
    assert code == 0, err
    assert (
        papers / "perolat2015-adp-zero-sum-markov-games.pdf"
    ).read_bytes() == b"%PDF-1.4 the PMLR copy"
    assert f"| perolat2015-adp-zero-sum-markov-games.pdf | ? | {PMLR_PDF} |" in out
    assert web.urls() == [PMLR_PDF]  # the PDF alone: no metadata lookup


def test_fetch_url_without_identifier_files_pdf_bytes_only(tmp_path, capsys):
    papers, req = fetch_env(tmp_path)
    web = FakeWeb([("tr.example/", ok(b"<!DOCTYPE html><html>a catalogue page"))])
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["--url", "https://tr.example/lids-p-2005", "--as", "x2005-lids-report"]
    code, out, err = run(argv, web, capsys)
    assert code == 3 and list(papers.iterdir()) == []


def test_fetch_needs_an_identifier_or_a_url(tmp_path, capsys):
    papers, req = fetch_env(tmp_path)
    web = FakeWeb([])
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    with pytest.raises(SystemExit) as e:
        run(argv + ["--as", "x2020-y"], web, capsys)
    assert e.value.code == 2  # usage
    assert "--url" in capsys.readouterr().err.splitlines()[-1]  # says what is missing
    assert web.requests == []


def fetch_usage_error(argv, web, capsys):
    """Run a fetch that must be refused as a usage error: (exit code, stderr)."""
    with pytest.raises(SystemExit) as e:
        run(argv, web, capsys)
    return e.value.code, capsys.readouterr().err


def test_a_fetch_usage_error_prints_fetchs_usage_not_the_roots(tmp_path, capsys):
    # The root parser's usage line lists the verbs, not fetch's options.
    papers, req = fetch_env(tmp_path)
    argv = ["--papers", str(papers), "--requests", str(req), "fetch", "--as", "x2020-y"]
    code, err = fetch_usage_error(argv, FakeWeb([]), capsys)
    assert code == 2 and err.startswith("usage: lit.py fetch [-h] --as NAME")
    assert "lit.py fetch: error: fetch needs a DOI or arXiv id" in err


@pytest.mark.parametrize("ident", ["", "  "], ids=["empty", "blank"])
def test_an_empty_identifier_is_a_usage_error_not_an_id_less_filing(
    ident, tmp_path, capsys
):
    # Read as no identifier, `fetch ""` would file the PDF id-less.
    papers, req = fetch_env(tmp_path)
    web = FakeWeb([("host.example", ok(b"%PDF-1.4"))])
    argv = ["--papers", str(papers), "--requests", str(req), "fetch", ident]
    argv += ["--as", "x2020-y", "--url", "https://host.example/p.pdf"]
    code, err = fetch_usage_error(argv, web, capsys)
    assert code == 2 and err.startswith("usage: lit.py fetch ")
    assert "an empty identifier" in err
    assert web.requests == [] and list(papers.iterdir()) == []


@pytest.mark.parametrize(
    "link",
    [
        "https://doi.org/10.1287/opre.1090.0796",
        "http://dx.doi.org/10.1287/opre.1090.0796",
        "https://DOI.org/10.1287/opre.1090.0796",
    ],
    ids=["doi.org", "dx.doi.org", "upper-case"],
)
def test_fetch_url_refuses_a_doi_link(link, tmp_path, capsys):
    # A DOI that resolves straight to a PDF would file the publisher's copy under
    # the DOI as provenance; --url names the PDF itself.
    papers, req = fetch_env(tmp_path)
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("doi.org/", ok(b"%PDF-1.4 the publisher's copy")),
            ("DOI.org/", ok(b"%PDF-1.4 the publisher's copy")),
        ]
    )
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["10.1287/opre.1090.0796", "--as", "brown2010-information-relaxations"]
    code, err = fetch_usage_error(argv + ["--url", link], web, capsys)
    assert code == 2 and err.startswith("usage: lit.py fetch ")
    assert "--url names the PDF itself, never a DOI link" in err
    assert web.requests == [] and list(papers.iterdir()) == []


BAD_URL_FLAGS = {**BAD_URLS, "empty": ""}


@pytest.mark.parametrize("url", BAD_URL_FLAGS.values(), ids=BAD_URL_FLAGS.keys())
def test_a_malformed_url_flag_is_a_usage_error_and_queues_nothing(
    url, tmp_path, capsys
):
    # A --url urllib cannot send ended as a note and "closed" (exit 3) — and with
    # --queue as a REQUESTS row for a paper nobody checked. Refused before any
    # request, the metadata lookup included.
    papers, req = fetch_env(tmp_path)
    web = FakeWeb([oa_route(fixture_json("oa_work_brown2010.json"))])
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["10.1287/opre.1090.0796", "--as", "brown2010-information-relaxations"]
    argv += ["--url", url, "--queue", "--needed-by", "T1", "--why", "the penalty"]
    code, err = fetch_usage_error(argv, web, capsys)
    assert code == 2 and err.startswith("usage: lit.py fetch ")
    last = err.rstrip("\n").splitlines()[-1]  # one line, whatever the URL holds
    assert last.startswith(f"lit.py fetch: error: bad --url {url!r}: ")
    assert web.requests == [] and list(papers.iterdir()) == []
    assert req.read_text() == REQUESTS_STUB


def test_an_arxiv_pdf_download_takes_the_arxiv_slot(tmp_path, capsys):
    # arXiv asks one address for 3 s between requests, PDFs included, and a burst
    # from parallel agents earns a temporary block.
    papers, req = fetch_env(tmp_path)
    clock = FakeClock()
    web = FakeWeb(
        [
            ("export.arxiv.org/api/query", ok(fixture("arxiv_search.xml"))),
            ("arxiv.org/pdf/1805.08328", ok(b"%PDF-1.5 the arXiv copy")),
        ],
        clock=clock,
    )
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["arXiv:1805.08328", "--as", "bastani2018-verifiable-rl"]
    code, out, err = run(argv, web, capsys, clock=clock)
    assert code == 0, err
    assert web.urls()[1] == "https://arxiv.org/pdf/1805.08328"
    assert web.times[1] - web.times[0] >= 3.0  # the metadata query, then the PDF


def test_queue_needs_an_identifier(tmp_path, capsys):
    # A queue row links the paper by its DOI or arXiv id, for the owner to find it.
    papers, req = fetch_env(tmp_path)
    web = FakeWeb([])
    argv = ["--papers", str(papers), "--requests", str(req), "fetch"]
    argv += ["--url", PMLR_PDF, "--as", "perolat2015-adp-zero-sum-markov-games"]
    argv += ["--queue", "--needed-by", "T2", "--why", "the sup-norm bound"]
    code, out, err = run(argv, web, capsys)
    assert code == 1 and "DOI or arXiv id" in err
    assert web.requests == [] and list(papers.iterdir()) == []
    assert req.read_text() == REQUESTS_STUB


def test_queue_needs_the_memo_and_the_reason(tmp_path, capsys):
    papers, req = fetch_env(tmp_path)
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
            "--queue",
            "--needed-by",
            "T1",
        ],
        FakeWeb([]),
        capsys,
    )
    assert code == 1 and "--why" in err
    assert req.read_text() == REQUESTS_STUB


def test_fetch_from_an_explicit_url_files_it_with_that_provenance(tmp_path, capsys):
    papers, req = fetch_env(tmp_path)
    web = FakeWeb(
        [
            oa_route(fixture_json("oa_work_brown2010.json")),
            ("faculty.example/brown/ir.pdf", ok(b"%PDF-1.6 author copy")),
        ]
    )
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
            "--url",
            "https://faculty.example/brown/ir.pdf",
        ],
        web,
        capsys,
    )
    assert code == 0, err
    assert (
        "| Operations Research 2010, pp. 785–801 | https://faculty.example/brown/ir.pdf |"
        in out
    )


UNPAYWALL_OUTAGES = {  # how the outage looks: the answer, and the attempts it costs
    "http-503": (fail(503), 3),
    "timeout-mid-body": (broken(socket.timeout("timed out")), 3),
    "truncated-body": (broken(http.client.IncompleteRead(b'{"doi": "10.', 400)), 3),
    "malformed-json": (ok(b"<!DOCTYPE html><html>Service Unavailable"), 1),
}


@pytest.mark.parametrize(
    "answer,attempts", UNPAYWALL_OUTAGES.values(), ids=UNPAYWALL_OUTAGES.keys()
)
def test_unpaywall_outage_does_not_block_an_openalex_pdf(
    answer, attempts, tmp_path, capsys
):
    # Unpaywall is the last fallback: its outage must not cost the copy OpenAlex
    # already named.
    papers, req = fetch_env(tmp_path)
    work = with_pdf_location(
        fixture_json("oa_work_brown2010.json"), "https://repo.example/brown2010.pdf"
    )
    web = FakeWeb(
        [
            oa_route(work),
            ("api.unpaywall.org", answer),
            ("repo.example/brown2010.pdf", ok(b"%PDF-1.4 the OpenAlex copy")),
        ]
    )
    code, out, err = run(
        [
            "--papers",
            str(papers),
            "--requests",
            str(req),
            "fetch",
            "10.1287/opre.1090.0796",
            "--as",
            "brown2010-information-relaxations",
        ],
        web,
        capsys,
    )
    assert len([u for u in web.urls() if "unpaywall" in u]) == attempts
    assert code == 0, err
    assert (
        papers / "brown2010-information-relaxations.pdf"
    ).read_bytes() == b"%PDF-1.4 the OpenAlex copy"
    assert "https://repo.example/brown2010.pdf |" in out
    assert "warning: unpaywall: " in err


# --------------------------------------------------------------------------- the CLI


def test_search_queries_openalex_with_select_and_the_key_in_a_header(capsys):
    web = FakeWeb([("api.openalex.org/works?", ok(fixture_json("oa_search.json")))])
    code, out, err = run(
        [
            "search",
            "information relaxations duality",
            "--n",
            "3",
            "--since",
            "2005",
            "--json",
        ],
        web,
        capsys,
    )
    assert code == 0, err
    assert [r["doi"] for r in json.loads(out)] == [
        "10.1287/opre.2014.1322",
        "10.1287/opre.1090.0796",
        "10.1287/opre.2018.1782",
    ]
    req = web.requests[0]
    assert (
        "select=" in req.full_url
        and "per-page=3" in req.full_url
        and "2005" in req.full_url
    )
    assert KEYS["OPENALEX_API_KEY"] not in req.full_url
    assert req.get_header("Authorization") == "Bearer " + KEYS["OPENALEX_API_KEY"]


def test_openalex_search_matches_titles_and_abstracts_not_full_text(capsys):
    # `search=` also matches full text (quantum spin chains for "information
    # relaxation dual bounds"); the title-and-abstract filter costs the same 10
    # credits. A comma would split the filter, so it is neutralised.
    web = FakeWeb([("api.openalex.org/works?", ok(fixture_json("oa_search.json")))])
    code, out, err = run(["search", "bounds, games", "--since", "2005"], web, capsys)
    assert code == 0, err
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(web.requests[0].full_url).query)
    assert "search" not in query
    assert query["filter"] == [
        "title_and_abstract.search:bounds  games,from_publication_date:2005-01-01"
    ]


def test_search_semantic_scholar_sends_its_key_in_a_header(capsys):
    web = FakeWeb(
        [
            (
                "api.semanticscholar.org/graph/v1/paper/search",
                ok(fixture_json("s2_search.json")),
            )
        ]
    )
    code, out, err = run(
        ["search", "stochastic shortest path error bound", "--source", "s2", "--json"],
        web,
        capsys,
    )
    assert code == 0, err
    assert json.loads(out)[0]["arxiv"] == "2605.22965"
    assert web.requests[0].get_header("X-api-key") == KEYS["SEMANTIC_SCHOLAR_API_KEY"]


def test_search_s2_without_a_key_is_a_clear_error_and_all_skips_it(capsys):
    cfg = dict(KEYS, SEMANTIC_SCHOLAR_API_KEY=None)
    code, out, err = run(
        ["search", "x", "--source", "s2"], FakeWeb([]), capsys, config=cfg
    )
    assert code == 1 and "SEMANTIC_SCHOLAR_API_KEY" in err
    web = FakeWeb(
        [
            ("api.openalex.org/works?", ok(fixture_json("oa_search.json"))),
            ("export.arxiv.org", ok(fixture("arxiv_search.xml"))),
        ]
    )
    code, out, err = run(
        ["search", "x", "--source", "all", "--json"], web, capsys, config=cfg
    )
    assert code == 0, err
    assert not any("semanticscholar" in u for u in web.urls())
    assert len(json.loads(out)) == 5


def test_search_all_deduplicates_across_sources(capsys):
    s2 = fixture_json("s2_search.json")
    s2["data"][0]["externalIds"] = {
        "DOI": "10.1287/OPRE.2014.1322"
    }  # the same paper as OpenAlex's first hit
    web = FakeWeb(
        [
            ("api.openalex.org/works?", ok(fixture_json("oa_search.json"))),
            ("api.semanticscholar.org", ok(s2)),
            ("export.arxiv.org", ok(fixture("arxiv_search.xml"))),
        ]
    )
    code, out, err = run(["search", "x", "--source", "all", "--json"], web, capsys)
    assert code == 0, err
    dois = [r["doi"] for r in json.loads(out) if r["doi"]]
    assert dois.count("10.1287/opre.2014.1322") == 1
    assert len(json.loads(out)) == 3 + 2 + 2


def test_refs_fetches_the_work_then_its_references_in_one_batch(capsys):
    web = FakeWeb(
        [
            (
                "api.openalex.org/works/doi:10.1287/opre.1090.0796",
                ok(fixture_json("oa_work_brown2010.json")),
            ),
            (
                "api.openalex.org/works?filter=openalex:",
                ok(fixture_json("oa_refs_batch.json")),
            ),
        ]
    )
    code, out, err = run(["refs", "10.1287/opre.1090.0796", "--json"], web, capsys)
    assert code == 0, err
    titles = [r["title"][:30] for r in json.loads(out)]
    assert titles[0].startswith("Lectures on Stochastic Program")  # most cited first
    batch = [u for u in web.urls() if "filter=openalex:" in u][0]
    assert "W" in batch and "|" in urllib.parse.unquote(batch)


def test_cites_filters_openalex_on_the_work_id(capsys):
    web = FakeWeb(
        [
            (
                "api.openalex.org/works/doi:10.1287/opre.1090.0796",
                ok(fixture_json("oa_work_brown2010.json")),
            ),
            (
                "api.openalex.org/works?filter=cites:W2151786492",
                ok(fixture_json("oa_search.json")),
            ),
        ]
    )
    code, out, err = run(
        ["cites", "10.1287/opre.1090.0796", "--n", "3", "--json"], web, capsys
    )
    assert code == 0, err
    assert len(json.loads(out)) == 3


def test_refs_from_semantic_scholar_most_cited_first(capsys):
    web = FakeWeb(
        [
            (
                "graph/v1/paper/DOI:10.1287/opre.1090.0796/references",
                ok(fixture_json("s2_refs.json")),
            )
        ]
    )
    code, out, err = run(
        ["refs", "10.1287/opre.1090.0796", "--source", "s2", "--n", "2", "--json"],
        web,
        capsys,
    )
    assert code == 0, err
    assert [r["title"] for r in json.loads(out)] == [
        "Game theory.",
        "Pricing American Options: A Duality Approach",
    ]


def test_the_docstring_names_exactly_the_verbs_that_take_json():
    # --help prints the module docstring, so it must name the verbs that take --json
    # and no other: budget and check take none.
    parser = lit.build_parser()
    verbs = next(
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    ).choices
    with_json = {
        verb
        for verb, sub in verbs.items()
        if any("--json" in a.option_strings for a in sub._actions)
    }
    m = re.search(r"^(\w[\w, ]*) take --json\.", lit.__doc__, re.M)
    assert m, "the docstring names the verbs that take --json"
    assert set(re.split(r", | and ", m.group(1))) == with_json
    assert with_json == {"search", "refs", "cites", "resolve"}


def test_budget_prints_the_remaining_credits_and_the_reset(capsys):
    web = FakeWeb(
        [
            (
                "api.openalex.org",
                ok(
                    {"id": "W1"},
                    {"x-ratelimit-remaining": "9977", "x-ratelimit-reset": "83324"},
                ),
            )
        ]
    )
    code, out, err = run(["budget"], web, capsys)
    assert code == 0 and "9977" in out and "83324" in out


def test_keys_never_appear_in_output_even_on_failure(capsys):
    web = FakeWeb(
        [("api.openalex.org", fail(500)), ("api.semanticscholar.org", fail(403))]
    )
    code, out, err = run(["search", "x"], web, capsys)
    assert code == 1
    code2, out2, err2 = run(["search", "x", "--source", "s2"], web, capsys)
    assert code2 == 1
    for text in (out, err, out2, err2):
        assert (
            KEYS["OPENALEX_API_KEY"] not in text
            and KEYS["SEMANTIC_SCHOLAR_API_KEY"] not in text
        )


# --------------------------------------------------------------------------- check


def check_setup(tmp_path, monkeypatch, in_file=(), in_environment=(), mode=0o600):
    """A key file under tmp_path holding the KEYS named in `in_file`, at `mode`,
    named by LIT_ENV; the KEYS named in `in_environment` exported and the others
    unset. Returns the file and the config main() would load from them."""
    path = tmp_path / "lit.env"
    path.write_text(
        "".join(f": ${{{name}:={KEYS[name]}}}\n" for name in in_file),
        encoding="utf-8",
    )
    path.chmod(mode)
    monkeypatch.setenv("LIT_ENV", str(path))
    for name in lit.CONFIG_KEYS:
        if name in in_environment:
            monkeypatch.setenv(name, KEYS[name])
        else:
            monkeypatch.delenv(name, raising=False)
    return path, lit.load_config(dict(os.environ))


def check_routes(**answers):
    """The web for check's four calls — OpenAlex's budget call, the smallest search
    on Semantic Scholar and on arXiv, one Unpaywall lookup — each answered from the
    recorded fixtures (the budget call as the budget test answers it) unless
    `answers` names another answer: openalex=, s2=, arxiv=, unpaywall=."""
    answer = {
        "openalex": ok({"id": "W1"}, {"x-ratelimit-remaining": "9977"}),
        "s2": ok(fixture_json("s2_search.json")),
        "arxiv": ok(fixture("arxiv_search.xml")),
        "unpaywall": ok(fixture_json("upw_brown2010.json")),
    }
    answer.update(answers)
    return FakeWeb(
        [
            ("api.openalex.org/works/", answer["openalex"]),
            ("api.semanticscholar.org/graph/v1/paper/search", answer["s2"]),
            ("export.arxiv.org/api/query", answer["arxiv"]),
            ("api.unpaywall.org/v2/", answer["unpaywall"]),
        ]
    )


def test_check_exit_codes(tmp_path, monkeypatch, capsys):
    # Ready: the key file present, mode 600 and the user's; both required keys set
    # from it; every set key from it; every configured source answering one cheap
    # call. Exit 0, one line per component and no other.
    path, config = check_setup(tmp_path, monkeypatch, in_file=lit.CONFIG_KEYS)
    web = check_routes()
    code, out, err = run(["check"], web, capsys, config=config)
    assert code == 0, out + err
    assert out.splitlines() == [
        f"key file: {path}: present; mode 600; owner ok",
        "OPENALEX_API_KEY (required): set (file)",
        "SEMANTIC_SCHOLAR_API_KEY (optional): set (file)",
        "LIT_CONTACT_EMAIL (required): set (file)",
        "openalex: ok",
        "semantic-scholar: ok",
        "arxiv: ok",
        "unpaywall: ok",
    ]
    assert len(web.requests) == 4 and err == ""
    # One source failing through the opener: every line still printed, exit 1,
    # and the handoff's step 5 named last.
    web = check_routes(s2=fail(403))
    code, out, err = run(["check"], web, capsys, config=config)
    lines = out.splitlines()
    assert code == 1 and len(lines) == 9
    assert lines[5].startswith(
        "semantic-scholar: failing: HTTP 403 for https://api.semanticscholar.org/"
    )
    assert lines[6:8] == ["arxiv: ok", "unpaywall: ok"]
    assert lines[8] == "resume at step 5: a failing source"
    # --no-network: the key file and the keys alone, and no request.
    web = FakeWeb([])
    code, out, err = run(["check", "--no-network"], web, capsys, config=config)
    assert code == 0 and len(out.splitlines()) == 4 and web.requests == []


def test_check_reports_file_mode_and_owner(tmp_path, monkeypatch, capsys):
    # A key file another account can read, or one another account owns, is no
    # place for a key: either fails at the handoff's step 1, as a missing file does.
    path, config = check_setup(
        tmp_path, monkeypatch, in_file=lit.CONFIG_KEYS, mode=0o644
    )
    offline = ["check", "--no-network"]
    code, out, err = run(offline, FakeWeb([]), capsys, config=config)
    assert code == 1
    assert out.splitlines()[0] == (
        f"key file: {path}: present; mode 644 (insecure); owner ok"
    )
    assert out.splitlines()[-1] == "resume at step 1: the key file"
    path.chmod(0o600)
    code, out, err = run(offline, FakeWeb([]), capsys, config=config)
    assert code == 0
    assert out.splitlines()[0] == f"key file: {path}: present; mode 600; owner ok"
    path.unlink()
    code, out, err = run(offline, FakeWeb([]), capsys, config=config)
    assert code == 1
    assert out.splitlines()[0] == f"key file: {path}: missing"
    assert out.splitlines()[-1] == "resume at step 1: the key file"
    path, config = check_setup(tmp_path, monkeypatch, in_file=lit.CONFIG_KEYS)
    owner = path.stat().st_uid
    monkeypatch.setattr(lit.os, "getuid", lambda: owner + 1)  # another account runs it
    code, out, err = run(offline, FakeWeb([]), capsys, config=config)
    assert code == 1
    assert out.splitlines()[0] == (
        f"key file: {path}: present; mode 600; owner {owner} (not the user)"
    )
    assert out.splitlines()[-1] == "resume at step 1: the key file"


def test_check_prints_no_value(tmp_path, monkeypatch, capsys):
    # The report says where each key comes from, never what it is — on a failure
    # too, where a source's message names the URL it asked and Unpaywall's URL
    # carries the contact address.
    path, config = check_setup(
        tmp_path,
        monkeypatch,
        in_file=lit.CONFIG_KEYS,
        in_environment=("OPENALEX_API_KEY",),
    )
    web = check_routes(openalex=fail(401), unpaywall=fail(503))
    code, out, err = run(["check"], web, capsys, config=config)
    assert code == 1
    contact = urllib.parse.quote(CONTACT, safe="")
    assert any(contact in url for url in web.urls())  # sent to Unpaywall ...
    for text in (out, err):
        assert not [value for value in KEYS.values() if value in text]
        assert contact not in text  # ... and printed nowhere
    assert out.splitlines()[-2] == (
        f"unpaywall: failing: HTTP 503 for https://api.unpaywall.org/v2/{lit.CHECK_DOI}"
        "?email=<withheld> after 3 attempts"
    )


def test_check_reports_an_environment_only_key_as_not_persisted(
    tmp_path, monkeypatch, capsys
):
    # The tool reads the environment first, so a key exported in this shell works
    # here and is gone in the next one: check says so, and fails at the step that
    # appends that key to the key file. A key in both places is persisted.
    path, config = check_setup(
        tmp_path,
        monkeypatch,
        in_file=("SEMANTIC_SCHOLAR_API_KEY", "LIT_CONTACT_EMAIL"),
        in_environment=("OPENALEX_API_KEY",),
    )
    code, out, err = run(["check"], check_routes(), capsys, config=config)
    lines = out.splitlines()
    assert code == 1
    assert lines[1] == (
        "OPENALEX_API_KEY (required): set (environment only, not persisted)"
    )
    assert "openalex: ok" in lines  # the exported key answers, and still fails
    assert lines[-1] == "resume at step 2: the OpenAlex key"
    path, config = check_setup(
        tmp_path,
        monkeypatch,
        in_file=("OPENALEX_API_KEY", "LIT_CONTACT_EMAIL"),
        in_environment=("SEMANTIC_SCHOLAR_API_KEY",),
    )
    code, out, err = run(["check", "--no-network"], FakeWeb([]), capsys, config=config)
    assert code == 1
    assert out.splitlines()[2] == (
        "SEMANTIC_SCHOLAR_API_KEY (optional): set (environment only, not persisted)"
    )
    assert out.splitlines()[-1] == "resume at step 3: the Semantic Scholar key"
    path, config = check_setup(
        tmp_path, monkeypatch, in_file=lit.CONFIG_KEYS, in_environment=lit.CONFIG_KEYS
    )
    code, out, err = run(["check", "--no-network"], FakeWeb([]), capsys, config=config)
    assert code == 0 and "environment only" not in out


def test_check_fails_on_a_missing_required_key_naming_the_step(
    tmp_path, monkeypatch, capsys
):
    # An empty key file at mode 600 is step 1 done: the check then fails at the
    # first required key it lacks, whatever the sources say, and an optional key
    # left unset fails nothing.
    path, config = check_setup(tmp_path, monkeypatch)
    web = check_routes()
    code, out, err = run(["check"], web, capsys, config=config)
    assert code == 1
    assert out.splitlines() == [
        f"key file: {path}: present; mode 600; owner ok",
        "OPENALEX_API_KEY (required): unset",
        "SEMANTIC_SCHOLAR_API_KEY (optional): unset",
        "LIT_CONTACT_EMAIL (required): unset",
        "openalex: unconfigured",
        "semantic-scholar: unconfigured (optional)",
        "arxiv: ok",
        "unpaywall: unconfigured",
        "resume at step 2: the OpenAlex key",
    ]
    assert len(web.requests) == 1 and "export.arxiv.org" in web.urls()[0]
    path, config = check_setup(tmp_path, monkeypatch, in_file=("OPENALEX_API_KEY",))
    code, out, err = run(["check"], check_routes(), capsys, config=config)
    lines = out.splitlines()
    assert code == 1
    assert "openalex: ok" in lines
    assert "semantic-scholar: unconfigured (optional)" in lines
    assert lines[-1] == "resume at step 4: the contact address"


def test_check_reports_an_off_shape_answer_as_failing_without_a_traceback(
    tmp_path, monkeypatch, capsys
):
    # Valid JSON of the wrong shape — Semantic Scholar's recorded results as a bare
    # list, not the object that holds them — is no error the tool raises itself;
    # check still reports it as that source failing, prints every other line and
    # names the step, never a traceback.
    path, config = check_setup(tmp_path, monkeypatch, in_file=lit.CONFIG_KEYS)
    web = check_routes(s2=ok(fixture_json("s2_search.json")["data"]))
    code, out, err = run(["check"], web, capsys, config=config)
    assert code == 1 and err == ""
    assert out.splitlines()[4:] == [
        "openalex: ok",
        "semantic-scholar: failing: AttributeError",
        "arxiv: ok",
        "unpaywall: ok",
        "resume at step 5: a failing source",
    ]
