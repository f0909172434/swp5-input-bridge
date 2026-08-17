from pathlib import Path

from swp5_input.actions import Kind
from swp5_input.parser import parse_document


def test_native_swp_plot_range_smoke_document():
    source = Path("examples/swp-native-plot-range-smoke.swpmd").read_text(encoding="utf-8")
    actions = parse_document(source)

    command_index = next(i for i, action in enumerate(actions) if action.kind == Kind.SWP_COMMAND)
    assert actions[command_index - 1].kind == Kind.CURSOR_LEFT
    assert actions[command_index].value == "plot:2d-rectangular-range:0:1.45"
    assert any(a.kind == Kind.TEX and a.value == "tan" for a in actions)

    displays = source.split("$$")[1::2]
    assert displays
    assert all(block.strip()[-1] not in ".,;:" for block in displays)
    assert "K_\\rho" not in source
