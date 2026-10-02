# cvx-workflow-skills

Portable Agent Skills for convex optimization, targeting Claude Code, Codex,
OpenCode, and pi. Apache-2.0; currently private development.

| Skill | Scope |
|---|---|
| [cvx-model](skills/cvx-model/SKILL.md) | Natural-language requirements → efficient CVXPY code for real continuous convex LP/QP/SOCP models |
| [cvx-explain](skills/cvx-explain/SKILL.md) | Supplied CVXPY code → Markdown/LaTeX describing variables, parameters, fixed data, objective, and constraints |
| cvx-canon | Planned next: direct solver-native assembly, updates, and primal recovery |
| cvx-solver | Deferred until the other skills are satisfactory |

Each distributed skill is self-contained. `cvx-model` prioritizes reusable code
and includes optional construction and original-expression checks. Standalone
proofs, dual analysis, and performance consultations are outside its scope.
`cvx-explain` describes supplied code without changing the model or inventing
application meanings.

## Develop and test

The small [validation package](tests/README.md) checks skill-file format.
Python 3.14 and [uv](https://docs.astral.sh/uv/) are required:

```bash
uv sync --locked
uv run --no-sync python -B -m tests
```

The second command checks required metadata, skill/folder name agreement, and
instruction bodies. It does not execute skill code or call models. Release
assembly is a separate optional command documented in `tests/README.md`;
`release.json` selects the shipping resources. Generated output belongs under
ignored `artifacts/`.

## Use an assembled skill

| Harness | Project/session-local mechanism |
|---|---|
| Claude Code | `claude --plugin-dir /absolute/path/to/artifacts/release` |
| Codex | Copy an assembled skill into project `.agents/skills/<name>/` |
| OpenCode | Copy into project `.agents/skills/<name>/` or `.opencode/skills/<name>/` |
| pi | `pi -e /absolute/path/to/artifacts/release` |

Copy from `artifacts/release/skills/`, including each skill's bundled license.
Ask cvx-model to build a model from your requirements; supply CVXPY code to
cvx-explain and ask for its mathematical description.

## Evidence

Previous local evaluations covered helpers, recipes, reference models, and
grading. A gpt-6-luna application batch accepted 12/12 first
attempts across 36 numerical instances; this small batch had no baseline or
repeats and does not establish a general success rate. cvx-explain has offline
checks only. Native loading was observed for Claude Code, Codex, and pi;
OpenCode remains untested. The historical evaluation suite is retained locally;
the shared checker validates format only.
