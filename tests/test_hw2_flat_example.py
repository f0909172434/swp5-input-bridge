from pathlib import Path

from swp5_input.actions import Kind
from swp5_input.parser import parse_document


def test_hw2_flat_left_end_example_parses_end_to_end():
    source = Path("examples/hw2-left-end-flat.swpmd").read_text(encoding="utf-8")
    actions = parse_document(source)

    assert any(a.kind == Kind.DISPLAY_START for a in actions)
    assert any(a.kind == Kind.MATH_START for a in actions)
    assert any(a.kind == Kind.TEX and a.value == "Lambda" for a in actions)
    assert any(a.kind == Kind.TEX and a.value == "liminf" for a in actions)
    assert any(a.kind == Kind.FRACTION for a in actions)
    assert any(a.kind == Kind.RADICAL for a in actions)
    assert any(a.kind == Kind.INTEGRAL for a in actions)
    assert "\\ref" not in source
    assert "\\label" not in source
    assert "(ref:" not in source
