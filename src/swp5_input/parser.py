from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, Kind


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


def parse_document(source: str) -> list[Action]:
    """Parse plain text with native SWP inline and display math blocks.

    ``$ ... $`` marks inline mathematics and ``$$ ... $$`` marks display
    mathematics. Markdown is otherwise intentionally not implemented. Text
    outside math blocks is preserved exactly.
    """
    out: list[Action] = []
    cursor = 0
    while cursor < len(source):
        start = source.find("$", cursor)
        if start < 0:
            if cursor < len(source):
                out.append(Action(Kind.TEXT, source[cursor:]))
            break
        if start > cursor:
            out.append(Action(Kind.TEXT, source[cursor:start]))

        if source.startswith("$$", start):
            end = source.find("$$", start + 2)
            if end < 0:
                raise ParseError("Unclosed $$ display block")
            expr = source[start + 2:end].strip()
            out.append(Action(Kind.DISPLAY_START))
            out.extend(parse_math(expr))
            out.append(Action(Kind.DISPLAY_END))
            cursor = end + 2
        else:
            end = source.find("$", start + 1)
            if end < 0:
                raise ParseError("Unclosed $ inline-math block")
            expr = source[start + 1:end].strip()
            out.append(Action(Kind.MATH_START))
            out.extend(parse_math(expr))
            out.append(Action(Kind.MATH_END))
            cursor = end + 1
    return out
