"""Put the repository's root on the import path, so the tests import `tools.doc_budgets` as the repository runs it.

`tests/` has no `__init__.py`, nor has any directory under it: a `tests/tools` package would stand in front of the
repository's own `tools/`, so the test files keep basenames that are unique across the repository instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
