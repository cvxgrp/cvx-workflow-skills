# Notation and portable math

Write descriptions in the notation of *Convex Optimization* (Boyd and
Vandenberghe), spelled so it renders without a custom preamble. The same source
compiles in an ordinary LaTeX document.

## Standard form

```latex
$$
\begin{array}{ll}
\text{minimize} & p^T(u+c) \\
\text{subject to} & -D\mathbf{1} \preceq c \preceq C\mathbf{1}, \quad
u + c \succeq 0 \\
& q_{t+1} = q_t + c_t, \quad t = 1, \ldots, T-1
\end{array}
$$

with variables $c, q \in \mathbf{R}^T$.
```

- Use `\begin{array}{ll}` with `\text{minimize}`/`\text{maximize}` and
  `\text{subject to}` in the left column. Continuation lines leave it empty.
- Follow the display with a sentence naming the decision variables and their
  domains. Name parameters and fixed data separately, as the description requires.
- Use `\preceq`/`\succeq` for componentwise vector inequalities and for the
  semidefinite order on symmetric matrices; use `\leq`/`\geq` for scalars. On
  matrices, entrywise and semidefinite inequalities are different constraints:
  write entrywise ones with indices or say "elementwise" explicitly.
- Spell out index ranges (`i = 1, \ldots, m`). Short related constraints may
  share a line, separated by `\quad`.

## Portable macros

Markdown renderers load no document preamble, so shorthand macros from the book
or a paper (`\ones`, `\reals`, `\Tr`, ...) are undefined there. KaTeX also lacks
`\mbox`. Write the expanded forms:

| Macro | Write instead | Macro | Write instead |
|---|---|---|---|
| `\mbox{...}` | `\text{...}` | `\Expect` | `\mathop{\mathbf{E}}` |
| `\ones` / `\zeros` | `\mathbf{1}` / `\mathbf{0}` | `\Prob` | `\mathop{\mathbf{prob}}` |
| `\reals` | `\mathbf{R}` | `\var` / `\cov` | `\mathop{\mathbf{var}}` / `\mathop{\mathbf{cov}}` |
| `\integers` / `\complex` | `\mathbf{Z}` / `\mathbf{C}` | `\diag` | `\mathop{\mathbf{diag}}` |
| `\symm` | `\mathbf{S}` | `\Tr` | `\mathop{\mathbf{tr}}` |
| `\lambdamax` / `\lambdamin` | `\lambda_{\max}` / `\lambda_{\min}` | `\Rank` | `\mathop{\mathbf{rank}}` |
| `\argmin` / `\argmax` | `\mathop{\mathrm{argmin}}` / `\mathop{\mathrm{argmax}}` | `\dom` | `\mathop{\mathbf{dom}}` |
| `\geqK` / `\leqK` | `\succeq_K` / `\preceq_K` | `\Co` | `\mathop{\mathbf{conv}}` |

`check_latex.py --table` prints the complete mapping. Do not use `eqnarray`,
`equation`, `displaymath`, or shorthands such as `\BEQ`/`\BEAS`; use `$$ ... $$`
with an `array` inside.

`\reals`, `\argmin`, and `\argmax` fail silently under KaTeX: KaTeX defines
them itself, so they render without an error but not in the book's notation
(`\reals` gives a blackboard-bold ℝ). Use the replacements above.

## marimo notebooks

This section applies only when the description goes into a marimo notebook.

marimo renders math with KaTeX and an empty macro table, with errors reported
as small red text rather than an exception. Put math in an `mo.md` cell using a
raw string:

```python
mo.md(r"""... \text{minimize} ... \\ ...""")   # correct
mo.md("""... \text{minimize} ... \\ ...""")    # broken
```

Without the `r` prefix, Python consumes escapes before KaTeX sees them: `\t`
becomes a tab, so `\text` breaks, and `\\` collapses to `\`, removing every
array line break. Leave existing cells unchanged unless asked to edit them.

## Standalone LaTeX

The portable spelling compiles unchanged. When the target document already
defines the book macros and matching its source matters, reverse the table
(`\mathbf{1}` to `\ones`, `\text{minimize}` to `\mbox{minimize}`) and use
`\[ ... \]` for displays. The checker below targets preamble-free rendering and
will flag those macros; do not run it on such a document.

## Optional check

The bundled [math checker](../scripts/check_latex.py) extracts `$...$`,
`$$...$$`, and `\[...\]` math from Markdown, `.tex`, or Python files and reports
`file:line` with the replacement:

    python /absolute/skill/path/scripts/check_latex.py description.md

It always runs a static scan for the macros and environments above. It also
renders each snippet with KaTeX when `node` and a KaTeX ES-module bundle are
available: pass `--katex /path/to/katex.mjs`, or it uses the bundle shipped
with an installed marimo. For a marimo notebook, it additionally flags `mo.md`
strings with backslashes that lack an `r` prefix. Exit 0 means no problems were
found by the engine reported in its output, 1 means problems, 2 means a
missing file. A pass does not check that the math describes the code correctly.
