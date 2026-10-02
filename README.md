# cvx-workflow-skills

Portable Agent Skills for convex optimization, targeting Claude Code, Codex,
OpenCode, and pi. Apache-2.0; currently private development.

| Skill | Status / deliverable |
|---|---|
| [`cvx-model`](skills/cvx-model/SKILL.md) | Experimental: natural-language requirements → efficient CVXPY code for real continuous convex LP/QP/SOCP models |
| [`cvx-explain`](skills/cvx-explain/SKILL.md) | Brief companion: supplied CVXPY code → Markdown/LaTeX describing variables, parameters, fixed data, objective, and constraints |
| `cvx-canon` | Second priority, not implemented: direct solver-native assembly, updates, and primal recovery; duals only when requested |
| `cvx-solver` | Explicitly deferred until the other two skills are satisfactory |

`cvx-model` prioritizes reusable Python code, with conditional recipes, CVXPY/DPP
guidance, and optional construction and original-expression checkers. The small
construction checker needs only `build(data)` and reports DCP/DPP, shapes,
exposed atom approximation errors, and exceptions without solving. Point mode
checks stated examples without solving. See [helper usage and limits](skills/cvx-model/references/verification.md).
`cvx-explain` describes code as written without inventing application meanings
or changing the model. Each skill works independently. Standalone proofs, dual
analysis, and performance consultations are outside cvx-model's current scope.
Mixed-integer/nonconvex solving, additional cones, and other modeling
languages are outside the validated implementation scope.

Current work targets reliable natural-language modeling on small models,
initially `gpt-6-luna`. Five worked recipes cover sparse production, mean-loss
lasso, transportation, perspectives, and repeated ridge solves.
Some tests are taken from the additional exercises of Stanford's Convex Optimization I (EE 364A).
Supplied-data checks are independently authored; solutions are grader references,
not installed-skill resources or candidate context.

## Build and check

Development uses Python 3.14 and [uv](https://docs.astral.sh/uv/). Setup is explicit;
builds do not install dependencies or invoke models:

```bash
uv sync --locked
uv run --no-sync python -m unittest discover -s tests -v
uv run --no-sync python tools/build_release.py
uv run --no-sync python tools/validate_release.py dist/release
uv run --no-sync agentskills validate dist/release/skills/cvx-model
uv run --no-sync agentskills validate dist/release/skills/cvx-explain
```

Install **assembled output**, never the authoring directory:

| Harness | Project/session-local mechanism | Actual M1 check |
|---|---|---|
| Claude Code | `claude --plugin-dir /absolute/path/to/dist/release` | Plugin load and automatic DCP-case selection observed |
| Codex | Copy `dist/release/skills/cvx-model` to project `.agents/skills/cvx-model` | Load and automatic DCP/math-case selection observed |
| OpenCode | Copy to project `.agents/skills/cvx-model` or `.opencode/skills/cvx-model` | Not tested; executable unavailable |
| pi | `pi -e /absolute/path/to/dist/release` | Package load and automatic DCP-case selection observed |

Ask, for example: “Build a mean-loss lasso, keeping the supplied regularization
coefficient.” For cvx-explain, supply code and ask for its mathematical model.
The helper's optional dependencies are declared inline; use an existing compatible
Python environment or explicitly invoke uv. Nothing is installed globally.

## Evidence and limits

**102 local tests pass.** Both skills pass assembly and reference validation.
The release and worked recipes are checked, the three
new exercise-derived examples reproduce reference answers, and three separate recipe
performance workloads pass matched-accuracy checks. These checks do not qualify
a language model. At the earlier live-evaluation checkpoint, generated code
passed all 20 numerical development cases; direct semantic review accepted
21/24 development answers and 4/6 held-out answers. Those results refer to the
earlier skill snapshot. Numerical success alone did not validate explanations.
The full M1 acceptance gate remains open: the broader historical scope had
semantic/generalization and routing issues, mathematical-only automatic selection was inconsistent, and
OpenCode was unavailable. See [M1 evidence](evals/M1_REPORT.md) and
[evaluation contracts/reproduction](evals/README.md). The fresh pi/`gpt-6-luna`
qualification passed **31/39** with-skill cases, below its 95% gate. All three
exercise-derived cases passed in both conditions, and all 25 executable with-skill models
passed numerical probes; artifact/routing and explanation failures remain.
See [the qualification report](evals/LUNA_QUALIFICATION.md). The user-selected
smaller run has no repeats or baseline beyond those exercise-derived cases. No broad or statistical
improvement claim is made. M2 has not started.
The historical qualification used the earlier snapshot. The first focused
cvx-model rerun returned **27/27 valid Python artifacts**, passed **26/27 numerical
cases**, and accepted **23/27 overall**, below the 95% target. See
[the focused pass report](evals/LUNA_MODEL_V2.md). cvx-explain has offline checks
only. The [refinement rerun](evals/LUNA_CONSTRUCTION_FEEDBACK.md) passes **27/27
construction and numerical cases**, with **24/27 accepted overall** (88.9%).
The 95% gate remains unmet. No supplied-example construction failure occurred,
so the opt-in [construction-feedback mode](evals/README.md#optional-construction-feedback)
triggered no correction sessions; its correction efficacy remains unmeasured.
The current skill adds explicit approximation-atom routing, a copyable exact
geometric-mean constructor, and simpler validation guidance. Future evaluations
drop the geometric-mean repair rubric's unrequested explanation criterion;
historical scores retain their frozen rubrics. The
[fresh application pass](evals/LUNA_FRESH_V1.md) accepts **12/12 first attempts**
on 12 new descriptions and 36 new numerical instances. It meets that batch's
predeclared mathematical gate, with no corrections triggered; it does not
establish a general 95% success rate or complete the broader harness checks.
A versioned code-generation evaluation mode asks
for Python source and lets the adapter serialize the stored JSON artifact;
the model no longer needs to escape math and code into JSON. The legacy protocol
and its failures remain retained. See [the focused evaluation mode](evals/README.md#focused-code-generation-protocol).

`release.json` explicitly selects every shipped resource. Generated releases,
evaluation traces, environments, and caches are ignored. `AGENTS.md`, `CLAUDE.md`,
`manual/`, and the source `registry/` remain local-only. Before publishing, ensure
selected inputs are committed. CI remains disabled at
`.github/workflows/ci.yml.disabled`; no publishing/deployment workflow exists.

See [PLAN.md](PLAN.md) for the design and staged roadmap.
