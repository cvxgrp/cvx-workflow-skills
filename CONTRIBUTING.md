# Contributing

Bug reports, suggestions, documentation fixes, and focused skill improvements
are welcome. Raise bugs and suggestions in
[GitHub issues](https://github.com/cvxgrp/cvx-workflow-skills/issues), and submit
code or skill changes through a fork and pull request.

## Issues

Check existing issues before opening a new one. For bugs, include the affected
skill, a minimal reproducible prompt or code example with shareable data, expected
and actual behavior, and relevant harness, model, Python, solver, or framework
versions. For numerical errors, include the original objective and constraints,
solver status, and observed residuals when available.

For suggestions, describe the use case and desired behavior. Discuss substantial
scope changes in an issue before investing in a large implementation.

## Fork and pull request

1. Fork the repository and clone your fork.
2. Create a branch for a focused change.
3. Make the change and run the relevant checks below.
4. Push the branch to your fork and open a pull request against `main` in
   [cvxgrp/cvx-workflow-skills](https://github.com/cvxgrp/cvx-workflow-skills).
5. Describe the problem, resulting behavior, checks run, and any remaining
   limitations. Link the related issue when there is one.

New to contributing? Start with GitHub's guides to
[contributing to a project](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project),
[forking a repository](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/fork-a-repo),
and [creating a pull request from a fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).
The [Agent Skills specification](https://agentskills.io/specification) explains
the skill format.

## Local setup and checks

Use Python 3.14 and [uv](https://docs.astral.sh/uv/getting-started/installation/).
From your clone, install the locked development dependencies explicitly:

```bash
uv sync --locked
```

For skill changes, check `SKILL.md` format, metadata, folder/name agreement, and
instruction bodies:

```bash
uv run --no-sync python -B -m tests
```

For changes to skills, bundled resources, the release map, or packaging tools,
also assemble and validate the distribution:

```bash
uv run --no-sync python -B -m tests.build_release
uv run --no-sync python -B -m tests.validate_release artifacts/release
```

These offline checks do not execute skill helpers, solve problems, or call models.
If you change a helper or numerical example, run a focused check of the assembled
resource with the needed optional dependencies and report what it verifies.
Keep numerical correctness, transformation correctness, and fidelity to the
original requirements distinct. Live model calls are not required for routine
contributions. See [tests/README.md](tests/README.md) for tooling details.

## Keep the distribution focused

- Edit authoring files in `skills/<skill-name>/`; rebuild generated output.
- Include a skill's required inputs in tracked source files. Keep installed skills
  self-contained, with no checkout or sibling-skill dependency.
- When adding, moving, or removing a bundled resource, update `release.json`.
- Keep repository tooling lightweight and compartmentalized in `tests/`.
  Put generated output and evaluation artifacts under ignored `artifacts/`.
- For native solver applications, assemble from original data rather than exporting
  CVXPY solver data or using its reduction-chain inversion.
- Include only material you have permission to contribute, preserving relevant
  attribution and license notices. Contributions are under the repository's
  [Apache-2.0 license](LICENSE).

CI is not enabled yet. Run the relevant local checks and include their results in
your pull request; numerical or model-evaluation claims should state the actual
coverage and dependencies used.
