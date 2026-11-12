"""The pack's own checks: what every file under the pack must satisfy at every release.

They are public, so they screen for shapes, never for names. Each addition to the pack appends its checks here.
The file runs wherever the pack does, in the repository that holds it and in a release clone alike, so it looks at
the pack and never above it. Python 3.9 or later; the standard library and pytest only.
"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[1]
STARTER = PACK / "starter"
PROCESS = STARTER / "docs" / "process.md"

# The documented placeholders and only them. A token is two braces, an upper-case name and two braces.
PLACEHOLDERS = {
    "PROJECT",
    "OWNER",
    "REPO_URL",
    "PACKAGE",
    "TEST_COMMAND",
    "LINT_COMMAND",
    "INTERPRETER",
    "QUOIN_VERSION",
}
TOKEN = re.compile(r"\{\{([A-Z_]+)\}\}")

# A fill comment is one line: what the adopter fills, a semicolon, the rule the fill follows. FILL_OPEN finds every
# comment that starts like one, so a malformed comment cannot slip past by missing the grammar's first characters.
FILL = re.compile(r"<!-- fill: [^>]+ -->")
FILL_OPEN = re.compile(r"<!--\s*fill\b", re.IGNORECASE)

# The shapes of an address and of a key or a token, which appear nowhere in the pack. This file's own text matches
# none of them; an example needed by a test is built at run time from pieces.
SHAPES = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "openai-key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "github-token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,}"),
    "aws-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "slack-token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
}

# The starter's document checker reads links this way: a line that starts with three backticks or three tildes
# opens or closes a fence, and every other line outside a fence has its code spans removed before its links are read.
FENCES = ("```", "~~~")
CODE_SPAN = re.compile(r"`[^`]*`")
LINK = re.compile(r"\]\(([^)\s]+)\)")
SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]+:")

SKIPPED_DIRS = {".git", "__pycache__", ".pytest_cache"}

# The contract's shape: every `## ` and `### ` heading of the starter's process.md, exact and in order. The other
# starter files cite these sections by name.
PROCESS_HEADINGS = [
    "## Purpose and principles",
    "## Session types",
    "### I. Ideation session",
    "### II. The loop — one item, two sessions",
    "### III. Survey session",
    "### Small-change lane",
    "## Adversarial review protocol",
    "### The gate transitions",
    "## Handoff economics",
    "## Doc taxonomy",
    "## Canonical and pointer sites",
    "## Model policy",
    "### The binding table",
    "### The seats",
    "### Counsel triggers",
    "### The cap",
    "### Dispatch",
    "## Roadmap upkeep",
    "## Budgets",
    "## Conventions",
    "## History",
    "## Extension — measurement work",
    "## Extension — plans verified in an overlay",
]

# The extensions: sections an adopter keeps or deletes whole, each opening with the sentence that says when to adopt
# it. The core never refers to one, so deleting either leaves nothing dangling.
EXTENSIONS = ("## Extension — measurement work", "## Extension — plans verified in an overlay")
ADOPTION = "Adopt this extension when"

# A deleted extension's own vocabulary, which nothing left behind may use: the measurement extension's counsel
# triggers 7–9, named alone or as the end of a range ("triggers 1–9").
EXTENSION_TRACES = {EXTENSIONS[0]: re.compile(r"triggers? (?:[1-6][–-])?[7-9]\b|7–9", re.IGNORECASE)}

# process.md's word budget, counted as the budget check counts words: whitespace-split tokens.
PROCESS_WORDS = 10_500
# The starter's document check. The pack's tests load it by its path and run it as `python3 -I <path>`, since they
# cannot import the starter as a package.
DOC_BUDGETS = STARTER / "tools" / "doc_budgets.py"

# A `(#anchor)` in process.md, and a link into process.md from anywhere in the starter, as raw text: a reference a
# reader can follow is checked whether or not it sits in code.
ANCHOR_LINK = re.compile(r"\(#([^)\s]*)\)")
PROCESS_ANCHOR = re.compile(r"process\.md#([\w-]+)")

# The boot files and document stubs the starter ships besides process.md, the seat charters, the runbooks, the tools
# and the skeletons, relative to the starter. Each is complete as shipped: its sections and its rules of upkeep, with
# placeholders and fill comments where a project's facts go.
BOOT_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    ".gitignore",
    "docs/process-log.md",
    "docs/roadmap.md",
    "docs/id-registry.md",
    "docs/designs/.gitkeep",
    "docs/plans/README.md",
    "docs/handoffs/README.md",
    "docs/explainers/00-index.md",
]
KEPT_EMPTY = {"docs/designs/.gitkeep"}

# The gate's launcher, a bash script the starter ships executable, and the starter's two runbooks. The launcher is run
# as `bash <path>` from a path built from this file, never from the working directory: the pack's tests also run in a
# release clone, where there is no `pack/`. The gate transition table is process.md's alone; its header row is what a
# runbook would carry if it copied the table instead of citing it.
GATE = STARTER / "tools" / "codex_gate.sh"
RUNBOOKS = STARTER / "docs" / "runbooks"
RUNBOOK_NAMES = ("codex-gate.md", "worktree-sessions.md")
TABLE_HEADER = "| Event |"

# The research stack (process.md §III). The survey document ships its six sections, each opening with its one-line
# upkeep rule and holding nothing else but the sweep log's and the index's table headers; the papers index is §6,
# where `tools/lit.py index` reads it. The queue ends with its table, since `lit.py fetch --queue` appends its rows
# at the end of the file. The setup handoff has the contract's five sections (process.md §Handoff economics), and its
# manifest the fill cells the adoption writes beside the pack's version.
SURVEY = STARTER / "docs" / "reports" / "literature-review.md"
SURVEY_SECTIONS = [
    "## 1. The field's prior art",
    "## 2. What is settled",
    "## 3. Open questions",
    "## 4. Sweep log",
    "## 5. Watchlist",
    "## 6. Local papers index (`docs/papers/`)",
]
UPKEEP = re.compile(r"\*Upkeep: [^*]+\*")
QUEUE = STARTER / "docs" / "papers" / "REQUESTS.md"
QUEUE_TABLE = ["| # | DOI / URL | Title (authors, venue, year) | Needed by (memo) | Why | Status |", "|" + "---|" * 6]
SETUP_HANDOFF = STARTER / "docs" / "handoffs" / "HANDOFF-research-setup.md"
HANDOFF_SECTIONS = [
    "## Prerequisites",
    "## EXECUTE",
    "## ESCALATE, do not improvise",
    "## What happens after",
    "## Component manifest",
]
# Code carries one placeholder: the literature tool's default for its repository URL, which adoption
# fills. Built from pieces, as this file builds every example it must not carry.
CODE_SUFFIXES = (".py", ".sh")
REPO_URL_TOKEN = "{" * 2 + "REPO_URL" + "}" * 2

# CLAUDE.md's digest section, found by the start of its heading, and the section citation its bullets carry: a `§`,
# then a section of process.md named by its heading's text or, for a session type, its numeral, up to a comma, a
# semicolon or a closing parenthesis.
DIGEST = "## Way of working"
SECTION_CITATION = re.compile(r"§([^,;)]+)")

# A commit hash at a status site: seven to forty lower-case hex digits as a word. A seven-letter word spelled in a to
# f or a long number is a false hit by this rule, and is reworded.
SHA = re.compile(r"\b[0-9a-f]{7,40}\b")
# The token the adopter fills with the pack's tag and commit: a hash by the time it is written, so no status site has
# it.
VERSION_TOKEN = "{{QUOIN_VERSION}}"

# A model, by its id or its alias, is named as the binding table writes it: an id is a family name and a version, an
# alias the family name alone. One may stand only where a single edit rebinds it: a row of the binding table
# (process.md, Model policy), a seat file's frontmatter, and a row of the table of what degrades in SETUP.md. Nothing
# in this file spells an id, this pattern included: an example is built at run time from pieces.
MODEL_ID = re.compile(r"claude-[a-z]+-\d+(-\d+)?|`(?:fable|opus|sonnet|haiku)`|(?<=^model: )(?:fable|opus|sonnet|haiku)$", re.M)
BINDING_TABLE = "### The binding table"
BINDING_HEADER = ["Role", "Default", "Stand-in", "Where set"]
DEGRADE_TABLE = "## What degrades without each piece"
# The binding table's rows for the seats: the role cell's text, and the agent type and seat file the row binds.
SEAT_ROLES = {"Counsel": "counsel", "Reviewer": "reviewer"}
# What every seat file removes, whatever its model: the file-writing tools (process.md, Model policy, The seats).
SEAT_TOOLS_REMOVED = "Edit, Write, NotebookEdit"
# The start of a Default cell: the model (its id or its alias) in backticks, a comma, the effort, and the word 'effort'.
DEFAULT_CELL = re.compile(r"`([^`]+)`, (\w+) effort")
# The sections of the reviewer charter that process.md cites by name (Model policy, The seats): its Cover and Report
# brief the second whole-branch review, and its Gate mode is what the seat does for a gate round the gate's tool cannot
# run. A rename would leave the contract citing a section that is not there.
REVIEWER_SECTIONS = ["## Cover", "## Report", "## Gate mode"]

# The skeletons (process.md §Doc taxonomy, the Skeletons row): fourteen templates under
# docs/skeletons/, each a document's house shape as a title and headings with one line of guidance under each and no
# content, and the four session kickoff prompts the owner copies into a gitignored local/. The names are exact.
SKELETONS = STARTER / "docs" / "skeletons"
SKELETON_NAMES = [
    "design.md",
    "plan.md",
    "handoff.md",
    "results.md",
    "report.md",
    "explainer.md",
    "pr-description.md",
    "gate-focus.md",
    "counsel-package.md",
    "reviewer-package.md",
    "kickoff-planning-session.md",
    "kickoff-implementation-session.md",
    "kickoff-pickup-session.md",
    "kickoff-survey-session.md",
]
# A kickoff is a prompt pasted into a session: it opens with the launch line, the command that starts the session, which
# leaves the model to the binding table (an id is written only there) and the effort to the owner's confirmation.
KICKOFF = "kickoff-"
LAUNCH = "## Launch"
LAUNCH_TOKENS = ("claude --model ‹", "the binding table", "--effort max")
ATX = re.compile(r"(#{1,6}) ")

# The guide to the two paths. It has three sections, exact and in order. Path B holds one fenced block, the kickoff
# prompt of the fusion session, which an adopter pastes into a session: a link in it would resolve nothing, so it holds
# none, and it names what the session reads and makes. The reconciliation checklist is a table of three columns whose
# rows are the eleven decisions a fusion session makes, in this order, the host's choice left empty.
ADOPTING = PACK / "ADOPTING.md"
ADOPTING_SECTIONS = [
    "## Path A — a fresh repository",
    "## Path B — an existing repository: the fusion session",
    "## The reconciliation checklist",
]
PROMPT_NAMES = (
    "planning class",
    "mechanics/README.md",
    "starter/docs/process.md",
    "reconciliation checklist",
    "design doc",
    "to begin with",
    "pull request",
)
CHECKLIST_HEADER = ["Decision", "The pack's default", "The host's choice"]
CHECKLIST_DECISIONS = [
    "Layout and vocabulary",
    "Commit style",
    "The host's quality gates as the fast suite",
    "The PR review as the owner's gate",
    "The models available and the seats' binding",
    "Codex's availability",
    "Budgets on or off",
    "The id registry on or off",
    "The handoff threshold",
    "Where the ledger lives",
    "The host's own privacy rules for documents",
]

# The environment guide. The table of what degrades without each piece stands under the heading DEGRADE_TABLE spells,
# since the model-id check finds the rows where a model may stand by its id or its alias. It has a header, a separator
# and at least DEGRADE_ROWS rows, and a row for each piece of DEGRADE_PIECES, found in the first cell.
SETUP = PACK / "SETUP.md"
DEGRADE_ROWS = 4
DEGRADE_PIECES = ("codex", "superpowers", "uv")

# The index of the mechanics path B picks from: a table of three columns with a row for each mechanic, in this order,
# its name as code and not a link (the pages are to come), and the third column one of three values.
MECHANICS_INDEX = PACK / "mechanics" / "README.md"
INDEX_HEADER = ["Mechanic", "One line", "Path B"]
PATH_B = {"first", "later", "measurement only"}
MECHANICS = [
    "roadmap-as-the-spec",
    "design-docs",
    "the-two-session-loop",
    "plans",
    "adversarial-gates",
    "model-policy-and-seats",
    "counsel-triggers",
    "subagent-driven-development",
    "handoffs-and-monitors",
    "one-home-per-fact",
    "worktrees-and-checkouts",
    "survey-and-literature",
    "explainers",
    "working-with-the-owner",
    "evidence-rules",
    "the-small-change-lane",
]

# The path-B host, the repository a fusion session is rehearsed on (ADOPTING.md, Path B): a small service whose
# conventions differ from the starter's defaults on purpose. It is a repository in miniature, with a unittest suite and
# a make target of its own, so the pack's collection skips it (conftest.py) and a test here runs its check as the host's
# CI does. HOST_FILES names its twelve files, each with the text that carries the convention it exists for; an empty
# tuple is a file the service needs and no convention rides on. The tab in the Makefile's recipe is part of its
# convention. The host knows nothing of the pack, so no file names it.
HOST = PACK / "tests" / "fixtures" / "host"
HOST_FILES = {
    "README.md": (),
    "CONTRIBUTING.md": ("SVC-<n>: <subject>", "squash"),
    "CODEOWNERS": ("* @example-org/svc-maintainers",),
    ".github/PULL_REQUEST_TEMPLATE.md": (),
    ".github/workflows/ci.yml": ("push", "pull_request", "make check"),
    "Makefile": ("\n\tPYTHONPATH=src python3 -m unittest discover -s tests -t .\n",),
    "docs/adr/0001-record-architecture-decisions.md": ("## Status", "## Context", "## Decision", "## Consequences"),
    "docs/runbook.md": ("## Start", "## Stop", "## Health check", "## Rollback"),
    "src/svc/__init__.py": (),
    "src/svc/app.py": ("def handle(request: dict) -> dict:",),
    "tests/__init__.py": (),
    "tests/test_app.py": ("from svc.app import handle",),
}


def relative(path: Path) -> str:
    return path.relative_to(PACK).as_posix()


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def all_files(root: Path | None = None) -> list[Path]:
    """Every file under `root` (the pack by default), outside .git and the caches, in path order."""
    found = []
    for directory, subdirs, names in os.walk(PACK if root is None else root):
        subdirs[:] = [name for name in subdirs if name not in SKIPPED_DIRS]
        found += [Path(directory) / name for name in names if name not in SKIPPED_DIRS]
    return sorted(found)


def text_files(root: Path | None = None) -> list[Path]:
    """Every file under `root` (the pack by default), outside .git and the caches, that decodes as UTF-8, in path
    order."""
    found = []
    for path in all_files(root):
        try:
            path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found.append(path)
    return found


def not_utf8_text(root: Path | None = None) -> list[str]:
    """`<path>: <why>` for every file under `root` (the pack by default), outside .git and the caches, that is not
    UTF-8 text: its bytes are not valid UTF-8, or it holds a NUL byte, as UTF-16 or UTF-32 text does in every ASCII
    character."""
    base = PACK if root is None else root
    found = []
    for path in all_files(base):
        data = path.read_bytes()
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            found.append(f"{path.relative_to(base).as_posix()}: not valid UTF-8")
            continue
        if b"\0" in data:
            found.append(f"{path.relative_to(base).as_posix()}: a NUL byte")
    return found


def markdown_files() -> list[Path]:
    return [path for path in text_files() if path.suffix == ".md"]


def markdown_links(text: str) -> list[tuple[int, str]]:
    """The (line number, target) of every `[label](target)` link outside fenced code and code spans.

    Every target is returned, external ones and bare anchors included; the caller decides which to follow.
    """
    links = []
    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith(FENCES):
            fenced = not fenced
        elif not fenced:
            links += [(number, target) for target in LINK.findall(CODE_SPAN.sub("", line))]
    return links


def spelled_as_written(where: Path, root: Path) -> bool:
    """Whether every part of `where`, a path under `root`, is on disk spelled as it is written.

    A link that resolves only on a case-insensitive file system fails here, as it would on any other.
    """
    here = root
    for part in where.relative_to(root).parts:
        if part not in os.listdir(here):
            return False
        here = here / part
    return True


def unresolved_links(path: Path) -> list[str]:
    """`file:line: target` for each link in a Markdown file that is not a path inside the pack.

    A link with a scheme and a bare anchor are not paths. For any other, the anchor is stripped and the rest is
    resolved from the file's own directory: it must exist, spelled as written, and lie under the pack.
    """
    root = PACK.resolve()
    broken = []
    for number, target in markdown_links(path.read_text(encoding="utf-8")):
        if SCHEME.match(target) or target.startswith("#"):
            continue
        where = (path.parent / target.split("#", 1)[0]).resolve()
        if root not in (where, *where.parents) or not where.exists() or not spelled_as_written(where, root):
            broken.append(f"{relative(path)}:{number}: {target}")
    return broken


def unfenced(lines: list[str]) -> list[tuple[int, str]]:
    """(index, line) of every line outside fenced code, the fence lines themselves left out."""
    kept, fenced = [], False
    for index, line in enumerate(lines):
        if line.startswith(FENCES):
            fenced = not fenced
        elif not fenced:
            kept.append((index, line))
    return kept


def section_headings(text: str) -> list[str]:
    """The `## ` and `### ` heading lines of a Markdown text, outside fenced code, in order."""
    return [line.rstrip() for _, line in unfenced(text.splitlines()) if line.startswith(("## ", "### "))]


def github_slug(heading: str) -> str:
    """The anchor GitHub gives a heading: its text lower-cased, punctuation dropped, each space a hyphen."""
    text = heading.lstrip("#").strip().lower()
    return "".join(char for char in text if char.isalnum() or char in " _-").replace(" ", "-")


def heading_slugs(text: str) -> set[str]:
    """The anchor of every heading of a Markdown text, at any level, outside fenced code."""
    return {github_slug(line) for _, line in unfenced(text.splitlines()) if re.match(r"#{1,6} ", line)}


def without_section(text: str, heading: str) -> str:
    """The text with one `## ` section cut out: from its heading line to the next `## ` heading, or to the end."""
    lines = text.splitlines(keepends=True)
    start = next(index for index, line in enumerate(lines) if line.rstrip() == heading)
    later = [index for index, line in unfenced(lines) if index > start and line.startswith("## ")]
    end = later[0] if later else len(lines)
    return "".join(lines[:start] + lines[end:])


def dangling_references(root: Path, deleted: tuple[str, ...]) -> list[str]:
    """What a copy of the starter at `root` still points at once the `deleted` sections are gone from its process.md.

    A `(#…)` anchor in process.md, or a `process.md#…` link in any file of the copy, that names no remaining
    heading; and any file that still carries a deleted section's heading text, its anchor or its own vocabulary
    (`EXTENSION_TRACES`).
    """
    text = (root / "docs" / "process.md").read_text(encoding="utf-8")
    slugs = heading_slugs(text)
    problems = [
        f"docs/process.md:{line_of(text, match.start())}: (#{match.group(1)}) names no heading"
        for match in ANCHOR_LINK.finditer(text)
        if match.group(1) not in slugs
    ]
    for path in text_files(root):
        name = path.relative_to(root).as_posix()
        body = path.read_text(encoding="utf-8")
        for match in PROCESS_ANCHOR.finditer(body):
            if match.group(1) not in slugs:
                problems.append(f"{name}:{line_of(body, match.start())}: process.md#{match.group(1)} names no heading")
        lowered = body.lower()
        for heading in deleted:
            for trace in (heading[3:].lower(), github_slug(heading)):
                if trace in lowered:
                    problems.append(f"{name}: still carries '{trace}' of a deleted section")
            vocabulary = EXTENSION_TRACES.get(heading)
            if vocabulary is not None:
                for match in vocabulary.finditer(body):
                    where = line_of(body, match.start())
                    problems.append(f"{name}:{where}: still carries '{match.group(0)}' of a deleted section")
    return problems


def h1_block(text: str) -> str:
    """The text after the title line up to the first `## ` heading: the block the budget check calls the H1 block."""
    block = []
    for line in text.splitlines()[1:]:
        if line.startswith("## "):
            break
        block.append(line)
    return "\n".join(block)


def section_lines(text: str, prefix: str) -> list[str]:
    """The lines under the `## ` heading that starts with `prefix`, up to the next `## ` heading outside fenced code.

    Empty when no heading starts with it.
    """
    kept, inside, fenced = [], False, False
    for line in text.splitlines():
        if line.startswith(FENCES):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            inside = line.startswith(prefix)
        elif inside:
            kept.append(line)
    return kept


def top_level_bullets(lines: list[str]) -> list[str]:
    """Each top-level bullet of `lines` as one text: a line starting `- ` and the lines after it up to the next bullet,
    a blank line or a heading."""
    bullets: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("- "):
            if current:
                bullets.append("\n".join(current))
            current = [line]
        elif current and line.strip() and not line.startswith("#"):
            current.append(line)
        else:
            if current:
                bullets.append("\n".join(current))
            current = []
    if current:
        bullets.append("\n".join(current))
    return bullets


def status_paragraphs(text: str) -> list[str]:
    """The runs of lines, each up to a blank line or a heading, that hold a bolded `**Status:` marker."""
    paragraphs: list[str] = []
    run: list[str] = []
    for line in text.splitlines() + [""]:
        if not line.strip() or re.match(r"#{1,6}\s", line):
            if any("**Status:" in item for item in run):
                paragraphs.append("\n".join(run))
            run = []
        else:
            run.append(line)
    return paragraphs


def core_section_names() -> set[str]:
    """What a citation of process.md may call a core section: its heading's text, or a session type's numeral."""
    names = set()
    for heading in PROCESS_HEADINGS:
        if heading in EXTENSIONS:
            continue
        title = heading.lstrip("#").strip()
        names.add(title)
        numeral = re.match(r"([IV]+)\. ", title)
        if numeral:
            names.add(numeral.group(1))
    return names


def section_body(text: str, heading: str) -> list[tuple[int, str]]:
    """(line number, line) of every line under the line that reads `heading`, up to the next heading of the same or a
    higher level outside fenced code. Empty when no line reads `heading`."""
    lines = text.splitlines()
    outside = unfenced(lines)
    level = len(heading) - len(heading.lstrip("#"))
    starts = [index for index, line in outside if line.rstrip() == heading]
    if not starts:
        return []
    ends = [index for index, line in outside if index > starts[0] and re.match(rf"#{{1,{level}}} ", line)]
    return [(number + 1, lines[number]) for number in range(starts[0] + 1, ends[0] if ends else len(lines))]


def fenced_blocks(lines: list[str]) -> list[str]:
    """The text of every fenced block among `lines`, in order, the fence lines left out. A fence the lines leave open
    closes no block, so its text is not returned."""
    blocks: list[str] = []
    current: list[str] | None = None
    for line in lines:
        if line.startswith(FENCES):
            if current is None:
                current = []
            else:
                blocks.append("\n".join(current))
                current = None
        elif current is not None:
            current.append(line)
    return blocks


def table_rows(lines: list[str]) -> list[list[str]]:
    """The cells of every table row among `lines`, each row a list of stripped cells: a line starting with `|`, split at
    the pipes, the outer two left out. A cell that holds a pipe splits in two."""
    return [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines if line.startswith("|")]


def section_citations(text: str) -> list[str]:
    """The name that each `§` of a Markdown text introduces, outside fenced code, read as the digest check reads it
    (SECTION_CITATION, with whitespace folded). A table row is read cell by cell, so that a citation ends where its cell
    does and not at the next comma, rows further down."""
    lines = [line for _, line in unfenced(text.splitlines())]
    pieces = ["\n".join(line for line in lines if not line.startswith("|"))]
    pieces += [cell for row in table_rows(lines) for cell in row]
    return [" ".join(match.group(1).split()) for piece in pieces for match in SECTION_CITATION.finditer(piece)]


def binding_rows(text: str) -> dict[str, list[str]]:
    """The binding table of a process.md text: each row's cells keyed by its role cell, the header and the separator
    left out. Raises ValueError when the section holds no table with the expected header and four cells to a row."""
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for _, line in section_body(text, BINDING_TABLE)
        if line.startswith("|")
    ]
    if not rows or rows[0] != BINDING_HEADER or any(len(row) != len(BINDING_HEADER) for row in rows):
        raise ValueError(f"'{BINDING_TABLE}' holds no table headed {', '.join(BINDING_HEADER)}")
    return {row[0]: row for row in rows[2:]}


def seat_frontmatter(text: str) -> dict[str, str]:
    """The frontmatter of a seat file, read as the subset of YAML the seat files use: `key: value` lines and folded
    blocks (`key: >` and the indented lines under it). Raises ValueError at the first line outside that subset, and
    where YAML would read a plain value differently from how it is written, so that a broken frontmatter fails here and
    not when the harness loads the agent."""
    lines = text.splitlines()
    if lines[:1] != ["---"] or "---" not in lines[1:]:
        raise ValueError("the file does not open with a frontmatter between two '---' lines")
    fields: dict[str, list[str]] = {}
    folded: list[str] | None = None
    for number, line in enumerate(lines[1 : lines.index("---", 1)], 2):
        if not line.strip():
            if folded is not None:
                folded.append("")
        elif folded is not None and line.startswith(" "):
            folded.append(line.strip())
        else:
            key = re.fullmatch(r"([A-Za-z][A-Za-z0-9_]*): ?(.*)", line)
            if key is None or key.group(1) in fields:
                raise ValueError(f"line {number} is not a new 'key: value' line: {line[:60]!r}")
            name, value = key.groups()
            if value == ">":
                folded = fields[name] = []
            elif not value or ": " in value or " #" in value or value.endswith(":") or value[0] in "[]{}&*!|>'\"%@`":
                raise ValueError(f"line {number}: YAML would not read the plain value of '{name}' as written")
            else:
                folded, fields[name] = None, [value]
    return {name: " ".join(part for part in parts if part) for name, parts in fields.items()}


def seat_file_problems(rows: dict[str, list[str]], agents: Path) -> list[str]:
    """What is wrong with the seat files in `agents` against the binding table's `rows`, one line each: a seat with no
    row, a row not set at its seat file, a missing seat file or one whose frontmatter does not parse, a name, model,
    effort or tool list the row does not bind, no description, and any file in the directory that is not a seat file."""
    problems = []
    for role, seat in SEAT_ROLES.items():
        row = rows.get(role)
        bound = DEFAULT_CELL.match(row[1]) if row else None
        if bound is None:
            problems.append(f"the binding table has no '{role}' row whose default reads `id`, effort")
            continue
        if row[3] != f"`.claude/agents/{seat}.md`":
            problems.append(f"the '{role}' row is set at {row[3]}, not at `.claude/agents/{seat}.md`")
        if not (agents / f"{seat}.md").is_file():
            problems.append(f"{seat}.md: no such seat file")
            continue
        try:
            front = seat_frontmatter((agents / f"{seat}.md").read_text(encoding="utf-8"))
        except ValueError as error:
            problems.append(f"{seat}.md: {error}")
            continue
        wanted = {"name": seat, "model": bound[1], "effort": bound[2], "disallowedTools": SEAT_TOOLS_REMOVED}
        for key, value in wanted.items():
            if front.get(key) != value:
                problems.append(f"{seat}.md: {key} is {front.get(key)!r}, the table binds {value!r}")
        if not front.get("description"):
            problems.append(f"{seat}.md: no description")
    for path in sorted(agents.glob("*")):
        if path.name not in {f"{seat}.md" for seat in SEAT_ROLES.values()}:
            problems.append(f"{path.name}: in the agents directory but not a seat file")
    return problems


def model_id_sites(pack: Path) -> dict[str, set[int]]:
    """For each file of `pack` that may name a model, by its id or its alias, the line numbers where it may: the rows of
    the binding table in the starter's process.md, the frontmatter of each seat file and the rows of the table of what
    degrades in SETUP.md (a pack without that file has no such site). Prose beside a table, and a seat file's body, are
    not sites."""
    sites: dict[str, set[int]] = {}
    for name, heading in (("starter/docs/process.md", BINDING_TABLE), ("SETUP.md", DEGRADE_TABLE)):
        if (pack / name).is_file():
            body = section_body((pack / name).read_text(encoding="utf-8"), heading)
            sites[name] = {number for number, line in body if line.startswith("|")}
    for seat in sorted((pack / "starter" / ".claude" / "agents").glob("*.md")):
        lines = seat.read_text(encoding="utf-8").splitlines()
        if lines[:1] == ["---"] and "---" in lines[1:]:
            sites[seat.relative_to(pack).as_posix()] = set(range(2, lines.index("---", 1) + 1))
    return sites


def model_id_report(pack: Path) -> tuple[list[str], set[str]]:
    """(stray, read) over the text files of `pack`: `file:line: id` for each model, by its id or its alias, outside the
    sites that may name one, and the files where one was read at such a site."""
    sites = model_id_sites(pack)
    stray, read = [], set()
    for path in text_files(pack):
        name = path.relative_to(pack).as_posix()
        text = path.read_text(encoding="utf-8")
        for match in MODEL_ID.finditer(text):
            number = line_of(text, match.start())
            if number in sites.get(name, ()):
                read.add(name)
            else:
                stray.append(f"{name}:{number}: {match.group(0)}")
    return stray, read


def run_gate(
    tmp_path: Path, focus: str, *, companion: bool = False, relative: bool = False, args: tuple[str, ...] = ()
) -> tuple[subprocess.CompletedProcess[str], Path]:
    """Run the gate launcher as `bash <script> <focus file> <args>` on a focus file that holds `focus`.

    CODEX_PLUGIN names `tmp_path/plugin`, an empty directory, or with `companion` one that holds a stub companion
    script, which is never run; no real plugin is used and nothing here touches the network. A fake `node` first on the
    PATH records its working directory and its arguments in a record file, which exists only if something ran `node`.
    The focus file is named by its absolute path from `tmp_path`, or with `relative` by a relative path from a caller's
    directory, which is where the run starts. Returns the finished process and the record; `launch` reads the record.
    """
    plugin = tmp_path / "plugin"
    plugin.mkdir(exist_ok=True)
    if companion:
        (plugin / "scripts").mkdir(exist_ok=True)
        (plugin / "scripts" / "codex-companion.mjs").write_text("throw new Error('never run');\n", encoding="utf-8")
    node = tmp_path / "bin" / "node"
    node.parent.mkdir(exist_ok=True)
    node.write_text('#!/bin/bash\npwd > "$GATE_RECORD"\nprintf \'%s\\0\' "$@" >> "$GATE_RECORD"\n', encoding="utf-8")
    node.chmod(0o755)
    caller = tmp_path / "caller" if relative else tmp_path
    caller.mkdir(exist_ok=True)
    (caller / "focus.txt").write_text(focus, encoding="utf-8")
    record = tmp_path / "record"
    env = {
        **os.environ,
        "CODEX_PLUGIN": str(plugin),
        "GATE_RECORD": str(record),
        "PATH": f"{node.parent}{os.pathsep}{os.environ['PATH']}",
    }
    named = "focus.txt" if relative else str(caller / "focus.txt")
    done = subprocess.run(
        ["bash", str(GATE), named, *args], cwd=caller, env=env, capture_output=True, text=True, check=False
    )
    return done, record


def launch(record: Path) -> tuple[Path, list[str]] | None:
    """Where the fake `node` ran and with which arguments, or None if it never ran."""
    if not record.exists():
        return None
    cwd, _, argv = record.read_text(encoding="utf-8").partition("\n")
    return Path(cwd), argv.split("\0")[:-1]


def atx_headings(lines: list[str]) -> list[tuple[int, int]]:
    """(index, level) of every heading line, `#` to `######` and a space, in order."""
    found = []
    for index, line in enumerate(lines):
        match = ATX.match(line)
        if match:
            found.append((index, len(match.group(1))))
    return found


def heading_bodies(lines: list[str]) -> list[tuple[str, list[str]]]:
    """(heading line, its non-blank lines up to the next heading of any level or the end) for every heading of level two
    or deeper, in order."""
    headings = atx_headings(lines)
    bodies = []
    for index, level in headings:
        if level >= 2:
            end = min((later for later, _ in headings if later > index), default=len(lines))
            bodies.append((lines[index].rstrip(), [line for line in lines[index + 1 : end] if line.strip()]))
    return bodies


def skeleton_shape_problems(text: str) -> list[str]:
    """What is wrong with the shape of a skeleton's text, one line each. A skeleton is one `# ` title on its first line,
    at least one `## ` heading, and under every heading of level two or deeper exactly one non-blank line before the
    next heading or the end; the block between the title and the first such heading holds one-line paragraphs only, the
    header's own fields."""
    lines = text.splitlines()
    headings = atx_headings(lines)
    problems = []
    if [index for index, level in headings if level == 1] != [0]:
        problems.append("it must carry one '# ' title, on its first line")
    if not [index for index, level in headings if level == 2]:
        problems.append("it has no '## ' heading")
    deeper = [index for index, level in headings if level >= 2]
    block = lines[1 : deeper[0] if deeper else len(lines)]
    if any(before.strip() and after.strip() for before, after in zip(block, block[1:])):
        problems.append("the block under the title holds a paragraph of more than one line")
    problems += [
        f"'{heading}' is followed by {len(body)} non-blank lines, not one"
        for heading, body in heading_bodies(lines)
        if len(body) != 1
    ]
    return problems


def skeleton_content_problems(text: str, *, kickoff: bool = False) -> list[str]:
    """What is wrong with what a skeleton says, one line each: a Markdown link (a copy kept at another depth would
    dangle, so a skeleton cites in words); an HTML comment (a fill comment is what an adopter replaces, where a skeleton
    stays a template); a `§` citation of what is no core section of process.md, and no citation at all; and for a
    kickoff a first section that is not the launch line, or a section whose line cites no section."""
    problems = []
    if markdown_links(text):
        problems.append("it links, and a copy kept at another depth would dangle: a skeleton cites in words")
    if "<!--" in text:
        problems.append("it holds an HTML comment: a skeleton's guidance is a line of text, never a fill comment")
    names = core_section_names()
    cited = [" ".join(match.group(1).split()) for match in SECTION_CITATION.finditer(text)]
    problems += [f"it cites '{name}', which is no core section of process.md" for name in cited if name not in names]
    if not cited:
        problems.append("it cites no section of process.md with '§'")
    if kickoff:
        bodies = heading_bodies(text.splitlines())
        launch = bodies[0][1][:1] if bodies and bodies[0][0] == LAUNCH else []
        if not launch or any(token not in launch[0] for token in LAUNCH_TOKENS):
            problems.append(f"it does not open with '{LAUNCH}' and a line holding {', '.join(LAUNCH_TOKENS)}")
        problems += [
            f"'{heading}' cites no section of process.md" for heading, body in bodies if "§" not in " ".join(body)
        ]
    return problems


def doc_budgets():
    """The starter's document check, loaded from its path."""
    spec = importlib.util.spec_from_file_location("starter_doc_budgets", DOC_BUDGETS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_placeholders_are_from_the_set():
    stray = []
    for path in text_files():
        text = path.read_text(encoding="utf-8")
        for match in TOKEN.finditer(text):
            if match.group(1) not in PLACEHOLDERS:
                stray.append(f"{relative(path)}:{line_of(text, match.start())}: {match.group(0)}")
    assert not stray, "tokens outside the placeholder set:\n" + "\n".join(stray)


def test_adopting_table_names_every_placeholder():
    rows = re.findall(r"^\|\s*`\{\{([A-Z_]+)\}\}`\s*\|", ADOPTING.read_text(encoding="utf-8"), re.MULTILINE)
    missing = sorted(PLACEHOLDERS - set(rows))
    extra = sorted(set(rows) - PLACEHOLDERS)
    repeated = sorted({name for name in rows if rows.count(name) > 1})
    assert not (missing or extra or repeated), (
        "the placeholder table needs exactly one row per member: "
        f"missing {missing}, outside the set {extra}, repeated {repeated}"
    )


def test_fill_comments_have_the_grammar():
    bad = []
    for path in markdown_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for opening in FILL_OPEN.finditer(line):
                comment = FILL.match(line, opening.start())
                if comment is None or ";" not in comment.group(0):
                    bad.append(f"{relative(path)}:{number}: {line.strip()[:90]}")
    assert not bad, "fill comments that are not one line of 'what; the rule it follows':\n" + "\n".join(bad)


def test_relative_links_resolve_inside_the_pack():
    broken = [line for path in markdown_files() for line in unresolved_links(path)]
    assert not broken, "links that do not resolve to a path inside the pack:\n" + "\n".join(broken)


def test_every_file_is_utf8_text():
    """Every file of the pack is UTF-8 text with no NUL byte, so the checks that read the pack as text read all of it:
    a file in another encoding, UTF-16 say, would pass them unread."""
    problems = not_utf8_text()
    assert not problems, "files that are not UTF-8 text:\n" + "\n".join(problems)


def test_no_address_or_key_shape():
    found = []
    for path in text_files():
        text = path.read_text(encoding="utf-8")
        for name, shape in SHAPES.items():
            for match in shape.finditer(text):
                found.append(f"{relative(path)}:{line_of(text, match.start())}: {name}")
    assert not found, "the shape of an address or a key (the text itself is never printed):\n" + "\n".join(found)


def test_license_is_mit_in_the_pack():
    assert (PACK / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")


def test_changelog_lists_releases_newest_first():
    lines = (PACK / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# Changelog"
    headings = [line[3:] for line in lines if line.startswith("## ")]
    assert headings, "CHANGELOG.md has no '## ' heading"
    if headings[0] == "Unreleased":
        headings = headings[1:]
    versions = []
    for heading in headings:
        version = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", heading)
        assert version, f"'## {heading}' is neither 'Unreleased' (first) nor a version, vMAJOR.MINOR.PATCH"
        versions.append(tuple(int(part) for part in version.groups()))
    assert versions == sorted(set(versions), reverse=True), "versions must be distinct and newest first"


def test_process_headings_are_the_contract():
    lines = PROCESS.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# Process — the way of working"
    assert section_headings("\n".join(lines)) == PROCESS_HEADINGS
    for heading in EXTENSIONS:
        opening = next(line for line in lines[lines.index(heading) + 1 :] if line.strip())
        assert ADOPTION in opening, f"'{heading}' must open with its adoption sentence"


@pytest.mark.parametrize(
    ("deleted", "plant", "expected"),
    [
        (EXTENSIONS[:1], None, None),
        (EXTENSIONS[1:], None, None),
        (EXTENSIONS, None, None),
        (
            EXTENSIONS[:1],
            ("docs/process.md", "[measurement](#extension--measurement-work)"),
            "(#extension--measurement-work) names no heading",
        ),
        (
            EXTENSIONS[:1],
            ("docs/planted.md", "[measurement](process.md#extension--measurement-work)"),
            "process.md#extension--measurement-work names no heading",
        ),
        (
            EXTENSIONS[:1],
            ("docs/process.md", "§Extension — measurement work"),
            "still carries 'extension — measurement work' of a deleted section",
        ),
        (
            EXTENSIONS[:1],
            ("docs/process.md", "the extension--measurement-work anchor"),
            "still carries 'extension--measurement-work' of a deleted section",
        ),
        (
            EXTENSIONS[:1],
            ("docs/process.md", "counsel trigger 8 fires"),
            "still carries 'trigger 8' of a deleted section",
        ),
        (
            EXTENSIONS[:1],
            ("docs/planted.md", "when one of the counsel triggers 1–9 fires"),
            "still carries 'triggers 1–9' of a deleted section",
        ),
    ],
    ids=[
        "measurement-deleted",
        "overlay-deleted",
        "both-deleted",
        "link-planted-in-the-core",
        "link-planted-elsewhere",
        "heading-text-planted-in-the-core",
        "slug-planted-in-the-core",
        "trigger-number-planted-in-the-core",
        "trigger-range-planted-elsewhere",
    ],
)
def test_extension_deletion_leaves_no_dangling_reference(tmp_path, deleted, plant, expected):
    """Each extension deleted from a scratch copy of the starter, then both: nothing left points at what went. Each
    planted case leaves one trace of the deleted measurement extension — a link in the core or in another file, its
    heading text, its anchor as bare text, a trigger number of its own or a range ending in one — and the check must
    name that trace."""
    root = tmp_path / "starter"
    shutil.copytree(STARTER, root, ignore=shutil.ignore_patterns(*SKIPPED_DIRS))
    process = root / "docs" / "process.md"
    text = process.read_text(encoding="utf-8")
    if plant:
        where, planted = plant
        if where == "docs/process.md":
            first = PROCESS_HEADINGS[0] + "\n"
            text = text.replace(first, first + "\n" + planted + "\n", 1)
        else:
            (root / where).write_text(planted + "\n", encoding="utf-8")
    for heading in deleted:
        text = without_section(text, heading)
    process.write_text(text, encoding="utf-8")
    assert section_headings(text) == [heading for heading in PROCESS_HEADINGS if heading not in deleted]
    problems = dangling_references(root, deleted)
    if expected is None:
        assert not problems, "references left dangling by the deletion:\n" + "\n".join(problems)
    else:
        assert any(expected in problem for problem in problems), problems


def test_process_within_budget():
    words = doc_budgets().count_words(PROCESS.read_text(encoding="utf-8"))
    assert words <= PROCESS_WORDS, f"process.md has {words} words; its budget is {PROCESS_WORDS}"


def test_doc_budgets_check_passes_on_the_starter():
    """The starter is within the budgets its own file records: the document check, run as an adopter runs it
    (process.md §Budgets), exits 0 over the starter, and on a failure the problems it printed are shown."""
    done = subprocess.run(
        ["python3", "-I", str(DOC_BUDGETS), "check", "--root", str(STARTER)], capture_output=True, text=True
    )
    assert done.returncode == 0, done.stdout + done.stderr


def test_starter_boot_files_exist():
    problems = []
    for name in BOOT_FILES:
        path = STARTER / name
        if path.is_symlink() or not path.is_file():
            problems.append(f"{name}: not a regular file")
        elif name not in KEPT_EMPTY and not path.read_text(encoding="utf-8").strip():
            problems.append(f"{name}: empty")
    assert not problems, "the boot files and stubs the starter ships:\n" + "\n".join(problems)


def test_starter_gitignore_keeps_the_sessions_local_state_out_of_git():
    """The starter's `.gitignore`, which path A copies whole: the ledger, the owner's prompts and the session worktrees
    (process.md §II, stage 5 and Checkouts, and the taxonomy's Skeletons row; the worktree runbook, §1), the
    environments and caches, and last the line below which the project adds its own. Path B creates the host's file if
    it has none and appends only the entries a mechanic needs, the first three (ADOPTING.md, the fusion session's
    prompt)."""
    lines = [line.strip() for line in (STARTER / ".gitignore").read_text(encoding="utf-8").splitlines()]
    entries = {line for line in lines if line and not line.startswith("#")}
    needed = {".superpowers/", "/local/", ".claude/worktrees/", ".venv/", "__pycache__/", ".pytest_cache/", ".DS_Store"}
    assert needed <= entries, f"the .gitignore lacks {sorted(needed - entries)}"
    assert [line for line in lines if line][-1] == "# {{PROJECT}}: the project's own entries below"


def test_claude_digest_cites_process_and_adds_nothing():
    """CLAUDE.md's digest is bullets and nothing else, and each cites process.md, the contract, at a section of it.

    A bullet's `§Name` must name a core section of process.md, so a digest cannot cite an extension, which a project
    may delete, nor a section that does not exist.
    """
    lines = section_lines((STARTER / "CLAUDE.md").read_text(encoding="utf-8"), DIGEST)
    bullets = top_level_bullets(lines)
    names = core_section_names()
    problems = []
    for line in lines:
        if line.strip() and not line.startswith(("- ", "  ")):
            problems.append(f"not a bullet: {line.strip()[:70]}")
    for bullet in bullets:
        where = bullet.splitlines()[0][:70]
        cited = [" ".join(match.group(1).split()) for match in SECTION_CITATION.finditer(bullet)]
        if "process.md" not in bullet:
            problems.append(f"does not contain 'process.md': {where}")
        if not cited:
            problems.append(f"cites no section with '§': {where}")
        for name in cited:
            if name not in names:
                problems.append(f"cites '{name}', which is no core section of process.md: {where}")
    assert bullets, f"CLAUDE.md has no bullet under '{DIGEST}'"
    assert not problems, "the digest cites the contract and adds nothing:\n" + "\n".join(problems)


def test_status_sites_carry_no_sha():
    """No commit hash, and no token that becomes one, at a status site: CLAUDE.md's H1 block and the roadmap's status
    paragraphs and 'Now and next' (process.md §Budgets: the no-hash rule at status sites)."""
    claude = (STARTER / "CLAUDE.md").read_text(encoding="utf-8")
    roadmap = (STARTER / "docs" / "roadmap.md").read_text(encoding="utf-8")
    block = h1_block(claude)
    queue = "\n".join(section_lines(roadmap, "## Now and next"))
    paragraphs = status_paragraphs(roadmap)
    # The sites must hold text, else the check would pass over nothing.
    assert [line for line in block.splitlines() if line.startswith("**Status")], "CLAUDE.md's H1 block has no Status"
    assert [line for line in block.splitlines() if line.startswith("**Next:**")], "CLAUDE.md's H1 block has no Next"
    assert queue.strip(), "the roadmap's 'Now and next' is empty"
    assert paragraphs, "the roadmap has no status paragraph"
    sites = {"CLAUDE.md H1 block": block, "roadmap 'Now and next'": queue}
    sites.update({f"roadmap status paragraph {number}": text for number, text in enumerate(paragraphs, 1)})
    found = []
    for name, text in sites.items():
        found += [f"{name}: '{match.group(0)}' reads as a commit hash" for match in SHA.finditer(text)]
        if VERSION_TOKEN in text:
            found.append(f"{name}: {VERSION_TOKEN} is filled with a commit at adoption")
    assert not found, "status sites name no commit:\n" + "\n".join(found)


def test_model_ids_live_only_in_the_binding_sites():
    """A model, by its id or its alias, stands only where one edit rebinds it: a row of the binding table, a seat file's
    frontmatter and a row of the environment guide's table of what degrades. A model named anywhere else, in the prose
    beside those tables too, is a site a rebinding at adoption would miss (process.md, Model policy, The binding table).
    Each of those sites holds a model, so a heading that was renamed cannot hide a table from the check."""
    stray, read = model_id_report(PACK)
    assert not stray, "model ids outside the binding sites:\n" + "\n".join(stray)
    sites = {
        "SETUP.md",
        "starter/docs/process.md",
        *(f"starter/.claude/agents/{seat}.md" for seat in SEAT_ROLES.values()),
    }
    assert sites <= read, f"no model id was read at {sorted(sites - read)}, so the check has not seen those sites"


def test_seat_frontmatter_matches_the_binding_table():
    """Each seat file pins the model and the effort its row of the binding table binds, is named for its agent type and
    removes the file-writing tools; the starter's agents directory holds those files and no other."""
    rows = binding_rows(PROCESS.read_text(encoding="utf-8"))
    problems = seat_file_problems(rows, STARTER / ".claude" / "agents")
    assert not problems, "the seat files against the binding table:\n" + "\n".join(problems)


def test_reviewer_charter_keeps_the_sections_process_cites():
    """process.md cites the reviewer charter's Cover, Report and Gate mode sections by name; a charter that renames one
    leaves the contract pointing at nothing, and the copies agreeing with each other would not notice."""
    text = (STARTER / ".claude" / "agents" / "reviewer.md").read_text(encoding="utf-8")
    missing = [heading for heading in REVIEWER_SECTIONS if heading not in section_headings(text)]
    assert not missing, f"the reviewer charter has no {missing}, which process.md cites by name"


def test_codex_gate_script_refuses_a_dash_led_focus(tmp_path):
    """The launcher refuses a focus text with a dash-led token (the companion would read it as a flag): exit 2 and the
    word 'dash' on stderr, before the plugin is looked for. A clean focus, with no companion script in the plugin
    directory, stops with a non-zero exit that names CODEX_PLUGIN. Neither run launches anything."""
    refused, record = run_gate(tmp_path, "-x\n")
    assert refused.returncode == 2, refused.stderr
    assert "dash" in refused.stderr, refused.stderr
    assert "CODEX_PLUGIN" not in refused.stderr, "the refusal did not stop the launcher before it looked for the plugin"
    assert launch(record) is None, "the launcher ran node on a focus text it refused"
    clean, record = run_gate(tmp_path, "Review the design.\n")
    assert clean.returncode != 0, "a clean focus with no plugin should stop"
    assert "CODEX_PLUGIN" in clean.stderr, clean.stderr
    assert launch(record) is None, "the launcher ran node with no companion script to run"


def test_codex_gate_script_runs_the_companion_from_the_root(tmp_path):
    """With a clean focus and a plugin that holds a companion script, the launcher reads a relative focus path from the
    caller's directory, moves to the repository root (the starter's, one level above `tools/`) and runs the companion
    there: `adversarial-review`, `--background`, the options it was given, then `--` and the focus text, each a
    separate argument. A fake `node` stands in for the companion, so nothing real runs."""
    done, record = run_gate(
        tmp_path, "Review the design.\nEnd with a verdict.\n", companion=True, relative=True, args=("--base", "main")
    )
    assert done.returncode == 0, done.stderr
    call = launch(record)
    assert call is not None, "the launcher never ran node"
    cwd, argv = call
    assert cwd.resolve() == STARTER.resolve(), f"the companion ran from {cwd}, not from the repository root"
    assert argv == [
        f"{tmp_path / 'plugin'}/scripts/codex-companion.mjs",
        "adversarial-review",
        "--background",
        "--base",
        "main",
        "--",
        "Review the design.\nEnd with a verdict.",
    ]


def test_codex_gate_script_keeps_a_spaced_path_one_argument(tmp_path):
    """A `--cwd` path with a space reaches the companion as one argument, and the focus text as another: the launcher
    passes its options through as given, never joined into one string for the companion to split again. A fake `node`
    stands in for the companion."""
    checkout = tmp_path / "project worktree"
    checkout.mkdir()
    done, record = run_gate(
        tmp_path, "Review the branch.\n", companion=True, args=("--base", "main", "--cwd", str(checkout))
    )
    assert done.returncode == 0, done.stderr
    call = launch(record)
    assert call is not None, "the launcher never ran node"
    assert call[1][1:] == [
        "adversarial-review",
        "--background",
        "--base",
        "main",
        "--cwd",
        str(checkout),
        "--",
        "Review the branch.",
    ]


def test_codex_gate_script_ships_executable():
    """AGENTS.md and process.md run the launcher directly (`tools/codex_gate.sh FOCUS_FILE …`), never under the
    interpreter of the Python tools, so the starter's copy keeps its executable bit."""
    assert GATE.is_file(), "tools/codex_gate.sh is missing"
    assert os.access(GATE, os.X_OK), "tools/codex_gate.sh is not executable"


def test_runbooks_cite_the_table_not_restate_it():
    """The gate transition table is process.md's alone (§Adversarial review protocol, The gate transitions): the gate
    runbook names it, and neither runbook carries a copy of its header row."""
    texts = {name: (RUNBOOKS / name).read_text(encoding="utf-8") for name in RUNBOOK_NAMES}
    for name, text in texts.items():
        assert TABLE_HEADER not in text, f"{name} copies the gate transition table; cite process.md's"
    assert "gate transitions" in texts["codex-gate.md"], "codex-gate.md does not cite the gate transitions"


def test_code_carries_one_token_the_literature_tools_repo_url_default():
    """No code file of the starter carries a placeholder but one: the literature tool's default for LIT_REPO_URL, the
    literal token adoption fills. A token anywhere else in code would be rewritten by a fill never meant for it."""
    found = []
    for path in text_files(STARTER):
        if path.suffix in CODE_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            for match in TOKEN.finditer(text):
                line = text.splitlines()[line_of(text, match.start()) - 1].strip()
                found.append((relative(path), match.group(0), line.startswith("REPO_URL = ")))
    assert found == [("starter/tools/lit.py", REPO_URL_TOKEN, True)], found


def test_survey_ships_its_sections_each_with_its_upkeep_rule():
    """The survey document ships its six sections and no content: under each heading its one-line upkeep rule, and
    under the sweep log and the papers index their table's header and separator. The index stays §6, the section
    `tools/lit.py index` reads and `fetch` names in the row it prints."""
    text = SURVEY.read_text(encoding="utf-8")
    assert section_headings(text) == SURVEY_SECTIONS
    for heading in SURVEY_SECTIONS:
        body = [line for _, line in section_body(text, heading) if line.strip()]
        assert body and UPKEEP.fullmatch(body[0]), f"'{heading}' does not open with its upkeep rule"
        rest = body[1:]
        assert len(rest) in (0, 2) and all(line.startswith("|") for line in rest), f"'{heading}' holds content"


def test_queue_ends_with_the_table_fetch_appends_to():
    """`lit.py fetch --queue` numbers its row from the table and appends it at the end of the file, so the queue ships
    with its six-column table last, and empty."""
    lines = [line for line in QUEUE.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines[-2:] == QUEUE_TABLE


def test_research_setup_handoff_has_the_contracts_five_sections():
    """The setup handoff is a five-section handoff (process.md §Handoff economics) shipped as a template: its manifest
    holds a fill cell for the execution SHA and one for each component's path, and the pack's version as provenance."""
    text = SETUP_HANDOFF.read_text(encoding="utf-8")
    assert section_headings(text) == HANDOFF_SECTIONS
    manifest = "\n".join(line for _, line in section_body(text, "## Component manifest"))
    assert VERSION_TOKEN in manifest
    assert len(FILL.findall(manifest)) == 6, "the execution SHA and the five components' paths"


def test_skeletons_are_headings_with_one_guidance_line():
    """docs/skeletons/ holds exactly the fourteen templates of SKELETON_NAMES (process.md §Doc taxonomy, the Skeletons
    row), and each is a title and headings with one line of guidance under every heading below the title
    (`skeleton_shape_problems`), none empty and none more. The handoff skeleton's `## ` headings are the contract's
    five (process.md §Handoff economics), the ones the setup handoff keeps, in order."""
    present = sorted(path.name for path in SKELETONS.iterdir()) if SKELETONS.is_dir() else []
    assert present == sorted(SKELETON_NAMES), f"docs/skeletons/ holds {present}, not exactly SKELETON_NAMES"
    problems = []
    for name in SKELETON_NAMES:
        path = SKELETONS / name
        if path.is_symlink() or not path.is_file():
            problems.append(f"{name}: not a regular file")
        else:
            problems += [f"{name}: {found}" for found in skeleton_shape_problems(path.read_text(encoding="utf-8"))]
    assert not problems, "skeletons that are not headings with one line of guidance:\n" + "\n".join(problems)
    assert section_headings((SKELETONS / "handoff.md").read_text(encoding="utf-8")) == HANDOFF_SECTIONS


def test_skeletons_cite_process_by_section_and_link_nothing():
    """A skeleton cites the contract by section in words and links nothing, since a copy lands at another depth (a
    package in the SDD workspace, a focus file in a scratchpad, a kickoff under local/); its guidance is a line of text,
    never a fill comment. Every `§` citation names a core section of process.md, so none cites an extension or a section
    that is not there. A kickoff opens with its launch line, which cites the binding table where the model is bound (the
    model-id test keeps a model out of it), and every one of its sections cites a section."""
    problems = []
    for name in SKELETON_NAMES:
        path = SKELETONS / name
        if not path.is_file():
            problems.append(f"{name}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        problems += [f"{name}: {found}" for found in skeleton_content_problems(text, kickoff=name.startswith(KICKOFF))]
    assert not problems, "skeletons that link, hold a comment or cite what is not a section:\n" + "\n".join(problems)


def test_the_gate_focus_skeleton_passes_the_launchers_dash_check(tmp_path):
    """The gate-focus skeleton carries no dash-led token (process.md §Adversarial review protocol, The gate package),
    and the launcher is the judge, so the rule keeps its one home: run on the skeleton's text with an empty plugin
    directory, a clean text gets past the dash check and stops at the plugin lookup (CODEX_PLUGIN named on stderr,
    nothing launched), where a dash-led token is refused earlier, exit 2, 'dash' on stderr and the tokens on stdout."""
    path = SKELETONS / "gate-focus.md"
    assert path.is_file(), "docs/skeletons/gate-focus.md is missing"
    done, record = run_gate(tmp_path, path.read_text(encoding="utf-8"))
    assert "dash" not in done.stderr, f"the launcher refused the skeleton:\n{done.stdout}{done.stderr}"
    assert done.returncode != 0 and "CODEX_PLUGIN" in done.stderr, done.stderr
    assert launch(record) is None, "the launcher ran node on the skeleton"


def test_adopting_has_both_paths_and_the_prompt():
    """ADOPTING.md has the guide's three sections, exact and in order. Path B holds one fenced block, the fusion
    session's kickoff prompt: it names what the session reads and makes (PROMPT_NAMES) and holds no link, which a
    pasted session could not follow. The reconciliation checklist is a table headed as CHECKLIST_HEADER, with one row
    for each decision of CHECKLIST_DECISIONS in order, a default in every row and the host's choice empty."""
    text = ADOPTING.read_text(encoding="utf-8")
    assert [heading for heading in section_headings(text) if heading.startswith("## ")] == ADOPTING_SECTIONS
    blocks = fenced_blocks([line for _, line in section_body(text, ADOPTING_SECTIONS[1])])
    assert len(blocks) == 1, f"Path B holds {len(blocks)} fenced blocks, not the one prompt"
    absent = [name for name in PROMPT_NAMES if name not in blocks[0]]
    assert not absent, f"the fusion session's prompt does not name {absent}"
    assert "](" not in blocks[0], "the prompt holds a link, which resolves nothing in a pasted session"
    rows = table_rows([line for _, line in section_body(text, ADOPTING_SECTIONS[2])])
    assert rows and rows[0] == CHECKLIST_HEADER, f"the checklist's header is {rows[:1]}, not {CHECKLIST_HEADER}"
    assert len(rows) > 1 and all(set(cell) <= set("-:") for cell in rows[1]), "the header has no separator row"
    assert [row[0] for row in rows[2:]] == CHECKLIST_DECISIONS
    assert all(len(row) == 3 and row[1] and not row[2] for row in rows[2:]), "a row lacks its default or has a choice"


def test_adopting_names_every_file_that_holds_the_version_token():
    """The placeholder table's row for the pack's version names, as code spans, each file of the starter where the
    token stands and no other: an adopter writes the version at the sites the row names, so a site the row lacks would
    keep its token, and a name the starter no longer holds sends the adopter to a file that is not there."""
    lines = ADOPTING.read_text(encoding="utf-8").splitlines()
    row = next((line for line in lines if line.startswith(f"| `{VERSION_TOKEN}`")), "")
    named = {span for span in re.findall(r"`([^`]+)`", row) if span.endswith(".md")}
    holding = {
        path.relative_to(STARTER).as_posix()
        for path in text_files(STARTER)
        if VERSION_TOKEN in path.read_text(encoding="utf-8")
    }
    assert named == holding, f"the row names {sorted(named)}; the token stands in {sorted(holding)}"


def test_setup_has_the_degrade_table():
    """SETUP.md ends with the table of what degrades without each piece, under the one heading DEGRADE_TABLE spells (the
    model-id check finds the rows where a model may stand by its id or its alias). The table has a header, a separator
    and at least DEGRADE_ROWS rows as wide as the header, none with an empty cell; a row for each of DEGRADE_PIECES; and
    the models its rows name are ones the binding table binds, so that a rebinding cannot leave a row describing a
    default that is gone."""
    assert SETUP.is_file(), "SETUP.md is missing"
    text = SETUP.read_text(encoding="utf-8")
    assert section_headings(text).count(DEGRADE_TABLE) == 1, f"SETUP.md must have the heading '{DEGRADE_TABLE}' once"
    rows = table_rows([line for _, line in section_body(text, DEGRADE_TABLE)])
    assert len(rows) > 1 and all(cell and set(cell) <= set("-:") for cell in rows[1]), "the table has no separator row"
    header, data = rows[0], rows[2:]
    assert len(data) >= DEGRADE_ROWS, f"the table has {len(data)} rows, not {DEGRADE_ROWS}"
    assert all(len(row) == len(header) and all(row) for row in data), "a row is narrower than the header or has a gap"
    absent = [piece for piece in DEGRADE_PIECES if not any(re.search(rf"\b{piece}\b", row[0].lower()) for row in data)]
    assert not absent, f"the table has no row for {absent}"
    cells = [row[1] for row in binding_rows(PROCESS.read_text(encoding="utf-8")).values()]
    bound = {match.group(1) for match in map(DEFAULT_CELL.match, cells) if match}
    named = {match.group(0).strip("`") for row in data for match in MODEL_ID.finditer(" ".join(row))}
    assert named <= bound, f"the table names {sorted(named - bound)}, which the binding table does not bind"


def test_mechanics_index_has_sixteen_rows():
    """mechanics/README.md is the index of the mechanics path B picks from: a table headed INDEX_HEADER with a row for
    each name of MECHANICS, in that order, the name as code and not a link (the pages are to come), a description that
    cites a core section of the contract with a `§`, and a third cell that is one of PATH_B."""
    assert MECHANICS_INDEX.is_file(), "mechanics/README.md is missing"
    rows = table_rows(MECHANICS_INDEX.read_text(encoding="utf-8").splitlines())
    assert rows and rows[0] == INDEX_HEADER, f"the index's header is {rows[:1]}, not {INDEX_HEADER}"
    assert len(rows) > 1 and all(cell and set(cell) <= set("-:") for cell in rows[1]), "the header has no separator row"
    data = rows[2:]
    assert len(data) == len(MECHANICS), f"the index has {len(data)} rows, not {len(MECHANICS)}"
    assert [row[0] for row in data] == [f"`{name}`" for name in MECHANICS]
    assert all(len(row) == len(INDEX_HEADER) and all(row) for row in data), "a row has a missing or an empty cell"
    outside = [f"{row[0]}: '{row[2]}'" for row in data if row[2] not in PATH_B]
    assert not outside, f"a Path B cell outside {sorted(PATH_B)}: {outside}"
    names = core_section_names()
    problems = []
    for row in data:
        cited = section_citations(row[1])
        if not cited:
            problems.append(f"{row[0]} cites no section of process.md with '§'")
        problems += [f"{row[0]} cites '{name}', no core section of process.md" for name in cited if name not in names]
    assert not problems, "the index's descriptions cite the contract by section:\n" + "\n".join(problems)


def test_setup_citations_name_core_sections_of_the_contract():
    """Every `§` in SETUP.md cites a core section of process.md (the runbooks and ADOPTING.md are cited in words), so
    that a section renamed in the contract cannot leave the guide pointing at nothing."""
    assert SETUP.is_file(), "SETUP.md is missing"
    cited = section_citations(SETUP.read_text(encoding="utf-8"))
    assert cited, "SETUP.md cites no section of process.md with '§'"
    stray = sorted({name for name in cited if name not in core_section_names()})
    assert not stray, f"SETUP.md cites {stray}, which are no core sections of process.md"


def test_host_fixture_checks_pass():
    """The example host's own check passes as its CI runs it: `make check` in the fixture's directory exits 0 and runs
    its one test. unittest writes the count to stderr, so both streams are read. The directory is built from this file,
    never from the working directory, since the pack's tests also run in a release clone, where there is no `pack/`. The
    run leaves nothing behind in the pack, which the release tool requires of every test run: the child gets this
    process's environment with bytecode writing off."""
    assert shutil.which("make"), "make is not on the PATH, and the host's check is a make target"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    done = subprocess.run(["make", "-C", str(HOST), "check"], capture_output=True, text=True, env=env, check=False)
    output = done.stdout + done.stderr
    assert done.returncode == 0, output
    assert "Ran 1 test" in output, output


def test_host_fixture_has_its_conventions():
    """The example host has its twelve files, each a regular file, and in them the conventions the fusion session must
    reconcile with the starter's defaults: HOST_FILES gives each file's text (the commit subject and the squash merge,
    the code owners' team, the CI events and command, the make recipe with its tab, the operations headings, the
    handler's signature). The host knows nothing of the pack, so no file names it."""
    problems = []
    for name, markers in HOST_FILES.items():
        path = HOST / name
        if path.is_symlink() or not path.is_file():
            problems.append(f"{name}: not a regular file")
            continue
        text = path.read_text(encoding="utf-8")
        problems += [f"{name}: lacks {marker!r}" for marker in markers if marker not in text]
        if "quoin" in text.lower():
            problems.append(f"{name}: names the pack, which the host knows nothing of")
    assert not problems, "the host fixture lacks what it exists to carry:\n" + "\n".join(problems)


# The checks above are only as good as the helpers they stand on, so these show the helpers reading what they should.


def test_markdown_links_read_outside_fences_and_code_spans():
    text = "\n".join(
        [
            "[a](one.md) and `[b](two.md)` then [c](three.md#part)",
            "```",
            "[d](four.md)",
            "```",
            "~~~",
            "[e](five.md)",
            "~~~",
            "[f](https://example.invalid/x) [g](#here)",
            "    ```",
            "[h](six.md)",
        ]
    )
    assert markdown_links(text) == [
        (1, "one.md"),
        (1, "three.md#part"),
        (8, "https://example.invalid/x"),
        (8, "#here"),
        (10, "six.md"),
    ]


def test_the_link_check_catches_an_escape_and_a_missing_target(tmp_path, monkeypatch):
    pack = tmp_path / "pack"
    pack.mkdir()
    (tmp_path / "above.md").write_text("above the pack\n", encoding="utf-8")
    (pack / "ok.md").write_text("inside the pack\n", encoding="utf-8")
    page = pack / "page.md"
    page.write_text(
        "[escape](../above.md) [missing](missing.md) [absolute](/ok.md) [case](OK.md)\n"
        "[ok](ok.md#part) [anchor](#top) [external](https://example.invalid/x) `[code](nowhere.md)`\n",
        encoding="utf-8",
    )
    monkeypatch.setitem(globals(), "PACK", pack)
    assert unresolved_links(page) == [
        "page.md:1: ../above.md",
        "page.md:1: missing.md",
        "page.md:1: /ok.md",
        "page.md:1: OK.md",
    ]


def test_the_shapes_catch_what_they_name():
    examples = {
        "email": "someone" + "@" + "example.org",
        "openai-key": "sk-" + "a" * 24,
        "github-token": "ghp" + "_" + "a" * 36,
        "aws-key": "AKIA" + "A" * 16,
        "slack-token": "xoxb" + "-" + "1" * 12,
        "private-key": "-----BEGIN " + "RSA PRIVATE KEY" + "-----",
        "jwt": ".".join(["eyJ" + "a" * 12, "b" * 12, "c" * 12]),
    }
    assert set(examples) == set(SHAPES)
    for name, example in examples.items():
        assert SHAPES[name].search(f"a line with {example} in it"), name
    ordinary = "an ordinary line of prose with a v1.2 tag, a 3-part-name and a path like docs/plans/README.md"
    assert not [name for name, shape in SHAPES.items() if shape.search(ordinary)]


def test_github_slug_reads_a_heading_as_github_does():
    assert github_slug("### II. The loop — one item, two sessions") == "ii-the-loop--one-item-two-sessions"
    assert github_slug("## Extension — measurement work") == "extension--measurement-work"
    assert github_slug("### Small-change lane") == "small-change-lane"
    assert github_slug("## A `code_name` (and more)") == "a-code_name-and-more"


def test_without_section_cuts_to_the_next_section_outside_fences():
    text = "# T\n\n## A\n\nkeep\n\n## B\n\n```\n## not a heading\n```\n\ncut\n\n## C\n\nkeep too\n"
    assert without_section(text, "## B") == "# T\n\n## A\n\nkeep\n\n## C\n\nkeep too\n"
    assert without_section(text, "## C") == "# T\n\n## A\n\nkeep\n\n## B\n\n```\n## not a heading\n```\n\ncut\n\n"


def test_fenced_blocks_and_table_rows_read_what_they_should():
    lines = ["text", "```", "one", "| not | a row |", "```", "| a | b |", "~~~", "two", "~~~", "```", "open"]
    assert fenced_blocks(lines) == ["one\n| not | a row |", "two"]
    assert fenced_blocks(["```", "```", "after"]) == [""]
    assert fenced_blocks(["no fence", "at all"]) == []
    rows = ["| Decision | The pack's default |", "|---|:-:|", "| x |  |", "text | not a row", " | indented |", "|a|b|c|"]
    assert table_rows(rows) == [["Decision", "The pack's default"], ["---", ":-:"], ["x", ""], ["a", "b", "c"]]


def test_boot_file_readers_read_what_they_should():
    text = "\n".join(
        [
            "# Title",
            "Goal line.",
            "**Status (a day):** a state.",
            "**Next:** a session.",
            "## Way of working — the digest (x)",
            "- first (process.md §II, the stop; §Budgets)",
            "  continued here (process.md §Model",
            "  policy)",
            "",
            "- second",
            "",
            "```",
            "## not a heading",
            "```",
            "stray prose",
            "## Load-bearing facts",
            "- a fact",
        ]
    )
    assert h1_block(text) == "Goal line.\n**Status (a day):** a state.\n**Next:** a session."
    lines = section_lines(text, DIGEST)
    assert lines[0] == "- first (process.md §II, the stop; §Budgets)" and lines[-1] == "stray prose"
    assert "## not a heading" in lines and "- a fact" not in lines
    assert section_lines(text, "## Absent") == []
    assert top_level_bullets(lines) == [
        "- first (process.md §II, the stop; §Budgets)\n  continued here (process.md §Model\n  policy)",
        "- second",
    ]
    cited = [" ".join(match.group(1).split()) for match in SECTION_CITATION.finditer(text)]
    assert cited == ["II", "Budgets", "Model policy"]
    assert {"II", "Model policy", "Small-change lane", "The seats"} <= core_section_names()
    assert not core_section_names() & {"Extension — measurement work", "measurement work"}
    roadmap = "# R\n**Status: one.**\n\n## A\n**Status: two**\nmore\n\n### B\ntext\n\n**Status: three.**\ntext\n"
    assert status_paragraphs(roadmap) == ["**Status: one.**", "**Status: two**\nmore", "**Status: three.**\ntext"]
    assert status_paragraphs("fill\n**Status: joined.**") == ["fill\n**Status: joined.**"]
    assert status_paragraphs("Status: unbolded\n\n**Status ( not a marker\n") == []


def test_the_sha_rule_reads_hashes_and_nothing_else():
    for hashed in ["abc1234", "merged at 5e8f1a2.", "0123456789abcdef0123", "a defaced tree", "id 20300227"]:
        assert SHA.search(hashed), hashed
    for plain in ["2030-02-27 in PR #12", "a decade ago, a facade, 123456", "abc123 and ABCDEF0", "abcdefg1, v0.1.0"]:
        assert not SHA.search(plain), plain


def test_section_citations_read_prose_cells_and_fences():
    text = "\n".join(
        [
            "Prose (process.md §Adversarial review",
            "protocol; a runbook, section 1) and (process.md §II, stage 3).",
            "",
            "| Without | The rule |",
            "|---|---|",
            "| a piece | process.md §Conventions |",
            "| another | process.md §Budgets; process.md §Model policy, Dispatch |",
            "",
            "```",
            "§Inside a fence",
            "```",
        ]
    )
    assert sorted(section_citations(text)) == sorted(
        ["Adversarial review protocol", "II", "Conventions", "Budgets", "Model policy"]
    )
    assert section_citations("a runbook, section 1, and no citation") == []


def test_text_files_skip_caches_and_binary_files(tmp_path, monkeypatch):
    for name, data in {
        "README.md": b"text\n",
        ".github/workflows/ci.yml": b"on: push\n",
        ".git/config": b"inside git\n",
        "linked/.git": b"gitdir: elsewhere\n",
        "tests/__pycache__/x.pyc": b"a cache\n",
        ".pytest_cache/state": b"a cache\n",
        "blob.bin": b"\xff\xfe\x00",
    }.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_bytes(data)
    monkeypatch.setitem(globals(), "PACK", tmp_path)
    assert [relative(path) for path in text_files()] == [".github/workflows/ci.yml", "README.md"]


def test_the_text_check_catches_other_encodings_and_a_nul(tmp_path):
    """Bytes that are not valid UTF-8, and a NUL byte, which UTF-16 or UTF-32 text without a byte-order mark carries in
    every ASCII character, are each reported by file; UTF-8 with a byte-order mark is text, and .git and the caches
    are not read."""
    for name, data in {
        "README.md": "plain text\n".encode("utf-8"),
        "bom.md": "﻿text with a byte-order mark\n".encode("utf-8"),
        "utf16.md": "text\n".encode("utf-16"),
        "docs/utf16le.md": "text\n".encode("utf-16-le"),
        "latin1.md": "café\n".encode("latin-1"),
        "nul.txt": b"a \x00 byte\n",
        ".git/blob": b"\xff inside git\n",
        "tests/__pycache__/x.pyc": b"\xff a cache\n",
    }.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_bytes(data)
    assert not_utf8_text(tmp_path) == [
        "docs/utf16le.md: a NUL byte",
        "latin1.md: not valid UTF-8",
        "nul.txt: a NUL byte",
        "utf16.md: not valid UTF-8",
    ]


def test_the_model_id_check_reads_the_binding_sites_and_nothing_else(tmp_path):
    """Ids planted at the sites that may name one are read; ids planted anywhere else are reported, each at its line."""
    ok, bad = "claude-" + "sonnet-5-5", "claude-" + "opus-5-5"

    def table(model: str) -> list[str]:
        return ["| Role | Default |", "|---|---|", f"| Counsel | `{model}`, max effort |"]

    files = {
        "starter/docs/process.md": [
            "# Process",
            f"{bad} before the section",
            "## Model policy",
            "### The binding table",
            f"{bad} in the prose of the section",
            *table(ok),
            f"{bad} in the prose after the table",
            "### The seats",
            *table(bad),
        ],
        "starter/.claude/agents/counsel.md": ["---", f"model: {ok}", "---", f"{bad} in the body"],
        "starter/.claude/agents/stray.md": ["no frontmatter", f"model: {bad}"],
        "SETUP.md": [
            "# Setup",
            "## What degrades without each piece",
            f"{bad} in its prose",
            *table(ok),
            "## Next",
            *table(bad),
        ],
        "README.md": [f"{bad} in an ordinary file"],
        "tests/test_x.py": [f'ID = "{bad}"'],
    }
    for name, lines in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    planted = [
        f"{name}:{number}: {bad}"
        for name, lines in files.items()
        for number, line in enumerate(lines, 1)
        if bad in line
    ]
    stray, read = model_id_report(tmp_path)
    assert sorted(stray) == sorted(planted) and len(planted) == 10
    assert read == {"starter/docs/process.md", "starter/.claude/agents/counsel.md", "SETUP.md"}
    empty = tmp_path / "empty"
    empty.mkdir()
    assert model_id_report(empty) == ([], set())
    assert not MODEL_ID.search("claude-code and claude --model <id>, the pattern's own text: " + MODEL_ID.pattern)


def test_binding_rows_read_the_table_of_the_binding_section():
    row = ["Counsel", "`m-1`, max effort", "the same", "`.claude/agents/counsel.md`"]
    header = "| " + " | ".join(BINDING_HEADER) + " |"
    lines = ["## Model policy", "### The binding table", "", header, "|---|---|---|---|"]
    lines += ["| " + " | ".join(row) + " |", "### The seats", "| Seat | x | y | z |"]
    assert binding_rows("\n".join(lines)) == {"Counsel": row}
    for text in ["## Model policy", "\n".join(lines[:3] + ["| Role | Default |", "|---|---|"])]:
        with pytest.raises(ValueError):
            binding_rows(text)


def test_seat_frontmatter_reads_the_subset_of_yaml_the_seats_use():
    good = "---\nname: x\ndescription: >\n  one two\n  three\n\nmodel: m-1\n---\nnot: read\n"
    assert seat_frontmatter(good) == {"name": "x", "description": "one two three", "model": "m-1"}
    for bad in [
        "no frontmatter\n",
        "---\nname: x\n",
        "---\ndescription: >\nnot indented: so not part of the block\n---\n",
        "---\ndescription: Rules: on one question\n---\n",
        "---\ndescription: ends with a colon:\n---\n",
        "---\nmodel: m-1 # a comment YAML would drop\n---\n",
        "---\nname: x\nname: y\n---\n",
        "---\nname: x\n  stray: indented\n---\n",
        "---\nmodel:\n---\n",
    ]:
        with pytest.raises(ValueError):
            seat_frontmatter(bad)


def test_seat_files_are_held_to_the_binding_rows(tmp_path):
    """The comparison behind the frontmatter check, run on seat files planted in a scratch directory: files that match
    their rows pass; a wrong model, effort or tool list, a missing file, an extra file, a malformed frontmatter, a wrong
    name, no description, and a row that is missing or set elsewhere are each reported."""
    ok, wrong = "claude-" + "sonnet-5-5", "claude-" + "opus-5-5"
    rows = {
        role: [role, f"`{ok}`, max effort", "the same", f"`.claude/agents/{seat}.md`"]
        for role, seat in SEAT_ROLES.items()
    }

    def seat_file(seat: str, **changes: str | None) -> str:
        fields = {"name": seat, "description": "A seat.", "model": ok, "effort": "max"}
        fields.update({"disallowedTools": SEAT_TOOLS_REMOVED, **changes})
        lines = [f"{key}: {value}" for key, value in fields.items() if value is not None]
        return "\n".join(["---", *lines, "---", "The charter.", ""])

    for seat in SEAT_ROLES.values():
        (tmp_path / f"{seat}.md").write_text(seat_file(seat), encoding="utf-8")
    assert seat_file_problems(rows, tmp_path) == []

    (tmp_path / "counsel.md").unlink()
    astray = seat_file("reviewer", model=wrong, effort="high", disallowedTools="Edit, Write")
    (tmp_path / "reviewer.md").write_text(astray, encoding="utf-8")
    (tmp_path / "extra.md").write_text("not a seat\n", encoding="utf-8")
    assert seat_file_problems(rows, tmp_path) == [
        "counsel.md: no such seat file",
        f"reviewer.md: model is '{wrong}', the table binds '{ok}'",
        "reviewer.md: effort is 'high', the table binds 'max'",
        f"reviewer.md: disallowedTools is 'Edit, Write', the table binds '{SEAT_TOOLS_REMOVED}'",
        "extra.md: in the agents directory but not a seat file",
    ]

    (tmp_path / "extra.md").unlink()
    (tmp_path / "counsel.md").write_text("no frontmatter\n", encoding="utf-8")
    renamed = seat_file("reviewer", name="review", description=None)
    (tmp_path / "reviewer.md").write_text(renamed, encoding="utf-8")
    rows["Reviewer"][3] = "`.claude/agents/other.md`"
    assert seat_file_problems(rows, tmp_path) == [
        "counsel.md: the file does not open with a frontmatter between two '---' lines",
        "the 'Reviewer' row is set at `.claude/agents/other.md`, not at `.claude/agents/reviewer.md`",
        "reviewer.md: name is 'review', the table binds 'reviewer'",
        "reviewer.md: no description",
    ]
    del rows["Counsel"]
    missing_row = "the binding table has no 'Counsel' row whose default reads `id`, effort"
    assert seat_file_problems(rows, tmp_path)[0] == missing_row


def test_the_skeleton_checks_catch_what_they_name():
    """A good skeleton and a good kickoff pass both checks, and each planted defect is reported by the check that names
    it: for the shape, a heading with two lines, none before the next heading or none at the end of the file, a deeper
    heading held to the same rule, a header paragraph of two lines, no title, two titles and no `## ` heading; for the
    content, a link, a comment, a citation of an unknown section and of an extension, no citation, and for a kickoff
    an opening other than its launch line, a launch line without the binding table or the effort, and a section that
    cites nothing."""

    def text(*lines: str) -> str:
        return "\n".join(lines) + "\n"

    cite = "*Guidance (process.md §II, stage 1).*"
    good = text(
        "# T",
        "",
        "*A field.*",
        "",
        "*Another.*",
        "",
        "## One",
        "",
        cite,
        "",
        "### Deeper",
        "",
        "*More.*",
        "",
        "## Two",
        "",
        cite,
    )
    launch = "Run `claude --model ‹the class's model, process.md §Model policy, the binding table› --effort max`."
    kickoff = text("# K", "", LAUNCH, "", launch, "", "## Reads", "", "Read it (process.md §II, stage 1).")
    assert skeleton_shape_problems(good) == [] and skeleton_content_problems(good) == []
    assert skeleton_shape_problems(kickoff) == [] and skeleton_content_problems(kickoff, kickoff=True) == []
    shape = {
        "two lines": (text("# T", "## One", cite, "more", "## Two", cite), "'## One' is followed by 2"),
        "none before the next heading": (text("# T", "## One", "## Two", cite), "'## One' is followed by 0"),
        "none at the end of the file": (text("# T", "## One", cite, "## Two", ""), "'## Two' is followed by 0"),
        "two under a deeper heading": (text("# T", "## One", "### In", cite, cite), "'### In' is followed by 2"),
        "a header paragraph of two lines": (text("# T", "*a*", "*b*", "", "## One", cite), "more than one line"),
        "no title": (text("## One", cite), "one '# ' title"),
        "two titles": (text("# T", "# U", "## One", cite), "one '# ' title"),
        "no second-level heading": (text("# T", "", "*A field.*"), "no '## ' heading"),
    }
    for what, (planted, expected) in shape.items():
        assert any(expected in found for found in skeleton_shape_problems(planted)), what
    content = {
        "a link": (good.replace("*More.*", "[More](more.md)."), "it links"),
        "a comment": (good.replace("*More.*", "<!-- fill: more; the rule -->"), "HTML comment"),
        "an unknown section": (good.replace("§II, stage 1", "§Imaginary, stage 1"), "cites 'Imaginary'"),
        "an extension": (good.replace("§II", "§" + EXTENSIONS[0][3:]), f"cites '{EXTENSIONS[0][3:]}'"),
        "no citation": (good.replace("§II, stage 1", "stage 1"), "cites no section"),
    }
    for what, (planted, expected) in content.items():
        assert skeleton_shape_problems(planted) == [], what
        assert any(expected in found for found in skeleton_content_problems(planted)), what
    opening = {
        "an opening other than the launch line": (kickoff.replace(LAUNCH, "## Reads first"), "does not open with"),
        "no binding table in the launch line": (kickoff.replace(", the binding table", ""), "does not open with"),
        "no effort in the launch line": (kickoff.replace(" --effort max", ""), "does not open with"),
        "a section that cites nothing": (kickoff.replace("(process.md §II, stage 1)", "now"), "'## Reads' cites no"),
    }
    for what, (planted, expected) in opening.items():
        assert skeleton_shape_problems(planted) == [], what
        assert any(expected in found for found in skeleton_content_problems(planted, kickoff=True)), what
