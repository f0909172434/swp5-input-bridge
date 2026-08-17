from __future__ import annotations

import os
import time
from typing import Iterable

from .actions import Action, Kind
from .profile import SWP55Profile


class DriverError(RuntimeError):
    pass


class SWPDriver:
    def __init__(self, profile: SWP55Profile | None = None, pause: float = 0.03):
        self.profile = profile or SWP55Profile()
        self.pause = pause
        self._keyboard = None
        self._window = None

    def connect(self) -> None:
        if os.name != "nt":
            raise DriverError("Live SWP automation is supported only on Windows. Use 'plan' on other platforms.")
        try:
            from pywinauto import Desktop, keyboard
        except ImportError as exc:
            raise DriverError("pywinauto is required for live automation on Windows.") from exc

        candidates = Desktop(backend="win32").windows(title_re=self.profile.window_title_regex, visible_only=True)
        if not candidates:
            raise DriverError("Scientific WorkPlace window not found. Open SWP 5.5 and a document first.")
        if len(candidates) > 1:
            titles = [w.window_text() for w in candidates]
            raise DriverError(f"Multiple SWP windows found; keep one target window open: {titles}")
        self._window = candidates[0]
        self._window.set_focus()
        self._keyboard = keyboard

    def execute(self, actions: Iterable[Action]) -> None:
        if self._window is None or self._keyboard is None:
            self.connect()
        assert self._window is not None and self._keyboard is not None
        for action in actions:
            if not self._window.has_focus():
                raise DriverError("SWP lost focus; aborting before sending more input.")
            self._execute_one(action)
            time.sleep(self.pause)

    def _execute_one(self, action: Action) -> None:
        assert self._keyboard is not None
        send = self._keyboard.send_keys
        p = self.profile

        if action.kind in {Kind.TEXT, Kind.TYPE}:
            self._paste(action.value or "")
        elif action.kind == Kind.TEX:
            self._send_tex(action.value or "")
        elif action.kind == Kind.DISPLAY_START:
            send(p.display_start)
        elif action.kind == Kind.DISPLAY_END:
            send(p.display_end)
        elif action.kind == Kind.MATH_START:
            send(p.math_start)
        elif action.kind == Kind.MATH_END:
            send(p.math_end)
        elif action.kind == Kind.SUBSCRIPT:
            send(p.subscript)
        elif action.kind == Kind.SUPERSCRIPT:
            send(p.superscript)
        elif action.kind == Kind.FRACTION:
            send(p.fraction)
        elif action.kind == Kind.RADICAL:
            send(p.radical)
        elif action.kind == Kind.INTEGRAL:
            send(p.integral)
        elif action.kind == Kind.NEXT_FIELD:
            send(p.next_field)
        elif action.kind == Kind.EXIT_TEMPLATE:
            send(p.exit_template)
        elif action.kind == Kind.NEWLINE:
            send("{ENTER}")
        else:
            raise DriverError(f"Unsupported action kind: {action.kind}")

    def _paste(self, text: str) -> None:
        if not text:
            return
        try:
            import pyperclip
        except ImportError as exc:
            raise DriverError("pyperclip is required for live automation on Windows.") from exc
        pyperclip.copy(text)
        self._keyboard.send_keys("^v")

    def _send_tex(self, name: str) -> None:
        if not name.isalpha():
            raise DriverError(f"Unsafe TeX macro name: {name!r}")
        self._keyboard.send_keys(f"^({name})")
