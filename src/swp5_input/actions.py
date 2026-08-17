from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


SUPPORTED_SWP_COMMANDS = (
    "compute:evaluate",
    "compute:evaluate-numerically",
    "compute:simplify",
    "compute:solve-exact",
    "plot:2d",
    "plot:3d",
    "typeset:compile-pdf",
    "typeset:preview-pdf",
)

PLOT_2D_RANGE_PREFIX = "plot:2d-rectangular-range:"


def parse_plot_2d_range_command(command: str) -> tuple[float, float] | None:
    """Return (xmin, xmax) for a parameterized rectangular plot directive."""
    if not command.startswith(PLOT_2D_RANGE_PREFIX):
        return None
    payload = command[len(PLOT_2D_RANGE_PREFIX):]
    parts = payload.split(":")
    if len(parts) != 2:
        return None
    try:
        xmin, xmax = (float(part) for part in parts)
    except ValueError:
        return None
    if not xmin < xmax:
        return None
    return xmin, xmax


def is_supported_swp_command(command: str) -> bool:
    return command in SUPPORTED_SWP_COMMANDS or parse_plot_2d_range_command(command) is not None


class Kind(str, Enum):
    TEXT = "text"
    TYPE = "type"
    TEX = "tex"
    DISPLAY_START = "display_start"
    DISPLAY_END = "display_end"
    MATH_START = "math_start"
    MATH_END = "math_end"
    SUBSCRIPT = "subscript"
    SUPERSCRIPT = "superscript"
    FRACTION = "fraction"
    RADICAL = "radical"
    INTEGRAL = "integral"
    NEXT_FIELD = "next_field"
    EXIT_TEMPLATE = "exit_template"
    NEWLINE = "newline"
    CURSOR_LEFT = "cursor_left"
    SWP_COMMAND = "swp_command"


@dataclass(frozen=True)
class Action:
    kind: Kind
    value: str | None = None

    def render(self) -> str:
        if self.value is None:
            return self.kind.value
        return f"{self.kind.value}: {self.value!r}"
