"""The document check as a test, for a Python host (docs/process.md, Budgets).

`tools/doc_budgets.py check` over this repository, as `python3 -I tools/doc_budgets.py check` runs it: each problem
it finds is printed as `<path>: <message>`, and pytest shows the printed lines when the test fails.
"""

from __future__ import annotations

from pathlib import Path

from tools import doc_budgets

ROOT = Path(__file__).resolve().parents[2]


def test_the_documents_are_within_their_budgets():
    assert doc_budgets.main(["check", "--root", str(ROOT)]) == 0
