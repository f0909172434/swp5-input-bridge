from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .actions import Action, Kind
from .driver import DriverError, SWPDriver
from .parser import ParseError, parse_document, parse_math


def _actions_from_args(args):
    if args.expr is not None:
        return [Action(Kind.MATH_START), *parse_math(args.expr), Action(Kind.MATH_END)]
    path = Path(args.file)
    return parse_document(path.read_text(encoding="utf-8"))


def cmd_plan(args) -> int:
    actions = _actions_from_args(args)
    for index, action in enumerate(actions, 1):
        print(f"{index:03d}  {action.render()}")
    return 0


def cmd_write(args) -> int:
    if not args.yes:
        print("Refusing live input without --yes. Run 'plan' first, then repeat with --yes.", file=sys.stderr)
        return 2
    actions = _actions_from_args(args)
    driver = SWPDriver(pause=args.pause)
    driver.execute(actions)
    return 0


def cmd_doctor(_args) -> int:
    print(f"swp5-input-bridge {__version__}")
    print(f"platform: {sys.platform}")
    if os.name != "nt":
        print("live driver: unavailable (Windows required)")
        return 1
    try:
        driver = SWPDriver()
        driver.connect()
    except DriverError as exc:
        print(f"live driver: NOT READY - {exc}")
        return 1
    print("live driver: ready; exactly one visible Scientific WorkPlace window found")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swp5-input", description="Scientific WorkPlace 5.5 math input bridge")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="check whether live SWP automation is available")
    doctor.set_defaults(func=cmd_doctor)

    for name, func, help_text in [
        ("plan", cmd_plan, "parse input and print actions without touching SWP"),
        ("write", cmd_write, "send parsed actions to the focused SWP 5.5 window"),
    ]:
        p = sub.add_parser(name, help=help_text)
        source = p.add_mutually_exclusive_group(required=True)
        source.add_argument("--expr", help="restricted LaTeX-like math expression")
        source.add_argument("--file", help="UTF-8 .swpmd file with $$ display-math blocks")
        if name == "write":
            p.add_argument("--yes", action="store_true", help="required acknowledgement for live input")
            p.add_argument("--pause", type=float, default=0.03, help="pause between actions in seconds")
        p.set_defaults(func=func)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ParseError, DriverError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
