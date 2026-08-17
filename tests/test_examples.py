from pathlib import Path

from swp5_input.actions import Kind
from swp5_input.parser import parse_document


def test_hw2_left_end_example_parses_end_to_end():
    root = Path(__file__).resolve().parents[1]
    source = (root / "examples" / "hw2-left-end.swpmd").read_text(encoding="utf-8")

    actions = parse_document(source)

    assert actions
    assert any(a.kind == Kind.DISPLAY_START for a in actions)
    assert any(a.kind == Kind.MATH_START for a in actions)
    assert any(a.kind == Kind.FRACTION for a in actions)
    assert any(a.kind == Kind.INTEGRAL for a in actions)
    assert any(a.kind == Kind.RADICAL for a in actions)
    assert any(a.kind == Kind.TEX and a.value == "Lambda" for a in actions)
    assert any(a.kind == Kind.TEX and a.value == "rho" for a in actions)
    assert any(a.kind == Kind.TEX and a.value == "limsup" for a in actions)


def test_hw2_left_end_example_has_no_reference_markup():
    root = Path(__file__).resolve().parents[1]
    source = (root / "examples" / "hw2-left-end.swpmd").read_text(encoding="utf-8")

    assert "\\ref" not in source
    assert "\\label" not in source
    assert "(ref:" not in source
