import pytest

from swp5_input.actions import Action, Kind
from swp5_input.driver import DriverError, SWPDriver
from swp5_input.parser import ParseError, parse_document, parse_swp_command


class FakeKeyboard:
    def send_keys(self, *_args, **_kwargs):
        pass


class FakeWindow:
    def __init__(self, failures=None):
        self.calls = []
        self.failures = set(failures or [])

    def menu_select(self, path):
        self.calls.append(path)
        if path in self.failures:
            raise RuntimeError("not found")


def test_directive_becomes_semantic_action_and_is_not_typed():
    actions = parse_document("$$x\\tan x$$\n[[swp:plot:2d]]\nDone.")
    command_index = next(i for i, action in enumerate(actions) if action.kind == Kind.SWP_COMMAND)
    assert actions[command_index].value == "plot:2d"
    assert actions[command_index - 1].kind == Kind.DISPLAY_END
    assert actions[command_index + 1].kind == Kind.TEXT
    assert actions[command_index + 1].value.startswith("\n")
    assert not any("[[swp:" in (action.value or "") for action in actions if action.kind == Kind.TEXT)


def test_supported_command_parser():
    assert parse_swp_command("compute:evaluate-numerically") == Action(
        Kind.SWP_COMMAND, "compute:evaluate-numerically"
    )


def test_unknown_directive_fails_closed():
    with pytest.raises(ParseError):
        parse_document("[[swp:compute:invent-result]]")


def test_driver_uses_compute_menu_path():
    driver = SWPDriver()
    driver._keyboard = FakeKeyboard()
    window = FakeWindow()
    driver._window = window

    driver._send_swp_command("compute:evaluate-numerically")

    assert window.calls == ["Compute->Evaluate Numerically"]


def test_driver_falls_back_for_plot_menu_spelling():
    driver = SWPDriver()
    driver._keyboard = FakeKeyboard()
    window = FakeWindow(failures={"Compute->Plot 2D"})
    driver._window = window

    driver._send_swp_command("plot:2d")

    assert window.calls == ["Compute->Plot 2D", "Compute->Plot2D"]


def test_driver_rejects_unknown_command():
    driver = SWPDriver()
    driver._keyboard = FakeKeyboard()
    driver._window = FakeWindow()

    with pytest.raises(DriverError):
        driver._send_swp_command("compute:invent-result")
