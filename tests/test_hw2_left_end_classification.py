from pathlib import Path

from swp5_input.actions import Kind
from swp5_input.parser import parse_document


def test_hw2_left_end_classification_parses_end_to_end():
    source = Path("examples/hw2-left-end-classification.swpmd").read_text(encoding="utf-8")
    actions = parse_document(source)

    assert actions
    assert any(a.kind == Kind.DISPLAY_START for a in actions)
    assert any(a.kind == Kind.MATH_START for a in actions)
    assert any(a.kind == Kind.FRACTION for a in actions)
    assert any(a.kind == Kind.RADICAL for a in actions)
    assert any(a.kind == Kind.INTEGRAL for a in actions)

    for command in [
        "Lambda",
        "lim",
        "limsup",
        "liminf",
        "theta",
        "tan",
        "cos",
        "sin",
        "arccos",
        "pi",
        "infty",
    ]:
        assert any(a.kind == Kind.TEX and a.value == command for a in actions)

    assert "Case 1." in source
    assert "Case 2." in source
    assert "Case 3." in source
    assert "K_\\rho" not in source
    assert "\\ref" not in source
    assert "\\label" not in source
