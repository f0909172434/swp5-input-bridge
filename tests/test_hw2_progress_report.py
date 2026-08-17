from pathlib import Path

from swp5_input.actions import Kind
from swp5_input.parser import parse_document


def test_hw2_progress_report_parses_and_contains_live_swp_actions():
    source = Path("examples/hw2-progress-report.swpmd").read_text(encoding="utf-8")
    actions = parse_document(source)

    assert actions
    assert any(a.kind == Kind.DISPLAY_START for a in actions)
    assert any(a.kind == Kind.MATH_START for a in actions)
    assert any(a.kind == Kind.FRACTION for a in actions)
    assert any(a.kind == Kind.RADICAL for a in actions)
    assert any(a.kind == Kind.INTEGRAL for a in actions)
    assert any(a.kind == Kind.SWP_COMMAND and a.value == "compute:evaluate-numerically" for a in actions)
    assert any(a.kind == Kind.SWP_COMMAND and a.value == "plot:2d" for a in actions)

    for command in ["Lambda", "lim", "limsup", "liminf", "theta", "tan", "cos", "sin", "arccos", "pi", "infty"]:
        assert any(a.kind == Kind.TEX and a.value == command for a in actions)

    assert "Problem and branch formulation" in source
    assert "Left-end classification" in source
    assert "SWP computational illustration" in source
    assert "K_\\rho" not in source
    assert "[[swp:compute:evaluate-numerically]]" in source
    assert "[[swp:plot:2d]]" in source
