# cvx-workflow-skills

Portable [Agent Skills](https://agentskills.io/) for building optimization models,
describing them, and implementing them through existing solvers. Use them with
Claude Code, Codex, OpenCode, or pi. Each assembled skill includes its own
instructions, references, examples, helpers, and license where applicable.

## Skills

| Skill | What it does |
|---|---|
| [cvx-model](skills/cvx-model/SKILL.md) | Turns natural-language requirements into reusable, efficient CVXPY code for real continuous convex LP, QP, and SOCP problems. |
| [cvx-explain](skills/cvx-explain/SKILL.md) | Reads CVXPY code and produces a Markdown/LaTeX description of its variables, parameters, fixed data, objective, and constraints. |
| [cvx-canon](skills/cvx-canon/SKILL.md) | Generates Moreau, SCS, HiGHS, or IPOPT implementations, including assembly, parameter updates, and original-variable recovery. Supports focused convex relaxations and convex-concave procedures. |

`cvx-model` keeps its modeling scope focused for use with smaller models.
`cvx-canon` is intended for more capable models: it accounts for software
framework, hardware, precision, batching, and differentiation requirements.
Moreau IPM is its default convex conic backend, including PyTorch/JAX paths;
IPOPT supports CasADi, Pyomo, and native callbacks for local nonlinear optimization.

## Build the distribution

The repository's build tools require Python 3.14 and
[uv](https://docs.astral.sh/uv/getting-started/installation/). From a clone:

```bash
git clone https://github.com/cvxgrp/cvx-workflow-skills.git
cd cvx-workflow-skills
uv sync --locked
uv run --no-sync python -B -m tests.build_release
uv run --no-sync python -B -m tests.validate_release artifacts/release
```

The assembled distribution is in `artifacts/release/`. It contains standalone
skill folders, a Claude Code plugin manifest, and a pi package manifest.
`release.json` selects the shipped files; generated artifacts are ignored by Git.

## Install and use

Install from the assembled distribution, preserving each skill's complete folder
and bundled license. These options load skills for a project or session:

| Harness | Setup | Documentation |
|---|---|---|
| Claude Code | Run `claude --plugin-dir /absolute/path/to/artifacts/release`, or copy selected folders from `artifacts/release/skills/` into your project's `.claude/skills/`. | [Plugins](https://code.claude.com/docs/en/plugins), [skills](https://code.claude.com/docs/en/skills) |
| Codex | Copy selected folders from `artifacts/release/skills/` into your project's `.agents/skills/`. | [Skills](https://learn.chatgpt.com/docs/build-skills) |
| OpenCode | Copy selected folders into your project's `.agents/skills/` or `.opencode/skills/`. | [Skills](https://opencode.ai/docs/skills/) |
| pi | Run `pi -e /absolute/path/to/artifacts/release`. | [Packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md) |

For example, ask your agent:

- **cvx-model:** “Write a reusable CVXPY model minimizing squared distance from
  a supplied vector, subject to a Euclidean norm bound. Make the vector and radius
  parameters.”
- **cvx-explain:** “Describe this CVXPY model in Markdown, distinguishing decision
  variables, parameters, and fixed data.”
- **cvx-canon:** “Implement this optimization problem using Moreau in PyTorch,
  on CPU with float64 data, batching, and gradients through the solution.”

The build does not install modeling or solver packages. Running generated code
requires the packages used by that application, such as CVXPY, a selected solver,
or a framework integration. Each skill documents relevant requirements.

## Development and contributions

Run the lightweight skill-format check with:

```bash
uv run --no-sync python -B -m tests
```

It checks metadata, skill/folder names, and instruction bodies. Release validation
also checks bundled resources and manifests. Numerical and live model evaluations
are separate activities; these checks do not establish solution correctness or
performance. The skills are under active development, and generated models should
be checked against their original requirements.

Report bugs and suggestions through
[GitHub issues](https://github.com/cvxgrp/cvx-workflow-skills/issues).
Contributions use forks and pull requests; see [CONTRIBUTING.md](CONTRIBUTING.md)
for setup, checks, and resources for first-time contributors.

## License

[Apache-2.0](LICENSE).
