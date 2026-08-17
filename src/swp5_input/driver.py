from __future__ import annotations

import os
import re
import time
from typing import Iterable

from .actions import (
    Action,
    Kind,
    SUPPORTED_SWP_COMMANDS,
    is_supported_swp_command,
    parse_plot_2d_range_command,
)
from .profile import SWP55Profile


class DriverError(RuntimeError):
    pass


_COMMAND_MENU_PATHS = {
    "compute:evaluate": ("Compute->Evaluate",),
    "compute:evaluate-numerically": ("Compute->Evaluate Numerically",),
    "compute:simplify": ("Compute->Simplify",),
    "compute:solve-exact": ("Compute->Solve->Exact",),
    "plot:2d": (
        "Compute->Plot 2D->Rectangular",
        "Compute->Plot2D->Rectangular",
        "Compute->Plot 2D",
        "Compute->Plot2D",
    ),
    "plot:3d": (
        "Compute->Plot 3D->Rectangular",
        "Compute->Plot3D->Rectangular",
        "Compute->Plot 3D",
        "Compute->Plot3D",
    ),
    "typeset:compile-pdf": ("Typeset->Compile PDF",),
    "typeset:preview-pdf": ("Typeset->Preview PDF",),
}

_PLOT_2D_RECTANGULAR_PATHS = (
    "Compute->Plot 2D->Rectangular",
    "Compute->Plot2D->Rectangular",
)


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
        elif action.kind == Kind.CURSOR_LEFT:
            send("{LEFT}")
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
        if not is_supported_swp_command(command):
            raise DriverError(f"Unsupported SWP command: {command!r}")

        plot_range = parse_plot_2d_range_command(command)
        if plot_range is not None:
            self._send_plot_2d_with_interval(*plot_range)
            return

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

    def _send_plot_2d_with_interval(self, xmin: float, xmax: float) -> None:
        """Create a native rectangular plot after setting its x sampling interval."""
        if self._window is None or self._keyboard is None:
            raise DriverError("Scientific WorkPlace window is not connected")

        errors = []
        opened = False
        self._keyboard.send_keys("{VK_CONTROL down}", vk_packet=False)
        try:
            for path in _PLOT_2D_RECTANGULAR_PATHS:
                try:
                    self._window.menu_select(path)
                    opened = True
                    break
                except Exception as exc:
                    errors.append(f"{path}: {exc}")
        finally:
            self._keyboard.send_keys("{VK_CONTROL up}", vk_packet=False)

        if not opened:
            raise DriverError("Could not invoke native rectangular plot: " + "; ".join(errors))

        try:
            self._configure_plot_interval_dialog(xmin, xmax)
        except Exception as exc:
            if isinstance(exc, DriverError):
                raise
            raise DriverError(f"Could not configure SWP Plot Properties interval: {exc}") from exc

        try:
            self._window.set_focus()
        except Exception:
            pass

    def _configure_plot_interval_dialog(self, xmin: float, xmax: float) -> None:
        plot_dialog = self._find_plot_properties_dialog(timeout=6)
        plot_handle = getattr(plot_dialog, "handle", None)

        items_tab = self._find_control(plot_dialog, ("items", "plotted"), preferred_types={"TabItem"})
        self._activate_control(items_tab)
        time.sleep(0.15)

        interval_button = self._find_control(
            plot_dialog,
            ("variables", "intervals", "automation"),
            preferred_types={"Button"},
        )
        self._activate_control(interval_button)
        time.sleep(0.15)

        interval_dialog = self._find_interval_dialog(exclude_handle=plot_handle, timeout=5)
        edits = [control for control in interval_dialog.descendants() if self._control_type(control) == "Edit"]
        numeric = []
        for edit in edits:
            value = self._numeric_control_value(edit)
            if value is not None:
                numeric.append((edit, value))

        lower_boxes = [control for control, value in numeric if abs(value + 5.0) <= 0.25]
        upper_boxes = [control for control, value in numeric if abs(value - 5.0) <= 0.25]
        if not lower_boxes or not upper_boxes:
            raise DriverError(
                "Plot Intervals opened, but the default rectangular -5 and 5 interval boxes could not be identified. "
                + self._control_summary(interval_dialog)
            )

        for control in lower_boxes:
            self._set_edit(control, self._format_number(xmin))
        for control in upper_boxes:
            self._set_edit(control, self._format_number(xmax))
        self._click_ok(interval_dialog)

        plot_dialog = self._find_plot_properties_dialog(timeout=3, preferred_handle=plot_handle)
        self._click_ok(plot_dialog)

    def _find_plot_properties_dialog(self, timeout: float, preferred_handle=None):
        return self._find_legacy_dialog(
            self._is_plot_properties_title,
            timeout=timeout,
            preferred_handle=preferred_handle,
            missing_message=(
                "Plot Properties is visible in SWP but the automation could not attach to it. "
                "The dialog is a legacy Win32 window, so discovery must use its native HWND rather than UIA title enumeration."
            ),
        )

    def _find_interval_dialog(self, exclude_handle=None, timeout: float = 5):
        return self._find_legacy_dialog(
            self._is_interval_dialog_title,
            timeout=timeout,
            exclude_handle=exclude_handle,
            missing_message="Variables, Intervals, and Automation was opened, but its interval dialog was not found",
        )

    def _find_legacy_dialog(
        self,
        title_matcher,
        *,
        timeout: float,
        preferred_handle=None,
        exclude_handle=None,
        missing_message: str,
    ):
        """Discover old SWP modal dialogs with win32, then re-wrap by HWND for UIA controls.

        SWP 5.5 predates modern UI Automation. On current Windows versions a dialog can be
        plainly visible and still be absent from Desktop(backend='uia').windows(). Native
        win32 enumeration reliably sees the HWND; once found, UIA can usually wrap that same
        handle and expose tab/button/edit controls.
        """
        try:
            from pywinauto import Desktop
        except ImportError as exc:
            raise DriverError("pywinauto is required for Plot Properties automation") from exc

        deadline = time.time() + timeout
        seen_titles: list[str] = []
        while time.time() < deadline:
            win32_desktop = Desktop(backend="win32")
            matches = []
            for window in win32_desktop.windows(visible_only=True):
                try:
                    handle = getattr(window, "handle", None)
                    if exclude_handle is not None and handle == exclude_handle:
                        continue
                    title = window.window_text().strip()
                    if title and title not in seen_titles:
                        seen_titles.append(title)
                    if title_matcher(title):
                        matches.append(window)
                except Exception:
                    continue

            if preferred_handle is not None:
                matches.sort(key=lambda w: 0 if getattr(w, "handle", None) == preferred_handle else 1)

            for win32_window in matches:
                handle = getattr(win32_window, "handle", None)
                if handle is None:
                    continue
                try:
                    uia_spec = Desktop(backend="uia").window(handle=handle)
                    uia_spec.wait("visible", timeout=0.5)
                    return uia_spec.wrapper_object()
                except Exception:
                    # Legacy controls may not expose a UIA provider. Returning the native
                    # wrapper is still better than claiming that the visible dialog is absent.
                    return win32_window

            time.sleep(0.1)

        titles = ", ".join(repr(title) for title in seen_titles[-20:])
        suffix = f" Visible top-level windows: {titles}" if titles else ""
        raise DriverError(missing_message + suffix)

    @staticmethod
    def _is_plot_properties_title(title: str) -> bool:
        return "plot properties" in title.strip().lower()

    @staticmethod
    def _is_interval_dialog_title(title: str) -> bool:
        text = title.strip().lower()
        is_plot_interval = "plot interval" in text or ("interval" in text and "plot" in text)
        is_variables_interval = "interval" in text and "variable" in text
        return is_plot_interval or is_variables_interval

    @staticmethod
    def _control_type(control) -> str:
        return str(getattr(getattr(control, "element_info", None), "control_type", ""))

    def _find_control(self, parent, tokens: tuple[str, ...], preferred_types: set[str] | None = None):
        candidates = []
        for control in parent.descendants():
            try:
                text = control.window_text().strip().lower()
            except Exception:
                continue
            if text and all(token in text for token in tokens):
                candidates.append(control)
        if preferred_types:
            typed = [c for c in candidates if self._control_type(c) in preferred_types]
            if typed:
                return typed[0]
        if candidates:
            return candidates[0]
        raise DriverError(
            f"Could not find control containing {tokens}. " + self._control_summary(parent)
        )

    @staticmethod
    def _activate_control(control) -> None:
        if hasattr(control, "select"):
            try:
                control.select()
                return
            except Exception:
                pass
        control.click_input()

    @staticmethod
    def _numeric_control_value(control) -> float | None:
        values = []
        for getter in ("get_value", "window_text"):
            if not hasattr(control, getter):
                continue
            try:
                values.append(str(getattr(control, getter)()))
            except Exception:
                pass
        for text in values:
            text = text.strip().replace("−", "-")
            match = re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text)
            if match:
                try:
                    return float(text)
                except ValueError:
                    pass
        return None

    @staticmethod
    def _set_edit(control, value: str) -> None:
        if hasattr(control, "set_edit_text"):
            control.set_edit_text(value)
            return
        if hasattr(control, "set_text"):
            control.set_text(value)
            return
        control.click_input()
        control.type_keys("^a" + value, set_foreground=False)

    def _click_ok(self, dialog) -> None:
        ok = self._find_control(dialog, ("ok",), preferred_types={"Button"})
        self._activate_control(ok)
        time.sleep(0.2)

    @staticmethod
    def _format_number(value: float) -> str:
        return f"{value:.12g}"

    def _control_summary(self, parent) -> str:
        parts = []
        for control in parent.descendants()[:80]:
            try:
                text = control.window_text().strip()
                kind = self._control_type(control)
                if text:
                    parts.append(f"{kind}:{text!r}")
            except Exception:
                continue
        return "Visible controls: " + ", ".join(parts)
