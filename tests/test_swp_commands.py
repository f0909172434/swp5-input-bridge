import pytest

from swp5_input.actions import Action, Kind
from swp5_input.driver import DriverError, SWPDriver
from swp5_input.parser import ParseError, parse_document, parse_swp_command


class FakeKeyboard:
    def __init__(self):
        self.calls = []

    def send_keys(self, keys, **kwargs):
        self.calls.append((keys, kwargs))


class FakeWindow:
    def __init__(self, failures=None):
        self.calls = []
        self.failures = set(failures or [])

    def menu_select(self, path):
        self.calls.append(path)
        if path in self.failures:
            raise RuntimeError("not found")


def test_directive_reenters_math_before_native_plot_command():
    actions = parse_document("$$x\\tan x$$\n[[swp:plot:2d]]\nDone.")
    command_index = next(i for i, action in enumerate(actions) if action.kind == Kind.SWP_COMMAND)
    assert actions[command_index].value == "plot:2d"
    assert actions[command_index - 1].kind == Kind.CURSOR_LEFT
    assert actions[command_index - 2].kind == Kind.DISPLAY_END
    assert actions[command_index + 1].kind == Kind.TEXT
    assert actions[command_index + 1].value.startswith("\n")
    assert not any("[[swp:" in (action.value or "") for action in actions if action.kind == Kind.TEXT)


def test_compute_directive_reenters_math_too():
    actions = parse_document("$$2+3$$\n[[swp:compute:evaluate-numerically]]")
    command_index = next(i for i, action in enumerate(actions) if action.kind == Kind.SWP_COMMAND)
    assert actions[command_index - 1].kind == Kind.CURSOR_LEFT


def test_supported_command_parser():
    assert parse_swp_command("compute:evaluate-numerically") == Action(
        Kind.SWP_COMMAND, "compute:evaluate-numerically"
    )


def test_unknown_directive_fails_closed():
    with pytest.raises(ParseError):
        parse_document("[[swp:compute:invent-result]]")


def test_cursor_left_action_uses_keyboard():
    driver = SWPDriver()
    keyboard = FakeKeyboard()
    driver._keyboard = keyboard
    driver._window = FakeWindow()

    driver._execute_one(Action(Kind.CURSOR_LEFT))

    assert keyboard.calls == [("{LEFT}", {})]


def test_driver_uses_compute_menu_path():
    driver = SWPDriver()
    driver._keyboard = FakeKeyboard()
    window = FakeWindow()
    driver._window = window

    driver._send_swp_command("compute:evaluate-numerically")

    assert window.calls == ["Compute->Evaluate Numerically"]


def test_driver_uses_rectangular_2d_plot_command():
    driver = SWPDriver()
    driver._keyboard = FakeKeyboard()
    window = FakeWindow()
    driver._window = window

    driver._send_swp_command("plot:2d")

    assert window.calls == ["Compute->Plot 2D->Rectangular"]


def test_driver_falls_back_for_plot_menu_spelling():
    driver = SWPDriver()
    driver._keyboard = FakeKeyboard()
    window = FakeWindow(failures={"Compute->Plot 2D->Rectangular"})
    driver._window = window

    driver._send_swp_command("plot:2d")

    assert window.calls == [
        "Compute->Plot 2D->Rectangular",
        "Compute->Plot2D->Rectangular",
    ]


def test_driver_rejects_unknown_command():
    driver = SWPDriver()
    driver._keyboard = FakeKeyboard()
    driver._window = FakeWindow()

    with pytest.raises(DriverError):
        driver._send_swp_command("compute:invent-result")
