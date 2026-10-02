# Skill format checks

```bash
uv sync --locked
uv run --no-sync python -B -m tests
```

The checker requires `SKILL.md`, valid Agent Skills frontmatter and metadata,
a skill name matching its folder, and a nonempty instruction body. It uses the
reference validator and does not run helpers, solve models, or call a model.
Only `skills-ref` and its small dependency set are required.

Optional release assembly is separate:

```bash
uv run --no-sync python -B -m tests.build_release
uv run --no-sync python -B -m tests.validate_release artifacts/release
```

Assembly follows `release.json`. Generated releases belong under ignored
`artifacts/`. The previous numerical tests, graders, fixtures, live adapters,
and disabled CI template are retained locally in `artifacts/history/development-suite/`.
They are not part of the shared validation package.
