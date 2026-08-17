import pytest

from swp5_input.actions import Kind
from swp5_input.parser import ParseError, parse_document, parse_math


def sig(actions):
    return [(a.kind.value, a.value) for a in actions]


def test_limit_expression():
    actions = parse_math(r"\lim_{\rho\to0^+}K_\rho(m_\rho)=0")
    assert sig(actions) == [
        ("tex", "lim"),
        ("subscript", None),
        ("tex", "rho"),
        ("tex", "to"),
        ("type", "0"),
        ("superscript", None),
        ("type", "+"),
        ("exit_template", None),
        ("exit_template", None),
        ("type", "K"),
        ("subscript", None),
        ("tex", "rho"),
        ("exit_template", None),
        ("type", "(m"),
        ("subscript", None),
        ("tex", "rho"),
        ("exit_template", None),
        ("type", ")=0"),
    ]


def test_fraction_and_integral():
    actions = parse_math(r"F(s)=\int_0^s f(t)\,dt+\frac{1}{2}")
    kinds = [a.kind for a in actions]
    assert Kind.INTEGRAL in kinds
    assert Kind.FRACTION in kinds
    assert Kind.NEXT_FIELD in kinds


def test_document_display_blocks():
    actions = parse_document("Lemma.\n$$K_\\rho=0$$\nDone.")
    assert actions[0].kind == Kind.TEXT
    assert any(a.kind == Kind.DISPLAY_START for a in actions)
    assert any(a.kind == Kind.DISPLAY_END for a in actions)
    assert actions[-1].kind == Kind.TEXT


def test_rejects_unknown_command():
    with pytest.raises(ParseError):
        parse_math(r"\totallyunknown{x}")
