"""Parse, apply, check, regenerate and verify a plan's file blocks.

The practice is the plan-overlay extension of ``docs/process.md``. A plan carries its
code as file blocks: a marker line ``**File: `path`** (whole file)`` or
``**File: `path`** (unified diff against `main`)``, a blank line, then a fenced block
of three or more backticks (a markdown file that itself holds fences takes a longer
fence). Tasks are ``### Task N`` headings; ``N`` may be dotted (``Task 1.3``).

Usage, from the repository root::

    python3 -I tools/plan_blocks.py list PLAN
    python3 -I tools/plan_blocks.py imports PLAN
    python3 -I tools/plan_blocks.py applies PLAN BASE
    python3 -I tools/plan_blocks.py check PLAN TASK BASE
    python3 -I tools/plan_blocks.py extract PLAN TASK OUTDIR
    python3 -I tools/plan_blocks.py regen PLAN WORKTREE OVERLAY
    python3 -I tools/plan_blocks.py verify PLAN WORKTREE OVERLAY SCRATCH

``check`` compares the working tree with task TASK's blocks (a whole file as written, a
diff applied with ``patch -p1 -l`` to BASE's blob, so the whitespace hook's stripped
context lines still apply); ``applies`` tries every diff against BASE; ``imports`` lists
the repository imports that no tree file and no block of the same or an earlier task
provides, and checks the names of a package's ``from`` imports (``cmd_imports``). An
import's first name is the repository's when the working directory holds a directory or
a ``.py`` file of that name, or a block of the plan, of any task, has a path whose first
part is that name or that name plus ``.py``; an import of any other package is left
unchecked. One rule says what provides a module, whatever kind of package holds it: a
``.py`` file, or any file under its directory (an ``__init__.py`` is one), in the tree
or in a block landed by then; a directory without ``__init__.py`` is a namespace
package. Each prefix of a dotted import resolves as Python resolves it within a
directory, a package with an ``__init__.py`` first, then a module file, then a
namespace directory (PEP 420), and an import through a module file is not provided,
since a module is no package. A name n of ``from X import n`` is provided when the
module ``X.n`` is, or when ``X/__init__.py`` is provided and n is a whole word of its
text; the names of a module file are not checked. ``regen`` refills every
block from OVERLAY — a whole file copied, a diff computed by ``diff -u`` between the
WORKTREE and OVERLAY copies with ``a/``-``b/`` headers — and strips trailing
whitespace as the pre-commit hook would; ``verify`` extracts the blocks, applies
them to a fresh copy of WORKTREE under SCRATCH and compares every touched path with
OVERLAY byte for byte. Exit status 0 when every check passes, 1 otherwise; a task with
no blocks fails ``check`` and ``extract``. Exit status 2, with nothing written: a block
path outside the tree — absolute, or with a ``..`` part (``parse`` raises
``PlanError``) — for every command; and for ``verify``, resolving the three paths
first and before it deletes anything, a SCRATCH/tree that is or holds WORKTREE or
OVERLAY, or a SCRATCH that is or lies inside either, by spelling or by filesystem
identity (device and inode, so a case alias or a link counts), a SCRATCH/tree that is
a link, or an input that is not a directory. ``patch`` runs with its stdin closed, so
a prompt cannot hang a check, and ``verify`` removes a link planted at
SCRATCH/the.diff before each write instead of writing through it.
"""

from __future__ import annotations

import filecmp
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

TASK = re.compile(r"^#{1,4}\s+Task\s+(\d+(?:\.\d+)*)\b")
FILE = re.compile(r"^\*\*File: `([^`]+)`\*\*\s*\(([^)]*)\)(.*)$")
FENCE = re.compile(r"^(`{3,})(.*)$")
IMPORT = re.compile(r"^\+?\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))")
EXCLUDES = (
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".hypothesis",
)

Kind = Literal["whole", "diff"]


@dataclass(frozen=True)
class Block:
    """One file block of a plan: its task, path, kind, body and the body's line span."""

    task: str
    path: str
    kind: Kind
    content: str
    start: int
    end: int


class PlanError(ValueError):
    """Signal a plan the tool refuses: a block path outside the tree."""


def tree_path(path: str, number: int) -> str:
    """Return a marker's path; raise PlanError when it is absolute or has a ``..``."""
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts:
        raise PlanError(
            f"line {number}: the block path {path!r} is outside the tree "
            "(absolute, or with a '..' part)"
        )
    return path


def parse(plan: Path) -> list[Block]:
    """Return every file block of ``plan`` in order, with the body's line span.

    Raises:
        PlanError: a marker's path is absolute or has a ``..`` part.
    """
    lines = plan.read_text(encoding="utf-8").split("\n")
    blocks: list[Block] = []
    task = "-"
    fence: str | None = None
    pending: tuple[str, Kind] | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        match = FENCE.match(line)
        if fence is None and match:
            if pending is not None:
                ticks = match.group(1)
                start = i + 1
                i += 1
                while i < len(lines) and lines[i].rstrip() != ticks:
                    i += 1
                body = "\n".join(lines[start:i])
                blocks.append(
                    Block(task, pending[0], pending[1], body + "\n", start, i)
                )
                pending = None
                i += 1
                continue
            fence = match.group(1)
            i += 1
            continue
        if fence is not None:
            if line.rstrip() == fence:
                fence = None
            i += 1
            continue
        found = TASK.match(line)
        if found:
            task = found.group(1)
        marker = FILE.match(line)
        if marker:
            kind: Kind = "diff" if "diff" in marker.group(2) else "whole"
            pending = (tree_path(marker.group(1), i + 1), kind)
        i += 1
    return blocks


def git_show(base: str, path: str) -> bytes | None:
    """Return the file at ``base``, or None when it does not exist there."""
    done = subprocess.run(
        ["git", "show", f"{base}:{path}"], capture_output=True, check=False
    )
    return done.stdout if done.returncode == 0 else None


def apply_diff(original: bytes | None, diff: str, path: str) -> bytes:
    """Apply a unified diff to ``original`` with ``patch -p1 -l``; return the result."""
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if original is not None:
            target.write_bytes(original)
        diff_path = Path(temp) / "the.diff"
        diff_path.write_text(diff, encoding="utf-8")
        done = subprocess.run(
            ["patch", "-p1", "-l", "--no-backup-if-mismatch", "-i", str(diff_path)],
            cwd=temp,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        if done.returncode != 0:
            raise RuntimeError(
                f"patch failed for {path}:\n{done.stdout}\n{done.stderr}"
            )
        return target.read_bytes()


def cmd_list(blocks: list[Block]) -> int:
    """Print every block's task, kind, path and line count."""
    for block in blocks:
        print(
            f"task {block.task}: {block.kind:5} {block.path} "
            f"({block.content.count(chr(10))} lines)"
        )
    return 0


def cmd_extract(blocks: list[Block], task: str, out: Path) -> int:
    """Write task ``task``'s blocks under ``out`` (a diff gets a ``.diff`` suffix)."""
    if not any(block.task == task for block in blocks):
        print(f"no file blocks for task {task}")
        return 1
    for block in blocks:
        if block.task != task:
            continue
        dest = out / (block.path + (".diff" if block.kind == "diff" else ""))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(block.content, encoding="utf-8")
        print(dest)
    return 0


def cmd_check(blocks: list[Block], task: str, base: str) -> int:
    """Compare the tree with task ``task``'s blocks; print SAME or DIFF per file."""
    if not any(block.task == task for block in blocks):
        print(f"no file blocks for task {task}")
        return 1
    ok = True
    for block in blocks:
        if block.task != task:
            continue
        tree = Path(block.path).read_bytes() if Path(block.path).exists() else None
        if block.kind == "whole":
            want = block.content.encode("utf-8")
        else:
            want = apply_diff(git_show(base, block.path), block.content, block.path)
        same = tree == want
        ok &= same
        print(f"{'SAME' if same else 'DIFF'} {block.kind:5} {block.path}")
        if not same and tree is not None:
            with tempfile.NamedTemporaryFile("wb", delete=False) as handle:
                handle.write(want)
            done = subprocess.run(
                ["diff", "-u", handle.name, block.path],
                capture_output=True,
                text=True,
                check=False,
            )
            print("\n".join(done.stdout.splitlines()[:40]))
            os.unlink(handle.name)
    print("ALL SAME" if ok else "DIFFERENCES")
    return 0 if ok else 1


def cmd_applies(blocks: list[Block], base: str) -> int:
    """Try every diff block against ``base``; print applies or FAILS per file."""
    ok = True
    for block in blocks:
        if block.kind != "diff":
            continue
        try:
            apply_diff(git_show(base, block.path), block.content, block.path)
            print(f"task {block.task}: applies {block.path}")
        except RuntimeError as exc:
            ok = False
            print(f"task {block.task}: FAILS {block.path}: {exc}")
    return 0 if ok else 1


def added_text(block: Block) -> str:
    """Return a block's text as it lands: a whole file, or a diff's added lines."""
    if block.kind == "whole":
        return block.content
    return "\n".join(
        line[1:]
        for line in block.content.split("\n")
        if line.startswith("+") and not line.startswith("+++")
    )


def landed_by_task(blocks: list[Block]) -> dict[str, list[Block]]:
    """Map each task to the blocks that have landed by it: its own and earlier ones."""
    first: dict[str, int] = {}
    for block in blocks:
        first.setdefault(block.task, len(first))
    return {
        task: [block for block in blocks if first[block.task] <= rank]
        for task, rank in first.items()
    }


def provided(path: str, paths: set[str]) -> bool:
    """Return whether the working tree or the landed ``paths`` provide ``path``."""
    return path in paths or Path(path).exists()


def landed_text(path: str, lands: list[Block]) -> str:
    """Return a path's tree text followed by the text of its landed blocks."""
    parts = [Path(path).read_text(encoding="utf-8")] if Path(path).exists() else []
    parts.extend(added_text(block) for block in lands if block.path == path)
    return "\n".join(parts)


def imported_names(rest: str) -> list[str] | None:
    """Return the names a ``from`` import binds, or None for a multi-line import.

    The remainder after ``import`` loses a trailing comment and its parentheses, and
    each comma-separated part gives its first word (``a as b`` gives ``a``); a ``*``
    or an empty part gives nothing. A remainder that is only ``(`` gives None.
    """
    text = rest.split("#", 1)[0].strip()
    if text == "(":
        return None
    names: list[str] = []
    for part in text.replace("(", " ").replace(")", " ").split(","):
        words = part.split()
        if words and words[0] != "*":
            names.append(words[0])
    return names


def repository_packages(blocks: list[Block]) -> set[str]:
    """Return the first names of the imports that ``imports`` checks.

    A name is the repository's when the working directory holds a directory or a
    ``.py`` file of that name, or when any block, of any task, has a path whose first
    part is that name or that name plus ``.py``. A name that is not a Python
    identifier, and an ``EXCLUDES`` entry, never counts.
    """
    names: set[str] = set()
    for entry in Path(".").iterdir():
        if entry.is_dir():
            names.add(entry.name)
        elif entry.suffix == ".py" and entry.is_file():
            names.add(entry.stem)
    for block in blocks:
        for part in PurePosixPath(block.path).parts[:1]:
            names.add(part.removesuffix(".py"))
    return {name for name in names if name.isidentifier() and name not in EXCLUDES}


def provided_under(prefix: str, paths: set[str]) -> bool:
    """Return whether the tree or the landed ``paths`` hold a file under ``prefix``.

    The tree's ``EXCLUDES`` directories are not entered.
    """
    if any(path.startswith(prefix + "/") for path in paths):
        return True
    for _, subdirs, files in os.walk(prefix):
        subdirs[:] = [name for name in subdirs if name not in EXCLUDES]
        if files:
            return True
    return False


def module_kind(base: str, paths: set[str]) -> str | None:
    """Return what Python finds at ``base`` within its directory, or None.

    Its precedence, PEP 420's: a package with an ``__init__.py`` ("package"), then a
    module file ``base.py`` ("module"), then a directory that holds a file, read as a
    namespace package ("namespace"); each in the working tree or among the landed
    ``paths``.
    """
    if provided(base + "/__init__.py", paths):
        return "package"
    if provided(base + ".py", paths):
        return "module"
    if provided_under(base, paths):
        return "namespace"
    return None


def module_provided(base: str, paths: set[str]) -> bool:
    """Return whether the module at ``base`` is provided: the one rule for a module.

    A ``base.py`` file, or any file under ``base/`` (an ``__init__.py`` is one), in the
    working tree or among the landed ``paths``, provides it, whatever kind of package
    the directory is. Every prefix of its dotted name must resolve too, each by
    ``module_kind``: a prefix nothing provides, or one that resolves to a module file,
    which is no package to hold the rest, leaves the module unprovided.
    """
    parts = base.split("/")
    for depth in range(1, len(parts) + 1):
        kind = module_kind("/".join(parts[:depth]), paths)
        if kind is None or (kind == "module" and depth < len(parts)):
            return False
    return True


def provides_name(base: str, name: str, have: set[str], init_text: str) -> bool:
    """Return whether the package at ``base`` provides ``name`` to a ``from`` import.

    It does when the module ``base/name`` is provided (``module_provided``), whatever
    kind of package ``base`` is. A package with an ``__init__.py`` also provides a whole
    word of its text, ``init_text``; a namespace package has none (the text is empty).
    """
    if module_provided(f"{base}/{name}", have):
        return True
    return re.search(rf"\b{re.escape(name)}\b", init_text) is not None


def cmd_imports(blocks: list[Block]) -> int:
    """List the repository imports that no landed block or tree file provides.

    Only an import of a repository package is checked (``repository_packages``). A
    module is provided (``module_provided``) by a ``.py`` file or by any file under its
    directory, an ``__init__.py`` included, in the tree or in a landed block; a
    directory without ``__init__.py`` is a namespace package. Each prefix of its name
    resolves by Python's precedence (``module_kind``), and one that resolves to a
    module file leaves the rest unprovided. A module import checks that. A
    ``from X import n`` of a package also checks each name n: the module ``X.n`` must
    be provided by the same rule, whatever kind of package X is, or, when
    ``X/__init__.py`` is provided, n must occur as a whole word in its text (its tree
    text and the landed blocks' text). A multi-line import checks its module alone, and
    the names of a module file are attributes, not checked.
    """
    landed = landed_by_task(blocks)
    paths = {task: {block.path for block in lands} for task, lands in landed.items()}
    packages = repository_packages(blocks)
    ok = True
    for block in blocks:
        if not block.path.endswith(".py"):
            continue
        lands = landed[block.task]
        have = paths[block.task]
        for line in block.content.split("\n"):
            if block.kind == "diff" and not line.startswith("+"):
                continue
            match = IMPORT.match(line)
            if not match:
                continue
            module = match.group(1) or match.group(2)
            if module.split(".")[0] not in packages:
                continue
            base = module.replace(".", "/")
            if not module_provided(base, have):
                ok = False
                print(
                    f"task {block.task}: {block.path} imports {module}: "
                    "NOT FOUND by then"
                )
                continue
            names = imported_names(line[match.end() :]) if match.group(1) else None
            if names is None:
                continue
            kind = module_kind(base, have)
            if kind == "module":
                continue  # a module file: its names are attributes
            init_text = ""  # a namespace package: no __init__.py text to read
            if kind == "package":
                init_text = landed_text(base + "/__init__.py", lands)
            for name in names:
                if provides_name(base, name, have, init_text):
                    continue
                ok = False
                print(
                    f"task {block.task}: {block.path} imports {module}.{name}: "
                    "NOT FOUND by then"
                )
    print("imports checked")
    return 0 if ok else 1


def unified_diff(old: Path, new: Path, path: str) -> str:
    """Return ``diff -u old new`` with a/b headers; raise when the files agree."""
    done = subprocess.run(
        ["diff", "-u", str(old) if old.exists() else os.devnull, str(new)],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 1:
        raise RuntimeError(
            f"{path}: diff exit {done.returncode} (no difference, or an error)"
        )
    lines = done.stdout.splitlines()
    lines[0] = f"--- a/{path}"
    lines[1] = f"+++ b/{path}"
    return "\n".join(lines) + "\n"


def cmd_regen(plan: Path, blocks: list[Block], worktree: Path, overlay: Path) -> int:
    """Refill every block of ``plan`` from ``overlay``; strip trailing spaces."""
    lines = plan.read_text(encoding="utf-8").split("\n")
    for block in reversed(blocks):
        if block.kind == "whole":
            body = (overlay / block.path).read_text(encoding="utf-8").rstrip("\n")
        else:
            body = unified_diff(
                worktree / block.path, overlay / block.path, block.path
            ).rstrip("\n")
        fence = FENCE.match(lines[block.start - 1])
        assert fence is not None
        if fence.group(1) in body.split("\n"):
            raise RuntimeError(
                f"{block.path}: the body holds the fence {fence.group(1)!r}; "
                "use a longer one"
            )
        old = "\n".join(lines[block.start : block.end])
        same = [x.rstrip() for x in body.split("\n")] == [
            x.rstrip() for x in old.split("\n")
        ]
        print(
            f"{block.path:60} {block.kind:5} {'same' if same else 'changed':8} "
            f"{body.count(chr(10)) + 1:5} lines"
        )
        lines[block.start : block.end] = body.split("\n")
    text = "\n".join(line.rstrip() for line in lines)
    plan.write_text(text, encoding="utf-8")
    print("plan rewritten:", len(text.splitlines()), "lines")
    return 0


def copy_tree(source: Path, target: Path) -> None:
    """Copy ``source`` to ``target`` without the caches and the repository data."""
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(*EXCLUDES))


Identity = tuple[int, int]


def identity(path: Path) -> Identity | None:
    """Return the (device, inode) ``path`` names, a link followed; None if absent."""
    try:
        found = path.stat()
    except OSError:
        return None
    return found.st_dev, found.st_ino


def lineage(path: Path) -> set[Identity]:
    """Return the identities of ``path`` and of each of its ancestors that exists.

    A path that does not exist yet contributes from its nearest existing ancestor up.
    """
    found: set[Identity] = set()
    for candidate in (path, *path.parents):
        key = identity(candidate)
        if key is not None:
            found.add(key)
    return found


def overlap(worktree: Path, overlay: Path, scratch: Path) -> str | None:
    """Return why ``verify`` must refuse these resolved paths, or None when apart.

    ``verify`` deletes and rebuilds SCRATCH/tree and writes SCRATCH/the.diff, so the
    tree must neither be nor hold an input, and SCRATCH must neither be one nor lie
    inside one. The paths are compared by spelling and by filesystem identity — the
    device and inode of each path and of its existing ancestors, a link followed — so
    a case alias on a case-insensitive filesystem is refused too; a SCRATCH/tree that
    does not exist holds nothing. An input that is not a directory, and a SCRATCH/tree
    that is a link (to an input, into one, elsewhere or to itself), are refused as well.
    """
    tree = scratch / "tree"
    tree_id = identity(tree)
    around = lineage(tree)
    for name, path in (("WORKTREE", worktree), ("OVERLAY", overlay)):
        if not path.is_dir():
            return f"{name} ({path}) is not a directory"
        if (
            tree == path
            or tree in path.parents
            or (tree_id is not None and tree_id in lineage(path))
        ):
            return f"SCRATCH/tree ({tree}) is or holds {name} ({path})"
        path_id = identity(path)
        if (
            scratch == path
            or path in scratch.parents
            or (path_id is not None and path_id in around)
        ):
            return f"SCRATCH ({scratch}) or its tree is or lies inside {name} ({path})"
    if tree.is_symlink():
        return f"SCRATCH/tree ({tree}) is a symbolic link"
    return None


def cmd_verify(
    blocks: list[Block], worktree: Path, overlay: Path, scratch: Path
) -> int:
    """Apply the blocks to a copy of the worktree; compare it with the overlay.

    The three paths are resolved first; an overlap (``overlap``) exits 2 before
    anything is deleted. A link planted at SCRATCH/the.diff is removed before each
    write, so the file it names is never written through.
    """
    worktree, overlay, scratch = (p.resolve() for p in (worktree, overlay, scratch))
    problem = overlap(worktree, overlay, scratch)
    if problem is not None:
        print(f"refusing: {problem}; nothing deleted or written")
        return 2
    tree = scratch / "tree"
    if tree.exists():
        shutil.rmtree(tree)
    copy_tree(worktree, tree)
    failed: list[str] = []
    for block in blocks:
        target = tree / block.path
        target.parent.mkdir(parents=True, exist_ok=True)
        if block.kind == "whole":
            target.write_text(block.content, encoding="utf-8")
            continue
        diff_path = scratch / "the.diff"
        diff_path.unlink(missing_ok=True)
        diff_path.write_text(block.content, encoding="utf-8")
        done = subprocess.run(
            [
                "patch",
                "-p1",
                "-l",
                "-s",
                "-N",
                "--no-backup-if-mismatch",
                "-i",
                str(diff_path),
            ],
            cwd=tree,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        if done.returncode != 0:
            failed.append(f"{block.path}: {done.stdout.strip()} {done.stderr.strip()}")
    print(f"{len(blocks)} blocks applied; {len(failed)} failed")
    for failure in failed:
        print("FAILED:", failure)
    paths = sorted({block.path for block in blocks})
    differ = [p for p in paths if not filecmp.cmp(tree / p, overlay / p, shallow=False)]
    print(
        f"{len(paths)} files compared; "
        + ("all identical to the overlay" if not differ else f"DIFFER: {differ}")
    )
    return 0 if not failed and not differ else 1


def main(argv: list[str] | None = None) -> int:
    """Run the command line; return the exit status."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 2:
        print(__doc__)
        return 2
    mode, plan = args[0], Path(args[1])
    try:
        blocks = parse(plan)
    except PlanError as exc:
        print(f"refusing the plan: {exc}")
        return 2
    if mode == "list":
        return cmd_list(blocks)
    if mode == "imports":
        return cmd_imports(blocks)
    if mode == "applies":
        return cmd_applies(blocks, args[2])
    if mode == "check":
        return cmd_check(blocks, args[2], args[3])
    if mode == "extract":
        return cmd_extract(blocks, args[2], Path(args[3]))
    if mode == "regen":
        return cmd_regen(plan, blocks, Path(args[2]), Path(args[3]))
    if mode == "verify":
        return cmd_verify(blocks, Path(args[2]), Path(args[3]), Path(args[4]))
    print(f"unknown mode {mode}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
