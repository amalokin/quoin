#!/usr/bin/env python3
"""Hold the documentation to its budgets (docs/process.md, Budgets).

    python3 -I tools/doc_budgets.py check [--root DIR] [--budgets PATH]
    python3 -I tools/doc_budgets.py init [--root DIR] [--budgets PATH] [--force]

``check`` holds the repository at the root (default: the working directory) to its
budgets file (default: docs/doc-budgets.json, read from the root, as are the paths it
names): each budgeted file to its baseline until its ``active`` flag is set, then to its
total, or to its item caps and the total of the rest outside the items; the boot path's
total, a coarse alarm; CLAUDE.md's H1 block; the roadmap's status rules over the
sections whose items are entries; each design header to its baseline plus the allowance
until its row is active, then to the header budget; every docs/designs/*-design.md to a
row of ``design_headers``, and every row to a design; the line limit over the budgeted
files and the active headers; no commit SHA at a status site, and no site emptied; no id
that a design's Active obligations cite found only in its companion log; and every
relative link in CLAUDE.md, AGENTS.md, README.md, the seat charters and docs/ resolving,
but in the dated plans and handoffs, whose dead links are held to the pin
``record_dead_links``: a new one fails, and so does a pinned one that no longer dies.
Each problem is printed on stdout as ``<path>: <message>``, a problem of no one file at
the budgets file, and the count on stderr.
With no design yet (no docs/designs/*-design.md, no design_headers row), no design header need be held.
Exit status: 0 no problem, 1 at least one, 2 the budgets file missing or malformed, or a
file that cannot be read.

``init`` writes the budgets file for a fresh repository: the default numbers, each
budgeted file's baseline measured as it stands, a row for each design with its header's
baseline, all of them active from ``adoption``, and the dated records' dead links as
they stand; then it runs ``check`` against what it wrote and returns its status. It
refuses to overwrite the budgets file without ``--force``, and to run without the five
budgeted files: exit 2.

A design's row in ``design_headers`` is written by hand in the design's first PR (``init``
writes one for each design already on disk): ``baseline_words`` is the header's measured
words, ``target_from`` names when the row is held to the header budget (``init`` writes
``adoption``; the check requires a string and reads no more), and ``active`` is true from
that first PR.

Stdlib only, Python 3.9 or later, so it runs under ``-I``. The counting rules are
process.md's §Budgets: words and tokens are whitespace-split tokens; the H1 block is the
lines after the title line up to the first line starting with ``## ``; a fence opens and
closes with three backticks or three tildes at the start of a line; a table row is a
line whose first non-blank character is ``|``; an entry is a ``### `` or ``#### ``
heading under a named section with its text up to the next heading; a status paragraph
is the run of lines, up to a blank line or a heading, that contains ``**Status:``; a
top-level bullet is a line starting ``- `` at column 0 with the lines after it up to the
next such line, a blank line or a heading.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

FENCES = ("```", "~~~")
HEADING = re.compile(r"#{1,6}\s")
CODE_SPAN = re.compile(r"`[^`]*`")
LINK = re.compile(r"\]\(([^)\s]+)\)")
EXTERNAL = ("http://", "https://", "mailto:", "#")

# The series ids (the id registry's): a hyphenated chain — a head of one to four
# letters or digits starting with a capital, an optional letters-only part, then one
# or two parts of a letter and digits (R-2a-14, R-3b-7, R-Q2-18, R-A5-2, R-ext-3,
# R-K14, R-Q11, R-AB-4, AB-15, AB2-6, D-12, Q-16, A-6, O-4, F-2, H-3, Q3-m2, A4-m3,
# R-plan-F2) — or a bare id of one to three capitals and one or two digits (D14, F7,
# Q02, AB12, DQ4, AF8, RX2, A2, O2, Q4). Never a line citation (L412) or a date.
ID = (
    r"(?:[A-Z][A-Za-z0-9]{0,3}(?:-[A-Za-z]+)?(?:-[A-Za-z]?\d+[a-z]?){1,2}"
    r"|[A-Z]{1,3}\d{1,2}[a-z]?)"
)
# an id is bounded by characters that are neither word characters nor hyphens: "A-4" is
# not found in "A-45" or "A-4-5", "R-3b-7" not in "R-3b-70"
ID_BEFORE = r"(?<![\w-])"
ID_AFTER = r"(?![\w-])"
SERIES = re.compile(ID_BEFORE + ID + ID_AFTER)
# a hex token with at least one letter and one digit, not a decimal fraction's digits
# nor a hyphenated run (batch-20300115 is a directory, not a SHA)
SHA = re.compile(
    r"(?<![\w/.,-])(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,40}(?![\w-])"
)


# --- the counting rules ---------------------------------------------------------


def count_words(text: str) -> int:
    """Count words as whitespace-split tokens."""
    return len(text.split())


def h1_block(text: str) -> str:
    """Return the H1 block: the lines after the title up to the first ``## `` line."""
    block: list[str] = []
    for line in text.splitlines()[1:]:
        if line.startswith("## "):
            break
        block.append(line)
    return "\n".join(block)


def has_section(text: str, section: str) -> bool:
    """Tell whether a line outside fenced code starts with ``section``."""
    fenced = False
    for line in text.splitlines():
        if line.startswith(FENCES):
            fenced = not fenced
        elif not fenced and line.startswith(section):
            return True
    return False


def table_rows(text: str, section: str) -> list[str]:
    """Return the table rows of the ``## `` section starting with ``section``."""
    rows: list[str] = []
    inside = fenced = False
    for line in text.splitlines():
        if line.startswith(FENCES):
            fenced = not fenced
        elif fenced:
            continue
        elif line.startswith("## "):
            inside = line.startswith(section)
        elif inside and line.lstrip().startswith("|"):
            rows.append(line)
    return rows


def status_paragraphs(text: str) -> list[str]:
    """Return the status paragraphs: the runs of lines holding ``**Status:``."""
    paragraphs: list[str] = []
    run: list[str] = []
    for line in text.splitlines() + [""]:
        if not line.strip() or HEADING.match(line):
            if any("**Status:" in item for item in run):
                paragraphs.append("\n".join(run))
            run = []
        else:
            run.append(line)
    return paragraphs


def entries(text: str, section: str) -> list[tuple[str, str]]:
    """Return the ``### `` and ``#### `` headings under ``section`` with their text.

    An entry's text runs up to the next heading of any level; a line inside fenced code
    is never a heading.
    """
    found: list[tuple[str, str]] = []
    current: tuple[str, list[str]] | None = None
    inside = fenced = False
    for line in text.splitlines():
        if line.startswith(FENCES):
            fenced = not fenced
        if HEADING.match(line) and not fenced:
            if current is not None:
                found.append((current[0], "\n".join(current[1])))
            current = None
            if line.startswith("# ") or line.startswith("## "):
                inside = line.startswith(section)
            elif inside and (line.startswith("### ") or line.startswith("#### ")):
                current = (line, [])
        elif current is not None:
            current[1].append(line)
    if current is not None:
        found.append((current[0], "\n".join(current[1])))
    return found


def entry_headings(text: str, section: str) -> list[str]:
    """Return the entry heading lines under ``section`` by a whole-section scan.

    Counted apart from the line-by-line walk of ``entries``, so that the two disagree
    when either loses or invents a heading.
    """
    prose = "\n".join(line for _, line in prose_lines(text))
    pattern = re.compile(
        r"^" + re.escape(section) + r"[^\n]*\n(.*?)(?=^#{1,2} |\Z)", re.M | re.S
    )
    return [
        line
        for body in pattern.findall(prose)
        for line in body.splitlines()
        if line.startswith(("### ", "#### "))
    ]


def entry_items(text: str, section: str) -> list[str]:
    """Return each entry under ``section`` as one text, its heading line first."""
    return [f"{heading}\n{body}" for heading, body in entries(text, section)]


def top_level_bullets(text: str, section: str) -> list[str]:
    """Return the top-level bullets of the sections headed ``section``.

    A bullet is a line starting ``- `` at column 0 and the lines after it up to the next
    such line, a blank line or a heading; a fenced line is neither a bullet nor a
    heading.
    """
    bullets: list[str] = []
    current: list[str] | None = None
    inside = fenced = False
    for line in text.splitlines():
        if line.startswith(FENCES):
            fenced = not fenced
        heading = bool(not fenced and HEADING.match(line))
        starts = not fenced and line.startswith("- ")
        if current is not None and (heading or starts or not line.strip()):
            bullets.append("\n".join(current))
            current = None
        if heading and line.startswith(("# ", "## ")):
            inside = line.startswith(section)
        if inside and starts:
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        bullets.append("\n".join(current))
    return bullets


ITEM_KINDS: dict[str, Callable[[str, str], list[str]]] = {
    "table row": table_rows,
    "entry": entry_items,
    "top-level bullet": top_level_bullets,
}


def section_items(text: str, section: str, rule: dict[str, object]) -> list[str]:
    """Return the items of kind ``rule`` in the sections headed ``section``."""
    return ITEM_KINDS[str(rule["item"])](text, section)


def count_rest(text: str, item_sections: dict[str, dict[str, object]]) -> int:
    """Count the words of ``text`` outside every item of ``item_sections``."""
    return count_words(text) - sum(
        count_words(item)
        for section, rule in item_sections.items()
        for item in section_items(text, section, rule)
    )


def item_problems(text: str, item_sections: dict[str, dict[str, object]]) -> list[str]:
    """List the growing lists' failures: an item over its cap or a lost section."""
    problems: list[str] = []
    for section, rule in item_sections.items():
        if not has_section(text, section):
            problems.append(f"no section headed `{section}`: is its heading renamed?")
            continue
        items = section_items(text, section, rule)
        if not items:
            problems.append(f"no {rule['item']} in the `{section}` section")
        limit = int(str(rule["max_words"]))
        for item in items:
            if count_words(item) > limit:
                problems.append(
                    f"a {rule['item']} of {count_words(item)} words in `{section}`, "
                    f"over its {limit}: {item.splitlines()[0][:60]}"
                )
    return problems


def file_budget_problems(text: str, entry: dict[str, object]) -> list[str]:
    """List a budgeted file's failures: its baseline before cleanup, its caps after."""
    words = count_words(text)
    if not entry["active"]:
        limit = int(str(entry["baseline_words"]))
        return [f"{words} words, over its baseline of {limit}"] if words > limit else []
    if "item_sections" not in entry:
        limit = int(str(entry["target_words"]))
        return [f"{words} words, over its total of {limit}"] if words > limit else []
    sections = entry["item_sections"]
    assert isinstance(sections, dict)
    problems = item_problems(text, sections)
    rest, limit = count_rest(text, sections), int(str(entry["rest_words"]))
    if rest > limit:
        problems.append(
            f"the rest, outside the items, of {rest} words, over its total of {limit}"
        )
    return problems


def roadmap_status_problems(
    text: str, word_limit: int, sections: Sequence[str]
) -> list[str]:
    """List what fails in the roadmap's status rules over the entries of ``sections``.

    Every status paragraph is within ``word_limit`` words, each entry holds exactly one
    and no unbolded ``Status:``, the fences balance, and the checks cover something: a
    status paragraph exists, entries exist, and the walk finds as many entries as the
    whole-section scan finds headings.
    """
    problems: list[str] = []
    fences = sum(1 for line in text.splitlines() if line.startswith(FENCES))
    if fences % 2:
        problems.append(
            f"{fences} fence lines: an unclosed fence hides every entry after it"
        )
    paragraphs = status_paragraphs(text)
    if not paragraphs:
        problems.append("no status paragraph: is every `**Status:` marker unbolded?")
    for paragraph in paragraphs:
        if count_words(paragraph) > word_limit:
            problems.append(
                f"a status paragraph of {count_words(paragraph)} words: "
                f"{paragraph[:50]}"
            )
    found: list[tuple[str, str]] = []
    headings: list[str] = []
    for section in sections:
        found += entries(text, section)
        headings += entry_headings(text, section)
    if not found:
        problems.append("no entries: are the section headings renamed?")
    if len(found) != len(headings):
        problems.append(f"{len(found)} entries for {len(headings)} headings")
    for heading, body in found:
        count = len(status_paragraphs(body))
        if count != 1:
            problems.append(f"{heading}: {count} status paragraphs, not exactly one")
    if re.search(r"(?<!\*\*)\bStatus:", "\n".join(body for _, body in found)):
        problems.append("an unbolded `Status:` in an entry")
    return problems


def boot_path_problems(texts: Iterable[str], limit: int) -> list[str]:
    """List the boot path's total over ``limit``, a coarse alarm."""
    total = sum(count_words(text) for text in texts)
    return (
        [f"the boot path's {total} words, over its alarm of {limit}"]
        if total > limit
        else []
    )


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Return (number, line) of every prose line: outside fences, not a table row."""
    lines: list[tuple[int, str]] = []
    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith(FENCES):
            fenced = not fenced
        elif not fenced and not line.lstrip().startswith("|"):
            lines.append((number, line))
    return lines


def long_lines(text: str, limit: int) -> list[int]:
    """Return the numbers of the prose lines longer than ``limit`` characters."""
    return [number for number, line in prose_lines(text) if len(line) > limit]


def relative_links(text: str) -> list[str]:
    """Return the targets of ``[…](target)`` links outside fenced code and code spans.

    External and ``#…`` targets are skipped.
    """
    links: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith(FENCES):
            fenced = not fenced
        elif not fenced:
            links += [
                target
                for target in LINK.findall(CODE_SPAN.sub("", line))
                if not target.startswith(EXTERNAL)
            ]
    return links


def now_and_next(text: str) -> list[str]:
    """Return the lines of the roadmap's ``## Now and next`` section."""
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.startswith("## Now and next")
        elif inside:
            lines.append(line)
    return lines


def status_site_lines(
    roadmap_text: str, claude_text: str, header_texts: Sequence[str]
) -> list[str]:
    """Return every line a commit SHA must not stand on (process.md §II stage 7)."""
    lines: list[str] = []
    for paragraph in status_paragraphs(roadmap_text):
        lines += paragraph.splitlines()
    lines += now_and_next(roadmap_text)
    lines += h1_block(claude_text).splitlines()
    for text in header_texts:
        lines += h1_block(text).splitlines()
    return lines


def sha_lines(lines: Iterable[str]) -> list[str]:
    """Return the lines that carry a commit SHA."""
    return [line for line in lines if SHA.search(line)]


CLAUDE_HEADER_MARKERS = ("**Status", "**Next:**")
DESIGN_STATUS_MARKER = "Status:"


def status_site_problems(
    roadmap_text: str, claude_text: str, header_texts: Sequence[str]
) -> list[str]:
    """List what fails in the no-SHA rule: a SHA at a status site, or a site emptied.

    The roadmap's status paragraphs and a non-blank "Now and next", CLAUDE.md's header
    block with a line starting ``**Status`` and one starting ``**Next:**``, and at least
    one design header holding ``Status:`` must exist, so that a renamed heading or an
    unbolded marker cannot take a site out of the check.
    """
    problems: list[str] = []
    if not status_paragraphs(roadmap_text):
        problems.append(
            "no roadmap status paragraph: is every `**Status:` marker unbolded?"
        )
    if not "".join(now_and_next(roadmap_text)).strip():
        problems.append("no `## Now and next` lines in the roadmap: renamed, or blank?")
    claude_block = h1_block(claude_text)
    if not claude_block.strip():
        problems.append(
            "CLAUDE.md's header block is empty: does a `## ` line follow its title?"
        )
    else:
        for marker in CLAUDE_HEADER_MARKERS:
            if not any(line.startswith(marker) for line in claude_block.splitlines()):
                problems.append(
                    f"CLAUDE.md's header block has no line starting with `{marker}`"
                )
    if not header_texts:
        problems.append("no design header is held to the rule")
    for text in header_texts:
        block, title = h1_block(text), text.partition("\n")[0]
        if not block.strip():
            problems.append(f"an empty design header: {title}")
        elif DESIGN_STATUS_MARKER not in block:
            problems.append(
                f"a design header without `{DESIGN_STATUS_MARKER}`: {title}"
            )
    lines = status_site_lines(roadmap_text, claude_text, header_texts)
    return problems + [
        f"a commit SHA at a status site: {line}" for line in sha_lines(lines)
    ]


RECORD_DIRS = (("docs", "plans"), ("docs", "handoffs"))


def is_dated_record(path: Path, root: Path) -> bool:
    """Tell whether ``path`` is a dated record (a plan or handoff, not its index)."""
    parts = path.relative_to(root).parts
    return parts[:2] in RECORD_DIRS and parts[2:] != ("README.md",)


def markdown_files(root: Path) -> list[Path]:
    """Return CLAUDE.md, AGENTS.md, README.md, the seat charters and ``docs/**/*.md``.

    The seat charters are ``.claude/agents/*.md``.
    """
    return [
        root / "CLAUDE.md",
        root / "AGENTS.md",
        root / "README.md",
        *sorted((root / ".claude" / "agents").glob("*.md")),
        *sorted((root / "docs").rglob("*.md")),
    ]


def dead_links(root: Path, records: bool) -> list[tuple[str, str]]:
    """Return (file, link) of every relative link that resolves to nothing.

    With ``records`` false the dated records are skipped (theirs are asserted against a
    pin); with it true only the dated records are read.
    """
    dead: list[tuple[str, str]] = []
    for path in markdown_files(root):
        if not path.is_file() or is_dated_record(path, root) != records:
            continue
        for link in relative_links(path.read_text(encoding="utf-8")):
            if not (path.parent / link.split("#")[0]).exists():
                dead.append((str(path.relative_to(root)), link))
    return sorted(dead)


ACTIVE_OBLIGATIONS = re.compile(
    r"\n## (?:\d+\. )?Active obligations[^\n]*\n(.*?)(?=\n## |\Z)", re.S
)


def obligations_only_in_companion_logs(root: Path) -> list[tuple[str, str]]:
    """Return (design, id) cited by Active obligations yet found only in the log.

    An id absent from both the design and its companion log is another document's and
    is skipped.
    """
    buried: list[tuple[str, str]] = []
    for design in sorted((root / "docs" / "designs").glob("*-design.md")):
        text = design.read_text(encoding="utf-8")
        match = ACTIVE_OBLIGATIONS.search(text)
        if not match:
            continue
        rest = text[: match.start()] + text[match.end() :]
        log = design.with_name(design.stem + "-log.md")
        companion = log.read_text(encoding="utf-8") if log.exists() else ""
        for ident in re.findall(
            ID_BEFORE + r"(?:" + ID + r"|20\d\d-\d\d-\d\d)" + ID_AFTER, match.group(1)
        ):
            bounded = ID_BEFORE + re.escape(ident) + ID_AFTER
            if not re.search(bounded, rest) and re.search(bounded, companion):
                buried.append((design.name, ident))
    return buried


# --- the two commands -----------------------------------------------------------

BUDGETS = "docs/doc-budgets.json"
CLAUDE = "CLAUDE.md"
ROADMAP = "docs/roadmap.md"
DESIGNS = "docs/designs"
DESIGN_GLOB = "*-design.md"
# What a session reads at its start; their total is a coarse alarm.
BOOT_PATH = ("CLAUDE.md", "docs/roadmap.md", "docs/process.md", "AGENTS.md")
NO_DESIGN_HEADER = "no design header is held to the rule"
SHA_AT_A_SITE = "a commit SHA at a status site: "
DESIGN_GUARDS = ("an empty design header: ", "a design header without ")
NUMBER_KEYS = (
    "line_limit_chars",
    "boot_path_total_words",
    "claude_h1_block_words",
    "roadmap_status_paragraph_words",
    "design_header_words",
    "inactive_header_allowance_words",
    "memory_index_chars",
)
# The one number that may be 0: an inactive header allowed no growth past its baseline.
MAY_BE_ZERO = ("inactive_header_allowance_words",)
# What ``init`` writes: the numbers, then each budgeted file's total, or its item
# sections (the kind of item and its cap) and the total of the rest; ``init`` adds each
# file's baseline, its ``target_from`` and its ``active`` flag.
DEFAULTS: dict[str, Any] = {
    "line_limit_chars": 400,
    "boot_path_total_words": 20000,
    "claude_h1_block_words": 350,
    "roadmap_status_paragraph_words": 40,
    "design_header_words": 250,
    "inactive_header_allowance_words": 100,
    "memory_index_chars": 2500,
    "files": {
        "CLAUDE.md": {
            "rest_words": 900,
            "item_sections": {
                "## Doc map": {"item": "table row", "max_words": 30},
                "## Load-bearing facts": {"item": "top-level bullet", "max_words": 200},
            },
        },
        "docs/roadmap.md": {
            "rest_words": 1200,
            "item_sections": {
                "## Items": {"item": "entry", "max_words": 200},
                "## Parking lot": {"item": "top-level bullet", "max_words": 200},
                "## Standing decisions": {"item": "top-level bullet", "max_words": 200},
            },
        },
        "docs/process.md": {"target_words": 10500},
        "AGENTS.md": {"target_words": 2000},
        "README.md": {"target_words": 700},
    },
}
TARGET_FROM = "adoption"


class Malformed(Exception):
    """Signal a budgets file that is missing or malformed: the exit status is 2."""


def whole(value: object, least: int = 1) -> bool:
    """Tell whether ``value`` is a whole number of at least ``least``, not a boolean."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= least


def entry_faults(entry: object) -> list[str]:
    """List what an entry of ``files`` or ``design_headers`` lacks of their common keys."""
    if not isinstance(entry, dict):
        return ["not an object"]
    faults: list[str] = []
    if not whole(entry.get("baseline_words"), 0):
        faults.append("`baseline_words` is not a whole number")
    if not isinstance(entry.get("target_from"), str):
        faults.append("`target_from` is not a string")
    if not isinstance(entry.get("active"), bool):
        faults.append("`active` is neither true nor false")
    return faults


def file_entry_faults(entry: object) -> list[str]:
    """List what makes an entry of ``files`` malformed, its item sections included.

    An entry has a total (``target_words``) or item sections with the total of the rest
    (``rest_words``, which ``file_budget_problems`` reads whenever the sections are
    there); each section is a ``## `` heading's start that no other section's starts
    with, its rule a kind of item and a cap.
    """
    faults = entry_faults(entry)
    if not isinstance(entry, dict):
        return faults
    sectioned = "item_sections" in entry
    if sectioned == ("target_words" in entry):
        faults.append("it needs `target_words` or `item_sections`, one and not both")
    if sectioned != ("rest_words" in entry):
        faults.append("`rest_words` goes with `item_sections`, and only with them")
    for key in ("target_words", "rest_words"):
        if key in entry and not whole(entry[key]):
            faults.append(f"`{key}` is not a positive whole number")
    sections = entry.get("item_sections", {})
    if not isinstance(sections, dict):
        return faults + ["`item_sections` is not an object"]
    for section, rule in sections.items():
        if not section.startswith("## "):
            faults.append(f"the section `{section}` does not start with `## `")
        if not (
            isinstance(rule, dict)
            and set(rule) == {"item", "max_words"}
            and isinstance(rule["item"], str)
            and rule["item"] in ITEM_KINDS
            and whole(rule["max_words"])
        ):
            faults.append(
                f"the rule of `{section}` is not an `item` of "
                f"{', '.join(ITEM_KINDS)} with a positive whole `max_words`"
            )
    faults += [
        f"`{later}` starts with `{section}`, so its items would count twice"
        for section in sections
        for later in sections
        if later != section and later.startswith(section)
    ]
    return faults


def budget_faults(budgets: object) -> list[str]:
    """List what makes a budgets file malformed: a key missing or a value misshapen."""
    if not isinstance(budgets, dict):
        return ["not a JSON object"]
    faults = [
        f"`{key}` is not a {'' if key in MAY_BE_ZERO else 'positive '}whole number"
        for key in NUMBER_KEYS
        if not whole(budgets.get(key), 0 if key in MAY_BE_ZERO else 1)
    ]
    faults += [
        f"`{key}` is not an object"
        for key in ("files", "design_headers")
        if not isinstance(budgets.get(key), dict)
    ]
    pin = budgets.get("record_dead_links")
    if not isinstance(pin, list) or not all(
        isinstance(pair, list)
        and len(pair) == 2
        and all(isinstance(part, str) for part in pair)
        for pair in pin
    ):
        faults.append("`record_dead_links` is not a list of [record, link] pairs")
    if faults:
        return faults
    for path, entry in budgets["files"].items():
        faults += [f"files, {path}: {fault}" for fault in file_entry_faults(entry)]
    for path, entry in budgets["design_headers"].items():
        faults += [f"design_headers, {path}: {fault}" for fault in entry_faults(entry)]
    if not entry_sections(budgets["files"]):
        faults.append(
            f"files, {ROADMAP}: no item section of `entry` items, where the roadmap's "
            "status rules read its entries"
        )
    return faults


def entry_sections(files: dict[str, Any]) -> list[str]:
    """Return the roadmap's item sections whose items are entries, as ``files`` names them."""
    roadmap = files.get(ROADMAP)
    sections = roadmap.get("item_sections") if isinstance(roadmap, dict) else None
    if not isinstance(sections, dict):
        return []
    return [
        section
        for section, rule in sections.items()
        if isinstance(rule, dict) and rule.get("item") == "entry"
    ]


def load_budgets(path: Path) -> dict[str, Any]:
    """Read the budgets file; raise ``Malformed`` when it is missing or malformed."""
    if not path.is_file():
        raise Malformed("no such file (`init` writes it)")
    try:
        budgets = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise Malformed(f"not JSON: {exc}") from None
    faults = budget_faults(budgets)
    if faults:
        raise Malformed("malformed: " + "; ".join(faults))
    return dict(budgets)


class Reader:
    """Read each file of a repository once, keeping the paths of the missing ones."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.texts: dict[str, str] = {}
        self.missing: list[str] = []

    def __call__(self, path: str) -> str:
        """Return the text of ``path``, or the empty text for a file that is missing."""
        if path not in self.texts:
            file = self.root / path
            if file.is_file():
                self.texts[path] = file.read_text(encoding="utf-8")
            else:
                self.texts[path] = ""
                self.missing.append(path)
        return self.texts[path]


def designs_on_disk(root: Path) -> list[str]:
    """Return the path, from the root, of every ``docs/designs/*-design.md``."""
    return sorted(
        path.relative_to(root).as_posix() for path in (root / DESIGNS).glob(DESIGN_GLOB)
    )


def too_long(number: int, limit: int) -> str:
    """Say that line ``number`` is over the line limit."""
    return f"line {number} is longer than the line limit of {limit} characters"


def status_site_report(
    roadmap: str,
    claude: str,
    held: Sequence[tuple[str, str]],
    where: str,
    waived: bool,
) -> list[tuple[str, str]]:
    """Run the no-SHA rule over the status sites; return each problem with its file.

    ``held`` is the (path, text) of each design whose row is active. A SHA goes to the
    file of its site, in the order the rule reads the sites; a design header's guard to
    the first held design whose header alone gives it; a guard of the roadmap or of
    CLAUDE.md to that file; and the guard that no design header is held to the budgets
    file ``where`` — or nowhere when ``waived``: before the first design, with none on
    disk and no row, there is no header to hold.
    """
    sites = [
        (ROADMAP, status_site_lines(roadmap, "", [])),
        (CLAUDE, status_site_lines("", claude, [])),
    ]
    sites += [(path, status_site_lines("", "", [text])) for path, text in held]
    shas = iter([path for path, lines in sites for _ in sha_lines(lines)])
    pending = list(held)
    report: list[tuple[str, str]] = []
    for message in status_site_problems(roadmap, claude, [text for _, text in held]):
        if message.startswith(SHA_AT_A_SITE):
            path = next(shas, where)
        elif message == NO_DESIGN_HEADER:
            if waived:
                continue
            path = where
        elif message.startswith(DESIGN_GUARDS):
            index = next(
                (
                    index
                    for index, (_, text) in enumerate(pending)
                    if message in status_site_problems("", "", [text])
                ),
                None,
            )
            path = DESIGNS if index is None else pending.pop(index)[0]
        elif message.startswith(CLAUDE):
            path = CLAUDE
        else:
            path = ROADMAP
        report.append((path, message))
    return report


def pin_problems(
    dead: Sequence[tuple[str, str]], pin: Sequence[Sequence[str]], where: str
) -> list[tuple[str, str]]:
    """Hold the dated records' dead links to their pin, in both directions.

    A dead link the pin lacks fails at its record; a pinned link that no longer dies,
    resolved or its record gone, fails at the budgets file ``where``, and so does a pin
    out of the order ``dead_links`` gives (sorted, with multiplicity).
    """
    pinned = [(record, link) for record, link in pin]
    found: list[tuple[str, str]] = []
    if pinned != sorted(pinned):
        found.append((where, "record_dead_links is not sorted"))
    found += [
        (record, f"a dead link not on {where}'s record_dead_links pin: {link}")
        for record, link in sorted((Counter(dead) - Counter(pinned)).elements())
    ]
    found += [
        (where, f"record_dead_links pins a link that no longer dies: {record}: {link}")
        for record, link in sorted((Counter(pinned) - Counter(dead)).elements())
    ]
    return found


def check_problems(
    root: Path, budgets: dict[str, Any], where: str
) -> tuple[list[tuple[str, str]], bool]:
    """Return every problem of the repository at ``root`` as (path, message), by rule,
    and whether the repository has no design yet.

    ``where`` is the budgets file's path, at which a problem of no one file is told. No
    design yet — no ``docs/designs/*-design.md`` and no row in ``design_headers`` — is
    the one case in which no design header need be held to the no-SHA rule.
    """
    read = Reader(root)
    files: dict[str, dict[str, Any]] = budgets["files"]
    rows: dict[str, dict[str, Any]] = budgets["design_headers"]
    limit = budgets["line_limit_chars"]
    found: list[tuple[str, str]] = []
    for path, entry in files.items():
        text = read(path)
        if path not in read.missing:
            found += [(path, message) for message in file_budget_problems(text, entry)]
            found += [(path, too_long(line, limit)) for line in long_lines(text, limit)]
    claude, roadmap = read(CLAUDE), read(ROADMAP)
    words, cap = count_words(h1_block(claude)), budgets["claude_h1_block_words"]
    if words > cap:
        found.append((CLAUDE, f"an H1 block of {words} words, over its {cap}"))
    paragraph = budgets["roadmap_status_paragraph_words"]
    found += [
        (ROADMAP, message)
        for message in roadmap_status_problems(roadmap, paragraph, entry_sections(files))
    ]
    boot = [read(path) for path in BOOT_PATH]
    found += [
        (where, message)
        for message in boot_path_problems(boot, budgets["boot_path_total_words"])
    ]
    designs = designs_on_disk(root)
    found += [
        (path, f"no row in {where}'s design_headers: a design gets one in its first PR")
        for path in designs
        if path not in rows
    ]
    found += [
        (path, f"a row in {where}'s design_headers, but no such design")
        for path in rows
        if path not in designs
    ]
    held: list[tuple[str, str]] = []
    for path, entry in rows.items():
        if path not in designs:
            continue
        text = (root / path).read_text(encoding="utf-8")
        block = h1_block(text)
        words = count_words(block)
        if entry["active"]:
            cap = budgets["design_header_words"]
            if words > cap:
                found.append((path, f"a header of {words} words, over its {cap}"))
            # the header starts on the line after the title: its line n is the file's n + 1
            found += [
                (path, too_long(line + 1, limit)) for line in long_lines(block, limit)
            ]
            held.append((path, text))
        else:
            baseline = entry["baseline_words"]
            allowance = budgets["inactive_header_allowance_words"]
            if words > baseline + allowance:
                found.append(
                    (
                        path,
                        f"a header of {words} words, over its baseline of {baseline} "
                        f"and the allowance of {allowance}",
                    )
                )
    no_design = not designs and not rows
    found += status_site_report(roadmap, claude, held, where, no_design)
    found += [
        (
            f"{DESIGNS}/{design}",
            f"`{ident}`, cited by its Active obligations, is found only in its "
            "companion log",
        )
        for design, ident in obligations_only_in_companion_logs(root)
    ]
    found += [
        (path, f"a relative link that resolves to nothing: {link}")
        for path, link in dead_links(root, records=False)
    ]
    dead = dead_links(root, records=True)
    found += pin_problems(dead, budgets["record_dead_links"], where)
    return [(path, "no such file") for path in read.missing] + found, no_design


def run_check(root: Path, where: str) -> int:
    """Check the repository at ``root`` against its budgets file; return the status."""
    try:
        budgets = load_budgets(root / where)
    except Malformed as exc:
        sys.stderr.write(f"doc_budgets: {where}: {exc}\n")
        return 2
    problems, no_design = check_problems(root, budgets, where)
    for path, message in problems:
        sys.stdout.write(f"{path}: {message}\n")
    if no_design:
        sys.stderr.write("check: no design yet: no header is held until the first lands\n")
    plural = "" if len(problems) == 1 else "s"
    sys.stderr.write(f"check: {len(problems)} problem{plural}\n")
    return 1 if problems else 0


def cmd_check(args: argparse.Namespace) -> int:
    """Run ``check``; return the exit status."""
    return run_check(Path(args.root), args.budgets)


def initial_budgets(root: Path) -> dict[str, Any]:
    """Return the budgets file for ``root``: the defaults, every baseline measured."""
    budgets: dict[str, Any] = {key: DEFAULTS[key] for key in NUMBER_KEYS}
    budgets["files"] = {}
    for path, shape in DEFAULTS["files"].items():
        text = (root / path).read_text(encoding="utf-8")
        entry: dict[str, Any] = {"baseline_words": count_words(text)}
        entry.update(copy.deepcopy(shape))
        entry.update(target_from=TARGET_FROM, active=True)
        budgets["files"][path] = entry
    budgets["design_headers"] = {}
    for path in designs_on_disk(root):
        header = h1_block((root / path).read_text(encoding="utf-8"))
        budgets["design_headers"][path] = {
            "baseline_words": count_words(header),
            "target_from": TARGET_FROM,
            "active": True,
        }
    budgets["record_dead_links"] = [list(pair) for pair in dead_links(root, records=True)]
    return budgets


def cmd_init(args: argparse.Namespace) -> int:
    """Run ``init``: write the budgets file, then check against it; return the status."""
    root = Path(args.root)
    target = root / args.budgets
    if target.exists() and not args.force:
        sys.stderr.write(f"doc_budgets: {target} exists: pass --force to overwrite it\n")
        return 2
    missing = [path for path in DEFAULTS["files"] if not (root / path).is_file()]
    if missing:
        sys.stderr.write(
            f"doc_budgets: no {', '.join(missing)} under {root}: init measures each "
            "budgeted file as it stands\n"
        )
        return 2
    budgets = initial_budgets(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(budgets, indent=2, ensure_ascii=False) + "\n"
    target.write_text(text, encoding="utf-8")
    sys.stderr.write(
        f"init: wrote {target}: {len(budgets['files'])} files, "
        f"{len(budgets['design_headers'])} designs, "
        f"{len(budgets['record_dead_links'])} pinned dead links\n"
    )
    return run_check(root, args.budgets)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="doc_budgets.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", metavar="{check,init}")
    commands.required = True
    check = commands.add_parser(
        "check", help="hold the repository to its budgets file; exit 0, 1 or 2"
    )
    init = commands.add_parser(
        "init", help="write the budgets file for a fresh repository, then check it"
    )
    for command in (check, init):
        command.add_argument(
            "--root",
            default=".",
            metavar="DIR",
            help="the repository's root (default: the working directory)",
        )
        command.add_argument(
            "--budgets",
            default=BUDGETS,
            metavar="PATH",
            help=f"the budgets file, from the root (default: {BUDGETS})",
        )
    init.add_argument(
        "--force", action="store_true", help="overwrite an existing budgets file"
    )
    check.set_defaults(func=cmd_check)
    init.set_defaults(func=cmd_init)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command line; return the exit status."""
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"doc_budgets: {exc}\n")
        return 2


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
