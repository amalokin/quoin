"""The plan-blocks tool over a fixture plan, a worktree repo and an overlay copy."""

from __future__ import annotations

import hashlib
import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tools import plan_blocks as pb

OLD = "def a() -> int:\n    return 1\n"
NEW = "def a() -> int:\n    return 2\n"
PLAN = """# A plan

### Task 1.1: Change a

**File: `pkg/a.py`** (unified diff against `main`)

```diff
```

### Task 2: Add b

**File: `pkg/b.py`** (whole file)

```python
```

**File: `docs/x.md`** (whole file)

````markdown
````
"""


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


def repository_variable(name: str) -> bool:
    """Tell whether ``name`` is one of git's repository variables."""
    return name in GIT_REPOSITORY_VARIABLES or name.startswith(
        ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
    )


@pytest.fixture(autouse=True)
def without_repository_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drop git's repository variables, for the git the tool itself runs."""
    for name in [name for name in os.environ if repository_variable(name)]:
        monkeypatch.delenv(name)


def git(repo: Path, *args: str) -> str:
    """Run a git command in ``repo``, on that repository alone; return its output."""
    env = {k: v for k, v in os.environ.items() if not repository_variable(k)}
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return done.stdout


def make_world(base: Path) -> tuple[Path, Path, Path]:
    """Create a worktree repo on ``main``, a changed overlay copy and a plan.

    All three go under ``base``.
    """
    worktree = base / "worktree"
    (worktree / "pkg").mkdir(parents=True)
    (worktree / "docs").mkdir()
    (worktree / "pkg" / "a.py").write_text(OLD, encoding="utf-8")
    git(worktree, "init", "-q", "-b", "main")
    git(worktree, "add", ".")
    git(worktree, "commit", "-q", "-m", "base")
    overlay = base / "overlay"
    pb.copy_tree(worktree, overlay)
    (overlay / "pkg" / "a.py").write_text(NEW, encoding="utf-8")
    (overlay / "pkg" / "b.py").write_text(
        "from tools import doc_budgets\nfrom pkg import c\n", encoding="utf-8"
    )
    (overlay / "docs" / "x.md").write_text("# X\n\n```\ncode\n```\n", encoding="utf-8")
    plan = base / "plan.md"
    plan.write_text(PLAN, encoding="utf-8")
    return worktree, overlay, plan


@pytest.fixture
def world(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create a worktree repo on ``main``, a changed overlay copy and a plan."""
    return make_world(tmp_path)


def host_state(host: Path) -> dict[str, Any]:
    """Read what a git pointed at the repository ``host`` would change there.

    Its configuration, refs and worktrees, and the indexes of its two checkouts.
    """
    admin = host / ".git"
    return {
        "config": git(host, "config", "--list", "--local"),
        "refs": git(host, "for-each-ref"),
        "worktrees": git(host, "worktree", "list", "--porcelain"),
        "indexes": [
            hashlib.sha256(index.read_bytes()).hexdigest()
            for index in (admin / "index", admin / "worktrees" / "wt" / "index")
        ],
    }


def test_git_leaves_the_host_repository_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Build the world in a hook's environment; leave the hook's repository as it was.

    git hands a hook in a linked worktree GIT_DIR and GIT_INDEX_FILE, so a suite a
    hook runs inherits them; the host here is a scratch repository.
    """
    host = tmp_path / "host"
    host.mkdir()
    (host / "README.md").write_text("the host\n", encoding="utf-8")
    git(host, "init", "-q", "-b", "main")
    git(host, "add", "README.md")
    git(host, "commit", "-q", "-m", "the host")
    git(host, "worktree", "add", "-q", "-b", "feature", str(tmp_path / "wt"))
    before = host_state(host)
    admin = host / ".git" / "worktrees" / "wt"
    monkeypatch.setenv("GIT_DIR", str(admin))
    monkeypatch.setenv("GIT_INDEX_FILE", str(admin / "index"))
    worktree, _, _ = make_world(tmp_path / "world")
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_INDEX_FILE")
    assert host_state(host) == before
    assert git(worktree, "log", "--format=%s") == "base\n"
    # Configuration given in the environment stays out too.
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.bare")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    assert git(worktree, "config", "--get", "core.bare") == "false\n"


def test_parse_finds_tasks_kinds_and_longer_fences(
    world: tuple[Path, Path, Path],
) -> None:
    """Parse the three blocks with their dotted task ids, kinds and empty bodies."""
    _, _, plan = world
    blocks = pb.parse(plan)
    assert [(b.task, b.path, b.kind) for b in blocks] == [
        ("1.1", "pkg/a.py", "diff"),
        ("2", "pkg/b.py", "whole"),
        ("2", "docs/x.md", "whole"),
    ]


def test_regen_fills_the_blocks_and_verify_reproduces_the_overlay(
    world: tuple[Path, Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Refill the blocks from the overlay, then rebuild the overlay from them."""
    worktree, overlay, plan = world
    assert pb.main(["regen", str(plan), str(worktree), str(overlay)]) == 0
    text = plan.read_text(encoding="utf-8")
    assert (
        "--- a/pkg/a.py\n+++ b/pkg/a.py" in text
        and "-    return 1\n+    return 2" in text
    )
    assert (
        "from pkg import c" in text
        and "````markdown\n# X\n\n```\ncode\n```\n````" in text
    )
    assert not any(line != line.rstrip() for line in text.split("\n"))
    assert (
        pb.main(
            [
                "verify",
                str(plan),
                str(worktree),
                str(overlay),
                str(tmp_path / "scratch"),
            ]
        )
        == 0
    )
    assert "all identical to the overlay" in capsys.readouterr().out


def test_regen_refuses_a_body_that_holds_its_fence(
    world: tuple[Path, Path, Path],
) -> None:
    """Raise when a markdown body carries the same fence the block opens with."""
    worktree, overlay, plan = world
    plan.write_text(
        plan.read_text(encoding="utf-8").replace(
            "````markdown\n````", "```markdown\n```"
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="longer one"):
        pb.main(["regen", str(plan), str(worktree), str(overlay)])


def test_applies_and_check_against_main_and_the_overlay(
    world: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Apply the diff to main, then check the overlay's files against the blocks."""
    worktree, overlay, plan = world
    pb.main(["regen", str(plan), str(worktree), str(overlay)])
    monkeypatch.chdir(worktree)
    assert pb.main(["applies", str(plan), "main"]) == 0
    assert pb.main(["check", str(plan), "1.1", "main"]) == 1
    monkeypatch.chdir(overlay)
    git(overlay, "init", "-q", "-b", "main")
    (overlay / "pkg" / "a.py").write_text(OLD, encoding="utf-8")
    git(overlay, "add", "pkg/a.py")
    git(overlay, "commit", "-q", "-m", "base")
    (overlay / "pkg" / "a.py").write_text(NEW, encoding="utf-8")
    assert pb.main(["check", str(plan), "1.1", "main"]) == 0
    assert pb.main(["check", str(plan), "2", "main"]) == 0


def test_applies_prints_fails_for_a_diff_that_does_not_match_the_base(
    world: tuple[Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Print FAILS and return 1 for a diff whose removed line the base lacks."""
    worktree, _, plan = world
    stale = (
        "--- a/pkg/a.py\n+++ b/pkg/a.py\n@@ -1,2 +1,2 @@\n"
        " def a() -> int:\n-    return 7\n+    return 2\n"
    )
    plan.write_text(
        PLAN.replace("```diff\n```", "```diff\n" + stale + "```"), encoding="utf-8"
    )
    monkeypatch.chdir(worktree)
    assert pb.main(["applies", str(plan), "main"]) == 1
    assert "task 1.1: FAILS pkg/a.py" in capsys.readouterr().out


def test_check_and_extract_fail_for_a_task_with_no_blocks(
    world: tuple[Path, Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit 1 for task 9.9, which has no blocks, and write nothing."""
    worktree, _, plan = world
    monkeypatch.chdir(worktree)
    out = tmp_path / "out"
    assert pb.main(["check", str(plan), "9.9", "main"]) == 1
    assert pb.main(["extract", str(plan), "9.9", str(out)]) == 1
    text = capsys.readouterr().out
    assert text.count("no file blocks for task 9.9") == 2
    assert "ALL SAME" not in text
    assert not out.exists()


def whole_plan(path: Path, blocks: list[tuple[str, str, str]]) -> Path:
    """Write a plan of whole-file blocks given as (task, file path, body) triples."""
    text = ""
    for task, file_path, body in blocks:
        text += (
            f"### Task {task}: a task\n\n**File: `{file_path}`** (whole file)\n\n"
            f"```python\n{body}```\n\n"
        )
    path.write_text(text, encoding="utf-8")
    return path


def run_imports(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    blocks: list[tuple[str, str, str]],
) -> tuple[int, str]:
    """Run ``imports`` on a plan of the given blocks; return its status and output."""
    plan = whole_plan(tmp_path / "plan.md", blocks)
    status = pb.main(["imports", str(plan)])
    return status, capsys.readouterr().out


@pytest.fixture
def tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a tree whose tools package defines VALUE, and make it the cwd."""
    root = tmp_path / "tree"
    (root / "tools").mkdir(parents=True)
    (root / "tools" / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.chdir(root)
    return root


@pytest.mark.usefixtures("tree")
def test_imports_flags_a_name_its_package_does_not_provide(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report tools.mod: tools/__init__.py lacks it and no block provides it."""
    body = "from tools import mod\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.mod: NOT FOUND by then" in out


@pytest.mark.usefixtures("tree")
def test_imports_flags_a_module_no_tree_file_or_block_provides(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report tools.nothing_here, a module that neither the tree nor a block has."""
    body = "from tools.nothing_here import x\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 1
    assert "imports tools.nothing_here: NOT FOUND by then" in out


@pytest.mark.usefixtures("tree")
def test_imports_accepts_a_module_a_later_block_of_the_same_task_provides(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept tools.mod when a later block of the same task provides it."""
    blocks = [
        ("1", "tests/test_user.py", "from tools import mod\n"),
        ("1", "tools/mod.py", "X = 2\n"),
    ]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 0
    assert "NOT FOUND" not in out


@pytest.mark.usefixtures("tree")
def test_imports_does_not_count_a_block_of_a_later_task(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report tools.mod when only a later task's block provides tools/mod.py."""
    blocks = [
        ("1", "tests/test_user.py", "from tools import mod\n"),
        ("2", "tools/mod.py", "X = 2\n"),
    ]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.mod: NOT FOUND by then" in out


def test_imports_accepts_a_module_already_in_the_tree(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept tools.mod when the tree holds tools/mod.py."""
    (tree / "tools" / "mod.py").write_text("X = 2\n", encoding="utf-8")
    body = "from tools import mod\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 0
    assert "NOT FOUND" not in out


@pytest.mark.usefixtures("tree")
def test_imports_accepts_a_name_the_package_init_defines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept VALUE, which tools/__init__.py defines, aliased and with a comment."""
    body = "from tools import VALUE as v  # the constant\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 0
    assert "NOT FOUND" not in out


def test_imports_does_not_check_the_names_of_a_module_file(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept any name from tools.mod, a module file whose names are attributes."""
    (tree / "tools" / "mod.py").write_text("X = 2\n", encoding="utf-8")
    body = "from tools.mod import anything\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 0
    assert "NOT FOUND" not in out


@pytest.mark.usefixtures("tree")
def test_imports_leaves_a_package_outside_the_repository_unchecked(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept an import from pkg, which is not one of the repository packages."""
    body = "from pkg import c\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 0
    assert "NOT FOUND" not in out


@pytest.mark.usefixtures("tree")
def test_imports_checks_only_the_module_of_a_multi_line_import(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept a multi-line import of tools: its module is checked, not its names."""
    body = "from tools import (\n    mod,\n)\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 0
    assert "NOT FOUND" not in out


def grow(root: Path, files: dict[str, str]) -> None:
    """Write each of ``files`` (a relative path and its text) under ``root``."""
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


@pytest.fixture
def empty_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an empty tree and make it the cwd."""
    root = tmp_path / "tree"
    root.mkdir()
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def bare_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a tree whose tools/ has other.py but no __init__.py; make it the cwd."""
    root = tmp_path / "tree"
    grow(root, {"tools/other.py": "VALUE = 1\n"})
    monkeypatch.chdir(root)
    return root


def test_imports_checks_a_package_the_tree_provides(
    empty_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report app.missing and app.gone from app, a package the tree holds.

    app is neither tools nor tests: the tree holding it makes it the repository's.
    """
    grow(empty_tree, {"app/__init__.py": "VALUE = 1\n"})
    body = "from app import VALUE\nfrom app import missing\nfrom app.gone import x\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 1
    assert "task 1: tests/test_user.py imports app.missing: NOT FOUND by then" in out
    assert "task 1: tests/test_user.py imports app.gone: NOT FOUND by then" in out
    assert out.count("NOT FOUND") == 2


def test_imports_checks_a_module_file_the_tree_provides(
    empty_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report helpers.sub but not helpers: the tree holds helpers.py, a module."""
    grow(empty_tree, {"helpers.py": "X = 1\n"})
    body = "import helpers\nimport helpers.sub\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 1
    assert "task 1: tests/test_user.py imports helpers.sub: NOT FOUND by then" in out
    assert out.count("NOT FOUND") == 1


@pytest.mark.usefixtures("empty_tree")
def test_imports_checks_a_package_only_a_later_task_provides(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report shop in an earlier task than the one that creates shop/.

    No directory of the tree is named shop: the plan's own block paths name it, and
    a task after the one that creates it accepts the import.
    """
    imports = "from shop import models\n"
    blocks = [("1", "tests/test_user.py", imports), ("2", "shop/models.py", "X = 2\n")]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 1
    assert "task 1: tests/test_user.py imports shop: NOT FOUND by then" in out
    blocks = [("1", "shop/models.py", "X = 2\n"), ("2", "tests/test_user.py", imports)]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 0
    assert "NOT FOUND" not in out


@pytest.mark.usefixtures("empty_tree")
def test_imports_checks_a_module_file_a_block_names(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report util.sub: a block at util.py makes util a module of the repository."""
    blocks = [
        ("1", "util.py", "X = 1\n"),
        ("1", "tests/test_user.py", "import util\nimport util.sub\n"),
    ]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 1
    assert "task 1: tests/test_user.py imports util.sub: NOT FOUND by then" in out
    assert out.count("NOT FOUND") == 1


@pytest.mark.parametrize("name", ["__pycache__", "3d"])
@pytest.mark.parametrize("source", ["the tree", "a block"])
def test_imports_never_counts_an_excluded_or_non_identifier_name(
    name: str,
    source: str,
    empty_tree: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Leave an import from NAME unchecked though the tree or a block holds NAME.

    A cache directory and a name that is no identifier are no package names.
    """
    blocks = [("1", "tests/test_user.py", f"from {name} import thing\n")]
    if source == "the tree":
        grow(empty_tree, {f"{name}/data.txt": "x\n"})
    else:
        blocks.append(("1", f"{name}/data.py", "X = 1\n"))
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 0
    assert "NOT FOUND" not in out


def test_imports_reads_the_tree_at_each_run(
    empty_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Leave app unchecked while the tree lacks it, and check it once it is there."""
    blocks = [("1", "tests/test_user.py", "from app import missing\n")]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 0
    assert "NOT FOUND" not in out
    grow(empty_tree, {"app/__init__.py": "VALUE = 1\n"})
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 1
    assert "task 1: tests/test_user.py imports app.missing: NOT FOUND by then" in out


def test_imports_accepts_a_subpackage_beside_the_package_init(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept tools.sub: tools/sub/__init__.py stands beside tools/__init__.py."""
    grow(tree, {"tools/sub/__init__.py": "Y = 3\n"})
    body = "from tools import sub\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 0
    assert "NOT FOUND" not in out


def test_a_package_with_an_init_provides_a_subdirectory_that_holds_a_file(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept tools.sub: tools/ has an __init__.py, sub/ holds leaf.py and has none.

    VALUE, a word of the __init__.py, is accepted too. tools.hollow, a directory that
    holds only a cache, and tools.gone, which is nothing at all, are reported.
    """
    grow(tree, {"tools/sub/leaf.py": "Y = 3\n"})
    grow(tree, {"tools/hollow/__pycache__/x.pyc": "x\n"})
    body = (
        "from tools import sub\nfrom tools import VALUE\n"
        "from tools import hollow\nfrom tools import gone\n"
    )
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.hollow: NOT FOUND by then" in out
    assert "task 1: tests/test_user.py imports tools.gone: NOT FOUND by then" in out
    assert out.count("NOT FOUND") == 2


@pytest.mark.usefixtures("tree")
def test_a_package_with_an_init_provides_a_subdirectory_a_block_fills(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report tools.fresh before the block that lands tools/fresh/leaf.py, not after."""
    imports = ("tests/test_user.py", "from tools import fresh\n")
    leaf = ("tools/fresh/leaf.py", "Y = 3\n")
    status, out = run_imports(tmp_path, capsys, [("1", *imports), ("2", *leaf)])
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.fresh: NOT FOUND by then" in out
    status, out = run_imports(tmp_path, capsys, [("1", *leaf), ("2", *imports)])
    assert status == 0
    assert "NOT FOUND" not in out


def test_a_namespace_package_provides_a_module_the_tree_holds(
    bare_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept tools.mod in each import form: tools/ holds mod.py and no __init__.py."""
    grow(bare_tree, {"tools/mod.py": "X = 2\n"})
    body = "from tools import mod\nimport tools.mod\nfrom tools.mod import anything\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 0
    assert "NOT FOUND" not in out


def test_a_namespace_package_provides_a_module_a_block_lands(
    bare_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept tools.mod when a later block of the same task lands tools/mod.py."""
    assert not (bare_tree / "tools" / "__init__.py").exists()
    blocks = [
        ("1", "tests/test_user.py", "from tools import mod\n"),
        ("1", "tools/mod.py", "X = 2\n"),
    ]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 0
    assert "NOT FOUND" not in out


def test_a_namespace_package_flags_a_name_nothing_provides(
    bare_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report tools.missing but not tools.other, which the directory holds."""
    assert not (bare_tree / "tools" / "__init__.py").exists()
    body = "from tools import other\nfrom tools import missing\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.missing: NOT FOUND by then" in out
    assert out.count("NOT FOUND") == 1


@pytest.mark.usefixtures("bare_tree")
def test_a_namespace_package_does_not_count_a_block_of_a_later_task(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report tools.mod when only a later task's block lands tools/mod.py."""
    blocks = [
        ("1", "tests/test_user.py", "from tools import mod\n"),
        ("2", "tools/mod.py", "X = 2\n"),
    ]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.mod: NOT FOUND by then" in out


@pytest.mark.usefixtures("bare_tree")
def test_a_namespace_package_has_no_init_text_to_search(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report tools.VALUE though other.py defines it: no __init__.py text is read."""
    body = "from tools import VALUE\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.VALUE: NOT FOUND by then" in out


def test_a_namespace_package_holds_a_subdirectory_with_files(
    bare_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept tools.sub in each form: tools/sub/ holds leaf.py and no __init__.py."""
    grow(bare_tree, {"tools/sub/leaf.py": "X = 3\n"})
    body = (
        "from tools import sub\nimport tools.sub\n"
        "from tools.sub import leaf\nimport tools.sub.leaf\n"
    )
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 0
    assert "NOT FOUND" not in out


@pytest.mark.usefixtures("bare_tree")
def test_a_file_a_block_lands_under_a_directory_provides_its_module(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept tools.sub when a block lands tools/sub/leaf.py, and report tools.su."""
    blocks = [
        ("1", "tests/test_user.py", "import tools.sub\nimport tools.su\n"),
        ("1", "tools/sub/leaf.py", "X = 3\n"),
    ]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.su: NOT FOUND by then" in out
    assert out.count("NOT FOUND") == 1


def test_a_module_file_beside_a_directory_keeps_its_names_unchecked(
    bare_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept any name from tools.mod, a module file that shadows the mod/ beside it."""
    grow(bare_tree, {"tools/mod.py": "X = 2\n", "tools/mod/leaf.py": "Y = 3\n"})
    body = "from tools.mod import anything\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 0
    assert "NOT FOUND" not in out


@pytest.mark.usefixtures("bare_tree")
def test_a_multi_line_import_of_a_namespace_package_checks_its_module_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Check a multi-line import's module alone: tools passes, tools.gone is flagged."""
    body = (
        "from tools import (\n    nothing,\n)\n"
        "from tools.gone import (\n    nothing,\n)\n"
    )
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.gone: NOT FOUND by then" in out
    assert out.count("NOT FOUND") == 1


@pytest.mark.usefixtures("empty_tree")
def test_an_import_through_a_plain_module_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report reviewprobe.leaf: reviewprobe.py, a module, shadows reviewprobe/.

    Python resolves each prefix of a dotted import within its directory, a package
    with an __init__.py first, then a module file, then a namespace directory, so
    reviewprobe is the module file, which is no package to hold leaf.
    """
    blocks = [
        ("1", "reviewprobe.py", "X = 1\n"),
        ("1", "reviewprobe/leaf.py", "Y = 2\n"),
        ("1", "tests/test_probe.py", "import reviewprobe.leaf\n"),
        ("1", "tests/test_from.py", "from reviewprobe.leaf import Y\n"),
    ]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 1
    flagged = "imports reviewprobe.leaf: NOT FOUND by then"
    assert f"task 1: tests/test_probe.py {flagged}" in out
    assert f"task 1: tests/test_from.py {flagged}" in out
    assert out.count("NOT FOUND") == 2


def test_each_prefix_resolves_by_python_s_precedence(
    empty_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept a leaf under a package whose __init__.py wins over the module file
    beside it, and under a namespace directory with no module file beside it; report
    a leaf under a directory a module file shadows, at any depth.
    """
    grow(
        empty_tree,
        {
            "app/__init__.py": "",
            "app.py": "X = 1\n",
            "app/leaf.py": "Y = 2\n",
            "space/leaf.py": "Y = 2\n",
            "space/inner.py": "X = 1\n",
            "space/inner/leaf.py": "Y = 2\n",
        },
    )
    body = "import app.leaf\nimport space.leaf\nimport space.inner.leaf\n"
    status, out = run_imports(tmp_path, capsys, [("1", "tests/test_user.py", body)])
    assert status == 1
    flagged = "imports space.inner.leaf: NOT FOUND by then"
    assert f"task 1: tests/test_user.py {flagged}" in out
    assert out.count("NOT FOUND") == 1


def test_a_directory_holding_only_a_cache_provides_no_module(
    bare_tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report tools.gone: a directory holding only a __pycache__ provides nothing."""
    grow(bare_tree, {"tools/gone/__pycache__/x.pyc": "x\n"})
    blocks = [("1", "tests/test_user.py", "import tools.gone\n")]
    status, out = run_imports(tmp_path, capsys, blocks)
    assert status == 1
    assert "task 1: tests/test_user.py imports tools.gone: NOT FOUND by then" in out


def test_extract_writes_a_task_s_blocks(
    world: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    """Write task 2's two whole files and task 1.1's diff under the output directory."""
    worktree, overlay, plan = world
    pb.main(["regen", str(plan), str(worktree), str(overlay)])
    out = tmp_path / "out"
    assert pb.main(["extract", str(plan), "2", str(out)]) == 0
    assert (
        (out / "pkg" / "b.py")
        .read_text(encoding="utf-8")
        .startswith("from tools import doc_budgets")
    )
    assert pb.main(["extract", str(plan), "1.1", str(out)]) == 0
    assert (
        (out / "pkg" / "a.py.diff")
        .read_text(encoding="utf-8")
        .startswith("--- a/pkg/a.py")
    )


def test_verify_fails_for_a_block_that_differs_from_the_overlay(
    world: tuple[Path, Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exit 1 and print DIFFER when the overlay moved on after the blocks' regen."""
    worktree, overlay, plan = world
    pb.main(["regen", str(plan), str(worktree), str(overlay)])
    (overlay / "pkg" / "b.py").write_text("changed after regen\n", encoding="utf-8")
    capsys.readouterr()
    scratch = tmp_path / "scratch"
    assert (
        pb.main(["verify", str(plan), str(worktree), str(overlay), str(scratch)]) == 1
    )
    out = capsys.readouterr().out
    assert "3 files compared; DIFFER: ['pkg/b.py']" in out
    assert "all identical" not in out


def snapshot(root: Path) -> dict[str, bytes]:
    """Return every file under ``root`` by its relative path, with its bytes."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


Layout = Callable[[Path], tuple[Path, Path, Path]]

OVERLAPS: dict[str, Layout] = {
    "the overlay is SCRATCH/tree": lambda t: (t / "wt", t / "s" / "tree", t / "s"),
    "SCRATCH/tree holds the worktree": lambda t: (
        t / "s" / "tree" / "wt",
        t / "ov",
        t / "s",
    ),
    "SCRATCH is the worktree": lambda t: (t / "wt", t / "ov", t / "wt"),
    "SCRATCH lies inside the overlay": lambda t: (t / "wt", t / "ov", t / "ov" / "s"),
    "an overlay spelled with .. that is SCRATCH/tree": lambda t: (
        t / "wt",
        t / "s" / "x" / ".." / "tree",
        t / "s",
    ),
}


@pytest.mark.parametrize("case", sorted(OVERLAPS))
def test_verify_refuses_a_scratch_that_overlaps_an_input(
    case: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exit 2 before any deletion; both inputs keep every byte."""
    worktree, overlay, scratch = OVERLAPS[case](tmp_path)
    (worktree / "pkg").mkdir(parents=True)
    (worktree / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (overlay / "pkg").mkdir(parents=True, exist_ok=True)
    (overlay / "pkg" / "a.py").write_text("x = 2\n", encoding="utf-8")
    (overlay / "OVERLAY_ONLY.txt").write_text("keep me\n", encoding="utf-8")
    plan = whole_plan(tmp_path / "plan.md", [("1", "pkg/a.py", "x = 3\n")])
    before = (snapshot(worktree), snapshot(overlay))
    status = pb.main(["verify", str(plan), str(worktree), str(overlay), str(scratch)])
    assert status == 2
    assert "refusing" in capsys.readouterr().out
    assert (snapshot(worktree), snapshot(overlay)) == before


def test_verify_resolves_a_relative_scratch_before_comparing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Refuse a relative SCRATCH that resolves inside the overlay (the cwd)."""
    worktree, overlay = tmp_path / "wt", tmp_path / "ov"
    (worktree / "pkg").mkdir(parents=True)
    (worktree / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (overlay / "pkg").mkdir(parents=True)
    (overlay / "pkg" / "a.py").write_text("x = 2\n", encoding="utf-8")
    plan = whole_plan(tmp_path / "plan.md", [("1", "pkg/a.py", "x = 3\n")])
    monkeypatch.chdir(overlay)
    before = snapshot(overlay)
    assert pb.main(["verify", str(plan), str(worktree), str(overlay), "s"]) == 2
    assert "refusing" in capsys.readouterr().out
    assert snapshot(overlay) == before


def case_insensitive(directory: Path) -> bool:
    """Tell whether the filesystem holding ``directory`` folds the case of names."""
    probe = directory / "case-probe"
    probe.mkdir()
    folded = (directory / "CASE-PROBE").exists()
    probe.rmdir()
    return folded


def test_verify_refuses_a_case_alias_of_scratch_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Refuse an OVERLAY spelled SCRATCH/TREE where the filesystem folds case."""
    if not case_insensitive(tmp_path):
        pytest.skip("a case-sensitive filesystem: SCRATCH/TREE is no alias of the tree")
    worktree, scratch = tmp_path / "wt", tmp_path / "s"
    (worktree / "pkg").mkdir(parents=True)
    (worktree / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
    real = scratch / "tree"
    (real / "pkg").mkdir(parents=True)
    (real / "pkg" / "a.py").write_text("x = 2\n", encoding="utf-8")
    (real / "OVERLAY_ONLY.txt").write_text("keep me\n", encoding="utf-8")
    plan = whole_plan(tmp_path / "plan.md", [("1", "pkg/a.py", "x = 3\n")])
    before = (snapshot(worktree), snapshot(real))
    alias = scratch / "TREE"
    status = pb.main(["verify", str(plan), str(worktree), str(alias), str(scratch)])
    assert status == 2
    assert "refusing" in capsys.readouterr().out
    assert (snapshot(worktree), snapshot(real)) == before


CASE_ALIASES: dict[str, Layout] = {
    "the worktree under SCRATCH/TREE": lambda t: (
        t / "s" / "TREE" / "wt",
        t / "ov",
        t / "s",
    ),
    "SCRATCH spelled SC, the overlay sc": lambda t: (t / "wt", t / "sc", t / "SC"),
    "SCRATCH not yet made, under OV, the overlay ov": lambda t: (
        t / "wt",
        t / "ov",
        t / "OV" / "new" / "deeper",
    ),
}


@pytest.mark.parametrize("case", sorted(CASE_ALIASES))
def test_verify_refuses_an_overlap_spelled_by_a_case_alias(
    case: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Refuse each overlap only identity sees; create, delete and write nothing."""
    if not case_insensitive(tmp_path):
        pytest.skip("a case-sensitive filesystem: the spellings name different paths")
    worktree, overlay, scratch = CASE_ALIASES[case](tmp_path)
    for root, text in ((worktree, "x = 1\n"), (overlay, "x = 2\n")):
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "a.py").write_text(text, encoding="utf-8")
    plan = whole_plan(tmp_path / "plan.md", [("1", "pkg/a.py", "x = 3\n")])
    before = (sorted(tmp_path.rglob("*")), snapshot(worktree), snapshot(overlay))
    status = pb.main(["verify", str(plan), str(worktree), str(overlay), str(scratch)])
    assert status == 2
    assert "refusing" in capsys.readouterr().out
    after = (sorted(tmp_path.rglob("*")), snapshot(worktree), snapshot(overlay))
    assert after == before


def test_verify_refuses_an_input_that_is_not_a_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exit 2 for an OVERLAY that does not exist, before SCRATCH is made."""
    worktree, scratch = tmp_path / "wt", tmp_path / "s"
    (worktree / "pkg").mkdir(parents=True)
    (worktree / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
    plan = whole_plan(tmp_path / "plan.md", [("1", "pkg/a.py", "x = 3\n")])
    args = ["verify", str(plan), str(worktree), str(tmp_path / "none"), str(scratch)]
    assert pb.main(args) == 2
    assert "not a directory" in capsys.readouterr().out
    assert not scratch.exists()


@pytest.mark.parametrize(
    "target", ["the overlay", "inside the overlay", "elsewhere", "itself"]
)
def test_verify_refuses_a_scratch_tree_that_is_a_link(
    target: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Refuse a SCRATCH/tree link with exit 2, whatever it names.

    An input, a directory inside one, a directory elsewhere, or itself (a loop).
    """
    worktree, overlay, scratch = tmp_path / "wt", tmp_path / "ov", tmp_path / "s"
    elsewhere = tmp_path / "elsewhere"
    for root, text in ((worktree, "x = 1\n"), (overlay, "x = 2\n"), (elsewhere, "y\n")):
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "a.py").write_text(text, encoding="utf-8")
    scratch.mkdir()
    pointee = {
        "the overlay": overlay,
        "inside the overlay": overlay / "pkg",
        "elsewhere": elsewhere,
        "itself": scratch / "tree",
    }[target]
    (scratch / "tree").symlink_to(pointee, target_is_directory=True)
    plan = whole_plan(tmp_path / "plan.md", [("1", "pkg/a.py", "x = 3\n")])
    before = (snapshot(worktree), snapshot(overlay), snapshot(elsewhere))
    status = pb.main(["verify", str(plan), str(worktree), str(overlay), str(scratch)])
    assert status == 2
    assert "refusing" in capsys.readouterr().out
    assert (snapshot(worktree), snapshot(overlay), snapshot(elsewhere)) == before
    assert (scratch / "tree").is_symlink()


def diff_plan(path: Path, diff: str) -> Path:
    """Write a one-task plan whose one block is ``diff``, a diff of ``pkg/a.py``."""
    path.write_text(
        "### Task 1: one\n\n**File: `pkg/a.py`** (unified diff against `main`)\n\n"
        f"```diff\n{diff}```\n",
        encoding="utf-8",
    )
    return path


def test_verify_fails_for_a_diff_block_that_does_not_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exit 1 and print FAILED for a diff that does not apply; no file differs."""
    worktree, overlay = tmp_path / "wt", tmp_path / "ov"
    for root in (worktree, overlay):
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "a.py").write_text(OLD, encoding="utf-8")
    stale = (
        "--- a/pkg/a.py\n+++ b/pkg/a.py\n@@ -1,2 +1,2 @@\n"
        " def a() -> int:\n-    return 7\n+    return 2\n"
    )
    plan = diff_plan(tmp_path / "plan.md", stale)
    scratch = tmp_path / "scratch"
    assert (
        pb.main(["verify", str(plan), str(worktree), str(overlay), str(scratch)]) == 1
    )
    out = capsys.readouterr().out
    assert "1 blocks applied; 1 failed" in out
    assert "FAILED: pkg/a.py:" in out
    assert "1 files compared; all identical to the overlay" in out


@pytest.mark.parametrize("kind", ["symbolic", "hard"])
def test_verify_replaces_a_link_planted_at_the_diff(
    kind: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Remove a link at SCRATCH/the.diff before writing; the file it names is kept."""
    worktree, overlay, scratch = tmp_path / "wt", tmp_path / "ov", tmp_path / "s"
    for root, text in ((worktree, OLD), (overlay, NEW)):
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "a.py").write_text(text, encoding="utf-8")
    scratch.mkdir()
    planted, named = scratch / "the.diff", overlay / "pkg" / "a.py"
    if kind == "symbolic":
        planted.symlink_to(named)
    else:
        os.link(named, planted)
    change = (
        "--- a/pkg/a.py\n+++ b/pkg/a.py\n@@ -1,2 +1,2 @@\n"
        " def a() -> int:\n-    return 1\n+    return 2\n"
    )
    plan = diff_plan(tmp_path / "plan.md", change)
    before = snapshot(overlay)
    status = pb.main(["verify", str(plan), str(worktree), str(overlay), str(scratch)])
    assert status == 0
    assert "1 files compared; all identical to the overlay" in capsys.readouterr().out
    assert snapshot(overlay) == before


@pytest.mark.parametrize("where", ["absolute", "../climbed.txt", "pkg/../../x.txt"])
def test_a_block_path_outside_the_tree_is_refused(
    where: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Refuse an absolute or ``..`` marker path in parse; every command exits 2."""
    victim = tmp_path / "victim.txt"
    victim.write_text("precious\n", encoding="utf-8")
    path = str(victim) if where == "absolute" else where
    plan = whole_plan(tmp_path / "plan.md", [("1", path, "overwritten\n")])
    with pytest.raises(pb.PlanError, match="outside the tree"):
        pb.parse(plan)
    out, tree = tmp_path / "out" / "deep", tmp_path / "wt"
    tree.mkdir()
    for args in (
        ["list"],
        ["extract", "1", str(out)],
        ["verify", str(tree), str(tree), str(tmp_path / "scratch")],
    ):
        assert pb.main([args[0], str(plan), *args[1:]]) == 2
    assert capsys.readouterr().out.count("outside the tree") == 3
    assert victim.read_text(encoding="utf-8") == "precious\n"
    assert not (tmp_path / "out").exists() and not (tmp_path / "scratch").exists()


def test_patch_runs_with_its_stdin_closed(
    world: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Give every ``patch`` call ``stdin=DEVNULL``, so a prompt cannot hang a check."""
    worktree, overlay, plan = world
    pb.main(["regen", str(plan), str(worktree), str(overlay)])
    seen: list[object] = []
    real = subprocess.run

    def spy(command: list[str], *args: Any, **kwargs: Any) -> Any:
        """Record the stdin of a patch call, then run the command."""
        if command[0] == "patch":
            seen.append(kwargs.get("stdin"))
        return real(command, *args, **kwargs)

    monkeypatch.setattr(pb.subprocess, "run", spy)
    monkeypatch.chdir(worktree)
    assert pb.main(["applies", str(plan), "main"]) == 0
    scratch = tmp_path / "scratch"
    assert (
        pb.main(["verify", str(plan), str(worktree), str(overlay), str(scratch)]) == 0
    )
    assert seen == [subprocess.DEVNULL, subprocess.DEVNULL]
