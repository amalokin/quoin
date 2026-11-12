"""Collection rules for the pack's own checks.

`fixtures/` holds the example host repository for path B. It has a unittest suite of its own, run through its own
`make` target, so the pack's collection must not pick it up.
"""

from __future__ import annotations

collect_ignore = ["fixtures"]
