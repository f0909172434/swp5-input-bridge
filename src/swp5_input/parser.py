from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, Kind, SUPPORTED_SWP_COMMANDS, is_supported_swp_command


class ParseError(ValueError):
    pass


_SIMPLE_TEX = {
    "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta", "eta",
    "theta", "vartheta", "iota", "kappa", "lambda", "mu", "nu", "xi", "pi",
    "rho", "sigma", "tau", "upsilon", "phi", "varphi", "chi", "psi", "omega",
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi",
    "Psi", "Omega", "infty", "to", "le", "leq", "ge", "geq", "neq", "pm", "times",
    "cdot", "partial", "sin", "cos", "tan", "cot", "sec", "csc", "log", "ln", "exp",
    "lim", "liminf", "limsup", "min", "max", "sup", "inf", "arccos", "arctan",
}

_DIRECTIVE_PREFIX = "[[swp:"
_DIRECTIVE_SUFFIX = "]]"


@dataclass
class MathParser:
    source: str
    pos: int = 0

    def parse(self) -> list[Action]:
        actions = self._parse_until(None)
        self._skip_spaces()
        if self.pos != len(self.source):
            raise ParseError(f"Unexpected input at position {self.pos}: {self.source[self.pos:self.pos+20]!r}")
        return actions

    def _parse_until(self, terminator: str | None) -> list[Action]:
        out: list[Action] = []
        raw: list[str] = []

        def flush() -> None:
            if raw:
                out.append(Action(Kind.TYPE, "".join(raw)))
                raw.clear()

        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if terminator is not None and ch == terminator:
                flush()
                self.pos += 1
                return out
            if ch.isspace():
                self.pos += 1
                continue
            if ch == "\\":
                flush()
                out.extend(self._parse_command())
                continue
            if ch == "_":
                flush()
                self.pos += 1
                out.append(Action(Kind.SUBSCRIPT))
                out.extend(self._parse_argument())
                out.append(Action(Kind.EXIT_TEMPLATE))
                continue
            if ch == "^":
                flush()
                self.pos += 1
                out.append(Action(Kind.SUPERSCRIPT))
                out.extend(self._parse_argument())
                out.append(Action(Kind.EXIT_TEMPLATE))
                continue
            if ch == "{":
                flush()
                self.pos += 1
                out.extend(self._parse_until("}"))
                continue
            if ch == "}":
                if terminator is None:
                    raise ParseError(f"Unmatched }} at position {self.pos}")
                break
            raw.append(ch)
            self.pos += 1

        flush()
        if terminator is not None:
            raise ParseError(f"Missing closing {terminator!r}")
        return out

    def _parse_argument(self) -> list[Action]:
        self._skip_spaces()
        if self.pos >= len(self.source):
            raise ParseError("Expected argument at end of expression")
        if self.source[self.pos] == "{":
            self.pos += 1
            return self._parse_until("}")
        if self.source[self.pos] == "\\":
            return self._parse_command()
        ch = self.source[self.pos]
        self.pos += 1
        return [Action(Kind.TYPE, ch)]

    def _parse_command(self) -> list[Action]:
        assert self.source[self.pos] == "\\"
        self.pos += 1
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos].isalpha():
            self.pos += 1
        name = self.source[start:self.pos]
        if not name:
            if self.pos >= len(self.source):
                raise ParseError("Trailing backslash")
            literal = self.source[self.pos]
            self.pos += 1
            if literal in {",", ";", "!", " "}:
                return []
            return [Action(Kind.TYPE, literal)]

        if name in {"quad", "qquad"}:
            return []

        if name in {"left", "right"}:
            self._skip_spaces()
            if self.pos >= len(self.source):
                raise ParseError(f"\\{name} requires a delimiter")
            if self.source[self.pos] == "\\":
                self.pos += 1
                start = self.pos
                while self.pos < len(self.source) and self.source[self.pos].isalpha():
                    self.pos += 1
                delim = self.source[start:self.pos]
                mapping = {"lbrace": "{", "rbrace": "}", "langle": "<", "rangle": ">"}
                if delim not in mapping:
                    raise ParseError(f"Unsupported delimiter \\{delim}")
                return [Action(Kind.TYPE, mapping[delim])]
            delim = self.source[self.pos]
            self.pos += 1
            return [Action(Kind.TYPE, delim)]

        if name == "frac":
            numerator = self._required_group("fraction numerator")
            denominator = self._required_group("fraction denominator")
            return [Action(Kind.FRACTION), *numerator, Action(Kind.NEXT_FIELD), *denominator, Action(Kind.EXIT_TEMPLATE)]

        if name == "sqrt":
            body = self._required_group("radical body")
            return [Action(Kind.RADICAL), *body, Action(Kind.EXIT_TEMPLATE)]

        if name == "int":
            return [Action(Kind.INTEGRAL)]

        if name in {"mathrm", "mathbf", "mathit"}:
            return self._required_group(f"{name} body")

        if name in _SIMPLE_TEX:
            return [Action(Kind.TEX, name)]

        raise ParseError(f"Unsupported command: \\{name}")

    def _required_group(self, label: str) -> list[Action]:
        self._skip_spaces()
        if self.pos >= len(self.source) or self.source[self.pos] != "{":
            raise ParseError(f"Expected {{{{...}}}} for {label}")
        self.pos += 1
        return self._parse_until("}")

    def _skip_spaces(self) -> None:
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            self.pos += 1


def parse_math(source: str) -> list[Action]:
    return MathParser(source).parse()


def parse_swp_command(command: str) -> Action:
    command = command.strip()
    if not is_supported_swp_command(command):
        supported = ", ".join(SUPPORTED_SWP_COMMANDS)
        raise ParseError(
            f"Unsupported SWP command {command!r}. Supported commands: {supported}, "
            "or plot:2d-rectangular-range:<xmin>:<xmax>"
        )
    return Action(Kind.SWP_COMMAND, command)


def _next_special(source: str, cursor: int) -> tuple[int, str] | None:
    math_pos = source.find("$", cursor)
    directive_pos = source.find(_DIRECTIVE_PREFIX, cursor)
    candidates = []
    if math_pos >= 0:
        candidates.append((math_pos, "math"))
    if directive_pos >= 0:
        candidates.append((directive_pos, "directive"))
    if not candidates:
        return None
    return min(candidates, key=lambda item: item[0])


def parse_document(source: str) -> list[Action]:
    """Parse plain text, native SWP math blocks, and semantic SWP directives.

    ``$ ... $`` marks inline mathematics and ``$$ ... $$`` marks display
    mathematics. A directive such as ``[[swp:plot:2d]]`` becomes an application
    command rather than document text. When a Compute or Plot directive follows
    a math block, the parser first moves the insertion point one position left,
    into the mathematical object. This follows SWP 5.5's documented automatic
    selection rule and is more reliable than leaving the caret outside a display.
    """
    out: list[Action] = []
    cursor = 0
    last_was_math_close = False

    while cursor < len(source):
        special = _next_special(source, cursor)
        if special is None:
            if cursor < len(source):
                out.append(Action(Kind.TEXT, source[cursor:]))
            break

        start, special_kind = special
        between = source[cursor:start]
        defer_whitespace = special_kind == "directive" and last_was_math_close and between != "" and between.strip() == ""
        if between and not defer_whitespace:
            out.append(Action(Kind.TEXT, between))
            last_was_math_close = False

        if special_kind == "directive":
            end = source.find(_DIRECTIVE_SUFFIX, start + len(_DIRECTIVE_PREFIX))
            if end < 0:
                raise ParseError("Unclosed [[swp:...]] directive")
            command = source[start + len(_DIRECTIVE_PREFIX):end].strip()
            if last_was_math_close and (command.startswith("compute:") or command.startswith("plot:")):
                out.append(Action(Kind.CURSOR_LEFT))
            out.append(parse_swp_command(command))
            if defer_whitespace:
                out.append(Action(Kind.TEXT, between))
            cursor = end + len(_DIRECTIVE_SUFFIX)
            last_was_math_close = False
            continue

        if source.startswith("$$", start):
            end = source.find("$$", start + 2)
            if end < 0:
                raise ParseError("Unclosed $$ display block")
            expr = source[start + 2:end].strip()
            out.append(Action(Kind.DISPLAY_START))
            out.extend(parse_math(expr))
            out.append(Action(Kind.DISPLAY_END))
            cursor = end + 2
            last_was_math_close = True
        else:
            end = source.find("$", start + 1)
            if end < 0:
                raise ParseError("Unclosed $ inline-math block")
            expr = source[start + 1:end].strip()
            out.append(Action(Kind.MATH_START))
            out.extend(parse_math(expr))
            out.append(Action(Kind.MATH_END))
            cursor = end + 1
            last_was_math_close = True

    return out
