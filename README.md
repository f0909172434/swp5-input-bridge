# swp5-input-bridge

`swp5-input-bridge` is a conservative Windows automation bridge for **Scientific WorkPlace 5.5**. It enters structured mathematics as native SWP objects and can invoke selected SWP Compute, Plot, and Typeset commands through the real application UI.

It exists because pasting LaTeX-like text into SWP 5.5 produces literal source such as `\frac` and `\rho`. The bridge parses a restricted notation and replays the equivalent SWP 5.5 actions instead of editing the generated `.tex` file behind SWP's back.

## Status

Experimental live driver. Parser and dry-run planning are testable on Python 3.10 and 3.12. Live entry and application commands require Windows and SWP 5.5.

The project does **not** save, close, overwrite, or rename SWP files. File management remains manual so a failed automation run cannot destroy the working document.

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

Open SWP 5.5 and exactly one target document, then:

```powershell
swp5-input doctor
swp5-input plan --expr "\lim_{\rho\to0^+}\Lambda_\rho(m_\rho)=0"
swp5-input write --expr "\lim_{\rho\to0^+}\Lambda_\rho(m_\rho)=0" --yes
```

`write` refuses to run without `--yes`.

## Document input

A `.swpmd` file is plain UTF-8 text. Use `$ ... $` for inline mathematics and `$$ ... $$` for display mathematics.

```text
Lemma. Assume that $f(0)>0$. Then

$$
\lim_{\rho\to0^+}\Lambda_\rho(m_\rho)=0
$$
```

Preview and write it with:

```powershell
swp5-input plan --file examples/basic.swpmd
swp5-input write --file examples/basic.swpmd --yes
```

## SWP application directives

A standalone directive line is not typed into the document. It becomes a semantic SWP application action. When a Compute or Plot directive immediately follows a math block, the bridge moves the caret one position left into the mathematical object before invoking the command. This follows SWP 5.5's automatic-selection behavior and avoids the failure mode where the caret sits outside a display.

```text
$$
0.860333589\tan(0.860333589)
$$
[[swp:compute:evaluate-numerically]]

$$
x\tan x
$$
[[swp:plot:2d]]
```

Supported directives:

- `[[swp:compute:evaluate]]`
- `[[swp:compute:evaluate-numerically]]`
- `[[swp:compute:simplify]]`
- `[[swp:compute:solve-exact]]`
- `[[swp:plot:2d]]`
- `[[swp:plot:3d]]`
- `[[swp:typeset:compile-pdf]]`
- `[[swp:typeset:preview-pdf]]`

For 2D plotting the driver first invokes the native menu path `Compute -> Plot 2D -> Rectangular`, with spelling fallbacks for installations that expose `Plot2D` as one word.

## Native Compute/Plot smoke test

Before generating a long document, a short live smoke test is available:

```powershell
py -m swp5_input.cli write --file examples/swp-native-compute-plot-smoke.swpmd --yes
```

The expected visible behavior in SWP is:

1. `2+3` receives a native computed result
2. the numerical trigonometric expression receives a native numerical result
3. `x tan x` is followed by an SWP-generated rectangular 2D plot

If the source expressions appear but the result or plot does not, the native SWP command path has not executed successfully and the full report should not be generated yet.

## HW-2 progress report

`examples/hw2-progress-report.swpmd` is a self-contained local bifurcation progress report. It contains the problem and branch formulation, the three-case left-end theorem and proofs, a native SWP numerical computation, and a native SWP rectangular 2D plot.

After the native smoke test succeeds, open a blank SWP document and run:

```powershell
py -m swp5_input.cli write --file examples/hw2-progress-report.swpmd --yes
```

Save the document manually. To compile it afterwards:

```powershell
py -m swp5_input.cli command typeset:compile-pdf --yes
```

## Supported math

- ordinary letters, digits, punctuation, parentheses, relations
- inline and display mathematics
- subscripts and superscripts: `_`, `^`
- common TeX-named Greek symbols, including capital Greek letters
- `\lim`, `\liminf`, `\limsup`, `\infty`, `\to`
- `\frac{...}{...}`
- `\sqrt{...}`
- `\int` with subscript/superscript limits
- common names such as `\sin`, `\cos`, `\tan`, `\sec`, `\log`, `\exp`
- `\left` / `\right` delimiters in the supported basic forms
- spacing commands `\quad` and `\qquad`

Unknown math commands and unknown `[[swp:...]]` directives fail closed instead of being typed into SWP.

## Safety model

- live automation works only on Windows
- exactly one visible window matching `Scientific WorkPlace` must exist
- the driver focuses that window before input
- if SWP loses focus, the driver aborts
- `plan` never touches SWP
- `write` and `command` require explicit `--yes`
- Compute/Plot/Typeset use semantic menu paths, not absolute screen coordinates
- save/close/file-overwrite automation remains intentionally disabled

## Current limitation

Plot creation is automated, but Plot Properties such as exact axis range and labels are not yet controlled because SWP 5.5 exposes those settings through a separate Plot Properties dialog. That dialog should be automated only after one control-tree smoke test on the actual Windows installation; the bridge does not guess screen coordinates.
