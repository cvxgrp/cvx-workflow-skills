# cvx-workflow-skills

Portable Agent Skills for convex optimization, targeting Claude Code, Codex,
OpenCode, and pi. Apache-2.0; currently private development.

| Skill | Scope |
|---|---|
| [cvx-model](skills/cvx-model/SKILL.md) | Natural-language requirements → efficient CVXPY code for real continuous convex LP/QP/SOCP models |
| [cvx-explain](skills/cvx-explain/SKILL.md) | Supplied CVXPY code → Markdown/LaTeX describing variables, parameters, fixed data, objective, and constraints |
| [cvx-canon](skills/cvx-canon/SKILL.md) | Solver-native Moreau/SCS/HiGHS/IPOPT code, updates, and primal recovery; focused CCP and convex relaxations |
| cvx-solver | Deferred until the other skills are satisfactory |

Each distributed skill is self-contained. `cvx-model` prioritizes reusable code
and includes optional construction and original-expression checks. Standalone
proofs, dual analysis, and performance consultations are outside its scope.
`cvx-explain` describes supplied code without changing the model or inventing
application meanings.

`cvx-canon` targets more capable models and defaults to Moreau IPM for convex
conic problems, including CPU/CUDA and PyTorch/JAX deployment requirements.
It includes SCS, HiGHS MILP, and IPOPT through CasADi, Pyomo, or native callbacks,
with explicit distinctions between exact formulations, relaxations, and local
solution guarantees. Native applications do not depend on CVXPY at runtime.
Backend references and worked examples are bundled in the skill; solver packages
are application dependencies, not requirements for the repository's format check.

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
Ask cvx-canon for a native implementation from requirements, a formulation, or
CVXPY code, specifying a backend, software framework, hardware, and batching or
differentiation requirement when relevant.

## Evidence

Previous local evaluations covered helpers, recipes, reference models, and
grading. A gpt-6-luna application batch accepted 12/12 first
attempts across 36 numerical instances; this small batch had no baseline or
repeats and does not establish a general success rate. cvx-explain has offline
checks only. Native loading was observed for Claude Code, Codex, and pi;
OpenCode remains untested. cvx-canon is experimental: local checks cover Moreau
CPU/SCS conic assembly, recovery, reuse, and CCP; HiGHS MILP; IPOPT derivatives;
Moreau CPU PyTorch/JAX batch gradients; and CasADi/IPOPT native solves. Pyomo
construction, parameter updates, and NL writing are checked; its native IPOPT
executable is unavailable locally. A previous cvx-canon version passed 10/10 fresh
gpt-6.1-sol rubric cases (99/100); the framework additions have local checks only.
GPU paths and specialized SCS builds remain untested. These small checks and
batches are development evidence, not broad qualification.
The historical evaluation suite is retained locally;
the shared checker validates format only.
