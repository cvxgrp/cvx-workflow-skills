#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check that math in Markdown, .tex, or Python files renders without a preamble.

Markdown renderers load no document preamble, so book macros (\\ones, \\Tr,
\\symm, ...) are undefined there, and KaTeX also lacks \\mbox. Under KaTeX these
fail as inline red error text rather than an exception, so they are easy to miss.

A static scan always runs. When node and a KaTeX ES-module bundle are available
(--katex PATH, or the bundle shipped with an installed marimo), each snippet is
also rendered with KaTeX. For marimo notebooks, mo.md strings containing
backslashes without an r prefix are flagged.

Usage:
    check_latex.py FILE [FILE ...]
    check_latex.py --text '\\ones^T x'
    check_latex.py --table

Exit status: 0 no problems found, 1 problems found, 2 missing file.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Book macro -> preamble-free replacement.
MACRO_MAP = {
    r"\zeros": r"\mathbf{0}",
    r"\ones": r"\mathbf{1}",
    r"\reals": r"\mathbf{R}",
    r"\integers": r"\mathbf{Z}",
    r"\complex": r"\mathbf{C}",
    r"\symm": r"\mathbf{S}",
    r"\Span": r"\mathop{\mathrm{span}}",
    r"\range": r"\mathcal{R}",
    r"\nullspace": r"\mathcal{N}",
    r"\Rank": r"\mathop{\mathbf{rank}}",
    r"\Tr": r"\mathop{\mathbf{tr}}",
    r"\cond": r"\mathop{\mathbf{cond}}",
    r"\diag": r"\mathop{\mathbf{diag}}",
    r"\lambdamax": r"\lambda_{\max}",
    r"\lambdamin": r"\lambda_{\min}",
    r"\Prob": r"\mathop{\mathbf{prob}}",
    r"\Expect": r"\mathop{\mathbf{E}}",
    r"\var": r"\mathop{\mathbf{var}}",
    r"\cov": r"\mathop{\mathbf{cov}}",
    r"\Co": r"\mathop{\mathbf{conv}}",
    r"\argmin": r"\mathop{\mathrm{argmin}}",
    r"\argmax": r"\mathop{\mathrm{argmax}}",
    r"\epi": r"\mathop{\mathbf{epi}}",
    r"\dist": r"\mathop{\mathbf{dist}}",
    r"\vol": r"\mathop{\mathbf{vol}}",
    r"\Card": r"\mathop{\mathbf{card}}",
    r"\sign": r"\mathop{\mathbf{sign}}",
    r"\dom": r"\mathop{\mathbf{dom}}",
    r"\aff": r"\mathop{\mathbf{aff}}",
    r"\cl": r"\mathop{\mathbf{cl}}",
    r"\intr": r"\mathop{\mathbf{int}}",
    r"\relint": r"\mathop{\mathbf{rel\,int}}",
    r"\bd": r"\mathop{\mathbf{bd}}",
    r"\ourinf": r"\inf",
    r"\oursup": r"\sup",
    r"\geqK": r"\succeq_K",
    r"\gK": r"\succ_K",
    r"\leqK": r"\preceq_K",
    r"\lK": r"\prec_K",
    r"\geqKst": r"\succeq_{K^*}",
    r"\gKst": r"\succ_{K^*}",
    r"\leqKst": r"\preceq_{K^*}",
    r"\lKst": r"\prec_{K^*}",
    r"\geqL": r"\succeq_L",
    r"\gL": r"\succ_L",
    r"\leqL": r"\preceq_L",
    r"\lL": r"\prec_L",
    r"\mbox": r"\text",
    r"\eg": r"\text{e.g.}",
    r"\ie": r"\text{i.e.}",
    r"\BEAS": r"use $$\begin{array}{ll} ... \end{array}$$",
    r"\EEAS": r"use $$\begin{array}{ll} ... \end{array}$$",
    r"\BEA": r"use $$\begin{array}{ll} ... \end{array}$$",
    r"\EEA": r"use $$\begin{array}{ll} ... \end{array}$$",
    r"\BEQ": r"use $$ ... $$",
    r"\EEQ": r"use $$ ... $$",
}

# KaTeX defines these itself: they render without error, not in book notation.
SILENT = {r"\reals", r"\argmin", r"\argmax"}

BAD_ENVIRONMENTS = {
    "eqnarray": r"use \begin{array}{ll}",
    "eqnarray*": r"use \begin{array}{ll}",
    "equation": "use $$ ... $$",
    "displaymath": "use $$ ... $$",
    "center": "not a math environment; drop it",
}

MATH_PATTERNS = [
    re.compile(r"\$\$(.+?)\$\$", re.S),
    re.compile(r"\\\[(.+?)\\\]", re.S),
    re.compile(r"(?<!\$)\$([^$\n]+?)\$(?!\$)"),
]

# marimo-specific: an mo.md string literal and its prefix.
MO_MD = re.compile(r"""mo\.md\(\s*([rRbBuUfF]*)("{3}|'{3}|"|')""")


def find_katex(explicit: Path | None) -> Path | None:
    """Return a KaTeX ES-module bundle: explicit path, else marimo's (if installed)."""
    if explicit is not None:
        return explicit if explicit.is_file() else None
    try:
        import marimo

        assets = Path(marimo.__file__).parent / "_static" / "assets"
        for candidate in sorted(assets.glob("katex*.js")):
            return candidate
    except Exception:
        pass
    return None


def katex_check(snippets: list[str], bundle: Path | None) -> list[str | None] | None:
    """Render each snippet with KaTeX; None overall when KaTeX is unavailable."""
    if bundle is None or not shutil.which("node"):
        return None
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # node loads a bundle as an ES module only with the .mjs extension.
        shutil.copy(bundle, tmp / "katex.mjs")
        (tmp / "run.mjs").write_text(
            "import * as mod from './katex.mjs';\n"
            "const katex = mod.renderToString ? mod : mod.default;\n"
            "const items = JSON.parse(process.argv[2]);\n"
            "const out = items.map(s => {\n"
            "  try {\n"
            "    katex.renderToString(s, {displayMode: true, throwOnError: true, macros: {}});\n"
            "    return null;\n"
            "  } catch (e) { return e.message; }\n"
            "});\n"
            "process.stdout.write(JSON.stringify(out));\n"
        )
        try:
            res = subprocess.run(
                ["node", str(tmp / "run.mjs"), json.dumps(snippets)],
                capture_output=True, text=True, timeout=60,
            )
            return json.loads(res.stdout) if res.returncode == 0 else None
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            return None


def extract_math(text: str) -> list[tuple[int, str]]:
    """Return (line, snippet) for display and inline math in any text file."""
    found, spans = [], []
    for pattern in MATH_PATTERNS:
        for m in pattern.finditer(text):
            if any(s <= m.start() < e for s, e in spans):
                continue
            spans.append((m.start(), m.end()))
            found.append((text.count("\n", 0, m.start()) + 1, m.group(1)))
    return sorted(found)


def static_check(snippet: str) -> list[str]:
    """Find book macros and unsupported environments without rendering."""
    problems = []
    for macro in sorted(MACRO_MAP, key=len, reverse=True):
        # Require a non-letter boundary so \var does not match \varepsilon.
        if re.search(re.escape(macro) + r"(?![A-Za-z])", snippet):
            note = " (renders under KaTeX, but not in book notation)" if macro in SILENT else ""
            problems.append(f"{macro} -> {MACRO_MAP[macro]}{note}")
    for env, fix in BAD_ENVIRONMENTS.items():
        if re.search(r"\\begin\{" + re.escape(env) + r"\}", snippet):
            problems.append(rf"\begin{{{env}}} unsupported -> {fix}")
    return problems


def marimo_raw_string_check(text: str) -> list[tuple[int, str]]:
    """marimo-specific: flag mo.md strings with backslashes but no r prefix."""
    if "marimo.App(" not in text:
        return []
    problems = []
    for m in MO_MD.finditer(text):
        prefix, quote = m.group(1), m.group(2)
        end = text.find(quote, m.end())
        body = text[m.end():end if end >= 0 else len(text)]
        if "r" not in prefix.lower() and "\\" in body:
            line = text.count("\n", 0, m.start()) + 1
            problems.append((line, "mo.md string has backslashes but no r prefix -> use r\"\"\"...\"\"\""))
    return problems


def check_file(path: Path, bundle: Path | None) -> tuple[list[str], bool]:
    """Return (messages, whether KaTeX rendering ran) for one file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    messages = [f"{path}:{line}: {issue}" for line, issue in marimo_raw_string_check(text)]
    blocks = extract_math(text)
    if not blocks:
        return messages, False
    rendered = katex_check([snippet for _, snippet in blocks], bundle)
    for i, (line, snippet) in enumerate(blocks):
        issues = static_check(snippet)
        if rendered is not None and rendered[i] and not issues:
            issues.append(f"KaTeX: {rendered[i].splitlines()[0][:120]}")
        messages.extend(f"{path}:{line}: {issue}" for issue in issues)
    return messages, rendered is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--text", help="check one snippet instead of files")
    parser.add_argument("--table", action="store_true", help="print the macro mapping")
    parser.add_argument("--katex", type=Path, help="KaTeX ES-module bundle (e.g. katex/dist/katex.mjs)")
    args = parser.parse_args()

    if args.table:
        print(f"{'macro':<14} {'write instead':<34} note")
        for macro, replacement in MACRO_MAP.items():
            note = "renders under KaTeX, not book notation" if macro in SILENT else ""
            print(f"{macro:<14} {replacement:<34} {note}")
        return 0

    if args.katex is not None and not args.katex.is_file():
        print(f"{args.katex}: no such KaTeX bundle", file=sys.stderr)
        return 2
    bundle = find_katex(args.katex)

    if args.text:
        issues = static_check(args.text)
        rendered = katex_check([args.text], bundle)
        if rendered is not None and rendered[0] and not issues:
            issues.append(f"KaTeX: {rendered[0].splitlines()[0][:120]}")
        engine = "KaTeX render and static scan" if rendered is not None else "static scan only"
        for issue in issues:
            print(issue)
        print(f"({engine})")
        return 1 if issues else 0

    if not args.files:
        parser.error("pass files, --text, or --table")

    messages, any_rendered = [], False
    for path in args.files:
        if not path.is_file():
            print(f"{path}: no such file", file=sys.stderr)
            return 2
        file_messages, rendered = check_file(path, bundle)
        messages.extend(file_messages)
        any_rendered = any_rendered or rendered
    engine = "KaTeX render and static scan" if any_rendered else "static scan only"
    if messages:
        print(f"Math problems ({engine}):")
        for message in messages:
            print("  " + message)
        return 1
    print(f"No math problems found ({engine}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
