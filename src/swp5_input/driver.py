from __future__ import annotations

import os
import time
from typing import Iterable

from .actions import Action, Kind, SUPPORTED_SWP_COMMANDS
from .profile import SWP55Profile


class DriverError(RuntimeError):
    pass


_COMMAND_MENU_PATHS = {
    "compute:evaluate": ("Compute->Evaluate",),
    "compute:evaluate-numerically": ("Compute->Evaluate Numerically",),
    "compute:simplify": ("Compute->Simplify",),
    "compute:solve-exact": ("Compute->Solve->Exact",),
    "plot:2d": ("Compute->Plot 2D", "Compute->Plot2D"),
    "plot:3d": ("Compute->Plot 3D", "Compute->Plot3D"),
    "typeset:compile-pdf": ("Typeset->Compile PDF",),
    "typeset:preview-pdf": ("Typeset->Preview PDF",),
}


class SWPDriver:
    def __init__(self, profile: SWP55Profile | None = None, pause: float = 0.03, command_pause: float = 0.8):
        self.profile = profile or SWP55Profile()
        self.pause = pause
        self.command_pause = command_pause
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
            time.sleep(self.command_pause if action.kind == Kind.SWP_COMMAND else self.pause)

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
        elif action.kind == Kind.SWP_COMMAND:
            self._send_swp_command(action.value or "")
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
        send = self._keyboard.send_keys
        send("{VK_CONTROL down}", vk_packet=False)
        try:
            if name[0].isupper():
                send("{VK_SHIFT down}", vk_packet=False)
                try:
                    send(name[0].lower(), vk_packet=False)
                finally:
                    send("{VK_SHIFT up}", vk_packet=False)
                if len(name) > 1:
                    send(name[1:], vk_packet=False)
            else:
                send(name, vk_packet=False)
        finally:
            send("{VK_CONTROL up}", vk_packet=False)

    def _send_swp_command(self, command: str) -> None:
        if command not in SUPPORTED_SWP_COMMANDS:
            raise DriverError(f"Unsupported SWP command: {command!r}")
        if self._window is None:
            raise DriverError("Scientific WorkPlace window is not connected")

        errors = []
        for path in _COMMAND_MENU_PATHS[command]:
            try:
                self._window.menu_select(path)
                return
            except Exception as exc:
                errors.append(f"{path}: {exc}")

        attempted = "; ".join(errors)
        raise DriverError(
            f"Could not invoke SWP command {command!r}. Tried menu paths: {attempted}. "
            "This usually means the installed SWP menu text differs from the English 5.5 menu."
        )
