# swp5-input-bridge

`swp5-input-bridge` is a conservative Windows automation bridge for **Scientific WorkPlace 5.5**. It enters structured mathematics as native SWP objects and can now invoke selected SWP Compute, Plot, and Typeset commands through the real application UI.

It exists because pasting LaTeX-like text into SWP 5.5 produces literal source such as `\frac` and `\rho`. The bridge parses a restricted notation and replays the equivalent SWP 5.5 actions instead of editing the generated `.tex` file behind SWP's back.

## Status

Experimental live driver. Parser and dry-run planning are testable on Python 3.10 and 3.12. Live entry and application commands require Windows, SWP 5.5, and an English-menu installation for the current Compute/Plot/Typeset menu paths.

The project still does **not** save, close, overwrite, or rename SWP files. File management remains manual so a failed automation run cannot destroy the working document.

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
\lim_{\rho\to0^+}\Lambda_\rho(m_\rho)=0.
$$
```

Preview and write it with:

```powershell
swp5-input plan --file examples/basic.swpmd
swp5-input write --file examples/basic.swpmd --yes
```

## SWP application directives

A standalone directive line is not typed into the document. It is converted into a semantic application action. When it immediately follows a math block, whitespace is delayed until after the action so the SWP insertion point is still to the right of the expression when Compute or Plot is invoked.

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

The same application actions can be invoked directly. For example, after manually saving the current SWP document:

```powershell
swp5-input command typeset:compile-pdf --yes
```

MacKichan's SWP 5.5 documentation describes the same UI workflow: place the insertion point to the right of an expression, then use Compute > Evaluate / Evaluate Numerically / Plot 2D / Plot3D. The driver uses `pywinauto` menu selection rather than screen coordinates.

## HW-2 progress report

`examples/hw2-progress-report.swpmd` is a self-contained local bifurcation progress report. It includes the problem and branch formulation, the three-case left-end theorem and proofs, a numerical SWP computation, and a live 2D plot action.

After pulling the latest repository and opening a blank SWP document:

```powershell
py -m swp5_input.cli plan --file examples/hw2-progress-report.swpmd
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
