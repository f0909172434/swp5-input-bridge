from pathlib import Path

from swp5_input.actions import Kind
from swp5_input.parser import parse_document


def test_native_compute_plot_smoke_document_has_real_swp_actions():
    source = Path("examples/swp-native-compute-plot-smoke.swpmd").read_text(encoding="utf-8")
    actions = parse_document(source)

    commands = [a.value for a in actions if a.kind == Kind.SWP_COMMAND]
    assert commands == [
        "compute:evaluate",
        "compute:evaluate-numerically",
        "plot:2d",
    ]
    assert sum(a.kind == Kind.CURSOR_LEFT for a in actions) == 3
