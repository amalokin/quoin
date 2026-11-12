"""The document checks over fixtures, and their two commands over temporary repositories.

Each rule here has a case that passes and a case that fails when that rule alone is
removed: the counting rules; the item caps, the rests and the whole-file totals at their
limits; the boot-path alarm; the roadmap's status rules and the cross-check of its two
entry walkers; the SHA pattern clause by clause and at each status site; the guards that
keep a site in the check; the id regex; both halves of the obligations test and its
dates; the links. ``init`` and ``check`` run over a temporary repository that holds the
five budgeted files: the defaults ``init`` writes, its refusal to overwrite and its
check of what it wrote; ``check``'s exit statuses and a malformed budgets file; a
repository with no design yet, and the designs and their rows held one for one once one
exists; the dated records held to their pin of dead links; and each problem printed at
the file it is about.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from tools import doc_budgets as dc

ROADMAP = """# Roadmap

*Intro.*

## Now and next

- **Now.** Nothing running.

## Items

### 1. First item
Goal text.
**Anchor:** a check.

**Status: done 2030-01-15 (PR #3).** Headline. [design](designs/a.md)

### 2. Item two
Goal.

**Status: in waves.** Two waves.

#### 2a. Wave a
Goal.

**Status: implemented 2030-03-02 (PR #11).** Headline.

## Later items

### 3. Third item
Goal.

**Status: implemented 2030-02-10 (PR #8).** Headline.

## Parking lot

- One parked thing
  wrapped over two lines.
- Another.

## Standing decisions

- **Made:** a rule.
"""

CLAUDE = """# Title

Goal paragraph.

**Status (2030-04-01):** merged through PR #12.

**Next:** the next session.

## Doc map

| Doc | Read when |
|---|---|
| [roadmap](docs/roadmap.md) | Start here |

## Load-bearing facts

- **Alpha** one fact.
- **Beta** another
  wrapped.
"""

DESIGN = """# A design

*Proposed 2030-01-15. Depth: implementable. Status: done (PR #3).*

## Goal

Text.
"""

SECTIONS = ("## Items", "## Later items")
A_SHA = "abc1234"


def test_count_words_and_h1_block() -> None:
    """Count whitespace tokens, and take the header block up to the first ``## ``."""
    assert dc.count_words("a b  c\nd") == 4
    assert dc.h1_block(CLAUDE).strip().startswith("Goal paragraph.")
    assert "Doc map" not in dc.h1_block(CLAUDE)
    assert dc.h1_block("# T\nintro\n### Sub\ntext\n## Next\nrest\n") == (
        "intro\n### Sub\ntext"
    )


def test_table_rows_skip_fences_and_other_sections() -> None:
    """Count a section's rows whole, an indented one too, and skip fenced rows."""
    text = (
        CLAUDE
        + "\n## Other\n\n```\n| not | a row |\n```\n| x | y |\n  | indented | row |\n"
    )
    assert dc.table_rows(text, "## Doc map") == [
        "| Doc | Read when |",
        "|---|---|",
        "| [roadmap](docs/roadmap.md) | Start here |",
    ]
    assert dc.table_rows(text, "## Other") == ["| x | y |", "  | indented | row |"]


def test_status_paragraphs_run_to_a_blank_line_or_heading() -> None:
    """Take the run of lines around ``**Status:``, up to a blank line or a heading."""
    paragraphs = dc.status_paragraphs(ROADMAP)
    assert len(paragraphs) == 4
    assert paragraphs[0].startswith("**Status: done 2030-01-15")
    assert "Goal text" not in paragraphs[0]
    assert dc.status_paragraphs("### H\n**Status: a.** b\n#### I\nc\n") == [
        "**Status: a.** b"
    ]


def test_entries_cover_both_levels_and_match_the_heading_scan() -> None:
    """Walk ``###`` and ``####`` entries under a section, each ending at a heading."""
    items = dc.entries(ROADMAP, "## Items")
    assert [heading for heading, _ in items] == [
        "### 1. First item",
        "### 2. Item two",
        "#### 2a. Wave a",
    ]
    assert "2a" not in items[1][1]
    assert dc.entry_headings(ROADMAP, "## Items") == [heading for heading, _ in items]
    assert [heading for heading, _ in dc.entries(ROADMAP, "## Later items")] == [
        "### 3. Third item"
    ]


def test_a_fenced_heading_is_not_an_entry() -> None:
    """Ignore a ``###`` line inside fenced code in both the walk and the scan."""
    text = ROADMAP.replace("Goal text.", "Goal text.\n```\n### not an entry\n```")
    assert len(dc.entries(text, "## Items")) == 3
    assert len(dc.entry_headings(text, "## Items")) == 3


def test_top_level_bullets_include_wrapped_lines() -> None:
    """Take a bullet with its wrapped and fenced lines, ending at a blank or heading."""
    bullets = dc.top_level_bullets(ROADMAP, "## Parking lot")
    assert bullets == ["- One parked thing\n  wrapped over two lines.", "- Another."]
    assert dc.top_level_bullets(ROADMAP, "## Standing decisions") == [
        "- **Made:** a rule."
    ]
    fenced = "## Parking lot\n\n- Code:\n```\n- not a bullet\n```\n- Next.\n"
    assert dc.top_level_bullets(fenced, "## Parking lot") == [
        "- Code:\n```\n- not a bullet\n```",
        "- Next.",
    ]


def test_item_problems_report_a_cap_and_a_lost_section() -> None:
    """Flag an item over its cap, a section with no item and a section lost."""
    rules: dict[str, dict[str, object]] = {
        "## Parking lot": {"item": "top-level bullet", "max_words": 3}
    }
    problems = dc.item_problems(ROADMAP, rules)
    assert len(problems) == 1 and "over its 3" in problems[0]
    # the longer bullet holds 8 words: at its cap it passes
    rules["## Parking lot"]["max_words"] = 8
    assert dc.item_problems(ROADMAP, rules) == []
    assert dc.item_problems(
        ROADMAP, {"## Parking lot": {"item": "table row", "max_words": 30}}
    ) == ["no table row in the `## Parking lot` section"]
    gone = ["no section headed `## Gone`: is its heading renamed?"]
    rule: dict[str, dict[str, object]] = {
        "## Gone": {"item": "top-level bullet", "max_words": 3}
    }
    assert dc.item_problems(ROADMAP, rule) == gone
    assert dc.item_problems("```\n## Gone\n- a bullet\n```\n", rule) == gone


def test_file_budget_problems_by_entry_shape() -> None:
    """Hold an inactive file to its baseline, an active one to its total or items."""
    assert dc.file_budget_problems("a b c", {"active": False, "baseline_words": 2}) == [
        "3 words, over its baseline of 2"
    ]
    assert (
        dc.file_budget_problems("a b c", {"active": False, "baseline_words": 3}) == []
    )
    assert dc.file_budget_problems("a b c", {"active": True, "target_words": 3}) == []
    assert dc.file_budget_problems("a b c", {"active": True, "target_words": 2}) == [
        "3 words, over its total of 2"
    ]
    entry: dict[str, object] = {
        "active": True,
        "rest_words": 5,
        "item_sections": {
            "## Load-bearing facts": {"item": "top-level bullet", "max_words": 10}
        },
    }
    problems = dc.file_budget_problems(CLAUDE, entry)
    assert len(problems) == 1 and "the rest, outside the items" in problems[0]
    # CLAUDE holds 41 words, 8 of them in its two bullets: the rest is 33
    entry["rest_words"] = 33
    assert dc.file_budget_problems(CLAUDE, entry) == []
    entry["rest_words"] = 32
    assert dc.file_budget_problems(CLAUDE, entry) == [
        "the rest, outside the items, of 33 words, over its total of 32"
    ]


def test_roadmap_status_problems_pass_and_fail() -> None:
    """Pass a well-formed roadmap and flag each mutation of its status rules."""
    assert dc.roadmap_status_problems(ROADMAP, 40, SECTIONS) == []
    unbolded = ROADMAP.replace("**Status: in waves.**", "Status: in waves.")
    problems = dc.roadmap_status_problems(unbolded, 40, SECTIONS)
    assert any("not exactly one" in p for p in problems) and any(
        "unbolded" in p for p in problems
    )
    none = ROADMAP.replace("**Status:", "Status:")
    assert "no status paragraph: is every `**Status:` marker unbolded?" in (
        dc.roadmap_status_problems(none, 40, SECTIONS)
    )
    doubled = ROADMAP.replace("Goal text.", "**Status: twice.** Again.\n")
    assert any(
        "2 status paragraphs" in p
        for p in dc.roadmap_status_problems(doubled, 40, SECTIONS)
    )
    long = ROADMAP.replace("Headline. [design](designs/a.md)", " ".join(["word"] * 50))
    assert any(
        "status paragraph of" in p
        for p in dc.roadmap_status_problems(long, 40, SECTIONS)
    )
    # the longest status paragraph holds 7 words: at the limit it passes
    assert dc.roadmap_status_problems(ROADMAP, 7, SECTIONS) == []
    at_six = dc.roadmap_status_problems(ROADMAP, 6, SECTIONS)
    assert len(at_six) == 1 and "a status paragraph of 7 words" in at_six[0]
    unclosed = ROADMAP.replace("Goal text.", "```\nGoal text.")
    assert any(
        "unclosed fence" in p
        for p in dc.roadmap_status_problems(unclosed, 40, SECTIONS)
    )
    assert dc.roadmap_status_problems(ROADMAP, 40, ("## Gone",)) == [
        "no entries: are the section headings renamed?"
    ]


def test_roadmap_status_problems_cross_check_the_two_walkers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Flag a line walk and a whole-section scan that disagree on the entries."""

    def no_headings(text: str, section: str) -> list[str]:
        """Find no heading, as a broken scan would."""
        return []

    monkeypatch.setattr(dc, "entry_headings", no_headings)
    assert "4 entries for 0 headings" in dc.roadmap_status_problems(
        ROADMAP, 40, SECTIONS
    )


def test_boot_path_problems_alarm_over_the_total() -> None:
    """Pass a boot path at its alarm and flag one a word over it."""
    assert dc.boot_path_problems(["a b", "c"], 3) == []
    assert dc.boot_path_problems(["a b", "c d"], 3) == [
        "the boot path's 4 words, over its alarm of 3"
    ]


def test_long_lines_exempt_tables_and_fences() -> None:
    """Count only prose lines over the line limit; a line at the limit passes."""
    text = (
        "x" * 50
        + "\n"
        + "w" * 40
        + "\n| "
        + "y" * 60
        + " |\n```\n"
        + "z" * 60
        + "\n```\n"
    )
    assert dc.long_lines(text, 40) == [1]


def test_relative_links_skip_code_and_external_targets() -> None:
    """List relative link targets outside code spans, fences and external URLs."""
    text = "[a](x.md) `[b](y.md)` [c](https://e) [d](#sec)\n```\n[e](z.md)\n```\n"
    assert dc.relative_links(text) == ["x.md"]


def test_status_site_problems_pass_the_fixtures_and_skip_other_lines() -> None:
    """Pass the fixtures, a directory name, and a SHA on a line that is no site."""
    assert dc.status_site_problems(ROADMAP, CLAUDE, [DESIGN]) == []
    not_a_sha = ROADMAP.replace("(PR #3).", "(PR #3, data/runs/batch-20300115).")
    assert dc.status_site_problems(not_a_sha, CLAUDE, [DESIGN]) == []
    assert (
        dc.status_site_problems(
            ROADMAP.replace("Goal text.", f"Goal text {A_SHA}."),
            CLAUDE.replace("one fact.", f"one fact {A_SHA}."),
            [DESIGN.replace("\nText.", f"\nText {A_SHA}.")],
        )
        == []
    )


SHA_AT_A_SITE = {
    "roadmap-status-paragraph": (
        ROADMAP.replace("(PR #3).", f"(PR #3, {A_SHA})."),
        CLAUDE,
        DESIGN,
    ),
    "roadmap-now-and-next": (
        ROADMAP.replace("Nothing running.", f"Nothing running since {A_SHA}."),
        CLAUDE,
        DESIGN,
    ),
    "claude-header-block": (
        ROADMAP,
        CLAUDE.replace("PR #12.", f"PR #12 at {A_SHA}."),
        DESIGN,
    ),
    "design-header": (
        ROADMAP,
        CLAUDE,
        DESIGN.replace("(PR #3).", f"(PR #3, {A_SHA})."),
    ),
}


@pytest.mark.parametrize("site", sorted(SHA_AT_A_SITE))
def test_status_site_problems_find_a_sha_at_each_site(site: str) -> None:
    """Flag a commit SHA at each status site, the only site that holds it."""
    roadmap, claude, design = SHA_AT_A_SITE[site]
    problems = dc.status_site_problems(roadmap, claude, [design])
    assert len(problems) == 1, problems
    assert problems[0].startswith("a commit SHA at a status site: ")
    assert A_SHA in problems[0]


SITE_TAKEN_OUT = {
    "roadmap-status-unbolded": (
        ROADMAP.replace("**Status:", "Status:"),
        CLAUDE,
        [DESIGN],
        "no roadmap status paragraph",
    ),
    "now-and-next-renamed": (
        ROADMAP.replace("## Now and next", "## Now"),
        CLAUDE,
        [DESIGN],
        "no `## Now and next` lines",
    ),
    "now-and-next-blank": (
        ROADMAP.replace("- **Now.** Nothing running.", ""),
        CLAUDE,
        [DESIGN],
        "no `## Now and next` lines",
    ),
    "claude-header-empty": (
        ROADMAP,
        "# Title\n## Doc map\n",
        [DESIGN],
        "CLAUDE.md's header block is empty",
    ),
    "claude-status-unbolded": (
        ROADMAP,
        CLAUDE.replace("**Status (", "Status ("),
        [DESIGN],
        "no line starting with `**Status`",
    ),
    "claude-next-unbolded": (
        ROADMAP,
        CLAUDE.replace("**Next:**", "Next:"),
        [DESIGN],
        "no line starting with `**Next:**`",
    ),
    "no-design-header": (ROADMAP, CLAUDE, [], "no design header is held to the rule"),
    "design-header-empty": (
        ROADMAP,
        CLAUDE,
        ["# A design\n## Goal\n"],
        "an empty design header: # A design",
    ),
    "design-status-renamed": (
        ROADMAP,
        CLAUDE,
        [DESIGN.replace("Status:", "State:")],
        "a design header without `Status:`",
    ),
}


@pytest.mark.parametrize("site", sorted(SITE_TAKEN_OUT))
def test_status_site_problems_flag_a_site_taken_out_of_the_check(site: str) -> None:
    """Flag each way a status site drops out of the check: renamed, unbolded, empty."""
    roadmap, claude, headers, problem = SITE_TAKEN_OUT[site]
    problems = dc.status_site_problems(roadmap, claude, headers)
    assert any(problem in p for p in problems), problems


@pytest.mark.parametrize(
    "sha", ["abc1234", "0123456789abcdef0123456789abcdef01234567"], ids=["7", "40"]
)
def test_the_sha_regex_matches_7_to_40_hex_characters(sha: str) -> None:
    """Match a hex token of 7 to 40 characters with a letter and a digit."""
    assert dc.SHA.findall(f"merged at {sha}.") == [sha]


@pytest.mark.parametrize(
    "text",
    [
        "data/abc1234",
        "v1.abc1234",
        "1,abc1234",
        "batch-abc1234",
        "xabc1234",
        "1234567",
        "defaced",
        "abc123",
        "abc1234g",
        "abc1234-x",
        "a" * 20 + "1" * 21,
    ],
    ids=[
        "after-a-slash",
        "after-a-dot",
        "after-a-comma",
        "after-a-hyphen",
        "after-a-letter",
        "no-letter",
        "no-digit",
        "six-characters",
        "running-into-a-letter",
        "running-into-a-hyphen",
        "41-characters",
    ],
)
def test_the_sha_regex_needs_each_of_its_clauses(text: str) -> None:
    """Find no SHA where one clause of the pattern alone fails."""
    assert dc.SHA.search(f"see {text} here") is None


@pytest.mark.parametrize(
    "ident",
    [
        "R-2a-14",
        "R-3b-7",
        "R-Q2-18",
        "R-A5-2",
        "R-ext-3",
        "R-K14",
        "R-Q11",
        "R-AB-4",
        "AB-15",
        "AB2-6",
        "D-12",
        "Q-16",
        "A-6",
        "O-4",
        "F-2",
        "H-3",
        "Q3-m2",
        "A4-m3",
        "R-plan-F2",
        "D14",
        "F7",
        "Q02",
        "AB12",
        "DQ4",
        "AF8",
        "RX2",
        "A2",
        "O2",
        "Q4",
    ],
)
def test_the_id_regex_matches_each_series_whole(ident: str) -> None:
    """Match every listed id whole, bounded as an id is."""
    assert dc.SERIES.findall(f"see {ident} here") == [ident]


FOREIGN_TOKENS = [
    ("A-45", ["A-45"]),
    ("A-4-5", ["A-4-5"]),
    ("R-3b-70", ["R-3b-70"]),
    ("L412", []),
    ("2030-04-01", []),
    ("Python3", []),
    ("x-F7", []),
    ("F7-x", []),
]


@pytest.mark.parametrize(
    ("text", "found"), FOREIGN_TOKENS, ids=[text for text, _ in FOREIGN_TOKENS]
)
def test_the_id_regex_rejects_longer_and_foreign_tokens(
    text: str, found: list[str]
) -> None:
    """Find no shorter id inside a longer token, a line citation, a date or a word."""
    assert dc.SERIES.findall(f"see {text} here") == found


def test_obligations_only_in_companion_logs(tmp_path: Path) -> None:
    """Report an id or a date that Active obligations cite and only the log holds."""
    designs = tmp_path / "docs" / "designs"
    designs.mkdir(parents=True)
    (designs / "x-design.md").write_text(
        "# X\n\n*Status: done.*\n\n## Goal\n\nQ3 and A-45 hold as of 2030-05-01.\n\n"
        "## Active obligations\n\n- F5 open; Q3 open; D9 open; A-4 open.\n"
        "- The rows of 2030-05-20 and 2030-05-01 stay open.\n\n"
        "## Decision log\n\n| Date | Ruling | Rationale |\n|---|---|---|\n",
        encoding="utf-8",
    )
    (designs / "x-design-log.md").write_text(
        "| 2030-05-20 | **F5** moved; Q3, A-4 and 2030-05-01 too |\n", encoding="utf-8"
    )
    (designs / "y-design.md").write_text(
        "# Y\n\n## 3. Active obligations\n\n- O3 open.\n", encoding="utf-8"
    )
    (designs / "y-design-log.md").write_text(
        "| 2030-05-21 | **O3** |\n", encoding="utf-8"
    )
    assert dc.obligations_only_in_companion_logs(tmp_path) == [
        ("x-design.md", "F5"),
        ("x-design.md", "A-4"),
        ("x-design.md", "2030-05-20"),
        ("y-design.md", "O3"),
    ]


def test_dead_links_and_dated_records(tmp_path: Path) -> None:
    """Resolve links relative to each file, anchors cut; keep dated records apart."""
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    (tmp_path / "docs" / "handoffs").mkdir()
    for name in ("CLAUDE.md", "AGENTS.md", "README.md"):
        (tmp_path / name).write_text(
            "[ok](docs/plans/README.md) [part](docs/plans/README.md#part) "
            "[bad](nope.md)\n",
            encoding="utf-8",
        )
    (tmp_path / "docs" / "plans" / "README.md").write_text("index\n", encoding="utf-8")
    (tmp_path / "docs" / "handoffs" / "README.md").write_text(
        "index\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "plans" / "2030-01-01-x.md").write_text(
        "[dead](gone.md)\n", encoding="utf-8"
    )
    assert dc.is_dated_record(tmp_path / "docs" / "plans" / "2030-01-01-x.md", tmp_path)
    assert not dc.is_dated_record(tmp_path / "docs" / "plans" / "README.md", tmp_path)
    assert dc.dead_links(tmp_path, records=False) == [
        ("AGENTS.md", "nope.md"),
        ("CLAUDE.md", "nope.md"),
        ("README.md", "nope.md"),
    ]
    assert dc.dead_links(tmp_path, records=True) == [
        ("docs/plans/2030-01-01-x.md", "gone.md")
    ]


def test_dead_links_read_the_seat_charters(tmp_path: Path) -> None:
    """Resolve the links of `.claude/agents/*.md` relative to each charter."""
    agents = tmp_path / ".claude" / "agents"
    agents.mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "process-log.md").write_text("log\n", encoding="utf-8")
    (agents / "counsel.md").write_text(
        "[ok](../../docs/process-log.md) [bad](../../docs/gone.md)\n", encoding="utf-8"
    )
    assert dc.dead_links(tmp_path, records=False) == [
        (".claude/agents/counsel.md", "../../docs/gone.md")
    ]
    assert dc.dead_links(tmp_path, records=True) == []


# --- the two commands over a temporary repository -------------------------------------

BUDGETS = "docs/doc-budgets.json"
BOOT_FILES = {
    "CLAUDE.md": (
        "# A project\n\nGoal.\n\n**Status (2030-06-01):** adopted.\n"
        "**Next:** the first session.\n\n## Doc map\n\n| Doc | Read when |\n|---|---|\n"
        "| [docs/roadmap.md](docs/roadmap.md) | Start here |\n\n"
        "## Load-bearing facts\n\n- **Alpha** one fact.\n"
    ),
    "docs/roadmap.md": (
        "# Roadmap\n\n## Now and next\n\n**Now.** Nothing running.\n\n## Items\n\n"
        "### 1. First item\n\nGoal.\n\n**Status: not started.**\n\n"
        "## Parking lot\n\n- An idea.\n\n## Standing decisions\n\n- A decision.\n"
    ),
    "docs/process.md": "# Process\n\nThe contract.\n",
    "AGENTS.md": "# Guidelines\n\nThe mechanics.\n",
    "README.md": "# A project\n\nThe setup.\n",
}
ONE_DESIGN = "docs/designs/one-design.md"
DESIGN_TEXT = "# One design\n\n*Status: proposed.*\n\n## Goal\n\nText.\n"
NO_DESIGN_LINE = (
    "With no design yet (no docs/designs/*-design.md, no design_headers row), "
    "no design header need be held."
)


def make_root(tmp_path: Path, files: dict[str, str] | None = None) -> Path:
    """Write the five budgeted files, and ``files`` beside or over them, under a root."""
    root = tmp_path / "repo"
    for name, text in {**BOOT_FILES, **(files or {})}.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def run(capsys: pytest.CaptureFixture[str], *argv: object) -> tuple[int, str, str]:
    """Run the command line; return its exit status, its stdout and its stderr."""
    capsys.readouterr()
    status = dc.main([str(arg) for arg in argv])
    out, err = capsys.readouterr()
    return status, out, err


def budgets_of(root: Path) -> dict:
    """Read the budgets file under ``root``."""
    return json.loads((root / BUDGETS).read_text(encoding="utf-8"))


def save(root: Path, budgets: dict) -> None:
    """Write ``budgets`` as the budgets file under ``root``."""
    (root / BUDGETS).write_text(json.dumps(budgets, indent=2) + "\n", encoding="utf-8")


def words(root: Path, name: str) -> int:
    """Count a file's words as whitespace-split tokens, apart from the tool."""
    return len((root / name).read_text(encoding="utf-8").split())


def test_init_writes_the_defaults_and_refuses_to_overwrite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Write the defaults with each baseline measured; refuse a second run unforced."""
    root = make_root(tmp_path)
    assert run(capsys, "init", "--root", root)[0] == 0
    since = {"target_from": "adoption", "active": True}
    assert budgets_of(root) == {
        "line_limit_chars": 400,
        "boot_path_total_words": 20000,
        "claude_h1_block_words": 350,
        "roadmap_status_paragraph_words": 40,
        "design_header_words": 250,
        "inactive_header_allowance_words": 100,
        "memory_index_chars": 2500,
        "files": {
            "CLAUDE.md": {
                "baseline_words": words(root, "CLAUDE.md"),
                "rest_words": 900,
                "item_sections": {
                    "## Doc map": {"item": "table row", "max_words": 30},
                    "## Load-bearing facts": {
                        "item": "top-level bullet",
                        "max_words": 200,
                    },
                },
                **since,
            },
            "docs/roadmap.md": {
                "baseline_words": words(root, "docs/roadmap.md"),
                "rest_words": 1200,
                "item_sections": {
                    "## Items": {"item": "entry", "max_words": 200},
                    "## Parking lot": {"item": "top-level bullet", "max_words": 200},
                    "## Standing decisions": {
                        "item": "top-level bullet",
                        "max_words": 200,
                    },
                },
                **since,
            },
            "docs/process.md": {
                "baseline_words": words(root, "docs/process.md"),
                "target_words": 10500,
                **since,
            },
            "AGENTS.md": {
                "baseline_words": words(root, "AGENTS.md"),
                "target_words": 2000,
                **since,
            },
            "README.md": {
                "baseline_words": words(root, "README.md"),
                "target_words": 700,
                **since,
            },
        },
        "design_headers": {},
        "record_dead_links": [],
    }
    written = (root / BUDGETS).read_bytes()
    status, _, err = run(capsys, "init", "--root", root)
    assert status == 2 and "--force" in err
    assert (root / BUDGETS).read_bytes() == written
    (root / "README.md").write_text(
        "# A project\n\nThe setup, now longer.\n", encoding="utf-8"
    )
    assert run(capsys, "init", "--root", root, "--force")[0] == 0
    assert budgets_of(root)["files"]["README.md"]["baseline_words"] == 7


def test_init_then_check_passes_on_a_fixture_root(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Pass ``check`` on what ``init`` writes for the five files and one design."""
    root = make_root(tmp_path, {ONE_DESIGN: DESIGN_TEXT})
    status, out, _ = run(capsys, "init", "--root", root)
    assert (status, out) == (0, "")
    written = budgets_of(root)
    for name in ("CLAUDE.md", "docs/roadmap.md"):
        assert "rest_words" in written["files"][name], name
    assert written["design_headers"] == {
        ONE_DESIGN: {"baseline_words": 2, "target_from": "adoption", "active": True}
    }
    assert run(capsys, "check", "--root", root)[:2] == (0, "")


def test_check_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exit 0 within budget, 1 with a file over it, 2 with no budgets file."""
    root = make_root(tmp_path)
    assert run(capsys, "init", "--root", root)[0] == 0
    assert run(capsys, "check", "--root", root)[:2] == (0, "")
    (root / "README.md").write_text("\n".join(["word"] * 701) + "\n", encoding="utf-8")
    assert run(capsys, "check", "--root", root)[:2] == (
        1,
        "README.md: 701 words, over its total of 700\n",
    )
    (root / BUDGETS).unlink()
    status, out, err = run(capsys, "check", "--root", root)
    assert (status, out) == (2, "") and BUDGETS in err


BOOT_WORDS = sum(
    len(BOOT_FILES[name].split())
    for name in ("CLAUDE.md", "docs/roadmap.md", "docs/process.md", "AGENTS.md")
)


def write(root: Path, name: str, text: str) -> None:
    """Write ``text`` as the file ``name`` under ``root``."""
    (root / name).write_text(text, encoding="utf-8")


def change_budgets(root: Path, change: Callable[[dict], object]) -> None:
    """Apply ``change`` to the budgets file under ``root``."""
    budgets = budgets_of(root)
    change(budgets)
    save(root, budgets)


def cite_an_obligation_only_the_log_holds(root: Path) -> None:
    """Give the design an Active obligations section whose id only its log holds."""
    write(root, ONE_DESIGN, DESIGN_TEXT + "\n## Active obligations\n\n- F5 open.\n")
    write(root, "docs/designs/one-design-log.md", "| 2030-05-20 | **F5** moved |\n")


# Each rule of ``check`` broken alone in a repository that passed it, and the line that
# ``check`` must print for it.
RULES: dict[str, tuple[Callable[[Path], object], str]] = {
    "a-budgeted-file-missing": (
        lambda root: (root / "AGENTS.md").unlink(),
        "AGENTS.md: no such file",
    ),
    "an-item-over-its-cap": (
        lambda root: change_budgets(
            root,
            lambda b: b["files"]["CLAUDE.md"]["item_sections"][
                "## Load-bearing facts"
            ].update(max_words=2),
        ),
        "CLAUDE.md: a top-level bullet of 4 words in `## Load-bearing facts`, over "
        "its 2: - **Alpha** one fact.",
    ),
    "a-prose-line-over-the-limit": (
        lambda root: write(root, "AGENTS.md", "# Guidelines\n\n" + "x" * 401 + "\n"),
        "AGENTS.md: line 3 is longer than the line limit of 400 characters",
    ),
    "the-h1-block-over-its-budget": (
        lambda root: write(
            root,
            "CLAUDE.md",
            BOOT_FILES["CLAUDE.md"].replace("Goal.\n", "Goal.\n" + "word\n" * 350),
        ),
        "CLAUDE.md: an H1 block of 358 words, over its 350",
    ),
    "a-status-paragraph-over-its-budget": (
        lambda root: change_budgets(
            root, lambda b: b.update(roadmap_status_paragraph_words=2)
        ),
        "docs/roadmap.md: a status paragraph of 3 words: **Status: not started.**",
    ),
    "the-boot-path-over-its-alarm": (
        lambda root: change_budgets(root, lambda b: b.update(boot_path_total_words=10)),
        f"{BUDGETS}: the boot path's {BOOT_WORDS} words, over its alarm of 10",
    ),
    "an-active-header-over-its-budget": (
        lambda root: write(
            root, ONE_DESIGN, DESIGN_TEXT.replace("proposed.*", "proposed.*" + " w" * 249)
        ),
        f"{ONE_DESIGN}: a header of 251 words, over its 250",
    ),
    "an-active-header-line-over-the-limit": (
        lambda root: write(
            root, ONE_DESIGN, DESIGN_TEXT.replace("proposed.*", "proposed.* " + "y" * 400)
        ),
        f"{ONE_DESIGN}: line 3 is longer than the line limit of 400 characters",
    ),
    "an-inactive-header-over-its-allowance": (
        lambda root: change_budgets(
            root,
            lambda b: (
                b.update(inactive_header_allowance_words=0),
                b["design_headers"][ONE_DESIGN].update(active=False, baseline_words=1),
            ),
        ),
        f"{ONE_DESIGN}: a header of 2 words, over its baseline of 1 and the allowance "
        "of 0",
    ),
    "an-obligation-only-in-the-log": (
        cite_an_obligation_only_the_log_holds,
        f"{ONE_DESIGN}: `F5`, cited by its Active obligations, is found only in its "
        "companion log",
    ),
}


@pytest.mark.parametrize("rule", sorted(RULES))
def test_check_runs_each_rule(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], rule: str
) -> None:
    """Fail each rule alone, through ``check``, at the file it is about."""
    root = make_root(tmp_path, {ONE_DESIGN: DESIGN_TEXT})
    assert run(capsys, "init", "--root", root)[:2] == (0, "")
    breaks, line = RULES[rule]
    breaks(root)
    status, out, _ = run(capsys, "check", "--root", root)
    assert status == 1
    assert line in out.splitlines(), out


# Each way of breaking the budgets file that ``check`` refuses, applied to what ``init``
# wrote: a text that is no JSON, or the JSON changed.
MALFORMED = {
    "not-json": lambda b: "{",
    "a-number-missing": lambda b: {
        k: v for k, v in b.items() if k != "memory_index_chars"
    },
    "a-number-not-whole": lambda b: {**b, "line_limit_chars": "400"},
    "an-allowance-below-zero": lambda b: {**b, "inactive_header_allowance_words": -1},
    "no-rest-beside-item-sections": lambda b: {
        **b,
        "files": {
            **b["files"],
            "CLAUDE.md": {
                k: v for k, v in b["files"]["CLAUDE.md"].items() if k != "rest_words"
            },
        },
    },
    "target-and-item-sections": lambda b: {
        **b,
        "files": {
            **b["files"],
            "CLAUDE.md": {**b["files"]["CLAUDE.md"], "target_words": 900},
        },
    },
    "an-unknown-item-kind": lambda b: {
        **b,
        "files": {
            **b["files"],
            "CLAUDE.md": {
                **b["files"]["CLAUDE.md"],
                "item_sections": {"## Doc map": {"item": "row", "max_words": 30}},
            },
        },
    },
    "a-section-inside-another": lambda b: {
        **b,
        "files": {
            **b["files"],
            "docs/roadmap.md": {
                **b["files"]["docs/roadmap.md"],
                "item_sections": {
                    "## Items": {"item": "entry", "max_words": 200},
                    "## Items and more": {"item": "entry", "max_words": 200},
                },
            },
        },
    },
    "a-design-row-without-its-flag": lambda b: {
        **b,
        "design_headers": {
            ONE_DESIGN: {"baseline_words": 2, "target_from": "adoption"}
        },
    },
    "the-pin-not-pairs": lambda b: {**b, "record_dead_links": [["a.md"]]},
    "the-roadmap-with-a-total-only": lambda b: {
        **b,
        "files": {
            **b["files"],
            "docs/roadmap.md": {
                "baseline_words": 5,
                "target_words": 1200,
                "target_from": "adoption",
                "active": True,
            },
        },
    },
    "no-roadmap-entry": lambda b: {
        **b,
        "files": {k: v for k, v in b["files"].items() if k != "docs/roadmap.md"},
    },
}


@pytest.mark.parametrize("fault", sorted(MALFORMED))
def test_check_refuses_a_malformed_budgets_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], fault: str
) -> None:
    """Exit 2, reading nothing else, on a budgets file of the wrong shape."""
    root = make_root(tmp_path, {ONE_DESIGN: DESIGN_TEXT})
    assert run(capsys, "init", "--root", root)[0] == 0
    broken = MALFORMED[fault](budgets_of(root))
    if isinstance(broken, str):
        (root / BUDGETS).write_text(broken, encoding="utf-8")
    else:
        save(root, broken)
    status, out, err = run(capsys, "check", "--root", root)
    assert (status, out) == (2, "") and BUDGETS in err, err


def test_init_refuses_without_a_budgeted_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exit 2 and write nothing when a file ``init`` would measure is missing."""
    root = make_root(tmp_path)
    (root / "AGENTS.md").unlink()
    status, out, err = run(capsys, "init", "--root", root)
    assert (status, out) == (2, ""), out
    assert err.startswith("doc_budgets: no AGENTS.md under ") and "as it stands" in err, err
    assert not (root / BUDGETS).exists()


def test_a_file_that_cannot_be_read_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exit 2, printing no problem, when a file the commands read is not UTF-8."""
    root = make_root(tmp_path)
    assert run(capsys, "init", "--root", root)[0] == 0
    (root / "README.md").write_bytes(b"# A project\n\n\xff\xfe\n")
    for argv in (["check"], ["init", "--force"]):
        status, out, err = run(capsys, *argv, "--root", root)
        assert (status, out) == (2, ""), (argv, out)
        assert err.startswith("doc_budgets: "), (argv, err)


def test_the_budgets_path_is_read_from_the_root(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Write and read ``--budgets`` under the root, and print its problems there."""
    root = make_root(tmp_path)
    other = "config/budgets.json"
    assert run(capsys, "init", "--root", root, "--budgets", other)[:2] == (0, "")
    assert (root / other).is_file() and not (root / BUDGETS).exists()
    assert run(capsys, "check", "--root", root, "--budgets", other)[:2] == (0, "")
    assert run(capsys, "check", "--root", root)[0] == 2
    budgets = json.loads((root / other).read_text(encoding="utf-8"))
    budgets["boot_path_total_words"] = 10
    (root / other).write_text(json.dumps(budgets), encoding="utf-8")
    assert run(capsys, "check", "--root", root, "--budgets", other)[:2] == (
        1,
        f"{other}: the boot path's {BOOT_WORDS} words, over its alarm of 10\n",
    )


@pytest.mark.parametrize("designs", ["empty", "absent"])
def test_check_passes_before_the_first_design(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], designs: str
) -> None:
    """Hold no design header where there is no design yet: none on disk, no row."""
    root = make_root(tmp_path)
    if designs == "empty":
        (root / "docs" / "designs").mkdir()
    status, out, err = run(capsys, "init", "--root", root)
    assert (status, out) == (0, "")
    assert budgets_of(root)["design_headers"] == {}
    status, out, err = run(capsys, "check", "--root", root)
    assert (status, out) == (0, "")
    assert "design header" not in out + err
    # the note on stderr and the waiver read one condition
    assert "no design yet" in err


def test_designs_and_their_rows_are_held_one_for_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Fail a design with no row and a row with no design; hold a header once one exists."""
    root = make_root(tmp_path)
    assert run(capsys, "init", "--root", root)[0] == 0
    (root / ONE_DESIGN).parent.mkdir(parents=True)
    (root / ONE_DESIGN).write_text(DESIGN_TEXT, encoding="utf-8")
    status, out, err = run(capsys, "check", "--root", root)
    assert status == 1
    assert f"{ONE_DESIGN}: no row in {BUDGETS}'s design_headers" in out
    assert "no design yet" not in err
    budgets = budgets_of(root)
    row = {"baseline_words": 2, "target_from": "adoption", "active": True}
    budgets["design_headers"] = {ONE_DESIGN: row}
    save(root, budgets)
    assert run(capsys, "check", "--root", root)[:2] == (0, "")
    row["active"] = False
    save(root, budgets)
    status, out, _ = run(capsys, "check", "--root", root)
    assert status == 1
    assert f"{BUDGETS}: no design header is held to the rule\n" in out
    row["active"] = True
    budgets["design_headers"]["docs/designs/gone-design.md"] = dict(row)
    save(root, budgets)
    status, out, _ = run(capsys, "check", "--root", root)
    assert status == 1
    assert out.startswith("docs/designs/gone-design.md: a row in ")
    # rows with no design on disk are no repository before its first design
    (root / ONE_DESIGN).unlink()
    status, out, err = run(capsys, "check", "--root", root)
    assert status == 1
    assert f"{BUDGETS}: no design header is held to the rule\n" in out
    assert "no design yet" not in err


def test_check_holds_the_dated_records_to_their_pin(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Pin a record's dead links at ``init``; fail a new one, a resolved one, disorder."""
    record = "docs/plans/2030-01-01-x.md"
    root = make_root(tmp_path, {record: "[a](a-gone.md) [b](b-gone.md)\n"})
    assert run(capsys, "init", "--root", root)[0] == 0
    pin = [[record, "a-gone.md"], [record, "b-gone.md"]]
    assert budgets_of(root)["record_dead_links"] == pin
    assert run(capsys, "check", "--root", root)[:2] == (0, "")
    (root / record).write_text(
        "[a](a-gone.md) [b](b-gone.md) [c](c-gone.md)\n", encoding="utf-8"
    )
    assert run(capsys, "check", "--root", root)[:2] == (
        1,
        f"{record}: a dead link not on {BUDGETS}'s record_dead_links pin: c-gone.md\n",
    )
    (root / record).write_text("[a](a-gone.md) [b](b-gone.md)\n", encoding="utf-8")
    (root / "docs" / "plans" / "b-gone.md").write_text("found\n", encoding="utf-8")
    assert run(capsys, "check", "--root", root)[:2] == (
        1,
        f"{BUDGETS}: record_dead_links pins a link that no longer dies: "
        f"{record}: b-gone.md\n",
    )
    (root / "docs" / "plans" / "b-gone.md").unlink()
    budgets = budgets_of(root)
    budgets["record_dead_links"] = pin[::-1]
    save(root, budgets)
    status, out, _ = run(capsys, "check", "--root", root)
    assert (status, out) == (1, f"{BUDGETS}: record_dead_links is not sorted\n")


def test_check_prints_each_problem_at_the_file_it_is_about(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Print ``<path>: <message>``, a status-site problem at the file of its site."""
    same = "# Same title\n\n*Status: proposed.*\n\n## Goal\n"
    root = make_root(
        tmp_path,
        {
            ONE_DESIGN: DESIGN_TEXT,
            "docs/designs/a-design.md": same,
            "docs/designs/b-design.md": same.replace("*Status: proposed.*\n\n", ""),
        },
    )
    # two designs share a title, and only the second has an empty header
    assert run(capsys, "init", "--root", root)[:2] == (
        1,
        "docs/designs/b-design.md: an empty design header: # Same title\n",
    )
    claude = BOOT_FILES["CLAUDE.md"].replace("adopted.", f"adopted at {A_SHA}.")
    (root / "CLAUDE.md").write_text(claude, encoding="utf-8")
    sited = DESIGN_TEXT.replace("proposed.", f"proposed at {A_SHA}.")
    (root / ONE_DESIGN).write_text(sited, encoding="utf-8")
    (root / "README.md").write_text("# A project\n\n[gone](nowhere.md)\n", encoding="utf-8")
    status, out, _ = run(capsys, "check", "--root", root)
    assert status == 1
    assert sorted(out.splitlines()) == [
        f"CLAUDE.md: a commit SHA at a status site: **Status (2030-06-01):** adopted at "
        f"{A_SHA}.",
        "README.md: a relative link that resolves to nothing: nowhere.md",
        "docs/designs/b-design.md: an empty design header: # Same title",
        f"{ONE_DESIGN}: a commit SHA at a status site: *Status: proposed at {A_SHA}.*",
    ]


def test_help_states_the_no_design_exception(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Say in ``--help``, in one line, that a repository with no design holds no header."""
    with pytest.raises(SystemExit) as stopped:
        dc.main(["--help"])
    assert stopped.value.code == 0
    assert NO_DESIGN_LINE in capsys.readouterr().out.splitlines()
