from swp5_input.driver import SWPDriver


class FakeKeyboard:
    def __init__(self):
        self.calls = []

    def send_keys(self, keys, **kwargs):
        self.calls.append((keys, kwargs))


def test_tex_command_holds_ctrl_for_entire_name():
    driver = SWPDriver()
    keyboard = FakeKeyboard()
    driver._keyboard = keyboard

    driver._send_tex("rho")

    assert keyboard.calls == [
        ("{VK_CONTROL down}", {"vk_packet": False}),
        ("rho", {"vk_packet": False}),
        ("{VK_CONTROL up}", {"vk_packet": False}),
    ]


def test_capital_tex_command_shifts_initial_only():
    driver = SWPDriver()
    keyboard = FakeKeyboard()
    driver._keyboard = keyboard

    driver._send_tex("Lambda")

    assert keyboard.calls == [
        ("{VK_CONTROL down}", {"vk_packet": False}),
        ("{VK_SHIFT down}", {"vk_packet": False}),
        ("l", {"vk_packet": False}),
        ("{VK_SHIFT up}", {"vk_packet": False}),
        ("ambda", {"vk_packet": False}),
        ("{VK_CONTROL up}", {"vk_packet": False}),
    ]


def test_tex_command_releases_ctrl_if_typing_raises():
    class RaisingKeyboard(FakeKeyboard):
        def send_keys(self, keys, **kwargs):
            self.calls.append((keys, kwargs))
            if keys == "rho":
                raise RuntimeError("boom")

    driver = SWPDriver()
    keyboard = RaisingKeyboard()
    driver._keyboard = keyboard

    try:
        driver._send_tex("rho")
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected RuntimeError")

    assert keyboard.calls[-1] == ("{VK_CONTROL up}", {"vk_packet": False})


def test_capital_tex_command_releases_shift_and_ctrl_on_failure():
    class RaisingKeyboard(FakeKeyboard):
        def send_keys(self, keys, **kwargs):
            self.calls.append((keys, kwargs))
            if keys == "l":
                raise RuntimeError("boom")

    driver = SWPDriver()
    keyboard = RaisingKeyboard()
    driver._keyboard = keyboard

    try:
        driver._send_tex("Lambda")
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected RuntimeError")

    assert ("{VK_SHIFT up}", {"vk_packet": False}) in keyboard.calls
    assert keyboard.calls[-1] == ("{VK_CONTROL up}", {"vk_packet": False})
