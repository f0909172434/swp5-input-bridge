# swp5-input-bridge

`swp5-input-bridge` is a small, keyboard-first Windows automation bridge for entering structured mathematics into **Scientific WorkPlace 5.5** as native SWP math objects.

It exists for one narrow problem: pasting LaTeX-like text into SWP 5.5 produces literal source such as `\frac` and `\rho`. This bridge parses a conservative subset of LaTeX-like notation and replays the equivalent SWP 5.5 keyboard actions instead.

## Status

**v0.1 MVP / experimental live driver.** The parser and dry-run planner are testable anywhere. Live entry requires Windows, SWP 5.5, and a one-time smoke test on the target installation.

The project deliberately does **not** save, close, overwrite, or manage SWP files. It only sends input to an already-open SWP document.

## Install

On Windows with Python 3.10+:

```powershell
pipx install git+https://github.com/f0909172434/swp5-input-bridge.git
```

For development:

```powershell
git clone https://github.com/f0909172434/swp5-input-bridge.git
cd swp5-input-bridge
python -m pip install -e ".[dev]"
pytest
```

## First use

Open SWP 5.5 and a disposable blank document, then:

```powershell
swp5-input doctor
swp5-input plan --expr "\lim_{\rho\to0^+}K_\rho(m_\rho)=0"
```

If the plan looks correct, test live input in the disposable document:

```powershell
swp5-input write --expr "\lim_{\rho\to0^+}K_\rho(m_\rho)=0" --yes
```

`write` refuses to run without `--yes`.

## Document input

A `.swpmd` file is plain UTF-8 text. Only `$$ ... $$` is special; it marks a display-math block.

```text
Lemma. Assume that

$$
\lim_{\rho\to0^+}K_\rho(m_\rho)=0.
$$

The proof is complete.
```

Preview it:

```powershell
swp5-input plan --file examples/basic.swpmd
```

Then, after placing the cursor in SWP:

```powershell
swp5-input write --file examples/basic.swpmd --yes
```

## Supported math in v0.1

- ordinary letters, digits, punctuation, parentheses, relations
- subscripts and superscripts: `_`, `^`
- common TeX-named Greek symbols: `\rho`, `\lambda`, `\alpha`, ...
- `\lim`, `\liminf`, `\limsup`, `\infty`, `\to`
- `\frac{...}{...}`
- `\sqrt{...}`
- `\int` with subscript/superscript limits
- common names such as `\sin`, `\cos`, `\tan`, `\log`, `\exp`
- `\left` / `\right` delimiters (basic form)

Unknown commands fail closed with a parser error rather than being typed into SWP.

## Safety model

- live automation works only on Windows
- exactly one visible window matching `Scientific WorkPlace` must exist
- the driver focuses that window before input
- if SWP loses focus, the driver aborts
- `plan` never touches SWP
- `write` requires explicit `--yes`
- no save/close/file-overwrite automation exists in v0.1

## SWP 5.5 keyboard strategy

The bridge uses documented v5.5 shortcuts such as `Ctrl+M` for mathematics, `Ctrl+D` for a display, `Ctrl+F` for a fraction, `Ctrl+H` / `Ctrl+L` for super/subscripts, and `Ctrl+I` for an integral. TeX-named symbols are entered by holding `Ctrl` while typing the symbol name.

See [docs/swp55-shortcuts.md](docs/swp55-shortcuts.md) and [docs/windows-smoke-test.md](docs/windows-smoke-test.md).

## Non-goals for v0.1

Matrices, cases, aligned multi-line displays, equation numbering, automatic saving, visual computer-use fallback, and arbitrary LaTeX are intentionally out of scope until the basic SWP 5.5 path is validated on a real installation.
