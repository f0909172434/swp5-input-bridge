from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SWP55Profile:
    """Keyboard profile for Scientific WorkPlace 5.5 on Windows."""

    window_title_regex: str = r".*Scientific WorkPlace.*"
    math_start: str = "^m"
    math_end: str = "^t"
    display_start: str = "^d"
    fraction: str = "^f"
    radical: str = "^r"
    superscript: str = "^h"
    subscript: str = "^l"
    integral: str = "^i"
    next_field: str = "{TAB}"
    exit_template: str = "{SPACE}"
    display_end: str = "{RIGHT}"
